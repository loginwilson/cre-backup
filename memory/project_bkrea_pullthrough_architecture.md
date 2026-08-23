---
name: project_bkrea_pullthrough_architecture
description: "BKREA core principle — Data → card → filter → map; every parcel's card is complete, the filter only buckets/overlays"
metadata: 
  node_type: memory
  type: project
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-23T14:32:16.738Z
---

The governing architecture of [[project_bkrea_territory_intel]], stated by Login (2026-07-23): **Data → card → filter → map.**

- **Every parcel** in the polygon pulls its full data to the **card** — Property Information, Opportunity (live even when *negative*, e.g. an overbuilt hotel), Development history, Comparable, Contacts — regardless of whether it's bucketed. The card is a universal dossier.
- **The filter** operates on the card data to create **overlay criteria**; the **map overlay/bucket count** reflects only what matches. Bucketing is a presentation lens, never a gate on the data pull.
- Sales analysis window = **2016 → today** (the MapPLUTO range that lets $/BSF·$/land·$/SF and before/after envelope be computed). Older sales can be *recorded* but carry no analysis. Territory is currently one sandbox (LIC/Hunters Point, block ~76–450+); the plan is to scale the pull to all 5 boroughs.

**Why it matters:** the classic bug is a filter that gates at the wrong layer. Example fixed 3881db7: Comparables→Sales defaulted to a DEV-SITE lens (underbuilt land only), which silently dropped built **investment sales** (hotel/office/retail assets that sold) — the inverse of a dev site — so the Hotel lane read 0 despite full hotel cards. Fix = `isInvestmentSale` as a partner lens (see `lib/salesLedger.ts`), so built assets survive the filter. Hotel 0→11 live.

**How to apply:** when a comparable "clearly falls in" but shows 0, suspect the FILTER (wrong standard) or a pull that gated by bucket — not the classification. Verify the card has the data first (data→card), then check what the filter drops. Reasoning must be **spatial** (the polygon's parcel set), never neighborhood/block heuristics. Related: [[feedback_decisive_execution]].
