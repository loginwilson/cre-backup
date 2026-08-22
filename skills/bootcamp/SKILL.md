---
name: bootcamp
description: Run extraction-bootcamp iterations per the P-5 loop — draw a random completed document from the store, read it cold, reconcile against its rd row, grade it against the three tests, record entries in Bootcamp.md, and bank. Use when the user types /bootcamp (one run), /bootcamp N (N consecutive runs), or /bootcamp auto (keep running until the user returns — overnight learning mode).
---

# THE BOOTCAMP LOOP — iterations of P-5

**The law is `D:\CRE Decoding System\Bootcamp\Bootcamp.md`. Read it in full
before the first iteration of a session** (three Read calls, ~2,900 lines) —
"a rule not loaded at the right moment does not exist." The three tests, the
four process laws (P-1..P-4), the loop itself (P-5), and every G/R/M entry
are the constitution; this skill is only the trigger.

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

The rd row IS the draw sheet — it carries `doc_type`, `pages`, the
recorded date, and everything needed to open the pdf. **Derive the path
from the recorded date** (`By Document\<YYYY>\<MM Mon>\<DD>\<id>.pdf`);
NEVER `rglob` the By Document tree — a full-tree glob hangs for minutes
and was killed twice.

To restock the board with unseen types, sample ids from disk directory
walks and type them with ONE batched indexed lookup (100 ids per query).

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

## 4 · VERDICTS — grade the three tests honestly

Deliver to the user in this exact shape: **1 · The anybody test** (the
summary — real names exact, real terms taught in place, no felt
complexity) · **2 · The data test** (the event table, eleven columns,
anchored, five-state honest, plus claims) · **3 · The event test** (all
eleven functions asked of every page; ledger closed empty or honestly).
Then a candid GRADE with the miss ledger — an unflagged miss found later
costs double.

⚠ **The verdict is a TEACHING artifact, never the DB record** (THE
LENGTH LAW, Bootcamp.md). The corpus stores rows + gated claims +
a summary GENERATED FROM the rows — not this prose. Length in the
verdict is free; length in the spec costs cluster wall-clock.

## 5 · WHY-PASS

Ask "why does it matter" of everything kept — as a FILTER it selects
claims; as an ANSWER it may only produce LABELED HYPOTHESES.

## 6 · ADJUST — write the entries

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
