"""CONCURRENT MAPPING — because the 6-second pause was invented, not measured.

⚠ MY ERROR, AND IT COST TWO HOURS. docmap.probe() paced at 6s between map
loads. That number was picked before anything had been measured, at a time when
this project believed ACRIS was rate-limiting it — a belief that turned out to
be a missing cookie jar. Maps answer in ~0.3s and are 13 KB of HTML.

    sequential at 6s     1,201 maps  =  2 hours
    16 concurrent        1,201 maps  =  ~25 seconds

⚠ A PACE THAT WAS NEVER MEASURED IS NOT A SAFETY MARGIN, IT IS A GUESS WEARING
ONE. The honest way to be gentle is to measure the ceiling and sit below it,
which is exactly what the fetch ramp did — and this reuses that answer (16
concurrent peaked; 24 degraded) rather than inventing a new number.

⚠ CHECKPOINTS EVERY RESULT. The predecessor accumulated maps in memory and
wrote once at the end, so an interrupted run persisted nothing — 762 maps were
in flight and 321 on disk when this was written, and the rest had to be
recovered by re-parsing a log file.
"""
import asyncio
import json
import pathlib
import re
import sys
import time
import urllib.parse

import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id="
CACHE = pathlib.Path("docmaps.jsonl")
CONC = 8          # ⚠ WAS 16 AND IT TRIPPED THE SERVER (2026-08-18).
                  # 12,077 documents at conc 16 (~48/s), cold, no Referer, no
                  # gate -> ACRIS served its "Bandwidth Notice" at every URL,
                  # HTTP 200, and Login had to clear it. Acquisition sustains
                  # 4 procs x conc 20 at 93.8 pg/s for DAYS without a trip, so
                  # it was never the rate — it was the CLIENT. Match
                  # acquire_async.py: conc 8, seeded session, Referer.


def parse(html, doc_id):
    m = {"doc_id": doc_id}
    for fld in ("hid_Cov", "hid_Sup", "hid_Tax"):
        mm = re.search(rf'name="{fld}"[^>]*value="([^"]*)"', html)
        v = mm.group(1).strip() if mm else ""
        m[fld] = int(v) if v.isdigit() else None
    # ⚠ hid_TotalPages IS ONLY IN THE FRAME SRC, URL-ENCODED. Not a form field.
    fm = re.search(r'searchCriteriaStringValue=([^"&\']+)', html)
    tot = None
    if fm:
        try:
            tot = json.loads(urllib.parse.unquote(fm.group(1))).get("hid_TotalPages")
        except Exception:
            t2 = re.search(r'TotalPages%22%3A(\d+)', html)
            tot = int(t2.group(1)) if t2 else None
    m["hid_TotalPages"] = tot
    # ⚠ THREE STATES, NOT TWO. Measured over 5.4M maps:
    #     positive  97.65%  normal, acquire pages 1..N
    #     0          1.99%  RTXL almost entirely — no image exists
    #    -1          0.36%  microfilm-era WILL/MMTG/MAPS — also no image
    # Both non-positive states return ACRIS's PLACEHOLDER image (13,684 bytes,
    # md5 4081a3f2...), verified live. So they are the same finding: THE INDEX
    # IS ALL THERE WILL EVER BE.
    #
    # The first version tested `if tot:` — which is False for 0 but TRUE for
    # -1, so 19,570 documents were written with an instrument range of [1, -1],
    # an empty span that reads as valid. Flag them instead of computing
    # nonsense, so acquisition can skip them by intent rather than by accident.
    if tot is not None and tot <= 0:
        m["no_image"] = True
        m["instrument"] = None
    if tot and tot > 0:
        sup, tax, cov = m["hid_Sup"] or 0, m["hid_Tax"] or 0, m["hid_Cov"] or 0
        after = [x for x in (sup, tax) if x]
        m["instrument"] = [cov + 1, (min(after) - 1) if after else tot]
        m["instrument_pages"] = m["instrument"][1] - m["instrument"][0] + 1
        m["supporting"] = [sup, tot] if sup else None
        m["tax_return"] = tax or None
    return m


async def run(doc_ids, conc=CONC):
    import aiohttp
    done = set()
    if CACHE.exists():
        for line in CACHE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["doc_id"])
    todo = [d for d in doc_ids if d not in done]
    print(f"{len(done):,} already mapped · {len(todo):,} to go · {conc} concurrent")
    if not todo:
        return
    stop = asyncio.Event()
    sem = asyncio.Semaphore(conc)
    out = open(CACHE, "a", encoding="utf-8")
    lock = asyncio.Lock()
    t0, n_ok, n_err = time.time(), 0, 0

    conn = aiohttp.TCPConnector(limit=conc, limit_per_host=conc)
    async with aiohttp.ClientSession(connector=conn,
                                     headers={"User-Agent": UA},
                                     timeout=aiohttp.ClientTimeout(total=60)) as s:
        # ⚠ SEED THE SESSION BEFORE ASKING FOR ANYTHING. session_fetch.py
        # measured this exactly: cold urllib at ONE request per 25s was refused
        # at request 5, while a real session at 40x the rate had zero refusals —
        # "it was never a rate limit, the difference is the client". This file's
        # own docstring already suspected "a missing cookie jar"; it never
        # actually seeded one.
        async with s.get("https://a836-acris.nyc.gov/DS/DocumentSearch/") as r:
            body = await r.read()
            if b"Bandwidth Notice" in body:
                raise SystemExit("  ⚠ ACRIS Bandwidth Notice on the landing page "
                                 "— REFUSED before we started. Do not retry.")
        await asyncio.sleep(1.0)
        async def one(d):
            nonlocal n_ok, n_err
            if stop.is_set():
                return
            async with sem:
                try:
                    async with s.get(VIEW + d, headers={
                            "Referer": VIEW + d}) as r:
                        body = await r.read()
                        ct = r.headers.get("Content-Type", "")
                except Exception:
                    n_err += 1
                    return
                try:
                    fetch_pages._check_denied(body, ct)
                except fetch_pages.AccessDenied:
                    stop.set()                      # ⚠ everything halts
                    print("  ⚠ REFUSED — stopping the map. No retry.")
                    return
                m = parse(body.decode("utf-8", "ignore"), d)
                # ⚠ SAME FALSY-ZERO BUG AS map_acris.py — see the note there.
                # 0 pages means an index-only document; it must be RECORDED so
                # it is marked done, not counted as an error forever.
                if m["hid_TotalPages"] is None:
                    n_err += 1
                    return
                async with lock:                    # ⚠ persist immediately
                    out.write(json.dumps(m) + "\n")
                    out.flush()
                    n_ok += 1
                    if n_ok % 100 == 0:
                        el = time.time() - t0
                        print(f"    {n_ok:,} mapped  {n_ok/el:.1f}/s  "
                              f"({el:.0f}s elapsed)")
        await asyncio.gather(*(one(d) for d in todo))
    out.close()
    el = time.time() - t0
    print(f"\n  {n_ok:,} mapped in {el:.0f}s ({n_ok/max(el,.001):.1f}/s), {n_err} failed")


if __name__ == "__main__":
    wl = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "worklist_DEVR.json"))
    asyncio.run(run([r["document_id"] for r in wl]))
    pg = [json.loads(l)["hid_TotalPages"] for l in
          CACHE.read_text(encoding="utf-8").splitlines() if l.strip()]
    import statistics
    print(f"  {len(pg):,} maps · mean {statistics.mean(pg):.1f} pages · "
          f"total {sum(pg):,} pages for the mapped set")
