---
name: bkrea-pluto-archive-delta
description: PLUTO archive spans 02a–26v1 (three naming eras); DM delta anchored at job year; lineage resolves vanished DM lots to successors
metadata: 
  node_type: memory
  type: project
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-07-30T18:46:32.524Z
---

As of 2026-07-30: the PLUTO tabular archive spans **02a → 26v1 (current)** — the "ends at 18v1" belief was wrong; the 18v2+ era is citywide csv named `nyc_pluto_{v}_csv.zip` (22v3/23v1 never published; 18v2–22v2 on www.nyc.gov, 23v2+ only on s-media). Wired in `scripts/buildLotLineage.ts` (VINTAGES, citywide split, quote-aware csv). `plutoVintage.ts` anchors the drop search **at the DM's job year** — anchoring on the last standing building broke once the archive outgrew the rebuild (a 2015 DM un-confirmed itself against its 251,307 sf successor tower).

Delta trial (MN, 8 keys): 3 CONFIRMED, 2 LIVE, 2 LINEAGE → resolved by block conservation (MN 2013 lot 44 → 29, ONE45 LENOX 4-lot assemblage at 22v2; MN 1309 lot 72 → 69 at 23v2), 1 NOT_FOUND (lot never carried building area — check condo/billing-lot mismatch). Extell criterion holds to current: ten 2002 single lots → 7502 at 13v2, standing 487,351 sf at 26v1. All MN vintages cached in repo `.pluto-archive/` (gitignored).

Matrix with full archive: BIS DM details 0% → **100%** (live bldgarea 0 must TRIGGER the delta — cleared vs vacant is ambiguous; VACANT is a first-class answer). Timeline scored against **stage** (filed-only or approved-no-permit = complete; `PlanApprovedDate` exists on the raw PW1). Contacts walk EVERY envelope PW1 (approved ⇒ all three roles signed somewhere). Citywide sweep `scripts/dmSweep.ts` (~46k keys, one borough-vintage load each; parseAll must buffer-scan or Brooklyn/Queens OOM silently); results → Supabase via migration `0011_dm_sweep_lineage.sql` + `scripts/pushDmSweep.ts` (idempotent upserts for daily change polls; **user must apply 0011 in the SQL editor** — CLI not linked, no DB URL in .env.local). ⚠ DOB NOW portal tarpits ~11 s/call after heavy use (Akamai) — matrix runs crawl; 30 s timeouts in dobNowClient keep them terminating. `lot_lineage` doubles as the ACRIS join layer for before-vs-now sales analysis. Gate: DOB NOW 100/100/100/100, then BIS to same level, then 5-boro population (approved 2008+, rejected/withdrawn-no-follow-up 2020+) and daily polls; see [[project_bkrea_source_registry]].
