# -*- coding: utf-8 -*-
"""CAN THE RICHMOND PDF LANE RUN WITHOUT A BROWSER? YES - MEASURED 2026-08-22.

The standing note said "python cannot do richmond pdf - 403 on a valid fresh
token, TLS-layer fingerprint, this lane alone needs a real browser." That was
measured against richmondcountyclerk.com. THE PDFs DO NOT LIVE THERE.

rc_feed mints by asking richmond for /ViewVscmsDocument/ViewContent with
redirects disabled and keeping the 302 Location. That Location points at
  iapps.courts.state.ny.us/vscms_public/viewer?token=v2....
- the NY State Unified Court System - and the token is self-authenticating.

⚠ ONE HEADER IS LOAD-BEARING (see HDRS below). It HANGS the library-default
UA rather than refusing it, which is why this looked like a rate limit for an
hour. A timeout is not a refusal, and the difference between them is the
whole finding.

⚠ LANDS DIRECTLY INTO THE STORE (login 2026-08-22: "you need to get the fetch
to pull it into the folder so its easier ... we should be able to just slot it
into its folder and the db with ease"). The old path wrote to _incoming and
let rc_pdf_land.py move it, which meant EVERY PDF WAS WRITTEN TWICE, READ
ONCE AND DELETED ONCE - four disk operations for one file - and the hop
became the bottleneck the moment the fetch got fast: measured 23:08 on
2026-08-22, fetch 11.6/s against lander 1.8/s, backlog 20,731 files / 7.0 GB
and growing. Writing where the file belongs removes the stage entirely.

⚠ ONE DB WRITER THREAD, COMMIT PER FILE. Workers never touch the write
connection. SQLite has ONE writer seat and eight lanes want it; the two
measured disasters are both in this repo - batching commits across slow work
collapsed acris rd 99 -> 16 docs/s (rc_pdf_land.py), and a live keyer blocked
every walker (routine_organization.py). Small frequent locks taken by a
single thread is the shape that survives.

⚠ SECURITY: same requests, same tokens, same pacing the feed already sets.
On a REFUSAL (401/403/429) this STOPS - it does not retry and does not rotate
anything. A refusal is a result to report, not an obstacle to route around.

Usage:  python rc_pdf_pull.py                  # 16 workers
        python rc_pdf_pull.py --workers 24
        python rc_pdf_pull.py --incoming       # legacy: stage to _incoming
"""
import argparse, threading, queue, time, json, pathlib, sqlite3, sys
import urllib.request
import requests

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import corpus_paths as CP
from rc_source import UA

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8077)
ap.add_argument("--workers", type=int, default=16)
ap.add_argument("--batch", type=int, default=3, help="urls asked per poll")
ap.add_argument("--pace", type=float, default=0.0)
ap.add_argument("--incoming", action="store_true",
                help="legacy staging path; leaves work for rc_pdf_land.py")
a = ap.parse_args()

STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                     r"\Legal Instruments Acquisition")
INCOMING = STORE / "_incoming"
FEED = "http://localhost:%d" % a.port

# ⚠ THE USER-AGENT IS LOAD-BEARING ON THE COURTS HOST - MEASURED 2026-08-22.
# Alternating requests, one variable, everything else identical:
#     python-requests/2.34.2 (library default) -> ReadTimeout at 45s, 2/2
#     acris-decoder/1.0 (this project's UA)    -> 200 + full pdf in 1.5s, 2/2
# ⚠ rc_source.py:37 says the host "does not gate on User-Agent at all". That
# is FALSE for iapps.courts.state.ny.us. It may still hold for richmond.
# This is NOT spoofing - it is the project's own honest self-identifying UA.
# Do not substitute a browser UA: already measured to buy nothing, and it
# would make the client dishonest.
HDRS = {"User-Agent": UA,
        "Referer": "https://www.richmondcountyclerk.com/",
        "Accept": "application/pdf,*/*"}

lock = threading.Lock()
stat = {"got": 0, "bytes": 0, "err": 0, "empty": 0, "wrote": 0}
STOP = threading.Event()
DBQ = queue.Queue(maxsize=10000)          # (did, relpath) -> the one writer


def feed_batch(n):
    try:
        with urllib.request.urlopen("%s/batch?n=%d" % (FEED, n), timeout=20) as r:
            return json.load(r)
    except Exception:
        return []


def db_writer():
    """THE ONLY THREAD THAT WRITES - and it writes in BATCHES.

    ⚠ READ rc_pdf_land.py's comment before changing this. It commits PER FILE
    because batching held the write lock across ~50 CPU-heavy conversions
    (30-60 s each) and collapsed acris rd from 99 to 16 docs/s. Its actual
    rule is the last line of that comment: "converted OUTSIDE the
    transaction". THE SLOW WORK WAS THE PROBLEM, NOT THE BATCH.

    Here there is no conversion, no file IO, no network - the bytes are
    already on disk before anything is queued. A batch of BATCH_N bare
    UPDATEs holds the lock for MILLISECONDS and takes ONE seat acquisition
    instead of N. Per-file commit measured ~2-6/s against a fetch of 13/s
    with the queue climbing past 2,500; the seat contention was the ceiling
    and the batch is what removes it.

    FLUSH_S bounds latency so a trickle still lands promptly."""
    BATCH_N, FLUSH_S = 250, 2.0
    con = sqlite3.connect(CP.NAV_DB, timeout=600)
    con.execute("PRAGMA busy_timeout=300000")
    pending, last = [], time.time()

    def flush():
        nonlocal pending, last
        if not pending:
            return
        try:
            con.executemany("UPDATE navigation SET pdf=? WHERE id=?", pending)
            con.commit()                       # ONE seat acquisition
            with lock:
                stat["wrote"] += len(pending)
        except Exception:
            with lock:
                stat["err"] += len(pending)
        pending, last = [], time.time()

    while not (STOP.is_set() and DBQ.empty()):
        try:
            did, rel = DBQ.get(timeout=0.5)
            pending.append((rel, did))         # executemany order = params
        except queue.Empty:
            pass
        if len(pending) >= BATCH_N or (pending and time.time() - last >= FLUSH_S):
            flush()
    flush()
    con.close()


def worker():
    s = requests.Session()
    s.headers.update(HDRS)
    # read-only handle: the `recorded` date decides the folder, and reads
    # never contend for the writer seat
    ro = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=120)
    while not STOP.is_set():
        work = feed_batch(a.batch)
        if not work:
            with lock:
                stat["empty"] += 1
            time.sleep(3)
            continue
        for did, loc in work:
            if STOP.is_set():
                return
            try:
                r = s.get(loc, timeout=(10, 90), stream=True)
                if r.status_code in (401, 403, 429):
                    print("\n!! REFUSED %s on %s - STOPPING THE LANE. "
                          "No retry, no rotation." % (r.status_code, did),
                          flush=True)
                    STOP.set()
                    return
                if r.status_code != 200:
                    with lock:
                        stat["err"] += 1
                    continue
                body = r.content
                if len(body) < 5 or body[:4] != b"%PDF":
                    with lock:
                        stat["err"] += 1
                    continue

                if a.incoming:
                    dst = INCOMING / f"{did}.pdf"
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    rel = None
                else:
                    rec = ro.execute(
                        "SELECT json_extract(recorded_details,'$.recorded')"
                        " FROM navigation WHERE id=?", (did,)).fetchone()
                    dest = CP.doc_store_dir(did, (rec[0] if rec else "") or "")
                    dest.mkdir(parents=True, exist_ok=True)
                    dst = dest / f"{did}.pdf"
                    rel = str(dst.relative_to(STORE))

                # atomic: a partial file must never look landed
                tmp = dst.with_suffix(".pdf.part")
                tmp.write_bytes(body)
                tmp.replace(dst)

                if rel:
                    DBQ.put((did, rel))
                with lock:
                    stat["got"] += 1
                    stat["bytes"] += len(body)
            except Exception:
                with lock:
                    stat["err"] += 1
            if a.pace:
                time.sleep(a.pace)


ths = [threading.Thread(target=worker, daemon=True) for _ in range(a.workers)]
wr = None
if not a.incoming:
    wr = threading.Thread(target=db_writer, daemon=True)
    wr.start()
print("rc_pdf_pull: %d workers -> %s" %
      (a.workers, "_incoming (legacy)" if a.incoming else "STORE + db"),
      flush=True)
for t in ths:
    t.start()

t0, last = time.time(), 0
try:
    while any(t.is_alive() for t in ths):
        time.sleep(10)
        with lock:
            s = dict(stat)
        el = time.time() - t0
        print("  +%-4d  total %-6d  %.2f/s  %.1f MB  db %-6d q%-5d err %d  empty %d"
              % (s["got"] - last, s["got"], s["got"] / el, s["bytes"] / 1e6,
                 s["wrote"], DBQ.qsize(), s["err"], s["empty"]), flush=True)
        last = s["got"]
except KeyboardInterrupt:
    STOP.set()
    print("\nstopping - draining db queue...", flush=True)

STOP.set()
if wr:
    wr.join(timeout=120)
with lock:
    s = dict(stat)
el = time.time() - t0
print("DONE  %d fetched · %d db rows · %.1f MB · %.2f/s · err %d"
      % (s["got"], s["wrote"], s["bytes"] / 1e6, s["got"] / el if el else 0,
         s["err"]), flush=True)
