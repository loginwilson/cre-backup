"""WALK THE GAP — every CRFN between the specification ceiling and the live ceiling.

    ACRIS_CORPUS_ROOT=D:/acris python live_gap.py --run

WARNING - THE GAP IS NOT A RANGE. It is holes BELOW our high-water mark plus a
contiguous run above it. A forward walk gets the second and silently misses the
first - measured 2026-08-18: 3,449 holes below, 357 above.

WARNING - THE CEILING MOVES EVERY MONTH. Read from _socrata_ceiling.json, never
hardcoded: a stale (too low) ceiling re-fetches thousands of documents the
extract already has, because `held` tracks only the live queue. AND IT BREAKS AT
THE YEAR ROLLOVER - crfn is YYYY+serial, so 2026000233436 -> 2027000000001 makes
the subtraction hugely negative. routine_4am advances the ceiling only after a
PROVEN span 0.

WARNING - APPEND EVERY RECORD IMMEDIATELY. An abort must cost ONE document, not
the run. Resumable by construction: what is in the queue is never re-asked.

WARNING - CONCURRENCY 3, JUSTIFIED BY MEASUREMENT, NOT HOPE. The only trip ever
was conc 16 COLD in a 12,077-document burst. Conc 8 with a seeded session ran
clean the SAME DAY on this host; acquisition sustains 80 connections at 93.8
pg/s for days. Three workers (~1.3 req/s total) is a fifth of the measured-clean
level. On ANY Refused: stop everything - never retry a refusal, never raise the
worker count to "catch up".
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import live_crfn as LC
import live_delta as LD

QUEUE = HERE / "_live_delta_queue.jsonl"
EDGE = HERE / "_crfn_edge.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    _c = HERE / "_socrata_ceiling.json"
    _d = json.loads(_c.read_text(encoding="utf-8")) if _c.exists() else {}
    ap.add_argument("--baseline", type=int,
                    default=_d.get("ceiling", 2026000216616),
                    help="specification ceiling (advanced by routine on span 0)")
    a = ap.parse_args()

    held = set()
    if QUEUE.exists():
        for l in QUEUE.open(encoding="utf-8"):
            c = str(json.loads(l).get("crfn") or "").strip()
            if c.isdigit():
                held.add(int(c))
    edge = json.loads(EDGE.read_text(encoding="utf-8"))["edge"]
    gap = [n for n in range(a.baseline + 1, edge + 1) if n not in held]
    print(f"  ceiling {a.baseline} -> live {edge}")
    print(f"  span {edge-a.baseline:,} · held {len(held):,} · TO FETCH {len(gap):,}")
    if not a.run:
        print("  --run not given.")
        return

    s = LD.Session().open().open_crfn()
    ctrl = max(held) if held else a.baseline
    if LC.parse_detail(LC.detail_html(s, ctrl)) is None:
        sys.exit(f"  CONTROL {ctrl} did not resolve - refusing to classify. "
                 f"A malformed request looks exactly like an empty one.")
    print(f"  control {ctrl} resolves - probe OK")

    def _safe(n):
        """(n, parsed, error-name): exceptions cross threads as values."""
        try:
            return n, LC.parse_detail(LC.detail_html(s, n)), None
        except Exception as e:
            return n, None, type(e).__name__

    found = unissued = done = 0
    t0 = time.time()
    refused = False
    BLOCK = 30
    with QUEUE.open("a", encoding="utf-8") as f:
        with ThreadPoolExecutor(max_workers=3) as ex:
            for b0 in range(0, len(gap), BLOCK):
                if refused:
                    break
                for n, d, err in ex.map(_safe, gap[b0:b0 + BLOCK]):
                    done += 1
                    if err == "Refused":
                        print(f"  REFUSED at {n} after {done-1} lookups - "
                              f"STOPPING. {found:,} already queued are not lost.")
                        refused = True
                        break
                    if err:
                        print(f"    {n} ERROR {err} - skipped")
                        continue
                    if d is None:
                        unissued += 1
                        continue
                    d["crfn"] = str(n)
                    f.write(json.dumps(d) + "\n")
                    f.flush()                       # per-record, resumable
                    found += 1
                    if found % 100 == 0:
                        r = (time.time() - t0) / done
                        print(f"    {found:,} found · {unissued} unissued · "
                              f"{done:,}/{len(gap):,} · "
                              f"{(len(gap)-done)*r/60:.0f} min left")

    print(f"\n  DONE {found:,} documents · {unissued} unissued · "
          f"{(time.time()-t0)/60:.1f} min")
    print("  next: live_land.py --apply, then crfn_monitor.py (span must be 0)")


if __name__ == "__main__":
    main()
