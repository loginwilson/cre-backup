# Round ledger

Orchestrator-owned. Agents do not write here.

One row per phase, plus the hash commitments. The hashes are the point: recorded
when an agent posts DONE, re-verified when the round is revealed. A hash that
moved between those two moments means a committed file was edited after the
agent could have seen the other table — the round is void and the document is
spent.

---

## Setup — 2026-08-29

| | |
|---|---|
| operative spec | `04 Extractions\TRAYCER.md` · sha256 `3acb8a8f674a7e27c9f53c11b1afa33a8de207e141e9ffbe13fe0f3ee8a74aac` |
| identical to | `C:\Users\smile\Downloads\TRAYCER_3.md` (same hash — the pasted copy and the on-disk spec are one file) |
| orchestrator | `663740bc-5dde-4f8f-aa2a-e422380ab12c` |
| extractor A | `a4b71377-faae-49bd-a52e-21a6af570528` · claude / opus[1m] / max |
| extractor B | `385c2a70-15f5-46f1-8a88-310aa77018c0` · codex / gpt-5.6-sol / max |
| target model | UNNAMED — building against the weakest plausible open-weight floor |
| size ceiling | extraction build ≈ 15k tokens, set before any score was visible |

---

## Block 1 — framework creation

### Drafting phase (blind)

| | A | B |
|---|---|---|
| briefed | 2026-08-29 | 2026-08-29 |
| `A/B DRAFT DONE` | — | — |
| `framework.md` | — | — |
| `matrix-spec.md` | — | — |
| `surveyed.md` | — | — |
| `draft-notes.md` | — | — |

### Reconciliation

| | |
|---|---|
| published to `framework\drafts\` | — |
| points of disagreement | — |
| v1 written by | A (pen) |
| v1 verified by | B |
| v1 sha256 | — |

### Output

| | |
|---|---|
| first document id | — |
| rule expected to break | — |

---

## Round 1

Not started.

<!-- template for each round:

| | A | B |
|---|---|---|
| document id | | |
| framework version in | | |
| DONE at | | |
| extraction.json | sha256 | sha256 |
| resolved.md | | |
| objections.md | | |
| notes.md | | |
| hashes re-verified at reveal | | |

matrix differences:
event-table differences that vanish at the matrix (logged, no rule):
both-flagged-the-same-gap:
neither citation supported either value:
rules added/changed:
frozen test cases:
emitted-to-flagged ratio:
version out:
next document id, and which untested rule it strains:

-->
