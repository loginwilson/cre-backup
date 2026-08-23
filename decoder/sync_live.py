"""LIVE SYNC — is each source level, and is the whole db level, RIGHT NOW?

Login 2026-08-22: *"each against their source total and then a total row
together so we know each source is live and then the entire db total"* and
*"i want live not a batch for the day with sync"*.

⚠ THIS FILE'S FIRST VERSION REPORTED GARBAGE AND IS WORTH REMEMBERING. It
regex-scraped numbers off routine_synchronization's stdout and produced:

    acris     system 21,615,745 · source 2,501,589 · DELTA -19,114,156
    richmond  system 21,615,745 · source 2,501,589 · DELTA -19,114,156

- ACRIS's total minus RICHMOND's total, reported for both sources, as a
NEGATIVE delta of 19 million. It had a guard against reporting a delta it
did not measure, but the guard only caught EMPTY output, never WRONG output.
**Scraping a human-readable log is not a measurement.** crfn_monitor.py had
the right shape all along: "CONTROL FIRST... if the known-good watermark does
not resolve, this refuses to report anything at all."

THE FIX: THERE IS ONE AUTHORITY AND IT IS THE LEDGER. routine_synchronization
computes levelness and writes `synchronization` (run_at, source, system_total,
source_total, delta, doc_ids). This file RUNS it, then READS THAT TABLE. No
parsing, no second definition of the edge, nothing to drift.

⚠ WHY SYNC CAN BE LIVE WHILE ACQUISITION BACKFILLS. Everything else queues on
SQLite's ONE writer seat (measured: two independently written per-row writers
both landed on ~2/s; batching bare UPDATEs cleared 12.5/s). Sync is exempt on
VOLUME: it appends ~1,650 rows/day = 0.019/s. The lander wanted 12/s and the
keyer swept millions - THOSE starve a seat. An id-append does not.

⚠ IT IS POLLING, NOT PUSH. Neither source has a webhook. The interval is a
request-budget decision: the ACRIS edge is gallop+bisect (~30 requests,
crfn_monitor.py), richmond is one date-range window. Do not go below ~5 min;
you cannot out-poll a clerk's office recording ~1,550 documents a day.

⚠ THE FIELD TRAP THIS INHERITS (docs/sources/acris/LIVE_SYNC.md §1):
`recorded_datetime` LAGS ~11 DAYS. Measured 2026-08-11: newest
recorded_datetime in all of ACRIS was 2026-07-31 while a query for "recorded
since 2026-08-01" returned ZERO and 28,196 rows had actually landed. Key every
delta on `:updated_at` - when the row LANDED. Never re-derive this.

Usage:  python sync_live.py                 # 15 min, report + board
        python sync_live.py --every 300     # 5 min
        python sync_live.py --once
        python sync_live.py --apply         # land the delta when non-zero
"""
from __future__ import annotations

import argparse
import pathlib
import sqlite3
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LEDGER = ("D:/CRE Decoding System/00 Synchronizations"
          "/Legal Instruments Synchronization"
          "/Legal Instruments Synchronization.db")
BOARD = "D:/CRE Decoding System/Updates/Updates.db"
PY = sys.executable

ap = argparse.ArgumentParser()
ap.add_argument("--every", type=int, default=900)
ap.add_argument("--once", action="store_true")
ap.add_argument("--apply", action="store_true",
                help="land the delta when non-zero (writes ~0.019 rows/s)")
ap.add_argument("--log", default="sync_live.log")
a = ap.parse_args()
LOG = HERE / a.log


def say(msg):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def refresh_ledger():
    """Run the ONE authority. --dry = steps 1-3 (system, source, delta):
    it measures levelness and writes the ledger without landing anything."""
    args = [PY, "-u", str(HERE / "routine_synchronization.py")]
    if not a.apply:
        args.append("--dry")
    subprocess.run(args, cwd=str(HERE), timeout=3600,
                   capture_output=True, text=True)


def read_ledger():
    """Newest row per source, straight from the ledger. Reads OUR OWN db -
    never a scan of the contended navigation table."""
    con = sqlite3.connect("file:" + LEDGER + "?mode=ro", uri=True, timeout=60)
    out = {}
    for src in ("acris", "richmond", "TOTAL"):
        r = con.execute(
            "SELECT run_at, system_total, source_total, delta"
            " FROM synchronization WHERE source=?"
            " ORDER BY rowid DESC LIMIT 1", (src,)).fetchone()
        if r:
            out[src] = r
    con.close()
    return out


def to_board(src, system, source_total, delta, run_at):
    try:
        b = sqlite3.connect(BOARD, timeout=60)
        pct = round(100 * system / source_total, 2) if source_total else 0.0
        b.execute(
            "INSERT OR REPLACE INTO update_board"
            " (phase,source,rate_now,rate,increase,pct_increase,landed,needed,"
            "  pct_of_total,eta,status,as_of)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("synchronization", src.lower(), 0.0, 0.0, delta, 0.0,
             system, source_total, pct,
             "level" if delta == 0 else "-",
             "COMPLETE" if delta == 0 else "ACTIVE", str(run_at)))
        b.commit()
        b.close()
    except Exception as e:
        say("  board write failed for %s: %s" % (src, e))


say("sync_live up · every %ds · apply=%s · ledger is the authority"
    % (a.every, a.apply))
while True:
    t0 = time.time()
    try:
        refresh_ledger()
    except Exception as e:
        say("routine_synchronization FAILED: %s - reporting the LAST ledger"
            " values, not a guess" % type(e).__name__)

    rows = read_ledger()
    if not rows:
        say("ledger empty - NOT reporting (a number we did not measure is"
            " not a number)")
    for src in ("acris", "richmond", "TOTAL"):
        if src not in rows:
            continue
        run_at, system, source_total, delta = rows[src]
        mark = "LEVEL" if delta == 0 else ("BEHIND %s" % f"{delta:,}")
        say("%-9s system %13s · source %13s · %s   (%s)"
            % (src, f"{system:,}", f"{source_total:,}", mark, run_at))
        to_board(src, system, source_total, delta, run_at)

    if a.once:
        break
    time.sleep(max(60, a.every - (time.time() - t0)))
