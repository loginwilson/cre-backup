"""ONE TOUCH: get richmond pdfs acquiring, and KEEP them acquiring all night.

    python rc_night.py            warm, start, then supervise until stopped
    python rc_night.py --status   what it is doing right now
    python rc_night.py --stop     stop the supervisor and the lane

login 2026-08-25: "just get the richmond pdf acquiring to my one touch for
the night please."

⚠⚠ THE FAILURE THIS EXISTS FOR IS A SILENT STALL, NOT A CRASH. Measured four
times on 2026-08-25:

    19:21  cold start              -> minted 0 · err 0   for 3+ min
    19:38  started after rc_bench  -> 6.62/s
    20:30  cold start              -> minted 0 · err 0   for 2+ min
    20:34  started after rc_bench  -> 5.77/s

The lane is ALIVE the whole time it produces nothing, so keepalive.py — which
restarts a lane that has DIED — never fires. This supervisor watches the
`pdfs` counter instead of the process table.

⚠ THE WARM-UP IS EMPIRICAL AND ITS MECHANISM IS UNPROVEN. rc_bench.py writes
nothing locally (no store, no db) and rc_sync.Window keeps no cookie jar on
disk, so it leaves no local state the lane could inherit. That points at
SERVER-SIDE session state — the clerk site appears to want recent legitimate
search activity from this IP before ViewContent starts handing out 302s. Four
runs is a recipe, not a mechanism. Do not write it up as a cause.

⚠ WHY next_ids' FAILURE IS INVISIBLE, which is what made this cost an hour:
rc_lane's miner does `try: grab = next_ids(20) except Exception: grab = []`,
and the PROGRESS line prints minted/err/stale/synced/rd/hot but NOT `skipped`.
So every counter that could explain the stall is either swallowed or unprinted.

⚠⚠ SECURITY — A REFUSAL ENDS THE NIGHT. If the lane log ever shows REFUSED,
a Bandwidth Notice, or workers stopped, this supervisor STOPS and does not
restart. It never retries through a refusal and never rotates anything.
Richmond is also capped at MAX_RESTARTS so a persistent fault cannot turn into
an all-night retry loop against the county.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LANE_LOG = HERE / "rc_lane.log"
NIGHT_LOG = HERE / "rc_night.log"
PY = sys.executable

# from relocate.py — the same markers, deliberately not a second vocabulary
REFUSAL = ("REFUSED", "Bandwidth Notice", "ALL WORKERS STOPPED",
           "BACKFILL WORKERS STOPPED")
PROGRESS = re.compile(r"PROGRESS\s+([\d,]+)\s+pdfs")

CHECK_EVERY = 300          # 5 min between productivity checks
GRACE = 180                # a fresh start gets this long before it is judged
MAX_RESTARTS = 12          # then stop and say so — never an all-night loop
# ⚠ RAISED 6 -> 12 FOR AN UNATTENDED NIGHT (2026-08-25). One restart costs a
# 25-document warm-up, so twelve is still trivial load. This cap only guards
# benign restart churn - A REFUSAL STILL STOPS EVERYTHING IMMEDIATELY and is
# checked before the counter, so raising this cannot make us retry a refusal.


def say(msg):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with NIGHT_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def lane_tail(n=400):
    try:
        return LANE_LOG.read_text(encoding="utf-8",
                                  errors="replace").splitlines()[-n:]
    except OSError:
        return []


def refusal_on_record():
    for ln in reversed(lane_tail()):
        if any(m in ln for m in REFUSAL):
            return ln.strip()[:160]
    return ""


def pdfs_now():
    """The last PROGRESS count, or None if the lane has not printed one yet."""
    for ln in reversed(lane_tail(80)):
        m = PROGRESS.search(ln)
        if m:
            return int(m.group(1).replace(",", ""))
    return None


def lane_running():
    r = subprocess.run([PY, str(HERE / "fleet.py"), "status"],
                       cwd=str(HERE), capture_output=True, text=True,
                       timeout=180)
    for ln in (r.stdout or "").splitlines():
        if "rc_lane" in ln and "RUNNING" in ln:
            return True
    return False


def warm():
    """⚠ REUSES rc_bench.py RATHER THAN REIMPLEMENTING THE MINT PATH.
    It is the proven isolator, it is documented safe (same host, same headers,
    fewer requests than a minute of normal running, stops on 401/403/429), and
    a second copy of this logic would drift from it. Cost is 25 documents
    downloaded and discarded."""
    say("warming the session (rc_bench, 25 docs, discarded)")
    r = subprocess.run([PY, str(HERE / "rc_bench.py"), "--n", "25",
                        "--levels", "8"], cwd=str(HERE),
                       capture_output=True, text=True, timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    if "REFUSED" in out:
        say(">> REFUSED DURING WARM-UP - stopping, by rule. Nothing retried.")
        return False
    for ln in out.splitlines():
        if ln.startswith("minted") or ln.startswith("BEST"):
            say("   " + ln.strip())
    return "minted 0 tokens" not in out


def start_lane():
    subprocess.run([PY, str(HERE / "fleet.py"), "start", "sync"],
                   cwd=str(HERE), capture_output=True, text=True, timeout=240)
    say("rc_lane started (acris stays paused by the fleet.py guard)")


def stop_lane():
    subprocess.run([PY, str(HERE / "fleet.py"), "stop", "sync"],
                   cwd=str(HERE), capture_output=True, text=True, timeout=240)


ap = argparse.ArgumentParser()
ap.add_argument("--status", action="store_true")
ap.add_argument("--stop", action="store_true")
a = ap.parse_args()

if a.status:
    print("rc_lane running:", lane_running())
    print("pdfs on the last PROGRESS line:", pdfs_now())
    r = refusal_on_record()
    print("refusal on record:", r or "none")
    print()
    print("last supervisor lines:")
    try:
        for ln in NIGHT_LOG.read_text(encoding="utf-8").splitlines()[-12:]:
            print("   " + ln)
    except OSError:
        print("   (no rc_night.log yet)")
    raise SystemExit

if a.stop:
    stop_lane()
    say("supervisor asked to stop; rc_lane stopped. Kill this process to end "
        "the supervision loop.")
    raise SystemExit

# ── the night ────────────────────────────────────────────────────────────
say("=" * 68)
say("RICHMOND NIGHT RUN starting")

import corpus_paths as CP                                      # noqa: E402
if not CP.NAV_DB.exists():
    say(">> THE CORPUS IS NOT REACHABLE AT %s - re-attach the drive first."
        % CP.NAV_DB)
    raise SystemExit(1)
say("corpus reachable at %s" % CP.NAV_DB)

restarts = 0
if lane_running():
    say("rc_lane is already running - leaving it alone and watching it")
else:
    if not warm():
        raise SystemExit(1)
    start_lane()

time.sleep(GRACE)
last = pdfs_now()
say("baseline after %ds grace: %s pdfs" % (GRACE, last))

while True:
    time.sleep(CHECK_EVERY)

    r = refusal_on_record()
    if r:
        say(">> REFUSAL ON RECORD - STOPPING THE NIGHT. Not retried, nothing "
            "rotated. Read it before restarting anything:")
        say("   %s" % r)
        stop_lane()
        break

    now = pdfs_now()
    if now is None:
        say("no PROGRESS line yet - waiting")
        continue

    if last is not None and now > last:
        rate = (now - last) / CHECK_EVERY
        say("OK  %s pdfs  (+%s in %dm = %.2f/s)"
            % ("{:,}".format(now), "{:,}".format(now - last),
               CHECK_EVERY // 60, rate))
        last = now
        continue

    # ⚠ ALIVE BUT PRODUCING NOTHING - the whole reason this file exists.
    say("⚠ STALLED: %s pdfs, unchanged over %d min. The lane is alive and "
        "idle, which keepalive.py cannot see." % ("{:,}".format(now),
                                                  CHECK_EVERY // 60))
    restarts += 1
    if restarts > MAX_RESTARTS:
        say(">> %d restarts already - stopping rather than retrying all night "
            "against the county. Something is wrong that a restart does not "
            "fix." % MAX_RESTARTS)
        stop_lane()
        break
    say("restart %d of %d: stop -> warm -> start" % (restarts, MAX_RESTARTS))
    stop_lane()
    time.sleep(5)
    if not warm():
        stop_lane()
        break
    start_lane()
    time.sleep(GRACE)
    last = pdfs_now()
    say("baseline after restart: %s pdfs" % last)
