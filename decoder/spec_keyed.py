"""IS THE SPECIFICATION KEYED FOR A PARCEL ACQUISITION? — four checks, denominators on all.

    ACRIS_CORPUS_ROOT=D:/acris python spec_keyed.py

⚠ WHY A PERCENTAGE IS THE WRONG ANSWER. "91.9% parcel-keyed" cannot tell you
whether the missing 8% is 1.75M UCC filings (correct — personal property has no
land to key to) or 1.75M deeds (a defect that silently truncates every title
chain). Same number, opposite meanings. **So the unreached set is broken out BY
DOCUMENT TYPE**, because that is what distinguishes them.

THE TWO WAYS A PARCEL KEY FAILS — Login, 2026-08-19:

  1 THE BBL CHANGED (lineage). A document filed under a lot that has since been
    merged, subdivided or condo-converted. 24,419 of the 1,250,935 BBLs ACRIS has
    named are identities DOF has superseded, carrying 545,345 documents. `family()`
    gathers a parcel plus every PREDECESSOR, so a successor's walk collects them —
    but only if the retired name is still reachable. CHECK 3 measures that instead
    of trusting it.

  2 IT IS NOT REAL PROPERTY. A UCC filing against business equipment has no BBL by
    nature and is reached by PARTY. Demanding a parcel key for it would either
    invent one or condemn ~4.5M correct records. CHECK 2 asks the question that
    actually matters — reachable by SOMETHING — and CHECK 4 shows what is not.

⚠ A DANGLING LINK IS NOT A LINK (check 1). parcel_document may name a bbl that is
absent from `parcel`. The walk selects FROM `parcel`, so such a document is linked
and still unreachable — the worst shape, because a link-counting audit scores it
as healthy.

Read-only. Safe beside the pull; do not run against a DB mid-landing (the numbers
would describe a state that no longer exists by the time they print).
"""
from __future__ import annotations

import os
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP
import lineage

FAILED = []


def head(n, s):
    print(f"\n{'='*74}\n  CHECK {n} · {s}\n{'='*74}", flush=True)


def main():
    if not CP.drive_present():
        sys.exit(f"  drive absent: {CP.SPEC_DB}")
    con = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=1")
    q = con.execute
    t0 = time.time()

    total = q("SELECT COUNT(*) FROM document").fetchone()[0]
    parcels = q("SELECT COUNT(*) FROM parcel").fetchone()[0]
    print(f"  specification: {total:,} documents · {parcels:,} parcels", flush=True)

    # ── 1 · DANGLING LINKS ───────────────────────────────────────────────
    head(1, "dangling parcel links — a link to a bbl the walk cannot select")
    dang = q("SELECT COUNT(DISTINCT pd.document_id) FROM parcel_document pd"
             " LEFT JOIN parcel p ON p.bbl = pd.bbl WHERE p.bbl IS NULL").fetchone()[0]
    print(f"  documents linked ONLY to a bbl absent from `parcel`: {dang:,}")
    if dang:
        FAILED.append(f"{dang:,} documents linked to a bbl not in `parcel`")
        for b, n in q("SELECT pd.bbl, COUNT(*) FROM parcel_document pd"
                      " LEFT JOIN parcel p ON p.bbl=pd.bbl WHERE p.bbl IS NULL"
                      " GROUP BY pd.bbl ORDER BY 2 DESC LIMIT 8"):
            print(f"    {b}  {n:,} documents")
    else:
        print("  ✓ every parcel link resolves to a selectable parcel")

    # ── 2 · REACHABLE BY SOMETHING ───────────────────────────────────────
    head(2, "reachable by SOMETHING — parcel or party (this must be 0)")
    unreach = q(
        "SELECT COUNT(*) FROM document d WHERE"
        " NOT EXISTS(SELECT 1 FROM parcel_document pd WHERE pd.document_id=d.document_id)"
        " AND NOT EXISTS(SELECT 1 FROM party_document pt WHERE pt.document_id=d.document_id)"
    ).fetchone()[0]
    print(f"  reachable by NEITHER parcel nor party: {unreach:,} of {total:,}")
    if unreach:
        FAILED.append(f"{unreach:,} documents reachable by neither path")
        print("  ⚠ these are invisible to acquisition forever, and look exactly")
        print("    like work not yet done. By type:")
        for t, n in q(
            "SELECT COALESCE(d.doc_type,'(none)'), COUNT(*) FROM document d WHERE"
            " NOT EXISTS(SELECT 1 FROM parcel_document pd WHERE pd.document_id=d.document_id)"
            " AND NOT EXISTS(SELECT 1 FROM party_document pt WHERE pt.document_id=d.document_id)"
            " GROUP BY 1 ORDER BY 2 DESC LIMIT 15"):
            print(f"    {t:<14} {n:>12,}")
    else:
        print("  ✓ every document is reachable by at least one path")

    # ── 3 · LINEAGE EXPOSURE ─────────────────────────────────────────────
    head(3, "lineage — documents whose only names are RETIRED")
    lineage._load()
    retired_all = set(lineage._FWD)          # any bbl with a successor is retired
    known = {r[0] for r in q("SELECT bbl FROM parcel")}
    retired_here = retired_all & known
    print(f"  retired names DOF has superseded, present in `parcel`: "
          f"{len(retired_here):,} of {len(known):,}")
    # a retired name still IN `parcel` is still selected by the walk, so its
    # documents are reached; the risk is a retired name NOT in `parcel`
    orphan_retired = q(
        "SELECT COUNT(DISTINCT pd.document_id) FROM parcel_document pd"
        " WHERE NOT EXISTS(SELECT 1 FROM parcel p WHERE p.bbl = pd.bbl)").fetchone()[0]
    print(f"  documents whose bbl is not selectable: {orphan_retired:,}")
    print(f"  ⓘ a RETIRED name that is still in `parcel` is still walked — its")
    print(f"    documents are reached directly, and family() also gathers them")
    print(f"    into the successor's record. Duplication is deduped by the ledger;")
    print(f"    the failure mode is a name that is not selectable at all (above).")

    # ── 4 · WHAT IS NOT PARCEL-KEYED, BY TYPE ────────────────────────────
    head(4, "not parcel-keyed — by document type (is it personal property?)")
    rows = q(
        "SELECT COALESCE(d.doc_type,'(none)'), COUNT(*) FROM document d"
        " WHERE NOT EXISTS(SELECT 1 FROM parcel_document pd"
        "                   WHERE pd.document_id=d.document_id)"
        " GROUP BY 1 ORDER BY 2 DESC LIMIT 25").fetchall()
    nokey = sum(n for _, n in rows)
    print(f"  documents with NO parcel link (top 25 types shown):")
    print(f"  {'type':<14}{'count':>14}")
    for t, n in rows:
        print(f"  {t:<14}{n:>14,}")
    print(f"\n  ⚠ READ THIS TABLE, DO NOT AVERAGE IT. UCC/personal-property types")
    print(f"    here are CORRECT — they have no land to key to. DEED, MTGE, DEEDO,")
    print(f"    AGMT and similar appearing here are REAL PROPERTY and would be")
    print(f"    silently skipped by a parcel walk.")

    print(f"\n{'='*74}")
    if FAILED:
        print("  ⚠ NOT READY — acquisition would silently miss documents:")
        for f in FAILED:
            print(f"      {f}")
    else:
        print("  ✓ every document is reachable and every parcel link resolves.")
    print(f"  ({time.time()-t0:.0f}s)")
    con.close()


if __name__ == "__main__":
    main()
