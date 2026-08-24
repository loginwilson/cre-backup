"""PHASE 1 - THE RD PASS, top to bottom (login, 2026-08-20 evening: "thats
phase 1. the rd of 24 million doc id... Its literally url, pull, land,
repeat").

One job only: for every row in the navigation table with an empty
recorded_details, fetch the ACRIS rd page, parse it through rd_parse (THE
one place the format is known), land the dict into the row. NO pdf work -
the earlier walker fetched every page image alongside the rd (1,590 page
images in its first 500 docs) which is phase-3 work riding on phase 1;
rd-only is one ~60KB fetch per doc.

Design:
  - todo streams from the nav db by id-cursor (ascending = top to bottom;
    24M ids never sit in RAM, and ThreadPoolExecutor.map is NOT used
    because it buffers the whole iterable as futures)
  - workers write under one lock, committed every BATCH rows; the db is in
    WAL mode so DB Browser (read-only) watches it live
  - resume = WHERE recorded_details = '' - the table is its own ledger
  - the id-echo is asserted before the page is read; refusal stops ALL
    workers (no retry, no rotation - standing rule)
  - RC_ rows are excluded: Richmond is its own lane (POST by internal id)

OPERATING POINT, measured 2026-08-21 (single-lane-bump protocol, disjoint
table-slice measurement): 4 processes x 28 workers over disjoint id-range
quarters (--lo/--hi) = ~138-140 docs/s AGGREGATE - the server's ceiling
(4x36 = no gain; a single lane at 36 read linear only by borrowing the
controls' headroom - only the FULL-FLEET reading settles a rollout).
Judge rates from disjoint table slices or the board, never a lane's own
printer (restarted lanes' reporters go mute while landing fine).

Usage:  python rd_walk.py [--workers 28] [--lo A --hi B] [--limit N]
"""
import argparse
import pathlib
import queue
import re
import sqlite3
import sys
import threading
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP
import fetch_pages
import json
import live_delta as LD
import rd_parse as RD

ap = argparse.ArgumentParser()
ap.add_argument("--workers", type=int, default=32)
ap.add_argument("--limit", type=int, default=0)
# id-range shard: the GIL pins one process near one core (measured 114% at
# 48 threads, 49.0 docs/s = the same as 32), so scaling is PROCESSES over
# disjoint id ranges - 4 x 20 is the acquisition campaign's proven shape
# for ACRIS's ~80-connection ceiling
ap.add_argument("--lo", default="", help="walk ids > this")
ap.add_argument("--hi", default="￿", help="walk ids < this")
a = ap.parse_args()

BATCH = 200
FAILS = CP.NAV_WORK / "rd_walk_fails.jsonl"

con = sqlite3.connect(CP.NAV_DB, timeout=600, check_same_thread=False)
con.execute("PRAGMA journal_mode=WAL")
con.execute("PRAGMA busy_timeout=300000")
# ⚠ NO STARTUP COUNT. `SELECT COUNT(*) ... WHERE recorded_details != ''` is a
# full scan of 24M rows - it cost MINUTES of dead time on every restart and
# made a healthy lane look stalled. The dashboard owns the totals; a lane
# only needs to report what IT pulled.
already = 0

stop = threading.Event()
lock = threading.Lock()
q = queue.Queue(maxsize=20_000)
stats = {"done": 0, "fail": 0, "pending": 0}
ua = {"User-Agent": fetch_pages.UA}


def feeder():
    """id-cursor stream of empty rows, ascending - the top-to-bottom order"""
    fed, cursor = 0, a.lo
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    while not stop.is_set():
        rows = read.execute(
            "SELECT id FROM navigation WHERE recorded_details = ''"
            " AND id > ? AND id < ? AND id NOT LIKE 'RC_%'"
            " ORDER BY id LIMIT 10000",
            (cursor, a.hi)).fetchall()
        if not rows:
            break
        cursor = rows[-1][0]
        for (did,) in rows:
            if stop.is_set():
                return
            q.put(did)
            fed += 1
            if a.limit and fed >= a.limit:
                q.put(None)
                return
    q.put(None)


pend, pend_lock = [], threading.Lock()


def flush():
    with pend_lock:
        batch, pend[:] = pend[:], []
    if not batch:
        return
    for attempt in range(120):       # ⚠ NEVER DIE ON A LOCK. An index build
        try:                         # held an exclusive write txn for 5+ min
            with lock:               # and killed all three walkers at once.
                con.executemany(     # Rows stay in `batch` until they land.
                    "UPDATE navigation SET recorded_details=? WHERE id=?",
                    batch)
                con.commit()
            return
        except sqlite3.OperationalError:
            time.sleep(5)
    with pend_lock:                  # give up this round, requeue for later
        pend[:0] = batch


def worker():
    while not stop.is_set():
        did = q.get()
        if did is None:
            q.put(None)          # let the other workers see the end too
            return
        try:
            req = urllib.request.Request(
                LD.BASE + "/DS/DocumentSearch/DocumentDetail?doc_id=" + did,
                headers={**ua, "Referer": LD.BASE + "/DS/DocumentSearch/"})
            with urllib.request.urlopen(req, timeout=90) as r:
                html = RD.clean_html(r.read().decode("utf-8", "replace"))
            LD.check_refused(html)
            flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
            # read NOTHING until the page proves it is about this doc
            if not re.search(r"DOCUMENT ID:\s*" + re.escape(did), flat):
                raise ValueError("page does not echo id")
            rec = RD.parse_acris(html)
            rec["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            with pend_lock:
                pend.append((json.dumps(rec, separators=(",", ":")), did))
                n = len(pend)
            if n >= BATCH:
                flush()
            with lock:
                stats["done"] += 1
        except (fetch_pages.AccessDenied, LD.Refused) as e:
            # ⚠ BOTH refusal types, 2026-08-24: check_refused() raises
            # LD.Refused, but this catch only knew fetch_pages.AccessDenied -
            # so on the 09:00 re-refusal every worker logged "Refused" to the
            # fails file and KEPT REQUESTING. A detector that fires into the
            # wrong except clause is a detector that does not exist.
            stop.set()
            print(f"  REFUSED at {did} - STOPPING ALL: {e}", flush=True)
        except Exception as e:
            with lock:
                stats["fail"] += 1
                with FAILS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"id": did,
                                         "err": type(e).__name__}) + "\n")


print(f"rd walk phase 1: {already:,} already filled · "
      f"{a.workers} workers · top to bottom", flush=True)
threads = [threading.Thread(target=feeder, daemon=True)]
threads += [threading.Thread(target=worker, daemon=True)
            for _ in range(a.workers)]
t0 = time.time()
for t in threads:
    t.start()
try:
    while any(t.is_alive() for t in threads[1:]):
        time.sleep(60)
        flush()
        el = time.time() - t0
        with lock:
            d, f = stats["done"], stats["fail"]
        print(f"  PROGRESS {already + d:,} total · +{d:,} this run · "
              f"{d/el:.1f} docs/s · {f} fail · {el/60:.0f} min", flush=True)
finally:
    flush()
el = time.time() - t0
print(f"\nrun end: +{stats['done']:,} in {el/60:.1f} min "
      f"({stats['done']/max(el,1e-9):.1f} docs/s) · {stats['fail']} failed",
      flush=True)
