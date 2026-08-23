---
name: project-bkrea-territory-intel
description: "BKREA Territory Intelligence — the ACTIVE app (Next.js/Vercel map product). Location, workflow, comps state."
metadata: 
  node_type: memory
  type: project
  originSessionId: afb4a6ee-e4cc-4f55-9c4f-36b930a50c92
  modified: 2026-07-22T16:34:46.088Z
---

**This is the active project the operator means by "my app" / "the app we've been building."**
The Queens CRE Python tool ([[project-queens-cre]], `Downloads/queens-cre-intelligence`) is an
EARLIER PROTOTYPE — do NOT go there for current work.

## Location & stack
- Path: `C:\Users\smile\OneDrive\Desktop\Claude\Sessions\bkrea-territory-intelligence-app`
- Next.js / TypeScript map app, deploys to **Vercel + Firebase** via GitHub Actions on push.
- Runs locally on **localhost:3000** (dev server, not always up). Operator also has a live Vercel deploy.
- Sibling folders `bkrea-territory-intelligence` and `-autonomous-benchmark` are older/benchmark copies — the `-app` folder is the live one (most recent source edits).

## How to work on it (from CLAUDE.md — authoritative)
- **The repo IS the memory.** Two Claude accounts alternate via git push/pull; chat history is not the source of truth.
- Start every session: read `docs/CURRENT_HANDOFF.md`, then `docs/PRODUCT.md`, summarize state, then WAIT for the operator's instruction — **no code until greenlit.**
- Commits MUST use committer email `284472887+loginwilson@users.noreply.github.com` (Vercel Hobby deploy gate — any other email is blocked).

## Product
Broker-facing territory intelligence: live map of parcels/ownership/opportunity. Buckets:
**Developments · Opportunities · Comparables** (+ QRS/rezoning, study-area signals). Standing operator
bar: "complex information packaged valuably and simply — the worst thing is to overcomplicate." Every
surface one-sentence-explainable by an average broker; complexity behind expanders/tooltips.

## Comparables — state as of 2026-07-22
Four lanes: **Sales · Condos · Rentals · Commercial (leases)**.
- **Sales lane** = fully automated from DOF (only automated lane); $/BSF under sale-date zoning, multi-lot
  deed detection. Core: `lib/salesLedger.ts`, `lib/comps.ts`, `lib/condoSellouts.ts`, `lib/rentPool.ts`,
  `components/map/card/comparables.tsx`.
- **Condos/Rentals** = import/sweep-dependent (Marketproof sellouts, StreetEasy rents), empty until fed.
- **Commercial-leases lane = NOT BUILT YET.** Currently ACRIS recorded leases as trigger/encumbrance
  signals (~5/yr borough-wide), NOT a rent-comp set. Needs a T3 rent import (Crexi paste / rent roll).
  This is "how we derive commercial comps" — the pending build.
- Governing rule throughout: **never fabricate** — empty-until-imported, no $/SF without real SF, min-comps
  floors (≥5 closed), Derived rents always badged/gated.
- `docs/audits/COMPARABLES.md`: Round 1 audit (Opus) COMPLETE; **Fable 5 challenge pending** = UI/UX
  legibility tune-up + verify the `zoningReference` FAR table (drives every $/BSF, isDevGrade, asset rescue).

## Open threads
- Build commercial-leases rent lane (T3 import).
- Fable 5 audit challenge (UI/UX + FAR-table verification).
- Nightly `territory-sweep.yml` no-ops without SWEEP_EMAIL/SWEEP_PASSWORD/SOCRATA_APP_TOKEN secrets.
