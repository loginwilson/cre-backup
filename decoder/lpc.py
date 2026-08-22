"""LPC — the envelope constraint zoning cannot see, and a second owner source.

Why LPC belongs in an ENVELOPE decoder at all: **whether an enlargement is
visible, and therefore permissible, is decided at the Commission, not in the FAR
calculation.** A site can hold unused development rights the Commission will
never let anyone build. And because landmark rights are TRANSFERABLE (ZR 74-79
and the special-district TDR regimes), designation does not destroy an envelope —
it DETACHES it. That makes LPC a DEVR subtype, inside the envelope ledger.

⚠ **CALENDARED ≠ DESIGNATED.** A calendared building is not yet landmarked but is
already constrained in practice, and there is NO recorded instrument behind it —
so it is invisible to any ACRIS-only view.

⚠ KEY FORMATS — five datasets, FOUR conventions, and a fifth spelling of borough
appears here that no other agency uses. Measured 2026-08-05:

    gpmc-yuvp  buildings    borough **'BK'** (TWO-LETTER)   + a real `bbl` column
    ncre-qhxs  desig/cal    `boroughid`                     + a real `bbl` column
    dpm2-m9mq  permits      borough 'Brooklyn' (title)      no bbl
    wycc-5aqt  violations   **boro** 'BROOKLYN' (upper)     no bbl
    ck4n-5h6x  complaints   borough 'Brooklyn' (title)      no bbl

Prefer the `bbl` column wherever it exists — it is unambiguous and skips the
whole borough-spelling problem. That is now the first rule of adding a source.
"""
import sys, pathlib
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk
import keys

BUILDINGS = "gpmc-yuvp"    # every building covered by a designation, WITH BBL
DESIG_CAL = "ncre-qhxs"    # designated AND calendared, WITH BBL
PERMITS = "dpm2-m9mq"      # applications: applicant AND owner of record
VIOLATIONS = "wycc-5aqt"
COMPLAINTS = "ck4n-5h6x"

BORO_NAME = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn",
             "4": "Queens", "5": "Staten Island"}
BORO_ABBR = {"1": "MN", "2": "BX", "3": "BK", "4": "QN", "5": "SI"}

SPEC = {
    BUILDINGS:  {"bbl_col": "bbl", "col": "borough", "case": "abbr"},
    DESIG_CAL:  {"bbl_col": "bbl", "col": "boroughid", "case": "num"},
    PERMITS:    {"bbl_col": None,  "col": "borough", "case": "title"},
    VIOLATIONS: {"bbl_col": None,  "col": "boro", "case": "upper"},
    COMPLAINTS: {"bbl_col": None,  "col": "borough", "case": "title"},
}


def boro_value(bbl, dataset):
    b = str(keys.parts(bbl)[0])
    case = SPEC[dataset]["case"]
    return {"upper": BORO_NAME[b].upper(), "title": BORO_NAME[b],
            "abbr": BORO_ABBR[b], "num": b}[case]


def control_query_ok(dataset):
    """Self-calibrating, and branching on what the dataset ACTUALLY has —
    bbl column, or borough+block, in that order of preference."""
    sample = bulk.socrata(dataset, limit=1)
    if not sample:
        return False, f"{dataset}: returned nothing at all"
    row, sp = sample[0], SPEC[dataset]
    if sp["bbl_col"] and row.get(sp["bbl_col"]):
        val = row[sp["bbl_col"]]
        found = bulk.socrata(dataset, where=f"{sp['bbl_col']}='{val}'", limit=5)
        return bool(found), f"{dataset}: {sp['bbl_col']}={val!r} -> {len(found)} rows (BBL-keyed)"
    boro, blk = row.get(sp["col"]), row.get("block")
    if not (boro and blk):
        return False, f"{dataset}: sample lacks {sp['col']}/block — has {sorted(row)[:6]}"
    found = bulk.socrata(dataset, where=f"{sp['col']}='{boro}' and block='{blk}'", limit=5)
    return bool(found), f"{dataset}: {sp['col']}={boro!r} block={blk!r} -> {len(found)} rows"


def rows_for(bbls, dataset, strict_lot=True):
    """Rows for a set of BBLs.

    ⚠ `strict_lot` is not optional in spirit. The first version of this filter
    ended `... in wanted or True`, which makes the whole condition a no-op — so
    block-level rows were returned as if they were lot-level. It showed up as a
    contradiction (0 designated buildings, 35 LPC permits) rather than as a
    silent overcount, but only because LPC permits cannot exist without a
    designation. On a dataset with no such invariant it would simply have been
    wrong.
    """
    sp = SPEC[dataset]
    if sp["bbl_col"]:
        out = []
        vals = [str(int(b)) for b in bbls]
        for i in range(0, len(vals), bulk.IN_CLAUSE_MAX):
            joined = ",".join(f"'{x}'" for x in vals[i:i + bulk.IN_CLAUSE_MAX])
            out += bulk.socrata(dataset, where=f"{sp['bbl_col']} in({joined})")
        return out
    wanted, groups = set(), defaultdict(set)
    for b in bbls:
        boro = boro_value(b, dataset)
        _, blk, lot = keys.parts(b)
        groups[boro].add(str(blk))
        wanted.add((boro, str(blk), str(lot)))
    out = []
    for boro, blocks in groups.items():
        blocks = sorted(blocks)
        for i in range(0, len(blocks), bulk.IN_CLAUSE_MAX):
            joined = ",".join(f"'{x}'" for x in blocks[i:i + bulk.IN_CLAUSE_MAX])
            out += bulk.socrata(dataset, where=f"{sp['col']}='{boro}' and block in({joined})")
    if not strict_lot:
        return out
    return [r for r in out
            if (r.get(sp["col"]), str(r.get("block")), str(r.get("lot"))) in wanted]


def status_for(bbls):
    """Is each parcel regulated — and HOW? Three states, and the middle one is
    the one an ACRIS-only view cannot see."""
    desig = rows_for(bbls, DESIG_CAL)
    blds = rows_for(bbls, BUILDINGS)
    by_bbl = {}
    for r in blds:
        by_bbl.setdefault(r.get("bbl"), {})["building_record"] = r
    for r in desig:
        d = by_bbl.setdefault(r.get("bbl"), {})
        st = (r.get("status") or r.get("desig_stat") or "").upper()
        d["designation"] = r
        d["state"] = ("designated" if "DESIG" in st or r.get("desdate")
                      else "calendared" if "CALEND" in st else f"unmapped:{st[:30]}")
    return by_bbl


if __name__ == "__main__":
    for ds in (BUILDINGS, DESIG_CAL, PERMITS, VIOLATIONS, COMPLAINTS):
        ok, detail = control_query_ok(ds)
        print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")
