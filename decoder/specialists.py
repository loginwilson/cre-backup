"""DOC-TYPE SPECIALISTS — one agent per instrument type, getting better each run.

⚠ THE TOKEN PROBLEM THIS SOLVES, measured on lot 49:

    12 reading agents      ~2.7M tokens
    862 pages opened
    260 claims
    ~10,200 tokens PER CLAIM   ·   ~3,100 tokens PER PAGE

A page image costs 1.5-3k tokens just to enter context, so roughly HALF the
bill was pixels. Prompting cannot fix that. Only reading fewer pages can.

⚠ AND THE MEASUREMENT THAT SAYS IT IS SAFE TO READ FEWER:

    p001 alone      21% of all claims
    p001-p005       51% of all claims
    862 pages       0.30 claims/page
    cover-only      0.54 claims/page

A generalist agent reads a 40-page mortgage front to back because it does not
know what a mortgage contains. A SPECIALIST DOES. It knows the twenty slots a
mortgage has and roughly where each one sits, so it opens six pages and checks
a list instead of opening forty and forming an impression.

⚠ THE PROFICIENCY IS THE MENU, AND THE MENU IS DURABLE.
A slot menu is what one agent learned, written down so the next one starts
there. Each run may return MENU UPDATES — a slot nobody had listed, a page
prior that was wrong — and the menu is better for every future document of
that type, across every parcel. That is the compounding the user asked for:
not a model that remembers, a FILE that accumulates.

⚠ AND THE THIRD BENEFIT, WHICH MATTERS MOST FOR CORRECTNESS:
a checklist cannot forget. Prose reading silently omits; a slot left blank is
visible. Every "I dropped the word VIEW twice" error on this corpus was an
omission that a slot check would have caught, because the slot would have sat
there unanswered.

PAGE PRIORS BELOW ARE MEASURED, not guessed — from where claims actually sat
in 75 decoded documents on this parcel.
"""

# status vocabulary for every slot check. THREE outcomes, never two.
PRESENT, ABSENT, NOT_LOOKED = "PRESENT", "ABSENT", "NOT_LOOKED"

SPECIALISTS = {

"MTGE": dict(
  label="Mortgage / Gap Mortgage / Building or Project Loan Mortgage",
  priors=[1, 3, 8, 13, 14, 16, 17, 18],
  budget=10,
  slots=[
    "mortgage amount, taxable amount, exemption code, every tax component, TOTAL",
    "maximum principal secured — WORDS and NUMERALS separately",
    "lien position (first / second / third), stated verbatim",
    "interest rate — or the clause that defers it to an unrecorded note",
    "maturity date — or the clause that defers it",
    "Lien Law section 13 trust-fund covenant",
    "Lien Law Article 3-A, and any section 22 building loan CONTRACT",
    "alteration / demolition consent, and whether consent is reasonable or sole",
    "assignment of rents — ABSOLUTE or COLLATERAL, quote the deciding words",
    "bar on collecting rent more than one month in advance",
    "junior financing bar",
    "due-on-sale / transfer / change-of-control, and any family carve-out",
    "acceleration triggers, enumerated",
    "default rate and late charge",
    "financial reporting and inspection/appraisal at borrower cost",
    "recourse or non-recourse — ABSENT is not the same as non-recourse",
    "any guaranty referenced but not recorded",
    "does an unrecorded loan agreement CONTROL on conflict — quote it",
    "construction progress reporting (marks a real build)",
    "cross-default to other facilities",
  ],
  traps=[
    "⚠ FACE AMOUNTS ARE NOT ADDITIVE ACROSS A CONSOLIDATION CHAIN. Stated "
    "OUTSTANDING BALANCES are. A 2023 chain here summed to $146,344,892 of "
    "face and $120,000,000 of truth.",
    "⚠ Exemption 255 means NO NEW MONEY — the tax was paid on a companion gap "
    "mortgage. Find the gap; it carries the real new lending.",
    "⚠ Words and numerals disagree. One instrument reads 'NINETEEN MILLION "
    "AND 00/100 DOLLARS ($48,000,000.00)' and was recorded twice that way.",
  ]),

"CEMA": dict(
  label="Consolidation / Amendment / Restatement / Spreader Agreement",
  priors=[1, 4, 5, 14, 22, 32],
  budget=10,
  slots=[
    "cover tax block; exemption 255 means this is not new money",
    "consolidated amount, and the single-lien statement",
    "is it a CONSOLIDATION or a true SPREADER — quote the operative clause",
    "if a spreader: onto WHAT. Additional lots, or merely interests in the "
    "same land already encumbered",
    "maximum principal secured, words and numerals",
    "first-lien representation",
    "no-default or no-offset representation, AND THE DATE IT SPEAKS AS OF",
    "does the unrecorded loan agreement control on conflict",
    "the SCHEDULE of prior mortgages — transcribe every row",
    "prior mortgage tax paid per row, and whether TYPED or HANDWRITTEN",
    "new money — usually only in the margin, never in the typed text",
    "Lien Law section 13 covenant",
  ],
  traps=[
    "⚠ THE NEW-MONEY SPLIT IS HANDWRITTEN. Twice on this parcel the typed "
    "text said only the consolidated total and the split existed only as "
    "marginalia. No OCR finds it.",
    "⚠ PRIOR-TAX FIGURES IN 255 AFFIDAVITS ARE OFTEN WRONG. On this parcel "
    "the 1990 tax is stated as $22,500 by the instrument, $27,500 by a 2003 "
    "affidavit, $22,500 by a 2013 schedule and $28,000 by a 2014 affidavit. "
    "Record what the document says; never reconcile it.",
    "⚠ 'AGREEMENT' on the cover often hides a full mortgage restatement.",
  ]),

"ZLDA": dict(
  label="Zoning Lot Development and Easement Agreement",
  priors=[1, 5, 8, 24, 25, 32, 33, 40, 42, 44],
  budget=14,
  slots=[
    "cover doc type — 'DEVELOPMENT RIGHTS' marks a priced transfer",
    "⚠ THE TAX STAMPS ON THE COVER. This is the ONLY route to the price.",
    "the DEVELOPMENT RIGHTS CHART — usually a late exhibit, not the body",
    "floor area TRANSFERRED, per lot, with the label quoted verbatim",
    "floor area RETAINED by each seller",
    "the resulting BALANCE, and whose",
    "lot areas and the FAR the arithmetic implies",
    "light, air AND VIEW easement — the exact granting words",
    "the easement geometry: from what elevation, to what, from what DATUM, "
    "over what horizontal distance, for how long",
    "WHOSE land is burdened and WHOSE benefited — never assume mutual",
    "upzoning / downzoning reallocation formulas and their trigger",
    "whether either party may draw on the other's balance",
    "the full zoning-lot member list",
    "who signed, and who is bound WITHOUT signing",
    "which annexed forms are EXECUTED and which are blank specimens",
  ],
  traps=[
    "⚠ 'LIGHT, AIR AND VIEW' — THE THIRD WORD GETS DROPPED. On this parcel "
    "the operative grant says view and the annexed FORM omits it. They are "
    "different instruments; report both.",
    "⚠ THE PRICE IS DELIBERATELY OFF-RECORD. The purchase agreement is "
    "referenced by a Memorandum that states no price, with a prepared "
    "Termination that erases even that notice at closing. THE TAX STAMP IS "
    "THE ONLY WITNESS.",
    "⚠ A LIMITING PLANE IS NAMED FROM THE ESTATE BEING DESCRIBED. The same "
    "130-foot plane is an 'upper limiting plane' in one instrument and a "
    "'lower' one in another. ALWAYS record which VOLUME is conveyed, not "
    "which adjective was used.",
    "⚠ AN UNEXECUTED EXHIBIT BINDS NOTHING. Five live burdens were once "
    "recorded off a blank form here and had to be retracted.",
  ]),

"DEED": dict(
  label="Deed / Conveyance",
  priors=[1, 2, 3, 4, 5],
  budget=6,
  slots=[
    "⚠ THE TAX STAMPS. NYC RPTT / 2.625% and NYS RETT / 0.4% must AGREE.",
    "the RP-5217 Full Sale Price, if annexed — a third independent witness",
    "grantor and grantee, exactly as written",
    "the consideration RECITAL (usually $10 — never the price)",
    "'subject to' clause, and any schedule of permitted exceptions",
    "covenants — grantor's acts, Lien Law section 13, warranty or none",
    "prior-deed recital: date, reel/page or CRFN",
    "any reservation, exception, or development-rights language",
    "the legal description, and whether it says deed vs survey distances",
  ],
  traps=[
    "⚠ THE $10 RECITAL IS A 4,270,000x TRAP on this parcel. Price is NEVER "
    "in the grant; it is on the cover stamps.",
    "⚠ A $0.00 RETT WITH A NONZERO RPTT, OR BOTH ZERO, MEANS "
    "COMMONLY-CONTROLLED PARTIES — an allocation, not a sale. No price is "
    "derivable and saying so is the correct answer.",
    "⚠ A PRIOR-DEED RECITAL CAN CITE THE WRONG INSTRUMENT. One here fuses "
    "the date of one 1971 deed with the reel/page of another that runs the "
    "opposite way.",
  ]),

"ASST": dict(
  label="Assignment of Mortgage / of Leases and Rents",
  priors=[1, 2, 3, 4],
  budget=4,
  slots=[
    "assignor and assignee",
    "the consideration — on this corpus it EQUALS the outstanding balance, "
    "which is the number that actually matters",
    "what is assigned: which mortgages, by CRFN or reel/page",
    "recourse language — almost always 'without recourse'",
    "section 275 affidavit: filed, or expressly disclaimed as secondary market",
  ],
  traps=[
    "⚠ MOST ASSIGNMENTS ARE EMPTY. Four servicing transfers here ran 29 "
    "pages and produced ZERO substantive terms. THAT IS A RESULT — record "
    "the pages as opened-and-empty so nobody reads them again. DO NOT SPEND "
    "A LARGE BUDGET HERE.",
    "⚠ The consideration on an assignment is the balance, not a price.",
  ]),

"SAGE": dict(
  label="Sundry Agreement / Sundry Miscellaneous — ⚠ THE JUNK TYPE THAT ISN'T",
  priors=[1, 2, 3, 4, 5],
  budget=8,
  slots=[
    "⚠ WHAT THE INSTRUMENT CALLS ITSELF in its own title — the ACRIS type is "
    "nearly always wrong for this bucket",
    "parties, and what each gives up",
    "any subordination: of what, to what, and on what CONDITIONS",
    "any right of first refusal, option, or franchise reference",
    "any environmental covenant or cleanup agreement",
    "duration, and whether it binds successors",
  ],
  traps=[
    "⚠ ON THIS PARCEL, 'SAGE' AND 'SUNDRY MISCELLANEOUS' HID: a Marriott "
    "hotel-franchise right of first refusal, a lender waiver subordinating "
    "to a zoning lot declaration, and an ENVIRONMENTAL RESTRICTIVE COVENANT "
    "tied to a Voluntary Cleanup Agreement that NO MORTGAGE MENTIONS. "
    "NEVER SKIP THIS TYPE ON ITS COVER LABEL.",
    "⚠ Conditional subordinations can switch OFF. One here holds only while "
    "the lender is not a hotel competitor AND the debt complies with a "
    "section of an unrecorded franchise agreement.",
  ]),
}


def prompt(doctype, doc_id, n_pages, folder, bbl):
    s = SPECIALISTS[doctype]
    priors = [p for p in s["priors"] if p <= n_pages]
    return f"""You are the {doctype} specialist. You have decoded many
{s['label']} instruments. Read {doc_id} for {bbl}.

Pages: {folder}   ({n_pages} images, p001..p{n_pages:03d})

⚠ PAGE BUDGET: about {s['budget']} pages. These are where {doctype} facts sat
in previously decoded instruments of this type — START HERE, IN ORDER:
    {priors}
Then open more ONLY to close a slot still marked NOT_LOOKED. Do not read
front to back. A page image costs real money; an unread page costs nothing
but must be reported honestly as NOT_LOOKED.

⚠ YOU ARE CHECKING A LIST, NOT FORMING AN IMPRESSION. For every slot return
PRESENT with a verbatim quote, ABSENT because you read the page and it is not
there, or NOT_LOOKED. Never write ABSENT for a page you did not open.

SLOTS:
{chr(10).join(f'  {i+1:>2}. {x}' for i, x in enumerate(s['slots']))}

KNOWN TRAPS FOR THIS TYPE:
{chr(10).join('  ' + t for t in s['traps'])}

RETURN JSON ONLY — no prose:
{{
 "document_id": "{doc_id}",
 "doctype_indexed": "<what the cover calls it>",
 "doctype_actual": "<what the instrument calls itself>",
 "page_count_declared": <the cover's own PAGE 1 OF N, or null>,
 "pages_opened": [1,3,...],
 "pages_empty": [<opened, nothing there — this is COVERAGE, not a gap>],
 "slots": [{{"slot": 1, "status": "PRESENT", "page": 3,
             "y": [0.10, 0.24], "verbatim": "...", "value_num": null,
             "unit": null, "note": "..."}}],
 "menu_update": {{
    "new_slots": ["<a term this type carries that the menu does not list>"],
    "bad_priors": [<page numbers in the prior list that held nothing>],
    "good_pages": [<pages that held facts but were NOT in the priors>]
 }}
}}

⚠ EVERY PRESENT SLOT NEEDS "y": [top, bottom] AS A FRACTION OF PAGE HEIGHT.
Err wide — include the heading above the clause. That region is what lets the
page image be deleted afterwards; a slot without one costs 10x the storage
forever, and a crop showing a clause without its heading proves nothing.

⚠ menu_update IS HOW YOU GET BETTER. If this instrument carried a term the
slot list does not name, say so — it becomes a slot for every future
{doctype} on every parcel. If a prior page was empty, say so — the priors
sharpen. That file is the proficiency; you are writing to it.
"""


def budget_report():
    print("SPECIALIST BUDGETS vs GENERALIST READING\n")
    print("  type    slots  priors  budget   generalist   saving")
    tot_b = tot_g = 0
    seen = {"MTGE": 37, "CEMA": 61, "ZLDA": 110, "DEED": 5,
            "ASST": 8, "SAGE": 12}
    for t, s in SPECIALISTS.items():
        g = seen.get(t, 20)
        tot_b += s["budget"]
        tot_g += g
        print(f"  {t:<7} {len(s['slots']):>4}  {len(s['priors']):>6}  "
              f"{s['budget']:>6}   {g:>10}   {100*(1-s['budget']/g):>5.0f}%")
    print(f"\n  typical doc set    {tot_b:>3} pages vs {tot_g:>3}   "
          f"{100*(1-tot_b/tot_g):.0f}% fewer page-reads")
    print(f"  at ~3,100 tokens/page that is "
          f"~{(tot_g-tot_b)*3100/1000:.0f}k tokens saved per document set")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    budget_report()
