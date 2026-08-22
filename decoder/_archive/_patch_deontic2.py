"""Write the remaining 25 slot sentences.

Each is WHO / MUST or MAY / WHAT / the detail / who can release it — the same
grammar as the first 24. Where a clause binds nobody (a definition, a
representation) the actor is the thing itself and the modality says so, because
"this slot has no sentence" and "this slot's sentence is unusual" must not look
alike.
"""
import pathlib

MORE = {
 # ---- MetLife mortgage, 2023110100486009 ------------------------------
 "one_parcel_foreclosure": ("MetLife", "MAY",
   "sell the whole property as ONE parcel at a foreclosure sale",
   "which on an assemblage means the site is sold intact rather than lot by lot",
   "MetLife"),
 "lender_cost_lien": ("the owner of lot 49", "MUST",
   "repay whatever MetLife spends defending the lien, including counsel fees",
   "and those sums become a lien RANKING AHEAD of anything recorded after this mortgage",
   "MetLife"),
 "possession_on_default": ("the owner of lot 49", "MUST",
   "pay MetLife a fair monthly rent for any space it occupies after default",
   "or vacate - and can be removed by summary proceedings if it does neither",
   "MetLife"),
 "repair_covenant": ("the owner of lot 49", "MUST",
   "keep the buildings in reasonably good repair",
   "failure is an acceleration trigger in its own right", "MetLife"),
 "violation_compliance": ("the owner of lot 49", "MUST",
   "comply with any government order or notice of violation",
   "failing to do so accelerates the loan - so a DOB violation is not just a fine, it is a default",
   "MetLife"),
 "insurance_254": ("the owner of lot 49", "MUST",
   "carry the insurance the mortgage requires",
   "construed under Real Property Law section 254", "MetLife"),
 "loan_agreement_controls": ("the unrecorded Loan Agreement", "MUST",
   "govern wherever it conflicts with this mortgage",
   "except as to creating and perfecting the lien. The rate, maturity, reserves and recourse carve-outs therefore live in a document ACRIS has never seen",
   "both parties, privately and off the register"),
 "lien_law_trust_fund": ("the owner of lot 49", "MUST",
   "hold every advance as a TRUST FUND under NY Lien Law section 13",
   "spending it on the cost of the improvement before anything else",
   "nobody - it is a statutory duty"),
 "binds_tenants": ("subsequent owners, lenders, TENANTS and SUBTENANTS", "MUST",
   "take subject to this mortgage",
   "so a lease signed today is already bound by covenants agreed in 2023",
   "MetLife"),
 "no_oral_modification": ("both parties", "MUST NOT",
   "change or terminate this mortgage by conversation or conduct",
   "only a signed writing will do", "nobody"),
 "insurability_default": ("the owner of lot 49", "MUST",
   "keep the building insurable",
   "if two or more New York fire insurers refuse to write it, the loan accelerates - a physical-condition risk wired directly to the debt",
   "MetLife"),
 "fixtures_removal_default": ("the owner of lot 49", "MUST NOT",
   "remove, demolish or destroy fixtures, chattels or personal property",
   "unless promptly replaced with items of at least equal quality, free of chattel mortgages",
   "MetLife"),
 "tax_law_change_default": ("the owner of lot 49", "MUST",
   "accept acceleration on 30 days' notice if the law taxing mortgages changes",
   "a risk allocated to the borrower, not the lender", "MetLife"),
 "catchall_covenant_default": ("the owner of lot 49", "MUST",
   "keep every other covenant in the mortgage",
   "breach of ANY of them is itself an acceleration trigger", "MetLife"),

 # ---- Goldman CEMA, 2013081200922003 ----------------------------------
 "no_default_rep": ("the owner of lot 49", "MUST",
   "represent that no default exists on the existing notes and mortgages",
   "as at 2013-08-07, including any event that would become a default with time or notice. A DATED STATEMENT THAT THE LOAN WAS PERFORMING",
   "nobody - it is a representation, not a promise"),
 "fee_title_rep": ("the owner of lot 49", "MUST",
   "represent that it holds good, marketable, insurable fee title",
   "subject to Permitted Encumbrances - a list defined in the UNRECORDED Loan Agreement, so what actually burdens the title is off-register",
   "nobody"),
 "authority_rep": ("the owner of lot 49", "MUST",
   "represent that signing breaches no operating agreement, lease, mortgage or law",
   "", "nobody"),
 "consolidation_amount": ("the existing notes", "MUST",
   "merge into ONE debt of $40,500,000",
   "this is the consolidated position, NOT new money - the new money in this batch was $1,500,000",
   None),
 "consolidated_note": ("a new Consolidated, Amended and Restated Note", "MUST",
   "replace the existing notes entirely",
   "⚠ the note itself is NOT RECORDED, so the interest rate and maturity are off-register",
   None),
 "collateral_easements": ("lot 49's air rights and development rights", "MUST",
   "form part of the lender's collateral",
   "named expressly in the granting clause, along with land in the bed of any adjoining street to its centre line",
   "the lender, on repayment"),
 "collateral_improvements": ("any building erected later", "MUST",
   "become the lender's collateral automatically",
   "'now or hereafter erected' - so the tower built in 2016 was already pledged under a 2013 instrument",
   "the lender, on repayment"),
 "collateral_equipment": ("equipment and furnishings, now or later acquired",
   "MUST", "form part of the collateral under UCC Article 9",
   "⚠ CARVE-OUT: property belonging to TENANTS under leases is excluded, except to the extent the owner has an interest in it",
   "the lender, on repayment"),
 "modification_by_schedule": ("Schedule C, at pages 20-52 of this instrument",
   "MUST", "supersede and replace every prior mortgage term",
   "⚠ and it IS recorded - unlike the MetLife structure, this deal put its operative terms on the register",
   "both parties, by a signed writing"),

 # ---- 2019 split, 2019071700601003 ------------------------------------
 "emergency_definition": ("an 'Emergency Situation'", "MUST",
   "mean one of four things, and only those four",
   "1) structural support impaired or bodily injury likely  2) substantial economic loss, or civil or criminal penalties, to either owner  3) loss of utility, elevator or other essential services  4) ingress or egress blocked. ⚠ the 2010 ZLDA used this concept UNDEFINED - nine years later the same sponsor's counsel bounded it",
   None),
 "zr_12_10_definitions": ("'dwelling unit', 'floor area', 'floor area ratio', "
   "'lot coverage', 'zoning lot', 'parties in interest', 'use' and 'bulk'",
   "MUST", "take their meanings from Zoning Resolution section 12-10",
   "⚠ the agreement defers to the ZR, so a future ZR amendment moves these definitions underneath the contract without anyone signing anything",
   "the City, by amending the Zoning Resolution"),
}

p = pathlib.Path("doctype_terms.py")
t = p.read_text(encoding="utf-8")
anchor = "}\n\n\ndef _d(slot):"
assert anchor in t, "DEONTIC block not found"
lines = []
for k, (a, m, ac, o, c) in MORE.items():
    lines.append(" %r: (%r, %r,\n   %r,\n   %r, %r)," % (k, a, m, ac, o, c))
t = t.replace(anchor, "\n".join(lines) + "\n" + anchor)
p.write_text(t, encoding="utf-8")
print(f"added {len(MORE)} sentences")
