# LEGAL INSTRUMENTS — DERIVATION

> **BOOTCAMP GOVERNS THIS FILE.** Every function, mode, event row and vocabulary
> used here is defined in [`Bootcamp.md`](../../Bootcamp/Bootcamp.md) - the ONE authority.
> Never redefine a term in this file; correct it there and it corrects
> everywhere. A rule that is not in the bootcamp is not a rule.


**This document is the source of truth for producing a legal instruments
derivation.** An agent runs this phase from this file alone.

# OVERVIEW

**The job: RELEVANCY TODAY.** The chains are the past; derivation collapses
them into the PRESENT — the current state of every parcel and party, to the
most granular level, with every answer traceable. The principle: **the
present is the sum of the past.** A parcel's "now" is nothing more than its
chains evaluated at today's date — is it encumbered, did it sell its air
rights, how much envelope remains, has the debt matured, who really owns it,
are they buying or selling around here, what are they developing. Once the
history is complete, the present state falls out of it.
**The boundary, upstream:** derivation intakes per key, behind resolution's
closed-or-named check — chains, accounts, written chains, relationship
edges. It never re-chains and never re-reads; a question it cannot answer
points at the named break or the missing source, it never guesses past one.
**The boundary, downstream:** there is no phase 06. Derivation's output IS
the product — what the cards, the maps, the queries, and the person read.
The loop closes here: the nightly sync at the top of the system exists so
that THIS phase's answers are fresh every morning.
**Table change 2026-08-20 (Bootcamp r49): event rows carry `doc_type` in
PROVENANCE.** Nothing in this phase's contract moves - chains and accounts
arrive as before - but answers gain a traceable dimension: "how much
envelope remains" can now cite the DEVR events behind it by type, and the
type->function ledger resolution builds becomes a derivable output itself
(what actually happens, per instrument type, with denominators).
**Two modes, same output:** BACKFILL derives each key as resolution closes
it; NIGHTLY DELTA re-derives exactly the keys whose chains changed overnight
(trigger-based — a key nothing touched is not recomputed, its answers stand
with their as-of date).
**Freshness is the product.** Every answer carries its AS-OF stamp — the
point the map was last proven level. Competitors are lagged, wrong, or
varying; an answer stamped "as of this morning, 04:00, proven level" is the
edge the whole system exists to produce.

---

# 1 · OUTPUT

Per key, four artifacts — the same two tracks a third time: **the outputs
(data)** = the present state and the metrics; **the outputs (written)** = the
macro summary and the signals' reasoning. Data and prose travel together at
every altitude: event -> chain -> output.

1. **THE PRESENT STATE** — the answers to the QUESTION REGISTRY (below),
   each one carrying its value, its trace (through chain -> event -> claim ->
   page), and its as-of stamp:

       encumbered?        YES — $4.4M outstanding to Lender X since 2019 [trace]
       air rights?        SOLD — 100,000 SF to 5-01234-0009 in 2016, $40M [trace]
       envelope left?     31,400 SF remaining of 74,000 [trace]
       debt matured?      MATURES 2027-03 [trace]
       owner tenure?      5th Ave LLC since 2003 (21 yrs) [trace]

2. **THE METRICS** — the numbers: $/SF by use, acquisition basis,
   outstanding debt, envelope SF, hold period, per-lot apportionments. Every
   metric is a FORMULA plus TRACED INGREDIENTS — and normalizations are
   labeled as normalizations ($/BSF is a division we chose, not a fact we
   found; the honest metric names its denominator).
3. **THE MACRO SUMMARY** — the second altitude: the parcel's whole story in
   a paragraph, generated from the written chain and the present state,
   never authored free-hand. (Extraction summarized the document; this
   summarizes the parcel.)
4. **THE SIGNALS** — the inference tier, ALWAYS labeled as inference, never
   mixed into the facts: distress pressure (the principal behind the owner
   under judgment), portfolio membership, market movement (the contact's
   event feed), active-nearby (buying/selling within the territory),
   development posture. A signal shows its reasoning; a reader can always
   see why the system thinks it, and that it is a THINK, not a record.

**⚠ The newest fact must never be the hidden one — PENDING documents surface
PROVISIONALLY.** A document recorded yesterday has its index row in the map
immediately, but its image is `pending`, so its events do not exist yet.
Rather than letting the freshest recording be invisible for up to 7 days, the
present state surfaces every pending document on the key as a PROVISIONAL,
INDEX-ONLY entry — "new mortgage recorded 2026-08-18, $2.1M per index, scan
pending — answers may shift" — clearly labeled, never mixed into the derived
answers, replaced by the real events the run after the scan attaches. (Index
values are used here under their verifier verdicts: parties trusted, amounts
flagged for the known-false classes.)

**Terminal states — every (key × question) concludes in exactly one:**

| state | meaning |
|---|---|
| **answered** | derived from the chains, traced, stamped |
| **partial — source named** | the question needs a source not yet in the system (landmark status -> LPC; rezoning qualification -> DCP; abatement schedule -> DOF; variance in action -> BSA; remediation -> DEC). The answer states WHAT is missing and lights up the day that source joins |
| **blocked — break named** | the chain carries a named break where this answer would come from — "unknown: title chain breaks 1994" beats a guess, every time |

The exact sum holds per key: `answered + partial + blocked = every question
in the registry`. No question silently skipped, no unknown dressed as an
answer.

**The run stamp — every run leaves one measured line.** When, mode, keys
derived (count / denominator), answers by state, signals raised, registry
size. A rising blocked-rate points upstream at chains; a rising partial-rate
is the argument for the next source.

---

# 2 · METHOD

## Evaluate the chains at t = now

The core operation is almost embarrassingly simple, because every hard part
was done upstream: take the key's accounts (which provably equal their
chains) and read them at today's date. Outstanding debt = the debt account's
current balance. Envelope remaining = the envelope account's current balance.
Owner = the last uncontradicted link of the ownership chain. Encumbered =
any live lien the chains hold, including party-bridged ones. The present
state is a READ, not a computation — the computation already happened, link
by link, with an audit at every step.

## The question registry — relevancy is EXTENSIBLE

Every question the present state answers is a REGISTRY ENTRY:

    question | inputs (chains/accounts/sources) | rule | output shape

- "Encumbered?" reads the debt + lien chains. "Envelope remaining?" reads
  the envelope account. "Actively selling here?" reads the party chain
  filtered to the territory and the trailing window.
- **Every row declares WHICH KEYS it applies to.** Parcel questions
  (envelope, encumbrance) run on parcel keys; party questions (portfolio,
  actively buying/selling, exposure) run on party keys — the present state
  exists for BOTH, and the exact sum runs over each key's APPLICABLE rows
  only. A party's "now" is as first-class as a parcel's.
- **Adding a question is adding a row, never new machinery** — the chains
  already hold the past; a new question is a new way of reading it.
- **Every entry declares its sources.** Questions answerable from legal
  instruments answer NOW; questions needing LPC, DCP, DOF, BSA, or DEC sit
  `partial — source named` until that source joins the graph. The registry
  is therefore also the SOURCE ROADMAP: the most-wanted partial answers name
  the next source worth wiring in.

## Events are not only transactions — the graph takes every kind

The chains so far carry TRANSACTIONAL events (a party did a thing to a lot —
the legs are written in the document). But an event is anything dated,
sourced, and anchored that changes a property's state — and REGULATORY events
qualify in full: an amended zoning resolution, a landmark designation, a new
abatement rule. Their difference is only in how their subjects are found:

- a transactional event NAMES its lots and parties;
- a regulatory event's subjects are COMPUTED BY APPLICABILITY — every parcel
  meeting the amendment's criteria is a leg, derived by rule, anchored to the
  text that made it so.

One amendment event can therefore flip an eligibility answer on thousands of
parcels overnight — and the existing machinery already carries it: the event
enters the graph, the touched keys re-derive on trigger, the registry's
"eligible for X?" rows go from `partial — source named` to `answered` the day
the regulatory feed joins. Same graph, same chains, same audit — the source
is new; the machinery is not.

## The inference tier — signals think, facts record

- A FACT traces to a page. A SIGNAL traces to reasoning over facts. The two
  never share a column, a table, or a sentence without the label.
- The named-debtor rule's counterpart lives here: the judgment against the
  individual never entered the LLC's chain (the law), but HERE it becomes
  the distress signal on the LLC's parcel (the read), labeled with its
  reasoning: "principal-linked pressure — J. Amato (relationship edge,
  2 corroborations) under judgment since 2023."
- Contact resolution (deed -> mortgage -> permit -> enriched profile) and
  market movement (the contact's event feed) live in this tier — they are
  the system's highest inferences, and they are only as good as the chains
  under them, which is why they live LAST.
- **The enrichment boundary:** signals compute from the graph plus
  EXPLICITLY REGISTERED enrichment sources — never a silent external lookup.
  Anything researched from outside enters as a registered source with its own
  provenance, or it does not inform an answer.

## Freshness discipline

- Every answer's as-of stamp is the sync's last proven-level point — never
  the wall clock. An answer is "fresh" because the map was PROVEN level this
  morning, not because today is today.
- The nightly delta re-derives ONLY keys whose chains changed — and any key
  a changed entity touches (the parked-event wake-up's counterpart: a new
  judgment re-derives every parcel its debtor owns).
- An answer that cannot be refreshed (its key's chain went defective
  upstream) is MARKED STALE with the date it was last good — shown, never
  hidden.

---

# 3 · CHECK — every question concludes, every answer traces

1. **The exact sum, per key:** `answered + partial + blocked = the key's
   APPLICABLE registry rows`. No question skipped; no unknown dressed as an
   answer. Every answer is stamped with the RULE VERSION that produced it —
   when a registry rule changes, the stamp says exactly which answers predate
   it and must re-derive.
2. **The trace audit:** sample answers back through chain -> event -> claim
   -> page. An answer that cannot walk its trace is withdrawn and re-derived.
3. **Metrics recompute:** every metric re-derives from its ingredients; a
   metric that cannot be recomputed from the chains is deleted — metrics are
   never stored truths, only stored formulas.
4. **The tier audit:** no signal appears where a fact belongs — sample the
   present state for inference language; sample the signals for missing
   reasoning. The label is load-bearing.
5. **Freshness audit:** every as-of stamp matches a proven sync level; stale
   answers are marked, and the stale count is on the run stamp.
6. **The check NESTS PER KEY.** A derived key is live product immediately.

There is no next phase to gate — the check here gates the PRODUCT: an answer
that fails its audit is withdrawn from the surface, never left standing
because removal is awkward.

---

# 4 · HANDOFF — the phase when said and done

The handoff is to the PERSON and the PRODUCT. Per key: the present state
(every registry question answered, partial, or blocked — honestly), the
metrics with their formulas, the macro summary, and the labeled signals —
each answer stamped with the morning it was proven current, each traceable
to a page in a recorded instrument. This is what the whole system was for:
open a parcel and know its now — encumbrance, envelope, ownership, debt,
posture — at a granularity nobody else has, refreshed while you slept.
And the loop closes: questions the registry cannot answer become its next
entries; partials name the next source; tomorrow at 04:00 the sync runs
again, and the answers are fresh again.

---

*The question registry ships with the legal-instruments questions live and
the cross-source questions named-but-partial; it grows by row, never by
rebuild. Derivation rules are design-final; registry contents are a living
inventory. The numbers age; the reasons do not.*
