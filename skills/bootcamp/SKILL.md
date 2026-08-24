---
name: bootcamp
description: Run extraction-bootcamp iterations per the P-5 loop — draw a random completed document from the store, read it cold, reconcile against its rd row, grade it against the three tests, record entries in Bootcamp.md, and bank. Use when the user types /bootcamp (one run), /bootcamp N (N consecutive runs), or /bootcamp auto (keep running until the user returns — overnight learning mode).
---

# THE BOOTCAMP LOOP — iterations of P-5

**The law is `D:\CRE Decoding System\Bootcamp\Bootcamp.md`. Read it in full
before the first iteration of a session** (~5,400 lines) — "a rule not
loaded at the right moment does not exist." The three tests, the process
laws (P-1..P-5), and every G/R/M entry are the constitution; this skill is
only the trigger.

⚠ **AND READ `D:\CRE Decoding System\Bootcamp\Compose Card.md` AGAIN AT
EVERY COMPOSE STEP — every run, not once per session.** It is short by
design because the authority file is too long to consult per sentence.
The measured failure mode of this whole system is rules that exist but
are UNADDRESSABLE when they would fire: the length law was broken by its
own author within the hour, and the motive-claim ban failed on its third
run after two recorded corrections. The card is the fix; loading it is
not optional.

## Modes (from the argument)

- **no argument** — ONE iteration, then stop and report. The
  watch-and-monitor mode: the login likes to push back mid-run, and the
  best rules have come from exactly that. **Deliver report + why-pass
  WITHOUT a self-grade** — the login prompts for the grade after
  reading (outside-the-momentum grading is more objective; login
  2026-08-22). Grade only when asked.
- **a number N** — N consecutive iterations, each complete (recorded and
  graded) before the next begins. Batching changes the PACING, never the
  DELIVERY: every run in the batch gets the FULL verdict format (anybody
  test, data table, event test, grade + miss ledger, why-pass pairs) —
  never a shortened digest (login 2026-08-22).
- **`auto` / `until-back`** — the overnight mode: keep running full
  iterations back-to-back until the login sends a message; ALWAYS finish
  and record the current run before stopping (a half-recorded run is
  worse than one fewer run). Report a one-line progress note after each
  run (doc id · pages · grade · streak) so the morning read is a table,
  not archaeology. Corrections and rulings queue up as usual — never
  decided silently just because nobody is watching.

  **THE GRADE ROTATION (login 2026-08-22): never grade in the same
  breath.** Each iteration opens by GRADING THE PREVIOUS RUN — re-read
  its banked entry cold (a full document of other work has displaced
  its momentum) with the adversarial checklist: (1) relationship or
  motive claims stated as fact (family, heirship, business role, cause
  of delay/death — the measured defect class); (2) unmarked inferences
  anywhere in summary or table; (3) vacuous reconciliation ✓s (was the
  document-side reading strong enough to EARN the agreement?); (4)
  single-look values on degraded film. Then draw the next document.
  Sequence: grade N-1 → run N report → grade N → run N+1 report → ...
  The LAST run of the night stays ungraded — the login grades it in
  the morning (keeps the human in the calibration loop).

## 1 · DRAW — the DRAW BOARD first, db-first always

`D:\CRE Decoding System\Bootcamp\Draw Board.md` holds typed candidates
(doc_type · recorded date · id · size) and marks what has been drawn.
Check `Run Log.md` for eras/types already covered, then take an UNSEEN
type × era cell — never prefer ease.

**The db is READABLE while the lanes acquire** (login 2026-08-22): WAL
allows unlimited readers alongside the single writer. Open read-only
with a timeout and use INDEXED lookups (`WHERE id=?`, `id IN (...)`) or
a BOUNDED rowid window (`WHERE rowid BETWEEN r AND r+500`) at a random
offset — that is a range read, not a scan. **Barred: full-table scans
(they walk millions of rows) and any write (that seat is the lanes').**

**THE DRAW QUERY** (login 2026-08-22 — "shouldn't it be as easy as
reading doc id rows with their rd and pdf columns filled"). The rd row
IS the draw sheet and the `pdf` column IS the path. One query yields
type, pages, borough AND the file:

```sql
SELECT id, recorded_details, pdf
  FROM navigation
 WHERE rowid BETWEEN ? AND ?          -- bounded window, indexed
   AND pdf IS NOT NULL AND pdf != ''
```

NEVER `rglob` the By Document tree — a full-tree glob hangs for minutes
and was killed twice. Never derive the path from the date; read it.

⚠ **The landed PDFs are a CONTIGUOUS PREFIX**, rowid 1 .. ~210,000 of
24,117,334 — acquisition fills in order. A uniform random window over
the whole table returns ZERO rows and reads as "no pdfs exist." Draw
inside the landed band. ⚠ `pdf` may hold the sentinel `"imageless"`.

The band is already four-borough and type-rich (QUEENS 548 · BROOKLYN
474 · MANHATTAN 423 · BRONX 157; MORTGAGE 503 · DEED 169 ·
ASSIGNMENT-MORTGAGE 155 · AGREEMENT 149 · SATISFACTION 147 · INITIAL
COOP UCC1 123 · POWER OF ATTORNEY 86 · DEED-OTHER 61), so **type, page
count and borough are all selectable at draw** — that is the point of
the method. Runs 1–39 skewed Richmond/old only because the disk-walk
method sampled whatever was on disk.

⚠ **SEALED FIELDS AT DRAW TIME** (Compose Card #14). Read ONLY
`type`, `pages`, `borough` and `pdf` from the drawn row. `parties`,
`amount`, `doc_date`, `parcels` and `remarks` STAY SEALED until §3 —
rd is the VERIFIER, never the prior (R4-4). Print only the four
unsealed fields; do not dump the row at draw.

⚠ `pages` is the MAIN-document count (cover + instrument) and is NOT
the pdf's page count — supporting documents are appended beyond it.
**Render and read the whole file, never `pages` pages** (R40-1).

## 2 · READ COLD — every page, no rd fields in view

Small pdfs: Read the file directly. Large ones: render via fitz at dpi=120
into the scratchpad and Read each page image (pdftoppm is not installed):

```python
import fitz, pathlib
doc = fitz.open(SRC); print("pages:", len(doc))
for i in range(len(doc)):
    doc[i].get_pixmap(dpi=120).save(OUT / f"p{i+1:03d}.png")
```

Maintain the open-events ledger (P-1) — events open until a later page
closes them or the last page confirms `unread`. Load reading guards
(G-003/029, R4-4) now; composing guards (G-015..023, R-004, G-018) when
building rows; render guards (G-024/025/026/036/036a) when writing the
summary.

## 3 · RECONCILE — the rd row, field by field

One indexed lookup (safe on the hot table):

```python
con.execute("SELECT id, keyed_by, key, recorded_details FROM navigation WHERE id=?", (DOC_ID,))
```

Agreement = free verification. Disagreement = a finding, never smoothed.
⚠ Negative claims about the index require READING the full index field
(R7-4 — the parties list must be printed in full before any claim about
it). If the document cites package siblings, pull their rd rows too.

## 3a · THE ASSUMPTION LAW (Bootcamp.md, 2026-08-22)

Every delivered statement is READ (anchored), VERIFIED (two witnesses),
or INFERRED — and inferences are MARKED IN THE SENTENCE. Unknown beats
wrong: "too faint to read" is a deliverable; a guess is corpus poison.
rd can settle a faint reading but never upgrades unread → read (mark
"accepted, rd sole witness"). If something cannot be done, say so as
the result.

## 4 · VERDICTS — **RE-READ THE COMPOSE CARD FIRST**

`D:\CRE Decoding System\Bootcamp\Compose Card.md` — nine checks, read
before writing the first sentence of any verdict. Tier every sentence
(READ / DERIVED / INFERRED); apply the class-vs-instance test to any
imported knowledge; state EFFECT, never intent; scan for trigger words;
keep entities distinct from officers; keep the instrument's own nouns;
earn every ✓; respect the length budget; say plainly what could not be
done.

## 4a · VERDICTS — the three tests, in the RE-RULED delivery order
## (login 2026-08-24, run 41; full spec: Bootcamp.md THE SHAPE)

Deliver in this exact order: **1 · The event test** FIRST — the eleven
functions asked of pdf AND rd, which fire (mode + effect), which do
not, any candidate twelfth dissolved (G-020) or queued; mode-watch
notes; what is NOT an event; "ledger closed empty." **2 · The data
test** — the event table as the evidence: one row per event, parties
in from/to or as ACTOR-CLAIMS on the event id (the party ruling:
entity AND its paired human names, always), then Claims ·
⚠ Unresolved · Reconciliation. **3 · The anybody test** LAST — the
summary anybody understands: CAST first, real names exact, real terms
taught in place, recitals attributed, no felt complexity.

**Single-run loop:** deliver 1-2-3 → STOP (no self-grade, no why) →
login prompts "grade and why" → deliver THE GRADE-AND-WHY FORMAT
(below, exactly) → login prompts "fix and record" → fixes BY ACTION
(grep the count, take the crop, correct the banked text) → four-file
close → next draw. Batch/auto mode self-grades per the rotation.
Pre-bank passes produce ARTIFACTS (crop files on disk, greps run in
the same action) — Card #12/#13; a remembered action is not a check.

## 4b · THE GRADE-AND-WHY FORMAT (login ruling 2026-08-24, run 46 —
## re-taught twice in one session; follow it EXACTLY)

The "grade and why" reply is TWO blocks, in this order:

**BLOCK 1 — THE GRADE, with its reasonings.** Everything about my
performance lives here and ONLY here:
```
R<n> GRADE (self, cold checklist, ledger read first) — <letter>
<one-line framing: how many misses, which classes/structures hit>
1. <Miss: CLASS name + member list from the Ledger; what I delivered;
   what the page actually holds; which rule/structure it broke; the
   honest phrasing that was free.>
2. ...
HELD: <single paragraph: the disciplines that worked, defects caught,
arithmetic that ran clean, cells exercised — the credit side.>
<if the grade needs justifying: one "Why <grade> and not <higher>" line.>
```

**BLOCK 2 — WHY, simple points.** This is about THE DOCUMENT'S EVENTS
— never about the grade (the why-pass of P-5 §5, delivered here per
the run-41 re-ruling). One point per data-table event or event
cluster. Each point has the fixed shape:
```
WHY <the event> matters — terminates at <the product/phase it feeds>:
<the full explanation in system terms>. = <ONE sentence in plain
language anybody could understand — the "=" line is MANDATORY.>
```
The "= " restatement is the login's read; the explanation before it
is the system's. Both are required; neither substitutes for the
other. Close with "Ready for fix-and-record on your word."

Format failures recorded 2026-08-24 (run 46 grading): (a) delivered
the grade as essay sections with headers instead of numbered
misses + HELD; (b) wrote the WHY about the grade instead of the
document's events; (c) dropped the "explanation = simple restatement"
pair shape. Each was corrected by the login in-session. The format
IS the deliverable; a right grade in the wrong shape reads as wrong.

⚠ **The verdict is a TEACHING artifact, never the DB record** (THE
LENGTH LAW, Bootcamp.md). The corpus stores rows + gated claims +
a summary GENERATED FROM the rows — not this prose. Length in the
verdict is free; length in the spec costs cluster wall-clock.

## 5 · WHY-PASS

Ask "why does it matter" of everything kept — as a FILTER it selects
claims; as an ANSWER it may only produce LABELED HYPOTHESES.

## 6 · ADJUST — **THE FOUR-FILE CLOSE** (a run is not done until all four)

  1 `Bootcamp.md`     run entry + any new law
  2 `Run Log.md`      one-line stamp (id · pages · streak · grade)
  3 `Grade Ledger.md` the graded miss BY CLASS + where the fix landed
  4 `Draw Board.md`   mark the drawn document off — IN THE SAME COMMIT
                      (an unmarked board silently re-offers drawn docs
                      and the coverage claim goes false unnoticed)

Plus `Lexicon.md` when a document teaches a CLASS-LEVEL term (the
Context Line's tier-2 lookup — never add from memory, only from a
document). Plus `Compose Card.md` when the fix is compose-time
behaviour.

⚠ **At grading, READ `Grade Ledger.md` first.** Name the miss CLASS, not
the instance; if the class already has rows, say so and grade harder — a
repeat of a recorded lesson costs double. A class reaching 3+ rows is a
MISSING STRUCTURE, not a discipline problem: change the shape instead of
writing another rule.

## 6a · ADJUST — the entries themselves

Append the run to Bootcamp.md (`# RANDOM-DOCUMENT RUN <n> — <id> ...`,
R<n>-x findings with teaching anchors, CONFIRMATIONS block) and stamp
`Run Log.md`. Judgment calls go to the RULINGS QUEUE marked
`ruling: pending` (P-3) — never decided silently. A wrong recorded
finding is corrected in place, loudly, the same day.

## 7 · BANK

`powershell -NoProfile -ExecutionPolicy Bypass -File C:\dev\cre-backup\refresh.ps1`
(or note that the nightly sync will carry it).

## Standing constraints

- No nav-table scans; indexed lookups only. Never touch the acquisition
  lanes or their throughput.
- The streak (consecutive runs forcing zero schema changes) is measured
  across runs; report its new value each run.
- Cost note for long overnight chains: each long document costs real
  context; if context runs low mid-iteration, finish and record the
  current run before starting another.
