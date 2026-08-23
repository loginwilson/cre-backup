---
name: project-queens-cre
description: "Queens CRE Intelligence System — location, status, workflow, and architecture"
metadata: 
  node_type: memory
  type: project
  originSessionId: b9d84e3b-f9e4-4585-b820-fcc3ebc2be3b
---

Project is at: `C:\Users\smile\Downloads\queens-cre-intelligence`

**Why:** CRE broker focused on development sites in Long Island City and Queens. Tool pulls public NYC data, scores development prospects, generates pre-call briefs, BOVs, and buyer lists.

**How to apply:** Always cd to this path when working on the project. It is a git repo with Python 3.10+. Only dependency beyond stdlib is `requests`.

## Current state (as of 2026-06-01)
- All 5 phases built + strengthening additions committed
- Database: 324,559 Queens lots loaded, 30,003 in LIC area
- Scheduled tasks registered: QueensCRE-Daily (Mon–Fri 4am), QueensCRE-Weekly (Sun 3am)
- No `.env` file — Socrata app token not set (system runs without it at lower rate limits)

## Workflow — what runs and when
- **Mon–Fri 4am**: `run_daily.py` — 6-step pipeline (API check → daily brief → research all 45 → BOV → buyer match → market log). Done by ~6:30–7am.
- **Sunday 3am**: `run_weekly.py` — full PLUTO refresh (324k lots) + Stage 2 enrichment of top 500.

## Output by 9am each morning
- `output/briefs/daily_brief_YYYY-MM-DD.txt` — Section A (top 25 commercial/dev) + Section B (top 25 residential-upside), ★★ = on both lists
- `output/briefs/research_summary_YYYY-MM-DD.txt` — one-pager: all 45 properties, signals, contact, angle
- `output/briefs/precall_<address>_YYYY-MM-DD.txt` — full pre-call brief per property
- `output/bov/bov_<address>_YYYY-MM-DD.txt` — comp-backed BOV
- `output/buyers/buyers_<address>_YYYY-MM-DD.txt` — ranked buyer list
- `output/market_log/market_log_YYYY-MM-DD.md` — Markdown intelligence pub

## Dual-track brief system
- **Section A**: top 25 by score, any zoning — commercial/industrial dev play
- **Section B**: top 25 where residential is as-of-right (M/R mixed, R, C zones) — broader buyer pool (condo/rental devs). Ranked by score + buildable SF.
- `residential_zoning_bonus` in config.SCORING gives these lots extra points.
- ★★ flag = property appears on BOTH lists → highest priority (motivated seller + residential buyer pool)

## Key files
- `main.py` — interactive CLI (9 options)
- `run_daily.py` — daily automation orchestrator
- `run_weekly.py` — weekly PLUTO + enrichment
- `market_log.py` — daily Markdown intelligence pub
- `schedule_pipeline.ps1` — registers both Task Scheduler tasks (run once as Admin)
- `config.py` — all settings, scoring weights, dataset IDs
- `src/scoring.py` — scoring model + `residential_allowed()`
- `src/database.py` — SQLite layer including cumulative buyers table
- `src/skiptrace.py` — LLC → callable person (HPD + DOB + NY DOS)
- `src/motivation.py` — tax liens + aged mortgage signals

## Open roadmap items (from STRENGTHENING.md)
1. Replace LIC boundary ZIP approximation with real DCP GeoJSON (point-in-polygon)
2. ZAP active rezoning applications feed
3. DOF assessment roll for true market value
4. Caching layer (30-day PLUTO, 7-day ACRIS TTL)
5. Pre-foreclosure / lis pendens signals
