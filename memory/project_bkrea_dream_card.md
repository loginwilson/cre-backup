---
name: bkrea-dream-card
description: "THE MANDATE — restructure the card to the dream populate (Property Info + 3 lenses, contacts/notes absorbed), systemize on a few parcels, then scale to the 7,030-lot territory as proof of concept"
metadata: 
  node_type: memory
  type: project
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-07-30T22:31:53.320Z
---

**BACKUP (2026-07-30):** both lines live on GitHub `loginwilson/bkrea-territory-intelligence` — `main` (the stable app) and `rebuild` (the mirror). The mirror's remotes: `origin`=GitHub, `local`=the main app folder. So from the mirror, plain `git push` backs up `rebuild`; merging into main later is a normal PR/merge. ⚠ The main repo sat **220 commits unpushed** for a whole day of engine work before this — push at the end of every working session, not just at milestones.

**⭐ THE WORKING REPO IS NOW `C:\dev\bkrea-v2`, branch `rebuild`, port 3001 (operator decision 2026-07-30).** It is no longer "the mirror" — it is the live line from today onward, and today's commits land there. `C:\dev\bkrea-territory-intelligence-app` (port 3000, `main`) is frozen as the reference/fallback: read it for how something used to work, don't build in it. Default to the v2 path for every file read, edit, script run, and dev server.

**THE MIRROR — how it was made (2026-07-30 eve):** the rebuild lives at **`C:\dev\bkrea-v2`, branch `rebuild`** (cloned from the main repo at checkpoint commit `21281b0` — the day's full engine + card evolution + 438-doc harvest cache all committed). Mirror runs on **port 3001** (`.claude/launch.json`), has its own `.env.local`, `.bulk/`, `data/developments-*.ndjson`, `.pluto-archive/` copies. Original repo at `C:\dev\bkrea-territory-intelligence-app` stays untouched as the reference/fallback. In the mirror: strip heatmap + verified functionality, keep filters as interface shells, retire legacy data-JSON feeds, design ONE clean read model (parcel_card over developments+snapshot+debt+comps), preserve broker-entered data (visits/notes/overrides/names) by BBL before clearing, then pilot-5 → 7,030. **Rebuild forward, never roll back — the engine commits are the asset.**

**The mandate (operator 2026-07-30):** all sources are proven (DOB NOW, BIS, ACRIS, PLUTO 02a–26v1, CofO, SofO, permits) — now restructure the card to the dream populate. Holes are ACCEPTED and rendered honestly. **Systemize the per-parcel populate on a FEW parcels first, then scale to the 7,030-lot LIC territory as proof of concept.**

**Card spine:** *identity → what's happening → what it's worth → what to do:* **Property Information** (always-visible parcel identity) → **Development** → **Comparable** → **Opportunity** (reconstruction queued — debt-positioning lens). Contacts and Notes sections are REMOVED as standalone; contacts live inside their lens (Development's field sets exist; ownership with Property Info/Opportunity), notes become per-section.

**Property Information fields** (all PLUTO/MapPLUTO-fillable citywide except noted): name (⭐ ALREADY POPULATED for the LIC territory from the earlier Marketproof/research pass — fills now there; citywide stays empty-until-matched), address, BBL/boro/block/lot, neighborhood, zonedist1-4 + overlays + special districts, owner (+ real-company when research pinged), yearbuilt/yearalter, lotarea, frontage×depth, lot type (PLUTO `lottype` = corner/inside/through — free, keep), floor area **with use distribution** (resarea/comarea/officearea/retailarea/garage/storage/factory/other — free citywide), FAR as the movement pair (builtfar vs max of resid/comm/facilfar), stories, units (PLUTO gives res/total only; per-use unit mix deepens via SofO harvest — honest slot).

**Populate systemization:** one per-parcel assembly = PLUTO identity + `developments` row (stage/summary/splits/financing) + doc harvest (PW1/SofO) + project-debt chain + comps lanes. Pilot set: pick ~5 LIC parcels of different characters (delivered condo=Vesta ✓ done, stalled construction, pre-development, quiet no-dev rowhouse, office/commercial) → verify each card face → then the 7,030 run. Existing machinery: devBulk/dailyPull, harvestDocs, projectDebt (dev-lot via lineage; v2 = borrower-entity join), liveDevelopment fetch. See [[bkrea-dev-card-grammar]], [[bkrea-debt-throughline]], [[bkrea-devbulk]].
