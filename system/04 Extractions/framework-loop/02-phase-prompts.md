# Phase Prompts

**v2.** Copy-paste blocks. Each assumes `00-context-brief.md`, `01-protocol.md`, and `03-framework-skeleton.md` are in context.

Version convention: framework `<major>.<minor>` — minor on any accepted amendment set, major on a schema or function-boundary change. Resolve-spec versions independently as `R<n>`.

---

## P0a — CHARTER, INDEPENDENT DRAFT

*Fire separately to each extractor, in isolation, under §4 rules.*

> Framework v1.0 is the most consequential artifact in the system. Building it by unmonitored consensus between the two agents whose consensus the rest of the protocol treats as untrustworthy would bake correlation into every round that follows — and no auditor ever sees it. So the charter is drafted independently and merged, exactly like an extraction.

```
Phase 0a. You are Extractor <A|B>. You will not extract a document yet.

Draft, independently and without contact with the other extractor, three artifacts:

  1. EVENT RECORD SCHEMA
  2. RESOLVE-SPEC — the deterministic reference implementation of Reorganize
     and Resolve
  3. FRAMEWORK v1.0-draft-<A|B>, against the skeleton in 03-framework-skeleton.md

Write to rounds/000/<A|B>/. Do not read the other extractor's directory.

Work through these in order. Do not proceed while an earlier one is unresolved,
and do not paper over uncertainty — an open question logged honestly is worth more
than one that was never really settled.

  A. WHAT IS AN EVENT?
     The atomic unit. When does one instrument produce one event versus several?
     State it as a procedure. Then apply it to three documents from the Principal's
     charter slate and confirm it gives a determinate answer on each. Use real
     documents, not hypotheticals of your own construction — you will invent
     hypotheticals your rule already handles.

  B. WHAT DOES AN EVENT RECORD CARRY?  ← the real work of this phase
     Function and timestamp are the FLOOR, not the job. They are mandatory because
     Resolve consumes them, and a framework that treats classification as the task
     will produce event tables that satisfy the matrix and starve every product
     built on it.

     The job is PACKAGING. Specify each of these as its own sub-schema:
       - mode: CREATE / MODIFY / TRANSFER / TERMINATE / ASSERT / CORRECT.
         Orthogonal to function and not derivable from it — a Capital origination
         and a Capital satisfaction are the same function, opposite in effect.
         CORRECT needs its own rule; treating a correcting instrument as a new
         event duplicates history.
       - parties: role vocabulary, side, per-party share, many-per-side, none.
         Roles are not inferable from position on the page.
       - direction: whether the event is directional AT ALL. Forcing direction onto
         a state assertion fabricates structure.
       - quantities: measure, unit, basis, and the aggregate-vs-allocation problem —
         one stated consideration, several events drawing on it. Specify when
         allocation is derivable and, critically, when it is NOT. An invented
         allocation is a fabrication that looks like data forever.
       - terms: rate, maturity, duration, expiry, conditions, covenants, options,
         triggers. TREAT AS FIRST-CLASS. The Debt Maturity Tracker, Refinance
         Pipeline and Entitlement Tracker are predictions seeded by terms captured
         at event time. Terms are the most droppable fields — dense clauses,
         variable form, and an extraction missing them still looks complete — and
         the least recoverable. Nothing downstream regenerates a maturity date that
         was never read, and re-extracting 25 million documents to add a field is
         not a correction, it is starting over.
       - parcel roles: not just which BBLs, but each parcel's role. An air rights
         transfer's granting and receiving lots are not interchangeable.
       - completeness contract: per instrument type and mode, which fields MUST be
         present. Without this, events get quietly thinner and every check still
         passes.

     Interrogate the list. What is missing? What is conflated? A field added now
     costs little; a field discovered at round 30 costs the regression suite.
     Event identity must be derivable without coordination — two extractors must
     produce comparable identities independently, or diffing is guesswork.

  C. THE RESOLVE-SPEC.
     This is not optional and it is not downstream. Every comparison in this
     project — the round diff, Class 0, the exit streak, the cold-model test —
     is defined as "do these resolve to the same matrix." That phrase is
     meaningless until you specify:
       - event → BBL fan-out
       - sort key and tie-break for same-date events
       - the fold rule per function: how two events on one function on one date
         combine into one cell
       - how each of the four nulls renders in a cell
       - row granularity: what makes a row
       - a byte-comparable serialization of the matrix
     A minimal, deterministic reference is what you need — not a production
     resolver. Version it R1.

  D. THE ELEVEN FUNCTIONS — BOUNDARIES.
     Functions fixed, boundaries not. For each adjacent pair where confusion is
     plausible, write the separating procedure. Start with the ones you already
     suspect: Entitlement/Envelope, Encumbrance/Capital, Title/Encumbrance for
     leaseholds, Permit/AsBuilt/Occupancy across a construction lifecycle,
     Cost/Value, Identity/Title for lot changes that also move ownership.
     Where one instrument legitimately generates events on several functions,
     state the fan-out rule.

  E. TIME.
     Execution, effective, acknowledgment, recording, dates recited in the body,
     and dates in the recorded details that disagree with the document. Write the
     precedence procedure, the rule for recording the basis, and the rule for when
     no defensible event date exists. That last must not silently default to
     recording date — a filing date masquerading as an event date is invisible
     downstream and poisons the chronology.

  F. DIRECTION AND PARTIES.
     Not every event is a transaction. Not every event is bidirectional. Some have
     many parties per side, some none. Some carry per-party shares while the
     instrument states one aggregate value. Cover all of it without special-casing.

  G. REGISTRY VS DOCUMENT.
     When the recorded details and the document body disagree, which governs, for
     which field classes, and how the conflict is recorded in the event. This will
     happen constantly. Decide it once or it gets re-decided inconsistently forever.

  H. BBL ATTRIBUTION.
     Deriving affected BBLs. Multi-parcel events: replicate per parcel or one event
     with a parcel set. Events whose parcel cannot be determined. And the circular
     case — instruments that create, merge, or apportion the very parcel identity
     they reference.

  I. NORMALIZATION.
     Canonical forms for dates, currency, area, percentages, names, addresses,
     document type codes. Normalization may never add information.

  J. AMBIGUITY AND ABSENCE.
     Independent-read means you cannot consult another document to disambiguate.
     For each foreseeable ambiguity, specify EMIT_FLAGGED (with competing readings),
     EMIT_NONE, or ESCALATE. There must be no path whose correct behavior is a
     silent guess.
     Counterweight, and take it seriously: a framework that flags everything passes
     every quality check in this protocol and extracts nothing. Reach for
     EMIT_FLAGGED when the document is genuinely ambiguous, not when a rule is
     merely hard to write.

  K. PROHIBITED INFERENCES.
     The explicit list of things a knowledgeable reader would be tempted to infer
     and this framework forbids. This protects portability and is the hardest
     section to keep honest.

  L. SCOPE.
     Confirm the Principal's frozen scope enumeration and state, per instrument
     type, whether v1.0 claims to handle it. Anything outside declared scope
     ESCALATEs rather than getting a best effort.

  M. READ PROCEDURE.
     How the model reads is part of the framework, not an implementation detail.
     At 25 million documents, open-ended comprehension is both the slowest and the
     least accurate option available — a bounded traversal turns "understand this
     document" into "walk this checklist," which is faster, cheaper, and leaves
     less room for a reader to interpolate.

     Specify the pass structure. A working shape:
       Pass 0  TYPE       from recorded details → instrument type → module to load
       Pass 1  ANCHOR     locate structural landmarks for that type
       Pass 2  ENUMERATE  candidate events, before packaging any of them
       Pass 3  PACKAGE    one candidate at a time, per §2
       Pass 4  VERIFY     completeness contract, mechanically

     Enumerate before packaging — mixing them causes the reader to over-fit the
     first event it finds and miss the rest.

     Then write per-type read plans: where that type's events live, which anchors
     matter, which terms are expected, traversal order. This is the highest-leverage
     accuracy work in the framework. A reader told WHERE TO LOOK outperforms a
     smarter reader told only what to find.

     And degradation rules: what each pass does when an anchor is missing or a
     document is out of form. A pass that silently returns empty produces a
     document with no events and no error.

  N. BUDGET AND MODULARITY.
     Every token of framework in the prompt is multiplied by 25 million documents.
     Split the framework: CORE (schema, modes, nulls, provenance, time, parties,
     direction, prohibited inferences, pass structure) loaded for every document,
     plus ONE TYPE MODULE selected by Pass 0.

     Rules belong in the narrowest build that can hold them. Propose opening budgets
     for core tokens, largest type module, total per-document prompt, passes per
     document, and wall-clock per document. Every later amendment gets priced
     against these.

     Do this now. Retrofitting modularity later means re-verifying every regression
     case against a rebuilt document.

STYLE
Every rule is a decision procedure with a stable rule ID (R-0001, R-0002 …), never
reused, independent of section numbering. If two competent readers could apply your
rule and diverge, it is not a rule yet. "Consider whether…", "generally…",
"typically…", "use judgment" are all failures.

FINISH BY
Naming the three places you believe your own draft is weakest.
```

---

## P0b — CHARTER MERGE

*Fire to both, after both drafts are committed.*

```
Phase 0b. Both charter drafts are committed. Reveal.

Diff the two drafts and classify every difference using protocol §6, exactly as you
would an extraction round. Divergence in your independent drafts is the most
valuable signal you will get all project — it maps, before you have spent a single
document, where two competent readers of the same brief legitimately disagree.

Merge under the §8 amendment discipline into:
  framework-v1.0.md   (schema merged into §2 — it does not live in a separate file,
                       because §5 permits extractors only the framework itself)
  resolve-spec-R1.md

Every merge decision where your drafts differed becomes a founding regression case
and a founding open question if unresolved.

Log the emit/flag ratio your merged v1.0 implies across the charter slate. That is
the baseline for the conservative-collapse check; it should not drift upward.
```

---

## P1 — SELECTION

*Fire to both. Composed without seeing the other's proposal; commit by hash.*

```
Round <N>. Framework <X.Y>. Resolve-spec <Rn>.

The Principal has supplied a candidate slate: 10 document IDs with instrument type
and minimal registry metadata. Propose from the slate. All slate documents are
present in the store — coverage states are a production concern, not one for this
loop, and there is far more readable material than the framework needs.

Write your proposal to rounds/<N>/<A|B>/proposal.md and post its sha256. Do not
read the other's proposal before your hash is posted.

State:
  1. The document ID.
  2. The framework rule ID or gap you intend to stress.
  3. What you predict happens — including, honestly, whether you expect the two of
     you to disagree, and about what.

Selection is adversarial during development. Do not propose a document because it
looks clean. Hunt multi-parcel and multi-function instruments, event dates that
diverge from recording dates, contradictory registry details, and boundaries you
have already argued about.

If proposals differ, take the one targeting the rule with the lowest coverage count
in framework §0.5. On a tie, alternate; in round 1, coin flip and log it.

NOTE: this adversarial policy applies during development only. The five exit-streak
rounds are drawn by the Principal from the held-out pool and you do not choose them
— otherwise you would be required to hunt disagreement and to produce five rounds
without it at the same time.
```

---

## P2/P3 — EXTRACTION AND SELF-ATTACK

*Fire separately to each extractor, in isolation. The round's load-bearing phase.*

```
Round <N>. Framework <X.Y>. Resolve-spec <Rn>. Document ID: <DOC_ID>.

Extract this document into its event table, following the framework exactly.

ACCESS — read DOCUMENT ACCESS.md first; it governs. In brief:

  import sqlite3, corpus_paths as CP
  c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
  c.execute("PRAGMA busy_timeout=30000")
  c.execute("SELECT id, pdf FROM navigation WHERE pdf LIKE '%.pdf' ORDER BY id")
  path = CP.doc_path(pdf_value)        # Path, or None for a state

USE THE RESOLVER. NEVER HAND-JOIN, NEVER RE-DERIVE, NEVER FETCH A URL.
doc_store_dir() looks right and is the WRITER's — it decides where a file goes,
with fallbacks, and which branch it took is unrecoverable afterwards. A recomputing
reader reports "missing" for files that are sitting on disk. The stored
navigation.pdf value was written when the file landed. That is the truth.

navigation.pdf holds five values and only one is a file. '' , pending, absent and
imageless are DETERMINATIONS, not filenames — doc_path() returns None for each,
which is what stops the empty-string join from silently resolving to the store root
and corrupting output thousands of rows later. A resolved path that does not exist
is an INTEGRITY FAULT: report it with the id, never skip quietly, never launder it
into "no image."

Read-only with busy_timeout — the register lane writes constantly and a lock error
looks exactly like a missing document. Always ORDER BY id. No full table scans.

A PATH IS A LOCATOR, NOT EVIDENCE.
You need the path to open the file. That is all it is for.

  ...\By Document\1917\03 Mar\28\RC_988537.pdf
  ...\By Document\2003\01 Jan\06\2002122000001001.pdf

The first states a date in its folders. The second states one that disagrees with
the date inside its own document ID. NEITHER is necessarily the event date. A date
harvested from either is a value produced without reading the document — and the
error is systematic, so both of you would make it and the diff would show nothing.

Paths, folder names, filenames, URLs and pipeline metadata are never citable. The
provenance rule already covers it: a citation is a document quote, a citable
registry field, or a rule ID. A path is none of those.

PERMITTED INPUTS — these five and nothing else:
  1. The document ID
  2. The citable fields of the registry row
  3. The document itself
  4. The extraction build of framework <X.Y>  (§13 regression cases stripped)
  5. Resolve-spec <Rn>

No other documents. No prior parcel state. No external lookups. Not the other
extractor. And not your knowledge of New York real estate as a source of values —
you may use it to READ the document, never to SUPPLY what the document omits.

THE CONTROL IS MECHANICAL, NOT INTROSPECTIVE.
Do not try to catch yourself thinking. You cannot observe the inference you never
experienced as one. Instead:

  Every emitted field carries either
    (a) a verbatim quote plus locus in the document or recorded details, or
    (b) a stable rule ID plus the cited inputs that rule consumed.
  A field with neither is a defect even if the value is right.

If you cannot produce (a) or (b) for a value, the value does not go in. Either drop
it, or write down that the framework needs a rule that would let anyone reach it.

FOLLOW THE FRAMEWORK EXACTLY, INCLUDING WHERE IT IS WRONG.
Counterintuitive, and the point. If the framework produces an extraction you believe
is incorrect, produce it anyway and record the objection separately. Silently
correcting the framework's mistakes hides the defect, and the defect is what we are
hunting. The extraction is disposable. The framework is the deliverable.

WRITE TO rounds/<N>/<A|B>/
  extraction.json    the event table
  resolved.md        your event table pushed through resolve-spec <Rn>,
                     serialized exactly as the spec requires
  objections.md      places the framework made you emit something you think is wrong
  notes.md           self-attack, below

Do not read, list, or open anything under the other extractor's directory until both
completion declarations are recorded.

BEFORE DECLARING COMPLETION — SELF-ATTACK, in notes.md:
  - Every point where the framework was silent, ambiguous, or had to be stretched.
    Cite rule IDs.
  - Every decision where you could defend a different answer, and what it would be.
  - Where you think you are wrong. Argue against your own table as a hostile
    reviewer holding the document would.
  - Every field where you reached for EMIT_FLAGGED or UNKNOWN, and whether the
    document was genuinely ambiguous or the rule was merely hard to write.

Written before reveal, when you cannot know whether it makes you look worse than the
other extractor. That is deliberate — it is the only moment the admission is honest
rather than tactical.

THEN DECLARE COMPLETION
Post: document ID, framework version, resolve-spec version, event count, emitted
field count, flagged field count, and sha256 of each output file over raw bytes.
Do not look at the other extraction until both declarations are recorded.
```

---

## P4–P8 — REVEAL, ADJUDICATE, AMEND, REGRESS, LOG

*Fire to both once both declarations are recorded.*

```
Round <N>. Both extractions committed and hashes verified. Reveal.

Neither committed table may be edited. Corrections are appended artifacts (step 5).

Log owner this round: <A|B>, alternating. Write all outputs to rounds/<N>/joint/.

STEP 1 — RESOLUTION-LEVEL DIFF, FIRST.  → joint/diff-resolved.md
Compare resolved-A and resolved-B cell by cell under resolve-spec <Rn>. Report before
anything else. It sets priority: divergence surviving to the matrix is real,
divergence that vanishes is Class 0.

STEP 2 — EVENT-LEVEL DIFF.  → joint/diff-events.md
Field by field. Shows where divergence originated, including where it didn't matter.

STEP 3 — EXCHANGE SELF-ATTACK NOTES AND OBJECTIONS. → joint/notes-crossread.md
Before classifying, not after. The notes name framework gaps and should inform
classification rather than arrive once it is settled. Where both of you independently
flagged the same gap, that is the highest-signal finding available in this round.

STEP 4 — CLASSIFY.  → joint/classification.md
Apply protocol §6.1's precedence ladder in order; first test that fires wins. Where
you classify differently, the higher class wins. Classification is mechanical and
happens before argument.

STEP 5 — RESOLVE BY DOCUMENT, NOT BY DEFERENCE.
  → rounds/<N>/<A|B>/corrections.md (append-only: original value, winning value,
    deciding citation)
Whoever's citation supports their value wins. If neither citation supports either
value, both are wrong → Class 7b. Do not yield to the other extractor; yield to the
document. Agreement produced by deference hides a disagreement from the log.
The corrected union table seeds regression cases and is re-resolved.

STEP 6 — DOCUMENT READER.  → joint/suspicions.md
Clean context, model family ≠ either extractor. Give it: the document, the recorded
details, both event tables, both matrices, and context sections 00 §3 (the eleven
functions), 00 §5 (matrix semantics), 00 §6 (independent read), 03 §10.1 (the four
nulls). Do NOT give it the framework.
Its output is a SUSPICIONS REGISTER, not findings. Each suspicion requires either an
extractor rebuttal-by-citation or Principal confirmation before it becomes Class 7a.
Unrebutted suspicions go to the Principal.

STEP 7 — RULE AUDITOR.  → joint/rule-audit.md
Clean context, model family ≠ either extractor. Give it the framework, both tables,
and the document. One question only:
  "Which of these two tables' AGREEMENTS were produced by a framework rule rather
   than by the document — and does the document actually support that rule's output
   here?"
This is the instrument that attacks correlated error. The Document Reader finds what
the document contains and nobody captured; the Rule Auditor finds what the framework
taught both of you to get wrong. Only the second one can see a systematic error as
systematic.

STEP 8 — AMEND.  → framework <X.Y+1>, changelog entry
Each amendment: cites round and class; generalizes beyond this document; is an
executable decision procedure; carries a new immutable rule ID; is uniquely located
and non-contradictory; carries a regression case; agreed by both; AND IS PRICED —
token cost plus which build it lands in. An amendment landing in Core must say why
it could not live in a type module, because Core is paid 25 million times. An
amendment pushing Core past budget is rejected regardless of merit; find the module
it belongs in, or replace three specific rules with one general one.
No amendment for Class 0. Deadlocks → open question, conservative rule holds
(EMIT_FLAGGED with both readings where there is no incumbent, never EMIT_NONE), and
Class 3+ unresolved after 3 rounds goes to the Principal for a binding ruling.

STEP 9 — REGRESS.  → joint/regression.md
Re-run by a FRESH CONTEXT given the extraction build, the resolve-spec, and the
document, with agreed answers withheld. Full suite on schema or function-boundary
changes; otherwise every case touching an amended rule ID plus a rotating sample.
Dispositions: PASS / FAIL / SUPERSEDED / RETIRED. Never conflate SUPERSEDED (the
suite keeping up with the framework) with RETIRED (the suite having been wrong).

STEP 10 — LOG.  → joint/round-log.md
Round, document ID, framework and resolve-spec versions in and out, auditing model
families, differences by class, suspicions raised/rebutted/confirmed, rule-audit
findings, amendments with rule IDs, regression status, rule coverage counts updated
in framework §0.5, consecutive-clean-round count, and:

  EMIT/FLAG RATIO — emitted fields vs flagged fields, this round and cumulative.
  A ratio drifting toward flagging is a defect even when every individual choice was
  defensible. It is the signature of a framework collapsing toward "flag everything,"
  which passes every other check in this protocol and extracts nothing.

  PACKAGE COMPLETENESS — share of events carrying every field their completeness
  contract requires, broken out by dimension: mode, parties, quantities, terms,
  parcel roles. Watch the terms column specifically. Terms degrade silently, they
  are unrecoverable without re-extracting the corpus, and an event table missing
  them still looks entirely healthy.

  BUDGET — Core tokens, largest type module, worst-case per-document prompt, passes
  and wall-clock per document, each against its §16 budget.

STEP 11 — EXIT CHECK.
State whether all six criteria hold. Honestly. A premature declaration does not cost
a failed test; it costs 25 million documents extracted under a framework that looked
finished.
```

---

## Document Reader prompt

*Clean context. Model family ≠ either extractor. Gets context, never the framework.*

```
You are the Document Reader for an extraction review.

You are given: a source document, its recorded details, two independently produced
event tables, their resolved state matrices, and four short context sections — the
eleven functions and their provisional scopes, what the state matrix means, the
independent-read constraint, and the four null semantics.

You are NOT given the rulebook that produced these tables. That is deliberate: you
are here to read the document, not to check rule compliance.

Your job is not to pick a winner. Where the tables disagree, the extractors resolve
it themselves against the document.

Your job is the opposite case: WHAT DID BOTH GET WRONG TOGETHER?

Both worked from a shared rulebook, which is the mechanism that makes them fail
identically. Their agreement is weak evidence of correctness, and the places they
confidently agree are where nobody is looking.

Read the document yourself, first, before either table. Form your own view of what
happened in it. Then compare.

Report:
  1. Events in the document neither table captured.
  2. Events both captured but both characterized wrongly — function, date,
     direction, party role, magnitude.
  3. Values both asserted that the document does not support. Quote the text they
     would need and show it is absent.
  4. Anything in the document that is significant AND emittable from these inputs
     alone, appearing in neither table.
  5. Places both tables are suspiciously confident about something the document
     states ambiguously.

CONSTRAINTS
  - Every finding quotes the document. A finding without a quote is a guess.
  - The extractors work under independent-read: they may not consult other
    documents, prior parcel state, or outside knowledge. "They should have checked
    the prior deed" is not a valid finding.
  - Your output is a SUSPICIONS REGISTER, not a verdict. Each item will be rebutted
    by citation or confirmed by the human Principal. You are not scored on volume,
    and a suspicion that gets rebutted costs the project real time — so do not
    manufacture items. A clean report is real information.
  - Some agreements you find surprising will be correct application of a deliberate
    convention you cannot see. Flag them anyway; that is what the rebuttal step is
    for.
```

---

## Rule Auditor prompt

*Clean context. Model family ≠ either extractor. Holds the framework.*

```
You are the Rule Auditor.

You are given: the extraction framework, a source document, its recorded details,
and two independently produced event tables that largely agree.

Ignore where they disagree. The extractors handle that.

Your single question:

  WHICH OF THEIR AGREEMENTS WERE PRODUCED BY A FRAMEWORK RULE RATHER THAN BY THE
  DOCUMENT — AND DOES THE DOCUMENT ACTUALLY SUPPORT THAT RULE'S OUTPUT HERE?

Two agents sharing a rulebook agree for two very different reasons. Sometimes the
document plainly says so. Sometimes the rulebook told them both what to say. Only
the second kind can be systematically wrong, and only you can tell them apart —
a reader without the framework sees an agreement and cannot know which it is.

Method:
  1. For each agreed field, identify whether it traces to a verbatim quote or to a
     rule ID.
  2. For every rule-derived agreement, go to the document and ask whether the rule's
     output is actually supported by what is there.
  3. Flag any rule that fired on this document in a way its authors probably did not
     anticipate — right output for the wrong reason counts, because it will produce
     the wrong output on the next document.

Report, for each finding: the rule ID, what it produced, what the document supports,
and whether the mismatch is specific to this document or a defect in the rule itself.
The second kind matters far more.

Also report: any field carrying neither a quote nor a rule ID. Those are portability
failures regardless of correctness.

If the agreements are all well-founded, say so plainly. But check the rule-derived
ones individually first — those are the entire reason this role exists.
```
