---
name: project-decoder-seven-phases
description: "The phase tree 00-07, the two-database architecture, the per-phase trio format, and the structural triggers — settled 2026-08-21"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-21T21:57:19.508Z
---

THE PHASE TREE (folders on D:\CRE Decoding System\): 00 Synchronizations ·
01 Navigations · 02 Acquisitions · 03 Organizations · 04 Extractions ·
05 Resolutions · 06 Derivations · 07 Productizations. Four bands: sync =
staying aligned with sources · nav→org = THE RECORD · ext→der = THE READING
· 07 = packaging.

**TWO DATABASES, ONE BOUNDARY (2026-08-21).** THE RECORD =
`D:\CRE Decoding System\Legal Instruments.db` (tree ROOT — renamed/moved
from "01 Navigations\Legal Instruments Navigation.db"; `corpus_paths.NAV_DB`
points there; old file kept as frozen backup). One `navigation` table,
columns in PHASE ORDER: id | rd_url | pdf_url | recorded_details | pdf |
keyed_by | key. Extraction reads it BY PARCEL and writes
`Legal Instruments Decoded.db` (events/claims — shape changes to many rows
per doc, hence the split); doc id + key are the join.

**PER-PHASE TRIO + WATCH:** `routine_<phase>.py` (six-step grammar) +
concise md (old ones archived to _archive/) + the shared db + a board row
(every new routine ships with its row). Built and proven: sync (4AM sched),
nav (4:20AM audit — NAVIGATION LEVEL first run), org
(routine_organization.py, parked until acq fills contexts; nav_key.py is
the engine). Acq md written; lanes = 4×20 acris rd start, rd/pdf split A/B
open, Richmond rd+pdf via Chrome.

**STRUCTURAL TRIGGERS in the record db** (bad states unrepresentable):
`mint_urls` — any inserted id gets both urls in the same transaction
(GLOB 'RC_*' branches the mint; ⚠ LIKE 'RC.%' matched nothing — the control
insert caught it). `key_rules` — keyed_by only ''/parcel/reference/
pdf-pass/pdf with evidence landed; PARTY ABORTS (party proves association
not coverage — it is DECODING, lives with function in 05/06).

**ORG LADDER (settled):** parcel (inline the moment rd lands — the walker
holds the parse) · reference (convergent quiet passes) · pdf (when file on
disk). No network → fully automatable; never a sweeping process beside
writing lanes. First audit 2026-08-21: parcel 2,661,283 · reference 47 ·
pdf-pass 12,034 · unkeyed 21.37M · identity CLOSED at 24,042,114.

**COMPLETENESS CLOSED 2026-08-21:** ACRIS = Socrata distinct-id diff (every
band matched exactly; masters carry DUPLICATE rows — always count distinct)
+ CRFN census per year (hole-proof probe: seed at held count, Fibonacci
confirm) → 7,010 residues = 6,808 void + 1 held + **201 live documents the
index dropped — landed**. Richmond = rc_census window sweep 1850→today
(keep-alive requests ~2× faster; control-first). Socrata refresh ~weekly
(was Aug-10); the CRFN edge walk owns the tail — and the index DROPS live
docs, so the counter census is load-bearing, not redundant.
