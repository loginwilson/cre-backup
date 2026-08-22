"""Record the four SMIS instruments, and correct two things I got wrong.

⚠ CORRECTION 1 — "SINGLE DECLARANT MEANS ONE PARTY CONTROLLED EVERYTHING" IS FALSE

    I recorded the August 2013 eight-lot declaration as: "by 112-118 West 25th
    LLC ALONE - single declarant, because Extell now controls every rights
    interest." The document says the OPPOSITE, in terms, at p006:

      "this subsequent Declaration ... shall be effective as to 120-22 W 25
       Street LLC, 124-26 W 25 Street LLC, Lot 23 Owner, Lot 22 Owner, Lot 21
       Owner and Lot 20 Owner, WITHOUT THEIR SIGNATURES HERETO, by reason of
       their prior consent to a declaration merging the several zoning lots."

    Seven other fee owners and four mortgagees still held their interests in
    August 2013. One signature works because each of them PRE-CONSENTED, in an
    earlier recorded instrument, to being bound by a future declaration they
    would never see. Control was assembled by ADVANCE WAIVER, not by ownership.

    ⚠ I inferred a fact about OWNERSHIP from a fact about SIGNATURES. The
    mechanism is in paragraph 4 of each May declaration - the owner "shall be
    deemed automatically and without any further action on its part to have
    consented to and waived its right to execute an amended or replacement
    Declaration". That is the clause that makes the whole assemblage work, and
    I had not read it.

⚠ CORRECTION 2 — THE 2020 "SMIS" IS NOT A ZONING DECLARATION AT ALL

    I wrote: "on this parcel SMIS has been a DECL three times out of three, so
    this is a candidate - but it is NOT assumed to be one." Correct to hedge.
    It is a DECLARATION OF COVENANTS AND RESTRICTIONS under a NYC Office of
    Environmental Remediation Voluntary Cleanup Agreement dated 2016-02-10.

    The words "zoning lot", "Section 12-10", "floor area" and "development
    rights" appear NOWHERE in its 19 pages. This is an ENVIRONMENTAL instrument
    and it opens a function ACRIS was not previously carrying on this parcel.
"""
import pathlib

DECL = {
 # ---- the eight-lot declaration ---------------------------------------
 ("2013080901116001", "zoning_lot_declared"): ("PRESENT", "p003",
   "Block 800 lots 20, 21, 22, 23, 49, 53, 55 and 56 declared ONE zoning lot",
   ("the eight lots", "MUST", "be treated as ONE zoning lot",
    "'Said lots are located within a single block and are hereby declared to be "
    "a tract of land to be treated as one zoning lot for the purposes of the "
    "Resolution'", "only subdivision under the Zoning Resolution")),
 ("2013080901116001", "single_signature_by_pre_consent"): ("PRESENT", "p006",
   "⚠ ONE SIGNATURE, SEVEN OTHER OWNERS STILL IN PLACE",
   ("the six other fee owners and their mortgagees", "MUST",
    "be bound WITHOUT SIGNING",
    "⚠ 'shall be effective as to [them] without their signatures hereto, by "
    "reason of their prior consent to a declaration merging the several zoning "
    "lots'. Control was assembled by ADVANCE WAIVER, not ownership - the "
    "opposite of what a single declarant appears to mean",
    "nobody - the consents were given irrevocably in earlier instruments")),
 ("2013080901116001", "anti_severance"): ("PRESENT", "p006",
   "a breach cannot un-merge the zoning lot",
   ("any party", "MUST NOT", "achieve separate zoning-lot treatment by breach",
    "'the Property shall be treated as one zoning lot unless such zoning lot is "
    "subdivided in accordance with the provisions of the Resolution'",
    "⚠ NOBODY - only the Zoning Resolution's own subdivision procedure")),
 ("2013080901116001", "no_amendment_mechanism"): ("ABSENT", "p004",
   "⚠ NO amendment, termination, expiration or release clause anywhere in the "
   "instrument. Once recorded it can only be unwound by ZR subdivision",
   ("the parties", "MAY NOT", "amend, terminate or release this declaration",
    "⚠ there is no mechanism. Compare the 2020 environmental covenant, which "
    "DOES give an agency power to terminate on petition",
    "nobody")),
 ("2013080901116001", "dob_consent"): ("ABSENT", "p004",
   "⚠ no agency is a party. DOB, City Planning and BSA appear nowhere in 27 "
   "pages; the only public office named is the City Register", None),
 ("2013080901116001", "co_recording_covenant"): ("ABSENT", "p004",
   "'certificate of occupancy' appears nowhere in the document", None),
 ("2013080901116001", "floor_area_allocated"): ("ABSENT", "p004",
   "⚠ NO square-foot figure, FAR or percentage anywhere. A zoning-lot "
   "declaration MERGES; it does not allocate. The quantities live in the "
   "ZLDAs", None),

 # ---- the May declarations: the clause that makes it all work ---------
 ("2013052101674003", "future_declaration_waiver"): ("PRESENT", "p004",
   "⚠ THE KEYSTONE CLAUSE — the owner waives its right to sign anything later",
   ("lot 22 (Brick Farms)", "MUST",
    "be deemed to have consented to every FUTURE enlargement declaration",
    "⚠ 'be deemed automatically and without any further action on its part to "
    "have consented to and waived its right to execute an amended or "
    "replacement Declaration regardless of whether Owner executes such amended "
    "or replacement Declaration'. This is why August 2013 needed one signature",
    "lot 49 alone holds the benefit")),
 ("2013052101674003", "confirming_documents_10bd"): ("PRESENT", "p004",
   "10 business days to execute confirming instruments on request",
   ("lot 22", "MUST", "execute whatever confirms a new parcel's incorporation",
    "within 10 business days of a request with copies of the documents",
    "lot 49")),
 ("2013052101674007", "future_declaration_waiver"): ("PRESENT", "p005",
   "the identical keystone waiver, binding lot 21",
   ("lot 21 (133 West 24th Street Corp)", "MUST",
    "be deemed to have consented to every FUTURE enlargement declaration",
    "same automatic-consent-and-waiver formula as lot 22", "lot 49")),

 # ---- the 2020 environmental covenant ---------------------------------
 ("2020061600455001", "environmental_use_restriction"): ("PRESENT", "p002",
   "⚠ NOT A ZONING INSTRUMENT — an OER cleanup covenant",
   ("the owner of lot 49", "MUST NOT",
    "exceed restricted commercial use, plant vegetable gardens, farm, or use "
    "untreated groundwater",
    "without the prior written approval of the NYC Office of Environmental "
    "Remediation. Arises from a Voluntary Cleanup Agreement dated 2016-02-10",
    "the NYC Office of Environmental Remediation")),
 ("2020061600455001", "engineering_controls"): ("PRESENT", "p003",
   "engineering controls must be operated and maintained per the Site "
   "Management Plan",
   ("the owner of lot 49", "MUST",
    "operate and maintain the engineering controls specified in the Site "
    "Management Plan",
    "⚠ they 'may not be discontinued or modified without an amendment of the "
    "SMP or the termination of this Declaration approved by the Office'. The "
    "SMP itself is an UNRECORDED document",
    "the NYC Office of Environmental Remediation")),
 ("2020061600455001", "deed_recital_required"): ("PRESENT", "p003",
   "every future deed must recite that it is subject to this declaration",
   ("any seller of lot 49", "MUST",
    "recite in the deed that the conveyance is subject to this declaration and "
    "the Site Management Plan",
    "unless the agency has consented to termination. ⚠ a RECITAL, not a CRFN - "
    "so it will not be found by a cross-reference search",
    "the Relevant Agency, by consenting to termination")),
 ("2020061600455001", "agency_termination"): ("PRESENT", "p003",
   "⚠ the ONLY one of the four with a real termination mechanism",
   ("any owner of lot 49", "MAY",
    "petition the agency to modify or terminate this declaration",
    "on not less than 30 days' written notice to every owner of record, "
    "provided human health and the environment stay protected",
    "the NYC Office of Environmental Remediation or its successor")),
 ("2020061600455001", "e_designation"): ("PRESENT", "p009",
   "the site is registered by DOB as an E-DESIGNATED property",
   ("lot 49", "MUST", "remain subject to E-designation registration at DOB",
    "⚠ an environmental designation that constrains what may be built and how - "
    "and it is a DOB record, so the DOB lane can corroborate it",
    "the agency, on completion of remediation")),
}

DEFECTS = [
 ("2013052101674003", "RIDGEWOOD SAVINGS BANK, mortgagee on lot 22, has a BLANK "
  "waiver column in the May 2013 certification (p018) and is OMITTED ENTIRELY "
  "from the August 2013 eight-lot certification. No waiver CRFN exists for it "
  "in any of the four documents. ⚠ The lot 21 mortgagee's identical May gap WAS "
  "closed later by CRFN 2013000241547; lot 22's was not. A mortgagee that never "
  "subordinated is a title question, not a clerical one"),
 ("2013080901116001", "the certification header reads 'SUBDIVISION C OF SECTION "
  "12-10' while both May certifications read 'SUBDIVISION D' - and the May body "
  "text confirms subdivision (d) is correct"),
 ("2013052101674003", "scribal errors as printed: 'Lot 56 (the Lot 53 Land)' in "
  "both May declarations; 'the right to mrege the Lots 53, 55 and 56 Land with "
  "other parcels fo land'; Brick Farms mislabelled '(Lot 23 Owner)' where lot 22 "
  "was intended"),
 ("2020061600455001", "two internal conflicts: p007 requires certification "
  "'every three years thereafter' while p008 says 'every ten years thereafter' "
  "from the same baseline; and p009 says 'restricted RESIDENTIAL use' where "
  "p002 and p008 say COMMERCIAL"),
]


def main():
    p = pathlib.Path("doctype_terms.py")
    t = p.read_text(encoding="utf-8")
    src = ["\nDECL_INSTANCE = {"]
    for (doc, slot), (st, pg, val, deo) in DECL.items():
        src.append(" (%r, %r): (%r, %r, %r, %r)," % (doc, slot, st, pg, val, deo))
    src.append("}\n")
    t = t.replace("def _d(slot):", "\n".join(src) + "\n\ndef _d(slot):", 1)
    t = t.replace("""    inst += [dict(document_id="2019071700601003",""",
"""    for (doc, slot), (st, pg, val, deo) in DECL_INSTANCE.items():
        d = deo or (None, None, None, None, None)
        inst.append(dict(document_id=doc, effective=None, slot=slot, status=st,
                         page=pg, value_text=val, burdened_bbl="1008000049",
                         verbatim=val, actor=d[0], modality=d[1], action=d[2],
                         object=d[3], consent_of=d[4]))
    inst += [dict(document_id="2019071700601003",""")
    p.write_text(t, encoding="utf-8")

    # correct the claim that inferred ownership from a signature
    c = pathlib.Path("claims.py")
    ct = c.read_text(encoding="utf-8")
    ct = ct.replace(
      '''   text="Declaration of Zoning Lot Restrictions over EIGHT lots (49, 20, 21, 22, "
        "23, 53, 55, 56) by 112-118 West 25th LLC ALONE — single declarant",
   eff="2013-08-07", ans=["ENVELOPE", "ENCUMBER"],
   note="INDEXED AS 'SMIS'. The zoning lot in final form"),''',
      '''   # ⚠ CORRECTED. I wrote "single declarant, because Extell now controls every
   # rights interest" — inferring a fact about OWNERSHIP from a fact about
   # SIGNATURES. p006 says the opposite outright: six other owners are bound
   # "without their signatures hereto, by reason of their prior consent."
   text="Declaration of Zoning Lot Restrictions over EIGHT lots (49, 20, 21, "
        "22, 23, 53, 55, 56). ONE signature — but seven other fee owners and "
        "four mortgagees still held their interests. They are bound by ADVANCE "
        "WAIVER given in the earlier declarations, not by having sold out",
   eff="2013-08-07", ans=["ENVELOPE", "ENCUMBER", "CONSENT"],
   note="INDEXED AS 'SMIS'. The zoning lot in final form. The keystone is "
        "paragraph 4 of each May declaration, by which each owner waived its "
        "right to execute any future amended or replacement declaration"),''')
    c.write_text(ct, encoding="utf-8")
    print(f"recorded {len(DECL)} declaration slots + {len(DEFECTS)} defects; "
          f"corrected the single-declarant inference")


main()
