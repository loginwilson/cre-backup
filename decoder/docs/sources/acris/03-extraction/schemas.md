# SCHEMAS — the contract that assures resolution

**A schema is not a field list.** A field list produces a score; a score degrades
quietly. The whole point of this file is that a schema must be able to **fail**.

⚠ **THE ONLY THINGS THAT HAVE EVER CAUGHT A SILENT DEFECT IN THIS PROJECT ARE
CHECKS THAT REFUSE, NOT SCORES THAT DROP.** 2026-08-14: three splitter bugs, none
raised an error, all three caught by one rule — *each dataset compares its own
row count to the live count and refuses to record itself complete otherwise.*
Schemas need the same shape.

**TABLE CHANGE 2026-08-20 (Bootcamp r49):** every event row carries
`doc_type` in PROVENANCE - copied from the navigation index (the raw ACRIS
code, e.g. `DEVR`; labels decode via `_doctype_codes.json`), never read from
the page. Schema consequence: `doc_type` is a REQUIRED provenance field with
establishment rule "index only" - no channel may settle it from the
document, and a page that contradicts it is a FINDING logged against the
index, not a value to overwrite. It feeds the measured type -> function
ledger and the closure test "functions within the type's measured
distribution, else surfaced".

## A SCHEMA HAS FOUR PARTS

### 1. Fields — and required vs optional IS the denominator

⚠ **Without a required set you can never say what was MISSED.** An envelope fact
nobody noticed is indistinguishable from an envelope fact that was not there.
That is the coverage failure this project pays for repeatedly: `pp_doc.py`
reported success over ZERO pages; film "quality" fell 77.2% → 41.6% when nothing
about quality changed. **A score over fewer fields is a different question, not a
worse answer.**

### 2. Establishment rule — WHICH channel may settle this field

Per field, not per document. A channel that cannot see a field must never be
allowed to confirm it.

| field kind | may be settled by |
|---|---|
| party **role** (grantor/grantee) | image channels **+ index** — index is the only thing that catches an inversion |
| party **identity** (who signed) | image only — the index has entities, never people |
| money | image (cover-page stamps) · index only as **last resort** |
| legal description · SF quantity | image only — **absent from the index in any form** |

### 3. Refusal conditions — what makes the field say UNRESOLVED

Stated per field, in advance. If a field can be wrong in a known way, the schema
names that way and refuses rather than guessing.

⚠ **THREE STATES, NEVER TWO.** `present` · `absent_by_nature` · `unread`. Many
instruments genuinely involve no money; collapsing that into the same null as
"not read yet" makes every sum built on it wrong, and makes a real zero
indistinguishable from the DEVR trap where the index reports 0 and the true price
is on the cover-page stamps.

### 4. ⚠ CLOSURE TESTS — THIS IS THE PART THAT ASSURES ANYTHING

Cross-field statements that **must hold**, and fail loudly when they do not.
Not confidence. Arithmetic and logic that close.

**Within a document:**
- A transfer has a sender AND a receiver. One without the other is incomplete by
  construction, not a low-confidence result.
- The SF in the granting clause and the SF in the exhibit must agree. ⚠ If they
  disagree, that is `disputed` — **never pick one**. Silently choosing a winner
  converts the system's one honest uncertainty signal into a confident wrong
  answer (measured: asking a model to reconcile a page scored **+0 / −12**).
- If the instrument states the sender's remaining rights, it must reconcile with
  prior minus transferred.
- Every instrument has at least two sides; the index `party_type` must corroborate
  the roles read from the image.

**Across the lineage — the strongest check available:**
- ⚠ **DEVELOPMENT RIGHTS ARE CONSERVED.** SF leaving a sending lot must arrive at
  a receiving lot. Summed citywide over the envelope lineage, transfers net to
  zero. A non-zero residual is a decode error, a missing document, or a
  misdirected effect — and it is measurable without knowing the right answer for
  any single document.
- A satisfaction must discharge a mortgage that exists and is not already
  discharged.
- An assignment must move a note that was previously created.

**CAPITAL — added 2026-08-17 from the case library (`docs/sources/acris/cases/`):**
- ⚠ **`prior_balance + new_advance == principal`** on any consolidation. Measured exact on
  2020020400712009 (79,586,625.11 + 5,913,374.89 = 85,500,000.00). This is the check that
  separates a REPLACEMENT from an ADDITION — posting the face as new debt inflates the
  subject by the whole prior balance.
- ⚠ **The tax stamp closes on the taxable amount ROUNDED UP TO THE NEXT $100.** All five
  components and the total reproduce to the cent at the statutory rate. Without the
  round-up every component is cents-off and reads like OCR damage.
  **The stamp is the only number in a document a third party verified and banked** — when a
  recital and a stamp disagree, the stamp is the arbiter.
- **`ceiling` and `balance` are different fields.** *"up to"* / *"maximum amount secured"*
  establishes an upper bound only; an account opened from it carries **no balance**. A
  consolidation is the exception — §255 forces the balance into the record.
- **Frame count vs the cover's page count.** More frames than claimed means a SECOND
  document is in the file, announced only on its own cover page.

**Why closure beats confidence:** a per-document score cannot tell you that a
document is *missing*. A conservation residual can.

## HOW THE THREE LAYERS FIT

| layer | shape | job |
|---|---|---|
| detection | type-agnostic scan | does this document touch function F at all? Catches the ZLDA hiding among 920,875 AGMTs |
| **contract** | **by FUNCTION** | what the lineage requires — envelope, ownership, debt |
| reading strategy | **by DOCUMENT TYPE** | *where* those facts live in this instrument |

⚠ **The unreliable input belongs in the hint, never the contract.** The index
`doc_type` and the instrument disagree routinely — which is why
`source_document` carries a separate `true_type`. Selecting the *contract* by
type would inherit that error at step one; selecting the *reading strategy* by
type only degrades a hint.

## THE FIRST SCHEMA, AND HOW TO PROVE IT

**Envelope**, with DEVR and AIRRIGHT as its first reading strategies —
1,265 documents total, small enough to verify every one by hand.

⚠ **1,180 DEVR documents are already on disk** (`devr_pages/`, 42,310 pages), so
the schema can be measured before acquisition delivers anything. The test is not
"what score did it get" but:

1. how many required fields were established, per document — **with the
   denominator printed**
2. how many closure tests passed, failed, or could not run
3. what the conservation residual is across every transfer decoded

⚠ **A schema that passes every closure test on 1,180 documents has been tested on
0.011% of ACRIS and on ONE document type.** Expect it to be wrong in ways only
easements and ZLDAs can reveal.
