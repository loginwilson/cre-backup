# BIS Web — the source

**Second source through [the workflow](../../WORKFLOW.md). Not started.**
Same five steps, different sanitization strategy — this page records the strategy
as planned and the two findings that already constrain it.

Login, 2026-08-14: *"specification on bis web is going to be different since we
will map it different, acquisition will prob only be pw1 and zd1, extract will
probably only be project details and contacts, resolution is following the
project and the people at different stages and maybe even the parcels different
projects over the years, derivation will be more so for products that would use
bis web like a dev pipeline map."*

## ⚠ TWO FINDINGS THAT ALREADY EXIST — READ BEFORE PLANNING

### 1. Document access — ⚠ SOLVED ELSEWHERE. Get the method before planning.

A 2026-08-06 probe recorded `/bisweb/JobsQueryByNumberServlet` as **403 at the
Akamai edge** and concluded document access was refused. **Login, 2026-08-14:
that was worked out in the developments chat — the conclusion is superseded.**

⚠ **DO NOT PLAN BIS ACQUISITION FROM THE OLD NOTE, AND DO NOT RE-DERIVE IT BY
PROBING.** The working method exists in another conversation; retrieve it from
there when BIS starts. Building around a refusal that has already been resolved
would throw away real coverage — the mirror image of the mistake this whole
structure exists to prevent, and this time it was the *stale* record doing the
misleading rather than the missing one.

⚠ The old note is kept here rather than deleted because the reasoning it carries
is still live for *other* sources: a published policy in prose on a landing page
counts even when `robots.txt` is unreachable, and a refusal must be recorded as
FAILED and never as "complete with 0 facts". Those rules stand; the BIS verdict
does not.

### 2. A row is not a job — this is the specification unit

`doc__=01` is the original; `02+` are amendments that **restate nothing**.
`zoning_dist1` is present on **0 of 63,293** NB amendment rows.

| specified per | district reported |
|---|---|
| row | "24% missing" |
| **job** | **100% present** |

**Same data. One of those numbers is an artifact of the unit.** This is the
clearest illustration of why specification is a per-source choice and not a
mechanical copy. (DOB NOW: 939,107 rows = 555,652 jobs; New Building is 9,432
jobs, not 54,043 rows.)

## THE RUN AS PLANNED

| # | phase | BIS strategy | status |
|---|---|---|---|
| 1 | specification | map by **job**, not row | not started |
| 2 | acquisition | PW1 · ZD1 — ⚠ **constrained by the refusal** | blocked as originally conceived |
| 3 | extraction | project details + contacts | not started |
| 4 | resolution | a project through its stages · people across projects · **parcels across different projects over the years** | not started |
| 5 | derivation | development-pipeline values | not started |
| → | product | a dev pipeline map | not started |

⚠ **Resolution is where BIS earns its place**, and it is genuinely different from
ACRIS's: the interesting lineage is a *project* moving through stages and the
*same people* recurring across projects — and a parcel accumulating several
projects over decades. That is not a conveyance chain, but it is the same event
graph, which is exactly why step 4 is shared and not per-source.

## KNOWN BEFORE WE START

- **DOB NOW has NO zoning columns at all** — checked against all 95 columns of
  `w9ak-ipjd`. Absent from the schema, not sparse. It carries
  `total_construction_floor_area`, which is **not** zoning floor area. NOW is the
  current system, so for every new building filed since ~2021 the structured
  envelope gap is 100% — **and the document that closes it is behind the
  refusal.**
- **The one real BIS gap is an ERA, not a field:** `proposed_zoning_sqft` is 1.9%
  before 2008 and 100% from 2009.
- **Contacts:** only the *developer* genuinely needs the document. Architect
  phone/email is not in DOB data at all, and joining on licence number
  "resolves" 37% **entirely by collision** — 23.9% of register numbers are reused
  across types. Contractor phone is on 99.6% of 4M BIS permits and unused.
- ⚠ **Socrata `$offset` without `$order` silently drops and duplicates rows while
  the COUNT stays right.** Always `$order=:id`. Fixed in shared `bulk.py`, so it
  affected every decoder.

Measured findings live in `DOB_TRAPS.md`; `dob.py` carries them as code.
