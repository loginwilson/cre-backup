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
