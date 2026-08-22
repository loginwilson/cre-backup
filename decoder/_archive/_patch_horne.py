"""Record the 2012 Horne ZLDA body (2012122701550003 pp004-029).

Read in full by a dispatched agent. Recording rather than re-reading.

⚠ THE SAME SPONSOR, THE SAME BLOCK, TWO YEARS APART — AND THE TERMS DIFFER.
Decoding both against one menu makes the drift visible:

    slot                  2010 (Sabetfard)        2012 (Horne)
    light/air easement    20-ft BAND above 23 ft  ELEVATION PLANE at 155.24 ft
                          from the rear lot line  over the whole 25 x 114'6" lot
    plane movable?        no                      ⚠ YES — owner may RAISE it
    plan review           10 business days        5 business days + 5-day
                                                  objection window + binding
                                                  architect arbitration
    alteration bar        four prohibited effects FIVE — adds "may not commence
                                                  before the first TCO"
    existing bldg carve   PRESENT                 ABSENT — unnecessary, the
                                                  easement starts above the roof
    repair carve-out      PRESENT                 ABSENT
    unit cap              absent                  absent
    bonus rights split    not addressed           80/20 to owner, flipping to
                                                  50/50 if the developer spent
                                                  >= $10,000 in professional fees

A decoder that assumed "ZLDAs on this block are the same" would have carried
the 2010 numbers into 2012 and been wrong about four of them.
"""
import pathlib

HORNE_SLOTS = {
 "rights_conveyance": ("PRESENT", "p008",
   "conveys the Subject Development Rights; owner expressly RETAINS Retained "
   "DR, Owner Bonus DR and Owner Upzoning DR",
   ("lot 23 (the Horne co-op)", "MUST",
    "convey its Subject Development Rights to lot 49",
    "but keeps its Retained, Bonus and Upzoning rights - it did not sell "
    "everything", None)),
 "cooperation_covenant": ("PRESENT", "p015",
   "RECIPROCAL — runs to whichever party is the Requesting Party, at that "
   "party's sole cost including the other's attorneys' fees; 10 business days",
   ("either party", "MUST", "cooperate with whichever one is Requesting",
    "at the Requesting Party's sole cost including the other side's reasonable "
    "attorneys' fees; documents produced within 10 business days, and after a "
    "further 5 days' notice the requester may file in the other's name",
    "the requesting party")),
 "light_air_view_easement": ("PRESENT", "p008",
   "⚠ A DIFFERENT SHAPE FROM 2010: an elevation-defined horizontal plane at "
   "155.24 ft above Manhattan Topographic Bureau datum, over the whole "
   "25 ft x 114 ft 6 in lot. VIEW included. ⚠ AND THE PLANE CAN BE RAISED",
   ("lot 23 (the Horne co-op)", "MUST NOT",
    "let anything rise above 155.24 ft above the Manhattan datum, across its "
    "whole 25 x 114'6\" lot",
    "a perpetual easement of light, air AND VIEW. ⚠ THE HEIGHT IS NOT FIXED - "
    "the owner may RAISE the plane whenever it acquires Bonus or Upzoning "
    "rights and uses them to add floor area, on 15 business days' notice with "
    "drawings. Anyone treating 155.24 as a permanent ceiling will be wrong "
    "after the first increase",
    "lot 49, as benefited owner")),
 "existing_building_carveout": ("ABSENT", "p008",
   "no carve-out, and none needed — the easement begins ABOVE the existing "
   "roof. The only recognition of existing structures is for rooftop "
   "mechanicals, and only if the plane is later raised", None),
 "repair_carveout": ("ABSENT", "p008",
   "⚠ UNLIKE 2010 — no clause exempts repairs from the encroachment bar. "
   "'Rebuilding' is defined to INCLUDE reconstruction and replacement and is "
   "prohibited on the same terms as an Alteration", None),
 "confirming_instrument": ("PRESENT", "p008",
   "20 business days; Exhibit G form or such alternative as DOB requires; "
   "Developer records at its sole expense",
   ("lot 23", "MUST", "sign a separate recordable easement when lot 49 asks",
    "within 20 business days, on the Exhibit G form or whatever DOB requires; "
    "lot 49 records it at its own cost", "lot 49")),
 "alteration_restriction": ("PRESENT", "p008",
   "⚠ FIVE prohibited effects, one more than 2010",
   ("lot 23", "MUST NOT",
    "build, alter or rebuild if the work would",
    "(a) COMMENCE BEFORE the first temporary CO for the entire lot 49 building "
    "- a timing bar 2010 did not have  (b) encroach above the Lower Limiting "
    "Plane as it may be raised  (c) create or worsen a non-compliance delaying "
    "lot 49's permit or CO  (d) use any rights other than its Retained, Bonus "
    "or Upzoning rights  (e) change use, or amend its CO, so as to reduce "
    "lot 49's rights", "lot 49")),
 "plan_review_right": ("PRESENT", "p009",
   "⚠ 5 business days, NOT the 10 of 2010 — plus a 5-day objection window and "
   "binding architect arbitration",
   ("lot 23", "MUST",
    "give lot 49 the complete DOB application and all plans 5 business days "
    "before filing",
    "lot 49 then has 5 business days to object; silence is a CONCLUSIVE "
    "WAIVER, time being of the essence. A dispute goes to a jointly chosen "
    "architect of 10+ years' NYC experience, AAA-appointed if they cannot "
    "agree in 15 days, whose determination BINDS; the loser pays",
    "lot 49, by not objecting")),
 "violation_covenant": ("PRESENT", "p010",
   "reciprocal — lot 49 owes the same covenant back at section II.B.2",
   ("lot 23", "MUST NOT",
    "create or permit a violation of the Zoning Resolution, building code or "
    "fire code",
    "that would delay a permit or CO for ANY building on the combined zoning "
    "lot, or create or increase a non-conforming use. ⚠ lot 49 owes the "
    "identical covenant back", "lot 49")),
 "cure_period": ("PRESENT", "p010",
   "30 days to commence, reciprocal",
   ("lot 23", "MUST", "begin curing within 30 days of notice",
    "then proceed diligently with commercially reasonable efforts. Lot 49 owes "
    "the same", "lot 49")),
 "self_help_license": ("PRESENT", "p010",
   "entry licence with four conditions; reimbursement at CITIBANK PRIME "
   "COMPOUNDED MONTHLY; general entry notice 10 days",
   ("lot 49", "MAY", "enter lot 23 and cure at lot 23's expense",
    "only after notice, at reasonable times except in an Emergency, without "
    "unreasonable interference, protecting the owner's property, and carrying "
    "insurance naming lot 23 AND any mortgagee it knows of. Repayment carries "
    "interest at Citibank prime compounded monthly; lot 23 keeps the right to "
    "contest both the violation and the spend", "lot 23, by curing first")),
 "injunctive_relief": ("PRESENT", "p024",
   "specific performance expressly reserved, with NO CONSEQUENTIAL DAMAGES",
   ("either party", "MAY", "seek injunctive relief and specific performance",
    "but NOT consequential damages; and recovery is limited to that party's "
    "interest in the combined zoning lot - no personal liability for partners, "
    "officers, directors or shareholders", None)),
 "runs_with_land": ("PRESENT", "p023",
   "four-part binding clause; also binds future acquirers to FUTURE "
   "modifications they never signed",
   ("every party with any interest, and their successors", "MUST",
    "take subject to this agreement",
    "⚠ and section X binds future acquirers to future MODIFICATIONS they "
    "never executed", "all parties in interest")),
 "dob_consent_to_amend": ("PRESENT", "p048",
   "⚠ ONLY IN THE EXHIBIT G FORM, which is unexecuted. The ZLDA itself is "
   "amended by the parties alone with no agency consent",
   ("both parties", "MUST NOT",
    "modify, amend or terminate the CONFIRMING easement without DOB consent",
    "⚠ but this lives in the unexecuted Exhibit G form. The ZLDA itself "
    "(section XXI) needs only the parties' signatures - no agency at all",
    "NYC Department of Buildings, once the form is executed")),
 "co_recording_covenant": ("PRESENT", "p048",
   "⚠ also only in the Exhibit G form",
   ("the owner of either parcel", "MUST",
    "put the CRFN on every future CO and in any deed",
    "⚠ contingent - this sits in the unexecuted Exhibit G form", "DOB")),
 "unit_cap": ("ABSENT", "p016",
   "no dwelling-unit cap anywhere in the body. Residential use is a MONEY "
   "trigger instead: if residential use appears before the permanent CO, "
   "lot 49 owes lot 23 the 'Section 3(d) Rights' under a Sale Agreement that "
   "is NOT part of this instrument", None),
}

# clauses with no slot in the ZLDA menu — the menu grows
NEW_SLOTS = [
 ("bonus_rights_split", True, "BOTH", "ENVELOPE",
  "how are the owner's bonus rights split, and what flips the ratio?",
  "p006 section I.C — Owner Parcel Bonus Rights are pro-rated by lot area, "
  "then OWNER TAKES 80%. ⚠ the split flips to 50/50 if the bonus became "
  "available through the Developer's efforts AND not less than $10,000 in "
  "professional fees. A NAMED DOLLAR THRESHOLD THAT REALLOCATES VALUE"),
 ("lower_limiting_plane_raise", False, "GRANTOR", "HEIGHT",
  "⚠ can the height plane MOVE?",
  "p008 section II.A.2 — the owner may raise the Lower Limiting Plane using an "
  "'Owner Permitted Increase', on 15 business days' notice with architectural "
  "drawings and the proposed new height; the easement is deemed raised to the "
  "minimum height that permits the work. THE CONSTRAINT IS VARIABLE"),
 ("architect_arbitration", False, "BOTH", "PROCESS",
  "who decides a plans dispute, and is it binding?",
  "p009 — two architects, then a jointly designated Qualified Professional "
  "(licensed, 10+ years on similar NYC buildings), AAA-appointed if no "
  "agreement in 15 days, determination in 15 days and BINDING; fees split then "
  "shifted to the loser. The owner may not file pending resolution"),
 ("anti_merger_covenant", True, "GRANTOR", "ENVELOPE",
  "may the burdened lot join a DIFFERENT zoning lot?",
  "p011 section II.A.5 — the owner may not merge its zoning lot with any "
  "parcel outside the combined zoning lot without the developer's prior "
  "written consent. The mirror of the assemblage right"),
 ("non_opposition_covenant", False, "GRANTOR", "PROCESS",
  "may the burdened owner object at a public hearing?",
  "p016 section III.D — the owner shall not voluntarily appear in opposition "
  "before the community board, CPC, DCP, DOB, City Council, BSA, HPD, LPC or "
  "any state or federal agency"),
 ("downzoning_allocation", False, "BOTH", "ENVELOPE",
  "what happens to rebuild rights if the area is DOWNZONED?",
  "p013 sections II.C.1-3 — three scenarios (one building, all buildings, some "
  "buildings) allocating post-downzoning rebuild rights pro rata by the "
  "Exhibit D ratio"),
 ("upzoning_allocation", False, "BOTH", "ENVELOPE",
  "who gets the upside of an UPZONING?",
  "p014 section II.C.4 — split as if each were a separate zoning lot; if the "
  "upzoning does not reach the owner's premises, the owner gets nothing"),
 ("residential_use_trigger", False, "GRANTEE", "USE",
  "does residential use on the developer parcel cost anything?",
  "p016 section III.E — if any residential use appears before the permanent "
  "CO, the developer owes the owner the 'Section 3(d) Rights' set out in a "
  "SALE AGREEMENT NOT PART OF THIS INSTRUMENT. ⚠ an off-register obligation "
  "triggered by a use decision"),
 ("estoppel_certificates", False, "BOTH", "PROCESS",
  "how often can a party demand a status certificate?",
  "p022 — not more than twice a year, on 20 business days' notice, at the "
  "requester's cost, no liability except for fraud"),
 ("preconstruction_survey", False, "GRANTOR", "ACCESS",
  "may the developer document the neighbour's condition before building?",
  "p022 section XIII.A — right to enter and document pre-existing condition on "
  "10 days' written notice, owner's representative may accompany throughout at "
  "the developer's cost"),
 ("construction_insurance", False, "GRANTEE", "PROCESS",
  "what insurance must the builder carry, and rated how?",
  "p023 — ISO Form CG 00 01, owner as additional insured primary and "
  "non-contributory, occurrence basis, $5,000,000 per occurrence / $10,000,000 "
  "aggregate, defence costs OUTSIDE the limit, carrier rated A-X or better by "
  "A.M. Best"),
 ("effect_of_breach", True, "BOTH", "ENVELOPE",
  "does a breach un-merge the zoning lot?",
  "p024 section XVI — no. The merger survives contract failure, which protects "
  "the envelope against a dispute between the parties"),
 ("subdivision_right", False, "GRANTEE", "ENVELOPE",
  "may the developer subdivide without paying again?",
  "p020 section IX — the developer may subdivide 'without any additional "
  "compensation or consideration to Owner'. ⚠ THIS IS WHY THE 2019 SPLIT "
  "NEEDED NO CONSENT FROM ANY OF THE SIX SELLER LOTS"),
]


def main():
    p = pathlib.Path("doctype_terms.py")
    t = p.read_text(encoding="utf-8")

    # 1 · extend the ZLDA menu
    src = ["\n# ---- slots found in the 2012 Horne instrument that the 2010 one",
           "# ---- did not have. The menu grows as instances are read.",
           "ZLDA_SLOTS += ["]
    for s, ty, b, d, v, n in NEW_SLOTS:
        src.append(" (%r, %r, %r, %r,\n  %r,\n  %r)," % (s, ty, b, d, v, n))
    src.append("]\n")

    # 2 · the Horne instance
    src.append("HORNE_INSTANCE = {")
    for slot, (st, pg, val, deo) in HORNE_SLOTS.items():
        src.append(" %r: (%r, %r, %r)," % (slot, st, pg, val))
    src.append("}\n")
    src.append("HORNE_DEONTIC = {")
    for slot, (st, pg, val, deo) in HORNE_SLOTS.items():
        if deo:
            src.append(" %r: %r," % (slot, deo))
    src.append("}\n")

    t = t.replace("def _d(slot):", "\n".join(src) + "\n\ndef _d(slot):", 1)

    # 3 · emit the instance rows
    t = t.replace("""    inst += [dict(document_id="2019071700601003",""",
"""    def _hd(s):
        d = HORNE_DEONTIC.get(s)
        if not d:
            return dict(actor=None, modality=None, action=None, object=None,
                        consent_of=None)
        return dict(actor=d[0], modality=d[1], action=d[2], object=d[3],
                    consent_of=d[4])

    inst += [dict(document_id="2012122701550003", effective="2012-12-19",
                  slot=s, status=v[0], page=v[1], value_text=v[2],
                  burdened_bbl="1008000023", verbatim=v[2], **_hd(s))
             for s, v in HORNE_INSTANCE.items()]
    inst += [dict(document_id="2019071700601003",""")

    p.write_text(t, encoding="utf-8")
    print(f"recorded {len(HORNE_SLOTS)} Horne slots + {len(NEW_SLOTS)} new menu slots")


main()
