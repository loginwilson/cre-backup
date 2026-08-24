---
name: project-decoder-source-onboarding
description: "login's settled playbook for adding a source (DOB, BIS, DOF, …) — map inventory → pull code → source keyer → enter sync with inflow tracking → backfill+inflow count as ONE number"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T17:20:33.595Z
---

**THE SOURCE ONBOARDING PLAYBOOK (login, 2026-08-24 — "the move is"):**

1. **Map the doc-id inventory** — the source's id scheme, total count, and
   the spine rows (prefix + native id, like RC_). Mapping = INSERT into the
   record db; mint_urls gets a branch for the prefix's url shape.
2. **Figure out the pull in python** — how recorded details and the
   pdf/image (or however the source displays a document) are fetched.
   Probe the ladder before declaring anything unfetchable
   ([[feedback-never-assert-unfetchable]]).
3. **Figure out the keyer for THIS source** — where the key lives decides
   the pass structure: in-row (DOB BIN/BBL → pass 1 only, insert trigger)
   vs in-document (acris references/parties → passes 2/3). Key rules join
   key_rules' vocabulary.
4. **Enter it into sync** — edge/delta mechanism per source (crfn+1 probe,
   date-window page, Socrata :updated_at …) with inflow tracking SINCE THE
   MAPPED STATE: needed grows with inflow, and the mapped backlog drains
   through the same gates.
5. **Backfill and inflow count into ONE number** — landed = needed − todo
   (partial index per gate column, the ix_nav_rd_todo pattern); a doc is
   complete when its LAST gate fills (keyed at end of chain). Separate
   walker fleets are a THROUGHPUT choice for big backlogs, not
   architecture — same triggers, gates, counters; retire at 100%.

Each new source is five artifacts: id scheme · mint branch · key rule ·
sync probe · board row. The db already holds two custodians in one table
without caring which is which — that's the proof of shape.

**LANE-FIRST UPDATE (2026-08-24, after acris_lane proved out):** a new
source never gets separate sync + backfill fleets — it gets ONE LANE from
day zero (the acris_lane skeleton): edge probe tracks inflow at the front,
feeders drain the mapped todo through every gate (rd → key → pdf), a
GOVERNOR self-tunes worker width against the source's own load signals,
one refusal tripwire, one board row whose landed = READY (needed −
last-gate todo). The source's ACCESS RULE is discovered, not assumed:
**piano** (one access point, sequenced — acris) vs **drumroll** (fire
freely, just never push through a refusal — richmond). **UNIVERSAL RAMP
LAW regardless of rule** (login 2026-08-24, trip #3): never open
connections all at once — every lane launches with a soft ramp, staggers
cold starts, and treats mass simultaneous failure (network change,
sleep/wake) as a reconnect event demanding a full re-ramp, never a
straight reconnect at width. "The warmup is well worth a 5 minute wait." login: "the hardest
part is mapping the inventory which gives the ids. after that it's just
figuring out what the url mints are" — acq throughput and keying are the
same principle every time, coming off the rd and pdfs.

Related: [[project-decoder-fleet-restore]], [[project-decoder-updates-board]],
[[project-dob-decoder-state]]
