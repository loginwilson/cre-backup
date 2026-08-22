"""RESTORE RICHMOND doc_type FROM ITS OWN LEDGER — undo an ACRIS-scoped sweep.

    ACRIS_CORPUS_ROOT=D:/acris python rc_doctype_restore.py            report
    ACRIS_CORPUS_ROOT=D:/acris python rc_doctype_restore.py --apply

⚠ WHY THIS EXISTS. _doctype_backfill.py normalised document.doc_type onto ACRIS's
control-code vocabulary but was NOT scoped to ACRIS, so it also rewrote Richmond
rows: MORTGAGE -> MTGE (~644k), DECLARATION -> DECL, EASEMENT -> EASE, LEASE ->
LEAS. Richmond is a separate register with its OWN vocabulary (64 types: MORTGAGE,
DEED, SAT, A/MTG, CONSOLIDATION AGR, P/ATTY, REL, UCC ...).

⚠ RESTORE FROM SOURCE, NEVER BY INVERTING THE MAP. Richmond natively uses SAT for
407,370 documents, and SAT is also an ACRIS code - so inverting (code -> descrip-
tion) would flip rows the sweep never touched and corrupt them. The ledger is the
authority: it holds one doc_type per document, measured 0 conflicts across
2,891,086 link rows / 2,426,404 documents, so document -> doc_type is a function.

⚠ SIDE DATABASE, NOT A PYTHON DICT. 2.4M ids in memory competes with a running
pull on a 16 GB box that thrashes at 0.8 GB free.
"""
from __future__ import annotations
import argparse, json, pathlib, sqlite3, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP

LEDGER = pathlib.Path("D:/acris/01-specification/index/rc_ledger.jsonl")
SIDE = pathlib.Path("D:/acris/00-run/state/_rc_doctype_restore.db")


def build_side():
    if SIDE.exists():
        SIDE.unlink()
    s = sqlite3.connect(SIDE)
    s.execute("CREATE TABLE t (did TEXT PRIMARY KEY, dt TEXT)")
    batch, n = [], 0
    with LEDGER.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            iid, dt = r.get("internal_id"), r.get("doc_type")
            if not iid or not dt:
                continue
            batch.append(("RC_" + str(iid), dt))
            if len(batch) >= 50000:
                s.executemany("INSERT OR IGNORE INTO t VALUES (?,?)", batch)
                n += len(batch); batch = []
    if batch:
        s.executemany("INSERT OR IGNORE INTO t VALUES (?,?)", batch)
        n += len(batch)
    s.commit()
    got = s.execute("SELECT COUNT(*) FROM t").fetchone()[0]
    s.close()
    print(f"  ledger -> side db: {n:,} rows read · {got:,} distinct documents")
    return got


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    build_side()

    con = sqlite3.connect(CP.SPEC_DB, timeout=7200)
    con.execute("ATTACH DATABASE ? AS src", (str(SIDE),))
    diff = con.execute(
        "SELECT COUNT(*) FROM document d JOIN src.t t ON t.did = d.document_id"
        " WHERE d.doc_type IS NOT t.dt").fetchone()[0]
    print(f"  Richmond rows whose doc_type differs from the ledger: {diff:,}")
    for dt_now, dt_led, n in con.execute(
            "SELECT d.doc_type, t.dt, COUNT(*) FROM document d"
            " JOIN src.t t ON t.did = d.document_id"
            " WHERE d.doc_type IS NOT t.dt GROUP BY 1,2 ORDER BY 3 DESC LIMIT 12"):
        print(f"    {str(dt_now):<24} -> {str(dt_led):<28} {n:>9,}")

    if not a.apply:
        print("\n  --apply not given; nothing written.")
        con.close(); return

    cur = con.execute(
        "UPDATE document SET doc_type = (SELECT t.dt FROM src.t t"
        "                                WHERE t.did = document.document_id)"
        " WHERE substr(document_id,1,3)='RC_'"
        "   AND EXISTS (SELECT 1 FROM src.t t WHERE t.did = document.document_id"
        "               AND t.dt IS NOT document.doc_type)")
    con.commit()
    print(f"\n  restored {cur.rowcount:,} rows")
    left = con.execute(
        "SELECT COUNT(*) FROM document d JOIN src.t t ON t.did = d.document_id"
        " WHERE d.doc_type IS NOT t.dt").fetchone()[0]
    print(f"  still differing: {left:,}   <- must be 0")
    print(f"  {(time.time()-t0)/60:.1f} min")
    con.close()


if __name__ == "__main__":
    main()
