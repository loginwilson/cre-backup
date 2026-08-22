"""UNIFY document.doc_type ONTO THE ACRIS CODE VOCABULARY.

    ACRIS_CORPUS_ROOT=D:/acris python _doctype_backfill.py --apply

⚠ TWO SPELLINGS OF ONE TYPE. The bulk path stored codes (MTGE), a second path
stored descriptions (MORTGAGE). 671,882 rows carry descriptions - 644,243 of them
MORTGAGE - so any GROUP BY doc_type, and every calibration in lexicon.py keyed on
MTGE/SAT/DEED, silently sees a fraction of the corpus.

⚠ THE CODE IS CANONICAL. lexicon.doc_type_canon() resolves description -> code
from ACRIS's own control-code table (126 codes -> 126 descriptions, 0 collisions),
so this is lossless and idempotent.

⚠ REVERSIBLE. _doctype_backfill_plan.json holds every (description, code, count)
pair, so the mapping can be inverted if this turns out to be the wrong direction.

⚠ ACRIS ROWS ONLY - THIS IS NOT OPTIONAL. The first version of this script had no
source scope and rewrote ~644,000 RICHMOND rows into ACRIS's vocabulary (MORTGAGE
-> MTGE). Richmond is a separate register with its own 64-type vocabulary; see
rc_doctype_restore.py, which had to put them back from the ledger. Every statement
below carries the ACRIS filter, and a reversal by inverting the map is UNSAFE
because Richmond natively uses SAT - which is also an ACRIS code.
"""

from __future__ import annotations
import argparse, json, pathlib, sqlite3, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP
import lexicon as LX

# ⚠ SOURCE SCOPE. ACRIS ids carry no prefix; other registers do.
ACRIS_ONLY = " AND substr(document_id,1,3) <> 'RC_' "

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    plan = json.loads(pathlib.Path("_doctype_backfill_plan.json").read_text(encoding="utf-8"))
    plan = [(d, c, n) for d, c, n in plan if d != c]
    print(f"  {len(plan)} labels · {sum(n for *_ , n in plan):,} rows to rewrite")

    con = sqlite3.connect(CP.SPEC_DB, timeout=7200)
    codes = sorted({c for _, c, _ in plan})
    ph = ",".join("?" * len(codes))
    before = dict(con.execute(f"SELECT doc_type, COUNT(*) FROM document"
                              f" WHERE doc_type IN ({ph})" + ACRIS_ONLY
                              + " GROUP BY doc_type", codes))
    print("\n  BEFORE (code spelling already present):")
    for c in codes[:8]:
        print(f"    {c:<12} {before.get(c, 0):>9,}")

    if not plan:
        # AN EMPTY PLAN IS A CLEAN RESULT, NOT A NO-OP TO FALL THROUGH.
        # Building "CASE doc_type END" with no WHEN is a SQL syntax error, so
        # without this the SUCCESS case - nothing left to normalise - crashes.
        print("\n  nothing to rewrite - ACRIS doc_type is already one vocabulary.")
        con.close()
        return

    if not a.apply:
        print("\n  --apply not given; nothing written."); return

    t0 = time.time()
    # one pass, all labels at once - 51 separate UPDATEs would be 51 table scans
    case = " ".join(f"WHEN ? THEN ?" for _ in plan)
    params = [x for d, c, _ in plan for x in (d, c)] + [d for d, _, _ in plan]
    ph2 = ",".join("?" * len(plan))
    cur = con.execute(f"UPDATE document SET doc_type = CASE doc_type {case} END"
                      f" WHERE doc_type IN ({ph2})" + ACRIS_ONLY, params)
    con.commit()
    print(f"\n  rewrote {cur.rowcount:,} rows in {(time.time()-t0)/60:.1f} min")

    descs = [d for d, _, _ in plan]
    left, = con.execute("SELECT COUNT(*) FROM document WHERE doc_type IN (%s)"
                        % ",".join("?" * len(descs)) + ACRIS_ONLY, descs).fetchone()
    print(f"  description-spelled rows remaining: {left:,}   <- must be 0")
    after = dict(con.execute(f"SELECT doc_type, COUNT(*) FROM document"
                             f" WHERE doc_type IN ({ph})" + ACRIS_ONLY
                             + " GROUP BY doc_type", codes))
    print("\n  AFTER:")
    for c in codes[:8]:
        print(f"    {c:<12} {before.get(c,0):>9,} -> {after.get(c,0):>9,}")
    con.close()

if __name__ == "__main__":
    main()
