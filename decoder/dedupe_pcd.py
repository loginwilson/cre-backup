"""DEDUPE parcel_document, ADD ITS MISSING PRIMARY KEY, AND SHOW PROGRESS.

    ACRIS_CORPUS_ROOT=D:/acris python dedupe_pcd.py

WARNING - WHY THERE ARE DUPLICATES. parcel_document was created with NO primary
key and NO unique constraint, so INSERT OR IGNORE had nothing to conflict against
and every re-run re-inserted rows already present. Measured 2026-08-18:
34,043,930 rows where 26,742,947 are real. document / party_document /
reference_document / remark_document all have real keys and are unaffected.

WARNING - THIS IS NOT JUST TODAY'S CLEANUP. live_land.py uses the same
INSERT OR IGNORE on this table and runs EVERY DAY in the routine, so any
overlapping window duplicated links silently - and parcel.n_docs is COUNT(*) over
this table, which acquisition FILTERS AND RANKS ON. The key closes a daily leak.

WARNING - THE KEY IS ALSO THE INDEX n_docs NEEDS. With ix_pd_bbl dropped for bulk
loading, COUNT(*) WHERE bbl = ? became a full scan of 34M rows, once per parcel,
367,687 times. The PRIMARY KEY (bbl, document_id) turns that into a seek.

WARNING - ORDER BY IS THE WHOLE PERFORMANCE STORY. A bare INSERT..SELECT places
each row at a RANDOM position in a 5 GB B-tree - random writes, and the first
attempt went I/O-bound at ~1% CPU with no way to see progress. Feeding rows in
KEY ORDER makes every insert an append. Same result, sequential I/O.

WARNING - CHUNKED SO PROGRESS IS VISIBLE. A single INSERT..SELECT reports nothing
until it commits, so "working" and "deadlocked" look identical - which cost three
premature kills today. This prints every chunk.
"""
from __future__ import annotations

import sqlite3
import sys
import time

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP

CHUNK = 200_000

con = sqlite3.connect(CP.SPEC_DB, timeout=7200)
con.execute("PRAGMA busy_timeout=7200000")
con.execute("PRAGMA synchronous=OFF")
con.execute("PRAGMA cache_size=-2000000")   # ~2 GB page cache
con.execute("PRAGMA temp_store=FILE")

t0 = time.time()
before = con.execute("SELECT COUNT(*) FROM parcel_document").fetchone()[0]
print("  before %s rows" % format(before, ","), flush=True)

con.executescript("""
DROP TABLE IF EXISTS parcel_document_new;
CREATE TABLE parcel_document_new (
  bbl TEXT NOT NULL, document_id TEXT NOT NULL, partial_lot TEXT,
  easement TEXT, air_rights TEXT, subterranean TEXT, property_type TEXT,
  PRIMARY KEY (bbl, document_id)) WITHOUT ROWID;
""")
print("  target table created (%.0fs)" % (time.time() - t0), flush=True)

# WARNING - TWO CONNECTIONS, NOT ONE. Committing on the SAME connection that
# holds an open ORDER BY cursor throws "database is locked" - it survived 5.2M
# rows on 2026-08-18 and then died when the sort spilled to disk. The reader gets
# its own read-only connection so the writer can commit freely.
rcon = sqlite3.connect("file:" + str(CP.SPEC_DB).replace("\\", "/") + "?mode=ro",
                       uri=True, timeout=7200)
rcon.execute("PRAGMA busy_timeout=7200000")
rcon.execute("PRAGMA cache_size=-1000000")
cur = rcon.execute(
    "SELECT bbl, document_id, partial_lot, easement, air_rights, "
    "subterranean, property_type FROM parcel_document "
    "ORDER BY bbl, document_id")
print("  scan started, streaming in chunks of %s" % format(CHUNK, ","), flush=True)

read = 0
while True:
    rows = cur.fetchmany(CHUNK)
    if not rows:
        break
    con.executemany(
        "INSERT OR IGNORE INTO parcel_document_new VALUES (?,?,?,?,?,?,?)", rows)
    con.commit()
    read += len(rows)
    el = time.time() - t0
    rate = read / max(el, 1)
    left = (before - read) / max(rate, 1)
    print("    %s/%s  %s rows/s  %.0f min left"
          % (format(read, ","), format(before, ","), format(int(rate), ","),
             left / 60), flush=True)

after = con.execute("SELECT COUNT(*) FROM parcel_document_new").fetchone()[0]
print("  distinct %s  (removed %s)  %.0fs"
      % (format(after, ","), format(before - after, ","), time.time() - t0),
      flush=True)

con.executescript("""
DROP TABLE parcel_document;
ALTER TABLE parcel_document_new RENAME TO parcel_document;
CREATE INDEX IF NOT EXISTS ix_pd_doc ON parcel_document(document_id);
""")
con.commit()
print("  swapped, ix_pd_doc rebuilt (%.0fs)" % (time.time() - t0), flush=True)

print("  recomputing n_docs - a SEEK now, not a scan...", flush=True)
con.execute("UPDATE parcel SET n_docs = (SELECT COUNT(*) FROM parcel_document pd "
            "WHERE pd.bbl = parcel.bbl)")
con.commit()
print("  DONE %.0fs - parcel_document %s rows"
      % (time.time() - t0, format(after, ",")), flush=True)
rcon.close()
con.close()
