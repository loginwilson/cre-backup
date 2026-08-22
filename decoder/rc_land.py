"""LAND THE RICHMOND LEDGER — SI's corpus into the same five-table specification.

    ACRIS_CORPUS_ROOT=D:/acris python rc_land.py --check
    ACRIS_CORPUS_ROOT=D:/acris python rc_land.py --apply

WARNING - document_id IS RC_<internal_id>, NOT the instrument number. The
instrument is the official citation but old book-era numbering may collide
across eras; the internal id is the system's own unique key AND the endpoint
derives from it (viewDocumentInfo/<id>, ViewContent?p_endorsementId=<id>) - the
exact ACRIS pattern, where document_id is the system id and the official number
(CRFN) is a field. The instrument/book/page binding lives in rc_binding.

WARNING - ONE WRITER AT A TIME. Run only when nothing else writes the spec DB
(the lesson of three deadlocks on 2026-08-18).

WARNING - RECOMPUTE n_docs, NEVER INCREMENT - and only for touched parcels.
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

import corpus_paths as CP

LEDGER = pathlib.Path("D:/acris/01-specification/index/rc_ledger.jsonl")
BATCH = 20000

DDL = """
CREATE TABLE IF NOT EXISTS rc_binding (
  document_id TEXT PRIMARY KEY,       -- RC_<internal_id>
  instrument  TEXT,
  book        TEXT,
  page        TEXT
);
CREATE INDEX IF NOT EXISTS ix_rcb_instr ON rc_binding(instrument);
"""


def iso(s):
    try:
        m, d, y = (int(x) for x in (s or "").split("/"))
        return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, TypeError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ⚠ STREAM. The predecessor built a dict of every document and a set of every
    # (bbl, doc) link before writing anything - roughly a GB of Python objects at
    # 2.86M rows, on a 16 GB box that thrashes at 0.8 GB free. Nothing needed the
    # whole thing in memory: `document` is keyed by document_id and
    # `parcel_document` by (bbl, document_id), so INSERT OR IGNORE does the
    # dedupe the dict was doing, in the engine, at no memory cost.
    def ledger_rows():
        with LEDGER.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)

    def bbl_of(r):
        try:
            b, l = int(r["block"]), int(r["lot"])
            return f"5{b:05d}{l:04d}" if b and l else None
        except (ValueError, TypeError):
            return None

    rows = sum(1 for _ in ledger_rows())
    print(f"  ledger rows {rows:,} (streaming; dedupe is the primary key's job)")

    con = sqlite3.connect(CP.SPEC_DB, timeout=600)
    con.execute("PRAGMA busy_timeout=600000")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(DDL)
    q = con.execute
    before = {t: q(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("document", "parcel_document", "rc_binding")}
    print("  BEFORE:", {k: f"{v:,}" for k, v in before.items()})
    if not a.apply:
        print("  --check only.")
        return

    t0 = time.time()
    dbuf, bbuf, lbuf = [], [], []
    touched = set()          # BBLs only - needed for the n_docs recompute
    done = 0

    def flush():
        with con:
            if dbuf:
                con.executemany(
                    "INSERT OR IGNORE INTO document(document_id, doc_type, doc_date,"
                    " recorded_date, amount, reel_yr, reel_nbr, reel_pg, microfilm,"
                    " image_state) VALUES (?,?,NULL,?,?,'','','',0,'unknown')", dbuf)
            if bbuf:
                con.executemany(
                    "INSERT OR IGNORE INTO rc_binding(document_id, instrument, book,"
                    " page) VALUES (?,?,?,?)", bbuf)
            if lbuf:
                con.executemany(
                    "INSERT OR IGNORE INTO parcel_document(bbl, document_id)"
                    " VALUES (?,?)", lbuf)
        dbuf.clear(); bbuf.clear(); lbuf.clear()

    for r in ledger_rows():
        did = "RC_" + str(r["internal_id"])
        dbuf.append((did, r.get("doc_type"), iso(r.get("recorded")), "0"))
        bbuf.append((did, r.get("instrument"), r.get("book"), r.get("page")))
        b = bbl_of(r)
        if b:
            lbuf.append((b, did)); touched.add(b)
        done += 1
        if len(dbuf) >= BATCH:
            flush()
            if done % (BATCH * 10) == 0:
                rate = done / max(time.time() - t0, 1e-9)
                print(f"    {done:,}/{rows:,} · {rate:,.0f} rows/s · "
                      f"{(rows-done)/rate/60:.1f} min left")
    flush()
    print(f"  streamed in {time.time()-t0:.0f}s")

    bbls = sorted(touched)
    with con:
        con.executemany(
            "INSERT OR IGNORE INTO parcel(bbl, n_docs, first_date, last_date,"
            " n_microfilm) VALUES (?,0,NULL,NULL,0)", [(b,) for b in bbls])
    for i in range(0, len(bbls), BATCH):
        with con:
            con.executemany(
                "UPDATE parcel SET n_docs=(SELECT COUNT(*) FROM parcel_document"
                " pd WHERE pd.bbl=parcel.bbl) WHERE bbl=?",
                [(b,) for b in bbls[i:i + BATCH]])
    print(f"  n_docs recomputed on {len(bbls):,} SI parcels  {time.time()-t0:.0f}s")

    # invalidate any materialised SI manifests
    reopened = 0
    for b in bbls:
        f = CP.BYPARCEL / b[0] / b[1:6] / b[6:] / "_INDEX.md"
        if f.exists():
            f.unlink()
            reopened += 1
    print(f"  manifests invalidated: {reopened:,}")

    after = {t: q(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
             for t in ("document", "parcel_document", "rc_binding")}
    print(f"\n  RESULT ({(time.time()-t0)/60:.1f} min)")
    for k in before:
        print(f"    {k:<16} {before[k]:>12,} -> {after[k]:>12,}"
              f"  ({after[k]-before[k]:+,})")
    # watermark for live sync
    mx = max(int(r["internal_id"]) for r in ledger_rows())
    (HERE / "_rc_watermark.json").write_text(json.dumps(
        {"internal_id": mx, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "note": "max internal id landed; rc live sync gallops from here"},
        indent=1), encoding="utf-8")
    print(f"  watermark -> internal_id {mx}")
    con.close()


if __name__ == "__main__":
    main()
