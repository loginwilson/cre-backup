"""THE STRATIFIED SAMPLE — the run that decides whether to rent the cores.

Everything measured on 2026-08-10 came from two accidents of what happened to be
on disk: 1,180 DEVRs (all 2003+, 90% Manhattan) and 52 mixed documents (almost
all 2010+). Every conclusion drawn from them is therefore a conclusion about
modern Manhattan paper, and each time that sample was extrapolated it broke:

    a field map learned on a 2014 cover page bound the FILING FEE on 150
    consecutive 2003 pages, at 96% OCR confidence, silently

    a trigger lexicon written from one document scored 25/25 on that document
    and missed a real clause on page 15 of the SAME document

    "Tesseract cannot read microfilm" was concluded from 13 pages fed in raw,
    and became false the moment the film frame was cropped off

So this pulls a small, DELIBERATELY SPREAD sample: N documents for every
combination of document type and era, so that each measurement has a denominator
and nothing is generalised from whatever arrived first.

WHAT IT UNBLOCKS, all three of which are currently unmeasured:

    LAYER 1  OCR accuracy per type and per era      is the text close enough
    LAYER 2  trigger calibration per type           does a lexicon generalise
    LAYER 3  cross-document reference formats       how does a 1979 instrument
                                                    cite a 1978 mortgage

⚠ IT QUEUES BEHIND THE MAP AND FIRES BY ITSELF. AcrisLock(wait=True) blocks
until the mapper releases, so this can be started now and left. Do not "help" it
by stopping the map: 1,076 sockets in TIME_WAIT once made a local resource
exhaustion look exactly like an ACRIS refusal, and an hour went into diagnosing
the wrong host.

⚠ ON A REFUSAL IT STOPS DEAD. No retry, no backoff, no rotation. Three refusals
in fifty minutes on 2026-08-05 all came from treating the first one as a puzzle
to route around.

⚠ INSTRUMENT PAGES ONLY. The map says where the instrument ends and supporting
documents begin, so nothing is fetched blind. Range-scanning to find an exhibit
is the technique that got this project cut off in the first place.

    python stratified_sample.py --plan     show the cells, pull nothing
    python stratified_sample.py            select, map, fetch (waits for the lock)
"""
import asyncio
import collections
import concurrent.futures as cf
import json
import os
import pathlib
import sys
import time

import acris_lock
import afetch
import amap
import bulk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MASTER = "bnx9-e6tj"
OUT = pathlib.Path("sample_pages")
PLAN = pathlib.Path("_sample_plan.json")
STATE = pathlib.Path("_sample_state.json")

PER_CELL = int(os.environ.get("PER_CELL", 20))
WORKERS = 8            # measured: bytes flat from 8 to 32 while latency doubled
MAP_CONC = 32          # small job; no reason to open a wide pool

# ── EVERY type, pulled live ─────────────────────────────────────────────
# ⚠ NOT A HAND-PICKED LIST ANY MORE. The first version named 14 types chosen
# for volume and "signal", and that choice was itself a hypothesis about where
# the interesting documents are. The DEVR survey then found SEVEN distinct
# instrument mechanisms filed under ONE type — a party wall covenant, a §98-33
# special district transfer, corrections, amendments — none of which the type
# label predicted. If the label does not predict the instrument, then choosing
# types by their labels selects for nothing except my expectations.
#
# So: all 95, and let the empty cells report themselves.
def all_types():
    rows = bulk.socrata(MASTER, select="doc_type,count(1) as n",
                        group="doc_type", paginate=True)
    return [r["doc_type"] for r in
            sorted(rows, key=lambda r: -int(r["n"])) if r.get("doc_type")]

# ── eras ────────────────────────────────────────────────────────────────
# ⚠ THE ERA BOUNDARIES ARE WHERE THINGS BREAK, NOT THE TYPES. Cover-page
# layouts clustered 2013-2026 and 2004-2013 with 2003 stragglers; OCR
# confidence fell off a cliff at the microfilm boundary and nowhere else.
ERAS = [
    ("film",   "starts_with(document_id,'FT_')"),
    ("pre90",  "not starts_with(document_id,'FT_') "
               "AND recorded_datetime < '1990-01-01T00:00:00.000'"),
    ("90s",    "recorded_datetime between '1990-01-01T00:00:00.000' "
               "and '1999-12-31T23:59:59.000'"),
    ("00s",    "recorded_datetime between '2000-01-01T00:00:00.000' "
               "and '2009-12-31T23:59:59.000'"),
    ("2010+",  "recorded_datetime >= '2010-01-01T00:00:00.000'"),
]


def select(TYPES):
    """One cell per (type, era). Candidates are spread, not taken off the top.

    ⚠ $order IS NOT OPTIONAL. $offset paging without it silently duplicated and
    dropped rows on this API — 199,888 rows came back with only 199,679 distinct
    ids, and two runs an hour apart disagreed. bulk.socrata now defaults it, but
    the spreading below also depends on a stable order to mean anything.
    """
    plan = {}
    for t in TYPES:
        for era, where in ERAS:
            w = f"doc_type='{t}' AND ({where})"
            try:
                rows = bulk.socrata(MASTER, where=w,
                                    select="document_id,recorded_datetime",
                                    limit=600, paginate=False)
            except Exception as e:
                print(f"  {t:<9} {era:<6} query failed: {str(e)[:50]}")
                continue
            if not rows:
                continue
            # ⚠ SPREAD, DO NOT TAKE THE FIRST N. Ids are ordered, so the first
            # ten share a recording day, a borough and often one title company —
            # which is exactly the homogeneity that made a lexicon built from
            # one document look complete.
            step = max(1, len(rows) // PER_CELL)
            picked = [rows[i]["document_id"] for i in range(0, len(rows), step)][:PER_CELL]
            plan[f"{t}|{era}"] = picked
    PLAN.write_text(json.dumps(plan, indent=1))
    return plan


def show(plan, TYPES):
    eras = [e for e, _ in ERAS]
    print(f"\n{'type':<10}" + "".join(f"{e:>8}" for e in eras) + f"{'total':>8}")
    print("-" * (10 + 8 * len(eras) + 8))
    grand = 0
    for t in TYPES:
        row = [len(plan.get(f"{t}|{e}", [])) for e in eras]
        grand += sum(row)
        if sum(row):
            print(f"{t:<10}" + "".join(f"{n:>8}" for n in row) + f"{sum(row):>8}")
    print("-" * (10 + 8 * len(eras) + 8))
    tot = [sum(len(plan.get(f"{t}|{e}", [])) for t in TYPES) for e in eras]
    print(f"{'ALL':<10}" + "".join(f"{n:>8}" for n in tot) + f"{grand:>8}")
    empty = [k for k in (f"{t}|{e}" for t in TYPES for e, _ in ERAS)
             if not plan.get(k)]
    if empty:
        print(f"\n  {len(empty)} empty cells (type did not exist in that era) — "
              f"expected for DEVR, ZONE and the tax types")
    return grand


async def acquire(plan):
    ids = sorted({d for v in plan.values() for d in v})
    print(f"\nmapping {len(ids):,} documents")
    await amap.run(ids, conc=MAP_CONC)

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
                if r.get("doc_id") in set(ids):
                    maps[r["doc_id"]] = r

    jobs, noimg = [], 0
    for d in ids:
        m = maps.get(d)
        if not m:
            continue
        tot = m.get("hid_TotalPages")
        # ⚠ THREE STATES. >0 normal, ==0 and <0 BOTH mean no image exists.
        # `if not tot` once scored 0 a parse failure and stalled a run for two
        # hours; `if tot` treated -1 as truthy and wrote 19,570 ranges of [1,-1].
        if tot is None or tot <= 0:
            noimg += 1
            continue
        rng = m.get("instrument") or [1, tot]
        lo, hi = rng[0], rng[1]
        if hi < lo:
            continue
        for p in range(lo, hi + 1):
            jobs.append((d, p))
    print(f"  {len(jobs):,} instrument pages · {noimg} documents have no image")
    if not jobs:
        return

    OUT.mkdir(exist_ok=True)
    writer = cf.ThreadPoolExecutor(4)
    f = afetch.Fetcher(WORKERS)
    await f.__aenter__()
    saved, t0 = 0, time.time()
    try:
        await f.warm(jobs[0][0])
        i = 0
        while i < len(jobs):
            b = jobs[i:i + WORKERS * 6]
            i += len(b)
            sem = asyncio.Semaphore(WORKERS)
            res = await asyncio.gather(*(f.page(d, p, sem) for d, p in b))
            if any(r and r.get("err") == "REFUSED" for r in res):
                print(f"\n  ⚠ REFUSED after {saved:,} pages — stopping. No retry.")
                break
            # ⚠ WRITE OFF THE FETCH LOOP. Measured 2026-08-10: writing 48
            # TIFFs synchronously between batches — each with its own mkdir
            # syscall — held throughput at 12.1 pg/s while the network alone
            # measured 25.7 pg/s. Half the run was the disk, and it looked
            # exactly like a slow link.
            good = [r for r in res if r and r.get("ok")]
            for r in good:
                (OUT / r["doc"]).mkdir(parents=True, exist_ok=True)
            list(writer.map(lambda r: (OUT / r["doc"] /
                                       f"p{r['page']:03d}.tif").write_bytes(r["data"]),
                            good))
            saved += len(good)
            if saved and saved % 400 < WORKERS * 6:
                el = time.time() - t0
                print(f"    {saved:,}/{len(jobs):,}  {saved/el:.1f} pg/s", flush=True)
    finally:
        await f.__aexit__()
    el = time.time() - t0
    print(f"\n  {saved:,} pages in {el/60:.1f} min ({saved/max(el,1):.1f} pg/s)")
    sz = sum(x.stat().st_size for x in OUT.rglob("*.tif"))
    print(f"  {OUT}/ now {sz/1e6:.0f} MB")
    STATE.write_text(json.dumps({"saved": saved, "at": time.time()}))


async def main():
    TYPES = all_types()
    print(f'{len(TYPES)} document types live in ACRIS')
    plan = json.loads(PLAN.read_text()) if PLAN.exists() else select(TYPES)
    n = show(plan, TYPES)
    if "--plan" in sys.argv:
        print("\n  --plan given: nothing fetched.")
        return
    print(f"\n  {n} documents to acquire.")
    print("  " + acris_lock.status())
    with acris_lock.AcrisLock("stratified_sample", wait=True):
        await acquire(plan)


if __name__ == "__main__":
    asyncio.run(main())
