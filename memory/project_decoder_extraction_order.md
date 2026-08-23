---
name: decoder-extraction-order
description: "Extraction reads documents ISOLATED and order-independent; BBL/chronological ordering belongs to resolution, as a sort over extracted rows"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-23T01:25:30.754Z
---

Settled 2026-08-22 (login asked whether extraction could run BBL-ordered
oldest→newest, or isolated-then-reordered). **Isolated, then reordered.**

Five reasons, four engineering and one that is the real one:

1. A document's BBL set is unknown until it is read (R40 deed carried 3).
2. Documents attach to many parcels — a BBL queue re-reads or dedups.
3. Chain edges arrive as REEL/PAGE cites in the BEING clause, not BBL,
   so resolution needs a cite resolver regardless of read order.
4. BBL order serializes what the H200 fleet must parallelize.
5. ⚠ **Chronological reading invites the bootcamp's core defect.** Having
   just read the 1997 deed, a reader carries its facts into the 2002 read
   as a PRIOR — and every standing rule says neighbours, siblings and the
   rd are VERIFIERS, never priors (R4-4). Isolation keeps each claim
   anchored to its own pages.

**Why:** order-independence is a CORRECTNESS property, not just an
engineering convenience.

**How to apply:** extraction owes resolution the CITES as first-class
fields — reel/page, CRFN, document id, prior-deed dates — so the edges
exist to sort on. Reordering is then cheap and re-runnable by BBL, party,
function or chain without re-reading anything. See
[[acris-resolution-model]], [[decoder-extraction-loop]],
[[decoder-seven-phases]].
