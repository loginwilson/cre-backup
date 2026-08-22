"""Keep the ACRIS map running overnight through outages, sleep and restarts.

⚠ WHY THE MAPPER ALONE IS NOT ENOUGH. map_acris.py drops a document on any
network exception and stops the whole run when a batch returns zero successes.
That is correct behaviour for a refusal — but a dropped wifi link, a laptop
sleeping, or a router reboot looks identical to it, and the run would simply be
over with nobody watching. A 15-hour unattended job needs to survive things
that last 30 seconds.

WHAT THIS DOES
    * restarts the mapper whenever it exits, until the map is complete
    * waits longer after each consecutive failure (30s, 60s, 120s ... max 10min)
      so a genuinely down link is not hammered
    * resets the backoff as soon as a run makes real progress
    * logs every restart with the count at that moment

⚠ WHAT IT DOES NOT DO — AND MUST NOT. It does not restart through a REFUSAL.
If ACRIS declines service, the mapper stops on purpose and a supervisor that
relaunches it would be retrying into a block automatically, all night, which is
exactly the behaviour this project has refused all day. The log is checked for
the refusal marker and the supervisor exits.

⚠ RESUMING IS FREE because the mapper skips ids already in acris_maps.jsonl —
so a restart costs one pass over the done-set, not repeated work.
"""
import pathlib
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAPS = pathlib.Path("acris_maps.jsonl")
IDS = pathlib.Path("acris_ids.jsonl")
LOG = pathlib.Path("_supervise.log")
MAX_BACKOFF = 600


def count(p):
    if not p.exists():
        return 0
    n = 0
    with open(p, "rb") as f:
        for _ in f:
            n += 1
    return n


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    target = count(IDS)
    log(f"supervising · {target:,} documents to map")
    backoff, run, zero_runs = 30, 0, 0
    while True:
        done = count(MAPS)
        if target and done >= target * 0.999:
            log(f"COMPLETE · {done:,}/{target:,}")
            return
        run += 1
        log(f"run #{run} starting at {done:,}/{target:,} "
            f"({100*done/max(target,1):.1f}%)")
        import os
        env = dict(os.environ, MAP_CONC=os.environ.get("MAP_CONC", "128"))
        runlog = pathlib.Path("_map_acris_run.log")
        # ⚠ REMEMBER WHERE THIS RUN'S OUTPUT BEGINS. The log is CUMULATIVE and
        # the first version read its last 4,000 characters — so ANY refusal
        # ever printed, by any run, sat in the tail and would stop the
        # supervisor permanently on the next exit. A transient refusal at 07:20
        # would have silently ended the overnight job hours later, with the
        # supervisor reporting it as a deliberate stop.
        start_at = runlog.stat().st_size if runlog.exists() else 0

        with open(runlog, "a", encoding="utf-8") as out:
            p = subprocess.run([sys.executable, "-u", "map_acris.py"],
                               stdout=out, stderr=subprocess.STDOUT, env=env)
        after = count(MAPS)
        gained = after - done

        # ⚠ A REFUSAL IS NOT A CRASH. Do not relaunch into it — but judge it on
        # THIS run only.
        this_run = ""
        if runlog.exists():
            with open(runlog, encoding="utf-8", errors="replace") as fh:
                fh.seek(start_at)
                this_run = fh.read()
        # ⚠ ANY REFUSAL ENDS SUPERVISION. THE RULE ABOVE WAS WRONG AND IT WAS
        # WRONG BECAUSE IT DESCRIBED A BUG.
        #
        # It used to read: "a refusal that still let the run do real work is
        # transient — batches recover independently; only a run that was refused
        # AND achieved nothing is actually blocked." Batches appeared to recover
        # only because map_acris scoped its stop flag INSIDE each batch, so the
        # next batch silently went back at ACRIS. This file then read the
        # resulting progress as evidence the refusal had not mattered.
        #
        # On 2026-08-10 that pair of assumptions logged SIX refusals as
        # "transient ... continuing" and kept requesting for hours. Two
        # components can agree perfectly and both be wrong, and the agreement is
        # what makes it look like a working system.
        #
        # A refusal is an ANSWER. Progress alongside it does not soften it.
        if "REFUSED" in this_run:
            log(f"ACRIS REFUSED SERVICE (run gained {gained:,}) — STOPPING. "
                f"Not retrying, not backing off into it. "
                f"Resume by hand later at lower MAP_CONC.")
            return

        log(f"run #{run} exited rc={p.returncode}, mapped {gained:,} "
            f"(total {after:,})")
        # ⚠ NEVER RETRY A BROKEN RUN ALL NIGHT AGAIN.
        # Overnight this supervisor relaunched a run that mapped ZERO documents
        # thirteen times over two hours, each time logging only "little
        # progress". The cause was a falsy-zero bug in the mapper, and the
        # supervisor's patience is exactly what hid it. Backoff is for a down
        # LINK; repeated zero-progress runs are a BUG, and a bug needs a human,
        # not another attempt.
        if gained > 1000:
            backoff, zero_runs = 30, 0
        else:
            zero_runs += 1
            if zero_runs >= 3:
                log(f"STOPPING: {zero_runs} consecutive runs made no progress. "
                    f"This is a defect, not an outage — check "
                    f"_map_acris_run.log for the failure reason.")
                return
            backoff = min(backoff * 2, MAX_BACKOFF)
            log(f"no progress ({zero_runs}/3) — backing off {backoff}s")
        time.sleep(backoff)


if __name__ == "__main__":
    main()
