---
name: project-acris-refusal-20260824
description: "ACRIS served its Bandwidth Notice 2026-08-24 03:45 — acris rd+pdf backfills STOPPED per the stop-on-refusal rule; what stopped, what runs on, and the resume protocol"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T09:11:22.625Z
---

**ACRIS REFUSED SERVICE 2026-08-24 ~03:45 EDT** — the image endpoint served
its Bandwidth Notice ("further access to acris is denied", "acris bandwidth
notice"; 5/5 signals) and by 03:44 the **rd endpoint served it too** (the
sync probe caught it). Sequence: rd rates sagged from ~03:00 (5m 74 → 10),
`ValueError` fails piling up in rd_walk_fails = the notice HTML failing to
parse (the rd walkers have NO refusal detector — add one before any relaunch),
then image_walk's detector fired 03:45 and all three pdf lanes stopped
themselves cleanly (zero-byte stderr = deliberate exit, not a crash).
CORRECTION (05:10): rd_walk DOES have the detector (LD.check_refused on
every page → AccessDenied → stop.set()); it never fired because rd was
served GENERIC error pages (0/5 signals → honest ValueError), not the
notice — fetch_pages deliberately refuses to conflate the two. The code
gap I claimed did not exist; the only real gap is no cumulative-volume
governor to self-pause before ACRIS's threshold.
RESOLUTION: service returned ~05:09 2026-08-24 (confirmed by sync probe
"control ok" after restart). Backfills relaunched at a GENTLER OPERATING
POINT per login's "continue and don't trip it": rd 4×20 (was 4×28),
image 3×14 (was 3×28, halving pdf byte rate — the budget spender).

**Stopped per the rule (do NOT restart until service is confirmed back):**
4× rd_walk (acris) — killed 03:48 because they were unknowingly hammering
through the refusal (+2,400 fails/20 min) — and 3× image_walk (self-stopped).

**Still running:** the full richmond side (different custodian, unaffected —
rc_feed/rc_pdf_pull/rc_pdf_land + rc_live), acris_live sync (its designed
exponential-backoff hold: 20s→40s→80s→160s single-request probes; it is the
resume detector — "level at crfn … control ok" reappearing = service back),
board daemon, board_truth/bridge, org_backfill_arm.

**Resume protocol:** wait for acris_live to report level again, let login
decide when to relaunch backfills ("resume another day" per the notice), and
consider gentler settings on relaunch (the notice is a bandwidth complaint —
4×28 rd + 3×28 pdf + sync was the load that drew it; it followed the 03:00
maintenance-window sag). ⚠ The board's acris acq rows reading STALLED during
this state is CORRECT — parked-config can't express it (parked is phase-level
and would wrongly mark richmond pdf too).

Related: [[project-rc-rd-coded]], [[project-acris-bulk-acquisition]],
[[project-decoder-updates-board]]
