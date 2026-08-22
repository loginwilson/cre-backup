"""LAND REFERENCES AND REMARKS — BOTH REGISTRIES. The last 2 of the 5 components.

    ACRIS_CORPUS_ROOT=D:/acris python land_index_rest.py --apply

⚠ THESE SAT ON DISK UNLANDED. references.jsonl.gz and remarks.jsonl.gz have been
in index_full since 2026-08-14 with no table to land into — present, correct, and
unreachable. That is the same failure as party_document: data that LOOKS held
because the file exists. A component is not held until something can select it.

⚠ NOT EVERY DOCUMENT HAS EVERY COMPONENT, AND THAT IS NOT A GAP.
    master      100%   it IS the record
    legals      where the document touches a parcel
    parties     where the document names anyone
    references  where the document points at a prior recording
    remarks     ~11% — 493,910 personal rows across 4,544,590 documents
The endpoint is ALWAYS constructible from document_id; whether it resolves to an
image is the no_image FINDING, not a missing component.

⚠ MIRROR THE PUBLISHED INDEX. No invented keys (see the party_key deletion).
"""
from __future__ import annotations
import argparse, os, gzip, json, pathlib, sqlite3, sys, time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP

# ⚠ THE INDEX LIVES ON THE CORPUS DRIVE, NOT NEXT TO THE CODE. C: filled to
# ZERO bytes on 2026-08-18 with the pull writing here; the files moved to D:
# and this path was NOT updated, so landing crashed on a missing file and the
# chain still reported rc=0 because its LAST command succeeded.
IN = pathlib.Path(os.environ.get("ACRIS_INDEX_OUT")
                  or "D:/acris/01-specification/index/index_staging")
BATCH = 20000

DDL = """
CREATE TABLE IF NOT EXISTS reference_document (
  document_id  TEXT NOT NULL,
  reel_year    TEXT, reel_borough TEXT, reel_nbr TEXT, reel_page TEXT,
  ref_crfn     TEXT, ref_doc_id  TEXT,
  PRIMARY KEY (document_id, reel_year, reel_borough, reel_nbr, reel_page)
);
CREATE INDEX IF NOT EXISTS ix_ref_doc ON reference_document(document_id);
CREATE TABLE IF NOT EXISTS remark_document (
  document_id     TEXT NOT NULL,
  sequence_number TEXT,
  remark_text     TEXT,
  PRIMARY KEY (document_id, sequence_number)
);
CREATE INDEX IF NOT EXISTS ix_rem_doc ON remark_document(document_id);
"""


def stream(p):
    if not p.exists():
        print(f"  ⚠ MISSING {p.name} — skipped (nothing landed for it)"); return
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def chunked(it, n=BATCH):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) >= n:
            yield buf; buf = []
    if buf:
        yield buf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    con = sqlite3.connect(CP.SPEC_DB, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(DDL); con.commit()
    b = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
         for t in ("reference_document", "remark_document")}
    print("BEFORE:", {k: f"{v:,}" for k, v in b.items()})
    if not a.apply:
        print("  --apply not given."); return
    t0 = time.time()

    for label, fn in (("real", "references.jsonl.gz"),
                      ("personal", "personal_references.jsonl.gz")):
        n = 0
        for ch in chunked(stream(IN / fn)):
            with con:
                con.executemany(
                    "INSERT OR IGNORE INTO reference_document(document_id, reel_year,"
                    " reel_borough, reel_nbr, reel_page, ref_crfn, ref_doc_id)"
                    " VALUES (?,?,?,?,?,?,?)",
                    [(r.get("document_id"), str(r.get("reference_by_reel_year") or ""),
                      str(r.get("reference_by_reel_borough") or ""),
                      str(r.get("reference_by_reel_nbr") or ""),
                      str(r.get("reference_by_reel_page") or ""),
                      r.get("reference_by_crfn_") or r.get("reference_by_crfn"),
                      r.get("reference_by_doc_id")) for r in ch])
            n += len(ch)
        print(f"  references/{label:<9} {n:>12,}  {time.time()-t0:.0f}s")

    for label, fn in (("real", "remarks.jsonl.gz"),
                      ("personal", "personal_remarks.jsonl.gz")):
        n = 0
        for ch in chunked(stream(IN / fn)):
            with con:
                con.executemany(
                    "INSERT OR IGNORE INTO remark_document(document_id,"
                    " sequence_number, remark_text) VALUES (?,?,?)",
                    [(r.get("document_id"), str(r.get("sequence_number") or ""),
                      r.get("remark_text")) for r in ch])
            n += len(ch)
        print(f"  remarks/{label:<12} {n:>12,}  {time.time()-t0:.0f}s")

    aft = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
           for t in ("reference_document", "remark_document")}
    print(f"\n  ── RESULT ({(time.time()-t0)/60:.1f} min) ──")
    for k in b:
        print(f"  {k:<20} {b[k]:>12,} -> {aft[k]:>12,}  ({aft[k]-b[k]:+,})")
    d = con.execute("SELECT COUNT(*) FROM document").fetchone()[0]
    print(f"\n  ── COMPONENT COVERAGE over {d:,} documents ──")
    for t, col in (("parcel_document", "parcel"), ("party_document", "party"),
                   ("reference_document", "reference"), ("remark_document", "remark")):
        c = con.execute(f"SELECT COUNT(DISTINCT document_id) FROM {t}").fetchone()[0]
        print(f"  has {col:<10} {c:>12,}  ({100*c/d:5.1f}%)")
    con.close()


if __name__ == "__main__":
    main()
