"""PHASE 01 · SYNCHRONIZATION, AS A SERVICE — find new doc ids, feed nav.

    python sync_service.py                    # report only, writes nothing
    python sync_service.py --apply            # the real thing
    python sync_service.py --apply --every 60

Login 2026-08-23: *"every 60 seconds or whatever the upper limit is to maximize
efficiency, we run python to find new doc id and send it to the db to begin nav
basically."*

THE PHASE'S ONE CLAIM:  EVERY DOC ID THE SOURCE HAS ISSUED IS IN THE DB.

⚠ THE CADENCE IS ADAPTIVE, NOT 60s. A fixed interval is wrong in BOTH
directions, and the governing metric says so — login: *"the point of the
pipeline is to beat inflow. The process needs to move faster than the
recordings."*

    ACRIS records ~1,550-1,676 documents per BUSINESS day  (measured)
    ~8 recording hours                                     -> ~3.2 / minute
    a quiet pass costs 1 control + CONFIRM_BLANKS(8) misses = 9 requests
    a busy pass costs 1 + (new) + 8

So at rush hour a fixed 60s sleep means we sit idle holding a known-stale edge;
overnight it means 540 requests an hour to re-learn a number that cannot move.
Instead:

    landed > 0   ->  GO AGAIN IMMEDIATELY. We are behind inflow by definition:
                     the source had documents we did not. Chasing costs nothing
                     extra because the walk stops itself at 8 blanks.
    landed == 0  ->  sleep --every. We are level; the next document is the only
                     thing worth waiting for.

That is self-pacing: it accelerates exactly when the register is busy and idles
when it is not, without a holiday calendar or a business-hours table to be
wrong about.

⚠ IT DOES NOT HAMMER AN UNREACHABLE HOST. Measured 2026-08-23 11:04:
a836-acris.nyc.gov returned 503 site-wide, including the bare root. A failing
pass backs off exponentially to --max-backoff instead of retrying every minute,
and it says so on every held tick. A monitor that goes quiet is
indistinguishable from a monitor that died.

⚠ A FAILED PASS IS NOT A LEVEL PASS. sync_fast exits non-zero and writes
nothing when the control does not resolve. This service must never treat that
as "landed 0" — that would reset the backoff and, worse, report level while
blind.

⚠ THIS REPLACES phase_monitor's --gate ROLE, NOT phase_monitor. Login
2026-08-23: *"monitor would just have a row for each source where we have
system total, source total, and a delta check... this isnt part of the
pipeline."* The monitor becomes a LEVELNESS AUDIT. This service is the pipeline.
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

PY = sys.executable
LOG = HERE / "sync_service.log"

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true",
                help="write; without it sync_fast reports and writes nothing")
ap.add_argument("--every", type=int, default=60,
                help="seconds to sleep after a pass that found NOTHING")
ap.add_argument("--max-backoff", type=int, default=900,
                help="ceiling for the failure backoff")
ap.add_argument("--source", choices=["acris"], default="acris",
                help="richmond's fast path is rc_sync_fast.py; it needs its "
                     "own service because its window is a DATE, not a counter")
ap.add_argument("--once", action="store_true")
a = ap.parse_args()

# sync_fast prints "landed N ids into navigation" on success and
# "level - nothing to land" when there is nothing. ⚠ PARSE THE NUMBER, DO NOT
# INFER IT FROM THE EXIT CODE - a pass that lands 0 and a pass that FAILED both
# leave you with "not success" unless you read what it actually said.
_LANDED = re.compile(r"landed\s+([\d,]+)\s+ids")
_LEVEL = re.compile(r"level - nothing to land")


def say(m):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def one_pass():
    """Returns (ok, landed). ok=False means WE LEARNED NOTHING - not level."""
    cmd = [PY, "-u", str(HERE / "sync_fast.py")] + (["--apply"] if a.apply else [])
    try:
        r = subprocess.run(cmd, cwd=str(HERE), capture_output=True,
                           text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        say("  sync_fast TIMED OUT at 1800s - reporting nothing")
        return False, 0
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        tail = [l for l in out.splitlines() if l.strip()][-1:] or ["(no output)"]
        say("  pass FAILED rc=%d · %.150s" % (r.returncode, tail[0]))
        return False, 0
    m = _LANDED.search(out)
    if m:
        return True, int(m.group(1).replace(",", ""))
    if _LEVEL.search(out):
        return True, 0
    # ⚠ SUCCEEDED BUT SAID SOMETHING WE DO NOT RECOGNISE. Do not call that
    # level. An unparsed success is an unknown, and unknown > wrong.
    tail = [l for l in out.splitlines() if l.strip()][-1:] or ["(no output)"]
    say("  pass rc=0 but UNPARSED · %.150s" % tail[0])
    return False, 0


def main():
    say("sync_service up · source %s · idle sleep %ds · apply=%s"
        % (a.source, a.every, a.apply))
    if not a.apply:
        say("  ⚠ --apply NOT given: sync_fast will report and write NOTHING. "
            "Every pass will read as level.")
    fails = 0
    while True:
        t0 = time.time()
        ok, landed = one_pass()
        el = time.time() - t0

        if not ok:
            fails += 1
            # exponential, capped, announced
            wait = min(a.every * (2 ** fails), a.max_backoff)
            say("  held after %d consecutive failure(s) - next attempt in %ds "
                "(source unreachable is NOT 'level'; nothing was written)"
                % (fails, wait))
        elif landed:
            fails = 0
            wait = 0
            say("  landed %d · %.1fs · GOING AGAIN NOW (behind inflow)"
                % (landed, el))
        else:
            fails = 0
            wait = a.every
            say("  level · %.1fs · next in %ds" % (el, wait))

        if a.once:
            return 0 if ok else 1
        if wait:
            time.sleep(wait)


if __name__ == "__main__":
    sys.exit(main() or 0)
