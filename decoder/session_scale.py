"""IS THE CEILING PER-SESSION OR PER-CLIENT? A diagnostic, run on the cheap
endpoint.

⚠ WHY THIS IS BEING MEASURED RATHER THAN ASSUMED. Earlier today this project
declined to test something on the belief that it would be circumvention, and
separately built an entire rate-limit theory on top of a missing cookie jar.
Both were assumptions dressed as caution. Login's point stands: measure first,
decide second.

THE QUESTION
    Both endpoints peak at ~16 concurrent connections — images at 28 req/s,
    maps at 198 req/s. Same session, same cookie jar. So the CONCURRENCY
    ceiling looks connection-shaped rather than endpoint-shaped. What we do not
    know is what it is attached to:

        PER CLIENT (address / server capacity)
            -> a second session changes nothing. Question closed, no decision
               to make.
        PER SESSION (cookie)
            -> a second session doubles it, and that is a DECISION rather than
               a discovery: N cookies to obtain N budgets is asking a server
               to treat one user as N. That call belongs to whoever owns the
               relationship with the City, made knowingly — not slid into
               because a benchmark looked good.

THE TEST
    A alone at 16 · B alone at 16 · A+B simultaneously at 16 each.

        combined ≈ single   -> per client
        combined ≈ 2x       -> per session

⚠ RUN ON THE MAP ENDPOINT, NOT ON IMAGES. Maps are 13 KB renders, the light
path. Answering a structural question should not cost the heavy endpoint
anything, and this is the gentlest way to ask it.

⚠ AND THE RESULTS ARE DISCARDED. This is a timing measurement; nothing is
harvested.
"""
import asyncio
import json
import statistics
import sys
import time

import amap
import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def make_session(conc):
    """A fresh session: its own connector and its own cookie jar."""
    import aiohttp
    conn = aiohttp.TCPConnector(limit=conc, limit_per_host=conc)
    s = aiohttp.ClientSession(connector=conn, headers={"User-Agent": amap.UA},
                              timeout=aiohttp.ClientTimeout(total=60))
    return s


async def arm(session, ids, conc, label, results):
    sem = asyncio.Semaphore(conc)
    lat, ok, err = [], 0, 0
    t0 = time.time()

    async def one(d):
        nonlocal ok, err
        async with sem:
            t = time.time()
            try:
                async with session.get(amap.VIEW + d) as r:
                    body = await r.read()
                    ct = r.headers.get("Content-Type", "")
            except Exception:
                err += 1
                return
            lat.append(time.time() - t)
            try:
                fetch_pages._check_denied(body, ct)
            except fetch_pages.AccessDenied:
                err += 1
                results[label] = {"refused": True}
                return
            ok += 1
    await asyncio.gather(*(one(d) for d in ids))
    wall = time.time() - t0
    results[label] = {"ok": ok, "err": err, "wall": round(wall, 2),
                      "req_per_s": round(ok / wall, 1) if wall else 0,
                      "mean_lat": round(statistics.mean(lat), 3) if lat else None}


async def main(n=200, conc=16):
    wl = json.load(open("worklist_DEVR.json"))
    ids = [r["document_id"] for r in wl]
    A_ids = (ids * 5)[:n]
    B_ids = (ids * 5)[n:2 * n]

    print(f"per-session vs per-client · {conc} concurrent per session · "
          f"{n} requests per arm · MAP endpoint\n")

    # --- A alone
    res = {}
    sA = await make_session(conc)
    await arm(sA, A_ids, conc, "A_alone", res)
    print(f"  A alone          {res['A_alone']['req_per_s']:>7} req/s  "
          f"lat {res['A_alone']['mean_lat']}")
    await asyncio.sleep(2)

    # --- B alone (a genuinely separate session: new connector, new cookie jar)
    sB = await make_session(conc)
    await arm(sB, B_ids, conc, "B_alone", res)
    print(f"  B alone          {res['B_alone']['req_per_s']:>7} req/s  "
          f"lat {res['B_alone']['mean_lat']}")
    await asyncio.sleep(2)

    # --- A and B at the same time
    t0 = time.time()
    await asyncio.gather(arm(sA, A_ids, conc, "A_both", res),
                         arm(sB, B_ids, conc, "B_both", res))
    wall = time.time() - t0
    combined = (res["A_both"]["ok"] + res["B_both"]["ok"]) / wall
    print(f"  A+B together     {combined:>7.1f} req/s combined  "
          f"(A {res['A_both']['req_per_s']} + B {res['B_both']['req_per_s']})")
    print(f"                   lat A {res['A_both']['mean_lat']} "
          f"B {res['B_both']['mean_lat']}")

    await sA.close()
    await sB.close()

    single = max(res["A_alone"]["req_per_s"], res["B_alone"]["req_per_s"])
    ratio = combined / single if single else 0
    print(f"\n{'='*62}")
    print(f"  single session : {single} req/s")
    print(f"  two sessions   : {combined:.1f} req/s   =  {ratio:.2f}x")
    if ratio < 1.25:
        print("\n  -> PER CLIENT. A second session buys nothing. Question closed;\n"
              "     there is no decision to make and nothing to scale.")
    elif ratio > 1.7:
        print("\n  -> PER SESSION. Sessions scale. ⚠ THIS IS NOW A DECISION, NOT A\n"
              "     FINDING: running N sessions asks the server to treat one user\n"
              "     as N. That is Login's call to make explicitly.")
    else:
        print(f"\n  -> PARTIAL ({ratio:.2f}x). Contended, not cleanly additive —\n"
              "     consistent with shared server capacity rather than a\n"
              "     per-session budget.")
    json.dump(res, open("_session_scale.json", "w"), indent=1)


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 200))
