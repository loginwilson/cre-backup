---
name: project-bkrea-overnight-review
description: "The 2026-07-27/28 overnight read-only review of the BKREA app — where its findings live, what survived, and the search method that actually works in this codebase"
metadata: 
  node_type: memory
  type: project
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-07-28T06:52:48.191Z
---

An overnight read-only review ran 2026-07-27 → 28 against `C:\dev\bkrea-territory-intelligence-app`
at HEAD `a8c9bb6`. Output is 27 numbered markdown docs plus `00-MORNING-BRIEF.md` and `QUEUE.md` in
`docs/review/overnight-2026-07-27/`. No code was changed.

**16 candidate findings, 10 dissolved under checking, 6 survived.** The survivors, ranked by money:

1. `territoryAcrisSales` can half-work invisibly on 216 condo lots (silent — looks like a complete answer)
2. `changeDetect` cannot distinguish a failed scanner from a quiet day; `perSource` is discarded at the only call site
3. `fetchDevelopment` never rejects, so three callers' retry handling is unreachable
4. **The DOF tax-lien ladder** — 298 territory parcels, 47 chronic, 71 reached Final Sale. The one *net-new revenue* signal: every existing lane answers "what is this worth", none answers "who is likely to sell". See [[project_bkrea_viability]].
5. `condoAddrKey` has no borough component and the resolver maps are first-writer-wins — **measured 184 collisions across 5 boroughs, but 0 on 40,000 Queens+Brooklyn addresses.** Latent, not live; Queens hyphen-stripping accidentally separates the two. Fix before any borough expansion.
6. Five FAR errors in `lib/zoningReference.ts` — already fixed and pushed. See [[reference_bkrea_zoning_sources]].

**Why:** the ten dissolutions all had one shape — a comment, a dial, or a dated decision was already
there and I had not read far enough. `lib/pullLog.ts` even states the governing doctrine outright
("an unstamped pull is indistinguishable from a market that simply did not move"), implemented at
four layers, and findings 1–3 are all the single layer that violates it.

**How to apply:** in this codebase, do NOT search for "what is missing" — that search produced a 60%
false-positive rate. Search for **"where is an existing, written rule not applied."** Read the file
header comments before forming any hypothesis; they are load-bearing documentation. And state every
finding as a falsifiable prediction a script can run — the findings that survived were the ones that
got executed, not reasoned. Related: [[feedback_bkrea_pull_package_monitor]],
[[project_bkrea_change_tracking]].
