---
name: project-decoder-updates-board
description: THE standing way login watches routines perform — D:\CRE Decoding System\Updates\ routine_update.py; one row per phase×source; five metrics + computed STATUS + time-to-time window; cadence per phase adjustable at request
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-21T18:27:00.853Z
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
- No full 24M scans on a tick (stops WAL checkpointing): absolutes = daily
  sync step-1 count + lane log counters folded across restarts.

Related: [[project-decoder-seven-phases]], [[feedback-bkrea-scale-failure]]
