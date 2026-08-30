---
name: feedback-source-naming-convention
description: "THE NAMING LAW (login 2026-08-28): per source exactly three names - <source> reproduction / <source> update / <source> audit - for both md and py; 'the naming of these files is where we get bitten'"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d1473bc-bb54-490c-8d66-326f7b72067b
  modified: 2026-08-28T21:30:37.446Z
---

**Per source, exactly THREE named parts, and the md/py FILES carry these
names** (login 2026-08-28, after richmond closed):

    <source> reproduction   the db populating - the CYCLE (sync + monitor
                            inflow -> minters in db logic -> rd cells ->
                            pdf to folder + path/pending/absent)
    <source> update         reports on the CHANGES IN OUR DB (board rows)
    <source> audit          separate check that READS THE SOURCE and
                            compares to our db (enumeration) - a safety
                            check, NOT part of the cycle

**Why:** "the naming of these files for md and py is where we get bitten"
- sessions die and a fresh Claude gets pointed at a NAME; ambiguous names
(rc_lane, batch_walk, routine_update) cost whole sessions of re-discovery.

**How to apply:** new code/md for a source part takes the convention name
from birth (acris_reproduction.py was renamed from batch_walk.py BEFORE
its first run). Existing running code renames only at a safe boundary -
rc_lane.py = richmond reproduction, rename DEFERRED to the key-column
removal ("may be difficult to change with docs inflowing"). Shared
engines (routine_update.py, board_truth.py serve both sources) keep one
implementation; the per-source NAME maps to their ROWS, documented in the
source's reproduction md. Current state:

| name | md | py |
|---|---|---|
| richmond reproduction | D:\CRE Decoding System\Reproduction\richmond reproduction\RICHMOND REPRODUCTION.md | rc_lane.py (rename deferred) |
| richmond update | §4 of that md | routine_update.py + board_truth.py rows |
| richmond audit | §5 of that md | ...\Reproduction\richmond reproduction\richmond_audit.py |

**The Reproduction folder lives at the CRE ROOT on OneTouch
(`D:\CRE Decoding System\Reproduction\`), one SUBFOLDER per source**
(login moved richmond's into `richmond reproduction\` themselves,
2026-08-28) — acris gets `acris reproduction\` when it proves.
richmond_audit.py holds an ABSOLUTE path to the decoder modules, so it
runs from any location.
| acris reproduction | (md after the test proves) | acris_reproduction.py (UNTESTED group-entry design) |
| acris update | (with the md) | same shared board engines |
| acris audit | (exists as acris_census.py machinery; formalize on acris close) | - |

See [[project-rc-sync-closed-20260828]], [[project-acris-pooled-method]].
