# LEGAL INSTRUMENTS — EXTRACTION

> **BOOTCAMP GOVERNS THIS FILE.** Every function, mode, event row and vocabulary
> used here is defined in [`Bootcamp.md`](../../Bootcamp/Bootcamp.md) - the ONE authority.
> Never redefine a term in this file; correct it there and it corrects
> everywhere. A rule that is not in the bootcamp is not a rule.


**This document is the source of truth for producing a legal instruments
extraction.** An agent runs this phase from this file alone.

# OVERVIEW

**The job:** turn each acquired document into its EVENTS. Extraction searches
the document, raises CLAIMS about what it says, verifies claims into events —
each carried by **subject × function × mode + quantity + term** — writes them
into the data tables, and gives EACH EVENT its own summary. A
single document can carry multiple events. The ladder is
`claim -> event -> account -> inference`; extraction owns the first rung and
the verification into the second — chaining and inference belong downstream.
**The boundary, upstream:** extraction reads the acquisition table and the
key folders — never the network. It intakes only behind Acquisition's closed
count, and it inherits the lag column: `pending` docs are simply not here yet;
`imageless` docs contribute index-only events.
**The boundary, downstream:** 04 Resolutions receives events and summaries
and chains them per key — into TIME chains and FUNCTION chains; 05
Derivations then turns chains into output metrics and MACRO summaries.
Summaries live at two altitudes and each phase owns one: extraction writes
the EVENT-level summary (this document, decoded); derivation writes the
CHAIN-level summary (this parcel's story, measured). Extraction never
chains; it only produces the links.

**⚠ THIS PHASE IS UNIQUE: it has a PREP PHASE — the BOOTCAMP — before it can
run at scale.** Every other phase's method was executable on day one; this
one must first be TRAINED into a bootcamp. The phase therefore has two lives:

1. **BOOTCAMP (frontier model, small scale):** feed parcel-keyed documents
   OLDEST -> NEWEST into the strongest available reader. Every document it
   handles correctly confirms vocabulary; every miss becomes a guard, a rail,
   or a vocabulary entry. The accumulating product is **THE BOOTCAMP** — the
   document that lets a lesser model do this job.
2. **PRODUCTION (open model, full scale):** an open model runs the bootcamp
   at concurrency. The corpus is ~17M documents; production is only possible
   parallelized.

**Three preconditions gate production, and the acquisition backfill (weeks)
is the window to close them:**
1. an open model with visual document reasoning at frontier level,
2. compute access sorted (the parallelization substrate),
3. the workflow optimized across time, cost, and accuracy — measured, like
   every parameter in this system.

**Bootcamp runs DURING the acquisition backfill — the phases overlap on
purpose.** It starts the day the first parcels close (it needs documents, not
the whole corpus), and every week of the backfill is a week of training. The
target: the day acquisition finishes, the bootcamp is converged, the gates
are measured, and production starts immediately — zero idle time between
phases.

**The parcel is the unit of flow — this is WHY the corpus is keyed by BBL.**
A finished parcel holds every document a chain needs, so completion CASCADES
per parcel: acquisition closes the parcel -> extraction runs it bottom to top
-> every documented event and event summary exists -> resolution chains it
(chronology and function) -> derivation writes its outputs and inferences —
all while the rest of the corpus is still pulling. Keyed randomly or by doc
type, events would scatter across unfinished sets and no chain could form
until acquisition completed EVERYTHING. The per-key nested check (§3) is this
principle enforced.

---

# 1 · OUTPUT

**Per document, three artifacts:**

1. **Claims** — every reading, kept with its conditions (which reader, which
   page, which region). Claims are the evidence layer: they can DISAGREE, and
   a better reader can settle them later because they are still there.
2. **Events, in the data tables** — a claim set that agrees verifies into an
   event row in the fixed column order **`mode · subject · function · from · to ·
   quantity · term`**, anchored to `document_id + page`.
   Those seven are the CONTENT. The full table is **eleven columns in three
   groups, and it never grows**:

       IDENTITY     event_id | row
       PROVENANCE   doc_id | page | recorded | executed
       CONTENT      mode | subject | function | from | to | quantity | term

   The row is the unit — a multidirectional transfer is several ROWS sharing
   one event id, never several events. Facts refuse to exist without an anchor.
   - **Two tables, and only two.** CLAIMS is open and free-form so it can
     absorb whatever any source prints; EVENTS is closed and controlled. Every
     event column is a controlled vocabulary, a reference, a value with a unit,
     a typed duration, or a timestamp — **no column is free text**, which is
     exactly why a new document type cannot force a new column.
   - **Opposite-direction functions are separate rows (G-018).** A mortgage
     moves CAPITAL lender→borrower and ENCUMBRANCE borrower→lender. One row
     would have to lie about one of them. One event id, two rows.
   - **The three tiers, and the SPINE GATE.** `mode·subject·function` is the
     SPINE (always controlled vocabulary, **never `unread`**), `from·to` the
     DIRECTION, `quantity·term` the MEASURE. **If any of mode, subject or
     function cannot be determined, there is no event — it stays a claim.** The
     measures may be unread because a document can change the world without
     stating an amount; the spine cannot, because a change you cannot name,
     about something you cannot name, is not a change you observed.
   - **`subject` has three types: `parcel`, `entity`, `class`.** Class is what
     lets a rule-level source in — a zoning text amendment or a tax-code change
     is ONE event on a class of lots, fanned out to members at 05 Derivations,
     never copied per-parcel at extraction.
   - **When a split is unread, write ONE aggregate row (G-021)**, marked
     `split: unread`, with the set in `from`. Never divide evenly to reach N
     rows — and never compute a per-sender rate off an aggregate row.
   - **A consolidation is closing rows plus one opening row (G-022).** New money
     is COMPUTED as `opening − sum(closings)`, never taken off the face.
   - **A document type is a CLAIM, not a schema.** Anything meaningful only
     inside one source's vocabulary — instrument form, statutory cite, permit
     sub-type, exemption code — is a claim. A new source adds ROWS and one
     small mode+function dictionary stored in its own md; never a column.
   - **mode** is the settled vocabulary `transacts` / `observes` / `signals`
     — did the world change, was state merely recited, or is this an
     interested party's intent. It is NOT the instrument form; the form
     ("bargain and sale, with covenant") is an attribute beside doc type.
     Mode is assigned **per event**, because one deed carries all three modes
     at clause level, and **only `transacts` may assert that state changed**.
   - **subject** is what the event is ABOUT (the parcel, or the entity for
     party-keyed events) — not the routing key.
   - **quantity**: an amount always exists. Bound it when it cannot be exact
     (`$10 recited, <= $500 by stamp`); `unresolved` alone is a failure to
     read, not a property of the document.
   - **term** is the duration or estate, and is **never blank on a title
     event** — the granting clause states it (fee simple absolute, life
     estate, leasehold with years). Encumbrances take their term from their
     release condition.
   - **from / to** carry the direction of the FUNCTION, not of the money:
     `from` parts with what the function names, `to` receives it (the
     doc-type authority declares both). `observes` events have no direction —
     from/to are `n/a`.
   - **The summary is generated from the row, mechanically:** *[from]
     [function verb per mode] [quantity] of [subject] to [to], [term]*. If the
     sentence cannot be written from the row, the ROW is wrong — never patch
     the sentence.
   - **quantity and term are the two slots that may legitimately be ABSENT**,
     and absence must be distinguished from failure. Each takes exactly one of
     three states, never a blank: **a value** · **`n/a` + the reason this event
     kind has none** · **`unread`** (it exists, we failed to get it). `n/a` is
     a claim about the event; `unread` is a claim about us — collapsing them
     destroys the only signal that says whether to go back. Quantity always
     carries its UNIT (money · area · share · count); term always carries its
     KIND (estate · duration · maturity · condition). **An event with both
     slots `n/a` is suspect** — it is probably a recital or a reference, not an
     event, and is inspected before it may enter a chain.
3. **The event summary — ONE PER EVENT, not one per document.** Every event
   carries its own written statement of what it did; a document with three
   events owes three summaries. The data row and the summary are the two
   tracks of the same event and travel together — never a table row without
   its sentence, never a sentence without its row.

**Terminal states — every acquired document concludes in exactly one:**

| state | meaning |
|---|---|
| **extracted** | events in the tables + summary written |
| **escalated -> extracted** | the working model missed; the highest model resolved it |
| **unreadable** | the highest model could not make the data out — an honest, terminal, HUMAN-VISIBLE state |
| **unresolvable** | readable, but the content fits no event — listed for review, never forced into a table |

The state column is never blank, and the exact-sum identity holds over the
population that is actually here:

    extracted + escalated + unreadable + unresolvable
    = every LINKED or IMAGELESS document handed off by Acquisition

`pending` documents are OUTSIDE the sum — they have no file yet; they ride
the inherited column and enter the identity the run after they flip. An
`imageless` doc extracts from its index row alone and counts as extracted.

**Scale & home:** the claims, tables, summaries, and bootcamp live in this
source folder; everything up to and through this phase stores on the corpus
drive. (Cross-phase storage architecture — drives, database, backup — belongs
to the system md.)

**The bootcamp's own output is THE BOOTCAMP**, and it is a living document in
this folder:
- the **vocabulary ledger** — every subject/function/mode term MEASURED, with
  denominators mandatory (`rate: unread — no extractor yet` predicted the
  fabricated 6.0% interest rate; the ledger's honesty is a safety device);
- the **guards and rails** — one entry per miss, stating the failure, the
  document that taught it, and the rule that prevents it;
- **`canon()` — the ONE normalizer.** Every term passes through it; two
  spellings of one function are one function.

**⚠ THE SAFETY LAW, above every other rule: NEVER MAKE INFORMATION UP.**
An empty cell beats a plausible fabrication, every time. A value no reader
can support does not get written — it becomes `unresolved` on the claim
layer with its distribution visible (e.g. `{732491: 5, 732441: 2}`), or the
document goes `unreadable`. Plausible-and-wrong is the only unrecoverable
failure this phase can produce, because downstream phases BUILD on it.

---

# 2 · METHOD

## The bootcamp loop (prep phase — the bootcamp is built here)

1. **Pick a parcel; read its folder OLDEST -> NEWEST** via the `_INDEX` —
   chronology is the teacher: the 1971 deed teaches the vocabulary the 1998
   mortgage assumes.
2. **Extract:** raise claims, verify events, fill the tables, write the
   summary — using only the bootcamp as instructions (the frontier model
   plays the role the open model will later hold; what it needs beyond the
   bootcamp is what the bootcamp is missing).
3. **Verify against the index** (see the verifier table below) and against
   the document's own arithmetic where it self-validates (tax stamps,
   consideration sums — respecting known exemptions).
4. **Every miss becomes bootcamp:** a guard (never do X), a rail (always do
   Y), or vocabulary (this phrase IS that function). One entry per miss,
   citing the teaching document.
5. **Loop until dry:** when N consecutive parcels add nothing to the
   bootcamp, the vocabulary has converged for that document population —
   record the denominator (which doc types, which era) and widen the
   population. Convergence on Greenpoint deeds is NOT convergence on
   microfilm mortgages: a reader proven on one corpus is not proven on
   another.

## The bootcamp mechanics — how a stateless agent learns

**The agent cannot learn; the bootcamp is the learning.** Every session
starts cold and must reach full competence from the files alone. Four
mechanisms enforce it:

1. **The cold-start test (the phase's meta-check):** a fresh agent given only
   this md + the bootcamp must extract as well as yesterday's agent. Run it
   on a schedule; a drop on restart means competence was living in a
   conversation instead of the files — that leak IS the hole. Fix by writing
   the missing knowledge down, never by keeping the session alive.
2. **Constitution vs case law:** this md holds the rules that never change;
   the bootcamp holds what converges. Every bootcamp entry uses one grammar —
   **the failure + the teaching document (anchored) + the rule** — a
   calibration, never a bare config: a bare rule gets re-litigated, a rule
   with its reason does not.
3. **Addressability:** the bootcamp is structured BY THE SLOT IT PROTECTS
   (per doc type, per field), and step 2 of extraction names which sections
   to load for the document at hand. A rule the agent does not read at the
   right moment does not exist — unaddressable is indistinguishable from
   unwritten.
4. **The gold set — iteration that cannot regress:** every teaching document
   becomes a permanent regression test with its known-correct extraction. Any
   bootcamp change re-runs the gold set: everything previously correct must
   stay correct, or the change is rejected. And the BACKWARD RE-CHECK: when a
   new trap is found, re-run it over every earlier extraction — prior work
   was judged by rules that predate the lesson, so it looks cleanest exactly
   where it is most likely wrong.

## Reading channels — where independent readings come from (measured)

Agreement needs INDEPENDENCE, and independence is manufactured, not assumed:

- **One look is never a reading.** Two agreeing runs at one size are ONE
  look. Vary size AND crop before believing a value (measured: `732441` read
  identically twice at one scale and differently five times across 900–2000
  px — the stable answer was the second one).
- **Channels catch each other's failure modes:** the VLM reads what OCR
  cannot, but the VLM also FABRICATES structure (section labels) that only
  the weaker OCR channel can refute. Neither channel is the referee alone;
  never align channels line-by-line.
- **Never ask a model to reconcile or rewrite a page** — measured +0/−12: it
  fixes nothing and damages what was right. Reconciliation is arithmetic over
  claims, done by code, not by a model.
- **A dead server is not a reading.** One crash poisons every later request
  in the slot, and a column of errors reads like evidence. Restart between
  configurations; treat identical repeated failures as harness, not corpus.

## The extraction rules (both lives, non-negotiable)

- **Claims hold disagreement; events cannot.** An event resolves only on
  agreement between independent readings; otherwise the field stays
  `unresolved` WITH its distribution. Unresolved is a STATE, not a bucket.
- **Never show a reader a candidate value for the field it is reading** —
  priming transfers the error. A pointer to a REGION is allowed; a value is
  not.
- **Anchor every fact:** no event enters a table without `document_id +
  page`, and a claim is gated on its anchored line's region — a page-level
  gate once built a BBL from a reel number.
- **Extract only what has a slot** in mode/subject/function/quantity/term —
  a value with no home costs rounds and buys nothing.
- **NEVER INVENT A VOCABULARY.** Functions, modes and their aliases live in one
  place and resolve through `canon()`. A column filled with locally invented
  values looks correct and silently prevents every downstream grouping —
  measured twice in one day (a second canon map, then modes written as
  instrument forms).
- **Capture the internal-vs-external evidence on every conveyance** — name
  match, entity match, mailing-address match, signature/officer match, and any
  corporate-authority recital. Whether a transfer is INTERNAL is an inference
  for 05 Derivations (and it decides whether the price is a comparable at all);
  extraction records the five tests as claims and never rules.
- **Multiple events per document is normal — and an event is N-LEGGED, not
  two-sided.** Every event is a set of LEGS: (subject, role, direction,
  quantity, share). Two legs is just the simple case (transfer: -SF sender,
  +SF receiver). The real corpus is multidirectional: an air-rights deal can
  be 9 legs (8 sending lots, each with its OWN unique SF and $ apportionment,
  one receiving lot); a deed can carry multiple equity partners as fractional
  grantee legs (50/25/25); an RPTT can state one lot's specific share of a
  combined value. Direction, role, effect, and SHARE are first-class from the
  start.
- **THE BALANCE INVARIANT — the event's own arithmetic:** legs must balance.
  SF out = SF in; fractional interests sum to 100%; per-lot apportionments
  sum to the stated total ($40M split 8 ways must re-add to $40M). An
  imbalance is `unresolved`, never forced — and a split the document does NOT
  state stays unresolved WITH the total known: pro-rata is never assumed,
  because an invented split poisons every per-lot economic figure downstream.
- **Extraction preserves; derivation classifies.** Whether a mortgage is
  land, construction, bridge, operating, refi, or distressed is usually NOT
  written on the instrument — it is an INFERENCE built later from multiple
  sources (the permit that witnesses a construction loan, the payoff pattern
  that witnesses a refi). Extraction's duty is to preserve the raw features
  that make that inference possible — amounts, terms, lender, building-loan
  references and affidavits, what the money touched — verbatim and anchored.
  A feature dropped here is an answer derivation can never give.
- **A document extracts ONCE.** A multi-key document's events serve every key
  that references it — extraction is per document, chains are per key, and
  double-extraction would double-count in every chain downstream.
- **Every extraction is stamped with the BOOTCAMP VERSION that produced it.**
  The backward re-check is only possible because of this stamp: when a new
  trap lands, the re-check targets exactly the documents judged under older
  versions — without the stamp, "which docs predate the lesson" is
  unanswerable.

## The index as verifier — trusted where measured, never blindly

**THE TRUST LEDGER (settled 2026-08-20): the verdict table below is a PRIOR,
not a constitution.** Every extraction run measures the register: each
field-level comparison (document value vs register value) lands in a
per-field x per-doc-class agreement ledger with denominators. Verifier
weight follows the LEDGER - a field is a good checker exactly to the degree
its measured agreement rate says so, per class, re-measured as the corpus
is read. "Parties verify well" must become "parties agree N% of M
comparisons on DEEDs" or it is an opinion wearing a verdict's clothes.
The run stamp carries the ledger's movement; a field whose agreement rate
DROPS is a finding about the register (or about the reader) either way.


| index field | verdict as verifier |
|---|---|
| parties | **GOOD** for entity verification — the recorded names check extracted parties |
| doc type | **WEAK** — documents are mislabeled and misfiled at the source; a mismatch is a flag, never a veto. Mislabels do not matter downstream IF extraction is clean: the EVENTS carry the truth, and Resolution chains events, not filing codes |
| document amount | ⚠ **ZERO MEANS A DIFFERENT THING PER CLASS (measured 2026-08-20 on 24M docs):** DEED $0 = real state - candidate internal/no-consideration transfer, note it, verify via stamps; DEVR $0 = the register failing to carry the stamps' price - NEVER verifies (49.7% of DEVRs do carry a number - the old absolute "amount=0 for every DEVR" is REVISED); MTGE amount is a keeper (85.6% real principal, $0 = anomaly flag); SAT/ASST/PAT/INIT/TERM/INIC carry no amount field at all - 100.0% structural zero, omitted at nav. Original note: **KNOWN FALSE for whole classes** — the index says $0 for every DEVR (price lives in the transfer-tax stamps, not the recital: the $10 recital is a 500,000x trap) |
| recorded date | good for chronology; the doc's own execution date can differ and both are events |


**Settled 2026-08-20 (login): the DOCUMENT is the source of truth; the index
is a SECONDARY verifier of the pdf analysis.** The model reads the document
cold and extracts the events; the index then checks the extraction. Three
consequences:

- ⚠ **VERIFY AFTER, NEVER PRIME.** The index value is never shown to the
  model before or during its read - same rule, same reason as the OCR
  candidate ban (primed with `73241` the model answered `732491` twice;
  priming transfers the error). The comparison happens OUTSIDE the model,
  after the cold read. An uncertain party name is the canonical use: the
  cold read produces a candidate, the index confirms or disputes it, and a
  dispute stays at CLAIM level with both recorded - the event resolves only
  on agreement.
- **The index can be wrong, and extraction is how we find out.** A verified
  disagreement is a FINDING about the index (mislabel, truncation, role
  case), logged with document_id + field, not silently overruled in either
  direction. ⚠ Role DIRECTION is the known blind spot: grantor<->grantee
  inversion scores 100% on name-matching and reverses the lineage - names
  verify names; direction is verified only by the document's own grant
  language.
- **Some facts are not in the index at all, by design.** Price lives in the
  cover-page tax stamps; the SF quantity lives in an exhibit; terms live in
  the body. For those the index is silent and the document stands alone -
  absence of index corroboration is NOT a strike against the reading.

**THE BRIEFING — overview, analyze, conclude (login design, 2026-08-20).**
The recorded_details row is not only a post-read verifier; it FRAMES the
read. Before the model opens the document it receives a briefing rendered
deterministically from the row plus the trust ledger — a thesis of what this
document claims to be and what must be established: "a DEED recorded
2026-08-19, Queens condo unit, one grantor, three grantees, $0-recital
class — establish consideration from the cover stamps; cites one prior
instrument — confirm the citation." The login's DEVR example is the model
case: the briefing says "the register reports $0 and a DEVR's register
amount NEVER verifies — find the actual consideration," so the model walks
in knowing the register's blind spot instead of piecing the document
together from scratch. Overview (the briefing) -> analyze (the read) ->
conclude (the event rows).

⚠ **THE BRIEFING CARRIES SHAPE AND TASKS, NEVER CANDIDATE VALUES for fields
the read must establish.** Counts, classes, dates-of-record, per-class trust
warnings: in. The party NAMES, the amount figure, the quantity: out — those
are exactly what priming transfers errors into (the register missed ZHENG,
NINA on the very deed that proved the party gap; a primed model inherits
that miss, and role inversion rides in the same door unseen). The values
meet the extraction OUTSIDE the model, field-by-field, after the cold read —
where a dispute becomes a logged finding instead of an inherited error.
Same rule, both directions: the briefing aims the model's attention; it
never lends the model its answers.

**NAMING (updated 2026-08-20, final):** the nav column is `recorded_details`
(the login's name for the contract: recording information + parties +
parcels + references + remarks + the measured exceptions), superseding
`doc_info`; both sources still title the page "Document Information".
In prose here, "the index" and "the register's entry" mean the same thing:
THEIR voice about the document, never ours. The register LOCATES the
document; only extraction says what it did - the register is one line, the
document is quantities x parties x conditions moving over time (the Domino
Exhibit J: 2,131,871.50 SF allocated pro-rata across five premises, the
actual 215,858 SF transfer living in footnote iii, the whole schedule
"deemed modified" as rights move - three dimensions no register line can
hold; this is why decoding exists).

**The index was WIDENED 2026-08-20** (see the Navigation md - the nav table's
`index` column now carries the custodian's whole detail page). New verifier
material this adds:

| new index field | verdict as verifier |
|---|---|
| remarks[] | **GOOD** - exemption affidavits live here; this is the field that stops the 1.5% mortgage-tax check falsely flagging HECMs/CEMAs |
| parcels[].partial / easement / air_rights / subterranean | ⚠ **ASYMMETRIC - Y is signal, N is noise** (corrected same day: first written "GOOD as flags"; the Domino DEVR refuted it - AIR RIGHTS reads N on every lot of a document whose entire purpose is moving 215,858 SF of development rights). A Y earns attention (26,768 air-rights Ys corpus-wide); an N establishes NOTHING - no event field, no filter, no gate may key on a register N |
| references[] | **GOOD for Resolution** - the custodian's own chain candidates (11.9M edges); extraction checks the document cites what the index says it cites |
| parties[].addr | **GOOD** for entity disambiguation - two SPEs sharing a name rarely share an address |

**Settled 2026-08-20 (login): the extraction row CARRIES the doc type.**
Each extracted event records the index's doc type beside the event columns
(doc type is CONTEXT from the index, never an extracted fact - Bootcamp
remains the authority for the event columns themselves):

    doc_type | mode | subject | function | effect | from | to | quantity | term

Why: the index stores ACRIS's raw code (`DEVR`, `MCON`), and
`_doctype_codes.json` - ACRIS's own 126-type control table - holds the full
label (DEVELOPMENT RIGHTS). With the type on every event row, the
type -> function co-occurrence becomes a MEASURED ledger as extraction runs:
"DEVR carries transfer+release in these proportions, with these
denominators." Resolution then chains on measured pairings instead of
assumed ones, and the ledger runs BACKWARDS too - a document whose extracted
functions sit far outside its type's measured distribution is either a
source mislabel (known to happen; type is a WEAK verifier, above) or a
genuinely unusual instrument, and both are worth surfacing. This is the
same move as every other vocabulary here: never assumed, always counted,
denominator mandatory.

## Escalation (the miss clause)

    working model extracts -> verified?           done: `extracted`
                       -> miss/conflict?     escalate one tier up
    escalation tier resolves                -> done: `escalated -> extracted`
    escalation tier cannot make it out      -> done: `unreadable` (honest)
    readable but fits no event              -> done: `unresolvable` (listed)

**The model ladder differs per life.** Bootcamp: the frontier model IS the
worker (it is both teacher and escalation). Production: the working tier is
the mid-size open model; the escalation tier is the highest-parameter open
model — only IT may declare `unreadable`.

Escalation is a RATE to track (the run stamp carries it): a rising escalation
rate says the bootcamp has a gap or the corpus changed population; near-zero
escalation says the open model is ready for more of the corpus.

## Production (after the gates)

Production has two duties: the BACKFILL (the corpus, parallelized) and the
NIGHTLY DELTA — each morning's newly acquired documents run through
extraction the same night, so the wake-up-fresh chain holds through this
phase. Same model, same bootcamp, same rules for both.

The open model, the bootcamp, the same rules, at concurrency on the
parallel-compute substrate. Parameters (model, concurrency, cost/doc,
accuracy floor) are **UNSETTLED** — they are the bootcamp's exit measurement,
written here when measured, with the same honesty as every labeled parameter
in this system.

| | current thinking (candidates, NOT commitments) |
|---|---|
| substrate | storage through this phase on the corpus drive (20 TB); extraction compute on the parallel cluster (Torch) for concurrency |
| working tier | best open VLLM at reasonable parameters — candidate: Qwen ~27B class |
| escalation tier | highest-parameter open model — candidate: Kimi K3 class |
| status | ALL subject to change at bootcamp exit; the target is optimized across time × cost × accuracy, measured |

**The run stamp — every run leaves one measured line.** Each run appends one
line to the phase's run log: when, mode (bootcamp/production), documents
processed (count / denominator), events raised, escalation rate, unreadable
and unresolvable counts, bootcamp entries added. A drifting rate is the first
sign the bootcamp has aged.

---

# 3 · CHECK — every document concludes, nothing invented

1. **The exact sum:** `extracted + escalated + unreadable + unresolvable =
   every linked or imageless document handed off` — states live in ONE
   column; `pending` sits outside the sum until it flips; the remainder is a
   LISTED failure set, never a bucket.
2. **The anchor audit:** sample events back to their pages — every fact
   resolves to `document_id + page`, and the page supports it. A fact that
   cannot be traced is removed and its document re-runs.
3. **The fabrication guard:** no event value exists without a supporting
   claim; no claim exists without a reading that produced it under recorded
   conditions. Spot-check unresolved distributions — an `unresolved` that
   quietly became a value without new agreement is a violation.
4. **Denominators on every rate** — "98.6%" means nothing without "of 73
   artifacts across 4 pages." Bootcamp convergence is only claimable for the
   population it was measured on.
5. **The lag pass-through:** `pending` documents are NOT misses — they are
   tomorrow's extractions, visible in the inherited column, and they do not
   block the check for the population that is here.

6. **The receipt invariant:** every `extracted` document carries at least
   one event, and **every event carries exactly one summary** — "extracted" is
   never an empty label, and no event row travels without its sentence.
   Every unresolved field inside an extracted document travels AS unresolved,
   with its distribution — Resolution must never receive it as a value or as
   zero.
7. **The check NESTS PER KEY, and handoff is per key:** a key whose linked
   and imageless documents have all concluded hands its events to Resolution
   immediately — the corpus does not wait for itself. Corpus-level handoff is
   simply the day every key has closed.

Only a closed count with a clean anchor audit hands off to 04 Resolutions.

---

# 4 · HANDOFF — the phase when said and done

04 Resolutions receives, per key, the ingestion interface of this phase:
one event record per document (doc id -> its events, its summary, its state,
its bootcamp version) — the event data tables (subject × function × mode +
quantity + term, anchored), the event summaries in chronological order, and
the honest remainder states (`unreadable`, `unresolvable`, `pending`,
unresolved fields WITH their distributions) riding alongside so no chain
silently spans a gap it cannot see or treats an unknown as a zero.
Resolution turns events into chronological chains and functional chains —
extraction has already made the links strong enough to bear that weight, and
the bootcamp stands as the record of how, ready to train the next reader.

---

*The bootcamp is the prep phase; production parameters are UNSETTLED until it
exits. Prior measurements carried in from the decoder work (OCR/VLM findings,
the priming trap, the anchor rules) hold until re-measured on this corpus —
the numbers age; the reasons do not.*

---

## 2026-08-21 — THE DATA ACCESS CONTRACT (settled; the decode approach is not)

**Where extraction gets its data — settled today:** it refers to the
**Legal Instruments DB** (`D:\CRE Decoding System\Legal Instruments.db`,
one `navigation` table). It moves through doc ids **BY PARCEL** — the
organization phase's `key` column groups every document onto its BBL(s) —
and for each document uses the two payloads acquisition landed:
`recorded_details` (the structured page, parsed) and the attached **pdf**
(path in the `pdf` column, file under `By Document\YYYY\MM Mon\DD\`).

    SELECT id, recorded_details, pdf FROM navigation
    WHERE key LIKE '%<bbl>%' ORDER BY id      -- one parcel's documents,
                                              -- recorded chronology

That is the whole input surface: no network, no other store. Upstream
guarantees it inherits: every id present (the censuses closed both
custodians), every row url-minted (structural), keys custodian-asserted
only (the key_rules trigger).

**What is NOT settled — deliberately:** the best time / cost / accuracy
approach for the analysis itself. That is the BOOTCAMP's question
(`D:\CRE Decoding System\Bootcamp\Bootcamp.md` — the one extraction
authority) and it gets answered by measurement, not by choosing here.
This section only fixes how the data arrives to whatever approach wins.

**The output — Legal Instruments Decoded DB (login 2026-08-21):** extraction
reads the Legal Instruments DB and writes `Legal Instruments Decoded.db` —
a SECOND database, because the shape changes at this boundary: the record
is one row per document; the reading is many rows per document (events,
tiers, quantities, per the Bootcamp's tables). Phases 04–06 build the
decoded db the way 01–03 built the record db; the doc id + key carry
across as the join.
