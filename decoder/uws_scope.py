"""SCOPE THE 110 WEST 88TH COMP SET — who is in range, and who is already pulled.

    python uws_scope.py

The operator's filters are SF, units, year built, and DISTANCE, so distance is a
COLUMN not a cutoff — the radius here only has to be wide enough that their own
2,175-building view is contained inside it. 1.5 mi holds 4,113.

⚠ WHAT THIS ANSWERS FIRST is not "what are the comps" but "how much of this set
    is already on disk". A StreetEasy pull is the scarce resource; scanning the
    530 MB already harvested costs nothing and decides how large the pull has to
    be. Guessing that number would size the browser run wrong in both directions.
"""
import bisect, json, math, pathlib, sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
SUBJECT = {"bbl": "1012180129", "label": "110 West 88th Street",
           "lat": 40.7878413, "lon": -73.9718362}
RADIUS_MI = 1.5
OUT = HERE / "uws_scope.json"


def miles(lat, lon):
    kx = 69.172 * math.cos(math.radians(SUBJECT["lat"]))
    return math.hypot((lon - SUBJECT["lon"]) * kx, (lat - SUBJECT["lat"]) * 69.055)


def scope():
    bl = json.loads((HERE / "buildings/streeteasy-buildings.json").read_text(encoding="utf-8"))
    keys = {r["slug"]: r for r in json.loads(
        (HERE / "buildings/streeteasy-parcel-keys.json").read_text(encoding="utf-8"))}
    out = []
    for b in bl:
        lat, lon = b.get("lat"), b.get("lon")
        if not (isinstance(lat, (int, float)) and isinstance(lon, (int, float))):
            continue
        d = miles(lat, lon)
        if d > RADIUS_MI:
            continue
        k = keys.get(b["slug"]) or {}
        if not k.get("bbl"):
            continue
        out.append({"slug": b["slug"], "bbl": k["bbl"], "name": b.get("name"),
                    "address": b.get("address"), "lat": lat, "lon": lon,
                    "miles": round(d, 3), "se_units": b.get("units"),
                    "se_stories": b.get("stories"), "se_built": b.get("built"),
                    "se_active": b.get("activeRentals"),
                    "verdict": k.get("verdict")})
    out.sort(key=lambda r: r["miles"])
    return out


def already_pulled(bbls):
    """Which of these parcels are in the harvest already, and with how much."""
    want = set(bbls)
    have = defaultdict(lambda: Counter())
    for fp in sorted((HERE / "leases_raw").glob("leases_*.jsonl")):
        with open(fp, encoding="utf-8") as f:
            for line in f:
                i = line.find('"bbl":"')
                if i < 0:
                    continue
                bbl = line[i + 7:line.find('"', i + 7)]
                if bbl not in want:
                    continue
                lane = "active" if '"lane":"active"' in line else "historical"
                have[bbl][lane] += 1
    return have


if __name__ == "__main__":
    rows = scope()
    print(f"{SUBJECT['label']} · BBL {SUBJECT['bbl']}")
    print(f"{len(rows):,} keyed StreetEasy rental buildings within {RADIUS_MI} mi\n")
    for r in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5):
        n = bisect.bisect_right([x["miles"] for x in rows], r)
        print(f"  within {r:>4} mi   {n:>6,}")

    have = already_pulled({r["bbl"] for r in rows})
    pulled = [r for r in rows if r["bbl"] in have]
    print(f"\nALREADY HARVESTED: {len(pulled):,} of {len(rows):,} parcels "
          f"({len(pulled)/len(rows)*100:.1f}%) · "
          f"{sum(sum(c.values()) for c in have.values()):,} listings")
    print(f"STILL TO PULL:     {len(rows)-len(pulled):,} buildings")

    for r in rows:
        c = have.get(r["bbl"])
        r["pulled_active"] = c["active"] if c else 0
        r["pulled_historical"] = c["historical"] if c else 0
    OUT.write_text(json.dumps({"subject": SUBJECT, "radius_mi": RADIUS_MI,
                               "buildings": rows}, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT}")
