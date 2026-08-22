# DOB NOW documents — the surface, and where the OWNER hides

# ★★★ SEARCH THE SITE, NOT THE JOB — Login, 2026-08-06

> "inventory the documents on the site, not the job summary. remember this is
>  zoomed into a specific job, but when you search a site you can choose the
>  job and there may be other documents"

Correct, and it exposed surfaces the job view cannot reach. The **Property
Profile** header carries nine site-level buttons, each its own record set
spanning EVERY job on the site:

    Penalties Owed · Building Schedule of Occupancy · Certificate of Occupancy
    Certificate of Compliance · Active Tenant Protection Plans · After Hour
    Variance · Energy Submission · Loft Board Submission · Notifications

## ★ CERTIFICATE OF OCCUPANCY — THIS IS THE ACRIS JOIN

The CO detail names the recorded instruments burdening the property, BY CRFN:

    CO 4625206-0000008 · Renewal Without Change · issued 07/10/2026
    associated with job# Q00564746-I1
    R-2 Residential · Class A-HAEA-Hereafter Erected · 12 storeys · 125.00 ft
    499 dwelling units · I-B 2-Hour Protected · 0 open / 111 enclosed parking
    LEGAL LIMITATIONS
      Restrictive Declaration   L-1387, P-307, 2025000128427   <- CRFN
      Zoning Exhibit            2022000124028, 2022000124029   <- CRFNs
      BSA Calendar / CPC Calendar   None

★★ **This settles the ownership question without DOB ever giving up a phone.**
Login's own framing: *"for ownership as long as we can key it to the project and
the relation to deed and mortgage, it works."* The CO hands over the CRFNs:

    DOB CO -> CRFN -> ACRIS instrument -> declarant / deed / mortgage
           -> the Notices + acknowledgment blocks -> a NAMED HUMAN with a phone

It also carries `L-1387, P-307` — a Liber/Page reference for the pre-CRFN era,
so the join reaches back past 1966 digitisation too.

★ And the CO names `BSA Calendar Number(s)` and `CPC Calendar Number(s)` —
the ENTITLEMENT join (Chat 3) stated on the DOB record. `None` here, but on a
variance site that is the pointer straight to the grant.

## ⚠ CORRECTION — "Additional BINs for Building" IS populated

Earlier I recorded the Property Profile as showing `Additional BINs: NONE` and
concluded it "erases the four demolished predecessors." **Wrong.** It reads:

    Additional BINs for Building: 4436573, 4436574, 4000017, 4436572

— including **4000017, a BIN that appears in NO feed I pulled.** So the profile
publishes the BIN set directly and more completely than scraping BINs out of job
rows. `site_history.py` should resolve BINs from the Property Profile, not from
filings.

## Certificate of Compliance — an equipment register, not a party record

`/Publish/BE-MS-ST/PrintCOC/COC_Print.html?JobNumber={BIN}|{seq}` — CONSTRUCTIBLE.
6 pages: HVAC/AC units with location, efficiency, manufacturer, capacity, model,
**serial number**, and a **Job Filing Number per item** (Q01190386-S1,
Q01284289-S1, Q00564746-S3). No owner. Useful as an equipment-to-filing index
and for dating mechanical installs; useless for contact.

## Active Tenant Protection Plans — an OWNER INDEX across jobs

Grid columns: Request Number · Request Type · Status · **Associated Job Filing
Number** · Job Filing Status · Work On floors · **Applicant of Record** ·
**Owner** · Modified Date. Seven TPPs across FOUR jobs on this site, naming
owners the Q00564746 job view never showed (Thomas Turner, Kay Rigaud, alongside
Peter Papamichael).

⚠ **The TPP body itself is boilerplate** — egress, fire safety, dust, noise,
essential services. It *references* contacts without naming them: "contact
information of Site Safety Manager / Site Safety Coordinator / Superintendent of
Construction / Owner / Owner's Designee" — but that notice is posted in the
lobby, not published online. The grid's Owner column is the value, not the body.

⚠ **A date boundary is stated on the TPP screen:** "Below are TPPs for jobs
created after December 28, 2020. For jobs created before December 28, 2020, the
TPP is a document on the individual job record." So TPP is STRUCTURED post-2020
and a DOCUMENT pre-2020 — two retrieval paths split on a date.

## ★★ BUILDING SCHEDULE OF OCCUPANCY — THIS SETTLES TCO vs FINAL CO

30 rows, per floor. Columns: Floor · Status · **Occupancy Type** · Building Code
(Existing | Proposed) · Occupancy Classification · Occupancy Group · Description
of Use.

    Cellar   Verified  INTERIM     Storage S-2               Parking Garage
    Cellar   Verified  INTERIM     Factory & Industrial F-2  Mechanical
    Cellar   Verified  INTERIM     Residential R-2           Apartment House
    Floor 1  Verified  TEMPORARY   Residential R-2           Apartment House
    Floor 1  ACTIVE    (proposed)  Institutional I-4         <- pending change
    Floor 1  Verified  TEMPORARY   Business B                Business & Service
    Floor 1  Verified  TEMPORARY   Mercantile M              Retail Sales

★ **`Occupancy Type` is the temp/final flag the CO feeds do not publish.**
`pkdm-hqz6` gives only `Initial` / `Renewal With(out) Change`, which is why
delivered-vs-complete was unresolved. Here it is stated per floor: this building
is **TEMPORARY / INTERIM occupancy — `temporary_operation`, NOT `operation`.**
Eight CO records from 2025-05 to 2026-07, all TCO.

⇒ In the stage model (signalling → pre-development → construction →
temporary operation → operation), **the CO alone does not prove `operation`.**
Read the Building Schedule of Occupancy's `Occupancy Type` before promoting a
site to operation, or every TCO building reads as complete.

★ The `Active / Institutional I-4` row sits in the PROPOSED columns — a stage
transition IN FLIGHT (the daycare filing), visible before it lands.

## ★ NOTIFICATIONS — the construction-velocity ledger

23 records across MANY jobs on the site. Columns: Notification Number ·
**Notification Type** · Status · **Associated Job #** · **Notified By** · Created Date.

    2025-09-26  Tenant Protection Plan 72 Hour            Q01284289-I1  DAVID CHAGNON
    2025-07-22  Suspended Scaffold                        Q00807482-S3  VICTOR BOBER
    2025-06-24  Protection & Mechanical Methods REMOVAL   Q01157072-I1  IBRAIM REXHA
    2025-06-24  Supported Scaffold REMOVAL                Q00914221-I1  IBRAIM REXHA
    2025-05-29  Construction Fence REMOVAL                Q00700079-I1  Paul Perdek
    2025-04-08  Tenant Protection Plan 72 Hour            Q01190386-S1  ANTHONY RIVERA JR.

★ **Physical site events, dated, named, in no Socrata feed.** Fence and scaffold
REMOVAL notices in May-June 2025 are the signature of a site finishing — and
they cluster right around the 2025-05-09 initial CO. Fence out, scaffold down,
certificate issued. That is construction→occupancy velocity measured in weeks,
from the site's own filings.

⇒ Feed these to the stage model as `construction_winding_down` evidence, and use
`72 Hour` TPP notices as the marker that work is about to start in an occupied
building.

## After Hour Variance — empty at site level

Clicked; no modal, no records. Not an error — this site has no AHV at the
property level (the Job Summary DID show `Q9581831 - AHV Per...` on I1, so AHV
lives on the JOB row, not the site button, at least here). ⚠ Verify on a site
that has one before concluding the button is decorative.

## Still unopened on that row

Penalties Owed · Building Schedule of Occupancy · After Hour Variance ·
Energy Submission · Loft Board Submission · Notifications.

---


Measured 2026-08-06 on job Q00564746 (2-33 50 Avenue, Queens blk 17 lot 1).

## THE ACCESS CHAIN — public, no login

    /publish/index.html#!/COVJobSummary?JobId={JOB}&UserId=PublicPortalUser
      -> page to the filing, click the Job# link  (fires showInfoFromSummary)
      -> Filing Details modal -> expand "Documents"
      -> each row's anchor: ng-click="downloadDocument(...)"   NO auth gate
      -> resolves to a STABLE, RE-FETCHABLE URL:

    https://a810-dobnow.nyc.gov/Publish/DocumentStage/PortalDownloadedDocuments/
        {BOROUGH}/{JobId}/{Filing}/Supporting Documents//{id}/{filename}.pdf

★ Verified re-fetchable on a fresh request (HTTP 200, `application/pdf`).
★ **Born-digital, not scans** — `%PDF-1.7`, font tables present, 3 image
  XObjects in a 2.6 MB file. **These are parseable as TEXT, not vision reads.**
  That changes the cost profile completely versus BIS B-Scan rasters.

## ⚠ DOCUMENTS LIVE ON THE INITIAL FILING

    filing C7 (amendment)   0 documents
    filing P2 (amendment)   1 document
    filing I1 (INITIAL)    26 documents

Same rule as §26: **the initial filing is where the substance is.** Concluding
"DOB NOW publishes no documents" from an amendment — which I did — is wrong.

## THE 26 DOCUMENTS ON I1

    ZD1: DOB Zoning Diagram                    Zoning Exhibit form (1-5)
    Restrictive Declaration/Easement 1         Restrictive Declaration/Easement 2
    Site Survey: Initial                       House Number Verification: TOPO Stamp
    DEP: Sewer Certification                   Local Law 92/94 Sustainable Roof Zone
    Certificate of Insurance (= PGL1)          Certification by Insurance Broker
    Additional Insured Authorizations          Standpipe Alarm Drawings or AI1
    Street Tree Checklist                      Parks Dept Acknowledgment Letter
    Other Documents - Narrative of Changes to PAA
    Other 1-10 Documents - Prior to Approval   Additional Supporting document1

## ★ WHAT THE DOCUMENTS ACTUALLY YIELD — first read

`Certificate of Insurance` is really **PGL1: Project Specific General Liability
Insurance Summary and Affirmation**, a DOB form:

    §1  2-33 50 Ave · Queens · Block 17 · Lot 1 · BIN 4436873 · CB 402
    §2  Tower crane: YES · Calculated GL insurance required: $80M
    §3  APPLICANT STATEMENT AND SIGNATURES
          CONGRESS BUILDERS LLC · Registration/Tracking # 600734
          wet signature · dated 2/14/2022
          notarised: Wanda Rivera-Mangan, NP 01RI4953999, Bronx Cty, exp 7/31/2025
    §4  BROKERS CERTIFICATION
          Sterling Risk · 135 Crossways Park Dr, Woodbury NY · e-mail field
          per-occurrence $85M · aggregate $85M
          notarised: Neva Hoffmaier, NP 02HO6097177

★ **CONGRESS BUILDERS LLC — the general contractor — appears in NO Socrata feed
for this job.** The supporting documents name counterparties the structured data
does not have.

⚠ But it is **not the owner**. The documents so far yield contractor, broker and
notary — people one call from the principal, not the principal.

## ⚠ THE PW1 ENDPOINT RETURNS §26 NULL

    GET /Publish/WrapperServicePP/WrapperService.svc/GetJobFilingPW1/{guid}
    -> 493 fields, full PW1 schema, and EVERY owner-contact field null:
       RelationshiptoOwnerPW1Statement · OwnerTypePW1Statement · Date26PW1statemnt
       OwnerSealAndSignature.OwnerNameStatementPrintPW1 / OwnerDateStatementPW1
       condoOwnerDetails.Email / BusinessTelephone / BusinessAddress / City / Zip

⚠ **The same GUID was requested for both I1 and P2** — so it appears to be the
JOB's GUID, not the filing's, and one payload serves every filing view. If that
holds, the null §26 is the job-level answer and the public endpoint is stripped
at source. **NOT YET CONFIRMED** — the tab froze before the identity fields
could be re-read. Confirm by checking whether the payload carries a
FilingNumber, and whether it differs per filing.

---

# ★ THE STRATEGY — Login, 2026-08-06

> "we still want to find owner regardless as the highest indicator and value
>  source so my suggestion is to look through all documents on the site that
>  could have an owner since there tend to be many job filings"

Right approach. A site has many jobs; each job's **initial filing** has its own
document set; the owner is executed on *some* of them. Sweep the documents, not
the feeds.

## Ranked by likelihood of carrying the OWNER, with reasons

1. **Restrictive Declaration / Easement 1 & 2** — ★ BEST BET, UNTESTED.
   These are **recorded instruments**, executed BY THE OWNER as declarant. Per
   `EXTRACTION_CONTRACT.md`, instruments of this class carry a **Notices block**
   — "the richest contact source in ACRIS ... a NAMED HUMAN behind an SPE, with
   a phone, from 2004 onward" — plus acknowledgment blocks naming who signed for
   the entity. If any DOB NOW document holds a full owner block, it is this one.
   It also cross-references straight into ACRIS by CRFN.
2. **Zoning Exhibit form (1-5)** — the zoning-lot certification. Owner-executed;
   on a merged zoning lot it names every party lot's owner.
3. **Site Survey: Initial** — surveyor certifies for a named client (the owner).
4. **Parks Dept Acknowledgment Letter** — correspondence, addressed to a person.
5. **DEP Sewer Certification** — applicant/owner block.
6. **Other Documents - Narrative of Changes to PAA** — prose, often naming who
   directed the change.
7. `Other 1-10 Documents - Prior to Approval` — grab-bag; one already proved to
   be plan-examiner markup (useful for the objection narrative, not contact).

## Method for the sweep

* Per SITE: enumerate every job (worklist already has 226,685 parcels).
* Per JOB: open the **initial filing** only. Documents live there.
* Read the Documents grid — it NAMES each document before you fetch anything,
  so the sweep is planned from names and only promising ones are downloaded.
* Fetch is a plain GET on a stable URL, and the PDFs are **born-digital**, so
  extraction is text parsing, not OCR.

⚠ Fragility to design around: the portal modal does not rebind from a stale
state (reload the route between filings), grids lag several seconds before
links bind, and heavy documents freeze the renderer. Build in waits and treat
a frozen tab as retry-with-fresh-tab, never as "no documents".
