"""THE MANIFEST — the ACRIS index IS the work list. Everything else is downstream.

⚠ THE ROOT CAUSE OF EVERY DEFECT FOUND TODAY.

The page images for lot 49 were collected WITHOUT an index-anchored manifest.
So the folder contains:

  · five documents belonging to OTHER PARCELS (two Brooklyn powers of
    attorney, a $410M Deutsche Bank loan on Block 827, a 1979 subordination
    on lot 53, and an in rem order with no legible block or lot)
  · one folder holding a DIFFERENT DOCUMENT'S BODY
  · five truncated documents, worst 1 page of 5

Not one of those is a reading failure. Every one is a FETCH failure, and
every one is impossible if the fetch is driven by the index.

⚠ AND THE INDEX IS FREE. It is structured data on NYC Open Data — no images,
no page reads, no tokens. The four datasets that matter:

    8h5j-fqxa  LEGALS      BBL -> document_id.  THE SPINE JOIN.
    bnx9-e6tj  MASTER      doc type, dates, amounts, CRFN, page count
    636b-3b5g  PARTIES     every party and its role
    pwkr-dpni  REFERENCES  document -> document cross-references

So the correct order is:

    LEGALS by BBL          -> the true document list, for free
    MASTER join            -> type, date, amount
    reconcile against disk -> FOREIGN (on disk, not in index)
                              MISSING (in index, not on disk)
    route by type          -> the specialist that reads it
    fetch pages            -> only for documents that survived all of the above

⚠ CORRECTION — I ASSERTED SOMETHING HERE THAT IS FALSE.

This file previously claimed "THE PAGE COUNT COMES FROM THE INDEX, NOT FROM
THE COVER PAGE," and that this removes the two-counter confusion entirely.
IT DOES NOT. A cold run over all 96 documents on lot 49 returned page_count
EMPTY FOR EVERY ONE. The count still has to be read off the cover page, so
the PAGE-1-OF-N vs Document-Page-Count rule still applies in full — and the
SHORT check below only fires when MASTER happens to carry a count, which on
this parcel is never.

⚠ I wrote that claim confidently, in a file whose entire purpose is to stop
me trusting a summary over a source. Measuring it took one query.

Run:  python manifest.py <bbl>          pull and reconcile
      python manifest.py 1008000049
"""
import json
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://data.cityofnewyork.us/resource"
LEGALS, MASTER = "8h5j-fqxa", "bnx9-e6tj"
PAGE = 1000


def fetch(dataset, where, select=None):
    """⚠ ALWAYS $order=:id. Without it $offset silently drops and duplicates
    rows while the COUNT stays right — a trap that has already corrupted a
    decoder in this project once."""
    out, offset = [], 0
    while True:
        q = {"$where": where, "$order": ":id",
             "$limit": PAGE, "$offset": offset}
        if select:
            q["$select"] = select
        url = f"{BASE}/{dataset}.json?" + urllib.parse.urlencode(q)
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            batch = json.loads(r.read().decode())
        out.extend(batch)
        if len(batch) < PAGE:
            return out
        offset += PAGE


def index_for(bbl):
    boro, block, lot = int(bbl[0]), int(bbl[1:6]), int(bbl[6:])
    where = f"borough={boro} AND block={block} AND lot={lot}"
    legals = fetch(LEGALS, where)
    ids = sorted({r["document_id"] for r in legals if r.get("document_id")})
    master = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        lst = "','".join(chunk)
        master.update({r["document_id"]: r
                       for r in fetch(MASTER, f"document_id in('{lst}')")})
    return ids, master, legals


def decoded():
    """⚠ A SWEPT DOCUMENT IS DONE, NOT MISSING. Once its claims are crop-backed
    the pages are deleted BY DESIGN, so reconciling only against pages_out
    reports finished work as a gap — which is exactly the false-alarm shape
    this whole file exists to remove."""
    import claims as K
    import reads as R
    return ({c["document_id"] for c in K.rows()} | set(R.OPENED))


def on_disk():
    import pathlib
    p = pathlib.Path("pages_out")
    if not p.is_dir():
        return {}
    return {d.name: len([f for f in d.iterdir() if f.is_file()])
            for d in p.iterdir() if d.is_dir()}


def main():
    bbl = sys.argv[1] if len(sys.argv) > 1 else "1008000049"
    print(f"ACRIS INDEX · BBL {bbl}\n")
    try:
        ids, master, legals = index_for(bbl)
    except Exception as e:
        print(f"  ⚠ index fetch failed: {type(e).__name__}: {e}")
        return
    disk = on_disk()
    print(f"  documents in the ACRIS index : {len(ids)}")
    print(f"  document folders on disk     : {len(disk)}\n")

    idx = set(ids)
    done = decoded()
    foreign = sorted(set(disk) - idx)
    missing = sorted(idx - set(disk) - done)      # never fetched at all
    swept = sorted((idx & done) - set(disk))      # decoded, pages reclaimed
    both = sorted(idx & set(disk))

    print(f"  ⚠ FOREIGN — on disk, NOT in this parcel's index : {len(foreign)}")
    for d in foreign:
        print(f"      {d}  {disk[d]:>3} pages")
    print(f"\n  ⚠ MISSING — in the index, never fetched : {len(missing)}")
    for d in missing[:40]:
        m = master.get(d, {})
        print(f"      {d}  {m.get('doc_type','?'):<10} "
              f"{(m.get('document_date') or '')[:10]:<12} "
              f"{m.get('document_amt','')}")
    if len(missing) > 40:
        print(f"      ... and {len(missing)-40} more")

    short = []
    for d in both:
        n = master.get(d, {}).get("page_count")
        if n and disk[d] < int(n):
            short.append((d, int(n), disk[d]))
    print(f"\n  ⚠ SHORT — fewer pages than the INDEX declares : {len(short)}")
    for d, n, have in short:
        print(f"      {d}  index says {n:>3}, on disk {have:>3}")

    print("\n" + "=" * 66)
    ok = len(both) + len(swept) - len(short)
    print(f"  USABLE {ok}/{len(ids)} indexed documents "
          f"({100*ok//max(len(ids),1)}%)")
    counted = sum(1 for d in both if master.get(d, {}).get("page_count"))
    print(f"  ⚠ MASTER carries a page_count for {counted}/{len(both)} of "
          f"these — the SHORT check above")
    print(f"    is only meaningful for those. Truncation still has to be")
    print(f"    caught from the cover page's own PAGE 1 OF N.")
    if foreign or missing or short:
        print("\n  ⚠ DO NOT DECODE FROM THIS FOLDER UNTIL IT RECONCILES.")


main()
