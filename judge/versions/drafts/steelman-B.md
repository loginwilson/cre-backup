# Steelman — Extractor B

Written without reading `reconcile-A.md`, `steelman-A.md`, A's transcript, or A's private reasoning. The fact that A's steelman changed A's positions is not used as evidence here.

My positions entering this exercise were:

- an express leasehold creation/assignment belongs in Title because it creates or transfers a possessory estate; Encumbrance fires only for an independently stated burden;
- an observation has an occurrence/statement time and a separate asserted-valid time; when only the former is known it can appear in an evidence-time lane but cannot compose into state at that time;
- sale price belongs in Value, project expenditure in Cost, while transfer tax and recording fee were quantities that did not create Cost events merely by appearing on a cover or tax form.

## 1. Deadlock: lease as Title versus Encumbrance

### 1.1 Strongest case for the position I do not hold: lease as Encumbrance

The strongest Encumbrance position is not “a lease is a burden because lawyers call it one.” It starts from the matrix's unit of resolution: a tax-lot BBL. On the ordinary recorded lease or memorandum, the indexed BBL is the fee parcel. The document names a landlord who retains fee ownership and a tenant who obtains a time-limited right of possession. If the event is written into that BBL's Title cell as a transfer to the tenant, the matrix has made a statement the instrument does not make: that the tenant displaced the fee holder in the parcel's title chronology.

Title is the most dangerous column in which to rely on a richly typed object and hope every consumer remembers the type. At 25M documents, many downstream queries will ask “who held title at this time?” before they ask “which estate kind?” A leasehold event in the same Title column as fee conveyances creates a false-positive owner unless every consumer is estate-aware forever. The safer parcel-level rule is:

- Title tracks ownership of the indexed legal parcel/estate;
- Encumbrance tracks time-bounded possessory and contractual claims that burden that parcel;
- a lease becomes Title only when the leasehold itself is the indexed legal object—a separately identified leasehold BBL, condominium leasehold unit, or another instrument-expressly distinct estate key.

This is not merely defensive schema design. It follows the document's asymmetry. The landlord can later convey the fee while the lease continues; the tenant can assign or surrender the lease while the fee holder remains. Those are two independent chronologies. On one fee BBL, the lease chronology composes naturally as an Encumbrance object:

`CREATE lease burden → TRANSFER tenant/holder → MODIFY term → TERMINATE surrender/expiration`

The fee chronology remains:

`TRANSFER fee holder → ...`

Putting both into Title requires a multi-estate graph inside every Title cell and requires fee deeds not to overwrite leasehold objects, lease assignments not to look like fee transfers, and consumers to filter before answering even elementary ownership questions. Encumbrance already needs a multi-object graph for mortgages, easements, options, and covenants; a lease fits its lifecycle without adding a second meaning to “title holder.”

The no-outside-inference rule strengthens this case. Words such as “leases,” “demises,” “landlord,” and “tenant” prove a granted possessory right and term. They do not, by themselves, prove the corpus's intended analytical category “ownership interest.” Treating every possessory right as Title imports a legal taxonomy into the matrix. Treating it as an expressly granted claim on the indexed fee parcel stays closer to what the recording presents.

A separately indexed leasehold is the principled exception, not a concession. There the BBL/object itself is the leasehold estate. A transfer of that indexed object belongs in Title because the matrix's row no longer stands for the fee parcel. The boundary is therefore observable from the inputs: what legal object is indexed and expressly conveyed, not what a reader knows about estates.

### 1.2 Document shape that would settle it

Freeze a two-part conformance fixture from real instruments, not a doctrinal description:

**Fixture L1 — one fee BBL, concurrent estates stated.** A ground lease or memorandum that:

- indexes exactly one ordinary fee BBL;
- expressly says the landlord owns/retains the fee;
- “leases and demises” the entire premises to the tenant for 75–99 years;
- gives an explicit commencement and expiration;
- expressly permits assignment;
- includes, in the same package or a later operative section, an assignment or surrender that changes only the tenant/leasehold and says the fee ownership is unchanged.

Run both schemas through the fold. The test is not which label sounds legal. The test is whether the Title design can keep fee and leasehold objects concurrent, apply the lease transfer/termination only to the leasehold object, and let the query “fee holder after the lease assignment” return the landlord without special-case repair. If it cannot, Encumbrance wins for a one-fee-BBL lease.

**Fixture L2 — separately indexed leasehold object.** An assignment of a leasehold condominium/unit or other instrument where the cover and operative clause identify the indexed object itself as the leasehold estate, including an appurtenant common interest. If an Encumbrance-only rule cannot represent the assignee as holder of that indexed estate without pretending the estate is merely a burden, Title wins for that shape.

The pair is necessary. L1 tests whether Title corrupts fee continuity; L2 tests whether Encumbrance erases a separately identified estate. A single easy lease will only confirm whichever schema was designed around it.

### 1.3 Downstream cost of each answer

| answer | chronology/resolution benefit | chronology/resolution cost | cost at 25M scale |
|---|---|---|---|
| Always/ordinarily Title | Preserves the leasehold as a possessory estate and makes assignments/surrenders visible to estate consumers. | Mixes fee and leasehold holders on one BBL; requires object-key and estate-kind filtering in every ownership resolver; an unsafe consumer can report tenant as fee owner. | Systematic false-positive title holders and more complex Title folds/queries on every lease. The error is high severity even if lease volume is modest. |
| Encumbrance on fee BBL, Title only for separately indexed leasehold | Keeps fee ownership stable and models lease lifecycle alongside other burdens; simple “fee title” queries stay safe. | A leasehold consumer must look outside Title on ordinary fee BBLs; assignment of a valuable long-term lease can be hidden among mortgages/covenants; Encumbrance becomes semantically crowded. | Systematic undercount of leasehold estates unless downstream joins Encumbrance; large multi-object Encumbrance cells and more function-specific queries. |
| Linked Title + Encumbrance for every lease | Represents both the estate and burden facets explicitly. | Duplicates one operative act across two high-volume state registers; requires cross-function identity and exact paired termination/transfer forever. | Doubles lease events and creates reconciliation failures whenever one side of the pair is missed. It is not free merely because both statements can be defended. |

### 1.4 Did the steelman move me?

It narrowed my position but did not reverse it.

I no longer think “lease is Title” is safe unless Title is explicitly a multi-estate object map and every Title query is required to name `interest_kind`. A scalar or winner-takes-all Title cell would make the Encumbrance position decisively better.

Given the state-object architecture I proposed, I still choose Title when the operative words expressly create or transfer a leasehold/possessory estate. The reason is evidentiary: the document directly grants/transfers that estate, and suppressing it from Title makes the Title function unable to answer who holds a leasehold. I would not automatically add Encumbrance on the same fee BBL; that second event requires an independently specified burden path, not the legal intuition that every lease burdens the fee.

I will change to the Encumbrance-with-indexed-leasehold-exception rule if Fixture L1 shows that the closed Title schema or its actual downstream consumer cannot keep concurrent fee and leasehold objects separate without special cases. That is a real possibility, not a rhetorical escape hatch.

## 2. Deadlock: observation date when only statement time is known

### 2.1 The two candidate rules

My current rule is bitemporal:

- `occurrence_time` records when the survey/certificate/affidavit/statement was made;
- `asserted_valid_time` records when the document says the observed condition was true;
- when valid time is absent, the observation may appear at occurrence time in a separate evidence-time lane but does not write state at that time.

The strongest opposing rule is stricter: if the document gives only when the statement was made, the observation is unplaced in the BBL's state chronology. Statement time remains provenance/registry metadata, but the event does not land on the state time axis until the truth time is supported.

### 2.2 Strongest case for leaving it unplaced

The principal called the downstream key the **applicable date**, not the document-production date. For a transaction, those often coincide: a deed executed today transfers today. For an observation they are different propositions:

1. “The affiant signed this statement on 2020-06-01.”
2. “The described condition was true on 2020-06-01.”

The first does not entail the second. An affidavit signed in 2020 can recount a condition seen in 1960; a survey certificate can be issued from an older field survey; an appraisal can be signed after its valuation date; a transfer form can classify use from records rather than a same-day inspection. If valid time is absent, placing the observation in the 2020 BBL row—even with `epistemic_character = OBSERVATION`—invites the state resolver to read “evidence entered here” as “state true here.”

The promised separate evidence lane may not protect against this. The next phase reorganizes events into each BBL's chronology and resolves by function. Every extra temporal lane is another contract every consumer must honor. If one canonical chronology carries a date, many downstream systems will sort and window on it without preserving the difference between evidence time and valid time. The safe rule is to refuse the tempting date rather than rely on perfect downstream discipline.

This is the temporal analogue of refusing to use recording date. Recording proves when the registry received an instrument, not when its represented state applied. A signature proves when an observation was asserted, not when its content was true. Renaming the first fact `occurrence_time` does not make it a state-valid date.

At corpus scale, statement-date placement creates a directional bias: observations accumulate near filing/digitization periods, making old buildings, uses, values, and absence assertions look newly created or newly true. The errors will be plausible. A 2020 observation in a 2020 cell looks normal, so it will survive review and then influence every later state. An unplaced observation is visibly incomplete and can be resolved later from an explicit measurement/inspection/as-of date or a cross-document process.

Leaving it unplaced does not mean dropping it. The event retains BBL, function, parties, content, statement time, terms, evidence, and `valid_time = UNKNOWN`; it appears in an observation-valid-time exception lane and coverage counts. What it refuses is precisely the unsupported relation between the words and a parcel-state moment.

### 2.3 Document shape that would settle it

Use a matched pair plus one adversarial control:

**Fixture O1 — same form, explicit truth time.** A signed survey, appraisal, physical-condition certificate, or occupancy affidavit that visibly carries three distinct fields:

- inspection/survey/valuation/as-of date;
- signature/certification date;
- recording date.

The three dates must differ. The event must land on the stated truth/as-of date for state evidence, while signature time remains observation occurrence and recording remains registry fact. This proves the schema can preserve all clocks.

**Fixture O2 — same form, truth-time field blank.** The same form/template and same kind of present-state statement, with the inspection/as-of field blank but the signature date completed. Apply both candidate rules. If statement-date placement causes O2 to land where O1 would have landed only because its explicit truth date happened to equal signature, it has collapsed two independent fields. If the observation becomes unusable despite current-tense words expressly tied to certification (“I hereby certify that the premises now contain…”), the unplaced rule may be too strict.

**Fixture O3 — adversarial recital.** A statement signed in 2020 that expressly says the described condition existed “in 1960” or “at the time of the 1960 survey,” with no claim about 2020. Any rule that writes the condition into 2020 state fails immediately. This fixture prevents a system from treating all signed observations as contemporaneous.

The deciding question is operational: can the downstream resolver place O2 at the statement date in an evidence-time lane while mechanically preventing every state query/fold from treating that as valid time? If yes, the bitemporal rule preserves evidence without fabrication. If no—if the consumer has one date axis—O2 must remain unplaced.

### 2.4 Downstream cost of each answer

| answer | chronology/resolution benefit | chronology/resolution cost | cost at 25M scale |
|---|---|---|---|
| Statement date becomes state/applicable date | Every observation is placeable; one time axis; simple rows and joins. | Fabricates truth time; observations can overwrite or conflict with transactions at the wrong moment; recitals of old conditions become present state. | Systematic temporal drift toward signature/filing eras, plausible false current-state assertions, and poisoned downstream state after each misplaced observation. |
| Bitemporal: statement date in evidence lane, valid time separate/possibly UNKNOWN | Preserves when evidence entered and what interval it claims; no transaction fold; observations remain searchable. | Requires two temporal indexes and every consumer to distinguish them; unknown valid-time observations still cannot resolve state. | More storage/query complexity and consumer-contract risk, but no forced fabrication if implemented correctly. |
| Leave observation unplaced whenever valid time is absent | Maximally honest state chronology; impossible to mistake statement time for truth time. | Removes many useful current-tense surveys/forms/affidavits from the main chronology; creates a large exception lane; downstream cannot rank them among state evidence. | High unplaced rate and loss of observational coverage, but failures are visible rather than silently wrong. Heavy/escalation cannot fix genuinely unstated dates. |

### 2.5 Did the steelman move me?

Yes, conditionally and materially.

I still prefer the bitemporal rule when the next phase truly supports two separately named time axes and forbids OBSERVATION events from the transaction fold. But I no longer support placing an observation at statement time inside a single undifferentiated BBL chronology. If v1's matrix/consumer has only one `WHEN` axis, the opposing rule is correct: leave valid time unplaced and carry statement time only as evidence metadata.

So my position is now a hard interface test, not a prose warning:

- two-axis consumer with separate observation lane → place occurrence at statement time, valid time UNKNOWN, no state composition;
- one-axis state chronology → do not place from statement time; route to UNKNOWN_VALID_TIME.

This movement follows from tracing the consumer, not from learning that A moved.

## 3. Gap, not deadlock: transfer tax and recording fee

My reconciliation left transfer tax and recording fee as typed quantities unless an operative clause independently created a cost obligation. That strands amounts the Cost consumer needs and makes their matrix placement depend on which form happened to carry them. I replace that position with this proposed rule.

### 3.1 Proposed executable rule

1. **Recognize exact kinds.** When a citable cover, registration field, executed tax/transfer form, receipt, or operative clause labels an amount as NYC/NYS real-property transfer tax, mortgage tax, transfer tax, recording fee, filing fee, or another named tax/fee, create one quantity-registry item with exact kind `TRANSFER_TAX`, `MORTGAGE_TAX`, `RECORDING_FEE`, `FILING_FEE`, or `OTHER_NAMED_TAX_FEE`. Preserve the raw label and source-specific status words.
2. **Emit a Cost observation.** The labeled amount emits `function = COST`, `mode = ASSERT`, `epistemic_character = OBSERVATION`, subtype `TRANSACTION_TAX` or `RECORDING_FEE`. It asserts a transaction/recording cost measurement; it does not create, transfer, modify, or terminate a payment obligation merely by being reported.
3. **Type the status without inference.** Set cost status only from the label/verb: `PAID`, `CHARGED`, `DUE`, `ASSESSED`, `EXEMPT`, or `REPORTED_AMOUNT`. A bare field such as “Filing Fee $125.00” is `REPORTED_AMOUNT`, not PAID. A zero is numeric zero only when the field is affirmatively completed; a blank is UNKNOWN.
4. **Date honestly.** Applicable/valid time is the explicit paid/charged/due/assessment date if stated. A form's explicit transaction/as-of date may be used only when its wording attaches the tax/fee to that date. Otherwise valid time is UNKNOWN. The recording timestamp is never substituted, even for a recording fee. Statement/cover occurrence time can live in the evidence lane under the observation rule above.
5. **Parties stay unknown unless stated.** Do not infer payer from grantor/mortgagor, payee from the City/State/register, or allocation from customary liability. Populate payer/payee only from express labels/clauses.
6. **Scope and BBL fan.** Link the Cost observation to the transaction event group and its expressly affected BBL/scope set. If one amount covers several BBLs/events and no allocation is stated, keep one `INSTRUMENT_TOTAL` quantity with `allocation_status = NOT_DERIVABLE`; every fanned projection references that id and none carries a parcel amount. A document-level recording fee with no supportable affected BBL remains an unplaced/document-scope Cost observation rather than being attached by address.
7. **Source authority is field-local.** An executed tax form or receipt controls the tax/fee amount it labels; a recording cover/registration controls the register-reported tax/fee field. If both are present and differ, apply the tax/fee source hierarchy and preserve the lower-ranked discrepancy. Do not let either source resolve consideration, sale price, principal, payoff, value, or another quantity kind.
8. **Deduplicate only the same measurement.** Exact repeated displays of the same kind, amount, status, scope, and transaction reference coalesce with both evidence ids. Different tax kinds coexist. Same-kind/same-scope controlling values that differ become a document conflict; they are not summed or averaged.
9. **No tax-rate inference; enforce derivation closure.** Every derived output must name an allowed derivation rule from the framework's closed, enumerable set and cite each input that rule requires. This tax/fee rule adds no allowed route from a tax/fee amount to price, principal, payoff, taxable consideration, or value, and no route from another amount to tax/fee using an unstated rate. A different intra-document derivation is lawful only if another enumerated rule expressly admits it; being numerically correct is not an admission rule.
10. **An unlabeled registration amount stays untyped.** `registration.amount` or its schema equivalent is retained as `INDEX_REPORTED_AMOUNT` with semantic kind UNKNOWN unless a citable image label or operative text identifies what it measures. Registration type never supplies the kind. It creates no Value/Cost/Capital event while untyped. In frozen test document `2002122700153001`, the image's `NYS Real Estate Transfer Tax: $2,102.00` is a TRANSFER_TAX Cost observation, while the registration's `$525,500.00` remains UNKNOWN in meaning even though applying the unstated $2-per-$500 statutory rate would recover that exact true consideration.
11. **Fold as evidence, not lifecycle.** The Cost cell's observation layer records the measurement and provenance. It does not set a project-cost lifecycle or overwrite separately stated construction/renovation/operating costs.

### 3.2 Why this rule is preferable

It gives the Cost function a stable home for explicit transaction charges without conflating them with sale Value or Capital. It also avoids A's stronger overclaim that every listed fee was necessarily paid and avoids B's orphan quantity with no Cost event. The OBSERVATION character and status vocabulary carry exactly what the source states.

At scale, this adds Cost observations to many recorded transactions, but they are low-complexity, typed, and quantity-conserving. The alternative—leaving them unattached—makes a later consumer rediscover function placement from form type, which defeats the framework.

### 3.3 Did writing the rule move me?

Yes. I move from “tax/fee is usually quantity metadata only” to “an affirmatively labeled tax/fee amount is a Cost ASSERT/OBSERVATION with a typed status.” The change is not that a recording cover becomes legal proof of payment; `REPORTED_AMOUNT` is deliberately weaker. The change is that the measurement now has an explicit function and cannot be silently dropped downstream.
