<!-- BUILD:CORE §0 COMMON -->
# NYC C.R.E.D. extraction framework v2

This rulebook turns one supplied recorded-instrument package into a provenance-closed event table. Rule ids are immutable: a later version may amend or retire a rule, but never reuse its id for a different decision.

**Blocks are ordered by which pass reads them, not by subject.** §0+§1 is the shared prefix every semantic pass loads and must be byte-identical across all eleven lens prompts. §2 is the per-lens suffix. §3 is the support pass. §4 is enrichment. §5 is assembly. §6 is adapters, read only at registration. §7 names the version gate. A rule placed by topic rather than by reader defeats the partition and is a defect.

**FR-SCOPE-001 — Inputs.** The only semantic inputs are the supplied document id, raw `registration.json`, and every supplied page image. Read the document independently. Do not use another instrument, parcel history, website, map, law lookup, slate field, local path, URL, filename, or pipeline timestamp to supply a value.

**FR-SCOPE-002 — Knowledge boundary.** Domain knowledge may decode words visible in an allowed input. It may not add a party, role, amount, semantic kind, date, parcel, priority, duration, legal effect, relationship, or status not supported by a quote or an admitted derivation.

**FR-SCOPE-003 — Provenance closure.** Every emitted scalar, sentinel, classification, link, and normalized value terminates in either `QUOTE` support or one stable rule id in the loaded bundle with all input paths named. A correct value with neither is a defect. A rule outside the loaded bundle is not an allowed derivation.

**FR-ID-001 — Identifier grammar.** All ids are `<document_id>-<prefix><ordinal>`: `E` evidence, `A` anchor, `S` section, `P` party, `R` party relationship, `Q` quantity, `X` external reference, `T` evidence time, `B` boundary, `O` ordering, `G` event group, `EV` event. Ordinals are zero-padded to three digits and assigned only by the rule that owns the registry. Percent-escape `%` and `:` inside any identity component; never slug, transliterate, or append a contextual suffix to make an id unique.

**FR-NULL-001 — UNKNOWN.** Use when an applicable required field has no supported single value. Reason is `NOT_STATED`, `ILLEGIBLE`, `CONFLICT`, `UNALLOCATABLE`, `UNSUPPORTED_BBL`, `UNSUPPORTED_DATE`, `VALID_TIME_PRESENT_BUT_UNNORMALIZABLE`, `INCORPORATED_SECTION_NOT_SUPPLIED`, or `NOT_CHECKABLE`. It is field-local unless a placement key is affected.

**FR-NULL-002 — NOT_APPLICABLE.** Use only when a module's conditional schema asks a field and supported inputs prove that branch structurally cannot apply. Omitted out-of-schema paths are absent, not NOT_APPLICABLE.

**FR-NULL-003 — ASSERTED_NONE.** Use only for express scoped negation and cite it. When the negation is parcel state content, FR-PKG-003 requires an observation event. **A search that found nothing never produces ASSERTED_NONE.**

**FR-NULL-004 — NO_CHANGE.** Use only as an express MODIFY/CORRECT field operation preserving a named path or all other terms. It carries a known earlier value only within this document's fold; unseen prior state remains UNKNOWN. It is never a blank matrix cell.

**FR-NULL-005 — Absent versus null.** An unstated optional attribute is **absent from the output**, not an UNKNOWN object. Emit UNKNOWN only where a rule or module `required_when` test makes the field applicable. A registry of UNKNOWN objects for every attribute the document might have stated is a defect.

**FR-SER-001 — Canonical JSON.** UTF-8 without BOM, LF endings, two-space indentation, one terminal LF. Use FR-REC-001 key order. Sort registries by ids; lane records by event id; unordered ids/roles/flags/candidates lexically after deduplication; preserve evidence/field-op/document sequence only where declared. Never emit JSON null, blank strings, `TBD`, or free-text `N/A`/`NONE`. Exact decimals are quoted base-10 without grouping or exponent and **omit trailing fractional zeros**; fractions are reduced strings; dates are ISO; sentinels uppercase. Raw display forms preserve what the document shows.

**FR-SUP-001 — Support union.** Every supported leaf carries exactly one of `{kind:"QUOTE", evidence_ids:[...]}` or `{kind:"RULE", rule_id, inputs:[...]}`. No other support shape exists. A derivation may cite evidence as context inside `inputs` but never masquerades as a quote.

**D-2 — Scalar normalization.** Normalize a certain quoted scalar without changing meaning: Unicode NFC; trim edge whitespace; collapse internal whitespace for normalized names; uppercase normalized names and identifiers; remove money grouping; map a visible `$` to `USD`; reduce a stated fraction; preserve leading zeros in identifiers; parse only an unambiguous four-digit-year date to ISO. Store raw and normalized forms. **Never expand a two-digit year.** Preserve spaces in an identity component; percent-escape only `%` and `:`.

*D-2 is in §0 rather than §4 because `FR-ANC-001` needs it to compute an `anchor_id`, and a discovery lens loads §0+§1 only. A rule invoked by a block is loaded by every pass that loads that block.*

**FR-LOAD-006 — Per-pass block loads.** Each pass loads exactly:

| pass | blocks |
|---|---|
| discovery lens ×11 | §0, §1, its own §2 item, `discovery.schema` |
| `DOCUMENT_SUPPORT` ×1 | §0, §1, §3, `discovery.schema` |
| enrichment ×E | §0, §1, §4, the `(function, module)` module, `enrichment.schema` |
| assembly ×1 | §0, §1, §4, §5, all loaded modules, `template.json` |
| registration | §0, §6, the selected adapter, and the `[REGISTRATION]` rule set |
| release gate | §7 and `version-gate.md` |

Schema validation is **not** a semantic pass: it is deterministic computation run by a conforming Draft 2020-12 validator, per `FR-SCHEMA-005`. The semantic page passes remain twelve.

**The `[REGISTRATION]` rule set** is `FR-REC-012`, `FR-REC-013`, `FR-DATE-008`, `FR-QTY-005`, and `D-9`. Each is marked `[REGISTRATION]` at its definition and each is loaded by the registration pass wherever it is physically filed. They sit in §4 and §5 because they were filed by topic; **filing by topic is the defect this ordering exists to remove**, and moving them physically is a build-tool task, not a licence to leave the dependency undeclared.

**A rule may cite only rule ids present in the blocks and rule sets its own pass loads.** A citation across that boundary is a build defect, not a documentation nit: the pass cannot execute the rule and produces a confident answer with a complete-looking ledger. This table is the input to the static dependency-closure check.

**This table is authoritative for what a pass loads.** `FR-LOAD-001` describes how the *bundle* is composed and selected; it is not a statement that any single pass holds all of it. Where the two appear to disagree, `FR-LOAD-006` governs.

<!-- BUILD:CORE §1 DISCOVERY -->
## §1 Discovery core

Read by every discovery lens, by the support pass, by enrichment, and by assembly. Nothing here may name a specific function's admitted paths.

### 1.1 Pages and anchors

**FR-PAGE-001 — Supplied-image inventory.** Open every supplied image in numeric package order. The scans have no evidentiary text layer: OCR may locate text, but every quoted character is verified on the image. Assign `p01`…`pNN`; `NN` is the count of images, not any printed or registered count. Store one primary page class from the first matching row:

1. visible recording/endorsement cover header → `COVER` or `COVER_CONTINUATION`;
2. visible supporting-document cover header → `SUPPORT_COVER`;
3. incorporated exhibit/rider under FR-PAGE-003 → `EXHIBIT` or `RIDER`;
4. page containing operative instrument clauses → `INSTRUMENT`;
5. titled filed tax/transfer/compliance form → `SUPPORT_FORM`;
6. only acknowledgement/jurat → `ACKNOWLEDGMENT`;
7. only back-panel/record-and-return material → `ENDORSEMENT`;
8. no visible content → `BLANK`;
9. otherwise → `ADMIN`.

Store legibility separately as `CLEAR`, `PARTIAL`, or `UNREADABLE`; a partly legible page never becomes a semantic page class. Store `encoded_resolution` — the pixel dimensions and effective dpi at which the pass actually inspected the page.

**FR-PAGE-002 — Page-count reports.** Record each visible or registration page count as a separately quoted report with its raw label and apparent scope. Never use it as the extraction inventory and never force unlike reports to agree. A cover `PAGE 1 OF 5`, cover field `Document Page Count: 3`, registration `pages: 5`, and eight supplied images may all coexist. Only a missing or duplicate image against the supplied package manifest is an input-integrity failure; count disagreement alone is not.

**FR-PAGE-003 — Incorporation.** Treat an attached page as instrument content on the first satisfied test: (a) exact body label and page label match; (b) an explicit `annexed/attached hereto` reference plus exactly one unattached page whose visible subject matches the named subject; (c) uninterrupted executed pagination or title plus signature or initials continuity. Record the test and both section ids. If none succeeds, classify the page normally.

**FR-PAGE-005 — Incorporated section not supplied.** When an executed clause says a section, schedule, exhibit, or rider is attached or made part of this instrument and **no supplied candidate page exists**, keep the referring clause's normal disposition and create an `incorporated_section_references[]` record with `target_status: NOT_SUPPLIED`, raw label, and support. A required value whose contents lie in that target is `UNKNOWN/INCORPORATED_SECTION_NOT_SUPPLIED`, never `NOT_STATED` and never `UNRESOLVED_SECTION`. It is not an external reference: the instrument says the target is part of itself. This is extraction `EXCEPTION` unless the absent target prevents a mandatory function, object, or placement key, in which case FR-QC-009 scoping governs.

**FR-PAGE-004 — Marks.** A handwritten or typed insertion in an executed blank controls the preprint in that blank. A checked option is present. An unchecked option is not its negation. Struck or obliterated text is not positive evidence; a visible replacement is evidence. Do not restore obliterated content from context or registration.

**FR-PAGE-006 — Unattributed annotation.** An insertion, marginal note, or interlineation that is unsigned, uninitialled, and undated, and does not sit in an executed blank or replace struck text, is inventoried as its own anchor with class `UNATTRIBUTED_ANNOTATION`. Quote the annotation and its visual anchor. **It fills no party, state, term, or time field** unless an enumerated execution test proves adoption — party initials or signature expressly adopting the insertion. Readability is not adoption, and a resolved visual attachment is not adoption.

**FR-ANC-001 — Anchor grammar.** An anchor is the smallest region a pass can point at. Its identity component is taken from the first applicable: printed field label; clause number plus heading; signature or stamp label; the literal annotation text, or the enclosing printed label plus `NONCHARACTER_MARK` where the mark bears no readable character; otherwise the D-2-normalized leading text of the region, truncated at 64 characters on a character boundary. `anchor_id` is `A` plus the first 16 hex of SHA-256 over the canonical tuple `(page_id, controlled_zone, identity_component, occurrence_index)`, where `occurrence_index` counts identical identity components **on that page only** and is independent of unrelated regions. Controlled zones are `TOP`, `UPPER`, `MIDDLE`, `LOWER`, `BOTTOM`, `MARGIN_L`, `MARGIN_R`, `STAMP`, `HANDWRITTEN`.

**FR-ANC-002 — Mechanical atomicity.** One anchor is exactly one of: a heading; a paragraph or numbered/lettered clause; a form row, or an individually labelled field within a row; a signature line; an acknowledgement; a stamp; a marginal annotation; a handwritten insertion or mark; an exhibit item; or the smallest administrative region. **Split any visually grouped region whenever its children could receive different evidence, legibility, or dispositions.** In columns, order top-to-bottom within the leftmost column, then the next column, unless a printed sequence crosses columns. Atomicity is decided before any semantic question is asked of the region.

**FR-ANC-003 — Anchors are found, not cut.** Anchors arise from lens hits and from the FR-DOC-002 visual-residual inventory, then snap to FR-ANC-002 units. There is no prior semantic segmentation pass. Sections in the final output are the union of snapped anchors; §5 assembles them.

### 1.2 Evidence

**FR-EV-001 — Evidence atom.** Store `source_kind` (`PAGE_IMAGE` or `REGISTRATION`), anchor id or raw JSON path, controlled zone and occurrence ordinal for images, shortest verbatim span sufficient to prove the field, `legibility`, `encoded_resolution`, and candidate readings when partial. Preserve visible characters, spelling, capitalization, punctuation, handwriting and strike status; collapse visual line breaks and spacing runs to one ASCII space. A visible table cell is quoted as label plus value. Never cite a path, URL, filename, query, inferred page number, or slate value.

**FR-EV-001a — Mark bearing no character.** For a visible mark with no readable character, set `quote` to the containing printed label, `quote_is_label: true`, `mark_status: NONCHARACTER_OR_UNRESOLVED`, and carry the candidate transcriptions and crop. **The label does not prove a value.** No semantic value may be emitted from the mark until a character is supported. If competing transcriptions would change a semantic output, FR-ESC-002(1) applies. This rule exists because FR-EV-001's verbatim-span requirement and FR-SER-001's ban on blank strings are otherwise jointly unsatisfiable for such a mark.

**FR-EV-010 — Searched-and-empty is not a finding.** A labelled field a pass was required to visit is disposed of by the first matching row:

| condition | disposition | emits |
|---|---|---|
| a readable value is present | normal evidence atom | atom, anchor |
| a **visible mark** bearing no readable character | `VISIBLE_UNREADABLE_MARK` → FR-EV-001a | atom, anchor, candidates, crop |
| **no mark of any kind** | `EMPTY_FIELD_SEARCHED` | **nothing** — no atom, no anchor, no semantic null, no finding |

`EMPTY_FIELD_SEARCHED` is recorded once per page-function cell as a count, not per field. An empty field has no mark, no proving span, and no candidate transcription, so FR-EV-001a cannot apply to it: that rule's subject is a mark. **A rule that turns blank fields into findings converts exhaustive search into affirmative noise**, which is the sweep's own failure mode inverted, and it would fire proportionally to a residue this framework has not measured.

**FR-EV-002 — Semantic proof.** A quoted passage must prove that exact semantic field, not merely contain the same number, name, or date. Presence is not proof. `$2,102.00` labeled transfer tax cannot support `FULL_SALE_PRICE = 525500`.

**FR-EV-003 — Derived support.** A derived field uses `{kind: RULE, rule_id, inputs}`. Every input path has closed support. Store a `derivation_record` when a D-rule requires audit details.

**FR-EV-004 — Source authority is field-local.** Choose the highest available source for the exact field:

| field | controlling order |
|---|---|
| present legal act, object, effect, operative party role, rights, duties, conditions, applicable time | executed operative clause → incorporated directed schedule/rider → executed form performing that act → visible cover |
| signature, capacity, authority, acknowledgement | executed signature/authority/acknowledgement section → operative clause → visible cover |
| indexed classification, current recording id/time, indexed BBL/unit/extent | image cover → adapter-normalized registration → body |
| transfer-report value/use and tax-return field | executed named form/return → same-kind image cover field → image-proven same-kind registration report |
| debt/security economics | executed debt/security clause → directed executed modification/schedule → same-kind image cover field |
| named tax/fee amount | executed same-kind return/receipt → image cover label → image-proven same-kind registration report |

Same-rank incompatible values remain field-local candidates after testing distinct scopes and kinds and express correction. A lower-rank difference is `source_discrepancy`, not automatically document ambiguity. Nominal consideration and full sale price are different kinds.

**FR-EV-005 — Illegibility sequence at discovery.** Read the supplied render; if a matrix-relevant character remains uncertain, use one 900-dpi full-page or lossless crop reread. **A discovery pass stops here.** If two graphic candidates survive the reread and would alter function, character or mode, placement, state path, quantity or term, pointer, or coverage disposition, return `UNCERTAIN` with `uncertainty_kind: VISUAL_CANDIDATES` per FR-SWP-006, carrying both candidates and the crop. Registration may corroborate its own indexed field but never repair body text. **A reread is generated in response to what this pass found; it is never part of the shared prefix.**

Digit adjudication under D-1 and escalation routing are **not discovery acts** — they run at enrichment and at the heavy tier, which load the blocks that define them. This is deliberate: a discovery lens that adjudicated glyphs would be classifying, and eleven isolated lenses adjudicating the same mark would produce eleven adjudications for FR-COV-004 to reconcile.

**FR-EV-006 — Registration referent firewall.** A declared path proves index location, not semantic referent. Registration fills event quantity, term, time, role, share, scope, or state only when image evidence proves that referent; otherwise retain an index report with referent `UNKNOWN`. Current id and time, page reports, raw pointers, indexed names, and parcel candidates are technical reports, not event semantics. Type and co-occurrence never choose.

**FR-EV-007 — Index versus referent.** A summary, count, aggregate, column, or derived index describes the index. It supplies no property of the corpus, of a registry, or of any document. Read a field's referent from the values it holds and from an adapter declaration, never from its name, its type, its null rate, or a distribution over it. The stratified slate yields registry-expressible sample counts only, never corpus proportions.

**FR-EV-008 — Pattern coverage and residue.** Any rule keyed to a value pattern — a filler set, a label list, a literal alias, a trigger phrase — states the pattern's observed coverage and what it does with the residue. A rule written for the dominant case that silently deletes or misclassifies the rare true case is a defect, and the rare case is where the true values live. This rule binds the authors of this framework as well as its readers.

### 1.3 The sweep

**FR-SWP-001 — Function sweep.** Every supplied page is read once **per function**, eleven times, in FR-FN-001 order, plus once by the FR-DOC-002 support pass. A page-function cell with no record is an incomplete extraction, not a clean one. **All eleven run regardless of which modules are nominated:** a lens asks, a module receives, and gating the sweep on nomination omits exactly the content nomination did not anticipate.

**FR-SWP-002 — Lens isolation.** Each lens runs in a fresh inference context carrying §0, §1, its own §2 item, and the document. **It never receives another lens's output.** Eleven passes of one reader are not eleven witnesses: agreement among them is correlated search coverage, never corroboration. No lens result may be resolved by majority.

**FR-SWP-003 — Loading unit.** One whole-document context per function, emitting one cell per supplied page. Isolation is between lenses, not between pages. Pages multiply image inspections, never framework loads. A lens must inspect running text, every labelled field and table cell, signature and acknowledgment blocks, stamps, handwriting, and margins on every page, and emit its per-page cell even where the page is blank.

**FR-SWP-004 — Result union.** A page-function cell is exactly one of:

- `HIT` — an act or assertion within this function's boundary is present; carries `ACT_CANDIDATE` anchors;
- `SUPPORT_ONLY` — content within this boundary exists and supports, but fills no path of this function;
- `NO_HIT` — the search found no span within this boundary;
- `UNCERTAIN` — see FR-SWP-006.

Every cell carries `page_id`, `function`, `status`, anchor ids, `question_set_version`, `search_completed`, and `encoded_resolution`. `HIT` and `SUPPORT_ONLY` carry the smallest proving or candidate span and its legibility.

**FR-SWP-005 — NO_HIT is a search record, not evidence.** `NO_HIT` records that this search reported no span. It carries no evidentiary support, creates no null field unless that field is independently required, and **can never produce `ASSERTED_NONE`**. Eleven `NO_HIT`s across every page establish `NOT_STATED` for this document; they establish nothing about the parcel, the registry, or the world. A `NO_HIT` recorded at a resolution too low to see the content is a weaker record than one recorded where the content was legible, which is why `encoded_resolution` is mandatory on every cell.

**FR-SWP-006 — UNCERTAIN and its destination.** `UNCERTAIN` carries `uncertainty_kind`, the candidate outputs, and the exact affected paths. **No committed record may remain bare `UNCERTAIN`.** Only `VISUAL_CANDIDATES`, `VISUAL_ATTACHMENT_CANDIDATES`, and `RULE_BRANCH_CANDIDATES` are marked `escalation_eligible: true`. **A discovery pass marks; it does not route** — routing is an assembly decision under §5, which discovery does not load. A framework gap, a genuine document conflict, missing content, or a value that is simply not stated routes to its own lane and **is not escalation**.

**FR-SWP-007 — Cross-cutting subcheck.** For every `HIT` and `SUPPORT_ONLY` anchor, and identically for every function, capture as **raw spans**: the participants and their stated roles, capacities, contact and relation words; the object; the parcel or scope words; quantity and value words; date, extent, order, and condition words; pointer and incorporation words; and any express absence. **Raw spans only — classification happens at enrichment.** Eleven lenses classifying one anchor produce eleven classifications and manufacture conflicts that §5 must then adjudicate; deferring classification removes them by construction. This subcheck is why a Title lens captures a party's stated address without the address becoming an Identity event.

**FR-SWP-008 — Boundary exclusion without nomination.** When a span matches a boundary other than the target's, the lens records `EXCLUDED_BY_BOUNDARY:<function or rule id>` **on the candidate claim, not on the anchor**, or returns `NO_HIT`/`SUPPORT_ONLY` for its own function. **It does not nominate the other function.** A nomination is one lens telling another what to look for, which is FR-SWP-002 violated through the back door as helpfulness. The other lens finds the span independently or not at all.

**FR-SWP-009 — Candidate claim identity.** One anchor may carry several candidate claims — a clause conveying an estate *and* imposing a use restriction is two. **Every `HIT` and `SUPPORT_ONLY` anchor enumerates its candidate claims, not only the excluded ones.** Assign `candidate_claim_id = CC` plus the first 12 hex of SHA-256 over the canonical tuple `(anchor_id, claim_raw)`, where `claim_raw` is the smallest span stating that one claim.

Every exclusion names its claim id, and **every emitted event names the claim ids it resolves in `resolves_claim_ids`**. Identity assigned only on the negative path cannot be matched against on the positive one: FR-COV-005's three tests ask whether *this claim* was answered, and an event that does not say which claim it answers cannot answer the question. **Without claim identity on both paths, two claims on one clause collapse** — a correct `SUPPORT_ONLY` for one appears to resolve the other, or both report as one orphan, and the difference is invisible in the output.

**FR-FN-001 — Function boundaries.** The eleven functions in fixed order, with the boundary question each lens is asked. **Every lens carries this whole table as a negative contrast: a boundary cannot be applied without knowing what lies on the other side of it.** Only the target's positive card in §2 carries admitted paths, triggers, and examples, and the discovery schema permits a `HIT` only for the target function.

| function | boundary question |
|---|---|
| `IDENTITY` | Does the act or assertion establish or change formal parcel/unit identity, boundary, composition, designation, name, or address? Routine premises description is scope only. |
| `TITLE` | Does it create, transfer, correct, surrender, or terminate ownership or an expressly possessory estate? |
| `ENTITLEMENT` | Does it grant or change a non-possessory land-use or development capacity, right, option, or authorization? |
| `ENVELOPE` | Does it legally constrain or allocate physical mass or form — height, setback, bulk, area, facade, structural envelope — even without a number? |
| `ENCUMBRANCE` | Does it create or change a lien, security interest, easement, covenant, land-running burden or benefit, rents assignment, or priority relation? |
| `CAPITAL` | Does it create or change a debt, facility, funding or equity obligation, principal or balance, repayment, or finance term? |
| `PERMIT` | Does a named government authority receive, issue, amend, suspend, renew, or revoke authorization for work or regulated operation? |
| `AS_BUILT` | Does it observe or assert what physically exists or was completed? |
| `OCCUPANCY` | Does it observe or assert actual use/capacity or government-authorized use/capacity, with basis distinguished? |
| `COST` | Does it state project expenditure or commitment, or a labeled transaction or filing tax or fee? |
| `VALUE` | Does it state sale or nominal consideration, assessed, appraised, or fair-market value, or another property or interest valuation? |

### 1.4 Party grammar

Grammar only. The party registry schema is §5; splitting them is deliberate and follows the load classes.

**FR-PARTY-002 — Roles and capacity.** The body's operative grammar controls legal role. Preserve visible `role_raw`. Cover panel numbers have no role meaning. Indexed role labels are `indexed_role` only unless body words expressly delegate to them. Preserve capacity and relationship words verbatim; **do not turn spouse, trustee, custodian, affiliate, or officer language into identity, share, tenancy, or personal obligation.**

**FR-PARTY-005 — What counts as a stated party span.** A distinctly named person or entity is a party span wherever named, including when named only as a representative, parent, affiliate, or signatory. Capture the name verbatim. **Do not decide operative status at discovery** — registry membership is not operative status, and §5 decides participation from event grammar.

**FR-PARTY-006 — Stated attribute spans.** Capture as raw spans, per named party: address words with their governing preposition (`residing at`, `with addresses at`, `whose address is`); telephone and electronic-mail words; legal-form designators; and any express relation between two named parties with its verbatim relation words. **Never infer the beneficial owner.** A relation is captured only when the document states it; a holding company with no stated parent stays a holding company.

**FR-EV-009 — Legal designators are grammar, not name shape.** Entity type is set only from an exact form or grammar label, or from the closed legal-designator table in the adapter. Absent one, entity type is `UNKNOWN`. Inferring a person or an organization from how a name looks is prohibited.

<!-- BUILD:CORE §2 LENS CARDS -->
## §2 Per-lens cards

Exactly one card loads per discovery lens, appended to §0+§1. Each card carries positive vocabulary for its own function only, plus the FR-FN-002 collision rows naming that function. **The negative contrast table in FR-FN-001 is shared; positive vocabulary is not.** Positive vocabulary for a function the lens cannot emit is an invitation to emit it.

**FR-FN-002 — Mandatory boundary tests.** Each card carries every row below that names its function; no card carries the whole table.

1. Express debt **and** collateral → linked Capital + Encumbrance; one layer alone → only its function. Lien or UCC release and payment never imply each other. *(Capital, Encumbrance)*
2. Possessory lease creation, transfer, surrender, or termination → Title leasehold; memorandum of an elsewhere-made lease → Title NOTICE. Lease or rent security → Encumbrance/Capital per clause; a fee burden requires separate express words. *(Title, Encumbrance, Capital)*
3. Easement or covenant → Encumbrance; add Envelope for physical mass or form, Entitlement for granted development capacity, Title only for express possession. Air and subterranean interests follow the same possessory/right/burden/form split. *(Encumbrance, Envelope, Entitlement, Title)*
4. Zoning-lot composition or geometry → Identity; capacity or right → Entitlement; bulk or form constraint → Envelope. Agency or application naming is not Permit. *(Identity, Entitlement, Envelope, Permit)*
5. Government-authorized use → Occupancy `AUTHORIZED`; express actual use → `ACTUAL`; **a private use restriction is Encumbrance, not Occupancy.** *(Occupancy, Encumbrance)*
6. Government work or operation authorization → Permit; private or title-company certification is not Permit. *(Permit)*
7. Sale and nominal consideration → separate Value kinds; project expenditure → Cost; financing principal → Capital; a labeled tax or fee → Cost. *(Value, Cost, Capital)*
8. A general deed warranty or covenant is a Title term. An encumbrance-absence observation requires express present absence of a named, scoped burden. *(Title, Encumbrance)*
9. A contract of sale creates no categorical event. Emit only expressly filled rights, options, or burdens; never import equitable conversion. *(Title, Entitlement, Encumbrance)*

**Card `IDENTITY`.** Fires only on express creation, merger, apportionment, subdivision, renumbering, supersession, correction, or present certification of a formal parcel, unit, or zoning-lot composition or designation. Trigger words: *creates, merges, apportions, subdivides, renumbers, supersedes, is hereby designated, is certified to be.* Admitted receiving paths, ESTATE_IDENTITY: `identity.designations`, `.existence_status`, `.composition`, `.former_designation`, `.new_designation`. A premises recital, an operative subset, or a partial-premises description is **scope**, never Identity. Named parties are not Identity content — capture them through FR-SWP-007. Rows 4.

**Card `TITLE`.** Fires on creation, conveyance, assignment, surrender, correction, or termination of a fee, condominium, common, life, remainder, leasehold, subleasehold, or undivided estate; on an express present possession statement; and on any separately printed operative **exception, reservation, covenant, assumption, or lease term** attaching to the estate conveyed. Trigger words: *grants and releases, conveys, demises, leases, assigns, surrenders, subject to, excepting and reserving, together with, assumes, covenants.*

Admitted receiving paths, ESTATE_IDENTITY — a printed clause matching any of these is a `HIT`, not a `NO_HIT`: `title.estate_label`, `.holders`, `.reservations`, `.exceptions`, `.appurtenant_interests`, `.possession_statement`, `.tenancy_raw`, `.covenant_raw`, `.assumption`, `.consideration_quantity_ids`, `.subject_to_pointer_ids`; and for a lease estate `title.lease.premises`, `.permitted_use`, `.rent_quantity_ids`, `.security_deposit`, `.assignment_consent`, `.subletting_consent`, `.renewal_option`, `.purchase_option`, `.termination_option`, `.default_remedy`.

`interest_kind` is mandatory and never defaults from a deed label. A separately identified common interest is its own object even when conveyed together with a unit, and the parent's `appurtenant_interests` link is cumulative with it. Rows 2, 3, 8, 9.

**Card `ENTITLEMENT`.** Fires on grant, transfer, reservation, or change of a **non-possessory** land-use or development capacity, right, option, or authorization. Trigger words: *grants the right to, reserves the right to, transfers development rights, air rights, licence, option to.* Admitted receiving paths, LAND_RIGHTS: `entitlement.right_kind` (`DEVELOPMENT_RIGHT`, `AIR_RIGHT`, `SUBTERRANEAN_RIGHT`, `LAND_USE_AUTHORIZATION`, `LICENSE`, `OPTION`, `OTHER_NAMED`), `.holders`, `.capacity`, `.authority_or_source`. A named application or a desired approval is a term or reference, not Entitlement. Rows 3, 4, 9.

**Card `ENVELOPE`.** Fires on a legal constraint or allocation of physical mass or form. Trigger words: *shall not exceed, setback, floor area, lot coverage, bulk, facade, height limit, buildable.* Admitted receiving paths, LAND_RIGHTS: `envelope.constraint_kind` (`HEIGHT`, `SETBACK`, `FLOOR_AREA`, `LOT_COVERAGE`, `BULK`, `FACADE`, `STRUCTURAL`, `BUILDABLE_VOLUME`, `SUBTERRANEAN_VOLUME`, `OTHER_NAMED`), `.limit_or_allocation`, `.geometry`, `.permitted_work`, `.prohibited_work`, `.preservation_standard`. **No number is required.** A description of what exists rather than what is constrained is As Built. Rows 3, 4.

**Card `ENCUMBRANCE`.** This function is fed by **two** modules and the card carries both. Fires on creation or change of a lien, security interest, easement, covenant, land-running burden or benefit, rents or proceeds assignment, declaration burden, option, right of first refusal, lis pendens, priority relation, **or a privately imposed use restriction.** Trigger words: *mortgages, grants a security interest, subject to the declaration, covenants running with the land, easement, shall be used only for, subordinate to, assigns the rents, releases of record.*

Admitted receiving paths, SECURED_FINANCE: `encumbrance.security_kind` (`MORTGAGE_LIEN`, `UCC_FIXTURE`, `ASSIGNMENT_OF_RENTS`, `OTHER_SECURITY`), `.holders`, `.collateral_scope`, `.priority`, `.rents_proceeds`. LAND_RIGHTS: `encumbrance.land_kind` (`EASEMENT`, `COVENANT`, `DECLARATION_BURDEN`, `USE_RESTRICTION`, `OPTION`, `ROFR`, `LIS_PENDENS`, `OTHER_NAMED`), `.beneficiaries`, `.burdened_parties`, `.physical_scope`, `.legal_scope`, `.access`, `.inspection`, `.construction_duty`, `.maintenance_duty`, `.cost_responsibility`, `.runs_with_land`. Rows 1, 2, 3, 5, 8, 9.

**Card `CAPITAL`.** Fires on creation or change of a debt, note, credit facility, funding or equity obligation, principal, balance, payoff, maximum lien, repayment, rate, or finance term. Trigger words: *promises to pay, indebtedness, principal sum, matures, interest at, guaranty, prepayment.* Admitted receiving paths, SECURED_FINANCE: `capital.obligation_kind`, `.obligors`, `.obligees`, `.original_principal`, `.current_balance`, `.payoff`, `.maximum_lien`, `.credit_limit`, `.new_money`, `.rate`, `.rate_type`, `.rate_index`, `.rate_margin`, `.payment`, `.advance_right`, `.readvance_right`, `.prepayment`, `.default`, `.guaranty`. Security without a stated obligation is Encumbrance alone. Rows 1, 2, 7.

**Card `PERMIT`.** Requires a **named government authority** plus a stated application, receipt, issuance, approval, amendment, renewal, suspension, revocation, or expiry of authorization for work or regulated operation. Admitted receiving paths, PUBLIC_PHYSICAL: `permit.kind`, `.identifier`, `.authority`, `.work_scope`, `.status`, `.conditions`. Private, engineer, or title-company certification never qualifies. Rows 4, 6.

**Card `AS_BUILT`.** Fires on an observation or assertion of what physically exists or was completed: item kind, geometry, floor area, unit count, completion, condition, location, operational status. Admitted receiving paths are PUBLIC_PHYSICAL `as_built.item_kind`, `.geometry`, `.floor_area`, `.unit_count`, `.completion`, `.condition`, `.location`, `.operational_status`.

**Visit every labelled measurement field on a form, then dispose of it by FR-EV-010.** A field bearing a visible mark with no readable character is `VISIBLE_UNREADABLE_MARK` and a finding under FR-EV-001a. **A field with no mark at all is `EMPTY_FIELD_SEARCHED`, which creates no evidence atom, no anchor, no semantic null and no finding** — it is a search result, not content. Rows: none.

**Card `OCCUPANCY`.** Fires on an observation or assertion of actual use or capacity, or of government-authorized use or capacity. Trigger words: *is occupied as, certificate of occupancy, permitted occupancy, maximum occupancy, presently used as.* Admitted receiving paths, PUBLIC_PHYSICAL: `occupancy.basis` (mandatory, `ACTUAL` or `AUTHORIZED`), `.use`, `.capacity`, `.certificate_id`, `.subject`. It does **not** absorb a privately imposed use restriction, which is Encumbrance. A disjunctive statement uses `DISJUNCTIVE_SET` and promotes no member. Rows 5.

**Card `COST`.** Fires on a stated project expenditure or present commitment to expend, or on a labeled transaction or filing tax or fee. Trigger words: *will apply the consideration first to the payment of the cost of the improvement, shall expend, transfer tax, mortgage tax, recording fee, filing fee, paid, charged, due, assessed, exempt.* Admitted receiving paths, ECONOMICS: `cost.kind` (`PROJECT_EXPENDITURE`, `PROJECT_BUDGET`, `CONTRACT_COMMITMENT`, `TRANSACTION_TAX`, `RECORDING_FEE`, `OTHER_NAMED`), `.amount`, `.status`, `.subject`, `.payer`, `.payee`.

Not every obligation to pay: a repayment obligation is Capital and a purchase price is Value. **A clause presently committing a party to project expenditure is a Cost transaction whether or not an amount is stated** — a missing amount is a missing measurement, not a missing commitment. A form reporting a budgeted, incurred, charged, paid, assessed, or exempt amount is a Cost observation. Rows 7.

**Card `VALUE`.** Fires on stated sale or nominal consideration, assessed, appraised, or fair-market value, or another property or interest valuation. Trigger words: *in consideration of, ten dollars and other valuable consideration, full sale price, assessed value, appraised at, fair market value.* Admitted receiving paths, ECONOMICS: `value.kind` (`NOMINAL_CONSIDERATION`, `FULL_SALE_PRICE`, `ASSESSED_VALUE`, `APPRAISED_VALUE`, `FAIR_MARKET_VALUE`, `OTHER_NAMED`), `.amount`, `.subject_interest`, `.basis`, `.completion_basis`. Nominal consideration and full sale price are separate kinds at any numbers. Financing amounts are Capital; project amounts are Cost. Rows 7.

<!-- BUILD:CORE §3 SUPPORT -->
## §3 Document support pass

The twelfth read. Whole-document, one context, semantic. It emits no function event.

**FR-DOC-001 — Why it exists.** Eleven function lenses cannot guarantee facts that validly fill **no** function. An authority-only instrument with no function event would otherwise capture no parties at all. Running the cross-cutting subcheck only on function hits reproduces, on a zero-event document, exactly the omission the sweep was built to cure.

**FR-DOC-002 — Visual-residual inventory.** Inventory every visible text region, mark, stamp, signature, and annotation on every page. Union the anchors from all eleven lenses; every region **not** in that union is a residual. Each residual is disposed of as `ADMINISTRATIVE`, or **backfilled through the eleven FR-FN-001 boundary questions** — which this pass loads with §1 — and recorded as `BACKFILL_CANDIDATE` naming the boundaries it may match, or as `NO_LENS_CLAIM` where none matches. A residual may add or split anchors; final sections are the snapped union.

**The backfill records candidates; it does not classify.** This pass loads no §2 positive card and cannot emit a function event, so a matched residual is a candidate for that lens's function which §5 adjudicates — recorded, never resolved here.

This pass is semantic: an unclaimed region cannot be identified as unclaimed by geometry, because a lens anchors a *field* while a connected component is a *shape*, and the two agree only where unanchored content sits in whitespace.

**FR-DOC-003 — Support registries.** This pass extracts, independent of any function: party attribute and relationship spans under FR-PARTY-005/006; capacity and authority recitals; raw pointer and incorporation words; current-recording identity; notarial anchors; page-count reports; signature and execution inventory; and marks under FR-EV-001a. These populate §5 registries and never a state delta.

**FR-DOC-004 — Backfill.** Anything operative-looking that all eleven lenses missed is recorded with its anchor, the candidate function(s), and `SWEEP_BACKFILL`. It does not become an event here; §5 decides, and a backfilled candidate that no lens found is a coverage finding regardless of outcome.

<!-- BUILD:CORE §4 ENRICHMENT -->
## §4 Enrichment

Read by enrichment passes and by assembly, never by a discovery lens. Enrichment reruns only the `(function, module)` pairs that hit, batched across their pages.

**FR-DER-001 — Closed derivation registry.** The loaded bundle's stable classification rules and D-1 through D-10 are the complete extraction derivation set. No analogy, plausibility, customary rule, unstated conversion, or unlisted calculation is admitted.

**D-1 — Intra-document digit exemplar comparison.** Apply only after FR-EV-005 and only to one ambiguous Arabic digit `0–9`.

1. Before exemplar search, record the target location and a visually derived candidate set of **exactly two** digits. Field meaning, arithmetic, registration, expected content, and outside knowledge may not supply either candidate. This order claim is auditable but not fully provable from final output; fresh-context frozen reruns are the independent check.
2. Admit one `writer_cluster_id` only by `CONTINUOUS_ENTRY` (target and exemplars lie in one uninterrupted handwritten entry) or `CROSS_ENTRY_STYLE_MATCH` (at least three distinct certain non-target glyphs recur in both entries and match, with no mismatch, on recorded loop topology, connected-component form, slant bucket, terminal direction, and relative height). Ink color, tone, line weight, page proximity, subject matter, and registration are insufficient; bitonal scans destroy the first three as reliable evidence.
3. Inventory every certain occurrence of each candidate digit in the admitted cluster; do not select convenient exemplars. Before choosing, record features invariant across each candidate class. The target matches a class only when it matches every invariant. Where competing-class exemplars exist, it must fail at least one invariant of that class.
4. Resolve two-sided when the selected digit has at least two certain exemplars, all inventoried forms are consistent, and the competing class does not match. Resolve one-sided only when the pre-recorded set is binary, the selected digit has at least two certain exemplars, every occurrence is inventoried, at least two independent construction features recur in all and in the target, no exemplar contradicts, and no competing exemplar exists. **Absence of the competitor is not evidence; positive recurrence is.** Record `TWO_SIDED` or `ONE_SIDED`, every location, count, inventory scope, features, and output digit.
5. Otherwise keep both candidates and continue to escalation. D-1 never infers a field's content or semantic kind.

Letters, punctuation, signs, ligatures, and whole tokens are deferred, not permanently excluded. Their recoverable loss — including handwritten party names — must be counted; extend only through a separate frozen fixture and an enumerated rule.

*D-2 is defined in §0, not here, because `FR-ANC-001` needs it at discovery. Every pass that loads §0 holds it.*

**D-3 — Canonical BBL.** From cited borough plus block plus lot, map borough `Manhattan/New York=1`, `Bronx=2`, `Brooklyn/Kings=3`, `Queens=4`, `Staten Island/Richmond=5`; left-pad block to five and lot to four digits. Do not derive any component from address or geometry.

**D-4 — Partial-date interval.** A stated four-digit year becomes the closed Gregorian interval January 1–December 31; a stated month becomes its first–last calendar day; a day has equal endpoints. Preserve precision. Never print a padded day as the stated value.

**D-5 — Document-stated arithmetic.** Derive a numeric result only when the document itself states an exhaustive equation, subtotal or total relationship, or formula; every operand is quoted; and operators are limited to exact `+`, `−`, `×`, `÷`. Record expression and exact inputs. A displayed total, when present, is the source and arithmetic is validation. External rates and constants, tax-rate back-computation, plausible components, and division by zero are excluded.

**D-6 — Explicit allocation.** Allocate one quoted total only when the document states exhaustive target shares or a complete formula. Record exact arithmetic, targets, and remainder; allocations must sum exactly to the stated total when the text says exhaustive. **Otherwise retain one `NOT_DERIVABLE` total and emit no per-target records.** A stated total plus n named parties never yields n shares: headcount is a property of the record, not a statement of the document.

**D-7 — Express equality or definition.** Propagate a value within this document only when an exact definition, equation, or incorporated schedule says the two named fields or terms are identical. Similar labels, values, parties, or context are insufficient.

**D-8 — Controlling-source selection.** Select among already typed same-field candidates by FR-EV-004 after separating semantic kind and scope. Record every candidate, ranks, selected input, and lower-rank discrepancies. This never changes a candidate's semantic kind.

**D-9 `[REGISTRATION]` — Pointer parsing.** Split a quoted external locator into only visibly present components (document id, `CRFN`, file number, borough, year, reel, page, book, instrument, map sequence, or `OTHER`). Preserve `locator_raw`; parsing never resolves a target document.

**D-10 — Exact local linkage.** Reuse an in-document object or value reference only on an exact recorded identifier, an exact defined local name, an exact section or schedule pointer, or a demonstrative whose grammatically available antecedent set contains exactly one keyed object. Similar parties, amounts, dates, parcels, or event proximity are not linkage.

### 4.1 Classification of spans

**FR-PKG-001 — Candidate trigger.** For every anchor with a `HIT` or `SUPPORT_ONLY` cell, identify each present-tense operative verb/object pair that grants, conveys, leases or demises, assigns, assumes, creates, amends, corrects, subordinates, releases, terminates, files, certifies, approves, revokes, or expressly declares a matrix state; and each signed or certified assertion of a current or explicitly dated state. Emit one single-function event for every independently filled module path.

**FR-PKG-001a — Additive paths.** A phrase-triggered term on one function is **not consumed** by a linked event on another function. Emit every independently required path, then apply split and merge. A Declaration exception fills both `title.exceptions` and a separate Encumbrance event; a Lien Law improvement-cost covenant fills both `title.covenant_raw` and a Cost transaction. Merge only on exact object-key equality proved under D-10.

**FR-PKG-002 — No-event content.** Do not emit for a historical recital alone, a definition alone, a signature or acknowledgement alone, a notice or return address, preparer, notary, or fee-routing metadata, a form id, an unchecked alternative, a general warranty or boilerplate with no filled state path, a legal description used only as another event's scope, or a reference to an unseen act. Definitions may supply values.

**FR-PKG-003 — Assertion and absence.** Emit an observation only when executed words assert a function path, including an express scoped absence. An assertion that no encumbrance, assignment, permit, occupancy, equipment, or other path exists is `OBSERVATION + ASSERT` with `ASSERTED_NONE`, stated scope, affected parcels, and asserted-valid time when stated. A blank, an unchecked box, a covenant only against one party's own acts, or a promise about future conduct is not a parcel-state absence assertion.

**FR-PKG-004 — Split dimensions.** Split when any of these differs: function; state-object key; mode; applicable or valid time; unconditional versus condition-dependent effect; FROM/TO party set or share; independently operating parcel set; or noncommuting field paths. Keep asymmetric parcel roles of one transaction together. Keep one amount shared through its quantity id.

**FR-PKG-005 — Merge test.** Merge adjacent candidates only when all are equal: state-object key, function, mode, epistemic character and lane, time object and status, party-direction set, affected BBL/scope set, and event condition; and their field operations commute. Preserve every anchor and evidence id. **Similar parties, amount, date, or parcel never supplies object equality**, and topical proximity is not equality: a locally stated use restriction is its own keyed Encumbrance unless exact D-10 language makes it a field of an already keyed covenant.

**FR-MODE-001 — Ordered mode test.** After scope splitting, take the first match: (1) words identify a prior value in this same object or act as erroneous or omitted and replace or delete it → `CORRECT`; (2) words end the whole identified object or effect → `TERMINATE`; (3) words move an existing object, interest, or obligation between holders with its identity continuing → `TRANSFER`; (4) words change an identified continuing object's field, scope, or priority — a partial release is here → `MODIFY`; (5) words bring the object, right, or obligation into existence → `CREATE`; (6) words state a condition without changing it, or legally establish a declaration without creating the described thing → `ASSERT`; (7) none → no event for that anchor and function. Two same-rank incompatible modes after scope splitting create a classification candidate package; do not use page order.

**FR-CHAR-001 — Epistemic character.** `TRANSACTION` performs the act; `OBSERVATION` states evidence about state without changing it; `NOTICE` reports or indexes a claim or act made elsewhere without proving it now. Observation and notice use ASSERT or CORRECT. Transaction uses other modes, except a module-admitted declaration that legally establishes a path may use ASSERT. The set is closed. **Character and mode are separate axes and both are emitted;** neither renders the other.

**FR-FN-003 — Title precondition.** Every Title event and object has a mandatory `interest_kind` from its module, and its key contains that kind. Fee and leasehold objects coexist.

**FR-FN-004 — Appurtenant placement.** A separately keyed interest of **any** `interest_kind` with no independently stated or indexed BBL is placed on an exact affected BBL only when the operative text expressly makes it appurtenant to, part of, or transferred together with the object on that BBL. Use the exact FR-BBL-003 relation role. Shared parties, address, event group, or proximity is insufficient. The separate object and the parent object's `title.appurtenant_interests` link are **cumulative**, not alternatives.

### 4.2 Time

**FR-DATE-001 — Transaction applicable time.** Take the first supported source: (1) an `effective/as of/from/commencing/terminated on` phrase grammatically attached to the present act, or a module-listed equivalent; (2) the present-instrument dating clause governing it; (3) the latest required execution date when all named operative parties are expressly required before effect; (4) dated execution of a unilateral act effective on execution; (5) an acknowledgment expressly proving execution date; (6) UNKNOWN. Basis is respectively `EXPLICIT_EFFECTIVE`, `INSTRUMENT_DATE`, `COMPLETION_OF_REQUIRED_EXECUTION`, `EXECUTION_DATE`, `ACKNOWLEDGED_EXECUTION`, or `UNSUPPORTED`. An index or cover Document Date is only a candidate unless an operative clause incorporates it or a module form makes that label the act or as-of date.

**FR-DATE-002 — Recording never applies.** Registration or cover recording time is a registry fact only. It is never transaction applicable time, observation asserted-valid time, a latest bound, an undated sort key, or a tie-break — even when filing or recording is the legal mechanism and every other date is absent.

**FR-DATE-003 — Observation clocks.** Derive statement or occurrence time into `evidence_time_registry` only from an express date when the statement, certification, report, or affidavit was made. Derive asserted-valid time only from words stating when the observed condition or value held (`as of`, an inspection, survey, or valuation date, `since`, `during`, `from…to`, or an exact form label directed to the observation). An inspection date is valid time, not statement time, unless the text expressly makes it both. **Never copy occurrence time into valid time.** A transaction or instrument date never becomes an observation's asserted-valid time merely because the observation sits in, or concerns, that act. A form-level `Preparation Date`, `Report Date`, or `Certification Date` is occurrence time for assertions on that form unless a narrower occurrence date controls; it is never valid or applicable time. Route a supported valid interval to `observations_dated`; otherwise route to `observations_unplaced` and emit no date-shaped key there.

**FR-DATE-004 — Partial and conflicting dates.** Normalize with D-4. Keep day, month, or year precision. Resolve same-field evidence through FR-EV-004; same-rank incompatible candidates remain UNKNOWN and may escalate if reader-resolvable. A referenced instrument date, preparation date, tax-report date, an acknowledgement not proving execution, and a temporal boundary are not the present act's time. **When a directed valid-time field exists but D-2 cannot normalize it, the unplaced reason is `VALID_TIME_PRESENT_BUT_UNNORMALIZABLE`, not `NO_VALID_TIME_STATED`** — the difference is between a document that said nothing and one that said something this framework cannot yet read.

**FR-DATE-005 — Boundaries.** Promote stated commencement, maturity, expiration, option windows, renewal deadlines, and other future boundaries as **boundary candidates** carrying affected object, function, and parcels, type from `COMMENCEMENT`, `MATURITY`, `EXPIRATION`, `OPTION_OPEN`, `OPTION_CLOSE`, `RENEWAL_DEADLINE`, `OTHER_NAMED` plus raw label, interval, consequence, condition, and `effect_status`. **Enrichment emits candidates; §5 assigns ids and validates shape** — a boundary candidate cites no `B` id, because id assignment belongs to the pass that can see the whole document. A boundary changes composed state only when exact words make the consequence automatic without an unresolved condition and the loaded module marks that path `SELF_EXECUTING`. Mortgage maturity never means payment or lien termination; option close never means exercise.

**FR-DATE-006 — Conditional effect.** If an effect depends on a condition the document does not state has occurred, route it to `conditional_events`, quote trigger and consequence, and emit no unconditional applicable-time key. `CONDITION_DEPENDENT` is not `UNKNOWN`. If this document states occurrence, cite it and route the resulting act normally.

**FR-DATE-006a — Conditional materiality.** Emit a conditional event when the stated consequence **identifies a module path and a keyed state object touched by a present act in this document**. Exclude as `NO_EVENT / BOILERPLATE_EXCLUDED` only a clause whose consequence names no filled path — a pure severability clause reciting that an invalid provision is severed and the remainder survives, naming no object and no path.

A clause providing that on a stated condition a different named instrument or article governs an already emitted object's `encumbrance.legal_scope` **does** identify a path and a keyed object, and is a conditional event. Wording alone never decides: *"other terms continue to govern"* excludes only where those terms are unnamed and no emitted object is touched. `boilerplate` is a disposition reached by testing the consequence against the emitted set, never a label applied by recognition. Frozen as a pair: the Article 18 governing-terms case emits; the pure severability control does not.

**FR-DATE-007 — Sequence.** Capture only exact present-act ordering language, as **ordering candidates** carrying type `BEFORE`, `AFTER`, or `SIMULTANEOUS`, the two act references, and support; §5 assigns `O` ids and resolves references to event ids. `Simultaneously herewith` creates `SIMULTANEOUS`; `immediately prior` and `immediately after` create directed relations. Page order, signature order, recording timestamp, and customary closing sequence never create a relation.

**FR-DATE-008 `[REGISTRATION]` — Index-reported date referent.** Retain registration `doc_date` as `document.index_reported_date`, referent `UNKNOWN`. Change the referent only when an allowed input structurally nests it under, or visibly labels it as, a named current act, reference, or object. Field name, type, numerical agreement, file-number digits, recording time, and form revision date supply neither referent nor century. Unknown-referent dates fill no event, evidence, or boundary time.

**FR-DATE-009 — Canonical notarial anchor.** In `document.notarial_date_anchor`, record `PRESENT`, quote, and the full-word four-digit date from an executed acknowledgment's fixed `On … in the year …` wording; else `NOT_PRESENT`. It is the canonical internal century anchor but proves only acknowledgment occurrence and supplies applicable time only under FR-DATE-001(5). Another date needs an admitted exact link to borrow it. Count absence; financing statements commonly lack acknowledgments.

### 4.3 Parties, parcels, quantities

**FR-PARTY-003 — Direction and shares.** `DIRECTIONAL` requires a supported FROM side parting with or bearing an identified interest, object, or obligation and a supported TO side receiving or holding it. Otherwise `NON_DIRECTIONAL` and sides `NONE`. Several parties per side and several roles per party are allowed. Direction is a **structured relation set**, not necessarily one FROM→TO pair. Extract exact shares. **A share field exists only where words establish a share slot**; it is absent otherwise, and never inferred as equal, marital, or proportional.

**FR-BBL-001 — Parcel inventory versus affected set.** `document.parcel_inventory` records every body, cover, and registration candidate with source and discrepancy. An event's `parcel_bindings` contains only exact BBL/scope pairs affected by that event's clause or assertion. An explicit operative subset controls a broader cover. Indexed parcels may complete the set only when the clause expressly applies to the whole indexed or recorded premises. Addresses, neighbours, referenced parcels, and the document union never default into an event.

**FR-BBL-002 — Canonical identity.** Use a quoted ten-digit BBL or D-3. Preserve raw borough, block, and lot and support. Never derive from address, street, metes and bounds, adjacency, an inferred borough, or an external map. If property-linked but no BBL is supportable, retain the event, use `UNKNOWN/UNSUPPORTED_BBL`, add it to `exceptions.unplaced_parcel`, and make chronology validation non-PASS.

**FR-BBL-003 — Role and scope.** Each affected pair has sorted roles from `SUBJECT`, `GRANTING`, `RECEIVING`, `BURDENED`, `BENEFITED`, `SERVIENT`, `DOMINANT`, `COLLATERAL_LOCATION`, `DECLARED_COMPONENT`, `UNIT_APPURTENANT`; and scope from `ENTIRE_BBL`, `PARTIAL_BBL`, `UNIT`, `AIR_SPACE`, `SUBTERRANEAN_SPACE`, `FACADE`, `EASEMENT_AREA`, `DESCRIBED_PREMISES`, or `UNKNOWN`. Roles remain parcel attributes. A partial, unit, vertical, facade, or easement description never becomes a whole lot during fan. **Same BBL at distinct scopes stays distinct — a unit conveyance and a whole-lot conveyance are different objects and must never merge.** Extract parcel share only when stated.

**FR-BBL-004 — Missing extent.** A bare registration BBL identifies a lot but does not prove whole or partial extent. Emit scope `UNKNOWN/NOT_STATED`, never `ENTIRE_BBL` or `NOT_APPLICABLE`.

**FR-QTY-001 — Quantity registry.** Store each measurement once with `quantity_id`, `kind`, `label_raw`, raw and normalized value, currency or unit, scope, target event, object, parcel, and **party** ids, `allocation_status`, `allocation_group_id`, and support. Assign ids by first supporting anchor, then this kind order: `NOMINAL_CONSIDERATION`, `FULL_SALE_PRICE`, `ASSESSED_VALUE`, `APPRAISED_VALUE`, `FAIR_MARKET_VALUE`, `ORIGINAL_PRINCIPAL`, `CURRENT_BALANCE`, `PAYOFF`, `MAXIMUM_LIEN`, `CREDIT_LIMIT`, `NEW_MONEY`, `RENT`, `PROJECT_COST`, `TRANSFER_TAX`, `MORTGAGE_TAX`, `RECORDING_FEE`, `FILING_FEE`, `OTHER_NAMED_TAX_FEE`, `DEVELOPMENT_RIGHTS`, `COMMON_INTEREST`, `PERCENT_INTEREST`, `AREA`, `DIMENSION`, `DURATION`, `RATE`, `OTHER_NAMED`. Type from the governing label or words, never document type. **Choose the most specific governing kind: `COMMON_INTEREST` before `PERCENT_INTEREST`.** Different kinds coexist even at equal numbers.

**FR-QTY-002 — Normalization and zero.** Use D-2. Money is exact decimal with supported currency. Percent is the stated percentage, rational fractions are reduced, dimensions retain stated units. **Every affirmatively completed named numeric field creates one quantity even when no function event fires.** An affirmatively completed zero is numeric zero. **A blank field is UNKNOWN only where a module `required_when` test makes that quantity applicable; otherwise it is `EMPTY_FIELD_SEARCHED` under FR-EV-010 and emits nothing** — a blank named field on a form nobody's module asked about is a search result, not a null. `no new indebtedness` is ASSERTED_NONE for new money, not zero.

**FR-QTY-003 — Scope and allocation.** Quantity scope is `EVENT`, `STATE_OBJECT`, `PARCEL`, `PARTY_SHARE`, `INSTRUMENT_TOTAL`, or `MULTI_EVENT_TOTAL`. Determine it from exact targets in this order: one event or object → its scope; **an operative clause grammatically directing the measurement to one named party or an exact joint party set → `PARTY_SHARE` with `target_party_ids`**; more than one emitted event sharing one stated amount → `MULTI_EVENT_TOTAL`; a whole executed instrument or form with no narrower target → `INSTRUMENT_TOTAL`. Never decide scope from the word `TOTAL`. `allocation_status` is `EXPLICIT` for stated components, `DERIVED` only through D-6, `NOT_DERIVABLE` for an unallocated total over several targets, `NOT_APPLICABLE` for a single-target measurement. **Where a seller conveys a measured quantity at a stated value, the quantity and its value share one `allocation_group_id`** so the pairing survives; without it, four quantities and four values leave which-at-which underdetermined. Fan references one total; it never duplicates or divides it.

**FR-QTY-004 — Conflict and deduplication.** Coalesce exact repeated displays only when kind, value, status, scope, target, and referred object match; retain all evidence. Different kinds or scopes remain separate. Same-kind, same-scope controlling differences are a field conflict; never sum, average, or choose by plausibility.

**FR-QTY-005 `[REGISTRATION]` — Registration amount.** Retain raw `registration.amount` in `document.index_reported_amount` with semantic kind `UNKNOWN` unless a citable image label or operative text identifies what it measures. `INDEX_REPORTED_AMOUNT` is an adapter field, not a quantity kind. Instrument classification never supplies meaning. While untyped it emits no Value, Cost, or Capital event and resolves no body or form field.

**FR-TERM-001 — Module paths only.** A term record has a module-controlled `path`, value type, raw and normalized value, party, object, and scope ids when stated, and support. Emit only paths whose module `required_when` test succeeds. If required and unstated, emit UNKNOWN. Do not serialize every possible token.

**Phrase-set coverage, per FR-EV-008.** A module path whose `required_when` reads *"emit only on their phrases"* names a phrase set that is **`ASSERTED_UNMEASURED`** — the phrases were drawn from instruments read to date and no coverage over any registry has been measured. **Residue behaviour: a clause that plainly fills a path but matches no listed phrase is emitted as a `GENERIC_GAP` framework gap naming the anchor and the intended path, never silently dropped and never forced onto the nearest listed phrase.** An under-specified phrase set must fail loudly, because a term that matches nothing and is discarded leaves no symptom at all.

**FR-REF-001 — Reference classes.** Every reference carries `reference_class`: `RECORDED_INSTRUMENT`, `GOVERNING_DOCUMENT`, `STATUTE_REGULATION`, or `INCORPORATED_SECTION`. Preserve `relation_raw`, `locator_raw`, and D-9 components for all. **Only `RECORDED_INSTRUMENT` and a uniquely identified `GOVERNING_DOCUMENT` enter document-id resolution and continuity.** `STATUTE_REGULATION` is authority-only. `INCORPORATED_SECTION` follows FR-PAGE-005 and never enters external continuity. Store `resolution_status: UNRESOLVED_BY_EXTRACTION`. Never supply a target document or event id, resolve it, or import unseen contents.

**FR-NOINF-001 — Absolute exclusions.** Never infer: prior or current ownership, lien, permit, or lease status; party identity, role, share, or relationship; BBL from address or geometry; parcel adjacency, benefit, or burden; a recording, preparation, or reference date as applicable time; current balance from principal; payment from release or release from payment; a standard rate, maturity, priority, or remedy; whole-lot scope from partial or unit; the contents of an external pointer; semantic kind from registration type; or law, statute, regulation, or contract text not included.

**FR-NOINF-002 — Tax route.** Never derive consideration, price, principal, payoff, taxable amount, or value from a tax or fee using an unstated rate, and never derive a tax or fee from another amount using an unstated rate. Numerical consistency — even when the computed number is true — is not an admission rule.

<!-- BUILD:CORE §5 ASSEMBLY -->
## §5 Assembly

Read once per document, after the sweep, the support pass, and enrichment. No discovery lens loads this block.

### 5.1 Schema gate

**FR-SCHEMA-001 — Closed extraction schema.** The loaded bundle includes `extraction.schema.json` and one canonical empty template. Every output validates against that exact schema before semantic QC. Unknown keys, missing required keys, alternate aliases, JSON nulls, and enum values outside the schema fail the schema gate, make `validation.overall = FAIL`, and leave semantic checks `NOT_REACHED`. The schema fixes every nested lane, event core, support, time, registry, exception, count, and validation shape; prose may constrain semantics but may **not** rename or reshape them. The schema's own token cost counts against the loaded bundle; it is not a place to hide context.

**FR-SCHEMA-002 — Canonical field choices.** `bbl`; `directionality`; `external_reference_id`; `value`; `registration_path_inventory`; `parcel_bindings`; `participations`; support union per FR-SUP-001. Holder changes use `{remove:[{party_id,share}], add:[{party_id,share}]}`. A typed UNKNOWN is `{value:"UNKNOWN", reason:<FR-NULL-001>}`. Any applicable, valid, or occurrence interval uses one shape `{status, interval_start, interval_end, precision, basis, support}`; UNKNOWN omits interval keys and supplies `reason`.

**FR-SCHEMA-003 — Build identity.** The **build tool**, not the reader, emits `bundle_manifest`. Component extent is by declared boundary, not by file: a component runs from its heading through the line before the next heading of equal or higher level, digest over UTF-8 bytes with one trailing LF, heading line included. `bundle_sha256` is the digest of core, the selected adapter, then the selected modules **in bundle-file order**, each separated by one LF. A module nominated and not loaded is not part of the bundle and never enters the hash. Record `framework_file_sha256` alongside; it identifies the file, not the load. Every event copies `bundle_sha256`. A hand-authored manifest fails the schema gate. The extractor cannot cite hashes as document evidence.

**FR-SCHEMA-005 — Schema validation is computation, not a reading pass.** The gate runs in a conforming Draft 2020-12 validator against `extraction.schema.json`. **No model reads the schema and no pass loads it.** A model asked to validate can hallucinate a `PASS`, costs more than the validator, and is slower; the validator is deterministic and its result is checkable by re-running it. The semantic page passes therefore remain **twelve** — eleven lenses and the support pass — and the schema is not in any pass's context budget.

Assembly must still know the shape it emits. It loads `template.json`, the canonical empty instance generated from the schema, which carries every required key and enum in place with no values. **A producer that learns its shape from a post-hoc rejection is being debugged rather than specified**, and the template is what makes the closed schema usable rather than merely enforceable. `FR-SCHEMA-001` is unchanged: a gate failure makes `validation.overall = FAIL` with semantic checks `NOT_REACHED`.

**FR-SCHEMA-004 — Validation record.** `validation.checks` contains exactly eleven ordered records `{check_id, result, detail}` for `FR-QC-001` through `FR-QC-011`. `result` is `PASS`, `FAIL`, `EXCEPTION`, `NOT_APPLICABLE`, `NOT_REACHED`, or `NOT_SATISFIABLE`. Version-level gates appear with their externally supplied result or `NOT_APPLICABLE` plus reason. `counts` holds schema-fixed integer numerators and denominators; never encode a ratio as free text.

### 5.2 Envelope and lanes

**FR-REC-001 — Canonical envelope.** `extraction.json` has keys in this order:

`framework_version`, `bundle_manifest`, `document`, `page_inventory`, `function_sweep_ledger`, `coverage_ledger`, `evidence_registry`, `derivation_records`, `party_registry`, `party_relationship_registry`, `quantity_registry`, `external_reference_registry`, `incorporated_section_references`, `registration_annotations`, `evidence_time_registry`, `transactions`, `observations_dated`, `observations_unplaced`, `notices`, `conditional_events`, `temporal_boundaries`, `ordering_relations`, `exceptions`, `counts`, `validation`.

There is deliberately no single `events` array.

**FR-REC-002 — Physical lane separation.** Lanes are exclusive: `transactions` holds unconditional state acts; `observations_dated` observations with supported valid intervals; `observations_unplaced` those without one and without any date-shaped sort field; `notices` acts or claims made elsewhere; `conditional_events` condition-dependent transaction effects. Membership — not a discriminator — enforces the boundary. Observation and notice records carry an `evidence_time_registry` id, never its time; the state resolver never receives that registry.

**FR-REC-003 — Shared event core.** Every lane record contains `event_id`, `event_group_id`; `anchor_ids`, `section_ids`, `module_ids`, `bundle_sha256`; `epistemic_character` (`TRANSACTION`, `OBSERVATION`, `NOTICE`) **and** `mode` or `would_be_mode` — both axes, neither substituting for the other; `function`; `state_object_key` and `object_type`; `interest_kind`, mandatory for Title and absent otherwise; `participations`; `directionality`; `parcel_bindings`; `quantity_ids`, `terms`, `external_reference_ids`; `certainty`; `resolution_provenance`; `support`; `field_conflicts`; `document_flags`. Do not populate global placeholder fields. A module path exists only when that module's `required_when` test succeeds; a required but unstated path is UNKNOWN; a path outside the triggered schema is absent.

**FR-REC-003a — Certainty and provenance are orthogonal.** `certainty` is `SUPPORTED` or `UNKNOWN` and is **field-local**; the event-level value renders the worst field-local certainty. `resolution_provenance` is `PRIMARY` or `ADJUDICATED`. An event escalated and then resolved is both supported and adjudicated; one enum cannot carry both without hiding one, and an adjudicated event is a real output rather than a failure. `ADJUDICATED` records history and is never the semantic answer.

**FR-REC-004 — Lane-specific content.** A transaction adds `applicable_time` and an ordered `state_delta`. A dated observation adds `asserted_valid_time` and ordered `assertions`; it has no occurrence-time field. An unplaced observation adds `unplaced_reason` and `assertions`; it has no date or interval key. A notice adds `notice_claims` and raw pointer ids but no composed-state delta. A conditional event adds `would_be_mode`, ordered `would_be_delta`, and `condition` (verbatim trigger, consequence, status), but no active delta and no unconditional applicable-time key.

`state_delta` has `lifecycle_op` (`ACTIVATE`, `PRESERVE`, `DEACTIVATE`, `ASSERT_STATE`) and module-admitted field operations `{path, op, value, value_type, support}` where `op` is `SET`, `REMOVE_ASSERTED`, `NO_CHANGE`, or `UNKNOWN`. Observation `assertions` use `{path, value|ASSERTED_NONE, value_type, scope, support}` and never lifecycle operations.

**FR-REC-004a — Disjunctive value.** `DISJUNCTIVE_SET` is an ordered list of verbatim alternatives meaning *the assertion says one listed alternative holds and does not say which*. It never promotes a member to state. It differs from a set, which asserts every member, and from UNKNOWN, which has no supported content.

**FR-REC-005 — Time registries.** In source-anchor order assign `T001`… to every observation and notice and `B001`… to boundaries. Each evidence-time item has id, event id, and either a supported occurrence interval with basis and support or UNKNOWN plus reason. A boundary records id, source event, affected object, function, and parcels, type (`COMMENCEMENT`, `MATURITY`, `EXPIRATION`, `OPTION_OPEN`, `OPTION_CLOSE`, `RENEWAL_DEADLINE`, `OTHER_NAMED` plus raw label), interval, consequence, condition, and `effect_status` (`INFORMATIONAL`, or module-admitted `SELF_EXECUTING`). Self-executing boundaries add a module-admitted `boundary_delta`; informational ones cannot. A boundary is not another event.

**FR-REC-006 — Ordering relations.** In first supporting-anchor order assign `O001`…. Store `{relation_id, type, before_event_or_group_id, after_event_or_group_id, support}`; `type` is `BEFORE`, `AFTER`, or `SIMULTANEOUS`; normalize `AFTER` to the corresponding edge. Emit only when exact wording orders the present acts.

**FR-REC-007 — Stable ids.** Assemble anchors first. Sort the combined final event set by first anchor id in page and reading order, clause order within the anchor, fixed FR-FN-001 function order, object first-mention order, then mode order `CORRECT`, `TERMINATE`, `TRANSFER`, `MODIFY`, `CREATE`, `ASSERT`. Assign `EV001`… across all physical lanes. Events from one act share `G001`…, ordered by that act's first anchor. Recompute after a valid escalation merge; identical final events receive identical ids regardless of discovery order.

**FR-REC-007a — Event group boundary.** Events share one group when they arise from **one operative execution or certification act**. Function, object, or module splitting alone never creates another group. Create another group only for a separate execution or certification, a distinct present act or effect clause with its own party set or consideration, or an express separate effective act. Record the group-anchor id.

**FR-REC-008 — State-object key.** Choose the first applicable: an exact recorded identifier; an exact defined instrument-local name or unit; a D-10 link to an earlier keyed object; an identified agreement; otherwise a local first-mention ordinal. The identity component is the **exact D-2-normalized raw name**: preserve spaces, percent-escape only `%` and `:`, never slug, never append a contextual or relational suffix to make a key look unique. Relations live in keyed fields and parcel roles. Prefix the function. For Title the key contains the mandatory interest kind: `TITLE:<INTEREST_KIND>:<identity>`. Do not merge keys by similar parties, values, dates, or parcels.

**FR-REC-009 — References versus current identity.** Current recording identifiers live in `document.current_recording_identity`. A pointer to another recording lives only in `external_reference_registry`. Neither substitutes for the other.

**FR-REC-010 — Document/adapter record.** `document` contains document id, adapter id and version, exact raw registration, `registration_path_inventory`, normalized index classification, reported date, recording fact, current identity, parties, parcel inventory, reported amount, page-count reports, notarial anchor, image count, and package hash. Declared nonsemantic keys remain archived and excluded from semantic provenance.

**FR-REC-011 — Mode-to-delta map.** CREATE → `ACTIVATE`; MODIFY, TRANSFER, and CORRECT → `PRESERVE`; TERMINATE → `DEACTIVATE`; module-admitted transaction ASSERT → `ASSERT_STATE`. A conditional event applies the same mapping to `would_be_mode` inside `would_be_delta` only; it never becomes active state before matrix condition resolution.

**FR-REC-012 `[REGISTRATION]` — Registration path closure.** Each adapter begins with machine-readable `REGISTRATION_PATHS_JSON = [...]`. Inventory every path **present in the supplied registration**, and give it disposition `NORMALIZED_INDEX_FACT`, `RAW_CITABLE`, `POINTER_SOURCE`, `REGISTRY_ANNOTATION`, `DECLARED_NONSEMANTIC`, or `UNMAPPED`, with receiving path or rule. **A key present with an empty or filler value is present.** It is dispositioned `DECLARED_NONSEMANTIC` with reason `EMPTY_VALUE` or `ADAPTER_DECLARED_FILLER`, never skipped as absent — the difference between *this registry did not state it* and *this reader did not look* must survive into the output. `UNMAPPED` is a framework gap; never treat an unknown field as absent or silently nonsemantic.

**FR-REC-013 `[REGISTRATION]` — Mixed pointer or annotation paths.** An adapter may declare a path `MIXED_POINTER_OR_ANNOTATION`. Core then disposes by **content**: a value resolving to a recording locator under D-9 is `POINTER_SOURCE`; a value that does not is `REGISTRY_ANNOTATION`, stored in `registration_annotations[]` as `{source_path, raw, raw_temporal_tokens, relation_raw, semantic_status:"UNRESOLVED_REGISTRY_ANNOTATION", support}`. Do not normalize a two-digit year; do not infer a party, corrected value, act, function, event, target, applicable time, valid time, or chronology edge from it. **An adapter may not declare such a path unconditionally in either direction** — declaring every remark a pointer silently admits a pointer to a recording that does not exist, and declaring none makes a registry-side note an `UNMAPPED` failure. Undeclared paths remain `UNMAPPED`.

### 5.3 Parties

**FR-PARTY-001 — Party registry.** `party_registry[]` is `{party_id, party_kind, names[], attributes[], index_coverage_qa, support}`. **Every distinctly named person or entity receives a `party_id`**, including one named only as a representative, parent, or affiliate; orphan names referenced by string are prohibited. `party_kind` is `NATURAL_PERSON`, `ORGANIZATION`, `GOVERNMENT`, `TRUST`, `ESTATE`, or `UNKNOWN`, set only per FR-EV-009.

`names[]` holds exactly one `PRIMARY_AS_WRITTEN` plus only textually labelled `DBA`, `FORMER_NAME`, `AKA`, `TRADE_NAME`, or `OTHER_STATED`, each `{name_kind, name_raw, name_normalized, source_class, support}`. **A related company is never promoted to a name variant.**

`attributes[]` is a **closed** `oneOf`, never a general bag: `ADDRESS` `{address_use, use_raw?, value_raw, components?, source_class, support}` with `address_use` in `MAILING`, `RESIDENCE`, `NOTICE`, `BUSINESS`, `REGISTERED_OFFICE`, `UNSPECIFIED`, and components `street_raw`, `unit_raw`, `city_raw`, `state_raw`, `postal_code_raw`, `country_raw` each absent when not textually separable; `PHONE` and `EMAIL` with raw value, optional mechanically normalized value, source class, support; `ENTITY_FORM` with raw and closed normalized form. There is no catch-all member: a new semantic class must extend the schema, not pass closure silently.

`source_class` is `INSTRUMENT_STATED`, `VISIBLE_COVER`, or `REGISTRATION_INDEX`. **Support proves location; source_class states what kind of claim it is.** Identical values from two classes remain two records and never merge or overwrite. *"with addresses at"* is `UNSPECIFIED`; *"residing at"* is `RESIDENCE`. Unstated attributes are absent, not UNKNOWN.

**FR-PARTY-007 — Relationship registry.** `party_relationship_registry[]` is `{relationship_id, subject_party_id, predicate, object_party_id, relation_raw, source_class, support}`. Predicates are directional and closed: `PARENT_OF`, `SUBSIDIARY_OF`, `AFFILIATE_OF`, `MANAGER_OF`, `MEMBER_OF`, `OFFICER_OF`, `SIGNATORY_FOR`, `AGENT_FOR`, `TRUSTEE_OF`, `NOMINEE_FOR`, `OTHER_STATED`, normalized only by the adapter's closed phrase table. `OTHER_STATED` preserves the raw edge and **never merges identities**. Capturing a stated relation is not asserting the parties are the same person, and FR-PARTY-002 continues to forbid turning affiliate or officer language into identity. **Event participation determines operative status; registry membership does not.**

**FR-PARTY-008 — Participation.** Role, capacity, and share are properties of an **event**, not of a person. Event `participations[]` is `{party_id, role_raw, module_role, capacity_raw?, share?, support}`. The same entity may be grantor, grantee, affiant, and representative in one document. **Every signed or certified assertion includes each person or entity expressly making or certifying it**, with exact role and support; non-directional does not mean partyless. Being named as subject, buyer, or seller does not make a party an affiant unless form grammar says so.

**FR-PARTY-004 — Index coverage QA.** The adapter declares its comparator **capability set**: the party attributes the registry can be compared on — for example `{name, role, address}`, `{name, role}`, `{name}`, or the empty set. For each declared attribute the result is `CONFIRMED`, `DISCREPANCY` with the exact delta, or `NOT_CHECKABLE`. **A declared-comparable attribute with no value on this row is `NOT_CHECKABLE`, and an attribute outside the capability set is always `NOT_CHECKABLE`** — never a silent pass. An empty capability set is `NO_COMPARATOR`. This is QA only; it never creates or merges a party or overwrites a role. It exists because a registry that supplies names but no roles renders a verified role and an unverifiable one identically, and a reversed grantor/grantee on such a registry has no symptom.

### 5.4 Coverage, conflict, findings

**FR-COV-001 — Sections from anchors.** Final sections are the FR-ANC-002 snapped union of every lens anchor and every FR-DOC-002 residual. Assign `S001`… in page and reading order. A section stores page, controlled zone, occurrence ordinal, class, legibility, `encoded_resolution`, and its anchor id.

**FR-COV-002 — One disposition.** Every section has exactly one: `EVENT` with event ids; `VALUES_ONLY` with receiving registry or event paths; `REFERENCE_ONLY` with reference ids; `SUPPORT_ONLY` with receiving registry paths; `NO_EVENT` with one reason from `ADMINISTRATIVE`, `BLANK`, `SIGNATURE_ONLY`, `ACKNOWLEDGMENT_ONLY`, `NOTICE_ADDRESS`, `DEFINITION_ONLY`, `HISTORICAL_RECITAL_ONLY`, `BOILERPLATE_EXCLUDED`, `DUPLICATE_DISPLAY`, `NO_LENS_CLAIM`, or `OTHER_RULED` plus rule id; or `UNRESOLVED_SECTION`, which can never accompany validation `PASS`.

**FR-COV-003 — Coverage closure.** `PASS` requires: eleven sweep cells for every supplied page plus the support pass; every `HIT` and `UNCERTAIN` mapped to a final path, finding, or escalation; every residual dispositioned; every emitted record linked to an anchor and section; and every section appearing once. A zero-event document requires all lens searches **completed**, not merely a set of no-event sections. Count pages, sections, dispositions by reason, unresolved sections, emitted fields and events, flags, illegible fields, sweep cells by status, and escalation outcome. **This proves eleven completion records exist. It does not prove the reader inspected faithfully** — only frozen fresh-context fixtures test that, exactly as D-1's ordering claim is not provable from output.

**FR-COV-004 — Sweep conflict.** Two lens outputs claiming **mutually exclusive** classification, object, or attachment for one anchor are `SWEEP_CONFLICT`. Deterministic boundary rules decide; otherwise route to `RULE_BRANCH_CANDIDATES` or visual-attachment escalation. **Never resolve by vote.** A legitimate multi-function hit — one clause filling Title and Encumbrance paths — is **not** a conflict; it is FR-PKG-001a. Discovery candidates are not events: merge exact within-function duplicates only after source-authority and dedup tests, **never merge across functions**, and link one act by `event_group_id` with shared parties and quantities carried as registry ids rather than copied facts.

**FR-COV-005 — Boundary orphan.** A **candidate claim** carrying at least one `EXCLUDED_BY_BOUNDARY` and no resolving disposition is a `BOUNDARY_ORPHAN` finding, keyed by its FR-SWP-009 `candidate_claim_id`. All three resolution tests are exhaustive and each names what it checked: **`EVENT_HIT`** with the event ids examined, **`SUPPORT_RECEIVING_PATH`** with the paths examined, **`NAMED_NO_EVENT_RULE`** with the rule ids examined. An orphan exists only when all three return `ABSENT`.

Store the resolution link, not an anchor-level status — an anchor-level condition falsely indicts correct zero-event support, where an authority or capacity anchor legitimately resolves as `SUPPORT_ONLY` into a receiving path. Every lens can decline a claim for a principled reason and leave nothing holding it; eleven lenses make unanimous decline more likely than one pass did, and each individual ledger row remains well-formed while the content vanishes.

**FR-AMB-001 — Separate outcomes.** Keep distinct: document ambiguity or conflict; image illegibility; a genuinely unstated value; unplaced function, BBL, or transaction time; framework or schema gap; input integrity failure; model validation failure; and escalation. Never relabel one as another.

**FR-AMB-002 — Document finding.** A final document flag requires two or more evidence-supported readings of the same controlling field after scope, kind, rank, and correction tests and, where eligible, both reader tiers. Framework silence, difficulty, commercial oddity, a lower-rank discrepancy, or missing text is not a document flag.

**FR-AMB-003 — Placement.** A readable competing function, BBL, or transaction applicable-time reading is an escalation candidate. A genuinely absent BBL or time remains a cited exception and makes state-chronology status non-PASS. A framework gap blocks the bundle version; it is neither escalation nor a document flag. Unknown observation valid time correctly routed to its unplaced lane does not by itself fail extraction QC.

**FR-AMB-004 — Closed final finding codes.** `document_flags` uses only `AMBIGUOUS_GLYPH`, `AMBIGUOUS_GRAMMAR`, or `CONFLICTING_CONTROLLING_EVIDENCE`, each with candidates and proof. Final unreadability without two document readings is `exceptions.ILLEGIBLE_FINAL`. Framework, input, and model failures use their own exception classes. No free-text uncertainty flag is allowed.

`exceptions` separates `framework_gaps` (bundle defect), `unclassifiable_content` (a supplied readable passage with no admitted result), `incorporated_sections_not_supplied`, `registration_annotations`, `boundary_orphans`, `illegible_final`, `unplaced_parcel`, and `input_failures`. Each carries exact source ids and one owner class.

### 5.5 Escalation

**FR-ESC-001 — Route, not answer.** The primary produces a complete provisional extraction and ledger. Escalation is operational sidecar metadata carried in `routing.json`, not in `extraction.json`; the extraction retains only an opaque routing id, status, and `resolution_provenance`. In a blind round with no heavy pass, mark `PENDING_HEAVY` and do not call the provisional file final.

**FR-ESC-002 — Closed triggers.** Escalate the document once if at least one record passes exactly one test: (1) `VISUAL_CANDIDATES` — after reread and D-1, at least two graphic transcriptions remain and change a semantic, placement, or coverage output; (2) `VISUAL_ATTACHMENT_CANDIDATES` — two plausible termini for a leader, insertion, or annotation produce different anchor or party links; (3) `RULE_BRANCH_CANDIDATES` — one cited passage contains discriminating words for two existing rule branches, attachment cannot be resolved, and both complete candidate outputs differ; (4) `MODEL_VALIDATION_FAILURE`; (5) `CONTEXT_LINK_FAILURE`. Do not escalate `NOT_STATED`, a genuinely absent date or BBL, an unallocatable total, a clear same-rank document conflict, a framework gap, a missing image, or *this is hard*.

**FR-ESC-002a — Attachment is geometry only.** A heavy adjudication of `VISUAL_ATTACHMENT_CANDIDATES` decides **where a mark points**, nothing else. A resolved terminus does not prove adoption or operative effect; FR-PAGE-006 continues to control whether any field may be filled. An unadopted annotation may be linked and preserved without becoming operative.

**FR-ESC-003 — Immutable payload.** Carry document id; input hashes; adapter, framework, and module ids, versions, and bundle hash; provisional extraction, ledger, validation, and candidate diff; trigger; affected paths, anchors, and rules; all candidates and evidence; relevant pages and lossless crops, **all pages for context**; and the replaceable-path allowlist. Exclude slate, other documents, parcel history, resolved pointers, lookups, and unstated law.

**FR-ESC-004 — Heavy task.** Apply the identical frozen bundle to identical inputs and adjudicate each trigger as `RESOLVED`, `DOCUMENT_AMBIGUITY`, `INSUFFICIENT_EVIDENCE`, or `INVALID_TRIGGER`. Return replacements only inside the allowlist with quote or rule closure. **The heavy task replaces only the triggering lens, path, or section allowlist; all other primary results freeze.** Do not change rules, use outside information, resolve pointers, edit unrelated paths, or escalate again.

**FR-ESC-005 — Merge-back.** Validate scope, schema, provenance, coverage, and QC; merge allowed replacements; recompute registries, ids, links, and serialization — never patch a matrix. Ambiguity or insufficient evidence becomes its final null, candidates, or finding, with `resolution_provenance: ADJUDICATED`. An invalid trigger retains the conforming primary answer and records a false escalation.

**FR-ESC-006 — Telemetry.** Version-gate rule; see §7.

### 5.6 Validation

**FR-QC-001 — Input coverage closure.** Every supplied image and section passes FR-COV-003; package sequence is intact; page-count reports do not become inventory; every present registration path has one FR-REC-012 disposition and no `UNMAPPED` path remains.

**FR-QC-002 — Provenance closure.** Recursively walk every semantic leaf and sentinel. Each ends in a proving quote or a loaded rule with supported inputs. Run FR-EV-002 semantic proof, not substring presence.

**FR-QC-003 — Lane firewall.** Reject a single events array, mixed lane content, occurrence time in dated observations, any date-shaped unplaced-observation field, an evidence-time state input, a notice delta, or an active conditional delta.

**FR-QC-004 — Title object safety.** Every Title event, key, and object has a supported `interest_kind`; fee and leasehold keys are distinct; no serialized holder list exists outside an interest-kind map. Failure invokes the R-1 inversion and must be reported, not repaired silently.

**FR-QC-005 — Placement and coverage.** Every resolved transaction has one function, at least one exact BBL/scope binding, and an applicable-time status. Dated observations have function, binding, and asserted-valid interval. No event fans from parcel inventory alone.

**FR-QC-006 — Conservation and linkage.** Every event links anchors and sections; every quantity, pointer, party, and relationship id resolves once; no quantity is duplicated through fan; event groups arise from one act; ordering and boundary links resolve; no external pointer has a resolved target.

**FR-QC-007 — Module and schema closure.** Every state, assertion, and term path is defined by a loaded module with matching function, lane, mode, value type, `required_when`, and merge behaviour. Unknown required paths are explicit; out-of-schema paths are absent. A module never fires from a registration name alone.

**FR-QC-008 — Trigger-frequency audit.** Version-gate rule; see §7.

**FR-QC-009 — Scoped outcome.** Every non-PASS finding carries `failure_scope` — `DOCUMENT`, `REGISTRATION_PATH`, `SECTION`, `EVENT_GROUP`, `EVENT`, or `FIELD` — and the exact affected ids. `validation.overall` is `PASS`, `EXCEPTION`, or `FAIL`. **`FAIL` is reserved for integrity, schema, provenance, or model failures whose semantic effect cannot be bounded.** A completely bounded finding is `EXCEPTION`: exclude its affected records and preserve every independent record. A framework gap remains loud and blocks the affected bundle path or group, but does not become document-wide merely by being a framework gap. An unknown field whose effect cannot be bounded remains `FAIL`.

**FR-QC-010 — Frozen runs.** Version-gate rule; see §7.

**FR-QC-011 — Referent-shift finder.** Version-gate rule; see §7.

**FR-SER-003 — Follow fixed rules.** When a rule appears wrong, emit its result and record the objection outside committed extraction. Never silently repair the framework. A failed validation remains deliverable with named failures; do not invent a value to obtain PASS.

<!-- BUILD:CORE §7 VERSION GATE -->
## §7 Version gate

`version-gate.md` is part of this release and is **binding, not advisory**. A release without a completed, recorded gate run is invalid. It contains `FR-QC-008` (trigger-frequency audit), `FR-QC-010` (frozen fresh-context runs), `FR-QC-011` (referent-shift finder), and `FR-ESC-006` (escalation telemetry). These are cross-document by construction — a per-version frequency audit, a fixture rerun, an `n≥200`-per-cell finder, and a rate cap — so no single-document run can execute any of them in any registry; each appears in `validation.checks` as `NOT_APPLICABLE` with reason.

**FR-QC-008a — Conditional stratification.** The year-band cross-tab in `FR-QC-008` applies **only where the frame contains more than one recorded-year band for that registry**, and otherwise reports `NOT_SATISFIABLE` with the observed band count. A binding gate containing a check that cannot pass either blocks every release or is waived by habit, and a habitually waived check is how a gate stops being read.

<!-- BUILD:CORE §6 LOADING AND ADAPTERS -->
## §6 Loading and adapters

Read at load and at registration processing. Registration is not a page: **no block in §6 ever enters a sweep pass.**

**FR-LOAD-001 — Marked bundle.** Load §0–§5 and the one FR-LOAD-002 adapter. Inventory pages, run the sweep, then nominate modules from lens hits, adapter classification, visible self-title, headings, and operative verb/object pairs; load every content-confirmed trigger. Registration type only nominates. Hybrids load several modules. A late trigger requires loading it, updating the manifest, and rerunning enrichment for the affected `(function, module)` pairs — **never rerunning discovery, which is module-independent by FR-SWP-001.**

**FR-LOAD-002 — Adapter selection.** Select by document-id namespace only: prefix `RC_` → `RICHMOND`; `FT_` → `FILM_FT`; `BK_` → `FILM_BK`; all-decimal id → `ACRIS_DIGITAL`. Any other namespace is `FRAMEWORK_GAP`; do not guess an adapter.

**FR-LOAD-003 — Module manifest.**

| module | load when a visible clause or form expressly concerns |
|---|---|
| `ESTATE_IDENTITY` | parcel or unit identity; possessory fee, leasehold, subleasehold, common, life, or other estate |
| `SECURED_FINANCE` | debt or credit; security, rents or proceeds, UCC, priority, assignment, release, satisfaction, modification |
| `LAND_RIGHTS` | easement, covenant, restriction; development, air, or subterranean right, zoning-lot relation, form constraint, private land-use privilege |
| `PUBLIC_PHYSICAL` | government permit or approval; occupancy, survey, completion, installed item, present condition or use |
| `ECONOMICS` | consideration or value, project expenditure, tax, filing or recording fee |
| `NOTICE_AUTHORITY` | notice of an elsewhere-made act, authority-only material, raw cross-document pointer |
| `GENERIC_GAP` | a lens returned `HIT` and no other loaded module admits a receiving path |

The trigger is the stated act or object, never an instrument-type name. `GENERIC_GAP` cannot invent paths. **A `HIT` with no receiving module is exactly its trigger** — under the ungated sweep this fires on content a nomination-driven read would never have looked for.

**FR-LOAD-004 — Execution order.** Adapter → page inventory → **eleven ungated discovery lenses, isolated** → `DOCUMENT_SUPPORT` pass with visual-residual inventory and backfill → anchor union and snapping → module confirmation from hits → batched `(function, module)` enrichment → assembly, registries, stable ids → escalation if admitted → merge-back → QC → canonical serialization. Matrix resolution is a later phase governed by `matrix-spec.md`; no extractor decision may depend on a rule found only there.

**FR-LOAD-005 — Vocabulary drift.** Adapters use per-label historical alias maps, never one modern lookup or a registry-wide cutover. Unknown or broad labels nominate nothing but cannot suppress content discovery. Label era never changes clause confirmation.

**FR-ADP-001 — Adapter declaration contract.** Every adapter declares: `REGISTRATION_PATHS_JSON`; per-path disposition or `MIXED_POINTER_OR_ANNOTATION`; a **filler value set per path**; a **comparator capability set**; and a closed legal-designator table. A filler declaration removes data with no downstream symptom — a deleted value leaves no gap, no exception, and no `NOT_CHECKABLE` — so each filler set carries its evidence inline as observed distribution and `n`, or is marked `ASSERTED_UNMEASURED`. **Filler is a property of the value at a path, never of the path**: a set of `{"00000"}` says nothing about a `US` or a zip appearing anywhere else, and any value outside the set is a stated attribute. Per FR-EV-008, state the residue.

**Closed legal-designator table** (all adapters): `ORGANIZATION` on exact token `LLC`, `L.L.C.`, `INC`, `INC.`, `CORP`, `CORP.`, `CORPORATION`, `COMPANY`, `CO.`, `LP`, `L.P.`, `LLP`, `LTD`, `N.A.`, `ASSOCIATION`, `PARTNERSHIP`; `TRUST` on `TRUST`, `TRUSTEE OF`; `ESTATE` on `ESTATE OF`; `GOVERNMENT` on `CITY OF`, `STATE OF`, `COUNTY OF`, `DEPARTMENT OF`, `AUTHORITY`, `AGENCY`. `NATURAL_PERSON` only on an exact grammatical label — `residing at`, `his wife`, `individually`, `an individual`. Name shape never decides.

**Coverage: `ASSERTED_UNMEASURED`.** These tokens were selected from instruments read in round 1 and from general form vocabulary; no frequency over any registry has been measured. **Residue behaviour, per FR-EV-008: a name matching no token yields `party_kind: UNKNOWN` and is emitted in full with every attribute intact.** No name is dropped, suppressed, or classified by shape, and an unmatched designator is not a finding. Measuring this table's coverage is a version-gate obligation under `FR-QC-008`.

<!-- BUILD:ADAPTER ACRIS_DIGITAL -->
## Adapter ACRIS_DIGITAL

REGISTRATION_PATHS_JSON = ["amount","at","borough","collateral","crfn","doc_date","expiration","pages","parcels","parcels[].address","parcels[].air_rights","parcels[].bbl","parcels[].easement","parcels[].partial","parcels[].subterranean","parcels[].unit","parcels[].use","parties","parties[].address","parties[].address2","parties[].city","parties[].country","parties[].name","parties[].panel","parties[].state","parties[].zip","pct","recorded","references","references[].borough","references[].crfn","references[].doc_id","references[].file_nbr","remarks","type"]

**AD-ACRIS-001 — Shape.** Apply FR-REC-012; ACRIS fields are type-conditional, so inventory every present path and normalize only declared ones. Declared paths include raw `type`, `doc_date`, `crfn`, `recorded`, `borough`, `amount`, panel-indexed parties, parcels carrying `bbl`/`partial`/`use`/`address`/`unit`, `expiration`, `collateral`, and `references[]`. `type` nominates only. Panels never determine role. `doc_date` follows FR-DATE-008; `recorded` is a recording fact. `crfn` and any explicitly current file number identify the current recording. `expiration` and `collateral` are index-reported facts with referent and scope UNKNOWN unless allowed evidence identifies them; they trigger no event alone. `amount` follows FR-QTY-005; `pages` is a count report; `at` is nonsemantic.

Image-cover indexing fields outrank registration for the same index fact. Probe each `references[]` item independently for `doc_id`, `crfn`, `file_nbr`, and `borough`; preserve every found component and treat any absent form as normal. `CROSS REFERENCE DATA` is a pointer source through D-9. **`remarks` is `MIXED_POINTER_OR_ANNOTATION`** under FR-REC-013. A present `pct` creates a mandatory image-search candidate for party or estate share and nominates ESTATE_IDENTITY, but remains index-reported with referent UNKNOWN until exact image proof. Parcel `air_rights`/`subterranean`/`easement` flags nominate LAND_RIGHTS review but supply no event, role, direction, or scope without image proof. Do not interpret normalized type as cover or body wording.

**AD-ACRIS-002 — Comparator and filler.** Capability set `{name, role, address}` — `parties[].panel` is not a role and does not enter it; role comparability comes from body-delegated cover labels only, and where absent the result is `NOT_CHECKABLE`. Filler sets: none declared; `ASSERTED_UNMEASURED`. Party addresses are index metadata and enter `party_registry.attributes[]` with `source_class: REGISTRATION_INDEX`, never merged with an `INSTRUMENT_STATED` address.

<!-- BUILD:ADAPTER RICHMOND -->
## Adapter RICHMOND

REGISTRATION_PATHS_JSON = ["amount","at","book","doc_type","image_state","instrument","page","parcels","parcels[].bbl","parties","parties[].column","parties[].company","parties[].name","parties[].person","parties[].role","recorded","status"]

**AD-RICH-001 — Shape.** Normalize `doc_type`, `recorded`, parties and any nonblank indexed `role`, bare parcel BBLs, `book`, `page`, and `instrument`. `amount` follows FR-QTY-005. **Registration has no `pages` or `doc_date`**; a visible County Clerk cover Document Date is image evidence only. Indexed roles remain `indexed_role`; body grammar controls operative role. An empty `parties` array is `NO_INDEX_PARTIES`, never ASSERTED_NONE or completeness — extract every party from images. `column` and `person`/`company` are index metadata, not role or entity proof. Bare BBL extent is UNKNOWN under FR-BBL-004. Missing unit, address, or use is missing schema data, not NOT_APPLICABLE. `image_state`, `status`, and `at` are nonsemantic; `at` is pipeline scrape time and cannot enter any time lane.

**`book`/`page`/`instrument` identify the current recorded instrument.** Richmond **`page` is a locator paired with `book`, never a page-count extent** — unlike ACRIS `pages`, which is an extent report; the two keys are different referents and this distinction must not be compressed away. `page: ""` means the locator is unstated and supplies no extent; it is a present path under FR-REC-012 and is dispositioned, never skipped. These fields become an external reference only when an exact field, remark, or body label presents a distinct referenced instrument. Never use an inferred borough.

**AD-RICH-002 — Per-label historical nomination.** Preserve raw `doc_type` and map only the proven label pairs below; accept both columns in every year because each label has its own history and no registry-wide cutover is admitted.

| act family | legacy label | later label | nominated module |
|---|---|---|---|
| conveyance | `DEED` | `DEED` | ESTATE_IDENTITY |
| mortgage satisfaction | `SAT` | `SATISFACTION OF MORTGAGE` | SECURED_FINANCE |
| mortgage assignment | `A/MTG` | `ASSIGNMENT OF MORTGAGE` | SECURED_FINANCE |
| mortgage release candidate | `REL` | `RELEASE OF MORTGAGE` | SECURED_FINANCE |

Other literal labels nominate only their visible act family (`MORTGAGE`, `LEASE`, `A/LEASE`, `EASEMENT`, `AFFIDAVIT`, `NOTICE`, `UCC`, `AGREEMENTS`, `ORDER`). Broad `AGREEMENTS`/`ORDER` nominates no module; the sweep decides. `REL` remains a candidate, not proof that the release concerns a mortgage. Pre-1960 `DEED` remains valid.

**Coverage: `ASSERTED_UNMEASURED`.** The four proven pairs and the additional literals are the labels observed to date; no proportion of Richmond rows carrying them has been measured, and the residue is not known to be small. **Residue behaviour, per FR-EV-008: an unmatched `doc_type` nominates no module, is preserved raw, and suppresses nothing.** The eleven lenses run regardless — nomination is not a gate on discovery — so an unknown label costs a module load, never a search. Unknown labels never produce zero-event results by themselves.

**AD-RICH-003 — Comparator and filler.** Capability set `{name, role}`. No `remarks` path exists, so no `MIXED_POINTER_OR_ANNOTATION` declaration applies. Filler sets: none declared; `ASSERTED_UNMEASURED`. An empty `parties` array yields capability `NO_COMPARATOR` for that row.

<!-- BUILD:ADAPTER FILM_FT -->
## Adapter FILM_FT

REGISTRATION_PATHS_JSON = ["amount","at","borough","doc_date","file_nbr","map_seq","pages","parcels","parcels[].address","parcels[].bbl","parcels[].partial","parcels[].remarks","parcels[].use","parties","parties[].address","parties[].city","parties[].country","parties[].name","parties[].panel","parties[].state","parties[].zip","recorded","reel_page","references","references[].doc_id","remarks","rptt","type"]

**AD-FT-001 — Shape.** Normalize declared `type`, `recorded`, `borough`, `map_seq`, `reel_page`, parties, and parcel index fields. Optional `doc_date` follows FR-DATE-008; `amount` follows FR-QTY-005; `pages` is a count report. `rptt`, party addresses, and parcel remarks are index reports with referent UNKNOWN unless image proof identifies them. `reel_page` and an explicitly current `file_nbr` identify the current recording. `references[].doc_id` is a pointer source through D-9. **Top-level `remarks` and `parcels[].remarks` are `MIXED_POINTER_OR_ANNOTATION`** under FR-REC-013 — they are *not* unconditionally pointer sources; a non-locator remark admitted as a pointer manufactures a reference to a recording that does not exist and passes validation silently. No cover is assumed. Parcel `use: PRE-ACRIS` is a source marker, never property use or Occupancy. `at` is nonsemantic.

**AD-FT-002 — Comparator and filler.** Capability set `{name}`. **There is no `role` key in a FILM_FT party object**, so every role claim on this registry is `NOT_CHECKABLE` under FR-PARTY-004 — a reversed grantor and grantee here has no index symptom. Filler sets: `parties[].zip ∈ {"00000","00000-0000"}` — observed distribution `n=7,120`, `99.86%` covered, residue is 23 real postal codes which are stated attributes and are **not** removed; `parties[].country ∈ {"US"}` — `n=7,120`, `100%`, invariant because the pipeline writes it, so a foreign party's country would be asserted wrongly rather than merely absent. A value outside either set is a stated attribute.

<!-- BUILD:ADAPTER FILM_BK -->
## Adapter FILM_BK

REGISTRATION_PATHS_JSON = ["amount","at","borough","doc_date","map_seq","pages","parcels","parcels[].bbl","parcels[].partial","parcels[].use","parties","parties[].name","parties[].panel","recorded","reel_page","remarks","type"]

**AD-BK-001 — Shape.** `FILM_BK` loads `AD-FT-001` as its shared adapter base together with this clause; the registration pass holds both. Apply AD-FT-001 for the paths declared here. `doc_date` follows FR-DATE-008 and never automatically supplies applicable time. Normalize current book, reel, and map identifiers from raw fields. **Top-level `remarks` is `MIXED_POINTER_OR_ANNOTATION`**: a remark such as `D BOOK/PAGES: 156/36` resolves to a locator and is a raw unresolved pointer, while a remark that does not resolve is a registry annotation. No cover is assumed; `PRE-ACRIS` remains non-occupancy metadata.

**AD-BK-002 — Comparator and filler.** Capability set `{name}`; no `role` key exists. Filler sets: none declared; `ASSERTED_UNMEASURED`.

<!-- BUILD:MODULE ESTATE_IDENTITY -->
## Module ESTATE_IDENTITY

Owns Identity and Title paths for parcel identity and possessory estates.

**FR-EST-001 — Identity acts.** Routine premises recitals never fill Identity. Emit Identity only for express creation, merger, apportionment, subdivision, renumbering, supersession, correction, or present certification of a formal parcel, unit, or zoning-lot composition or designation.

**FR-EST-002 — Estate acts.** Fee, condominium, common, life, leasehold, subleasehold estate creation, conveyance, assignment, surrender, correction, and termination fill Title. Choose supported `interest_kind`: `FEE`, `CONDOMINIUM_UNIT`, `COMMON_INTEREST`, `LIFE_ESTATE`, `REMAINDER`, `LEASEHOLD`, `SUBLEASEHOLD`, `UNDIVIDED_SHARE`, or `OTHER_NAMED` plus raw estate words. Never default to FEE from a deed label.

**FR-EST-003 — Lease branching.** `leases/demises` creating possessory premises → Title CREATE; transfer of the continuing tenant interest → Title TRANSFER; surrender or whole termination → Title TERMINATE; amendment → Title MODIFY. A memorandum stating a lease was made elsewhere → Title NOTICE/ASSERT. An assignment offered as collateral or an assignment of rents triggers SECURED_FINANCE instead; an independently worded covenant burdening the fee also triggers LAND_RIGHTS.

**FR-EST-004 — Concurrent objects.** A leasehold without its own indexed BBL is placed under FR-FN-004 on the affected fee BBL under a `TITLE:LEASEHOLD:` key. A separately identified sublease, fee, common interest, or unit uses another key. **A separately keyed common interest and the parent unit's `title.appurtenant_interests` link are cumulative.** Title holder extraction is invalid without interest kind.

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `identity.designations` | Identity; transaction/observation | set of typed raw/canonical designations | formal designation asserted or changed | set union; correction targets one member |
| `identity.existence_status` | Identity; create/modify/correct/assert | `CREATED`, `MERGED`, `APPORTIONED`, `RENUMBERED`, `SUPERSEDED`, `ASSERTED_EXISTS`, UNKNOWN | the act states one status branch | scalar conflict on unordered differences |
| `identity.composition` | Identity; create/modify/assert | set of BBL/unit ids | composition is the act | exact affected set; never inventory union |
| `identity.former_designation`, `identity.new_designation` | Identity; modify/correct | typed designation | former/new grammar appears | paired scalar |
| `title.estate_label` | Title; all | raw named estate | every Title event | immutable after create except express correction |
| `title.holders` | Title; transaction | interest ledger `{party_id, share}` | create/transfer/terminate changes a holder | ledger operation; no estate-blind aggregate |
| `title.reservations`, `title.exceptions` | Title; transaction | supported term sets | reservation or exception is operative | set union or targeted correction |
| `title.appurtenant_interests` | Title; transaction | keyed interest records | common, exclusive-use, or appurtenant interest changes | object-keyed map |
| `title.lease.premises` | Title LEASEHOLD/SUBLEASEHOLD | parcel/scope set | lease estate created or asserted | replace only on express amendment |
| `title.possession_statement` | Title; observation/transaction assert | typed raw statement | present possession expressly stated | assertion layer unless legally established |

Required term paths emit only on their phrases: raw or set `title.tenancy_raw`, `title.covenant_raw`, `title.lease.permitted_use`; id sets `title.consideration_quantity_ids`, `title.subject_to_pointer_ids`, `title.lease.rent_quantity_ids`; quantity id `title.lease.security_deposit`; structured terms `title.lease.assignment_consent`, `title.lease.subletting_consent`, `title.lease.renewal_option`, `title.lease.purchase_option`, `title.lease.termination_option`, `title.lease.default_remedy`, `title.assumption`. Missing rent is UNKNOWN only when the lease text says rent exists but omits it.

Promote supported lease commencement, expiration, option windows, renewal deadlines, and termination dates as boundaries. `SELF_EXECUTING` requires exact automatic-effect words and no unresolved condition.

<!-- BUILD:MODULE SECURED_FINANCE -->
## Module SECURED_FINANCE

**FR-FIN-001 — Independent layer test.** For each clause, identify whether it acts on collateral security, on a monetary obligation, or on both. Emit Encumbrance and Capital separately only for stated effects. One shared principal may be referenced by both without duplication.

**FR-FIN-002 — Lifecycle.** Security creation → Encumbrance CREATE; debt or facility creation → Capital CREATE. Assignment transfers only the layer expressly assigned. Priority or subordination without holder transfer → Encumbrance MODIFY. Partial collateral or debt release → scoped MODIFY. Whole lien or filing release → Encumbrance TERMINATE. Capital TERMINATE requires express payment, cancellation, forgiveness, discharge, or termination. UCC termination never proves debt payment.

**FR-FIN-003 — Notice filings.** A UCC form, memorandum, or notice whose underlying security agreement is not supplied creates a NOTICE/ASSERT of an Encumbrance claim or filing, not a transaction CREATE. Capture the initial file number and external pointers. The recording timestamp supplies no applicable time.

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `encumbrance.security_kind` | Encumbrance; all | `MORTGAGE_LIEN`, `UCC_FIXTURE`, `ASSIGNMENT_OF_RENTS`, `OTHER_SECURITY` | security path fires | immutable named kind |
| `encumbrance.holders` | Encumbrance; transaction | interest ledger | holder granted, transferred, released | ledger operation |
| `encumbrance.collateral_scope` | Encumbrance; transaction/notice | typed parcel/property description | collateral identified | scoped set; partial release targets member |
| `encumbrance.priority` | Encumbrance; transaction/observation | raw relation plus object refs | priority or subordination stated | relation set |
| `encumbrance.rents_proceeds` | Encumbrance; transaction/notice | typed security scope | rents or proceeds are collateral | set union or targeted release |
| `capital.obligation_kind` | Capital; transaction/observation | `MORTGAGE_DEBT`, `NOTE_DEBT`, `CREDIT_FACILITY`, `FUNDING_COMMITMENT`, `EQUITY_COMMITMENT`, `OTHER_NAMED` | obligation path fires | immutable except correction |
| `capital.obligors`, `capital.obligees` | Capital; transaction | party-interest ledgers | parties owe, are owed, or transfer obligation | ledger operation |
| `capital.original_principal`, `capital.current_balance`, `capital.payoff`, `capital.maximum_lien`, `capital.credit_limit`, `capital.new_money` | Capital; transaction/observation | quantity id | governing words type the amount | distinct scalar paths; never copy among them |
| `capital.rate`, `capital.rate_type`, `capital.rate_index`, `capital.rate_margin` | Capital; transaction | exact quantity/enum/raw term | clause states that term | targeted replacement |
| `capital.payment`, `capital.advance_right`, `capital.readvance_right`, `capital.prepayment`, `capital.default`, `capital.guaranty` | Capital; transaction | typed term | exact obligation phrase occurs | object/path merge |

Promote maturity, rate-reset, payment-start, advance-window, and commitment-expiration dates. Maturity and filing lapse are always informational unless exact automatic state-effect words say otherwise. A statement that a mortgage `has not been assigned` is an Encumbrance observation of assignment-history absence with its exact scope; a blank prior-assignment field says nothing. An original principal recited only to identify a referenced mortgage stays on the external-reference record.

<!-- BUILD:MODULE LAND_RIGHTS -->
## Module LAND_RIGHTS

**FR-LAND-001 — Function split.** For a private easement, covenant, or restriction, fill Encumbrance. Add Envelope for a legal constraint on physical mass, placement, facade, or form; no number is required. Add Entitlement for a granted, transferred, or reserved nonpossessory development capacity or land-use privilege. Do not add Title unless possessory-estate words separately trigger ESTATE_IDENTITY.

**FR-LAND-002 — Government/private boundary.** Naming an application, agency, regulation, or desired approval is a term or reference. A government grant of land-use capacity may fill Entitlement. Permit requires the PUBLIC_PHYSICAL test. **Private residential or commercial use limits are Encumbrance, not Occupancy**, and a locally stated use restriction is its own keyed object unless exact D-10 language makes it a field of an already keyed covenant.

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `entitlement.right_kind` | Entitlement; all | `DEVELOPMENT_RIGHT`, `AIR_RIGHT`, `SUBTERRANEAN_RIGHT`, `LAND_USE_AUTHORIZATION`, `LICENSE`, `OPTION`, `OTHER_NAMED` | nonpossessory right acted or asserted | immutable named kind |
| `entitlement.holders` | Entitlement; transaction | interest ledger | grant, transfer, or reservation names holder | ledger operation |
| `entitlement.capacity` | Entitlement; transaction/observation | quantity/set | capacity is quantified | scoped scalar or set |
| `entitlement.authority_or_source` | Entitlement; transaction/observation | party/id/raw reference | source expressly named | set of supported records |
| `envelope.constraint_kind` | Envelope; transaction/observation | `HEIGHT`, `SETBACK`, `FLOOR_AREA`, `LOT_COVERAGE`, `BULK`, `FACADE`, `STRUCTURAL`, `BUILDABLE_VOLUME`, `SUBTERRANEAN_VOLUME`, `OTHER_NAMED` | physical-form path fires | keyed constraint object |
| `envelope.limit_or_allocation`, `envelope.geometry`, `envelope.permitted_work`, `envelope.prohibited_work`, `envelope.preservation_standard` | Envelope; transaction/observation | quantity/geometry/raw term | exact constraint states it | per-constraint path merge |
| `encumbrance.land_kind` | Encumbrance; all | `EASEMENT`, `COVENANT`, `DECLARATION_BURDEN`, `USE_RESTRICTION`, `OPTION`, `ROFR`, `LIS_PENDENS`, `OTHER_NAMED` | land burden or benefit path fires | immutable named kind |
| `encumbrance.beneficiaries`, `encumbrance.burdened_parties` | Encumbrance; transaction | party-interest ledgers | parties expressly hold or bear it | ledger operation |
| `encumbrance.physical_scope`, `encumbrance.legal_scope`, `encumbrance.access`, `encumbrance.inspection`, `encumbrance.construction_duty`, `encumbrance.maintenance_duty`, `encumbrance.cost_responsibility`, `encumbrance.runs_with_land` | Encumbrance; transaction/observation | scoped typed terms | corresponding words occur | path-specific set or scalar |

Parcel role grammar is mandatory: development capacity uses GRANTING/RECEIVING; easement uses SERVIENT/DOMINANT when stated; covenant uses BURDENED/BENEFITED. Never derive those relations from adjacency or deed order. Promote duration, termination, consent, option, casualty, and condemnation dates as boundaries or conditions; no common-law permanence is assumed.

<!-- BUILD:MODULE PUBLIC_PHYSICAL -->
## Module PUBLIC_PHYSICAL

**FR-PHY-001 — Permit acts.** A Permit event requires a named government authority plus a stated application, receipt, issuance, approval, amendment, renewal, suspension, revocation, or expiry of work or regulated-operation authorization. Private, title-company, or engineer certification does not qualify. An application can be a transaction with status `APPLIED`; a document merely mentioning one is reference-only.

**FR-PHY-002 — Observation basis.** As Built and Occupancy content is observational unless a government act itself authorizes occupancy. `AUTHORIZED` and `ACTUAL` are distinct Occupancy bases. A cover property type or registry `use` alone cannot trigger an observation. An executed transfer or compliance form triggers only fields it affirmatively states.

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `permit.kind`, `permit.identifier`, `permit.authority`, `permit.work_scope`, `permit.status`, `permit.conditions` | Permit; transaction/notice | enum/id/party/raw/set | government act fills the field | keyed permit object |
| `as_built.item_kind`, `as_built.geometry`, `as_built.floor_area`, `as_built.unit_count`, `as_built.completion`, `as_built.condition`, `as_built.location`, `as_built.operational_status` | As Built; observation | typed scalar/set/quantity | present physical statement fills it | evidence assertion by valid interval |
| `occupancy.basis` | Occupancy; transaction/observation | `AUTHORIZED` or `ACTUAL` | every Occupancy event | immutable per object |
| `occupancy.use`, `occupancy.capacity`, `occupancy.certificate_id`, `occupancy.subject` | Occupancy; transaction/observation | raw/set/quantity/id | exact field stated | keyed state or assertion path |

Inspection, survey, valuation-like physical as-of, test, issue, effective, expiration, and completion dates follow FR-DATE rules. Signature or certification date is evidence time only unless the form expressly states the condition is true on that date. Permit expiration may be `SELF_EXECUTING` only on exact automatic-expiry words. An executed assertion that equipment, use, or occupancy is absent produces a scoped observation with ASSERTED_NONE; a blank checkbox never does. A disjunctive statement uses `DISJUNCTIVE_SET` under FR-REC-004a and promotes no member.

<!-- BUILD:MODULE ECONOMICS -->
## Module ECONOMICS

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `value.kind` | Value; observation | `NOMINAL_CONSIDERATION`, `FULL_SALE_PRICE`, `ASSESSED_VALUE`, `APPRAISED_VALUE`, `FAIR_MARKET_VALUE`, `OTHER_NAMED` | valuation path fires | immutable measurement kind |
| `value.amount`, `value.subject_interest`, `value.basis`, `value.completion_basis` | Value; observation | quantity id/object/raw enum | governing words state it | one observation per kind/scope/time |
| `cost.kind` | Cost; transaction/observation | `PROJECT_EXPENDITURE`, `PROJECT_BUDGET`, `CONTRACT_COMMITMENT`, `TRANSACTION_TAX`, `RECORDING_FEE`, `OTHER_NAMED` | Cost path fires | immutable kind |
| `cost.amount`, `cost.status`, `cost.subject`, `cost.payer`, `cost.payee` | Cost; transaction/observation | quantity id/enum/object/party | exact words state it | one path per kind/scope/time |

**FR-ECO-001 — Value separation.** Nominal deed consideration, full sale price, assessed, appraised, and fair-market value are separate Value observations. A nominal amount never overwrites a sale price. Financing amounts remain Capital; project amounts remain Cost. **A source date becomes asserted-valid time only when its words attach the measurement to that date**; a deed's dating clause dates the deed, not its consideration recital. A checked transfer condition is never `value.basis` without words equating it to the valuation basis.

**FR-ECO-002 — Tax and fee recognition.** A citable cover, executed return, receipt, or form, or an operative clause labeling a named tax or fee creates its exact quantity kind. **Every affirmatively completed panel number remains a quantity under FR-QTY-002.** A **preprinted registry-panel field** creates a Cost observation only when (a) nonzero; (b) exact status words say PAID, CHARGED, DUE, ASSESSED, or EXEMPT; (c) an executed return or receipt states the same field; or (d) a present operative act in this document gives it an exact FR-ECO-003 target. Otherwise its disposition is `VALUES_ONLY`, including an affirmative zero. This exception applies **only to adapter-declared universal registry panels**, never to executed returns, receipts, or operative clauses — the trigger otherwise fires on a property of the form rather than of the instrument. Set status solely from visible words; a bare filled field is `REPORTED_AMOUNT`. Payer and payee require express labels.

**FR-ECO-003 — Act versus filing attachment.** A charge stated as levied on a transaction or act links to that act's event group and affected parcel set. A charge stated as levied on filing or recording stays document-scope and links to no act event group; without a supportable BBL it is counted as unplaced rather than attached by address. One unallocated multi-event amount remains `INSTRUMENT_TOTAL`/`NOT_DERIVABLE`. Executed return or receipt controls its named field; cover or index controls the register-reported field. Preserve discrepancies and never use either to resolve consideration, principal, or value.

**FR-ECO-004 — Cost character.** A clause presently committing a party to project expenditure is a Cost **transaction**, whether or not an amount is stated; a missing amount is a missing measurement, not a missing commitment. A form or receipt reporting a budgeted, incurred, charged, paid, assessed, or exempt amount is a Cost **observation**. Exact status words control. A displayed amount alone never decides between obligation and measurement.

<!-- BUILD:MODULE NOTICE_AUTHORITY -->
## Module NOTICE_AUTHORITY

**FR-NOT-001 — Notice.** A memorandum, notice, affidavit, UCC form, or register remark reporting an interest or act made elsewhere goes in `notices` with mode ASSERT and the target function and object type supported by its words. It may carry raw pointers and stated claim attributes; it has no lifecycle delta and imports no target state. If the same document also performs a present act, load that act's module and emit a separate transaction.

**FR-NOT-002 — Authority-only content.** A power of attorney, corporate resolution, trustee or officer affidavit, acknowledgement, or capacity recital supplies party authority, capacity, and evidence only unless an independent clause fills one of the eleven functions. **A complete zero-event result names `NO_FUNCTION_PATH_FILLED`, must pass FR-COV-003 with all twelve searches completed, and must still carry the FR-DOC-003 support registries** — a document with no function event still has parties, and losing them is the failure this framework exists to prevent.

**FR-NOT-003 — Pointer sources.** Capture visible cross-reference labels and locators, and adapter-authorized remarks resolved as pointers under FR-REC-013, through FR-REF-001 with `reference_class: RECORDED_INSTRUMENT`. `amends`, `substitutes`, `assigns`, `satisfies`, `corrects`, `derives from`, or another exact relation is stored raw; never choose a relation from document type. A statute or code citation is `STATUTE_REGULATION` and authority-only; an internal schedule is `INCORPORATED_SECTION` under FR-PAGE-005.

<!-- BUILD:MODULE GENERIC_GAP -->
## Module GENERIC_GAP

**FR-GAP-001 — No improvisation.** This module defines no state, assertion, or term path. For each lens `HIT` not covered by a loaded module, record the anchor, verb and object, candidate function, required output path, and `FRAMEWORK_GAP` with `failure_scope`. Do not invent a subtype or path, and do not suppress the clause to obtain a zero-event document. Under FR-SWP-001 this module is the receiver for content a nomination-driven read would never have sought.

<!-- BUILD:END -->
