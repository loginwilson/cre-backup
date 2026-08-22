# THE MAP

**Read [WORKFLOW.md](WORKFLOW.md) for the model. Read this for where things are.
Then run `python status.py` for what state they are in.**

```
docs/
  WORKFLOW.md          the source→product model — applies to EVERY source
  sources/
    acris/             ← the first source. Each step of the sanitization:
      01-specification/    workflow.md · data.md · selection.md · index.md
      02-acquisition/      workflow.md · data.md
      03-extraction/       workflow.md · data.md
      04-resolution/       workflow.md · data.md
      05-derivation/       workflow.md · data.md
  products/            outside the sanitization — reads derivations
```

**Folders are sources. Inside a source are the five sanitization steps. Product
is not in there** — it sits downstream with its own store.

## SOURCES × THE FIVE STEPS

| source | 1 specification | 2 acquisition | 3 extraction | 4 resolution | 5 derivation |
|---|---|---|---|---|---|
| **ACRIS** | ✅ [complete](sources/acris/01-specification/workflow.md) | [begins 2026-08-17](sources/acris/02-acquisition/workflow.md) | [3 channels + fusion](sources/acris/03-extraction/workflow.md) | [contract built](sources/acris/04-resolution/workflow.md) | [systematic only](sources/acris/05-derivation/workflow.md) |
| DOB NOW / BIS | partial (`dob.py`) | — | — | — | — |
| DCP / BSA / LPC | partial (`dcp.py`, `bsa.py`, `lpc_cofa.py`) | — | — | — | — |
| DOF / PLUTO | partial (parcel spine) | — | — | — | — |
| **HPD · OER · DOS · ZAP** | **nothing** | — | — | — | — |

⚠ **Four sources in the diagram have no work at all.** Naming them beats a table
that only lists what exists.

## ACRIS · SPECIFICATION — the two standing tracks

Login, 2026-08-14: *"selection is document id daily. Index is support index
daily."*

| track | keeps current | state |
|---|---|---|
| **selection** — [selection.md](sources/acris/01-specification/selection.md) | the doc-id map, 17,049,742 | ✅ reconciled ACRIS ↔ local ↔ Supabase |
| **index** — [index.md](sources/acris/01-specification/index.md) | the support index, 100,764,843 | ✅ 5/5 datasets exact |

⚠ **Specification never finishes** — Live Sync loops back into it. Both dailies
run, both are proven to detect (28,374 and 174,163 rows over a forced window),
and they cross-check: `index_daily`'s master delta equals `selection_daily`'s
count for the same window.

## ⚠ NAMING: THE DIAGRAM SAYS "SPECIFICATION", THE CODE SAYS "SELECTION"

In the model, **specification** is the phase. In this repo, "selection" now means
one *track inside it* (the doc-id daily), which is Login's own refinement and is
sharper than either alone.

⚠ **The scripts still carry the old sense** — `selection_cross.py` audits the
doc-id map (the track), but `selection_daily.py` and `_selection_*` state files
predate the distinction. **Not renaming code on the eve of acquisition**; six
scripts and a live 04:00 routine is the wrong trade today. Recorded so the two
are known to be the same thing rather than quietly diverging.

---

## ⚠ WHY THIS STRUCTURE EXISTS

Login, 2026-08-14: *"everytime I return to a phase weve tested, the results are
worse cause we forget configs and rules."*

The knowledge was never missing. **It was unaddressable.** Measured in one day:

- `selection_delta.py` was written *because* `map_delta.py` never touches
  Supabase, said so in its own docstring, and was never scheduled.
- `bulk.socrata_in()` chunks concurrently; `acquire_index._by_doc` rewrote the
  same chunking serially, inside a module that already imported it.
- `arcgis_all()` counts-then-parallelises; `socrata()` three functions away paged
  one at a time. **4.4x** sat unused.
- `fuse.py` accepts an `index_path` and records `"structured_record": false` —
  the third channel was designed in and never wired.
- **`selection_cross.py` proved all three sides agree and wrote it to one state
  file, while `selection_daily.py` looked for a watermark in another** — so the
  daily refused every night with *"run selection_cross.py first"*, which had
  already run and passed.

That last one is the pattern in its purest form: the proof existed, in a file the
job that needed it never read.

## ⚠ THE PHASE FILE IS THE PROCEDURE. THE LOOSE DOCS ARE HISTORY.

Login: *"many of the loose files are probably not going to be as relevant as we
have iterated. thats why we need to know the steps we follow today."*

The `.md` files in the repo root were written across weeks and **most have been
superseded by work that did not go back and edit them.**

- **Each phase file carries THE STEPS WE FOLLOW TODAY** and is self-sufficient.
- **A loose doc is HISTORY unless a phase file explicitly promotes it** by name.
  Unpromoted means unverified, not wrong — never quote one as a rule without
  re-checking it against the code.
- **Promotion requires reading it against current behaviour**, not recognising
  the title.

Nothing has been bulk-promoted. That list starts short on purpose.

## LONG-RUN TRAPS

Live in memory, not here — they cross sources and steps:
`~/.claude/projects/C--Users-smile/memory/project_acris_*.md`
