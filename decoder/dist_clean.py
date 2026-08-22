"""DOES SESSION DISTRIBUTION MATTER? Third attempt, this time controlled.

⚠ TWO PRIOR ATTEMPTS, BOTH CONFOUNDED, WITH OPPOSITE CONCLUSIONS.

    attempt 1  1 session x16 vs 2 sessions x16 EACH.
               32 total connections against a ceiling measured at 16 — the
               two-session arm was over the limit before it started.
               Concluded "sessions are irrelevant". Could not have concluded
               anything else.

    attempt 2  held total connections at 16, but gave each arm 64 pages PER
               SESSION — so the arms fetched 64, 128 and 256 pages. The
               4-session arm amortised its warm-up over 4x the work.
               Concluded "4x4 wins by 2.81x". The confound is the same size as
               the claimed effect.

⚠ SO: HOLD EVERYTHING FIXED EXCEPT THE THING BEING TESTED.

    same total pages          256 per arm
    same total connections     16 per arm
    same warm-up accounting    every session warmed BEFORE the clock starts
    same pages                 identical job list replayed per arm? no —
                               pages differ in size, so each arm gets a
                               DIFFERENT slice; sizes are reported so a lucky
                               slice is visible rather than silent

    varying only               1x16 · 2x8 · 4x4

⚠ AND WARM-UP IS EXCLUDED FROM THE TIMED SECTION. The previous run timed
warm() inside the measurement, which penalises whichever arm opens more
sessions — the opposite bias to the batch-size one, and just as wrong.
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
TOTAL_PAGES = 256
TOTAL_CONN = 16


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


async def arm(jobs, nsess, conc):
    """nsess sessions, conc connections each, TOTAL_PAGES split between them."""
    per = len(jobs) // nsess
    fetchers = [afetch.Fetcher(conc) for _ in range(nsess)]
    for f in fetchers:
        await f.__aenter__()
    # ⚠ WARM OUTSIDE THE CLOCK — otherwise more sessions is penalised for
    # nothing, which is how you get the opposite wrong answer.
    for i, f in enumerate(fetchers):
        await f.warm(jobs[i * per][0])

    t0 = time.time()
    chunks = [jobs[i * per:(i + 1) * per] for i in range(nsess)]
    results = await asyncio.gather(
        *(f.fetch_many(c) for f, c in zip(fetchers, chunks)))
    wall = time.time() - t0

    flat = [r for sub in results for r in sub]
    ok = [r for r in flat if r and r.get("ok")]
    saved = save(flat)
    lat = [r["secs"] for r in ok]
    mb = sum(r["bytes"] for r in ok) / 1e6
    for f in fetchers:
        await f.__aexit__()
    return {"sessions": nsess, "conc_each": conc, "total_conn": nsess * conc,
            "pages": len(jobs), "ok": len(ok), "wall": round(wall, 2),
            "req_per_s": round(len(ok) / wall, 2) if wall else 0,
            "mb": round(mb, 1),
            "mb_per_s": round(mb / wall, 2) if wall else 0,
            "mean_lat": round(statistics.mean(lat), 3) if lat else None,
            "saved": saved}


async def main(reps=2):
    jobs = load_jobs()
    print(f"{len(jobs):,} unfetched pages · {TOTAL_PAGES} per arm · "
          f"{TOTAL_CONN} total connections · {reps} reps\n")
    cur = 0
    rows = []
    # ⚠ INTERLEAVE THE REPS. Running all of arm A then all of arm B lets any
    # drift in server load masquerade as an arm effect.
    order = [(1, 16), (2, 8), (4, 4)] * reps
    for nsess, conc in order:
        chunk = jobs[cur:cur + TOTAL_PAGES]
        cur += TOTAL_PAGES
        if len(chunk) < TOTAL_PAGES:
            print("  out of pages")
            break
        r = await arm(chunk, nsess, conc)
        rows.append(r)
        print(f"  {nsess} x {conc:>2}  {r['ok']:>3}/{r['pages']} pages  "
              f"{r['req_per_s']:>6} req/s  {r['mb_per_s']:>5} MB/s  "
              f"lat {r['mean_lat']}  ({r['mb']} MB)")
        await asyncio.sleep(3)

    print(f"\n{'='*66}")
    by = {}
    for r in rows:
        by.setdefault((r["sessions"], r["conc_each"]), []).append(r)
    for k, v in sorted(by.items()):
        rr = [x["req_per_s"] for x in v]
        mm = [x["mb_per_s"] for x in v]
        print(f"  {k[0]} x {k[1]:>2}   req/s {statistics.mean(rr):>6.2f}  "
              f"MB/s {statistics.mean(mm):>5.2f}  (n={len(v)}, "
              f"range {min(rr)}-{max(rr)})")
    # ⚠ COMPARE ON MB/s, NOT req/s. Pages vary 20-80 KB, so a slice of light
    # pages inflates req/s. Bytes moved is the honest unit.
    best = max(by.items(), key=lambda kv: statistics.mean(x["mb_per_s"] for x in kv[1]))
    worst = min(by.items(), key=lambda kv: statistics.mean(x["mb_per_s"] for x in kv[1]))
    spread = (statistics.mean(x["mb_per_s"] for x in best[1]) /
              statistics.mean(x["mb_per_s"] for x in worst[1]))
    print(f"\n  spread on BYTES: {spread:.2f}x   best {best[0][0]}x{best[0][1]}")
    if spread < 1.2:
        print("  -> distribution does NOT matter. The earlier 2.81x was the\n"
              "     batch-size confound, not a session effect.")
    else:
        print(f"  -> distribution DOES matter, {spread:.2f}x on bytes moved.")
    print(f"  {sum(r['saved'] for r in rows)} pages saved")
    json.dump(rows, open("_dist_clean.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2))
