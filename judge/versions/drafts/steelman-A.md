# STEELMAN — A

Written before seeing `reconcile-B.md`. Two genuine deadlocks steelmanned, plus
the rule for the tax/fee gap you correctly re-classified out of the queue.

Where a steelman moved me I say so, because that is the useful signal and hiding
it would waste the exercise.

---

## 1 · LEASE — TITLE, OR ENCUMBRANCE?

**B's position (FR-FN-002, FR-FN-024):** creation, assignment, surrender or
termination of a leasehold estate is `TITLE`. Rent and lease economics are Title
terms.

**My position, and I have held two:** my frozen draft (M-LEASE) says
`ENCUMBRANCE` on the fee parcel, with `TITLE` only on the leasehold's own BBL if
one is indexed. My reconciliation §5.2 proposed something different — both,
linked. I should not have let those drift, and the difference matters below.

### 1.1 The strongest case for B

**a · Title's question is "who holds an interest", and a leasehold is one.** A
tenant under a 99-year ground lease has exclusive possession, an alienable
estate, and usually the whole economic interest in the improvements. If that is
not Title, then Title means "the fee", which is narrower than the function's own
question and narrower than the eleven-function scheme implies. B's reading uses
the function as defined; mine quietly redefines it.

**b · My rule is the always-dual instinct I already lost on.** In §5.3 I conceded
B's evidence-conditioned Capital/Encumbrance rule over my R-FN-3 always-dual
emission, and in §5.5 I attacked B's mandatory term population as TRAYCER warning
#3. My reconciliation's lease proposal is the same always-dual pattern, applied
to a type that recurs across all four namespaces. B can name that inconsistency
and would be right to.

**c · My "false fee transfer" argument is an argument against collapsing cells,
not against B's classification.** I said B's rule makes a consumer see the fee
change hands. Under B's own model it does not: MX-CELL-001 makes a cell a map
keyed by `state_object_key`, and FR-REC-004 gives the leasehold its own key,
distinct from the fee's. The Title cell holds two objects — a fee object,
untouched, lifecycle UNKNOWN, and a leasehold object, TRANSFER, ACTIVE. Nothing
says the fee moved. My objection reduces to "a naive consumer might flatten the
cell", which is a complaint about consumers.

**d · The strongest one: Encumbrance-on-fee is derivable, Title-on-leasehold is
not.** From a leasehold estate object you can compute that the fee is burdened —
it is an entailment, and a downstream phase can derive it without a second event.
The converse fails: from `ENCUMBRANCE kind=LEASE` you cannot recover the estate,
its term, its assignability, or who holds it, unless you copy all of that into
the Encumbrance payload — at which point you are storing one object twice and
have created a synchronisation problem across 25M documents. **Emit the richer
object; derive the poorer one.** I think this is the best argument on either side
of the question.

**e · My frozen rule does not do what I claimed, and it loses more than B's.**
M-LEASE puts Title on "the leasehold's own BBL if one is indexed" — and in this
corpus a leasehold almost never has its own tax lot. So my rule emits Title
almost never, and the tenant's estate, term and identity never appear in the
Title function anywhere in the corpus. B loses nothing; I lose the entire
leasehold layer. **That is a worse failure than the one I accused B of**, and it
is in my frozen draft rather than in my reconciliation, which makes it evidence
about my reading of the question rather than a debating point.

### 1.2 What would settle it — two document shapes

Neither is a principle; both are checkable, and each is a frozen test case
whichever way you rule.

**Shape L1 — estate transfer versus security assignment.** An instrument titled
"Assignment of Lease" or "Assignment of Leases and Rents" whose **assignee is a
lender** and whose operative words are collateral language ("as collateral
security for", "to secure payment of"). B's FR-FN-024 says on its face that
assignment of a leasehold estate is Title — and read literally it converts every
collateral assignment into a recorded change of ownership. My rule calls it
Encumbrance, correctly.

*Candidate already in the corpus:* `RC_1000046` — Richmond, ASSIGNMENT OF LEASE,
three BBLs, ASSIGNOR `OUTERBRIDGE COMMONS LP` → ASSIGNEE `SOVEREIGN BANK, N.A.`,
property type Vacant Land. **I read its cover page only; the body is unread**, so
I am naming a shape I expect it to have, not a fact. A bank taking a ground lease
estate outright is unusual; a bank taking a collateral assignment is routine. The
document will say which, and that is exactly the property a test case needs.

**Shape L2 — an estate with no parcel of its own.** A ground lease assignment of
the entire remaining term, consideration stated, indexed only against the fee
lot, the fee owner not a party. Under B: `TITLE/TRANSFER` on the fee's BBL, and
the fee holder is never named in the Title column of their own parcel. Under my
frozen rule: no Title event at all, and the largest transaction on that parcel is
absent from Title. Both answers are visibly odd; the ruling should be made
looking at one.

*Candidates:* `2003010500014002` and `2003010600302005` — both in B's
`surveyed.md`, both unread by me.

### 1.3 What each answer costs

| | if B is right | if I am right |
|---|---|---|
| my frozen M-LEASE | leasehold estates absent from Title corpus-wide — a whole layer missing, undetectable because nothing points at it | correct |
| my reconciliation §5.2 | one redundant Encumbrance event per lease instrument — small, bounded, visible | correct |
| B's FR-FN-024 | correct | every collateral assignment of leases and rents is a recorded ownership change in the Title chronology; the fee owner is never a party, so nothing in the event signals the error |

**This is not a coin-flip question.** Both errors are systematic and neither is
self-announcing. But note the asymmetry: my reconciliation's error is bounded
volume, B's is wrong content.

### 1.4 The synthesis the steelman produced

Writing (d) and (e) changed what I think the question is. **Both rules key on the
instrument type, and that is the actual defect.** B keys "lease → Title"; my
draft keys "lease → Encumbrance". The discriminator is not the word *lease* but
what the operative clause moves:

> If the clause moves the **estate** — possession, term, the tenant's interest —
> the object is the leasehold estate and the function is `TITLE`.
> If it moves a **security interest in** that estate or its rents, the object is
> the security interest and the function is `ENCUMBRANCE`.
> These are different objects with different `state_object_key`s under
> FR-REC-004, and one instrument may do both.

That dissolves Shape L1 entirely and is better than either position I have held.
It leaves one residue, which is what still needs your ruling: **when the estate
has no BBL of its own, which parcel's Title column does the estate object live
in?** The choices are the fee's BBL (B, with the estate as a distinct keyed
object in the cell) or nowhere (my frozen draft). I now think B's is right, on
argument (d), provided the cell is never flattened to a single value — and that
proviso is a matrix-spec rule, not a function-boundary rule.

**Net: I have moved substantially toward B**, and the part of my position that
survives is the estate/security discriminator rather than the classification.

---

## 2 · WHERE AN OBSERVATION LANDS

The tension I hold both sides of. In §3.3 I accepted B's rule that an
UNKNOWN-dated event goes to the undated annex and never touches a dated cell. In
§8.3 I argued an observation's placeable date is the date of the observed
*condition*, which documents usually do not state. Together: observations are
annexed wholesale. In §9 I leaned to the alternative — place at the observation
date, marked, because it is a genuine upper bound.

So the position I do not hold is **strict**: condition-date unstated → UNKNOWN →
annex.

### 2.1 The strongest case for strict annexation

**a · An upper bound is not a date, and the chronology sorts on dates.** Placing
an observation at its observation date places it at the latest moment it could
have been true. That is precisely the error the whole date-precedence apparatus
exists to prevent — a 2020 filing of a 2018 event lands ten places wrong — and
knowing it is a bound does not move it. A 1960 condition certified in 2020 sorts
sixty years late whether or not we annotate it.

**b · A marker does not protect a consumer that does not read markers.** My
proposal is "place it, marked". But both drafts assume downstream reads the three
load-bearing tags; that is the premise of the entire consumer message. If markers
were reliably honoured we would not need the annex for undated *transactions*
either — and I conceded that one without argument. I am accepting annexation when
a transaction's date is unknown and rejecting it when an observation's is, and
the epistemic difference cuts the **other way**: a transaction's unknown date is
an evidentiary failure that better evidence could fix; an observation's unknown
condition-date is a *structural* property of observations. The case for keeping
observations out of a dated chronology is therefore stronger than the case for
keeping undated transactions out, not weaker.

**c · The annex is a queue, not a bin.** My §8.1 makes annex membership a tracked
failure, and strict can accept that happily. Annexed observations are exactly the
population a later cross-document phase should work on, because an observed
condition's date is often recoverable from *other* documents — a certificate of
occupancy, a prior deed, an earlier affidavit. Placing them speculatively now
forecloses that, and **a wrong date in the chronology is harder to detect and fix
than an honest absence**, because absence announces itself and a plausible date
does not.

**d · "Four columns routinely empty" is the correct result, not a cost.**
Occupancy, As Built, Value and Permit *should* be sparse in a recording-office
corpus. The registry records transactions and observes physical conditions only
incidentally, on tax forms and compliance affidavits attached for other reasons.
A framework that populates a physical-state history out of RP-5217 use codes is
manufacturing one. The emptiness is itself information: it says the recording
corpus does not know what was built there — which is true, and which a populated
column would conceal.

### 2.2 What would settle it

**The philosophical question has a measurable form, and that is the better
question:** *what fraction of observations in the corpus state a condition-date
distinct from the filing date?* If most observations self-date ("continuously
used as a two-family dwelling since 1974", "as of the date of this survey"),
strict costs almost nothing and (a)–(d) win outright. If almost none do, strict
annexes a large population and the cost is real. This is countable, not
arguable, and it should be counted before it is ruled on.

**Shape O1 — the self-dating observation.** An affidavit or certification whose
text states when the condition began or was measured, filed materially later.
Both rules agree here (place at the stated condition-date), so it does not
discriminate — but its *frequency* is the measurement above.

**Shape O2 — the true discriminator: a document whose entire content is an
observation with no stated condition-date.** Under strict it produces zero placed
events, an empty matrix, and contributes nothing to any chronology. Under my lean
it produces one placed, marked event. **A document that extracts to nothing
placeable is the sharpest possible statement of the cost**, and it makes the
ruling concrete rather than abstract.

*Candidate already in the corpus:* `2003010801527001` — ZONING LOT DESCRIPTION, a
private title-company certification asserting present zoning-lot composition and
100-by-25-foot geometry. From B's `surveyed.md`; **unread by me.** If that
document extracts to an empty matrix, strict has a visible price. If it turns out
to state an as-of date, it is Shape O1 and we need another.

### 2.3 What each answer costs at 25M scale

| | strict (annex) | lean (place at observation date, marked) |
|---|---|---|
| chronology | observations never inject a wrong date | some fraction of physical-state history dated wrong by an unknown interval |
| error character | **honest absence** — announces itself, countable in the `placement` block | **systematic bias** — errors all point one way, post-dating conditions toward filing dates |
| recoverability | recoverable by a later cross-document phase, if built | a plausible wrong date is not detectably wrong later |
| columns | Occupancy / As Built / Value / Permit routinely sparse | routinely populated, partly with compressed dates |

That framing is what moved me: **honest absence versus systematic bias.** Random
error averages out under aggregation; bias does not, and this bias is one-signed
by construction — every observation is placed at or after its condition's true
date, never before.

**Writing this steelman moved me toward strict**, against the lean I recorded in
§9. I am not withdrawing the lean, because you said this one is yours to rule and
because the measurement in §2.2 could still overturn it — if observations
routinely self-date, strict is cheap and the argument is over; if they never do,
argument (d) has to carry more weight than I am confident it can. But you should
know that the side I argued for in §9 is the side I now think is weaker.

---

## 3 · TRANSFER TAX AND RECORDING FEE — THE GAP, CLOSED

You are right that this was mis-posed. It is not a boundary between two
positions; it is a hole. Here is a rule.

**Evidence it has to cover.** From `2002122700153001`'s cover: Recording Fee
`$52.00`, Affidavit Fee `$0.00`, NYC RPTT Filing Fee `$25.00`, NYS Real Estate
Transfer Tax `$2,102.00`, and a mortgage-tax block (County / City / Spec / TASF /
MTA / NYCTA) totalling `$0.00`. From `2003010600117004`: handwritten marginal
`MTGE TAX PAID: $2,000.00` and `MTGE TAX PAID: $42,091.50`.

> **R-FEE-1 · A charge creates no event.** A tax, fee or charge stated in
> connection with recording writes to no cell under any of the eleven functions.
> It is not `COST` — it is not expenditure on the property or a project — and it
> is not `VALUE` — it is not a valuation of the property. It is a fact about the
> transaction with the registry.
>
> **R-FEE-2 · Placement follows what the charge is levied on.**
> - A charge levied on an **act** attaches as a quantity on that act's event,
>   `kind: TAX`: real property transfer tax → the `TITLE` event; mortgage
>   recording tax → the `ENCUMBRANCE` event for the lien taxed. If the act it
>   relates to produced no event, it falls to `filing_charges`.
> - A charge levied on the **filing** — recording fee, filing fee, affidavit fee,
>   page fee — attaches to a document-level `filing_charges` block and to **no
>   event**. It relates to the recording, not to any act, and attaching it to one
>   event of a multi-event document would be an arbitrary choice that looks like
>   a finding.
>
> **R-FEE-3 · Never derive, in either direction.** A charge is never converted
> into a consideration, principal, taxable amount or value, and none of those is
> ever converted into a charge. The rate is not in the document. (A R-NEV-9,
> B FR-NOINF-008.)
>
> **R-FEE-4 · Zero is a value; blank is not.** A printed `$0.00` on a completed
> charge line is `USD 0.00`. An empty charge line is `UNKNOWN`. (B FR-QTY-004.)
>
> **R-FEE-5 · Marginal tax stamps are charges.** A handwritten or stamped
> `MTGE TAX PAID $n` in a margin is a charge under R-FEE-2 with `src: MARGIN` and
> `author: UNKNOWN`. It never overrides a printed charge at the same rank, and it
> is not evidence of the lien's amount.

This refines my reconciliation §5.1 recommendation rather than restating it:
§5.1 said "quantities on the operative event", which has no answer for a
recording fee on a five-event document. R-FEE-2's act/filing split does.

Two consequences worth stating so they are not discovered later. **R-FEE-3 is the
rule that forbids the one derivation everybody will want**: on
`2002122700153001` the NYS transfer tax of `$2,102.00` resolves the ambiguous
handwritten sale price exactly, at $2 per $500 — and the rate is nowhere in the
document. That inference is the single most tempting one in the corpus and it
must stay closed. And **R-FEE-1 leaves `COST` with almost nothing to do in a
recording corpus**: under B's split, which I accepted, Cost is construction,
renovation, repair, operating and professional expenditure, and a registry sees
those only in building loan agreements. If `COST` turns out to be empty across
the first several rounds, that is a finding about the corpus rather than a defect
in the rule — but it should be watched, because a function that never fires is
the kind of thing that gets quietly repurposed.
