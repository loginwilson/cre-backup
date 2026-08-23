"""PHASE CHAIN — the five phases in order, each gated by its own assertion.

    python phase_chain.py                 # run it
    python phase_chain.py --dry           # every phase in report-only mode
    python phase_chain.py --from nav      # start partway down
    python phase_chain.py --stop-on-fail  # halt at the first NOT LEVEL

    monitorization -> synchronization -> navigation -> acquisition -> organization
                                                          (live source database)

⚠ SEARCHED FIRST (CLAUDE.md rule 1). `chain.py` is the FINANCING chain — SAT and
ASST resolved back to the mortgage they act on. `pipeline.py` is the workflow on
ONE DOCUMENT. `routine_4am.py` is the daily ACRIS routine. None of them runs the
phases in order, which is why this exists.

THE POINT IS THE GATES, NOT THE SEQUENCE. Running five scripts back to back is a
batch file. What makes this a chain is that **each phase makes ONE claim**, and a
phase that cannot prove its claim does not get to hand work to the next one:

    monitorization   the source's edge is known, as of seconds ago
    synchronization  every document the source has, we have an id for
    navigation       every id is tabled with key, index and endpoint
    acquisition      every document that has an image has a pdf attached
    organization     every document is keyed to what it is about

⚠ A PHASE THAT DECLINES IS NOT A PHASE THAT FAILED, and the chain must not
conflate them. `routine_acquisition.py` refuses to scan while the walkers are
writing (it needs `--anyway` to override). With the fleet running that is the
CORRECT answer, not an error — so the chain reports DECLINED separately from
NOT LEVEL. Folding them together would teach us to ignore real failures.

⚠ NEVER PIPE A LONG RUN THROUGH A FILTER (CLAUDE.md rule 5, walked into again
tonight: a `| tail -20` block-buffered a background job and made a live process
look hung for five minutes). Every phase writes its own log file and the chain
reads the file afterwards.

⚠ THE CHAIN DOES NOT REPAIR. It reports which phase is not level and stops
asking that phase's downstream to pretend otherwise. *Never repair a number to
make a check pass.*
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
LOGS = HERE / "_chain_logs"
PY = sys.executable

# name, script, args, args added by --dry, how long we let it run
PHASES = [
    ("monitor", "phase_monitor.py", ["--once"], [], 900),
    ("sync",    "routine_synchronization.py", ["--source", "both"], ["--dry"], 5400),
    ("nav",     "routine_navigation.py", [], ["--dry"], 5400),
    ("acq",     "routine_acquisition.py", [], ["--dry"], 5400),
    ("org",     "routine_organization.py", [], ["--dry"], 5400),
]

ap = argparse.ArgumentParser()
ap.add_argument("--dry", action="store_true")
ap.add_argument("--from", dest="start", default=None,
                help="first phase to run (monitor|sync|nav|acq|org)")
ap.add_argument("--only", default=None)
ap.add_argument("--stop-on-fail", action="store_true")
a = ap.parse_args()

LOGS.mkdir(exist_ok=True)
names = [p[0] for p in PHASES]
if a.start:
    PHASES = PHASES[names.index(a.start):]
if a.only:
    PHASES = [p for p in PHASES if p[0] == a.only]


def verdict(name, text, rc):
    """⚠ READ THE PHASE'S OWN WORDS, don't infer from a return code. These
    routines print `LEVEL` / `NOT LEVEL - report, do not repair` and several
    exit 0 either way, because being not-level is a RESULT, not a crash.

    ⚠ AND EACH PHASE STATES ITS CLAIM IN ITS OWN VOCABULARY. The first version
    of this file used one LEVEL/NOT-LEVEL heuristic for all five and scored a
    perfectly healthy monitor run as NO VERDICT - the monitor's language is
    `quiet` / `NEW` / `reporting NOTHING`, and it never says LEVEL. A grader
    that does not speak the phase's language reports the GRADER's gap as the
    PHASE's failure, which is the same disease as reading an error as a zero."""
    t = text.upper()

    if name == "monitor":
        # ⚠ The claim is "THE EDGE IS KNOWN", not "something arrived". `quiet`
        # is a PASS - a quiet minute is the answer working. The failure is the
        # monitor declining to answer, which it says explicitly and by design.
        if "REPORTING NOTHING" in t or "UNPROVEN" in t or "NO KNOWN EDGE" in t:
            return "NOT LEVEL"
        if "BROKEN READ" in t:
            return "NOT LEVEL"
        edges = t.count("EDGE ")
        return "LEVEL" if edges >= 2 else "NO VERDICT"

    if "NOT LEVEL" in t:
        return "NOT LEVEL"
    if "LEVEL" in t:
        return "LEVEL"
    # the busy-guards: these decline rather than fight the lanes
    if "LANES" in t and ("WRIT" in t or "BUSY" in t or "REFUS" in t):
        # ⚠ A DECLINE THAT STILL MEASURED SOMETHING SHOULD SAY SO. nav runs a
        # bounded tail probe when it cannot afford the full scan - "tail clean"
        # is strictly more than "declined", and strictly less than LEVEL.
        if "UNMINTED ROWS AT THE TAIL" in t:
            return "NOT LEVEL"
        if "TAIL CLEAN" in t:
            return "DECLINED (tail ok)"
        return "DECLINED"
    if rc != 0:
        return "ERROR rc=%d" % rc
    return "NO VERDICT"


print("=" * 78)
print("PHASE CHAIN%s  ·  %s" % ("  (dry)" if a.dry else "",
                                time.strftime("%Y-%m-%d %H:%M:%S")))
print("=" * 78)

results = []
for name, script, args, dry_args, cap in PHASES:
    log = LOGS / ("%s.log" % name)
    cmd = [PY, "-u", str(HERE / script)] + args + (dry_args if a.dry else [])
    print("\n--- %s · %s ---" % (name.upper(), script), flush=True)
    t0 = time.time()
    try:
        with log.open("w", encoding="utf-8") as fh:
            rc = subprocess.call(cmd, cwd=str(HERE), stdout=fh,
                                 stderr=subprocess.STDOUT, timeout=cap)
    except subprocess.TimeoutExpired:
        rc, cap_hit = -1, True
    else:
        cap_hit = False
    el = time.time() - t0
    text = log.read_text(encoding="utf-8", errors="replace")
    v = "TIMEOUT >%ds" % cap if cap_hit else verdict(name, text, rc)
    results.append((name, v, el, log))
    for ln in text.strip().splitlines()[-6:]:
        print("   " + ln)
    print("   => %s   (%.0fs)   log %s" % (v, el, log.name), flush=True)
    if a.stop_on_fail and v.startswith(("NOT LEVEL", "ERROR", "TIMEOUT")):
        print("\n   stopping: %s is not level and --stop-on-fail is set" % name)
        break

print("\n" + "=" * 78)
print("%-9s %-16s %8s   %s" % ("PHASE", "VERDICT", "SECONDS", "LOG"))
for name, v, el, log in results:
    print("%-9s %-16s %8.0f   %s" % (name, v, el, log.name))
bad = [n for n, v, _, _ in results
       if v.startswith(("NOT LEVEL", "ERROR", "TIMEOUT", "NO VERDICT"))]
dec = [n for n, v, _, _ in results if v == "DECLINED"]
print("=" * 78)
if dec:
    print("DECLINED (not a failure): %s" % ", ".join(dec))
print("CHAIN LEVEL" if not bad else "CHAIN NOT LEVEL - %s" % ", ".join(bad))
