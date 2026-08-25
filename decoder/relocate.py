"""MOVING LOCATIONS: put the fleet down clean, bring it back HOT.

login 2026-08-25: "I will be moving locations again so you need to get it
ready so that when i reconnect with wifi and tell you, that we can get it
warmed up and throughput high again" ... "on both".

    python relocate.py down     stop everything, release D:, ready to eject
    python relocate.py up       start both lanes warm + the supervisor
    python relocate.py check    what is running and what the tempo remembers

>> WHAT THE LANES ACTUALLY PRODUCE IS *SYNCED ROWS*, NOT FILES (login
2026-08-25: "when you say 'pdfs' its important that you realize its about the
entire sync pipeline"). The counter named `pdfs` is the last gate of a chain
that is rd -> key -> image -> READY, so a row only advances it once the WHOLE
pipeline closed on that document. Reading it as "files downloaded" undersells
it and, worse, invites tuning the image fetch in isolation.

⚠⚠ ORDER MATTERS ON THE WAY DOWN. keepalive.py MUST die first. It is a
supervisor: stop a lane while it is watching and it dutifully restarts the
lane within 60 s, and the eject then fails on a drive it just reopened.

⚠⚠ AND A PLANNED SHUTDOWN IS NOT A REFUSAL. acris marks lane_tempo.json
DIRTY when the server refuses, and a dirty flag means the next start must not
resume at the peak. A force-kill for a house move is not evidence about
acris - but the kill can leave the flag dirty anyway, and on 2026-08-25 that
cost an hour: the lane cold-started at 12/s against a measured 107.3/s peak
and was still only at 28/s half an hour later.

So `down` re-stamps the tempo CLEAN - but only after reading the log and
confirming NO REFUSAL was recorded. If a refusal IS on record the flag is
left exactly as it is and that is reported loudly. ⚠ This is the one thing in
here that could paper over a real signal, which is why it is conditional,
noisy, and never silent.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                      # noqa: E402

W = CP.NAV_WORK
TEMPO = W / "lane_tempo.json"
ACRIS_LOG = W / "acris_lane.log"
REFUSAL = ("REFUSED", "Bandwidth Notice", "ALL WORKERS STOPPED",
           "BACKFILL WORKERS STOPPED")
FLEET_NAMES = ("acris_lane", "rc_lane", "keepalive", "routine_update",
               "board_truth", "org_backfill_arm")
act = (sys.argv[1] if len(sys.argv) > 1 else "check").lower()


def ps():
    """pid -> command line, for every python process we own."""
    out = {}
    try:
        txt = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
             " | Select-Object ProcessId,CommandLine"
             " | ConvertTo-Csv -NoTypeInformation"],
            capture_output=True, text=True, timeout=90).stdout
    except Exception:
        return out
    for ln in txt.splitlines()[1:]:
        try:
            pid = int(ln.split(",")[0].strip('"'))
        except (ValueError, IndexError):
            continue
        out[pid] = ln
    return out


def fleet(*args):
    r = subprocess.run([sys.executable, str(HERE / "fleet.py")] + list(args),
                       cwd=str(HERE), capture_output=True, text=True,
                       timeout=180)
    for ln in (r.stdout or "").splitlines():
        print("   " + ln)


def refusal_on_record():
    if not ACRIS_LOG.exists():
        return ""
    try:
        tail = ACRIS_LOG.read_text(encoding="utf-8",
                                   errors="replace").splitlines()[-400:]
    except OSError:
        return ""
    for ln in reversed(tail):
        if any(m in ln for m in REFUSAL):
            return ln.strip()[:160]
    return ""


def show_tempo():
    try:
        d = json.loads(TEMPO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("   tempo   no lane_tempo.json - acris would start COLD")
        return None
    age = (time.time() - d.get("at", 0)) / 3600.0
    print("   tempo   rps %.1f - peak %.1f - %s - stamped %.1f h ago%s"
          % (d.get("rps", 0), d.get("best", 0),
             "clean" if d.get("clean") else "DIRTY", age,
             "  <- older than the 6 h warm window, would start COLD"
             if age > 6 else ""))
    return d


# ---------------------------------------------------------------- DOWN
if act == "down":
    print("PUTTING THE FLEET DOWN FOR A MOVE")
    live = ps()
    killed = 0
    for pid, ln in live.items():
        if "keepalive.py" in ln:
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Stop-Process -Id %d -Force" % pid],
                           capture_output=True, timeout=60)
            killed += 1
    print("   supervisor: %d keepalive process(es) stopped FIRST (a live"
          " supervisor restarts every lane below within 60 s)" % killed)
    time.sleep(2)
    print("   lanes:")
    fleet("stop", "sync")
    fleet("stop", "board")
    time.sleep(3)

    r = refusal_on_record()
    d = show_tempo()
    if d is not None:
        if r:
            print("   >> A REFUSAL IS ON RECORD - LEAVING THE TEMPO FLAG"
                  " EXACTLY AS IT IS. The next start will ramp cautiously,"
                  " which is correct. Do not override this by hand.")
            print("      %s" % r)
        elif not d.get("clean"):
            d["clean"] = True
            d["at"] = time.time()
            TEMPO.write_text(json.dumps(d))
            print("   tempo   re-stamped CLEAN - the flag was set by this"
                  " shutdown, and no refusal appears anywhere in the acris"
                  " log. A house move is not evidence about acris.")
        else:
            d["at"] = time.time()
            TEMPO.write_text(json.dumps(d))
            print("   tempo   clock refreshed so the peak is still inside the"
                  " 6 h warm window when you reconnect")

    still = [ln for pid, ln in ps().items()
             if any(k + ".py" in ln for k in FLEET_NAMES)]
    print()
    if still:
        print("%d fleet process(es) STILL RUNNING - the eject will fail:"
              % len(still))
        for ln in still:
            print("   %s" % ln[:150])
    else:
        print("EVERY FLEET PROCESS IS DOWN. D: is released - safe to eject.")
        print("   If windows still refuses, something OUTSIDE the fleet holds"
              " the drive (on 2026-08-24 it was an orphaned tail/grep from a"
              " watch loop). Event 225 names the holder.")
    print()
    print("   When you are back on wifi:  python relocate.py up")

# ---------------------------------------------------------------- UP
elif act == "up":
    print("BRINGING THE FLEET BACK UP")
    if not CP.NAV_DB.exists():
        print(">> THE CORPUS IS NOT REACHABLE AT %s" % CP.NAV_DB)
        print("   Re-attach the drive before starting - lanes that start"
              " without it fail per-row and burn the climb for nothing.")
        raise SystemExit(1)
    print("   corpus  reachable at %s" % CP.NAV_DB)
    show_tempo()
    print("   lanes:")
    fleet("start", "sync")
    fleet("start", "board")
    time.sleep(2)
    subprocess.Popen([sys.executable, "-u", str(HERE / "keepalive.py")],
                     cwd=str(HERE),
                     stdout=(HERE / "keepalive.out").open("a"),
                     stderr=subprocess.STDOUT)
    print("   supervisor: keepalive started LAST, so its first pass sees the"
          " lanes running rather than missing")
    print()
    print("   >> GIVE ACRIS A LONG WARM-UP BEFORE JUDGING IT (login"
          " 2026-08-25: \"90+ is ideal and more time warming up is required"
          " thats all\"). The pool is cold, the first window carries the"
          " spin-up, and the ladder needs uninterrupted clean minutes to")
    print("      step at all. Watch for the WARM RESUME line, then let it sit."
          " Judge on SYNCED ROWS/s, never on the request rate.")
    print("   then:  python relocate.py check")

# ---------------------------------------------------------------- CHECK
else:
    print("FLEET CHECK  %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    live = ps()
    for want in FLEET_NAMES:
        hit = [pid for pid, ln in live.items() if want + ".py" in ln]
        print("   %-17s %s" % (want, "pid %s" % hit[0] if hit else "DOWN"))
    show_tempo()
    r = refusal_on_record()
    if r:
        print("   refusal on record in the acris log: %s" % r)
