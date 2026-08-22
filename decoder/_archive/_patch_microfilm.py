"""THE MICROFILM ERA 1971-2003. 100 of 100 pages read.

⚠ THE HEADLINE: the 2003 section-255 exemption rests on a handwritten figure
$5,000 HIGHER than the tax the 1990 instrument itself records as paid.
"""
import pathlib
import re

NEW = '''
 # ---- 1971: the round trip -----------------------------------------------
 C("c1971-roundtrip", "FT_1330008495633", "p001", "conveyance",
   text="TWO DEEDS, ONE ROUND TRIP. 112 West 25 Realty Corp conveyed to 112 "
        "West 25 Company on 1971-10-04 (Reel 220 p836); the Company conveyed "
        "it straight back to the Corp on 1971-10-09 (Reel 220 p838). Both "
        "recorded 1971-10-27 at 10:55, consecutive document numbers 12697 and "
        "12698, both bearing $00.00 transfer tax",
   eff="1971-10-09", stated="1971-10-27",
   parties=["112 WEST 25 REALTY CORP", "112 WEST 25 COMPANY (a co-partnership: "
            "David Gleicher, Anna Gleicher, David Lippel, Jennie Lippel)"],
   ans=["TITLE"],
   note="on the face of the record title ends that day back in 112 WEST 25 "
        "REALTY CORP - yet the 1998 grantor is 112 WEST 25 COMPANY"),
 C("c1971-greenwich", "FT_1320008495632", "p001", "consolidation",
   num=127_795.81, unit="USD",
   text="both 1971 deeds are taken SUBJECT TO 'a mortgage held by the "
        "Greenwich Savings Bank in the present unpaid principal amount of "
        "$127,795.81' - taken subject to, with no assumption language",
   eff="1971-10-04", ans=["CAPITAL", "TITLE"],
   note="the oldest debt figure in the record for this parcel"),
 C("c1816-partition", "FT_1320008495632", "p001", "boundary_origin",
   text="the metes and bounds derive from 'the partition map filed December, "
        "1816' - the boundary authority for this parcel is 209 years old",
   eff="1816-12-01", stated="1971-10-04", ans=["PARCEL"],
   note="recited identically in both 1971 deeds"),

 # ---- 1990: the root -----------------------------------------------------
 C("c1990-tax-actual", "FT_1980000345898", "p001", "tax_paid",
   num=22_500.00, unit="USD",
   text="the 1990 mortgage tax ACTUALLY PAID was $22,500.00 - witnessed "
        "TWICE: handwritten in the left margin of p001 as 'M.T. $22,500 -' "
        "and machine-stamped on the p026 recording backer as 'MTGETX 297509 "
        "$22,500.00', with 'Includes Special $2,500 -' written in the tax box",
   eff="1990-07-05", ans=["CAPITAL"],
   note="$22,500 / $1,000,000 = 2.25%, of which the Special component is "
        "$2,500 = 0.25%. Two independent witnesses on the same instrument"),
 C("c2003-affidavit-overstates", "2003110900238001", "p019", "defect",
   text="⚠ THE 2003 SECTION-255 EXEMPTION AFFIDAVIT CLAIMS 'Mortgage tAx paid "
        "$27,500.00' AGAINST THE 1990 MORTGAGE - $5,000 MORE THAN THE 1990 "
        "INSTRUMENT ITSELF RECORDS AS PAID ($22,500.00, twice witnessed)",
   eff="2003-11-28", ans=["CAPITAL", "IDENTIFY"],
   note="⚠ the affidavit's own arithmetic ($27,500.00 + $4,527.56) is what "
        "justified recording $969,656.99 of consolidated debt at $0.00 tax. "
        "The agent cropped and enlarged the handwriting to confirm it reads "
        "27,500. This is a live exposure, not a transcription doubt - the "
        "exemption is supported by a figure the underlying record contradicts"),
 C("c1998-tax-decomp", "FT_1710006669171", "p009", "tax_rate",
   num=2.000, unit="percent",
   text="the 1998 mortgage tax decomposes into the full statutory stack on "
        "the endorsement: County (basic) 1132 + City (Addt'l) 2264 + Spec "
        "Addt'l 566 + TASF nil + MTA 566 + NYCTA nil = TOTAL 4528, against "
        "$226,378.12 = 0.500 + 1.000 + 0.250 + 0.250 = 2.000% exactly",
   eff="1999-06-29", ans=["CAPITAL"],
   note="two independent witnesses again: the p001 margin note 'MT / "
        "$4527.56' carries the unrounded cents, the p009 endorsement carries "
        "the rounded total AND the components. 1998 was 2.000%; by 2007 the "
        "same commercial rate is 2.800%"),
 C("c1990-rate-absent", "FT_1980000345898", "p014", "unresolved",
   text="⚠ THE 1990 ROOT MORTGAGE STATES NO INTEREST RATE AND NO MATURITY. "
        "Both are expressly delegated to a Note that was never recorded - "
        "p014 says only 'the Applicable Interest Rate as defined in the Note' "
        "and 'the Maturity Date as defined in the Note'. Prepayment too: 'If "
        "permitted by the Note, the Debt may be prepaid'",
   eff="1990-06-01", ans=["CAPITAL"],
   note="⚠ THE OFF-REGISTER STRUCTURE IS 35 YEARS OLD ON THIS PARCEL. The "
        "same move Anglo Irish makes in 2007, MetLife in 2023 and Deutsche "
        "Bank in 2025 - the operative economics in an unrecorded agreement - "
        "is already here in 1990. What the lien actually inherits forward is "
        "not a rate but a POSITION AND A MAXIMUM"),
 C("c1990-fixed", "FT_1980000345898", "p013", "unresolved",
   text="what the 1990 mortgage DOES fix numerically: default rate 'twenty "
        "four (24%) percent per annum' and a late charge of 'five (5%) "
        "percent' after ten days",
   eff="1990-06-01", ans=["CAPITAL"],
   note="the punitive numbers are recorded; the actual price of the money is "
        "not"),
 C("c1990-recourse", "FT_1980000345898", "p003", "unresolved",
   text="the 1990 mortgage is RECOURSE - no exculpation or non-recourse "
        "clause appears anywhere in paragraphs 1 through 48. It contemplates "
        "a Guarantor (para 20(e) defines the term, para 15 requires Guarantor "
        "balance sheets) but NO GUARANTY IS IN THE RECORDED PACKAGE",
   eff="1990-06-01", ans=["CAPITAL"],
   note="see c2003-nonrecourse - the flip happens thirteen years later"),
 C("c1990-dueonsale", "FT_1980000345898", "p008", "easement",
   text="the 1990 due-on-sale clause is unusually wide: consent needed for "
        "sale, installment sale, master lease, transfer of more than 10% of "
        "corporate stock, change or resignation of a general partner, AND "
        "'the removal or resignation of the managing agent' - consent 'in its "
        "sole discretion', and 'Mortgagee shall not be required to "
        "demonstrate any actual impairment of its security'",
   eff="1990-06-01", ans=["ENCUMBRANCE", "TITLE"],
   note="carve-out at 9(d): partnership interests may pass on death to "
        "immediate family of the deceased general partner. The Edelman "
        "family carve-out survives into the 1998 CEMA and the 2003 "
        "modification"),
 C("c1990-asbestos", "FT_1980000345898", "p018", "easement",
   text="the property is covered by an asbestos report - 'the report prepared "
        "by Enviro-Probe, Inc., dated February 27, 1990' - and para 35 "
        "requires the property be 'kept free of Asbestos' except as that "
        "report discloses. Para 36's environmental indemnity 'shall survive "
        "any termination, satisfaction, assignment, entry of a judgment of "
        "foreclosure or delivery of a deed in lieu of foreclosure'",
   eff="1990-06-01", ans=["ENCUMBRANCE"],
   note="an obligation that outlives the lien itself. Also the only "
        "environmental fact in the entire ACRIS record for this parcel"),

 # ---- the tenancy that closes a twelve-year loop --------------------------
 C("c1995-lease", "FT_1730006667273", "p001", "unresolved",
   text="THE OPERATING TENANCY, recorded nowhere else: the owner 'did, by "
        "Lease Agreement dated May 1, 1995 ... demise and lease to LMG "
        "REALTY, L.L.C., and which LMG REALTY, L.L.C. did, by Sublease "
        "Agreement, sublease to STEVE AND AL'S GARAGE, INC.'",
   eff="1995-05-01", stated="1998-11-24",
   parties=["LMG REALTY, L.L.C. (lessee)",
            "STEVE AND AL'S GARAGE, INC. (sublessee, the actual occupant)"],
   ans=["TENANCY", "INCOME"],
   note="⚠ THIS CLOSES A TWELVE-YEAR LOOP. LMG Realty L.L.C. is the same "
        "party paid $2,300,000 in 2007 for the assignment of its sublease "
        "(see c2007-2p3m-answer). The 2007 buyer was buying OUT the 1995 "
        "leasehold in order to merge the estates and develop. A parking "
        "garage occupied this site - which is why the deed showed no "
        "development-rights language and the property was worth assembling"),
 C("c1998-collat-lease", "FT_1730006667273", "p002", "easement",
   text="the lessor MUST NOT, without written consent, 'Cancel or surrender "
        "said LEASE', 'Modify said LEASE ... so as to decrease the term', or "
        "'Consent to an Assignment ... which will relieve LESSOR and/or "
        "LESSEE of liability' - and 'any of the above acts, if done without "
        "the written consent of ASSIGNEE, shall be null and void'",
   eff="1998-11-24", ans=["ENCUMBRANCE", "TENANCY"],
   note="the lender locked the 1995 LMG lease in place. Any 2007 buyer had to "
        "clear this to collapse the estates"),

 # ---- 1998: the seven-month lag, explained -------------------------------
 C("c1998-lag-explained", "FT_1370006667337", "p012", "defect",
   text="THE SEVEN-MONTH LAG WAS DEFECTIVE PAPERWORK, NOT AN ESCROW. Two "
        "documents carry the reviewer's handwritten rejection notes - 'Need a "
        "complete recital for consol.' and 'Need Back Sheets' on the "
        "collateral assignment p006, and 'Need Back Sheet' with an arrow on "
        "the CEMA p012, plus a struck title number '380-NY-8675' hand-"
        "corrected to 8710",
   eff="1999-06-29", ans=["IDENTIFY"],
   note="the deed was acknowledged 1998-11-23, one day BEFORE the refinance "
        "closed. The whole package then walked in together on 1999-06-29 "
        "within three minutes - 10:15 deed, 10:16 mortgage + cancellation + "
        "assignment + collateral assignment, 10:17 CEMA - all six sharing "
        "cashier receipt 63875. ⚠ THE LAG IS THE PACKAGE'S, NOT THE DEED'S. "
        "An event-date timeline built on recording dates puts this entire "
        "1998 transaction in 1999"),
 C("c1998-recital-defect", "FT_1570006671557", "p001", "defect",
   text="⚠ the 1998 deed recites 'the same as conveyed to the party of the "
        "first part by deed from 112 West 25 Realty Corp. dated October 9, "
        "1971 and recorded October 27, 1971 in Reel 220, Page 836' - but Reel "
        "220 p836 is DATED OCTOBER 4. The deed dated October 9 is at Reel 220 "
        "p838 AND IT RUNS THE OPPOSITE WAY, Company to Realty Corp",
   eff="1999-06-29", ans=["TITLE", "IDENTIFY"],
   note="⚠ the recital fuses the date of one instrument with the reel/page of "
        "the other, and the 1971 RETURN-LEG DEED IS NOT ACCOUNTED FOR "
        "ANYWHERE IN THE 1998 CONVEYANCE. Whether the Oct 9 deed was "
        "intended, delivered, or superseded cannot be determined from these "
        "instruments. This is very likely the ancestor of the 'NOTE: Recites "
        "incorrect legal description' flag that rides forward to today"),
 C("c1998-apple-balance", "FT_1810006667281", "p003", "consideration",
   num=798_621.88, unit="USD",
   text="Queens County Savings Bank paid $798,621.88 for Apple Bank's 1990 "
        "mortgage, and the section 275 affidavit swears 'There is presently "
        "outstanding under the Mortgage the principal sum of $798,621.88' - "
        "consideration equals the outstanding balance exactly",
   eff="1998-09-28", stated="1999-06-29", ans=["CAPITAL"],
   note="the acquire-the-paper move, 1998 edition - executed nine months "
        "before it was recorded. 'without recourse for any reason whatsoever "
        "against the Assignor'"),
 C("c1998-cema-typo", "FT_1370006667337", "p001", "defect",
   text="⚠ the 1998 CEMA's own consolidation figure disagrees with itself on "
        "one line: 'ONE MILLION TWENTY-FIVE THOUSAND AND 00/100 "
        "($1,035,000.00)' - words say 1,025,000, numerals say 1,035,000",
   eff="1998-11-24", ans=["CAPITAL"],
   note="$1,025,000.00 is stated correctly three other times (p001, p003 "
        "twice) and corroborated by the handwritten 'MTge Amt. 1,025,000.00' "
        "on the collateral assignment p001. Under NY construction the WORDS "
        "control. Recorded as a defect, not repaired"),
 C("c1998-interlineations", "FT_1370006667337", "p006", "defect",
   text="TWO INITIALLED HANDWRITTEN INTERLINEATIONS CHANGE THE DEAL and "
        "appear in no typed text: '* AND MANAGE THE LEASES' inserted into the "
        "rent-assignment clause (p006, widening the lender's power) and "
        "'REASONABLE' inserted into 'in its sole ^ determination' on cure "
        "extensions (p010, narrowing it)",
   eff="1998-11-24", ans=["ENCUMBRANCE", "INCOME"],
   note="⚠ no OCR or text-layer extraction finds these. They are only "
        "visible by looking at the page"),
 C("c1990-cancel-narrow", "FT_1260006667226", "p001", "defect",
   text="⚠ the 1999 instrument indexed SAGE DOES NOT SATISFY A MORTGAGE. It "
        "cancels only 'that certain Agreement for the Assignment of Leases "
        "... recorded July 5, 1990 in Reel 1707, page 1311'. The $1,000,000 "
        "mortgage at Reel 1707 p1285 was NOT discharged - it was assigned and "
        "consolidated forward",
   eff="1999-06-29", ans=["CAPITAL", "IDENTIFY"],
   note="⚠ a satisfaction-keyed reader would mark the 1990 debt as closed "
        "here. It is still alive today inside the $123,000,000 lien. Also: "
        "the execution date is hand-corrected 'November' to 'October' with "
        "'SO IN ORIGINAL' stamped, and the notary's stamp reads 'Commission "
        "Expires April 24, 1998' - which PREDATES the October 28, 1998 "
        "acknowledgment"),

 # ---- 2003: the recourse flip --------------------------------------------
 C("c2003-nonrecourse", "2003110900238001", "p013", "easement",
   text="THE DEBT BECAME NON-RECOURSE IN 2003. Para 27: 'the covenants, "
        "obligations and liabilities of the party of the second part ... "
        "shall not be the personal liability of the party of the second part "
        "... and the sole remedies ... shall be to proceed against the "
        "premises, except for environmental issues'",
   eff="2003-10-28", stated="2003-11-28", ans=["CAPITAL"],
   note="⚠ the 1990 and 1998 debt was RECOURSE. This modification - which "
        "'does not create any additional indebtedness' and paid $0.00 tax - "
        "quietly moved the borrower's personal exposure to zero with a single "
        "environmental carve-out. A pure-dollars reading sees nothing happen "
        "in 2003"),
 C("c2003-balance", "2003110900238001", "p003", "consolidation",
   num=969_656.99, unit="USD",
   text="'as of November 1, 2003, is indebted ... in the sum of "
        "($969,656.99) Dollars', consolidated as 'a valid single first "
        "mortgage lien'",
   eff="2003-11-01", ans=["CAPITAL"],
   note="rate reset to 5.50% fixed through 2010-09-30, then Prime + 2.50% "
        "with a 5.50% floor and 16.00% cap; $5,505.61 monthly; maturity "
        "2015-12-01 - unchanged from the 1998 CEMA"),
 C("c2003-proptype", "2003110900238001", "p001", "property_type",
   text="the 2003 cover page declares the property type 'APARTMENT BUILDING' "
        "- while the only recorded tenancy is a parking garage (Steve and "
        "Al's Garage, Inc.) and the 1990 mortgage's dwelling-type box is "
        "circled 'OVER 6'",
   eff="2003-11-28", ans=["IDENTIFY"],
   note="⚠ cover-page property type is a filer's checkbox, not a survey. The "
        "2007 batch declares the same parcel 'COMMERCIAL REAL ESTATE'"),
 C("c1990-legal-conflict", "FT_1980000345898", "p023", "defect",
   text="⚠ TWO DIFFERENT METES FOR THE SAME LOT. The 1990 Exhibit A reads '82 "
        "feet 8-3/4 inches' and '114 feet 10 inches'; the 1998 deed and the "
        "2003 Schedule A read 'about 82 feet 10 inches' and '114 feet 6 "
        "inches more or less'",
   eff="1990-06-01", ans=["PARCEL"],
   note="not resolvable from these documents. A candidate ancestor for the "
        "'incorrect legal description' flag carried forward through six "
        "generations of consolidation"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 2007.*$", t, re.M) or re.search(
        r"^ # ---- 20\d\d.*$", t, re.M)
    assert m, "no anchor"
    anchor = m.group(0)
    t = t.replace(anchor, NEW + anchor, 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 24 microfilm-era claims above:", anchor.strip())


main()
