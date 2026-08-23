---
name: reference_socrata_pagination_order
description: Socrata $offset paging without $order silently drops and duplicates rows while the row COUNT stays correct — always pass $order=:id
metadata: 
  node_type: memory
  type: reference
  originSessionId: 5e3987d2-a689-4455-ba4f-ed13d53b22e6
  modified: 2026-08-06T13:12:27.368Z
---

Socrata `$offset` pagination with **no `$order`** is not stable. The server may
return rows in a different order per page request, so offset paging skips some
rows and repeats others.

Measured 2026-08-06 on `ic3t-wcy2` (DOB BIS jobs), `job_type='NB'`:

    unordered:  199,888 rows / 199,679 distinct  (209 dupes) — and run-to-run
                results differed from each other, so it is not deterministic
    $order=:id: 199,888 rows / 199,888 distinct  (0 dupes)

**Why it hides:** the row count is correct in every case. The one check anybody
performs on a bulk pull is the check this failure passes. It was found only
because two measurement rounds of the same query disagreed by 48 job numbers.

**Fix:** `$order=:id` — Socrata's own row identifier, unique and indexed.
Verified present on ic3t-wcy2, w9ak-ipjd, ipu4-2q9a, bs8b-p36w, pkdm-hqz6,
bnx9-e6tj (ACRIS master) and yvxd-uipr (BSA). Not valid alongside `$group`, so
skip it on aggregates.

Applied as the default in `decoder/bulk.py`, which every decoder chat shares —
so this was never a DOB-only bug.

Same family as [[feedback_bkrea_scale_failure]]: large N hides the defect
because the summary line looks right.
