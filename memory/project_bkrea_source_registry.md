---
name: project_bkrea_source_registry
description: "docs/sources/ is the single organised registry — one file per data source, six fixed sections; ACRIS is next"
metadata: 
  node_type: memory
  type: project
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-07-30T15:46:52.513Z
---

`docs/sources/` in the BKREA app is the **one place** that documents how any data source is pulled.
One file per source, and every file answers the same six questions in the same order:

1. **PURPOSE** — which bucket it moves (DEVELOPMENT / OPPORTUNITY / COMPARABLE)
2. **SOURCE** — hosts, dataset ids, keys, identifier traps, **measured** coverage dates, and how
   "no data" can be a lie for that source specifically
3. **DOCUMENTS** — what it publishes, what each is worth, with n
4. **EXTRACTION** — the path plus the reading rules, each annotated with the failure that taught it
5. **FIELDS** — what is harvested, how it is cleaned, **how it is verified**, fill rate
6. **SECTION** — ⏸ deliberately empty; card assignment is deferred until the pull side is settled

Written 2026-07-30: `01-dob-bis` · `02-dob-now` · `03-pluto`. Stubs: `04-acris` · `05-dof` · `06-dcp`.
`_TEMPLATE.md` is the starting point for a new source.

**Why it exists:** ten docs already covered slices of source→document→extraction→field (~3,300 lines)
and disagreed in places. The README names exactly what is superseded and what is NOT —
`DATA_SOURCES.md` (citywide endpoint atlas), `FIELD_REGISTER.md` (field-level spec) and the generated
`PERMIT_LEGEND.md` all stay.

**Order of work:** finish DOB NOW + BIS Web, then ACRIS (deeds, mortgages, easements, ZLDA), then DOF,
then DCP. Related: [[feedback_bkrea_pull_package_monitor]], [[project_bkrea_territory_intel]].
