"""ATTACH PLUTO TO THE COMP SET — the filters the operator actually asked for.

    python uws_pluto.py

StreetEasy states units, stories and a build year, and PLUTO states GROSS FLOOR
AREA, which StreetEasy does not carry at all. Since the filter list is "sf, units,
built, distance", three of the four come from here.

⚠ BOTH SOURCES ARE KEPT, NEVER MERGED INTO ONE COLUMN. StreetEasy's unit count is
    what is on the market; PLUTO's `unitsres` is what the city records. They
    disagree often enough that collapsing them would silently pick a winner — and
    a disagreement is a signal about condo/rental splits and stale reference data,
    not noise to be averaged away.

⚠ AND `yearalter` IS A SEPARATE FILTER FROM `yearbuilt`. A 1920 building gut-
    renovated in 2019 competes with new construction; filtering on yearbuilt alone
    hides exactly the comps that matter for a new rental.
"""
import json, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import condo_sales as C

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
SCOPE = HERE / "uws_scope.json"
OUT = HERE / "uws_pluto.json"

FIELDS = ("bbl,address,ownername,bldgclass,landuse,zonedist1,zonedist2,lotarea,"
          "bldgarea,comarea,resarea,officearea,retailarea,numbldgs,numfloors,"
          "unitsres,unitstotal,yearbuilt,yearalter1,yearalter2,builtfar,residfar,"
          "commfar,latitude,longitude,cd,zipcode,assesstot,version")


def pull(bbls):
    got, bbls = {}, sorted(set(bbls))
    # PLUTO stores bbl as a NUMBER with decimals ("1012180129.00000000"), so an
    # `in(...)` on strings returns nothing. Compare numerically.
    for i in range(0, len(bbls), 200):
        part = bbls[i:i + 200]
        w = ",".join(part)
        for r in C.soda("64uk-42ks", {"$select": FIELDS,
                                      "$where": f"bbl in({w})", "$limit": 5000}):
            got[str(int(float(r["bbl"])))] = r
        print(f"  {min(i+200, len(bbls)):>6,}/{len(bbls):,} · {len(got):,} found",
              end="\r", flush=True)
    print()
    return got


if __name__ == "__main__":
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))
    rows = scope["buildings"]
    bbls = {r["bbl"] for r in rows}
    print(f"asking PLUTO about {len(bbls):,} parcels...")
    t0 = time.time()
    p = pull(bbls)
    print(f"  {len(p):,} of {len(bbls):,} parcels found ({len(p)/len(bbls)*100:.1f}%) "
          f"in {time.time()-t0:,.0f}s")
    miss = sorted(bbls - set(p))
    if miss:
        # a BBL PLUTO does not know is usually a retired lot or a condo billing
        # lot — worth naming, never worth silently dropping
        print(f"  ⚠ {len(miss):,} not in PLUTO (retired lot or condo billing lot): "
              f"{', '.join(miss[:6])}{' …' if len(miss) > 6 else ''}")
    OUT.write_text(json.dumps(p, indent=1), encoding="utf-8")
    print(f"wrote {OUT}")
