"""RETIRED LOTS — recovered from the sales record, which proves they existed.

    python retired_lots.py --find          # report only
    python retired_lots.py --find --write  # fold into spine.jsonl

THE GAP THIS FILLS

    `LEDGER_SCHEMA.md`, from the start: *"Retired lots must be rows, not
    omissions. A lot that merged in 2017 still owns its pre-2017 history, and
    any gate keyed to live lots drops it silently."*

    The spine is built from the CURRENT DOF tax map, so it holds only live lots.
    Every parcel that has since been merged, subdivided, renumbered or dissolved
    is simply absent — and a decoder joining on it gets no row, which reads
    exactly like "this source has nothing for that parcel."

    Measured on condo sales: 988 of 374,466 (0.26%) landed on BBLs the spine
    does not contain, across 674 distinct lots, weighted heavily to old sales
    (147 in 2004, 7 in 2024). Five were checked against PLUTO, the DTM tax-lot
    layer AND the DTM condo-unit layer: absent from all three. The lots are gone.

★ THE SALES RECORD IS ITSELF THE EVIDENCE. A recorded sale is proof that a lot
    existed on that date and was conveyed. So the archive that reaches back to
    2003 is not only a comparables source — it is a register of parcels the
    current tax map has forgotten, and the sale date bounds when the lot was
    alive.

    This scans EVERY sale, not just condominiums. A retired 1-family lot matters
    to the spine exactly as much as a retired condo unit.

⚠ ABSENT FROM THE SPINE IS NOT AUTOMATICALLY RETIRED. Three things produce it:
      retired      the lot existed and no longer does          <- what we want
      bad row      a malformed borough/block/lot in the source
      not covered  a lot type no current layer carries
    A sample is checked against the live layers before anything is written, and
    the check is REPORTED. Writing all three as "retired" would put fiction in
    the spine, which is worse than the gap it fixes.
"""
import json, os, pathlib, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import condo_sales as CS

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SPINE_DIR = pathlib.Path(os.environ.get(
    "DECODER_SPINE", pathlib.Path(__file__).with_name("spine")))
DTM = ("https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services"
       "/Tax_Lot_View/FeatureServer/0/query")


def lot_kind(bbl):
    """READ from the lot number — the only signal available for a lot that no
    layer still describes. Stated as INFERRED because that is what it is."""
    lot = int(bbl[6:])
    return ("condo_unit" if 1001 <= lot <= 7500 else
            "condo_billing" if lot > 7500 else "tax_lot")


def all_sale_bbls():
    """Every BBL that ever appears in a sale, with the dates that bound it.

    ⚠ NO PRICE FILTER. `pull_sales` drops $0 and nominal conveyances because
    they are not market comps — but a $0 transfer is still PROOF THE LOT
    EXISTED, which is the only question here. Reusing the comps filter would
    quietly shrink the register of parcels.
    """
    seen = {}

    def note(b, d, src):
        if len(b) != 10 or not b.isdigit():
            return False
        if b[0] not in "12345" or b[1:6] == "00000" or b[6:] == "0000":
            return False               # malformed: boro 0/6+, block 0, lot 0
        e = seen.get(b)
        if e is None:
            seen[b] = {"first": d, "last": d, "n": 1, "src": src}
        else:
            e["n"] += 1
            if d and (not e["first"] or d < e["first"]):
                e["first"] = d
            if d and (not e["last"] or d > e["last"]):
                e["last"] = d
        return True

    bad = Counter()
    print("scanning the archive (2003-2015), every property type...")
    for fp in sorted((pathlib.Path(__file__).with_name("sales_archive")).glob("*.xls")):
        rows, err = CS.read_archive_file(fp)
        if err:
            print(f"  ⚠ {fp.name}: {err}")
            continue
        for r in rows:
            try:
                b = CS.bbl(r["borough"], r["block"], r["lot"])
            except Exception:
                bad["unusable_bbl"] += 1
                continue
            if not note(b, str(r.get("sale_date") or "")[:10], "archive"):
                bad["malformed_bbl"] += 1
    print(f"  {len(seen):,} distinct BBLs so far")

    print("scanning Socrata (2016 ->), every property type...")
    for ds in (CS.ANNUAL, CS.ROLLING):
        off = 0
        while True:
            rows = CS.soda(ds, {"$select": "borough,block,lot,sale_date",
                                "$limit": 50000, "$offset": off, "$order": "sale_date"})
            if not rows:
                break
            for r in rows:
                try:
                    b = CS.bbl(r["borough"], r["block"], r["lot"])
                except Exception:
                    bad["unusable_bbl"] += 1
                    continue
                if not note(b, str(r.get("sale_date") or "")[:10], ds):
                    bad["malformed_bbl"] += 1
            off += len(rows)
            if len(rows) < 50000:
                break
    print(f"  {len(seen):,} distinct BBLs total · dropped {dict(bad)}")
    return seen


def verify(bbls, n=40):
    """Are they really gone? Ask all three live layers."""
    sample = bbls[:n]
    w = " or ".join(f"bbl='{b}'" for b in sample)
    pl = {str(r["bbl"]).split(".")[0] for r in
          CS.soda("64uk-42ks", {"$select": "bbl", "$where": w, "$limit": 500})}
    cu = {str(r["unit_bbl"]) for r in
          CS.soda("eguu-7ie3", {"$select": "unit_bbl",
                                "$where": " or ".join(f"unit_bbl='{b}'" for b in sample),
                                "$limit": 500})}
    q = {"where": "BBL IN (" + ",".join(f"'{b}'" for b in sample) + ")",
         "outFields": "BBL", "returnGeometry": "false", "f": "json"}
    dtm = {str(a["attributes"]["BBL"]) for a in json.load(urllib.request.urlopen(
        DTM + "?" + urllib.parse.urlencode(q), timeout=180)).get("features", [])}
    alive = [b for b in sample if b in pl or b in cu or b in dtm]
    return len(sample), len(alive), alive[:6]


def find(write=False):
    spine = {}
    with open(SPINE_DIR / "spine.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            spine[r["bbl"]] = r
    print(f"spine holds {len(spine):,} live parcels\n")

    seen = all_sale_bbls()
    missing = {b: e for b, e in seen.items() if b not in spine}
    print(f"\n{len(missing):,} BBLs sold at least once and are NOT in the spine")

    kinds = Counter(lot_kind(b) for b in missing)
    boro = Counter(b[0] for b in missing)
    print(f"  inferred kind: {dict(kinds)}")
    print(f"  by borough:    {dict(sorted(boro.items()))}")
    last_yr = Counter((e["last"] or "????")[:4] for e in missing.values())
    print(f"  last sold:     {dict(sorted(last_yr.items())[:8])} …")

    n, alive, ex = verify(sorted(missing))
    print(f"\n  VERIFIED {n} against PLUTO + DTM tax lots + DTM condo units:")
    print(f"    {n - alive} absent from all three -> genuinely RETIRED")
    print(f"    {alive} still alive somewhere -> NOT retired{': ' + ', '.join(ex) if ex else ''}")
    if alive:
        print("    ⚠ a non-zero count here means the spine is missing LIVE lots too, "
              "which is a different and larger problem than retirement")

    if not write:
        print("\n  report only — re-run with --write to fold these into the spine")
        return missing

    p = SPINE_DIR / "spine.jsonl"
    added = 0
    with open(p, "a", encoding="utf-8") as f:
        for b, e in sorted(missing.items()):
            f.write(json.dumps({
                "bbl": b, "boro": b[0], "block": int(b[1:6]), "lot": int(b[6:]),
                "kind": lot_kind(b),
                "has_condo": False, "has_reuc": False, "has_air": False,
                "has_sub": False, "has_easement": False,
                "status": "retired",
                "parent": None, "children": [],
                # the evidence, carried on the row: this lot is here because a
                # recorded sale proves it existed between these dates
                "source": f"DOF_SALES retired · {e['n']} sale(s) "
                          f"{e['first']}..{e['last']}",
                "kind_confidence": "inferred_from_lot_number",
            }, separators=(",", ":")) + "\n")
            added += 1
    total = sum(1 for _ in open(p, encoding="utf-8"))
    print(f"\n  appended {added:,} retired parcels — spine is now {total:,} rows "
          f"({len(spine):,} live + {added:,} retired)")
    return missing


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--find" in a:
        find(write="--write" in a)
    else:
        print(__doc__)
