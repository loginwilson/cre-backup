# Ruling — RC_1598772 (1911 Richmond deed)

Five extractors, blind, identical instructions, no contact. Judge: orchestrator.
Every change below names this document.

## Counts

| | events |
| --- | --- |
| A | 16 |
| D | 26 |
| B | 27 |
| E | 27 |
| C | 29 |

**The spread is mostly splitting policy, not disagreement** — B, C and D each showed
it independently. One clause with two dollar thresholds is one row or two; twenty
prohibited trades is one row or twenty; a jurat splits or does not. Treat row-count
deltas as artifacts until proven otherwise.

## Settled by evidence, not vote

**The marks on "Sixteen and Seventeen" are lead-in flourishes. The words are
operative. The orchestrator was wrong.**

Five readers, five methods, unanimous. The decisive one was measurement, not opinion:

> Every horizontal ink run ≥110 native px on page 1 returns **exactly one** — the
> 1,295 px strike through *"subject, however, to all assessments…"*. Shear-corrected
> span across slopes −0.12…+0.12: the three genuine cancellations score **76.3 / 76.4
> / 53.8 %** of region width, each peaking sharply at one slope. *"Sixteen and
> Seventeen"* scores **12.3 %**, flat at every slope — the same band as known
> flourishes (*Heberton Avenue* 10.3 %, *State of New York* 7.9 %). A strike would
> have to land at 50–75 %. No overlap.

Scripts are re-runnable in `loop/B/`. **A measurement ended a dispute that four
readings had only voted on.** That is the model for factual disputes: not debate.

Two corollaries, both found independently more than once:

- the acknowledgment venue lines — *State / City / County of New York* — are **all
  three operative**. At page zoom, three stacked flourishes each starting further
  right read as strikes, in exactly the place a reader expects strikes.
- **the scans are bitonal, so stroke order is unrecoverable.** Nobody — including a
  referee — can settle "drawn before or after" from these images. Only extent and
  morphology are available.

**Residual, unresolved:** one reader reads the acknowledgment **day** as 18 with 15
as the only other candidate it would accept; the figure is overwritten by descenders
from the venue lines. Four read 18. Calendar-possible range 14–25. Not outcome-bearing
here; recorded so it is not lost.

## Accepted into the framework

Ranked by independent confirmations. **No debate was held. These replicated across
blind readers with no contact, which is stronger evidence than any discussion would
produce.**

### 1. There is no mode for a clause deleted before execution — *all five*

Three printed clauses are ruled out in ink. None of `ASSERT / TRANSFER / CREATE /
MODIFY / TERMINATE` fits: `TERMINATE` reads downstream as *"a burden was released"*,
which is false; `MODIFY` says the world changed when only the form did. Yet *"the deed
as executed is not subject to assessment liens"* is load-bearing and exists **only**
because of a deletion.

Every reader buried it in `terms`, where nothing indexing by function will find it.

**Add a sixth mode: `STRUCK`** — the instrument considered this and removed it before
execution. It is not an assertion of absence (rule 7) and not a termination.

**Also needed and currently invented per-reader:** a test for *which* strikes earn a
row. One reader's — *a strike gets a row when the struck text, if left standing, would
have changed what the instrument does* — is the best offered and would have produced
one row here rather than three. Adopt it, and say so, or readers will keep inventing
their own and the counts will keep diverging.

### 2. `time` holds one date and a covenant has two — *four of five*

Every restriction in this deed expires **1915-01-01**, stated once on page 2. The
whole covenant scheme runs three years and eight months. Creation goes in `time`; the
expiry has nowhere to live but prose.

One reader: *"if a table omits that, everything else it says about this parcel is
wrong after 1915."*

**Add `until` beside `time`.** Also add it to the labelled date block, which currently
has three roles and none is expiry.

### 3. Splitting policy is unstated — *three of five*

Two readers following the framework exactly can differ by a factor of two on row count
while agreeing about everything. This is the single largest source of noise in the
council's input.

**State the rule: one row per operative act, not per constraint and not per
citation** — and give the two worked cases from this document (the $2,000/$3,000
thresholds; the twenty prohibited trades).

### 4. The recording act and the return-to party fit none of the eleven — *three of five*

Rule 1 exiles the recording *date* to the brief and silently takes three other facts
with it: the **9 a.m. time** (which fixes same-day priority), the registry's own act,
and *"C. Livingston Bostwick, for Wood, Harmon & Co."* — the only appearance of the
grantor's agent and address.

**Rules 1 and 5 of v3 contradict each other here**, and one reader proved it: rule 5
names the return-to party as worth catching; rule 1, obeyed literally, deletes the row
that would hold it. An early round already lost party addresses as an undetected error.
This is the same hole one page over.

**Resolve the contradiction.** Either a twelfth function for registry acts, or an
explicit registry lane below the table that the citation rule still reaches.

### 5. `parties: from → to` breaks on ASSERT rows — *two of five*

Eight to ten rows per table are assertions. "Never an undirected list" is right for a
transfer and meaningless for *"the grantor is a New York corporation."* Readers
overloaded the arrow — one as asserter → recipient, one as name → capacity. **Two
different relations wearing the same notation is exactly what reads as agreement
between readers who meant different things.**

### 6. `where` assumes the row is about the subject parcel — *two of five*

Two events are placed **precisely** on land this deed does not convey — *"any part of
South New York, Addition Number Four"*, and the lots on four named streets. Blank is
false; a BBL does not exist. Both readers wrote prose the deterministic BBL check
cannot see.

## Accepted at the top rank — this is a PRECONDITION, not a seventh item

> **Re-ranked after review.** This was first filed below the two-confirmation
> findings as "single source." That was wrong, and the reason matters more than the
> correction.
>
> **It is not an independent proposal. It is the precondition for the unanimous
> one.** `STRUCK` carries five confirmations — but a `STRUCK` mode whose evidence is
> a character citation is a mode you can *assert* and never *verify*. The quotation
> of struck words is byte-identical to the quotation of live words, so nothing
> downstream can distinguish a correct `STRUCK` from a fabricated one.
>
> Shipping finding 1 without this adds **a field no checker can ever falsify** —
> which, in a round whose other theme is that verifiers keep shipping broken, is the
> worst possible thing to add.
>
> The skeptic's question is therefore not *"does a single-source change carry enough
> evidence?"* but *"can finding 1 be implemented without it?"* It cannot.

### 7. A citation cannot prove a crossing-out

The evidence for a struck clause is **a line drawn through text**. A quotation of
struck words is indistinguishable from a quotation of live words, so the fact that
matters survives only in `terms`, where `tablecheck.py` cannot reach it.

More generally: **the entire lot-designation finding rests on the shape of a stroke,
and the citation column carries only characters.** On this document that is the
difference between conveying two lots and conveying none.

### The general form, because it will keep recurring

**A citation format bounds the class of claims it can support.**

Ours encodes characters. It can therefore support claims about *which words are on
the page* and, in principle, **nothing about how they are marked**. That is not a
tooling gap better OCR closes — **marks are not characters.** Any finding whose
evidence is a mark needs a citation carrying geometry.

**Minimum viable citation:** page · rect in normalised page coordinates · mark type
from `plain | struck | inserted | flourish | marginal | uncertain`. Keep the character
span alongside — it remains the cheap faithfulness check.

And it composes with the bound this document established: **mark *type* is measurable**
(the ink-run method settled flourish-vs-strike with numbers), **mark *order* is not**
(bitonal scans lose stroke sequence). So `struck` is a citable claim; *struck-before-
execution* is permanently `uncertain` on these scans — which is exactly the third
value finding 1 requires.

This also relocates a defect in the verification design rather than merely
under-specifying it: a stage that verifies extraction against a **transcription**
cannot flag struck text at all, because struck text produces no character-level
anomaly. The stage that would settle these cases never receives them. The interface
between the stages was wrong.

## Accepted — a discipline, demonstrated rather than argued

### 8. Verify against the artifact, never against the brief

One reader, told by the orchestrator that a checker defect existed, **checked the live
tool instead of taking the claim** — found another reader had already proved it and
the fix had landed, and withdrew its own finding before filing.

This must be a rule, not a happy accident. **A reader working from the orchestrator's
summary replicates the orchestrator's errors instead of reading the page**, and the
round's independence quietly degrades into five readings of my brief. The orchestrator
was wrong three times this session; every one was caught by someone who went to the
source.

Earned by demonstration: one reader did it, the others did not.

## Rejected

**Nothing.** No proposal this round failed the "names the document" test.

Note for the skeptic: item 7 has one source but is **not** optional — finding 1 cannot
be implemented without it. Judge it as a precondition, not as a standalone proposal.

## Method note

The council was **not convened as a debate**, deliberately. Four of the six findings
above replicated across blind readers before any of them communicated. Independent
replication is stronger evidence than discussion, and the documented failure of
homogeneous debate — agents abandoning correct lone positions to match a majority —
is a real risk with five same-model readers.

Disagreement is a **localiser**: it says *where* the framework is ambiguous, not *who
is right*. Facts go to measurement. Only genuine representational questions are worth
arguing, and none this round needed it.
