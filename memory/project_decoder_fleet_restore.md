---
name: project-decoder-fleet-restore
description: "THE relaunch recipe after the One Touch (D:) is re-plugged — exact commands/order for the whole fleet, 2026-08-24 morning state, and the ix_nav_rd_todo index that killed the wade"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T14:15:33.038Z
---

**SUPERSEDED BY `fleet.py` (in the decoder dir):
`python fleet.py status|start <lane>|stop <lane>` — THE roster is fleet.py's
LANES dict; the listing below is history.** ⚠ CUTOVER 2026-08-24 ~10:12:
lanes are now **sync (acris_lane + rc_live) · rcpdf · board** — the old rd
and apdf lanes were REMOVED from the roster (acris_lane.py absorbed
acris_live + rd_walk×4 + image_walk×3; see
[[project-acris-consolidated-lane]]). Restore = `python fleet.py start all`,
verify with `fleet.py status` + the board.

**FLEET PAUSED 2026-08-24 ~06:45 for One Touch (D:) ejection — relaunch in
this order when login says the drive is back** (all Start-Process detached,
-WindowStyle Hidden, stdout/err redirected; cwd = the decoder dir
`C:\Users\smile\Downloads\Source Folder (Real Estate Data)\Decoder Prompt\decoder`,
walker logs into NAV_WORK):

1. `acris_live.py --apply --pdf --every 10` (→ decoder\acris_live.log)
2. `rc_live.py --apply --every 10` (→ rc_live.log)
3. rc trio: `rc_feed.py --miners 24 --ahead 1200` · `rc_pdf_pull.py
   --workers 16 --batch 3` (→ rc_feed.log / rc_pull.log — canonical names,
   the board's counter+heartbeat read rc_pull.log's `db N`) ·
   `rc_pdf_land.py --loop --raw`
4. rd walkers 4×28 → NAV_WORK\rd_walk_a1..a4.log; ranges:
   `"" → 2012061200165002 → 2024062000194001 → FT_2710000762071 → U+FFFF`
5. `routine_update.py --loop` (cwd D:\CRE Decoding System\Updates) and
   `board_truth.py --loop --every 600` (cwd decoder, log → Updates\)
6. acris pdf (image_walk ×3) stays PARKED — config
   `updates_config.json: "parked": ["acquisition pdf|acris"]` (per-lane
   parking added 2026-08-24; phase-level would wrongly park richmond).

**State at pause:** acris rd 15,254,580/21,615,745 = 70.6% (was 76.6/s and
climbing); richmond pdf 759,057/2,501,589 = 30.3% at ~15/s; keying pass 1
lockstep exact; both syncs level (acris edge crfn 2026000237865).

**ix_nav_rd_todo EXISTS (built 2026-08-24, 31 min):** partial index
`ON navigation(id) WHERE recorded_details=''`. Killed the re-wade (feeder
finds frontier instantly; restarts are free) and made rd landed EXACT —
routine_update now computes `landed = total − COUNT(todo)` (0.4 s) instead
of baseline+lane-counter arithmetic (which zeroed to a stale 12.9M baseline
on every relaunch). ⚠ LESSONS: (1) CREATE INDEX holds the db WRITE LOCK for
its whole build — richmond's writer queues behind it (q grows, fetch
continues); pause writers or accept the hold. (2) A builder mid-build shows
ZERO ReadTransferCount and ~10% CPU on Windows — the IO counters are NOT
evidence it is stuck; I killed a working build twice on that misreading.
Trust only its completion line. (3) The write-lock holder was found by
elimination: kill-and-probe with `BEGIN IMMEDIATE`.

**⚠ EJECT BLOCKERS:** orphaned `tail -f`/`grep` watchers from old sessions'
Monitors held D: log handles (27 processes; found via System event log
id 225, which NAMES the blocking process). Kill tail/grep/sleep, then a
final "System pid 4" block is just cache flush — wait 30 s or shut down.

Related: [[project-acris-refusal-20260824]], [[project-decoder-updates-board]]
