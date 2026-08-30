# Principal Operating Guide

**For you, not for the agents.** The loop has five jobs it cannot do for itself, because each one requires either ground truth or an authority the extractors don't have. This is what those jobs are and when they happen.

---

## Before round 1

### Freeze the scope enumeration
List the instrument types, sources, and date ranges the framework is expected to handle. Write it into framework §0.4 yourself.

The extractors must not own this. Exit criterion 2 requires breadth "across every instrument type in scope" — if they can edit the scope, they can satisfy that criterion by deleting the hard types, and it will look like progress.

### Build the charter slate
~6 documents for Phase 0a. Spread across instrument types, including at least one you already know is nasty.

The charter prompt asks the extractors to test their event-boundary rule against real documents rather than hypotheticals of their own construction, because a model inventing its own test cases invents ones its rule already handles.

### Build the ground-truth set
~15 documents, extracted and adjudicated **by hand**. This is the most tedious thing on the list and the only real ground truth in the entire system. Everything else is models checking models.

Include: at least two multi-parcel instruments, two where the event date differs from the recording date, two where the registry details contradict the document, and at least one that is genuinely ambiguous and *should* be flagged rather than asserted — you need to be able to distinguish appropriate flagging from collapse.

### Build the held-out pool
~20 documents the extractors never see, never propose, and never hear about. Split it:

- **Exit-streak documents** — the five you feed in for criterion 1
- **Cold-model documents** — for criterion 5

Produce your own reference extraction for each cold-model document. Criterion 5 compares the cold model's matrix against *your reference*, not against a committed extraction — because for a document the extractors never saw, there is no committed extraction to compare to.

### Set the thresholds
Criteria 6, 7 and 8 need numbers. Decide them before the loop starts, while you have no stake in whether they pass — thresholds set after you can see the scores are not thresholds.

- **Recall floor** — minimum share of ground-truth events emitted, scored on the **full package** (function, date, mode, parties, quantities, terms, parcel roles), not on classification alone
- **Flag ceiling** — maximum share of fields permitted to be flagged
- **Gap tolerance** — maximum acceptable frontier/target accuracy difference
- **Budget** — Core tokens, worst-case per-document prompt, passes and wall-clock per document

Opening values of 90% and 15% are reasonable for the first two; calibrate after you have hand-extracted the fifteen and can see how ambiguous the corpus actually is. For the budget, work backwards from throughput: 25 million documents at your Torch allocation gives you a per-document time and token envelope, and that envelope is the constraint, not an aspiration.

### Name the target model
Write it into the Principal log before round 1 — the specific open-weight model and size you expect to run extraction on, or the two or three candidates.

Everything about how the framework should be written depends on this, and "we'll decide later" resolves in practice to "we assumed frontier capability." If you genuinely don't know yet, name the *weakest* plausible candidate and build against that; a framework that works on the floor also works above it.

---

## Every round

### Supply a candidate slate
10 document IDs with instrument type and minimal registry metadata.

The extractors cannot select adversarially without knowing something about the documents beforehand, and protocol §5 forbids them from looking. The slate resolves that — and it keeps selection from being fully controlled by the two agents whose blind spots are the target.

### Verify hashes
Record the sha256 at declaration, re-verify at reveal. A hash that changed means a committed file was edited. Void the round.

This takes ten seconds and it is the only thing making commit-then-reveal more than an honor system.

### Receive escalations
`rounds/<N>/joint/escalations.md`. Rule on out-of-scope documents and on ambiguities the framework has no procedure for.

---

## Every 5 rounds — the ground-truth check

Both extractors run the ground-truth set under normal isolation.

| Round | Extractor accuracy | A/B agreement | Emit/flag ratio | Package completeness |
|---|---|---|---|---|

**Agreement rising while accuracy is flat is convergent error.** That is the failure mode most likely to kill this project, it is a trend rather than an event, and this table is the only place it becomes visible. The Rule Auditor produces per-round anecdotes; anecdotes cannot show you a slope.

Accuracy holding steady while the flag ratio climbs is the framework buying its scores by declining to extract.

Package completeness is scored on the **full event package**, not on function and timestamp. Break out terms separately — they degrade silently, they are unrecoverable without re-extracting the corpus, and an event table missing them looks perfectly healthy.

---

## Every 5 rounds — the target-model gate

Same ground-truth set, same framework version, run on the **actual open-weight model** you plan to use.

| Round | Extractor accuracy | Target accuracy | **Gap** | Target-specific failures |
|---|---|---|---|---|

**The gap is the headline number of the project.** Your working assumption is that open weights will be near frontier by extraction time, and that is probably right — but it is an assumption about a model that does not exist yet, and this is where you find out.

The reason capability doesn't rescue a loose framework: a more capable reader doesn't hallucinate less here, it hallucinates *more plausibly*. Where the rules are silent it interpolates confidently and coherently, and nothing downstream can tell an interpolation from an observation. The framework's job is to remove the occasions to interpolate. The gap tells you whether it has.

A gap that is flat or widening while extractor accuracy improves means the loop is optimizing for the wrong reader. The response is not more rules — it is shallower ones, more explicit read order, and more specificity pushed into type modules.

Log the target's *specific* failures too, not just the score: rules it misapplies, passes it skips, fields it drops, output formats it fails to produce. Those enter the loop as Class 7c and are the most actionable findings you will get.

Start this early. Round 5, not round 25 — a framework can drift a long way from followable in twenty rounds.

---

## On demand — arbitration

A Class 3+ open question unresolved after 3 rounds comes to you. Rule on it. The ruling is binding, logged, frozen as a regression case, and not re-litigable.

Without this the loop can deadlock permanently on a single boundary argument: protocol §8.1 says unresolved questions stay open, exit criterion 4 says no Class 3+ questions may remain, and the extractors have already established they cannot agree. Two good models can disagree forever about whether a restrictive declaration is Envelope or Encumbrance. Someone has to decide, and it isn't them.

You also confirm or dismiss unrebutted Document Reader suspicions. Only Principal-confirmed suspicions become Class 7a — otherwise the loop's agenda gets set by its lowest-information participant.

---

## At the end — the cold-model test

Criterion 5, and the only one that really matters.

Give a model with no history of this work:

1. The **extraction build** of the framework — §13 stripped
2. The resolve-spec
3. **§14 worked examples removed** — a cold model that reproduces the answer by pattern-matching an example has not shown the *rules* are portable
4. One held-out document and its recorded details

Compare its resolved matrix against your reference extraction.

Then run the traceability audit on its output: every field must carry a verbatim quote locus or a rule ID. Fields with neither are portability failures even where the value is right — they mean the model reached the answer by a route the framework doesn't describe, which will not survive contact with 25 million documents.

Run this on at least three held-out documents, ideally with three different model families. One pass is an anecdote.

---

## Things to watch for

**The loop declaring victory early.** Exit criteria are checked by the agents who want to be finished. Check them yourself.

**Flag ratio creeping up.** Every deadlock resolved conservatively moves the framework one notch toward "flag everything," and nothing in the loop moves it back. §0.6 is the tripwire.

**The regression suite becoming the whole cost.** By round 30, unbounded full runs dominate. Protocol §9.2 samples, but watch that boundary amendments still trigger full runs — those are exactly the ones that invalidate old answers.

**Suspicions going unrebutted because nobody has time.** They queue to you. A growing unrebutted queue means the Document Reader is generating noise, the extractors are ignoring it, or both — and either way the correlated-error defense is not running.

**Both extractors getting quieter.** Falling disagreement counts look like progress and are equally consistent with two models learning each other's habits. Cross-check against the accuracy series before believing it.
