"""RUN THE CHECKPOINT FOREVER, APPENDING TO ONE LOG — the ongoing background task.

    ACRIS_CORPUS_ROOT=D:/acris python checkpoint_loop.py &

⚠ WHY A LOOP AND NOT A CHAIN OF ONE-SHOTS. Each checkpoint launched separately stops the
moment nobody relaunches it, so the record has holes exactly when attention lapsed —
which is when it is most wanted. This writes to `00-run/logs/checkpoints.log` until the
run itself ends.

⚠ IT MUST BE CHEAPER THAN WHAT IT MEASURES. Two ledger reads and one directory
enumeration (0.3 s for 7,400 parcels). It never reads a manifest and never queries the
spec DB — a 7,000-manifest walk on the same USB drive cost 20 pg/s on 2026-08-18, so the
monitor was briefly the biggest single drag on the thing it was monitoring.

⚠ IT STOPS WHEN THE WORK STOPS. If `_STOP` appears (a pause or a refusal) it records that
and exits rather than logging identical idle lines all night.
"""
from __future__ import annotations

import datetime, io, os, pathlib, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
import corpus_paths as CP

LOG = CP.log("checkpoints")
WINDOW = int(os.environ.get("CP_WINDOW", "600"))


def main():
    while True:
        if CP.STOP.exists():
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.datetime.now():%H:%M:%S}] _STOP present — "
                        f"{CP.STOP.read_text(encoding='utf-8', errors='replace').strip()}\n")
            return
        r = subprocess.run([sys.executable, str(HERE / "watch10.py"), str(WINDOW)],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=dict(os.environ,
                                                      ACRIS_CORPUS_ROOT=str(CP.ROOT)),
                           cwd=str(HERE))
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"\n===== {datetime.datetime.now():%Y-%m-%d %H:%M:%S} =====\n")
            f.write(r.stdout or "")
            if r.returncode != 0:
                f.write(f"[checkpoint exited {r.returncode}]\n{(r.stderr or '')[:400]}\n")


if __name__ == "__main__":
    main()
