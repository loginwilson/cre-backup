# Where the parties live in DOB NOW — walked on B01262921

Job **B01262921** (plumbing, 280 Kent Avenue), the DOB NOW continuation of BIS
job 320917503. Walked 2026-08-07 in the Public Portal. 5 filings: I1 · S1 ·
S2 · P1 · P2.

---

## ★ THE ERA JOIN IS BIDIRECTIONAL AND HARVESTABLE

Every DOB NOW filing on this job names the BIS job in free text:

    B01262921-I1   UNDERGROUND PLUMBING IN CONJUNCTION WITH NEW BUILDING 320917503
    B01262921-S1   PLUMBING WORK IN CONJUNCTION WITH NB 320917503
    B01262921-S2   BOILER INSTALLATION IN CONJUNCTION WITH NB 320917503
    B01270573-I1   SPRINKLER AND STANDPIPE IN CONJUNCTION WITH NB 320917503
    B01270573-S1   TEMPORARY STANDPIPE IN CONJUNTION WITH NEW BUILDING 320917503

and BIS doc 01 names them back (`DOB NOW JOBS: PL B01262921-S1, SP/SD
B01270573-I1`). **A 9-digit BIS job number inside a NOW `job_description` is a
harvestable edge**, and it survives the typo (`CONJUNTION`) because the job
number is the anchor, not the phrasing.

---

## ⚠⚠ THE OWNER'S CONTACT FIELDS DO NOT EXIST IN DOB NOW

Not blank — **absent from the schema.** Read off `Plans/Work (PW1)` on S1:

    APPLICANT INFORMATION          OWNER INFORMATION
    License Type    ✓              Owner Type                 ✓
    License Number  ✓              First Name                 ✓  Hale
    First Name      ✓  Jared       Middle Initial             ✓
    Middle Initial  ✓  R           Last Name                  ✓  Everets
    Last Name       ✓  Donnamiller Title                      ✓  (empty)
    Business Name   ✓  WSP         Business Name/Agency Name  ✓  TWO TREES
    Business Address ✓ 250 W 34th  ── no address field ──
    City / State / Zip ✓           ── no phone field ──
                                   ── no email field ──

The applicant and the filing representative each get a full business address.
The owner gets a name and an entity. In BIS the fields existed and were empty;
**in DOB NOW they were never designed in.**

### `Statements & Signatures` is NOT the §26 equivalent

The name invites the assumption. It is wrong. The section contains **ten
occupancy / rent-regulation / loft-law questions and nothing else** — no name,
no signature block, no phone, no email:

    1-2   occupied dwelling units during construction
    3-4   occupied dwelling units
    5     rent control / rent stabilization
    6     DHCR notification
    7     Loft Board (MDL Article 7-C)
    8-10  interior work in owner-occupied units

⚠ Do not send a §26 harvester at `Statements & Signatures`. The owner block is
in **`Plans/Work (PW1)` → Owner Information**.

---

## ⚠ CORRECTED — THE OWNER NAME COLUMN IS NOT `owner_s_first_name`

I first reported that "the DOB NOW feed drops the owner's personal name
entirely — a party layer built from `w9ak-ipjd` has no people in it."
**That was wrong, and it was my own bug.** The columns are `owner_first_name`
and `owner_last_name` — **no `_s_`**, unlike every other owner field in the
same table (`owner_s_business_name`). Querying the `_s_` form returns HTTP 400;
reading it with `.get()` silently yields `None`, which reads exactly like an
empty column.

Measured 2026-08-07 over all 939,832 rows:

    owner_first_name        938,836   99.9%
    owner_last_name         939,006   99.9%
    owner_s_business_name   881,036   93.7%
    owner_type              939,707  100.0%
      ...== "Not Applicable" 44,946    4.8%

The five filings, read correctly:

    B01262921-I1  2025-07-30  Hale Everets  Not Applicable
    B01262921-S1  2025-08-15  Hale Everets  Not Applicable
    B01262921-P1  2025-10-07  Hale Everets  Not Applicable
    B01262921-P2  2026-03-06  Hale Everets  TWO TREES
    B01262921-S2  2026-07-31  Hale Everets  TWO TREES

⚠ **A mixed naming convention inside one table is a silent-zero trap** — the
same class of failure as the six key conventions. Probe the column list before
trusting a fill rate; a 400 means "no such column", not "no data".

**What survives from the original finding:** `"Not Applicable"` is a literal
string on 4.8% of all DOB NOW rows and must be excluded from owner harvests.
The entity name genuinely appears only from P2 onward on this job, while the
signatory `Hale Everets` is present from I1 — so the *name* is the reliable
key here, not the entity.

---

## THE PARTIES, AND THE CROSS-ERA PERSON LINKS

    OWNER        Hale Everets · TWO TREES · Corporation or LLC
    APPLICANT    Jared R Donnamiller · PE 092491 · WSP
                 250 West 34th Street, New York NY 10119
    FILING REP   Kelly Byrnes · SOCOTEC, Inc.
                 151 West 42 Street, 24th Floor, New York NY 10036
    DELEGATED    Alexander Rippere · X-006255
    (P1 only)    Dylan Nacht · RYBAK DEVELOPMENT CORP
    PROJECT      Project-000000359

**Three of these are the same humans as the 2014 BIS filing, at different
firms or in different roles:**

| person | BIS 320917503 (2014) | DOB NOW B01262921 (2025-26) |
|---|---|---|
| **Hale Everets** | §26 owner signatory, `DOMINO A PARTNERS LLC` | Owner, `TWO TREES` |
| **Jared Donnamiller** | applicant, doc 02 mechanical | applicant, PE at **WSP** |
| **Alexander Rippere** | §3 Filing Representative, SOCOTEC | **Delegated Associate**, X-006255 |

★ Everets under `DOMINO A PARTNERS LLC` in 2014 and under `TWO TREES` in 2026
**closes the inference** made in `NARRATIVE_280KENT.md` from `bty7-2jhb`
(Everets → GREEN STAR BUILDERS at 45 Main Street, Two Trees' own address).
That was Tier 3 name-matching; DOB NOW states it directly. It is now a read,
not a guess.

⚠ But note the direction of travel: the *contact* still came from the 1989-2013
feed. DOB NOW confirms **who**, never **how to reach them**.

---

## PROPERTY PROFILE — TWO THINGS WORTH HARVESTING

    PARTIAL STOP WORK ORDER EXISTS ON THIS PROPERTY
    DOB Special Place Name:  LOT 1 REAPPORTIONED
    DOB Building Remarks:    BLOCK 2414 NEW LOT 3 (7/17)
    Environmental Restrictions: HAZMAT/NOISE/AIR
    Tidal Wetlands: Yes · Special Flood Hazard Area: Yes
    Additional BINs for Building: NONE

**The lot-lineage note resolves a discrepancy I had flagged as a defect.** BIS
§1 files this job at **lot 1**; the BIS header and DOB NOW both say **lot 3**.
That is not an error — the lot was reapportioned in **July 2017**, three years
after the job was filed. `DOB Building Remarks` carries the lineage in prose.

⚠ Consequence for spine matching: a job filed in 2014 keys to a lot that no
longer exists. Matching on the filing's own §1 lot silently drops it from any
current-lot gate. This is the same lineage failure recorded in
`project_bkrea_lot_lineage`.

`PARTIAL STOP WORK ORDER` is a live stage signal available on the Property
Profile and nowhere in the job feeds.

---

## DOCUMENTS ARE THIN ON SUBSEQUENT FILINGS

    S1  →  1 document   "Other Documents - AI1 - PAA P2"  (2026-03-13, Accepted)

Against the LIC job where **I1 held 26 documents**. Documents concentrate on
the **initial** filing; `-S`/`-P` filings carry only what that amendment added.
Reading "the most recent filing" for documents returns almost nothing — read
`-I1` for the corpus and the later filings for the deltas.
