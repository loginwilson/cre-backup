# RUN STATE — live

**Purpose:** the orchestrator's context is finite and will be lost. Anything needed
to continue the run without the user re-explaining it lives here. Update it at every
phase boundary, not at the end.

Last updated: 2026-08-31, at dispatch of phase 1.

---

## Where the run is

**PHASE 1 — RE-EMIT TEST. ✅ COMPLETE. Batch closed, partially ruled.**

**FEED went 0 of 125 → 100% on all five**, gate clean on the first run, no loosening.
Full report: `judge/batches/RE-EMIT-1.md`. Tables archived with hashes in the backup
repo under `tables/RC_1598772/`.

| reader | v1 → v2 rows | FEED | sha256 |
|---|---|---|---|
| A | 16 → 16 | 100% | `57a414ebb5924ad9` |
| C | 29 → **16** | 100% | `bb2000d53487514e` |
| E | 27 → 19 | 100% | `41a8a2ef6224ff6a` |
| D | 26 → 22 | 100% | `2069674c063f6179` |
| B | 27 → **26** | 100% | `2e731f51e6984984` |

**Ruled and applied** (these blocked m2, because the worked example is what the next
reader calibrates against):
- grantor is `WOOD HARMON RICHMOND REALTY COMPANY` — three distinct names had been
  merged into one
- covenants bind *"the herein-described premises"*; the plat phrase is the grantor's
  **reservation**. The old spec would have fanned fourteen rows to the wrong parcels.
- cost floors vary by **family count**, not street
- a building cost floor is **`COST`**, not `ENVELOPE` — `function` is a machine field,
  so the file's self-contradiction was making identical readings produce different
  state records
- the worked example is now **transcribed from a sealed reader table**, not composed

**Fixed in code:** the zoom leak (27 crops had landed in a shared `loop/zoom/`), and
the `until < date` row check, which was dead on every v4 table.

**Still open:** `BBLS_OK` accepts `SET:` + any prose. Left deliberately — a regex
cannot judge whether a criterion is evaluable, and three readers contest the
framework's own worked failure case.

### ✅ DONE since the batch closed

**1. Class spec rebuilt from measurement** (`8ef52d8`). §2 is now counted across 99
rows from five readers, not guessed. The guess listed six functions; **eight fired**.
`ENTITLEMENT` (9 rows) was unpredicted — the grantor's reserved rights are
development rights attaching to land. `CAPITAL`/`PERMIT`/`AS_BUILT` came in at
**0 of 99**, which is the first prediction in this project written before the fact
and confirmed by count. New §7 carries the measured baseline m2 is scored against.

**2. The ten gaps ruled** (`c3da82d`). Accepted the five with 3+ independent
confirmations: `until` gains `UNKNOWN(<reason>)`; party rows carry the subject BBLs;
`basis` gains `recorded`; registry rows are CITE-checked and FEED-exempt by design
rather than by accident; card 3 claims the mark, not the moment. **Held** the
single-source five — the homeless private approval right has two instances but only
one document, and the promotion bar is a third.

The new lane check found **uncited registry rows in three of five tables** on its
first run — and closing them produced the round's best finding.

**3. `SEARCH RECORD` — a negative is not a row** (`abd822c`). All three readers with
an uncited registry row **removed it rather than manufacture a quote**, then
independently asked for the same rule. Their reason beat mine: *"I found nothing"* is
not an event — nothing happened — and its evidence is **coverage and sensitivity**,
not a rect around a thing. One reader: *"a document with no fee stamp and a document
nobody looked at produce identical row tables unless the search itself is recorded."*

Negatives now live in a `SEARCH RECORD` block below the table, each region as
`p<N> · [x0,y0,x1,y1]` plus a dpi, so they are falsifiable by re-rendering. The
checker validates the rects and flags a missing dpi.

⚠ **Changing the form changed the substance** — one reader: *"stating it that way
forced me to actually do the search rather than assert it; my original row was backed
only by having read both pages whole."* Another corrected its own *"both margins at
900 dpi"* on finding only one had been. **The row form let a weak negative look
strong.**

**4. `--rect` cropped the page box, not the scan** (`69abab5`). `build()` was fixed
long ago to hand over the native bitmap unresampled; **`zoom()` never was.** On m1 the
box is 10 × 17 in while the scan is 3296 × 5132 — 329.6 dpi across, 301.9 down — so
**every crop made this round was 9.18% narrow**, including every mark rect verified in
five sealed tables. Now crops the scan: the band `[0,0,0.18,1]` renders 593 × 5132,
against 540 × 5100 before.

*Rects are unaffected* — they are normalised, and the ink-run ratios that settled the
flourish dispute divide out any uniform horizontal scale. **The readings held; the
evidence path did not.**

Consequently `native` is a legal sensitivity in a `SEARCH RECORD`, and is the only
honest one for a page with an embedded scan: there is no single dpi, so a number
sends a referee to a different image.

> **Twice now, changing the *form* of a claim exposed something it was hiding.**
> Restating a row as a search record made a reader discover it had swept only two
> margins; restating regions as rects made it find the crop distortion, and its
> coverage went from four regions to eight.

**⏳ Outstanding: nothing.** All five tables gate clean. A's search record is now nine
regions, 0 malformed.

---

# ▶ PHASE A — IN FLIGHT

**`RC_970273` · Richmond DEED · 2 pages · recorded 1955-12-21.** Package already
built; nothing fetched. **Three readers: B, C, D.** A and E deliberately idle — idle
costs nothing, and A is held in reserve as referee, since it did the round's most
rigorous measurement work.

Output: `loop/<X>/RC_970273/table-v2.md`, gate-clean before sealing.

⚠ **Class membership is UNCONFIRMED and that is deliberate.** rd types it `DEED`; m1
was 1911 and this is 1955, so the developer is almost certainly different. Readers
were told to judge membership themselves against the spec's §1 signals and say so.
**If it is not a member, that is a clean result about the signals, not a wasted
round** — and it cost 3 reader-runs on a 2-page document to find out.

Readers were given the standing §7 prediction and told explicitly that **deviation is
a finding, not a correction** — the prediction exists to be wrong in a measurable way.
The anchoring risk of showing them the prediction is accepted knowingly: coverage
cannot be scored without it.

## ▶ PHASE B — QUEUED, not dispatched

**`2002122000002001` · SATISFACTION OF MORTGAGE · 2 pages · ACRIS digital, 2003.**

Chosen as the sharpest available discriminator. On m1, `CAPITAL` fired **0 times in
99 rows** and `TERMINATE` **0 times**. A satisfaction should fire both. If it does,
the class spec is confirmed to be genuinely class-specific rather than a description
of documents in general — and it costs the same as m1, because size drives cost and
this is 2 pages.

Run it **under the same frozen framework** as phase A, then rule both together. No
framework change between them, or phase B stops being a test.

### Budget

6 reader-runs total (3 + 3), against ~13 already spent this session. Both documents
are 2 pages; the largest packaged document is 25 pages and would cost ~12× m1 per
reader. **Size dominates cost, not reader count.**

---

### ⏭ THEN — how to choose m3

**Three readers, not five.** The council localises ambiguity, and the schema now
states most of what it was localising; generalisation is the open question.

**Choose the document deliberately, and note the tension:**
- *Same class* (another platted-subdivision covenant deed) scores the standing
  prediction in §7 — coverage and structural surprise become real numbers, and
  `LOOP.md`'s unit of work is a **class batch**, so this is the orthodox choice.
- *Different class* (a modern typed ACRIS instrument) tests whether the framework
  generalises beyond one 1911 handwritten deed — every rule in it still comes from
  that single document.

**Recommendation: same class.** The prediction is written and unscored; a class batch
converges when two consecutive members add no structural surprise, and nothing can
converge if every draw is a different class. That was `LOOP.md`'s founding diagnosis —
nineteen classes in twenty runs, and no rule ever got a second instance.

Finding a sibling means one indexed lookup, not a corpus walk. The spec names the
cheapest source: **the grantor's other deeds in the same plat** carry near-identical
covenant text.

> ⚠ **Ten hours were lost to a liveness hole.** All five were dispatched; four
> rendered crops and did real work, and every transcript ended on *"writing the
> table"* with no file on disk. Nothing errored, so nothing reported. It surfaced
> only because the user asked.
>
> All five have been **resumed, not re-dispatched** — their reading is still in
> context and redoing it would waste the expensive half. The resume says: write the
> file first, even if incomplete, then gate it.
>
> The rule is now in `OVERNIGHT.md` under LIVENESS: readers write first and refine
> after, and the orchestrator polls disk rather than waiting for a message.
> **Never wait on a reader without a timeout.**

Five readers, identical brief, re-emitting their sealed `RC_1598772` tables into the
redefined schema. **No new reading, no new disk access** — the package already
exists. The question is narrow and deliberately cheap:

> **Is the new schema fillable from a real document?**

If readers who already solved this document cannot produce clean machine fields, the
schema is wrong, and that is much better learned here than on a fresh dispatch.

Output per reader: `loop/<X>/RC_1598772/table-v2.md`
Gate: `python bin/tablecheck.py <table>` must return clean before sealing.

Each reader also reports four things, and **item 3 matters more than the table**:
FEED %, hardest column, **what the schema could not express**, and any row where
`bbls` needed a guess.

## Baseline to beat

| measure | value | source |
|---|---|---|
| FEED (Reconstruction-ready rows) | **0 of 125** | five sealed v1 tables |
| structural surprise | not yet measurable | needs m2 |
| coverage | not yet measurable | needs a scored prediction |

## When all five report — do this

1. Record each `table-v2.md` sha256 **before** reading any of them together.
2. Run `tablecheck.py` over all five. Record FEED % each.
3. Collect the "what the schema could not express" answers. **These are structural
   surprise.** Sort structural from incidental; only structural counts.
4. Rule: does any reported gap force a schema change?
   - A change must name the clause that forced it.
   - **Check it against RC_1598772 itself** — a change contradicting an
     already-read document is rejected or recorded as a branch.
   - Route class-specific findings to `framework/specs/`, mechanical ones to
     `bin/tablecheck.py`, and cross-class ones to `EXTRACT-CARD.md` **only by
     displacing a card**. The card set is capped at twelve.
5. Write `judge/batches/RE-EMIT-1.md` with the numbers and the ruling.
6. Then, and only then, phase 2.

## PHASE 2 — first fresh document

**Do not start until phase 1 is ruled on.** The framework is frozen for a whole
batch; changing it between members turns a test into a fit.

- **Three readers, not five.** The council's job was localising ambiguity, and the
  schema now states explicitly most of what it was localising. Generalisation is the
  open question, so readers-per-document should fall and documents-per-night rise.
- Pick a document **structurally unlike** `RC_1598772` — every rule in the current
  framework came from one handwritten 1911 covenant deed. A modern typed ACRIS
  instrument will show immediately which rules are general and which were fitted to
  one scribe's pen. Candidates already packaged in `loop/docs/`.
- One document in flight at a time. Package via `docpkg.py <id>` only.

## Hard constraints — these do not relax overnight

- **Never touch the corpus.** No directory walk, no navigation-db query, no
  acquisition or reproduction script, no network. `docpkg.py` is the only path.
  See `ACCESS-DISCIPLINE.md`. A heavy reader on the USB volume starves the register
  lane — that already happened once, for three and a half hours.
- **`acris_reproduction.py` is the user's, and it is running.** Do not touch it, do
  not kill it, do not start one. A second process against the registry is the ban
  condition.
- **Workspaces stay narrowed** while reading. Widening is a council step, and the
  council is not an overnight activity.
- **Do not revise the framework mid-batch.** Accumulate findings; rule when the
  batch closes.

## Stop conditions — any one halts the run

1. An integrity problem — `doc_path()` returns a path and the file is absent.
2. A gate failure a reader cannot clear in one attempt. **Never loosen the checker.**
3. Two consecutive members with no structural surprise — the class is closed. This
   is success.
4. Any error touching the db or the store.

A halt writes what it knows and stops. **It never picks another document to keep
busy.**

## Open, carried forward

- No held-out scored set exists, so no number yet says one framework version beats
  another. FEED, coverage and structural surprise are the three that need no gold
  set; a gold set still needs the user's reading time.
- `DEED-RESTRICTIVE-COVENANT.md` has **one member**. Its standing prediction is
  written and unscored until m2.
- Candidate functions with no home in the eleven, from m1: a **private
  discretionary approval right**, and a **parcel definition** (the filed map).
  Promote on a third document, not before.
