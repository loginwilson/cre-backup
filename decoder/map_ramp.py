"""HOW FAST CAN MAPPING GO? The cheap endpoint deserves its own ceiling test.

⚠ THE IMAGE CEILING DOES NOT APPLY HERE, AND ASSUMING IT DID WOULD BE THE SAME
MISTAKE AS THE 6-SECOND PAUSE. GetImage tops out near 28 req/s because pulling
a scan off a document store is heavy work. DocumentImageView is a 13 KB HTML
render — a completely different cost — and it has already been observed at
199 req/s in the same session, with the same cookie jar, that images cap at 28.

That single fact also settles the "is it a rate cap on us" question: if any
per-session or per-client request cap existed, mapping could not run 7x faster
than fetching through the same session. There is no cap. There are two
endpoints with different speeds.

So this ramps 8 -> 24 and lets LATENCY name the ceiling, exactly as the image
ramp did. Same rule: stop when the server starts queueing, not when it refuses.
"""
import asyncio
import json
import statistics
import sys
import time

import amap
import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LAT_ABORT = 1.6


async def level(ids, conc):
    import aiohttp
    lat, ok, err, refused = [], 0, 0, False
    sem = asyncio.Semaphore(conc)
    conn = aiohttp.TCPConnector(limit=conc, limit_per_host=conc)
    t0 = time.time()
    async with aiohttp.ClientSession(
            connector=conn, headers={"User-Agent": amap.UA},
            timeout=aiohttp.ClientTimeout(total=60)) as s:
        async def one(d):
            nonlocal ok, err, refused
            async with sem:
                t = time.time()
                try:
                    async with s.get(amap.VIEW + d) as r:
                        body = await r.read()
                        ct = r.headers.get("Content-Type", "")
                except Exception:
                    err += 1
                    return
                lat.append(time.time() - t)
                try:
                    fetch_pages._check_denied(body, ct)
                except fetch_pages.AccessDenied:
                    refused = True
                    return
                m = amap.parse(body.decode("utf-8", "ignore"), d)
                if m["hid_TotalPages"]:
                    ok += 1
                else:
                    err += 1
        await asyncio.gather(*(one(d) for d in ids))
    wall = time.time() - t0
    ls = sorted(lat)
    return {"conc": conc, "n": len(ids), "ok": ok, "err": err,
            "wall_s": round(wall, 2),
            "req_per_s": round(ok / wall, 1) if wall else 0,
            "mean_lat": round(statistics.mean(ls), 3) if ls else None,
            "p95": round(ls[int(len(ls) * .95) - 1], 3) if len(ls) > 3 else None,
            "refused": refused}


async def main(per_level=200):
    wl = json.load(open("worklist_DEVR.json"))
    pool = [r["document_id"] for r in wl]
    # ⚠ RE-MAPPING ALREADY-MAPPED DOCUMENTS ON PURPOSE. This is a timing test,
    # not a harvest; using fresh ids would confound the measurement with which
    # documents happen to be slow. The results are discarded.
    print(f"map ramp · {per_level} requests per level · results discarded\n")
    rows, base = [], None
    for c in (8, 12, 16, 20, 24):
        ids = (pool * 10)[:per_level]
        r = await level(ids, c)
        rows.append(r)
        if base is None:
            base = r["mean_lat"]
        ratio = r["mean_lat"] / base if base else 1
        print(f"  {c:>3} conc  {r['ok']:>4}/{r['n']} ok  {r['wall_s']:>6}s  "
              f"{r['req_per_s']:>6} req/s  lat {r['mean_lat']} ({ratio:.2f}x)  "
              f"p95 {r['p95']}  err {r['err']}")
        if r["refused"]:
            print("\n  ⚠ REFUSED — stopping. No retry.")
            break
        if ratio > LAT_ABORT:
            print(f"\n  ⚠ latency {ratio:.2f}x baseline — ceiling at {c}.")
            break
        await asyncio.sleep(2)

    best = max(rows, key=lambda r: r["req_per_s"])
    print(f"\n{'='*60}")
    for r in rows:
        print(f"  {r['conc']:>3}  {r['req_per_s']:>6} req/s   lat {r['mean_lat']}")
    print(f"\n  peak {best['req_per_s']} req/s at {best['conc']} concurrent")
    print(f"  -> ALL 17,036,716 ACRIS documents mapped: "
          f"{17_036_716/best['req_per_s']/3600:.1f} hours")
    print(f"  -> images cap at ~28 req/s — mapping is "
          f"{best['req_per_s']/28:.0f}x faster on the SAME session")
    json.dump(rows, open("_map_ramp.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 200))
