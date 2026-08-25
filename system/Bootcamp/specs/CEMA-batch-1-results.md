# CEMA BATCH 1 — RESULTS

Scored against `CEMA-batch-predictions.md`, which was written and banked
before either document was opened.

| | COVERAGE | SURPRISE | PREDICTIONS |
|---|---|---|---|
| #4 `2003011000989002` | 100% | 9 | **8 of 10** |
| #5 `BK_7030040000013` | 100% | 7 | **8 of 10** |

**16 of 20 predictions held.** Coverage was 100% on both — every spec field the
documents carried was found, which is what a read sheet derived from a class is
supposed to buy. **The four failures are the valuable part**, and three of them
land on the same field.

---

## THE HEADLINE — THE SPEC'S SHARPEST FIELD WAS WRONG

specs/CEMA.md called the restated-terms location "the class's sharpest trap"
and predicted, from three members, that the terms would be **elsewhere**.
**Both new members put them closer to hand than predicted, in two different
places.** Five members, four locations:

| member | where the rate, payment and maturity live |
|---|---|
| r13 | in the agreement |
| r45 | in an unrecorded note — not in the filing at all |
| r55 | in a separate simultaneous agreement — not in the filing |
| **#4** | **in a Consolidated Note appended under the same document_id** |
| **#5** | **on the face of the agreement itself** |

**The corrected rule:** the terms are ALWAYS either in the filing or named by
it. The field is not *stated / not stated* — it is **WHICH SERIES HOLDS THEM**,
and answering it requires reading every page under the document_id (L-9), not
reading the agreement alone. #4's agreement says only "the terms and conditions
set forth in the Appendix"; a reader who stopped at the agreement would have
written "not stated" while the full schedule sat eight pages later.

---

## THE SECOND CROSS-CUTTING FIND — THE ARITHMETIC HAS THREE SHAPES

r55 flagged a $792,261.60 gap as suspicious. It was not. **Which shape applies
is determined by WHICH FIGURE the constituents are recited with**, and that is
readable before any subtraction:

| shape | recited as | closes? | members |
|---|---|---|---|
| A | unpaid balance + new money = consolidated | **YES, to the penny** | r13, **#4** |
| B | original principals, no new money = consolidated | **YES, exactly** | **#5** |
| C | original principals, with a balance stated separately | **NO, and should not** | r55 |

#4: $146,943.66 unpaid + $96,656.34 new = **$243,600.00** exactly.
#5: $2,000.00 + $9,000.00 + $9,000.00 = **$20,000.00** exactly.

**Read which figure is recited BEFORE computing.** A gap under shape C is not a
discrepancy; a gap under A or B is.

---

## PREDICTION LOG

### #4 · `2003011000989002` · BRONX · FHA residential CEMA

| # | prediction | result |
|---|---|---|
| 4.1 | CAPITAL·modifies `transacts` | **HOLD** |
| 4.2 | constituents with citations | **HOLD** — Reel 1868 p.1089; the second "to be recorded simultaneously" |
| 4.3 | new money identifiable | **HOLD** — $96,656.34 |
| 4.4 | the arithmetic closes | **HOLD** — to the penny |
| 4.5 | restated terms on the page | **PARTIAL FAIL** — in the appended Note, not the agreement |
| 4.6 | §255 affidavit appended | **HOLD** — plus a SUPPORTING DOCUMENT COVER PAGE declaring it |
| 4.7 | tax on new money only | **HOLD** — Taxable Mortgage Amount = $96,656.34 exactly |
| 4.8 | principal in words AND figures | **HOLD** — and they MATCH, on both principal and rate |
| 4.9 | VALUE does not fire | **HOLD** |
| 4.10 | rd `amount` reads $0.00 | **FAIL** — rd.amount = **$243,600.00** |

### #5 · `BK_7030040000013` · BROOKLYN · 1970 film

| # | prediction | result |
|---|---|---|
| 5.1 | CAPITAL·modifies `transacts` | **HOLD** |
| 5.2 | constituents in the body, not exhibits | **HOLD** — three mortgages recited on p1 |
| 5.3 | restated terms NOT on the page | **FAIL** — fully on the page |
| 5.4 | no §255 in the file; tax from backer stamps | **HOLD** — "NO MTGE. TAX PAID" + an "AFFIDAVIT" stamp |
| 5.5 | the arithmetic may not close | **FAIL** — closes exactly, on original principals |
| 5.6 | a spread means >1 estate or parcel | **HOLD** — three parcels |
| 5.7 | consideration nominal | **HOLD** — $1.00 |
| 5.8 | the 1978 discharge is a chain expectation | **HOLD** |
| 5.9 | rd `doc_date` holds the recording date | **HOLD** — 3/17/1970 rec. vs 5 March 1970 executed |
| 5.10 | true caption on the backer; catch-all rescued by remarks | **HOLD** |

---

## SURPRISES — #4 (9)

1. **AN FHA FORM FAMILY.** FHA Case No. 374-4098988-703; "NEW YORK FHA
   CONSOLIDATION EXTENSION AND MODIFICATION AGREEMENT 1/96"; "FHA Multistate
   Fixed Rate Note 10/95". The spec knew only Fannie/Freddie 3172 and 3033.
2. **THE HOLDER CHAIN RIDES A RECORDED ASSIGNMENT.** Both mortgages assigned to
   WELLS FARGO HOME MORTGAGE INC., the first cited at Reel 1868 Page 1099.
   ⚠ This QUALIFIES R13-2, which said the chain rides corporate succession and
   warned against demanding an assignment that never existed. **Both happen.
   Determine which; assume neither.**
3. ⚠ **THE REGISTER INDEXES THE ORIGINATOR, NOT THE HOLDER.** The cover names
   MGN FUNDING CORP. as MORTGAGEE although both mortgages had been assigned to
   Wells Fargo. **A title search on Wells Fargo does not reach this document.**
   INDEXING-DEFECT class, new shape.
4. **A PACKAGE SIBLING IS NAMED ON THE COVER** — Cross Reference Document ID
   `2003011000989001`, the new $96,656.34 mortgage. r54's capture gap, handed
   to the reader by the register.
5. **TAX $0.00 AGAINST A STATED TAXABLE AMOUNT OF $96,656.34** — because the
   tax was collected on the sibling instrument, not here. Earned three ways:
   the cover block, the §255 affidavit, and clerk marginalia reading
   "TAX pd. $3004" and "TAX pd $1909" (R13-2's handwriting rule, fired).
   $3,004 on $150,220.00 is exactly 2.00%.
6. **A ZIP DISCREPANCY INSIDE ONE FILING** — the affidavit says 10472; the
   cover and the note both say 10461.
7. **THE AFFIDAVIT MISNAMES THE RECORDING OFFICE** — "County Clerk's Office of
   Bronx County" for an instrument recorded with the City Register.
8. ⚠ **TWO LOAN NUMBERS** — Note "Loan ID 0025696097" vs Mortgage
   "Loan No. 0025690497". Not settled at this resolution; one may be a misread.
9. **THREE PAGE-COUNT NAMESPACES, ALL DIFFERENT** — cover 15, rd 17, pdf 20
   (R40-1). The 5-page excess is the supporting series: cover page + §255
   affidavit, filed twice.

## SURPRISES — #5 (7)

1. ⚠ **THE HOLDER IS A DEAD MAN'S ESTATE.** BERT W. SEIDENBERG, Executor of the
   Estate of SAMUEL SEIDENBERG, holds all three mortgages. The constituents run
   to **Fannie** Seidenberg (1946, twice) and **Samuel** Seidenberg (1955) — a
   family lending chain across two generations, and the holder chain resolves
   by **probate**, not by assignment or succession. A third mechanism.
2. **A PRINTED STANDARD FORM WITH STRUCK-THROUGH TEXT** — NYBTU Form 8026
   (9-63). The deletions are part of the instrument (R34-3's deletion layer,
   arriving on a CEMA for the first time).
3. **NO NEW MONEY AT ALL.** A pure consolidation — which is why the tax is
   zero, and it is the cleanest instance of the §255 logic in the corpus.
4. **THE ARITHMETIC CLOSES ON ORIGINAL PRINCIPALS** — shape B, new.
5. **THE SPREAD IS PARCEL-TO-PARCEL, NOT ESTATE-TO-ESTATE.** The Liber 9406
   p.602 lien is spread over Parcels II and III; the p.606 lien over Parcel I.
   r55 spread across leasehold and fee; r45 forbade merger. **Three different
   moves, all called "spread".**
6. **A PREPAYMENT PREMIUM** — 2% of the unpaid balance, after 1973-01-10, on 30
   days' written notice.
7. **A 24-YEAR-OLD CONSTITUENT** — the 1946 mortgages were still live in 1970.

---

## WHAT THIS COST, AND WHAT IT BOUGHT

Two documents. Sixteen surprises, four failed predictions, three corrections to
the spec, and one rule (the arithmetic shapes) that resolves a finding r55
delivered as an open question.

**Compare with the old loop:** two runs would have produced two prose verdicts,
two letter grades, and one or two new cards. Nothing from run N would have
reached run N+1 except by recall.

**The number to watch is SURPRISE: 9 and 7.** It is high because the spec was
built on three members. If members 6 and 7 do not bring it down, the class is
not converging and the method is not working.
