# ACRIS · SPECIFICATION · **SELECTION** — the doc-id daily

**Keeps current:** the doc-id map — which ACRIS documents exist and how to reach
them. **17,049,742 documents**, reconciled ACRIS ↔ local ↔ Supabase.

The other track is [index.md](index.md). Phase-level docs: [workflow.md](workflow.md)
· [data.md](data.md).

## THE STEPS WE FOLLOW TODAY

```bash
python selection_daily.py            # look — seconds
python selection_daily.py --repair   # look and populate both sides
python selection_cross.py            # the exhaustive audit — ~20 min
```

The `acris-selection` routine runs the daily at **04:00**.

## ⚠ TWO JOBS ON PURPOSE, AND THE CHEAP ONE CANNOT REPLACE THE COMPLETE ONE

| | asks | cost |
|---|---|---|
| `selection_daily.py` | `:updated_at > watermark`, then only those ids | **seconds** |
| `selection_cross.py` | every id, all three pairs crossed separately | ~20 min |

⚠ **A forward-only monitor inherits every gap it already has and reports clean
forever.** It cannot see a withdrawal or a re-index. Both schedules, or the cheap
check gets mistaken for a complete one.

⚠ **The audit crosses all THREE PAIRS separately**, not totals against totals.
ACRIS↔local, ACRIS↔Supabase, local↔Supabase. Two sides agreeing while the third
drifts is invisible to a totals check.

## CALIBRATIONS

| setting | value | measured | failure if wrong |
|---|---|---|---|
| membership test, local | `_local_ids.idx`, sorted 8-byte hashes, 136 MB | binary search vs 19.5M-line scan | a linear scan makes the daily as slow as the audit, so it stops being run |
| membership test, Supabase | `document_id=in.(...)`, batches of 150 | 2026-08-14 | larger batches exceed the URL limit and return a **404, which PostgREST answers as an empty result** — reading as "nothing missing" |
| watermark advance | only after work completes | a report-only run once advanced it and the next real run found 0 rows | the skipped window becomes invisible **forever** while printing "map is current" |

## ⚠ TRAPS

**The audit's proof was in a file the daily never read.** `selection_cross.py`
wrote `_selection_cross_state.json`; `selection_daily.py` looked for a watermark
in `_selection_daily_state.json`, found none, and refused with *"run
selection_cross.py first"* — which **had already run and passed**. Scheduled at
04:00, it would have refused every night indefinitely. Fixed 2026-08-14:
`seed_from_audit()` adopts a **clean** audit's `dataset_stamp`.

⚠ **Seed with the stamp, never the clock.** `checked_at` is naive local time;
ACRIS `:updated_at` is UTC. Seeding from wall-clock silently skips the EDT
offset — four hours of updates, once, invisibly.

⚠ **Only from a CLEAN audit.** Seeding from one that found differences would
declare those differences already handled.

⚠ **19,549,196 lines collapse to 17,049,742 distinct ids.** The mappers append,
so re-runs rewrite the same id. Comparing lines to rows reports every duplicate
as a loss.

⚠ **`document_id` is not unique in MASTER** (17,065,090 rows vs 17,049,742
documents). Dedupe before counting anything.

## PROVEN, NOT CLAIMED — 2026-08-14

- audit: **ALL THREE AGREE at 17,049,742**, `missing_locally: 0`, verdict clean
- daily over a forced 4-week window: **28,374 documents**, both sides hold all,
  missing 0, **54s**
- the daily correctly refused to advance the watermark past a `--since` override

⚠ **All three agreeing proves the COPY is faithful, not that the SOURCE is
complete.** All three would agree just as perfectly on a hole in ACRIS. The known
hole is Staten Island — see [data.md](data.md).
