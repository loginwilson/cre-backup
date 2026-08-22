# ACRIS · RESOLUTION — THE DATA

What this phase produces and where it lives. The *how* is in
[workflow.md](workflow.md).

**TABLE CHANGE 2026-08-20 (Bootcamp r49):** event rows carry `doc_type`
in PROVENANCE (raw ACRIS code, from the navigation index). New grouping
dimension for chains: doc_type x function is the measured ledger; a
citation in the nav index's `references[]` panel is a CANDIDATE link this
phase verifies against events.

## STORE: SUPABASE, ENTIRELY

**This is the first phase whose data belongs online in full**, and for a reason
rather than by preference: the whole point of the event graph is that it is
queried two different ways. A filesystem cannot do that. Nothing here is bulk —
it is the distilled result of 10 TB, which is exactly why it fits.

Schema: `decoder` (see `migrations/001_decoder_schema.sql`). `public` becomes a
read-only archive of prior generations; nothing is deleted.

## ⚠ ONE GRAPH, TWO TRAVERSALS — NOT TWO STORES

The single most consequential design decision in this phase.

| traversal | ordered by | answers |
|---|---|---|
| **chronology** | time primary | what happened to this parcel, in order |
| **functional lineage** | function primary | how did this right/obligation get here |

Both read the *same* events. Building two datasets would guarantee they drift,
and the drift would be invisible because each would be internally consistent.

## ⚠ DIRECTION, ROLE AND EFFECT ARE FIRST-CLASS FROM DAY ONE

Not attributes added later. An event records **who did what to whom, and what it
did to each side.** One TDR transfer writes **−SF on the sender and +SF on the
receiver** from a single document. If direction is bolted on afterwards, that
document becomes two unrelated rows and the arithmetic never closes.

⚠ **Transcription scoring structurally CANNOT see a role inversion.** Swap
grantor and grantee and the text scores 100% while the lineage runs backwards.
Only the index channel (`party_type`) catches it. This is why role validation
belongs here as a hard check, not as a quality metric.

## WHAT RESOLUTION JOINS AGAINST — the parcel spine

Events attach to parcels, and the parcel identity comes from the **DOF Digital
Tax Map**, not PLUTO.

- **1,164,820 parcels** — PLUTO omits 307,436 condo unit lots
- **306,443 condo lineage edges**

⚠ **Two known spine defects, both live:**
1. The C/R/A/S/E flags are **relationships, not identities** — 19,419 lots are
   mis-kinded. **Never gate on `kind == "ground"`.**
2. Condo **billing** lots are in neither DTM layer — 11,132 parcels /
   412,507 apartments, which is the new-tower stock.

⚠ **Merger and subdivision lineage is still missing.** A retired BBL drops out
of any gate-keyed pull, and the loss is invisible because audits read the
filter's own output.

## ⚠ THE TARGET IS WHAT HAPPENED, NOT A BETTER RECORD OF THE DOCUMENT

Login, 2026-08-14: *"not only actually fixing acris index but much more
information too like what actually happened."*

A better index still describes a *document*. Resolution describes an *event*, and
events do not fit in a row:

| level | what it says |
|---|---|
| ACRIS index | a DEED was recorded on date D, parties A and B |
| better index | …for $X, and A signed by John Smith, Managing Member |
| **what happened** | A conveyed Lot 5 to B for $X, **subject to** an existing mortgage, **together with** rights severed under the 1994 ZLDA, **excepting** the easement at CRFN Z |

⚠ **ONE INSTRUMENT, SEVERAL FUNCTIONS.** That is why `event.functions` is an
array. "Conveyed subject to the obligations of the 1994 zoning lot agreement" is
ownership AND zoning; modelling it as ownership-only silently drops the
encumbrance, and the parcel then reads as unburdened.

⚠ **WHAT HAPPENED IS OFTEN CROSS-DOCUMENT, SO IT CANNOT BE READ FROM ONE PAGE.**
A satisfaction means nothing except in relation to the mortgage it discharges; an
assignment means nothing without the note it moves. This is what REFERENCES
(8,699,896 rows) is for and why the graph is a graph. ⚠ But references coverage
is **2.0%** on the image-less set — measured over the whole set, after a
2,000-doc sample over-read it at 28%, a **14x** error. Most linkage must come
from the instrument text, not from the index.

⚠ **TERMS HAVE NO STRUCTURED HOME YET, AND THAT IS AN OPEN GAP.** Rate, maturity,
prepayment, guaranty, subordination, assignment of rents — these are "what
happened" in the sense that matters commercially, and today they can only land as
`claim` rows with a kind. `event` carries action, functions, dates and effects,
but nothing models a term. Naming it rather than pretending the schema is
complete.

⚠ **A PARAPHRASE OF A COVENANT IS NOT A COVENANT.** Where the obligation is the
fact, the words are the evidence — keep them verbatim with document_id and page,
and let the derived form point back at them. This is the same rule that keeps
`[UNRESOLVED]` in accepted text rather than smoothing it away.

## THE INPUT CONTRACT

Resolution consumes **evidence records**, never raw text and never images. Each
carries `document_id` · `page` · claim · confidence · channel agreement · disk
path. The path is what lets an online assertion be audited against offline
source.

⚠ **A fact refuses to exist without `document_id` + page.** No claim enters the
graph unanchored, however obvious it looks.

⚠ **Escalation state must survive into the graph.** An `unresolved` page is not
an absent fact — it is a known gap, and derivation must be able to tell the
difference. Silently treating unreadable as empty is how a hole reads as a zero.

## STATUS TODAY

The contract is built (`resolve/canonical.py`, `claims.py`, `fuse.py`,
`event.py`, `locate.py`); entity resolution exists (`entities.py`, `roles.py`,
`id_strength.py`, written 2026-08-05). **No corpus has passed through it**,
because acquisition has not run. The graph is designed and empty.
