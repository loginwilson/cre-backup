---
name: reference_bkrea_fdic
description: "FDIC bank data for BKREA retail comps — what the APIs give, and why it's corridor CONTEXT + a vacancy signal, not a rent comp"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-26T17:41:35.496Z
---

**STATUS: DEPRIORITIZED (Login, 2026-07-26, after this research): "maybe it isn't on the map and can just be a part of the dashboard later as a fun little fact."** Do NOT build a map overlay or a card field. Keep this file as the finished research if it's revived for the dashboard.

**Assigned by Login 2026-07-26** ("less familiar with the FDIC, but told it could signal value — figure out how it works, where its value is, and assign it where necessary"). Researched live 2026-07-26.

**Two working public APIs (no key, note `banks.data.fdic.gov` 301-redirects to `api.fdic.gov`):**
1. `https://api.fdic.gov/banks/locations` — CURRENT branches. Fields: `NAME` (bank), `OFFNAME` (branch), `ADDRESS/CITY/ZIP`, `SERVTYPE_DESC` ("FULL SERVICE - BRICK AND MORTAR"), `ESTYMD` (established), **`LATITUDE`/`LONGITUDE` (pre-geocoded)**. 16 branches in Long Island City. Index rebuilt ~daily (saw `locations_20260724…`). Contains ACTIVE branches only — no closure date field.
2. `https://api.fdic.gov/banks/sod` — **Summary of Deposits**, the valuable one: **`DEPSUMBR` = deposits at THAT BRANCH ($ thousands)** by **`YEAR`**, annual series back to 1994 (155,191 NY rows). Filter `STALPBR`, address `ADDRESBR`, city `CITYBR`, name `NAMEFULL`.

**WHERE THE VALUE IS — FDIC gives NO rent, so it is NOT a comp tier.** Comps need rate·size·date·term; FDIC has none. It belongs as **Retail CONTEXT**, and as a **signal**, never in Blended/Documented/Reported/Active:
- **Corridor strength** — `DEPSUMBR` and its YoY trend is a proxy for the trade area's economic weight. Bank branches sit on prime ground-floor retail, so deposits ≈ how good that corner is. Supports/【challenges】 a retail rent a listing claims.
- **Tenure** — `ESTYMD`; a 1954 branch is a long-validated location.
- **VACANCY / OPPORTUNITY SIGNAL (the best use):** a branch present in one snapshot and gone from the next = a CLOSURE. Bank branches are large, corner, high-visibility ground-floor space, so a closure means prime retail is coming available — often before it lists. Since `locations` is current-only and refreshes ~daily, **diffing daily snapshots yields closures/openings**; SOD gives the slower annual confirmation. This is the free, PUBLIC analogue of the "actives that remove" signal in the Crexi/LoopNet harvest.

**Fit with the commercial-comps design** ([[project_bkrea_commercial_comps]]): the four tiers all come from listing/paid platforms; FDIC rides alongside as retail corridor context + a closure trigger for the harvest ([[project_bkrea_change_tracking]]).
