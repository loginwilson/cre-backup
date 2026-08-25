# RICHMOND COUNTY CLERK — the source

**Staten Island. Third source through [the workflow](../../WORKFLOW.md).
Specification CONFIRMED and landed 2026-08-18. Acquisition path measured, not started.**

## WHY THIS SOURCE EXISTS AT ALL

ACRIS is a **split custodian** for Staten Island: it carries the RPTT and a thin
tail of other filings, while the **deeds and mortgages live at the Richmond County
Clerk back to 1945**. A four-borough ACRIS corpus is not four-fifths of the city —
it is a city with a hole where one borough's conveyances should be.

Proven on a real parcel after landing (BBL 5000150012, block 15 lot 12, 45 documents):

    2023-08-09  Satisfaction Of Mortgage  RC_2711145         <- Richmond
    2021-09-21  RPTT                      2021092000721001   <- ACRIS
    2021-09-02  Deed                      RC_2602913         <- Richmond
    2021-07-12  LDMK                      2021070601052001   <- ACRIS

Neither source alone tells the story. **This is the argument for the source in one
parcel** — the deed and the transfer-tax return are in different systems.

---

## 1 · SPECIFICATION — the block ledger  ✅ DONE

One GET returns a WHOLE block's ledger, no paging:

    GET /Search/ShowResultsBlocks/0?Block=N&HiLot=12&SelectedDocumentIdentifier=0

| measured 2026-08-18 | value |
|---|---|
| number space swept | **8,999 / 8,999 blocks** (1..8999, exhaustive) |
| ledger rows | 2,891,086 |
| **distinct documents** | **2,426,404** |
| distinct SI parcels touched | 188,887 (183,947 landed with valid BBLs) |
| paging flags raised | 0 |
| wall clock | ~13 min for the 4,994-block full pass |

Columns are exactly `BLOCK · LOT · BOOK · PAGE · RECORDED · TYPE · NUMBER`. Each row's
button carries `value="<INTERNAL_ID>"` and displays the INSTRUMENT — **the ledger
publishes the id-binding IN BULK**, which ACRIS made us fetch one document at a time.

⚠ **SWEEP THE NUMBER SPACE, NOT THE SPINE.** Keying the sweep to today's tax map is
the obvious move and silently loses history: **2,392 blocks carry 47,498 document
rows and do not exist on the current map.** A spine-keyed sweep never requests them
and nothing in its output indicates the gap — the same invisible-loss shape as
retired BBLs dropping out of a gate-keyed pull. 2,818 numbers are genuinely empty.

⚠ **ROWS ARE NOT DOCUMENTS.** One instrument spans one row per lot it touches:
2,891,086 rows -> 2,426,404 documents. Reporting rows as documents overstates the
corpus by 19%.

### What landed

    document          21,611,255  ->  24,037,659   (+2,426,404)
    parcel_document   26,442,304  ->  28,984,893   (+2,542,589)
    rc_binding                 0  ->   2,426,404

`document_id` is `RC_<internal_id>` — the system's own unique key, and the key the
access path needs. The instrument/book/page citation lives in `rc_binding`.

⚠ **THERE IS NO REFERENCE OR REMARK LAYER.** The detail page has three sections and
that is all there is. Their absence is a property of the source, not a gap in the pull.

---

## 2 · LIVE SYNC — date range  ✅ BUILT

    GET  /Search/SearchIndex                     mints cookie + __RequestVerificationToken
    POST /Search/SearchIndex   button=DateRangeSearch
    POST /Search/DateRangeSearch  StartSearchDate=MM/DD/YYYY  EndSearchDate=MM/DD/YYYY

| measured | value |
|---|---|
| 1 day | 102 documents, 1 request, ~~no paging~~ ⚠ **IT PAGES NOW — see §2b** |
| 30 days | 2,982 documents · 2.03 MB · 2.8 s |
| 60 / 90 / 365 days | **0 documents, 8 KB** |
| reach back | 1998, 2019, 2024 all return normally |

⚠ **THE OVER-CAP RESPONSE IS A SILENT ZERO.** 60 days returns HTTP 200 with an 8 KB
page and no rows — shaped exactly like a genuinely empty range. Never exceed 30 days,
and never read 0 rows as "nothing recorded" without the density check.

⚠ **INSTRUMENT NUMBER IS A DENSE MONOTONIC COUNTER — Richmond's CRFN.** A 30-day 2019
window ran 725293..728274: 2,982 slots, 2,982 documents, **0 missing**. So a window
proves ITSELF complete by `max - min + 1 == count`, independent of both access paths.
⚠ Density holds WITHIN a window only — across eras there is a discontinuity
(2005 -> instrument 7,795; 2006 -> 98,786). Never extend the proof corpus-wide.

Daily job is `rc_daily.py` (3-day lookback, dedupes against what is held).

---

## 2b · THE SOURCE CHANGED UNDER US — two defects, both silent  (2026-08-23)

Found while wiring the monitor's Richmond half. **Both would have reported success
forever.** Neither was detected by any check that existed; the *density proof* caught
both, and it is the only thing that did.

### DEFECT 1 — the row regex died. Every window parsed 0 rows.

Every date-range window, 2019 and 2026 alike, returned **0 rows** while the server sent
a real **30 KB results page**. Not the over-cap trap above (that page is ~8 KB); the
results were there and the pattern no longer matched them.

    OLD  <button name="ViewDetailsButton" value="2825706">1016821</button>
    NEW  <a href="/Search/ViewDocumentInfo/2825706"><span>1016821</span>

Same two values — `internal_id` and `instrument` — moved from a button into an anchor
plus a span. The results table also went 7 columns → 5 (BOOK, PAGE, RECORDED, TYPE,
DOCUMENT No.).

⚠ **THIS IS THE WORST FAILURE SHAPE IN THE SYSTEM.** `rc_daily`/`rc_sync` would have
reported *"0 new documents"* every day, forever, and looked healthy doing it — the
disease `LIVE_SYNC.md` warns about for `recorded_datetime`, arriving by another route.
**A parser that can only return "nothing" cannot tell you it is broken.** Both patterns
are kept in `_ROW`: the old costs nothing and the corpus was built with it.

### DEFECT 2 — the window paginates at 17 rows. We were reading 10% of a day.

With the regex fixed, **every** window returned exactly 17 rows — the tell. The footer
says `Page 1 of 10`. Pagination is a plain **GET**, easier than the POST that opens the
window, and ⚠ **its dates are ISO, not the form's MM/DD/YYYY**:

    /Search/DateRangeSearch?StartSearchDate=2019-06-03&EndSearchDate=2019-06-03
                           &SelectedDocumentIdentifier=0&pageNumber=N

`Window.rows()` now follows every page, and **raises rather than returning a short list**
if a page fails — a partial window that looks whole is how this defect got in.

### THE DENSITY PROOF IS WHAT CAUGHT BOTH

| 2019-06-03 | slots | docs | missing |
|---|---|---|---|
| page 1 only | 144 | 17 | **127** |
| all 10 pages | 159 | 159 | **0** |

`max - min + 1 == count`. It needs nothing from the server and cannot be satisfied by a
confident wrong answer. **Re-verified across a full week — every weekday missing 0:**

    Mon 08/17  102 docs  max 1,016,820      (⚠ 102 - the ORIGINAL documented figure;
    Tue 08/18  131 docs  max 1,016,951       the 2026-08-18 measurement was RIGHT,
    Wed 08/19  184 docs  max 1,017,135       the site changed after it)
    Thu 08/20  112 docs  max 1,017,247
    Fri 08/21  103 docs  max 1,017,350
    Sat/Sun    0 docs   — both weekends, genuinely closed

### ⚠ THE EDGE IS NOT ON PAGE 1

08/21: page 1 topped out at **1,017,264**; the day's true max was **1,017,350**. Rows
ascend, so late filings land on late pages. A monitor watching page 1 would stare at a
**frozen** number all day and call every tick "quiet" while ~86 documents landed behind
it. `Window.edge()` reads the **last** page: **2 requests, ~5 s** vs 10 requests /
19–28 s, verified 3/3 against the full-window max. That is what makes a one-minute
cadence affordable.

### ⚠ AN EMPTY DAY IS NOT AN EDGE

Weekends are genuinely empty (two measured, weekday density perfect either side), so
`phase_monitor` **walks back up to 5 days** to the last day that actually recorded
something. Five empty days in a row is reported as a **broken read**, not a quiet week.

### ✅ THE BACKWARD RE-CHECK — did the dead parser lose anything?

Standing rule: *when a new trap is found, re-run it over every earlier entry —
prior work was judged by rules that predate the lesson.* So the fixed window was
run wide and checked against what we actually hold:

    window 08/01 .. 08/21 (21 days)     1,824 documents · 108 pages · 194 s
    density                             1,824 slots · 1,824 docs · missing 0
    against navigation                  HELD 1,824 · ABSENT 0

**Nothing was lost.** The corpus stayed complete because the BLOCK LEDGER path
(`rc_feed` / the coded rd walk) was covering Richmond the whole time — the
date-range search is the *delta* path, and its silence never subtracted anything
already held. The defect was in what we could SEE, not in what we HAD.

⚠ That is luck of architecture, not a reason to relax: had we been relying on the
delta path alone — which is exactly the plan for daily freshness — the silence
would have been a permanent, invisible hole.

**THE LESSON, WHICH IS NOT ABOUT RICHMOND:** every claim in this file has a date on it
because *a source can change without telling you, and the failure it hands you is a
plausible number, not an error.* The regex, the page count and the edge each produced a
clean, healthy-looking answer that was wrong. Only the arithmetic proof — the one check
that does not consult the source about its own completeness — disagreed.

---

## 2c · `rc_sync_fast.py` — the O(delta) path the monitor fires  (2026-08-23)

Richmond had no fast sync, so `phase_monitor --gate` had nothing to fire for it
but `routine_synchronization.py` — whose STEP 1 counts 24.1M rows (**464 s at
best, 27 min under contention**) before it even looks at the source. On a
one-minute cadence that IS the pile-up.

    routine_synchronization.py   proves levelness   minutes   periodic
    rc_sync_fast.py              lands the delta    seconds   every minute

⚠ **RICHMOND NEEDS NO GALLOP.** ACRIS's `sync_fast.py` walks the CRFN counter
upward because its edge is a *boundary to be found*. Richmond's date-range window
**returns the documents themselves**, so the delta is just "which of these do we
not hold" — one primary-key lookup per row, no scan anywhere.

    measured 2026-08-23:  3-day window · 103 documents · 7 pages · 22 s
                          density 103/103 missing 0 · held 103 · NEW 0

⚠ **EVERY WORK COLUMN IS `''`, NEVER NULL.** `nav_append.py:216` states the
invariant: *"rd_walk sees recorded_details='', image_walk sees pdf='', nav_key
sees keyed_by=''"*. Those lanes select on `= ''` and **NULL is not `''`**, so a
row inserted with NULLs is invisible to every downstream lane forever — while
looking perfectly healthy (id present, count right, url audit passing). It would
also fall outside `ix_nav_pdf_todo`, so `board_truth` would count it as **LANDED:
a document with no pdf, reported as acquired.** `sync_fast.py` had exactly this
bug; verified against a scratch table that all three lanes now see the row.

---

## 3 · ACQUISITION — BROWSER-ASSISTED, not direct-endpoint

> ⚠⚠ **SUPERSEDED 2026-08-22 — SEE §3d. THE PDF LANE NEEDS NO BROWSER.**
> Everything below about Richmond's *viewer route* still holds, and the
> ethics table (#1/#2/#3) stands unchanged and was not bent to get here.
> What was wrong is the CONCLUSION: the pdf bytes do not come from
> richmondcountyclerk.com at all. They come from a second host, and an
> honest HTTP client sending THIS PROJECT'S OWN UA is served instantly.
> Measured 12.77 pdf/s against the browser's 1.31/s. Read §3d before
> acting on anything in this section.

### ACCESS MODE: **browser-native**

    SOURCE                Richmond County Clerk
    ACCESS MODE           browser-native
    DOCUMENT ROUTE        /ViewVscmsDocument/ViewContent?p_endorsementId={internal_id}
    OBSERVED              real Chrome navigation succeeds
                          direct HTTP clients receive Cloudflare 403 / managed challenge
    REQUIREMENT           use normal browser navigation
                          do NOT substitute backend HTTP retrieval unless separately supported

⚠ **"USE CHROME" AND "PRETEND TO BE CHROME" ARE NOT THE SAME THING.** Three distinct
approaches get collapsed constantly, and only the third is a problem:

| # | approach | what it is | here |
|---|---|---|---|
| 1 | **real Chrome, driven by hand** — navigate, render, save | genuine browser access | **works** |
| 2 | **real Chrome, automated** (Playwright/Selenium, visible, no stealth plugins, no forged fingerprint) | genuine browser access, automated | **the intended acquisition route — verify it behaves like #1** |
| 3 | backend client (curl/requests/urllib) with a spoofed Chrome UA, mimicked TLS fingerprint, or replayed `cf_clearance` | dressing up as a browser | **do not** |

The measurement — honest HTTP client 403s, real Chrome renders the document — tells
you the access mode is **browser-native**. It does not tell you to make an HTTP client
impersonate a browser. Those are opposite conclusions from the same fact.

⚠ **IF AUTOMATED CHROME (#2) IS ITSELF CHALLENGED, DO NOT HIDE THAT IT IS AUTOMATED.**
The two legitimate moves are to keep the retrieval human-assisted, or to pursue an
authorised bulk / remote-access route with the County Clerk. Adding stealth tooling
to make #2 look like #1 converts a supported approach into #3.


**Acquisition method is a property of the SOURCE, not of the decoder.** Two methods
exist and they are not interchangeable:

| method | source | unit | transport |
|---|---|---|---|
| **direct-endpoint** | ACRIS | one PAGE | derived URL -> TIFF, any client |
| **browser-assisted** | Richmond | one DOCUMENT | derived URL -> PDF, opened in Chrome |

ACRIS serves bitonal page TIFFs from a URL that is a pure function of `doc_id`, to
any client, at 75-90 pages/s. Richmond serves whole-document JPEG PDFs through a
viewer opened in a browser. Same shape of index, completely different retrieval.

⚠ **DO NOT COPY THE ACRIS ACQUISITION CODE FOR THIS SOURCE.** It assumes pages, a
page-count map, and a client-agnostic endpoint. Richmond has documents, no page
map (one unit each, known for free), and browser-assisted transport. An agent that
reuses the ACRIS pattern here will build a page walker for a source that has no
pages and conclude the source is broken.

### THE PATH

    specification  ->  internal_id
                   ->  https://www.richmondcountyclerk.com/ViewVscmsDocument/ViewContent?p_endorsementId=<internal_id>
                   ->  opens in Chrome, renders the PDF
                   ->  the viewer serves a PDF (transient)
                   ->  compress to bitonal G4 TIFF (below)
                   ->  store     D:/acris/02-acquisition/documents/RC_<internal_id>.tif
                   ->  the PDF is NOT kept - storing it is 20.3 TB instead of 1.2 TB
                   ->  record in the acquisition ledger

**The access point is IN the specification.** Two equivalent renderings, both
complete for all 2,426,404 documents:

| rendering | where | use |
|---|---|---|
| `rc_access` view | `01-specification/parcel_spec.db` | query it like a table — `SELECT image_url FROM rc_access WHERE ...` |
| `rc_urls_ALL.csv` | `01-specification/index/` | a flat 668 MB work list; regenerate with `rc_urls.py` (3.6 min) |

Both carry `document_id · internal_id · instrument · doc_type · doc_date ·
recorded_date · amount · book · page · image_state · detail_url · image_url`, and
the CSV adds `bbls` and `store_at`. **Nothing needs deriving at retrieval time.**

⚠ **THE TWO RENDERINGS ARE NOT EQUIVALENT, AND THE CSV'S STALENESS IS INVISIBLE.**
Corrected 2026-08-19 while tracing why acquisition was not seeing the current
specification. The row mixes two different KINDS of field:

| field | kind | goes stale? |
|---|---|---|
| `image_url`, `detail_url` | **derived** from `document_id` | never — it is a function of the key |
| **`image_state`** | **an OBSERVATION**, rewritten by every detail pull | **immediately** |

`rc_access` is a VIEW, so it re-reads both on every query and is always current.
`rc_urls_ALL.csv` is a SNAPSHOT: it freezes `image_state` at the moment
`rc_urls.py` ran. Measured that day — the CSV was stamped 06:41 while the
specification had moved on by **127,763 documents**, nearly all of them
`unknown -> present`, i.e. exactly the transition that makes a document
acquirable.

⚠ **And nothing about the file looks wrong**, because the always-correct half
(the URL) is what every row is mostly made of. A run driven off a stale CSV
fetches valid addresses for a stale subset and reports complete success — the
same shape as the manifest lesson in the ACRIS acquisition doc ("the stale
artifact was the measurement, not the corpus").

**So: drive acquisition from `rc_access`, not from the CSV.** Regenerate the CSV
only for an offline/hand-off work list, and treat its timestamp as part of its
meaning — a CSV without the time it was cut is not a work list, it is a rumour.

⚠ **THE VIEW STORES NOTHING ON PURPOSE.** `image_url` is a pure function of
`document_id`, so materialising it would duplicate 2.4M strings that can never
disagree with the key they come from — and would silently go stale if the host path
moved. One definition, in `rc_access`.

⚠ **THE URL MINTS A FRESH TOKEN PER REQUEST.** Store the `p_endorsementId` form,
never a resolved `?token=v2...` URL — those carry a timestamp and signature and go
stale within minutes. The durable key is `internal_id`.

⚠ **WHY BROWSER-ASSISTED — MEASURED 2026-08-18.** The county host mints the token to
an anonymous request and redirects to the state viewer host
`iapps.courts.state.ny.us`. That host runs a **Cloudflare managed challenge**
(`cType: 'managed'`, body: *"Enable JavaScript and cookies to continue"*), so a
plain HTTP client gets **403 + a 6.4 KB challenge page** rather than the PDF. A
browser clears it by executing the challenge script, which is what the challenge is
for. **The retrieval step therefore runs in a real browser — do not paper over this
with a User-Agent string; the UA is not what is being checked, and a spoofed one
just hides the mechanism from whoever debugs it next.**

### WORK LIST — drive it from image_state, not from the full corpus

    image_state = present     retrievable now
    image_state = pending     scan not attached yet; recheck next day
    image_state = imageless   no scan will ever exist - never queue it

Measured: ~0.2% of historical documents are `imageless`. Filtering on
`image_state = present` is what stops an acquisition run burning time on the
~5,000 documents that have nothing behind them.

### CONCURRENCY — measured 2026-08-18

| conc | success | fetch MB/s | docs/s |
|---|---|---|---|
| 1 | 6/6 | 5.19 | 0.46 |
| 2 | 5/6 | 3.41 | 0.29 |
| 3 | 5/6 | 6.52 | 0.77 |
| **4** | **6/6** | **6.27** | **1.04** |
| 6 | 6/6 | 3.87 | 0.65 |

**Run at concurrency 4.** No degradation was observed anywhere from 1 to 6, so 4 is
the best measured point rather than a ceiling — higher is likely fine and worth
re-measuring. Roughly **1 doc/s and ~6 MB/s**.

⚠ **THIS IS A BANDWIDTH LIMIT, NOT A REQUEST-RATE ONE.** The index pull sustains
concurrency 56 against the same host on ~10 KB pages. Documents average 8.4 MB —
about 800x larger — so a handful of concurrent document fetches equals thousands of
index requests' worth of traffic. Judge pacing in MB/s, not requests.

⚠ **A FAILED FETCH IS ALMOST ALWAYS TRANSIENT.** Retry with exponential backoff,
3 attempts. Measured: every failure retried successfully, including a batch where
2 of 5 failed and both succeeded on the first retry. **Slow down on failures;
never retry harder.**

### COMPRESSION — 17x, measured over 358 pages

Richmond scans are **JPEG, DeviceRGB, 8-bit, ~300 dpi** — 24 bits per pixel for
black ink on white paper. That is why 2.4M Richmond documents cost more than 21M
ACRIS documents: ACRIS ships bitonal TIFF at ~0.05 MB/page, Richmond ~0.68 MB/page.

| option | ratio | full corpus | lossy? |
|---|---|---|---|
| original | 1.0x | 20.3 TB | — |
| grayscale 300dpi q70 | 1.2x | 16.8 TB | mild |
| grayscale 200dpi q75 | 2.1x | 9.8 TB | mild — fallback |
| grayscale 150dpi q70 | 3.3x | 6.2 TB | visible |
| **bitonal CCITT G4 200dpi** | **16.7x** | **1.2 TB** | **YES — irreversible — THE DEFAULT** |

Compression cost is ~1.1 s/document of CPU and is **decoupled from fetching** — it
touches no server, so run it in parallel and it never gates the pull.

**BITONAL CCITT G4 200dpi IS THE DEFAULT — signed off by Login, 2026-08-18**, on the
reasoning that it *"matches tif"*: it lands Richmond in the same 1-bit format ACRIS
already ships, so one corpus has one format and the extraction stack sees no seam.
20.3 TB -> 1.2 TB.

⚠ **IT IS STILL IRREVERSIBLE, SO THE FALLBACK IS NAMED, NOT IMPLIED.** 1-bit
conversion destroys faint stamps, coloured seals and light handwriting. Threshold
180, measured ink coverage 3-11% across the test pages (near 0% would mean the
threshold erased the page — check this number per batch, it is the cheap alarm).
**If a document class turns out to carry colour or faint seal detail that matters,
that class goes to grayscale 200dpi q75; the default does not change for it
silently.**

### THROUGHPUT — compressed acquisition runs UNDER 1 SECOND PER DOCUMENT

Compression is pure CPU, touches no server, and parallelises freely. Fetching does
not. Measured 2026-08-18 on 12 documents / 78 MB / 8 cores:

| setting | ratio | serial s/doc | **parallel s/doc** |
|---|---|---|---|
| bitonal 200dpi | 17.4x | 0.93 | **0.39** |
| bitonal 150dpi | 22.8x | 0.68 | **0.24** |
| bitonal 120dpi | 27.7x | 0.41 | **0.15** |
| grayscale 200dpi | 2.0x | 0.97 | **0.31** |
| grayscale 150dpi | 2.9x | 0.80 | **0.24** |

Fetch at concurrency 4 is ~1.0 doc/s. Every compression setting sits below that in
parallel, so **compression is never the constraint** - run it in a process pool
beside the fetch and end-to-end throughput equals fetch throughput.

    fetch (conc 4)              ~1.0 doc/s          <- the only real constraint
    compress (8-core pool)      0.15-0.39 s/doc     <- free, runs in the gaps
    END TO END                  ~1 doc/s, compressed

⚠ **DO NOT COMPRESS SERIALLY IN THE FETCH LOOP.** Serial conversion costs
0.41-0.97 s/doc and roughly halves throughput for nothing - it was the difference
between a ~30 day and a ~57 day full-corpus estimate.

---

## 3b · TWO ACQUISITION PLANS — pick one per use case

An agent working this source should choose deliberately. Both are supported by the
same specification; they differ only in whether bytes are kept.

### PLAN A — RETRIEVE AND STORE (compressed)

Use when the document is evidence: something cited in a deal, a comp, a chain of
title, anything that must survive the source changing.

    read rc_urls_ALL.csv where image_state='present'
    fetch at concurrency 4, 3 retries with exponential backoff
    compress in a process pool (never in the fetch loop)
    write to D:/acris/02-acquisition/documents/RC_<internal_id>.<ext>
    record in the acquisition ledger

    cost: ~1 doc/s · 0.5 MB/doc bitonal (default), 4 MB/doc grayscale (fallback)
    whole borough: ~30 days, 1.2 TB bitonal
    a 500-parcel territory (~7,500 docs): ~2 hours, ~4 GB

### PLAN B — LIVE URL, ANALYSE IN PLACE (default)

Use for everything else. The endpoint is a pure function of `internal_id`, so the
address costs nothing to keep and never goes stale. Fetch when something needs to
read the document, extract, and keep the EXTRACTION rather than the bytes.

    specification holds the URL for all 2,426,404 documents already
    open -> decode -> keep the claims/events -> discard or cache the file
    storage: ~0

⚠ **PLAN B IS NOT AN ARCHIVE.** If the county changes systems or retires the
viewer, everything not stored is gone. ACRIS's own 174,142 image-less documents are
proof that sources lose things. So Plan B is the default for breadth, and Plan A is
mandatory for anything load-bearing.

### HOW TO CHOOSE

| situation | plan |
|---|---|
| document cited in a deal, comp, or title chain | **A — store it** |
| active watchlist parcel / territory | **A — scoped, hours not days** |
| exploratory read, one-off question | **B** |
| whole-corpus sweep | **B** — 2.4M x Plan A is ~30 days and 1.2 TB |
| anything feeding extraction into the tables | **A** — the bytes are needed anyway, so caching is free |

⚠ **BITONAL (THE DEFAULT) IS IRREVERSIBLE.** 17-28x and it matches the format the
rest of the corpus already uses. Threshold 180. Report ink coverage per batch;
a class that needs colour or faint seal detail is moved to grayscale explicitly.

## 4 · IMAGE LAG RULES — measured, not invented

    age 0 days   0/15 imaged        age 1 day   11/11 imaged
    ages 4-90    100%               1998-2024   100% in every sampled year but one

Richmond attaches scans **overnight — a step at ~24 h, not a decay curve.** ACRIS by
contrast is 400/400 imaged same-day and needs no pending queue at all.

The page publishes which state a document is in, so image state is **observed, never
scheduled**: `View Imaged Document` -> present · `No Image Available At This Time` -> pending.

1. **Record at the event.** New documents land immediately as `pending`. The index is
   the event; the scan is evidence for a later phase. A missing scan is never a hole
   in the specification.
2. **Recheck once, the next morning.** A step function justifies no graduated schedule.
3. **Terminal at 7 days -> `imageless`, never asked again.** Required, because `pending`
   and structurally imageless are **indistinguishable on any single read** — the page
   prints the same words for both, and only age separates them. The class is real: a
   2000 AMENDMENT (instrument 73755, internal 959553) still reads "No Image Available"
   26 years on.

⚠ **THE 2,426,404 HISTORICAL DOCUMENTS ARE `unknown`, NOT `pending`.** They never enter
the queue. Initialising them as pending would make rule 3 mark all 2.4M `imageless`
seven days from now — inventing a fact about 2.4M documents nobody ever observed.

Queue depth = source lag x daily volume ≈ 102 documents. Trivial by construction.

---

## 5 · TRAPS THAT COST TIME TODAY

**The detail page is session-guarded.** A bare GET of `/Search/viewDocumentInfo/<id>`
always returns a 2,180-byte `INVALID REQUEST: UNAUTHORIZED SEARCH ACCESS` shell at
**HTTP 200**. It parses to an empty document and every downstream count still adds up.
Reach it by re-POSTing the results form with `ViewDetailsButton=<id>`.
⚠ The session needs *A* search, not *THE* search — internal ids from 2006 and 1998
both resolve through a window opened on 08/17/2026.

**Two namespaces, no formula.** instrument 1004388 -> internal 2809822; consecutive
pairs exist but diffs range -7.4M..+2.1M. **Never derive one from the other.** The
ledger and the detail page are the only bindings, and we banked 2,426,404 of them.

**`&nbsp;` arrives as the literal entity**, not `\xa0` — strip before collapsing
whitespace or the party regex never matches.

**BLOCKS precedes PARTIES on the page** (measured: BLOCKS at 270, PARTIES at 554).
Slicing PARTIES..BLOCKS yields an empty segment and zero parties on a page with two
plainly visible.

**An ungrouped regex stop reads imaged documents and crashes on unimaged ones.**
`_field(t, "Status", "View|BLOCKS")` builds `Status:\s*(.*?)\s*View|BLOCKS` — the
alternation splits the WHOLE pattern, so a page matching the bare `BLOCKS` branch
returns a match whose `group(1)` is `None`. That branch is taken exactly when there is
no "View Imaged Document" link — **the entire population an image-lag study is made
of.** 8/8 same-day samples died this way and the run reported `0 present · 0 pending`,
which reads like a finding. Stops must be wrapped `(?:...)`.

---

## 6 · RUNNING UNATTENDED — two different silences

The layer-2 detail pull is a multi-day job that runs while nobody is watching, so it
has to tell apart the two ways it can fail. **They look identical from the outside and
need opposite responses.**

| failure | what the probe sees | correct response | guard |
|---|---|---|---|
| **link down** (wifi drops, laptop moves) | `link_up()` fails | hold; consume NOTHING | `hold_for_link()` |
| **host degrades** (server starts refusing) | `link_up()` succeeds, documents fail | cool off, then stop | `check_degradation()` |

⚠ **AN OUTAGE USED TO CONSUME THE WORKLIST.** Without the link gate, a dropped
connection does not stop the pull — every worker keeps taking ids, fails its 3
attempts in seconds, and writes an error row. At conc 20 a 20-minute outage burns
tens of thousands of documents into `err` rows. Nothing is *lost* (an error row is
not a done row, so they re-queue) but the run reports garbage, and a long enough
outage would march through the whole remainder and "finish" with everything failed.

**Measured 2026-08-18.** A real outage produced 708 error rows across ~12,000
documents (0% → 3.8% → 10.5%, climbing). Every one of the 708 succeeded on a plain
retry — **0 were document problems.** That is the signature of a link failure, and it
is why the gate asks *"is the link down?"* rather than *"is this document bad?"*

⚠ **BOTH GUARDS WERE PROVEN ON KNOWN-BAD INPUT BEFORE BEING BELIEVED.**
A guard whose counter reads zero is a claim, not a result.

    link gate        probe -> black hole: blocked 45s+, event cleared, released on
                     restore, returned True (retry the SAME id). 
    degradation      every document refused with the link UP: cooled 5 min, then
                     10 min, then STOPPED - 4,400 of 5,000 documents spared rather
                     than ground into error rows.

⚠ **THE FIRST DEGRADATION TEST WAS UNDER-POWERED AND LOOKED LIKE A PASS.** With a
600-document worklist the third trigger lands on the last row, so "stopped early" and
"ground through everything" are the same number. **Size the input so the two outcomes
can differ**, or the test cannot fail.

---

## FILES

| file | does |
|---|---|
| `rc_source.py` | session, ledger parser, detail parser, refusal + unauthorized guards |
| `rc_route.py` | route discovery — walks the menu to find DateRangeSearch |
| `rc_sweep.py` | the block sweep, checkpointed per block |
| `rc_land.py` | lands the ledger (streams; never buffers the corpus) |
| `rc_sync.py` | date-range window + instrument-density completeness proof |
| `rc_daily.py` | the daily job: delta, details, lag rules, land |
| `rc_detail_pull.py` | Target A campaign, priority-ordered (deeds first) |
| `rc_imagelag.py` | the lag study (`--recent`, `--era`) |
| `rc_verify.py` | counts + a real parcel read |


## 3d · THE PDF LANE IS PURE PYTHON — measured 2026-08-22, supersedes §3

**12.77 pdf/s, 16 workers, zero errors** against the browser loop's **1.31/s**.
No browser anywhere in the lane. `rc_pdf_pull.py`.

### WHAT §3 GOT WRONG (and it was one inference, not the measurements)

§3's measurements were right: an honest HTTP client DOES get 403 /
Cloudflare-challenged at `richmondcountyclerk.com`, and real Chrome DOES
render the document. The error was concluding that therefore **the whole
lane** is browser-native. Two things were never checked:

**1 · THE PDF BYTES ARE ON A DIFFERENT HOST.** `rc_feed.py` asks Richmond for
`/ViewVscmsDocument/ViewContent?p_endorsementId=` with redirects DISABLED and
keeps the `Location` header. That Location points at

    iapps.courts.state.ny.us/vscms_public/viewer?token=v2....

the NY State Unified Court System, and the token is SELF-AUTHENTICATING.
Richmond only ever issues the 302 — and it issues it to Python, today, in
production, because that is exactly what the feed's miners already do. **The
part of Richmond that refuses Python is not the part the pdf comes from.**

**2 · THE USER-AGENT IS LOAD-BEARING ON THE COURTS HOST.** Alternating
requests, one variable, everything else identical:

| User-Agent | result |
|---|---|
| `python-requests/2.34.2` (library default) | **ReadTimeout at 45s, 2/2** |
| `acris-decoder/1.0 (public land records...)` (ours) | **200 + full pdf, 1.5s, 2/2** |

⚠ It **HANGS** the default rather than refusing it. No status code, no error,
no challenge page — just silence until the client gives up.

⚠ **§3's line "it does not gate on User-Agent at all" is FALSE for
iapps.courts.state.ny.us.** It may still hold for richmond itself.

### THIS IS NOT APPROACH #3, AND THE TEST IS THE UA ITSELF

§3's table has rows for real-Chrome-by-hand (#1), real-Chrome-automated (#2),
and backend-client-dressed-as-Chrome (#3 — do not). It has no row for what
actually works, so add it:

| # | approach | what it is | here |
|---|---|---|---|
| 4 | **honest HTTP client sending THIS PROJECT'S OWN self-identifying UA** — `acris-decoder/1.0 (public land records indexing; contact via repo owner)` | not impersonating anything; it says what it is and who to contact | **works, 12.77/s** |

The distinction is sharp and worth keeping sharp: **#3 lies about who is
calling; #4 tells the truth about who is calling.** The host serves us
*because* we identify honestly, not despite it — the anonymous library
default is what it stalls. No TLS mimicry, no forged fingerprint, no replayed
`cf_clearance`, no stealth plugin, no cookie theft. Swapping in a Chrome UA
would move this to #3 AND was already measured to buy nothing.

### WHY THE BROWSER HAD TO GO ANYWAY

It was not merely slower — it was **designed to die**. Every pdf became a
permanent record in Edge's download manager inside the tab's own process, so
memory grew monotonically with throughput on a 16 GB box already at 88% used.
Edge's own verdict, on 2026-08-22, after ~84,000 records:

    RC_1076793.pdf   Couldn't download - Browser crashed
    RC_1076574.pdf   Couldn't download - Browser crashed

The harder it worked, the sooner it crashed. Clearing the list resets the
clock; it does not remove the mechanism. `rc_pdf_pull.py` accumulates nothing.

### MEASURED SCALING — and where the ceiling actually is

| workers | rate | errors |
|---|---|---|
| browser loop | 1.31/s | crashes |
| 4 | 3.46/s | 0 |
| 8 | 7.01/s | 0 |
| 16 | **12.77/s** | 0 |

⚠ **THE DOWNLOAD SIDE IS NOT SATURATED AT 16. THE FEED IS NOW THE
BOTTLENECK.** Measured under the 16-worker run: minting ran ~9.5/s against
~13/s consumption, `ready` drained 476 → 23, and `empty-polls` began
appearing. Two self-imposed gates now bind, and BOTH were written for the
browser:

  `rc_feed.py  MAX_IN_FLIGHT = 15`  counts .crdownload/.tmp in _incoming.
      Written to stop the browser putting 708 files in flight. Python bounds
      concurrency with its own worker count, so this now caps us at ~15.
  `rc_feed.py  --ahead 300`  parks the miners whenever ready >= 300, which is
      why minting reads +128 · +0 · +39 · +0 · +208 — a sawtooth, not a limit.

**Raise both before measuring the courts host's real ceiling** — everything
above 15 concurrent is currently measuring our own gate, not the source.

### THE METHOD LESSON (this one cost an hour)

The missing UA produced **silence**, and silence was read as a rate limit that
does not exist. Concurrency was blamed, an 8-worker burst was blamed, cooldowns
were served, and a connection-pool story was built on top — all around a
missing header in our own client. Two rules from CLAUDE.md would have caught it
in one step and neither was applied:

- **one variable at a time** — the burst changed workers, batch size and
  headers simultaneously
- **a timeout is not a refusal** — a refusal names itself; a hang names nothing,
  so it gets whatever cause the reader already believes

⚠ And the first two "python works!" results were `r.raw.read(6)` — **six bytes
of a header, reported as a working download.** Testing a proxy for the thing
and reporting it as the thing. Full-body reads are the only proof that counts.

### FILES

    rc_pdf_pull.py   the lane. --workers N --batch N --pace S.
                     Stops the lane on 401/403/429 - no retry, no rotation.
    rc_watch.py      stall detector; classifies frozen-tab vs blocked-download
                     vs dry-feed. Written for the browser era; still useful
                     for watching the feed side.
    rc_browser_loop.js  SUPERSEDED. Keep for reference only.

---

## 3e · ONE LANE — the consolidation  (2026-08-24, supersedes §3d and §2c)

**`rc_lane.py` IS THE ONLY RICHMOND PROCESS.** It absorbed `rc_live` (probe),
`rc_feed` (token minting) and `rc_pdf_pull` (fetch + land), and DROPPED
`rc_pdf_land` outright — the courts host serves a real pdf and the puller
already landed it, so the lander only ever drained a legacy `_incoming`
backlog. 4 processes → 1; 1,026 lines → 899. The retired scripts now live in
`_archive/richmond_preconsolidation/` so they cannot be started by habit.

⚠ **`rc_pdf_land.log` IS STILL READ BY THE BOARD AND MUST BE.** It is a
STATIC HISTORICAL BASELINE now — the file no longer grows, but the pdfs it
counts really did land. Deleting the branch would erase them from the board.

**WHY ONE LANE, AND WHY IT NEEDS NO WARM-UP.** Richmond drums: no pacer, the
county's latency is the only governor. Measured on restart 2026-08-24 — first
minute 10.03/s, thirteenth minute 18.37/s, `err 0`. ACRIS cannot do this (its
metronome must climb a rung at a time), which is exactly why richmond can be
stopped and restarted freely and acris cannot.

### ⚠ THE MISS THIS CONSOLIDATION EXISTS TO FIX

login, 2026-08-24: *"youve just been counting the change, but not recording
the url, details, pdf, or key properly."* Correct, and the cause was
structural: **`rc_live` landed only `id` + `rd_url` + `pdf_url`.** rd was a
separate walker that had already finished its backfill and was not watching
the edge, and `rc_heal` was a one-shot script nobody re-ran. So a new filing
got an id and a url and then stopped — no rd, therefore no key (the
`key_on_rd` trigger fires on rd), therefore no pdf.

`rc_lane` adds the **rd heal** organ, driven by THE GRANT RULE: a detail
unlocks only after the session has fetched the LISTING PAGE its id appears
on. So the heal opens a trailing `--rd-days` window, reads its pages, and
only then fetches details — all on one session. A cold detail fetch does not
fail loudly; it returns HTTP 200 and a 4,212-byte shell, which is worse.

⚠ **THE WORKLIST IS THE WINDOW, NOT THE CORPUS.** The first version selected
rd-less rows with `json_extract` over 2.5M rows, timed out past 100 s, and
healed NOTHING while logging as if it worked. Inverted: enumerate the
window's rows, then check each against the db.

**MEASURED AFTER THE FIX**, today's 7-digit filings (`RC_2825450..RC_2826619`):

    rd_url  400/400  100%
    rd      400/400  100%     <- was the miss
    key     400/400  100%     <- follows rd for free, via key_on_rd
    pdf      79/318   25%     of image_state=present, still pulling
    image_state: 318 present · 82 absent · 0 stuck pending

Corpus-wide: **rows with rd but no key = 0**, **rows with no rd at all = 0**.
`rd 105` in the PROGRESS line is the heal landing exactly the 105 filings
login counted independently for the day.

### ⚠ TWO ORDERING TRAPS THAT FAKED A CLEAN AUDIT (both mine, 2026-08-24)

RC ids live in **two namespaces**: legacy 6-digit and current 7-digit. TEXT
ordering puts `RC_999999` ABOVE `RC_2826619`, so:

- `ORDER BY id DESC LIMIT 500` returned SIX-DIGIT rows and reported **pdf
  0.0%** — read as "today landed no images". It had sampled the backfill.
- `WHERE id >= 'RC_2800000' AND id < 'RC_2900000'` looks like a 7-digit range
  and matches `RC_289643` too — same wrong answer, second time.

**The predicate that is actually right:** `id >= 'RC_2' AND id < 'RC_3' AND
LENGTH(id) = 10` — an index slice plus a length test, no `CAST(SUBSTR(...))`
(which forces a 2.5M-row scan and times out). A 0.0% that agrees with your
fear is the one to re-derive before reporting.

### ⚠ CONCURRENCY HEADROOM TEST — 24/16 IS THE SETTING, MEASURED 2026-08-24 19:51

login asked for both lanes "scaled for maximum output". Tested by raising ONLY
richmond's concurrency (24 miners/16 pullers -> 32/28) with acris untouched,
and measuring both lanes for 5 minutes:

                        24 / 16          32 / 28
    richmond docs/s     15.0 - 16.2      14.1      <- SLOWER, not faster
    acris delivered     55/s (79%)       35.3/s (51%)
    acris fails             1                4

**More connections made richmond slower AND took a third of acris's share.**
That is saturation, not headroom: the extra sockets queue instead of
delivering. Reverted to 24/16.

**THE CONSTRAINT IS THE LINK, NOT EITHER LANE'S CONFIG.** Measured combined:

    richmond  16.2 docs/s x 2.53 Mb/doc = 41.0 Mb/s
    acris      3.78 docs/s x 2.90 Mb/doc = 11.0 Mb/s
                                          -------
                                           51.9 Mb/s

against the highest figure ever observed on this connection, >=52.7 Mb/s.

⚠ **SO acris's "delivered only 79%" IS NOT A DEFECT AND MUST NOT BE TUNED.**
The governor is reading a link that richmond is using four fifths of. Raising
`--max-inflight` there would bank a peak the wire never carried - which is the
exact failure `save_tempo(delivered)` exists to prevent.

⚠ **AND THE TOTAL DOES NOT DEPEND ON THE SPLIT.** Fixed bytes through a fixed
pipe: acris has ~19.8M docs x 2.90 Mb and richmond ~1.27M x 2.53 Mb left, so
whichever order they run in, the finish is the same. richmond clears in under
a day and acris then gets the whole link (~18 docs/s, ~13 days) - which is
why the honest lever is BYTES PER DOC, not concurrency, and bytes/doc is the
source's own scan resolution, not ours to compress.
