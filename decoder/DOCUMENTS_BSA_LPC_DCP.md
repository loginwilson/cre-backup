# What to decode from BSA, LPC and DCP — measured 2026-08-06

Everything below is a count taken today, not a repetition of the brief. Where a
number here contradicts `DECODER_CHATS.md` or `KICKOFF_PROMPTS.md`, this file is
the one that was measured.

---

## The question that decides whether a document is worth opening

For each source, one question ranks everything:

> **Does the binding fact exist in the structured feed, or only in the document?**

That is the same question DOB answers with "the ZD1 is the only source for
two-thirds of envelope filings". Asked of these three sources it gives three
completely different answers, and the answers — not the row counts — are what
determines the work.

| source | the binding fact | in the feed? | document needed |
|---|---|---|---|
| **BSA** | the varied envelope (floor area, FAR, units, height) and the conditions | **no — the feed carries no number at all** | **every granted dimensional case** |
| **LPC** | designated / not, when, which lot | **yes, per BBL, 100%** | only 1,493 rows, and only for the boundary |
| **DCP** | which parcels, and the approved action | **no — the export drops the BBLs** | every project, for the parcel link alone |

---

## 1 · BSA — 10,805 applications

### Corrections to the brief, measured

| | brief said | measured today |
|---|---|---|
| BZ | 1,859 | **4,182** |
| Appeal | 1,668 | **3,449** |
| SOC | 1,350 | **2,910** |
| BZY | — | **257** |
| total | 10,805 | 10,805 ✔ |
| decision PDFs | "100% carry decisions_url" | 100% carry a **URL-shaped string** — see below |

**`decisions_url` is a formula, not a link.** All 10,805 rows equal
`.../decisions/<calendar>.pdf` exactly, with zero exceptions. Nothing in the
feed asserts the file exists. Probed by decade (14 per decade, HEAD):

| decision decade | rows | sampled | 200 | 404 |
|---|---|---|---|---|
| 1990s | 573 | 14 | 13 | 1 |
| 2000s | 4,785 | 14 | 14 | 0 |
| 2010s | 3,948 | 14 | 14 | 0 |
| 2020s | 1,496 | 14 | 12 | 2 |

The 404s cluster in **recent** cases — decided but not yet posted. A queue
sorted newest-first therefore maximises its own failure rate: the first pilot
took 8 404s in 40 because of the sort order, not because of the corpus.

### The document, section by section

A resolution is one PDF, 1–18 pages, with a fixed skeleton:

| section | what it yields |
|---|---|
| header p1 | calendar no · **premises block/lot as the Board states it** · action · vote · DOB job number (carries the `-I1` suffix — the DOB join) |
| THE RESOLUTION p1 | the **DOB objection quoted verbatim** — the authoritative list of what was waived, with ZR cites |
| The Request | the relief in one sentence, "contrary to §§ …" |
| Location | **lot area** (the *zoning* lot, which is not the tax lot) |
| Proposal | what was applied for — floor area, FAR, units, height, coverage, parking |
| *(the district recital)* | **the as-of-right maximum** — the baseline that makes relief computable |
| Findings (a)–(e) | the legal test; no dimensions |
| Decision | "Therefore it is Resolved … on further condition:" then the **THAT-clauses**, which bind the parcel permanently and must appear on the CO |
| Certification | the date the resolution was **filed** — the second date axis |

Both date axes are present on the same page pair: 2025-12-BZ was **adopted
June 1, 2026** and **filed June 26, 2026**. `happened` and `recorded`, exactly
as the ledger wants them.

### What is worth decoding, in order

1. **BZ, granted, dimensional — the whole point.** 4,182 BZ, of which 3,433
   granted. Of those, the ones whose relief touches bulk rather than use.
   Pilot split: **bulk 21 · both 3 · use 7** of 31 readable.
2. **BZY (257)** — vested-rights extensions. Establishes that a lapsed permit
   still runs, which is a live-development signal.
3. **SOC (2,910)** — extensions of term/time on an existing grant. These change
   *when* a burden expires, not what it is.
4. **Appeal (3,449)** — mostly DOB determinations and GCL 35/36 (Common Law
   Vesting 513, GCL 36 1,450). Envelope-relevant only occasionally.

### Coverage, on the honest denominator

Extraction of the granted envelope, over the 31-decision pilot:

| population | found | rate |
|---|---|---|
| all readable decisions | 17/31 | 55% |
| dimensional (bulk or both) | 17/24 | 71% |
| **dimensional AND multi-page** | **17/19** | **89%** |

The three denominators differ because two whole populations legitimately have
nothing to find:

* **use variances state no dimension** — 0/7, correctly. A §72-21 that varies
  the use group does not touch the envelope. Counting them as misses would have
  understated the decoder by 20 points and hidden the two real failures.
* **1-page decisions** (5 of 31) are short-form orders and withdrawals. There is
  no resolution body to read.

### Traps, each of which cost a wrong answer first

1. **The index lot is not the parcel.** 2025-12-BZ: index says Block 10789
   Lot 0027; block 10789 *has no lot 27*; the resolution says **Lot 271**, which
   PLUTO gives as 220-28 Jamaica Avenue — the address the index itself carries.
   Across all 2015+ single-lot cases, **20.4% of index BBLs (461/2,259) do not
   exist in PLUTO**: 450 ground lots, 11 condo/REUC unit lots. Address-matching
   the misses on the same block repairs 39, and **almost all of those repairs
   are `75xx` condo billing lots** — the index BBL was right when filed and the
   lot has since been retired into a condo. So the field is a filing-time
   snapshot on top of a lineage problem. `index block/lot == document block/lot`
   is now a standing self-check.
2. **`lots` is free text, truncated at 20 characters.** 1,365 of 10,805 rows are
   non-numeric. Real values: `1,28,29,30,105,1001-`, `82,83,84,85 (tent 82`,
   `p/o 19 (tent 25 & 27` — each cut mid-lot. A multi-lot assemblage variance
   cannot have its parcel set read from the index at all.
3. **`tent.` means the lot does not exist yet.** `50, 63 (tent. 52)` is a merger
   that has not happened. Treating it as a BBL invents a parcel.
4. **403 on robots.txt was a user-agent block, not a refusal.** Default
   python-urllib gets 403 from `www.nyc.gov/robots.txt`; any descriptive UA gets
   200 and the policy is `Disallow: /html/misc/` and nothing else. *Worth
   passing to the DOB chat, whose brief is blocked on "both DOB hosts 403 their
   own robots.txt" — that is the same symptom.*
5. **Granted and permitted are worded identically.** "a maximum building height
   of 55 feet" (district, p4) and "a maximum building height of 122 feet"
   (granted, p11). Only position separates them, so a whole-document match
   always returns the district figure and every variance silently grants zero.
   Fixed by matching each layer only inside its own region; guarded by a check
   that at least one granted parameter must differ from its permitted twin.
6. **The same numbers appear twice, on different pages, meaning different
   things** — once in Proposal (asked for), once in Decision (granted). Citing
   the wrong one gives a real page, a real number, and the wrong legal force.
7. **The roman numeral moves.** "Proposal" is section III in 19 resolutions and
   IV in 3, because a "Board History" section is inserted on re-opened cases.
   Anchor on the name. 24% of resolutions use a different scheme entirely
   ("I. The Premises", "III. The Zoning Resolution") — a different format, not
   a broken one.
8. **The running header lands inside sentences.** Unstripped, the text reads
   `dwelling unit (Z.R. 2025-12-BZ 2 §§ 23-52(b)`, so any pattern crossing a
   page break captures the calendar number as part of the citation.
9. **A ZR section and a Queens house number are the same shape.** `220-28
   Jamaica Avenue` vs `23-52(b)`. Zoning chapters are 1–2 digits; without that
   guard every Queens premises line contributes a fictitious section.
10. **The zoning lot is not the tax lot.** 2025-12-BZ states 51,170.80 sf of lot
    area; PLUTO gives the tax lot as 60,610 sf — **18% apart**. An FAR taken
    over the wrong one is wrong by that margin, so the stated area is stored as
    its own fact.
11. **A grant is not always a grant.** 1,112 Withdrawn and 525 Denied. Emitting
    `variance_granted` for those would put floor area on a parcel that never
    got it.
12. **Split sites cannot be reduced to one number.** 2025-28-BZ caps lot
    coverage separately in its R6A/BR and R5B/BR portions. Taking the first
    figure attributes a portion's cap to the whole parcel; those cases are
    flagged `multipart` and their caps carry "NOT site-wide".

---

## 2 · LPC — the designation is already structured; the document is not the work

**`ncre-qhxs` — 39,363 rows, every one with a BBL and a designation date.**

    lm_type      Historic District  36,936 · Individual  2,065
                 Scenic 212 · Interior 150
    lp_number    1,769 distinct designations
    bbl          33,736 distinct parcels, 100% populated
    desdate      100% populated

⚠ **Every row reads `status = DESIGNATED`. There are no calendared rows.** Both
the brief and `lpc.py`'s docstring describe this dataset as "designated AND
calendared" and treat the calendared population as its headline finding — the
building that is constrained in practice with no recorded instrument behind it.
**That population is not in this feed.** Whatever is true about calendared
buildings has to come from somewhere else, and until it does, it is unknown
rather than absent.

**So LPC needs almost no document decoding.** The binding fact — this BBL is
landmarked, of this type, on this date — is fully structured. The designation
report adds architectural description, not constraint.

The exception is precise and small:

    boundaries = 'See designation report'      1,014
    boundaries = 'Partial lot' / 'Partial Lot'   479
    boundaries = 'Irregular'                      15
    ------------------------------------------------
    rows whose extent the feed does not state  1,508

Those 1,508 are the only LPC rows where the report is the sole source, and what
it supplies is the boundary — *which part of the lot is regulated*. Everything
else is `Block & Lot` (37,829) and needs nothing.

⚠ Access is **unresolved and does not need resolving yet**: designation reports
sit on `s-media.nyc.gov`, which returns **404 on robots.txt** — no policy
published at all. A 404 is not a 403 and not a permission. Since the documents
are not needed for the binding fact, this stays an open question rather than a
blocker.

**The LPC document that does matter for development is the permit**
(`dpm2-m9mq`, 349,692 rows) — and only one of its types:

| regulation_type | rows | envelope? |
|---|---|---|
| Certificate of No Effect | 137,723 | no — by definition no exterior effect |
| Permit for Minor Work | 52,624 | no |
| Expedited CofNE | 33,712 | no |
| **Certificate of Appropriateness** | **10,051** | **yes — this is what authorises a new building or enlargement in a historic district** |
| Commission Denial | 1,289 | yes, negatively |

That is the LPC analogue of a BSA variance: **10,051 CofAs**, not 349,692
permits. ⚠ The permits table has no `bbl` column — it keys on
borough/block/lot with borough spelled as a title-case name, a fourth
convention among LPC's five datasets.

---

## 3 · DCP — the feed drops the one field that joins to a parcel

**`hgx4-8ukb` — 32,931 projects.** Every project has an id, an applicant, a
borough, a status and a brief.

⚠ **No BBL. No block. No lot. No address.** Not one of the 32,931 rows carries a
parcel identifier of any kind. The finest geography in the export is the
community district.

**But the ZAP project page has them.** `zap.planning.nyc.gov/projects/2019K0147`
renders `BBLs: 3074230011 3074230036 3074230038` along with the action list and
a Public Documents section. So the parcel link exists at DCP and is **stripped
in the Socrata export** — the same shape as DOB's ZD1 gap, except that here what
is missing is not a measurement but the join itself.

⚠ **The `actions` column is populated on 1,480 of 32,931 rows — 4.5%.** The
action is instead recoverable from the ULURP number, which encodes it
(`220026ZMK` = ZM, Brooklyn): **27,968 rows, 84.9%.** A census taken from the
`actions` column understates every action type by a factor of ~19.

Parsed properly, the envelope-bearing population:

| code | projects | what it does |
|---|---|---|
| **ZM** | **1,575** | zoning **map** amendment — the district itself changes. The largest envelope change there is. |
| **ZS** | **1,392** | CPC special permit — conditions bind the site, like a BSA variance |
| **ZR** | 1,021 | zoning text amendment |
| ZC | 1,865 | certification |
| ZA | 1,653 | authorization |
| | **7,506** | projects carrying a zoning action, of 32,931 |

Non-zoning bulk: RC 4,979 · PP 3,171 · UC 1,992 · EC 1,549 · TC 1,409 — renewals,
dispositions and city-property actions, which are ownership signals rather than
envelope ones.

⚠ **`4j6i-9rmr` is 91 rows, not a ULURP universe.** The brief lists it beside
ZAP as though the two were comparable. It is a small table of community-board
and borough-president recommendations. The ULURP universe is inside ZAP.

**What to decode from DCP, and in what order**

1. **The ZAP project page itself, for the 7,506 zoning-action projects — for
   the BBLs.** This is the highest-value retrieval of the three sources, because
   without it 32,931 DCP projects cannot be attached to any parcel at all.
   ⚠ The page is a client-side app: the served HTML is an empty shell and the
   data arrives through the app, so a plain fetch returns nothing. Policy is
   permissive (`zap.planning.nyc.gov/robots.txt` = `Allow: /`); the open item is
   *how* to read it, not *whether*.
2. **CPC reports for ZS (1,392)** — the special-permit conditions, the direct
   analogue of the BSA THAT-clauses.
3. **ZM (1,575)** — the district before and after. The action's existence is
   already a fact; the document supplies the boundary.

---

## Addendum — the LPC and DCP documents, read rather than described

### The CofA is a permit that states no number

Read end to end: **COFA-25-07271**, 244 Waverly Place, Greenwich Village
Historic District, 6 pages.

A BSA resolution states an envelope — 232,985.77 sf, 4.55 FAR, 310 units,
122 ft. **A Certificate of Appropriateness states none of that.** There is no
floor area, no FAR, no height, no unit count anywhere in it. Every dimension is
local and incidental: "shifted approximately 5′ farther east", "an approximately
6′-8″ portion".

⚠ A decoder written on the BSA template would report this document as empty. It
is not empty — it is a different kind of statement:

> **BSA** says *this parcel may hold 232,985.77 square feet.*
> **LPC** says *this parcel may be changed in this way, and not otherwise.*

The CofA regulates **form, not quantity**. What it yields a parcel ledger is the
approved work — and specifically whether that work enlarges the building:

    "constructing a gray-finished metal-clad, one-story rooftop addition"
    "reducing the footprint ... reconstructing the façade in a new plane"

**What the document has that the feed does not:**

| | |
|---|---|
| **public hearing + public meeting dates** | the feed has only `received_date` and `issue_date`; the actual decision date is document-only. Here: heard Dec 10 2024, decided Jan 14 2025, issued May 16 2025 — **three dates, and the feed carries one of them** |
| **the approved-work narrative** | 5,518 characters of exactly what may be built. The feed compresses this to a `worktypes` code, and 1,664 CofA rows carry the code `Legacy- Not Available` |
| **the findings** | 11,928 characters of *why* it was approvable — which is what predicts whether the same proposal next door will be |
| **RCNY Title 63 sections** | the LPC analogue of a ZR cite. §2-15 is *"Rooftop and Rear Yard Additions or Enlargements"* — finding it is the strongest in-document signal that the building got bigger. 14 sections cited on this one permit |
| **the design team** | Juliet Hernandez-Eli RA, Stephen Lampard PE, Gregory C. Moormann PE, Florinela Muresan PE — named on the drawing list. The feed's `applicant_name` is one person |
| **the consultant chain** | `cc: Emma Waterloo, Deputy Director; JM Zoning` — the expeditor actually running the job |
| **a document chain** | the permit cites LPC 03-5929, LPC 25-04036, LPC 25-10753 by number |
| **the owner entity** | Roundsquare Development LLC, 147 West 35th Street — the feed's `owner_name` is the individual |

⚠ **Retrievability is a hard cutoff at 2016.** Sampled 4/year by HEAD:
2012–2015 → **0/4 every year**; 2016 → 3/4; 2017–2026 → **4/4 every year**.
So of 10,051 CofAs, **2,870 have a document and 7,181 predate the archive**.
Reporting CofA coverage without that denominator would present a 28% result as
a 100% one.

⚠ **The stop word is inside the prose.** The findings capture first ended at
`/Therefore/` — and LPC findings are written *"…with the loss of both stoops,
**therefore** the proposed alterations will bring it closer…"*. The capture
stopped 168 characters in, on the first clause, and looked like a success. Real
terminators are structural (`is being issued`, `SHOP DRAWINGS`), not rhetorical.
Fixing it took the findings from 168 to 11,928 characters.

### DCP: the document inventory is public; the documents are not

The ZAP API catalogues every filed document per project — name, artifact type,
upload date, SharePoint location. Measured over the run so far: **8,627
documents across 201 resolved projects, ~43 per project.** The names are
self-describing and the envelope ones are obvious:

    10. Zoning Comparison Table.pdf        <- district before vs after: the envelope
    11. Zoning Change Map.pdf
    1. Project Description.pdf
    EAS-2959-Avenue-Y-042224-11-19.pdf     <- the RWCDS, with floor areas
    25. Proposed Zoning Text - Appendix F - MIH.pdf

⚠ **The files themselves return HTTP 401.** All three plausible retrieval forms
against `nyco365.sharepoint.com` — folder+filename, site+serverRelativeUrl, and
the SharePoint `download.aspx?SourceUrl=` form — return **401 Unauthorized**.
So DCP is split cleanly: **the inventory is fully obtainable and the content is
behind authentication.** That is the DOB situation exactly — ask, do not probe —
and it is recorded here as an open question rather than worked around.

⚠ **90% of the DCP queue is a paper-era stub.** Of 7,102 envelope-action
projects, **6,391 carry a `P`-prefixed legacy id** (P1977K0071, P1977Q0168) —
records migrated into ZAP from before the digital era. Measured on the first 285
pulled: **205 returned no BBLs at all, and every one of those 205 was
P-prefixed.** They have no geography and no documents. The first run order
front-loaded them and spent its first hour on records with nothing in them; the
queue now sorts modern-first, and the resolution rate went from 28% to ~47% on
the same corpus.

**This is the second time queue order decided what a partial run was worth** —
BSA sorted newest-first ran straight into the decisions that have not been
posted yet. Order is not cosmetic.

---

## Audit against RULE_DOCUMENTS_NOT_INDEXES

Three decoders, audited against the rule after it was handed down. Two of them
were violating it, and the third only partly.

### DCP — retracted in full

`dcp.py` wrote **695 facts sourced entirely from the ZAP project record**, each
carrying `page="project-record"`. That is not a page. It satisfied the `Fact`
validator — which exists to prevent this exact thing — without there being any
paper to walk back to. A case-management detail screen is the rule's own example
of what may not be a source.

All 695 are retracted in the sink. `to_facts()` now returns `[]` and says why in
its docstring. DCP's honest position:

| | |
|---|---|
| finding aid | **complete** — 1,983 BBLs and a `source_documents` row for every filed document |
| decode | **not started** — 0 documents read, therefore 0 facts |

Those two must not look alike, which is why the run now heartbeats
`FINDING AID ONLY — 0 documents read, therefore 0 facts by design` rather than
reporting a clean completion. Every document row is written `decode_status:
unread` with `unread_reason: HTTP 401`.

⚠ A second, quieter failure surfaced immediately: the document classifier scored
**64 of 65 as `unclassified`** while looking like it worked. DCP names files
`01.-Project-Description.pdf`, and patterns written with `\s*` between words
match none of them. The index was not just an illegitimate source — it was being
read badly. Normalising hyphens first fixed it.

### BSA — the outcome was index-sourced

`to_facts()` decided whether to emit `variance_granted` from the **index's
`status` column**, on a document that states the answer in capitals on page 1:

    ACTION OF BOARD — Application granted on condition.

And every BBL took its borough from the index's `borough_code`, on a document
whose first line reads `PREMISES: 220-28 Jamaica Avenue, Queens`.

Both now come from the resolution, and the index is demoted to what the rule
permits — a free independent witness. On the first 91 decodes of the corrected
run it is already earning that role:

    bbl provenance      document 82 · borough_from_index 5 · insufficient 4
    outcome (document)  granted 79 · withdrawn 7 · denied 1 · not stated 4
    check failures      index block/lot disagrees      5
                        index status disagrees         4
                        pages_read < pages_total       4
                        index borough disagrees        2

The index disagreeing with the document four times on the outcome is the point.
Under the old code those four would have been silently decided by the index.

### LPC — an index value wearing a document citation

`verbatim` fell back to the feed's `worktypes` code when the approved-work
narrative failed to extract, and `historic_context` was taken from the feed's
`lmnametype`. A permit whose narrative could not be read is a permit that has
not been decoded; it now emits nothing and says so. The historic district is
printed in the permit's own header and is read from there.

### The completeness test, on every fact

`pages_read / pages_total` now rides on every BSA and LPC fact, and
`pages_read == pages_total` is a self-check. It already fails on 4 of 91 BSA
decodes — PDFs with a page that yields no text inside an otherwise readable
document. Those are pages present and unread, which is not the same as pages
that say nothing, and previously nothing recorded the difference.

⚠ **Still unread, and recorded as such:** every BSA resolution references its
`"Approved Plans" — Twenty-Five (25) sheets` and a DOB job number. Those are
separate documents this decoder has not opened. The resolution is the binding
instrument, but `documents_read / documents_exist` for a BSA case is 1 of at
least 2.

---

## Where this leaves the three sources

* **BSA** — the documents *are* the data. Decoding is the whole job, it is
  running, and it works at 89% on the population that has anything to say.
* **LPC** — the documents are almost never needed. 39,363 designations are
  already per-BBL; 1,508 rows need a boundary from a report, and 10,051 CofAs
  are the envelope-relevant permits hiding inside 349,692 rows.
* **DCP** — the documents are needed for a reason no one would guess from the
  brief: not for numbers, but because the export has no parcel key at all.
