---
name: project_acris_document_inventory
description: "Counted inventory of ACRIS/DOB by type — the signal types are TINY (DEVR 1,201, AIRRIGHT 64), FT_ microfilm is 35.8% with no document_date, Staten Island is a split custodian, and a median parcel is only 12 documents"
metadata: 
  node_type: memory
  type: project
  originSessionId: 176544e8-656c-4540-a15c-f710beced15e
  modified: 2026-08-14T18:49:21.529Z
---

Counted live from the free index 2026-08-05/06. Full tables in
`decoder/DOCUMENT_INVENTORY.md`.

**THE SIGNAL TYPES ARE TINY — the inverted ratio.** ACRIS is 17,036,716 docs
across 95 types, but 5 types (MTGE/DEED/SAT/ASST/PAT) are **80.8%** of it. The
15 envelope classes are 1,278,242 — of which **AGMT alone is 920,875 (72%)**.
The four types that name a rights transfer outright — **DEVR 1,201 · AIRRIGHT 64
· LIC 140 · DEED,RC 474** — total **1,879 documents, 0.011% of ACRIS.**
Also: ZONE 46,079 · EASE 20,862 · DECL 19,155 · LDMK 1,226 · CONS 1,577.

**⚠ `no_image` IS NOT A SAFE GATE, AND 174,142 IMAGE-LESS DOCS SIT IN THE
ACQUISITION QUEUE.** Measured 2026-08-14: `document_map.no_image` is TRUE for the
`total_pages = 0` population and **FALSE for the `total_pages = -1` population**,
though neither has an image. 8 of 8 sampled −1 documents were in
`acquisition_pending`. ACRIS serves its no-image placeholder as **HTTP 200**, so a
runner would record ~174,000 successful fetches of a placeholder with nothing
erroring. **Gate on the ledger (`source_document.acquisition_mode`), never on that
flag.** Fix: `ledger_backfill.py` records them as mode `index`.
⚠ **AND THEY ARE NOT A PRE-1960s TAIL.** Exact by decade: 1960s 30,033 · 1970s
41,030 · **1980s 42,343** · 1990s 38,861 · 2000s 10,615 · 2010s–2020s **4,648**
(1,073 in the 2020s alone); only ~6,600 predate 1960. **No date rule can gate
them** — image-less documents are still being created. Types: RTXL 108,385 (62%),
**DEED 19,714, MTGE 16,441** — for those the index is the entire record, forever.
⚠ The no-image pull wrote `acris_placeholder_returned` for ALL 174,142,
flattening the 0 (placeholder) vs −1 (microfilm, never scanned) distinction that
document_map still holds. Recover the reason from `total_pages`; do not copy the
pull's value.

**⚠ FT_ = FILM TRANSFER = 6,092,729 docs (35.8%), and it silently broke
timelines.** All carry reel/page citations, reaching back past 1967. **79%
(4,811,623) have NO `document_date`, only `recorded_datetime`** — so any code
reading document_date drops 4.8M documents as "undated", and they are exactly the
EARLY ones. A parcel history claiming birth-to-present was starting in the modern
era. Fixed via `timeline.doc_date()` fallback + `reel_of()`. **Pre-electronic
parcel history is reachable from the FREE index today, no images needed.**

**⚠ STATEN ISLAND IS A SPLIT CUSTODIAN.** ACRIS master has **ZERO** documents
recorded in borough 5. But ACRIS legals has 206,662 SI parcel links across
192,950 documents — sampled at BOTH ends of the index, >98% are **RPTT transfer
TAX returns**, administratively recorded in the Bronx. SI deeds/mortgages/
easements live with the **Richmond County Clerk** (digitised to **1945**, earlier
than ACRIS; $0.25/page; (718) 675-7700; read their published Terms first).
Generalises: a parcel history from ACRIS alone can be structurally incomplete,
not merely unread — **RPTT present with no matching deed is the tell.**

**THE NUMBER THE WORKFLOW RUNS ON: a median parcel is 12 documents** (mean 13.7,
p90 23, max 78; measured on 519 LIC lots / 7,100 docs). At 2 requests/doc that is
**~2 parcels/day → 760/year** within the existing polite budget; at the 15-req
per-page fallback, 101/year. **The 17M figure governs corpus acquisition and does
NOT govern walking a parcel** — arguing the 17M number was the wrong frame.

**DOB is document-bearing too, and only partly pluggable.** BIS 2,715,848 jobs
(NB 199,888 + A1 220,051 carry ZD1); DOB NOW 939,107 filings; 15,207,079 DOB
records total. On NB+A1, `proposed_zoning_sqft` is **non-zero only 32.9%** and
`zoning_dist1` missing on 24% — **so for ~2/3 of envelope filings the ZD1
document is the only source.** DOB NOW is thinner still (no zoning district or
zoning sqft at all). Both DOB hosts **403 their own robots.txt** — no published
policy to read; treat as unknown, ask rather than probe.

Related: [[project_acris_bulk_acquisition]], [[project_acris_decoder]],
[[project_bkrea_lot_lineage]], [[feedback_bkrea_scale_failure]].

## ⚠ VERIFIED 2026-08-14: ACRIS HAS **ZERO** STATEN ISLAND RECORDINGS

`recorded_borough` in MASTER has only FOUR values — Manhattan 6,213,473 · Queens
4,926,801 · Brooklyn 4,336,657 · Bronx 1,588,159. Borough 5 does not appear at all;
the earlier "RPTT only" reading understated it. Richmond County deeds are with the
**County Clerk**, not ACRIS. Login 2026-08-14: *"we will consolidate later with their
county clerk"* — parked deliberately, not overlooked.

But LEGALS carries **207,392 rows for borough 5** — Staten Island PROPERTIES referenced
by instruments recorded in the other four boroughs. So the parcels are visible while
their conveyance history is not, which is the shape most likely to read as coverage.

⚠ **THIS IS THE GAP CLASS INTERNAL RECONCILIATION CANNOT SEE.** ACRIS ↔ local ↔
Supabase agreeing at 17,049,742 ([[project_acris_selection_job]]) proves the copy is
faithful. All three would agree just as perfectly on a hole in the source. Completeness
of the SOURCE is a separate question from completeness of the COPY, and only an
outside witness answers it.
