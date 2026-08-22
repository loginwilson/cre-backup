# Tracking a site's development history — the approach

Measured 2026-08-06. Scope: new build · conversion · enlargement.

---

## 0. THE DAB→DOB RATE, MEASURED PROPERLY — AND MY GUESS WAS WRONG

I claimed the 7.71% DOB-citation rate was depressed by administrative noise in
the denominator, on the strength of three sampled rows. Measured across all
77,931:

    administrative boilerplate    445 / 77,931   0.6%
    substantive                77,486 / 77,931  99.4%
    -> DOB job cited on substantive only:  8.32%   (was 7.71% on everything)

**The noise class barely exists.** Three rows was not a sample, it was an
anecdote, and it produced a wrong hypothesis. The rate is ~8%, full stop.

### But Change_Type splits it into two different worlds

    Change_Type              n        cites DOB job    cites CRFN
    Lot Apportionment    23,772       5,813  24.5%    12,609  53.0%
    Lot Merger           23,662         207   0.9%    13,173  55.7%
    Condominium           9,416          95   1.0%     8,664  92.0%
    REUC                  8,429           0   0.0%         0   0.0%
    DAB Wizard            6,802         254   3.7%     2,890  42.5%
    Air and Subterranean    185          36  19.5%       123  66.5%
    Air                      10           9  90.0%        10 100.0%
    Boundary Line         2,348           3   0.1%        57   2.4%
    ALL                  77,931       6,451   8.3%    38,050  49.1%

★ **APPORTIONMENT IS THE CONSTRUCTION SIGNAL. MERGER IS THE TITLE SIGNAL.**
You apportion a lot because you are building on it, and the DOB job number is
how the change is justified — 24.5%, three times the average, and ~19–90% on
air/subterranean lots. You merge a lot because title moved, so the authority is
a deed and the citation is a CRFN — 0.9% DOB, 55.7% CRFN.

⚠ And the "tightest cut" is a trap: filtering to transactions that ADD or DROP a
lot gives **2.43%**, *lower* than the average, because that population is 81%
Lot Merger. "The lot moved" is not "something was built".

**Conclusion:** the alteration book is an ACRIS join first (49.1%, and 92% on
condos) and a DOB join only on apportionment. Do not build site tracking on the
DAB→DOB link. Build it on DAB→ACRIS, and take the DOB citation as free
corroboration where it appears — it is 98.3% precise when it does.

---

## 1. THE UNIT IS THE SITE, AND ITS IDENTITY IS A SET

Not a BBL, not a BIN, not a job. A site is ground, and every identifier it
carries is temporary. Resolve identity FIRST, then pull.

    BBL set  = today's BBL
             + DOF Digital Alteration Book lineage (dof_lineage.history)
             + PLUTO appbbl / condono
    BIN set  = every BIN appearing on any record keyed to any BBL in that set

Both are needed and neither implies the other — proven on Queens 17/1:
five BINs under **one unchanged lot** (so `appbbl` is correctly `None` and
lot-lineage tooling finds nothing), while lots 28→29 on the same block show a
real `appbbl` chain that a BIN union would miss.

⚠ Lineage is only published from **2008-05-20** (DAB). Before that, lot changes
must be inferred from PLUTO vintages or read out of documents.

## 2. UNION SIX INDEXES ON THAT IDENTITY SET — none is a superset

| source | reach | why it is not optional |
|---|---|---|
| `bty7-2jhb` historical permits | 1989–2013 | the only pre-2000 layer; owner address + phone |
| `ipu4-2q9a` permits | ≥1992–2022 | carries jobs the jobs feed lacks |
| `ic3t-wcy2` BIS jobs | 2000–2025 | job type, envelope fields, B-Scan route |
| `w9ak-ipjd` DOB NOW | 2016–now | current filings, base/suffix chain |
| DOB NOW portal | 2016–now | per-filing Zoning Information |
| `bs8b-p36w` / `pkdm-hqz6` | — | CO; ⚠ no temporary/final flag |

Proven on Queens 17/1: permits reference 10 job numbers, the jobs feed has 6.
Five exist only in permits — including the entire 2003 demolition. One exists
only in jobs (filed, never permitted), which is its own finding.

⚠ Each has its own key spelling — **five conventions measured so far.** Control
every query before reporting an absence.

## 3. SEGMENT INTO DEVELOPMENT CYCLES

Scope alone cannot be ordered — a site runs through repeated cycles and nothing
in "new build / conversion / enlargement" marks the seam.

**Demolition is the seam, and it is a precursor to NEW BUILD specifically** —
not to conversion or enlargement. Include `DM` in the PULL as segmenter and
signal; exclude it from the OUTPUT as a development type.

⚠ **DM is not reliably the leading edge.** Queens 17/1 filed its NB on
2021-08-19 and its three DMs on 2021-10-07 — the new building came first by
seven weeks. `ACP5` asbestos assessment is documented as often earlier than the
DM filing. **Lead/lag between DM and NB is UNMEASURED — do not assume order.**

⚠ And a demolition can wear an alteration's clothes: the 2003 event here was
filed as `A2` — *"removal of partial collapsed section of two story building"*.
A job-type filter alone drops it. Read the description.

## 4. WHICH DOCUMENTS TO PULL — the rule

**Never open a document to learn something the index already states.** Open one
only to answer a question the index provably cannot. Measured, those are:

| question | why the index cannot answer | where | pages |
|---|---|---|---|
| **developer name/role/phone/e-mail/mailing** | `owner_s_house_number` populated on **25 of 318,869**; no phone or e-mail column exists anywhere | PW1 **§26** | **last page only** |
| condo/co-op board contact | not published | PW1 §26A | last |
| executed signature + P.E./R.A. seal | details page prints *"( See paper form )"* | PW1 §25 | last |
| metes and bounds | details page says *"see the Plot Diagram"* | **PD1** | ? |
| zoning floor area, pre-2008 | `proposed_zoning_sqft` 1.9% before 2008 | **ZD1** | ? |
| bulk/3D as filed | not published | ZD1 | ? |

Everything else — stage, dates, job/work type, permittee **and their direct
phone (99.6% of 3,989,787 BIS permits)**, and for DOB NOW the entire zoning
statement — comes free from the index or the portal.

★ **§26 is the LAST page of the PW1** (proven: page 5 of 5). So the developer
contact costs one page render, not five. Read the last page first.

⚠ For DOB NOW the envelope needs **no document at all** — the portal's Zoning
Information section carries districts with per-district area, lot area, lot
width/type, street legal width, yards, height & setback, the pre-1961 flag and
the zoning-lot-certification flag. Carry its `Auto Populated: No` flag onto
every derived fact: that means the applicant keyed it, not the system.

## 5. WHAT TO EXTRACT FROM EACH DOCUMENT

Per `EXTRACTION_CONTRACT.md` — every value with `document_id` + `page`.
Priority order, because a partial read must degrade predictably:

1. **§26** owner block — name · relationship · business · street/city/state/zip ·
   phone · e-mail · signature date · owner type checkbox
2. **§2 / §3** applicant of record and filing representative — name, business,
   address, phone, mobile, e-mail, licence/registration number
3. **§12** zoning — district(s), overlay, special district, map number, street
   legal width + status, **zoning lot tax-lot roster**, use/area/FAR table,
   lot area, lot type, coverage, yards
4. **§8** enlargement flag (horizontal/vertical) + total building SF
5. **§9** the binding flags — landmark + docket no., lot merger/reapportionment,
   restrictive declaration/easement, zoning exhibit record, BSA/CPC calendar nos.
6. **§25** seal, signature, sign date
7. **PD1** metes and bounds, verbatim per the contract's transcription rule

★ §9 and §12 are where DOB names the ACRIS instrument: `Filing includes Lot
Merger / Reapportionment`, `Restrictive Declaration / Easement`,
`Zoning Exhibit Record`, and the tax-lot roster. That is the DOB-side statement
of what should exist in the recorded record — a `Yes` with no instrument found
is a finding.

## 6. HOW FAR BACK — and what is still untested

    scanned DOB documents online       2008        MEASURED
    DOB NOW documents                  2016        MEASURED
    lot lineage published (DAB)        2008-05-20  from dof_lineage.py
    job records, no documents          2000        MEASURED
    permit records, no documents       1989-05-11  MEASURED (bty7-2jhb)

## ★★★ BELOW 1989: I-CARDS REACH 1914 — TESTED 2026-08-06

**HPD calls them "Historical Image Cards", not I-cards** — which is why a search
for "i-card" finds nothing. There is **no Socrata dataset**; the open-data
catalog has none. Web only.

    hpdonline.nyc.gov/hpdonline/  ->  search Address / BIN / Registration / BBL
      -> building page (e.g. /building/433239/overview)
      -> Overview tile "Historical Image Cards  Yes  [View All]"
      -> /building/<id>/historical   ->  Icard_<n>.pdf, opens as a blob in a new tab

⚠ The date on the listing (2/6/2008) is the **SCAN** date, not the card's date.

### What a card actually contains — 11-55 45 Avenue, Queens (blk 52 lot 1)

    CLASSIFICATION  NEW LAW      (post-1901 Tenement House Act)
    ORIGIN          TENEMENT HOUSE DEPT. — NEW BUILDING PLAN
      Bldg 1 · Plan No. 121 · Date filed 6-17-14 · Date Approved 6-24-14
      Certificate No. 83 · Date issued 5-28-15
    LEGAL OCCUPANCY   No. Ap'ts 27 · Height 5
    ALTERATION PLANS  dated entries (1-13-65 ... completed 5/7/85)
    ACCEPTANCES       67783 4/10/58 · 308876 1/24/63 · 316095 3/26/63
    Reg # 415241      <- the join back to the modern HPD record
    ---- inspection side, 3 pages total ----
    Stories 5 · Lot Size 50 x 100-8 7/8 · Lot: Corner · Fireproof: non
    Total Apts 27 · Total Rooms 100 · Apts per floor 3-6 · Stores 2
    Rooms per apartment: 3-rm x13 · 4-rm x9 · 5-rm x5 = 27
    Per storey  apts 3/6/6/6/6 · rooms 12/22/22/22/22 · W.C.s 3/6/6/6/6
    RENTAL OF APTS  front 21 @ 5 rooms $38.00 · rear 5 @ 4 rooms · court 1 @ 3 rooms
    VIOLATIONS + REVIEW ("increase or decrease in No. of apts: NONE")  4/1/16

**A new-building plan filed 1914-06-17, approved 1914-06-24, certificate issued
1915-05-28 — 75 years before the earliest DOB record online**, and it carries
the same lifecycle DOB records today: filed → approved → certificate issued.
Plus **alteration plans with dates** (conversion / enlargement), **legal
occupancy** (the envelope as established), **lot dimensions**, **unit mix**, and
**actual rents from 1916**.

★ **It contradicts PLUTO, and it wins.** PLUTO says `yearbuilt 1917`; the card
says plan filed 1914, certificate 1915. The card is the primary document;
`yearbuilt` is a later administrative estimate.

### ⚠ The scope limit that matters

I-cards are a **Tenement House Department / HPD** record — they exist for
**multiple dwellings**, not for commercial or industrial buildings. Queens 17/1
(an art warehouse, then industrial) would have none. So this closes the pre-1989
gap **for residential only**, which is exactly the stock a conversion or
enlargement is usually performed on — but it is not a general pre-1989 layer.

### Coverage — ADDRESSABLE POPULATION MEASURED, HIT RATE ONLY SPOT-CHECKED

**⚠ A true coverage measurement was NOT possible and was not faked.** The
per-building flag comes from
`mspwvw-hpdleov3.nyc.gov/hpdonline.api/1.0/api/building/historicimage/list/<id>`,
which answers:

    {"code":"900902","message":"Missing Credentials",
     "description":"... header: 'ApiKey : Bearer ACCESS_TOKEN' ... or 'apikey: API_KEY'"}

The SPA carries that key in its bundle. **Lifting it to sweep 90,000 buildings
is using a credential we were not granted, against a service that explicitly
gates it — not done.** A real coverage number needs HPD's permission or a data
request. Everything below is what could be established without it.

**The addressable population, measured exactly** — `kj4p-ruqc`, 379,130 rows.
`buildingid` joins HPD Online 1:1 (verified: 433239 → block 52 lot 1,
BIN 4430575, registration 415241). Classes predating the 1929 Multiple Dwelling
Law, Active only:

    NEW LAW TENEMENT               42,430
    OLD  LAW TENEMENT              25,086
    HERETOFORE CONVERTED CLASS A   19,148
    HERETOFORE CONVERTED CLASS B    1,745
    HERETOFORE ERECTED EXISTING       582
    NEW/OLD LAW SRO                   349
    CONVERTED NEW/OLD LAW TENEMENT    285
    ------------------------------------------
    ~89,600 active buildings in the addressable classes

("HEREAFTER" classes postdate 1929 and fall outside the Tenement House
Department's card series. `HEREAFTER ERECTED CLASS A` alone is 42,259.)

**Spot check — n = 9. This is NOT a coverage rate.**

    433239  NEW LAW TENEMENT          Yes
    650075  NEW LAW TENEMENT          Yes
    425646  NEW LAW TENEMENT          No
    702608  OLD  LAW TENEMENT         Yes
    403443  OLD  LAW TENEMENT         No
    812146  HERETOFORE CONVERTED A    Yes
    445936  HERETOFORE CONVERTED A    No
    1010165 HEREAFTER ERECTED A       No
    1007176 HEREAFTER ERECTED A       No

    pre-1929 classes   4 / 7 carry a card
    post-1929 classes  0 / 2

★ **Class does not determine presence.** Three New Law tenements split
Yes/Yes/No; two Old Law split Yes/No. So the flag must be READ per building, not
inferred from class. At n=7 the pre-1929 rate is somewhere very wide around
~57% — the honest statement is **"common but not universal, and nowhere near
100%"**, and nothing tighter is supportable from nine buildings.

**Operationally that is fine:** the `Historical Image Cards: Yes/No` flag sits on
the building Overview page you are already loading, so presence costs nothing
extra per site. Treat I-cards as a **checkable per-building lookup**, never as a
layer that can be assumed present.

⚠ Deep-linking to `/building/<id>/historical` redirects to `page-not-found` —
the SPA requires arriving via `/overview` first.

### Also on the HPD building page, free

`Property Owner Registration Information` — Head Officer, Officer, Corporation,
Managing Agent, each with a **name and mailing address** (here: Alex Kaskel and
Mark Levine, 1155 45th Owner LLC, 401 Park Avenue South). An owner-contact
source independent of both ACRIS and DOB, refreshed annually rather than on
transaction — see `SOURCE_MAP_DOB.md` on registration being a monitoring source.

**Still untested below 1989:** for NON-residential sites there is no online
layer found yet. Candidates, all UNVERIFIED by me:

* **records request** (DOB NOW: BIS Options) — pre-BIS job numbers return
  folders, microfilm, docket books, reels; BBL returns folders, microfilm and
  **index cards / I-cards**. Needs an eFiling account; ends at a borough counter.
* **HPD Online I-cards** — pre-1938 multiple dwellings, published free.
* **BSA** — calendar numbers to the 1930s–40s, grants still in force.
* **DORIS / Municipal Archives** — building plans, docket books, block-and-lot
  collections, and the 1940s tax photographs.

Each needs the same treatment everything else got: control the query, state the
denominator, and never report an absence from an untested source.
