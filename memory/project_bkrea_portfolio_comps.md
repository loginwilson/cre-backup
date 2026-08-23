---
name: project_bkrea_portfolio_comps
description: "Future BKREA direction — comparables across an owner's portfolio / assemblage, not just per-parcel; blocked on Opportunities & Developments cleanup"
metadata: 
  node_type: memory
  type: project
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-24T13:55:25.336Z
---

Login's idea (2026-07-24), PARKED: build comparables across a **portfolio / assemblage** — where one owner holds multiple lots. Sometimes acquired at the same time, sometimes assembled over years. The interesting comp lens is looking **across portfolios/assemblages** as the unit of comparison, not the single parcel.

**Why it's live-relevant already:** the nominal-basis fix ([[project_bkrea_condo_sale_populate]] item 4) surfaced a real assemblage — "42ND ROAD LIC PROPERTY OWNER LLC" owns both the Aura LIC tower lot (23-10 42 Rd) and the adjacent garage lot (42-34 24 St), appbbl-linked. That owner-as-assemblage grouping IS the portfolio lens in miniature.

**Blocker (Login's own call):** must finish cleaning up the **Opportunities** and **Developments** logic first — there are holes in them, and portfolio comps sit on top of correct per-parcel classification. Don't start portfolio work until those are solid.

**How to apply:** when Opps/Devs are cleaned up, revisit. Grouping key candidates: ownername + appbbl chains + shared deed document_id. See [[project_bkrea_territory_intel]].
