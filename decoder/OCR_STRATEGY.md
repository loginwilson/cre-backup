# OCR strategy — every route, measured

**2026-08-10.** Every number here was measured on this machine, on real ACRIS
documents, tonight or today. Where something is estimated it says so. Where an
earlier claim in this project turned out to be wrong, the correction is kept
rather than the original quietly replaced — the wrong numbers are how the right
ones got found.

---

## 0 · The constraint that shapes everything

The tiers have wildly different volumes, so they have wildly different budgets.
Any design that treats them the same is wrong before it starts.

```
TIER                      VOLUME          therefore must be
index every page          140.2M pages    ~free, fast, coordinates
read the cover page        17.0M pages    layout-aware, table-capable
verify a value              ~10M crops    cheap per crop, high precision
read prose the OCR mangled   the residue   expensive, rare, escalated
```

⚠ This is the thing most document-AI writing gets wrong for our case. A pipeline
built for a few hundred invoices can afford a deep model on every page. At 17M
documents the tier that must be nearly free is the one those pipelines treat as
trivial.

---

## 1 · What was measured

### Tesseract 5.4 (binary, free)

```
20,190 pg/hr    12 procs · psm 6 · OMP_THREAD_LIMIT=1 · 8 physical cores
 2,494 pg/hr    single process
13,148 pg/hr    with TSV coordinates, while the mapper competed for CPU
```

Config levers, all measured, all spent:

```
psm 6 vs psm 3            1.15x   (uniform block beats auto layout here)
8 -> 12 processes         1.16x
12 -> 16 processes        0.96x   past the physical core count
batching pages per call   1.00x   process spawn was never the cost
dictionaries off          1.00x
downscale to 150 dpi      0.98x   resize costs what OCR saves
--oem 0 legacy engine     PHANTOM — 346,405 pg/hr at 0 characters.
                          Tesseract 5 ships LSTM-only traineddata; the legacy
                          engine had no model, failed instantly, and "ran fast"
                          by doing nothing. Only caught because recall was
                          printed in the same table as speed.
```

Quality, on 4,271 pages of the stratified sample:

```
                pages   mean conf   words/pg   BLIND (unusable)
modern           2,943      87.0        375       4.1-4.8%
microfilm        1,328      69.9        352      26.4-29.4%
```

### Microfilm — the frame, not the engine

Raw film scored 45.2 conf. Five preprocessing arms — Otsu, autocontrast,
Sauvola, median, upscale — moved it **+0.3**, because ACRIS ships film already
binarised and there is no tone left to threshold.

Cropping the film frame off moved it **+33.0**:

```
raw film      45.2 conf   944 words/page   <- phantom tokens from grain
cropped       78.2 conf   310 words/page
modern scan   89.7 conf   324 words/page
```

⚠ 944 words/page against a modern page's 324 was the tell, and it was visible
in the numbers for hours before anyone looked at the image. **Tesseract was
reading the film grain.** One glance at the page settled what five preprocessing
arms could not.

### RapidOCR / PaddleOCR-ONNX

```
219 pg/hr   CPU
209 pg/hr   DirectML on Intel Arc 140V   <- the integrated GPU gives NOTHING
```

⚠ 92x slower than Tesseract. It can never be a full-page engine at this volume.

But it has a **fixed per-call cost**, not a per-pixel one:

```
8.69 MP full page   19.06s
1.48 MP band         7.22s
0.33 MP tight box    4.69s
0.05 MP value box    3.44s     180x fewer pixels, only 5.5x faster
```

So ~3.4s is overhead per invocation. Which means **tiling amortises it**:

```
10 crops, separate calls   29.30s   22 boxes
10 crops, tiled into one    9.25s   19 boxes   -> 3.2x
```

⚠ Tiling lost 3 of 22 detections at tile boundaries (8px padding). Padding needs
tuning before this is safe.

### Multi-engine consensus — it catches real errors

On the answer-key deed, where the truth was established by reading the images:

```
              TRUTH          TESSERACT           RAPIDOCR
month         MAY            "day of ja" (lost)  "day or MAy"      RAPID WINS
grantor       ALIB, INC.     "WW ALIB, INC."     "ALIB,INC."       RAPID WINS
street        32-44 58 ST    "32-4458 STREET"    "32-44 58 STREET" RAPID WINS
zip           11377          "137)"              absent            BOTH FAIL
```

⚠ `WW ALIB` is the error that would silently break entity matching across the
whole corpus, and Tesseract reported it at high confidence. **Tesseract's own
confidence is not an error detector.** A second engine is.

⚠ But failures correlate on badly degraded regions — on the metes-and-bounds
both engines missed 20.33, 279.67 and 11377 together. When two engines fail the
same way, agreement becomes false confidence. Token overlap was only 143 of
572/397, so they are not generally correlated; the correlation is specific to
degradation.

---

## 2 · Every route considered

### Index tier — every page, 140.2M

```
Tesseract         20,190 pg/hr · free · coordinates          CHOSEN
RapidOCR/Paddle      219 pg/hr                               92x too slow
Surya / docTR     deep learning, needs a real GPU            no GPU here
commercial API    ~$1.50/1,000 pages -> ~$210,000            unaffordable at
                                                             this volume
```

⚠ Nothing competes. The index tier is settled and further tuning here buys
nothing — six configurations measured, all within noise.

### Layout / table tier — the cover page, 17.0M pages

**This is the worst-performing component in the system and the biggest available
win.**

```
stamp bound on   11 of 537 documents = 2.0%
```

The cover page is a two-column table. Tesseract reads straight across it, so the
label lands on a different line from its value:

```
NYC Real Property Transfer Tax:
Exemption: | $ 155,503.36
```

The characters are perfect. The **binding** is destroyed. No page-segmentation
mode fixes it — psm 1, 3, 4, 6, 11 and 12 all fail, because the columns genuinely
interleave in reading order.

⚠ And a hand-written spatial rule made it worse: it bound the FILING FEE on 150
consecutive 2003 cover pages at 96% OCR confidence, silently, because the older
form's label runs on into "Filing Fee" and the offsets are nearly identical to
the transfer-tax row on the 2014 form.

Candidates, none yet tested:

```
Docling (IBM)          layout + table structure + boxes, local, needs torch
PaddleOCR PP-Structure table recognition, ONNX — runtime already installed
Surya                  strong layout, GPU-hungry
Azure DI / Textract     excellent tables, ~$1.50/1,000 -> ~$26k for 17M covers
LayoutLMv3             best-in-class, needs training data we don't have yet
```

⚠ The economics differ completely from the index tier: **one cover page per
document**, not every page. 17M instead of 140.2M. A slower, better engine is
affordable here in a way it never is on the index.

### Verification tier — is this value right

```
Tesseract confidence     NOT an error detector — 96% on "WW ALIB"
second OCR engine        catches what confidence misses, ~3.4s/call fixed cost,
                         3.2x better tiled
three-witness arithmetic RPTT/rate == RETT/0.400% == document_amt
                         verified exact on $2,975,000 and $5,923,938
model reads the crop     resolves everything, including handwriting no engine
                         will ever read ($2,940 handwritten -> $735,000)
```

⚠ The three-witness check is the cheapest and strongest of these and it is free.
It caught my own bug: RPTT hardcoded at 2.625% when NYC has four statutory rates,
which reported ELEVEN CORRECT extractions as "REAL misreads".

### Escalation tier — the residue

```
blind page (conf<55 or <25 words)   -> model reads the WHOLE page, ~659 tok
value present but engines disagree  -> model reads the CROP, ~300 tok
required slot absent                -> model reads the section
```

---

## 3 · The pipeline

```
                     ┌──────────────────────────────────────┐
  every page ───────>│ TESSERACT  20,000 pg/hr, 12 procs     │
                     │ text + word boxes + confidence        │
                     └────────────┬─────────────────────────┘
                                  │  free, parallel, embarrassingly so
              ┌───────────────────┼───────────────────┐
              v                   v                   v
     ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐
     │ BLIND PAGE?    │  │ SECTION INDEX  │  │ COVER PAGE       │
     │ conf<55 or     │  │ Section N.N /  │  │ layout engine    │
     │ <25 words      │  │ ARTICLE /      │  │ (table-aware)    │
     │ 12.4% of pages │  │ EXHIBIT + boxes│  │ 1 page per doc   │
     └───────┬────────┘  └───────┬────────┘  └────────┬─────────┘
             │                   │                     │
             │            trigger lexicon        stamps -> price
             │            per instrument form           │
             │                   │                     v
             │                   v            ┌──────────────────┐
             │          ┌────────────────┐    │ THREE-WITNESS    │
             │          │ SECTION CROPS  │    │ RPTT/r == RETT/r │
             │          │ heading -> next│    │ == document_amt  │
             │          └───────┬────────┘    └────────┬─────────┘
             │                  │                      │ pass -> done,
             │                  v                      │ no model needed
             │        ┌──────────────────┐             │
             │        │ 2nd OCR, TILED   │             │
             │        │ agree -> accept  │             │
             │        │ differ -> escalate             │
             │        └───────┬──────────┘             │
             └────────────────┴──────────────┬─────────┘
                                             v
                                    ┌──────────────────┐
                                    │ MODEL reads the  │
                                    │ CROP. Claim +    │
                                    │ verbatim + box.  │
                                    └────────┬─────────┘
                                             v
                          VERTICAL: slots per instrument form
                                             v
                          IDENTIFY: which BBL, which party, which prior doc
                                             v
                          HORIZONTAL: chain · conservation · lifecycle
                                             v
                                       RESOLUTION
```

### Where the parallelism is

```
TESSERACT     embarrassingly parallel. No shared state. Scales linearly with
              cores and restarts cleanly, so cheap preemptible capacity works.
              ~1,650-2,500 pg/hr per core measured.
DOCUMENTS     independent. A parcel's 104 documents extract concurrently;
              wall clock is the slowest document, not the sum.
CROPS         independent within a document, and TILE into one call.
CHECKS        pure functions over claims. Trivially parallel.
ACQUISITION   ⚠ NOT parallel. One polite stream. Measured 25.7 pg/s and it
              never moved with concurrency, sessions, ethernet or VPN.
              This is the binding constraint and money does not fix it.
```

---

## 4 · Cost model

```
OCR the corpus       140.2M pages ÷ ~1,650 pg/hr/core = ~85,000 core-hours
                     ~59 cores matched to acquisition rate -> ~63 days
                     ~EUR 300-400 total, once
                     ⚠ core-hours are CONSERVED: 125 cores x 30 days costs the
                       same as 59 x 63. Renting longer is not more expensive.

MODEL, per document  cover page mechanical (0 tokens if the check passes)
                     + 6-10 section crops x ~300 tok
                     + blind pages x ~659 tok
                     ~= 2,000-3,000 tokens

MODEL, corpus-wide   17M x 2,400 = ~40 BILLION tokens.
                     ⚠ NOT HAPPENING. Ever. At any budget.

MODEL, what you need ~9,000 documents/year of real work = a few million tokens
```

⚠ The 17M number matters for exactly one thing: **finding which nine thousand.**
That is what the index and the map do, for free, without extraction.

---

## 5 · Ranked, by measured value

```
1  LAYOUT ENGINE ON COVER PAGES
   2% -> ? on the single most valuable field in ACRIS (the true price, which
   the index omits from 74.3% of deeds). Untested. Highest expected value.

2  TESSTRAIN ON MICROFILM
   blind rate 26-29% pre-2000 vs 4% modern. Each blind page costs a 659-token
   full read instead of a 300-token crop. The fonts are consistent (legal
   typewriter, Courier); a custom .traineddata should beat generic English badly.

3  MULTI-ENGINE CONSENSUS ON CROPS, TILED
   proven to catch WW ALIB and the lost month. 3.2x with tiling.
   ⚠ needs a measured false-agreement rate before it can be trusted as a check.

4  MORE TESSERACT TUNING
   spent. Six configurations, all within noise.

5  GPU
   DirectML measured at 0.95x. The integrated Arc is not a lever.
```

---

## 6 · What is NOT measured, and matters

```
- Docling / PP-Structure on the cover page. The #1 item is untested.
- The false-agreement rate when two engines fail identically.
- Whether tesstrain actually helps on this film. Assumed, not shown.
- Whether the conventional structure (WITNESSETH / WHEREAS / IN WITNESS
  WHEREOF) holds for DEEDS and MORTGAGES. Verified on 20 DEVRs only, and
  old deeds are unbroken prose with no numbered sections.
- Cost per crop from a commercial OCR API on the 17M cover pages (~$26k).
```

---

## 7 · Corrections kept on the record

Every one of these was stated confidently and was wrong. They are here because
the pattern matters more than the individual errors: **a number describing an
image is not the image, and a metric that survives the damage you care about
will always report that nothing is wrong.**

```
"16 days to acquire the corpus"      never reproducible. Best ever ~31 pg/s.
                                     Real figure ~63 days at 25.7 pg/s.
"Tesseract cannot read microfilm"    it was reading the film frame.
"byte size predicts claim density"   the SMALLEST page held the only geometry.
"claims cluster front and back"      the middle held the upzoning clause.
"--oem 0 is 19x faster"              it returned zero characters.
"the map is stalled"                 megabyte rounding hid 5,800 documents.
"eleven real misreads"               my check used 1 of NYC's 4 statutory rates.
"ACRIS is blocking us" (x5)          probing with urllib while the job ran
                                     aiohttp. Different headers, different
                                     treatment. The job was never blocked.
"the survey menu is complete"        26 slots from ONE document; the next two
                                     documents broke it in three ways.
```
