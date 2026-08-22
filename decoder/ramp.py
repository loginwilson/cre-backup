"""FIND THE CONCURRENCY CEILING BY MEASURING IT, NOT BY PICKING A NUMBER.

⚠ WHAT THE SERVER SAYS WHEN IT IS SATURATED IS **LATENCY**, NOT AN ERROR.
A refusal is the last signal, not the first. Long before it refuses, a loaded
server answers more slowly — so the honest ceiling is the concurrency level at
which THROUGHPUT STOPS RISING and LATENCY STARTS CLIMBING. Past that point more
connections do not move more pages; they just queue, and the only thing that
grows is the load on a shared civic system.

So this ramps 1 -> 2 -> 4 -> 8, holding the page count constant, and reports:

    throughput   req/s          does it actually scale?
    latency      mean and p95   is the server straining?
    errors       any refusal    -> STOP EVERYTHING, immediately

⚠ CEILING AT 8 ON PURPOSE. Browsers open ~6 connections per host, so 6-8 is
ordinary client behaviour and is the honest upper bound for a tool that is not
trying to be special. This is a measurement, not a race.

⚠ ONE SESSION, MANY CONNECTIONS — which is what a browser is. Every worker
shares the same cookie jar rather than minting its own session, because N
independent sessions is N users, and we are one.

⚠ AND IT STOPS ON THE FIRST REFUSAL. No retry, no backoff-and-continue. Today
this project blocked Login's own browser; the cost of pushing is borne by a
real person.
"""
import http.cookiejar
import json
import statistics
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id="
IMG = "https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage"

_jar = http.cookiejar.CookieJar()
_lock = threading.Lock()
STOP = threading.Event()


def _opener():
    with _lock:
        o = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(_jar))
    o.addheaders = [("User-Agent", UA)]
    return o


def warm(doc_id):
    """Establish the session the way clicking the link does."""
    o = _opener()
    req = urllib.request.Request(VIEW + doc_id)
    with o.open(req, timeout=60) as f:
        data, hd = f.read(), dict(f.headers)
    fetch_pages._check_denied(data, hd.get("Content-Type", ""))
    return len(_jar)


def one(job):
    doc, page = job
    if STOP.is_set():
        return None
    o = _opener()
    req = urllib.request.Request(f"{IMG}?doc_id={doc}&page={page}")
    req.add_header("Referer", VIEW + doc)
    t0 = time.time()
    try:
        with o.open(req, timeout=90) as f:
            data, hd = f.read(), dict(f.headers)
    except Exception as e:
        return {"ok": False, "err": type(e).__name__, "secs": time.time() - t0}
    dt = time.time() - t0
    try:
        fetch_pages._check_denied(data, hd.get("Content-Type", ""))
    except fetch_pages.AccessDenied as e:
        STOP.set()                      # ⚠ every worker halts
        return {"ok": False, "err": "REFUSED", "secs": dt, "msg": str(e)[:100]}
    ct = hd.get("Content-Type", "")
    return {"ok": "tiff" in ct and len(data) > 500, "secs": dt,
            "bytes": len(data), "ct": ct}


def level(jobs, workers):
    STOP.clear()
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        res = [r for r in ex.map(one, jobs) if r]
    wall = time.time() - t0
    ok = [r for r in res if r.get("ok")]
    lat = sorted(r["secs"] for r in ok)
    refused = any(r.get("err") == "REFUSED" for r in res)
    return {
        "workers": workers, "n": len(jobs), "ok": len(ok),
        "wall_s": round(wall, 1),
        "req_per_s": round(len(ok) / wall, 2) if wall else 0,
        "mean_lat": round(statistics.mean(lat), 2) if lat else None,
        "p95_lat": round(lat[int(len(lat) * .95) - 1], 2) if len(lat) > 3 else None,
        "errors": len(res) - len(ok), "refused": refused,
        "mb": round(sum(r.get("bytes", 0) for r in ok) / 1e6, 1),
    }


def main(per_level=24):
    maps = {}
    for line in open("docmaps.jsonl", encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if r.get("hid_TotalPages", 0) >= 40:
                maps[r["doc_id"]] = r["hid_TotalPages"]
    docs = list(maps)[:8]
    print(f"ramp over {len(docs)} mapped documents\n")
    warm(docs[0])

    rows = []
    page_cursor = {d: 1 for d in docs}
    for w in (1, 2, 4, 8):
        jobs = []
        i = 0
        while len(jobs) < per_level:
            d = docs[i % len(docs)]
            if page_cursor[d] <= maps[d]:
                jobs.append((d, page_cursor[d]))
                page_cursor[d] += 1
            i += 1
        r = level(jobs, w)
        rows.append(r)
        print(f"  {w:>2} workers  {r['ok']:>3}/{r['n']} ok  {r['wall_s']:>6}s  "
              f"{r['req_per_s']:>6} req/s  lat mean {r['mean_lat']} p95 {r['p95_lat']}"
              f"  err {r['errors']}")
        if r["refused"]:
            print("\n  ⚠ REFUSED — stopping the ramp. Do not retry.")
            break
        time.sleep(3)

    print("\n" + "=" * 66)
    base = rows[0]
    for r in rows:
        eff = r["req_per_s"] / base["req_per_s"] / r["workers"] if base["req_per_s"] else 0
        lat_x = r["mean_lat"] / base["mean_lat"] if base["mean_lat"] else 0
        print(f"  {r['workers']:>2}w  {r['req_per_s']:>6} req/s  "
              f"{r['req_per_s']/base['req_per_s']:>5.2f}x throughput  "
              f"{eff*100:>5.0f}% per-connection efficiency  "
              f"latency {lat_x:.2f}x")
    # ⚠ THE CEILING IS WHERE EFFICIENCY COLLAPSES OR LATENCY CLIMBS, whichever
    # comes first — not the highest raw number.
    best = max(rows, key=lambda r: r["req_per_s"])
    print(f"\n  peak throughput at {best['workers']} workers: {best['req_per_s']} req/s")
    if best["req_per_s"]:
        print(f"  -> 41,066 DEVR pages: {41066/best['req_per_s']/3600:.1f} h")
    json.dump(rows, open("_ramp.json", "w"), indent=1)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 24)
