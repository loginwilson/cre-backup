"""THE ORG BACKFILL, AS A MAINTENANCE WINDOW — drop index, key, rebuild.

    python org_bulk_key.py              # report only
    python org_bulk_key.py --apply      # do it (FLEET MUST BE PAUSED)

⚠ WHY THIS EXISTS. `nav_key.py` sweeps in python at ~163 keys/s, so the 5.9M
pre-trigger rows take ~10 hours. Login 2026-08-23: *"im super confused why it
would be hard for a keyer to quickly read ... this should take minutes."* Right,
and the reason it wasn't is invisible in the SQL. Measured on 3,000 rows:

    SET keyed_by  (NOT indexed)   138,774 rows/s   -> 5.9M in 0.7 MINUTES
    SET key       (INDEXED)            94 rows/s   -> 5.9M in 17.5 HOURS
    ------------------------------------------------ the index costs 1,482x

`ix_nav_key ON navigation(key)` turns every key write into a RANDOM insert into
a 24.1M-entry b-tree on a USB drive. The json parse, the row write and the
key_rules trigger are all rounding errors beside it.

So: DROP the index, write the keys with nothing to maintain, REBUILD it once.
A rebuild is a single sequential sort. 5.9M random inserts are not.

⚠ THE FLEET MUST BE PAUSED, AND THIS CHECKS. CREATE INDEX holds the single
writer seat for the whole build; every walker and both live lanes queue behind
it. The documented incident: "an index build held an exclusive write txn for
5+ min and killed all three walkers at once."

⚠ THE INDEX IS RECREATABLE, THE KEYS ARE NOT. If this dies between DROP and
CREATE, the data is intact and only the index is missing - rerun stage 3. That
asymmetry is why dropping an index is a safe move and dropping data is not.

⚠ TWO GUARDS THE OBVIOUS VERSION MISSES:
  json_valid()  - json_each RAISES on a malformed blob, which would abort the
                  whole transaction after doing all the work.
  'parcel' is decided by THE KEY BEING NON-EMPTY, not by parcels existing -
                  key_rules ABORTS on keyed_by='parcel' with an empty key, and
                  a parcel entry with a null $.bbl produces exactly that.
"""
from __future__ import annotations

import argparse
import pathlib
import sqlite3
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                      # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--batch", type=int, default=250_000,
                help="rows per transaction; bounds how much is lost on a kill")
ap.add_argument("--force", action="store_true",
                help="skip the fleet check (you had better be sure)")
a = ap.parse_args()

IX = "CREATE INDEX ix_nav_key ON navigation(key)"

KEY_SQL = """
WITH t AS (
  SELECT n.id AS id,
         COALESCE((SELECT group_concat(json_extract(value,'$.bbl'), ';')
                     FROM json_each(n.recorded_details, '$.parcels')), '') AS bbl
    FROM navigation n
   WHERE n.recorded_details != ''
     AND (n.keyed_by IS NULL OR n.keyed_by = '')
     AND json_valid(n.recorded_details)
   LIMIT ?
)
UPDATE navigation
   SET key = t.bbl,
       keyed_by = CASE WHEN t.bbl != '' THEN 'parcel' ELSE 'pdf-pass' END
  FROM t
 WHERE navigation.id = t.id
"""


def fleet_writing():
    """⚠ NAME THE PROCESSES, DO NOT ASSUME. A build that starts under load does
    not fail - it stalls every lane behind it for hours."""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
             " | ForEach-Object { $_.CommandLine }"],
            capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return ["(could not read the process list)"]
    names = ("rd_walk", "image_walk", "rc_feed", "rc_pdf_pull", "rc_pdf_land",
             "acris_live", "rc_live", "nav_key")
    return [n for n in names if n in out]


busy = fleet_writing()
print("=" * 70)
print("ORG BULK KEY — drop index · key · rebuild")
print("=" * 70)
print("  writers running: %s" % (", ".join(busy) if busy else "NONE (good)"))
if busy and not a.force:
    print()
    print("  ⚠ REFUSING. Pause these first - CREATE INDEX holds the writer seat")
    print("    for the whole build and every one of them will queue behind it.")
    if not a.apply:
        print("  (report mode: continuing to show the plan)")
    else:
        sys.exit(1)

con = sqlite3.connect(CP.NAV_DB, timeout=3600)
for p in ("busy_timeout=1800000", "cache_size=-400000", "temp_store=MEMORY"):
    con.execute("PRAGMA %s" % p)

# ⚠ DO NOT COUNT BEFORE WORKING. `COUNT(*) ... WHERE keyed_by=''` is an
# unindexed scan of 24.1M rows - measured at over six minutes, to print a
# number that changes as soon as we start. The batch loop reports actual
# progress, which is the only figure that is both true and free.
has_ix = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='ix_nav_key'"
                     ).fetchone()[0]
todo = None
if not a.apply:
    todo = con.execute(
        "SELECT COUNT(*) FROM navigation WHERE recorded_details!=''"
        " AND (keyed_by IS NULL OR keyed_by='') AND id < '3'"
        " AND id NOT LIKE 'RC!_%' ESCAPE '!'").fetchone()[0]
    print("  rows needing a key: %s" % "{:,}".format(todo))
print("  ix_nav_key present: %s" % bool(has_ix))
print()
if not a.apply:
    print("  --apply not given. Plan:")
    print("    1  DROP INDEX ix_nav_key")
    print("    2  bulk UPDATE in %s-row transactions" % "{:,}".format(a.batch))
    print("    3  %s" % IX)
    print()
    print("  measured: 138,774 rows/s without the index vs 94 with it.")
    sys.exit(0)

t0 = time.time()
# ── 1 · DROP ────────────────────────────────────────────────────────────────
if has_ix:
    t = time.time()
    con.execute("DROP INDEX ix_nav_key")
    con.commit()
    print("  1 · dropped ix_nav_key  (%.1fs)" % (time.time() - t))
else:
    print("  1 · ix_nav_key already absent - resuming")

# ── 2 · KEY ─────────────────────────────────────────────────────────────────
done, t_key = 0, time.time()
while True:
    t = time.time()
    try:
        n = con.execute(KEY_SQL, (a.batch,)).rowcount
        con.commit()
    except Exception as e:
        con.rollback()
        print("  ⚠ batch FAILED (%s: %.90s) - stopping. Keys already committed "
              "are kept; ix_nav_key is still DROPPED, rerun to finish."
              % (type(e).__name__, e))
        break
    if n <= 0:
        break
    done += n
    el = time.time() - t
    print("     keyed %9s  (+%s in %.1fs = %.0f/s)  total %.1f min"
          % ("{:,}".format(done), "{:,}".format(n), el, n / el if el else 0,
             (time.time() - t_key) / 60))
print("  2 · keyed %s row(s) in %.1f min"
      % ("{:,}".format(done), (time.time() - t_key) / 60))

# ── 3 · REBUILD ─────────────────────────────────────────────────────────────
t = time.time()
print("  3 · rebuilding ix_nav_key (one sequential sort; this is the long part)")
con.execute(IX)
con.commit()
print("      rebuilt in %.1f min" % ((time.time() - t) / 60))
con.close()
print()
print("  TOTAL %.1f min" % ((time.time() - t0) / 60))
