# ACRIS · PHASE 3 — EXTRACTION

**Status: fusion built and scored. Escalation lane exported, never run. Index
channel pulled but unwired.** Run `python status.py` for live coverage.

## GOAL

Convert the images into **one evidence record per document**: what the page says,
how firmly that was established, and where the reading is still open.

⚠ **This layer settles CHARACTERS, not meaning.** No party gets a role here, no
amount is interpreted, no document type is decided. Those are resolution's job.
Mixing them is how a transcription defect becomes a semantic fact with provenance
attached.

## THE THREE CHANNELS

| channel | what it is | what only it can do |
|---|---|---|
| **VLM** (Qwen) | reads the page | best raw accuracy: 98.9% on our corpus |
| **OCR** (PaddleOCR) | reads the page | **makes boxes** — the only source of geometry |
| **index** (ACRIS structured record) | did NOT read the page | independent of the pixels entirely |

⚠ **The index is attached, never merged.** It is not a third reading — it is what
the source itself recorded. Fusing it character-wise would produce disputes on
every abbreviation and settle nothing. It corroborates *fields*, and it lives in
its own block so no downstream reader mistakes a recorded value for a read one.

⚠ **The weaker engine stays because of geometry, not accuracy.** Qwen emitted 9
markdown section labels — `**Document Title**`, `**Signature Block**` — describing
layout that was not printed on the page. Paddle produced **0 such tokens across
34 pages**: an OCR engine reports regions it detected and structurally cannot
invent a phrase. The 96.5% engine caught the 98.8% engine's fabrication. A better
VLM does not retire this; **Qwen3.8-27B ships with no grounding or bounding-box
output** (card checked 2026-08-14), so Paddle remains the only geometry channel.

## STEPS WE FOLLOW TODAY

```
python bakeoff/run_serial.py --doc <id> --prompt-variant strict   # VLM channel
python bakeoff/pp_doc.py --src <ABSOLUTE path to pages>           # OCR channel
python resolve/fuse.py --doc <id> --vlm q35-fair --ocr ppbox      # evidence record
python resolve/locate.py --doc <id>                               # runs -> pixel regions
python resolve/score_fused.py --json                              # the system's score
python resolve/export_escalation.py                               # crops for the hard tail
```

## THE ESCALATION LADDER — three outcomes, not two

| outcome | when | what happens |
|---|---|---|
| **resolved** | both channels read the same characters | accepted, `established_by = image_agreement` |
| **unconfident** | channels disagree, or one returned nothing | crop escalated to a stronger model, **blind** |
| **unresolved** | the pixels do not establish it | recorded as `[UNRESOLVED]`, never invented |

⚠ **Escalation is blind, always.** The escalation model is never shown what the
other engines read. Showing it converts an independent reading into agreement
with a guess. `export_escalation.py` ships `prompts.jsonl` + crops and keeps
`manifest.jsonl` (the candidate readings) at home — with a leak check that fails
the export if candidate text appears in the shipped half.

⚠ **Escalate only what matters and only what nothing else can supply** — an
amount, a name, a date, a quantity, an identifier. A disputed word in boilerplate
is not worth a model call.

⚠ **Unreadable is not the same as unknown.** Filling a gap from the index is not
automatic: the value is accepted only if nothing else in the document contradicts
it, and only once that field, for that record type, has been checked against the
documents themselves.

## CALIBRATIONS — value · measurement · failure if changed

| setting | where | value | measured | failure if wrong |
|---|---|---|---|---|
| alignment unit | `fuse.py` | **tokens** | line alignment scored 0.0% agreement with ZERO disputed runs — an impossible shape. VLM returned 9 lines for what Paddle returned as 1 | lines are a per-engine layout artefact and change with rotation |
| sub-block acceptance | `fuse.py:FUZZY` | **1.0** (off) | swept 1.0→0.5: weighted accepted 87.4→88.2%, book did not move, ceiling never fell | **thresholds were never the constraint — coverage is.** Tuning here buys ~1pt and hides the real gap |
| run split | `fuse.py:RUN_SPLIT` | **12 tokens** | above this a dispute is structural (one channel skipped a block), not a misread phrase | short runs are crops to escalate; long ones are pages to re-read |
| page key | `fuse.py:page_key` | strips `.png`, `.txt`, **and `.aNNN`** | angle suffixes made 11 "pages" from 7; agreement read 0.18 — a join failure wearing a quality mask, 2026-08-14 | the empty-intersection guard catches a TOTAL join failure, not a partial one |
| Paddle per-page timeout | `pp_doc.py` | **1200s** | 300s killed the densest pages as `NO OUTPUT`; film scored 77.2% → 41.6% and it was coverage, not quality | a timeout regression is indistinguishable from a quality regression in the score alone |
| VLM prompt | `bakeoff/run.py:PROMPT_STRICT` | **strict** | p006 fabricated section labels 4→0, preamble 1→0, word count 2,383→2,393 (unchanged) | baseline invents structural labels the page does not contain |
| rotation novelty | `run_serial.py:NOVEL` | **0.60** | a rotated pass is kept only if >60% of its tokens are new | naive concatenation writes the upright page three times |
| unrotate | `locate.py:unrotate` | right angles only | verified by single-pixel probe at every corner × angle; PIL `expand=True` **swaps W/H at 90/270** | an eyeballed derivation gets the swap wrong and every box lands off-page |
| crop geometry | `export_escalation.py` | `MIN_H=40 PAD_X=24 LINE_H=46` | 77 crops → 1.8 MB; 210 crops → 18.3 MB | too tight and the escalation model loses the context that disambiguates |
| corpus weighting | `score_fused.py` | film 25.5 / book 4.0 / digital 70.5 | the actual corpus shape | an unweighted mean over-reports, since digital is 100% on both engines |

## RULES

1. **This layer does not reason.** Characters only.
2. **Agreement is the unit of confidence, not a model's self-report.** A logprob
   is an opinion about its own output; two independent channels landing on the
   same characters is evidence.
3. **Disagreement is recorded, not resolved.** Silently keeping the better
   engine's run wins most of the time and is wrong exactly where it matters —
   a disputed run is where the page is hard, which is where the value usually is.
4. **Never store the normalised form.** Normalising for comparison is right;
   storing it lowercases a name and eats the spacing in "16 feet 3 inches".
5. **A zero-byte output is a failed read, not an empty page.** The harness has
   written these on HTTP 200.
6. **Coverage before score.** A score over fewer pages is a different question,
   not a better answer.
7. **Never ask a model to reconcile or rewrite a page** — measured +0/−12.

## THE NUMBERS (2026-08-13, corpus-weighted, CRITICAL artifacts)

| | score |
|---|---|
| best VLM alone | 98.9% |
| OCR alone | 95.7% |
| **FUSED accepted** | **86.6%** |
| **FUSED + escalation (ceiling)** | **99.7%** |

Read the gap, not the rank. Accepted *below* the best engine is the price of
refusing to assert a contested value. The ceiling *above* it is what the second
channel and the crops buy. Almost all the gain is book: 85.5% → 97.6%.

⚠ **Book's shortfall is coverage, not accuracy** — 2 of 7 pages had only one
channel, 1,562 tokens with nothing to check them against. No threshold creates a
second reading.

## BUILT / UNWIRED / UNBUILT

- **Built:** `fuse.py` · `canonical.py` · `locate.py` · `score_fused.py` ·
  `sweep_fuzzy.py` · `export_escalation.py`
- **Unwired:** `fuse.py:index_path` (third channel designed in, never connected) ·
  rotation (`--angles` exists; **no VLM run has ever read a rotated page**) ·
  `bakeoff/extract.py` (built, never run)
- **Unbuilt:** the escalation model call itself — crops are exported and have
  never been sent

## TRAPS

- **llama.cpp wedges on rotated multimodal input** — log dies at `processing
  task` with no `prompt processing` line. Pre-rotate PNGs on disk: that fixes
  Paddle's sideways backer AND the VLM wedge with one change.
- **FT p007 defeats Paddle entirely** — 1200s, no output, while neighbours take
  90–200s. Try a lower `--side`.
- **`pp_doc.py` resolves a relative `--src` against its own directory**, so
  `--src bakeoff/pages/X` from the repo root matched nothing, printed "0 pages"
  and exited 0. Always pass absolute paths; it now raises on an empty page set.
- **A wedged `-np 1` slot poisons every later test** — restart the server before
  each diagnostic.
- **Zero-byte files make resume skip them forever.**

## PROMOTED DOCS

None yet re-read against current behaviour. `EXTRACTION_CONTRACT.md`,
`OCR_STRATEGY.md`, `DECODE_EXACTNESS.md`, `DECODE_SHAPE.md` are candidates and
are **history until confirmed**.

Memory: `project_acris_extraction_resolver.md` · `project_acris_ocr_stack.md` ·
`project_acris_vlm_harness_traps.md`

---

## ADDED 2026-08-17 — THE OCR POLICY IS SETTLED (extraction overall remains BETA)

**v6-tiny · `limit_side_len` 736 · four angles · union.**
**98.6% of 73 CRITICAL artifacts across 4 pages, 5.6–6.1 s/page single-process.**

Every entry below is a CALIBRATION: the value, how it was measured, and what it fails like.

| finding | measured | fails like |
|---|---|---|
| **more pixels is WORSE** | 736→95.9% · 1024→95.9% · 1536→94.5% · 2048→93.2% · **native 2880→91.8%** | "use full resolution" is the plausible and wrong instinct; detectors have a TRAINED SCALE |
| `box_thresh` does nothing | identical 70/73 at .5 / .3 / .2 / .15 | tuning it feels productive and changes nothing |
| `unclip_ratio` 2.2 | finds the single-char `LOT 1`, **costs 3 other artifacts** (70→67) | widening every polygon bleeds neighbours into normal text |
| union over det-config | **+0.0** for 2× time | looks like diligence, buys nothing |
| union over scale | **+0.0** for 2× time | same |
| **union over ANGLE** | **+2.7** — the only axis that pays | 4-angle is the whole gain |
| tier does not lever quality | tiny 95.9% **= medium 95.9%**, small 91.8% | contradicts Paddle's published chart (det 86.2 vs 80.6) because that scores general/multilingual per-character and we score ARTIFACT recall on typewritten English |
| the classifier is 2-class | `Cls: label_list: ["0","180"]` | cannot express 270°, which was the winning angle on the sideways backer — it tops out at 94.4% where 4-angle union reaches 100% |

⚠ **RUNTIME BEAT TIER ON OUR KNOWN FAILURE.** The four-round `LOT 1` stall: RapidOCR/
OpenVINO missed it at tiny AND medium; **native Paddle v6-medium found it** (`'1'` at
[1175,1551]). Same model version, different runtime, different answer — the box is being
FILTERED, not missed. **On Torch the move is the native runtime, not merely a bigger tier.**

⚠ **A DOCUMENT IS THE UNIT, NOT A PAGE.** `bakeoff/doc_ocr.py` reads a multipage TIFF or
PDF directly. Ten pages of one mortgage are evidence for ONE event; page-at-a-time produced
19 rows of restated reel number. Four angles yield duplicate lines (2,105 raw → **941
unique, 45%**); collapse them preferring the upright pass, whose box was never transformed.

### The 4B's two jobs, and the guards that transfer to 27B

**1 · pointer** — which region does each OCR line belong to.
**2 · table fill** — what value goes in which field.

Neither job asks it to transcribe. The guards are INTERFACE constraints, so they bind a 27B
on Torch or an 8B in a lab exactly as they bind a 4B:

- returns `{"<line>": "<region>"}` and nothing else → invented text is **unrepresentable**,
  invented index is **arithmetic**
- **keyed by LINE, never by region** — region-keyed let the model read the list as a
  CHECKLIST: 70 assignments for 44 lines, `signature` and `notary` given the SAME line.
  Line-keyed took duplicates 27→0, regions 11→6, and ran 35% faster
- **the anchor is COMPUTED, never claimed** — asked for line numbers it returns correct
  values on fabricated anchors (everything defaults to line 1)
- ⚠ **never show it the OCR's candidate for the field it is reading** — cold it answers one
  way; primed with `73241` it answered `732491` twice. Priming transfers the error.

⚠ **UNPLACED IS NOT A DEFECT.** A covenant page is ~115 lines of boilerplate carrying maybe
two terms; leaving 100 unplaced is correct. The objective is **coverage of the TABLE**, not
of the page. Login, 2026-08-17: *"we are not trying to get every bit of info, we are trying
to fill our data tables with the accurate information."*

### ⚠ THE 1.5% ARITHMETIC CHECK PRODUCES FALSE ALARMS ON EXEMPT DOCUMENTS

The 1981 mortgage self-validates three ways (`$4,000,000 × 1.5% = $60,000` = the stamp).
But `2005082901835001` is a HECM: principal **469,342.50**, tax **0.00**, `Exemption: 280`.
**A `tax ÷ principal = 1.5%` scoring function would flag this correct document as broken**,
and every HECM, CEMA and government-backed loan with it. The check must read the exemption
field, or it fails exactly where the corpus is most interesting.

### Three empty states, and they are different facts

From the same document:
- `interest_rate` — **ABSENT**: §22 describes only the mechanism (1-year CMT via H.15(519),
  ±2.0% periodic, ±5.0% lifetime); the rate lives in the **Note**, which is not recorded
- `signatory` — **UNREAD**: handwritten, two `(Seal)` marks, no channel read it
- `authority` — **INAPPLICABLE**: an individual signed personally, no attorney-in-fact

Collapsing these into one blank loses real information. `unresolved` is a STATE, not a
bucket — *a bucket looks like an answer*.

### ⚠ `principal` CAN BE A CEILING

*"up to a maximum principal amount of"* — on a reverse mortgage the face amount is not money
lent. **`bound` must be `upper`, not `exact`.** This is what the schema's `bound` field
exists for, and it would have been silently wrong.

---

# ADDED 2026-08-17 — THE CASE METHOD (standardised)

**Every document worked by hand produces a case file, and a case file is not a summary —
it is the unit that teaches the system.** Login, 2026-08-17: *"each document we do you will
be teaching yourself on what you learned for how to extract, resolve, and derive."*

Cases live in `docs/sources/acris/cases/<document_id>.md`, indexed by `cases/INDEX.md`.

## WHY A CASE AND NOT A NOTE

A finding written into chat is gone. A finding written as a bare config gets re-litigated.
A case is the only form that survives, because it carries all four things a later reader
needs: the **document** (so the claim is checkable), the **rule**, the **measurement**, and
**who enforces it**.

⚠ **THE CASE IS ALSO THE EVAL.** This is the part that is easy to miss and is the whole
point at scale. The plan is to hand these rules to an open-weight reasoner and run
extraction in parallel. *How will we know when it is good enough?* Not by benchmark claims
— by replaying the case library and diffing against the recorded answer. **Every case
worked today is a test the candidate model must pass.** Without the library, "the open
weight is ready" is a guess. With it, it is a number with a denominator.

## THE FIVE SECTIONS

| section | contains | rule |
|---|---|---|
| **1 · Provenance** | doc id, type, page count, what the file actually held, OCR cost | state the *file* structure, not the cover page's claim about it |
| **2 · Extraction** | the five axes — mode · subject · function · quantity · terms | verbatim operative clause; every quantity carries unit + bound + page |
| **3 · Resolution** | numbered decisions, what settled each, the resolved event, the account | a rejected claim stays attached; `absent` / `unresolved` / `unread` never merge |
| **4 · Derivation** | plain English — what happened, who, the money, what it means | **written so a broker can read it cold.** No jargon, no field names |
| **5 · Rules learned** | tiered by ENFORCER — see below | a rule with no enforcer tier is not finished |

## ⚠ TIER EVERY RULE BY WHO ENFORCES IT — THIS IS WHAT MAKES IT SCALE

The cheapest tier that can enforce a rule is the tier that must. Handing the reasoner work
a regex does is paying inference for arithmetic, and it is the difference between a system
that runs on 17M documents and one that does not.

| tier | enforcer | cost at corpus scale | example from case 2020020400712009 |
|---|---|---|---|
| **CODE** | deterministic check | **free** | `prior_balance + new_advance == principal`; tax components vs stated rate; page-count vs actual frames |
| **MODEL** | the reader | per-document inference | which sentence is operative; is this quantity a face or a balance |
| **HUMAN** | exception queue | rare, expensive | a closure test fails and the document is not obviously wrong |

**Most of what a case teaches is CODE.** Of the six rules from 2020020400712009, four are
deterministic. Write those as checks in the schema, not as prose in a prompt — a prompt
instruction is advisory, a closure test fails loudly.

⚠ **A rule discovered on one document is a hypothesis.** Promote it to the phase doc only
after it has been re-run backward over every earlier case. That is the standing
back-check rule and it applies here: prior cases were judged by rules that predate the
lesson, so they look cleanest where they are most likely wrong.

## ⚠ CORRECTION 2026-08-17 — DERIVATION HAPPENS TWICE, AND THEY ARE DIFFERENT PRODUCTS

Login: *"id even argue extraction, derivation of the extraction, resolution, derivation on
the resolution."* Correct, and the case method above understated it. **Four stages, not
three**, and the two derivations answer different questions:

| stage | produces | question answered | needs a chain? |
|---|---|---|---|
| extraction | claims | what does the paper say | no |
| **derivation of the extraction** | **single-document facts** | **what does this document say about the world** | **NO** |
| resolution | events + accounts | what actually happened | 1+ documents |
| **derivation of the resolution** | **current state** | **what is true NOW** | usually yes |

⚠ **THIS IS WHY IT MATTERS AT SCALE.** The first derivation is available on **every document
on day one**, before any lineage exists. 17M documents each yield shippable facts —
use, parties, capital structure, physical history, boundary constraints — with no chain at
all. Lineage *upgrades* those facts; it is not a precondition for having them.

### ⚠ OPENINGS DECAY. CLOSURES DO NOT.

Measured on FT_4070002230107 (1986 termination, no chain available):

- an **opening** document (mortgage, lease) states a condition that may have ended — a 1986
  mortgage tells you almost nothing in 2026
- a **closing** document (`terminates`, `satisfies`, `releases`) states a condition that
  **cannot reverse** — a 1986 termination is still true in 2026

So a lone terminating document supports **present-tense claims 40 years later**, and a lone
opening document does not. **Weight closures far above openings when deriving current state
from thin evidence**, and never let an unresolved opening decay silently into a fact.

### A DOCUMENT WITH NO LINEAGE STILL EMITS THE SHAPE OF ITS CHAIN

FT_4070002230107 names Reel 1518/442, Reel 1629/1737, two indentures, and a contemplated
successor transfer. **Lineage is the walk's OUTPUT, not its prerequisite** — every legal
description is the parcel's geometry at a moment (proved to 0.002% on Block 1206), and every
recital is a pointer. Do not block the parcel walk on a lineage table that the walk builds.

## CAMPAIGN DECISIONS — 2026-08-24 (login, settled in conversation)

### The extraction-ready gate (defined; enforcement to build)

A document is extraction-ready when it has **passed synchronization**: doc id
+ both urls + recorded_details + pdf + keyed bbl — a pure column test, no
scans. Two edges are part of the definition:

- **`imageless` is a VERDICT, not a gap** — those documents (FT_ era heavy)
  are extraction-ready FROM RD ALONE.
- **`pdf-pass` documents enter extraction UNKEYED by design** — extraction is
  what produces their key (pass 3 closes behind extraction). The gate is
  therefore: keyed via pass 1 or 2, OR carrying the pdf-pass verdict.

### Reader design: single VLM + escalation ladder (the OCR channel is retired)

Modern vision LLMs carry OCR internally; the problem is hallucination, not
reading. Anti-hallucination is structural, not a second weak reader:

- the evidence rule above all: **extract evidence and fact, never infer or
  assume** — inference is hallucination; context-with-proof only
- multi-read bands (vary size and crop, never prompt-priming with candidates)
- **escalation ladder**: a base model reads everything; uncertainty triggers
  (self-disagreement across bands, anchor-region failure, self-validation
  arithmetic failure, cross-grader disagreement) escalate the page to a much
  larger model. ⚠ The model is DELIBERATELY not pinned — chosen when compute
  resources are in hand. Near-term: test distilled/quantized ~4B builds of
  27B-class models in the open harness on the laptop.

### Extraction's three deliverables, in order

1. functional read-through — every page read under the eleven functions
2. events → the clean data table
3. the anybody summary — GENERATED FROM the table (a completeness check,
   never a second author)

Then: grade + why it matters → fixes + record in the Bootcamp → next run.

### Mode: constitution settled, case law accretes through runs

The three modes (transacts / observes / signals) are settled at clause level,
assigned per event never per document — mode is NOT the instrument form and
cannot be derived from doc-type codes (filings fail to capture it; one
document carries many). The open work is `observes` (weak — reliably RECITAL,
not proven observation): the recital-laundering risk. Mode matures one
bootcamp miss at a time; no separate mode project exists.

### Grading: cross-grading replaces bakeoff

bakeoff/extract.py is retired as over-engineering. Its protection moves into
the bootcamp: an open model in a local harness extracts alongside Claude,
each grades the other; disagreement doubles as an escalation trigger (two
models rarely share a hallucination). The draw is self-directed — the model
queues its own clusters (borough/type/era/pages) by where its ledger shows
the least proven coverage.

### Scale context (why the campaign waits on hardware)

Acquisition ≈ 20 days on this machine (network-paced; the source sets the
ceiling). Decoding ≈ 100+ years on this laptop vs WEEKS on serious compute
(~750M pages) — the compute investment is the moat between a decoded
database and everyone who merely packages public rows.
