"""KEEP THE OVERNIGHT WALK ALIVE — and know the difference between dead and STOPPED.

    ACRIS_CORPUS_ROOT=D:/acris nohup python -u watchdog.py --until 05:00 &

⚠ WHY. Login is asleep; the walk runs to 05:00. A driver that dies at 01:00 costs four
hours and nobody is awake to notice. Nothing else in the tree restarts it.

⚠ THE ONE DISTINCTION THAT MATTERS. A crash and a refusal look identical from outside —
both leave no driver running. Restarting after a refusal would be exactly the
"retry the refused request" the phase doc forbids, and the limiter is address-level, so
it would cost Login their own ACRIS access while they sleep.

    _STOP present  ->  ACRIS said no. NEVER restart. Report and exit.
    _STOP absent   ->  the process died on its own. Restart is safe.

The stop flag is a FILE precisely so it survives the death of the process that wrote it;
an in-memory flag would be erased by the very crash it needs to outlive.

⚠ RESTARTS ARE BOUNDED. A driver that dies instantly and repeatedly is broken, not
unlucky — after `--max-restarts` the watchdog stops and leaves the evidence rather than
spinning until morning writing nothing.
"""
from __future__ import annotations

import argparse, datetime, os, pathlib, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
import corpus_paths as CP
ROOT = CP.ROOT
STOP = CP.STOP
LOG = CP.log("watchdog")


def say(m):
    line = f"[{datetime.datetime.now():%H:%M:%S}] {m}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def driver_alive():
    """⚠ Match on the SCRIPT NAME in the command line, not on 'python' — this watchdog
    is itself a python process and would otherwise find only itself."""
    # ⚠ psutil, NOT wmic. wmic is deprecated and ABSENT from this machine's PATH —
    # the call raised, the except branch returned True ("assume alive"), and the
    # watchdog would have sat there all night believing a dead driver was running.
    # A guard whose probe always says "fine" is not a guard.
    try:
        import psutil
        for pr in psutil.process_iter(["name", "cmdline"]):
            try:
                cl = pr.info.get("cmdline") or []
            except Exception:
                continue
            if any("overnight.py" in str(x) for x in cl):
                return True
        return False
    except Exception:
        return True          # ⚠ can't tell -> assume alive; never restart on ignorance


def ledger_pages():
    import sqlite3
    p = CP.LEDGER
    if not p.exists():
        return 0
    try:
        c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        n = c.execute("SELECT COALESCE(SUM(got),0) FROM doc WHERE status='ok'").fetchone()[0]
        c.close()
        return n or 0
    except Exception:
        return 0


def only_one(tag):
    """⚠ REFUSE TO BE THE SECOND COPY. Restarting the run by hand left 6 drivers and 4
    watchdogs alive at once on 2026-08-17 — and because each watchdog restarts a driver
    it believes is missing, duplicates BREED rather than merely accumulate. Every copy
    then draws on the same address-level limiter while each one thinks it is the only
    client, which is exactly the pattern the phase doc forbids.

    A PID file alone is not enough: a killed process leaves its file behind. Check that
    the recorded PID is BOTH alive AND running this same script before yielding to it."""
    import os as _os
    pf = CP.pid_file(tag)
    try:
        import psutil
        if pf.exists():
            old = int(pf.read_text().strip() or 0)
            if old and psutil.pid_exists(old):
                try:
                    cl = " ".join(str(x) for x in (psutil.Process(old).cmdline() or []))
                    if f"{tag}.py" in cl:
                        print(f"  {tag}: pid {old} is already running — refusing to start a second copy")
                        raise SystemExit(0)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        pf.write_text(str(_os.getpid()), encoding="utf-8")
    except SystemExit:
        raise
    except Exception:
        pass          # ⚠ the guard must never be the reason nothing runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--until", default="05:00")
    ap.add_argument("--every", type=int, default=120)
    ap.add_argument("--max-restarts", type=int, default=8)
    # ⚠ MEASURED OPTIMUM, keep in step with pull.py DEFAULT. 4 x 20 = 80 connections;
    # 80 is ACRIS's knee (140 conns collapses to ~60 pg/s). This default only applies to a
    # direct `python watchdog.py` — pull.py passes its own --args — but a stale default
    # here is how a tuned config silently stops being the one that runs.
    ap.add_argument("--args", default="--procs 4 --conc 20 --batch 5 --docs-cap 6000 "
                                      "--boro  --lo 8 --hi 300")
    a = ap.parse_args()
    only_one("watchdog")

    hh, mm = (int(x) for x in a.until.split(":"))
    now = datetime.datetime.now()
    end = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if end <= now:
        end += datetime.timedelta(days=1)

    say(f"WATCHDOG up — guarding until {end:%H:%M}, checking every {a.every}s")
    restarts, last_pages, stalls = 0, ledger_pages(), 0

    while datetime.datetime.now() < end:
        time.sleep(a.every)
        if STOP.exists():
            say("⚠ _STOP present — ACRIS refused. NOT restarting. Watchdog exiting.")
            return
        pages = ledger_pages()
        if pages > last_pages:
            say(f"ok · {pages:,} pages recorded (+{pages-last_pages:,})")
            stalls = 0
        else:
            stalls += 1
            say(f"⚠ no new pages for {stalls} check(s) · {pages:,} total")
        last_pages = pages

        if not driver_alive():
            if restarts >= a.max_restarts:
                say(f"⚠ {restarts} restarts already — driver is broken, not unlucky. "
                    "Stopping and leaving the evidence.")
                return
            restarts += 1
            until = f"--until {a.until}"
            cmd = [sys.executable, "-u", str(HERE / "overnight.py")] + \
                a.args.split() + until.split()
            say(f"driver gone and no _STOP -> restart #{restarts}")
            with open(CP.log("overnight_run"), "a", encoding="utf-8") as lg:
                subprocess.Popen(cmd, stdout=lg, stderr=lg,
                                 env=dict(os.environ, ACRIS_CORPUS_ROOT=str(ROOT)),
                                 cwd=str(HERE))
    say(f"WATCHDOG done at {a.until} · {ledger_pages():,} pages · {restarts} restarts")


if __name__ == "__main__":
    main()
