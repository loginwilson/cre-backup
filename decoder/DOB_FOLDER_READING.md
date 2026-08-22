# Reading a DOB job folder — the narrative, not the forms

# ★★ HOW TO READ A PW1 CHAIN — Login, 2026-08-06. READ THIS FIRST.

## §26 IS SIGNED ON THE INITIAL PW1 ONLY

> "many times owners only sign the first pw1 and then arent required to anymore
>  unless they change to a new owner filing. this usually doesnt happen in terms
>  of a change, but when directors of real estate in a company change for
>  instance, it requires the new one to fill it out"

**This inverts the retrieval strategy.** I had been reading the LATEST PW1 in a
folder expecting the freshest contact. Wrong — the later scans are PAAs and
their §26 is BLANK. The owner executes once, at the initial filing, and is not
required to re-execute for an amendment.

    READ THE EARLIEST PW1 (Initial Filing) for §26.
    Then scan LATER PW1s only to detect a NEWLY POPULATED §26.

★ **A populated §26 appearing mid-chain is an EVENT, not a duplicate.** It means
the authorised signatory changed — commonly a new director of real estate at the
same company, occasionally a genuine change of owner. That is a party-change
signal available nowhere else, and it is exactly what a "who is the contact NOW"
question needs.

⚠ So a blank §26 on a late PAA is **not missing data**. It is the form working as
designed, and recording it as "no contact found" would be a false negative.

## §4A PAIRS THE AMENDMENT TO WHAT IT AMENDS

`4A Indicate existing document number affected by filing: 01`

So the chain reconstructs itself: **doc 01 → 01, 02 → 02, 03 → 03.** A PAA names
its parent. Timelining a property means following that pairing, not treating
each scan as a separate filing. §4 also states which kind it is —
`Initial Filing` vs `Post Approval Amendment (PAA)` vs `Subsequent Filing` vs
`Reinstatement` vs `Withdrawal` — so the role of each scan in the chain is
declared on its own face.

## THE PROFESSIONAL TEAM CHANGES TOO, AND THE CHAIN SHOWS IT

Job 421374845 (131-02 40 Road, Queens · 179 documents · 32 PW1s):

    2017 INITIAL   §2 Anthony K NG · Angelo Ng & Anthony Ng Architects Studio PC
                      718-457-1151 · INFO@ARCHITECTSSTUDIONY.COM · lic 24574
                   §3 Leo Vita Berrardi, same firm, reg 003397
    2026 PAA       §2 Ning LU · LU NING ARCHITECTURE PLLC
                      718-395-8637 · NINGARCH@GMAIL.COM · lic 032658
                   §3 BMB BUILDING CONSULTING INC, reg 004462

Nine years, architect and expeditor both replaced. Reading only the initial
filing gives a stale professional team; reading only the latest gives no owner.
**You need the first for §26 and the last for §2/§3.**

## THE RULE, COMPACT

    §26 owner contact      -> EARLIEST PW1 (Initial Filing)
    §26 changed            -> any later PW1 with a POPULATED §26
    §2/§3 current team     -> LATEST PW1
    chain structure        -> §4 filing type + §4A parent document number

⚠ Environment note: paging a large scan is unreliable here — the PDF plug-in
stops taking keyboard focus and the page-number box rejects input on heavy
documents. `ctrl+End` worked on a 5-page scan with a small folder and failed on
jobs with 179 and 282 documents. Read small scans first; the failure is in the
viewer, not the data.

---

# ★ FIRST REAL DECODE — PW1, job 421843884, scancode SC181108001

Read in the browser's own PDF viewer (no download, nothing written to disk).
**`pages_read 2 / pages_total 5`** — page 1 and page 5. Pages 2–4 NOT read.

## The finding: the details page drops exactly the reach fields

`§26 Property Owner's Statements and Signatures`, **page 5**, as printed:

    Owner Type            [X] Individual
    Name (please print)   DOMINIC STILLER
    Relationship to Owner OWNER
    Business Name/Agency  DSENY ENGINEERING SERVICES PC
    Street Address        30-01 39TH AVENUE
    City / State / Zip    LONG ISLAND CITY  NY  11101
    Telephone Number      (347) 730-6990          Fax: (blank)
    E-Mail Address        DSENY.EFILING@GMAIL.COM
    Signature and Date    [signed] 11-5-25

The same §26 on `JobsQueryByNumberServlet`:

| field | details page | document |
|---|---|---|
| Name | DOMINIC STILLER | DOMINIC STILLER |
| Relationship to Owner | OWNER | OWNER |
| Business Name | DSENY ENGINEERING SERVICES PC | same |
| Owner Type | INDIVIDUAL | Individual |
| **Business Address** | **blank** | 30-01 39TH AVENUE, LIC NY 11101 |
| **Telephone** | **blank** | (347) 730-6990 |
| **E-Mail** | **blank** | DSENY.EFILING@GMAIL.COM |
| **Signature / date** | absent | signed 11-5-25 |

**The rendering keeps identity and drops reach.** Not intermittent, not a bad
record — a structural cut, and it is the same cut Socrata makes
(`owner_s_house_number` populated on 25 of 318,869 scoped originals; no owner
phone or e-mail column exists at all). The details page and Socrata are two
views of the same keyed BIS record. The scan is a different source: what the
filer actually wrote and signed, which DOB never keyed.

⇒ **No amount of reading details pages will ever yield a developer phone.**
For the contact mandate the document is not the fallback, it is the only source.

## ★ THE SCALING LEVER: §26 IS THE LAST PAGE

§26 sits at the END of the PW1 — page 5 of 5 here, and the PW1 is a fixed-format
form. So the developer contact costs **one page read, not five.** Read the last
page first; only go earlier if the form revision differs.

Also on that last page and nowhere in the rendering:
* the **P.E./R.A. embossed seal** with its own sign date (10-3-25) — §25, which
  the details page fills with the literal text *"( See paper form or check
  Forms Received )"*
* **§26A Condo/Co-Op Board** — name, title, street, phone, e-mail. Blank here,
  but this is the contact path for a condo/co-op, and the form states §26A is
  *required if a unit owner signed §26*.
* **§26B Lessee Responsible for Annual Sign or Marquee Permit** — a tenant
  contact block.
* footer `DOB Reference Number: T00002563466 · User Ref ID: 3969`, form rev 11/2022

## Provenance is printed on the document

Page 1 carries a barcode reading `DEPT. BLDGS · 421843884 Job Number ·
SC181108001 Scan Code`. **The document states its own citation** — job number
and scancode — so a decoded page can be tied back without trusting the URL it
came from.

## ⚠ What this one job does NOT prove

Here the owner IS the engineer — Dominic Stiller of DSENY filed as owner of a
1–2 family job. So the §26 contact is not a third-party developer, and the
*value* of the contact on this job is low. What is proven is **structural**:
the fields exist on the form and are dropped by the rendering. Whether §26 is
filled, and by whom, on a real ground-up development is UNTESTED and is the next
thing to measure.

## How it was read (no download)

The in-app preview pane cannot composite the PDF plug-in surface — the viewer
renders as a black rectangle — and top-level navigation to
`BSCANJobDocumentContentServlet` triggers a save dialog. Reading it in the
**user's own Chrome** works: the viewer renders inline, screenshots composite,
`ctrl+End` jumps to the last page. Wheel-scroll does not reach the plug-in and
the page-number box did not take typed input; keyboard navigation did.

---

> ## ⚠ COVERAGE OF THE METHOD SECTION BELOW
> **`pages_read 0 / pages_total 5`** on the one scan identified
> (job 421843884, PW1, `SC181108001`, 496,577 bytes, 5 raster pages).
> **`documents_opened 0 / 10`** on job 421841813's folder.
>
> Everything below the "narrative" heading was assembled from BIS **detail
> screens** — `JobsQueryByNumberServlet`, `DocumentOverviewServlet`,
> `BScanVirtualJobFolderServlet`. Under `RULE_DOCUMENTS_NOT_INDEXES.md` that is
> **not a decode**. It is a finding aid, and it is recorded here as method, not
> as fact. No `facts.Fact` has been written from any of it, and none should be
> until the scans are read.
>
> **The detail screen says so itself.** PW1 §25 Applicant's Statements and
> Signatures renders as: *"( See paper form or check Forms Received )"*. The
> rendering explicitly defers to the scan for the executed page — the same shape
> as an ACRIS acknowledgment block, and exactly the thing a summary screen
> cannot carry.
>
> **Why 0 pages were read (2026-08-06):** the scan is reachable and confirmed
> (`application/pdf`, `%PDF-1.4`, `/Count 5`, 5 image XObjects, LEADTOOLS
> PDFWriter — a raster scan with no usable text layer). It could not be *read*
> because (a) downloading is not permitted, (b) the browser pane does not
> composite the PDF plug-in surface into screenshots, so the viewer renders as a
> black rectangle, and (c) top-level navigation to the content servlet triggers a
> save dialog rather than an inline render. Reachable ≠ read. Recorded as
> **UNREAD**, never as decoded.

Companion to `EXTRACTION_CONTRACT.md`. That contract governs what a decode
returns; this governs how a DOB folder is *read*, because a folder is a
**sequence**, and reading it as a pile of forms produces confident nonsense.

Learned walking job 421841813 end to end, 2026-08-06.

---

## The narrative spine — six surfaces, in this order

Each is a separate servlet under `/bisweb/`, all keyed on `passjobnumber`
(+ `allbin`, and `allisn` for some). Read them in this order, because each one
sets up the question the next one answers.

| # | surface | servlet | what it tells you |
|---|---|---|---|
| 1 | **Document Overview** | `DocumentOverviewServlet` | how many documents (01, 02+) the job has, and **the job description in plain language** — the narrative seed |
| 2 | **Application Details** | `JobsQueryByNumberServlet` | the PW1 as HTML, §1–§26: parties, contacts, zoning, building characteristics |
| 3 | **Virtual Job Folder** | `BScanVirtualJobFolderServlet` | every scanned form with `Form ID · Doc No · PAA · DATE SCANNED · SCAN CODE` |
| 4 | **Plan Examination / All Comments** | `PlanExaminationOverviewServlet` · `JB2CommentsServlet` | what DOB objected to — why the job is where it is |
| 5 | **All Permits** | `JobsPermitsDisplayServlet` | what was actually authorised, and when |
| 6 | **C/O Summary / Preview** | `COApplicationSummaryServlet` · `COPreviewServlet` | what legally exists at the end |

Plus `JB2ScheduleAServlet` (occupancy/use by floor) and `JB2ScheduleBServlet`
(zoning computations) as their own tabs.

The document itself:

    BScanJobDocumentServlet?...&scancode=XXX      viewer page
    BSCANJobDocumentContentServlet?passjobnumber=&scancode=XXX
                                                 the bytes (application/pdf)

---

## ⚠ TRAP 1 — THE FOLDER HOLDS SUPERSEDED COPIES

A folder does **not** contain one PW1. It contains every PW1 ever scanned,
including the ones that were replaced. Job 421841813, all on 2025-05-06:

    round 3  03:19  BIF1  BOROUGH INTAKE FORM          SC181108011
             03:19  PW1   doc 01  PAA No               SC181108010
             03:20  PW1A                               SC181108009
             03:19  EF1                                SC181108008
    round 2  02:29  PW1   doc 01  PAA No               SC181108005
             02:29  PW1A                               SC181108007
             02:29  EF1                                SC181108004
    round 1  09:27  PW1   (no Doc No, no PAA)          SC181108002
             09:27  PW1A                               SC181108003
             09:23  EF1                                SC181108001

**Three complete submission rounds, one day.** Selecting "the PW1" by FORM NAME
returns whichever row happens to come first and is wrong two times in three.
Nothing about the result looks wrong — it is a real, well-formed PW1 with real
numbers, just not the operative ones. Same failure shape as every other trap in
this project: *a check that reports success because it looked in the wrong place.*

**The rule:** group folder rows by `Form ID`, order by `DATE SCANNED`, take the
LATEST — and record the superseded scancodes rather than discarding them, because
the delta between rounds is itself a finding (what did the applicant change after
DOB looked at it?).

**`BOROUGH INTAKE FORM` (BIF1) is the tell.** It appears only in the round DOB
actually took in. When present, it dates the accepted round; when absent from
earlier rounds, those rounds were superseded before intake.

## ⚠ TRAP 2 — `Doc No.` AND `PAA` ARE THE DISAMBIGUATORS, AND THEY ARE BLANK ON SOME ROWS

In the folder above, the round-1 PW1 carries no `Doc No.` and no `PAA` value,
while rounds 2 and 3 carry `01` / `No`. A blank is not "this is document 01" —
it is *unassigned*, i.e. scanned before the filing was docketed. Treating blank
as 01 silently merges pre-intake drafts into the operative record.

`PAA = Yes` marks a post-approval amendment, and it is visible in the FOLDER
LISTING — so the amendment question is answered before any document is opened.
Given that 48.2% of DOB NOW new-building jobs carry a PAA (see `DOB_TRAPS.md`),
this column decides whether the numbers you are about to read are current.

## ⚠ TRAP 3 — THE ADDRESS ON THE LIST IS NOT THE ADDRESS ON THE JOB

Building on My Block listed job 421841813 as **42-80 HUNTER STREET**. The job's
own pages say **42-57 27 STREET**. Same BIN 4005120, same Block 431 Lot 30 — a
corner parcel with two frontages, and the two systems chose different ones.
Join on **BIN + block/lot**, never on the address string.

---

## The narrative, written from the six surfaces

Job **421841813** · A1 · BIN 4005120 · Queens Block 431 Lot 30 · CB 402 (LIC)

> Filed 2024-12-18 as an Alteration Type 1 — the filing type that changes use,
> egress or occupancy and forces a new certificate of occupancy. Its own stated
> purpose, from Document Overview: *"APPLICATION FILED TO ESTABLISH METES AND
> BOUND, PART OF A LARGER ZONING LOT WITH TWO TAX LOTS. OBTAIN NEW CERTIFICATE
> OF OCCUPANCY."*
>
> That single sentence is the whole reason this job matters. It is not a
> renovation — it is a **regularisation of a building sitting on a merged zoning
> lot spanning two tax lots**, which is the DOB-side statement of exactly what a
> ZLDA does on the ACRIS side. `§12 Zoning lot includes the following tax lots`
> on the PW1 is where the roster is stated, and it is the join to the recorded
> instrument.
>
> The applicant re-filed three times on 2025-05-06 before intake accepted the
> third round (BIF1 present only there). A permit record exists —
> `421841813-01-AL` — but was never issued, and the job's last action is
> **PLAN EXAM — DISAPPROVED**. No plan-exam comments are published, so *why* it
> was disapproved is not in the structured surfaces and is a document question.
>
> **Stage: pre-development, stalled at plan exam.** Not construction — the AL
> permit exists as a record, not as an authorisation.

That is the shape every job narrative takes:

    intent (Document Overview job description)
      -> parties and envelope (PW1 §2, §3, §12, §26)
      -> what was submitted and re-submitted (folder rounds)
      -> what DOB pushed back on (plan exam / comments)
      -> what was authorised (permits)
      -> what legally exists (C/O)

Read in that order, a folder answers *what is happening here and who is doing
it*. Read as a pile of PDFs, it answers nothing.

---

## Pacing

`a810-bisweb.nyc.gov` runs an Akamai **Visitor Prioritization** queue. When it
holds you: **wait, do not refresh** — the page says refreshing extends the delay.
A cold hit on a deep servlet 403s; a session that came through the queue does
not. Requests here were spaced ~1.5s and nothing refused. This is per-job
retrieval on a watchlist, not a crawl.
