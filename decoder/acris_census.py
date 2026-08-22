"""THE ACRIS CENSUS — per-year issued-vs-held, the county's own counter as
the denominator (login 2026-08-21: "make sure we gather all doc ids. this
goes for acris too").

For every CRFN year (CRFNs are YYYY + a dense per-year sequence):

    issued(Y) = the year's highest sequence, found by the proven
                control-gallop-bisect probe against ACRIS's own counter
    held(Y)   = documents recorded in Y in our specification
    delta(Y)  = issued - held   (an UPPER bound: some issued numbers
                never resolve to documents)

    python acris_census.py --run          probe every year, write the table
    python acris_census.py --report       print what is stored

⚠ WHY THIS CLOSES THE ACRIS SIDE. The daily sync proves levelness at the
EDGE; it says nothing about holes deep in history. This census bounds every
year: a year with delta 0 is closed arithmetic; a year with a positive
delta names exactly how many documents are unaccounted for and where. The
2026 check (issued 235,036 vs held 234,972 -> <=64) was the prototype.

⚠ WHAT IT CANNOT SEE, recorded honestly: pre-CRFN documents (microfilm
FT_/BK_ ids) have no counter to census against - their completeness rests
on ACRIS's own reel indexes, enumerated during the original acquisition.
There is no electronic corpus before that on the ACRIS side (confirmed);
Staten Island's older paper lives at Richmond County, whose census is the
window sweep (rc_census.py).

⚠ POLITE: 3 parallel year-probes, one session each - a fraction of the
4x20 acquisition load this host has already served. STOPS on a refusal.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP
import live_crfn as LC
import live_delta as LD

OUT = (pathlib.Path(r"D:\CRE Decoding System\00 Synchronizations")
       / "Legal Instruments Synchronization" / "ACRIS Census.json")
FIRST_YEAR = 2003          # ACRIS's first CRFN year
PACE = 1.5

ap = argparse.ArgumentParser()
ap.add_argument("--run", action="store_true")
ap.add_argument("--report", action="store_true")
a = ap.parse_args()


def resolves(s, crfn):
    time.sleep(PACE)
    return LC.parse_detail(LC.detail_html(s, str(crfn))) is not None


def year_edge(s, year, held_hint=0):
    """the year's highest issued sequence - seed, gallop, bisect, confirm.

    ⚠ THE SEQUENCE HAS HOLES (2009 measured: a gallop from seq 1 stopped
    at 122 with 430,881 documents held - a few unissued numbers read as
    the edge). Two defenses, both from the held count we already know:
      - SEED at held_hint: the edge cannot sit below what we hold, so
        start the climb there instead of at 1
      - CONFIRM with a Fibonacci spread, not consecutive probes: a small
        hole fails 1,2,3 but something resolves at +8 or +21; when it
        does, the climb RESUMES from there instead of trusting the hole
    Returns (edge, requests) or (None, n) if no seed resolves or the
    result still sits below the held count (impossible for a true edge)."""
    base = year * 10**9
    n = [0]

    def r(seq):
        n[0] += 1
        return resolves(s, base + seq)

    lo = 0
    for seed in sorted({1, max(1, held_hint // 2), max(1, held_hint)},
                       reverse=True):
        if r(seed):
            lo = seed
            break
    if lo == 0:
        return None, n[0]          # nothing resolves - report, don't guess
    while True:
        step = 1
        while True:
            if r(lo + step):
                lo, step = lo + step, step * 2
            else:
                hi = lo + step
                break
            if step > 1 << 21:
                return None, n[0]
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if r(mid):
                lo = mid
            else:
                hi = mid
        far = next((k for k in (1, 2, 3, 5, 8, 13, 21, 34, 55, 89)
                    if r(lo + k)), None)
        if far is None:
            break                  # the spread is all blank - a real edge
        lo += far                  # a hole, not the edge - climb on
    if held_hint and lo < held_hint * 0.99:
        return None, n[0]          # below what we hold - the probe failed
    return lo, n[0]


def held_by_year():
    """documents recorded per year, digital ids only (CRFN era)"""
    spec = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True,
                           timeout=900)
    rows = spec.execute(
        "SELECT substr(recorded_date, 1, 4) y, COUNT(*)"
        " FROM document WHERE document_id < '3'"
        " AND recorded_date IS NOT NULL GROUP BY y").fetchall()
    spec.close()
    return {r[0]: r[1] for r in rows if (r[0] or "").isdigit()}


def run():
    # ⚠ 3 YEARS IN PARALLEL, one session each - a fraction of the 4x20
    # acquisition load this host served without complaint; years are
    # independent probes. Entries whose stored edge sits below 99% of the
    # held count are the HOLE BUG's output (2009: "issued 122") and
    # re-probe under the fixed year_edge.
    import threading
    from concurrent.futures import ThreadPoolExecutor
    held = held_by_year()
    got = json.loads(OUT.read_text()) if OUT.exists() else {}
    this_year = dt.date.today().year
    for y in list(got):
        if not y.isdigit():
            continue
        e, h = got[y].get("issued"), got[y].get("held", 0)
        if e is None or e < h * 0.99:
            del got[y]             # hole-bug victim - re-probe
    lock = threading.Lock()
    tls = threading.local()

    def one(year):
        if not hasattr(tls, "s"):
            tls.s = LD.Session().open().open_crfn()
        edge, reqs = year_edge(tls.s, year, held.get(str(year), 0))
        h = held.get(str(year), 0)
        with lock:
            if edge is None:
                print(f"{year}: UNPROVEN (no seed/confirm after {reqs}"
                      f" requests) - held {h:,}", flush=True)
                got[str(year)] = {"issued": None, "held": h}
            else:
                print(f"{year}: issued {edge:,} · held {h:,} ·"
                      f" delta {edge - h:+,}  ({reqs} requests)", flush=True)
                got[str(year)] = {"issued": edge, "held": h,
                                  "delta": edge - h}
            got["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            OUT.write_text(json.dumps(got, indent=1))

    todo = [y for y in range(FIRST_YEAR, this_year + 1)
            if str(y) not in got or y == this_year]
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(one, todo))
    print("ACRIS CENSUS COMPLETE")


def report():
    if not OUT.exists():
        print("no census yet - run with --run")
        return
    got = json.loads(OUT.read_text())
    tot_i = tot_h = 0
    print(f"{'year':<6} {'issued':>10} {'held':>10} {'delta':>8}")
    for y in sorted(k for k in got if k.isdigit()):
        r = got[y]
        i, h = r.get("issued"), r.get("held", 0)
        tot_h += h
        if i is None:
            print(f"{y:<6} {'UNPROVEN':>10} {h:>10,}")
            continue
        tot_i += i
        print(f"{y:<6} {i:>10,} {h:>10,} {i - h:>+8,}")
    print(f"{'TOTAL':<6} {tot_i:>10,} {tot_h:>10,} {tot_i - tot_h:>+8,}"
          f"   (delta is an UPPER bound - unissued numbers exist)")


if a.run:
    run()
elif a.report:
    report()
else:
    print(__doc__)
