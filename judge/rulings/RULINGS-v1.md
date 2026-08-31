# Rulings — binding, frozen, not re-litigable

Orchestrator, 2026-08-30, after both reconciliations and both steelmen were committed and
verified. v1 is built against this document. Where a ruling carries a **precondition**, the
precondition is part of the ruling: if v1 cannot satisfy it, the ruling inverts, and the
inversion is reported to me rather than absorbed silently.

Nothing here was decided from one side's argument. Both steelmen moved their authors, and
two of the three questions stopped being boundary disputes once written out.

---

## R-1 · Lease — Title, under a precondition

**A clause is classified by what it moves, never by the word *lease*.**

| the clause moves | function |
| --- | --- |
| a possessory estate (creates, transfers, surrenders, terminates a leasehold) | **Title**, as a leasehold object |
| a security interest *in* a leasehold (collateral assignment of leases and rents) | **Encumbrance / Capital**, per the security rules |
| an independently stated burden on the fee | **Encumbrance**, additionally, and only on express words |

This dissolves the collateral-assignment case that both drafts mishandled, and it is the
reason A's `M-LEASE` and B's lease rule were both defective: **both keyed on the word.**

**Precondition — and it is the whole ruling.** B's steelman established that "lease is
Title" is safe *only* if Title is a multi-estate object map in which every object carries a
mandatory `interest_kind` (FEE · LEASEHOLD · SUB_LEASEHOLD · …) and **no fold or query can
return a Title holder without naming it.** A scalar or winner-takes-all Title cell makes the
Encumbrance position decisively better, because at 25M documents most consumers will ask
*who held title* long before they ask *which estate kind*, and a leasehold sitting in Title
becomes a false-positive owner forever.

v1's matrix is the state-object architecture both of you converged on, so this condition is
satisfiable **by construction**. Build it that way. If it turns out you cannot keep
concurrent fee and leasehold objects separate without special-case repair, **R-1 inverts** to
Encumbrance-on-fee with a Title exception only for a separately indexed leasehold object,
and you tell me.

**Residual, answered.** Where the leasehold has no BBL of its own — which in this corpus is
almost always — the leasehold object lives in the **indexed fee BBL's Title column, keyed
separately from the fee object.** It is the only BBL the document gives. A's frozen rule
placed it on "the leasehold's own BBL if indexed", a lot that mostly does not exist, and so
dropped the leasehold layer out of Title corpus-wide while looking correct.

**Frozen fixtures L1 and L2**, as specified in `steelman-B.md` §1.2. Both are required: L1
tests whether Title corrupts fee continuity, L2 whether Encumbrance erases a separately
indexed estate. A single easy lease confirms whichever schema was designed around it.

---

## R-2 · Observation time — bitemporal, enforced structurally

An observation carries **two** times, never one:

- `occurrence_time` — when the statement was made
- `asserted_valid_time` — the interval the document says the condition held

**Absent valid time is `UNKNOWN`. It is never copied from occurrence time.**

B's steelman reduced this to an interface test: bitemporal is safe with a two-axis consumer
and an observation lane that cannot compose into state; with a single undifferentiated
chronology, the observation must be left unplaced. I am making the condition true — **v1
provides two named axes, and the state chronology sorts OBSERVATION events on
`asserted_valid_time` only.**

**The enforcement is structural, not a flag.** B's objection is the correct one: *"every
extra temporal lane is another contract every consumer must honour"*, and the next phase
does not exist yet to honour it. So an OBSERVATION with `asserted_valid_time = UNKNOWN`
**must serialize without any field a state sorter can consume.** Not a nulled date, not a
date behind a flag — absent. Make the wrong thing impossible rather than forbidden; this is
R-4's closure principle applied to time.

A's framing of why, which decides it: strict handling produces **honest absence**, while
statement-date placement produces **systematic bias** — every observation lands at or after
its condition's true date and never before, so the error accumulates in one direction and
never averages out. Old buildings, uses and values appear newly true near filing and
digitisation eras, and each error is individually plausible enough to survive review.

**Frozen fixtures O1, O2, O3**, as specified in `steelman-B.md` §2.3. O3 — a statement
signed in one year expressly describing a condition decades earlier — is the one that fails
any rule writing observations into their signature year.

---

## R-3 · Transfer tax and recording fee — a gap, now closed

Adopt `steelman-B.md` §3.1 in full as the base rule, with one merge from A.

Load-bearing points: a labelled tax or fee is a **Cost `ASSERT` / `OBSERVATION`** with a
status taken only from the label — `REPORTED_AMOUNT`, not `PAID`; the recording timestamp is
**never** substituted as its date, not even for a recording fee; payer and payee come only
from express words, never from customary liability; an unallocated total stays one registry
object with `allocation_status = NOT_DERIVABLE`.

**From A, incorporated as the attachment rule:** charges levied on an **act** attach to that
act's event; charges levied on the **filing** attach at document scope and to no event.
Without it, a recording fee on a five-event document gets attached to one of them
arbitrarily and reads downstream as a finding.

---

## R-4 · `registration.amount`, and the two requirements that make it enforceable

**`registration.amount` carries no meaning derived from the instrument's type.** It is
retained as an index-reported amount with semantic kind `UNKNOWN` unless a citable image
label or operative text says what it measures. Registration type never supplies the kind.

Two general requirements, both of which you already had and neither of you had recognised as
the enforcement mechanism:

**R-4a · Closure, not prohibition.** *"Negative rules are unverifiable; closure is
verifiable."* Every field terminates in a verbatim quote **or** a named rule drawn from a
**closed, enumerable set**, with its inputs named. A reader that back-computes must then
either quote a number that is not on the page or name a rule that does not exist — both
detectable by someone who never sees the reasoning. Being numerically correct is not an
admission rule.

**R-4b · The quote must prove the field.** B's `FR-EV-002`: a quote must prove *that exact
semantic field*, not merely contain the same number. A quote of `$2,102.00` attached to a
value of `525500` passes a presence check and fails a proof check. Presence checking is what
a cheap validator does; proof checking is what the framework must specify.

The transfer-tax back-computation is named as forbidden **explicitly**, because a rule that
says only "no outside knowledge" will not stop a model that does not experience a statutory
rate as outside knowledge.

---

## R-5 · Intra-document exemplar comparison — the first enumerated derivation

On the frozen document a handwritten figure is ambiguous in isolation and resolvable from
inside the document by a route neither draft had a rule for. `UNKNOWN` is **not** a safe
answer where such a route exists — it is an under-read, and freezing it would have taught
every future reader to decline a value the document supports.

A was told only that a route existed, went and found it, and found it **more completely than
I had.** I had located exemplars in one field; A located four across two, and identified a
weakness I had missed. The rule below is A's, and it is adopted:

> Where a character is not certain after the 900 dpi re-render, locate instances of each
> candidate character elsewhere in the same document, in the same fill-in campaign, at
> positions where that character's identity is not in doubt. Resolve only if (a) at least two
> exemplars of one candidate exist, (b) the glyph matches their form, and (c) exemplars of the
> competing candidate either do not match or do not exist. Record the rule, the location of
> every exemplar, the exemplar count, and whether the comparison was **two-sided** or
> **one-sided**. If no candidate has exemplars, or more than one matches, the field stays
> `UNKNOWN`.

Three limits, all A's, all binding:

- **One-sided comparisons are weaker and must be recorded as such.** Absence of the competing
  character may only mean the writer never had occasion to write it. The record carries which
  kind it was so a reviewer can weight it. The frozen case is one-sided.
- **Same hand must be established, not assumed.** The frozen package alone carries at least
  two hands. Exemplars drawn across hands prove nothing.
- **Character identity only.** No inference about content, and none from one field's value to
  another's.

**Why this is load-bearing rather than a curiosity.** A's count: five of the ten documents it
read carry material values handwritten into printed blanks — recording dates, book and page,
block and lot, party names, tax stamps. The corpus is scans of printed forms with handwritten
fill-ins, and a form has many fields in one hand. **Both drafts answered this situation with
`UNKNOWN`**, which discards the commonest recoverable evidence in the corpus.

**And it closes a hole in R-4a that would otherwise have been fatal.** A's formulation:
*"the set has to be populated with the routes that are legal, or closure just becomes a
stricter way of returning nothing."* Closure without an enumerated set of admitted
derivations is not rigour, it is universal `UNKNOWN`. This is derivation **D-1**; v1 must
enumerate the rest.

**Consequent amendment to escalation:** an illegibility escalation fires only after the
re-render **and** after exemplar comparison fails. Otherwise the heavy tier is paid to do
work the primary could have done from the page in front of it.

**B holds the pen and must critique this before writing it in.** It arrives as A's proposal,
not as settled text — B has been right about evidence handling before, on `R-INP-6a`, against
a document neither agent had seen.

---

## R-6 · Size — the binding number is what the reader holds at once

| bundle | ceiling |
| --- | --- |
| **core** — always loaded, every document | **15,000 tokens** |
| **core + one type module + one registry adapter** — what is actually in context for one document | **22,000 tokens** |
| type modules, individually | no fixed cap; each self-contained, none restating core |

### R-6a · Does the matrix spec count inside the 22,000? No — conditionally

Raised by A before v1 was written, which is the right time: settled afterwards, B writes to
one reading and A measures by another, and a cycle is spent arguing about the measurement
instead of the content.

**Production extraction emits events. Resolution into a BBL chronology is a separate phase
with a separate reader.** So the 22,000 governs **core + triggered modules + registry
adapter**, and the matrix spec carries its own budget, measured separately.

**The condition, and A audits it: no rule needed to produce a correct event may live only in
the matrix spec.** If an extractor must know it, it belongs in core or a module. State paths
per function are module content, not matrix content. **If the matrix spec turns out to carry
anything extraction depends on, the split is a fiction and the matrix spec counts inside the
22,000** — report it rather than absorbing it.

Note what is *not* evidence here: this loop's own agents hold both, because Block 2 requires
`resolved.md`. That is a property of the loop, whose readers are frontier models where the
ceiling does not bind. It says nothing about the production bundle.

### R-6c · The matrix spec's ceiling is 10,000 tokens, provisional

A's gate correctly refuses to invent a number and prints *"no ceiling ruled yet"*. Here is
one, and here is exactly how much it is worth.

**10,000 tokens.** Two grounds, neither of them strong on its own:

- The resolution reader holds the spec **plus one BBL's entire event history**. A
  well-transacted lot could carry hundreds of events, and an event serialising with its
  evidence, parties, quantities and terms is not small. The spec must stay a minority of that
  context, not compete with it.
- A resolution spec larger than two-thirds of the *entire extraction core* is prima facie
  suspect and should have to argue for itself.

**What this number is not.** It is not derived from a measured event-count distribution per
BBL, because extraction has not run and that distribution does not exist. It is set now, in
advance, for the same reason the original 15,000 was: a threshold chosen after anyone can see
whether it is convenient is not a threshold. **Revise it when the resolution phase's reader
and context budget are actually specified**, and revise it by re-deriving from observed
events per BBL — not by arguing from this paragraph.

The gate reports matrix-spec size at **every** version bump whether or not the ceiling binds,
so growth stays visible before it becomes a problem. Reporting is the part that matters; the
number is the part I am least confident in.

### R-6b · Section markers are mandatory

A measurement tool that sniffs headings yields a number the author can move by renaming a
heading. v1 carries explicit markers — `<!-- BUILD:CORE -->`, `<!-- BUILD:MODULE <name> -->`,
`<!-- BUILD:ADAPTER <name> -->`, `<!-- BUILD:END -->` — and the gate **refuses to measure** an
unmarked file rather than guessing. Cheap now, expensive to retrofit.

The token estimator is a **declared convention** (`chars/3.6`, with `chars/4.2` reported
alongside), not a measurement: no tokenizer is installed here and the production reader's
differs from any that could be. What matters is that it is deterministic, published, and
identical for both agents. The gate exits non-zero when over, so *"v1 fits"* is something the
build reports rather than something either agent asserts in prose.

Measured mechanically by a build script, reported at every version bump, not estimated in
prose. The original 15k was justified by a weak reader with scarce context; that
justification is gone, and the ceiling stays on the ground that **a rulebook too large to
hold coherently is applied inconsistently across 25M documents** — as true of a strong reader
as a weak one.

Modules load on trigger. B is right that hybrid instruments need more than one, so A's
exactly-one rule is rejected: a deed with an attached occupancy assertion, or a mortgage plus
rents assignment, must load both.

---

## R-7 · Rules key to acts, never to instrument-type names

Promoted from A's lease finding to a **standing constraint on how every rule in v1 is
written.** Richmond says `A/LEASE`, `REL`, `SAT`; ACRIS says `ASSIGNMENT OF LEASES AND
RENTS`; film says neither. Registration only *nominates* modules; operative content confirms
them. `Document Type: DEED, 1-2 FAMILY` on a cover against `"type": "DEED"` in the registry
shows the registry value is a **normalisation, not a transcription**.

---

## R-8 · The pen for v1 goes to B. A verifies, and owns the budget audit.

Not a judgement about whose work was better, and not a demotion — A's contribution to this
block was exceptional and is why half these rulings exist.

The reasoning is architecture and incentives. **v1 is substantially B's design** — the
state-object map, the evidence registry, the quantity registry, clause-keyed module
triggers, the bitemporal record — and A has said plainly that its own module architecture is
name-keyed and does not survive R-7. The pen belongs with whoever is writing their own
design; faithful transcription of someone else's is a real risk, and A named it first.

**B's draft is also the one over budget**, at ~21.4k against 15k, and B conceded it. The
agent that must cut should be the one holding the pen, not the one asking for cuts.

**A verifies, with authority to reject.** Not a rubber stamp: A owns the mechanical budget
measurement under R-6 and may return v1 for exceeding it, and A owns the trigger-frequency
audit under R-9. Those are A's demonstrated strengths — it measured the collision, it found
its own vacuous rule, it found the interlock on the frozen document.

**The pen returns to A at v2.** Alternation is preserved.

---

## R-9 · Trigger-frequency check — standing, with its limit stated

At every version bump, for each rule with a conditional trigger: **how often does it actually
fire in the corpus?** A rule that never fires and a rule that always fires are both defects,
and both are invisible from the rule's text. Registry-expressible triggers are measured
directly against the slate's 609,811 sampled rows; content-dependent triggers need a sampled
frame.

**The limit, stated in v1 rather than as a footnote:** frequency catches vacuity and
over-capture and says **nothing** about whether a boundary is drawn correctly, because a
wrong classification fires at a perfectly plausible rate. It must never stand in for
boundary testing.

---

## R-10 · Selection — assigned strata, identical round documents

Survey strata are **assigned and complementary**; `surveyed.md` stays mandatory so any
disagreement can be attributed to exposure rather than reasoning. That distinction has
already paid: all fifteen ids B surveyed were ACRIS 2002–03, and nearly every difference
between the drafts traced to that.

**Round documents are identical for both agents** — different strata for surveying, the same
document for extracting, or the blind comparison is worthless.

**Each round's document comes from a stratum not yet tested**, recorded in the round log with
the rule it strains. The readable corpus is 2002–03 ACRIS, pre-ACRIS film, and Richmond; the
ACRIS documentation floor sits around October 2003 and there is no modern ACRIS to draw on.
Left alone both of you drift to 2003 ACRIS because it is the cleanest and most structured,
which is the failure this rule exists to prevent.

---

## Frozen test cases

| id | document | tests |
| --- | --- | --- |
| **TC-001** | `2002122700153001` | three-way: under-read to `UNKNOWN`, right answer by forbidden route, right answer by citable route. Also page inventory — four different page counts, actual is 8 images — and R-4's typing rules |
| **L1 · L2** | to be selected | R-1 — fee continuity under a leasehold, and a separately indexed leasehold estate |
| **O1 · O2 · O3** | to be selected | R-2 — three clocks preserved, blank truth-time, and an adversarial historic recital |

Expected answers are held outside both agents' workspaces. Re-runs go to fresh contexts with
answers withheld, per TRAYCER.md — otherwise the test measures memory, not the framework.
