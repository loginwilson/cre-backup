---
name: bkrea-dob-field-traps
description: "Verified DOB field names, join keys and the traps that make feeds silently fold nothing — check here before wiring any DOB source"
metadata: 
  node_type: memory
  type: reference
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-07-31T11:39:10.050Z
---

**Guessing DOB column names has burned this project twice.** Verify against a live sample before wiring anything.

**THE CO JOIN TRAP.** The certificate feed is its OWN module in DOB NOW, so it keys differently: jobs carry `job_filing_number` = `Q00848877-I1`, certificates carry `job_filing_name` = `Q00848877`. **Strip the `-XX` suffix or the join returns zero** — 24,691 final COs matched nothing in a naive test. And there is **no "Temporary" filing type**: `c_of_o_filing_type` values are `Initial` (8,741), `Renewal Without Change` (45,846), `Renewal With Change` (6,481), `Final` (18,682). A TCO is an Initial or a Renewal; only `Final` is the real CO.

**FEEDS (all verified live, fill rates from real samples)**
- Jobs: BIS `bis-jobs` (`job_type` only ever A1/NB/DM; `pre__filing_date`, `approved`, `fully_permitted`, `enlargement_sq_footage` 100%, `initial_cost` 100%, no work-area field) · NOW `now-jobs` (`filing_date` 99%, `approved_date` 89%, `total_construction_floor_area` 99%, `proposed_dwelling_units` 93%; ⚠ `first_permit_date` only 39% — **the permits feed is the authority**, not this).
- Permits: BIS **`ipu4-2q9a`** (`permit_type` NB/FO/AL/EW/PL/EQ/DM/SG, `permit_sequence__`, `issuance_date`, `expiration_date`, `job_start_date` 100%, `filing_status` INITIAL/RENEWAL) · NOW **`rbx6-tga4`** (`work_type`, `sequence_number`, `issued_date`, `expired_date`, `filing_reason`, `permit_status` = `Permit Issued` → `Signed-off`, `work_on_floor` 94%). Permit number encodes the trade: `X08008823-I1-GC`.
- Certificates: BIS `bs8b-p36w` · NOW `pkdm-hqz6`.
- Other: **`g76y-dcqj` After Hour Variance** — best "crews on site right now" signal (bbl 99%, dated windows, `crane_use` flag, joins via `workpermitnumber`). `i296-73x5` Stalled Construction Sites is **complaint-derived**, not a DOB determination. ⚠ **`n4tc-j6kh` "Inspections Requested" is SCHOOL inspections**, not construction — a name that would fold nothing.

**FIELDS THAT LOOK USEFUL AND AREN'T**
- `work_on_floor` is the job's **scope, not progress** — every permit on a job carries the same value and it never moves (99.2% flat across multi-permit jobs). Not a velocity signal.
- BIS `existing_*` fields are unfilled ~half the time (`existingno_of_stories` 0 on 49%, `existing_zoning_sqft` 0 on 51%), so any "proposed > existing" test measures FIELD POPULATION, not change. Only `enlargement_sq_footage` needs no baseline.
- BIS `permit_status` has no sign-off (ISSUED/IN PROCESS/RE-ISSUED) but **NOW permits DO sign off per trade** (~25% read `Signed-off`) — per-phase completion is visible in the new system only.

**UNRESOLVED:** where the **19,373 `LOC Issued`** jobs land. A Letter of Completion is a finish line for jobs that never get a CO; if the stage model only keys on TCO/CO they are misfiled. Cheapest real bug available.

**BBL:** NOW's `bbl` field is 92.4% (worse than BIS's 97.4%) but **100% recoverable** from borough+block+lot — zero truly unmatchable. Compute it, never read it, or 9,485 filings silently vanish.

Related: [[bkrea-stage-model]], [[bkrea-source-registry]], [[bkrea-devbulk]].
