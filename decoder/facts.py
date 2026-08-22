"""One fact, one citation — the durable output of every decode.

LOGIN'S REQUIREMENT, stated 2026-08-06:

    "as easy as document # page # this action occurred for this much"

That sentence is the whole schema. A fact this project keeps is worthless unless
a person can be walked back to the exact page it was read from, so EVERY fact
carries `document_id` + `page` and refuses to exist without them.

THIS SETTLES THE STORE-vs-DELETE QUESTION

    The IMAGE is replaceable — it is always re-fetchable from ACRIS by document
    id and page, which is precisely what the citation encodes. The FACT is not
    replaceable, because re-deriving it costs a fetch, a read and a judgement.

    So: the citation is the durable asset. Storing images is a CACHE — worth
    keeping because it makes parser fixes retroactive and costs ~$400 for the
    whole corpus, but never the thing we rely on. Losing the corpus costs time;
    losing the facts costs the work itself.

WHAT MAKES A FACT ROW USABLE LATER

  * **Addressable** — document_id + page. Anything else is an anecdote.
  * **Typed** — `predicate` is a controlled vocabulary, not prose, so a lifecycle
    can be assembled by filtering rather than by reading.
  * **Dated on TWO axes** — when the thing HAPPENED (document date) versus when
    it became public (recorded date). A rights transfer signed in October and
    recorded in November is one fact with two dates, and confusing them
    reorders a parcel's history.
  * **Self-justifying** — `derivation` records HOW we know. A figure computed
    from tax stamps and a figure read off a page are different epistemic
    objects and must not look alike downstream.
  * **Versioned** — `parser` stamps every row, so "re-decode everything read by
    parser < 9" is a query. Without it, a parser fix cannot be applied backwards.
"""
import json, pathlib, sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import keys

PARSER = 9

# Controlled vocabulary. Prose here would make the lifecycle unassemblable —
# you cannot filter on a sentence.
PREDICATES = {
    # rights & envelope
    "rights_transferred": "development rights moved between zoning lots",
    "zoning_lot_merged": "lots joined into one zoning lot (ZLDA)",
    "easement_granted": "an easement burdens the parcel",
    "declaration_recorded": "a covenant or restriction binds the parcel",
    "restriction_terminated": "a prior burden was released",
    "landmark_designated": "LPC designation applied",
    "variance_granted": "BSA relieved a zoning requirement",
    # BSA, added 2026-08-06 — a variance is only useful as a PAIR of numbers.
    # "the Board allowed 232,985 sf" means nothing until you also hold "the
    # district allowed 102,341 sf"; the relief is the difference and neither
    # half can carry it alone. So the two layers get two predicates and the
    # parameter (floor_area | far | dwelling_units | building_height |
    # base_height | lot_area) rides in `parameter`, never in prose.
    "envelope_permitted": "the as-of-right maximum the decision recites",
    # the Board measures the ZONING lot; PLUTO measures the TAX lot. On
    # 2025-12-BZ they differ by 9,439 sf (51,170.80 vs 60,610) — 18%. Both are
    # correct about different things, and an FAR taken over the wrong one is
    # wrong by that margin, so the stated area is its own fact.
    "lot_area_stated": "the lot area a decision computes its ratios over",
    "envelope_limited": "the maximum the approval itself imposes",
    # most variances cap only the parameter they varied — a side-yard variance
    # says nothing about floor area — so on the majority of resolutions the
    # only numeric statement of the building is what the applicant PROPOSED,
    # which the "conform to the approved plans" condition then binds. That is
    # weaker than an explicit cap and must never be stored as if it were one.
    "envelope_proposed": "the figure applied for, bound only by the approved plans",
    # a condition is not a note. it is a permanent burden that outlives the
    # applicant, must appear on the certificate of occupancy, and is the only
    # place a parking/height/attenuation obligation is ever written down.
    "condition_imposed": "an approval condition binds the parcel permanently",
    # ownership & money
    "conveyed": "title passed",
    "consideration_paid": "a price was paid",
    "mortgaged": "debt secured against the parcel",
    "mortgage_satisfied": "debt discharged",
    "mortgage_assigned": "the lender changed",
    # parties, added 2026-08-06 by the DOS decoder.
    #
    # These do not describe the PARCEL — no DOS document names a block or lot.
    # They describe the ENTITY that signed a document about the parcel, and they
    # are kept as parcel facts because that is the only way they reach a
    # timeline: "the LLC that took these development rights was formed four
    # months earlier and dissolved eighteen months after" is a statement about
    # the deal, assembled from three sources, none of which could make it alone.
    "entity_registered": "an entity came into existence with NY DOS",
    # ⚠ an SPE that wound up is ABSENT from the ACTIVE entity index, so a failed
    # lookup and a closed-out deal look identical. This predicate is what makes
    # them different, and it must never be inferred from absence — it requires
    # the dissolution filing itself.
    "entity_dissolved": "an entity dissolved, surrendered authority, or merged out",
    # the service-of-process address is the rung ABOVE the SPE on the contact
    # ladder — the principal's office or their attorney's.
    "service_address_known": "the address NY DOS sends process to for this entity",
    # lifecycle
    "filed": "an application was filed with an agency",
    "permit_issued": "work was authorised",
    "co_issued": "a certificate of occupancy issued",
    "demolished": "the improvement was removed",
}


class Fact(dict):
    """A single decoded assertion, refusing to exist without its citation."""

    def __init__(self, predicate, *, document_id, page, bbls, happened=None,
                 recorded=None, value=None, unit=None, parties=None,
                 derivation=None, verbatim=None, source="ACRIS", confidence="read",
                 **extra):
        if predicate not in PREDICATES:
            raise ValueError(f"unknown predicate {predicate!r} — add it to "
                             f"PREDICATES deliberately rather than inventing "
                             f"vocabulary at the call site")
        if not document_id or page is None:
            raise ValueError(f"{predicate}: a fact without document_id AND page "
                             f"cannot be walked back to a page, so it is not a "
                             f"fact this project keeps")
        if confidence not in ("read", "derived", "inferred"):
            raise ValueError("confidence must be read | derived | inferred")
        if confidence == "derived" and not derivation:
            raise ValueError(f"{predicate}: a DERIVED value must record HOW it "
                             f"was derived, or it is indistinguishable from one "
                             f"read off the page")
        super().__init__(
            predicate=predicate, document_id=str(document_id), page=page,
            bbls=[str(b) for b in (bbls or [])],
            happened=keys.iso_date(happened), recorded=keys.iso_date(recorded),
            value=value, unit=unit, parties=parties or [],
            derivation=derivation, verbatim=verbatim, source=source,
            confidence=confidence, parser=PARSER, **extra)

    def cite(self):
        """The one-line form Login asked for."""
        d = self["happened"] or self["recorded"] or "    ?     "
        val = ""
        if self["value"] is not None:
            val = (f" for ${self['value']:,.0f}" if self["unit"] == "USD"
                   else f" — {self['value']:,} {self['unit'] or ''}".rstrip())
        who = f"  [{' -> '.join(self['parties'])}]" if self["parties"] else ""
        mark = {"read": "", "derived": " (derived)", "inferred": " (INFERRED)"}[self["confidence"]]
        return (f"{d}  {self['source']} {self['document_id']} p{self['page']}  "
                f"{self['predicate']}{val}{mark}{who}")


def lifecycle(facts):
    """Facts -> a parcel's ordered history. Sorting is on the NORMALISED date."""
    dated = [f for f in facts if f["happened"] or f["recorded"]]
    undated = [f for f in facts if not (f["happened"] or f["recorded"])]
    dated.sort(key=lambda f: f["happened"] or f["recorded"])
    return dated, undated


def by_parcel(facts):
    out = defaultdict(list)
    for f in facts:
        for b in f["bbls"] or ["(unattributed)"]:
            out[b].append(f)
    return dict(out)


def summarise(facts):
    """What is known, and — as importantly — how confidently."""
    from collections import Counter
    c = Counter(f["predicate"] for f in facts)
    conf = Counter(f["confidence"] for f in facts)
    docs = {f["document_id"] for f in facts}
    money = [f for f in facts if f["unit"] == "USD" and f["value"]]
    return {"facts": len(facts), "documents": len(docs),
            "predicates": dict(c.most_common()), "confidence": dict(conf),
            "money_facts": len(money),
            "total_consideration": sum(f["value"] for f in money)}


if __name__ == "__main__":
    # Today's real decode of 2010102601040006, expressed as citable facts.
    F = [
        Fact("zoning_lot_merged", document_id="2010102601040006", page=3,
             bbls=["1008000049", "1008000053", "1008000055", "1008000056"],
             happened="2010-10-14", recorded="2010-11-16",
             parties=["120-22 W 25 STREET LLC", "124-26 W 25 STREET LLC",
                      "112-118 WEST 25TH LLC"],
             verbatim="ZONING LOT DEVELOPMENT AND EASEMENT AGREEMENT ... "
                      "NEW YORK COUNTY BLOCK 800, LOTS 49, 53, 55 and 56",
             crfn="2010000384312"),
        Fact("rights_transferred", document_id="2010102601040006", page=1,
             bbls=["1008000053", "1008000055"],
             happened="2010-10-14", recorded="2010-11-16",
             parties=["120-22 W 25 STREET LLC", "112-118 WEST 25TH LLC"],
             verbatim="Document Type: DEVELOPMENT RIGHTS",
             crfn="2010000384312"),
        Fact("consideration_paid", document_id="2010102601040006", page=1,
             bbls=["1008000053", "1008000055"],
             happened="2010-10-14", recorded="2010-11-16", value=5_000_000,
             unit="USD", confidence="derived",
             derivation="NYC RPTT $131,250.00 / 0.02625 = $5,000,000 AND "
                        "NYS RETT $20,000.00 / 0.004 = $5,000,000 — two "
                        "independent stamps agreeing; index document_amt = 0",
             verbatim="Ref.No. 2010000376481 PREPAID $131,250.00 ; "
                      "Ref.No. 3801156 PREPAID $20,000.00"),
    ]
    print("PARCEL LIFECYCLE — from decoded facts\n")
    dated, undated = lifecycle(F)
    for f in dated:
        print("  " + f.cite())
    print("\n  derivations:")
    for f in dated:
        if f["derivation"]:
            print(f"    {f['document_id']} p{f['page']}: {f['derivation']}")
    print("\n  summary:", json.dumps(summarise(F), indent=1))
