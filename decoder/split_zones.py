"""Split-district lots: measure the per-district share of a tax lot, then apply
ZR 77-22 to get the one FAR that is actually lawful there.

WHY THIS EXISTS
    PLUTO publishes a single residfar/commfar/facilfar per lot. On a lot divided
    by a district boundary that number is not the lot's FAR — it is one of the
    two districts' FARs, silently chosen. DCP's Zoning Tax Lot Database names
    both districts but publishes no split percentage. So the percentage has to be
    measured.

THE RULE (ZR 77-22, quoted from zr.planning.nyc.gov):
    "The maximum floor area ratio permitted on each portion of such zoning lot
     ... shall be determined under the applicable regulations. Each such floor
     area ratio shall be multiplied by the percentage of the zoning lot to which
     such floor area ratio applies. The sum of the products thus obtained shall
     be the adjusted maximum floor area ratio applicable to such zoning lot."
    -> adjusted_FAR = Σ (FAR_i × share_i).  Area-weighted, not max, not first.

METHOD
    DOF tax-lot polygon (via MapPLUTO's FeatureServer) ∩ DCP zoning-district
    polygons (nyzd), both requested in EPSG:2263 (NY State Plane Long Island,
    US survey feet) so shapely areas come back in square feet with no
    reprojection step of our own to get wrong.

    True polygon intersection — not grid sampling. The BKREA app samples because
    a browser has no geometry library; here shapely is available, so this is the
    stricter computation and can be used to check that estimator.

WHAT IS REPORTED, ALWAYS
    - polygon area vs PLUTO's stated lot area (external proof the geometry is
      the right lot)
    - coverage: Σ intersected area ÷ polygon area. Zoning boundaries and tax-lot
      boundaries are drawn independently and do not align perfectly; coverage
      well under 100% means the shares are not trustworthy for this lot.
    Nothing is repaired to make a number look better.
"""
import json, math, sys, time, urllib.parse, urllib.request

ARC = "https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services"
# DOF's own Digital Tax Map — the authority on where a tax lot is, and the
# arbitrator this project already ranks above PLUTO. Using MapPLUTO's outline as
# a proxy for it returned a 1,625 sf two-ring FRAGMENT for BBL 3025200100 whose
# own LotArea attribute said 65,000; the DTM returns 74,925. Shares measured on
# that fragment looked flawless — 100% coverage, two tidy districts — because a
# ratio cannot tell you it was taken over the wrong footprint.
DTM = ("https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services"
       "/Digital_Tax_Map_VIEW/FeatureServer/5")
SR = 2263  # NY State Plane Long Island, US survey feet -> shapely area is ft²

# DTM flags worth carrying: an air lot or an easement lot has a footprint that
# does not mean what a normal lot's footprint means.
DTM_FLAGS = ("CONDO_FLAG", "AIR_LOT_FLAG", "EASEMENT_FLAG", "SUB_LOT_FLAG",
             "BILL_BBL_FLAG", "REUC_FLAG", "LOT_NOTE")


def _get(url, params, tries=3):
    q = urllib.parse.urlencode(params)
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(f"{url}?{q}", timeout=90) as f:
                return json.load(f)
        except Exception as e:              # transient ArcGIS 5xx / timeouts
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{url} failed after {tries}: {last}")


def _collect(gj, out, flags, key):
    from shapely.geometry import shape
    for feat in gj.get("features") or []:
        p = feat.get("properties") or {}
        raw = p.get(key)
        if raw in (None, ""):
            continue
        b = str(int(float(raw)))
        g = shape(feat["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        # a lot can be carried as several features — union, never last-wins
        out[b] = out[b].union(g) if b in out else g
        if flags is not None:
            flags.setdefault(b, {}).update(
                {k: p[k] for k in DTM_FLAGS if p.get(k) not in (None, "")})
    return out


def lot_polygons(bbls, flags=None):
    """BBL -> shapely geometry in state-plane feet.

    DOF's Digital Tax Map first; MapPLUTO only for lots the DTM does not return,
    and the caller is told which source each lot came from via `flags`.
    """
    out = {}
    bbls = [str(int(b)) for b in bbls]
    for i in range(0, len(bbls), 25):
        chunk = bbls[i:i + 25]
        gj = _get(f"{DTM}/query", {
            "where": "BBL IN (" + ",".join(f"'{b}'" for b in chunk) + ")",
            "outFields": "BBL," + ",".join(DTM_FLAGS), "returnGeometry": "true",
            "outSR": SR, "f": "geojson"})
        _collect(gj, out, flags, "BBL")
    if flags is not None:
        for b in out:
            flags.setdefault(b, {})["geometry_source"] = "DOF Digital Tax Map"

    missing = [b for b in bbls if b not in out]
    for i in range(0, len(missing), 25):
        chunk = missing[i:i + 25]
        gj = _get(f"{ARC}/MAPPLUTO/FeatureServer/0/query", {
            "where": "BBL IN (" + ",".join(chunk) + ")",
            "outFields": "BBL,LotArea", "returnGeometry": "true",
            "outSR": SR, "f": "geojson"})
        _collect(gj, out, flags, "BBL")
        if flags is not None:
            for b in chunk:
                if b in out:
                    flags.setdefault(b, {})["geometry_source"] = \
                        "MapPLUTO (DOF Digital Tax Map had no polygon)"
    return out


def zoning_polygons(bounds, pad=200.0):
    """nyzd base-district polygons intersecting a state-plane bbox (feet)."""
    from shapely.geometry import shape
    w, s, e, n = bounds
    gj = _get(f"{ARC}/nyzd/FeatureServer/0/query", {
        "geometry": f"{w-pad},{s-pad},{e+pad},{n+pad}",
        "geometryType": "esriGeometryEnvelope", "inSR": SR,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "ZONEDIST", "returnGeometry": "true",
        "outSR": SR, "f": "geojson"})
    out = []
    for feat in gj.get("features") or []:
        d = ((feat.get("properties") or {}).get("ZONEDIST") or "").strip()
        g = feat.get("geometry")
        if not d or not g:
            continue
        geom = shape(g)
        if not geom.is_valid:
            geom = geom.buffer(0)
        out.append((d, geom))
    return out


def overlay_polygons(bounds, pad=200.0):
    """DCP commercial overlays (`nyco`) intersecting a state-plane bbox.

    An overlay is drawn ~100-200 ft deep from the street, so it routinely covers
    PART of a lot. Which part matters: under ZR 33-121 the overlaid portion of a
    residence district carries commercial floor area and the rest carries none,
    so the overlay share is a real measurement, not a yes/no flag.
    """
    from shapely.geometry import shape
    w, s, e, n = bounds
    gj = _get(f"{ARC}/nyco/FeatureServer/0/query", {
        "geometry": f"{w-pad},{s-pad},{e+pad},{n+pad}",
        "geometryType": "esriGeometryEnvelope", "inSR": SR,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "OVERLAY", "returnGeometry": "true",
        "outSR": SR, "f": "geojson"})
    out = []
    for feat in gj.get("features") or []:
        d = ((feat.get("properties") or {}).get("OVERLAY") or "").strip()
        g = feat.get("geometry")
        if not d or not g:
            continue
        geom = shape(g)
        if not geom.is_valid:
            geom = geom.buffer(0)
        out.append((d, geom))
    return out


def shares_for(bbl, lot_geom, zones, stated_lot_area=None):
    """Measured per-district shares of one lot. Returns a dict that states its
    own trustworthiness rather than a bare percentage."""
    poly_area = lot_geom.area
    by_dist = {}
    for d, zg in zones:
        if not zg.intersects(lot_geom):
            continue
        a = zg.intersection(lot_geom).area
        if a > 0:
            by_dist[d] = by_dist.get(d, 0.0) + a
    covered = sum(by_dist.values())
    shares = {d: a / covered for d, a in by_dist.items()} if covered else {}
    # PLUTO's own lot area is the external check that we grabbed the right lot
    area_delta = None
    if stated_lot_area:
        area_delta = (poly_area - stated_lot_area) / stated_lot_area
    return {
        "bbl": bbl,
        "polygon_area_sf": round(poly_area, 1),
        "pluto_lot_area_sf": stated_lot_area,
        "polygon_vs_pluto": None if area_delta is None else round(area_delta, 4),
        "district_area_sf": {d: round(a, 1) for d, a in
                             sorted(by_dist.items(), key=lambda kv: -kv[1])},
        "shares": {d: round(v, 4) for d, v in
                   sorted(shares.items(), key=lambda kv: -kv[1])},
        "coverage": round(covered / poly_area, 4) if poly_area else 0.0,
        "source": "tax-lot polygon ∩ DCP nyzd, EPSG:2263",
    }


def adjusted_far(shares, far_by_district, use):
    """ZR 77-22: Σ(FAR_i × share_i). Returns (far, note) — and refuses, with a
    reason, rather than guessing past a district it has no FAR for."""
    missing = [d for d in shares if d not in far_by_district]
    if missing:
        return None, f"no FAR on record for {sorted(missing)} — not computed"
    total = 0.0
    parts = []
    for d, sh in shares.items():
        f = far_by_district[d].get(use)
        if f is None:
            return None, f"{d} has no {use} FAR — a portion of the lot permits none"
        total += f * sh
        parts.append(f"{d} {f}×{sh:.3f}")
    return round(total, 4), "ZR 77-22: " + " + ".join(parts)


def measure(bbls, stated_areas=None):
    """Measure a batch. One zoning fetch per lot bbox (lots here are scattered
    across boroughs, so a shared territory bbox would pull the whole city)."""
    stated_areas = stated_areas or {}
    flags = {}
    lots = lot_polygons(bbls, flags)
    out, missing = {}, []
    for b in bbls:
        g = lots.get(str(int(b)))
        if g is None:
            missing.append(b)
            continue
        r = shares_for(b, g, zoning_polygons(g.bounds), stated_areas.get(b))
        r.update(flags.get(str(int(b))) or {})
        # Overlay coverage on the SAME footprint. Two readings are kept: the
        # share of the whole lot, and — the one ZR 33-121 actually needs — how
        # much of EACH zoning district's portion the overlay reaches, since the
        # overlay grants commercial floor area only where it lands.
        zones = zoning_polygons(g.bounds)
        ov, per_district = {}, {}
        for od, og in overlay_polygons(g.bounds):
            if not og.intersects(g):
                continue
            inter = og.intersection(g)
            if inter.area <= 0:
                continue
            ov[od] = ov.get(od, 0.0) + inter.area
            for zd, zg in zones:
                if zg.intersects(inter):
                    a = zg.intersection(inter).area
                    if a > 0:
                        per_district.setdefault(zd, {})
                        per_district[zd][od] = per_district[zd].get(od, 0.0) + a
        area = r["polygon_area_sf"]
        r["overlay_shares"] = ({d: round(a / area, 4)
                                for d, a in sorted(ov.items(), key=lambda kv: -kv[1])}
                               if area else {})
        r["overlay_by_district"] = {
            zd: {"overlay": max(v, key=v.get),
                 "covered_fraction_of_district": round(
                     sum(v.values()) / r["district_area_sf"][zd], 4)}
            for zd, v in per_district.items() if r["district_area_sf"].get(zd)}
        out[b] = r
    return out, missing


if __name__ == "__main__":
    import pathlib
    base = json.load(open(pathlib.Path(__file__).with_name("baselines.json"),
                          encoding="utf-8"))
    want = sys.argv[1:] or [k for k, v in base.items()
                            if (v.get("dcp_zoning") or {}).get("zoning_district_2")]
    res, missing = measure(want, {k: (base.get(k) or {}).get("lot_area") for k in want})
    for b in want:
        r = res.get(b)
        if not r:
            print(f"{b}  NO POLYGON")
            continue
        print(f"{b}  poly {r['polygon_area_sf']:>10,.0f} sf  vs pluto "
              f"{(r['pluto_lot_area_sf'] or 0):>10,.0f}  "
              f"({(r['polygon_vs_pluto'] or 0)*100:+.1f}%)  coverage {r['coverage']*100:.1f}%")
        for d, sh in r["shares"].items():
            print(f"        {d:<12} {sh*100:6.2f}%   {r['district_area_sf'][d]:>10,.0f} sf")
    if missing:
        print("no MapPLUTO polygon for:", missing)

MIH = ("https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services"
       "/nycmih/FeatureServer/0")


def mih_areas(bounds, pad=100.0):
    """Mandatory Inclusionary Housing areas intersecting a state-plane bbox.

    MIH is not a flag on a lot, it is a MAPPED AREA with an OPTION and an
    ADOPTION DATE — 279 of them citywide. Three consequences:

      * it is geometric, so a lot can be partly in and partly out;
      * the OPTION (1 / 2 / 3, deep affordability, workforce) sets the
        affordability required, and therefore which ZR 23-22 column applies;
      * it is DATED, so whether MIH applied to a 2014 instrument is a different
        question from whether it applies today.
    """
    from shapely.geometry import shape
    w, s_, e, n = bounds
    gj = _get(f"{MIH}/query", {
        "geometry": f"{w-pad},{s_-pad},{e+pad},{n+pad}",
        "geometryType": "esriGeometryEnvelope", "inSR": SR,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "Status,ProjectNam,DateAdopte,ZR_ULURPno,MIH_Option,CD",
        "returnGeometry": "true", "outSR": SR, "f": "geojson"})
    out = []
    for feat in gj.get("features") or []:
        pr = feat.get("properties") or {}
        g = feat.get("geometry")
        if not g:
            continue
        geom = shape(g)
        if not geom.is_valid:
            geom = geom.buffer(0)
        out.append((pr, geom))
    return out


def mih_for_lot(lot_geom):
    """Which MIH area(s) cover this lot, and how much of it."""
    from datetime import datetime, timezone
    area = lot_geom.area
    hits = []
    for pr, geom in mih_areas(lot_geom.bounds):
        if not geom.intersects(lot_geom):
            continue
        cov = geom.intersection(lot_geom).area
        if cov <= 0:
            continue
        ms = pr.get("DateAdopte")
        adopted = (datetime.fromtimestamp(ms / 1000, timezone.utc).date().isoformat()
                   if isinstance(ms, (int, float)) else None)
        hits.append({"project": pr.get("ProjectNam"), "option": pr.get("MIH_Option"),
                     "status": pr.get("Status"), "adopted": adopted,
                     "ulurp": pr.get("ZR_ULURPno"), "community_district": pr.get("CD"),
                     "covered_fraction_of_lot": round(cov / area, 4) if area else None})
    return sorted(hits, key=lambda h: -(h["covered_fraction_of_lot"] or 0))
