"""CAN SYNC RUN LIVE WHILE BACKFILL IS STILL GOING? YES - THIS IS THAT LOOP.

Login 2026-08-22: "I am ok with not live right now, but in the future it would
be important... I want to see if the sync part can go live though since we wont
be live for a while given backfill. but we can be live which would be nice on
COUNT."

⚠ WHY SYNC IS THE ONE PHASE THAT CAN GO LIVE DURING BACKFILL. Everything else
queues on SQLite's SINGLE WRITER SEAT, and that seat is the measured ceiling:
rc_pdf_land got 1.8/s and a freshly written direct-to-store writer got ~2/s -
same number, different code, because the constraint is the lock and not the
code. Sync is exempt for two reasons:

    1. --dry WRITES NOTHING TO THE NAV DB. Steps 1-3 only: system total,
       source total, delta. It reads. It cannot block a walker.
    2. Even a full sync lands ~1,650 rows/day (~0.02/s) - noise against a
       seat doing 2/s.

WHAT THIS BUYS: A LIVE DENOMINATOR. Every percentage on the board is measured
against `needed`, and `needed` is frozen at whatever the last sync said. At
3% acquired that stale denominator is the difference between "we are 3.58%
done" and "we are 3.58% done against a number that stopped being true days
ago." This makes the denominator true continuously while acquisition crawls.

⚠ IT IS POLLING, NOT PUSH. Neither source has a webhook. "Live" here means a
tight interval, and the interval is a REQUEST BUDGET decision:
    ACRIS    the CRFN edge is gallop+bisect, ~33 requests per probe
    RICHMOND one date-range window, 1 request
At the default 15 minutes that is ~136 requests/hour, against a source that
records ~1,550 documents per business day. Do not drop below 5 minutes
without a reason - you are not going to out-poll a clerk's office.

⚠ THE FIELD TRAP THIS LOOP INHERITS (docs/sources/acris/LIVE_SYNC.md §1):
`recorded_datetime` LAGS ~11 DAYS. Measured 2026-08-11: the newest
recorded_datetime in all of ACRIS was 2026-07-31 and a query for "recorded
since 2026-08-01" returned ZERO while 28,196 rows had actually landed.
A delta keyed on the record's own date reports "nothing new" forever, looks
healthy, and falls permanently behind. Key on `:updated_at` - when the row
LANDED. routine_synchronization already does; never re-derive this.

Usage:  python sync_live.py                    # 15 min, report + board
        python sync_live.py --every 300        # 5 min
        python sync_live.py --once             # one probe, then exit
        python sync_live.py --apply            # ALSO land the delta when it
                                               # appears (writes; see above)
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sqlite3
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BOARD = pathlib.Path(r"D:\CRE Decoding System\Updates\Updates.db")
PY = sys.executable

ap = argparse.ArgumentParser()
ap.add_argument("--every", type=int, default=900, help="seconds between probes")
ap.add_argument("--once", action="store_true")
ap.add_argument("--apply", action="store_true",
                help="land the delta when non-zero (writes to the nav db)")
ap.add_argument("--log", default="sync_live.log")
a = ap.parse_args()
LOG = HERE / a.log


def say(msg):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def probe():
    """Steps 1-3 for both sources. Returns {source: (system, source, delta)}.
    Parses the routine's own output rather than reimplementing its logic -
    there is ONE definition of the edge and it lives in that file."""
    out = subprocess.run(
        [PY, "-u", str(HERE / "routine_synchronization.py"), "--dry"],
        capture_output=True, text=True, timeout=900,
        cwd=str(HERE)).stdout
    found = {}
    for src in ("acris", "richmond"):
        # tolerate formatting drift: take the last three big numbers on any
        # line naming the source
        for line in out.splitlines():
            if src not in line.lower():
                continue
            nums = [int(x.replace(",", ""))
                    for x in re.findall(r"\b\d[\d,]{2,}\b", line)]
            if len(nums) >= 2:
                found[src] = (nums[0], nums[1],
                              nums[2] if len(nums) > 2 else nums[1] - nums[0])
    return found, out


def to_board(src, system, source_total, delta):
    try:
        b = sqlite3.connect(BOARD, timeout=60)
        win = time.strftime("%B %d, %Y %I:%M %p").replace(" 0", " ")
        pct = round(100 * system / source_total, 2) if source_total else 0.0
        b.execute(
            "INSERT OR REPLACE INTO update_board"
            " (phase,source,rate_now,rate,increase,pct_increase,landed,needed,"
            "  pct_of_total,eta,status,as_of)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("synchronization", src, 0.0, 0.0, delta, 0.0,
             system, source_total, pct,
             "complete" if delta == 0 else "-",
             "COMPLETE" if delta == 0 else "ACTIVE", win))
        b.commit()
        b.close()
    except Exception as e:
        say("  board write failed: %s" % e)


say("sync_live up · every %ds · apply=%s" % (a.every, a.apply))
while True:
    t0 = time.time()
    try:
        found, raw = probe()
    except Exception as e:
        say("probe FAILED: %s" % type(e).__name__)
        found, raw = {}, ""

    if not found:
        # never report a zero we did not measure
        say("probe returned nothing parseable - NOT reporting a delta "
            "(a count we did not measure is not a count)")
    for src, (system, source_total, delta) in sorted(found.items()):
        say("%-9s system %12s · source %12s · DELTA %s"
            % (src, f"{system:,}", f"{source_total:,}", f"{delta:,}"))
        to_board(src, system, source_total, delta)
        if delta and a.apply:
            say("  landing delta for %s ..." % src)
            subprocess.run([PY, "-u", str(HERE / "routine_synchronization.py"),
                            "--source", src], cwd=str(HERE), timeout=3600)

    if a.once:
        break
    time.sleep(max(30, a.every - (time.time() - t0)))
