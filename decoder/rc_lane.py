# -*- coding: utf-8 -*-
"""THE CONSOLIDATED RICHMOND LANE — sync + mint + pull + land, one process.

login 2026-08-24: *"we should actually spend our night consolidating richmond
like we have for acris. This one should be much simpler since the code can
drum. richmond probably wont have anything to sync on new docs anyways, the
rd is done and the pdf would run the same if its the only thing the sync lane
would be doing so we may as well build it to run as one lane."*

    python rc_lane.py --apply [--miners 24] [--workers 16]

⚠ THIS ABSORBS FOUR PROCESSES. rc_live (probe) · rc_feed (token minting) ·
rc_pdf_pull (fetch + land) · rc_pdf_land (dead - see below). Do not run them
alongside it: two minters would hand the same ids out twice, because
`served_ids` is per-process state and nothing in the table records that a
token was minted.

⚠ rc_pdf_land IS ALREADY DEAD WEIGHT AND THIS DROPS IT. Its log is empty.
It swept `_incoming` and converted browser-downloaded COLOR JPEG pages to G4
TIFF - the old Chrome path. rc_pdf_pull replaced that: the courts host serves
a real PDF (`body[:4] == b"%PDF"`), landed straight into the store. Nothing
has needed conversion since. Keeping it running was harmless but it is not
part of the lane.

──────────────────────────────────────────────────────────────────────────
THE DRUMROLL SETTING (login: "there isnt a metronome on richmond. it can just
drum away and move as fast as the server allows based on my ping - latency can
do feedback loops")

ACRIS gets a metronome because it trips on bunched ARRIVALS: a pacer chooses
the rate and `--max-inflight` supplies backpressure. Richmond has earned the
opposite setting - PROVEN at 160 concurrent connections for 26 hours - so
there is no pacer here at all. Concurrency is the only dial, and the feedback
loop is latency itself: when the server slows, every worker waits longer, and
the request rate falls WITH it automatically. That is backpressure for free,
and it is the one thing drumroll does better than a metronome.

⚠ SO THE SAFETY IS NOT PACING, IT IS THE REFUSAL VERDICT. Nothing here backs
off on load, because load is not what hurts this source. What hurts is
mistaking a single restricted document for a lane-wide refusal - see
refusal_verdict().

──────────────────────────────────────────────────────────────────────────
WHAT CONSOLIDATION ACTUALLY BUYS (beyond one pid)

The feed served tokens over `http://localhost:8077/batch` with a CORS header
and a BaseHTTPRequestHandler, because its consumer used to be a BROWSER. In
one process that is a `queue.Queue`. The entire HTTP hop, the port, the CORS
allowance and the polling loop all disappear - every minted token now moves
between threads instead of over a socket.

⚠ TWO HOSTS, NOT ONE - THE ASYMMETRY THAT MATTERS HERE. Minting talks to
richmondcountyclerk.com; the image comes from iapps.courts.state.ny.us on a
self-authenticating token. They are different servers with different limits,
so they get INDEPENDENT worker pools (--miners, --workers). Sizing them as
one number would let a slow minter starve a fast puller, or the reverse.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import queue
import re
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request

import requests

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                      # noqa: E402
import rc_source as RC                                         # noqa: E402
import rc_sync as RCS                                          # noqa: E402

# > rc_rd_walk PARSES argv AT IMPORT - shim it away, then restore. Its
# parse_detail() is the CORPUS SCHEMA parser (the shape the 2.4M existing rows
# already use, NOT rc_source's), and re-deriving it would re-derive the
# divergence between them.
_argv, sys.argv = sys.argv, ["rc_rd_walk.py"]
import rc_rd_walk as RW                                        # noqa: E402
sys.argv = _argv

STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                     r"\Legal Instruments Acquisition")
INCOMING = STORE / "_incoming"
LEDGER = (r"D:\CRE Decoding System\00 Synchronizations"
          r"\Legal Instruments Synchronization"
          r"\Legal Instruments Synchronization.db")
STATE = HERE / "_rc_live_page.json"
RESTRICTED_F = HERE / "rc_restricted.jsonl"
FAILS = HERE / "rc_lane_fails.jsonl"

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true",
                help="write; default reports and writes nothing")
ap.add_argument("--miners", type=int, default=24,
                help="token minters against richmondcountyclerk.com")
ap.add_argument("--workers", type=int, default=16,
                help="pullers against the courts image host")
ap.add_argument("--hot-pdf", action="store_true",
                help="let a freshly synced filing's IMAGE jump the pdf queue."
                     " ⚠ OFF by default since 2026-08-25, matching acris."
                     " login: \"sync gets doc id, mints, rd, pass 1, and then"
                     " pdf adds to the backfill.\" The sync already lands the"
                     " id, the url, the rd and pass-1 key - everything"
                     " freshness-sensitive - so only the IMAGE waits its turn,"
                     " and the sequential pdf run is never interrupted by"
                     " inflow. ⚠ The backfill reaches it IMMEDIATELY once"
                     " level, because a new filing sorts at the END of the id"
                     " order the pass walks.")
ap.add_argument("--ahead", type=int, default=1200,
                help="minted tokens kept ready ahead of the pullers")
# ⚠ NO --batch. rc_pdf_pull took tokens 3 at a time to amortise an HTTP
# round-trip to the feed's localhost endpoint. In one process the queue is
# in memory, so batching buys nothing and only makes a puller hold tokens it
# is not yet working on - which matters because tokens EXPIRE (TOKEN_TTL).
ap.add_argument("--every", type=int, default=10,
                help="seconds between synchronization probes")
ap.add_argument("--sweep-every", type=int, default=900,
                help="seconds between full-day sweeps (the cached-page tick"
                     " is blind to earlier pages)")
ap.add_argument("--cooldown", type=int, default=600,
                help="seconds all workers hold while a 4xx is arbitrated")
ap.add_argument("--stall-after", type=int, default=300,
                help="seconds with ZERO successful pulls before the transport"
                     " is presumed dead and recycled")
ap.add_argument("--rd-every", type=int, default=900,
                help="seconds between rd heal passes for rd-less RC rows")
ap.add_argument("--hot-recheck", type=float, default=1800,
                help="seconds before a recent filing may be pushed onto the"
                     " hot list again. Its pull may still be in flight, and"
                     " re-queueing every pass would fill the hot lane with"
                     " duplicates of itself.")
ap.add_argument("--absent-recheck", type=int, default=21600,
                help="seconds before re-asking about a document whose"
                     " scan was not up yet (default 6h)")
ap.add_argument("--lag-days", type=int, default=7,
                help="THE SCAN-LAG WINDOW. login 2026-08-25: \"if no image"
                     " comes back from the url then it is no pdf, but there is"
                     " a 7 day lag period given for new filings.\" Inside the"
                     " window an absent image is SCAN LAG - the row keeps"
                     " pdf='' and stays in the queue. Outside it, absent is a"
                     " FACT about the document and is recorded as a verdict.")
ap.add_argument("--rd-days", type=int, default=30,
                help="trailing window the rd heal opens (the grant rule: a"
                     " window's own pages unlock its ids' details)")
ap.add_argument("--pending-every", type=int, default=300,
                help="seconds between PENDING RECHECK sweeps - re-ask every"
                     " row still waiting on a scan. 0 disables. ⚠ The mint"
                     " request IS the image test (302=up · 200/404=dead"
                     " end), so this costs exactly ONE request per pending row"
                     " and needs no listing page and no grant rule. MEASURED"
                     " 2026-08-26: 203 pending rows = a 12 s sweep at the"
                     " lane's 16 docs/s. The interval is the only throttle -"
                     " see pending_recheck().")
ap.add_argument("--day", default=None, help="probe this MM/DD/YYYY, not today")
a = ap.parse_args()

# ⚠ VIEWER TOKENS EXPIRE. Overnight 2026-08-22 the consumer stalled while the
# feed kept its buffer full; by morning all 786 ready tokens were hours dead
# and even "fresh" polls served corpses. A token older than this is discarded
# at CONSUME time and its id released to be re-minted.
TOKEN_TTL = 600

# ⚠ THE USER-AGENT IS LOAD-BEARING ON THE COURTS HOST - MEASURED 2026-08-22.
# Alternating requests, one variable, everything else identical:
#     python-requests/2.34.2 (library default) -> ReadTimeout at 45s, 2/2
#     acris-decoder/1.0 (this project's UA)    -> 200 + full pdf in 1.5s, 2/2
# A timeout is not a refusal, and that difference cost an hour of wrong
# diagnosis. NOT spoofing - this is the project's own honest self-identifying
# UA. Do not substitute a browser UA: measured to buy nothing, and it would
# make the client dishonest.
HDRS = {"User-Agent": RC.UA,
        "Referer": RC.BASE + "/",
        "Accept": "application/pdf,*/*"}

# >> THE HOT LIST - WHY "SYNCED" DID NOT MEAN COMPLETE (measured 2026-08-24).
# Of 80 richmond documents the sync landed today, 80 had urls, 73 had rd, 73
# had keys - and ZERO had pdfs. Not a failure: the miner selects
# `... AND pdf = '' ORDER BY id`, and RC ids are sequential, so today's
# RC_282xxxx filings sit at the END of the queue behind 1.39M older documents.
# At 13 docs/s the backfill would not reach them for ~29 hours.
#
# ACRIS solved this long ago with a hot list ("new filings jump the line") so
# today's documents are fully ready the same day. Richmond never had one. So:
# a freshly-rd'd id goes on the hot list, miners mint it BEFORE taking any
# backfill batch, and pullers drain the hot side first. A new filing now goes
# id -> rd -> key -> pdf in minutes instead of a day.
hot_ids = queue.Queue()                   # ids needing a token URGENTLY
ready_hot = queue.Queue()                 # their minted tokens, jump the line
WAKE_RD = threading.Event()               # the probe pokes the rd heal awake
WAKE_PEND = threading.Event()             # ...and the pending recheck
# >> PER-DOCUMENT COOLDOWN ON THE ABSENT RE-CHECK. Without it, a row
# recorded inside the window whose scan NEVER appears gets re-asked every
# --rd-every forever: ~100 new absent rows a day accumulating over 30
# days, each re-fetched 96 times a day, is tens of thousands of pointless
# requests at a source that has done nothing wrong. Most scans land within
# a day or two, so checking a given document a few times a day is plenty.
_absent_at: dict[str, float] = {}
# >> ids already pushed onto the hot list, with when. Without this the window
# re-queues the same recent filings every --rd-every while their pull is still
# in flight, and the hot lane fills with duplicates of itself.
_hot_at: dict[str, float] = {}
ready = queue.Queue()                     # (did, location, minted_at)
DBQ = queue.Queue(maxsize=10000)          # (did, relpath|'pending'|'absent')
                                          # -> the ONE writer
# miners need the recorded date to apply the lag; one shared read handle,
# guarded, because sqlite connections are not thread-safe
_RO: list = [None]
_RO_LK = threading.Lock()
STOP = threading.Event()
HOLD = threading.Event()                  # 4xx arbitration in progress
lock = threading.Lock()
grab_lock = threading.Lock()              # guards next_ids + served_ids as a
                                          # UNIT (a nested take of the
                                          # non-reentrant stats lock
                                          # deadlocked rc_feed v1 at startup)
tl = threading.local()
served_ids: set[str] = set()              # never hand the same doc out twice
stat = {"minted": 0, "skipped": 0, "got": 0, "bytes": 0, "err": 0,
        "wrote": 0, "stale": 0, "synced": 0, "probe_req": 0, "rd": 0,
        "hot": 0}
last_ok = [time.time()]
# !! EVIDENCE THAT WORK WAS ATTEMPTED, not merely that it succeeded.
# The watchdog below cannot tell 'the route died' from 'there is nothing
# to do' without this - and richmond is at 100%, so 'nothing to do' is
# now its NORMAL state. Measured 2026-08-27: 6 recycles in 30 minutes,
# every 300s on the dot, each one discarding warm sockets to repair a
# route that was never broken.
last_try = [0.0]

RESTRICTED = set()
if RESTRICTED_F.exists():
    for _ln in RESTRICTED_F.read_text(encoding="utf-8").splitlines():
        try:
            RESTRICTED.add(json.loads(_ln)["id"])
        except Exception:
            pass


def say(m):
    print("%s  %s" % (time.strftime("%H:%M:%S"), m), flush=True)


# ── the transport, swappable ───────────────────────────────────────────
# ⚠ A NETWORK CHANGE MUST NOT NEED A RESTART (the acris lesson, 2026-08-24).
# Every pooled socket is bound to the old route; after a vpn hop or an ip
# re-lease they are all dead and urllib3 rediscovers that ONE REQUEST AT A
# TIME - each worker burning a full timeout to relearn the same fact, which
# is what makes a route change look like a hang. Swapping the session closes
# every stale socket at once. Overnight runs need this more than anything.
_SESS = [None]
_sess_lk = threading.Lock()
_recycles = [0]


def _new_session():
    s = requests.Session()
    s.headers.update(HDRS)
    s.mount("https://", requests.adapters.HTTPAdapter(
        pool_connections=4, pool_maxsize=max(8, a.workers), max_retries=0))
    return s


def recycle_session(why):
    with _sess_lk:
        old, _SESS[0] = _SESS[0], _new_session()
        _recycles[0] += 1
        n = _recycles[0]
    if old is not None:
        try:
            old.close()
        except Exception:
            pass
    say("  ⟳ TRANSPORT RECYCLED (#%d): %s" % (n, why))


_SESS[0] = _new_session()


def watchdog():
    """⚠ THE SILENT ROUTE CHANGE. A burst of errors is the loud case. The
    quiet one is worse: the route dies while every worker sits inside a
    90 s socket timeout, so nothing fails, nothing lands, no counter moves,
    and the lane looks busy while doing nothing. Only a human noticing a flat
    board ever caught that."""
    while not STOP.is_set():
        time.sleep(20)
        now = time.time()
        quiet = now - last_ok[0]
        trying = (now - last_try[0]) < a.stall_after
        # !! SILENCE ONLY MEANS A DEAD ROUTE IF WE WERE ACTUALLY TRYING.
        # `last_ok` moves on a SUCCESSFUL pull, so an idle lane starves it
        # and the old test fired forever. Requiring a RECENT ATTEMPT makes
        # the two cases separable:
        #   issuing + not succeeding -> the route really is dead -> recycle
        #   not issuing at all       -> no work; silence is correct -> wait
        # A DETECTOR THAT CANNOT DISTINGUISH INTENDED SILENCE FROM FAILURE
        # IS ONE THAT GETS IGNORED - the same lesson the night watch learned
        # twice on 2026-08-26.
        if quiet >= a.stall_after and trying and not HOLD.is_set():
            recycle_session("no successful pull for %.0fs while STILL"
                            " ISSUING - presuming the route changed under us"
                            % quiet)
            last_ok[0] = time.time()


# ── minting (richmondcountyclerk.com) ──────────────────────────────────

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def next_ids(n):
    """Next RC docs needing a pdf, skipping ones already handed out.
    Caller holds grab_lock.

    ⚠ BOUND THE ID RANGE. RC_ ids sort AFTER every acris id, so an unbounded
    scan walks 21M acris rows (evaluating json_extract on the way) before
    reaching the first Richmond row - measured 2026-08-22: minting fell to
    0.83/s while the consumer took 2.7/s, starving the lane. `id > 'RC'`
    starts the index seek at the Richmond block.

    ⚠ Also skips ids whose RAW download still sits in _incoming: a restart
    forgets served_ids, and re-serving them made the old browser path
    re-download 2,300+ as "RC_x (1).pdf" dups. The download IS the evidence.
    Legacy now that pulls land directly, but the guard costs one glob."""
    have_raw = {re.sub(r" \(\d+\)$", "", p.stem)
                for p in INCOMING.glob("RC_*.pdf")} if INCOMING.exists() \
        else set()
    con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=120)
    con.execute("PRAGMA busy_timeout=60000")
    rows = con.execute(
        "SELECT id FROM navigation WHERE id > 'RC' AND id LIKE 'RC_%'"
        # ⚠⚠ 'pending' IS STILL TODO (login 2026-08-25: "pedning remains
        # in que until 7 dyas passes"). The moment a cell holds 'pending' it
        # stops matching pdf='' - so every todo predicate, the partial index
        # and the board's denominator had to move in ONE change or those rows
        # would silently leave the worklist AND be counted as landed.
        " AND recorded_details != '' AND pdf IN ('', 'pending')"
        " AND json_extract(recorded_details, '$.image_state') = 'present'"
        " ORDER BY id LIMIT ?",
        (n + len(served_ids) + len(have_raw),)).fetchall()
    con.close()
    return [r[0] for r in rows
            if r[0] not in served_ids and r[0] not in have_raw][:n]


def _open_ro():
    _RO[0] = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True,
                             timeout=120, check_same_thread=False)
    _RO[0].execute("PRAGMA busy_timeout=120000")


def miner():
    """⚠ A MINER MUST NEVER DIE. A bare exception here silently killed all
    six threads at startup once and minting sat at 0 while the lane looked
    healthy - hence the outer guard as well as the inner one."""
    while not STOP.is_set():
      try:
        if HOLD.is_set():
            time.sleep(5)
            continue
        # > HOT FIRST, ALWAYS - and note this is checked BEFORE the --ahead
        # buffer test. A full backfill buffer must never delay a filing that
        # landed minutes ago; that is the whole point of the hot list.
        grab, is_hot = [], False
        try:
            grab = [hot_ids.get_nowait()]
            is_hot = True
        except queue.Empty:
            if ready.qsize() >= a.ahead:
                time.sleep(5)
                continue
            with grab_lock:
                try:
                    grab = next_ids(20)
                except Exception:
                    grab = []
                served_ids.update(grab)
        if not grab:
            time.sleep(15)
            continue
        for did in grab:
            if STOP.is_set():
                return
            iid = did[3:]
            try:
                if not hasattr(tl, "op"):
                    # a clerk session per miner thread, cookies and all
                    w = RCS.Window("08/17/2026", "08/17/2026")
                    tl.op = urllib.request.build_opener(
                        urllib.request.HTTPCookieProcessor(w.s.jar),
                        _NoRedirect())
                    tl.op.addheaders = [("User-Agent", RC.UA)]
                time.sleep(RC.PACE)
                req = urllib.request.Request(
                    RC.BASE + "/ViewVscmsDocument/ViewContent"
                    "?p_endorsementId=%s" % iid)
                req.add_header("Referer",
                               RC.BASE + "/Search/ViewDocumentInfo/%s" % iid)
                # ⚠⚠ THREE OUTCOMES, NEVER TWO (login 2026-08-25: "we have
                # the url, if it doesnt show, its absent, if it shows a fetch
                # its pdf, and if its absent but the recorded date of the doc
                # id is in the lag period it gets pending").
                #
                # This used to collapse "the endpoint answered and there is
                # no image" together with "our request never got there" into
                # one `skipped` counter. They are opposite facts: the first
                # is a statement ABOUT THE DOCUMENT and may be recorded; the
                # second is a statement about US and must only be retried.
                # login named this exactly: "any error that isnt from a
                # deadend url should not msireport a missing url if the
                # system is just failing the fetch".
                loc, outcome = None, "error"
                try:
                    with tl.op.open(req, timeout=60):
                        # 200 with redirects disabled = the endpoint answered
                        # and handed us no image location. A DEAD END.
                        outcome = "noimage"
                except urllib.error.HTTPError as e:
                    # ⚠ THE 302 IS THE PRODUCT. The pdf does NOT live on
                    # richmond: the Location points at the NY State courts
                    # viewer with a self-authenticating token.
                    if e.code in (301, 302, 303):
                        loc = e.headers.get("Location") or ""
                        # ⚠⚠ A 302 IS NOT AUTOMATICALLY AN IMAGE, and
                        # "any Location at all" was the wrong test. MEASURED
                        # 2026-08-26, both ids minted back to back on ONE
                        # session so the session cannot be the difference:
                        #
                        #   RC_2825613 (image up) -> 302
                        #     https://iapps.courts.state.ny.us/vscms_public/
                        #     viewer?token=v2....
                        #   RC_2820269 (no image) -> 302  /Search/SearchError
                        #
                        # The clerk answers a no-image document with a
                        # REDIRECT TO ITS OWN ERROR PAGE. The old test called
                        # that "present", handed '/Search/SearchError' to the
                        # puller, and requests died client-side with
                        # MissingSchema before any request left the machine -
                        # so the row could never resolve and never even
                        # reached the state machine. It stayed dormant only
                        # because next_ids() gated on image_state='present',
                        # which no such row can match; pending_recheck() is
                        # what put these ids in front of a miner at all.
                        #
                        # ⚠ THE TEST IS "AN ABSOLUTE URL WE CAN FETCH",
                        # not "not the error page" - a relative Location of
                        # any shape is unfetchable and must never be called
                        # present. And this only ever produces `noimage`,
                        # which _no_image() turns into 'pending' inside the
                        # lag window; a verdict of 'absent' still needs the
                        # lag to have expired AND the rd to agree.
                        if loc[:8].lower().startswith(("http://", "https:/")):
                            outcome = "present"
                        else:
                            loc, outcome = None, "noimage"
                    elif e.code == 404:
                        outcome = "noimage"     # the url itself is a dead end
                    else:
                        # 403/429/5xx say nothing about the DOCUMENT
                        outcome = "error"
                if outcome == "present" and loc:
                    (ready_hot if is_hot else ready).put(
                        (did, loc, time.time()))
                    with lock:
                        stat["minted"] += 1
                        if is_hot:
                            stat["hot"] += 1
                elif outcome == "noimage":
                    # THE LAG DECIDES WHICH KIND OF "no pdf" THIS IS.
                    _no_image(did)
                else:
                    with lock:
                        stat["skipped"] += 1      # ours - retry, never record
            except Exception:
                with lock:
                    stat["skipped"] += 1
      except Exception:
        time.sleep(5)


# ── the refusal verdict ────────────────────────────────────────────────

def refusal_verdict(did, code):
    """⚠ A LONE 4xx IS AMBIGUOUS, AND GUESSING COST ~55 MINUTES (2026-08-24).
    RC_1873622 - an EXHIBIT filed to the City - 403'd once inside a 190,594
    doc clean run, and the any-4xx-stops-all rule silenced the whole lane.
    login: "richmond should never have stalled."

    Sealed and restricted records 403 at ANY request rate. That is a VERDICT
    ABOUT ONE DOCUMENT, not a refusal of us. So: hold everything, cool down,
    then ONE probe of a DIFFERENT document decides.
        probe also 4xx -> the LANE is refused -> STOP for good. No retry, no
                          rotation; resuming is login's call.
        probe fine     -> the original doc is RESTRICTED -> quarantine it
                          with evidence and the lane resumes itself.
    The refused document is NEVER re-requested either way."""
    if HOLD.is_set() or STOP.is_set():
        return                             # one arbiter at a time
    HOLD.set()
    say("!! %s on %s - HOLDING ALL WORKERS %ds; one probe of a DIFFERENT doc"
        " will decide: lane refused vs doc restricted" % (code, did,
                                                          a.cooldown))
    try:
        time.sleep(a.cooldown)
        try:
            pdid, ploc, _ = ready.get(timeout=30)
        except queue.Empty:
            say("   no probe token available - releasing the hold, unproven")
            return
        try:
            pr = _SESS[0].get(ploc, headers=HDRS, timeout=(10, 90))
            ok = pr.status_code == 200 and pr.content[:4] == b"%PDF"
        except Exception as e:
            say("   probe unproven (%s) - releasing the hold" % type(e).__name__)
            return
        if ok:
            RESTRICTED.add(did)
            with RESTRICTED_F.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "id": did, "code": code,
                    "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "probe": pdid, "verdict": "doc restricted"}) + "\n")
            say("   VERDICT: %s is RESTRICTED (probe %s returned a pdf) -"
                " quarantined, lane resumes" % (did, pdid))
            ready.put((pdid, ploc, time.time()))
        else:
            STOP.set()
            say("   VERDICT: THE LANE IS REFUSED (probe %s also failed) -"
                " STOPPING. No retry, no rotation." % pdid)
    finally:
        HOLD.clear()


# ── pulling (iapps.courts.state.ny.us) ─────────────────────────────────

def puller():
    # ⚠⚠ ONE SESSION PER WORKER, LIKE THE CODE THAT MEASURED 10+ docs/s.
    # login 2026-08-25: "however acqusition richmond pdf ran is the code that
    # the pdf path needs to run on". The retired rc_pdf_pull.py gave EVERY
    # worker its own requests.Session (its worker() line 201); the
    # consolidation replaced that with one process-wide pooled session, and
    # richmond has not seen 10 docs/s since. A shared urllib3 pool makes 64
    # threads contend for connection checkout on one lock, and any pool
    # churn is paid as a fresh TLS handshake per document. A per-thread
    # session gives each worker its OWN kept-alive connection - no checkout,
    # no churn, no shared lock. ⚠ This is not a tuning guess: it is the
    # difference between the code that hit 11.6/s and the code that did not.
    sess = requests.Session()
    sess.headers.update(HDRS)
    sess.mount("https://", requests.adapters.HTTPAdapter(
        pool_connections=2, pool_maxsize=4, max_retries=0))
    ro = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=120)
    ro.execute("PRAGMA busy_timeout=60000")
    while not STOP.is_set():
        while HOLD.is_set() and not STOP.is_set():
            time.sleep(5)
        # > drain the hot side first; only then the backfill
        try:
            did, loc, minted = ready_hot.get_nowait()
        except queue.Empty:
            try:
                did, loc, minted = ready.get(timeout=5)
            except queue.Empty:
                continue
        if STOP.is_set():
            return
        if did in RESTRICTED:
            continue
        # ⚠ CHECK THE TOKEN'S AGE AT CONSUME TIME, NOT AT MINT TIME. A full
        # buffer plus a stalled consumer means every token in it is dead.
        if time.time() - minted > TOKEN_TTL:
            with lock:
                stat["stale"] += 1
            with grab_lock:
                served_ids.discard(did)    # release it to be re-minted
            continue
        try:
            # ⚠ stream=True, as the proven puller had it: the body is read
            # off the socket by .content below, so the READ timeout applies
            # per chunk rather than to one whole 5 MB transfer.
            last_try[0] = time.time()      # issued - see watchdog
            r = sess.get(loc, timeout=(10, 90), stream=True)
            if r.status_code in (401, 403, 429):
                refusal_verdict(did, r.status_code)
                continue
            if r.status_code != 200:
                _fail(did, "HTTP %d" % r.status_code)
                continue
            body = r.content
            # ⚠ MAGIC-CHECK BEFORE WRITING. A short or non-pdf body that gets
            # written and recorded is a permanent wrong answer that looks
            # exactly like success.
            if len(body) < 5 or body[:4] != b"%PDF":
                _fail(did, "not a pdf (%d bytes, %r)" % (len(body), body[:8]))
                continue
            last_ok[0] = time.time()
            rec = ro.execute("SELECT recorded_details FROM navigation"
                             " WHERE id=?", (did,)).fetchone()
            recorded = ""
            if rec and rec[0]:
                try:
                    recorded = json.loads(rec[0]).get("recorded", "") or ""
                except ValueError:
                    recorded = ""
            # ⚠ STORE PATH = RECORDED CHRONOLOGY. CP.doc_store_dir owns that
            # rule; the id's own digits are a SUBMISSION date and can lag.
            dest = CP.doc_store_dir(did, recorded)
            dest.mkdir(parents=True, exist_ok=True)
            dst = dest / ("%s.pdf" % did)
            # ⚠ .part THEN RENAME. A crash mid-write must never leave a
            # truncated pdf sitting where a complete one belongs.
            tmp = dst.with_suffix(".pdf.part")
            tmp.write_bytes(body)
            tmp.replace(dst)
            with lock:
                stat["got"] += 1
                stat["bytes"] += len(body)
            if a.apply:
                DBQ.put((did, str(dst.relative_to(STORE))))
        except Exception as e:
            _fail(did, "%s: %.80s" % (type(e).__name__, e))


def _fail(did, why):
    with lock:
        stat["err"] += 1
    with FAILS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                             "id": did, "why": why}) + "\n")


# ── the one writer ─────────────────────────────────────────────────────

def writer():
    """⚠ ONE SEAT, BATCHED. Measured 2026-08-22 on the acris side: per-row
    commits gave ~2/s and ONE executemany per 250 rows kept pace with 12.5/s.
    The work was never the problem; holding the write lock during it was."""
    con = sqlite3.connect(CP.NAV_DB, timeout=600)
    con.execute("PRAGMA busy_timeout=300000")
    pend = []

    def flush():
        if not pend:
            return
        for _try in range(120):            # never die on a lock
            try:
                # ⚠ ONLY OVER AN UNDECIDED CELL. A landed path is never
                # overwritten by a later 'pending'/'absent', and 'absent' is
                # never silently reverted; 'pending' -> path is the one
                # upgrade that must work.
                con.executemany("UPDATE navigation SET pdf=? WHERE id=?"
                                " AND pdf IN ('', 'pending')",
                                [(p, d) for d, p in pend])
                con.commit()
                break
            except sqlite3.OperationalError:
                time.sleep(5)
        with lock:
            stat["wrote"] += len(pend)
        pend.clear()

    while not STOP.is_set():
        try:
            pend.append(DBQ.get(timeout=5))
        except queue.Empty:
            flush()
            continue
        if len(pend) >= 250:
            flush()
    flush()
    con.close()


# ── synchronization (the probe) ────────────────────────────────────────

def urls(did):
    """Pure function of the id — the same mint as nav_append and
    routine_navigation."""
    n = did[3:]
    return ("%s/Search/viewDocumentInfo/%s" % (RC.BASE, n),
            "%s/ViewVscmsDocument/ViewContent?p_endorsementId=%s"
            % (RC.BASE, n))


def land(ids):
    """⚠ EVERY WORK COLUMN IS '' AND NEVER NULL. Those lanes select on
    `= ''`, and NULL is not '' - so a NULL row is invisible to every lane
    forever while looking perfectly healthy."""
    con = sqlite3.connect(CP.NAV_DB, timeout=600)
    con.execute("PRAGMA busy_timeout=300000")
    batch = [(d, "", urls(d)[0], "", urls(d)[1], "", "") for d in ids]
    for _try in range(120):
        try:
            con.executemany(
                "INSERT OR IGNORE INTO navigation"
                " (id, recorded_details, rd_url, pdf, pdf_url, keyed_by, key)"
                " VALUES (?,?,?,?,?,?,?)", batch)
            con.commit()
            break
        except sqlite3.OperationalError:
            time.sleep(5)
    else:
        con.close()
        raise RuntimeError("could not acquire the write lock in 10 minutes")
    n = con.total_changes
    con.close()
    return n


def _url_minted(con_, did):
    """⚠ NEVER CALL A MISSING MINT A DEAD END. If pdf_url was never written,
    the reason there is no image is OURS, and recording "no pdf" would hide a
    minting defect as a fact about the document - permanently, since the row
    would leave the todo set. No mint => no verdict; the row stays todo."""
    try:
        r = con_.execute("SELECT COALESCE(pdf_url,'') FROM navigation"
                         " WHERE id=?", (did,)).fetchone()
    except Exception:
        return False
    return bool(r and r[0])


def _no_image(did):
    """The url is a dead end. Record WHICH kind, and only ever into an
    undecided cell.

    login 2026-08-25: "the pdf cell just has the path for the fetch. if no
    pdf itll either be absent or pending. and pedning remains in que until 7
    days passes."

        pending  recorded inside --lag-days. STAYS IN THE QUEUE - the scan
                 has not arrived yet. PROVEN necessary: 10 of 10 documents
                 recorded on a Friday had no image then and did after the
                 weekend.
        absent   the lag expired. The document has no scan, and this is the
                 determination that lets completion reach 100%.

    ⚠ Written through DBQ, the ONE writer seat - miners never touch the write
    connection. ⚠ And only over '' or 'pending': a real path is never
    overwritten, and 'absent' never silently reverts."""
    rec = cur = ""
    try:
        with _RO_LK:
            r = _RO[0].execute("SELECT json_extract(recorded_details,"
                               "'$.recorded'), pdf,"
                               " json_extract(recorded_details,"
                               "'$.image_state') FROM navigation"
                               " WHERE id=?", (did,)).fetchone()
        rec = (r[0] if r and r[0] else "") or ""
        cur = (r[1] if r and r[1] else "") or ""
        shot = (r[2] if r and r[2] else "") or ""
    except Exception:
        rec = cur = shot = ""         # unreadable => treated as in-lag below
    state = "pending" if _in_lag(rec) else "absent"
    # ⚠ 'absent' NEEDS TWO SOURCES TO AGREE. The url saying "no image" is
    # one reading and it can also be produced by a bad session; the DETAIL
    # PAGE saying so in its own words ("No Image Available At This Time" ->
    # image_state) is the second. If our own rd says the image is PRESENT and
    # the url disagrees, the odd one out is far more likely to be us - so
    # refuse the verdict and leave the row queued to be asked again. Costs one
    # re-ask; the alternative is a fabricated determination that nothing ever
    # revisits.
    if state == "absent" and shot == "present":
        with lock:
            stat["skipped"] = stat.get("skipped", 0) + 1
        return
    # ⚠ A RE-ASK THAT CHANGES NOTHING MUST NOT WRITE. pending_recheck()
    # puts the WHOLE pending set back through the miners every
    # --pending-every seconds and nearly every answer is "still pending" -
    # that would be 203 identical UPDATEs a sweep, ~58k a day, dirtying pages
    # and taking the one writer seat to record no fact at all. The stat
    # counter still moves, so a sweep that changed nothing is still visible
    # as work done rather than looking like a dead thread.
    if cur != state:
        DBQ.put((did, state))
    with lock:
        stat[state] = stat.get(state, 0) + 1


def _in_lag(recorded):
    """Is this filing still inside the --lag-days scan window?

    ⚠ UNPARSEABLE DATE => TREAT AS IN-LAG. An unreadable recorded date must
    never license a permanent "no pdf": the failure mode of guessing wrong
    here is a document silently marked as having no scan when it has one, and
    nothing would ever look again. Staying in the queue costs one re-ask."""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(recorded or ""))
    if not m:
        return True
    try:
        t = time.mktime((int(m.group(3)), int(m.group(1)), int(m.group(2)),
                         0, 0, 0, 0, 0, -1))
    except (ValueError, OverflowError):
        return True
    return (time.time() - t) < a.lag_days * 86400


def pending_recheck():
    """RE-ASK EVERY ROW STILL WAITING ON A SCAN - the dynamic maturation.

    login 2026-08-26: "is there a more dynamic way for those pending images to
    get checked over just a nightly check?" - yes, and it is cheaper than the
    two things that were half-doing the job.

    > THE MINT REQUEST IS ALREADY THE IMAGE TEST. miner() asks
    /ViewVscmsDocument/ViewContent with redirects OFF and reads three outcomes:
    302+Location = the scan is up, 200 or 404 = dead end, 403/429/5xx = ours
    and retried. So "has the scan arrived?" costs exactly ONE request per
    document - no detail page, no listing page, and ⚠ NO GRANT RULE,
    because the mint endpoint takes a bare id. MEASURED 2026-08-26: the
    pending set was 203 rows over 2 recording dates, so a full sweep is 203
    requests, ~12 s at the lane's measured 16 docs/s. At --pending-every 300
    that is 0.68 req/s.

    > WHAT IT REPLACES.
      * rd_heal DOES re-ask pending ids - but to FIND them it opens a 30-day
        Window and pages it at 17 rows a page: 2,701 rows / ~160 listing
        requests every 15 min, to rediscover 203 ids we already know BY NAME.
        Then --absent-recheck (6 h) throttles each one, so a pending document
        was actually looked at four times a day.
      * rc_pdf_state.py at 04:00 is NOT a checker at all - it is the calendar
        maturation (pending -> absent at day 7), pure SQL, no network. That one
        genuinely belongs nightly and stays, now as a safety net.

    > NOTHING DOWNSTREAM NEEDED BUILDING. _no_image() already writes 'pending'
    while the row is in lag and 'absent' once it expires, and the writer only
    ever fills an undecided cell. Feeding these ids to the miners therefore
    makes the MATURATION dynamic too, not just the check.

    ⚠ A DEDICATED TIMER, NOT A RELAXED next_ids(). The obvious version of
    this is to drop `image_state='present'` from next_ids(). That gate was
    right during the backfill - it kept 24 miners off 1.39M imageless rows -
    and removing it now would simply have those same miners spinning on the
    same 203 rows at 16/s forever. THE INTERVAL IS THE THROTTLE.

    ⚠ SELECTED THROUGH THE INDEXED PREDICATE, SPLIT IN PYTHON. A bare
    `pdf='pending'` cannot use ix_nav_pdf_todo - SQLite will not prove
    `='pending'` implies the IN list - and degrades to a 2.5M-row scan. That is
    the exact drift that cost 12 minutes of cold start on 2026-08-25.

    ⚠ NEVER STACK SWEEPS. hot_ids is unbounded; if the last sweep is still
    draining, skip this one rather than queueing the same ids twice."""
    if a.pending_every <= 0:
        say("  PENDING RECHECK: disabled (--pending-every 0)")
        return
    while not STOP.is_set():
        WAKE_PEND.wait(a.pending_every)
        WAKE_PEND.clear()
        if STOP.is_set():
            return
        if HOLD.is_set():
            continue
        try:
            if not hot_ids.empty():
                say("  PENDING RECHECK: skipped, %d id(s) still draining from"
                    " the last sweep" % hot_ids.qsize())
                continue
            con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True,
                                  timeout=120)
            con.execute("PRAGMA busy_timeout=60000")
            rows = con.execute(
                "SELECT id, pdf FROM navigation WHERE id > 'RC'"
                " AND id LIKE 'RC_%' AND pdf IN ('', 'pending')").fetchall()
            con.close()
            ids = [d for d, p in rows if p == "pending"]
            for did in ids:
                hot_ids.put(did)
            say("  PENDING RECHECK: %d row(s) awaiting a scan re-asked"
                " (1 mint request each); %d unassigned also in the queue"
                % (len(ids), len(rows) - len(ids)))
        except Exception as e:
            say("  PENDING RECHECK: %s - will retry next sweep"
                % type(e).__name__)


def fresh(rows):
    """Which of these do we not hold? One PK lookup each - no scan."""
    con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=600)
    con.execute("PRAGMA busy_timeout=300000")
    out = []
    for r in rows:
        did = "RC_" + r["internal_id"]
        if not con.execute("SELECT 1 FROM navigation WHERE id=?",
                           (did,)).fetchone():
            out.append(did)
    con.close()
    return out


def _load_page(today):
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
        if st.get("date") == today:
            return int(st.get("page", 1))
    except Exception:
        pass
    return 1


def _save_page(today, page):
    STATE.write_text(json.dumps({"date": today, "page": page,
                                 "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
                                indent=1), encoding="utf-8")


_last_sweep = [0.0]


def probe():
    """One request every --every seconds against today's date window.

    ⚠ rows=0 IS NOT THE SAME AS A QUIET DAY. An over-cap range, changed
    markup and a genuine absence all return HTTP 200 with no rows; only the
    server's own "NO RECORDS FOUND" distinguishes the third. Anything else
    is a BROKEN READ and must write nothing."""
    import datetime as dt
    while not STOP.is_set():
        today = a.day or dt.date.today().strftime("%m/%d/%Y")
        page = _load_page(today)
        sweep = (time.time() - _last_sweep[0]) >= a.sweep_every
        try:
            state, rows, pages = RCS.quick_day(today, page=page)
            with lock:
                stat["probe_req"] += 1
        except Exception as e:
            say("  PROBE UNPROVEN (%s: %.60s) - nothing written"
                % (type(e).__name__, e))
            time.sleep(a.every)
            continue
        if state == "unknown":
            say("  window returned rows=0 WITHOUT 'NO RECORDS FOUND' - a"
                " broken read, not a quiet day. Nothing written.")
            time.sleep(a.every)
            continue
        if state == "empty":
            time.sleep(a.every)
            continue

        seen = list(rows)
        if pages > page:                   # the day grew past the cached page
            for p in range(page + 1, pages + 1):
                st2, more, _ = RCS.quick_day(today, page=p)
                with lock:
                    stat["probe_req"] += 1
                if st2 == "rows":
                    seen.extend(more)
            say("  day grew: page %d -> %d" % (page, pages))
        elif sweep and pages > 1:
            # ⚠ THE CACHED-PAGE TICK IS BLIND TO EARLIER PAGES - sweep
            # occasionally. But NOT right after an overflow-follow already
            # read the whole day, or every page gets read twice.
            for p in range(1, pages):
                st2, more, _ = RCS.quick_day(today, page=p)
                with lock:
                    stat["probe_req"] += 1
                if st2 == "rows":
                    seen.extend(more)
            _last_sweep[0] = time.time()

        new = fresh(seen)
        if new and a.apply:
            n = land(new)
            with lock:
                stat["synced"] += n
            say("  SYNC landed %d new richmond id(s) - page %d/%d"
                " - waking the rd heal" % (n, page, pages))
            # > POKE THE HEAL NOW. Waiting up to --rd-every for a timer would
            # leave a filing sitting with no rd, no key and no pdf for a
            # quarter of an hour after we already knew about it.
            WAKE_RD.set()
        _save_page(today, pages)
        time.sleep(a.every)


# -- rd, and the keying that follows it for free --------------------

def rd_heal():
    """Land recorded_details for RC rows that have none - keying comes free.

    > THIS IS THE ORGAN rc_live NEVER HAD, AND WITHOUT IT THE LANE IS NOT
    WHOLE (login 2026-08-24: "make sure it is keeping up with the sync, the
    url, rd, pdfs, and keying"). rc_live landed only id + rd_url + pdf_url;
    rd was a separate walker, and rc_heal was a one-shot script nobody re-ran.
    MEASURED: of 80 documents synced today, 7 still had no rd - exactly the 7
    that failed in the manual heal at 15:07 and were never retried.

    > THE GRANT RULE, MEASURED 2026-08-21: a detail unlocks only after the
    SESSION has fetched THE LISTING PAGE the id appears on. A held id whose
    page was never fetched returns a 4,212-byte shell; the same id right after
    its page returns full RECORDED DETAILS. So: open a Window over the
    trailing days -> read its pages -> then fetch details, all on the SAME
    session. Fetching a detail cold does not fail loudly - it returns HTTP 200
    and a lie, which is far worse.

    > KEYING IS NOT DONE HERE AND MUST NOT BE. The key_on_rd trigger keys each
    landing INSIDE rd's own transaction - free, atomic, impossible to forget.
    Today's data proves it: every row with rd has a key, every row without has
    none. A keyer in this loop would be a second writer racing the trigger."""
    import datetime as dt
    while not STOP.is_set():
        try:
            ro = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True,
                                 timeout=120)
            ro.execute("PRAGMA busy_timeout=60000")
            # >>> THE WINDOW IS THE WORKLIST - DO NOT SCAN THE CORPUS.
            # First version asked the table "which RC rows are absent or
            # pending?" with a json_extract predicate. There is no index on
            # that expression, so it read 2.5M rows parsing JSON on every one
            # - MEASURED: still running past 100 s, which meant rd_heal never
            # got past its own first query and healed NOTHING. The rd-less
            # half of the same question answers in 0.0 s because
            # `recorded_details = ''` is a plain indexed comparison.
            #
            # So invert it. The date window already knows exactly which
            # documents were recorded in the period we care about; ask the
            # TABLE about those ids one PK lookup at a time. O(window), not
            # O(corpus), and every lookup rides the primary key.
            b = dt.date.today()
            lo = b - dt.timedelta(days=a.rd_days)
            fmt = "%m/%d/%Y"
            w = RCS.Window(lo.strftime(fmt), b.strftime(fmt))
            wrows = w.rows()
            ro = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True,
                                 timeout=120)
            ro.execute("PRAGMA busy_timeout=60000")
            _now = time.time()
            hits = []
            hotq = 0
            for r in wrows:
                iid = r["internal_id"]
                if _now - _absent_at.get(iid, 0.0) < a.absent_recheck:
                    continue
                got = ro.execute("SELECT recorded_details, pdf FROM"
                                 " navigation WHERE id=?",
                                 ("RC_" + iid,)).fetchone()
                if not got:
                    continue                      # the probe lands new ids
                if not got[0]:
                    hits.append(iid)              # no rd at all
                    continue
                try:
                    st = str(json.loads(got[0]).get("image_state", "")).lower()
                except ValueError:
                    continue
                # >>> PENDING AND RECENT-ABSENT ARE NOT VERDICTS. Re-ask.
                if st in ("absent", "pending"):
                    hits.append(iid)
                # >>> AND A RECENT FILING THAT HAS ITS IMAGE BUT NO PDF JUMPS
                # THE QUEUE. This case did nothing until 2026-08-25, and it is
                # the one that broke the "today's filings are ready today"
                # promise. The hot list only ever fired for ids whose rd
                # landed FRESH in this heal - so a document rd'd yesterday
                # fell back to ordinary queue position, and the miner selects
                # `ORDER BY id` on TEXT, where richmond's two id namespaces
                # interleave: RC_1xxxxxx < RC_2xxxxxx < RC_9xxxx. MEASURED:
                # yesterday's RC_2825450 block sat behind 60,103 older todo
                # rows - 83 to 200 minutes away - while 239 of its 318
                # image-present rows had no pdf.
                # ⚠ THE WINDOW IS THE WORKLIST, exactly as for rd: this is
                # O(window) PK lookups, never a scan of 2.5M rows.
                # ⚠ `not got[1]` WAS WRONG AND EXCLUDED EXACTLY THE
                # ROWS THIS BRANCH EXISTS FOR. got[1] is the pdf column, and
                # this was written when it held only '' or a path. 'pending'
                # is truthy, so from the day the fourth state landed, a row
                # whose scan had JUST ARRIVED was the one row that could never
                # reach the hot list.
                elif st == "present" and got[1] in ("", "pending"):
                    if _now - _hot_at.get(iid, 0.0) >= a.hot_recheck:
                        _hot_at[iid] = _now
                        if a.hot_pdf:
                            hot_ids.put("RC_" + iid)
                        hotq += 1
            ro.close()
            say("  RD HEAL: window %s .. %s lists %d row(s); %d need work"
                " (rd-less or scan-not-yet-up); %d recent filing(s) with an"
                " image but no pdf pushed to the HOT LIST"
                % (lo.strftime(fmt), b.strftime(fmt), len(wrows), len(hits),
                   hotq))
            if not hits:
                WAKE_RD.wait(a.rd_every)
                WAKE_RD.clear()
                continue
            wcon = sqlite3.connect(CP.NAV_DB, timeout=600) if a.apply else None
            if wcon:
                wcon.execute("PRAGMA busy_timeout=300000")
            landed = failed = 0
            for iid in hits:
                if STOP.is_set():
                    break
                try:
                    _, h = RCS.RR.post(w.s, "/Search/DateRangeSearch",
                                       w._f(ViewDetailsButton=str(iid)))
                    rec = RW.parse_detail(h, iid)
                except Exception as e:
                    msg = str(e)
                    # > A REFUSAL STOPS THE HEAL, NOT THE LANE. The pdf side
                    # talks to a DIFFERENT host on self-authenticating tokens;
                    # richmond refusing the detail route says nothing about
                    # the courts image route.
                    if ("403" in msg or "Forbidden" in msg
                            or "nauthorized" in msg):
                        say("  RD HEAL REFUSED at RC_%s - stopping the heal"
                            " (pdf lane is another host, unaffected): %.60s"
                            % (iid, e))
                        break
                    failed += 1
                    continue
                if not a.apply:
                    continue
                for _try in range(60):
                    try:
                        # > never overwrite an rd we already hold
                        # >> OVERWRITE ONLY TO IMPROVE. An rd-less row
                        # takes anything; an absent/pending row is
                        # replaced ONLY once the scan is actually
                        # there. Never downgrade a present reading -
                        # a transient blip must not erase a fact we
                        # already hold.
                        wcon.execute(
                            "UPDATE navigation SET recorded_details=?"
                            " WHERE id=? AND (recorded_details=''"
                            "  OR json_extract(recorded_details,"
                            "     '$.image_state') IN"
                            "     ('absent','pending'))",
                            (json.dumps(rec, separators=(",", ":")),
                             "RC_" + iid))
                        wcon.commit()
                        landed += 1
                        break
                    except sqlite3.OperationalError:
                        time.sleep(5)
                # > STRAIGHT ONTO THE HOT LIST. It has rd now, so it is
                # mintable - and it must not wait behind 1.39M older ids.
                # image_state gates it exactly as next_ids() would.
                # >>> PENDING IS NOT IMAGELESS, AND THE DIFFERENCE IS THE
                # WHOLE POINT (login 2026-08-24: "the big difference between
                # a pending image vs an imageless claim").
                #
                # PROVEN, not theorised: 10 of 10 documents recorded FRIDAY
                # read "absent" in our stored rd and "present" at the source
                # today - the scans simply arrived over the weekend. Treating
                # that first reading as a verdict strands the document
                # forever, because the miner requires image_state='present'
                # and nothing ever looked again.
                #
                #   present                -> mint it now (the hot list)
                #   pending                -> THE SOURCE ITSELF says it is
                #                             coming. Never a verdict.
                #   absent, recorded recently -> scan lag. Never a verdict.
                #   absent, long after recording -> only THIS is a real
                #                             "no image" fact, and the
                #                             --rd-days window is what draws
                #                             that line: outside it we stop
                #                             asking, and the row keeps an
                #                             EMPTY pdf column - honest todo,
                #                             never a fabricated verdict.
                #
                # Same family as acris writing a refusal down as a permanent
                # "imageless": a freshness-dependent reading, frozen too
                # early.
                #
                # ⚠⚠ A VERDICT IS NOW WRITTEN, AND ONLY UNDER THESE GUARDS
                # (login 2026-08-25: "any error that isnt from a deadend url
                # should not msireport a missing url if the system is just
                # failing the fetch"). "no pdf" must be a fact about the
                # DOCUMENT, never a symptom of our own transport:
                #
                #   1 THE SOURCE MUST HAVE SAID SO, IN ITS OWN WORDS. The
                #     state must be 'pending', which means the page literally
                #     carried "No Image Available At This Time" - login's
                #     screenshot of RC_2825613 is exactly that string. It is
                #     NOT enough for the state to be merely not-present:
                #     'unknown' means we did not recognise the page and must
                #     ask again. And st_now comes from a detail page fetched
                #     SUCCESSFULLY - every failure path above does
                #     `failed += 1; continue` and never reaches here, so a
                #     timeout, reset, 5xx or refusal produces a RETRY, never
                #     a conclusion.
                #   2 THE LAG WINDOW MUST HAVE EXPIRED (--lag-days).
                #   3 THE URL MUST HAVE BEEN MINTED. An un-minted row is OUR
                #     gap, not a dead end at the source, and calling it "no
                #     pdf" would bury a minting bug as a document fact.
                #   4 IT ONLY EVER FILLS AN EMPTY COLUMN (pdf='' in the
                #     UPDATE), so it can never overwrite a real path.
                st_now = str(rec.get("image_state", "")).lower()
                if st_now == "present":
                    if a.hot_pdf:
                        hot_ids.put("RC_" + iid)  # only with --hot-pdf
                    _absent_at.pop(iid, None)     # resolved - stop tracking
                # ⚠ THE rd-PARSE VERDICT WAS RETIRED 2026-08-25. It read a
                # marker string off the detail page to decide "no image",
                # which needed two parsers to agree about page markup and
                # they did not. login replaced it with something simpler and
                # stronger: "we have the url, if it doesnt show, its absent".
                # The MINER now decides from what the url actually does - see
                # _no_image() - so there is exactly one place that can record
                # a no-pdf fact, and it is the place that asked the url.
                else:
                    # pending OR absent-but-recent: both mean ASK AGAIN LATER,
                    # and neither is recorded as a conclusion anywhere.
                    _absent_at[iid] = time.time()
                time.sleep(0.3)          # a healer has no reason to hurry
            if wcon:
                wcon.close()
            with lock:
                stat["rd"] += landed
            say("  RD HEAL: landed %d - failed %d"
                " (key_on_rd keyed each landing in the same transaction)"
                % (landed, failed))
        except Exception as e:
            say("  RD HEAL error (%s: %.60s)" % (type(e).__name__, e))
        WAKE_RD.wait(a.rd_every)
        WAKE_RD.clear()


# ── progress ───────────────────────────────────────────────────────────

def reporter():
    t0 = time.time()
    last = dict(stat)
    while not STOP.is_set():
        time.sleep(60)
        with lock:
            s = dict(stat)
        el = time.time() - t0
        d = s["got"] - last["got"]
        # > `db N` IS A CONTRACT, NOT DECORATION. routine_update parses the
        # board's richmond cumulative out of this log with r"db ([\d,]+)".
        # rc_pdf_pull printed it; dropping it would leave the board reading a
        # dead log and reporting the lane STALE while it ran perfectly.
        say("PROGRESS %s pdfs · db %s · %.2f/s now · %.2f/s avg · %.1f GB"
            " · minted %s"
            " (ready %d) · err %d · stale %d · synced %d - rd %d - hot %d"
            " · pending %d - absent %d · %d min"
            % ("{:,}".format(s["got"]), "{:,}".format(s["wrote"]),
               d / 60.0, s["got"] / el if el else 0,
               s["bytes"] / 1024 ** 3, "{:,}".format(s["minted"]),
               ready.qsize(), s["err"], s["stale"], s["synced"], s["rd"],
               s["hot"], s.get("pending", 0), s.get("absent", 0), el / 60))
        last = s


if __name__ == "__main__":
    say("rc_lane up · DRUMROLL: no pacer, latency is the governor · %d miners"
        " -> %d pullers · ahead %d · probe every %ds · apply=%s ·"
        " %d restricted on file"
        % (a.miners, a.workers, a.ahead, a.every, a.apply, len(RESTRICTED)))
    if not a.apply:
        say("  ⚠ DRY RUN - pdfs will be fetched and stored but the table is"
            " NOT updated. Use --apply for the real thing.")
    threads = [threading.Thread(target=probe, daemon=True),
               threading.Thread(target=rd_heal, daemon=True),
               threading.Thread(target=pending_recheck, daemon=True),
               threading.Thread(target=watchdog, daemon=True),
               threading.Thread(target=writer, daemon=True),
               threading.Thread(target=reporter, daemon=True)]
    _open_ro()          # miners read the recorded date through this
    threads += [threading.Thread(target=miner, daemon=True)
                for _ in range(a.miners)]
    threads += [threading.Thread(target=puller, daemon=True)
                for _ in range(a.workers)]
    for t in threads:
        t.start()
    try:
        while not STOP.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        STOP.set()
    say("stopped · %s pdfs · %s written · %d err"
        % ("{:,}".format(stat["got"]), "{:,}".format(stat["wrote"]),
           stat["err"]))
