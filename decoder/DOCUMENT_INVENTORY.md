# Document inventory by source and type — counted 2026-08-05

Every figure below is a live count from the free index, not an estimate.

**The finding that matters:** the envelope classes are dominated by one huge
catch-all (AGMT, 920,875 = 72% of the set), while the *highest-signal* types are
astonishingly small. **DEVR is 1,201 documents. AIRRIGHT is 64.** That changes
what is achievable without money, without bulk delivery, and without touching
anyone's rate limit.

---

## ACRIS — 17,036,716 documents across 95 types

### The bulk of the corpus is financing and conveyance

| type | count | % |
|---|---|---|
| MTGE mortgage | 4,216,266 | 24.75% |
| DEED | 3,640,429 | 21.37% |
| SAT satisfaction | 2,626,714 | 15.42% |
| ASST assignment | 2,207,817 | 12.96% |
| PAT | 1,067,600 | 6.27% |

Those five are **74.8%** of ACRIS. They are the financing throughline, not the
envelope.

### The 15 envelope / encumbrance classes — 1,278,242 (7.5%)

| type | count | what it is |
|---|---|---|
| AGMT | 920,875 | agreement — **catch-all, 72% of the set** |
| SAGE | 133,727 | sundry agreement — catch-all |
| SMIS | 59,282 | sundry miscellaneous — catch-all |
| CERT | 55,648 | certificate |
| **ZONE** | **46,079** | **zoning lot description** |
| EASE | 20,862 | easement |
| DECL | 19,155 | declaration |
| MISC | 13,470 | miscellaneous — catch-all |
| TERA | 4,462 | termination of agreement |
| CONS | 1,577 | consent |
| LDMK | 1,226 | landmark designation |
| **DEVR** | **1,201** | **development rights** |
| DEED, RC | 474 | deed with restrictive covenant |
| LIC | 140 | license |
| **AIRRIGHT** | **64** | **air rights** |

**The signal-to-volume ratio is inverted.** The four types that name a rights
transfer outright — DEVR, AIRRIGHT, LIC, DEED RC — total **1,879 documents**,
0.011% of ACRIS. The catch-alls that require reading to know whether they matter
total 1,127,354, or 88% of the envelope set.

---

## What is reachable at the polite cap (50 requests/day)

Assuming the whole-document endpoint works — **2 requests per document** (the
container plus the boundary proof), not ~15 per page.

| subset | docs | requests | time |
|---|---|---|---|
| **DEVR only** | **1,201** | 2,402 | **48 days** |
| **DEVR + AIRRIGHT** | **1,265** | 2,530 | **51 days** |
| + LIC, DEED RC, LDMK, CONS | 4,682 | 9,364 | 187 days |
| + TERA | 9,144 | 18,288 | 366 days |
| + DECL, EASE | 49,161 | 98,322 | 5.4 years |
| + ZONE | 95,240 | 190,480 | 10.4 years |
| + the catch-alls | 357,367 | 714,734 | 39.2 years |
| all 15 envelope classes | 1,278,242 | 2,556,484 | 140 years |
| entire ACRIS | 17,036,716 | 34,073,432 | 1,867 years |

**The line between weeks and centuries sits between row 2 and row 5.** The pure
development-rights corpus is obtainable in under two months at the existing
budget, with no money, no bulk delivery and no policy change. Everything from
DECL/EASE upward requires acquisition.

### ⚠ The dependency

This rests entirely on the **whole-document endpoint**, which is **untested** —
access went down before it could be tried, and none of the five candidate URLs in
`fetch_document.py` is confirmed. If it does not work, per-page fetching at ~15
requests per document makes even DEVR alone **360 days**.

**Testing that endpoint is therefore the single highest-value action available.**
It is the difference between 51 days and 5 years for the same corpus. It is
already wired into the 05:16 harvest task.

---

## DOB — the source Login correctly flagged as document-bearing

Line data is the index; the **PW1 application and ZD1 zoning diagram are the
documents**, and this project has already established that material facts live
only in the PDF (developer contact is §26, which the web page never renders).

### BIS jobs by type — 2,715,848

| type | count | carries |
|---|---|---|
| A2 alteration | 1,677,085 | PW1 |
| A3 alteration | 471,763 | PW1 |
| **A1 major alteration** | **220,051** | **PW1 + ZD1** |
| **NB new building** | **199,888** | **PW1 + ZD1** |
| DM demolition | 80,346 | PW1 |
| PA / SI / SC | 66,714 | PW1 |

### DOB NOW filings by type — 939,107

| type | count |
|---|---|
| Alteration | 795,378 |
| New Building | 54,043 |
| Alteration CO | 49,047 |
| No Work | 17,568 |
| ALT-CO w/ existing elements | 15,662 |
| Full Demolition | 7,409 |

**The envelope-bearing DOB set — NB + A1 (BIS) plus New Building + ALT-CO
(NOW) — is 539,643 filings**, each with a ZD1 stating zoning district, lot area,
FAR and floor area as filed. That is the single richest structured statement of
the envelope outside ACRIS, and it is 2.4× larger than the entire ACRIS envelope
set excluding catch-alls.

**Access policy: UNKNOWN.** Both DOB hosts return **403 on `robots.txt`**, so
there is no published crawl policy to read. Silence is not permission — treat as
ACRIS was treated, and ask.

---

## Other structured sources — free, unmetered, never blocked

| source | rows |
|---|---|
| ACRIS parties | 46,456,160 |
| DOF assessment change | 48,408,326 |
| ACRIS legals | 22,688,577 |
| HPD violations | 11,148,085 |
| ACRIS remarks | 5,732,215 |
| DOB permits | 3,989,787 |
| DOF exemptions | 3,574,260 |
| DOF sales | 845,607 |
| HPD registrations | 203,236 |
| DOB certificates of occupancy | 143,061 |
| LPC buildings | 38,105 |

**163,919,090 rows total**, all pullable today at ~50–100 GB.

---

## Where documents are obtainable under a *published* permissive policy

`www1.nyc.gov/robots.txt` disallows only `/html/misc/`. Documents hosted there —
**BSA decisions, LPC designation reports, DCP/ULURP records** — fall under a
published policy that permits retrieval. Counts not yet taken; that is the next
inventory to run.

---

## ⚠ FT_ — the microfilm era, 35.8% of ACRIS

**6,092,729 documents** carry ids prefixed `FT_` ("film transfer"). Every one has
a reel/page citation; the sampled span reaches back to **1967 and earlier**.

**The trap, found 2026-08-05 and fixed:** **4,811,623 of them (79%) have NO
`document_date`** — only `recorded_datetime`. Any code reading `document_date`
drops 4.8 million documents as "undated", and they are precisely the EARLY ones.
A parcel timeline claiming birth-to-present was silently starting in the modern
era. `timeline.doc_date()` now falls back; `timeline.reel_of()` surfaces the
microfilm citation, which is the archival address a person would actually quote.

Practical consequence: **pre-electronic parcel history is reachable from the free
index today**, without a single image. Dates, types, parties and reel citations
for the whole microfilm era are already in hand.

---

## Staten Island — a SPLIT custodian, verified 2026-08-05

**ACRIS master contains ZERO documents recorded in Staten Island.** Manhattan
6,187,365 · Bronx 1,587,413 · Brooklyn 4,336,273 · Queens 4,925,665 · Staten
Island **0**.

But ACRIS *legals* carries **206,662 Staten Island parcel links across 192,950
distinct documents**, touching 3,794 blocks. Sampled at **both ends** of the
index to rule out ordering bias, those documents are **almost entirely RPTT and
RPTT&RET — real property transfer TAX RETURNS** (>98% in both samples),
administratively recorded in the Bronx and Manhattan. Zero FT_ records.

**So a Staten Island parcel's history is split across two systems:**

| what | where | note |
|---|---|---|
| transfer tax returns (RPTT) | **ACRIS** — 192,950 docs | states that a transfer happened + consideration |
| deeds, mortgages, easements, declarations | **Richmond County Clerk** | digitised to **1945** — earlier than ACRIS |

**This matters beyond Staten Island**: it proves a parcel history assembled from
ACRIS alone can be structurally incomplete rather than merely unread, and the
gap is invisible unless you check the custodian. RPTT presence without a
corresponding deed is the tell.

Richmond County Clerk: 130 Stuyvesant Place, 2nd Floor · (718) 675-7700 ·
richmondcountyclerk.com — Land Document Search by document number, party, date
range, block/lot, and book/page. Copies $0.25/page, certified $4/page. **Read
their published Terms before any programmatic access** — the portal states
"By searching, you agree to: Terms • Privacy • Disclosures", and those terms
govern, exactly as ACRIS's bandwidth policy governs there.

---

## Documents per PARCEL — the number the workflow actually runs on

Measured on LIC blocks (519 lots, 7,100 documents):

| | value |
|---|---|
| median documents/parcel | **12** |
| mean | 13.7 |
| p90 | 23 |
| max | 78 |

| approach | requests/parcel | rate at 50/day |
|---|---|---|
| whole-document endpoint | 24 | **~2 parcels/day → 760/year** |
| per-page fallback | 180 | ~1 per 3.6 days → 101/year |

**This is the scaling answer for parcel-by-parcel work.** The 17M figure governs
corpus acquisition; it does not govern walking a parcel's history. A median
parcel is twelve documents.

---

## Summary — three tiers

1. **Obtainable now, free, within budget:** DEVR + AIRRIGHT (1,265 documents,
   ~51 days) — *conditional on the whole-document endpoint working.*
2. **Obtainable now under published permissive policy:** BSA / LPC / DCP
   documents — uncounted, unstarted.
3. **Requires acquisition:** everything from DECL/EASE upward, all of DOB's
   ZD1/PW1 set pending a policy answer, and the full corpus.
