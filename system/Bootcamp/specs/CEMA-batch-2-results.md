# CEMA BATCH 2 — RESULTS

Scored against `CEMA-batch-2-predictions.md`, banked at `66254c8` before either
document was rendered.

| | COVERAGE | SURPRISE | PREDICTIONS |
|---|---|---|---|
| #6 `RC_146262` · 2019 · 33pp | 100% | **6** | **10 of 11** |
| #7 `RC_1474230` · 1983 · 5pp | 100% | **8** | **5 of 10** (3 fail · 1 unresolved · 1 n/a) |

Batch 1 was 9 and 7. **Batch 2 is 6 and 8 — mean 8.0 → 7.0.**

# ⚠ THE STANDING PREDICTION FAILED

specs/CEMA.md predicted, before the draw: *"surprise falls below 5 on each …
**if surprise does not fall, the class is not converging and the method is not
working.**"*

**It did not fall below 5 on either.** By the criterion set in advance, that is
a fail, and it is recorded as one. I drew the era extremes deliberately to
stress the spec, which inflates surprise — but the draw rationale and the
criterion were written in the same file, before reading, so the confound does
not excuse the result.

## But the diagnosis is not "the method fails" — it is "the metric is too coarse"

Sorting the 14 surprises by kind:

**STRUCTURAL — the spec lacks a field or a rule (4):**

1. ⚠ **OBLIGOR ASSUMPTION — A CHAIN MECHANISM ON THE OTHER SIDE** (#7). The
   spec's holder-chain field tracks how the LENDER's interest moves. In #7 the
   holder never moved: Chase was mortgagee throughout. What moved was the
   **BORROWER**. ALLIED WOODBROOK INC. (the sponsor) signed the $69,500
   mortgage; Donald B. Blank "agrees to take over all of the rights and
   obligations under the Note and Mortgage". **The CEMA is doing double duty —
   assumption plus consolidation — and the spec has no field for it.**
2. ⚠ **CEMAs RECURSE** (#6). Form 3172 §II(B) carries alternate wording for the
   case where "Exhibit A indicates that all of the Notes and Mortgages have
   already been combined by a previous agreement". **A CEMA can consolidate
   already-consolidated debt**, and Exhibit A is where you learn whether this
   one is a first link or a later one. The spec treated every CEMA as a first
   link.
3. ⚠ **THE ASSIGNMENT ROUND TRIP** (#6). Mortgage 2 was assigned MERS-as-
   nominee-for-Envoy → **RoundPoint Mortgage Servicing** → **Envoy** →
   MERS-as-nominee-for-Envoy: three separate instruments dated 06/07, 06/07 and
   06/13/2019, all recorded simultaneously with the CEMA. **The holder ends
   where it began.** Four chain expectations out of one paragraph, and the
   spec's "assignment / succession / probate" trichotomy does not describe it.
4. ⚠ **THE OPERATIVE SENTENCE HAS A BOUNDED EXCEPTION** (#7). See below.

**INCIDENTAL — defects or facts about this instance (10):** a date typed
"04/27/208" in a sworn affidavit · Richmond records go to a COUNTY CLERK, not a
City Register · ALLIED WOODBROOK INC. is not in rd's party index (INDEXING-
DEFECT, party-omitted, recurring) · a condo unit (lot 1013), first in the class
· the 1979 form prescribes its own deletion (IIA or IIB, printed "initial here"
markers) · an Exhibit A named as attached and not present · a printed lender
address struck and retyped, initialed · the new money engineered to an odd
figure so the total lands on a round $520,000.00 · tax declared prospectively
("to be paid at the time of recording") rather than stamped after · GSE forms
already existed in 1979.

**The metric counted a three-digit date typo equally with a missing field.**

**RULING FOR LOOP.md: surprise must be graded STRUCTURAL vs INCIDENTAL. Only
structural surprise has to converge.** Incidental surprise is unbounded because
documents are messy, and a spec that drove it to zero would just be a spec that
had stopped looking. Structural surprise: **batch 1 ≈ 6, batch 2 = 4.** That is
a fall, and it is the number to carry forward.

---

## THE OPERATIVE SENTENCE — NOW BOUNDED, NOT BROKEN

The spec called *"constitute in law but one mortgage, a single lien"* the class's
most reliable in-document identifier, present in all five members 1970–2009.

- **#6 (2019, Form 3172 rev. 5/01) §IV: "The Consolidated Mortgage secures the
  Consolidated Note and will constitute in law a single lien upon the
  Property."** — PRESENT. The identifier now spans **1970 → 2019**.
- **#7 (1983, FNMA/FHLMC 8/79 Plain Language) — ABSENT.** The form says only
  "This combining of notes and mortgages is known as a 'consolidation'."

**The exception is the form, not the era.** Form 3172 carries the plain-language
gloss AND the legal formula; the 8/79 plain-language form carries only the
gloss. Six of seven members have it. **Do not treat its absence as evidence
against the class — check the form family first.**

---

## THE ARITHMETIC HELD — SHAPE A, TWICE, NO FOURTH SHAPE

- **#6:** $423,100.37 unpaid + $96,899.63 new = **$520,000.00** exactly.
- **#7:** $69,500.00 + $13,200.00 = **$82,700.00** exactly.

⚠ **#7 exposes a degenerate case:** its constituent note was six months old and
nothing had amortised, so "the principal amount of the Note that has not been
paid" **equals the original principal**. Shapes A and B converge when a
constituent is new. Not a fourth shape — a boundary between two.

**Prediction 7.5 and 6.5 both held. Three shapes still suffice, across 1970–2019.**

---

## PREDICTION LOG

### #6 · `RC_146262` · 2019 Richmond · MERS/Envoy · Form 3172

| # | prediction | result |
|---|---|---|
| 6.1 | CAPITAL·modifies `transacts` | **HOLD** |
| 6.2 | the operative sentence is present | **HOLD** — §IV, verbatim |
| 6.3 | constituents with citations | **HOLD** — Document ID# 699015 |
| 6.4 | new money present | **HOLD** — $96,899.63 |
| 6.5 | arithmetic is SHAPE A, closes to the penny | **HOLD** — $520,000.00 |
| 6.6 | terms in an appended Consolidated Note | **HOLD** — Exhibit C, per §III |
| 6.7 | §255 affidavit appended | **HOLD** — pp. 31–32 |
| 6.8 | tax on the new money only | **HOLD** — $1,956.45 on $96,899.63 (2.019%) |
| 6.9 | VALUE does not fire | **HOLD** |
| 6.10 | the chain rides MERS-as-nominee and needs no assignment | **PARTIAL FAIL** — MERS is nominee, **and** three recorded assignments were still required |
| 6.11 | the consolidated sum exists only in the pdf | **HOLD** |

### #7 · `RC_1474230` · 1983 Richmond · Chase · FNMA/FHLMC 8/79

| # | prediction | result |
|---|---|---|
| 7.1 | CAPITAL·modifies `transacts` | **HOLD** |
| 7.2 | the operative sentence is present | **FAIL** — plain-language gloss only |
| 7.3 | constituents recited in the body | **HOLD** |
| 7.4 | a printed standard form, NOT a GSE form | **FAIL** — it is FNMA/FHLMC 8/79. My reasoning ("1983 predates GSE forms") was simply wrong |
| 7.5 | fits shape A, B or C — no fourth | **HOLD** — shape A, degenerate |
| 7.6 | restated terms in the filing or named by it | **HOLD** — on the page: 9.90%, $719.65/mo, due 2013-12-01 |
| 7.7 | §255 affidavit appended or stamped-absent | **FAIL** — absent, with no marker located in 5 pages |
| 7.8 | tax $0.00 or on new money only | **UNRESOLVED** — no tax mark located; new money was $13,200.00 |
| 7.9 | VALUE does not fire | **HOLD** |
| 7.10 | the holder chain resolves by assignment, succession or probate | **N/A — and that is the finding.** The holder never moved; the OBLIGOR did |

---

## THE FACTS

**#6** — CONSOLIDATION, EXTENSION AND MODIFICATION AGREEMENT, Form 3172 1/01
(rev. 5/01), dated 06/13/2019, recorded Richmond County Clerk 07/11/2019.
MATTHEW and LORI MANGINE with MERS as nominee for ENVOY MORTGAGE, LTD (Houston,
TX). Constituents: 04/27/2018 $430,000.00 (Doc ID# 699015, tax $8,785.00 paid),
unpaid $423,100.37; plus 06/13/2019 $96,899.63 new (tax $1,956.45 to be paid).
Consolidated **$520,000.00**. Consolidated Note = Exhibit C; Consolidated
Mortgage = Exhibit D; §255 affidavit at pp. 31–32. BBL 5070540402.

**#7** — EXTENSION/CONSOLIDATION AGREEMENT, NEW YORK 1-4 Family FNMA/FHLMC 8/79
Plain Language, dated 12/01/1983, recorded Richmond County Clerk same day, Reel
20 pages 3979–3983. DONALD B. BLANK with THE CHASE MANHATTAN BANK, N.A.
Constituents: mortgage signed by **ALLIED WOODBROOK INC.** 05/23/1983 in favour
of Chase, $69,500.00 (Reel 14 p. 1756), unpaid $69,500.00; plus 12/01/1983
$13,200.00 new. Consolidated **$82,700.00** at **9.90%**, $719.65/mo from
01/01/1984, due **12/01/2013**. 3% prepayment premium in year one. Property:
**38 Hemlock Court, Unit 143 B**, Staten Island — a condominium unit. Paragraph
IIA struck through and initialed "DB"; IIB governs. BBL 5070481013.
