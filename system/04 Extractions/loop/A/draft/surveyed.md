# SURVEYED — A, Block 1 drafting phase

Everything I opened while drafting, and what it taught me. Split by depth,
because "I read the images" and "I read the registration" are different evidence
and a Block 3 comparison of corpora needs to know which.

**Where the packages are.** I built survey packages into
`loop\A\scratch\docs\<id>\` rather than the shared `loop\docs\`, using a wrapper
(`loop\A\scratch\pkg.py`) that imports `bin\docpkg.py` and changes only the
output root — same module, same fitz, same 300 dpi, so the renders are identical
to what `docpkg.py` produces. Reason: `loop\docs\` is the shared package
directory, and building there during a blind phase would publish to B the list
of ids I chose to look at. That is a one-way leak I can avoid at zero cost. If
the orchestrator wants these in the shared tree, they can be rebuilt byte-for-
byte from the ids below.

## 1 · READ AS IMAGES

| id | type | pages read | what it taught me |
|---|---|---|---|
| `2002122000002001` | SATISFACTION OF MORTGAGE | p01–p02 | The ACRIS cover page is generated from what the presenter typed and says so: *"will control for indexing purposes in the event of any conflict with the rest of the document"* — **indexing**, not the legal act. Drove R-INP-8. The body's *"which Mortgage HAS NOT been assigned of record"* is an affirmative negative, next to a blank "List of Assignments:" that is not — the pair is the whole of R-NULL-2. The recited $366,000 principal belongs to the referenced mortgage, not to this act (R-QTY-6). Panel 1 is the borrower; the party who executes is panel 2 (R-PARTY-1). |
| `2002122700153001` | DEED, 1-2 FAMILY | p01–p08 + 3 zooms | The single most productive document I opened. Cover says "PAGE 1 OF 5"; the PDF has **8** images, and pages 6–8 are a SUPPORTING DOCUMENT COVER PAGE, an RP-5217 and a smoke-detector affidavit — carrying the sale price, the assessed value, the use class and the occupancy assertion. A reader who trusts the page count loses four of the eleven columns. This is R-INP-2 and half of M-DEED. Body recites `$10.00`; registration says `$525,500.00`; the two are different fields, not a contradiction (M-DEED consideration ladder). Schedule A is a **title insurer's** page bound in — its metes and bounds are incorporated, its insurance solicitation is not (R-INP-4). Grantors are "AVINADAV SIEV AND PAZIA SIEV, HIS WIFE": relationship word, no share stated (R-PARTY-6, R-PARTY-7). The covenant against grantor's acts is a **scoped** ASSERTED_NONE with "except as aforesaid" (R-NULL-3). |
| ↳ zoom `p07` @900dpi | RP-5217 field 12 | | Full Sale Price is handwritten and the second digit reads `4` or `2` — 545,500 or 525,500. The registration says 525,500. This is a real document ambiguity with a cross-source resolution, and it is the case R-INP-6 exists for. It also showed me what **not** to do: NYS RETT $2,102.00 resolves it arithmetically, but only if you supply a tax rate the document never states — hence R-NEV-9. |
| `2002122700120002` | MORTGAGE | p03, p04, p22 | Fannie/Freddie Form 3033. Principal `$384,900.00` and maturity `December 1, 2032` are stated in the definitions section; **the interest rate is not** — it lives in the note, which is not recorded. That is R-TERM-2, and it is the cleanest example I found of an `UNKNOWN` that is a complete answer rather than a flag. Rider checkboxes: 1-4 Family and Mortgage Insurance checked, Adjustable Rate not — which asserts no such rider, not a fixed rate (R-TERM-3). PDF p22 is printed "Page 14 of 17": printed numbering does not track image order (R-INP-3). |
| `2002122000027001` | ASSIGNMENT, MORTGAGE | p02 | Critical values are **handwritten into a printed form**: recording date, book, page, block, lot, execution date. The county of record is **blacked out**, and the address makes it obvious — which is exactly the inference R-INP-5 and R-NEV-10 forbid. `prior assignments:` blank, with no affirmative statement anywhere: `UNKNOWN`, and the contrast with the satisfaction above is what makes R-NULL-2 falsifiable. |
| `2003010600117004` | AGREEMENT (NYBTU 8026 consolidation) | p03 | The document I would have got most wrong without reading one. Party of the first part is the **holder of the mortgages**, party of the second part the owner — the exact inversion R-PARTY-1 forbids you to assume. Two recited mortgages, one with a handwritten *"WHICH MORTGAGE HAS A REDUCED PRINCIPAL BALANCE OF $369,432.74"*, the other `$1,530,567.26` recorded "contemporaneously herewith" with the printed liber/page **struck through with XXXX** (R-INP-5). The two sum to exactly $1,900,000 — a derivation I am allowed to show (R-QTY-5) but must not allocate across the four indexed BBLs (R-QTY-3). Marginal handwriting "MTGE TAX PAID: $42,091.50" is content, of unknown authorship. |
| `2003010600065002` | EASEMENT (façade preservation) | p03 | The restrictive-declaration boundary case in the flesh. It burdens the parcel, runs with the land, reserves rights, constrains the building — and states **no quantity or dimension**. Under my cell schemas that is `ENCUMBRANCE` and not `ENVELOPE`, and it is the document that convinced me the boundaries have to be settled by defining what a cell *holds*, not by describing what a function *means*. |
| `FT_1000000027200` | DECLARATION, 1981 (film) | p01 | Film-era documents have **no ACRIS cover page** — the instrument starts at p01 with a reel/page stamp in the margin. The registration has no `doc_date`, so the only date in the JSON is the recording date; the instrument's own date ("this 19th day of March, 1981", the day handwritten) is on the image. Drove R-INP-9 and the warning against letting a missing `doc_date` trigger date fallback. Content named `Alteration Application #601/80` and a BSA application, and a 60-foot clear-distance requirement — `PERMIT` + `ENTITLEMENT` + a stated dimension, which is why `ENVELOPE`'s cell includes dimensional limits on building position. Scan quality is materially worse: dark borders, speckle, photographed against black. |
| `RC_1000046` | ASSIGNMENT OF LEASE (Richmond) | p01 | A **different cover page entirely** — Richmond County Clerk format. Three identifiers for one document: navigation id `RC_1000046`, "Document Id: 000000000479148", "LAND DOC# 451358". The cover states a Document Date (10/25/2012) that the registration JSON does not carry at all. `PROPERTY DATA # OF LOTS 3` but only one lot is printed, followed by *"And Addl Blocks and/or Lots"* — while the registration lists all three. Neither source is complete, which is R-PARCEL-4. BBL `5075110001` confirmed the 1+5+4 digit grammar. |
| `2003010500041001` | INITIAL UCC1 | p03 | UCC1 Addendum: box 13 "fixture filing" checked, field 14 carries the real-estate description as `Section: 09 / Block: 2764 / Lot: 08` — a section number, not a BBL. Field 15 (record owner) and field 16 (additional collateral) blank: `UNKNOWN`, not none. Confirmed M-UCC. |
| `BK_6620000200233` | ASSIGNMENT, MORTGAGE, 1966 (book) | p02 | Seventeen indexed parties. The body shows why: one assignor and a dozen assignees, several of whom appear **twice in different capacities** ("JEROME OSINOFF, individually and as custodian for ROBERT OSINOFF … under the New York Uniform Gifts To Minors Act"; "JEROME ZUFLACHT, individually, as executor of the Estate of Phyllis Zuflacht, deceased, and as successor custodian for …"). No shares stated anywhere — R-PARTY-6. The register's index **inverts** the custodianship, listing the minor as the party with "CUST OF" appended; that is a semantic corruption, not just truncation, and it produced R-PARTY-8. Nominal consideration recital again. Handwritten liber/page partly illegible. Bound-book scan against black with a curled corner. |

## 2 · READ AS REGISTRATION ONLY

| id | why I pulled it | what it taught me |
|---|---|---|
| `FT_1000000016200` | largest parcel count in my sample | DECLARATION, 113 pages, **129 parcels**: old Lot 30 plus condo unit lots 1001–1128. The canonical `IDENTITY.CREATE` case and the reason M-DECLARATION carries a condominium branch. Its `parcels[].remarks` read *"DECL/CONDO FKA LOT 30 NKA LTS 1001-1128 CORRECTED FROM R642 ON 11/14/89"* — an index annotation added seven years after recording, which is why `remarks` is non-citable in R-INP-7. |
| `2002122000012001` | zero-parcel document | POWER OF ATTORNEY with **no `parcels` key at all**. Forced R-PARCEL-6 and the M-AUTHORITY zero-event rule. |
| `RC_1000046` | Richmond registration shape | Different schema from ACRIS: `doc_type`/`instrument`/`book`/`page`/`status`/`image_state`, parties carrying an explicit `role` plus `person`/`company` columns, parcels carrying `bbl` only. Parties are **case-variant duplicated** ("SOVEREIGN BANK, N.A." as both `ASSIGNEE` and `Assignee`) — four entries for two parties, hence the dedup in R-PARTY-4. |
| `BK_6620000200233` | 17-party outlier | Confirmed the index truncation ("ROBERT OSINOFF CUST OF") before I read the body and learned it was also inverted. |

## 3 · SAMPLED CENSUS (not individual documents)

`loop\A\scratch\census.py` — bounded id-range walks from 18 start points across
the ACRIS-digital, film, book and Richmond namespaces, 400 rows each, no full
scans. **2,373 readable rows** (`pdf LIKE '%.pdf'`) tallied by type.

Result, ordered: `(none)` 1195 — all Richmond, which carries `doc_type` instead
of `type` — then MORTGAGE 337, DEED 322, ASSIGNMENT MORTGAGE 172, SATISFACTION
OF MORTGAGE 121, AGREEMENT 81, POWER OF ATTORNEY 54, SUNDRY AGREEMENT 32,
DEED OTHER 13, RELEASE 13, LEASE 7, ASSIGNMENT OF LEASES AND RENTS 6, then
single digits of INITIAL UCC1, MISCELLANEOUS, CONTRACT OF SALE, INITIAL COOP
UCC1, DECLARATION, SUNDRY MISCELLANEOUS, UCC3 TERMINATION, ASSIGNMENT OF LEASE,
EASEMENT, CERTIFICATE, VACATE ORDER.

What that shaped:
- **Five types are ~95% of the corpus.** The module set is sized to that, and
  M-GENERIC has to be genuinely usable rather than a stub, because `(none)`,
  `AGREEMENT`, `SUNDRY AGREEMENT` and `MISCELLANEOUS` together are a large,
  heterogeneous tail whose registration type tells you nothing.
- **`AGREEMENT` is not a document type.** It covered a consolidation agreement,
  a spreader, and things I did not open. The module has to send you to the
  instrument's own title.
- Outliers worth targeting later: `2003010500008001` MORTGAGE over 13 parcels;
  `BK_6620000100166` MORTGAGE over 39 parcels with 9 parties;
  `FT_1000000033900` AGREEMENT over 25 parcels; `RC_1000106` over 74 parcels;
  `2003010600117001`–`005`, a five-document closing package on the same 4 BBLs
  (deed, assignment, mortgage, agreement, miscellaneous) — five separate
  independent reads, which is a good later test of whether the framework keeps
  them separable.

## 4 · BUILT BUT NOT READ

`2003010600065003` (LEASE), `2003010600117005` (MISCELLANEOUS, 4 parcels),
`2003010600155003` (ASSIGNMENT MORTGAGE, 3 parcels). Packages exist in my
scratch tree; I stopped reading when the marginal document stopped changing a
rule. Recording them here so the gap is visible rather than implied: **I wrote
M-LEASE without having read a lease**, which is the weakest module in the draft
and I have said so in `draft-notes.md`.
