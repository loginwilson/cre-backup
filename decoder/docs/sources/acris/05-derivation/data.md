# ACRIS · DERIVATION — THE DATA

## ⚠ THIS PHASE HAS NO DATA DESIGN YET. THAT IS THE ACCURATE STATE.

**TABLE CHANGE 2026-08-20 (Bootcamp r49):** event rows carry `doc_type`
in PROVENANCE. Contract unchanged; per-type traceability and the
type->function ledger become derivable outputs.

Derivation has been decided **architecturally** and not at all **operationally**.
Writing table shapes, column lists or refresh strategies here would be inventing
calibrations — a value with no measurement behind it, which is the one thing this
documentation exists to prevent.

What is settled is short, and all of it is *why*, not *how*.

## WHAT IS SETTLED

**Store: Supabase.** Derived values are precomputed and written to the database.

**Why derivation is its own phase** — Login, 2026-08-14: *"the reason derivation
exists is because it makes apps easier to do than having the app calc the data to
display, the data is pre calc in the database for the app to just worry on ui/ux.
not to mention it can be made dynamic in how the database calcs and pulls
derivations based on the app we develop in the end."*

⚠ **A derivation is a VALUE, not a product.** A number computable from the
resolved graph and traceable back to evidence. The same derived value feeds
different products for different audiences — the moment one is shaped for a
single screen it has stopped being a derivation and become application logic in
the wrong layer.

⚠ **ONE DEFINITION PER VALUE.** "Varying" is the competitor failure mode this
whole system exists to beat, and it is what happens when each screen computes its
own $/BSF. One definition, in the database, traceable to events.

⚠ **Every derived value must carry its provenance forward.** It inherits the
worst grade of the evidence beneath it. A confident number resting on a
`single_channel` read is not a confident number, and the only place that can be
known is here.

## WHAT IS NOT DECIDED

- table shapes, keys, grain
- how values are recomputed when upstream events change — full rebuild, delta,
  or triggered
- which values exist at all, beyond the ones the app work has already needed
- how a derivation's provenance grade is represented alongside it

These get written when they are **measured**, not when they are guessed.

## WHAT ALREADY EXISTS AND SHOULD BE READ FIRST

Real derivation work has been done in the territory app and its reasoning is
recorded — `$/BSF` as a normalization rather than a measurement, the buildout
comparison, the viability rules. That is the closest thing to a worked example
and it belongs in the conversation when this phase is designed for real.

⚠ **But it was built app-first, not decoder-first.** Reading it as a template
would import exactly the coupling this phase exists to remove.
