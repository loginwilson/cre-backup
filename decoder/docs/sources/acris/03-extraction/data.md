# ACRIS · EXTRACTION — THE DATA

What this phase produces and where it lives. The *how* is in
[workflow.md](workflow.md).

## THE SPLIT THAT MAKES THIS PHASE WORK

Extraction produces two things of very different size, and they go to different
places. Confusing them is what would put 10 TB in a database or strand the
resolution phase offline.

| product | size | store |
|---|---|---|
| **accepted page text** — what the channels read | bulk; **unmeasured, plausibly ~300 GB** | **drives**, offline backups |
| **evidence records** — the claims, with provenance | small, queryable | **Supabase** |

⚠ **THE EVIDENCE RECORD IS THE BRIDGE, AND IT MUST CARRY A PATH.** Resolution
runs entirely in Supabase and must be able to point back at the page it is
asserting from. So every record holds `document_id` · `page` · the claim ·
confidence · which channels agreed · **and where the text and the image live on
disk.** Without the path, the online half can never be audited against the
source and the 10 TB becomes unreachable rather than merely offline.

This is what lets acquisition and extraction stay on drives while resolution,
derivation and application run online. They are not two disconnected halves —
the record is the join.

⚠ **The text volume is a GUESS and is labelled as one.** ~2 KB/page × ~148M
pages is arithmetic on an unmeasured average, not a measurement. It decides
nothing until a real sample is measured over film, book and digital eras
separately, which behave differently enough that one number will not cover all
three.

## THE THREE CHANNELS — and why fusion needs all of them

| channel | what it is | what it is good at |
|---|---|---|
| VLM | one model reads every film/book page | the whole page, in order |
| OCR | the weaker text channel | catching what the VLM invents |
| **index** | ACRIS's own structured record | parties, roles, BBLs, types, dates |

⚠ **The VLM fabricates section labels, and ONLY the weaker OCR channel catches
it.** This is why the weaker channel is not redundant and cannot be dropped for
speed. A single-channel read is recorded as `single_channel` — the lowest
provenance grade — precisely because nothing was in a position to disagree.

⚠ **The index channel is the only one that can catch a ROLE INVERSION.** Swap
grantor and grantee and transcription scoring reads 100% — the text is
character-perfect and the meaning is reversed. `party_type` from PARTIES is the
independent witness. This is why selection's index pull is an extraction
dependency, not a nicety.

## PROVENANCE GRADES — recorded per span, worst-wins

`resolve/canonical.py`. Four grades: `image_agreement` · `order_artifact` ·
`disputed` · `single_channel`. A span inherits the worst grade covering it.

⚠ **Never align channels on lines.** Line breaks are a rendering artifact and
differ per channel; aligning on them manufactures disagreement where the
channels actually agree.

## MEASURED — the bakeoff

The bench is 26 pages, **identical pixels for every engine**, in
`bakeoff/pages/`. That fixed set is the only reason engine numbers are
comparable at all.

- fusion: **87.4% asserted / 99.7% ceiling**, vs **98.9%** for the best single
  engine
- ⚠ **Asserted and ceiling are different questions.** 87.4% is what fusion is
  willing to stand behind; 99.7% is what it got right among those. The gap is
  coverage, and **coverage — not the thresholds — has always been the
  constraint.**
- ⚠ **Never ask a model to reconcile or rewrite a page.** Measured **+0 / −12**.
  It repairs nothing and damages what was already right.

## ON DISK TODAY

Everything extracted so far is bench and calibration material over the 1,180
DEVR documents in `devr_pages/`. **There is no corpus extraction output**, and
none will exist until acquisition runs.

## THE ESCALATION LADDER — what the record must be able to say

Login's framing: **resolved** (text, accepted) · **unconfident** (escalate to the
stronger channel) · **unresolved** (not readable). The evidence record must
distinguish these three, because resolution treats them differently and
derivation must never quietly consume an unresolved page as fact.

`resolve/export_escalation.py` is the arm that pulls the middle band out.
