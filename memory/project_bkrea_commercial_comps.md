---
name: project_bkrea_commercial_comps
description: BKREA Commercial comparables — LIVE (34 comps in Supabase, card+overlay+filter shipped); crawl of 41 new rate-bearing rows is what remains
metadata:
  node_type: memory
  type: project
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-27T23:08:04.761Z
---

**STATUS 2026-07-27: LIVE and essentially CLOSED.** `commercial_comps` holds **341 rows, 289
counted, review queue EMPTY, `FAIL 0`**. Card + filter + bucket all ship; actives monitored per
source via `activesMonitor`. (Earlier "34 comps" / "41 rows left to crawl" states are both
superseded.) Pipeline contract + per-bucket status: `docs/PIPELINE_RULES.md`; lane specifics:
`docs/harvest/commercial-pipeline.md`. **Comparables is fully closed** — the last defect (Marketproof
condo address parser) was fixed 2026-07-27; see [[project_bkrea_condo_sale_populate]] and
`docs/HANDOFF_2026-07-27.md`. Next block of work is bringing **Developments and Opportunities**
up to the comparables standard.

## The one rule that governs the pull
**THE TABLE IS A WORKLIST, NOT A DATA SOURCE.** Login caught me trying to bulk-normalize
table columns. Proof from the live baseline: row 0 publishes "$10,300 - $1,440,000" as a
$/SF/YR. And 38-58 11 St shows table Building SqFt 4,220 while the actual leased RSF is
2,425 — building sqft is NEVER the divisor. Only the **Lease Data TAB → Space History** is
the record (rate · leased RSF · dates · term · Source). The table decides only WHICH rows to
open, and is the diff surface for monitoring. Provenance (documented vs reported) exists ONLY
inside the record — that alone makes the per-listing walk structurally necessary.

⚠ Clicking the "Lease Data" chip opens the RECORD tab. Verify `drawerTab=lease`. The drawer
needs ~10s to render — reading at 4-5s produces false "not rendered". Nav presence, not page
length, is the render test. Never store screenshot coordinates across sessions and never
compute a scale from a DOM anchor — screenshot and read positions off it, every time.

## Card ⇄ overlay must survive the SAME gate
Login: *"theres an overlay on 36-35 36 street but no commercial section … this tells me we are
pulling from the wrong spot."* Data and key were both fine. The Commercial block sits inside
the rentals IIFE in `components/map/card/comparables.tsx`, which early-returns on
`!hasMf && byUse.size===0 && !storefronts` — so a parcel with a commercial comp but no
multifamily never reached it, while the overlay (no such gate) still painted. Fixed by adding
`commercialComps` to that bail. **Any new lane added inside that IIFE inherits its early
return.** Card, layer count and overlay all read `commercialFiltered` — one source, cannot drift.

## Architecture that works
`data/crexi-lic-records.json` (raw CAPTURE) → `scripts/deriveCrexiComps.ts` (DERIVATION) →
`commercial_comps`. The split means a rule change is a re-derive, not a re-crawl. `compId` is
deterministic, so re-crawling a covered row upserts rather than duplicates. `countsAsComp`
truth gate = rate + denominator + date + source. Evidence tiers: **documented** (rent
rolls/income statements) > **reported** (broker) > **active** (asking). Actives do NOT bucket
— "the bucket is the record".

## Monitoring
`scripts/crexiWorklistHarvest.js` — paste in console on the 4-neighbourhood query. Reads the
AG Grid DOM (no API exposed; Crexi runs bot detection so it scrolls the loaded grid rather
than issuing requests). **Head-capture is sufficient**: the query sorts rate-DESC and
rate-bearing rows are contiguous at 0–65, so a row GAINING a rate jumps into the head. The
harvester returns `contiguous:false` if that assumption ever breaks. Baseline:
`data/crexi-worklist-baseline.json` (1,377 records, 66 rate-bearing, 25 already crawled).
Diff logic in `lib/crexiWorklist.ts`. KEY: an active listing that DISAPPEARS is a probable
lease event — the harvest manufactures the historical series, so a missed day is permanently
lost data. Public lease-event signals (DOB fit-out, DCWP, SLA, CofO) are INVISIBLE PLUMBING
that raise a comp's confidence — Login: signals improve the number, they don't sit next to it.

Defect catalogue and per-shape rules: [[project_bkrea_crexi_derivation]]. Boundary/query:
`docs/harvest/crexi-query.md` — neighbourhoods, NOT the old hand-drawn polygon (polygons can't
be recreated reliably; Crexi's built-in geographies can). Ground lease is the one lane still
NOT POPULATED — Login hopes ACRIS, but the spike said no (all LIC-range ground rents show 0);
ACRIS is an ENCUMBRANCE signal only, and is ruled out for lease comps generally.

See [[project_bkrea_territory_intel]], [[project_bkrea_change_tracking]],
[[feedback_bkrea_pull_package_monitor]].
