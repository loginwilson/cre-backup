---
name: project_bkrea_lot_lineage
description: "Lot lineage (retired BBL → today's parcel) is a PREREQUISITE for scaling past OneLIC, not a comp-lane nicety — and its failure mode is silent"
metadata: 
  node_type: memory
  type: project
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-08-05T11:35:09.072Z
---

Operator, 2026-08-05: **"you also need to remember for scaling that fixing the lineage is necessary
for later on."** Lineage is not a Comparable feature; it is a precondition for every pull that keys
on a BBL.

**The mechanism.** A gate is *today's* lot numbers, resolved from the polygon against live MapPLUTO.
Any document recorded on a lot since merged, subdivided or renumbered is filed under a BBL that is
no longer in the gate, so a BBL-keyed filter drops it. `.acris/legals` is harvested BY BLOCK, so the
data was already on disk — `deriveAcrisDeeds` threw it away with one line (`if (!parcels.has(bbl))
continue`).

**Why it survived: the audit read the filter's own output.** Every check ran over
`data/acris-deeds.ndjson`, which that filter produced, found zero retired-lot deeds, and reported the
gap closed. Measuring from inside the pipeline cannot see a loss the pipeline caused — see
[[feedback_bkrea_scale_failure]].

**Measured on OneLIC 2026-08-05** (`scripts/audits/lineageGap.ts`): 12 retired lots resolve into 11
gate parcels; **+10 comps recovered (158 → 168)**, including all three trades of the lot now inside
condo billing lot `4004387502` ($12.5M 2008 · $15.3M 2013 · $21.85M 2015). Condo billing lots are the
worst case — they assemble several parcels AND sit at lot ≥ 1001, so the unit-row filter drops them a
second time unless `_injected` is judged on the recorded lot.

⚠ **The real constraint is ambiguity, not plumbing.** The same run declined **201** vanished lots on
gate blocks that had multiple candidate sinks. 12 resolved against 201 declined is a ~6% resolution
rate, and at 7,030 LIC lots that ratio scales with the territory. `scripts/lineageMap.ts` returns
`declined` alongside the map precisely so callers report what they could not reach.

⚠ **A recovered trade is a sale of the OLD footprint.** Denominators must be read against
`recordedBbl`, never the successor, and `repeatPairs` must not pair across footprints — otherwise a
part is compared to the whole and the difference is called appreciation.

Related: [[project_bkrea_comparable_property]], [[project_bkrea_pluto_archive_delta]],
[[feedback_bkrea_document_over_page]].
