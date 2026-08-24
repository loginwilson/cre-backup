---
name: project-acris-consolidated-lane
description: acris_lane.py = ALL of acris in one process (edge+rd+pdf+key); ready=needed−pdf_todo; freshness clause; scaling plan for <30-day target
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T14:15:19.000Z
---

**THE CONSOLIDATED ACRIS LANE (cut over 2026-08-24 ~10:12).** `acris_lane.py`
(decoder dir) is the ONLY process allowed to touch ACRIS — login's piano rule:
"one access at a time... a super concise machine playing piano." Four organs,
one process: edge probe (10s reservation, walk-on-hit, rd arrives IN the probe
request) · rd backfill (28 workers, ix_nav_rd_todo) · pdf pool (20 workers,
trailing feeder + HOT LIST — sync landings jump the queue; new filing fully
ready in ~1 min, proven 10:08) · keying (key_on_rd trigger, no process).
Launch: `python fleet.py start sync` or
`python acris_lane.py --apply --workers 28 --pdf-workers 20`, stdout →
NAV_WORK\acris_lane.log. Retired: acris_live, rd_walk×4, image_walk×3 —
starting any beside the lane recreates the tripping condition.

**FRESHNESS CLAUSE:** TotalPages≤0 on a doc recorded within --fresh-days (30)
= DEFERRED (pdf stays '', feeder wrap retries), never `imageless` — scan lag
is not a verdict. Only aged docs earn `imageless`.

**READY = needed − pdf_todo** (exact: pdf only ever follows rd;
ix_nav_pdf_todo index-only). Board sync acris row = (ready, ledger total);
rate keys off the lane's "PDF PROGRESS N pdfs · M imageless" line (ready-docs,
one subtraction for rate+increase). rd detail = "N total" line + hidden acq rd
row. ONE refusal tripwire stills BOTH pools; probe continues as resume
detector; resume = login's call.

**<30-day target** (login): ~19.9M pdfs left needs ≥7.7 ready/s sustained;
measured image-backend ceiling ~6-8/s aggregate (worker-independent). Plan:
scale pool (CPU was 46% of one core), inherit rd's threads when rd closes
(~2 days), ProcessPool-offload img2pdf/md5 if GIL pins first. Next: rc_lane
for richmond (rd closed → edge+pdf only) → pure 2-row board. See
[[project-decoder-updates-board]], [[project-decoder-fleet-restore]],
[[project-acris-refusal-20260824]].
