---
name: project-acris-blip-cascade
description: "2026-08-25 — how one wifi drop cascaded into a night at 1/7 throughput, the four rules that let it, and relocate.py for moving locations"
metadata:
  node_type: memory
  type: project
  originSessionId: d8ac9502-9d7e-49e0-8048-b07c41ae0f18
  modified: 2026-08-25T11:01:42.628Z
---

**ONE NETWORK DROP COST THE WHOLE NIGHT, THROUGH FOUR RULES THAT EACH LOOKED
REASONABLE.** Measured 2026-08-25 06:37–06:47:

    06:37:32  mass failure (26/min) -> width SLAMMED 56 -> 8
              governor correctly said "local transport event, not acris"
    06:38:33  the RESIDUAL 3 failures from the SAME drop fell through to the
              ordinary shed branch, which never asks the probe -> blamed on
              acris -> TEMPO 28 -> 21 and the banked peak TRIMMED
    06:44     output frozen at 2,925, ONE socket open, only the probe alive
    06:47     keepalive restarted it -> COLD at 12/s, climbing 12/20/28

## THE FOUR FIXES (commit 19d3025)

**1 · THE SHED BRANCH NOW ASKS THE PROBE.** The oracle (`probe_ok_at` within
90 s ⇒ acris is still serving us ⇒ this is local) lived **only** on the
`shed >= 10` branch. ⚠ The tail of every blip is always `>= 3` and always
arrives a minute late, so on a flaky link the lane **ratchets down
permanently** — the mass branch protects the tempo and the shed branch takes
it away sixty seconds later.

**2 · WIDTH RESTORES AFTER A BLIP.** The recovery branch was literally
`if False and ...` — disabled correctly (under the piano gate width is SHARE,
not pressure, so hunting a width ceiling is meaningless) **but the blip
handlers still slam width to 8.** No restore path = 1/7 of the workers for
the rest of the night. ⚠ Restoring toward `_target` would have been a second
bug: in row phase `_target` is 12, not the configured 56 — hence `FULL_WIDTH`.

**3 · A DIRTY TEMPO ≠ 12/s.** The flag means *"do not resume AT the peak"*;
it was never evidence the floor is the only safe rate. Now
`--dirty-fraction 0.4` of the remembered peak.

**4 · A COLD START NO LONGER ERASES THE PEAK.** `_best` began at 0.0, so the
first `save_tempo` wrote `best = max(0, 12) = 12`. **One dirty restart
destroyed a banked 107.3/s** and every later warm resume could only return to
28. Carry the mark across even when declining to start on it.

VERIFIED 10 min after restart: WARM RESUME at 96.6/s (not 12), delivered
74.9 → 84.8/s, width held 56, 7.4–7.8 synced docs/s, 2 fails, zero collapses.

## ⚠ THE DIAGNOSTIC THAT NAMED IT

`netstat` showed **0 CLOSE_WAIT and 1 ESTABLISHED** on the acris pid. That
ruled out the [[project-acris-ua-and-deadlock]] pool deadlock immediately —
the workers were not blocked on dead sockets, they were **starved**. Check
the socket table before assuming the known bug recurred.

## relocate.py — MOVING LOCATIONS

`python relocate.py down | up | check`. Two orderings are load-bearing:

- **keepalive dies FIRST on the way down** (a live supervisor restarts every
  lane within 60 s and the eject fails on a drive it just reopened) and
  **starts LAST on the way up**.
- **A planned shutdown is not a refusal.** `down` re-stamps the tempo clean —
  but only after confirming no refusal is in the acris log. If one is, the
  flag is left alone and said loudly. Conditional, noisy, never silent.

## login's VOCABULARY (recorded 2026-08-25)

- **THE PIANO METHOD is acris, and it names the METRONOME, not the count.**
  Departures are sequenced on a self-adjusting pacer so requests never
  overlap. `--max-inflight 1` is single notes, 64 is chords, **both are
  piano**. richmond is **THE DRUM** — no pacer, latency the only governor.
- **"pdfs" means THE WHOLE SYNC PIPELINE.** The counter is the last gate of
  rd → key → image → READY; a row advances it only when the entire chain
  closed. Reading it as "files downloaded" invites tuning the image fetch in
  isolation.
- **90+ req/s is the target and a LONG warm-up is expected** — the ladder
  needs uninterrupted clean minutes to step at all.

⚠ richmond was raised 16 → 26 workers as a PROBE and the result is
**INCONCLUSIVE** — it was raised in the same window acris recovered, so the
two cannot be told apart (CLAUDE.md rule 2, one variable at a time). It
averages 4.87 MB/doc and was already pulling ~296 Mb/s, so bandwidth is the
likelier governor. See [[project-acris-measured-ceiling]],
[[project-decoder-fleet-restore]].
