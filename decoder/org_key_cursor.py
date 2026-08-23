"""THE ORG BACKFILL, CURSOR-WALKED — login's design, 2026-08-23.

    python org_key_cursor.py --apply

*"cant you filter the table so the only rows showing have columns with rd
filled and no key filled? that makes it a top to bottom back fill"* — exactly.
Two row filters, walked ONCE in id order behind a cursor:

    recorded_details != ''  AND  keyed_by = ''
      parcels in the rd -> keyed_by='parcel',   key = bbl[;bbl...]
      no parcels        -> keyed_by='pdf-pass', key = ''   (rd read, unkeyable)

⚠ WHY THE PREVIOUS ATTEMPT (org_bulk_key.py) REPORTED "keyed 0". It trusted
cursor.rowcount on an `UPDATE ... FROM (CTE)`, a statement shape where rowcount
is not reliable, then `if n <= 0: break` quit after one batch and went straight
to rebuilding the index. This version counts what it actually wrote
(executemany over explicit ids) and prints EVERY batch, flushed - a run that
says nothing for 6 minutes is indistinguishable from a dead one.

⚠ THE CURSOR IS WHAT MAKES IT NOT O(n²). A filter-only batch loop re-scans all
previously-keyed rows every batch. `id > cursor ORDER BY id` rides the PK, so
every row is read once for the whole run. (An index range scan measured
23,802 rows/s vs 341/s fetching via ix_nav_key - sequential wins, which is
also why no new index is needed for this.)

⚠ ix_nav_key MUST BE ABSENT WHILE WRITING. Measured 2026-08-23 on 3,000 rows:
SET on a non-indexed column 138,774 rows/s; SET key with ix_nav_key present
94 rows/s - the index costs 1,482x (every key is a random insert into a 24M-
entry b-tree on the USB drive). Drop it, write, rebuild ONCE (a sequential
sort). ⚠ If this dies mid-run: keys committed are KEPT, the index is simply
absent - rerun, it resumes at the cursor and rebuilds at the end.

⚠ INVALID JSON IS pdf-pass, NOT A CRASH AND NOT A SKIP. json_each RAISES on a
malformed blob (aborting the batch), and skipping leaves rows silently unkeyed
forever. json_valid() gates the parse; invalid -> '' -> pdf-pass, same as
"rd read, no usable parcels".

⚠ 'parcel' IS DECIDED BY THE KEY BEING NON-EMPTY, not by parcels existing -
key_rules ABORTS keyed_by='parcel' with an empty key, and a parcels array
whose $.bbl values are null produces exactly that.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                      # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--batch", type=int, default=50_000)
ap.add_argument("--no-rebuild", action="store_true",
                help="skip the index rebuild (to chain another maintenance job)")
a = ap.parse_args()

STATE = HERE / "_org_key_cursor.json"

# bbl computed IN the SELECT: one pass, no python json parsing
SEL = """
SELECT id,
       CASE WHEN json_valid(recorded_details)
            THEN COALESCE((SELECT group_concat(json_extract(value,'$.bbl'), ';')
                             FROM json_each(recorded_details, '$.parcels')), '')
            ELSE '' END
  FROM navigation
 WHERE id > ?
   AND recorded_details != ''
   AND (keyed_by IS NULL OR keyed_by = '')
 ORDER BY id
 LIMIT ?
"""

con = sqlite3.connect(CP.NAV_DB, timeout=3600)
for p in ("busy_timeout=1800000", "cache_size=-400000", "temp_store=MEMORY"):
    con.execute("PRAGMA %s" % p)

has_ix = con.execute(
    "SELECT 1 FROM sqlite_master WHERE name='ix_nav_key'").fetchone()
cursor = ""
if STATE.exists():
    cursor = json.loads(STATE.read_text(encoding="utf-8")).get("cursor", "")
print("ORG KEY CURSOR · ix_nav_key %s · resume from %r"
      % ("PRESENT" if has_ix else "absent (good)", cursor or "start"),
      flush=True)

if not a.apply:
    rows = con.execute(SEL, (cursor, 5)).fetchall()
    for did, bbl in rows:
        print("  would key %s -> %s %r"
              % (did, "parcel" if bbl else "pdf-pass", bbl[:40]), flush=True)
    print("--apply not given: NOTHING WRITTEN")
    sys.exit(0)

if has_ix:
    t = time.time()
    print("dropping ix_nav_key (writes are 1,482x slower with it present)...",
          flush=True)
    con.execute("DROP INDEX ix_nav_key")
    con.commit()
    print("  dropped in %.0fs" % (time.time() - t), flush=True)

t0, total, parcels, passes = time.time(), 0, 0, 0
while True:
    t = time.time()
    rows = con.execute(SEL, (cursor, a.batch)).fetchall()
    if not rows:
        print("no more rows above the cursor - keying DONE", flush=True)
        break
    up = [("parcel" if bbl else "pdf-pass", bbl, did) for did, bbl in rows]
    cur = con.executemany(
        "UPDATE navigation SET keyed_by=?, key=? WHERE id=? AND keyed_by=''",
        up)
    con.commit()
    cursor = rows[-1][0]
    # ⚠ THE CURSOR ADVANCES ONLY AFTER THE COMMIT (index_daily's law)
    STATE.write_text(json.dumps({"cursor": cursor}), encoding="utf-8")
    n = cur.rowcount if cur.rowcount and cur.rowcount > 0 else len(rows)
    total += n
    b_parcel = sum(1 for k, _b, _d in up if k == "parcel")
    parcels += b_parcel
    passes += len(rows) - b_parcel
    el = time.time() - t
    print("  keyed %9s  (+%s in %5.1fs = %6.0f/s)  parcel %s · pdf-pass %s · at %s"
          % ("{:,}".format(total), "{:,}".format(n), el,
             n / el if el else 0, "{:,}".format(parcels),
             "{:,}".format(passes), cursor[:16]), flush=True)

print("KEYED %s in %.1f min  (parcel %s · pdf-pass %s)"
      % ("{:,}".format(total), (time.time() - t0) / 60,
         "{:,}".format(parcels), "{:,}".format(passes)), flush=True)

if not a.no_rebuild:
    t = time.time()
    print("rebuilding ix_nav_key (one sequential sort)...", flush=True)
    con.execute("CREATE INDEX ix_nav_key ON navigation(key)")
    con.commit()
    print("  rebuilt in %.1f min" % ((time.time() - t) / 60), flush=True)
con.close()
print("ALL DONE in %.1f min total" % ((time.time() - t0) / 60), flush=True)
