"""PUSH FOR 100% — by fixing OUR client first, then ramping until THEY object.

⚠ THE MISSING EFFICIENCY WAS OURS. ramp.py built a fresh urllib opener on every
single request — object construction, and a new TCP/TLS handshake, 24 times per
level. That is pure client-side waste and it shows up as "the server didn't
scale". Here each worker THREAD builds one opener and reuses it, so connections
stay alive across requests. Any gain from this costs ACRIS nothing at all — it
is strictly less work for them.

⚠ AND THE HONEST WAY TO FIND A CEILING IS TO LET THE SERVER SET IT. The signal
is LATENCY, not errors. This aborts the moment mean latency rises meaningfully
above the single-stream baseline, because that is the server saying "I am
queueing you now" — long before it would ever refuse.

⚠ WHERE THIS STOPS AND WHY. It ramps to 16 and no further. 6-8 connections is
ordinary browser behaviour; 16 is an aggressive-but-real client. Past that it
stops being a measurement of what we need and becomes load-testing somebody
else's production system — and the value is ZERO, because at 8 workers
acquisition is already ~50x faster than extraction. There is nothing on the
other side of that door worth having.
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

LAT_ABORT = 1.6          # abort if mean latency exceeds 1.6x the baseline
_jar = http.cookiejar.CookieJar()
_tl = threading.local()
STOP = threading.Event()


def opener():
    """⚠ ONE PER THREAD, REUSED. This is the whole fix — keep-alive works only
    if the opener survives between requests."""
    o = getattr(_tl, "op", None)
    if o is None:
        o = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(_jar))
        o.addheaders = [("User-Agent", UA), ("Connection", "keep-alive")]
        _tl.op = o
    return o


def warm(doc_id):
    o = opener()
    with o.open(urllib.request.Request(VIEW + doc_id), timeout=60) as f:
        data, hd = f.read(), dict(f.headers)
    fetch_pages._check_denied(data, hd.get("Content-Type", ""))
    return len(_jar)


def one(job):
    doc, page = job
    if STOP.is_set():
        return None
    req = urllib.request.Request(f"{IMG}?doc_id={doc}&page={page}")
    req.add_header("Referer", VIEW + doc)
    t0 = time.time()
    try:
        with opener().open(req, timeout=90) as f:
            data, hd = f.read(), dict(f.headers)
    except Exception as e:
        return {"ok": False, "err": type(e).__name__, "secs": time.time() - t0}
    dt = time.time() - t0
    try:
        fetch_pages._check_denied(data, hd.get("Content-Type", ""))
    except fetch_pages.AccessDenied:
        STOP.set()
        return {"ok": False, "err": "REFUSED", "secs": dt}
    return {"ok": "tiff" in hd.get("Content-Type", "") and len(data) > 500,
            "secs": dt, "bytes": len(data)}


def level(jobs, workers):
    STOP.clear()
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        res = [r for r in ex.map(one, jobs) if r]
    wall = time.time() - t0
    ok = [r for r in res if r.get("ok")]
    lat = sorted(r["secs"] for r in ok)
    return {"workers": workers, "n": len(jobs), "ok": len(ok),
            "wall_s": round(wall, 2),
            "req_per_s": round(len(ok) / wall, 2) if wall else 0,
            "mean_lat": round(statistics.mean(lat), 3) if lat else None,
            "p95": round(lat[int(len(lat) * .95) - 1], 3) if len(lat) > 3 else None,
            "errors": len(res) - len(ok),
            "refused": any(r.get("err") == "REFUSED" for r in res),
            "mb": round(sum(r.get("bytes", 0) for r in ok) / 1e6, 1)}


def main(per_level=32):
    maps = {}
    for line in open("docmaps.jsonl", encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if r.get("hid_TotalPages", 0) >= 60:
                maps[r["doc_id"]] = r["hid_TotalPages"]
    docs = list(maps)[:16]
    print(f"ramp2 over {len(docs)} documents, keep-alive openers\n")
    warm(docs[0])

    cursor = {d: 1 for d in docs}
    rows, base_lat = [], None
    for w in (1, 4, 8, 12, 16):
        jobs, i = [], 0
        while len(jobs) < per_level:
            d = docs[i % len(docs)]
            if cursor[d] <= maps[d]:
                jobs.append((d, cursor[d]))
                cursor[d] += 1
            i += 1
        r = level(jobs, w)
        rows.append(r)
        if base_lat is None:
            base_lat = r["mean_lat"]
        ratio = r["mean_lat"] / base_lat if base_lat else 1
        print(f"  {w:>2}w  {r['ok']:>3}/{r['n']} ok  {r['wall_s']:>6}s  "
              f"{r['req_per_s']:>6} req/s  lat {r['mean_lat']} "
              f"({ratio:.2f}x base)  p95 {r['p95']}  err {r['errors']}")
        if r["refused"]:
            print("\n  ⚠ REFUSED — stopping. No retry.")
            break
        if ratio > LAT_ABORT:
            print(f"\n  ⚠ LATENCY {ratio:.2f}x BASELINE — the server is queueing us. "
                  f"CEILING FOUND at {w} workers. Stopping.")
            break
        time.sleep(3)

    print("\n" + "=" * 70)
    b = rows[0]
    for r in rows:
        ideal = b["req_per_s"] * r["workers"]
        print(f"  {r['workers']:>2}w  {r['req_per_s']:>6} req/s   "
              f"ideal {ideal:>6.1f}   efficiency {100*r['req_per_s']/ideal:>5.0f}%   "
              f"lat {r['mean_lat']}")
    best = max(rows, key=lambda r: r["req_per_s"])
    print(f"\n  peak {best['req_per_s']} req/s at {best['workers']} workers")
    print(f"  -> 41,066 DEVR pages : {41066/best['req_per_s']/60:.0f} min")
    print(f"  -> 190M corpus pages : {190e6/best['req_per_s']/86400:.0f} days")
    json.dump(rows, open("_ramp2.json", "w"), indent=1)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 32)
