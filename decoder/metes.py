"""Metes and bounds — the legally operative parcel description.

A deed conveys the land DESCRIBED, not "tax lot 34". Tax lots are DOF's
administrative overlay for assessment; the DTM is the City's official geometry
for that overlay; PLUTO is quarterly packaging on top. The survey courses in the
recorded instrument are the source, and they are available for ANY era — which
is what closes the pre-2002 geometry gap that no parcel file can reach.

The survey is authoritative but not infallible. This pilot alone found an 18'11"
gap between abutting parcels, a "28th feet" typo, and two variant course sets for
one lot where neither closed. So every description is walked as a traverse and
reported with its CLOSURE ERROR: area is only trustworthy when the courses come
back to the point of beginning.

Handles the NYC vocabulary:
  distances   "100 feet" · "16 ft 3 in" · "8 ft 9-1/2 in" · 27'2" · 104.96
  directions  cardinal words (easterly/northerly/...) for rectilinear blocks, and
              full bearings N 76°19'05" E for surveyed traverses
Curves ("R=2,335.00 arc 128.46") are detected and reported as unhandled rather
than silently approximated by a chord.
"""
import math
import re

FEET = r"(\d[\d,]*(?:\.\d+)?)"
CARDINAL = {"north": 0.0, "northerly": 0.0, "south": 180.0, "southerly": 180.0,
            "east": 90.0, "easterly": 90.0, "west": 270.0, "westerly": 270.0}


ONES = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
        "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
        "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fourty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
HALVES = {"half": 0.5, "quarter": 0.25, "three-quarters": 0.75}
WORD_NUM_RE = re.compile(
    r"\b((?:(?:one|two|three|four|five|six|seven|eight|nine)\s+hundred"
    r"|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fourty|fifty|sixty|seventy|eighty|ninety)"
    r"(?:[\s-]+(?:and\s+)?(?:one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|"
    r"nineteen|twenty|thirty|forty|fourty|fifty|sixty|seventy|eighty|ninety))*)",
    re.I)


def words_to_number(phrase):
    """'one hundred and seventy-two' -> 172. None if it is not a number phrase.

    Older descriptions — and plenty of recent ones — spell distances out:
    "RUNNING THENCE northerly parallel with Graham Avenue, ONE HUNDRED FEET;
     THENCE easterly parallel with Devoe Street, TWENTY-TWO FEET". A digits-only
    parser returns nothing for these, which (correctly) drops the course rather
    than guessing — but drops the whole traverse with it.
    """
    total = 0
    seen = False
    for tok in re.split(r"[\s-]+", phrase.strip().lower()):
        if tok in ("and", ""):
            continue
        if tok == "hundred":
            total = (total or 1) * 100
            seen = True
        elif tok in TENS:
            total += TENS[tok]
            seen = True
        elif tok in ONES:
            total += ONES[tok]
            seen = True
        else:
            return None
    return total if seen else None


# Recorded originals mix "1/2" with the single-character "½". The typed form
# parsed and the unicode form was DROPPED SILENTLY — "117 feet ¼ inch" returned
# 117.0, losing the quarter inch with no complaint, which is the worst kind of
# miss because the number still looks reasonable. Normalise before anything runs.
VULGAR = {"¼": "1/4", "½": "1/2", "¾": "3/4", "⅓": "1/3", "⅔": "2/3",
          "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8"}


def _unvulgar(t):
    for ch, frac in VULGAR.items():
        t = t.replace(ch, " " + frac)
    return t


# A degrees-minutes-seconds ANGLE. Anchored on the degrees token, so it can only
# ever match something already declared to be an angle — never a bare distance
# like 27'2". Everything after the degrees is optional because descriptions
# write all of "90°", "89°40'", "89 degrees 40' 14\"" and "76°19'05\"".
_DMS = re.compile(
    # ⚠ LONGEST ALTERNATIVE FIRST. Python alternation is leftmost-first, not
    # longest-match: with `deg\.?` ahead of `degrees?`, "89 degrees 40' 40\""
    # matched only "89 deg" and left "rees 40' 40\"" behind for the feet pattern
    # to eat. The fix for the bug re-created the bug until this order was right.
    r"\d{1,3}(?:\.\d+)?\s*(?:°|º|degrees?|deg\.?)\s*"
    r"(?:\d{1,2}\s*(?:'|′|minutes?|min\.?)\s*"
    r"(?:\d{1,2}(?:\.\d+)?\s*(?:\"|″|seconds?|sec\.?)\s*)?)?",
    re.I)


def parse_distance(text):
    """'16 ft 3 in' / '8 feet 9-1/2 inches' / '76 feet, 8 inches' / "27'2\"" -> feet.

    Two things this must survive, both found in recorded originals:

    * an ORDINAL SUFFIX typed onto the number — "28th feet" for "28 feet". The
      figure is still legible to a human and must stay legible here.
    * a COMMA between the feet and inches — "76 feet, 8 inches". Without it the
      inches are dropped and 76'8" silently becomes 76'.

    And one thing it must NOT do: fall back to "the first number in the clause".
    That fallback read "westerly parallel with 75th Street, 28th feet" as 75
    feet — it took the STREET NUMBER. A course that cannot be parsed is visible
    the moment you look at the traverse; a course parsed to the wrong distance
    is invisible and poisons the area. Return None and let it be unparseable.
    """
    t = _unvulgar(text.lower().replace("–", "-"))
    # ⚠ BUG #10 (found 2026-08-13, doc 2017053000419005 Exhibit B / Schedule A).
    # AN ANGLE'S MINUTES AND SECONDS WEAR THE SAME MARKS AS FEET AND INCHES.
    #   "...forms an interior angle of 89 degrees 40' 40\" with the last
    #    mentioned course 154.36 feet"
    # The feet pattern below matched 40' 40" FIRST — 40 feet 40 inches = 43.333 —
    # and the real 154.36 never got looked at. Same trap on a surveyed bearing:
    #   "N 76°19'05\" E 100.00 feet"  ->  19'05" = 19.417 ft, not 100.00.
    # Both are silently wrong distances, which is the failure mode this parser
    # exists to refuse. So the DMS group is REMOVED before any distance is read;
    # bearings are parsed separately by parse_bearing and lose nothing.
    # (The spelled-out form — "89 degrees 31 minutes 20 seconds ... 50 feet" —
    # never tripped it, which is why it survived nine earlier bug hunts.)
    t = _DMS.sub(" ", t)
    # Feet (tolerating an ordinal suffix), then optional inches after a space or a
    # comma. The inches may be a whole number ("8 inches"), a whole plus a
    # fraction ("4-3/8 inches"), or a BARE FRACTION ("1/2 inch") — the last is
    # common in NYC descriptions and was being dropped, turning a lot recorded at
    # 25'0-1/2" x 100' = 2,504.17 sf into a tidy, wrong 2,500.
    # ⚠ THE SEPARATOR MUST ALLOW A SPACE, NOT ONLY A HYPHEN. Found 2026-08-06 in
    # the Exhibit B description of 2010102601040006: "about 82 feet 8 3/4 inches"
    # parsed as 82.0, dropping 8.75in = 0.729ft. The hyphenated form ("4-3/8")
    # and the bare fraction ("1/2") each had their own earlier fix; the
    # SPACE-SEPARATED mixed number fell in the gap between them — a bug created
    # by two fixes that each looked complete.
    #
    # It was caught only because the traverse's closure error (0.667 ft) was of
    # the same order as the dropped inches. CLOSURE IS A PARSER TEST: a
    # description that should close and does not is usually a mis-read course,
    # not a bad survey.
    m = re.search(FEET + r"(?:st|nd|rd|th)?\s*(?:feet|foot|ft\.?|')"
                  r"(?:[\s,]*(?:(\d+)(?:(?:\s*-\s*|\s+)(\d+)/(\d+))?|(\d+)/(\d+))"
                  r"\s*(?:inches|inch|in\.?|\"))?", t)
    if m:
        ft = float(m.group(1).replace(",", ""))
        whole, num, den, bare_n, bare_d = m.groups()[1:6]
        inches = float(whole) if whole else 0.0
        if num and den:
            inches += float(num) / float(den)
        elif bare_n and bare_d:
            inches += float(bare_n) / float(bare_d)
        ft += inches / 12.0
        return ft
    m = re.search(r"(\d+)\s*(?:inches|inch|in\.?|\")", t)
    if m:
        return float(m.group(1)) / 12.0

    # SPELLED-OUT distances, e.g. "twenty-two feet", "one hundred feet",
    # "seventy-six feet eight inches". Tried only after the numeric forms so a
    # digit always wins, and anchored to the unit word so a stray "one" in prose
    # ("part of the way through a party wall") can never become a distance.
    wm = re.search(WORD_NUM_RE.pattern + r"\s*(?:feet|foot|ft\.?)", t, re.I)
    if wm:
        ft = words_to_number(wm.group(1))
        if ft is not None:
            rest = t[wm.end():]
            im = re.match(r"[\s,]*(?:and\s+)?" + WORD_NUM_RE.pattern +
                          r"\s*(?:inches|inch|in\.?)", rest, re.I)
            if im:
                inches = words_to_number(im.group(1))
                if inches is not None:
                    ft += inches / 12.0
            else:
                dm = re.match(r"[\s,]*(?:and\s+)?(\d+)\s*(?:inches|inch|in\.?)", rest, re.I)
                if dm:
                    ft += float(dm.group(1)) / 12.0
            return float(ft)
    return None


# A quadrant bearing, with the quadrant letters either abbreviated ("N ... E")
# or SPELLED OUT ("North 00°37'08\" West"). The spelled-out form is what a
# surveyed description actually uses, and matching only the abbreviation sent
# every such course through the cardinal fallback — which returned a compass
# direction instead of the surveyed angle, silently.
BEARING_RE = re.compile(
    r"\b(N(?:orth)?|S(?:outh)?)\s*(\d{1,3})\s*(?:°|deg\.?|d\b)\s*"
    r"(\d{1,2})?\s*(?:'|′|min\.?|m\b)?\s*"
    r"(\d{1,2}(?:\.\d+)?)?\s*(?:\"|″|sec\.?|s\b)?\s*"
    r"(E(?:ast)?|W(?:est)?)\b", re.I)


def parse_bearing(text):
    """'N 76°19'05" E' or 'North 00°37'08" West' -> azimuth degrees;
    else a cardinal word; else None."""
    m = BEARING_RE.search(text)
    if m:
        ns, deg, mi, se, ew = m.groups()
        ang = float(deg) + float(mi or 0) / 60 + float(se or 0) / 3600
        north, east = ns.upper().startswith("N"), ew.upper().startswith("E")
        if north:
            return ang if east else (360 - ang) % 360
        return 180 - ang if east else 180 + ang
    # NYC street names contain compass words ("East 71st Street", "West Street",
    # "North Conduit Avenue"), so a bare-cardinal match can fire on the street
    # rather than the course and flip the bearing 180 degrees. The -ly adverbs
    # are unambiguous about being directions, so try those first.
    #
    # But WHICH adverb: a course routinely names a second direction as a
    # REFERENCE — "westerly parallel with Leonard Street 100 feet to the
    # Southerly side of Ten Eyck Street" travels west and merely mentions the
    # south side of a street. Scanning a fixed list (northerly, southerly, ...)
    # returns whichever comes first in THE LIST, so that course resolved as
    # south: a 90-degree error, silent, on any description that cites a street
    # side — which is most of them.
    #
    # The direction of travel is the FIRST direction word in the CLAUSE. Take the
    # leftmost match by position, not by list order. (This bug was introduced by
    # the fix above it — worth remembering that a guard can create the thing it
    # was guarding against.)
    hits = [(m.start(), CARDINAL[w])
            for w in ("northerly", "southerly", "easterly", "westerly")
            for m in re.finditer(rf"\b{w}\b", text, re.I)]
    if hits:
        return min(hits)[1]
    hits = [(m.start(), CARDINAL[w])
            for w in ("north", "south", "east", "west")
            for m in re.finditer(rf"\b{w}\b(?!\s+(?:\d|[A-Z][a-z]*\s*(?:Street|St\.?|"
                                rf"Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?)))",
                                text, re.I)]
    return min(hits)[1] if hits else None


def courses(description):
    """Split a description into course clauses and parse each."""
    # A description opens with "BEGINNING at ..." and closes with "... to the
    # point of BEGINNING", so splitting on every occurrence and taking the last
    # piece yields the empty tail. Split once, on the first occurrence.
    body = re.split(r"\bbeginning\b|\bbegins?\b", description, maxsplit=1, flags=re.I)[-1]
    # The clause between BEGINNING and the first "thence" is a TIE LINE locating
    # the point of beginning from a street corner ("distant 54 feet 5 inches
    # southerly from ..."). It is not a boundary course; counting it throws the
    # closure error by exactly the tie distance.
    if re.search(r"\bthence\b", body, re.I):
        body = re.split(r"\bthence\b", body, maxsplit=1, flags=re.I)[1]
        body = "thence " + body
    out = []
    for clause in re.split(r";|\bthence\b", body, flags=re.I):
        clause = clause.strip(" ,.")
        if not clause:
            continue
        if re.search(r"\bcurve|\barc\b|radius|R\s*=", clause, re.I):
            out.append({"raw": clause, "kind": "curve", "azimuth": None, "distance": None})
            continue
        # ⚠ THE BEARING MUST BE REMOVED BEFORE THE DISTANCE IS READ.
        # In a bearing, 37'08" means 37 MINUTES 8 SECONDS. In a distance, the
        # identical string means 37 FEET 8 INCHES. Reading the clause
        # "North 00°37'08\" West, a distance of 50.69 Feet" for a distance first
        # returns 37.67 ft — the bearing's own minutes and seconds — and ignores
        # the 50.69 the document actually states. Same notation, opposite
        # meaning, and nothing about the result looks wrong.
        # A DEFLECTION ANGLE is a third bearing form: the course is stated as an
        # angle against the PREVIOUS line or a named street ("on a line which
        # forms an angle of 89 degrees 45 minutes 50 seconds ... with the
        # southerly side of Pine Street"), not against north. The cardinal
        # fallback still yields the right general direction, but it throws away
        # the minutes and seconds — here 89°45'50" is silently rounded to 90°.
        # Flag it so the traverse is not read as precise when it is not.
        deflection = bool(re.search(r"forms?\s+an\s+angle\s+of|deflect", clause, re.I))
        az = parse_bearing(clause)
        bm = BEARING_RE.search(clause)
        for_distance = (clause[:bm.start()] + " " + clause[bm.end():]) if bm else clause
        dist = parse_distance(for_distance)
        if az is not None and dist:
            out.append({"raw": clause, "kind": "line", "azimuth": az, "distance": dist,
                        "azimuth_basis": "deflection_angle_approximated" if deflection
                                         else "stated"})
    return out


def traverse(description):
    """Walk the courses. Returns area (shoelace), perimeter, closure error and
    the fraction of the perimeter that closure error represents."""
    cs = courses(description)
    lines = [c for c in cs if c["kind"] == "line"]
    if len(lines) < 3:
        return {"ok": False, "reason": f"only {len(lines)} parseable courses",
                "courses": cs}
    x = y = 0.0
    pts = [(0.0, 0.0)]
    for c in lines:
        rad = math.radians(c["azimuth"])
        x += c["distance"] * math.sin(rad)
        y += c["distance"] * math.cos(rad)
        pts.append((x, y))
    area = abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
                   for i in range(len(pts) - 1))) / 2.0
    perim = sum(c["distance"] for c in lines)
    closure = math.hypot(x, y)
    return {"ok": True, "n_courses": len(lines),
            "has_curve": any(c["kind"] == "curve" for c in cs),
            "area_sf": round(area, 1), "perimeter_ft": round(perim, 2),
            "closure_error_ft": round(closure, 3),
            "closure_ratio": round(closure / perim, 6) if perim else None,
            "courses": cs}


def verdict(t, tol_ratio=0.005):
    """A description is usable when it closes. 1:200 (0.5%) is generous for a
    transcription; surveys close far tighter."""
    if not t.get("ok"):
        return "unparseable"
    if t["has_curve"]:
        return "has_curve_unhandled"
    if t["closure_ratio"] is None:
        return "unknown"
    return "closes" if t["closure_ratio"] <= tol_ratio else "does_not_close"


if __name__ == "__main__":
    import json, pathlib, sys
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    tests = []
    if src:
        for f in src.glob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            for ld in d.get("legal_descriptions", []) or []:
                if ld.get("dimensions"):
                    tests.append((d["doc_id"], ld.get("lot") or ld.get("exhibit"),
                                  ld.get("computed_area_sf"), ld["dimensions"]))
    print(f"{'document':<20}{'lot':<28}{'stated':>10}{'traverse':>10}{'closure':>9}  verdict")
    ok = 0
    for doc, lot, stated, dim in tests:
        t = traverse(dim)
        v = verdict(t)
        a = t.get("area_sf")
        match = ""
        if a and stated:
            match = "  MATCH" if abs(a - stated) <= max(2, 0.02 * stated) else "  differs"
            ok += 1 if "MATCH" in match else 0
        print(f"{doc:<20}{str(lot)[:27]:<28}{str(stated or '-'):>10}{str(a or '-'):>10}"
              f"{str(t.get('closure_error_ft','-')):>9}  {v}{match}")
    print(f"\ntraverses reproducing the stated area: {ok}/{len(tests)}")
