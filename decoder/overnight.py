"""RUN THE WALK UNATTENDED: parcel -> documents -> PDFs -> organised folder.

    ACRIS_CORPUS_ROOT=D:/acris python -u overnight.py --procs 6 --conc 12 --until 05:00

⚠ WHY A DRIVER AND NOT A BIGGER --docs. acquire_async.py fetches; it does not decide
what to fetch next, and it does not build the human view. Login, 2026-08-17 22:15,
going to bed: *"acqusition actively pulling documents to their dedicated bbl/parcel...
I open a parcel folder to see the index in pdf form of the doc tiffs."* That is three
steps per parcel, and the third is the one that makes the corpus readable.

⚠ PARCELS ARE THE UNIT OF WORK, AND WHOLE PARCELS ARE THE POINT. A half-acquired
parcel is not half as useful — the walk is chronological, so a gap in the middle is a
hole in the reasoning. Each batch is materialised the moment its documents land, so a
folder is either being filled or complete, never abandoned silently.

⚠ STOP DEAD ON REFUSAL, RUN-SCOPED. The phase doc records a scoping bug where the stop
Event lived INSIDE the retry loop, so each batch built a fresh one and the log printed
"stopping" six times while the run carried on. Here the flag is a FILE on disk
(`_STOP`), checked before every batch and written by any worker that sees a refusal —
it cannot be scoped away, and it survives a driver restart. The limiter is
address-level: pushing through costs Login their own ACRIS access.

⚠ CONCURRENCY IS PER PROCESS AND PROCESSES ARE THE LEVER. Measured 2026-08-17:
conc 48 in ONE process was SLOWER than conc 24 (20.5 vs 32.0 pg/s), while 8 processes
x conc 8 reached 40.6 pg/s at 30.8% mean CPU — not CPU-bound, not network-bound.
Scale processes, not threads.
"""
from __future__ import annotations

import argparse, datetime, os, pathlib, sqlite3, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
import corpus_paths as CP
ROOT = CP.ROOT
DB = CP.SPEC_DB
STOP = CP.STOP
LOG = CP.log("overnight")


def say(msg):
    line = f"[{datetime.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def parcels(limit, lo, hi, boro):
    """⚠ ORDER IS DELIBERATE: deepest first inside the band. A parcel with 60 documents
    teaches more per request than sixty parcels with one. The band excludes the
    administrative giants (block 99999 carries 45,644 documents on one BBL and is not a
    parcel in any physical sense) and the single-document lots that cost a round trip
    to learn nothing."""
    # ⚠ READ-ONLY. The delta writes this file on a schedule; a write handle we
    # never use would still contend for the lock. See LIVE_SYNC.md §9.
    # ⚠ --boro TAKES A LIST. "1,2,3,4" is non-Staten-Island in ONE run. Before
    # 2026-08-19 it took a single digit, so covering four boroughs meant four
    # separate runs each with its own pool, and the deepest-first ordering was
    # per-run rather than global - a 60-document Manhattan parcel would wait
    # behind a 9-document Queens one. One run, one ordering, one stop flag.
    boros = [b.strip() for b in str(boro).split(",") if b.strip()]
    like = " OR ".join(["bbl LIKE ?"] * len(boros))
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    q = con.execute(
        "SELECT bbl, n_docs FROM parcel WHERE n_docs BETWEEN ? AND ? "
        f"AND ({like}) AND substr(bbl,2,5) <> '99999' "
        "ORDER BY n_docs DESC LIMIT ?",
        tuple([lo, hi] + [f"{b}%" for b in boros] + [limit]))
    out = q.fetchall()
    con.close()
    return out


def ledger_totals():
    """(documents, pages) recorded ok. ⚠ Read from the ledger the workers write, so the
    driver never reports progress it merely inferred."""
    led = CP.LEDGER
    if not led.exists():
        return (0, 0)
    try:
        c = sqlite3.connect(f"file:{led}?mode=ro", uri=True)
        r = c.execute("SELECT COUNT(*), COALESCE(SUM(got),0) FROM doc "
                      "WHERE status='ok'").fetchone()
        c.close()
        return (r[0] or 0, r[1] or 0)
    except sqlite3.Error:
        return (0, 0)


def acquired(bbl):
    """How many of this parcel's documents already have a PDF on disk."""
    store = CP.STORE
    # ⚠ READ-ONLY. The delta writes this file on a schedule; a write handle we
    # never use would still contend for the lock. See LIVE_SYNC.md §9.
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    docs = [r[0] for r in con.execute(
        "SELECT DISTINCT document_id FROM parcel_document WHERE bbl=?", (bbl,))]
    con.close()
    return sum((store / d[:2] / f"{d}.pdf").exists() for d in docs), len(docs)


# ------------------------------------------------------------------ link gate
PROBE = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentSearchCriteria"
try:
    from fetch_pages import UA as UA_PROBE
except Exception:                      # never let the gate be the reason nothing runs
    UA_PROBE = "acris-decoder/1.0"


def link_up(timeout=15):
    """Is the link (and ACRIS) answering at all? One cheap GET, no image."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(
            PROBE, headers={"User-Agent": UA_PROBE})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500          # a 4xx still proves the link is up
    except Exception:
        return False


def hold_for_link(say):
    """⚠ AN OUTAGE MUST NOT END THE NIGHT.

    Login, 2026-08-20: *"a brief connection drop derails a night work ... we need
    to build a resume when that happens."* The Richmond pull has had exactly this
    gate since 2026-08-18 (`rc_detail_pull.hold_for_link`) and acquisition never
    got it - the rule existed, in this repo, unused, which is this project's
    recurring shape.

    Block until the link returns. The caller RE-SUBMITS the same batch, so the
    worklist is never consumed by an outage. Probes every 15s and says so every
    5 minutes, because a silent hold is indistinguishable from a hang."""
    t0 = time.time()
    say("** LINK DOWN - holding; batch NOT consumed, worklist intact")
    waited = 0
    while not link_up():
        time.sleep(15)
        waited += 15
        if waited % 300 == 0:
            say(f"   still down after {waited // 60} min")
    el = time.time() - t0
    say(f"** LINK BACK after {el / 60:.1f} min - resuming where it left off")
    return el


def run_batch(bbls, conc, docs_cap):
    """One acquire_async process over a batch of parcels. Returns (pages, refused)."""
    # ⚠ --max-pages MUST BE RAISED OR EVERY PARCEL TRUNCATES AT ~150 DOCUMENTS.
    # acquire_async defaults to 1800 pages and, for a parcel pick, charges an ESTIMATED
    # 12 pages per document because the spec index carries no page count — so the cap
    # bites at 1800/12 = 150 documents no matter how deep the parcel is. Measured
    # 2026-08-17: BBL 4071170051 has 234 documents, selection returned all 234, the
    # ledger had never even attempted 49 of them, and the folder read "not acquired"
    # forever. Selection was right; a stopping rule nobody passed was the cause.
    # A cap is a stopping rule, not a corruption rule — so size it past the work.
    cmd = [sys.executable, "-u", str(HERE / "acquire_async.py"),
           "--docs", str(docs_cap), "--conc", str(conc),
           "--max-pages", str(docs_cap * 12 + 20000)]
    for b in bbls:
        cmd += ["--parcel", b]
    env = dict(os.environ, ACRIS_CORPUS_ROOT=str(ROOT))
    try:
        # ⚠ encoding= IS LOAD-BEARING, NOT TIDINESS. text=True decodes with the Windows
        # locale codec (cp1252), which mangles the run banner's box-drawing characters —
        # the page parser silently returned 0 for every batch that actually fetched
        # hundreds of pages. The REFUSAL CHECK reads the same string, so a mangled
        # decode could have swallowed the one signal that must never be missed.
        p = subprocess.run(cmd, capture_output=True, timeout=3600, env=env,
                           encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return 0, False
    out = (p.stdout or "") + (p.stderr or "")
    return out, classify(out)


# ------------------------------------------------------------------ classify
# The five notice phrases _check_denied() matches. A REFUSAL means ACRIS SAID SO.
_NOTICE = ("further access to acris is denied",
           "acris bandwidth notice",
           "automated scripts/robots",
           "exceeded the bandwidth limits",
           "subscription data services",
           "acris is refusing service")      # AccessDenied's own message

# Transport failures. Every one of these is the LINK, not the server's policy.
_TRANSPORT = ("connectionrefusederror", "connectionreseterror",
              "connectionaborted", "connectionerror", "clientconnectorerror",
              "serverdisconnectederror", "clientoserror", "clientpayloaderror",
              "timeouterror", "timed out", "cannot connect to host",
              "getaddrinfo failed", "gaierror", "name or service not known",
              "temporary failure in name resolution", "ssl", "eof occurred",
              "winerror 10054", "winerror 10060", "winerror 10061",
              "winerror 10065", "winerror 11001", "network is unreachable",
              "no route to host", "remote end closed connection")


def classify(out):
    """"ok" | "refused" | "linkdown".

    ⚠ THIS REPLACES A SUBSTRING MATCH THAT COST A WHOLE NIGHT. It read:

        refused = ("REFUS" in out.upper() or "AccessDenied" in out ...)

    and **ConnectionRefusedError - the ordinary result of a wifi drop - contains
    "Refused"**. On 2026-08-19 at 23:49 a brief connection loss was therefore
    reported as "REFUSED by ACRIS", the run wrote a refusal _STOP and halted, and
    the night's acquisition ended after 5 parcels. The evidence that it was never
    a refusal: `refusals.jsonl` was never created (so no HTTP refusal was ever
    logged), and the driver's own detail scan found NONE of the notice phrases -
    it recorded "(no signal detail captured)". The single most common transport
    error in Python contains the word the safety check was keyed on.

    So: **a refusal requires POSITIVE evidence that ACRIS said no.** Anything
    that is merely a broken connection is the link, and the link comes back.

    Order matters: notice phrases are checked FIRST, so a genuine bandwidth
    notice still stops everything even if the batch also logged socket noise."""
    low = out.lower()
    if any(sig in low for sig in _NOTICE):
        return "refused"
    if any(sig in low for sig in _TRANSPORT):
        return "linkdown"
    return "ok"


def only_one(tag):
    """⚠ REFUSE TO BE THE SECOND COPY. Restarting the run by hand left 6 drivers and 4
    watchdogs alive at once on 2026-08-17 — and because each watchdog restarts a driver
    it believes is missing, duplicates BREED rather than merely accumulate. Every copy
    then draws on the same address-level limiter while each one thinks it is the only
    client, which is exactly the pattern the phase doc forbids.

    A PID file alone is not enough: a killed process leaves its file behind. Check that
    the recorded PID is BOTH alive AND running this same script before yielding to it."""
    import os as _os
    pf = CP.pid_file(tag)
    try:
        import psutil
        if pf.exists():
            old = int(pf.read_text().strip() or 0)
            if old and psutil.pid_exists(old):
                try:
                    cl = " ".join(str(x) for x in (psutil.Process(old).cmdline() or []))
                    if f"{tag}.py" in cl:
                        print(f"  {tag}: pid {old} is already running — refusing to start a second copy")
                        raise SystemExit(0)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        pf.write_text(str(_os.getpid()), encoding="utf-8")
    except SystemExit:
        raise
    except Exception:
        pass          # ⚠ the guard must never be the reason nothing runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=6)
    ap.add_argument("--conc", type=int, default=12)
    ap.add_argument("--batch", type=int, default=1, help="parcels per process")
    ap.add_argument("--docs-cap", type=int, default=3000, help="max docs per process call")
    ap.add_argument("--until", default="05:00")
    ap.add_argument("--lo", type=int, default=8)
    ap.add_argument("--hi", type=int, default=300)
    ap.add_argument("--boro", default="4",
                    help="borough digit, or a comma list: 1,2,3,4 = non-Staten-Island")
    ap.add_argument("--pool", type=int, default=6000)
    a = ap.parse_args()
    only_one("overnight")

    # ⚠ A REFUSAL STOP IS A HUMAN'S DECISION, NOT A STALE FLAG.
    # This used to unlink _STOP unconditionally. The refusal path writes
    # "refused <when>" into that file and says "Delete _STOP to resume later" -
    # meaning a person looks first. But night_chain restarts acquisition after
    # the 4am sync, and an unconditional unlink would have ERASED a refusal and
    # resumed against the source that refused us, which the standing rule
    # forbids ("on a refusal: stop; do not retry, do not rotate anything").
    # Any OTHER stop (the chain's own "night_chain stop") is a control flag and
    # is cleared as before.
    if STOP.exists():
        _why = STOP.read_text(encoding="utf-8", errors="replace")
        if "refus" in _why.lower() or "denied" in _why.lower():
            print("REFUSAL STOP PRESENT - NOT STARTING.", flush=True)
            print(f"  {STOP}", flush=True)
            for _ln in _why.splitlines():
                print(f"  | {_ln}", flush=True)
            print("  A person must read this and delete the file deliberately.",
                  flush=True)
            return 2
        STOP.unlink()
    hh, mm = (int(x) for x in a.until.split(":"))
    now = datetime.datetime.now()
    end = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if end <= now:
        end += datetime.timedelta(days=1)

    # ⚠ THE CAP MUST CLEAR THE BATCH OR PARCELS COME OUT HALF-BUILT. Measured
    # 2026-08-17 with batch=3 / cap=400 against a 8-300 doc band: only 6 of 55 parcels
    # finished, the rest frozen mid-chronology at exactly the cap. A half-acquired
    # parcel is not half a parcel — the walk is ordered, so the hole is in the middle
    # of the story and nothing downstream can tell a gap from an ending. The driver
    # never revisits, so "finish later" meant "never".
    need = a.batch * a.hi * 2          # x2 headroom for lineage predecessors
    if a.docs_cap < need:
        say(f"⚠ docs-cap {a.docs_cap} < batch*hi*2 ({need}) — parcels WILL truncate; "
            f"raising to {need}")
        a.docs_cap = need

    say(f"OVERNIGHT START  procs={a.procs} conc={a.conc} batch={a.batch} "
        f"boro={a.boro} docs {a.lo}-{a.hi}  until {end:%Y-%m-%d %H:%M}")
    pool = parcels(a.pool, a.lo, a.hi, a.boro)
    say(f"pool: {len(pool):,} parcels, {sum(n for _, n in pool):,} documents")

    # ⚠ SKIP WHAT IS ALREADY WHOLE. The pool is deterministic and always starts at the
    # top, so a restart re-walks every finished parcel: the ledger's `done` filter means
    # nothing is fetched, but a process is still spawned per group and the spec read for
    # each. Measured 2026-08-17: 14 minutes and 0 pages after restarting at 608 parcels.
    # A parcel whose manifest reports no outstanding documents is finished; reading that
    # file is far cheaper than re-deriving the answer.
    # ⚠ TWO MARKERS MEAN OUTSTANDING, NOT ONE. `pending scan` is a document that
    # returned the placeholder while still inside the image lag window
    # (image_policy.TERMINAL_DAYS=7) — we asked, and the scan may yet attach on day 3
    # or day 6. Testing only for `not acquired` retired those parcels as COMPLETE the
    # first time they were walked, so the image landed and nothing ever came back for
    # it: a permanent silent loss that every count reported as clean. Old manifests
    # predate the marker and are unaffected, so this is safe to apply to what is
    # already on disk. See parcel_folder.empty_ids().
    OUTSTANDING = ("| not acquired |", "| pending scan |")
    finished = set()
    for f in CP.BYPARCEL.rglob("_INDEX.md"):
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
            if any(m in txt for m in OUTSTANDING):
                continue
            d = f.parent
            finished.add(f"{d.parent.parent.name}{d.parent.name}{d.name}")
        except OSError:
            continue
    queue = [b for b, _ in pool if b not in finished]
    say(f"skipping {len(finished):,} parcels already complete -> {len(queue):,} to walk")
    i = tot_pages = tot_parcels = 0
    # ⚠ BASELINE THE LEDGER. It is shared and resumable, so its absolute total includes
    # every earlier run; only the DELTA is this run's work.
    start_pages = ledger_totals()[1]
    t0 = time.time()
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # ⚠ NO ROUND BARRIER. The first shape submitted `procs` parcels and waited for ALL
    # of them before starting the next batch — so with a band of 8-300 documents, seven
    # workers idled while the biggest parcel finished, every single round. Wall clock
    # became "slowest parcel per round" instead of "total work / workers". Measured
    # 52.8-54.7 pg/s with 64 connections in flight, against ~116 pg/s implied by 64
    # documents at a 4.13s mean — the missing half was the barrier.
    #
    # This is a CONTINUOUS POOL: a worker that finishes takes the next parcel
    # immediately and nothing waits on anything else.
    pending, done_bbls, last_say = {}, [], time.time()
    outages = []                       # seconds held, one per outage
    ex = ThreadPoolExecutor(max_workers=a.procs)

    def submit_next():
        nonlocal i
        while len(pending) < a.procs and i < len(queue):
            g = queue[i:i + a.batch]
            i += a.batch
            if g:
                pending[ex.submit(run_batch, g, a.conc, a.docs_cap)] = g

    def materialise(bbls):
        """⚠ ONE CALL for many parcels — parcel_folder.py re-reads the 138,867-line
        image-less gzip per invocation, so per-parcel calls paid it N times."""
        if not bbls:
            return 0
        try:
            cmd = [sys.executable, str(HERE / "parcel_folder.py")]
            for b in bbls:
                cmd += ["--bbl", b]
            subprocess.run(cmd, capture_output=True, timeout=1800,
                           env=dict(os.environ, ACRIS_CORPUS_ROOT=str(ROOT)))
        except Exception:
            pass
        return len(bbls)

    submit_next()
    while pending and datetime.datetime.now() < end:
        if STOP.exists():
            say("⚠ _STOP present — halting"); break
        fin = next(as_completed(list(pending)), None)
        if fin is None:
            break
        grp = pending.pop(fin)
        try:
            _out, verdict = fin.result()   # ⚠ _out is EVIDENCE on refusal
        except Exception:
            _out, verdict = "", "ok"
        if verdict == "linkdown":
            # ⚠ RE-SUBMIT THE SAME BATCH. The parcels in `grp` were not acquired
            # and must not be counted as done - an outage that silently consumed
            # the worklist would leave holes that no failure count reports.
            outages.append(hold_for_link(say))
            pending[ex.submit(run_batch, grp, a.conc, a.docs_cap)] = grp
            continue
        if verdict == "refused":
            # ⚠ PERSIST WHY, NOT JUST THAT. Until 2026-08-18 this wrote the bare word
            # "refused" and discarded `_out` — which carries AccessDenied's message
            # naming WHICH notice signals matched. At the one moment the system most
            # needs evidence, it was throwing the evidence away, leaving a human to
            # choose between "wait a day" and "we are blocked" with nothing to go on.
            detail = ""
            try:
                for ln in (_out or "").splitlines():
                    if any(k in ln.lower() for k in
                           ("refusing service", "denied", "bandwidth", "robot",
                            "subscription")):
                        detail += ln.strip() + chr(10)
            except Exception:
                pass
            STOP.write_text(
                f"refused {datetime.datetime.now():%Y-%m-%d %H:%M}" + chr(10)
                + (detail or "(no signal detail captured)"), encoding="utf-8")
            say("⚠ REFUSED by ACRIS — stopping the run, no retry. "
                "Delete _STOP to resume later.")
            break
        done_bbls += grp
        submit_next()                      # ⚠ refill immediately; never drain to empty
        # ⚠ MATERIALISE IN GROUPS, NOT PER PARCEL — but never let a parcel sit
        # unmaterialised for long, or a folder the user opens is missing its index.
        if len(done_bbls) >= a.procs or (not pending and done_bbls):
            tot_parcels += materialise(done_bbls); done_bbls = []
        if time.time() - last_say >= 60:
            last_say = time.time()
            el = time.time() - t0
            d, pg = ledger_totals()
            tot_pages = pg - start_pages
            say(f"{tot_parcels:>5} parcels done · {len(pending)} in flight · "
                f"{pg:>10,} pages / {d:,} docs · "
                f"{tot_pages/max(1,el):.1f} pg/s avg · {el/60:.0f} min")

    tot_parcels += materialise(done_bbls)
    ex.shutdown(wait=False, cancel_futures=True)
    tot_pages = ledger_totals()[1] - start_pages

    say(f"DONE  {tot_parcels} parcels, {tot_pages:,} pages, "
        f"{(time.time()-t0)/60:.0f} min, {tot_pages/max(1,time.time()-t0):.1f} pg/s avg")


if __name__ == "__main__":
    # ⚠ PROPAGATE THE CODE. main() returns 2 when it declines to start on a
    # refusal stop; swallowing that would report a clean run to whatever
    # launched us, which is how a refusal becomes invisible.
    sys.exit(main() or 0)
