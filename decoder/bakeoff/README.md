# Proposer bake-off — portable kit

Self-contained. 21 MB. Copy the whole folder to any GPU box (Torch), serve a
model, run, score. Nothing here reaches ACRIS or needs credentials.

```
keys/    3 hand-read answer keys, written BEFORE any OCR ran
pages/   26 page images, 1800px, the same pages the keys describe
run.py   one engine over all 26 pages -> out/<engine>/
report.py  the matrix + the pairwise number that decides the architecture
score.py   the scorer, unchanged from the main decoder
```

## Why this exists

Every accuracy figure in this project comes from `tesseract`, `rapidocr` and
`Qwen3-VL-4B` — a 2025 generation. The 2026 leaderboards are led by models a
quarter the size. This kit measures whether that transfers to **1967 microfilm
with handwriting and a sideways backer**, which is not what OmniDocBench
measures.

## The candidates

| slot | model | size | why |
|---|---|---|---|
| proposer | GLM-OCR | 0.9B | OmniDocBench 94.62, fastest |
| proposer | PaddleOCR-VL-1.5/1.6 | 0.9B | 94.50 / 96.33, built for messy scans |
| proposer | FireRed-OCR | 2B | Qwen3-VL base, trained against hallucination |
| proposer | HunyuanOCR | 1B | densest output; license needs legal review |
| verifier | Qwen3.8-27B dense | 27B | fits one H100; adjudicates, doesn't transcribe |
| baseline | Qwen3-VL-4B | 4B | the incumbent — must be beaten to justify a switch |

⚠ **Run the incumbent too.** Without `qwen3-vl-4b` in the same table on the same
pages, a new engine's number cannot be compared to anything already measured.

## Protocol

```bash
vllm serve zai-org/GLM-OCR --limit-mm-per-prompt image=1 --port 8000

python run.py glm-ocr --model zai-org/GLM-OCR --url http://127.0.0.1:8000
python run.py glm-ocr --model zai-org/GLM-OCR --url http://127.0.0.1:8000 --rot
python report.py
```

Rules, each one bought with a measurement:

1. **Same minimal prompt for every engine.** A domain-calibrated prompt was
   tested on the book document (2026-08-12) and scored **86% against the generic
   prompt's 92%** — 830 more words, 5 fewer facts. Naming the fields turns a
   transcriber into a form-filler. Per-engine prompt tuning also makes results
   non-transferable.
2. **Rotation is a variant, not a prompt.** The backer block is recovered by
   rotating the page and by nothing else — not by a richer prompt, not by a
   dedicated stamp-only second pass. Both variants get run; the delta is the
   real cost of the historical eras.
3. **1400px render.** A width sweep put 1400 ahead of 1800, ahead of native
   2536, ahead of 3200. Native scored **worst**.
4. **A failed call writes no file.** An empty `.txt` is indistinguishable from
   an engine that read the page and found nothing. Opposite findings.
5. **CRITICAL tier only in the headline.** It is the tier every engine is
   genuinely being asked for; `ALL` averages answers to different questions.

## What `report.py` decides

Beyond accuracy it prints two numbers per engine pair:

- **disagree** — one proposer got a fact, the other didn't. *This is the
  verifier's workload.*
- **both miss** — neither surfaced it. No adjudication recovers these.

Those settle whether proposers are worth having at all.

### The arithmetic they feed

Estimates, stated assumptions, **not measurements** — `run.py` produces the real
`sec_per_page` and these get rewritten from it.

Corpus: **148,238,970 pages.** Assume ~1,600 image tokens in, ~800 out, vLLM
continuous batching, one H100.

| configuration | pages/hr/GPU | GPU-hours for the corpus |
|---|---|---|
| 27B dense on every page | ~3,500 | **~42,000** |
| two 0.9B proposers on every page | ~40,000 each | **~7,400** |

Break-even: the cascade stops paying only when the proposers disagree on more
than **~82% of artifacts**. Below that, proposers-then-verifier wins — and it
wins hard at plausible rates:

| disagreement | cascade GPU-hours | vs 27B-everywhere |
|---|---|---|
| 5% | ~9,500 | **4.4× cheaper** |
| 20% | ~15,800 | 2.7× cheaper |
| 50% | ~28,400 | 1.5× cheaper |
| 82% | ~42,000 | break-even |

In wall-clock on an 8-GPU allocation: 42,000 GPU-hours is **219 days**; 9,500 is
**49 days**. That is the difference between a project and a non-starter.

⚠ **One assumption carries the whole table.** It assumes the verifier reads the
*image* only for disagreements, and that structuring the agreed pages happens
from **text alone** — where a text-only model is ~10× cheaper again, having no
1,600 image tokens to prefill. If field extraction turns out to need pixels on
every page, this collapses back to 27B-everywhere and the proposers are
pointless. **Test that explicitly before committing.**

## The verifier test — `verify.py`

The accuracy table above scores **extractors**. It does not test the claim the
whole architecture rests on: that a model reading two disagreeing transcriptions
produces a better one than either. `verify.py` tests exactly that, three ways on
identical inputs:

| config | verifier sees | this is |
|---|---|---|
| `UNION` | — (both readings concatenated, no reasoning) | the baseline to beat |
| `TEXT` | two readings, **no image** | **Option A** — OCR → text reasoner |
| `VISION` | two readings **+ the page image** | **Option B** |

**`VISION − TEXT` is the measured value of the pixels.** Every number in this
debate so far has been an estimate of it; this measures it.

```bash
python verify.py --url http://127.0.0.1:8000 --model Qwen/Qwen3.8-27B \
                 --engines glm-ocr,paddleocr-vl
```

Field names are never shown to the model — it is asked for a corrected
transcription, not a list of named fields. Naming them would tell it what to
hunt for and make the task easier than the real pipeline's.

Gains and regressions are reported **separately**. A verifier can destroy a
correct reading it distrusts, or "fix" a right answer into a plausible wrong
one. A net +1 that is +4/−3 is a coin flip with extra steps, not reasoning.

## Qwen3.8-27B status (checked 2026-08-12)

**Not released.** Alibaba said weights ship the week of 10 August 2026 for both
Qwen3.8-Max and Qwen3.8-27B; as of today there is no official repo, no model
card, and **no named license**.

⚠ **Every `Qwen3.8-27B` currently on HuggingFace is a third-party upload or
placeholder.** Download only from the official `Qwen` org. Precedent on license
is split — Qwen3.5/3.6 shipped Apache-2.0, but Max-class went closed and older
releases used Tongyi Qianwen terms (100M-MAU threshold). Read the LICENSE file
the day it lands; even the restrictive case is fine at BKREA's scale.

**Stand-ins available today** for both the bulk and verifier slots: Qwen3-VL-8B
/ 32B, Qwen3.5-VL-2B / 9B. Run one now so the harness and the baseline exist
before the 27B drops — then 27B is a single extra row, not a new project.

## Is 27B the right verifier

Open question, and the kit can answer it. What is known:

- Qwen3-VL-8B scores **96.1 DocVQA**, Qwen3-VL-4B **95.3** — both clear *every*
  Gemma 3 size including 27B. Parameter count is a poor predictor of reading.
- InternVL3.5-8B: OCRBench 840, MMMU 73.4 — viable, less document-specialised.
- Qwen3.5-9B beats Qwen3-VL-30B-A3B on every vision benchmark.
- **Non-thinking mode scores higher on OCR than thinking mode** (85.4 vs 84.5).

⚠ But the verifier is not doing OCR. It is adjudicating between two candidate
readings while holding the image — a *reasoning* task, where size helps more
than it does for transcription. So the OCR benchmarks above argue against a big
model in the **proposer** slot and say little about the **verifier** slot. Run
the verifier comparison on the pages every proposer missed, not on all 26.

## Not in scope here

Qwen3.8-Max (2.4T MoE, 95B active) is ruled out as a bulk engine: ~4.8 TB just
to hold the weights, ~60 H100s. Its reported strength is object detection and
small-object grounding, which matters only if coordinates come back on the
table. Treat it as a last-resort API call on pages that fail everything —
priced by an escalation rate **that has still never been measured.**
