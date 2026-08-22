"""HOW BIG IS ACRIS, ACTUALLY? Sample-map the big types and stop guessing.

⚠ THE 190 MILLION PAGE FIGURE IS A GUESS AND EVERY PLAN RESTS ON IT. It was
built by multiplying citywide type counts against per-type page means measured
on ONE PARCEL — lot 49, a commercial assemblage whose mortgages and agreements
are far longer than a typical filing. Every type since measured properly has
come in lower, some by 4x:

    type        guessed    measured
    EASE          42.0       10.5
    ZONE           6.5        4.7
    DEVR          51.8       36.2

The corpus is dominated by DEED, MTGE, SAT and ASST — 12.7M of 17M documents —
and a satisfaction of mortgage is one to three pages, not eleven. If the true
mean is 7 rather than 11, acquisition drops from 80 days to about 50 for the
same work.

⚠ SAMPLE, NOT CENSUS, AND SAY SO. Mapping all 17M is 24 hours; mapping 500 per
type is under a minute and gets the mean to within a few percent. What it
CANNOT do is tell you the tail — one 900-page declaration among 500 samples
swings a mean badly — so the median is reported alongside, and any type whose
mean and median diverge wildly is flagged as needing a full census.

⚠ THE SAMPLE IS NOT RANDOM. Socrata returns rows ordered by :id, which
correlates with recording sequence, so a head-sample skews old. Three windows
are taken across the id range instead — still not random, but not one era.
"""
import asyncio
import json
import pathlib
import statistics
import sys
import time

import amap
import bulk
import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MASTER = "bnx9-e6tj"
CACHE = pathlib.Path("census_maps.jsonl")


def sample_ids(doc_type, total, per_type=450):
    """Three windows across the id range — head, middle, tail."""
    out, seen = [], set()
    k = max(per_type // 3, 1)
    for frac in (0.0, 0.45, 0.9):
        off = int(total * frac)
        try:
            rows = bulk.socrata(MASTER, where=f"doc_type='{doc_type}'",
                                select="document_id", limit=k, offset=off,
                                order="document_id", paginate=False)
        except Exception as e:
            print(f"    window {frac}: {type(e).__name__}")
            continue
        for r in rows:
            d = r["document_id"]
            if d not in seen:
                seen.add(d)
                out.append(d)
    return out


async def map_sample(ids, conc=16):
    import aiohttp
    res, stop = [], asyncio.Event()
    sem = asyncio.Semaphore(conc)
    conn = aiohttp.TCPConnector(limit=conc, limit_per_host=conc)
    async with aiohttp.ClientSession(connector=conn,
                                     headers={"User-Agent": amap.UA},
                                     timeout=aiohttp.ClientTimeout(total=60)) as s:
        async def one(d):
            if stop.is_set():
                return
            async with sem:
                try:
                    async with s.get(amap.VIEW + d) as r:
                        body = await r.read()
                        ct = r.headers.get("Content-Type", "")
                except Exception:
                    return
                try:
                    fetch_pages._check_denied(body, ct)
                except fetch_pages.AccessDenied:
                    stop.set()
                    print("    ⚠ REFUSED — stopping.")
                    return
                m = amap.parse(body.decode("utf-8", "ignore"), d)
                if m.get("hid_TotalPages"):
                    res.append(m)
        await asyncio.gather(*(one(d) for d in ids))
    return res


async def main(types):
    counts = {r["doc_type"]: int(r["n"]) for r in
              bulk.socrata(MASTER, select="doc_type,count(1) as n",
                           group="doc_type", paginate=True)}
    out, fh = [], open(CACHE, "a", encoding="utf-8")
    print(f"{'type':<10}{'docs':>11}{'sampled':>9}{'mean':>7}{'median':>8}"
          f"{'p90':>6}{'-> pages':>14}")
    for t in types:
        n_docs = counts.get(t, 0)
        if not n_docs:
            continue
        ids = sample_ids(t, n_docs)
        t0 = time.time()
        maps = await map_sample(ids)
        for m in maps:
            m["doc_type"] = t
            fh.write(json.dumps(m) + "\n")
        pg = sorted(m["hid_TotalPages"] for m in maps)
        if not pg:
            print(f"{t:<10}{n_docs:>11,}{0:>9}  (no maps)")
            continue
        mean, med = statistics.mean(pg), statistics.median(pg)
        p90 = pg[int(len(pg) * .9) - 1]
        est = mean * n_docs
        out.append({"type": t, "docs": n_docs, "sampled": len(pg),
                    "mean": round(mean, 1), "median": med, "p90": p90,
                    "est_pages": int(est), "secs": round(time.time() - t0, 1)})
        flag = "  ⚠ skewed" if mean > med * 2 else ""
        print(f"{t:<10}{n_docs:>11,}{len(pg):>9}{mean:>7.1f}{med:>8.0f}"
              f"{p90:>6}{est:>14,.0f}{flag}")
    fh.close()

    tot_docs = sum(r["docs"] for r in out)
    tot_pg = sum(r["est_pages"] for r in out)
    print(f"\n{'='*72}")
    print(f"  {tot_docs:,} documents  ->  {tot_pg:,.0f} pages "
          f"(mean {tot_pg/max(tot_docs,1):.1f} pages/doc)")
    print(f"  vs the 190,000,000 page guess: {tot_pg/190e6:.2f}x")
    for rate, lbl in ((28, "28 req/s"), (32, "32 req/s")):
        print(f"  acquire at {lbl:<10} {tot_pg/rate/86400:>6.0f} days")
    print(f"  storage as TIFF   {tot_pg*53/1e9:,.1f} TB")
    json.dump(out, open("_corpus_census.json", "w"), indent=1)
    print("\n  ⚠ SAMPLE, not census. Medians shown so a long-tail type cannot")
    print("    quietly inflate a mean. Types flagged skewed need a full map.")


if __name__ == "__main__":
    T = sys.argv[1:] or ["DEED", "MTGE", "SAT", "ASST", "PAT", "AGMT",
                         "RPTT&RET", "RPTT", "AL&R", "REL", "MORTGAGE", "UCC1"]
    asyncio.run(main(T))
