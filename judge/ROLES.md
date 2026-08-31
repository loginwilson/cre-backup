# Roles

## The finding this is built on

**Same model, different method diverges as much as different model, same method.**

Measured here, small sample, but consistent. Across two documents, Claude and GPT
— different families, no contact — split four times. Across two documents, two
*Claude* readings split three times: an unlabelled `16.00` typed as a fee, an
internal contradiction one of them invented, and copperplate lead-in flourishes
read as strike-throughs.

What differed in the second case was not the model. It was reading order, zoom
level, and entry point.

And the thing cross-family diversity was supposed to buy did not materialise: in an
early round, Claude and GPT made **two identical errors** — missing party addresses,
and no lane for illegible text — and neither caught either.

So: differentiate readers by **method**, and run them all on one model with a
predictable plan. A reader that can drop out mid-round is worse than no reader,
because then no two rounds have the same composition and nothing can be compared.

## The readers

All Claude Opus 5. Blind — each workspace contains only its own folder while
reading. **Identical instructions, deliberately.**

> ⚠ **This section previously assigned each reader a different method** —
> sequential, function sweep, index-first, strict, inclusive. That is no longer the
> design, and it sat here contradicting practice for a full round. It is recorded
> rather than deleted because the reason for the change matters.

**Why identical.** If five readers use five methods and diverge, the divergence is
uninterpretable: it could be framework ambiguity or it could be method. With
identical instructions, **every divergence is a fact about the framework** — it
localises exactly where the instructions admit two readings. Divergence becomes a
measurement instead of noise.

It also passed the field test. On `RC_1598772`, five identical readers produced
16 / 26 / 27 / 27 / 29 rows and the spread was almost entirely **splitting policy** —
which is precisely the kind of framework gap this arrangement is meant to expose,
and it would have been unattributable under five different methods.

**What the method diversity used to buy is now bought elsewhere.** The function
sweep became a separate coverage probe, run *after* the readers seal so it cannot
contaminate them; strict-versus-inclusive became the splitting rule, stated in the
schema rather than embodied in two disagreeing readers.

> *Grounded in the finding at the top of this file: same model, different method
> diverges as much as different model, same method. If method alone produces
> divergence, then method must be held constant for divergence to mean anything.*

## Convening

Blind while reading, open while arguing.

When every reader has sealed a table, the workspaces widen so each can read the
others' **tables** — not the orchestrator's summary of them. They argue their own
reading, because they did it. Before the next document, the workspaces narrow again.

The orchestrator is out of the middle for this step, deliberately.

### Two rules that stop the council collapsing into agreement

**Tables only, never reasoning.** Reasoning anchors. A conclusion has to be
re-derived.

**Agreement must be paid for.** For every row a reader accepts, it states what it
independently checked — not *"I agree with E4"* but *"E4: re-read page 2, the quote
is the whole operative clause."* Agreeing then costs the same as disagreeing, which
removes the only reason to nod.

**Framing:** the challenge round is not *"compare tables."* It is **"this table is
wrong somewhere — find it."** Asked to verify, a model confirms. Asked to refute, it
looks.

## Not everything is a debate

| kind | question | who settles it |
| --- | --- | --- |
| **factual** | what does the page say? | **referee** — has the images and the zoom tool, sees the readings anonymised, made no claim |
| **judgment** | how should we represent this? | **the council** |

About two-thirds of divergences so far have been factual. The flourish-vs-strike
dispute was settled by zooming to 900 dpi in under a minute; arguing it would have
produced two confident opinions and no answer.

## The separations

**The orchestrator's reading is not ground truth.** It is one more claim, filed in
`loop/claims/`, competing on equal terms. There is no answer key. This is the most
important line here: the orchestrator was wrong three times in two hours, and each
time was caught only because a reader happened to disagree.

**The referee does not know who said what.** Claims arrive anonymised and shuffled;
its workspace excludes every reader folder. Authority bias is the specific way an
orchestrator corrupts a record.

**The skeptic does not write rules.** One job: reject any framework rule that does
not name the document that forced it. The author of a rule is the worst judge of
whether it is needed.

**Selection is published, not delegated.** The coverage map is readable. Selection
bias is real but it is the least corrupting failure, because it is visible.

## The overlap kept on purpose

Readers criticise the framework while using it. That is the highest-value signal the
system produces — every framework finding so far came from the friction of actually
filling a table. A critic who has not extracted produces theory.

## Binding on everyone

1. **Every row carries the quote that proves it.** No citation is a hallucination,
   whoever wrote it. `bin/tablecheck.py` enforces this.
2. **A labelled date line above every table** — `instrument:`, `acknowledged:`,
   `recorded:`, `UNKNOWN` where unstated. The checker previously tried to parse
   dates out of prose, assigned one date to all three roles, and mistook a 1907
   survey-filing date for a recording date. Structure at the source, not parsing at
   the destination.
3. **Agreement earns no credit.** Disagreement is investigated; agreement is not
   evidence.
4. **A framework rule must name the document that forced it.** v2 reached 129 KB by
   answering questions no document had asked.
5. **"I cannot tell" is a valid answer** and is worth more than a confident guess.

## What no arrangement of models can catch

If the eleven functions miss a category of real-world event, nothing here finds it —
every checker works from the same list. That needs a person who knows property law
reading the function table and asking what is absent.

The non-model layers are the real backstop: arithmetic and calendar order
(`bin/tablecheck.py`), chain consistency across documents (a misread grantor breaks
a chain and announces itself without anyone knowing the right answer), and a human
on a sample large enough to put a number on the error rate.
