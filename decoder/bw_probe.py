"""IS 2.9 MB/s THE SERVER, THE PIPE, OR US? And does the 16-connection ceiling
survive warm connections?

⚠ TWO THINGS I SHOULD HAVE CHECKED EARLIER.

  1. THE PIPE HAS NEVER BEEN MEASURED. Acquisition sits at ~2.9 MB/s — about
     23 Mbps. If this connection is 100+ Mbps we are using a quarter of it and
     concurrency still has room. If it is a 25 Mbps line we have been at the
     ceiling since lunchtime and every further test is wasted. Nobody looked.

  2. THE 16-CONNECTION CEILING CAME FROM COLD BURSTS. Every ramp built a fresh
     connection pool per level and paid TCP/TLS setup inside the measurement.
     Repeated WARM and sustained, the same work doubled (28 -> 56 req/s). A
     ceiling found cold is not evidence about warm, and 24 was called
     "degraded" on exactly that basis.

⚠ THE STOPPING RULE IS UNCHANGED: latency is the server talking. Past 1.6x the
warm baseline is the ceiling, whatever throughput says.
"""
import asyncio
import json
import pathlib
import statistics
import sys
import time

import afetch
import fetch_budget

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = pathlib.Path("devr_pages")


def load_jobs():
    maps = {}
    for line in pathlib.Path("docmaps.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("instrument"):
                maps[r["doc_id"]] = tuple(r["instrument"])
    wl = {r["document_id"] for r in json.load(open("worklist_DEVR.json"))}
    jobs = []
    for d in (k for k in maps if k in wl):
        lo, hi = maps[d]
        for p in range(lo, hi + 1):
            if not fetch_budget.already_have(d, p):
                jobs.append((d, p))
    return jobs


def save(res):
    n = 0
    for r in res:
        if r and r.get("ok"):
            d = OUT / r["doc"]
            d.mkdir(parents=True, exist_ok=True)
            (d / f"p{r['page']:03d}.tif").write_bytes(r["data"])
            fetch_budget.note_fetch(r["doc"], r["page"])
            n += 1
    return n


async def warm_sustained(jobs, start, total_conn, nsess=2, seconds=40):
    conc = max(total_conn // nsess, 1)
    fetchers = [afetch.Fetcher(conc) for _ in range(nsess)]
    for f in fetchers:
        await f.__aenter__()
    cur = start
    for f in fetchers:
        await f.warm(jobs[cur][0])
    # ⚠ PRIME THE POOL BEFORE TIMING. Every connection established first — this
    # is precisely what the cold ramps failed to do.
    prime = jobs[cur:cur + total_conn]
    cur += len(prime)
    per = max(len(prime) // nsess, 1)
    await asyncio.gather(*(f.fetch_many(prime[i * per:(i + 1) * per])
                           for i, f in enumerate(fetchers)))

    t0, windows, saved = time.time(), [], 0
    while time.time() - t0 < seconds:
        batch = jobs[cur:cur + total_conn * 6]
        if len(batch) < total_conn:
            break
        cur += len(batch)
        per = max(len(batch) // nsess, 1)
        w0 = time.time()
        res = await asyncio.gather(*(f.fetch_many(batch[i * per:(i + 1) * per])
                                     for i, f in enumerate(fetchers)))
        wall = time.time() - w0
        flat = [r for sub in res for r in sub]
        ok = [r for r in flat if r and r.get("ok")]
        saved += save(flat)
        if any(r and r.get("err") == "REFUSED" for r in flat):
            print("      REFUSED — stopping.")
            break
        if ok:
            windows.append({
                "req_per_s": len(ok) / wall,
                "mb_per_s": sum(r["bytes"] for r in ok) / 1e6 / wall,
                "lat": statistics.mean([r["secs"] for r in ok])})
    for f in fetchers:
        await f.__aexit__()
    if not windows:
        return None, cur, saved
    return {"total_conn": total_conn, "sessions": nsess,
            "req_per_s": round(statistics.mean(w["req_per_s"] for w in windows), 1),
            "mb_per_s": round(statistics.mean(w["mb_per_s"] for w in windows), 2),
            "lat": round(statistics.mean(w["lat"] for w in windows), 3),
            "windows": len(windows)}, cur, saved


async def main():
    jobs = load_jobs()
    print(f"{len(jobs):,} unfetched pages\n")
    print("WARM SUSTAINED — does the ceiling move once connections are primed?\n")
    print(f"{'conn':>6}{'req/s':>9}{'MB/s':>8}{'Mbps':>8}{'latency':>10}")
    cur, rows, tot_saved, base_lat = 0, [], 0, None
    for total in (16, 24, 32, 48):
        r, cur, saved = await warm_sustained(jobs, cur, total, 2, 40)
        tot_saved += saved
        if not r:
            break
        rows.append(r)
        if base_lat is None:
            base_lat = r["lat"]
        ratio = r["lat"] / base_lat
        print(f"{total:>6}{r['req_per_s']:>9}{r['mb_per_s']:>8}"
              f"{r['mb_per_s']*8:>8.1f}{r['lat']:>8} ({ratio:.2f}x)")
        if ratio > 1.6:
            print(f"\n  latency {ratio:.2f}x baseline — ceiling at {total} connections.")
            break
        await asyncio.sleep(3)

    print(f"\n{'='*64}")
    if not rows:
        print("  no data")
        return
    best = max(rows, key=lambda r: r["mb_per_s"])
    print(f"  peak {best['mb_per_s']} MB/s ({best['mb_per_s']*8:.0f} Mbps) "
          f"at {best['total_conn']} connections")
    spread = (max(r["mb_per_s"] for r in rows) /
              min(r["mb_per_s"] for r in rows)) if len(rows) > 1 else 1
    print(f"  spread across levels: {spread:.2f}x")
    if spread < 1.15 and len(rows) > 2:
        print("  -> FLAT across concurrency = a PIPE or fixed-capacity limit.\n"
              "     More connections cannot help.")
    print(f"\n  corpus 140.2M pages at {best['req_per_s']} req/s: "
          f"{140.2e6/best['req_per_s']/86400:.0f} days")
    print(f"  {tot_saved} pages saved")
    json.dump(rows, open("_bw_probe.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
