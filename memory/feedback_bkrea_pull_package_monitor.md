---
name: feedback_bkrea_pull_package_monitor
description: "BKREA's governing architecture — pull → package → monitor, derived per bucket category from its goal"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-26T18:53:27.109Z
---

**The governing frame for all BKREA data work (Login 2026-07-26): PULL → PACKAGE → MONITOR.** Apply it per BUCKET CATEGORY, and derive it in this order:

1. **Start from the bucket + its GOAL.** "Look at the bucket category, ask what the goal is for that section." Commercial comparables' goal = base-level market/submarket understanding without calling brokers at unit level.
2. **Compile what the SOURCES should be** for that goal (public vs listing vs paid).
3. **Build a TRANSLATOR per source** that turns it into a **pull package** — one normalized shape.
4. **PACKAGE** = the card section that consumes it (here: the Commercial section of the Comparable card).
5. **MONITOR** = the change tracking over the same pull.

**"Much of pull is pull logic — which is where we should start."** The hard part is making one pull serve BOTH packaging and monitoring, so design the package for both from the start (stable identity per comp so a diff is possible, plus the fields packaging renders).

Worked example (in flight): bucket = commercial comparables · source = Crexi · translator = `lib/crexiLease.ts` (+ `lib/sourceAdapters.ts` registry for the other 6 sources) · package = commercial section of the comp card · monitor = the daily harvest.

**Why the PROSE EXTRACTOR is the backbone, not a bonus (Login 2026-07-26):** "this extractor is going to be the backbone regardless since it should keep the pull from being manual and allows for scaling." So don't treat description-mining as an edge case for records whose rate field failed — it is the mechanism that makes the pull non-manual and therefore scalable to other territories. Build it out accordingly. (This settled my open question about sampling hit-rate first — no need, build it.)

See [[project_bkrea_commercial_comps]], [[project_bkrea_change_tracking]].
