"""THE RICHMOND RD LANE - recorded details for every RC_ row, landing in
the one table (login, 2026-08-20: "acris max speed, richmond max speed, and
keyer following both"). Different host, own connection budget - costs the
ACRIS campaign nothing.

Fetch is the door-URL POST by INTERNAL id (id minus the RC_ prefix - the
binding measured today: document_id = "RC_" + internal_id). Instrument
numbers REPEAT at Richmond, so every pull cross-checks the returned
instrument against rc_binding's for this document - mismatch is a FAIL row,
never a capture (a BBL from someone else's page is the one unrecoverable
error). parse_detail returns bbls; they land as parcels [{"bbl": ...}] so
the keyer reads ACRIS and RC rows identically.

A stale session returns the UNAUTHORIZED shell at HTTP 200 - the window is
rebuilt once, then the doc fails. Refusal stops ALL workers, no retry.
Measured 2026-08-18: conc 8 = 4.4 docs/s near-linear; the one trip ever was
a cold burst at 16, so this lane holds at 10.

Usage:  python rc_walk.py [--workers 10] [--limit N]
"""
import argparse
import json
import pathlib
import queue
import sqlite3
import sys
import threading
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP
import rc_source as RC
import rc_sync as RS

ap = argparse.ArgumentParser()
ap.add_argument("--workers", type=int, default=10)
ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()

BATCH = 100
FAILS = CP.NAV_WORK / "rc_walk_fails.jsonl"

con = sqlite3.connect(CP.NAV_DB, timeout=600, check_same_thread=False)
con.execute("PRAGMA journal_mode=WAL")
con.execute("PRAGMA busy_timeout=300000")
spec = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True,
                       check_same_thread=False)
spec_lock = threading.Lock()

stop = threading.Event()
lock = threading.Lock()
q = queue.Queue(maxsize=10_000)
stats = {"done": 0, "fail": 0, "lotless": 0}
tl = threading.local()


def feeder():
    fed, cursor = 0, "RC_"
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    while not stop.is_set():
        rows = read.execute(
            "SELECT id FROM navigation WHERE recorded_details = ''"
            " AND id > ? AND id LIKE 'RC_%' ORDER BY id LIMIT 5000",
            (cursor,)).fetchall()
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
            q.put(None)
            return
        iid = did[3:]
        try:
            with spec_lock:
                row = spec.execute(
                    "SELECT instrument FROM rc_binding WHERE document_id=?",
                    (did,)).fetchone()
            expect = row[0] if row else None
            d = None
            for attempt in range(2):
                try:
                    if not hasattr(tl, "w"):
                        tl.w = RS.Window("08/17/2026", "08/17/2026")
                    d = tl.w.detail(iid)
                    break
                except RC.Unauthorized:
                    if hasattr(tl, "w"):
                        del tl.w          # stale session - rebuild once
                    if attempt:
                        raise
            if d is None:
                raise ValueError("no document")
            if expect and d.get("instrument") != expect:
                raise ValueError(f"instrument mismatch "
                                 f"{d.get('instrument')!r} != {expect!r}")
            bbls = d.pop("bbls", [])
            if bbls:
                d["parcels"] = [{"bbl": b} for b in bbls]
            else:
                with lock:
                    stats["lotless"] += 1
            d["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            with pend_lock:
                pend.append((json.dumps(d, separators=(",", ":")), did))
                n = len(pend)
            if n >= BATCH:
                flush()
            with lock:
                stats["done"] += 1
        except RC.Refused as e:
            stop.set()
            print(f"  REFUSED at {did} - STOPPING ALL: {e}", flush=True)
        except Exception as e:
            with lock:
                stats["fail"] += 1
                with FAILS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"id": did, "err": type(e).__name__,
                                         "msg": str(e)[:120]}) + "\n")


print(f"rc walk: {a.workers} workers", flush=True)
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
            s = dict(stats)
        print(f"  PROGRESS {s['done']:,} done ({s['done']/el:.1f} docs/s) · "
              f"{s['lotless']:,} lot-less · {s['fail']} fail · "
              f"{el/60:.0f} min", flush=True)
finally:
    flush()
