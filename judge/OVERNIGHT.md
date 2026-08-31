# The overnight harness

**Nothing in this file runs without explicit approval.** Written after a session in
which unattended work broke a live registration pull.

## What can run unattended, and what cannot

| step | unattended? | why |
|---|---|---|
| draw the next member of a class | yes | one indexed db lookup |
| build the package | yes | `docpkg.py <id>`, one document |
| dispatch N readers | yes | mechanical |
| gate each table with `tablecheck.py` | yes | arithmetic and format |
| score coverage + structural surprise | yes | counting against a written spec |
| log surprises to the spec's §6 | yes | append only |
| **change the framework, a card, or a spec** | **NO** | see below |

**The framework is frozen for the whole batch.** This is not caution, it is the
method: `LOOP.md` §I.3 records three cures that passed on the run that produced them
and failed on the very next document. A rule changed between members turns the batch
from a test into a fit, and nobody is awake to notice.

So overnight **accumulates scored readings**. Judgment happens when you are back.
That is a real limit, and stating it is better than pretending otherwise.

## The unit of work

A **class batch**, never a random document. Five members of one class, read in
sequence against a spec written before any of them is opened.

    for each member of the batch:
        1  read specs/<CLASS>.md and record the standing prediction
        2  docpkg.py <id>            -> the package, built once
        3  dispatch to N readers, blind, workspaces narrowed
        4  wait for every table to seal
        5  tablecheck.py <table>     -> GATE. a table is not sealed until clean
        6  score: COVERAGE, STRUCTURAL SURPRISE, INCIDENTAL SURPRISE
        7  append surprises to the spec's §6. CHANGE NOTHING ELSE.
        8  next member

## ⚠ LIVENESS — the hole that silently ate a whole night

**A reader can end its turn mid-work with everything in context and nothing on
disk.** It does not error, it does not report, and it does not appear stalled: the
orchestrator is simply waiting for a message that will never arrive.

> *Measured 2026-08-31. Five readers were dispatched, four rendered crops and did
> real work — one had already settled the marks by measurement, "strikes 22.1% and
> 7.5% longest dark run, flourishes 1.8% and 1.6%" — and every transcript ended on
> the words "writing the table." No table existed. **Ten hours passed**, and it was
> found only because the user asked whether anything had happened.*

Two rules follow, and the harness is not unattended-safe without both:

**1. Readers write first and refine after.** The brief must say so explicitly: *a
partial table on disk beats a perfect one in context.* An artifact that exists can
be gated, scored and resumed; one held in context is lost the moment the turn ends.

**2. The orchestrator polls for liveness, and never just waits.** A reader is
STALLED when its output file is absent AND nothing in its folder has changed for
30 minutes. On detecting a stall: **nudge once** — resume, do not re-dispatch, since
its reading is still in context and redoing it wastes the expensive half. If the
file is still absent 30 minutes after the nudge, that reader is **dead for this
round**: record it, proceed with the readers that sealed, and do not block the batch
on it.

Liveness is checkable from disk alone — file present? folder mtime recent? — so it
costs nothing and needs no cooperation from the reader.

## Stop conditions — any one halts the batch

1. **An integrity problem** — `doc_path()` returns a path and the file is absent.
   Report with the id. Never treat as "no image."
2. **A tablecheck failure a reader cannot clear in one attempt.** Do not loosen the
   check to make it pass.
3. **Two consecutive members with no structural surprise** — the class is CLOSED.
   That is success, and it stops.
4. **Budget** — a stated ceiling on reader-runs, decremented per dispatch.
5. **Any error touching the db or the store.** Halt, do not retry, do not improvise
   an alternative path.

A halt writes what it knows and stops. **It never picks a different document to keep
busy.**

## Hard constraints

- **One document in flight at a time.** No parallel packages, no prefetch.
- **`docpkg.py` is the only path to a file.** See `ACCESS-DISCIPLINE.md`.
- **No directory walk, ever** — the store is on a USB volume the register lane
  writes to, and a heavy reader collapses the writer's throughput without a single
  network call.
- **Workspaces stay narrowed.** Readers never see each other's folders while
  reading. Widening is a council step and the council is not an overnight activity.
- **Crops go to the reader's own folder**, never the shared package — a crop's
  filename is the rect it was cut from, which tells the next reader where to look.

## The morning artifact

One file, `judge/batches/<CLASS>-<n>.md`:

- the standing prediction, verbatim, as written before the batch
- per member: coverage %, structural surprise count, incidental surprise count
- the accumulated surprise log, sorted structural first
- **a proposed spec diff — proposed, not applied**
- every halt, with its condition

Then the batch is ruled on with you awake: each proposed change is checked against
the class's prior members, and **a change contradicting an already-read document is
rejected** or recorded as a branch.

## What this is measuring

Not whether a document was read correctly — there is no answer key and the
orchestrator is not one.

It measures whether **the spec predicted the document**. Coverage says the read found
what the spec knew to look for. Structural surprise says how much the spec did not
know. Only structural surprise has to fall; incidental surprise is unbounded because
documents are messy, and a spec that drove it to zero would be a spec that had
stopped looking.

**Falling structural surprise across a class is the only thing in this system that
constitutes learning.**

## Before the first unattended run

Run one member **supervised**, end to end, and confirm: the package built from the
stored path, the gate actually rejected something, the score came out, and nothing
touched the corpus outside `docpkg.py`. A harness that has never been watched
succeed is not a harness.
