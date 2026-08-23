---
name: feedback_phase_organization
description: "Phases get WORSE on return because configs and rules are unaddressable, not forgotten — fix is source×phase docs carrying CALIBRATIONS (value + measurement + failure mode) plus a computed status board"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7c5a3ccb-a88e-40cd-a587-cc575cf7a400
  modified: 2026-08-14T16:11:27.447Z
---

Login, 2026-08-14: *"everytime I return to a phase weve tested, the results are
worse cause we forget configs and rules."* And: *"the hope is to get these phases
nailed down and organized."*

**Why:** the knowledge was never missing — it was **unaddressable**. Six times in
one day the solution already existed in the codebase and was rebuilt or missed:
`selection_delta.py` (written because `map_delta.py` never touches Supabase,
never scheduled) · `bulk.socrata_in()` concurrent while `_by_doc` re-wrote it
serially in a module that already imported it · `arcgis_all()` parallel while
`socrata()` three functions away paged serially (**4.4x unused**) ·
`fuse.py:index_path` designed in and never wired · `acquire_index.py` unused ·
`extract.py` built, never run.

**How to apply:**

1. **`docs/README.md` = source × phase map.** Six phases, from the charter
   (`~/Downloads/NYC CRE Data Decoding System.docx`): selection · acquisition ·
   extraction · resolution · **derivation** · application. Every source walks the
   same six; rules differ per-source-per-phase, hence source first.
   `docs/acris/01..06-*.md` exist.

2. **Seven fixed sections per phase file:** goal · steps we follow today ·
   **calibrations** · rules · built/unwired/unbuilt · traps · promoted docs.

3. **⚠ A CALIBRATION IS A VALUE PLUS ITS EVIDENCE.** A bare `WORKERS = 5` invites
   "optimizing" to 8, which measures SLOWER than serial (throttled). Record
   value · how measured · when · **what breaks if changed**. Never record a value
   not measured here. Re-measure per era — film/book/digital differ. An A/B must
   alternate order and repeat, or a burst-throttled API reports whichever arm ran
   second as faster (this produced a 3.7x-backwards conclusion).

4. **⚠ POINT AT CONFIGS, NEVER COPY THEM.** "threshold at `fuse.py:FUZZY`,
   calibrated 2026-08-13, sweep in `_sweep_fuzzy.json`" — not "FUZZY = 1.0". A
   transcribed value goes stale silently and is then *trusted*. Same rule as
   [[feedback_live_source_over_transcription]].

5. **⚠ STATUS IS COMPUTED, NOT WRITTEN.** `python status.py` reads the state
   files the jobs themselves write, so the board cannot disagree with reality.
   It earned itself on run one: caught a stale `master` record (23,016-row
   "shortfall" against a file that was already correct — `pull()` rewrote state
   wholesale from an in-memory copy and clobbered `repair_tail.py`'s update) and
   a page-key join bug that made extraction agreement read 0.18.
   It also carries an **UNWIRED register** — built-and-unconnected work, which
   nothing else tracks and which is the cheapest work available.

6. **⚠ THE PHASE FILE IS THE PROCEDURE; THE 52 LOOSE `.md` FILES ARE HISTORY.**
   Login: *"many of the loose files are probably not going to be as relevant as we
   have iterated. thats why we need to know the steps we follow today."* A loose
   doc is promoted only after being re-read against current behaviour — never on
   the strength of its title. Nothing has been bulk-promoted.

7. **⚠ REPORT COVERAGE BESIDE SCORE.** The costliest regressions were coverage
   failures wearing a quality mask: `pp_doc.py` succeeding over ZERO pages, a
   300s timeout killing dense pages, film "quality" 77.2%→41.6%. A score over
   fewer pages is a different question, not a worse answer.

**Derivation is its own phase for a stated reason** — Login: *"the data is pre
calc in the database for the app to just worry on ui/ux… it can be made dynamic
in how the database calcs and pulls derivations based on the app we develop."*
The app never computes what it displays. See [[project_acris_selection_job]].
