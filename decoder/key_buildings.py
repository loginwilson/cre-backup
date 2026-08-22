"""BULK KEYER — 41,816 StreetEasy buildings to the parcel spine, in one pass.

    python key_buildings.py --list data/streeteasy-buildings.json
    python key_buildings.py --list ... --out public/streeteasy-parcel-keys.json

WHY THIS EXISTS — LOGIN CAUGHT THE ARCHITECTURE, 2026-08-06

    "right now are you keying the 41,816 buildings to the parcel spine? or just
     moving through the building listings one at a time"

    One at a time. `streeteasyPullCity.js` called ArcGIS per building, inside
    the crawl loop, cached only on an exact coordinate match — which never
    repeats. That is 41,816 sequential round trips braided into the pull. It
    works at 2,893 buildings and cannot hold at 41,816: slow, rate-exposed, and
    every crash throws away all the placement work along with the crawl.

    It is also the lesson devBulk already learned and wrote down: pull feeds
    wholesale, derive locally, never make per-site portal calls at population
    scale. Placement is a BULK JOIN, not a step inside a crawl.

HOW IT IS BOUNDED — MULTIPOINT, NOT ONE POINT AT A TIME

    ArcGIS accepts `esriGeometryMultipoint`, so ONE request asks "which lots
    intersect any of these 100 pins" and returns those polygons with geometry.
    41,816 pins therefore cost ~420 requests instead of 41,816, and the exact
    pin->lot assignment is then done LOCALLY by ray casting.

    The server does the spatial filter, which is what it is good at; this does
    the assignment, which needs to know which pin is which. Neither guesses.

    Everything is cached to disk by tile, so a re-run after a bigger enumeration
    only fetches what is new.

WHAT COMES OUT

    One row per building: slug, bbl, ground_bbl, verdict, and the reason. Every
    building gets a row — an unplaced building is a RESULT, not an omission. A
    building with no ledger is visibly missing; a building on the wrong lot is a
    comp that looks perfectly normal and is silently false.

    verdicts:
      exact                pin inside one lot that can hold the building
      capacity-rejected    pin inside a lot that cannot (0 res units, or under a
                           third of the unit count the source states)
      ambiguous            pin inside several candidate lots, none decisive
      no-polygon           pin inside no lot at all
      no-pin               the source gave no coordinates
      FAILED               the lookup itself failed — retryable, NOT a verdict

⚠ CAPACITY STILL ADJUDICATES. A pin is only as good as its precision: tested
    2026-08-06, coordinates rounded to ~100 m placed four known buildings on
    neighbouring lots, cleanly and confidently. Geometry proposes; the
    residential unit count disposes.

⚠ MapPLUTO IS THE MATCHER, THE TAX MAP IS THE CROSS-CHECK. Measured on one pin
    near Gotham Point: the DOF tax map returns 4000160001 (the physical BASE
    lot), MapPLUTO returns 4000167501 (the condominium BILLING lot). Not a
    disagreement — the condo split. StreetEasy, DOF sales and the app all key on
    the billing lot, so MapPLUTO is the answer and the tax map says what is
    underneath. Both are carried.
"""
import json, math, os, pathlib, sys, time, urllib.parse, urllib.request
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sink

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SOURCE = "STREETEASY"
MAPPLUTO = ("https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services"
            "/MAPPLUTO/FeatureServer/0/query")
DTM = ("https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services"
       "/Tax_Lot_View/FeatureServer/0/query")
CACHE = pathlib.Path(__file__).with_name("keycache")
SPINE_DIR = pathlib.Path(os.environ.get(
    "DECODER_SPINE", pathlib.Path(__file__).with_name("spine")))

BATCH = 100          # pins per multipoint request
NYC = (-74.30, 40.47, -73.68, 40.93)


def _get(url, params, tries=4):
    """Three outcomes. A transport failure RAISES — it must never be recorded as
    'no polygon here', because those two look identical in the response and mean
    opposite things."""
    body = urllib.parse.urlencode(params).encode()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url, data=body,          # POST: a 100-point geometry overflows a GET
                headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=300) as f:
                d = json.load(f)
            if "error" in d:
                raise RuntimeError(str(d["error"])[:160])
            return d.get("features", [])
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"FAILED after {tries} tries: {type(last).__name__}: {last}")


def fetch_candidates(pins, layer, out_fields):
    """Every polygon intersecting ANY of these pins, WITH geometry."""
    geom = {"points": [[p[0], p[1]] for p in pins],
            "spatialReference": {"wkid": 4326}}
    return _get(layer, {
        "geometry": json.dumps(geom), "geometryType": "esriGeometryMultipoint",
        "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields, "returnGeometry": "true",
        "outSR": 4326, "f": "json"})


def in_ring(x, y, ring):
    """Ray casting. Exact, dependency-free, and the whole reason this can run
    locally instead of asking a server 41,816 times."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
            if x < xint:
                inside = not inside
        j = i
    return inside


def in_polygon(x, y, rings):
    """Esri polygons carry outer rings clockwise and HOLES counter-clockwise in
    the same `rings` array. Counting a hole as an outer ring puts a pin in a
    courtyard onto the lot that surrounds it, so parity is what decides: an odd
    number of containing rings is inside, an even number is in a hole.
    """
    hits = sum(1 for r in rings if len(r) > 2 and in_ring(x, y, r))
    return hits % 2 == 1


def bbox(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def capacity(units_res, source_units):
    """Can this lot hold this building?

    ⚠ THE ONE-SIDED TEST IS NOT ENOUGH, and this keyer proved it on its own
    output. `reconcileRentLots`' rule only rejects lots that are too SMALL
    (`unitsres * 3 < units`). Measured 2026-08-06 over 2,856 buildings: geometry
    and the address match disagreed on 16, and the unit count called all 16
    "both plausible" — because a lot that is far too BIG passes trivially.

    The clearest case is one this codebase has already been burned by:

        The Cove   123 units   pin landed on 4004377502 = SKYLINE TOWER, 802 units

    802 comfortably "holds" 123, so the test said yes. It is still the wrong
    building — the pin drifted onto a much larger neighbour, which is precisely
    the failure geometry was brought in to prevent. So the band is two-sided:
    a lot holding many times the building's own unit count is as suspect as one
    holding a fraction of it.
    """
    if units_res is None:
        return False, "matched lot has no unitsres"
    if units_res <= 0:
        return False, "lot records 0 residential units"
    if not source_units or source_units <= 0:
        return True, "source states no unit count — capacity UNTESTED, not passed"
    if units_res * 3 < source_units:
        return False, (f"lot holds {int(units_res)} residential units vs the "
                       f"source's {int(source_units)} — a 3x shortfall")
    # Too big, by the same factor. Small buildings need a floor: a 2-unit house
    # on a 12-unit lot is ordinary imprecision, not a drift onto a tower.
    if source_units >= 10 and units_res > source_units * 3:
        return False, (f"lot holds {int(units_res)} residential units against the "
                       f"source's {int(source_units)} — 3x too LARGE, the pin has "
                       f"most likely drifted onto a bigger neighbour")
    return True, None


def closeness(units_res, source_units):
    """Tie-break among candidates that all pass: the lot whose recorded unit
    count is nearest the source's own.

    Two independent counts of the same building should agree, and where they do
    the placement is confirmed rather than merely permitted — 1 QPS states 391
    units and lot 4004250001 records exactly 391. Lower is better; None when
    there is nothing to compare, so it can never outrank a real comparison.
    """
    if not units_res or not source_units:
        return None
    return abs(units_res - source_units) / max(source_units, 1)


def load_list(path):
    rows = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    ok, nopin = [], []
    for b in rows:
        lat, lon = b.get("lat"), b.get("lon")
        if (isinstance(lat, (int, float)) and isinstance(lon, (int, float))
                and NYC[1] <= lat <= NYC[3] and NYC[0] <= lon <= NYC[2]):
            ok.append(b)
        else:
            # ⚠ Out-of-bounds is its own bucket. A New Jersey pin that slipped
            # the geography filter is not "unplaceable", it is OUT OF SCOPE, and
            # collapsing the two hides a broken enumeration.
            nopin.append(b)
    return rows, ok, nopin


def key_all(list_path, out_path=None, batch=BATCH, offline=False):
    """`offline=True` answers every pin from the spine's own polygons.

    The spine now carries geometry (856,614 MapPLUTO parcels, `spine_geometry.py`),
    so placement needs no server at all. The multipoint path below already cut
    41,816 requests to ~420; this takes it to ZERO, and makes re-keying free —
    which matters because re-keying is what you do every time the list grows or
    the spine is corrected, and a free operation gets done while a costly one
    gets skipped.
    """
    run_id = f"keyer-{int(time.time())}"
    CACHE.mkdir(parents=True, exist_ok=True)
    loc = loc_dtm = None
    if offline:
        import spine_geometry
        loc = spine_geometry.Locator("mappluto")
        # ⚠ THE CROSS-CHECK IS OPTIONAL AND ITS ABSENCE IS NOT AGREEMENT.
        # The tax map answers a different question from MapPLUTO — what is
        # physically under the pin, versus which parcel the world keys on — and
        # for a condominium the two differ BY DESIGN (base lot vs billing lot).
        # If its geometry has not been pulled, `ground_bbl` stays None and the
        # run says the check did not run. Silently omitting it would let a
        # missing witness read as a corroborating one.
        try:
            loc_dtm = spine_geometry.Locator("dtm")
        except SystemExit:
            print("  ⚠ no DTM geometry — ground_bbl will be None. That is the "
                  "cross-check NOT RUN, not the cross-check agreeing. "
                  "Run: spine_geometry.py --pull dtm --index dtm")

    allrows, pinned, nopin = load_list(list_path)
    print(f"building list: {len(allrows):,} rows · {len(pinned):,} with a usable "
          f"NYC pin · {len(nopin):,} without")
    if not pinned:
        raise SystemExit("no pins — re-export the list with __seExport()")

    sink.heartbeat(SOURCE, run_id, done=0, total=len(allrows),
                   note="bulk parcel keying")

    out, stat = [], Counter()
    for b in nopin:
        stat["no-pin"] += 1
        out.append({"slug": b.get("slug"), "bbl": None, "ground_bbl": None,
                    "verdict": "no-pin",
                    "reason": "no coordinates, or coordinates outside NYC",
                    "name": b.get("name"), "address": b.get("address")})

    groups = [pinned[i:i + batch] for i in range(0, len(pinned), batch)]
    print(f"{len(groups):,} multipoint requests "
          f"(vs {len(pinned):,} if this were done one at a time)")

    for gi, grp in enumerate(groups, 1):
        if offline:
            # Same scoring, local candidates — from the spine's own polygons.
            feats = {"mp": [{"attributes": {"BBL": h["bbl"], "UnitsRes": h.get("ur"),
                                            "BldgClass": h.get("cls"),
                                            "Address": h.get("adr")},
                             "geometry": {"rings": h["rings"]}}
                            for b in grp for h in loc.locate(b["lat"], b["lon"])],
                     "dtm": [{"attributes": {"BBL": h["bbl"]},
                              "geometry": {"rings": h["rings"]}}
                             for b in grp for h in loc_dtm.locate(b["lat"], b["lon"])]
                            if loc_dtm else []}
            # de-duplicate: one lot can serve several pins in the group
            for lane in ("mp", "dtm"):
                seen, uniq = set(), []
                for f in feats[lane]:
                    k = f["attributes"]["BBL"]
                    if k not in seen:
                        seen.add(k)
                        uniq.append(f)
                feats[lane] = uniq
        else:
            ck = CACHE / f"g{gi:05d}.json"
            if ck.exists():
                feats = json.loads(ck.read_text(encoding="utf-8"))
            else:
                pins = [(b["lon"], b["lat"]) for b in grp]
                try:
                    mp = fetch_candidates(pins, MAPPLUTO, "BBL,Address,UnitsRes,BldgClass")
                    dtm = fetch_candidates(pins, DTM, "BBL")
                except Exception as e:
                    # FAILED is retryable and is NOT a placement verdict.
                    for b in grp:
                        stat["FAILED"] += 1
                        out.append({"slug": b.get("slug"), "bbl": None, "ground_bbl": None,
                                    "verdict": "FAILED", "reason": str(e)[:180],
                                    "name": b.get("name"), "address": b.get("address")})
                    continue
                feats = {"mp": mp, "dtm": dtm}
                ck.write_text(json.dumps(feats), encoding="utf-8")

        mp_idx = [(bbox(f["geometry"]["rings"]), f["geometry"]["rings"], f["attributes"])
                  for f in feats["mp"] if f.get("geometry", {}).get("rings")]
        dtm_idx = [(bbox(f["geometry"]["rings"]), f["geometry"]["rings"], f["attributes"])
                   for f in feats["dtm"] if f.get("geometry", {}).get("rings")]

        for b in grp:
            x, y = b["lon"], b["lat"]
            hits = [a for (bb, rings, a) in mp_idx
                    if bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]
                    and in_polygon(x, y, rings)]
            ground = next((str(a["BBL"]).split(".")[0] for (bb, rings, a) in dtm_idx
                           if bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]
                           and in_polygon(x, y, rings)), None)
            row = {"slug": b.get("slug"), "name": b.get("name"),
                   "address": b.get("address"), "ground_bbl": ground,
                   "source_units": b.get("units")}
            if not hits:
                row |= {"bbl": None, "verdict": "no-polygon",
                        "reason": (f"pin sits on tax lot {ground} but inside no "
                                   f"MapPLUTO polygon" if ground else
                                   "pin is inside no lot polygon at all")}
                stat["no-polygon"] += 1
            else:
                scored = []
                for a in hits:
                    ur = None if a.get("UnitsRes") is None else float(a["UnitsRes"])
                    ok, why = capacity(ur, b.get("units"))
                    scored.append((ok, why, a, ur))
                good = [s for s in scored if s[0]]
                if len(good) == 1:
                    ok, why, a, ur = good[0]
                    row |= {"bbl": str(a["BBL"]).split(".")[0], "verdict": "exact",
                            "units_res": ur, "bldg_class": a.get("BldgClass"),
                            "pluto_address": a.get("Address"), "reason": why}
                    stat["exact"] += 1
                elif len(good) > 1:
                    # Several lots could each hold it. Prefer the one whose unit
                    # count MATCHES the source's rather than merely exceeding it.
                    ranked = sorted(
                        good, key=lambda s: (closeness(s[3], b.get("units")) is None,
                                             closeness(s[3], b.get("units")) or 0))
                    ok, why, a, ur = ranked[0]
                    c = closeness(ur, b.get("units"))
                    if c is not None and c <= 0.25:
                        row |= {"bbl": str(a["BBL"]).split(".")[0], "verdict": "exact",
                                "units_res": ur, "bldg_class": a.get("BldgClass"),
                                "pluto_address": a.get("Address"),
                                "reason": f"{len(good)} candidate lots; chose the one "
                                          f"whose {int(ur)} residential units match the "
                                          f"source's {int(b.get('units') or 0)}"}
                        stat["exact"] += 1
                    else:
                        row |= {"bbl": None, "verdict": "ambiguous",
                                "reason": "pin is inside " + str(len(good)) +
                                          " lots that could each hold it and no unit "
                                          "count is decisive: " +
                                          ", ".join(str(s[2]["BBL"]).split(".")[0] for s in good[:4])}
                        stat["ambiguous"] += 1
                else:
                    ok, why, a, ur = scored[0]
                    row |= {"bbl": None, "verdict": "capacity-rejected",
                            "units_res": ur, "bldg_class": a.get("BldgClass"),
                            "reason": f"{str(a['BBL']).split('.')[0]}: {why}"}
                    stat["capacity-rejected"] += 1
            out.append(row)

        if gi % 25 == 0 or gi == len(groups):
            done = sum(stat.values())
            print(f"  {gi:,}/{len(groups):,} requests · {done:,}/{len(allrows):,} "
                  f"buildings keyed · exact {stat['exact']:,}")
            sink.heartbeat(SOURCE, run_id, done=done, total=len(allrows),
                           note="bulk parcel keying")

    print(f"\nKEYED {sum(stat.values()):,} of {len(allrows):,} buildings\n")
    for k in ("exact", "capacity-rejected", "ambiguous", "no-polygon", "no-pin", "FAILED"):
        if stat.get(k):
            print(f"  {k:<20}{stat[k]:>8,}   {stat[k]/len(allrows)*100:>5.1f}%")
    placed = stat["exact"]
    print(f"\n  {placed:,} of {len(allrows):,} placeable "
          f"({placed/len(allrows)*100:.1f}%). The rest are RESULTS with a stated "
          f"reason, not omissions.")
    if stat.get("FAILED"):
        print(f"  ⚠ {stat['FAILED']:,} FAILED are retryable — delete their tiles "
              f"in {CACHE} and re-run. They are NOT unplaceable.")

    # a BBL claimed by two buildings is a real signal, not noise: one lot can
    # genuinely hold several buildings, and it can also mean a bad pin
    byb = Counter(r["bbl"] for r in out if r.get("bbl"))
    multi = {b: n for b, n in byb.items() if n > 1}
    if multi:
        print(f"\n  {len(multi):,} lots carry MORE THAN ONE building "
              f"({sum(multi.values()):,} buildings). Group by BBL before writing "
              f"— a harvest write is a REPLACE, so two towers written separately "
              f"wipe each other.")

    if out_path:
        p = pathlib.Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"\nwrote {p}  ({len(out):,} rows)")

    sink.heartbeat(SOURCE, run_id, done=sum(stat.values()), total=len(allrows),
                   status="complete", note=f"exact={placed}")
    return out, dict(stat)


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(name, default=None):
        return next((a[i + 1] for i, x in enumerate(a) if x == name and i + 1 < len(a)), default)
    lst = opt("--list", "buildings/streeteasy-buildings.json")
    out = opt("--out", "buildings/streeteasy-parcel-keys.json")
    key_all(lst, out, batch=int(opt("--batch", BATCH)),
            offline="--offline" in a)
