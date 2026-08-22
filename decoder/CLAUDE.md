# DECODER — read this before touching anything

`source → decoding system (specification · acquisition · extraction · resolution ·
derivation) → product`. The authority for the workflow is `docs/WORKFLOW.md`. The
authority for the tables is the Decoder Data Tables artifact: claim → event → account →
inference, with subject × function × mode carrying quantities and terms.

**Live sync EXISTS and is confirmed** (`docs/sources/acris/LIVE_SYNC.md`) — do not build
more of it now; the full workflow takes a long time to run through and there is time later.

---

## PHASE DOCS — read the one for the phase you are working in

⚠ **THE PHASE DOCS ALREADY EXIST — 1,523 lines. DO NOT WRITE NEW ONES.** On 2026-08-17 I
wrote `SPECIFICATION.md` and `ACQUISITION.md` as if from scratch; both were worse
duplicates of files already sitting in this tree (the existing acquisition doc knows about
**174,142 image-less documents that must never be fetched** — mine did not). They are in
`_archive/duplicate_phase_docs/`. **Append to the existing file; never start a parallel one.**

| phase | doc | status |
|---|---|---|
| 1 specification | `docs/sources/acris/01-specification/` — data · index · selection · workflow | **CONFIRMED** |
| 2 acquisition | `docs/sources/acris/02-acquisition/` — data · workflow | **CONFIRMED** |
| 3 extraction | `docs/sources/acris/03-extraction/` — data · schemas · workflow | **BETA** — OCR policy settled, table-fill in progress |
| 4 resolution | `docs/sources/acris/04-resolution/` — data · workflow | written |
| 5 derivation | `docs/sources/acris/05-derivation/` — data · workflow | written |
| live sync | `docs/sources/acris/LIVE_SYNC.md` | **CONFIRMED** |
| second source | `docs/sources/bis/00-source.md` | scaffolded |

Each phase doc is FOUNDATION (source-agnostic, graduated to `docs/WORKFLOW.md`) then
SOURCE-SPECIFIC. Entries are CALIBRATIONS — value + how it was measured + what it fails
like — never bare configs. A bare `limit_side_len: 736` gets re-litigated; the same number
with "native 2880 scores 91.8% because the detector has a trained scale" does not.

## THE FIVE RULES THAT WOULD HAVE PREVENTED TODAY'S ERRORS

**1 · SEARCH BEFORE YOU WRITE.** There are 261 .py files at root. On 2026-08-17 I built
four scripts that already existed:

| built | already there |
|---|---|
| a `limit_side_len` sweep | `ocr_scale.py` — *"DOES OCR NEED FULL RESOLUTION?"* |
| `vlm_device.py` | `gpu_bench.py` — *"CPU vs DirectML on the Intel Arc 140V"* |
| `rapid_v6.py` | `v6_probe.py` — *"IS PP-OCRv6 WORTH ITS COST?"* |
| a 4-angle union test | `rot_compare.py` — *"UPRIGHT vs ROTATED"* |

Every file's docstring opens with the question it answers. `grep -l "<the question>" *.py`
before writing. The fix usually exists and is unaddressable, not missing.

**2 · ONE VARIABLE AT A TIME, OR YOU WILL NAME THE WRONG MECHANISM.** Four confident
diagnoses were wrong on 2026-08-17 — each from a single measurement:

- "CTC blank collapse drops the digit" → **it was handwriting**; one crop refuted it
- "the 8192 context is the ceiling" → **it crashed at 3,311 tokens**, well under
- "it's a system-RAM wall" → the vision encoder was on the **iGPU** the whole time
- "the VLM reads the handwriting exactly and stably" → **5 later readings disagreed**

Before naming a cause: change exactly one thing and re-measure. Crop and LOOK at the
pixels before theorising about them.

**3 · NEVER REPORT AN IMAGE-READ VALUE FROM ONE LOOK.** Two agreeing runs at one size is
ONE look. Vary **size AND crop**, not just prompt wording. `732441` read as `732441` twice
at 1620 px and `732491` five times at 900–2000 px. A single look invents facts that look
exactly like facts: the p009 signature produced `L. J. Gath` on one of four bands —
correct orthography, plausible surname, entirely fabricated.

**4 · EVERY RATE CARRIES ITS DENOMINATOR, AND COVERAGE ≠ RECALL.** "98.6%" means nothing
without "of 73 CRITICAL artifacts across 4 pages". A reader proven on one corpus is not
proven on another. A counter sitting at zero is a claim to verify, not a result — prove a
new guard fires on known-bad input before believing it.

**5 · DON'T PIPE LONG RUNS THROUGH `grep`.** It block-buffers; a 15-minute device
comparison produced zero output and was lost. Write to a file, then read the file.

---

## MEASURED AND SETTLED — do not re-derive

**OCR policy: v6-tiny · `limit_side_len` 736 · 4 angles · union.**
98.6% of 73 CRITICAL artifacts, 6.1 s/page single-process.

| finding | number |
|---|---|
| more pixels is WORSE | 736 → 95.9%, native 2880 → 91.8%. Detectors have a trained scale. |
| `box_thresh` does nothing | identical 70/73 at .5 / .3 / .2 / .15 |
| `unclip_ratio` 2.2 | finds the single-char `LOT 1`, costs 3 other artifacts |
| union over det-config | **+0.0** — not worth 2× |
| union over scale | **+0.0** — not worth 2× |
| union over ANGLE | **+2.7** — the only axis that pays |
| tier does not lever quality | tiny 95.9% = medium 95.9%, small 91.8% |
| the classifier is 2-class | `label_list: ["0","180"]` — cannot express 270°, the winning angle |
| context is not the VLM ceiling | 32768 was **4× slower**, same answers |

⚠ **RUNTIME BEAT TIER on our known failure.** `LOT 1`: RapidOCR/OpenVINO missed it at
tiny AND medium; **native Paddle v6-medium found it** (`'1'` at [1175,1551]). On Torch the
move is the native runtime, not merely a bigger tier.

⚠ **The vision encoder has been on the Arc iGPU by default** — `-ngl 0` governs the
language model only, `--mmproj-offload` defaults ON. Every image-size limit in this repo
(the 900 px in `route.py`, "1400 hangs the encoder") was tuned around a device placement
nobody chose. **Unresolved — rerun `vlm_device.py` writing to a file.**

---

## THE VLM READS THE READABLE AND MUST CLAIM THE UNREADABLE

Measured behaviour: **printed → reads reliably · blank → refuses reliably · handwriting →
erratic in BOTH directions** (false reads and false refusals, plus one invented name).

Asking the model "can you read this?" asks it to introspect its own confidence, which it
cannot do. **Derive readability from behaviour instead**, and resolve in the right stage:

> a **claim** can hold disagreement; an **event** cannot.
> `unresolved` is a STATE, not a bucket — *a bucket looks like an answer*.

Every reading becomes its own claim with its conditions recorded. The event field resolves
only on agreement; otherwise it stays `unresolved` with the distribution visible
(`{732491: 5, 732441: 2}`). That reads the readable and claims the unreadable without ever
asking the model to judge itself — and a better reader can settle it later, because the
claims are still there.

⚠ **NEVER show the VLM the OCR's candidate for the field it is reading.** Cold, it answers
one way; primed with `73241` it answered `732491` twice. Priming transfers the error. OCR
points at a REGION; it never supplies the value.

⚠ **A dead server is not a reading.** One crash kills the `-np 1` slot and every later
request fails identically — a column of `ERR` rows reads like evidence the model failed.
Restart between configurations.

---

## EXTRACT ONLY WHAT HAS A SLOT

If a value has no home in subject / function / mode / quantity / term, do not spend a
round on it. `732441` is unread by every channel AND fills no field — chasing it was
wasted. Conversely `authority` was READ correctly and thrown away for want of a slot.

The answer keys tier by TRANSCRIPTION completeness, which is not the same denominator as
table-field recall. Score against the tables.

**Self-validating documents beat hand keys at scale** — the 1981 mortgage checks itself
three ways with no human key (`$4,000,000 × 1.5% = $60,000` = the stamp; `40,000 + 10,000 +
10,000 = 60,000`; `387 P.A.S.` = 387 Park Avenue South = Schedule A).
⚠ **BUT THE 1.5% CHECK FALSELY FLAGS EXEMPT DOCUMENTS.** A 2005 HECM has principal
469,342.50, tax **0.00**, `Exemption: 280` — correct, and the check would call it broken.
Every HECM, CEMA and government-backed loan with it. **Read the exemption field or the
scoring function fails where the corpus is most interesting.**

**Vocabulary ledger status is binding.** `rate · duration · share` are `unread — no
extractor yet`, yet extraction asks for `interest_rate` anyway and returned **6.0% on a
1981 mortgage** (real rates were 15–18%). The ledger predicted that. An empty cell beats a
plausible fabrication.

---

## FACTS

Corpus: `devr_pages` 1,180 docs / 42,310 pages / 2.1 GB · `sample_pages` 537 ·
`lease_pages` 148. **Data ≈ 7.9 GB, code + fixtures ≈ 73 MB.** Fixtures are `bakeoff/`
(3 docs, 26 pages, 3 hand keys) — that is the practice set; the rest is accumulated bulk
and does not belong on a laptop.

Machine: Intel Core Ultra 7 266V · Arc 140V iGPU (8 GB carved from the same 16 GB) ·
16 GB total. Running llama-server takes the box to 0.8 GB free and it thrashes. Kill it
when done.

Model: Qwen3-VL-4B-Instruct Q4_K_M + `4B-mmproj-F16.gguf`.

⚠ **If an LLM with OCR does the same job at comparable speed, prefer it over standard OCR.**
Current standing (NOT yet a fair head-to-head): VLM-alone 96.4% blended over 21 pages;
v6-tiny × 4 angles 98.6% over 73 artifacts / 4 pages, at 6.1 s/page vs ~30–60 s/page for
the 4B on this CPU. Different denominators — **run the head-to-head before concluding.**

## SECURITY

Credentials live in `C:\dev\acris-decoder.env` — never print them. **Do not build a bulk
image scraper and do not work around bot detection.** On a refusal: stop; do not retry, do
not rotate anything. **Never repair a number to make a check pass** — report the failure.
