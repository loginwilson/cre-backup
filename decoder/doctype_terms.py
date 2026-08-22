"""DOCTYPE TERM TEMPLATES — codify the type, then read instances against it.

LOGIN, 2026-08-06:

    "It's technically both. Documents tend to mix and match terms, so you have
     to codify the document type basically by identifying PATTERNS ACROSS THE
     TYPE."

    Exactly. A ZLDA is not bespoke prose. It is a standard clause set, assembled
    from a menu, with a handful of negotiated values dropped in. Once the menu is
    written down, reading instance #2 stops being "read 110 pages and hope" and
    becomes "check each slot: present, absent, or varied — and what value."

    That is the difference between decoding one document and decoding 1,201.

⚠ THE THREE CORRECTIONS THIS EXERCISE PRODUCED IMMEDIATELY

    Reading 2010102601040006 pp008-009 against the template found THREE errors in
    structured data already written from the Exhibit D chart alone:

    1. THE EASEMENT IS "LIGHT, AIR AND VIEW", not light and air. View is a
       separate protected interest and a broader restriction.

    2. THE BAND IS MEASURED FROM THE REAR LOT LINE, EXTENDING 20 FT NORTH — not
       from "the lot line shared with lot 49" as I recorded it. On a
       through-block assemblage those are different lines, so the burdened
       region was in the wrong place on the parcel.

    3. ⚠ ONLY THE "120 OWNER" GRANTS IT. My constraint row said "applies to
       lots 53, 55 and 56 alike". The clause reads "120 Owner hereby grants" —
       lot 53 ONLY. Lots 55 and 56 sold rights without granting a light-and-air
       easement, so their height constraint was INVENTED BY ME.

    All three came from having read the CHART and not the COVENANTS. The chart
    gives quantities; only the body gives terms. This is the concrete cost of
    3% terms coverage.
"""
import csv, pathlib, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent

DDL = """
-- the MENU: what clauses a document type is known to carry ------------------
create table if not exists doctype_term_slots (
  doc_type   text not null,
  slot       text not null,        -- stable name for the clause
  typical    bool not null,        -- appears in most instances?
  burdens    text not null,        -- GRANTOR | GRANTEE | BOTH
  dimension  text,                 -- HEIGHT | USE | ACCESS | PROCESS | REMEDY
  what_varies text,                -- the negotiated values to capture
  note       text,
  primary key (doc_type, slot)
);

-- the INSTANCE: which slots this document actually used, and how -------------
create table if not exists doctype_term_instance (
  document_id text not null,
  slot        text not null,
  status      text not null,       -- PRESENT | ABSENT | NOT_LOOKED
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
  value_text  text,                -- the negotiated value
  burdened_bbl text,
  verbatim    text,
  primary key (document_id, slot)
);

-- ⚠ ABSENT means we read the document and the clause is not there. NOT_LOOKED
-- is the default. A type template makes the gap VISIBLE: with a menu of 14
-- slots, a document with 6 read and 8 NOT_LOOKED reports 43% examined instead
-- of "decoded".

create or replace view doctype_coverage as
select i.document_id, count(*) filter (where status='PRESENT') as present,
       count(*) filter (where status='ABSENT') as absent,
       count(*) filter (where status='NOT_LOOKED') as not_looked
from doctype_term_instance i group by i.document_id;
"""

# ---------------------------------------------------------------------------
# THE ZLDA MENU, built from 2010102601040006 §II and the 2013 instruments.
# `what_varies` is the point: it names the negotiated value to extract, so the
# next ZLDA is a fill-in rather than a hunt.
# ---------------------------------------------------------------------------
ZLDA_SLOTS = [
 ("rights_conveyance", True, "GRANTOR", "ENVELOPE",
  "how many sf; from which lot; retained balance",
  "§II.A.1 'Owner hereby conveys to Developer the Subject Development Rights'"),
 ("cooperation_covenant", True, "GRANTOR", "PROCESS",
  "at whose cost; reimbursement trigger",
  "Owner must cooperate with incorporation into the Developer Building, at no "
  "cost to Owner unless reimbursed"),
 ("light_air_view_easement", True, "GRANTOR", "HEIGHT",
  "WHICH LOT grants it (not always all of them); the line it is measured FROM; "
  "the depth; the elevation; whether VIEW is included",
  "⚠ the slot that produced all three corrections"),
 ("existing_building_carveout", True, "GRANTOR", "HEIGHT",
  "may the existing building remain in the easement area?",
  "'Owner shall be permitted to maintain in the Light and Air Easement Area the "
  "Owner Building as it exists on the date hereof'"),
 ("confirming_instrument", True, "GRANTOR", "PROCESS",
  "how many business days to execute; whose form; who records; whose expense",
  "20 Business Days after written request, in the form of Exhibit F or as DOB "
  "requires; Developer may record at its sole expense"),
 ("alteration_restriction", True, "GRANTOR", "USE",
  "the four prohibited effects (a)-(d)",
  "no Alterations or Rebuilding that (a) encroach on the easement area, "
  "(b) create/increase non-compliance delaying the Developer's permit or CO, "
  "(c) utilise Developer Development Rights, (d) change use or amend the CO so "
  "as to decrease Developer Development Rights"),
 ("repair_carveout", True, "GRANTOR", "USE",
  "does a repair count as encroachment?",
  "'repairs that do not increase the envelope of the existing Owner Building "
  "shall not be deemed an encroachment'"),
 ("plan_review_right", True, "GRANTOR", "PROCESS",
  "notice period before DOB filing",
  "Owner must give Developer its Rebuilding Plans NOT LESS THAN TEN BUSINESS "
  "DAYS before submitting to DOB, so Developer can confirm compliance"),
 ("violation_covenant", True, "GRANTOR", "USE",
  "what counts as a Violation",
  "Owner must not create or permit a violation of the ZR, building code or fire "
  "code that would delay a permit or CO on the Combined Zoning Lot, or create a "
  "new non-conforming use"),
 ("cure_period", True, "GRANTOR", "REMEDY",
  "days to commence cure",
  "THIRTY DAYS after notice, then proceed diligently and continuously"),
 ("self_help_license", True, "GRANTOR", "ACCESS",
  "conditions on entry; emergency exception; insurance required",
  "Developer may cure at Owner's expense and has a LICENSE TO ACCESS the Owner "
  "Parcel; only after notice, only at reasonable times except in an Emergency "
  "Situation, no unreasonable interference; Developer must carry liability "
  "insurance naming Owner AND ANY MORTGAGEE of the Owner Parcel"),
 ("injunctive_relief", True, "GRANTOR", "REMEDY",
  "is specific performance reserved?",
  "Developer may maintain any action at law or equity including injunctive "
  "relief to compel cure"),
 ("dob_consent_to_amend", False, "BOTH", "PROCESS",
  "is DOB a required consenting party?",
  "⚠ present in the DOB-FORM easement (Exhibit G); makes the burden "
  "unreleasable by the parties alone"),
 ("runs_with_land", True, "BOTH", "PROCESS",
  "binds successors?",
  "covenants run with the land and bind heirs, successors and assigns"),
 ("co_recording_covenant", False, "BOTH", "PROCESS",
  "must the CRFN appear on every future CO and deed?",
  "breach risks revocation of a building permit or CO"),
 ("unit_cap", False, "GRANTOR", "USE",
  "maximum dwelling units",
  "seen on lot 21 (seven units) — NOT a standard ZLDA slot, negotiated"),
 ("parking_lane_letter", False, "GRANTOR", "ACCESS",
  "width; period; expires with construction",
  "a FORM attached as an exhibit, executed per job — does NOT run with the land"),
]

# what the 2010 instrument actually did, slot by slot
INSTANCE_2010 = {
 "rights_conveyance": ("PRESENT", "p008", "53,578 sf from lots 53/55/56",
                       "1008000053", "Owner hereby conveys to Developer the "
                       "Subject Development Rights"),
 "cooperation_covenant": ("PRESENT", "p008", "at no cost to Owner unless reimbursed",
                          "1008000053", "Owner shall cooperate with Developer, at "
                          "no cost or financial obligation to Owner unless Owner "
                          "is reimbursed"),
 "light_air_view_easement": ("PRESENT", "p008",
    "LIGHT, AIR AND VIEW · granted by the 120 OWNER ONLY (lot 53) · measured "
    "from the REAR LOT LINE extending 20 ft NORTH · beginning 23 ft above curb "
    "level · PERPETUAL",
    "1008000053",
    "120 Owner hereby grants to Developer a perpetual easement for light, air "
    "and view (the 'Light and Air Easement') above the portion of the 120 Owner "
    "Land beginning at the rear lot line (as defined in the Zoning Resolution) "
    "of the 120 Owner Land and extending from such rear lot line a distance of "
    "twenty (20') feet to the north of such rear lot line, beginning at a height "
    "of twenty-three (23') feet above curb level"),
 "existing_building_carveout": ("PRESENT", "p008",
    "the 120 Owner Building may remain as it exists at the date hereof",
    "1008000053", "Notwithstanding the above, 120 Owner shall be permitted to "
    "maintain in the Light and Air Easement Area the 120 Owner Building as it "
    "exists on the date hereof"),
 "confirming_instrument": ("PRESENT", "p008",
    "20 Business Days; Exhibit F form or as DOB requires; Developer records at "
    "its sole expense", "1008000053",
    "If requested in writing by Developer, 120 Owner shall, within twenty (20) "
    "Business Days after its receipt of such request, execute, acknowledge and "
    "deliver to Developer a document confirming the grant"),
 "alteration_restriction": ("PRESENT", "p008",
    "four prohibited effects (a) encroachment (b) non-compliance delaying "
    "Developer's permit/CO (c) use of Developer Development Rights (d) use "
    "change or CO amendment decreasing Developer Development Rights",
    "1008000053",
    "Owner covenants and agrees that no new buildings, improvements, "
    "alterations or additions shall be constructed or allowed to exist on the "
    "Owner Parcel"),
 "repair_carveout": ("PRESENT", "p008", "repairs not increasing the envelope",
    "1008000053", "provided that any repairs of the Owner Building that do not "
    "increase the envelope of the existing Owner Building shall not be deemed "
    "to be an encroachment"),
 "plan_review_right": ("PRESENT", "p009", "10 Business Days before DOB filing",
    "1008000053", "not less than ten (10) Business Days prior to submitting to "
    "the Department of Buildings any plans or zoning calculations ... Owner "
    "shall give a copy of Owner's Rebuilding Plans to Developer"),
 "violation_covenant": ("PRESENT", "p009", "ZR, building code, fire code",
    "1008000053", "Owner covenants and agrees not to create, or permit to "
    "exist, a violation of the Zoning Resolution or any building code, fire "
    "code, or other law"),
 "cure_period": ("PRESENT", "p009", "30 days after notice", "1008000053",
    "Owner shall commence a cure within thirty (30) days after receiving notice "
    "of the same from Developer"),
 "self_help_license": ("PRESENT", "p009",
    "after notice; reasonable times except Emergency Situation; no unreasonable "
    "interference; liability insurance naming Owner AND its mortgagee",
    "1008000053",
    "Developer shall have the right to cure such Violation at the expense and "
    "for the account of Owner ... it being agreed that Developer shall have a "
    "license to have access to the Owner Parcel for the purpose of effecting "
    "such cure"),
 "injunctive_relief": ("PRESENT", "p009", "action at law or equity",
    "1008000053", "Developer may, at its option, maintain any action permitted "
    "at law or in equity or by statute against Owner ... including an action "
    "for injunctive relief to compel Owner to cure such Violation"),
 "dob_consent_to_amend": ("NOT_LOOKED", None, None, None, None),
 "runs_with_land": ("NOT_LOOKED", None, None, None, None),
 "co_recording_covenant": ("NOT_LOOKED", None, None, None, None),
 "unit_cap": ("ABSENT", "p008", "no unit cap in this instrument", None, None),
 "parking_lane_letter": ("NOT_LOOKED", None, None, None, None),
}


# ---------------------------------------------------------------------------
# THE MORTGAGE MENU, from 2023110100486009 p005 (MetLife, $25,490,000).
# The statutory NY covenants plus negotiated riders. Read against ANY mortgage.
# ---------------------------------------------------------------------------
MTGE_SLOTS = [
 ("one_parcel_foreclosure", True, "BORROWER", "REMEDY",
  "may the premises be sold as one parcel?",
  "§10 'in the case of a foreclosure sale, said premises ... may be sold in one "
  "parcel' — matters on an ASSEMBLAGE: the lender can sell the whole thing "
  "together rather than lot by lot"),
 ("lender_cost_lien", True, "BORROWER", "REMEDY",
  "do the lender's legal costs become debt, and at what priority?",
  "§11 sums paid to defend the lien, including counsel fees, become a lien "
  "PRIOR to any interest attaching after this mortgage"),
 ("rents_assignment", True, "BORROWER", "INCOME",
  "are rents assigned; when does the lender take them",
  "§12 rents, issues and profits assigned as further security; lender WAIVES "
  "collection until default, revocable on FIVE DAYS' WRITTEN NOTICE"),
 ("advance_rent_bar", True, "BORROWER", "INCOME",
  "how far in advance may rent be collected",
  "§12 no rent may be collected MORE THAN ONE MONTH IN ADVANCE without the "
  "lender's written consent"),
 ("possession_on_default", True, "BORROWER", "INCOME",
  "what happens to occupancy on default",
  "§12 on default the borrower pays fair rental value monthly to the lender or "
  "a receiver, or vacates and may be EVICTED BY SUMMARY PROCEEDINGS"),
 ("acceleration_triggers", True, "BORROWER", "REMEDY",
  "what makes the whole balance due",
  "§13 (a) no tax receipts within 20 days of demand (b) ALTERATION, DEMOLITION "
  "OR REMOVAL of any building without written consent (c) assignment of rents "
  "without consent (d) buildings not in reasonably good repair (e) failure to "
  "comply with a violation notice"),
 ("alteration_consent", True, "BORROWER", "USE",
  "⚠ may the owner alter or demolish, and whose consent is needed",
  "§13(b) THE REDEVELOPMENT CONSTRAINT. Actual OR THREATENED alteration, "
  "demolition or removal of any building without the lender's written consent "
  "accelerates the entire loan"),
 ("repair_covenant", True, "BORROWER", "USE",
  "standard of maintenance",
  "§13(d) buildings must be kept in reasonably good repair"),
 ("violation_compliance", True, "BORROWER", "USE",
  "must violations be cured",
  "§13(e) failure to comply with any order or notice of violation is an "
  "acceleration event — links DOB violations directly to the debt"),
 ("insurance_254", True, "BORROWER", "PROCESS",
  "insurance under RPL §254",
  "§9 additional insurance construed under Real Property Law section 254"),
 # ---- from p006 -------------------------------------------------------
 ("max_principal_secured", True, "BORROWER", "REMEDY",
  "⚠ THE CEILING ON THE LIEN — not the same as the consolidated position",
  "§18 'the maximum amount of principal indebtedness secured by this Mortgage "
  "or which under any contingency may be secured' — caps what this instrument "
  "can ever secure, regardless of what the consolidation says"),
 ("limited_recourse", False, "LENDER", "REMEDY",
  "is the borrower personally liable?",
  "§16 'Recourse under this Mortgage is limited as provided in Section 12.20 of "
  "the Loan Agreement' — a NON/LIMITED-RECOURSE loan. The lender's remedy is "
  "the building, not the sponsor's other assets, subject to carve-outs"),
 ("loan_agreement_controls", True, "BOTH", "PROCESS",
  "⚠ which document actually governs, and is it recorded?",
  "§19 'In the event of any conflict ... the provisions of the Loan Agreement "
  "shall control', except as to creation and perfection of liens. THE LOAN "
  "AGREEMENT IS NOT RECORDED — rate, maturity, covenants and reserves live in "
  "a document ACRIS has never seen"),
 ("lien_law_trust_fund", True, "BORROWER", "PROCESS",
  "must advances be spent on the improvement first?",
  "§14 advances held as a TRUST FUND under NY Lien Law §13, applied FIRST to "
  "the cost of the improvement before any other purpose"),
 ("binds_tenants", True, "BORROWER", "PROCESS",
  "who is bound besides the owner?",
  "§17 covenants run with the land and bind subsequent owners, encumbrancers, "
  "TENANTS AND SUBTENANTS — a lease taken today is taken subject to this"),
 ("no_oral_modification", True, "BOTH", "PROCESS",
  "can it be varied by conduct?",
  "§17 'may not be changed or terminated orally'"),
 ("insurability_default", True, "BORROWER", "REMEDY",
  "does uninsurability accelerate?",
  "§13(f) if two or more NY fire insurers refuse to write the building, the "
  "loan accelerates — a climate/condition risk with a debt trigger"),
 ("fixtures_removal_default", True, "BORROWER", "REMEDY",
  "may fixtures be removed?",
  "§13(g) removal, demolition or destruction of fixtures or chattels unless "
  "promptly replaced with equal quality, free of chattel mortgages"),
 ("tax_law_change_default", True, "BORROWER", "REMEDY",
  "what if mortgage taxation changes?",
  "§13(h) on 30 days' notice, a law changing the taxation of mortgages "
  "accelerates the loan"),
 ("catchall_covenant_default", True, "BORROWER", "REMEDY",
  "is any breach a default?",
  "§13(i) failure to keep ANY other covenant in the Mortgage"),
]

MTGE_INSTANCE = {
 "one_parcel_foreclosure": ("PRESENT", "p005", "may be sold in one parcel"),
 "lender_cost_lien": ("PRESENT", "p005", "counsel fees become a PRIOR lien"),
 "rents_assignment": ("PRESENT", "p005", "waived until default; 5 days' notice"),
 "advance_rent_bar": ("PRESENT", "p005", "one month maximum"),
 "possession_on_default": ("PRESENT", "p005", "fair rental value or eviction"),
 "acceleration_triggers": ("PRESENT", "p005", "five triggers (a)-(e)"),
 "alteration_consent": ("PRESENT", "p005",
   "⚠ NO ALTERATION, DEMOLITION OR REMOVAL WITHOUT METLIFE'S WRITTEN CONSENT"),
 "repair_covenant": ("PRESENT", "p005", "reasonably good repair"),
 "violation_compliance": ("PRESENT", "p005", "violation notice = default"),
 "insurance_254": ("PRESENT", "p005", "RPL section 254"),
 "max_principal_secured": ("PRESENT", "p006", "$25,490,000 MAXIMUM"),
 "limited_recourse": ("PRESENT", "p006",
   "limited per Loan Agreement §12.20 — NON/LIMITED RECOURSE"),
 "loan_agreement_controls": ("PRESENT", "p006",
   "⚠ the Loan Agreement CONTROLS and is NOT RECORDED"),
 "lien_law_trust_fund": ("PRESENT", "p006", "NY Lien Law §13 trust fund"),
 "binds_tenants": ("PRESENT", "p006", "binds owners, encumbrancers, TENANTS, subtenants"),
 "no_oral_modification": ("PRESENT", "p006", "no oral change or termination"),
 "insurability_default": ("PRESENT", "p006", "2+ insurers refusing = default"),
 "fixtures_removal_default": ("PRESENT", "p006", "unless promptly replaced, equal quality"),
 "tax_law_change_default": ("PRESENT", "p006", "30 days' notice"),
 "catchall_covenant_default": ("PRESENT", "p006", "any other covenant"),
}


# ---------------------------------------------------------------------------
# THE CEMA / CONSOLIDATION MENU, from 2013081200922003 p005 (Goldman, $40.5M).
# ⚠ This is the type ACRIS calls AGMT. 14 of lot 49's documents are AGMT and
# every one of them is one of these.
# ---------------------------------------------------------------------------
CEMA_SLOTS = [
 ("no_default_rep", True, "BORROWER", "PROCESS",
  "is the borrower representing it is current?",
  "§1(b) 'there are no defaults or events of default under the Existing Notes "
  "and Mortgages, nor has any event occurred that would be a default ... with "
  "the passage of time, the giving of notice, or both' — A DATED STATEMENT "
  "THAT THE LOAN WAS PERFORMING, useful as a distress signal by its absence"),
 ("fee_title_rep", True, "BORROWER", "PROCESS",
  "what encumbrances are carved out, and where are they listed?",
  "§1(c) good, marketable, insurable fee title SUBJECT TO PERMITTED "
  "ENCUMBRANCES — ⚠ defined in the Term (Committed Loan) Loan Agreement, which "
  "is NOT RECORDED. The list of what burdens the title is off-register"),
 ("authority_rep", True, "BORROWER", "PROCESS",
  "does this breach the operating agreement or another instrument?",
  "§1(d) execution violates no article of organization, operating agreement, "
  "lease, mortgage, indenture or law"),
 ("consolidation_amount", True, "BOTH", "REMEDY",
  "⚠ THE SINGLE INDEBTEDNESS after combining — not new money",
  "§2 the Existing Notes 'have been combined and consolidated to constitute a "
  "single indebtedness in the aggregate principal amount of ...'"),
 ("consolidated_note", True, "BORROWER", "PROCESS",
  "is there a replacement note, and is it recorded?",
  "§3 a Consolidated, Amended and Restated Mortgage Loan Note is substituted "
  "for the Existing Notes. ⚠ THE NOTE IS NOT RECORDED — rate and maturity are "
  "off-register"),
 ("lien_spreader", True, "BORROWER", "ENVELOPE",
  "⚠ does the lien SPREAD to property it did not previously cover?",
  "§4 the liens are consolidated and coordinated into ONE mortgage 'and, as so "
  "consolidated and coordinated, are hereby SPREAD OVER THOSE PORTIONS OF THE "
  "PROPERTY NOT ALREADY COVERED THEREBY'. ⚠ ON AN ASSEMBLAGE THIS IS HOW "
  "NEWLY-ACQUIRED LAND AND AIR RIGHTS GET PULLED UNDER THE EXISTING LIEN"),
 ("single_first_lien", True, "BOTH", "PRIORITY",
  "what priority does the consolidated lien hold?",
  "§4 'shall hereafter constitute in law but one mortgage, a single, FIRST LIEN "
  "upon the Premises securing the Indebtedness' — the PRIORITY answer, stated "
  "outright"),
 # ---- SCHEDULE C, the granting clause (pp020-052) ---------------------
 ("collateral_additional_land", True, "BORROWER", "ENVELOPE",
  "⚠ does the lien reach rights the owner has NOT YET BOUGHT?",
  "Sch C (b) 'All additional lands, estates and DEVELOPMENT RIGHTS HEREAFTER "
  "ACQUIRED by Mortgagor for use in connection with the Land and the "
  "development of the Land'. ⚠ AN AFTER-ACQUIRED PROPERTY CLAUSE OVER AIR "
  "RIGHTS. On an assemblage the lender captures each purchase automatically as "
  "it is made — no new instrument required. Pair it with the §4 spreader and "
  "the lender holds the whole assemblage the moment it exists"),
 ("collateral_easements", True, "BORROWER", "ENVELOPE",
  "are air rights and development rights named as collateral?",
  "Sch C (d) the granted estate expressly includes 'air rights and development "
  "rights ... privileges, liberties, servitudes, tenements, hereditaments and "
  "appurtenances', plus land in the bed of any street to the centre line"),
 ("collateral_improvements", True, "BORROWER", "PROCESS",
  "does it cover buildings not yet built?",
  "Sch C (c) buildings, fixtures, additions, ENLARGEMENTS and improvements "
  "'now or hereafter erected' — the tower built in 2016 became collateral "
  "under a 2013 instrument"),
 ("collateral_equipment", True, "BORROWER", "PROCESS",
  "what personal property is caught, and what is carved out?",
  "Sch C (e) UCC Article 9 equipment, now owned or hereafter acquired. "
  "⚠ CARVE-OUT: 'Equipment shall not include any property belonging to TENANTS "
  "under leases' except to the extent the Mortgagor has an interest"),
 ("modification_by_schedule", True, "BORROWER", "PROCESS",
  "⚠ WHERE DO THE OPERATIVE TERMS ACTUALLY LIVE?",
  "§5 the Mortgages are modified, extended, amended and restated IN THEIR "
  "ENTIRETY and their terms 'shall be and hereby are SUPERSEDED AND REPLACED "
  "by the terms ... set forth in SCHEDULE C annexed hereto'. ⚠ SCHEDULE C IS "
  "RECORDED — unlike the Loan Agreement. On this instrument it is pp020-052, "
  "which is why the document is 61 pages"),
]

# ---------------------------------------------------------------------------
# THE SPLIT-ZLDA MENU, from 2019071700601003 p008 (lot 49 / lot 50 division).
# A sixth ZLDA that DIVIDES rather than merges — different slots entirely.
# ---------------------------------------------------------------------------
SPLIT_SLOTS = [
 ("bonus_rights_allocation", True, "BOTH", "ENVELOPE",
  "⚠ how are FUTURE bonus development rights split?",
  "§N Lot 49 takes 54.52% of any Development Rights Parcel Bonus Development "
  "Rights, being its pro rata share by lot area: 8,527 / 15,639 = 54.5239%. "
  "⚠ VERIFIED TO THE STATED FIGURE. A FORWARD-LOOKING SPLIT — if either lot "
  "ever earns bonus FAR (inclusionary housing, plaza, transit), it divides on "
  "this ratio without a new agreement"),
 ("future_agency_rights", True, "BOTH", "ENVELOPE",
  "are rights won later from an agency captured?",
  "§M 'Lot 49 Development Rights' includes any additional rights acquired 'by "
  "application to any Agency for a SPECIAL PERMIT, VARIANCE or any other "
  "permit or approval' — a future BSA variance or DCP special permit is "
  "pre-allocated by this instrument"),
 ("construction_easement", True, "BOTH", "ACCESS",
  "is there a construction access right between the lots?",
  "§J 'Easements' expressly includes a CONSTRUCTION EASEMENT — the two lots "
  "carry mutual construction access"),
 ("emergency_definition", True, "BOTH", "ACCESS",
  "what triggers emergency entry, and how is it bounded?",
  "§K four limbs: 1) structural support or bodily injury 2) substantial "
  "economic loss or civil/criminal penalties to either owner 3) loss of "
  "utility, elevator or essential services 4) interference with ingress or "
  "egress. ⚠ The same concept the 2010 ZLDA used unbounded — here it is DEFINED"),
 ("zr_12_10_definitions", True, "BOTH", "PROCESS",
  "which terms take their meaning from the Zoning Resolution?",
  "§I 'dwelling unit', 'floor area', 'floor area ratio', 'lot coverage', "
  "'zoning lot', 'parties in interest', 'use' and 'bulk' all take their ZR "
  "§12-10 meanings — the instrument defers to the ZR, so a ZR amendment can "
  "move these definitions underneath the agreement"),
]

SPLIT_INSTANCE = {
 "bonus_rights_allocation": ("PRESENT", "p008", "54.52% lot 49 / 45.48% lot 50"),
 "future_agency_rights": ("PRESENT", "p008", "special permits and variances captured"),
 "construction_easement": ("PRESENT", "p008", "mutual construction easement"),
 "emergency_definition": ("PRESENT", "p008", "four defined limbs"),
 "zr_12_10_definitions": ("PRESENT", "p008", "defers to ZR 12-10"),
}

CEMA_INSTANCE = {
 "no_default_rep": ("PRESENT", "p005", "no defaults as of 2013-08-07"),
 "fee_title_rep": ("PRESENT", "p005",
   "⚠ Permitted Encumbrances defined in an UNRECORDED Loan Agreement"),
 "authority_rep": ("PRESENT", "p005", "no violation of the operating agreement"),
 "consolidation_amount": ("PRESENT", "p005", "$40,500,000 single indebtedness"),
 "consolidated_note": ("PRESENT", "p005", "⚠ Consolidated Note NOT RECORDED"),
 "lien_spreader": ("PRESENT", "p005",
   "⚠ SPREAD over portions not already covered — catches the acquired air rights"),
 "single_first_lien": ("PRESENT", "p005", "a single FIRST LIEN"),
 "collateral_additional_land": ("PRESENT", "p021",
   "⚠ after-acquired DEVELOPMENT RIGHTS automatically become collateral"),
 "collateral_easements": ("PRESENT", "p021",
   "air rights and development rights named in the granting clause"),
 "collateral_improvements": ("PRESENT", "p021", "now or hereafter erected"),
 "collateral_equipment": ("PRESENT", "p021", "UCC Art 9; tenant property carved out"),
 "modification_by_schedule": ("PRESENT", "p005",
   "Schedule C (pp020-052) supersedes and replaces all prior mortgage terms"),
}



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
 'one_parcel_foreclosure': ('MetLife', 'MAY',
   'sell the whole property as ONE parcel at a foreclosure sale',
   'which on an assemblage means the site is sold intact rather than lot by lot', 'MetLife'),
 'lender_cost_lien': ('the owner of lot 49', 'MUST',
   'repay whatever MetLife spends defending the lien, including counsel fees',
   'and those sums become a lien RANKING AHEAD of anything recorded after this mortgage', 'MetLife'),
 'possession_on_default': ('the owner of lot 49', 'MUST',
   'pay MetLife a fair monthly rent for any space it occupies after default',
   'or vacate - and can be removed by summary proceedings if it does neither', 'MetLife'),
 'repair_covenant': ('the owner of lot 49', 'MUST',
   'keep the buildings in reasonably good repair',
   'failure is an acceleration trigger in its own right', 'MetLife'),
 'violation_compliance': ('the owner of lot 49', 'MUST',
   'comply with any government order or notice of violation',
   'failing to do so accelerates the loan - so a DOB violation is not just a fine, it is a default', 'MetLife'),
 'insurance_254': ('the owner of lot 49', 'MUST',
   'carry the insurance the mortgage requires',
   'construed under Real Property Law section 254', 'MetLife'),
 'loan_agreement_controls': ('the unrecorded Loan Agreement', 'MUST',
   'govern wherever it conflicts with this mortgage',
   'except as to creating and perfecting the lien. The rate, maturity, reserves and recourse carve-outs therefore live in a document ACRIS has never seen', 'both parties, privately and off the register'),
 'lien_law_trust_fund': ('the owner of lot 49', 'MUST',
   'hold every advance as a TRUST FUND under NY Lien Law section 13',
   'spending it on the cost of the improvement before anything else', 'nobody - it is a statutory duty'),
 'binds_tenants': ('subsequent owners, lenders, TENANTS and SUBTENANTS', 'MUST',
   'take subject to this mortgage',
   'so a lease signed today is already bound by covenants agreed in 2023', 'MetLife'),
 'no_oral_modification': ('both parties', 'MUST NOT',
   'change or terminate this mortgage by conversation or conduct',
   'only a signed writing will do', 'nobody'),
 'insurability_default': ('the owner of lot 49', 'MUST',
   'keep the building insurable',
   'if two or more New York fire insurers refuse to write it, the loan accelerates - a physical-condition risk wired directly to the debt', 'MetLife'),
 'fixtures_removal_default': ('the owner of lot 49', 'MUST NOT',
   'remove, demolish or destroy fixtures, chattels or personal property',
   'unless promptly replaced with items of at least equal quality, free of chattel mortgages', 'MetLife'),
 'tax_law_change_default': ('the owner of lot 49', 'MUST',
   "accept acceleration on 30 days' notice if the law taxing mortgages changes",
   'a risk allocated to the borrower, not the lender', 'MetLife'),
 'catchall_covenant_default': ('the owner of lot 49', 'MUST',
   'keep every other covenant in the mortgage',
   'breach of ANY of them is itself an acceleration trigger', 'MetLife'),
 'no_default_rep': ('the owner of lot 49', 'MUST',
   'represent that no default exists on the existing notes and mortgages',
   'as at 2013-08-07, including any event that would become a default with time or notice. A DATED STATEMENT THAT THE LOAN WAS PERFORMING', 'nobody - it is a representation, not a promise'),
 'fee_title_rep': ('the owner of lot 49', 'MUST',
   'represent that it holds good, marketable, insurable fee title',
   'subject to Permitted Encumbrances - a list defined in the UNRECORDED Loan Agreement, so what actually burdens the title is off-register', 'nobody'),
 'authority_rep': ('the owner of lot 49', 'MUST',
   'represent that signing breaches no operating agreement, lease, mortgage or law',
   '', 'nobody'),
 'consolidation_amount': ('the existing notes', 'MUST',
   'merge into ONE debt of $40,500,000',
   'this is the consolidated position, NOT new money - the new money in this batch was $1,500,000', None),
 'consolidated_note': ('a new Consolidated, Amended and Restated Note', 'MUST',
   'replace the existing notes entirely',
   '⚠ the note itself is NOT RECORDED, so the interest rate and maturity are off-register', None),
 'collateral_easements': ("lot 49's air rights and development rights", 'MUST',
   "form part of the lender's collateral",
   'named expressly in the granting clause, along with land in the bed of any adjoining street to its centre line', 'the lender, on repayment'),
 'collateral_improvements': ('any building erected later', 'MUST',
   "become the lender's collateral automatically",
   "'now or hereafter erected' - so the tower built in 2016 was already pledged under a 2013 instrument", 'the lender, on repayment'),
 'collateral_equipment': ('equipment and furnishings, now or later acquired', 'MUST',
   'form part of the collateral under UCC Article 9',
   '⚠ CARVE-OUT: property belonging to TENANTS under leases is excluded, except to the extent the owner has an interest in it', 'the lender, on repayment'),
 'modification_by_schedule': ('Schedule C, at pages 20-52 of this instrument', 'MUST',
   'supersede and replace every prior mortgage term',
   '⚠ and it IS recorded - unlike the MetLife structure, this deal put its operative terms on the register', 'both parties, by a signed writing'),
 'emergency_definition': ("an 'Emergency Situation'", 'MUST',
   'mean one of four things, and only those four',
   "1) structural support impaired or bodily injury likely  2) substantial economic loss, or civil or criminal penalties, to either owner  3) loss of utility, elevator or other essential services  4) ingress or egress blocked. ⚠ the 2010 ZLDA used this concept UNDEFINED - nine years later the same sponsor's counsel bounded it", None),
 'zr_12_10_definitions': ("'dwelling unit', 'floor area', 'floor area ratio', 'lot coverage', 'zoning lot', 'parties in interest', 'use' and 'bulk'", 'MUST',
   'take their meanings from Zoning Resolution section 12-10',
   '⚠ the agreement defers to the ZR, so a future ZR amendment moves these definitions underneath the contract without anyone signing anything', 'the City, by amending the Zoning Resolution'),
}



# ---- slots found in the 2012 Horne instrument that the 2010 one
# ---- did not have. The menu grows as instances are read.
ZLDA_SLOTS += [
 ('bonus_rights_split', True, 'BOTH', 'ENVELOPE',
  "how are the owner's bonus rights split, and what flips the ratio?",
  "p006 section I.C — Owner Parcel Bonus Rights are pro-rated by lot area, then OWNER TAKES 80%. ⚠ the split flips to 50/50 if the bonus became available through the Developer's efforts AND not less than $10,000 in professional fees. A NAMED DOLLAR THRESHOLD THAT REALLOCATES VALUE"),
 ('lower_limiting_plane_raise', False, 'GRANTOR', 'HEIGHT',
  '⚠ can the height plane MOVE?',
  "p008 section II.A.2 — the owner may raise the Lower Limiting Plane using an 'Owner Permitted Increase', on 15 business days' notice with architectural drawings and the proposed new height; the easement is deemed raised to the minimum height that permits the work. THE CONSTRAINT IS VARIABLE"),
 ('architect_arbitration', False, 'BOTH', 'PROCESS',
  'who decides a plans dispute, and is it binding?',
  'p009 — two architects, then a jointly designated Qualified Professional (licensed, 10+ years on similar NYC buildings), AAA-appointed if no agreement in 15 days, determination in 15 days and BINDING; fees split then shifted to the loser. The owner may not file pending resolution'),
 ('anti_merger_covenant', True, 'GRANTOR', 'ENVELOPE',
  'may the burdened lot join a DIFFERENT zoning lot?',
  "p011 section II.A.5 — the owner may not merge its zoning lot with any parcel outside the combined zoning lot without the developer's prior written consent. The mirror of the assemblage right"),
 ('non_opposition_covenant', False, 'GRANTOR', 'PROCESS',
  'may the burdened owner object at a public hearing?',
  'p016 section III.D — the owner shall not voluntarily appear in opposition before the community board, CPC, DCP, DOB, City Council, BSA, HPD, LPC or any state or federal agency'),
 ('downzoning_allocation', False, 'BOTH', 'ENVELOPE',
  'what happens to rebuild rights if the area is DOWNZONED?',
  'p013 sections II.C.1-3 — three scenarios (one building, all buildings, some buildings) allocating post-downzoning rebuild rights pro rata by the Exhibit D ratio'),
 ('upzoning_allocation', False, 'BOTH', 'ENVELOPE',
  'who gets the upside of an UPZONING?',
  "p014 section II.C.4 — split as if each were a separate zoning lot; if the upzoning does not reach the owner's premises, the owner gets nothing"),
 ('residential_use_trigger', False, 'GRANTEE', 'USE',
  'does residential use on the developer parcel cost anything?',
  "p016 section III.E — if any residential use appears before the permanent CO, the developer owes the owner the 'Section 3(d) Rights' set out in a SALE AGREEMENT NOT PART OF THIS INSTRUMENT. ⚠ an off-register obligation triggered by a use decision"),
 ('estoppel_certificates', False, 'BOTH', 'PROCESS',
  'how often can a party demand a status certificate?',
  "p022 — not more than twice a year, on 20 business days' notice, at the requester's cost, no liability except for fraud"),
 ('preconstruction_survey', False, 'GRANTOR', 'ACCESS',
  "may the developer document the neighbour's condition before building?",
  "p022 section XIII.A — right to enter and document pre-existing condition on 10 days' written notice, owner's representative may accompany throughout at the developer's cost"),
 ('construction_insurance', False, 'GRANTEE', 'PROCESS',
  'what insurance must the builder carry, and rated how?',
  'p023 — ISO Form CG 00 01, owner as additional insured primary and non-contributory, occurrence basis, $5,000,000 per occurrence / $10,000,000 aggregate, defence costs OUTSIDE the limit, carrier rated A-X or better by A.M. Best'),
 ('effect_of_breach', True, 'BOTH', 'ENVELOPE',
  'does a breach un-merge the zoning lot?',
  'p024 section XVI — no. The merger survives contract failure, which protects the envelope against a dispute between the parties'),
 ('subdivision_right', False, 'GRANTEE', 'ENVELOPE',
  'may the developer subdivide without paying again?',
  "p020 section IX — the developer may subdivide 'without any additional compensation or consideration to Owner'. ⚠ THIS IS WHY THE 2019 SPLIT NEEDED NO CONSENT FROM ANY OF THE SIX SELLER LOTS"),
]

HORNE_INSTANCE = {
 'rights_conveyance': ('PRESENT', 'p008', 'conveys the Subject Development Rights; owner expressly RETAINS Retained DR, Owner Bonus DR and Owner Upzoning DR'),
 'cooperation_covenant': ('PRESENT', 'p015', "RECIPROCAL — runs to whichever party is the Requesting Party, at that party's sole cost including the other's attorneys' fees; 10 business days"),
 'light_air_view_easement': ('PRESENT', 'p008', '⚠ A DIFFERENT SHAPE FROM 2010: an elevation-defined horizontal plane at 155.24 ft above Manhattan Topographic Bureau datum, over the whole 25 ft x 114 ft 6 in lot. VIEW included. ⚠ AND THE PLANE CAN BE RAISED'),
 'existing_building_carveout': ('ABSENT', 'p008', 'no carve-out, and none needed — the easement begins ABOVE the existing roof. The only recognition of existing structures is for rooftop mechanicals, and only if the plane is later raised'),
 'repair_carveout': ('ABSENT', 'p008', "⚠ UNLIKE 2010 — no clause exempts repairs from the encroachment bar. 'Rebuilding' is defined to INCLUDE reconstruction and replacement and is prohibited on the same terms as an Alteration"),
 'confirming_instrument': ('PRESENT', 'p008', '20 business days; Exhibit G form or such alternative as DOB requires; Developer records at its sole expense'),
 'alteration_restriction': ('PRESENT', 'p008', '⚠ FIVE prohibited effects, one more than 2010'),
 'plan_review_right': ('PRESENT', 'p009', '⚠ 5 business days, NOT the 10 of 2010 — plus a 5-day objection window and binding architect arbitration'),
 'violation_covenant': ('PRESENT', 'p010', 'reciprocal — lot 49 owes the same covenant back at section II.B.2'),
 'cure_period': ('PRESENT', 'p010', '30 days to commence, reciprocal'),
 'self_help_license': ('PRESENT', 'p010', 'entry licence with four conditions; reimbursement at CITIBANK PRIME COMPOUNDED MONTHLY; general entry notice 10 days'),
 'injunctive_relief': ('PRESENT', 'p024', 'specific performance expressly reserved, with NO CONSEQUENTIAL DAMAGES'),
 'runs_with_land': ('PRESENT', 'p023', 'four-part binding clause; also binds future acquirers to FUTURE modifications they never signed'),
 'dob_consent_to_amend': ('PRESENT', 'p048', '⚠ ONLY IN THE EXHIBIT G FORM, which is unexecuted. The ZLDA itself is amended by the parties alone with no agency consent'),
 'co_recording_covenant': ('PRESENT', 'p048', '⚠ also only in the Exhibit G form'),
 'unit_cap': ('ABSENT', 'p016', "no dwelling-unit cap anywhere in the body. Residential use is a MONEY trigger instead: if residential use appears before the permanent CO, lot 49 owes lot 23 the 'Section 3(d) Rights' under a Sale Agreement that is NOT part of this instrument"),
}

HORNE_DEONTIC = {
 'rights_conveyance': ('lot 23 (the Horne co-op)', 'MUST', 'convey its Subject Development Rights to lot 49', 'but keeps its Retained, Bonus and Upzoning rights - it did not sell everything', None),
 'cooperation_covenant': ('either party', 'MUST', 'cooperate with whichever one is Requesting', "at the Requesting Party's sole cost including the other side's reasonable attorneys' fees; documents produced within 10 business days, and after a further 5 days' notice the requester may file in the other's name", 'the requesting party'),
 'light_air_view_easement': ('lot 23 (the Horne co-op)', 'MUST NOT', 'let anything rise above 155.24 ft above the Manhattan datum, across its whole 25 x 114\'6" lot', "a perpetual easement of light, air AND VIEW. ⚠ THE HEIGHT IS NOT FIXED - the owner may RAISE the plane whenever it acquires Bonus or Upzoning rights and uses them to add floor area, on 15 business days' notice with drawings. Anyone treating 155.24 as a permanent ceiling will be wrong after the first increase", 'lot 49, as benefited owner'),
 'confirming_instrument': ('lot 23', 'MUST', 'sign a separate recordable easement when lot 49 asks', 'within 20 business days, on the Exhibit G form or whatever DOB requires; lot 49 records it at its own cost', 'lot 49'),
 'alteration_restriction': ('lot 23', 'MUST NOT', 'build, alter or rebuild if the work would', "(a) COMMENCE BEFORE the first temporary CO for the entire lot 49 building - a timing bar 2010 did not have  (b) encroach above the Lower Limiting Plane as it may be raised  (c) create or worsen a non-compliance delaying lot 49's permit or CO  (d) use any rights other than its Retained, Bonus or Upzoning rights  (e) change use, or amend its CO, so as to reduce lot 49's rights", 'lot 49'),
 'plan_review_right': ('lot 23', 'MUST', 'give lot 49 the complete DOB application and all plans 5 business days before filing', "lot 49 then has 5 business days to object; silence is a CONCLUSIVE WAIVER, time being of the essence. A dispute goes to a jointly chosen architect of 10+ years' NYC experience, AAA-appointed if they cannot agree in 15 days, whose determination BINDS; the loser pays", 'lot 49, by not objecting'),
 'violation_covenant': ('lot 23', 'MUST NOT', 'create or permit a violation of the Zoning Resolution, building code or fire code', 'that would delay a permit or CO for ANY building on the combined zoning lot, or create or increase a non-conforming use. ⚠ lot 49 owes the identical covenant back', 'lot 49'),
 'cure_period': ('lot 23', 'MUST', 'begin curing within 30 days of notice', 'then proceed diligently with commercially reasonable efforts. Lot 49 owes the same', 'lot 49'),
 'self_help_license': ('lot 49', 'MAY', "enter lot 23 and cure at lot 23's expense", "only after notice, at reasonable times except in an Emergency, without unreasonable interference, protecting the owner's property, and carrying insurance naming lot 23 AND any mortgagee it knows of. Repayment carries interest at Citibank prime compounded monthly; lot 23 keeps the right to contest both the violation and the spend", 'lot 23, by curing first'),
 'injunctive_relief': ('either party', 'MAY', 'seek injunctive relief and specific performance', "but NOT consequential damages; and recovery is limited to that party's interest in the combined zoning lot - no personal liability for partners, officers, directors or shareholders", None),
 'runs_with_land': ('every party with any interest, and their successors', 'MUST', 'take subject to this agreement', '⚠ and section X binds future acquirers to future MODIFICATIONS they never executed', 'all parties in interest'),
 'dob_consent_to_amend': ('both parties', 'MUST NOT', 'modify, amend or terminate the CONFIRMING easement without DOB consent', "⚠ but this lives in the unexecuted Exhibit G form. The ZLDA itself (section XXI) needs only the parties' signatures - no agency at all", 'NYC Department of Buildings, once the form is executed'),
 'co_recording_covenant': ('the owner of either parcel', 'MUST', 'put the CRFN on every future CO and in any deed', '⚠ contingent - this sits in the unexecuted Exhibit G form', 'DOB'),
}



BF_INSTANCE = {
 'rights_conveyance': ('PRESENT', 'p008', 'conveys Excess DR + Owner Parcel Bonus DR; owner retains ONLY the Retained DR utilised by its existing building, plus a mechanical-equipment right'),
 'light_air_view_easement': ('PRESENT', 'p007', '⚠ FIXED elevation plane at 130 ft above Manhattan Topographical Bureau datum (2.75 ft above USC&GS mean sea level, Sandy Hook), coincident with the WHOLE lot 22 boundary. Perpetual. VIEW INCLUDED. NO raise mechanism'),
 'existing_building_carveout': ('PRESENT', 'p008', 'may retain, add and replace rooftop MECHANICALS above the present roof - but no mechanical may exceed the plane or use the conveyed rights'),
 'repair_carveout': ('PRESENT', 'p008', "repairs are not a prohibited Alteration, but triple-conditioned and the right EXPIRES at lot 49's first full TCO"),
 'confirming_instrument': ('PRESENT', 'p008', '20 business days; Exhibit F form or whatever DOB requires; developer records at its sole expense'),
 'alteration_restriction': ('PRESENT', 'p008', 'FIVE prohibited effects, and (a) is a TIMING bar with a four-year outside date'),
 'plan_review_right': ('PRESENT', 'p009', '⚠ NO WAITING PERIOD AT ALL - the single largest concession the owner won across the three instruments'),
 'violation_covenant': ('PRESENT', 'p009', 'reciprocal - lot 49 owes the identical covenant'),
 'cure_period': ('PRESENT', 'p009', '30 days to commence, both directions'),
 'self_help_license': ('PRESENT', 'p009', "entry and cure; interest at CITIBANK PRIME COMPOUNDED MONTHLY; entry under the easements needs 5 days' notice"),
 'injunctive_relief': ('PRESENT', 'p020', 'specific performance yes; ⚠ NO consequential-damages bar - instead a NON-RECOURSE cap'),
 'dob_consent_to_amend': ('ABSENT', 'p022', "⚠ NOT IN THE BODY. Section XXI names only 'all of the parties hereto'. The DOB-consent language exists ONLY in the unexecuted Exhibit G form"),
 'runs_with_land': ('PRESENT', 'p020', 'runs with the land; enforceable by a mortgagee-assignee after default; ⚠ future acquirers bound to FUTURE modifications they never signed'),
 'unit_cap': ('ABSENT', 'p004', 'no dwelling-unit limit anywhere in the body'),
 'co_recording_covenant': ('ABSENT', 'p013', "no CRFN-on-CO requirement. Nearest analogue: lot 22 must amend its CO to note the combined zoning lot, at lot 49's cost - or accept a DOB file notation if it has no CO"),
 'bonus_rights_split': ('ABSENT', 'p007', '⚠ NO SPLIT. All bonus rights are folded into the conveyance; lot 49 takes 100%. Compare lot 23, which kept 80% and could reach 50/50'),
 'anti_merger_covenant': ('PRESENT', 'p010', 'may not merge with any parcel outside the combined zoning lot'),
 'non_opposition_covenant': ('PRESENT', 'p014', '⚠ TIME-STAGGERED, NOT RECIPROCAL'),
 'downzoning_allocation': ('PRESENT', 'p011', 'three scenarios: one building, all buildings, some buildings'),
 'upzoning_allocation': ('PRESENT', 'p012', '⚠ EACH KEEPS ITS OWN UPSIDE - SUBJECT TO A DEVELOPER CALL OPTION AT THE ORIGINAL PRICE'),
 'subdivision_right': ('PRESENT', 'p016', '⚠ ONE-WAY. Lot 49 may subdivide without consent; lot 22 may not subdivide at all'),
 'estoppel_certificates': ('PRESENT', 'p018', "twice a year maximum, 20 business days' notice, no liability except fraud"),
 'preconstruction_survey': ('PRESENT', 'p018', 'entry onto the land AND into the building'),
 'construction_insurance': ('PRESENT', 'p019', '⚠ $1,000,000 per occurrence / $2,000,000 aggregate / $10,000,000 umbrella - and NO carrier-rating requirement'),
 'effect_of_breach': ('PRESENT', 'p020', 'a breach does NOT un-merge the zoning lot'),
 'architect_arbitration': ('ABSENT', 'p016', '⚠ no arbitration of any kind. The only architect is a one-way opinion letter lot 49 must buy before subdividing'),
 'residential_use_trigger': ('ABSENT', 'p004', "no payment triggered by residential use on lot 49 - unlike the Horne instrument's Section 3(d) Rights"),
}

BF_DEONTIC = {
 'rights_conveyance': ('lot 22 (Brick Farms co-op)', 'MUST', 'convey its Subject Development Rights to lot 49', '= its excess rights PLUS all its bonus rights. It keeps only what its existing building already uses', None),
 'light_air_view_easement': ('lot 22', 'MUST NOT', 'let anything rise above 130 ft above the Manhattan datum, anywhere on its lot', "a perpetual easement of light, air AND VIEW. ⚠ Unlike lot 23's plane, this one is FIXED - the body contains no mechanism to raise it", 'lot 49, as benefited owner'),
 'existing_building_carveout': ('lot 22', 'MAY', 'keep, add and replace rooftop mechanical equipment - HVAC, bulkheads', 'above the present roof height, but NOTHING may exceed the 130 ft plane or use any of the conveyed development rights', 'lot 49'),
 'repair_carveout': ('lot 22', 'MAY', 'repair and maintain its building', "provided the work does not change the use, does not change the floor area, and does not change the envelope or air space the building occupies today. ⚠ the right EXPIRES at lot 49's first full TCO", 'lot 49'),
 'confirming_instrument': ('lot 22', 'MUST', 'sign a recordable confirming easement when lot 49 asks', 'within 20 business days, on the annexed form or any alternative DOB requires; lot 49 records it at its own cost', 'lot 49'),
 'alteration_restriction': ('lot 22', 'MUST NOT', 'build, alter or rebuild if the work would', "(a) COMMENCE before lot 49's first full TCO or four years from 2013-05-17, WHICHEVER IS SOONER  (b) rise above the 130 ft plane  (c) create or worsen a non-compliance delaying lot 49's permit or CO  (d) use any rights beyond its Retained DR  (e) change use, or amend its CO, so as to reduce lot 49's rights. ⚠ lot 49's mirror covenant has only TWO effects - a sharp asymmetry", 'lot 49'),
 'plan_review_right': ('lot 22', 'MUST', 'give lot 49 a copy of any DOB application and plans', "⚠ 'prior to submitting', with NO stated number of days, NO objection window and NO arbitration - solely so lot 49 can verify compliance. Compare 2010's ten business days and 2012's five days plus a binding architect determination. Separately, zoning analyses must be exchanged within 10 days AFTER filing", 'lot 49'),
 'violation_covenant': ('lot 22', 'MUST NOT', 'create or permit a violation of the Zoning Resolution, building code or fire code', 'that would delay a permit or CO for ANY building on the combined zoning lot, or create or increase a non-conformity. Lot 49 is bound identically', 'lot 49'),
 'cure_period': ('lot 22', 'MUST', 'begin curing within 30 days of notice', 'then proceed diligently and continuously. Reciprocal', 'lot 49'),
 'self_help_license': ('lot 49', 'MAY', "enter lot 22 and cure at lot 22's expense", 'after notice, at reasonable times except an emergency it reasonably determines, without unreasonable interference, carrying insurance naming lot 22 and any mortgagee it knows of. Repayment carries Citibank prime compounded monthly; lot 22 expressly keeps the right to CONTEST both the violation and the spend', 'lot 22, by curing first'),
 'injunctive_relief': ('either party', 'MAY', 'seek injunctive relief and specific performance', "⚠ but recovery runs SOLELY to that party's interest in the combined zoning lot, including rental insurance, condemnation and sales proceeds. No personal liability for partners, officers, directors or shareholders", None),
 'dob_consent_to_amend': ('both parties', 'MAY', 'amend or terminate this agreement by themselves', '⚠ no agency consent is required by the AGREEMENT. The DOB-consent clause lives only in the unexecuted Exhibit G form, so it binds nothing until that form is signed', 'lot 22 and lot 49, alone'),
 'runs_with_land': ('everyone acquiring any interest, now or later', 'MUST', 'take subject to this agreement AND to future modifications of it', "⚠ 'without having executed such future modifications, to the same extent that it would have been had it been a signatory'", 'all parties in interest'),
 'anti_merger_covenant': ('lot 22', 'MUST NOT', 'merge its zoning lot with any parcel not already in the combined zoning lot', "without lot 49's prior written consent", 'lot 49'),
 'non_opposition_covenant': ('lot 22', 'MUST NOT', 'voluntarily appear in opposition to lot 49 at any public body', "community board, CPC, DCP, DOB, City Council, BSA, HPD, LPC or any city, state or federal agency - immediately and indefinitely. ⚠ lot 49's mirror obligation does not begin until the sooner of its first full TCO or four years", 'lot 49'),
 'downzoning_allocation': ('both parcels', 'MUST', 'share post-downzoning rebuild rights pro rata', "one casualty - rebuild limited to that parcel's own allocation and may not reduce the others'. All buildings - pro rata per Exhibit D. Some - pro rata among the affected only, after backing out surviving buildings", None),
 'upzoning_allocation': ('lot 49', 'MAY', "BUY lot 22's upzoning upside at the same price per square foot it paid in 2013", "⚠ $135.19/sf, exercisable within 90 days of final 197-c/197-d approval, so long as it acts before its first full TCO. Lot 22's 'retained upside' is retrospectively priced at the 2013 number", 'lot 49, by not exercising'),
 'subdivision_right': ('lot 49', 'MAY', "subdivide the combined zoning lot without lot 22's consent", "and without further payment, provided it first gives lot 22 the application and a NY-licensed architect's opinion that the subdivision will not diminish lot 22's rights. ⚠ LOT 22 HAS NO SUBDIVISION RIGHT AT ALL. This is why the 2019 split needed nobody's consent", None),
 'estoppel_certificates': ('either party', 'MUST', 'furnish a status certificate on request', "not more than twice a year, on 20 business days' notice, at the requester's cost. ⚠ no liability even for negligent or inadvertent non-disclosure - only fraud", None),
 'preconstruction_survey': ('lot 22', 'MUST', 'let lot 49 survey its building before construction', 'entry onto the land and INTO the building, scheduled in consultation, normal business hours, contractor insured', 'lot 49'),
 'construction_insurance': ('lot 49', 'MUST', 'carry construction liability insurance', "$1M per occurrence, $2M aggregate, $10M umbrella, occurrence basis, naming lot 22 AND all its mortgagees as additional insureds, non-cancelable without notice. ⚠ NO A.M. Best rating required - compare the Horne instrument's A-X requirement", 'lot 22'),
 'effect_of_breach': ('the zoning lot merger', 'MUST', 'survive any breach of this agreement', 'the combined zoning lot stays one zoning lot unless and until formally subdivided - the envelope is protected from a contract dispute', None),
}



DECL_INSTANCE = {
 ('2013080901116001', 'zoning_lot_declared'): ('PRESENT', 'p003', 'Block 800 lots 20, 21, 22, 23, 49, 53, 55 and 56 declared ONE zoning lot', ('the eight lots', 'MUST', 'be treated as ONE zoning lot', "'Said lots are located within a single block and are hereby declared to be a tract of land to be treated as one zoning lot for the purposes of the Resolution'", 'only subdivision under the Zoning Resolution')),
 ('2013080901116001', 'single_signature_by_pre_consent'): ('PRESENT', 'p006', '⚠ ONE SIGNATURE, SEVEN OTHER OWNERS STILL IN PLACE', ('the six other fee owners and their mortgagees', 'MUST', 'be bound WITHOUT SIGNING', "⚠ 'shall be effective as to [them] without their signatures hereto, by reason of their prior consent to a declaration merging the several zoning lots'. Control was assembled by ADVANCE WAIVER, not ownership - the opposite of what a single declarant appears to mean", 'nobody - the consents were given irrevocably in earlier instruments')),
 ('2013080901116001', 'anti_severance'): ('PRESENT', 'p006', 'a breach cannot un-merge the zoning lot', ('any party', 'MUST NOT', 'achieve separate zoning-lot treatment by breach', "'the Property shall be treated as one zoning lot unless such zoning lot is subdivided in accordance with the provisions of the Resolution'", "⚠ NOBODY - only the Zoning Resolution's own subdivision procedure")),
 ('2013080901116001', 'no_amendment_mechanism'): ('ABSENT', 'p004', '⚠ NO amendment, termination, expiration or release clause anywhere in the instrument. Once recorded it can only be unwound by ZR subdivision', ('the parties', 'MAY NOT', 'amend, terminate or release this declaration', '⚠ there is no mechanism. Compare the 2020 environmental covenant, which DOES give an agency power to terminate on petition', 'nobody')),
 ('2013080901116001', 'dob_consent'): ('ABSENT', 'p004', '⚠ no agency is a party. DOB, City Planning and BSA appear nowhere in 27 pages; the only public office named is the City Register', None),
 ('2013080901116001', 'co_recording_covenant'): ('ABSENT', 'p004', "'certificate of occupancy' appears nowhere in the document", None),
 ('2013080901116001', 'floor_area_allocated'): ('ABSENT', 'p004', '⚠ NO square-foot figure, FAR or percentage anywhere. A zoning-lot declaration MERGES; it does not allocate. The quantities live in the ZLDAs', None),
 ('2013052101674003', 'future_declaration_waiver'): ('PRESENT', 'p004', '⚠ THE KEYSTONE CLAUSE — the owner waives its right to sign anything later', ('lot 22 (Brick Farms)', 'MUST', 'be deemed to have consented to every FUTURE enlargement declaration', "⚠ 'be deemed automatically and without any further action on its part to have consented to and waived its right to execute an amended or replacement Declaration regardless of whether Owner executes such amended or replacement Declaration'. This is why August 2013 needed one signature", 'lot 49 alone holds the benefit')),
 ('2013052101674003', 'confirming_documents_10bd'): ('PRESENT', 'p004', '10 business days to execute confirming instruments on request', ('lot 22', 'MUST', "execute whatever confirms a new parcel's incorporation", 'within 10 business days of a request with copies of the documents', 'lot 49')),
 ('2013052101674007', 'future_declaration_waiver'): ('PRESENT', 'p005', 'the identical keystone waiver, binding lot 21', ('lot 21 (133 West 24th Street Corp)', 'MUST', 'be deemed to have consented to every FUTURE enlargement declaration', 'same automatic-consent-and-waiver formula as lot 22', 'lot 49')),
 ('2020061600455001', 'environmental_use_restriction'): ('PRESENT', 'p002', '⚠ NOT A ZONING INSTRUMENT — an OER cleanup covenant', ('the owner of lot 49', 'MUST NOT', 'exceed restricted commercial use, plant vegetable gardens, farm, or use untreated groundwater', 'without the prior written approval of the NYC Office of Environmental Remediation. Arises from a Voluntary Cleanup Agreement dated 2016-02-10', 'the NYC Office of Environmental Remediation')),
 ('2020061600455001', 'engineering_controls'): ('PRESENT', 'p003', 'engineering controls must be operated and maintained per the Site Management Plan', ('the owner of lot 49', 'MUST', 'operate and maintain the engineering controls specified in the Site Management Plan', "⚠ they 'may not be discontinued or modified without an amendment of the SMP or the termination of this Declaration approved by the Office'. The SMP itself is an UNRECORDED document", 'the NYC Office of Environmental Remediation')),
 ('2020061600455001', 'deed_recital_required'): ('PRESENT', 'p003', 'every future deed must recite that it is subject to this declaration', ('any seller of lot 49', 'MUST', 'recite in the deed that the conveyance is subject to this declaration and the Site Management Plan', 'unless the agency has consented to termination. ⚠ a RECITAL, not a CRFN - so it will not be found by a cross-reference search', 'the Relevant Agency, by consenting to termination')),
 ('2020061600455001', 'agency_termination'): ('PRESENT', 'p003', '⚠ the ONLY one of the four with a real termination mechanism', ('any owner of lot 49', 'MAY', 'petition the agency to modify or terminate this declaration', "on not less than 30 days' written notice to every owner of record, provided human health and the environment stay protected", 'the NYC Office of Environmental Remediation or its successor')),
 ('2020061600455001', 'e_designation'): ('PRESENT', 'p009', 'the site is registered by DOB as an E-DESIGNATED property', ('lot 49', 'MUST', 'remain subject to E-designation registration at DOB', '⚠ an environmental designation that constrains what may be built and how - and it is a DOB record, so the DOB lane can corroborate it', 'the agency, on completion of remediation')),
}


def _d(slot):
    """The deontic sentence for a slot, or explicit nulls saying we lack it."""
    d = DEONTIC.get(slot)
    if not d:
        return dict(actor=None, modality=None, action=None, object=None,
                    consent_of=None)
    return dict(actor=d[0], modality=d[1], action=d[2], object=d[3],
                consent_of=d[4])


def main():
    slots = [dict(doc_type="ZLDA", slot=s, typical=t, burdens=b, dimension=d,
                  what_varies=v, note=n)
             for s, t, b, d, v, n in ZLDA_SLOTS]
    slots += [dict(doc_type="MTGE", slot=s, typical=t, burdens=b, dimension=d,
                   what_varies=v, note=n) for s, t, b, d, v, n in MTGE_SLOTS]
    slots += [dict(doc_type="ZLDA-SPLIT", slot=s, typical=t, burdens=b,
                   dimension=d, what_varies=v, note=n)
              for s, t, b, d, v, n in SPLIT_SLOTS]
    slots += [dict(doc_type="AGMT/CEMA", slot=s, typical=t, burdens=b,
                   dimension=d, what_varies=v, note=n)
              for s, t, b, d, v, n in CEMA_SLOTS]
    inst = [dict(document_id="2010102601040006", effective="2010-10-14", slot=s,
                 status=v[0], page=v[1], value_text=v[2], burdened_bbl=v[3],
                 verbatim=v[4], **_d(s)) for s, v in INSTANCE_2010.items()]
    inst += [dict(document_id="2023110100486009", effective="2023-10-16", slot=s,
                  status=v[0], page=v[1], value_text=v[2],
                  burdened_bbl="1008000049",
                  verbatim=dict((x[0], x[5]) for x in MTGE_SLOTS)[s],
                  **_d(s)) for s, v in MTGE_INSTANCE.items()]
    inst += [dict(document_id="2013081200922003", effective="2013-08-07", slot=s,
                  status=v[0], page=v[1], value_text=v[2],
                  burdened_bbl="1008000049",
                  verbatim=dict((x[0], x[5]) for x in CEMA_SLOTS)[s],
                  **_d(s)) for s, v in CEMA_INSTANCE.items()]
    def _hd(s):
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
    def _bf(s):
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
    for (doc, slot), (st, pg, val, deo) in DECL_INSTANCE.items():
        d = deo or (None, None, None, None, None)
        inst.append(dict(document_id=doc, effective=None, slot=slot, status=st,
                         page=pg, value_text=val, burdened_bbl="1008000049",
                         verbatim=val, actor=d[0], modality=d[1], action=d[2],
                         object=d[3], consent_of=d[4]))
    inst += [dict(document_id="2019071700601003", effective="2019-05-20", slot=s,
                  status=v[0], page=v[1], value_text=v[2],
                  burdened_bbl="1008000049",
                  verbatim=dict((x[0], x[5]) for x in SPLIT_SLOTS)[s],
                  **_d(s)) for s, v in SPLIT_INSTANCE.items()]

    print(f"ZLDA TERM MENU — {len(slots)} slots codified from the type\n")
    for s in slots:
        mark = "·" if s["typical"] else "○"
        print(f"  {mark} {s['slot']:<28} {s['dimension'] or '':<8} "
              f"{s['what_varies'][:56]}")
    print("\n  · typical (expect it)   ○ negotiated (check for it)")

    p = sum(1 for i in inst if i["status"] == "PRESENT")
    a = sum(1 for i in inst if i["status"] == "ABSENT")
    n = sum(1 for i in inst if i["status"] == "NOT_LOOKED")
    print(f"\n2010102601040006 against the menu: {p} PRESENT · {a} ABSENT · "
          f"{n} NOT_LOOKED  ({100*(p+a)/len(inst):.0f}% examined)")

    print("\n⚠ CORRECTIONS THIS READING FORCED ON DATA ALREADY WRITTEN:\n")
    print("  1. light_air_view_easement is 'light, air AND VIEW' —")
    print("     recorded as 'light and air'. View is a separate interest.")
    print("  2. the band runs from the REAR LOT LINE, 20 ft NORTH —")
    print("     recorded as 'from the lot line shared with lot 49'.")
    print("     On a through-block assemblage those are different lines.")
    print("  3. ⚠ ONLY THE 120 OWNER (LOT 53) GRANTS IT.")
    print("     acris_constraints said 'applies to lots 53, 55 and 56 alike'.")
    print("     Lots 55 and 56 sold rights and granted NO easement — their")
    print("     height constraint was INVENTED. It must be retracted.")
    print("\n  All three came from reading the CHART and not the COVENANTS.")
    print("  The chart gives quantities. Only the body gives terms.")

    for name, data in (("doctype_term_slots", slots),
                       ("doctype_term_instance", inst)):
        fp = HERE / f"{name}.csv"
        with open(fp, "w", newline="", encoding="utf-8") as f:
            # fieldnames must be the UNION across rows, not the first row's
            # keys. Rows from different menus carry different fields, and
            # taking the first row silently drops every column the later ones
            # added — which is how the deontic fields vanished on first write.
            fn = []
            for r in data:
                for k in r:
                    if k not in fn:
                        fn.append(k)
            w = csv.DictWriter(f, fieldnames=fn, restval="")
            w.writeheader(); w.writerows(data)
        print(f"\n  wrote {fp.name} ({len(data)} rows)")


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL); sys.exit(0)
    main()
