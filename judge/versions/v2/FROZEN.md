# v2 — FROZEN 2026-08-30

This release is frozen as the working base. **No further revisions until the
document queue has run.** Findings from documents go to a v3 backlog; findings
from re-reading v2 do not.

Reason: v2 went through three review cycles against one extracted document.
That ratio is backwards. The framework is now ahead of the evidence, and the
only thing that can tell us what is actually wrong with it is documents.

## Frozen bytes

| file | sha256 (16) | bytes |
| --- | --- | --- |
| `framework.md` | `506b88d823d06a6b` | 129,413 |
| `matrix-spec.md` | `34b95ef778f1630a` | 31,084 |
| `discovery.schema.json` | `40b9254e1bcddef6` | 14,042 |
| `enrichment.schema.json` | `73367921c088fcaf` | 18,809 |
| `extraction.schema.json` | `3f147c8cec6d7952` | 60,260 |
| `template.json` | `33cc33579c92bea5` | 2,107 |
| `fixtures/positive.json` | `1cd49f1321af0ea2` | 9,913 |
| `fixtures/fixturecheck.py` | `5a42532f2f292a53` | 2,066 |
| `v2-notes.md` | `ecedcfe587728085` | 21,640 |

## What is verified

- all 32 schema definitions satisfiable (`bin/schemacheck.py`, 0 UNSAT)
- 16 fixtures pass, 5 negatives correctly rejected (`fixtures/fixturecheck.py`)
- the round-1 defect list (15 items) is incorporated

## What is NOT verified — carried openly, not hidden

These were B's returns 1–3. They are real. They are deferred because none of
them blocks reading a document, and all of them are cheaper to settle once we
know which parts of the framework documents actually exercise.

| gap | consequence while frozen |
| --- | --- |
| no prompt compiler / dependency manifest | passes are assembled by hand; `emitted_by:"BUILD_TOOL"` is a self-assertion |
| no `version-gate.md`, no recorded gate run | release provenance is this file, nothing stronger |
| partition not tested (no shadow-diff runner) | **run FULL_BUNDLE only.** Partitioned loading is unproven and must not be used |
| per-pass dependency closure unproved | a lens may cite a rule it did not load; watch for confident `NO_HIT` |
| `FR-EV-008` coverage not stated for every literal table | filler/alias residue unknown on some paths |

**Operating rule while frozen:** every run is `FULL_BUNDLE_V2 /
PARTITION_NOT_TESTED`. Cost is the price of not testing two things at once.

## Unfreezing

v2 unfreezes when the queue has produced enough evidence to say which of the
above actually cost us an event. Not before.
