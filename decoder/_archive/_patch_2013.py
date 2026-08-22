"""THE 2013 GOLDMAN BATCH + THE 2014 SUPPORTING DOCUMENTS.

⚠ CORRECTS c-taxcredit-drift, WHICH I RECORDED ONE HOUR AGO. I said the
  figures drift "each higher than the last". THE 2013 SCHEDULE HAS THEM RIGHT.
  It is not drift. It is two wrong affidavits with a correct one between them.
"""
import pathlib
import re

FIX_OLD = '''⚠ THREE INSTRUMENTS STATE THREE DIFFERENT FIGURES FOR THE TAX PAID "
        "ON THE SAME 1990 MORTGAGE, EACH HIGHER THAN THE LAST.'''
FIX_NEW = '''⚠ FOUR INSTRUMENTS STATE THE TAX PAID ON THE SAME 1990 MORTGAGE "
        "AND TWO OF THEM ARE WRONG.'''

NEW = '''
 # ---- ⚠ the correction to my own drift claim -----------------------------
 C("c2013-taxcredit-correct", "2013081200922004", "p020", "tax_paid",
   num=22_500.00, unit="USD",
   text="⚠ THE 2013 SCHEDULE HAS THE PRIOR-TAX FIGURES RIGHT. It states the "
        "1990 mortgage tax as $22,500.00 and the 1998 as $4,528.00 - both "
        "matching the original instruments exactly - alongside "
        "$1,072,716.41 (2007) and $45,001.60 (2012)",
   eff="2013-08-28", ans=["CAPITAL"],
   note="⚠ THIS CORRECTS c-taxcredit-drift, WHICH I RECORDED AN HOUR AGO "
        "SAYING THE FIGURES DRIFT 'EACH HIGHER THAN THE LAST'. THEY DO NOT. "
        "The sequence is $22,500 (1990 instrument) -> $27,500 (2003 "
        "affidavit, WRONG) -> $22,500 (2013 schedule, RIGHT) -> $28,000 "
        "(2014 affidavit, WRONG). It is not a drift and not a trend - it is "
        "two wrong affidavits with a correct one between them. My "
        "recomputed-at-current-rate hypothesis survives for 2003 and 2014 "
        "but explains nothing about why 2013 got it right. I found this by "
        "crossing a THIRD agent against the two that produced the original "
        "claim"),

 # ---- the structural rule: why a termination AND an assignment ----------
 C("c-tlr-assignment-grammar", "2014112601161001", "p003", "unresolved",
   text="WHY EVERY REFINANCING HERE HAS BOTH A TERMINATION AND AN "
        "ASSIGNMENT: a MORTGAGE LIEN can be assigned forward and preserved, "
        "which is what avoids the tax. AN ASSIGNMENT OF LEASES AND RENTS "
        "CANNOT BE - it is a present, absolute transfer to a NAMED assignee, "
        "with no mechanism to slide a different assignee into it. So the "
        "outgoing lender must terminate its AL&R and the incoming lender "
        "must take a fresh one, same day",
   eff="2014-12-02", ev="derived", ans=["CAPITAL", "INCOME"],
   note="⚠ A REUSABLE DECODE RULE, not a fact about this lot. It predicts the "
        "shape of every lender change in the corpus: ASST (tax $0) + small "
        "GAP MTGE (taxed on new money only) + CEMA (exemption 255, tax $0) + "
        "TL&R (kills the old rents assignment) + new AL&R (exemption 255). "
        "Both 2013 and 2014 follow it exactly. In 2014 the OUTGOING lender "
        "is Goldman - the same party that was the INCOMING lender in 2013"),
 C("c2013-275-sworn", "2013081200922001", "p012", "unresolved",
   text="THE BORROWER CERTIFIED THE TAKEOUT STRUCTURE UNDER OATH. The RPL "
        "section 275 statement has exactly one box ticked: '[X] b. Assignment "
        "of the existing mortgage(s) to a new lender in a transaction in "
        "which the assigned mortgage(s) will be consolidated with a new "
        "mortgage securing additional monies advanced by the new lender.' "
        "The alternative box - 'no new monies will be advanced' - is unticked",
   eff="2013-08-07", stated="2013-08-28", ans=["CAPITAL"],
   note="⚠ EVIDENCE, NOT INFERENCE. The tax-efficient structure I derived "
        "from the pattern of stamps is stated on the face of the record and "
        "sworn to by Jeffrey Wai Hung Lam as Manager"),
 C("c-275-posture-flip", "2014112601161003", "p004", "defect",
   text="⚠ THE SAME ECONOMIC MOVE, TWO DIFFERENT COMPLIANCE POSTURES. The "
        "2013 assignment FILED a section 275 statement under oath. The 2014 "
        "assignment DISCLAIMS it: 'THIS ASSIGNMENT is not subject to the "
        "requirements of Section 275 of the Real Property Tax Law because it "
        "is an assignment within the secondary mortgage market'",
   eff="2014-12-02", ans=["CAPITAL", "IDENTIFY"],
   note="fifteen months apart, identical transaction shape. Also note the "
        "2014 text says 'Real Property TAX Law' - section 275 is in the Real "
        "Property Law"),

 # ---- ⚠ the hotel was planned before the construction loan --------------
 C("c2014-marriott-hotel", "2014112601161002", "p003", "unresolved",
   text="⚠ THE HOTEL PLAN IS DATED NOVEMBER 2014, TEN MONTHS BEFORE THE "
        "CONSTRUCTION LOAN. Marriott's subordination defines the Bank's "
        "mortgage to reach 'any mortgage or security deed securing "
        "construction and project financing between Franchisee and the Bank "
        "FOR THE FUTURE CONSTRUCTION OF A HOTEL TO BE LOCATED ON THE "
        "PROPERTY'",
   eff="2014-11-25", stated="2014-12-02", ans=["PERMIT", "CAPITAL"],
   note="⚠ THIS DOCUMENT TELLS YOU WHAT THE MONEY IS FOR - a Marriott-"
        "franchised hotel, with the 2015 Building Loan and Project Loan "
        "already contemplated in the November 2014 subordination. The "
        "underlying Memorandum of Right of First Refusal is dated 2014-07-14, "
        "recorded 2014-08-13, Document ID 2014080700619001. ⚠ An instrument "
        "ACRIS types as 'SAGE / SUNDRY AGREEMENT' is the single best evidence "
        "of development intent in the whole record"),
 C("c2014-marriott-condition", "2014112601161002", "p003", "easement",
   text="Marriott's right of first refusal is subordinate to the mortgage "
        "'if and for so long as: (i) the Mortgage remains validly recorded "
        "and in full force and effect; and (ii) the Bank is not a Competitor "
        "or Affiliate of a Competitor' - and the subordination 'relates only "
        "to Marriott's real estate rights ... is not a subordination of the "
        "Franchise Agreement'",
   eff="2014-11-25", ans=["ENCUMBRANCE", "TITLE"],
   note="⚠ A CONDITIONAL SUBORDINATION THAT CAN SWITCH OFF. If the lien is "
        "ever assigned to a hotel competitor, Marriott's ROFR climbs back "
        "ahead of the mortgage. Every subsequent assignment in this chain - "
        "MetLife 2023, Deutsche Bank 2025 - is silently tested against that "
        "condition"),

 # ---- the chain is 23 years and 11 holders -------------------------------
 C("c-chain-eleven", "2013081200922001", "p005", "cross_reference",
   text="ONE UNBROKEN LIEN, ELEVEN HOLDERS, 1990 TO 2014: Apple Bank For "
        "Savings -> Queens County Savings Bank -> New York Community Bank -> "
        "Anglo Irish Bank Corporation PLC -> Irish Bank Resolution Corp -> "
        "LSREF2 Clover Trust 2011 -> Wells Fargo Bank NA -> LSREF2 Clover "
        "Trust 2011 (back again) -> UBS Real Estate Securities -> Goldman "
        "Sachs Bank USA -> Shanghai Commercial Bank",
   eff="2013-08-07", ans=["CAPITAL", "PARTY"],
   note="⚠ THE ROOT IS REEL 1707 PAGE 1285, THE 1990 APPLE BANK MORTGAGE - "
        "not the 1999 entries, which are 1998 instruments recorded late. Both "
        "the 2013 and the 2014 cover pages carry that 1990 reel/page as their "
        "PRIMARY cross-reference. Continue the chain past this batch and it "
        "reaches MetLife (2023) and Deutsche Bank (2025): THIRTEEN HOLDERS, "
        "THIRTY-FIVE YEARS, ONE LIEN"),
 C("c2013-lsref-roundtrip", "2013081200922001", "p006", "defect",
   text="⚠ LSREF2 CLOVER TRUST 2011 APPEARS TWICE IN THE CHAIN. It assigns to "
        "Wells Fargo on 2011-11-08 (CRFN 2011000425491) and takes it back "
        "from Wells Fargo on 2012-10-05 (CRFN 2012000427965)",
   eff="2012-10-05", ans=["CAPITAL", "PARTY"],
   note="a holder-count that treats parties as unique understates the "
        "assignment count. Compare the 1971 deed round trip - the same shape, "
        "forty years earlier, on title rather than debt"),

 # ---- defects in the supporting documents --------------------------------
 C("c2013-tlr-indexdefect", "2013081200922005", "p001", "defect",
   text="⚠ THE COVER PAGE NAMES THE WRONG PARTY. p001 indexes 'PARTY TWO: "
        "112-229 WEST 28TH LLC'; the instrument itself at p003 names "
        "'112-118 WEST 25TH LLC'",
   eff="2013-08-28", ans=["IDENTIFY"],
   note="⚠ the cover page controls for indexing, so a NAME-KEYED search for "
        "this termination against the correct borrower MISSES IT. Same class "
        "as the 2018 splitter indexed to lot 50 - the operative instrument "
        "hides behind a bad cover page"),
 C("c2014-tlr-drafting", "2014112601161001", "p003", "defect",
   text="the operative sentence terminates 'that certain TERMINATION OF "
        "Assignment of Leases and Rents' - the word 'Termination' sits where "
        "'Assignment' belongs, so as written it terminates the wrong "
        "instrument type",
   eff="2014-12-02", ans=["IDENTIFY", "INCOME"],
   note="intent is recoverable because the identifying CRFN 2013000344224 "
        "that follows is unambiguous. Recorded as a defect, not repaired"),
 C("c2014-gap-thin", "2014112601161004", "p005", "unresolved",
   text="⚠ THE 2014 GAP MORTGAGE ACCELERATES ON DEMAND WITH NO TRIGGER AT "
        "ALL: 'That the whole of the principal sum evidenced by said note "
        "shall become due upon the demand of the Mortgagee.' Seven paragraphs "
        "total, against twenty-two in the 2013 Goldman gap",
   eff="2014-11-25", ans=["CAPITAL"],
   note="⚠ ABSENT from the 2014 gap and PRESENT in the 2013 one: alteration "
        "and demolition consent, the bar on rent more than one month in "
        "advance, the Lien Law section 13 trust-fund covenant, junior-"
        "financing and transfer bars, financial reporting. All of it moved "
        "into the unrecorded Loan Agreement between 2013 and 2014. THE RECORD "
        "GOT THINNER AS THE DEBT GOT BIGGER"),
 C("c2013-devrights-collateral", "2013081200922001", "p003", "easement",
   text="the 2013 assignment reaches the mortgages 'affecting (i) the real "
        "property as described on Exhibit B-1 ... AND (ii) THE DEVELOPMENT "
        "RIGHTS ATTRIBUTABLE TO THE REAL PROPERTY AS DESCRIBED ON EXHIBIT "
        "B-2' - development rights are itemised as SEPARATE collateral, in "
        "their own exhibit",
   eff="2013-08-07", ans=["ENVELOPE", "CAPITAL"],
   note="Exhibit B-1/B-2 at p007-p011 records the light-and-air easement over "
        "Tax Lot 53 under CRFN 2010000384312 and covers Block 800 Lot 23. The "
        "purchased air rights are pledged from 2013 onward"),
 C("c2013-termination-fees", "2013081200922004", "p006", "easement",
   text="section 5(g): 'any termination fees payable under a Lease for the "
        "early termination or surrender thereof shall be paid JOINTLY to the "
        "Assignor and the Lender' - and section 5(m) bars letting any Lease "
        "become subordinate to any lien other than the lender's",
   eff="2013-08-07", ans=["INCOME", "ENCUMBRANCE"],
   note="the 2013 Goldman AL&R bars subordination of leases; the 2014 "
        "Shanghai AL&R does NOT (see c2014-lease-lock). A covenant present in "
        "one generation and absent in the next"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    assert FIX_OLD in t, "drift claim text not found - cannot correct it"
    t = t.replace(FIX_OLD, FIX_NEW, 1)
    m = re.search(r"^ # ---- 2015.*$", t, re.M)
    assert m, "no anchor"
    t = t.replace(m.group(0), NEW + m.group(0), 1)
    p.write_text(t, encoding="utf-8")
    print("corrected c-taxcredit-drift and recorded 13 claims")


main()
