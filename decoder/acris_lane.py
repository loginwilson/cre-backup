"""THE CONSOLIDATED ACRIS LANE — one process, one access point, one workflow.

    python acris_lane.py --apply --workers 28        # the real thing

⚠⚠ THE RAMP LAW — NEVER COLD-LAUNCH THIS LANE (login, 2026-08-24 13:03):
"you cant cold launch the code... it needs to ramp and not just restart at
80 or whatever." A restart that fires every worker at once opens ~80 cold
TLS connections in one second - ACRIS served its Bandwidth Notice ONE
SECOND after exactly such a relaunch (trip #3), after absorbing the
governor's gentle climb to width 52 all morning without complaint. The
ramp is CODED AS UNAVOIDABLE below (pdf width always starts at RAMP_START
and climbs; rd workers stagger 0.5s apart) - do not add any launch path
that bypasses it, and treat every restart as a load event to be minimized
(width/tuning changes belong to the governor, not to relaunches).

Login's design (2026-08-24, docs/sources/acris/LIVE_SYNC.md "THE CONSOLIDATED
LANE"): ACRIS tripped its Bandwidth Notice twice while the edge-prober
(acris_live) and the doc-walkers (rd_walk x4) ran as SEPARATE python
processes - two behaviors under one IP. The theory (login's): ACRIS tolerates
ONE access point that maximizes workers, not multiple access points. So this
file IS the acris presence: the edge probe, the rd backfill, the ledger, and
the edge state all live in one process. When this runs, NOTHING ELSE may
touch ACRIS (acris_live and rd_walk must be stopped - it replaces them).

THE ROTATION (login: "constantly doing the rd, but every 10 seconds subbing
in the edge"): workers drain the backfill continuously; an edge thread runs
the probe every --every seconds. A probe hit IS the document - detection and
rd arrive in the same request (nothing to queue; the landing is a local
write and key_on_rd keys it in the same transaction). Only the pdf ever
queues, and that lane is parked separately. Bursts: the probe walks until
blanks + control re-prove level (the acris_live walk, unchanged).

REFUSAL DISCIPLINE: every fetch path catches BOTH fetch_pages.AccessDenied
and live_delta.Refused (the 09:00 lesson - a detector that fires into the
wrong except clause does not exist). On refusal the WORKERS stop for good;
the edge probe alone continues on exponential backoff as the resume
detector. Backfill resume after a refusal is LOGIN'S CALL (restart the
lane), never automatic - "resume another day" is the notice's own text.

Board: PROGRESS lines print "N total" like rd_walk's, so routine_update's
counter/heartbeat read this log (NAV_WORK\\acris_lane.log via redirect).

THE PDF POOL (login 2026-08-24: "build pdf into it too... one eta one code
that eventually results in the level ready to decode"): a third organ in the
same process - workers drain `pdf='' AND recorded_details!=''` through
acris_pdf.fetch_pdf (image_walk's body with every trap intact), and every
sync landing jumps the queue via the hot list so a new filing is fully
ready minutes after recording. Same access point, same refusal tripwire:
a notice on EITHER endpoint stops ALL workers, rd and pdf alike.

⚠ THE FRESHNESS CLAUSE (login: "a new doc id from the edge walk may very
well miss its image... the lag distribution"): TotalPages<=0 on a doc
recorded within --fresh-days is NOT an imageless verdict - the scan may
simply not be uploaded yet. Those are DEFERRED (pdf stays '', retried when
the feeder wraps), and only aged docs earn `pdf='imageless'`. A permanent
verdict must never be written on a temporary state.

READY TO DECODE = rd + (pdf|imageless) + key. Because pdf only ever follows
rd, ready = needed - pdf_todo exactly (ix_nav_pdf_todo, index-only), and
the board's synchronization row measures distance to a fully synchronized,
decode-ready mirror. That is the one rate and the one eta.
"""
from __future__ import annotations

import argparse
import contextlib
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

import acris_edge as AE                                        # noqa: E402
import acris_pdf as AP                                         # noqa: E402
import corpus_paths as CP                                      # noqa: E402
import fetch_pages                                             # noqa: E402
import live_delta as LD                                        # noqa: E402
import rd_parse as RD                                          # noqa: E402

EDGE_STATE = HERE / "_crfn_edge.json"
LEDGER_DB = (r"D:\CRE Decoding System\00 Synchronizations"
             r"\Legal Instruments Synchronization"
             r"\Legal Instruments Synchronization.db")
ACRIS_URL = "https://a836-acris.nyc.gov/DS/DocumentSearch/"
CONFIRM_BLANKS = 8
FAILS = CP.NAV_WORK / "acris_lane_fails.jsonl"
BATCH = 200

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--workers", type=int, default=28)
ap.add_argument("--pdf-workers", type=int, default=12)   # STARTING width
ap.add_argument("--pdf-max", type=int, default=48)       # governor's ceiling
ap.add_argument("--ramp-step", type=int, default=2)
ap.add_argument("--ramp-every", type=int, default=60)
ap.add_argument("--phase", default="row",
                choices=("row", "auto", "rd", "pdf", "both"),
                help="WHICH BACKFILL ORGAN OWNS THE WIRE (login 2026-08-24)."
                     " Interleaving rd and pdf only ever paid because they"
                     " are SEPARATE SERVER POOLS (measured 08-21: rd held"
                     " 135/s under pdf load) - under one wire that benefit"
                     " is gone, so running them together adds convergence"
                     " risk for zero throughput. auto = drain rd first (5.4M"
                     " requests, ~2.4%% of the work, and it keys the whole"
                     " corpus), then open pdf. The WALK always interleaves -"
                     " it is time-based and costs 0.1 req/s."
                     " ⚠ row (DEFAULT, login: 'I would like start to finish"
                     " by row') = THE ASSEMBLY LINE: one worker carries one"
                     " document all the way to READY - rd, key (trigger),"
                     " image - then takes the next. One pass over the"
                     " corpus, every row it touches is finished.")
ap.add_argument("--max-inflight", type=int, default=1,
                help="how many acris requests may be OPEN AT ONCE, process"
                     "-wide. 1 = pure piano: the code cannot collide two"
                     " requests. Higher = chords.")
ap.add_argument("--max-rps", type=float, default=20.0,
                help="TOTAL acris requests/second across rd + pdf pages +"
                     " probe. ⚠ THE TEMPO (login 2026-08-24, trip #5): at"
                     " 8ms latency worker count STOPPED controlling rate -"
                     " the same 28 rd workers did 13/s on a 228ms line and"
                     " 38/s on a fast one. Pace must be STATED, not implied"
                     " by concurrency. ~1.3M requests were spent on 2026-08-24"
                     " and the trips accelerated (5h/4h/47m/49m apart) - the"
                     " signature of a depleting budget, not a worker limit.")
ap.add_argument("--rps-max", type=float, default=80.0,
                help="ceiling for the governor's TEMPO climb. The dial that"
                     " matters is now requests/second, not worker count:"
                     " evenly-metered arrivals are what the VPN was"
                     " accidentally providing all morning (~77 req/s, no"
                     " blocks). The bucket makes that spacing deliberate.")
# ⚠ ON BY DEFAULT (login 2026-08-24: "we really do want fails to get solved
# for and never pile up since it assures perfection of the system"). A
# quarantined doc is skipped ON SIGHT, so without this it is stuck FOREVER
# and the pile only grows. Adjudication is also nearly free - the whole
# quarantine set is 1 doc today, a handful of requests - so there is no
# reason to make remembering a flag the thing that stands between us and a
# complete corpus. --no-adjudicate exists for a deliberate skip.
# ⚠ THE STEP IS SEARCH RESOLUTION, NOT A SAFETY MARGIN (2026-08-24).
# +2 was never protection against a block - the PACER is what keeps the
# arrival pattern safe, and it is identical at any rate (83 ms apart at
# 12/s, 6.7 ms at 150/s, burst capacity 1 either way). The step only sets
# how precisely we locate the ceiling, and overshoot is SELF-CORRECTING:
# shed >= 3 trims the tempo 25% and holds 10 minutes. Paying 42 rungs x 3
# min to crawl from 47 to 130 buys resolution nobody needs.
ap.add_argument("--rung-step", type=float, default=2.0,
                help="req/s added per clean window (default 2.0; 4-6 is"
                     " reasonable - overshoot self-corrects)")
# ⚠ WARM FRACTION IS EVIDENCE-BASED, NOT A GUESS. 0.6 was the cautious
# first value; 2026-08-24 then measured a warm start at 28.8 req/s
# delivering 28.8 in its FIRST window with zero sheds, after an hour
# clean at 48. Raising it re-earns fewer rungs. ⚠ It is still a margin:
# a restart follows some event, and resuming at 100% of a peak assumes
# the peak is still safe - which only the SERVER gets to confirm.
ap.add_argument("--warm-fraction", type=float, default=0.6,
                help="fraction of the banked peak tempo to resume at")
ap.add_argument("--no-reconcile", dest="reconcile",
                action="store_false",
                help="skip the startup re-feed of unresolved failures"
                     " (reconcile is ON by default)")
ap.set_defaults(reconcile=True)
ap.add_argument("--cold-start", dest="resume_warm", action="store_false",
                help="ignore the saved tempo and ramp from --max-rps"
                     " (warm resume is ON by default)")
ap.set_defaults(resume_warm=True)
ap.add_argument("--no-adjudicate", dest="adjudicate", action="store_false",
                help="skip the startup re-attempt of quarantined docs"
                     " (adjudication is ON by default)")
ap.set_defaults(adjudicate=True)
ap.add_argument("--stall-after", type=int, default=120,
                help="seconds with ZERO successful requests before the"
                     " transport is presumed dead and recycled")
ap.add_argument("--contiguous", action="store_true",
                help="hold ONE document's whole network burst uninterrupted."
                     " ⚠ COSTS ~64x THROUGHPUT - it serializes the entire"
                     " lane to one request at a time. Off by default; the"
                     " pacer provides the anti-lump guarantee instead.")
ap.add_argument("--step-minutes", type=int, default=10,
                help="clean minutes a width must hold before +2 (login"
                     " 2026-08-24: 10-min windows 'to truly see if things"
                     " degrade or recover stronger' - 5 was too thin to"
                     " separate a ceiling bend from a heavy-doc patch)")
ap.add_argument("--fresh-days", type=int, default=30)
ap.add_argument("--verify-imageless", action="store_true",
                help="ONE-TIME SWEEP of every pdf='imageless' row before the"
                     " normal backfill (login 2026-08-24: 'do a real pass on"
                     " them to assure theres no pdf'). A refusal is HTTP 200"
                     " with no TotalPages, so blocked requests were recorded"
                     " as imageless - a permanent verdict from a temporary"
                     " refusal. Re-asking costs 1 request when the verdict"
                     " holds, and when it does NOT the same worker fetches"
                     " and lands the pdf on the spot: verify and repair in"
                     " one motion. Resumable via _verify_cursor.txt.")
ap.add_argument("--every", type=int, default=10)
ap.add_argument("--control-every", type=int, default=60)
ap.add_argument("--deep-every", type=int, default=300)
ap.add_argument("--max", type=int, default=500)
ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()

REFUSALS = (fetch_pages.AccessDenied, LD.Refused)

stop_workers = threading.Event()     # refusal or shutdown: backfill halts
lock = threading.Lock()
q: queue.Queue = queue.Queue(maxsize=20_000)
pdf_q: queue.Queue = queue.Queue(maxsize=20_000)
pdf_hot: queue.Queue = queue.Queue()   # sync landings jump the pdf queue
stats = {"done": 0, "fail": 0,
         "pdfs": 0, "imageless": 0, "deferred": 0, "pdf_fail": 0,
         "verified": 0,   # imageless RE-confirmed: not new readiness
         "shed": 0}          # Short/timeout = the server's load signal
pdf_width = [0]              # live width, governed; workers idle above it
rd_width = [9999]            # rd gate - collapsed by the governor after a
                             # reconnect event so 28 workers never reopen
                             # connections in one burst (login: "if you are
                             # not connected, never just throw all the
                             # connections at once")
rd_all_fed = threading.Event()   # rd feeder exhausted the todo set
ua = {"User-Agent": fetch_pages.UA}
PDF_FAILS = CP.NAV_WORK / "acris_lane_pdf_fails.jsonl"
# the governor re-reads this EVERY MINUTE; absent or blank = use --rps-max
CEILING_FILE = CP.NAV_WORK / "lane_ceiling.txt"
# ⚠ IN-RUN RETRY LEDGER. Without it a failed doc keeps pdf='' and is only
# retried when the feeder's cursor WRAPS THE WHOLE 19.8M-ROW SET - correct
# (nothing lost, nothing faked) but the healing lands at the END of the sync
# instead of seconds later. MEASURED 2026-08-24: 146 of 159 failed docs healed
# on a later attempt - 92%, across EVERY class (SSLError 49/50, HTTP 400 36/43,
# Short 18/19). Transport noise, not document defects.
_attempts = {}
_att_lk = threading.Lock()
MAX_ATTEMPTS = 3
# ⚠ an absolute stop no file may cross. The old sharded fleet measured
# ~140 req/s aggregate as acris's served ceiling; 150 keeps that as the
# outer bound so a fat-fingered file can never launch a stampede.
HARD_CEILING = 150.0
PDF_BATCH = 25
VERIFY_CURSOR = CP.NAV_WORK / "_verify_cursor.txt"


def _quarantine(path, n=3):
    """ids that failed >=n times = server-side defects (login: "any defect
    should be cleaned up for maximal performance"). Skipped on sight so they
    stop costing fetches - but their columns STAY EMPTY (todo state) for a
    later adjudication pass. Never a fake verdict to make a row look done."""
    try:
        c = {}
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                i = json.loads(ln)["id"]
            except Exception:
                continue
            c[i] = c.get(i, 0) + 1
        return {i for i, k in c.items() if k >= n}
    except OSError:
        return set()


def _diagnosed(*paths):
    """ids whose failure already carries a CAUSE - stop re-asking them.

    _frames() appends its stop_why to the Short message ("placeholder(end-
    marker) at page N" = the server truly ends the doc early, its defect;
    "non-TIFF at page N" = possibly a FORMAT our II/MM test wrongly rejects,
    ours). Either way the question has an answer on record."""
    out = set()
    for path in paths:
        try:
            for ln in path.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(ln)
                except Exception:
                    continue
                m = str(r.get("msg", ""))
                if "placeholder(" in m or "non-TIFF at page" in m:
                    out.add(r.get("id"))
        except OSError:
            pass
    return out - {None}


QUAR_RD = _quarantine(FAILS)
QUAR_PDF = _quarantine(PDF_FAILS)
DIAGNOSED = _diagnosed(FAILS, PDF_FAILS)

con = sqlite3.connect(CP.NAV_DB, timeout=600, check_same_thread=False)
con.execute("PRAGMA journal_mode=WAL")
con.execute("PRAGMA busy_timeout=300000")


def say(m):
    print("%s  %s" % (time.strftime("%H:%M:%S"), m), flush=True)


class Tempo:
    """THE LANE'S METRONOME — one token per acris request, shared by every
    organ (rd fetch, pdf map, pdf page, edge probe). This is the piano rule
    made literal: a chosen tempo, not "as fast as the fingers move."

    ⚠ WHY THIS EXISTS (trip #5, 2026-08-24 14:39): concurrency was never the
    tripper - the morning ran 28 rd + 52 pdf workers clean for four hours.
    What tripped was VOLUME, and volume = concurrency x (1/latency), so a
    faster line silently tripled our request rate at identical settings.
    Workers now bound simultaneity; THIS bounds pace."""

    def __init__(self, rps):
        self.rps = float(rps)
        self.next_at = time.time()
        self.lk = threading.Lock()
        self.spent = 0

    def take(self):
        """Reserve THE NEXT DEPARTURE SLOT, then sleep until it.

        ⚠⚠ THIS IS A PACER, NOT A BUCKET — AND THAT IS THE WHOLE POINT
        (2026-08-24). It used to bank tokens up to a FULL SECOND's worth
        (`tokens = min(self.rps, ...)`), so after any idle stretch — img2pdf
        converting a long document, a batch of db writes — the saved-up
        beats were all playable at once and N workers fired back-to-back
        with ZERO spacing. Average rate looked perfect; arrivals were
        chords. That is drumming, measured at the same req/s that read as
        clean.

        It also explains why piano "worked a long time and then broke": the
        228 ms VPN kept the wire permanently busy, so tokens never had a
        chance to bank. When latency dropped, workers finished fast, went
        idle during local work, banked a second of tokens, and released
        them in a burst — identical settings, identical rate, newly bursty
        arrivals.

        Reserving a slot makes spacing a PROPERTY OF THE SCHEDULE rather
        than a side effect of how busy the wire happened to be. Burst
        capacity is exactly 1, at any latency, after any idle. A governor
        change to .rps takes effect on the next reservation."""
        with self.lk:
            now = time.time()
            due = self.next_at if self.next_at > now else now
            self.next_at = due + 1.0 / self.rps
            self.spent += 1
        delay = due - time.time()
        if delay > 0:
            time.sleep(delay)


# ⚠⚠ THE EARNED TEMPO SURVIVES A RESTART (login 2026-08-24: "a loss in
# connection would kill a ton of progress on ramp up speed. if we have to
# wait multiple hours to ever hit optimal speed, it isnt ideal").
#
# Climbing +2/s every 3 clean minutes means ~35 minutes to reach 36/s and
# over two hours to reach the ceiling. Throwing that away on every restart
# made the ramp the single most expensive thing in the system - and it is
# what made "just restart it" an unaffordable answer to any problem.
#
# So the governor records what it earned, and a restart RESUMES WARM at a
# fraction of it. Two guards keep that honest:
#   - the save is stamped CLEAN or DIRTY. A refusal, or a mass failure the
#     probe could not vouch for, writes DIRTY and the next start ignores
#     the saved value entirely - we never resume hot into a server that
#     just pushed back.
#   - the resume is a FRACTION (60%) and never above the ceiling, so it
#     re-earns the top rungs rather than assuming them. Even warm, that is
#     a rate acris served us minutes ago, and the pacer spaces every
#     departure identically at any rate - so a warm start is not a
#     stampede, which is the thing the ramp law actually guards against.
TEMPO_FILE = CP.NAV_WORK / "lane_tempo.json"
WARM_FRACTION = a.warm_fraction
WARM_MAX_AGE = 6 * 3600        # older than this and the world has moved on


# ⚠⚠ BANK THE HIGH-WATER MARK, NOT THE CURRENT TEMPO (login 2026-08-24:
# "what if we earn a higher tempo, does it track that and start there not
# cold?"). Saving the CURRENT value ratchets DOWNWARD across restarts: warm
# resume starts at 60% of the save, the very next rung overwrites the save
# with that lower number, and each restart compounds it - 48 -> 28.8 -> 17.3.
# The saved number has to be the best tempo the lane has actually HELD
# cleanly, so every resume measures from the peak rather than from wherever
# the climb happened to be when it was interrupted.
#
# ⚠ AND THE PEAK IS TRIMMED BY THE SERVER, NEVER ONLY BY US. On a shed the
# high-water resets DOWN to the post-backoff tempo: a rate acris pushed back
# on stops being evidence that the rate is safe, so it must not survive as a
# resume target. The mark means "highest rate recently sustained with no
# pushback" - which is exactly the claim a warm start needs to make.
_best = [0.0]


def save_tempo(rps, clean, trim=False):
    rps = float(rps)
    if trim:
        _best[0] = rps          # the server spoke: the old peak is void
    else:
        _best[0] = max(_best[0], rps)
    try:
        TEMPO_FILE.write_text(json.dumps(
            {"rps": round(rps, 1), "best": round(_best[0], 1),
             "clean": bool(clean), "at": time.time()}), encoding="utf-8")
    except OSError:
        pass


def _warm_start(cold):
    if not a.resume_warm:
        return cold, ""
    try:
        d = json.loads(TEMPO_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return cold, ""
    if not d.get("clean"):
        return cold, " (saved tempo was DIRTY - starting cold, by design)"
    if time.time() - d.get("at", 0) > WARM_MAX_AGE:
        return cold, " (saved tempo too old - starting cold)"
    peak = float(d.get("best", d.get("rps", cold)))
    _best[0] = peak                      # carry the mark across the restart
    warm = max(cold, min(peak * WARM_FRACTION, a.rps_max))
    if warm <= cold:
        return cold, ""
    return warm, ("WARM RESUME · peak clean tempo %.1f/s -> starting at"
                  " %.1f/s instead of %.1f - the climb is not thrown away"
                  % (peak, warm, cold))


_start_rps, _warm_note = _warm_start(float(a.max_rps))
tempo = Tempo(_start_rps)

# ⚠⚠ THE NO-COLLISION GATE (login 2026-08-24, trip #5): "we are drumming
# when we need to play piano. the code can never collide the requests."
# --max-inflight 1 means ONE acris request is open at a time, process-wide,
# across every organ - rd, pdf map, pdf page, edge probe. Workers still
# exist (they overlap the LOCAL work: parsing, converting, db writes) but
# they queue at this gate for the network. This is the piano rule enforced
# in code rather than trusted to configuration.
inflight = threading.Semaphore(a.max_inflight)


@contextlib.contextmanager
def slot():
    """Every acris request passes through here: tempo first, then the
    collision gate. No request path may bypass it."""
    tempo.take()
    with inflight:
        yield


# ⚠⚠ THE TURN (login 2026-08-24: "the issue is when you are running the walk
# and it breaks the sequencing"). slot() stops requests OVERLAPPING; this
# stops them INTERLEAVING. A document's requests - its map and all its pages
# - are one contiguous burst down the wire, and the walk waits for a row
# boundary instead of cutting in between page 5 and page 6. That is what a
# browser reading a document looks like.
#
# ⚠ HELD ONLY ACROSS NETWORK WORK, NEVER ACROSS CONVERSION. img2pdf takes
# seconds on a long document; holding the turn through it would idle the
# wire for every other worker - the whole point of having a crew. fetch_pdf
# releases before it converts.
_turn = threading.Lock()


@contextlib.contextmanager
def turn():
    """⚠⚠ OFF BY DEFAULT, AND THE MEASUREMENT SAYS WHY (2026-08-24).

    This is ONE GLOBAL LOCK held across a document's whole network burst
    (map + every page). With it on, the lane's real concurrency is 1 - the
    64-connection pool and the pacer are both inert, because nothing may
    START until the previous document FINISHES. Measured: 491 reqs in 120 s
    = 4.1 req/s = exactly 1/(244 ms RTT). Serialized, the <30-day target's
    66 req/s would need a 15 ms round trip. Not slow - arithmetically
    impossible.

    ⚠ CONTIGUITY WAS NEVER THE PROTECTION; SPACING IS. login's model:
    "acris doesnt want to see one ip accessing it in lumps." A lump is
    SIMULTANEOUS ARRIVAL, which the pacer now makes impossible by
    construction - no two requests depart within 1/rps of each other, at
    any latency, after any idle. Interleaving two documents is not a lump;
    it is what a browser with two tabs does. Contiguity is a DIFFERENT
    property, it costs ~64x, and it buys nothing the pacer does not
    already guarantee.

    Kept as a dial, not deleted: --contiguous restores it if evidence ever
    says arrival ORDER (not spacing) mattered after all."""
    if a.contiguous:
        with _turn:
            yield
    else:
        yield



# ⚠⚠ THE SINGLE VOICE (login 2026-08-24, the settled diagnosis): "acris
# trips when multiple requests come in simultaneously so it needs to
# sequentially orchestrate... its not the number of requests, its the
# overlap when they converge that tells them to block."
#
# So the lane holds ONE http session with a pool of exactly ONE connection,
# and slot() lets one request down it at a time. Not merely serialized -
# serialized ON A SINGLE KEPT-ALIVE CONNECTION, which is what a browser
# looks like and removes the repeated cold TLS handshakes that provoked the
# stampede trips. Workers remain parallel for LOCAL work (parsing, img2pdf,
# db writes); only the network is single file. Richmond is exempt - the
# drumroll rule holds there (proven 160 concurrent connections).
def _new_session():
    sess = requests.Session()
    sess.headers.update({"User-Agent": fetch_pages.UA})
    sess.mount("https://", requests.adapters.HTTPAdapter(
        pool_connections=1, pool_maxsize=a.max_inflight, max_retries=0,
        pool_block=True))
    return sess


# ⚠⚠ THE TRANSPORT RESTARTS ITSELF - A NETWORK CHANGE IS NOT A HUMAN'S JOB
# (login 2026-08-24: "how to restart it since changing networks will require
# the restart every time"). Every pooled socket is bound to the old route;
# after a VPN hop, a wifi switch or an ip re-lease they are all dead, and
# urllib3 only discovers that ONE REQUEST AT A TIME - each worker burns a
# full timeout rediscovering the same fact, which is what made a network
# change look like a hang that only a process restart could clear.
#
# So the session lives in a BOX and gets swapped wholesale: one recycle
# closes every stale socket and the next request builds a clean pool on the
# new route. That is the restart, minus the process, minus the human, and
# minus losing the climb.
_SESSION_BOX = [None]
last_ok = [time.time()]
_sess_lk = threading.Lock()
_recycles = [0]


def recycle_session(why):
    """Swap in a clean pool. Safe to call from any thread, any time."""
    with _sess_lk:
        old, _SESSION_BOX[0] = _SESSION_BOX[0], _new_session()
        _recycles[0] += 1
        n = _recycles[0]
    if old is not None:
        try:
            old.close()          # closes every pooled socket
        except Exception:
            pass
    say("  ⟳ TRANSPORT RECYCLED (#%d) - fresh connection pool: %s" % (n, why))


# ⚠⚠ THE POOL MUST BE AS WIDE AS --max-inflight, OR CONCURRENCY BECOMES A
# COLD-HANDSHAKE GENERATOR (measured 2026-08-24). urllib3's `block` defaults
# to False: with pool_maxsize=1 and 16 requests in flight, ONE takes the
# pooled connection and the other FIFTEEN call _new_conn() — a fresh TLS
# handshake each — then get discarded on release because the pool is full.
# Continuously. The "single kept-alive connection, what a browser looks
# like" claim above is only true at --max-inflight 1; at 16 we were minting
# and burning ~15 cold connections per cycle, which is the very stampede
# signature that trips this server ("160 cold TLS opens in one instant").
#
# So the pool is sized to the gate, and pool_block=True makes it a HARD
# ceiling — nothing can open a connection outside it, ever. Combined with
# the pacer above, connections are also born EVENLY SPACED (at 12/s the
# first handshakes are 83 ms apart), so the ramp warms the pool instead of
# stampeding it. Concurrency is now a warm-connection count, not a
# handshake rate — which is what makes raising it safe.
_SESSION_BOX[0] = _new_session()      # the live pool (swappable, see above)


def one_at_a_time(url, referer, timeout=90):
    """Every acris request in this process, single file, one connection.

    ⚠ RAISES urllib.error.HTTPError ON 4xx/5xx — DO NOT "SIMPLIFY" THIS AWAY.
    urllib raises on 4xx; `requests` returns it as an ordinary response. Every
    refusal detector in this repo catches urllib.error.HTTPError (acris_edge's
    401/403/429 branch, fetch_pages' callers, rd_walk's), so a 403 arriving as
    a normal response would be parsed as a blank page and the workers would
    keep hammering a server that just refused us. Same family as the 09:00
    lesson: a detector that fires into the wrong except clause does not
    exist."""
    with slot():
        sess = _SESSION_BOX[0]
        r = sess.get(url, headers={"Referer": referer}, timeout=timeout)
    last_ok[0] = time.time()      # the wire is proven alive, this instant
    if r.status_code >= 400:
        # ⚠ CARRY THE EVIDENCE. str(HTTPError) is only "HTTP Error 400:
        # Bad Request" - it drops the url, so the fails log could not say
        # whether the MAP or a PAGE 400d, and we nearly reasoned a verdict
        # out of that gap. MEASURED 2026-08-24: 36 of the 43 docs that threw
        # 400 later downloaded a COMPLETE pdf - so 400 is transient noise,
        # NOT "this document has no image". Never map it to a verdict.
        err = urllib.error.HTTPError(url, r.status_code, r.reason,
                                     r.headers, None)
        err.acris_body = r.content[:180]
        raise err
    return r.content, r.headers.get("Content-Type", "")


AP.FETCH = one_at_a_time    # pdf maps + pages join the same single voice
AE.FETCH = one_at_a_time    # and the walk too - ZERO exceptions on the wire


def urls(did):
    return (ACRIS_URL + "DocumentDetail?doc_id=" + did,
            ACRIS_URL + "DocumentImageView?doc_id=" + did)


# ── EDGE (the sync half) — acris_live's proven machinery, verbatim logic ──

def read_edge():
    return int(json.loads(EDGE_STATE.read_text(encoding="utf-8"))["edge"])


def write_edge(n):
    st = json.loads(EDGE_STATE.read_text(encoding="utf-8"))
    st["edge"] = n
    st["watermark"] = n
    EDGE_STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


def land(rows):
    """INSERT empty then UPDATE rd, one transaction - key_on_rd is AFTER
    UPDATE OF recorded_details, so the order is what makes pass 1 fire."""
    ins = [(did, "", urls(did)[0], "", urls(did)[1], "", "")
           for _c, did, _r in rows]
    upd = [(rd, did) for _c, did, rd in rows if rd]
    for _try in range(120):
        try:
            with lock:
                con.executemany(
                    "INSERT OR IGNORE INTO navigation"
                    " (id, recorded_details, rd_url, pdf, pdf_url, keyed_by,"
                    " key) VALUES (?,?,?,?,?,?,?)", ins)
                con.executemany(
                    "UPDATE navigation SET recorded_details=?"
                    " WHERE id=? AND recorded_details=''", upd)
                con.commit()
            return
        except sqlite3.OperationalError:
            time.sleep(5)
    raise RuntimeError("write lock unavailable for 10 minutes")


def write_ledger(n_docs, ids):
    try:
        lg = sqlite3.connect(LEDGER_DB, timeout=60)
        try:
            prev = lg.execute(
                "SELECT system_total FROM synchronization"
                " WHERE source='acris' AND system_total > 0"
                " ORDER BY run_at DESC LIMIT 1").fetchone()
            sysn = (prev[0] if prev else 0) + n_docs
            lg.execute("INSERT OR REPLACE INTO synchronization"
                       " (run_at, source, system_total, source_total, delta,"
                       " doc_ids) VALUES (?,?,?,?,?,?)",
                       (time.strftime("%Y-%m-%d %H:%M"), "acris", sysn, sysn,
                        0, ";".join(ids)))
            lg.commit()
        finally:
            lg.close()
    except Exception as e:
        say("  ⚠ ledger write failed (%s) - rows ARE landed" % type(e).__name__)


_last_control = [0.0]
_last_deep = [0.0]


def control_ok(edge):
    if time.time() - _last_control[0] < a.control_every:
        return True
    with slot():
        state, _did = AE.quick_crfn(edge)
    if state == "live":
        _last_control[0] = time.time()
        return True
    return False


def edge_tick():
    """One sync pass: shallow probe, walk on hits, land + key + ledger.
    Returns (ok, landed, refused)."""
    edge = read_edge()
    deep = (time.time() - _last_deep[0]) >= a.deep_every
    limit = CONFIRM_BLANKS if deep else 1
    if deep:
        _last_deep[0] = time.time()
    found, blanks, n = [], 0, edge
    try:
        # ⚠ THE WHOLE WALK IS ONE TURN: it waits for a row boundary rather
        # than cutting into a document's page sequence, and its own 1-8
        # requests stay contiguous. Pure network, no local work - safe to
        # hold. Costs at most one long document's burst of latency, against
        # a 10s cadence and filings that post in clerk-batches.
        with turn():
            while blanks < limit and (n - edge) < a.max:
                n += 1
                state, did, html = AE.fetch(n)
                if state != "live":
                    blanks += 1
                    continue
                blanks = 0
                try:
                    rec = json.dumps(RD.parse_acris(html),
                                     separators=(",", ":"))
                except Exception as e:
                    say("  ⚠ rd parse failed for %s (%s) - landing rd='' for"
                        " the backfill to retry" % (did, type(e).__name__))
                    rec = ""
                found.append((n, did, rec))
    except REFUSALS as e:
        say("  PROBE REFUSED: %.90s - nothing written" % e)
        return False, 0, True
    except Exception as e:
        code = getattr(e, "code", None)
        say("  PROBE UNPROVEN (%s%s: %.90s) - nothing written"
            % (type(e).__name__, " %d" % code if code else "", e))
        return False, 0, False
    if (n - edge) >= a.max:
        say("  ⚠ walked %d without %d blanks - run routine_synchronization"
            " (gallop+bisect). Nothing written." % (a.max, CONFIRM_BLANKS))
        return False, 0, False
    if not found:
        try:
            if not control_ok(edge):
                say("  CONTROL %d did not resolve - unproven" % edge)
                return False, 0, False
        except REFUSALS as e:
            say("  CONTROL REFUSED: %.60s" % e)
            return False, 0, True
        except Exception as e:
            say("  CONTROL errored (%s) - unproven" % type(e).__name__)
            return False, 0, False
        say("  level at crfn %d · %s walk, %d blank(s), control ok · %d req"
            % (edge, "DEEP" if deep else "shallow", blanks, n - edge))
        return True, 0, False
    if not a.apply:
        say("  would land %d (report-only)" % len(found))
        return True, 0, False
    land(found)
    write_edge(found[-1][0])
    write_ledger(len(found), [d for _c, d, _r in found])
    with lock:
        stats["done"] += len(found)
    # hot-list: a fresh filing's pdf is fetched NOW, not when the backfill
    # reaches it. Only rows whose rd parsed - pdf must follow rd, and a row
    # landed rd='' would break `ready = needed - pdf_todo` if pdf'd first.
    # ⚠ carries the rd JSON, not a bare date: the assembly line reads it to
    # know the row already has its recorded details (skip stage 1) AND to
    # get the recorded date for the store path. _rec_date() accepts either.
    for _c, did, rec in found:
        if rec:
            pdf_hot.put((did, rec, False))
    say("  SYNC landed %d · rd in the SAME request · edge %d -> %d"
        % (len(found), edge, found[-1][0]))
    return True, len(found), False


# ⚠ LAST MOMENT ACRIS WAS PROVEN TO BE SERVING US (set by the probe).
probe_ok_at = [0.0]


def watchdog():
    """⚠ THE SILENT NETWORK CHANGE (login: "changing networks will require
    the restart every time"). A burst of failures is the LOUD case and the
    governor handles it. The quiet case is worse: a route dies while every
    worker sits inside a 90 s socket timeout, so nothing fails, nothing
    lands, no counter moves, and the lane looks busy while doing nothing.
    Only a human noticing a flat board ever caught that.

    So: if NOTHING has succeeded for --stall-after seconds, the transport is
    presumed dead and gets recycled. Cheap (the probe alone re-proves the
    route in one request) and self-limiting - a healthy lane refreshes
    last_ok several times a second, so this can never fire under load."""
    while True:
        time.sleep(15)
        quiet = time.time() - last_ok[0]
        if quiet >= a.stall_after and not stop_workers.is_set():
            recycle_session("nothing has succeeded for %.0fs - presuming the"
                            " route changed under us" % quiet)
            last_ok[0] = time.time()      # give the new pool a fair window
            pdf_width[0] = min(pdf_width[0], 8)
            tempo.rps = max(4.0, tempo.rps * 0.5)
            say("  ⟳ re-ramping after the stall: tempo %.1f/s, width %d"
                % (tempo.rps, pdf_width[0]))


def edge_thread():
    """The reservation: one probe per --every seconds forever, exponential
    backoff while unproven/refused. Outlives a worker stop - this is the
    resume detector."""
    fails = 0
    while True:
        ok, _landed, refused = edge_tick()
        if ok:
            # ⚠ THE ORACLE. A successful probe is PROOF the server is still
            # serving THIS ip on THIS session - the governor reads it to tell
            # a local transport blip from an actual shedding server.
            probe_ok_at[0] = time.time()
        if refused and not stop_workers.is_set():
            stop_workers.set()
            # ⚠ a refusal marks the saved tempo DIRTY: the next start
            # must ramp COLD, never resume into a server that refused.
            save_tempo(tempo.rps, clean=False)
            say("  ⚠ REFUSED - BACKFILL WORKERS STOPPED (probe continues on"
                " backoff; restart the lane to resume backfill: login's call)")
        if ok:
            fails = 0
            time.sleep(a.every)
        else:
            fails += 1
            hold = min(a.every * (2 ** min(fails, 7)), 900)
            say("  held after %d failure(s) - next attempt in %ds" %
                (fails, hold))
            time.sleep(hold)


# ── BACKFILL (the acq half) — rd_walk's machinery on the todo index ──

def feeder():
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    fed, cursor = 0, ""
    while not stop_workers.is_set():
        rows = read.execute(
            "SELECT id FROM navigation WHERE recorded_details = ''"
            " AND id > ? AND id NOT LIKE 'RC_%'"
            " ORDER BY id LIMIT 10000", (cursor,)).fetchall()
        if not rows:
            # drained: the governor reallocates rd's budget to pdf, and the
            # feeder WRAPS after a rest instead of exiting - error rows
            # (HTTPError voids, URLError blips) landed nothing, so the todo
            # index still owes them and each sweep re-attempts. Nothing is
            # ever missed, only delayed; the column is the ledger, not the
            # error log.
            rd_all_fed.set()
            time.sleep(600)
            cursor = ""
            continue
        cursor = rows[-1][0]
        for (did,) in rows:
            if stop_workers.is_set():
                return
            q.put(did)
            fed += 1
            if a.limit and fed >= a.limit:
                q.put(None)
                return
    q.put(None)


pend, pend_lock = [], threading.Lock()


def flush():
    with pend_lock:
        batch, pend[:] = pend[:], []
    if not batch:
        return
    for _try in range(120):
        try:
            with lock:
                con.executemany(
                    "UPDATE navigation SET recorded_details=? WHERE id=?",
                    batch)
                con.commit()
            return
        except sqlite3.OperationalError:
            time.sleep(5)
    with pend_lock:
        pend[:0] = batch


def worker(idx=0):
    time.sleep(idx * 0.5)        # stagger cold starts - never a stampede
    while not stop_workers.is_set():
        if idx >= rd_width[0]:   # collapsed after a reconnect event
            time.sleep(5)
            continue
        try:
            did = q.get(timeout=5)
        except queue.Empty:
            continue
        if did is None:
            q.put(None)
            return
        if did in QUAR_RD:
            continue
        try:
            body, _ct = one_at_a_time(       # the single voice
                LD.BASE + "/DS/DocumentSearch/DocumentDetail?doc_id=" + did,
                LD.BASE + "/DS/DocumentSearch/")
            html = RD.clean_html(body.decode("utf-8", "replace"))
            LD.check_refused(html)
            flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
            if not re.search(r"DOCUMENT ID:\s*" + re.escape(did), flat):
                raise ValueError("page does not echo id")
            rec = RD.parse_acris(html)
            rec["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            with pend_lock:
                pend.append((json.dumps(rec, separators=(",", ":")), did))
                n = len(pend)
            if n >= BATCH:
                flush()
            with lock:
                stats["done"] += 1
        except REFUSALS as e:
            if not stop_workers.is_set():
                stop_workers.set()
                # ⚠ a refusal marks the saved tempo DIRTY: the next start
                # must ramp COLD, never resume into a server that refused.
                save_tempo(tempo.rps, clean=False)
                say("  REFUSED at %s - BACKFILL WORKERS STOPPED: %.90s"
                    % (did, e))
        except Exception as e:
            with lock:
                stats["fail"] += 1
            with FAILS.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"id": did,
                                     "err": type(e).__name__}) + "\n")


# ── PDF POOL (the image half) — acris_pdf's recipe on the pdf todo set ──

ppend, ppend_lock = [], threading.Lock()


def pdf_flush():
    with ppend_lock:
        batch, ppend[:] = ppend[:], []
    if not batch:
        return
    for _try in range(120):
        try:
            with lock:
                con.executemany(
                    "UPDATE navigation SET pdf=? WHERE id=? AND pdf=''",
                    batch)
                con.commit()
            return
        except sqlite3.OperationalError:
            time.sleep(5)
    with ppend_lock:
        ppend[:0] = batch


def pdf_feeder():
    """image_walk's trailing feeder: pdf follows rd through the same id
    order. When it runs dry it WRAPS to '' after a rest - that sweep is what
    retries deferred fresh docs and Short failures left behind the cursor."""
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    cursor = ""
    while not stop_workers.is_set():
        rows = read.execute(
            "SELECT id, json_extract(recorded_details, '$.recorded')"
            " FROM navigation WHERE pdf = ''"
            " AND recorded_details != ''"
            " AND id > ? AND id NOT LIKE 'RC_%'"
            " ORDER BY id LIMIT 5000", (cursor,)).fetchall()
        if not rows:
            time.sleep(600)
            cursor = ""
            continue
        cursor = rows[-1][0]
        for did, rec_date in rows:
            if stop_workers.is_set():
                return
            pdf_q.put((did, rec_date or ""))


def _rec_date(v):
    """Accept either the rd JSON or a bare recorded-date string."""
    if not v:
        return ""
    if v.lstrip().startswith("{"):
        try:
            return json.loads(v).get("recorded", "") or ""
        except Exception:
            return ""
    return v


def _fresh(rec_date):
    """Recorded within --fresh-days. On these, TotalPages<=0 means 'scan not
    uploaded yet' (the lag distribution), never an imageless verdict."""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", rec_date or "")
    if not m:
        return False
    try:
        t = time.mktime((int(m.group(3)), int(m.group(1)), int(m.group(2)),
                         0, 0, 0, 0, 0, -1))
    except (ValueError, OverflowError):
        return False
    return (time.time() - t) < a.fresh_days * 86400


def pdf_worker(idx):
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    while not stop_workers.is_set():
        if idx >= pdf_width[0]:      # governed: idle above the live width
            time.sleep(5)
            continue
        try:
            item = pdf_hot.get_nowait()
        except queue.Empty:
            try:
                item = pdf_q.get(timeout=5)
            except queue.Empty:
                continue
        did, rec_date = item
        if did in QUAR_PDF:
            continue
        try:
            row = read.execute("SELECT pdf FROM navigation WHERE id=?",
                               (did,)).fetchone()
            if row is None or row[0]:
                continue           # landed already (hot/wrap overlap)
            st, val = AP.fetch_pdf(did, rec_date, turn=turn)
            if st == "imageless" and _fresh(rec_date):
                with lock:
                    stats["deferred"] += 1
                continue           # scan lag, not a verdict - wrap retries
            with ppend_lock:
                ppend.append((val, did))
                n = len(ppend)
            with lock:
                stats["pdfs" if st == "pdf" else "imageless"] += 1
            if n >= PDF_BATCH:
                pdf_flush()
        except REFUSALS as e:
            if not stop_workers.is_set():
                stop_workers.set()
                # ⚠ a refusal marks the saved tempo DIRTY: the next start
                # must ramp COLD, never resume into a server that refused.
                save_tempo(tempo.rps, clean=False)
                say("  PDF REFUSED at %s - ALL WORKERS STOPPED: %.90s"
                    % (did, e))
        except Exception as e:
            kind = type(e).__name__
            with lock:
                stats["pdf_fail"] += 1
                # THE SERVER'S EVERY DIALECT OF "SLOW DOWN" counts as shed
                # (2026-08-24 11:03: at width 22 the pushback arrived as
                # "connection forcibly closed"/SSL EOF/RemoteDisconnected -
                # NOT Shorts - and the governor climbed blind to it). HTTP
                # 400 stays an ordinary per-doc fail.
                msg = str(e)
                if (kind in ("Short", "TimeoutError", "RemoteDisconnected",
                             "IncompleteRead")
                        or "timed out" in msg or "10054" in msg
                        or "10060" in msg or "UNEXPECTED_EOF" in msg
                        or "forcibly closed" in msg):
                    stats["shed"] += 1
            with PDF_FAILS.open("a", encoding="utf-8") as fh:
                # ⚠ STAMP IT. Without a time these rows cannot be tied to
                # a RUN, and on 2026-08-24 that cost a wrong diagnosis: I
                # read pre-patch rows, concluded the new url/body evidence
                # "did not fire", and reported that - it had fired, on the
                # only 400 the new code had actually seen. An append-only
                # log without a clock cannot answer "since when".
                rec_f = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                         "id": did, "err": kind, "msg": str(e)[:120]}
                if getattr(e, "url", None):
                    rec_f["url"] = str(e.url)[:160]
                if getattr(e, "acris_body", None):
                    rec_f["body"] = e.acris_body.decode(
                        "utf-8", "replace")[:180]
                fh.write(json.dumps(rec_f) + "\n")


def governor():
    """THE RAMP THAT KEEPS THE PHILOSOPHY (login 2026-08-24: "figure out
    where ramp up can happen without killing the philosophy... the
    intelligence needs to know once rd backfill finishes that it can
    allocate more resources to the pdf and live sync").

    One rule set, applied every minute:
      - the server's shed signal (Short/timeout) is OBEYED, never pushed
        through: a shedding minute steps width DOWN 25% and holds 10 min
      - 5 consecutive clean minutes EARN +2 width, up to --pdf-max
      - rd backfill draining hands its budget over: +8 width immediately
        (the reallocation login asked for - same server, freed tonnage)
      - a refusal is above this governor's pay grade: stop_workers stills
        everything and only the probe continues (unchanged)."""
    streak, hold, last = 0, 0, {"shed": 0, "pdfs": 0, "imageless": 0,
                               "verified": 0}
    rd_handed = False
    # per-width measurement: settled average over the width's WHOLE window,
    # announced at every transition - the ceiling shows as this number
    # flattening (or falling) across steps while minutes stay clean
    win_t0, win_c0 = time.time(), 0

    def settle(w):
        with lock:
            c = stats["pdfs"] + stats["imageless"]
        el = time.time() - win_t0
        return ("width %d averaged %.2f ready/s over %.1f min"
                % (w, (c - win_c0) / el if el else 0.0, el / 60)), c

    while not stop_workers.is_set():
        time.sleep(60)
        with lock:
            s = dict(stats)
        shed = s["shed"] - last["shed"]
        # ⚠⚠ PROGRESS FOR THE CLIMB INCLUDES VERIFIED ROWS; THE RATE DOES NOT
        # (the 15:37 freeze, 2026-08-24). The climb test below is `shed == 0
        # and landed > 0` - "is the lane doing work". Re-confirmed imageless
        # rows book to their own `verified` counter so they cannot inflate
        # the READY rate, which was right; but they were left out of THIS sum
        # too, so a verify sweep made landed 0 EVERY minute, reset the clean
        # streak every minute, and the tempo could never step. Symptom: 2,645
        # verified / 52 pdfs / 0.1 ready/s, pinned at the launch cap with
        # ZERO sheds - a governor blind to its own progress.
        #
        # So the two questions get two different sums: work happening (this,
        # includes verified) vs rows completed (settle(), excludes it). An
        # honest counter a control loop does not read is a control loop that
        # cannot see itself.
        landed = (s["pdfs"] + s["imageless"] + s["verified"]
                  - last["pdfs"] - last["imageless"] - last["verified"])
        last = s
        w = pdf_width[0]
        if rd_all_fed.is_set() and not rd_handed:
            rd_handed = True
            pdf_width[0] = min(w + 8, a.pdf_max)
            verdict, win_c0 = settle(w)
            win_t0 = time.time()
            say("  GOVERNOR rd backfill drained - budget reallocated,"
                " pdf width %d -> %d (%s)" % (w, pdf_width[0], verdict))
            streak = 0
            continue
        if rd_width[0] < a.workers and shed == 0:
            rd_width[0] = min(rd_width[0] + 6, a.workers)   # gentle recovery
        # ── THE TEMPO IS THE DIAL NOW (login 2026-08-24: "get the rate up to
        # a legitimately good figure sustained"). Width stopped meaning
        # anything once the bucket paced the wire; requests/second is what
        # ACRIS experiences. Climb it the way the governor climbed width:
        # +2/s per clean window, back off hard on the server's own signal.
        rps = tempo.rps
        # ⚠⚠ THE CEILING IS LIVE-TUNABLE (login 2026-08-24: "if we do see
        # that theres room and we get there without blocking then we should
        # push that ceiling as we step"). --rps-max was NEVER a measured
        # acris limit - it is OUR number. The only measurement of what acris
        # tolerates is the old sharded fleet at ~140 req/s aggregate,
        # sustained for hours. Raising it used to mean a RESTART, which threw
        # away the entire earned climb (back to 12/s, hours to return) - so
        # the ceiling is re-read from a FILE every minute. Echo a number into
        # lane_ceiling.txt and the governor picks it up on its next tick.
        # It is a BRAKE as well: a lower number trims the tempo immediately.
        ceiling = a.rps_max
        try:
            _txt = CEILING_FILE.read_text(encoding="utf-8").strip()
            if _txt:
                ceiling = max(4.0, min(float(_txt), HARD_CEILING))
        except (OSError, ValueError):
            pass
        if ceiling < tempo.rps:
            tempo.rps = ceiling
            say("  GOVERNOR ceiling now %.1f/s - tempo trimmed to match"
                % ceiling)
            rps = tempo.rps
        if shed >= 10:
            # MASS failure in one minute = a reconnect event (network change,
            # sleep/wake, IP re-lease), not ordinary shedding: every keep-
            # alive died and the reconnection wave IS a stampede (login:
            # "do network changes count as resets?" - yes; "never just throw
            # all the connections at once"). BOTH pools collapse and re-ramp
            # gently - never a trim.
            verdict, win_c0 = settle(w)
            win_t0 = time.time()
            # ⚠⚠ ASK THE ORACLE BEFORE THROWING AWAY THE CLIMB (2026-08-24).
            # 15:56: 50 SSLErrors in ONE minute, then ZERO for the next four
            # while pdfs kept landing - a single transport event (every open
            # connection dying at once), not a server refusing us. The probe
            # never missed a beat through it, which is PROOF acris was still
            # serving this ip. The old code could not tell that from a real
            # shed, so it paid the full 10-minute collapse for local network
            # noise - and on a flaky link that is a permanent ceiling, because
            # the climb needs uninterrupted clean minutes to step at all.
            #
            # Probe healthy  -> LOCAL blip: the dead connections are already
            #                   gone, so drop width (the pool must re-warm)
            #                   but KEEP the earned tempo and hold only 2 min.
            # Probe silent   -> treat as the server: full collapse, 10 min.
            served = time.time() - probe_ok_at[0] < 90
            # every pooled socket just died together - throw the pool away
            # rather than let each worker rediscover that on its own timeout
            recycle_session("mass failure (%d/min)" % shed)
            pdf_width[0] = 8
            rd_width[0] = 4
            if served:
                hold, streak = 2, 0
                save_tempo(tempo.rps, clean=True)   # local blip, not acris
                say("  GOVERNOR mass failure (%d/min) but THE PROBE IS STILL"
                    " SERVED (%.0fs ago) - local transport event, not acris:"
                    " tempo HELD at %.1f/s, pdf %d -> 8, rd -> 4, hold 2 min"
                    " (%s)" % (shed, time.time() - probe_ok_at[0], tempo.rps,
                               w, verdict))
            else:
                tempo.rps = max(4.0, rps * 0.4)
                hold, streak = 10, 0
                save_tempo(tempo.rps, clean=False, trim=True)  # probe silent = server
                say("  GOVERNOR mass failure (%d/min), PROBE SILENT TOO -"
                    " treating as the server, FULL RE-RAMP: tempo %.1f ->"
                    " %.1f/s, pdf %d -> 8, rd -> 4, hold 10 min (%s)"
                    % (shed, rps, tempo.rps, w, verdict))
        elif shed >= 3:
            verdict, win_c0 = settle(w)
            win_t0 = time.time()
            tempo.rps = max(4.0, rps * 0.75)
            save_tempo(tempo.rps, clean=True, trim=True)   # peak was refuted
            hold, streak = 10, 0
            say("  GOVERNOR server shedding (%d) - TEMPO %.1f -> %.1f/s,"
                " hold 10 min (%s)" % (shed, rps, tempo.rps, verdict))
        elif hold > 0:
            hold -= 1
        elif shed < 3 and landed > 0:
            # ⚠⚠ AN ISOLATED SHED MUST NOT ZERO THE CLIMB (measured 17:30,
            # 2026-08-24). This read `shed == 0`, so ONE RemoteDisconnected or
            # one timeout in a minute sent the branch to `else: streak = 0`
            # and the 3-minute clean streak restarted from scratch. Observed:
            # 12 failures across 29 minutes cost ~20% of the rungs - 17:23
            # settled "over 6.0 min" and 17:29 never fired - with ZERO shed
            # events in the log, because 1-2 sheds never print anything.
            #
            # The thresholds now agree with each other. `shed >= 3` is what
            # this governor treats as the server actually pushing back; below
            # that is ordinary transport noise, and the code already declines
            # to back off for it. Declining to back off while also refusing to
            # advance is the worst of both - on a link with any packet loss it
            # silently caps the rate at whatever rung the first hiccup found.
            streak += 1
            # ⚠ UNDER PIANO (--max-inflight 1) WIDTH IS NOT PRESSURE, IT IS
            # SHARE. The gate decides what reaches the wire, so widening
            # cannot provoke anything - it only changes how the single wire
            # is DIVIDED between rd and pdf (waiters per organ = that
            # organ's share) and keeps the wire busy while workers do local
            # work. So the governor stops hunting a width ceiling; the
            # ceiling now lives in --max-rps and the round trip.
            if streak >= a.step_minutes and rps < ceiling:
                verdict, win_c0 = settle(w)
                win_t0 = time.time()
                tempo.rps = min(rps + a.rung_step, ceiling)
                save_tempo(tempo.rps, clean=True)   # bank the rung
                streak = 0
                say("  GOVERNOR %d clean minutes - TEMPO %.1f -> %.1f/s (%s)"
                    % (a.step_minutes, rps, tempo.rps, verdict))
                continue
            if False and streak >= a.step_minutes and w < a.pdf_max:
                verdict, win_c0 = settle(w)
                win_t0 = time.time()
                pdf_width[0] = min(w + 2, a.pdf_max)
                streak = 0
                say("  GOVERNOR %d clean minutes - width %d -> %d (%s)"
                    % (a.step_minutes, w, pdf_width[0], verdict))
        else:
            streak = 0


# ⚠ THE STAMPEDE LESSON (13:03:50, trip #3): a relaunch that opens 50+ cold
# connections in one instant is nothing like the governor's +2 ramp - ACRIS
# absorbed a gentle climb to 52 all day, then served the Bandwidth Notice
# the second a restart fired everything at once. Same physics as richmond's
# sess() stagger ("160 cold TLS opens in one instant = SSLError across the
# board"). So a launch RAMPS: width starts small and a warmup thread raises
# it +4 every 30s until the requested width, then the governor owns it.
# login 2026-08-24 (post trip #4): "warm up going too fast can be just as
# bad as cold starting" - the ramp defaults GENTLE now (+2/60s; ~25 min to
# width 52) and is a dial, not a constant.
RAMP_START, RAMP_STEP, RAMP_EVERY = 8, a.ramp_step, a.ramp_every
_target = min(a.pdf_workers, a.pdf_max)
# PHASE GATE: in rd/auto the pdf pool holds a token width (2) so the sync
# HOT LIST still images new filings the moment they record - today's
# documents stay fully ready - while the pdf BACKFILL waits its turn.
HOT_ONLY = 2
pdf_backfill = threading.Event()
pdf_width[0] = (min(RAMP_START, _target) if a.phase in ("pdf", "both")
                else min(HOT_ONLY, _target))
if a.phase in ("pdf", "both"):
    pdf_backfill.set()


def warmup_ramp():
    if a.phase == "rd":
        say("  PHASE rd - pdf backfill parked, %d workers held for the sync"
            " hot list (new filings still get images at once)" % HOT_ONLY)
        return
    if a.phase == "auto" and not rd_all_fed.is_set():
        say("  PHASE rd first - pdf backfill opens when the rd gap drains"
            " (rd is ~2.4%% of remaining requests and keys the corpus);"
            " %d pdf workers held for the sync hot list" % HOT_ONLY)
        while not rd_all_fed.is_set() and not stop_workers.is_set():
            time.sleep(30)
        if stop_workers.is_set():
            return
        say("  PHASE rd drained -> opening the pdf backfill")
        pdf_width[0] = min(RAMP_START, _target)
    pdf_backfill.set()
    while pdf_width[0] < _target and not stop_workers.is_set():
        time.sleep(RAMP_EVERY)
        pdf_width[0] = min(pdf_width[0] + RAMP_STEP, _target)
    if not stop_workers.is_set():
        say("  RAMP complete - width %d, governor owns it" % pdf_width[0])

# ── THE ASSEMBLY LINE (--phase row) — one worker, one row, start to finish ──

def row_feeder():
    """Every INCOMPLETE row, in id order, from ix_nav_pdf_todo.

    ⚠ ONE INDEX COVERS BOTH GAPS: a row missing rd necessarily has pdf=''
    too (nothing ever lands an image before its rd - image_walk and the pdf
    pool both require recorded_details!=''), so `pdf=''` IS the not-ready
    set. `pdf='imageless'` is ready-by-verdict and correctly excluded.
    Wraps on exhaustion so error rows and deferred-fresh rows get retried."""
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")

    # ── the one-time imageless sweep, ahead of the normal backfill ──
    if a.verify_imageless:
        cur = VERIFY_CURSOR.read_text().strip() if VERIFY_CURSOR.exists() else ""
        if cur != "DONE":
            say("  VERIFY IMAGELESS: sweeping every imageless row from %r -"
                " a held verdict costs 1 request, a false one is repaired on"
                " the spot" % cur)
            n = 0
            while not stop_workers.is_set():
                rows = read.execute(
                    "SELECT id, recorded_details FROM navigation"
                    " WHERE pdf = 'imageless' AND id > ? AND id NOT LIKE 'RC_%'"
                    " ORDER BY id LIMIT 2000", (cur,)).fetchall()
                if not rows:
                    VERIFY_CURSOR.write_text("DONE")
                    say("  VERIFY IMAGELESS COMPLETE - %s rows re-asked"
                        % "{:,}".format(n))
                    break
                for did, rd in rows:
                    if stop_workers.is_set():
                        return
                    q.put((did, rd or "", "verify"))     # verify: not progress
                    n += 1
                cur = rows[-1][0]
                VERIFY_CURSOR.write_text(cur)     # resumable across restarts
                while q.qsize() > 500 and not stop_workers.is_set():
                    time.sleep(2)

    # ⚠⚠ THE RECONCILE SWEEP - DRIVE THE RESIDUE TO ZERO, DON'T WAIT FOR IT
    # (login 2026-08-24: "Can we make sure all errors resolve to 0 errors so
    # that we are clean"). A failed doc keeps its column empty, which IS the
    # todo state, so the feeder does re-attempt it - but only when the cursor
    # WRAPS THE WHOLE CORPUS, which is the end of the sync. "It heals
    # eventually" is not the same claim as "the residue is zero."
    #
    # The fails logs are tiny (255 docs against 21.6M), so re-feeding every
    # unresolved one at startup costs almost nothing and makes the residue
    # converge continuously instead of asymptotically. DIAGNOSED docs are
    # excluded - their answer is already on record; re-asking burns requests
    # for a question that has been answered.
    #
    # ⚠ GRADED PER STAGE, like lane_reconcile.py: an rd failure is resolved
    # when recorded_details arrives, a pdf failure when pdf does. Grading
    # either by the other reports normal pending work as an error - measured,
    # and it manufactured a 37% "outstanding" figure that was really 5.9%.
    if a.reconcile:
        want = {}
        for _p, _st in ((FAILS, "rd"), (PDF_FAILS, "pdf")):
            try:
                for _ln in _p.read_text(encoding="utf-8").splitlines():
                    try:
                        _i = json.loads(_ln)["id"]
                    except Exception:
                        continue
                    if _i and _i not in DIAGNOSED:
                        want[_i] = "pdf" if want.get(_i) == "pdf" or                             _st == "pdf" else "rd"
            except OSError:
                pass
        fed = 0
        for _i in sorted(want):
            _r = read.execute("SELECT pdf, recorded_details FROM navigation"
                              " WHERE id = ?", (_i,)).fetchone()
            if not _r:
                continue
            _done = bool(_r[0]) if want[_i] == "pdf" else bool(_r[1])
            if not _done:
                q.put((_i, _r[1] or "", ""))
                fed += 1
        if fed:
            say("  RECONCILE: re-feeding %d unresolved failure(s) of %d on"
                " record - the residue closes now, not at the cursor wrap"
                % (fed, len(want)))
        else:
            say("  RECONCILE: 0 unresolved failures - every one on record"
                " ended as a landing or a recorded verdict")
    stuck = []          # ⚠ defined unconditionally: the guard below reads it
    if a.adjudicate and (QUAR_PDF or QUAR_RD):
        # ⚠ A DIAGNOSED DOC IS DONE BEING ASKED. Adjudication runs at every
        # start, so without this a permanently-broken document burns a fresh
        # handful of requests on every restart and grows the fails log
        # forever - the pile login asked us never to let build. Once a
        # failure carries a CAUSE (_frames' stop_why: "placeholder(end-marker)
        # at page N" or "non-TIFF at page N"), re-asking adds nothing: the
        # answer is recorded and it is the SOURCE's defect, not a transport
        # flake. Its columns still stay EMPTY - diagnosed is not a verdict,
        # and a later policy pass can still adjudicate the class.
        stuck = sorted((QUAR_PDF | QUAR_RD) - DIAGNOSED)
        if DIAGNOSED:
            say("  %d quarantined doc(s) already carry a recorded cause -"
                " not re-asking (see acris_lane_pdf_fails.jsonl)"
                % len(DIAGNOSED))
    if a.adjudicate and (QUAR_PDF or QUAR_RD) and stuck:
        say("  ADJUDICATING %d quarantined doc(s) - one attempt each, with"
            " the diagnosis the original failures never recorded"
            % len(stuck))
        for _d in stuck:
            _r = read.execute("SELECT recorded_details FROM navigation"
                              " WHERE id = ?", (_d,)).fetchone()
            q.put((_d, (_r[0] if _r else "") or "", "adjudicate"))
    cursor = ""
    while not stop_workers.is_set():
        rows = read.execute(
            "SELECT id, recorded_details FROM navigation WHERE pdf = ''"
            " AND id > ? AND id NOT LIKE 'RC_%'"
            " ORDER BY id LIMIT 5000", (cursor,)).fetchall()
        if not rows:
            rd_all_fed.set()
            time.sleep(600)
            cursor = ""
            continue
        cursor = rows[-1][0]
        for did, rd in rows:
            if stop_workers.is_set():
                return
            q.put((did, rd or "", ""))


def row_worker(idx):
    """Carry ONE document to READY: rd (if missing) -> key by trigger ->
    image -> next. Every request goes down the single voice; the local work
    (parse, img2pdf, db) overlaps with other workers' turns on the wire."""
    time.sleep(idx * 0.5)
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    while not stop_workers.is_set():
        # crew size is governed: the reconnect rule collapses it to a
        # handful after a mass-failure event, then it climbs back
        if idx >= pdf_width[0]:
            time.sleep(5)
            continue
        try:
            item = pdf_hot.get_nowait()          # new filings jump the line
        except queue.Empty:
            try:
                item = q.get(timeout=5)
            except queue.Empty:
                continue
        did, rd_json, mode = (item if len(item) == 3
                              else (item[0], item[1], ""))
        is_verify = (mode == "verify")
        # ⚠ ADJUDICATION BYPASSES QUARANTINE ON PURPOSE. Quarantine is an
        # honest holding state - the row keeps EMPTY columns, never a fake
        # verdict - but nothing ever re-examined it, so a doc that failed 3
        # times was stuck forever. Worse, the quarantined Short docs failed
        # BEFORE _frames() recorded WHY it stopped, so their logs read
        # "short: 1/3 pages" with no cause. One attempt writes the real
        # diagnosis: placeholder(end-marker) = the server truly ends the doc
        # early (its defect); non-TIFF = maybe a FORMAT our II/MM test wrongly
        # rejects (ours). The verdict becomes EVIDENCE, not a guess.
        if mode != "adjudicate" and (did in QUAR_RD or did in QUAR_PDF):
            continue
        try:
            # ── stage 1: recorded details (skipped when already held) ──
            if not rd_json:
                with turn():
                    body, _ct = one_at_a_time(
                        LD.BASE + "/DS/DocumentSearch/DocumentDetail?doc_id="
                        + did, LD.BASE + "/DS/DocumentSearch/")
                html = RD.clean_html(body.decode("utf-8", "replace"))
                LD.check_refused(html)
                flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
                if not re.search(r"DOCUMENT ID:\s*" + re.escape(did), flat):
                    raise ValueError("page does not echo id")
                rec = RD.parse_acris(html)
                rec["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                rd_json = json.dumps(rec, separators=(",", ":"))
                with pend_lock:
                    pend.append((rd_json, did))
                    n = len(pend)
                if n >= BATCH:
                    flush()                      # trigger keys each landing
                with lock:
                    stats["done"] += 1
            # ── stage 2: the image, same row, same turn-taking wire ──
            rec_date = _rec_date(rd_json)
            st, val = AP.fetch_pdf(did, rec_date, turn=turn)
            if st == "imageless" and _fresh(rec_date):
                with lock:
                    stats["deferred"] += 1       # scan lag, not a verdict
                continue
            # ⚠ A RE-CONFIRMED imageless IS NOT NEW READINESS (login
            # 2026-08-24: "is the rate actually representative of row
            # completion or bs?" - it was not). The board reads
            # pdfs+imageless as the ready delta, so counting verification
            # sweeps there inflates the rate against work already done.
            # Books to its own counter instead; a verdict OVERTURNED (the
            # source now reports pages) lands as a real pdf and DOES count.
            if is_verify and st == "imageless":
                with lock:
                    stats["verified"] += 1
                continue
            with ppend_lock:
                ppend.append((val, did))
                m = len(ppend)
            with lock:
                stats["pdfs" if st == "pdf" else "imageless"] += 1
            if m >= PDF_BATCH:
                pdf_flush()
        except REFUSALS as e:
            if not stop_workers.is_set():
                stop_workers.set()
                # ⚠ a refusal marks the saved tempo DIRTY: the next start
                # must ramp COLD, never resume into a server that refused.
                save_tempo(tempo.rps, clean=False)
                say("  REFUSED at %s - ALL WORKERS STOPPED: %.90s" % (did, e))
        except Exception as e:
            kind = type(e).__name__
            with lock:
                stats["pdf_fail"] += 1
                msg = str(e)
                if (kind in ("Short", "TimeoutError", "RemoteDisconnected",
                             "IncompleteRead")
                        or "timed out" in msg or "10054" in msg
                        or "10060" in msg or "UNEXPECTED_EOF" in msg
                        or "forcibly closed" in msg):
                    stats["shed"] += 1
            with PDF_FAILS.open("a", encoding="utf-8") as fh:
                # ⚠ STAMP IT. Without a time these rows cannot be tied to
                # a RUN, and on 2026-08-24 that cost a wrong diagnosis: I
                # read pre-patch rows, concluded the new url/body evidence
                # "did not fire", and reported that - it had fired, on the
                # only 400 the new code had actually seen. An append-only
                # log without a clock cannot answer "since when".
                rec_f = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                         "id": did, "err": kind, "msg": str(e)[:120]}
                if getattr(e, "url", None):
                    rec_f["url"] = str(e.url)[:160]
                if getattr(e, "acris_body", None):
                    rec_f["body"] = e.acris_body.decode(
                        "utf-8", "replace")[:180]
                fh.write(json.dumps(rec_f) + "\n")
            # ⚠ HEAL IT NOW, NOT AT THE WRAP - bounded, and never for a
            # refusal (caught above; that stills the whole lane). The retry
            # re-enters through the SAME pacer, so it changes nothing about
            # what acris sees - only WHEN we ask again.
            with _att_lk:
                _attempts[did] = _attempts.get(did, 0) + 1
                again = _attempts[did] < MAX_ATTEMPTS
            if again and not stop_workers.is_set():
                q.put((did, rd_json, mode))


say("acris_lane up · %s · %s · %.1f req/s cap · edge every %ds · apply=%s"
    " · quarantined %d rd / %d pdf"
    % ("PIANO: one request on the wire, one connection, contiguous per row"
       if a.max_inflight <= 1
       else "CHORDS: up to %d requests at once" % a.max_inflight,
       ("ASSEMBLY LINE: %d workers, each carries a row rd->key->image->READY"
        % a.workers) if a.phase == "row"
       else "phase=%s · %d rd + pdf width %d (max %d)"
       % (a.phase, a.workers, pdf_width[0], a.pdf_max),
       tempo.rps, a.every, a.apply, len(QUAR_RD), len(QUAR_PDF)))
if _warm_note:
    say(" " + _warm_note.lstrip(" ·"))
threads = [threading.Thread(target=edge_thread, daemon=True),
           threading.Thread(target=watchdog, daemon=True)]
if a.phase == "row":
    # THE ASSEMBLY LINE: one pool, each worker carries a row to READY.
    # `--workers` is the crew size - enough to keep the single wire busy
    # while others parse and convert, never a pressure setting.
    pdf_width[0] = a.workers          # gate is the wire, not the width
    threads.append(threading.Thread(target=row_feeder, daemon=True))
    threads += [threading.Thread(target=row_worker, args=(i,), daemon=True)
                for i in range(a.workers)]
else:
    threads.append(threading.Thread(target=feeder, daemon=True))
    threads += [threading.Thread(target=worker, args=(i,), daemon=True)
                for i in range(a.workers)]
    if a.apply and a.pdf_workers > 0:
        threads.append(threading.Thread(target=pdf_feeder, daemon=True))
        threads.append(threading.Thread(target=warmup_ramp, daemon=True))
        threads += [threading.Thread(target=pdf_worker, args=(i,),
                                     daemon=True)
                    for i in range(a.pdf_max)]
if a.apply:
    threads.append(threading.Thread(target=governor, daemon=True))
t0 = time.time()
for t in threads:
    t.start()
try:
    while True:
        time.sleep(60)
        flush()
        pdf_flush()
        el = (time.time() - t0) / 60
        with lock:
            s = dict(stats)
        say("  PROGRESS %s total · %.1f docs/s · %d fail · %.0f min ·"
            " %s reqs @ %.1f/s%s"
            % ("{:,}".format(s["done"]),
               s["done"] / (el * 60) if el else 0.0, s["fail"], el,
               "{:,}".format(tempo.spent),
               tempo.spent / (el * 60) if el else 0.0,
               " · WORKERS STOPPED (refusal)" if stop_workers.is_set()
               else ""))
        if a.pdf_workers > 0:
            say("  PDF PROGRESS %s pdfs · %s imageless · %d deferred ·"
                " %d fail · %s verified · width %d"
                % ("{:,}".format(s["pdfs"]), "{:,}".format(s["imageless"]),
                   s["deferred"], s["pdf_fail"],
                   "{:,}".format(s["verified"]), pdf_width[0]))
except KeyboardInterrupt:
    stop_workers.set()
    # ⚠ AN OPERATOR STOP IS CLEAN, NOT A REFUSAL. Marking it dirty would
    # make every deliberate restart ramp from scratch - which is precisely
    # the cost this whole mechanism exists to remove.
    save_tempo(tempo.rps, clean=True)
    flush()
    pdf_flush()
    say("stopped · %s landed" % "{:,}".format(stats["done"]))
