import pathlib

p = pathlib.Path("doctype_terms.py")
t = p.read_text(encoding="utf-8")

t = t.replace("""  status      text not null,       -- PRESENT | ABSENT | NOT_LOOKED
  page        text,
  value_text  text,                -- the negotiated value""",
"""  status      text not null,       -- PRESENT | ABSENT | NOT_LOOKED
  page        text,
  -- THE DEONTIC STRUCTURE, added 2026-08-06 after a usability failure.
  -- The card rendered the SLOT NAME ("alteration_restriction") plus a fragment
  -- of value. A slot name is an INDEX KEY, not a statement: it does not say who
  -- is bound, what they may not do, or who can release it.
  -- Login, reading the card: "the terms doesn't really explain the terms of the
  -- light and air on 120, and alteration is confusing as to who it applies to
  -- and what it is." Correct. acris_terms carried actor/modality/action from
  -- the start; the doctype menu never did, so menu-sourced terms rendered as
  -- labels while hand-entered ones rendered as sentences.
  actor       text,                -- WHO is bound
  modality    text,                -- MUST | MUST_NOT | MAY | MAY_ONLY_IF
  action      text,                -- the verb
  object      text,                -- what it acts on / the detail
  consent_of  text,                -- who can release it
  value_text  text,                -- the negotiated value""")

DEONTIC_SRC = '''
# The SENTENCE for each slot: who is bound, what they must or must not do, the
# detail, and who can release it. Rendered instead of the slot name.
DEONTIC = {
 "light_air_view_easement": ("lot 53 (the '120 Owner')", "MUST NOT",
   "build, or let anything rise, above 23 ft within a 20-ft band measured north from its rear lot line",
   "a perpetual easement of light, air AND VIEW in lot 49's favour",
   "lot 49, as benefited owner"),
 "existing_building_carveout": ("lot 53", "MAY",
   "keep its existing building standing inside that band",
   "as it stood on 2010-10-14 - but may not extend it", "lot 49"),
 "rights_conveyance": ("lots 53, 55 and 56", "MUST",
   "transfer their unused floor area to lot 49",
   "23,864 + 15,070 + 14,644 = 53,578 sf", None),
 "alteration_restriction": ("lot 53", "MUST NOT",
   "alter, add to, rebuild or replace its building if the work would",
   "(a) encroach into lot 49's light-and-air band  (b) create or worsen a zoning non-compliance that delays lot 49's permit or certificate of occupancy  (c) use any of lot 49's development rights  (d) change its use, or amend its CO, so as to reduce lot 49's rights",
   "lot 49"),
 "repair_carveout": ("lot 53", "MAY",
   "repair its building without that counting as an encroachment",
   "provided the repair does not enlarge the existing envelope", "lot 49"),
 "plan_review_right": ("lot 53", "MUST",
   "give lot 49 a copy of its plans and zoning calculations",
   "at least 10 business days before filing them with the Department of Buildings, so lot 49 can check them",
   "lot 49"),
 "violation_covenant": ("lot 53", "MUST NOT",
   "create or allow a violation of the Zoning Resolution, building code or fire code",
   "that would delay a permit or CO anywhere on the combined zoning lot, or create a non-conforming use",
   "lot 49"),
 "cure_period": ("lot 53", "MUST",
   "begin curing any such violation within 30 days of notice",
   "then proceed diligently and continuously", "lot 49"),
 "self_help_license": ("lot 49", "MAY",
   "enter lot 53's property and cure the violation itself, at lot 53's expense",
   "only after notice, only at reasonable hours except in an Emergency, without unreasonable interference, and carrying liability insurance naming lot 53 AND its mortgagee",
   "lot 53, by curing first"),
 "confirming_instrument": ("lot 53", "MUST",
   "sign a separate recordable easement document when lot 49 asks",
   "within 20 business days, on the Exhibit F form or whatever form DOB requires; lot 49 records it at its own cost",
   "lot 49"),
 "cooperation_covenant": ("lot 53", "MUST",
   "cooperate with lot 49's use of the transferred rights",
   "at no cost to lot 53 unless it is reimbursed", "lot 49"),
 "injunctive_relief": ("lot 49", "MAY",
   "sue to force lot 53 to cure", "including by injunction", None),
 "alteration_consent": ("the owner of lot 49", "MUST NOT",
   "alter, demolish or remove any building - or even threaten to",
   "without MetLife's written consent; doing so accelerates the entire loan",
   "MetLife"),
 "acceleration_triggers": ("the owner of lot 49", "MUST",
   "avoid five acceleration triggers",
   "unpaid taxes  unconsented alteration or demolition  assigning rents  letting the building fall out of good repair  failing to comply with a violation notice",
   "MetLife"),
 "advance_rent_bar": ("the owner of lot 49", "MUST NOT",
   "collect rent more than one month in advance",
   "without MetLife's written consent", "MetLife"),
 "rents_assignment": ("the owner of lot 49", "MAY",
   "keep collecting the building's rents",
   "until default - MetLife may take them on five days' written notice", "MetLife"),
 "max_principal_secured": ("this mortgage", "MAY",
   "secure no more than $25,490,000",
   "however large the consolidated position grows", None),
 "limited_recourse": ("MetLife", "MAY NOT",
   "pursue the sponsor's other assets",
   "recourse is limited per section 12.20 of the unrecorded Loan Agreement",
   None),
 "lien_spreader": ("the lender's lien", "MUST",
   "spread automatically over property it did not previously cover",
   "which is how each air-rights purchase became collateral without a new instrument",
   None),
 "single_first_lien": ("the consolidated mortgage", "MUST",
   "rank as a single FIRST lien on the premises", "", None),
 "collateral_additional_land": ("development rights bought in future", "MUST",
   "become the lender's collateral the moment they are acquired",
   "an after-acquired property clause reaching air rights", None),
 "bonus_rights_allocation": ("lots 49 and 50", "MUST",
   "split any FUTURE bonus floor area 54.52% / 45.48%",
   "by lot-area ratio, automatically, with no new agreement", "both owners"),
 "construction_easement": ("each lot", "MUST",
   "let the other enter to build, underpin, shore and protect",
   "during initial construction and any later alteration", "the granting owner"),
 "future_agency_rights": ("lots 49 and 50", "MUST",
   "split rights won later from any agency on the same ratio",
   "special permits, variances, any approval", "both owners"),
}


def _d(slot):
    """The deontic sentence for a slot, or explicit nulls saying we lack it."""
    d = DEONTIC.get(slot)
    if not d:
        return dict(actor=None, modality=None, action=None, object=None,
                    consent_of=None)
    return dict(actor=d[0], modality=d[1], action=d[2], object=d[3],
                consent_of=d[4])


'''
t = t.replace("def main():", DEONTIC_SRC + "def main():", 1)

t = t.replace("""                 page=v[1], value_text=v[2], burdened_bbl=v[3],
                 verbatim=v[4]) for s, v in INSTANCE_2010.items()]""",
"""                 page=v[1], value_text=v[2], burdened_bbl=v[3],
                 verbatim=v[4], **_d(s)) for s, v in INSTANCE_2010.items()]""")

for inst, slots in (("MTGE_INSTANCE", "MTGE_SLOTS"),
                    ("CEMA_INSTANCE", "CEMA_SLOTS"),
                    ("SPLIT_INSTANCE", "SPLIT_SLOTS")):
    old = ("                  verbatim=dict((x[0], x[5]) for x in %s)[s])\n"
           "             for s, v in %s.items()]" % (slots, inst))
    new = ("                  verbatim=dict((x[0], x[5]) for x in %s)[s],\n"
           "                  **_d(s)) for s, v in %s.items()]" % (slots, inst))
    t = t.replace(old, new)

p.write_text(t, encoding="utf-8")
print("doctype_terms.py patched with deontic structure")
