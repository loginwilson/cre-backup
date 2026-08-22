"""SPINE GEOMETRY — give every parcel its polygon, so keying never needs a server.

    python spine_geometry.py --pull mappluto      # ~430 requests, resumable
    python spine_geometry.py --pull dtm           # ~430 requests, resumable
    python spine_geometry.py --index              # build the grid index
    python spine_geometry.py --locate 40.7480 -73.9400

WHY, IN ONE LINE

    Login, 2026-08-06: *"give the spine geometry."* The spine was built with
    `returnGeometry=false`, so 1,175,952 parcels carry a BBL, a kind and a
    lineage — and not one coordinate. Every spatial question therefore had to be
    asked of ArcGIS at the moment it came up.

    With polygons on disk, keying becomes a LOCAL JOIN: 41,816 StreetEasy
    buildings, every DOF condo sale, any DOB filing with a coordinate — all
    answered from memory, forever, with no network in the path and no rate limit
    to respect. The bulk keyer already cut 41,816 requests to ~420 by batching;
    this takes it to zero.

⚠ TWO LAYERS, BECAUSE NEITHER IS THE WHOLE PARCEL UNIVERSE
    Measured on one pin near Gotham Point: the DOF tax map returns 4000160001
    (the physical BASE lot); MapPLUTO returns 4000167501 (the condominium
    BILLING lot). That is the condo split, not a disagreement.

      MapPLUTO  the MATCHER — returns the BBL StreetEasy, DOF sales and the app
                all key on, including the 11,132 condo billing lots that appear
                in no DTM layer at all
      DTM       the GROUND — the legal tax lot, including the condo BASE lots
                MapPLUTO drops

    Pull MapPLUTO first: it is what placement actually resolves against.

⚠ A GENERALISED POLYGON IS A WRONG ANSWER WAITING TO HAPPEN. `maxAllowableOffset`
    would shrink the download substantially and it is not used here. NYC lots are
    routinely 20 ft wide; simplifying their outlines moves boundaries by metres
    and silently reassigns pins near a lot line — the exact error this whole
    exercise exists to remove. `geometryPrecision=6` (~0.1 m) is applied instead,
    which drops digits rather than vertices.

⚠ THREE OUTCOMES. A page that fails RAISES and the tile is not written, so a
    re-run refetches it. A tile written short would look complete forever.
"""
import json, math, os, pathlib, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SPINE_DIR = pathlib.Path(os.environ.get(
    "DECODER_SPINE", pathlib.Path(__file__).with_name("spine")))
GEO = SPINE_DIR / "geometry"

LAYERS = {
    "mappluto": {
        "url": ("https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/"
                "services/MAPPLUTO/FeatureServer/0/query"),
        "fields": "BBL,UnitsRes,BldgClass,Address",
        "bbl": "BBL", "page": 2000,
    },
    "dtm": {
        "url": ("https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/"
                "services/Tax_Lot_View/FeatureServer/0/query"),
        "fields": "BBL",
        "bbl": "BBL", "page": 2000,
    },
}

# ~0.002 deg is roughly 200 m: small enough that a cell holds tens of lots, big
# enough that the index is a few hundred thousand keys rather than millions.
CELL = 0.002


def _post(url, params, tries=5):
    body = urllib.parse.urlencode(params).encode()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"})
            with urllib.request.urlopen(req, timeout=600) as f:
                d = json.load(f)
            if "error" in d:
                raise RuntimeError(str(d["error"])[:200])
            return d
        except Exception as e:
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"FAILED after {tries} tries: {type(last).__name__}: {last}")


def pull(layer, resume=True):
    """Every polygon in the layer, paged and tiled to disk.

    Resumable by construction: each page is its own file, so an interrupted run
    at page 300 of 430 keeps 300 pages. That matters because this is a download
    measured in tens of minutes and it WILL be interrupted.
    """
    cfg = LAYERS[layer]
    out = GEO / layer
    out.mkdir(parents=True, exist_ok=True)
    page, off, wrote, feats = cfg["page"], 0, 0, 0

    # count first, so progress has a denominator instead of being a rising number
    tot = _post(cfg["url"], {"where": "1=1", "returnCountOnly": "true", "f": "json"})
    total = tot.get("count")
    print(f"{layer}: {total:,} features -> ~{math.ceil(total / page):,} pages")

    while True:
        pf = out / f"p{off:07d}.json"
        if resume and pf.exists():
            off += page
            wrote += 1
            continue
        d = _post(cfg["url"], {
            "where": "1=1", "outFields": cfg["fields"], "returnGeometry": "true",
            "outSR": 4326, "geometryPrecision": 6,
            "resultOffset": off, "resultRecordCount": page,
            "orderByFields": cfg["bbl"], "f": "json"})
        fs = d.get("features", [])
        if not fs:
            break
        rows = []
        for f in fs:
            rings = (f.get("geometry") or {}).get("rings")
            if not rings:
                continue                    # a lot with no polygon: real, and unusable here
            a = f["attributes"]
            b = str(a.get(cfg["bbl"]) or "").split(".")[0]
            if len(b) != 10:
                continue
            rows.append({"bbl": b, "rings": rings,
                         **({"ur": a.get("UnitsRes"), "cls": a.get("BldgClass"),
                             "adr": a.get("Address")} if layer == "mappluto" else {})})
        pf.write_text(json.dumps(rows), encoding="utf-8")
        wrote += 1
        feats += len(rows)
        off += page
        if wrote % 20 == 0:
            print(f"  {off:,}/{total:,} ({off/total*100:.0f}%) · {feats:,} polygons this run")
        if len(fs) < page:
            break
    held = sum(1 for _ in out.glob("p*.json"))
    print(f"  {layer}: {held:,} page files on disk")
    return held


def load(layer):
    """All polygons for a layer, with a reconciliation. A load that silently
    returns fewer parcels than were pulled is the failure mode this project has
    met nine times."""
    out = GEO / layer
    files = sorted(out.glob("p*.json"))
    if not files:
        raise SystemExit(f"no geometry for {layer} — run --pull {layer} first")
    polys, dupes = {}, 0
    for f in files:
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r["bbl"] in polys:
                dupes += 1                  # multi-polygon parcels: keep the first, count the rest
                continue
            polys[r["bbl"]] = r
    print(f"  {layer}: {len(polys):,} parcels with geometry from {len(files):,} pages"
          + (f" ({dupes:,} extra polygons on multi-part parcels)" if dupes else ""))
    return polys


def bbox(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def build_index(layer):
    """Grid index: cell -> [bbl]. Written next to the pages so `locate` is a
    dict lookup plus a handful of ray casts."""
    polys = load(layer)
    grid = defaultdict(list)
    for b, r in polys.items():
        x0, y0, x1, y1 = bbox(r["rings"])
        for cx in range(int(x0 / CELL), int(x1 / CELL) + 1):
            for cy in range(int(y0 / CELL), int(y1 / CELL) + 1):
                grid[f"{cx},{cy}"].append(b)
    p = GEO / f"{layer}_index.json"
    p.write_text(json.dumps({"cell": CELL, "grid": grid}), encoding="utf-8")
    sizes = Counter(len(v) for v in grid.values())
    print(f"  index: {len(grid):,} cells · median {sorted(sizes.elements())[len(list(sizes.elements()))//2]} "
          f"parcels/cell · max {max(sizes)} -> {p}")
    return grid


def in_ring(x, y, ring):
    inside, n = False, len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y):
            if x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi:
                inside = not inside
        j = i
    return inside


def in_polygon(x, y, rings):
    """Esri packs outer rings and HOLES into one `rings` array, so parity decides:
    an odd number of containing rings is inside, an even number is a courtyard."""
    return sum(1 for r in rings if len(r) > 2 and in_ring(x, y, r)) % 2 == 1


class Locator:
    """Local point-in-polygon over the whole city. No network, ever."""

    def __init__(self, layer):
        self.layer = layer
        self.polys = load(layer)
        p = GEO / f"{layer}_index.json"
        if not p.exists():
            raise SystemExit(f"no index — run --index after --pull {layer}")
        d = json.loads(p.read_text(encoding="utf-8"))
        self.cell, self.grid = d["cell"], d["grid"]

    def locate(self, lat, lon):
        """Every parcel whose polygon contains this pin. Usually one; several
        where lots genuinely overlap. Returns [] for a pin on a street bed —
        which is a RESULT, not a failure."""
        key = f"{int(lon / self.cell)},{int(lat / self.cell)}"
        hits = []
        for b in self.grid.get(key, []):
            r = self.polys[b]
            x0, y0, x1, y1 = bbox(r["rings"])
            if x0 <= lon <= x1 and y0 <= lat <= y1 and in_polygon(lon, lat, r["rings"]):
                hits.append(r)
        return hits


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--pull" in a:
        layer = a[a.index("--pull") + 1]
        pull(layer)
    if "--index" in a:
        for layer in (["mappluto", "dtm"] if a[a.index("--index") + 1:] == [] else
                      [a[a.index("--index") + 1]]):
            if (GEO / layer).exists():
                build_index(layer)
    if "--locate" in a:
        i = a.index("--locate")
        lat, lon = float(a[i + 1]), float(a[i + 2])
        loc = Locator("mappluto")
        for h in loc.locate(lat, lon):
            print(f"  {h['bbl']}  ur={h.get('ur')}  {h.get('cls')}  {h.get('adr')}")
    if not a:
        print(__doc__)
