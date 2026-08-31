# CLASS SPEC — deed carrying a developer's restrictive covenant scheme

Governed by `Bootcamp/LOOP.md`. Format follows `Bootcamp/specs/CEMA.md`.

| member | doc | era | custodian | pages | scheme expiry |
|---|---|---|---|---|---|
| m1 | RC_1598772 | 1911 | Richmond | 2 | 1915-01-01 |

⚠ **ONE MEMBER. THIS IS A SEED, NOT A SPEC.** Everything below is a *prediction*
extracted from a single document, and a single instance cannot distinguish a class
property from an instance quirk. CEMA needed three banked members before its spec
was worth testing. **Read every claim here as "expected", never as "known".**

**Status: OPEN.** Structural surprise: not yet measurable — the first number arrives
with m2.

---

## 1 · IDENTITY — how to recognise it

**Expected:** a fee conveyance of platted subdivision lots, where the grantor is a
development company and the operative weight of the instrument is in the covenants,
not the grant.

Signals, in expected order of reliability — **none yet confirmed on a second
member**:

1. **The grantor is a development company.** m1: **`WOOD HARMON RICHMOND REALTY
   COMPANY`**, printed in caps, six times across two pages.
   
   ⚠ **This document carries THREE similar names and they are not stated to be the
   same entity.** *Wood, Harmon & Co.* appears only as the firm the plat was
   *surveyed for* and as the *return-to* party. An earlier version of this spec
   merged all three; five readers caught it independently. **Do not assume a
   relationship the deed does not state.**
2. **A filed-map reference the lot numbers depend on.** m1: *map no. 995 B*, filed
   Richmond County Clerk 1907-07-05. **Without the map, "lot 16, block 403" is not a
   location.**
3. **A covenant block with a stated expiry** running to a round calendar date.
4. **Reserved rights running back to the grantor** — approval over plans, fences,
   or building lines.

⚠ **UNTESTED PREDICTION:** the register type is expected to read `DEED` and to be
accurate, since the instrument *is* a deed — the covenants ride along. If a member
appears under a catch-all shelf, that is a structural surprise and this section is
wrong.

## 2 · THE EVENT — which of the eleven fire

**Signature (expected):**

| function | mode | why |
|---|---|---|
| **TITLE** | `TRANSFER` | the conveyance itself — one row |
| **ENCUMBRANCE** | `CREATE` | the covenant scheme as a burden running with the land |
| **ENVELOPE** | `CREATE` | setbacks, building lines, materials |
| **COST** | `CREATE` | building cost floors — a duty to spend. ⚠ **not ENVELOPE**; settled 2026-08-31 |
| **OCCUPANCY** | `CREATE` | family counts, prohibited trades, use restrictions |
| **IDENTITY** | `ASSERT` | grantor's corporate existence and the officer's capacity |
| **VALUE** | `ASSERT` | recited consideration |

**Expected NOT to fire:** `AS_BUILT` — on a vacant platted lot nothing has been
built. `CAPITAL` — a deed carries no debt. `PERMIT` — approvals here are **private**,
held by the grantor, not government.

⚠ Deviation from this signature is a finding, not a correction.

## 3 · FIELDS

| field | always / usually / sometimes | where it sits | how it is verified | absence looks like |
|---|---|---|---|---|
| grantor (company) | always | first recital | rd party list | — |
| grantee | always | first recital | rd party list | — |
| consideration | always | recital | rd `amount`; may read `$0.00` | recited nominal sum |
| lot + block | always | description | rd, and the filed map | — |
| **filed map number** | expected always | description | ⚠ **not in rd** — document only | *"or intended to be filed"* |
| covenant expiry | expected always | covenant block | calendar arithmetic | scheme runs forever — check twice |
| building cost floor | usually | covenant block | varies by **family count** — `COST` | — |
| prohibited trades | usually | covenant block | one row, list in `terms` | — |
| private approval right | expected usually | reserved rights | — | ⚠ has no home in the eleven |
| struck clauses | sometimes | printed form | **rect + mark (card 1)** | — |
| recording time | expected always | endorsement | registry lane | — |
| return-to party | expected always | endorsement back | registry lane | often the only agent address |

## 4 · VERIFICATION — the tests this class requires

- **The expiry is calendar arithmetic.** m1's scheme runs 1911-04-14 → 1915-01-01:
  three years, eight months. **A table omitting it is wrong about the parcel from
  1915 onward.**
- **The map date is a fourth kind of date.** Not instrument, not acknowledgment, not
  recording. It has no slot in the labelled block and has already been mistaken for
  a recording date once by a checker.
- **Lot numbers against the filed map**, never against the index alone.
- **Every strike gets a rect** before any claim rests on it (card 1).
- **Cost floors vary by FAMILY COUNT, not street** (m1, p1): $2,000 *"if built for
  use and occupancy of one family only"*; $3,000 *"if built as a double house … or
  as a double tenement."* Nothing ties either figure to a street. One clause, two
  numbers — **one row** under card 2, and the function is `COST`.

## 5 · CHAIN — what this class points at and does not contain

- **The filed map** (m1: no. 995 B, Richmond County Clerk). The parcel description is
  meaningless without it, and it is a separate instrument in a separate series.
- **The plat's other lots — and ⚠ NOT via the covenants.** The covenants bind *"any
  part of the **herein-described premises**"* only, so covenant rows carry the
  **subject BBLs**. The phrase reaching the plat — *"any part of South New York,
  Addition Number Four"* — sits in the grantor's **reservation**, its exemption from
  its own scheme. Only the reservation rows carry `SET:`.
  
  ⚠ **An earlier version of this spec had this backwards.** One reader: *"Had I
  followed the spec, fourteen rows would have fanned to the wrong parcels — the
  covenants would have reached the whole subdivision and missed lots 16 and 17
  entirely."* That is a wrong parcel history produced silently at Reorganize, which
  is worse than a wrong reading because nothing downstream would flag it.
- **The grantor's other deeds in the same plat.** A uniform scheme is enforceable
  across the subdivision, so siblings should carry near-identical covenant text.
  **This is the cheapest available cross-document check for this class.**

## 6 · SURPRISES — the running log

**m1 (RC_1598772)** — baseline; a first member's surprises are unclassifiable
because there was no spec to surprise. Recorded for m2 to score against:

*Structural (the framework had no place to put it):*
- a clause **deleted before execution** — no mode fitted → `STRUCK`
- a covenant **expiry** — the row held one date and the scheme has two → `until`
- the **registry's own act**, its time, and the return-to party → registry lane
- a **private discretionary approval right** — `PERMIT` is government-only, and
  `ENVELOPE` captures the constraint while losing the veto holder. **Still has no
  home. Candidate function.**
- a **parcel definition** (the filed map) — filed under `IDENTITY`, whose triggers
  are all persons and entities. A map is not a party. **Candidate function.**

*Incidental (about this instance):*
- acknowledgment day overwritten by descenders — four readers read 18, one holds 15
  as the only alternative; calendar range 14–25
- no fee, tax or revenue stamp found in either margin at 900 dpi — *"I found
  nothing"*, not *"the document says there is nothing"*

---

## THE STANDING PREDICTION FOR m2

Written **before** m2 is drawn, so it can be scored:

1. The six-function signature in §2 fires, and `AS_BUILT`/`CAPITAL`/`PERMIT` do not.
2. A filed-map reference is present and **is not in rd**.
3. The covenant scheme carries a stated expiry.
4. A private approval right appears and still has no home in the eleven.
5. Structural surprise **≤ 3**.

If 1–4 hold on m2, they become expectations. If any fails, that section is wrong and
gets rewritten — **not patched**.
