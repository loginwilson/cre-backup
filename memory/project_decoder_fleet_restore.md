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

## ⚠⚠ A PULLED USB LEAVES PROCESSES ALIVE AND WRITING NOWHERE (2026-08-26 21:22)

login unplugged the One Touch mid-run. What it looked like afterwards:

    D:              back, Healthy, same free space, DB + WAL all present
    rd_walk         STILL ALIVE, same pid, err log 0 bytes, no traceback
    rd TODO count   4,879,825 -> 4,879,825 over 60s   <-- ZERO ROWS LANDING

**Windows invalidates open handles when a volume is removed.** Replugging
mounts a NEW volume instance; handles opened before the pull keep pointing at
nothing. SQLite raised nothing the lane logged, so the lane looked perfectly
healthy while writing into the void.

⚠ **THE cwd DECIDES WHO DIES AND WHO WEDGES.** `routine_update` (cwd on D:)
was killed outright by the unplug. `rd_walk` (cwd on C:) survived the pull and
kept running - which is WORSE, because a dead process is obvious and a wedged
one is not. Do not read "the lane is still up" as "the lane is fine".

### THE ONLY CHECK THAT WORKS

A log-watching monitor CANNOT see this - the failure writes nothing at all, and
silence is identical to health. **Ask the DATABASE whether rows are landing:**

    SELECT COUNT(*) FROM navigation WHERE recorded_details=''
      AND id NOT LIKE 'RC_%'        -- twice, 60-90s apart

Unchanged = wedged, no matter how alive the process looks. Watchdog written at
scratchpad/rd_watchdog.py: polls this every 5 min and prints ONLY on trouble
(wedge, crawl, refusal, missing process, drive gone).

### RECOVERY - NOTHING IS LOST

Kill and relaunch. An interrupted document is not a damaged document: its row
simply stays `recorded_details=''` and the feeder picks it up again. In-memory
`pend` (<=200 rows) is discarded and re-fetched. After restart: 5,323 rows in
90s = 59.1 docs/s, err 0. **Do NOT run integrity_check** - 22 GB takes ~an hour
and blocks everything; successful commits are stronger evidence than any
read-only scan, and the lane commits every 200 rows.

⚠ The Fleet Guard restarted `board_truth` on its own within 5 min but does NOT
notice a wedged process - it only replaces MISSING ones. Aliveness is not the
same predicate as usefulness. See [[project-decoder-updates-board]].

### ⚠ A DETECTOR WITH NO MEMORY REPORTS A STATE, NOT AN EVENT (2026-08-26)

The wedge watchdog above would have spammed every 5 minutes all night the
moment it fired once. Two defects, both from writing it against the state that
existed at the time:

  1 it grepped the log TAIL for "refus" - but refusal text STAYS in the log,
    so ONE event re-reports forever. Fix: remember each log's byte offset and
    read only NEW bytes. An event is a transition; a grep sees only a state.
  2 it called zero-rows-landing "WEDGED" - correct at 21:30, WRONG after 21:55
    when acris was stopped ON PURPOSE. **An alarm that cannot distinguish
    intended silence from failure is an alarm that gets ignored.**

Replacement at scratchpad/night_watch.py watches only what can still break
while acris is deliberately down: drive loss, rc_lane death, and - inverted -
an ACRIS lane RESTARTING when nothing should have restarted it.
⚠ It does NOT probe acris to see if the block lifted. A "has it resumed?"
request is still a request, and the notice said stop.

### ⚠ TaskStop ON A MONITOR DOES NOT REAP ITS `tail` - AND IT BLOCKS THE EJECT

2026-08-27 07:36, eject refused with every lane already dead. KERNEL-PNP
**Event 225 named the blocker outright**:

    tail.exe pid 21016 stopped the removal ... command line:
    tail -F "D:/.../rd_walk_a1.log"      <- spawned by a Monitor at 20:04,
                                            ELEVEN HOURS EARLIER

Stopping a Monitor kills the supervising process but leaves the `tail`/`grep`
children holding their files - and a held file on D: holds the VOLUME. Three
orphaned tails and three greps had accumulated across the night.

**THE FAST PATH - do not guess at handles:**

    Get-WinEvent -FilterHashtable @{LogName='System'; Id=225;
      StartTime=(Get-Date).AddMinutes(-30)}

It names process, pid AND command line. Then kill tail/grep by name (⚠ NOT
bash - the agent's own shell is one), and close any Explorer window on D:
(`Shell.Application`.Windows() -> .Quit()), which also blocks.

⚠ lanes_pause.py reports "processes RUNNING FROM D:" - which is a DIFFERENT
predicate and was empty the whole time. A process running from C: can still
hold a file on D:. Add the Event-225 check to the pause routine.
