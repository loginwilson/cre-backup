# NYC C.R.E.D. Extraction Framework v1-B

Status: isolated Block 1 draft. This file defines the extraction build. The reader must also apply matrix-spec.md after producing the event table.

## 0. Reader contract and execution order

This framework turns one recorded instrument package into an event table. The only allowed inputs are the supplied document id, its supplied registration record, and every page image in that document package. Do not use another instrument, parcel history, a website, a map, a party database, or unstated New York real-estate knowledge to supply a value.

Apply these steps in order:

1. Read every page image, including covers, riders, exhibits, continuation pages, signatures, acknowledgments, tax forms, and affidavits.
2. Build the evidence registry under rules FR-EV-001 through FR-EV-009.
3. Identify operative acts and qualifying assertions under FR-PKG-001 through FR-PKG-012.
4. Split them into event packages, then assign mode, function, date, parties, quantities, terms, and parcels.
5. Replace every absent field with one of the four semantic nulls under FR-NULL-001 through FR-NULL-007.
6. Run the validations in section 15. Do not repair a failed validation by inventing a value.
7. Serialize the event table, then apply matrix-spec.md.

**FR-SCOPE-001 — Independent reading.** Treat the instrument as the only evidence of its legal and factual effects. A reference to an earlier instrument identifies or describes an object; it does not import the earlier instrument's unseen contents.

**FR-SCOPE-002 — Knowledge boundary.** Domain knowledge may decode words that appear in the instrument. It may not add a party, amount, date, parcel, priority, duration, right, obligation, status, or relationship that the allowed inputs do not state or deterministically encode.

**FR-SCOPE-003 — Rule execution.** A derived value is valid only when a rule id below names the procedure and every input named by that procedure is present in the event table or evidence registry.

**FR-SCOPE-004 — Module loading.** Load sections 0 through 10 and 12 through 15 for every document. From section 11 load only module FR-TERM-100 and the modules whose trigger matches the operative instrument. Load more than one triggered module when one instrument performs more than one kind of act. This keeps the per-document extraction build within the context ceiling.

## 1. Evidence and provenance

### 1.1 Evidence registry

**FR-EV-001 — Evidence atom.** Give each cited passage an evidence id E001, E002, and so on in page order. Store:

- source_kind: PAGE_IMAGE or REGISTRATION;
- location: page-NN plus a unique visible anchor, or registration followed by the field path;
- quote: the shortest verbatim span that proves the value;
- legibility: CLEAR or PARTIAL;
- note: required only when PARTIAL, naming the unreadable characters with question marks.

A visible table cell may be quoted as column label plus cell value. A check mark is quoted as the label plus [checked]. A deletion is quoted as the affected words plus [struck]. Within quote, preserve visible characters, capitalization, and punctuation; replace each visual line break or run of spacing between words with one ASCII space. Do not cite a filename, URL, package path, database query, or inferred page number as evidence.

**FR-EV-002 — Observed field support.** A field copied from the instrument carries support of kind QUOTE and one or more evidence ids. The quote must prove that exact semantic field, not merely contain the same number or name.

**FR-EV-003 — Derived field support.** A normalized, classified, calculated, or inherited field carries support of kind RULE with exactly one rule id and input paths. Each input path must itself have valid support. A derived field may also list evidence ids, but the rule and inputs remain required.

**FR-EV-004 — Shared support.** Several fields may point to one evidence atom. Never broaden the quote to an entire paragraph when a shorter span proves each field.

**FR-EV-005 — Handwriting and form marks.** Within an executed form, a handwritten or typed insertion controls the preprinted text in the same blank. A checked choice is present. An unchecked choice is not evidence of its negation. Text visibly struck through is excluded from positive extraction.

**FR-EV-006 — Blank and unused forms.** A blank, unchecked, or unexecuted template field supplies no value. A visible N/A, NONE, deletion, or equivalent explicit negation supplies ASSERTED_NONE only for the field named by that mark.

**FR-EV-007 — Illegible text.** Transcribe only characters that are visually supportable. If one uncertain character can change a matrix field, set that field to UNKNOWN, store all legible candidates, cite the partial passage, and add flag ILLEGIBLE_MATRIX_FIELD. Do not use registration data to silently repair legal text.

**FR-EV-008 — Registration exclusions.** Ignore registration URLs, retrieval timestamps, pipeline metadata, local filenames, and preparation metadata unless the instrument makes preparation itself an operative act. Registration type, document id, CRFN, recorded time, document date, parties, amounts, and parcels remain admissible at the ranks in FR-EV-009.

**FR-EV-009 — Field-specific source ranking.** Resolve a conflict by field class:

| field class | rank 1 | rank 2 | rank 3 |
|---|---|---|---|
| legal act, estate, object, mode, operative party role, rights, obligations, conditions, event date | executed operative clause or executed amendment/rider | executed schedule or executed instrument-specific annex | recording cover or registration |
| signatures, authority, acknowledgement | executed signature/authority/acknowledgement page | executed operative clause | recording cover or registration |
| indexed document id, CRFN, recording time, indexed document type, indexed BBL/unit/partial-lot status | recording cover | registration | operative instrument |
| tax-reporting sale price, assessed value, exemption, property use | executed tax or transfer report | recording cover or registration | operative instrument |
| debt and lien economics | executed note/mortgage/security clause | executed modification, affidavit, or schedule directed to that debt | recording cover or registration |

Use the highest available rank for that field. When two sources at the same highest rank disagree and neither expressly corrects the other, set the field to UNKNOWN and record both candidates. A lower-ranked value remains a conflict note but cannot replace the higher-ranked value. A nominal consideration in a deed and a full sale price in an executed transfer report are different semantic quantities, not a conflict.

## 2. Event-table record

**FR-REC-001 — Document envelope.** The event table has document_id, registration_type, crfn, recorded_at, source_page_count, framework_version, evidence_registry, party_registry, quantity_registry, events, unresolved_items, and validation. Copy indexed metadata with FR-EV-009 support. source_page_count is the number of supplied page images, not a printed cover count.

**FR-REC-002 — Event package shape.** Every event contains all of these fields:

| field | required content |
|---|---|
| event_id | deterministic id under FR-REC-003 |
| event_group_id | links simultaneous effects of one operative act |
| status | RESOLVED or UNRESOLVED |
| function | one fixed function or UNKNOWN |
| subtype | controlled lower-case description of the affected state object |
| object_label_raw | shortest verbatim phrase naming the affected state object |
| mode | CREATE, MODIFY, TRANSFER, TERMINATE, ASSERT, CORRECT, or UNKNOWN |
| state_object_key | object identity under FR-REC-004 |
| effective_date | value, precision, interval_start, interval_end, basis, support |
| parties | event-party records pointing to party_registry, with roles, sides, shares, authority, support |
| direction | DIRECTIONAL or NON_DIRECTIONAL, plus from_party_ids and to_party_ids |
| parcels | every affected parcel with BBL, role, scope, unit, share, and support |
| quantities | ordered quantity_ids pointing to quantity_registry under section 9 |
| terms | typed term objects from section 11 |
| state_delta | lifecycle and field operations that the matrix fold will apply |
| references | referenced instruments and identifiers without imported contents |
| support | support for function, subtype, mode, and object classification |
| conflicts | field-level competing evidence that survived FR-EV-009 |
| review_flags | only flags allowed by FR-AMB-005 |

No event may omit a field. Use the four semantic nulls, not JSON null, blanks, empty strings, or empty placeholders. Arrays may be empty only when the corresponding concept is NOT_APPLICABLE and that sentinel appears in a companion status field.

**FR-REC-003 — Event identifiers.** After all events are found, sort candidate events by earliest operative evidence page, then vertical reading order on that page, then fixed function order from matrix-spec.md, then mode order CREATE, MODIFY, TRANSFER, TERMINATE, ASSERT, CORRECT, UNKNOWN. Number them document_id:E001, document_id:E002, and so on. Events produced by one clause share document_id:G001, G002, and so on using the same first-appearance order.

**FR-REC-004 — State-object key.** Choose the first applicable key:

1. If the event names a CRFN, recording file number, UCC initial file number, reel/page, or other unique recorded-instrument id for the affected object, use FUNCTION:REF:identifier-type:normalized-identifier, with components normalized under FR-REC-009.
2. If the act creates an object and gives it a unique instrument-local name or unit, use FUNCTION:NAMED:normalized-name-or-unit, normalized under FR-REC-009.
3. If an operative clause explicitly points to an object already keyed earlier in this same document (“that easement,” “the mortgage described above,” or an exact clause/schedule reference), reuse that key and cite the linking words. Similar parties, amounts, dates, or parcels are not an explicit link.
4. If it affects one identified agreement without a recorded id, use FUNCTION:AGREEMENT:event_group_id.
5. Otherwise use FUNCTION:LOCAL:event_group_id:subtype:NN, where NN is the one-based two-digit order of same-function, same-subtype objects at their first operative mention. Reuse that local key only through item 3.

Do not merge two keys because parties, amounts, dates, or parcels resemble one another. A linked Capital and Encumbrance event have separate function-prefixed keys and share event_group_id and references.

**FR-REC-005 — State delta.** state_delta has lifecycle_op and ordered field_ops. lifecycle_op is ACTIVATE for CREATE, PRESERVE for MODIFY/TRANSFER/CORRECT, DEACTIVATE for TERMINATE, OBSERVE for ASSERT, or UNKNOWN. Each field_op is SET, REMOVE_ASSERTED, NO_CHANGE, or UNKNOWN, with path, value, and support. REMOVE_ASSERTED means the document expressly says the item is absent; it does not erase historical evidence.

### 2.1 Controlled subtypes

**FR-REC-006 — Subtype dictionary.** Choose the first exact concept supported by the operative object words. Use only these lower-case tokens:

| function | subtype tokens, in precedence order |
|---|---|
| Identity | address; bbl; tax_lot; lot_boundary; zoning_lot; condominium_unit_designation; building_name; parcel_composition; other_identity |
| Title | fee_estate; leasehold_estate; condominium_unit; common_interest; life_estate; other_possessory_estate |
| Entitlement | development_right; air_right; land_use_authorization; development_license; development_option; other_land_use_privilege |
| Envelope | height; setback; floor_area; lot_coverage; bulk; facade; structural_envelope; buildable_volume; other_physical_constraint |
| Encumbrance | mortgage_lien; ucc_fixture_interest; easement; covenant; declaration_burden; assignment_of_rents; lien_priority; other_property_burden |
| Capital | mortgage_debt; note_debt; credit_facility; funding_commitment; equity_contribution; other_finance_obligation |
| Permit | permit_application; construction_permit; work_permit; operating_permit; governmental_approval; other_governmental_authorization |
| As Built | installed_equipment; building_geometry; actual_floor_area; completed_work; physical_condition; other_existing_physical_state |
| Occupancy | authorized_use; authorized_capacity; actual_use; actual_capacity |
| Cost | construction_cost; renovation_cost; repair_cost; operating_cost; professional_cost; project_budget; other_project_cost |
| Value | nominal_consideration; full_sale_price; assessed_value; appraised_value; allocated_transaction_value; other_property_value |

An `other_` token is allowed only when the function rule is satisfied and none of the earlier tokens in that row describes the words. Store the shortest operative object phrase separately as object_label_raw. Do not coin a new subtype.

**FR-REC-007 — Subtype split.** Within one function, separately keyed objects with different subtype tokens are separate events. Several fields or quantities about one object do not cause a split. When one source asserts distinct Value kinds, create one Value ASSERT object per Value subtype so that one valuation does not overwrite another.

**FR-REC-008 — Canonical event-table serialization.** Write extraction.json as UTF-8 without BOM, LF line endings, two-space indentation, and one terminal LF. Envelope keys use the FR-REC-001 order. Registry records sort by their ids; events sort by event_id; unresolved_items sort by earliest evidence id then candidate function then candidate mode. Event keys use the FR-REC-002 table order. Unordered id, role, flag, and candidate arrays are deduplicated and sorted lexically; evidence quotes, ordered field_ops, and expressly sequenced terms retain their defined order. Use the scalar forms in MX-SER-003. Emit every required field and never emit JSON null.

**FR-REC-009 — Key-component normalization.** For state_object_key components, apply Unicode NFC; uppercase letters; trim edge whitespace; collapse internal whitespace to one ASCII space; replace % with %25 and : with %3A; preserve all other punctuation and leading zeros. identifier-type is CRFN, UCC_FILE, REEL_PAGE, or OTHER_RECORDED. Format reel/page as REEL=normalized-reel;PAGE=normalized-page. This normalization is for keys only and never changes raw evidence.

## 3. Finding and splitting events

**FR-PKG-001 — Operative-act trigger.** Create an event candidate for each clause that presently grants, conveys, assigns, assumes, creates, changes, subordinates, corrects, releases, terminates, files, certifies, approves, revokes, or expressly declares a state that maps to a function. The verb and its object must both be visible or supported by a ranked source.

**FR-PKG-002 — Assertion trigger.** Create an ASSERT candidate only when the document expressly states a current state, the assertion maps to a matrix field, and the clause does not itself operate to change that state. Examples are an executed affidavit that equipment is installed and operational, or a certification of present zoning-lot geometry.

**FR-PKG-003 — Historical recital exclusion.** A recital about an earlier act is not a new event. Store its identifiers, dates, original amounts, and described status as references or terms of the present event. If the instrument independently makes a current assertion about the referenced object, create only the current ASSERT event at the present event date.

**FR-PKG-004 — Future and conditional acts.** A promise, option, remedy, or event that will occur only after a future condition is a term of the current event. Do not emit the future event unless the same document states that the condition has occurred and the act is now effective.

**FR-PKG-005 — Function split.** One operative clause produces one event for each function whose state changes. Link the events with one event_group_id. Do not force one primary function when the clause independently changes two functions.

**FR-PKG-006 — Object split.** Within one function, split events when the clause affects different state_object_keys. Do not split repeated descriptions of the same object.

**FR-PKG-007 — Mode split.** Within one function and state object, split events when independent clauses apply different modes and neither is merely the means of the other. An assignment plus an amendment to the assigned agreement yields TRANSFER and MODIFY. A transfer that necessarily carries existing terms without changing them yields TRANSFER only.

**FR-PKG-008 — Date split.** Split clauses into different events when they have different effective dates or one is presently effective and another is conditional. Clauses with one act, one date, and several BBLs remain one event with several parcel entries.

**FR-PKG-009 — Party-direction split.** Split when different portions of an instrument have different from/to party sets or different explicit shares. Do not split multiple parties on the same side of the same act.

**FR-PKG-010 — Parcel-role split.** Keep granting, receiving, burdened, benefited, collateral, and subject parcels in one event when those roles form one transaction. Split only when the clauses operate independently on different parcel sets.

**FR-PKG-011 — Administrative attachments.** A cover page, tax form, smoke-detector affidavit, or certification may create a separate ASSERT event when FR-PKG-002 is satisfied. Otherwise it supplies fields or evidence to an operative event and does not create an event by being attached.

**FR-PKG-012 — No-effect content.** Do not emit events for addresses used only for notice, recording fees, notary commissions, return addresses, boilerplate successor clauses, general warranties, unused form alternatives, or legal descriptions that only delimit another event's premises.

## 4. Event modes

Apply the first rule whose test matches the clause's legal verb and object. Do not choose mode from registration type alone.

**FR-MODE-001 — CREATE.** Use CREATE when the clause brings the state object into existence, activates it, issues it, or first establishes the relevant right, obligation, lien, estate, permit, physical condition, or valuation assertion.

**FR-MODE-002 — MODIFY.** Use MODIFY when an existing object continues and the clause changes one or more of its fields, scope, priority, obligations, beneficiaries, parcel coverage, or terms without stating that the prior statement was erroneous.

**FR-MODE-003 — TRANSFER.** Use TRANSFER when an existing object continues and its holder, obligor, beneficiary, ownership interest, or specified share moves from one party to another. Store assumptions of obligations in terms and party roles. Do not label the carried terms MODIFY unless the clause changes them.

**FR-MODE-004 — TERMINATE.** Use TERMINATE when the clause releases, cancels, discharges, revokes, expires, surrenders, or ends the object or its effect on the named scope. A partial release is MODIFY with released_scope as a field operation; it is TERMINATE only for a separately keyed released object.

**FR-MODE-005 — ASSERT.** Use ASSERT when the document states a present state without operating to create, modify, transfer, terminate, or correct it. An indexed description on a cover is not enough unless a signed or certified source meets FR-PKG-002.

**FR-MODE-006 — CORRECT.** Use CORRECT only when the clause identifies a prior value as erroneous, mistaken, omitted, or in need of correction and supplies the replacement or deletion. Record old_value when stated and new_value. An ordinary amendment is MODIFY.

**FR-MODE-007 — Competing modes.** If two highest-ranked operative clauses apply incompatible modes to the same object and neither limits the other by scope or sequence, set mode and function to UNKNOWN, status UNRESOLVED, preserve the mode candidates, and send the package to unresolved_items. Do not select the mode appearing later on the page.

## 5. Fixed function boundaries

Each event receives exactly one function. FR-PKG-005 creates linked events when one act crosses boundaries.

**FR-FN-001 — Identity.** Use Identity for an act or qualifying assertion that establishes or changes the formal identity, composition, boundary, tax-lot/unit designation, parcel name, building name, or address of real property. A metes-and-bounds exhibit used only to identify the premises of another event is parcel scope, not a separate Identity event. A zoning-lot certification that only states which land constitutes the zoning lot is Identity ASSERT.

**FR-FN-002 — Title.** Use Title for ownership or a possessory estate: fee, leasehold, condominium unit, appurtenant common interest, life estate, or another expressly named estate; and for its creation, transfer, correction, or termination. A lease creation or assignment is Title. A license or permission that creates no possessory estate is Entitlement or Encumbrance according to FR-FN-003 and FR-FN-005.

**FR-FN-003 — Entitlement.** Use Entitlement for a non-possessory right or governmental/private authorization to develop, build, enlarge, use development capacity, transfer air/development rights, or exercise a land-use privilege. A certification of geometry without a grant of capacity is Identity. A private promise restricting construction is Envelope and, when it runs with or burdens land, Encumbrance.

**FR-FN-004 — Envelope.** Use Envelope for a legally operative constraint or allocation of physical building mass or exterior form: height, setback, lot coverage, floor area, bulk, facade preservation, structural envelope, or defined buildable volume. Use As Built for a statement of what physically exists. Create a linked Encumbrance event when the constraint is also a land-running covenant or easement.

**FR-FN-005 — Encumbrance.** Use Encumbrance for a lien, mortgage security interest, UCC fixture interest, easement, covenant, declaration burden, restrictive agreement, assignment of rents, priority relationship, or comparable burden/benefit attached to property. A debt without collateral is Capital only. A priority-only subordination changes Encumbrance and does not change Capital.

**FR-FN-006 — Capital.** Use Capital for a debt, credit facility, funding commitment, equity contribution, principal/balance, repayment obligation, or finance terms. A mortgage that both secures and evidences a loan yields linked Encumbrance and Capital events. A satisfaction yields Capital TERMINATE only when it expressly states the debt or obligation is paid, cancelled, or discharged; release of the lien alone yields Encumbrance TERMINATE.

**FR-FN-007 — Permit.** Use Permit for an application, issuance, approval, amendment, renewal, suspension, or revocation by the governmental authority named in the document that authorizes physical work or a regulated operation. A recorded private certification, title-company certification, or notice is not a Permit.

**FR-FN-008 — As Built.** Use As Built for an observed, certified, or expressly asserted existing physical characteristic: installed equipment, current dimensions, unit/building configuration, completed work, actual floor area, or physical condition. A future maintenance or construction duty is a term of Envelope or Encumbrance, not As Built.

**FR-FN-009 — Occupancy.** Use Occupancy for an expressly stated lawful authorized occupancy/use/capacity or an expressly stated actual current occupancy/use. Mark basis AUTHORIZED or ACTUAL. A private restriction to residential or commercial use is Encumbrance unless a governmental approval grants the use, in which case create a linked Occupancy event. A cover-page property type alone does not meet FR-PKG-002; an executed transfer report's current use may support Occupancy ASSERT.

**FR-FN-010 — Cost.** Use Cost for an incurred, paid, budgeted, or contractually committed expenditure for construction, renovation, repair, operation, professional work, or a project. Purchase price, nominal consideration, debt principal, assessed value, tax, recording fee, and insurance coverage are not Cost.

**FR-FN-011 — Value.** Use Value for sale consideration, appraised value, assessed value, allocated transaction value, or another express valuation of the property or interest. Keep each valuation kind separate. A financing principal is Capital; a project expense is Cost.

### 5.1 Mandatory linked-function tests

**FR-FN-020 — Secured finance test.** When a clause creates or changes both an obligation/credit facility and collateral security, emit Capital and Encumbrance events. If it addresses only security or priority, emit Encumbrance. If it addresses only the obligation, emit Capital.

**FR-FN-021 — Easement/covenant test.** Emit Encumbrance for the granted burden/benefit. Also emit Envelope when the operative terms constrain physical mass or facade; Entitlement when they grant development capacity; Title only when they expressly convey a possessory estate.

**FR-FN-022 — Declaration/common-interest test.** Emit Title when the act assigns or changes a unit's appurtenant common interest or exclusive-use common element. Emit Encumbrance for independently imposed land-running restrictions or obligations. Do not emit Encumbrance merely because the operative vehicle is a declaration.

**FR-FN-023 — Zoning-lot test.** Emit Identity for creation, correction, or present certification of zoning-lot composition or geometry. Emit Entitlement only when the same act grants, transfers, reserves, or quantifies development rights or capacity. Emit Envelope only when it fixes physical bulk constraints.

**FR-FN-024 — Lease test.** Creation, assignment, surrender, or termination of the leasehold estate is Title. Independently granted options, licenses, or development rights are Entitlement. Rent and lease economics stay as Title terms unless the instrument separately creates or transfers a financing obligation.

**FR-FN-025 — Evidence-only value test.** Sale price and assessed value on an executed transfer report create linked Value ASSERT events only when the report states them as current transaction/property values. Nominal deed consideration remains a Value quantity of kind NOMINAL_CONSIDERATION and does not overwrite FULL_SALE_PRICE.

## 6. Dates and date basis

effective_date contains value in ISO form when complete, precision DAY/MONTH/YEAR/UNKNOWN, interval_start, interval_end, basis code, and support.

**FR-DATE-001 — Date precedence.** For each event, take the first available source:

1. an explicit clause saying effective, as of, from, commencing, terminated on, assigned on, or equivalent for that event;
2. the date in the operative instrument's opening or dating clause;
3. when the document expressly requires execution by all named operative parties before effect, the latest required party execution date;
4. a dated execution signature for the party whose unilateral act is effective on execution;
5. an acknowledgement date that expressly proves the execution date when no operative or signature date is supplied;
6. recording/filing date only under FR-DATE-005;
7. UNKNOWN.

Store the chosen basis code EXPLICIT_EFFECTIVE, INSTRUMENT_DATE, COMPLETION_OF_REQUIRED_EXECUTION, EXECUTION_DATE, ACKNOWLEDGED_EXECUTION, OPERATIVE_FILING, or UNSUPPORTED.

For item 1, “equivalent” means a date phrase grammatically attached to the event's operative verb/object that expressly states when that act takes effect. A page heading, preparation date, “dated as of” reference to another instrument, tax-report date, or acknowledgement date does not satisfy item 1 unless its words expressly attach it to the present act.

**FR-DATE-002 — Instrument date versus acknowledgements.** When an explicit effective or instrument date exists, later signature or acknowledgement dates do not replace it unless the instrument states effectiveness depends on those later acts.

**FR-DATE-003 — Party-specific dates.** If separate unilateral acts become effective on each party's execution and the dates differ, split under FR-PKG-008. If the document requires all signatures, use the latest required execution date and keep every signature date in party authority data.

**FR-DATE-004 — Referenced dates.** A date belonging to an earlier mortgage, deed, lease, declaration, filing, or note is a reference/term of the present event. It is not the present event date.

**FR-DATE-005 — Operative filing.** Use the recorded/filing date when the act being extracted is the filing, continuation, termination filing, notice, or other act whose operative clause expressly says effectiveness is achieved by filing/recording. For a UCC form, the filing event may use OPERATIVE_FILING; the unseen security agreement's creation date remains UNKNOWN. Never use recording date because every other date is absent.

**FR-DATE-006 — Conditional dates.** If a future date depends on an unsatisfied condition, store it as a term and do not use it as the present event date. If the document states the condition occurred, use the stated occurrence/effective date.

**FR-DATE-007 — Partial dates.** Convert a year to interval January 1 through December 31 and a month to its first through last calendar day. Do not invent a day. A complete date has identical interval start and end.

**FR-DATE-008 — Date conflict.** Apply FR-EV-009 before precedence. Same-rank incompatible candidates produce UNKNOWN with candidate intervals and flag CONFLICTING_EVENT_DATE. Filing date remains excluded unless FR-DATE-005 applies.

## 7. Parties, roles, shares, and direction

**FR-PARTY-000 — Party registry and ids.** A party_registry item has party_id, name_raw, name_normalized, aliases_explicitly_equated, and support. Create one item per distinct operative party, sorted by first operative mention and then exact name_raw; assign document_id:P001, P002, and so on. Reuse an id only when the exact name_raw recurs or the document expressly equates two names. Each event-party record has party_id, role_raw, roles, side, share, authority, and support. A representative who is not an operative party appears only inside authority and receives no party_id.

**FR-PARTY-001 — Operative parties.** Extract every party that grants, receives, owes, is owed, assigns, is assigned, assumes, releases, benefits, is burdened, declares, certifies, approves, or is otherwise given an operative role. Do not treat a presenter, return recipient, preparer, notary, attorney, abstract company, or signatory as an operative party solely because it appears.

**FR-PARTY-002 — Names.** Store name_raw exactly as printed and name_normalized by uppercasing, trimming edge punctuation/space, and collapsing internal whitespace. Do not expand initials, correct spelling, join aliases, or merge entities.

**FR-PARTY-003 — Function roles.** Use the instrument's role when present; otherwise use the first matching controlled role:

- Title: grantor/grantee, landlord/tenant, assignor/assignee, transferor/transferee, declarant, unit_owner;
- Encumbrance: mortgagor/mortgagee, debtor/secured_party, releasor/releasee, subordinating_lienholder/senior_lienholder, easement_grantor/easement_grantee, burdened_party/benefited_party;
- Capital: borrower/lender, obligor/obligee, assignor/assignee, contributor/recipient;
- Permit: applicant/issuing_authority;
- assertion functions: declarant/certifier/subject_party;
- other transfers: granting_party/receiving_party.

Keep the printed role as role_raw and the controlled role as role.

**FR-PARTY-004 — Representatives.** When a person signs as attorney-in-fact, officer, member, trustee, authorized agent, or other representative, the represented entity is the operative party. Store the signer in authority with representative_name, capacity, represented_party_id, and support. Add the signer as an operative party only when a separate clause gives that signer rights or obligations personally.

**FR-PARTY-005 — Sides.** Assign side FROM to a party surrendering or transferring a right/object; TO to a party receiving it; BOTH to a party that both gives and receives in the same event; and NEUTRAL to a declarant, certifier, approving authority, or participant in a non-directional modification.

**FR-PARTY-006 — Direction.** direction is DIRECTIONAL when at least one identified right, estate, object, obligation, or share moves from FROM to TO. Populate both party-id lists. It is NON_DIRECTIONAL for CREATE without a transferor, bilateral MODIFY, priority arrangements without a transferred holder, ASSERT, CORRECT without a holder change, and acts by an authority. Do not invent from/to sides to make an event directional.

**FR-PARTY-007 — Shares.** Store an exact fraction, percent, or described interest only when the instrument states it. Normalize fractions to reduced numerator/denominator and percents to an exact decimal while retaining raw text. Joint ownership, marital status, plural grantees, or order of names does not support equal shares. Use UNKNOWN for an applicable unstated share.

**FR-PARTY-008 — Several roles.** One party may have several roles in one event; store each role once. Several parties may occupy one side. Do not collapse them into a collective party unless the instrument names the collective as a legal party.

**FR-PARTY-009 — Cover conflicts.** Party panels on a recording cover are indexing evidence. Operative clauses control legal roles. A continuation/addendum that is part of the executed filing controls omitted parties at the same operative rank.

## 8. Parcel attribution and roles

**FR-BBL-001 — BBL form.** A canonical BBL is ten digits: one borough digit, five block digits, four lot digits. When borough, block, and lot are separately visible, derive the form with borough codes Manhattan 1, Bronx 2, Brooklyn 3, Queens 4, Staten Island 5 and left zero-padding. Record raw components and support the canonical value with this rule and those inputs.

**FR-BBL-002 — Indexed BBL.** For the indexed BBL use the recording cover, then registration, under FR-EV-009. Preserve the operative instrument's legal description and unit even when it differs. Do not resolve the conflict with a map or outside source.

**FR-BBL-003 — Affected-set test.** Include a parcel only when an operative clause, incorporated schedule/exhibit, or highest-ranked indexing source identifies it as within the act's scope. A return address, notice address, party address, or referenced earlier instrument's unrelated property is not affected.

**FR-BBL-004 — Cover list versus operative subset.** A multi-parcel cover is a candidate affected set. If the operative clauses explicitly limit the act to a subset, use that subset. If the operative act addresses the whole declared/mortgaged/leased premises and the cover enumerates its BBLs, include all enumerated BBLs.

**FR-BBL-005 — Parcel roles.** Assign every parcel one or more controlled roles: SUBJECT, GRANTING, RECEIVING, BURDENED, BENEFITED, SERVIENT, DOMINANT, COLLATERAL_LOCATION, DECLARED_COMPONENT, or UNIT_APPURTENANT. Use GRANTING/RECEIVING for development-right movement; SERVIENT/DOMINANT for easements; BURDENED/BENEFITED for covenants; SUBJECT when no asymmetric role is expressed.

**FR-BBL-006 — Partial scope.** Store scope ENTIRE_BBL, PARTIAL_BBL, UNIT, AIR_SPACE, FACADE, EASEMENT_AREA, or DESCRIBED_PREMISES. A partial-lot mark, unit number, vertical area, facade, or metes-and-bounds subset prevents whole-BBL scope. Fanning to a BBL never changes partial scope into entire scope.

**FR-BBL-007 — Parcel shares.** Extract an affected parcel's share only when stated. Do not infer shares from area, frontage, unit count, order, or number of BBLs.

**FR-BBL-008 — Unresolved BBL.** If the act is property-linked but no canonical BBL is supportable, store bbl UNKNOWN with the available legal description/unit and flag UNRESOLVED_BBL. The event remains in the table but matrix-spec.md sends it to the unresolved-parcel annex.

**FR-BBL-009 — Multi-role same BBL.** Store one parcel entry per BBL and scope, with a sorted role array. If two distinct scopes on the same BBL are independently affected, keep separate entries.

## 9. Quantities and allocation

**FR-QTY-000 — Quantity record.** Each quantity_registry item has quantity_id, kind, label_raw, value_raw, value_normalized, currency_or_unit, scope, applies_to_event_ids, applies_to_parcels, applies_to_party_ids, allocation_status, allocations, and support. After events are identified, sort quantities by earliest supporting evidence page and reading order, then by the kind order in FR-QTY-001, then scope; assign document_id:Q001, Q002, and so on. Store one registry item and reference its id from every applicable event. A repeated display of the same labeled quantity is shared only when the instrument says it is the same total or both passages are exact repetitions about the same object and scope.

Every quantity has quantity_id, kind, raw_text, normalized_value, unit_or_currency, scope, allocation_status, applies_to_event_ids, applies_to_parcels, and support.

**FR-QTY-001 — Semantic typing.** Assign kind from the words that label or govern the number. Never type a number from document type alone. Use only these kinds, in this order: NOMINAL_CONSIDERATION, FULL_SALE_PRICE, ASSESSED_VALUE, APPRAISED_VALUE, ORIGINAL_PRINCIPAL, CURRENT_BALANCE, MAXIMUM_LIEN, CREDIT_LIMIT, NEW_MONEY, RENT, COST, FEE, TAX, PERCENT_INTEREST, COMMON_INTEREST, AREA, DIMENSION, DURATION, RATE, OTHER_NAMED. Use the first token whose meaning the governing words expressly name. Use OTHER_NAMED only when none matches, and store the shortest governing label in label_raw; do not coin a new kind.

**FR-QTY-002 — No conflation.** Original principal, current balance, maximum lien, credit limit, new money, payoff, mortgage tax amount, sale price, assessed value, nominal consideration, cost, fee, and tax are separate quantities even when values match.

**FR-QTY-003 — Normalization.** Money is exact decimal plus stated currency; do not assume currency when no symbol/name appears. Percent is an exact decimal percentage, not a fraction of one. Fractions are reduced rational values. Dimensions retain original unit and may include a deterministic unit conversion only when the conversion rule and inputs are recorded.

**FR-QTY-004 — Explicit zero.** A printed or written zero is numeric 0 when the field is affirmatively completed or the operative text states zero. A blank is not zero. "No new indebtedness" is ASSERTED_NONE for NEW_MONEY, not numeric 0.

**FR-QTY-005 — Quantity scope.** Set scope to EVENT, STATE_OBJECT, PARCEL, PARTY_SHARE, INSTRUMENT_TOTAL, or MULTI_EVENT_TOTAL from the governing words. A quantity that covers several BBLs or events remains one quantity object referenced by each affected event.

**FR-QTY-006 — Explicit allocation.** allocation_status is EXPLICIT only when the document states each allocation. It is DERIVED only when the document supplies a complete formula, all inputs, and the rule is recorded. Store the calculation expression and inputs.

**FR-QTY-007 — Not derivable.** When one total covers several events, objects, parties, or parcels and neither explicit allocations nor a complete formula exist, set allocation_status NOT_DERIVABLE. Keep the total once at its joint scope. Any requested component amount is UNKNOWN with support pointing to this rule and total. Do not divide equally, by stated shares unless the text applies those shares to the quantity, by area, or by BBL count.

**FR-QTY-008 — Not applicable allocation.** allocation_status is NOT_APPLICABLE when the quantity has exactly one target or is inherently non-allocative, such as duration or an instrument-wide rate.

**FR-QTY-009 — Amount conflicts.** Apply semantic typing before conflict resolution. Two differently typed amounts coexist. Two same-kind same-scope values at the same highest rank conflict and the normalized value becomes UNKNOWN with candidates.

## 10. References and cross-event linkage

**FR-REF-001 — Reference record.** Store referenced instrument type, date, recording identifier, parties, amount, and described relation only when stated. Each observed component has its own support.

**FR-REF-002 — No imported state.** A reference proves that this document refers to an object; it does not prove the object's unseen current balance, priority, assignments, terms, continuing validity, or parcel scope.

**FR-REF-003 — Group linkage.** Events from one operative act share event_group_id. Use related_event_ids to link Capital/Encumbrance, Envelope/Encumbrance, or other paired effects. A quantity's applies_to_event_ids controls shared quantities.

**FR-REF-004 — Referenced amount.** An original mortgage principal quoted in an assignment or satisfaction is ORIGINAL_PRINCIPAL of the referenced object. It is not assignment consideration, payoff, current balance, or new financing.

## 11. Terms modules

Load FR-TERM-100 for every event plus only triggered modules.

**FR-TERM-100 — Core terms.** For every event extract stated duration; start/end/maturity; conditions precedent/subsequent; options and who may exercise them; renewal/extension; termination rights; notice periods; priority; retained/reserved rights; assumptions; referenced-instrument ids; and any explicit sequence relation between present events. Encode a sequence relation as type EVENT_SEQUENCE with before_event_id, after_event_id, and support; do not create one from page or clause order. Use typed objects with name, value, holder/obligor when stated, scope, and support. Missing applicable terms are UNKNOWN; do not summarize them away.

**FR-TERM-101 — Term record and ids.** A term has term_id, name, status, value_raw, value_normalized, holder_party_ids, obligor_party_ids, scope, and support. status is PRESENT, UNKNOWN, NOT_APPLICABLE, or ASSERTED_NONE. value_raw and value_normalized take the same semantic sentinel when status is not PRESENT. Sort first by module order core, 110, 120, ..., 190; then by the token order in FR-TERM-102; then repeated values by evidence page and reading order. Number the result event_id:T01, T02, and so on. Deduplicate a token that occurs in more than one triggered module. Repeat a token only for independently stated values with different holder, obligor, scope, or condition.

**FR-TERM-102 — Controlled term names.** The prose lists in modules FR-TERM-110 through FR-TERM-190 map to these tokens in this order; use no synonyms or new tokens:

| module | ordered term-name tokens |
|---|---|
| core | DURATION; START_DATE; END_DATE; MATURITY_DATE; CONDITION_PRECEDENT; CONDITION_SUBSEQUENT; OPTION; RENEWAL; EXTENSION; TERMINATION_RIGHT; NOTICE_PERIOD; PRIORITY; RESERVED_RIGHT; ASSUMPTION; REFERENCED_INSTRUMENT_ID; EVENT_SEQUENCE |
| deed/title | ESTATE_OR_INTEREST; FRACTIONAL_SHARE; TENANCY; RESERVATION; EXCEPTION; SUBJECT_TO_INSTRUMENT; COVENANT; POSSESSION; CONSIDERATION; TRANSFER_VALUE; APPURTENANT_INTEREST |
| lease | LEASED_PREMISES; ORIGINAL_LEASE_ID; LANDLORD; TENANT; ASSIGNOR; ASSIGNEE; COMMENCEMENT_DATE; EXPIRATION_DATE; REMAINING_TERM; RENT; RENT_ESCALATION; SECURITY_DEPOSIT; PERMITTED_USE; RENEWAL_OPTION; PURCHASE_OPTION; TERMINATION_OPTION; ASSIGNMENT_CONSENT; SUBLETTING_CONSENT; ASSUMED_OBLIGATION; DEFAULT_REMEDY; APPURTENANT_INTEREST |
| mortgage/debt | ORIGINAL_PRINCIPAL; CURRENT_BALANCE; MAXIMUM_LIEN; CREDIT_LIMIT; NEW_MONEY; DEBT_TYPE; REVOLVING_STATUS; RATE_TYPE; STATED_RATE; RATE_INDEX; RATE_MARGIN; RATE_RESET; RATE_FLOOR; RATE_CAP; PAYMENT; MATURITY_DATE; ADVANCE_RIGHT; READVANCE_RIGHT; PRIORITY; COLLATERAL_CATEGORY; RENT_OR_PROCEEDS_SECURITY; GUARANTY; PREPAYMENT_TERM; DEFAULT_TERM; PAYMENT_ASSERTION; SUBORDINATE_OBJECT_ID; SENIOR_OBJECT_ID; AFFECTED_LAYER |
| UCC | FILING_ACTION; INITIAL_FILE_NUMBER; DEBTOR; SECURED_PARTY; ASSIGNEE; FIXTURE_FILING_INDICATOR; REAL_ESTATE_DESCRIPTION; RECORD_OWNER; COLLATERAL_CATEGORY; AMENDMENT_SCOPE; CONTINUATION_SCOPE; TERMINATION_SCOPE; FILING_DATE_BASIS |
| easement/declaration | GRANT; BURDEN; BENEFIT; SERVIENT_PARCEL; DOMINANT_PARCEL; BURDENED_PARCEL; BENEFITED_PARCEL; PHYSICAL_SCOPE; LEGAL_SCOPE; ACCESS_RIGHT; INSPECTION_RIGHT; CONSTRUCTION_DUTY; MAINTENANCE_DUTY; COST_RESPONSIBILITY; DURATION; PERPETUITY; RUNS_WITH_LAND; ASSIGNMENT_TERM; RESERVED_RIGHT; CONSENT_RIGHT; CONDITIONAL_TERMINATION; NOTICE_PERIOD; CASUALTY_THRESHOLD; CONDEMNATION_THRESHOLD; COMMON_ELEMENT_CLASS; UNIT_APPURTENANCE; AMENDED_SECTION |
| entitlement/envelope | RIGHT_OR_CAPACITY_TYPE; GRANTING_PARCEL; RECEIVING_PARCEL; FLOOR_AREA; BULK; HEIGHT; SETBACK; GEOMETRY; PERMITTED_WORK; PROHIBITED_WORK; PRESERVATION_STANDARD; APPROVAL_RIGHT; CONSENT_RIGHT; TRANSFER_TERM; RESERVATION; DURATION; CONDITION; NAMED_REGULATION |
| permit/occupancy/as-built | AUTHORITY; CERTIFIER; APPLICATION_NUMBER; PERMIT_NUMBER; CERTIFICATE_NUMBER; AUTHORIZED_WORK; AUTHORIZED_USE; AUTHORIZED_CAPACITY; ACTUAL_USE; USE_BASIS; ISSUE_DATE; EFFECTIVE_DATE; EXPIRATION_DATE; CONDITION; REVOCATION; COMPLETION_STATUS; PHYSICAL_ITEM; PHYSICAL_QUANTITY; PHYSICAL_LOCATION; OPERATIONAL_STATUS; INSPECTION_DATE; TEST_DATE |
| cost/value | MEASURE_KIND; SUBJECT_INTEREST; SUBJECT_PROJECT; MEASUREMENT_DATE; AMOUNT; CURRENCY; SOURCE_TYPE; COMPLETION_BASIS; VALUE_KIND; COMMITMENT_STATUS; PAYER; PAYEE; ALLOCATION_SCOPE |
| change/release | TARGET_OBJECT_ID; CHANGED_FIELD; OLD_VALUE; NEW_VALUE; PRESERVED_TERM; RELEASED_SCOPE; RETAINED_SCOPE; CORRECTION_REASON; AFFECTED_LAYER |

For each event, populate every core token and every token in each triggered module: PRESENT with an observed/derived value, UNKNOWN when the concept can apply but is not supported, ASSERTED_NONE when expressly negated, or NOT_APPLICABLE when it cannot structurally apply to that event. Use a narrower token such as RENEWAL_OPTION, CASUALTY_THRESHOLD, or STATED_RATE instead of also creating the broad OPTION, CONDITION, or AMOUNT token for the same words; mark the displaced broad token NOT_APPLICABLE. The module prose tells what passage belongs in each token; it does not authorize a different name.

**FR-TERM-110 — Deed/title transfer module.** Trigger: deed, conveyance, estate transfer, or common-interest assignment. Extract estate/interest conveyed; fractional share; tenancies exactly as stated; reservations; exceptions; specific subject-to instruments; covenants; assumption; possession; consideration quantities; transfer-report values; and appurtenant interests. Generic "subject to matters of record" without an identified matter is a term string, not an Encumbrance ASSERT. A named declaration/easement with recording reference qualifies under FR-PKG-002 when asserted to burden the transferred estate.

**FR-TERM-120 — Lease module.** Trigger: lease creation, assignment, assumption, amendment, surrender, or termination. Extract premises and estate; original lease id/date; landlord, tenant, assignor, assignee; commencement; expiration or duration; remaining term; rent and escalation; security deposit; permitted use; renewal/purchase/termination options; assignment/subletting consent; assumed obligations; defaults/remedies; extension; and appurtenant/common interests. Unknown expiration stays UNKNOWN even when a standard lease length could be guessed.

**FR-TERM-130 — Mortgage/secured-debt module.** Trigger: mortgage, deed of trust, security agreement, assignment, satisfaction, subordination, or modification. Extract original principal; current balance; maximum lien; credit limit; new money; debt type; revolving status; rate fixed/variable; stated rate; index, margin, reset, floors/caps; payment; maturity; advances/readvances; priority; collateral categories; rents/proceeds; guaranty; prepayment/default terms; payoff/payment assertion; subordinate/senior object ids; and whether lien, debt, or both are affected. Terms absent because a referenced credit agreement is not supplied are UNKNOWN.

**FR-TERM-140 — UCC module.** Trigger: UCC1, UCC3, continuation, assignment, amendment, or termination. Extract filing action; initial file number; debtor and secured party; assignee; fixture-filing indicator; real-estate description; record owner if stated; collateral categories; amendment scope; continuation; termination scope; and filing date basis. A UCC termination terminates filing effectiveness stated by the form; it does not prove the secured obligation was paid.

**FR-TERM-150 — Easement/covenant/declaration module.** Trigger: easement, declaration, restrictive covenant, right of way, zoning-lot agreement, or declaration amendment. Extract grant/burden/benefit; servient/dominant or burdened/benefited parcels; physical/legal scope; access/inspection; construction and maintenance duties; cost responsibility; duration/perpetuity; running-with-land clause; assignment; reservations; consent rights; conditional termination; notice; casualty/condemnation thresholds; common-element classification; unit appurtenance; and declaration section being changed.

**FR-TERM-160 — Entitlement/envelope module.** Trigger: air/development rights, zoning-lot certification, bulk agreement, facade restriction, or development covenant. Extract right/capacity type; granting and receiving parcels; quantified floor area/bulk/height/setback; geometry; permitted/prohibited work; preservation standard; approval/consent; transfer/reservation; duration; conditions; and source regulation named in the document. A cited regulation is a reference; do not import its text.

**FR-TERM-170 — Permit/occupancy/as-built module.** Trigger: governmental permit/approval, certificate of occupancy/use, physical-condition certification, or installed-equipment affidavit. Extract authority/certifier; application/permit/certificate number; authorized work/use/capacity; actual use basis; issue/effective/expiration; conditions; revocation; completion status; physical item; quantity/location; operational status; and inspection/test date. Do not turn a private certifier into a governmental authority.

**FR-TERM-180 — Cost/value module.** Trigger: an operative or asserted Cost or Value event. Extract valuation/cost kind; subject interest/project; valuation or measurement date; amount; currency; source type; as-is/as-complete status; assessed/appraised/sale/nominal distinction; incurred/budgeted/contracted status; payer/payee; and allocation scope.

**FR-TERM-190 — Modification/correction/release module.** Trigger: mode MODIFY, CORRECT, or TERMINATE. Extract target object id; exact field/scope changed; old value when stated; new value; unchanged clauses expressly preserved; released versus retained scope; reason/correction statement; and whether the obligation, security, filing, estate, or only priority is affected. "All other terms remain in effect" produces NO_CHANGE for unspecified fields only when a prior state exists within this same document fold; otherwise it is a preservation term and the unseen fields remain UNKNOWN.

## 12. Semantic nulls

Represent a semantic null as an object with sentinel, reason_code, and support. Never use bare null.

**FR-NULL-001 — UNKNOWN.** Use UNKNOWN when the field applies but the allowed inputs do not support one value, the text is illegible, same-rank evidence conflicts, or an allocation cannot be derived. Name the reason: NOT_STATED, ILLEGIBLE, CONFLICT, UNALLOCATABLE, UNSUPPORTED_BBL, or UNSUPPORTED_DATE.

**FR-NULL-002 — NOT_APPLICABLE.** Use NOT_APPLICABLE when the field cannot structurally apply to this event: for example rate on an easement with no payment obligation, from/to party lists on a non-directional assertion, or allocation of a single-target duration.

**FR-NULL-003 — ASSERTED_NONE.** Use ASSERTED_NONE only when the instrument expressly negates the field: no assignment, no new indebtedness, no rate, none, N/A in the named executed field, or an explicit absence assertion. Cite the negating words/mark.

**FR-NULL-004 — NO_CHANGE.** Use NO_CHANGE only in a MODIFY/CORRECT state_delta when the instrument expressly says that the named field or all other terms remain unchanged. It means carry a known prior value within the fold; it is not a substitute for a missing extraction value.

**FR-NULL-005 — No prior state.** Because each document is independent, an unseen prior value is UNKNOWN even when a modification says it continues unchanged. Matrix folding may carry only a value established earlier within the same event stream.

**FR-NULL-006 — Zero and empty collections.** Numeric zero is a value, not a null. An empty party/parcel/term array is allowed only when its status is NOT_APPLICABLE; otherwise populate UNKNOWN as the unresolved member.

**FR-NULL-007 — Matrix absence.** If a document supplies no event for a function, its initial matrix cell is UNKNOWN with reason NO_DOCUMENT_EVIDENCE. It is not NO_CHANGE, NOT_APPLICABLE, or ASSERTED_NONE.

## 13. Ambiguity, conflict, and review flags

**FR-AMB-001 — Field-local uncertainty.** When an event act is clear but one field is uncertain, emit the event and set only that field UNKNOWN. Do not make the whole event unresolved.

**FR-AMB-002 — Core uncertainty.** When function, mode, or affected BBL cannot be resolved after all applicable rules, retain one status UNRESOLVED package with candidate values and evidence. Do not emit mutually exclusive resolved events. matrix-spec.md keeps it outside resolved cells.

**FR-AMB-003 — Scope-specific conflict.** Before declaring conflict, test whether clauses concern different parties, parcels, objects, dates, quantity kinds, or released/retained scopes. If so, split or type them; they are not competing values.

**FR-AMB-004 — Express correction.** An express correction at the same or higher source rank supersedes the identified erroneous value under mode CORRECT. Preserve both as old/new; do not list a conflict.

**FR-AMB-005 — Allowed review flags.** review_flags may contain only:

- ILLEGIBLE_MATRIX_FIELD;
- CONFLICTING_SAME_RANK_EVIDENCE;
- CONFLICTING_EVENT_DATE;
- UNRESOLVED_CLASSIFICATION;
- UNRESOLVED_BBL;
- UNALLOCATABLE_TOTAL;
- MISSING_REQUIRED_EXECUTION_EVIDENCE;
- INCOMPLETE_DOCUMENT_IMAGE_SET.

Each flag requires affected paths and evidence ids. Do not flag a value merely because it required a difficult rule, because a term is absent, or because another classification could be argued after the rules decide it.

**FR-AMB-006 — Incomplete image set.** Compare supplied images to an explicit printed total only to detect missing images. When the package contains fewer images than a reliable cover says are in the stored instrument and the absent page could contain operative content, add INCOMPLETE_DOCUMENT_IMAGE_SET and mark validation failed. Do not infer the missing content.

## 14. Prohibited inferences

**FR-NOINF-001 — Prior/current ownership.** Do not infer that a grantor, mortgagor, assignor, declarant, record owner, or cover-page party actually held an interest beyond the role asserted in this instrument.

**FR-NOINF-002 — Party identity.** Do not merge spelling variants, affiliates, spouses, agents, trusts, banks, successors, or addresses unless this document expressly equates them.

**FR-NOINF-003 — Shares.** Do not infer equal, marital, joint, or proportional shares.

**FR-NOINF-004 — Parcel relation.** Do not infer adjacency, common ownership, dominant/servient status, zoning-lot membership, benefited/burdened status, or allocation from addresses or BBL sequence.

**FR-NOINF-005 — Dates.** Do not substitute preparation, acknowledgement, recording, tax-report, referenced-instrument, or database dates for event date except through FR-DATE-001 and FR-DATE-005.

**FR-NOINF-006 — Debt status.** Do not infer current balance from original principal; payment from lien release; lien release from debt payment; new money from maximum lien; consideration from principal; or debt termination from a UCC filing termination.

**FR-NOINF-007 — Terms.** Do not supply standard rates, maturity, lease expiration, priority, remedies, statutory effects, permit status, or customary clauses absent from the instrument.

**FR-NOINF-008 — Quantities.** Do not divide a total, convert nominal consideration to sale price, derive value from tax, infer currency, or copy one amount into another quantity kind.

**FR-NOINF-009 — Legal effect from label.** Registration type selects candidate modules; it does not prove an operative event. Read the operative clause. Conversely, an operative act controls even when the cover label is broad or wrong for legal-effect fields.

**FR-NOINF-010 — Present state from recital.** Do not treat a historical recital as a newly occurring event or as proof that the referenced state continued until this instrument, except for the current assertion expressly made.

**FR-NOINF-011 — Whole-parcel scope.** Do not upgrade a unit, facade, fixture location, easement area, air space, or partial lot to the entire BBL during fanning.

**FR-NOINF-012 — External law.** Do not import a statute, regulation, recorded declaration, credit agreement, note, lease, survey, map, or exhibit that is referenced but not included.

## 15. Deterministic quality checks

**FR-QC-001 — Page completion.** validation.pages_read lists every supplied page-NN exactly once. Failure blocks completion.

**FR-QC-002 — Event completeness.** Each event has every FR-REC-002 field; exactly one function/mode value or a supported UNKNOWN; at least one parcel entry or supported UNKNOWN BBL; effective date object; and at least one operative/assertion evidence atom.

**FR-QC-003 — Provenance closure.** Walk every scalar and sentinel. Each terminates in QUOTE support or RULE support whose input paths themselves pass. Derived canonical BBLs, normalized dates, normalized quantities, roles, functions, modes, and object keys require rule support.

**FR-QC-004 — Package coherence.** Events sharing an event_group_id must derive from one operative clause/act. They may differ by function but must use compatible effective dates, party set, and parcel transaction unless the split rule records why.

**FR-QC-005 — Quantity conservation.** For every quantity_id, serialize the normalized quantity once. Event references must not multiply its value. Explicit or derived component allocations must sum exactly to the total when the document says they exhaust it; otherwise do not run a sum check.

**FR-QC-006 — Null vocabulary.** Search all values for JSON null, blank strings, TBD, N/A as free text, NONE as free text, and omitted required fields. Replace only through section 12; a visible N/A remains in evidence but its extracted value is ASSERTED_NONE or NOT_APPLICABLE according to the mark's meaning.

**FR-QC-007 — Forbidden-fallback check.** If effective_date equals recorded_at, verify basis OPERATIVE_FILING and FR-DATE-005 support. Equality by coincidence does not permit a recording-date basis.

**FR-QC-008 — Function boundary check.** Apply all mandatory linked-function tests FR-FN-020 through FR-FN-025. Adding a linked event requires an independent state change; sharing one clause alone is insufficient.

**FR-QC-009 — Event order stability.** Re-run FR-REC-003 after edits. event_id order must match evidence and fixed function/mode order, not the extractor's discovery order.

**FR-QC-010 — Final outputs.** validation records PASS only when FR-QC-001 through FR-QC-009 pass or names the failing rule ids. A failed package remains deliverable with unresolved_items; never fabricate values to obtain PASS.
