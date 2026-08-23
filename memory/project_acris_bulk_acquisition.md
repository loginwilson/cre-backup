---
name: project-acris-bulk-acquisition
description: "ACRIS acquisition — measured concurrency ladder (linear to 144 conn), the lane protocol, and the standing traps"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-22T04:14:10.775Z
---

**THE RD CAMPAIGN, remeasured 2026-08-21 on the certified corpus** (4
processes × N workers over disjoint id-range quarters via rd_walk.py
--lo/--hi; quartile boundaries computed from the remaining empty-rd rows):

    4×20 ≈ 99 docs/s · 4×28 ≈ 138 · 4×36 ≈ 139 (NO GAIN)
    ⚠ THE CEILING IS AGGREGATE ~140 docs/s: a single lane at 36 read 44.3
    (borrowing the controls' unused headroom) but the full 4×36 fleet split
    the same total — a passing single-lane test ≠ a gaining rollout; only
    the full-fleet reading settles it. OPERATING POINT: 4×28.
    → whole ACRIS rd backfill ≈ 42 h (vs the old 19-22 day plan)

**The escalation protocol that made it safe:** bump ONE lane, keep three as
live controls, judge on ≥15-min windows; roll out only when the test lane
scales linearly AND controls hold flat (controls sagging = stealing from
ourselves). Refusal stops everything, no retry. Process count stays 4 (16
GB RAM ceiling); scale is workers-per-process.

**⚠ MEASURE FROM THE TABLE, NOT THE PRINTER:** rate = disjoint id-band
slice growth over 2-min windows. A restarted lane's stdout reporter can go
MUTE while the lane lands at full rate (3 of 4 did — 26-28 established
connections each, +34 docs/s measured, zero printed lines). And slices must
be DISJOINT with lane ranges: an overlapping slice double-counted a
neighbor and read 103.7 where truth was 44.3.

**Board wiring:** lanes print PROGRESS lines → a bridge mirrors each lane's
last line to `_working/rd_walk_<taskid>.log` → routine_update glob-sums
logs NEWER THAN the dash_baseline stamp (older logs are inside the
baseline — summing them double-counts). Richmond rd baseline: 2,426,803 of
2,501,589 (the census-recovered 74,786 need the Chrome lane).

**THE LOCKED SEQUENCE (2026-08-22 00:15, experiment-priced — full detail
in the acquisition md's "LOCKED CONFIGURATION" block):** acris rd 4×28
~100/s (priority, ~2.3 days) + acris pdf 2×28 ~8 docs/s + richmond rd
CLOSED (walker = daily follower) + richmond pdf ONE visible browser
(feed 32 miners/ahead 300 → 2 pullers ~2/s → raw lander; converter
PARKED). After rd closes: everything to pdfs — richmond two-browser
(3.1/s, the iapps wall is PER-CLIENT ~2/s: Edge+Chrome adds, second tab
same browser doesn't), converter resumes, acris pdf ladder re-runs on
freed cores. PRICED BY EXPERIMENT: pause test (browsers stopped → acris
55→101/s in minutes; browsers = real machine tax, no warm-back in 14-min
sustained watch); two-browser-now buys richmond ~1 day, costs acris rd
~2 days + acris pdf 8→5/s. ⚠ browser tab must stay VISIBLE. Board: live
daemon (60s rows, 20-min rate window, as_of = freshness stamp), schtask
writer DISABLED (two writers raced → negative rates), bridge v5 skips
task outputs older than the baseline stamp. 4AM sync + 4:20 nav audit
standing.

**⚠ THE HELD-LOCK COLLAPSE (2026-08-21 ~9:30 PM):** the RC pdf lander's
commit-every-50 held the nav db's ONE write lock across ~50 CPU-heavy G4
conversions (30-60 s each stretch) — acris rd collapsed 99 → 16 docs/s and
every lane queued on busy_timeout. Rule: daemons sharing the record db
COMMIT PER ROW, convert/compute OUTSIDE the transaction. A lane that slows
right after a new daemon starts = suspect a held lock before CPU/server.

**WE ONLY MEASURE DOC/S** (user rule, restated 2026-08-21 night): every
report, board row, and ceiling is docs/s — pages are a lane-internal load
gauge only, never a headline number. PDF ceiling in the real unit: ~8
docs/s aggregate at night (film ~6 + digital ~2; film ≈3.7 pg/doc vs
digital ≈13.4 is WHY film completes docs 3× faster).

Old ledger-lump lesson stands: counters commit in lumps; never judge a
rate under 15 min. ⚠ ACRIS pdf end-of-doc is a PLACEHOLDER served as HTTP
200. **A/B SETTLED 2026-08-21: rd and pdf are SEPARATE POOLS** — run both;
sequential idles the image backend. **PDF CEILING: ~40 pg/s aggregate ≈
6.3 docs/s** (2×28 = 3-process-60-worker = same 40; one process knees ~26
on the GIL; hint of two ~20 sub-pools digital/film). OPERATING POINT: rd
4×28 + pdf 2×28 (digital arm + film arm). Film ≈3.7 pg/doc vs digital
≈13.4 → tilt film-first to front-load completed docs. pdf runway ≈145M
pages / 40 ≈ 40 days continuous — the long pole; rd ≈2 days.
