# ⚠⚠ READ THIS FIRST — THESE ARTEFACTS ALREADY EXIST. DO NOT RE-DERIVE THEM.
On 2026-08-18 a whole session re-measured things that were already built on
2026-08-16. The artefacts were not missing, they were UNADDRESSABLE — nothing
pointed at them, so the session rediscovered them from scratch. That is the
documented failure mode of this project; this header is the fix.

    _doctype_codes.json   126 types. Per type: description, class_code_description,
                          party1_type, party2_type. THIS IS THE PARTY-ROLE
                          VOCABULARY — do not build one.
                            29 personal types: AMFL AMND ASGN ASUM BRUP CNFL CONT
                            CORP DPFTL FL FTL INIC INIT NAFTL NTXL PRCFL PRFL PSGN
                            PWFL RCRFL RFL RFTL RLSE SUBO TERM "UCC ADEN" UCC1 UCC3 WFL
                            24 use DEBTOR/SECURED PARTY · 1 uses PARTY ONE/IRS
                            18 types publish NO direction (incl. DEVR, ZONE, ADEC)
                            classes: 40 OTHER · 34 DEEDS · 29 UCC+FED LIEN · 23 MORTGAGES
    _doctype_table.json   total 21,612,352 · rp 17,065,090 · pp 4,547,262
    _doctype_of.json      1,848 document_id -> doc_type
    _hole_sample.json     40 holes classified (all personal, 0 unissued)
    _crfn_edge.json       last measured live edge + probe cost
    _pp_expected.json     Socrata's own count for each of the five pp datasets

BEFORE MEASURING ANYTHING, GREP THIS DIRECTORY FOR IT.

# LIVE STATE, DELTA, AND THE DAILY ROUTINE — measured 2026-08-18

## THE REGISTER IS ~21.6M, NOT 17M
    real property (extract 17,049,742 + live 12,584)   17,062,326
    personal property (UCC + federal liens)             4,544,590
    REGISTER                                           21,606,916
We hold 79%. Every "17M" figure in this project is the real-property slice only.

## 1 · LIVE STATE — SOLVED, 25 REQUESTS
`crfn_monitor.py` gallops from the watermark (x2 until blank), bisects, then
requires 8 consecutive blanks to accept the edge. O(log n): a 100,000-number gap
still costs ~34 requests.
    measured 2026-08-18: watermark 2026000233079 -> edge 2026000233303, 25 reqs
⚠ CONFIRM, NEVER FIRST-BLANK. The counter has genuine holes; a single blank may
be a hole, not the end. Terminating on it is the same error as the four paging
bugs — a derived signal instead of the server's.
⚠ CONTROL FIRST. A malformed request returns the same empty page as a real
absence. Refuse to report anything if the known-good watermark does not resolve.

## 2 · DELTA — EXACT, BECAUSE DENSITY IS ~100%
Sampled 40 holes evenly across the window (`hole_sample.py`, `_hole_sample.json`):
    has parcel + personal   12/12   INITIAL UCC1 · UCC3 · INITIAL COOP UCC1
    no parcel + personal    28/28   UCC3 · FEDERAL LIEN-IRS · RELEASE OF FED LIEN
    UNISSUED                 0/40
-> CRFN span EQUALS document count. `edge - watermark` is arithmetic, not an estimate.
-> ALL 3,449 holes are personal property. The real-property sweep is CLEAN in this
   window. An earlier claim of a "~671 missed real property" gap was an estimate
   from the July ratio and is WRONG — the measurement retired it.
-> 30% of UCC filings carry a BBL (fixture + co-op filings). Those land in the
   EXISTING parcel spine with no schema change.

## 3 · OUTSTANDING — THE COMPLETE LIST
### Real property (654 documents, none landed)
    430   discovered, in _live_delta_queue.jsonl, NOT landed   -> 0 requests
    224   issued above the watermark                           -> 224 lookups
### Personal property (4,544,590 documents, NOTHING DONE)
    3,449   holes inside the current live window               -> 3,449 lookups
    ~4.54M  historical backfill                                -> not started
    no schema · no parser · no channel · not in the routine
### Index components — WE CAPTURE 2 OF 5
The CRFN detail page carries ALL FIVE Socrata components in ONE 118 KB fetch:
    DOCUMENT ID -> master     PARTY 1/2/3 -> parties     PARCELS -> legals
    REMARKS -> remarks        REFERENCES -> references
`parse_detail()` reads the header and the property table and DISCARDS parties,
remarks, and references. For every delta document we drop 3 of 5 files' content,
and it is invisible because parties.jsonl (1.08 GB) sits on disk from the monthly.

## 4 · TRAPS — PAID FOR, DO NOT REDISCOVER
⚠ FLATTENED TEXT SCRAMBLES THE SECTIONS. Stripping tags puts each section's DATA
under the NEXT section's heading. Measured on CRFN 2026000219334:
    'PARCELS BOROUGH BLOCK LOT ... UNIT'                    <- header only
    'REMARKS QUEENS 12452 19 ENTIRE LOT DWELLING ONLY...'   <- the PARCEL row
A section-boundary parser would file parcels under remarks for every document and
still look correct in a spot check. THE 5-COMPONENT PARSER MUST READ THE TABLE
STRUCTURE, NOT THE FLATTENED TEXT. Get it right BEFORE the fetch — re-fetching
433 MB is the only genuinely expensive step in the plan.
⚠ NO RETRY. A transient HTTP 307 killed the walk on its FIRST document. Over
3,673 requests a transient is near-certain. Retry with backoff.
⚠ ABORTS DISCARD WORK. The byte rail threw away 40 MB of completed sweeps and the
queue never grew. Write every record incrementally; make a kill cost one record.
⚠ THE BYTE RAIL IS SIZED FOR THE WRONG JOB. 40 MB vs a measured need of 3,673 x
118 KB = 433 MB. Raise it DELIBERATELY with the measurement written down — never
nudged to make a run finish.
⚠ cp1252 CONSOLE. routine_4am.py had no stdout reconfigure; printing a stage tail
containing the warning glyph raised UnicodeEncodeError AFTER the stage ran, so
_finish() never wrote the ledger. Every scheduled 04:00 run would have died this
way, including on success. FIXED 2026-08-18.
⚠ 63% OF SWEEPS RETURN ZERO ROWS at 156 KB each — 25.3 MB of the 40 MB budget
spent learning nothing. Sweep active types only and let CRFN arithmetic catch the
rare ones; exhaustive sweeping and completeness are NOT the same thing.

## 5 · WHY PERSONAL PROPERTY IS A PREREQUISITE, NOT A SCOPE EXPANSION
CRFN is one counter across BOTH corpora. Excluding personal property drops
density from ~100% to ~83%, and at 83% a genuine miss is INDISTINGUISHABLE from a
UCC filing we chose not to land. Today 40/40 unexplained holes were personal.
While that index is excluded, "are we up to date?" cannot be answered — only
asserted. The 4.5M documents are almost beside the point; the denominator is.
UCC filings ARE fully imaged (2-4 pages, real doc_ids, same endpoint function) —
they are NOT index-only records.

## 6 · SAFETY ENVELOPE — WHAT ACTUALLY TRIPPED, AND WHAT DID NOT
TRIPPED : 12,077 documents at CONC 16, cold, in a burst (amap.py) -> Bandwidth
          Notice at every URL, served as HTTP 200. Fixed: CONC 8, seeded session,
          Referer, AIMD.
DID NOT : today's 70+ live requests — 25 (edge) + 40 (sample) + 5 (checks) —
          sequential, one connection, 2.5s pace.
PLANNED : 3,673 lookups = 433 MB over ~2.5 h = 48 KB/s, sequential. Same shape as
          the probe, just longer. Acquisition itself sustains 93.8 pg/s for days.
=> The constraint is CONCURRENCY, not volume. Pace and connection count are the
   levers; total bytes are not.

## 7 · BUILD ORDER (each step blocks the next)
1. Structure-based 5-component parser (NO requests) — traps above
2. `party` + `party_document` beside `parcel` + `parcel_document`, shared `document`
3. live_land.py guard: refuse only if NO parcel AND NO party
4. Fetch the 3,673 ONCE, all five components, resumable + retrying
5. Land -> map -> push -> re-probe the edge; span must return 0
6. Routine: all 5 boroughs, real AND personal, all 5 components, active types only

# ============================================================
# GAME PLAN — LIVE STATE SYNCED WITH SPECIFICATION
# written 2026-08-18 after confirming personal property on Socrata
# ============================================================

## THE KEY REALISATION: THE 4.5M IS A DOWNLOAD, NOT A CRAWL
All five personal-property components publish on Socrata. Confirmed live:
    sv7x-dduq  master      4,547,264      uqqa-hym2  legals      3,981,194
    nbbg-wtuz  parties    11,035,386      6y3e-jcrc  references  7,724,967
    fuzi-5ks9  remarks       493,910      TOTAL     27,782,721 rows
=> ACRIS is touched ONLY for the gap between the extract's good_through_date
   (2026-07-31) and today. That is ~3,449 documents, not 4.5 million.
=> Socrata is a different host, built for bulk, and has never been the trip risk.

## PHASE 0 · BASELINE — SOCRATA BULK (no ACRIS, no trip)
Pull all five personal-property datasets to index/index_full/personal_*.jsonl.gz
using the existing bulk.py path. pp_spec.py already targets sv7x-dduq; extend to
the other four.
⚠ $offset WITHOUT $order SILENTLY DROPS AND DUPLICATES ROWS while COUNT stays
correct. Always $order=:id. This is already fixed in bulk.py — do not regress it.
⚠ COUNT FIRST, COMPARE AFTER. Record each dataset's count(1) before the pull and
assert the landed row count matches. A short pull looks identical to a complete
one on disk.

## PHASE 1 · SCHEMA — THE PARTY SPINE
    parcel -> parcel_document -.
                                >-- document   (one table, one CRFN counter)
    party  -> party_document  -'
`party` carries name_raw AND name_canon (lexicon.canon()) so the matching decision
never forces a 11M-row migration later. Store both from day one.
⚠ `walk` has bbl in its PRIMARY KEY, so it cannot track a partyless document.
That table needs the same treatment or personal property is untrackable.

## PHASE 2 · PARSER — 5 COMPONENTS, STRUCTURE-BASED
Read the HTML TABLE STRUCTURE. Flattened text files each section's DATA under the
NEXT section's HEADING (proven on CRFN 2026000219334 — see TRAPS above).
Must emit master + parties + legals + remarks + references from ONE fetch.
Validate against Socrata: pull 50 known personal-property documents from the five
datasets, parse the same 50 live, and require field-level agreement. THE PARSER IS
NOT DONE UNTIL IT AGREES WITH THE PUBLISHED INDEX ON A SAMPLE IT DID NOT CHOOSE.

## PHASE 3 · THE LIVE GAP ONLY (~4,103 documents)
    430   real property, already queued, NOT landed      0 requests
    224   real property above the watermark            224 lookups
  3,449   personal property in the live window       3,449 lookups
                                                    -----------
                                                     3,673 lookups
= 433 MB over ~2.5 h = 48 KB/s, SEQUENTIAL, one connection.
Rails: retry-with-backoff (a transient 307 killed the last walk at document 1),
per-record incremental write (an abort must cost ONE record, not 40 MB), byte rail
raised DELIBERATELY to 500 MB with this measurement recorded, check_refused() at
the door, control-probe first.

## PHASE 4 · LAND -> MAP -> PUSH -> RE-PROBE
Drive first (it decides what gets WALKED), then map, then Supabase (it decides
what gets FETCHED). Landing Supabase first creates rows nothing selects.
THE PROOF IS THE RE-PROBE: run crfn_monitor.py after landing. `span outstanding`
must return 0. That is a measurement against the live counter, not a row count we
computed from our own output.

## PHASE 5 · THE DAILY ROUTINE — ALL OF IT
    1. crfn_monitor.py            ~25 req   live edge; if span 0, STOP, done
    2. sweep ACTIVE types only   ~180 req   63% of type x borough sweeps return
                                            zero rows at 156 KB each — 25.3 MB of
                                            the budget spent learning nothing
    3. CRFN arithmetic on the rows  free    a rare type shows up as a HOLE
    4. resolve holes            1 req/gap   this is where rare types get caught
    5. land -> map -> push
    6. re-probe -> span must be 0
Covers BOTH corpora, ALL FIVE boroughs, ALL FIVE components.
Steady state ~1,550 documents/day (~260 of them personal) ≈ 1 hour.

## WHAT "DONE" MEANS — ONE SENTENCE
crfn_monitor.py reports span 0 against a register of ~21.6M with personal property
landed, so that a hole in the counter is once again EVIDENCE OF A MISS rather than
an expected artefact of an index we chose to ignore.

## ⚠ OPEN GAP — REFERENCES AND REMARKS HAVE NO TABLES (2026-08-18)
land_personal.py lands 3 of 5 components:
    master  -> document          OK
    legals  -> parcel_document   OK
    parties -> party_document    OK  (verbatim mirror of the Socrata index)
    references (7,724,967)       PULLED TO DISK, NO TABLE, NOT LANDED
    remarks    (493,910)         PULLED TO DISK, NO TABLE, NOT LANDED
This is the SAME gap party_document had an hour earlier: the data is on disk and
looks present, but nothing can reach it. "Index attached" is 3/5 until these land.
Real property has the same gap — references.jsonl.gz and remarks.jsonl.gz have sat
in index_full since 2026-08-14 with no table either.

## ⚠ DO NOT INVENT KEYS FOR AN INDEX SOCRATA ALREADY PUBLISHES
A party_key + name normalizer was built and then DELETED the same hour. Socrata
publishes document_id · party_type · name · address · city · state · zip · country.
Mirroring that cannot be wrong; any key we invent can be, and would have to be
migrated across 11M rows. Entity matching is a LATER decision — storing the index
verbatim keeps it open. lexicon.canon() is the EXTRACTION function-vocabulary
normalizer and returns None for names; it is not an entity resolver.

# ============================================================
# RICHMOND COUNTY (SI DEEDS) — MEASURED MODEL, 2026-08-18
# 4 probes; saved pages in scratchpad rc_block15.html / rc_detail.html
# ============================================================
- Ledger: GET /Search/ShowResultsBlocks/0?Block=N  -> WHOLE block, no paging seen
  (block 15 = 234 docs, 437 KB, one response). Columns: block/lot/book/page/
  recorded/type/NUMBER. The NUMBER cell is a form BUTTON: visible text =
  instrument number, value= INTERNAL id. Ledger publishes the binding IN BULK.
- Two namespaces like ACRIS (CRFN vs doc_id): instrument 1004388->internal
  2809822 consecutive pairs exist but NOT derivable (diffs -7.4M..+2.1M).
- Detail: GET /Search/viewDocumentInfo/<internal_id> — master (instrument, type,
  recorded, consideration, book/page, status) + PARTIES WITH ROLES (Mortgagor/
  Mortgagee named per document — richer than ACRIS) + all blocks/lots.
- Image: /ViewVscmsDocument/ViewContent?p_endorsementId=<internal_id> — endpoint
  derives from the INTERNAL id; binding is DATA -> needs a binding table.
- POST needs __RequestVerificationToken + cookie (400 without); GET detail is clean.
- PLAN: R1 block sweep (~8,000 blocks from OUR parcel spine, 1.5s pace, per-block
  checkpoints) -> RC_<instrument> in the same five tables. R2 parties at
  acquisition. R3 live sync = gallop/bisect/confirm on internal id (no year
  prefix -> NO rollover trap); routine gains a second counter loop.
- COMPLETENESS: instrument density in the modern era + cross-witness vs ACRIS SI
  RPTT records we already hold.
- ⚠ site runs bot detection; probes stay few/paced; captcha path is a no-no.

## R4 · RICHMOND'S NAME-KEYED CORPUS — the block sweep CANNOT see it (2026-08-18)
The block/lot sweep captures every instrument TYPE but only documents that touch
property. Richmond as County Clerk also records name-keyed documents: judgments,
county-level UCCs, federal liens, lis pendens — the SI analog of ACRIS personal
property, and the same blind spot: excluded, a real miss is indistinguishable
from a filing we chose not to index. Fixes: (a) the site's name/date search as
the bulk channel, or (b) internal-id enumeration 1..~2.8M (near-dense) as a
background campaign. LIVE sync has NO such gap - the id gallop enumerates ids,
so name-keyed documents are captured automatically from the watermark forward.

## R4 ROUTE DISCOVERY — Richmond date/name search (2026-08-18)
Land Documents Search offers 6 modes: Document Number · PARTY/COMPANY NAME ·
DATE RANGE · Block&Lot · Book&Page · Book&Page Special. The FORMS are behind a
captcha; the RESULT ROUTES are served openly (ShowResultsBlocks proved this - no
challenge on the result URL). DATE RANGE is the R4 key: a date sweep enumerates
EVERYTHING incl. name-keyed judgments/county UCCs the block sweep cannot see.
The ShowResultsDate-shaped route is not in the saved pages (lives in the search
UI JS). DISCOVER IT by reading the live search page's JavaScript in a browser -
never blind-probe the captcha-guarded site. Do NOT touch the captcha (hard rule).

---

## RICHMOND — THE DATE-RANGE ROUTE (discovered 2026-08-18, off the site's own form)

    GET  /Search/SearchIndex                      -> mints cookie + __RequestVerificationToken
    POST /Search/SearchIndex   button=DateRangeSearch
    POST /Search/DateRangeSearch  StartSearchDate=MM/DD/YYYY  EndSearchDate=MM/DD/YYYY

Rows are `<button name="ViewDetailsButton" value="<INTERNAL_ID>">INSTRUMENT</button>`
— the SAME binding the block ledger publishes, so the endpoint derives with no extra fetch.

| measured | value |
|---|---|
| 1 day (08/17/2026) | 102 docs, 1 request, no paging |
| 18 days | 1,425 docs · 1.03 MB · 2.7 s |
| 30 days | 2,982 docs · 2.03 MB · 2.8 s |
| 60 / 90 / 365 days | **0 docs, 8 KB** |
| reach back | 1998 and 2019 and 2024 all return normally |

⚠ **THE OVER-CAP RESPONSE IS A SILENT ZERO, NOT AN ERROR.** 60 days returns HTTP 200 with
an 8 KB page and no rows — identical in shape to a genuinely empty range. This is the
ACRIS end-of-document placeholder trap again. **Never use a window > 30 days, and never
read 0 rows as "nothing recorded" without the density check below.**

### INSTRUMENT NUMBER IS A DENSE MONOTONIC COUNTER — Richmond's CRFN

30-day window 2019: instruments 725293..728274 = 2,982 slots, 2,982 documents,
**0 missing in run**. This is the same arithmetic that made ACRIS answerable:

    max(instrument) - min(instrument) + 1 == count   ->  the window is COMPLETE

It gives Richmond a completeness proof that is independent of BOTH access paths, so the
block sweep and the date sweep can be checked against each other rather than each being
checked against its own output (the failure shape of every audit that read the filter's
own results).

### DIVISION OF LABOUR — settled

- **historical corpus = BLOCK LEDGER.** Whole block per request, far denser per call than
  walking days. In progress: 2,436/3,789 blocks, 1,849,922 rows, 0 paging flags.
- **daily delta = DATE RANGE.** One POST per day (~102 docs) or one per ≤30-day catch-up.
- ⚠ **THE BLOCK SWEEP CANNOT SEE A BLOCK-LESS DOCUMENT.** Anything filed without a
  block/lot is structurally invisible to a block-keyed sweep — the same class as ACRIS's
  37.6% parcel-less personal property, which we only found by counting. The date sweep
  returns every recorded document regardless of parcel, so **the instrument-density check
  across a date window is also the test for how much the block sweep is missing.**

---

## IMAGE STATE — RECORD AT RECORDING, PULL WHEN THE SCAN SURFACES

**ACRIS DOES NOT LAG. MEASURED 2026-08-18, DENOMINATOR 400.** Random sample of the
16,923 documents recorded 2026-08-03..08-18 (every recorded date covered, incl. the
current day): **400/400 imaged, 0 with no image.** The 4 initial URLErrors were
transient and all resolved with pages (16, 43, 3, 22) on sequential retry. So ACRIS
attaches the image at recording and **needs no lag distribution and no pending queue.**

**RICHMOND DOES LAG** — the detail page publishes which state a document is in:

    "View Imaged Document"             -> present
    "No Image Available At This Time"  -> pending

so image state is OBSERVED, never inferred and never scheduled. Measured: every
document recorded 8/18 reads `pending`; a document recorded 8/7 reads `present`.

### THE RULE
1. **Record at recording.** The index lands the day the instrument records; the image
   endpoint DERIVES from the internal id, so access is never what is missing.
2. **Mark, don't chase.** `image_state=pending` + `image_checked=<date>` on the row.
3. **Recheck BY WINDOW, not by document.** Re-open the date-range window for a day that
   still holds pending rows and re-POST only those internal ids - a few dozen requests,
   not a crawl. The pending set is the ONLY thing that may ever drive image acquisition;
   that is what keeps this bounded and stops it becoming a bulk scraper.
4. **The queue MUST have a terminal state.** `pending` and `structurally imageless` are
   identical on any single read. Past the measured p99 lag, a still-pending document is
   reclassified `imageless` and stops being asked for. Without this the queue retries
   forever - and ACRIS's own 174,142 imageless documents show the class is real.

⚠ **`document.image_state` / `document.image_checked` WERE ADDED 2026-08-18** (ALTER,
0.14 s, metadata-only on 21.6M rows). **The Supabase table does not have them yet** -
add both columns BEFORE the push or the schemas drift.

### ⚠ THE PARSER READ IMAGED DOCUMENTS AND CRASHED ON UNIMAGED ONES
`_field(t, "Status", "View|BLOCKS")` built `Status:\s*(.*?)\s*View|BLOCKS`. The
alternation was UNGROUPED, so it split the whole pattern: a page matching the bare
`BLOCKS` branch returned a match whose group(1) was `None` -> AttributeError. That branch
is taken exactly when there is no "View Imaged Document" link, i.e. on every PENDING
document - the entire population an image-lag study is made of. 8/8 samples on the
current day died this way and the run reported `0 present · 0 pending`, which reads like
a finding. Stops must be wrapped `(?:...)`.

---

## ⚠ RICHMOND IS A NAVIGATION MAP, NOT AN ACQUISITION MAP — SETTLED 2026-08-18

Do not re-litigate this and do not build a workaround. The chain was tested to the
last hop with correct browser semantics (same session, detail page loaded first,
Referer set):

    1  detail page loads                                          OK
    2  /ViewVscmsDocument/ViewContent?p_endorsementId=<id>        OK - mints a token
    3  302 -> iapps.courts.state.ny.us/vscms_public/viewer?token=v2...   OK
    4  that host returns HTTP 403, body <title>Just a moment...</title>  REFUSED

`Just a moment...` is Cloudflare's bot-detection interstitial. The images are served
by the NYS **Unified Court System**, not by the county. So:

* the URL IS derivable from our index - all 2,426,404 documents mint a working token
* a PERSON can reach any scan, back to 1998
* an automated client cannot, and getting past that interstitial - including by
  driving a real browser to harvest at scale - is the same prohibited act in a
  costume (CLAUDE.md: "do not work around bot detection"; user: "the captcha way
  is a no no")

**ACRIS is acquirable because NYC publishes it that way. Richmond is not because the
state does not.** The only legitimate route to Richmond images at scale is a bulk
data request to the Richmond County Clerk + UCS. That is a conversation, not a script.

### ACQUISITION-MAP SCORECARD (measured)

| requirement | ACRIS | Richmond |
|---|---|---|
⚠ **CORRECTED.** The first version of this table scored Richmond 1/4 by silently
using the IMAGE as the unit. THERE ARE TWO TARGETS WITH OPPOSITE VERDICTS, and
collapsing them made a permitted, fully-specified acquisition look impossible.

| requirement | ACRIS (pages) | Richmond DETAILS | Richmond IMAGES |
|---|---|---|---|
| stable id | 21,611,255 ✓ | 2,426,404 ✓ | 2,426,404 ✓ |
| resolvable address | ✓ doc_id → DocumentImageView | ✓ `/Search/viewDocumentInfo/<internal_id>` | ✓ mints a token |
| known extent | ✓ 16,901,071 docs → **148,798,851 pages** | ✓ **1 unit per document, free** | ✗ none |
| known exclusions | ✓ 174,142 with reasons | ✓ none needed | ✗ all `unknown` |
| **permitted** | ✓ | ✓ **no bot detection on the county host** | ✗ Cloudflare at UCS |
| measured cost | 75-90 pg/s → 19-22 d | 4.4 doc/s @ conc 8, 0 err → ~153 h | n/a |

Richmond's DETAIL acquisition is a cleaner map than ACRIS's: extent costs ACRIS
16.9M page-map lookups and costs Richmond nothing, because a detail page is one
unit. It yields parties-with-roles, consideration, status, every block/lot and
image_state - most of the analytical value. Only EXTRACTION needs the images.

ACRIS acquisition is COSTED AND READY: 148.8M pages at the measured 75-90 pg/s =
19-22 days, matching the independent estimate in 02-acquisition. Two gaps remain -
extent covers 78.2% (the 4.54M personal-property register was pulled after the
mapping was built and never mapped) and page maps stop at 2026-07 (16,923 August
documents have endpoints but no known extent).
