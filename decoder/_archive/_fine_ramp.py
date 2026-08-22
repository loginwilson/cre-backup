"""FINE SWEEP AROUND THE IMAGE PEAK — 8, 10, 12, 14, 16.

⚠ THE COARSE RAMP SKIPPED 12. It tested 8 -> 16 -> 24 on the async path and
called 16 the peak, but never looked between 8 and 16. 8 had the lowest latency
measured all day (0.300s) and 16 the highest throughput (27.93 req/s) at 1.24x
that latency — the optimum is somewhere in the gap nobody sampled.

⚠ AND THE PAGES ARE KEPT. The earlier ramps discarded everything they fetched,
which meant paying the heavy endpoint for pure measurement. These are real DEVR
instrument pages that acquisition needs anyway, written to devr_pages/ and
recorded in the ledger, so the test doubles as work.
"""
import asyncio
import json
import pathlib
import sys
import time

import afetch
import fetch_budget

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = pathlib.Path("devr_pages")


def jobs_for(n, cursor, maps):
    out = []
    docs = list(maps)
    i = 0
    while len(out) < n and i < len(docs) * 400:
        d = docs[i % len(docs)]
        lo, hi = maps[d]
        p = cursor.get(d, lo)
        while p <= hi and fetch_budget.already_have(d, p):
            p += 1
        if p <= hi:
            out.append((d, p))
            cursor[d] = p + 1
        i += 1
    return out


async def main(per_level=48):
    maps = {}
    for line in pathlib.Path("docmaps.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("hid_TotalPages") and r.get("instrument"):
            maps[r["doc_id"]] = tuple(r["instrument"])
    wl = {r["document_id"] for r in json.load(open("worklist_DEVR.json"))}
    maps = {k: v for k, v in maps.items() if k in wl}
    print(f"{len(maps):,} mapped DEVR documents · {per_level} pages per level\n")

    cursor, rows, saved = {}, [], 0
    for c in (8, 10, 12, 14, 16):
        jobs = jobs_for(per_level, cursor, maps)
        if len(jobs) < per_level:
            print("  (ran out of unfetched pages)")
            break
        async with afetch.Fetcher(c) as f:
            await f.warm(jobs[0][0])
            t0 = time.time()
            res = await f.fetch_many(jobs)
            wall = time.time() - t0
        ok = [r for r in res if r and r.get("ok")]
        for r in ok:                      # ⚠ keep what we paid for
            d = OUT / r["doc"]
            d.mkdir(parents=True, exist_ok=True)
            (d / f"p{r['page']:03d}.tif").write_bytes(r["data"])
            fetch_budget.note_fetch(r["doc"], r["page"])
            saved += 1
        lat = sorted(x["secs"] for x in ok)
        row = {"conc": c, "ok": len(ok), "n": len(jobs),
               "req_per_s": round(len(ok) / wall, 2),
               "mean_lat": round(sum(lat) / len(lat), 3) if lat else None,
               "p95": round(lat[int(len(lat) * .95) - 1], 3) if len(lat) > 3 else None,
               "mb": round(sum(x["bytes"] for x in ok) / 1e6, 1)}
        rows.append(row)
        print(f"  {c:>2} conc  {row['ok']:>3}/{row['n']}  {row['req_per_s']:>6} req/s  "
              f"lat {row['mean_lat']}  p95 {row['p95']}  {row['mb']} MB")
        if any(r and r.get("err") == "REFUSED" for r in res):
            print("  ⚠ REFUSED — stopping.")
            break
        await asyncio.sleep(2)

    print("\n" + "=" * 60)
    base = rows[0]
    for r in rows:
        # ⚠ SCORE = throughput per unit of latency. Raw peak throughput picks
        # the setting that makes their server work hardest; this picks the one
        # that gets the most out of it per unit of strain.
        score = r["req_per_s"] / (r["mean_lat"] / base["mean_lat"])
        print(f"  {r['conc']:>2}  {r['req_per_s']:>6} req/s  lat {r['mean_lat']}  "
              f"({r['mean_lat']/base['mean_lat']:.2f}x)   score {score:.1f}")
    best_t = max(rows, key=lambda r: r["req_per_s"])
    best_s = max(rows, key=lambda r: r["req_per_s"] / (r["mean_lat"] / base["mean_lat"]))
    print(f"\n  highest throughput : {best_t['conc']} conc, {best_t['req_per_s']} req/s")
    print(f"  best throughput/latency : {best_s['conc']} conc, {best_s['req_per_s']} req/s")
    print(f"  -> DEVR 42,569 instrument pages at {best_s['req_per_s']} req/s: "
          f"{42569/best_s['req_per_s']/60:.0f} min")
    print(f"  {saved} pages saved to devr_pages/ (not discarded)")
    json.dump(rows, open("_fine_ramp.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 48))
