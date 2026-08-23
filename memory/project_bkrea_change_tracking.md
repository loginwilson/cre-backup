---
name: project_bkrea_change_tracking
description: BKREA populate = populate once then TRACK CHANGES per-parcel across many sources; pluggable scanner registry (lib/changeDetect.ts)
metadata: 
  node_type: memory
  type: project
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-26T18:12:00.399Z
---

**WHY THIS IS ARCHITECTURE, NOT PLUMBING (Login 2026-07-26):** "once we prove the system works on pull, package, monitor for my territory, we can test another smaller territory and the final run is to attempt the entire map." **LIC is the TEST BED — everything must work as a SYSTEM, parameterized by territory, never hardcoded.** Consequences to hold onto:
- Registries (`lib/changeDetect.ts` scanners, `lib/sourceAdapters.ts`) already take (boro, blocks) / paste text — territory-agnostic by design. Keep it that way.
- **Populate-once + monitor is the ONLY model that survives citywide** (~860k tax lots); a time-based re-pull never would. Already built.
- **HONEST TENSION — the paste-based commercial adapter does NOT scale.** Public pulls, scanners and the rate normalizer are all territory-agnostic pure logic and scale fine. But hand-pasting Crexi listings works for LIC's 39 rated records and cannot work citywide. Before "the entire map", commercial comps needs a real feed / partnership / broker feed-loop — or explicit acceptance that the lane is thin outside focus territories. Say this out loud rather than discovering it at scale.
- **Coverage honesty scales too:** 39 rated of 793 with any record (~5%) in LIC is a preview of every territory. The card must state coverage so a thin comp set never reads as a market fact.

**Core model (Login 2026-07-25): populate ONCE, then TRACK CHANGES per parcel across MANY sources — never re-pull the whole 7,030-parcel territory on a timer.**

**CORRECTED MODEL (Login 2026-07-25, commit 5259c63): NO time-based expiry at all.** "One time population with a daily monitoring system for changes." `POPULATE_FRESH_MS = Infinity` — a populated parcel stays populated. A re-run fetches only: (a) never-populated parcels, (b) parcels a CHANGE SCANNER flagged, (c) EVERYTHING when a new **MapPLUTO release** lands. PLUTO only changes on release, so the release tag is a monitoring key: `fetchPlutoVersion()` (lib/populate.ts) reads the dataset's `version` field (e.g. "26v1"); `plutoReleaseChanged(stored)` (lib/changeDetect.ts) compares + returns the live tag, stored in localStorage `bkrea.plutoVersion`. First run records the tag without stampeding; any failure = "nothing changed". Panel footer reports COVERAGE ("N/M parcels populated"), not freshness. STILL TODO: an actual DAILY scheduler (today the monitors run when a populate runs).

**Shipped earlier (superseded where noted):**
- ~~`POPULATE_FRESH_MS` 72h → 30 days~~ → now Infinity, see above.
- Client populate `CONCURRENCY` 3 → **8** (MapWorkspace ~6501) for the initial/forced pull.
- **Change-scanner registry** `lib/changeDetect.ts` (commits c17b8bc, 506c9e8): `ChangeScanner = {source, scan(boro, blocks:Set<number>, sinceISO, signal) => Set<bbl>}`; `detectChangedBBLs(scanners, …)` runs them concurrently, unions, returns `{changed, perSource}`, each best-effort. Populate loop runs it ONCE up front (45-day lookback) then skips a parcel only if **fresh AND not in changed set** — so a parcel that changed is re-fetched even inside the 30-day window.
- Two scanners live: **dof-sales** (recorded sale, `w2pb-icbu`+`usep-8jbt`, via `fetchRecentlySoldBBLs` in salesLedger.ts) and **dob-now** (new job filing, `w9ak-ipjd`, ISO `filing_date`).

**Sources — what the app tracks & what's missing (Login 2026-07-25):**
- PUBLIC (cheap date-filter → good scanners): DOF sales ✓, DOB filings ✓. NEXT: **ACRIS new-docs** (`bnx9-e6tj` recorded_datetime — new deed/mortgage/lien; block-scoping via Legals is heavy, ~350k recs — needs care), **HPD registrations** (ownership change + contact intel — biggest ownership gap), **DOF tax liens/arrears** (distress), **DCP ULURP/rezoning apps** (active upzones, beyond adopted amendments the study-area uses), **DOB/ECB violations**, **LPC landmark** (air rights). Also NYS DOS entity filings + JustFix "Who Owns What" for owner-behind-LLC + portfolio graph.
- LISTING (StreetEasy, CREXI, LoopNet) + PAID (Marketproof Pro/Pipeline, CoStar, Reonomy, Trepp): NO cheap date-filter API → they do NOT get scanners; refresh on the time window / on demand / their own change feed. Also news: YIMBY, PincusCo, The Real Deal, Traded.

**Ops note:** when a slow populate is running the OLD code, DON'T wait — hard-refresh to load new code; already-populated parcels persist (Supabase, batched flush) and get skipped. Watch for Socrata throttling at 8-wide; dial to 6 if failures spike. See [[project_bkrea_condo_sale_populate]], [[project_bkrea_sandbox_env]].
