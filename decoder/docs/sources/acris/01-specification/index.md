# ACRIS · SPECIFICATION · **INDEX** — the support index daily

**Keeps current:** ACRIS's own structured record — **100,764,843 rows** across
five published Socrata datasets. This is extraction's **third fusion channel**,
and for 174,142 documents it is the entire record, permanently.

The other track is [selection.md](selection.md).

## THE STEPS WE FOLLOW TODAY

```bash
python index_daily.py            # report only — seconds
python index_daily.py --apply    # write the delta and advance the watermark
python pull_index_fast.py        # the full partitioned pull — rebuild only
```

## STATE — 5/5 EXACT, 2026-08-14

| dataset | rows | file |
|---|---|---|
| master `bnx9-e6tj` | 17,065,090 | 403 MB |
| legals `8h5j-fqxa` | 22,727,180 | 411 MB |
| **parties `636b-3b5g`** | **46,540,137** | 1,083 MB |
| references `pwkr-dpni` | 8,699,896 | 115 MB |
| remarks `9p4w-7npp` | 5,732,540 | 96 MB |

⚠ **`party_type` is the row that matters.** It is who-was-grantor from a
structured source, and the only check that catches a **role inversion** — swap
grantor and grantee and transcription scoring reads 100% while the lineage runs
backwards. No second OCR channel can see that.

⚠ **Do NOT trust `document_amt` for money.** 0 for every DEVR. The index is
authoritative **per field, never wholesale**.

## CALIBRATIONS

| setting | value | measured | failure if wrong |
|---|---|---|---|
| `LIMIT` | 50,000 | honoured by Socrata | at exactly the limit a page is indistinguishable from truncated |
| `WORKERS` | 5 | **8 ≈ serial** (throttled), 2026-08-14 | raising it looks like tuning and costs 4x |
| partition bounds | local histogram, 9,148 prefixes | 13s, zero planning queries | server-side planning costs more than the pull |
| `--apply` | required to persist | 2026-08-14 | without it the job re-seeds every run and **can never detect anything** |

## ⚠ THE PULL: NEVER PAGE DEEP, AND NEVER GUESS A SPLIT POINT

`$offset` collapses — 1.1s at offset 0, **23.7s at 40M (~850 rows/s)** — and the
cumulative rows/s hides it because early speed props up the average. Partition by
`document_id` range with `$order=document_id` instead: an index scan, flat.

**Three splitter bugs, none of which raised an error.** Every one was a silent
shortfall that looked like healthy progress:

1. **An open sentinel breaks the splitter.** Last range ended at `"￿"`, so
   the midpoint fell above every real id and each "split" only trimmed the top.
   Lost 23,010 master rows.
2. **A midpoint may not lie between its own endpoints.** Splitting produced
   `"200301W"` — a **letter in numeric id space** under a non-C collation, so the
   halves did not tile the parent. Lost **202,275** legals rows.
3. **A document cannot be separated from itself.** One `document_id` with
   ≥ `LIMIT` rows makes every child as big as its parent. Parties froze at
   **exactly 31,898,850** for ten minutes while requests climbed 3,800 → 5,080.

⚠ **Bug 3 does not look stuck.** Requests climb and the queue even *drains* — the
empty siblings pop while one hot chain descends forever. Every health signal
except the row count reads normal. **Reading the queue as progress is the
mistake.**

**The fix replaced blind splitting entirely: keyset advance.** Keep the rows
already fetched, drop the partial last document, resume from that boundary.
Progress is guaranteed (`last > first >= lo`) and nothing is lost. It also
stopped discarding overfull pages:

| | rows/s |
|---|---|
| blind split | 8,645 |
| **keyset advance** | **52,559** |

⚠ **What caught all three: each dataset compares its own count to the live count
and REFUSES to record itself complete otherwise.** That check earned its keep
three times in one day. `repair_tail.py` likewise refuses to swap in a repaired
file that does not reconcile.

⚠ **Three concurrent writers, no error.** Two launches printed no log and looked
like failures; all three appended to one gzip at triple speed, which reads as
good news. There is now a PID lock — **never remove it to force a run.**

⚠ **A delta larger than 5M rows raises** — that is a republish, not a change set.

## PROVEN, NOT CLAIMED — 2026-08-14

- all five datasets reconciled **exactly** against live counts
- delta over a forced 4-week window: **174,163 rows** across all five, **18s**
- **cross-check:** the master delta is **28,374** — identical to what
  `selection_daily.py` found independently for the same window
