# CASE LIBRARY — the rules, and the eval that proves a model can apply them

**Every document worked by hand produces a case file.** The method is in
`docs/sources/acris/03-extraction/workflow.md` → *THE CASE METHOD*.

⚠ **THIS DIRECTORY IS TWO THINGS AT ONCE, AND THE SECOND IS THE POINT.**

1. the **rules ledger** — what each document taught, tiered by who enforces it
2. the **evaluation set** — every case is a document with a recorded answer

The plan is to hand these rules to an open-weight reasoner and run extraction in parallel.
*How do we know when it is good enough?* **Not from benchmark claims — by replaying this
library and diffing against the recorded answer.** Without it, "the open weight is ready" is
a guess. With it, it is a number with a denominator.

---

## THE CASES

| document | type | pages | what it established |
|---|---|---|---|
| [2016081800161001](2016081800161001.md) | MORTGAGE (gap) | 22 | ceiling ≠ balance · event collapse · cross-collateral posting · agent ≠ creditor |
| [2020020400712009](2020020400712009.md) | MORTGAGE AND CONSOLIDATION | 42 | **two documents in one file** · consolidation = replacement · face vs balance · tax-stamp arbiter · geometry needs calibration |
| [FT_4070002230107](FT_4070002230107.md) | **indexed `LEAS`, actually a TERMINATION** | 11 | ⚠ **doc_type carries no SIGN** · first `terminates` · first account CLOSED · `$1` is a component · survival ≠ encumbrance · terms EXPIRE · **microfilm OCRs faster** |

**Needs backfill** (worked 2026-08-17 before the standard existed — re-run and write up):

| document | type | why it matters |
|---|---|---|
| the ZLDA/easement | EASEMENT | a **6,199 SF ENVELOPE** quantity inside a document typed EASEMENT. The type is a hint, never the contract |
| the 2016 CEMA | AGMT (CEMA) | conservation exact to the penny; the exemption-255 mechanism |

---

## THE RULES LEDGER

⚠ **Tier every rule by who enforces it.** The cheapest tier that can enforce a rule is the
tier that must. Handing the reasoner work a regex does is paying inference for arithmetic.

### CODE — deterministic, free at corpus scale

| rule | check | case |
|---|---|---|
| Frame count vs cover claim | `len(frames) > cover.page_count` ⇒ scan for a second cover page | 2020…009 |
| Consolidation closure | `prior_balance + new_advance == principal` | 2020…009 |
| Tax closure | components vs `ceil(taxable/100)*100 × statutory rate` | 2020…009 |
| **Taxable rounds UP to next $100** | `ceil(taxable/100)*100` | 2020…009 |
| Restatement authority | source instrument > cover/index > later schedule | 2020…009 |
| Geometry calibration | never report DTM polygon area absolutely (**median +3.5%**, 38% within ±3% over 2,057 lots) | 2020…009 |
| Never date from the document ID | ID prefix ≠ recorded date | 2016…001 |
| Ceiling ≠ balance | `"up to"` / `"maximum … secured"` ⇒ `bound: upper`, account carries **no balance** | 2016…001 |
| Collapse events sharing one cap | same date + parties + subject + cap ⇒ one event | 2016…001 |
| Cross-collateral posting | multi-parcel + joint & several ⇒ full to each, `shared`, **never summed** | 2016…001 |
| Account stays open on evidence | only recordable exits ⇒ no decay, no expiry | 2016…001 |
| **⚠ `doc_type` carries no SIGN** | never derive open/close from the type — `LEAS` covers create, amend **and terminate**. A sign error posts a phantom 40-year leasehold | FT_407… |
| Reel/page and recorded date from the INDEX, never the image | `master.reel_nbr` · `reel_pg` · `recorded_datetime` | stamp split 2160/2100; OCR date `1996` vs truth **1986** — a 10-year error | FT_407… |
| Repeated stamps self-validate | same value ≥3× outranks one degraded read | FT_407… |
| `document_amt` is not the quantity | index `0` vs instrument **$7,500,000** | FT_407… |
| A term needs an EXPIRY field | without it a dead covenant encumbers forever (expired 1990-05-31) | FT_407… |
| FT_ microfilm is **not** the slow half | **3.9 s/page** vs 4.9–5.3 modern | FT_407… |
| ⚠ Exemption before arithmetic | the 1.5%/2.8% check **falsely flags every exempt document** — read the exemption field first | prior ledger |

### MODEL — needs a reader

| rule | case |
|---|---|
| The operative clause locates the event; covenants and recitals are terms (35 sections → 3 events) | 2016…001 |
| A boilerplate mention is not an event — *"air rights and development rights"* as collateral with **no SF quantity**. The quantity decides, not the noun | 2016…001 |
| Cross-collateralization has **no clause** — it is readable only from the shape of the grant | 2016…001 |
| `as administrative agent` ⇒ role AGENT, principal absent (MERS-shaped) | 2016…001 |
| **Face vs balance is a qualifier**: *"original principal aggregate amount"* vs *"on which there is now owing"* | 2020…009 |
| A consolidation **replaces**; a mortgage **adds**. Read which before posting | 2020…009 |
| An omnibus granting clause is not a title transfer — *"sold, aliened, enfeoffed, conveyed"* is NY mortgage drafting | both |
| A struck-and-rewritten figure may swap **fields**, not values | 2020…009 |

### HUMAN — exception queue

| trigger | case |
|---|---|
| A closure test fails and the document is not obviously wrong | 2020…009 — one root error (face used where balance belonged), hand-corrected in ¶3, never in ¶1 |
| A legal description contradicts the cover on block/lot | 2016…001 — `1201` vs `1206`, settled on abutting geometry |
| ⚠ **The tax stamp is the arbiter** — the only number a third party verified and banked | 2020…009 |

---

## STANDING PRINCIPLES

- **Separate the slots and most "contradictions" evaporate.** They are field-assignment
  errors, not value disagreements.
- **`absent` / `unresolved` / `unread` are three different facts.** An `absent` filed as
  `unresolved` sends someone hunting a document that will never exist; an `unread` filed as
  `absent` retires a field a better reader would close.
- **A rejected claim stays attached to the event.** The error is really on the paper and
  anyone reading the instrument will hit it.
- **Two copies of one drafted paragraph are one witness, not two.**
- **⚠ OPENINGS DECAY, CLOSURES DO NOT.** A lone 1986 *termination* supports present-tense
  claims in 2026; a lone 1986 *mortgage* supports almost none. Weight closures far above
  openings when deriving current state from thin evidence.
- **⚠ DERIVATION HAPPENS TWICE.** Derivation-of-extraction (*what does this document say
  about the world*) needs **no chain** and ships on every document on day one.
  Derivation-of-resolution (*what is true now*) usually needs one.
- **A document with no lineage still emits the shape of its chain** — recitals are pointers,
  and every legal description is the parcel's geometry at a moment. **Lineage is the walk's
  output, not its prerequisite.**
- **The derivations worth the most break the easiest.** *"This lot has a mortgage"* survives
  any upstream error and is worth nothing. *"This owner is over-levered"* is worth a phone
  call and dies to a single mis-posting.

---

## EVAL PROTOCOL — how to decide the open weight is ready

Do **not** score on transcription completeness. **Score against the tables.**

For each case, the candidate model gets the raw document and the rules, and must produce:

| # | scored on | pass condition |
|---|---|---|
| 1 | the five axes | every quantity matches value **and** `bound`; no extra events; no missed events |
| 2 | closure tests | every CODE-tier check that applies **runs and passes** |
| 3 | resolution decisions | same collapse, same rejected claims, same account movement |
| 4 | empty states | `absent` / `unresolved` / `unread` assigned correctly — this is where a weak model fabricates |
| 5 | derivation | a reader who has not seen the document reaches the same conclusion |

⚠ **Report the denominator every time.** "Passed the case library" means nothing without
*how many cases, of which document types*. A reader proven on mortgages is not proven on
easements — the ZLDA case exists precisely because type predicts nothing.

⚠ **Back-check on every new rule.** When a case teaches something new, **re-run it over
every earlier case.** Prior cases were judged by rules that predate the lesson, so they look
cleanest exactly where they are most likely wrong.
