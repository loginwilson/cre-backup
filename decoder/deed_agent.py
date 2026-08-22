"""THE DEED AGENT — the first real extractor, and the one that can be checked.

⚠ WHY DEED IS FIRST. It is the only ACRIS type where the extraction PROVES
ITSELF. Price has three independent witnesses computed by two different
authorities at two different rates:

    NYC RPTT  / 2.625%   (commercial, over $500k)
    NYS RETT  / 0.400%
    RP-5217 "Full Sale Price", if annexed

If the extraction is wrong they stop agreeing. Every other type — a mortgage
covenant, an easement's geometry — either extracted or did not, and you only
find out by reading it again.

⚠ THE LADDER. A document enters at L0 and climbs only when a function asks
something the current level cannot answer.

    L0  index only      free       chain · parties · dates · 25% of prices
    L1  cover crop      ~700 tok   the price the index lies about
    L2  grant pages     ~2,100     subject-to · covenants · rights language
    L3  full read       ~9,000     only when L2 leaves a needed slot unanswered

⚠ THE BUDGET IS A FLOOR, NOT A CAP. An agent that hits its budget with slots
still NOT_LOOKED keeps reading and reports that the prior was wrong. A fast
extractor that misses things is worse than a slow one — a single dropped word
reversed a conclusion on this parcel.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ⚠ RESOLUTION IS PER SLOT TYPE, NOT PER DOCUMENT. Measured on a clean
# 2013 laser-printed deed, 2537x3335:
#
#   full page @100%                     ~3,100 tok
#   full page @25%   legible            ~  194 tok   16x
#   full page @20%   legible, tight     ~  124 tok   25x
#   one line  @100%  a strip            ~   41 tok
#
# ⚠ PROSE SURVIVES 20%. IDENTIFIERS DO NOT. At 20% a CRFN reads but a 6
# against an 8 is a coin toss, and a document id you get wrong points at
# the wrong instrument forever. So:
#
#   PASS 1  whole page @20%   comprehend, locate, fill every PROSE slot
#   PASS 2  strip @100%       every NUMBER and IDENTIFIER, exactly
#
# ~206 tokens a page, 15x cheaper AND more accurate where accuracy counts.
#
# ⚠ AND DO NOT TRIM THE MARGINS. The ink bounding box on an ACRIS scan is
# the whole page: film artifacts on one edge, and on this deed the transfer
# tax written by hand in the LEFT MARGIN — a corroborating witness that a
# trim would have cut.
#
# ⚠ 20% IS FOR CLEAN MODERN SCANS. 1971 microfilm with black borders and
# skew will need 50% or 100%. Resolution is a prior the menu learns per
# document type AND per era.
# ⚠ PAGE PRIORS ARE REAL. REGION PRIORS ARE NOT. I conflated them and was
# wrong twice in one hour — guessed the tax block at y 0.30-0.60 (it is
# 0.62-0.97) and guessed a CRFN strip that turned out to be the WITNESSETH
# paragraph.
#
# WHICH PAGE holds a thing is stable: a cover page is a cover page, a grant
# follows it. WHERE ON THE PAGE is not — every drafter puts the recital, the
# rights clause and the covenants wherever they land, and there are as many
# layouts as there are law firms.
#
# ⚠ SO THE REGION COMES FROM LOOKING, NEVER FROM A PRIOR:
#
#   1  open the page at 20%           ~124 tok
#   2  READ IT. see what is there. "the recital is here, the covenants
#      are there, the rights clause runs across the middle"
#   3  crop THOSE regions for proof   free, mechanical, PIL
#   4  re-read any number strip @100% ~41 tok each
#
# The agent is not finding a rectangle it was told about. It is reading a
# page and deciding what mattered — which is the only thing that survives
# document variants.
SCALE_PROSE = 0.20
SCALE_EXACT = 1.00

RPTT_RATE = 0.02625      # NYC, commercial over $500,000
RETT_RATE = 0.00400      # NYS
TOLERANCE = 0.02         # 2% — rounding in the stamps, not a real disagreement

SLOTS = [
 ("stamps",      "L1", "NYC RPTT and NYS RETT amounts from the cover tax block"),
 ("price",       "L1", "⚠ DERIVED from the stamps, never from the grant"),
 ("rp5217",      "L1", "RP-5217 Full Sale Price if annexed — a third witness"),
 ("parties",     "L0", "grantor and grantee, exactly as printed"),
 ("recital",     "L2", "the stated consideration — usually $10, ALWAYS a trap"),
 ("subject_to",  "L2", "'subject to' clause and any schedule of exceptions"),
 ("covenants",   "L2", "grantor's acts · Lien Law 13 · warranty or none"),
 ("prior_deed",  "L2", "the prior-deed recital: date and reel/page or CRFN"),
 ("rights",      "L2", "development rights, air rights, zoning lot language"),
 ("legal",       "L2", "the description, and whether it gives deed vs survey"),
]

TRAPS = [
 "⚠ THE $10 RECITAL IS A 4,270,000x TRAP. One deed here recites Ten Dollars "
 "against $42,700,000 of stamps. PRICE IS NEVER IN THE GRANT.",
 "⚠ BOTH STAMPS $0.00 MEANS COMMONLY-CONTROLLED PARTIES — an allocation, "
 "not a sale. No price exists and SAYING SO IS THE CORRECT ANSWER. Confirm "
 "by checking whether the same person signed both sides.",
 "⚠ ONE STAMP ZERO AND THE OTHER NONZERO leaves a single-witness "
 "derivation. Flag it weaker; never present it as verified.",
 "⚠ A PRIOR-DEED RECITAL CAN CITE THE WRONG INSTRUMENT. One here fuses the "
 "date of one 1971 deed with the reel/page of another that runs the "
 "opposite way.",
 "⚠ A DEED MAY SAY NOTHING ABOUT DEVELOPMENT RIGHTS EVEN ON AN ASSEMBLAGE "
 "PARCEL. Absence is a finding — record it, do not hunt for it forever.",
]


def witnesses(rptt, retp, rp5217=None):
    """Return each witness's implied price and whether they agree."""
    w = {}
    if rptt:
        w["RPTT"] = rptt / RPTT_RATE
    if retp:
        w["RETT"] = retp / RETT_RATE
    if rp5217:
        w["RP5217"] = float(rp5217)
    if not w:
        return w, None, "NO STAMPS — no price derivable"
    vals = list(w.values())
    lo, hi = min(vals), max(vals)
    if len(w) == 1:
        return w, lo, "⚠ SINGLE WITNESS — weaker evidence, flag it"
    if hi == 0:
        return w, 0.0, "BOTH STAMPS ZERO — commonly-controlled, not a sale"
    if (hi - lo) / hi <= TOLERANCE:
        return w, sum(vals) / len(vals), f"✓ {len(w)} WITNESSES AGREE"
    return w, None, (f"⚠ WITNESSES DISAGREE by {100*(hi-lo)/hi:.1f}% — "
                     f"THE EXTRACTION FAILED. Do not record a price.")


def prompt(doc, level, pages):
    want = [s for s in SLOTS if s[1] <= level]
    return f"""You are the DEED specialist. Read document {doc}.
Pages on disk: {pages}

LEVEL {level}. Open only what this level needs:
  L1 = page 1 only (the cover tax block)
  L2 = pages 1-5 (cover, grant, covenants, prior-deed recital)

⚠ THE BUDGET IS A FLOOR, NOT A CAP. If a slot below is still NOT_LOOKED when
you reach the budget, KEEP READING and say the prior was wrong. Missing a
term is far worse than spending pages.

SLOTS:
{chr(10).join(f'  {i+1:>2}. [{lv}] {k:<11} {d}' for i,(k,lv,d) in enumerate(want))}

TRAPS:
{chr(10).join('  ' + t for t in TRAPS)}

Return JSON only:
{{"document_id":"{doc}","pages_opened":[1],
  "slots":[{{"slot":"stamps","status":"PRESENT","page":1,
             "y":[0.28,0.52],"verbatim":"...","value_num":null}}],
  "menu_update":{{"bad_priors":[],"good_pages":[],"new_slots":[]}}}}

⚠ EVERY PRESENT SLOT NEEDS "y":[top,bottom] AS A FRACTION OF PAGE HEIGHT.
That region becomes the proof AND is what lets the page be deleted."""


def check(doc, rptt, retp, rp5217=None, indexed=None):
    w, price, verdict = witnesses(rptt, retp, rp5217)
    print(f"\n  {doc}")
    for k, v in w.items():
        print(f"    {k:<8} implies ${v:>15,.0f}")
    print(f"    {verdict}")
    if price is not None:
        print(f"    -> PRICE ${price:,.0f}")
        if indexed is not None:
            d = abs(price - float(indexed))
            ok = "✓ matches index" if d < 1 else (
                f"⚠ INDEX SAYS ${float(indexed):,.0f} — differs by ${d:,.0f}")
            print(f"    {ok}")
    return price, verdict


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prompt":
        doc = sys.argv[2]
        p = pathlib.Path("pages_out") / doc
        n = len(list(p.glob("*.png"))) if p.is_dir() else 0
        print(prompt(doc, sys.argv[3] if len(sys.argv) > 3 else "L1", n))
    else:
        print("DEED AGENT · slots and ladder\n")
        for k, lv, d in SLOTS:
            print(f"  [{lv}] {k:<11} {d}")
        print(f"\n  {len(TRAPS)} traps · three-witness guard at "
              f"{TOLERANCE*100:.0f}% tolerance")
