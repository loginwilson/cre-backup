"""PHASE 00- · MONITORIZATION — the cheap question, once a minute.

Login 2026-08-22: *"i think we have a monitor phase ahead of sync and a new
count indicates sync to kick off"* · *"it will be the same as sync, just a lot
cheaper as 1 request a minute checking the specific new filings"*.

THE PHASE'S ONE CLAIM:  THE SOURCE'S EDGE IS KNOWN, AS OF SECONDS AGO.

It never gathers a doc id, never mints a url, never writes the nav db. It
answers one yes/no and hands the answer to sync. That is why it can tick every
minute while sync — which scans, gathers and writes — cannot.

    MONITOR  "has anything shown up?"      1-8 requests
    SYNC     "exactly what, and land it"   gallop+bisect + gather + write

⚠ NOT SOCRATA (login: "socrata isnt good... socrata lags"). Socrata is a
REPUBLISHED MIRROR on its own refresh schedule, so `:updated_at` says when
Open Data reposted, not when the Register recorded. On a one-minute cadence it
shows nothing for hours and then dumps. **The CRFN counter and the date-range
window are the live surfaces — the same ones sync uses.**

⚠ A BLANK IS NOT THE EDGE. The CRFN counter has genuine holes (11 measured in
July, all verified unissued). Probing only edge+1 would report "quiet" forever
if a hole sits there while filings land at edge+5. So the monitor probes a
SPAN above the edge and reports new if ANY resolves. crfn_monitor.py needs
CONFIRM_BLANKS=8 to declare an edge; a monitor only needs to know SOMETHING is
there, which is why it is cheap.

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
a = ap.parse_args()
LOG = HERE / "phase_monitor.log"


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
    import live_delta as LD
    try:
        s = LD.Session().open().open_crfn()
        control = LC.parse_detail(LC.detail_html(s, edge)) is not None
    except Exception as e:
        say("acris    PROBE UNPROVEN (%s) - reporting NOTHING, not 'quiet'"
            % type(e).__name__)
        return None
    if not control:
        say("acris    CONTROL %s did not resolve - probe unproven, reporting "
            "NOTHING" % f"{edge:,}")
        return None

    hits, calls, errs = [], 0, 0
    for k in range(1, a.span + 1):
        n = edge + k
        calls += 1
        try:
            if LC.parse_detail(LC.detail_html(s, n)) is not None:
                hits.append(n)
                break                  # something is there; sync finds the rest
        except Exception:
            errs += 1                  # an error is NOT an absence
    if errs and not hits:
        say("acris    %d/%d probes ERRORED - reporting NOTHING" % (errs, calls))
        return None
    say("acris    edge %s · control ok · probed +1..+%d (%d req) · %s"
        % (f"{edge:,}", a.span, calls + 1,
           ("NEW at %s" % f"{hits[0]:,}") if hits else "quiet"))
    return bool(hits)


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
    day, tried, edge, npages = _dt.date.today(), [], None, 0
    for _ in range(5):
        d = day.strftime("%m/%d/%Y")
        try:
            edge, npages = RCS.Window(d, d).edge()
        except Exception as e:
            say("richmond %s window FAILED (%s) - reporting NOTHING, not a "
                "zero we did not measure" % (d, type(e).__name__))
            return None
        if edge:
            break
        tried.append(day.strftime("%a"))
        day -= _dt.timedelta(days=1)
    if not edge:
        say("richmond no rows in the last 5 days (%s) - that is NOT a quiet "
            "week, it is a broken read. Reporting NOTHING." % ",".join(tried))
        return None

    st = seen()
    prev = st.get("richmond_edge")
    st["richmond_edge"] = edge
    st["richmond_date"] = day.strftime("%m/%d/%Y")
    remember(st)
    new = prev is not None and edge > prev
    say("richmond %s · edge %s · %d pages%s%s"
        % (day.strftime("%m/%d/%Y"), f"{edge:,}", npages,
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
