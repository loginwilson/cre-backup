# ACRIS · PHASE 4 — RESOLUTION

**Status: contract built, claims partly built, index verifier NOT built.**

## GOAL

Move from perception to reasoning. Extraction settled *what the page says*;
resolution determines *what happened to the asset*.

```
accepted text → CLAIMS → EVENTS → roles + direction + effect
              → FUNCTIONAL LINEAGES → chronology + function → STATE
```

## ⚠ ONE GRAPH, TWO TRAVERSALS — NOT TWO DATASETS

- **Chronology** — date primary, function is an attribute. *"What happened to
  this property over time?"*
- **Functional lineage** — function primary, date is an attribute. *"How did this
  development-rights / debt / ownership position evolve?"*

Duplicating events to serve both views guarantees they drift, and a parcel
history that disagrees with its own financing history is worse than either alone.

## ⚠ DIRECTION IS RECORDED, NEVER INFERRED

`parcels: [A, B]` has already destroyed the thing that matters. One event writes
**two** directional effects, so each side reads correctly from its own vantage:

```
participant   Lot 17    sender      −42,500 BSF
participant   Lot 22    receiver    +42,500 BSF
```

Two participants is the *simplest* case, not the general one — a zoning lot
merger may bind five lots, and a transfer may draw from several granting parcels.
Effect is not limited to floor area: the same instrument carries consideration,
execution and recording dates, a governing agreement, often a term.

⚠ **The ratio a broker wants — $ per transferred buildable SF — is not stored.**
It is *derived* from two quantities the event already holds. That is phase 5's
job, not this one.

## ⚠ THIS IS WHAT TRANSCRIPTION SCORING CANNOT SEE

An engine that emits both `SPRINGFIELD EQUITIES LTD` and `Peninsula National
Bank` scores 2/2 whether or not it knows which is mortgagor. **Swap them and the
debt lineage inverts — borrower becomes lender — with full provenance and perfect
citations.** Transcription at 96% with roles inverted is worse than 90% with
roles right, which is why role assignment is validated *here* rather than trusted
from the extractor.

**Demonstrated, 2026-08-13:** the fused run asserted a mortgagee of `articles of
personal property now or hereafter attached to` and graded it
`image_agreement — settled`. Both channels genuinely read those characters. The
defect was structural: `and (.{3,160}?),? the Mortgagee` was unanchored and the
phrase occurs ~19 more times in one 1967 mortgage's covenant boilerplate.
**A second channel checks characters; only clause STRUCTURE checks meaning.**

⚠ And the label itself was damaged: that recital ends `The MORTGAGE, WITNESSETH`
— Qwen and Paddle *independently* dropped the final E of MORTGAGEE. **Two
channels agreeing is not two channels being right when the failure is
legible-but-wrong.**

## CALIBRATIONS

| setting | where | value | measured | failure if wrong |
|---|---|---|---|---|
| provenance grades | `canonical.py:GRADE_ORDER` | image_agreement > order_artifact > disputed > single_channel | worst-grade-wins over a span | averaging grades makes a 90%-agreed name with an invented tail look 90% established |
| order safety | `canonical.py` | `order_safe` only when fully agreed | role is assigned by WORD ORDER; `order_artifact` means the channels disagreed on position | a role claim over an order-unsettled span can invert silently |
| recital match | `claims.py:RECITAL` | one sentence, both roles | matching roles independently let take-first-match win on boilerplate | refuse on >1 candidate; ambiguity is a result |
| same-clause window | `claims.py:SAME_CLAUSE` | 400 chars | beyond it the label is boilerplate, not a recital | a free page search returns 19 false mortgagees |
| char-weighted settled | measured 2026-08-13 | digital 86.0% · film 80.2% · **book 50.8%** | different denominator from the 86.6% CRITICAL-artifact score | conflating the two overstates book badly |

## RULES

1. **Refusing is a result.** A mortgage with one identified side cannot be
   written as an event — emitting nothing and saying why is correct; a
   half-event gives a lineage a lender that does not exist.
2. **The event inherits its weakest ingredient.** One unconfirmed party name
   makes the whole record a lead, because the record is used as a unit.
3. **Leads are printed as `LEAD`, not as `EVENT` with a footnote.** Burying
   "unresolved" in a field is how it stops being read.
4. **Every value carries how it was established** — `image` / `index` /
   `escalation` / `unresolved`. Collapsing these is how a $0 microfilm mortgage
   becomes a fact.
5. **An unresolved quantity is not zero.** Unknowns are counted and reported
   beside the total.
6. **A fact without `document_id` + `page` refuses to exist.**
7. **MERS is a NOMINEE, not a lender.** Treating it as mortgagee poisons the
   financing chain corpus-wide.

## BUILT / UNWIRED / UNBUILT

- **Built:** `event.py` (the contract) · `claims.py` (regex claims, deliberately
  a placeholder for a model) · `canonical.py` (provenance bridge)
- **Unbuilt and next:** **the index verifier** — PARTIES carries `party_type` for
  every document and is now on disk. It is the one check that catches role
  inversion, and nothing consumes it yet.
- **Entity resolution — DESIGNED AND WRITTEN, UNWIRED, UNVERIFIED.** ⚠ I called
  this "unbuilt" twice on 2026-08-14 and was wrong both times; `whats_live.py`'s
  drift check found it. Written 2026-08-05, nothing imports it:
  - `entities.py` (300 lines) — three layers: `observation` (immutable — this
    NAME, in this ROLE, on this LOT, on this DOCUMENT, on this DATE), `entity`
    (**a JOIN, not an edit** — the observation keeps the document's own
    spelling), `timeline` (fold observations in date order; this is what makes
    time linear). A contact is a further fold and deliberately not built here.
  - `roles.py` (188 lines) — controlled vocabulary with `capacity`
    (principal / financial / professional / governmental / fiduciary) and
    `counterpart`, because roles come in pairs. Built as a registry up front
    precisely so one person does not become "attorney", "counsel", "atty" and
    "Esq." and split into four people.
  - `id_strength.py` (107 lines) — identification strength BY DOCUMENT TYPE:
    none → signature → printed_name → addressed → full_contact. A property of
    the type, not the instance, so you reach for the right document instead of
    hunting page by page.

  **Status is "exists", not "works"** — none of it has been run against the
  46.5M-row PARTIES surface. That is the next question, not a rewrite.
- **Open:** the permitted value lists (actions, roles, functions) are being
  settled agentically by running the resolver over real batches and letting it
  propose what it needs, rather than fixed up front.

## PROMOTED DOCS

None re-read yet. `LEDGER_SCHEMA.md`, `LOT49_*.md`, `SIGNATURE_LADDER.md`,
`CONTACT_RESOLUTION.md` are candidates and are **history until confirmed**.

Memory: `project_acris_resolution_model.md` · `project_acris_doctype_decode_rules.md`
