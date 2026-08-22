"""THE IMAGE PULL - pdfs for every row, running CONCURRENT with the rd pass
(A/B SETTLED 2026-08-21: rd and pdf are SEPARATE SERVER POOLS - rd held
135 docs/s under pdf load; sequential idles the image backend).

OPERATING POINT, measured 2026-08-21: 2 processes x 28 workers (a digital
arm --lo 0 --hi 3 and a film arm --lo 3), ~6-8 docs/s AGGREGATE - the
ceiling (3x~60 workers = the same total; one process knees ~26 on the
GIL). WE MEASURE DOC/S - the pg/s in this lane's printer is an internal
load gauge only. Film completes ~3x the docs per page (~3.7 pg/doc vs
~13.4 digital) - tilt film-first when completed-doc count matters.

Per doc: map -> TotalPages. <=0 pages -> pdf='imageless' (the dead end the
login called out). Else fetch every page, G4-wrap to ONE pdf in the store,
land the relative path in the pdf column. The acquisition traps hold:
  - the PLACEHOLDER blob (md5 4081a3f2...) served as HTTP 200 is END,
    never a page
  - a SHORT document (fewer pages than the map promised) is a FAILURE row
    for retry, never a pdf - a 1-of-8 read looks exactly like success
  - refusal anywhere stops ALL workers; no retry, no rotation
Store = RECORDED CHRONOLOGY (the login's rule): CP.doc_store_dir lands
By Document/YYYY/MM Mon/DD/<id>.pdf from the rd row's recorded date.
Resume = WHERE pdf = ''.

Usage:  python image_walk.py --workers 28 --lo 0 --hi 3   (digital arm)
        python image_walk.py --workers 28 --lo 3          (film arm)
"""
import argparse
import hashlib
import json
import pathlib
import queue
import sqlite3
import sys
import threading
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP
import fetch_pages
import img2pdf
import live_delta as LD
import re

ap = argparse.ArgumentParser()
ap.add_argument("--workers", type=int, default=16)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--lo", default="0")
ap.add_argument("--hi", default="￿")
a = ap.parse_args()

BATCH = 50
STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                     r"\Legal Instruments Acquisition")
FAILS = CP.NAV_WORK / "image_walk_fails.jsonl"
VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView"

con = sqlite3.connect(CP.NAV_DB, timeout=600, check_same_thread=False)
con.execute("PRAGMA journal_mode=WAL")
con.execute("PRAGMA busy_timeout=300000")

stop = threading.Event()
lock = threading.Lock()
q = queue.Queue(maxsize=10_000)
stats = {"pdfs": 0, "imageless": 0, "fail": 0, "pages": 0}
ua = {"User-Agent": fetch_pages.UA}


def feeder():
    fed, cursor = 0, a.lo
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    while not stop.is_set():
        # FOLLOW THE RD PASS (login: "PDF must follow RD") - only docs whose
        # recorded_details already landed; the pdf lane trails the rd lane
        # through the same id order and never overtakes it
        rows = read.execute(
            "SELECT id, json_extract(recorded_details, '$.recorded')"
            " FROM navigation WHERE pdf = ''"
            " AND recorded_details != ''"
            " AND id > ? AND id < ? AND id NOT LIKE 'RC_%'"
            " ORDER BY id LIMIT 5000",
            (cursor, a.hi)).fetchall()
        if not rows:
            # caught up with the rd lane - wait for it to land more, then
            # resume from the same cursor (never exit while rd still runs)
            time.sleep(60)
            continue
        cursor = rows[-1][0]
        for did, rec_date in rows:
            if stop.is_set():
                return
            q.put((did, rec_date or ""))
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
                con.executemany("UPDATE navigation SET pdf=? WHERE id=?",
                                batch)
                con.commit()
            return
        except sqlite3.OperationalError:
            time.sleep(5)
    with pend_lock:                  # give up this round, requeue for later
        pend[:0] = batch


def get(url, referer, timeout=90):
    req = urllib.request.Request(url, headers={**ua, "Referer": referer})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def worker():
    while not stop.is_set():
        item = q.get()
        if item is None:
            q.put(None)
            return
        did, rec_date = item
        try:
            body, ct = get(VIEW + "?doc_id=" + did,
                           LD.BASE + "/DS/DocumentSearch/DocumentDetail"
                           "?doc_id=" + did)
            mhtml = body.decode("utf-8", "ignore")
            mm = re.search(r"TotalPages%22%3A(-?\d+)", mhtml)
            total = int(mm.group(1)) if mm else 0
            if total <= 0:
                with pend_lock:
                    pend.append(("imageless", did))
                    n = len(pend)
                with lock:
                    stats["imageless"] += 1
                if n >= BATCH:
                    flush()
                continue
            frames = []
            for p in range(1, total + 1):
                if stop.is_set():
                    return
                data, ct = get(f"{fetch_pages.BASE}?doc_id={did}&page={p}",
                               VIEW + "?doc_id=" + did)
                fetch_pages._check_denied(data, ct)
                if data[:2] not in (b"II", b"MM") or \
                   hashlib.md5(data).hexdigest() == fetch_pages.PLACEHOLDER:
                    break
                frames.append(data)
                with lock:
                    stats["pages"] += 1
            if len(frames) != total:
                raise ValueError(f"short: {len(frames)}/{total} pages")
            d = CP.doc_store_dir(did, rec_date)
            d.mkdir(parents=True, exist_ok=True)
            pdf = d / f"{did}.pdf"
            pdf.write_bytes(img2pdf.convert(frames))
            with pend_lock:
                pend.append((str(pdf.relative_to(STORE)), did))
                n = len(pend)
            with lock:
                stats["pdfs"] += 1
            if n >= BATCH:
                flush()
        except fetch_pages.AccessDenied as e:
            stop.set()
            print(f"  REFUSED at {did} - STOPPING ALL: {e}", flush=True)
        except Exception as e:
            with lock:
                stats["fail"] += 1
                with FAILS.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"id": did, "err": type(e).__name__,
                                         "msg": str(e)[:120]}) + "\n")


print(f"image walk [{a.lo}..{a.hi}]: {a.workers} workers", flush=True)
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
        print(f"  PROGRESS {s['pdfs']:,} pdfs · {s['pages']:,} pages "
              f"({s['pages']/el:.1f} pg/s) · {s['imageless']:,} imageless · "
              f"{s['fail']} fail · {el/60:.0f} min", flush=True)
finally:
    flush()
