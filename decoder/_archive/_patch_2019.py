"""THE 2019 SUBDIVISION AND THE 2020 DOCUMENTS. 65 of 65 pages read.

⚠ THE ELEVATION IS 130 FEET. I have carried "lower limiting plane" as a
  geometry with no number since the first air-rights read. Here it is, with
  its datum.

⚠ AND A BROWNFIELD. 2020061600455001 is not a bridge loan - it is an
  environmental restrictive covenant tied to a 2016 Voluntary Cleanup
  Agreement with NYC OER. Nothing in the debt record hinted at it.
"""
import pathlib
import re

NEW = '''
 # ---- ⚠ THE ELEVATION, WITH ITS DATUM ------------------------------------
 C("c2019-lot20-elevation", "2019071700601001", "p007", "easement",
   subject="1008000020",
   text="LOT 20 IS SPLIT AT 130 FEET. 'LOT 20, LOWER PARCEL - All that certain "
        "plot, piece or parcel of land, LYING BELOW a lower limiting plane "
        "drawn at an elevation of 130 FEET above the datum level used by the "
        "Topographical Bureau, Borough of Manhattan, which is 2.78 feet above "
        "National Geodetic Survey vertical datum 1929 ... mean sea level "
        "Sandy Hook New Jersey' - and 'LOT 20, AIR SPACE PARCEL ... LYING "
        "ABOVE' the same plane",
   eff="2019-07-22", vfrom=130.0, vto=None,
   vdatum="Topographical Bureau, Borough of Manhattan = NGVD 1929 + 2.78 ft",
   hext="the Lot 20 footprint, 116 feet 5 inches deep from West 24th Street, "
        "beginning 425 feet westerly",
   ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ THE NUMBER I HAVE BEEN MISSING ALL SESSION. Every prior instrument "
        "said 'lower limiting plane' and none gave the elevation. ⚠ THE AIR "
        "SPACE PARCEL HAS NO STATED CEILING - it is open-ended upward. And "
        "the datum is doubly specified, city bureau AND national geodetic, "
        "which is what makes 130 feet a locatable plane rather than a number. "
        "Recorded identically in 2019071700601002 p016"),

 # ---- ⚠ Marriott waived --------------------------------------------------
 C("c2019-marriott-waived", "2019071700601001", "p003", "unresolved",
   text="MARRIOTT WAIVED AND SUBORDINATED ITS RIGHT OF FIRST REFUSAL: 'THIS "
        "WAIVER AND SUBORDINATION OF ROFR is made as of the 18th day of June "
        "2019, by Marriott International, Inc.' - signed by Kip W. Vreeland, "
        "Senior Vice President, Full Service Franchising",
   eff="2019-06-18", stated="2019-07-22", ans=["ENCUMBRANCE", "CONSENT"],
   note="⚠ THIS PARTLY ANSWERS THE OPEN MARRIOTT QUESTION. The 2014 "
        "subordination was CONDITIONAL on three things and I flagged that no "
        "later paperwork addressed the conditions. This 2019 waiver is a "
        "fresh, specific consent to the zoning-lot restructuring - but it is "
        "scoped to THAT event. It does not cure the conditions for the 2023 "
        "MetLife or 2025 Deutsche Bank assignments, which remain unaddressed"),
 C("c2019-franchise-named", "2019071700601001", "p003", "unresolved",
   text="the franchise is named at last: a RENAISSANCE HOTEL Franchise "
        "Agreement dated July 14, 2014 with Lam Gen 25 LLC as Franchisee, and "
        "Lam Gen 25 is 'a party in interest ... with respect to the combined "
        "zoning lot'",
   eff="2014-07-14", stated="2019-07-22", ans=["TENANCY", "PERMIT"],
   note="the 2014 memorandum named no brand - 'Renaissance' appeared only in "
        "a file-reference footer, and in the 2023 paperwork only as a running "
        "page footer. ⚠ HERE IT IS IN OPERATIVE TEXT for the first time"),
 C("c2019-zlda-date", "2019071700601001", "p003", "cross_reference",
   text="'Franchisee is party to a Zoning Lot and Development Easement "
        "Agreement DATED AS OF MAY 20, 2019 (the ZLDA) with LG CHELSEA LLC "
        "(the Lot 50 Owner)' - while the ZLDA recorded at CRFN 2019000231248 "
        "carries a recording date of 2019-07-22",
   eff="2019-05-20", stated="2019-07-22", ans=["ENVELOPE", "IDENTIFY"],
   note="⚠ execution 2019-05-20, mortgagee waiver 2019-05-20, Marriott waiver "
        "2019-06-18, recording 2019-07-22. FOUR DATES, ONE TRANSACTION. And "
        "the ZLDA ITSELF IS STILL NOT IN THE CORPUS - third instance of the "
        "operative instrument being the missing one, after the 2010 ZLDA and "
        "the 2023 CEMA"),
 C("c2019-ninelots", "2019071700601002", "p003", "zoning_lot_members",
   text="the Combined Zoning Lot is 'designated as Lots 20, 21, 22, 23, 49, "
        "50, 53, 55 and 56 in Block 800' - 120 West 25th (53), 124 West 25th "
        "(55), 126 West 25th (56), 127 West 24th (23), 131 West 24th (22), "
        "133 West 24th (21), 135 West 24th (20), plus lots 49 and 50",
   eff="2019-05-20", stated="2019-07-22", ans=["ENVELOPE", "PARCEL"],
   note="assembled by FIVE declarations recorded over three years: CRFN "
        "2010000384309 (2010-10-14), 2013000007932 (2012-12-19), "
        "2013000241544 and 2013000241548 (both 2013-05-17), and a fifth. ⚠ "
        "NOTE 2010000384309 IS THE DECLARATION, NOT THE ZLDA AT ...312 - the "
        "assemblage is documented by the announcements while the deals stay "
        "off the record"),
 C("c2019-shanghai-waived", "2019071700601002", "p003", "unresolved",
   text="'THIS WAIVER AND SUBORDINATION OF MORTGAGE is made as of the 20th "
        "day of May, 2019, by SHANGHAI COMMERCIAL BANK LTD., NEW YORK BRANCH' "
        "- subordinating BOTH the Lot 49 Mortgage and the Lot 50 Mortgage to "
        "the zoning-lot declaration",
   eff="2019-05-20", stated="2019-07-22", ans=["CONSENT", "PRIORITY"],
   note="the lender consented to the subdivision that split its own "
        "collateral. Signed by Timothy Chan and Chiu Nam Wu - the same two "
        "officers who signed the 2014 Marriott subordination"),

 # ---- ⚠ THE BROWNFIELD, absent from every debt document ------------------
 C("c2020-cleanup", "2020061600455001", "p002", "easement",
   text="⚠ AN ENVIRONMENTAL RESTRICTIVE COVENANT. 'DECLARATION OF COVENANTS "
        "AND RESTRICTIONS' made by LAM GEN 25 LLC, tied to a VOLUNTARY "
        "CLEANUP AGREEMENT DATED FEBRUARY 10, 2016 with the NYC OFFICE OF "
        "ENVIRONMENTAL REMEDIATION. ACRIS types it 'SUNDRY MISCELLANEOUS'",
   eff="2016-02-10", stated="2020-06-16", ans=["ENCUMBRANCE", "PERMIT"],
   note="⚠ NOTHING IN THE ENTIRE DEBT RECORD HINTS AT THIS. Not one mortgage, "
        "assignment or CEMA from 2015 through 2025 mentions contamination, "
        "remediation or OER - and the only prior environmental fact in the "
        "corpus is a 1990 asbestos report. A covenant that runs with the land "
        "and constrains use, recorded under the junk doc-type again, exactly "
        "like the Marriott subordination. ⚠ MY BRIEF CALLED THIS DOCUMENT "
        "'the 2020 bridge loan'. It has no lender, no loan amount and no "
        "assignment of rents anywhere in 19 pages"),
 C("c2020-loan", "2020081400407002", "p003", "mortgage", num=5_000_000,
   unit="USD",
   text="the actual 2020 loan: 'WHEREAS, Assignee is loaning Assignor the "
        "principal sum of $5,000,000 (the Loan)' from SHANGHAI COMMERCIAL "
        "BANK LTD., NEW YORK BRANCH",
   eff="2020-08-05", stated="2020-08-14", ans=["DEBT"],
   note="⚠ the companion MORTGAGE is Document ID 2020081400407001 and IS NOT "
        "IN THE CORPUS. Fourth instance of the operative instrument missing"),
 C("c2020-tax-conflict", "2020081400407002", "p013", "defect",
   text="⚠ THE COVER PAGE CLAIMS AN EXEMPTION AND THE AFFIDAVIT'S OWN MARGIN "
        "SAYS THE TAX WAS PAID. Cover p001: 'Taxable Mortgage Amount: $0.00' "
        "and 'Exemption: 255'. The section 255 affidavit at p013 carries a "
        "handwritten note under the $5,000,000 indebtedness recital: "
        "'Mortgage Tax Paid $140,000.00'",
   eff="2020-08-14", ans=["DEBT", "IDENTIFY"],
   note="$140,000 / $5,000,000 = 2.800% exactly - the correct commercial rate "
        "on the full principal. So the handwriting describes tax paid on the "
        "COMPANION MORTGAGE (which is not in the corpus) while THIS "
        "instrument is the exempt assignment of rents. Most likely a "
        "cross-reference, not a contradiction - but both are on the record "
        "and I am not repairing either. ⚠ HANDWRITING, AGAIN"),
 C("c2020-hybrid-assignment", "2020081400407002", "p006", "easement",
   text="⚠ THE 2020 ASSIGNMENT NEVER SAYS 'ABSOLUTE' OR 'COLLATERAL' - "
        "neither word appears in its sixteen sections. The granting clause "
        "reads absolute ('Assignor intending hereby to assign to Assignee ALL "
        "OF THE LANDLORD'S INTEREST in said Leases') but section 6 is "
        "collateral in structure: rents are 'received and collected by "
        "Assignor AS A TRUST FUND for the sums secured by the Mortgage'",
   eff="2020-08-05", ans=["INCOME", "ENCUMBRANCE"],
   note="⚠ I HAVE BEEN CLASSIFYING THESE BINARILY - absolute versus "
        "collateral - and treating the label as the fact. This one refuses "
        "the label and has to be read structurally. The 2025 Deutsche Bank "
        "assignment is expressly absolute, the 2020 Shanghai one is not: "
        "that difference is real and I would have missed it by keyword"),
 C("c2019-broken-exhibits", "2019071700601002", "p010", "defect",
   text="⚠ TWO EXHIBITS ARE EMPTY PLACEHOLDERS AS RECORDED. Exhibit B (Lot "
        "49, p010) and Exhibit D (Lot 50, p013) each read only 'ALL that "
        "certain plot, piece or parcel of land ... bounded and described as "
        "follows: BEGINNING' followed by blank space, with the footer 'Error! "
        "Unknown document property name.'",
   eff="2019-07-22", ans=["PARCEL", "IDENTIFY"],
   note="a Word autofill failure recorded into the permanent land record. The "
        "substantive boundary text does survive elsewhere in the same "
        "instrument under different headers, so the description is "
        "recoverable - but the LABELLED exhibits for both subdivided lots are "
        "blank"),
 C("c2019-deed-vs-survey", "2019071700601002", "p010", "boundary_origin",
   text="the 2019 metes and bounds reconcile the old conflict explicitly: "
        "'THENCE South 0 degrees 0 minutes 4.9 seconds East, 82.73 feet (82 "
        "FEET 10 INCHES ON DEED)'",
   eff="2019-07-22", ans=["PARCEL"],
   note="⚠ A SURVEYED DISTANCE AND A DEED DISTANCE, PRINTED SIDE BY SIDE. "
        "82.73 surveyed feet = 82 feet 8.76 inches, which is the 1990 "
        "mortgage's '82 feet 8-3/4 inches'. So BOTH figures in the "
        "thirty-five-year conflict are right: 8-3/4 inches is the survey and "
        "10 inches is the deed. ⚠ THIS RESOLVES c1990-legal-conflict and "
        "c2010-legal-conflict-again - not a defect at all, but two "
        "measurement conventions that no instrument bothered to distinguish "
        "until 2019"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 2020.*$", t, re.M) or re.search(
        r"^ # ---- 202[0-3].*$", t, re.M)
    assert m, "no anchor"
    t = t.replace(m.group(0), NEW + m.group(0), 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 13 claims; resolved the 35-year boundary conflict")


main()
