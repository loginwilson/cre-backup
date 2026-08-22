# ACRIS · PHASE 1 — SPECIFICATION

**Specify inputs: what data and documents are in scope.** Status: **CONFIRMED**.

The general method lives in `docs/WORKFLOW.md`. Everything here is ACRIS-specific and has
not graduated. See `../../../CLAUDE.md` for the rules that bind every phase.

---

## 1 · What ACRIS is the authority for — and what it hands off

⚠ **A DENOMINATOR THAT INCLUDES WHAT THE SOURCE CANNOT KNOW MAKES A FINISHED DECODE READ
AS BROKEN.** A completeness test was once built whose denominator included *"what does the
hotel earn"* and *"when was it built, to what plan"*. ACRIS knows neither and never will.
Scoring against them made a complete decode read as 80% — a number that sends someone back
to re-read pages that could not possibly hold the answer.

⚠ **AND "NOT IN ACRIS" IS A COMPLETE ANSWER, NOT AN OPEN ITEM.** *"The interest rate is
not in ACRIS"* was logged as OPEN. It is closed. ACRIS's job on that question is to tell
you, with evidence, that six generations of lender deliberately kept the rate off the
register. Confirmed again 2026-08-17 on a 2005 HECM: §22 describes the adjustment
mechanism (1-year CMT via H.15(519), ±2.0% periodic, ±5.0% lifetime) and the **rate itself
lives in the Note**, which is not recorded. That is `absent`, not `unread`.

| ACRIS is authority for | ACRIS hands off |
|---|---|
| what documents exist against a parcel | rents, income, operating data |
| parties, priority, recorded money | construction dates and plans |
| the parcel key as the register holds it | as-built condition |

---

## 2 · The support index — pulled once, by partition

**100,764,843 rows across five datasets**, ~1 hour with `pull_index_fast.py`.

⚠ **`$offset` IS THE BOTTLENECK AND IT GETS WORSE AS THE PULL SUCCEEDS.** Measured
2026-08-14 on PARTIES (46.5M rows), 20,000 rows/request:

```
offset          0    1.1 s
offset  1,000,000    4.5 s
offset  5,000,000    7.6 s
```

So **partition, do not page**. The pull is split by a natural key and each partition starts
at offset 0.

⚠ **THE PAGINATION TRAP THAT AFFECTED EVERY DECODER.** `$offset` without `$order` silently
DROPS and DUPLICATES rows while the COUNT stays correct — so every integrity check passes
while the data is wrong. **Always `$order=:id`.** Fixed in the shared `bulk.py`, which is
why it reached every source, not just ACRIS.

---

## 3 · Selection is three layers, and the map lives in three places

```
index         which documents exist          (the support index above)
doc-id        the per-document endpoint      (page count, type, parties)
pages         the image itself               (acquisition, phase 2)
```

⚠ **THE IMAGE URL IS A PURE FUNCTION OF `doc_id`**, so all ~17M access points need nothing
stored. Do not build a URL table.

⚠ **THREE SIDES, THREE PAIRS, NEVER A CHAIN** (`selection_cross.py`):

```
ACRIS      the authority — what documents exist
local      the jsonl map files on this machine
Supabase   document_map — what acquisition will actually read
```

Each can move independently. Checking `ACRIS→local` and `local→Supabase` and inferring
`ACRIS→Supabase` hides the case where two errors cancel. **The authority for what
acquisition reads is `document_map` in Supabase**, not a local jsonl.
Corpus: **17,049,742 documents.**

---

## 4 · ⚠ THE REGISTER IS A PRIOR, NEVER A FILTER

Running every function detector against every document type:

- **CERT** — its *expected* function fires on **2%**, while three *unexpected* ones fire on **27–45%**
- **DEED** — carries ENCUMBRANCE on **18%** (covenants riding in on a conveyance)
- **SUBL** — used for *mortgage* subordination, not lease subordination

A reader that trusted the type code would look for the one thing that is not there. Use the
register's own claim to rank what to check first; never to decide what a document contains.

Confirmed again 2026-08-17: the cover page named the lender as **FINANCIAL FREEDOM SENIOR
FUNDING CORPORATION** while the instrument said *"given to **INDYMAC BANK, F.S.B.**"* —
and the document itself explains it (*"A SUBSIDIARY OF INDYMAC BANK, F.S.B."*). Both true,
at different levels. Picking one loses the other.

---

## 5 · One specialist per type — no generalist fallthrough

`doctype_registry.py` routes **every** ACRIS type to exactly one specialist. Types sharing
a grammar share a specialist: a satisfaction and a termination are the same shape of
instrument (something is released — find WHAT, and what SURVIVES) even though ACRIS names
them differently.

⚠ **WHY THIS IS ENFORCED.** A generalist reads front to back because it does not know what
the instrument contains: **~2.7M tokens and 862 page-reads on ONE parcel, ~10,200 tokens
per claim.** A specialist opens six pages and checks a list.

---

## 6 · What the corpus actually contains

| fact | number |
|---|---|
| documents | 17,049,742 |
| **median parcel** | **12 documents** → ~760 parcels/yr at one-parcel-at-a-time |
| DEVR (development rights) | 1,201 |
| AIRRIGHT | 64 |
| `FT_` microfilm | **35.8%** of pages — and **79% carry NO `document_date`** |
| Personal Property register (coops — UCC only, no deed/mortgage) | 4,547,262 |
| POA | 1,072,246 |

⚠ **SIGNAL TYPES ARE TINY.** DEVR is 1,201 documents out of 17M. Any sampling plan that
draws uniformly will never see them.

⚠ **DROPPING UNDATED DOCUMENTS SILENTLY DELETED 4.8M EARLY RECORDS** from timelines,
because 79% of microfilm has no `document_date`. Date-filter with care; prefer the
recording stamp.

⚠ **STATEN ISLAND IS A SPLIT CUSTODIAN.** ACRIS holds RPTT only; the deeds live at Richmond
County back to 1945. A citywide claim that does not say this is wrong for one borough.

⚠ **`hid_TotalPages` IS ~99.5% RELIABLE** — 1 over-count in 208 documents. Good enough to
plan with, not good enough to treat as an end-of-document test (see ACQUISITION §3).

---

## 7 · Runbook

```
python pull_index_fast.py            # baseline, all five datasets, ~1 h
python pull_index_fast.py --verify   # row counts per partition
python selection_cross.py            # three-way audit, report only  (~20 min)
python selection_cross.py --repair   # populate both sides, then re-verify
```

⚠ `selection_cross.py` is an **AUDIT, not a daily job** — it re-proves 17M documents that
did not move. The daily path is in `LIVE_SYNC.md`.
