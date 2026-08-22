"""IS ~30 Mbps ACRIS'S LIMIT, OR OURS? The one untested lever, tested carefully.

⚠ WHAT WE KNOW, AND WHY THE QUESTION IS STILL OPEN.

    three network conditions, same result
        home wifi                28.4 Mbps
        office, no VPN            8.1
        office, VPN (113 down)   30.3      <- 4x the link, +7% throughput
    128 connections WARM          runs for hours, no refusal
    128 connections COLD          refused within seconds

So concurrency stopped adding bytes long before bandwidth did. But the ONE
configuration never tried is high concurrency that is properly WARMED — the
failed attempt opened 128 sockets simultaneously from nothing, which is a
burst, not a concurrency level. Those are different experiments and only the
burst has been run.

⚠ HOW THIS DIFFERS FROM THE TEST THAT GOT REFUSED.

    that one   opened N connections at once, cold, measured immediately
    this one   RAMPS the pool: 32 -> target in steps, each step given real
               work, so the server sees a client growing rather than a flood

⚠ ABORT RULES, IN ORDER OF PRECEDENCE.
    1. ANY refusal            -> stop everything, immediately, no retry
    2. bytes not increasing   -> the ceiling is real; more connections are
                                 pure load with no return
    3. latency > 2.5x base    -> queueing
A level only "wins" if it moves MORE BYTES. req/s alone is misleading because
page sizes vary 3x.
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

LINK_MBPS = 112.85
BASE_MBPS = 30.3          # what the map draws at 128 warm


class Pool:
    """A session whose connection pool is grown gradually, never burst."""

    def __init__(self, cap):
        self.cap = cap
        self.session = None

    async def __aenter__(self):
        import aiohttp
        conn = aiohttp.TCPConnector(limit=self.cap, limit_per_host=self.cap,
                                    ttl_dns_cache=600)
        self.session = aiohttp.ClientSession(
            connector=conn, headers={"User-Agent": amap.UA},
            timeout=aiohttp.ClientTimeout(total=60))
        return self

    async def __aexit__(self, *a):
        await self.session.close()

    async def hit(self, doc, sem, out):
        async with sem:
            t = time.time()
            try:
                async with self.session.get(amap.VIEW + doc) as r:
                    body = await r.read()
                    ct = r.headers.get("Content-Type", "")
            except Exception as e:
                out["err"].append(type(e).__name__)
                return
            dt = time.time() - t
            try:
                fetch_pages._check_denied(body, ct)
            except fetch_pages.AccessDenied:
                out["refused"] = True
                return
            out["lat"].append(dt)
            out["bytes"] += len(body)
            out["ok"] += 1

    async def warm_to(self, level, ids, cursor):
        """⚠ GROW the pool in steps, giving each step real work. This is the
        difference between a client ramping up and a client flooding."""
        step = 32
        cur = step
        while cur < level:
            sem = asyncio.Semaphore(cur)
            out = {"lat": [], "bytes": 0, "ok": 0, "err": [], "refused": False}
            batch = ids[cursor:cursor + cur * 2]
            cursor += len(batch)
            await asyncio.gather(*(self.hit(d, sem, out) for d in batch))
            if out["refused"]:
                return cursor, True
            cur = min(cur * 2, level)
            await asyncio.sleep(0.5)
        return cursor, False


async def measure(pools, level_each, ids, cursor, seconds=25):
    sems = [asyncio.Semaphore(level_each) for _ in pools]
    outs = [{"lat": [], "bytes": 0, "ok": 0, "err": [], "refused": False}
            for _ in pools]
    t0 = time.time()
    while time.time() - t0 < seconds:
        tasks = []
        for p, sem, out in zip(pools, sems, outs):
            batch = ids[cursor:cursor + level_each * 3]
            cursor += len(batch)
            if not batch:
                break
            tasks += [p.hit(d, sem, out) for d in batch]
        if not tasks:
            break
        await asyncio.gather(*tasks)
        if any(o["refused"] for o in outs):
            break
    wall = time.time() - t0
    ok = sum(o["ok"] for o in outs)
    nbytes = sum(o["bytes"] for o in outs)
    lat = [x for o in outs for x in o["lat"]]
    return {
        "sessions": len(pools), "conc_each": level_each,
        "total_conn": len(pools) * level_each,
        "ok": ok, "req_per_s": round(ok / wall, 1) if wall else 0,
        "mbps": round(nbytes * 8 / 1e6 / wall, 1) if wall else 0,
        "lat": round(statistics.mean(lat), 3) if lat else None,
        "refused": any(o["refused"] for o in outs),
        "errs": sum(len(o["err"]) for o in outs),
    }, cursor


async def main():
    done = set()
    with open("acris_maps.jsonl", encoding="utf-8") as f:
        for l in f:
            if l.strip():
                done.add(json.loads(l)["doc_id"])
    ids = []
    with open("acris_ids.jsonl", encoding="utf-8") as f:
        for l in f:
            if not l.strip():
                continue
            d = json.loads(l)["document_id"]
            if d not in done:
                ids.append(d)
            if len(ids) >= 120000:
                break
    print(f"{len(ids):,} unmapped ids · link {LINK_MBPS} Mbps · "
          f"baseline {BASE_MBPS} Mbps at 128 warm\n")
    print(f"{'config':>14}{'conn':>6}{'maps/s':>9}{'Mbps':>7}{'%link':>7}{'lat':>8}")

    cursor, rows = 0, []
    plan = [(2, 64), (2, 96), (2, 128), (2, 192)]
    for nsess, each in plan:
        pools = [Pool(each) for _ in range(nsess)]
        for p in pools:
            await p.__aenter__()
        refused = False
        for p in pools:
            cursor, refused = await p.warm_to(each, ids, cursor)
            if refused:
                break
        if refused:
            print("  ⚠ REFUSED during warm-up — stopping, no retry.")
            for p in pools:
                await p.__aexit__()
            break
        r, cursor = await measure(pools, each, ids, cursor)
        for p in pools:
            await p.__aexit__()
        rows.append(r)
        print(f"{f'{nsess}x{each}':>14}{r['total_conn']:>6}{r['req_per_s']:>9}"
              f"{r['mbps']:>7}{100*r['mbps']/LINK_MBPS:>6.0f}%{r['lat']:>8}"
              + ("  ⚠ REFUSED" if r["refused"] else ""))
        if r["refused"]:
            print("  stopping — no retry.")
            break
        # ⚠ bytes must actually grow, or more connections are pure load
        if len(rows) > 1 and r["mbps"] < rows[-2]["mbps"] * 1.08:
            print(f"\n  bytes stopped growing ({rows[-2]['mbps']} -> {r['mbps']}) "
                  f"— ceiling reached.")
            break
        await asyncio.sleep(4)

    print(f"\n{'='*58}")
    if not rows:
        print("  no data")
        return
    best = max(rows, key=lambda r: r["mbps"])
    gain = best["mbps"] / BASE_MBPS
    print(f"  best {best['sessions']}x{best['conc_each']} = "
          f"{best['total_conn']} conn · {best['mbps']} Mbps · {gain:.2f}x baseline")
    corpus = 140.2e6
    pages_s = best["mbps"] * 1e6 / 8 / 53000
    print(f"  corpus 140.2M pages at this byte rate: "
          f"{corpus/pages_s/86400:.1f} days   (was 16)")
    if gain < 1.15:
        print("\n  -> ACRIS's ceiling is real. Neither bandwidth nor concurrency\n"
              "     moves it. 16 days is the floor for image acquisition.")
    json.dump(rows, open("_push_ceiling.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
