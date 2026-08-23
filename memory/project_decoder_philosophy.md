---
name: project_decoder_philosophy
description: "The Data Decoder is its own project, NOT a feature of the app — decode the data systems into practical derivations because existing CRE apps run on lagged, wrong and varying data; so freshness IS the product edge"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7c5a3ccb-a88e-40cd-a587-cc575cf7a400
  modified: 2026-08-14T16:17:07.767Z
---

Login, 2026-08-14: *"this data decoder is its own massive project and I want to
treat it separate. instead of building the app from the start, my philosophy has
become to decode the data systems into practical derivations for application
usage since the data used in current apps is highly lagged, wrong, and varying."*

**The decoder is the foundation, not a feature.** Applications are built on top of
its derivations; the derivations are not shaped for one application. See
[[feedback_phase_organization]] — that is why derivation is its own phase.

## What this changes about what "done" means

The advantage claimed is **current, correct, consistent** against competitors that
are lagged, wrong and varying. So:

- **Freshness is the product, not maintenance.** A decoder that is right once and
  stale in a month has no edge over what already exists. The daily routines
  (`selection_daily.py`, `index_daily.py`, the `acris-selection` routine) are the
  differentiator, not chores around it. Budget attention accordingly.
- **Correctness must be provable, not asserted.** "Wrong" is the competitor's
  failure mode, so every number needs its evidence: provenance per value,
  reconciliation that reports UNKNOWN rather than zero, and a refusal to repair a
  figure to make a check pass.
- **Consistency means ONE definition per value.** "Varying" is what happens when
  each screen computes its own $/BSF. Precompute in the database, one definition,
  traceable to events — the app only does UI/UX.
- **Generality is a requirement, not elegance.** The moment a derivation is
  shaped for one screen it stops being a derivation.

## Infrastructure separation (confirmed 2026-08-14)

Two Supabase projects, both Login's, deliberately separate:

| project | host | what |
|---|---|---|
| BKREA app | `ghjkjxfxtpqhxxkxbdrp` | the territory app — **was shared**, hands off |
| **Data Decoder** | `trljekigamtnxqfoyorm` | this project's store, entirely ours |

⚠ **The decoder store is 67 tables of layered generations**, and only ONE carries
current meaning: `document_map`, 17,047,472 rows. The rest is residue —
`acris_bbl_spine` AND `decoder_bbl_spine`, `acris_posting` AND `decoder_posting`,
`acris_document` AND `decoder_document` AND `decoder_documents`, a full parallel
view set (`acris_v_*` / `decoder_v_*`, six each), `acquisition_pending` as a
near-duplicate 17M copy of document_map, plus superseded experiments
(`parcels` 1.2M, `parcel_geometry` 1.7M, `residential_leases` 1.4M,
`condo_sales` 374k).

**Fix chosen: a new SCHEMA, not a new project** —
`migrations/001_decoder_schema.sql`. `ALTER TABLE ... SET SCHEMA` moves
document_map instantly with no data copy, versus ~14 h to re-push 17M rows into a
fresh project. `public` becomes a read-only archive: nothing deleted, and no old
script can write to the new store by accident.
⚠ **The move is LAST.** Six scripts read `document_map` through PostgREST
(push_selection, push_maps_tail, reconcile_selection, selection_cross,
selection_daily, selection_delta). Moving before both schemas are exposed and
those readers are repointed makes them 404 — and a PostgREST 404 returns an EMPTY
RESULT, which reads as "nothing to reconcile".

## The storage rule (was an accident, now stated)

- **DISK / the drive** — images, and bulk immutable source pulls. Written once,
  read sequentially, never queried per row.
- **SUPABASE** — anything the pipeline or an application must QUERY.

⚠ **Open decision:** the 100.8M-row support index sits exactly on that line.
Leaning master + parties + legals in Supabase (86.3M, the three fusion uses),
references + remarks on disk. Not settled.
