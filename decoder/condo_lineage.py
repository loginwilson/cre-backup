"""CONDO LINEAGE — base lot <-> billing lot <-> unit lots, from DOF's own key.

    python condo_lineage.py --pull --build
    python condo_lineage.py --check 4004377502

THE HOLE THIS FILLS

    The spine holds 306,725 condo UNIT parcels and 11,132 condo BILLING parcels
    and NOT ONE EDGE BETWEEN THEM. A unit points at its BASE lot
    (`condo_base_bbl`); the billing lot points at nothing and nothing points at
    it. So a condo sale — which lands on a unit lot — cannot be rolled up to the
    building it is in, and a building keyed to its billing lot cannot reach its
    own sales.

    Login: *"the same must be done for Condo using DOF services."*

⚠ AND `spine.py` ALREADY NAMES THE ANSWER WITHOUT PULLING IT.
    `CONDO_BILLING = "p8u6-a6it"` has been sitting in that file as an unused
    constant. The dataset is the DOF Digital Tax Map's condominium layer, 12,196
    rows, and it carries every edge needed:

        condo_billing_bbl   3023107501     the 75xx tax-billing lot
        condo_base_bbl      3023100037     the physical lot it stands on
        condo_key           300973         and the UNITS layer carries this too
        condo_name          "THE 323 W. 39TH ST CONDOMINIUM"

    So the join is DOF's OWN KEY, not a name or an address match. That matters:
    every other route between these three parcels — name similarity, shared
    address, geometric containment — is a guess that works most of the time,
    which is the worst kind of join because its failures are invisible.

★ `condo_name` IS ALSO THE NAME CONSOLIDATION. Login expected to need Marketproof
    for it. DOF publishes the condominium's legal name against its billing lot,
    which is the authoritative version of what a listing service approximates.

⚠ condo_key IS NOT condo_number. `condo_key` = borough digit + the condo number
    zero-padded to five: condo 835 in Manhattan is `100835`, condo 973 in
    Brooklyn is `300973`. Joining on `condo_number` alone silently merges
    Manhattan condo 835 with Brooklyn condo 835. The spine's existing
    `condo_units.jsonl` was pulled WITHOUT `condo_key`, so this re-pulls it
    rather than reconstructing the key and hoping.
"""
import json, os, pathlib, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sink

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SOURCE = "DOF_CONDO"
BILLING = "p8u6-a6it"
UNITS = "eguu-7ie3"
SPINE_DIR = pathlib.Path(os.environ.get(
    "DECODER_SPINE", pathlib.Path(__file__).with_name("spine")))
DECODER_ENV = pathlib.Path("C:/dev/acris-decoder.env")


def env():
    v = {}
    for line in open(DECODER_ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip().strip('"').strip("'")
    return v


def soda(ds, select, tries=5):
    """Whole dataset, paged. A transport failure raises — never a short pull."""
    tok = env().get("SOCRATA_APP_TOKEN")
    out, off = [], 0
    while True:
        url = (f"https://data.cityofnewyork.us/resource/{ds}.json?"
               + urllib.parse.urlencode({"$select": select, "$limit": 50000,
                                         "$offset": off, "$order": ":id"}))
        req = urllib.request.Request(url, headers={"X-App-Token": tok} if tok else {})
        last = None
        for i in range(tries):
            try:
                with urllib.request.urlopen(req, timeout=300) as f:
                    chunk = json.load(f)
                break
            except Exception as e:
                last = e
                time.sleep(2 * (i + 1))
        else:
            raise RuntimeError(f"{ds} FAILED at offset {off}: {last}")
        if not chunk:
            break
        out.extend(chunk)
        off += len(chunk)
        if len(chunk) < 50000:
            break
    return out


def pull():
    SPINE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"pulling {BILLING} (condo billing <-> base)...")
    b = soda(BILLING, "condo_billing_bbl,condo_base_bbl,condo_key,condo_number,"
                      "condo_base_boro,condo_base_block,condo_base_lot,condo_name")
    (SPINE_DIR / "condo_billing_map.jsonl").write_text(
        "\n".join(json.dumps(r, separators=(",", ":")) for r in b), encoding="utf-8")
    print(f"  {len(b):,} rows")

    print(f"re-pulling {UNITS} WITH condo_key...")
    u = soda(UNITS, "unit_bbl,condo_base_bbl,condo_key,condo_number,unit_designation")
    (SPINE_DIR / "condo_units_keyed.jsonl").write_text(
        "\n".join(json.dumps(r, separators=(",", ":")) for r in u), encoding="utf-8")
    print(f"  {len(u):,} rows")
    return len(b), len(u)


def build(write_spine=True):
    """Fold the edges into the spine. Reconciles, and says so."""
    run_id = f"condo-lineage-{int(time.time())}"
    bmap = [json.loads(l) for l in
            (SPINE_DIR / "condo_billing_map.jsonl").read_text(encoding="utf-8").splitlines() if l]
    units = [json.loads(l) for l in
             (SPINE_DIR / "condo_units_keyed.jsonl").read_text(encoding="utf-8").splitlines() if l]
    print(f"billing rows {len(bmap):,} · unit rows {len(units):,}")
    sink.heartbeat(SOURCE, run_id, done=0, total=len(bmap) + len(units),
                   note="condo lineage")

    # condo_key -> the condominium
    condo = {}
    dupe_key = 0
    for r in bmap:
        k = str(r.get("condo_key") or "")
        bb = str(r.get("condo_billing_bbl") or "")
        if not k or len(bb) != 10:
            continue
        if k in condo and condo[k]["billing"] != bb:
            # one condo_key with two billing lots is real (phased condos) and must
            # be recorded, not overwritten by whichever row was read second
            condo[k].setdefault("extra_billing", []).append(bb)
            dupe_key += 1
            continue
        condo.setdefault(k, {"billing": bb, "base": str(r.get("condo_base_bbl") or ""),
                             "name": r.get("condo_name"), "units": []})
    print(f"  {len(condo):,} condominiums keyed"
          + (f" · {dupe_key:,} extra billing lots on phased condos" if dupe_key else ""))

    unmatched = Counter()
    for r in units:
        k = str(r.get("condo_key") or "")
        ub = str(r.get("unit_bbl") or "")
        if len(ub) != 10:
            unmatched["bad_unit_bbl"] += 1
            continue
        if k not in condo:
            # a unit whose condominium is absent from the billing layer. REPORTED,
            # never dropped — it is the case where a sale can never roll up.
            unmatched["no_billing_row"] += 1
            continue
        condo[k]["units"].append(ub)
    print(f"  units attached: {sum(len(c['units']) for c in condo.values()):,} of {len(units):,}")
    for k, v in unmatched.items():
        print(f"     ⚠ {v:,} {k}")

    sizes = [len(c["units"]) for c in condo.values()]
    empty = sum(1 for s in sizes if s == 0)
    print(f"  {empty:,} condominiums have a billing lot and ZERO unit lots "
          f"(commercial condos, or units not yet in the DTM)")

    if not write_spine:
        return condo

    # ── fold into spine.jsonl ────────────────────────────────────────────────
    p = SPINE_DIR / "spine.jsonl"
    rows, n = {}, 0
    with open(p, encoding="utf-8") as f:
        for line in f:
            n += 1
            r = json.loads(line)
            rows[r["bbl"]] = r
    print(f"\nspine: {n:,} lines read, {len(rows):,} parcels")

    stat = Counter()
    for k, c in condo.items():
        bb, base = c["billing"], c["base"]
        if bb in rows:
            rows[bb]["condo_key"] = k
            rows[bb]["condo_name"] = c.get("name")
            rows[bb]["base_bbl"] = base or None
            rows[bb]["children"] = sorted(set(rows[bb].get("children") or []) | set(c["units"]))
            stat["billing_linked"] += 1
        else:
            stat["billing_lot_ABSENT_from_spine"] += 1
        if base in rows:
            rows[base]["billing_bbl"] = bb
            rows[base]["condo_key"] = k
            rows[base]["condo_name"] = c.get("name")
            stat["base_linked"] += 1
        elif base:
            stat["base_lot_ABSENT_from_spine"] += 1
        for ub in c["units"]:
            if ub in rows:
                rows[ub]["billing_bbl"] = bb
                rows[ub]["condo_key"] = k
                rows[ub]["condo_name"] = c.get("name")
                stat["unit_linked"] += 1
            else:
                stat["unit_ABSENT_from_spine"] += 1

    print("\nEDGES WRITTEN")
    for k, v in stat.most_common():
        mark = "   ⚠" if "ABSENT" in k else ""
        print(f"  {k:<34}{v:>9,}{mark}")

    tmp = p.with_suffix(".jsonl.new")
    with open(tmp, "w", encoding="utf-8") as f:
        for b in sorted(rows):
            f.write(json.dumps(rows[b], separators=(",", ":")) + "\n")
    out_n = sum(1 for _ in open(tmp, encoding="utf-8"))
    if out_n != len(rows):
        raise SystemExit(f"REFUSING TO SWAP — wrote {out_n:,} of {len(rows):,}")
    tmp.replace(p)
    print(f"\nspine rewritten: {out_n:,} parcels (was {n:,} lines) — "
          f"parcel count unchanged, edges added")

    sink.heartbeat(SOURCE, run_id, done=len(bmap) + len(units),
                   total=len(bmap) + len(units), status="complete",
                   note=f"{stat['unit_linked']} unit edges")
    return condo


def check(bbl):
    """Walk one condominium from whichever parcel you have."""
    rows = {}
    with open(SPINE_DIR / "spine.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            rows[r["bbl"]] = r
    r = rows.get(str(bbl))
    if not r:
        return print(f"{bbl} is not in the spine")
    print(json.dumps({k: v for k, v in r.items() if k != "children"}, indent=1))
    kids = r.get("children") or []
    print(f" children: {len(kids)}  {kids[:8]}{' …' if len(kids) > 8 else ''}")
    for rel in ("billing_bbl", "base_bbl", "parent"):
        if r.get(rel) and r[rel] in rows:
            o = rows[r[rel]]
            print(f" {rel} -> {o['bbl']} {o['kind']} "
                  f"{o.get('condo_name') or ''} children={len(o.get('children') or [])}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--pull" in a:
        pull()
    if "--build" in a:
        build()
    if "--check" in a:
        check(a[a.index("--check") + 1])
    if not a:
        print(__doc__)
