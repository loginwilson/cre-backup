# THE LOOP — what replaces the bootcamp, and why

Written at the close of run 55, on the login's ruling: *"we need a system
that learns and improves. we are just repeating currently."*

This file governs. Bootcamp.md remains the RECORD of runs 1-55 and the
source material for the specs; it is no longer the process.

---

## I. WHY THE OLD LOOP COULD NOT LEARN

Four findings, all from the banked record, none of them opinion.

**1. Nineteen classes in twenty runs.** Runs 36-55 read: subordination, POA,
easement, declaration of covenants, deed, condo declaration, declaration of
merger (x2), amended condo declaration, CEMA, development rights, corporate
certificate, waiver and consent, letters patent, in rem deed, waiver of legal
grade, affidavit concerning real estate, certified copy of will, termination
of regulatory agreement, CEMA. **Two repeats in twenty draws.** The reader was
a first-timer on nearly every document. There was never a second instance
against which a first instance could become a rule.

**2. The grade is flat.** Runs 35-55: B, B+, D, B+, B−, B+, B+, B, B−, C+, B,
B+, B, C+, C+, C+, B, C+. Twenty runs, no trend.

**3. The cures overfit, and the record says so three times.** Every precheck
check was validated against the run that produced it and passed. Three are
recorded failing on the very next document: r21→r37 (name integrity), r45→r46
(count-per-se), r54→r55 (closure). A check tested once, one run later, on a
randomly drawn document of a different class, is not tested.

**4. The loop mints artifacts only for defects, so correct reads decay
(R55-4).** r47 read handwritten interlineations and recorded whether they were
initialed. Because that was RIGHT, no rule, no check, nothing carried it. At
r55 an uninitialed interlineation on the operative sum went unread. **The
system's memory is a list of ways it has failed. It has no description of how
to succeed.**

And one consequence that explains the most stubborn class: the rule base
(~10,000 lines across five files, ~100 numbered rules) passed the point where
it can be recalled rather than consulted. RECALL-AS-SOURCE stands at six
members (37, 41, 43, 51, 54, 55). At r55 four rule citations went out
unverified and one was fabricated outright. That is a capacity limit, not
carelessness, and no further rule can fix it.

---

## II. WHAT CHANGES

**The unit of work is a CLASS BATCH, not a document.** Five documents of one
class, drawn together, read in sequence.

**The output is a SPEC, not a verdict.** Verdicts do not compose — fifty-five
of them gave run 56 nothing to stand on. A spec composes: each new member
either conforms to it or breaks it, and breaking it updates the spec. That is
a state that accumulates, which is the minimum requirement for learning.

**The measurement is two numbers, not a letter.**

- **COVERAGE** — of the spec fields this document actually carries, how many
  did the read find? Should sit at 100%. When it does not, the failure is
  reading discipline, and it is now a number rather than an opinion.
- **SURPRISE** — how many things did this document carry that the spec did not
  predict? Counted, not judged.

**Surprise falling across a class IS the learning.** A class is CLOSED when
two consecutive new members produce zero surprises. That is convergence, and
it is the first thing in fifty-five runs that can be said to have improved.

The letter grade may stay as a summary. It is not the measurement and never
was one — it was an opinion, self-assigned, about work no one else read,
against no fixed reference.

---

## III. THE SPEC FORMAT

One file per class, `specs/<CLASS>.md`, six sections.

**1. IDENTITY — how to recognise it.** The shelf types it hides under, its
caption language, its remarks patterns. This is where the type-shelf and
catch-all knowledge finally lands as reusable data instead of a recurring
surprise. Six mismatches and two catch-alls have been discovered one at a
time; they belong here, per class, as expectations.

**2. THE EVENT — which of the eleven fire.** Per class this is nearly fixed,
and it is the class's signature. For CEMA: CAPITAL·modifies, `transacts`.
Deviations from the signature are findings.

**3. FIELDS — the extraction schema.** A table: field · always / usually /
sometimes / never · where it sits · how it is verified · what absence looks
like. This is the part a program can eventually fill.

**4. VERIFICATION — the tests this class requires.** Not general discipline;
the specific arithmetic and comparisons this class always needs. This is the
READ SHEET, and it is derived from the class rather than invented per run.

**5. CHAIN — what this class always points at.** The documents it names and
does not contain.

**6. SURPRISES — the running log.** What each new member carried that the spec
did not predict. This is the learning record and the number that should fall.

---

## IV. THE GATE

When a spec changes, it is re-checked against the class's prior members. **A
spec edit that contradicts an already-read document is rejected**, or the
contradiction is recorded as a branch. Nothing is asserted for a class that
one of its own members disproves.

This is the regression test the loop has never had, and the material for it
already exists: fifty-five decoded documents, banked.

---

## V. WHAT HAPPENS TO THE ~100 RULES

Every existing rule sorts into exactly one of three buckets.

- **(a) class-specific** → moves into that class's spec and **stops being
  something to remember**. R40-2 (the $10 recital), R36-1 (remarks rescue a
  catch-all), L-8 (the §255 affidavit), R11-1 (the index keeps one cite):
  these are facts about document classes, not general wisdom.
- **(b) mechanizable over delivered text** → stays in precheck, unchanged.
- **(c) genuine cross-class judgment** → a SHORT card set, small enough to
  hold in working memory. The assumption law, READ/DERIVED/INFERRED, the three
  cell states, Card #2 class-vs-instance. Target: no more than a dozen.

Buckets (a) and (b) leave the reader's memory entirely. That is the only
available cure for RECALL-AS-SOURCE, because the class is caused by the size
of what must be recalled.

---

## VII. ⚠ SURPRISE IS TWO NUMBERS, NOT ONE (ruled at batch 2)

Batch 2 failed its own convergence criterion: surprise was 6 and 8 against a
predicted "below 5 on each". Recorded as a fail.

The diagnosis is that **the metric was too coarse. It counted a three-digit
date typo in a sworn affidavit equally with a missing spec field.**

**Surprise is therefore graded by kind:**

- **STRUCTURAL** — the spec lacks a FIELD or a RULE. The document does
  something the spec has no place to put. (batch 2: obligor assumption ·
  CEMAs recurse · the assignment round trip · the operative sentence's
  form-bounded exception.)
- **INCIDENTAL** — a defect or a fact about THIS instance. A typo, a missing
  exhibit, an unindexed party, a custodial quirk of the era.

**ONLY STRUCTURAL SURPRISE HAS TO CONVERGE.** Incidental surprise is unbounded
because documents are messy, and a spec that drove it to zero would be a spec
that had stopped looking. Incidental findings are still recorded — they are
what the corpus is for — but they do not measure the spec.

Measured retrospectively: **structural surprise 6 (batch 1) → 4 (batch 2).**
That is the number to carry.

⚠ **A class CLOSES when two consecutive members add NO STRUCTURAL surprise** —
not when they add nothing at all.

## VI. FIRST BATCH

**CEMA**, which already has three read members:

| run | doc | era | sum |
|---|---|---|---|
| 13 | RC_1043006 | 2009 | modern, §255 affidavit IN the file |
| 45 | FT_1000000284200 | 1988/89 | Manhattan, $173M, deconsolidation |
| 55 | BK_7140048401460 | 1971 | Queens, $1.575M, leasehold+fee spread |

Three members already spanning four decades and three custodians. Two more
draws close the batch. The spec is built from the three banked entries FIRST —
no new reading — and then the two new draws test it. That is the first real
test this system has ever run: a prediction made before the document is
opened, and scored against it.
