---
name: project-bkrea-comparable-property
description: "Comparable·Property is a residual-shortcut — the full reasoning, three removed features, and the HBU-at-purchase test live in docs/COMPARABLE_PROPERTY.md"
metadata: 
  node_type: memory
  type: project
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-08-05T01:47:13.331Z
---

The Comparable · Property lens was worked out end-to-end on 2026-08-04. **The reasoning lives in
`docs/COMPARABLE_PROPERTY.md` in the repo** — read that before touching the section, because three
good-sounding features were built and removed that day and the doc records why each fails.

**The one idea:** land price is a residual, so **$/BSF is a normalization, not a measurement** — only
valid when the comps share the terms it collapsed (use, era, entitlement certainty). Every dead end
was asking $/BSF a question it had normalized away.

**Do not rebuild:** per-use scenario pricing (one comp + N−1 fictions), value-ranking of uses (needs
product $/SF no feed carries), or picking the lens from the distribution (cannot separate wrong-lens
from a buyer who paid up).

**Non-obvious facts that cost real time to establish:**
- DOF's annualized sales dataset spans **2016-01-01 → 2025-12-31 only**. The `sinceYear: 2016` floor
  is the data's edge; no parameter reaches earlier. Pre-2016 depth comes from ACRIS priced
  conveyances + the local PLUTO archive (`scripts/deriveAcrisComps.ts`) — took OneLIC from 79 to 237
  comps. ACRIS consideration only survives from ~2000.
- `zoning_changes.json` infers rezoning years from **biennial** PLUTO snapshots, so ±2 years. Real
  dates need ZAP; OneLIC is `2024Q0304`, completed 2025-11-28. ZAP has **no geometry** — community
  district only — so it cannot date a rezoning per parcel.
- **A band is market evidence; the territory is a work scope.** Widening the vacant-land band to ±60
  blocks left the residential median identical ($260) with 10× the sample. The drawn-territory rule
  is about where WORK happens, not where EVIDENCE comes from.

See [[project-bkrea-pluto-archive-delta]] and [[feedback-bkrea-scale-failure]].
