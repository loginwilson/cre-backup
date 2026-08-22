"""THE 2010 AIR-RIGHTS BATCH + THE MARRIOTT ROFR. 44 pages read.

⚠ THE PATTERN, NOW TWICE: THE OPERATIVE INSTRUMENT IS THE ONE MISSING.
  The 2010 ZLDA (CRFN 2010000384312) is not in the corpus.
  The 2023 CEMA (CRFN 2023000287582) is not in the corpus.
  In both cases everything on disk RECITES the missing document.
"""
import pathlib
import re

NEW = '''
 # ---- ⚠ the ZLDA itself is not here --------------------------------------
 C("c2010-zlda-missing", "2010102601040003", "p004", "defect",
   text="⚠ THE 2010 ZONING LOT DEVELOPMENT AND EASEMENT AGREEMENT IS NOT IN "
        "THIS CORPUS. All four recorded documents name it - 'that certain "
        "Zoning Lot Development and Easement Agreement (the ZLDA), dated as "
        "of the date hereof, made by and among Developer and Owner' - and "
        "none contains it. The batch CRFNs run 2010000384308, 384309, "
        "384310, 384311, all filed 2010-11-16 15:35; the ZLDA is 384312, the "
        "next number in the sequence",
   eff="2010-10-14", stated="2010-11-16", ev="derived",
   ans=["ENVELOPE", "IDENTIFY"],
   note="⚠ SECOND INSTANCE OF THE SAME PATTERN TODAY. The $120,000,000 CEMA "
        "(CRFN 2023000287582) is also absent while everything on disk recites "
        "it. THE DOCUMENTS THAT SURVIVE A BULK PULL ARE THE CONSENTS, "
        "WAIVERS AND CERTIFICATIONS; THE INSTRUMENT THEY ALL POINT AT IS THE "
        "ONE THAT GOES MISSING. Every floor-area figure, every FAR, every "
        "price for development rights and every light/air/view granting "
        "clause for lots 53, 55 and 56 lives in that document. They are "
        "ABSENT from the record I hold, not merely unfound"),
 C("c2010-declaration-defers", "2010102601040003", "p004", "zoning_lot_members",
   text="the recorded Declaration of Zoning Lot Restrictions does only four "
        "things: it identifies Lot 49 as 'Developer Land' and Lots 53, 55 and "
        "56 as 'Owner Land', declares the combined parcel 'one zoning lot' "
        "under Section 12-10(d) of the Zoning Resolution, consents to "
        "enlargement, and annexes metes-and-bounds. It defers ALL easement "
        "substance to the ZLDA",
   eff="2010-10-14", stated="2010-11-16", subject="1008000053",
   ans=["ENVELOPE", "PARCEL"],
   note="⚠ THE DECLARATION IS THE ANNOUNCEMENT; THE ZLDA IS THE DEAL. A "
        "decoder that reads declarations and skips ZLDAs learns which lots "
        "were merged and nothing about what moved between them"),
 C("c2010-banks-bound-unsigned", "2010102601040004", "p003", "unresolved",
   text="TWO LENDERS BOUND THEIR LIENS TO A DOCUMENT NEITHER EVER SIGNED. New "
        "York Community Bank and Anglo Irish Bank each recorded a waiver "
        "making its mortgage 'subject and subordinate to the Zoning Lot "
        "Development and Easement Agreement dated as of October 14, 2010 ... "
        "which is intended to be recorded prior hereto or simultaneously "
        "herewith'",
   eff="2010-10-14", stated="2010-11-16", ans=["CONSENT", "ENCUMBRANCE"],
   note="⚠ CONSENT GIVEN IN ADVANCE, TO TERMS NOT YET RECORDED. The clearest "
        "instance of the rule I got wrong on the 2013 declaration: DO NOT "
        "INFER OWNERSHIP OR AGREEMENT FROM WHO SIGNED. Anglo Irish signed in "
        "Dublin before an Irish notary commissioned for life"),
 C("c2010-devrights-price", "2010110900202001", "p001", "consideration",
   num=5_000_000, unit="USD",
   text="the 2010 transfer from 120-22 W 25 STREET LLC to 112-118 WEST 25TH "
        "LLC carries 'NYC Real Property Transfer Tax: $131,250.00' and 'NYS "
        "Real Estate Transfer Tax: $0.00'. $131,250 / 2.625% = $5,000,000",
   eff="2010-10-14", stated="2010-11-09", ev="derived", ans=["VALUE", "ENVELOPE"],
   note="⚠ BUNDLED, NOT PER-LOT. p002 adds a SECOND grantor, 124-26 W 25 "
        "STREET LLC, to the same property-data block covering Lots 53, 55, 56 "
        "AND 49 together - so this is one tax figure across multiple lots and "
        "two grantor LLCs, with no per-lot breakout. ⚠ AND THE NYS RETT IS "
        "$0.00, so unlike every other priced transfer in this corpus there is "
        "NO SECOND WITNESS to the $5,000,000. Treat it as a single-source "
        "derivation"),
 C("c2009-lot53-price", "2009122400274001", "p001", "consideration",
   num=5_242_000, unit="USD", subject="1008000053",
   text="the December 2009 fee acquisition of Lot 53 by 120-22 W 25 STREET "
        "LLC from 120 WEST 25TH STREET REALTY COMPANY, L.L.C. of Hurst, "
        "Texas: 'NYC Real Property Transfer Tax: $137,602.50' and 'NYS Real "
        "Estate Transfer Tax: $20,968.00'",
   eff="2009-12-17", stated="2009-12-24", ev="derived", ans=["VALUE", "TITLE"],
   note="TWO INDEPENDENT WITNESSES AGREE: $137,602.50 / 2.625% = $5,242,000 "
        "and $20,968.00 / 0.400% = $5,242,000. ⚠ SO THE ADJOINING LOT COST "
        "$5,242,000 IN FEE TEN MONTHS BEFORE ITS DEVELOPMENT RIGHTS MOVED FOR "
        "roughly $5,000,000 BUNDLED. The seller was an out-of-state LLC"),
 C("c2009-deed-truncated", "2009122400274001", "p001", "defect",
   text="⚠ TRUNCATED 1 OF 5. The cover page declares 'Document Page Count: 4' "
        "and 'PAGE 1 OF 5'; the folder holds ONE image. The granting clause, "
        "the full legal description, the habendum and every signature page "
        "are not on disk",
   eff="2009-12-24", ans=["IDENTIFY", "TITLE"],
   note="⚠ FOURTH CONFIRMED TRUNCATION. Everything I know about this "
        "conveyance comes from its tax stamps. That is enough to derive the "
        "price and nothing else"),
 C("c2010-005-truncated", "2010102601040005", "p001", "defect",
   text="⚠ TRUNCATED 8 OF 9. The cover page header reads 'PAGE 1 OF 9'; the "
        "folder holds eight images",
   eff="2010-11-16", ans=["IDENTIFY"],
   note="⚠ FIFTH CONFIRMED TRUNCATION. This is the Anglo Irish subordination "
        "- one page of a lender's consent instrument is simply absent"),
 C("c2010-legal-conflict-again", "2010102601040003", "p008", "defect",
   text="⚠ THE SAME BOUNDARY CONFLICT, TWENTY YEARS ON. Document ...002 p005 "
        "gives the course as 'about 82 feet 10 inches'; document ...003 p008, "
        "Exhibit A 'Developer Land', gives the identical course on the "
        "identical lot as '82 feet 8 3/4 inches'",
   eff="2010-10-14", ans=["PARCEL", "IDENTIFY"],
   note="⚠ INDEPENDENT CORROBORATION of c1990-legal-conflict. The 1990 "
        "mortgage said 82'8-3/4\\" and 114'10\\"; the 1998 deed and 2003 "
        "schedule said 82'10\\" and 114'6\\". BOTH VARIANTS ARE STILL IN "
        "CIRCULATION IN 2010, in two documents recorded the same minute. "
        "This is the live ancestor of the 'NOTE: Recites incorrect legal "
        "description' flag that rides forward into the current lien"),

 # ---- the Marriott ROFR, read in full ------------------------------------
 C("c2014-rofr-terms", "2014080700619001", "p004", "easement",
   text="Marriott's right of first refusal is 'to purchase the real estate ... "
        "upon the terms contained in Section 17.4, Section 17.5 and Section "
        "17.6 of the Agreement' - the Agreement being a FRANCHISE AGREEMENT "
        "dated July 14, 2014 which is not attached, not recorded, and not in "
        "this corpus",
   eff="2014-07-14", stated="2014-08-13", ans=["ENCUMBRANCE", "TITLE"],
   note="⚠ THE TRIGGER MECHANICS - what counts as a sale event - LIVE IN THE "
        "UNATTACHED SECTION 17.4. The recorded memorandum gives notice that a "
        "right exists and withholds every term that would let you price it. "
        "The same off-register structure as the mortgages, applied to an "
        "option instead of a loan"),
 C("c2014-rofr-duration", "2014080700619001", "p004", "easement",
   text="'The Right of First Refusal will terminate upon the termination of "
        "the Agreement; provided that in the event of an early termination "
        "of the Agreement, the Right of First Refusal WILL SURVIVE such early "
        "termination in accordance with the provisions of Section 17.6'",
   eff="2014-07-14", ans=["ENCUMBRANCE"],
   note="⚠ A VARIABLE DURATION, NOT A TERM OF YEARS. It can outlive the "
        "franchise that created it, on terms not in the record. No notice "
        "period for exercise appears anywhere in the eight pages. And no "
        "'successors and assigns' clause was found - though p004 calls the "
        "rights 'real estate rights in the Premises' for which 'damages are "
        "not an adequate remedy', which is how it runs with the land in "
        "substance"),
 C("c2014-rofr-conditional", "2014080700619001", "p004", "easement",
   text="the subordination has THREE conditions, all of which must hold: "
        "Marriott's rights 'will only be subordinate to the exercise of the "
        "rights of Lenders ... only if and for so long as: (i) the Lender is "
        "not a Competitor or Affiliate of a Competitor ... (ii) any such "
        "mortgage ... is and remains validly recorded and in full force and "
        "effect; and (iii) the indebtedness underlying such mortgage complies "
        "with the requirements of Section 5.2 of the Agreement'",
   eff="2014-07-14", ans=["ENCUMBRANCE", "PRIORITY"],
   note="⚠ CONDITION (iii) IS NEW AND I HAD ONLY TWO. The 2014 bank "
        "subordination recited conditions (i) and (ii); the underlying "
        "memorandum adds a THIRD - the debt itself must comply with Section "
        "5.2 of an unrecorded franchise agreement. So whether Marriott's ROFR "
        "sits ahead of or behind a $123,000,000 lien turns partly on a "
        "document nobody outside the deal can read"),
 C("c2014-rofr-counterparts", "2014080700619001", "p005", "defect",
   text="the memorandum is executed IN COUNTERPARTS and neither page is "
        "complete: p005 carries Marriott's signature (Kip W. Vreeland, Chief "
        "Officer, Full Service Franchising) with the franchisee block BLANK; "
        "p006 is the mirror image, Jeffrey Lam signed with the franchisor "
        "block blank",
   eff="2014-07-14", ans=["CONSENT", "IDENTIFY"],
   note="⚠ NEITHER PAGE ALONE PROVES AGREEMENT AND A READER WHO OPENS ONE "
        "SEES AN UNSIGNED FORM. Both notarial certificates are complete. Also "
        "⚠ Jeffrey Lam's acknowledgment is dated JUNE 18, 2014 - a month "
        "BEFORE the memorandum's own stated date of July 14, 2014"),
 C("c2014-rofr-exhibit-garbled", "2014080700619001", "p008", "defect",
   text="⚠ Exhibit 1's metes and bounds are badly corrupted against every "
        "other copy of this description: 'THENCE southerly parallel with the "
        "westerly side of 6th Avenue 18 feet' (elsewhere 114 feet 6 inches), "
        "'THENCE westerly parallel with the northerly side of 42th Street 75 "
        "feet' (there is no 42th Street; it is 24th), and 'THENCE northerly "
        "... 100 feet and 10 inches' (elsewhere 197 feet 6 inches)",
   eff="2014-08-13", ans=["PARCEL", "IDENTIFY"],
   note="⚠ THE ONLY RECORDED DESCRIPTION OF WHAT MARRIOTT'S OPTION COVERS IS "
        "INTERNALLY IMPOSSIBLE. Recorded as found; not repaired"),
 C("c2010-declaration-signdate", "2010102601040003", "p006", "defect",
   text="the Declaration is dated 'this 14th day of October, 2010' but its "
        "acknowledgment is dated 'the 11th day of December, 2009' - a "
        "ten-month gap consistent with a reused signature page",
   eff="2010-10-14", ans=["IDENTIFY"],
   note="⚠ THIRD DATE ANOMALY OF THE SESSION, all the same species: the 2013 "
        "spreader notarized eight days before its own execution date, the "
        "Marriott memorandum acknowledged a month early, and this one ten "
        "months. ⚠ AN ACKNOWLEDGMENT DATE IS NOT AN EVENT DATE and should "
        "never be used as one"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 2011.*$", t, re.M) or re.search(
        r"^ # ---- 201[1-3].*$", t, re.M)
    assert m, "no anchor"
    t = t.replace(m.group(0), NEW + m.group(0), 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 14 claims from the 2010 batch and the Marriott ROFR")


main()
