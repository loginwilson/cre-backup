"""THE NIGHT WATCH — steps 5-8 of the night, with the hour bug fixed.

    nohup python -u night_watch.py > /c/tmp/watch.log 2>&1 &

`night_chain.py` did steps 1-4 correctly (pull, sweep, land, nav) and then blew
through the 4am wait in two minutes because of ONE comparison:

    if now.hour >= 6:            # meant "past 6am, stop waiting"
        break                    # true at 23:30, and every hour from 06:00 on

It reached step 6 at 23:28 the night before, `23 >= 6` was true immediately, so
it ran steps 7-8 at once and exited — leaving TWO drivers and EIGHT workers
against an ~80-connection ceiling. This file is those steps done again.

⚠ A WALL-CLOCK HOUR IS NOT A DEADLINE. Every time comparison here is against an
absolute `datetime` computed once, so "wait until 6am" cannot silently mean
"wait until any hour numbered 6 or more". If you add a check, add it as a
datetime, never as `.hour`.

⚠ ONE DRIVER. Refuses to start if an overnight.py is already alive — the
duplicate is the failure mode this exists to clean up, and re-creating it while
fixing it would be absurd.
"""
from __future__ import annotations
import datetime as dt
import pathlib
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import corpus_paths as CP

PY = sys.executable
ACQ = ["--procs", "4", "--conc", "20", "--boro", "1,2,3,4",
       "--lo", "1", "--hi", "2000", "--pool", "2000000"]
# ⚠ AN EXPLICIT WINDOWS PATH, NOT A POSIX ONE. Python on Windows resolves
# "/tmp/x" to C:\tmp\x and "/c/tmp/x" to C:\c\tmp\x, while Git Bash resolves
# "/tmp" to the user Temp directory. That mismatch already hid a duplicate
# acquisition run for two minutes tonight (N-14) - the log looked silent because
# the tail was reading a different file of the same name. Name the drive.
ACQ_LOG = r"C:\tmp\acq.log"


def log(m):
    print(f"[{dt.datetime.now():%H:%M:%S}] {m}", flush=True)


def drivers():
    """PIDs of live overnight.py drivers (not their workers)."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" |"
         " Where-Object { $_.CommandLine -like '*overnight.py*' } |"
         " Select-Object -ExpandProperty ProcessId) -join ','"],
        capture_output=True, text=True)
    s = (out.stdout or "").strip()
    return [int(x) for x in s.split(",") if x.strip().isdigit()]


def stop_acq(reason):
    """⚠ CONTROL STOP, NEVER A REFUSAL WORD. overnight.py now declines to start
    when _STOP contains 'refus'/'denied' (N-13). Writing either word here would
    wedge the run permanently and look like the source refused us."""
    CP.STOP.write_text(f"night_watch stop - {reason}\n", encoding="utf-8")
    log(f"  _STOP written ({reason}); waiting for drivers to halt")
    for _ in range(40):
        time.sleep(15)
        if not drivers():
            log("  all drivers halted")
            break
    else:
        log("  ⚠ drivers still alive after 10 min — leaving _STOP in place, NOT killing")
        return False
    if CP.STOP.exists():
        CP.STOP.unlink()
    return True


def start_acq(until):
    if drivers():
        log(f"  ⚠ a driver is already alive {drivers()} — NOT starting a second")
        return False
    log(f"START acquisition until {until}")
    subprocess.Popen([PY, "-u", "overnight.py"] + ACQ + ["--until", until],
                     cwd=str(HERE),
                     stdout=open(ACQ_LOG, "a", encoding="utf-8"),
                     stderr=subprocess.STDOUT)
    return True


def main():
    log("NIGHT WATCH START")

    if CP.STOP.exists():
        why = CP.STOP.read_text(encoding="utf-8", errors="replace")
        if "refus" in why.lower() or "denied" in why.lower():
            log("REFUSAL STOP PRESENT — standing down. A person must clear it.")
            for ln in why.splitlines():
                log(f"  | {ln}")
            return 2
        CP.STOP.unlink()
        log("  cleared a stale control stop")

    live = drivers()
    if len(live) > 1:
        log(f"  {len(live)} drivers alive {live} — halting all before restarting one")
        if not stop_acq("duplicate drivers"):
            return 1
        live = drivers()

    # --- absolute deadlines, computed ONCE ---------------------------------
    now = dt.datetime.now()
    acq_end = now.replace(hour=3, minute=50, second=0, microsecond=0)
    if acq_end <= now:
        acq_end += dt.timedelta(days=1)
    # ⚠ THE FIRST 06:00 AFTER NOW — derived from now, NOT from acq_end. Deriving
    # it from acq_end meant a 05:30 start waited for the NEXT day's six o'clock
    # and slept through the sync it was written to catch: the same "a time is not
    # a deadline" error one line further down. Caught by tabulating the function
    # at six start times instead of only the one I happened to be starting at.
    give_up = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if give_up <= now:
        give_up += dt.timedelta(days=1)
    log(f"  acquisition will stop at {acq_end:%Y-%m-%d %H:%M}")
    log(f"  sync wait gives up at   {give_up:%Y-%m-%d %H:%M}")

    if not live:
        start_acq(f"{acq_end:%H:%M}")
    else:
        log(f"  one driver already running {live} — leaving it")

    # --- hold for the 4am sync --------------------------------------------
    tsv = HERE / "_routine_4am.tsv"
    before = tsv.stat().st_mtime if tsv.exists() else 0
    log("waiting for the 4am sync (watching _routine_4am.tsv)")
    stopped = False
    while True:
        time.sleep(120)
        now = dt.datetime.now()
        if not stopped and now >= acq_end and drivers():
            log("03:50 reached — stopping acquisition for the sync")
            stop_acq("4am sync needs the machine")
            stopped = True
        if tsv.exists() and tsv.stat().st_mtime > before:
            log("4am routine finished")
            break
        if now >= give_up:
            log(f"{give_up:%H:%M} reached without a sync record — continuing anyway")
            break

    if drivers():
        stop_acq("nav rebuild before restart")

    # --- navigation back to live, then acquisition -------------------------
    log("START nav-live: nav_build.py")
    rc = subprocess.call([PY, "-u", "nav_build.py"], cwd=str(HERE))
    log(f"  nav-live rc={rc}")

    start_acq("23:00")
    log("NIGHT WATCH DONE — acquisition running on the live table")
    return 0


if __name__ == "__main__":
    sys.exit(main())
