---
name: project-acris-party-not-a-key
description: "MEASURED - party fan-out grows with observation (93 lots at 25+ docs); \"single-lot\" is a sampling artifact, so party is a candidate set not a key; pass 2 (reference) proven and ready"
metadata: 
  node_type: memory
  type: project
  originSessionId: 36a502fe-953e-4ab9-ab0c-cd3194ce697c
  modified: 2026-08-27T14:09:53.647Z
---

**A "party" route for keying is DEAD, and now on evidence rather than on the
`key_rules` assertion alone.** Measured 2026-08-27 over 120,000 keyed rows
(0.64% of 18.6M), 165,730 distinct party names:

| seen in N docs | parties | **mean lots** | % single-lot |
|---|---|---|---|
| 1 | 115,576 | 1.20 | 93.08% |
| 2 | 36,607 | 1.38 | 82.47% |
| 3-4 | 9,403 | 1.95 | 57.19% |
| 5-9 | 2,488 | 4.90 | 21.26% |
| 10-24 | 1,012 | 12.48 | 2.67% |
| **25+** | **644** | **93.23** | **0.31%** |

⚠ **THE HEADLINE "86.71% SINGLE-LOT" IS BACKWARDS, NOT MERELY SOFT.** Single-
lot-ness is a property of NOT HAVING SEEN THE PARTY YET, not of the party. A
name seen once has fan-out 1 *by construction*. At 0.64% sampling a
once-seen name appears ~156x corpus-wide = the bottom row. **The number decays
as data is added** - the rare case where more evidence makes an estimate worse
instead of tighter. First measurement I ran was scattered across 48 bands
precisely to avoid era-bias, and that is exactly what stopped names from
recurring: it measured my own sampling. **Conditioning on occurrence count is
what exposed it** - any "% single-X" over a sparse sample needs that check.

**Why it can't go in `key` even when correct:** for parcel/reference the
`;`-join means "this document is on ALL of these". A party set means "on ONE of
these". Same column, same syntax, opposite meaning - undetectable downstream.

**What survives:** party as a CANDIDATE SET, its own column, never `key`.
85.34% of unkeyed rows carry an already-seen party; **0% have no party at all**
(universally present, just not discriminating). 33.5% of multi-lot parties sit
on ONE BLOCK = assemblage, where multi-lot is the correct answer. The exact
rule ("full-corpus lot set == 1") is computable but NOT estimable from a
sample - compute it in the same lanes-stopped window as the pass-2 index.

**PASS 2 (reference) IS PROVEN AND READY** - `pass2_migration.sql` +
`pass2_e2e.py` in the session scratchpad, 20 checks green against the live
schema/triggers. Population = **1,279,855 rows = 6.41% of landed**. Three
traps the harness caught that reasoning did not:
- ⚠ `recursive_triggers` DEFAULTS OFF -> chains deeper than one hop silently
  do not resolve. A SQL transitive closure CANNOT substitute: one UPDATE
  cannot observe its own effects, so it finds P but reads Q's key as empty.
  The pragma is PER-CONNECTION - assert it at lane startup, never trust it.
- ⚠ the edge-harvest trigger RACES `key_on_rd` (same event, no documented
  order) - so resolution must ALSO fire on the refs INSERT.
- ⚠ guard on `keyed_by='pdf-pass'`, NOT `''` - `key_on_rd` already writes
  'pdf-pass' for parcel-less rows, so a `''` guard skips its own targets.

Applying it needs the lanes STOPPED (`ix_nav_crfn` reads 21.6M rows' JSON
under a write lock). See [[project-decoder-phase-assertions]],
[[project-acris-resolution-model]], [[feedback-bkrea-scale-failure]].
