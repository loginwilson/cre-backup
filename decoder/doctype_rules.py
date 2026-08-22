"""Per-document-type decode rules — WHERE each key fact lives, and its traps.

LOGIN'S REQUIREMENT, 2026-08-06:

    "lot 1 transferred blank sf to lot 2 through a zlda for blank amount
     resulting in $/sf ... knowing how to decode say a development rights
     document in general down to the key takeaways"

So each type gets a RULE SET: the facts worth having, the page region each one
lives in, and the traps that make a naive read wrong. The rules are data, not
prose, so a decoder can follow them and a person can audit them.

WHY RULES BEAT READING
    A 116-page ZLDA contains four numbers that matter and 112 pages of covenant
    boilerplate. Without rules you read everything and still miss the quantity,
    because the quantity is not where the grant is.

════════════════════════════════════════════════════════════════════════════
LEARNED FROM 2010102601040006 (ZLDA, MN Blk 800 Lots 49/53/55/56), 2026-08-06
════════════════════════════════════════════════════════════════════════════

⚠ TRAP 1 — THE $10 RECITAL. The body reads "NOW THEREFORE, in consideration of
  Ten Dollars ($10.00) and other good and valuable consideration". The actual
  price was $5,000,000, provable only from the cover-page tax stamps. Reading
  the recital gives an answer wrong by a factor of 500,000, and it LOOKS like a
  real figure — the worst kind of error. **Never take consideration from the
  recital. Always derive it from the stamps** (see consideration.py).

⚠ TRAP 2 — THE QUANTITY IS NOT IN THE GRANT. The granting clause says "Owner
  hereby conveys to Developer the Subject Development Rights" — no number. The
  term is defined as "the Subject Development Rights as defined herein and as
  shown on **Exhibit D**". The square footage lives in an EXHIBIT, tens of pages
  after the grant. A decoder that stops at the granting clause records a
  transfer with no quantity and does not know it is missing one.

⚠ TRAP 3 — SHARES HIDE IN DEFINITIONS. "Developer's Owner Parcel Bonus
  Development Rights shall mean 59.4% of any Owner Parcel Bonus Development
  Rights." A percentage that materially changes who owns what, sitting in a
  definitions list, not in any operative clause.
"""

COVER = "recording and endorsement cover page (always page 1)"
CAPTION = "title/caption page (usually pages 2-4)"
RECITALS = "WHEREAS clauses and CERTAIN DEFINITIONS (usually pages 4-8)"
GRANT = "the operative granting clause"
EXHIBITS = "exhibits, after the signature pages"

RULES = {
    "DEVR": {
        "also": ["ZONE", "AIRRIGHT"],
        "plain_name": "development rights transfer / zoning lot development agreement",
        "takeaway": "{granter_lots} transferred {sf} sf to {grantee_lots} "
                    "via {instrument} for {amount}, = {psf}/sf",
        "facts": [
            {"fact": "document_type", "where": COVER, "how": "'Document Type:' line"},
            {"fact": "parcels", "where": COVER,
             "how": "PROPERTY DATA block — ⚠ CHECK 'Additional Properties on "
                    "Continuation Page'; page 1 shows only the first two"},
            {"fact": "parties", "where": COVER, "how": "PARTY ONE = granter, PARTY TWO = grantee"},
            {"fact": "dates", "where": COVER,
             "how": "Document Date = signed; Recorded/Filed = public. TWO DATES, "
                    "never conflate"},
            {"fact": "crfn", "where": COVER, "how": "City Register File No."},
            {"fact": "consideration", "where": COVER,
             "how": "derive from RPTT + RETT stamps via consideration.py",
             "trap": "⚠ the recital says $10.00 — NEVER use it"},
            {"fact": "lots_in_zoning_lot", "where": CAPTION,
             "how": "caption names every lot in the combined zoning lot"},
            {"fact": "floor_area_transferred", "where": EXHIBITS,
             "how": "follow the defined term (e.g. 'as shown on Exhibit D') to "
                    "its exhibit",
             "trap": "⚠ NOT in the granting clause — the grant names a defined "
                     "term with no number"},
            {"fact": "shares", "where": RECITALS,
             "how": "percentages in CERTAIN DEFINITIONS (e.g. 59.4%)"},
            {"fact": "easements", "where": GRANT,
             "how": "light-and-air easements, with height and distance limits"},
        ],
        "derived": ["price_per_bsf = consideration / floor_area_transferred"],
    },
    "DEED": {
        "plain_name": "conveyance",
        "takeaway": "{grantor} sold {parcels} to {grantee} for {amount} on {date}",
        "facts": [
            {"fact": "parties", "where": COVER, "how": "PARTY ONE = grantor, PARTY TWO = grantee"},
            {"fact": "consideration", "where": "THE INDEX — no image needed",
             "how": "⭐ TESTED 2026-08-06 on deed 2009122400274001: index "
                    "document_amt = $5,242,000 predicted RPTT $137,602.50 and "
                    "RETT $20,968.00; the cover page showed BOTH TO THE CENT. "
                    "For DEEDs the index price is truthful — the exact opposite "
                    "of DEVR, where document_amt is 0 and the price exists only "
                    "on the image. So a deed's price costs ZERO requests.",
             "trap": "⚠ $0 or $10 means nominal — a family or entity transfer, "
                     "NOT a market sale. Flag it, never price from it. And ⚠ "
                     "every FT_ (pre-2000 microfilm) deed carries amt=0 — 13 of "
                     "19 deeds on the pilot zoning lot. For those the image is "
                     "the only source."},
            {"fact": "grantor_domicile", "where": COVER,
             "how": "an OUT-OF-STATE grantor address is a long-hold signal — "
                    "2009122400274001 sold from Hurst, Texas to an SPE formed "
                    "eight days earlier"},
            {"fact": "parcels", "where": COVER, "how": "PROPERTY DATA + continuation"},
            {"fact": "legal_description", "where": EXHIBITS,
             "how": "Schedule A — metes and bounds; run metes.traverse()"},
        ],
    },
    "MTGE": {
        "plain_name": "mortgage",
        "takeaway": "{borrower} borrowed {amount} from {lender} against {parcels}",
        "facts": [
            {"fact": "parties", "where": COVER,
             "how": "PARTY ONE = borrower/mortgagor, PARTY TWO = lender/mortgagee",
             "trap": "⚠ MERS is a NOMINEE, not the lender — the real lender is "
                     "named in the body"},
            {"fact": "amount", "where": COVER, "how": "Mortgage Amount in FEES AND TAXES"},
            {"fact": "borrower_spe", "where": COVER,
             "how": "the borrowing entity is the join key to the whole "
                    "financing chain"},
        ],
    },
    "AGMT": {
        "also": ["SAGE", "M&CON", "SPRD", "AL&R", "TL&R"],
        "plain_name": "agreement — the largest catch-all in ACRIS (920,875), and "
                      "MAJORITY FINANCIAL",
        "takeaway": "{parties} agreed {what} affecting {parcels}",
        "facts": [
            {"fact": "is_it_financing", "where": COVER,
             "how": "58.4% of AGMT carry a dollar amount (537,677 of 920,875). "
                    "An amount is the CLASSIFIER: with one it is a financing "
                    "instrument, without one it could be a ZLDA, an easement "
                    "agreement, anything. Median $1,000,000; max seen $410,000,000"},
            {"fact": "new_money", "where": COVER,
             "how": "read TAXABLE Mortgage Amount and the Exemption code — NOT "
                    "Mortgage Amount",
             "trap": "⚠⚠ THE BIGGEST MONEY TRAP FOUND SO FAR. On "
                     "2014040900899002: Mortgage Amount $410,000,000, TAXABLE "
                     "$0.00, exemption 255, every tax $0.00. It is a "
                     "consolidation/spreader — the tax was paid on the "
                     "underlying loan, so NO NEW MONEY MOVED. `document_amt` "
                     "reports FACE, never new money."},
            {"fact": "parcels_spanned", "where": COVER,
             "how": "count the legals rows, not the cover page",
             "trap": "⚠⚠ THE SAME AMOUNT APPEARS ON EVERY PARCEL. "
                     "2014040900899002 touches THIRTEEN parcels across five "
                     "blocks, each showing $410,000,000. A naive parcel-level "
                     "sum reports $5,330,000,000 of debt where the true new "
                     "money is $0. NEVER aggregate document_amt across parcels "
                     "without de-duplicating by document_id first."},
            {"fact": "consolidation_target", "where": "references (pwkr-dpni)",
             "how": "CEMAs are filed as AGMT, NOT as M&CON — lot 1008000049 has "
                    "zero M&CON and eleven AGMT, and its assignments resolve "
                    "into those AGMTs. Use chain.root_of() to find what is "
                    "being consolidated."},
        ],
        "derived": ["new_money = taxable_amount (0 means a pure consolidation)"],
    },
    "EASE": {
        "plain_name": "easement",
        "takeaway": "{parcels} burdened by a {kind} easement benefiting {grantee}",
        "facts": [
            {"fact": "burdened_parcel", "where": COVER, "how": "PROPERTY DATA"},
            {"fact": "kind", "where": GRANT, "how": "light and air / access / support / utility"},
            {"fact": "geometry", "where": GRANT,
             "how": "heights above curb, distances from lot lines — these BIND "
                    "the envelope"},
        ],
    },
    "DECL": {
        "plain_name": "declaration / restrictive covenant",
        "takeaway": "{parcels} restricted: {restriction}",
        "facts": [
            {"fact": "restriction", "where": GRANT, "how": "what may not be built or done"},
            {"fact": "beneficiary", "where": RECITALS, "how": "who can enforce — often the City"},
            {"fact": "termination", "where": GRANT,
             "how": "how it ends — look for a matching TERA later in the chain"},
        ],
    },
}


def rules_for(doc_type):
    t = (doc_type or "").strip().upper()
    if t in RULES:
        return RULES[t]
    for k, v in RULES.items():
        if t in (v.get("also") or []):
            return v
    return None


def checklist(doc_type):
    """What must be found before a decode of this type counts as complete.

    An UNANSWERED fact is a finding. Silence about floor area on a rights
    transfer means the exhibit was not read — not that no area moved.
    """
    r = rules_for(doc_type)
    return [f["fact"] for f in r["facts"]] if r else []


def plain(doc_type, **v):
    """The one-line takeaway a person can read without the document."""
    r = rules_for(doc_type)
    if not r:
        return None
    out = r["takeaway"]
    for k, val in v.items():
        out = out.replace("{" + k + "}", str(val))
    import re
    missing = re.findall(r"\{(\w+)\}", out)
    for m in missing:
        out = out.replace("{" + m + "}", f"[{m} NOT FOUND]")
    return out


if __name__ == "__main__":
    import sys
    t = (sys.argv[1] if len(sys.argv) > 1 else "DEVR").upper()
    r = rules_for(t)
    if not r:
        raise SystemExit(f"no rules for {t}; have: {', '.join(RULES)}")
    print(f"{t} — {r['plain_name']}\n")
    for f in r["facts"]:
        print(f"  {f['fact']:<24} {f['where']}")
        print(f"  {'':<24} {f['how']}")
        if f.get("trap"):
            print(f"  {'':<24} {f['trap']}")
        print()
    for d in r.get("derived", []):
        print(f"  derived: {d}")
    print("\n  EXAMPLE (2010102601040006, decoded 2026-08-06):")
    print("   ", plain("DEVR", granter_lots="MN Blk 800 Lots 53 & 55",
                       grantee_lots="Lots 49 & 56", sf="[Exhibit D not yet read]",
                       instrument="a ZLDA", amount="$5,000,000", psf="$?"))
