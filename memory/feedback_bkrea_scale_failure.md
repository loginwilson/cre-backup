---
name: feedback-bkrea-scale-failure
description: "Works on one lot, fails across many — because at scale I read my own summary line instead of the result"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b81cdba8-aef2-4c37-a0d9-9daa59a3b947
  modified: 2026-08-04T13:25:17.172Z
---

**I verify single-lot work by looking at it, and population work by reading a summary line I wrote
myself.** Operator, 2026-08-04: *"you are failing at scale. it's like you start well and can do it
when we focus on one lot, but you fail when we test the method across many. you seem to lose the
rules."*

**Why:** every scale failure has one shape — the step ran, exited 0, printed a confident number, and
the number described something other than what I believed. Measured examples from one session:

```
deriveAcrisDeeds   ran on 7,089 parcels while the territory was 364 (I saw it, rationalized it)
pushDevelopments   wrote 98,368 rows with GATE=1 SET — the flag was ignored, total printed proudly
developer reach    95% on disk, 48% on the card, for eighteen hours
parcelPull         built, tested per-parcel, in NO pipeline — so it only ran when I remembered
duplicate BBL      upsert winner decided by batch boundary, i.e. at random
```

**⭐ THE COUNTER-INTUITIVE PART, WHICH IS THE REAL LESSON: LARGE N HIDES BUGS.** The duplicate-BBL
collision was invisible across 98,368 rows because the copies fell in different 500-row batches;
narrowing to 364 made them collide and fail on the first run. Scale is not the safer test — it is
where errors go quiet. Refining on the small drawn territory before scaling is correct *for that
reason*, not just for cost.

**How to apply:**
- **Print the denominator and where it came from** on every population step. Three of the four
  failures above were denominator errors and each would have been one visible line.
- **End every chain with a live-vs-disk comparison, never a timestamp** — a timestamp says "fresh"
  about a push that wrote the wrong thing (`scripts/liveStale.ts`).
- **A step not in `territoryRefresh.ts` does not exist.** Guarded by `lib/chainComplete.test.ts`.
- **Scope is enforced, not remembered** — `studyArea()` is gated by default, `ALL=1` widens loudly;
  guarded by `lib/territoryScope.test.ts`. Opt-in gating (`GATE=1`) is the same defect as `--write`
  and `MAX=0`: a flag whose forgetful default is wrong.
- Related: [[feedback-bkrea-document-over-page]], [[project-bkrea-territory-intel]].
