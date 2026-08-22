"""THE 2012 UBS BATCH. 110 of 110 pages read.

⚠ AND IT NAMES THE GROUND LEASE. The May 1, 1995 lease to LMG Realty is not
  a tenancy detail - it is THE LEASEHOLD ESTATE that makes every "Fee and
  Leasehold Mortgage" in this chain mean what it says.
"""
import pathlib
import re

NEW = '''
 # ---- ⚠ the ground lease, named and dated --------------------------------
 C("c2012-groundlease", "2012101500666007", "p005", "unresolved",
   text="THE 1995 LEASE IS THE GROUND LEASE. Recital I: Borrower owns '(i) "
        "the Land and the Improvements ... (ii) the leasehold estate in the "
        "Land pursuant to that certain Lease dated as of May 1, 1995 between "
        "Borrower (AS SUCCESSOR-IN-INTEREST TO 112 WEST 25 COMPANY), as "
        "landlord, and Borrower (AS SUCCESSOR-IN-INTEREST TO LMG REALTY, "
        "L.L.C.), as tenant, as amended by a First Amendment dated as of June "
        "1, 1997, a Second Amendment dated as of June 1, 2007, and a Third "
        "Amendment dated as of November 30, 2008'",
   eff="1995-05-01", stated="2012-10-05", ans=["TENANCY", "TITLE"],
   note="⚠ THE SAME ENTITY IS BOTH LANDLORD AND TENANT, AND THE RECITAL SAYS "
        "SO IN TERMS. This closes the loop three ways: the 1998 collateral "
        "assignment named the LMG lease (c1995-lease); the 2007 batch bought "
        "LMG's sublease for $2,300,000 (c2007-2p3m-answer) and amended the "
        "lease the same day; and here in 2012 the merger is recited as "
        "settled fact. ⚠ THE THIRD AMENDMENT, 2008-11-30, IS AN EVENT I HAD "
        "NO RECORD OF AT ALL - none of the amendments is recorded"),
 C("c2012-fee-and-leasehold", "2012101500666006", "p004", "unresolved",
   text="the 2012 gap mortgage is titled a 'FEE AND LEASEHOLD MORTGAGE' and "
        "recites the same 1995 lease - so the lender took BOTH estates as "
        "collateral rather than relying on the merger",
   eff="2012-10-05", ans=["TENANCY", "DEBT"],
   note="⚠ A LENDER THAT MORTGAGES BOTH SIDES OF A MERGED LEASE IS INSURING "
        "AGAINST THE MERGER BEING UNDONE. Compare the 2007 CEMA's absolute "
        "bar on subordinating the ground lease and its irrevocable power of "
        "attorney to exercise renewals - three lenders in a row treat this "
        "leasehold as a live risk, not a formality"),
 C("c2012-no-garage", "2012101500666007", "p005", "unresolved",
   text="STEVE AND AL'S GARAGE, INC. appears NOWHERE in 110 pages of the 2012 "
        "batch, and neither does the 2007 sublease assignment",
   eff="2012-10-05", ans=["TENANCY"],
   note="the sublessee named in 1998 is gone from the record by 2012 and no "
        "instrument records its departure. ⚠ A TENANCY CAN LEAVE THE RECORD "
        "WITHOUT LEAVING A DOCUMENT - the only trace of the occupant is in "
        "the collateral assignment that pledged its rent"),

 # ---- ⚠ a $1,000 conflict inside one instrument --------------------------
 C("c2012-tax-conflict", "2012101500666007", "p044", "defect",
   text="⚠ THE SAME TAX FIGURE APPEARS FOUR TIMES IN ONE FILING AND ONE COPY "
        "DISAGREES BY $1,000. Schedule 1 attached to the mortgage (p044, "
        "cursive) reads '$46,001.60'. Schedule A attached to the bundled "
        "section 255 affidavit (p049, block print) reads '$45,001.60'. The "
        "gap mortgage's own typed cover-page total is $45,001.60, and "
        "document ...008 Schedule A (p022) also reads $45,001.60",
   eff="2012-10-31", ans=["DEBT", "IDENTIFY"],
   note="three of four agree; the outlier is handwritten. The agent confirmed "
        "it by pixel-level zoom rather than guessing. NOT REPAIRED - and note "
        "$45,001.60 / $1,607,226.43 = 2.800%, so the typed figure is the "
        "arithmetically correct one. ⚠ THE HANDWRITTEN FIGURES ARE WHERE THIS "
        "CORPUS BREAKS, EVERY TIME: the 2003 and 2014 prior-tax affidavits, "
        "the 2013 and 2014 new-money splits, and now this"),
 C("c2012-nooffset", "2012101500666007", "p004", "unresolved",
   text="recital E: 'The outstanding principal indebtedness evidenced by the "
        "Existing Notes and secured by the Existing Mortgages is $39,000,000 "
        "and Borrower represents and warrants that BORROWER HAS NO OFFSETS, "
        "DEFENSES OR COUNTERCLAIMS under or with respect to any of its "
        "obligations' - speaking as of October 5, 2012",
   eff="2012-10-05", ans=["DEBT", "PRIORITY"],
   note="a no-offset representation, not a no-default one, but dated and "
        "sworn. Together with the 2013 spreader's no-default rep these are "
        "the only two dated borrower representations found in the corpus"),
 C("c2012-consolidation-only", "2012101500666007", "p006", "consolidation",
   num=39_000_000, unit="USD",
   text="'the Existing Mortgages are hereby COMBINED AND CONSOLIDATED so that "
        "together they shall hereafter constitute in law but one mortgage, a "
        "single lien covering the Property ... and securing the principal sum "
        "of up to $39,000,000.00 and ... are hereby amended and restated in "
        "their entirety'. Maximum principal stated twice, words and numerals "
        "agreeing both times",
   eff="2012-10-05", stated="2012-10-31", ans=["DEBT"],
   note="⚠ NOT A SPREADER. Recital H lists 'spread' only among FUTURE "
        "modification possibilities. Second control case against the 2014 "
        "'NINETEEN MILLION ($48,000,000.00)' defect - 2012 and 2013 are both "
        "internally consistent, 2014 is not"),
 C("c2012-lot20-plane", "2012101500666008", "p017", "easement",
   text="the Lot 20 benefit is expressly bounded by a PLANE: 'TOGETHER WITH "
        "the benefits of that certain easement for light and air over Tax Lot "
        "20 (LOWER LIMITING PLANE) set forth in that certain Zoning Lot "
        "Development and Easement Agreement dated as of 2/14/2008 by and "
        "between 351 E 61 Realty LLC -and- 135 West 24th Buyer LLC, recorded "
        "on 2/26/2008 under CRFN 2008000078652'",
   eff="2008-02-14", stated="2012-10-31", subject="1008000020",
   vdatum="lower limiting plane (elevation not stated in this instrument)",
   ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ 'LOWER LIMITING PLANE' MEANS LOT 49 OWNS AIR ABOVE AN ELEVATION "
        "AND SOMEONE ELSE OWNS BELOW IT - the cover page confirms it, listing "
        "Lot 20 as 'Fee above a plane'. ⚠ THE ELEVATION ITSELF IS NOT IN THIS "
        "DOCUMENT. It is in CRFN 2008000078652, and the parties to that 2008 "
        "agreement are NEITHER of this parcel's owners - a right lot 49 "
        "enjoys was created by two strangers four years earlier"),
 C("c2012-lots-listed", "2012101500666008", "p002", "zoning_lot_members",
   text="the cover page lists Block 800 Lot 49 as FEE, Lot 20 as 'Fee above a "
        "plane', and Lots 21, 22, 23, 53, 55 and 56 as 'DEVELOPMENT RIGHTS' "
        "parcels - three different species of interest on one cover page",
   eff="2012-10-31", ans=["ENVELOPE", "PARCEL"],
   note="⚠ AND SEVERAL OF THOSE LOTS' OWN PROPERTY TYPES READ 'APARTMENT "
        "BUILDING'. A decoder that treats every lot on a cover page as "
        "collateral would report this lender as holding liens on seven "
        "apartment buildings. It holds a fee, a fee above a plane, and six "
        "bundles of transferred floor area"),
 C("c2012-exhibit-asymmetry", "2012101500666008", "p016", "defect",
   text="⚠ document ...008's Exhibit A describes ONLY Parcel 1 (Lot 49) and "
        "Parcel 2 (part of Lot 20) by metes and bounds - there is NO legal "
        "description for Lots 21, 22, 23, 53, 55 or 56, although the cover "
        "page of the same instrument lists all of them as subject "
        "development-rights parcels",
   eff="2012-10-31", ans=["PARCEL", "IDENTIFY"],
   note="the companion mortgage ...007 does carry full Exhibit B-1/B-2 "
        "descriptions for those lots. ⚠ TWO INSTRUMENTS RECORDED THE SAME "
        "MINUTE, ONE DESCRIBING SIX LOTS THE OTHER ONLY NAMES"),
 C("c2012-loanagt-controls", "2012101500666008", "p010", "unresolved",
   text="section 5.1 'Conflict of Terms': 'In case of any conflict between "
        "the terms of this Assignment and the terms of the Loan Agreement, "
        "the terms of the Loan Agreement shall prevail' - and the mortgage "
        "itself contains NO parallel clause",
   eff="2012-10-05", ans=["DEBT", "IDENTIFY"],
   note="⚠ THE CONFLICT CLAUSE IS IN THE ASSIGNMENT, NOT THE MORTGAGE. "
        "Reading only the mortgage would show a self-contained instrument. "
        "The rate is deferred too - 'The Loan secured by this Mortgage is a "
        "VARIABLE INTEREST RATE LOAN, as more particularly set forth in the "
        "Loan Agreement' (...006 p011), with no maturity date either"),
 C("c2012-condemnation-split", "2012101500666007", "p009", "easement",
   text="condemnation proceeds are pledged in the MORTGAGE - 'All proceeds "
        "of any of the foregoing, including, without limitation, proceeds of "
        "insurance and condemnation awards' - but are ABSENT from the "
        "assignment of leases and rents' own property clause at ...008 items "
        "(a) through (i)",
   eff="2012-10-05", ans=["INCOME", "ENCUMBRANCE"],
   note="the same split found in 2014 and 2015. ⚠ A CONSISTENT DRAFTING "
        "CONVENTION ACROSS THREE LENDERS: condemnation rides with the "
        "mortgage, rents ride with the assignment. Worth encoding as an "
        "expectation rather than rediscovering each time"),
 C("c2012-prenotarized", "2012101500666007", "p035", "defect",
   text="the notary acknowledgments are dated JULY 5 and JULY 17, 2012 while "
        "the mortgage itself is dated OCTOBER 5, 2012 and recorded October "
        "31 - signature pages executed and notarized three months before the "
        "instrument's own date",
   eff="2012-07-17", stated="2012-10-31", ans=["IDENTIFY"],
   note="⚠ FOURTH DATE ANOMALY, ALL THE SAME SPECIES: the 2010 declaration "
        "acknowledged ten months early, the 2014 Marriott memorandum a month "
        "early, the 2013 spreader eight days early, and now this three months "
        "early. ⚠ AN ACKNOWLEDGMENT DATE IS NOT AN EVENT DATE AND MUST NEVER "
        "SEED A TIMELINE - this is now proven on four separate instruments"),
 C("c2012-devrights-pledged", "2012101500666007", "p006", "easement",
   text="section 1.01 items 2-3 grant 'Development Rights' as collateral: "
        "'The Development Rights Parcels or Excess Development Rights "
        "attributable thereto and, AS THEY ARE ACQUIRED BY BORROWER, the "
        "Excess Development Rights attributable to the Future Development "
        "Rights Parcels' - split across Exhibit B-1 (owned) and Exhibit B-2 "
        "(future)",
   eff="2012-10-05", ans=["ENVELOPE", "DEBT"],
   note="⚠ THE B-1 / B-2 SPLIT IS THE 2012 INVENTION and it is genuinely "
        "informative: B-1 is floor area already acquired, B-2 is floor area "
        "the borrower intends to acquire. The 2013 spreader drops the split "
        "back to a contingent catch-all (c2013-devrights-contingent). The "
        "lender's own exhibits record an ASSEMBLAGE STILL IN PROGRESS"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 2013.*$", t, re.M)
    assert m, "no anchor"
    t = t.replace(m.group(0), NEW + m.group(0), 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 13 claims from the 2012 UBS batch")


main()
