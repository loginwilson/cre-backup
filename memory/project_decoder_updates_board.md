---
name: project-decoder-updates-board
description: THE standing way login watches routines perform — D:\CRE Decoding System\Updates\ routine_update.py; one row per phase×source; five metrics + computed STATUS + time-to-time window; cadence per phase adjustable at request
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-23T04:43:25.504Z
---

**The Updates board is login's one way of seeing how routines perform**
(2026-08-21). Every routine built from now on ships with its row here —
never a bespoke dashboard again.

- Lives in `D:\CRE Decoding System\Updates\`: `routine_update.py` (the
  loop), `updates_config.json` (per-phase cadence seconds + parked list —
  adjust at request, re-read every pass), `Updates.db` table `update_board`
  (login watches it in DB Browser read-only) + chat lines via a Monitor.
- Row shape: `phase | source | <measurement window> | rate | +increase |
  %incr | landed/needed | %of total | STATUS`. The window is time-to-time
  ("August 21, 2026 2:25 to 2:30") — an increase is meaningless without the
  span it covers. Rates windowed ~20 min, never single-tick.
- **STATUS is COMPUTED from numbers + live process list, never hand-set**:
  COMPLETE (landed≥needed; a measured zero-delta counts — nothing owed IS
  complete) · ACTIVE (increased this tick) · PENDING (process working,
  nothing landed yet) · STALLED (partial, no process, not parked) ·
  NOT STARTED · PARKED (declared in config). A flat counter and a dead
  process look identical unless both are checked.
- No full 24M scans on a tick (stops WAL checkpointing).
- ⚠ **`landed` COMES FROM THE `pdf` COLUMN NOW, NOT FROM LANE LOGS**
  (2026-08-23). `board_truth.py --loop` anchors it; logs only carry the
  delta since the anchor, and a stale anchor (>2h) is ignored in favour of
  the live estimate. Log arithmetic had richmond at 102,241 vs **156,677
  true — 35% low** — because one branch looked for `rc_pull.log` in
  NAV_WORK while the lane writes it to its own cwd. Counter arithmetic
  drifts one way and reads as healthy; see [[rules-that-dont-fire]].
- ⚠ **COUNT THE TODO SET, READ THE TOTAL.** Measured same-minute:
  `ix_nav_pdf_todo` 23.1M entries in **30s** (hot — walkers query `pdf=''`
  constantly) vs PK autoindex 2.5M in **168s** (cold). 50x from index
  choice alone. A plain `count(*)` picks `ix_nav_key`, the index the keyer
  is writing — that pass ran 28 min unfinished. Totals come from the sync
  ledger (validated against sync's own independent scan, exact match), so
  a pass is **131s**. `landed = total − todo` borrows navigation's
  assertion, so the anchor records `depends_on` rather than hiding it.
- ⚠ Positional `INSERT INTO update_board VALUES (...)` broke
  `routine_navigation` and `routine_organization` — 10 values into 12
  columns, rejected outright, so **neither phase ever wrote its own row**
  while routine_update's estimate filled it in and looked fine. Name the
  columns; the table has already grown three.

Related: [[project-decoder-seven-phases]], [[feedback-bkrea-scale-failure]]
