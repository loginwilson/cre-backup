---
name: project-decoder-updates-board
description: THE standing way login watches routines perform — D:\CRE Decoding System\Updates\ routine_update.py; one row per phase×source; five metrics + computed STATUS + time-to-time window; cadence per phase adjustable at request
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T00:19:06.637Z
---

**⚠ BOARD REDESIGNED 2026-08-23 (login's final spec) — NINE ROWS, THREE
TIMESCALES, FOUR STATUSES.** Rows: sync ×2 · acq rd ×2 · acq pdf ×2 · keying
pass 1 (ONE summed "all" row = Σ of both acq-rd rows, since keying ≡ rd by the
trigger) · pass 2 "all" · pass 3 "all". Columns per row: NOW kit (rate_now ·
increase_now · pct_now · eta_now, 60s) + WINDOW kit (rate · increase ·
pct_increase · eta, 5 min — **eta is the 5-minute basis**) + TOTAL (landed ·
needed · pct_of_total). All pct denominators = NEEDED (fixed ruler). Statuses:
COMPLETE · ACTIVE · **PENDING (deliberate: parked lanes show eta="paused" with
rates zeroed; gated passes show "at rd/pdf 100%") · STALLED (unexpected break —
incl. wedged-but-alive lanes via heartbeat-log mtime >3 min)**. as_of carries
"now=60s · window=5m". ⚠ TRAPS from the rebuild: (1) PowerShell ConvertTo-Json
writes a **UTF-8 BOM** that silently blanked the config (cfg() now utf-8-sig +
loud fallback); (2) schema changes must DROP update_board (N_COLS check) or
INSERTs die while the table survives; (3) walkers launched without stdout
redirects are invisible to the board — logs must land in NAV_WORK as
rd_walk_a[1-4].log / image_walk_i[1-3].log; (4) rd_walk feeders have NO cursor:
every restart re-wades from --lo through rd-complete rows (~4 min quiet drive,
HOURS under pdf load — pause pdf lanes to let rd feeders reach frontier).
FUTURE SOURCE PRINCIPLE (login): built sync-first from day one, a new source
never needs acq/backfill lanes at all — "just run sync up to the decode";
the acq rows exist only because this corpus predates the live lanes.

**⚠ RATE AND INCREASE MUST COME FROM THE SAME SUBTRACTION (2026-08-23
evening).** Counter lanes (_CUM_SPEC) difference the lanes' own cumulative
log counters per-file-stateful (missed parse carries; a drop = that file's
restart); a leftover line then OVERWROTE d_now with the anchored-landed
diff → "5.42/s with +0" on the board. Now gated `if cum is None`. Richmond
pdf's counter+heartbeat = rc_pdf_pull's OWN stdout log (`db N` field, the
rows actually written) at the decoder dir — watching rc_pdf_land.log kept a
6-hour wedge invisible. rc_feed/rc_pdf_pull print to STDOUT: relaunches
must redirect to the canonical rc_feed.log/rc_pull.log names or the board
goes blind. **WARM-UP BASELINES (login): rd 100/s · acris pdf 10/s ·
richmond pdf 10/s minimum, preference 100+/12/12** — the board's recovery
is judged against these, and richmond pdf has exceeded 12/s post-restart.

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
- ⚠ **THE SYNC LEDGER HOLDS TWO ROW KINDS THAT LOOK IDENTICAL.**
  `routine_synchronization` writes a TOTAL row (`system_total` = full
  count, delta 0); `sync_fast`/`rc_sync_fast` write a DELTA row
  (`system_total` 0, delta = ids just landed). Nothing in the schema
  distinguishes them. Reading "the latest row for this source" took
  `system_total + delta` from a delta row → acris total **5** →
  `landed = -20,721,031` **published to the board**. Always filter
  `system_total > 0` when you want a total.
- ⚠ **SANITY-GATE ANY PUBLISHED FIGURE**: `0 <= landed <= total`. The
  anchor had no gate, so an impossible number reached the board
  unchallenged. Refuse to publish and say why — never clamp (clamping
  hides the bug and still reports a false level). I got lucky the bad
  denominator was 5; at 21,000,000 it would have shown a plausible 4.3%
  and nothing would have caught it.
- ⚠ **NEVER DIFFERENCE AN ANCHORED COUNTER FOR A RATE — unless the window
  IS the anchor interval.** Anchoring `landed` to a 30-min re-measure made
  the level right and the derivative nonsense (1.37/s shown vs 11/s real,
  `rate_now` 0.0 = reads as stalled). Aliasing comes from a window SHORTER
  than the update it observes. `board_truth` now publishes its own rate
  differenced between consecutive anchors — same arithmetic, opposite
  verdict, decided by the span. ⚠ Lane `total_docs/total_minutes` is a
  LIFETIME average and drifts high; measured from the column, acris pdf
  was 9.56/s vs the lane's 11.06/s.
- ⚠ Positional `INSERT INTO update_board VALUES (...)` broke
  `routine_navigation` and `routine_organization` — 10 values into 12
  columns, rejected outright, so **neither phase ever wrote its own row**
  while routine_update's estimate filled it in and looked fine. Name the
  columns; the table has already grown three.

Related: [[project-decoder-seven-phases]], [[feedback-bkrea-scale-failure]]
