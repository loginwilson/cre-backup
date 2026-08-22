"""NAVIGATE BY DOCUMENT TYPE — and never touch the ACRIS site to do it.

⚠ THE NAVIGATION PROBLEM DISSOLVES. "How do we walk ACRIS by document type"
sounds like a site-traversal question — find a search form, page through
results, scrape rows. It is not. Socrata's MASTER dataset already holds every
document_id in the corpus keyed by doc_type, and LEGALS holds the BBLs. Both
are free, unthrottled, need no session, and cannot get anybody blocked.

    THE WORK LIST IS AN INDEX QUERY. ONLY THE PIXELS ARE SCARCE.

So the whole traversal is:

    Socrata MASTER   doc_type='DEVR'  ->  1,201 document_ids     free
    Socrata LEGALS   those ids        ->  their BBLs             free
    DocumentImageView?doc_id=X        ->  hid_TotalPages/Sup/Tax  one HTML load
    GetImage?doc_id=X&page=N          ->  the pages           ⚠ THROTTLED

⚠ AND document_id IS THE doc_id THE IMAGE ENDPOINT WANTS. Verified 2026-08-09
against the live site: the results table displays a CRFN (2026000013440) while
the image endpoint takes a doc_id (2026010900977002), and Socrata's
`document_id` is the SECOND one. Anyone building the work list by scraping the
results table would be doing throttled work to obtain a free field.

⚠ RETIRED BBLs ARE THE KNOWN HOLE. A 2005 DEVR is keyed to the lot numbers of
2005. Lots merge, split and retire, so a BBL join against today's parcel spine
silently drops documents — and the loss is invisible because the filter returns
clean-looking output. The BBL is recorded here AS FILED (`bbl_raw`); mapping it
to a current parcel is IDENTIFY's job, downstream, and must not be done here.
"""
import collections
import json
import pathlib
import sys

import bulk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MASTER = "bnx9-e6tj"
LEGALS = "8h5j-fqxa"
PARTIES = "636b-3b5g"


def worklist(doc_type, with_parties=False):
    """Every document of one type, citywide, with BBLs. No site access."""
    master = bulk.socrata(
        MASTER, where=f"doc_type='{doc_type}'",
        select="document_id,crfn,doc_type,document_date,recorded_datetime,"
               "recorded_borough,document_amt,reel_yr,reel_nbr,reel_pg",
        paginate=True)
    ids = [m["document_id"] for m in master]
    print(f"  {doc_type}: {len(ids):,} documents")

    legals = collections.defaultdict(list)
    for i in range(0, len(ids), bulk.IN_CLAUSE_MAX):
        q = ",".join(f"'{c}'" for c in ids[i:i + bulk.IN_CLAUSE_MAX])
        for r in bulk.socrata(LEGALS, where=f"document_id in({q})",
                              select="document_id,borough,block,lot,easement,"
                                     "partial_lot,property_type",
                              paginate=True):
            legals[r["document_id"]].append({
                "bbl_raw": f"{r['borough']}{int(r['block']):05d}{int(r['lot']):04d}",
                "borough": r["borough"], "block": r["block"], "lot": r["lot"],
                # ⚠ PARTIAL LOT IS NOT DECORATION. A document flagged partial
                # touches part of the tax lot only — routine on condo and
                # air-rights work — so a claim from it must NOT be attributed
                # to the whole parcel without checking which part.
                "partial_lot": r.get("partial_lot"),
                "easement": r.get("easement"),
            })

    rows = []
    for m in master:
        rows.append({**m, "legals": legals.get(m["document_id"], [])})
    unlinked = sum(1 for r in rows if not r["legals"])
    print(f"  {len(rows)-unlinked:,} linked to a BBL, "
          f"⚠ {unlinked:,} with NO legal record")
    return rows


def summarize(rows, doc_type):
    yrs = collections.Counter(
        (r.get("recorded_datetime") or "")[:4] for r in rows)
    boro = collections.Counter(r.get("recorded_borough") for r in rows)
    nleg = collections.Counter(len(r["legals"]) for r in rows)
    print(f"\n  {doc_type} — by borough: "
          + ", ".join(f"{k}:{v}" for k, v in sorted(boro.items()) if k))
    ys = sorted(y for y in yrs if y.isdigit())
    if ys:
        print(f"  recorded {ys[0]}–{ys[-1]}; busiest "
              + ", ".join(f"{y}({yrs[y]})" for y, _ in yrs.most_common(5)))
    # ⚠ A DOCUMENT ON MANY LOTS IS THE NORMAL CASE HERE, NOT AN ANOMALY — a
    # development-rights transfer names a granting lot and a receiving lot at
    # minimum, and a zoning lot merger can name a dozen.
    print(f"  lots per document: "
          + ", ".join(f"{k}→{v}" for k, v in sorted(nleg.items())[:8]))
    multi = sum(v for k, v in nleg.items() if k > 1)
    print(f"  {multi:,} documents touch MORE THAN ONE LOT "
          f"({100*multi/max(len(rows),1):.0f}%)")


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "DEVR"
    rows = worklist(t)
    summarize(rows, t)
    out = pathlib.Path(f"worklist_{t}.json")
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"\n  -> {out}  ({out.stat().st_size/1e6:.1f} MB)")
