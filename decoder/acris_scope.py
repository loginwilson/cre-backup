"""WHAT ACRIS IS THE AUTHORITY FOR — and what it hands off.

⚠ THE FRAMING ERROR THIS FIXES. I built a completeness test whose denominator
included "what does the hotel earn" and "when was it built, to what plan".
ACRIS does not know those things and never will. Scoring the ACRIS decode
against them made a finished decode read as 80% — a number that would send
someone back to re-read pages that could not possibly contain the answer.

⚠ AND THE SECOND, WORSE HALF OF THE SAME ERROR: I logged "the interest rate
is not in ACRIS" as an OPEN item. It is not open. It is a COMPLETE ANSWER.
ACRIS's job on that question is to tell you, with evidence, that six
generations of lender deliberately kept the rate off the register — and it
does, across 1990, 2007, 2012, 2013, 2014, 2023 and 2025. A decoder that can
prove a fact is absent has answered the question. NOT RECORDED IS A FINDING.

So there are three verdicts, not two:

  ANSWERED      ACRIS is the authority and the corpus answers it
  NOT-RECORDED  ACRIS is the authority and the answer is "no such record",
                proven across enough instruments to be a finding rather
                than a gap
  MISSING       ACRIS IS the authority, the instrument SHOULD be in ACRIS,
                and I do not hold it. ⚠ THIS IS THE ONLY REAL FAILURE.

Anything else belongs to another decoder and is a HANDOFF, not a gap.
"""

ANSWERED, NOT_RECORDED, MISSING = "ANSWERED", "NOT-RECORDED", "MISSING"

# ---------------------------------------------------------------------------
# ACRIS IS THE AUTHORITY FOR THESE. Nothing else belongs in the denominator.
# ---------------------------------------------------------------------------
SCOPE = {
"TITLE": [
 ("the ownership chain", ANSWERED,
  "112 West 25 Realty Corp -> 112 West 25 Company (1971 round trip) -> "
  "Edelman Family LP (1998) -> 112-118 West 25th LLC (2007, $42,700,000) -> "
  "Lam Gen 25 LLC -> Chelsea 25 Hotel LLC"),
 ("how Chelsea 25 Hotel LLC took the fee", ANSWERED,
  "BY AN 'OWNER AGREEMENT DATED OCTOBER 16, 2023', not a deed — which is "
  "why no deed was ever found. Recital F of the Second A&R Memorandum of "
  "Right of First Refusal: the parties execute it 'to document FRANCHISEE'S "
  "TRANSFER OF ITS FEE OWNERSHIP OF THE REAL PROPERTY TO OWNER'. ⚠ It was "
  "hiding in a document ACRIS types SUNDRY MISCELLANEOUS. The Owner "
  "Agreement itself is not recorded"),
 ("the estate structure today", ANSWERED,
  "fee in Chelsea 25 Hotel LLC, operating lease in Lam Gen 25 LLC — the "
  "propco/opco hotel split, recited in the 2023 loan documents"),
],
"DEBT": [
 ("what is owed today", ANSWERED,
  "$85,000,000 drawn against a $123,000,000 lien held by Deutsche Bank AG, "
  "New York Branch. From STATED OUTSTANDING BALANCES, not face amounts"),
 ("every holder, 1990 to today", ANSWERED,
  "thirteen: Apple Bank, Queens County Savings, New York Community, Anglo "
  "Irish, Irish Bank Resolution, LSREF2 Clover Trust, Wells Fargo, LSREF2 "
  "again, UBS, Goldman Sachs, Shanghai Commercial, MetLife, Deutsche Bank"),
 ("how much was ever really borrowed", ANSWERED,
  "the 2023 chain reconciles exactly: $94,510,000 assigned + $25,490,000 new "
  "= $120,000,000. The same chain's FACE amounts sum to $146,344,892 and "
  "mean nothing. Every consolidation's new money is separable from its "
  "carry-forward"),
 ("the interest rate, at any point in 35 years", NOT_RECORDED,
  "⚠ A FINDING, NOT A GAP. Six generations state the size and withhold the "
  "price: 1990 'the Applicable Interest Rate AS DEFINED IN THE NOTE', 2012 "
  "'a variable interest rate loan, as more particularly set forth in the "
  "Loan Agreement', 2013/2014/2023/2025 silent across 200+ pages. The only "
  "rates ever recorded are 7.25% (1998) and 5.50% (2003), both on the "
  "$1M-scale predecessor loan. ACRIS's answer is that the rate was "
  "deliberately kept off the register, and that is worth knowing"),
 ("recourse", ANSWERED,
  "recourse 1990-2003; non-recourse from 2003-10-28 para 27 with an "
  "environmental carve-out; 2015 silent but a Completion Guaranty is "
  "referenced and unrecorded"),
],
"ENVELOPE": [
 ("how much floor area may be built", ANSWERED,
  "141,929 sf on lot 49. THE CHAIN CLOSES TO THE SQUARE FOOT: 209,968 "
  "+22,845 +10,726 +10,722 +14,703 = 268,964, split 2019 into 141,929 / "
  "127,035 = 268,964"),
 ("where every square foot came from", ANSWERED,
  "lots 53+55+56 (53,578 sf, 2010), 23 (22,845), 22 (10,726), 21 (10,722), "
  "20 (14,703) — seven sellers, mostly residential co-ops"),
 ("the volume constraints on it", ANSWERED,
  "lot 20's contribution comes from the portion BELOW a 130-foot plane, "
  "datum NGVD 1929 + 2.78 ft. Crop proofs/9534509cfd4986d7.png"),
 ("what the air rights cost", ANSWERED,
  "PER LOT, FROM THE ZLDA COVER STAMPS — lot 22 $1,450,000 over 10,726 sf "
  "= ~$135/sf, lot 21 $1,340,500 over 10,722 sf = ~$125/sf, each with two "
  "independent witnesses ten days apart. The 2010 lots 53/55/56 bundle was "
  "$5,000,000 over 53,578 sf = ~$93/sf. ⚠ Lot 20 shows $0/$0 because "
  "grantor and grantee are the SAME ENTITY — an internal reassignment, not "
  "a sale, so no price exists to find. The purchase agreements themselves "
  "are deliberately unrecorded; the tax stamp is the only witness"),
],
"ENCUMBRANCE": [
 ("what runs with the land", ANSWERED,
  "112 recorded terms across 43 documents — the Marriott ROFR, light/air/"
  "view easements over seven lots, the environmental covenant, ground-lease "
  "locks, an asbestos disclosure surviving foreclosure"),
 ("the environmental condition", ANSWERED,
  "a Voluntary Cleanup Agreement dated 2016-02-10 with NYC OER, recorded as "
  "a restrictive covenant under doc-type SUNDRY MISCELLANEOUS. ⚠ NOT ONE "
  "mortgage 2015-2025 mentions it"),
 ("where Marriott's ROFR ranks against the lien", NOT_RECORDED,
  "⚠ A FINDING. The subordination is conditional on (i) the lender not "
  "being a hotel competitor, (ii) the mortgage remaining validly recorded, "
  "and (iii) THE DEBT COMPLYING WITH SECTION 5.2 OF AN UNRECORDED FRANCHISE "
  "AGREEMENT. ACRIS's answer is that the rank is not determinable from the "
  "register, and that the third condition exists at all is the finding — "
  "the 2014 bank subordination recites only the first two"),
],
"PRIORITY": [
 ("the lien ladder", ANSWERED,
  "2015 states it uniquely and explicitly: $48M land loan first, Building "
  "Loan $31.93M second, Project Loan $33.78M third"),
 ("today's rank", ANSWERED,
  "'a first mortgage loan in an amount of $120,000,000' — recited in the "
  "companion assignment"),
],
"TENANCY": [
 ("the leasehold structure", ANSWERED,
  "ground lease dated 1995-05-01, 112 West 25 Company to LMG Realty, "
  "subleased to Steve and Al's Garage; amended 1997, 2007, 2008; merged "
  "into one entity by 2012; re-split propco/opco by 2023"),
 ("what the occupancy is", ANSWERED,
  "a Renaissance-branded Marriott hotel — franchise agreement 2014-07-14, "
  "Lam Gen 25 LLC as Franchisee and Operating Lessee"),
],
"INCOME": [
 ("what income is pledged and when a lender may take it", ANSWERED,
  "every generation pledges rents; 2014 and 2025 expressly ABSOLUTE, 2020 "
  "refuses the label and must be read structurally. Condemnation rides with "
  "the mortgage, not the assignment — consistent across three lenders"),
],
"VALUE": [
 ("what the land last traded for", ANSWERED,
  "$42,700,000, June 2007. Three witnesses: NYC RPTT / 2.625%, NYS RETT / "
  "0.4%, and the RP-5217's printed Full Sale Price. The deed recites $10"),
 ("what the leasehold cost", ANSWERED,
  "$2,300,000 for LMG Realty's sublease — from a filing with ZERO pages, "
  "both stamps independently returning it"),
 ("tax paid at every step", ANSWERED,
  "every stamp reconstructed and rate-checked; ⚠ two prior-tax affidavits "
  "(2003, 2014) overstate the 1990 payment against the instrument itself"),
],
"PARCEL": [
 ("the physical lot", ANSWERED,
  "through-block; 8,527 sf (lot 49) + 7,112 sf (lot 50) after the 2019 "
  "split; boundaries derive from an 1816 partition map"),
 ("the boundary discrepancy", ANSWERED,
  "NOT A DEFECT — '82 feet 10 inches (deed) (82 feet 8 3/4 inches - "
  "survey)'. Two conventions. Carried as an error through four reads"),
],
"CONSENT": [
 ("who had to agree", ANSWERED,
  "seven fee owners, four mortgagees including a 2000-vintage CMBS trust, "
  "and Marriott. Each co-op pre-consented to future mergers on ten business "
  "days' notice"),
 ("who was bound without signing", ANSWERED,
  "New York Community Bank and Anglo Irish bound their liens to a ZLDA "
  "neither signed; six owners bound in 2013 'by reason of their prior "
  "consent'"),
],
"IDENTIFY": [
 ("what a careful reader would still get wrong", ANSWERED,
  "52 recorded defects — the $10 and $19M traps, three wrong cover pages, "
  "four acknowledgment dates preceding their own instruments, a 27-year "
  "uncured legal-description note, and every material error in handwriting"),
],
}

# ---------------------------------------------------------------------------
# ⚠ NOT ACRIS'S JOB. These are HANDOFFS, and a handoff is a deliverable —
# it carries the ACRIS-side facts the other decoder needs in order to start.
# ---------------------------------------------------------------------------
HANDOFF = [
 ("DOB", "when it was built and to what plan",
  "ACRIS gives you: a monthly construction-progress covenant, a Completion "
  "Guaranty, a $65,710,000 building+project stack dated 2015-09-02, and a "
  "2016 cleanup agreement. ACRIS does NOT record a draw schedule, a "
  "completion date, or any description of the building"),
 ("DOF", "what the hotel earns and what it is assessed at",
  "ACRIS gives you: every rent pledge and the exact entity that holds the "
  "operating lease. ACRIS never states an income figure — every assignment "
  "pledges the rents and none quantifies them"),
 ("DOB / CO", "delivery date and the certificate chain",
  "ACRIS gives you the 2016 VCA date as an earliest-completion signal and "
  "the 2019 subdivision as a post-delivery event"),
 ("LPC / DCP", "whether anything overrides the FAR-10 envelope",
  "ACRIS gives you the nine-lot zoning lot and the 130-foot plane; it does "
  "not know the district, a landmark, or a special-district rule"),
 ("the franchise, unrecorded", "Section 5.2 and Section 17.4",
  "⚠ NO PUBLIC SOURCE. ACRIS proves these sections exist and control "
  "Marriott's priority and the ROFR's trigger. Only the parties hold them"),
]
