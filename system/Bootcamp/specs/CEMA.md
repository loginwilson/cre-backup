# CLASS SPEC — CEMA (Consolidation, Extension and Modification Agreement)

Built from three banked members, then tested against two drawn for the
purpose. Governed by LOOP.md.

| run | doc | era | custodian | size | consolidated sum |
|---|---|---|---|---|---|
| 13 | RC_1043006 | 2009 | Richmond | 27pp | $408,600.00 |
| 45 | FT_1000000284200 | 1988/89 | Manhattan film | 65pp | $173,000,000 |
| 55 | BK_7140048401460 | 1971 | Queens film | 7pp | $1,575,000.00 |
| b1-4 | 2003011000989002 | 2002/03 | Bronx ACRIS | 20pp | $243,600.00 |
| b1-5 | BK_7030040000013 | 1970 | Brooklyn film | 8pp | $20,000.00 |
| b2-6 | RC_146262 | 2019 | Richmond | 33pp | $520,000.00 |
| b2-7 | RC_1474230 | 1983 | Richmond | 5pp | $82,700.00 |

**SEVEN members, 1970 to 2019**, five custodians, residential through
mega-commercial. **Status: OPEN.** Surprise 9, 7 (batch 1) then 6, 8
(batch 2) — the raw number did not fall and the standing prediction FAILED.
⚠ **Graded by kind, structural surprise went 6 → 4.** See
CEMA-batch-2-results.md and LOOP.md §VII. The class closes when two
consecutive members add no STRUCTURAL surprise.

---

## 1 · IDENTITY — how to recognise it

**The shelf is usually right, and when it is wrong it is wrong differently
each time.** Five members, five type situations:

| run | register type | true caption |
|---|---|---|
| 13 | CONSOLIDATION | accurate |
| 45 | BUILDING LOAN MORTGAGE | a STACKED caption — consolidation is one clause of six |
| 55 | SUNDRY AGREEMENT | catch-all; backer reads CONSOLIDATION AND EXTENSION AGREEMENT, "Spread" added by hand |
| b1-4 | MORTGAGE AND CONSOLIDATION | accurate — the instrument is captioned CONSOLIDATION, EXTENSION AND MODIFICATION AGREEMENT |
| b1-5 | SUNDRY AGREEMENT | catch-all; backer reads CONSOLIDATION AND EXTENSION AGREEMENT, and the remarks name it |
| b2-6 | CONSOLIDATION AGR | accurate |
| b2-7 | CONSOLIDATION AGR | accurate — captioned EXTENSION/CONSOLIDATION AGREEMENT |

⚠ **Do not expect the type to name the class — but do not assume it lies
either.** A 1%-sample measurement (240,000 rows) found 672 of 736 gated
records carrying `CONSOLIDAT` sitting on an accurate CONSOLIDATION shelf —
**91.3%**. The founding three were an unrepresentative sample.

⚠ **AND THE MEASUREMENT IS BIASED IN A KNOWN DIRECTION.** The search key
was the string `CONSOLIDAT`, so a CEMA is found only if its type or remarks
contain it. r55's remarks read `CONS & EXT` — **this search would have
missed it.** 91.3% is an UPPER bound on shelf accuracy; the mislabelled
members are exactly the ones under-counted.

**What actually identifies it, in order of reliability:**

1. **rd remarks.** r55's read `CONS & EXT L 6203 MP 81 ETAL` and named the
   class before a page was rendered (R36-1, confirmed in the field).
2. **The operative sentence.** Some form of *"constitute in law … a single
   lien"* — **present in SIX of seven, across 1970 to 2019** (b2-6's Form
   3172 §IV carries it verbatim). Still the most reliable in-document
   identifier.

   ⚠ **ONE BOUNDED EXCEPTION, AND IT IS THE FORM, NOT THE ERA.** The
   FNMA/FHLMC **8/79 Plain Language** form (b2-7, 1983) carries only the
   gloss — "This combining of notes and mortgages is known as a
   'consolidation'" — and no legal formula. Form 3172 carries BOTH. **Check
   the form family before treating absence as evidence against the class.**
3. **A constituent list** — mortgages recited with liber/reel citations,
   either in the body (r55 four of them, b1-5 three, b1-4 two) or as an
   exhibit (r13 Exhibit A, r45 Exhibit B). Body for small, exhibit for
   large.
4. ⚠ **`amount $0.00` in rd — TRUE ON THREE OF FIVE, NOT A RULE.** r13, r55
   and b1-5 read $0.00; **b1-4 reads the full $243,600.00.** R13-4's
   "the index is amount-blind exactly where the money is" is a TENDENCY,
   not a property. Never infer the class from a zero, and never infer a
   zero from the class.

**Form families** — at least three, and the form tells you where to look:
- **Fannie/Freddie** 3172 (NY CEMA, 1/01 rev. 5/01) + 3033 (consolidated
  mortgage) — r13, b2-6. Restated terms ride as **Exhibit C** (Consolidated
  Note) and **Exhibit D** (Consolidated Mortgage).
- **FNMA/FHLMC 8/79 PLAIN LANGUAGE** Extension/Consolidation Agreement —
  b2-7. ⚠ GSE forms existed by 1979; do not assume a pre-1990s CEMA is a
  bespoke or NYBTU form. The form prescribes its own deletion (IIA *or* IIB,
  with printed "initial here" markers).
- **FHA** "NY FHA Consolidation Extension and Modification Agreement 1/96"
  + "FHA Multistate Fixed Rate Note 10/95", carrying an FHA Case No. — b1-4
- **NYBTU** printed forms, e.g. Form 8026 (9-63), pre-ACRIS, ⚠ with
  **struck-through printed text that is part of the instrument** — b1-5

---

## 2 · THE EVENT — the signature

**CAPITAL·modifies, `transacts`.** **All five, 1970 through 2009.** This is
the class's signature and a deviation from it is a finding.

Additional functions fire with SIZE, not with the class:

- r13 and b1-4 (residential): CAPITAL·modifies alone.
- b1-5 (1970 commercial, 8pp): + IDENTITY `observes` (three parcels).
- r55 (commercial, 7pp): + TITLE `observes`, IDENTITY `observes`, COST.
- r45 (commercial, 65pp): + CAPITAL·**creates** (the new advance as its own
  row), ENCUMBRANCE·creates, COLLATERAL·creates ×2 (assignment of leases and
  rents; UCC fixture filing).

⚠ **VALUE never fires. Five for five.** The consolidated sum is what is
OWED. Every member carries a large number that is not a price and not an
assessment.

---

## 3 · FIELDS

| field | frequency | where it sits | verification | absence looks like |
|---|---|---|---|---|
| **consolidated principal** | ALWAYS | operative clause, in words AND figures | **compare words to figures** — r55's words as typed did not match, corrected by an uninitialed interlineation | never absent |
| **constituent debts** (date · mortgagor · holder · sum · liber/reel cite) | ALWAYS | body list (r55) or exhibit (r13 A, r45 B) | each cite is a chain expectation; count them | never absent |
| **the arithmetic** | ALWAYS present, **NOT always closing** | derived | sum constituents, compare to consolidated | see §4 |
| **new money** | USUALLY | named as a gap mortgage (r13 $17,635.95) or a fresh advance (r45 $10,000,000) | tax is charged on THIS, not on face | r55: none identifiable; the 4th mortgage recorded simultaneously is the candidate |
| **restated terms** (rate · payment · maturity) | **ALWAYS EXIST. LOCATION VARIES — FIVE MEMBERS, FOUR LOCATIONS** | b1-5 on the face of the agreement · r13 in the agreement · **b1-4 in a Consolidated Note appended under the same document_id** · r45 in an unrecorded note · r55 in a separate simultaneous agreement | **the question is WHICH SERIES holds them, not whether they are stated**; read every page under the document_id (L-9) before writing "not stated" | see the ⚠ below |
| **mortgage recording tax** | ALWAYS at issue | cover (modern) or backer stamps (film) | must be EARNED — r55 had a typed audit line AND a "NO MTGS. TAX PAID" stamp | never absent; a $0.00 is a finding, not a blank |
| **§255 affidavit** | ALWAYS RELEVANT, not always present | appended (r13) or stamped-and-absent (r55, "AFFID. FILED") | L-8 both ways | see §4 |
| **estates encumbered** | ALWAYS | operative/granting clause | fee · leasehold · air rights · combinations | never absent |
| **consideration** | USUALLY | recital | nominal ($1.00 r55) — R40-2, not a price | — |
| **parties** | ALWAYS | opening + acknowledgments | read from acknowledgments, not signatures | — |
| ⚠ **obligor continuity** (NEW, b2-7) | **CHECK ALWAYS** | the "take over obligations" paragraph, and the constituents' named mortgagors | ⚠ **compare the mortgagor on each constituent to the party signing.** b2-7's constituents were signed by ALLIED WOODBROOK INC. (a sponsor) and the CEMA is how DONALD B. BLANK **assumed** them — the CEMA doing double duty as an assumption. The holder never moved | same names throughout (r13, b1-4, b2-6) |
| ⚠ **is this a FIRST link?** (NEW, b2-6) | **CHECK ALWAYS** | Exhibit A / the constituent list | **CEMAs RECURSE.** Form 3172 §II(B) carries alternate wording for constituents "already been combined by a previous agreement". Read Exhibit A to learn whether this is a first consolidation or a later one | a flat list of original mortgages |
| **the holder chain** | ALWAYS RELEVANT | recitals, or absent | ⚠ **MECHANISMS SEEN**: recorded assignment (b1-4) · corporate succession with no assignment (r13, "N/K/A" + MERS) · **probate** (b1-5, an executor) · ⚠ **MERS-as-nominee PLUS a chain of assignments that RETURNS TO THE START** (b2-6: MERS/Envoy → RoundPoint → Envoy → MERS/Envoy, three instruments, all recorded simultaneously) | assume nothing; **count the assignment instruments — each is a chain expectation** |

⚠ **THE RESTATED-TERMS FIELD IS THE CLASS'S SHARPEST TRAP, AND THE SPEC GOT
IT WRONG.** Built on three members, it predicted the terms would be
ELSEWHERE. **Both batch-1 members put them closer to hand than predicted**,
in two different places (4.5 partial fail, 5.3 outright fail).

b1-4 is the instructive one: its agreement says only "the terms and
conditions set forth in the Appendix", and the full schedule — 6.250%,
$1,499.89/mo, maturity 2033-01-01 — sits eight pages later in the appended
Consolidated Note. **A reader who stopped at the agreement would have
written "not stated" with the answer in the same PDF.**

---

## 4 · VERIFICATION — the read sheet for this class

Run every one of these before composing. Derived from the class, not invented
per document.

1. **SUM THE CONSTITUENTS AND COMPARE — BUT READ WHICH FIGURE IS RECITED
   FIRST.** ⚠ **THREE SHAPES, and the shape is readable before any
   subtraction:**
   - **A — unpaid balance + new money = consolidated. CLOSES to the penny.**
     (r13; b1-4: $146,943.66 + $96,656.34 = $243,600.00)
   - **B — original principals, no new money = consolidated. CLOSES
     exactly.** (b1-5: $2,000 + $9,000 + $9,000 = $20,000)
   - Confirmed twice more at batch 2, both shape A: **b2-6** $423,100.37 +
     $96,899.63 = **$520,000.00**; **b2-7** $69,500.00 + $13,200.00 =
     **$82,700.00**. ⚠ b2-6 shows the modern pattern — **the new money is
     the odd figure, chosen so the total lands round.**
   - **C — original principals, balance stated separately. DOES NOT CLOSE,
     AND SHOULD NOT.** (r55: $2,367,261.60 originated vs $1,575,000 owing)

   ⚠ **A AND B CONVERGE WHEN A CONSTITUENT IS NEW.** b2-7's note was six
   months old with nothing amortised, so "the principal amount … that has
   not been paid" EQUALS the original. Not a fourth shape — a boundary.

   **A gap under shape C is not a discrepancy. A gap under A or B is.**
   r55 delivered its gap as an open question; the shape answers it.

   Historic detail:
   - r13: $390,964.05 unpaid + $17,635.95 new = $408,600.00 — **to the penny**
   - r45: $163,000,000 + $10,000,000 = $173,000,000 — **exact**
   - r55: $2,367,261.60 originated vs $1,575,000.00 owing — **$792,261.60
     gap, unexplained on the page**
   - **The difference between ORIGINATED and UNPAID is the whole question.**
     r13 recited the unpaid balance, so it closed. r55 recited only original
     principals, so it cannot close and the gap is not a defect. **Check which
     figure the document gives before calling a gap a discrepancy.**
2. **WORDS VS FIGURES on the consolidated sum.** r55 failed this and the miss
   reached delivery. Note any interlineation and **whether it is initialed**
   (the r47 discipline, recovered here).
3. **TAX: find the line AND the exemption.** Never accept a $0.00 or a reduced
   figure from one mark. r13: $331.54 on the new money, justified by the
   appended affidavit. r55: $0.00, earned from two register marks.
4. **§255 AFFIDAVIT — present, or merely stamped?** Both are findings (L-8 and
   its inverse). If present, it is the **price-witness** and carries the prior
   tax paid. If stamped-absent, it is a chain expectation.
5. **ESTATES: is a leasehold involved?** If yes:
   - Is there an **anti-merger covenant** (r45 ¶50(g)) or a **cross-spread**
     (r55, each estate's mortgage made to cover both)? These are opposite
     solutions to the same problem.
   - ⚠ **Is the underlying LEASE named?** r55 never named it and the read
     never asked. **A leasehold with no lease cited is always a chain gap.**
6. **THE HOLDER CHAIN MAY RIDE SUCCESSION, NOT ASSIGNMENT.** r13's Countrywide
   → Bank of America is "N/K/A" — corporate succession, plus MERS as nominee.
   **Do not demand an assignment instrument that never existed** (R13-2).
7. **COUNT THE DOCUMENT NUMBERS.** r13 carried five (cover Document Id · LAND
   DOC stamp · lender's Doc ID · Loan # · Title #) and rd indexed the stamp,
   not the header (R13-3).
8. **CHECK WHAT THE INDEX DROPPED.** r55's remarks kept one liber cite of
   three behind a literal "ETAL" (R11-1). r55's `doc_date` held the recording
   date and lost the execution date.
9. **HANDWRITING IS NOT NOISE.** r13's examiner marginalia carried tax facts
   later confirmed by the typed affidavit (R13-2). r55's backer caption gained
   "Spread" by hand.

---

## 5 · CHAIN — what a CEMA always points at

- **Every constituent mortgage**, by liber/reel and page. Always cited, never
  contained.
- **The §255 affidavit**, when stamped rather than appended.
- **The note or loan agreement**, when the terms are not on the page (r45).
- **A separate extension agreement**, when the extension is by reference (r55).
- **The ground lease**, whenever a leasehold estate is encumbered. ⚠ Missed at
  r55.
- **The deed** that put the current owner in title, when the constituent
  mortgages name a different mortgagor (r55: Ruskin Gardens Inc. → the two
  Ruskin corporations).

---

## 6 · SURPRISES — the learning record

Retrospective for the three founding members. Going forward, one entry per new
member, and **this list is the measurement**: the class closes when two
consecutive members add nothing.

| run | surprise |
|---|---|
| 13 | the §255 affidavit rides IN the package · examiner marginalia carries tax facts · five document numbers on one instrument · holder chain by corporate succession, no assignment |
| 45 | "consolidation" can be one clause of a six-part stacked caption · the constituent schedule can be a 69-year genealogy · anti-merger covenant, contractually forbidding what r43 treated as doctrine · a DECONSOLIDATION in the chain |
| **b1-4** | an **FHA** form family, not just Fannie/Freddie · the holder chain can ride a **recorded assignment** · **the register indexes the ORIGINATOR, not the assignee** — a search on the real holder misses the document · the package sibling is named on the cover · tax $0.00 against a stated taxable amount, because the tax was collected on the sibling · a ZIP discrepancy inside one filing · the affidavit misnames the recording office · three page-count namespaces all differing (15/17/20) |
| **b1-5** | **the holder is a dead man's estate** and the chain resolves by PROBATE · a printed NYBTU form with **struck-through text** (R34-3's deletion layer, on a CEMA) · **no new money at all** · the arithmetic closes on ORIGINAL principals · **the spread is PARCEL-to-PARCEL**, a third meaning of "spread" alongside r55's estate-to-estate and r45's anti-merger · a 2% prepayment premium · a 24-year-old constituent still live |
| **b2-6** | ⚠ STRUCTURAL: **CEMAs recurse** (3172 §II(B)) · **an assignment round trip** — MERS/Envoy → RoundPoint → Envoy → MERS/Envoy, three instruments recorded simultaneously. Incidental: a date typed "04/27/208" in a sworn affidavit · Richmond files with a COUNTY CLERK, not a City Register · tax declared prospectively rather than stamped · the new money engineered to a round total |
| **b2-7** | ⚠ STRUCTURAL: **obligor assumption — the chain moved on the BORROWER side** · **the operative sentence is absent from the 8/79 plain-language form**. Incidental: GSE forms existed by 1979 · a condo UNIT (lot 1013), first in the class · the form prescribes its own deletion, initialed · an Exhibit A named as attached and not present · a printed lender address struck and retyped · ALLIED WOODBROOK INC. signed a constituent and is not in rd's party index |
| 55 | the shelf can be a pure catch-all and rd remarks carry the true class · the arithmetic does not close when only original principals are recited · liens can be cross-spread across leasehold and fee instead of anti-merged · tax zero provable from register marks alone · the extension terms can live in a simultaneous separate instrument |

**Batch 1 scored: 16 of 20 predictions held, coverage 100% on both, surprise
9 and 7.** All three pre-draw predictions came true (terms on the page —
b1-5; appended §255 affidavit — b1-4; residential under an accurate type —
b1-4). The value was in the four that failed, three of which landed on the
restated-terms field.

**BATCH 2 SCORED. The standing prediction FAILED** — surprise was 6 and 8,
not below 5. Recorded as a fail in CEMA-batch-2-results.md. The arithmetic
prediction HELD (shape A twice, no fourth shape); the holder-chain
prediction was N/A on b2-7 because the chain moved on the other side.

⚠ **The diagnosis is that the METRIC was too coarse** — it counted a
three-digit date typo equally with a missing field. Graded by kind,
**structural surprise went 6 → 4**. LOOP.md §VII now defines the split.

**PREDICTED FOR MEMBERS 8 AND 9, recorded now:** **structural surprise ≤ 2
on each.** The two new fields (obligor continuity, first-link) will apply
cleanly. No fourth arithmetic shape. Draw a NON-Richmond, NON-residential
member and one 1990s member — the two thinnest cells left.
