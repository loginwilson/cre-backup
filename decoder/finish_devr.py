"""FINISH THE DEVR TYPE — the remaining ~7,400 instrument pages.

⚠ SETTINGS CHOSEN FROM TODAY'S MEASUREMENTS, NOT GUESSED.

    8 workers        bytes were FLAT from 8 to 32 while latency doubled
                     (1.19 -> 1.49 MB/s, 0.181s -> 0.381s). Everything above
                     8 is load with no return.
    one session      4x8 measured 0.91x of 1x32; sessions share one allocation
    WARMED           three refusals today came from opening pools fast, not
                     from concurrency. The pool grows through real work here.
    abort on refusal no retry. Retrying is what turned one refusal into three.

⚠ RUNS ALONGSIDE THE MAP DELIBERATELY. The map endpoint (DocumentImageView)
and the image endpoint (GetImage) were shown to have separate budgets — the
map ran normally while images were refused. Running both is also a live test
of that claim: if the map's rate drops when this starts, they are not as
separate as they looked.

⚠ ONLY INSTRUMENT PAGES. The map records where the instrument ends and
supporting documents begin, so nothing is fetched blind and no range is
scanned — the technique that got this project blocked in August.
"""
import asyncio
import json
import pathlib
import statistics
import sys
import time

import acris_lock
import afetch
import fetch_budget

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = pathlib.Path("devr_pages")
WORKERS = 8


def todo():
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


async def main():
    # ⚠ QUEUES BEHIND THE MAP rather than racing it for sockets.
    with acris_lock.AcrisLock("finish_devr", wait=True):
        await _main()


async def _main():
    jobs = todo()
    print(f"{len(jobs):,} DEVR instrument pages remaining · {WORKERS} workers, warmed\n")
    if not jobs:
        print("  DEVR is complete.")
        return
    f = afetch.Fetcher(WORKERS)
    await f.__aenter__()
    saved, t0, lat = 0, time.time(), []
    try:
        await f.warm(jobs[0][0])
        # ⚠ grow gently: 2 -> 4 -> 8, working at each step
        cur, i = 2, 0
        while cur <= WORKERS and i < len(jobs):
            sem = asyncio.Semaphore(cur)
            b = jobs[i:i + cur * 3]
            i += len(b)
            res = await asyncio.gather(*(f.page(d, p, sem) for d, p in b))
            if any(r and r.get("err") == "REFUSED" for r in res):
                print("  ⚠ REFUSED during warm-up — stopping. No retry.")
                return
            for r in res:
                if r and r.get("ok"):
                    dd = OUT / r["doc"]
                    dd.mkdir(parents=True, exist_ok=True)
                    (dd / f"p{r['page']:03d}.tif").write_bytes(r["data"])
                    fetch_budget.note_fetch(r["doc"], r["page"])
                    saved += 1
            cur *= 2
            await asyncio.sleep(1)

        sem = asyncio.Semaphore(WORKERS)
        while i < len(jobs):
            b = jobs[i:i + WORKERS * 6]
            i += len(b)
            res = await asyncio.gather(*(f.page(d, p, sem) for d, p in b))
            if any(r and r.get("err") == "REFUSED" for r in res):
                print(f"\n  ⚠ REFUSED after {saved:,} pages — stopping. No retry.")
                break
            for r in res:
                if r and r.get("ok"):
                    dd = OUT / r["doc"]
                    dd.mkdir(parents=True, exist_ok=True)
                    (dd / f"p{r['page']:03d}.tif").write_bytes(r["data"])
                    fetch_budget.note_fetch(r["doc"], r["page"])
                    saved += 1
                    lat.append(r["secs"])
            if saved and saved % 500 < WORKERS * 6:
                el = time.time() - t0
                print(f"    {saved:,}/{len(jobs):,}  {saved/el:.1f} pg/s  "
                      f"lat {statistics.mean(lat[-200:]):.3f}  "
                      f"~{(len(jobs)-saved)/max(saved/el,.01)/60:.0f} min left",
                      flush=True)
    finally:
        await f.__aexit__()
    el = time.time() - t0
    print(f"\n  {saved:,} pages in {el/60:.1f} min ({saved/el:.1f} pg/s)")
    sz = sum(x.stat().st_size for x in OUT.rglob('*.tif'))
    print(f"  devr_pages now {sz/1e9:.2f} GB")


if __name__ == "__main__":
    asyncio.run(main())
