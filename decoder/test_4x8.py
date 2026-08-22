"""4 SESSIONS x 8 WORKERS vs 1 SESSION x 32 — same 32 total connections.

⚠ THE HYPOTHESIS BEING TESTED (Login's): 8 workers is the optimum inside one
session, so four sessions at 8 should multiply it — and the latency seen with
multiple sessions earlier was the local connection, not ACRIS.

⚠ THE EVIDENCE AGAINST IT, so the result can be judged fairly:
    two independent sessions, measured together   142.6 maps/s combined
    each session alone                            163.7 and 177.8
    -> they SPLIT the pool (71.7 + 71.4), they did not add
    distribution at 16 total connections          all arms 2.45-3.27 MB/s
    -> only the TOTAL mattered, never the shape

⚠ AND THE LOCAL-CONGESTION EXPLANATION HAS A PROBLEM: the link is at 25%
utilisation (28 of 113 Mbps) with 13 ms ping. Local congestion produces latency
near saturation, not at a quarter of it. If latency still rises here at 25%
utilisation, it is not the pipe.

CONTROLS
    * identical TOTAL connections (32) in both arms — the only variable is shape
    * identical page budget per arm
    * interleaved 1x32 / 4x8 / 1x32 / 4x8 so server drift cannot fake an effect
    * every session warmed gently BEFORE the clock starts
    * bytes, not req/s — DEVR pages vary 20-80 KB
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
TOTAL = 32
PER_ARM = 700


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


async def arm(nsess, work, cursor):
    each = TOTAL // nsess
    fs = [afetch.Fetcher(each) for _ in range(nsess)]
    for f in fs:
        await f.__aenter__()
    saved = 0
    try:
        # ⚠ warm every session gently before timing — never open cold
        for f in fs:
            await f.warm(work[cursor][0])
            wb = work[cursor:cursor + each * 2]
            cursor += len(wb)
            res = await f.fetch_many(wb)
            saved += save(res)
            if any(r and r.get("err") == "REFUSED" for r in res):
                return None, cursor, saved
            await asyncio.sleep(1)

        t0, ok, nbytes, lat = time.time(), 0, 0, []
        got = 0
        while got < PER_ARM:
            chunks = []
            for _ in fs:
                b = work[cursor:cursor + each * 3]
                cursor += len(b)
                chunks.append(b)
            if not any(chunks):
                break
            res = await asyncio.gather(*(f.fetch_many(c) for f, c in zip(fs, chunks)))
            flat = [r for sub in res for r in sub]
            saved += save(flat)
            if any(r and r.get("err") == "REFUSED" for r in flat):
                return None, cursor, saved
            good = [r for r in flat if r and r.get("ok")]
            ok += len(good)
            got += len(flat)
            nbytes += sum(r["bytes"] for r in good)
            lat += [r["secs"] for r in good]
        wall = time.time() - t0
    finally:
        for f in fs:
            await f.__aexit__()
    return {"sessions": nsess, "each": each, "ok": ok,
            "req_per_s": round(ok / wall, 1) if wall else 0,
            "mb_per_s": round(nbytes / 1e6 / wall, 2) if wall else 0,
            "lat": round(statistics.mean(lat), 3) if lat else None,
            "p95": round(sorted(lat)[int(len(lat) * .95) - 1], 3) if len(lat) > 5 else None,
            }, cursor, saved


async def main():
    work = jobs()
    print(f"{len(work):,} unfetched DEVR pages · {TOTAL} total connections both arms\n")
    print(f"{'config':>10}{'pages':>7}{'req/s':>8}{'MB/s':>7}{'lat':>8}{'p95':>8}")
    cursor, rows, total_saved = 0, [], 0
    for nsess in (1, 4, 1, 4):
        r, cursor, s = await arm(nsess, work, cursor)
        total_saved += s
        if r is None:
            print(f"  {nsess}x{TOTAL//nsess}: ⚠ REFUSED — stopping. No retry.")
            break
        rows.append(r)
        label = f"{nsess}x{r['each']}"
        print(f"{label:>10}{r['ok']:>7}{r['req_per_s']:>8}"
              f"{r['mb_per_s']:>7}{r['lat']:>8}{r['p95']:>8}")
        await asyncio.sleep(4)

    if len(rows) < 2:
        print("\n  not enough data")
        return
    by = {}
    for r in rows:
        by.setdefault(r["sessions"], []).append(r)
    print(f"\n{'='*54}")
    for k in sorted(by):
        v = by[k]
        mb = [x["mb_per_s"] for x in v]
        la = [x["lat"] for x in v]
        print(f"  {k} x {TOTAL//k:<3}  MB/s {statistics.mean(mb):.2f} "
              f"({min(mb)}-{max(mb)})   latency {statistics.mean(la):.3f}")
    if len(by) == 2:
        one = statistics.mean(x["mb_per_s"] for x in by[1])
        four = statistics.mean(x["mb_per_s"] for x in by[4])
        print(f"\n  4x8 vs 1x32 on BYTES: {four/one:.2f}x")
        if four / one < 1.15:
            print("  -> NO MULTIPLICATION. Sessions share one allocation; only\n"
                  "     the TOTAL connection count matters, and it has plateaued.")
        else:
            print(f"  -> sessions DO help: {four/one:.2f}x")
    print(f"  {total_saved:,} pages saved")
    json.dump(rows, open("_test_4x8.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
