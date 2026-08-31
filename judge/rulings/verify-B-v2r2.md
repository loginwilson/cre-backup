# Extractor B reverification of framework v2, revision 2

## Verdict: RETURN

The resubmission is materially better, but it is not releasable. The highest-severity defect is new and mechanical: the mandatory `function_sweep_ledger` cannot contain even one schema-valid row. Because the top-level schema requires that ledger to be nonempty, no conforming `extraction.json` exists. The final quantity type has the same composition defect. Round 2 must not start on this revision.

I accept the orchestrator's narrow deferral of the build tool/version gate and the partition shadow runner only for a later round explicitly labelled **FULL_BUNDLE_V2 / PARTITION_NOT_TESTED**. That deferral does not cover the failures below: they are present in the full-bundle prose and schemas being tested.

## What passes

- **Return 7 is closed.** `FR-DATE-006a` gives the Article 18 / severability pair an executable discriminator: a named alternative instrument or article governing an already-keyed object's `encumbrance.legal_scope` emits a conditional event; pure severability naming no object and filling no path does not. This restores the adjudicated round-1 result.
- **Return 2b, lens-card content, is closed.** The cards now enumerate their modules' admitted paths and triggers. In particular, Encumbrance carries both SECURED_FINANCE and LAND_RIGHTS rather than a generic boundary paraphrase.
- The specific structural repairs for target-function coupling, proving anchors on `HIT`/`SUPPORT_ONLY`, lane constants, fixed QC order, and `DOCUMENT_SUPPORT` pass identity are sound in isolation.
- **Return 6 is improved but not closed.** The visible-mark branch is now separated from searched-and-empty, but `FR-QTY-002` still contradicts it; see R2-5.

## R2-1 — the required extraction schema is unsatisfiable

`extraction.schema.json` requires a nonempty `function_sweep_ledger`. Its `ledger_row` is defined as:

1. `allOf` a `$ref` to `discovery.schema.json#/$defs/cell`; then
2. add required `function` and `pass_kind` properties.

The referenced discovery `cell` has `additionalProperties: false` and does not declare `function` or `pass_kind`. Under Draft 2020-12, `additionalProperties` is evaluated inside that referenced subschema; properties introduced by a sibling subschema do not reopen it. Therefore:

- omit `function`/`pass_kind` and fail the extraction wrapper's `required`;
- include them and fail the referenced cell's `additionalProperties: false`.

No `ledger_row` can validate. Since the top level requires at least one, no extraction can validate.

The final `quantity` definition repeats the error. It references enrichment's `quantity_candidate`, which is closed with `additionalProperties: false`, then adds `quantity_id` and final target-id arrays in a sibling schema. Including `quantity_id` violates the referenced candidate; omitting it violates the final wrapper.

`unevaluatedProperties: false` on the wrappers cannot undo either referenced schema's rejection.

**Required fix:** factor each reused shape into an extensible common core, then close the discovery/enrichment and final wrappers only after each wrapper declares all of its properties. Alternatively, duplicate the complete closed shape deliberately. Add positive, minimal fixtures for one ledger row and one final quantity and make validation of both a release gate. Negative fixtures alone cannot detect a schema that rejects everything.

## R2-2 — the declared pass load graph still is not dependency-closed

`FR-LOAD-006` now lists pass blocks, but the executable rules do not fit that graph.

### Registration cannot run from its declared load

Registration loads only section 0, section 6, and the selected adapter. `AD-ACRIS-001` nevertheless instructs it to apply `FR-REC-012`, `FR-REC-013`, `FR-DATE-008`, `FR-QTY-005`, and D-9 from sections 4 and 5. These are not explanatory citations: they decide the disposition and referent of present registration values and pointers. The other adapters have the same class of dependency. `AD-BK-001` additionally says to apply `AD-FT-001`, although the selected adapter is BK, so its own declared load excludes the rule it executes.

`FR-LOAD-001` also says to load sections 0–5 plus an adapter, while `FR-LOAD-006` specifies narrow per-pass loads. The framework does not state which manifest is authoritative.

### Discovery retains unavailable actions

The new intended path is that discovery stops after its reread and emits typed uncertainty. But section 1 still says a competing transcription makes `FR-ESC-002(1)` apply, and `FR-SWP-006` also routes to `FR-ESC-002`; discovery does not load section 5 where that rule lives. The same pass is told both to stop and to perform an unavailable route.

### Assembly and schema validation underload their inputs

Assembly excludes section 3 while consuming the `FR-DOC-002` residual product and the `FR-DOC-003` support-registry contract. These may be handoffs, but the framework has no machine-readable distinction between a handoff contract and a rule the receiving pass must apply.

The schema gate is declared to load only section 0 and `extraction.schema.json`, but that schema has more than twenty external references into `discovery.schema.json` and `enrichment.schema.json`. A conforming validator needs those resources in its registry or a generated dereferenced schema.

**Required fix:** make rule dependencies machine-readable as `APPLY` versus `HANDOFF`. Reject every `APPLY` edge outside the pass load. Compile shared adapter logic into a loaded adapter kernel, turn discovery's escalation language into an emitted eligibility handoff, and give schema validation a complete local schema registry or a dereferenced build artifact. Commit the zero-violation dependency report for every pass, module pair, and adapter.

## R2-3 — candidate-claim identity still exists only on the negative path

`FR-SWP-009` says every exclusion and every later resolution names `candidate_claim_id`. The schemas implement exclusions but not the positive side:

- no canonical candidate-claim registry exists;
- event HITs, support-receiving links, and named no-event decisions do not carry the claim id;
- `claim_raw` is optional on the discovery exclusion, so the hash input need not survive discovery;
- the orphan record's checked event ids, paths, and rule ids are optional, so a claimed exhaustive test can serialize without naming what it examined.

The hash tuple `(anchor_id, claim_raw)` also collides when the same claim text occurs twice within one atomic anchor. It needs an occurrence discriminator or exact source-span identity.

One event and one exclusion on the same anchor therefore remain ambiguous: assembly cannot prove that the event resolved a different claim rather than the excluded one.

**Required fix:** add canonical `candidate_claims[]` records containing id, anchor, exact claim span/raw text, and within-anchor occurrence identity. Require the id on every event HIT, `SUPPORT_ONLY` receiving link, and named no-event decision. Make orphan resolution a closed union keyed to that exact id, with nonempty checked targets. Freeze a fixture where one anchor contains two claims, one resolves, and the other remains orphaned, plus a repeated-identical-text fixture.

## R2-4 — one generic `module_path` defeats lane-specific closure

The schema reuses `enrichment.schema.json#/$defs/module_path` for event terms, transaction field operations, observation assertions, notice claims, and conditional deltas. That record requires only `path`, `value_type`, and `support`; `value` and `op` are optional, `value` accepts every JSON type including null, and the same generic `op` enum is available in every context.

The closed schema consequently accepts states the prose explicitly forbids, including:

- a transaction field operation with no `op`;
- an observation assertion with `op: NO_CHANGE`;
- a term carrying `REMOVE_ASSERTED`;
- an assertion with neither a value nor `ASSERTED_NONE`;
- a semantic path whose value is JSON null.

This contradicts `FR-REC-004`, which defines different shapes for field operations and assertions, and the global ban on JSON nulls.

**Required fix:** replace the generic reuse with closed, context-specific records: `term_record`, `field_operation`, `assertion`, `notice_claim`, and `conditional_field_operation`. Require exactly one legal value branch in each, and prohibit operation tokens outside the lanes that define them. Add negative fixtures for every cross-lane counterexample above.

## R2-5 — searched-empty still has two incompatible meanings

`FR-EV-010` and the AS_BUILT card say an unmarked required field is `EMPTY_FIELD_SEARCHED` and emits no evidence atom, anchor, semantic null, or finding. `FR-QTY-002` still says, without a narrower condition, **“blank is UNKNOWN.”** Both rules can apply to a blank numeric form field, and no precedence chooses between them.

The discovery schema also leaves `empty_fields_searched` optional even though `FR-EV-010` says it is recorded once per page-function cell. A reader can omit the count and still validate.

**Required fix:** state that a merely searched blank creates no quantity. `UNKNOWN` is permitted only when independent words or a triggered `required_when` rule establish that a quantity slot exists and its content is missing or unreadable. Require `empty_fields_searched` on every cell, including zero. Freeze a pair consisting of an unmarked numeric box and an independently established-but-unreadable value slot.

## R2-6 — several “closed” semantic records remain arbitrary objects

The enlarged extraction schema closes many prior holes, but these semantic records still accept arbitrary keys and values:

- `bundle_manifest.modules_nominated_not_loaded[]`;
- page and document `page_count_reports[]`;
- `document.index_reported_date`;
- `document.index_reported_amount`;
- `document.current_recording_identity`;
- `document.parcel_inventory[]`;
- `document.notarial_date_anchor`.

`raw_registration` may deliberately be an opaque source blob. The listed records are not opaque: they are interpreted index/document facts whose referent, provenance, and allowed keys are load-bearing. The schema currently accepts an `index_reported_date` carrying invented `applicable_time`, or a parcel inventory object asserting unsupported `ENTIRE_BBL` scope.

**Required fix:** close each semantic/index-report shape and explicitly isolate the one opaque raw-input exception. Add negative fixtures proving that an index date cannot contain event time, and parcel inventory cannot contain event scope, direction, or state.

## R2-7 — `FR-SCHEMA-005` is the wrong kind of thirteenth pass

Separating production from validation is correct. Treating JSON Schema validation as another inference context is not.

1. Draft 2020-12 validation is deterministic computation. A model can hallucinate a PASS and costs more than a conforming validator.
2. The proposed gate underloads its external references.
3. Assembly does not load the schema or the still-deferred canonical template. A post-hoc gate may reject shape but cannot give the producer the shape it must emit.
4. The schema itself says it is “Loaded at assembly and by the schema gate,” contradicting `FR-SCHEMA-005` and the cost model.

If the model gate remains, its stated 17,134-token load omits the referenced discovery and enrichment schemas. Under the declared character estimator those add about 6,614 tokens, so the quoted floor is understated.

**Ruling:** keep the schema closed; do not recover cost by reopening it. Run a deterministic Draft 2020-12 validator with a local registry containing all three schemas, or validate one generated dereferenced schema. Supply assembly a generated canonical template or assembly-specific projection. Remove schema validation from the semantic inference-pass count. Re-measure the producer's projection rather than charging a model to imitate a validator.

## Ruling on the shared-prefix overrun

The 868-token overrun is not, by itself, a release defect; correctness outranks the 6,500 planning target. But it cannot yet be called the price of closure because dependency and semantic closure still fail.

The first cuts should be phase corrections, not weakened rules:

- move `FR-LOAD-006` and its dependency metadata into the compiler/release-gate artifact rather than paying every lens to read build instructions;
- reduce `FR-SER-001` in the shared prefix to the canonicalization invariant actually needed during discovery and keep full serialization in assembly;
- move version-authoring coverage rules such as `FR-EV-008` to the binding version gate while retaining a one-line runtime residue invariant;
- keep only the runtime empty-field invariant in the shared prefix and put the detailed disposition table in the AS_BUILT and support cards that execute it;
- remove rationale duplication only after the dependency graph passes.

Do not cut D-2, evidence proof, candidate identity, the function contrast table, or uncertainty typing to hit 6,500. Measure again after the graph and generated projections exist.

## Cost ruling

The published `178,741 / 399,001` range is not decision-grade on this revision:

- its mandatory schema currently accepts no extraction;
- the schema-gate load omits external schema dependencies;
- the assembly template/projection is unmeasured;
- the load graph is not closed.

If schema validation becomes deterministic, the current model floor is approximately `178,741 - 17,134 = 161,607`, plus the measured assembly template/projection and any corrected pass dependencies. If it remains a model context and loads all schema resources, the floor is about `185,355`. Publish neither as final until the generated artifacts are measured.

## Scope of deferred Returns 1 and 3

I do not reopen the missing build-tool outputs or symmetric partition shadow runner for the proposed blind round, provided its manifest and every later citation say **FULL_BUNDLE_V2 / PARTITION_NOT_TESTED**. The round may not be cited as evidence for byte-identical prompts, build identity, dependency closure, or partition equivalence. Those remain production blockers and section 7 cannot record them as passed.

## Reverification gate

Resubmit after all of the following are true:

1. a positive minimal extraction and positive final quantity validate against all three schemas;
2. every executable pass dependency is inside its declared load, with external schemas locally resolvable;
3. candidate-claim identity survives every positive and negative resolution path;
4. lane-specific semantic records reject cross-lane operations, missing values, and JSON nulls;
5. blank numeric fields have one deterministic disposition and every sweep cell records the searched-empty count;
6. every semantic/index-report object is closed, with raw input explicitly isolated;
7. schema validation is deterministic and assembly receives a generated shape/template;
8. negative fixtures cover the two-claim anchor, repeated claim text, registry-date and parcel smuggling, wrong-lane operations, unresolved external references, and wrong-pass escalation.

Return 7 and the lens-card content do not need another rewrite. Preserve them.
