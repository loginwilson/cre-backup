# NYC C.R.E.D. Extraction Framework

**Version:** 0.0 (skeleton — unpopulated)
**Status:** DRAFT — not yet valid for extraction
**Companion:** `resolve-spec-R<n>.md` — ships with this document everywhere it goes

> This is the artifact the loop exists to produce. The extractors draft it
> independently in Phase 0a, merge it in 0b, and amend it every round thereafter.
> It must stand alone: a model with no memory of the conversation that produced it,
> holding only this document, the resolve-spec, and a source document, must be able
> to extract correctly.
>
> **Every rule is a decision procedure** and carries an **immutable rule ID**
> (`R-0001`, never reused, independent of section numbering — sections move, and a
> stale provenance citation pointing at a renumbered rule is worse than none). If
> two competent readers could apply a rule and produce different outputs, it is not
> finished. Delete "consider", "generally", "typically", "in most cases", and
> "use judgment" wherever they appear.
>
> **The reader is an open-weight model on Torch, not you** — likely near frontier
> capability, but that is an assumption to measure rather than build on. Capability
> does not make a loose framework safe: where rules are silent, a capable reader
> interpolates plausibly, and plausible interpolation is indistinguishable from
> observation everywhere downstream. Write rules that remove the occasion to
> interpolate. See §15 for read order and §16 for build architecture.
>
> **Builds.** *Core* + *type modules* are what production loads (§16.1). The
> *development build* is everything. The *extraction build* is Core + one module,
> with §13 stripped — §13 stores prior documents' agreed answers, and reading it
> would be a lawful route around the input restriction in protocol §5.

---

## §0 — Meta

### 0.1 Version
`<major>.<minor>` — minor on every accepted amendment set, major on a schema change or a §3.3 function-boundary change. A major bump triggers a full regression run and may put cases into SUPERSEDED.

### 0.2 Changelog

| Version | Round | Class | Sections touched | Summary |
|---|---|---|---|---|
| 1.0 | 000 | — | all | Initial charter |

### 0.3 Open questions register

Unresolved disagreements. Class 3 and above must be empty before exit.

| ID | Round | Class | Question | Conservative rule in force | Rounds open | Blocking exit? |
|---|---|---|---|---|---|---|

Class 3+ questions open more than 3 rounds go to the Principal for a binding ruling (protocol §8.1).

### 0.4 Scope

The instrument types, sources, and date ranges this version claims to cover.

**The Principal owns and freezes this enumeration before the loop starts.** The extractors may not narrow it — a self-editable scope makes the breadth exit criterion satisfiable by deletion.

**Extraction of anything outside declared scope is an ESCALATE, not a best effort.**

### 0.5 Rule coverage

Incremented at P8. Drives document selection — the least-tested rule wins ties.

| Rule ID | Section | Rounds exercised | Last exercised | Regression cases |
|---|---|---|---|---|

### 0.6 Yield series

The conservative-collapse detector. A ratio drifting toward flagging is a defect even when every individual choice was defensible.

| Round | Fields emitted | Fields flagged | Ratio | Cumulative ratio |
|---|---|---|---|---|

---

## §1 — Inputs

### 1.0 Access

**Choose the ID → read the registry row → open the PDF at the stored path.** Three steps, no variation.

Read the stored path; never re-derive it, never search, never fetch a URL. `DOCUMENT ACCESS.md` governs the mechanics — follow it exactly, trap list included.

### 1.0.1 A path is a locator, not evidence

Seeing the path is necessary and fine. Citing it is not.

`…\By Document\1917\03 Mar\28\RC_988537.pdf` states a date in its folders. `…\2003\01 Jan\06\2002122000001001.pdf` states one that disagrees with the date inside its own document ID. Neither is necessarily the event date. A value harvested from either is a value produced without reading the document — and the error is systematic, so both readers make it and the diff catches nothing.

> **Paths, folder names, filenames, URLs and pipeline metadata are never citable.**

Enforced by §11's provenance rule, not by new machinery: a citation must be a document quote, a citable registry field, or a rule ID, and a path is none of these.

### 1.0.2 Citable registry fields

Enumerate what **is** citable, not what is excluded — across 25 million rows an exclusion list admits every new pipeline column by default.

| Registry field | Citable | Notes |
|---|---|---|

### 1.0.3 Document modality
The corpus spans a century; the reader does not face one kind of file. `manifest.json` declares modality — native text layer, OCR'd scan, image-only — and §15 branches on it.

OCR error is a first-class ambiguity source with its own rules: garbled text is `UNKNOWN`, not absent, and a confidently misread numeral is more dangerous than an illegible one. An 1917 Richmond County instrument is a scan; do not write a read procedure that assumes selectable text.

### 1.1 Permitted inputs
Exactly three: the extraction packet, the extraction build of this framework (Core + the type module selected by read Pass 0), and the resolve-spec.

### 1.2 Recorded details vs. document
When the registry's structured details and the document body disagree, which governs, for which field classes, and how the conflict is recorded in the event.

*This will happen constantly. Decide it once, here, or it gets re-decided inconsistently forever.*

### 1.3 Unreadable or partial documents
Illegible scans, missing pages, truncated exhibits. Rule for what may still be extracted and what must be flagged.

---

## §2 — Event record schema

> **The schema lives here, in the framework, and nowhere else.** Protocol §5 permits extractors the framework and the resolve-spec; a schema in a third file is a file they are not allowed to read, and the cold model in exit criterion 5 would never receive it. Phase 0a's working draft is merged into this section and then deleted.
>
> **Frozen after Phase 0b.** Changes only under protocol §8. A schema change is a major version bump, triggers a full regression run, and puts every case that used the changed field into SUPERSEDED — expensive by design.

> **Classification is the floor, not the job.** Function and timestamp are what Resolve consumes, so they are mandatory — but a framework that treats tagging as the work will produce event tables that satisfy the matrix and starve every product built on it. The substance of this section is *packaging*.

### 2.1 Field definitions

| Field | Type | Required | Definition | Null semantics permitted |
|---|---|---|---|---|

### 2.2 Mode
What the event does to state: `CREATE` · `MODIFY` · `TRANSFER` · `TERMINATE` · `ASSERT` · `CORRECT`.

Orthogonal to function and not derivable from it. A Capital origination and a Capital satisfaction are the same function and opposite in effect; without mode, Resolve cannot fold them. Define the permitted modes per function and the procedure for determining mode from the document.

`CORRECT` deserves its own rule — instruments that correct a prior filing are common, and treating a correction as a new event duplicates history.

### 2.3 Parties and roles
Party record, role vocabulary, side assignment, per-party share. Multiple parties per side; events with no counterparty; parties whose role is stated in one place and modified in another.

Roles are not inferable from position on the page. Specify how role is determined, and what happens when it cannot be.

### 2.4 Direction
Whether an event is directional at all, and if so, from what to what. Enumerate which functions and modes permit direction. **Forcing direction onto a state assertion fabricates structure** — the schema must allow non-directional events natively rather than by convention.

### 2.5 Quantities and allocation
Measure, unit, basis. The document-level aggregate versus per-event allocation. Shares, percentages, fractional and equity interests.

The hard case: an instrument states one consideration, and several events legitimately draw on it. Specify when allocation is derivable, how, and — critically — the rule for when it is **not**. An invented allocation is a fabrication that looks like data and will never be caught downstream.

### 2.6 Terms
Rate, maturity, duration, expiry, conditions precedent, covenants, options, reversion and step triggers.

**First-class from v1.0.** The Debt Maturity Tracker, Refinance Pipeline, Construction Loan Monitor and Entitlement Tracker are all predictions seeded by terms captured at event time. Terms are the most droppable fields — dense clauses, variable form, and an extraction missing them still looks complete — and the least recoverable, since nothing downstream regenerates a maturity date that was never read. Re-extracting 25 million documents to add a field is not a correction; it is starting over.

Specify per instrument type which terms are expected, and make their absence an explicit `ASSERTED_NONE` or `UNKNOWN` rather than a silent omission.

### 2.7 Parcel roles
Not just which BBLs an event touches, but each parcel's role in it. An air rights transfer's granting and receiving lots are not interchangeable; a merger's constituent lots are not the resulting lot.

### 2.8 Identity and determinism
How an event is identified. Two extractions of the same document must produce comparable event identities without coordination — otherwise diffing is guesswork.

### 2.9 Ordering within a document
When several events come from one instrument and share a date, what determines their order.

### 2.10 Completeness contract
Per instrument type and mode, the fields that MUST be present for the event to be considered complete. An event missing a required field is a flagged defect, not a quietly shorter row.

This is what stops silent degradation: without it, an extractor under time pressure emits thinner and thinner events and every quality check still passes.

---

## §3 — Function taxonomy

### 3.1 The eleven
Fixed. Identity · Title · Entitlement · Envelope · Encumbrance · Capital · Permit · As Built · Occupancy · Cost · Value.

### 3.2 Positive definitions
For each function: what belongs in it, stated so that membership is testable.

### 3.3 Boundary decision procedures
The high-value section. For each adjacent pair, the procedure that separates them.

At minimum: Entitlement/Envelope · Encumbrance/Capital · Title/Encumbrance (leaseholds) · Permit/AsBuilt/Occupancy across a construction lifecycle · Cost/Value · Identity/Title (lot changes that also move ownership).

### 3.4 Multi-function fan-out
When one instrument legitimately produces events on several functions, and how those events reference one another.

*Worked reference case — an air rights transfer, which may simultaneously produce Entitlement (rights move), Envelope (granting lot's buildable form is constrained), Encumbrance (restrictive declaration recorded), and Value (consideration stated). Specify exactly which events are emitted, on which parcels, in which directions.*

---

## §4 — Event boundary rules

### 4.1 The atomic test
The procedure determining whether a passage yields one event or several.

### 4.2 Splitting
When one instrument becomes multiple events: multi-parcel, multi-party, multi-function, multi-date.

### 4.3 Non-splitting
When apparent multiplicity is a single event. *Prevents Class 2 inflation.*

### 4.4 Recitals and background
Documents recite history. Rule for when a recited prior event is emitted as an event and when it is context only.

*A high-risk area: recitals are how a filing "remembers" earlier events, and both over-emitting and under-emitting them corrupt chronology.*

---

## §5 — Temporal rules

### 5.1 Date precedence
Ordered procedure for deriving event date from available candidates: execution, effective, acknowledgment, recording, dates recited in body, dates in recorded details.

### 5.2 Basis recording
Every event date carries the basis on which it was derived. Enumerate the permitted bases.

### 5.3 Conflicting dates
Document and recorded details disagree; body and signature block disagree; multiple effective dates.

### 5.4 No defensible date
What to emit when no date can be derived. **This must not default to recording date silently** — a filing date masquerading as an event date is invisible downstream and poisons the chronology.

### 5.5 Ranges, conditions, and futures
Events with duration, effective-upon-condition, or stated future effect.

---

## §6 — Parties and direction

### 6.1 Party model
Identification, roles, multiplicity. Parties with no counterparty. Parties on both sides.

### 6.2 Directionality
Enumerate permitted directions. State which functions permit which. **Not every event is directional; do not force one.**

### 6.3 Non-transactional events
Events that are state assertions rather than exchanges — a certificate issuing, a status changing.

### 6.4 Party normalization
How entity names are canonicalized. Explicitly: how far normalization may go **without** using outside knowledge to resolve an identity.

---

## §7 — Value, share, and equity

### 7.1 Document-level vs. event-level value
An instrument may state one aggregate consideration while individual events carry shares, percentages, or partial interests. The allocation rule.

### 7.2 Non-allocable value
When aggregate value cannot be defensibly split. **Rule must forbid inventing an allocation.**

### 7.3 Shares, percentages, fractional interests
Representation and arithmetic. Whether shares must sum, and what to do when they don't.

### 7.4 Value types
Consideration, assessed, market, taxable, estimated cost, actual cost — kept distinct, never merged.

---

## §8 — BBL attribution

### 8.1 Parcel identification
Deriving affected BBLs from the document and recorded details.

### 8.2 Multi-parcel events
One event touching several parcels: replicate per parcel, or single event with a parcel set. Decide and justify — Reorganize depends on it.

### 8.3 Unidentifiable parcel
An event whose parcel cannot be determined cannot be reorganized. Rule for what happens to it.

### 8.4 Lot changes
Instruments that create, merge, apportion, or dissolve the parcel identity they reference. *Circular by nature — the event changes the thing it is attributed to. Handle explicitly.*

---

## §9 — Normalization

Canonical forms for dates, currency, area and dimension, percentages, names, addresses, document type codes. **Normalization may never add information.**

---

## §10 — Null semantics and ambiguity

### 10.1 The four nulls
`NO_CHANGE` — this event does not touch this function.
`UNKNOWN` — the document is silent or illegible.
`NOT_APPLICABLE` — the function cannot apply to this parcel or instrument type.
`ASSERTED_NONE` — the document affirmatively states there is none.

Never interchangeable. Each carries a distinct meaning in the matrix.

### 10.2 Ambiguity taxonomy and response

| Ambiguity type | Response | Notes |
|---|---|---|

Permitted responses: `EMIT_FLAGGED` (with competing readings and confidence) · `EMIT_NONE` · `ESCALATE`.

**There must be no case whose correct behavior is a silent guess.** If this table has a gap, the gap is a finding, not a judgment call.

**Counterweight — read this every time you add a row.** A framework that routes everything to `EMIT_FLAGGED` and `UNKNOWN` produces no disagreements, passes every regression case, and is perfectly portable. It also extracts nothing, and it will pass five of the six exit criteria while doing so. Reach for a flag when the *document* is genuinely ambiguous — never when the *rule* is merely hard to write. Every row added here moves the yield series in §0.6, and that series is watched.

### 10.4 Escalation

`ESCALATE` is delivered, not just recorded. Escalations are written to `rounds/<N>/joint/escalations.md` and addressed to the Principal, who rules. State whether an escalation blocks the round or is logged and deferred.

### 10.3 Confidence
When flagged emission carries confidence, what the levels mean and how downstream should read them.

---

## §11 — Provenance

### 11.1 Requirement
Every field is cited to a locus with a verbatim quote, or derived by a stable rule ID from cited inputs, or explicitly marked absent. No fourth option. An uncited value is a defect even when correct.

This is not bookkeeping — it is the only mechanical, verifiable form of the portability guarantee. "A model without NYC knowledge could not reach this value" describes a referee that does not exist; every candidate model has New York real estate in pretraining, so that test can never actually be run. "This field has neither a quote nor a rule ID" is the same defect, stated so a machine can find it.

### 11.2 Citation format
Locus specification for document and for recorded details.

### 11.3 Derived values
Rule ID plus the cited inputs it consumed. Every provenance entry records the rule ID **and the framework version it was written under**, so a citation frozen at v1.4 remains interpretable at v3.0.

---

## §12 — Prohibited inferences

> The portability firewall. The hardest section to keep honest, and the one that decides whether the final cold-model test passes.

### 12.1 The rule
Domain knowledge may be used to **read** the document. It may never be used to **supply** a value the document does not contain.

### 12.2 Prohibited list
Enumerated inferences a knowledgeable reader would be tempted to make and this framework forbids. Grows every round.

| ID | Prohibited inference | Round added | Correct behavior instead |
|---|---|---|---|

### 12.3 The portability test — operationalized

Do not state this as an ablation you cannot perform. Every candidate model knows New York real estate; the naive referee is a thought experiment, not an available instrument.

The runnable form is a **traceability audit**: every emitted field must name a verbatim quote locus or a stable rule ID. A field with neither is a portability failure, mechanically detectable, no referee required.

The Rule Auditor runs this audit every round. The Principal runs it again on the cold-model test, against a framework build with §14 removed — a cold model that can only reproduce the answer by pattern-matching a worked example has not demonstrated that the *rules* are portable.

---

## §13 — Regression cases

> **Stripped from the extraction build.** This section stores prior documents' agreed answers; leaving it in would make "read the framework" a lawful way to read prior extractions.
>
> Re-run by a **fresh context** with the agreed answer withheld (protocol §9.1). An extractor who remembers the answer reproduces it whether or not the framework still generates it — which tests recall, not portability, and cannot detect the failure this suite exists to detect.

| Case ID | Doc ID | Round | Class | Rule IDs | Point at issue | Agreed answer | Frozen under | Disposition | Last verified |
|---|---|---|---|---|---|---|---|---|---|

**Dispositions.** `PASS` · `FAIL` (the amendment broke something — fix the amendment) · `SUPERSEDED` (correct under the old version, invalidated by a schema or boundary change; re-adjudicated against the new version, old answer archived with the version that produced it, re-frozen; both extractors plus Principal) · `RETIRED` (the original resolution was itself wrong — Principal only, logged as Class 7a).

SUPERSEDED and RETIRED are never conflated. The first is the suite keeping up with the framework. The second is the suite having been wrong.

---

## §14 — Worked examples

> **De-identified and illustrative.** No live document IDs, no verbatim instrument text traceable to a specific filing. These teach the rules; they are not an answer key for documents in the corpus.

Full extractions for the canonical instrument types in scope, each showing document → events → resolved matrix contribution.

The framework's most effective teaching device for a cold model. Include at least one deliberately hard case per instrument type — and at least one where the correct answer is to flag rather than assert, so a cold reader learns that flagging is a legitimate outcome and not a failure.

Because a cold model may pattern-match these instead of applying the rules, exit criterion 5 is run against a build with this section removed.

---

## §15 — Read procedure

> How the model reads is part of the framework, not an implementation detail. At 25 million documents on an open-weight reader, open-ended comprehension is both the slowest and the least accurate option available. A bounded traversal converts "understand this document" into "walk this checklist," which is faster, cheaper, and — on a weaker model — substantially more accurate.

### 15.1 Pass structure

Define the fixed sequence. A working shape:

| Pass | Input | Output | Notes |
|---|---|---|---|
| **0 — Type** | Recorded details | Instrument type; the type module to load | Cheap, near-deterministic, routes everything downstream. Get this wrong and every later pass is wrong. |
| **1 — Anchor** | Document + type module | Located structural landmarks | Granting clause, schedules, exhibits, signature block, acknowledgment, riders. |
| **2 — Enumerate** | Anchors | Candidate events | Boundary rules from §4. Enumerate before packaging — mixing the two causes the reader to over-fit the first event it finds. |
| **3 — Package** | Each candidate + type module | Full event records | §2 packaging, one candidate at a time. |
| **4 — Verify** | Event set + completeness contract | Pass or flagged defects | §2.10. Mechanical check, not a judgment. |

### 15.2 Per-type read plans
For each instrument type: where its events live, which anchors matter, which terms are expected, and the traversal order. This is the highest-leverage accuracy work in the framework — a reader told *where to look* outperforms a smarter reader told only *what to find*.

### 15.3 Degradation rules
What the procedure does when an anchor is missing, a document is out of form, or a pass returns nothing. Every pass needs a defined failure exit; a pass that silently returns empty produces a document with no events and no error.

---

## §16 — Budget and modularity

> Every token of framework in the prompt is multiplied by 25 million documents. A framework that grows without bound becomes unrunnable long before it becomes wrong, and nothing else in this document will notice it happening.

### 16.1 Build architecture

| Build | Contents | Loaded |
|---|---|---|
| **Core** | Schema, modes, nulls, provenance, time, parties, direction, prohibited inferences, read procedure §15.1 | Every document |
| **Type modules** | Per-instrument-type rules, read plans, expected terms, worked boundaries | One per document, selected by Pass 0 |
| **Development build** | Core + all modules + §13 + §14 | Never used for extraction |
| **Extraction build** | Core + one module | Production |

**Rules belong in the narrowest build that can hold them.** A rule in Core is paid for on every document forever; the same rule in a type module is paid for only where it applies. This is the pressure that keeps the framework from becoming a monolith, and it must be applied at amendment time — retrofitting modularity later means re-verifying every regression case.

### 16.2 Budgets

| Quantity | Budget | Current | Notes |
|---|---|---|---|
| Core tokens | | | Multiplied by 25M |
| Largest type module | | | Worst-case per document |
| Total prompt per document | | | Core + module + document + details |
| Passes per document | | | §15.1 |
| Wall-clock per document | | | On target hardware |

### 16.3 Amendment pricing
Every amendment states its token cost and which build it lands in. An amendment that adds to Core states why it could not live in a module.

Amendments that push Core past budget are rejected regardless of merit. Not because the rule is wrong — because a framework that cannot run is worth less than one that runs slightly worse.

---
