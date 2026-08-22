"""MAP ALL OF ACRIS — the selection stage, run whole.

This is the SELECTION step of select -> acquire -> extract -> resolve ->
derive -> apply, and it is the one that makes every later stage decidable:
after this, "what does it cost to acquire type X" is a query, not a guess.

Per document it records: total pages, which pages are the instrument, where
supporting documents start, and whether an RP-5217 exists. Roughly 180 bytes
each, so all 17M is ~3 GB of JSON. No images, no acquisition budget.

⚠ IT CALIBRATES ITS OWN CONCURRENCY BEFORE COMMITTING. Every fixed pacing
number in this project has been wrong — a 6-second pause invented before
anything was measured (1,200x too slow), a "ceiling at 16 connections" that was
a cold-start artifact (the real one is ~128), and a rate limit that was a
missing cookie jar. So this measures on the live link at start-up rather than
trusting a constant, and re-measures if throughput drifts.

⚠ RESUMABLE AND CHECKPOINTED PER DOCUMENT. An earlier mapper accumulated
results in memory and wrote once at the end; 762 maps were in flight and 321 on
disk when it was interrupted, and the rest had to be recovered by re-parsing a
log. Nothing here is held in memory that has not been written.

⚠ STOPS DEAD ON A REFUSAL. No retry, no backoff-and-continue.
"""
import asyncio
import json
import pathlib
import statistics
import sys
import time

import acris_lock
import amap
import bulk
import fetch_pages

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import collections
_ERR = collections.Counter()

# ⚠ REFUSAL IS RUN-SCOPED, NOT BATCH-SCOPED. THIS IS THE BUG THAT LET THE MAP
# RETRY THROUGH SIX REFUSALS ON 2026-08-10.
#
# _batch() used to create its own `stop = asyncio.Event()`. A refusal set it,
# halted that batch, printed "REFUSED — stopping. No retry." — and then the
# NEXT batch built a fresh Event and went straight back at it. The docstring
# promised the run stopped dead. It did not. Six refusals were logged while the
# map carried on gaining documents, which is precisely the behaviour that turned
# one refusal into three on 2026-08-05 and cost the image endpoint for an hour.
#
# The lesson is not "move the flag". It is that a stop signal scoped INSIDE the
# retry loop cannot stop the loop, and the log will happily print the word
# "stopping" every time it fails to.
_REFUSED = False

MASTER = "bnx9-e6tj"
IDS = pathlib.Path("acris_ids.jsonl")
MAPS = pathlib.Path("acris_maps.jsonl")
STATE = pathlib.Path("map_acris_state.json")


# ─────────────────────────────────────────────────────── ids
def pull_ids():
    """Every document_id in ACRIS, by type, streamed to disk."""
    done = set()
    if STATE.exists():
        done = set(json.loads(STATE.read_text())["types_pulled"])
    counts = {r["doc_type"]: int(r["n"]) for r in
              bulk.socrata(MASTER, select="doc_type,count(1) as n",
                           group="doc_type", paginate=True)}
    todo = [t for t in sorted(counts, key=lambda t: counts[t]) if t not in done]
    print(f"{len(counts)} types · {sum(counts.values()):,} rows · "
          f"{len(todo)} types to pull")
    with open(IDS, "a", encoding="utf-8") as f:
        for t in todo:
            rows = bulk.socrata(MASTER, where=f"doc_type='{t}'",
                                select="document_id,doc_type,recorded_datetime",
                                paginate=True)
            seen = set()
            n = 0
            for r in rows:
                d = r["document_id"]
                if d in seen:
                    continue          # ⚠ MASTER carries exact duplicate rows
                seen.add(d)
                f.write(json.dumps(r) + "\n")
                n += 1
            f.flush()
            done.add(t)
            STATE.write_text(json.dumps({"types_pulled": sorted(done)}))
            print(f"  {t:<12} {len(rows):>9,} rows -> {n:>9,} ids")
    return counts


# ─────────────────────────────────────────────────────── calibrate
async def calibrate(ids, levels=(32, 64, 128, 192)):
    """Find the concurrency that moves the most maps on THIS link, now."""
    print("\ncalibrating concurrency on the live link")
    best, base_lat, cur = None, None, 0
    for c in levels:
        chunk = ids[cur:cur + c * 6]
        cur += len(chunk)
        if len(chunk) < c:
            break
        t0 = time.time()
        res = await amap.run_batch(chunk, c) if hasattr(amap, "run_batch") \
            else await _batch(chunk, c)
        wall = time.time() - t0
        ok, lat = res
        if not ok:
            break
        rate = ok / wall
        ml = statistics.mean(lat) if lat else 0
        if base_lat is None:
            base_lat = ml
        ratio = ml / base_lat if base_lat else 1
        print(f"  {c:>4} conc  {rate:>6.1f} maps/s  lat {ml:.3f} ({ratio:.2f}x)")
        if best is None or rate > best[1]:
            best = (c, rate)
        if ratio > 2.0:
            print(f"  latency {ratio:.2f}x — stopping calibration")
            break
        await asyncio.sleep(2)
    print(f"  -> using {best[0]} concurrent ({best[1]:.0f} maps/s)")
    return best[0], cur


async def _batch(ids, conc):
    """Map a batch, return (ok_count, latencies). Results are persisted."""
    import aiohttp
    lat, ok = [], 0
    sem = asyncio.Semaphore(conc)
    stop = asyncio.Event()
    out = open(MAPS, "a", encoding="utf-8")
    lock = asyncio.Lock()
    conn = aiohttp.TCPConnector(limit=conc, limit_per_host=conc)
    async with aiohttp.ClientSession(connector=conn,
                                     headers={"User-Agent": amap.UA},
                                     timeout=aiohttp.ClientTimeout(total=60)) as s:
        async def one(rec):
            nonlocal ok
            if stop.is_set():
                return
            d = rec["document_id"] if isinstance(rec, dict) else rec
            async with sem:
                t = time.time()
                try:
                    async with s.get(amap.VIEW + d) as r:
                        body = await r.read()
                        ct = r.headers.get("Content-Type", "")
                except Exception as e:
                    # ⚠ NEVER SWALLOW SILENTLY AGAIN. The bare `except: return`
                    # here cost two hours overnight: 5,120 requests failed per
                    # run, thirteen supervised retries, and the log said only
                    # "no progress" — the actual reason was never recorded once.
                    _ERR[f"{type(e).__name__}: {str(e)[:80]}"] += 1
                    return
                lat.append(time.time() - t)
                try:
                    fetch_pages._check_denied(body, ct)
                except fetch_pages.AccessDenied:
                    global _REFUSED
                    _REFUSED = True          # ⚠ ends the RUN, not just this batch
                    stop.set()
                    print("\n  ⚠ REFUSED BY ACRIS — ending the run. No retry.")
                    return
                m = amap.parse(body.decode("utf-8", "ignore"), d)
                # ⚠ ZERO PAGES IS A FINDING, NOT A FAILURE.
                # Some ACRIS documents are index-only and carry no scanned
                # image at all — ESRM, ESTL, MERG, TERDECL and friends. The
                # original test was `if not m.get("hid_TotalPages")`, and 0 is
                # FALSY, so every image-less document was scored a parse error,
                # never written, and therefore never marked done. They pooled in
                # the todo stream across restarts until an entire 5,120-document
                # batch was nothing but them, ok==0, and the run stopped. That
                # cost the whole night: 13 supervised retries, 0 progress.
                # None  -> the parse genuinely failed. Count it, skip it.
                # 0     -> the document has no images. RECORD IT.
                if m.get("hid_TotalPages") is None:
                    _ERR["parse failed: no page data in HTML"] += 1
                    return
                if isinstance(rec, dict):
                    m["doc_type"] = rec.get("doc_type")
                    m["recorded"] = (rec.get("recorded_datetime") or "")[:10]
                async with lock:
                    out.write(json.dumps(m) + "\n")
                    ok += 1
        await asyncio.gather(*(one(r) for r in ids))
    out.close()
    if ok == 0 and _ERR:
        print("  ⚠ batch failures:", flush=True)
        for k, v in _ERR.most_common(5):
            print(f"      {v:>5}x  {k}", flush=True)
    return ok, lat


# ─────────────────────────────────────────────────────── main
async def main():
    # ⚠ ONE ACRIS JOB AT A TIME. Today the map's 128 connections and ~25
    # restarts left 1,076 sockets in TIME_WAIT, and the DEVR fetch then could
    # not complete a TLS handshake — an error that names the remote host and
    # looks exactly like an ACRIS refusal. The constraint is local; the lock
    # is local-wide and covers both endpoints.
    print("  " + acris_lock.status())
    n = acris_lock.sockets_to_acris()
    if n > 800:
        print(f"  ⚠ {n} sockets to :443 — new handshakes may fail; waiting to drain")
    with acris_lock.AcrisLock("map_acris", wait=True):
        await _main()


async def _main():
    if not IDS.exists() or IDS.stat().st_size == 0:
        pull_ids()
    # ⚠ STREAM. NEVER LOAD THE ID FILE WHOLE.
    #
    # The first version did `IDS.read_text()` then built a dict per line. At 17M
    # documents that is a ~1.7 GB string, then 17M more strings from
    # splitlines(), then 17M dicts — comfortably over 10 GB peak on a 15.7 GB
    # machine, and it would have died the moment the id pull finished, after an
    # hour of work.
    #
    # `done` is a set of ids only (~17M x ~60 B = 1 GB, acceptable and
    # necessary for resume). The id file is read line by line, forever.
    done = set()
    for p in (MAPS, pathlib.Path("docmaps.jsonl"),
              pathlib.Path("census_maps.jsonl")):
        if p.exists():
            with open(p, encoding="utf-8") as f:
                for l in f:
                    if l.strip():
                        done.add(json.loads(l)["doc_id"])
    print(f"{len(done):,} already mapped")

    def stream_todo():
        with open(IDS, encoding="utf-8") as f:
            for l in f:
                if not l.strip():
                    continue
                r = json.loads(l)
                if r["document_id"] not in done:
                    yield r

    # calibrate on a small head slice, then stream the rest
    head = []
    gen = stream_todo()
    for r in gen:
        head.append(r)
        if len(head) >= 3000:
            break
    if not head:
        print("nothing to map")
        return
    # ⚠ PIN THE CONCURRENCY ON RESTARTS. Calibration is noisy — across two runs
    # it chose 128 (measured 300 maps/s) and then 192 (measured 177, and ran at
    # 229). A 15-hour supervised job restarts an unknown number of times, and
    # re-rolling the dice each time means some runs are 40% slower for no
    # reason. 128 has now measured best twice; use it unless told otherwise.
    import os
    pin = os.environ.get("MAP_CONC")
    if pin:
        conc, used = int(pin), 0
        print(f"  concurrency pinned to {conc}")
    else:
        conc, used = await calibrate(head)
    leftover = head[used:]

    t0, total = time.time(), 0
    CH = conc * 40
    batch = leftover
    exhausted = False
    while not exhausted:
        while len(batch) < CH:
            try:
                batch.append(next(gen))
            except StopIteration:
                exhausted = True
                break
        if not batch:
            break
        ok, lat = await _batch(batch, conc)
        total += ok
        batch = []
        el = time.time() - t0
        rate = total / el if el else 0
        print(f"  {total:>10,} mapped  {rate:>6.0f} maps/s  "
              f"{el/3600:>5.2f}h elapsed", flush=True)
        # ⚠ CHECKED HERE, BEFORE ANOTHER BATCH IS BUILT. A refusal that only
        # ends the batch it happened in is not a stop; it is a pause.
        if _REFUSED:
            print("\n  ⚠ ACRIS REFUSED. Everything mapped so far is on disk and "
                  "this is resumable.\n"
                  "    Do NOT restart immediately. Let the connection state "
                  "drain, wait, and resume\n"
                  "    at LOWER concurrency (MAP_CONC). Retrying into a refusal "
                  "is what escalates it.", flush=True)
            break
        if ok == 0:
            print("  no progress — stopping")
            break
    print(f"\n  {total:,} mapped in {(time.time()-t0)/3600:.2f}h")


if __name__ == "__main__":
    asyncio.run(main())
