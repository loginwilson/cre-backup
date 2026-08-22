# ⚠⚠ READ THIS FIRST - ACRIS REFUSED AT 23:49 ON 2026-08-19 ⚠⚠

    _STOP contains:   refused 2026-08-19 23:49
                      (no signal detail captured)

**ACQUISITION IS STOPPED ON PURPOSE. DO NOT DELETE `_STOP` TO RESTART IT.**
The standing rule is *on a refusal: stop; do not retry, do not rotate anything.*
The run halted itself, `_STOP` was deliberately left in place, and nothing has
been retried.

## What is safe to believe

    nav table       COMPLETE and PASSED its gate (see below) - unaffected
    Richmond pull   COMPLETE, 2,426,404/2,426,404, 0 errors - unaffected
    acquisition     STOPPED. 5 parcels, 29,342 pages landed before the refusal.
    night_watch     STILL RUNNING (pid varies). Harmless - see the warning below.

## ⚠ night_watch WILL PRINT A LINE THAT IS NOT TRUE

At ~06:00 it runs its last two steps and logs:

    NIGHT WATCH DONE - acquisition running on the live table

**With a refusal `_STOP` present, acquisition will NOT be running.** overnight.py
declines to start (exit 2) and says so in `C:\tmp\acq.log`. The "DONE" line is
printed unconditionally by code that was already loaded when the refusal
happened and could not be corrected in place. **Verify with the process list,
never with that line.**

    powershell "(Get-CimInstance Win32_Process -Filter \"Name like '%python%'\" |
      Where-Object { $_.CommandLine -like '*overnight.py*' }).Count"

## Probable cause - my bug, stated plainly

`night_chain.py` step 6 compared `now.hour >= 6`, which was true at 23:28, so it
started a SECOND acquisition driver at 23:30 while the first was still running:

    23:30 - 23:40   8 workers, ~160 connections, against a MEASURED ~80 ceiling,
                    both drivers walking the same worklist in the same order
    23:41           halted via _STOP, restarted as ONE driver (4 workers)
    23:49           ACRIS refused

Causation is not proven - the refusal came ~9 minutes after returning to a
single driver - but a ten-minute burst at twice the connection ceiling is the
most likely explanation and no other change was made in that window. Recorded as
bootcamp **N-14**.

## What to do in the morning

1. **Decide, do not react.** Read `_STOP`. The refusal carried no detail text,
   so there is no stated duration or reason to work from.
2. If resuming: delete `_STOP` **deliberately**, and restart at a LOWER
   concurrency than 4x20 - the previous measured-safe setting ran 4x20 for one
   process count, not two. Consider 2x20 for the first hour and watch.
3. Do NOT rotate anything, do not change the user agent, do not retry faster.
4. The 4am sync hits **Socrata** (index data, app-token, low volume), which is a
   different service from the image server that refused. It ran or will run
   normally; that is not a retry of the refused endpoint.

---
# SESSION RESUME — 2026-08-19 NIGHT (read this first after compaction)

Login is out for the night. The instruction, verbatim:

> *"we have to get nav complete, perfrom acq till 4, sync, get navv back to
> lvie, and continue acq again"*
> *"by the time i go to work you are back at acq cause the sync and nav have
> resovled for the live state and continued the acq"*

Everything below is state, not plan. **Do not restart anything that is already
running.**

---

## 1 · WHAT IS RUNNING

    PID 33600   night_chain.py            the controller  -> /tmp/chain.log
    PID 32372   rc_detail_pull.py c80     the ORIGINAL pull -> /tmp/rcpull.log
    PID 32252   rc_detail_pull.py c80     the chain's DUPLICATE sweep (see below)

Monitor task `bmlic3h17` reports stage transitions and alerts on
`REFUSED|Traceback|LINK DOWN`; it exits when it sees `NIGHT CHAIN DONE`.

**Chain sequence** (steps 1-4 done or in flight by the time you read this):

    1 wait out the pull        2 sweep error rows        3 rc_detail_land --apply
    4 nav_build                5 acquisition --until 03:50
    6 hold for _routine_4am.tsv mtime change (kill_acq at 03:50 as backstop)
    7 nav_build again          8 acquisition --until 23:00   -> NIGHT CHAIN DONE

## 2 · TWO PULLS ARE RUNNING AND THAT IS KNOWN

`pull_alive()` compared `rc_detail.jsonl` size 20 seconds apart. The pull
commits in LUMPS, so at 21:51 a healthy pull at 80% read as dead and the chain
started a second `--conc 80` sweep on the same worklist.

**Assessed, not ignored.** Appends are one flushed record at a time so lines
cannot interleave; landing is keyed so duplicates are no-ops; the redundant
sweep finishes AFTER the real pull so stage ordering still holds. Cost is ~70k
duplicate fetches. **0 errors on both after an hour.** A kill was denied by the
auto-mode classifier and was judged not worth pressing.

`pull_alive()` is FIXED on disk (asks the process table; 300s fallback window) —
but PID 33600 loaded the old code, so the fix lands on the NEXT run, not this
one. Recorded as bootcamp **N-11**.

## 3 · NAV_BUILD NOW REFUSES REDUNDANT REBUILDS — this DOES take effect tonight

The 4am routine ends with a nav rebuild AND the chain rebuilds at step 7. Two
full passes over 11 GB, acquisition back 24 minutes late.

Fixed in the JOB, not either scheduler (`nav_build.py --force` overrides):
a full rebuild is refused when `parcel_spec.db` (max of `db` and `-wal`) is
older than the csv it produced. Proven on 4 cases both directions before
being trusted. Bootcamp **N-12**.

⚠ `-wal` is load-bearing and `-shm` is POISON. SQLite writes land in `-wal`
before checkpointing, so the `.db` mtime alone would skip needed rebuilds. But
`-shm` is touched by any connection OPENING, including read-only ones and
nav_build's own — including it made the guard see a newer source every time and
**never fire at all**, which would have reported a fix while changing nothing.
Corrected before it ever ran.

## 3b · TWO MORE FIXES THAT LAND TONIGHT (both in freshly-launched scripts)

**`overnight.py` no longer erases a refusal.** It opened with an unconditional
`STOP.unlink()`. The refusal path writes `refused <when>` into that same file and
says "delete to resume later" — meaning a person. The chain restarts acquisition
after the 4am sync, so the unlink would have deleted a refusal and resumed
against the source that refused us. Now: `refus`/`denied` in the contents →
print it verbatim, exit 2, leave the file. Anything else → clear as before.
Tested both ways. Bootcamp **N-13**.

**`nav_verify.py` is new** — the phase gate. Reads the CSV, not the database it
was built from, because a gate that queries the source proves the source is fine
and says nothing about the artifact acquisition opens.

    python nav_verify.py                 the real table
    python nav_verify.py <path>          any table, for testing

Gates (pass/fail, exit non-zero): UNKEYED == 0 · doc id present · endpoint
present · endpoint is a MINTING url. Coverage (printed, never a gate, marked
`cov`): Richmond index, ACRIS parties. Proven against a fixture built to break
it — which is how two bugs in the gate itself were found. Bootcamp **G-034**.

⚠ If acquisition is NOT running in the morning, check `_STOP` FIRST:

    python -c "import corpus_paths as CP,pathlib;p=pathlib.Path(CP.STOP);print(p.read_text() if p.exists() else 'no _STOP - not stopped')"

A file containing `refused` means ACRIS declined and **the run stopped on
purpose**. Do not delete it to make things start again — read it, and decide.

## 4 · MORNING CHECK — one command each

```bash
tail -5 "C:/Users/smile/Downloads/Source Folder (Real Estate Data)/Decoder Prompt/decoder/_routine_4am.tsv"
```

Each line is `timestamp<TAB>stage:rc:seconds …`. **`rc` of `0` or `SKIP` is
clean; anything else failed.** The chain proceeds past the sync regardless of
its verdict — deliberately, so one bad stage does not cost the whole day — so
this TSV is the only place the verdict is recorded.

    grep -c "NIGHT CHAIN DONE" /tmp/chain.log     1 = step 8 reached
    tail -3 /tmp/acq.log                          acquisition progress
    tail -3 /tmp/chain.log                        current stage

## 5 · WHAT TONIGHT'S ACQUISITION COVERS — printed, per bootcamp N-10

                                        parcels      doc links     share
    IN THIS RUN                       1,157,165     25,373,106    86.53%
    excluded: Staten Island             188,905      3,089,643    10.54%
    excluded: >2,000 docs (139 giants)      139        704,724     2.40%
    excluded: block 99999                   103        157,082     0.54%
    CORPUS                            1,346,312     29,324,555   100.00%

**Staten Island is excluded ON PURPOSE** — Login supervises the start of
Richmond document acquisition personally. Verified `--boro 1,2,3,4` returns
zero borough-5 parcels.

The 139 giants (deepest `1010090037`, 79,980 docs) need a run whose unit of
work is the PAGE, not the parcel — at `--hi 99999999` all workers park on one
document set and nothing ever completes or resumes.

⚠ The admin filter `substr(bbl,2,5)<>'99999'` catches BLOCK 99999, not high
LOTS. 1,942 lot>=7500 parcels (24,040 docs, 0.08%) remain in the pool
deliberately. Note `2039299999` is lot 9999, NOT block 99999 — the two look
alike in a BBL and are different filters.

## 6 · PRE-FLIGHT ALREADY DONE — do not redo

    land        rc_detail_land.py report-only: 2,439,798 detail records,
                8,526,069 parties, 2,905,701 lot links, image_state
                present 2,436,127 / pending 2,963 / ERR 708
    acquisition selector returns 1,157,165 parcels, Staten Island = 0
    4am task    ACRIS_CORPUS_ROOT unset at User/Machine/Process — no phantom
                corpus. _finish() writes the TSV AFTER navigation, so the chain
                cannot start a concurrent rebuild.
    dead paths  every `D:/acris` hit in the 4am scripts is a DOCSTRING example,
                not live code. The examples are still misleading and should be
                corrected when convenient.

## 7 · THE OTHER THREAD — the ZLDA is fully read

`2010102601040006` read end to end (110 pp). Bootcamp is at **r45** with a new
`FULL-DOCUMENT RUN` section (D-1…D-9) and the extraction rewritten at
`03 Extractions/…/Gold Set/1-00800-0049/ZLDA 2010 - extraction.md`.

Answer to Login's standing question: **$93.32 per buildable sf** — 53,578 zsf
for $5,000,000, price from the cover stamps with two independent taxes agreeing
to the dollar. **$/sf by LOT is not in the document** and the pro-rata split is
a derivation that must never price a comparable.

Model impact from the ZLDA: **no new columns.** One new field state —
`unavailable` (the source does not have the page) — which made the four-state
section five, corrected in place.

## 8 · THE TABLE GREW — RANDOM-DOCUMENT RUN 3 ADDED `effect`

A cold 4-page TL&R (`2012121901163001`, Queens 1266/1) could not be written in
the frozen columns: a TERMINATION came out identical to a GRANT. `function` says
which kind of thing, `mode` says whether it moved, neither says what happened to
it. Added `effect` — `creates · transfers · modifies · releases` — to the SPINE.

    17 release-effect doc types = 4,977,173 of 24,037,915 documents = 20.7%

One document in five is a release, so without it one in five rows said the
opposite of what it meant. Derive it from the DOC TYPE (an authority we already
hold and which covers the whole corpus), never from direction — role inversion
scores 100% on transcription and reverses the lineage silently. The type SEEDS
it per document; the clause CONFIRMS or overrides per row.

⚠ The freeze criterion RESET. Four documents have been read end to end; the
corpus has 126 types. `effect` was back-filled into the ZLDA extraction and all
five rows re-judged — all `creates`/`transfers`, none changed meaning, which is
exactly why that document could never have found the gap.
