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
reading.

| reader | method | catches what the others miss |
| --- | --- | --- |
| **1 Sequential** | page 1 to N, as a person reads | narrative flow; what the document is *for*; clauses that modify earlier clauses |
| **2 Function sweep** | one function across all pages, then the next | the party wall inside a surveyor's third boundary course |
| **3 Index-first** | read the registry row, then hunt the document for each field | what the index gets wrong, and what it omits |
| **4 Strict** | nothing is an event without an operative verb and a named party | over-emission — the sixteen fee rows a cover page can manufacture |
| **5 Inclusive** | every clause does something until proven otherwise | omission — a covenant expiry buried in one sentence |

Readers 4 and 5 disagree **by construction**. That is the design working: their
splits land on the framework's open boundary questions instead of surfacing by luck.

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
