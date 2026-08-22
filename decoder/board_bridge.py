"""THE BOARD BRIDGE - mirrors each running lane's last PROGRESS line into
_working/<kind>_<taskid>.log, which routine_update glob-sums.

⚠ WHY THIS IS A FILE, NOT AN INLINE -c COMMAND (2026-08-22): the inline
version died with exit 127 when its shell context changed, and the board
silently fell back to bare baselines - acris rd read 7.8% when it was
26.8%, acris pdf read its baseline exactly. A phase that reports from a
feed must not depend on a shell one-liner staying alive.

⚠ CONSUMED-TASK GUARD (v5): a task output older than the dash_baseline
stamp is already INSIDE the baseline count - mirroring it again
double-counts (that is how richmond rd once read 100.17%). The baseline
mtime is re-read every pass, so a re-baseline immediately retires the
logs it consumed.

Usage:  python board_bridge.py [--quiet-exit-min 60]
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP

TASKS = pathlib.Path(
    r"C:\Users\smile\AppData\Local\Temp\claude\C--Users-smile"
    r"\2812a9cb-82a0-4f82-b389-d0bead413962\tasks")
BASE = CP.NAV_WORK / "dash_baseline.json"
KIND = {"rd walk phase 1": "rd_walk",
        "image walk [": "image_walk",
        "rc rd walk": "rc_rd_walk"}

ap = argparse.ArgumentParser()
ap.add_argument("--quiet-exit-min", type=int, default=0,
                help="exit after N quiet minutes; 0 = run forever")
a = ap.parse_args()

print(f"board bridge up · watching {TASKS}", flush=True)
quiet = 0
while True:
    moved = 0
    bstamp = BASE.stat().st_mtime if BASE.exists() else 0
    for p in TASKS.glob("*.output"):
        try:
            if p.stat().st_mtime <= bstamp:
                continue                      # consumed into the baseline
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        kind = next((v for k, v in KIND.items() if k in txt), None)
        if not kind:
            continue
        last = ""
        for ln in txt.splitlines():
            if "PROGRESS" in ln:
                last = ln
        if not last:
            continue
        out = CP.NAV_WORK / f"{kind}_{p.stem}.log"
        prev = out.read_text(encoding="utf-8", errors="replace") \
            if out.exists() else ""
        if last not in prev:
            out.write_text(last, encoding="utf-8")
            moved += 1
    if moved:
        print(f"  mirrored {moved} lane line(s)", flush=True)
        quiet = 0
    else:
        quiet += 1
    if a.quiet_exit_min and quiet >= a.quiet_exit_min:
        print("bridge exiting - no lane movement", flush=True)
        break
    time.sleep(60)
