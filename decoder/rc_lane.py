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
ap.add_argument("--ahead", type=int, default=1200,
                help="minted tokens kept ready ahead of the pullers")
ap.add_argument("--batch", type=int, default=3,
                help="tokens a puller takes per turn")
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

ready = queue.Queue()                     # (did, location, minted_at)
DBQ = queue.Queue(maxsize=10000)          # (did, relpath) -> the ONE writer
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
        "wrote": 0, "stale": 0, "synced": 0, "probe_req": 0}
last_ok = [time.time()]

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
        quiet = time.time() - last_ok[0]
        if quiet >= a.stall_after and not HOLD.is_set():
            recycle_session("no successful pull for %.0fs - presuming the"
                            " route changed under us" % quiet)
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
        " AND recorded_details != '' AND pdf = ''"
        " AND json_extract(recorded_details, '$.image_state') = 'present'"
        " ORDER BY id LIMIT ?",
        (n + len(served_ids) + len(have_raw),)).fetchall()
    con.close()
    return [r[0] for r in rows
            if r[0] not in served_ids and r[0] not in have_raw][:n]


def miner():
    """⚠ A MINER MUST NEVER DIE. A bare exception here silently killed all
    six threads at startup once and minting sat at 0 while the lane looked
    healthy - hence the outer guard as well as the inner one."""
    while not STOP.is_set():
      try:
        if ready.qsize() >= a.ahead or HOLD.is_set():
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
                loc = None
                try:
                    with tl.op.open(req, timeout=60):
                        pass
                except urllib.error.HTTPError as e:
                    # ⚠ THE 302 IS THE PRODUCT. The pdf does NOT live on
                    # richmond: the Location points at the NY State courts
                    # viewer with a self-authenticating token.
                    loc = (e.headers.get("Location")
                           if e.code in (301, 302, 303) else None)
                if loc:
                    ready.put((did, loc, time.time()))
                    with lock:
                        stat["minted"] += 1
                else:
                    with lock:
                        stat["skipped"] += 1
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
    ro = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=120)
    ro.execute("PRAGMA busy_timeout=60000")
    while not STOP.is_set():
        while HOLD.is_set() and not STOP.is_set():
            time.sleep(5)
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
            r = _SESS[0].get(loc, timeout=(10, 90))
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
                con.executemany("UPDATE navigation SET pdf=? WHERE id=?",
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
            say("  SYNC landed %d new richmond id(s) · page %d/%d"
                % (n, page, pages))
        _save_page(today, pages)
        time.sleep(a.every)


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
        say("PROGRESS %s pdfs · %.2f/s now · %.2f/s avg · %.1f GB · minted %s"
            " (ready %d) · err %d · stale %d · synced %d · %d min"
            % ("{:,}".format(s["got"]), d / 60.0, s["got"] / el if el else 0,
               s["bytes"] / 1024 ** 3, "{:,}".format(s["minted"]),
               ready.qsize(), s["err"], s["stale"], s["synced"], el / 60))
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
               threading.Thread(target=watchdog, daemon=True),
               threading.Thread(target=writer, daemon=True),
               threading.Thread(target=reporter, daemon=True)]
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
