---
name: project_acris_selection_job
description: "THREE LAYERS (index / doc-id endpoint / pages) and the daily-vs-audit split; the image URL is a pure function of doc_id, and the Socrata pull was serial while the concurrent helper sat unused in the same file"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7c5a3ccb-a88e-40cd-a587-cc575cf7a400
  modified: 2026-08-14T19:00:17.004Z
---

Settled 2026-08-14. Selection is **three layers**, and conflating them is what made
the pull look inherently slow:

| layer | what it is | cost | status |
|---|---|---|---|
| **index** | ACRIS structured record, 5 published Socrata datasets | minutes | pulling |
| **doc-id endpoint** | the 17M direct image access points | ~minutes (Socrata) | HAVE IT |
| **pages** | page count + geometry per doc_id | **15–27 h**, per-document | DONE, one-off |

The page layer was a ONE-TIME drive-sizing job (how many pages → how much disk). It
does not repeat. Login: *"the pages was just to help us understand size of harddrive."*

⚠ **THE IMAGE ACCESS POINT IS A PURE FUNCTION OF doc_id** —
`https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage?doc_id={id}&page={n}`.
So the "17 million directly mapped access points" need nothing stored: every id in
the selection map IS the endpoint. No navigation, no URL column.
(⚠ Still bound by [[project_acris_bulk_acquisition]] — never build a bulk image
scraper, never work around bot detection, STOP on a refusal.)

## The index — 100,764,843 rows, all published

MASTER `bnx9-e6tj` 17,065,090 · LEGALS `8h5j-fqxa` 22,727,180 ·
**PARTIES `636b-3b5g` 46,540,137** · REFS `pwkr-dpni` 8,699,896 · REMARKS `9p4w-7npp` 5,732,540

**174,086 documents (1.03%) have NO retrievable image** — 108,817 at hid_TotalPages 0,
65,269 microfilm-era at −1. Mostly RTXL (108,386) but **19,712 DEEDS and 16,440
MORTGAGES**, for which the index is the entire record, forever. Measured over
`acris_maps.jsonl` (16,977,910 of 17,049,742) so the true figure is slightly higher.
`_noimage_ids.txt` + `pull_index_noimage.py` → `index_noimage.jsonl`.
**PULLED 2026-08-14: all 174,086 in 326s, 360 MB.** master 100% · parties 174,067 ·
legals 174,018 · remarks 89.6% · **references only 2.0%** (the 2,000-doc sample said
28% — a small sample over-read a sparse surface by 14x; size sparse coverage on the
whole set, never on a sample). 19 documents carry no party row at all.
`party_type` = {1: 217,234 · 2: 76,880 · 3: 9} — both sides of the instrument present,
which is what makes it usable for role verification rather than just names.

**⚠ THE INDEX IS THE FLOOR, NEVER THE TARGET — THE WHOLE POINT IS TO BEAT IT.**
Login, 2026-08-14: *"were trying to read the documents to create a much better
indexed representation of these docs with legitimate parties, $, descriptions,
terms... the index is so base level and is a poor representation of the data in a
doc."* So the index is authoritative for a NARROW question — did this party
appear, on which side, what type, what date, which BBL — and for nothing else.
⚠ **Entity ≠ person.** The index records `123 MAIN ST LLC`; the instrument says
"by John Smith, its Managing Member". Only the document names the human behind
the SPE, and that is the thread linking one SPE to the next deal (see
[[project_bkrea_debt_throughline]], [[project_bkrea_reach_ladder_roles]]).
Signature/notary/"by ___, its ___" blocks are therefore HIGH-VALUE extraction
targets — and they sit at the END of documents, where
[[feedback_bkrea_document_over_page]] applies: never cap how many pages are read.
⚠ **Money is a LAST RESORT from the index, not a source.** Good on some types,
wrong on others (0 for every DEVR), and many documents involve no money at all —
so a null must distinguish *no consideration exists* from *not yet read*. Never 0.
⚠ **Legal description and SF are NOT in the index in any form.** No fusion trick
recovers them; they come from the instrument body and the exhibits or not at all.

**PARTIES is fusion's third channel and it fixes the one thing provenance can't see** —
it carries `party_type` per name, from a structured source. See
[[project_acris_resolution_model]]: character-level agreement graded a mortgagee of
`articles of personal property now or hereafter attached to` as SETTLED. An index
lookup catches that; a second OCR channel cannot.

## ⚠ SERIAL PAGING WAS THE WHOLE COST, AND THE FIX WAS ALREADY IN THE FILE

`bulk.socrata()` walked pages one at a time while `arcgis_all()` (same file) got the
count first and fetched concurrently, and `socrata_in()` (same file) chunked
concurrently. 17M rows at 50,000/page = 341 sequential round trips.
**Measured 4.38x** (median of 3, alternating order, identical id sets).
`acquire_index._by_doc` had the identical defect — serial chunks while `socrata_in`
sat unused in the module it already imported.

⚠ **The first A/B said parallel was 3.7x SLOWER.** I ran the parallel arm first, which
tripped rate limiting; the serial arm then measured the calm afterwards. **Alternate
the order and repeat, or a burst-throttled API will lie about which arm is faster.**
⚠ 8 workers ≈ serial (throttled). 5 is the ceiling. count(1) costs 0.6s — not the issue.

## Daily vs audit — two jobs, not one

- **`selection_daily.py`** — O(delta). Asks ACRIS `:updated_at > watermark`, checks only
  those ids against both sides. Local membership via `_local_ids.idx` (sorted 8-byte
  hashes, 136 MB, written by the audit) — a binary search, not a 19.5M-line scan.
  Seconds when nothing moved.
- **`selection_cross.py`** — the audit. Crosses all THREE PAIRS separately, repairs both
  sides, re-verifies. **20 min. Verified clean 2026-08-14: ALL THREE AGREE at 17,049,742.**
- Routine **`acris-selection`** runs 04:00 daily.

⚠ **THE DAILY CANNOT REPLACE THE AUDIT.** A forward-only monitor inherits every gap it
already has and reports clean forever — it cannot see a withdrawal or re-index. Both
schedules, or the cheap check gets mistaken for a complete one.
⚠ **The old `daily_delta.py`/`map_delta.py` (Windows task, 04:00) writes to LOCAL FILES
ONLY and never touches Supabase** — which is what acquisition reads. That gap is why
this job exists.

## ⚠ BULK PULL: $offset IS THE BOTTLENECK, AND TWO SPLITTER BUGS THAT LOSE ROWS SILENTLY

Measured 2026-08-14 on PARTIES, 20,000 rows/request:
`offset 0` 1.1s · `1M` 4.5s · `5M` 7.6s · `20M` 21.4s · `40M` **23.7s (~850 rows/s)**.
The server walks every skipped row, so a paged pull starts fast and crawls — and the
CUMULATIVE rows/s hides it because early speed props up the average. Master's
instantaneous rate had already halved by 43%.

**Fix: partition by `document_id` range, never page deep.** A range filter with
`$order=document_id` is an index scan and stays FLAT (2.4s at offset 0, 2.1s at offset
500,000). Partition bounds come from a LOCAL histogram of the 17M ids we already hold
(13s, 9,148 eight-char prefixes) — zero planning queries. `pull_index_fast.py`.
Rates: 21k rows/s (master) → 56k rows/s once the splitter stopped churning.
⚠ `:id` keyset filtering is NOT supported (400); values look like `row-29wv~chui_2buq`.
⚠ Range filter + `$order=:id` is stable but defeats the index: 28–67s vs 2.4s.
⚠ Fetch-and-split wastes whole pages — an overfull partition transfers 50,000 rows
before you learn it is overfull (155 rows written after 80 requests).

**⚠ BUG 1 — AN OPEN SENTINEL BREAKS THE SPLITTER.** Last range ended at `"￿"`.
When it came back full, `midpoint("FT_49900","￿")` fell back to ALPHA's midpoint
`'c'` — above every real id — so each "split" only trimmed the top and never divided
the data. Lost 23,010 master rows, ALL `FT_4990*`. Bound the last range by
`next_key()` of a real prefix and add a separate open tail range.

**⚠ BUG 2 — A MIDPOINT MAY NOT LIE BETWEEN ITS OWN ENDPOINTS.** Splitting
["20030130","20030200") produced `"200301W"` — a LETTER in a numeric id space. ASCII
says 'W' > '3'; the column is text under a **non-C collation** where that is not
guaranteed, so the two halves did not tile the parent and rows fell in neither.
Legals lost **202,275** rows this way, on top of the 26,700 from bug 1. Same collation
trap as the false 660,708-document shortfall in `reconcile_selection.py` — punctuation
there, a letter here. **Keep every bound inside the character class the data uses:**
ACRIS ids are an era marker then digits only (`pos 0 [2BF] · 1 [0KT] · 2 [012_] ·
3+ [0-9]`, measured over 3M ids). `subdivide()` tiles explicitly and uses digits only.

**⚠ BUG 3 — A DOCUMENT CANNOT BE SEPARATED FROM ITSELF, SO THE DESCENT NEVER ENDS.**
Splitting divides the *id space*; when one `document_id` carries ≥ the 50,000-row page
limit, every child still contains that whole document. Each level yields ten empty
siblings plus one child as big as its parent, forever. Parties froze at **exactly
31,898,850 (68.5%)** for ten minutes while requests climbed 3,800 → 5,080 — killed and
re-run 2026-08-14.
⚠ **IT DOES NOT LOOK STUCK.** Requests climb steadily and the *queue even drains*
(the empty siblings pop while one hot chain descends), so every health signal except
the row count looks normal. Queue −114 over 1,280 requests solves to 106 splits and
~1,174 zero-row children — 106×11. **Reading the queue as progress is the mistake.**
Fix: when a full page's first and last `document_id` are equal, page that one document
with `$offset` + `$order=:id` (safe only here — one document, small offsets, unique
sort) and resume the range at `doc + "0"`. Plus a deep-split warning at id length ≥ 9,
because a normal split happens at 4–7.
⚠ **The tiling was NOT at fault and I nearly "fixed" it.** `_diag_tiling.py` counts a
parent, subdivides, and counts every child: they summed EXACTLY at every level. Probe
the splitter against the server before rewriting it — the arithmetic on the log named
the real cause, the plausible suspect did not.
⚠ **Back-check: master, legals and remarks were never exposed.** Master is one row per
document, and all three reconciled EXACTLY against live counts — which is the check
that would have caught this. Only parties (2.73 rows/doc, high variance) could hit it.

⚠ **NEITHER OF THE FIRST TWO BUGS RAISED AN ERROR.** No request failed, nothing was logged, and the only
symptom was a short total — which is why every dataset compares its own row count to
the live count and REFUSES to swap in a repaired file that does not reconcile
(`repair_tail.py` left legals untouched when its repair came up 202,275 short).

⚠ **THREE CONCURRENT WRITERS, NO ERROR.** Two launches printed no log and looked like
failures; all three appended to one gzip at triple speed, which reads as good news.
`pull_index_fast.py` now takes a PID lock. Never remove the lock to force a run.

## ⚠ SOCRATA IS MONTHLY — the lag is ARCHITECTURAL, not a tuning problem (2026-08-18)

All 19 ACRIS-family datasets are declared `Update Frequency: Monthly` and move together
(2026-08-10 13:35Z, `good_through_date` 2026-07-31). So `selection_daily.py` polls a
source that changes 12×/year: **"0 changed rows" is the correct answer on ~30 of 31 days**
and "clean" reads as "we're current" when it means "nothing arrived". Verified three ways
— SoQL `max(:updated_at)`, `/api/views/{id}.json` `rowsUpdatedAt`, `metadata/v1`
`dataUpdatedAt` — plus content: recordings run ~1,100–1,500/day right up to 07-31 and stop
on a clean month boundary. We are not behind ACRIS; **this channel is 18–41 days behind
reality** (~1,300 docs/day unseen).

**THE LIVE DISCOVERY CHANNEL EXISTS AND WORKS.** Every a836 endpoint we use
(`DocumentImageView`, `GetImage`, `GetPdf`) is keyed by a doc_id we must already have —
discovery was the missing capability, and the monthly index was the only source of ids.

    POST https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentTypeResult

⚠ **the doc_id is NOT in any URL** — grepping `doc_id=` returns zero. It arrives as a bare
argument on each row's buttons: `onclick='JavaScript:go_detail("2026072900842001")'` /
`go_image(...)`. Rows also carry borough, block, lot, CRFN, doc date, recorded datetime to
the second, **page count**, party 1/2/3 and doc amount.

Measured constraints (from `/DS/Scripts/DocumentType.js`, not guessed): doc type MANDATORY
(no all-types query — one request per type) · borough MANDATORY (`0 ALL BOROUGHS` sits at
index 0 and the handler rejects it) · date range ≤ 31 days · `cmb_date` presets `7` / `31`
/ `DR` make a daily delta one parameter · `hid_max_rows` 10/25/50/99 + `hid_page` · **no
total-record count is displayed**, so a sweep must page to exhaustion and cannot verify
itself against a stated total. Cost ≈ 97 real-property types × 5 boroughs ≈ 485 queries
(~8–10 min/day at the 1 req/s pacing). UCC types use a separate path, `/DS/DocumentSearch/UCC`.
6/6 requests HTTP 200, no refusal, session established the documented way (GET the landing
page, keep the cookies it sets).

**Proof it closes a real hole:** 10 Queens DEED ids returned for "Last 7 days", all
recorded 8/17/2026, **0 of 10 present** in `acris_maps.jsonl`, `_remaining_sorted.jsonl`
or `docmaps.jsonl`.

⚠ **The doc_id's leading date is the SUBMISSION date, not the recorded date.**
`2026072900842001` = 2026-07-29 + seq 00842 + sub 001, but it was recorded 8/17 — 19 days
later. Format is `YYYYMMDD` + 5-digit seq + 3-digit sub-index (sub frequencies decay
001→523,699, 002→202,091, 003→128,186). So the id space IS arithmetically enumerable —
**and enumeration is the wrong answer**: ~1,300 guesses/day against the image host,
end-of-doc placeholders served as HTTP 200 make existence detection unreliable, and the
leading date would mis-date everything. Search asks a question; enumeration tries keys.

**THE 126 DOC TYPES DECOMPOSE EXACTLY** (control codes `7isb-wh4c`, 126 rows, all
record_type D): **95** occur in real property master (the audit's 95 — and zero orphans
the other way, every type in our 17M corpus is in the vocabulary) · **29** are UCC AND
FEDERAL LIENS living in the PERSONAL property master `sv7x-dduq` — **4,547,264 documents
entirely outside the map**, zero type overlap with real property, incl. INIT 1,007,504 ·
INIC (INITIAL COOP UCC1) 970,047 · TERM 988,530 · FL 377,103 · RFL 192,680 — the co-op
financing instruments, where no mortgage is recorded · **2** exist nowhere in either
corpus: `REIT` (REAL ESTATE INV TRUST DEED) and `SI CORR` (SI BILLING UPDATE OFFICE USE).
⚠ `SI CORR` + the live borough dropdown offering `5 STATEN ISLAND / RICHMOND` are worth one
query against the parked "ACRIS holds zero Staten Island" assumption. UNTESTED.

**PERSONAL PROPERTY IS NOW SPECIFIED** (2026-08-18, `pp_spec.py` → `index_full/personal_master.jsonl.gz`,
13.1 min, 143 requests, 0 failed). Verified against two independent witnesses: 4,547,264
rows written == live row count, and **4,544,590 distinct document_ids == Socrata's own
`count(distinct document_id)`** — the file was built by partitioned prefix ranges, the
check came from a SoQL aggregate, and they agree exactly. 30 doc types, 0 rows without an
id, recorded 1964–2026, and roughly half the ids are `FT_` microfilm-era. Register total
now specified: 17,049,742 + 4,544,590 = **21,594,332**.
⚠ It is a SPECIFICATION, not a map — ids/type/date only, no page ranges. It must NOT be
pushed into `document_map`: `no_image` there is computed from `total_pages`, so a bare id
asserts "ACRIS holds no image for this document", a permanent claim about a record nobody
has looked at.
