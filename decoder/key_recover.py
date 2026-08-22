"""RECOVER THE UNPLACED — new towers must not be lost to stale reference data.

    python key_recover.py

WHAT IT RECOVERS, AND ON WHAT EVIDENCE

    928 of 41,765 buildings failed placement. Measured causes, not assumed:

      built 2020+   19.2% of the failures vs 2.4% of the corpus — 8x over-
                    represented, and 107 of those 178 are ACTIVELY LISTING.
                    A demolished building does not advertise apartments.

    So the dominant cause is PLUTO LAGGING NEW CONSTRUCTION. The lot really is
    the right one; PLUTO still describes it as it was before the tower went up
    (`unitsres = 0`, class V for vacant), and the capacity test — which asks "can
    this lot hold these apartments?" — is answered from a snapshot that predates
    them. The test is right and the reference data is old.

    TWO RECOVERIES, EACH WITH ITS OWN WITNESS:

    1. `no-polygon` (341)  the pin is inside no polygon in EITHER layer, which
       for a lot-tiled city means the pin sits in a street bed. Recovered by
       NEAREST LOT within a tight radius — and only when the winner's unit count
       corroborates. Distance alone would just pick the biggest neighbour.

    2. `capacity-rejected` on a 0-unit lot  the geometry already says the pin is
       INSIDE this lot. That is strong evidence. What is missing is proof the
       building exists, and DOB has it: a new-building job or a certificate of
       occupancy on that BBL is an independent witness that something got built
       there. PLUTO not knowing is then a lag, not a contradiction.

⚠ RECOVERED IS NOT THE SAME AS EXACT, AND NEVER RECORDED AS IF IT WERE. Each
    gets its own verdict — `recovered-nearest` or `recovered-dob` — so a comp
    built on one can be told from a comp built on a clean geometric hit.

⚠ AND A BUILDING THAT CANNOT BE CORROBORATED STAYS UNPLACED. The point is not to
    drive the number to 100%; it is to lose no building that the evidence
    actually supports.
"""
import json, math, os, pathlib, sys, time
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import condo_sales as C
import key_stream as K

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

KEYS = pathlib.Path("buildings/streeteasy-parcel-keys.json")
LIST = pathlib.Path("buildings/streeteasy-buildings.json")
M_LAT = 110574.0
MAX_M = 75.0          # a pin in a street bed is metres from its lot, not blocks


def metres(lon1, lat1, lon2, lat2):
    k = 111320.0 * math.cos(math.radians(lat1))
    return math.hypot((lon2 - lon1) * k, (lat2 - lat1) * M_LAT)


def nearest_lots(targets):
    """Stream MapPLUTO once; for each target pin keep the closest few lots."""
    grid = defaultdict(list)
    for i, t in enumerate(targets):
        cx, cy = int(t["lon"] / K.CELL), int(t["lat"] / K.CELL)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                grid[f"{cx+dx},{cy+dy}"].append(i)
    best = defaultdict(list)
    for fp in sorted((K.GEO / "mappluto").glob("p*.json")):
        for r in json.loads(fp.read_text(encoding="utf-8")):
            rings = r.get("rings")
            if not rings:
                continue
            xs = [p[0] for ring in rings for p in ring]
            ys = [p[1] for ring in rings for p in ring]
            cxm, cym = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
            for i in set(grid.get(f"{int(cxm/K.CELL)},{int(cym/K.CELL)}", ())):
                t = targets[i]
                d = metres(t["lon"], t["lat"], cxm, cym)
                if d <= MAX_M:
                    best[i].append((d, {"bbl": r["bbl"], "ur": r.get("ur"),
                                        "cls": r.get("cls"), "adr": r.get("adr")}))
    return {i: sorted(v)[:6] for i, v in best.items()}


def dob_built(bbls):
    """Does DOB record a NEW BUILDING or a CO on this lot? An independent witness
    that something was built, which is exactly what PLUTO is missing."""
    got = {}
    bbls = sorted(set(bbls))
    for i in range(0, len(bbls), 100):
        part = bbls[i:i + 100]
        w = " or ".join(f"bbl='{b}'" for b in part)
        try:
            for r in C.soda("w9ak-ipjd", {
                    "$select": "bbl,job_type,filing_date,job_status_descrp",
                    "$where": f"({w}) and job_type='New Building'", "$limit": 5000}):
                got.setdefault(str(r["bbl"]), []).append(("NB", r.get("filing_date")))
        except Exception:
            pass
        try:
            for r in C.soda("bs8b-p36w", {
                    "$select": "bbl,c_o_issue_date,job_type",
                    "$where": f"({w})", "$limit": 5000}):
                got.setdefault(str(r["bbl"]), []).append(("CO", r.get("c_o_issue_date")))
        except Exception:
            pass
    return got


def main():
    keys = json.loads(KEYS.read_text(encoding="utf-8"))
    lst = {b["slug"]: b for b in json.loads(LIST.read_text(encoding="utf-8"))}
    by_slug = {r["slug"]: r for r in keys}

    nopoly = [r for r in keys if r["verdict"] == "no-polygon"]
    rejected = [r for r in keys if r["verdict"] == "capacity-rejected"]
    print(f"unplaced: {len(nopoly)} no-polygon · {len(rejected)} capacity-rejected\n")

    # ── 1. NEAREST LOT for pins that fell in a street bed ───────────────────
    # ⚠ CAPACITY-REJECTED IS THE SAME DEFECT AS NO-POLYGON, and excluding it lost
    # real towers. Sven's pin lands in 4004030001 (class U2, 0 units) when its
    # own lot 4004030003 records exactly 958 residential units against
    # StreetEasy's 958 — a perfect corroboration one lot away. DWTN lands on a
    # 47-unit lot with 465 units of its own. The pin is metres into the
    # neighbour, which is precisely what the nearest-lot search is for.
    #
    # The bar is HIGHER here than for no-polygon, though: there the pin matched
    # nothing, so any lot that can hold the building is an improvement. Here the
    # geometry already gave an answer and we are overruling it, so the unit count
    # has to do the work — a CLOSE match, not merely a possible one.
    targets = []
    for r in rejected:
        b = lst.get(r["slug"]) or {}
        if b.get("lat") and b.get("lon") and b.get("units"):
            targets.append({"slug": r["slug"], "lat": b["lat"], "lon": b["lon"],
                            "units": b.get("units"), "strict": True})
    for r in nopoly:
        b = lst.get(r["slug"]) or {}
        if b.get("lat") and b.get("lon"):
            targets.append({"slug": r["slug"], "lat": b["lat"], "lon": b["lon"],
                            "units": b.get("units"), "strict": False})
    print(f"searching for the nearest lot within {MAX_M:.0f} m of {len(targets)} pins...")
    near = nearest_lots(targets)
    rec1 = 0
    for i, cands in near.items():
        t = targets[i]
        # corroboration required: the winner must be able to hold the building.
        # Distance alone would hand every pin to whichever neighbour is biggest.
        if t.get("strict"):
            # overruling a geometric hit: require the unit counts to AGREE, and
            # take the best agreement rather than the closest lot
            ok = sorted(((abs(float(a["ur"]) - t["units"]) / max(t["units"], 1), d, a)
                         for d, a in cands if a.get("ur") and float(a["ur"]) > 0),
                        key=lambda x: x[0])
            ok = [(d, a) for c, d, a in ok if c <= 0.25]
        else:
            ok = [(d, a) for d, a in cands
                  if a.get("ur") and float(a["ur"]) > 0
                  and (not t["units"] or float(a["ur"]) * 3 >= t["units"])]
        if not ok:
            continue
        d, a = ok[0]
        row = by_slug[t["slug"]]
        row |= {"bbl": a["bbl"], "verdict": "recovered-nearest",
                "units_res": float(a["ur"]), "bldg_class": a.get("cls"),
                "pluto_address": a.get("adr"),
                "reason": (f"pin landed on a lot that cannot hold {t['units']} units; "
                           f"lot {d:.0f} m away records {int(float(a['ur']))} — a match"
                           if t.get("strict") else
                           f"pin fell outside every polygon; nearest lot that can hold "
                           f"{t['units']} units is {d:.0f} m away")}
        rec1 += 1
    print(f"  recovered {rec1} of {len(targets)} by nearest lot")

    # ── 2. DOB as the witness PLUTO is missing ──────────────────────────────
    zero = [r for r in rejected if "0 residential units" in (r.get("reason") or "")]
    cand_bbl = {}
    for r in zero:
        b = (r.get("reason") or "").split(":")[0]
        if b[:1].isdigit() and len(b) == 10:
            cand_bbl[r["slug"]] = b
    print(f"\nasking DOB about {len(set(cand_bbl.values()))} lots PLUTO calls empty...")
    dob = dob_built(cand_bbl.values())
    rec2 = 0
    for slug, bbl in cand_bbl.items():
        ev = dob.get(bbl)
        if not ev:
            continue
        b = lst.get(slug) or {}
        row = by_slug[slug]
        kinds = sorted({k for k, _ in ev})
        row |= {"bbl": bbl, "verdict": "recovered-dob",
                "reason": f"PLUTO records 0 residential units, but DOB has "
                          f"{'/'.join(kinds)} on this lot — the building exists and "
                          f"PLUTO has not caught up (StreetEasy: built "
                          f"{b.get('built')}, {b.get('units')} units)"}
        rec2 += 1
    print(f"  recovered {rec2} of {len(zero)} with a DOB new-building or CO record")

    out = list(by_slug.values())
    stat = Counter(r["verdict"] for r in out)
    print(f"\nFINAL — {len(out):,} buildings")
    for k, n in stat.most_common():
        print(f"  {k:<22}{n:>8,}{n/len(out)*100:>7.1f}%")
    placed = sum(n for k, n in stat.items() if k.startswith(("exact", "recovered")))
    print(f"\n  PLACED {placed:,} of {len(out):,} ({placed/len(out)*100:.1f}%)")
    print(f"  distinct parcels: {len({r['bbl'] for r in out if r.get('bbl')}):,}")
    KEYS.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"  wrote {KEYS}")


if __name__ == "__main__":
    main()
