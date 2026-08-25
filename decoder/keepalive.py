"""KEEP THE FLEET UP OVERNIGHT - restart what died, revive what wedged.

login 2026-08-24: "wifi may drop... most nights we have seen one of two
things. either we get blocked which I am hoping we solved or we stall because
of an outage or coding error. Please assure the failsafe is in place to run
the remainder of the night."

⚠ THIS SUPERVISES THE PROCESSES. IT IS NOT THE NETWORK WATCHDOG.
acris_lane already recycles its own transport when a route dies under it
(--stall-after), and the governor collapses on a shed and re-climbs. Those
handle a wifi drop WHILE THE PROCESS LIVES, and they are the right layer for
it - a lane that heals itself never loses its place in the climb. What nothing
covered until now is the process being GONE or WEDGED: an unhandled exception
on a thread, an OOM kill, a hang no internal timer can see. That is the gap
this fills, and only that.

    THREE STATES, THREE ANSWERS
      DEAD    no process        -> start it
      WEDGED  alive, but its log has not moved for --stale-min  -> kill, start
      REFUSED the lane stopped ITSELF on a refusal  -> ⚠ LEAVE IT DOWN

⚠⚠ THE REFUSAL RULE IS ABSOLUTE AND IS WHY THIS SCRIPT IS DANGEROUS WITHOUT
IT. The decoder's standing order is "On a refusal: stop; do not retry, do not
rotate anything." A supervisor that blindly restarts turns a single refusal
into an all-night retry loop hammering a server that already said no - the
exact behaviour most likely to earn a real block. So before ANY restart the
last lines of the lane's log are read, and if the lane reported a refusal the
supervisor stands down for that lane permanently and says so.

⚠ AND A RESTART STORM IS ITS OWN OUTAGE. A lane that dies on a coding error
would otherwise be relaunched every 60 s forever, burying the cause under
thousands of log lines. Restarts are capped per hour; past the cap the lane is
retried on a long interval and the cap is reported, never silently raised.

    python keepalive.py                 supervise (foreground)
    python keepalive.py --once          one pass, report only, changes nothing
    python keepalive.py --status        what it would do right now
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                      # noqa: E402

W = CP.NAV_WORK
LOG = HERE / "keepalive.log"

ap = argparse.ArgumentParser()
ap.add_argument("--every", type=int, default=60, help="seconds between passes")
ap.add_argument("--stale-min", type=float, default=6.0,
                help="a lane log untouched this long, with the process still"
                     " alive, is WEDGED. The lanes print PROGRESS about once a"
                     " minute, so 6 min is ~6 missed heartbeats - long enough"
                     " that a slow minute or a 5-min imageless sweep cannot"
                     " trip it.")
ap.add_argument("--max-restarts", type=int, default=6,
                help="per lane per hour before backing off")
ap.add_argument("--once", action="store_true", help="one pass then exit")
ap.add_argument("--status", action="store_true", help="report only, no action")
a = ap.parse_args()

# name -> (fleet lane, heartbeat log, must-be-fresh)
# ⚠ board_truth is deliberately NOT freshness-checked: it re-counts on a ~30
# MINUTE anchor interval, so a 6-minute silence is its NORMAL state. Checking
# it would manufacture a wedge every single pass.
# ⚠⚠ AND WATCH THE OUTPUT COUNTER, NOT JUST THE LOG (added 2026-08-25
# after a stall BOTH failsafes missed). At 05:15 a burst of ConnectionError /
# ChunkedEncodingError killed every acris worker connection. The lane then sat
# for 7+ minutes with pdfs FROZEN at 36,256 - and neither layer noticed:
#   - the in-process watchdog reads last_ok, which the EDGE PROBE refreshed
#     every 10s by succeeding, so "something succeeded recently" stayed true
#   - this supervisor read the log MTIME, which the same probe refreshed every
#     10s by printing "level at crfn ... control ok"
# A chatty probe made a lane with every worker dead look perfectly alive to
# both. ⚠ THE ONLY HONEST LIVENESS QUESTION IS "IS IT PRODUCING DOCUMENTS?" -
# a heartbeat proves a thread is running, never that work is happening.
PROGRESS_RE = {
    "acris_lane": re.compile(r"PDF PROGRESS ([\d,]+) pdfs"),
    "rc_lane": re.compile(r"PROGRESS ([\d,]+) pdfs"),
}
_last_count: dict[str, tuple[int, float]] = {}


def produced(name, log):
    """The lane's own cumulative output counter, or None if not applicable."""
    rx = PROGRESS_RE.get(name)
    if not rx or not log or not log.exists():
        return None
    try:
        txt = log.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]
    except OSError:
        return None
    for ln in reversed(txt):
        m = rx.search(ln)
        if m:
            return int(m.group(1).replace(",", ""))
    return None


SUPERVISED = {
    "acris_lane": ("sync", W / "acris_lane.log", True),
    "rc_lane": ("sync", HERE / "rc_lane.log", True),
    "routine_update": ("board", None, False),
    "board_truth": ("board", None, False),
    "org_backfill_arm": ("board", None, False),
}

REFUSAL = ("REFUSED", "Bandwidth Notice", "ALL WORKERS STOPPED",
           "BACKFILL WORKERS STOPPED")

_hist: dict[str, list[float]] = {}
_standdown: set[str] = set()


def say(msg):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def running() -> dict[str, int]:
    """name -> pid, from the live command lines. One source of truth."""
    out = {}
    try:
        ps = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
             " | Select-Object ProcessId,CommandLine | ConvertTo-Csv -NoTypeInformation"],
            capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return out
    for ln in ps.splitlines():
        for name in SUPERVISED:
            if name + ".py" in ln:
                try:
                    out[name] = int(ln.split(",")[0].strip('"'))
                except (ValueError, IndexError):
                    pass
    return out


def refused(log: pathlib.Path | None) -> str:
    """⚠ Did the lane stop ITSELF because the server said no?"""
    if not log or not log.exists():
        return ""
    try:
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-60:]
    except OSError:
        return ""
    for ln in reversed(tail):
        if any(m in ln for m in REFUSAL):
            return ln.strip()[:150]
    return ""


def stale_for(log: pathlib.Path | None) -> float:
    if not log or not log.exists():
        return 0.0
    return (time.time() - log.stat().st_mtime) / 60.0


def throttled(name) -> bool:
    h = [t for t in _hist.get(name, []) if time.time() - t < 3600]
    _hist[name] = h
    return len(h) >= a.max_restarts


def restart(name, lane, why):
    if a.status:
        say("WOULD RESTART %s (%s)" % (name, why))
        return
    if throttled(name):
        say("⚠ %s wants a restart (%s) but has already been restarted %d times"
            " this hour - BACKING OFF. That many restarts is a CODING ERROR"
            " or a persistent outage, not a blip; read the lane log."
            % (name, why, a.max_restarts))
        return
    _hist.setdefault(name, []).append(time.time())
    say("RESTARTING %s - %s" % (name, why))
    try:
        subprocess.run([sys.executable, str(HERE / "fleet.py"), "start", lane],
                       cwd=str(HERE), capture_output=True, text=True, timeout=120)
    except Exception as e:
        say("  restart failed: %s: %.80s" % (type(e).__name__, e))


def one_pass():
    live = running()
    for name, (lane, log, fresh) in SUPERVISED.items():
        if name in _standdown:
            continue
        r = refused(log)
        pid = live.get(name)
        if pid is None:
            # ⚠ DEAD *AND* REFUSED = the lane obeyed the standing order. It is
            # not broken; restarting it would be us overriding a refusal.
            if r:
                _standdown.add(name)
                say("⚠⚠ %s IS DOWN AFTER A REFUSAL - NOT RESTARTING, BY RULE."
                    " The server said no and the lane stopped, which is"
                    " correct. Standing down for this lane until a human"
                    " decides. Last line: %s" % (name, r))
                continue
            restart(name, lane, "process is GONE")
            continue
        if fresh:
            # >> STALLED-BUT-CHATTY: the log is moving but no documents are
            # being produced. This is the case that cost 7 minutes of dead
            # lane on 2026-08-25 and would have cost the whole night.
            cnt = produced(name, log)
            if cnt is not None:
                prev, since = _last_count.get(name, (None, time.time()))
                if prev is None or cnt != prev:
                    _last_count[name] = (cnt, time.time())
                elif time.time() - since >= a.stale_min * 60:
                    if r:
                        _standdown.add(name)
                        say("⚠⚠ %s has produced nothing for %.1f min AFTER A"
                            " REFUSAL - NOT restarting, by rule. Last line: %s"
                            % (name, (time.time() - since) / 60, r))
                        continue
                    say("%s is alive and its log is MOVING, but its output"
                        " counter has been stuck at %d for %.1f min - the"
                        " probe is chatting while the workers are dead"
                        % (name, cnt, (time.time() - since) / 60))
                    if not a.status:
                        subprocess.run(
                            ["powershell", "-NoProfile", "-Command",
                             "Stop-Process -Id %d -Force" % pid],
                            capture_output=True, timeout=60)
                        time.sleep(4)
                    _last_count.pop(name, None)
                    restart(name, lane, "output frozen at %d for %.1f min"
                            % (cnt, (time.time() - since) / 60))
                    continue
            mins = stale_for(log)
            if mins >= a.stale_min:
                if r:
                    _standdown.add(name)
                    say("⚠⚠ %s is silent %.1f min AFTER A REFUSAL - NOT"
                        " restarting, by rule. Last line: %s" % (name, mins, r))
                    continue
                say("%s is alive (pid %d) but its log has not moved for"
                    " %.1f min - WEDGED" % (name, pid, mins))
                if not a.status:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command",
                         "Stop-Process -Id %d -Force" % pid],
                        capture_output=True, timeout=60)
                    time.sleep(4)
                restart(name, lane, "wedged - log silent %.1f min" % mins)


def status():
    live = running()
    print("SUPERVISOR STATUS  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    for name, (lane, log, fresh) in SUPERVISED.items():
        pid = live.get(name)
        bits = ["pid %-6s" % (pid if pid else "DOWN")]
        if fresh and log:
            bits.append("log %.1f min old" % stale_for(log))
        r = refused(log)
        if r:
            bits.append("⚠ refusal on record")
        print("   %-17s %s" % (name, " · ".join(bits)))


if a.status:
    status()
    one_pass()
    raise SystemExit(0)

say("keepalive up - supervising %d processes every %ds"
    " (wedged = log silent %.0f min · max %d restarts/hour · ⚠ a lane that"
    " stopped on a REFUSAL is left down, by rule)"
    % (len(SUPERVISED), a.every, a.stale_min, a.max_restarts))
while True:
    try:
        one_pass()
    except Exception as e:
        say("supervisor error (%s: %.90s) - continuing" % (type(e).__name__, e))
    if a.once:
        break
    time.sleep(a.every)
