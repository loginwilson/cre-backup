"""THE RICHMOND CENSUS — completeness proven by the county's OWN enumeration
(login 2026-08-21: "gotta confirm 100% coverage first").

Why this shape and not a per-id walk: the new site grants detail access ONLY
to ids in the last search's result set (measured 2026-08-21 - a HELD id
outside the results gets the same UNAUTHORIZED as any void id, so a cold
detail probe can classify nothing). The date-range LIST is the one surface
the county answers unconditionally - so the census sweeps every window in
their history and collects every internal id they list. Then:

    listed - held   = MISSED documents  -> land through the normal sync path
    range  - listed = VOID by the county's own testimony
    held + void = range                 -> 100% coverage, as arithmetic

    python rc_census.py --run            sweep (resumable, oldest first)
    python rc_census.py --report         listed/held/void accounting

⚠ WINDOWS ARE <= 30 DAYS (a longer ask returns a SILENT ZERO - the measured
cap). Empty windows cost one request and are recorded as swept, because "no
window ever listed id X" is only evidence once every window has actually
been swept.

⚠ CONTROL FIRST, EVERY RUN (the standing doctrine): a known-nonzero window
must parse rows before any zero is believed; rc_window.control() raises
ProbeBroken otherwise. If the county redesigns again, this run STOPS
instead of recording thousands of false-empty windows.

⚠ PACED FOR A MULTI-DAY BACKGROUND JOB: sequential, one connection,
PACE seconds between pages. ~143k pages for 2.4M listings; the census is a
one-time backfill racing nobody. Resume = the windows table; kill it any
time.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP
import rc_window as RW

DB = (pathlib.Path(r"D:\CRE Decoding System\00 Synchronizations")
      / "Legal Instruments Synchronization" / "Richmond Census.db")
# ⚠ 1940 WAS TOO LATE. The first census windows returned 200+ rows/month in
# 1940 - the county lists records at least that old, so anything before the
# START would have been branded VOID falsely. 1850 predates organized county
# recording; empty windows cost one request each and are the PROOF the range
# start is early enough (the first nonzero window marks the true beginning).
START = dt.date(1850, 1, 1)
SPAN = 30                       # the measured window cap
# 10 workers @ 0.30s = the rd backfill's proven concurrency against this
# county (10 concurrent, 2.4M requests, zero trips) - not a new experiment
WORKERS = 10
PACE = 0.30

ap = argparse.ArgumentParser()
ap.add_argument("--run", action="store_true")
ap.add_argument("--report", action="store_true")
a = ap.parse_args()

# check_same_thread=False: 8 workers share this connection, but every
# write already serializes under the run() lock - sqlite only objects to
# the cross-thread handle, not to what we do with it
con = sqlite3.connect(DB, timeout=600, check_same_thread=False)
con.executescript("""
CREATE TABLE IF NOT EXISTS listing (
    internal_id INTEGER PRIMARY KEY,
    instrument  TEXT, recorded TEXT, type TEXT, window_start TEXT);
CREATE TABLE IF NOT EXISTS window (
    start TEXT PRIMARY KEY, end TEXT, rows INTEGER, pages INTEGER,
    swept_at TEXT);
""")


def windows():
    d = START
    today = dt.date.today()
    while d <= today:
        e = min(d + dt.timedelta(days=SPAN - 1), today)
        yield d, e
        d = e + dt.timedelta(days=1)


def run():
    # ⚠ PARALLEL OVER WINDOWS (login 2026-08-21: "1-2 days is
    # absurdly long" - and it was: the site served the rd backfill's 2.4M
    # requests at 10 concurrent without one trip; this census is 143k
    # requests, 6% of that proven load). Windows are independent; sqlite
    # writes serialize under one lock; a failed window is NEVER marked
    # swept, so resume re-asks it. ProbeBroken stops the whole pool.
    import threading
    from concurrent.futures import ThreadPoolExecutor
    RW.control()
    print(f"control OK - census running ({WORKERS} workers)")
    done = {r[0] for r in con.execute("SELECT start FROM window")}
    todo = [(s, e) for s, e in windows() if s.isoformat() not in done]
    total = len(done) + len(todo)
    lock = threading.Lock()
    stop = threading.Event()
    n_win = [len(done)]
    t0 = time.time()

    def one(win):
        s, e = win
        if stop.is_set():
            return
        try:
            rows, pages = RW.window(s.isoformat(), e.isoformat(), pace=PACE)
        except RW.ProbeBroken:
            stop.set()
            raise
        except Exception as ex:
            print(f"  ⚠ {s} window failed ({type(ex).__name__}) - left"
                  f" unswept; resume re-asks it", flush=True)
            return
        with lock:
            for r in rows:
                con.execute("INSERT OR IGNORE INTO listing VALUES"
                            " (?,?,?,?,?)",
                            (int(r["internal_id"]), r["instrument"],
                             r["recorded"], r["type"], s.isoformat()))
            con.execute("INSERT OR REPLACE INTO window VALUES (?,?,?,?,?)",
                        (s.isoformat(), e.isoformat(), len(rows), pages,
                         time.strftime("%Y-%m-%dT%H:%M:%S")))
            con.commit()
            n_win[0] += 1
            if rows or n_win[0] % 25 == 0:
                el = (time.time() - t0) / 60
                print(f"PROGRESS {n_win[0]}/{total} windows · {s}"
                      f" +{len(rows):,} rows · {el:.0f} min", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(one, todo))
    print("CENSUS SWEEP COMPLETE" if not stop.is_set()
          else "STOPPED - probe broken")


def report():
    listed = {r[0] for r in con.execute("SELECT internal_id FROM listing")}
    nav = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=900)
    held = {int(r[0][3:]) for r in nav.execute(
        "SELECT id FROM navigation WHERE id > 'RC_'") if r[0][3:].isdigit()}
    nav.close()
    w = con.execute("SELECT COUNT(*), MIN(start), MAX(end)"
                    " FROM window").fetchone()
    total = sum(1 for _ in windows())
    hi = max(held | listed) if held | listed else 0
    missed = sorted(listed - held)
    phantom = sorted(held - listed)
    print(f"windows swept    : {w[0]}/{total}  ({w[1]} .. {w[2]})")
    print(f"county lists     : {len(listed):,}")
    print(f"we hold          : {len(held):,}")
    print(f"MISSED (listed, not held)  : {len(missed):,}"
          + (f"  e.g. {missed[:5]}" if missed else ""))
    print(f"held, never listed (yet)   : {len(phantom):,}"
          " (windows not swept yet explain these until the sweep completes)")
    if w[0] == total:
        void = hi - len(held | set(missed))
        print(f"VOID by the county's own testimony: "
              f"{hi:,} - {len(held | set(missed)):,} = {void:,}")
        print("held + missed + void = range -> 100% COVERAGE"
              if not missed else
              "land the MISSED first, then the identity closes")


if a.run:
    run()
elif a.report:
    report()
else:
    print(__doc__)
