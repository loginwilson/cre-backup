# NYC C.R.E.D. — Shared Context Brief

**Distribute this document identically to every agent in the loop. It is context, not instruction. The rules you will operate under are in `01-protocol.md`.**

---

## 1. What this system is

NYC C.R.E.D. (Commercial Real Estate Decoded) is a source-first property intelligence system for New York City. It ingests public records — ACRIS, DOB, DOF, BSA, DCP, Richmond County, and others over time — and converts them into a reconstructed functional history of every parcel.

The organizing conviction: most real estate products begin with a product question and work backward to answer *the state now*. That approach discards the meaning of each individual document and loses historical context. C.R.E.D. inverts it. Decode the source thoroughly first, reconstruct how the present came to be, and the products fall out of the reconstruction.

The system has three phases:

| Phase | What it does | Output |
|---|---|---|
| **1. Reproduction** | Enumerate, synchronize, navigate, and document the source. Build a complete, source-faithful mirror of the record universe. | A live inventory of filing IDs, structured registry details, and the source documents themselves. |
| **2. Reconstruction** | **Extract** each document into events → **Reorganize** events onto the parcels and timeline they belong to → **Resolve** the ordered events into functional state through time. | BBL-level event histories and a temporal state matrix. |
| **3. Production** | Derive signals from reconstructed state and productize them. | Current, historical, and predictive property intelligence. |

**Your work is confined to Extract — the first step of Reconstruction.** You are not building Reorganize or Resolve. But you must understand both, because extraction output that cannot reorganize and resolve correctly is worthless, and the correctness bar for extraction is defined entirely by what those downstream steps need.

---

## 2. The Reproduction layer you inherit

Reproduction is complete enough to work against. The Legal Instruments DB holds roughly **25 million rows**, each keyed by a document ID, each carrying structured registry detail from the source system, and each associated with a source document file.

### 2.1 The access loop

Three steps, every document, no variation:

1. **Choose the document ID** from the Legal Instruments DB.
2. **Read the registry row** — the structured detail the source captured at filing.
3. **Open the PDF at the stored path** recorded in that row.

```
RC_988537
  D:\CRE Decoding System\...\By Document\1917\03 Mar\28\RC_988537.pdf
  EXISTS   248.1 KB

2002122000001001
  D:\CRE Decoding System\...\By Document\2003\01 Jan\06\2002122000001001.pdf
  EXISTS   93.2 KB
```

**Read the stored path. Never re-derive it, never search for it, never fetch a URL.** The row is authoritative. Re-deriving a path finds nothing for files that exist, and going to the web for a document you already hold is slower, less reliable, and returns something you cannot prove is the same file.

Work from rows where the document is present. Coverage edge cases — not yet fetched, adjudicated imageless — are a production concern, not a framework-development one; there is far more than enough readable material to build and test the framework on.

### 2.2 A path is a locator, not evidence

You will see the path, because you need it to open the file. That is all it is for.

Look at what those paths contain. The first says `1917\03 Mar\28`. The second says `2003\01 Jan\06` — while its document ID begins `20021220`. Folder date and ID date already disagree, and **neither is necessarily the event date.** A reader that harvests a date from the directory structure has produced a value having read nothing, and it will be a *recording*-flavored date, which is precisely what §4 exists to keep separate from event date.

That failure is invisible from inside the loop: systematic rather than random, so both extractors commit it identically and the A/B diff shows nothing. It would also make extraction output a function of storage layout — reorganize the archive and the corpus changes.

So the rule is not "don't look at the path." It is:

> **Paths, folder names, filenames, URLs and pipeline metadata are never citable.** They locate the file. They say nothing about what is in it.

The existing provenance requirement already enforces this: every field carries a verbatim quote from the document, or a citable registry field, or a rule ID. A path is none of those, so it can never appear in a valid citation. Nothing extra to check — just never make it an exception.

### 2.3 Citable registry fields

The registry row mixes genuine source content with pipeline bookkeeping. Enumerate which fields are **citable** — recorded party names, document type, recording date as the registry states it — and treat everything else as plumbing you may use to find the file and may never quote as fact.

Enumerate the citable list explicitly rather than listing what's excluded. Across 25 million rows and an evolving pipeline, an exclusion list admits every new column by default and nobody notices.

---

## 3. Extract: a document becomes events

A document is not a fact. A document is a *record of one or more things that happened*. The unit of reconstruction is the **event**, not the document.

Many instruments contain several events. An air rights transfer, for example, may simultaneously move development rights, create a restrictive declaration constraining the granting parcel, state a consideration, and encumber both parcels — four or more distinct events, affecting two or more parcels, carrying different dates, parties, and directions, all inside one filing.

Every event is assigned to exactly one of **eleven functions**:

| # | Function | Provisional scope |
|---|---|---|
| 1 | **Identity** | What the parcel *is* as a legal and administrative object. Lot creation, merger, apportionment, condominium declaration, designation and address change. |
| 2 | **Title** | Who holds the estate and in what form. Fee transfers, deeds, ownership interests and shares, tenancy form, life estates, reversions. |
| 3 | **Entitlement** | What the parcel is legally permitted to become. Zoning district and special district, variances, special permits, ULURP actions, development rights held or transferred. |
| 4 | **Envelope** | The permitted or defined physical form. Bulk, FAR utilized and remaining, height and setback, coverage, form-constraining declarations. |
| 5 | **Encumbrance** | Claims and limits against the estate. Mortgages as liens, easements, restrictive declarations, leases, mechanics liens, UCC filings. |
| 6 | **Capital** | Financing structure and its movement. Originations, assignments, consolidations and modifications, subordination, satisfaction, position in the debt stack. |
| 7 | **Permit** | Authorization to perform work. Job filings, permit issuance, work authorizations, sign-offs, demolition authorization. |
| 8 | **As Built** | The physical reality actually constructed. Gross square footage, unit count, stories, constructed use, completion, demolition. |
| 9 | **Occupancy** | Legal permission to occupy, and by what use. Certificates of occupancy, temporary certificates, use group occupancy, vacancy. |
| 10 | **Cost** | Expenditure to create or alter. Estimated and actual construction cost, job cost filings. |
| 11 | **Value** | Worth. Consideration on transfer, assessed value, market value, taxable value. |

**These eleven functions are fixed.** They are the columns of the state matrix and the spine of every downstream product. You may not add, remove, or merge them.

**Their boundaries are not fixed.** The definitions above are provisional and deliberately incomplete. Deciding where Entitlement ends and Envelope begins, whether a restrictive declaration is Encumbrance or Envelope or both, whether a lease is Title or Encumbrance — these boundary questions are where extraction errors actually live, and settling them with decision procedures is a substantial part of your job.

---

## 4. Reorganize: events find their parcel and their place in time

Extracted events are then fanned onto the BBL or BBLs they affect and sorted chronologically.

Two properties of this step constrain extraction directly:

**Events fan to parcels, not to documents.** One document may produce events touching several BBLs, and each event must carry the parcel or parcels it affects. An event that cannot be attributed to a parcel cannot be reorganized.

**Filing date is not event date.** A document recorded in 2020 may record something that happened in 2018. Chronology is built on when the thing *happened*, not when it was filed. Every event therefore needs a derived event date with an explicit basis, and the framework must specify how that date is derived when the document offers several candidates — execution, effective, recording, acknowledgment — or none.

---

## 5. Resolve: events become state through time

Ordered events resolve into the **Temporal State Matrix** — the core artifact of the whole system.

- The **vertical axis is time.**
- The **horizontal axis is the eleven functions.**
- A **cell** is the state of one function at one point in time.
- Reading **across a row** gives the complete functional state of a parcel on a given date.
- Reading **down a column** gives the full history of one function.

This is what makes the system work. Present state is credible because it is grounded in reconstructed history; historical depth supplies context for pressure, momentum and behavior; patterns across time produce predictive signal.

**The matrix is your real acceptance test.** Two extractions of the same document are equivalent if and only if they resolve to the same matrix. Event tables that look different but resolve identically are equivalent. Event tables that look nearly identical but resolve differently are not.

Which means the phrase "resolve to the same matrix" has to be given a precise meaning before it can carry that weight. Row granularity, the sort key and tie-break for same-date events, how two events on one function on one date fold into a single cell, how each null renders, and the serialization used for comparison — all of it must be pinned down. You will therefore produce a **resolve-spec** alongside the framework in Phase 0: a minimal deterministic reference implementation of Reorganize and Resolve. Not a production resolver — just enough that "same matrix" is a fact rather than an opinion. It versions independently and travels with the framework everywhere the framework goes.

A consequence worth stating plainly: a blank cell is ambiguous, and ambiguity here is corrosive. "This event did not touch this function," "this function is unknown at this time," "this function cannot apply to this parcel," and "the document affirmatively states there is none" are four different states. They must be distinguishable in the event record, not inferred downstream.

---

## 6. Independent read

Each document is extracted **in isolation**. No cross-document context. No neighboring filings, no prior state of the parcel, no knowledge of what came before or after.

This is a deliberate architectural choice, not a limitation to work around:

- It is the only thing that scales to 25 million documents.
- It keeps extraction deterministic and reproducible — the same document yields the same events regardless of processing order.
- It puts all cross-document reasoning in Reorganize and Resolve, where it belongs and where it can be audited.

The direct consequence: **you cannot resolve ambiguity by looking at other records.** When a document is ambiguous, the framework must tell you what to do about it. Silent guessing is the single most damaging failure mode in this system, because a plausible guess is indistinguishable from a fact once it reaches the matrix.

---

## 6.5 What an event actually is

Assigning a function and a timestamp is the *minimum* an event must carry, because those two fields are what Resolve consumes to build the matrix. They are not the hard part, and a framework that treats classification as the job will fail.

The hard part is **packaging**: the rigid discipline by which a document distills into events that carry everything downstream needs, with nothing invented and nothing dropped.

An event package must account for at least:

| Dimension | What it carries | Why it is hard |
|---|---|---|
| **Function + timestamp** | One of eleven; derived event date and its basis | Required by Resolve. The floor, not the job. |
| **Mode** | Whether the event CREATES, MODIFIES, TRANSFERS, TERMINATES, ASSERTS, or CORRECTS state | A mortgage origination and a satisfaction are both Capital and opposite in effect. Function alone cannot resolve. |
| **Parties and roles** | Every party, its role, its side, its share | Many parties per side. Sometimes no counterparty. Roles are not inferable from position on the page. |
| **Direction** | Whether the event is directional at all, and if so from what to what | Not everything is a transaction. Forcing direction onto a state assertion fabricates structure. |
| **Quantities** | Measure, unit, basis, and allocation | One instrument may state a single aggregate while individual events take shares or fractional interests. Allocation is sometimes derivable and sometimes not — and inventing one is a fabrication that will never be caught downstream. |
| **Terms** | Rate, maturity, duration, conditions, covenants, options, triggers | See below. Most likely thing to be dropped, most expensive to lose. |
| **Parcel attribution** | Affected BBLs, and each parcel's role in the event | An air rights transfer has a granting and a receiving parcel. They are not interchangeable. |
| **State delta** | What the function's state becomes, in the four null semantics | This is what Resolve folds into a cell. |
| **Provenance** | Per field: quote and locus, or rule ID and inputs | The only mechanical portability guarantee. |

### Terms are how the past generates the future

The Production layer includes a Debt Maturity Tracker, a Refinance Pipeline, a Construction Loan Monitor, an Entitlement Tracker. Every one of those is a *prediction seeded by a term extracted at event time*. A mortgage event without its maturity date cannot feed a maturity tracker. A ground lease without its expiry cannot feed anything.

Terms are the most droppable field — they sit in dense clauses, they vary in form, and an extraction that omits them still looks complete. They are also unrecoverable: no amount of matrix reconstruction regenerates a maturity date that was never captured, and re-extracting 25 million documents to add a field is not a correction, it is starting over.

Treat terms as first-class from v1.0.

---

## 6.6 Three constraints, not one

**Accuracy** is the binding one. Millions of documents extracted at 85% accuracy is not a database with some errors in it — it is a corpus nobody can trust for any individual answer, which is the only kind of answer the products give. You are only as good as the accuracy of your data.

**Time.** Extraction must run at speed across the corpus. The read procedure is part of the framework, not an implementation detail — see §15 of the skeleton.

**Cost.** Processing and storage are covered by the Torch allocation. What is *not* covered is the framework's own token footprint: every token of framework sitting in the prompt is multiplied by 25 million documents. A framework that grows without bound becomes unrunnable long before it becomes wrong.

These pull against each other. More rules generally buy accuracy and always cost tokens and time. The framework therefore carries an explicit budget, and every amendment is priced against it.

---

## 6.7 The reader is not you

Production extraction runs on an **open-weight model** on Torch — not the models developing this framework. Open weights will likely be near frontier capability by then. Plan as though that is true, and do not build on it.

Here is the part that matters, and it runs against intuition: **a more capable reader does not hallucinate less in this setting. It hallucinates more plausibly.** Where your rules are silent, a capable model interpolates — confidently, coherently, in a form indistinguishable from an actual reading. That output passes every downstream check, because nothing downstream can tell an interpolation from an observation. Capability without constraint is the mechanism that produces confident false data at scale; it is not the defense against it.

So the framework's job is not to prop up a weak reader. It is to **remove the occasions on which any reader has to interpolate.** Get that right and intelligence becomes a bonus — speed, robustness to messy scans — rather than a dependency you cannot audit.

The measure of this framework is therefore not how accurately *you* extract. It is **how small the gap is between your accuracy and the target model's on the same framework and the same documents**. A small gap means the rules are doing the work. A large gap means they are being carried.

Practically: mechanical decision procedures over deep conditional reasoning; explicit read order over open comprehension; bounded context over "here are all the rules, work out which apply." Each of these buys time and cost as well as accuracy, at any capability level.

---

## 7. What you are actually building

You are building **the extraction framework** — a rulebook that converts any document in scope into its event table.

The framework is the deliverable. The individual extractions are not. Every document you process exists only to stress the framework and expose where it is underspecified.

The framework must satisfy one final test, which you do not administer:

> A model with no memory of your conversation, given only the framework and the resolve-spec and a document it has never seen, must produce an event table that resolves to the same matrix as the reference extraction.

Everything follows from that. It means the framework must be written as **executable decision procedures, not advice**. "Consider whether the instrument transfers development rights" is useless. "IF the instrument conveys development rights AND the granting lot is identified, THEN emit an Entitlement event on the granting lot with direction OUTBOUND and a paired Entitlement event on the receiving lot with direction INBOUND" is a rule. Every rule carries an immutable ID so that a value extracted today can still name the procedure that produced it three versions from now.

It also means your own domain knowledge is a hazard. You both know a great deal about New York real estate. That knowledge will let you quietly repair ambiguous documents in ways that don't generalize — and every time you do, the framework fails its portability test while appearing to succeed.

Do not try to police this by introspection. You cannot reliably notice an inference you never experienced as an inference, and "a model without NYC knowledge couldn't reach this" describes a referee that does not exist — every model has New York property records in its pretraining. The control is mechanical instead:

> **Every emitted field carries either a verbatim quote and locus, or a rule ID and the inputs that rule consumed. A field with neither is a defect, whether or not the value is correct.**

That is checkable by anyone. Domain knowledge may justify a rule you *write into the framework*. It may never justify a value you extract.

### 7.1 Two ways this goes wrong

Both are failures. They pull in opposite directions and you will feel pressure toward whichever one you are not currently worried about.

**Bloat.** Legislating every difference produces a rulebook too large and too special-cased for a cold model to apply consistently. Guarded by the Class 0 rule: if a difference doesn't change the matrix, it doesn't get a rule.

**Conservative collapse.** The subtler one. A framework that routes everything to "flagged" or "unknown" produces no disagreements, passes every regression case, and is perfectly portable — and extracts nothing. Every argument you end by reaching for the safe answer moves one notch this way, and nothing moves it back. Guarded by a yield floor and a flag-ratio series that is logged every round.

Flag when the *document* is ambiguous. Never when the *rule* is hard to write.
