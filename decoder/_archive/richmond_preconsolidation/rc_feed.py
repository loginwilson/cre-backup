"""THE RC PDF FEED - makes the browser lane fully autonomous (login,
2026-08-20: "use the url endpoint and save process as an encoded one shot").

Mints viewer tokens continuously (6 concurrent clerk sessions) into an
internal queue and serves them over localhost HTTP. The Chrome consumer
loop polls GET /batch?n=25 and downloads each - so after ONE injection the
lane runs itself: feed mints ahead, Chrome fetches and saves to _incoming,
rc_pdf_land converts and lands. No manual batches ever again.

localhost is a trustworthy origin, so the https viewer page may fetch it;
CORS is opened for exactly that. The feed touches ONLY richmondcountyclerk
(minting) - the image host is Chrome's alone.

Usage:  python rc_feed.py [--port 8077] [--ahead 300]
"""
import argparse
import json
import pathlib
import queue
import re
import sqlite3
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP
import rc_source as RC
import rc_sync as RS

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8077)
ap.add_argument("--ahead", type=int, default=300,
                help="minted urls to keep ready ahead of the browser")
ap.add_argument("--miners", type=int, default=6)
a = ap.parse_args()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


ready = queue.Queue()
tl = threading.local()
lock = threading.Lock()
stats = {"minted": 0, "served": 0, "skipped": 0, "stale": 0}
TOKEN_TTL = 600   # ⚠ viewer tokens EXPIRE. Overnight 2026-08-22 the
                  # consumer stalled (hidden tab) while the feed kept its
                  # buffer full - by morning all 786 ready tokens were
                  # hours dead and even "fresh" polls served corpses. A
                  # token older than TTL is discarded at serve time and
                  # its id released to re-mint.
served_ids = set()          # never hand the same doc out twice in one run


grab_lock = threading.Lock()     # guards next_ids + served_ids as ONE unit
                                 # (a nested take of the non-reentrant stats
                                 # lock deadlocked v1 at startup)


INCOMING = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                        r"\Legal Instruments Acquisition\_incoming")


def next_ids(n):
    """next RC docs needing a pdf, skipping ones already handed out.
    Caller holds grab_lock. ⚠ Also skips ids whose RAW download already
    sits in _incoming unconverted - a feed restart forgets served_ids and
    re-served 2,300+ backlog ids, so Chrome re-downloaded them all as
    "RC_x (1).pdf" dups (2026-08-21). The download IS the evidence."""
    have_raw = {re.sub(r" \(\d+\)$", "", p.stem)
                for p in INCOMING.glob("RC_*.pdf")} if INCOMING.exists() \
        else set()
    con = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=120)
    con.execute("PRAGMA busy_timeout=60000")
    # ⚠ BOUND THE ID RANGE. RC_ ids sort AFTER every acris id, so an
    # unbounded scan walks 21M acris rows (evaluating json_extract on the
    # way) before reaching the first Richmond row - measured 2026-08-22:
    # minting fell to 0.83/s while the browser consumed 2.7/s, starving
    # the lane. `id > 'RC'` starts the index seek at the Richmond block.
    rows = con.execute(
        "SELECT id FROM navigation WHERE id > 'RC' AND id LIKE 'RC_%'"
        " AND recorded_details != '' AND pdf = ''"
        " AND json_extract(recorded_details, '$.image_state') = 'present'"
        " ORDER BY id LIMIT ?",
        (n + len(served_ids) + len(have_raw),)).fetchall()
    con.close()
    return [r[0] for r in rows
            if r[0] not in served_ids and r[0] not in have_raw][:n]


def miner():
    while True:
      try:                          # ⚠ a miner must NEVER die - a bare
        if ready.qsize() >= a.ahead:  # exception here silently killed all 6
            time.sleep(5)             # threads at startup, minted stuck at 0
            continue
        with grab_lock:
            try:
                grab = next_ids(20)
            except Exception:
                grab = []
            served_ids.update(grab)
        if not grab:
            time.sleep(15)
            continue
        for did in grab:
            iid = did[3:]
            try:
                if not hasattr(tl, "op"):
                    w = RS.Window("08/17/2026", "08/17/2026")
                    tl.op = urllib.request.build_opener(
                        urllib.request.HTTPCookieProcessor(w.s.jar),
                        _NoRedirect())
                    tl.op.addheaders = [("User-Agent", RC.UA)]
                time.sleep(RC.PACE)
                req = urllib.request.Request(
                    RC.BASE + "/ViewVscmsDocument/ViewContent"
                    f"?p_endorsementId={iid}")
                req.add_header("Referer",
                               RC.BASE + f"/Search/ViewDocumentInfo/{iid}")
                loc = None
                try:
                    with tl.op.open(req, timeout=60):
                        pass
                except urllib.error.HTTPError as e:
                    loc = (e.headers.get("Location")
                           if e.code in (301, 302, 303) else None)
                if loc:
                    ready.put([did, loc, time.time()])
                    with lock:
                        stats["minted"] += 1
                else:
                    with lock:
                        stats["skipped"] += 1
            except Exception:
                with lock:
                    stats["skipped"] += 1
      except Exception:
        time.sleep(5)               # outer guard: keep the miner alive


class H(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ⚠ BATCH SIZE IS THE BROWSER'S CONCURRENCY - CAP IT HERE, NOT IN THE
    # PAGE. The worker fires every url in a batch at once, so serving 25+
    # meant ~99 downloads in flight: each got 1/99th of the per-IP grant
    # (~2 doc/s total, the wall - nothing finished for ~45 s, then a wave
    # completed together (the login's "backs up, freezes, then jumps
    # massively and clears"). Worse, EDGE SPAWNS ONE quarantine.mojom
    # SCANNER PROCESS PER IN-FLIGHT DOWNLOAD: measured 2026-08-22, 254 of
    # them holding 6.13 GB - the very RAM that blocked adding an acris pdf
    # lane. Serving 10 keeps throughput at the wall (10 is ~5 s of work at
    # 2/s) while the scanner fleet and the wave pattern both collapse.
    # Server-side because the feed restarts cheaply; the browser loop
    # doesn't.
    MAX_SERVE = 10
    # ⚠ THE BATCH CAP DID NOT CAP CONCURRENCY (measured 2026-08-22, hours
    # after it shipped): the worker polls again while its downloads are
    # still running, so 10-per-poll compounded into 708 files in flight -
    # SEVEN TIMES worse than the 99 the cap was written to fix. The unit
    # that needs capping is OUTSTANDING work, and the browser cannot know
    # it - but the DISK can: every in-flight download is a .crdownload/.tmp
    # in _incoming. Serve nothing while that count is high; the worker
    # keeps polling and gets work the moment the queue drains. Poll-rate
    # independent, browser-code untouched.
    # ⚠ RAISED 15 -> 200 on 2026-08-22 when the lane went pure-python.
    # The 15 existed because the BROWSER could not know its own outstanding
    # work (10-per-poll compounded into 708 files in flight). rc_pdf_pull.py
    # bounds concurrency with --workers, so the disk-polling proxy is no
    # longer the only brake - and at 16 workers it WAS the brake: measured
    # 12.77/s with `ready` draining 476->23 and empty-polls climbing, i.e.
    # we were measuring our own gate, not the courts host.
    # Keep it well above --workers; it is now a runaway backstop, not a pacer.
    MAX_IN_FLIGHT = 200

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/batch":
            n = int(parse_qs(u.query).get("n", ["25"])[0])
            out = []
            try:
                inflight = sum(1 for p in INCOMING.iterdir()
                               if p.suffix.lower() in (".crdownload", ".tmp")) \
                    if INCOMING.exists() else 0
            except OSError:
                inflight = 0
            try:
                while inflight < self.MAX_IN_FLIGHT \
                        and len(out) < min(n, self.MAX_SERVE):
                    did, loc, born = ready.get_nowait()
                    if time.time() - born > TOKEN_TTL:
                        with lock:
                            stats["stale"] += 1
                        with grab_lock:
                            served_ids.discard(did)   # re-mint later
                        continue
                    out.append([did, loc])
            except queue.Empty:
                pass
            with lock:
                stats["served"] += len(out)
            self._send(out)
        elif u.path == "/stats":
            with lock:
                s = dict(stats)
            s["ready"] = ready.qsize()
            self._send(s)
        else:
            self._send({"err": "unknown"}, 404)


for _ in range(a.miners):
    threading.Thread(target=miner, daemon=True).start()


def reporter():
    while True:
        time.sleep(60)
        with lock:
            s = dict(stats)
        print(f"  FEED minted {s['minted']:,} · served {s['served']:,} · "
              f"ready {ready.qsize()} · skipped {s['skipped']}", flush=True)


threading.Thread(target=reporter, daemon=True).start()
print(f"rc feed on http://localhost:{a.port} · {a.miners} miners · "
      f"keeps {a.ahead} ahead", flush=True)
ThreadingHTTPServer(("127.0.0.1", a.port), H).serve_forever()
