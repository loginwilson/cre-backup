<!-- MATRIX:SCOPE SEPARATE_RESOLUTION_READER -->
# NYC C.R.E.D. resolved matrix specification v2

This specification consumes a closed set of completed v2 `extraction.json` files plus the exact immutable module schemas named by their bundle manifests, and produces `resolved.md`: the three renderings the owner specified — function sweep, event table with party and quantity sub-tables, and document brief — followed by parcel chronologies and a lossless canonical block. A one-file set is the loop case; a corpus set enables cross-document continuity. **Resolution never discovers events or supplies missing extraction fields.** All event-producing rules and path schemas live in the extraction bundle.

## 0. Contract and execution order

**MX-SCOPE-001 — Accepted input set.** Sort a supplied manifest by document id then extraction SHA-256. Require one file per document id, strict canonical envelopes, one framework version, valid lanes, registries, coverage, and ids, and exact adapter/module text whose hashes match each bundle manifest. Duplicate ids or differing bytes for one id are `INPUT_SET_CONFLICT`. **A `FAIL` input yields no state projections but keeps its exception report and its three renderings. An `EXCEPTION` input contributes only records outside every exclusion scope and serializes all excluded ids and reasons.** Every state input withheld solely by this gate appears exactly once in `input_failures[].suppressed_state_inputs` with full source id and eligibility keys; another exception record may reference the id but may not count it again as routed material.

**MX-SCOPE-002 — Fixed order.** Functions always appear as `IDENTITY`, `TITLE`, `ENTITLEMENT`, `ENVELOPE`, `ENCUMBRANCE`, `CAPITAL`, `PERMIT`, `AS_BUILT`, `OCCUPANCY`, `COST`, `VALUE`.

**MX-SCOPE-003 — Three state inputs.** The state compiler receives only (1) unconditional transaction projections with supported applicable intervals; (2) dated-observation projections containing asserted-valid intervals and assertion payloads, never occurrence or statement times; (3) temporal-boundary projections. `observations_unplaced`, `notices`, `conditional_events`, `evidence_time_registry`, `registration_annotations`, `boundary_orphans`, unresolved classifications, undated transactions, and unplaced parcels remain physically separate inputs to audit and exception renderers. They are not handed to the state sorter.

**MX-SCOPE-004 — Order of work.** Input gate → current-recording index → reference and object-continuity resolution → fan → physical stream compilation → interval components → state-action order graph → state fold → evidence and informational-boundary attachment → status → exception and audit lanes → the three renderings → canonical serialization → QC. Serialization tie-breaks never become semantic order.

**MX-SCOPE-005 — One-BBL production unit.** Indexing, exact reference lookup, and fan are deterministic coordination steps. A production fold invocation receives this spec, exact module schemas, and one canonical BBL's complete projections, registries, and reference resolutions; it receives no other BBL history. Multi-BBL output runs the same fold independently per ascending BBL and concatenates. No state operation crosses BBL jobs.

## 1. Fan to affected BBL/scope

**MX-FAN-001 — Transaction projection.** For each transaction, group its `parcel_bindings` by exact `(bbl, scope)` and emit one projection per group. Sort groups by BBL then scope and assign `<event_id>/P001`…. Merge that pair's role array in controlled role order. The projection carries source document, event, and group ids, extraction and matrix object ids, function, **`epistemic_character` and `mode` both**, object type, mandatory Title interest kind, applicable interval, participations and directionality, state delta, quantity, term, and reference ids, `certainty`, `resolution_provenance`, support, and conflicts. Parcel inventory is never a fan source.

**MX-FAN-002 — Dated-observation projection.** Apply the same grouping and id procedure to `observations_dated`. Copy asserted-valid interval, function, object, interest kind, assertions, ids, scope, and provenance. **Do not copy `evidence_time_id` or any occurrence or statement date.** Reject a projection that exposes either.

**MX-FAN-003 — Boundary projection.** Fan a boundary only to its own affected pairs; assign `<boundary_id>/P001`… by BBL then scope. Carry boundary, object, and event id, function, boundary type and interval, consequence, condition, effect status, and any admitted boundary delta.

**MX-FAN-004 — Scope conservation.** Fanning preserves `UNIT`, `PARTIAL_BBL`, `AIR_SPACE`, `SUBTERRANEAN_SPACE`, `FACADE`, `EASEMENT_AREA`, `DESCRIBED_PREMISES`, and UNKNOWN. **Same BBL at different scopes produces different projections and never merges.** Several parcel roles on one exact pair produce one projection.

**MX-FAN-005 — Quantity conservation.** Projections reference existing quantity ids. `INSTRUMENT_TOTAL`, `MULTI_EVENT_TOTAL`, and every `NOT_DERIVABLE` total remain one registry record and never acquire a parcel amount. Only an `EXPLICIT` or `DERIVED` allocation naming that pair may appear as a parcel value. **A `PARTY_SHARE` quantity projects to the party, not to the parcel**, and quantities sharing an `allocation_group_id` are rendered together so a measured amount stays paired with its value.

**MX-FAN-006 — Ineligible placement.** Unknown BBL routes the source id once to `unplaced_parcel`; unknown transaction time routes each otherwise fanned pair once to `undated_transactions`; unresolved function, mode, or object routes once to `unresolved_classification`. None enters a dated state stream. Duplicate routing is invalid.

## 2. Cross-document reference and object continuity

**MX-LINK-001 — Current-recording index.** Index each input by supplied `DOC_ID` and its `current_recording_identity` components: `CRFN`, `FILE_NUMBER`, `BOOK`, `PAGE`, `INSTRUMENT`, `REEL`, `YEAR`, `BOROUGH`. Match only typed components already present in an external-reference record; every supplied component must equal the corresponding normalized target component, and omitted components are not invented. Do not use document type, relation words, amount, party, BBL, date, or chronology to choose a document. **A Richmond `page` is a book locator and is matched only against `PAGE` as a locator component, never as an extent.**

**MX-LINK-002 — Pointer resolution.** For each external reference, retain the extraction record unchanged and emit one matrix resolution record. **Resolution depends on `reference_class`: only `RECORDED_INSTRUMENT` and a uniquely identified `GOVERNING_DOCUMENT` enter document-id resolution.** `STATUTE_REGULATION` and `INCORPORATED_SECTION` resolve to `NOT_CONTINUITY_TARGET`, which is not a failure and not `UNPARSEABLE`. For eligible classes: no parseable locator gives `UNPARSEABLE`; zero matching identities gives `TARGET_OUTSIDE_INPUT`; one gives `DOCUMENT_RESOLVED`; more than one gives `DOCUMENT_AMBIGUOUS` with every candidate id. A relation label never breaks a tie.

**MX-LINK-003 — Continuing-object test.** For a source transaction in mode MODIFY, CORRECT, TRANSFER, or TERMINATE whose reference has `DOCUMENT_RESOLVED`, consider target-document transaction events with the same function, the same Title interest kind when applicable, and at least one exact affected pair. Select on the first satisfied row: (1) an exact cross-document object identifier supported in both extractions selects its one target; (2) otherwise exactly one candidate remains after the stated filters. Zero or several is `CONTINUITY_UNRESOLVED`; never use party, amount, proximity, customary sequence, or similar names.

**MX-LINK-004 — Matrix object identity.** Create one node per `(document_id, state_object_key)` and a directed continuation edge to the unique MX-LINK-003 target. Reject an edge across function, Title interest kind, or disjoint BBL/scope. Acyclic components with exactly one sink use `matrix_object_id = MO:` plus SHA-256 of that sink's canonical `(document_id, state_object_key)`; an unlinked node is its own sink. A cycle, several target edges from one source, or several sinks is `CONTINUITY_UNRESOLVED`. **Because key construction is stable identity, FR-REC-008's byte grammar is load-bearing here**: a slugged or suffixed key produces a different node.

## 3. Time streams and same-instant order

**MX-TIME-001 — Sort keys.** Transaction projections use only `applicable_time`. Observation projections use only `asserted_valid_time`. Boundary projections use only their boundary interval. **Recording time, occurrence time, evidence-time id, document id, event id, page order, and mode are forbidden as chronology keys.**

**MX-TIME-002 — Interval components.** For each BBL, order eligible projections by interval start then end. Sweep left to right maintaining the maximum end in the current component; add a projection when its start is on or before that maximum, otherwise begin a new component. A component is one uncertain time batch: a broad year bridges precise dates and the output marks the component uncertain rather than inventing order.

**MX-TIME-003 — Batch ids and labels.** Assign `<bbl>-R001`…. If every projection in a component has one identical complete day, label `AFTER YYYY-MM-DD`; otherwise `AFTER [min_start..max_end]~UNCERTAIN` with cell reason `TIME_COMPONENT_UNCERTAIN`. The composed layer is the state after all nonconflicting state actions in that component, not a claim it held throughout.

**MX-TIME-004 — State-action order graph.** Nodes are transaction projections and `SELF_EXECUTING` boundary projections in one component. For every pair with disjoint source intervals add `INTERVAL_BEFORE`. Add extraction ordering relations whose endpoints are in the component; normalize AFTER to BEFORE. SIMULTANEOUS joins transaction endpoints only when intervals overlap. An express edge opposite an interval edge, a disjoint SIMULTANEOUS relation, or a directed cycle is `ORDER_CONFLICT`. Dated observations and informational boundaries are not nodes.

**MX-TIME-005 — Partial-order fold.** Collapse valid simultaneous nodes and compute reachability. For every two state-action nodes with no path either way, test commutativity under MX-FOLD-010. A noncommuting incomparable pair is `ORDER_CONFLICT`; preserve candidate deltas without choosing a sequence. Topologically fold conflict-free nodes.

**MX-TIME-006 — Deterministic tie-break.** Among proven-commuting ready nodes and for serialization, order by interval start, interval end, function order, source kind `TRANSACTION` then `BOUNDARY`, mode order `CORRECT`, `TERMINATE`, `TRANSFER`, `MODIFY`, `CREATE`, `ASSERT`, source id, projection id. Across BBLs use ascending ten-digit BBL. Output-only; it cannot resolve a conflict.

**MX-TIME-007 — Separate nonstate chronologies.** `observation_occurrence_audit` may display evidence-time records ordered by their own evidence times, labeled `EVIDENCE_TIME_ONLY`, containing no state cell. Notices order in `notice_lane` by supported notice occurrence time, otherwise id. Conditional events order only by supported boundary or condition dates and remain `CONDITION_DEPENDENT`. `registration_annotations` is ordered by source path and carries **no** time axis at all — a registry-side note has no admitted clock in this version, and that gap is recorded rather than filled. None merges into composed-state rows.

## 4. Cell and object model

**MX-CELL-001 — Cell shape.** Each dated BBL/function cell contains `status`, `reason`, `composed_state`, `evidence_assertions`, `boundaries`, `applied_transaction_ids`, `observation_ids`, `boundary_ids`, and `conflicts`. The last three arrays are sorted and deduplicated. For functions other than Title, `composed_state.objects` is a map keyed by `state_object_key`. **Title instead uses `objects_by_interest_kind`; a generic `title.holders` list is forbidden.**

**MX-CELL-002 — State object.** Keyed by `matrix_object_id`, containing every extraction object key and member, object type, function, Title interest kind when applicable, lifecycle (`UNKNOWN`, `ACTIVE`, `INACTIVE`, `CONFLICT`), module-typed fields, holder and obligor ledgers, exact coverage records, quantity, term, and reference ids, history, source ids, and field conflicts. Different matrix object ids always coexist.

**MX-CELL-003 — Initial state.** Before the first eligible transaction, composed state is `UNKNOWN/NO_DOCUMENT_EVIDENCE`; no unseen object or field is generated. A first MODIFY, TRANSFER, or CORRECT instantiates only its keyed object and touched paths with lifecycle UNKNOWN. A first TERMINATE may set INACTIVE because the present act states termination, while unseen prior attributes remain unknown.

**MX-CELL-004 — Coverage.** Coverage records are exact `(bbl, scope, roles, unit or share when stated)`. A projection touches only its pair. Partial release changes only named coverage. Unknown scope remains unknown; it cannot expand to whole lot.

**MX-CELL-005 — Layer firewall.** `composed_state` receives transactions and admitted self-executing boundary deltas only. `evidence_assertions` receives dated observations only. Notice, unplaced observation, evidence occurrence, registry-annotation, and conditional content has no field path into either layer.

## 5. Fold

**MX-FOLD-001 — Carry.** Start a batch from the prior batch's composed object maps for that BBL and function. Retain unchanged values and append `CARRY@<prior_batch>` provenance. A function untouched in a later row carries; before any transaction it remains UNKNOWN. `NO_CHANGE` is not used for ordinary carry.

**MX-FOLD-002 — Projection target.** Apply a transaction projection only to its function, matrix object id, and exact coverage. Add source keys, ids, and references, then execute lifecycle and ordered module-admitted field operations. Linked events in other functions never share state fields.

**MX-FOLD-003 — CREATE.** `ACTIVATE` sets lifecycle ACTIVE and applies supported `SET`, `REMOVE_ASSERTED`, and `UNKNOWN` operations. Unnamed paths are not generated. CREATE on an already ACTIVE object coalesces only identical commuting deltas.

**MX-FOLD-004 — MODIFY.** `PRESERVE` retains lifecycle and untouched paths. `SET` changes the named path, `REMOVE_ASSERTED` stores scoped ASSERTED_NONE, `UNKNOWN` makes only that path unknown, `NO_CHANGE` carries a known value at that exact path. With no known value, NO_CHANGE yields `UNKNOWN/NO_PRIOR_STATE`.

**MX-FOLD-005 — TRANSFER.** Preserve object identity and unmodified paths. Ledger operations add supported TO interests. Remove a FROM interest wholly only on express all or entire, or an unqualified whole-object transfer with no retained or partial qualifier. Apply exact stated fractions; **applicable unstated extent makes transferred and retained interests UNKNOWN, never equal shares.** Assumption adds an obligor unless express release removes one.

**MX-FOLD-006 — TERMINATE.** `DEACTIVATE` sets the exact object and coverage INACTIVE and records termination event and scope. Preserve historical attributes. Termination never sets debt paid, balance zero, lien absent, permit expired, or holder absent unless separate operations state those effects.

**MX-FOLD-007 — ASSERT_STATE and CORRECT.** A transaction ASSERT applies only module-admitted legal-declaration paths and manufactures no lifecycle. CORRECT replaces or deletes only the path expressly identified as erroneous, preserving old and new values and support in correction history. It does not rewrite prior batches.

**MX-FOLD-008 — Observation attachment.** Add each assertion as a separate evidence object keyed by event id, path, valid interval, and scope. ASSERTED_NONE remains a scoped negative assertion. Observation serialization never overwrites composed state. Compare with a composed path only when every state action establishing that path has an interval ending before the observation interval starts; matching values become `CORROBORATES`, incompatible values `DISPUTES_COMPOSED_STATE`, otherwise `TEMPORALLY_INDETERMINATE`. Incompatible observations at the same interval and scope become `OBSERVATION_CONFLICT` without changing transaction state.

**MX-FOLD-009 — Boundaries.** Attach every boundary to its function and object at its own batch. `INFORMATIONAL` never changes state. A `SELF_EXECUTING` boundary applies its module-admitted delta at its graph position only when condition status is resolved and ordinary conflict rules pass.

**MX-FOLD-010 — Commutativity and conflict.** Incomparable deltas commute only when they target different object keys, different non-lifecycle paths, or identical compatible values. Incompatible outcomes on one object or path, or incomparable lifecycle operations on one object, produce local `ORDER_CONFLICT` with all candidates and source ids; no candidate is selected. **Never use last-write-wins.**

**MX-FOLD-011 — Path merge policies.** Apply the loaded module's declared merge: scalar replacement or conflict, set union or targeted removal, keyed-map merge, or interest-ledger operation. A path, type, or mode without a matching module policy invalidates the input rather than selecting a generic fallback.

**MX-FOLD-012 — Quantities and nulls.** A quantity reference alone does not write a state field. Fold only a module operation naming the quantity path. Preserve kinds, scopes, and unallocated totals. UNKNOWN is path-local; ASSERTED_NONE is evidence; NOT_APPLICABLE is a proven structural branch; NO_CHANGE is an operation, never stored state. JSON null or blank is invalid.

## 6. Status and exception lanes

**MX-STAT-001 — Cell status precedence.** After each batch: (1) `STATE_CONFLICT` when composed lifecycle or touched path conflicts; (2) `EVIDENCE_CONFLICT` when composed state is single-valued but dated observations conflict; (3) `PARTIAL` when at least one composed object exists and a transaction-touched required path is UNKNOWN; (4) `RESOLVED` when at least one composed object exists and every touched path is single-valued; (5) `EVIDENCE_ONLY` when no composed object exists but observation or boundary records do; (6) `UNKNOWN` when the document supplies neither layer. Inactive objects stay visible and can be RESOLVED. A conflict affects only its BBL, function, object, path, and time.

**MX-STAT-002 — Exception lanes.** Render, count, and conserve, each with exact source ids and one owner class: `undated_transactions`, `conditional_events`, `observations_unplaced`, `notice_lane`, `unplaced_parcel`, `unresolved_classification`, `unresolved_continuity`, `document_ambiguities`, **`illegible_final`**, **`boundary_orphans`**, **`incorporated_sections_not_supplied`**, **`registration_annotations`**, `unclassifiable_content`, `framework_gaps`, and `input_failures`. None changes a dated composed cell.

`illegible_final` exists because a mark that could not be read is a finding the matrix must be able to state. Without it, an unreadable measurement vanishes between extraction and resolution and the matrix returns a document **silent about the thing that most often went wrong** — asserting a clean read it never had. Separate `framework_gaps` (a bundle defect) from `unclassifiable_content` (a supplied readable passage with no admitted result); they have different owners and different fixes.

**MX-STAT-003 — Matrix outcome.** **Any manifest input with extraction `FAIL` makes the matrix `FAIL`.** Accepted `EXCEPTION` inputs make the matrix at least `EXCEPTION`. There is no unmapped upstream-FAIL case. `PASS` otherwise requires accepted inputs, every eligible event conserved, no missing transaction placement key, no `CONTINUITY_UNRESOLVED` after a document-resolved pointer, no state-order conflict, and all matrix QC passing. Preserved unknown-valid-time observations, notices, conditions, `NOT_CONTINUITY_TARGET` references, and pointers outside the closed input do not alone prevent PASS. Surviving document ambiguity, undated or unplaced transaction, ambiguous present target, unresolved present-target continuity, boundary orphan, or order conflict yields `EXCEPTION`. Invalid schema, provenance, lane, fan, fold, or serialization yields `FAIL`.

## 7. The three renderings

**MX-VIEW-001 — Order.** `resolved.md` renders, per document, in this order: **function sweep**, then **event table** with party and quantity sub-tables, then **document brief**. The order is load-bearing: the sweep is what makes the table trustworthy and the table is what makes the brief trustworthy. Chronologies and the canonical block follow.

**MX-VIEW-002 — Function sweep rendering.** One row per supplied page per function, eleven per page, plus the support pass. Columns: `page`, `function`, `anchors`, `status`, `disposition`. **`anchors` is populated wherever an anchor exists, including where no event fires** — a `SUPPORT_ONLY` cell whose anchor exists must not render identically to a `NO_HIT` cell where nothing was found, because that identity is precisely how an unreadable mark comes to have nowhere to exist. `status` carries the four-state union and, for `NO_HIT`, the recorded `encoded_resolution`. A blank cell is a rendering error, not a clean page.

**MX-VIEW-003 — Event table rendering.** Columns: `event`, `page`, `bbl`, `scope`, `object`, `function`, `character`, `mode`, `direction`, `parties→`, `quantity→`, `terms`, `date`, `date_kind`, `date_basis`, `certainty`, `evidence`, `summary`.

- `bbl` and `scope` render `parcel_bindings`; **an event binding several parcels renders one row per binding or a structured list, never a scalar** — a single-parcel example cannot exhibit the failure a scalar column permits.
- `object` renders the `state_object_key`, never a free label. Two Title transfers on one BBL on one date are distinguished only by this column.
- `character` and `mode` are **both** rendered: character is the lane `MX-SCOPE-003` reads, mode is the state effect. Neither substitutes for the other.
- `direction` renders the structured relation as `FROM → TO` where exactly one pair exists, otherwise the relation set. The arrow is a projection, not the stored form.
- **`date_kind` is mandatory and names which clock the cell shows** — `APPLICABLE` for transactions, `ASSERTED_VALID` for dated observations, empty for unplaced. One undifferentiated date column renders two different clocks in one cell and undoes at the presentation layer the firewall `FR-DATE-003` establishes; `date_basis` (`instrument`, `effective`, `as_of`, `UNKNOWN`) is the late-filing guard, and `UNKNOWN` must render visibly differently from absent.
- `certainty` renders the worst field-local certainty; an adjudicated event additionally shows `resolution_provenance: ADJUDICATED`. **An escalated event is a real output, not a failure.**
- `evidence` renders ordered support ids; `page` renders ordered support page ids. Neither may be forced to a single page or quote for a multi-page event.
- `summary` is one derived line. **It may introduce no claim absent from its own row** and is never evidence.

**MX-VIEW-004 — Party sub-table.** One row per party **per event**, because role and share are event properties: `party_id`, `role`, `name_as_written`, `entity_type`, `stated_parent`, `natural_persons`, `address`, `phone`, `email`, `share`, `quantity_ids`, `evidence`. `stated_parent` and `natural_persons` render from `party_relationship_registry` by predicate; contact columns render from `attributes[]` and **show `source_class`**, since an index-supplied address and an instrument-stated one are different claims and never merge. `share` is empty where no share slot exists — never `UNKNOWN` merely because a party participates, and never an inferred equal split.

**MX-VIEW-005 — Quantity sub-table.** `quantity`, `kind`, `value`, `scope`, `target`, `allocation_status`, `allocation_group_id`. A `PARTY_SHARE` row targets a `party_id`. **Rows sharing an `allocation_group_id` render adjacently** so a measured quantity stays paired with its value; four quantities and four values with no group key leave which-at-which underdetermined.

**MX-VIEW-006 — Document brief.** Short enough to decide from without opening the document: identity line with address, unit, borough, BBL; signed and recorded dates; one paragraph of the operative acts; counts of events, dated and unplaced. **The warnings are part of the brief, not an appendix** — unstated shares, unsupplied incorporated sections, unattributed annotations, illegible finals, boundary orphans, and `NOT_CHECKABLE` comparator results each render as a line. A reader shown only a clean summary trusts it more than it deserves.

## 8. Canonical serialization

**MX-SER-001 — One required file.** `resolved.md` contains the bounded human view followed by a fenced `json` block holding the entire canonical object. Canonical JSON, not table typography, decides semantic equality.

**MX-SER-002 — Canonical envelope.** Keys in order: `matrix_spec_version`, `framework_version`, `matrix_run_id`, `input_manifest`, `function_sweep_views`, `event_table_views`, `reference_resolutions`, `bbl_chronologies`, `observation_occurrence_audit`, `notice_lane`, `conditional_lane`, `undated_transactions`, `observations_unplaced`, `unplaced_parcel`, `unresolved_classification`, `unresolved_continuity`, `document_ambiguities`, `illegible_final`, `boundary_orphans`, `incorporated_sections_not_supplied`, `registration_annotations`, `unclassifiable_content`, `framework_gaps`, `input_failures`, `external_reference_registry`, `party_registry`, `party_relationship_registry`, `quantity_registry`, `conflicts`, `counts`, `validation`.

`matrix_run_id` is SHA-256 of the canonical sorted input manifest. Each manifest row carries document id, extraction SHA-256, framework version, adapter id, module ids, and `bundle_sha256`. Bundle hashes may differ because selected modules differ; the framework version may not. Each BBL chronology contains ascending batches; each batch has batch id, label, interval start and end, uncertainty basis, and exactly eleven cells in MX-SCOPE-002 order.

**MX-SER-003 — Title serialization and query contract.** Title composed state serializes only as `objects_by_interest_kind`. The human cell prints `TITLE[<interest_kind>] <object_key> …`. Any API derived from this matrix requires `(bbl, time, interest_kind)` before returning holders; wildcard kinds return a grouped map, never one holder list. Missing kind is a validation error.

**MX-SER-004 — Human view.** Render title, version, run id, and input count; then per document the three MX-VIEW renderings; then one section per BBL with a table of `Time` plus eleven functions; then input, reference-resolution, exception, and audit sections in MX-SER-002 order. Escape `|` as `&#124;`, backslash as `\\`, line breaks as spaces. Do not truncate the canonical block.

**MX-SER-005 — Scalar and order rules.** UTF-8 without BOM, LF endings, two-space JSON indentation, terminal LF. Exact decimals are quoted base-10 without grouping, exponent, or trailing fractional zeros; fractions reduced; booleans JSON booleans; dates ISO; sentinels uppercase. Sort normalized map keys by Unicode code point; ids, roles, flags, and candidates lexically after deduplication. Preserve only declared field-op, express sequence, and verbatim evidence order.

**MX-SER-006 — Provenance.** A resolved field names source document and event ids and fold rule ids; carried fields name the prior batch. Event ids join through the input manifest to extraction evidence instead of repeating quotes. Canonical validation carries every extraction SHA-256 and the manifest hash.

## 9. QC

**MX-QC-001 — Fan conservation.** Each eligible source record yields exactly its distinct affected pairs. Every ineligible source id occurs exactly once in its proper lane. Role multiplicity never creates projection multiplicity. Every id suppressed by MX-SCOPE-001 appears exactly once in `suppressed_state_inputs`.

**MX-QC-002 — Lane firewall.** Injecting evidence-time, notice, registry-annotation, or unplaced-observation records into the state compiler is rejected. Dated-observation projections contain asserted-valid time only. Occurrence-time changes cannot alter any BBL batch or cell byte.

**MX-QC-003 — Ordering reproducibility.** Reversing every input array produces byte-identical canonical JSON. Every semantic edge is proved by disjoint source intervals or cites an extraction ordering relation. Every incomparable state-action pair either commutes or produces `ORDER_CONFLICT`.

**MX-QC-004 — Title safety.** Every Title projection and object carries interest kind and nests beneath it; object keys are distinct across kinds; no estate-blind holder output exists.

**MX-QC-005 — Fold trace and locality.** Every composed touched field identifies source transaction ids, module merge policy, and fold rule; every evidence assertion identifies its observation; carry names the prior batch. Conflicts remain local.

**MX-QC-006 — Time integrity.** No recording or occurrence time appears as a state sort basis. Partial-date overlap, disjoint intervals, observation clocks, conditions, and boundaries route exactly as specified. Unknown-valid-time observation records have no route into dated cells. **Every rendered date cell carries a `date_kind`.**

**MX-QC-007 — Quantity and reference conservation.** Each quantity and reference record serializes once; projections contain ids only. No `NOT_DERIVABLE` total becomes an allocation. Every pointer has one resolution record; only exact unique matches gain target ids; a target outside the input imports no state. Every `allocation_group_id` member set is complete or the group is a conflict.

**MX-QC-008 — Cell completeness and dual view.** Every dated row has eleven cells with the MX-CELL-001 fields. Parse the canonical block and the human view; BBLs, batches, statuses, Title kinds, object, assertion, and boundary ids, quantities, source events, and lane membership agree. **Every sweep view has eleven rows per supplied page plus the support row, and no rendered `anchors` cell is empty where an anchor id exists.** Empty annexes render `NONE` only in prose; canonical arrays are empty arrays.

**MX-QC-009 — Frozen conformance set.** Re-run in fresh contexts with expected answers withheld: TC-001, TC-003, L1/L2 Title estate separation, O1/O2/O3 observation clocks, and fixtures for partial dates, incomparable noncommuting actions, mixed transaction and observation, assertion of absence, condition-dependent effect, zero-event document with support registries intact, FT/BK/Richmond adapters, pointer target absent, unique, and ambiguous, cross-document continuation, multi-BBL unallocated total, a multi-parcel event, a `PARTY_SHARE` allocation group, an illegible final, and a boundary orphan. Any regression blocks the version.
