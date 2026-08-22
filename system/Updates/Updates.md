# UPDATES — how routines are watched

**The job: answer "what does my update say" at any moment.** One board, one
row per phase × source, computed from the phases' own databases — never
hand-set. This is the user's way of seeing how routines are performing.

**The routine:** `routine_update.py`, run by the scheduled task
'Legal Instruments Update Board' every 5 minutes (`run_update.cmd` wraps it —
schtasks cannot carry a spaced path). Each tick reads the phase dbs, computes
the metrics, rewrites the board, and appends the printed lines to
`update_board.log`.

**The db:** `Updates.db`, one table:

    update_board: phase | source | as_of | rate | increase | pct_increase
                  | landed | needed | pct_of_total | status

**The row grammar** (one printed line per row):

    synchronization | acris | August 21, 2026 4:09 to 4:14 | 0.0/s
    | +0  +0.00% | 2,395 / 2,395 = 100.00% | COMPLETE

- **as_of** — a plain freshness stamp ("as of August 21, 2026 11:05 PM").
  Every row refreshes every 60 s; a stale stamp means the daemon died.
  rate and increase are both measured over the same trailing ~20-minute
  window — one denominator, immune to commit lumps.
- **rate / increase / %incr** — movement inside that window. **The unit is
  DOC/S, always** — every counter the board reads is a document count
  (rd "+N this run" · pdf "N pdfs"+imageless · sync/nav ids). Pages are a
  lane-internal load gauge and never become a board rate; a lane that only
  prints pages gets fixed at the lane, not parsed around.
- **landed / needed / % of total** — progress against the phase's own target
- **status** — COMPLETE (landed ≥ needed) · ACTIVE (a process is pulling or
  the count moved) · STALLED (partial and not moving) · PENDING (nothing yet).
  Only these four; status is COMPUTED, never typed in.

⚠ COMPLETE means "the last measured delta closed", not "level this second" —
the board is only as fresh as the phase's last run. The as_of window says when.

**Config:** `updates_config.json` — `show` whitelists which phases render
(rows outside it are deleted, not greyed); `cadence` per phase, adjustable at
request. Currently showing: synchronization only.

**Scaling rule: every new routine ships with its board row.** As phases build
out (navigations, acquisitions, …) each adds its rows to the same table; the
board accretes rows, the grammar never changes.

---

## ⚠ NEVER RE-DERIVE A RATE THE LANE ALREADY MEASURED (2026-08-22)

**The board must READ each lane's own published rate, not difference its own
`landed` between passes.** This is the single rule that fixed three separate
symptoms the login watched all morning.

**The mechanism — aliasing, not throughput.** A lane emits its PROGRESS line
about every 60 s. The board ticked every 60 s. Sampling a lumpy feed at the
feed's own frequency makes the two drift in and out of phase, so one pass sees
two lumps and the next sees none. The *same healthy fleet* printed:

    now 0.0/s  →  now 175.4/s  →  now 13.3/s  →  now 38.4/s

while four rd shards sat rock-steady at 22.8–22.9 docs/s each. The login read
that as a dying fleet ("it says 0 across the board", "the speed looks off") and
was right to: **the instrument was broken, the work never was.**

| | board said | lanes said | |
|---|---|---|---|
| acris rd | 13.3/s | 22.9+22.8+22.9+22.8 = **91.4/s** | off by ~7× |

**The fix.** Every lane already computes a rate over its own full run —
authoritative, smooth, free. Sum those. `LANE_RATE[(phase, source)]` is
populated from the logs and *wins* over any differenced rate; differencing
survives only where no lane publishes a rate (rc_pdf_land prints landings).

**Three standing rules that fall out of this:**

1. **`MIN_SPAN` = 180 s — never divide by a gap shorter than the source's own
   update interval.** A restart left 11 s of history and published acris rd at
   **295.68 docs/s**, over 2× a ceiling we had MEASURED at ~138. It decayed to
   64.5 across three passes as the window filled — but *a spike that corrects
   itself is still a spike that got published*. Below MIN_SPAN there is no rate
   yet, and saying so beats inventing one.
2. **A quiet log contributes LANDED but never RATE** (`LANE_FRESH` = 10 min).
   A 17-hour-dead `image_walk` log was still being summed into the fleet rate.
   Its work happened and did not un-happen — so it stays in `landed` — but it
   is not evidence about *now*.
3. **pg/s is a load gauge; doc/s is the headline.** The pdf lane prints
   `20.3 pg/s`. Doc/s is derived from its own doc counter over its own elapsed
   minutes, and **imageless docs count in the numerator** — they are resolved,
   they just have no image to fetch. `landed` already sums them, and a rate
   whose numerator disagreed with its own denominator would be wrong twice.

**How it was verified — the only reason to believe any of it.** The fixed board
and an independent hand-computation from the raw lane logs were derived
separately and compared:

| | board | hand-calc | |
|---|---|---|---|
| acris rd | 91.3/s | 91.4/s | ✓ |
| acris pdf | 6.6/s | 6.64/s | ✓ |
| richmond pdf | 1.8/s | ~1.7/s | ✓ |

**Fleet standing vs the locked 100/8/2 target: 91 / 6.3 / 1.7** — 91%, 78%,
85%. Near target, and never "nowhere near" as the broken board implied.

### ⚠ CORRECTION (same day): the fix above OVER-CORRECTED — window ≥ 20 min, lifetime only as fallback

Preferring the lane's lifetime self-reported rate fixed the aliasing and then
hid a regime change in the other direction: after the priority boost the fleet
measurably ran **122.7 / 8.6 doc/s — above the 100/8 target** — while the
board printed "avg 89.9 / 6.5" from 19-hour lifetime averages that dips had
dragged down (login: "shouldnt we be near 100/8" — it was, and the board said
otherwise). The precise rule both incidents agree on:

**A differenced rate is honest iff its window spans many commit lumps.**
60 s samples of 60 s lumps → aliasing (the morning's 0→175 whipsaw). An
11 s cold-start → 295/s fiction. A 20-min window → ~20 lumps, ~5% edge error,
and it tracks the CURRENT regime. A lifetime average is lump-proof but
memorializes history — legitimate only as the cold-start fallback before the
window fills. `avg` = 20-min differenced · `now` = 5-min differenced ·
fallback = lane lifetime, in that order, never reordered.
