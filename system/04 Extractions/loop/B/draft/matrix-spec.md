# NYC C.R.E.D. Resolved Matrix Specification v1-B

Status: isolated Block 1 draft. This specification consumes one event table conforming to framework.md and produces a deterministic resolved-state matrix. It does not re-read the instrument, reinterpret evidence, or repair extraction errors.

## 0. Matrix contract

**MX-SCOPE-001 — Unit of resolution.** The matrix describes document-supported state by affected BBL and time batch. Rows are time batches. Columns are the eleven fixed functions. A cell contains a map of state objects; it is not a single winning event.

**MX-SCOPE-002 — Fixed function order.** Use this order everywhere: Identity, Title, Entitlement, Envelope, Encumbrance, Capital, Permit, As Built, Occupancy, Cost, Value.

**MX-SCOPE-003 — No external baseline.** Each document is folded independently. Before its first event, every BBL/function cell has status UNKNOWN and reason NO_DOCUMENT_EVIDENCE. Do not obtain a baseline from another document, a parcel history, registration chronology, or outside knowledge.

**MX-SCOPE-004 — Accepted input.** Accept an event table only when its framework_version is v1-B, all required fields exist, every event_id is globally unique, every RESOLVED event has one non-UNKNOWN state_object_key, and validation does not name a provenance-closure failure. Repeated state_object_keys are required when several events affect the same object. A package may contain UNRESOLVED events and field-level UNKNOWN values; those are valid inputs handled below.

**MX-SCOPE-005 — Execution order.** Apply, in order: input validation; BBL fanning; time normalization; batch construction; total ordering; folding; cell-status calculation; serialization; output validation. Never sort or fold before fanning.

## 1. Projection and BBL fanning

**MX-FAN-001 — Projection shape.** A projection contains projection_id, event_id, event_group_id, bbl, parcel_scope, parcel_roles, function, mode, state_object_key, effective_date, parties, direction, quantity references, terms, state_delta, support, conflicts, and review_flags. It points to the source event; it does not copy a quantity into a new quantity object.

**MX-FAN-002 — Fan procedure.** For each RESOLVED event, group its parcel entries by exact pair (canonical BBL, scope). Emit one projection per pair. Merge roles for that pair into a deduplicated array sorted by the controlled role order SUBJECT, GRANTING, RECEIVING, BURDENED, BENEFITED, SERVIENT, DOMINANT, COLLATERAL_LOCATION, DECLARED_COMPONENT, UNIT_APPURTENANT. Set projection_id to event_id followed by /P and the one-based BBL/scope group number after lexical sorting by BBL then scope.

**MX-FAN-003 — Same BBL, different scope.** Keep separate projections when one event affects different scopes on the same BBL, such as UNIT and FACADE. The cell may later contain both projections under the same state object; their scopes remain separate in that object's coverage array.

**MX-FAN-004 — Partial scope preservation.** Fanning maps an act to the tax lot used as a matrix row key. It never changes UNIT, PARTIAL_BBL, AIR_SPACE, FACADE, EASEMENT_AREA, or DESCRIBED_PREMISES into ENTIRE_BBL.

**MX-FAN-005 — Quantities under fan.** Every projection retains quantity_id references and the quantity's original scope and allocation_status. An INSTRUMENT_TOTAL, MULTI_EVENT_TOTAL, or unallocated multi-parcel total is serialized once in the quantity registry and referenced from every applicable projection. It is never represented as a parcel amount. A parcel amount exists only when its allocation_status is EXPLICIT or DERIVED and its target identifies that BBL/scope.

**MX-FAN-006 — Party and parcel roles.** Fanning does not turn parcel roles into party direction. GRANTING/RECEIVING, BURDENED/BENEFITED, and SERVIENT/DOMINANT remain parcel attributes. from_party_ids and to_party_ids remain exactly those of the event.

**MX-FAN-007 — Unknown BBL.** An event with UNKNOWN canonical BBL emits no resolved projection. Serialize it once in the unresolved-parcel annex with its event_id, legal-description/unit data, function candidate, mode, date, and reason. It does not create an UNKNOWN-BBL matrix.

**MX-FAN-008 — Unresolved core classification.** An event whose status is UNRESOLVED or whose function, mode, or state_object_key is UNKNOWN emits no resolved projection. Serialize it once in the unresolved-classification annex. Field-level UNKNOWN values in an otherwise RESOLVED event do not block projection.

## 2. Time normalization, sorting, and tie-breaks

**MX-TIME-001 — Date interval.** Represent each supported date as the closed interval [interval_start, interval_end] supplied by framework.md. A complete day has equal endpoints. Reject an interval whose end precedes its start. Preserve value, precision, and basis.

**MX-TIME-002 — Undated events.** An UNKNOWN effective date emits no dated projection. Serialize the projection in the undated annex, grouped by BBL and function. It must not change any dated cell because its position relative to dated acts is unknowable.

**MX-TIME-003 — Overlap component.** For each BBL, sort dated projections by interval_start, then interval_end. Sweep from left to right. Start a component with the first interval and maintain component_end as the maximum end seen. Add the next projection to that component when its interval_start is less than or equal to component_end; then extend component_end if needed. Otherwise start a new component. Each component is one time batch.

**MX-TIME-004 — Batch label.** If every projection in a batch has the same complete date, label it YYYY-MM-DD. Otherwise label it [minimum interval_start..maximum interval_end]~UNCERTAIN. The latter means ordering inside the connected interval component is not established; it does not assert that all acts were simultaneous.

**MX-TIME-005 — Express sequence.** Within a time batch, an ordering relation exists only when the event table contains an explicit sequence term supported by the instrument, such as “immediately after,” ordinal steps, or one act expressly effective after another. Build a directed graph of those relations. A cycle produces ORDER_CONFLICT for the involved objects and moves the competing deltas to the conflict annex.

**MX-TIME-006 — Legal fold groups.** Topologically layer the express-sequence graph. Events with no path ordering one before the other occupy the same legal fold group. Apply groups in graph order. Events in the same group are unordered and combine under the simultaneous rules in section 4; their serialization tie-break never creates a legal sequence.

**MX-TIME-007 — Deterministic output tie-break.** Within one legal fold group sort projections for output by: interval_start; interval_end; fixed function order in MX-SCOPE-002; mode order CREATE, MODIFY, TRANSFER, TERMINATE, ASSERT, CORRECT, UNKNOWN; event_id; projection_id. The event_id already encodes operative evidence page and reading order under FR-REC-003. This is only a total serialization order.

**MX-TIME-008 — Across-BBL order.** Sort BBL matrices by canonical ten-digit BBL ascending. Batches within a BBL sort by their component interval_start, then interval_end, then batch label. Do not use recording time or document id to break semantic date ties.

**MX-TIME-009 — Date/sequence contradiction.** When an explicit EVENT_SEQUENCE edge says A precedes B but A's interval starts after B's interval ends, mark ORDER_CONFLICT for both projections and do not use the edge to reorder dates. A consistent edge across non-overlapping batches is redundant and needs no within-batch fold relation.

## 3. Cell and state-object model

**MX-CELL-001 — Cell shape.** A cell has status, reason, objects, applied_event_ids, and flags. objects is a map keyed by state_object_key. Each object contains lifecycle, assertion_basis, fields, holders, obligors, coverage, quantity_refs, term_refs, source_event_ids, and object_conflicts. Map keys and arrays use the ordering rules in section 6.

**MX-CELL-002 — Object lifecycle.** lifecycle is UNKNOWN, ACTIVE, INACTIVE, or CONFLICT. ASSERT events do not prove creation and therefore retain UNKNOWN lifecycle unless the assertion expressly states active/existing status as a field. CREATE sets ACTIVE. TERMINATE sets INACTIVE. MODIFY, TRANSFER, and CORRECT preserve a known lifecycle and leave an unseen lifecycle UNKNOWN.

**MX-CELL-003 — Initial object.** When the first event for an object is MODIFY, TRANSFER, CORRECT, or TERMINATE, instantiate the object with lifecycle UNKNOWN and the event's stated delta. Do not generate an open-ended list of unseen fields. An applicable field that the extraction requires but the document omits is already present as UNKNOWN under framework.md. TERMINATE may set lifecycle INACTIVE because the present act states termination, while prior existence and prior terms remain UNKNOWN.

**MX-CELL-004 — Coverage.** coverage is a set of records (bbl, scope, parcel_roles, unit, share). A projection adds or updates only its own BBL/scope coverage. A partial release removes or marks released only the expressly identified scope. It never deactivates unrelated coverage.

**MX-CELL-005 — Multiple objects.** Objects coexist within a function cell. A new object never overwrites a different object merely because function, parties, amount, or BBL match. One cell can therefore contain multiple liens, estates, values, permits, or assertions.

**MX-CELL-006 — Document-touched path.** The document-touched paths for an object are exactly: paths named by any of its field_ops; lifecycle; coverage records supplied by its projections; holder/obligor interests changed by TRANSFER; and the status/value of quantity or term records carried by those events. A referenced quantity or term with status/value UNKNOWN therefore makes the cell PARTIAL. No other path is invented for status calculation.

## 4. Fold semantics

**MX-FOLD-001 — Carry.** Begin each batch from the immediately preceding resolved cell for that BBL/function. Copy its object map and add source notation CARRY@prior-batch to unchanged objects. For the first batch, use MX-SCOPE-003. A function with no event in a later row carries exactly; it is not NO_CHANGE.

**MX-FOLD-002 — Projection application.** Apply a projection only to its function column and state_object_key. Add event_id to source_event_ids and applied_event_ids. Merge its coverage record and references, then apply lifecycle and ordered field_ops. Never apply one linked function's fields to another linked function.

**MX-FOLD-003 — CREATE.** ACTIVATE sets lifecycle ACTIVE and applies SET, REMOVE_ASSERTED, and UNKNOWN field operations. Existing values not named by the delta remain as they were. A CREATE on an already ACTIVE object is not silently idempotent: identical deltas coalesce; incompatible lifecycle or field assertions use MX-FOLD-010.

**MX-FOLD-004 — MODIFY.** PRESERVE retains lifecycle and all fields not named. SET replaces only the named path. REMOVE_ASSERTED sets that path to ASSERTED_NONE with the event's support. UNKNOWN sets that path to UNKNOWN with its stated reason/candidates. NO_CHANGE carries the known value at that path; if no known value exists, the result remains UNKNOWN/NO_PRIOR_STATE.

**MX-FOLD-005 — TRANSFER.** Preserve the object and all unmodified terms. Add each TO party as holder/obligor of the transferred interest. Remove a FROM party's entire interest only when the text says all/entire or transfers the unqualified whole named state object with no partial or retained-interest qualifier. When a fractional transfer is stated, reduce only that stated share. When extent is applicable but unstated, record transferred share UNKNOWN and remaining FROM interest UNKNOWN; do not assume equal shares. An assumption adds the assuming obligor without deleting an existing obligor unless release is express.

**MX-FOLD-006 — TERMINATE.** DEACTIVATE sets lifecycle INACTIVE for the expressly terminated object and coverage. Preserve prior fields and mark termination_event_id and termination_scope. A partial release represented as MODIFY follows MX-FOLD-004. Termination does not set debt paid, balance zero, holder absent, or collateral absent unless separate field operations expressly say so.

**MX-FOLD-007 — ASSERT.** OBSERVE applies stated fields with assertion_basis ASSERTED and leaves lifecycle UNKNOWN unless the asserted field itself is status. An assertion may coexist with operative state. It replaces a prior asserted value for the same object/path only when later in an express legal fold group; otherwise conflicts are handled under MX-FOLD-010.

**MX-FOLD-008 — CORRECT.** Apply new_value or explicit deletion to the named path and preserve the identified old_value in correction_history with event_id. CORRECT supersedes only the value identified as erroneous. It does not rewrite event history or unrelated fields.

**MX-FOLD-009 — Commuting unordered deltas.** In one legal fold group, deltas commute when they address different object keys, different non-lifecycle paths, or identical values with compatible lifecycle operations. Combine them and sort provenance. An event_group_id does not itself impose order.

**MX-FOLD-010 — Unordered conflict.** For the same object/path in one legal fold group, two non-identical SET/REMOVE_ASSERTED/UNKNOWN outcomes are CONFLICT unless one is an express correction of the other. Incompatible lifecycle operations, including unsequenced ACTIVATE and DEACTIVATE, are CONFLICT. Store all candidates with event_ids; do not apply last-write-wins using page order, function order, mode order, or event id.

**MX-FOLD-011 — Ordered change.** Between express legal fold groups, later groups apply to the prior group's result. A later supported SET may replace an earlier value without conflict. History retains both event ids and values.

**MX-FOLD-012 — Semantic nulls.** UNKNOWN creates uncertainty at only the named path. ASSERTED_NONE is an observed negative value. NOT_APPLICABLE is a structural value and cannot be replaced by a non-applicable omission. NO_CHANGE is an operation, never a stored state value. JSON null, blank, and missing required paths are invalid.

**MX-FOLD-013 — Quantities.** Fold only quantity semantics named by a field_op; merely referencing a quantity does not overwrite a state field. Preserve every typed quantity and its scope. Different quantity kinds coexist. Same-kind/same-scope conflicts follow MX-FOLD-010. Unallocatable totals remain joint references and never become parcel values.

## 5. Cell status

**MX-STAT-001 — Status precedence.** Calculate cell status after each batch in this order: CONFLICT if any object lifecycle or document-touched path is CONFLICT; PARTIAL if at least one object exists and any document-touched path defined by MX-CELL-006 has value UNKNOWN; ASSERTED if all supported objects in the cell arise only from ASSERT events; RESOLVED if at least one object exists and every document-touched path is single-valued; UNKNOWN if no object has document evidence. ASSERTED_NONE is a field value, not a cell status.

**MX-STAT-002 — Unknown baseline.** A carried UNKNOWN cell remains UNKNOWN/NO_DOCUMENT_EVIDENCE until an event supplies an object. NOT_APPLICABLE is not a valid whole-cell replacement because a later document event could still affect any fixed function.

**MX-STAT-003 — Inactive objects.** A cell containing only determinately INACTIVE objects is RESOLVED when their document-touched fields are single-valued. Serialization must show the inactive objects; do not render the cell as empty or ASSERTED_NONE.

**MX-STAT-004 — Conflict locality.** A conflict in one object/path makes that cell CONFLICT but does not contaminate another function, BBL, object, or batch. Later express-order events may resolve a field prospectively; prior conflict history remains recorded.

## 6. Canonical serialization

**MX-SER-001 — Output files.** Produce resolved.md and resolved.json from the same in-memory matrix. resolved.json is canonical for machine comparison. resolved.md is a deterministic human-readable view. A conforming comparison checks canonical JSON equality first; Markdown differences alone are renderer defects.

**MX-SER-002 — JSON envelope.** Serialize keys in this order: matrix_spec_version, framework_version, document_id, bbl_matrices, party_registry, quantity_registry, unresolved_parcel, unresolved_classification, undated, conflicts, validation. Copy only party records referenced by a projection or annex and preserve their event-table ids. Use UTF-8 without BOM, LF line endings, two-space indentation, and one terminal LF.

**MX-SER-003 — Canonical scalar forms.** Dates use YYYY-MM-DD. Closed uncertain intervals use separate interval_start and interval_end. Money and other exact decimals serialize as quoted base-10 strings without grouping commas or exponent notation; remove leading plus signs and trailing fractional zeros, but retain one zero before a decimal point. Rational fractions serialize as quoted reduced numerator/denominator. Booleans are true/false. Sentinels are uppercase strings.

**MX-SER-004 — Key and array order.** Preserve the envelope key order in MX-SER-002 and the declared field order for typed records. Sort otherwise unordered map keys by Unicode code point after normalization. Sort event ids, party ids, quantity ids, term ids, roles, flags, and candidate values lexically after deduplication. Preserve document order only for ordered field_ops, expressly sequenced acts, and verbatim evidence.

**MX-SER-005 — BBL matrix JSON.** Each BBL record contains bbl, batches. Each batch contains label, interval_start, interval_end, order_basis, and cells. cells contains exactly the eleven function keys in MX-SCOPE-002 order. No cell is omitted and no value is blank.

**MX-SER-006 — Markdown layout.** Write the title, version/document header, then one section per BBL. Under each BBL render a table with columns Time followed by the eleven functions in MX-SCOPE-002 order. Use one row per batch. After matrices, render in order: Party Registry, Quantity Registry, Unresolved Parcel, Unresolved Classification, Undated, Conflicts, Validation. Emit “NONE” only as a renderer token for an empty annex; it is not a semantic field value.

**MX-SER-007 — Compact cell rendering.** Render a cell as STATUS followed by its objects sorted by state_object_key. For each object show key, lifecycle, holders/obligors when applicable, coverage scope, document-touched fields, quantity ids, and source event ids. Render UNKNOWN and CONFLICT reasons/candidates inline. Escape vertical bars as &#124;, backslashes as two backslashes, and line breaks as a single space. Do not truncate values.

**MX-SER-008 — Provenance.** The matrix may cite event_ids instead of repeating page quotes, because the event table is the provenance registry. Every derived carried or folded value records source_event_ids and fold rule ids. resolved.json validation includes input_event_table_sha256 so the matrix can be joined to the exact extraction.

**MX-SER-009 — Empty corpus case.** If no event fans to a canonical BBL, bbl_matrices is an empty array and resolved.md has no BBL table. Applicable unresolved annexes still serialize. Do not invent a row for registration BBLs not assigned to an event.

## 7. Deterministic algorithm and validation

**MX-ALG-001 — Reference algorithm.** A conforming implementation performs this exact loop:

1. Validate the event table under MX-SCOPE-004.
2. Fan every eligible event under section 1; route ineligible events to annexes.
3. For each BBL, route UNKNOWN dates to undated; build dated overlap components under MX-TIME-003.
4. In each component, build express ordering layers; fold each layer under section 4 from the prior resolved cell.
5. Calculate all eleven cell statuses after each component and carry untouched columns.
6. Sort all registries and annexes under section 6; render JSON and Markdown.
7. Run MX-QC-001 through MX-QC-008.

**MX-QC-001 — Fan conservation.** For each eligible event, projection count equals its distinct canonical BBL/scope pairs. Every projection points back to exactly one event. Every ineligible event appears exactly once in its applicable annex.

**MX-QC-002 — Quantity conservation.** Each quantity_id occurs once in the quantity registry. Projection and object references do not create additional numeric values. No NOT_DERIVABLE total appears as a parcel allocation.

**MX-QC-003 — Ordering reproducibility.** Reversing input event-array order must produce byte-identical resolved.json. If it does not, a hidden input-order tie-break exists and validation fails.

**MX-QC-004 — No fabricated sequence.** Every non-simultaneous edge within a date batch cites an explicit sequence term. Serialization order alone never appears as order_basis.

**MX-QC-005 — Fold trace.** Every document-touched field in every object identifies the event_ids and one of MX-FOLD-003 through MX-FOLD-013. Every carried value identifies its prior batch.

**MX-QC-006 — Cell completeness.** Every dated row has exactly eleven cells. Every cell has status, reason, objects, applied_event_ids, and flags. An absent function is UNKNOWN or carried, never blank.

**MX-QC-007 — Annex exclusion.** No unresolved-BBL, unresolved-core, or undated projection changes a dated resolved cell. Its source event_id appears in its annex and nowhere in applied_event_ids.

**MX-QC-008 — Dual-render agreement.** Parse resolved.json and the unescaped semantic content of resolved.md. BBLs, batches, cell statuses, object keys, lifecycles, document-touched fields, quantities, events, and annex membership must match. validation is PASS only when MX-QC-001 through MX-QC-008 all pass; otherwise name every failing rule id.
