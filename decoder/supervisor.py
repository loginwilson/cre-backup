"""KEEP ACQUISITION RUNNING WHENEVER THE DRIVE AND THE LINK ARE THERE.

    ACRIS_CORPUS_ROOT=D:/acris nohup python supervisor.py &

Login's standing instruction, 2026-08-18: *"if the drive is plugged in and the wifi is on
then this needs to be running essentially unless I say otherwise."*

⚠ THE WHOLE JOB IS TELLING FOUR SILENCES APART. A driver that is not running looks
identical from outside whether the drive was unplugged, the wifi dropped, Login paused it,
or ACRIS refused us. Three of those should resume automatically. The fourth must NEVER be
resumed, because the limiter is address-level and retrying a refusal costs Login their own
ACRIS access. So the flag is READ, not merely tested for existence:

    drive absent          -> wait. Not a stop. Login moved locations with the drive.
    link down             -> wait. Not a stop.
    _STOP "paused by hand"-> wait for Login. This IS "unless I say otherwise".
    _STOP "refused"       -> ⚠ STOP FOREVER. Report and exit. Never restart.
    nothing running, all clear -> start it.

⚠ IT MUST NOT BECOME THE SECOND DRIVER. Duplicates BREED here — each watchdog restarts a
driver it believes missing, and every copy draws on the same address-level budget while
believing it is the only client. So: check for a live overnight.py before starting, and
refuse to run as a second supervisor.

⚠ RESTARTS ARE BOUNDED. A driver that dies instantly and repeatedly is broken, not
unlucky; after --max-starts the supervisor stops and leaves the evidence.
"""
from __future__ import annotations

import argparse, datetime, os, pathlib, socket, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
import corpus_paths as CP

LOG = CP.log("supervisor")
ACRIS_HOST = "a836-acris.nyc.gov"


def say(m):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {m}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass          # the log lives on the drive; if it is gone, keep supervising


def drive_up():
    """⚠ TEST A PATH, NOT A DRIVE LETTER. Windows keeps D: in the namespace briefly after
    a yank; the corpus directory is what acquisition actually needs."""
    try:
        return (CP.ROOT / "00-run").is_dir() and CP.SPEC_DB.exists()
    except OSError:
        return False


def link_up():
    """A TCP connect, never an HTTP request — this is a reachability probe, not traffic."""
    try:
        with socket.create_connection((ACRIS_HOST, 443), timeout=6):
            return True
    except OSError:
        return False


def running(script, exclude_self=False):
    """⚠ EXCLUDE OUR OWN PID WHEN ASKING "IS ONE ALREADY RUNNING". Without it the
    singleton guard finds THIS process, concludes a supervisor exists, and exits —
    so the guard against duplicates guarantees zero instead. Third variant of the same
    self-count bug today (watchdog's wmic probe, watch10's `driver 4`, this)."""
    me = os.getpid()
    try:
        import psutil
        for p in psutil.process_iter(["pid", "name", "cmdline"]):
            if exclude_self and p.info["pid"] == me:
                continue
            try:
                if not (p.info.get("name") or "").lower().startswith("python"):
                    continue
                cl = p.info.get("cmdline") or []
                if len(cl) < 2:
                    continue
                nm = pathlib.Path(str(cl[1]) if str(cl[1]) != "-u"
                                  else (cl[2] if len(cl) > 2 else "")).name
                if nm == script:
                    return True
            except Exception:
                continue
    except Exception:
        return True          # ⚠ cannot tell -> assume yes; never start on ignorance
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=90)
    ap.add_argument("--until", default="23:59")
    ap.add_argument("--max-starts", type=int, default=20)
    a = ap.parse_args()

    if running("supervisor.py", exclude_self=True):
        print("supervisor already running — refusing to start a second copy")
        return

    say(f"SUPERVISOR up — acquisition runs whenever drive+link are present, "
        f"unless _STOP says otherwise")
    starts = 0
    was = {}
    while True:
        time.sleep(a.every)

        if not drive_up():
            if was.get("drive") is not False:
                say("⚠ drive not present — waiting. NOT a stop; will resume when it returns.")
            was["drive"] = False
            continue
        if was.get("drive") is False:
            say("drive back")
        was["drive"] = True

        if not link_up():
            if was.get("link") is not False:
                say(f"⚠ cannot reach {ACRIS_HOST} — waiting. NOT a stop.")
            was["link"] = False
            continue
        if was.get("link") is False:
            say("link back")
        was["link"] = True

        if CP.STOP.exists():
            why = CP.STOP.read_text(encoding="utf-8", errors="replace").strip()
            if "refused" in why.lower():
                say(f"⚠⚠ ACRIS REFUSED — {why}. NOT restarting, ever. Supervisor exiting.")
                return
            if was.get("stop") != why:
                say(f"paused by hand ({why}) — standing by until it is cleared")
            was["stop"] = why
            continue
        was.pop("stop", None)

        if not running("overnight.py"):
            if starts >= a.max_starts:
                say(f"⚠ {starts} starts already — the driver is broken, not unlucky. Exiting.")
                return
            starts += 1
            say(f"driver not running and everything is clear -> start #{starts}")
            subprocess.Popen([sys.executable, str(HERE / "pull.py"),
                              "--resume", "--until", a.until],
                             env=dict(os.environ, ACRIS_CORPUS_ROOT=str(CP.ROOT)),
                             cwd=str(HERE),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
