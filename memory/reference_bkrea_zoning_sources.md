---
name: reference_bkrea_zoning_sources
description: "BKREA zoning knowledge sources — the uploaded DCP PDFs are image-only scans (how to read them), plus the authoritative ZR site and what lib/zoningReference.ts already covers"
metadata: 
  node_type: memory
  type: reference
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-26T16:33:22.724Z
---

**Sources Login supplied 2026-07-26 for making BKREA zoning-expert:**

1. **NYC Zoning Handbook, 2025 Edition** (DCP) — `C:\Users\smile\Downloads\Fable 5 (Sunday, July 26, 2026)\New York City Zoning Handbook.pdf`, 128 pages. Post-City-of-Yes (2024 reforms: Carbon Neutrality, Economic Opportunity, Housing Opportunity).
2. **The Zoning Tables** (DCP) — same folder, 163 pages. District-by-district bulk tables.
3. **Zoning Resolution — the authoritative source**: https://zr.planning.nyc.gov/ — Login: "the best reference will always be directly reading and understanding the zoning resolution."
4. **ZoLa** (DCP mapping; what PropertyScout uses) + rezonings — Login: the references cover general rules but MISS tiny district-specific details and special districts.
5. Separately: **tax abatements / bonuses** (421-a, J-51, ICAP, 485-x…) — a whole other axis.

**CRITICAL — both PDFs are IMAGE-ONLY SCANS (zero text layer).** `pdftotext`/pypdf extract 0 chars; `pdftoppm` is NOT installed so the Read tool can't render them directly. WORKING PIPELINE (verified): `pip install pillow`, then extract the embedded page image with pypdf and Read the PNG:
```python
import pypdf, os
r = pypdf.PdfReader(PDF); img = list(r.pages[PAGE_INDEX].images)[0]
open(OUT_PNG,"wb").write(img.data)   # then Read the PNG (renders visually)
```
Each page ≈ 250–300 KB PNG and is EXPENSIVE to read visually — read pages SELECTIVELY, never in bulk.

**The ZR site is fetchable + text-based + section-addressable** (verified via WebFetch): 14 Articles + 11 Appendices; URLs like `/article-ii/chapter-3`, `/appendix-b-index-special-purpose-districts`, `/recently-adopted/<project>`, `/search`. Article II ch.3 returns REAL regulatory text incl. "MAXIMUM FLOOR AREA RATIO FOR R1-R5 DISTRICTS" tables. → PREFER the ZR site over the scans for rule text; use the scans for visual bulk tables.

**Already in the repo:** `lib/zoningReference.ts` (392 lines) is a real reference engine — `ZONING_REFERENCE: Record<string, DistrictRef>` with residential base+affordable FAR (narrow/wide via `FarValue`), CF FAR, commercial FAR, manufacturing FAR, `residentialEquivalent` (C→R mapping), duFactor. It was **already transcribed from this handbook's Ch.8**. Division of labour: MapPLUTO supplies per-parcel base FAR (authoritative, handles overlays/split zones); the reference adds what PLUTO lacks (MIH/affordable bonus, C→R equivalence, bulk rules).
Its own documented **PENDING list ≈ Login's wish list**: M2-A/M3-A two-tier FARs, commercial overlays, **special districts (incl. ZR 117-321 waterfront subareas), UAP/IH, TDR/air-rights bonuses**. Related: `lib/qrs.ts` (260), `lib/studyArea.ts` (387), `lib/rezoning.ts` (386).

See [[project_bkrea_opportunity_card]] (viability derivation: non-viable owners, TDR/ZLDA, QRS street-width/block-size) and [[project_bkrea_change_tracking]].
