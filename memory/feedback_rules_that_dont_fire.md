---
name: rules-that-dont-fire
description: "A rule fails at the moment it would fire, not at the moment it's written — phrase-scans catch phrase-shaped defects only; workflow steps need a checklist"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-23T00:42:10.876Z
---

Measured across bootcamp runs 33-37 (2026-08-22). The system's dominant
failure mode is NOT missing rules — it is rules that exist and do not
fire:

- The motive/narrative ban existed from run 10 and failed at 33, 34, 35.
- The trigger-word list (written at 35) fixed the PHRASE-shaped version
  and was blind at 37, where the same defect used ordinary words
  ("Freddie Mac owns millions of home loans" — no trigger word in it).
- The name-integrity rule was written at midday after finding "Leader"
  for LEIDER, and did not fire hours later on the same day.

**Why:** the enforcement shape must match the defect shape. A word scan
catches word-shaped defects. It cannot catch (a) unanchored claims built
from ordinary vocabulary, or (b) a WORKFLOW step that was skipped — a
missing action has no phrase to match.

**How to apply:** three distinct mechanisms, not one —
1. **word scan** (Compose Card #4) for motive/relationship/scale phrasing;
2. **pre-bank checklist** (Card #12) for workflow steps: NAMES re-read at
   high dpi, SOURCES cite a Lexicon entry, SLOTS canonical + role-labelled;
3. **structure** where a class hits 3+ occurrences — make the bad state
   unrepresentable (e.g. amount slot REQUIRES a qty_role) instead of
   writing another rule.
Recurrence is tracked in `Bootcamp\Grade Ledger.md`; the ledger is read
BEFORE grading. See [[context-line-compose-card]],
[[bootcamp-four-file-close]].
