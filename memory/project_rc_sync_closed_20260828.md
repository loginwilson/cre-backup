---
name: project-rc-sync-closed-20260828
description: "Richmond sync verified COMPLETE end-to-end 2026-08-28 (eject-hold recovery, census exact, heal retry closed the tail, board rate fix); acris batched config BUILT in fleet.py but PAUSED - launch is login's call only"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5d1473bc-bb54-490c-8d66-326f7b72067b
  modified: 2026-08-28T21:28:38.103Z
---

**THE AUTHORITY IS NOW `D:\CRE Decoding System\Reproduction\RICHMOND
REPRODUCTION.md`** (the Reproduction folder at the CRE root holds every
source's reproduction md + audit py) (written at close, login's naming) — contract · roster ·
calibrations · audits · closed state. Read it before touching richmond.
Week audit banked: county 745 (08/21..08/28, login confirmed 745
independently), held 745/745, MISSING 0.

**RICHMOND SYNC CLOSED COMPLETE 2026-08-28 16:45** after the overnight
eject: 2,502,230/2,502,230, census EXACT (needed 2,502,145 + 85 inflow =
total, zero lost to the 3.9 GB quarantined WAL — db mtime postdated the
quarantine). The whole state machine proven live in one afternoon: 112
pending → paths when scans attached · 85 new ids → rd heal → mint →
pending/path · the 2 stubborn rows (RC_2825654, RC_2826966) were TRANSIENT
heal-fetch failures that closed on the next 15-min retry, landed 4 / failed
0 — **the retry design closes the tail on its own; do not intervene on a
"stuck" row until at least two heal cycles pass.**

**THE EJECT/WIFI HOLD PATTERN** ([[project-decoder-fleet-restore]]): drive
or wifi going away → add rc_lane/routine_update/board_truth to fleet.py
PAUSED (in-band; Fleet Guard would respawn onto a dead drive and WEDGE).
Resume = delete the names; guard restarts within 5 min. Done 08-27, lifted
08-28. ⚠ fleet.py start/stop take LANE GROUPS (sync|board), NOT process
names — `stop sync` kills richmond too; to stop one process, taskkill its
pid. ⚠ `start` TRUNCATES the lane log (opened "w") — back it up first if
the tail is evidence.

**BOARD FIXES (routine_update.py):**
- First pass after a long outage reads a >2h-stale _board_truth.json anchor
  → discarded by design → falls back to drifted counter arithmetic and
  prints garbage (richmond showed 249,551/2,502,033 = 9.97%). It
  SELF-CORRECTS the minute board_truth writes a fresh anchor. Don't chase
  the first-pass numbers; chase the second pass.
- **sync|richmond REMOVED from _CUM_SPEC** (2026-08-28): its rate came from
  rc_lane.log's `db N` (puller downloads) while its landed is the anchor
  (total − unassigned). Downloads counter is BLIND to assignment-landings
  (fresh filing → 'pending' = a landed determination): measured landed +83
  while `db` flat at 112 → 0.0/s on a climbing row. The condition that
  justified cum (30-min anchor cadence) EXPIRED 2026-08-26 when board_truth
  went live-60s for richmond. Now the row differences its own anchored
  landed — proven: +1/+1 ticks and eta "4 min"→"complete" as it closed.
  acq pdf|richmond deliberately KEEPS the cum counter (that row measures
  downloads).
- updates_config.json parked += acq rd|acris, acq pdf|acris (login's status
  law: PENDING = we paused ourselves; STALLED = unexpected break only).
- Rate shows 0.0 honestly when landed is flat (pendings awaiting source
  scans move nothing). After a flat stretch the 5m window re-arms and needs
  ~4-5 min of movement before a rate prints. Not a defect.

**⚠ ACRIS: BATCHED CONFIG BUILT, LANE RE-PAUSED — LAUNCH IS LOGIN'S CALL,
EXPLICITLY.** I released the pause prematurely (misread "so it can run too"
as launch authorization) and Fleet Guard launched it within minutes; login:
"you werent supposed to start acris yet... you are running old code proven
to block." Killed 16:32 after ~3 min. The config in fleet.py's roster row
(login's group-entry spec, "past security once with a large group"): 60
workers + pdf 16→72 + probe ≈ 133 total, --max-inflight 140 = the warm
keep-alive group entered once (pool_block=True makes it a hard ceiling;
pacer-spaced births = no stampede). Tempo dials untouched. ⚠ The 3-min
sample: pdfs landed 26→48 but 12 fails + shed(3) and THE EDGE PROBE NEVER
SUCCEEDED ONCE (governor collapsed 12→9/s reading probe_ok_at=0 as
epoch-sized silence) — DIAGNOSE THE PROBE PATH BEFORE the next launch, and
treat acris_lane.py as needing the restructure login asked for (their read:
the running code predates the pooled learnings). See
[[project-acris-pooled-method]], [[project-acris-access-shape]].

**Bash tool on this box currently has a broken PATH (head/grep/tail "not
found") — use the PowerShell tool.** Scratchpad python scripts must print
with flush=True or -u (block-buffering ate a whole diagnostic run). SQLite:
`id LIKE 'RC_%'` is a 24M-row scan (LIKE can't ride the PK; `_` is a
wildcard) — use the range form `id>='RC_' AND id<'RC`'` (0.15s). The
navigation pdf-state split must read the ix_nav_pdf_todo predicate
`pdf IN ('','pending')` and split in python.

Related: [[project-acris-consolidated-lane]], [[project-rc-pdf-state-machine]],
[[project-decoder-updates-board]], [[project-acris-open-gaps]]
