"""THE NIGHT CHAIN — pull -> sweep -> land -> nav -> acq -> (4am sync) -> nav -> acq.

    nohup python -u night_chain.py > /tmp/chain.log 2>&1 &

⚠ ONE CONTROLLER, NO RACES. The 4am scheduled task still owns the sync itself;
this chain STOPS acquisition before it fires and RESTARTS acquisition after it
finishes, so the sync never competes with 4 x 20 connections for the drive.

⚠ EVERY STEP IS RESUMABLE AND IDEMPOTENT. Nothing here holds state that matters:
the pull resumes from its ledger, landing is keyed so re-landing changes nothing,
nav_build is a full rebuild, and acquisition resumes by reading the DISK. A crash
at any point costs the current step, never the night.

⚠ ACQUISITION STOPS AT 03:50, NOT 04:00. The sync needs the machine, and _STOP
is only honoured BETWEEN parcels - a ten minute margin is the drain time for a
2,000-document parcel in flight.
"""
from __future__ import annotations
import datetime as dt, os, pathlib, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import corpus_paths as CP

PY = sys.executable
ACQ = ["--procs", "4", "--conc", "20", "--boro", "1,2,3,4",
       "--lo", "1", "--hi", "2000", "--pool", "2000000"]


def log(m):
    print(f"[{dt.datetime.now():%H:%M:%S}] {m}", flush=True)


def run(label, args, timeout=None):
    log(f"START {label}: {' '.join(args)}")
    t0 = time.time()
    try:
        rc = subprocess.call([PY, "-u"] + args, cwd=str(HERE), timeout=timeout)
    except subprocess.TimeoutExpired:
        log(f"  {label} TIMED OUT after {timeout}s — continuing")
        return 1
    log(f"  {label} rc={rc} in {(time.time()-t0)/60:.1f} min")
    return rc


def pull_alive():
    """⚠ THE PROCESS TABLE IS THE LIVENESS TEST, NOT FILE GROWTH.

    MEASURED 2026-08-19: this asked whether rc_detail.jsonl grew over 20s. The
    pull commits in lumps, so a healthy pull looks dead inside a short window -
    the chain declared it finished at 21:51 while it was 80% through and started
    a SECOND --conc 80 sweep on the same worklist. 160 connections at Richmond
    and ~70k duplicate fetches. Never measure a lumpy writer over a short window.

    A running rc_detail_pull.py IS the pull. File growth is kept only as a
    fallback for a pull started outside this machine's process table, and it is
    given a window long enough to span a commit lump."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" |"
         " Where-Object { $_.CommandLine -like '*rc_detail_pull.py*' -and"
         f" $_.ProcessId -ne {os.getpid()} }}).Count"],
        capture_output=True, text=True)
    try:
        others = int((out.stdout or "0").strip() or 0)
    except ValueError:
        others = 0
    if others > 0:
        return True
    p = CP.INDEX / "rc_detail.jsonl"
    a = p.stat().st_size
    time.sleep(300)                     # ⚠ must span a commit lump, not a burst
    return p.stat().st_size > a


def kill_acq():
    """⚠ _STOP FIRST, KILL SECOND. The flag is checked between parcels; a parcel
    in flight can take minutes. Kill only after giving it a real chance."""
    CP.STOP.write_text("night_chain stop\n", encoding="utf-8")
    for _ in range(30):
        time.sleep(20)
        if not any_overnight():
            log("  acquisition halted on _STOP")
            break
    else:
        log("  acquisition did not halt — killing workers")
        subprocess.call(["powershell", "-NoProfile", "-Command",
                         "Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" |"
                         " Where-Object { $_.CommandLine -like '*overnight.py*' -or"
                         " $_.CommandLine -like '*acquire_async*' } |"
                         " ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"])
    for f in (CP.pid_file("overnight"), CP.STOP):
        if f.exists():
            f.unlink()


def any_overnight():
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" |"
                          " Where-Object { $_.CommandLine -like '*overnight.py*' -or"
                          " $_.CommandLine -like '*acquire_async*' }).Count"],
                         capture_output=True, text=True)
    try:
        return int((out.stdout or "0").strip() or 0) > 0
    except ValueError:
        return False


def start_acq(until):
    for f in (CP.pid_file("overnight"), CP.STOP):
        if f.exists():
            f.unlink()
    log(f"START acquisition until {until}")
    subprocess.Popen([PY, "-u", "overnight.py"] + ACQ + ["--until", until],
                     cwd=str(HERE),
                     stdout=open("/tmp/acq.log", "a", encoding="utf-8"),
                     stderr=subprocess.STDOUT)


def main():
    log("NIGHT CHAIN START")

    # 1 -------------------------------------------------- wait out the ledger pull
    while pull_alive():
        pass
    log("pull no longer writing")

    # 2 ------------------------------- sweep the error rows (they never left the queue)
    run("sweep", ["rc_detail_pull.py", "--run", "--conc", "80"], timeout=3600)

    # 3 ------------------------------------------------------------------- land
    run("land", ["rc_detail_land.py", "--apply"], timeout=7200)

    # 4 ------------------------------------------------------- navigation rebuild
    run("nav", ["nav_build.py"], timeout=7200)

    # 5 ----------------------------------------------- acquisition until 03:50
    start_acq("03:50")

    # 6 ------------------------------------- hold until the 4am sync has finished
    tsv = HERE / "_routine_4am.tsv"
    before = tsv.stat().st_mtime if tsv.exists() else 0
    log("waiting for the 4am sync to complete (watching _routine_4am.tsv)")
    while True:
        time.sleep(120)
        now = dt.datetime.now()
        if now.hour == 3 and now.minute >= 50 and any_overnight():
            kill_acq()
        if tsv.exists() and tsv.stat().st_mtime > before:
            log("4am routine finished")
            break
        if now.hour >= 6:
            log("06:00 reached without a sync record — continuing anyway")
            break

    # 7 --------------------------------------- navigation back to live, then acq
    run("nav-live", ["nav_build.py"], timeout=7200)
    start_acq("23:00")
    log("NIGHT CHAIN DONE — acquisition running on the live table")


if __name__ == "__main__":
    main()
