"""IS THE RICHMOND PDF FETCH SLOW, OR IS rc_lane SLOW? — one measurement.

login 2026-08-25: "over 2 days for 900,000 docs is absurd given that there
are no access restriction on richmond so you need to figure out why your
acqusition process is so slow. It is your code" — and, ruling out the excuse
I was about to reach for: "no youve run over 10 in peak hours too".

So this isolates the DOWNLOAD PATH from the lane's structure. It mints its
own tokens and downloads them in its own process, with nothing else running:
no miners competing for the GIL, no writer, no probe, no rd_heal.

    rc_lane measures  ~2.4 docs/s at 16 pullers
    rc_pdf_pull measured 11.6 docs/s at 16 workers (2026-08-22 23:08)

If this benchmark reaches ~11/s, the fetch is fine and rc_lane's STRUCTURE is
the defect. If it also sits near 2.4/s, the fetch itself regressed and the
lane is innocent. Either answer is worth more than another theory.

⚠ IT WRITES NOTHING - no store, no db. It downloads, measures, discards. A
benchmark that lands files would be indistinguishable from the lane it is
supposed to be measuring against.

⚠ SECURITY: same host, same headers, same tokens the lane already uses, and
FEWER requests than a minute of normal running. On 401/403/429 it stops
immediately and reports - it does not retry and does not rotate anything.

    python rc_bench.py                  # mint 120, try 8 / 16 / 32
    python rc_bench.py --n 200 --levels 16,32,48
"""
from __future__ import annotations

import argparse
import pathlib
import queue
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests                                                # noqa: E402
import corpus_paths as CP                                      # noqa: E402
import rc_source as RC                                         # noqa: E402
import rc_sync as RCS                                          # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=120, help="documents to mint")
ap.add_argument("--levels", default="8,16,32",
                help="puller counts to compare")
ap.add_argument("--mint-threads", type=int, default=12)
a = ap.parse_args()

HDRS = {"User-Agent": RC.UA,
        "Referer": RC.BASE + "/",
        "Accept": "application/pdf,*/*"}
REFUSED = threading.Event()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


# ── 1 · take work straight off the todo index ────────────────────────────
con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=180)
con.execute("PRAGMA busy_timeout=180000")
# ⚠⚠ SAMPLE WHAT THE LANE ACTUALLY PULLS, OR THE BENCHMARK LIES.
# The first version of this took ORDER BY id DESC - the NEWEST richmond ids -
# and measured 30 docs/s against the lane's 2.4, which looked like a 12x code
# defect. It was not: those documents average 0.26 MB and the ones the lane
# is working average 5.2 MB. In BYTES the lane was already the faster of the
# two. next_ids() walks ASCENDING with image_state='present', so this must.
ids = [r[0] for r in con.execute(
    "SELECT id FROM navigation WHERE id > 'RC' AND id LIKE 'RC_%'"
    " AND recorded_details != '' AND pdf = ''"
    " AND json_extract(recorded_details, '$.image_state') = 'present'"
    " ORDER BY id LIMIT ?", (a.n,))]
con.close()
print("took %d richmond ids that still need a pdf" % len(ids))

# ── 2 · mint tokens exactly the way the lane's miner does ────────────────
tl = threading.local()
minted, mlk = [], threading.Lock()
q_in: queue.Queue = queue.Queue()
for _i in ids:
    q_in.put(_i)


def mint():
    while not REFUSED.is_set():
        try:
            did = q_in.get_nowait()
        except queue.Empty:
            return
        iid = did[3:]
        try:
            if not hasattr(tl, "op"):
                w = RCS.Window("08/17/2026", "08/17/2026")
                tl.op = urllib.request.build_opener(
                    urllib.request.HTTPCookieProcessor(w.s.jar), _NoRedirect())
                tl.op.addheaders = [("User-Agent", RC.UA)]
            time.sleep(RC.PACE)
            req = urllib.request.Request(
                RC.BASE + "/ViewVscmsDocument/ViewContent"
                "?p_endorsementId=%s" % iid)
            req.add_header("Referer",
                           RC.BASE + "/Search/ViewDocumentInfo/%s" % iid)
            loc = None
            try:
                with tl.op.open(req, timeout=60):
                    pass
            except urllib.error.HTTPError as e:
                if e.code in (401, 403, 429):
                    REFUSED.set()
                    print("  ⚠ REFUSED while minting (HTTP %d) - stopping"
                          % e.code)
                    return
                loc = (e.headers.get("Location")
                       if e.code in (301, 302, 303) else None)
            if loc:
                with mlk:
                    minted.append(loc)
        except Exception:
            pass


t = time.time()
ts = [threading.Thread(target=mint, daemon=True)
      for _ in range(a.mint_threads)]
[x.start() for x in ts]
[x.join() for x in ts]
print("minted %d tokens in %.1fs (%.1f mints/s with %d threads)"
      % (len(minted), time.time() - t,
         len(minted) / max(0.001, time.time() - t), a.mint_threads))
if REFUSED.is_set() or not minted:
    raise SystemExit("nothing to measure")

# ── 3 · download at each concurrency level ───────────────────────────────
print()
print("DOWNLOAD ONLY - own process, own sessions, nothing else running")
print("  %-8s %8s %9s %9s %8s %7s" %
      ("pullers", "docs/s", "MB/s", "Mb/s", "per-conn", "errs"))

results = []
for lvl in [int(x) for x in a.levels.split(",") if x.strip()]:
    work: queue.Queue = queue.Queue()
    # every level gets the SAME token list; tokens live 10 min
    for u in minted:
        work.put(u)
    got, byt, err, lk = [0], [0], [0], threading.Lock()

    def pull():
        # ⚠ one session per worker - what rc_pdf_pull.py did
        s = requests.Session()
        s.headers.update(HDRS)
        s.mount("https://", requests.adapters.HTTPAdapter(
            pool_connections=2, pool_maxsize=4, max_retries=0))
        while not REFUSED.is_set():
            try:
                loc = work.get_nowait()
            except queue.Empty:
                return
            try:
                r = s.get(loc, timeout=(10, 90), stream=True)
                if r.status_code in (401, 403, 429):
                    REFUSED.set()
                    return
                body = r.content
                if len(body) >= 5 and body[:4] == b"%PDF":
                    with lk:
                        got[0] += 1
                        byt[0] += len(body)
                else:
                    with lk:
                        err[0] += 1
            except Exception:
                with lk:
                    err[0] += 1

    t = time.time()
    th = [threading.Thread(target=pull, daemon=True) for _ in range(lvl)]
    [x.start() for x in th]
    [x.join() for x in th]
    el = max(0.001, time.time() - t)
    mbs = byt[0] / el / 1024 / 1024
    print("  %-8d %8.2f %9.1f %9.0f %8.2f %7d"
          % (lvl, got[0] / el, mbs, mbs * 8, mbs * 8 / lvl, err[0]))
    results.append((lvl, got[0] / el, mbs * 8, err[0]))
    if REFUSED.is_set():
        print("  ⚠ REFUSED - stopping the sweep, by rule")
        break

print()
if results:
    best = max(results, key=lambda r: r[1])
    print("BEST: %d pullers -> %.2f docs/s (%.0f Mb/s, %d errors)"
          % (best[0], best[1], best[2], best[3]))
    print()
    print("rc_lane currently measures ~2.4 docs/s at 16 pullers.")
    print("If this is far above that, the FETCH is fine and rc_lane's")
    print("structure is the defect. If it is similar, the lane is innocent")
    print("and the download path itself is what regressed.")
