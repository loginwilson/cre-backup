"""REBUILD reference_document WITH THE FULL KEY — the 5-col PK LOST DATA.

    ACRIS_CORPUS_ROOT=D:/acris python fix_reference_key.py

WARNING - WHAT WENT WRONG. The first PK was (document_id + 4 reel fields). But
CRFN-era references carry EMPTY reel fields, so every distinct CRFN reference on
one document collapsed to a single row: 16,424,863 source rows -> 9,420,932
landed, and the differing ref_crfn / ref_doc_id values were silently dropped.
A reference is identified by WHAT IT POINTS AT - the pointer belongs in the key.

WARNING - RE-STREAM FROM SOURCE, NOT FROM THE DEFICIENT TABLE. The collapsed rows
are gone from the table; only the D: files still have them.

WARNING - '' NOT NULL IN KEY COLUMNS. WITHOUT ROWID requires NOT NULL keys, and
None would throw; empty string carries the same meaning here (field not given).
"""
from __future__ import annotations

import gzip
import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP

IN = pathlib.Path("D:/acris/01-specification/index/index_staging")
CHUNK = 100_000

con = sqlite3.connect(CP.SPEC_DB, timeout=7200)
con.execute("PRAGMA busy_timeout=7200000")
con.execute("PRAGMA synchronous=OFF")
con.execute("PRAGMA cache_size=-1500000")

t0 = time.time()
con.executescript("""
DROP TABLE IF EXISTS reference_document_new;
CREATE TABLE reference_document_new (
  document_id TEXT NOT NULL,
  reel_year TEXT NOT NULL DEFAULT '', reel_borough TEXT NOT NULL DEFAULT '',
  reel_nbr TEXT NOT NULL DEFAULT '', reel_page TEXT NOT NULL DEFAULT '',
  ref_crfn TEXT NOT NULL DEFAULT '', ref_doc_id TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (document_id, reel_year, reel_borough, reel_nbr, reel_page,
               ref_crfn, ref_doc_id)) WITHOUT ROWID;
""")
print("  target table created", flush=True)


def s(v):
    return "" if v is None else str(v)


total = 0
for fn in ("references.jsonl.gz", "personal_references.jsonl.gz"):
    path = IN / fn
    if not path.exists():
        print(f"  MISSING {fn} - REFUSING a partial rebuild", flush=True)
        sys.exit(1)
    n = 0
    buf = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            buf.append((s(r.get("document_id")),
                        s(r.get("reference_by_reel_year")),
                        s(r.get("reference_by_reel_borough")),
                        s(r.get("reference_by_reel_nbr")),
                        s(r.get("reference_by_reel_page")),
                        s(r.get("reference_by_crfn_") or r.get("reference_by_crfn")),
                        s(r.get("reference_by_doc_id"))))
            if len(buf) >= CHUNK:
                con.executemany("INSERT OR IGNORE INTO reference_document_new "
                                "VALUES (?,?,?,?,?,?,?)", buf)
                con.commit()
                n += len(buf)
                buf = []
                if n % 2_000_000 < CHUNK:
                    print(f"    {fn} {n:,}  {time.time()-t0:.0f}s", flush=True)
    if buf:
        con.executemany("INSERT OR IGNORE INTO reference_document_new "
                        "VALUES (?,?,?,?,?,?,?)", buf)
        con.commit()
        n += len(buf)
    total += n
    print(f"  {fn}: {n:,} rows streamed  {time.time()-t0:.0f}s", flush=True)

after = con.execute("SELECT COUNT(*) FROM reference_document_new").fetchone()[0]
con.executescript("""
DROP TABLE reference_document;
ALTER TABLE reference_document_new RENAME TO reference_document;
CREATE INDEX IF NOT EXISTS ix_ref_doc ON reference_document(document_id);
""")
con.commit()
print(f"  DONE {time.time()-t0:.0f}s - streamed {total:,} -> "
      f"{after:,} distinct (true dupes removed: {total-after:,})", flush=True)
con.close()
