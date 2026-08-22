"""THE 2011-2013 MERGER DOCUMENTS. 122 of 122 pages read.

⚠ AND IT DESTABILISES THE 130-FOOT PLANE I REPORTED AN HOUR AGO.
  2013 calls it an UPPER limiting plane. 2012 and 2019 call it a LOWER one.
  Same elevation, opposite sides, and I asserted which side lot 49 benefits
  from on the strength of one word.
"""
import pathlib
import re

NEW = '''
 # ---- ⚠ the plane, contradicted -----------------------------------------
 C("c2013-plane-upper", "2013052101674002", "p009", "easement",
   subject="1008000020",
   text="⚠ THE SAME 130-FOOT PLANE, CALLED THE OPPOSITE THING. Here the "
        "excess development rights taken from Lot 20 are 'ALL that portion of "
        "the below described parcel LYING BELOW AN UPPER LIMITING PLANE drawn "
        "at an elevation of 130 feet above the datum level used by the "
        "topographical bureau, Borough of Manhattan, which is 2.78 feet above "
        "National Geodetic Survey vertical datum 1929'",
   eff="2013-05-17", vto=130.0,
   vdatum="Topographical Bureau, Borough of Manhattan = NGVD 1929 + 2.78 ft",
   ans=["ENVELOPE", "ENCUMBRANCE"],
   note="⚠ CONTRADICTS HOW I READ c2012-lot20-plane AND c2019-lot20-elevation. "
        "The 2012 mortgage says 'Tax Lot 20 (LOWER limiting plane)'; the 2019 "
        "declaration splits Lot 20 into a Lower Parcel BELOW a LOWER limiting "
        "plane at 130 ft and an Air Space Parcel ABOVE it; this 2013 waiver "
        "describes the transferred rights as lying BELOW an UPPER limiting "
        "plane at the same 130 ft. The ELEVATION and DATUM are consistent "
        "across all three - the SIDE is not. ⚠ I WROTE THAT LOT 49 'OWNS AIR "
        "ABOVE AN ELEVATION'. THAT IS NOT ESTABLISHED. A limiting plane is "
        "named from the perspective of the estate being described, and I "
        "inferred a direction from a single adjective. Recorded as an open "
        "contradiction, not resolved"),

 # ---- ⚠ the ZLDAs are missing, again ------------------------------------
 C("c2013-zldas-missing", "2013052101674007", "p003", "defect",
   text="⚠ THE LOT 21 ZLDA AND THE LOT 22 ZLDA ARE BOTH ABSENT. Each is dated "
        "May 15, 2013 and each is named repeatedly across four of these "
        "documents - the Lot 22 ZLDA 'between Brick Farms Cooperative Ltd. "
        "and 112-118 West 25th LLC', the Lot 21 ZLDA 'between 133 West 24th "
        "Street Corporation and 112-118 West 25th LLC' - and neither is in "
        "the corpus",
   eff="2013-05-15", stated="2013-05-21", ev="derived",
   ans=["ENVELOPE", "IDENTIFY"],
   note="⚠ FIFTH AND SIXTH INSTANCES. Missing so far: the 2010 ZLDA, the 2019 "
        "ZLDA, the Lot 21 and Lot 22 ZLDAs, the $120,000,000 CEMA, and the "
        "2020 mortgage. EVERY ONE IS THE OPERATIVE INSTRUMENT AND EVERY ONE "
        "IS RECITED BY DOCUMENTS THAT DID SURVIVE THE PULL. This is no longer "
        "an observation, it is the finding: THE FETCH SYSTEMATICALLY RETURNS "
        "THE CONSENTS AND LOSES THE DEALS"),
 C("c2013-nosquarefeet", "2013052101674007", "p021", "unresolved",
   text="⚠ ZERO SQUARE-FOOTAGE FIGURES IN 122 PAGES ACROSS TEN DOCUMENTS. No "
        "lot area, no floor area generated, transferred or retained, no "
        "envelope balance, no FAR and no price. Every dimensional figure is a "
        "linear metes-and-bounds course in feet and inches",
   eff="2013-05-21", ans=["ENVELOPE"],
   note="⚠ THE STRUCTURAL LESSON OF THE WHOLE DAY. Declarations MERGE lots "
        "and waivers SUBORDINATE liens; only ZLDAs move floor area. Ten "
        "documents, 122 pages, four lenders and seven lots - and not one "
        "number that tells you how much was built or bought. A decoder can "
        "read every declaration on a block and know the assemblage exists "
        "without learning its size"),
 C("c2013-zlda-2007date", "2013052101674003", "p003", "cross_reference",
   text="⚠ CRFN 2010000384312 IS DATED FEBRUARY 2, 2007 - the recital reads "
        "'ZLDA dated February 2, 2007 ... recorded ... at CRFN 2010000384312' "
        "covering the Lots 53, 55 and 56 unused development rights",
   eff="2007-02-02", stated="2013-05-21", ans=["ENVELOPE", "IDENTIFY"],
   note="⚠ SIGNED IN 2007, RECORDED IN 2010 - a three-and-a-half-year lag on "
        "the instrument that moved the first tranche of development rights "
        "onto this lot. The 2010 batch documents all bear an October 14, 2010 "
        "ZLDA date, so either two ZLDAs exist or the recital is describing an "
        "earlier agreement the 2010 one replaced. Not resolvable from what I "
        "hold - and the document that would resolve it is the one missing"),

 # ---- the merger sequence, dated -----------------------------------------
 C("c2013-merger-sequence", "2013052101674007", "p003", "zoning_lot_members",
   text="THE ASSEMBLAGE, IN ORDER. Lots 53, 55 and 56 merged into lot 49 by "
        "the 2010 Declaration (CRFN 2010000384309). Lot 23 joined by "
        "Declaration CRFN 2013000007932 with ZLDA CRFN 2013000007933, "
        "recorded 2013-01-08. Lot 22 (Brick Farms Cooperative Ltd) joined "
        "2013-05-17. Lot 21 (133 West 24th Street Corporation) joined last, "
        "completing the seven-lot Combined Zoning Lot",
   eff="2013-05-17", stated="2013-05-21", ans=["ENVELOPE", "PARCEL"],
   note="lots 20, 21, 22, 23, 53, 55, 56 assembled onto 49 across three "
        "years, one or two lots at a time, each requiring its own "
        "declaration, its own title certification and its own mortgagee "
        "waiver. Lot 50 does not exist yet - it is still part of lot 49"),
 C("c2013-brickfarms-ratner", "2013052101674003", "p001", "party_role",
   text="BRICK FARMS COOPERATIVE LTD is 'c/o FOREST CITY RATNER COMPANIES', "
        "and 133 West 24th Street Corporation is a separate cooperative; the "
        "2010 sellers 120-22 W 25 Street LLC and 124-26 W 25 Street LLC are "
        "'c/o SABET MANAGEMENT DEVELOPMENT COMPANY'",
   eff="2013-05-17", subject="1008000022",
   parties=["BRICK FARMS COOPERATIVE LTD (c/o Forest City Ratner Companies)",
            "133 WEST 24TH STREET CORPORATION",
            "THE HORNE BUILDING OWNERS CORP",
            "112-118 WEST 25TH LLC (c/o Extell Development Company)"],
   ans=["CONSENT", "TITLE"],
   note="⚠ THE AIR-RIGHTS SELLERS ARE RESIDENTIAL CO-OPS AND ONE IS A FOREST "
        "CITY RATNER ENTITY. A co-op selling its unused development rights is "
        "a board decision, not an owner decision - which is why every one of "
        "these needs a signed declaration from an 'Authorized Board Member "
        "and Shareholder' rather than a deed"),
 C("c2013-wellsfargo-waiver", "2013052101674006", "p003", "unresolved",
   text="WELLS FARGO BANK MINNESOTA, N.A., as Trustee for the Registered "
        "Holders of Credit Suisse First Boston Mortgage Securities Corp. "
        "Commercial Mortgage Pass-Through Certificates, Series 2000-C1, "
        "waived its right to execute the Declaration and subordinated its "
        "July 20, 1999 mortgage on Lot 21 to the Lot 21 ZLDA",
   eff="2013-05-17", subject="1008000021", ans=["CONSENT", "PRIORITY"],
   note="⚠ A CMBS TRUST HAD TO SIGN OFF ON THE AIR-RIGHTS SALE. The consent "
        "chain reaches certificateholders in a 2000-vintage securitisation "
        "for a lien recorded fourteen years earlier. UBS gave the parallel "
        "waiver on lot 49's own mortgage, signed by Henry Chung and Siho Ham"),
 C("c2013-enlargement-preconsent", "2013052101674007", "p005", "easement",
   text="paragraph 4: the Owner 'shall, by executing this Declaration be "
        "deemed AUTOMATICALLY AND WITHOUT ANY FURTHER ACTION ON ITS PART to "
        "have consented to and waived its right to execute an amended or "
        "replacement Declaration' if the Developer later adds parcels - and "
        "'shall, WITHIN TEN (10) BUSINESS DAYS after receiving a request "
        "therefore from Developer ... execute all documents and instruments "
        "required to confirm the incorporation of such Additional Parcels'",
   eff="2013-05-17", subject="1008000021", ans=["CONSENT", "ENVELOPE"],
   note="⚠ A VARIABLE OBLIGATION TRIGGERED BY NOTICE. This is how the "
        "assemblage kept growing without renegotiating with every prior "
        "seller: each co-op pre-consents to the next merger it knows nothing "
        "about. It is also why the 2019 nine-lot restructuring needed so few "
        "new signatures"),
 C("c2013-deed-vs-survey-early", "2013052101674007", "p021", "boundary_origin",
   text="Schedule A already prints both conventions in 2013: '82 feet 10 "
        "inches (deed) (82 feet 8 3/4 inches - survey)'",
   eff="2013-05-21", ans=["PARCEL"],
   note="⚠ CORROBORATES c2019-deed-vs-survey SIX YEARS EARLIER. The "
        "distinction was documented in 2013 and I still carried it as an "
        "unresolved defect through the 1990, 1998, 2003 and 2010 reads. The "
        "answer was sitting in a title certification the whole time"),
 C("c2013-signer-uncertain", "2013052101674003", "p008", "defect",
   text="⚠ TWO SIGNER NAMES I AM NOT ASSERTING. On the Lot 22 declaration the "
        "cursive signature block and the notary block do not clearly agree - "
        "the notary page, which is the more legible, reads 'personally "
        "appeared JONATHAN PRESSMAN'. On the Wells Fargo waiver the signature "
        "block appears to read 'Mindy G. Vit[to]' while the notary block "
        "reads 'Mindy Goldstein'",
   eff="2013-05-17", ans=["CONSENT", "IDENTIFY"],
   note="⚠ RECORDED AS UNCERTAIN ON PURPOSE. Jonathan Pressman definitely "
        "signed the LOT 21 declaration as 'Authorized Board Member and "
        "Shareholder' of 133 West 24th Street Corporation; whether the same "
        "person also signed for Brick Farms on lot 22 is not established. A "
        "name is a reach-ladder rung and a wrong one is worse than a blank"),
 C("c2011-servicing-chain", "2011112200806001", "p001", "cross_reference",
   text="the four 2011 documents are pure servicing transfers on lot 49's own "
        "mortgage and its assignment of rents: Irish Bank Resolution "
        "Corporation Limited to LSREF2 Clover Trust 2011 (CRFN 2011000425485 "
        "and ...488), then LSREF2 to Wells Fargo (CRFN 2011000425491 and "
        "...493), against CRFN 2007000336516 and 2007000336517",
   eff="2011-11-08", stated="2011-12-06", ans=["DEBT"],
   note="⚠ THE MORTGAGE AND THE RENTS ASSIGNMENT MOVE AS A PAIR, each needing "
        "its own instrument. Four documents, 29 pages, and ZERO substantive "
        "content - no floor area, no easement, no terms. ⚠ THE COST OF "
        "READING THEM WAS THE ONLY WAY TO LEARN THEY WERE EMPTY, which is an "
        "argument for doc-type triage before page-level reading"),
'''


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^ # ---- 2014.*$", t, re.M)
    assert m, "no anchor"
    t = t.replace(m.group(0), NEW + m.group(0), 1)
    p.write_text(t, encoding="utf-8")
    print("recorded 12 claims; flagged the plane contradiction")


main()
