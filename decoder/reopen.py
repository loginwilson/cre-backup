"""WHICH COMPLETE PARCELS HAVE NEW DOCUMENTS — and reopen them so the walk refetches.

    python reopen.py                 # report only (safe, the default)
    python reopen.py --apply         # delete the stale manifests
    python reopen.py --bbl 3002470009 --apply

⚠ WHY THIS EXISTS. `overnight.py` decides a parcel is finished by reading its `_INDEX.md`
and looking for `| not acquired |`. That manifest is a CACHE written when the parcel was
materialised, and it is deliberately not re-derived at skip time (re-deriving cost 14
minutes and 0 pages on restart). So when live sync adds a document to a parcel that was
already whole, the parcel is skipped FOREVER: the specification knows about the document
and acquisition never sees it.

⚠ DERIVED, NOT REPORTED. This asks the specification which parcels have outgrown their
manifest, rather than trusting the delta to hand over a list. A delta that half-fails
still reports the rows it thinks it wrote; the corpus itself cannot misreport what it
holds. Same reason `whats_live.py` computes the carry list from the import graph.

⚠ DELETE THE MANIFEST, DO NOT REGENERATE IT. Measured 2026-08-18: regenerating via
parcel_folder is 0.94 s/parcel, unlinking is 1.85 ms — 8.9 hours vs 63 seconds at 34,000
parcels. A parcel with no manifest is simply not in the driver's `finished` set, so it
re-enters the queue and the walk writes a fresh index at the end anyway.

⚠ THE COUNT TO COMPARE AGAINST IS THE LINEAGE FAMILY, DEDUPED — not `parcel.n_docs`.
`parcel_folder.rows()` lists every document across the parcel's predecessors, and a
document recorded against many lots appears once. Summing `n_docs` over a family
over-counts badly: Manhattan block 4's condo units carry 2,693 links over 78 unique
documents. Comparing against the wrong number would reopen thousands of parcels that are
in fact complete, and re-walk the entire corpus for nothing.
"""
from __future__ import annotations

import argparse, pathlib, re, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP

HDR = re.compile(r"\*\*(\d+) documents\*\*")


def expected(con, bbl, fam_cache):
    """DISTINCT documents across the parcel's lineage family — what the manifest lists."""
    try:
        import lineage
        fam = lineage.family(bbl)
    except Exception:
        fam = [bbl]
    qs = ",".join("?" * len(fam))
    return con.execute(
        f"SELECT COUNT(DISTINCT document_id) FROM parcel_document WHERE bbl IN ({qs})",
        list(fam)).fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually delete stale manifests")
    ap.add_argument("--bbl", action="append", default=[])
    ap.add_argument("--from", dest="src", default=None,
                    help="file of BBLs, one per line — the delta's touched list")
    a = ap.parse_args()

    con = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True)
    BY = CP.BYPARCEL

    # ⚠ TWO MODES, AND THE FAST ONE IS NOT A SUBSTITUTE FOR THE SLOW ONE.
    #   --from <file>  candidates from the delta: O(touched). This is the daily path.
    #   (no args)      sweep every manifest: O(materialised). Catches what the delta
    #                  under-reported, which its own row count cannot see.
    # ⚠ The delta narrows the CANDIDATES; the specification still decides. A delta that
    # half-failed still reports the rows it believes it wrote.
    # ⚠ NEVER PASS 16,000 BBLs AS --bbl: Windows caps a command line near 32k characters,
    # so the call is silently truncated or refused. Use --from.
    bbls = list(a.bbl)
    if a.src:
        bbls += [ln.strip() for ln in pathlib.Path(a.src).read_text(
            encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    if bbls:
        seen, uniq = set(), []
        for b in bbls:
            b = b.strip()
            if len(b) == 10 and b not in seen:
                seen.add(b); uniq.append(b)
        print(f"  candidates from delta: {len(uniq):,} parcels")
        mans = [BY / b[0] / b[1:6] / b[6:] / "_INDEX.md" for b in uniq]
    else:
        print("  full sweep of every materialised manifest (slow — prefer a pause)")
        mans = list(BY.rglob("_INDEX.md"))

    checked = stale = open_already = 0
    grew = 0
    for f in mans:
        if not f.exists():
            continue
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        checked += 1
        if "| not acquired |" in t:
            open_already += 1          # already queued; nothing to do
            continue
        m = HDR.search(t)
        if not m:
            continue
        stated = int(m.group(1))
        d = f.parent
        bbl = f"{d.parent.parent.name}{d.parent.name}{d.name}"
        exp = expected(con, bbl, None)
        if exp > stated:
            stale += 1; grew += exp - stated
            print(f"  {bbl}  manifest {stated} -> spec {exp}  (+{exp-stated})")
            if a.apply:
                f.unlink(missing_ok=True)

    print()
    print(f"  checked            {checked:,} manifests")
    print(f"  already open       {open_already:,}  (still have work queued)")
    print(f"  STALE / reopened   {stale:,}  carrying {grew:,} new documents")
    if stale and not a.apply:
        print("  -> nothing deleted. re-run with --apply to reopen them.")
    if not stale:
        print("  every complete parcel still matches the specification.")


if __name__ == "__main__":
    main()
