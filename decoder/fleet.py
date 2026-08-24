"""THE FLEET ROSTER - every lane, every process, one command each.

login (2026-08-24): "each process has fleets of processes in them so if i
lost everything and said kick off richmond pdf or acris rd, it would be
difficult to pinpoint every moving piece." This file IS the pinpointing:
the lane definitions below are the single authority for what "acris rd"
or "richmond pdf" means - scripts, arguments, ranges, log paths. Change a
lane's shape HERE, never in a shell history.

    python fleet.py status              what is running / missing, per lane
    python fleet.py start <lane|all>    launch a lane's missing processes
    python fleet.py stop <lane|all>     stop a lane's processes

Lanes: sync (acris = THE CONSOLIDATED LANE; richmond = rc_live until
rc_lane exists) · rcpdf (richmond pdf trio) · board (routine_update +
board_truth + pass-2 arm).

⚠ THE 2026-08-24 CUTOVER: acris_lane.py absorbed acris_live, the rd_walk
fleet (4x28) AND the image_walk fleet (3x14). ONE process is the whole
acris presence - edge probe every 10s, rd backfill workers, pdf pool with
the sync hot-list, keying via the key_on_rd trigger (needs no process).
The old "rd" and "apdf" lanes are RETIRED: starting them alongside the
lane would put a second access point on ACRIS, which is the tripping
condition the lane exists to remove. Their definitions live in git
history if a rollback ever needs them.
"""
import pathlib
import subprocess
import sys
import time

PY = sys.executable
HERE = pathlib.Path(__file__).parent
W = pathlib.Path(r"D:\CRE Decoding System\01 Navigations"
                 r"\Legal Instruments Navigation\_working")
UPD = pathlib.Path(r"D:\CRE Decoding System\Updates")
HI = "\uffff"

# (name, script, args, cwd, stdout-log) - one row per PROCESS.
LANES = {
    "sync": [
        # THE CONSOLIDATED ACRIS LANE - sync + rd backfill + pdf pool, one
        # access point. Log goes to NAV_WORK (the board reads it there).
        # ⚠ NEVER COLD-LAUNCH (login 13:03, trip #3): the lane self-ramps
        # from width 8 - that is load-bearing, not a slow start. Restarts
        # are themselves a load event; minimize them.
        # ⚠ PIANO CONFIG (login 14:45, after trip #5): --max-inflight 1 means
        # rd, pdf AND THE SYNC WALKER can never be on the wire together -
        # "its not the number of requests, its the overlap when they
        # converge that tells them to block." All three organs take turns
        # down ONE kept-alive connection. Worker counts are SHARE OF THE
        # WIRE, not pressure. Do not raise --max-inflight without login.
        ("acris_lane", "acris_lane.py",
         ["--apply", "--workers", "8", "--pdf-workers", "12",
          "--max-inflight", "1", "--max-rps", "20"],
         HERE, W / "acris_lane.log"),
        ("rc_live", "rc_live.py",
         ["--apply", "--every", "10"], HERE, HERE / "rc_live.log"),
    ],
    "rcpdf": [
        ("rc_feed", "rc_feed.py",
         ["--miners", "24", "--ahead", "1200"], HERE, HERE / "rc_feed.log"),
        ("rc_pdf_pull", "rc_pdf_pull.py",
         ["--workers", "16", "--batch", "3"], HERE, HERE / "rc_pull.log"),
        ("rc_pdf_land", "rc_pdf_land.py",
         ["--loop", "--raw"], HERE, HERE / "rc_land_stdout.log"),
    ],
    "board": [
        # pass-2 arm: polls the board, releases the reference keyer at
        # acris rd >= 99.95% - part of the standing fleet (caught missing
        # 2026-08-24 after the lock-hunt kill; login asked "is pass 2
        # armed" and it was not running)
        ("org_backfill_arm", "org_backfill_arm.py",
         ["--poll", "600"], HERE, HERE / "org_backfill_arm.log"),
        ("routine_update", str(UPD / "routine_update.py"),
         ["--loop"], UPD, UPD / "routine_update.log"),
        # ⚠ board_truth.py lives in Updates\, NOT the decoder dir - a launch
        # with the wrong cwd dies instantly with "can't open file" and a PID
        # that looked healthy (caught by fleet.py status, 2026-08-24)
        ("board_truth", str(UPD / "board_truth.py"),
         ["--loop", "--every", "600"], UPD, UPD / "board_truth.log"),
    ],
}


def _running():
    """{marker: pid} for our scripts, via WMIC-free tasklist+cmdline scan."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
         " | ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }"],
        capture_output=True, text=True).stdout
    procs = {}
    for line in out.splitlines():
        pid, _, cmd = line.partition("|")
        if pid.strip().isdigit():
            procs[int(pid)] = cmd
    return procs


def _match(cmd, script, args):
    if pathlib.Path(script).name not in cmd:
        return False
    # the --lo VALUE uniquely identifies a walker arm (a4's --hi is a
    # 1-char sentinel and its --lo equals a3's --hi, so hi tokens and
    # bare substring checks mis-bind arms - match the --lo binding)
    if "--lo" in args:
        import re as _re
        want = args[args.index("--lo") + 1]
        m = _re.search(r'--lo"?\s+"?([^\s"]*)', cmd)
        return bool(m) and m.group(1) == want
    for token in args:
        if token and len(token) > 3 and token not in cmd:
            return False
    return True


def status():
    procs = _running()
    for lane, rows in LANES.items():
        print(lane)
        for name, script, args, _, _ in rows:
            pid = next((p for p, c in procs.items()
                        if _match(c, script, args)), None)
            print("  %-14s %s" % (name, "RUNNING pid %d" % pid if pid
                                  else "not running"))


def start(lane):
    procs = _running()
    for name, script, args, cwd, log in LANES[lane]:
        if any(_match(c, script, args) for c in procs.values()):
            print("  %-14s already running" % name)
            continue
        err = log.with_suffix(log.suffix + ".err")
        with log.open("w") as lo, err.open("w") as eo:
            p = subprocess.Popen(
                [PY, "-u", script] + args, cwd=str(cwd), stdout=lo,
                stderr=eo, creationflags=subprocess.CREATE_NO_WINDOW
                | subprocess.CREATE_NEW_PROCESS_GROUP)
        print("  %-14s started pid %d" % (name, p.pid))
        time.sleep(0.3)


def stop(lane):
    procs = _running()
    for name, script, args, _, _ in LANES[lane]:
        for pid, cmd in procs.items():
            if _match(cmd, script, args):
                subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                               capture_output=True)
                print("  %-14s stopped pid %d" % (name, pid))


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "status"
    target = sys.argv[2] if len(sys.argv) > 2 else "all"
    if verb == "status":
        status()
    else:
        lanes = list(LANES) if target == "all" else [target]
        if verb == "start" and target == "all":
            lanes = [l for l in lanes if l != "apdf"]   # parked stays parked
        for l in lanes:
            print(l)
            {"start": start, "stop": stop}[verb](l)
