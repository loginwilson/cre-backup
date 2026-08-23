---
name: project_acris_ocr_stack
description: SETTLED 2026-08-12 — one VLM reads every historical page (Design B); the cheap-cascade-plus-gate design was killed by measuring the gate
metadata:
  node_type: memory
  type: project
  originSessionId: 7c5a3ccb-a88e-40cd-a587-cc575cf7a400
  modified: 2026-08-17T12:40:05.044Z
---

**DESIGN B: one VLM reads the pixels of every film/book page and emits fields. No OCR
proposers, no union, no reconciliation, no trust gate.** Cheap OCR keeps only the digital
class (70.5% of pages, already 100%). Chosen because free Torch compute makes the 4×
compute premium cost wall-clock instead of money — ~39 days on 4 H200 nodes.

Measured against three hand-read answer keys (227 CRITICAL artifacts) built BEFORE any OCR:
`FT_1680008647768` (film 1981), `BK_6730047100023` (book 1967), `2015022400608001` (digital
2015, partial 4/9 pages). n=21 pages — every number here is directional.

## What each configuration actually scores (CRITICAL, transcribed)

| config | film | book | digital | blended |
|---|---|---|---|---|
| tesseract | 70% | 61% | 93% | 86.0% |
| rapidpool (RapidOCR ×8 processes) | 77% | 73% | 98% | 91.5% |
| **Qwen3-VL-4B alone** | 87% | **92%** | 100% | **96.4%** |
| tesseract+rapidpool | 89% | 81% | 100% | 96.5% |
| all three | 95% | 95% | 100% | 98.5% |

**One 4B VLM beats two CPU engines unioned on book, 92% vs 81%.** That is the whole case
for Design B. Third engine adds only +0.5.

## ⚠ THE GATE DOES NOT WORK AS A TRUST BOUNDARY — this killed the cascade

Earlier memory said the trigger "caught 14/14 real failures". **That measured a narrower
question** (does it catch pages where the STAMP was missed) and was being used to justify
trusting cheap OCR everywhere. The real confusion matrix, `bakeoff/gate.py`:

```
21 pages · 10 had ≥1 wrong CRITICAL fact
caught 4/10 (40%) · MISSED 6/21 silently · escalated 9/21 (43%)
```

The silent failures are the shape of the problem: book p006/p007 each had 5–6 wrong fields
(notary, loan_no, rec_tax, title_co, register) while `REC. 471` read perfectly — so the gate
checked the stamp, saw it fine, and passed the page. **It can ask "is the stamp there"; it
cannot ask "is this name right."** Keep the validators as a 1% AUDIT SAMPLE for systemic
breaks, never as the thing that decides a page is correct.

## ⚠ NEVER ASK A MODEL TO RECONCILE OR REWRITE

Given two OCR readings + the page image and told to produce one corrected transcription:
**+0 gained / −12 lost** (text-only: −22). It deleted `REC. 471` and its page numbers as
noise. Additive mode (`union + verifier`) = **+0/−0** — harmless and useless. Same shape as
the domain-calibrated prompt: **86% vs the generic prompt's 92%**, 830 more words, 5 fewer
facts. **Any instruction that makes a model reorganise a page loses facts.**

## Settled operating rules

Generic one-sentence prompt · **1400px** (native scored *worst*) · rotation +90/270 on
`FT_`/`BK_` ONLY and it is the only thing that recovers backers (no prompt substitutes) ·
score per class, never averaged · **transcribed ≠ pointed** (blended 98.5 / 99.7; of 9
artifacts nothing transcribes, 8 are POINTED — box right, characters wrong).

## Rejected, with numbers

`tessdata_best` (worse, 3× slower) · contrast (zero) · Otsu (worse) · inversion (0/6) ·
page-crop (**cut text out**) · native resolution (**worst**) · PaddleOCR (4 attempts, 0
pages) · RapidOCR DirectML (10%) · rec_batch 32/64 · psm12 · domain-calibrated prompts ·
stamp-only second pass (found nothing rotation didn't) · verifier/reconciler layer.

## ⚠ MODEL TIER IS NOT A QUALITY LEVER ON THIS CORPUS — settled 2026-08-17

Login's hypothesis was a hardware ladder: tiny on the laptop, small at a lab, medium under
Torch, buying accuracy at each step. **Measured on 73 CRITICAL artifacts over 4 pages, all
three v6 tiers run on THIS laptop and the ladder does not exist:**

| config | hit/of | recall | s/page |
|---|---|---|---|
| v4-mobile (the old default) | 69/73 | 94.5% | 3.45 |
| **v6-tiny** | 70/73 | **95.9%** | **1.50** |
| v6-small | 67/73 | 91.8% | 4.82 |
| v6-medium | 70/73 | 95.9% | 16.27 |

tiny MATCHES medium at 1/11th the cost and beats small. ⚠ This contradicts Paddle's own
published chart (detection 86.2 medium → 80.6 tiny; recognition 83.2 → **73.5 tiny, below
even v5-mobile**) and both are correct: their benchmark is general/multilingual/scene text
scored per character, ours is typewritten English legal text scored on ARTIFACT recall,
where names and numbers are printed redundantly. **A published tier ladder does not
transfer to a corpus it was not measured on** — cf. [[feedback_decoder_extraction_loop]]
rule 5, a reader proven on one corpus is not proven on another.
**How to apply:** run v6-tiny everywhere; spend lab/Torch hardware on PARALLELISM (more
pages at once), never on a heavier tier.

## ⚠ HEAVIER DETECTION MADE THE KNOWN FAILURE WORSE, NOT BETTER

The four-round extraction stall was `LOT 1` — a single character never detected. Tier was
the obvious suspect and is innocent. Token found immediately right of `LOT` on FT p010:

```
v4-mobile rot0 → '1'      ← the OLDEST model is the ONLY tier that finds it
v6-tiny   rot0 → None
v6-small  rot0 → None
v6-medium rot0 → None
```

Native-Paddle v6-medium DID read it (`'1'` at [1175,1551]) while RapidOCR/OpenVINO
v6-medium does not — same model version, different runtime, different answer. So the box
is being FILTERED, not missed. Swept the det knobs: **`box_thresh` does nothing at all**
(70/73 identical at .5/.3/.2/.15); **`unclip_ratio` is the entire effect** — 2.2 recovers
the `1` and costs 3 other artifacts (70→67), because widening every polygon bleeds
neighbours into normal text. It is not a setting with a right value; it is two jobs.

## ⚠ UNION OVER ANGLES PAYS; UNION OVER DET-CONFIGS DOES NOT

Same channel logic as the resolver (each (engine, angle, det-config) is its own channel),
but only one axis earns its cost:

| policy | channels | recall | s/page |
|---|---|---|---|
| tight · angle 0 | 1 | 95.9% | 1.64 |
| **tight · 4 angles** | 4 | **98.6%** | **6.41** |
| tight+loose · angle 0 | 2 | 95.9% | 3.00 |
| tight+loose · 4 angles | 8 | 98.6% | 11.81 |

The loose channel adds **+0.0** on the scored set for 2× the time. On the sideways backer
alone, 4-angle v6-tiny is the first config to read the page COMPLETELY (18/18, where
angle 0 = 88.9% and the best single angle 270 = 94.4%).
⚠ **RapidOCR's orientation classifier is `label_list: ["0","180"]` — 2-class**, so it
cannot express 270°, which is exactly the winning angle on that page; it tops out at
94.4% where the 4-angle union reaches 100%. And doc-orientation alone adds NOTHING
(77.8% → 77.8%); the gain is textline-orientation or the pair.
**Settled policy: v6-tiny × 4 angles, union.** 98.6% at 6.4 s/page single-process,
1 artifact short of complete across 73.

## ⚠ THE RESIDUAL 1.4% IS HANDWRITING — a modality boundary, not a tuning gap

Login: "98.6% is so close. we need to figure out why it doesn't meet it at 100%." The one
miss is `732441` on FT p010. Fuzzy-searching every channel found it is NOT missed — it is
read as `73241`, one digit short, box `(326,1461)-(816,1627)`. I hypothesised CTC blank
collapse on the double `4`. **Cropping the box refuted that: the number is HANDWRITTEN**,
in pen under the blackletter "Mortgage" — `7,32441 (USR 11836)`. A print-trained CTC
recogniser is simply the wrong reader for a pen stroke; no threshold recovers it.
**So of 73 CRITICAL artifacts the OCR union reads every PRINTED one, and the only failure
is hand-written** — the same modality as the standing unread signatory
(`signature -> person`). Two known unreads, one cause.
**How to apply:** stop tuning OCR for the last point; route handwriting to the VLM, which
is not CTC and is the channel that exists to cross this boundary. Denominator that
matters going forward is PRINTED recall (100%) vs HANDWRITTEN recall (measured separately).
⚠ Always crop and LOOK before naming a mechanism — "CTC collapse" was a plausible,
confident and wrong story that one image killed. See [[feedback_confidence_backcheck]].

## ⚠ MORE PIXELS IS WORSE — the detector has a TRAINED scale, 2026-08-17

Login: "an ocr that cant look at its preferred pixels is only working at half its
capabilities." Reasonable, and measured false for OCR. RapidOCR's config is
`limit_side_len: 736, limit_type: min`, so every page is rescaled before detection.
Isolating ONLY that knob on v6-tiny, angle 0, 73 CRITICAL artifacts:

| side_len | LOT→ | recall |
|---|---|---|
| **736 (default)** | None | **95.9%** |
| 1024 | None | 95.9% |
| 1536 | **1** | 94.5% |
| 2048 | **1** | 93.2% |
| 2880 (native) | None | 91.8% |

**Native resolution is the WORST.** These detectors are trained at a fixed input scale;
feeding 2880 puts glyphs at a size the model never saw. ⚠ And RapidOCR runs on OpenVINO —
**Vulkan is not in the OCR path at all**, so OCR resolution was never a runtime compromise.
Only the VLM path (llama.cpp) ever was.
⚠ But the four-round `LOT 1` stall DOES appear at 1536-2048 and nowhere else, so scale is
a real axis with no single winner — same shape as unclip_ratio. Union over scale was then
measured and adds **+0.0** (736×4angles = 1536×4angles = 736+1536×4angles = 98.6%), so
**736 × 4 angles stays the settled policy** at 6.1 s/page.

## ⚠ STABILITY ACROSS LOOKS IS THE READABILITY TEST — not the model's self-report

Login: "it cant fabricate them and it has to know when the text is just too poor to get a
name." Measured on the same page, same model, same temperature:

| target | asked | answers |
|---|---|---|
| `732441` (hand) | 2 prompts × 2 runs | `732441` **every time** |
| signature (hand) | 4 crops × 2 prompts | `UNREADABLE` ×3, `L. J. Gath` ×1, `Attornethor` ×1 |
| blank control | 2 runs | `NONE` / `UNREADABLE` |

⚠ **THE MODEL SAYING "UNREADABLE" IS NOT SUFFICIENT.** It refused on 3 of 4 signature
bands and GUESSED on the fourth. Running only that band writes `Ariel Gratch` into the
table as `L. J. Gath` — initials, plausible surname, correct orthography, nothing in the
string reveals it is invented. Only repetition exposes it.
**How to apply:** never ask once. N independent looks (different crop bounds AND phrasing);
all agree → `verbatim`; N−1 → `corrected`, flagged; disagreement or majority refusal →
`unread`. Free gate: the VLM reliably tags `[hand]` vs `[print]` per line — a `[print]`
value needs only OCR corroboration, a `[hand]` value must pass the stability test.
⚠ **NEVER SHOW THE VLM THE OCR'S CANDIDATE FOR THE FIELD IT IS READING.** Told "OCR read
this as 73241, correct it" it answered `732491` twice. Priming transfers the error instead
of correcting it. OCR points at a REGION; it never supplies the value.

## ⚠⚠ I REPORTED THE HANDWRITING READ AS "EXACT AND STABLE" AND IT IS NOT — retracted

Same session, hours apart. **What I claimed:** the VLM reads `732441` correctly, "exact,
stable, with a refusal control", so the OCR/handwriting modality boundary is crossed.
**Basis:** 2 runs, one crop, one image size. **What a wider sweep found** — the same crop
at five sizes (`bakeoff/vlm_res.py`), unprimed, temperature 0:

```
 900 / 1200 / 1568 / 2000 px  ->  '732491'  x4     (2560 px timed out)
 earlier, 1620 px             ->  '732441'  x2
```

**5 readings disagree with 2.** The value is UNSTABLE, so `732441` is unread by EVERY
channel — OCR drops a digit, the VLM flips one — and my "decisive" claim was the exact
error I had written a rule against one message earlier: judging readability from too few
looks. What survives: the model refuses on blank paper, and it tags `[hand]` vs `[print]`
per line correctly. Those are real. "It read the number" is not.
**How to apply:** the stability test is not advisory — run it before reporting ANY
handwritten value, including when the first answers agree. Two agreeing runs at one size
is one look, not two. Vary SIZE and CROP, not just the prompt wording.
⚠ And this makes 732441 doubly irrelevant: unread by everything AND holding no schema
slot. See [[feedback_confidence_backcheck]] — re-run every new trap over earlier rounds.

## ⚠ THE VLM CEILING IS RAM, NOT CONTEXT AND NOT VULKAN

The 8192-context ladder crashed at **3,311 image tokens — well UNDER the window**, so the
context-overflow theory (mine) is wrong too. The tell is the timing curve, not the token
count: 900px 4.4s · 1200px 7.1s · 1568px 11.0s · **2000px 89.2s** · 2560px timeout at 424s.
An 8x time jump for 1.6x the pixels is a memory wall on 16 GB shared with the iGPU, not
compute scaling. Practical ceiling on this box: **~1568 px** for a crop.

## ⚠ THE VLM's 900 px CEILING WAS INHERITED FROM A CRASH, NOT MEASURED

Two failures were being conflated: `ggml_vulkan: device lost` was measured on GPU OFFLOAD,
while the 2026-08-17 ConnectionResetError happened at 3600 px on the **CPU path (-ngl 0)**
where the Vulkan backend is not loaded — an ordinary allocation blow-up on a 16 GB
shared-memory box (Intel Core Ultra 7 266V, Arc 140V iGPU carving its "8 GB" out of the
same 16 GB). ⚠ Crop-then-magnify is cheap, magnify-the-page is fatal: a 490 px crop at 3x
(1470 px) ran fine while a full-width band at 2x (3600 px) killed the server.
⚠ OpenVINO already drives this exact GPU well for OCR at 1.5 s/page, so the silicon is not
the limit — llama.cpp's backend choice is. `bakeoff/vlm_res.py` walks the real ceiling.

## Open

**27B is UNMEASURED** — the one assumption Design B rests on. 26-page test, run it first on
Torch. · Gate firing rate at corpus scale (108 unkeyed pages in `render/sample/`). ·
Structured-field extraction never tested (`bakeoff/extract.py` built, never run) — right
characters in the wrong field scores 100% on every metric here and inverts a lineage.

Portable kit: `decoder/bakeoff/` (21 MB, keys + 26 pages + run/report/route/verify/extract/
gate). See [[project_acris_bulk_acquisition]], [[project_acris_document_inventory]],
[[project_acris_decoder]].
