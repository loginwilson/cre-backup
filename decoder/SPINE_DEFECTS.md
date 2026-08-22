# Two spine defects found by the STREETEASY decoder, 2026-08-06

Found while reconciling 1,212 rent ledgers against the spine. **Both are in the
spine, not in the ledgers**, so they affect every decoder, not just this one.
Written here rather than patched into `spine.py` directly because other chats
may be mid-run against it — fold them in deliberately.

The STREETEASY decoder carries its own corrected overlay (`streeteasy.py`,
`spine_overlay()`), so it is not blocked waiting for this.

---

## DEFECT 1 — the DTM flags are RELATIONSHIPS, not identities

`spine.lot_kind()` reads `CONDO_FLAG` / `REUC_FLAG` / `AIR_LOT_FLAG` /
`SUB_LOT_FLAG` as *this lot IS that kind*. They mean *this tax lot HAS a related
lot of that kind*.

**The proof is internal — no outside source needed.** 445 lots carry two or more
of these flags at once, and 12 carry three:

| flags present together | lots |
|---|---|
| CONDO + REUC | 335 |
| REUC + AIR | 39 |
| CONDO + AIR | 32 |
| CONDO + SUB | 13 |
| REUC + SUB | 8 |
| CONDO + REUC + AIR | 6 |
| CONDO + REUC + SUB | 6 |

A lot cannot simultaneously *be* a utility lot and *be* an air lot. Under the
relationship reading every one of these is ordinary.

**Confirmed against PLUTO.** Sampling 200 of the 7,952 lots the spine calls
`reuc`: 199 exist in PLUTO as ordinary tax lots, 77 of them with residential
units, building classes O (66), C (36), D (31). Named examples, all flagged
`REUC_FLAG='R'` by the DTM:

| BBL | PLUTO | what it is |
|---|---|---|
| 4004030003 | D6, **958 units**, 64 fl | **Sven** — one of the largest rental towers in LIC |
| 4002640001 | D6, 671 units, 45 fl | 28-02 Jackson Avenue |
| 4000170028 | D8, 372 units, 32 fl | 2-01 50th Avenue — *also* flagged AIR and EASEMENT |

`4000170028` is the single clearest case: `REUC_FLAG='R'`, `AIR_LOT_FLAG='A'` and
`EASEMENT_FLAG='E'` on one row, and it is a 372-unit apartment building.

**Blast radius:** ~19,400 of 858,168 tax lots (2.3%) carry a wrong `kind`.
Anything gating on `kind == "ground"` silently discards them. In this decoder it
produced 33 false "misplaced ledger" verdicts over 3,929 real rental events —
2.7% of the sample, matching the citywide rate.

⚠ `spine.py`'s own docstring cites this misreading as evidence for choosing the
DTM over PLUTO: *"BBL 1022551031 is lot 1031 and is a REUC, not a condo unit."*
That claim rests on the identity reading and should be re-checked with the rest.

**The fix:** every row in `Tax_Lot_View` IS a tax lot. Carry the flags as
`has_condo` / `has_reuc` / `has_air` / `has_sub` / `has_easement` alongside the
kind, never as the kind.

---

## DEFECT 2 — condominium BILLING lots are absent from the spine entirely

`Tax_Lot_View` returns **nothing** for BBLs in the `75xx` lot range. Five queried
directly, all absent from the DTM, all present in PLUTO with hundreds of
apartments each:

| BBL | PLUTO | building |
|---|---|---|
| 4000067503 | RM, 1,132 units, 33 fl | Gotham Point |
| 4000867501 | RM, 1,122 units, 48 fl | 5Pointz LIC |
| 4004337501 | RM, 974 units, 50 fl | Hayden |
| 4004377502 | RM, **802 units, 67 fl** | Skyline Tower |
| 4002397501 | RM, 467 units, 44 fl | AltaLIC |

**Measured citywide:** PLUTO holds 11,141 parcels with `lot >= 7501`. **11,132 of
them (99.9%) are absent from the spine**, and they carry **412,507 residential
units**.

**Why it happens — the two authorities keep opposite halves of a condo:**

* the **DTM** keeps the pre-condo BASE lot and sets `CONDO_FLAG='C'` on it
  (11,268 such lots — nearly the same count as the 11,141 billing lots)
* **PLUTO** drops that base lot and keeps the BILLING lot instead
* the DTM condo-unit layer's `condo_base_bbl` points at the **base** lot, never
  at the billing lot — verified: **0 of 307,436** unit rows reference a `75xx`
  BBL

So the billing lot is a real, separately-taxed parcel that appears in *neither*
DTM layer, and nothing in the current spine links base → billing → units.

**Why it matters most to rentals specifically:** these are the new towers. 43 of
1,212 ledgers (3.5%, 11,073 rental events) sit on billing lots, and the spine
calls all 43 "not a parcel". At the 41,816-building citywide scale that is the
single largest parcel-match failure mode in the pipeline.

**The fix:** pull `lot >= 7501` from PLUTO as parcels with
`kind = "condo_billing"`, and add the `base -> billing` lineage edge, which has
to be reconstructed since neither layer states it.
