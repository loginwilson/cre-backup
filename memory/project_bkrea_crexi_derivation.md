---
name: project_bkrea_crexi_derivation
description: Crexi lease-data derivation rules learned by crawling records one at a time — the defect catalogue behind lib/crexiLease.ts
metadata: 
  node_type: memory
  type: project
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-26T20:27:17.856Z
---

**The Crexi translator's rules were LEARNED BY READING RECORDS, one Lease Data tab at a time** (crawl began 2026-07-26, Login: "all I am doing is giving you the area to work within and you are learning how to pull"). Territory query saved in `docs/harvest/crexi-query.md`; 844 records, 793 with a lease record, only 39 with a published lease rate.

**The governing lesson: Crexi's table columns are NOT a data source.** Every published figure must be re-derived. Defect catalogue (each found on a real record, each with tests in `lib/crexiLease.test.ts`):

- **(A) TOTAL wearing a /SF label** — 38-58 11 St: "$116,400/SF/YR" is the annual total; ÷ 4,220 SF = **$27.58**.
- **(B) ANNUAL rate typed into the MONTHLY field**, ×12 by Crexi — 30-16 30th Dr "$68/SF/MO → $816/YR"; the true rate is $68/SF/YR. **The tell is NOT internal inconsistency** — monthly×12 always equals yearly, even when right (23-22 30th Ave: $4.42×12=$53.04≈$53 ✓). The tell is that the *yearly* figure lands out of band while the *monthly* one lands in band.
- **(C) Shared-rate multi-space** — one rent stamped on every space row; sum the RSF, emit ONE comp (else double-count AND misstate the rate).
- **(D) "Update" status churn** — 23-22 30th Ave has **76** Space-History rows, all status "Update" across two days: broker keystrokes on a live listing, not deals. Collapse to latest-per-distinct-rate, tier `active`.
- **(E) No building → no $/SF** — 11 Street (APN 4000650151) is a 1,000 SF NYC DOT sliver with blank Building SqFt and a published "$468/SF/YR". The danger is Lot SqFt sitting there ready to be mistaken for a denominator. Ground leases are the exception.
- **Residential Unit Mix blocks (Dwellsy IQ)** are spliced into mixed-use records and drag the published rate range toward apartment rents. Strip before parsing. On 23-22 the unit mix even matched a *different building* (30th Road vs 30th Avenue).

**Derived RSF (Login's insight):** RSF = annual total ÷ annual $/SF — recovers records that would otherwise fail the truth gate for want of a denominator. Two guards: circularity (Crexi prints one fact twice; quotient of 12 = a unit conversion, not a size) and plausibility. **It survives an annualization error** — a shared factor of 12 cancels, so size is knowable while the rate is still in dispute.

**Use type is per SPACE, not per BUILDING** (Login: "we need to know what use type is comping at what"). 38-58 11 St is Industrial and leases an "Office"; a Ground Floor is retail even in an office building; medical is office. A deal spanning mixed space drops the use rather than picking one.

## ⭐ TWO SOURCES PER RECORD — the core model (confirmed 2026-07-26)

| Where in the Lease Data tab | Format | Tier | What it is |
|---|---|---|---|
| **Space History** | text | `reported` / `active` | a broker's ACCOUNT of a deal |
| **blue "Data Tables" button** | **IMAGES** | `documented` | income statements & rent rolls — named tenants, exact SF and rent |

Login: *"this is very reliable cause its an income statement with tenants and exact numbers. This is the same place you may see rent rolls."* **Clicking Data Tables is REQUIRED on every record** — reading only Space History is what kept the crawl stuck at `reported` for seven records. 23-22 30th Ave has **23 data tables**; #1 is a full rent roll on a record whose Space History held only asking rates.

Tables are hosted images → **no regex reaches them; the documented tier is a VISION step** (transcribe, then `parseIncomeStatement` in `lib/crexiIncomeStatement.ts`). Slower and less automatable than the text tiers — factor that into any daily-harvest promise.

**Reconciliation rule:** a statement's own columns disagree. Motion PT on 23-22 reads $42.74 (annual col) / $47.24 (monthly×12) / $46 (stated base). **Prefer monthly×12** — it ties to the printed gross totals. NEVER average conflicting columns; pick the reading the document's arithmetic supports and carry the disagreement into the note. Compute the blended rate ($506,590 ÷ 9,540 = $53.10), don't copy the rounded "$53" average line.

**RENT ROLLS DO EXIST ON CREXI — behind CLICKABLE DATA TABLES in some Lease Data sections** (Login, 2026-07-26: "I know for a fact just from flipping through the tabs that there are some of the lease data sections that have data tables that I click and I can see the entire rent roll attached"). So expanding those tables is part of reading a record, not an optional extra.

**Expect REPORTED to dominate** — "most data on historical will be broker reported." That is the normal shape, not a defect in the parser. **Documented is RARE but real**: only a few records carry a roll.

⚠ Don't repeat my error: on 1043 47th Ave (APN 4000470017, the record behind Login's "5,300 SF of commercial at $13,000" example) the roll WAS gated — public page shows only Asking Price, Cap 5.6%, aggregate NOI $439,602, then "Contact Exclusive Agents … Offering Memorandum". I generalized that single record into "Crexi does not publish rent rolls," which is FALSE. One gated record proves nothing about the corpus.

**Method (Login's instruction): move through the territory historicals IN ORDER, classify as you go, and note whenever a NEW means of deriving a comp appears.** Don't hunt for a specific shape — crawl and classify.

**MIXED USE ≠ residential.** 1043 47th Ave is typed "Mixed Use, Multifamily, Retail" / subtype "Apartment Building" — 13 free-market apartments over 5,000+ SF retail. The residential guard was rejecting it at record scope and taking the retail with it. Test the TYPE for "Mixed Use" + a named commercial lane, NOT the subtype — that still catches Center Blvd (typed plainly "Industrial" + "Apartment Building" = mislabelled, not mixed).

**Drive the drawer by URL, not clicks:** set `selectedId` + `selectedSlug` from a `/property-records/<APN>-<CITY>-<ZIP>/<hash>` link. Clicking rows and arrows fails silently and often.

**HOW TO READ A RECORD FAST (found 2026-07-26):** don't screenshot the drawer. With the Lease Data tab open, run `document.body.innerText`, `lastIndexOf('Space History')`, slice ~900–2200 chars. That returns the whole Space History + Timeline + Marketing Description as clean text in ONE call — and it is exactly the format `parseCrexiLease` consumes. Roughly 10× cheaper than scroll-and-screenshot.

**Crexi renders it as a DEFINITION LIST**, so label and value land on SEPARATE lines ("Asking Rate Monthly" ⏎ "$30.00/SF/MO"). `foldLabelValueLines` handles this; the label list is a whitelist so space headings ("Office" ⏎ "1,795") don't get fused. Hand-written one-line fixtures hid this bug for six records — **always test against verbatim copied page text.**

Stepping the drawer: click the next arrow in the drawer header, but re-locate it each time — page scroll moves it and clicks silently miss (the URL's `selectedSlug` is the check that you actually advanced). Batching 3 click→read cycles in one call did NOT work for this reason.

**⚠ Crexi runs `api.rupt.dev` device fingerprinting / bot detection** (observed 2026-07-26). The manual learning crawl is fine, but the scaled daily harvest should NOT be an automated scraper against Crexi — pursue a licensed feed, or lean on public sources. The translator is source-agnostic and keeps its value either way.

Commits: `6515e0c` (B) · `21171e1` (D + unit mix) · `c4b6b04` (per-space use, derived RSF, no-building).

See [[project_bkrea_commercial_comps]], [[feedback_bkrea_pull_package_monitor]].
