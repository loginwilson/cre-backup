"""How a parcel's ENVELOPE changed over time — in plain language.

LOGIN'S THESIS, 2026-08-06:

    "if you go through all the documents on a parcel that would affect its
     envelope, you should be able to explain how the envelope adjusted over
     time based on all the inputs ... this is why we have those 15 main fields
     all documents fall into"

That is the product. Not a document list — a NARRATIVE with arithmetic, where
every sentence cites the page it came from.

THE FOUR KINDS OF INPUT THAT MOVE AN ENVELOPE

  1. **The rule changed.** A rezoning, a text amendment, a special district, a
     MIH area. The lot did nothing; what it was allowed to do changed. Source:
     ZR (live feed) + DCP actions.
  2. **The lot changed.** Merger, apportionment, condo declaration. Lot area
     moves, so permitted floor area moves with it. Source: DOF alteration book.
  3. **Rights moved.** DEVR / AIRRIGHT / ZONE — floor area transferred between
     lots of a zoning lot, or across a district boundary by special permit.
  4. **A burden attached or lifted.** EASE / DECL / LDMK / CONS / TERA. The
     arithmetic is unchanged but the buildable envelope is constrained — a
     light-and-air easement can sterilise area the FAR still permits.

⚠ WHY THIS MUST DECLARE ITS OWN IGNORANCE

    An envelope story assembled from PARTIALLY decoded documents is worse than
    none, because it reads as complete. Measured 2026-08-06 on a pilot parcel:
    33 ACRIS documents existed and 3 were decoded — a story from those 3 would
    have described a 2010 rights transfer and said nothing about 1967-2009.

    So every narrative prints, at the top, how much of the record it has read.
    A number that CANNOT be computed is named as unread, never omitted and never
    silently treated as zero.
"""
import sys, pathlib
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import keys

# The 15 classes, grouped by HOW they move an envelope. This grouping is the
# reason the 15 exist as a set — each answers a different question.
MOVERS = {
    "rights": {"DEVR", "AIRRIGHT", "ZONE"},
    "burden": {"EASE", "DECL", "LDMK", "CONS", "LIC", "DEED, RC"},
    "release": {"TERA"},
    "context": {"AGMT", "SAGE", "SMIS", "CERT", "MISC"},   # catch-alls: read to classify
}
ALL15 = set().union(*MOVERS.values())


def kind_of(doc_type):
    for k, s in MOVERS.items():
        if doc_type in s:
            return k
    return None


NARRATE = {
    "rights_transferred": "development rights moved",
    "zoning_lot_merged": "lots joined into one zoning lot, so floor area is "
                         "pooled across them",
    "easement_granted": "an easement now burdens the lot, sterilising area the "
                        "FAR still permits",
    "declaration_recorded": "a covenant restricts what may be built",
    "restriction_terminated": "a prior restriction was released",
    "landmark_designated": "LPC designation constrains alteration",
    "variance_granted": "BSA relieved a zoning requirement",
}


def gather(bbl):
    """Everything on this parcel that could move the envelope, read or not."""
    import bulk
    boro, blk, lot = keys.parts(bbl)
    legs = bulk.socrata("8h5j-fqxa",
                        where=f"borough='{boro}' and block='{blk}' and lot='{lot}'",
                        paginate=True)
    ids = sorted({r["document_id"] for r in legs})
    if not ids:
        return []
    mas = bulk.socrata_in("bnx9-e6tj", "document_id", ids)
    import timeline
    out = []
    for m in mas:
        t = m.get("doc_type")
        if t not in ALL15:
            continue
        out.append({"document_id": m["document_id"], "doc_type": t,
                    "kind": kind_of(t), "date": timeline.doc_date(m),
                    "reel": timeline.reel_of(m), "crfn": m.get("crfn")})
    out.sort(key=lambda d: d["date"] or "")
    return out


def story(bbl, facts=None):
    """The narrative. Prints coverage FIRST so nothing below can mislead."""
    facts = facts or []
    docs = gather(bbl)
    decoded = {f["document_id"] for f in facts}
    read = [d for d in docs if d["document_id"] in decoded]
    unread = [d for d in docs if d["document_id"] not in decoded]

    print(f"HOW THE ENVELOPE MOVED — {bbl}\n")
    if not docs:
        print("  no envelope or encumbrance documents recorded against this lot")
        return
    pct = len(read) / len(docs) * 100
    print(f"  READ {len(read)} of {len(docs)} envelope/encumbrance documents "
          f"({pct:.0f}%)")
    if unread:
        print(f"  ⚠ {len(unread)} UNREAD — everything below is provisional, and "
              f"silence in a period only means nothing has been READ there\n")
    else:
        print()

    by_kind = defaultdict(list)
    for d in docs:
        by_kind[d["kind"]].append(d)
    print("  what is on record:")
    for k in ("rights", "burden", "release", "context"):
        if by_kind[k]:
            ts = ", ".join(sorted({d["doc_type"] for d in by_kind[k]}))
            print(f"    {k:<8} {len(by_kind[k]):>3}  ({ts})")

    print("\n  chronology:")
    for d in docs:
        mark = "read" if d["document_id"] in decoded else "UNREAD"
        rel = [f for f in facts if f["document_id"] == d["document_id"]]
        line = (f"    {d['date'] or '    ?     '}  {d['doc_type']:<9} "
                f"{d['document_id']:<18} [{mark}]")
        print(line + (f"  {d['reel']}" if d["reel"] else ""))
        for f in rel:
            what = NARRATE.get(f["predicate"], f["predicate"])
            amt = (f"  ${f['value']:,.0f}" if f.get("unit") == "USD" and f.get("value")
                   else (f"  {f['value']:,} {f.get('unit') or ''}" if f.get("value") else ""))
            print(f"        -> {what}{amt}   (p{f['page']})")

    print("\n  arithmetic:")
    sf = [f for f in facts if f.get("unit") == "sf" and f.get("value")]
    money = [f for f in facts if f.get("unit") == "USD" and f.get("value")]
    if sf and money:
        tot_sf = sum(f["value"] for f in sf)
        tot_m = sum(f["value"] for f in money)
        print(f"    {tot_sf:,.0f} sf moved for ${tot_m:,.0f} = "
              f"${tot_m/tot_sf:,.2f}/sf")
    elif money and not sf:
        tot_m = sum(f["value"] for f in money)
        print(f"    ${tot_m:,.0f} paid, but FLOOR AREA IS UNREAD — $/sf cannot be")
        print(f"    computed. NOT zero, NOT estimated: unread.")
    else:
        print("    nothing quantified yet")

    if unread:
        print(f"\n  to finish this story, read:")
        for d in unread[:10]:
            print(f"    {d['date'] or '    ?     '}  {d['doc_type']:<9} {d['document_id']}")
        if len(unread) > 10:
            print(f"    ... and {len(unread)-10} more")


if __name__ == "__main__":
    import facts as F
    bbl = sys.argv[1] if len(sys.argv) > 1 else "1008000053"
    demo = [
        F.Fact("zoning_lot_merged", document_id="2010102601040006", page=3,
               bbls=["1008000049", "1008000053", "1008000055", "1008000056"],
               happened="2010-10-14", recorded="2010-11-16"),
        F.Fact("rights_transferred", document_id="2010102601040006", page=1,
               bbls=["1008000053", "1008000055"], happened="2010-10-14"),
        F.Fact("consideration_paid", document_id="2010102601040006", page=1,
               bbls=["1008000053"], happened="2010-10-14", value=5_000_000,
               unit="USD", confidence="derived",
               derivation="NYC RPTT $131,250/0.02625 and NYS RETT $20,000/0.004 "
                          "both = $5,000,000"),
    ]
    story(bbl, demo)
