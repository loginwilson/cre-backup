"""LOT LINEAGE — derived from buildings, because a building does not move.

⚠ THE IDEA. A tax lot is an administrative fiction that gets merged, apportioned
and condo-converted. A BUILDING is physical and keeps its BIN through all of it.
So if a job filed in 2003 says BIN 3057923 sits on lot 3020277501, and today's
footprint says that same BIN sits on 3020270010, the lot changed and the building
witnessed it. Every BIN that has ever been stated on two different lots is a
lineage edge, and the filing dates order it.

That makes DOB — a source with no interest in tax lots at all — the largest
lineage witness available, because it states (BIN, BBL) 3.6M times.

⚠ WHAT THIS CANNOT SEE, MEASURED NOT ASSUMED. BIS pre-filing dates begin
01/01/2000 and DOB NOW begins 2016-08-04. So this reconstructs lineage from 2000
forward and is BLIND before it. Login, 2026-08-16: "there was a record before BIS
came to play in 2000." That record is the way back; until it is acquired, every
pre-2000 lot change is `unread`, not absent.

⚠ THREE WAYS TO BE WRONG, ALL HANDLED EXPLICITLY:

  1. A CONDO IS NOT A MERGER. DOB states the billing lot (75xx), the tax map
     states the land lot. That is a KEY mismatch, already solved in bin_bbl.py,
     and it is resolved BEFORE anything is called lineage — otherwise 3,307
     condo jobs in a 60k sample masquerade as lot changes.

  2. A CORNER BUILDING IS NOT A MERGER EITHER. One BIN can genuinely sit across
     two lots that BOTH still exist. So an edge is only claimed when the old lot
     is GONE from the current universe and the new one is present. Both alive =
     multi-lot, reported separately, never as lineage.

  3. A TYPO IS NOT A LOT CHANGE. One filing clerk's slip looks identical to a
     merger with one witness. Edges carry their witness count, and a single
     witness is reported as WEAK rather than silently believed.

    python lot_lineage.py            # pull, derive, measure
    python lot_lineage.py --report   # from what is already on disk
"""
from __future__ import annotations

import collections, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

import bulk, bin_bbl

PLUTO = "64uk-42ks"
FEEDS = [("BIS", "ic3t-wcy2", "bin__", "pre__filing_date"),
         ("NOW", "w9ak-ipjd", "bin", "filing_date")]
OBS = os.path.join(HERE, "_lineage_obs.jsonl")
OUT = os.path.join(HERE, "_lot_lineage.json")
UNI = os.path.join(HERE, "_live_bbls.json")

BORO_NUM = {"MANHATTAN": "1", "BRONX": "2", "BROOKLYN": "3", "QUEENS": "4",
            "STATEN ISLAND": "5"}
YEAR = re.compile(r"(19|20)\d{2}")


def bbl_of(boro, block, lot):
    b = BORO_NUM.get(str(boro or "").strip().upper())
    try:
        blk, lt = int(str(block).strip()), int(str(lot).strip())
    except (TypeError, ValueError):
        return None
    return f"{b}{blk:05d}{lt:04d}" if b and blk > 0 else None


def year_of(v):
    m = YEAR.search(str(v or ""))
    return int(m.group(0)) if m else None


def pull():
    with open(OBS, "w", encoding="utf-8") as fh:
        for label, ds, bf, df in FEEDS:
            print(f"pulling {label} {ds} …", flush=True)
            rows = bulk.socrata(ds, select=f"{bf},borough,block,lot,{df}",
                                paginate=True)
            n = 0
            for r in rows:
                b = str(r.get(bf) or "").strip().split(".")[0]
                if not b.isdigit() or b.endswith("000000"):
                    continue
                bbl = bbl_of(r.get("borough"), r.get("block"), r.get("lot"))
                if not bbl:
                    continue
                fh.write(json.dumps([b, bbl, year_of(r.get(df)), label]) + "\n")
                n += 1
            print(f"  {label}: {len(rows):,} rows -> {n:,} usable observations")


def current_universe():
    """Every BBL that exists TODAY. Deliberately BROAD — a lot wrongly counted as
    alive only costs a missed edge; one wrongly counted as dead invents lineage."""
    if os.path.exists(UNI):
        uni = set(json.load(open(UNI, encoding="utf-8")))
        j = json.load(open(bin_bbl.JOIN, encoding="utf-8"))["bin2bbl"]
        print(f"  live BBL universe cached: {len(uni):,}")
        return uni, j
    uni = set()
    print("pulling current PLUTO BBLs …", flush=True)
    for r in bulk.socrata(PLUTO, select="bbl", paginate=True):
        b = bin_bbl.norm_bbl(r.get("bbl"))
        if b:
            uni.add(b)
    print(f"  PLUTO {len(uni):,}")
    j = json.load(open(bin_bbl.JOIN, encoding="utf-8"))["bin2bbl"]
    uni |= set(j.values())
    for v in bin_bbl._billing().values():
        uni.add(v)
    print(f"  ∪ footprints ∪ condo land lots = {len(uni):,} live BBLs")
    json.dump(sorted(uni), open(UNI, "w"), separators=(",", ":"))
    return uni, j


def main():
    if "--report" not in sys.argv or not os.path.exists(OBS):
        pull()
    uni, fp = current_universe()

    seen = collections.defaultdict(dict)      # bin -> {bbl: (min_yr, max_yr, n)}
    obs = condo = unkeyable = 0
    with open(OBS, encoding="utf-8") as fh:
        for line in fh:
            b, bbl, yr, _src = json.loads(line)
            land = bin_bbl.land_bbl(bbl)      # ⚠ condo billing resolved FIRST
            # ⚠ REFUSED, NOT COERCED. An out-of-range block or lot builds an
            # over-length BBL; norm_bbl rejects it and the observation is
            # DROPPED and counted. Letting None through made it a dict key and
            # invented an edge from nowhere.
            if not land:
                unkeyable += 1
                continue
            if land != bbl:
                condo += 1
            obs += 1
            d = seen[b]
            lo, hi, n = d.get(land, (9999, 0, 0))
            d[land] = (min(lo, yr or 9999), max(hi, yr or 0), n + 1)

    print(f"\nOBSERVATIONS {obs:,} · {condo:,} were condo billing lots, "
          f"resolved to land lots before any lineage was claimed")
    print(f"BINs seen: {len(seen):,}")

    multi = {b: d for b, d in seen.items() if len(d) > 1}
    print(f"  BINs stated on >1 lot: {len(multi):,}")

    edges = collections.defaultdict(lambda: {"bins": set(), "last_old": 0,
                                             "first_new": 9999})
    multilot = 0
    crossboro = set()
    for b, d in multi.items():
        dead = {k: v for k, v in d.items() if k not in uni}
        alive = {k: v for k, v in d.items() if k in uni}
        if not dead:
            multilot += 1                      # ⚠ corner building, NOT lineage
            continue
        # prefer today's footprint as the terminal node; else any live lot
        to = fp.get(b) if fp.get(b) in alive else (
            max(alive, key=lambda k: alive[k][1]) if alive else None)
        if not to:
            continue
        for old, (lo, hi, _n) in dead.items():
            if old == to:
                continue
            # ⚠ A BUILDING CANNOT CHANGE BOROUGH. Two of the six strongest edges
            # in the first run were 4->2 and 2->1: a borough field mistyped on a
            # filing, which looks EXACTLY like a well-witnessed merger because
            # the same wrong value repeats across a job's amendments. Rejected
            # outright and counted — never ranked as lineage.
            if old[0] != to[0]:
                crossboro.add((old, to))
                continue
            e = edges[(old, to)]
            e["bins"].add(b)
            e["last_old"] = max(e["last_old"], hi)
            e["first_new"] = min(e["first_new"], alive[to][0])

    strong = {k: v for k, v in edges.items() if len(v["bins"]) >= 2}
    print(f"\nLINEAGE EDGES  {len(edges):,} total · "
          f"{len(strong):,} with 2+ building witnesses (STRONG)")
    print(f"  ⚠ multi-lot buildings excluded (both lots alive): {multilot:,}")
    print(f"  ⚠ cross-BOROUGH pairs REJECTED (mistyped borough): {len(crossboro):,}")

    sameblk = sum(1 for a, b in edges if a[:6] == b[:6])
    print(f"  same block   {sameblk:,} ({100*sameblk/max(len(edges),1):.0f}%) "
          f"— mergers, apportionments\n  cross block  {len(edges)-sameblk:,} "
          f"— renumbering, or a bad filing")

    yrs = collections.Counter(v["last_old"] for v in edges.values() if v["last_old"])
    print("\nWHEN THE OLD LOT WAS LAST STATED — the reach of this method")
    for y in sorted(yrs)[:3] + sorted(yrs)[-3:]:
        print(f"  {y}  {yrs[y]:>6,}")
    print("  ⚠ nothing before 2000 — BIS begins 01/01/2000 and DOB NOW 2016-08-04.")

    top = sorted(edges.items(), key=lambda kv: -len(kv[1]["bins"]))[:6]
    print("\nSTRONGEST EDGES")
    for (a, b), v in top:
        print(f"  {a} -> {b}   {len(v['bins'])} buildings   "
              f"old last seen {v['last_old'] or '?'}")

    json.dump({"edges": [{"from": a, "to": b, "witnesses": len(v["bins"]),
                          "bins": sorted(v["bins"])[:10],
                          "old_last_seen": v["last_old"],
                          "new_first_seen": None if v["first_new"] == 9999
                          else v["first_new"],
                          "strength": "strong" if len(v["bins"]) >= 2 else "weak"}
                         for (a, b), v in sorted(edges.items(),
                                                 key=lambda kv: -len(kv[1]["bins"]))],
               "counts": {"observations": obs, "condo_resolved": condo,
                          "unkeyable": unkeyable,
                          "bins": len(seen), "multi_lot_bins": len(multi),
                          "multilot_excluded": multilot,
                          "crossboro_rejected": len(crossboro),
                          "edges": len(edges), "strong": len(strong),
                          "live_bbls": len(uni)},
               "blind_before": 2000},
              open(OUT, "w"), separators=(",", ":"))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
