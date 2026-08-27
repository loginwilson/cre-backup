---
name: project-rc-pdf-state-machine
description: The four pdf states, why 'absent' not NULL, and the trigger+nightly pair that took richmond to 100% ASSIGNED on 2026-08-26
metadata:
  type: project
---

**RICHMOND CLOSED 100% ON 2026-08-26** — 2,501,863 rows, board status COMPLETE.
"100%" means **ASSIGNED**, not fetched (login): every row carries a state.

    <path>      fetched                      ASSIGNED · done
    'absent'    determined, no image         ASSIGNED · done
    'pending'   no image yet, still in lag   ASSIGNED · STILL QUEUED
    ''          never checked                NOT ASSIGNED  <- the only todo

⚠ **NEVER NULL FOR "no pdf".** login proposed it; board_truth.py forbids it in
its own header: `landed = total - todo`, and a NULL row is neither, so it is
absorbed into landed and reports completion that did not happen. NULL is
reserved for "never minted" and is a DEFECT SIGNAL the nullprobe watches.

**THE TWO HALVES, AND THE ONE THAT WAS MISSING.** `rc_rd_refresh.py` re-walks
docs recorded in the last 7 days and replaces their rd, so image_state flips to
'present' when the scan attaches. It NEVER touched `pdf` — so a doc that passed
day 7 with no image stopped being refreshed and sat at `''` forever, invisible
to the miner (which selects image_state='present'). That is how **6,699 rows**
accumulated and why richmond stalled at 99.60%.

Now it is a pair, and both are scheduled:
- **trigger `pdf_state_on_rd`** — on rd landing, no image ⇒ `pdf='pending'`, in
  the same transaction (same shape as `key_on_rd`). Assignment cannot be
  forgotten or race a batch job. Deliberately does NOT touch image_state
  'present' (pdf stays '' so the miner still sees work) or a MISSING
  image_state ("we never asked" ≠ "there is none").
- **`rc_pdf_state.py --apply`** — matures pending → 'absent' past the 7-day lag.
  In `C:\dev\cre_ledger_4am.cmd` with the nightly ledger refresh.
- **`rc_rd_backfill_old.py`** — one-off; 68 pre-1950 rows whose rd predated the
  image_state field. No fleet process could ever reach them.

⚠ **QUERY THE INDEXED PREDICATE, SPLIT IN PYTHON.** `pdf=''` CANNOT use
ix_nav_pdf_todo (`WHERE pdf IN ('','pending')`) — SQLite will not prove `=''`
implies the IN list, and it degrades to a 2.5M-row PK scan (69 s measured).
board_truth reads the indexed set (a few hundred rows) and counts `''` in
python: O(queued), not O(table). See [[project-rc-lane-cold-start]].

⚠ Also fixed 2026-08-26: `routine_synchronization.py` `land()` was a positional
6-value INSERT against an 8-column table — it had been killing the nightly run
since 08-24, freezing every board denominator. Name columns explicitly.

---

## ⚠ A 302 IS NOT AN IMAGE — the mint Location must be classified (2026-08-26)

`miner()` read every redirect as a hit: `outcome = "present" if loc else "noimage"`.
MEASURED, two ids minted back to back on ONE session (so the session cannot be
the difference):

    RC_2825613  image up   -> 302  https://iapps.courts.state.ny.us/vscms_public/viewer?token=v2....
    RC_2820269  no image   -> 302  /Search/SearchError

**The clerk answers a no-image document with a redirect to its own error page.**
The old test called that "present", handed `/Search/SearchError` to the puller,
and requests died client-side with `MissingSchema` — *no request ever left the
machine*, so the row could not resolve and never reached the state machine at
all. The tell was `err` climbing by EXACTLY the sweep size each pass.

Test is **"an absolute URL we can fetch"**, not "not the error page" — any
relative Location is unfetchable and must never be called present.

⚠ It stayed dormant for as long as it did because `next_ids()` gates on
`image_state='present'`, which no such row can match. Feeding pending rows to a
miner is what exposed it — **a gate that hides a bug is not a fix.**

⚠ **'absent' NOW NEEDS TWO SOURCES TO AGREE.** The url saying "no image" is one
reading and a bad session can produce it too; the detail page saying so in its
own words (`image_state`) is the second. `_no_image()` refuses the verdict when
the rd says `present` and the url disagrees — the odd one out is far more likely
to be us. Costs one re-ask; the alternative is a fabricated determination that
nothing ever revisits.

## PENDING RECHECK — dynamic, and cheaper than the nightly it replaces

`pending_recheck()` in rc_lane (`--pending-every`, default 300 s) pushes the
whole pending set onto `hot_ids`. One mint request per row answers "has the scan
arrived?" — no detail page, no listing page, **no grant rule** (the mint endpoint
takes a bare id). 203 rows ≈ 12 s at 16 docs/s.

It replaces two things that were half-doing the job:
- `rd_heal` did re-ask pending ids, but to FIND them it opens a 30-day Window and
  pages it at 17 rows/page — ~160 listing requests every 15 min to rediscover ids
  we already know BY NAME — then throttles each by `--absent-recheck` (6 h).
- `rc_pdf_state.py` at 04:00 was never a checker; it is the calendar maturation
  (pending→absent at day 7), pure SQL. It stays, as the safety net.

⚠ **A DEDICATED TIMER, NOT A RELAXED `next_ids()`.** Dropping the
`image_state='present'` gate would have 24 miners spinning the same rows at 16/s
forever. THE INTERVAL IS THE THROTTLE.

⚠ Fixed alongside: the hot-list branch was `st == "present" and not got[1]` —
`got[1]` is the pdf column and `'pending'` is TRUTHY, so from the day the fourth
state landed, a row whose scan had just arrived was the one row that could never
jump the queue.

**Verified end to end 2026-08-26** (source listing → PK lookup → file on disk):
08/24 = 105/105 pdfs, 762.8 MB, day fully closed · 08/25 = 100 landed / 57
pending · 08/26 = 74 filed, 0 outstanding, all through rd+key, all pending.
`pending → absent` is NOT observable while nothing in the queue is older than a
day — proven instead by the boundary (day 6 pending / day 7 absent / unparseable
→ pending) and by `rc_pdf_state.py --lag 1` selecting exactly the 57.

## ⚠ RICHMOND INTERNAL IDS ARE SPARSE — 325,051 "gaps" are UNISSUED (2026-08-26)

A continuity audit over the richmond id range reported:

    id range   1 .. 2,827,084      span 2,827,084
    held                           2,502,033
    MISSING FROM THE SEQUENCE        325,051   in 64,289 runs

**That number is meaningless as a completeness signal.** The county does not
allocate internal ids densely. VERIFIED against the source, not inferred:
four recording dates drawn from rows BRACKETING the gap runs (11/4/2019,
11/6/2019, 12/24/2019, 3/29/2013) — the county listed 635 documents across
them and we hold **every one, 0 missing**.

⚠ **A COLD DETAIL FETCH CANNOT TEST THIS.** The grant rule means an id whose
listing page the session never fetched returns HTTP 200 and a ~4,212-byte
shell — *identical* to a non-existent id. Only the LISTING PAGE for a date can
say what exists. Any future "are we missing documents?" question must be asked
date-by-date against the listing, never id-by-id against the detail route.

⚠ Gap SHAPE was the early tell and it was right: ids 1..2,234,746 are dense
(one lone gap, RC_60881) and every later gap clusters above 2,234,747 in
alternating singles and short runs — allocation behavior, not fetch failure,
which would be random or contiguous. Shape suggested it; the listing proved it.

**Richmond audited COMPLETE 2026-08-26**: 2,502,033 rows · 0 missing rd · 0 with
rd but unkeyed · 0 `pdf IS NULL` · 0 unassigned · 183 pending awaiting county
scans · 0 documents the county lists that we lack.
