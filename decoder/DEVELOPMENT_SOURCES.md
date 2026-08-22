# Every source that tracks development, earliest to present

Measured 2026-08-06 unless marked. Nothing here is asserted from a workbook —
each reach figure came from a query whose denominator is stated. Sources that
were NOT tested are listed at the bottom as untested, not omitted.

Scope: new build · conversion · enlargement. `DM` carried as segmenter/signal.

## ⚠ OWNERSHIP — this is a RECONNAISSANCE map, not a build list

Written by **Chat 2 (DOB BIS + NOW)**. The rule in `DECODER_CHATS.md` is that
one chat owns one source and writes one `source` value. This document does NOT
claim any of the following:

| source | owner | what Chat 2 does with it |
|---|---|---|
| **BSA · LPC · DCP** | **Chat 3** | ⚠ NOT MINE. §4 below is reach reconnaissance only — measured because "how far back" cannot be answered without it. **Hand the figures to Chat 3; do not build on them here.** |
| ACRIS | Chat 1 | consume facts from the sink |
| DOS entities | Chat 4 | consume |
| StreetEasy / comps | Chat 5 | consume |
| **DOB BIS · DOB NOW · B-Scan · CO** | **Chat 2 (mine)** | decode and write |
| DOF alteration book / spine | shared infrastructure | read; `dof_lineage.py` patched with evidence |
| **HPD I-cards · 1940s + 1980s tax photos** | **UNASSIGNED** | see below |

★ **HPD and the tax photos have no owner.** `DECODER_CHATS.md` assigns ACRIS,
DOB, BSA/LPC/DCP, DOS and StreetEasy — nobody has HPD or DORIS. They are also
**the only development layers that reach before 1989**, and they key on BIN and
BBL exactly as DOB does. That is a decision for Login: either Chat 2 takes them
(the join is identical to the DOB one) or they get their own chat. **Until that
is decided, nothing here writes facts under an HPD or DORIS source name.**

The distinction that matters: **owning a source ≠ consuming it.** Assembling a
site timeline from facts other chats wrote is exactly what the shared sink is
for. Decoding another chat's documents is not.

---

## THE LADDER

    1914 ─────────────────────────────────────────────────────► ~1985   HPD I-card (residential only)
              1939-41 ●                                                 1940s tax photos (every building)
                                              1982-87 ●                 1980s tax photos (every building)
                                                    1989 ──────► 2013   bty7-2jhb historical permits
                                                      ≥1992 ──────► 2022  ipu4-2q9a permits
                                                          1998 ──────►   BSA decisions
                                                            2000 ─────►  ic3t-wcy2 BIS jobs
                                                              2008 ───►  B-Scan job DOCUMENTS
                                                              2008 ───►  DOF alteration book (lineage)
                                                                2016 ─►  DOB NOW + portal

★ **2008 is the digital horizon** — three independent systems begin there:
scanned job documents, the keyed zoning figure (`proposed_zoning_sqft` 1.9% →
86.6%), and published lot lineage (DAB, 2008-05-20).

---

## 1. HPD I-CARDS — "Historical Image Cards" · 1914 → ~1985 · FREE

`hpdonline.nyc.gov` → Address/BIN/BBL search → `/building/<id>/overview` →
tile "Historical Image Cards Yes/No" → `/building/<id>/historical` → PDF.

**A running ledger, not a snapshot.** The 11-55 45 Avenue card carries the 1914
new-building plan AND alteration plans through 1965, completions to 1985, and
acceptances in 1958/1963 — one card spanning 71 years.

Gives: NEW BUILDING PLAN no. + **date filed / date approved / certificate no. +
date issued** · ALTERATION PLANS with dates · LEGAL OCCUPANCY (apts, height) ·
lot size + lot type · unit mix by room count · per-storey apt/room/WC counts ·
stores · **actual rents** · violations · HPD registration no. (join to modern).

⚠ **Residential only** — a Tenement House Dept record. Non-residential sites
have none. ⚠ Beats PLUTO: card says plan 1914 / certificate 1915, PLUTO says
`yearbuilt 1917`. ⚠ Deep links to `/historical` 404; go via `/overview`.

Addressable population (`kj4p-ruqc`, 379,130 rows, `buildingid` joins 1:1):
**~89,600 active buildings** in pre-1929 classes — NEW LAW TENEMENT 42,430,
OLD LAW 25,086, HERETOFORE CONVERTED A 19,148, + B/SRO/converted ~2,960.
Presence spot-check n=9: pre-1929 **4/7**, post-1929 **0/2**. **Class does not
predict it** — read the flag per building. Bulk API is key-gated; not swept.

## 2. 1940s TAX PHOTOGRAPHS — 1939-1951, bulk 1939-41 · FREE

`nycrecords.access.preservica.com/1940s-tax-photographs/` (DORIS/Preservica;
the old Luna endpoint is dead). Collection REC0040 · **722,485 images on 130
reels** · arranged by borough then **BLOCK and LOT** — BBL-keyed, spine-joinable.

⚠ DORIS's own caveat: *"some tax-exempt buildings, parcels with vacant lots or
those missed by the original photographers will not be found."* Original
negatives are restricted (nitrate film); the digitised images are the access copy.

## 3. 1980s TAX PHOTOGRAPHS — 1982-1987 · FREE

Same portal. Department of Finance, 35mm, **a second comprehensive census of
every property**. Sits precisely in the gap between the I-card era (~1985) and
BIS (2000). Two photographic censuses ~45 years apart give a visual before/after
on any lot without a single document request.

## 4. BSA — dense 1998 → 2026 · FREE PDFs

`yvxd-uipr`, **10,805 rows**, `decisions_url` on **100%**, block+lots on 99.75%.
Types: BZ 4,182 · Appeal 3,449 · SOC 2,910 · BZY 257.
Status: Granted 8,934 · Withdrawn 1,112 · Denied 525 · Dismissed 227.
Carries the **ZR `section`** relied on (§72-21, §73-xx) and `zoning_district`.

⚠ **It does NOT reach the 1930s-40s.** Filed-year density: 1968=2, 1986=1,
1994=1, 1996=1, then **1998=484** and 100-560/yr after. Four strays before 1998.
The "calendar numbers to the 1930s-40s" claim describes BSA's *numbering system*,
not this dataset.
⚠ **Calendar-number format flipped**: old `434-68-BZ` = seq-year-type; new
`2025-13-BZ` = year-seq-type. Parse both or you get nonsense years.
⚠ PDFs 403 from a plain client; browser only.

## 5. HISTORICAL DOB PERMITS — 1989-05-11 → 2013-04-24 · FREE

`bty7-2jhb`, **2,428,526 rows**. The deepest DOB layer and previously untouched
by this project. Uniquely carries `owner_s_house` / `_street_name` / `_city` /
`_state` / `_zip`, `owner_s_phone`, `permittee_s_phone`,
`superintendent_business_name`.
⚠ **Fifth key convention**: `borough='QUEENS'` upper + **UNPADDED** block/lot.
The padded form returns 0 rows and reads as "nothing here".

## 6. DOB PERMITS — ≥1992 → 2022 · FREE

`ipu4-2q9a`. `permittee_s_phone__` on **99.6% of 3,989,787**.
⚠ `issuance_date` mixes `01/01/2007` and `2020-06-05` formats in one text
column — min/max on it lies.

## 7. BIS JOBS — 2000-01-01 → 2025 · FREE

`ic3t-wcy2`, hard floor at 2000. ⚠ `bbl` column holds a **BIN on 32.6%** — build
the key from borough/block/lot. ⚠ A row is a job DOCUMENT (`doc 01` original,
`02+` amendments that restate nothing).

## 8. B-SCAN JOB DOCUMENTS — 2008 → · FREE

`my_community.jsp` → `JobsQueryByNumberServlet` → `BScanVirtualJobFolderServlet`
→ `BScanJobDocumentServlet?scancode=` → `BSCANJobDocumentContentServlet` (PDF).
Folder rows carry `Form ID · Doc No · PAA · DATE SCANNED · SCAN CODE`.
**Measured floor 2008**: 2000/2003/2005/2007 all return "No Scanned Documents
Found For This JOB"; 2008 returns 15. ⚠ Not 100% after 2008 either.
⚠ Akamai visitor queue — **wait, never refresh**.

## 9. DOF DIGITAL ALTERATION BOOK — 2008-05-20 → · lineage · FREE

`dof_lineage.py`. `Lot_Action` (Added/Dropped/Affected) + `Auth_for_Change`.
Citation rates over all 77,931: **CRFN 49.1%**, DOB job **8.3%** — and by type,
**Lot Apportionment 24.5% DOB / 53.0% CRFN** vs **Lot Merger 0.9% / 55.7%**.
★ Apportionment is the construction signal; merger is the title signal.
⇒ Use DAB→ACRIS as the join; take DOB citations as corroboration (98.3% precise).

## 10. DOB NOW — 2016 → now · FREE

`w9ak-ipjd` + the public portal. Portal Filing Details (**double-click** grid
rows) → Plans/Work (PW1) · **Zoning Information** · Scope · TR1 · TR8 · EN2 ·
PW2 · AHV · Withdrawal/Supersede · Statements & Signatures · Documents.
★ Zoning Information carries what the extract does not: districts **with
per-district area**, lot area total, lot width/type, **street legal width**,
yards, height & setback, pre-1961 flag, zoning-lot-certification flag, and an
`Auto Populated` flag telling you whether the applicant keyed it.

## 11. CERTIFICATES OF OCCUPANCY

`bs8b-p36w` (143,061) + `pkdm-hqz6` (80,082). ⚠ Not additive — 14,793 job
numbers appear in both. ⚠ **No temporary/final flag published** — delivered vs
complete must be read off the portal.

---

## UNTESTED — listed so they are not mistaken for absent

* **DOB records request** (pre-BIS job numbers, microfilm, docket books, reels).
  Deliberately not pursued — needs an eFiling account and a borough pickup.
* **DORIS building plans / docket book / block-and-lot collections** — the
  collection guides exist (`a860-collectionguides.nyc.gov`); contents not tested.
* **LPC designation reports** — often the fullest building history for
  landmarked and historic-district properties. Not tested.

## The rule that governs all of it

No layer is a superset of the layer below. Queens 17/1: the permits feed held
five jobs the jobs feed did not, **and** the jobs feed held one the permits feed
did not. Resolve the site identity set first (every BBL ∪ every BIN), fire all
layers against it in parallel, merge on date, segment at the demolitions —
and control every query before reporting an absence.
