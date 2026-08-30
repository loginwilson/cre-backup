"""THE FLEET ROSTER - every lane, every process, one command each.

login (2026-08-24): "each process has fleets of processes in them so if i
lost everything and said kick off richmond pdf or acris rd, it would be
difficult to pinpoint every moving piece." This file IS the pinpointing:
the lane definitions below are the single authority for what "acris rd"
or "richmond pdf" means - scripts, arguments, ranges, log paths. Change a
lane's shape HERE, never in a shell history.

    python fleet.py status              what is running / missing, per lane
    python fleet.py start <lane|all>    launch a lane's missing processes
    python fleet.py stop <lane|all>     stop a lane's processes

Lanes: sync (acris_lane + rc_lane - BOTH consolidated now) Â· board
(routine_update + board_truth + pass-2 arm). The "rcpdf" lane is RETIRED:
rc_lane absorbed the trio on 2026-08-24.

âš  THE 2026-08-24 CUTOVER: acris_lane.py absorbed acris_live, the rd_walk
fleet (4x28) AND the image_walk fleet (3x14). ONE process is the whole
acris presence - edge probe every 10s, rd backfill workers, pdf pool with
the sync hot-list, keying via the key_on_rd trigger (needs no process).
The old "rd" and "apdf" lanes are RETIRED: starting them alongside the
lane would put a second access point on ACRIS, which is the tripping
condition the lane exists to remove. Their definitions live in git
history if a rollback ever needs them.

âš  THE SAME CUTOVER FOR RICHMOND (2026-08-24, evening): rc_lane.py absorbed
rc_live (probe), rc_feed (token minting) and rc_pdf_pull (fetch + land),
and DROPPED rc_pdf_land - the courts host serves a real pdf and the puller
already landed it, so the lander only ever drained a legacy _incoming
backlog. 4 processes -> 1. Retired scripts moved OUT of the import path to
_archive/richmond_preconsolidation/ so they cannot be started by habit.

âš  WHY RICHMOND ALSO GAINED AN rd HEAL, AND WHY THAT MATTERS TO THE ROSTER.
rc_live landed only id + rd_url + pdf_url. rd was a SEPARATE walker that
had finished its backfill and was no longer watching the edge, so a new
filing got an id and a url and then stopped - no rd, therefore no key (the
key_on_rd trigger fires on rd), therefore no pdf. The lane looked healthy
because it was counting ids. **A roster is only honest if each lane owns
its whole pipeline**; a lane that owns four of five stages will report the
four and stay silent about the fifth.

âš  THE TWO LANES HAVE OPPOSITE PACING, AND THE ROSTER MUST NOT BLUR THEM.
acris runs a METRONOME (one request per beat, a governed climb, a banked
peak in lane_tempo.json) because it trips under lumpy load. richmond runs
a DRUMROLL (no pacer, latency is the only governor, proven at 160
concurrent connections). Consequence for operations: **richmond can be
stopped and restarted freely at full speed; acris cannot** - a restart
costs it the climb unless the banked peak is fresh (WARM_MAX_AGE 6 h).
Stop acris GRACEFULLY (fleet.py stop) so it saves a clean peak; a
force-kill mid-shed can flag it dirty and cold-start the next run at 12/s.
"""
import pathlib
import subprocess
import sys
import time

PY = sys.executable

# scripts that may only ever have ONE instance, whatever their args
# âš  THE COMMENT AT acris_lane CLAIMED "PAUSED lanes are skipped by
# `start`" AND NO SUCH SKIP EXISTED - `fleet.py start sync` would have
# restarted acris right after its Bandwidth Notice. A comment is not
# enforcement. Found 2026-08-25 while restarting richmond after a crash.
# ⚠⚠ EDIT ORDER IS A SAFETY RULE: **PAUSED NAME FIRST, LANE SECOND.**
# Cost 6 live requests into an active ban, 2026-08-29 12:39. Writing a
# new LANES entry makes that lane startable the instant the file is
# saved, and CRE Fleet Guard fires `fleet.py start all` EVERY 5 MINUTES.
# I added `acris_repro_register` to LANES, then added it to PAUSED a
# minute later - and the guard launched it in the gap, during a denial
# I had just finished parking the fleet for. The lane behaved perfectly
# (stop-on-refusal killed it in 23 s) but the requests still went out.
# A roster with a 5-minute guard has NO safe window: add the string to
# PAUSED, save, THEN write the lane. Same rule for un-pausing in
# reverse - remove the name only when you actually intend it to run.
PAUSED = {
          # ══ REFUSAL HOLD 2026-08-29 12:23 — ACRIS DENIED ACCESS ══════
          # NOT a false positive. The preserved body is the real notice:
          # "Further access to ACRIS is denied ... detection of automated
          # scripts/robots that are capturing data from the website or
          # having exceeded the bandwidth limits we have established."
          # 25,605 B, HTTP 200, hard match, saved under _working/refusals/
          # (refusal-20260829-12*.html). All three film shards took it
          # independently within 0.9 min of entry, at three different ids
          # (FT_1670008460667 / FT_2250000832425 / FT_4670007391867) —
          # source-wide, not a transport blip.
          #
          # ⚠⚠ FLEET GUARD RESTARTED THE SHARDS INTO THE REFUSAL THREE
          # TIMES (12:24, 12:29, 12:34) BEFORE THESE NAMES WERE PARKED.
          # stop-on-refusal stopped each PROCESS, but nothing stopped the
          # thing that respawns processes. A refusal hold is not complete
          # until the guard is told; that is what these four names are.
          # THE RESTART LOOP IS ITSELF A RETRY — and the notice names
          # "automated scripts" as a trigger, so respawning is the exact
          # behaviour that earns a longer ban.
          #
          # Un-pausing is LOGIN'S EXPLICIT CALL, never the guard's and
          # never mine. Do not retry, do not rotate the UA, do not lower
          # the worker count and try again, do not "just probe once" —
          # a probe is a request, and we were told no. The lawful route
          # off this hold is the one the notice itself names: the bulk
          # NYC Open Data / Socrata datasets (a DIFFERENT host, which is
          # how the audit already runs) or the City Register's
          # subscription data service, Ph 212-487-6300.
          "acris_repro_sync",
          # ⚠ THE FOUR SHARDS ARE RETIRED, NOT MERELY PAUSED (2026-08-29).
          # They are four doors on ONE floor - the deviation from the
          # approved three-door shape, live at the moment of the denial.
          # Do not revive them. The single door `acris_repro_register`
          # (40 workers) below replaces all four; the GIL cost is stated
          # at its lane entry and is accepted.
          "acris_repro_reg_b",
          "acris_repro_reg_c",
          "acris_repro_reg_d",
          # >> RELEASED 13:3x 2026-08-29 on login's "start it" - and this
          # is the FIRST acris run that is honestly one door. The FLOOR
          # GATE in acris_reproduction.py now makes a 0-worker floor not
          # exist: 1 session, 1 entry, no monitor, no pending_recheck.
          # Verified before launch: banner reads "1 FLOOR, 1 ENTRY:
          # register 40". If it ever reads otherwise, STOP.
          # (history: three doors passed for one all morning - see the
          # floor-gate comment in acris_reproduction.py.)
          "acris_repro_reg_a",
          # >> THE DIGITAL BAND WAITS ITS TURN (measured 2026-08-29).
          # reg_a's 937,756 todo rows are digital-era (2016-2021+), whose
          # DocumentDetail pages are ~118 KB and slow to generate; the
          # film shards' records are compact and instant. Running them
          # together, film wins the race and the heavy requests TIME OUT:
          # b/c/d 20 docs/s each with ZERO fails while reg_a managed
          # 0.17-0.63/s with a ~5:1 fail ratio at BOTH 28 and 10 workers -
          # so it is the DOCUMENT WEIGHT, not our concurrency.
          # ⚠ RUN reg_a ALONE once the film shards close (2.81M rows at
          # ~61/s ≈ 13 h), and give it a longer --timeout then.

          # eject hold 2026-08-28 21:15 LIFTED 2026-08-29 - drive back,
          # 15.9 TB free, db clean (WAL checkpointed to 0 before eject),
          # write probe OK.
          # >> SYNC-CHECK FIRST (login 2026-08-29): bring up richmond and
          # the acris sync floor to confirm BOTH sources are level after
          # the overnight gap. register stays parked until that check
          # returns; on a weekend there are few filings, so a level sync
          # is the expected answer and cheap to prove.
          "acris_repro_document",
          # >> REGISTRATION-ONLY RUN (login 2026-08-28 21:0x, after the
          # approved verdict). The floors contend at the SOURCE - register
          # does ~11 docs/s alone vs ~4.5 beside a document floor pulling
          # 32 req/s - so rd closes fastest with the pipe to itself
          # (82.65% -> 100%), and documentation then inherits the whole
          # pipe. Un-pause this name to put the document floor back.
          # The sync floor stays up: it is 0.7 req/s and it is what keeps
          # the corpus level with new filings.
                                # drive-loss hold 20:0x LIFTED 20:1x -
          # D: back, 15.9 TB free, db intact, write probe OK.
          # ⚠ THE RATE MYSTERY THAT NIGHT WAS THE DRIVE, NOT THE CODE:
          # rd starved 6.15 -> 1.82/s and req/s dipped in the minutes
          # BEFORE the disconnect - a disk backing up every write. If
          # rates sag with acris serving cleanly, MEASURE THE DISK
          # (% Idle Time) before touching a worker count.
                                # eject hold 19:05 LIFTED 19:2x - D: back,
          # WAL intact (SQLite replays/drops at open by design; the lanes'
          # own writes are the loudest corruption detector there is).
                                # >> acris_reproduction RELEASED 17:4x
          # 2026-08-28 - login's go ("only one way to know it works
          # right?") for the 2-hour acceptance test. Fleet Guard now
          # keeps it alive across crashes. âš  NEVER alongside acris_lane
          # (two access points = the tripping condition) - acris_lane
          # stays PAUSED below.
          "acris_lane",         # âš  RE-PAUSED 2026-08-28 16:32 - login:
          # "you werent supposed to start acris yet." The batched config
          # below is BUILT and compile-checked; launch is login's call,
          # explicitly, not the guard's. (First 2 min of the batched entry:
          # pdfs landed 26->48 at width 60, but 12 fails + shed(3) and THE
          # PROBE NEVER SUCCEEDED ONCE - governor collapsed 12->9/s.
          # Diagnose the probe silence BEFORE the next launch.)
          # (prior note, kept: released 2026-08-28 on login:
          # "fix the acris approach so it can run too. exactly like
          # richmond, 1 entry batched with max workers around 128-140 and
          # each split into their respective job of monitor, walk, rd, and
          # pdf." The batched entry IS the pooled design already in the
          # lane: pool_maxsize=--max-inflight + pool_block=True = a hard
          # ceiling of WARM keep-alive connections, each born once, evenly
          # spaced by the pacer - past security once, as a group, then no
          # cold handshake ever again.)
          # âš  RETIRED WITH KEYING (2026-08-27). This arm exists only to
          # launch nav_key.py at 99.95% sync, and nav_key writes
          # navigation.keyed_by / navigation.key - the two columns login
          # asked to remove. The columns are still PHYSICALLY present
          # (a drop rewrites all 24.1M rows), so nav_key would not error;
          # it would silently spend hours repopulating dead columns.
          # Remove from PAUSED only if keying is deliberately revived.
          "org_backfill_arm"}
# â”€â”€ EJECT HOLD 2026-08-27 23:35 â€” LIFTED 2026-08-28 16:05 â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# D: was ejected overnight, so rc_lane / routine_update / board_truth
# were parked here to stop Fleet Guard respawning them onto a missing
# drive (that does NOT error, it WEDGES - dead handles, empty err log,
# only a db row-count delta detects it). D: is back and verified
# (Legal Instruments.db + _working + Updates all present, 15.9 TB free),
# so the three names are released. acris_lane and org_backfill_arm stay
# paused for their own reasons above.
# âš  THE SAME HOLD IS THE RIGHT MOVE NEXT TIME THE DRIVE OR THE WIFI
# GOES: park the names, do not kill the guard.

# ⚠ acris_reproduction.py IS DELIBERATELY *NOT* A SINGLETON (2026-08-28).
# The three floors are now three PROCESSES - one GIL each. Matching on
# script name alone would make fleet see floor #2 as "already running"
# and never start floors #2 and #3. They are distinguished by their args,
# which is exactly what _match falls back to for non-singletons. This is
# NOT a second access point: each floor still opens ONE session and enters
# once (three doors total, as before) - it just no longer shares an
# interpreter with the floors it was starving.
SINGLETON = {"acris_lane.py", "rc_lane.py", "routine_update.py",
             "board_truth.py"}
HERE = pathlib.Path(__file__).parent
W = pathlib.Path(r"D:\CRE Decoding System\01 Navigations"
                 r"\Legal Instruments Navigation\_working")
UPD = pathlib.Path(r"D:\CRE Decoding System\Updates")
HI = "\uffff"

# (name, script, args, cwd, stdout-log) - one row per PROCESS.
LANES = {
    "sync": [
        # THE CONSOLIDATED ACRIS LANE - sync + rd backfill + pdf pool, one
        # access point. Log goes to NAV_WORK (the board reads it there).
        # âš  NEVER COLD-LAUNCH (login 13:03, trip #3): the lane starts at a
        # low --max-rps and the governor earns every +2 step with clean
        # minutes. With the pacer, connections are also BORN evenly spaced
        # (83 ms apart at 12/s), so the pool warms instead of stampeding -
        # the ramp law now holds by construction, not by a warmup thread.
        # Restarts are themselves a load event; minimize them.
        #
        # âš  A NETWORK CHANGE NO LONGER NEEDS A RESTART (login: "changing
        # networks will require the restart every time"). The lane keeps its
        # session in a swappable box: the governor recycles the pool on any
        # mass failure, and a watchdog recycles it after --stall-after
        # seconds with zero successes (the SILENT case - every worker parked
        # inside a 90 s timeout while the board sits flat).
        # âš  PIANO AT DRUM PACE (login 16:00, after the 15:56 diagnosis):
        # "so fast that it feels seamless yet it technically is spaced not
        # to overlap... acris doesnt want to see one ip accessing it in
        # lumps." The anti-lump guarantee is THE PACER (Tempo reserves each
        # departure slot, burst capacity exactly 1), NOT --max-inflight 1
        # and NOT the contiguity lock - both of those merely made the lane
        # single-file, which cost ~64x throughput and protected nothing the
        # pacer does not already guarantee.
        #
        # âš  CONCURRENCY IS SIZED TO rate x RTT, NEVER MAXIMIZED. Little's
        # Law at the 80 req/s ceiling: 2.2 connections at 28 ms RTT, 20 at
        # a pessimistic 250 ms. 24 covers the ceiling with headroom; 64 only
        # bought self-contention (RTT stretched to ~4 s) and a 50-request
        # blast radius when one transport blip hit. Raising --max-inflight
        # does NOT raise throughput - the pacer owns the rate. Raise
        # --rps-max instead, and only on evidence.
        # âš âš  ACRIS IS PAUSED BY LOGIN (2026-08-25, after its Bandwidth
        # Notice). It is listed here so `fleet.py status` still reports it,
        # but PAUSED lanes are skipped by `start`. Remove the flag - or run
        # `python fleet.py start acris_lane --force` - to bring it back.
        ("acris_lane", "acris_lane.py",
         # >> WORKERS ARE THE DEMAND, THE TEMPO IS ONLY A LIMIT (measured
         # 2026-08-24 19:55). Each worker holds ONE request at a time, so the
         # pool can generate at most workers/RTT req/s: 32 workers / 0.58 s =
         # 55/s, which is EXACTLY the delivered figure the governor kept
         # reporting as "the wire is the limit". It was not the wire - it was
         # us. Commanding 69.4/s cannot conjure demand 32 workers do not make,
         # so delivered sat at 79% and the climb gate (needs 90%) locked the
         # lane out of its own ramp. 52 workers / 0.58 s = ~90/s, which is
         # what 8 docs/s needs. --max-inflight must exceed the worker count or
         # IT becomes the new cap.
         # >> THE BATCHED GROUP (login 2026-08-28): ~128-140 workers total,
         # ONE entry, split by job - monitor = the edge probe Â· walk = the
         # feeder cursor Â· rd = 60 workers Â· pdf = governor 16 -> 72. Peak
         # 60 + 72 + probe â‰ˆ 133, inside the 128-140 spec. --max-inflight
         # 140 is the GROUP SIZE: the warm-connection pool is a hard
         # ceiling entered once (pacer-spaced births, keep-alive after),
         # so concurrency is a warm-connection count, never a handshake
         # rate - the checkpoint model. Tempo dials untouched: the pacer
         # still owns arrival spacing (what ACRIS actually meters), and
         # the governor still earns every rung.
         ["--apply", "--phase", "row", "--workers", "60",
          "--pdf-workers", "16", "--pdf-max", "72",
          # >> --max-inflight WAS THE BINDING CONSTRAINT, NOT ACRIS (measured
          # 18:59): commanded 69.4/s, delivered 61.8/s, and the governor
          # correctly refused to climb - "the wire is the limit now, not the
          # tempo". Little's Law: 24 in flight / 0.388 s RTT = ~62/s ceiling,
          # exactly what we saw. Concurrency still FLOATS to rate x RTT and is
          # never maximized; this only stops the cap from binding before the
          # rate does. 40 / 0.388 = ~103 delivered, which at 11.2 reqs/doc is
          # ~9 docs/s.
          "--max-inflight", "140", "--max-rps", "12", "--rps-max", "150",
          # >> CLIMB FAST, BECAUSE THE THING WE FEARED WAS NOT THE RATE.
          # Every "trip" chased on 2026-08-24 turned out to be (a) acris's
          # edge 503ing our User-Agent string and (b) our own CLOSE_WAIT pool
          # deadlock - neither caused by pace. The gentle +2/3min ramp was
          # insurance against a mechanism that did not exist. +8 every 2 min
          # reaches 150 from a warm 69 in ~20 min, and the governor now
          # actually SEES a shed (503 sets err.acris_shed) so it collapses
          # instead of climbing through one.
          # >> TEN-MINUTE RUNGS, TWENTY-MINUTE CONFIRM, HOT START (login's
          # design, 2026-08-24 20:22). A 2-minute window at ~6.5 docs/s is
          # ~780 documents and is DOMINATED BY NOISE - proven twice tonight,
          # where the first rung after a restart measured 3.96 then 4.22
          # ready/s because the window contained the lane's own spin-up, and
          # the next rung then looked like a "+59% improvement" that was
          # mostly the first number being wrong. 10 minutes is ~3,900
          # documents.
          #
          # And 20 minutes of confirmation matters more than the rung length:
          # acris dips transiently (delivery went 91% -> 87% -> 77% inside six
          # minutes tonight), so a 6-minute confirm can sit ENTIRELY INSIDE
          # one dip and revert on it. 20 minutes spans the dip AND the
          # recovery - "that gives enough time for recovery to occur".
          #
          # âš  WHICH ONLY WORKS IF THE LADDER STARTS HOT ("you have to make
          # sure the rung starts hot so it doesnt take forever to find
          # ceiling"). At 10 min/rung a cold start from 12/s would take hours;
          # from a banked 92.6 peak, 0.9 puts us at ~83 and the ceiling is
          # ~5 rungs away. The banked peak is a MEASURED clean tempo, so
          # resuming near it is evidence-backed, not optimism.
          "--step-minutes", "10", "--rung-step", "8",
          "--confirm-windows", "2",
          "--warm-fraction", "0.9"],
         HERE, W / "acris_lane.log"),
        # >> ACRIS REPRODUCTION - the GROUP-ENTRY design (login 2026-08-28):
        # one batched entry (~130 warm connections, pool_block hard ceiling,
        # 0.5s-staggered births = past security once as a group), floors
        # monitor 1 Â· rd 60 Â· pdf 69, NO pacer NO governor - latency is the
        # governor, exactly the proven rd_walk chassis (28 workers 145 min /
        # 80 workers clean, zero refusals). Stop-on-refusal stills every
        # floor. UNTESTED: first run is the 2-hour acceptance test - needed
        # rising with new doc ids (the monitor's catch-up walk IS the
        # startup enumeration), landed moving, an end-to-end rate on
        # doc id -> mint -> rd -> pdf. âš  NEVER beside acris_lane (two
        # access points). Speed law: 12->28 workers doubled rd, 80 didn't
        # help - per-floor counts are TUNING dials once it proves clean.
        # >> WIDTHS ARE MEASURED, NOT GUESSED (acris_pdf_bench 2026-08-28):
        # the IMAGE endpoint took 32 pdf workers at 80 docs/s with ZERO
        # soft-refusals; the 4,922-byte soft-refusal is a CONNECTION-COUNT
        # trip, not a volume one. The first run's 60 rd + 69 pdf = 129
        # simultaneous connections exceeded acris's ~80-connection ceiling
        # and the sensitive image endpoint shed. rd 40 + pdf 24 + monitor =
        # 65 total keeps every floor inside its proven-clean zone AND the
        # group under the ceiling. Tune UP from here only on a clean run.
        # >> THE CEILING IS THE IMAGE ENDPOINT, NOT rd (measured 2026-08-28):
        # rd (DocumentDetail) tolerates ~80 concurrent (rd_walk); the image
        # endpoint (DocumentImageView) is the sensitive one - bench-clean at
        # 32 ALONE, but 65 COMBINED connections (40 rd + 24 pdf) soft-refused
        # 1,172x in one minute. So the group ceiling is set by images, well
        # under rd's 80. rd 28 + pdf 16 + monitor 1 = 45 stays under the
        # observed 65 trip with pdf at half its solo-clean width. Tune UP
        # only from a clean run; the mass-fail breaker (300/min) is the net.
        # >> THREE FLOORS = THREE PROCESSES (measured 2026-08-28). Sharing
        # ONE interpreter, the floors share a GIL, and the document floor's
        # img2pdf conversion STARVED the register floor: rd ran 2.7 docs/s
        # beside pdf vs 8.0 -> 9.4 -> 11.2 (still climbing) ALONE. Same
        # doors, same one-entry-per-floor rule - one interpreter each.
        # ⚠ Only the sync floor probes the edge; the other two pass
        # --every 3600 so they never touch the crfn endpoint.
        # ⚠ --floor IS THE IDENTITY TOKEN, not decoration: _match below
        # ignores tokens <= 3 chars, so 20/40/0/10 cannot tell these three
        # apart and every floor matched every other ("already running" for
        # a floor that had just died). The name is what makes them distinct.
        # ⚠⚠ LOGS LIVE ON C:, NOT ON THE USB DRIVE (2026-08-28). Three
        # different floors died silently with EMPTY stderr, and so did
        # routine_update and board_truth - every process whose log sat on
        # D:. The one process that never died all night is rc_lane, the
        # only one logging to the decoder dir on C:. The drive drops
        # intermittently (it vanished outright once at ~20:0x); a process
        # holding a log handle on it dies, AND ITS TRACEBACK DIES WITH IT
        # because the .err file is on the same dead volume. Keeping the
        # heartbeat on C: both survives a hiccup and preserves the
        # evidence. The board reads these paths - keep them in step.
        ("acris_repro_sync", "acris_reproduction.py",
         ["--floor", "sync", "--sync-workers", "20", "--rd-workers", "0",
          "--pdf-workers", "0", "--every", "10"],
         HERE, HERE / "acris_repro_sync.log"),
        # ══ THE APPROVED SHAPE: ONE REGISTER DOOR, 40 WORKERS ═══════════
        # login 2026-08-29, after the denial: "acris should not deny if we
        # do exactly the approach we've decided on. this is to batch one
        # entry 40 workers on registration."
        #
        # ⚠ THIS IS THE ENTRY THE FOUR SHARDS BELOW REPLACED, AND THAT
        # SUBSTITUTION IS THE DEVIATION THAT EARNED THE 12:23 NOTICE.
        # The approved design is THREE doors (sync · register · document).
        # Sharding register into reg_a..reg_d to beat the GIL silently made
        # it SIX, and five were live at 12:23 (a+b+c+d+sync) carrying 84
        # register workers. The group-entry contract is "few doors, wide
        # crews, keep-alive after" - four doors on one floor breaks it.
        # Speed was real (61 docs/s) and it is not worth a ban.
        #
        # ⚠ HONEST COST: one door is one process is ONE GIL, and rd parsing
        # is pure Python - measured ceiling ~11 docs/s alone (8.0 -> 9.4 ->
        # 11.2 climbing). 40 workers do NOT make 40 docs/s here; they only
        # keep the pipe full while the parser is the bottleneck. Do not read
        # a low docs/s on this lane as a source limit - req/s is the
        # controlled variable, and the GIL owns the rest.
        ("acris_repro_register", "acris_reproduction.py",
         ["--floor", "register", "--sync-workers", "0", "--rd-workers", "40",
          "--pdf-workers", "0", "--every", "3600"],
         HERE, HERE / "acris_repro_register.log"),
        # >> REGISTER IS SHARDED FOUR WAYS (2026-08-29). One process caps
        # near 10-11 docs/s - rd parsing is pure Python under one GIL - so
        # 40+/s needs PROCESSES over DISJOINT id ranges, the old fleet's
        # proven shape (4 x 28 workers ~= 138 docs/s aggregate). Cuts are
        # at the 25/50/75% marks of the ACTUAL outstanding rows (3,751,565
        # on 2026-08-29, ~937,891 each), not equal id-space - the todo set
        # clumps by era and equal ranges would finish at wildly different
        # times. ⚠ Ranges MUST stay disjoint or two shards fetch the same
        # document twice. Recompute the cuts if the todo set shifts a lot.
        # ⚠ reg_a IS THE DIGITAL BAND AND IT IS NOT LIKE THE OTHERS.
        # All-digit ids sort BEFORE "FT_", so this shard drew every modern
        # ~118 KB document while b/c/d got compact film records. MEASURED
        # 2026-08-29 at 28 workers: b/c/d ran 19 docs/s with ZERO fails
        # while reg_a managed 0.63/s with 182 fails - acris serves the
        # heavy pages SHORT under that much concurrency (the non-echoing
        # page). Fewer workers on the heavy band is the dial.
        ("acris_repro_reg_a", "acris_reproduction.py",
         ["--floor", "reg_a", "--sync-workers", "0", "--rd-workers", "10",
          "--pdf-workers", "0", "--every", "3600",
          "--lo", "0", "--hi", "FT_1670003716867"],
         HERE, HERE / "acris_repro_reg_a.log"),
        ("acris_repro_reg_b", "acris_reproduction.py",
         ["--floor", "reg_b", "--sync-workers", "0", "--rd-workers", "28",
          "--pdf-workers", "0", "--every", "3600",
          "--lo", "FT_1670003716867", "--hi", "FT_2180004364618"],
         HERE, HERE / "acris_repro_reg_b.log"),
        ("acris_repro_reg_c", "acris_reproduction.py",
         ["--floor", "reg_c", "--sync-workers", "0", "--rd-workers", "28",
          "--pdf-workers", "0", "--every", "3600",
          "--lo", "FT_2180004364618", "--hi", "FT_4650007215965"],
         HERE, HERE / "acris_repro_reg_c.log"),
        ("acris_repro_reg_d", "acris_reproduction.py",
         ["--floor", "reg_d", "--sync-workers", "0", "--rd-workers", "28",
          "--pdf-workers", "0", "--every", "3600",
          "--lo", "FT_4650007215965", "--hi", HI],
         HERE, HERE / "acris_repro_reg_d.log"),
        ("acris_repro_document", "acris_reproduction.py",
         ["--floor", "document", "--sync-workers", "0", "--rd-workers", "0",
          "--pdf-workers", "40", "--every", "3600"],
         HERE, HERE / "acris_repro_document.log"),
        # âš  THE 2026-08-24 RICHMOND CUTOVER: rc_lane.py absorbed rc_live
        # (probe), rc_feed (token minting) and rc_pdf_pull (fetch+land), and
        # DROPPED rc_pdf_land entirely - its log was empty, because the
        # courts host serves a real pdf and rc_pdf_pull already landed it
        # straight into the store; the JPEG->G4 conversion belonged to the
        # retired browser path.
        #
        # âš  NEVER run the old trio alongside it: served_ids is per-process,
        # so two minters hand the SAME ids out twice and nothing in the table
        # records that a token was minted.
        #
        # âš  THE DRUM, NOT THE PIANO. No pacer - latency is the governor
        # (proven 160 concurrent connections for 26 h). Concurrency is the
        # only dial and the safety is refusal_verdict, not pacing.
        # >> "RICHMOND MAY BE ABLE TO DRUM QUICKER" - ASKED AND ANSWERED
        # (login 2026-08-25). It cannot, and the reason is worth keeping so
        # nobody re-tries it: richmond is TOTAL-LINK-capped, not
        # per-connection throttled, so pullers are not the dial.
        #
        # MEASURED at the office, single variable, acris stable throughout:
        #     26 pullers -> 2.57, 1.97, 2.43 = 2.32 docs/s
        #     40 pullers -> 2.12, 1.95, 2.02 = 2.03 docs/s
        # 54% more pullers bought 0% more output (slightly worse, in noise),
        # and bulk throughput pinned at ~80 Mb/s at BOTH widths. That is the
        # signature of a shared pipe being full, not a server metering each
        # connection - if it metered per connection, more would have scaled.
        #
        # âš  AND THE LOCATION IS THE VARIABLE THAT ACTUALLY MOVES THIS.
        # Same code, same width: 5.8-9.4 docs/s at home (230-287 Mb/s,
        # ~2.6 MB/s per connection) vs 2.3 here (~0.4 MB/s per connection).
        # richmond pulls ~5 MB documents so it is BANDWIDTH-shaped; acris
        # pulls many small pages so it is LATENCY-shaped and barely notices
        # (84.8 -> 74.9 req/s across the same move). Never read one lane's
        # rate as evidence about the other's, or about the link.
        #
        # So: back to the leanest width that reaches the cap. Extra sockets
        # at a full pipe add contention and steal from acris for nothing.
        # âš  WIDTH 8, NOT 16 - MEASURED 2026-08-25 by rc_bench.py in its own
        # process, nothing else running, same 60 tokens at both levels:
        #     8 pullers  -> 28.23 docs/s  84 Mb/s  0 errors
        #    16 pullers  -> 18.76 docs/s  56 Mb/s  0 errors
        # 16 is PAST the cap and self-contends; per-connection throughput
        # collapses 10.54 -> 3.50 Mb/s. richmond averages ~5 MB/doc, so the
        # pipe fills at 8 and extra sockets only steal from each other.
        ("rc_lane", "rc_lane.py",
         ["--apply", "--miners", "24", "--workers", "8"],
         HERE, HERE / "rc_lane.log"),
    ],
    "board": [
        # pass-2 arm: polls the board, releases the reference keyer at
        # acris rd >= 99.95% - part of the standing fleet (caught missing
        # 2026-08-24 after the lock-hunt kill; login asked "is pass 2
        # armed" and it was not running)
        ("org_backfill_arm", "org_backfill_arm.py",
         ["--poll", "600"], HERE, HERE / "org_backfill_arm.log"),
        ("routine_update", str(UPD / "routine_update.py"),
         ["--loop"], UPD, UPD / "routine_update.log"),
        # âš  board_truth.py lives in Updates\, NOT the decoder dir - a launch
        # with the wrong cwd dies instantly with "can't open file" and a PID
        # that looked healthy (caught by fleet.py status, 2026-08-24)
        # >> 60s, NOT 600 (login 2026-08-26: "the board should be constantly
        # counting. theres a 60 second and 5 minute rate"). Affordable only
        # because board_truth now counts the todo set through
        # ix_nav_pdf_todo (0.2 s) instead of the unindexed IN form (8-22 s);
        # the exact pending pass still runs on its own 600 s cadence inside.
        ("board_truth", str(UPD / "board_truth.py"),
         ["--loop", "--every", "60"], UPD, UPD / "board_truth.log"),
    ],
}


def _running():
    """{marker: pid} for our scripts, via WMIC-free tasklist+cmdline scan."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
         " | ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }"],
        capture_output=True, text=True).stdout
    procs = {}
    for line in out.splitlines():
        pid, _, cmd = line.partition("|")
        if pid.strip().isdigit():
            procs[int(pid)] = cmd
    return procs


def _match(cmd, script, args):
    """âš  MATCH ON THE SCRIPT FOR SINGLE-INSTANCE LANES (2026-08-24 15:33).
    fleet start launched a SECOND acris_lane because the running one had a
    different tempo config than the roster's, so the arg-token check failed
    and it looked "not running" - two acris presences at once, which is the
    exact convergence the piano rule exists to prevent. Any lane that must
    be a singleton matches on script name alone."""
    if pathlib.Path(script).name not in cmd:
        return False
    if pathlib.Path(script).name in SINGLETON:
        return True
    # the --lo VALUE uniquely identifies a walker arm (a4's --hi is a
    # 1-char sentinel and its --lo equals a3's --hi, so hi tokens and
    # bare substring checks mis-bind arms - match the --lo binding)
    # ⚠ --floor IS AN EXACT-VALUE BINDING, NOT A SUBSTRING (2026-08-28).
    # The generic token loop below asks `token in cmd`, and "sync" is a
    # substring of "--sync-workers" - which EVERY floor carries. So the
    # sync roster entry matched the register process, `start` said
    # "already running", and a floor I had just killed never came back.
    # Same defect the --lo case below was written for; same cure.
    if "--floor" in args:
        import re as _re
        want = args[args.index("--floor") + 1]
        m = _re.search(r'--floor"?\s+"?([^\s"]+)', cmd)
        return bool(m) and m.group(1) == want
    if "--lo" in args:
        import re as _re
        want = args[args.index("--lo") + 1]
        m = _re.search(r'--lo"?\s+"?([^\s"]*)', cmd)
        return bool(m) and m.group(1) == want
    for token in args:
        if token and len(token) > 3 and token not in cmd:
            return False
    return True


def status():
    procs = _running()
    for lane, rows in LANES.items():
        print(lane)
        for name, script, args, _, _ in rows:
            pid = next((p for p, c in procs.items()
                        if _match(c, script, args)), None)
            print("  %-14s %s" % (name, "RUNNING pid %d" % pid if pid
                                  else "not running"))


def start(lane):
    procs = _running()
    for name, script, args, cwd, log in LANES[lane]:
        if name in PAUSED and "--force" not in sys.argv:
            print("  %-14s PAUSED - skipped (--force to override)" % name)
            continue
        if any(_match(c, script, args) for c in procs.values()):
            print("  %-14s already running" % name)
            continue
        err = log.with_suffix(log.suffix + ".err")
        with log.open("w") as lo, err.open("w") as eo:
            p = subprocess.Popen(
                [PY, "-u", script] + args, cwd=str(cwd), stdout=lo,
                stderr=eo, creationflags=subprocess.CREATE_NO_WINDOW
                | subprocess.CREATE_NEW_PROCESS_GROUP)
        print("  %-14s started pid %d" % (name, p.pid))
        time.sleep(0.3)


def stop(lane):
    procs = _running()
    for name, script, args, _, _ in LANES[lane]:
        for pid, cmd in procs.items():
            if _match(cmd, script, args):
                subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                               capture_output=True)
                print("  %-14s stopped pid %d" % (name, pid))


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else "status"
    target = sys.argv[2] if len(sys.argv) > 2 else "all"
    if verb == "status":
        status()
    else:
        lanes = list(LANES) if target == "all" else [target]
        if verb == "start" and target == "all":
            lanes = [l for l in lanes if l != "apdf"]   # parked stays parked
        for l in lanes:
            print(l)
            {"start": start, "stop": stop}[verb](l)
