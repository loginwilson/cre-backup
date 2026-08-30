"""ACRIS PDF WIDTH BENCH - find the pdf-worker count that pulls CLEAN.

login 2026-08-28: "figure out how to get the pdf optimized workers within
that batch. no reason a pdf shouldnt be capable of pulling." Proven: the
image IS there (a failing doc's viewer returns 13 KB + TotalPages when
fetched calmly). It degraded only under 130-worker load. So there is a
width where the image endpoint stays clean - MEASURE it, do not guess.

METHOD (rc_bench's shape): one warm pooled session (the group-entry
model), sweep the ACTIVE pdf width up a ladder, each rung a fixed window,
measuring docs/s AND the soft-refusal rate. The soft-refusal is acris's
4,922-byte "no TotalPages" page served under convergence - page_count now
RAISES on it, so it is a clean, countable signal, distinct from a real
503 (which stops the whole bench). Control-first: width 1 must pull a real
doc before any failure at width N is believed.

⚠ MEASURE-ONLY: nothing is written to the db. The fetched images are
discarded; the docs stay todo and get pulled for real by the lane later.
⚠ ONE ACCESS POINT: never run this while acris_reproduction is up.

    python acris_pdf_bench.py [--rungs 8,16,24,32,40,48] [--secs 90]
"""
import argparse
import queue
import sqlite3
import sys
import threading
import time
import urllib.error

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\smile\Downloads\Source Folder (Real Estate"
                   r" Data)\Decoder Prompt\decoder")
import corpus_paths as CP                                      # noqa: E402
import fetch_pages                                             # noqa: E402
import live_delta as LD                                        # noqa: E402
import acris_pdf as AP                                         # noqa: E402
import requests                                                # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--rungs", default="8,16,24,32,40,48")
ap.add_argument("--secs", type=int, default=90)
ap.add_argument("--stagger", type=float, default=0.5)
a = ap.parse_args()
RUNGS = [int(x) for x in a.rungs.split(",")]
MAXW = max(RUNGS)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": fetch_pages.UA})
SESSION.mount("https://", requests.adapters.HTTPAdapter(
    pool_connections=1, pool_maxsize=MAXW + 8, max_retries=0,
    pool_block=True))

reqs = [0]
reqs_lock = threading.Lock()


def fetch_bytes(url, referer, timeout=90):
    with reqs_lock:
        reqs[0] += 1
    r = SESSION.get(url, headers={"Referer": referer}, timeout=timeout)
    try:
        if r.status_code >= 400:
            err = urllib.error.HTTPError(url, r.status_code, r.reason,
                                         r.headers, None)
            err.acris_shed = r.status_code in (429, 500, 502, 503, 504)
            raise err
        return r.content, r.headers.get("Content-Type", "")
    finally:
        r.close()


AP.FETCH = fetch_bytes

# the real work order: rd landed, pdf still todo, ascending (oldest first,
# exactly where the lane failed)
ids = queue.Queue()
_read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True)
_rows = _read.execute(
    "SELECT id, recorded_details FROM navigation"
    " WHERE pdf IN ('','pending') AND recorded_details != ''"
    " AND id NOT LIKE 'RC_%' ORDER BY id LIMIT 20000").fetchall()
for _r in _rows:
    ids.put(_r)
print("bench feed: %d todo docs (oldest first)" % len(_rows), flush=True)

stop = threading.Event()
rung = {"done": 0, "soft": 0, "short": 0, "fail": 0}
rung_lock = threading.Lock()


def _rec_date(v):
    if v and v.lstrip().startswith("{"):
        import json
        try:
            return json.loads(v).get("recorded", "") or ""
        except Exception:
            return ""
    return v or ""


def worker(deadline):
    while time.time() < deadline and not stop.is_set():
        try:
            did, rd = ids.get_nowait()
        except queue.Empty:
            return
        try:
            AP.fetch_pdf(did, _rec_date(rd))       # measure-only, discard
            with rung_lock:
                rung["done"] += 1
        except (fetch_pages.AccessDenied, LD.Refused) as e:
            stop.set()
            print("  ⚠ REAL REFUSAL at %s - STOPPING BENCH: %.80s"
                  % (did, e), flush=True)
        except urllib.error.HTTPError as e:
            if getattr(e, "acris_shed", False):
                stop.set()
                print("  ⚠ %d (shed) at %s - STOPPING BENCH" % (e.code, did),
                      flush=True)
            else:
                with rung_lock:
                    rung["fail"] += 1
        except AP.Short:
            with rung_lock:
                rung["short"] += 1
        except ValueError as e:
            # the soft-refusal: the 4,922-byte page with no TotalPages
            with rung_lock:
                if "did not identify" in str(e):
                    rung["soft"] += 1
                else:
                    rung["fail"] += 1
        except Exception:
            with rung_lock:
                rung["fail"] += 1


# control-first: width 1 must pull one doc before any failure is believed
print("control @ width 1 ...", flush=True)
_c0 = reqs[0]
worker(time.time() + 30)
if rung["done"] == 0 and rung["soft"] == 0:
    print("  ⚠ control pulled nothing in 30s - not benchmarking on noise",
          flush=True)
    sys.exit(1)
print("  control ok: done %d soft %d short %d (%d reqs)"
      % (rung["done"], rung["soft"], rung["short"], reqs[0] - _c0), flush=True)

print("\n%-6s %8s %8s %7s %7s %7s %8s" % ("width", "docs/s", "done",
                                          "soft", "short", "fail", "soft%"))
for w in RUNGS:
    if stop.is_set():
        break
    with rung_lock:
        rung.update(done=0, soft=0, short=0, fail=0)
    r0, t0 = reqs[0], time.time()
    deadline = t0 + a.secs
    ts = []
    for i in range(w):
        t = threading.Thread(target=worker, args=(deadline,), daemon=True)
        t.start()
        ts.append(t)
        time.sleep(a.stagger)
    for t in ts:
        t.join()
    el = time.time() - t0
    with rung_lock:
        d, so, sh, fa = (rung["done"], rung["soft"], rung["short"],
                         rung["fail"])
    tot = d + so + sh + fa
    softpct = 100.0 * so / tot if tot else 0.0
    print("%-6d %8.2f %8d %7d %7d %7d %7.1f%%"
          % (w, d / el, d, so, sh, fa, softpct), flush=True)

print("\nbench end · %d reqs total" % reqs[0], flush=True)
