# v2 drafting notes — Extractor A

Written before finishing, as in round 1, so it records what I thought while the
work was still open rather than what I would defend afterward.

---

## 0a. Revision 3 — R2-1…R2-7

**R2-1 was real and my revision-2 fix caused it.** Closing `cell` and `quantity_candidate` with `additionalProperties: false` and then extending them through `$ref` produced two defs that reject every instance — `additionalProperties` is not annotation-aware across a `$ref`, so it cannot see a wrapper's own properties, and `unevaluatedProperties: false` on the wrapper cannot undo it. **No conforming `extraction.json` existed.** Fixed by splitting `cell_base`/`quantity_base` with no closure and applying `unevaluatedProperties: false` at each point of use.

`schemacheck.py` now reports **32 satisfiable, 2 UNSAT**. I verified both remaining rows and they are synthesiser artifacts, not defects: `interval` picks the first enum value `SUPPORTED` and then does not honour the `if/then` that requires `interval_start`; `evidence_time` nests the same broken interval. Real instances of both branches validate, and `fixtures/positive.json` ships them so the claim is checkable rather than asserted. **I did not weaken a correct conditional to make a synthesiser succeed** — that is the same move as shrinking a framework to make a number look better.

`fixtures/fixturecheck.py` runs 11 positive and 5 negative fixtures: **16 fixtures, 0 failures.** The negatives cover the counterexamples from both reviews — a HIT with no anchor, a transaction claiming `NOTICE`, eleven duplicate `FR-QC-001`s, an observation assertion carrying a lifecycle op, and a JSON null.

**On the tool: it found what two reviews and I missed, and the reason is the question it asks.** Every negative fixture passes against a schema that rejects everything, so a suite made only of negatives certifies an unsatisfiable schema as sound. *Does at least one instance exist* is the complement, and nothing in the loop asked it. That is a general lesson about test suites, not about this schema.

**R2-2** — `FR-LOAD-006` is now stated as authoritative over `FR-LOAD-001`; the `[REGISTRATION]` rule set (`FR-REC-012`, `FR-REC-013`, `FR-DATE-008`, `FR-QTY-005`, `D-9`) is named, marked at each definition, and loaded by the registration pass. They remain physically in §4/§5, which is filing by topic — the defect this ordering exists to remove — and the relocation is a compiler task. `FILM_BK` declares `AD-FT-001` as its shared base. Discovery now *marks* `escalation_eligible` and does not route, since routing is a §5 decision it does not load.

**R2-3** — every `HIT` and `SUPPORT_ONLY` anchor enumerates its candidate claims, and `resolves_claim_ids` is required on the event core. Identity on the negative path alone could not be matched against on the positive one, so FR-COV-005's tests had nothing to compare.

**R2-4** — the generic `module_path` split into `field_op` (carries `op`, deltas and boundaries only), `assertion` (no `op`, observation lanes only) and `term`. `value` excludes JSON null everywhere. An observation carrying a lifecycle operation is now unconstructable.

**R2-5** — `FR-QTY-002` reconciled: a blank field is UNKNOWN only where a module `required_when` makes it applicable, otherwise `EMPTY_FIELD_SEARCHED`.

**R2-6** — `index_reported_date`, `index_reported_amount`, `current_recording_identity`, `parcel_inventory`, `page_count_reports` and `notarial_date_anchor` are closed. `raw_registration` stays an open object deliberately and says so: it is the archived input, not an output shape.

**R2-7 adopted.** Schema validation is deterministic computation run by a validator, not a reading pass; **the semantic page passes are twelve again** and the schema is in no pass's budget. Assembly instead loads `template.json`, the generated empty instance, so the producer is specified rather than debugged by rejection.

### Cost after revision 3

| pass | load |
|---|---:|
| discovery ×11 | 12,003 |
| support | 12,285 |
| enrichment ×E | 21,073 |
| assembly | 26,265 |

```
floor 170,583  ·  ceiling 423,459        (rev 2: 178,741 / 399,001)
```

Floor fell because the schema left assembly. **Ceiling rose because `enrichment.schema.json` grew from 2,978 to 5,225** when one permissive `module_path` became three exact shapes — the R2-4 fix, and the largest single cost in this revision. `§0+§1` is now **7,759**, up 391 for claim identity and the load table, and still the number I would attack first.

**These figures remain non-decision-grade in one respect I want stated rather than buried:** they assume a `(function, module)` enricher loads about 1,000 tokens of module text and that assembly loads about 3,100. Both are estimates over a loaded set, not measurements of a real run, and no run exists.

---

## 0. Revision 2 — B's returns 2, 4, 5, 6, 7

### Why check 4 did not run

I specified it, named it as the one that fails silently, argued it into the
release conditions, and shipped without it. The answer is not that I forgot.

**I verified the partition's *size* and never its *closure*, and the size number
was satisfying enough to stop at.** `§0+§1 = 6,337` against a 6,500 target is a
crisp result that looks like verification. It measures whether the block fits a
context. It says nothing about whether the rules inside it can execute — and
`FR-ANC-001` invoked D-2 from §4 the whole time, so a discovery lens could not
compute the `anchor_id` every downstream join depends on. **A partition that hits
its token target and cannot run its own rules is worse than no partition, because
the number looks right.**

The mechanism was available: grep every rule citation in a block against the ids
defined in the blocks that block's pass loads. It is a twenty-line script. I did
not write it because check 4 was framed in my own structure document as something
to run *"after drafting, before release"* — a release gate — and I was still
drafting when I posted. That framing was mine and it was wrong: closure is a
property of the text, checkable the moment the text exists, and treating it as a
gate deferred it past the point where anyone would look.

This is the same shape as the CV test, where I scored the wrong metric and caught
it mid-run. Here nothing caught it before B. The difference is that in the CV test
I was measuring something I did not already believe; here I was confirming
something I did, and I stopped at the first number that agreed with me.

### Which of the seven would round 2 have surfaced

The orchestrator scoped 4, 5, 6, 7 as blocking round 2 and 1, 3 as production.
I agree with the split and **disagree with the reason given for it.**

| return | would round 2 surface it? | |
|---|---|---|
| 1 build/gate absent | no | by construction |
| 2 dependency closure | **no** | masked — B and I read the whole framework, so the missing D-2 never bites |
| 3 shadow diff absent | no | by construction |
| 4 schema permissiveness | **no** | invisible to a conforming reader: the counterexamples are outputs a careful extractor would not produce |
| 5 claim-level orphan | only if a document happens to carry two claims on one clause | partial |
| 6 blank-field findings | **yes, immediately** | a Richmond deed's form fields would generate noise on the first page |
| 7 Article 18 regression | **no** | it fails silently; surfacing it requires hunting for an absence |

**Only Return 6 would reliably surface.** So these four do not block round 2
because the round would catch them — they block it because **round 2 would
inherit them into its evidence.** A schema that accepts a Title pass emitting
Cost cells produces no complaint from a careful reader and then certifies
whatever a careless one emits later. A silently suppressed conditional Encumbrance
produces no event and no exception, so a clean-looking round 2 would be cited as
confirming a rule that is wrong.

**On the one question asked: no, an unbuilt partition does not corrupt round 2 —
but it does something worth naming.** Reading the whole framework means round 2
tests v2's *rules* and not v2's *delivery*, and a pass would be evidence for
full-bundle v2 only. The guard is cheap: **round 2's result must be labelled as
testing full-bundle v2**, so a later reader cannot cite it as evidence the
partition works. That is the same distinction as *eleven completion records exist*
versus *the reader inspected faithfully*, one level up.

### What changed, and what it cost

`FR-DATE-006a` restored to the narrow test — emit when the consequence identifies
a module path and keyed object touched by a present act; exclude only a
consequence naming no filled path. Article 18 and a pure severability control are
frozen as a pair. **B is right that v2 was worse than v1 there.**

`FR-EV-010` added: `EMPTY_FIELD_SEARCHED` creates no atom, anchor, null or
finding and is counted once per cell; `VISIBLE_UNREADABLE_MARK` is the
`FR-EV-001a` path. The AS_BUILT card no longer instructs a reader to manufacture
findings from blank fields.

`FR-EV-008` coverage and residue now stated for the legal-designator table, the
Richmond alias table and module phrase sets — all three `ASSERTED_UNMEASURED`
with explicit residue routing, because the honest answer is that no coverage was
measured and the residue must fail loudly rather than be dropped.

D-2 moved to §0; D-1 and escalation removed from the discovery path entirely —
a discovery lens now stops at reread and returns `UNCERTAIN`, which is more
correct than moving D-1 up, since eleven isolated lenses adjudicating one glyph
would produce eleven adjudications. `FR-LOAD-006` states each pass's blocks and
makes cross-block citation a build defect. Cards now carry their modules'
admitted receiving paths — Encumbrance carries both SECURED_FINANCE and
LAND_RIGHTS.

`FR-SWP-009` assigns `candidate_claim_id` before any exclusion, and the orphan is
keyed by claim with three exhaustive tests naming what each checked.

**Cost, measured.** Every pass load now fits 33,000:

| pass | load |
|---|---:|
| discovery ×11 | 11,347 |
| support | 11,629 |
| enrichment ×E | 18,355 |
| assembly | 25,161 |
| schema gate | 17,134 |

```
floor 178,741   ·   ceiling 399,001 at twelve enrichers
```

Against revision 1's 137,240 / 340,352 and the 141,000 / 309,000 plan. **Fixing
the returns cost ~41k on the floor and ~59k on the ceiling, almost all of it the
schema.** Closing every semantic object doubled `extraction.schema.json` from
7,619 to 15,474 — a closed schema is comparable in size to the prose it
validates, which I had not anticipated and which nobody costed.

That forced one architectural change I want flagged rather than buried:
**`FR-SCHEMA-005` makes the schema gate its own pass.** Assembly plus the closed
schema measured 40,373 and exceeded the live ceiling. The gate needs no
composition rule, no module and no §5 prose, so it runs alone at 17,134 and
assembly runs at 25,161. Two passes that each fit beat one that does not. It is a
load-class split, not a new check.

`§0+§1` is now **7,368**, over the 6,500 target by 868. That is the price of
dependency closure — D-2, `FR-LOAD-006`, `FR-EV-010` and `FR-SWP-009` all belong
in the shared prefix — and it is paid eleven times per document. I think it is
the right trade and it is the number I would attack first if the floor has to
come down.

---

## 1. The budget, measured

Measured with the same `chars/3.6` gate v1 used.

### Aggregate ceilings — two are exceeded

| | measured | ceiling | |
|---|---:|---:|---|
| core (§0–§5, §7) | **23,952** | 16,500 | **over by 7,452** |
| schema suite | **12,749** | 11,000 | **over by 1,749** |
| matrix spec | 8,634 | 10,000 | under |
| all modules (7) | 5,359 | — | a loaded set is 3–4 |
| all adapters (4) | 2,376 | — | one loads |
| bundle (core + 1 adapter + loaded modules) | ~27,878 | 22,000 | **over by ~5,878** |

### Per-pass loads — every one fits

| pass | loads | measured |
|---|---|---:|
| discovery lens ×11 | §0+§1 + one §2 slice + `discovery.schema` | **8,839** |
| `DOCUMENT_SUPPORT` ×1 | §0+§1+§3 + `discovery.schema` | **9,012** |
| enrichment ×E | §0+§1+§4 + module + `enrichment.schema` | **16,926** |
| assembly ×1 | §0+§1+§4+§5 + loaded modules + `extraction.schema` | **30,999** |

`§0+§1` measures **6,337** against the 6,500 target. Discovery at 8,839 fits B's
9,000 planning ceiling. Assembly at 30,999 is the largest single context and fits
the 33,000 live ceiling.

```
framework cost = 11 × 8,839  +  9,012  +  30,999  +  16,926 E
               = 137,240 floor   ·   340,352 at all twelve enrichers
```

**Floor came in under plan (137,240 against 141,000); ceiling came in over
(340,352 against 309,000).** The whole overrun is the enrichment pass, planned at
14,000 and measured at 16,926, because §4 carries the full derivation registry
D-1…D-10 plus classification, time, parties, parcels and quantities for a pass
that classifies one function's spans.

### What I am claiming, and it may be wrong

**The `core ≤ 16,500` ceiling no longer measures anything a reader
experiences.** Under v1, core was one block every run loaded. Under v2 no pass
loads all of core: §2 is eleven items of which one loads, §3 loads only for the
support pass, §4 and §5 never load at discovery. The number that binds is the
per-pass load, and all four fit.

That is a real argument and it is also exactly the shape of argument I would
distrust from someone else — *my measurement is over, therefore the measurement
is wrong.* So, plainly: **I did not do a serious compression pass.** I chose to
report the number rather than shrink prose, because the instruction was to
measure and not target-fill, and because the growth is the round's deliverable —
the party record, the relationship registry, the sweep protocol, the schema gate,
comparator capability, reference classes, incorporated sections, boundary
orphans. If the honest answer is that core must fit 16,500 as a document, roughly
7,500 tokens have to come out and I do not know which 7,500 without being told
which findings to drop.

**The `bundle ≤ 22,000` overrun is the more serious one**, because unlike core it
does describe a real context: assembly loads core plus modules plus schema.
Assembly measures 30,999 and fits the 33,000 live ceiling, but only because the
adapter is not loaded at assembly. That is correct — registration is not a page —
but it means the two ceilings are now measuring overlapping and slightly
different things, and I would rather flag that than quietly satisfy whichever one
is easier.

**Schema at 12,749 against 11,000.** B's 8,500 measured floor was over round-1
paths; the party-inclusive estimate was 10,500; the full method contract took it
to 11,000; measured it is 12,749. The extraction schema alone is 7,619. I do not
think this one is arguable — the schema is what it is, and 11,000 was an estimate
made before it existed.

---

## 2. What I could not fit, and what I deferred

**A second partition of §4.** Enrichment is the heaviest pass after assembly and
is the only ceiling overrun in the cost formula. §4 could plausibly split into a
shared classification kernel (D-rules, split/merge, mode, character) and a domain
half (time, parties, parcels, quantities), letting a `(function, module)`
enricher load less. I did not do it because I could not convince myself any real
enricher needs less than most of §4, and a partition that never reduces a load is
cost with no benefit. **Untested.**

**The build tool.** §2 as written is a *source* form: nine collision rows tagged
with the functions they name, plus eleven cards. The per-lens slice — one card
plus only the rows naming that function — is produced by a build step **that does
not exist**. So the 8,839 discovery figure is a projection of a build step nobody
has written, and if the build ships the whole §2 to every lens, discovery becomes
~8,000+1,300 and the eleven-lens term rises about 15%.

The same gap covers `FR-SCHEMA-003`: the manifest is build-tool-emitted, and
there is no build tool.

**`§0+§1` byte-identical across eleven prompts.** Written as a requirement in
`FR-SWP-002` and the structure doc. **Not verified**, for the same reason.

**Verification check 4.** I named it as the one that matters and the only one
that fails silently — *for each pass, prove the rules it must apply are inside the
blocks it loads* — and I have not run it. B's shadow-discovery diff is the
mechanism and it needs a fixture set and a partitioned runner. **This is the
largest untested claim in the release.** A discovery lens needing a rule it
cannot see does not error; it produces a worse answer with a complete-looking
sweep ledger.

**No fixtures are shipped.** `FR-QC-010` and `MX-QC-009` name a conformance set
including TC-001, TC-003, L1/L2, O1/O2/O3, and new fixtures for multi-parcel
events, `PARTY_SHARE` allocation groups, illegible finals and boundary orphans.
None exists. The version gate is binding and cannot currently pass.

**`version-gate.md` is named but not written.** §7 points at it and declares it
binding. Writing it was not in this task; naming it without shipping it is
exactly the "moved to a file nobody is required to run" failure I argued against,
and it is open until the file exists.

**The registry-side clock.** v1's known gap — no vocabulary for registry-side
time — is *still not closed*. `FR-REC-013` gives a non-locator remark a lane and
a raw temporal token, and `MX-TIME-007` states plainly that
`registration_annotations` has no time axis. The gap is now recorded rather than
hidden, which is a smaller thing than fixing it.

---

## 3. Where I think I am wrong

**Rule-id hygiene.** The contract says an id may be amended or retired but never
reused for a different decision. Several ids carry meanings that moved further
than "amended":

- **`FR-COV-001`** was *segment the page*; it is now *sections are the snapped
  union of anchors*. The question is the same — what is a section — but the
  mechanism inverted from cutting to collecting.
- **`FR-PARTY-001`** was *one record per distinct **operative** person*; it is
  now *every distinctly named person or entity, with names, attributes and
  comparator QA*. That is arguably a different decision and may deserve a new id.
- **`FR-REC-012`** gained the present-but-empty rule, which changes which paths
  are inventoried at all.

I kept the ids because a reader tracing a v1 objection to its v2 answer is better
served by continuity than by purity, and because renumbering breaks every
cross-reference in both cross-examinations. **B should check this; I am not
confident.**

**The party split is uncomfortable and I still think it is right.** Grammar in
§1, schema in §5, splitting the `FR-PARTY-*` id family across two blocks that no
single pass loads together. I predicted this would be the placement quietly
re-merged during drafting. I did not re-merge it. It still reads wrong on the
page, which is what order-by-reader costs.

**§1 is 5,113 tokens and every lens pays it eleven times.** It is the single most
leveraged number in the framework — one token there costs eleven per document
plus the support pass. I did not optimise it against that leverage; I wrote it
for correctness and measured afterward. A pass specifically aimed at §1 density
is probably worth more than anything else available.

**I asserted `AS_BUILT` must "visit every labelled measurement field whether or
not it appears filled."** That is a rule aimed squarely at the round-1 ACRES
miss, and it is the kind of rule that reads as sound and behaves as
over-instruction — a 27B reader may now emit an anchor for every empty cell on a
form. `FR-EV-008` obliges me to state the residue and I cannot: **I do not know
how many empty labelled fields a typical form has**, and the rule may generate
noise proportional to that unknown.

**`FR-DATE-006a` conditional materiality may be too strong.** I wrote that a
savings clause whose consequence is that other terms continue to govern fills no
path. B emitted exactly such a clause as a conditional Encumbrance in round 1 and
was right under v1. I have now written a rule that makes B's correct answer
wrong. If the materiality test is mis-set, v2 silently drops conditional events
that v1 caught, and the failure is invisible because nothing is emitted.

**Two clocks in one rendering.** `MX-VIEW-003` requires `date_kind`. That fixes
the column. It does not fix a consumer who reads the table without it, and the
brief in `MX-VIEW-006` prints dates in prose with no clock marker at all. I think
that is acceptable because the brief is explicitly a summary, but it is the same
defect one layer further out and I noticed it too late to restructure.

**I have not run v2 on a document.** Everything above is a claim about a text.
Round 2 is the test, and the two mechanisms most likely to be wrong — the
conflict contract and residual backfill — are the ones a small Richmond document
will exercise least.

---

## 4. What I would have B attack first

1. The `core` overrun: is my "the ceiling measures the wrong thing" argument
   sound, or self-serving?
2. Rule-id reuse on `FR-COV-001`, `FR-PARTY-001`, `FR-REC-012`.
3. `FR-DATE-006a` — does it make your round-1 conditional event wrong?
4. `AS_BUILT`'s visit-every-field instruction and its unstated residue.
5. §1 density, given the eleven-times leverage.
6. Whether §4 should be partitioned, since it is the only term over plan.
