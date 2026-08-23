---
name: bkrea-devbulk
description: "The population engine — pull feeds wholesale, derive 94k sites at 11µs/site, enrich watchlist via PW1; per-site portal calls can never population-scale"
metadata: 
  node_type: memory
  type: project
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-07-30T20:30:29.653Z
---

**The inversion (2026-07-30, operator-mandated: "sites in the blink of an eye").** Per-site interactive pulls (portal/BISWEB) can never serve the 5-boro population or daily polls — Akamai tarpits ~11 s/call after volume. `scripts/devBulk.ts`: **PULL** feeds wholesale to `.bulk/` NDJSON (BIS ic3t-wcy2 NB/DM/A1 doc-01 395,578 rows + NOW w9ak-ipjd 125,411 + both CofO sets, ~2.5 min citywide) → **DERIVE** every site as in-memory joins (94,361 sites, load 5.9 s + derive 1.1 s = 87,859 sites/sec) → **ENRICH** watchlist/changed jobs only via GetJobFilingPW1 (phones/emails/precision zoning; the feeds carry names/licenses/LLCs already; BIS feed carries approved/fully_permitted/signoff DATES + existing→proposed scale + occupancy for conversion-detect).

**Unit mix cracked (2026-07-30):** `GetMasterScheduleOfOccupancy/<BIN>` on WrapperPP — structured floor-by-floor rows (occupancy group, use, ZUG, dwelling units per floor; Vesta's 13 rows sum to its exact 115 units). Found in the SPA registry (alias `GetBinSofoOrBinCofo`); per-FILING `GetScheduleOfOccupancy` returns `[]` — the BIN-keyed master is the door. ⚠ `Proposed` is often an all-null object — read the populated side. Harvest also saves `firstParties` (the design architect often rides the FIRST filing — Vesta's Raymond Chan was its rep) + `sofoUnits` → `unit_splits`. Card reads live via `lib/liveDevelopment.ts` (bbl→governing_job match); reach attaches only to its own name/firm.

DM details in bulk join `dm_sweep` (document-grade). `grade` is explicit per row — speed never launders feed numbers into document numbers. Results → Supabase `developments` (migration 0012, upsert on bbl) alongside dm_sweep/lot_lineage/pluto_snapshot from 0011. `scripts/proveBbl.ts` = consistency harness driving the real dossier on random BBLs (document-grade spot checks). Daily flow: re-pull (Socrata `:updated_at` deltas eventually) → re-derive → push. See [[bkrea-pluto-archive-delta]].
