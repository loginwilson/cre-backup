---
name: project-acris-measured-ceiling
description: "The acris ladder now finds its ceiling by measuring output, not by a number anyone typed — design, the first measured result (91.3/s = 7.90 docs/s), and the traps it was built to avoid"
metadata: 
  node_type: memory
  type: project
  originSessionId: d8ac9502-9d7e-49e0-8048-b07c41ae0f18
  modified: 2026-08-25T01:04:40.362Z
---

**THE LADDER STOPS WHERE OUTPUT STOPS IMPROVING.** login's design, 2026-08-24:
*"dont pick a stop point. the point where the ceiling no long is improving is
where you stop"* and *"increase every 10 minutes until you see diminishing
returns. let it sit at the diminished rate for 20 minutes and if not out
producing the before stage, it goes back to the previous step... but you have
to make sure the rung starts hot so it doesnt take forever to find ceiling."*

    --step-minutes 10      a rung is ~3,900 documents, not ~780
    --confirm-windows 2    20 min at the suspected plateau before believing it
    --plateau-margin 0.02  a rung must beat the best by 2% to be "progress"
    --warm-fraction 0.9    start hot off the banked peak, or 10-min rungs
                           take hours from cold
    --reprobe-minutes 90   forget the peak and climb again; a ceiling is not
                           a constant

## ⚠ THE FIRST MEASURED CEILING (2026-08-24 20:23–21:03, richmond running)

    rung  tempo   delivered      ready docs/s   verdict
      1   83.3    79.3 (95%)     6.26           new best
      2   91.3    88.9 (97%)     7.90           NEW BEST <- the peak
      3   99.3    85.9 (86%)     7.54           plateau suspected (1/2)
     cfm  99.3    86.5 (87%)     --             confirmed (2/2) -> REVERT

**Pushing past the peak cost output AND delivery** — 7.90 -> 7.54 docs/s while
delivery fell 97% -> 87%. That is the diminishing-returns point, and it is the
first ceiling in this project that was measured rather than asserted.

⚠ **THIS IS A SHARED-LINK CEILING, NOT AN ACRIS LIMIT.** richmond was drumming
at ~14.5 docs/s throughout. Expect a higher acris ceiling once richmond
finishes — which is exactly what `--reprobe-minutes` exists for.

## ⚠ FOUR TRAPS THIS DESIGN EXISTS TO AVOID (all hit for real)

**1 · CLIMBING ON THE WRONG NUMBER.** The gate used to ask "did the wire carry
what we asked for" (delivered >= 90% of commanded). That can say YES while the
extra requests buy NO extra documents. The ladder now judges **ready docs/s**.

**2 · A SHORT WINDOW IS NOISE.** At ~6.5 docs/s a 2-minute rung is ~780 docs.
Measured twice: the first rung after a restart read 3.96 then 4.22 ready/s
because the window contained the lane's own SPIN-UP, making the next rung look
like a "+59% improvement" that was mostly the first number being wrong.

**3 · A 6-MINUTE CONFIRM CAN SIT INSIDE ONE DIP.** During rung 3 pdfs/min ran
462,464,477,489,462,471 then slumped to 282 and recovered to 467. A short
confirm landing on the slump would have banked a ceiling that was really one
bad minute. 20 minutes spans dip and recovery.

**4 · UNDER-DELIVERY MUST FEED THE REVERT, NOT BYPASS IT.** ⚠ I introduced
this one: the 90% gate ran BEFORE the ready-rate test and `continue`d, so the
lane hit 93.4/s, printed "holding" while delivery decayed 91%->87%->77%, and
would have sat on the WRONG SIDE of its own peak all night. Falling short of
90% now sets `ready = 0.0` and falls through to the confirm windows.

⚠ **AND NEVER REVERT TO AN UNPROVEN BEST.** `best_rps` starts at 0.0; a lane
under-delivering before recording any best would set `tempo.rps = 0`, which is
a divide-by-zero in the pacer (`next_at += 1.0/rps`), not a slow lane. Guarded
with `best_rps >= 1.0`.

## ⚠ AND THE HONEST-MEASUREMENT LESSON

I "proved" an earlier version by simulation using a curve where the value at
93.4/s **was a number I typed**, because the bug meant `settle()` never ran
there. login caught it: *"is that peak legit or just made up from what you
think or did the step up test you just ran find it? big difference."* The
simulation proved the ALGORITHM; it said nothing about where the peak was.
**A simulated input inside a real-looking table is indistinguishable from a
measurement.** Label the fabricated cell or do not draw the table.

`HARD_CEILING` is now 400 and is a RUNAWAY BACKSTOP ONLY — it was 150, which
would have become "the ceiling" while the curve was still rising. See
[[project-acris-consolidated-lane]], [[project-acris-ua-and-deadlock]].

## ⚠ THE RE-PROBE EARNED ITS KEEP ON THE FIRST TRY (2026-08-24 22:33-23:13)

90 minutes after settling at 91.3/s, the ladder forgot its peak and climbed
again. It found a MATERIALLY HIGHER ceiling with no human input:

    rung  tempo   delivered      ready docs/s   verdict
     re   91.3    90.9 (99%)     7.74 (90 min)  re-probe baseline
      1   99.3    97.3 (98%)     8.34           new best
      2  107.3   105.6 (98%)     8.74           NEW BEST <- the peak
      3  115.3    99.2 (86%)     --             under-delivered (1/2)
     cfm 115.3    92.6 (80%)     --             confirmed (2/2) -> REVERT

**91.3/s -> 107.3/s and 7.90 -> 8.74 docs/s, a +11% gain nobody asked for.**
⚠ And richmond had NOT finished - it was still drumming at ~15 docs/s
throughout. So the 21:03 ceiling was not a link ceiling at all; it was a
TRANSIENT one, and a settled-forever ladder would have sat under it all night.
**A ceiling measured once is a measurement of that hour, not of the system.**

⚠ NOTE HOW THE CONFIRM WINDOWS EARNED THEIR TIME BOTH WAYS. At 21:03 the two
windows agreed the plateau was real. At 23:03->23:13 delivery DEGRADED across
them (86% -> 80%), which is stronger evidence than a flat repeat: pushing
harder was actively making it worse.

**FAILURES DO NOT TRACK TEMPO.** Measured across the climb 91 -> 115/s: fails
rose ~2 per 5 minutes at a FLAT rate (33 at 21:59 -> 54 at 22:59) with no
inflection at any rung. A constant background rate, not congestion - so a
rising fail count during a climb is not by itself evidence the climb is
hurting.
