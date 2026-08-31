# C.R.E.D. extraction framework — backup

The ruleset that turns a recorded NYC property document into an **event table**:
one row for every thing the document does, placed in time and on a tax lot.

| file | what it is |
| --- | --- |
| `framework/framework.md` | the framework. One page. Eleven functions with definitions, eight rules, each naming the real document that forced it |
| `framework/ROLES.md` | who reads, who judges, and who is deliberately prevented from doing both |
| `framework/COUNCIL.md` | the protocol run after every document |
| `bin/tablecheck.py` | the checks that need no model — citations, date order, lot agreement, totals, corpus pointers |
| `bin/docpkg.py` | builds the page images from the source PDF at native resolution |

## Why it is this small

The previous version reached 129 KB plus three JSON schemas, a version gate and a
compiler. Across three documents it produced 32 defect reports, almost all of the
form *"the framework has no field for this."* **Not one was a document the models
could not read.** The reading was never the problem.

So: a rule may only enter this file if it names the document that forced it. A
separate skeptic rejects any rule that does not.

## How it is tested

Five extractors read the same document blind under identical instructions, then
convene and challenge each other. Identical instructions are the point — if each
used a different method, a disagreement would be uninterpretable. Same framework,
same method, same model means any disagreement is a clean signal that **the
framework underdetermined the answer.**

Agreement earns no credit. In an early round two extractors on different model
families made two identical errors and neither caught either one.

## What no arrangement of models catches

If the eleven functions miss a category of real-world event, nothing here finds it —
every checker works from the same list. The backstops are arithmetic and calendar
order, chain consistency across documents (a misread grantor breaks a chain and
announces itself without anyone knowing the right answer), and a human on a sample.
