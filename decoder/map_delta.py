"""THE DAILY COMMAND. Find what ACRIS published since last time, and map it.

    python map_delta.py            find + map + advance the watermark
    python map_delta.py --check    report only. Maps nothing, advances nothing.
    python map_delta.py --full     exhaustive per-type diff. Monthly. Slow.

⚠ THE FIELD THAT MAKES THIS CHEAP IS NOT IN THE DATA.

    modified_date        a COLUMN in the record   lags ~11 days
    recorded_datetime    a COLUMN in the record   lags ~11 days
    :updated_at          SOCRATA METADATA         when the row LANDED

Measured 2026-08-11: the newest recorded_datetime in all of ACRIS was
2026-07-31 and "recorded since 2026-08-01" returned ZERO — while 28,196
documents had genuinely appeared. Any monitor keyed on the data's own date
fields reports "nothing new" indefinitely while missing everything.

    :updated_at > 2026-08-09   ->  28,374 rows
    full 17M set difference    ->  28,196 new

They agree, so the cheap query is trustworthy. The small excess is rows
re-published rather than genuinely new, and it is harmless because the set
difference against what is already mapped decides what actually gets work.

⚠ THREE THINGS THIS FILE GOT WRONG, ALL OF WHICH LOOKED FINE WHILE RUNNING.

1. IT PULLED ALL 17M IDS TO FIND 28,000 OF THEM. Forty-five minutes to answer
   a question the API answers in seconds. The exhaustive path survives as
   --full because it is the only thing that can catch a gap from three weeks
   ago, but it is no longer the default.

2. IT READ THE MAP WITH json.loads — 17M JSON objects parsed to read one
   field, 65.8s. `doc_id` is the first key on every line, so a slice does it in
   16s, with a parse fallback per line so an odd key order costs speed instead
   of silently dropping documents.

3. IT ONLY QUEUED THE WORK. The delta appended ids and told you to go run
   supervise_map.py, which then re-read all 17M ids to work out what to do —
   paying the whole scan twice for a few thousand documents. It now maps them
   itself.
"""
import asyncio
import json
import os
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import acris_lock
import amap
import bulk

MASTER = "bnx9-e6tj"
MAPS = ("acris_maps.jsonl", "docmaps.jsonl", "census_maps.jsonl")
IDS = pathlib.Path("acris_ids.jsonl")
STATE = pathlib.Path("_map_delta_state.json")
# ⚠ IDS ALREADY IN THE LEDGER BUT NOT YET MAPPED. Without this, every failed
# retry appends the same ids again — 2 documents is nothing, but a refused
# 28,000-document batch retried nightly grows the ledger by a million rows a
# month and every one of them is a duplicate of a document already queued.
PENDING = pathlib.Path("_map_delta_pending.json")

# ⚠ THE MAP ENDPOINT'S OPTIMUM, MEASURED (287 docs/s). NOT 8 — that is the
# IMAGE endpoint's number, and confusing the two halved throughput for an hour
# on 2026-08-11. Scaled down for small batches; no reason to open 128 sockets
# for nine documents.
MAP_CONC = int(os.environ.get("MAP_CONC", 128))


def ids_from(path, key):
    """Every id in a jsonl file. Slice first, parse only if the slice misses."""
    head = '{"%s": "' % key
    n = len(head)
    out, bad = set(), 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith(head):
                e = line.find('"', n)
                if e > n:
                    out.add(line[n:e])
                    continue
            if not line.strip():
                continue
            try:                                # ⚠ fallback, never a skip
                v = json.loads(line).get(key)
            except ValueError:
                bad += 1
                continue
            out.add(v) if v else None
            bad += 0 if v else 1
    return out, bad


def mapped_ids():
    """⚠ ALL THREE MAP FILES. A completeness check that read only
    acris_maps.jsonl reported 98.64% when the truth was 100.000% — the other
    two hold 73,326 documents."""
    seen, bad = set(), 0
    for name in MAPS:
        p = pathlib.Path(name)
        if not p.exists():
            continue
        s, b = ids_from(p, "doc_id")
        seen |= s
        bad += b
    return seen, bad


def dataset_stamp():
    r = bulk.socrata(MASTER, select="max(:updated_at) as mx",
                     paginate=False, limit=1)
    return r[0]["mx"] if r else None


def arrivals_since(stamp):
    """Rows Socrata touched since `stamp`. This is the whole delta."""
    rows = bulk.socrata(MASTER, where=f":updated_at > '{stamp}'",
                        select="document_id,doc_type,recorded_datetime",
                        paginate=True)
    out = {}
    for r in rows:                              # ⚠ MASTER carries duplicates
        out.setdefault(r["document_id"], r)
    return out


def all_ids():
    """Every id, pulled per type. THE EXHAUSTIVE PATH — slow, and necessary.

    ⚠ KEEP IT DESPITE THE FAST PATH. A monitor that only ever asks "what
    changed since last time" cannot notice that it missed something three weeks
    ago. It inherits every gap it has ever had and reports clean. This is the
    only thing that can say "you are genuinely complete".
    """
    counts = {r["doc_type"]: int(r["n"]) for r in
              bulk.socrata(MASTER, select="doc_type,count(1) as n",
                           group="doc_type", paginate=True)}
    print(f"    {len(counts)} types · {sum(counts.values()):,} rows")
    out = {}
    for i, t in enumerate(sorted(counts, key=lambda x: counts[x]), 1):
        for r in bulk.socrata(MASTER, where=f"doc_type='{t}'",
                              select="document_id,doc_type,recorded_datetime",
                              paginate=True):
            out.setdefault(r["document_id"], r)
        if i % 20 == 0 or i == len(counts):
            print(f"    {i}/{len(counts)} types · {len(out):,} ids", flush=True)
    return out


def do_map(new, live):
    """Map the delta. Returns the ids that are on disk afterwards.

    ⚠ THE RETURN VALUE IS RE-READ FROM THE FILE, NOT ASSUMED FROM THE CALL.
    amap.run halts the whole gather on a refusal and returns normally either
    way, so "it came back" is not evidence anything was written. The watermark
    depends on this answer, and a watermark that advances on an assumption is
    how 28,196 documents once became permanently invisible.
    """
    # ⚠ QUEUE BEFORE MAPPING, NEVER AFTER. If the map dies halfway the ids are
    # already in the ledger, so the next run picks them up by set difference.
    # Appending afterwards would lose exactly the batch that failed.
    pend = set(json.loads(PENDING.read_text())) if PENDING.exists() else set()
    fresh = [d for d in new if d not in pend]
    with open(IDS, "a", encoding="utf-8") as fh:
        for d in fresh:
            fh.write(json.dumps(live[d]) + "\n")
    PENDING.write_text(json.dumps(sorted(pend | set(new))))
    print(f"  queued {len(fresh):,} new ids in {IDS.name}"
          f"{f' · {len(new)-len(fresh):,} already queued by an earlier run' if len(fresh) != len(new) else ''}")

    conc = max(4, min(MAP_CONC, len(new)))
    print(f"  mapping at {conc} concurrent ...\n")
    with acris_lock.AcrisLock("map_delta", wait=True):
        asyncio.run(amap.run(new, conc=conc))

    after, _ = ids_from(pathlib.Path("docmaps.jsonl"), "doc_id")
    done = set(new) & after
    PENDING.write_text(json.dumps(sorted((pend | set(new)) - done)))
    return done


def main():
    t0 = time.time()
    full = "--full" in sys.argv
    check = "--check" in sys.argv
    st = json.loads(STATE.read_text()) if STATE.exists() else {}
    last = st.get("dataset_stamp")

    have, bad = mapped_ids()
    # ⚠ STAMP READ BEFORE THE PULL. The pull that follows captures everything
    # up to pull time, which is at or after this stamp — so advancing to it can
    # only ever re-show a few rows tomorrow. Reading it afterwards would step
    # over anything that landed mid-run.
    now = dataset_stamp()
    print(f"  mapped locally     {len(have):>12,}"
          f"{f'   ⚠ {bad:,} unreadable lines' if bad else ''}")
    print(f"  dataset refreshed  {now}")
    print(f"  last delta run     {last or '(never)'}    ({time.time()-t0:.0f}s)\n")

    if full or not last:
        why = "--full requested" if full else "no prior run — first pass must be exhaustive"
        print(f"  EXHAUSTIVE pass ({why})")
        live = all_ids()
        new = sorted(set(live) - have)
        gone = len(have - set(live))
    else:
        print(f"  FAST pass — rows touched since {last}")
        live = arrivals_since(last)
        new = sorted(set(live) - have)
        gone = None
        print(f"    {len(live):,} documents arrived/changed · "
              f"{len(live)-len(new):,} of them already mapped")

    print(f"\n  NEW TO MAP         {len(new):>12,}")
    if gone:
        print(f"  ⚠ mapped but gone from MASTER: {gone:,} (withdrawn or re-indexed)")

    # ⚠ THE WATERMARK ADVANCES ONLY AFTER THE WORK IS DONE. NEVER ON A LOOK.
    #
    # An earlier version saved state before the branch below, so `--check`
    # advanced the watermark to the current stamp WITHOUT mapping anything —
    # and the next real run found 0 rows, because the 28,196 documents it had
    # just found were now behind the cutoff. Permanently invisible to every
    # future fast pass, silently, while reporting "✅ map is current".
    #
    # A watermark is a promise that everything before it has been HANDLED.
    # Moving it for merely having LOOKED is how a monitor lies about coverage.
    # ⚠ THE STATE FILE MUST SAY WHICH PASS WROTE IT. An earlier version
    # hardcoded mode="fast" in the not-new branch below, so an EXHAUSTIVE run
    # that found nothing — the only run that proves completeness in both
    # directions — recorded itself as a routine daily check. The one tell it
    # was full was that `gone` came back an integer instead of null.
    # `last_full` carries forward so "when was the last two-way check?" has an
    # answer that does not depend on reading the log.
    prior_full = st.get("last_full")

    def save(advance, mode):
        STATE.write_text(json.dumps({
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "mapped": len(have), "seen": len(live), "new": len(new),
            "gone": gone, "dataset_stamp": now if advance else last,
            "mode": mode,
            "last_full": (time.strftime("%Y-%m-%dT%H:%M:%S")
                          if mode == "full" else prior_full)}, indent=1))

    if check:
        save(advance=False, mode="check")
        if new:
            for d in new[:20]:
                print(f"      {d}")
            if len(new) > 20:
                print(f"      ... and {len(new)-20:,} more")
        print(f"\n  --check: nothing mapped, watermark unchanged.  "
              f"({time.time()-t0:.0f}s)")
        return

    if not new:
        # nothing to do, so all IS handled — but record WHICH pass said so.
        save(advance=True, mode="full" if full else "fast")
        print(f"\n  ✅ map is current.  ({time.time()-t0:.0f}s)")
        return

    done = do_map(new, live)
    miss = sorted(set(new) - done)

    print(f"\n  mapped {len(done):,} of {len(new):,}")
    if miss:
        # ⚠ DO NOT ADVANCE. Whatever stopped this — a refusal, a timeout, a
        # document with no map — must still be visible to tomorrow's run.
        save(advance=False, mode="fast-partial")
        print(f"  ⚠ {len(miss):,} NOT MAPPED — watermark held at {last}")
        for d in miss[:20]:
            print(f"      {d}")
        if len(miss) > 20:
            print(f"      ... and {len(miss)-20:,} more")
        print(f"\n  Re-run to retry. If the same ids fail twice, they are not "
              f"transient — check _supervise.log for REFUSED before retrying.")
    else:
        save(advance=True, mode="full" if full else "fast")
        print(f"  ✅ complete. watermark advanced to {now}")
    print(f"  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
