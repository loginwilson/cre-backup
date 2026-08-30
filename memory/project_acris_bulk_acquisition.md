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

## ⚠ 2026-08-26 — THE 4×28 OPERATING POINT NO LONGER HOLDS. ONE ARM ONLY.

ACRIS served its **Bandwidth Notice twice in one day** under the old fleet shape.
Measured curve for a SINGLE `rd_walk` arm (marginal docs/s, per-minute deltas —
never the lane printer's lifetime average):

    1 arm x 12 workers   13.8 docs/s
    1 arm x 28 workers   26.9 docs/s
    1 arm x 64 workers   33.6 docs/s   <- the efficient point
    1 arm x 80 workers   34.2 docs/s   <- +1.8% for +25% connections = CEILING
    4 arms x 28 (=112)   REFUSED, twice

⚠ **THE SOURCE COUNTS CONNECTIONS, NOT ARMS.** "One arm" is not itself the rule —
112 concurrent tripped it whether from 4 processes or 1. One arm is just a
convenient cap. The variable to tune is TOTAL CONCURRENCY.

⚠ **THE DOCSTRINGS' "GIL knee ~26 workers" IS WRONG FOR rd_walk.** 64 workers
beat 28 by 25% in one process. The parse releases the GIL more than the note
assumed. `image_walk`'s ~26 figure may still hold — it does far more CPU per doc
(G4 wrapping) — but it was never re-measured.

⚠ **THE BANDWIDTH NOTICE IS CUMULATIVE VOLUME, NOT INSTANTANEOUS RATE.** Proof:
after the block, a FOREGROUND run at 4 workers refused immediately. A rate limit
clears when the rate drops; this did not. Today's spend before the second block:
**193,625 rd docs ≈ 23 GB**, plus ~28k page images that morning.

⚠ **gzip IS NOT AVAILABLE — TESTED.** `Accept-Encoding: gzip` returns
`Content-Encoding: (none)` and the identical 118,475 bytes. So **118 KB per
document is fixed**, there is no compression lever, and the daily budget is
therefore a hard document count. At 34 docs/s that is ~14.4 GB/hour — an
overnight run would pull ~127 GB and is certain to trip.

⚠ **RESTARTS ARE THEMSELVES LOAD EVENTS.** The second refusal came after
laddering 12→20→28 workers in ~30 min, each rung restarting 4 processes, on a
host that had already refused once that day. The notice's own words are the
rule: *"do not retry, do not rotate, do not raise concurrency."*

**Richmond is unaffected by any of this** — different host
(richmondcountyclerk.com), ran `err 0` throughout both ACRIS blocks.

## ⚠ pdf IS ~12 REQUESTS PER DOCUMENT - PLAN IN REQUESTS, NOT DOCUMENTS

From the 2026-08-24 pdf tempo ladder:

    tempo  91.3 req/s  delivered  88.9  ->  7.90 docs/s   = 11.3 req/doc
    tempo 107.3 req/s  delivered 105.6  ->  8.74 docs/s   = 12.1 req/doc

A document is a metadata call PLUS one image request per page. rd is 1
request per document. **So the thing ACRIS meters (requests) and the thing we
count (documents) differ by ~12x on pdf and 1x on rd** - a pace that is safe
for rd says nothing about pdf.

    rd at 25.3 docs/s  =  ~25 req/s
    pdf at that same request rate  ->  ~2 docs/s
    pdf's own measured best        ->  8.74 docs/s

~19.6M pdf remaining at 8.74/s = **~26 days continuous**. pdf is the long
pole by a wide margin. ⚠ And at steady state, low document inflow still means
~12 pdf requests per new filing - the lane's request rate stays pdf-dominated
even when inflow is small.

## ⚠⚠ STORAGE MAY NOT FIT - MEASURE BEFORE THE pdf CAMPAIGN

    pdf store today   2,035,977 docs in ~2,640 GB  =  ~1.3 MB/doc
    full corpus       21.6M x 1.3 MB               =  ~28 TB
    the One Touch     18.6 TB total

⚠ ROUGH, AND THE UNCERTAINTY RUNS THE WRONG WAY: unknown what fraction of
those 2M are real files vs ZERO-BYTE `absent`/`imageless` verdicts. If many
are verdicts, real per-document size is HIGHER, not lower. Measuring the split
needs a table scan (pdf values other than ''/'pending' are not indexed) - do
it while lanes are PAUSED, not during a run. Answer this before committing to
a 26-day pdf campaign. See [[project-acris-access-shape]].
