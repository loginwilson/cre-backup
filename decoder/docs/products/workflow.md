# ACRIS · PHASE 6 — APPLICATION

**Status: not started here.** The BKREA territory app exists but runs on a
different data layer (PLUTO/DOF/DOB), not on the decoder's resolved graph.

## GOAL

Deliver the intelligence. By this point the difficult data work is done —
application is about **how it reaches the user**, not what it means.

⚠ **The application does not create intelligence. It packages already-resolved,
already-derived intelligence into the most useful experience for one audience.**

## ⚠ THE BOUNDARY THAT MATTERS

The app **reads stored values**. It does not compute them. See
[05-derivation](05-derivation.md) — every number is precalculated in the database
and traceable to evidence, so this layer is only UI/UX.

If a screen needs a number that does not exist as a stored derivation, the answer
is to add the derivation, **never** to compute it in the client. A formula that
lives in a component will disagree with the same formula in another component,
and neither will be traceable.

## ONE DATASET, DIFFERENT PRODUCTS

| audience | product |
|---|---|
| broker | territory map and opportunity radar |
| developer | development pipeline and site history |
| appraiser | comparables and valuation support |
| owner | property history and obligations |
| researcher | chronological and functional event access |
| resident | neighborhood pricing benchmarks by size |

Surfaces named in the charter: opportunity map · development pipeline ·
comparables GIS · TDR market · participant database · parcel evolution
visualizer · live-data underwriting · automated reporting.

## THE DESIGN PROBLEM

**Complex property histories must feel simple.** A parcel that has been
assembled, subdivided, sold, demolished and rebuilt has a genuinely complicated
history, and the user should still be able to read it at a glance. That is the
hard part of this phase — the data work is already finished.

## RULES

1. **No computation in the client.** If it needs deriving, derive it in phase 5.
2. **Every displayed number can name its evidence.** A figure the user cannot
   trace is a figure they will eventually stop trusting.
3. **Never render an unknown as zero.** A missing quantity is missing; showing
   `0 SF` or `$0` manufactures a fact. (This has already bitten the BKREA app —
   `NOMINAL/PARTIAL` deeds now surface as recorded price with a warning rather
   than a fabricated `$/bsf`.)
4. **The resolution layer stays general.** Do not reshape resolved data to suit
   one screen; that is how a product becomes the only consumer its data can serve.

## PRIOR ART — related but NOT this

The BKREA Territory Intelligence app (`C:\dev\bkrea-territory-intelligence-app`)
already solves much of the UI/UX problem for a broker audience, and its card
grammar, comparables logic and populate engine are worth lifting. **But it runs
on PLUTO/DOF/DOB, not on the decoder's event graph** — treat its definitions as
candidates to re-derive, not as answers to import.

Memory: `project_bkrea_territory_intel.md` · `project_bkrea_dream_card.md` ·
`feedback_bkrea_pull_package_monitor.md`

## PROMOTED DOCS

None. `SITE_TRACKING_APPROACH.md`, `CONTACT_ARCHITECTURE.md` are candidates and
are **history until re-read**.
