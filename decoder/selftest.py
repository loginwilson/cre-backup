"""Regression battery — run it, fix what falls, run it again.

Login's instruction: *"run until you fall and if you fall you start again."*
That is only possible if FALLING IS DETECTABLE, so every trap this project has
met becomes an assertion here. Nothing in it needs ACRIS images, so it runs while
the image endpoint is blocked.

Each assertion records the TRAP IT GUARDS, because a bare assertion tells a
future reader nothing about why it exists — and a test whose purpose is
forgotten is the first one deleted when it becomes inconvenient.
"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))

RESULTS = []


def check(group, name, cond, detail="", guards=""):
    RESULTS.append((group, name, bool(cond), detail, guards))
    return bool(cond)


def run():
    import keys, metes

    # ---- keys ------------------------------------------------------------
    g = "keys"
    for b in ("1014460001", "1015409003", "1014461101", "5000010001"):
        bo, bl, lo = keys.parts(b)
        check(g, f"round-trip {b}", keys.bbl(bo, bl, lo) == b)
    for fn, why in ((lambda: keys.bbl(None, 1, 1), "borough required"),
                    (lambda: keys.bbl(6, 1, 1), "borough range"),
                    (lambda: keys.bbl(1, 0, 1), "block range"),
                    (lambda: keys.bbl(1, 1, 10000), "lot range"),
                    (lambda: keys.parts("101446001"), "9-digit BBL rejected")):
        try:
            fn()
            check(g, why, False, "accepted an invalid value")
        except ValueError:
            check(g, why, True,
                  guards="block+lot with no borough returned a real parcel from "
                         "the WRONG BOROUGH")
    check(g, "air lot is NOT a condo unit", not keys.is_unit_lot("1015409003"),
          guards="lot>=1001 also matches air (9000+), REUC (8000+) and billing "
                 "(7501+) lots, so an air lot collapsed to a wrong parent")
    check(g, "billing lot is not a unit lot", not keys.is_unit_lot("1014467502"))
    check(g, "socrata pads / dob does not",
          keys.socrata_block("1014460001") == "01446"
          and keys.dob_block("1014460001") == "1446",
          guards="a padded block returns ZERO DOB rows and reads as 'no filing'")
    check(g, "dtm quotes / mappluto does not",
          "'" in keys.dtm_where(["1014460001"])
          and "'" not in keys.mappluto_where(["1014460001"]),
          guards="DOF stores BBL as a string, MapPLUTO as a number")

    # ---- dates -----------------------------------------------------------
    g = "dates"
    for v, want in (("01/03/2020", "2020-01-03"), ("1509033505000", "2017-10-26"),
                    ("2024-09-10T00:00:00.000", "2024-09-10"), ("garbage", None),
                    ("1/3/20", None), ("", None), (None, None)):
        got = keys.iso_date(v)
        check(g, f"iso_date({v!r})", got == want, f"got {got}",
              guards="BIS is MM/DD/YYYY, ArcGIS epoch-ms, the rest ISO — string "
                     "sorting a mixed list reorders a parcel history")

    # ---- distances -------------------------------------------------------
    g = "parse_distance"
    cases = [("100 feet", 100.0), ("76 feet, 8 inches", 76 + 8 / 12),
             ("28th feet", 28.0), ("25 feet 1/2 inch", 25 + .5 / 12),
             ("50 feet 4-3/8 inches", 50 + 4.375 / 12), ("16 ft 3 in", 16.25),
             ("117 feet ¼ inch", 117 + .25 / 12), ("8 feet ½ inch", 8 + .5 / 12),
             # SPACE-separated mixed number. The hyphenated and bare-fraction
             # forms each got their own fix; this fell in the GAP BETWEEN THEM
             # and dropped 8.75in from a real Exhibit B on 2026-08-06.
             ("82 feet 8 3/4 inches", 82 + 8.75 / 12),
             ("about 82 feet 8 3/4 inches", 82 + 8.75 / 12),
             ("twenty-two feet", 22.0), ("one hundred feet", 100.0),
             ("one hundred and seventy-two feet", 172.0),
             ("seventy-six feet eight inches", 76 + 8 / 12),
             ("along 75th Street", None),
             ("part of the way through a party wall", None),
             # ⚠ BUG #10, 2026-08-13 (doc 2017053000419005, Jamaica ZLDA).
             # AN ANGLE'S MINUTES AND SECONDS WEAR THE SAME MARKS AS FEET AND
             # INCHES, and they come FIRST in the clause. "89 degrees 40' 40\""
             # was read as 40 feet 40 inches = 43.333 and the real 154.36 was
             # never reached; the traverse missed closure by 111 ft. The same
             # trap on any surveyed bearing: N 76°19'05" E 100.00 feet -> 19.42.
             # Nine earlier bug hunts missed it because every description in the
             # store until now spelled the angle out ("31 minutes 20 seconds").
             ("northerly on a course which forms an interior angle of 89 "
              "degrees 40' 40\" with the last mentioned courses 154.36 feet", 154.36),
             ("thence N 76°19'05\" E 100.00 feet to a point", 100.0),
             ("forming an interior angle of 239°55'27\" with the previous "
              "course, a distance of 14.48 feet", 14.48),
             # ...while the spelled-out angle and a BARE feet-inches mark (no
             # degrees token anywhere) must be untouched by the guard.
             ("of 89 degrees 31 minutes 20 seconds with the last course 50 feet", 50.0),
             ("thence 27'2\" to a point", 27 + 2 / 12)]
    for s, want in cases:
        got = metes.parse_distance(s)
        ok = ((got is None and want is None)
              or (got is not None and want is not None and abs(got - want) < 1e-6))
        check(g, repr(s), ok, f"got {got} want {want}",
              guards="a fallback once read the STREET NUMBER as the distance")

    # ---- bearings --------------------------------------------------------
    g = "parse_bearing"
    for s, want in (("North 00°37'08\" West", 359.3811),
                    ("N 76°19'05\" E", 76.3181),
                    ("South 89°31'37\" West", 269.5269),
                    ("westerly parallel with Leonard Street", 270.0),
                    ("easterly along the Southerly side of Ten Eyck Street", 90.0)):
        got = metes.parse_bearing(s)
        check(g, repr(s[:46]), got is not None and abs(got - want) < 0.01,
              f"got {got} want {want}",
              guards="a course names a SECOND direction as a reference; travel "
                     "is the FIRST direction in the text")

    surveyed = ("BEGINNING; RUNNING THENCE North 00°37'08\" West, a distance of 50.69 "
                "Feet; THENCE North 89°31'32\" East, a distance of 16.00 Feet; THENCE "
                "South 00°28'20\" East, a distance of 50.69 Feet; THENCE South "
                "89°31'32\" West, a distance of 16.00 Feet to the point of BEGINNING.")
    t = metes.traverse(surveyed)
    first = next(c for c in t["courses"] if c["kind"] == "line")
    check("parse_bearing", "bearing minutes are not read as feet",
          abs(first["distance"] - 50.69) < 0.01, f"got {first['distance']}",
          guards="37'08\" is 37 MINUTES 8 SECONDS in a bearing and 37 FEET 8 "
                 "INCHES in a distance — identical text, opposite meaning")

    # ---- traverse --------------------------------------------------------
    g = "traverse"
    sq = ("BEGINNING; THENCE northerly 100 feet; THENCE easterly 50 feet; THENCE "
          "southerly 100 feet; THENCE westerly 50 feet to the point of BEGINNING.")
    t = metes.traverse(sq)
    check(g, "square closes", t["closure_error_ft"] < 1e-6, str(t["closure_error_ft"]))
    check(g, "square area 5000", abs(t["area_sf"] - 5000) < 0.1, str(t["area_sf"]))
    tie = ("BEGINNING at a point distant 72 feet westerly from the corner; THENCE "
           "northerly 100 feet; THENCE easterly 50 feet; THENCE southerly 100 feet; "
           "THENCE westerly 50 feet to the point of BEGINNING.")
    check(g, "tie line excluded from the courses",
          metes.traverse(tie)["n_courses"] == 4,
          f"got {metes.traverse(tie)['n_courses']}",
          guards="counting the tie line throws closure by exactly the tie distance")
    check(g, "unparseable stays unparseable",
          metes.verdict(metes.traverse("BEGINNING; THENCE northerly; THENCE easterly."))
          == "unparseable",
          guards="prefer an UNPARSEABLE course to a silently wrong one")

    # ---- refusal detection ----------------------------------------------
    # The safety path. A FALSE NEGATIVE here means continuing to request from a
    # server that has said no — the worst behaviour available to this project.
    g = "access"
    import fetch_pages
    from fetch_pages import AccessDenied

    # the notice as ACRIS actually serves it: Word HTML with the sentence SPLIT
    # ACROSS TAGS, which is why a raw-bytes search silently never matched
    notice = (b"<html><head><title>ACRIS Bandwidth Notice</title></head><body>"
              b"<p><span>Further access to</span> <span>ACRIS is</span> "
              b"<b>denied</b>. detection of <i>automated scripts/robots</i> or "
              b"having <span>exceeded the bandwidth limits</span> ... "
              b"<span>subscription data services</span></p></body></html>")
    try:
        fetch_pages._check_denied(notice, "text/html")
        check(g, "tag-split refusal is detected", False, "did NOT raise",
              guards="the phrase is broken across tags, so `b'...' in data` never "
                     "matched and the block detector could not fire AT ALL")
    except AccessDenied:
        check(g, "tag-split refusal is detected", True,
              guards="the phrase is broken across tags, so `b'...' in data` never "
                     "matched and the block detector could not fire AT ALL")

    check(g, "raw-bytes search would have MISSED it",
          b"Further access to ACRIS is denied" not in notice,
          guards="proves the old check was structurally incapable of firing, "
                 "not merely unlucky")

    for magic, label in ((b"II*\x00", "TIFF-LE"), (b"MM\x00*", "TIFF-BE"),
                         (b"%PDF-1.4", "PDF")):
        try:
            fetch_pages._check_denied(magic + b"\x00" * 2000, "image/tiff")
            check(g, f"real {label} is not a false positive", True,
                  guards="a refusal check that rejects real images stops all work")
        except AccessDenied:
            check(g, f"real {label} is not a false positive", False, "raised on an image")
    return RESULTS


if __name__ == "__main__":
    run()
    groups = {}
    for grp, name, ok, detail, guards in RESULTS:
        groups.setdefault(grp, []).append((name, ok, detail, guards))
    total = passed = 0
    for grp, rows in groups.items():
        n_ok = sum(1 for r in rows if r[1])
        total += len(rows)
        passed += n_ok
        print(f"  {grp:<18} {n_ok}/{len(rows)}")
        for name, ok, detail, guards in rows:
            if not ok:
                print(f"      FAIL {name}  {detail}")
                if guards:
                    print(f"           guards: {guards}")
    print(f"\n{passed}/{total} assertions pass")
    sys.exit(0 if passed == total else 1)
