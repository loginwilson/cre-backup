---
name: project_bkrea_sandbox_env
description: "BKREA local sandbox needs NEXT_PUBLIC_SOCRATA_APP_TOKEN in .env.local (gitignored) to match prod; without it comps/data features throttle and look like a \"different/older version\""
metadata: 
  node_type: memory
  type: project
  originSessionId: 9e7f9a5f-4f20-4aac-9627-cf89a65ff316
  modified: 2026-07-27T17:11:04.814Z
---

For the BKREA Territory Intelligence app ([[project_bkrea_territory_intel]]), `.env.local` is
**gitignored**, so a fresh clone or reset local sandbox silently differs from production even at the
SAME commit. The code reads six env vars; the two that production sets but a bare `.env.local` omits:

- **`NEXT_PUBLIC_SOCRATA_APP_TOKEN`** — no fallback in code. Missing → every territory-scale NYC
  Open Data query (MapPLUTO/sales/DOB/comparables) throttles as anonymous (429) and blanks out, so
  the sandbox looks like it's "missing features / an older version." Prod value (public, ships in the
  deployed client bundle; it's a rate-limit id, not a secret): `XBMcBRBwtwiD4elm0XS5iwLRZ`. Added to
  `.env.local` 2026-07-22.
- **`NEXT_PUBLIC_PARCELS_PMTILES`** — HAS a hardcoded fallback in `components/map/MapWorkspace.tsx`
  (`https://pub-09112d9efb394be99369c444ce4e9766.r2.dev/parcels.pmtiles`), and prod uses that SAME
  URL, so parcels render fine without it. No action needed.

**Vercel (production) env — CONFIRMED via dashboard 2026-07-22, only 3 vars:**
`NEXT_PUBLIC_SUPABASE_URL` (Jul 3), `NEXT_PUBLIC_SUPABASE_ANON_KEY` (Jul 3), and
`NEXT_PUBLIC_SOCRATA_APP_TOKEN` (**Added Jul 9**). Production does NOT have
`SUPABASE_SERVICE_ROLE_KEY` or `HARVEST_OWNER_ID` — those are LOCAL-ONLY (harvest script). This
proves the service-role "secret" is NOT what loads app data (data loads via the anon key against
Supabase cloud; service role is harvest-ingest only). The **Jul 9** timestamp is the root cause:
local `.env.local` was set up ~Jul 3 and never got the Jul-9 Socrata addition, so from Jul 9 on,
prod had working data and the sandbox was throttled → looked like a "newer version."

**Why:** the operator repeatedly saw the localhost sandbox as "a different/outdated version" because
data-driven features were empty — root cause was env config, not code (code = origin/main = prod
commit; same Supabase project `ghjkjxfxtpqhxxkxbdrp`). **How to apply:** if the sandbox looks
feature-poor vs the live app at bkrea-territory-intelligence.vercel.app, FIRST diff `.env.local`
against what the code reads (`grep process.env.NEXT_PUBLIC_*`) and against prod's public bundle —
before suspecting the code is out of date. `NEXT_PUBLIC_*` changes require a dev-server restart.

**TWO ACCOUNTS — RLS gotcha (found 2026-07-22).** The Supabase project has two auth users:
`loginwilson88@gmail.com` (id `b5351809…`) owns ALL real data — 3 territories incl. "Long Island
City" + "OneLIC", 378 assignments, 8,368 property_records — and has an **email/password** identity
(no Google needed). `territory-test@bkrea.com` (id `bad0767d…`) is a near-empty TEST account (one
"Hunters Point" territory, 0 assignments). Because of row-level security each login only sees its own
data, so signing into the sandbox as the test account (or any account other than loginwilson88) shows
a nearly EMPTY map — which reads as "outdated / nothing new / missing features" but is just the wrong
login. **Always sign into the sandbox as `loginwilson88@gmail.com` with email+password**, then
activate "Long Island City" or "OneLIC". HARVEST_OWNER_ID in .env.local = `b5351809…` (this account).

**⚠ DECIDED 2026-07-27: DEVELOP ON BARE `http://localhost:3000`, NOT `bkrea-sandbox.localhost:3000`.**
They are the SAME dev server on the SAME port — the sandbox name is only a `*.localhost` loopback
alias, so there is NO separate instance, database or config, and nothing to gain. There IS something
to lose: **Marketproof allow-lists the EXACT origin**, so the subdomain gets an empty array back and
the app falls back to cached listings — correct in production, silent failure in dev (a
normal-looking map, and a monitor reporting zero changes that are really zero refreshes). Measured:
same territory returned 0 listings on the subdomain and 12,247 on bare localhost. The harvest sink
`http://localhost:3000/api/harvest` also assumes bare localhost. `.claude/launch.json` now pins
`url` to `http://localhost:3000`. See `docs/PIPELINE_RULES.md`.

Google OAuth won't redirect to the `bkrea-sandbox` host unless whitelisted in Supabase → Auth → URL
Config; use email/password if you do use it.

**RECURRING dev-server STALE-SWC cache (hit 3× on 2026-07-24).** After editing `comparables.tsx`
(the huge card file), the Next dev server's HMR often throws a PHANTOM `Unexpected token \`div\`.
Expected jsx identifier` at an UNCHANGED line (e.g. 843, the `return (<div className="text-xs">`),
sometimes 500-ing the whole page. It is NOT a real syntax error: `npx tsc --noEmit` returns EXIT 0
and `npm run build` passes. It's a stale SWC/HMR cache. **Fix = restart the dev server clean:**
`npx kill-port 3000` → `rm -rf .next` → `npm run dev` (background), wait for "Ready", reload the
browser. Don't chase the phantom line number. Always trust `tsc`/`next build` over the dev console
for this file. **PREVENTION added 2026-07-24 (commit 2446eb2):** `next.config.mjs` sets
`config.cache = { type: "memory" }` in DEV ONLY (guarded by `dev`; prod build untouched) so no stale
on-disk cache can form. The clean-restart above is now the FALLBACK. If it still recurs often even
with memory cache, escalate to Turbopack (`next dev --turbo`) — different engine, bypasses the webpack
cache entirely.
