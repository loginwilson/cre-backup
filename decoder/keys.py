"""Parcel keys, one place, with the guards that stop a silent wrong answer.

WHY THIS EXISTS
    This decoder now drives ACRIS, DOB BIS + NOW, BSA, DCP (fdkv-4t4z, nyzd,
    nyco), PLUTO, MapPLUTO, DOF's Digital Tax Map, the Zoning Resolution, LPC and
    HPD. Every one of them keys a parcel slightly differently:

        ACRIS legals        borough / block / lot as SEPARATE integer columns
        Socrata PLUTO       block zero-padded to 5 ('01446')
        DOB BIS / NOW       block NOT padded ('1446')
        MapPLUTO ArcGIS     BBL numeric        -> BBL IN (1014460001)
        DOF DTM ArcGIS      BBL string         -> BBL IN ('1014460001')
        DCP fdkv-4t4z       bbl string

    The failures these produce do not look like failures. A DOB query with a
    padded block returns ZERO rows and reads as "no filing". A tax-map query on
    BLOCK=1540 AND LOT=3 with no borough returns BROOKLYN's block 1540 lot 3 —
    a real parcel, wrong city, no error. Both have happened here.

    So the rule is the same one the audit follows: do not remember the trap,
    enforce it. Block+lot without a borough raises. Every query builder below
    emits the dialect its source actually wants.
"""
import re

BOROS = {"manhattan": 1, "bronx": 2, "brooklyn": 3, "queens": 4, "staten island": 5,
         "richmond": 5, "kings": 3, "new york": 1}
BORO_NAME = {1: "Manhattan", 2: "Bronx", 3: "Brooklyn", 4: "Queens", 5: "Staten Island"}
BBL_RE = re.compile(r"^[1-5]\d{9}$")


def boro(b):
    """Borough as 1-5, from a number or a name. Raises rather than defaulting —
    a defaulted borough is how a Brooklyn lot answers a Manhattan question."""
    if b is None or (isinstance(b, str) and not b.strip()):
        raise ValueError("borough is required: block+lot is NOT a parcel key")
    if isinstance(b, str) and not b.strip().isdigit():
        key = b.strip().lower()
        if key not in BOROS:
            raise ValueError(f"unknown borough {b!r}")
        return BOROS[key]
    n = int(b)
    if n not in BORO_NAME:
        raise ValueError(f"borough out of range: {b!r}")
    return n


def bbl(borough, block, lot):
    """(borough, block, lot) -> canonical 10-digit BBL string."""
    n = boro(borough)
    block, lot = int(str(block).strip()), int(str(lot).strip())
    if not 0 < block <= 99999:
        raise ValueError(f"block out of range: {block}")
    if not 0 <= lot <= 9999:
        raise ValueError(f"lot out of range: {lot}")
    return f"{n}{block:05d}{lot:04d}"


def parts(the_bbl):
    """Canonical BBL -> (borough, block, lot) as integers."""
    s = str(the_bbl).strip()
    if not BBL_RE.match(s):
        raise ValueError(f"not a canonical 10-digit BBL: {the_bbl!r}")
    return int(s[0]), int(s[1:6]), int(s[6:])


# ---------------------------------------------------------------- per-source
def socrata_block(the_bbl):
    """PLUTO and ACRIS legals on Socrata pad the block to 5 characters."""
    return f"{parts(the_bbl)[1]:05d}"


def dob_block(the_bbl):
    """DOB does NOT pad. A padded block returns zero rows, which reads exactly
    like 'this parcel has no filings' — the trap that nearly went in the record
    once already. Always run a control query against a block known to have data
    before reporting an absence."""
    return str(parts(the_bbl)[1])


def arcgis_where(bbls, field="BBL", quoted=True):
    """`BBL IN (...)` for an ArcGIS layer. DOF's Digital Tax Map stores BBL as a
    STRING and MapPLUTO as a NUMBER; passing the wrong one returns nothing."""
    vals = [str(int(b)) for b in bbls]
    if quoted:
        return f"{field} IN (" + ",".join(f"'{v}'" for v in vals) + ")"
    return f"{field} IN (" + ",".join(vals) + ")"


def dtm_where(bbls):
    """DOF Digital Tax Map — BBL is a string field."""
    return arcgis_where(bbls, quoted=True)


def mappluto_where(bbls):
    """MapPLUTO — BBL is numeric."""
    return arcgis_where(bbls, quoted=False)


def lot_kind(the_bbl):
    """What KIND of lot this is. The ranges OVERLAP if tested naively.

    ⚠ `lot >= 1001` was being used to mean "condominium unit lot", but DOF's
    numbering puts several kinds above 1000:

        1-999       ground lot (a normal tax lot)
        1001-6999   CONDOMINIUM UNIT lot
        7501-7599   condominium BILLING lot (the one PLUTO carries)
        8000-8999   REUC (real estate of utility corporations)
        9000-9999   AIR lot / subterranean lot

    So an AIR lot satisfied `is_unit_lot` and would have been collapsed to a
    condominium's billing lot — a wrong parent, silently. Ranges from DOF's own
    tax-map documentation and corroborated by this project's data: 1015409003 is
    an air lot, 1014461101-1181 are condo units, 1014467502 is a billing lot.
    """
    lot = parts(the_bbl)[2]
    if lot >= 9000:
        return "air_or_subterranean"
    if 8000 <= lot < 9000:
        return "reuc"
    if 7501 <= lot < 7600:
        return "condo_billing"
    if lot >= 1001:
        return "condo_unit"
    return "ground"


def is_unit_lot(the_bbl):
    """Condominium UNIT lot only — not air, not REUC, not the billing lot."""
    return lot_kind(the_bbl) == "condo_unit"


def is_air_lot(the_bbl):
    return lot_kind(the_bbl) == "air_or_subterranean"


# ── Document ids ──────────────────────────────────────────────────────────────
# ⚠ A PARCEL KEY IS NOT THE ONLY KEY THAT CAN BE JUNK. Found 2026-08-19 by a
# census of `document` in the specification: ONE row keyed
#     '--51e970bd-7649-473e-956a-4c1ec01aff30--'
# which is a MIME multipart CLOSING BOUNDARY, not a document id. Something read a
# request/response body as data and inserted the frame. It was inert (no parcel
# links, no party rows, image_state NULL so acquisition could never queue it) —
# which is exactly why nothing caught it for as long as it sat there. An id that
# no source can produce is not a bad ROW, it is a bad STATE, so it gets made
# unrepresentable here rather than detected later.
#
# The four shapes the corpus actually contains, counted on the drive 2026-08-19:
#     20…   11,574,935   ACRIS CRFN era      2026012000388003   (16 digits)
#     FT_    8,315,404   ACRIS microfilm     FT_1320008495632
#     BK_    1,721,172   ACRIS microfilm     BK_7430068201487
#     RC_    2,426,404   Richmond Clerk      RC_2825123
DOC_ID_RE = re.compile(r"^(?:20\d{14}|(?:FT|BK)_\d{8,20}|RC_\d{1,12})$")


def is_document_id(v):
    """Does this string have the shape of a document id from a known custodian?"""
    return bool(v is not None and DOC_ID_RE.match(str(v).strip()))


def document_id(v):
    """Validate a document id at the boundary, or RAISE.

    ⚠ Call this in every LANDER, before the insert — not in a periodic audit. The
    malformed row above proves the difference: an audit finds junk after it is in
    the specification and someone has to decide whether deleting it loses
    something; a guard means it was never a row. Same rule as `boro()` refusing to
    default — a key that cannot be trusted must stop the write, not colour it.
    """
    s = str(v).strip() if v is not None else ""
    if not DOC_ID_RE.match(s):
        raise ValueError(
            f"not a document id from any known custodian: {s[:80]!r} "
            f"(expected 20+14 digits, FT_/BK_+digits, or RC_+digits)")
    return s


if __name__ == "__main__":
    ok = fail = 0
    def check(desc, fn, want=None, raises=False):
        global ok, fail
        try:
            got = fn()
            good = (got == want) and not raises
        except Exception as e:
            got, good = f"raised {type(e).__name__}", raises
        (globals().__setitem__("ok", ok + 1) if good
         else globals().__setitem__("fail", fail + 1))
        print(f"   [{'ok ' if good else 'FAIL'}] {desc:<52} -> {got}")
    check("bbl(1, 1446, 1)", lambda: bbl(1, 1446, 1), "1014460001")
    check("bbl('Manhattan', 1446, 1)", lambda: bbl("Manhattan", 1446, 1), "1014460001")
    check("bbl(None, 1540, 3) must RAISE", lambda: bbl(None, 1540, 3), raises=True)
    check("bbl('', 1540, 3) must RAISE", lambda: bbl("", 1540, 3), raises=True)
    check("parts('1015400003')", lambda: parts("1015400003"), (1, 1540, 3))
    check("socrata_block('1014460001')", lambda: socrata_block("1014460001"), "01446")
    check("dob_block('1014460001')", lambda: dob_block("1014460001"), "1446")
    check("dtm_where(['1015409003'])", lambda: dtm_where(["1015409003"]),
          "BBL IN ('1015409003')")
    check("mappluto_where(['1015409003'])", lambda: mappluto_where(["1015409003"]),
          "BBL IN (1015409003)")
    check("is_air_lot('1015409003')", lambda: is_air_lot("1015409003"), True)
    check("is_unit_lot('1014461101')", lambda: is_unit_lot("1014461101"), True)
    check("parts('101446001') must RAISE", lambda: parts("101446001"), raises=True)
    # ── document ids: one live example of each shape, then the known-bad input
    check("document_id ACRIS crfn", lambda: document_id("2026012000388003"),
          "2026012000388003")
    check("document_id microfilm FT_", lambda: document_id("FT_1320008495632"),
          "FT_1320008495632")
    check("document_id microfilm BK_", lambda: document_id("BK_7430068201487"),
          "BK_7430068201487")
    check("document_id richmond", lambda: document_id("RC_2825123"), "RC_2825123")
    # ⚠ THE ROW THAT PROMPTED THE GUARD — a MIME closing boundary found in the
    # specification 2026-08-19. A guard is not believed until it is proven on the
    # exact input that got through.
    check("document_id MIME boundary must RAISE",
          lambda: document_id("--51e970bd-7649-473e-956a-4c1ec01aff30--"), raises=True)
    check("document_id '' must RAISE", lambda: document_id(""), raises=True)
    check("document_id None must RAISE", lambda: document_id(None), raises=True)
    check("document_id bare bbl must RAISE", lambda: document_id("1014460001"),
          raises=True)
    print(f"\n{ok} pass / {fail} fail")

# ── Dates ─────────────────────────────────────────────────────────────────────
# ⚠ A SEVENTH FORMAT TRAP, and it corrupts TIMELINES rather than joins.
# DOB BIS returns "01/03/2020" (MM/DD/YYYY); DOB NOW, DOF and ACRIS return ISO
# "2024-09-10". String-sorting a mixed list interleaves them wrongly — a 2020
# event sorts before a 2024 one because "0" < "2" — so a parcel history reads
# out of order while every individual row is correct.
import re as _re


def iso_date(v):
    """Any of the date spellings met in this project -> 'YYYY-MM-DD', or None.

    Handles: ISO, MM/DD/YYYY, epoch milliseconds (ArcGIS), and datetimes with a
    time part. Returns None rather than guessing — an unparseable date must sort
    as unknown, not as year zero.
    """
    if v is None or v == "":
        return None
    s = str(v).strip()
    if _re.fullmatch(r"\d{13}", s):                       # epoch ms (ArcGIS)
        from datetime import datetime, timezone
        return datetime.fromtimestamp(int(s) / 1000, timezone.utc).date().isoformat()
    m = _re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)         # ISO / ISO datetime
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = _re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)     # MM/DD/YYYY
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None
