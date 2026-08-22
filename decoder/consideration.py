"""Recovering the PRICE of a transfer that the index records as zero.

THE FINDING, 2010102601040006 decoded 2026-08-06

    ACRIS master says `document_amt = 0` for that DEVR. The instrument is a
    Zoning Lot Development and Easement Agreement over Manhattan Block 800,
    Lots 49/53/55/56 — a development-rights transfer, which states no
    consideration on its face and therefore indexes as zero.

    But the RECORDING AND ENDORSEMENT COVER PAGE carries the tax stamps, and
    the taxes are computed FROM the consideration. So the price is recoverable
    by arithmetic:

        NYC RPTT  $131,250.00  at 2.625%  ->  $5,000,000
        NYS RETT  $ 20,000.00  at 0.400%  ->  $5,000,000

    TWO INDEPENDENT WITNESSES, agreeing exactly. That is what makes it a
    measurement rather than an inference — either tax alone would be a guess at
    which rate applied; both together pin the rate AND the price.

WHY THIS MATTERS MORE THAN ONE DOCUMENT

    $/BSF on a rights transfer is the number this whole project exists to
    produce, and the index reports it as zero for every DEVR. It is on the
    image, on page one, of every recorded instrument that paid transfer tax.

    This is the concrete answer to "why bother with the documents": not because
    the index is wrong, but because it is SILENT on the thing that matters.
"""

# NYC Real Property Transfer Tax — Administrative Code §11-2102.
# Rates are per CLASS and per THRESHOLD, which is why one stamp alone cannot
# identify the price: $131,250 is 2.625% of $5.0M and also 1.425% of ~$9.2M.
NYC_RPTT = {
    "residential_1_3": [(500_000, 0.01000), (float("inf"), 0.014250)],
    "other": [(500_000, 0.014250), (float("inf"), 0.026250)],
}
# NYS Real Estate Transfer Tax — Tax Law §1402: $2 per $500 = 0.4%.
NYS_RETT = 0.004

# ---------------------------------------------------------------------------
# NYC MORTGAGE RECORDING TAX — components MEASURED from a real cover page,
# 2020081400407001 (commercial, $5,000,000), decoded 2026-08-06.
#
# ⚠ RECORDED BECAUSE I GOT IT WRONG FROM MEMORY. My predicted breakdown put
# City Additional at 1.25% and OMITTED NYCTA entirely, giving 2.30% — while I
# had written "commercial >$500k = 2.80%" one step earlier and never checked my
# components against my own total. The arithmetic self-check was available and
# skipped. These figures are now transcribed from the page, not recalled.
MRT_COMMERCIAL_OVER_500K = {
    "county_basic":   0.00500,   # $25,000.00 on $5,000,000
    "city_additional": 0.01125,  # $56,250.00   <- NOT 1.25%
    "spec_additional": 0.00250,  # $12,500.00
    "tasf":            0.00000,  # $0.00
    "mta":             0.00300,  # $15,000.00
    "nycta":           0.00625,  # $31,250.00   <- the component I forgot exists
    "additional_mrt":  0.00000,  # $0.00
}                                # TOTAL 0.02800 -> $140,000.00 exactly


def mortgage_tax(amount, rates=None, year=None):
    """Expected MRT breakdown. Use to CHECK a cover page, not to replace it.

    ⚠ THE RATE IS NOT A CONSTANT — measured 2026-08-06 and this table is only a
    SNAPSHOT of one era and one bracket.

        2020 & 2023, commercial, >$500,000   ->  2.800%  (this table, verified
                                                  to the cent on both)
        1998, $226,378.12                    ->  2.0000% exactly
                                                  (FT_1710006669171, from the
                                                   handwritten margin "MT
                                                   $4527.56")

    Two variables move it: the ERA (rates were raised over time) and the AMOUNT
    (the $500,000 threshold splits the brackets). Applying the 2.8% table to a
    1998 loan overstates the tax by 40% — and produces a clean-looking number,
    which is the dangerous kind of wrong.

    So: this refuses to answer where it has not been verified, rather than
    returning a figure that would be believed.
    """
    if rates is None:
        if year is not None and int(year) < 2005:
            raise ValueError(
                f"MRT rates for {year} are NOT in this table. Measured: 1998 was "
                f"2.0000% flat on $226,378 while 2020/2023 commercial >$500k is "
                f"2.800%. Read the tax off the page (or the handwritten 'MT' "
                f"margin note) rather than predicting it for a pre-2005 document.")
        if amount < 500_000:
            raise ValueError(
                f"${amount:,.0f} is below the $500,000 bracket threshold and this "
                f"table is the ABOVE-threshold rate. The sub-$500k breakdown has "
                f"not been verified against a document — do not guess it.")
        rates = MRT_COMMERCIAL_OVER_500K
    out = {k: round(amount * v, 2) for k, v in rates.items()}
    out["TOTAL"] = round(sum(out.values()), 2)
    return out


def check_mortgage(index_amt, page_mortgage_amt, page_taxable_amt, page_tax_total):
    """Is the INDEX amount the face amount? And is there a CEMA?

    ⚠ THE CEMA TRAP. The cover page carries BOTH `Mortgage Amount` and `Taxable
    Mortgage Amount`. They were equal on 2020081400407001, but a Consolidation,
    Extension and Modification Agreement pays tax only on NEW money, so taxable
    falls far below face. **Which one `document_amt` follows is UNTESTED** — and
    on a CEMA that is the difference between "borrowed $50M" and "borrowed $5M
    and rolled $45M". Until a CEMA is decoded, say so rather than assume.
    """
    out = {"index_matches_face": index_amt == page_mortgage_amt,
           "cema_suspected": page_taxable_amt < page_mortgage_amt,
           "implied_rate": (page_tax_total / page_taxable_amt
                            if page_taxable_amt else None)}
    if out["cema_suspected"]:
        out["warning"] = (
            f"taxable {page_taxable_amt:,.0f} < face {page_mortgage_amt:,.0f} — "
            f"a CEMA. UNTESTED which figure document_amt reports; do not treat "
            f"the index amount as new money without reading the page.")
    return out


RETT_INCREMENT = 500.0    # NYS charges $2 per $500 OR FRACTION THEREOF


def from_nys(rett_paid):
    """NYS tax -> a WINDOW, not a point.

    ⚠ CORRECTED 2026-08-06. The statute is "$2 for each $500 **or fractional
    part thereof**", so the tax is computed on the consideration ROUNDED UP to
    the next $500. Dividing the stamp by 0.004 therefore recovers the rounded
    figure — an UPPER bound — never the exact price.

    Real case, DEVR 2012122701550003 (Horne Building co-op -> Extell):
        RPTT $121,135.61 / 0.02625  = $4,614,689.90   (exact)
        RETT  $18,460.00 / 0.004    = $4,615,000.00   (rounded up)
        index document_amt          = $4,614,690
    The two differ by $310.10 and the document is perfectly consistent.

    The earlier version returned a single number and reconcile() compared it at
    $1 tolerance — so it declared CONFLICT on a clean document. It only ever
    agreed before because the one case tested, $5,000,000, happens to be an
    exact multiple of $500. **A rule verified on a round number is not verified.**

    Returns (low, high]: consideration is greater than high-500 and at most high.
    """
    if not rett_paid:
        return None
    high = rett_paid / NYS_RETT
    return (high - RETT_INCREMENT, high)


def from_nyc(rptt_paid, prop_class="other"):
    """NYC tax -> candidate considerations, one per bracket.

    Returns a LIST, deliberately. A single number here would be a guess: the
    same payment is consistent with two different prices under two brackets,
    and only a second witness resolves it.
    """
    if not rptt_paid:
        return []
    out = []
    for threshold, rate in NYC_RPTT[prop_class]:
        amt = rptt_paid / rate
        lo = 0 if threshold == 500_000 else 500_000
        if lo < amt <= threshold or (threshold == float("inf") and amt > 500_000):
            out.append({"consideration": amt, "rate": rate})
    return out


def reconcile(rptt_paid=None, rett_paid=None, prop_class="other", tol=1.0):
    """Both stamps -> one consideration, or an honest failure.

    THE TWO WITNESSES ARE DIFFERENT KINDS OF WITNESS, which is the whole subtlety:
        RPTT is computed on the EXACT consideration        -> a point
        RETT is computed on it ROUNDED UP to the next $500 -> a window

    So agreement means the RPTT point falls inside the RETT window, NOT that the
    two numbers match. Comparing them as points threw CONFLICT on clean
    documents — see from_nys().

    FOUR OUTCOMES:
      confirmed   the exact RPTT figure lies within the RETT window
      single      one stamp only — reported WITH its ambiguity
      ambiguous   NYC only, and the bracket is not pinned
      CONFLICT    both present, and no bracket puts them in agreement. A real
                  finding about the document — never averaged, never chosen between.
    """
    nys = from_nys(rett_paid)
    nyc = from_nyc(rptt_paid, prop_class)

    if nys and nyc:
        lo, hi = nys
        for cand in nyc:
            c = cand["consideration"]
            # the exact figure must sit inside (hi-500, hi], with a cent of slack
            # for the rounding of the stamp itself
            if lo - tol < c <= hi + tol:
                return {"verdict": "confirmed", "consideration": round(c, 2),
                        "nyc_rate": cand["rate"], "witnesses": 2,
                        "rett_window": [round(lo, 2), round(hi, 2)],
                        "note": "RPTT (exact) falls inside the RETT window "
                                "(rounded up to the next $500) — the bracket is "
                                "pinned by the agreement, not assumed"}
        return {"verdict": "CONFLICT", "consideration": None, "witnesses": 2,
                "rett_window": [round(lo, 2), round(hi, 2)],
                "nyc_implies": [round(c["consideration"], 2) for c in nyc],
                "note": "no NYC bracket puts the exact figure inside the NYS "
                        "window — report it, do NOT reconcile by choosing one"}
    if nys:
        lo, hi = nys
        return {"verdict": "single", "consideration": round(hi, 2),
                "witnesses": 1, "rett_window": [round(lo, 2), round(hi, 2)],
                "note": f"NYS only. The price is somewhere in (${lo:,.0f}, "
                        f"${hi:,.0f}] — rounded UP to the next $500, so this is "
                        f"an upper bound, not the price"}
    if nyc:
        return {"verdict": "single" if len(nyc) == 1 else "ambiguous",
                "consideration": round(nyc[0]["consideration"], 2) if len(nyc) == 1 else None,
                "candidates": [round(c["consideration"], 2) for c in nyc],
                "witnesses": 1,
                "note": "NYC only; the bracket is not pinned without a second "
                        "witness"}
    return {"verdict": "no_stamps", "consideration": None, "witnesses": 0,
            "note": "no transfer tax paid — an exempt or nominal transfer, which "
                    "is itself a finding"}


if __name__ == "__main__":
    print("2010102601040006 — ZLDA, MN Block 800 Lots 49/53/55/56")
    print("  index document_amt = 0\n")
    r = reconcile(rptt_paid=131_250.00, rett_paid=20_000.00)
    for k, v in r.items():
        print(f"    {k:<15} {v}")
    print("\n  a CONFLICT case (taxes disagreeing):")
    for k, v in reconcile(rptt_paid=131_250.00, rett_paid=8_000.00).items():
        print(f"    {k:<15} {v}")
