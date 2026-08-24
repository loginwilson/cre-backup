"""ARM PASS 2 - fire the reference keyer the moment the acris sync closes.

THE PASS MODEL (login 2026-08-24, verbatim): "doc id, urls, rd, pass 1,
pdf, repeat until 100%, pass 2, reach 100%, now extraction" and "acris
synchronization takes care of everything from sync all the way up through
pass 2 basically... but the percentage now is based on achieving pass 1."

So the board's `synchronization | acris` row IS this gate. Its percentage
is PASS 1 COMPLETE per doc - id + urls + rd + parcel key + pdf (or a held
imageless verdict). Not rd alone, not images alone: the whole row.

    pass 1   the parcel key the rd row can assign by itself, written by the
             key_on_rd trigger inside rd's own transaction - free, and it
             is what the sync percentage counts.
    pass 2   THIS. The docs pass 1 could not give a BBL, keyed from
             REFERENCES that tie a bbl to a doc. Local work off rd data,
             zero ACRIS requests - but it can only run once EVERY doc id
             is complete, because a reference into a doc that has not
             landed yet resolves to nothing.
    pass 3   extraction.

⚠ DO NOT RE-GATE THIS ON rd ALONE. On 2026-08-24 I read "acris rd 8.10%"
against ~75% actual rd and started patching the arm to measure rd
directly - reasoning that reference keying needs no images so it should
not wait on them. The reasoning was sound and the premise was wrong: pass
2 waits on ROW COMPLETION, not on its own input being available. A
reference pointing at a doc whose rd has not landed is a silent miss, and
misses at this stage are invisible - exactly the failure class this file
was written to prevent.

⚠ THE TRIGGER IS NOT THE BACKFILL. `key_on_rd` keys every NEW landing for
free. It CANNOT reach rows written before it existed - a trigger has no
past tense. Those ~6.0M rows are the entire job here, and without this
pass organization tops out near 72%, never 100%.

Usage:  python org_backfill_arm.py [--poll 600] [--threshold 99.95]
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
                help="acris sync %% complete (pass 1) that releases pass 2")
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


def sync_pct():
    """acris PASS 1 completion, straight off the board - a cheap indexed read.

    ⚠ NEVER COUNT THE NAV TABLE TO ANSWER THIS. A 24M-row COUNT is the WAL
    trap that took the whole fleet down on 2026-08-21; the board already
    holds the number, measured, one row wide.

    The row is `synchronization | acris`, whose landed = needed - pdf_todo
    (READY: urls + rd + pdf-or-imageless + key). The old `acquisition rd`
    row is no longer written - see the module docstring for why rd alone
    is the wrong gate anyway."""
    if not BOARD.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{BOARD}?mode=ro", uri=True, timeout=30)
        row = con.execute(
            "SELECT landed, needed FROM update_board"
            " WHERE phase='synchronization' AND source='acris' AND needed > 0"
            " LIMIT 1").fetchone()
        con.close()
    except sqlite3.Error:
        return None
    return row[0] / row[1] * 100 if row and row[1] else None


print(f"armed · releases acris pass 2 (reference keying) at sync"
      f" >= {a.threshold}% · polling every {a.poll}s", flush=True)
while True:
    pct = sync_pct()
    if pct is None:
        print("  board unreadable - will retry", flush=True)
    elif pct >= a.threshold:
        print(f"RELEASED · acris sync at {pct:.2f}% (pass 1 complete)"
              f" · starting pass 2", flush=True)
        if a.dry_run:
            print(f"  (dry run) would run: nav_key.py {' '.join(ARGS)}",
                  flush=True)
        else:
            subprocess.Popen(
                [sys.executable, str(HERE / "nav_key.py")] + ARGS,
                cwd=str(HERE))
            print("  pass 2 launched · organization now closes its gap;"
                  " the board's org ETA starts reading a real number",
                  flush=True)
        break
    else:
        print(f"  acris sync (pass 1) {pct:.2f}% - holding "
              f"({a.threshold - pct:.2f}% to go)", flush=True)
    time.sleep(a.poll)
