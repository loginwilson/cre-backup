---
name: project_acris_extraction_resolver
description: Both engines read ~99% and the RESOLVER is what loses it (85.4% asserted vs 99.2% best engine); the VLM CANNOT read rotated pages (32.5% book) so it must always be fed upright, while OCR gains from angles — and angle diversity pays where engine diversity pays nothing
metadata: 
  node_type: memory
  type: project
  originSessionId: 7c5a3ccb-a88e-40cd-a587-cc575cf7a400
  modified: 2026-08-17T11:33:14.344Z
---

`resolve/fuse.py` + `locate.py` + `score_fused.py` + `export_escalation.py`, built 2026-08-13.
Three channels in, one evidence record out. Extraction settles CHARACTERS only —
roles, amounts and meaning stay in resolution ([[project_acris_resolution_model]]).

**THE SYSTEM FINALLY HAS A NUMBER.** Every prior figure was per-engine (Qwen 98.8%,
Paddle 96.5%). Corpus-weighted CRITICAL artifacts, scored with `score.py`'s own matcher:

| | score |
|---|---|
| best VLM alone | 98.9% |
| OCR alone | 95.7% |
| **FUSED accepted** (both channels agreed) | **86.6%** |
| **FUSED + escalation** (ceiling) | **99.7%** |

The 87.4→98.9 gap is the price of refusing to assert a contested value, and it is
fully recoverable — the ceiling proves the readings are present, just unadjudicated.
Ceiling > best engine is the second channel paying for itself. Gain is almost all in
**book: 85.5% → 97.6%**; digital is 100% on both engines, so there the second channel
buys only the fabrication check. Argues for era-weighted escalation budget, not flat.

**⚠ 2026-08-16 — THE ENGINES WERE NEVER THE PROBLEM; THE RESOLVER IS.** `resolve/channel_audit.py`
cross-tabs every engine on disk against the hand keys at ARTIFACT level (227 CRITICAL,
21 pages). Only **1 of 227** artifacts is unread by every engine — a 0.4% floor. Yet
FUSED accepted was 79.0%. The pipeline was discarding readings it already had.

**⚠ THE VLM CANNOT READ ROTATED PAGES. FEED IT UPRIGHT, ALWAYS.** The evidence records
were wired to `q35-rot` for both historical docs. Same engine family, upright vs rotated:

| doc | VLM rotated | VLM upright | OCR |
|---|---|---|---|
| film | 54.9% | **98.0%** | 94.5% |
| book | 32.5% | **93.4%** | 90.8% |

Rewiring to `q35-fair` moved best-VLM 85.8% → **99.2%** and accepted 79.0% → 85.4%.
OCR is the opposite — it GAINS from rotation (book ppv6-rot 93.8% vs ppv6 90.8%).
The two channels are anti-correlated by orientation, so every fusion so far paired a
strong reader with a blind one and logged the difference as a dispute.

**⚠ ANGLE DIVERSITY PAYS; ENGINE DIVERSITY PAYS NOTHING.** On 65 identical book artifacts:
ppv6 90.8% · ppv6-rot 93.8% · **ppv6 ∪ ppv6-rot 98.5%** (+7.7) · adding rapidpool as a
third engine: **98.5%, +0.0**. Keep Paddle, add angles, do not add a second OCR engine.
(rapidpool 92.3%, tesseract 73.8% — Rapid is NOT better on rotation, that was a guess.)

**⚠ CROSS-ORIENTATION FUSION FAILS AT THE TOKEN LEVEL — MEASURED, DON'T RETRY IT.**
Pairing VLM-upright × OCR-rotated seemed obvious and LOST: 18.1% agreement vs 49.6%
same-orientation, because rotated OCR emits ~3× the tokens in a different reading order
(9,843 with no VLM counterpart). Union at the ARTIFACT level works; alignment at the
TOKEN level does not. Artifacts are what the data tables consume — fuse there.

**⚠ COVERAGE WAS BEING SCORED AS FAILURE.** `score_fused.py` counted a page an engine had
NO FILE for as a page it read and failed. ppv6 book: reported 71.1%, actually **90.8%**
(18 of 24 "misses" were the missing p007). Fixed — each engine now carries its own
denominator and missing pages are reported as missing. Same trap as
[[feedback_bkrea_scale_failure]]: the audit read the filter's own output.

**⚠ 2026-08-16 — THE ARCHITECTURE SETTLED: OCR TRANSCRIBES, VLM PLACES, INDEX VERIFIES.**
Each channel used only where measured strong. OCR = characters + boxes (never loops,
21/21 clean; but returns the page as ONE line — BK p004 came back as a single 7,566-char
line from ppv6, ppbox AND tesseract). VLM = structure (the ONLY channel producing any —
25 lines on that same page at the same char count). Index = scoped to its authoritative
fields. `bakeoff/rapid_ma.py` (OCR, boxes in ORIGINAL page coords via locate.unrotate)
→ `bakeoff/route.py` (VLM places).

**⚠ THE INTERFACE IS THE ANTI-HALLUCINATION GUARD, NOT A FILTER.** The VLM is given
NUMBERED OCR lines and returns LINE NUMBERS only. Invented text becomes unrepresentable
(no field can hold it); an invented index is out of range, which is arithmetic.

**⚠ AND KEY BY LINE, NOT BY REGION — MEASURED, FT p001, same model/page/OCR:**

| | assignments | regions | duplicates | secs |
|---|---|---|---|---|
| region-keyed `{region:[lines]}` | 70 for 44 lines | 11 | **27** | 91 |
| line-keyed `{line:region}` | 42 for 44 lines | 6 | **0** | 59 |

Region-keyed let the model treat the region list as a CHECKLIST: it filled all eleven
rather than leave any empty, giving `signature` and `notary` the SAME line 12 and
`schedule`/`exhibit` the same line 20. That is fabrication in the only form left to a
model that cannot emit text — an invented PLACEMENT. Keyed by line, duplicate keys
collapse, so the failure is impossible rather than detected. Prompt must also say
"most pages use only two or three regions; do not force one."

**⚠ THE PLACEMENT IS REAL — regions came back CONTIGUOUS AND IN DOCUMENT ORDER** on a
1981 film mortgage read from badly garbled OCR (`Security Agrecments)，superior inlien`):
recording_stamp 0-1 (`REEL` / `586 761`) · parties 2-11 · granting_clause 12-17 ·
amount 13-14 (`（$4,000,000）-`) · legal_description 18-24 (`ALL that certain plot`) ·
covenants 25-41 · unplaced 42-43. Region → table: recording_stamp = registration,
parties = TITLE, amount = CAPITAL, legal_description = IDENTITY, covenants =
ENCUMBRANCE, granting_clause = the operative act (mode transacts). ⚠ n=1 page; the
region→function map is a reading, not yet measured.

**⚠ llama-server's VISION PATH HANGS ~1 IN 3 ON A FRESH PROCESS — THIS IS WHY run_cli.py
EXISTS.** Signature: `launch_slot_: processing task` then NO prompt-processing line ever
follows (stuck in image ENCODING, not generating slowly), then the client timeout
cancels. Reproduced twice on freshly started servers between two successes. Do not
"move to the server" as a fix; it needs hang-detect + restart. The CLI never hangs but
reloads 4.7 GB per page (~7 min/page on CPU), and CLI with `-ngl 99` dies with
`ggml_vulkan: device lost on Vulkan0` — reproduced with the machine IDLE, so it is the
Vulkan path, NOT contention with Paddle (an earlier reading of mine blamed Paddle).
Working server call: `-ngl 99 -c 8192 -np 1`, `cache_prompt:false`, thinking off → 59-76s/page.

**⚠ RAPIDOCR THROUGHPUT, HONEST NUMBERS.** 1.14 s/read at 8 procs × 1 thread on 8 cores
(64 reads, model load amortised) → ~15 h for all 47,378 local pages single-angle. The
sub-second figures belong to other things: 0.13 s/page is PP-OCRv6 on an **A100** (paper),
4.4 pages/s is **Tesseract** 8-wide (73.8% vs RapidOCR 92.3%), 0.072 pages/s was RapidOCR
from ONE process. ⚠ Paddle produced ZERO pages in ~12 min on 10 film pages × 3 angles here.

**⚠ THE "RAPIDOCR vs PADDLE" COMPARISON WAS NEVER ENGINE vs ENGINE — IT WAS v4-MOBILE
vs v6-MEDIUM.** `rapidocr_openvino` ships `ch_PP-OCRv4_det_infer.onnx` (4.7 MB MOBILE
detector) + `ch_PP-OCRv4_rec_infer.onnx` (10.9 MB), while `pp_doc.py` requests
`PP-OCRv6_medium_det`/`_rec`. RapidOCR IS PaddleOCR's models re-exported to
ONNX/OpenVINO — so every accuracy gap measured between them is a MODEL-VERSION gap,
two generations and one size class, sitting in exactly the component that fails.
⚠ DETECTION is what fails, not recognition: single-character values (`LOT 1`) and
rubber stamps (`1981 OCT 2`) are never emitted as text regions at ANY of 4 angles.
PP-OCRv5 gained ~13 pts end-to-end over v4 with detection gains specifically in
handwriting and degraded/ancient text; PP-OCRv6_medium reports the family's best
average Hmean 86.2%.
**→ THE MOVE IS TO UPGRADE RAPIDOCR'S MODELS, NOT TO SWITCH ENGINES.** RapidAI
publishes v4/v5/v6 in ONNX/OpenVINO, so newer detection can drop into the 1.14 s/read
pipeline without paying Paddle's ~2-month corpus cost on this box. Test before
believing: re-run FT p009/p010 and check whether `LOT 1` and the OCT-2 stamp appear.

**⚠ THE ORIENTATION CLASSIFIER WORKS — MEASURED, AND IT RETIRES THE MULTI-ANGLE SWEEP.**
`pp_orient.py` = pp_doc.py with `use_doc_orientation_classify=True` +
`use_textline_orientation=True`. FT p010 rotated on disk, PP-OCRv6_medium:

| page | classifier OFF | ON | |
|---|---|---|---|
| a000 upright | 1762 chars | 1742 | unaffected (−20, noise) |
| a090 | **556** | **1671** | +200%, recovers to 95% of upright |
| a270 | 1855 | 1832 | unaffected |

⚠ IT IS NOT FASTER — I briefly claimed a 6x speedup and that was a COLD START. The
OFF run's 23.8 min was `a000` alone taking 1281s for one-time model init; its other
pages ran 75s/70s against ON's 76/78/65s. Per-page steady state is the same.
⚠ THE DAMAGE IS ASYMMETRIC: 90° collapsed to 556 while 270° read 1855 — HIGHER than
upright. A probe that only asks "rotated or not" is insufficient; direction matters.

**⚠ BK p007, THE NATIVELY SIDEWAYS BACKER — THE TEST THAT SETTLES ANGLE POLICY.**
18 CRITICAL artifacts, PP-OCRv6_medium, scored on ARTIFACTS not characters:

| config | recall | time |
|---|---|---|
| OFF, angle 0 (today's default) | 77.8% | 59s |
| **ON, classifier** | **94.4%** | **61s** |
| OFF, 4-angle union | 100.0% | 268s |

Classifier = +16.6 pts for +2 SECONDS. Union = +5.6 pts more for +209 s (4.5x), and
its entire marginal gain is ONE artifact (`loan_no`). The classifier recovers `bank`,
`register`, `title_co`, `to_party` — four fields the production config silently drops
on every backer. Nothing is missed by all three, so the page is fully reachable.
**POLICY: classifier ON by default; multi-angle is an ESCALATION for pages still
missing something, never the standing cost** — the same shape as crop escalation.
⚠ MECHANISM: item count is IDENTICAL (70) OFF vs ON while chars go 802 -> 1151. The
classifier does not find more regions; it re-orients the crops so the RECOGNISER can
read them. Detection was never the failure on this page — recognition was.
⚠ ALSO: BK p007 is portrait BY CANVAS (1800x2963). Sideways content inside an upright
page is invisible to any dimension check; only the classifier or a real read finds it.

**⚠ WHY UNION-OF-4-ANGLES IS THE WRONG FIX EVEN THOUGH IT RAISES RECALL.** (1) 4x the
OCR bill — 15 h becomes 60 h for the 47,378 local pages. (2) A union answers "did any
pass read this", which is a CEILING, not an assertion — you still must adjudicate four
readings of one line, whereas the classifier yields ONE correctly-oriented read with
nothing to resolve. (3) It poisons the next stage, measured: `ppv6-rot` (0/90/270
concatenated) emitted ~3x the tokens and token-level fusion against it fell from 49.6%
agreement to 18.1%; routing had to be restricted to angle 0 because all-angles hands
the VLM three garbled duplicates of every line to place.

**⚠ WE DISABLED PADDLE'S ORIENTATION HANDLING AND THEN REBUILT IT BY BRUTE FORCE.**
`pp_doc.py:64-65` sets `use_doc_orientation_classify=False`, `use_doc_unwarping=False`,
`use_textline_orientation=False` — then we ran 0/90/270 passes to compensate, at 3x
the cost. PaddleOCR's own guidance is `use_angle_cls=True` for rotated scans, and
PP-StructureV2's PULC direction classifier measures 99% accuracy at 463 FPS on CPU.
⚠ RapidOCR meanwhile ALREADY runs a cls model (`use_cls: true`,
`ch_ppocr_mobile_v2.0_cls_infer.onnx`) — which is part of why multi-angle measured
+0.0% for it on film. Turn the built-ins ON before paying for extra passes.
Also from the docs: 300+ DPI recommended; PP-StructureV3 does layout + READING ORDER
(the job currently assigned to the VLM — worth measuring against it before scaling).

**⚠ AND RAPIDOCR'S MODELS ARE A CONFIG SWAP, NOT A REWRITE.** Its `config.yaml`
carries plain `model_path:` entries for Det/Cls/Rec, so v5/v6 ONNX detection can drop
into the 1.14 s/read pipeline. Keep v4-mobile while iterating for speed (Login,
2026-08-17: "for the sake of testing we want speed so this iterative feedback flows
quickly"); treat the v6 swap as a later measured change, not an assumed win.

**⚠ MULTI-ANGLE DID NOT GENERALISE — IT IS ENGINE- AND MATERIAL-SPECIFIC.** RapidOCR on
film, n=37 CRITICAL: a0 94.6% · a90 62.2% · a270 70.3% · **union 94.6%, lift +0.0%**. The
earlier +7.7 was PADDLE, on BOOK, n=65. Measure angle policy per doc type; it is a 3× cost.

**⚠ THE VULKAN HANG WAS IMAGE RESOLUTION — ISOLATED, NOT GUESSED.** llama-server's
vision path hung on ~50% of pages (4 of 8) at `prep(width=1400)`. At 900px the SAME
pages complete in 47-77s, 10/10 with ZERO hangs. `-fa off` alone did NOT fix it
(p004/p006 still timed out at 170s), so it is vision-ENCODER work, not attention.
⚠ 900px is a WORKAROUND, not a fix — 1400 was measured best for transcription. The
real fix is a backend that does not choke: this llama.cpp build ships ONLY
`ggml-vulkan.dll` (no SYCL/CUDA/OpenCL), but Intel Level Zero IS installed
(`ze_loader.dll`), so a llama.cpp **SYCL build** is a binary swap and is Intel's
native path for Arc. OpenVINO 2026.3 GenAI is the other candidate.
Working config: `-ngl 99 -c 8192 -np 1 -fa off`, 900px, `cache_prompt:false`, think off.

**⚠ FULL-DOC PLACEMENT SCORE IS 71% OF REACHABLE, NOT THE 100% ONE PAGE SUGGESTED.**
`bakeoff/route_score.py`, FT_1680008647768, 10 pages: 44/71 scored (62%), 44/62 of
artifacts OCR actually reached (71%), 30 ids excluded as unmapped. p001 alone was
12/12 — a single page badly overstates it.

**⚠ AND THE BIGGEST LESSON IS ABOUT THE TABLES, NOT THE MODEL: A FIELD'S REGION IS A
FUNCTION OF THE PAGE, NOT THE FIELD.** Most "misplacements" were MY map being rigid.
`mortgagor` lives in `parties` on p001 and in `signature` on p009 — same entity,
different region, different ROLE. `amount_figs` sits INSIDE the granting clause
(`WITNESSETH…to secure…($4,000,000)`), so `granting_clause` is defensible. `gen_partner`
on p010 is inside the acknowledgment, so `notary` is right. Genuine router errors were
narrow: bare continuation stamps (`586 767`, `586± 768`) read as `other`.
⚠ 30 unmapped ids were ALL covenant provisions the schema never had — `rpl291f`,
`due_on_sale`, `rent_roll`, `ucc_fs`, `carveout`, `judgment`, `stock`. A mortgage's
covenant table needs far more columns than a first guess supplies.

**⚠ EXTRACTION: THE VLM READS VALUES WELL AND CANNOT SELF-ANCHOR — SO COMPUTE THE
ANCHOR, DO NOT ASK FOR IT.** `bakeoff/extract.py` first cut: 44 rows, 12 verbatim,
32 unsupported, 52 bad_shape. But the READINGS are right off a 1981 film scan —
`ELLIOTT BAKST`, `24-0141715`, `September`, `1981`, `NEW YORK`, `Manhattan`,
`Fourth Avenue`, `387 P.A.S.ENTERPRISES`. The failure is the LINE NUMBER: the model
defaults to `line 1` when unsure, so p008 returned block/borough/county/lot/street all
= `586` @ line 1 and p009 returned every ack field = `769` @ line 1. Correct values,
fabricated anchors. FIX: never ask the VLM for the line — search its value back
against the OCR lines in code. The anchor becomes derived and verifiable instead of
claimed, the same move that killed placement duplicates. (Routing works because a line
NUMBER is all it returns; extraction broke because it must return a value AND a number.)

**⚠ THE REAL HALLUCINATION IS A DEGENERATE DECODE LOOP, AND IT IS FREE TO DETECT.**
`resolve/fabrication.py`. Not subtle misreading — the VLM latches onto a pattern and
re-emits it hundreds of times, always on the HARD pages (BK p006/p007, FT p006/p010):

| run | page | pattern | reps |
|---|---|---|---|
| qwen35-2b | BK p007 | `connection with individual property` | 286 |
| qwen35-2b | BK p006 | `david schum david schum` | 273 |
| q35-fair | BK p006 | counter `92394…92644` | 251 |
| qwen | BK p006 | `under section 703 and` | 130 |

BK p006's counter is the tell: p007 carries ONE genuine recording stamp
(`92334 JUL-10-67 92335`) and the model looped it 250× with an incrementing counter.
This alone inflated q35-fair's book unsupported-token rate to 26.8% (262 of 302 digits)
against 3–5% for every other run — and it is the run the resolver was wired to.

**⚠ OCR NEVER LOOPS, WHICH MAKES IT A FREE REFERENCE SIGNAL.** rapidpool clean on 21/21
pages; Paddle/Tesseract show only GENUINE boilerplate (`rents issues and profits` ×8,
`holder this mortgage` ×10) at the same count the VLM shows. So: real text repeats
EQUALLY in both channels, a loop repeats 10–30× more in the VLM. Discriminator needs no
model and no threshold tuning. (⚠ ppv6-rot shows ×30 vs ppv6's ×10 — that is the 3-angle
CONCATENATION, not a loop. Divide by the angle count before comparing.)
`q35-strict`, `qwen4b-fair`, `rapidpool` show ZERO loops (n=3, 6, 21 pages).

**⚠ ppv6-rot IS NOT "ROTATED OCR" — IT IS angles [0,90,270] CONCATENATED** into one text
file by `pp_doc.py`. That is why it emits ~3× the tokens: it contains each page three
times. Any token-level fusion against it is comparing one reading to three.

**⚠ TOKEN-LEVEL SUPPORT CATCHES INVENTED LABELS, BUT NOT ONES BUILT FROM REAL WORDS.**
Against the known `**Document Title**` / `**Signature Block**` case (still on disk at
q35-fair 2015022400608001 p006): 9 of 10 label tokens flagged as unsupported. The miss
was `signature` — genuinely printed on a signature page. Lexical support cannot see a
fabrication that reuses page vocabulary; that needs the placement guard instead.

**⚠ AND THE HAND KEYS CANNOT ARBITRATE PROSE.** They list CRITICAL ARTIFACTS, not full
page text, so an ordinary word the VLM read and OCR missed cannot be rescued and scores
as invented. Only the DIGITAL column reads as a fabrication rate (~1.8–3.6%); film and
book are upper bounds. Do not quote the pooled precision figure.

**⚠ THE VLM FABRICATES AND ONLY THE WEAKER ENGINE CAN SEE IT.** Qwen emitted
`**Document Title**`, `**Header**`, `**Body Text**`, `**Signature Block**` — 9 markdown
section labels describing LAYOUT, none printed on the page (crop reads only
`LR-205k (E) 10-21-2011 / ACKNOWLEDGEMENTS`). Plus an 18-word conversational preamble.
Paddle produced **0 such tokens across 34 pages** — an OCR engine reports regions it
detected and structurally cannot invent a phrase. The 96.5% engine caught the 98.8%
engine's error. This is why the weaker channel stays in the pipeline.
Fixed by `PROMPT_STRICT` in `bakeoff/run.py` (adds "output only characters physically
present… do not add section headings"): p006 labels 4→0, preamble 1→0, word count
2,383→2,393 (unchanged). `--prompt-variant` now recorded in run.json.

**⚠ NEVER ALIGN CHANNELS ON LINES.** The VLM returned 9 lines (one per paragraph);
Paddle returned the same 4,500 chars as ONE line. Line-aligned fusion scored 0.0%
agreement with ZERO disputed runs — an impossible result whose SHAPE exposed it.
Align on tokens. Lines are a per-engine layout artefact.

**⚠ THE CHANNELS ALSO DISAGREE ON ORDER** (VLM = reading order, Paddle = layout order).
difflib assumes monotonic order, so leftovers get labelled disputes. Test: a token
unmatched on BOTH sides was read by both — an alignment artefact, not evidence.
Queue 114 → 80 runs. Classify PER SIDE, never per run.

**⚠ "MISSED" vs "MADE UP" NEEDS GEOMETRY.** Paddle-only tokens are settled (a box exists
→ pixels exist → the VLM missed real text). VLM-only tokens are NOT — only Paddle makes
boxes, so the runs where the question matters most have no coordinates. Fix: bracket
between the nearest AGREED runs, which both channels read and Paddle has boxed.
Location 84% → 97%.

**⚠ CALIBRATION FOUND THE THRESHOLDS WERE NOT THE CONSTRAINT.** Swept sub-block
acceptance 1.0→0.5: weighted accepted moved 87.4%→88.2%, book did not move at all,
ceiling never fell. Book's 54.2% is **coverage**: 2 of 7 pages have only one channel
(1,562 tokens with nothing to check them against). No threshold creates a second reading.

**⚠ ON BOOK, PADDLE NOW BEATS THE VLM — 88.0% vs 85.5%** — and the whole swing is ONE
page: the sideways backer (BK p007). Paddle read it upright once its per-page timeout
went 300s -> 1200s; the VLM still has not, because its rotated passes wedge. Book
accepted 54.2% -> 65.1% from that single page. The "weaker" engine leads on the hardest
material purely on coverage.

**⚠ THE ROTATION FIX SERVES BOTH ENGINES AT ONCE.** Paddle timing out on the backer and
the VLM wedging at 90/270 are the SAME gap - sideways content - hit from two sides.
PRE-ROTATE THE PNGs ON DISK: Paddle then needs no --angles, and the VLM never sees the
expand=True canvas that triggers the llama.cpp wedge (BK p001: 444s, returned
`partial-1/3`, upright pass only - the one angle we already had).

**⚠ TWO SILENT-SUCCESS BUGS, SAME SHAPE, FIXED.** (1) pp_doc.py resolves a RELATIVE
--src against its OWN directory, so `--src bakeoff/pages/X` from the repo root became
`bakeoff/bakeoff/pages/X`, matched nothing, printed "0 pages" and exited 0 - Paddle
processed nothing and reported success. Now raises on an empty page set. (2) The 300s
default timeout killed the densest pages as `NO OUTPUT`. Both made scores collapse
(film 77.2% -> 41.6%) in a way that looked like a quality regression and was coverage.
⚠ ONE PAGE STILL DEFEATS PADDLE ENTIRELY: FT p007, 1200s no output, while its
neighbours take 90-200s. Try a lower --side.

Rotation exists but **no VLM run has ever seen a rotated page** — `R.encode(pg, 0, …)`
hardcoded angle 0 in every run while `run.py` accepted an angle all along. `--angles`
added; rotated boxes now map back via a `unrotate()` verified by single-pixel probe at
all corners/angles (PIL `expand=True` swaps W/H at 90/270 — the detail an eyeballed
derivation gets wrong). VLM union keeps a rotated pass only if >60% novel tokens;
naive concatenation would write the upright page 3×.

Export package: `_escalation_export/` — 1.8 MB for 77 crops, `prompts.jsonl` (image +
instruction) shipped, `manifest.jsonl` (candidate readings) kept home, leak-checked.
**Never show the escalation model what the other engines read** — that converts an
independent reading into agreement with a guess. See [[project_bkrea_scale_failure]].
