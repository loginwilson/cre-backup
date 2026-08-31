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

**MEASURED, not predicted.** Counted across **99 event rows from five independent
readers** of m1 (`judge/batches/RE-EMIT-1.md`). This replaces the orchestrator's
guess, which was wrong about two functions.

| function | rows | dominant mode | what fires it |
|---|---|---|---|
| **IDENTITY** | 22 | `ASSERT` | corporate existence, signing capacity, execution, acknowledgment |
| **ENVELOPE** | 22 | `CREATE` | setbacks, building lines, materials, building form |
| **OCCUPANCY** | 16 | `CREATE` | family counts, prohibited trades, liquor, use bans |
| **ENCUMBRANCE** | 14 | `CREATE` · `STRUCK` · `ASSERT` | the covenant scheme; the struck assessments clause; the covenant against encumbrances |
| **ENTITLEMENT** | 9 | `CREATE` | ⚠ **the grantor's reserved rights** — see below |
| **TITLE** | 6 | `TRANSFER` | the conveyance itself — one row per reader |
| **COST** | 5 | `CREATE` | the building cost floor — **one per reader, unanimous** |
| **VALUE** | 5 | `ASSERT` | recited consideration — **one per reader, unanimous** |

**Confirmed NOT to fire — 0 rows out of 99, all five readers:**
`CAPITAL` (a deed carries no debt) · `PERMIT` (approvals here are **private**) ·
`AS_BUILT` (nothing is built on a vacant platted lot). **The seed spec predicted
this and it held.**

### ⚠ Two corrections the measurement forced

**`ENTITLEMENT` fires and the seed spec did not predict it — 9 rows.** The grantor's
reserved rights (to build on the plat, to approve plans, to grant use rights) are
*development rights attaching to land that survive their owner*, which is exactly
`ENTITLEMENT`'s question. The seed listed only six functions; **eight fired.**

**`COST` is confirmed by count, not by argument** — five rows, one per reader,
after the file's self-contradiction was settled.

### Modes

| mode | rows | note |
|---|---|---|
| `CREATE` | 57 | the covenant scheme dominates the instrument |
| `ASSERT` | 32 | identity, capacity, consideration |
| `TRANSFER` | 5 | one per reader — the grant |
| `STRUCK` | 5 | **one per reader, unanimous** — the assessments clause |
| `MODIFY` | 0 | — |
| `TERMINATE` | 0 | ⚠ **and it should be 0.** One reader deleted its TERMINATE row on the merits: *"a TERMINATE row invents an act on a date when nothing happened."* `until` is the mechanism for a self-expiring scheme. |

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

## 7 · MEASURED BASELINE — what m2 is scored against

From 99 rows, five readers, m1. These are counts, not opinions.

**`bbls` forms actually used:**

| form | rows | reading |
|---|---|---|
| BBL list | **81** | the overwhelming default — rd supplies it, nobody derived one |
| `SET:` | 10 | ~2 per reader: the reservation over the plat, and the four-street carve-out |
| `INSTRUMENT` | 7 | used for execution / acknowledgment rows — **outside its stated scope**, which readers flagged |
| `UNPLACED` | **1** | a single row in 99. One reader chose it and said it was false |

**`until` populated: 9 · 16 · 7 · 14 · 10** — 56 of 99 rows, and **the spread is the
open gap made visible.** The expiry sentence sweeps *"all restrictions and covenants
in this instrument"*, and whether it reaches the grantor's reserved rights is
unsettleable from the page. Blank asserts perpetuity; a date asserts expiry; there is
no third state, so five readers guessed differently on the same clause. **A two-fold
spread on a machine field is the cost of the missing `UNKNOWN(reason)` form.**

---

## THE STANDING PREDICTION FOR m2

Written **before** m2 is drawn, so it can be scored:

1. **The eight-function signature in §2 fires**, and `AS_BUILT` / `CAPITAL` /
   `PERMIT` do not. (m1: 0 rows out of 99 for all three.)
2. `ENTITLEMENT` fires on the grantor's reserved rights — **now a measured
   expectation, not a guess.**
3. `STRUCK` and `TERMINATE` do not both appear; a self-expiring scheme uses `until`.
4. A filed-map reference is present and **is not in rd**.
5. The covenant scheme carries a stated expiry.
4. A private approval right appears and still has no home in the eleven.
5. Structural surprise **≤ 3**.

If 1–4 hold on m2, they become expectations. If any fails, that section is wrong and
gets rewritten — **not patched**.
