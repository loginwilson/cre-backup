# RECONCILE — A, on B's draft

Written after reading `drafts\B\` in full and before seeing B's reconciliation.
My own draft is frozen; everything here is a proposal for v1.

Headline, stated once so it does not have to be inferred from the length of §3:
**B's draft is better than mine on the model and worse on the inputs.** B built a
real state model — object identity, fold semantics, conflict handling, ordering
discipline — where I built a serialisation format. I built the registry and
package rules B has none of. I concede more than B does below, and I think that
is the correct outcome rather than a concession I am making to be agreeable.

---

## 1 · THE FIRST FINDING IS ABOUT THE CORPORA, NOT THE RULES

Before any rule difference: we surveyed **different axes**, and almost every
difference below traces to that rather than to reasoning.

| | A | B |
|---|---|---|
| documents read | 10 (8 in depth) | 15 (all pages of each) |
| id namespaces | ACRIS-digital, **`FT_` film, `BK_` book, `RC_` Richmond** | **ACRIS-digital only** — all 15 ids are `2002…`/`2003…` |
| selection axis | package and registry shape | legal-act shape |
| overlap | `2002122000002001`, `2002122700153001`, `2003010600065002`, `2003010500041001` | same four |

B read a subordination agreement, a maturity-date correction, a two-BBL deed
with an unallocated joint total, a 99-year ground lease assignment, a condo
declaration amendment, and a zoning-lot certification — six hard act-shapes I
never saw. I read a 1981 film declaration, a 1966 bound-book assignment, and a
Richmond cover page — three input shapes B never saw.

This is why B's framework has richer act taxonomy and no package rules, and why
mine has package rules and a thinner act model. It is also why the
orchestrator's item 3 lands harder on B's draft than on mine: **B's draft keys
module selection and evidence rank on `registration["type"]`, a field that does
not exist in the Richmond schema.** That is a corpus artefact, not carelessness,
and my own `draft-notes.md` §4 recorded the mirror-image weakness in mine — that
my survey was "badly skewed toward ACRIS-digital 2002–2003" on the act axis.

**Proposal for every later round: the two of us should not choose from the same
stratum.** The `slate.py` facets make that enforceable.

---

## 2 · WHERE WE AGREE

Stated once, briefly, because agreement is not the interesting part and TRAYCER
#5 says it is where nobody is looking.

Independent reading; no imported state from a referenced instrument; recitals of
earlier acts are references, not events; one clause may yield several events
across functions; filing date is not event date; shares are never inferred;
lumped totals are never allocated; blank ≠ zero and blank ≠ none; four semantic
nulls with distinct jobs; every field carries a quote or a named rule with named
inputs; flags are for ambiguous documents, not for hard rules; a metes-and-bounds
description used only to locate another event's premises is parcel scope, not an
Identity event; parcel roles are asymmetric and must not be recorded
symmetrically; panel/column order does not establish a party role.

We also independently reached the same three conclusions on the four documents
we both read, which is the only clean signal in this comparison: the $366,000 in
the satisfaction is the referenced principal and not this act's quantity; the
deed's $10 and the transfer report's $525,500 are different quantities rather
than a conflict; the façade easement burdens land **and** constrains physical
form. Two readers, no contact, same answers — worth recording precisely because
under TRAYCER #5 it is the least examined part of the round.

---

## 3 · WHERE B IS BETTER — I CONCEDE

### 3.1 `state_object_key` (B FR-REC-004) — the single best thing in either draft

I have **no equivalent**. My events carry a function, a mode and a serialised
payload, with no identity for the thing being acted on. That fails the moment a
document touches two mortgages: my matrix cannot say which one a satisfaction
terminates, and my `+`-joined cell string is a list of events, not a state.

B's five-step key ladder (recorded identifier → instrument-local name → express
within-document anaphora → agreement-scoped → local ordinal) is mechanical, and
the anti-merge clause — "Do not merge two keys because parties, amounts, dates,
or parcels resemble one another" — is exactly the discipline mine lacks.

**Adopt B's FR-REC-004 whole.** This is the change that makes the rest of the
matrix work, and everything in §3.2–§3.5 depends on it.

### 3.2 The empty cell is UNKNOWN, not NO_CHANGE (B FR-NULL-007, MX-SCOPE-003, MX-FOLD-001)

My rule: a cell no clause writes to is `NO_CHANGE`. **This is wrong and it is the
most consequential error in my draft.**

Reading one document alone, silence about Occupancy is not evidence that
Occupancy did not change — it is absence of evidence. `NO_CHANGE` asserts
continuity from silence. Across 25M documents that manufactures a false
"nothing happened" signal in every column a document does not touch, which is
most columns on most documents, and nothing downstream can distinguish it from a
real determination.

B's placement is also better on its own terms: `NO_CHANGE` becomes an
**operation** inside a `state_delta` (express "all other terms remain
unchanged"), never a stored cell value — MX-FOLD-012. That gives the fourth null
a real, narrow job instead of making it the default filler, which is what
TRAYCER's four-null requirement actually needs.

**Concede fully.** One amendment, which is a rendering matter and not a semantic
one: my `·` was the only reason an eleven-column table stayed scannable, and B's
MX-SER-007 "do not truncate values" will produce a markdown table no human
reads. Keep B's semantics and render `UNKNOWN / NO_DOCUMENT_EVIDENCE` as `·` in
the **markdown view only**, with the legend stated, `resolved.json` untruncated
and canonical. B's MX-SER-001 already makes JSON canonical, so this costs nothing.

### 3.3 Undated events, and my `sort_date` (B MX-TIME-002/003)

My `sort_date` falls back to the recording date when the event date is UNKNOWN.
I told myself it was "ordering only, never copied into `event_date`". It is
still R-DATE-3 violated one step removed: it places an undated act at a specific
point on the timeline, which is a claim the document does not support, and every
downstream consumer will read row order as chronology.

B routes undated projections to an annex where they cannot touch a dated cell.
That is strictly more honest and it costs only the completeness B names in its
own notes. **Concede.**

B's interval model (MX-TIME-001/003, connected overlap components) is also
better than my `date_precision` tag: a year-precision date becomes a real
interval rather than a date with an asterisk. B's own note 7 identifies the cost
— one broad year interval can bridge many precise dates into one uncertainty
batch — and I have no better answer, so I would adopt it with that limitation
recorded rather than invent one.

### 3.4 Serialisation order is not legal order (B MX-TIME-005/006/007, MX-QC-004)

My M-TIE-2 orders events within a cell by mode index, so `CREATE` always renders
before `TERMINATE`. That reads as a sequence, and I never said it was not one.
B separates the two explicitly, requires an express sequence term for any real
ordering, and enforces it with MX-QC-004 ("serialization order alone never
appears as order_basis"). **Concede.**

### 3.5 Conflict inside a cell (B MX-FOLD-010) and the source-rank table (B FR-EV-009)

I have no within-cell conflict handling at all — my cells concatenate. B's "two
non-identical outcomes for the same object/path in one unordered group are
CONFLICT, and do not apply last-write-wins using page order, function order,
mode order, or event id" is the rule I should have written.

B's FR-EV-009 field-class rank table is likewise better than my binary
R-INP-8 (cover controls indexing, body controls the act). B's five field classes
— and particularly routing tax-report values to the executed transfer report at
rank 1 — resolve cases my binary split leaves undetermined. **Adopt B's table**,
with the per-field admissibility amendment in §4.2.

### 3.6 MX-QC-003 — reversing input order must produce byte-identical output

A mechanical test for hidden order dependence. I have nothing like it, and **it
would have caught my §3.4 error automatically.** Adopt, and I would extend it:
run it as a standing check in every round, not only at implementation time.

### 3.7 Quantity semantics (B FR-QTY-001/002/004)

B's controlled `kind` list with "never type a number from document type alone",
and the no-conflation rule (original principal ≠ current balance ≠ maximum lien ≠
payoff even when the values match), is sharper than my R-QTY-2. B's FR-QTY-004 is
a distinction I missed entirely: *"No new indebtedness"* is `ASSERTED_NONE` for
`NEW_MONEY`, **not** numeric zero. Adopt.

### 3.8 Evidence anchors and quote length (B FR-EV-001)

My R-CIT-3 fixed a coarse zone vocabulary (`TOP·UPPER·MIDDLE·…`) so that two
readers could not disagree about a locator. My own `draft-notes.md` §3 admitted
this "traded verifiability for agreement, which is the wrong direction for a
framework whose whole purpose is to be checked." B's "unique visible anchor" is
right. Likewise B's "shortest verbatim span that proves the value" beats my
arbitrary ≤25-word cap, which I shipped untested and which cannot survive a long
condition. **Concede both.**

### 3.9 The recording date IS the event date when the act is the filing (B FR-DATE-005)

My R-DATE-3 bans the recording date absolutely. B permits it only when the
extracted act *is* the filing — a UCC3 termination's operative effect is
achieved by filing — and guards it with "never because every other date is
absent" plus FR-QC-007, which verifies the basis whenever `effective_date`
equals `recorded_at`. My absolute ban forces UNKNOWN onto a date the document
genuinely supports. **B is right; concede.** B's guard is stronger than my ban
because it is checkable.

---

## 4 · WHERE MY DRAFT IS RIGHT — B SHOULD CONCEDE

### 4.1 The four registration schemas, and package shape (A R-INP-9)

B's framework has no rule for any of: Richmond's `doc_type` instead of `type`;
Richmond's explicit `parties[].role`; Richmond's absent `pages` and absent
`doc_date`; Richmond's bare-BBL parcels (so entire-lot vs partial is **UNKNOWN**,
not `NOT_APPLICABLE`); `FT_`'s complete absence of `doc_date`; the absence of any
cover page at all on `FT_` and `BK_`, where the instrument text begins at p01
with a reel/page stamp in the margin.

Three concrete failures this produces in B's draft as written:

- **FR-SCOPE-004** selects modules by trigger, and FR-NOINF-009 says "registration
  type selects candidate modules". On a Richmond row there is no `type` key. A
  reader that looks it up finds nothing and has no instruction.
- **FR-EV-009** admits "registration" at rank 3 as one undifferentiated source.
  On `FT_` the registration supplies *no* date signal at all, so the rank-3 row
  for event date is empty and the rule never says so.
- **FR-BBL-006** derives `scope` from a partial-lot mark. Richmond parcels have
  no `partial` field, so scope must be `UNKNOWN` — and B's FR-NULL-002 would
  invite `NOT_APPLICABLE`, which is wrong: the lot may well be partial, we simply
  cannot see it.

Adopt my R-INP-9 table, extended with the orchestrator's four-schema detail.

### 4.2 Registration citability is per field, not per blob (A R-INP-7)

B's FR-EV-008 excludes URLs, retrieval timestamps, pipeline metadata, filenames
and preparation metadata — correct as far as it goes — then admits "registration
type, document id, CRFN, recorded time, document date, parties, amounts, and
parcels" wholesale. It does not name:

- **`parcels[].remarks`**, which carries index annotations added by the register
  *years later*: `FT_1000000016200` reads *"…CORRECTED FROM R642 ON 11/14/89"* on
  a 1982 recording. Under B's rule that is admissible at rank 3 as parcel data.
  It is not document content and was not in existence when the instrument was.
- **`image_state`** and **`status`**, which are pipeline fields exactly like
  `at`.

My R-INP-7 is a per-field table and names these. **One correction to my own rule
that the orchestrator's item 3 forces:** I made `remarks` cite *nothing*, and the
orchestrator notes `FT_` remarks carry real cross-references
(`"SUBSTITUTE MTGE REEL 595 PG 713"`). Blanket exclusion discards those. The
right rule is narrower than either of us wrote:

> `remarks` is inadmissible as evidence of the instrument's content or of any
> event field, and admissible only as an **index cross-reference** — an
> identifier pointing at another recording — at the lowest rank, never as a fact
> about the act, and always carrying that it is a register annotation of unknown
> date.

### 4.3 The cover page undercounts the package (A R-INP-2)

B's FR-AMB-006 detects the case where the package has **fewer** images than a
printed total. The commoner and more damaging case is the opposite: the stored
PDF has **more** pages than the cover's "PAGE 1 OF n", because supporting
documents are appended and not counted. `2002122700153001` says "PAGE 1 OF 5" and
has eight images; pages 6–8 are the supporting-document cover, the RP-5217 and
the smoke-detector affidavit, and they carry the sale price, the assessed value,
the use class and the occupancy assertion — four of the eleven columns.

B's FR-REC-001 does say `source_page_count` is the supplied image count "not a
printed cover count", and FR-QC-001 requires every supplied page be read, so B
would not lose the pages in practice. But nothing in B's draft *warns* that the
printed count undercounts, and a reader who trusts it stops early. Add my
R-INP-2 as an explicit warning.

### 4.4 The party index is semantically corrupt, not merely truncated (A R-PARTY-4/5/8)

B's FR-PARTY-009 correctly subordinates cover panels to operative clauses. It
does not warn that the index is actively wrong in two ways I found:

- **Richmond duplicates every party case-variantly.** `RC_1000046` lists four
  party entries for two parties (`SOVEREIGN BANK, N.A.` as both `ASSIGNEE` and
  `Assignee`). A coverage check against the raw list will mis-count every
  Richmond document. Dedup case-insensitively before comparing.
- **The book-era index inverts custodianship.** `BK_6620000200233` indexes
  `"ROBERT OSINOFF CUST OF"` — the *minor* listed as the party with the
  custodian's role appended — where the body reads *"JEROME OSINOFF, individually
  and as custodian for ROBERT OSINOFF … under the New York Uniform Gifts To
  Minors Act"*. The party is Jerome; Robert is not a party at all.

B's FR-PARTY-004 (representatives) handles the *shape* correctly once you read
the body. The addition needed is the warning that the index will disagree, plus
my R-PARTY-8: one name in two capacities is two party entries, and a beneficiary
named only inside another party's capacity phrase is not a party.

### 4.5 Re-render before declaring illegibility (A R-INP-6)

B's FR-EV-007 says transcribe only supportable characters and set the field
UNKNOWN. It never tells the reader that a higher-resolution render is available.
`docpkg.py --page N --dpi 900 --rect …` is a documented tool and the difference
between "illegible" and "legible at 900 dpi" is large on `FT_`/`BK_` film. A
framework that produces UNKNOWN where a zoom would produce a value is buying
agreement by declining to extract — TRAYCER #4 by a different route. Add the
zoom step as a required precondition to any `ILLEGIBLE` determination.

### 4.6 Explicit zero-event outcome (A M-AUTHORITY)

B has no power-of-attorney rule. B's triggers would probably produce zero events
by silence, which is the right answer arrived at by no route. Powers of attorney
are ~2% of my sampled corpus — call it 500,000 documents. "Zero events is a
complete extraction, not a failure" needs to be stated, with a
`no_events_reason`, or readers will invent an Identity or Title event to avoid
returning nothing.

---

## 5 · GENUINE DISAGREEMENTS

### 5.1 Cost vs Value — **I concede to B, and B's rule has a hole**

| | A | B |
|---|---|---|
| consideration, sale price | `COST` | `VALUE` |
| assessed value | `VALUE` | `VALUE` |
| construction / project spend | `COST` | `COST` |

**B is right.** "Value = valuation of the asset, Cost = expenditure on the
project" is a coherent ontology; mine turns COST into a grab-bag of "money that
moved" that means nothing downstream. B's FR-QTY-001 keeps
`NOMINAL_CONSIDERATION` and `FULL_SALE_PRICE` as distinct kinds inside Value, so
nothing is lost by moving them. My own `draft-notes.md` §1.2 already conceded
I had "chosen the rule that is easy to apply over the rule that produces the
more useful column."

**But B's split orphans transfer tax and recording fee.** FR-FN-010 expressly
excludes "tax, recording fee" from Cost; FR-FN-011 does not list them in Value.
FR-QTY-001 has `TAX` and `FEE` kinds with nowhere to attach. On the deed we both
read that is $2,102.00 NYS RETT, $25.00 RPTT filing fee and $52.00 recording fee
with no function.

**Neither of us got this right** — I swept them into COST, B drops them. My
recommendation: `TAX` and `FEE` attach as quantities on the operative event (the
Title transfer) and create **no** function event, because a recording fee is a
fact about the recording, not a state of the parcel. Needs a ruling.

### 5.2 Lease — Title or Encumbrance? **I think B is wrong here**

B FR-FN-002/FR-FN-024: "A lease creation or assignment is Title." Mine:
Encumbrance on the fee, Title only on the leasehold's own indexed BBL.

B's is doctrinally cleaner — a leasehold *is* a possessory estate. The failure is
mechanical, not doctrinal: **in this corpus the indexed BBL is almost always the
fee lot.** B's own survey has `2003010600302005`, a 99-year ground lease assigned
for the remaining term. Under FR-FN-024 that fans a `TITLE / TRANSFER` event onto
the fee lot's BBL. Anything reading the Title column then sees the fee change
hands, when the fee owner did not move.

The estate and the burden are two effects of one act, and B's own FR-PKG-005
machinery is built to emit both. FR-FN-024 forecloses it by fiat.

**My proposal:** leasehold creation/assignment emits `TITLE` on the leasehold
estate (B's key model gives it its own `state_object_key`) **and** a linked
`ENCUMBRANCE` on the fee parcel, same `event_group_id`. Rent stays as terms on
the Title event, as B has it. This costs one event and removes a false fee
transfer. If B disagrees, this needs a ruling — it changes the Title column on
every recorded lease in the corpus.

### 5.3 Dual emission on secured debt — **I concede to B**

Mine (R-FN-3): a secured obligation *always* fires Encumbrance + Capital,
including satisfactions, so the debt column closes.
B's (FR-FN-006): Capital TERMINATE only when the document expressly states the
debt is paid, cancelled or discharged.

B is more evidence-disciplined, and on the document we both read it reaches the
same answer: `2002122000002001` says *"does hereby certify that the following
Mortgage is **paid**, and does hereby consent that the same be discharged of
record"* — express payment, so Capital TERMINATE fires under B's rule too.

My concern from `draft-notes.md` §1.1 survives but is not a reason to override
the evidence rule: if satisfactions commonly discharge the lien without reciting
payment, B's rule leaves the Capital column accumulating debts that never close.
**Proposal instead of a rule change:** track *"Encumbrance TERMINATE without a
paired Capital TERMINATE"* as a per-round metric. If it is rare, B's rule is
right and my worry was theoretical. If it is common, we have measured a real
problem before legislating for it.

### 5.4 Illegible characters and cross-source repair — **I concede to B, reversing my own rule**

My R-INP-6a lets an illegible digit be resolved by adopting the candidate reading
that matches another input, recorded as `CROSS_SOURCE`. B's FR-EV-007 forbids
using registration data to repair legal text and returns UNKNOWN.

On the case that produced my rule — RP-5217 field 12 reading `545,500` or
`525,500`, registration `$525,500` — my rule returns 525,500 and B's returns
UNKNOWN.

**B is right and my rule is unsound**, for a reason B's own draft supplies: the
registration `amount` is presenter-supplied index data at rank 3, and the
transfer report is an executed tax form at rank 1. My rule lets rank-3 evidence
decide a rank-1 field, which FR-EV-009 forbids. My `draft-notes.md` §4 already
recorded a hostile reviewer making precisely this charge and my answer to it was
weak.

**Amendment I would keep:** record the cross-source agreement as a *candidate
note* on the UNKNOWN — "registration states 525500.00, which matches candidate
reading 2 of 2" — so the information survives without being laundered into a
resolved value. And §4.5's zoom step runs first, because most of these should
never reach the rule at all.

### 5.5 B's per-event term population is the bloat trap — **B should concede**

FR-TERM-102 requires every event to populate *every* token in every triggered
module with one of four statuses. The mortgage module has 29 tokens; deed 11 plus
16 core; easement/declaration 27. Most will be `NOT_APPLICABLE` or `UNKNOWN`.

This is TRAYCER warning #3 inside B's draft: a rulebook that legislates every
slot produces enormous output carrying almost no information, and it is a large
part of why B's build does not fit (§6). It is also a *flagging* problem wearing
a different hat — 29 `UNKNOWN`s per mortgage event will dominate any
emitted-to-flagged ratio and make the framework look thorough while extracting
little.

**Proposal:** keep B's controlled token vocabulary — it is good, and it prevents
synonym drift — but populate a token only when the document supports a value, or
when the token is on a short **required** list per module (for mortgage:
`ORIGINAL_PRINCIPAL`, `RATE_TYPE`, `STATED_RATE`, `MATURITY_DATE`, `PRIORITY`).
Everything else is emitted only if present. The required list is what guarantees
terms are not silently dropped — which is the real objective — without requiring
27 negative assertions to prove it.

---

## 6 · THE THREE NEW ITEMS

### 6.1 The size ceiling — measured, and only one of us fits

Measured at `chars / 3.6` over the published drafts, counting what a reader
actually holds to extract one document (framework core + one triggered module +
`matrix-spec.md`, since Block 2 requires `resolved.md`):

| | A | B |
|---|---|---|
| framework always-loaded | 10,101 | 13,728 |
| term core (B: FR-TERM-100/101/102) | — | 1,432 |
| largest single type module | 408 | 181 |
| matrix-spec | 3,468 | 6,049 |
| **extraction build** | **14,131** | **21,390** |
| against 15,000 | fits, ~900 headroom | **over by ~43%** |

B's FR-SCOPE-004 asserts the loading contract "keeps the per-document extraction
build within the context ceiling." It does not, and the assertion is unmeasured.
Two structural reasons, both fixable without losing B's model:

1. **FR-TERM-102 defeats B's own module loading.** It is a single table
   containing the token lists for *all ten* modules, and it is always loaded — so
   the untriggered modules' vocabulary loads regardless. Split it so each module
   carries its own token list. Saves roughly 900.
2. **§5.5's mandatory population** drives both context and output size.

The remainder has to come out of B's sections 0–10, where FR-REC/FR-TERM prose is
the densest. I would rather cut there, keeping B's models, than keep my leaner
draft — mine fits by being thinner, not by being better.

**Add a QC rule neither of us has:** the build is measured and recorded at every
version bump, and a version that exceeds the ceiling does not ship. A ceiling
nobody measures is not a ceiling. Now that the justification is
consistency-of-application rather than context scarcity, this matters more, not
less: an unmeasured ceiling drifts, and drift shows up as inconsistent
application across 25M documents, which is invisible per document.

### 6.2 The reader is capable but not clever-in-context

Two things in **my** draft were written for a weaker reader and should go:

- **R-CIT-3's coarse zone vocabulary** — designed so a weak reader could not
  disagree about a locator. Already conceded in §3.8 for a better reason.
- **The R-NEV-12 glossary** — a capable model does not need to be told `F/K/A`
  means "formerly known as". But I would **keep it**, with its purpose restated:
  it is not a crutch, it is a *permission boundary*. The rule that matters is
  R-NEV-11 — no expansion of an abbreviation the document does not expand,
  except from this list — and a closed list is what makes that checkable.

One thing was written for a **cleverer** reader and is now actively dangerous:

- **R-INP-6a cross-source resolution.** I assumed a reader that would weigh
  sources sensibly. A capable model will apply it confidently and often, and
  every application launders rank-3 index data into a rank-1 field with a
  citation that looks impeccable. This is the plausible-interpolation failure
  mode exactly: not crude error, but a well-cited wrong answer. Conceded in §5.4,
  and the orchestrator's item 1 is the second independent reason to drop it.

I would also flag one in **B's** draft: FR-EV-005's "a handwritten insertion
controls the preprinted text in the same blank" is correct, but B has no rule for
handwriting *outside* a blank — the marginal `"MTGE TAX PAID: $42,091.50"` and
`"WHICH MORTGAGE HAS A REDUCED PRINCIPAL BALANCE OF $369,432.74"` on
`2003010600117004` are unbounded annotations of unknown authorship. A capable
reader will treat them as instrument text. My R-INP-5/M-AGREEMENT cover the
strike-through half; neither of us covers authorship. Both should: marginal
annotation is content, `src: MARGIN`, `author: UNKNOWN`, and it never overrides
the executed text at the same rank.

### 6.3 Escalation — neither of us has anything, so here is a proposal

Neither draft contains the word. The four things owed:

**E-1 · Trigger.** Escalation is permitted only from a **closed list of
mechanical conditions**, never from the reader's felt uncertainty:

| trigger | condition |
|---|---|
| `ESC-ILLEGIBLE` | a field is `UNKNOWN/ILLEGIBLE` after the §4.5 zoom, **and** the field is one of: event date, function, mode, `state_object_key`, BBL, or a quantity `value_normalized` |
| `ESC-CONFLICT` | `CONFLICTING_SAME_RANK_EVIDENCE` or `CONFLICTING_EVENT_DATE` survives FR-EV-009 |
| `ESC-CLASSIFY` | `UNRESOLVED_CLASSIFICATION` under FR-AMB-002 |
| `ESC-DENSITY` | more than N operative clauses in one instrument (N set empirically; the 113-page, 129-parcel declaration is the shape this exists for) |

Nothing else escalates. A reader may not escalate because a rule was hard, a
document was long, or a value seemed commercially odd — the same discipline as
R-AMB-3, and for the same reason.

**E-2 · Payload.** Not the document. The escalation carries: the document id and
the page images **named by the triggering evidence atoms only**; the framework
core plus the triggered module; the partially-built event table with the
triggering fields marked; the trigger code; and the candidate values already
found. Sending the whole package back defeats the point of routing.

**E-3 · The question.** Closed, not open. *"For field &lt;path&gt;, which of these
candidate values does the cited evidence support, or is it UNKNOWN?"* The heavy
model returns a value **from the candidate set or UNKNOWN**, plus a quote. It
does not re-extract, does not add events, and cannot introduce a candidate the
primary did not find — otherwise the escalation tier becomes a second,
unauditable extractor with different rules.

**E-4 · Merge-back.** The returned value replaces the `UNKNOWN` at exactly that
path, with `support: {rule: "ESC-MERGE", tier: "ESCALATION", trigger: ...}` and
the original candidates retained. **Escalation is invisible in the matrix** — it
is a routing decision, not an output value — but it is recorded in
`validation.escalations` so the rate is auditable.

**E-5 · The ratio.** `escalated / emitted` is reported per document and tracked
per round alongside `flagged / emitted`. A primary that escalates everything
looks careful, extracts nothing, passes every check and burns the Torch budget.
**Both ratios drifting up at once means the framework is buying agreement
twice.** I would set no threshold yet — we have no baseline — but I would want
the round log to carry both from round one, so that when a threshold is set it is
set against measurements rather than against intuition.

One thing I want on the record because it is the failure mode I would bet on:
`ESC-ILLEGIBLE` is the trigger that will run away. Film and book scans are
materially worse than ACRIS-digital, my §4.5 zoom will not rescue all of them,
and a heavier model reading the same 900 dpi image of a 1966 bound-book page
photographed against black will usually not do better. **Escalation cannot fix
a scan.** If the measured `ESC-ILLEGIBLE` rate on `FT_`/`BK_` is high and its
resolution rate is low, the right answer is to stop escalating that trigger, not
to escalate harder — and we should look for that specifically rather than wait
for the budget to tell us.

---

## 7 · WHAT NEITHER OF US COVERED

1. **Transfer tax and recording fee have no function home** (§5.1). Mine
   mis-filed them; B's drops them.
2. **A misfiled scan.** B has `INCOMPLETE_DOCUMENT_IMAGE_SET` for missing pages.
   Neither of us handles images that are a *different instrument* than the
   registration describes. At 25M documents this exists. Needs a
   `DOCUMENT_MISMATCH` determination that fails the package rather than
   extracting a wrong document confidently.
3. **Disjoint parcel sets.** Neither of us says what happens when the
   registration's BBLs and the body's premises do not intersect at all. My
   R-PARCEL-4 takes a union, which would silently merge two unrelated parcel sets.
4. **`FT_`/`BK_` reel-page stamps as the only recording identifier.** Both drafts
   assume CRFN. Film documents have `reel_page` and no CRFN; B's FR-REC-004 key
   ladder handles it via `REEL_PAGE`, but neither draft says the stamp on the
   page image and the registration's `reel_page` are the same object, or which
   ranks higher.
5. **Build-size measurement as a QC rule** (§6.1).
6. **Cross-document object identity** — deliberately out of scope under
   independent reading, but the matrix will eventually need it, and I would rather
   record now that we chose to defer it than have it look like an oversight later.
7. **Everything in §8.** Cross-reference capture, the epistemic mode axis,
   temporal extent, conditionality, and the coverage ledger are all absent from
   both drafts. That section supersedes this list as the more serious answer to
   "what neither of us covered" — these six are gaps in a record; those are gaps
   in an input.

---

## 8 · THE EVENT TABLE HAS A CONSUMER

This arrived mid-reconciliation and it changes what v1 must specify. Taking it
in the order it was given, against both drafts.

### 8.0 The finding that reframes everything above

Both of us designed the event table as an **output**. B's is a rigorous
serialisation with a validation suite; mine is a canonical diffable artefact. The
whole of §3 and §4 argues about which is the better *record*.

It is not a record. It is the **input to every later phase**, and the test is not
"is this faithful to the document" but "can the next phase place this event in a
parcel's chronology without asking anything." Those are different tests, and
where they diverge both drafts optimised for the wrong one — most visibly in how
we each dispose of events we could not fully resolve.

### 8.1 The three load-bearing tags, and the safe-harbour that is not one

BBL, applicable date, function. An event missing any of the three is
**unplaceable**, and unplaceable means dropped, not degraded.

| | A | B |
|---|---|---|
| unknown BBL | `parcels: []`, matrix empty with a reason (R-PARCEL-6) | `UNRESOLVED_BBL` flag, event stays in table, matrix routes to unresolved-parcel annex (FR-BBL-008, MX-FAN-007) |
| unknown function/mode | **nothing** | one `UNRESOLVED` package with candidates, routed to annex (FR-AMB-002, MX-FAN-008) |
| unknown date | `sort_date` fallback placed it anyway — conceded in §3.3 | undated annex (MX-TIME-002) |

**My draft cannot represent an unplaceable event at all.** R-AMB-1 forbids
flagging when a rule is hard and I never defined an unresolved-event state, so a
document whose function I cannot determine has no lawful output in my framework.
That is a straightforward hole and B's FR-AMB-002 fills it. Concede.

But B's annexes are treated as a neutral destination, and under this reframing
they are not: **an annexed event is an event that will never reach a chronology.**
Three annexes (unresolved-parcel, unresolved-classification, undated) are three
silent loss channels, and nothing in B's validation counts them against anything.
MX-QC-007 checks only that annexed events do not contaminate resolved cells — it
treats containment as success.

**Proposal for v1:** annex membership is a **tracked failure**, not a
disposition. Every annexed event is counted in a `placement` block —
`placed / annexed_bbl / annexed_classification / annexed_undated` — reported per
document and per round beside the flag and escalation ratios. A framework whose
annex rate is climbing is losing events, and neither draft would currently
notice.

### 8.2 Cross-reference pointers — captured verbatim, never resolved

**This is the item I would have most likely dropped, and my draft actively
forbids capturing it from the one place film documents put it.**

R-INP-7 makes `parcels[].remarks` cite *nothing*. On `FT_` and `BK_` rows the
cross-reference lives nowhere else: `"SUBSTITUTE MTGE REEL 595 PG 713"`,
`"D BOOK/PAGES: 156/36"`. My blanket exclusion — written because I saw `remarks`
carrying a 1989 index correction on a 1982 recording and concluded the whole
field was register annotation — would discard the only pointer a film document
has. §4.2 already proposed the narrower rule; I am upgrading it from a refinement
to a **defect**, because the consequence is not a lost nicety but a permanently
severed link.

Worse, and neither of us caught this: **neither draft has any rule requiring the
ACRIS cover page's `CROSS REFERENCE DATA` block to be captured.** I read that
block on `2002122000002001` — it carries `MANHATTAN / Year 2001 / Reel 3221 /
Page 495`, the pointer to the mortgage being satisfied — and recorded it in my
survey notes. It appears in neither framework. B's `references` structure
(FR-REF-001) and my `references` array would both hold it; nothing tells the
reader to look.

What v1 needs, and neither draft has:

> **A required cross-reference capture step**, run once per document, that
> harvests every pointer from every place the four schemas put one — the cover's
> `CROSS REFERENCE DATA`; `crfn`; `reel_page`; `book`/`page`/`instrument`;
> `remarks`; and any recording locator recited in the instrument body — and
> records each **verbatim, with its source and its own evidence**, in a
> document-level `cross_references` block. Each entry is typed by what the
> document says the relation is (`AMENDS`, `SATISFIES`, `ASSIGNS`,
> `CONSOLIDATES`, `SUBSTITUTES_FOR`, `CORRECTS`, `RELATES_TO_UNSTATED`) taken
> from the document's own words, and `UNRESOLVED` is the permanent and correct
> state of every one of them.

The typed relation matters: an unresolved pointer that does not say what it
points *for* still leaves the next phase guessing. The document nearly always
says — "which Mortgage HAS NOT been assigned", "recorded contemporaneously
herewith", "SUBSTITUTE MTGE" — and that language is free to capture and
impossible to reconstruct later.

B is closer than I am here in one respect worth adopting: FR-REC-004's key ladder
already derives a `state_object_key` from a recording identifier
(`FUNCTION:REF:CRFN:…`, `REEL=…;PAGE=…`). That means a referenced object gets a
stable, cross-document-resolvable name **without** resolving it. The pointer and
the key should be the same object; B's ladder is the mechanism.

### 8.3 Mode — two fields, not one, and the rule that couples them

Effect-on-state (create/modify/transfer/terminate/assert/correct) and epistemic
character (transaction/observation/…) are orthogonal, and **both drafts carry
only the first.**

They cannot be collapsed, and the decisive case is the one the principal names:
an observation dated 2020 may describe a condition true since 1960. Folding it
into a 2020 cell as a change is a fabrication. But the case that proves they are
not merely *usually* different is closer to home — a covenant against grantor's
acts and a title company's zoning-lot certification are both `ASSERT`, and they
are not the same kind of thing. The covenant is made *by a party in a
transaction* and creates liability; the certification is a third party's
observation and creates nothing. One field cannot distinguish them.

**Proposal:**

```
mode      : CREATE | MODIFY | TRANSFER | TERMINATE | CORRECT | ASSERT
character : TRANSACTION | OBSERVATION | DETERMINATION
```

`TRANSACTION` — parties act, with legal effect between them.
`OBSERVATION` — a statement about a state of the world, changing nothing.
`DETERMINATION` — an authority (court, agency, register) rules, and the ruling
has effect. This is the third the corpus demands: my census turned up
`VACATE ORDER` and `CERTIFICATE`, and an agency approval is neither a bargain nor
an observation.

The coupling rule is what makes two fields cheap rather than free-floating:

> **An `OBSERVATION` may not carry any mode but `ASSERT`.** If a clause changes
> state, it is a `TRANSACTION` or a `DETERMINATION`. This is a QC check, not a
> guideline.

And the consequence the chronology actually needs:

> **An `OBSERVATION` carries two dates**: the date it was made, and the date of
> the condition observed when the document states one ("as of", "at the time of
> sale", "presently"). The second is what the chronology places; the first is
> when someone said so. Where the document states only the first, the observed
> condition's date is `UNKNOWN` — **not** the observation date.

That last clause is the whole point. The RP-5217's "use at the time of sale" and
the smoke-detector affidavit's present-tense installation are both observations
whose subject predates the filing by an unknown interval, and both drafts would
currently stamp them with the execution date and call it a state change.

B is nearer than I am: MX-CELL-002 already says "ASSERT events do not prove
creation and therefore retain UNKNOWN lifecycle", and FR-FN-009 already splits
Occupancy into `AUTHORIZED` / `ACTUAL` basis. Both are the right instinct
implemented at one function instead of as an axis.

### 8.4 The six required items, against both drafts

| # | requirement | A | B | verdict |
|---|---|---|---|---|
| 1 | stable event identity | M-TIE-3: id ordered by `sort_date` → function → mode → BBL → clause | FR-REC-003: id ordered by evidence page → reading order → function → mode | **B, and both need fixing** |
| 2 | temporal extent | `terms.maturity/commencement/duration` — prose in a blob | typed tokens `START_DATE`/`END_DATE`/`MATURITY_DATE` | **B closer, neither sufficient — restructure** |
| 3 | same-instant ordering | M-TIE-2 orders by mode index — invents sequence | `EVENT_SEQUENCE` term + MX-TIME-005 + MX-QC-004 | **B, but in-document only — gap** |
| 4 | conditionality | collapsed into `NONE_STATED` → UNKNOWN | FR-DATE-006 stores the condition; reason code still `NOT_STATED`/`UNSUPPORTED_DATE` | **both collapse it** |
| 5 | absence-assertions as events | R-NULL-3 + M-DEED emit `ENCUMBRANCE.ASSERT` | FR-NULL-003 makes it a *field value*; FR-PKG-002 would permit an event; FR-TERM-110 pushes the other way | **A, and B is internally inconsistent** |
| 6 | coverage ledger | `page_inventory` + `counts` | `validation.pages_read` + `unresolved_items` | **neither has it** |

**1 · Event identity.** Mine is worse than I realised and B's is not safe either.
My ordering key starts with `sort_date`, a *derived* value — so the moment a v2
rule changes a date basis, every id in the corpus shifts and every downstream
reference breaks. B anchors to physical layout (page, reading order), which does
not move when a rule changes. **Adopt B's**, with one improvement on both: the id
should be anchored to **page and reading order alone**, with a disambiguating
ordinal, and *not* to function and mode. Both drafts put classification in the
sort key, so a reclassification in v3 renumbers events that did not change. Ids
must be stable across framework versions, not merely deterministic within one.

**2 · Temporal extent — a shape change, not a field.** A mortgage has an
origination and a maturity; a lease has a term. Both drafts bury the far
boundary in terms, and B's matrix batches on `effective_date` only (MX-TIME-001,
MX-TIME-003). Promoting extent to a first-class `extent: {start, end, basis,
conditional}` alongside `effective_date` forces a decision B's §2 does not
currently contain: **does a maturity generate its own row in the chronology?** It
must — a loan maturing is a state change with a date — but that means the overlap
components are built from a set of *intervals and endpoints*, not from effective
dates. That is a restructure of B's time model, and it is the answer to the
orchestrator's "say so if the record cannot carry these without restructuring."
It can't. This one can't.

**3 · Same-instant ordering points outside the document.** B has the right
machinery and it is scoped wrongly: `EVENT_SEQUENCE` links events *within one
document*, and the canonical case — a deed and its purchase-money mortgage — is
**two documents**. My census found the shape directly: `2003010600117001`–`005`
is one closing package filed as five separate documents over the same four BBLs.
Nothing within any one of them can order it against the others. What can is the
document's own language, which I saw on `2003010600117004`: a mortgage recited as
recorded *"contemporaneously herewith"*, and the printed liber/page struck out
because it did not exist yet. **That phrase is an ordering pointer and it belongs
in `cross_references` (§8.2) with a relation type**, not in an in-document
sequence graph. Neither draft captures it.

**4 · Conditionality.** Mine collapses "no date stated" and "date depends on a
condition" into one UNKNOWN — exactly the loss named. B keeps the condition as a
term but its date reason codes (`NOT_STATED`, `ILLEGIBLE`, `CONFLICT`,
`UNALLOCATABLE`, `UNSUPPORTED_BBL`, `UNSUPPORTED_DATE`) have no `CONDITIONAL`, so
at the date field B collapses it too, one level down. Cheap fix, real gap in
both: add `CONDITIONAL` as a reason code, carry the condition verbatim, and make
it distinct from silence forever.

**5 · Absence-assertions.** The one place my draft is ahead. R-NULL-3 requires
`ASSERTED_NONE` to carry its scope verbatim and M-DEED emits an actual
`ENCUMBRANCE.ASSERT` event for the covenant against grantor's acts, scoped by
*"except as aforesaid"*. B's FR-NULL-003 makes absence a **field value** — which
has no date, no author and no place in a chronology. B's FR-PKG-002 would permit
an event, but FR-TERM-110 explicitly pushes the other way, so **two careful
readers of B's draft would answer differently**, which is B's own standard for
"not a rule yet". v1 should take mine: an assertion of absence is an event with a
date, an author, a scope and legal content.

**6 · Coverage ledger — neither of us has it, and it is a restructure.** Both
drafts track *pages read*; neither tracks *sections identified → event or stated
reason*. Building it means the clause segmentation — my R-SPLIT-1, B's
FR-PKG-001 — stops being an internal step and becomes a first-class output: every
segmented section gets an id, and every id resolves to either an event or a
recorded reason for emitting none (boilerplate, no function affected, historical
recital, not operative).

The consequence is larger than an extra artefact, and it is the reason I think
this is the most important of the six: **it fixes the denominator.** Both drafts
report emitted-to-flagged, and in both the denominator is "whatever the reader
happened to notice." A missed section and a correctly-empty section are currently
indistinguishable — from the reader, from each other, and from the round's
reviewer. With a ledger, a missed section is a section with no disposition, and
that is mechanically detectable. TRAYCER #4 asks us to track the ratio; neither
draft yet has a ratio that means anything.

### 8.5 Summary: what has to change shape

Additive (a field, no restructure): `character` and its coupling rule; the
`CONDITIONAL` date reason; absence-assertions as events; the `placement` counters.

**Restructures, in descending cost:**

1. **Coverage ledger** — clause segmentation becomes an output artefact, and both
   drafts' §3 changes from procedure to procedure-plus-record.
2. **Temporal extent** — the matrix time model batches on intervals *and*
   endpoints, not on effective dates. B's MX-TIME-003 is rewritten.
3. **Cross-reference capture** — a new document-level block, a new required
   harvest step across four registry schemas, and the repeal of my R-INP-7
   `remarks` exclusion.
4. **Event identity** — re-anchored to layout only, so ids survive
   reclassification across versions.

My event record cannot carry (1), (2) or (3) without restructuring. B's cannot
carry (1) or (2). Finding this at v1 costs a rewrite of two sections; finding it
at v3 costs the corpus.

## 9 · DEADLOCKS

Three. Everything else above I would accept B's answer on if B holds, or expect
B to accept mine.

- **§5.2 — lease as Title vs Encumbrance.** I have an argument I think is strong
  (B's rule writes a false fee transfer onto the indexed BBL) but it is genuinely
  contestable, and it changes the Title column on every recorded lease. My
  position: emit both, linked. Cost if B is right and I am wrong: one redundant
  Encumbrance event per lease. Cost if I am right and B is wrong: the Title
  column reports fee transfers that did not happen, and nothing downstream can
  detect it.
- **§5.1 fallout — where tax and fee live.** Not a disagreement between us; a hole
  both drafts have, and it needs a decision rather than a compromise. My
  position: quantities on the operative event, no function event.
- **§8.3 versus §3.3 — where an observation lands.** This one is a tension
  between two positions I have *both* taken in this document, and I would rather
  put it up than resolve it by preferring whichever I wrote later.

  In §3.3 I conceded B's rule that an event with an UNKNOWN date goes to the
  undated annex and never touches a dated cell. In §8.3 I argued that an
  observation's placeable date is the date of the *observed condition*, which
  documents usually do not state.

  Together those say: **every observation whose subject-date is unstated is
  annexed.** That is the smoke-detector affidavit, the RP-5217 use code and
  building class, most certifications — a large and systematically useful class
  of assertions, removed from the matrix wholesale. And by §8.1 that is not a
  neutral disposition, it is a loss.

  The alternative is to place an observation at its observation date with a
  marker that the condition it reports may predate it. That is honest about
  *when someone said so* and dishonest about *when it became true*, but it keeps
  the assertion in the chronology where it can be reasoned about.

  I lean to the second, on the ground that the observation date is a genuine
  upper bound on the condition — the condition was true no later than the day it
  was certified — and a bounded placement beats an annexed one. But I do not
  think my lean should settle it: the first position is the one that never
  fabricates, and I argued for it three sections earlier. Both positions cost
  something real and the choice determines whether four of the eleven columns are
  routinely populated or routinely empty.

---

## 10 · PROPOSED SHAPE OF v1

If B does not object, I would write v1 as **B's model on my inputs, restructured
for the consumer**:

- B's evidence rank table (§3.5) + my per-field registration citability (§4.2)
- B's `state_object_key` (§3.1), fold semantics, conflict handling, ordering
  discipline, and QC suite (§3.2–§3.7), including MX-QC-003
- My package-shape and four-schema rules, page inventory, index-corruption
  warnings, zoom-before-illegible (§4.1–§4.6)
- B's Cost/Value split (§5.1) with tax/fee ruled on
- B's evidence-conditioned Capital termination (§5.3) with the paired-close metric
- B's term vocabulary with §5.5's required-list population instead of mandatory
  population
- The escalation contract in §6.3
- **New, from §8:** the `cross_references` capture block; `character` as a second
  mode axis with its coupling rule; first-class `extent`; `CONDITIONAL` as a date
  reason; absence-assertions as events; layout-anchored event ids; the coverage
  ledger; the `placement` counters
- Rendering: B's canonical JSON, my `·` legend and a truncated markdown view
- A measured build under 15,000, recorded at the version bump

**One thing I want to flag before I write it rather than after.** Everything in
§8 adds. B's build is already ~21,400 against a 15,000 ceiling, mine is ~14,100
with ~900 of headroom, and the coverage ledger, cross-reference block, second
mode axis and extent model are all additions to whichever base we take. v1 cannot
be "both drafts plus the new requirements" — that lands somewhere north of
25,000.

So the pen's first job is deletion, and I would rather say now where I expect to
cut than discover it mid-write: B's FR-TERM-102 mandatory population (§5.5) and
its all-modules token table; B's FR-REC/FR-TERM prose, which is the densest
material in either draft and often restates a rule the QC suite already enforces;
my own type modules, most of which are thin and can fold into a shorter table;
and B's matrix-spec §6 serialisation prose, which specifies byte-level JSON
conventions at a length the reader does not need in context. If that is not
enough, the honest move is to tell the orchestrator the ceiling and the
requirements are in conflict — not to ship something over it quietly, which is
the one failure mode the ceiling exists to prevent.

I hold the pen for v1 and I am aware that most of §3 is me handing B the
architecture. That is the correct outcome: B built the better model. The two
places I am asking B to move — the registry/package rules and the lease
classification — are the two places my survey went and B's did not. And §8 says
neither of us built the right *thing*: we both built a record, and the job was an
input.
