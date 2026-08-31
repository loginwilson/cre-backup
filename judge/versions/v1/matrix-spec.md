<!-- MATRIX:SCOPE SEPARATE_RESOLUTION_READER R-6a -->
# NYC C.R.E.D. resolved matrix specification v1

This specification consumes a closed set of one or more completed v1 `extraction.json` files plus the exact immutable module schemas named by their bundle manifests, and produces `resolved.md`: parcel chronologies with time down, the eleven functions across, and a lossless canonical block. A one-file set is the loop/test case; a corpus set enables deliberately deferred cross-document continuity. Resolution never discovers events or supplies missing extraction fields. All event-producing rules and path schemas live in the extraction bundle.

## 0. Contract and execution order

**MX-SCOPE-001 — Accepted input set.** Sort a supplied manifest by document id then extraction SHA-256. Require one file per document id, strict canonical envelopes, one framework version, valid lanes/registries/coverage/ids, and exact adapter/module text whose hashes match each bundle manifest; use that text only for declared path types and merge policies. Duplicate ids or differing bytes for one id are `INPUT_SET_CONFLICT`. A `FAIL` input yields no state projections but keeps its exception report; an `EXCEPTION` input contributes eligible material while preserving every excluded item. Either keeps matrix validation non-PASS.

**MX-SCOPE-002 — Fixed order.** Functions always appear as `IDENTITY`, `TITLE`, `ENTITLEMENT`, `ENVELOPE`, `ENCUMBRANCE`, `CAPITAL`, `PERMIT`, `AS_BUILT`, `OCCUPANCY`, `COST`, `VALUE`.

**MX-SCOPE-003 — Three state inputs.** The state compiler receives only:

1. unconditional transaction projections with supported applicable intervals;
2. dated-observation projections containing asserted-valid intervals and assertion payloads, never occurrence/statement times;
3. temporal-boundary projections.

`observations_unplaced`, `notices`, `conditional_events`, `evidence_time_registry`, unresolved classifications, undated transactions, and unplaced parcels remain physically separate inputs to audit/exception renderers. They are not handed to the state sorter.

**MX-SCOPE-004 — Order of work.** Run: input gate → current-recording index → reference/object-continuity resolution → fan → physical stream compilation → interval components → state-action order graph → state fold → evidence/informational-boundary attachment → status → exception/audit lanes → canonical serialization → QC. Serialization tie-breaks never become semantic order.

**MX-SCOPE-005 — One-BBL production unit.** Indexing, exact reference lookup, and fan are deterministic coordination steps. A production fold invocation receives this spec, exact module schemas, and one canonical BBL's complete projections/registries/reference resolutions, including exactly resolved target records; it receives no other BBL history. Multi-BBL loop output runs the same fold independently per ascending BBL and concatenates the canonical BBL objects. No state operation crosses BBL jobs.

## 1. Fan to affected BBL/scope

**MX-FAN-001 — Transaction projection.** For each transaction, group its affected parcel records by exact `(canonical_bbl, scope)` and emit one projection per group. Sort groups by BBL then scope and assign `<event_id>/P001`…. Merge that pair's role array in controlled role order. The projection carries source document/event/group ids, extraction and matrix object ids, function, mode, object type, mandatory Title interest kind, applicable interval, parties/direction, state delta, quantity/term/reference ids, support, and conflicts. Parcel inventory is never a fan source.

**MX-FAN-002 — Dated-observation projection.** Apply the same exact BBL/scope grouping/id procedure to `observations_dated`. Copy asserted-valid interval, function/object/interest kind, assertions, ids, scope, and provenance. Do not copy `evidence_time_id` or any occurrence/statement date. Reject a projection that exposes either.

**MX-FAN-003 — Boundary projection.** Fan a boundary only to its own affected BBL/scope records; assign `<boundary_id>/P001`… by BBL then scope. Carry boundary/object/event id, function, boundary type/interval, consequence, condition, effect status, and any admitted boundary delta. A boundary has no party/quantity inference of its own.

**MX-FAN-004 — Scope conservation.** Fanning preserves `UNIT`, `PARTIAL_BBL`, `AIR_SPACE`, `SUBTERRANEAN_SPACE`, `FACADE`, `EASEMENT_AREA`, `DESCRIBED_PREMISES`, and UNKNOWN scope. Same BBL with different scopes produces different projections. Several parcel roles on one exact pair produce one projection, not several.

**MX-FAN-005 — Quantity conservation.** Projections reference existing quantity ids. `INSTRUMENT_TOTAL`, `MULTI_EVENT_TOTAL`, and every `NOT_DERIVABLE` total remain one registry record and never acquire a parcel amount. Only an `EXPLICIT` or `DERIVED` allocation naming that BBL/scope can appear as parcel value.

**MX-FAN-006 — Ineligible placement.** Unknown BBL routes document/source id once to `unplaced_parcel`; unknown transaction time routes each otherwise fanned pair once to `undated_transactions`; unresolved function/mode/object routes once to `unresolved_classification`. None enters a dated state stream. Duplicate routing is invalid.

## 2. Cross-document reference and object continuity

**MX-LINK-001 — Current-recording index.** Index each input by supplied `DOC_ID` and its `current_recording_identity` components: `CRFN`, `FILE_NUMBER`, `BOOK`, `PAGE`, `INSTRUMENT`, `REEL`, `YEAR`, and `BOROUGH`. Match only typed components already present in an external-reference record. Every supplied component must equal the corresponding normalized target component; omitted components are not invented. Do not use document type, relation words, amount, party, BBL, date, or chronology to choose a document.

**MX-LINK-002 — Pointer resolution.** For each external reference, retain the extraction record unchanged and emit one matrix resolution record. No parseable locator gives `UNPARSEABLE`; zero matching input identities gives `TARGET_OUTSIDE_INPUT`; one gives `DOCUMENT_RESOLVED`; more than one gives `DOCUMENT_AMBIGUOUS`, with every candidate id. A relation label never breaks a tie. Resolution points to an input document only—not to unseen contents—and records source/target extraction hashes.

**MX-LINK-003 — Continuing-object test.** For a source transaction in mode MODIFY, CORRECT, TRANSFER, or TERMINATE whose reference has `DOCUMENT_RESOLVED`, consider target-document transaction events with the same function, same Title interest kind when applicable, and at least one exact affected BBL/scope pair. Select a target object only on the first satisfied row: (1) an exact cross-document object identifier supported in both extractions selects its one target; (2) otherwise exactly one candidate object remains after the stated filters. Zero or several candidates is `CONTINUITY_UNRESOLVED`; do not use party, amount, proximity, customary sequence, or similar names to break it. Notices and CREATE/ASSERT events may link to the document for audit but never alias an object by this rule.

**MX-LINK-004 — Matrix object identity.** Create one node per `(document_id,state_object_key)` and a directed continuation edge from the source node to the unique MX-LINK-003 target node. Reject an edge across function, Title interest kind, or disjoint BBL/scope. Acyclic components with exactly one sink use `matrix_object_id = MO:` plus SHA-256 of that sink's canonical `(document_id,state_object_key)`; an unlinked node is its own sink. A cycle, several target edges from one source, or several sinks is `CONTINUITY_UNRESOLVED` and creates no union. Keep every extraction key/member. This root id remains stable when later continuations are added. An amendment/correction folds prospectively at its own applicable time and never rewrites the target event or an earlier batch.

## 3. Time streams and same-instant order

**MX-TIME-001 — Sort keys.** Transaction projections use only `applicable_time.interval_start/end`. Observation projections use only `asserted_valid_time.interval_start/end`. Boundary projections use only their boundary interval. Recording time, occurrence time, evidence-time id, document id, event id, page order, and mode are forbidden as chronology keys.

**MX-TIME-002 — Interval components.** For each BBL, initially order all eligible projections by interval start then end. Sweep left to right, maintaining the maximum end in the current component. Add a projection when its start is on/before that maximum; otherwise begin a new component. A component is one uncertain time batch. Thus a broad year can bridge precise dates; the output marks the component uncertain rather than inventing order.

**MX-TIME-003 — Batch ids and labels.** After component ordering, assign `<bbl>-R001`…. If every projection in a component has one identical complete day, label `AFTER YYYY-MM-DD`; otherwise label `AFTER [minimum_start..maximum_end]~UNCERTAIN`. The composed layer is the state after all nonconflicting state actions in that component, not a claim that it held throughout the displayed interval. Preserve each source interval and add cell reason `TIME_COMPONENT_UNCERTAIN` for the latter label.

**MX-TIME-004 — State-action order graph.** Nodes are transaction projections and `SELF_EXECUTING` boundary projections in one interval component. For every pair whose source intervals are disjoint, add `INTERVAL_BEFORE` from the earlier end to the later start. Add extraction ordering relations whose transaction event/group endpoints are in the component; normalize AFTER to BEFORE. SIMULTANEOUS joins transaction endpoints only when their intervals overlap. An express edge opposite an interval edge, a disjoint SIMULTANEOUS relation, or a directed cycle is `ORDER_CONFLICT`; affected deltas receive no invented order. Dated observations and informational boundaries are not graph nodes.

**MX-TIME-005 — Partial-order fold.** Collapse valid simultaneous nodes and compute reachability. For every two state-action nodes with no path either way, test commutativity under MX-FOLD-010. A noncommuting incomparable pair is `ORDER_CONFLICT`; preserve its candidate deltas without choosing a sequence. Topologically fold conflict-free nodes, using MX-TIME-006 only among ready nodes already proven to commute. Dated observations and informational boundaries attach after the state-action fold and never create an edge.

**MX-TIME-006 — Deterministic tie-break.** Among proven-commuting ready nodes and for serialization, order by interval start, interval end, function order, source kind `TRANSACTION` then `BOUNDARY`, mode order `CORRECT`, `TERMINATE`, `TRANSFER`, `MODIFY`, `CREATE`, `ASSERT` when present, source id, projection id. Across BBLs use ascending ten-digit BBL. This order is output-only and cannot resolve a conflict.

**MX-TIME-007 — Separate nonstate chronologies.** `observation_occurrence_audit` may display evidence-time registry records ordered by their own evidence times, clearly labeled `EVIDENCE_TIME_ONLY`; it contains no state cell. Notices may be ordered in a `notice_lane` by supported notice occurrence time, otherwise id. Conditional events order only by supported boundary/condition dates and remain `CONDITION_DEPENDENT`. None is merged into BBL composed-state rows.

## 4. Cell and object model

**MX-CELL-001 — Cell shape.** Each dated BBL/function cell contains `status`, `reason`, `composed_state`, `evidence_assertions`, `boundaries`, `applied_transaction_ids`, `observation_ids`, `boundary_ids`, and `conflicts`. The last three id arrays are sorted/deduplicated.

For functions other than Title, `composed_state.objects` is a map keyed by `state_object_key`. Title instead uses `composed_state.objects_by_interest_kind`, whose first keys are mandatory interest kinds and whose second keys are object keys. A generic `title.holders` list is forbidden.

**MX-CELL-002 — State object.** An object is keyed by `matrix_object_id` and contains every extraction object key/member, object type, function, Title interest kind when applicable, lifecycle (`UNKNOWN`, `ACTIVE`, `INACTIVE`, `CONFLICT`), module-typed fields, holder/obligor interest ledgers when applicable, exact coverage records, quantity/term/reference ids, history, source document/event ids, and field conflicts. Different matrix object ids always coexist.

**MX-CELL-003 — Initial state.** Before the first eligible transaction, composed state is `UNKNOWN/NO_DOCUMENT_EVIDENCE`; no unseen object/field is generated. A first MODIFY/TRANSFER/CORRECT instantiates only its keyed object and touched paths with lifecycle UNKNOWN. A first TERMINATE may set lifecycle INACTIVE because the present act states termination, while all unseen prior attributes remain unknown.

**MX-CELL-004 — Coverage.** Coverage records are exact `(bbl, scope, roles, unit/share when stated)`. A projection touches only its pair. Partial release changes only named coverage. Unknown scope remains unknown; it cannot expand to whole lot.

**MX-CELL-005 — Layer firewall.** `composed_state` receives transactions and admitted self-executing boundary deltas only. `evidence_assertions` receives dated observations only. Notice, unplaced observation, evidence occurrence, and conditional content has no field path into either layer.

## 5. Fold

**MX-FOLD-001 — Carry.** Start a batch from the immediately prior batch's composed object maps for that BBL/function. Retain unchanged values and append `CARRY@<prior_batch>` provenance. A function untouched in a later row carries; before any transaction it remains UNKNOWN. `NO_CHANGE` is not used for ordinary carry.

**MX-FOLD-002 — Projection target.** Apply a transaction projection only to its function, matrix object id, and exact coverage. Add source extraction keys/ids/references, then execute lifecycle and ordered module-admitted field operations. Linked events in other functions never share state fields.

**MX-FOLD-003 — CREATE.** `ACTIVATE` sets lifecycle ACTIVE and applies supported `SET`, `REMOVE_ASSERTED`, and `UNKNOWN` operations. Unnamed paths are not generated. CREATE on an already ACTIVE object coalesces only identical commuting deltas; incompatible lifecycle/path outcomes use MX-FOLD-010.

**MX-FOLD-004 — MODIFY.** `PRESERVE` retains lifecycle and untouched paths. `SET` changes the named path, `REMOVE_ASSERTED` stores scoped ASSERTED_NONE, `UNKNOWN` makes only that path unknown, and `NO_CHANGE` carries a known value at that exact path. With no known value, NO_CHANGE yields UNKNOWN/NO_PRIOR_STATE.

**MX-FOLD-005 — TRANSFER.** Preserve object identity and unmodified paths. Module interest-ledger operations add supported TO interests. Remove a FROM interest wholly only on express all/entire or an unqualified whole-object transfer with no retained/partial qualifier. Apply exact stated fractions; applicable unstated extent makes transferred and retained interests UNKNOWN. Assumption adds an obligor unless express release removes one.

**MX-FOLD-006 — TERMINATE.** `DEACTIVATE` sets the exact object/coverage INACTIVE and records termination event/scope. Preserve historical attributes. Termination never sets debt paid, balance zero, lien absent, permit expired, or holder absent unless separate operations state those effects.

**MX-FOLD-007 — ASSERT_STATE and CORRECT.** A transaction ASSERT applies only module-admitted legal-declaration paths and does not manufacture a lifecycle. CORRECT replaces/deletes only the path expressly identified as erroneous, preserving old/new values and support in correction history. It does not rewrite prior batches.

**MX-FOLD-008 — Observation attachment.** Add each assertion as a separate evidence object keyed by event id/path/valid interval/scope. ASSERTED_NONE remains a scoped negative assertion. Observation serialization never overwrites composed state. Compare it with a composed path only when every state action establishing that path has an interval ending before the observation interval starts; matching values become `CORROBORATES` and incompatible values `DISPUTES_COMPOSED_STATE`. Otherwise comparison is `TEMPORALLY_INDETERMINATE`. Incompatible observations with the same valid interval/scope become `OBSERVATION_CONFLICT` without changing transaction state.

**MX-FOLD-009 — Boundaries.** Attach every boundary to its function/object at its own batch. `INFORMATIONAL` never changes state. A `SELF_EXECUTING` boundary is a state-action node and applies its module-admitted delta at its graph position only when condition status is resolved and ordinary conflict rules pass; otherwise it remains a conditional/informational record.

**MX-FOLD-010 — Commutativity and conflict.** Incomparable deltas commute only when they target different object keys, different non-lifecycle paths, or identical compatible values. Incompatible outcomes on one object/path, or incomparable lifecycle operations on one object, produce local `ORDER_CONFLICT` with all candidates/source ids; no candidate is selected. Never use last-write-wins. A later node connected by an interval/express path may change an earlier value prospectively; history keeps both.

**MX-FOLD-011 — Path merge policies.** Apply the loaded module's declared merge: scalar replacement/conflict, set union/targeted removal, keyed-map merge, or interest-ledger operation. A path/type/mode without a matching module policy invalidates the input rather than selecting a generic fallback.

**MX-FOLD-012 — Quantities and nulls.** A quantity reference alone does not write a state field. Fold only a module operation naming the quantity path. Preserve kinds/scopes and unallocated totals. UNKNOWN is path-local; ASSERTED_NONE is evidence/value; NOT_APPLICABLE is a proven structural branch; NO_CHANGE is an operation, never stored state. JSON null/blank is invalid.

## 6. Status and exception lanes

**MX-STAT-001 — Cell status precedence.** After each batch:

1. `STATE_CONFLICT` when composed lifecycle/touched path conflicts;
2. `EVIDENCE_CONFLICT` when composed state is single-valued but dated observations conflict with it or each other;
3. `PARTIAL` when at least one composed object exists and a transaction-touched required path is UNKNOWN;
4. `RESOLVED` when at least one composed object exists and every transaction-touched path is single-valued;
5. `EVIDENCE_ONLY` when no composed object exists but observation/boundary records do;
6. `UNKNOWN` when the document supplies neither layer for that function at that batch.

Inactive objects stay visible and can be RESOLVED. A conflict affects only its BBL/function/object/path/time; later resolution never erases prior conflict history.

**MX-STAT-002 — Exception lanes.** Render, count, and conserve: `undated_transactions`, `conditional_events`, `observations_unplaced`, `notice_lane`, `unplaced_parcel`, `unresolved_classification`, `unresolved_continuity`, `document_ambiguities`, `framework_gaps`, and `input_failures`. None changes a dated composed cell. Genuinely unknown observation valid time remains a successful extraction finding but is visibly absent from state chronology.

**MX-STAT-003 — Matrix outcome.** `PASS` requires accepted inputs, every eligible event conserved, no missing transaction placement key, no `CONTINUITY_UNRESOLVED` after a document-resolved pointer, no state-order conflict, and all matrix QC passing. Preserved unknown-valid-time observations/notices/conditions and pointers to targets outside the closed input do not alone prevent PASS. Surviving document ambiguity, undated/unplaced transaction, ambiguous present target, unresolved present-target continuity, or order conflict yields `EXCEPTION`. Invalid schema/provenance/lane/fan/fold/serialization yields `FAIL`.

## 7. Canonical `resolved.md`

**MX-SER-001 — One required file.** `resolved.md` contains a bounded human view followed by a fenced `json` block holding the entire canonical object. No sibling JSON file is required. Canonical JSON, not table typography, decides semantic equality.

**MX-SER-002 — Canonical envelope.** Keys appear in order:

`matrix_spec_version`, `framework_version`, `matrix_run_id`, `input_manifest`, `reference_resolutions`, `bbl_chronologies`, `observation_occurrence_audit`, `notice_lane`, `conditional_lane`, `undated_transactions`, `observations_unplaced`, `unplaced_parcel`, `unresolved_classification`, `unresolved_continuity`, `document_ambiguities`, `framework_gaps`, `input_failures`, `external_reference_registry`, `party_registry`, `quantity_registry`, `conflicts`, `counts`, `validation`.

`matrix_run_id` is SHA-256 of the canonical sorted input manifest. Each manifest row contains document id, extraction SHA-256, framework version, adapter id, module ids, and bundle hash. Bundle hashes may differ because the selected modules/adapters differ; the framework version may not.

Each BBL chronology contains ascending batches. Each batch contains batch id, label, interval start/end, uncertainty/order basis, and exactly eleven cells in MX-SCOPE-002 order.

**MX-SER-003 — Title serialization/query contract.** Title composed state serializes only as `objects_by_interest_kind`. The human cell prints `TITLE[<interest_kind>] <object_key> …`. Any API/query derived from this matrix requires `(bbl, time, interest_kind)` before returning holders; wildcard kinds return a grouped map, never one holder list. Missing kind is a validation error. This preserves concurrent fee, leasehold, subleasehold, common, and other estates.

**MX-SER-004 — Human view.** Render title/version/matrix run/input count, then one section per BBL with a table `Time` plus eleven functions. Cells show status and stable object/assertion/boundary ids; detailed audit sections expand them. Render input, reference-resolution, exception, and audit sections in MX-SER-002 order. Escape `|` as `&#124;`, backslash as `\\`, and line breaks as spaces. Do not truncate the canonical JSON block.

**MX-SER-005 — Scalar/order rules.** UTF-8 without BOM, LF endings, two-space JSON indentation, terminal LF. Exact decimals are quoted base-10 without grouping/exponent/trailing fractional zeros; fractions are reduced strings; booleans are JSON booleans; dates are ISO; sentinels uppercase. Sort normalized map keys by Unicode code point; ids/roles/flags/candidates lexically after deduplication. Preserve only declared field-op, express sequence, and verbatim evidence order.

**MX-SER-006 — Provenance.** A resolved field names source document/event ids and fold rule ids; carried fields name prior batch. Event ids join through the input manifest to extraction evidence instead of repeating quotes. Canonical validation carries every exact extraction SHA-256 and the manifest hash.

## 8. Deterministic algorithm and QC

**MX-ALG-001 — Reference loop.** Coordination validates/sorts inputs, indexes identities, resolves pointers/continuity, fans records, routes ineligible material, and packages ascending one-BBL jobs. Each job compiles the three physical state inputs; creates interval components/graphs; for every batch/function carries and partially orders/folds transactions plus self-executing boundaries; attaches observations/informational boundaries; sets statuses; assembles audit/exception lanes; serializes; and runs QC.

**MX-QC-001 — Fan conservation.** Each eligible source record yields exactly its distinct affected BBL/scope projections. Every ineligible source id occurs exactly once in its proper lane. Role multiplicity never creates projection multiplicity.

**MX-QC-002 — Lane firewall.** Reversing or injecting evidence-time/notice/unplaced-observation records into the state compiler is rejected. Dated-observation projections contain asserted-valid time only. Occurrence-time changes cannot alter any BBL batch/cell byte.

**MX-QC-003 — Ordering reproducibility.** Reversing every input array produces byte-identical canonical JSON. Every semantic edge is either proved by disjoint source intervals or cites an extraction ordering relation. Every incomparable state-action pair either commutes or produces `ORDER_CONFLICT`; serialization order never appears as legal order.

**MX-QC-004 — Title safety.** Every Title projection/object carries interest kind and nests beneath it; object keys are distinct across kinds; no estate-blind holder output exists. Fixtures L1 and L2 test fee continuity and separately indexed leasehold representation.

**MX-QC-005 — Fold trace/locality.** Every composed touched field identifies source transaction ids, module merge policy, and MX fold rule; every evidence assertion identifies its observation; carry names prior batch. Conflicts remain local. Fixtures include partial release, lien release without debt-payment words, and unsequenced same-path deltas.

**MX-QC-006 — Time integrity.** No recording/occurrence time appears as state sort basis. Partial-date overlap, disjoint intervals, O1/O2/O3 observation clocks, conditions, and boundaries route exactly as specified. Unknown-valid-time observation records have no route into dated cells.

**MX-QC-007 — Quantity/reference conservation.** Each quantity and external-reference record serializes once; projections/objects contain ids only. No NOT_DERIVABLE total becomes an allocation. Every pointer has one resolution record; only exact unique document matches gain target ids, and only MX-LINK-003 gains object continuity. A target outside the input imports no state.

**MX-QC-008 — Cell completeness and dual view.** Every dated row has eleven cells with the MX-CELL-001 fields. Parse the canonical block and human audit view; BBLs, batches, statuses, Title kinds, object/assertion/boundary ids, quantities, source events, and lane membership agree. Empty annexes render `NONE` only in prose; canonical arrays are empty arrays.

**MX-QC-009 — Frozen/conformance set.** Re-run TC-001, L1/L2, O1/O2/O3, and fixtures for partial dates, incomparable noncommuting actions, mixed transaction/observation, assertion of absence, condition-dependent effect, zero-event document, FT/BK/Richmond adapters, pointer target absent/unique/ambiguous, cross-document continuation, and multi-BBL unallocated total in fresh contexts with expected answers withheld. Any regression blocks the version.
