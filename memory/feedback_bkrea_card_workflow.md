---
name: feedback_bkrea_card_workflow
description: "How Login and I iterate on BKREA property-card designs — build-verify-react loop, dev-server gotchas"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-24T19:03:34.653Z
---

How the BKREA card-design work goes (learned 2026-07-24 across a long session redoing Sale/Condo/Rental/Commercial/Development/Opportunity cards).

**Build-verify-react loop.** Login sends a hand-drawn mockup (green boxes on blue = his sketch style, NOT the literal theme — always confirm theme). For a genuinely open design question ("find an aesthetic way"), render a `show_widget` mockup so he can SEE options before I build in-app — it saved cycles on the Opportunity buildout-bar. Otherwise: implement in `components/map/PropertyCard.tsx` or `comparables.tsx`, verify live in the sandbox with a screenshot, let Login react, iterate. He decides fast and changes his mind mid-build — that's expected; don't over-ask, show him real renders.

**Why:** he's a non-developer CRE broker who thinks visually; a screenshot of the real card beats a description. **How to apply:** keep edits tsc-clean, verify each in-browser, commit per accepted change (owner git identity — see [[project_bkrea_territory_intel]]).

**DEV-SERVER GOTCHAS (cost real time):**
1. **NEVER run `npm run build` while `npm run dev` is running** — the production build overwrites the shared `.next` dir and the running dev server 404s its own chunks (looks like a crash / splash screen). Verify with `tsc` only during iteration; let Vercel build on push, OR stop the dev server before a local build.
2. **Stale SWC cache phantom** — mitigated by the in-memory webpack cache in `next.config.mjs` (see [[project_bkrea_sandbox_env]]); if it still recurs, restart clean (`kill-port 3000` → `rm -rf .next` → `npm run dev`).
3. After restarting the dev server, tell Login to **hard-refresh** (Ctrl+Shift+R) — his browser holds the old bundle.

**Sequencing (Login 2026-07-24):** finish CARD DESIGNS → then COMMERCIAL COMPARABLES ([[project_bkrea_commercial_comps]]). No auditing / air-rights ([[project_bkrea_opportunity_card]]) until then.
