---
name: feedback-guarded-roster-edit-order
description: "A roster watched by a restart guard has NO safe edit window - write the PAUSED name first, the lane second; cost 6 live requests into an active ban"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d1473bc-bb54-490c-8d66-326f7b72067b
  modified: 2026-08-29T16:56:47.723Z
---

**PAUSED NAME FIRST, LANE SECOND.** In `decoder\fleet.py`, adding a row to
`LANES` makes that lane startable the instant the file saves — and **CRE Fleet
Guard** is a Windows scheduled task firing `fleet.py start all` **every 5
minutes** (trigger `PT5M`).

On 2026-08-29, during an active ACRIS denial I had *just* finished parking the
fleet for, I wrote the `acris_repro_register` LANES entry, then added its name
to `PAUSED` about a minute later. The guard fired at **12:39:03** in that gap
and launched it straight into the ban. The lane behaved perfectly — stop-on-
refusal killed it in 23 seconds — but **6 requests still went out**, and login
had told me not to touch the source. login: *"you just killed my pull by
rogue"* / *"dont do that again."*

**Why:** an idempotent guard is a safety feature that becomes a hazard the
moment you edit the thing it reads. It does not know an edit is half-finished;
a partially-written roster is just a roster. There is no quiet moment to work
in — the window between two saves IS the exposure.

**How to apply:**
- Adding a lane: save the name into `PAUSED` **first**, verify, then write the
  `LANES` row. Reverse order for un-pausing — remove the name only when you
  actually intend it to run, as the last edit.
- After ANY roster edit, run the guard's own command (`python fleet.py start
  all`) and read the output. It prints `PAUSED - skipped` per name; that line
  is the proof, not the intention in your head.
- A hold is not applied until the **respawners** are handled, not just the
  processes: the guard task AND every scheduled task that touches the source
  (`ACRIS-MapDelta-Daily` was still armed for 04:00 and had to be disabled).
- Stopping a process ≠ stopping the work. Ask "what restarts this?" before
  believing anything is stopped.

Related: [[project-acris-access-shape]] (the shards/doors finding from the same
incident), [[project-decoder-fleet-restore]], [[feedback-decisive-execution]].
