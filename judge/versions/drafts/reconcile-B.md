# Block 1 reconciliation — Extractor B

Status: written after both committed drafts were published and before reading any reconciliation by A. I read A's four published files and B's four frozen files. I did not read A's reconciliation, private reasoning, transcript, working directory, or agent state. The frozen drafts remain unchanged.

Links: [A framework](A/framework.md) · [A matrix](A/matrix-spec.md) · [A survey](A/surveyed.md) · [A notes](A/draft-notes.md) · [B framework](B/framework.md) · [B matrix](B/matrix-spec.md) · [B survey](B/surveyed.md) · [B notes](B/draft-notes.md)

## 1. Bottom line

Neither draft can become v1 by editing around its edges.

- A is materially better on page inventory, package-shape awareness, registration-field citability, compact loading, zero-event cases, anti-flagging telemetry, and a human/canonical output contract. A also surveyed film, book, and Richmond material that B never saw.
- B is materially better on event object identity, provenance closure, typed quantities, affected-parcel scope, linked function effects, date intervals, semantic nulls, and especially the matrix. B actually folds CREATE/MODIFY/TRANSFER/TERMINATE/ASSERT/CORRECT into keyed state; A's “fold” is an ordered list of events in a cell.
- A's event record has an unconstrained payload. B's event record has state-delta paths but never defines the legal paths and value types per function. That missing state schema is the most important defect shared by the two designs: one is open at `payload`, the other at `field_ops.path`.
- The newly named downstream consumer changes the event record structurally. The record needs two temporal axes for observations, a separate epistemic character, sortable future boundaries, explicit condition status, same-instant relations, raw unresolved cross-document pointers, and a section-level coverage ledger. These are not six optional fields on either existing JSON shape.
- The primary/heavy reader design requires an operational routing contract outside final extraction output. Neither draft has one. A's flags and B's unresolved annexes cannot be relabeled “escalation.”
- A's measured build fits the approximate 15k ceiling; B's claim does not. By A's conservative `chars / 3.6` estimator, B's mandatory sections plus FR-TERM-100 and the matrix are about 21,186 tokens before a triggered term module. B must be cut and modularized.

My proposed v1 uses B's state-object/delta/fold architecture, A's input and loading discipline, a new closed state schema per function, and the new event/coverage/escalation contracts in sections 6–9 below.

## 2. Agreements to preserve

The drafts independently agree on the following. They need one concise v1 statement each, not parallel formulations:

1. One document is read independently from its supplied id, raw recorded details, and page images. No other instrument, parcel history, map, law lookup, or outside party data supplies a value.
2. Every supplied image is read, including appended supporting forms that a printed or registered page count may exclude.
3. Every extracted scalar or sentinel terminates in either a verbatim image/registration citation or a named rule with cited input paths.
4. Operative body text governs legal effect; cover and registration data govern only the indexing facts their fields actually assert.
5. A referenced instrument supplies a pointer and quoted attributes only. It never imports the referenced instrument's unseen state.
6. One clause can produce several linked single-function events. One amount can cover several events or parcels without being divided.
7. Party roles come from expressed roles/verbs, not panel order; plural parties do not imply equal shares.
8. Parcel direction matters. Granting/receiving and burdened/benefited parcels cannot be fanned symmetrically.
9. A partial release is a scoped modification, not termination of the entire object.
10. Missing terms remain semantic unknowns; unchecked or blank form fields do not assert absence.
11. Recording is not a generic event-date fallback. Under the principal's later instruction, it is never the applicable date at all.
12. Plausibility, customary New York terms, tax arithmetic using an unstated rate, and unstated current status may never fill a field.
13. Canonical output must make equal event tables resolve byte-identically and must conserve events, parcels, parties, quantities, and provenance.

## 3. Critical draft differences and my position

### 3.1 Loading and modules

| issue | A | B | v1 position and reason |
|---|---|---|---|
| Core budget | Measures core + one module + matrix at about 13.7–14k tokens (`§0`). | Says selective loading is below the ceiling but the actual mandatory bundle is about 21.2k by the same estimator (`FR-SCOPE-004`). | A is right to measure the exact bundle the reader holds. B's budget claim is false. Core + matrix must be measured mechanically in CI or a build script. |
| Number of modules | Exactly one type module. | Loads every module whose operative trigger matches. | B is right that hybrid instruments require more than one module. A's exactly-one rule fails a deed with an attached occupancy assertion, a mortgage plus rents assignment, or a declaration changing both common interests and facade obligations. |
| Module selection | Starts from `type`/`doc_type`, then instrument title, then generic. | Starts from registration type as a trigger but follows operative content. | Selection must run through the four-schema adapter, then confirm against the self-title and operative acts. Registration only nominates modules. A generic module must still execute the core clause/function tests; it cannot be “read and decide.” |
| Physical loading | Modules are heading ranges in one file. | Same. | Neither makes “load only this module” operational. Prefer a manifest and separate module files. If v1 is constrained to only `framework.md` and `matrix-spec.md`, a deterministic loader must extract named spans and report bundle ids, versions, hashes, and estimated tokens. |

The stronger production reader does not justify a larger silent core. It lets v1 delete scaffolding that tries to simulate weak-reader judgment, but it does not let v1 replace a decision procedure with “understand the document.” B's global subtype table, global term dictionary, and requirement to populate every core/module token on every event are examples of weak-reader over-scaffolding that create thousands of meaningless UNKNOWN/NOT_APPLICABLE decisions. Exact state schemas should live in the applicable modules instead.

### 3.2 Page inventory and evidence

A's R-INP-1 through R-INP-3 are better than B's single `pages_read` QC. V1 should retain a page inventory, image-number locators, supporting-form awareness, and the rule that supplied image count—not a printed or registered count—is the extraction inventory.

A's design still needs three changes:

1. `ILLEGIBLE` cannot be an exclusive whole-page class. A partly readable page may contain both operative text and unreadable fields. Store page class plus a separate legibility status and field/crop records.
2. Exact exhibit-label equality is a useful safe branch, not the entire incorporation procedure. A admits it silently discards cropped or unlabeled annexes; B uses “incorporated” without defining it. V1 needs ordered tests: an exact body/page label match; an explicit “annexed hereto” reference plus unique subject match; continuous executed pagination/title/signature or initial continuity; otherwise unresolved inclusion routed under the escalation contract if matrix-relevant. An uncertain page is not silently ADMIN.
3. A's 25-word quote cap and coarse zone alone are too weak for long conditions and dense pages. B's “shortest quote” and “unique visible anchor” are too subjective. Use an evidence registry, image page, controlled zone, occurrence ordinal within the zone, and the shortest span sufficient to prove the field with no fixed word cap. Normalize visual line breaks to single spaces but preserve characters, spelling, capitalization, punctuation, strike/handwriting status, and candidate readings.

B's evidence atoms and recursive provenance closure (`FR-EV-001`–`FR-EV-004`, `FR-QC-003`) are the better data model. A's per-field wrapper duplicates the same quote and has no shared evidence identity. V1 should use B's registry, with A's controlled source/location vocabulary.

On illegibility, B is right and A is wrong. A's R-INP-6a adopts the candidate that matches another input. That can launder a weaker registration transcription into unreadable legal text. Re-render/crop first; if the primary still has competing matrix-relevant transcriptions, escalate. Registration may be corroboration or a ranked source for its own field, never silent repair of body text. If the heavy reader also cannot resolve the characters, the final field is UNKNOWN/ILLEGIBLE with candidates. Scan failure is tracked separately from document ambiguity.

### 3.3 Registration and cover authority

A is much closer because R-INP-7 through R-INP-9 decide citability field by field and distinguish four package shapes. B's `registration_type`, `crfn`, `recorded_at`, and one generic rank table assume an ACRIS-shaped record.

A nevertheless contradicts itself: R-INP-8 says the body controls legal acts, while R-PARTY-1 takes a cover label, then Richmond registration role, then body verb. V1 must reverse that legal-role precedence. The body's operative grammar controls the event role. A cover label or Richmond index role is retained as `indexed_role`; it can fill the operative role only if the body expressly delegates to that label or a specific rule permits the lower-ranked source. Otherwise the legal role is UNKNOWN, not whatever panel metadata makes plausible.

Lower-ranked discrepancies are `source_discrepancy`, not automatically document ambiguity or a matrix conflict. Only incompatible values at the same controlling rank, after scope/type separation and express correction, create a document conflict.

The complete namespace adapter is specified in §7 below. A's statement that both FT and BK lack `doc_date` contradicts its own package table and the new facts: FT lacks it; BK has it. A's blanket non-citability statement is about `parcels[].remarks`; it must not swallow the top-level FT/BK `remarks` that carries raw cross-reference pointers.

### 3.4 Event schema and stable identity

A provides a readable example record but it is internally inconsistent: `quantity` is singular while R-QTY-2 permits several; `payload` is unconstrained; references, terms, and flags have no stable child ids; and merging preserves several clauses in a schema with one `clause`.

B's document-level party and quantity registries, `event_group_id`, `state_object_key`, `state_delta`, typed references, and provenance closure are better. B still fails executability because `field_ops.path` is open. Two readers may put a maturity in a Capital state path, a term only, an Encumbrance path, or two linked events and all appear locally conforming.

V1 needs a closed state schema per function, including legal path, value type, whether the path is state/observation/term-only, allowed modes, merge behavior, and which module extracts it. A's M-SER-3 key lists are a useful starting shape, not sufficient schemas. B's subtypes and term tokens are useful source material, not a substitute for the mapping.

Stable event identity should follow B's source order, not A's semantic date order. Date interpretation must not renumber every event. Segment the coverage ledger first; order candidates by section id, clause order, fixed function order, object order, then mode precedence; assign `doc_id-E###`. Re-extracting the same final event set produces the same ordinals. Events split across functions share a stable group id and section ids.

### 3.5 Event discovery, split, and merge

A's page-section exclusions and definitions-only handling are useful. Its R-SPLIT-4 merge is not a decision procedure: “payloads do not conflict” can merge two distinct objects, and A correctly predicted this would break first.

B's split dimensions—function, state object, mode, date, direction/share, and independent parcel transaction—are better. Use them, with these changes:

- A section can support several events, and several adjacent sections can support one event, but every merge requires the same state_object_key, function, mode, applicable-time object, party-direction set, affected BBL/scope set, and commuting state paths. Preserve all section ids and evidence. Similar parties/amounts/parcels never establish object sameness.
- B's within-document anaphora rule still needs a closed pointer test: reuse an object key only on exact recorded identifier, exact defined instrument-local name, exact section/schedule reference, or a demonstrative whose only grammatically available antecedent is that keyed object. Otherwise keep separate objects.
- A power of attorney, authority affidavit, or corporate resolution may legitimately produce zero events, but not because its registration type is on an authority list. Apply all function tests. When no state or observation path is filled, emit zero events and give a coverage-ledger reason.

### 3.6 Mode and epistemic character

B contains a direct precedence defect. It says “apply the first rule,” then lists CREATE and MODIFY before CORRECT. A correction that changes a field matches MODIFY before CORRECT. A's ordered test is the correct base: CORRECT → TERMINATE → TRANSFER → MODIFY → CREATE → ASSERT, with partial termination forced to MODIFY and competing scopes split before the test.

The principal's later distinction means mode is no longer enough. V1 needs two orthogonal fields:

| field | controlled values | question answered |
|---|---|---|
| `mode` | CREATE · MODIFY · TRANSFER · TERMINATE · CORRECT · ASSERT | What effect does this event have on the relevant state object? |
| `epistemic_character` | TRANSACTION · OBSERVATION · NOTICE | How does the document know or produce that effect? |

- TRANSACTION is an operative juridical/economic act: deed transfer, lien creation, modification, release, permit issuance, correction.
- OBSERVATION is evidence about a state without changing it: survey, appraisal, condition certification, actual-use report, assertion of absence.
- NOTICE records a pre-existing act or claim for notice/indexing without proving it was created now: memorandum, notice filing, UCC notice when the underlying security act is unseen.

Mode ASSERT can pair with OBSERVATION or NOTICE. A transaction normally pairs with the other five modes, but an operative declaration of present state may be TRANSACTION + ASSERT if the act legally establishes the declaration without creating the thing described. The module/state-path schema must settle such cases; the reader does not choose a fourth character.

This is a record-shape change in both drafts. It also changes folding: transactions compose into state; observations attach evidence with asserted valid time and never masquerade as creation/modification; notices attach a claim/pointer and do not import the unseen act.

### 3.7 Function boundaries

These differences change matrix cells and require settled calls:

| pattern | A result | B result | my v1 position |
|---|---|---|---|
| Secured finance | Capital + Encumbrance for originations, assignments, satisfactions as a class. | Emit each only if obligation and security are independently changed. | B. A makes the Capital column close neatly by inference. Evidence wins over column aesthetics. A mortgage can create both; assignment/release affects only what its words actually transfer/end. |
| Satisfaction/release | Always Encumbrance TERMINATE + Capital TERMINATE, including UCC termination module. | Capital terminates only if debt/payment/cancellation is express; UCC termination does not prove debt payment. | B. Lien/filing termination and obligation payment are independent fields. |
| Lease creation/assignment | Encumbrance on fee; Title only when a leasehold has its own indexed BBL; rent may create Capital. | Title because a leasehold is a possessory estate; rent stays a Title term absent separate finance. | B. A's own Title schema lists LEASEHOLD, then its module contradicts it. Do not infer an additional fee Encumbrance unless the instrument states a burden that fills that schema. |
| Common interest/restricted common element | No explicit Title branch beyond general schema. | Title when a unit's appurtenant common interest/exclusive-use element changes. | B; B's surveyed parking declaration is the concrete survivor. |
| Facade/form restriction without a number | Encumbrance only; Envelope requires a quantity/dimension. | Envelope + Encumbrance when physical exterior/form is constrained. | B. Envelope is physical form as well as a numeric metric. A nonphysical covenant remains Encumbrance only. |
| Zoning-lot composition certification | Identity only on change/difference/partial-lot triggers; declaration module tends toward entitlement/permit if application named. | Identity ASSERT for present composition/geometry; Entitlement only for capacity/right; Envelope only for bulk constraint. | B. A title-company geometry certification is not a government permit or capacity grant. |
| Application/agency named in a private declaration | Adds Entitlement + Permit broadly. | Permit requires an act by a named governmental authority authorizing work/operation. | B. A reference to an application is a pointer/term, not issuance. A land-use approval can be Entitlement without being a work Permit. |
| Private use restriction | May fall into Occupancy's broad lawful-use question. | Encumbrance; Occupancy separates ACTUAL from AUTHORIZED and needs an express basis. | B. |
| Sale price/consideration | Consideration, sale price, tax, and fees are Cost; Value excludes money paid. | Sale/nominal consideration are Value kinds; Cost is project/construction/operation expenditure. | Use B for sale price and nominal consideration as distinct Value measurements, and for project expenditure as Cost. Taxes/filing fees remain typed quantities attached to the relevant transaction unless an operative clause creates a cost obligation; they do not get a Cost event merely because paid. |
| Deed covenant against grantor's acts | Encumbrance ASSERT/ASSERTED_NONE. | General warranties produce no event; named present burdens may assert Encumbrance. | B. A title covenant is a Title term and scoped promise, not evidence that the parcel has no encumbrances. An explicit present assertion of no named/other burdens is an OBSERVATION + Encumbrance ASSERT with verbatim scope. |
| Identity from routine/partial description | Fires for partial indexed lot or body/registration designation difference. | Routine legal description is scope; Identity needs creation/change/present formal identity assertion. | B. A source discrepancy or partial premises is not an identity-changing event. |
| Contract of sale | Encumbrance CREATE kind OPTION by module. | No categorical rule. | Neither categorical rule is safe. Emit a right/option/encumbrance only if the operative words expressly create that path; never import equitable-conversion doctrine. |
| Supporting tax/use/equipment form | Several ASSERT events. | ASSERT only when a current state path is expressly stated; basis typed. | Retain assertions, with OBSERVATION character and asserted valid time. A form attachment does not create events solely by type. |

The global function procedure should be B's “test every function and link independent effects,” backed by closed per-function paths. It must not force a single primary function when two paths are genuinely filled. Conversely, sharing a clause is not sufficient for two events.

### 3.8 Dates, temporal extent, and conditionality

A is right to record all observed dates and to keep commencement/maturity/option dates distinct from the event's point. B is better on required-party execution, partial-date intervals, and not forcing undated events into a dated row.

Both old positions need changes:

- Withdraw B's FR-DATE-005 exception. Per the principal, the applicable date is never the recording/filing timestamp. `recorded_at` remains a registry fact and can prove only recording, not when the represented world-state applied.
- Reject A's matrix use of recording as `date_bound_latest` sort position. Marking it `~` does not undo the invented chronology.
- Do not promote registration `doc_date` or an RP-5217 sale date automatically. A cover Document Date is a lower-ranked candidate for the present instrument date; it becomes applicable only under an explicit module/date rule and is never available in FT/Richmond registration where absent. FT with no document-supported applicable date remains undated.
- Keep B's closed date intervals for DAY/MONTH/YEAR. Never pad a partial date to the first day. Overlapping intervals form an unordered time component unless explicit ordering language supplies a relation. B's connected-component approach is conservative but can let a broad year bridge precise dates; v1 should document that cost and include a conformance fixture.
- Promote same-instant ordering out of B's generic term list into top-level `ordering_relations[]`: BEFORE, AFTER, SIMULTANEOUS, each naming event/group ids, carrying the exact words and evidence. Page order, mode order, registration time, and event id are serialization tie-breaks only.

The event needs three temporal structures, not one overloaded date:

1. `applicable_time`: when the transaction/observation/notice occurred, with value/interval, precision, basis, and status DATED · PARTIAL · UNDATED · CONDITION_DEPENDENT.
2. `asserted_valid_time`: for OBSERVATION/NOTICE, the interval the document says the observed state was true. A 2020 survey describing a condition “since 1960” is evidence about that stated interval, not a 2020 state change. If no separate valid time is stated, it is UNKNOWN, not copied from observation date by assumption.
3. `temporal_boundaries[]`: sortable dates embedded in the object—COMMENCEMENT, MATURITY, EXPIRATION, OPTION_OPEN, OPTION_CLOSE, RENEWAL_DEADLINE, or OTHER_NAMED—with consequence, condition, and evidence. A boundary is not automatically a future TERMINATE event. The next phase may sort it without treating maturity as satisfaction or an option deadline as exercised.

Conditionality is not UNKNOWN. An operative clause whose effect depends on an unresolved condition emits a conditional event with `applicability.status = CONDITION_DEPENDENT`, a verbatim trigger and consequence, and no fabricated date. It goes to a conditional chronology lane and does not fold into unconditional state. If the same document states the condition occurred, record the occurrence evidence and dated effect. This replaces B's rule that future conditional acts are only terms and A's undifferentiated consequence-term handling.

### 3.9 Parties

B's raw/normalized party registry and separation of operative entity from representative are better. A's uppercase-only names lose evidence; B preserves it. A's legacy examples add two necessary refinements:

- A single person/entity has one party id when the exact raw name repeats or the document explicitly equates names, but may have several participation records for distinct roles/capacities. Do not duplicate identity merely because the same person acts individually and as trustee/custodian.
- A beneficiary/minor named only inside a capacity phrase is not an operative party unless an operative clause gives that person a right/obligation. Preserve the capacity text and index discrepancy.

Use body operative roles first. Keep A's deduplicated registration coverage check as QA only; Richmond's repeated case variants and inverted custodian indexing must not create parties or overwrite roles. Both drafts' no-share rule survives.

### 3.10 Parcels and BBL attribution

A is right that document-level parcel inventory may be a union: Richmond may print one lot and say additional lots while registration enumerates them. A is wrong to default every undistinguished event to that union without an affected-scope test.

V1 should separate:

- `parcel_inventory`: every body/cover/registration parcel candidate with source and discrepancy;
- `event.parcels`: only BBL/scope pairs the operative/assertion section affects.

Use B's affected-set procedure. An explicit operative subset controls a broader cover; when the clause applies to the whole recorded premises, indexed parcels may complete that premises. B's 16-BBL declaration with four changed unit interests demonstrates why A's unconditional union over-fans.

B's role/scope vocabularies are stronger: SUBJECT, GRANTING, RECEIVING, BURDENED, BENEFITED, SERVIENT, DOMINANT, COLLATERAL_LOCATION, DECLARED_COMPONENT, UNIT_APPURTENANT, and scopes including UNIT/FACADE/AIR_SPACE/EASEMENT_AREA. ADJOINING and REFERENCED belong in references/inventory and are never fanned unless separately affected.

For Richmond, a bare BBL gives canonical lot identity but not extent. Extent is UNKNOWN/NOT_STATED, not NOT_APPLICABLE and not ENTIRE_LOT. Slate-derived borough is never evidence. An event with no supportable BBL remains an event in an unplaced-parcel queue and coverage counts; it is never silently dropped or attached by address.

### 3.11 Quantities

B's document registry, semantic kind separation, scope, allocation status, and conservation are the correct base. A's singular event quantity cannot represent its own deed example and duplicates group totals through `ALLOCATION_NOT_DERIVABLE` placeholders.

V1 must repair B's draft details: define the quantity record once; include PAYOFF as a kind; define symbol-only currency representation; say where TAX/FEE quantities live when they do not create a Cost event; and close target schemas for event/parcel/party allocations.

Derived allocation or consolidation is allowed only when the document supplies an exhaustive relationship/formula and every input. A's permission to sum plausible component principals merely because a consolidation is present is too broad. If the document also states the total, the arithmetic is a validation, not the source of the total. One total remains one registry object regardless of event or BBL fan-out.

A's deed consideration ladder must not survive. Presenter-reported `registration.amount` is a separately typed indexed amount. It cannot resolve body nominal consideration or overwrite an RP-5217 amount. The source discrepancy remains visible.

### 3.12 Terms and state paths

A's required Capital/Encumbrance term block is compact but too narrow for leases, easements, permits, observations, and corrections. B's modules cover those classes much better, especially lease remaining term/common interest, UCC filing scope, facade duties/conditional termination, and correction old/new values.

B's implementation is too large and disagreement-prone: it populates every core token and every token in every triggered module, causing structurally irrelevant NOT_APPLICABLE decisions and making almost every cell PARTIAL because referenced UNKNOWN terms become touched paths.

V1 should give each module:

- a closed list of applicable state paths and term paths;
- the evidence trigger for each path;
- value type and normalization;
- whether absence means UNKNOWN or the path is structurally absent;
- fold behavior and temporal-boundary promotion;
- function/mode/character compatibility.

Only paths in triggered modules exist for that event. A missing applicable path is UNKNOWN. A path outside the triggered schema is absent, not a serialized NOT_APPLICABLE token. NOT_APPLICABLE remains an explicit structural result where the schema asks a conditional question and the stated inputs prove the branch cannot apply.

### 3.13 Nulls

The drafts disagree fundamentally. A uses NO_CHANGE in every cell untouched by the document. B starts independent state as UNKNOWN/NO_DOCUMENT_EVIDENCE, uses NO_CHANGE only as an express field operation, and carries established state forward.

B is right for a state matrix. Silence does not establish a prior state that can remain unchanged. V1 should distinguish:

- event coverage: NO_EVENT for a section/function after a rule-backed exclusion;
- event delta: NO_CHANGE only when the document expressly preserves a named field/terms in MODIFY/CORRECT;
- initial resolved state: UNKNOWN/NO_DOCUMENT_EVIDENCE;
- later empty row cell: carry the prior document-established state, with derived provenance;
- ASSERTED_NONE: explicit scoped absence, emitted as an OBSERVATION + ASSERT event when it is content;
- NOT_APPLICABLE: a rule-proven structural branch, not A's requirement that the document state “a condition making the function valueless.”

A's whole-document null repeated in every row is temporally wrong: an absence assertion dated after another event cannot populate earlier moments. B's time-aware fold is required.

### 3.14 Ambiguity, validation, and zero-event documents

A's admission discipline and emitted/flagged ratio are better than B's open-ended review flag list. A correctly says framework silence is not a document flag. A incorrectly combines image unreadability with document ambiguity.

B is better at keeping uncertainty field-local and preserving core-unresolved packages, but moving hard events to annexes without rates can buy matrix agreement by omission. Under the new load-bearing tags, a missing function/BBL/date cannot yield PASS merely because it is in an annex.

Track distinct outcomes:

- resolved emitted fields/events;
- document ambiguity/conflict;
- image illegibility;
- unplaced BBL/date/function events;
- framework/schema gap;
- validation failure;
- model escalation.

Zero-event/no-parcel packages remain valid only when the coverage ledger proves every section was handled and no section filled a function path. A's `no_events_reason` is useful; B's requirement that each event have a parcel cannot govern a document that correctly emits no events.

## 4. Matrix reconciliation

### 4.1 A's matrix is not a state matrix

A calls M-FOLD-1 a fold, but it joins event strings and explicitly does not merge at fold time. It cannot calculate the state of a mortgage after CREATE → MODIFY → TRANSFER → TERMINATE, apply a correction to one field, preserve unrelated terms, or keep several liens distinct. It is an event grid.

B's keyed object map, lifecycle, field operations, coverage, history, carry, partial release, and same-path conflict rules are the correct architecture. They must be retained after the per-function state paths are closed.

### 4.2 Fan

Use B's fan: one projection per exact affected BBL/scope, merged role array on the same pair, partial scope preserved, quantity references conserved, unknown BBL routed visibly. A's fan can duplicate one event for several roles and can fan ADJOINING/REFERENCED parcels.

Document-level union belongs before event scope; it is not the fan set. Fan conservation must prove every eligible event has exactly its distinct affected BBL/scope projections and every ineligible projection is in a counted queue.

### 4.3 Sort and same-instant order

- Sort on `applicable_time`, never recording time.
- Exact dates order normally. Disjoint partial-date intervals order; overlapping intervals form an unordered component.
- UNDATED and CONDITION_DEPENDENT events remain separate, counted chronology lanes. Neither is folded into dated unconditional state.
- Apply only explicit BEFORE/AFTER relations as legal order. SIMULTANEOUS creates one unordered group. A's mode index and B's event-id/function order are serialization tie-breaks only.
- In one unordered group, disjoint object/path changes commute; identical values coalesce; incompatible lifecycle or same-path values produce a local conflict. Never last-write-wins by page/event order.

The purchase-money-mortgage example must not be solved by customary knowledge. If the documents say “simultaneously herewith” or “immediately after/prior,” capture it. If they do not, the events are same-instant unordered even if a lawyer expects deed-before-mortgage.

### 4.4 Fold transactions, observations, and notices differently

The matrix needs two layers per function object:

1. `composed_state`: only TRANSACTION events apply lifecycle/field deltas.
2. `evidence_assertions`: OBSERVATION and NOTICE events attach asserted values/absence, observation time, asserted valid time, scope, and provenance. They do not create, modify, transfer, or terminate transactional state.

An assertion may corroborate, conflict with, or be silent about composed state. It never overwrites a transaction by being later in serialization. An explicit correction of an observation corrects that assertion record; it does not rewrite historical transactions.

Temporal boundaries are rendered/sorted as boundary records. They alter state only when the document expressly makes the boundary self-executing and the module's fold rule permits it. Mortgage maturity does not equal lien termination; option close does not prove exercise; lease expiration may be conditional on renewal/holdover terms.

### 4.5 Baseline and carry

Initial state is UNKNOWN/NO_DOCUMENT_EVIDENCE. After an event establishes a path, later rows carry it with derived provenance. NO_CHANGE is not a substitute for carry. Inactive objects remain visible with termination history.

### 4.6 Unplaceable events

B's unresolved/undated annex is better than dropping events, but under the consumer contract it cannot count as a successful resolved matrix. A load-bearing tag with competing readable candidates triggers escalation. If the heavy reader concludes the document itself is ambiguous, preserve the candidate event and mark the extraction `UNPLACEABLE_DOCUMENT_AMBIGUITY`; do not fabricate a function/BBL/date. Such a package goes to an exception queue and is counted. A genuinely absent applicable date is `UNPLACED_UNDATED`, not escalation and not recording-date substitution. Conditional events have their own lane and are not “undated.”

### 4.7 Serialization

B's lossless canonical JSON rules, registries, input hash, input-order reversal test, fan/quantity conservation, and dual-render validation are stronger. A's canonical cell text is lossy: delimiter replacement and quote truncation can make different values compare equal, and omitted null cells hide distinctions.

TRAYCER currently requires `resolved.md`. V1 should put a human table and a fenced canonical JSON or canonical JSONL block inside `resolved.md`, or explicitly authorize a sibling `resolved.json`. The machine comparison uses the lossless canonical structure; the Markdown table may abbreviate with stable ids and an audit section. This output-file choice is an orchestrator/principal contract question, not a semantic compromise.

Canonical output must include all eleven cells per dated row plus undated, conditional, unplaced, conflict, boundary, quantity, party, and external-reference sections. It must distinguish composed state from observations.

## 5. Where A is plainly better than B

1. **Measured loading contract.** A counted core, module, and matrix together. B quietly exceeded the stated ceiling.
2. **Legacy corpus exposure.** A opened FT, BK, and Richmond images and registrations. B's survey is deeper page-by-page but almost entirely 2002–2003 ACRIS.
3. **Page/package mechanics.** A explains supporting pages beyond printed count, image locators, cover types, marginal stamps, film scans, and four package shapes. B assumes the package is already semantically inventoried.
4. **Field-level registration citability.** A names non-evidence fields and distinctions B leaves in a generic rank table.
5. **Anti-flagging discipline and ratios.** A's admission test and emitted/flagged telemetry are a better base, after illegibility is separated.
6. **Concrete function cell keys.** A at least says what a function cell is intended to hold. B's open state paths are a blocking omission.
7. **Zero-event handling and party coverage QA.** A explicitly makes an authority-only result auditable and tests body parties against the index without letting the index control.
8. **Required output shape.** A keeps a canonical comparison representation inside the required `resolved.md`; B adds a file the workflow did not name.

These are not concessions for symmetry. Each prevents a concrete failure B's draft would miss.

## 6. What the newly named downstream consumer changes

### 6.1 Three placement keys are hard requirements

Every event needs a single resolved `function`, one or more affected `bbl` entries, and an `applicable_time` status/value. None may be an omitted field.

- A readable classification conflict on one of the three routes to the heavy reader.
- A genuinely absent BBL/date remains an explicit unplaced event and makes the extraction non-PASS for chronology placement; it is never replaced by address, inferred borough, or recording date.
- A framework gap is not escalation and not a document flag. It blocks the bundle/version and enters framework-repair telemetry.
- A document ambiguity that survives escalation remains a cited exception, not a guessed placement.

B's `UNRESOLVED` packages and matrix annex were a partial answer, but B allowed them alongside matrix PASS. That must change. A forced a mode/function through ordered tests but had no safe core-unresolved representation. V1 needs both the ordered decision procedures and the explicit exception queue.

### 6.2 Cross-document pointers: capture, never resolve

Both drafts have `references`, but neither makes the downstream seam complete across schemas. V1 needs a top-level registry of external pointers. Each record contains:

- `external_ref_id`;
- `relation_raw` (amends, substitutes, assigns, satisfies, corrects, derives from, or OTHER_NAMED);
- `locator_raw` verbatim;
- separately derived locator components when explicitly parseable: CRFN, borough/year/reel/page, reel_page, book/page, instrument, map sequence, or OTHER;
- source kind and exact registration path or page evidence;
- `resolution_status: UNRESOLVED_BY_EXTRACTION`;
- current event ids that carry the pointer.

The extraction never supplies a target event id, current target status, resolved document id, or imported target facts. The next cross-document phase may resolve it. Current instrument identifiers and target cross-references are different records.

Required sources include ACRIS cover `CROSS REFERENCE DATA`, top-level FT/BK remarks such as `SUBSTITUTE MTGE REEL 595 PG 713` and `D BOOK/PAGES: 156/36`, Richmond book/page/instrument fields when they express the referenced locator, ACRIS digital CRFN, and operative-body references. Registration remarks prove only that the register carries that pointer; they do not prove the referenced act's contents.

B's state_object_key may use the raw normalized locator to keep current events about the same named target together, but that is an extraction-local key, not cross-document resolution.

### 6.3 Required event shape

The reconciled event record must at least contain:

| group | required content |
|---|---|
| identity/coverage | stable event id, group id, coverage-section ids, framework/module bundle hash |
| placement | one function, affected BBL/scope/role entries, applicable time and basis |
| effect/knowledge | mode, epistemic character, state object key, state delta or assertion payload |
| temporal | asserted valid time, temporal boundaries, conditionality, same-instant/order relations |
| participants | party ids, operative roles/capacities, FROM/TO/NONE sides, shares, directional boolean |
| economics/terms | quantity ids, typed applicable terms, allocations/scopes |
| continuity | raw unresolved external-reference ids and current recording identity |
| proof/status | evidence ids or rule/input derivations, field conflicts, document ambiguity, placement/validation status |

This is a restructuring of A's record because its `payload`, date, quantity, terms, and reference objects cannot express state mapping, observation valid time, or shared registries. It is also a restructuring of B's record because B lacks epistemic character, promoted boundaries, conditional placement status, top-level order relations, a coverage ledger, and closed state paths.

### 6.4 Assertions of absence are events

An explicit assertion that no encumbrance, assignment, permit, occupancy, equipment, or other state-path value exists is OBSERVATION + ASSERT, with function, BBL/scope, applicable observation time, asserted valid time if stated, parties, and verbatim scope. Its state value is ASSERTED_NONE. It is not an empty cell and not a document-wide null painted across all rows.

A recognized this for a scoped deed covenant but over-generalized the covenant into a parcel-state assertion. B's FR-PKG-002/semantic nulls can carry it but did not require event emission. V1 should emit only when the clause grammatically asserts current absence of a function path, not merely promises against the grantor's own acts or leaves a form blank.

### 6.5 Coverage ledger

Neither draft supplies the required section-level ledger. A has page inventory; B has `pages_read`. V1 needs both, then deterministic section segmentation:

1. Assign page ids from supplied image order.
2. Within each page assign section ids in reading order to headings, paragraphs, numbered/lettered clauses, form fields/rows, signature blocks, acknowledgments, exhibits, and administrative regions that could be separately classified.
3. Every section record has its page/span, class, legibility, and exactly one disposition:
   - `EVENT` with one or more event ids;
   - `VALUES_ONLY` with paths/event ids receiving its definitions/terms;
   - `REFERENCE_ONLY` with external_ref ids;
   - `NO_EVENT` with a controlled rule-backed reason: ADMINISTRATIVE, BLANK, SIGNATURE_ONLY, ACKNOWLEDGMENT_ONLY, NOTICE_ADDRESS, DEFINITION_ONLY, HISTORICAL_RECITAL_ONLY, BOILERPLATE_EXCLUDED, DUPLICATE_DISPLAY, or OTHER_RULED with rule id;
   - `UNRESOLVED_SECTION` which cannot receive PASS and may trigger escalation if reader-resolvable.
4. Ledger QC proves every supplied page and section appears exactly once and every event/value/reference points back to at least one section.

This makes “missed” mechanically different from “read and excluded.” Coverage counts must include pages, sections, event-bearing sections, no-event sections by reason, unresolved sections, emitted fields/events, document flags, illegible fields, and escalated documents. The denominator is no longer whatever the extractor happened to emit.

## 7. Four recorded-details schemas

V1 needs a normalization adapter whose output names are stable but whose citations retain raw key paths. Schema is selected by id namespace, not by the presence of a convenient key.

| schema | normalize | explicit absences/limits | evidence rules |
|---|---|---|---|
| ACRIS digital (`2002…`+) | `type`, `doc_date`, `crfn`, recorded time, panel-indexed parties, parcel bbl/partial/use/address/unit | Panel number has no operative-role meaning. | `doc_date` is an indexed document-date candidate, not automatically applicable time. Parcel attributes and CRFN prove index facts. |
| Richmond (`RC_`) | `doc_type`, recorded time, explicit indexed party `role`, bare parcel BBLs, book/page/instrument | No `pages`; no registration `doc_date`; no partial/unit/address/use on bare parcel. Extent is UNKNOWN, not NOT_APPLICABLE or ENTIRE_LOT. | Role proves index attribution only. `image_state` and `status` are non-citable pipeline/status data. Cover image may separately state Document Date. |
| Film (`FT_`) | type field actually present in the raw record, recorded time, `reel_page`, top-level `remarks`, parcel data whose `use` may be literal `PRE-ACRIS` | No `doc_date`. No cover assumed. | `remarks` may supply a verbatim unresolved cross-reference only. `PRE-ACRIS` is an index/source marker, never Occupancy or actual property use. |
| Book film (`BK_`) | as FT plus `doc_date`; top-level remarks such as `D BOOK/PAGES: 156/36` | No cover assumed. | `doc_date` remains indexed document date, not recording and not automatic applicable time. Remarks supply pointers only. |

Common rules:

- `at`, URLs, local keys, retrieval timestamps, `image_state`, `status`, and selector/slate fields are never semantic evidence.
- Registration `recorded` is citable as the recording fact only and never applicable time.
- Missing schema keys are represented in adapter metadata, not confused with document assertions. A Richmond missing partial flag means UNKNOWN extent because extent is applicable but unstated.
- Raw and normalized registration are both retained; derivations cite raw field paths plus adapter rule ids.
- The adapter never resolves a top-level remark's referenced instrument.

This new requirement breaks B much more than A. B's registration envelope and source ranks must be replaced, not extended with aliases.

## 8. Primary/heavy escalation contract

### 8.1 Separation from document flags

Escalation is an operational route, not a semantic output. The primary must first produce a complete provisional extraction and coverage ledger; it may not replace work with `ESCALATE`.

- A final document flag means the supplied evidence itself remains ambiguous/conflicting/illegible after the same framework and both tiers.
- An escalation means the primary has a bounded, evidenced reader-resolution problem that the heavy reader can retry.
- Framework silence, missing evidence, a blank field, a genuinely absent date/BBL, and a clear same-rank document conflict are not escalations.

Routing metadata lives in an operational sidecar/telemetry store and is absent from final `extraction.json` and the resolved matrix. The heavy result, once validated, becomes the answer; final provenance remains quotes/rules, never “the heavy model said so.”

### 8.2 Allowed triggers

Escalate a document once when at least one record meets one of these finite tests:

1. `VISUAL_CANDIDATES`: after the mandated original render and one high-resolution crop/reread, a required field has two or more transcriptions; at least two remain graphically possible; and the alternatives change a placement key, mode/character, state path, quantity/term, external pointer, or coverage disposition.
2. `RULE_BRANCH_CANDIDATES`: the primary names one cited input passage and two different existing rule branches whose discriminating words are present but it cannot resolve which grammar/object they attach to; each candidate is fully specified and the outputs differ semantically. “No rule covers this” is FRAMEWORK_GAP, not escalation.
3. `MODEL_VALIDATION_FAILURE`: after one deterministic self-repair pass, coverage, required-field, schema, or provenance closure still fails because the model omitted/mislinked supplied readable content. A missing page, corrupt package, or framework contradiction is not model-actionable and does not qualify.
4. `CONTEXT_LINK_FAILURE`: the package exceeds the configured primary bundle/chunk limit and, after the required two-pass section/reference protocol, one or more exact cross-section links remain unresolved. The trigger carries the involved section ids. It is not “long document.”

Uncertainty with reason NOT_STATED, UNSUPPORTED_DATE, UNSUPPORTED_BBL, UNALLOCATABLE, or explicit document conflict does not trigger by itself. No free-text “hard/uncertain” trigger exists.

### 8.3 Payload

The immutable escalation payload contains:

- document id, raw recorded-details hash, page-manifest/image hashes, schema-adapter version;
- framework, matrix, module ids/versions and exact bundle hash;
- primary provisional extraction, coverage ledger, validation report, and canonical candidate matrix diff;
- trigger records with code, affected JSON paths/section ids, rule ids, candidate values/event packages, evidence ids, and why each candidate changes output;
- all page images for context-link/validation failures, or the relevant full pages plus lossless crops for visual/branch failures;
- an allowlist of paths/event sections the heavy answer may replace.

No slate row, other document, prior parcel state, resolved pointer, outside lookup, or unstated law is included.

### 8.4 Heavy task

The heavy prompt says: apply the identical frozen bundle to the identical inputs; reread the named evidence/sections; adjudicate each trigger as exactly one of RESOLVED, DOCUMENT_AMBIGUITY, INSUFFICIENT_EVIDENCE, or INVALID_TRIGGER; return replacement values or complete replacement event packages for the allowed sections; cite evidence ids and rule/input paths; do not change the framework, use outside information, resolve external references, edit unrelated paths, or escalate again.

The heavy model may identify an additional event only inside a section already marked unresolved/validation-failed, and must return the coverage-ledger disposition it replaces. It cannot opportunistically rewrite the rest of the document.

### 8.5 Merge-back

1. Validate heavy output against schema, allowed scope, citation/provenance closure, coverage conservation, and all QC.
2. RESOLVED replaces the provisional values/event packages only within scope. DOCUMENT_AMBIGUITY or INSUFFICIENT_EVIDENCE replaces them with the correct semantic null/candidates/final document flag. INVALID_TRIGGER retains the primary conforming answer and records an operational false-escalation outcome.
3. Recompute affected registries, stable final event ordering/ids, dependencies, fan, sort, fold, and canonical serialization from the merged event table. Never patch a matrix directly.
4. If heavy output is invalid, retry the heavy serialization once without new reasoning. A second invalid response is an operational extraction failure/exception queue, not a document ambiguity flag and not a silently accepted primary result.
5. Strip routing metadata from final artifacts.

### 8.6 Telemetry and budget discipline

Track at least:

- `escalation_rate = documents_sent_to_heavy / primary_documents_attempted`;
- rate by schema, stratum, module, page-count band, and trigger code;
- heavy resolution yield, document-ambiguity yield, invalid-trigger rate, heavy override rate, and escalation-failure rate;
- emitted-to-document-flagged, illegible, unplaced, and framework-gap ratios separately.

The numerical Torch budget/cap has not been supplied. It must be an external versioned production configuration and reported with the ratios; the model must not see the running rate and suppress a legitimate trigger to meet a quota. The finite admission tests—not a model judgment that a document is difficult—are the first defense against escalation-everything.

## 9. Selection after the slate completes

A's census and proposed 13-parcel mortgage were thoughtful but are invalid as the agreed first selection now: the full deterministic slate was not complete, the corpus slice was skewed, and A had already seen adjacent types/periods. B supplied no first id.

Selection remains OPEN until the orchestrator confirms the build complete. Then both agents should record:

- slate build/version and database fingerprint/hash;
- exact `facets`, `pick --where`, and `show` commands;
- chosen stratum and why it broadens surveyed coverage;
- deterministic candidate list/order and selected id;
- ids excluded because either agent already opened them;
- the exact rule/state-path/matrix behavior expected to break.

The selected document's extraction input is still only raw recorded details and page images. The slate, its inferred Richmond borough, facet counts, and selection annotations are never cited or copied into extraction.

My preference for the first round is now an unsurveyed non-ACRIS or mixed-schema stratum with readable images, but I will not nominate an id before completion. Film legibility should not be allowed to confound the first semantic test unless both agree that escalation/illegibility is the intended rule under test.

## 10. What the new facts break in B's frozen draft

This is the direct autopsy of my own design, separated from the A/B choices above.

1. **Reader and coherence.** I wrote for a weaker mid-size floor and compensated with a global subtype dictionary, a global term dictionary, and mandatory population of every core/module term. The stronger primary does not need that scaffolding, and at 25M documents it creates a larger inconsistency surface. At the same time, I left the genuinely load-bearing state paths open. I specified too much vocabulary and too little state grammar.
2. **Escalation.** My `review_flags`, `UNRESOLVED` packages, and annexes have no primary/heavy routing semantics. They can hide a hard event outside the matrix and make agreement look better. They also mix document ambiguity, reader uncertainty, illegibility, and framework failure. None can be renamed to satisfy the new contract.
3. **Recorded-details schemas.** My envelope assumes `registration_type`, `crfn`, `recorded_at`, and a generic registration shape. It has no RC/FT/BK adapter, no explicit Richmond missing-partial behavior, no handling of `doc_type`, `reel_page`, `book/page/instrument`, top-level remarks, or `PRE-ACRIS`. This is a replacement, not an alias patch.
4. **Size.** My loaded core plus FR-TERM-100 and matrix is about 76,269 characters, roughly 21,186 tokens by A's conservative estimator, before a triggered module. FR-SCOPE-004's assurance that selective loading stays under the ceiling is factually wrong.
5. **Applicable time.** FR-DATE-005 lets recording/filing date become event date when filing is the act. The principal's “applicable date, never recording date” rule invalidates it. My undated annex is temporally honest, but an annexed event was still allowed in a nominally PASS matrix.
6. **Consumer shape.** My event record lacks epistemic character, asserted valid time, promoted temporal boundaries, top-level order relations, conditional placement status, a raw external-pointer registry, and a section coverage ledger. `terms` and `references` cannot safely absorb these because the next phase needs to sort and resolve them directly.
7. **Assertions.** I could represent ASSERTED_NONE as a field and qualifying ASSERT event, but did not require an explicit absence assertion to become a scoped observation event. It could be reduced to a null and disappear from chronology.
8. **Internal executable defects.** My first-match mode list places CREATE/MODIFY before CORRECT; the quantity record is defined twice with different field names and omits PAYOFF from the controlled list while discussing it; `related_event_ids` is required in prose but absent from the event shape; required arrays refer to companion status fields not in that shape; state-delta paths are open; and matrix acceptance blocks only provenance-closure failure rather than every validation failure that affects placement/fold.
9. **Output contract.** I require `resolved.json` in addition to the workflow's named `resolved.md` and make the human cell unbounded. The lossless canonical representation is worth keeping, but the output-file and bounded-rendering contract needs an explicit decision.

These defects remain true even where B's underlying idea is preferable. They are not reasons to fall back to A's event grid.

## 11. Gaps neither draft covered

1. Closed, typed state paths and fold behavior for all eleven functions.
2. Orthogonal mode and epistemic character, with bitemporal observation handling.
3. Sortable temporal-boundary records distinct from state transitions.
4. Structured conditional events/lane rather than UNKNOWN date or prose-only terms.
5. Complete section-level coverage ledger and controlled no-event reasons.
6. Namespace-complete schema adapter and field-level handling of FT/BK top-level remarks.
7. Raw cross-document pointer registry and a strict non-resolution seam.
8. Primary/heavy escalation admission, payload, prompt, merge-back, failure handling, and telemetry.
9. A physically executable module loader/manifest and bundle hash.
10. Conformance fixtures/reference implementation for extraction-to-delta mapping and matrix fan/sort/fold/serialization.
11. A production failure policy for genuinely unplaceable BBL/function/date events; v1 should mark them non-PASS and retain them rather than pretending the matrix is complete.
12. A lossless canonical representation that fits the required output-file contract and a bounded human rendering.

Minimum conformance fixtures before the first live round should cover: same-day unsequenced conflicting deltas; undated versus condition-dependent event; partial year overlapping precise dates; same BBL with different scopes/roles; partial release; lien release without debt-payment words; transaction plus observation; observation with earlier asserted valid time; assertion of absence; mixed-act multi-module package; zero-event/no-parcel package; incomplete page/section ledger; FT/BK/Richmond registration; cross-reference remark kept unresolved; and a condo cover whose operative subset is smaller than the indexed set.

## 12. Deadlock and non-negotiable objections

There is no genuine interpersonal deadlock yet because I have not read A's reconciliation and written exchange has not occurred. Two external choices need the orchestrator/principal if not already fixed:

1. whether v1 may add physical module files and/or a sibling `resolved.json`, or must encode both through the two named Markdown files;
2. the numerical escalation budget/cap and reporting window.

My positions above are not halfway compromises. I would object to v1 if it:

- uses A's event-list grid as the resolved state matrix;
- uses recording time, a padded partial date, or a recording-bound placeholder as applicable chronology time;
- treats an unresolved condition as ordinary UNKNOWN date;
- omits epistemic character or folds observations as transactions;
- lacks closed function state paths;
- lets type-level expectations create Capital termination, Permit, lease Capital, contract-sale encumbrance, or other effects not stated;
- defaults an event to every parcel in the document union despite an operative subset;
- treats cover/index party roles as superior to body grammar;
- uses registration to repair unreadable legal text;
- resolves external pointers during extraction;
- allows unplaced events to disappear into an annex while reporting PASS;
- aliases flags, ambiguity, illegibility, framework gaps, and escalation;
- exceeds the measured core bundle ceiling or asks the reader to load a monolithic term dictionary;
- selects the first document before the complete deterministic slate is confirmed.

Those objections follow from concrete failure cases in the two surveys and the named downstream consumer, not from preference for B's wording.
