"""Close the split-district FAR gap: measure the shares, apply ZR 77-22, write
the result into baselines.json with its own provenance and confidence.

This is the fix for the one standing audit FAIL. A lot divided by a district
boundary has no single FAR, and PLUTO publishes one anyway — the primary
district's. Until now the audit refused to let those baselines be used. Now they
carry a measured, rule-derived FAR instead, or a stated reason why they cannot.

Pipeline:
    1. measure per-district area shares          (split_zones.py, shapely ∩)
    2. resolve each observed district's FAR      (the app's verified reference)
    3. adjusted FAR = Σ(FAR_i × share_i)         (ZR 77-22)
    4. write baselines[bbl]["split_far"], never overwriting PLUTO's own fields

Every lot lands in exactly one of three states, and the third is not a failure
to hide:
    resolved     shares measured, coverage sound, every district has a FAR
    unresolved   a district on the lot has no FAR on record (e.g. PARK) or the
                 geometry did not cover the lot — reported, not guessed
    not-split    the measurement found one district; DCP's second district is a
                 sliver or stale, and PLUTO's single FAR is correct after all

Usage: python close_split_far.py [--write]
"""
import json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).parent
BASELINES = HERE / "baselines.json"
SHARES = HERE / "split_zone_shares.json"
ZREF = HERE / "zoning_reference.json"
APP = pathlib.Path("C:/dev/bkrea-territory-intelligence-app")

sys.path.insert(0, str(HERE))
import split_zones as sz

# below this a district's slice is boundary noise between two independently drawn
# layers, not a real portion of the zoning lot. Reported, but excluded from the
# weighting (and the exclusion is stated on the record).
SLIVER = 0.01
MIN_COVERAGE = 0.97   # Σ intersected ÷ polygon area; below this the shares are not trustworthy

# nyzd categories that are not zoning districts. Land under these carries no FAR
# because no district is mapped over it, which is a different thing from a
# district whose FAR happens to be zero.
UNZONED = {"PARK", "PARKS", "BALL FIELD", "PUBLIC PLACE", "ROW"}

# A polygon much SMALLER than the lot area the same record states is a FRAGMENT,
# not the lot — MapPLUTO returns two small counter-clockwise rings totalling
# 1,625 sf for BBL 3025200100 while its own LotArea attribute says 65,000. Shares
# measured on a fragment describe whichever corner survived, and because they are
# ratios they come back looking perfectly well-formed: 100% coverage, two tidy
# districts, no error anywhere. Only the area cross-check catches it.
#
# The test is one-sided on purpose. A polygon LARGER than the stated area is the
# normal case (MapPLUTO's outlines run a few percent generous against DOF's
# reported area) and still covers the whole lot, so the ratios hold.
FRAGMENT_BELOW = -0.15


def load_baselines():
    return json.loads(BASELINES.read_text(encoding="utf-8"))


def split_lots(base):
    return sorted(k for k, v in base.items()
                  if (v.get("dcp_zoning") or {}).get("zoning_district_2"))


def measure(base, bbls, refresh=False):
    if SHARES.exists() and not refresh:
        cached = json.loads(SHARES.read_text(encoding="utf-8"))
        if all(b in cached for b in bbls):
            return cached
    res, missing = sz.measure(bbls, {b: (base.get(b) or {}).get("lot_area") for b in bbls})
    for b in missing:
        res[b] = {"bbl": b, "error": "no MapPLUTO polygon"}
    SHARES.write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def zr_all():
    """Every FAR the decoder needs, each from the ZR section that governs it.

        residential in R6-R12        ZR 23-22
        community facility in R      ZR 24-11
        commercial in C1-C8          ZR 33-122
        community facility in C      ZR 33-123
        commercial under a C1/C2
          OVERLAY on an R district   ZR 33-121 Column A, keyed by the UNDERLYING
                                     residence district
        manufacturing in M           ZR 43-12

    The transcribed reference stays as the fallback for what the Resolution's
    tables do not reach (A-suffix and MX districts, R1-R5), and every value
    records which of the two it came from.
    """
    import zr_feed
    out = {}
    for key in ("facility_R", "commercial_C", "facility_C",
                "commercial_overlay", "manufacturing_M", "uniform_MA"):
        try:
            out[key] = zr_feed.zr_far(key)[0]
        except Exception as e:                     # a section that will not parse
            print(f"   ZR {key} unavailable: {str(e)[:80]}")
            out[key] = {}
    # Residential is NOT a scalar per district — collapsing it to one number is
    # the very error this feed exists to prevent — so it keeps both figures.
    res, rec = zr_residential()
    out["residential_R"] = {
        d: {"residential_narrow": v["base"], "residential_wide": v["wide"],
            "section": rec["section"], "last_amended": rec["last_amended"]}
        for d, v in res.items() if v["base"] is not None}
    return out


def zr_residential():
    """R6–R12 residential FAR straight from ZR 23-22 — the source of record.

    Returns district -> {"base": narrow/unconditional, "wide": within 100 ft of a
    wide street, "cite": ...}. Anything the Resolution does not cover here
    (R1–R5, community facility, commercial, manufacturing) still comes from the
    transcribed reference, and every value carries which one it came from.
    """
    import zr_feed
    table, rec = zr_feed.conditional_far("23-22")
    out = {}
    for d, entries in table.items():
        std = [e for e in entries if e["column"].lower().startswith("standard")]
        if not std:
            continue
        uncond = [e["far"] for e in std if e["condition"] == "unconditional"]
        wide = [e["far"] for e in std if "wide street" in e["condition"].lower()]
        base = min(uncond) if uncond else (min(wide) if wide else None)
        out[d] = {"base": base, "wide": max(wide) if wide else base,
                  "cite": f"ZR {rec['section']} last amended {rec['last_amended']} "
                          f"(fetched {rec['fetched']})"}
    return out, rec


def far_table(districts):
    """Resolve district → FAR through the app's verified reference. MX pairs and
    anything else observed on the ground are passed in explicitly, because the
    reference resolves those at call time rather than storing them as keys."""
    subprocess.run(
        ["npx", "tsx", str(HERE / "dump_zoning_reference.mjs"), str(ZREF),
         ",".join(sorted(districts))],
        cwd=APP, check=True, capture_output=True, shell=True)
    return json.loads(ZREF.read_text(encoding="utf-8"))


USES = {
    # our key -> (reference field, what PLUTO calls it)
    # residential is measured at BOTH street widths: R7-1/R7-2/R8 (and their
    # commercial equivalents) carry different FARs on a wide street, and which
    # one applies is a fact about the lot's frontage that we have not
    # established. Picking one silently is exactly the kind of assumption that
    # reads as a measurement.
    "residfar": ("residential_narrow", "residential_wide", "residfar"),
    "commfar": ("commercial", "commercial", "commfar"),
    "facilfar": ("community_facility", "community_facility", "facilfar"),
}


def permits_none(district, field):
    """Is a blank in the reference a LEGAL zero, or a hole in the reference?

    The two look identical in the table (both null) and mean opposite things: an
    R district really does permit no commercial floor area, while R10A's blank
    community-facility cell is a gap in a hand-transcribed chart. Treating a gap
    as a zero understates an envelope; treating a legal zero as a gap blocks a
    lot that is perfectly computable. So the cases are named, and anything not
    named stays unresolved until the Zoning Resolution itself answers it.
    """
    d = district.upper()
    if field == "commercial":
        # Residence districts permit no commercial floor area as of right. A
        # commercial OVERLAY (nyco) would change that — overlays are a separate
        # layer and are not consulted here, so this holds only for lots with no
        # overlay, which the caller checks.
        return d.startswith("R")
    if field.startswith("residential"):
        # Manufacturing districts permit no as-of-right residential. MX pairs
        # ("M1-8A/R11") do, and resolve through the reference, so they never
        # reach here with a null.
        return d.startswith("M") and "/" not in d
    return False


def parent(d):
    """A contextual variant's parent district: R10A -> R10, C6-3X -> C6-3.

    The Resolution's tables often list only the parent, on the understanding
    that the letter suffix inherits it. Falling back is a documented step, not a
    silent one — every value says whether it came via the parent.
    """
    return re.sub(r"[A-Z]$", "", d) if re.search(r"\d[A-Z]$", d) else d


def district_far(d, use, ZR, zref, field, overlay_pct, special=None):
    """One district's FAR for one use — Resolution first, reference second.

    Returns (value, source) or (None, reason). `overlay_pct` is how much of the
    WHOLE LOT this district's commercial overlay covers, so an overlay that
    reaches half way onto the lot contributes half as much commercial floor area.
    """
    dd = d.upper()
    # ⚠ SPECIAL DISTRICTS SUPERSEDE THE CITYWIDE TABLES, and the failure is
    # silent: every citywide lookup succeeds and the answer is still wrong.
    # ZR 115-21 lifts C6-3 commercial FAR from 6.0 to 8.0 inside Downtown
    # Jamaica — the citywide answer understated BBL 4097930089 by 14%.
    # This must run BEFORE anything else resolves.
    if special:
        import special_districts as sd
        ov = sd.OVERRIDES.get(special)
        if ov:
            table = ov.get(use) or {}
            if dd in table:
                return table[dd], (f"ZR {ov['section']} ({ov.get('last_amended','')}) — "
                                   f"special district {special} SUPERSEDES the citywide table")
        elif sd.status(special) == "unverified":
            return None, (f"{d}: in special district {special}, which has NOT been checked "
                          f"for supersession — a citywide figure here is unsafe")

    # A mixed-use pair is written "M1-8A/R11": the M component governs
    # manufacturing/commercial/community facility, the R component residential.
    m_part = next((p for p in dd.split("/") if p.startswith("M")), None)
    r_part = next((p for p in dd.split("/") if p.startswith("R")), None)
    if r_part and use == "residfar":
        dd = r_part
    elif m_part and use in ("commfar", "facilfar"):
        hit = ZR["uniform_MA"].get(m_part)
        if hit:
            return hit["far"], (f"ZR {hit['section']} ({hit['last_amended']}) — "
                                f"one FAR for all permitted uses in an A-suffix M1")
        dd = m_part

    is_r = dd.startswith("R")
    is_c = dd.startswith("C")

    if use == "residfar":
        hit = ZR["residential_R"].get(dd)
        if hit:
            # `field` selects the street-width variant. R6 is 2.20, or 3.00
            # within 100 ft of a wide street; returning one number for both is
            # how the wide-street rule got deleted from the reference table.
            return hit[field], f"ZR {hit['section']} ({hit['last_amended']})"
    elif use == "facilfar":
        hit = (ZR["facility_R"].get(dd) if is_r else
               ZR["facility_C"].get(dd) if is_c else None)
        if hit:
            return hit["far"], f"ZR {hit['section']} ({hit['last_amended']})"
    elif use == "commfar":
        if is_c:
            hit = ZR["commercial_C"].get(dd)
            if hit:
                return hit["far"], f"ZR {hit['section']} ({hit['last_amended']})"
        elif is_r:
            # A residence district permits commercial floor area ONLY under a
            # C1/C2 overlay, and only on the overlaid part of the lot.
            if not overlay_pct:
                return 0.0, "no commercial overlay measured — a residence district permits none"
            hit = ZR["commercial_overlay"].get(dd) or ZR["commercial_overlay"].get(parent(dd))
            if hit:
                via = "" if dd in ZR["commercial_overlay"] else f" via {parent(dd)}"
                return (hit["far"] * overlay_pct,
                        f"ZR {hit['section']} Col A{via} x {overlay_pct:.1%} overlay coverage")
            return None, (f"{d}: overlay covers {overlay_pct:.1%} of the lot but "
                          f"ZR 33-121 has no row for it or its parent district")

    # fall back to the transcribed reference, and say so
    ref = zref.get(dd)
    v = (ref or {}).get(field)
    if v is not None:
        return v, "transcribed reference (lib/zoningReference.ts)"
    if permits_none(dd, field) and use != "commfar":
        return 0.0, "district permits none"
    return None, (f"{d}: no {use} in the Resolution's tables or the reference — "
                  f"a blank is a gap, not a legal zero")


def adjusted(shares, ZR, zref, use, field, overlay_by_district, special=None):
    """ZR 77-22 weighted FAR: Σ(FAR_i × share_i), where a portion permitting no
    such floor area contributes zero. Returns (value, note) or (None, reason)."""
    parts, total, srcs = [], 0.0, set()
    for d, sh in shares.items():
        f, src = district_far(d, use, ZR, zref, field,
                              overlay_by_district.get(d, 0.0), special)
        if f is None:
            return None, src
        total += f * sh
        srcs.add(src)
        parts.append(f"{d} {round(f, 4)}×{sh:.4f}")
    return round(total, 4), ("ZR 77-22 = " + " + ".join(parts)
                             + "   [" + "; ".join(sorted(srcs)) + "]")


def main(write=False, refresh=False):
    base = load_baselines()
    bbls = split_lots(base)
    print(f"{len(bbls)} split-district parcels in baselines.json\n")

    meas = measure(base, bbls, refresh)
    seen = set()
    for b in bbls:
        seen |= set((meas.get(b) or {}).get("shares") or {})
    print(f"districts observed on the ground: {sorted(seen)}")
    zref = far_table(seen)["districts"]

    # The Zoning Resolution outranks the transcribed table wherever it speaks.
    # Overlay it rather than replace it: ZR 23-22 covers R6-R12 residential; the
    # community-facility, commercial and manufacturing columns still come from
    # the reference, and each value now says which source it came from.
    ZR = zr_all()
    print("ZR sections in play: " + ", ".join(
        f"{k}->{next(iter(v.values()))['section']}" for k, v in ZR.items() if v))
    zr, zr_rec = zr_residential()
    src = {}
    overridden = []
    for d in seen:
        r = dict(zref.get(d) or {})
        if d in zr and zr[d]["base"] is not None:
            was = (r.get("residential_narrow"), r.get("residential_wide"))
            now = (zr[d]["base"], zr[d]["wide"])
            if was != now:
                overridden.append((d, was, now))
            r["residential_narrow"], r["residential_wide"] = now
            src[d] = zr[d]["cite"]
        else:
            src[d] = "transcribed reference (lib/zoningReference.ts)"
        zref[d] = r
    print(f"residential FAR from {zr_rec['url']} (last amended {zr_rec['last_amended']})")
    for d, was, now in overridden:
        print(f"   ZR OVERRIDES the transcribed table: {d} {was} -> {now}")
    absent = sorted(d for d in seen if not (zref.get(d) or {}).get("residential_wide"))
    print(f"no residential FAR on record for: {absent or 'none'}\n")

    resolved = unresolved = not_split = 0
    for b in bbls:
        m = meas.get(b) or {}
        bl = base[b]
        pluto = bl.get("far") or {}
        if m.get("error") or not m.get("shares"):
            print(f"{b}  UNRESOLVED — {m.get('error', 'no shares measured')}")
            bl["split_far"] = {"status": "unresolved", "reason": m.get("error", "no shares measured")}
            unresolved += 1
            continue

        raw = m["shares"]
        kept = {d: s for d, s in raw.items() if s >= SLIVER}
        dropped = {d: s for d, s in raw.items() if s < SLIVER}

        # UNZONED land is not a portion of the zoning lot with a FAR of zero — it
        # is not in the zoning lot at all. Mapped parkland carries no zoning
        # district, so blending it in at 0 would understate the FAR while
        # overstating the lot area, and the two errors do not cancel. Remove it
        # from the weighting and shrink the lot area it applies to instead.
        unzoned = {d: s for d, s in kept.items() if d.upper() in UNZONED}
        for d in unzoned:
            kept.pop(d)
        tot = sum(kept.values())
        zoned_fraction = tot
        kept = {d: s / tot for d, s in kept.items()} if tot else {}

        d_area = m.get("polygon_vs_pluto")
        if d_area is not None and d_area < FRAGMENT_BELOW:
            print(f"{b}  UNRESOLVED — polygon is {m['polygon_area_sf']:,.0f} sf against a "
                  f"stated {m['pluto_lot_area_sf']:,.0f} ({d_area*100:+.1f}%): a fragment, "
                  f"not the lot")
            bl["split_far"] = {
                "status": "unresolved",
                "reason": (f"MapPLUTO polygon {m['polygon_area_sf']:,.0f} sf vs its own "
                           f"LotArea {m['pluto_lot_area_sf']:,.0f} sf ({d_area*100:+.1f}%) — "
                           f"the geometry is a fragment; shares would describe the wrong "
                           f"part of the lot. Needs the DOF Digital Tax Map polygon."),
                "measured_shares": raw, "polygon_area_sf": m["polygon_area_sf"],
                "polygon_vs_pluto": d_area}
            unresolved += 1
            continue

        if m["coverage"] < MIN_COVERAGE:
            print(f"{b}  UNRESOLVED — zoning polygons cover only "
                  f"{m['coverage']*100:.1f}% of the lot")
            bl["split_far"] = {"status": "unresolved",
                               "reason": f"zoning coverage {m['coverage']:.3f} below {MIN_COVERAGE}",
                               "measured_shares": raw}
            unresolved += 1
            continue

        if len(kept) < 2:
            only = next(iter(kept), None)
            why = ("the rest of the lot is unzoned land"
                   if unzoned else "DCP's second district is a sliver")
            print(f"{b}  ONE DISTRICT on the ground — {only} covers "
                  f"{zoned_fraction*100:.1f}% of the lot; {why}")
            bl["split_far"] = {
                "status": "single_district", "district": only,
                "measured_shares": raw, "unzoned_excluded": unzoned or None,
                "zoned_fraction": round(zoned_fraction, 4),
                "zoned_lot_area_sf": (round(bl["lot_area"] * zoned_fraction, 1)
                                      if bl.get("lot_area") else None),
                "geometry_source": m["source"],
                "note": ("PLUTO's FAR stands, but it applies only to the ZONED "
                         "portion — the lot area must be reduced accordingly"
                         if unzoned else "PLUTO's single FAR stands for this lot")}
            not_split += 1
            continue

        out = {"status": "resolved", "shares": {d: round(s, 4) for d, s in kept.items()},
               "measured_shares": raw, "coverage": m["coverage"],
               "polygon_area_sf": m["polygon_area_sf"],
               "polygon_vs_pluto": m["polygon_vs_pluto"],
               "slivers_excluded": {d: round(s, 4) for d, s in dropped.items()} or None,
               "unzoned_excluded": {d: round(s, 4) for d, s in unzoned.items()} or None,
               "zoned_fraction": round(zoned_fraction, 4),
               "zoned_lot_area_sf": (round(bl["lot_area"] * zoned_fraction, 1)
                                     if bl.get("lot_area") else None),
               "geometry_source": m["source"],
               "rule": "ZR 77-22 (adjusted maximum FAR = Σ FAR_i × share_i)",
               "far_source": {d: src.get(d) for d in kept},
               "far": {}, "far_note": {}, "pluto_far": pluto, "as_of_right_sf": {}}
        # commercial overlays, MEASURED on the same footprint (nyco ∩ district ∩ lot)
        ovd = {d: v["covered_fraction_of_district"]
               for d, v in (m.get("overlay_by_district") or {}).items()}
        # the lot's special purpose district, from DCP's authoritative assignment
        dcp_z = bl.get("dcp_zoning") or {}
        special = next((dcp_z.get(f"special_district_{i}") for i in (1, 2, 3)
                        if dcp_z.get(f"special_district_{i}")), None)
        out["special_district"] = special
        if special:
            import special_districts as sd
            out["special_district_name"] = (sd.index().get(special) or ["?", "?"])[0]
            out["special_district_status"] = sd.status(special)
        out["overlay_shares"] = m.get("overlay_shares") or {}
        out["overlay_by_district"] = m.get("overlay_by_district") or {}

        bad = False
        for use, (fnarrow, fwide, _) in USES.items():
            vn, note_n = adjusted(kept, ZR, zref, use, fnarrow, ovd, special)
            vw, note_w = adjusted(kept, ZR, zref, use, fwide, ovd, special)
            out["far"][use] = vw
            out["far_note"][use] = note_w
            if fnarrow != fwide and vn != vw:
                out["far"][use + "_narrow"] = vn
                out["far_note"][use + "_narrow"] = note_n
                out["far_note"][use] = note_w + "  [WIDE-STREET figure; narrow " \
                                                f"street gives {vn} — frontage not established]"
            # against the ZONED lot area — unzoned land carries no floor area
            if vw is not None and out["zoned_lot_area_sf"]:
                out["as_of_right_sf"][use] = round(vw * out["zoned_lot_area_sf"], 1)
            if vw is None and use == "residfar":
                bad = True
        if bad:
            out["status"] = "unresolved"
            out["reason"] = out["far_note"]["residfar"]
            unresolved += 1
        else:
            resolved += 1
        bl["split_far"] = out

        tag = "RESOLVED  " if out["status"] == "resolved" else "UNRESOLVED"
        share_s = "  ".join(f"{d} {s*100:.1f}%" for d, s in kept.items())
        print(f"{b}  {tag} {share_s}")
        for use in USES:
            v, p = out["far"].get(use), pluto.get(use)
            if v is None:
                print(f"        {use:<9} —        pluto {p}   ({out['far_note'][use]})")
            else:
                delta = f"{(v/p-1)*100:+.1f}%" if p else "n/a"
                print(f"        {use:<9} {v:<8} pluto {p:<6} {delta}")

    print(f"\nresolved {resolved} | unresolved {unresolved} | not split in geometry {not_split}"
          f"  (of {len(bbls)})")
    if write:
        BASELINES.write_text(json.dumps(base, indent=1), encoding="utf-8")
        print(f"wrote split_far into {BASELINES.name}")
    else:
        print("dry run — pass --write to update baselines.json")


if __name__ == "__main__":
    main(write="--write" in sys.argv, refresh="--refresh" in sys.argv)
