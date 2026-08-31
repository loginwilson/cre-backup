<!-- BUILD:CORE -->
# NYC C.R.E.D. extraction framework v1

This rulebook turns one supplied recorded-instrument package into a provenance-closed event table. Rule ids are immutable: a later version may amend or retire a rule, but never reuse its id for a different decision.

## 0. Loading and execution contract

**FR-SCOPE-001 — Inputs.** The only semantic inputs are the supplied document id, raw `registration.json`, and every supplied page image. Read the document independently. Do not use another instrument, parcel history, website, map, law lookup, slate field, local path, URL, filename, or pipeline timestamp to supply a value.

**FR-SCOPE-002 — Knowledge boundary.** Domain knowledge may decode words visible in an allowed input. It may not add a party, role, amount, semantic kind, date, parcel, priority, duration, legal effect, relationship, or status not supported by a quote or an admitted derivation.

**FR-SCOPE-003 — Provenance closure.** Every emitted scalar, sentinel, classification, link, and normalized value terminates in either `QUOTE` support or one stable rule id in the loaded bundle with all input paths named. A correct value with neither is a defect. A rule outside the loaded bundle is not an allowed derivation.

**FR-LOAD-001 — Marked bundle.** Load `BUILD:CORE` and the one FR-LOAD-002 adapter. Inventory/segment pages; nominate modules from adapter classification, visible self-title, headings, and operative verb/object pairs; load every content-confirmed trigger. Registration type only nominates. Hybrids load several modules. A late trigger requires loading it, updating the manifest, and restarting discovery from the coverage ledger.

**FR-LOAD-002 — Adapter selection.** Select by document-id namespace only: prefix `RC_` → `RICHMOND`; `FT_` → `FILM_FT`; `BK_` → `FILM_BK`; all-decimal id → `ACRIS_DIGITAL`. Any other namespace is `FRAMEWORK_GAP`; do not guess an adapter.

**FR-LOAD-003 — Module manifest.** The available act modules and positive triggers are:

| module | load when a visible clause/form expressly concerns |
|---|---|
| `ESTATE_IDENTITY` | parcel/unit identity; possessory fee, leasehold, subleasehold, common, life, or other estate |
| `SECURED_FINANCE` | debt/credit; security, rents/proceeds, UCC, priority, assignment, release, satisfaction, modification |
| `LAND_RIGHTS` | easement/covenant/restriction; development/air/subterranean right, zoning-lot relation, form constraint, private land-use privilege |
| `PUBLIC_PHYSICAL` | government permit/approval; occupancy, survey, completion, installed item, present condition/use |
| `ECONOMICS` | consideration/value, project expenditure, tax, filing/recording fee |
| `NOTICE_AUTHORITY` | notice of an elsewhere-made act, authority-only material, raw cross-document pointer |
| `GENERIC_GAP` | a section contains an apparent matrix-relevant act but no prior module trigger matches |

The trigger is the stated act/object, never an instrument-type name. `GENERIC_GAP` cannot invent paths; it produces a framework-gap record naming the section and missing path family. A package with no function-filling section may validly emit zero events without loading it.

**FR-LOAD-004 — Execution order.** Apply: adapter → page inventory → section coverage ledger → evidence registry → D-1 reread where needed → module confirmation → event/registry extraction → escalation if admitted → merge-back → stable ids → QC → canonical serialization. Matrix resolution is a later phase governed by `matrix-spec.md`; no extractor decision may depend on a rule found only there.

**FR-LOAD-005 — Vocabulary drift.** Adapters use per-label historical alias maps, never one modern lookup or registry-wide cutover. Unknown/broad labels nominate nothing but cannot suppress content discovery. Audit mapping/coverage by registry, literal, and recorded-year band; label era never changes clause confirmation.

## 1. Pages, sections, and coverage

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

Store legibility separately as `CLEAR`, `PARTIAL`, or `UNREADABLE`; a partly legible page never becomes a semantic page class.

**FR-PAGE-002 — Page-count reports.** Record each visible or registration page count as a separately quoted report with its raw label and apparent scope. Never use it as the extraction inventory and never force unlike reports to agree. A cover `PAGE 1 OF 5`, cover field `Document Page Count: 3`, registration `pages: 5`, and eight supplied images may all coexist. Only a missing/duplicate image against the supplied package manifest is an input-integrity failure; count disagreement alone is not.

**FR-PAGE-003 — Incorporation.** Treat an attached page as instrument content on the first satisfied test: (a) exact body label and page label match; (b) an explicit `annexed/attached hereto` reference plus exactly one unattached page whose visible subject matches the named subject; (c) uninterrupted executed pagination/title plus signature or initials continuity. Record the test and both section ids. If none succeeds, classify the page normally; a matrix-relevant inclusion question becomes `UNRESOLVED_SECTION` and may satisfy FR-ESC-002.

**FR-PAGE-004 — Marks.** A handwritten/typed insertion in an executed blank controls the preprint in that blank. A checked option is present. An unchecked option is not its negation. Struck or obliterated text is not positive evidence; a visible replacement is evidence. Do not restore obliterated content from context or registration.

**FR-COV-001 — Sectioning.** In page order, segment every heading, paragraph, numbered/lettered clause, form row/field, definition, signature block, acknowledgement, exhibit item, and administrative region that can receive a separate disposition. Assign `pNN-sMM` in visible reading order. A section stores page, controlled zone (`TOP`, `UPPER`, `MIDDLE`, `LOWER`, `BOTTOM`, `MARGIN_L`, `MARGIN_R`, `STAMP`, `HANDWRITTEN`), occurrence ordinal in that zone, class, and legibility.

**FR-COV-002 — One disposition.** Every section has exactly one disposition:

- `EVENT` with one or more event ids;
- `VALUES_ONLY` with receiving registry/event paths;
- `REFERENCE_ONLY` with external-reference ids;
- `NO_EVENT` with one reason: `ADMINISTRATIVE`, `BLANK`, `SIGNATURE_ONLY`, `ACKNOWLEDGMENT_ONLY`, `NOTICE_ADDRESS`, `DEFINITION_ONLY`, `HISTORICAL_RECITAL_ONLY`, `BOILERPLATE_EXCLUDED`, `DUPLICATE_DISPLAY`, or `OTHER_RULED` plus rule id;
- `UNRESOLVED_SECTION`, which can never accompany validation `PASS`.

**FR-COV-003 — Coverage closure.** Every supplied page/section appears once; every event, registry value, evidence atom, and pointer links to a section. Zero events is complete only when every section has a non-event disposition and none fills a function path. Count pages, sections, event/value/reference/no-event dispositions by reason, unresolved sections, emitted fields/events, flags, illegible fields, and escalation outcome.

## 2. Evidence and admitted derivations

**FR-EV-001 — Evidence atom.** Assign evidence ids `E001`… in page/section order, then registration-path order. Store `source_kind` (`PAGE_IMAGE` or `REGISTRATION`), section id or raw JSON path, controlled zone and occurrence ordinal for images, shortest verbatim span sufficient to prove the field, `legibility`, and candidate readings when partial. Preserve visible characters, spelling, capitalization, punctuation, handwriting/strike status; collapse visual line breaks and spacing runs to one ASCII space. A visible table cell is quoted as label plus value. Never cite a path, URL, filename, query, inferred page number, or slate value.

**FR-EV-002 — Semantic proof.** A quoted passage must prove that exact semantic field, not merely contain the same number, name, or date. Presence is not proof. `$2,102.00` labeled transfer tax cannot support `FULL_SALE_PRICE = 525500`.

**FR-EV-003 — Derived support.** A derived field uses `{kind: RULE, rule_id, inputs}`. Every input path has closed support. Store a `derivation_record` when a D-rule requires audit details. A derivation may cite evidence as context but never masquerades as a quote.

**FR-EV-004 — Source authority is field-local.** Choose the highest available source for the exact field:

| field | controlling order |
|---|---|
| present legal act, object, effect, operative party role, rights, duties, conditions, applicable time | executed operative clause → incorporated directed schedule/rider → executed form performing that act → visible cover |
| signature, capacity, authority, acknowledgement | executed signature/authority/acknowledgement section → operative clause → visible cover |
| indexed classification, current recording id/time, indexed BBL/unit/extent | image cover → adapter-normalized registration → body |
| transfer-report value/use and tax-return field | executed named form/return → same-kind image cover field → image-proven same-kind registration report |
| debt/security economics | executed debt/security clause → directed executed modification/schedule → same-kind image cover field |
| named tax/fee amount | executed same-kind return/receipt → image cover label → image-proven same-kind registration report |

Same-rank incompatible values remain field-local candidates after testing distinct scopes/kinds and express correction. A lower-rank difference is `source_discrepancy`, not automatically document ambiguity. Nominal consideration and full sale price are different kinds.

**FR-EV-005 — Illegibility sequence.** Read the supplied render; if a matrix-relevant character remains uncertain, use one 900-dpi full-page or lossless crop reread. Then apply D-1 if eligible. If two graphic candidates still alter function, mode/character, placement, state path, quantity/term, pointer, or coverage disposition, test FR-ESC-002. Registration may corroborate its own indexed field but never repair body text.

**FR-EV-006 — Registration referent firewall.** A declared path proves index location, not semantic referent. Registration fills event quantity/term/time/role/share/scope/state only when image evidence proves that referent; otherwise retain an index report with referent `UNKNOWN`. Current id/time, page reports, raw pointers, indexed names, and parcel candidates are technical reports, not event semantics. Type/co-occurrence never chooses.

**FR-DER-001 — Closed derivation registry.** The loaded bundle's stable classification rules and D-1 through D-10 below are the complete extraction derivation set. No analogy, plausibility, customary rule, unstated conversion, or unlisted calculation is admitted.

**D-1 — Intra-document digit exemplar comparison.** Apply only after FR-EV-005 and only to one ambiguous Arabic digit `0–9`.

1. Before exemplar search, record the target location and a visually derived candidate set of exactly two digits. Field meaning, arithmetic, registration, expected content, and outside knowledge may not supply either candidate. This order claim is auditable but not fully provable from final output; fresh-context frozen reruns are the independent check.
2. Admit one `writer_cluster_id` only by `CONTINUOUS_ENTRY` (target and exemplars lie in one uninterrupted handwritten entry) or `CROSS_ENTRY_STYLE_MATCH` (at least three distinct certain non-target glyphs recur in both entries and match, with no mismatch, on recorded loop topology, connected-component form, slant bucket, terminal direction, and relative height). Ink color, tone, line weight, page proximity, subject matter, and registration are insufficient; bitonal scans destroy the first three as reliable campaign evidence.
3. Inventory every certain occurrence of each candidate digit in the admitted cluster; do not select convenient exemplars. Before choosing, record features invariant across each candidate class. The target matches a class only when it matches every invariant. Where competing-class exemplars exist, it must fail at least one invariant of that class.
4. Resolve two-sided when the selected digit has at least two certain exemplars, all inventoried forms are consistent, and the competing class does not match. Resolve one-sided only when the pre-recorded set is binary, the selected digit has at least two certain exemplars, every occurrence is inventoried, at least two independent construction features recur in all and in the target, no exemplar contradicts, and no competing exemplar exists. Absence of the competitor is not evidence; positive recurrence is. Record `TWO_SIDED` or `ONE_SIDED`, every location, count, inventory scope, features, and output digit.
5. Otherwise keep both candidates and continue to escalation. D-1 never infers a field's content or semantic kind.

Letters, punctuation, signs, ligatures, and whole tokens are deferred, not permanently excluded. Their recoverable loss—including handwritten party names—must be counted; extend only through a separate frozen fixture and enumerated rule.

**D-2 — Scalar normalization.** Normalize a certain quoted scalar without changing meaning: Unicode NFC; trim edge whitespace; collapse internal whitespace for normalized names; uppercase normalized names/identifiers; remove money grouping; map a visible `$` to `USD`; reduce a stated fraction; preserve leading zeros in identifiers; parse only an unambiguous four-digit-year date to ISO. Store raw and normalized forms. Never expand a two-digit year.

**D-3 — Canonical BBL.** From cited borough plus block plus lot, map borough `Manhattan/New York=1`, `Bronx=2`, `Brooklyn/Kings=3`, `Queens=4`, `Staten Island/Richmond=5`; left-pad block to five and lot to four digits. Do not derive any component from address or geometry.

**D-4 — Partial-date interval.** A stated four-digit year becomes the closed Gregorian interval January 1–December 31; a stated month becomes its first–last calendar day; a day has equal endpoints. Preserve precision. Never print a padded day as the stated value.

**D-5 — Document-stated arithmetic.** Derive a numeric result only when the document itself states an exhaustive equation, subtotal/total relationship, or formula; every operand is quoted; and operators are limited to exact `+`, `−`, `×`, `÷`. Record expression and exact inputs. A displayed total, when present, is the source and arithmetic is validation. External rates/constants, tax-rate back-computation, plausible components, and division by zero are excluded.

**D-6 — Explicit allocation.** Allocate one quoted total only when the document states exhaustive target shares or a complete formula. Record exact rational/decimal arithmetic, targets, and remainder; allocations must sum exactly to the stated total when the text says exhaustive. Otherwise retain one `NOT_DERIVABLE` total.

**D-7 — Express equality/definition.** Propagate a value within this document only when an exact definition, equation, or incorporated schedule says the two named fields/terms are identical. Similar labels, values, parties, or context are insufficient.

**D-8 — Controlling-source selection.** Select among already typed same-field candidates by FR-EV-004 after separating semantic kind and scope. Record every candidate, ranks, selected input, and lower-rank discrepancies. This never changes a candidate's semantic kind.

**D-9 — Pointer parsing.** Split a quoted external locator into only visibly present components (document id, `CRFN`, file number, borough/year/reel/page, reel/page, book/page, instrument, map sequence, or `OTHER`). Preserve `locator_raw`; parsing never resolves a target document.

**D-10 — Exact local linkage.** Reuse an in-document object/value reference only on an exact recorded identifier, exact defined local name, exact section/schedule pointer, or a demonstrative whose grammatically available antecedent set contains exactly one keyed object. Similar parties, amounts, dates, parcels, or event proximity are not linkage.

## 3. Output lanes and record schemas

**FR-REC-001 — Canonical envelope.** `extraction.json` has keys in this order:

`framework_version`, `bundle_manifest`, `document`, `page_inventory`, `coverage_ledger`, `evidence_registry`, `derivation_records`, `party_registry`, `quantity_registry`, `external_reference_registry`, `evidence_time_registry`, `transactions`, `observations_dated`, `observations_unplaced`, `notices`, `conditional_events`, `temporal_boundaries`, `ordering_relations`, `exceptions`, `counts`, `validation`.

There is deliberately no single `events` array.

**FR-REC-002 — Physical lane separation.** Lanes are exclusive: `transactions` holds unconditional state acts; `observations_dated` observations with supported valid intervals; `observations_unplaced` those without one and without any date-shaped sort field; `notices` acts/claims made elsewhere; `conditional_events` condition-dependent transaction effects. Membership—not a discriminator—enforces the boundary. Observation/notice records carry an `evidence_time_registry` id, never its time; the state resolver never receives that registry.

**FR-REC-003 — Shared event core.** Every lane record contains:

| field | content |
|---|---|
| `event_id`, `event_group_id` | FR-REC-007 ids |
| `section_ids`, `module_ids`, `bundle_hash` | coverage/rule bundle |
| `epistemic_character` | transaction/conditional=`TRANSACTION`; observation=`OBSERVATION`; notice=`NOTICE` |
| `function`; `mode` or `would_be_mode` | one function; conditional has would-be mode only |
| `state_object_key`, `object_type` | FR-REC-008 identity/module token |
| `interest_kind` | mandatory for Title; absent otherwise |
| `parties`, `direction` | participation/direction records |
| `parcels` | affected BBL/scope/role only |
| `quantity_ids`, `terms`, `external_ref_ids` | registry ids/module paths |
| `support` | function/mode/object/placement proof |
| `field_conflicts`, `document_flags` | scoped final findings |

Do not populate global placeholder fields. A module path exists for an event only when that module's `required_when` test succeeds; a required but unstated path is `UNKNOWN`. A path outside the triggered schema is absent.

**FR-REC-004 — Lane-specific content.** A transaction adds `applicable_time` and ordered `state_delta`. A dated observation adds `asserted_valid_time` and ordered `assertions`; it has no occurrence-time field. An unplaced observation adds `unplaced_reason` and `assertions`; it has no date or interval key. A notice adds `notice_claims` and raw pointer ids but no composed-state delta. A conditional event adds `would_be_mode`, ordered `would_be_delta`, and `condition` (verbatim trigger, consequence, status), but no active delta or unconditional applicable-time key.

`state_delta` has `lifecycle_op` (`ACTIVATE`, `PRESERVE`, `DEACTIVATE`, `ASSERT_STATE`) and module-admitted field operations `{path, op, value, value_type, support}` where `op` is `SET`, `REMOVE_ASSERTED`, `NO_CHANGE`, or `UNKNOWN`. Observation `assertions` use `{path, value|ASSERTED_NONE, value_type, scope, support}` and never lifecycle operations.

**FR-REC-005 — Time registries.** In source-section order assign `<document_id>-T001`… to every observation/notice and `<document_id>-B001`… to boundaries. Each evidence-time item has id, event id, and either supported occurrence interval/basis/support or `UNKNOWN` plus reason. A boundary records id, source event, affected object/function/parcels, type (`COMMENCEMENT`, `MATURITY`, `EXPIRATION`, `OPTION_OPEN`, `OPTION_CLOSE`, `RENEWAL_DEADLINE`, `OTHER_NAMED` plus raw label), interval, consequence, condition, and `effect_status` (`INFORMATIONAL` or module-admitted `SELF_EXECUTING`). Self-executing boundaries add module-admitted `boundary_delta`; informational ones cannot. A boundary is not another event.

**FR-REC-006 — Ordering relations.** In first supporting-section order assign `<document_id>-O001`…. Store top-level relations `{relation_id, type, before_event_or_group_id, after_event_or_group_id, support}`. `type` is `BEFORE`, `AFTER`, or `SIMULTANEOUS`; normalize `AFTER` to the corresponding edge for resolution. Emit only when exact wording orders the present acts. Page order, signature order, event id, mode, recording timestamp, and customary closing sequence never create a relation.

**FR-REC-007 — Stable ids.** Segment the coverage ledger first. Sort the combined final event set by first section id, clause order within section, fixed function order in FR-FN-001, object first-mention order, then mode order `CORRECT`, `TERMINATE`, `TRANSFER`, `MODIFY`, `CREATE`, `ASSERT`. Assign `<document_id>-E001`… across all physical lanes. Events from one act share `<document_id>-G001`… ordered by that act's first section. Recompute after valid escalation merge; identical final events receive identical ids regardless of discovery order or date interpretation.

**FR-REC-008 — State-object key.** Choose first applicable: exact recorded identifier; exact defined instrument-local name/unit; D-10 link to an earlier keyed object; identified agreement; otherwise local first-mention ordinal. Normalize components with D-2 and percent-escape `%` and `:`. Prefix function. For Title the key must also contain mandatory interest kind: `TITLE:<INTEREST_KIND>:<identity>`. Do not merge keys by similar parties, values, dates, or parcels. Linked functions use separate keys and one group id.

**FR-REC-009 — References versus current identity.** Current recording identifiers live in `document.current_recording_identity`. A pointer to another recording lives only in `external_reference_registry`. Neither substitutes for the other.

**FR-REC-010 — Document/adapter record.** `document` contains document id, adapter id/version, exact raw registration, path inventory, normalized index classification/reported-date/recording fact/current identity/parties/parcel inventory/reported amount/page-count reports, notarial-date anchor, image count, and package hash. Declared nonsemantic keys remain archived/excluded from semantic provenance; normalized values cite only adapter-declared citable paths.

**FR-REC-011 — Mode-to-delta map.** For a transaction, CREATE maps to `ACTIVATE`; MODIFY, TRANSFER, and CORRECT to `PRESERVE`; TERMINATE to `DEACTIVATE`; module-admitted transaction ASSERT to `ASSERT_STATE`. Field operations remain module-controlled. A conditional event applies the same mapping to `would_be_mode` only inside `would_be_delta`; it never becomes active state before matrix condition resolution.

**FR-REC-012 — Registration path closure.** Each adapter begins with machine-readable `REGISTRATION_PATHS_JSON = [...]`. Inventory every populated scalar/object/array path and give it disposition `NORMALIZED_INDEX_FACT`, `RAW_CITABLE`, `POINTER_SOURCE`, `DECLARED_NONSEMANTIC`, or `UNMAPPED`, with receiving path/rule. `UNMAPPED` is a framework gap and validation FAIL; never treat an unknown field as absent or silently nonsemantic.

## 4. Find, classify, split, and merge

**FR-PKG-001 — Candidate trigger.** For every section, identify each present-tense operative verb/object pair that grants, conveys, leases/demises, assigns, assumes, creates, amends, corrects, subordinates, releases, terminates, files, certifies, approves, revokes, or expressly declares a matrix state. Also identify each signed/certified assertion of a current or explicitly dated state. Test all eleven functions; emit one single-function event for every independently filled module path. One clause may yield linked events; sharing a clause alone never requires several.

**FR-PKG-002 — No-event content.** Do not emit for a historical recital alone, definition alone, signature/acknowledgement alone, notice/return address, preparer/notary/fee-routing metadata, form id, unchecked alternative, general warranty/boilerplate without a filled state path, legal description used only as another event's scope, or a reference to an unseen act. Definitions may supply values. Give each excluded section its FR-COV-002 disposition.

**FR-PKG-003 — Assertion and absence.** Emit an observation only when executed words assert a function path, including an express scoped absence. An assertion that no encumbrance, assignment, permit, occupancy, equipment, or other path exists is `OBSERVATION + ASSERT` with `ASSERTED_NONE`, stated scope, affected parcels, and asserted-valid time when stated. A blank, unchecked box, covenant only against one party's own acts, or promise about future conduct is not a parcel-state absence assertion.

**FR-PKG-004 — Split dimensions.** Split when any of these differs: function; state-object key; mode; applicable/valid time; unconditional versus condition-dependent effect; FROM/TO party set or share; independently operating parcel set; or noncommuting field paths. Keep asymmetric parcel roles of one transaction together. Keep one amount shared through its quantity id.

**FR-PKG-005 — Merge test.** Merge adjacent candidate sections only when all are equal: state-object key, function, mode, epistemic character/lane, time object/status, party-direction set, affected BBL/scope set, and event condition; and their field operations commute. Preserve every section/evidence id. Similar parties, amount, date, or parcel never supplies object equality.

**FR-MODE-001 — Ordered mode test.** After scope splitting, take the first match:

1. words identify a prior value in this same object/act as erroneous/omitted and replace/delete it → `CORRECT`;
2. words end the whole identified object/effect → `TERMINATE`;
3. words move an existing object/interest/obligation between holders with its identity continuing → `TRANSFER`;
4. words change an identified continuing object's field/scope/priority; a partial release is here → `MODIFY`;
5. words bring the object/right/obligation into existence → `CREATE`;
6. words state a condition without changing it, or legally establish a declaration without creating the described thing → `ASSERT`;
7. none → no event for that clause/function.

Two same-rank incompatible modes after scope splitting create a core-classification candidate package; do not use later page order.

**FR-CHAR-001 — Epistemic character.** `TRANSACTION` performs the act; `OBSERVATION` states evidence about state without changing it; `NOTICE` reports/indexes a claim or act made elsewhere without proving it now. Observation/notice use ASSERT or CORRECT. Transaction uses other modes, except a module-admitted declaration that legally establishes a path may use ASSERT. The set is closed.

**FR-FN-001 — Function test and order.** Test every module-admitted path in this fixed order. A function fires only when a path in its loaded module is filled or required-UNKNOWN by a present act/assertion.

| function | boundary question |
|---|---|
| `IDENTITY` | Does the act/assertion establish or change formal parcel/unit identity, boundary, composition, designation, name, or address? Routine premises description is scope only. |
| `TITLE` | Does it create, transfer, correct, surrender, or terminate ownership or an expressly possessory estate? |
| `ENTITLEMENT` | Does it grant/change a non-possessory land-use/development capacity, right, option, or authorization? |
| `ENVELOPE` | Does it legally constrain or allocate physical mass/form—height, setback, bulk, area, facade, structural envelope—even without a number? |
| `ENCUMBRANCE` | Does it create/change a lien, security interest, easement, covenant, land-running burden/benefit, rents assignment, or priority relation? |
| `CAPITAL` | Does it create/change a debt, facility, funding/equity obligation, principal/balance, repayment, or finance term? |
| `PERMIT` | Does a named government authority receive, issue, amend, suspend, renew, or revoke authorization for work/regulated operation? |
| `AS_BUILT` | Does it observe/assert what physically exists or was completed? |
| `OCCUPANCY` | Does it observe/assert actual use/capacity or government-authorized use/capacity, with basis distinguished? |
| `COST` | Does it state project expenditure/commitment or a labeled transaction/filing tax or fee? |
| `VALUE` | Does it state sale/nominal consideration, assessed/appraised/fair-market value, or another property/interest valuation? |

**FR-FN-002 — Mandatory boundary tests.** Apply every matching row:

- Express debt and collateral → linked Capital+Encumbrance; one layer alone → only its function. Lien/UCC release and payment never imply each other.
- Possessory lease creation/transfer/surrender/termination → Title leasehold; memorandum of an elsewhere-made lease → Title NOTICE. Lease/rent security → Encumbrance/Capital per clause; fee burden requires separate express words.
- Easement/covenant → Encumbrance; add Envelope for physical mass/form, Entitlement for granted development capacity, Title only for express possession. Air/subterranean interests follow the same possessory/right/burden/form split.
- Zoning-lot composition/geometry → Identity; capacity/right → Entitlement; bulk/form constraint → Envelope. Agency/application naming is not Permit.
- Government-authorized use → Occupancy `AUTHORIZED`; express actual use → `ACTUAL`; private use restriction → Encumbrance.
- Government work/operation authorization → Permit; private/title-company certification is not Permit.
- Sale/nominal consideration → separate Value kinds; project expenditure → Cost; financing principal → Capital; labeled tax/fee → Economics.
- General deed warranty/covenant is a Title term. Encumbrance-absence observation requires express present absence of a named/scoped burden.
- Contract of sale creates no categorical event. Emit only expressly filled rights/options/burdens; never import equitable conversion.

**FR-FN-003 — Title precondition.** Every Title event and object has a mandatory `interest_kind` from its module, and its key contains that kind. Fee and leasehold objects coexist. When the leasehold has no separate indexed BBL, place it on the indexed fee BBL under its separate Title key. Any extraction representation that cannot preserve concurrent estate objects fails validation and invokes the R-1 inversion; v1's representation is designed to preserve them.

## 5. Time, conditions, and sequence

**FR-DATE-001 — Transaction applicable time.** Take the first supported source: (1) `effective/as of/from/commencing/terminated on` phrase grammatically attached to the present act, or module-listed equivalent; (2) present-instrument dating clause governing it; (3) latest required execution date when all named operative parties are expressly required before effect; (4) dated execution of a unilateral act effective on execution; (5) acknowledgment expressly proving execution date; (6) UNKNOWN. Basis is respectively `EXPLICIT_EFFECTIVE`, `INSTRUMENT_DATE`, `COMPLETION_OF_REQUIRED_EXECUTION`, `EXECUTION_DATE`, `ACKNOWLEDGED_EXECUTION`, or `UNSUPPORTED`. Index/cover Document Date is only a candidate unless an operative clause incorporates it or a module form makes that label the act/as-of date.

**FR-DATE-002 — Recording never applies.** Registration/cover recording time is a registry fact only. It is never transaction applicable time, observation asserted-valid time, a latest bound, an undated sort key, or a tie-break—even when filing/recording is the legal mechanism and every other date is absent.

**FR-DATE-003 — Observation clocks.** Derive statement/occurrence time into `evidence_time_registry` only from an express date when the statement, certification, report, or affidavit was made. Derive asserted-valid time only from words stating when the observed condition/value held (`as of`, inspection/survey/valuation date, `since`, `during`, `from…to`, or an exact form label directed to the observation). An inspection date is valid time, not statement time, unless the text expressly makes it both. Never copy occurrence time into valid time. Route a supported valid interval to `observations_dated`; otherwise route to `observations_unplaced` and emit no date-shaped key there.

**FR-DATE-004 — Partial/conflicting dates.** Normalize with D-4. Keep day/month/year precision. Resolve same-field evidence through FR-EV-004; same-rank incompatible candidates remain UNKNOWN and may escalate if reader-resolvable. A referenced instrument date, preparation date, tax-report date, acknowledgement not proving execution, and temporal boundary are not the present act's time.

**FR-DATE-005 — Boundaries.** Promote stated commencement, maturity, expiration, option windows, renewal deadlines, and other future boundaries under FR-REC-005. A boundary changes composed state only when exact words make the consequence automatic without an unresolved condition and the loaded module marks that path `SELF_EXECUTING`. Mortgage maturity never means payment/lien termination; option close never means exercise.

**FR-DATE-006 — Conditional effect.** If an effect depends on a condition the document does not state has occurred, route it to `conditional_events`, quote trigger and consequence, and emit no unconditional applicable-time key. `CONDITION_DEPENDENT` is not `UNKNOWN`. If this document states occurrence, cite it and route the resulting dated/partial act normally. Future promises/remedies not presently effective remain terms or conditional events, never fabricated present state.

**FR-DATE-007 — Sequence.** Capture only exact present-act ordering language under FR-REC-006. `Simultaneously herewith` creates `SIMULTANEOUS`; `immediately prior/before` and `immediately after` create directed relations. Customary deed/purchase-money-mortgage order is not evidence.

**FR-DATE-008 — Index-reported date referent.** Retain registration `doc_date` as `document.index_reported_date`, referent `UNKNOWN`. Change the referent only when allowed input structurally nests it under or visibly labels a named current act, reference, or object. Field name/type, numerical agreement, file-number digits, recording time, and form revision date supply neither referent nor century. Unknown-referent dates fill no event/evidence/boundary time.

**FR-DATE-009 — Canonical notarial anchor.** In `document.notarial_date_anchor`, record `PRESENT`, quote, and full-word/four-digit date from an executed acknowledgment's fixed `On … in the year …` wording; else `NOT_PRESENT`. It is the canonical internal century anchor but proves only acknowledgment occurrence and supplies applicable time only under FR-DATE-001(5). Another date needs an admitted exact link to borrow it. Count absence; financing statements commonly lack acknowledgments.

## 6. Parties and parcels

**FR-PARTY-001 — Registry.** Create `<document_id>-P001`… per distinct operative person/entity in first operative-mention order. Store `name_raw`, D-2 normalized name, explicitly equated aliases, and support. Reuse only on exact raw recurrence or express equation. The same party may have several participation records/capacities; a representative named only as representative is authority data, not a separate operative party.

**FR-PARTY-002 — Roles and capacity.** The body's operative grammar controls legal role. Preserve visible `role_raw`; assign a module-controlled role from who performs/receives the verb. Cover panel numbers have no role meaning. Richmond `parties[].role` and cover role labels are `indexed_role` only unless body words expressly delegate to them. Preserve capacity/relationship verbatim; do not turn spouse, trustee, custodian, affiliate, or officer language into identity, share, tenancy, or personal obligation.

**FR-PARTY-003 — Direction and shares.** `DIRECTIONAL` requires a supported FROM side parting with/bearing an identified interest/object/obligation and a supported TO side receiving/holding it. Otherwise `NON_DIRECTIONAL` and sides `NONE`. Several parties per side and several roles per party are allowed. Extract exact shares; applicable unstated shares are `UNKNOWN`. Never infer equality, marital ownership, or proportionality.

**FR-PARTY-004 — Index coverage QA.** Compare deduplicated adapter party entries to operative parties and record `MATCH`, `BODY_EXTRA`, `INDEX_EXTRA`, or `DIVERGENT`. This is QA only; it never creates/merges a party or overwrites role.

**FR-BBL-001 — Parcel inventory versus affected set.** `document.parcel_inventory` records every body, cover, and registration candidate with source and discrepancy. `event.parcels` contains only exact BBL/scope pairs affected by that event's clause/assertion. An explicit operative subset controls a broader cover. Indexed parcels may complete the set only when the clause expressly applies to the whole indexed/recorded premises. Addresses, neighbours, referenced parcels, and the document union never default into an event.

**FR-BBL-002 — Canonical identity.** Use a quoted ten-digit BBL or D-3. Preserve raw borough/block/lot and support. Never derive from address, street, metes and bounds, adjacency, slate-inferred borough, or external map. If property-linked but no BBL is supportable, retain the event, use `UNKNOWN/UNSUPPORTED_BBL`, add it to `exceptions.unplaced_parcel`, and make chronology validation non-PASS.

**FR-BBL-003 — Role and scope.** Each affected pair has sorted roles from `SUBJECT`, `GRANTING`, `RECEIVING`, `BURDENED`, `BENEFITED`, `SERVIENT`, `DOMINANT`, `COLLATERAL_LOCATION`, `DECLARED_COMPONENT`, `UNIT_APPURTENANT`; and scope from `ENTIRE_BBL`, `PARTIAL_BBL`, `UNIT`, `AIR_SPACE`, `SUBTERRANEAN_SPACE`, `FACADE`, `EASEMENT_AREA`, `DESCRIBED_PREMISES`, or `UNKNOWN`. Roles remain parcel attributes. A partial/unit/vertical/facade/easement description never becomes whole lot during fan. Same BBL with distinct scopes stays distinct. Extract parcel share only when stated.

**FR-BBL-004 — Missing extent.** A bare Richmond registration BBL identifies a lot but does not prove whole/partial extent. Emit scope `UNKNOWN/NOT_STATED`, never `ENTIRE_BBL` or `NOT_APPLICABLE`.

## 7. Quantities, terms, and continuity

**FR-QTY-001 — Quantity registry.** Store each measurement once with `quantity_id`, `kind`, `label_raw`, raw/normalized value, currency/unit, scope, target event/object/parcel/party ids, allocation status/records, and support. Assign ids by first supporting section, then this kind order:

`NOMINAL_CONSIDERATION`, `FULL_SALE_PRICE`, `ASSESSED_VALUE`, `APPRAISED_VALUE`, `FAIR_MARKET_VALUE`, `ORIGINAL_PRINCIPAL`, `CURRENT_BALANCE`, `PAYOFF`, `MAXIMUM_LIEN`, `CREDIT_LIMIT`, `NEW_MONEY`, `RENT`, `PROJECT_COST`, `TRANSFER_TAX`, `MORTGAGE_TAX`, `RECORDING_FEE`, `FILING_FEE`, `OTHER_NAMED_TAX_FEE`, `PERCENT_INTEREST`, `COMMON_INTEREST`, `AREA`, `DIMENSION`, `DURATION`, `RATE`, `OTHER_NAMED`. Assign `<document_id>-Q001`… after that ordering.

Type from the governing label/words, never document type. Different kinds coexist even at equal numbers. A referenced mortgage principal belongs to the reference, not the present assignment/satisfaction quantity.

**FR-QTY-002 — Normalization and zero.** Use D-2. Money is exact decimal and supported currency; a visible `$` supports USD. Percent is the stated percentage, rational fractions are reduced, dimensions retain stated units. An affirmatively completed zero is numeric zero. Blank is UNKNOWN; `no new indebtedness` is ASSERTED_NONE for new money, not zero.

**FR-QTY-003 — Scope/allocation.** Quantity scope is `EVENT`, `STATE_OBJECT`, `PARCEL`, `PARTY_SHARE`, `INSTRUMENT_TOTAL`, or `MULTI_EVENT_TOTAL`. Use `EXPLICIT` for stated components, `DERIVED` only through D-6, `NOT_DERIVABLE` for an unallocated total over several targets, and `NOT_APPLICABLE` for one target/nonallocative measurement. Fan references one total; it never duplicates or divides it.

**FR-QTY-004 — Conflict/deduplication.** Coalesce exact repeated displays only when kind, value, status, scope, target, and referred object match; retain all evidence. Different kinds/scopes remain separate. Same-kind/scope controlling differences are a field conflict; never sum, average, or choose by plausibility.

**FR-QTY-005 — Registration amount.** Retain raw schema `registration.amount` in `document.index_reported_amount` with semantic kind `UNKNOWN` unless a citable image label or operative text identifies what it measures. `INDEX_REPORTED_AMOUNT` is an adapter field, not a quantity-registry kind. Instrument classification never supplies meaning. While untyped it emits no Value, Cost, or Capital event and resolves no body/form field.

**FR-TERM-001 — Module paths only.** A term record has module-controlled `path`, value type, raw/normalized value, party/object/scope ids when stated, and support. Emit only paths whose module `required_when` test succeeds. If required and unstated, emit UNKNOWN. Do not serialize every possible token. Promote dates listed by FR-DATE-005 to boundary records rather than burying them in prose.

**FR-REF-001 — Raw external pointers.** Assign `<document_id>-X001`… by supporting section then registration path. Store id, `relation_raw`, `locator_raw`, D-9 components, source/evidence, `resolution_status: UNRESOLVED_BY_EXTRACTION`, and current event ids. Capture every adapter `POINTER_SOURCE` and body/image reference verbatim. Never supply target document/event id, resolve it, or import unseen contents/state.

## 8. Nulls, findings, and failure classes

**FR-NULL-001 — UNKNOWN.** Use when an applicable required field has no supported single value. Reason is `NOT_STATED`, `ILLEGIBLE`, `CONFLICT`, `UNALLOCATABLE`, `UNSUPPORTED_BBL`, or `UNSUPPORTED_DATE`. It is field-local unless a placement key is affected.

**FR-NULL-002 — NOT_APPLICABLE.** Use only when a module's conditional schema asks a field and supported inputs prove that branch structurally cannot apply. Omitted out-of-schema paths are absent, not NOT_APPLICABLE.

**FR-NULL-003 — ASSERTED_NONE.** Use only for express scoped negation and cite it. When the negation is parcel state content, FR-PKG-003 requires an observation event.

**FR-NULL-004 — NO_CHANGE.** Use only as an express MODIFY/CORRECT field operation preserving a named path/all other terms. It carries a known earlier value only within this document's fold; unseen prior state remains UNKNOWN. It is never a blank matrix cell.

**FR-AMB-001 — Separate outcomes.** Keep distinct: document ambiguity/conflict; image illegibility; genuinely unstated value; unplaced function/BBL/transaction time; framework/schema gap; input integrity failure; model validation failure; and escalation. Never relabel one as another.

**FR-AMB-002 — Document finding.** A final document flag requires two or more evidence-supported readings of the same controlling field after scope/kind/rank/correction tests and, where eligible, both reader tiers. Store affected paths, candidates, and evidence. Framework silence, difficulty, commercial oddity, lower-rank discrepancy, or missing text is not a document flag.

**FR-AMB-003 — Placement.** A readable competing function, BBL, or transaction applicable-time reading is an escalation candidate. A genuinely absent BBL/time remains a cited exception and makes state-chronology status non-PASS. A framework gap blocks the bundle version; it is neither escalation nor a document flag. Unknown observation valid time is correctly routed to its physical unplaced-observation lane and does not by itself fail extraction QC.

**FR-AMB-004 — Closed final finding codes.** `document_flags` uses only `AMBIGUOUS_GLYPH`, `AMBIGUOUS_GRAMMAR`, or `CONFLICTING_CONTROLLING_EVIDENCE`, each with candidates and proof. Final unreadability without two document readings is `exceptions.ILLEGIBLE_FINAL`; framework/input/model failures use their own exception classes. No free-text uncertainty flag is allowed.

## 9. Primary/heavy escalation contract

**FR-ESC-001 — Route, not output.** The primary first produces a complete provisional extraction and coverage ledger. Escalation is operational sidecar metadata and is stripped from final extraction/matrix. It means this reader may have failed where the heavier reader can resolve; a document flag means the evidence remains ambiguous.

**FR-ESC-002 — Closed triggers.** Escalate the document once if at least one record passes exactly one test:

1. `VISUAL_CANDIDATES`: after 900-dpi reread and D-1, at least two graphic transcriptions remain and change a semantic/placement/coverage output;
2. `RULE_BRANCH_CANDIDATES`: one cited passage contains discriminating words for two existing rule branches, attachment cannot be resolved, and both complete candidate outputs differ;
3. `MODEL_VALIDATION_FAILURE`: after one deterministic self-repair, readable supplied content remains omitted/mislinked and schema, coverage, required-field, or provenance QC fails;
4. `CONTEXT_LINK_FAILURE`: after required two-pass section/reference processing for an over-limit package, exact named cross-section links remain unresolved.

Do not escalate NOT_STATED, genuinely absent date/BBL, unallocatable total, clear same-rank document conflict, framework gap, missing/corrupt image, or `this is hard`.

**FR-ESC-003 — Immutable payload.** Carry document id; input hashes; adapter/framework/module ids, versions, and bundle hash; provisional extraction/ledger/validation/candidate diff; trigger; affected paths/sections/rules; all candidates/evidence; relevant pages and lossless crops (all pages for context/validation); and replaceable-path/section allowlist. Exclude slate, other documents, parcel history, resolved pointers, lookups, and unstated law.

**FR-ESC-004 — Heavy task.** Apply the identical frozen bundle to identical inputs and adjudicate each trigger as `RESOLVED`, `DOCUMENT_AMBIGUITY`, `INSUFFICIENT_EVIDENCE`, or `INVALID_TRIGGER`. Return replacements only inside the allowlist with quote/rule closure. Do not change rules, use outside information, resolve pointers, edit unrelated paths, or escalate again. An additional event is allowed only in a section already unresolved/validation-failed and must replace its ledger disposition.

**FR-ESC-005 — Merge-back.** Validate scope/schema/provenance/coverage/QC; merge allowed replacements; recompute registries, ids, links, and serialization—never patch a matrix. Ambiguity/insufficient evidence becomes its final null/candidates/finding. Invalid trigger retains the conforming primary answer and records false escalation. Retry malformed heavy serialization once without new reasoning; then queue operational failure. Strip routing metadata.

**FR-ESC-006 — Telemetry.** Track escalation rate by adapter, assigned stratum, module, page band, and trigger; heavy resolution/document-ambiguity/invalid-trigger/override/failure rates; and emitted-to-flagged, illegible, unplaced, framework-gap, validation-failure, and deferred-handwriting ratios. Torch cap is external configuration; never show the running quota to the reader or suppress a qualifying trigger.

## 10. Prohibitions, validation, and serialization

**FR-NOINF-001 — Absolute exclusions.** Never infer: prior/current ownership or lien/permit/lease status; party identity/role/share/relationship; BBL from address/geometry; parcel adjacency/benefit/burden; recording/preparation/reference date as applicable time; current balance from principal; payment from release or release from payment; standard rate/maturity/priority/remedy; whole-lot scope from partial/unit; contents of an external pointer; semantic kind from registration type; or law/statute/regulation/contract text not included.

**FR-NOINF-002 — Tax route.** Never derive consideration, price, principal, payoff, taxable amount, or value from tax/fee using an unstated rate, and never derive tax/fee from another amount using an unstated rate. Numerical consistency—even when the computed number is true—is not an admission rule. Another intra-document value may be derived only by a separately admitted D-rule and its own inputs.

**FR-QC-001 — Input coverage closure.** Every supplied image/section passes FR-COV-003; package sequence is intact; page-count reports do not become inventory; every populated registration path has one FR-REC-012 disposition and no `UNMAPPED` path remains.

**FR-QC-002 — Provenance closure.** Recursively walk every semantic leaf and sentinel. Each ends in a proving quote or loaded rule with supported inputs. Run FR-EV-002 semantic proof, not substring presence. Reject undeclared rules and derivation inputs added after the output.

**FR-QC-003 — Lane firewall.** Reject a single events array, mixed lane content, occurrence time in dated observations, any date-shaped unplaced-observation field, evidence-time state input, a notice delta, or an active conditional delta.

**FR-QC-004 — Title object safety.** Every Title event/key/object has supported `interest_kind`; fee and leasehold keys are distinct; no serialized/queryable holder list exists outside an interest-kind map. Failure invokes R-1 inversion and must be reported, not repaired silently.

**FR-QC-005 — Placement/coverage.** Every resolved transaction has one function, at least one exact affected BBL/scope pair, and applicable-time status. Missing load-bearing tags appear in counted exception queues and state chronology is non-PASS. Dated observations have function, BBL/scope, and asserted-valid interval. No event fans from parcel inventory alone.

**FR-QC-006 — Conservation and linkage.** Every event links coverage sections; every quantity/pointer/party id resolves once; no quantity is duplicated through fan; event groups arise from one act; ordering/boundary links resolve; no external pointer has a resolved target.

**FR-QC-007 — Module/schema closure.** Every state/assertion/term path is defined by a loaded module with matching function, lane, mode, value type, required-when, and merge behavior. Unknown required paths are explicit; out-of-schema paths are absent. A module never fires from registration name alone.

**FR-QC-008 — Trigger-frequency audit.** Each version reports every conditional rule/module trigger's numerator/denominator. Use the 609,811-row stratified slate only for registry-expressible sample counts, never corpus proportions; cross-tab nominations by registry, literal label, and recorded-year band. Use an assigned sampled frame for content triggers. Zero/always firing signals vacuity/overcapture; plausible frequency does not prove the boundary.

**FR-QC-009 — Outcome/ratio.** `validation.overall` is `PASS`, `EXCEPTION`, or `FAIL`. `PASS` requires schema/provenance/coverage closure and no framework/integrity/model failure; correct conditional and unknown-valid-time observation lanes may coexist. A missing transaction placement key or surviving document ambiguity is `EXCEPTION`. Framework contradiction, uncovered section, invalid source/derivation, or integrity failure is `FAIL`. Counts report all FR-COV-003 and FR-ESC-006 denominators.

**FR-QC-010 — Frozen runs.** Fresh contexts with answers withheld re-run TC-001 for D-1/R-4/page inventory, TC-002 for adapter/date/pointer closure, L1/L2 for Title estate separation, and O1/O2/O3 for the two clocks and structural unplacement. Any failure blocks the version.

**FR-QC-011 — Referent-shift finder.** Per `(adapter,literal type,date path)` with `n≥200` parseable rows, bin nonnegative gap to `recorded` in fixed 183-day bins. Bins with `≥ceil(.01n)` rows are high; adjacent highs form modes. Emit `REFERENT_SHIFT_CANDIDATE` when a later mode totals `≥ceil(.05n)` and a separating bin has `≤floor(.005n)`. Report bins and negative/unparseable counts. Otherwise `NOT_DETECTED`, never `CLEAN`; diffuse shifts can pass.

**FR-SER-001 — Canonical JSON.** UTF-8 without BOM, LF endings, two-space indentation, one terminal LF. Use FR-REC-001 key order. Sort registries by ids; lane records by event id; unordered ids/roles/flags/candidates lexically after deduplication; preserve evidence/field-op/document sequence only where declared. Never emit JSON null, blank strings, `TBD`, or free-text `N/A/NONE`. Exact decimals are quoted base-10 without grouping/exponent; fractions are reduced strings; dates are ISO; sentinels uppercase.

**FR-SER-002 — Bundle identity.** `bundle_manifest` is loader-supplied, non-semantic run metadata: version/hash of core, selected adapter, every selected module, and the full concatenated extraction bundle. An event copies the bundle hash. The extractor cannot cite hashes as document evidence.

**FR-SER-003 — Follow fixed rules.** When a rule appears wrong, emit its result and record the objection outside committed extraction. Never silently repair the framework. A failed validation remains deliverable with named failures; do not invent a value to obtain PASS.

<!-- BUILD:MODULE ESTATE_IDENTITY -->
## Module ESTATE_IDENTITY

Load on the exact trigger in FR-LOAD-003. This module owns Identity and Title paths for parcel identity and possessory estates.

**FR-EST-001 — Identity acts.** Routine premises recitals never fill Identity. Emit Identity only for express creation, merger, apportionment, subdivision, renumbering, supersession, correction, or present certification of a formal parcel/unit/zoning-lot composition or designation. An operative subset or partial premises remains scope unless the words assert identity itself.

**FR-EST-002 — Estate acts.** Fee/condominium/common/life/leasehold/subleasehold estate creation, conveyance, assignment, surrender, correction, and termination fill Title. Choose supported `interest_kind`: `FEE`, `CONDOMINIUM_UNIT`, `COMMON_INTEREST`, `LIFE_ESTATE`, `REMAINDER`, `LEASEHOLD`, `SUBLEASEHOLD`, `UNDIVIDED_SHARE`, or `OTHER_NAMED` plus raw estate words. Never default to FEE from a deed label.

**FR-EST-003 — Lease branching.** `leases/demises` creating possessory premises → Title CREATE; transfer of the continuing tenant interest → Title TRANSFER; surrender/whole termination → Title TERMINATE; amendment → Title MODIFY. A memorandum stating a lease was made elsewhere → Title NOTICE/ASSERT. An assignment offered as collateral or an assignment of rents/proceeds triggers SECURED_FINANCE instead; an independently worded covenant burdening the fee also triggers LAND_RIGHTS.

**FR-EST-004 — Concurrent objects.** Put a leasehold without its own indexed BBL on the affected fee BBL but under a `TITLE:LEASEHOLD:` key. A separately identified sublease, fee, common interest, or unit uses another key. Title holder extraction is invalid without interest kind.

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `identity.designations` | Identity; transaction/observation | set of typed raw/canonical designations | formal designation is asserted or changed | set union; correction targets one member |
| `identity.existence_status` | Identity; create/modify/correct/assert | `CREATED`, `MERGED`, `APPORTIONED`, `RENUMBERED`, `SUPERSEDED`, `ASSERTED_EXISTS`, UNKNOWN | the act states one status branch | scalar conflict on unordered differences |
| `identity.composition` | Identity; create/modify/assert | set of BBL/unit ids | composition is the act/assertion | exact affected set; never inventory union |
| `identity.former_designation`, `identity.new_designation` | Identity; modify/correct | typed designation | former/new grammar appears | paired scalar |
| `title.estate_label` | Title; all | raw named estate | every Title event | immutable after create except express correction |
| `title.holders` | Title; transaction | interest ledger `{party_id, share}` | create/transfer/terminate changes a holder | ledger operation; no estate-blind aggregate |
| `title.reservations`, `title.exceptions` | Title; transaction | supported term sets | reservation/exception is operative | set union or targeted correction/removal |
| `title.appurtenant_interests` | Title; transaction | keyed interest records | common/exclusive-use/appurtenant interest changes | object-keyed map |
| `title.lease.premises` | Title LEASEHOLD/SUBLEASEHOLD | parcel/scope set | lease estate is created/asserted | replace only on express amendment/correction |
| `title.possession_statement` | Title; observation/transaction assert | typed raw statement | present possession is expressly stated | assertion layer unless legally established |

Required term paths are emitted only on their phrases: raw/set `title.tenancy_raw`, `title.covenant_raw`, `title.lease.permitted_use`; id sets `title.consideration_quantity_ids`, `title.subject_to_pointer_ids`, `title.lease.rent_quantity_ids`; quantity id `title.lease.security_deposit`; and structured trigger/consequence/party/scope terms `title.lease.assignment_consent`, `title.lease.subletting_consent`, `title.lease.renewal_option`, `title.lease.purchase_option`, `title.lease.termination_option`, `title.lease.default_remedy`, `title.assumption`. Missing rent is UNKNOWN only when the lease text says rent exists but omits it; otherwise the path is absent.

Promote supported lease commencement and expiration, option windows, renewal deadlines, and termination dates as boundaries. `SELF_EXECUTING` is allowed only for exact automatic-effect words and no unresolved condition; renewal, holdover, notice, or exercise language makes the boundary informational/conditional.

<!-- BUILD:MODULE SECURED_FINANCE -->
## Module SECURED_FINANCE

**FR-FIN-001 — Independent layer test.** For each clause, identify whether it acts on collateral security, monetary obligation, or both. Emit Encumbrance and Capital separately only for stated effects. One shared principal may be referenced by both without duplication.

**FR-FIN-002 — Lifecycle.** Creation of security → Encumbrance CREATE; creation of debt/facility → Capital CREATE. Assignment transfers only the layer expressly assigned. Priority/subordination without holder transfer → Encumbrance MODIFY. Partial collateral/debt release → scoped MODIFY. Whole lien/filing release → Encumbrance TERMINATE. Capital TERMINATE requires express payment, cancellation, forgiveness, discharge, or termination of the obligation. UCC termination never proves debt payment.

**FR-FIN-003 — Notice filings.** A UCC form, memorandum, or notice whose underlying security agreement is not supplied creates a NOTICE/ASSERT of Encumbrance claim/filing, not a transaction CREATE. Capture initial file number and external pointers. The recording timestamp supplies no applicable time.

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `encumbrance.security_kind` | Encumbrance; all | `MORTGAGE_LIEN`, `UCC_FIXTURE`, `ASSIGNMENT_OF_RENTS`, `OTHER_SECURITY` | security path fires | immutable named kind |
| `encumbrance.holders` | Encumbrance; transaction | interest ledger | holder is granted/transferred/released | ledger operation |
| `encumbrance.collateral_scope` | Encumbrance; transaction/notice | typed parcel/property description | collateral is identified | scoped set; partial release targets member |
| `encumbrance.priority` | Encumbrance; transaction/observation | raw relation plus object refs | priority/subordination stated | relation set; conflict on incompatible unordered relation |
| `encumbrance.rents_proceeds` | Encumbrance; transaction/notice | typed security scope | rents/proceeds are collateral | set union/targeted release |
| `capital.obligation_kind` | Capital; transaction/observation | `MORTGAGE_DEBT`, `NOTE_DEBT`, `CREDIT_FACILITY`, `FUNDING_COMMITMENT`, `EQUITY_COMMITMENT`, `OTHER_NAMED` | obligation path fires | immutable except correction |
| `capital.obligors`, `capital.obligees` | Capital; transaction | party-interest ledgers | parties owe/are owed or transfer obligation | ledger operation |
| `capital.original_principal`, `capital.current_balance`, `capital.payoff`, `capital.maximum_lien`, `capital.credit_limit`, `capital.new_money` | Capital; transaction/observation | quantity id | governing words type the amount | distinct scalar paths; never copy among them |
| `capital.rate`, `capital.rate_type`, `capital.rate_index`, `capital.rate_margin` | Capital; transaction | exact quantity/enum/raw term | clause states that term | targeted replacement; missing referenced note term UNKNOWN |
| `capital.payment`, `capital.advance_right`, `capital.readvance_right`, `capital.prepayment`, `capital.default`, `capital.guaranty` | Capital; transaction | typed term | exact obligation phrase occurs | object/path merge |

Promote maturity, rate-reset, payment-start, advance-window, and commitment-expiration dates. Maturity and filing lapse are always informational unless exact automatic state-effect words and a specific path rule say otherwise; this module supplies no automatic debt/lien termination rule.

A statement that a mortgage `has not been assigned` is an Encumbrance observation of assignment-history absence with its exact scope. A blank prior-assignment field says nothing. An original principal recited only to identify the referenced mortgage stays on the external-reference record unless the present clause independently asserts a Capital measurement.

<!-- BUILD:MODULE LAND_RIGHTS -->
## Module LAND_RIGHTS

**FR-LAND-001 — Function split.** For a private easement/covenant/restriction, fill Encumbrance. Add Envelope for a legal constraint on physical mass, placement, facade, or form; no number is required. Add Entitlement for a granted/transferred/reserved nonpossessory development capacity or land-use privilege. Do not add Title unless possessory-estate words separately trigger ESTATE_IDENTITY.

**FR-LAND-002 — Government/private boundary.** Naming an application, agency, regulation, or desired approval is a term/reference. A government grant of land-use capacity may fill Entitlement. Permit requires the PUBLIC_PHYSICAL government work/operation test. Private residential/commercial-use limits are Encumbrance, not Occupancy.

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `entitlement.right_kind` | Entitlement; all | `DEVELOPMENT_RIGHT`, `AIR_RIGHT`, `SUBTERRANEAN_RIGHT`, `LAND_USE_AUTHORIZATION`, `LICENSE`, `OPTION`, `OTHER_NAMED` | nonpossessory right is acted/asserted | immutable named kind |
| `entitlement.holders` | Entitlement; transaction | interest ledger | grant/transfer/reservation names holder | ledger operation |
| `entitlement.capacity` | Entitlement; transaction/observation | quantity/set | capacity is quantified | scoped scalar/set |
| `entitlement.authority_or_source` | Entitlement; transaction/observation | party/id/raw reference | source is expressly named | set of supported records |
| `envelope.constraint_kind` | Envelope; transaction/observation | `HEIGHT`, `SETBACK`, `FLOOR_AREA`, `LOT_COVERAGE`, `BULK`, `FACADE`, `STRUCTURAL`, `BUILDABLE_VOLUME`, `SUBTERRANEAN_VOLUME`, `OTHER_NAMED` | physical-form path fires | keyed constraint object |
| `envelope.limit_or_allocation`, `envelope.geometry`, `envelope.permitted_work`, `envelope.prohibited_work`, `envelope.preservation_standard` | Envelope; transaction/observation | quantity/geometry/raw term | exact constraint states it | per-constraint path merge |
| `encumbrance.land_kind` | Encumbrance; all | `EASEMENT`, `COVENANT`, `DECLARATION_BURDEN`, `OPTION`, `ROFR`, `LIS_PENDENS`, `OTHER_NAMED` | land burden/benefit path fires | immutable named kind |
| `encumbrance.beneficiaries`, `encumbrance.burdened_parties` | Encumbrance; transaction | party-interest ledgers | parties expressly hold/bear it | ledger operation |
| `encumbrance.physical_scope`, `encumbrance.legal_scope`, `encumbrance.access`, `encumbrance.inspection`, `encumbrance.construction_duty`, `encumbrance.maintenance_duty`, `encumbrance.cost_responsibility`, `encumbrance.runs_with_land` | Encumbrance; transaction/observation | scoped typed terms | corresponding words occur | path-specific set/scalar |

Parcel role grammar is mandatory: development capacity uses GRANTING/RECEIVING; easement uses SERVIENT/DOMINANT when stated; covenant uses BURDENED/BENEFITED. Never derive those relations from adjacency or deed order. Promote duration/termination/consent/option/casualty/condemnation dates as boundaries or conditions; no common-law permanence is assumed.

<!-- BUILD:MODULE PUBLIC_PHYSICAL -->
## Module PUBLIC_PHYSICAL

**FR-PHY-001 — Permit acts.** A Permit event requires a named government authority plus a stated application, receipt, issuance, approval, amendment, renewal, suspension, revocation, or expiry of work/regulated-operation authorization. Private/title-company/engineer certification does not qualify. An application can be a transaction with status `APPLIED`; a document merely mentioning one is reference-only.

**FR-PHY-002 — Observation basis.** As Built and Occupancy content is observational unless a government act itself authorizes occupancy. `AUTHORIZED` and `ACTUAL` are distinct Occupancy bases. A cover property type or registry `use` alone cannot trigger an observation. An executed transfer/compliance form triggers only fields it affirmatively states.

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `permit.kind`, `permit.identifier`, `permit.authority`, `permit.work_scope`, `permit.status`, `permit.conditions` | Permit; transaction/notice | enum/id/party/raw/set | government act fills corresponding field | keyed permit object; targeted status change |
| `as_built.item_kind`, `as_built.geometry`, `as_built.floor_area`, `as_built.unit_count`, `as_built.completion`, `as_built.condition`, `as_built.location`, `as_built.operational_status` | As Built; observation | typed scalar/set/quantity | present physical statement fills it | evidence assertion by valid interval |
| `occupancy.basis` | Occupancy; transaction/observation | `AUTHORIZED` or `ACTUAL` | every Occupancy event | immutable per object/assertion |
| `occupancy.use`, `occupancy.capacity`, `occupancy.certificate_id`, `occupancy.subject` | Occupancy; transaction/observation | raw/set/quantity/id | exact field is stated | keyed state/assertion path |

Inspection, survey, valuation-like physical as-of, test, issue, effective, expiration, and completion dates follow FR-DATE rules. Signature/certification date is evidence time only unless the form explicitly states the condition is true on that date. Permit expiration may be `SELF_EXECUTING` only on exact automatic-expiry words with no unresolved renewal/condition.

An executed assertion that equipment/use/occupancy is absent produces a scoped observation with ASSERTED_NONE. A blank checkbox never does. A zero-event supporting form is allowed when every completed field is administrative/party-only and the ledger proves no path was filled.

<!-- BUILD:MODULE ECONOMICS -->
## Module ECONOMICS

| admitted path | function; lanes/modes | value type | required when | merge |
|---|---|---|---|---|
| `value.kind` | Value; observation | `NOMINAL_CONSIDERATION`, `FULL_SALE_PRICE`, `ASSESSED_VALUE`, `APPRAISED_VALUE`, `FAIR_MARKET_VALUE`, `OTHER_NAMED` | valuation path fires | immutable measurement kind |
| `value.amount`, `value.subject_interest`, `value.basis`, `value.completion_basis` | Value; observation | quantity id/object/raw enum | governing words state it | one observation per kind/scope/time |
| `cost.kind` | Cost; transaction/observation | `PROJECT_EXPENDITURE`, `PROJECT_BUDGET`, `CONTRACT_COMMITMENT`, `TRANSACTION_TAX`, `RECORDING_FEE`, `OTHER_NAMED` | Cost path fires | immutable measurement/obligation kind |
| `cost.amount`, `cost.status`, `cost.subject`, `cost.payer`, `cost.payee` | Cost; transaction/observation | quantity id/enum/object/party | exact words state it | one path per kind/scope/time |

**FR-ECO-001 — Value separation.** Nominal deed consideration, full sale price, assessed value, appraised value, and fair-market value are separate Value observations/measurements. A nominal amount never overwrites sale price. Financing amounts remain Capital; project amounts remain Cost. The source date becomes asserted-valid time only when its words attach the measurement to that date.

**FR-ECO-002 — Tax/fee recognition.** A citable cover, executed return/receipt/form, or operative clause labeling NYC/NYS real-property transfer tax, mortgage tax, recording fee, filing fee, or another named tax/fee creates its exact quantity kind and a Cost `ASSERT` observation. It reports a measurement; it does not prove a payment obligation or payment merely by appearing.

Set status solely from visible words: `PAID`, `CHARGED`, `DUE`, `ASSESSED`, `EXEMPT`, or `REPORTED_AMOUNT`. A bare filled field is `REPORTED_AMOUNT`; affirmative zero is numeric zero; blank is UNKNOWN. Payer/payee require express labels. Applicable valid time is an explicit payment/charge/due/assessment/transaction-as-of date attached to that field; otherwise route the observation to `observations_unplaced`. Recording time is excluded.

**FR-ECO-003 — Act versus filing attachment.** A charge stated as levied on a transaction/act links to that act's event group and affected parcel set. A charge stated as levied on filing/recording stays document-scope and links to no act event group. Its own Cost observation remains; without a supportable BBL it is counted as unplaced rather than attached by address. One unallocated multi-event/multi-BBL amount remains `INSTRUMENT_TOTAL`/`NOT_DERIVABLE`; each projection may reference it but none receives a parcel amount.

Executed return/receipt controls its named tax/fee field; cover/index controls the register-reported field. Preserve discrepancies and never use either to resolve consideration/principal/value. Exact repeats coalesce; different kinds coexist; controlling same-kind/scope conflicts remain candidates. Fold Cost observations as evidence, never as project-cost lifecycle.

**FR-ECO-004 — Cost character.** A clause presently committing a party to project expenditure is a Cost transaction; a form/receipt/certification reporting budgeted, incurred, charged, paid, assessed, or exempt amount is a Cost observation. Exact status words control. A displayed amount alone never decides between obligation and measurement.

<!-- BUILD:MODULE NOTICE_AUTHORITY -->
## Module NOTICE_AUTHORITY

**FR-NOT-001 — Notice.** A memorandum, notice, affidavit, UCC form, or register remark reporting an interest/act made elsewhere goes in `notices` with mode ASSERT and the target function/object type supported by its words. It may carry raw pointers and stated claim attributes; it has no lifecycle delta and imports no target state. If the same document also performs a present act, load that act's module and emit a separate transaction.

**FR-NOT-002 — Authority-only content.** A power of attorney, corporate resolution, trustee/officer affidavit, acknowledgement, or capacity recital supplies party authority/capacity and evidence only unless an independent clause fills one of the eleven functions. A complete zero-event result names `NO_FUNCTION_PATH_FILLED` and must pass coverage closure; never assume zero events from the registration label.

**FR-NOT-003 — Pointer sources.** Capture visible cross-reference labels/locators and adapter-authorized top-level remarks through FR-REF-001. `amends`, `substitutes`, `assigns`, `satisfies`, `corrects`, `derives from`, or another exact relation is stored raw; do not choose a relation merely from document type.

<!-- BUILD:MODULE GENERIC_GAP -->
## Module GENERIC_GAP

**FR-GAP-001 — No improvisation.** This module defines no state, assertion, or term path. For each apparent matrix-relevant clause not covered by a loaded module, record section, verb/object, candidate function(s), required output path, and `FRAMEWORK_GAP`. Validation is FAIL for this bundle version. Do not invent a subtype/path or suppress the clause to obtain a zero-event document.

<!-- BUILD:ADAPTER ACRIS_DIGITAL -->
## Adapter ACRIS_DIGITAL

REGISTRATION_PATHS_JSON = ["amount","at","borough","collateral","crfn","doc_date","expiration","pages","parcels","parcels[].address","parcels[].air_rights","parcels[].bbl","parcels[].easement","parcels[].partial","parcels[].subterranean","parcels[].unit","parcels[].use","parties","parties[].address","parties[].address2","parties[].city","parties[].country","parties[].name","parties[].panel","parties[].state","parties[].zip","pct","recorded","references","references[].borough","references[].crfn","references[].doc_id","references[].file_nbr","remarks","type"]

**AD-ACRIS-001 — Shape.** Apply FR-REC-012 because ACRIS fields are type-conditional: inventory every present path and normalize only declared ones. Declared paths include raw `type`, `doc_date`, `crfn`, `recorded`, `borough`, `amount`, panel-indexed parties, parcels carrying `bbl`/`partial`/`use`/`address`/`unit`, `expiration`, `collateral`, and `references[]`. `type` nominates only. Panels never determine role. `doc_date` follows FR-DATE-008; `recorded` is recording fact. `crfn` and any explicitly current file number identify the current recording. `expiration` and `collateral` are index-reported facts with referent/scope UNKNOWN unless allowed evidence identifies them; they trigger no event alone. `amount` follows FR-QTY-005; `pages` is a count report; `at` is nonsemantic.

Image-cover indexing fields outrank registration for the same index fact. On every row, probe each `references[]` item independently for `doc_id`, `crfn`, `file_nbr`, and `borough`; preserve every found component, and treat any/all absent forms as normal. ACRIS `CROSS REFERENCE DATA` and locator-like `remarks` are also pointer sources through D-9. A present `pct` creates a mandatory image-search candidate for party/estate share and nominates ESTATE_IDENTITY, but remains index-reported with referent UNKNOWN until exact image proof. Party addresses are index metadata. Parcel `air_rights`/`subterranean`/`easement` flags nominate LAND_RIGHTS review but supply no event, role, direction, or scope without image proof. Do not interpret normalized type as cover/body wording.

<!-- BUILD:ADAPTER RICHMOND -->
## Adapter RICHMOND

REGISTRATION_PATHS_JSON = ["amount","at","book","doc_type","image_state","instrument","page","parcels","parcels[].bbl","parties","parties[].column","parties[].company","parties[].name","parties[].person","parties[].role","recorded","status"]

**AD-RICH-001 — Shape.** Normalize `doc_type`, `recorded`, parties and any nonblank indexed `role`, bare parcel BBLs, `book`, `page`, and `instrument`. `amount` follows FR-QTY-005. Registration has no `pages` or `doc_date`; a visible County Clerk cover Document Date is image evidence only. Indexed roles remain `indexed_role`; body grammar controls operative role. An empty `parties` array is `NO_INDEX_PARTIES`, never ASSERTED_NONE/completeness—extract every party from images. `column` and `person`/`company` are index metadata, not role/entity proof. Bare BBL extent is UNKNOWN under FR-BBL-004. Missing unit/address/use is missing schema data, not NOT_APPLICABLE. `image_state`, `status`, and `at` are nonsemantic.

Book/page/instrument identifies the current recording unless an exact field/remark/body label presents it as a cross-reference; only the latter enters the external-reference registry. Never use a slate-derived borough.

**AD-RICH-002 — Per-label historical nomination.** Preserve raw `doc_type` and map only the proven label pairs below; accept both columns in every year because each label has its own history and no registry-wide cutover is admitted:

| act family | legacy label | later label | nominated module |
|---|---|---|---|
| conveyance | `DEED` | `DEED` | ESTATE_IDENTITY |
| mortgage satisfaction | `SAT` | `SATISFACTION OF MORTGAGE` | SECURED_FINANCE |
| mortgage assignment | `A/MTG` | `ASSIGNMENT OF MORTGAGE` | SECURED_FINANCE |
| mortgage release candidate | `REL` | `RELEASE OF MORTGAGE` | SECURED_FINANCE |

Other literal labels nominate only their visible act family (`MORTGAGE`, `LEASE`, `A/LEASE`, `EASEMENT`, `AFFIDAVIT`, `NOTICE`). Unchanged `MORTGAGE` remains one label across eras. Broad `AGREEMENTS`/`ORDER` nominates no module; core page discovery decides. `REL` remains a candidate, not proof that the release concerns a mortgage. Pre-1960 `DEED` remains valid. Unknown labels never produce zero-event results by themselves.

<!-- BUILD:ADAPTER FILM_FT -->
## Adapter FILM_FT

REGISTRATION_PATHS_JSON = ["amount","at","borough","doc_date","file_nbr","map_seq","pages","parcels","parcels[].address","parcels[].bbl","parcels[].partial","parcels[].remarks","parcels[].use","parties","parties[].address","parties[].city","parties[].country","parties[].name","parties[].panel","parties[].state","parties[].zip","recorded","reel_page","references","references[].doc_id","remarks","rptt","type"]

**AD-FT-001 — Shape.** Normalize declared `type`, `recorded`, `borough`, `map_seq`, `reel_page`, parties, and parcel index fields. Optional `doc_date` follows FR-DATE-008; `amount` follows FR-QTY-005; `pages` is a count report. `rptt`, party addresses, and parcel remarks are index reports with semantic referent UNKNOWN unless image proof identifies them. `reel_page` and an explicitly current `file_nbr` identify the current recording. Top-level `remarks`, `references[].doc_id`, and locator-like parcel remarks are raw unresolved pointer sources through D-9. No cover is assumed. Parcel `use: PRE-ACRIS` is a source marker, never property use/Occupancy. `at` is nonsemantic.

<!-- BUILD:ADAPTER FILM_BK -->
## Adapter FILM_BK

REGISTRATION_PATHS_JSON = ["amount","at","borough","doc_date","map_seq","pages","parcels","parcels[].bbl","parcels[].partial","parcels[].use","parties","parties[].name","parties[].panel","recorded","reel_page","remarks","type"]

**AD-BK-001 — Shape.** Apply AD-FT-001 for the paths declared here. `doc_date` follows FR-DATE-008 and never automatically supplies applicable time. Normalize current book/reel/map identifiers from raw fields. A remark such as `D BOOK/PAGES: 156/36` is a raw unresolved pointer only. No cover is assumed; `PRE-ACRIS` remains non-occupancy metadata.

<!-- BUILD:END -->
