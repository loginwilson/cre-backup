# Extraction Framework Development Protocol

**v2. Distribute identically to every agent. Read `00-context-brief.md` first.**

Binding. Where it conflicts with your judgment, it wins — its constraints exist to defeat failure modes that are invisible from inside the loop.

---

## 1. Roles

| Role | Assigned to | Function |
|---|---|---|
| **Extractor A** | Claude Code | Independent extraction. Co-owner of the framework. |
| **Extractor B** | Codex | Independent extraction. Co-owner of the framework. |
| **Document Reader** | Clean context, model family ≠ either extractor | Reads the document with no framework. Hunts facts both extractors missed or mischaracterized. Output is *suspicion*, not finding. |
| **Rule Auditor** | Clean context, holds the framework | Examines what the extractors **agreed** on and asks whether the agreement was produced by the document or by a framework rule. |
| **Principal** | Human operator | Owns scope, candidate slates, ground truth, held-out pool. Arbitrates deadlocks. Confirms shared errors. Administers the cold-model test. |

Extractors A and B are peers. Neither is senior. Neither defers.

**Why two auditors.** When A and B disagree, they resolve it themselves against the document — no third party needed. The auditors exist for the opposite case, when they *agree*, because that is when the loop is blindest. But the two blindnesses have different causes and need different instruments. The Document Reader catches things the document contains that nobody captured. The Rule Auditor catches things the framework *taught both of them* to get wrong — which a frameworkless reader cannot distinguish from correct application of a deliberate convention.

**Model family matters more than context freshness.** Two LLMs reading the same ambiguous instrument agree largely because they share pretraining, not because they share a rulebook. A fresh context strips the conversation and leaves the priors. Both auditors must therefore come from a family that did not extract this round; where only two families are available, alternate. Record the auditing model in every round log.

---

## 1.5 The target model

Production extraction runs on an **open-weight model** on Torch. Extractors A and B are not that model.

The working assumption is that open weights will be near frontier capability by the time extraction runs. That is a reasonable bet and it is probably right. It is also an assumption about a model that does not exist yet, and the framework must not be built on it — so the loop measures it rather than trusting it.

**Capability does not substitute for the framework, and the reason is counterintuitive.** A smarter reader does not hallucinate less here. It hallucinates *more plausibly*. Where the rules are silent, a capable model interpolates — confidently, coherently, and in a form that survives every downstream check, because the output looks exactly like the output that came from an actual reading. Intelligence without constraint is the mechanism that produces confident false data at scale, not the defense against it.

So the framework's job is not to compensate for weak reasoning. It is to **remove the occasions on which any reader has to interpolate at all.** Done right, capability becomes a bonus — it buys speed and robustness to messy documents — rather than a load-bearing dependency.

**The primary metric of this project is the frontier/target gap**: extractor accuracy minus target-model accuracy on the same framework and the same documents. It is the empirical test of the capability assumption. A small gap means the rules are doing the work. A large gap means they are being carried, and you will not find out which until production unless you measure it.

The target model is therefore **in the loop** (§10.2), not saved for a final exam. A framework can drift a long way from followable in ten rounds, and discovering that at the end costs the project.

Practical consequences for how rules are written — note that each of these serves time and cost regardless of what the target model turns out to be:

- Mechanical decision procedures over deep conditional reasoning, so correctness does not vary with how hard the reader thinks
- Explicit read order over open comprehension (framework §15) — faster, cheaper, and it removes the freedom in which interpolation happens
- Bounded context per document (framework §16) rather than "here are all the rules, work out which apply"
- Every rule tested against: *could a reader follow this literally, without knowing anything about New York real estate, and get it right?* Not because the reader will be ignorant, but because a rule that survives that test has no gap left to fill.

---

## 2. Five failure modes

**Convergent error.** Two agents on a shared framework fail the *same way*, and the better the framework gets the more correlated they become. Agreement rate rises while accuracy plateaus — and the loop reads that as success. → Countered by the Rule Auditor, mandatory traceability, and the Principal's ground-truth series (§10). Note that this failure mode is a **trend**, not an event: it is detectable only by measuring agreement and accuracy as two separate series over time. Per-round anecdotes will not surface it.

**Anchoring.** Any leakage between extractors before both commit destroys the independence the method depends on. One glimpsed intermediate result contaminates the round beyond recovery. → Countered by commit-then-reveal (§4).

**Framework bloat.** Treating every disagreement as urgent produces a rulebook too large and too special-cased for a cold model to apply consistently — failing portability in a way that is very hard to see from inside. → Countered by the Class 0 rule (§6).

**Conservative collapse.** The opposite of bloat, and the more dangerous of the two because it *passes every quality check*. A framework that routes everything to `EMIT_FLAGGED` and `UNKNOWN` produces no disagreements, passes every regression case, and is perfectly portable. It also extracts nothing. Every deadlock resolved in favor of the conservative rule (§8.1) moves one notch toward this attractor and nothing moves it back. → Countered by the yield floor (§11.6) and the emit/flag ratio in every round log.

**Capability borrowing.** The framework appears to work, but what is actually working is the reader filling silent gaps with plausible interpolation. Invisible from inside the loop, because the readers doing the checking are the ones doing the filling — and their interpolations agree with each other. Surfaces in production, at scale, as confident false data that looks exactly like real extraction. → Countered by the target-model gate (§10.2), the traceability audit (§5.1), and the frontier/target gap as the headline metric.

---

## 3. Round structure

Phase 0 runs once. Phases 1–8 repeat per document.

```
P0  CHARTER      Independently draft, then merge: schema, resolve-spec, framework v1.0
P1  SELECTION    Blind-propose from the Principal's slate
P2  ISOLATION    Extract independently — no contact
P3  SELF-ATTACK  Each argues against its own table, before reveal
P4  REVEAL       Commit, then diff at resolution level and event level
P5  ADJUDICATE   Classify, resolve, then run both auditors
P6  AMEND        Framework changes under change control
P7  REGRESS      Fresh-context re-run of sampled frozen cases
P8  LOG          Record the round; return to P1
```

P6–P8 are folded into the P4/P5 prompt as steps 8–11.

---

## 4. Isolation (P2) — commit-then-reveal

The independence of the two extractions is the entire epistemic value of the exercise. Protect it mechanically.

1. **Separate directories.** `rounds/<N>/A/` and `rounds/<N>/B/`. Never a shared directory.
2. **Neither extractor may read, list, or open anything under the other's directory** until both have committed.
3. **Commit** = the output files are complete and the extractor has posted a declaration stating document ID, framework version, resolve-spec version, event count, emitted-vs-flagged field counts, and the `sha256` of each output file over its raw bytes.
4. The Principal (or a Traycer pre-commit step) records the hashes at declaration and re-verifies them at reveal. A hash that changes between declaration and reveal voids the round.
5. **Reveal** happens only after both declarations are recorded. A committed extraction is frozen. Changes of mind become logged corrections in P5 (§7.5), never edits.
6. **Any leakage voids the round.** Discard both extractions. Add the document to the burned register — it is contaminated for both parties permanently and may never be re-proposed. Restart at P1 with a different document.

If the environment cannot enforce this, the discipline stands in for it. Treat rule 2 as absolute regardless of what technically prevents you.

---

## 5. Extraction inputs — hard restriction

The **only** permitted inputs, every extraction, every round:

1. The **document ID**
2. The **registry row's citable fields** (§5.0.2)
3. The **document** at the stored path
4. The **extraction build** of the framework at version `<X.Y>` (Core + the type module selected by read Pass 0)
5. The resolve-spec at version `<R.n>`

### 5.0 Access

Three steps, no variation: **choose the ID → read the registry row → open the PDF via the resolver.**

`DOCUMENT ACCESS.md` is the contract and it governs absolutely. Read it before your first document. In brief:

```python
import sqlite3, corpus_paths as CP

c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
c.execute("PRAGMA busy_timeout=30000")

# readable rows only
c.execute("SELECT id, pdf FROM navigation WHERE pdf LIKE '%.pdf' ORDER BY id")

path = CP.doc_path(pdf_value)       # -> Path, or None for a state
```

**Use `CP.doc_path()`. Never hand-join, never re-derive.** `doc_store_dir()` looks like the right function and is the *writer's* — it decides where a file goes, with fallbacks, and which branch it took is unrecoverable. A recomputing reader reports "missing" for files sitting on disk. The stored `navigation.pdf` value was written when the file landed; that is the truth.

`navigation.pdf` holds five values and only one is a file. `''`, `pending`, `absent` and `imageless` are determinations, not filenames — `doc_path()` returns `None` for each, which is what stops the empty-string join from silently resolving to the store root. A resolved path that does not exist is an **integrity fault**: report it with the ID, never skip it quietly, never launder it into "no image."

Select rows where the document is present. Coverage states are a production concern, not one for this loop — there is far more readable material than the framework needs. **Count your own denominator** (`pdf LIKE '%.pdf'`); the board's "landed" figure includes determinations.

Operating alongside the reproduction lanes: read-only with `busy_timeout` (a lock error looks exactly like a missing document), always `ORDER BY id`, and no full table scans on a tick.

### 5.0.1 A path is a locator, not evidence

You will see the path — you need it to open the file. That is the whole of its role.

`…\By Document\1917\03 Mar\28\RC_988537.pdf` states a date in its directory structure. `…\2003\01 Jan\06\2002122000001001.pdf` states a different one from the date inside its own document ID. **Neither is necessarily the event date**, and a reader that harvests one has produced a value having read nothing — a recording-flavored date standing where §4 requires an event date.

That error is systematic rather than random, so both extractors commit it identically and the A/B diff shows nothing. It would also make extraction output a function of storage layout, which is disqualifying for a system claiming source-faithful reproduction.

> **Paths, folder names, filenames, URLs and pipeline metadata are never citable.**

No new machinery enforces this. The provenance rule already does: every field carries a verbatim document quote, a citable registry field, or a rule ID, and a path is none of those. Just never make it an exception.

### 5.0.2 Citable registry fields

The row mixes source content with pipeline bookkeeping. The framework enumerates which fields are **citable** — recorded party names, document type, recording date as the registry states it. Everything else is plumbing: usable to find the file, never quotable as fact.

Enumerate what is citable rather than what is excluded. Across 25 million rows and an evolving pipeline, an exclusion list admits every new column by default and nobody notices.

### 5.0.3 One note for the resolve-spec
Coverage is out of scope for the extraction loop, but the resolve-spec must reserve a place for it: a parcel with no events over a span because those documents were never fetched is not a parcel that was quiet, and in a resolved matrix the two are identical unless coverage travels forward as its own state. Leave the slot; fill it at production.

This is not tidiness. Archive paths encode information — a path like `…\By Document\1917\03 Mar\28\RC_988537.pdf` states a recording date in its directory structure, and a reader that sees it can emit a date having read nothing. That error is systematic rather than random, so both extractors commit it identically and it survives the A/B diff; it arrives looking cited; and the Document Reader cannot catch it because it never sees paths. It would also make extraction output a function of storage layout, which is disqualifying for a system whose claim is source-faithful reproduction.

**Paths, filenames, folder names, URLs, keying metadata and crawl timestamps are not weak evidence. They are not evidence.** They do not enter extraction at any confidence level, and no rule may cite them.

`details.json` is populated by **whitelist, never blacklist** — genuine registry content in, pipeline metadata out. Across 25 million rows and an evolving pipeline, a blacklist admits every new column by default and nobody notices; a whitelist fails closed.

### 5.0.1 Retrieval failure is not an extraction judgment
Missing file, checksum mismatch, zero-byte or corrupt file, page count of zero, or a document that does not correspond to its ID — these are **operational states**, reported by `manifest.json` and handled by the retrieval layer. They are not ambiguity, they do not go through the §10 ambiguity policy, and they never produce a partial extraction. A packet that fails retrieval does not reach an extractor.

**Extraction build** means the framework with §13 (regression cases) stripped. §13 stores prior documents' agreed answers; leaving it in would make "read the framework" a lawful way to read prior extractions, which §5 otherwise forbids. Framework §14 (worked examples) stays in, but must be written as illustrative and de-identified — no live document IDs.

**Prohibited:** other documents; prior parcel state; external lookups; the other extractor's output; and your own knowledge of New York real estate *as a source of extracted values*.

- **Permitted:** domain knowledge used to *read* — knowing what an abbreviation expands to, recognizing a standard form, parsing a schedule of parties.
- **Prohibited:** domain knowledge used to *supply* — inferring a typical value, assuming a customary party role, filling a missing date from what usually happens, silently correcting an apparent error.

### 5.1 How this is actually enforced

Do not rely on introspection. "Notice when you are about to use outside knowledge" asks for access to something you cannot observe — the inference you never experienced as an inference. The real control is mechanical:

> **Every emitted field carries either (a) a verbatim quote and locus, or (b) a stable rule ID plus the cited inputs that rule consumed. A field with neither is a defect, whether or not the value is correct.**

That is checkable by anyone, including a machine. Self-reported contamination notes in P3 are a supplement to this, never a substitute.

---

## 6. Disagreement taxonomy (P5)

Classify before discussing. Classification determines the response and stops the loudest disagreement from setting the agenda.

### 6.1 Precedence ladder

Classes overlap. Apply these tests **in order** and take the first that fires. Where the extractors classify differently, the **higher class wins**.

1. Resolved matrices identical? → **Class 0**
2. Externally found, both extractors wrong, Principal-confirmed? → **Class 7a**
3. Neither extractor's citation supports either value? → **Class 7b**
4. Event counts differ after normalizing decomposition? → **Class 5**
5. Same facts, different decomposition? → **Class 2**
6. Same fact, different function? → **Class 3**
7. Different event date or date basis? → **Class 4**
8. Same event, different value/party/direction/share? → **Class 6**
9. Same fact, different representation? → **Class 1**

### 6.2 Responses

| Class | Name | Response |
|---|---|---|
| **0** | Cosmetic | Log only. **No amendment permitted.** |
| **1** | Normalization | Amend: canonicalization rule |
| **2** | Granularity | Amend: event boundary rule |
| **3** | Classification | Amend: function boundary decision procedure |
| **4** | Temporal | Amend: date derivation rule |
| **5** | Existence | Resolve by citation, then amend detection or suppression |
| **6** | Content | Resolve by citation, then amend the relevant rule |
| **7a** | **Shared error, external** | Highest priority. Amend, plus a detection rule for the class of blindness |
| **7b** | **Mutual miss, internal** | Both wrong, found by the extractors. Amend as 7a |

**The Class 0 rule is the anti-bloat valve and it is not optional.** No matrix change, no new rule. You will want to legislate these anyway. Don't.

**Both 7a and 7b reset the exit streak.**

---

## 7. Reveal and resolution (P4)

### 7.1 Resolution-level diff, first
Push both event tables through the resolve-spec and compare matrices cell by cell. Report before anything else — it sets priority: divergence that survives to the matrix is real, divergence that vanishes is Class 0.

### 7.2 Event-level diff
Field by field. Tells you where divergence originated, including for divergence that turned out not to matter.

### 7.3 Exchange self-attack notes — *before* classifying
The notes name framework gaps. Reading them after the diffs are settled throws away most of their value. Places where both extractors independently flagged the same gap are the highest-signal finding available in a round.

### 7.4 Resolve by document, not by deference
Whoever's citation actually supports their value wins. If neither citation supports either value, both are wrong — Class 7b.

Agreement reached by one extractor yielding to the other, rather than to the document, is worse than disagreement: it hides a disagreement from the log.

### 7.5 Corrections are artifacts, not edits
A losing extractor does not edit its committed table. It appends to `rounds/<N>/<A|B>/corrections.md`: the original value, the winning value, and the citation that decided it. The **corrected union table** is what seeds regression cases and what gets re-resolved. Committed tables stay frozen as the record of what independence actually produced.

---

## 8. Amendment discipline (P6)

Every amendment must satisfy all seven:

1. **Cites its cause** — round number and disagreement class.
2. **Generalizes** — states a rule about a class of documents. An amendment naming its triggering document is rejected. You are writing law, not patching a case.
3. **Is executable** — a decision procedure with determinate inputs and outputs. If two competent readers could apply it and diverge, it is not finished.
4. **Carries a stable rule ID** — immutable, never reused, independent of section numbering (`R-0147`). Section numbers move; provenance citations must not rot.
5. **Is uniquely located and non-contradictory.** Conflicts are resolved by rewriting both rules, not by adding precedence notes.
6. **Carries a regression case** (§9).
7. **Is agreed by both extractors.**
8. **Is priced.** States its token cost and which build it lands in — Core or a type module. An amendment landing in Core must state why it could not live in a module.

### 8.0 Amendment pricing

Every token added to Core is paid on every document — **25 million times.** The same rule in a type module is paid only where it applies.

This is not an accounting nicety. It is the pressure that keeps the framework from becoming a monolith that is accurate in principle and unrunnable in practice, and it has to be applied at amendment time: retrofitting modularity later means re-verifying every regression case against a rebuilt document.

**An amendment that pushes Core past budget is rejected regardless of merit.** Not because it is wrong — because a framework that cannot run is worth less than one that runs slightly worse. When this happens, the response is to find the module the rule belongs in, or to replace three specific rules with one general one, not to raise the budget.

### 8.1 Deadlocks
Unresolved amendment disagreement is logged as an open question, and the framework holds the more conservative rule in force — where no incumbent rule exists, that default is `EMIT_FLAGGED` with both readings, **never** `EMIT_NONE`. Flagging preserves the disagreement for later resolution; emitting nothing destroys it.

**A Class 3+ open question unresolved after 3 rounds goes to the Principal, who rules.** The ruling is logged, frozen as a regression case, and is not re-litigable. Without this, one stubborn boundary argument blocks exit forever.

Version increments on every accepted amendment set, with a changelog entry naming round, class, rule IDs, and sections touched.

---

## 9. Regression suite (P7)

### 9.1 Fresh-context execution
**Regression cases are re-run by a clean context given the extraction build of the framework, the resolve-spec, and the document — with the agreed answer withheld.** An extractor who remembers the answer will reproduce it whether or not the framework still generates it, which tests recall and not portability. The extractors compare afterward.

### 9.2 Sampling
Full-suite runs on any schema change or any §3.3 function-boundary amendment. Otherwise a stratified sample: every case touching an amended rule ID, plus a rotating fraction of the rest. Unbounded full runs become the dominant cost by round 30.

### 9.3 Dispositions
- **PASS / FAIL.** A case that now fails means the amendment broke something. Fix the amendment.
- **SUPERSEDED.** A case whose agreed answer was correct under version V but is invalidated by a schema change or a function-boundary amendment is re-adjudicated against the new version, its old answer archived with the version that produced it, and re-frozen. Requires both extractors plus Principal sign-off.
- **RETIRED.** Only when the Principal rules the original resolution was itself wrong — which is logged as a Class 7a.

SUPERSEDED and RETIRED are different events and must never be conflated in the log. The first is the suite keeping up with the framework; the second is the suite having been wrong.

---

## 10. Measurement (Principal)

### 10.1 Ground-truth check — every 5 rounds

The Principal maintains a human-adjudicated ground-truth set of ~15 documents spanning declared scope. Both extractors run it under normal isolation. The Principal logs, separately:

- **Extractor accuracy** against ground truth
- **Agreement rate** between extractors
- **Emit/flag ratio**

**Agreement rising while accuracy is flat is the signature of convergent error.** It cannot be seen in a single round — it is a slope, and per-round anecdotes have no slope. Accuracy flat while the flag ratio climbs is the framework buying its scores by declining to extract.

### 10.2 Target-model gate — every 5 rounds

The same ground-truth set, same framework version, run on the **actual production open-weight model**. Log:

- **Target accuracy**
- **Frontier/target gap** — extractor accuracy minus target accuracy
- **Target-specific failure modes** — where the target model breaks that the extractors did not: rules it misapplies, passes it skips, fields it drops, formats it fails to produce

**The gap is the headline number of this project.** It is the only measurement that distinguishes a framework from a hint sheet, and it is the one the extractors cannot take themselves — they are, structurally, the wrong instrument.

A gap that is flat or widening while extractor accuracy improves means the loop is optimizing for the wrong reader. When that happens the response is not more rules; it is *shallower* rules, more explicit read order, and more of the framework's specificity pushed into type modules where a weaker reader meets less of it at once.

Target-model failure modes enter the round as **Class 7c** — a shared blindness of both extractors about what their own rules actually require of a reader. They amend like any other Class 7, and they reset the exit streak.

---

## 11. Exit criteria

The framework serves three constraints, not one. **Accuracy** is binding — a corpus at 85% is not a database with some errors, it is one nobody can trust for any individual answer, which is the only kind of answer the products give. **Time** and **cost** are hard limits at 25 million documents, and a framework that fails them is not a slower framework, it is an unusable one.

Finished when **all eight** hold:

1. **Five consecutive clean rounds** — zero Class 2–7 disagreements, all five documents drawn from the Principal's held-out exit pool, all five run under a **single frozen framework version**. No amendments of any class during the streak; any amendment or any Class 2+ resets to zero.
2. **Breadth** — every instrument type in the Principal's frozen scope enumeration extracted at least twice, in different rounds, under framework versions that differ in a section governing that instrument type.
3. **Regression suite passes in full** on the current version, fresh-context.
4. **No open questions** of Class 3 or above.
5. **Cold-model test** — the Principal gives a clean model the extraction build of the framework plus the resolve-spec and a held-out document, and its matrix matches the Principal's reference extraction for that document.
6. **Yield floor** — on the Principal's held-out sample, at least the agreed threshold of ground-truth events emitted with correct function and event date, and no more than the agreed ceiling of fields flagged. Yield is measured on the **full event package** (§2 of the framework), not on function and timestamp alone: an event correctly classified but missing its terms, parties, or quantities is a failure, not a partial success.

7. **Frontier/target gap within tolerance** — the target open-weight model, running the extraction build on the ground-truth set, lands within the agreed margin of extractor accuracy. This is the empirical check on the capability assumption, and it is the criterion most likely to be quietly skipped.

8. **Budget** — Core tokens, worst-case per-document prompt, passes per document, and wall-clock per document all within the §16 budgets on target hardware, measured on a representative sample rather than a best case.

Criterion 5 is the one that matters most. Criterion 6 stops the loop from passing 1–5 by refusing to extract anything. Criterion 7 stops it from passing by borrowing capability it cannot verify. Criterion 8 stops it from passing with a framework nobody can afford to run.

**Declaring completion early does not cost a failed test.** It costs 25 million documents extracted under a framework that looked finished.

---

## 12. Standing prohibitions

- Do not read anything in the other extractor's directory before both commit.
- Do not edit a committed extraction. Corrections are appended, logged, and reasoned.
- Do not amend for a Class 0 difference.
- Do not write a rule that only fires for the document that prompted it.
- Do not emit a field without a quote or a rule ID.
- Do not resolve ambiguity by guessing. If the framework has no rule for the case, that is a finding, not a judgment call.
- Do not converge for the sake of converging.
- Do not reach for `EMIT_NONE` or `UNKNOWN` to end an argument. Every such choice is logged in the emit/flag ratio, and a ratio drifting toward flagging is a defect even when every individual choice was defensible.
