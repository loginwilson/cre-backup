# ACRIS — the source, end to end

**The first source through [the workflow](../../WORKFLOW.md).** This page is the
whole run in one place; each phase folder holds the detail.

Login, 2026-08-14: *"acris goes to specification (which holds the doc id and
index mapping) to acquisition which will go to harddrives/backups/torch scratch,
then through extraction in torch via paddle, qwen, index fusion with final pass
on kimi for scraps, then resolved evidence makes the lineages across chronology
and function, and then we derive things from that as values like $/sf on air
rights transactions... the live sync then measures current state vs live state to
determine delta and assess what needs to live sync into specification again."*

## THE RUN

| # | phase | for ACRIS | where it lands |
|---|---|---|---|
| 1 | **specification** | doc-id map + index mapping | Supabase |
| 2 | **acquisition** | images by doc-id endpoint | drives · backups · Torch scratch |
| 3 | **extraction** | Paddle + Qwen + index → fusion → **Kimi on the scraps** | text to drives, evidence to Supabase |
| 4 | **resolution** | lineages across **chronology and function** | Supabase |
| 5 | **derivation** | values, e.g. **$/SF on air-rights transfers** | Supabase |
| → | **product** | e.g. an air-rights market product | its own database |
| ↺ | **live sync** | current state vs live state → delta → **back into specification** | — |

## 1 · SPECIFICATION — ✅ complete

Two standing tracks: [selection](01-specification/selection.md) (the doc-id map,
17,049,742) and [index](01-specification/index.md) (the support index,
100,764,843 rows, 5/5 exact).

⚠ **The doc id IS the image endpoint** —
`GetImage?doc_id={id}&page={n}`. Nothing to store, nothing to navigate. That is
why acquisition can run straight off the map.

## 2 · ACQUISITION — begins 2026-08-17

~148M pages, ~9.3 TB. 20 TB primary drive, 4 TB SSD backups, Torch as scratch
only. Measured: 4 procs × concurrency 8 → 49 pages/s → ~35 days.

⚠ **The ceiling is ACRIS's image service** (20 ms connect, 6% of the link) —
faster internet buys nothing.
⚠ **Never build a bulk image scraper and never work around bot detection. On a
refusal: stop.**
⚠ **`source_document` is unwired** — the one blocker. Without it the queue never
shrinks and a restart re-fetches everything.

## 3 · EXTRACTION — three channels, then escalation

| channel | role |
|---|---|
| **Paddle** | OCR — the weaker channel, and the only one that catches VLM fabrication |
| **Qwen** | VLM — reads every film/book page |
| **index** | ACRIS's structured record — the only thing that catches a role inversion |
| **Kimi** | **escalation on the scraps only**, not a fourth channel |

⚠ **Kimi is for what fusion could not settle, never a general pass.** The ladder
is resolved (text accepted) · unconfident (escalate) · unreadable (unresolved) —
and an `unresolved` page must stay visible as a known gap, or a hole reads as a
zero downstream.
⚠ **Never ask a model to reconcile or rewrite a page** — measured **+0 / −12**.
⚠ **Never align channels on lines** — line breaks are a rendering artifact.

## 4 · RESOLUTION — one graph, two traversals

**Chronology** (time primary) and **functional lineage** (function primary) read
the *same* events. Two datasets would drift, invisibly, because each would be
internally consistent.

⚠ **Direction, role and effect are first-class from day one.** One air-rights
transfer writes **−SF on the sender and +SF on the receiver**. Bolt direction on
later and that document becomes two unrelated rows whose arithmetic never closes.

## 5 · DERIVATION — the worked example, and why it is a hard one

**$/SF on an air-rights transfer** is Login's own example, and it happens to
require both of ACRIS's worst traps to be handled correctly:

⚠ **The price is not in the index.** `document_amt` is **0 for every DEVR** — the
figure comes from the cover-page RPTT/RETT stamps. The $10 recital is a
**500,000× trap**.
⚠ **The SF quantity is in an EXHIBIT, not the grant.** So the denominator cannot
be read from the instrument page at all.

A $/SF that skips either produces a confident wrong number — which is exactly the
"lagged, wrong and varying" failure this system exists to beat. Signal volume is
small and precious: **DEVR 1,201 · AIRRIGHT 64.**

## ↺ LIVE SYNC — current state vs live state

`selection_daily.py` + `index_daily.py`. Both proven to detect (28,374 and
174,163 rows over a forced window) and they cross-check each other.

⚠ **The delta returns to SPECIFICATION, not to the pipeline generally** — which
is why phase 1 never finishes. Freshness is the product, not maintenance.
⚠ **A daily cannot replace the audit.** A forward-only monitor inherits every gap
it already has and reports clean forever.

## ⚠ WHY WE READ THE DOCUMENTS AT ALL — the index is the floor, not the target

Login, 2026-08-14: *"were trying to read the documents to create a much better
indexed representation of these docs with legitimate parties, $, descriptions,
terms, etc. like the index is so base level and is a poor representation of the
data in a doc."*

**The deliverable is a better index than ACRIS's own.** That reframes the third
channel: the index is authoritative for a *narrow* question — did this party
appear, on which side, what type, what date, which BBL — and it is evidence for
nothing else. Treating it as the answer would cap the system at the quality of
the thing it exists to improve on.

### Entity ≠ person, and the person is the value

| | party |
|---|---|
| index | `123 MAIN ST LLC` — the entity, full stop |
| **document** | `123 MAIN ST LLC, **by John Smith, its Managing Member**` |

The index says the LLC was the mortgagor. Only the instrument names the human
behind the SPE — and that name is the thread linking one single-purpose entity to
the next deal, which is the whole reason a broker cares.

⚠ **So signature, notary and "by ___, its ___" blocks are high-value extraction
targets, and they sit at the END of a document.** Never cap how many pages are
read: the page count is the thing that decides whether the most valuable field in
the document is seen at all.

### The three fields, ranked by what the index can do

| field | index |
|---|---|
| party **role** (grantor vs grantee) | ✅ the only channel that catches an inversion |
| party **identity** (who signed) | ❌ entity only — the person is in the document |
| **money** | ⚠ last resort — right on some types, **0 for every DEVR**, and many documents involve no money at all |
| **legal description · SF** | ❌ not present in any form |

⚠ **A null in money must distinguish "no consideration exists" from "not read
yet".** Many instruments genuinely involve no money; collapsing that to 0 makes a
missing figure and a real zero indistinguishable, and every sum built on it
wrong.

## ⚠ WHAT ACRIS DOES NOT CONTAIN

**Staten Island recordings.** `recorded_borough` has four values only. Richmond
County deeds sit with the County Clerk back to 1945, while LEGALS still carries
207,392 rows referencing Staten Island *properties* — so the parcels are visible
and their conveyance history is not. The shape most likely to read as coverage.
