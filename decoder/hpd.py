"""HPD — registrations, contacts, distress, and the co-op blind spot.

Two things HPD gives that nothing else does:

  1. **CONTACTS, refreshed ANNUALLY.** Registration is mandatory every year for
     any building with 3+ residential units, so it files on the CALENDAR rather
     than on an event — which means it ages differently from every deed-driven
     source. Head officer, managing agent, corporate owner, and SHAREHOLDER.
  2. **THE CO-OP BLIND SPOT.** A co-op transfers SHARES, records no deed, and is
     therefore invisible in ACRIS. The `Shareholder` contact role is one of the
     only public routes to who holds the building.

⚠ THE JOIN GRAPH MATTERS MORE THAN THE PARCEL KEY. Two of these datasets carry
NO borough/block/lot at all:

    BBL ──> registrations (tesw-yqqr)  ──registrationid──> contacts (feu5-w2e2)
                     │
                     └──buildingid──> LL44 unit rents (9ay9-xkek)

So contacts and rents are reachable ONLY through the registration. A parcel with
no current registration has no reachable contact here — and that is a finding
about the building (fewer than 3 units, or non-compliance), not a gap in the pull.

⚠ AND THE KEY FORMAT IS PER DATASET, as with DOB. Measured 2026-08-05:
    tesw-yqqr registrations  boro 'BROOKLYN'  block '7974' UNPADDED  lot '28'
    wvxf-dwi5 violations     boro 'BROOKLYN'  block '3031' UNPADDED  lot '15'
    bzxi-2tsw CONH           borough 'MANHATTAN' + a real `bbl` column
    hcir-3275 AEP            boro 'Brooklyn' TITLE + a real `bbl` column
Never generalise a key format from one table to an agency.
"""
import sys, pathlib
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk
import keys

REGISTRATIONS = "tesw-yqqr"   # boro UPPER, block/lot unpadded, + registrationid/buildingid
CONTACTS = "feu5-w2e2"        # registrationid ONLY
VIOLATIONS = "wvxf-dwi5"      # boro UPPER, block/lot unpadded
CONH = "bzxi-2tsw"            # borough UPPER + bbl
AEP = "hcir-3275"             # boro TITLE + bbl
LL44_RENT = "9ay9-xkek"       # buildingid ONLY

BORO_NAME = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn",
             "4": "Queens", "5": "Staten Island"}
SPEC = {
    REGISTRATIONS: {"col": "boro", "case": "upper", "pad": 0, "bbl_col": None},
    VIOLATIONS:    {"col": "boro", "case": "upper", "pad": 0, "bbl_col": None},
    CONH:          {"col": "borough", "case": "upper", "pad": 0, "bbl_col": "bbl"},
    # ⚠ AEP has NO block/lot columns at all — bbl is the only parcel key
    AEP:           {"col": "boro", "case": "title", "pad": 0, "bbl_col": "bbl"},
}

# The roles that matter, and why. TITLE is more reliable than name (see
# SIGNATURE_LADDER.md) and these are typed, not handwritten.
ROLE_VALUE = {
    "Shareholder": "⚠ co-op — ACRIS records NO deed for a share transfer, so this "
                   "is one of the only public routes to who holds the building",
    "HeadOfficer": "the responsible officer of the owning entity — closest thing "
                   "to a named principal that HPD publishes",
    "Agent": "must be serviceable within NYC — often the most reachable human "
             "attached to an out-of-state owner",
    "CorporateOwner": "cross-checks the ACRIS grantee, and is refreshed ANNUALLY "
                      "where the deed is not",
    "IndividualOwner": "a natural person owning directly",
    "SiteManager": "day-to-day manager; most numerous role in the file",
}


def keyparts(bbl, dataset):
    boro, block, lot = keys.parts(bbl)
    sp = SPEC[dataset]
    name = BORO_NAME[str(boro)]
    return (name.upper() if sp["case"] == "upper" else name, str(block), str(lot))


def control_query_ok(dataset):
    """Self-calibrating: sample a real row from THIS dataset and prove our key
    construction finds it again.

    Branches on WHAT THE DATASET ACTUALLY HAS. The first version demanded a
    `block` column and failed AEP, which carries only `bbl` — the control was
    testing its own assumption rather than the dataset. A control keyed to a
    fixed parcel, or to a column that may not exist, manufactures failures
    exactly where it is meant to prevent them.
    """
    sample = bulk.socrata(dataset, limit=1)
    if not sample:
        return False, f"{dataset}: returned nothing at all"
    row, sp = sample[0], SPEC[dataset]
    if sp["bbl_col"] and row.get(sp["bbl_col"]):
        val = row[sp["bbl_col"]]
        found = bulk.socrata(dataset, where=f"{sp['bbl_col']}='{val}'", limit=5)
        return bool(found), (f"{dataset}: {sp['bbl_col']}={val!r} -> {len(found)} rows "
                             f"(keyed by BBL, no block column)")
    boro, blk = row.get(sp["col"]), row.get("block")
    if not (boro and blk):
        return False, f"{dataset}: sample lacks {sp['col']}/block — has {list(row)[:6]}"
    found = bulk.socrata(dataset, where=f"{sp['col']}='{boro}' and block='{blk}'", limit=5)
    return bool(found), f"{dataset}: {sp['col']}={boro!r} block={blk!r} -> {len(found)} rows"


def rows_for(bbls, dataset):
    """Parcel-keyed HPD datasets."""
    sp = SPEC[dataset]
    if sp["bbl_col"]:
        out = []
        vals = [str(int(b)) for b in bbls]
        for i in range(0, len(vals), bulk.IN_CLAUSE_MAX):
            part = vals[i:i + bulk.IN_CLAUSE_MAX]
            joined = ",".join(f"'{x}'" for x in part)
            out += bulk.socrata(dataset, where=f"{sp['bbl_col']} in({joined})")
        return out
    groups = defaultdict(set)
    for b in bbls:
        boro, blk, lot = keyparts(b, dataset)
        groups[boro].add((blk, lot))
    out = []
    for boro, pairs in groups.items():
        blocks = sorted({blk for blk, _ in pairs})
        for i in range(0, len(blocks), bulk.IN_CLAUSE_MAX):
            joined = ",".join(f"'{x}'" for x in blocks[i:i + bulk.IN_CLAUSE_MAX])
            out += bulk.socrata(dataset, where=f"{sp['col']}='{boro}' and block in({joined})")
    wanted = {keyparts(b, dataset) for b in bbls}
    return [r for r in out
            if (r.get(sp["col"]), r.get("block"), r.get("lot")) in wanted]


def contacts_for(bbls):
    """The chain: BBL -> registration -> contacts. Returns (contacts, registrations).

    An empty contact list for a parcel means it has no current registration —
    a fact about the BUILDING (under 3 units, or not registered), not a gap.
    """
    regs = rows_for(bbls, REGISTRATIONS)
    ids = sorted({r["registrationid"] for r in regs if r.get("registrationid")})
    contacts = bulk.socrata_in(CONTACTS, "registrationid", ids, quote=True) if ids else []
    by_reg = {r["registrationid"]: r for r in regs if r.get("registrationid")}
    for c in contacts:
        reg = by_reg.get(c.get("registrationid")) or {}
        c["_bbl"] = (keys.bbl({v.upper(): k for k, v in BORO_NAME.items()}[reg["boro"].upper()],
                              int(reg["block"]), int(reg["lot"]))
                     if reg.get("boro") and reg.get("block") and reg.get("lot") else None)
    return contacts, regs


if __name__ == "__main__":
    for ds in (REGISTRATIONS, VIOLATIONS, CONH, AEP):
        ok, detail = control_query_ok(ds)
        print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")
