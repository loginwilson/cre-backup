"""RE-TEST CONCURRENCY ON A FAST LINK — every prior ceiling was measured saturated.

⚠ WHY EVERY EARLIER CEILING IS SUSPECT. The concurrency limits this project
settled on — 128 connections for maps, 192 "degrading" at 2.82x latency, images
plateauing at 37 Mbps — were ALL measured on a link delivering ~28-30 Mbps,
which the traffic was fully saturating. A saturated pipe produces exactly the
signature we read as a server ceiling: throughput flat, latency climbing.

A speed test now reports 112.85 Mbps with a 13 ms NYC exit, while the mapper
draws 30.3. That is 27% utilisation. So the ceilings may have been the pipe all
along, and the server's real limit is unknown.

⚠ THE STOPPING RULE IS UNCHANGED AND STILL LATENCY. More connections are only
worth having if they move more BYTES. If latency climbs while bytes stay flat,
that is queueing — on the server, this time genuinely — and the answer is to
back off, not to push.

⚠ MEASURED ON THE MAP ENDPOINT, the light path. Asking a structural question
should not cost the heavy image endpoint anything.
"""
import asyncio
import json
import pathlib
import statistics
import sys
import time

import amap
import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LINK_MBPS = 112.85          # measured by speed test, VPN on


async def level(ids, conc):
    import aiohttp
    lat, ok, nbytes = [], 0, 0
    sem = asyncio.Semaphore(conc)
    stop = asyncio.Event()
    conn = aiohttp.TCPConnector(limit=conc, limit_per_host=conc)
    async with aiohttp.ClientSession(connector=conn,
                                     headers={"User-Agent": amap.UA},
                                     timeout=aiohttp.ClientTimeout(total=60)) as s:
        # ⚠ PRIME THE POOL OUTSIDE THE CLOCK. Cold connections are what made
        # every earlier ramp read low and produced a false "ceiling at 16".
        async def fetch(d, timed):
            nonlocal ok, nbytes
            if stop.is_set():
                return
            async with sem:
                t = time.time()
                try:
                    async with s.get(amap.VIEW + d) as r:
                        body = await r.read()
                        ct = r.headers.get("Content-Type", "")
                except Exception:
                    return
                dt = time.time() - t
                try:
                    fetch_pages._check_denied(body, ct)
                except fetch_pages.AccessDenied:
                    stop.set()
                    print("    REFUSED — stopping.")
                    return
                if timed:
                    lat.append(dt)
                    ok += 1
                    nbytes += len(body)

        await asyncio.gather(*(fetch(d, False) for d in ids[:conc]))
        body = ids[conc:conc + conc * 8]
        t0 = time.time()
        await asyncio.gather(*(fetch(d, True) for d in body))
        wall = time.time() - t0
    if not ok:
        return None
    mbps = nbytes * 8 / 1e6 / wall
    return {"conc": conc, "ok": ok, "req_per_s": round(ok / wall, 1),
            "mbps": round(mbps, 1),
            "pct_link": round(100 * mbps / LINK_MBPS),
            "lat": round(statistics.mean(lat), 3)}


async def main():
    # ids not yet mapped, so nothing is wasted
    done = set()
    with open("acris_maps.jsonl", encoding="utf-8") as f:
        for l in f:
            if l.strip():
                done.add(json.loads(l)["doc_id"])
    pool = []
    with open("acris_ids.jsonl", encoding="utf-8") as f:
        for l in f:
            if not l.strip():
                continue
            d = json.loads(l)["document_id"]
            if d not in done:
                pool.append(d)
            if len(pool) >= 20000:
                break
    print(f"{len(pool):,} unmapped ids · link {LINK_MBPS} Mbps\n")
    print(f"{'conc':>6}{'maps/s':>9}{'Mbps':>8}{'% link':>8}{'latency':>10}")
    rows, cur, base = [], 0, None
    for c in (128, 192, 256, 384, 512):
        chunk = pool[cur:cur + c * 9]
        cur += len(chunk)
        if len(chunk) < c * 2:
            break
        r = await level(chunk, c)
        if not r:
            break
        rows.append(r)
        if base is None:
            base = r["lat"]
        ratio = r["lat"] / base
        print(f"{c:>6}{r['req_per_s']:>9}{r['mbps']:>8}{r['pct_link']:>7}%"
              f"{r['lat']:>9} ({ratio:.2f}x)")
        # ⚠ bytes flat + latency climbing = queueing. Stop.
        if len(rows) > 1 and ratio > 2.0 and r["mbps"] < rows[-2]["mbps"] * 1.1:
            print(f"\n  latency {ratio:.2f}x with no byte gain — ceiling at {c}")
            break
        await asyncio.sleep(2)

    print(f"\n{'='*56}")
    best = max(rows, key=lambda r: r["mbps"])
    print(f"  best {best['conc']} conc · {best['req_per_s']} maps/s · "
          f"{best['mbps']} Mbps ({best['pct_link']}% of link)")
    rem = 17021446 - len(done)
    print(f"  {rem:,} remaining -> {rem/best['req_per_s']/3600:.1f} h")
    if best["pct_link"] < 50:
        print("\n  ⚠ still under half the link. The limit is ACRIS or the path,\n"
              "    not your connection — more bandwidth will not help.")
    json.dump(rows, open("_conc_retest.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
