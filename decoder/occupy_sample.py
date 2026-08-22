"""HEAD PAGES FOR THE LEASE FAMILY — the only ACRIS types whose function is OCCUPY.

⚠ WHY THIS EXISTS. The hidden-function matrix scored 518 documents across 13
types and every one of them landed in a function we already had a detector for.
That was not luck and it was not coverage: `stratified_sample.py` walks all 95
types, but nothing had ever pulled the lease family, so OCCUPY has never been
seen by this project at all. A function with no documents cannot be measured,
and "0 detectors, 0 documents" reads exactly like "nothing to find".

⚠ SPREAD ACROSS ERAS, NOT TAKEN OFF THE TOP — reusing stratified_sample.select,
because the first ten ids of any type share a recording day, a borough and often
one title company, which is the homogeneity that made a one-document lexicon
look complete.

⚠ HEAD PAGES ONLY. A lease can run 200 pages. The demise clause, the term and the
parties are all in the opening; the rest is boilerplate that would cost hours and
teach the detector nothing. HEAD is a stated limit, not a silent truncation — it
is printed with every count.
"""
from __future__ import annotations

import asyncio, json, pathlib, sys, time
import concurrent.futures as cf

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bulk, amap, afetch, acris_lock
import stratified_sample as ss

# LEAS lease · MLEA memorandum · ASSTO assignment of lease · TERL termination
# · SUBL subordination. Together 35,692 documents = 0.17% of ACRIS.
TYPES = ["LEAS", "MLEA", "ASSTO", "TERL", "SUBL"]
HEAD = 6
OUT = pathlib.Path("lease_pages")
PLAN = pathlib.Path("_occupy_plan.json")


async def acquire(plan):
    ids = sorted({d for v in plan.values() for d in v})
    print(f"\nmapping {len(ids):,} documents")
    await amap.run(ids, conc=32)

    want = set(ids)
    maps = {}
    for name in ("docmaps.jsonl", "acris_maps.jsonl"):
        p = pathlib.Path(name)
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("doc_id") in want:
                    maps[r["doc_id"]] = r

    jobs, noimg, capped = [], 0, 0
    for d in ids:
        m = maps.get(d)
        if not m:
            continue
        tot = m.get("hid_TotalPages")
        if tot is None or tot <= 0:      # 0 and -1 BOTH mean no image
            noimg += 1
            continue
        lo, hi = (m.get("instrument") or [1, tot])[:2]
        if hi < lo:
            continue
        if hi - lo + 1 > HEAD:
            capped += 1
            hi = lo + HEAD - 1
        jobs += [(d, p) for p in range(lo, hi + 1)]

    print(f"  {len(jobs):,} pages · {noimg} documents have no image · "
          f"{capped} documents capped at HEAD={HEAD} (body NOT read)")
    if not jobs:
        return

    OUT.mkdir(exist_ok=True)
    writer = cf.ThreadPoolExecutor(4)
    f = afetch.Fetcher(ss.WORKERS)
    await f.__aenter__()
    saved, t0 = 0, time.time()
    try:
        await f.warm(jobs[0][0])
        i = 0
        while i < len(jobs):
            b = jobs[i:i + ss.WORKERS * 6]
            i += len(b)
            sem = asyncio.Semaphore(ss.WORKERS)
            res = await asyncio.gather(*(f.page(d, p, sem) for d, p in b))
            if any(r and r.get("err") == "REFUSED" for r in res):
                print(f"\n  ⚠ REFUSED after {saved:,} pages — stopping. No retry.")
                break
            good = [r for r in res if r and r.get("ok")]
            for r in good:
                (OUT / r["doc"]).mkdir(parents=True, exist_ok=True)
            list(writer.map(lambda r: (OUT / r["doc"] /
                                       f"p{r['page']:03d}.tif").write_bytes(r["data"]),
                            good))
            saved += len(good)
            if saved and saved % 300 < ss.WORKERS * 6:
                print(f"    {saved:,}/{len(jobs):,}  "
                      f"{saved/(time.time()-t0):.1f} pg/s", flush=True)
    finally:
        await f.__aexit__()
    el = time.time() - t0
    print(f"\n  {saved:,} pages in {el/60:.1f} min ({saved/max(el,1):.1f} pg/s)")


async def main():
    if PLAN.exists():
        plan = json.loads(PLAN.read_text())
    else:
        ss.PER_CELL = 10
        plan = ss.select(TYPES)
        PLAN.write_text(json.dumps(plan, indent=1))
    tot = sum(len(v) for v in plan.values())
    print(f"{'type':<8}" + "".join(f"{e:>8}" for e, _ in ss.ERAS) + f"{'total':>8}")
    for t in TYPES:
        row = [len(plan.get(f"{t}|{e}", [])) for e, _ in ss.ERAS]
        print(f"{t:<8}" + "".join(f"{c:>8}" for c in row) + f"{sum(row):>8}")
    print(f"\n  {tot} documents to acquire · {acris_lock.status()}")
    if "--plan" in sys.argv:
        print("  --plan given: nothing fetched.")
        return
    with acris_lock.AcrisLock("occupy_sample", wait=True):
        await acquire(plan)


if __name__ == "__main__":
    asyncio.run(main())
