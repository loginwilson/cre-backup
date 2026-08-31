# Extractor B verification of framework v2

## Verdict: RETURN

v2 is not releasable for round 2. The architecture is materially better than v1, but the committed release cannot construct or verify the partition it specifies, and several committed schemas accept outputs that violate the prose contract. These are not documentation nits: each can produce a complete-looking ledger with missing or misrouted content.

I did not repeat the hash, registry-path coverage, prefix-size, party-split, date-enum, R-1, R-2, or annotation checks already reported by the orchestrator. This review attacks the unproved parts of the build.

## Return 1 — the binding release gate and build do not exist

`framework.md` §5.1 / `FR-SCHEMA-003` requires the build tool—not the reader—to emit `bundle_manifest`; §7 says `version-gate.md` is part of the release and that a release without a completed recorded gate run is invalid. The committed tree contains neither:

- no prompt/compiler or dependency manifest;
- no canonical empty extraction template required by `FR-SCHEMA-001`;
- no `version-gate.md`;
- no frozen fixtures or partitioned runner;
- no recorded gate run.

`v2-notes.md` §§2 expressly records each absence. The only build-named program is the v1-era `bin/buildsize.py`; it measures marked blocks but does not emit prompts, schemas, manifests, or gate results.

This is self-invalidating, not deferred polish. A reader can type `"emitted_by":"BUILD_TOOL"` into the schema-valid manifest even though no build tool exists. Nothing proves which bytes or rules the reader actually held.

**Required before resubmission:** ship the compiler, dependency manifest, canonical template, version gate, frozen fixtures, and a recorded successful gate run. Generated artifacts must carry source hashes. A hand-authored lookalike must fail for a reason stronger than a self-asserted constant.

## Return 2 — per-pass dependency closure fails; the thin cards are source stubs

The cards are not efficient compiled module feed cards. They are eleven short prose paragraphs, 260–435 characters each, followed by references such as `Rows 2, 3`. Concrete loaded-rule failures prove this:

1. A discovery lens loads §0 + §1 + its own §2 card. Yet `FR-ANC-001` in §1 invokes D-2 normalization, which lives in §4, and `FR-EV-005` invokes D-1 and `FR-ESC-002`, which live in §4 and §5. An unlabeled anchor cannot be deterministically identified from the rules the pass actually loads; the reread/derivation/escalation sequence is likewise unavailable.
2. `DOCUMENT_SUPPORT` loads §0 + §1 + §3. `FR-DOC-002` directs it to apply `FR-COV-002` in §5 and backfill through all eleven positive boundary tests while it loads none of the §2 positive cards.
3. Enrichment is also cross-block: for example `FR-DATE-005` and `FR-DATE-007` require the §5 `FR-REC-005`/`FR-REC-006` output contracts.

The content test reaches the same answer. The Title card does not carry the ESTATE_IDENTITY admitted vocabulary for `title.reservations`, `title.exceptions`, or the lease consent, option, default, assumption, rent, and permitted-use paths. A separately printed operative exception or lease term can therefore become a confident Title `NO_HIT` before the module that could receive it is loaded. Encumbrance is fed by both LAND_RIGHTS and SECURED_FINANCE but its card is only a broad noun list, not a compilation of either feed.

This is worse than a loud missing rule: the sweep cell still says `search_completed:true`.

**Required before resubmission:** define machine-readable rule dependencies and compile each pass. A build must reject every reference to an unloaded rule or include the exact compiled dependency. Per-lens cards must be generated from the canonical admitted-path/trigger catalog, with only the target function allowed to emit a HIT. Run a static dependency-closure check and the shadow test in Return 3.

## Return 3 — the required symmetric shadow diff is absent

No operative framework rule or program implements the negotiated shadow-discovery gate. The only mention is in `v2-notes.md`, which says it needs fixtures and a partitioned runner and has not been run.

The gate must compare partitioned discovery with full-bundle shadow discovery after canonical anchor union and fail symmetrically on any unexplained:

- gained or lost anchor;
- gained or lost `HIT` or `SUPPORT_ONLY`;
- gained or lost uncertainty;
- changed uncertainty kind or candidate set;
- gained or lost boundary exclusion.

The comparison must allow only enumerated deterministic normalizations. “Candidate diff” in the escalation payload is not this test. Until this gate exists, the principal risk of partitioning—a missing contract becoming a stronger answer—is wholly untested.

## Return 4 — the three schemas are hand-maintained and do not enforce their own contract

There is no canonical-schema compiler, source dependency manifest, or generated-file metadata. Observable drift already exists.

### Discovery/support schema

- `pass.function` and every `cell.function` are independent. A Title pass can emit Cost cells and validate, although only the target function may HIT.
- `HIT` and `SUPPORT_ONLY` require the `anchors` key but permit `anchors: []`; `proving_span` is optional. A hit with no proving or candidate span validates.
- The framework says every cell carries `question_set_version`; the schema puts it only on the pass envelope.
- `DOCUMENT_SUPPORT` cannot encode its own completion row. Every `cell` requires one of the eleven functions, while `DOCUMENT_SUPPORT` is not a function. Assembly then stores only the cells in `function_sweep_ledger`, discarding pass identity. `MX-VIEW-002` nevertheless requires the support row. The required rendering is unconstructable from a conforming extraction.

### Extraction schema

- Lane character is not fixed: a `transactions[]` member can validate with `epistemic_character: NOTICE`, and an observation can validate as `TRANSACTION`.
- Structures advertised as closed remain arbitrary objects, including `document`, derivation records, temporal boundaries, notice claims, conditional `would_be_delta`, reference components, several exception members, and field conflicts.
- `validation.checks` enforces a length of eleven but not one occurrence of each ordered `FR-QC-001`…`011`; eleven duplicates validate.

These directly contradict `FR-SCHEMA-001` (“fixes every nested … shape”) and `FR-SCHEMA-004` (“exactly eleven ordered records”). Semantic QC cannot rescue a schema whose stated purpose is to make alternate shapes unconstructable—especially when no QC runner ships.

**Required before resubmission:** establish one canonical schema source and generate the discovery micro-schema, enrichment schema, extraction schema, and empty template from it. Add lane constants, target-function coupling, nonempty proving anchors, support-pass identity, exact validation-check order, and closed definitions for every semantic object. Ship negative fixtures demonstrating that each counterexample above is rejected.

## Return 5 — `BOUNDARY_ORPHAN` is still anchor-level in the data model

`FR-COV-005` has the right prose: resolve the exact candidate claim, not the anchor. The schemas cannot carry that distinction:

- a discovery `boundary_exclusion` contains only `anchor_id`, `excluded_to`, and optional `rule_id`—no candidate-claim id;
- the final orphan has one anchor id and an optional free-text `candidate_claim`;
- `resolution_link.checked` is optional and need not contain the three required tests;
- there is no stable link from the claim to a particular exclusion, event HIT, support receiving path, or no-event rule.

Two candidate claims on one clause therefore collapse. A correct `SUPPORT_ONLY` disposition for claim A can appear to resolve excluded claim B, or both can be reported as one orphan.

**Required before resubmission:** assign a stable `candidate_claim_id` before exclusions; require it on every exclusion and orphan; make the three resolution tests exhaustive and link each result to the exact receiving event/path/rule. Add a fixture with two claims on one anchor, one resolved and one orphaned.

## Return 6 — v2 violates its own pattern-coverage rule and manufactures blank-field findings

`FR-EV-008` binds the framework authors: every filler set, literal alias, label list, and trigger phrase must state observed coverage and residue. v2 does this correctly for the FT zip filler, but not systematically:

- the closed legal-designator tokens have no observed coverage;
- the Richmond legacy/later aliases and additional literal labels have no counts, coverage, or residue;
- module term paths say they emit “only on their phrases” without enumerating the phrase set or its residue;
- the AS_BUILT card requires visiting every labelled measurement field and calls an **empty** field a finding under `FR-EV-001a`, while `FR-EV-001a` applies only to a **visible mark** bearing no readable character. An empty field has no mark, no proving span, and no candidate transcription.

The last rule turns exhaustive search into affirmative noise: blank form fields become findings, and a 27B reader is explicitly told to create them. `v2-notes.md` acknowledges that its residue is unknown.

**Required before resubmission:** distinguish `EMPTY_FIELD_SEARCHED` (a search result that creates no semantic null or evidence atom) from `VISIBLE_UNREADABLE_MARK` (the `FR-EV-001a` path). For every literal/pattern table, include observed coverage plus residue behavior, or mark the claim unmeasured and route every unmatched value without suppression. Gate `FR-EV-008` mechanically.

## Return 7 — `FR-DATE-006a` regresses an adjudicated round-1 result

Both round-1 cross-examinations concluded that the Article 18 clause was a conditional Encumbrance: its stated condition made a different provision govern the already emitted Declaration-burden object's `encumbrance.legal_scope`. A's own V2-09 proposal preserved that result while excluding pure severability language with no named path.

Committed `FR-DATE-006a` instead says that a consequence under which “other terms continue to govern” fills no path and is `NO_EVENT / BOILERPLATE_EXCLUDED`. That suppresses the exact qualifying clause the proposal was designed to retain. The failure is silent: no event or exception remains to expose it.

**Required before resubmission:** restore the narrower materiality test: emit when the consequence identifies a module path and keyed state object touched by a present act; exclude only clauses whose consequence names no filled path. Freeze the Article 18 case and a pure severability control as a pair.

## What does not need to be reopened

No objection from this review changes the adopted party-registry split, per-party allocation prohibition, two-clock physical lanes, multi-parcel bindings, geometry-only annotation adjudication, or matrix Title query contract. The problem is that the committed build cannot yet guarantee those sound decisions reach a reader or survive serialization.

## Reverification gate

Resubmission is ready for another verification only when all seven returns above are addressed and the following artifacts are committed together:

1. canonical source schema and generated three-schema suite plus empty template;
2. dependency manifest, prompt compiler, and emitted prompt/bundle manifests;
3. byte-identity and static dependency-closure reports for all twelve semantic passes;
4. symmetric shadow-diff runner and successful frozen-fixture result;
5. `version-gate.md` and a completed recorded gate run;
6. negative schema fixtures for target-function coupling, support-row identity, lane character, claim-level orphaning, and ordered QC ids;
7. paired fixtures for AS_BUILT blank versus unreadable mark and Article 18 conditional versus pure severability.

Until then, running round 2 would test an unbuilt partition and an internally nonconforming schema, not v2 as specified.
