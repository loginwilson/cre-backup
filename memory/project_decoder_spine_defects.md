---
name: project_decoder_spine_defects
description: "The parcel spine has two measured defects that break parcel-matching — DTM flags are relationships not identities (19,419 lots), and condo BILLING lots are in neither DTM layer (11,132 parcels, 412,507 apartments)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 952e3d80-2448-4fe2-b34d-a103d3caedd4
  modified: 2026-08-06T12:52:43.079Z
---

The shared parcel spine (`decoder/spine.py`, 1,164,820 parcels, built from the
DOF Digital Tax Map) was found wrong in two ways on 2026-08-06 while reconciling
StreetEasy rent ledgers. Both are written up in
`Downloads/Source Folder (Real Estate Data)/Decoder Prompt/decoder/SPINE_DEFECTS.md`.
`streeteasy.py` carries a corrected overlay; `spine.py` itself is NOT yet fixed.

**1. `CONDO_FLAG` / `REUC_FLAG` / `AIR_LOT_FLAG` / `SUB_LOT_FLAG` mean "this tax
lot HAS a related lot of that kind", not "this lot IS that kind."** 445 lots
carry two or more at once — `4000170028` carries REUC + AIR + EASEMENT and is a
372-unit apartment building. Sven (958 units) reads as a utility lot. Affects
19,419 lots; anything gating on `kind == "ground"` silently drops them.

**2. Condominium BILLING lots (`lot >= 7501`) are absent from the spine
entirely.** The DTM keeps the pre-condo BASE lot and flags it; PLUTO drops the
base lot and keeps the BILLING lot; the condo-unit layer's `condo_base_bbl`
points at the base lot (0 of 307,436 rows reference a 75xx BBL). So the billing
lot is in neither DTM layer: 11,132 of 11,141 missing, 412,507 residential units.
These are the new towers — Skyline Tower, Gotham Point, 5Pointz, Hayden.

**Why:** the spine is the join every decoder uses, so a parcel missing from it is
a parcel no decoder ever visits — and a wrong `kind` reads as a misplaced fact
rather than a bad spine.

**How to apply:** never gate on spine `kind == "ground"`; treat every
`Tax_Lot_View` row as a tax lot and the flags as related-lot markers. Add PLUTO
`lot >= 7501` as `condo_billing` parcels before matching anything to a parcel.
Relates to [[project_bkrea_lot_lineage]] and [[feedback_bkrea_scale_failure]].
