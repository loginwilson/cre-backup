# ACRIS · PHASE 1 — SELECTION

**Status: systemized.** Verified clean 2026-08-14. Run `python status.py` for
current numbers — nothing here restates one a job already records.

## GOAL

Know every document that exists, so acquisition can fetch it and nothing is
invisible to every later stage. Selection is **two products**:

| product | what it is | why it matters |
|---|---|---|
| **doc-id map** | 17,049,742 documents | each id **is** a direct image endpoint |
| **support index** | 100,764,843 rows, 5 datasets | the only record for image-less documents, and extraction's third channel |

⚠ **The doc id needs nothing else to reach the image.** The endpoint is a pure
function of it:
`https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage?doc_id={id}&page={n}`.
There is no URL to store and no page to navigate — that is what makes acquisition
fast. The page-geometry layer (`acris_maps.jsonl`) was a **one-time** job to size
the drive; it took 15–27 h and does not repeat.

## WHERE IT LIVES — three places, each able to move independently

| | what | authority |
|---|---|---|
| **ACRIS** | Socrata `bnx9-e6tj` + 4 index datasets | the source of truth |
| **local** | `acris_maps.jsonl`, `_remaining_sorted.jsonl`, `docmaps.jsonl`, `census_maps.jsonl` | working copy |
| **Supabase** | `document_map` | **what acquisition reads** |

A document missing from Supabase is never downloaded, never decoded, and the
event it records is invisible forever. That is the whole reason this phase has a
daily job.

## ENTRY POINTS

```
python status.py                          # where everything stands
python selection_daily.py --repair        # doc-id delta (seconds if nothing moved)
python index_daily.py --apply             # support-index delta
python selection_cross.py --repair        # THE AUDIT — all three pairs (~20 min)
python pull_index_fast.py                 # rebuild the index baseline (~70 min)
python reconcile_selection.py             # local vs Supabase, exact per slice
```

Scheduled: routine **`acris-selection`**, 04:00 daily (`~/.claude/scheduled-tasks/acris-selection/SKILL.md`).
Daily = the two deltas. Monday = the two full rebuilds.

## THE RULES

1. **Only ever ADD.** A document on one side and not another means the other side
   is behind. Deletion needs a human.
2. **An unanswerable query is UNKNOWN, never zero.** A range has twice failed
   every retry and answered in one second minutes later. Re-run; do not lower
   the number. A total that excludes an uncounted slice is a **lower bound**, and
   the run is not a reconciliation.
3. **Never repair a number to make a check pass.** Report the disagreement.
   `repair_tail.py` refuses to swap in a repaired file that does not reconcile.
4. **Cross all three PAIRS, never a chain.** A=B and B=C implies A=C only if all
   three were measured the same way, and they are not: ACRIS counts rows *with
   duplicate ids*, local counts distinct ids across append-only files, Supabase
   counts primary keys.
5. **Count distinct ids, not lines.** 19,549,196 local lines collapse to
   17,049,742 ids. Comparing lines to rows reports every duplicate as a loss.
6. **The daily cannot replace the audit.** A forward-only watermark inherits
   every gap it already has and reports clean forever — it cannot see a
   withdrawal or a re-index.
7. **A watermark advances only after the work is done, never on a look.** An
   earlier version saved state before the branch, so a report-only run moved the
   cutoff and hid 28,196 documents permanently while printing success.
8. **One writer.** `pull_index_fast.py` takes a PID lock. Three concurrent copies
   once interleaved the same gzip with no error at triple speed.

## CALIBRATIONS — value · measurement · failure if changed

Pointers, never copies: the authority is the code line, this table is why it
holds that value.

| setting | where | value | measured | failure if wrong |
|---|---|---|---|---|
| pull concurrency | `bulk.py:WORKERS` | **5** | 5 workers 5.3s vs serial 10.0s on 5 pages; **8 workers 10.4s ≈ serial** (throttled), 2026-08-14 | raising it reads as tuning and buys nothing; lowering costs 4.4x |
| page limit | `pull_index_fast.py:LIMIT` | **50,000** | honoured by Socrata; a response *exactly* at the limit is treated as truncated | accepting a full page writes a silently cut partition |
| partition target rows | `pull_index_fast.py:TARGET` | **40,000** (80% of limit) | leaves headroom so overflow is rare, not routine | at the limit every partition splits and the queue churns |
| parties target | `pull_index_fast.py:TARGET_BY_SET` | **12,000** | 2.73 rows/doc *average* but high variance; at 40,000 the queue went 533→2,195 with the row count frozen, 2026-08-14 | sizing by the mean stalls the pull entirely |
| partition bounds | `_id_prefix_counts.json` | 9,148 8-char prefixes | one 13s local pass over 17M ids; zero server planning queries | server-side planning costs ~9,000 count queries |
| split alphabet | `pull_index_fast.py:DIGITS` | **digits only** past pos 3 | id charset by position over 3M ids: `0 [2BF] · 1 [0KT] · 2 [012_] · 3+ [0-9]` | a letter bound cost 202,275 legals rows |
| Supabase slice key | `reconcile_selection.py:slice_of` | first 4 chars | matches the PK's natural order → index scan per slice | whole-table `count=exact` times out at 17M |
| exact-count retries | `reconcile_selection.py:count_exact` | 3, then split, then re-ask at end | a range failed every retry twice and answered in 1s minutes later | splitting on the first failure subdivides a range that was never too big |
| local id index | `_local_ids.idx` | 8-byte hashes, sorted | 136 MB, loads ~1s; rebuilt by every audit | without it the daily job must scan 19.5M lines (4 min) |
| watermarks | `_selection_daily_state.json`, `_index_daily_state.json` | per dataset | advance only after a clean re-check | advancing on a look hid 28,196 documents permanently |

## ⚠ TRAPS THAT COST REAL TIME HERE

- **`$offset` degrades with depth** — 1.1s at offset 0, **23.7s at 40M**. Never
  page deep; partition on `document_id` range with `$order=document_id` (flat:
  2.4s at offset 0, 2.1s at offset 500,000). `:id` keyset filtering is a 400.
- **`$order` is mandatory on any paged request.** Without it the row TOTAL stays
  correct while rows are silently duplicated and dropped — the one check anybody
  runs is the one this failure passes.
- **Bounds must stay inside the data's character class.** `next_key("2009")` by
  character-bump gives `"200:"`, an EMPTY range under a non-C collation → a false
  660,708-document shortfall. A split midpoint of `"200301W"` — a letter in a
  numeric id space — cost 202,275 legals rows. ACRIS ids are an era marker then
  **digits only** (`pos 0 [2BF] · 1 [0KT] · 2 [012_] · 3+ [0-9]`, over 3M ids).
- **An open sentinel breaks a splitter.** A range ending at `"￿"` split to a
  midpoint above every real id, so it never divided the data: 23,010 master rows
  lost, all `FT_4990*`.
- **Sizing by an average fails where variance is high.** Parties averages 2.73
  rows/document but some documents carry dozens; partitions built from the mean
  overflowed constantly and the queue churned 533 → 2,195 with the row count
  frozen. Use `TARGET_BY_SET`.
- **`daily_delta.py` / `map_delta.py`** (Windows Task Scheduler, 04:00) diff ACRIS
  against LOCAL FILES and write to LOCAL FILES only. They never touch Supabase.
  That gap is why `acris-selection` exists; it is the superset.

## ⚠ WHAT SELECTION CANNOT TELL YOU

All three sides agreeing proves the **copy** is faithful. It says nothing about
whether the **source** is complete — all three would agree on a hole in ACRIS.

**ACRIS holds ZERO Staten Island recordings.** `recorded_borough` has only four
values: Manhattan 6,213,473 · Queens 4,926,801 · Brooklyn 4,336,657 · Bronx
1,588,159. Richmond County deeds are with the **County Clerk**. LEGALS carries
207,392 rows referencing Staten Island *properties* recorded elsewhere, so the
parcels are visible while their conveyance history is not — the shape most likely
to read as coverage. Known, parked, to be consolidated with the county clerk.

## IMAGE-LESS DOCUMENTS — where the index IS the record

**174,142 documents (1.03%)** return ACRIS's placeholder rather than a page:
108,817 at `hid_TotalPages` 0, 65,269 microfilm-era at −1. Mostly RTXL (108,386),
but **19,712 DEEDS and 16,440 MORTGAGES** are in the set and no image of them
will ever exist. `_noimage_ids.txt` → `pull_index_noimage.py` →
`index_noimage.jsonl` (360 MB). Coverage: master 100% · parties 174,067 ·
legals 174,018 · remarks 89.6% · **references 2.0%**.

⚠ A 2,000-document sample put references at 28%. The true figure is 2.0% —
**a small sample over-read a sparse surface by 14x.** Size sparse coverage on the
whole set, never on a sample.

## DEEP DOCS

`SELECTION.md` · `DOCUMENT_INVENTORY.md` · `PARCEL_BANK.md` ·
`PARCEL_LIFECYCLE.md` · `SPINE_DEFECTS.md`

Memory: `project_acris_selection_job.md` · `project_acris_document_inventory.md`
