---
name: project-decoder-night-state-20260824
description: "State at 2026-08-24 shutdown — both lanes consolidated and verified, acris wire-limited at ~85/s, what to check first next session"
metadata: 
  node_type: memory
  type: project
  originSessionId: d8ac9502-9d7e-49e0-8048-b07c41ae0f18
  modified: 2026-08-24T23:10:08.819Z
---

**WHERE THINGS STOOD WHEN login WENT HOME, 2026-08-24 ~19:10.**

## THE TWO LANES ARE NOW THE WHOLE PRESENCE

`acris_lane.py` and `rc_lane.py` — one process per source, nothing else touches
either server. `python fleet.py status|start|stop sync` is the control.
⚠ Starting any retired script alongside them puts a SECOND access point on the
source, which is the tripping condition the consolidation exists to remove.
Retired to `_archive/richmond_preconsolidation/`: rc_live, rc_feed,
rc_pdf_pull, rc_pdf_land, rc_heal.

## MEASURED AT SHUTDOWN

    acris     tempo 85.4/s commanded, ~76 delivered (89%), ~6.5 docs/s,
              11.3 reqs/doc, 1 fail in 8 min, board 8.26%, ETA ~41 days
    richmond  27,098 pdfs, 14.3/s, err 0, board 48.95%, ETA ~0.35 days
              rd 100% · keys 100% · rd-heal worklist EMPTY ("0 need work")

## ⚠ ACRIS IS WIRE-LIMITED, NOT ACRIS-LIMITED — DO NOT CHASE THIS AS A BUG

The governor parks at 85.4/s printing *"delivered only 76.2/s (89%): the wire
is the limit now, not the tempo. Climbing further would only inflate the
banked peak."* That is CORRECT BEHAVIOUR and the most valuable thing built
today — it refuses to bank a peak the link never carried.

Little's Law is the whole story: delivered = concurrency / RTT. At ~388 ms RTT
`--max-inflight 24` capped delivery near 62/s no matter what the metronome
commanded; raising it to 40 lifted delivery to ~76. To go further the lever is
**RTT or reqs/doc, not tempo**. 8 docs/s needs ~90 delivered; 12 needs ~134.
⚠ **reqs/doc (11.3) is the cheapest unexplored lever** — 6.18 pages/doc is the
theoretical floor, so ~45% of requests are overhead worth accounting for.

## WHAT WAS FIXED TODAY (all committed)

See [[project-acris-ua-and-deadlock]] for the two big ones: the UA 503 wall and
the CLOSE_WAIT pool deadlock. Also:
- richmond rd/keying gap closed — rd 100%, rd-without-key 0 corpus-wide
- board is TWO rows, one synchronization row per source; richmond's row now
  means the WHOLE lane (was reporting 100% COMPLETE while pdf sat at 48%)
- `sync_verify.py` — proves all 7 components on both sources, plus component 8
  guarding the 100% claim. Run it FIRST next session.
- ✅ version control exists (see [[project-acris-open-gaps]] item 3)

## ⚠ FIRST THINGS TO CHECK NEXT SESSION

1. `python fleet.py status` — did anything survive / need restarting.
2. `python sync_verify.py` — all 7 components, both sources.
3. `python lane_reconcile.py` — residue was **800 resolved / 1 diagnosed /
   0 OUTSTANDING**. Outstanding must stay 0.
4. `lane_tempo.json` — must hold the PEAK and `clean: true`. ⚠ If the lanes
   were force-killed the flag may read dirty, which cold-starts at 12/s and
   throws away an hour of climb. Reseed `best` from the log's last clean
   `TEMPO x -> y` ONLY if that run had zero sheds. ⚠ `at` must be a real
   `time.time()` — writing `at: 0` reads as ancient (WARM_MAX_AGE 6 h) and
   silently cold-starts.

## STILL OPEN

- **The pdf three-state migration** (`path | pending | n/a`) is NOT done and
  must land as ONE change — column + board predicate `pdf IN ('','pending')` +
  `ix_nav_pdf_todo` rebuild. Writing the column alone makes those rows leave
  the todo set and the board counts them LANDED. `sync_verify.py` component 8
  guards this.
- `2003030501723001` needs a POLICY (self-contradicting source doc), not a retry.
- Imageless sweep still parked at cursor `2003071401640001`.
- Pass 2 unbuilt — spec in [[project-acris-open-gaps]].
