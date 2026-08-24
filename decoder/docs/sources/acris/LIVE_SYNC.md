# ACRIS · LIVE SYNC — the daily delta consolidation

**Monitor source → compare → delta manifest → back into sanitization.** Status:
**CONFIRMED**.

Cost is **O(what changed)**, never O(17M). The corpus is 17,049,742 documents and roughly
28,000 rows land on a given day; a daily job that re-proves the corpus in order to find the
day is the same error the selection job already corrected — *tracking the CORPUS instead of
the CHANGE*.

---

## 1 · ⚠ THE FIELD THAT MAKES THIS CHEAP IS NOT IN THE DATA

This is the single most important fact in the phase.

```
modified_date        a COLUMN in the record    lags ~11 days
recorded_datetime    a COLUMN in the record    lags ~11 days
:updated_at          SOCRATA METADATA          when the row LANDED
```

**Measured 2026-08-11:** the newest `recorded_datetime` in all of ACRIS was **2026-07-31**,
and a query for *"recorded since 2026-08-01"* returned **ZERO** — while **28,196 rows had
actually landed** in that window.

A daily job keyed on `recorded_datetime` reports "nothing new" every day, forever, and
looks perfectly healthy while falling ~11 days behind and never catching up. **Key every
delta on `:updated_at`.**

---

## 2 · The jobs, and which is which

| job | question it answers | cost |
|---|---|---|
| **`map_delta.py`** | what did ACRIS publish since last time — find it and map it | **THE DAILY COMMAND** |
| `daily_delta.py` | the scheduled wrapper Task Scheduler runs | — |
| `index_daily.py` | keep the 100.7M-row support index current, delta only | O(changed) |
| `selection_daily.py` | which document_map rows need to move | O(changed) |
| `selection_delta.py` | live ACRIS vs `document_map` **in Supabase** | O(changed) |
| `selection_cross.py` | ⚠ the three-way **AUDIT** — not a daily job | ~20 min |

```
python map_delta.py            find + map + advance the watermark
python map_delta.py --check    report only. Maps nothing, advances nothing.
python map_delta.py --full     exhaustive per-type diff. Monthly. Slow.
```

⚠ **`selection_cross.py` IS AN AUDIT AND A WRONG DAILY JOB.** It reads all four map files
(19.5M lines, ~4 min), counts 32 Supabase slices (~3 min) and pulls ACRIS per type
(~10 min) — twenty minutes re-proving 17,049,742 documents that did not move, to find the
handful that did. Run it weekly or after an incident, never nightly.

---

## 3 · ⚠ The watermark is the thing that can silently rot

**A watermark that advances on an assumption is worse than no watermark**, because it
converts a gap into a permanent, invisible one.

- **Never advance on "the request came back."** A response arriving is not evidence
  anything was written. `map_delta.py` guards exactly this: a run that advanced the
  watermark to the current stamp **without mapping anything** is the failure mode.
- ⚠ **A FORWARD-ONLY WATERMARK INHERITS EVERY GAP IT ALREADY HAS AND REPORTS CLEAN
  FOREVER.** It cannot see a row that was missed *before* the watermark was set. `index_daily.py`
  **extends** the baseline; it **cannot replace** it. The baseline comes from
  `pull_index_fast.py` (100,764,843 rows, ~1 h) and the monthly `--full` diff is what
  catches what the watermark structurally cannot.

---

## 4 · The scheduled wrapper, and how to read it

```
Task        ACRIS-MapDelta-Daily        (setup_schedule.ps1)
Log         _delta_daily.log            rotates at 5 MB
Summary     _delta_daily_status.tsv     one line per run, greppable
```

⚠ **IT ALWAYS EXITS 0, DELIBERATELY.** A refusal is not a failure of the job: ACRIS
declines, `map_delta` **holds the watermark**, and tomorrow's run picks up exactly the same
work. Exiting non-zero would paint the task red in Task Scheduler and train you to ignore
it — which is worse than silence.

**So the TSV is where you look, not the task status.** A run that mapped nothing writes
`PARTIAL`, and **two `PARTIAL`s in a row is the signal that something is actually wrong.**

⚠ No console window, deliberately — the task this replaced opened a python window daily.

---

## 5 · Where the authority lives

```
ACRIS      the authority — what documents exist
local      jsonl map files on this machine      "is my laptop current"
Supabase   document_map                          what acquisition will actually read
```

`map_delta.py` diffs against **local files**, which answers *"is my laptop current"* — a
real question, and **not** the one that governs acquisition. `selection_delta.py` exists
because the authority for what gets fetched is **`document_map` in Supabase**.

⚠ Paginate every Supabase read — there is a silent 1,000-row cap.

---

## 6 · Deciding what is live is DERIVED, not remembered

`whats_live.py` computes the carry list from the **import graph**: start at the entry
points genuinely run — the scheduled routine's commands and the phase docs' runbooks — walk
local imports transitively, and everything reached is live. Everything else is archive **by
default**, which is the safe direction: an archived file is one `git mv` from returning.

⚠ **DECIDING THE CARRY LIST FROM MEMORY IS HOW THINGS GET LOST.** There are 261 python
files here; nobody holds which twenty are current, and it changes weekly. This is the file
that answers *"everytime we add something new it just gets lost in the fold."*

```
python whats_live.py            # carry list and archive list
python whats_live.py --drift    # files that exist but nothing reaches
```

---

## 7 · Daily runbook

```
python map_delta.py --check                 # what landed, map nothing
python map_delta.py                         # map it, advance the watermark
python index_daily.py --apply               # extend the support index
python selection_daily.py --repair          # level document_map with ACRIS
grep PARTIAL _delta_daily_status.tsv | tail # two in a row = investigate
```

Monthly: `python map_delta.py --full` — the exhaustive per-type diff that catches what a
forward-only watermark cannot.

---

## 8 · ⚠ THE DELTA MUST LAND AS `parcel → parcel_document → document`, NOT AS DOCUMENTS

**Added 2026-08-18, after the specification was rebuilt around the parcel.** A delta that
writes correct, fresh, well-keyed document rows and stops there produces documents that
**acquisition can never fetch and no audit will flag as broken**. Both failures below are
silent — the delta reports success, the rows are genuinely present, and the documents are
never acquired.

### The shape, and why acquisition depends on it

```
parcel            1,250,935 rows   bbl, n_docs, first_date, last_date
   |                                ^ the pool selects HERE:  ORDER BY n_docs DESC
parcel_document  22,727,180 rows   bbl <-> document_id        ^ and filters on n_docs
   |
document         17,049,742 rows   document_id, doc_type, doc_date, reel...
```

`overnight.py` picks **parcels**, never documents:

```sql
SELECT bbl, n_docs FROM parcel WHERE n_docs BETWEEN ? AND ? ORDER BY n_docs DESC LIMIT ?
```

It then fetches that parcel's documents *through* `parcel_document`. **There is no code
path anywhere in acquisition that reads the `document` table directly.** A document is
reachable if and only if some parcel links to it.

### ⚠ FAILURE 1 — a document with no parcel link is unreachable forever

Write a row into `document` without its `parcel_document` links and the document exists,
is correct, and is invisible. It will sit in `coverage.py` as `NOT YET HELD` permanently —
a residue that never closes no matter how long the walk runs, and that looks exactly like
"we haven't got to it yet". Orphans already exist at roughly 0.2% in the early rows of the
table and ~0% in a random sample of 1,199, so the corpus is not clean on this today and a
new residue would not stand out.

**The delta must therefore carry the BBL links, not just the document id.** A doc id
without its parcels is not a decodable fact — it is an orphan with a name.

### ⚠ FAILURE 2 — a new document on an ALREADY-COMPLETE parcel is skipped

This one is worse, because the parcel is not new and nothing about it looks stale.

```python
# overnight.py — a parcel is "finished" iff its manifest shows nothing outstanding
for f in CP.BYPARCEL.rglob("_INDEX.md"):
    if "| not acquired |" in f.read_text(...):   continue
    finished.add(bbl)
queue = [b for b, _ in pool if b not in finished]
```

`_INDEX.md` is a **cached answer written when the parcel was materialised**. It is not
re-derived from the specification at skip time — deliberately, because re-deriving it cost
14 minutes and 0 pages on restart. So a parcel that was whole yesterday is still declared
whole today, and a document the delta added to it is **never queued**.

**The delta must invalidate the manifest of every parcel it touches.** Updating the
specification alone does not reopen a closed parcel.

⚠ **DELETE THE MANIFEST — DO NOT REGENERATE IT.** Both reopen the parcel, but measured
2026-08-18 they are four orders of magnitude apart:

| reopen method | per parcel | 34,000 parcels |
|---|---|---|
| re-run `parcel_folder.py --bbl` | 0.94 s | **8.9 hours** |
| `unlink()` the `_INDEX.md` | 1.85 ms | **63 seconds** |

```python
(BYPARCEL / b[0] / b[1:6] / b[6:] / "_INDEX.md").unlink(missing_ok=True)
```

A parcel with no `_INDEX.md` is never added to the driver's `finished` set, so it re-enters
the queue, is re-acquired, and the walk **materialises a fresh index at the end anyway** —
regenerating it up front is work that is about to be redone. The only thing lost between
the delete and the next walk is a browsable index for that parcel, for minutes.

⚠ At delta scale this is the difference between a sync that finishes inside a coffee break
and one that cannot run daily at all. A 9-hour reopen step would quietly force someone to
"just skip the ones that look complete" — which is precisely the failure this section
exists to prevent.

### The runbook — `reopen.py`, tested 2026-08-18 both ways

```
python reopen.py --from touched_bbls.txt          # report only (the default is safe)
python reopen.py --from touched_bbls.txt --apply  # delete the stale manifests
python reopen.py --apply                          # full sweep — prefer a pause
```

| mode | cost | when |
|---|---|---|
| `--from <file>` | O(parcels the delta touched) | **every delta.** The daily path. |
| no args | O(every materialised manifest) | periodic. Catches what the delta under-reported. |

⚠ **THE DELTA NARROWS THE CANDIDATES; THE SPECIFICATION DECIDES.** `reopen.py` re-reads
each candidate's manifest and compares it against the spec — it does not trust the delta's
claim that a row landed. A half-failed delta still reports the rows it believes it wrote,
so its own count can never detect its own failure. This is why the no-args sweep exists as
well: it is the only check that sees what the delta never mentioned.

⚠ **PASS BBLs IN A FILE, NEVER AS `--bbl` × 16,000** — Windows caps a command line near
32k characters and the call is silently truncated.

⚠ **COMPARE AGAINST DISTINCT DOCUMENTS OVER THE LINEAGE FAMILY, NOT `parcel.n_docs`.**
Manifests list every document across a parcel's predecessor lots, and a document recorded
against many lots is listed once. Summing `n_docs` over a family over-counts badly —
Manhattan block 4's condo units carry 2,693 links over 78 unique documents — and would
reopen thousands of parcels that are complete, re-walking the corpus for nothing.

⚠ **RUN IT AGAINST A PAUSED WALK, OR AT LEAST NOT DURING ONE.** The full sweep reads every
manifest on the same USB drive the workers are writing to; doing that mid-run cost a
measured **20 pg/s** on 2026-08-18.

Verified on 2026-08-18 in both directions, because a check that has only ever returned
"fine" is not a check: a manifest doctored to claim 50 documents against a specification
holding 57 was flagged `+7` and, in dry-run, correctly left on disk.

### Why the flow exists at all — it is not bookkeeping

The parcel grouping is what makes the corpus **readable oldest-to-newest**, which is the
whole basis of reading a chain rather than a pile of documents:

```
by-parcel/3/00247/0009/_INDEX.md     "98 documents in the ACRIS specification, oldest first"
  1966-11-18__BK_6630029500271__LDMK__295-271.pdf
  1974-01-07__BK_7430068201487__DEED__682-1487.pdf
  ...
```

A flat document list cannot produce that. Ownership, debt and lineage are all **sequences
on one parcel** — the deed that matters is the one before this mortgage, and the mortgage
that matters is the one still open. Lose the parcel grouping and every downstream question
becomes a join someone has to remember to write; keep it and the chronology is the
directory listing. `_INDEX.md` also carries the two facts a bare file list cannot: DOF
predecessor lots, and `no image` rows where the index *is* the whole record.

### Acceptance test — run this after every delta, and do not trust the row count

The delta's own "N rows inserted" cannot see either failure. Test reachability instead:

1. every new `document_id` appears in `parcel_document`  — else FAILURE 1
2. each touched `parcel.n_docs` **increased**            — else the pool's band filter and
   `ORDER BY n_docs DESC` still rank the parcel on stale counts
3. each touched parcel's `_INDEX.md` is absent or now shows `not acquired` — else FAILURE 2
4. `coverage.py` **ACCOUNTED + NOT YET HELD** rises by exactly the number of new documents

⚠ Test 4 is the one that catches a delta which wrote nothing at all. A job that finds zero
new rows and a job that is broken both print "nothing to do".

---

## 9 · ⚠ THE PASS-OVER IS A LOCKING PROBLEM, NOT A SCHEDULING ONE

**Measured 2026-08-18, while the walk was running.**

```
parcel_spec.db     journal_mode=delete   busy_timeout=5000
ledger.sqlite      journal_mode=delete   busy_timeout=5000
page_counts.db     journal_mode=delete   busy_timeout=5000
```

Nothing in the tree sets WAL. In `delete` mode a writer takes an **exclusive lock on the
whole file**, so the scheduled delta and the continuous walk cannot both touch
`parcel_spec.db`:

- delta writing  -> the walk's reads block, then raise `database is locked` after 5 s
- walk reading   -> the delta cannot acquire its write lock, and fails the same way

⚠ **AND THE WALK ALMOST ALWAYS HAS A HANDLE OPEN.** The spec DB is opened read-WRITE in
three places even though every one of them only reads:

```
overnight.py:55       con = sqlite3.connect(DB)          # parcels()
overnight.py:84       con = sqlite3.connect(DB)          # queue build
acquire_async.py:216  con = sqlite3.connect(spec_db)     # x4 worker processes
```

One driver plus four workers means a collision is the NORMAL case for a scheduled job,
not a rare race. Retrying on a timer does not fix it — it re-enters the same contention.

### The fix

```sql
PRAGMA journal_mode=WAL;    -- on parcel_spec.db, once; it persists in the file
```

WAL permits one writer concurrent with many readers, which is precisely this workload: a
periodic writer against a continuously-reading walk. **The delta then needs no knowledge
of acquisition's schedule at all** — there is no window to hit and no coordination to get
wrong, which is the only version of "smooth pass-over" that survives contact with a job
that runs unattended.

⚠ Applying it needs a brief exclusive lock, so set it at a restart, not mid-walk.
⚠ WAL is safe here because D: is a local USB volume. It is NOT safe over a network share.

Opening the three read-only call sites with `?mode=ro` is worth doing as well — it costs
nothing and removes the walk's ability to take a write lock it never wanted — but WAL is
the change that actually makes the two jobs coexist.

---

## 10 · ⚠ THE THREE SPECIFICATIONS MOVE TOGETHER, OR THEY DO NOT MOVE

**Added 2026-08-18.** The specification lives in THREE places and each can move
independently. A document present in one and absent from another is not a small
inconsistency — it is invisible, and every one of these failures is silent.

| store | what reads it | what a gap here costs |
|---|---|---|
| `D:\acris\01-specification\parcel_spec.db` | `overnight.py` selects parcels; `coverage.py` scores | a document no parcel reaches is NOT YET HELD forever |
| `index_full/*.jsonl.gz` + map jsonl | the audit's independent witness | the cross has nothing to disagree with, so it agrees |
| Supabase `document_map` | the acquisition workers | **acquisition never downloads it — the event is invisible forever** |

### The order is not arbitrary

```
discover        live_delta.py            ids + BBL links + page counts + crfn
   |
land drive      live_land.py --apply     parcel -> parcel_document -> document
   |                                     + invalidate _INDEX.md  + acceptance test
map             amap.py                  page RANGES — the only source of them
   |
push supabase   push_selection.py        complete rows, never bare ids
   |
local           the map jsonl the push read from
```

⚠ **DRIVE BEFORE SUPABASE.** The drive decides what gets walked; Supabase decides
what gets fetched. Landing Supabase first creates rows nothing selects. Landing the
drive first creates work that is queued and then resolves as the push catches up —
recoverable, and visible in the ledger, which the other order is not.

⚠ **NEVER PUSH A BARE ID TO `document_map`.** `no_image` is computed from
`total_pages`, so an id without page ranges asserts *"ACRIS holds no image for this
document"* — a permanent claim about the record, and false. This is why the delta
queues for the mapper instead of writing the table directly, and why `live_land.py`
touches the drive only.

### The invariant, and how to check it

After a delta, all three must account for the same documents **over the delta's CRFN
range** — not in total, because the corpora differ in scope by design (the drive and
`document_map` are real property; `index_full` also carries the 4,544,590 personal
property documents).

```
python selection_cross.py --repair      the three-way audit — weekly, ~20 min
```

⚠ **A PARTIAL RUN MUST SAY SO AND RESUME, NEVER RESTART.** Each stage is additive and
idempotent — `live_land.py` recomputes `n_docs` rather than incrementing precisely so
a second application is harmless. What is NOT harmless is a stage that half-ran and
reported success: the delta's own row count cannot see it, which is what the four-step
acceptance test in §8 exists to catch.

⚠ **THE SEAM IS CHECKABLE AND SHOULD BE CHECKED.** Measured 2026-08-18: the extract
ends at crfn `2026000216616` and the live delta opens at `2026000216617` — no gap and
no overlap. If a future delta does not abut the extract's maximum, something was
missed between them and no row count will show it.

## 2026-08-19 — the routine survives the drive, and the image policy is unified

**Why (measured):** at 04:01 `rc_daily` died at `sqlite3.connect` with `unable to
open database file` while `rc_detail_pull` was writing the same One Touch — and the
identical call had succeeded at 23:34 under the same pull. That error is the Windows
file-OPEN failing (transient sharing violation / device busy), which `timeout=` does
NOT cover: timeout paces lock waits *after* a successful open (`database is locked`
is the contention error — a different animal). The old shape also lost data
silently: the jsonl merge had already recorded pending→present flips, the recheck
queue dropped those docs, and the DB never learned — invisible in every row count.

**The fixes, and what each fails like:**

- `corpus_paths.connect_spec()` — retries the OPEN with backoff (2/10/30/60/120s).
  All spec-DB writers use it. Failure after every attempt DEFERS, never dies.
- `rc_daily` lands the **whole delta jsonl every run** (a few hundred upserts,
  sub-second) instead of only this run's fetches — the DB write is a pure function
  of the jsonl, so a failed landing costs nothing and self-heals next run. The
  upsert is fenced on `image_checked` (ISO, lexicographic) so a daily row can never
  regress a fresher state landed by the detail pull over the same documents.
- Drive absent → **SKIPPED (drive absent), exit 0, reported** in `_routine_4am.tsv`
  as `rc_daily:SKIP:0s` — distinguishable from success and failure forever. The
  ACRIS half still runs: edge + walk queue locally (append-per-record, resumable);
  land/map/push defer behind the same gate.
- `image_policy.py` is the **single image policy, both sources**: land as
  `pending` → probed each daily run while ≤ `TERMINAL_DAYS`=7 old → `imageless`,
  clock = recorded date, falling back to first_seen so no record is immortal.
  Richmond probes via its detail page (rc_daily, unchanged mechanics); ACRIS lands
  `pending` in `live_land` and is probed by `live_imageprobe.py` — page 1 through a
  real session, md5 vs the placeholder `4081a3f2…`, ~1 req/s, stop dead on refusal,
  capped at 2,500/run with the cap LOGGED. It runs as its own routine stage
  (`--only images`) because `acris()` returns early on the normal span-0 day, and
  yesterday's pendings need their probe on quiet days most of all.

**Calibration to watch:** 2026-08-18's 131 Richmond docs were still `pending` at
age 1 on the 08:17 run — the "step at ~24 h" was measured later in the day, so the
attach evidently happens during business hours, not by 4 AM. If age-2 docs are
still pending at a 4 AM run, re-measure the step; TERMINAL_DAYS=7 holds either way.

## THE CONSOLIDATED LANE — design (login, 2026-08-24, drafted during the Phase A/B trip experiment)

**Why.** Two refusals in 12 hours, and the working theory (login's): ACRIS
tolerates ONE access point per IP — one client identity doing one kind of
thing — but within that point the workers can be maximized. The evidence
fits: 112 walker connections ran 8h clean Saturday (workers within a
pattern are fine), while both trips came when the edge-prober and the
doc-walker ran as SEPARATE python processes — two behaviors under one IP.
Richmond, by contrast, is "just an access point" — it has never objected.
Consolidation also IS the endgame architecture (sync absorbs acq when
backfill closes); the trip theory just pulls it forward.

**Shape: one process per source = one access point.**

    acris_lane.py     ONE process owning ALL acris traffic
      ├─ rd worker pool (N threads, one UA, shared discipline)
      ├─ pdf worker pool (separate server pool, same process/identity)
      └─ the ROTATION (login's spec): workers drain the backfill queue
         continuously; every ~10s ONE request slot is SUBBED IN as the
         edge probe (edge+1 is just another doc fetch — the probe stops
         being a distinguishable second behavior). Control checks ride
         the same slot cadence.

**The queue: new filings jump to the FRONT (settled).** Freshness is the
product; a filing queued behind 5.8M backfill rows is days stale. On an
edge hit the new ids go to the head and walk detect → rd → key(trigger)
→ pdf serialized per doc (the `_pdf_hot` pattern generalized). Backfill
drains from the tail. Front-loading costs milliseconds/minute; per-doc
completeness = keyed at the end of its chain. Same rules for richmond
and for the pdf endpoint: hot first, backlog after.

**Worker count** within the lane: start at the proven shape (rd 28, pdf
14–28); Phase B (rd-alone, sync paused) settles whether width was ever
the problem — login's theory predicts it wasn't. Ladder only on
full-fleet readings.

**Refusal discipline baked in:** every fetch path catches BOTH
fetch_pages.AccessDenied and live_delta.Refused (the 09:00 lesson: a
detector firing into the wrong except clause does not exist) → all
workers stop; the edge probe alone continues on exponential backoff as
the resume detector, inside the same process.

**Reporting:** the lane feeds the same board rows (sync + acq per
source) — ledger write on every landing (goalposts move with inflow),
landed from the todo partial indexes, rates from the lane's own db-write
counters. Nothing about the board changes.

**Cutover:** build as `acris_lane.py` alongside the current fleet; prove
it in a dedicated window (it must hold the edge AND drain backfill
without a notice); then retire rd_walk×4 + image_walk×3 + the separate
acris_live, and mirror the pattern for richmond (rc_lane absorbing
rc_live + rc trio) for symmetry rather than necessity. fleet.py lanes
collapse to one row per source.

**REFINEMENT (login, same day): the front-vs-queue question DISSOLVES for
acris rd.** The edge probe RETURNS the rd in the same request — detection
and fetch are one act — so a new filing never enters the queue at all: by
the time the lane knows it exists, the rd is in hand and landing it is a
local write (trigger keys it in the same transaction). "It slots into the
backfilling workflow at the moment of sync — one workflow, not two
overlapping codes." Queueing only exists where a SECOND request is needed:
the doc's PDF (hot-first, the _pdf_hot pattern) and richmond's detail
fetch after its listing-page detection (front of queue, trivial volume).
Phase A evidence (2026-08-24 morning): sync-only ran clean while landing
+34 filings solo — consistent with one-access-point tolerance.

**BURST SEMANTICS (login's question: 2-3-4+ filings in one 10s window).**
The edge slot is a TIME RESERVATION, not a queue position — every ~10s the
next request belongs to the probe regardless of backfill pressure. On a
hit the slot enters WALK MODE: probe edge+1, +2, +3... (each hit lands
that doc's rd in the same request, trigger keys it), continuing until
consecutive blanks + a passing control re-prove level; then it releases
back to cadence. k filings cost k requests + blank-proofs (proven live:
"landed 9 · rd filled 3/3 in the SAME request"). Backfill workers keep
draining in their own slots throughout; in a freak burst the walk expands
to consume slots and backfill throttles — the correct inversion, freshness
first. Even a 1,000-doc recording dump ≈ 20s of full-lane attention. The
periodic DEEP walk (~300s, several past the edge) remains the net against
sparse crfn sequences. Levelness is proven (blanks + control), never
assumed.
