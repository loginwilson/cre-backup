"""What a parcel ALREADY KNOWS before anyone opens a document for it.

LOGIN, 2026-08-06:

    "The reason the ledger is important is that it can be applied to all
     involved lots. It saves us time reading the same document on multiple
     parcels."

THE ARITHMETIC, MEASURED ON BLOCK 800 (2026-08-06)

    Lot 49's decode read 96 documents. Those same documents appear in the ACRIS
    index of eight neighbouring lots:

        lot 20  94 docs · 12 already held      lot 50  37 docs · 10 held
        lot 21  43 docs · 13 already held      lot 53  91 docs · 33 held
        lot 22  42 docs · 16 already held      lot 55  88 docs · 28 held
        lot 23  46 docs · 20 already held      lot 56  82 docs · 28 held

        523 documents across the eight · 160 ALREADY HELD (31%)

    Without a DOCUMENT-KEYED registry those 160 get fetched again, read again,
    and decoded again — eight times over for the ZLDAs that name eight lots.
    With one, they are a lookup.

WHY THE KEY MUST BE THE DOCUMENT, NOT THE PARCEL

    The instinct is to key work by parcel: "have we done lot 53?" That question
    cannot be answered usefully, because lot 53's record overlaps lot 49's,
    lot 55's and lot 56's in different places. The answerable question is
    "have we read THIS DOCUMENT?" — and a document is read once, forever,
    for every parcel it touches.

    This is why claims carry `subject_bbl` separately from `bbl`. The 2010 ZLDA
    was read while working lot 49; it stated lot 53's lot area, generated area,
    retained area and excess. Those facts were filed under lot 53 AT THE MOMENT
    THEY WERE READ. When lot 53's own decode begins, they are already there —
    not as a cache to be revalidated, but as the same reading.

⚠ WHAT INHERITANCE IS NOT

    An inherited claim is NOT a substitute for decoding the parcel. It is a
    HEAD START with a known shape: it covers only the documents the other parcel
    happened to share. Lot 53 still has 58 documents nobody has opened. This
    module reports both halves, because "31% inherited" read as "31% done"
    would be exactly the kind of coverage inflation the fails register exists
    to catch.
"""
import json, os, pathlib, sys, urllib.request
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
LEGALS = "https://data.cityofnewyork.us/resource/8h5j-fqxa.json"


def _get(u):
    with urllib.request.urlopen(u.replace(" ", "%20")) as r:
        return json.load(r)


def index_docs(boro, block, lot):
    out, off = set(), 0
    while True:
        r = _get(f"{LEGALS}?borough={boro}&block={block}&lot={lot}"
                 f"&$select=document_id&$order=:id&$limit=1000&$offset={off}")
        out |= {x["document_id"] for x in r}
        if len(r) < 1000:
            return out
        off += 1000


def decoded_documents():
    """Every document any decode has READ, keyed by document_id.

    ⚠ Sourced from CLAIMS, not from the disk. A file in pages_out proves a
    fetch; only a claim proves a reading. Conflating the two is how "96 of 96
    documents fetched" became, in an earlier draft, "96 documents decoded".
    """
    sys.path.insert(0, str(HERE))
    import claims as K
    by_doc = defaultdict(list)
    for c in K.rows():
        by_doc[c["document_id"]].append(c)
    return by_doc


def inherit(boro, block, lot):
    bbl = f"{boro}{int(block):05d}{int(lot):04d}"
    live = index_docs(boro, block, lot)
    by_doc = decoded_documents()
    held = set(os.listdir(HERE / "pages_out")) if (HERE / "pages_out").exists() else set()

    read_docs = {d for d in live if d in by_doc}
    # claims ABOUT this parcel, wherever they were read
    about = [c for cl in by_doc.values() for c in cl if c["subject_bbl"] == bbl]

    return dict(bbl=bbl, live=live, read_docs=read_docs, about=about,
                held=live & held, unread=live - read_docs - (live & held),
                fetched_not_read=(live & held) - read_docs)


def report(boro, block, lot, label=""):
    r = inherit(boro, block, lot)
    n = len(r["live"])
    print(f"\n=== {r['bbl']}  lot {lot}  {label}")
    print(f"  {n} documents in its ACRIS index")
    print(f"    {len(r['read_docs']):>3} already READ   (claims exist)")
    print(f"    {len(r['fetched_not_read']):>3} fetched, NOT read")
    print(f"    {len(r['unread']):>3} never touched")
    if r["about"]:
        print(f"  ⭐ {len(r['about'])} claims ALREADY RECORDED about this parcel, "
              f"read while working another lot:")
        for c in sorted(r["about"], key=lambda x: x["effective"] or ""):
            v = (f"{c['value_num']:,.0f} {c['unit']}" if c["value_num"]
                 else (c["value_text"] or "")[:62])
            print(f"     {c['effective']}  {c['predicate']:<19} {v}")
            print(f"         from {c['document_id']}"
                  f"{' ' + c['page'] if c['page'] else ''}  [{c['evidence']}]")
    else:
        print("  no claims recorded about this parcel yet")
    return r


if __name__ == "__main__":
    print("INHERITANCE — what Block 800's lots already know from lot 49's decode")
    print("=" * 72)
    LOTS = [(20, "135 W 24th — airspace seller, and the 2008 ZLDA nobody has read"),
            (21, "133 W 24th co-op"), (22, "131 W 24th — Brick Farms co-op"),
            (23, "127 W 24th — Horne co-op, the through-block linchpin"),
            (50, "113-117 W 24th — the lot carved out in the split"),
            (53, "120 W 25th — Sabetfard"), (55, "124 W 25th"), (56, "126 W 25th")]
    tot_live = tot_read = tot_claims = 0
    for lot, label in LOTS:
        r = report("1", "800", lot, label)
        tot_live += len(r["live"]); tot_read += len(r["read_docs"])
        tot_claims += len(r["about"])
    print("\n" + "=" * 72)
    print(f"  {tot_live} documents across 8 lots · {tot_read} already read "
          f"({100*tot_read/tot_live:.0f}%) · {tot_claims} claims inherited")
    print(f"  {tot_live - tot_read} documents still require a first reading.")
    print("\n  ⚠ INHERITED IS NOT DONE. These lots have a head start whose SHAPE")
    print("    is known — it covers only what they share with lot 49. Every one")
    print("    still needs its own decode for the documents nobody has opened.")
