---
name: project-bkrea-rentals-pipeline
description: "BKREA rentals lane — StreetEasy api-v6 + alias batching, and the PLUTO placement test that stops ledgers landing on schools/warehouses"
metadata: 
  node_type: memory
  type: project
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-27T17:06:56.210Z
---

Rentals in [[project-bkrea-territory-intel]] run on **StreetEasy**, not Marketproof (Marketproof is
an enricher / cross-reference only). Full rules: `docs/rentals-pipeline.md` in the repo.

The four rules that were each learned by getting them wrong on 2026-07-27:

1. **`api-v6.streeteasy.com`, never `api-internal`.** api-v6 is camelCase and needs NO auth, and it
   keeps answering while streeteasy.com is PerimeterX-blocked. api-internal needs the cookie and
   dies with the session. An earlier session saved the queries but not the host, so this was lost
   twice.
2. **Batch with GraphQL aliases (12/request); do not pace.** PX counts REQUESTS, not rows. 11
   buildings → 10,414 events in one 312ms call. Pacing at 280ms got the session blocked.
3. **A geocoder answer is a candidate, not a placement.** Reverse-geocoding a pin put 1 QPS's 674
   leases on a 1920 factory and Gotham Point South's on a NYC school; forward-geocoding put The
   Pecora on a hotel. PLUTO adjudicates physically: `unitsres > 0` and `unitsres*3 >= units`.
   Unplaced (with a stated reason) beats misplaced — missing data is visible, wrong data is not.
   Do NOT use distinct unit labels as the capacity floor; it false-positived 536 parcels.
4. **Paginate every Supabase read.** PostgREST caps at 1,000 rows and returns them WITHOUT error;
   this made the monitor report 194 parcels when the truth was 1,122, and the number drifted between
   runs in a way that reads exactly like market movement.

Multi-tower lots are real (85 in Astoria+LIC): group by BBL before batching because a write is a
REPLACE. Gotham Point North 689 + South 443 = 1,132 = PLUTO's unitsres for lot 4000067503 — both
towers genuinely are one parcel. See [[project-bkrea-condo-sale-populate]] for the parallel
multi-lot convergence problem on the sales side.

**Why:** the operator's standing rule is "clean the data instead of just reporting it" and
"investigation rather than automatic removal" — a comp on the wrong parcel looks completely normal
and is silently false, which is worse than a gap.

**How to apply:** when adding any new rental source, run it through place → reconcile → monitor
before trusting a single number, and date-tag the pull (`data/pull-log.json` + per-parcel
`rentPulledAt`) so staleness is never inferred from a file mtime.
