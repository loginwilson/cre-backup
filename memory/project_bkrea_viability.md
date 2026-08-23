---
name: project_bkrea_viability
description: "BKREA opportunity viability — who structurally won't sell, and when the envelope/control isn't what it appears (TDR, easements)"
metadata: 
  node_type: memory
  type: project
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-26T16:49:51.519Z
---

**Viability = can this site actually be transacted and built, or is the buildable math academic?** (Login 2026-07-26.) Two separate questions:

**1. WHO WON'T SELL — reason by CATEGORY, never by collecting names.** Login: "you need to really think beyond the idea of me just giving the name — you need to understand who wouldn't be a seller." Single source of truth: `lib/opportunity.ts` → `UNLIKELY_CATEGORIES` + `unlikelySellerReason(record)` (returns WHY) with `isUnlikelySeller` as the boolean wrapper used by bucketing. Categories:
- **Rail** — incl. DEAD corporate names still on title (Pennsylvania RR, New York Central, Penn Central, Conrail, NY Connecting) + generic `railroad|railway|\brr\b` so successors aren't missed. MTA/LIRR/Metro-North/NYCTA/Amtrak/CSX.
- **Public authorities** — the word "authority" is itself the tell (TBTA, Battery Park City, RIOC, SCA); Port Authority separately.
- **State** (Dormitory Authority, ESD/UDC, OGS, SUNY/CUNY), **Federal** (GSA, USPS, VA, Army Corps, NPS), **utilities/infrastructure** (Con Ed, National Grid, Brooklyn Union, NY Telephone, Empire City Subway, pipelines), **cemeteries** (perpetual care).
- **DELIBERATELY EXCLUDED: religious owners** — churches/dioceses/congregations are among the most ACTIVE sellers of development rights in NYC; flagging them would hide real opportunities. Same logic for hospitals/universities.
- **Short tokens MUST be `\b`-anchored** — probed live, `%mta%` also matches "KABIR, MOMTAZ", "FAMTAN, L.L.C.", "EMTAK MANAGMENT LLC". PLUTO `OwnerType` is unreliable except `C`/`M` (its `O` holds private individuals); owner NAME is the real signal.
- Effect when broadened: LIC Opportunities 612 → 608 (caught 4 real non-viable owners the old list missed).
- **Don't duplicate this check on the card** — Login flagged a redundant red banner above the box vs the yellow verdict line below. The verdict line is the one.

**2. THE ENVELOPE / CONTROL MAY NOT BE WHAT IT APPEARS** — two advisory caveats now lead the Opportunity box (`components/map/PropertyCard.tsx`):
- **Air rights (TDR/ZLDA):** ACRIS records THAT development rights moved (a `DEVR` instrument, detected in `lib/acris.ts` airRights.transfers) but NEVER how much SF. The envelope math (`lib/development.ts` `netTdr = tdrAcquired − tdrDisposed`) only subtracts TDR a broker MANUALLY entered — so a lot that sold its air rights still shows full remaining SF. The flag asks for the ZLDA rather than inventing a number.
- **Encumbered control:** a PRIVATE owner can be unable to deliver the site. Canonical example (Login, 2 Street): a permanent LIRR access + utility easement — continuous access to operate/repair/replace LIRR electrical & communication facilities, bars alterations affecting them without approval, runs with the land indefinitely, terminates only if LIRR formally determines it's no longer required. The caveat prints the TERMS when we have them (broker write-up) rather than just ACRIS's bare "Present · N" count, because the terms decide whether the scenarios hold.

**Still open:** ZLDA / merged zoning lots where lots are separate on paper but the air rights sit on one — needs the actual zoning-lot merger picture, not just per-lot data. See [[reference_bkrea_zoning_sources]], [[project_bkrea_opportunity_card]].
