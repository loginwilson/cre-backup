# NYC C.R.E.D. EXTRACTION FRAMEWORK — v1 (A draft)

Turns one recorded instrument into an event table. Read the document, apply the
rules, emit events. Nothing here asks you to know New York real estate.

**Rule ids are immutable.** A rule may be rewritten, deprecated or deleted; its
id is never reused for different content.

## 0 · LOADING CONTRACT AND SIZE BUDGET

You load **CORE** (§1–§15), **exactly one TYPE MODULE** (§16) — the one matching
the document's type — and **`matrix-spec.md`**. Never load a module you are not
extracting under. All ten other modules stay out of context.

Measured at `chars / 3.6`, which is the conservative estimator for markdown with
tables and code blocks; a word-based estimate puts these ~25% lower.

| build part | budget | actual (v1) |
|---|---|---|
| CORE §1–§15 | 10,500 | 10,101 |
| one TYPE MODULE | 500 | 85–408 (M-DEED is the largest) |
| `matrix-spec.md` | 3,500 | 3,468 |
| **extraction build** | **≤ 15,000** | **~13,700–14,000** |

**The matrix spec counts.** Block 2 asks for `resolved.md` as well as
`extraction.json`, so the reader must hold both files; a budget that reports only
the framework is understating the build by a quarter. There is ~1,000 tokens of
headroom, not 4,000 — v2 has to delete before it adds.

If CORE ever exceeds its budget, a rule must be deleted, not shrunk by making
it vaguer. A vague rule costs more than a missing one: a missing rule shows up
as a gap, a vague rule shows up as agreement.

## 1 · INPUTS AND THE PAGE INVENTORY

Your inputs are exactly three things: the **document id**, **`registration.json`**,
and the **page images** `page-01.png … page-NN.png`. No other document, no prior
state of the parcel, no outside lookup, no url.

The images are scans with **no text layer**. Every character you cite you read
off an image.

**R-INP-1 · Build the page inventory first.** Before extracting anything, open
every page image in the package and assign each exactly one class:

| class | how you recognise it |
|---|---|
| `COVER` | "RECORDING AND ENDORSEMENT COVER PAGE" (NYC) or "Recording and Endorsement Cover Page" under a County Clerk seal (Richmond) |
| `COVER_CONT` | same header with "(CONTINUATION)" |
| `SUPPORT_COVER` | "SUPPORTING DOCUMENT COVER PAGE" |
| `INSTRUMENT` | the operative instrument's own text |
| `EXHIBIT` | a schedule/exhibit/rider referenced by the instrument (R-INP-4) |
| `ACK` | a notarial acknowledgment or jurat |
| `ENDORSE` | the instrument's back panel: names, title no., "record and return to" |
| `SUPPORT_FORM` | a filed form: RP-5217, transfer-tax return, affidavit of compliance |
| `ADMIN` | fee receipts, examiner stamps, routing slips, blank pages |
| `ILLEGIBLE` | the page carries text you cannot read at 900 dpi |

**R-INP-2 · The page count is not the page count.** `registration.pages` and the
cover page's "PAGE n OF m" count the *instrument only*. Supporting documents are
appended after them and are **not** included in either number. Read every image
in the package. A deed whose cover says "PAGE 1 OF 5" may have eight images, and
the sale price, the assessed value and the occupancy affidavit may all be on the
three the cover does not count.

**R-INP-3 · Cite the image, never the printed page number.** Locations are
`p01`…`pNN` — the package's own numbering. Printed numbering ("Page 14 of 17")
is per-form, restarts inside a package, and does not align with image order.
Record printed numbering only as content, never as a locator.

**R-INP-4 · Exhibit incorporation.** An `EXHIBIT` page supplies operative
content **iff** the instrument refers to it by a label that also appears on the
exhibit page (e.g. body: "SEE SCHEDULE 'A' ANNEXED HERETO"; page header:
"SCHEDULE A"). If the label does not match, class it `ADMIN` and use nothing
from it. Text on an incorporated exhibit that is not part of the referenced
content — a title insurer's solicitation, a form footer, a preparer's
advertisement — is not operative and is never quoted as instrument content.

**R-INP-5 · Struck-through and obliterated text.** Text crossed out, overtyped
with `XXXX`, or blacked out is **not operative**. Where a strike-out is replaced
by adjacent handwriting, the handwriting is operative. Where text is obliterated
and not replaced, the value it held is `UNKNOWN` with `illegible: "OBLITERATED"`
— you may not restore it from context, from the address, or from the
registration's borough.

**R-INP-6 · Illegible characters.** If a character is not certain, re-render:
`docpkg.py <id> --page N --dpi 900 --rect x0,y0,x1,y1`. If it is still not
certain, transcribe it as `[?]` in the quote and:
- **a** if another input states an unambiguous value that matches one of your
  candidate readings, adopt that reading, set `resolved_by: "CROSS_SOURCE"` and
  name both locations;
- **b** otherwise the field is `UNKNOWN`, `illegible: true`, and you record every
  candidate reading in `candidates`.
Never pick the more plausible digit. Never compute a value from a tax amount —
that needs a tax rate the document does not state (see R-NEV-9).

**R-INP-7 · Registration field citability.** `registration.json` is an input, but
its fields are not equally evidence. Citability is decided per field:

| field | citable as | never |
|---|---|---|
| `type` / `doc_type` | the register's **classification** | the document's self-description; it is normalised and abbreviated (cover "DEED, 1-2 FAMILY" → `"DEED"`; Richmond cover "ASSIGNMENT OF LEASE" → `"A/LEASE"`) |
| `doc_date` | the register's transcription of the cover's Document Date | the event date (R-DATE-*) |
| `recorded` | **the recording**, which is a real event | the event date, ever |
| `crfn`, `reel_page`, `instrument`, `book`, `page`, `map_seq` | the recording's identifiers | anything about the parcel |
| `borough` | the register's borough attribution | a substitute for an obliterated county in the body |
| `amount` | **the amount the presenter reported for this document**, meaning type-dependent (see the module) | "the price", "the loan", generically |
| `parties[].name` | the register's index entry | the party's name — index entries are truncated ("ROBERT OSINOFF CUST OF") and case-duplicated |
| `parties[].role` (Richmond) | the register's role attribution | a substitute for the body's operative verb |
| `parcels[].bbl` | the register's parcel attribution | the parcel set on its own (R-PARCEL-4) |
| `parcels[].partial`, `.unit`, `.address`, `.use` | the register's index entry | |
| `parcels[].remarks` | **nothing** — it is an index annotation, sometimes added decades later ("CORRECTED FROM R642 ON 11/14/89") | any field's evidence |
| `at`, `status`, `image_state`, `keyed_by`, `key`, `pages`, urls | **nothing** — pipeline metadata | any field's evidence |

**R-INP-8 · Cover page versus body.** The NYC cover page states: *"This page is
part of the instrument… The information on this page will control for indexing
purposes in the event of any conflict with the rest of the document."* It
controls **indexing**, and nothing else. Therefore:
- for **indexing attributes** — BBL set, unit, borough, document type, CRFN,
  recording date, fee and tax amounts printed on the cover — the cover controls;
- for **the legal act** — who conveys what to whom, on what terms, for what
  consideration, on what date — the **instrument body controls**.
When body and cover/registration state different values for the same field,
record the body's value, record the other in `conflict`, and set
`conflict: true`. Do not choose silently and do not average.

**R-INP-9 · Four package shapes.** What is present differs by id namespace.
Do not conclude a value is absent from the document because it is absent from
the registration.

| ids | cover page in images | `doc_date` in registration | `pages` | typical legibility |
|---|---|---|---|---|
| `2002…`–`2026…` (ACRIS digital) | yes, NYC format | yes | yes | good |
| `FT_…` (ACRIS film) | **no** — instrument text begins at p01, reel/page stamped in the margin | **no** | yes | poor: dark borders, speckle, skew |
| `BK_…` (bound book) | **no** | yes | yes | poor |
| `RC_…` (Richmond) | yes, County Clerk format | **no** — but the cover page image states Document Date | **no** | good |

For `FT_` and `BK_`, the only date in the registration is `recorded`. That does
not license R-DATE fallback: read the instrument for its own date first.

## 2 · CITATION

**R-CIT-1 · Every field carries its evidence.** A field is one of:

```json
{"v": <value>, "src": "BODY|COVER|REG|EXHIBIT|FORM|MARGIN",
 "q": "<verbatim ≤25 words>", "at": "p03/MIDDLE"}
{"v": <value>, "rule": "R-XXX-n", "in": ["<field path>", ...]}
```

A field with neither is a defect whether or not the value is right.

**R-CIT-2 · Quotes are verbatim.** Transcribe exactly what is printed or written,
including its own spelling and spacing. `[?]` marks an illegible character. Do
not expand abbreviations inside `q`; put the expansion in `v` with a `rule`.

**R-CIT-3 · Location vocabulary.** `at` is `p<NN>/<ZONE>` with `ZONE` from
exactly: `TOP · UPPER · MIDDLE · LOWER · BOTTOM · MARGIN_L · MARGIN_R ·
STAMP · HANDWRITTEN`. Coarse on purpose: two readers must not be able to
disagree about the locator. The quote is the precise locator.

**R-CIT-4 · Registration citations.** `src: "REG"` and `at` is the JSON key path,
e.g. `at: "reg:parcels[0].bbl"`. Fields marked "nothing" in R-INP-7 may not
appear in any `at`.

**R-CIT-5 · Derived fields.** `rule` names the rule id that produced the value;
`in` lists the field paths it consumed. A derivation whose inputs are not all
cited fields of this extraction is not a derivation — it is an inference, and it
is forbidden (§14).

## 3 · THE EVENT RECORD

```json
{
  "event_id": "<docid>-E01",
  "function": "IDENTITY|TITLE|ENTITLEMENT|ENVELOPE|ENCUMBRANCE|CAPITAL|
               PERMIT|AS_BUILT|OCCUPANCY|COST|VALUE",
  "mode": "CREATE|MODIFY|TRANSFER|TERMINATE|CORRECT|ASSERT",
  "directional": true|false,
  "event_date": {"v": "YYYY-MM-DD" | "UNKNOWN", ...evidence},
  "date_basis": "STATED_EFFECTIVE|EXECUTION|ACKNOWLEDGMENT|COVER_DOC_DATE|
                 NONE_STATED",
  "dates_observed": {"stated_effective": ..., "execution": ...,
                     "acknowledgment": ..., "cover_doc_date": ...,
                     "recorded": ...},
  "date_bound_latest": {"v": "YYYY-MM-DD", ...evidence},
  "parties": [{"name": {...}, "role": "<controlled>", "side": "FROM|TO|NONE",
               "share": {"v": "<fraction|percent>|UNKNOWN"},
               "capacity": {"v": "<verbatim, e.g. HIS WIFE, AS TRUSTEE>"}}],
  "parcels": [{"bbl": {...}, "parcel_role": "<controlled>",
               "extent": "ENTIRE_LOT|PARTIAL_LOT|UNIT|UNSTATED"}],
  "quantity": {"v": "USD <n.nn>" | "UNKNOWN" | "ALLOCATION_NOT_DERIVABLE",
               "kind": "<controlled>", "group": "<group id|null>", ...evidence},
  "terms": { ... per §11 and the type module ... },
  "payload": { ... per the function's cell schema, §4 ... },
  "references": [{"instrument": ..., "dated": ..., "recorded": ...,
                  "locator": ..., "amount": ..., "parties": ...}],
  "clause": {"q": "<the operative clause, ≤25 words>", "at": "p03/MIDDLE"},
  "flags": [{"field": "<path>", "kind": "AMBIGUOUS",
             "readings": [{"v": ..., "q": ..., "at": ...}, ...]}]
}
```

Absent keys mean "this function's schema has no such slot". A slot the schema
has but the document does not fill is `UNKNOWN`, never omitted.

## 4 · THE ELEVEN FUNCTIONS

Each function answers exactly one question about a parcel and holds exactly one
kind of cell. **The cell schema is what makes the boundary decidable** — you do
not ask "is this an Encumbrance or an Envelope", you ask "does this clause state
a value that goes in Encumbrance's cell? does it state one that goes in
Envelope's cell?" and both answers can be yes.

| # | function | its one question | cell holds |
|---|---|---|---|
| 1 | `IDENTITY` | *Which parcel is this, and does it exist as a distinct legal object?* | designation set (bbl, borough/block/lot, unit), existence status `EXISTS·CREATED·MERGED·APPORTIONED·RENUMBERED·SUPERSEDED`, stated former/new designations |
| 2 | `TITLE` | *Who holds an ownership interest, and which?* | holders with interest kind `FEE·LEASEHOLD·LIFE_ESTATE·REMAINDER·UNDIVIDED_SHARE·EQUITY_OF_REDEMPTION`, share, and the conveyance's covenant kind |
| 3 | `ENTITLEMENT` | *What is this parcel legally permitted to be or become?* | zoning district, permit/variance/authorisation/application identifiers, granting authority, use permissions, stated conditions of approval |
| 4 | `ENVELOPE` | *How much, and in what shape, may be built?* | floor area, FAR, height, stories, dwelling-unit count, development rights transferred/received/reserved, **and stated dimensional limits on building position** (setback, clear distance, lot coverage) |
| 5 | `ENCUMBRANCE` | *What non-ownership claim burdens this parcel?* | burden kind `MORTGAGE·LIEN·EASEMENT·COVENANT·LEASE·OPTION·ROFR·LIS_PENDENS·UCC_FIXTURE·ASSIGNMENT_OF_RENTS`, holder, status `OPEN·SATISFIED·RELEASED·ASSIGNED·SUBORDINATED·CONSOLIDATED·MODIFIED`, priority statements, scope |
| 6 | `CAPITAL` | *What monetary obligation runs against this parcel, on what terms?* | obligation kind, principal, rate, maturity, amortisation, advance schedule, prepayment, guaranty, cross-collateralisation, obligor and obligee |
| 7 | `PERMIT` | *What work has been authorised or applied for?* | application/permit/job identifiers, issuing body, scope of work, status |
| 8 | `AS_BUILT` | *What physically exists?* | stories, gross floor area, unit count built, structures, completion statements, installed equipment |
| 9 | `OCCUPANCY` | *Who or what may lawfully occupy it?* | use class as stated, dwelling/rooming unit count, certificate identifiers, occupancy in possession, compliance affidavits |
| 10 | `COST` | *What was paid, charged or is owed in connection with this act?* | named money register: consideration, sale price, taxes, fees, stated construction cost, stated payoff |
| 11 | `VALUE` | *What is this parcel asserted to be worth, apart from what was paid?* | assessed value, appraised value, stated fair market value, insured value |

**R-FN-1 · The function test.** For each operative clause (§6), test all eleven
cell schemas. Emit one event for **each** function whose cell the clause fills
with a value the clause states, or that a framework rule derives from what the
clause states. Fill with nothing → no event for that function. An event carries
exactly one function; never two.

**R-FN-2 · Identity does not fire on routine recitals.** Every instrument
describes its premises, and describing is not an Identity event. `IDENTITY`
fires only when the document states one of:
- **a** the parcel is created, merged, divided, renumbered, or declared into units;
- **b** a designation for the premises that differs from the registration's BBL set;
- **c** an express former/new designation ("formerly Lot 30, now Lots 1001–1128");
- **d** that the premises is part of, not all of, an indexed lot.
Otherwise the legal description is carried as `parcels[].description_kind`
(`METES_AND_BOUNDS·LOT_REFERENCE·MAP_REFERENCE·UNIT_REFERENCE·ADDRESS_ONLY·NONE`)
on the other events, and `IDENTITY` is `NO_CHANGE`.

**R-FN-3 · Encumbrance and Capital both fire on a secured obligation.** A clause
whose subject is a debt or other monetary obligation secured by, or payable in
respect of, the parcel writes to **both**: `ENCUMBRANCE` takes the security
interest (kind, holder, status, priority), `CAPITAL` takes the obligation
(principal, rate, maturity, terms). Same mode, same date, same parcels, two
events. If the document states no terms, the `CAPITAL` event still fires with
every term `UNKNOWN` — otherwise the debt column silently loses the origination,
the assignment or the payoff, and a column that never closes is worse than a
column that is empty.

**R-FN-4 · Party facts are not Identity.** The eleven functions describe the
*parcel*. A recital about a party — "F/K/A The Chase Manhattan Bank", "a New
York corporation", a merger of the lender — is recorded on the party
(`parties[].capacity`, `parties[].also_known_as`), never as an `IDENTITY` event.

**R-FN-5 · Settled boundary calls.** These bind; do not re-derive them.

| the thing | fires | does not fire | why |
|---|---|---|---|
| restrictive declaration stating a bulk limit and running with the land | `ENVELOPE` + `ENCUMBRANCE` | | it fills both cells |
| restrictive declaration with no stated dimension or quantity (e.g. a façade preservation easement) | `ENCUMBRANCE` | `ENVELOPE` | Envelope's cell takes quantities and dimensions; none are stated |
| declaration made to obtain an agency approval, naming the application | `+ ENTITLEMENT` `+ PERMIT` | | permit/application identifier and the permission sought are both stated |
| zoning-lot development agreement transferring floor area | `ENVELOPE` + `ENCUMBRANCE` | `TITLE` | development rights are not an ownership interest in the parcel |
| mortgage, building loan, assignment of rents | `ENCUMBRANCE` + `CAPITAL` | | R-FN-3 |
| lease or memorandum of lease | `ENCUMBRANCE` (+`CAPITAL` if rent is stated) | `TITLE` | a leasehold burdens the fee; the lessee's estate is `TITLE` **only on the leasehold's own BBL** if one is indexed |
| deed reciting consideration | `TITLE` + `COST` | `VALUE` | money paid is Cost; Value is worth asserted apart from payment |
| assessed value on a filed RP-5217 | `VALUE` | `COST` | asserted worth, not a payment |
| covenant against grantor's acts | `ENCUMBRANCE` (`ASSERT`) | | it asserts about the burden register, within a scope (R-NULL-3) |
| power of attorney, affidavit of authority, corporate resolution | *nothing* | all eleven | authority is not among the eleven functions; emit zero events and set `no_events_reason` |

## 5 · MODE

**R-MODE-1 · Ordered test, first match wins.** For each clause–function pair:

1. The clause states that an earlier recorded statement of **this same act** was
   erroneous and replaces it → `CORRECT`
2. The clause ends, releases, discharges, satisfies, vacates, revokes or
   terminates an identified existing thing → `TERMINATE`
3. The clause moves an identified existing thing from a named holder to a
   different named holder, the thing's own terms unchanged → `TRANSFER`
4. The clause changes a stated attribute of an identified existing thing, the
   thing and its holder persisting → `MODIFY`
5. The clause brings into existence a thing not previously existing, or grants a
   right not previously held → `CREATE`
6. The clause states a fact about the parcel or about an existing thing, without
   changing it → `ASSERT`
7. None of the above → the clause is not operative; emit nothing.

**R-MODE-2 · Notice instruments assert.** A memorandum, notice, or affidavit
whose purpose is to put an interest made elsewhere on the record is `ASSERT`,
not `CREATE`. This document did not create that interest.

**R-MODE-3 · Partial termination.** A release of part of the burdened property,
or of part of the debt, is `MODIFY` with `payload.released_scope` quoted, not
`TERMINATE`. `TERMINATE` requires the thing to end entirely.

## 6 · SPLITTING ONE INSTRUMENT INTO SEVERAL EVENTS

**R-SPLIT-1 · Operative clause.** A sentence, numbered paragraph, or lettered
subparagraph containing at least one operative verb: *grants · conveys ·
releases · quitclaims · mortgages · assigns · declares · covenants · restricts ·
reserves · subordinates · extends · modifies · consolidates · satisfies ·
discharges · terminates · certifies · gives notice · leases · demises ·
transfers · warrants · deposes*.

**R-SPLIT-2 · Not operative — never emit for these.** Recitals of authority and
capacity; habendum ("TO HAVE AND TO HOLD"); appurtenance recitals ("TOGETHER
with… streets and roads to the center lines"); Lien Law §13 trust-fund covenant;
statutory characterisations of the instrument itself ("not subject to §275 of
the Real Property Law"); notice-address, governing-law, severability,
counterparts, further-assurances, definitions sections, headings; form
identifiers; a rider checkbox list; the acknowledgment's own recital of
appearance.

**R-SPLIT-3 · Definitions sections are read, not emitted.** A "WORDS USED OFTEN
IN THIS DOCUMENT" or "Definitions" section is where the principal, the maturity
and the parties are stated. Take values from it; emit no event for it.

**R-SPLIT-4 · Merge.** After emitting, merge any two events sharing identical
`function`, `mode`, `parcel` set, `party` set and `event_date` whose payloads do
not state conflicting values for the same key. Union the payloads and keep both
`clause` quotes. This is what keeps a fifteen-paragraph mortgage from producing
fifteen events.

**R-SPLIT-5 · Riders and attached schedules are part of the instrument** when
R-INP-4 is satisfied. Their operative clauses are segmented and tested exactly
like the body's.

**R-SPLIT-6 · One quantity, several events, is normal.** Splitting a clause into
several events never splits its stated amount. See R-QTY-3.

## 7 · DATES

**R-DATE-1 · Record every date you see, then resolve one.** Populate
`dates_observed` with all of: stated effective date, execution date,
acknowledgment date, cover Document Date, recording date. Then set `event_date`
and `date_basis` by first available:

| order | basis | what qualifies |
|---|---|---|
| 1 | `STATED_EFFECTIVE` | a date the clause attaches to **the act the clause performs**, using effectiveness language: "effective as of", "as of", "takes effect on", "made this … day of" when the making *is* the act |
| 2 | `EXECUTION` | "Dated:", "IN WITNESS WHEREOF … this __ day of __", a signature date |
| 3 | `ACKNOWLEDGMENT` | the notarial jurat's date |
| 4 | `COVER_DOC_DATE` | the cover page's "Document Date" (or `registration.doc_date`) |
| 5 | `NONE_STATED` | nothing above exists |

**R-DATE-2 · A date attached to a consequence is a term, not the event date.**
Term commencement, maturity, first payment, a future closing, an option
expiry, a condition deadline — these go in `terms`. Only the date of the act
itself can be the event date. A lease executed 2019-03-04 for a term commencing
2019-07-01 is an event on 2019-03-04 with `terms.commencement = 2019-07-01`.

**R-DATE-3 · The recording date is never the event date.** Not as a fallback,
not "for convenience", not when everything else is missing. When
`date_basis` is `NONE_STATED`, `event_date.v` is `"UNKNOWN"` and
`date_bound_latest` is set to the recording date — the document existed by then,
which is all the recording proves.

**R-DATE-4 · Retroactive effective dates are honoured.** An instrument executed
2020-03-05 "effective as of January 1, 2018" is an event on 2018-01-01,
`date_basis: STATED_EFFECTIVE`. `dates_observed` still carries the execution
date, so the choice is visible and arguable.

**R-DATE-5 · Different events in one document may have different dates.** Resolve
per event, from that event's own clause, before falling through to
document-level dates.

**R-DATE-6 · Format.** `YYYY-MM-DD`. A date stated only as a month and year is
`YYYY-MM` and `date_precision: "MONTH"`; only a year is `YYYY`,
`date_precision: "YEAR"`. Never pad a missing day to `01`.

## 8 · PARTIES, ROLES, DIRECTION, SHARES

**R-PARTY-1 · Never derive a role from panel or column order.** Cover-page
"party 1 / party 2" and "party of the first part / second part" do not mean
grantor/grantee, borrower/lender, or actor/subject. On a satisfaction of
mortgage the executing lender is panel 2. On a consolidation agreement the party
of the first part is the *holder of the mortgages*, not the owner. Derive the
role from, in order: (a) the printed role label on the cover page
("GRANTOR/SELLER", "MORTGAGER/BORROWER", "ASSIGNOR INDEX"); (b) the Richmond
registration's `parties[].role`; (c) the body's operative verb — who does the
granting, who receives. Record `role_basis` as `COVER_LABEL`, `REG_ROLE`, or
`BODY_VERB`.

**R-PARTY-2 · Controlled roles.** `GRANTOR · GRANTEE · MORTGAGOR · MORTGAGEE ·
ASSIGNOR · ASSIGNEE · LESSOR · LESSEE · DECLARANT · BENEFICIARY · TRUSTEE ·
GUARANTOR · RELEASOR · RELEASEE · SUBORDINATING_PARTY · BENEFITED_PARTY ·
BURDENED_PARTY · AFFIANT · AUTHORITY · OTHER`. `OTHER` requires
`role_verbatim` quoting the label the document used.

**R-PARTY-3 · Direction.** `directional: true` iff the clause names a side that
parts with, or is burdened by, the thing **and** a side that receives or holds
it. Set `side` to `FROM` / `TO` accordingly. A declaration by a sole owner
binding the land, an affidavit, and an agency certification are
`directional: false`, all parties `side: NONE`.

**R-PARTY-4 · Names come from the body.** Use the name as the operative clause
prints it, uppercased, internal whitespace collapsed. The registration's index
entries are truncated and duplicated (Richmond repeats each party once
upper-case and once title-case; that is one party, not two). Deduplicate the
registration list case-insensitively before comparing.

**R-PARTY-5 · Coverage check.** Compare your party set against the deduplicated
registration party set. Record `party_coverage` as `MATCH`, `BODY_EXTRA`,
`REG_EXTRA` or `DIVERGENT`. A divergence is recorded, not resolved by preferring
one list.

**R-PARTY-6 · Shares are never inferred.** If shares are stated, record them as
stated. If two or more parties are on a side and no share is stated, every
`share` is `UNKNOWN` and the event carries
`share_allocation: "NOT_STATED"`. Equal shares are never assumed.

**R-PARTY-7 · Relationship and capacity words are quoted, not construed.**
"HIS WIFE", "AS TENANTS IN COMMON", "AS TRUSTEE", "CUST OF", "A NEW YORK
CORPORATION" go verbatim into `capacity`. Do not convert a relationship into a
tenancy, a share, or a survivorship right.

**R-PARTY-8 · One name in two capacities is two party entries.** *"JEROME
OSINOFF, individually and as custodian for ROBERT OSINOFF … under the New York
Uniform Gifts To Minors Act"* is two entries with the same `name` and different
`capacity`. A beneficiary named only inside another party's capacity phrase is
**not** a party: record them in `capacity` and nowhere else. The register's
index does the opposite — it lists the minor as the party and appends "CUST OF"
— which is one more reason R-PARTY-4 takes names from the body.

## 9 · PARCELS AND BBL ATTRIBUTION

**R-PARCEL-1 · BBL grammar.** A BBL is 10 digits: 1 borough + 5 block + 4 lot,
zero-padded. `1011321063` = borough 1, block 1132, lot 1063. Borough digits:
`1 MANHATTAN · 2 BRONX · 3 BROOKLYN · 4 QUEENS · 5 STATEN ISLAND`. Kings =
Brooklyn, New York = Manhattan, Richmond = Staten Island. This table is the
framework's; using it is a derivation (`rule: "R-PARCEL-1"`), not knowledge.

**R-PARCEL-2 · Parcel roles.** `SUBJECT · GRANTING · RECEIVING · BURDENED ·
BENEFITED · ADJOINING · REFERENCED`. Default `SUBJECT`. `GRANTING` / `RECEIVING`
are required whenever the clause moves a right between parcels (development
rights, easements): the two are not interchangeable and must not be recorded
symmetrically.

**R-PARCEL-3 · Extent.** `ENTIRE_LOT · PARTIAL_LOT · UNIT · UNSTATED`, from the
cover's `partial` field and the body. `PARTIAL_LOT` also fires R-FN-2(d).

**R-PARCEL-4 · The parcel set is the union of both sources.** Neither source is
complete: ACRIS covers list every indexed lot while the body may name one;
Richmond covers print one lot plus *"And Addl Blocks and/or Lots"* while the
registration lists all of them. Take the union, and set `bbl_source` per parcel
to `REG`, `COVER`, `BODY`, or `REG+BODY`.

**R-PARCEL-5 · Fan only to parcels the clause affects.** An event's parcel set
is the subset of the document's parcels that its own clause operates on. When
the clause does not distinguish, the set is every parcel in the union. A parcel
named only as a neighbour or a reference gets `parcel_role: ADJOINING` or
`REFERENCED` and is not fanned to by unrelated events.

**R-PARCEL-6 · Zero parcels is a real answer.** If the document identifies no
parcel, events still record with `parcels: []` and the matrix is empty with
`matrix_empty_reason: "NO_PARCEL_IDENTIFIED"`. Do not attach the event to a
parcel because one seems implied.

**R-PARCEL-7 · Never derive a BBL.** Not from an address, not from a metes and
bounds, not from a street name. A body that states "Block 6352 Lot 6" without a
borough is combined with the register's borough under R-PARCEL-1 and recorded as
a derivation.

## 10 · QUANTITIES AND ALLOCATION

**R-QTY-1 · Format.** `USD <digits>.<2 digits>`, no separators: `USD 384900.00`.
Non-money quantities carry a unit: `SF 12500`, `FT 60`, `FAR 10.00`, `UNITS 128`,
`PCT 51.00`.

**R-QTY-2 · Kinds.** `PRINCIPAL · REDUCED_BALANCE · CONSIDERATION_RECITED ·
SALE_PRICE · PAYOFF · TAX · FEE · RENT · ASSESSED_VALUE · APPRAISED_VALUE ·
FLOOR_AREA · DEVELOPMENT_RIGHTS · CONSTRUCTION_COST · OTHER`. Several quantities
of different kinds may attach to one event; the money register in a `COST` cell
is a list, not a number.

**R-QTY-3 · One amount over several events or parcels is never divided.** When a
single stated amount covers more than one event, parcel, or obligation, create a
quantity group: `{"group_id": "<docid>-Q1", "total": "USD 1900000.00",
"covers": ["<event ids>"], "parcels": ["<bbls>"]}`. Each covered event's own
`quantity.v` is `"ALLOCATION_NOT_DERIVABLE"` and carries `group`. Never allocate
by lot area, lot count, assessed value, frontage, or any other proportion — not
even when the arithmetic is easy and the answer looks obvious.

**R-QTY-4 · When the document states the allocation, use it** and set
`allocation_basis` with the quote.

**R-QTY-5 · Arithmetic on stated numbers is allowed and must be shown.** Summing
two stated principals into a stated consolidated total is a derivation:
`rule: "R-QTY-5"`, `in` listing both inputs. If the document also states the
total and it disagrees with your sum, record both and set `conflict: true`.

**R-QTY-6 · A recited amount belongs to the referenced instrument.** The
principal of a mortgage described by a satisfaction or an assignment is a
`references[].amount`, not this event's `quantity`. This event's quantity is
what *this act* moves, charges or secures — often nothing, which is `UNKNOWN`
if the act has an amount the document does not state, and absent if the act has
no amount at all.

## 11 · TERMS

**R-TERM-1 · Terms are the first thing to be dropped, so they are a required
slot.** Every `CAPITAL` and every `ENCUMBRANCE` event carries the terms block,
with each slot present and `UNKNOWN` when unstated:

```
principal · rate · rate_type · maturity · commencement · duration ·
amortisation · payment_frequency · prepayment · advance_schedule ·
guaranty · cross_collateral · conditions · options · default_remedies
```

Other functions carry `conditions` and `options` when stated. The type module
lists the extra slots for its type.

**R-TERM-2 · Silence about a term is `UNKNOWN`, and silence is common.** A NY
uniform mortgage states the principal and the maturity but **not the interest
rate** — the rate lives in the note, which is not recorded. `rate: UNKNOWN` is
the correct, complete answer, and it is not a flag (§13).

**R-TERM-3 · The absence of an attachment is not a statement about terms.** An
unchecked "Adjustable Rate Rider" box states that no such rider is attached
(`riders_attached` is `ASSERTED_NONE` for that rider). It does not state that
the loan is fixed-rate. `rate_type: UNKNOWN`.

**R-TERM-4 · Conditions and options are quoted, not summarised.** Record the
trigger and the consequence in the document's own words, ≤25 words each.

## 12 · THE FOUR NULLS

**R-NULL-1 · Decision procedure, in order.** For a (parcel, function, moment):

1. Does any operative clause in this document write to this cell? **No →
   `NO_CHANGE`.**
2. Does the document affirmatively state that the thing does not exist? **Yes →
   `ASSERTED_NONE`.**
3. Does the document state a condition under which this function can have no
   value at all? **Yes → `NOT_APPLICABLE`.**
4. Otherwise → **`UNKNOWN`**: a clause writes here, and the value is not stated.

**R-NULL-2 · A blank form field is `UNKNOWN`, not `ASSERTED_NONE`.** "List of
Assignments:" left empty says nothing. "prior assignments:" left empty says
nothing. `ASSERTED_NONE` needs affirmative words — *"which Mortgage HAS NOT been
assigned of record"*.

**R-NULL-3 · `ASSERTED_NONE` carries its scope, verbatim.** A covenant against
grantor's acts asserts nothing about encumbrances the grantor did not create,
and *"except as aforesaid"* narrows it further. Record
`asserted_none_scope: {"q": ..., "at": ...}`. An unscoped `ASSERTED_NONE` from a
scoped covenant is a serious error: it reads as "free and clear".

**R-NULL-4 · `NOT_APPLICABLE` is narrow.** It requires a stated condition, not an
absence and not your judgement. If you reach for it and cannot quote the
condition, the answer is `UNKNOWN` or `NO_CHANGE`.

## 13 · AMBIGUITY AND THE FLAGGING DISCIPLINE

**R-AMB-1 · Flag the document, never the rule.** A flag says *this document
admits two readings*. It never says *this framework did not tell me what to do*.
Where the framework is silent you still emit your answer and record the gap in
`notes.md` — the framework is fixed in Block 3, not by a flag.

**R-AMB-2 · Admission test — a field may be flagged `AMBIGUOUS` only if you can
supply two or more readings, each with its own quote and location**, and at
least one of:
- **a** two locations in the inputs state different values for the same field; or
- **b** one location's characters admit more than one reading after a 900 dpi
  re-render (R-INP-6).
If you cannot produce the readings with quotes, you may not flag. Emit your
value.

**R-AMB-3 · These are not flags.** A term the document does not state
(`UNKNOWN`); a rule you found hard to apply; a value you believe is
commercially odd; a discrepancy that does not change any cell (log it in
`notes.md`); anything you would resolve by knowing New York.

**R-AMB-4 · Count and report.** Every extraction reports
`emitted` (fields with a value), `flagged` (fields carrying an `AMBIGUOUS`
flag), and `ratio = flagged / emitted`. A framework that buys agreement by
flagging shows up here before it shows up anywhere else.

## 14 · WHAT MAY NEVER BE INFERRED

These are absolute. Producing any of them from knowledge rather than from a
cited field is a defect even when the value is right.

- **R-NEV-1** Equal or pro-rata shares among co-parties when none is stated.
- **R-NEV-2** Any allocation of a lumped amount (R-QTY-3).
- **R-NEV-3** The recording date as an event date (R-DATE-3).
- **R-NEV-4** A party's role from panel, column, or paragraph order (R-PARTY-1).
- **R-NEV-5** A BBL from an address, a street name, or a metes and bounds.
- **R-NEV-6** A tenancy, survivorship right, or share from a relationship word.
- **R-NEV-7** Whether a lien is still open, a permit still valid, a lease still
  running. This document is read alone.
- **R-NEV-8** Any zoning district, FAR, height limit, use group, assessed value
  or market value not stated in the inputs.
- **R-NEV-9** A consideration, principal or value computed from a tax or fee
  amount. That requires a rate the document does not state.
- **R-NEV-10** An obliterated, illegible or blank value restored from context
  (R-INP-5, R-NULL-2).
- **R-NEV-11** The expansion of an abbreviation the document does not expand,
  except from the glossary in R-NEV-12.
- **R-NEV-12** *Permitted glossary, and nothing beyond it:* `MORTGAGER =
  mortgagor`, `F/K/A = formerly known as`, `A/K/A = also known as`, `N/K/A = now
  known as`, `CUST OF = custodian of`, `SS: = scilicet (venue marker)`,
  `LIBER/REEL = recording volume`, `CRFN = City Register File Number`,
  `BBL = borough-block-lot`, `RPTT = NYC Real Property Transfer Tax`,
  `RETT = NYS Real Estate Transfer Tax`, `C of O = certificate of occupancy`,
  `BSA = Board of Standards and Appeals`, `CPC = City Planning Commission`,
  `DOB = Department of Buildings`, `UCC = Uniform Commercial Code`,
  `CEMA = consolidation, extension and modification agreement`.

**R-NEV-13 · Following the framework where you think it is wrong is mandatory.**
Emit what the rules produce, then record the objection in `objections.md`.
Silently correcting the framework hides the defect the loop exists to find.

## 15 · OUTPUT

`extraction.json`:

```json
{"document_id": ..., "framework_version": "v1",
 "page_inventory": [{"page": "p01", "class": "COVER"}, ...],
 "package_shape": "ACRIS_DIGITAL|ACRIS_FILM|BOOK|RICHMOND",
 "events": [ ... ],
 "quantity_groups": [ ... ],
 "no_events_reason": null,
 "counts": {"emitted": n, "flagged": n, "ratio": 0.00,
            "events": n, "parcels": n}}
```

`resolved.md`: that table pushed through `matrix-spec.md`.

---

# 16 · TYPE MODULES — load exactly one

Choose by `registration.type` / `doc_type`, then confirm against the
instrument's own title. **If the two disagree, the instrument's own title
chooses the module**, and the disagreement is recorded. If no module matches,
load `M-GENERIC`.

### M-DEED — `DEED`, `DEED, OTHER`, `DEED, 1-2 FAMILY`
Registration `amount` = the consideration the presenter reported.
Events, in the order they usually appear: `TITLE.TRANSFER` (grantor→grantee,
interest `FEE` unless the granting clause says otherwise, `covenant_kind` from
the form title: `BARGAIN_SALE · BARGAIN_SALE_WITH_COVENANT · QUITCLAIM ·
WARRANTY · EXECUTOR · REFEREE · CORRECTION`); `COST.ASSERT` holding the money
register; `ENCUMBRANCE.ASSERT` for any covenant against encumbrances (scope per
R-NULL-3).
**Consideration.** Record every figure separately:
`CONSIDERATION_RECITED` (body), `SALE_PRICE` (RP-5217 field 12),
`TAX` entries (RPTT, RETT, filing fee), `FEE` (recording fee). Then set
`consideration_resolved` by: **(a)** RP-5217 `SALE_PRICE` if present;
**(b)** else the body's recited amount if it exceeds `USD 10.00`;
**(c)** else `registration.amount` if greater than zero, `rule: "M-DEED-C"`;
**(d)** else `UNKNOWN`. A recited `TEN & 00/100 ($10.00)` is nominal and never
resolves the consideration by itself.
**Supporting forms carry the rest of the document's content.** RP-5217 →
`VALUE.ASSERT` (field 16 total assessed value), `OCCUPANCY.ASSERT` (field 9 use
at time of sale, field 15 building class), `COST` (field 12, 13), and field 11
"Date of Sale/Transfer" is a `STATED_EFFECTIVE` candidate for the
`TITLE.TRANSFER`. Smoke-detector affidavit → `OCCUPANCY.ASSERT` (one- or
two-family dwelling) + `AS_BUILT.ASSERT` (device installed).

### M-MORTGAGE — `MORTGAGE`, `BUILDING LOAN`, `ASSIGNMENT OF LEASES AND RENTS`
Registration `amount` = the principal.
`ENCUMBRANCE.CREATE` (kind `MORTGAGE`, holder = lender) **and**
`CAPITAL.CREATE` (R-FN-3). Terms live in the definitions section: principal and
maturity are stated; **the rate usually is not** (R-TERM-2). Riders listed with
a checked box are part of the instrument; a 1-4 Family Rider containing an
assignment of rents adds `ENCUMBRANCE.CREATE` kind `ASSIGNMENT_OF_RENTS`.
Building loan: `advance_schedule` from the schedule of advances; the total
advance commitment is the `PRINCIPAL`, and per-advance amounts are terms.

### M-SATISFACTION — `SATISFACTION OF MORTGAGE`, `RELEASE`, `UCC3 TERMINATION`
Registration `amount` is normally `$0.00` and means nothing.
`ENCUMBRANCE.TERMINATE` + `CAPITAL.TERMINATE`. The referenced mortgage's date,
recording locator and principal go in `references`, never in `quantity`
(R-QTY-6). The payoff amount is almost never stated → `quantity: UNKNOWN`.
A statement that the mortgage "HAS NOT been assigned of record" is
`ASSERTED_NONE` on the assignment history (R-NULL-2). A release of *part* of the
premises is `MODIFY` (R-MODE-3) and the released parcels take
`parcel_role: SUBJECT` with `extent: PARTIAL_LOT`.

### M-ASSIGNMENT — `ASSIGNMENT, MORTGAGE`, `ASSIGNMENT OF LEASE`, `A/LEASE`
`ENCUMBRANCE.TRANSFER` + `CAPITAL.TRANSFER`, assignor→assignee.
The assigned instrument's terms are `references`, not this event's terms — this
act changes the holder and nothing else, so every term slot is `UNKNOWN` unless
the assignment itself restates it. `prior assignments:` left blank is `UNKNOWN`
(R-NULL-2). Expect handwritten fill-ins for book, page, date and lot, and
expect the county to be struck out or blacked out (R-INP-5).
A consideration recital — *"in consideration of TEN ($10.00) DOLLARS and other
good and valuable consideration paid by …"* — adds `COST.ASSERT` with
`kind: CONSIDERATION_RECITED`; it does not resolve a price (M-DEED's resolution
rule is for deeds only). Assignments frequently carry many assignees on one
side with no shares stated: R-PARTY-6 and R-PARTY-8 both apply.

### M-AGREEMENT — `AGREEMENT`, `SUNDRY AGREEMENT`, `MISCELLANEOUS`
The type says nothing; read the instrument's own title. The commonest is a
**consolidation, extension and modification agreement** (NYBTU Form 8026):
- one `ENCUMBRANCE.MODIFY` + `CAPITAL.MODIFY` per recited mortgage whose stated
  attributes this agreement changes (a stated reduced principal balance is a
  `MODIFY` with `quantity.kind: REDUCED_BALANCE`);
- one `ENCUMBRANCE.MODIFY` + `CAPITAL.MODIFY` for the consolidation itself,
  quantity = the consolidated principal (state it if stated; else derive by
  R-QTY-5 from the stated components and show the inputs);
- mortgages recited as recorded elsewhere or "contemporaneously herewith" are
  `references`, **not** events — this document did not create them;
- marginal handwritten "MTGE TAX PAID $n" annotations are `COST.ASSERT`,
  `src: MARGIN`, with `author: UNKNOWN`;
- the consolidated lien over several parcels is one quantity group (R-QTY-3).

### M-DECLARATION — `DECLARATION`, `EASEMENT`, `CERTIFICATE`
`ENCUMBRANCE.CREATE` for the burden (kind `COVENANT` or `EASEMENT`), with
`runs_with_land` set from an express clause and `UNKNOWN` otherwise.
Add `ENVELOPE.CREATE` only if a quantity or dimension is stated (R-FN-5).
Add `ENTITLEMENT` and `PERMIT` when an application, permit, variance or agency
is named — record the identifier verbatim (`Alteration Application #601/80`) and
the granting body. A condominium declaration is additionally
`IDENTITY.CREATE` per unit lot, `existence_status: CREATED`, with the former lot
recorded as `superseded_designation`; the unit lots are the parcel set and the
former lot takes `parcel_role: SUBJECT`, `existence_status: SUPERSEDED`.
Reserved rights ("Grantor reserves the right to…") are `terms.options`.

### M-LEASE — `LEASE`, `MEMORANDUM OF LEASE`, `CONTRACT OF SALE`
A lease or memorandum is `ENCUMBRANCE.CREATE` kind `LEASE` on the fee parcel
(`ASSERT` if the page is a memorandum of a lease made elsewhere, R-MODE-2), plus
`CAPITAL.CREATE` if rent is stated. `commencement`, `duration`, `renewal
options`, `purchase options` are terms, never the event date (R-DATE-2). A
contract of sale is `ENCUMBRANCE.CREATE` kind `OPTION` — it is not a `TITLE`
event, because title has not moved.

### M-UCC — `INITIAL UCC1`, `INITIAL COOP UCC1`, `UCC3 TERMINATION`
`ENCUMBRANCE.CREATE` (or `TERMINATE`) kind `UCC_FIXTURE`, debtor→secured party.
Collateral description is `payload.scope`, quoted. A coop UCC secures shares,
not real property: still `ENCUMBRANCE` on the indexed BBL, with
`payload.collateral_kind: "COOPERATIVE_SHARES"` quoted from the form.

### M-AUTHORITY — `POWER OF ATTORNEY`, and affidavits of authority
Emit **zero events** (R-FN-5). Set
`no_events_reason: "AUTHORITY_ONLY — no clause writes to any of the eleven
functions"`. This is a complete extraction, not a failure. Record the principal
and the attorney-in-fact in `no_events_parties` so the round can check the call.

### M-GENERIC — anything else, including `(none)` and `VACATE ORDER`
Read the instrument's own title, segment its clauses under R-SPLIT-1, and apply
R-FN-1 with no type-specific expectations. Record
`module: "M-GENERIC"` and the instrument's title verbatim, so Block 3 can decide
whether a module is owed.
