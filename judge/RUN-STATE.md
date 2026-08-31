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

### ⏭ NEXT, in order

1. **Rebuild `framework/specs/DEED-RESTRICTIVE-COVENANT.md` from the five sealed
   tables** — not by patching. Every error corrected above traces to one cause: the
   spec was seeded from the orchestrator's reading of m1, which is the reading five
   readers overturned 5–0. Patching a bad source yields a patched bad source, and
   LOOP.md's rule is that a spec is built from banked members. Needs fresh context
   (~120 KB of tables).
2. **Rule the ten schema gaps** in `RE-EMIT-1.md`. Five carry 4–5 independent
   confirmations; `until`'s missing third state and the homeless private approval
   right carry **5 of 5**. Route to spec / checker / card — the card set is capped at
   twelve, so a new card must **displace** one.
3. **Then m2** — three readers, not five, and a document structurally unlike an 1911
   handwritten covenant deed.

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
