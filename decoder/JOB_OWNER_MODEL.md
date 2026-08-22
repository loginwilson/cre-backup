# The owner is a property of the JOB, not of the parcel

Measured 2026-08-07 on Queens block 17 lot 1 (2-29 50 Avenue / 49-18 5 Street).
33 years, 13 scope-bearing job folders, **three real ownerships**.

The question this answers: *if there's a development in 2002 and a new build in
2023, they may have different owners — so read the owner per job folder and
summarise each job.* Confirmed. Here it is.

---

## THE TIMELINE

    1992-12-02  400339674  A2   William Judson    JUDSON ART WAREHOUSE
    1997-07-11  400753591  A3   Jason William     JUDSON ART WAREHOUSE
                                212-974-1900 · 50 West 57th Street, New York 10019
    ──────────────────────────────────────────────────────────── OWNER CHANGES
    1998-01-14  400806927  A2   William Snyder    FORTRES
                                718-253-1655 · 49-20 5 St, Queens 11101
    2003-01-31  401603920  A3   Allen Hansen      FORTRESS NY INC.
    2003-02-24  401613811  A2   Alan Hansn        Fortress NY Holding
                                718-937-5500 · 49-20 5th Street, Queens 11101
    2003-03-26  401622981  DM   —                 —          ← no owner named
    2003-03-26  401622990  DM   —                 —
    ──────────────────────────────────────────────────────────── OWNER CHANGES
    2021-08-19  Q00564746  NB   —                 50TH & 5TH LIC LLC
    2021-10-07  421807511  DM   Peter Papamichael 50TH & 5TH LIC LLC
    2021-10-07  421807520  DM   Peter Papamichael 50TH & 5TH LIC LLC
    2021-10-07  421807502  DM   Peter Papamichael 50TH & 5TH LIC LLC
    2022-02-01  440704356  A3   Peter Papamichael 50TH & 5TH LIC LLC
                                516-805-1584 · j.lewis@vorea.com
                                184 North 8th Street, Brooklyn 11211

A 2003 demolition and a 2021 new build, different owners — the exact case.
The 2003 teardown was ordered by **Fortress**; the 2021 teardown and tower by
**Vorea**. Two separate development cycles, eighteen years apart, and only the
job folder separates them.

---

## ⚠ TWO FILTERS, OR THE TIMELINE IS NOISE

### 1. Trade filings put the TRADE in the owner field

Unfiltered, this lot reports **15+ ownership changes**. Filtered to
scope-bearing job folders it reports **3**. The false ones:

    CELTIC SERVICES NYC INC        general contractor
    SKYLINE SCAFFOLDING GROUP      scaffold
    VIK XS SERVICES INC            suspended scaffold
    THE VOREA CONSTRUCTION COS     the developer's own construction arm
    DOMAIN COMPANIES               operator
    Frankie's Brooklyn Pizza       TENANT fit-out
    Peanut and Honey Baby…         TENANT fit-out

**Take the owner only from an original scope filing** — BIS `doc__='01'` with
`job_type in (NB, A1, A2, A3, DM)`, or a DOB NOW `New Building`. Equipment,
scaffold, sign and tenant filings are not ownership evidence.

### 2. Entity spelling fragments one owner into several

    FORTRES  ·  FORTRESS NY INC.  ·  Fortress NY Holding      = one owner
    Allen Hansen  ·  Alan Hansn                               = one person

Normalise before segmenting, or every misspelling reads as a sale.

---

## WHERE THE CONTACT COMES FROM, BY ERA

| era | owner contact source | quality |
|---|---|---|
| **1989–2013** | `bty7-2jhb` — the **only** DOB feed that ever published `owner_s_phone` + address | structured, exact |
| **2014–~2022** | PW1 §26 on an `SC` (paper-scanned) document | OCR; digits need cross-scan voting |
| **~2022 onward** | PW1 §26 on an `ES` (eFiling) document — **no OCR text layer** | raster crop only |

`ipu4-2q9a` (modern permits) carries owner house/street/zip but **no phone
column at all**; `w9ak-ipjd` (DOB NOW) carries neither. So the structured owner
contact stops dead in 2013 and everything after it lives in the document.

⚠ The `ES` raster is legible to a human but the BIS PDF plug-in **freezes the
renderer** on large scans (measured: job 320917503 doc 18, a 205,578-byte
single image stream, hung `Page.captureScreenshot` for 30s). Page to it, don't
open it cold.

---

## ⚠ THE §26 EMAIL IS A COMPANY CONTACT, NOT THE SIGNATORY'S

Read off the scan for job 421807520 (crop, `SC181108036`, page 5):

    Name (please print):    Peter        Papamichael
    Relationship to Owner:  Member
    Business Name/Agency:   50th & 5th LIC LLC
    Street Address:         184 North 8th Street
    City: Brooklyn   State: NY   Zip: 11211
    Telephone Number:       516-805-1584          Fax:
    E-Mail Address:         j.lewis@vorea.com
    Signature and Date:     12-16-21

**The signatory is Papamichael; the email routes to J. Lewis.** Do not treat
`§26 name` and `§26 email` as the same person — store them as two fields with
two identities, or the party graph gains an edge that does not exist.

---

## THE OWNER'S ADDRESS IS ITSELF A SIGNAL

    JUDSON        50 West 57th Street, Manhattan   — absentee
    FORTRESS      49-20 5th Street, Queens 11101   — THE SITE ITSELF, owner-occupant
    50TH & 5TH    184 North 8th Street, Brooklyn   — absentee (Vorea's office)

Whether §26's address equals the premises separates an owner-user from an
investor, per job, at the date of filing. Fortress operated out of the building
it later demolished.

---

## THE SHAPE TO STORE

One row per **job folder**, never per parcel:

    bbl · job · source · doc · filing_date · job_type · scope
    owner_name · owner_role · owner_entity · owner_phone · owner_email · owner_addr
    owner_addr_is_site · contact_source (feed | SC scan | ES crop) · citation

`citation` = `(job, scancode, page)` for a document read, or `(dataset, job)`
for a feed read. Carry the same `involvement_at_date_only__not_current_ownership`
guard already used in `parcel_parties.jsonl` — **§26 proves who signed on that
date, never who owns it now.**

Within a long job the owner can change too: the PAA `Description of Amendment`
says *"supersede prior applicant of record, OWNER SIGNATORY"* (280 Kent docs 13
and 18). So a job folder holds an owner **timeline**, not a single owner — see
`NARRATIVE_280KENT.md`.
