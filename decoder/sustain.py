"""TWO TESTS THE EARLIER ONES GOT WRONG.

⚠ TEST 1 — SESSION DISTRIBUTION AT CONSTANT TOTAL CONNECTIONS.

session_scale.py compared 1 session x 16 against 2 sessions x 16 EACH — 32
total connections against a ceiling already measured at ~16. It then reported
"0.80x, therefore per-client". That conclusion may be right, but the experiment
could not have shown anything else: the two-session arm was over the ceiling
before it started. THE COMPARISON MUST HOLD TOTAL CONNECTIONS FIXED.

    1 session  x 16 conc  = 16 total
    2 sessions x  8 conc  = 16 total
    4 sessions x  4 conc  = 16 total

If all three match, sessions are irrelevant and the limit is per-client — this
time actually demonstrated. If splitting wins, the limit is per-session.

⚠ TEST 2 — SUSTAINED, NOT BURST. Every acquisition number today came from 48 to
200 request bursts lasting a couple of seconds. A server that throttles
gradually, or a cache that fills, would be invisible at that timescale, and the
58-day corpus estimate assumes a burst rate holds for eight weeks. That has
never been checked for even one minute.

Throughput is reported per 15-second window so DECAY IS VISIBLE rather than
averaged away.

⚠ PAGES ARE KEPT. These are real DEVR instrument pages the project needs; the
tests do genuine work rather than spending the heavy endpoint on measurement.
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


def save(results):
    n = 0
    for r in results:
        if r and r.get("ok"):
            dd = OUT / r["doc"]
            dd.mkdir(parents=True, exist_ok=True)
            (dd / f"p{r['page']:03d}.tif").write_bytes(r["data"])
            fetch_budget.note_fetch(r["doc"], r["page"])
            n += 1
    return n


async def one_session(jobs, conc, stats, label):
    async with afetch.Fetcher(conc) as f:
        await f.warm(jobs[0][0])
        t0 = time.time()
        res = await f.fetch_many(jobs)
        wall = time.time() - t0
    ok = [r for r in res if r and r.get("ok")]
    stats[label] = {"ok": len(ok), "wall": round(wall, 2),
                    "req_per_s": round(len(ok) / wall, 2) if wall else 0,
                    "mean_lat": round(statistics.mean([x["secs"] for x in ok]), 3)
                    if ok else None}
    return res


async def test_distribution(jobs, total=16, per_arm=64):
    print(f"TEST 1 · session distribution at {total} TOTAL connections\n")
    cursor = 0
    rows = []
    for nsess in (1, 2, 4):
        conc = total // nsess
        stats = {}
        arms = []
        for i in range(nsess):
            chunk = jobs[cursor:cursor + per_arm]
            cursor += per_arm
            arms.append(one_session(chunk, conc, stats, f"s{i}"))
        t0 = time.time()
        results = await asyncio.gather(*arms)
        wall = time.time() - t0
        saved = sum(save(r) for r in results)
        tot_ok = sum(stats[k]["ok"] for k in stats)
        lat = [stats[k]["mean_lat"] for k in stats if stats[k]["mean_lat"]]
        rows.append({"sessions": nsess, "conc_each": conc, "total": total,
                     "ok": tot_ok, "wall": round(wall, 2),
                     "req_per_s": round(tot_ok / wall, 2),
                     "mean_lat": round(statistics.mean(lat), 3) if lat else None})
        print(f"  {nsess} session(s) x {conc:>2} conc = {total}  "
              f"{tot_ok:>4} pages  {tot_ok/wall:>6.2f} req/s  "
              f"lat {rows[-1]['mean_lat']}  ({saved} saved)")
        await asyncio.sleep(3)
    base = rows[0]["req_per_s"]
    spread = max(r["req_per_s"] for r in rows) / min(r["req_per_s"] for r in rows)
    print(f"\n  spread across distributions: {spread:.2f}x")
    if spread < 1.2:
        print("  -> SESSIONS ARE IRRELEVANT. The limit is per-client, and this\n"
              "     time the experiment could actually have shown otherwise.")
    else:
        best = max(rows, key=lambda r: r["req_per_s"])
        print(f"  -> distribution matters: {best['sessions']} x {best['conc_each']} "
              f"wins at {best['req_per_s']} req/s")
    return rows, cursor


async def test_sustained(jobs, start, conc, seconds=90):
    print(f"\nTEST 2 · sustained at {conc} concurrent for {seconds}s")
    windows, saved_total = [], 0
    t_start = time.time()
    cursor = start
    async with afetch.Fetcher(conc) as f:
        await f.warm(jobs[cursor][0])
        while time.time() - t_start < seconds:
            chunk = jobs[cursor:cursor + conc * 8]
            if not chunk:
                break
            cursor += len(chunk)
            w0 = time.time()
            res = await f.fetch_many(chunk)
            wall = time.time() - w0
            ok = [r for r in res if r and r.get("ok")]
            saved_total += save(res)
            windows.append({"t": round(time.time() - t_start, 1),
                            "req_per_s": round(len(ok) / wall, 2),
                            "lat": round(statistics.mean([x["secs"] for x in ok]), 3)
                            if ok else None})
            if any(r and r.get("err") == "REFUSED" for r in res):
                print("  ⚠ REFUSED — stopping.")
                break
    for w in windows:
        print(f"    t+{w['t']:>5}s   {w['req_per_s']:>6} req/s   lat {w['lat']}")
    rates = [w["req_per_s"] for w in windows]
    if len(rates) >= 3:
        first, last = statistics.mean(rates[:2]), statistics.mean(rates[-2:])
        print(f"\n  first windows {first:.1f} -> last {last:.1f} req/s "
              f"({last/first:.2f}x)")
        # ⚠ THIS IS THE NUMBER THE 58-DAY ESTIMATE DEPENDS ON.
        if last / first < 0.85:
            print("  ⚠ DECAY. The burst rate does NOT hold. Every long-run\n"
                  "    estimate built on it is optimistic.")
        else:
            print("  -> holds. Burst rate is a fair basis for long runs.")
    print(f"  {saved_total} pages saved")
    return windows, cursor


async def main():
    jobs = load_jobs()
    print(f"{len(jobs):,} unfetched DEVR instrument pages available\n")
    rows, cur = await test_distribution(jobs)
    await asyncio.sleep(3)
    w12, cur = await test_sustained(jobs, cur, 12, 90)
    await asyncio.sleep(5)
    w16, cur = await test_sustained(jobs, cur, 16, 90)
    json.dump({"distribution": rows, "sustained_12": w12, "sustained_16": w16},
              open("_sustain.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main())
