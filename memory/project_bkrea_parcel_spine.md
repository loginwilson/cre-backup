---
name: project_bkrea_parcel_spine
description: "THE parcel spine every decoder walks — 1,164,820 parcels from DOF's Digital Tax Map (not PLUTO), 306,443 condo lineage edges; ⚠ TWO MEASURED DEFECTS (flag semantics + missing condo billing lots) and merger/subdivision lineage still missing"
metadata: 
  node_type: memory
  type: project
  originSessionId: 176544e8-656c-4540-a15c-f710beced15e
  modified: 2026-08-06T12:57:59.481Z
---

Built 2026-08-06. `decoder/spine.py` → `spine/spine.jsonl`. Every decoder (ACRIS,
DOB, BSA/LPC/DCP, DOS, StreetEasy) joins on this, so a parcel missing here is a
parcel no decoder ever visits.

**1,164,820 parcels**, fully reconciled from 1,165,604 rows read (73 duplicate
tax lots + 708 duplicate condo units = multi-polygon parcels; **3 BBL collisions**
that are both a tax lot AND a condo unit — kept as tax lot with a flag so
read-order does not decide).

**✅ BOTH DEFECTS FIXED AND REBUILT 2026-08-06** (found by the StreetEasy decoder,
verified independently, corrected in `spine.py`). See [[project_decoder_spine_defects]]
and `decoder/SPINE_DEFECTS.md` for the original findings.

* **flags are RELATIONSHIPS, not identities.** `lot_flags()` now carries
  `has_condo / has_reuc / has_air / has_sub / has_easement` ALONGSIDE kind, never
  as kind. Proof it had to be: **443 lots carry 2+ mutually exclusive flags** —
  a lot cannot BE a utility lot and BE an air lot. Verified: BBL 4004030003 is
  **Sven**, 958 units, now `kind=tax_lot has_reuc=True`.
* **condo BILLING lots added from PLUTO** (`64uk-42ks`, `lot>=7501`) — 11,141
  pulled, **11,132 new parcels carrying 412,507 residential units**. Verified
  present: Gotham Point 1,132 · 5Pointz 1,122 · Hayden 974 · Skyline Tower 802.

**CURRENT BUILD — 1,175,952 parcels**, reconciled from 1,176,745 rows read.
kind: tax_lot 858,095 · condo_unit 306,725 · condo_billing 11,132.
relationship flags: has_condo 22,400 · has_reuc 8,298 · has_air 242 · has_sub 70
· has_easement 37,594 · **443 multi-flagged**.

⚠ **A WITHDRAWN CLAIM, kept visible on purpose.** The old reason-to-prefer-DTM
"BBL 1022551031 is a REUC not a condo unit" rested on the identity misreading and
**does not stand**. It is left in the `spine.py` docstring marked withdrawn,
because a disproven belief that vanishes silently gets re-adopted later.

**⚠ USE DOF's DIGITAL TAX MAP, NOT PLUTO — but not alone.** The DTM **is** the
legal tax lot and it carries **307,436 condominium UNIT lots** PLUTO omits. But
PLUTO holds the condo BILLING lot the DTM omits, so neither layer is the whole
parcel universe and a spine built from one of them has a hole shaped like the
other. (The old third reason here — "BBL 1022551031 is a REUC, not a condo unit"
— rested on the flag misreading and does not stand.)

**Sources:** ArcGIS `Tax_Lot_View` on `services6.arcgis.com/yG5s3afENB5iO9fj`
(858,168; Socrata `smk3-tmxj` is **403**) + Socrata `eguu-7ie3` condo units
(307,436) + `p8u6-a6it` condo billing (12,196).

**Staten Island IS included** — 125,348 lots. Only ACRIS *recordings* exclude SI
(deeds live with the Richmond County Clerk); the tax map covers all five boroughs.

**LINEAGE IS THE ORGANISING PRINCIPLE.** `walk(bbl)` returns the whole family —
ancestors, descendants, siblings — so a decoder handed one lot never reads a
fragment of a history as the whole. Verified: one condo unit walks to all 53
parcels of its condominium.

**⚠ THE GAP — merger/subdivision lineage is NOT wired.** Only condo edges exist
(306,443, free from `condo_base_bbl`). The pilot parcels 1008000053 and
1014460001 walk to themselves alone even though 1014460001 has a known DOF lot
merger (trans 588545, CRFN 2024000254255). Next spine job: add DOF alteration-book
edges. Until then the spine is complete on PARCELS and incomplete on HISTORY.

Related: [[project_bkrea_lot_lineage]] (retired BBLs drop out of gate-keyed
pulls), [[project_acris_document_inventory]], [[project_acris_bulk_acquisition]].
Launch kit for parallel decoder chats: `decoder/KICKOFF_PROMPTS.md`,
`decoder/DECODER_CHATS.md`, schema in `decoder/LEDGER_SCHEMA.md`.
