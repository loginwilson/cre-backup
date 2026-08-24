"""ARM THE ACRIS KEYING BACKFILL - fire it the moment acris rd closes.

WHY THIS EXISTS (login 2026-08-22: "I want acqs done and in all fairness
acris rd is only a 1-2 day job so we could prob just leave organizations
until after rd is done"). The decision was MEASURED, not preferred:

    backfill NOW   -> org clears ~26 h, rd finishes ~56 h
    backfill AFTER -> rd finishes ~45 h, org clears ~49 h   <- 7 h sooner

Keying is a follower with NOTHING downstream waiting on it (extraction is
not running), so buying keys early buys nothing and costs 30-40% of the
fleet. But "later" is exactly the kind of promise a system forgets, and the
~6.0M unkeyed rows are invisible in every board reading that is not looking
for them. So the promise gets a process instead of a note.

⚠ THE TRIGGER IS NOT THE BACKFILL. `key_on_rd` keys every NEW landing for
free (it writes inside rd's own transaction). It CANNOT reach rows written
before it existed - a trigger has no past tense. Those ~6.0M rows are the
entire job here, and without this pass organization tops out near 72%,
never 100%.

Usage:  python org_backfill_arm.py [--poll 300] [--threshold 99.95]
"""
import argparse
import pathlib
import sqlite3
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

BOARD = pathlib.Path(r"D:\CRE Decoding System\Updates\Updates.db")

ap = argparse.ArgumentParser()
ap.add_argument("--poll", type=int, default=300, help="seconds between checks")
ap.add_argument("--threshold", type=float, default=99.95,
                help="acris rd %% complete that releases the backfill")
ap.add_argument("--dry-run", action="store_true",
                help="report the decision without launching")
a = ap.parse_args()

# ⚠ OPERATING POINT, MEASURED - DO NOT 'OPTIMISE' IT BY SHRINKING THE BATCH.
# The obvious theory (big batch = long lock hold = starved lanes) is WRONG
# here. Tested 2026-08-22 against the live fleet:
#     2,000 / 20s  -> keyer ~170/s · rd ~55/s · pdf ~4.6/s
#       500 /  5s  -> keyer ~300/s · rd 5.5-43/s ERRATIC · pdf 0.5-2.7/s
# The keyer got FASTER while the fleet nearly collapsed. The tax is
# ACQUISITION FREQUENCY, not hold time: small batches take the one WAL
# writer 4x as often and every acquisition interrupts six lanes mid-commit.
# Fewer, larger acquisitions win. To go gentler, lengthen the SLEEP.
ARGS = ["--src", "acris", "--loop", "--limit", "5000", "--sleep", "5"]


def rd_pct():
    """acris rd completion, straight off the board - a cheap indexed read.
    ⚠ NEVER COUNT THE NAV TABLE TO ANSWER THIS. A 24M-row COUNT is the WAL
    trap that took the whole fleet down on 2026-08-21; the board already
    holds the number, measured, one row wide."""
    if not BOARD.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{BOARD}?mode=ro", uri=True, timeout=30)
        row = con.execute(
            "SELECT landed, needed, status FROM update_board"
            " WHERE phase IN ('synchronization', 'acquisition rd')"
            " AND source='acris' AND needed > 0"
            " ORDER BY CASE phase WHEN 'synchronization' THEN 0 ELSE 1 END"
            " LIMIT 1").fetchone()
        con.close()
    except sqlite3.Error:
        return None
    if not row or not row[1]:
        return None
    return row[0] / row[1] * 100


print(f"armed · releases acris keying backfill at rd >= {a.threshold}%"
      f" · polling every {a.poll}s", flush=True)
while True:
    pct = rd_pct()
    if pct is None:
        print("  board unreadable - will retry", flush=True)
    elif pct >= a.threshold:
        print(f"RELEASED · acris rd at {pct:.2f}% · starting backfill",
              flush=True)
        if a.dry_run:
            print(f"  (dry run) would run: nav_key.py {' '.join(ARGS)}",
                  flush=True)
        else:
            subprocess.Popen(
                [sys.executable, str(HERE / "nav_key.py")] + ARGS,
                cwd=str(HERE))
            print("  backfill launched · organization now closes its gap;"
                  " the board's org ETA starts reading a real number",
                  flush=True)
        break
    else:
        print(f"  acris rd {pct:.2f}% - holding "
              f"({a.threshold - pct:.2f}% to go)", flush=True)
    time.sleep(a.poll)
