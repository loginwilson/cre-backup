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

Lanes: sync (acris_lane + rc_lane - BOTH consolidated now) · board
(routine_update + board_truth + pass-2 arm). The "rcpdf" lane is RETIRED:
rc_lane absorbed the trio on 2026-08-24.

⚠ THE 2026-08-24 CUTOVER: acris_lane.py absorbed acris_live, the rd_walk
fleet (4x28) AND the image_walk fleet (3x14). ONE process is the whole
acris presence - edge probe every 10s, rd backfill workers, pdf pool with
the sync hot-list, keying via the key_on_rd trigger (needs no process).
The old "rd" and "apdf" lanes are RETIRED: starting them alongside the
lane would put a second access point on ACRIS, which is the tripping
condition the lane exists to remove. Their definitions live in git
history if a rollback ever needs them.

⚠ THE SAME CUTOVER FOR RICHMOND (2026-08-24, evening): rc_lane.py absorbed
rc_live (probe), rc_feed (token minting) and rc_pdf_pull (fetch + land),
and DROPPED rc_pdf_land - the courts host serves a real pdf and the puller
already landed it, so the lander only ever drained a legacy _incoming
backlog. 4 processes -> 1. Retired scripts moved OUT of the import path to
_archive/richmond_preconsolidation/ so they cannot be started by habit.

⚠ WHY RICHMOND ALSO GAINED AN rd HEAL, AND WHY THAT MATTERS TO THE ROSTER.
rc_live landed only id + rd_url + pdf_url. rd was a SEPARATE walker that
had finished its backfill and was no longer watching the edge, so a new
filing got an id and a url and then stopped - no rd, therefore no key (the
key_on_rd trigger fires on rd), therefore no pdf. The lane looked healthy
because it was counting ids. **A roster is only honest if each lane owns
its whole pipeline**; a lane that owns four of five stages will report the
four and stay silent about the fifth.

⚠ THE TWO LANES HAVE OPPOSITE PACING, AND THE ROSTER MUST NOT BLUR THEM.
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
# ⚠ THE COMMENT AT acris_lane CLAIMED "PAUSED lanes are skipped by
# `start`" AND NO SUCH SKIP EXISTED - `fleet.py start sync` would have
# restarted acris right after its Bandwidth Notice. A comment is not
# enforcement. Found 2026-08-25 while restarting richmond after a crash.
PAUSED = {"acris_lane"}          # login paused it; --force overrides
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
        # ⚠ NEVER COLD-LAUNCH (login 13:03, trip #3): the lane starts at a
        # low --max-rps and the governor earns every +2 step with clean
        # minutes. With the pacer, connections are also BORN evenly spaced
        # (83 ms apart at 12/s), so the pool warms instead of stampeding -
        # the ramp law now holds by construction, not by a warmup thread.
        # Restarts are themselves a load event; minimize them.
        #
        # ⚠ A NETWORK CHANGE NO LONGER NEEDS A RESTART (login: "changing
        # networks will require the restart every time"). The lane keeps its
        # session in a swappable box: the governor recycles the pool on any
        # mass failure, and a watchdog recycles it after --stall-after
        # seconds with zero successes (the SILENT case - every worker parked
        # inside a 90 s timeout while the board sits flat).
        # ⚠ PIANO AT DRUM PACE (login 16:00, after the 15:56 diagnosis):
        # "so fast that it feels seamless yet it technically is spaced not
        # to overlap... acris doesnt want to see one ip accessing it in
        # lumps." The anti-lump guarantee is THE PACER (Tempo reserves each
        # departure slot, burst capacity exactly 1), NOT --max-inflight 1
        # and NOT the contiguity lock - both of those merely made the lane
        # single-file, which cost ~64x throughput and protected nothing the
        # pacer does not already guarantee.
        #
        # ⚠ CONCURRENCY IS SIZED TO rate x RTT, NEVER MAXIMIZED. Little's
        # Law at the 80 req/s ceiling: 2.2 connections at 28 ms RTT, 20 at
        # a pessimistic 250 ms. 24 covers the ceiling with headroom; 64 only
        # bought self-contention (RTT stretched to ~4 s) and a 50-request
        # blast radius when one transport blip hit. Raising --max-inflight
        # does NOT raise throughput - the pacer owns the rate. Raise
        # --rps-max instead, and only on evidence.
        # ⚠⚠ ACRIS IS PAUSED BY LOGIN (2026-08-25, after its Bandwidth
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
         ["--apply", "--phase", "row", "--workers", "56",
          # >> --max-inflight WAS THE BINDING CONSTRAINT, NOT ACRIS (measured
          # 18:59): commanded 69.4/s, delivered 61.8/s, and the governor
          # correctly refused to climb - "the wire is the limit now, not the
          # tempo". Little's Law: 24 in flight / 0.388 s RTT = ~62/s ceiling,
          # exactly what we saw. Concurrency still FLOATS to rate x RTT and is
          # never maximized; this only stops the cap from binding before the
          # rate does. 40 / 0.388 = ~103 delivered, which at 11.2 reqs/doc is
          # ~9 docs/s.
          "--max-inflight", "64", "--max-rps", "12", "--rps-max", "150",
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
          # ⚠ WHICH ONLY WORKS IF THE LADDER STARTS HOT ("you have to make
          # sure the rung starts hot so it doesnt take forever to find
          # ceiling"). At 10 min/rung a cold start from 12/s would take hours;
          # from a banked 92.6 peak, 0.9 puts us at ~83 and the ceiling is
          # ~5 rungs away. The banked peak is a MEASURED clean tempo, so
          # resuming near it is evidence-backed, not optimism.
          "--step-minutes", "10", "--rung-step", "8",
          "--confirm-windows", "2",
          "--warm-fraction", "0.9"],
         HERE, W / "acris_lane.log"),
        # ⚠ THE 2026-08-24 RICHMOND CUTOVER: rc_lane.py absorbed rc_live
        # (probe), rc_feed (token minting) and rc_pdf_pull (fetch+land), and
        # DROPPED rc_pdf_land entirely - its log was empty, because the
        # courts host serves a real pdf and rc_pdf_pull already landed it
        # straight into the store; the JPEG->G4 conversion belonged to the
        # retired browser path.
        #
        # ⚠ NEVER run the old trio alongside it: served_ids is per-process,
        # so two minters hand the SAME ids out twice and nothing in the table
        # records that a token was minted.
        #
        # ⚠ THE DRUM, NOT THE PIANO. No pacer - latency is the governor
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
        # ⚠ AND THE LOCATION IS THE VARIABLE THAT ACTUALLY MOVES THIS.
        # Same code, same width: 5.8-9.4 docs/s at home (230-287 Mb/s,
        # ~2.6 MB/s per connection) vs 2.3 here (~0.4 MB/s per connection).
        # richmond pulls ~5 MB documents so it is BANDWIDTH-shaped; acris
        # pulls many small pages so it is LATENCY-shaped and barely notices
        # (84.8 -> 74.9 req/s across the same move). Never read one lane's
        # rate as evidence about the other's, or about the link.
        #
        # So: back to the leanest width that reaches the cap. Extra sockets
        # at a full pipe add contention and steal from acris for nothing.
        # ⚠ WIDTH 8, NOT 16 - MEASURED 2026-08-25 by rc_bench.py in its own
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
        # ⚠ board_truth.py lives in Updates\, NOT the decoder dir - a launch
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
    """⚠ MATCH ON THE SCRIPT FOR SINGLE-INSTANCE LANES (2026-08-24 15:33).
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
