---
name: project_acris_resolution_model
description: "Resolution = ONE event graph with two traversals (chronology vs functional lineage), and direction/role/effect is first-class from day one — which is precisely what transcription scoring cannot see"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7c5a3ccb-a88e-40cd-a587-cc575cf7a400
  modified: 2026-08-14T01:29:01.393Z
---

Login's design for the RESOLUTION stage, settled 2026-08-12. Resolution is the final
sanitization step: canonical text → claims → events → functions/entities/references → graph.

## ONE graph, TWO traversals — not two datasets

- **Chronology** — date primary, function is an attribute. Answers "what happened to this
  property over time."
- **Functional lineage** — function primary, date is an attribute. Answers "how did the
  development-rights position evolve."

Every event carries three coordinates: **TIME · FUNCTION · OBJECT**, where object is the
persistent thing changed (Mortgage #12, ZLDA #7, Development Rights Pool #3, Easement #19).
Lineages resolve into present state by applying state-changing events in order.

## ⚠ DIRECTION IS FIRST-CLASS, NOT INFERRED DOWNSTREAM

A generic `TRANSFER` with `parcels: [Lot17, Lot22]` is not enough. One event writes TWO
directional effects:

```
effects: [
 {parcel: Lot17, role: sending_parcel,   effect: development_rights_decrease, qty: 42500},
 {parcel: Lot22, role: receiving_parcel, effect: development_rights_increase, qty: 42500}]
```

So Lot 17 reads "SENT 42,500 SF → Lot 22" and Lot 22 reads "RECEIVED 42,500 SF ← Lot 17" from
the same event. Every instrument has this polarity: grantor→grantee, borrower/lender,
burdened→benefited, assignor→assignee, releasing→released, fee owner→ground lessee. Events
also link horizontally across functions ("conveyed subject to the 1994 zoning lot agreement"
= ownership event that ASSUMES_OBLIGATION_UNDER a zoning lineage).

Function itself gets granular: establishment · availability · transfer (sending/receiving) ·
reservation · allocation · use · modification · reversion · termination.

## ⚠ WHAT THIS BREAKS IN THE CURRENT BENCH — the reason to record it

Every OCR/VLM number measured so far scores whether a fact was **SURFACED** (did the string
appear anywhere in the output). **It cannot see role assignment.** The 1967 book document
carries `SPRINGFIELD EQUITIES LTD` and `Peninsula National Bank`; an engine that emits both
scores 2/2 whether or not it knows which is mortgagor and which is mortgagee. Swap them and
the debt throughline inverts — borrower becomes lender — and the resolver builds a confident,
fully-cited, backwards lineage.

**Transcription at 96% with roles inverted is worse than 90% with roles right.** So
`bakeoff/extract.py` (built, never run) is now the highest-value untested thing, above
squeezing more points out of transcription. See [[project_acris_ocr_stack]],
[[project_acris_doctype_decode_rules]], [[project_bkrea_debt_throughline]].

## ⚠ PROVENANCE CANNOT CATCH A ROLE MISASSIGNMENT — demonstrated 2026-08-13

`resolve/canonical.py` (new) bridges the fused evidence into `claims.py`, so every claim is
graded by the provenance of the exact span its regex matched instead of the old hardcoded
`resolved_from="image"`. Four grades, worst-wins over a span:
`image_agreement` (settled) · `order_artifact` (both channels read the tokens, DIFFERENT
position — content corroborated, ORDER is not) · `disputed` · `single_channel`.
Character-weighted: digital 86.0% settled, film 80.2%, **book only 50.8%** (31.3% of its
characters were read by one channel alone). Don't confuse these with the 86.6% accepted in
[[project_acris_extraction_resolver]] — that is CRITICAL-artifact weighted, a different
denominator.

The first fused run asserted a mortgagee of `articles of personal property now or hereafter
attached to` and graded it **image_agreement — settled**, because both channels genuinely
read those characters. The defect was never transcription: `and (.{3,160}?),? the Mortgagee`
was unanchored and `the Mortgagee` occurs ~19 more times in one 1967 mortgage's covenant
boilerplate, so take-the-first-match won. **A second channel checks characters; only clause
STRUCTURE checks meaning.** Fix: match the recital as ONE sentence assigning both roles
(`between X, the MORTGAGOR, and Y ...`), refuse on >1 candidate, and bound any fallback to
400 chars of the mortgagor label.

⚠ **The label itself is damaged and both engines damage it identically.** That recital ends
`The MORTGAGE, WITNESSETH` — Qwen AND Paddle independently dropped the final E of MORTGAGEE.
Two channels agreeing is not two channels being right when the failure is legible-but-wrong.
Match `MORTGAGEE?` and anchor on `WITNESSETH`, which is era-stable.

**Fusion first paid off semantically here:** on the 1967 book document Qwen alone REFUSES
(cannot find the recital), Paddle alone finds it as `SPRINGFIELD EQUITIES LTD. a corpotation`
with the year misread 1968→1861, and FUSED emits a settled event — Winnicki (mortgagor) →
Springfield Equities (mortgagee), $21,000, 1966. Neither engine alone produces it.
Events now split into `_events.json` (established) vs `_leads.json` (unsettled, printed as
`LEAD` not `EVENT` — burying "unresolved" in a field is how it stops being read).
