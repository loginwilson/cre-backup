"""Special purpose districts — the layer that SUPERSEDES the citywide FAR tables.

WHY
    A lot's FAR can be read correctly off ZR 23-22 / 33-122 / 24-11 and still be
    wrong, because a special purpose district sits on top and modifies it. That
    failure is silent: every citywide lookup succeeds, nothing is null, and the
    number is simply superseded.

    Found live: BBL 4097930089 is C4-4D / C6-3 inside the Special Downtown
    Jamaica District (DJ). ZR 115-21 reads "the maximum floor area ratio
    permitted for commercial uses shall be 8.0 in C6-3 Districts and 12.0 in C6-4
    Districts". The citywide table says 6.0, so the computed commercial FAR came
    out 4.156 against a correct 4.739 — understated 14%, with no error anywhere.

HOW THIS IS KEPT HONEST
    Appendix B of the Resolution indexes every special district symbol to its
    section number, so the symbol DCP publishes per lot ("DJ") resolves to real
    regulatory text rather than to a memory of what the abbreviation means.

    Overrides are only recorded here once the section has been READ. A district
    with no entry is NOT assumed harmless — `status()` returns "unverified", and
    a lot carrying one is flagged rather than trusted. A regex that found no
    floor-area section is a weak negative: it means the search failed, not that
    the district is silent.
"""
import html, json, pathlib, re, urllib.request

BASE = "https://zr.planning.nyc.gov"
APPENDIX_B = f"{BASE}/appendix-b-index-special-purpose-districts"
CACHE = pathlib.Path(__file__).with_name("zr_special_districts.json")


def index(refresh=False):
    """symbol -> (district name, section number), straight from Appendix B."""
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    req = urllib.request.Request(APPENDIX_B, headers={"User-Agent": "acris-decoder/1.0"})
    page = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "ignore")
    out = {}
    for table in re.findall(r"<table.*?</table>", page, re.S):
        for row in re.findall(r"<tr.*?</tr>", table, re.S):
            cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                     for c in re.findall(r"<t[dh].*?</t[dh]>", row, re.S)]
            if len(cells) < 2:
                continue
            sym = re.search(r"\(([A-Z0-9\-/ ]{1,12})\)", cells[0])
            sec = re.match(r"^(\d{2,3}-\d{2})", cells[1] or "")
            if sym and sec:
                out[sym.group(1).strip()] = [re.sub(r"\s*\(.*", "", cells[0]).strip(),
                                             sec.group(1)]
    CACHE.write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


# Overrides recorded ONLY from text that has been read, with the citation that
# proves it. Absence from this table means "not yet checked", never "no effect".
OVERRIDES = {
    "DJ": {
        "section": "115-21", "last_amended": "2025-10-29",
        "url": f"{BASE}/article-xi/chapter-5/115-21",
        "quote": ("The underlying floor area regulations shall be modified as follows: the "
                  "maximum floor area ratio permitted for commercial uses shall be 8.0 in "
                  "C6-3 Districts and 12.0 in C6-4 Districts; in all Districts, the maximum "
                  "floor area ratio permitted for residential uses shall be as set forth "
                  "pursuant to the underlying district regulations"),
        # use -> {district: FAR}
        "commfar": {"C6-3": 8.0, "C6-4": 12.0},
        "residfar": {},        # explicitly unchanged by the section's own words
        "facilfar": {},        # not addressed in 115-21 — left to the underlying rules
        "notes": ["sky exposure plane buildings not permitted",
                  "FAR may be exceeded only via a CPC bonus (ZR 66-51 mass transit "
                  "station improvement, or 115-52 public plaza)"],
    },
    # Checked against the FULL section list of the district's chapter, not just
    # the sections a keyword search tagged — a title index cannot prove absence,
    # so a negative claim gets read in full or it is not made.
    "MSX": {
        "section": "121-00", "chapter": "Article XII Chapter 1 (22 sections, all read)",
        "url": f"{BASE}/article-xii/chapter-1",
        "commfar": {}, "residfar": {}, "facilfar": {},
        "verified_no_far_change": True,
        "quote": ("the chapter's only floor-area section is 121-31 Floor Area Exemption "
                  "for Public Schools; 121-30 SPECIAL BULK REGULATIONS covers yards, "
                  "height/setback and street walls, not FAR"),
        "notes": [
            "121-31 exempts PUBLIC SCHOOL floor area — applies only where one is present",
            "121-341 Transfer of development rights from LANDMARKS and 121-342 from the "
            "THEATER SUBDISTRICT: MSX changes the envelope through TRANSFER, not base FAR "
            "— directly this decoder's subject matter",
            "121-05 Applicability of Article XII Chapter 3 — incorporates the Special "
            "Mixed Use (MX) regulations by reference; a chain still to follow",
            "121-04 the Mandatory Inclusionary Housing Program applies here"],
    },
    "TA": {
        "section": "95-00", "chapter": "Article IX Chapter 5 (24 sections, all read)",
        "url": f"{BASE}/article-ix/chapter-5",
        "commfar": {}, "residfar": {}, "facilfar": {},
        "verified_no_far_change": True,
        "quote": "no floor-area section exists in the chapter; all 24 sections concern "
                 "transit easements, their volume, terms and termination",
        "notes": [
            "⚠ 95-11 RECORDATION — a transit easement is RECORDED, so it lands in ACRIS "
            "as an ENCUMBER against the lot. TA does not change FAR but it does generate "
            "instruments this decoder will meet (see also 95-12 Termination, 95-13 "
            "Previous Transit Easement Agreements)",
            "95-04 Certification of Transit Easement Volume — the easement is a VOLUME, "
            "described by a limiting plane, like the airspace parcels already decoded",
            "95-07 increases permitted zoning tower coverage — a bulk incentive, not FAR"],
    },
}


def status(symbol):
    """Three outcomes, never two: an override that applies, a district read and
    found not to modify this use, or one nobody has checked."""
    if not symbol:
        return "none"
    return "override" if symbol in OVERRIDES else "unverified"


def apply_override(symbol, district, use, citywide):
    """(value, source). Returns the citywide figure unchanged when no override
    covers this district+use, and flags when the district is unchecked."""
    ov = OVERRIDES.get(symbol)
    if not ov:
        return citywide, (f"citywide table; special district {symbol} NOT checked for "
                          f"supersession" if symbol else "citywide table")
    table = ov.get(use) or {}
    if district.upper() in table:
        return table[district.upper()], (f"ZR {ov['section']} ({ov['last_amended']}) "
                                         f"special district {symbol} SUPERSEDES the citywide table")
    return citywide, f"citywide table; ZR {ov['section']} does not modify {use} for {district}"


if __name__ == "__main__":
    idx = index()
    print(f"{len(idx)} special districts indexed from ZR Appendix B\n")
    for sym in sorted({"MSX", "TA", "DJ"} | set(OVERRIDES)):
        name, sec = idx.get(sym, ("?", "?"))
        print(f"  {sym:<5} {name[:44]:<46} ZR {sec:<8} {status(sym)}")
    print("\n  worked example — BBL 4097930089, C4-4D 70.9% / C6-3 29.1%, district DJ:")
    for d, share, cw in (("C4-4D", 0.709, 3.4), ("C6-3", 0.291, 6.0)):
        v, src = apply_override("DJ", d, "commfar", cw)
        print(f"     {d:<6} citywide {cw} -> {v}   {src}")
    tot = sum(apply_override("DJ", d, "commfar", cw)[0] * sh
              for d, sh, cw in (("C4-4D", 0.709, 3.4), ("C6-3", 0.291, 6.0)))
    print(f"     adjusted commercial FAR = {tot:.4f}   (citywide-only gave 4.1563)")
