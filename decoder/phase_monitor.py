"""PHASE 00- · MONITORIZATION — the cheap question, once a minute.

Login 2026-08-22: *"i think we have a monitor phase ahead of sync and a new
count indicates sync to kick off"* · *"it will be the same as sync, just a lot
cheaper as 1 request a minute checking the specific new filings"*.

THE PHASE'S ONE CLAIM:  THE SOURCE'S EDGE IS KNOWN, AS OF SECONDS AGO.

It never gathers a doc id, never mints a url, never writes the nav db. It
answers one yes/no and hands the answer to sync. That is why it can tick every
minute while sync — which scans, gathers and writes — cannot.

    MONITOR  "has anything shown up?"      3 requests, ~2s, BOTH custodians
    SYNC     "exactly what, and land it"   gallop+bisect + gather + write

⚠ BOTH LANES ARE PLAIN GETs AS OF 2026-08-23 — no session, no token, no sleep.
Login: *"to me its all about direct gets and making sure you can access."*
Richmond went first (`rc_sync.quick_day`, 12 requests -> 1) and ACRIS followed
the same morning (`acris_edge.quick_crfn`, session+token POST -> 1 GET).

    acris     GET DocumentDetail?hid_CRFN=<n>&SearchType=DocID   0.5-0.9s
    richmond  GET Search/DateRangeSearch?StartSearchDate=...     0.6-0.7s

⚠ NOT SOCRATA (login: "socrata isnt good... socrata lags"). Measured 2026-08-23
and it is far worse than "lags": the ACRIS master dataset's newest
recorded_datetime is **2026-07-31**, top CRFN 2026000216051, while our edge is
2026000237865. The open dataset is **21,814 documents and 23 days behind us**.
A monitor there would report calm through three weeks of filings.

⚠ ACRIS HAS NO USABLE DATE WINDOW, WHICH IS WHY THIS COUNTS INSTEAD OF DATING.
Login asked for the date shape first, for a good reason — *"the delta becomes
much easier since its just comparison of 60 second changes"* — a re-read window
makes delta a SET DIFFERENCE, which self-heals and needs no watermark. That is
exactly how richmond works. ACRIS will not sell it: the ID/CRFN search has no
date field at all, and the Document TYPE search HAS dates (Last 7 / Last 31 /
range) but REQUIRES a doc type and refuses a GET — every parameter set tried
returned the same 21,724-byte search-options menu, and the tokened POST bounced
to the form too. So "everything recorded today" is 60-odd searches, not one.
The CRFN counter is the only live re-readable window ACRIS offers.

⚠ A BLANK IS NOT THE EDGE — BUT THE MONITOR STILL ONLY PROBES +1. The counter
has genuine holes (11 measured in July, all verified unissued), so a hole at
edge+1 costs one tick of delay. That is the deliberate trade: the next tick
re-probes the same number and anything real above it is still there, whereas a
span-wide walk pays `span` requests on every QUIET minute, which is the common
case. Confirming a blank is SYNC's job - sync_fast.py requires CONFIRM_BLANKS=8
consecutive misses before believing one. (`--span` now affects nothing on the
acris lane; it is kept only so existing service invocations still parse.)

⚠ THIS FILE NEVER ADVANCES A WATERMARK. index_daily.py learned it the
expensive way: "state saved before the work meant a report-only run moved the
cutoff and the next real run found nothing, with 28,196 documents permanently
behind it while it printed success." **The monitor observes; SYNC advances the
watermark, and only after the rows are on disk.**

⚠ NO OVERLAP. Sync is slow and the monitor is fast, so the monitor WILL tick
again while sync is still running. It refuses to fire a second one — both by
a lock file and by checking the process list.

Usage:  python phase_monitor.py                 # watch, report, no firing
        python phase_monitor.py --gate          # fire sync when new appears
        python phase_monitor.py --once
        python phase_monitor.py --every 60
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import live_crfn as LC

EDGE_STATE = HERE / "_crfn_edge.json"
SEEN = HERE / "_monitor_seen.json"
LOCKDIR = HERE / "_monitor_sync.lock"
PY = sys.executable

ap = argparse.ArgumentParser()
ap.add_argument("--every", type=int, default=60)
ap.add_argument("--span", type=int, default=8,
                help="how far above the edge to probe (covers counter holes)")
ap.add_argument("--gate", action="store_true", help="fire sync on a hit")
ap.add_argument("--once", action="store_true")
ap.add_argument("--source", choices=["both", "acris", "richmond"],
                default="both")
ap.add_argument("--closed-every", type=int, default=0,
                help="seconds between probes on a day the register cannot "
                     "record (weekends). 0 = OFF, the default: never stop "
                     "monitoring.")
a = ap.parse_args()
LOG = HERE / "phase_monitor.log"

# ⚠ DO NOT POLL A CLOSED OFFICE ONCE A MINUTE. Measured 2026-08-23 07:00, a
# SUNDAY: 53 richmond ticks in one hour, each opening a session, walking back
# Sun -> Sat -> Fri and RE-FETCHING ALL SEVEN PAGES of Friday's results — to
# learn a number that had not moved all night (richmond 1,017,350 and acris
# 2,026,000,237,865, constant across ~300 ticks).
#
# Both registers record on BUSINESS DAYS ONLY - measured over two weekends,
# every Sat/Sun returns 0 documents while weekday density is perfect. So on a
# weekend the expensive question has a known answer and we were asking it
# anyway, ~540 requests an hour, at a county clerk that had already refused our
# document route hours earlier. That is not a cost THEY should carry for us.
#
# ⚠ THE BACKOFF MUST ANNOUNCE ITSELF. A monitor that goes quiet is
# indistinguishable from a monitor that died - the exact failure this whole
# system keeps re-learning. Every held tick prints why it held, what the last
# known edge was, and when it will look again.
#
# ⚠ HOLIDAYS ARE NOT HANDLED and deliberately so: a Monday holiday just polls
# normally and finds nothing, which is wasteful but CORRECT. A wrong holiday
# calendar would make us blind on a day that does record.
_LAST_CLOSED_PROBE = {}


def register_closed(now=None):
    """Sat/Sun. Both custodians record on business days only (measured)."""
    return (now or time.localtime()).tm_wday >= 5


def hold_closed(src):
    """True if we should SKIP this source's probe on a closed day."""
    if not a.closed_every or not register_closed():
        return False
    last = _LAST_CLOSED_PROBE.get(src, 0)
    if time.time() - last >= a.closed_every:
        _LAST_CLOSED_PROBE[src] = time.time()
        return False
    return True


def say(m):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def known_edge():
    """Sync owns this file. We only READ it."""
    try:
        return int(json.loads(EDGE_STATE.read_text(encoding="utf-8"))["edge"])
    except Exception:
        return 0


def seen():
    try:
        return json.loads(SEEN.read_text(encoding="utf-8"))
    except Exception:
        return {}


def remember(d):
    SEEN.write_text(json.dumps(d, indent=1), encoding="utf-8")


def sync_running():
    """⚠ The monitor ticks faster than sync finishes. Two guards, because a
    lock file survives a crash and a process check does not lie."""
    if LOCKDIR.exists():
        return True
    try:
        ps = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
             " | ForEach-Object { $_.CommandLine }"],
            capture_output=True, text=True, timeout=45).stdout
    except Exception:
        return False
    return "routine_synchronization" in ps


def fire_sync(src):
    if sync_running():
        say("  sync already running - NOT firing a second one")
        return
    try:
        LOCKDIR.mkdir()
    except FileExistsError:
        say("  lock held - NOT firing")
        return
    try:
        # ⚠ FIRE THE O(DELTA) PATH, NOT THE FULL ROUTINE. This called
        # routine_synchronization.py, which PROVES LEVELNESS: its STEP 1 counts
        # our own rows across 24.1M (measured ~27 minutes) before it looks at
        # the source at all. Firing that on a one-minute monitor cadence is the
        # pile-up login asked us to prevent - *"sync must move quick from top of
        # our count to the edge of theirs and find those ids quick to send to
        # nav. since it can pile up."*
        #
        # sync_fast.py's own docstring already drew the line and nothing was
        # wired to it:
        #     routine_synchronization.py   proves levelness   minutes   periodic
        #     sync_fast.py                 lands the delta    seconds   every minute
        #
        # ⚠ THE FULL ROUTINE IS STILL REQUIRED, just not here. A forward-only
        # walk "inherits every gap it already has and reports clean forever."
        # It runs on its own slower schedule; this path only ever moves forward.
        fast = {"acris": ["sync_fast.py", "--apply"],
                "richmond": ["rc_sync_fast.py", "--apply"]}.get(src)
        if not fast:
            # ⚠ NO FAST PATH FOR THIS SOURCE - say so rather than silently
            # firing the 27-minute routine at monitor cadence.
            say("  no O(delta) path for %s - NOT firing (the full routine "
                "would take minutes and the monitor ticks in seconds)" % src)
            return
        say("  --> firing %s for %s" % (fast[0], src))
        subprocess.run([PY, "-u", str(HERE / fast[0])] + fast[1:],
                       cwd=str(HERE), timeout=1800)
        say("  sync returned for %s" % src)
    except Exception as e:
        say("  sync FAILED for %s: %s" % (src, type(e).__name__))
    finally:
        try:
            LOCKDIR.rmdir()
        except OSError:
            pass


def probe_acris():
    """ONE request per number above the known edge, stopping at the first hit.
    Quiet minute = `span` requests. Busy minute = 1."""
    edge = known_edge()
    if not edge:
        say("acris    NO KNOWN EDGE - refusing to report (crfn_monitor must "
            "establish it first; a monitor with no reference is not a monitor)")
        return None
    # ⚠ CONTROL FIRST - crfn_monitor.py's rule, and the first version of this
    # file proved why. It called a session helper that does not exist, so
    # every probe threw, a broad `except` turned each error into found=False,
    # and it printed "quiet" after 8 instant failures. A MALFORMED REQUEST
    # LOOKS EXACTLY LIKE AN EMPTY ONE. Never let an error become a negative.
    #
    # ⚠ NOW A PLAIN GET - no session, no token, no PACE sleep (2026-08-23).
    # `hid_CRFN` works as a query parameter; see acris_edge.py for the four
    # measurements. This is the ACRIS twin of rc_sync.quick_day(), which
    # collapsed richmond's probe from 12 requests to 1 the same morning.
    # ⚠ ASK THE REAL QUESTION FIRST; PAY FOR THE CONTROL ONLY IF THE ANSWER IS
    # A BLANK. Login 2026-08-23: *"what are you requesting for 3 requests
    # instead of 1?"* — and the honest answer was that the control ran first
    # unconditionally, every tick, forever.
    #
    # A LIVE ANSWER IS ITS OWN CONTROL. If edge+1 returns a parsed detail page
    # with a doc id, the route works, the parse works and the host is up — a
    # separate control request proves nothing the answer did not already prove.
    # Only a BLANK is ambiguous (absent CRFN / malformed request / changed route
    # / 503 all look alike), and only a blank needs the second request.
    #
    #     busy minute   edge+1 live   -> 1 request   (the common case at rush hour:
    #                                   acris records ~3.2/min on a business day)
    #     quiet minute  edge+1 blank  -> 2 requests
    #
    # ⚠ THE CONTROL IS NOT OPTIONAL ON A BLANK, ONLY DEFERRED. Reporting "quiet"
    # off an unproven blank is the exact failure this file shipped with once
    # already: it printed quiet after 8 instant failures.
    import acris_edge as AE
    hits, calls, errs = [], 0, 0
    ctrl_doc = None
    try:
        calls += 1
        state, did = AE.quick_crfn(edge + 1)
        if state == "live":
            # self-proving: the route answered with a real document
            say("acris    edge %d · probed +1 (1 req) · NEW at %d -> %s"
                % (edge, edge + 1, did))
            return True
        ok, ctrl_doc = AE.edge_holds(edge)
        calls += 1
    except Exception as e:
        # ⚠ NAME THE STATUS, NOT JUST THE CLASS. "HTTPError" alone cannot
        # distinguish a 500 we should shrug at from a 403 we must STOP on, and
        # this line printed exactly that for one tick on 2026-08-23 while the
        # answer sat one attribute away.
        code = getattr(e, "code", None)
        say("acris    PROBE UNPROVEN (%s%s: %.90s) - reporting NOTHING, not "
            "'quiet'" % (type(e).__name__,
                         " %d" % code if code else "", e))
        return None
    if not ok:
        say("acris    CONTROL %s did not resolve - probe unproven, reporting "
            "NOTHING" % str(edge))
        return None

    # ⚠ ONE STEP, NOT A SPAN. The old probe walked +1..+span looking for the
    # first hit, which cost `span` requests on every QUIET minute - the common
    # case. The monitor's only job is to answer "is there anything above the
    # edge"; CRFN is a dense ascending counter, so edge+1 answers it. Walking
    # for the rest is sync_fast's job, and sync_fast already knows how (it
    # confirms CONFIRM_BLANKS=8 in a row before believing a blank, because the
    # counter has genuine unissued holes - 11 measured in July).
    #
    # ⚠ SO A LONE UNISSUED NUMBER AT edge+1 DELAYS DETECTION BY ONE TICK, and
    # that is deliberate: the next tick re-probes the same number, and any real
    # document above it is still there. A missed minute is recoverable; a
    # `span`-wide walk every quiet minute is a standing cost with no payer.
    #
    # Reaching here means edge+1 came back BLANK and the control then RESOLVED:
    # a PROVEN quiet. The blank was request 1, the control request 2.
    say("acris    edge %d · +1 blank, control ok (%s) · quiet (%d req)"
        % (edge, ctrl_doc or "?", calls))
    return False


def probe_richmond():
    """One date-range window for today. ⚠ The date-range search is NOT the
    Cloudflare-protected route - that is /ViewVscmsDocument/ViewContent, the
    DOCUMENT route. rc_feed and rc_sync hit the search endpoints from python
    continuously. Two routes on one host, different protection."""
    # ⚠ TWO BUGS FIXED 2026-08-23. Window lives in rc_sync, NOT rc_source, and
    # `rows` is a METHOD, not an attribute - the first version did
    # getattr(w,"rows") and len()'d a bound method. It reported the failure
    # honestly rather than a zero, which is the only reason it was harmless.
    import datetime as _dt
    import rc_sync as RCS

    # ⚠ TRACK THE EDGE, NOT THE COUNT. `instrument` is richmond's dense
    # monotonic counter (its CRFN). A max is strictly better than a row count:
    # two windows can hold the same NUMBER of documents while holding
    # different ones, and a count would call that quiet.
    #
    # ⚠ AND TAKE THE EDGE OFF THE LAST PAGE - see Window.edge(). The window
    # paginates at 17 rows and page 1's max is NOT the day's max.
    #
    # ⚠ WEEKENDS ARE GENUINELY EMPTY - measured 08/15-16 and 08/22-23, both
    # zero, with weekday density perfect on either side. So an empty today is
    # not a fault, but it is also not an EDGE. Walk back to the last day that
    # actually recorded something; otherwise every weekend the monitor would
    # either cry failure or forget where the source had got to.
    # ⚠ ONE GET, AND THE SERVER SAYS WHETHER IT IS EMPTY. Rewritten 2026-08-23
    # from login's find: the date-range search answers a plain query-string GET
    # with no session, no POST and no token — 0.7 s against the ~12 requests and
    # ~15 s a Window cost. That collapse matters twice over:
    #
    #   COST      12 all-or-nothing requests -> 1. The old shape failed as a
    #             UNIT, so ~1% per-request flakiness became ~12% per probe
    #             (measured: 12.5% richmond probe failures while acris, on the
    #             same network in the same minutes, was clean).
    #   TRUTH     the page SAYS "NO RECORDS FOUND FOR 8/23/2026-8/23/2026".
    #             We used to INFER quiet from parsing zero rows — the exact
    #             inference that was silently wrong for weeks.
    #
    # ⚠ AND THE WALK-BACK IS GONE. It existed to find "the last day that
    # recorded something", which was never the question. The question is "did
    # anything file TODAY", and an explicit NO RECORDS answers it outright. A
    # closed weekend is now a definite answer costing one request, not three
    # windows costing twelve.
    today = _dt.date.today().strftime("%m/%d/%Y")
    try:
        state, rows, npages = RCS.quick_day(today)
    except Exception as e:
        say("richmond %s FAILED (%s) - reporting NOTHING, not a zero we did "
            "not measure" % (today, type(e).__name__))
        return None

    if state == "unknown":
        # ⚠ THE STATE THAT DID NOT USED TO EXIST. Neither rows nor the
        # server's own empty message: the page changed under us, or we cannot
        # read it. This used to be indistinguishable from "quiet".
        say("richmond %s · page parsed NEITHER rows NOR 'NO RECORDS FOUND' - "
            "the markup may have changed again. Reporting NOTHING." % today)
        return None

    if state == "empty":
        st = seen()
        say("richmond %s · server says NO RECORDS FOUND · quiet (1 req) · "
            "edge holds at %s" % (today, f"{st.get('richmond_edge', 0):,}"))
        return False

    # rows today -> the edge is on the LAST page (rows ascend), 1 extra request
    edge = None
    if npages > 1:
        _, last, _ = RCS.quick_day(today, page=npages)
        rows = last or rows
    nums = [int(r["instrument"]) for r in rows if r["instrument"].isdigit()]
    edge = max(nums) if nums else None
    if not edge:
        say("richmond %s · rows parsed but no instrument numbers - reporting "
            "NOTHING" % today)
        return None
    day = _dt.date.today()
    tried = []

    st = seen()
    prev = st.get("richmond_edge")
    st["richmond_edge"] = edge
    st["richmond_date"] = day.strftime("%m/%d/%Y")
    remember(st)
    new = prev is not None and edge > prev
    say("richmond %s · edge %s · %d pages%s%s"
        % (day.strftime("%m/%d/%Y"), str(edge), npages,
           (" (walked back past %s)" % ",".join(tried)) if tried else "",
           "" if prev is None else
           ("  NEW (was %s)" % f"{prev:,}" if new else "  quiet")))
    return new


say("phase_monitor up · every %ds · span %d · gate=%s"
    % (a.every, a.span, a.gate))
while True:
    t0 = time.time()
    for src, fn in (("acris", probe_acris), ("richmond", probe_richmond)):
        if a.source not in ("both", src):
            continue
        if hold_closed(src):
            st = seen()
            edge = (st.get("richmond_edge") if src == "richmond"
                    else known_edge())
            left = a.closed_every - (time.time() - _LAST_CLOSED_PROBE.get(src, 0))
            say("%-8s register CLOSED (%s) - holding · last edge %s · next "
                "look in %dm  [the answer cannot change today]"
                % (src, time.strftime("%A"),
                   str(edge) if edge else "-", max(0, left) // 60))
            continue
        try:
            hit = fn()
        except Exception as e:
            say("%s probe ERROR: %s" % (src, type(e).__name__))
            hit = None
        if hit and a.gate:
            fire_sync(src)
    if a.once:
        break
    time.sleep(max(15, a.every - (time.time() - t0)))
