"""Record the 2013 Brick Farms ZLDA body (2013052101674004 pp004-023).

⚠ THREE INSTRUMENTS, ONE DEVELOPER, ONE BLOCK, AND NO TWO MATCH.

    slot                2010 Sabetfard       2012 Horne          2013 Brick Farms
    easement shape      20-ft BAND above     PLANE at 155.24 ft  PLANE at 130 ft
                        23 ft from rear      whole lot           whole lot
                        lot line
    plane movable       no                   ⚠ YES               no
    plan review         10 business days     5 BD + 5-day        ⚠ NONE. Copy
                                             objection + BINDING    "prior to
                                             architect arbitration  submitting",
                                                                    no waiting
                                                                    period, no
                                                                    objection,
                                                                    no arbitration
    alteration bar      four effects         five effects        five effects
    bonus rights        not addressed        80/20, flipping     ⚠ NO SPLIT -
                                             to 50/50 above         developer
                                             $10,000 in fees        takes 100%
    dollar figure       none                 $10,000 threshold   $5,000 CAP on
                                                                 owner's costs
    construction ins.   not read             $5M / $10M          $1M / $2M /
                                             A.M. Best A-X          $10M umbrella,
                                                                    NO rating req
    DOB consent         only in Exhibit G    only in Exhibit G   ⚠ ABSENT from
                        (unexecuted form)    (unexecuted form)      body; only the
                                                                   unexecuted form

    A decoder that read one and assumed the others would be wrong about the
    easement geometry, the review period, the bonus split, and the insurance,
    on every instrument it did not open.

⚠ AND I MADE THE SAME MISTAKE TWICE
    On 2010 I recorded "light and air" and the covenant said "light, air AND
    VIEW". I corrected it. Then I recorded lot 22's easement as "light and air"
    from the Exhibit F description — and it too says light, air and view. The
    same slip, on the same block, three hours apart. VIEW is a separate
    protected interest and dropping it understates the burden every time.
"""
import pathlib

BF = {
 "rights_conveyance": ("PRESENT", "p008",
   "conveys Excess DR + Owner Parcel Bonus DR; owner retains ONLY the Retained "
   "DR utilised by its existing building, plus a mechanical-equipment right",
   ("lot 22 (Brick Farms co-op)", "MUST",
    "convey its Subject Development Rights to lot 49",
    "= its excess rights PLUS all its bonus rights. It keeps only what its "
    "existing building already uses", None)),
 "light_air_view_easement": ("PRESENT", "p007",
   "⚠ FIXED elevation plane at 130 ft above Manhattan Topographical Bureau "
   "datum (2.75 ft above USC&GS mean sea level, Sandy Hook), coincident with "
   "the WHOLE lot 22 boundary. Perpetual. VIEW INCLUDED. NO raise mechanism",
   ("lot 22", "MUST NOT",
    "let anything rise above 130 ft above the Manhattan datum, anywhere on its lot",
    "a perpetual easement of light, air AND VIEW. ⚠ Unlike lot 23's plane, this "
    "one is FIXED - the body contains no mechanism to raise it",
    "lot 49, as benefited owner")),
 "existing_building_carveout": ("PRESENT", "p008",
   "may retain, add and replace rooftop MECHANICALS above the present roof - "
   "but no mechanical may exceed the plane or use the conveyed rights",
   ("lot 22", "MAY",
    "keep, add and replace rooftop mechanical equipment - HVAC, bulkheads",
    "above the present roof height, but NOTHING may exceed the 130 ft plane or "
    "use any of the conveyed development rights", "lot 49")),
 "repair_carveout": ("PRESENT", "p008",
   "repairs are not a prohibited Alteration, but triple-conditioned and the "
   "right EXPIRES at lot 49's first full TCO",
   ("lot 22", "MAY", "repair and maintain its building",
    "provided the work does not change the use, does not change the floor "
    "area, and does not change the envelope or air space the building occupies "
    "today. ⚠ the right EXPIRES at lot 49's first full TCO", "lot 49")),
 "confirming_instrument": ("PRESENT", "p008",
   "20 business days; Exhibit F form or whatever DOB requires; developer "
   "records at its sole expense",
   ("lot 22", "MUST", "sign a recordable confirming easement when lot 49 asks",
    "within 20 business days, on the annexed form or any alternative DOB "
    "requires; lot 49 records it at its own cost", "lot 49")),
 "alteration_restriction": ("PRESENT", "p008",
   "FIVE prohibited effects, and (a) is a TIMING bar with a four-year outside date",
   ("lot 22", "MUST NOT", "build, alter or rebuild if the work would",
    "(a) COMMENCE before lot 49's first full TCO or four years from 2013-05-17, "
    "WHICHEVER IS SOONER  (b) rise above the 130 ft plane  (c) create or worsen "
    "a non-compliance delaying lot 49's permit or CO  (d) use any rights beyond "
    "its Retained DR  (e) change use, or amend its CO, so as to reduce lot 49's "
    "rights. ⚠ lot 49's mirror covenant has only TWO effects - a sharp asymmetry",
    "lot 49")),
 "plan_review_right": ("PRESENT", "p009",
   "⚠ NO WAITING PERIOD AT ALL - the single largest concession the owner won "
   "across the three instruments",
   ("lot 22", "MUST", "give lot 49 a copy of any DOB application and plans",
    "⚠ 'prior to submitting', with NO stated number of days, NO objection "
    "window and NO arbitration - solely so lot 49 can verify compliance. "
    "Compare 2010's ten business days and 2012's five days plus a binding "
    "architect determination. Separately, zoning analyses must be exchanged "
    "within 10 days AFTER filing", "lot 49")),
 "violation_covenant": ("PRESENT", "p009",
   "reciprocal - lot 49 owes the identical covenant",
   ("lot 22", "MUST NOT",
    "create or permit a violation of the Zoning Resolution, building code or "
    "fire code",
    "that would delay a permit or CO for ANY building on the combined zoning "
    "lot, or create or increase a non-conformity. Lot 49 is bound identically",
    "lot 49")),
 "cure_period": ("PRESENT", "p009", "30 days to commence, both directions",
   ("lot 22", "MUST", "begin curing within 30 days of notice",
    "then proceed diligently and continuously. Reciprocal", "lot 49")),
 "self_help_license": ("PRESENT", "p009",
   "entry and cure; interest at CITIBANK PRIME COMPOUNDED MONTHLY; entry under "
   "the easements needs 5 days' notice",
   ("lot 49", "MAY", "enter lot 22 and cure at lot 22's expense",
    "after notice, at reasonable times except an emergency it reasonably "
    "determines, without unreasonable interference, carrying insurance naming "
    "lot 22 and any mortgagee it knows of. Repayment carries Citibank prime "
    "compounded monthly; lot 22 expressly keeps the right to CONTEST both the "
    "violation and the spend", "lot 22, by curing first")),
 "injunctive_relief": ("PRESENT", "p020",
   "specific performance yes; ⚠ NO consequential-damages bar - instead a "
   "NON-RECOURSE cap",
   ("either party", "MAY", "seek injunctive relief and specific performance",
    "⚠ but recovery runs SOLELY to that party's interest in the combined zoning "
    "lot, including rental insurance, condemnation and sales proceeds. No "
    "personal liability for partners, officers, directors or shareholders",
    None)),
 "dob_consent_to_amend": ("ABSENT", "p022",
   "⚠ NOT IN THE BODY. Section XXI names only 'all of the parties hereto'. The "
   "DOB-consent language exists ONLY in the unexecuted Exhibit G form",
   ("both parties", "MAY", "amend or terminate this agreement by themselves",
    "⚠ no agency consent is required by the AGREEMENT. The DOB-consent clause "
    "lives only in the unexecuted Exhibit G form, so it binds nothing until "
    "that form is signed", "lot 22 and lot 49, alone")),
 "runs_with_land": ("PRESENT", "p020",
   "runs with the land; enforceable by a mortgagee-assignee after default; "
   "⚠ future acquirers bound to FUTURE modifications they never signed",
   ("everyone acquiring any interest, now or later", "MUST",
    "take subject to this agreement AND to future modifications of it",
    "⚠ 'without having executed such future modifications, to the same extent "
    "that it would have been had it been a signatory'", "all parties in interest")),
 "unit_cap": ("ABSENT", "p004",
   "no dwelling-unit limit anywhere in the body", None),
 "co_recording_covenant": ("ABSENT", "p013",
   "no CRFN-on-CO requirement. Nearest analogue: lot 22 must amend its CO to "
   "note the combined zoning lot, at lot 49's cost - or accept a DOB file "
   "notation if it has no CO", None),
 "bonus_rights_split": ("ABSENT", "p007",
   "⚠ NO SPLIT. All bonus rights are folded into the conveyance; lot 49 takes "
   "100%. Compare lot 23, which kept 80% and could reach 50/50", None),
 "anti_merger_covenant": ("PRESENT", "p010",
   "may not merge with any parcel outside the combined zoning lot",
   ("lot 22", "MUST NOT",
    "merge its zoning lot with any parcel not already in the combined zoning lot",
    "without lot 49's prior written consent", "lot 49")),
 "non_opposition_covenant": ("PRESENT", "p014",
   "⚠ TIME-STAGGERED, NOT RECIPROCAL",
   ("lot 22", "MUST NOT",
    "voluntarily appear in opposition to lot 49 at any public body",
    "community board, CPC, DCP, DOB, City Council, BSA, HPD, LPC or any city, "
    "state or federal agency - immediately and indefinitely. ⚠ lot 49's mirror "
    "obligation does not begin until the sooner of its first full TCO or four "
    "years", "lot 49")),
 "downzoning_allocation": ("PRESENT", "p011",
   "three scenarios: one building, all buildings, some buildings",
   ("both parcels", "MUST", "share post-downzoning rebuild rights pro rata",
    "one casualty - rebuild limited to that parcel's own allocation and may not "
    "reduce the others'. All buildings - pro rata per Exhibit D. Some - pro "
    "rata among the affected only, after backing out surviving buildings",
    None)),
 "upzoning_allocation": ("PRESENT", "p012",
   "⚠ EACH KEEPS ITS OWN UPSIDE - SUBJECT TO A DEVELOPER CALL OPTION AT THE "
   "ORIGINAL PRICE",
   ("lot 49", "MAY",
    "BUY lot 22's upzoning upside at the same price per square foot it paid in 2013",
    "⚠ $135.19/sf, exercisable within 90 days of final 197-c/197-d approval, "
    "so long as it acts before its first full TCO. Lot 22's 'retained upside' "
    "is retrospectively priced at the 2013 number", "lot 49, by not exercising")),
 "subdivision_right": ("PRESENT", "p016",
   "⚠ ONE-WAY. Lot 49 may subdivide without consent; lot 22 may not subdivide "
   "at all",
   ("lot 49", "MAY", "subdivide the combined zoning lot without lot 22's consent",
    "and without further payment, provided it first gives lot 22 the "
    "application and a NY-licensed architect's opinion that the subdivision "
    "will not diminish lot 22's rights. ⚠ LOT 22 HAS NO SUBDIVISION RIGHT AT "
    "ALL. This is why the 2019 split needed nobody's consent", None)),
 "estoppel_certificates": ("PRESENT", "p018",
   "twice a year maximum, 20 business days' notice, no liability except fraud",
   ("either party", "MUST", "furnish a status certificate on request",
    "not more than twice a year, on 20 business days' notice, at the "
    "requester's cost. ⚠ no liability even for negligent or inadvertent "
    "non-disclosure - only fraud", None)),
 "preconstruction_survey": ("PRESENT", "p018",
   "entry onto the land AND into the building",
   ("lot 22", "MUST", "let lot 49 survey its building before construction",
    "entry onto the land and INTO the building, scheduled in consultation, "
    "normal business hours, contractor insured", "lot 49")),
 "construction_insurance": ("PRESENT", "p019",
   "⚠ $1,000,000 per occurrence / $2,000,000 aggregate / $10,000,000 umbrella "
   "- and NO carrier-rating requirement",
   ("lot 49", "MUST", "carry construction liability insurance",
    "$1M per occurrence, $2M aggregate, $10M umbrella, occurrence basis, "
    "naming lot 22 AND all its mortgagees as additional insureds, "
    "non-cancelable without notice. ⚠ NO A.M. Best rating required - compare "
    "the Horne instrument's A-X requirement", "lot 22")),
 "effect_of_breach": ("PRESENT", "p020",
   "a breach does NOT un-merge the zoning lot",
   ("the zoning lot merger", "MUST", "survive any breach of this agreement",
    "the combined zoning lot stays one zoning lot unless and until formally "
    "subdivided - the envelope is protected from a contract dispute", None)),
 "architect_arbitration": ("ABSENT", "p016",
   "⚠ no arbitration of any kind. The only architect is a one-way opinion "
   "letter lot 49 must buy before subdividing", None),
 "residential_use_trigger": ("ABSENT", "p004",
   "no payment triggered by residential use on lot 49 - unlike the Horne "
   "instrument's Section 3(d) Rights", None),
}


def main():
    p = pathlib.Path("doctype_terms.py")
    t = p.read_text(encoding="utf-8")

    src = ["\nBF_INSTANCE = {"]
    for slot, (st, pg, val, deo) in BF.items():
        src.append(" %r: (%r, %r, %r)," % (slot, st, pg, val))
    src.append("}\n\nBF_DEONTIC = {")
    for slot, (st, pg, val, deo) in BF.items():
        if deo:
            src.append(" %r: %r," % (slot, deo))
    src.append("}\n")
    t = t.replace("def _d(slot):", "\n".join(src) + "\n\ndef _d(slot):", 1)

    t = t.replace("""    inst += [dict(document_id="2019071700601003",""",
"""    def _bf(s):
        d = BF_DEONTIC.get(s)
        if not d:
            return dict(actor=None, modality=None, action=None, object=None,
                        consent_of=None)
        return dict(actor=d[0], modality=d[1], action=d[2], object=d[3],
                    consent_of=d[4])

    inst += [dict(document_id="2013052101674004", effective="2013-05-17",
                  slot=s, status=v[0], page=v[1], value_text=v[2],
                  burdened_bbl="1008000022", verbatim=v[2], **_bf(s))
             for s, v in BF_INSTANCE.items()]
    inst += [dict(document_id="2019071700601003",""")
    p.write_text(t, encoding="utf-8")

    # ⚠ the repeated slip: "light and air" where the document says "light, air
    # and view". Second time today, same block.
    c = pathlib.Path("claims.py")
    ct = c.read_text(encoding="utf-8")
    ct = ct.replace(
      '''   text="light and air over ALL of lot 22 above elevation 130 ft (2.75 ft above "
        "NGVD 1929 datum)", subject="1008000022", eff="2013-05-17",''',
      '''   # ⚠ CORRECTED - I dropped "view" AGAIN. The 2010 easement had the same
   # slip and was fixed hours earlier; this one repeated it from the Exhibit F
   # description. VIEW is a separate protected interest and omitting it
   # understates the burden every time.
   text="perpetual easement for LIGHT, AIR AND VIEW over the whole of lot 22 "
        "above a fixed horizontal plane at 130 ft above the Manhattan "
        "Topographical Bureau datum (2.75 ft above USC&GS mean sea level, "
        "Sandy Hook). No mechanism exists to raise the plane",
   subject="1008000022", eff="2013-05-17",''')
    c.write_text(ct, encoding="utf-8")
    print(f"recorded {len(BF)} Brick Farms slots; corrected the 'view' omission")


main()
