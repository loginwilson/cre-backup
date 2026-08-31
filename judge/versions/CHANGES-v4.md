# v3 → v4

Source: `framework/RULING-RC_1598772.md`.

All from `RC_1598772` (1911 Richmond deed), five blind readers, identical
instructions, no contact. **Confirmations are independent** — they replicated before
any reader saw another's table, which is stronger evidence than a discussion between
five instances of the same model would have produced.

| change | v4 rule | forced by | confirmed |
| --- | --- | --- | --- |
| citations carry **geometry and mark type** | 1 | a citation of struck words is byte-identical to a citation of live words | **precondition** |
| new mode **`STRUCK`** | 2 | three clauses ruled out in ink; no existing mode fits | 5 of 5 |
| new column **`until`** | table | every covenant expires 1915-01-01; `time` holds one date | 4 of 5 |
| **splitting policy** stated | 3 | identical readings produced 16 / 26 / 27 / 27 / 29 rows | 3 of 5 |
| **registry lane** | 4 | v3 rules 1 and 5 contradicted each other on one page | 3 of 5 |
| the arrow **means one relation** | 6 | readers overloaded `→` with two different relations | 2 of 5 |
| `where` carries **explicit scope** | 7 | two rows placed on land this deed does not convey | 2 of 5 |
| flourishes are not strikes | 8 | the orchestrator read two flourishes as cancellations | 5 of 5 against |
| the document **declines to say** | 9 | *"filed or intended to be filed"* | 1 of 5 |
| **verify the artifact, not the brief** | 14 | one reader checked the live tool instead of taking my claim | demonstrated |

## Why rule 1 is rule 1

`STRUCK` carries five confirmations and citation geometry carries one. Geometry
still ranks above it, because **it is not an independent proposal — it is the
precondition for the unanimous one.**

A `STRUCK` row cited by characters alone is a field you can assert and never
falsify: the quotation of struck words is identical to the quotation of live words,
so nothing downstream distinguishes a correct `STRUCK` from a fabricated one.
Shipping finding 1 without finding 7 would add **the one kind of field no checker
can ever reach** — in a round whose other recurring theme was verifiers shipping
broken while printing confident output.

The general form, because it will recur: **a citation format bounds the class of
claims it can support.** Ours encoded characters, so it could support claims about
which words are on the page and nothing about how they are marked. Marks are not
characters; better OCR does not close it.

## Structural changes, not rule changes

- **The event table gained a column** (`until`) and **a mode** (`STRUCK`). Both are
  additive; a v3 table remains readable as v4 with blanks.
- **The citation column changed shape.** `page + quote` → `page · rect · mark ·
  quote`. This is **not** backward compatible. Every v3 table cites characters only,
  so no v3 table can support a mark-dependent claim, including the RC_1598772
  tables that discovered the problem.
- **The registry lane is new and is not a function.** REGISTRY ACT stays a candidate
  in `UNNAMED-FUNCTIONS.md` until a third document forces it. A lane costs nothing
  to withdraw; a function does. The lane exists because obeying v3 rule 1 literally
  deleted the row that v3 rule 5 said to catch.
- **The labelled date block gained `expires:`.** `bin/tablecheck.py` does not yet
  validate it.

## Deleted

**Nothing.** Every v3 rule still names the document that forced it, so none failed
the test that would justify removing it.

That is not a comfortable result. The file went 9.5 KB → 19.6 KB for eight findings,
and the first draft landed 400 bytes under its own 20 KB cap. **The growth rate is
the thing to watch, not the size** — v2 died at 129 KB by the same mechanism, one
defensible addition at a time. Moving this changelog out of `framework.md` is the
first cut; it will not be the last one needed.

If v5 cannot be written without breaching the cap, the correct response is to delete
a rule, not to raise the cap.

## Not yet done

- no verifier that a cited rect contains the cited text — rule 1 is discipline, not
  guarantee
- no check on `expires:`
- no held-out scored set, so **there is no number saying v4 beats v3**
