"""SESSION DISTRIBUTION AT 128 TOTAL CONNECTIONS — 1x128 vs 2x64 vs 4x32.

⚠ THE ONE UNTESTED CELL. Distribution was measured cleanly at 16 total
connections and showed nothing (every arm 2.45-3.27 MB/s, ranges overlapping).
It has never been measured at the level we actually run — 128 — where the
per-session connection pool is 8x larger and might behave differently.

⚠ AND THE LAST ATTEMPT AT THIS GOT REFUSED, TWICE. What tripped it was not the
concurrency level but the RATE OF CONNECTION ESTABLISHMENT: 128 sockets opened
from nothing in seconds. The running map holds 128 for hours without complaint
because it grew there gradually during ordinary work.

So the ramp here is deliberately slow:

    start at 8           not 32
    grow x1.5            not x2
    real work each step  so the pool is used, not just opened
    2s between steps     not 0.5s

If it is refused anyway, that is the answer and the test stops. No retry, no
second attempt at a different shape.

⚠ MEASURED ON IMAGE PAGES WE ACTUALLY NEED — unfetched DEVR instrument pages,
written to disk and recorded in the ledger. The heavy endpoint is the one the
16-day estimate depends on, and nothing here is spent purely on measurement.
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
TOTAL = 128


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


async def gentle_warm(f, target, work, cursor):
    """⚠ GROW, don't open. 8 -> x1.5 -> target, working at every step."""
    cur = 8
    while True:
        batch = work[cursor:cursor + cur * 2]
        cursor += len(batch)
        if not batch:
            return cursor, False
        res = await f.fetch_many(batch)
        save(res)
        if any(r and r.get("err") == "REFUSED" for r in res):
            return cursor, True
        if cur >= target:
            return cursor, False
        cur = min(int(cur * 1.5) + 1, target)
        await asyncio.sleep(2)


async def arm(nsess, work, cursor, seconds=30):
    each = TOTAL // nsess
    fs = [afetch.Fetcher(each) for _ in range(nsess)]
    for f in fs:
        await f.__aenter__()
    for f in fs:
        await f.warm(work[cursor][0])
        cursor, refused = await gentle_warm(f, each, work, cursor)
        if refused:
            for x in fs:
                await x.__aexit__()
            return None, cursor

    t0, ok, nbytes, lat, saved = time.time(), 0, 0, [], 0
    while time.time() - t0 < seconds:
        chunks = []
        for _ in fs:
            b = work[cursor:cursor + each * 3]
            cursor += len(b)
            chunks.append(b)
        if not any(chunks):
            break
        res = await asyncio.gather(*(f.fetch_many(c) for f, c in zip(fs, chunks)))
        flat = [r for sub in res for r in sub]
        if any(r and r.get("err") == "REFUSED" for r in flat):
            for x in fs:
                await x.__aexit__()
            return None, cursor
        good = [r for r in flat if r and r.get("ok")]
        ok += len(good)
        nbytes += sum(r["bytes"] for r in good)
        lat += [r["secs"] for r in good]
        saved += save(flat)
    wall = time.time() - t0
    for f in fs:
        await f.__aexit__()
    return {"sessions": nsess, "each": each, "ok": ok,
            "req_per_s": round(ok / wall, 1) if wall else 0,
            "mb_per_s": round(nbytes / 1e6 / wall, 2) if wall else 0,
            "lat": round(statistics.mean(lat), 3) if lat else None,
            "saved": saved}, cursor


async def main():
    work = jobs()
    print(f"{len(work):,} unfetched DEVR instrument pages · {TOTAL} total conn\n")
    print(f"{'config':>10}{'pages':>8}{'req/s':>8}{'MB/s':>7}{'latency':>9}")
    cursor, rows = 0, []
    # ⚠ INTERLEAVED so drift in server load cannot masquerade as an arm effect
    for nsess in (1, 2, 4, 2, 4, 1):
        r, cursor = await arm(nsess, work, cursor)
        if r is None:
            print(f"  {nsess}x{TOTAL//nsess}: ⚠ REFUSED — stopping. No retry.")
            break
        rows.append(r)
        label = f"{nsess}x{r['each']}"
        print(f"{label:>10}{r['ok']:>8}{r['req_per_s']:>8}"
              f"{r['mb_per_s']:>7}{r['lat']:>9}")
        await asyncio.sleep(5)

    if not rows:
        print("\n  no data")
        return
    print(f"\n{'='*50}")
    by = {}
    for r in rows:
        by.setdefault(r["sessions"], []).append(r["mb_per_s"])
    for k in sorted(by):
        v = by[k]
        print(f"  {k} session(s) x {TOTAL//k:>3}   "
              f"MB/s {statistics.mean(v):.2f}  (n={len(v)}, {min(v)}-{max(v)})")
    lo = min(statistics.mean(v) for v in by.values())
    hi = max(statistics.mean(v) for v in by.values())
    print(f"\n  spread {hi/lo:.2f}x")
    # ⚠ overlapping ranges mean no effect, whatever the means say
    ranges = [(min(v), max(v)) for v in by.values()]
    overlap = max(r[0] for r in ranges) <= min(r[1] for r in ranges)
    if overlap or hi / lo < 1.15:
        print("  -> NO EFFECT. Ranges overlap; distribution does not matter at 128\n"
              "     any more than it did at 16.")
    else:
        print(f"  -> distribution matters at 128: best is "
              f"{max(by, key=lambda k: statistics.mean(by[k]))} sessions")
    print(f"  {sum(r['saved'] for r in rows):,} pages saved")
    json.dump(rows, open("_dist_128.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
