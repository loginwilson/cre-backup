# ACRIS · PHASE 5 — DERIVATION

**Status: not started.** Depends on resolution producing an event graph.

## GOAL

Turn the resolved event graph into **stored values** the application can read
directly.

## ⚠ WHY THIS IS ITS OWN PHASE — THE REASON IS ARCHITECTURAL, NOT TIDINESS

Login, 2026-08-14: *"the reason derivation exists is because it makes apps easier
to do than having the app calc the data to display, the data is pre calc in the
database for the app to just worry on ui/ux."*

**The app must never compute the number it displays.** Every derived value is
calculated once, written to the database, and traced back to the evidence that
produced it. The application reads it and renders it.

That buys four things:

1. **The app is only UI/UX.** No business logic in the client, no formula drift
   between two screens that claim to show the same figure.
2. **One definition per value.** `$/BSF` is computed in exactly one place. Two
   surfaces cannot disagree about what it means.
3. **Traceability survives.** A stored value carries the events it came from, so
   "why is this number what it is" is answerable from the row, not by re-running
   a calculation nobody kept.
4. **It stays dynamic.** How the database computes and serves derivations can be
   reshaped for whatever the application turns out to need — the resolution layer
   underneath does not move. *"it can be made dynamic in how the database calcs
   and pulls derivations based on the app we develop in the end."*

⚠ **A derivation is a value, not a product.** A number, term, classification or
set computed from the resolved graph and traceable to evidence. The same value
feeds different products for different audiences. The moment a derivation is
shaped for one screen it stops being a derivation and becomes application logic
in the wrong layer.

⚠ **Derivations consume resolved truth, never raw documents.** If a derivation
needs to re-read a document, resolution is incomplete — fix it there. A
derivation that reaches back into source material re-introduces every extraction
uncertainty the evidence record was built to settle.

## THE VALUES (from the charter)

- development-rights balance: sent, received, used, remaining
- price metrics: $/SF, $/BSF, $/unit
- comparable sets: sales, rentals, land, ground leases — filtered by function and date
- active debt, encumbrances and obligations as of a given date
- ownership and contact records with counterparty history
- parcel evolution: assemblage, subdivision, lineage across tax-lot changes
- residual land value and development feasibility inputs
- construction and development status from filings and milestones
- opportunity, distress and refinancing signals, **with the inputs that produced them**

⚠ **Some derivations need sources beyond recorded property data** — construction
cost, rents, market conditions. Those enter as their own sources through phases
1–4; they do not get shortcut into this layer.

## RULES

1. **Computed once, stored, traced.** Never computed at request time.
2. **A derivation must name its inputs.** A signal without the inputs that
   produced it is not checkable and will not be trusted twice.
3. **Normalisation is not measurement.** `$/BSF` is a *normalisation* of a price
   by an area — if either input is unknown the ratio is unknown, not zero.
4. **An unknown quantity is not zero.** Summing a missing SF figure as 0 produces
   a confident wrong balance. Unknowns are counted and reported beside the total.
   (`event.py:state` already does this — carry the same discipline up.)
5. **Date-scope every value that can change.** "Active debt" is meaningless
   without "as of". A derived value with no as-of date silently means "whenever
   this last ran".

## CALIBRATIONS

None yet — this phase has not run. When it does, every threshold that decides a
*classification* (what counts as underbuilt, distressed, comparable) is a
calibration and needs a measurement, not an opinion.

## BUILT / UNWIRED / UNBUILT

- **Unbuilt:** all of it.
- Prior art worth re-reading when this starts: the BKREA app already derives
  comparables, buildout and $/BSF from PLUTO + DOF. Those definitions are
  candidates to lift, **not to assume** — they were built against a different
  data layer.

## PROMOTED DOCS

None. `ENRICHMENT.md`, `RULE_APPLIED_COMPARABLES.md`, `DEVELOPMENT_INVENTORY.md`
are candidates and are **history until re-read**.
