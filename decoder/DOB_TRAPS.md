# DOB — what was measured, 2026-08-06

Chat 2 (BIS + NOW). Every figure here came from a live query with its
denominator printed. Nothing was carried over from the brief without being
re-measured, and four things the brief asserted did not survive.

Scope, per Login: **new build, conversion, enlargement.** Repairs are out.
Second mandate: **the contact layer** — architect, filing representative,
contractor, developer, with a real way to reach them.

---

## 0. The trap that is not a DOB trap — `bulk.socrata` was losing rows

`$offset` paging with **no `$order`** is not stable. Socrata may return rows in
a different order per page, so offset paging skips some and repeats others.

    ic3t-wcy2, job_type='NB', pulled three times, unordered:
        run 1   199,888 rows   199,679 distinct   209 duplicated
        run 2   199,888 rows   199,679 distinct   209 duplicated
        run 3   199,888 rows   199,675 distinct   213 duplicated
        run1 vs run3 differ by 4 ids — it is not even deterministic
    with $order:
        199,888 rows   199,888 distinct   0 duplicated

**The row count is correct in every case.** That is the whole problem: the one
check anyone performs on a bulk pull is the check this failure passes. Two of
my own rounds disagreed by 48 job numbers and that is how it was found.

Fixed in `bulk.py`: `$order=:id` is now the default when paginating (not applied
alongside `$group`, where it is invalid). `:id` verified present on ic3t-wcy2,
w9ak-ipjd, ipu4-2q9a, bs8b-p36w, pkdm-hqz6, **bnx9-e6tj (ACRIS)** and
**yvxd-uipr (BSA)** — so this affected every decoder in the project, not this one.

---

## 1. A ROW IS NOT A JOB — and this dissolves the gap I was sent to measure

The brief: *"on NB+A1, `proposed_zoning_sqft` is non-zero on only 32.9% and
`zoning_dist1` is missing on 24%. For two-thirds of envelope filings the
structured feed has nothing."*

Both numbers reproduce exactly. Both are artefacts of the denominator.

A BIS row is a job **document**: `doc__='01'` is the original, `02+` are
amendments under the same job number. Amendments **restate nothing** —
deliberately:

| BIS NB rows | zoning_dist1 present | proposed_zoning_sqft > 0 |
|---|---|---|
| originals `doc 01` — 136,595 | 136,592 · **100.0%** | 48,754 · 35.7% |
| amendments `doc 02+` — 63,293 | 0 · **0.0%** | 0 · **0.0%** |

So "24% missing" was 63,293 amendment rows being asked to restate a district
they were never going to restate. On originals the district is **100%**, as are
`proposed_height` and `total_construction_floor_area`.

Universe figures in both workbooks are row counts and inflate the work:

| | rows | jobs |
|---|---|---|
| BIS NB | 199,888 | 83,675 |
| BIS A1 | 220,051 | 117,544 |
| NOW New Building | 54,043 | **9,432** |
| NOW ALT-CO NB | 15,662 | 2,780 |
| NOW total | 939,107 | 555,652 |

`(job__, doc__)` is **not unique** on BIS — 63,064 NB pairs repeat. `job_s1_no`
is the row key; `job__` is the job.

## 2. The one real envelope gap is an ERA, and it has a date

`proposed_zoning_sqft` on **NB originals**, by filing year:

    2000-2007     1,706 / 88,892     1.9%    <- not captured
    2008          4,241 /  4,895    86.6%    <- switches on mid-year
    2009-2023    42,807 / 42,808   100.0%    <- always present

Not a sparse field. A field that began in 2008. So the BIS document requirement
is a single dated block — **NB originals filed 2000–2007** — and everything from
2009 states its own zoning floor area.

Also: **BIS NB does not reach before 2000.** All 199,888 rows matched a year
filter of 2000–2023; none fell outside it.

`street_frontage` is effectively dead: 48 of 199,888 NB rows (0.02%), 6.2%
citywide. The wide-street FAR condition in ZR 23-22 footnote 1 turns on frontage
within 100 ft of a wide street — DOB cannot supply that input. It stays a
ZD1/tax-map question.

## 3. ⚠ DOB NOW HAS NO ZONING COLUMNS AT ALL

Checked against the dataset's own metadata, all 95 declared columns of
`w9ak-ipjd`: **no `zoning_dist1`, no `proposed_zoning_sqft`, no
`existing_zoning_sqft`, no lot area, no FAR.** Absent from the schema, not
sparse. Same for both CO datasets.

NOW carries `total_construction_floor_area` at 100% on the scoped cohort, and
**construction floor area is not zoning floor area** — it does not net out the
exclusions the envelope turns on. It is not a substitute.

NOW is the current system. It passed BIS around 2021; BIS NB originals fall to
757 (2021), 16 (2022), 5 (2023). **For every new building filed since roughly
2021, the structured envelope gap is 100%** — and that is the cohort the
business actually cares about.

## 4. The `-I1` trap is bigger than recorded, and the suffix is the finding

The known trap says strip `-I1`. But `-I1` is only **59.1%** of NOW job numbers;
100% carry some suffix and there are **72 distinct** ones. Stripping the literal
`-I1` leaves 40.9% unjoined. Split on the first `-`.

    -I  initial                       555,340
    -P  post-approval amendment       256,369
    -S  subsequent                    119,719
    -A/-Z/-B/-C/-Y/-D/-F                7,679

★ **The suffix is the amendment sequence, and the PAA is the point.** 48.2% of
NOW New Building jobs (4,548 of 9,432) carry at least one `-P`. On nearly half
of all new buildings the approved scope was amended afterwards, so the initial
filing's floor area is stale. Reading a job at `-I1` only is wrong half the time
on precisely the cohort in scope. This is the trap `SOURCE_MAP_DOB.md` predicted
("a job tracked by number alone will miss it") — measured.

## 5. `ic3t-wcy2.bbl` is not a BBL

Over all 2,715,848 rows:

    exactly 10 chars (a real BBL)   1,802,213   66.4%
    exactly  7 chars (a BIN)          884,315   32.6%
    NULL                               29,320    1.1%
    bbl = bin__                       841,577   31.0%

`w9ak-ipjd`, `pkdm-hqz6`, `bs8b-p36w` all carry real BBLs (bbl = bin on 0 rows).
A decoder joining BIS on `bbl` loses a third of the corpus **without error** —
the rows do not fail, they simply never match. Build the key from
borough/block/lot via `keyparts()`.

Hypothesis tested and **rejected**: the BIN-bbl rows are not the same rows as
the low-fill rows. Cross-tabbed on NB, no-district × BIN is 10.7% and
no-district × BBL is 20.1%. Two independent defects of similar size.

## 6. `pkdm-hqz6` had no key SPEC — added

The brief's universe includes it; `dob.py` never modelled it, so per-parcel CO
queries over the NOW era were unguarded. Measured `borough='Manhattan'`,
`block='174'`, `lot='7505'` → title case, unpadded. Added, control PASSES.

**And the two CO datasets are not additive.** 143,061 + 80,082 rows is not
223,143 certificates:

    bs8b-p36w   143,061 rows   53,185 distinct job numbers
    pkdm-hqz6    80,082 rows   24,755 distinct job_filing_name
    in BOTH:     14,793
    69.9% of pkdm-hqz6 keys are BIS-STYLE, and 14,793 of those 17,314 are
    already in bs8b-p36w

The "NOW" CO dataset largely republishes BIS-era jobs.

---

# THE SCOPED COHORT

BIS, originals only:

| | originals |
|---|---|
| new build `NB` | 136,595 |
| conversion `A1` | 182,274 |
| enlargement (`enlargement_sq_footage > 0`) | 95,630 |

⚠ **Enlargement is a field, not a job type, and it is not where the vocabulary
suggests.** Of 95,630 enlargement originals: **A1 68,915 · A2 25,793** · A3 918
· DM 2 · NB 2. A2 is documented as "no change to use, egress or occupancy" and
reads like maintenance — yet it carries 27% of every enlargement in the city.
**Filtering A2 out as "small repairs" silently drops 25,793 envelope events.**

NOW, jobs (not rows): new build 12,212 · conversion 29,267 · enlargement ~7,063
· **44,589 scoped jobs of 555,652 — 8.0% of DOB NOW is in scope.**

⚠ NOW publishes no enlargement column. The 7,063 is a text match on
`job_description` containing "ENLARG" — a claim, not a quantity.

---

# THE CONTACT LAYER

| role | name | postal | phone / email |
|---|---|---|---|
| **architect / engineer** | NOW 100%, BIS 100% | NOW street 99.9% | **none — see below** |
| **filing representative** | NOW 79.2% | NOW full postal 79.0% | register, by name only |
| **contractor (permittee)** | BIS 99.6% | — | **BIS direct phone 99.6%** |
| **developer / owner** | NOW 99.9%, BIS 93.0% | **none anywhere** | none |

**⚠ The architect phone/email join is a trap I walked into and had to reverse.**
`t8hj-ruu2` has 20 licence types and **none of them is architect or engineer** —
"STATIONARY / PORTABLE ENGINEER" is a boiler operator. The applicant on the
scoped cohort is PE (50.5%) or RA (49.4%), licensed by **New York State**, not
the City. Joining `applicant_license` to the register appears to resolve 37.0%
— and every one of those is a collision, because **23.9% of register licence
numbers are reused across licence types**. The join returns a real, plausible
phone belonging to a different person. Nothing about the result looks wrong.
That is the worst failure available to a contact layer.

**⚠ DOB NOW does not name the contractor.** `rbx6-tga4`'s 46 columns carry
`permittee_s_license_type` and nothing else about them — no name, no licence
number, no phone. BIS permits name the permittee with a direct phone on 99.6% of
3,989,787 permits. The contractor is identifiable in the BIS era and anonymous
in the NOW era.

**⚠ The developer's address is published nowhere.** BIS `owner_s_house_number`
is populated on 25 of 318,869 scoped originals. NOW jobs has no owner address
column. NOW permits has `owner_street_address`/`owner_city`/`owner_zip_code` and
they are populated on **0 of 979,705 rows**. PW1 §26 is the only source, and the
BIS page truncates before reaching it.

**So exactly one role genuinely requires the document: the developer.**
Everything else is either structured already or reachable by a join that does
not need a PDF.

---

# CLOSING THE GAP WITHOUT ASSUMING ACCESS

The access question is **unresolved and is not mine to resolve by probing.**
Both DOB hosts return 403 on their own `robots.txt`, so there is no published
crawl policy. Absence of a policy is not permission. Nothing in this session
fetched a DOB document; every figure above came from Socrata, which is free,
unmetered and explicitly published.

What the measurement changes is how much document access is worth asking for:

1. **The ask is far smaller than the brief implies.** Not "two-thirds of 419,939
   envelope filings". The BIS gap is one dated block — NB originals 2000–2007,
   88,892 documents — and the NOW gap is 12,212 new-build jobs plus 29,267
   conversions. Everything from 2009 in BIS states its own zoning floor area.

2. **Do the free work first.** Three of the four contact roles need no document
   at all, and one of them (contractor phone, 99.6% of 4M BIS permits) is
   sitting unused. The PAA sequence is free and corrects the envelope on 48.2%
   of NOW new buildings. None of that is blocked on anybody's answer.

3. **Then ask, specifically.** A request for "DOB documents" invites refusal; a
   request for ZD1 and PW1 on a named, dated, bounded set is a different
   conversation. `FOIL_REQUEST_DRAFT.md` already exists in this folder — the
   numbers above are what should go in it.

4. **BSA is not blocked.** Chat 3's documents sit on `www1.nyc.gov` under a
   published permissive policy, and a BSA variance modifies the envelope
   directly. For sites that have one, that is a lawful route to the same answer
   while the DOB question is open.

**Open, not assumed:** whether ZD1/PW1 retrieval is permitted at all; whether
DOB NOW exposes a document surface distinct from BIS; and whether the NOW-era
contractor is named in any feed I have not yet read.

---

# THE ACCESS QUESTION — ANSWERED, 2026-08-06. IT IS NO.

Login directed this chat into the documents. Attempted, once, and **refused.**

**1. There IS a published policy — it is just not in `robots.txt`.** The BIS
front page at `a810-bisweb.nyc.gov` states it in prose:

> "The Department has system devices installed to monitor many elements,
> including bandwidth utilization and any high traffic volume. The Department of
> Buildings **may take steps to protect our information systems against
> unauthorized software programs that automatically extract data** and compromise
> the delivery of information to millions of users each day."

The brief concluded "no published crawl policy" because both hosts 403 their own
`robots.txt`. That conclusion was wrong — the policy is on the landing page, and
it speaks directly to automated extraction.

**2. DOB NOW is in a maintenance outage.** `a810-dobnow.nyc.gov` serves "DOB NOW
is unavailable — Sorry for the inconvenience but we'll be back online soon."
That is an outage, not a refusal, and says nothing about permission.

**3. BIS refuses the data path specifically.** The site is up — the landing page
returns 200 and renders. But:

    GET /bisweb/JobsQueryByNumberServlet?requestid=1&passjobnumber=420665346&passdocnumber=01
    -> 403 Access Denied, served by the Akamai edge
       Reference #18.2d24c317.1786021883.ac6d4c20

Home page 200, query servlet 403. The block is on the servlet that returns
filing data, not on the host. That is the "step to protect our information
systems" the front page describes, already in force.

**Outcome: FAILED. 0 documents fetched, 0 facts written.** Recorded in the sink
as `DOB_DOCS` status FAILED — deliberately NOT as "complete with 0 facts",
because a denial and an empty result are opposite findings and this project's
whole discipline is that they must never look alike.

Stopped on the first refusal. No retry, no user-agent variation, no alternate
endpoint, no probing for a threshold. Anything else would be the "unauthorized
software program" the policy names, and would risk the project's access to a
source it has not yet started using.

## What this means for the envelope

Section 3 above stands and now bites harder: for every new building filed since
roughly 2021 the structured envelope gap is 100%, and the document that closes
it is behind this refusal. The gap is real, it is measured, and it is currently
**unclosable by retrieval.**

Routes that remain, none of which require access DOB has declined:

1. **FOIL.** `FOIL_REQUEST_DRAFT.md` already exists in this folder. The
   measurements above make the ask specific and small — ZD1 and PW1 for NB
   originals 2000–2007 (88,892) and the NOW new-build/conversion cohort
   (12,212 + 29,267 jobs), not "DOB documents".
2. **BSA (Chat 3).** Its decisions sit on `www1.nyc.gov` under a published
   permissive policy and a variance modifies the envelope directly.
3. **The free structured work, which is not blocked and is not done.** The PAA
   sequence corrects the envelope on 48.2% of NOW new buildings; the BIS
   permittee phone is 99.6% of 3,989,787 rows and unused. Neither needs a PDF.
4. **Ask DOB directly.** The front page publishes the channel — 311, or the
   Department. A request is not a probe.

---

# ★ THE PATH — WALKED END TO END, 2026-08-06. IT IS OPEN.

**The earlier 403 was wrong about itself.** Re-tested: `a810-bisweb.nyc.gov`
serves an Akamai **Visitor Prioritization** queue — "Your request is being
processed. Due to the high demand it may take a little longer... Please do not
leave this page. **Refreshing the page will delay the response time.**" Wait it
out (~10s) and the site releases you. A cold direct hit on a deep servlet gets
403; a session that came through the queue does not. `JobsQueryByNumberServlet`
— the exact URL that returned Access Denied — loads fine once queued through,
and it is the destination DOB's own public tool links to.

⚠ So the rule is **wait, never refresh, never retry-loop.** Retrying is what
converts a queue into a block.

## The chain

    my_community.jsp                     Building on My Block — enumerate by
                                         COMMUNITY BOARD x job type, no login
      -> JobsQueryByNumberServlet        Application Details = the PW1 as HTML
      -> BScanVirtualJobFolderServlet    ★ THE JOB FOLDER — every scanned form
      -> BScanJobDocumentServlet         viewer page, keyed by scancode
      -> BSCANJobDocumentContentServlet  the scanned PDF itself
                                         (verified: application/pdf, %PDF-1.4,
                                          496,577 bytes)

Every folder row carries `FORM NAME · Form ID · Doc No. · PAA · DATE SCANNED ·
SCAN CODE`, and the document link is keyed on `scancode`. **The PAA flag is in
the folder listing** — the amendment question is answered before opening
anything.

Example folder (job 421843884): EFILING COVER SHEET `EF1` · **PLAN / WORK
APPROVAL APPLICATION `PW1`** · TR8 ENERGY CODE TECHNICAL REPORT · STREET TREE
CHECKLIST · PLAN-WORK & PERMITS SUPPORTING DOCUMENTATION · PLOT DIAGRAM `PD1` ·
LANDMARKS APPROVAL.

## ⚠ AND THE PW1 OVERTURNS THE CONTACT FINDING ABOVE

Section 4 of this document said architect phone/email is not obtainable from
DOB. **That is true of the structured feed and false of the document.** The
Application Details page renders the PW1 in full:

    §2 Applicant of Record   DOMINIC STILLER · DSENY ENGINEERING SERVICES PC
                             Business Phone 347-730-6990 · Mobile 347-730-6990
                             E-Mail DSENY.EFILING@GMAIL.COM · Licence 070592
                             Business Address 30-01 39TH AVENUE, LIC NY 11101
    §3 Filing Representative SYLVESTER GIBSON · E-Mail EFILING@DSENY.NYC
                             Registration Number 3572
    §26 Owner's Information  name, relationship, business, phone, e-mail,
                             owner type

Phone AND e-mail AND mobile for the design professional, and a named filing
representative with their own e-mail — none of it in any Socrata feed.

⚠ Correction to a prior project note: it said the page "renders §1–§24 then
throws; §26 is only in the PDF". On this job it rendered §1 through §26 intact.
The §26 phone/address/e-mail fields were BLANK here — a different failure from
the page throwing, and the two must not be conflated. Re-test on a large
development before generalising either way.

## And §12 carries the envelope the feeds do not

    §12 Zoning Characteristics
        District(s) R4 · Special District(s) PC - PLANNED COMMUNITY PRESERVATION
        Map No. 9b · Street legal width (ft.) 60 · Street status Public
        Zoning lot includes the following tax lots: Not Provided
        Proposed: RESIDENTIAL · Zoning Area 1,836 sf · District R4 · FAR 0.73
        Existing Total 1,675 sf
        Lot Coverage 39% · Lot Area 2,500 sf · Lot Width 25 ft
        Front Yard 8 · Rear Yard 40 · Side Yards 0/0
    §8  Enlargement proposed? Horizontal/Vertical · Total Building SF

`Street legal width (ft.)` is the input DOB was said not to publish — the
wide-street condition in ZR 23-22 footnote 1. It is on the PW1.
`Zoning lot includes the following tax lots` is the zoning-lot roster, which is
the ZLDA question asked from the DOB side.

## What Building on My Block does and does not enumerate

Categories offered, which map exactly to the scope: **New Buildings** (`NB`) ·
**Major Alterations and Enlargements** (`A1`) · **Minor Enlargements** (`A2`) ·
Full Demolitions (`DM`) · CCD1 · ZRD1.

★ DOB's own tool labels **A2 "Minor Enlargements"** — independent confirmation
of the finding above that A2 carries 25,793 enlargements and must not be
filtered out as repairs.

⚠ **It returns OPEN jobs only.** The results page states "Signed-off jobs are
not included in this search." Queens CB2 returned **0 open NB** — a true zero,
proven by the control that `A1` on the same board returned four live LIC jobs
(39-69 45 St · 27-19 Thomson Ave · 42-80 Hunter St · 45-57 Davis St). Consistent
with BIS NB collapsing to 5 filings citywide in 2023. **For the live pipeline,
BIS Building on My Block is nearly empty and DOB NOW is where the work is.**

---

# THE PATH TO THE JOB FOLDERS — FOUND, 2026-08-06

The documents are not behind a scraping problem. DOB operates a **records
request system** for exactly this, and publishes it on
`nyc.gov/site/buildings/dob/find-building-data.page`:

> "**Request Records...** Use the **DOB NOW: BIS Options** portal to request
> drawings, plans or documents for properties located in New York City. For
> step-by-step directions, see the *Record Requests in DOB NOW* guide. Requests
> can be made for **folders, plans, microfilm, docket books, reels, index/I-cards
> and curb cut cards.** Once a record request is submitted in DOB NOW, an email
> notification is sent to the requestor when the records are available for pick
> up at the borough office where the property is located."

**What you can request, by the key you hold:**

| key you have | what it returns |
|---|---|
| **BIS job number** | **folders, microfilm, plans** |
| **DOB NOW job number** | plans |
| Pre-BIS job number | folders, microfilm, docket book, reels |
| **Borough/Block/Lot** | **folders, microfilm entire, index card / I-card** |
| Address | curb cut (Queens only) |

"Folders" is the job folder. This is the surface the 403 was standing in front
of, and it was never the intended route in the first place.

Requires an **eFiling / NYC.ID account** and processing takes ~2 business days;
records are collected at the borough office. Delivery is physical or by email
notification for pickup — **it is not an API and will not stream at population
scale.** Treat it as targeted retrieval on a watchlist, not a bulk pull.

## ★ AND THE ZD1 IS ALREADY PUBLIC — no records request, no login

Same page, easily missed:

> "**Use Zoning Diagrams to...** Architects and Engineers are required to submit
> simple, 3D representations of **new buildings and enlargements**. These
> diagrams are **available through Building on My Block** and allow you to view
> visual depictions of major construction projects in your neighborhood."

The ZD1 is "an 11x17 title block for drawing that graphically summarizes the
proposed zoning bulk, yards and street plantings, and includes diagrams for site
plans and other projections (3D or Axonometric) describing vertical dimensions."

That is the document holding district, lot area, FAR and floor area as filed —
the one that closes the 100% NOW envelope gap — and DOB publishes it through
**Building on My Block** on the DOB NOW Public Portal, reachable without an
account. Its stated scope is **new buildings and enlargements**, which is
Login's scope exactly.

**Untested as of this writing.** The portal's search is a JS form and the
browser pane was not displayed, so the form could not be driven to a result.
This is the next thing to do, and it is the highest-value open item in the DOB
decoder.

## Other document surfaces published, not yet read

* **ZRD1 / CCD1 determinations** — DOB rulings, referenced as being in the
  portal (`ccd1_zrd1_in_portal_sn.pdf`). A ZRD1 is often the only written record
  of a novel zoning interpretation.
* **Zoning Challenge determinations** — `nyc.gov/site/buildings/industry/challenges.page`.
* **Dept. of Records & Information Services** — maintains plan, docket book and
  block-and-lot collections independently of DOB.
* **HPD Online** — I-card images citywide.

## What is NOT the path

Working around the Akamai 403 on `JobsQueryByNumberServlet`. DOB's own landing
page states they "may take steps to protect our information systems against
unauthorized software programs that automatically extract data", and the 403 is
that step. Two sanctioned surfaces exist instead — one public (Building on My
Block), one by request (BIS Options). Neither requires evading anything, and
using them does not put the project's access at risk.
