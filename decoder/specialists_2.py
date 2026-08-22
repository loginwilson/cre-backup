"""THE REMAINING NINE SPECIALISTS — every ACRIS type now has a reader.

⚠ WHY EVERY TYPE NEEDS ONE EVEN THOUGH NO SINGLE PARCEL HAS EVERY TYPE.

A type without a specialist falls through to a generalist, and a generalist
reads front to back because it does not know what the instrument contains.
On lot 49 that cost ~2.7M tokens for 260 claims. Worse, the types most likely
to be missing a specialist are the RARE ones — and on this parcel the rare
bucket is where the Marriott franchise ROFR, the environmental cleanup
covenant, and the instrument naming the fee conveyance were all hiding.

⚠ THE SLOTS BELOW ARE NOT INVENTED. Every one is a term this corpus actually
carried, or a trap it actually sprang. A checklist assembled from imagination
finds imaginary things.

Merged into specialists.SPECIALISTS at import.
"""

# ---------------------------------------------------------------------------
EXTRA = {

"ALR": dict(
  label="Assignment of Leases and Rents",
  priors=[1, 3, 4, 6, 7, 8, 10, 12],
  budget=8,
  slots=[
    "cover tax block — an ALR almost always claims exemption 255 because it "
    "secures the SAME debt as its companion mortgage. ⚠ ITS FACE AMOUNT IS "
    "A RESTATEMENT AND MUST NEVER BE ADDED TO THE MORTGAGE",
    "⚠ ABSOLUTE or COLLATERAL — quote the exact deciding words. 'present and "
    "absolute transfer ... not an assignment as security' vs 'Mortgagee "
    "waives the right to enter ... Mortgagor shall have a license'",
    "the licence back, and what revokes it — notice, or automatic on default",
    "what income is pledged: rents, security deposits, lease TERMINATION "
    "fees, percentage and index rents, utility resale, forfeited deposits, "
    "liquidated damages, loss-of-rents insurance, bankruptcy rejection claims",
    "⚠ ARE CONDEMNATION PROCEEDS IN THE GRANT? On this corpus they are "
    "consistently NOT — they ride with the mortgage instead. Check, do not "
    "assume",
    "borrower lease restrictions: enter/extend, cancel/terminate/surrender, "
    "reduce rent, advance rent beyond one month, material modification, "
    "consent to assignment or subletting — and whether SUBORDINATE is among "
    "them (often it is not)",
    "may the lender notify tenants without proving default",
    "mortgagee-in-possession disclaimer",
    "may the lender establish reserves out of rents before paying down debt",
    "termination: automatic and derivative on the mortgage's release, or a "
    "separate recorded instrument? and who pays for it",
    "does an unrecorded loan agreement control on conflict",
    "who signs — an ALR is frequently executed ONE-SIDED by the assignor only",
  ],
  traps=[
    "⚠ THE LABEL IS NOT ALWAYS PRESENT. One 2020 instrument here uses neither "
    "'absolute' nor 'collateral' anywhere in sixteen sections and must be "
    "read structurally: a licence-until-default plus a waiver-of-entry is "
    "COLLATERAL in substance whatever it calls itself.",
    "⚠ TERMINATION IS OFTEN DERIVATIVE AND THEREFORE LEAVES NO RECORD — "
    "'released and terminated as, when and to the extent the Security "
    "Instrument is released, WITHOUT THE NEED TO EXECUTE FURTHER "
    "INSTRUMENTS.' A reader waiting for a recorded satisfaction never sees "
    "one.",
    "⚠ 'INDEFEASIBLY PAID IN FULL' means a later preference clawback "
    "reanimates the obligation.",
  ]),

"RELEASE": dict(
  label="Satisfaction · Discharge · Termination · Release of a lien or an ALR",
  priors=[1, 2, 3, 4],
  budget=4,
  slots=[
    "⚠ EXACTLY WHAT IS BEING RELEASED — quote the identifying CRFN or "
    "reel/page. This is the whole document and it is routinely narrower "
    "than it appears",
    "what is NOT released. A release of an assignment of rents does NOT "
    "release the mortgage it secured",
    "partial or complete — is a PARCEL being released from a blanket lien",
    "any reservation, carve-out, or survival clause",
    "who executes, and whether the releasing party still holds the paper "
    "('the Assignment has not been assigned')",
    "consideration, and whether it equals an outstanding balance",
    "the date, versus the date of the instrument released",
  ],
  traps=[
    "⚠ THE 1999 INSTRUMENT ON THIS PARCEL, INDEXED 'SAGE', CANCELLED ONLY "
    "THE 1990 ASSIGNMENT OF LEASES AT REEL 1707 PAGE 1311. The $1,000,000 "
    "MORTGAGE AT PAGE 1285 WAS NEVER DISCHARGED — it was assigned forward "
    "and is still alive inside today's $123,000,000 lien, 26 years later. A "
    "satisfaction-keyed reader marks that debt closed and is wrong by a "
    "quarter century.",
    "⚠ Check the notary's commission dates. One release here bears an "
    "acknowledgment dated AFTER the notary's commission had expired, and a "
    "hand-corrected month with 'SO IN ORIGINAL' stamped over it.",
    "⚠ A release naming 'Termination of Assignment of Leases and Rents' as "
    "the thing terminated — instead of the Assignment itself — appears in "
    "this corpus. Read the identifying clause, not the caption.",
  ]),

"STAMP": dict(
  label="RPTT / RETT / RP-5217 — ⚠ THE COVER PAGE IS THE ENTIRE DOCUMENT",
  priors=[1, 2],
  budget=2,
  slots=[
    "NYC Real Property Transfer Tax paid",
    "NYS Real Estate Transfer Tax paid",
    "⚠ DIVIDE EACH BY ITS RATE AND CHECK THEY AGREE. Commercial over "
    "$500,000: RPTT 2.625%, RETT 0.400%. Two authorities, two rates, one "
    "answer — that agreement IS the proof",
    "the RP-5217 'Full Sale Price' if annexed — a third independent witness",
    "grantor and grantee as indexed",
    "Document Page Count — ⚠ ZERO IS VALID and means a tax-return-only "
    "filing with no recordable instrument",
    "the sale contract date, and the assessed value if printed",
  ],
  traps=[
    "⚠ A ZERO-PAGE FILING IS NOT AN ERROR AND IS NOT EMPTY. One on this "
    "parcel carried $60,375.00 and $9,200.00 of stamps that independently "
    "reconstruct a $2,300,000 conveyance recorded nowhere else — the "
    "purchase of a leasehold whose transfer instrument was never recorded.",
    "⚠ BOTH STAMPS ZERO MEANS COMMONLY-CONTROLLED PARTIES — an allocation, "
    "not a sale. No price is derivable and SAYING SO IS THE CORRECT ANSWER, "
    "not a failure. Confirm by checking whether the same person signed both "
    "sides.",
    "⚠ ONE STAMP ZERO AND THE OTHER NONZERO leaves a single-witness "
    "derivation. Flag it as weaker evidence; do not present it as verified.",
  ]),

"DECL": dict(
  label="Declaration of Zoning Lot Restrictions · Condominium Declaration",
  priors=[1, 3, 4, 5, 6],
  budget=8,
  slots=[
    "⚠ THE FULL LIST OF TAX LOTS declared to be one zoning lot",
    "which lot is 'Developer Land' and which is 'Owner Land'",
    "the Zoning Resolution section relied on — usually 12-10(d)",
    "⚠ WHETHER THIS DOCUMENT DEFERS ITS SUBSTANCE TO A ZLDA. Quote the "
    "deferral. A declaration MERGES lots; only a ZLDA MOVES floor area",
    "pre-consent to future enlargement, and the notice period it imposes",
    "every party in interest listed in the title certification, with its "
    "role and whether it signed or WAIVED",
    "any mortgagee waiver or subordination referenced by CRFN",
    "whether future owners are bound without signing",
  ],
  traps=[
    "⚠ A DECLARATION CONTAINS NO SQUARE FOOTAGE. Ten declarations and "
    "waivers on this parcel ran 122 pages and yielded ZERO floor-area "
    "figures. Every transfer number lives in the ZLDA. Budget accordingly "
    "and do not go hunting for numbers that are structurally absent.",
    "⚠ THE PRE-CONSENT CLAUSE IS HOW AN ASSEMBLAGE KEEPS GROWING. Each "
    "owner is 'deemed automatically and without any further action on its "
    "part' to consent to mergers it knows nothing about, with a ten "
    "business day duty to sign whatever comes next.",
    "⚠ Acknowledgment dates routinely precede the declaration's own date — "
    "ten months, in one case here. AN ACKNOWLEDGMENT DATE IS NOT AN EVENT "
    "DATE.",
  ]),

"SUBORD": dict(
  label="Subordination · Waiver · Consent",
  priors=[1, 3, 4, 5],
  budget=6,
  slots=[
    "who subordinates, and exactly what interest they hold",
    "what it is subordinated TO — quote the instrument and its CRFN",
    "⚠ THE CONDITIONS. A subordination that holds 'only if and for so long "
    "as' is REVERSIBLE. Enumerate every condition",
    "who is senior after this instrument",
    "what is expressly NOT subordinated",
    "does it bind successors, and is it recorded against every affected lot",
    "who signed, and whether the beneficiary signed at all",
  ],
  traps=[
    "⚠ THE MARRIOTT SUBORDINATION ON THIS PARCEL HAS THREE CONDITIONS, AND "
    "THE THIRD IS UNKNOWABLE FROM THE RECORD: the lender must not be a hotel "
    "competitor, the mortgage must remain validly recorded, AND the debt "
    "must comply with a section of an UNRECORDED franchise agreement. Two "
    "lender changes since have addressed none of them. So the priority "
    "question is genuinely undeterminable — and that is the answer.",
    "⚠ A LENDER CAN BIND ITS LIEN TO A DOCUMENT IT NEVER SIGNED, by "
    "recording its own waiver. Do not infer who agreed from who signed the "
    "principal instrument.",
    "⚠ A waiver given for ONE event does not cure conditions for later "
    "events. Marriott waived in 2019 for a zoning-lot restructuring only.",
  ]),

"LEASE": dict(
  label="Memorandum of Lease · Assignment of Lease · Sublease",
  priors=[1, 2, 3, 4, 5],
  budget=6,
  slots=[
    "landlord and tenant, exactly as named",
    "commencement, term, and every renewal option with its notice period",
    "⚠ IS THE LANDLORD THE SAME ENTITY AS THE TENANT? A merger of estates "
    "is what makes a site developable and a split is what makes it "
    "financeable",
    "every amendment recited, with its date — amendments are rarely recorded "
    "separately and the recital is often the only trace",
    "any sublease, and who the actual occupant is",
    "purchase option, right of first refusal, or right of first offer",
    "assignment and subletting restrictions",
    "the rent, if stated at all",
  ],
  traps=[
    "⚠ A MEMORANDUM GIVES NOTICE THAT A LEASE EXISTS WHILE RECORDING NONE "
    "OF ITS TERMS. Expect the rent to be absent by design.",
    "⚠ THE ONLY RECORD OF AN OPERATING TENANCY MAY BE INSIDE A LENDER'S "
    "COLLATERAL ASSIGNMENT. The 1995 ground lease and its garage sublease on "
    "this parcel appear nowhere else — the lease itself was never recorded.",
    "⚠ WATCH THE ESTATE STRUCTURE ACROSS TIME. Here: separate estates 1995, "
    "merged into one entity by 2007-2012, re-split into propco/opco by 2023. "
    "Each move changes who can sell, who can borrow, and who signs.",
  ]),

"EASE": dict(
  label="Easement · Party Wall · Light and Air",
  priors=[1, 3, 4, 5, 6],
  budget=8,
  slots=[
    "⚠ THE EXACT GRANTING WORDS. 'light, air AND VIEW' is three rights, not "
    "two, and the third is dropped constantly",
    "WHOSE land is burdened and WHOSE is benefited — never assume mutual",
    "⚠ THE GEOMETRY AS A VOLUME: from what elevation TO what elevation, "
    "measured from WHAT DATUM, over what horizontal area or depth",
    "duration — perpetual, a term of years, or until a triggering event",
    "⚠ IS IT VARIABLE? Can the plane be raised or the area changed, and on "
    "what trigger and whose notice",
    "any reservation the burdened owner keeps — existing structures, "
    "mechanical equipment above the roofline, replacement rights",
    "maintenance, access, and construction-protection obligations that "
    "outlive the grant",
    "whether an annexed FORM of easement differs from the operative grant",
  ],
  traps=[
    "⚠ A LIMITING PLANE IS NAMED FROM THE ESTATE BEING DESCRIBED. The same "
    "130-foot plane is an 'upper limiting plane' bounding the parcel below "
    "it and a 'lower limiting plane' bounding the parcel above it. RECORD "
    "WHICH VOLUME IS CONVEYED, NEVER WHICH ADJECTIVE WAS USED. I got this "
    "backwards once and reported it.",
    "⚠ EVERY LOT HAS ITS OWN PLANE. On this block: 155.24 ft, 150 ft, 130 "
    "ft, 130 ft. There is no blanket height.",
    "⚠ THE ANNEXED 'FORM OF LIGHT AND AIR EASEMENT' OMITS 'VIEW' IN FOUR "
    "SEPARATE AGREEMENTS HERE while the operative grant includes it. That "
    "is a systematic divergence, not a typo, and it decides whether a "
    "neighbour may build something that blocks the view without blocking "
    "light.",
    "⚠ THE DATUM CAN CONTRADICT ITSELF INSIDE ONE INSTRUMENT — 2.75 ft in "
    "the body and 2.78 ft with a different standard in the exhibits. The "
    "exhibits are what a surveyor uses.",
  ]),

"DISTRESS": dict(
  label="Lis Pendens · Mechanic's Lien · Judgment · Federal Lien · Bankruptcy",
  priors=[1, 2, 3, 4],
  budget=6,
  slots=[
    "the claimant, and what they say they are owed",
    "the amount claimed",
    "the court, index number, and filing date",
    "what the claim is ABOUT — unpaid work, a contract dispute, a tax",
    "⚠ FOR A MECHANIC'S LIEN: the last date work was performed. That dates "
    "construction activity more precisely than any permit",
    "whether it has been discharged, bonded, or vacated, and by what",
    "which lots it clouds",
  ],
  traps=[
    "⚠ THIS IS THE MOST TIME-SENSITIVE TYPE IN ACRIS AND THE EASIEST TO "
    "MISS, because a discharge is a separate later document. An undischarged "
    "lis pendens is a live cloud on title; a discharged one is history. "
    "ALWAYS look for the release before reporting the lien.",
    "⚠ A MECHANIC'S LIEN NAMES A CONTRACTOR AND A DATE — often the only "
    "public evidence of who actually built the building and when they "
    "stopped being paid.",
    "⚠ NONE APPEAR ON THIS PARCEL, which is itself a finding: 35 years, "
    "$123M of debt, a full ground-up construction, and no recorded distress.",
  ]),

"UCC": dict(
  label="UCC-1 Fixture Filing · UCC-3 Amendment or Termination",
  priors=[1, 2, 3],
  budget=3,
  slots=[
    "debtor and secured party, exactly as named",
    "the collateral description — fixtures, equipment, or all-assets",
    "whether it is a FIXTURE FILING against the real property",
    "for a UCC-3: continuation, amendment, assignment, or TERMINATION, and "
    "which original filing it acts on",
    "the file number of the original",
  ],
  traps=[
    "⚠ A UCC-1 IS THE CHEAPEST EVIDENCE THAT A LENDER RELATIONSHIP EXISTS "
    "and it often appears when no mortgage does. It also lapses after five "
    "years unless continued — so a live UCC-1 dates a relationship, and a "
    "lapsed one dates its end.",
    "⚠ LOW YIELD PER PAGE. Budget three pages and move on unless the "
    "collateral description names something specific.",
  ]),
}


def install():
    """Merge into the main registry so there is ONE place specialists live."""
    import specialists as S
    for k, v in EXTRA.items():
        S.SPECIALISTS.setdefault(k, v)
    return S.SPECIALISTS


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import doctype_registry as REG
    allspec = install()
    print(f"SPECIALISTS · {len(allspec)} built\n")
    print("  name       slots  traps  budget  types routed")
    routed = {}
    for t, (spec, tier, _) in REG.REGISTRY.items():
        routed[spec] = routed.get(spec, 0) + 1
    for name in sorted(allspec, key=lambda n: -len(allspec[n]["slots"])):
        s = allspec[name]
        print(f"  {name:<10} {len(s['slots']):>5}  {len(s['traps']):>5}  "
              f"{s['budget']:>6}  {routed.get(name, 0):>5}")
    missing = sorted(set(routed) - set(allspec))
    print()
    if missing:
        print(f"  ⚠ STILL UNBUILT: {', '.join(missing)}")
    else:
        print("  ✓ EVERY TYPE IN THE REGISTRY ROUTES TO A BUILT SPECIALIST.")
    tot_slots = sum(len(s["slots"]) for s in allspec.values())
    tot_traps = sum(len(s["traps"]) for s in allspec.values())
    print(f"  {tot_slots} slots · {tot_traps} traps · "
          f"{len(REG.REGISTRY)} ACRIS types covered")
