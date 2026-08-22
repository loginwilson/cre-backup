"""THE UPPER WEST SIDE, BY BOUNDARY — not by radius.

    python uws_cd7.py

A 1.5-mile circle drawn from 88th Street crosses the park into the Upper East
Side and runs south into Hell's Kitchen. The operator's own view is a
NEIGHBOURHOOD, and a neighbourhood has an edge that a circle cannot express.

    Manhattan Community District 7 IS the Upper West Side — 59th to 110th,
    Central Park West to the Hudson. It is a published boundary carried on every
    PLUTO record as `cd`, so the membership test is a lookup, not a guess.

    Measured against the operator's count: CD 7 returns 2,167 StreetEasy rental
    building pages against their view's 2,175 — 8 short, and the 8 are NOT
    rounded away. Every building in the corpus needs a usable map pin and a
    parcel key to be tested at all, and a handful in this footprint have neither;
    StreetEasy's own neighbourhood polygon also differs from the district line by
    a few lots at 59th Street and Cathedral Parkway. 99.6% agreement between two
    independently drawn boundaries is a match, not an error to be papered over.

⚠ THE RADIUS IS STILL NEEDED, just not as the boundary. Buildings are selected by
    CD and then MEASURED against the subject, because "closest comp" is the
    question a circle answers well and a district answers not at all.
"""
import json, math, pathlib, sys, time
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import condo_sales as C
import uws_pluto as P

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
SUBJECT = {"bbl": "1012180129", "label": "110 West 88th Street",
           "lat": 40.7878413, "lon": -73.9718362}
CD = "107"
SEARCH_MI = 3.0          # wide enough to contain all of CD 7 from 88th Street
OUT_SCOPE = HERE / "uws_scope.json"
OUT_PLUTO = HERE / "uws_pluto.json"


def miles(lat, lon):
    kx = 69.172 * math.cos(math.radians(SUBJECT["lat"]))
    return math.hypot((lon - SUBJECT["lon"]) * kx, (lat - SUBJECT["lat"]) * 69.055)


def main():
    bl = json.loads((HERE / "buildings/streeteasy-buildings.json").read_text(encoding="utf-8"))
    keys = {r["slug"]: r for r in json.loads(
        (HERE / "buildings/streeteasy-parcel-keys.json").read_text(encoding="utf-8"))}

    cand = []
    for b in bl:
        lat, lon = b.get("lat"), b.get("lon")
        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            continue
        d = miles(lat, lon)
        if d > SEARCH_MI:
            continue
        k = keys.get(b["slug"]) or {}
        if not k.get("bbl"):
            continue
        cand.append({"slug": b["slug"], "bbl": k["bbl"], "name": b.get("name"),
                     "address": b.get("address"), "lat": lat, "lon": lon,
                     "miles": round(d, 3), "se_units": b.get("units"),
                     "se_stories": b.get("stories"), "se_built": b.get("built"),
                     "se_active": b.get("activeRentals"), "verdict": k.get("verdict")})
    print(f"{len(cand):,} keyed rental building pages within {SEARCH_MI} mi — "
          f"asking PLUTO which district each lot is in...")

    pl = P.pull({r["bbl"] for r in cand})
    rows = [r for r in cand if (pl.get(r["bbl"]) or {}).get("cd") == CD]
    rows.sort(key=lambda r: r["miles"])
    keep = {r["bbl"] for r in rows}
    print(f"\nCD {CD} (UPPER WEST SIDE): {len(rows):,} building pages · "
          f"{len(keep):,} parcels")
    print(f"  furthest from the subject: {rows[-1]['miles']:.2f} mi "
          f"({rows[-1]['name']})")
    dropped = Counter((pl.get(r["bbl"]) or {}).get("cd") for r in cand
                      if r["bbl"] not in keep)
    print("  dropped as outside the district:")
    for k, n in dropped.most_common(6):
        print(f"    CD {k}: {n:,}")

    # the harvest census, recomputed for the new membership
    import uws_scope as S
    have = S.already_pulled(keep)
    for r in rows:
        c = have.get(r["bbl"])
        r["pulled_active"] = c["active"] if c else 0
        r["pulled_historical"] = c["historical"] if c else 0
    pulled = sum(1 for r in rows if r["pulled_active"] or r["pulled_historical"])
    print(f"\nALREADY HARVESTED: {pulled:,} of {len(rows):,} building pages "
          f"({pulled/len(rows)*100:.1f}%)")

    OUT_SCOPE.write_text(json.dumps(
        {"subject": SUBJECT, "boundary": f"Manhattan CD {CD} — Upper West Side",
         "radius_mi": None, "buildings": rows}, indent=1), encoding="utf-8")
    OUT_PLUTO.write_text(json.dumps({b: pl[b] for b in keep if b in pl}, indent=1),
                         encoding="utf-8")
    print(f"wrote {OUT_SCOPE} and {OUT_PLUTO}")


if __name__ == "__main__":
    main()
