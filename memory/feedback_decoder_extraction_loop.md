---
name: feedback_decoder_extraction_loop
description: "The extraction loop and its standing rules — never ask a model for anything derivable (anchors, line numbers), gate every claim on the REGION its anchored line sits in, and re-check each lesson against every earlier round"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7c5a3ccb-a88e-40cd-a587-cc575cf7a400
  modified: 2026-08-17T09:56:11.712Z
---

The loop is OCR → route → extract → score, run repeatedly on the same document until
accuracy stops moving, THEN scale sample, THEN scale doc types. Login, 2026-08-16:
"every lesson must be remembered so we dont forget going forward… we must learn from
each round of testing." Rounds so far and what each one taught:

**⚠ RULE 1 — NEVER ASK THE MODEL FOR ANYTHING YOU CAN DERIVE. Paid for twice.**
Asked the VLM to name the line each value came from: it returned CORRECT values on
FABRICATED anchors (p008 gave block/borough/county/lot/street all = "586" on line 1;
p009 gave every ack field = "769" on line 1). When it does not know a line it answers
`1`. Fix: the VLM returns VALUES ONLY and the anchor is SEARCHED for in code.
Routing survived only because a line NUMBER was its entire answer — nothing else to
get wrong.
**Why:** a model asked for a field will always fill it; absence of knowledge is not
expressible in a required field.
**How to apply:** if the harness can compute it, the harness computes it. Anything
the model must supply should be the smallest possible token, ideally an index into
something we already own.

**⚠ RULE 2 — MAKE THE BAD STATE UNREPRESENTABLE, DON'T DETECT IT.** Region-keyed
placement `{region:[lines]}` let the 4B treat the region list as a CHECKLIST: it
filled all 11 regions rather than leave any empty (70 assignments for 44 lines;
`signature`/`notary` given the SAME line 12). Re-keyed to `{line:region}` →
duplicates 27 → 0, regions 11 → 6, and 35% faster. Same move killed invented text:
the VLM never emits characters, only line numbers.

**⚠ RULE 3 — GATE EVERY CLAIM ON THE REGION ITS ANCHORED LINE SITS IN.** compose()
picked the best-anchored claim, ignored provenance, and built `BBL=1005860768` out of
`block=586 lot=768` — which was the RECORDING STAMP (reel 586, page 768). The real
lot is block 883. It then stamped `resolved: True`. ⚠ Gating on "does the PAGE carry
a legal_description" is TOO LOOSE and did not fix it — p008 has 2 such lines, so the
stamp value still passed. Gate on the line's OWN region.
**Why:** a fabricated subject is worse than no subject; it asserts confidence.

**⚠ RULE 4 — THE MODEL ECHOING THE PROMPT IS NOT EVIDENCE.** One round produced
`mortgagor: "Mortgagor"` (field name), `cross_collateral: "other property also
securing this obligation"` (my own hint), and `rate_type: "not specified"` (sentinel).
Guards for all three cut 57 claims → 34 and turned `borrower` into the correct
`387 P.A.S. ENTERPRISES`. Reject: value == field name, value ⊆ prompt hint, value ∈
sentinel set.

**⚠ RULE 5 — A READER PROVEN ON ONE CORPUS IS NOT PROVEN ON ANOTHER.** `signals` is
`status=proven` in lexicon.MODES on **BSA applications** (97%, 1050/27) — and the
ledger separately records under 10 hits in 23,282 ACRIS clauses. Document-wide argmax
let it win a MORTGAGE 5-2 over `transacts`. Two records of the same fact disagreeing
because the denominator did not travel with the status.
**How to apply:** mode belongs to the OPERATIVE clause (granting_clause / parties),
not a whole-document vote. A covenants section is dense with future-conditional
language (shall / will / upon) that reads as intent but is the TERMS OF A
TRANSACTION that already happened.

**⚠ RULE 6 — A FIELD'S REGION IS A FUNCTION OF THE PAGE, NOT THE FIELD.** `mortgagor`
is `parties` on p001 and `signature` on p009 — same entity, different ROLE. Most of
the 16 "misplacements" in the 71% score were my rigid one-home-per-field map, not the
router. `amount_figs` sits INSIDE the granting clause, so `granting_clause` is a
defensible answer for it. Score the map before blaming the model.

**⚠ RULE 7 — A PAGE IS NOT A ROW; AN EVENT IS.** The first extract emitted page
regions (`recording_stamp`, `parties`, `notary`) — 19 of 44 rows were the reel number
restated once per page. Ten pages of one mortgage are evidence for ONE CAPITAL event
on ONE parcel. See [[project_decoder_function_model]] for the settled shape:
claim → event → account.

**⚠ RULE 8 — A GATE IS ONLY AS GOOD AS THE ROUTER FEEDING IT.** Round 3 tightened the
region gate to the claim's own anchored line and the fabricated `BBL=1005860768`
SURVIVED. Reason: the ROUTER had put the stamp line `586± 768` into
`legal_description` on p008, so `block=586` passed a correct gate legitimately. A
downstream filter cannot repair an upstream mislabel.
**How to apply:** cross-check across pages instead of trusting one. p002 carries 13
legal_description lines and p008 carries 2 — prefer the page where the region
dominates, and treat a `block`/`lot` equal to that document's `reel`/`reel_page` as
suspect by construction.

**⚠ RULE 9 — EVERY GUARD IS A NEW WAY TO LOSE DATA; RE-SCORE AFTER EACH ONE.** The
same round that fixed `notary` (Katbhals → ELLIOTT BAKST) silently DROPPED
`principal_amount` entirely, because the gate demanded granting_clause/amount and the
value anchored elsewhere. Tightening precision cost recall and nothing announced it.
Every guard must report what it rejected, and a rejection count is not a success.

**⚠ THE VLM MUST NOT SUPPLY COORDINATES — OCR OWNS GEOMETRY.** Login proposed the VLM
locate the coordinates of confirmed text in the image. Measured twice, it cannot:
asked for line numbers it answers `1` when unsure. Correct division: OCR produces
boxes (real, from detection), the VLM produces the SEMANTIC VERDICT (which table /
field this text is), and the harness joins value → OCR line → box. The VLM verifies
by reading the image; it never reports where it looked.

**⚠ RULE 10 — A COUNTER SITTING AT ZERO IS A CLAIM TO VERIFY, NOT A RESULT.** The
parcel-key guard was silently DEAD for a full round: written through a shell heredoc,
`\b` inside a non-raw triple-quoted Python string became a literal BACKSPACE (0x08),
so the compiled pattern was `\x08reel\x08|…` and matched nothing. `not_a_parcel_key`
read 0, which is exactly what "nothing to catch" looks like. Read/Edit both HID the
control chars, so the bug was invisible until the bytes were printed with `repr()`.
**How to apply:** never author a regex through a heredoc — write a script file. And
when a new guard reports zero hits, prove it fires on a known-bad input before
believing it.

**⚠ RULE 11 — THE VOCABULARY THAT WORKS IS ON THE LINE, NOT IN THE VALUE.** Every
wrong `block`/`lot` came off a line that announces what it is: `586 761`,
`REEL 586c: 763`, `Northerly side of 27th Street…`. The value `27` is indistinguishable
from a lot number; the LINE containing it is not. Reject `block`/`lot` whose line
matches reel / street / avenue / side of / corner / northerly-southerly-easterly-westerly,
then cross-check the survivors against every reel and reel_page value observed
anywhere in the document (reel_page is PER PAGE — 761/763/764/768/769/770 here).

**⚠ WHERE ROUND 7 LANDED — 7 of 9 core fields correct, and it REFUSES the rest.**
block 883 ✓ · borough Manhattan ✓ · mortgagor 387 P.A.S. ENTERPRISES ✓ · mortgagee
CITIBANK, N.A. ✓ · principal 4,000,000 ✓ · tax_paid 60,000 ✓ (cross-checks:
4,000,000 × 1.5%) · recorded OCT 2 1981 ✓ · **lot = None → BBL unresolved,
missing=['lot']** — every surviving candidate was a reel page, so it declined rather
than fabricating, which is the correct failure.
⚠ `LOT 1` is never extracted at all: the key records it as a left-margin scrawl
`883 / 1` printed on the p010 backer. NEXT FIX: ask the backer for the parcel key as
a PAIR (`block/lot` as printed), not as two independent numeric fields.

**⚠ RULE 12 — OCR DETECTION DROPS SINGLE-CHARACTER VALUES, SO ANCHOR ON THE LABEL.**
The FT backer OCRs `BLOCK` at [974,1510] with `883` beside it, then `LOT` at
[977,1549] with NOTHING beside it — at all four angles. `LOT 1` is one character and
never survives text-region detection, so `lot` was not in the OCR stream and no
ranking could recover it. FIX: ask for the parcel key as a PAIR
(`parcel_key`), require the page to carry the LABELS (`\bblock\b` and `\blot\b`) as
the support test, and let the VLM read the value beside them from the image. New
anchor state `label_anchored`, ranked between `corrected` and `unanchored`.
This is the architecture working as designed: OCR points, the VLM reads.
⚠ Parse BOTH shapes — `BLOCK 883 LOT 1` and bare `883 1` (block is printed above
lot on a backer, so order carries it) — and REFUSE anything that is not exactly two
numbers.

**⚠ RULE 13 — AN ILLUSTRATIVE EXAMPLE MUST NEVER BE A STRING THE DOCUMENT COULD
CONTAIN.** The `parcel_key` hint read "e.g. 'BLOCK 883 LOT 1'". p010 genuinely reads
BLOCK 883 LOT 1, so the echo guard normalised both, found one inside the other, and
threw away the single most correct value in the run. Three rounds of work defeated by
an example I chose. Describe the SHAPE, and strip anything after `e.g.` /
`for example` / `such as` before running the echo comparison.

**⚠ RULE 14 — A GUARD MAY ONLY BE DISABLED BY THE THING THAT GENUINELY SUPERSEDES
IT.** compose() skipped the reel/page cross-check whenever a parcel_key CLAIM
existed rather than when one RESOLVED. Round 9 returned bare `883 1`, the labelled
regex matched nothing, block/lot fell back to guesses, and the disabled cross-check
passed `lot=761` — a reel page. Gate on `pk_resolved`, never on `pk`.

**⚠ ROUND 10 — THE SUBJECT RESOLVES CORRECTLY. `BBL=1008830001` = Manhattan block
883 lot 1, matching the hand key.** Also correct: mortgagor `387 P.A.S. ENTERPRISES`,
mortgagee `CITIBANK, N.A.`, principal `4,000,000`, tax_paid `60,000` (cross-checks at
1.5%), function CAPITAL, notary `ELLIOTT BAKST`. Ten rounds on ONE document, and the
guards now refuse rather than fabricate when they cannot resolve.
⚠ STILL WRONG: `signatory` reads garbled `Katbhals` — `signature → person` is still
genuinely UNREAD · `mode` is empty since mode moved to operative clauses only ·
`recorded` degraded from `OCT 2 1981` to bare `1981` · `interest_rate 6.0%` is
implausible for 1981 (rates were 15-18%) and has no cross-check.

**⚠ STILL OPEN AFTER 3 ROUNDS** (do not re-derive, fix): `principal_amount` reads
50000 where the document says $4,000,000 · `signer_name` and `notary_name` both
return the same garbled `Katbhals`, so `signature → person` stays UNREAD as the
ledger says · `lender` picked up `Sisson Realty` which is the mortgagor's general
partner, not the lender · covenant table is missing ~30 columns the document actually
uses (`rpl291f`, `due_on_sale`, `rent_roll`, `ucc_fs`, `carveout`, `judgment`,
`stock`).

See [[project_acris_extraction_resolver]] for the measured engine/harness facts and
[[feedback_confidence_backcheck]] — when a new trap is found here, re-run it over
every earlier round, because prior rounds were judged by rules that predate the lesson.
