---
name: project-decoder-phase-assertions
description: "What each of the six decoder phases ASSERTS when it completes, and therefore what its gate must prove"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-20T18:29:36.124Z
---

Each phase makes exactly ONE claim, and its gate exists to prove that claim. Stated
by the user 2026-08-20:

| phase | asserts | gate that proves it | status |
|---|---|---|---|
| **sync** | our system has EVERY SINGLE doc | `live state − new total == 0`, per custodian | ✅ built |
| **navigation** | every doc id is TABLED with what acquisition needs — key, index, endpoint | `UNKEYED == 0` + doc id / endpoint 100% | ✅ FINAL contract shipped 2026-08-20 |
| **acquisition** | the document IMAGE is sourced directly into the table (pdf attachment) | *(none yet — see below)* | ⚠ MISSING |
| **extraction** | the EVENTS of the document (data table / summary) | Bootcamp event row, five field states | partial |
| **resolution** | how the events CHAIN together (data table / summary) | — | not built |
| **derivation** | what MATTERS TODAY given all context, as outputs (data table / summary) | — | not built |

**It is a PASS-OFF workflow.** A phase may not start until the previous one
completed, unless deliberately authorized. Sync emits the dated table of new ids →
nav takes those ids and maps them → acq attaches the pdf → extraction reads it.
Enforced in `routine_4am.py`: `sync_table.py`'s exit code IS the gate, and
navigation prints `HELD` rather than building against a specification known to be
short (`--authorize-nav` overrides).

⚠ **THE ACQUISITION GATE DOES NOT EXIST YET** and it is the next one needed. Nav's
`pdf` column is a *computed path*, not evidence a file is there — `str(CP.STORE /
f"{did}.tif")` is written for all 24,039,303 rows whether or not anything was ever
fetched. So 100% of rows "have a pdf" by construction. The gate must count files
that actually exist, with `imageless` documents excluded from the denominator by
name (174,142 of them must never be fetched).

⚠ **A GATE READING ZERO PROVES NOTHING UNTIL YOU CHECK ITS DENOMINATOR.** Nav's
`UNKEYED 0` was true while it was still an open question whether every document was
present at all — those are different denominators. The real answer came from
counting both sides: spec DB 24,039,303 vs nav 24,039,303, difference 0. See
[[feedback-bkrea-scale-failure]] and [[feedback-confidence-backcheck]].

**NAV SHIPPED FINAL 2026-08-20 (login-approved):** seven columns
`id | keyed_by | key | recorded_details | rd_endpoint | pdf | pdf_endpoint`;
24,039,303 rows, gate PASS, plus the SORTED SIBLING
`legal_instrument_navigation_by_parcel.csv` — (key, recorded, id) order,
verified 0 violations full-pass — each parcel's documents read as its
chronological story (the bootcamp/extraction feed). Census recorded every
build: parcel 22,283,808 · party 1,711,319 · doc 44,176.

**The parcel-less model (MEASURED, 125-doc stratified probe + corpus census):**
digital-era parcel-less: 40% have their BBL on the rd page (bulk capture was
Socrata-blind — the rd re-pull recovers them; same walk fixes ACRIS parties
21.05%→full), 36% reference-attached, 24% genuinely party-keyed liens.
Film-era 1.34M = the personal-property/UCC ledger: 0% parcels, references
form a CLOSED loop (0 of 136 targets land parcel-keyed) — they key to the
DEBTOR and meet parcels via the entity join at derivation. Richmond: every
doc has a block; 306,857 lot-0000 docs are lot-less AT the custodian (probe
must pin the internal id — instrument numbers REPEAT and v1 read wrong docs,
a false 12/12). ⚠ Twice in one day a probe lied by parser: borough written
"MANHATTAN / NEW YORK" vs exact-match "MANHATTAN" (false 0/36), and CRFNs
line-wrapped in cells (false "no references") — parse the custodian's CELLS,
never exact-match or regex the flattened page.

Related: [[feedback-phase-organization]], [[project-decoder-bootcamp]],
[[project-acris-selection-job]], [[project-acris-resolution-model]].
