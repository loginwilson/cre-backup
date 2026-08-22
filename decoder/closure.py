"""CLOSURE — decode completeness measured in FACTS, not in documents read.

⚠ WHY THIS EXISTS. For thirteen hours I reported coverage as "documents read
/ documents on disk" and it kept saying 49%, 66%, 71%. Then I told the user
"ZERO square-footage figures in 122 pages" as though the envelope were
unknown. It is not unknown. It is CLOSED — every transfer and every balance
from 2010 to 2019, verified to the square foot, from five OTHER documents.

The unit of coverage was wrong. A document is not a fact. A fact can be
established four ways and only the first requires holding the document:

  READ      the instrument says it, and I read the page
  RECITED   other instruments quote it. TWO INDEPENDENT RECITALS BY PARTIES
            WITH OPPOSING INTERESTS IS STRONGER EVIDENCE THAN ONE READING —
            a lender and a borrower who both recite $40,500,000 are not
            colluding about it
  DERIVED   arithmetic on a recorded number. A tax stamp divided by its
            statutory rate returns the price the instrument refused to state
  CLOSED    a ledger balances. If A + B = C and all three are independently
            recorded, none of them can be wrong without the other two moving

⚠ AND THE CONVERSE, WHICH MATTERS MORE. Holding a document proves nothing on
its own. Four 2011 assignments, 29 pages, all read: zero facts. Reading is
the cost, not the result.

So: a MISSING document whose material terms are recited by two or more
independent instruments is DECODED. A HELD document nobody has mined is not.

Run:  python closure.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import claims as K
from _fix_routes import ROUTES, LABEL

READ, RECITED, DERIVED, CLOSED, OPEN = "READ", "RECITED", "DERIVED", "CLOSED", "OPEN"

# ---------------------------------------------------------------------------
# What each function must answer before the parcel is decoded. These are the
# questions a broker actually asks; they are not derived from what I happen
# to have found, which would make the test circular.
# ---------------------------------------------------------------------------
QUESTIONS = {
"ENVELOPE": [
 ("how much floor area may be built here today", CLOSED,
  "141,929 sf on lot 49. THE CHAIN CLOSES TO THE SQUARE FOOT: 209,968 (2010) "
  "+22,845 (lot 23) +10,726 (lot 22) +10,722 (lot 21) +14,703 (lot 20) = "
  "268,964, and the 2019 subdivision splits it 141,929 / 127,035 = 268,964 "
  "exactly. Five documents, nine years, every step verified"),
 ("where did the floor area come from", CLOSED,
  "seven co-op and LLC sellers: lots 53+55+56 (53,578 sf, 2010), lot 23 "
  "(22,845), lot 22 (10,726), lot 21 (10,722), lot 20 (14,703)"),
 ("at what FAR", READ,
  "FAR 10 — stated, and independently checked by lot 50: 7,112 sf x 10 = "
  "71,120, which is the land component of its 127,035 balance"),
 ("is the envelope constrained by anything other than FAR", CLOSED,
  "yes — lot 49's 14,703 sf from lot 20 comes from the portion BELOW a "
  "130-foot plane (NGVD 1929 + 2.78 ft). Settled by opening the page: the "
  "three instruments never disagreed, and the cite I held was off by one. "
  "Crop proofs/9534509cfd4986d7.png"),
],
"DEBT": [
 ("what is owed today", CLOSED,
  "$85,000,000 drawn against a $123,000,000 lien held by Deutsche Bank. "
  "Reconstructed from stated outstanding balances, not face amounts"),
 ("the 2023 recapitalisation", CLOSED,
  "$25.5M + $31.93M + $33.78M + $3.3M = $94,510,000 assigned, + $25,490,000 "
  "new = $120,000,000. Reconciles exactly; the same chain's FACE amounts sum "
  "to $146,344,892 and mean nothing"),
 ("every holder of the lien", CLOSED,
  "thirteen, 1990-2025: Apple Bank, Queens County Savings, New York "
  "Community, Anglo Irish, Irish Bank Resolution, LSREF2 Clover Trust, Wells "
  "Fargo, LSREF2 again, UBS, Goldman Sachs, Shanghai Commercial, MetLife, "
  "Deutsche Bank"),
 ("the interest rate, at any point in 35 years", OPEN,
  "⚠ GENUINELY NOT IN ACRIS, and this is a FINDING not a gap. Six "
  "generations state the size and withhold the price: 1990 'the Applicable "
  "Interest Rate as defined in the Note', 2012 'a variable interest rate "
  "loan', 2013/2014/2023/2025 silent. The only rates ever recorded are the "
  "1998 CEMA's 7.25% and the 2003 modification's 5.50% — both on a "
  "$1M-scale loan, neither on the development debt"),
],
"TITLE": [
 ("who owns it", RECITED,
  "CHELSEA 25 HOTEL LLC as fee owner with LAM GEN 25 LLC as Operating "
  "Lessee — the propco/opco hotel split, recited in the 2023 loan documents"),
 ("how Chelsea 25 Hotel LLC acquired the fee", OPEN,
  "⚠ NO CONVEYANCE EXISTS IN THIS CORPUS. It appears in none of mortgage "
  "items 1-9 and enters only by CO-SIGNING the 2023 gap mortgage. Two firms "
  "two years apart recite the same thing. ⚠ THE DEED IS NOT MERELY UNREAD — "
  "IT WAS NEVER PULLED, and it is the single most consequential missing "
  "instrument for a broker: you cannot name the seller"),
 ("the chain before that", CLOSED,
  "112 West 25 Realty Corp -> 112 West 25 Company (1971, round trip) -> "
  "Edelman Family LP (1998, $10 recital) -> 112-118 West 25th LLC (2007, "
  "$42,700,000) -> Lam Gen 25 LLC -> Chelsea 25 Hotel LLC"),
],
"VALUE": [
 ("what the land last traded for", CLOSED,
  "$42,700,000 in June 2007. Three witnesses: NYC RPTT $1,120,875 / 2.625%, "
  "NYS RETT $170,800 / 0.4%, and the RP-5217's own printed Full Sale Price. "
  "The deed's recital says $10"),
 ("what the leasehold cost", DERIVED,
  "$2,300,000 for LMG Realty's sublease, from a filing with ZERO pages — "
  "both stamps independently return it"),
 ("what the air rights cost", OPEN,
  "⚠ NOT ONE ZLDA IS IN THE CORPUS — 2010, 2019, lot 21 and lot 22 all "
  "missing, and price is the one term no other instrument recites. Nearest "
  "evidence: lot 53's FEE sold for $5,242,000 in Dec 2009 (two witnesses) "
  "and a bundled $5,000,000 transfer tax in 2010 (one witness only, the NYS "
  "RETT was $0.00)"),
],
"ENCUMBRANCE": [
 ("what burdens run with the land", READ,
  "112 recorded terms across 43 documents — the Marriott ROFR, the "
  "light/air/view easements over seven lots, the environmental covenant, "
  "the ground-lease locks"),
 ("the environmental condition", RECITED,
  "⚠ A VOLUNTARY CLEANUP AGREEMENT dated 2016-02-10 with NYC OER, recorded "
  "as a restrictive covenant under doc-type SUNDRY MISCELLANEOUS. NOT ONE "
  "mortgage 2015-2025 mentions it. The VCA itself is not in the corpus"),
 ("whether Marriott's ROFR sits ahead of or behind the lien", OPEN,
  "⚠ UNANSWERABLE FROM THE RECORD, BY DESIGN. Subordination holds only "
  "while (i) the lender is not a hotel competitor, (ii) the mortgage stays "
  "validly recorded, and (iii) THE DEBT COMPLIES WITH SECTION 5.2 OF AN "
  "UNRECORDED FRANCHISE AGREEMENT. Marriott waived once, in 2019, scoped to "
  "the zoning-lot restructuring. Neither the 2023 nor the 2025 assignment "
  "addresses any condition"),
],
"TENANCY": [
 ("who occupies it", CLOSED,
  "a Renaissance-branded Marriott hotel. Franchise agreement 2014-07-14, "
  "Lam Gen 25 LLC as Franchisee and Operating Lessee"),
 ("the leasehold structure", CLOSED,
  "ground lease dated 1995-05-01, 112 West 25 Company to LMG Realty, "
  "subleased to Steve and Al's Garage; amended 1997, 2007, 2008; both sides "
  "merged into one entity by 2012 and re-split propco/opco by 2023"),
 ("what the hotel earns", OPEN,
  "⚠ NOT AN ACRIS FACT AT ALL. Every assignment of rents pledges the income "
  "and none states it. This closes from DOF income filings, not here"),
],
"PERMIT": [
 ("was it built", RECITED,
  "yes — a monthly construction-progress covenant, a completion guaranty, a "
  "$65,710,000 building-and-project loan stack, and a 2016 TCO era implied "
  "by the VCA date"),
 ("when, and to what plan", OPEN,
  "⚠ NOT AN ACRIS FUNCTION. No draw schedule, no completion date, no "
  "description of the building is recorded anywhere. This closes from DOB "
  "job 121187214, not here"),
],
"PRIORITY": [
 ("the lien ladder", READ,
  "2015 states it explicitly and uniquely: $48M land loan first, Building "
  "Loan $31.93M SECOND, Project Loan $33.78M THIRD"),
 ("today's ranking", RECITED,
  "'a first mortgage loan in an amount of $120,000,000' — but stated in the "
  "companion assignment, because the mortgage itself is not in the corpus"),
],
"CONSENT": [
 ("who had to agree to the assemblage", CLOSED,
  "seven fee owners, four mortgagees incl. a CMBS trust, and Marriott. "
  "Each co-op pre-consented to future mergers on 10 business days' notice"),
 ("who was bound without signing", READ,
  "New York Community Bank and Anglo Irish bound their liens to a ZLDA "
  "neither ever signed; six owners bound in 2013 'by reason of their prior "
  "consent'"),
],
"PARCEL": [
 ("the physical lot", CLOSED,
  "through-block, 8,527 sf (lot 49) + 7,112 sf (lot 50) after the 2019 "
  "split; boundaries derive from an 1816 partition map"),
 ("the 82'8-3/4\" vs 82'10\" conflict", CLOSED,
  "NOT A DEFECT. A 2013 title certification prints both: '82 feet 10 inches "
  "(deed) (82 feet 8 3/4 inches - survey)'. Two conventions. I carried it as "
  "an error through four reads"),
],
"INCOME": [
 ("what income is pledged, and when the lender may take it", READ,
  "every generation pledges rents; 2014 and 2025 are expressly ABSOLUTE, "
  "2020 refuses the label and must be read structurally"),
],
"IDENTIFY": [
 ("what a careful reader would still get wrong", READ,
  "51 recorded defects — the $10 and $19M traps, three wrong cover pages, "
  "four acknowledgment dates preceding their own instruments, a 27-year "
  "uncured legal-description note, and every material error in handwriting"),
],
}

# missing instruments, and what the corpus establishes about each anyway
MISSING = [
 ("$120,000,000 CEMA", "CRFN 2023000287582", 4,
  "amount, first-lien status, exemption, the full 1990-2023 schedule, the "
  "gap tax of $713,720", "its own covenants and any representations"),
 ("2010 ZLDA", "CRFN 2010000384312", 6,
  "date, parties, the 53,578 sf transferred and its per-lot split, the "
  "resulting 209,968 sf balance", "the price, and the easement granting words"),
 ("Lot 21 + Lot 22 ZLDAs", "2013-05-15", 4,
  "dates, parties, 10,722 and 10,726 sf transferred, resulting balances",
  "the prices"),
 ("2019 ZLDA", "CRFN 2019000231248", 3,
  "date, the nine-lot membership, the 141,929 / 127,035 split",
  "the internal allocation terms"),
 ("2020 mortgage", "Doc ID 2020081400407001", 2,
  "$5,000,000 principal, Shanghai Commercial as lender, $140,000 tax paid "
  "(= 2.800%)", "its covenants"),
 ("the deed into Chelsea 25 Hotel LLC", "not identified", 0,
  "nothing", "⚠ EVERYTHING — this one is genuinely dark"),
]


def main():
    rows = K.rows()
    print(f"CLOSURE · {len(rows)} claims · "
          f"{len({c['document_id'] for c in rows})} documents cited\n")

    order = [CLOSED, READ, RECITED, DERIVED, OPEN]
    rank = {s: i for i, s in enumerate(order)}
    tot = opened = 0
    for fn, qs in QUESTIONS.items():
        worst = max(qs, key=lambda q: rank[q[1]])[1]
        n_open = sum(1 for q in qs if q[1] == OPEN)
        tot += len(qs)
        opened += n_open
        flag = "⚠ OPEN" if n_open else "COMPLETE"
        print(f"{fn}  —  {len(qs) - n_open}/{len(qs)} answered   {flag}")
        for q, status, detail in qs:
            mark = "⚠" if status == OPEN else " "
            print(f"  {mark} [{status:<7}] {q}")
            for line in _wrap(detail, 70):
                print(f"              {line}")
        print()

    print("=" * 72)
    print("INSTRUMENTS NOT IN THE CORPUS — and what is known regardless\n")
    for name, ref, n, known, unknown in MISSING:
        verdict = ("DECODED by recital" if n >= 2 else
                   "PARTIAL" if n == 1 else "⚠ DARK")
        print(f"  {name}  ({ref})")
        print(f"    recited by {n} independent instrument(s) -> {verdict}")
        print(f"    known:   {known}")
        print(f"    unknown: {unknown}\n")

    print("=" * 72)
    print(f"FACTS ANSWERED  {tot - opened}/{tot}  "
          f"({100 * (tot - opened) // tot}%)")
    print(f"GENUINELY OPEN  {opened}\n")
    print("  The open items, by what would actually close them:\n")
    for fn, qs in QUESTIONS.items():
        for q, status, detail in qs:
            if status != OPEN:
                continue
            # ⚠ DECLARED, NOT INFERRED. See _fix_routes.py for why.
            route = LABEL.get(ROUTES.get(q, "READ"), LABEL["READ"])
            print(f"    [{fn}] {q}")
            print(f"        -> {route}")
    print()
    fetchable = sum(1 for qs in QUESTIONS.values() for q, s, d in qs
                    if s == OPEN and ROUTES.get(q) == "FETCH")
    print(f"  ⚠ {fetchable} OF {opened} WOULD BE CLOSED BY FETCHING. NONE BY "
          f"READING MORE OF WHAT IS ALREADY ON DISK.")


def _wrap(s, w):
    out, cur = [], ""
    for word in s.split():
        if len(cur) + len(word) + 1 > w:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        out.append(cur)
    return out


main()
