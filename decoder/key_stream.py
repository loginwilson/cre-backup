"""KEY BY STREAMING — 41,765 pins against 1.7M polygons, in bounded memory.

    python key_stream.py --list buildings/streeteasy-buildings.json \
                         --out  buildings/streeteasy-parcel-keys.json

WHY NOT `key_buildings.py --offline`

    That loads every polygon into a dict and queries pins against it. At 2,856
    buildings it was fine; at 1.7M polygons it is a MemoryError — 406 MB of JSON
    becomes several GB as Python objects, and both layers are needed.

    So the index is INVERTED. There are 41,765 pins and 1,714,708 polygons, so
    index the small side: build a grid over the PINS, then stream the geometry
    page files once, testing each polygon only against the pins in the cells its
    bounding box covers. Memory is the pin index plus the results; the polygons
    are read and discarded a page at a time.

    Same answers, because the geometric test is unchanged — only the direction
    of the lookup differs.

⚠ MapPLUTO IS THE MATCHER, THE TAX MAP IS THE CROSS-CHECK. For a condominium,
    MapPLUTO returns the BILLING lot (the parcel StreetEasy, DOF and the spine
    all key on) while the DOF tax map returns the physical BASE lot underneath.
    Both are recorded. They agree except on condominiums, and disagreement is
    information rather than error.

⚠ CAPACITY IS TWO-SIDED. A lot with 0 residential units cannot host a rental
    building; a lot with many TIMES the building's own unit count is a pin that
    drifted onto a bigger neighbour. The Cove (123 units) landing on Skyline
    Tower (802) passes a one-sided test and is still the wrong building.
"""
import json, math, os, pathlib, sys, time
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sink

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SOURCE = "STREETEASY"
SPINE_DIR = pathlib.Path(os.environ.get(
    "DECODER_SPINE", pathlib.Path(__file__).with_name("spine")))
GEO = SPINE_DIR / "geometry"
CELL = 0.002                     # ~200 m
NYC = (-74.30, 40.47, -73.68, 40.93)


def in_ring(x, y, ring):
    inside, n, j = False, len(ring), len(ring) - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def in_polygon(x, y, rings):
    """Esri packs outer rings and HOLES into one array, so PARITY decides: an odd
    number of containing rings is inside, an even number is a courtyard. Counting
    a hole as an outer ring places a pin in the middle of a block onto the
    building that surrounds it."""
    return sum(1 for r in rings if len(r) > 2 and in_ring(x, y, r)) % 2 == 1


def capacity(units_res, source_units):
    if units_res is None:
        return False, "matched lot has no unitsres"
    if units_res <= 0:
        return False, "lot records 0 residential units"
    if not source_units or source_units <= 0:
        return True, "source states no unit count — capacity UNTESTED, not passed"
    if units_res * 3 < source_units:
        return False, (f"lot holds {int(units_res)} res units vs the source's "
                       f"{int(source_units)} — a 3x shortfall")
    # ⚠ "TOO LARGE" FLAGS, IT DOES NOT REJECT — and getting this wrong cost 71
    # correct placements. A 447-unit building on a 1,712-unit lot is ordinary in
    # Battery Park City, where one tax lot carries several towers. Rejecting on
    # the upper bound trades a false positive for a false NEGATIVE, and the false
    # negative is the worse one because it is silent: the building simply never
    # appears in any comp set, with nothing downstream to reveal the absence.
    #
    # The case it was written for — The Cove (123 units) landing inside Skyline
    # Tower's lot (802) — is caught by the closeness ranking instead, because
    # Skyline's own listing keys to that lot and matches it far better.
    if source_units >= 10 and units_res > source_units * 3:
        return True, (f"OVERSIZED LOT: {int(units_res)} res units against this "
                      f"building's {int(source_units)} — placed, but the pin may "
                      f"have drifted onto a bigger neighbour")
    return True, None


def closeness(units_res, source_units):
    """Two independent counts of one building should agree. 1 QPS states 391
    units and lot 4004250001 records exactly 391."""
    if not units_res or not source_units:
        return None
    return abs(units_res - source_units) / max(source_units, 1)


def load_pins(path):
    rows = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    pins, nopin = [], []
    for b in rows:
        lat, lon = b.get("lat"), b.get("lon")
        if (isinstance(lat, (int, float)) and isinstance(lon, (int, float))
                and NYC[1] <= lat <= NYC[3] and NYC[0] <= lon <= NYC[2]):
            pins.append(b)
        else:
            nopin.append(b)
    return rows, pins, nopin


def sweep(layer, pins, want_attrs):
    """Stream one layer's pages, collecting every polygon that contains a pin."""
    grid = defaultdict(list)
    for i, b in enumerate(pins):
        grid[f"{int(b['lon']/CELL)},{int(b['lat']/CELL)}"].append(i)

    hits = defaultdict(list)
    files = sorted((GEO / layer).glob("p*.json"))
    if not files:
        raise SystemExit(f"no geometry for {layer} — run spine_geometry.py --pull {layer}")
    scanned = 0
    for fp in files:
        for r in json.loads(fp.read_text(encoding="utf-8")):
            rings = r.get("rings")
            if not rings:
                continue
            scanned += 1
            xs = [p[0] for ring in rings for p in ring]
            ys = [p[1] for ring in rings for p in ring]
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
            cand = set()
            for cx in range(int(x0 / CELL), int(x1 / CELL) + 1):
                for cy in range(int(y0 / CELL), int(y1 / CELL) + 1):
                    cand.update(grid.get(f"{cx},{cy}", ()))
            for i in cand:
                b = pins[i]
                if x0 <= b["lon"] <= x1 and y0 <= b["lat"] <= y1 \
                        and in_polygon(b["lon"], b["lat"], rings):
                    hits[i].append({k: r.get(k) for k in want_attrs} | {"bbl": r["bbl"]})
    print(f"  {layer}: {scanned:,} polygons streamed · {len(hits):,} pins landed inside one")
    return hits


def key(list_path, out_path):
    run_id = f"keyer-stream-{int(time.time())}"
    allrows, pins, nopin = load_pins(list_path)
    print(f"building list: {len(allrows):,} rows · {len(pins):,} with a usable NYC pin "
          f"· {len(nopin):,} without")
    sink.heartbeat(SOURCE, run_id, done=0, total=len(allrows), note="parcel keying")

    t0 = time.time()
    mp = sweep("mappluto", pins, ["ur", "cls", "adr"])
    dtm = sweep("dtm", pins, [])
    print(f"  streamed both layers in {time.time()-t0:,.0f}s")

    # ⚠ CAPACITY IS A PER-LOT QUESTION, NOT A PER-BUILDING ONE.
    # One tax lot can carry several buildings — 1000160100 holds 395/365/385/345
    # South End Avenue, 1,128 units between them against the lot's 1,712. Tested
    # one at a time each looks "3x too LARGE" and is rejected; summed they pass
    # easily. That is the Gotham Point arithmetic (689 + 443 = 1,132 = unitsres)
    # applied the right way round. So the source unit count compared against a
    # lot is the SUM of every building whose pin landed in it.
    lot_units = defaultdict(int)
    for i, b in enumerate(pins):
        for a in mp.get(i, []):
            lot_units[a["bbl"]] += int(b.get("units") or 0)

    out, stat = [], Counter()
    for b in nopin:
        stat["no-pin"] += 1
        out.append({"slug": b.get("slug"), "bbl": None, "ground_bbl": None,
                    "verdict": "no-pin", "reason": "no coordinates, or outside NYC",
                    "name": b.get("name"), "address": b.get("address")})

    for i, b in enumerate(pins):
        cands = mp.get(i, [])
        ground = (dtm.get(i) or [{}])[0].get("bbl")
        row = {"slug": b.get("slug"), "name": b.get("name"), "address": b.get("address"),
               "ground_bbl": ground, "source_units": b.get("units"),
               "area": b.get("area"), "se_id": b.get("seId"),
               "active_rentals": b.get("activeRentals")}
        if not cands:
            row |= {"bbl": None, "verdict": "no-polygon",
                    "reason": (f"pin is on tax lot {ground} but inside no MapPLUTO polygon"
                               if ground else "pin is inside no lot polygon at all")}
            stat["no-polygon"] += 1
        else:
            scored = []
            for a in cands:
                ur = None if a.get("ur") is None else float(a["ur"])
                # compare against every building on this lot, not just this one
                # ⚠ JUDGE EACH BUILDING ON ITS OWN EVIDENCE. Testing against the
                # SUM of every building on the lot couples them: four badly-placed
                # pins inflate the total and reject the one that belongs. Tried
                # both ways — the sum rejected 794, per-building rejects 587, and
                # the extra 207 were legitimate placements dragged down by their
                # neighbours. `lot_units` is still computed and reported, because
                # knowing a lot carries several buildings matters to the PULL
                # (a write is a REPLACE); it just must not gate placement.
                ok, why = capacity(ur, b.get("units"))
                if ok and why is None and b.get("units") and ur and ur > (b["units"] or 0) * 3:
                    why = (f"OVERSIZED LOT: {int(ur)} res units against this "
                           f"building's {int(b['units'])}")
                scored.append((ok, why, a, ur))
            good = [s for s in scored if s[0]]
            if len(good) == 1:
                ok, why, a, ur = good[0]
                row |= {"bbl": a["bbl"], "verdict": "exact", "units_res": ur,
                        "bldg_class": a.get("cls"), "pluto_address": a.get("adr"),
                        "reason": why}
                stat["exact"] += 1
            elif len(good) > 1:
                ranked = sorted(good, key=lambda s: (closeness(s[3], b.get("units")) is None,
                                                     closeness(s[3], b.get("units")) or 0))
                ok, why, a, ur = ranked[0]
                c = closeness(ur, b.get("units"))
                if c is not None and c <= 0.25:
                    row |= {"bbl": a["bbl"], "verdict": "exact", "units_res": ur,
                            "bldg_class": a.get("cls"), "pluto_address": a.get("adr"),
                            "reason": f"{len(good)} candidates; chose the one whose "
                                      f"{int(ur)} res units match the source's "
                                      f"{int(b.get('units') or 0)}"}
                    stat["exact"] += 1
                else:
                    row |= {"bbl": None, "verdict": "ambiguous",
                            "reason": f"pin is inside {len(good)} lots that could each hold "
                                      f"it and no unit count is decisive: " +
                                      ", ".join(s[2]["bbl"] for s in good[:4])}
                    stat["ambiguous"] += 1
            else:
                ok, why, a, ur = scored[0]
                row |= {"bbl": None, "verdict": "capacity-rejected", "units_res": ur,
                        "bldg_class": a.get("cls"), "reason": f"{a['bbl']}: {why}"}
                stat["capacity-rejected"] += 1
        out.append(row)

    print(f"\nKEYED {len(out):,} of {len(allrows):,} buildings\n")
    for k in ("exact", "capacity-rejected", "ambiguous", "no-polygon", "no-pin"):
        if stat.get(k):
            print(f"  {k:<20}{stat[k]:>8,}   {stat[k]/len(allrows)*100:>5.1f}%")
    flagged = sum(1 for r in out if "OVERSIZED" in (r.get("reason") or ""))
    if flagged:
        print(f"  {'(of which flagged':<20}{flagged:>8,}   oversized lot — placed, worth review)")

    # ⚠ ONE LOT CAN HOLD SEVERAL BUILDINGS, AND A HARVEST WRITE IS A REPLACE.
    # Gotham Point is two towers on lot 4000067503 (689 + 443 = 1,132, exactly
    # its unitsres). Written in separate passes they wipe each other. Grouped
    # here so the puller merges within a lot — and NEVER across lots, however
    # much two lots share a project name.
    byb = Counter(r["bbl"] for r in out if r.get("bbl"))
    multi = {b: n for b, n in byb.items() if n > 1}
    print(f"\n  {len(byb):,} distinct parcels carry a building")
    if multi:
        print(f"  ⚠ {len(multi):,} parcels carry MORE THAN ONE building "
              f"({sum(multi.values()):,} buildings). The puller must group by BBL "
              f"before writing.")
    p = pathlib.Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nwrote {p} ({len(out):,} rows)")
    sink.heartbeat(SOURCE, run_id, done=len(out), total=len(allrows), status="complete",
                   note=f"exact={stat['exact']}")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(n, d=None):
        return next((a[i+1] for i, x in enumerate(a) if x == n and i+1 < len(a)), d)
    key(opt("--list", "buildings/streeteasy-buildings.json"),
        opt("--out", "buildings/streeteasy-parcel-keys.json"))
