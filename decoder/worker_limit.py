"""FIND THE PER-SESSION WORKER LIMIT — 8, 12, 16, 20, 24, 28, 32.

⚠ WHY THIS SHAPE, AFTER THREE REFUSALS. The refusals came from opening
connections FAST, not from holding many. The running map sits at 128 for hours
untouched; a ramp that opened 8 in a fresh pool got refused because the pool
itself was new and grew in seconds.

So this keeps ONE session alive for the whole run and widens the semaphore
through the levels. The connection pool grows the way the map's did — by doing
work — instead of being rebuilt per level. Nothing is ever opened cold.

⚠ MEASURE BYTES, NOT req/s. DEVR pages run 20-80 KB, so a level that happens
to draw light pages posts a flattering req/s. Every prior "gain" that later
evaporated (the 2.81x distribution result, the 13% session split) was this
mistake.

⚠ THE LIMIT IS WHERE BYTES STOP GROWING, not where latency first moves. Latency
rising while bytes still climb is just a deeper queue doing useful work.
Latency rising while bytes are flat is the ceiling.

⚠ ABORT ON ANY REFUSAL. No retry, no "try a gentler shape" — that is what
turned one refusal into three.
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
LEVELS = (8, 12, 16, 20, 24, 28, 32)


def jobs():
    maps = {}
    for line in pathlib.Path("docmaps.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("instrument"):
                maps[r["doc_id"]] = tuple(r["instrument"])
    wl = {r["document_id"] for r in json.load(open("worklist_DEVR.json"))}
    out = []
    for d in (k for k in maps if k in wl):
        lo, hi = maps[d]
        for p in range(lo, hi + 1):
            if not fetch_budget.already_have(d, p):
                out.append((d, p))
    return out


def save(res):
    n = 0
    for r in res:
        if r and r.get("ok"):
            dd = OUT / r["doc"]
            dd.mkdir(parents=True, exist_ok=True)
            (dd / f"p{r['page']:03d}.tif").write_bytes(r["data"])
            fetch_budget.note_fetch(r["doc"], r["page"])
            n += 1
    return n


async def main(seconds=22):
    work = jobs()
    print(f"{len(work):,} unfetched DEVR pages · one session, widened per level\n")
    print(f"{'workers':>8}{'pages':>7}{'req/s':>8}{'MB/s':>7}{'latency':>9}{'saved':>7}")

    # ⚠ ONE session, pool capped at the maximum we will reach. It is never
    # rebuilt, so connections established at level 8 are reused at 32.
    f = afetch.Fetcher(max(LEVELS))
    await f.__aenter__()
    cur, rows, total_saved = 0, [], 0
    await f.warm(work[0][0])

    try:
        for lvl in LEVELS:
            sem = asyncio.Semaphore(lvl)

            # gentle warm INTO this level using the existing pool
            wb = work[cur:cur + lvl * 2]
            cur += len(wb)
            res = await asyncio.gather(*(f.page(d, p, sem) for d, p in wb))
            total_saved += save(res)
            if any(r and r.get("err") == "REFUSED" for r in res):
                print(f"{lvl:>8}   ⚠ REFUSED during warm — stopping. No retry.")
                break
            await asyncio.sleep(1.5)

            t0, ok, nbytes, lat = time.time(), 0, 0, []
            while time.time() - t0 < seconds:
                batch = work[cur:cur + lvl * 4]
                cur += len(batch)
                if not batch:
                    break
                res = await asyncio.gather(*(f.page(d, p, sem) for d, p in batch))
                total_saved += save(res)
                if any(r and r.get("err") == "REFUSED" for r in res):
                    print(f"{lvl:>8}   ⚠ REFUSED — stopping. No retry.")
                    rows.append(None)
                    break
                good = [r for r in res if r and r.get("ok")]
                ok += len(good)
                nbytes += sum(r["bytes"] for r in good)
                lat += [r["secs"] for r in good]
            if rows and rows[-1] is None:
                break
            wall = time.time() - t0
            row = {"workers": lvl, "ok": ok,
                   "req_per_s": round(ok / wall, 1) if wall else 0,
                   "mb_per_s": round(nbytes / 1e6 / wall, 2) if wall else 0,
                   "lat": round(statistics.mean(lat), 3) if lat else None}
            rows.append(row)
            print(f"{lvl:>8}{ok:>7}{row['req_per_s']:>8}{row['mb_per_s']:>7}"
                  f"{row['lat']:>9}{total_saved:>7}")
            await asyncio.sleep(2)
    finally:
        await f.__aexit__()

    rows = [r for r in rows if r]
    if len(rows) < 2:
        print("\n  not enough levels completed")
        return
    print(f"\n{'='*56}")
    best = max(rows, key=lambda r: r["mb_per_s"])
    base = rows[0]
    print(f"{'workers':>8}{'MB/s':>7}{'vs 8':>7}{'latency':>9}{'verdict':>16}")
    for r in rows:
        gain = r["mb_per_s"] / base["mb_per_s"] if base["mb_per_s"] else 0
        lx = r["lat"] / base["lat"] if base["lat"] else 0
        v = "peak" if r is best else ("flat" if gain < 1.08 else "")
        print(f"{r['workers']:>8}{r['mb_per_s']:>7}{gain:>6.2f}x{r['lat']:>9}"
              f"{v:>16}")
    print(f"\n  peak {best['mb_per_s']} MB/s at {best['workers']} workers")
    # ⚠ the useful answer is the SMALLEST level within noise of the peak —
    # the least load that gets essentially everything.
    good = [r for r in rows if r["mb_per_s"] >= best["mb_per_s"] * 0.92]
    cheapest = min(good, key=lambda r: r["workers"])
    print(f"  cheapest within 8% of peak: {cheapest['workers']} workers "
          f"({cheapest['mb_per_s']} MB/s, lat {cheapest['lat']})")
    print(f"  {total_saved:,} pages saved")
    json.dump(rows, open("_worker_limit.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
