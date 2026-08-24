---
name: project-decoder-source-roadmap
description: "BANKED ROADMAP (login 2026-08-24): linear source progression after acris+richmond hit 100% — DOB → DOF → BSA/DCP → HPD → DEP/ECB/OATH → DOS; DTM = lineage source not overlay; knowledge bases (ZR, tax code) = a sibling decoded RULE BASE joined at derivation"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T15:29:36.109Z
---

**THE SOURCE ROADMAP (login: "yes bank it as the roadmap").** Every source =
the same five artifacts onto the BBL parcel spine ([[project-decoder-source-onboarding]],
lane-first). Order after acris+richmond reach 100% ready:

1. **DOB** — change layer. Rows shape-1 Socrata (BIS ic3t-wcy2 ~2.72M +
   DOB NOW w9ak-ipjd ~950k); the firm's view = NB 199,888 · DM 80,346 ·
   A1 220,066 + NOW's New Building 54,977 · Full Demo 7,541 · ALT-CO
   49,708+15,927 ≈ **628k jobs (83% cut)** — but MIRROR ALL ROWS, select at
   product layer. A1 enlargement flags are Y-or-blank (blank ≠ no); unit-
   count delta = conversion detector (34k). Key = in-row block/lot → BBL
   (NOT BIN: million-BIN placeholders on NBs, BIN churn at demo/rebuild —
   BIN = lineage attribute within BBL). Edge = crfn+1-style walk on
   sequential job numbers (Socrata lags ~a day = reconciliation ledger).
   Velocity from in-row lifecycle dates + permit renewals + CO events —
   never folder pulls; rows ARE the folder manifest (one row per job doc).
   Docs selective/last (ZD1 envelope drawings); Akamai re-probe when there.
   Pre-2000: login recalls a THIRD electronic system to ~1980 — likely the
   BIS MAINFRAME itself (late-80s; BISweb is its skin, Socrata undersells
   its depth) — probe actual job-number reach at mapping time; pre-1980s =
   microfilm, and the CO ARCHIVE (1920s+) is the authoritative old record —
   old filings add ~nothing over COs.
2. **DOF** — value layer (and ACRIS's parent org). Assessment roll,
   abatements/exemptions WITH EXPIRY (421-a/J-51 expiry = top sell signal),
   rolling sales, condo billing-lot attribution (closes the spine defect),
   tax-bill PDFs selective. **DTM's db role = the spine's LINEAGE SOURCE,
   not an overlay**: diff each release → merger/subdivision/apportionment
   events + retired BBLs (the invisible-dropout trap) + adjacency geometry
   for assemblage math; GIS overlay is a product view on top.
3. **BSA/DCP (ZAP)** — entitlement layer (login: "track applications and
   statuses"): variances, special permits, ULURP/rezonings — application-
   shaped like DOB, same velocity treatment. bsa.py exists.
4. **HPD** — registrations (owner/agent contacts → party sheets) +
   violations (distress).
5. **DEP ACP-5 (earliest demo tell) · ECB/OATH (distress)** — enrichers.
6. **DOS** — identity layer; keys to PARTIES not BBL (dos.py prototyped).

**KNOWLEDGE BASES (login's question answered):** governing rules (zoning
resolution, tax code, building code) are A SOURCE CLASS run through the
SAME five phases — but they decode into a **RULE BASE** (clause →
condition → consequence, cited to section), not events on parcels. zr
machinery exists (zr_index.py, zr_feed.py, split_zones.py; zr.planning.nyc.gov
is the fetchable authority — [[reference-bkrea-zoning-sources]]).
**DERIVATION IS THE JOIN**: decoded facts × rule base → today's meaning
("envelope +37k SF *under ZR 23-153*"); every derivation cites BOTH the
fact (document_id+page) AND the rule (section). Facts sync per-parcel
daily; rules change rarely but GLOBALLY — a ZR amendment re-derives
everywhere (why derivation is the living layer,
[[project-acris-resolution-model]]). Products consume derivations; the
rule base is what makes them citable. Rule base gets its own slow sync
lane (amendment tracking).

Endgame: spine = join surface · ACRIS = rights · DOB = change · DOF =
value · BSA/DCP = entitlement · HPD/ECB = condition · DOS = identity ·
rule bases = meaning. Related: [[project-acris-consolidated-lane]],
[[project-bkrea-parcel-spine]], [[project-decoder-philosophy]]
