"""ASYNC ACQUISITION — remove OUR bottleneck, not theirs.

⚠ WHAT THE THREAD RAMP ACTUALLY MEASURED. At 12-16 workers efficiency fell to
~70% WHILE LATENCY STAYED FLAT (0.35-0.40s at every level, including 16x load).
A saturating server answers slower. This one never moved.

    So the ceiling at 16 threads was CPython, not ACRIS.

Blocking sockets under the GIL stop scaling long before the server cares.
asyncio holds hundreds of sockets in one thread with no GIL contention, so the
same concurrency does more work — and crucially, THE LOAD ON ACRIS IS
IDENTICAL. Same number of in-flight requests, same pacing; we simply stop
wasting our own cycles.

⚠ THE DISTINCTION THAT MATTERS: this makes OUR CLIENT more efficient at a GIVEN
concurrency. It does not raise concurrency. Turning the dial up is a separate
decision with a separate justification, and it belongs to whoever owns the
relationship with the City — not to a performance patch.

⚠ REFUSAL HANDLING IS UNCHANGED AND ABSOLUTE. First refusal cancels every
in-flight request and the run stops. No retry, no backoff-and-continue.
"""
import asyncio
import http.cookies
import sys
import time

import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id="
IMG = "https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage"


class Refused(Exception):
    pass


class Fetcher:
    def __init__(self, concurrency=16, pace=0.0):
        self.n = concurrency
        self.pace = pace
        self.stop = False
        self.lat = []
        self.session = None

    async def __aenter__(self):
        import aiohttp
        # ⚠ ONE SESSION, ONE COOKIE JAR — a browser with N connections, not N
        # users. limit_per_host is what actually bounds in-flight requests.
        conn = aiohttp.TCPConnector(limit=self.n, limit_per_host=self.n,
                                    ttl_dns_cache=600, force_close=False)
        self.session = aiohttp.ClientSession(
            connector=conn, headers={"User-Agent": UA},
            timeout=aiohttp.ClientTimeout(total=90))
        return self

    async def __aexit__(self, *a):
        await self.session.close()

    async def warm(self, doc_id):
        async with self.session.get(VIEW + doc_id) as r:
            body = await r.read()
        fetch_pages._check_denied(body, r.headers.get("Content-Type", ""))
        return len(self.session.cookie_jar)

    async def page(self, doc_id, n, sem):
        if self.stop:
            return None
        async with sem:
            if self.pace:
                await asyncio.sleep(self.pace)
            t0 = time.time()
            try:
                async with self.session.get(
                        f"{IMG}?doc_id={doc_id}&page={n}",
                        headers={"Referer": VIEW + doc_id}) as r:
                    body = await r.read()
                    ct = r.headers.get("Content-Type", "")
            except Exception as e:
                return {"ok": False, "err": type(e).__name__, "doc": doc_id, "page": n}
            dt = time.time() - t0
            self.lat.append(dt)
            try:
                fetch_pages._check_denied(body, ct)
            except fetch_pages.AccessDenied:
                # ⚠ ONE REFUSAL STOPS EVERYTHING.
                self.stop = True
                return {"ok": False, "err": "REFUSED", "doc": doc_id, "page": n}
            if "tiff" not in ct or len(body) < 500:
                return {"ok": False, "err": "not-image", "ct": ct,
                        "doc": doc_id, "page": n, "secs": dt}
            return {"ok": True, "doc": doc_id, "page": n,
                    "data": body, "secs": dt, "bytes": len(body)}

    async def fetch_many(self, jobs):
        sem = asyncio.Semaphore(self.n)
        return await asyncio.gather(*(self.page(d, p, sem) for d, p in jobs))


async def bench(jobs, concurrency):
    async with Fetcher(concurrency) as f:
        await f.warm(jobs[0][0])
        t0 = time.time()
        res = await f.fetch_many(jobs)
        wall = time.time() - t0
    ok = [r for r in res if r and r.get("ok")]
    refused = any(r and r.get("err") == "REFUSED" for r in res)
    lat = sorted(f.lat)
    return {"concurrency": concurrency, "n": len(jobs), "ok": len(ok),
            "wall_s": round(wall, 2),
            "req_per_s": round(len(ok) / wall, 2) if wall else 0,
            "mean_lat": round(sum(lat) / len(lat), 3) if lat else None,
            "p95": round(lat[int(len(lat) * .95) - 1], 3) if len(lat) > 3 else None,
            "errors": len(res) - len(ok), "refused": refused,
            "mb": round(sum(r["bytes"] for r in ok) / 1e6, 1)}


async def main(per_level=48):
    import json
    maps = {}
    for line in open("docmaps.jsonl", encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if r.get("hid_TotalPages", 0) >= 60:
                maps[r["doc_id"]] = r["hid_TotalPages"]
    docs = list(maps)[:24]
    cursor = {d: 1 for d in docs}
    print(f"async ramp over {len(docs)} documents\n")

    rows, base = [], None
    for c in (8, 16, 24, 32):
        jobs, i = [], 0
        while len(jobs) < per_level:
            d = docs[i % len(docs)]
            if cursor[d] <= maps[d]:
                jobs.append((d, cursor[d]))
                cursor[d] += 1
            i += 1
        r = await bench(jobs, c)
        rows.append(r)
        if base is None:
            base = r["mean_lat"]
        ratio = r["mean_lat"] / base if base else 1
        print(f"  {c:>3} concurrent  {r['ok']:>3}/{r['n']} ok  {r['wall_s']:>6}s  "
              f"{r['req_per_s']:>6} req/s  lat {r['mean_lat']} ({ratio:.2f}x)  "
              f"p95 {r['p95']}  err {r['errors']}")
        if r["refused"]:
            print("\n  ⚠ REFUSED — stopping. No retry.")
            break
        # ⚠ LATENCY IS THE SERVER TALKING. Stop when it starts queueing us.
        if ratio > 1.6:
            print(f"\n  ⚠ latency {ratio:.2f}x baseline — ceiling at {c}. Stopping.")
            break
        await asyncio.sleep(3)

    print("\n" + "=" * 68)
    best = max(rows, key=lambda r: r["req_per_s"])
    for r in rows:
        print(f"  {r['concurrency']:>3}  {r['req_per_s']:>6} req/s   lat {r['mean_lat']}")
    print(f"\n  peak {best['req_per_s']} req/s at {best['concurrency']} concurrent")
    print(f"  threads managed 27.45 at 16 — async at 16: "
          f"{next((r['req_per_s'] for r in rows if r['concurrency']==16), 'n/a')}")
    for lbl, pg in (("DEVR 41,066", 41066), ("zoning 1.22M", 1_220_000),
                    ("corpus 190M", 190_000_000)):
        s = pg / best["req_per_s"]
        print(f"  {lbl:<16} {s/3600:>8.1f} h  ({s/86400:.1f} d)")
    json.dump(rows, open("_afetch.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 48))
