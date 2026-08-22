# The life of a parcel

**Status: a MODEL, not a build order.** This is the frame the decoders answer to
— written down so that when a gap appears we can say *which stage it belongs to*
and *what evidence should have marked it*, instead of discovering the gap by
tripping over it. Nothing here is scheduled. Several parts (cost decoders,
ground lease, party context, listing-service comparables) are noted precisely so
they are not started early.

Login's framing, 2026-08-05, in his words: a site goes *"pre development,
construction, temporary operation and operation, then when in operation it
produces unit level comparables... then it eventually reaches a point where that
operating site has some kind of signal... basically activity while operating that
either restricts or motivates or simply signals and then one day it eventually
does become a pre-development."*

The value is not the diagram. It is that **a stage change is a claim, and every
claim needs a document that made it true.** Once each transition has a named
piece of evidence, the parcel history becomes checkable rather than narrated —
and the patterns across thousands of parcels become extrapolable.

---

## The cycle

```
                  ┌─────────────────────────────────────────────┐
                  │                                             │
                  v                                             │
      ┌──> PRE-DEVELOPMENT ──> CONSTRUCTION ──> TEMPORARY OP ──> OPERATION
      │           ^                                                  │
      │           │                                                  │
      │           └──────────── restart, no sale ────────────────────┤
      │                                                              │
      └──────── restart via a SALE ──────────────────────────────────┘
                (land sale if underbuilt/vacant;
                 operating sale if the asset is the income)
```

Two things about this loop matter more than the boxes:

1. **It restarts with or without a conveyance.** An owner can carry a site
   straight from operation back into pre-development with nothing recorded but a
   filing. A model that waits for a deed misses every owner-driven restart.
2. **The sale at the turn is two different instruments wearing one name.** If
   the site is underbuilt or vacant, the trade prices *land* and the comparable
   is $/BSF. If the asset is the income, it prices *operation* and the comparable
   is a cap rate. Same deed type, different question — and which one it is
   depends on the envelope, which is what the ACRIS decoder computes.

---

## Stages, and what makes each one true

| Stage | Entered when | Evidence (source) | Already decoded? |
|---|---|---|---|
| **Pre-development** | a qualifying filing exists | DOB NB / enlargement / ≥10k conversion job filing | stage model settled; DOB feed mapped |
| **Construction** | the work permit issues | DOB work permit; FO/EA are irreversible starts, FN/SF/EQ/CH are mobilisation only | mapped, not built |
| **Temporary operation** | TCO | DOB TCO — renewals are the velocity signal; renewals without sign-off = stalled | mapped |
| **Operation** | final CO | DOB CO (`ASBUILT`) | mapped |
| **Unit-level production** | occupancy begins | condo unit deeds (ACRIS), residential/commercial/manufacturing leases, HPD registrations | ACRIS partial; leases = the comparables source family, not started |
| **Signal while operating** | *see below* | many sources | this is the least-covered stage |
| **Back to pre-development** | a qualifying filing, with or without a sale | DOB filing; ACRIS deed only if it traded | partial |

### The stage nobody models: activity *during* operation

Login's sharpest point. An operating site is not static — it emits signals that
**restrict**, **motivate**, or merely **mark** it, and today these are scattered
across sources that nobody joins:

| Signal | Direction | Source |
|---|---|---|
| ULURP application | motivates (upzoning sought) | DCP ZAP–BBL `2iga-a6mk` |
| BSA variance / special permit | motivates, or restricts on expiry | BSA — grants from the 1930s still bind |
| Landmark designation, or *calendaring* | restricts the envelope — but detaches it as TDR | LPC `gpmc-yuvp`, `ncre-qhxs` |
| Development-rights transfer out | restricts permanently | ACRIS DEVR — **decoded** |
| Ground lease | restricts for a term; can also *be* the development structure | ACRIS — **not yet decoded** |
| Long lease to a credit tenant | restricts (occupied) and motivates (income) | listing services + ACRIS memoranda |
| CONH requirement | hard gate — blocks DOB permits outright | HPD `bzxi-2tsw` |
| E-designation, POPS obligation | restricts | DCP `hxm3-23vy`, `rvih-nhyn` |
| Mortgage maturing / refinance | motivates | ACRIS — the debt throughline |
| Tax lien, AEP listing, vacate order | distress → motivates a sale | HPD, DOF |
| Rezoning landing over the lot | motivates | DCP `nyzd` vs PLUTO divergence |
| ACP5 asbestos filing | earliest demolition tell — often precedes the DM | DOB |

**A gap in this table is a gap in the model, and that is the point of writing it
down.** The rule for filling one: name the stage, name the transition it marks,
name the document that proves it, *then* build the decoder.

---

## What the cycle produces (the comparables layer)

Each stage emits a different comparable, and conflating them is the classic
error:

- **Land / development** — $/BSF. Only meaningful where the envelope is known,
  which is why envelope accounting comes first.
- **Operating asset** — price per unit, per SF, cap rate.
- **Unit level** — condo resales, residential rents, commercial and industrial
  leases. This is a **separate decoding problem against listing services**, with
  its own defect catalogue.
- **Cost** — soft and hard. Noted by Login as a future decoder family. Without
  it a valuation at the sale stage is incomplete, because the residual land
  value *is* revenue minus cost.

## The layer above: who the players are

Login, 2026-08-05: *"once we can identify the players at each stage from the
documents we can even build decoders for context to who each player in the game
is."*

Every stage names parties, and they are **already being captured** — ACRIS
grantor/grantee and the borrower SPE, DOB PW1 §26 owner with phone and email,
LPC permit applicant *and* owner of record, HPD managing agent, head officer and
shareholder. What does not exist yet is the layer that asks **who this party
is** — developer or holder, first-timer or repeat, which lender follows which
sponsor, who assembles and who sits. That is a decoder over the party
observations we are accumulating, not a new pull. It gets built once the stages
beneath it are reliable.

---

## Why this ordering is not arbitrary

Population and accuracy come first, then monitoring — Login's own sequencing,
and the reason is mechanical: **a lifecycle model built on unverified stage
transitions will extrapolate patterns that are artefacts of the gaps.** A stage
we cannot see (activity during operation) looks like a stage that did not happen,
and the pattern engine will happily learn that sites sit inert for twenty years
and then jump to construction.

So the order stands: get each transition's evidence named and decoded, keep the
audit at zero falls, then look for patterns — never the reverse.
