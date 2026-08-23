---
name: project_bkrea_condo_sale_populate
description: "How condo/multi-lot sales populate in BKREA — DOF already has them; fix is appbbl re-attribution in shapeSales, not an ACRIS pull"
metadata: 
  node_type: memory
  type: project
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-24T13:55:15.569Z
---

BKREA "every parcel returns its last sale + buckets reflect it" gate (Login, 2026-07-23). Hard-won findings:

**Bucket counts come ONLY from DOF** (`lib/salesLedger.ts` → `fetchTerritorySaleRows` pulls annualized `w2pb-icbu` 2016+ and rolling `usep-8jbt`, by block range). NO ACRIS. The per-parcel ACRIS deed (`lib/acris.ts` `fetchAcris`/`fetchAcquisition`) fills the Sale *card* lazily on click but NEVER merges into the ledger — so populating a card does NOT move the Sales/Residential/Condos bucket counts. That's the root of "populated cards, no bucket change."

**DOF ALREADY HAS the condo land sales** — they're just dropped when the land lot vanished into condo billing lots. `fetchTerritorySaleRows` (by block) returns the vanished land lots' historical rows. Verified 45 Road $9.82M 2016-04-05 5-lot deed: DOF puts the FULL price on ONE lot (lot 42 = $9,820,000) and **$0 on the 4 sibling lots** (40, 39, 9, and 33 on block 45), same sale_date. That $0+same-date+priced-sibling pattern is how DOF encodes a multi-lot deed (contrast ACRIS: full amt once per document_id). The land lots (40,39,42,9) are gone from PLUTO (subdivided → billing lots 7503/7504/7507/7508, +45/7503), so shapeSales drops/misattributes them.

**The fix (feasible, cheap — NOT a territory ACRIS pull):** in `shapeSales`, re-attribute a vanished land-lot sale to its CURRENT condo billing lot via PLUTO `appbbl` (reverse: billing lot's appbbl = land lot). Then the existing multi-lot deed grouping (byDeed) converges the 5 rows into ONE project. Per Login: multi-lot **converges to one, counts ONCE** in buckets; card breaks down per lot; outline frames ALL deed lots (a deed can span blocks — 45 Rd's 5th lot is on block 45, off-screen). See [[project_bkrea_territory_intel]].

**THE REAL GATE (Login, 2026-07-23):** only 1,319 of 7,030 parcels are labeled as ever-sold — because buckets = DOF 2016+ only. The other ~5,700 have their last deed FURTHER BACK in ACRIS (pre-2016) or in a form DOF drops. Every parcel has a last recorded deed; must pull it for ALL 7,030 (analysis if 2016+, else record date/price, else "date only"). Proof metric: the sold count climbs from 1,319 toward ~7,030.

**Sizing (measured 2026-07-23):** ACRIS Legals ~1,648 records/block (Queens blk 76: 156 distinct lots incl. historical/unit lots, 33 current PLUTO parcels). ~200 territory blocks → **~350k legal records + comparable Master volume**. TOO HEAVY for on-load → must be a ONE-TIME POPULATE (page territory ACRIS once, resolve last deed per parcel, STORE per-parcel; buckets read the stored last-sale). ACRIS Master has NO bbl; Legals has bbl but no doc_type/date/amt → must join Legals(bbl,doc_id)×Master(doc_id,doc_type,date,amt). Multi-lot grouping via Master document_id (reliable, unlike DOF's fuzzy date+price). Bulk production write → run on a sample block first, show the count move, then full territory.

**PARKED for a later "audit & fix-up" pass (Login 2026-07-23 — don't rabbit-hole now):**
1. Permanent one-click territory HEALTH/AUDIT view (the ad-hoc `window.__saleHealth` instrumentation this session should become a real diagnostic: count reconciliation, dropped-sale classification, coverage %).
2. STORED populate for scale — condos are filled by ~10 live ACRIS calls per territory load (`fetchLastSalesForParcels`); fine for one LIC territory, but many/large territories need a pull-once-and-cache last-sale per parcel.
3. Per-number SOURCE labels on the sale card (DOF vs ACRIS-via-appbbl).
4. Condo land-basis for ASSEMBLED TOWERS is the shakiest number — the single appbbl deed may be PARTIAL. DONE 2026-07-23: a soft flag (commit 66a8f69) when a BUILT-OUT residential building (built >70% of envelope) reads land $/SF < ~$150 → "verify full acquisition." A low $/BSF alone is NOT the tell (that's dev upside on underbuilt lots). **BROADENED 2026-07-24 (commit 4fa0077):** the flag now fires for ANY use when the land basis is far below market — `$/land SF < 50`, or `$/BSF < 10` when lot SF missing (anchor on $/land, FAR-independent, so genuine dev-upside low-$/BSF isn't flagged). Overlay: a nominal sale drops its fake per-SF rate and shows the RECORDED PRICE + "*" (emoji don't render on the MapLibre glyph layer) so the parcel stays visible but never poses as a comp. Canonical example = **42-34 24 St (BBL 4004280017, blk 428 lot 17)**: a $322K garage ($16/land · $1/BSF) swept into the **Aura LIC** tower assemblage (lot 19 = 23-10 42 Rd, appbbl→lot 17, same owner "42ND ROAD LIC PROPERTY OWNER LLC"; $74.7M constr. mtge 2023). STILL NOT fixed (deeper): the card divides a SINGLE lot's price by the COMBINED multi-lot envelope — a true fix only sums envelope across lots the priced deed actually covered. See [[project_bkrea_portfolio_comps]].
5. Known small gaps from the health check: ~1 apportionment successor + ~8 boundary-edge parcels miss their sale (of 7,030); dev-site filter bundles all controls into one lens; buckets classify by TODAY's zoning not use-at-sale.

**Overlay (Login-confirmed):** condo TODAY column = `$/USF` sellout, rental = `$/RSF`, both vs AT-PURCHASE `$/BSF` land basis. Multi-lot summation already fixed in acris.ts (commit 75c0e5a: reverse-appbbl sum of lotarea/buildable/built → 45 Rd reads $393/BSF not $1,637).
