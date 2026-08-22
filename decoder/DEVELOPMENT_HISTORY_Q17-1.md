# Queens Block 17 Lot 1 — a development history assembled end to end

2-11 / 2-33 50 Avenue (a.k.a. 49-02 5 Street, 41-18 / 4-20 / 4-42 / 4-44 / 4-46
49 Avenue), Hunters Point LIC, CB402. Run 2026-08-06.

**Coverage of this document:** assembled from FIVE structured sources unioned on
the BBL, plus the DOB NOW portal's per-filing Zoning Information read on screen.
**No scanned document has been opened.** Owner contact detail (PW1 §26) is
therefore NOT in this history — it is the next step, not a gap in the method.

---

## THE HISTORY

### Era 1 — Judson Art Warehouse (…–1997)
    1992-12-02  sprinkler work        ALLSTATE SPRINKLER CORP    owner JUDSON ART WAREHOUSE
    1997-07-11  waterproofing (A3)    A.O.I. WATERPROOFING INC.  owner JUDSON ART WAREHOUSE

### Era 2 — Fortress (1998–2003), and a collapse
    1998-01-14  HVAC (A2)             ULTRA AIR INC.             owner FORTRESS
    2003-01-31  140-FOOT HEAVY DUTY SIDEWALK SHED (job 401603920)
                MRC II CONTRACTING    owner FORTRESS NY INC.     zoning M1-1D
    2003-02-24  "Removal of partial collapsed section of two story building.
                 Erect temporary fence."  (job 401613811, A2)
                LJC DISMANTLING       owner Fortress NY Holding
    2003-03-26  DEMOLITION permits x2 (jobs 401622981, 401622990)
                LJC DISMANTLING

★ A 140-ft shed in January, a *partial collapse* in February, demolition in
March. That is a building failing, read straight off the permit sequence.

### — gap, 2003 to 2021, no DOB activity —

### Era 3 — 50TH & 5TH LIC LLC (2021–2025)
    2021-08-19  NB Q00564746 FILED — 12 storeys, 561,670 sf, 499 DU, 125 ft
                architect    PAUL CARR (RA), S9 ARCHITECTURE
                filing rep   MaryAnn Brown, GEORGE E. BERGER & ASSOCIATES
                owner        50TH & 5TH LIC LLC
                32 filings:  A1 A3x4 A5 A6 A7 A8 A9 B1-B5 C7 I1 P1-P4 P9
                             S1-S4 S6-S9 Z1 Z2
    2021-09-20  load test piles       MUESER RUTLEDGE CONSULTING ENGINEERS
    2021-10-07  DM x3 on BINs 4436571 / 4436573 / 4436574 (heights 18 / 25 / 27 -> 0)
    2021-11-18  interior demolition x3   CELTIC SERVICES NYC
    2022-01     construction fence, three heavy-duty sidewalk sheds
    2022-02-01  builder's pavement plan  BIS job 440704356 — FILED, NEVER PERMITTED
    2022-05-10  DM PERMITS ISSUED        CELTIC SERVICES NYC  ph 718-717-2721
    2022-07-11  sidewalk shed during NB construction
    2023-01-06  east + north hoists (49 Ave), dual 6000 lb personnel/material
    2023-03-10  overhead protection at ADJACENT properties
    2024-11-18  ★ TEMPORARY USE PERMIT — sales office 1st fl, MODEL APARTMENTS 6th fl
    2025-05-09  ★ CERTIFICATE OF OCCUPANCY — Initial, 499 DU, no. 4625206-0000001

### Era 4 — tenanting (2024–2026), read off the alteration filings
    2024-06  food market w/ commercial kitchen + hood   2024-12  daycare
    2025-01  Club Pilates          2025-03  GlowBar     2025-04  KidStrong
    2025-05  Tiger J health/fitness                     2025-07  Matsuzuki Sakura
    2025-07  Dumbo Market · Jasper · Frankie's Brooklyn Pizza
    2025-09  Stretch Lab           2025-12  Peanut and Honey Baby & Children

**Ownership chain:** JUDSON ART WAREHOUSE → FORTRESS NY INC / Fortress NY
Holding → 50TH & 5TH LIC LLC. THE VOREA CONSTRUCTION COMPANIES and DOMAIN
COMPANIES appear as the named owner on individual filings — a developer/operator
signal the deed will not show.

**Envelope (DOB NOW Zoning Information, filing C7):** M1-5 56,000 sf + M1-4
20,000 sf = **Lot Area Total 76,000**; corner; lot width 400; street legal width
60, public; yards 0/0/30; LIC Mixed Use District, map 8d; **lot existed prior to
15 Dec 1961: Yes**; **zoning lot certification (zoning exhibits) required: Yes**.

⚠ **The CO is probably not final.** Eight CO records, `Initial` 2025-05-09 then
seven renewals through 2026-07-10, all `c_of_o_status = CO Issued`. A renewal
series running fourteen months past the initial is the TCO pattern. `pkdm-hqz6`
does not publish a temporary/final flag, so **delivered-vs-complete is UNRESOLVED
here** and must be read off the portal's Certificate of Occupancy section.
Reporting this as "complete" would be exactly the stage error the model warns of.

---

# RUNNING THE SOURCES IN UNISON — the handoff is where things vanish

The point of this run was to prove nothing is lost when one system hands to the
next. It is lost, measurably, and here is where.

## ⚠ 1. THE JOBS FEED IS NOT THE RECORD. THE PERMITS FEED IS DEEPER.

On this one lot:

    job numbers in ipu4-2q9a (permits)   10
    job numbers in ic3t-wcy2 (jobs)       6
    in PERMITS but NOT in JOBS            5  <- 400339674, 400753591, 400806927,
                                                401622981, 401622990
    in JOBS but NOT in PERMITS            1  <- 440704356 (filed, never permitted)

**Reading `ic3t-wcy2` alone loses 1992, 1997, 1998 and the entire 2003
demolition** — i.e. it loses the event that cleared the site. And reading permits
alone loses the filed-but-never-permitted job, which is itself the finding
(intent without authorisation).

**Neither feed is a superset. Union them, always.**

## ⚠ 2. `ic3t-wcy2` HAS A HARD FLOOR AT 2000-01-01

Measured citywide: `min(pre__filing_date) = 01/01/2000`. Nothing earlier exists
in the jobs feed at all. Every pre-2000 DOB event reaches us only through the
permit feeds.

## ★ 3. `bty7-2jhb` HISTORICAL PERMIT ISSUANCE — the deepest online DOB layer

**1989-05-11 → 2013-04-24, 2,428,526 rows.** Never touched by this project
before today. It is what produced Era 1 and Era 2 above, and it carries fields
the modern feed does not: `owner_s_house`, `owner_s_house_street_name`,
`owner_s_house_city/state/zip`, `owner_s_phone`, `permittee_s_phone`,
`superintendent_business_name`, `job_type`, `filing_status`.

**An owner mailing address and phone, on permits back to 1989.**

## ⚠ 4. A FIFTH KEY CONVENTION — and it nearly produced a false "nothing here"

`bty7-2jhb` uses `borough='QUEENS'` (upper) with **UNPADDED** block and lot.

    borough='QUEENS' block='00017' lot='00001'  ->  0 rows
    borough='QUEENS' block='17'    lot='1'      -> 12 rows

The first form returned zero and reads exactly like "this lot has no historical
permits". The control query caught it. That is now **five conventions across six
DOB datasets** — the key format is a property of the DATASET, never the agency,
and an uncontrolled query is not evidence of absence.

## ⚠ 5. `ipu4-2q9a.issuance_date` MIXES DATE FORMATS — min/max on it is a lie

    min(issuance_date) = '01/01/2007'      max = '2020-06-05'

Both formats live in the same text column, so lexicographic min/max is
meaningless — this lot has permits from 1992 and 2022, outside that "range".
**Never characterise a feed's reach from min/max on a text date.**

## ⚠ 6. BIN IS NOT STABLE — five BINs on one lot

    4436571 · 4436572 · 4436573 · 4436574   the buildings that were demolished
    4625206                                  the building that replaced them

The Property Profile says `Buildings on Lot: 1` and `Additional BINs for
Building: NONE` — **true of today, and it erases the four predecessors.**
Anchor the history on the BBL and union every BIN the lot has ever carried.

⚠ And BIS appears to RE-ATTRIBUTE: the 2003 sidewalk-shed job 401603920 carries
BIN **4625206** — the BIN of a building that would not exist for eighteen years.
Mechanism unverified; treat BIN-on-an-old-job as unreliable and date events from
the filing/issuance date, never from the BIN.

## The unison rule

For one parcel, union — each with its own controlled key spelling:

| source | reach | gives |
|---|---|---|
| `bty7-2jhb` historical permits | 1989–2013 | earliest owners + owner address/phone |
| `ipu4-2q9a` permits | ≥1992–2022 | permittee + direct phone, jobs the jobs feed lacks |
| `ic3t-wcy2` BIS jobs | 2000–2025 | job type, envelope fields, B-Scan folder route |
| `w9ak-ipjd` DOB NOW | 2016–now | current filings, base/suffix chain |
| DOB NOW portal | 2016–now | per-filing Zoning Information, PW1, documents |
| `bs8b-p36w` / `pkdm-hqz6` CO | — | occupancy; ⚠ no temporary/final flag |

Then: order by date, classify type, attach players, resolve stage. The eras above
came out of exactly that union, and **three of the four eras would be invisible
from the jobs feed alone.**

## Still to do on this parcel

1. Open the PW1 for `Q00564746` — §26 owner contact, the one thing this history
   has no source for.
2. Read the portal's Certificate of Occupancy section to settle TCO vs final.
3. Test the pre-1989 layer: records request (pre-BIS job numbers, microfilm,
   docket books), I-cards via HPD Online, and BSA back to the 1930s–40s.
