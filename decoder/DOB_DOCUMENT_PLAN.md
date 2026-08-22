# DOB at scale — which documents, how to navigate, how they join the spine

Status 2026-08-06. **BIS chain: PROVEN end to end.** **DOB NOW: PARTIAL — the
document surface has not been found.** Marked throughout so nothing reads as
settled that isn't.

---

## 1. WHICH DOCUMENTS ARE NEEDED

Ranked by what they answer that no feed does. Anything a structured feed already
carries is NOT on this list — the cheapest document is the one you don't open.

### Tier 1 — the document is the ONLY source

| doc | where | what it uniquely gives | page |
|---|---|---|---|
| **PW1 §26** | job folder | **developer: name · relationship · business · street address · phone · e-mail · signature + date** | **LAST page** |
| **PW1 §26A** | same page | condo/co-op board contact — *required when a unit owner signs §26* | last |
| **PW1 §26B** | same page | lessee responsible for sign/marquee — a tenant contact | last |
| **PW1 §25** | last page | P.E./R.A. **embossed seal** + sign date. The details page prints the literal string *"( See paper form or check Forms Received )"* | last |
| **ZD1** | job folder | zoning diagram — district, lot area, FAR, floor area, yards, height **as filed**. The only envelope source for BIS pre-2008 and for ALL of DOB NOW | ? |
| **PD1** | job folder | metes and bounds. The details page says outright: *"To view metes and bounds, see the Plot Diagram (form PD-1)"* | ? |

★ **§26 is the last page of the PW1.** Proven on job 421843884 (page 5 of 5).
The PW1 is a fixed-format form, so the developer contact costs **one page read,
not five**. Read the last page first; only go earlier if the form revision
differs (footer carries the revision, e.g. `11/2022`).

### Tier 2 — document confirms, feed suffices day to day

`PW1 §12` zoning characteristics · `Schedule B / PW1B` zoning computations ·
`Schedule A / PW1A` occupancy by floor. All render on the details page. Their
HTML-vs-document agreement is **UNMEASURED** — the §26 result proves the
rendering drops fields silently, so these cannot be trusted until calibrated.

### Tier 3 — no document needed

Stage transitions (filing → permit → TCO → CO), permit dates, contractor phone
(99.6% of 3,989,787 BIS permits, structured), job/work types, status. Feeds are
complete here. Opening a document for these is wasted budget.

---

## 2. HOW TO NAVIGATE

### BIS — proven

    ENUMERATE   Socrata ic3t-wcy2 (finding aid — legitimate per
                RULE_DOCUMENTS_NOT_INDEXES: "which documents exist")
                or my_community.jsp (OPEN jobs only — see trap below)
      |
    FOLDER      BScanVirtualJobFolderServlet?passjobnumber=&passdocnumber=&allbin=
                CHEAP, TEXT, batchable. Returns per row:
                FORM NAME · Form ID · Doc No · PAA · DATE SCANNED · SCAN CODE
      |
    DOCUMENT    BScanJobDocumentServlet?...&scancode=XXX      (viewer)
                BSCANJobDocumentContentServlet?passjobnumber=&scancode=XXX  (PDF)

**The folder is the whole planning layer and it is free.** Before opening
anything it tells you: does a PW1 scan exist, how many rounds were filed, which
is operative, and whether a PAA exists. Harvest folders in bulk first; open
documents only for what the folder says is worth opening.

**Reading a document costs a rendered page + a vision read.** No text layer is
confirmed — the PDF is LEADTOOLS PDFWriter with one full-page image XObject per
page, and a `ctrl+F` test in the viewer did not open a find bar, so **whether a
text layer exists is UNRESOLVED**. Assume raster until measured. This single
question decides whether scale is "fetch and parse" or "fetch and look", so
**measure it before building anything.**

**Rendering:** the in-app preview pane cannot composite the PDF plug-in — the
viewer is a black rectangle — and top-level navigation to the content servlet
triggers a save dialog. The user's own Chrome renders it inline and screenshots
composite. `ctrl+End` jumps to the last page (which is where §26 is).
Wheel-scroll does not reach the plug-in; the page-number box did not take typed
input. **Keyboard navigation is the reliable control.**

**Pacing:** `a810-bisweb.nyc.gov` runs an Akamai Visitor Prioritization queue —
*"Please do not leave this page. Refreshing the page will delay the response
time."* **Wait it out; never refresh, never retry-loop.** A cold hit on a deep
servlet 403s; a session that came through the queue does not. Retrying is what
turns a queue into a block.

### DOB NOW — ★ FOUND 2026-08-06, and it changes the plan

    Job Number search (or BBL -> BIN)
      -> PROPERTY PROFILE          BIN-level. Spine fields, see §3.
      -> "BUILD: Job Filings" grid  View | Job# | Filing# | Job Type |
                                    Work Type(s) | Work on floor(s) | Address |
                                    Filing Status | Job Description
      -> click the View icon
      -> FILING DETAILS modal, per JOB#+FILING#, eleven sections:
             Plans/Work (PW1)          Zoning Information
             Scope of Work             Technical Report (TR1)
             TR8 Energy Progress       As Built Energy Analysis (EN2)
             Work Permit (PW2)         AHV Permit
             Withdrawal / Supersede    Statements & Signatures
             Documents                 [+ "Job Summary" button]

⚠ **Grid links need a DOUBLE-CLICK.** A single click only selects the row. This
cost an hour and reads exactly like "the link is dead".

## ★★ THE NOW ENVELOPE GAP IS NOT A DOCUMENT PROBLEM

`Zoning Information` is a **structured section on the filing**, and it carries
what the Socrata feed does not have a column for. Job Q00564746 filing C7,
2-11/2-33 50 Avenue (Hunters Point), verbatim:

    Zoning Lot Details
      Lot existed prior to December 15, 1961?   Yes
      Tax Lot(s)                                1
    Zoning District(s)        Auto Populated | District | Area (Sq. ft.)
                              No             | M1-5     | 56000
                              No             | M1-4     | 20000
      Overlay(s) N/A   Special District(s) Long Island City Mixed Use District
      Map Number 8d
      Is Zoning Lot Certification (Zoning Exhibits) required?   Yes
      Lot Area Total 76000.00   Lot Width 400   Lot Type Corner
      Lot Coverage / Open Space / OSR   Not Applicable
    Street Details   Street Legal Width (ft) 60 | Street Status Public |
                     new private street? Not Applicable
    Yard Details     yards? Yes | Front 0 | Side 0 | Rear 30 |
                     Rear Yard Equivalent Not applicable
    Height & Setback ...

**Corrections this forces to earlier findings in `DOB_TRAPS.md`:**

1. *"DOB NOW has no zoning columns at all — for every new building filed since
   ~2021 the structured envelope gap is 100%."* True of **`w9ak-ipjd`**. **False
   of DOB NOW.** The portal publishes a full per-filing zoning statement. The gap
   is between the Socrata extract and the portal, not between the City and us.
2. *"`street_frontage` is dead, so DOB cannot supply the wide-street input for
   ZR 23-22 footnote 1."* **`Street Legal Width (ft) = 60`, plus Street Status,
   is on every filing.** DOB supplies it — just not in the extract.
3. **The split-district problem is stated, not inferred.** `M1-5 56,000` +
   `M1-4 20,000` with `Lot Area Total 76,000` — the applicant's own split, and
   the parts sum to the whole. This is what the FAR work has been reconstructing
   from DOF tax-map geometry ∩ nyzd. Use the portal as the primary and the
   geometry as the check, not the reverse.

**Free self-checks this section hands you:**
* Σ district areas == Lot Area Total (56,000 + 20,000 == 76,000 ✓). A filing
  that fails this is a finding.
* `Auto Populated: No` — ⚠ DOB flags whether the APPLICANT keyed the value or
  the system filled it. An applicant-keyed district is a claim; treat its
  confidence accordingly. **Carry this flag onto every fact derived from it.**
* `Is Zoning Lot Certification (Zoning Exhibits) required? Yes` — the DOB-side
  flag that a zoning-lot instrument (the ACRIS ZLDA) should exist. A `Yes` with
  no recorded instrument found is a real finding.
* `Lot existed prior to December 15, 1961?` — the non-conforming-rights
  question, answered on the filing rather than inferred from the 1961 map.

⚠ **Filing suffixes run well past I/P/S.** This job's filings are
`C7 · B5 · B4 · B3 · B2 · B1`, all Job Type "New Building", work types GC / PL /
SP-SD. The citywide census found `I·P·S·A·Z·B·C·Y·D·F`, 72 distinct. Parse the
suffix, never match a literal.

## ★ TESTED 2026-08-06 — THE NOW PW1 IS TEXT, BUT IT IS NOT THE DOCUMENT

Filing Details -> **Plans/Work (PW1)** renders as **structured HTML, not a
scan**. Job Q00564746 filing C7, verbatim:

    Location    2-33 50 AVENUE · QUEENS · Block 17 · Lot 1 · BIN 4625206 · CB 402
    STAKEHOLDERS
    APPLICANT   Registered Architect · Licence 018855
                PAUL CARR · S9 Architecture and Engineering DPC
                322 8th Avenue, New York NY 10001
    OWNER       Owner Type: Partnership
                PETER PAPAMICHAEL · Title: MEMBER
                Business Name/Agency: 50TH & 5TH LIC LLC
    FILING REP  Class I/Preparer · MaryAnn Brown
                GEORGE E. BERGER & ASSOCIATES
                42 Oak Ave - 3rd Fl, Tuckahoe NY 10707
    DELEGATED   Stuart Berger · PE - 072476

★ Every party is NAMED and ROLE-TYPED. `Title: MEMBER` is the authority field —
the DOB NOW equivalent of the paper form's `Relationship to Owner`. This is
role-in-the-context-of-the-job, free, for all 49,616 scoped NOW jobs, and it
independently corroborates the name the historical permits feed gave for the
demolitions on the same lot.

⚠ **AND IT STOPS SHORT OF REACH.** The owner block carries name, type, title and
entity — **no street address, no telephone, no e-mail.** The applicant and
filing representative get business addresses; the owner gets none.

    portal gives you   BRUCE WEILL / AUTH. SIGNATORY / BUD SOUTH LLC
    portal withholds   (212) 672-1000  ·  BRUCE.WEILL@TFCORNERSTONE.COM

**So the e-mail-domain decode — the step that turns a shell into TF Cornerstone —
is NOT obtainable from the portal.** It needs the filed PW1 itself.

## ★★ CORRECTION 2026-08-06 — DOB NOW **DOES** SERVE DOCUMENTS PUBLICLY

I concluded "DOB NOW publishes no documents" from ONE amendment (C7) whose
Documents accordion was empty. **That was a sample of one and it was wrong.**

Filing **P2** of the same job has a document, with a live handler that is NOT
auth-gated:

    ng-click="downloadDocument(docgridtoptions)"      <- fires for the public

    Documents
    Created On   Document Name                            Status
    2023-12-27   Other 1 Documents - Prior to Approval    Accepted

It resolves to a plain, fetchable URL:

    https://a810-dobnow.nyc.gov/Publish/DocumentStage/PortalDownloadedDocuments/
        {BOROUGH}/{JobId}/{Filing}/{Category}//{id}/{filename}.pdf

    e.g. .../QUEENS/Q00564746/P2/Supporting Documents//202608060216349251053000341/
         Other 1 Documents - Prior to Approval.pdf

★ **So documents ARE public, and availability VARIES BY FILING.** Some filings
carry none; others carry supporting documents. Never conclude from one filing.

⚠ **Two different gates, and conflating them was my error:**
* the **status cells** on the Job Summary (ZD1 / TPP / AHV / Work Permit / CO /
  LOC) carry `ng-click="!grid.appScope.IsPublicPortalUser"` — they render text
  for the public and open for nobody. Those are status, permanently.
* the **Documents grid** inside Filing Details carries `downloadDocument(...)`
  with **no gate at all**. That is a real, public document surface.

## ★ THE OBJECTIVE: FIND A PW1 IN THE DOCUMENTS GRID

Login, 2026-08-06: *"your move for projects will be to literally find any pw1 in
the documents of dob now and that is the gold."*

What was actually retrieved on P2 was an 11-page **plan-examiner markup** —
reviewer comments in red ("Narration incomplete. See Section 8.4.2"), drawing
revision block. Valuable for the plan-exam narrative, **useless for §26**.

**The open question is now sharp and cheap to test:** does any filing publish a
document whose category or name is a **PW1**? The grid names the category
before you open anything, so categories can be enumerated across many filings
without fetching a single PDF.

⚠ **And the filing to check is `-I1`, the INITIAL** — because §26 is executed
only on the initial filing (see `DOB_FOLDER_READING.md`). Both filings tested so
far (C7, P2) were amendments. **I1's Documents grid has NOT been checked on any
job.** That is the next test and it is the one that matters.

Method that works (portal is flaky; this sequence survived):
    /publish/index.html#!/COVJobSummary?JobId={JOB}&UserId=PublicPortalUser
      -> set page size 20, page to the filing
      -> click the job-number link (fires showInfoFromSummary)
      -> click "Documents" to expand
      -> the anchor's ng-click is downloadDocument(...); it opens a real PDF URL
⚠ The modal does NOT rebind when clicked from a stale state — reload the route
  before opening a different filing or you will read the previous one's data.

## ⚠ THE NOW DOCUMENT PROBLEM — partially solved

Same modal, other sections:

* **Statements & Signatures** — expands to nothing. No jurat, no signature block.
* **Documents** — expands to nothing, **and fires NO network request at all.**
  It is a client-side toggle over data already in the Filing Details payload.
  So the payload itself carries an empty document list for this filing; the
  portal is not withholding it behind a second call it could be asked for.

⚠ Tested on ONE filing (C7, an amendment). Whether an initial `-I1` filing ever
populates Documents is **UNRESOLVED** — the portal hung repeatedly and the test
did not complete. Do not conclude "DOB NOW publishes no documents" from this.

### Routes not yet tried, in order of promise

1. **The `Job Summary` button** on the Filing Details header — untested. If it
   renders or generates a filing summary PDF, that is the closest thing to the
   document the portal offers without a login.
2. **Inspect the Filing Details payload directly** across many filings to see
   whether the document array is ever non-empty — one diagnostic answers it for
   the whole era, rather than clicking through filings one at a time.
3. **eFiling / NYC.ID login.** DOB NOW is a self-service system; documents are
   normally visible to the applicant and owner. This is an account question, not
   a technical one, and it is Login's to decide.
4. ⚠ **NOT B-Scan.** DOB NOW jobs are not in the BIS scan system. The BIS path
   proven earlier does not reach them.

### What this means for the contact layer, by era

    pre-1989      I-card (residential only)          name, no reach
    1989-2013     bty7-2jhb                          name + ADDRESS + PHONE ~95%
    2008+         B-Scan PW1 §26                     name + role + address +
                                                     phone + e-mail  <- full
    2016+ NOW     portal PW1                         name + ROLE + entity only
                  the filed PW1                      UNREACHED

★ The modern era is the WEAKEST for reach and the STRONGEST for role. The
1989-2013 era is the reverse. Neither alone gives a profile; together they do.

### DOB NOW — still open

Public portal, **no login required to search**:
Address · Borough/Block/Lot · BIN · Job Number · Device · Licensee (*includes
BIS records*) · Violations & Notices of Deficiency · Application Search ·
Electrical Special Installation.

Building on My Block (NOW flavour) filters by **Alterations · New Buildings ·
Alteration CO · ALTCO-NB** and by zoning-challenge status — the scoped cohort
exactly. It states: *"To search for BIS jobs, use the BIS Building On My Block
portal."* Two separate tools, two eras.

⚠ **BIS Building on My Block returns OPEN jobs only** — "Signed-off jobs are not
included in this search." Queens CB2 returned 0 open NB (true zero; control:
A1 on the same board returned 4 live LIC jobs). For the live pipeline BIS is
nearly empty. **DOB NOW is where current work is, and its document surface is
the biggest open item in this decoder.**

**NOT YET FOUND:** whether the NOW public portal exposes filing documents at
all, and if so by what URL. The BIN cell in BBL results selects rather than
navigates. This is the next thing to solve.

---

## 3. THE SPINE RELATION

**DOB is keyed on BIN. The spine is keyed on BBL. That is the whole problem.**

A BIN is a *building*; a BBL is a *tax lot*. They are not 1:1 — one lot can
carry several BINs, and a building can outlive the lot it sat on.

### The resolver DOB publishes

DOB NOW's **Borough/Block/Lot search is the official BBL→BIN resolver**, and its
result columns are the spine contract:

    Tax Lot | Address | House# Range | Obsolete | BIN

★ **`Obsolete` is a lot-lineage flag published by DOB.** That is directly the
problem `project_bkrea_lot_lineage` describes — retired BBLs dropping silently
out of any gate-keyed pull. DOB states it rather than making us infer it. This
should rank as a lineage source alongside SI/SC filings and DOF's alteration
book. **Untested against a known-retired lot — do that before relying on it.**

### Join rules, all measured

1. **NEVER join BIS on its `bbl` column.** 32.6% of `ic3t-wcy2.bbl` is a 7-char
   BIN, 66.4% a real BBL, 1.1% null. Rows don't fail — they silently never
   match. Build the key from borough/block/lot via `dob.keyparts()`.
2. **NEVER join on address.** Building on My Block listed job 421841813 as
   *42-80 HUNTER STREET*; the job's own pages say *42-57 27 STREET*. Same BIN,
   same Block 431 Lot 30 — a corner parcel where two systems chose different
   frontages.
3. **Key format is per DATASET, not per agency.** Three conventions across four
   DOB datasets (see `dob.py SPEC`). A padded block against an unpadded dataset
   returns zero rows and reads as "never filed on".
4. **A row is not a job.** BIS `doc 01` is the original, `02+` amendments that
   restate nothing. DOB NOW splits one job across `-I/-P/-S` filings. Count jobs.
5. **SI and SC job types are lineage events** — the DOB side of subdivision and
   condo-lot creation. Rank above PLUTO, below recorded instruments.

### Where DOB meets ACRIS

The PW1 states the zoning lot from the DOB side: `§12 Zoning lot includes the
following tax lots` — the roster. ACRIS states it from the instrument side (the
ZLDA). **The same fact from two independent sources is the strongest check
available**, and a disagreement is a finding, not an error to reconcile away.
Job 421841813's own description — *"PART OF A LARGER ZONING LOT WITH TWO TAX
LOTS"* — is exactly that join, written in plain language by the applicant.

⚠ And the standing rule: a DOB filing describes what is being built or CLAIMED.
A recorded instrument changes what MAY be built. DOB floor area never enters
`envelope_transferable`.

---

## 3b. THE DEVELOPMENT HISTORY — how far back, and how the two systems join

**BIS and DOB NOW are one timeline cut in half by a system migration, not two
sources.** NOW's first filings are 2016 (9 of them), it ramps from 2018 and
overtakes around 2021; BIS NB collapses to 757 originals in 2021, 16 in 2022,
5 in 2023. So a development that began under BIS and finished under NOW has its
head in one system and its tail in the other, and neither alone shows the arc.

### ⚠ THE JOIN IS THE BBL, NOT THE BIN — because a new building gets a NEW BIN

This is the trap that silently truncates a development history. Compare the two
parcels walked today:

    Block 431 Lot 30   BIN 4005120   an ORIGINAL BIN (low number)
    Block 17  Lot 1    BIN 4625206   a NEWLY ASSIGNED BIN (46xxxxx)

**BIN vintage is legible in the number.** A high BIN on a lot means a building
was *created* there — and the building it replaced carried a different BIN whose
demolition, and whose entire prior life, hangs off the OLD one. Assemble a
history on BIN and it begins at the new building, as though nothing preceded it.

So: **anchor on the BBL, resolve every BIN that lot has ever carried, and union
their filings.** The Property Profile supports this directly —
`Buildings on Lot`, `Additional BINs for Building`, `Condo`, and
`Alternate Addresses` with house-number ranges (which is also what reconciles
"2-33 50 Avenue" in Socrata against "2-11 50 Avenue" on the profile: the range
is 2-11 – 2-57).

And guard the lot itself: DOB NOW's BBL search publishes an **`Obsolete`** flag,
and `SI`/`SC` job types are the subdivision/condo lineage events. A retired BBL
drops out of any gate-keyed pull silently.

### ★ HOW FAR BACK THE DOCUMENTS GO — MEASURED 2026-08-06

**B-Scan begins in 2008.** Sampled NB doc-01 jobs, one or two per year, folder
opened for each:

    2000  job 301032451   NO SCANNED DOCUMENTS FOUND FOR THIS JOB
    2003  job 500567237   NO SCANNED DOCUMENTS FOUND
    2005  job 500791716   NO SCANNED DOCUMENTS FOUND
    2007  job 402631835   NO SCANNED DOCUMENTS FOUND
    ------------------------------------------------- the line
    2008  job 410058075   15 documents   PW1 · Schedule A · Schedule B ·
                                         PLOT DIAGRAM · asbestos exemption · TR
    2010  job 320139532   92 documents
    2012  job 420533355   12 documents
    2014  job 420944982   36 documents   (+ CERTIFICATE OF OCCUPANCY: APPLICATION)
    2016  job 421395822   36 documents   (+ CO objections, VERIFY TAX LOT)
    2018  job 321629181  114 documents
    2020  job 321591782   48 documents
    2021  job 440664238   NO SCANNED DOCUMENTS  ⚠ see caveat

And the five old jobs on Queens 17/1 — 1992, 1997, 1998, 2003 ×2 — all returned
the same explicit message. **This is a real empty, not a failure:** HTTP 200,
page renders premises / BIN / block / lot / job type correctly, and DOB states
"No Scanned Documents Found For This JOB" in words.

## ★★ 2008 IS THE SAME LINE THE ZONING FIELD APPEARS ON

From `DOB_TRAPS.md`, `proposed_zoning_sqft` on NB originals:

    2000-2007    1.9%      <- field effectively not captured
    2008        86.6%      <- switches on mid-year
    2009-2023  100.0%

**The scanned folder and the structured zoning field begin in the same year.**
That is not coincidence — it is eFiling. Before 2008 DOB was a paper process:
nothing keyed, nothing scanned. From 2008 the filing is electronic, so the data
is in the database *and* the document is in B-Scan. One boundary, two symptoms.

⚠ **Coverage after 2008 is not 100%.** The 2021 NB sampled returned zero
documents. Presence must be checked per job, never assumed from the year.

⚠ **My own error, recorded:** I computed each folder's scan date range by
sorting `MM/DD/YYYY` strings lexicographically, which produced impossible
ranges ("01/15/2021 to 12/28/2020"). The document COUNTS and the
found/not-found flag above are sound; the date ranges were wrong and are not
reported. Parse the date before ordering it.

## ★★★ 2008 IS THE DIGITAL HORIZON — THREE INDEPENDENT SYSTEMS AGREE

    B-Scan scanned job documents      first folder 2008     (measured today)
    proposed_zoning_sqft on NB        1.9% -> 86.6% in 2008 (measured)
    DOF Digital Alteration Book       2008-05-20            (dof_lineage.py)

Three separate agencies' systems, one boundary. **2008 is where NYC's
development record becomes digital**, and it is simultaneously the first year
you can read a filed document, the first year the zoning figure is keyed, and
the first year lot lineage is published rather than inferred.

Consequence for site tracking: **before 2008 you can establish THAT something
happened and to whom, but not WHAT was filed and not how the lot changed.**
1989–2007 is index-only on the DOB side and lineage-blind on the DOF side.

## TRACKING A SITE, NOT A LOT — the correction

A site is ground. Its lot number, its BINs, its addresses and its owners all
change, and a query keyed on today's BBL silently drops whatever was filed
against yesterday's identifiers. Two distinct mechanisms, and they are NOT the
same problem:

**1. BINs change while the lot stays put.** Queens 17/1 carried five BINs —
`4436571 · 4436572 · 4436573 · 4436574` demolished, `4625206` built — under one
unchanged lot number from 1992 to today. PLUTO `appbbl` for lot 1 is **None**,
because *the lot never changed*. Lineage tooling keyed on lot changes will find
nothing here and be correct, while four buildings' histories still hang off
retired BINs. Union every BIN the lot has ever carried.

**2. Lots change while the ground stays put.** Same block: PLUTO shows
`lot 28 appbbl 4000170021` and `lot 29 appbbl 4000170028`, both dated
2009-05-05 — a real 21 → 28 → 29 chain. Here `appbbl`/DAB is exactly right and
the BIN union would miss it.

**A site tracker needs both, and must not assume one implies the other.**

## SEGMENTING BY DEVELOPMENT CYCLE

Scope is new build / conversion / enlargement. But those alone cannot be ordered
into a history, because a site runs through REPEATED cycles and nothing in the
scope marks where one ends.

**Demolition is the boundary.** It is not itself a development type and does not
belong in the output as one — but without `DM` (and BIS `A2` "removal of partial
collapsed section", which is a demolition wearing an alteration's clothes) the
cycles run together. Queens 17/1:

    cycle 1   ...1992 - 2003   Judson Art Warehouse -> Fortress
                               ends: collapse (2003-02) + DM permits (2003-03)
    cycle 2   2021 - 2025      50th & 5th LIC LLC
                               starts: DM x3 (2021-10) -> NB -> CO (2025-05)

So the pull is scope + `DM` as a segmenter, and the output reports cycles, each
with its own type / envelope / players / stage.

### The document floor, stated plainly

| what | earliest | how |
|---|---|---|
| **Scanned DOB documents online** | **2008** | B-Scan Virtual Job Folder — free |
| DOB NOW filing documents | 2016 | portal Filing Details → Documents |
| Job records (no documents) | 2000 | `ic3t-wcy2` |
| Permit records (no documents) | **1989** | `bty7-2jhb`, 1989-05-11, 2.4M rows |
| Pre-2008 documents | earlier | **records request only — physical** |

So: **development documents are visible online back to 2008 and no further.**
1989–2007 is an index-only window — you can see that a job existed, its type,
its owner, its permittee and (in `bty7-2jhb`) an owner mailing address and
phone, but not a single page of what was filed. Those documents exist as
folders, microfilm, docket books and reels, and reaching them is a records
request with a borough-office pickup.

### How far back each layer reaches

| layer | reach | how | cost |
|---|---|---|---|
| **DOB NOW** | 2016 → now | portal Filing Details — zoning, PW1, signatures, documents | free, structured |
| **BIS + B-Scan folder** | ~2000 → 2023 (NB measured 2000–2023, none earlier) | `BScanVirtualJobFolderServlet` → scanned PW1/PD1/ZD1 | free, 1 page-read each |
| **Pre-BIS** | earlier | **records request only** — Pre-BIS Job Number returns folders, microfilm, docket books, reels; BBL returns folders, microfilm entire, **index card / I-card** | eFiling account, ~2 business days, borough pickup |
| **I-cards** | pre-1938 buildings | HPD Online, citywide | free |
| **BSA** | 1930s–40s, **still in force** | calendar numbers ("148-48-A" = 148th application of 1948); grants bind successors | free PDFs (Chat 3) |
| **ACRIS** | ~1966 digital horizon | the recorded instruments underneath all of it | Chat 1 |

⚠ **BIS NB does not reach before 2000.** All 199,888 NB rows matched a
2000–2023 year filter; none fell outside it. Anything earlier is a records
request, not a query. That is the hard floor on what can be assembled online.

### What to assemble, per job, once the timeline is ordered

* **development type** — NB · A1 conversion · A2/A1 with `enlargement_sq_footage
  > 0` · Alt-CO · ALT-CO NB (new building keeping existing elements, used to
  preserve non-conforming rights) · DM. DOB's own tool calls A2
  "Minor Enlargements", so A2 is in scope, not maintenance.
* **details / envelope** — NOW: `Zoning Information` (districts + per-district
  area, lot area, lot width/type, street legal width, yards, height & setback,
  1961 flag, zoning-lot-certification flag). BIS: §12 + the ZD1.
* **players** — applicant of record (§2, with phone/mobile/e-mail), filing
  representative (§3), **owner/developer (§26 — document only)**, permittee
  (permits feed, direct phone 99.6% in BIS), superintendent, site-safety manager.
* **timeline** — filed → plan exam (objections) → permit issued (FO/EA are the
  irreversible start; FN/SF/EQ/CH are only mobilisation) → TCO (practical
  delivery) → final CO. Renewals without sign-off = stalled. A `-P` amendment
  changes the envelope mid-stream on 48.2% of NOW new buildings.

The narrative order that makes it legible is unchanged: **intent → parties and
envelope → what was submitted and resubmitted → what DOB pushed back on → what
was authorised → what legally exists.**

## 4. ORDER OF WORK

1. **Resolve the text-layer question.** One measurement; it decides everything.
2. **Find the DOB NOW document surface.** The entire 100% envelope gap is there.
3. **Bulk-harvest BIS folders** for the scoped cohort — cheap, text, batchable,
   and it sizes the document work before any of it is done.
4. **Calibrate §12/Schedule A/B** HTML-vs-document on ~25 jobs, so the Tier-2
   fields can be trusted or condemned with a number.
5. Only then open documents at volume, last page first.
