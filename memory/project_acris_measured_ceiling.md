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

## ⚠ THE rd CEILING IS ACRIS-SIDE, AND NO LOCAL HARDWARE MOVES IT (2026-08-26)

Everything above is the **pdf** lane's tempo ladder. The **rd** lane has a
different axis — worker count — and its ceiling is not ours to raise.

    1 arm x 12   13.8 docs/s
    1 arm x 28   26.9 docs/s
    1 arm x 64   41.9 docs/s   (warm)
    1 arm x 80   43.4 docs/s   (warm, CLEAN)  <- +25% workers, +3.6% only
    4 arms x 28  REFUSED (112 connections, twice in one day)

**THE TEST THAT SETTLES IT: workers ÷ throughput = seconds per request.**

    12w -> 0.87s      28w -> 1.04s      64w -> 1.53s      80w -> 1.91s

Latency more than DOUBLES while throughput flattens. We are not getting more
documents, only making each request wait longer — the signature of queuing at
the SERVER. A local bottleneck would show rising latency too, so the curve
alone is not proof; what makes it proof is that every local candidate was
measured and excluded (below).

⚠ **login's reading — "warm up determines success, so we can push the ceiling"
— was the natural inference and it was wrong.** 64 and 80 warm to the SAME
number. Warm-up carries you TO the ceiling; it does not raise it. The tell is
convergence, not the climb.

### EVERY LOCAL CAUSE, MEASURED AND EXCLUDED

    CPU        rd_walk uses 0.58 of 8 cores            not CPU/GIL bound
    network    ~40 Mbps used of an 866 Mbps link,
               default route direct (VPN adapter idle) not link bound
    disk       lane barely touches the DB: feeder is
               1 query per 10,000 docs on a COVERING
               index (ix_nav_rd_todo), writer is 1
               commit per 200 rows, workers read 0    not disk bound
    RAM        1.5 GB free, cache crushed to 0.2 GB,
               commit 29.4/32.5 GB — real distress,
               but the lane does no DB reads to starve not the rd constraint

**SO: ~43-44 docs/s sustained is not buyable.** SSDs (arriving ~2026-09-09) will not speed
acquisition. They pay off in decode — extraction passes, parcel
reorganization, board queries — and possibly in OTHER sources, which are
parse-and-write shaped rather than request-throttled.

### THE STORAGE SHAPE (why the fix is small)

    the database        22.5 GB     0.84%  (projects to ~29 GB at 100% rd)
    the documents    2,640.1 GB    99.16%

The DB is a rounding error. Only the 0.84% needs seeks; the 99.16% is read
sequentially. Keep DB + hot working set on flash, bulk store on the big HDD.

⚠ D: is a Seagate One Touch **spinning USB** disk: ~200 IO/s, 8–12 ms seeks.
At 0% idle it is SEEK-bound at 2–5 MB/s, not swamped. `board_truth` reads it
CONTINUOUSLY to recompute counts — a dashboard taxing the disk 24/7, worth
throttling before decode.

### ⚠ TWO MEASUREMENT TRAPS I FELL INTO IN ONE HOUR

**1 · `Get-Process` HAS NO `ReadTransferCount`.** `$p.ReadTransferCount`
returns `$null` for every process, renders as `0.00`, and produces a clean
table of zeros. I concluded "no process is reading the drive" and built an
argument on it. **A property that does not exist reads as silence, not as an
error.** Use `Win32_PerfFormattedData_PerfProc_Process` (`IDProcess`,
`IOReadBytesPersec`), which resolves per-PID.

**2 · THE OBSERVER WAS THE LOAD.** With correct counters the largest reader of
the One Touch was `claude` at 2.17 MB/s — my own log tails, query plans and
stat calls, above every lane. Diagnosing a saturated disk by repeatedly
reading it measures the diagnosis.

⚠ And per this file's own standing rule: 42 docs/s is a measurement of THIS
day. Re-probe before treating it as the system's ceiling.
See [[project-acris-bulk-acquisition]], [[project-decoder-fleet-restore]].

### ⚠⚠ THE OBSERVER RUINED THE EXPERIMENT, NOT JUST THE DISK READING

I first scored the 80-worker hour at **37.5 docs/s sustained** and told login 80
was worse than 64. login asked the question that broke it: *"why would 80 =42.6
we be worse than 64 at 41.9?"* Mapping per-minute output to wall clock:

    20:32 min 28  20.8   my CPU measurement + disk counters
    20:39 min 35  24.6
    20:44 min 40  17.1   recursive Get-ChildItem over ALL of C:\ (98GB Users)
    20:49 min 45   9.3   WORST MINUTE OF THE HOUR - end of that scan
    20:52 min 48  28.0   my 24-sample correlation loop
    ---- I stopped measuring at 20:55 ----
    20:58 min 54  51.3
    20:59 min 55  58.0   BEST MINUTE OF THE HOUR

**Four of the five worst minutes were mine.** Clean average from min 52 on =
**43.4 docs/s**, ABOVE the 41.9 credited to 64w. login's original "last call
came in 43.4" was a CLEAN reading from min 15; I then buried the signal under
my own load and blamed the worker count.

⚠ I had already written the observer-effect lesson into this file ONE HOUR
EARLIER, for the disk reads - and did not apply it to the throughput numbers
sitting in the same table. **Knowing you are the load does not automatically
propagate to every number you are holding.** Before scoring any run, ask which
minutes contained your own commands and exclude them, or measure nothing while
a timed run is in flight.

⚠ AND THE EXCLUSIONS ABOVE INHERIT THIS. CPU/network/disk/RAM were all
sampled DURING the contaminated window. The reasoning still stands, but those
figures were taken under a load I created - weaker evidence than first stated.

### ⚠ AND THE "CEILING" DOUBLED THREE HOURS LATER (2026-08-26 21:46)

After the USB unplug forced a full lane restart, measured TWO independent ways:

    db row-count delta (90s)   72.7 docs/s
    board rate_now             69.25/s      (avg 80.39/s over 20 min)

**vs the 43.4 "clean ceiling" measured at 20:55 the same night.** Roughly
double, and not noise - two independent measures agree.

Cause NOT established. Three untested candidates: lighter ACRIS load near
22:00 than 20:30; fresh connections after the restart; and no diagnostics
loading the box. ⚠ Do not pick one without evidence.

**So "~43-44 docs/s is not buyable" above was overconfident.** The SHAPE of
that argument survives - more workers still did not buy more throughput, and
the latency curve was real - but the NUMBER was a measurement of one hour.
This file already says exactly that ("a ceiling measured once is a measurement
of that hour, not of the system") and I wrote a firm figure anyway, three
paragraphs below the warning. ⚠ **Quote the rate WITH ITS CLOCK TIME, always,
or the number outlives the conditions that produced it.**

### ⚠⚠ AND AT 21:55 IT REFUSED - THE SPEED WAS THE CAUSE (2026-08-26)

Nine minutes after measuring 72.7 docs/s and calling it good news, ACRIS served
its Bandwidth Notice. rd_walk detected it and stopped itself:

    run end: +110,158 in 28.4 min (64.6 docs/s) - 8 failed

    this run    110,158 docs
    prior run   176,148 docs
    ---------------------------------------------
                286,306 docs x 118 KB  =  ~33.9 GB today

**THE DOUBLED THROUGHPUT WAS NOT A WINDFALL, IT WAS THE TRIP.** I had stated
the correct model hours earlier - *"speed doesn't raise the total, it only
decides how fast we spend the day's allowance"* - and then failed to apply it
when the number moved in a pleasing direction. 72/s burns the allowance ~1.7x
faster than 43/s. **A rate that rises is a budget draining faster, not a
ceiling lifting.** Check the CUMULATIVE bytes before celebrating a rate.

⚠ This also re-explains the 21:46 doubling without needing a new mechanism:
running hot right up to a volume wall looks exactly like a raised ceiling
until the wall arrives.

WHAT DID NOT NEED FIXING: rd_walk honored stop-on-refusal by itself; fleet.py's
roster does NOT contain rd_walk (only acris_lane/rc_lane/routine_update/
board_truth/org_backfill_arm), and acris_lane is PAUSED - so the Fleet Guard
CANNOT restart an acris lane. Verified, not assumed. Richmond is a different
host and kept running.

### RETRACTED: THE 21:55 "REFUSAL" WAS OUR OWN FALSE POSITIVE (2026-08-26 22:05)

**Everything in the section above about a Bandwidth Notice at 21:55 is WRONG.**
login challenged it - *"Are you sure its a bandwidth notice. just reset and got
a 500 error"* - and one probe settled it:

    same doc id that "REFUSED":  HTTP 200 - 118,158 bytes - real document
    contains "Bandwidth Notice": False
    contains "bandwidth" at all: False

ACRIS never refused. `check_refused()` fired on its loose second clause,
`"bandwidth" in html[:2000].lower()`, during a WIFI OUTAGE (7,795 URLErrors in
the same fails file) - almost certainly a router/ISP interstitial. rd stopped
itself for the night over a page ACRIS never sent.

⚠ **AND SO THE "SPEED CAUSED THE TRIP" LESSON ABOVE IS ALSO RETRACTED.** The
33.9 GB arithmetic was real but explained nothing - there was no trip to
explain. I built a satisfying causal story (fast pull -> budget burn -> refusal)
on a premise I never checked, and it survived because it FELT like a lesson I
had earned earlier in the day. ⚠ A story that flatters a rule you already
believe deserves MORE scrutiny, not less.

**THE REAL DEFECT: A DETECTOR THAT HALTS A PIPELINE MUST PRESERVE ITS
EVIDENCE.** check_refused() stored nothing, so "was that actually a notice?"
was unanswerable and I asserted the answer anyway. FIXED in live_delta.py:
  - the loose clause now also requires "DOCUMENT ID" to be ABSENT (a real
    document always echoes it; an interstitial never does)
  - `_preserve_refusal()` writes the triggering page to
    _working/refusals/ so any future verdict can be AUDITED, not believed
  - proven on four shapes: real doc mentioning bandwidth PASSES, interstitial
    REFUSES, genuine notice REFUSES, ordinary doc PASSES

⚠ URLError IN BULK IS A LINK FAILURE, NOT A REFUSAL. A real ACRIS refusal is
HTTP 200 carrying a ~25,103-byte notice - it produces NEITHER URLError NOR a
500. Thousands of URLErrors means OUR side of the wire. Same lesson as the
hotspot earlier the same day, missed twice.

RESUMED 22:01 at 28 workers: 45.1 docs/s, 0 fails.

### ⚠⚠ THE REAL WALL ARRIVED AS HTTP 503, AND THE LANE WAS BLIND TO IT (22:07)

Resumed 22:01 at 28 workers. Clean for six minutes (16,576 docs, 45-52/s,
0-2 fails). Then:

    22:07  fails  6,127
    22:08  fails 19,160   <- ~13,000 failed requests in ONE MINUTE
                             `total` FROZEN at 16,576 - no documents at all
    22:13  probe: HTTPError 503
    22:14  killed

**A REFUSAL DETECTOR THAT ONLY READS BODIES IS BLIND TO EVERY REFUSAL THAT
ARRIVES AS A STATUS CODE.** check_refused() inspects the HTML of a SUCCESSFUL
reply, so it can only ever catch the 200-with-notice shape. HTTPError 503
raises before there is a body, fell through to the generic `except`, was
logged as an ordinary fail, and the worker took the next id. The lane retried
into the wall ~19,000 times in a minute.

⚠ I FIXED check_refused() AT 22:05 AND FELT DONE. Two minutes later the real
refusal walked in through a door I had not looked at. **Fixing the detector I
was already thinking about is not the same as asking what ELSE a refusal can
look like.** The shapes seen so far: 200 + notice page · 503 · 429.

FIXED in rd_walk.py: `except urllib.error.HTTPError` BEFORE the generic catch;
counts CONSECUTIVE 503/429 (any success resets it via stats["h503"]=0), and at
H503_STOP=40 calls stop.set(). 28 workers reach 40 in seconds, so the wall now
halts the lane instead of being hammered.

⚠ THREE DIFFERENT FAILURES IN ONE NIGHT, EACH LOOKING LIKE THE LAST:
    21:22  drive unplugged  -> alive but wedged, err log EMPTY
    21:55  wifi drop        -> OUR false-positive "Bandwidth Notice"
    22:07  genuine 503 wall -> invisible to the body inspector
Only the third was ACRIS refusing. **Do not reason from "it stopped again" to
"same cause" - all three presented as a stopped lane.**

TODAY'S TOTAL: 176,148 + 110,158 + 16,576 = ~302,882 docs = ~36 GB. Whether
the 503 is cumulative-daily or rate-based CANNOT be told from one observation.
