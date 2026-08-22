"""The parcel spine — every parcel in NYC, organised by LINEAGE.

WHAT THIS IS FOR

    Every decoder — ACRIS, DOB, BSA, LPC, StreetEasy — walks the SAME spine, so
    facts from different sources land on the same parcel and a site's history
    assembles instead of scattering. The spine is built once, before any decoder
    runs, and it must be complete: a parcel missing here is a parcel no decoder
    will ever visit.

⚠ NEITHER DTM NOR PLUTO IS THE WHOLE PARCEL UNIVERSE — YOU NEED BOTH

    The DTM is the right primary authority, for two reasons that survive:

      1. **It is legal, not derived.** DOF's Digital Tax Map IS the tax lot;
         PLUTO is a planning extract. (This project has been bitten: MapPLUTO
         polygons can be FRAGMENTS — a lot read as 1,625 sf that was 65,000.)
      2. **It carries 307,436 condominium UNIT lots that PLUTO omits.** They are
         separately conveyed, mortgaged and taxed — they are parcels.

    ⚠ A THIRD REASON WAS ASSERTED HERE AND IS WITHDRAWN. It read: "PLUTO infers
    lot kind from the lot NUMBER, whereas the DTM carries it as DATA — BBL
    1022551031 is a REUC, not a condo unit." That rested on reading the C/R/A/S/E
    flags as IDENTITIES. They are RELATIONSHIPS (see `lot_flags`), so the claim
    does not stand. Kept visible rather than deleted, because a withdrawn reason
    that vanishes silently is how a disproven belief gets re-adopted later.

    And the DTM has a hole of its own: **condominium BILLING lots are in neither
    DTM layer.** `Tax_Lot_View` returns 14 rows total for LOT>=7501; PLUTO holds
    11,141 of them carrying 412,507 residential units — the new towers. So the
    two authorities keep OPPOSITE HALVES of a condominium and the spine must
    take both.

THE TRUE PARCEL UNIVERSE, counted live 2026-08-06

    DTM tax lots                          858,168   (every row IS a tax lot)
    DTM condominium UNIT lots             307,436   (PLUTO omits these)
    PLUTO condo BILLING lots               11,141   (both DTM layers omit these)
    ------------------------------------------------
    TOTAL PARCELS                       ~1,176,000

    Plus RETIRED BBLs, which no live layer contains and which own their own
    history. They are added from ACRIS legals and the DOF alteration book.

LINEAGE IS THE ORGANISING PRINCIPLE, NOT AN EXTRA COLUMN

    Login: *"work the spine through lineage so it's easy to follow sites
    assembling and subdividing over time instead of it being scattered."*

    So every parcel carries `parent` and `children`, and the spine is walkable
    both ways:

      * a condo UNIT's parent is its base lot (`condo_base_bbl`) — 307,436 edges
        that come free from the DTM condo layer
      * a MERGED lot's parent is its successor (DOF alteration book)
      * a SUBDIVIDED lot's children are the lots it became

    `walk(bbl)` returns the whole family — ancestors, descendants and siblings —
    so a decoder asked for one lot never misses the history that moved next door.
"""
import json, os, pathlib, sys, time, urllib.parse, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import keys

OUT = pathlib.Path(os.environ.get("DECODER_SPINE",
                                  pathlib.Path(__file__).with_name("spine")))
DTM = ("https://services6.arcgis.com/yG5s3afENB5iO9fj/arcgis/rest/services"
       "/Tax_Lot_View/FeatureServer/0/query")
CONDO_UNITS = "eguu-7ie3"
CONDO_BILLING = "p8u6-a6it"

FLAGS = [("CONDO_FLAG", "C", "condo_billing"), ("REUC_FLAG", "R", "reuc"),
         ("AIR_LOT_FLAG", "A", "air"), ("SUB_LOT_FLAG", "S", "subterranean"),
         ("EASEMENT_FLAG", "E", "easement")]


def _dtm(where, fields, offset, n=2000):
    q = {"where": where, "outFields": fields, "returnGeometry": "false",
         "resultOffset": offset, "resultRecordCount": n,
         "orderByFields": "BBL", "f": "json"}
    for attempt in range(4):
        try:
            with urllib.request.urlopen(DTM + "?" + urllib.parse.urlencode(q),
                                        timeout=300) as f:
                d = json.load(f)
            if "error" in d:
                raise RuntimeError(str(d["error"])[:120])
            return [a["attributes"] for a in d.get("features", [])]
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def pull_tax_lots(limit=None, progress_every=50_000):
    """Every DTM tax lot. Resumable: appends to a JSONL and restarts where it
    stopped, because 858,168 rows is a run that WILL be interrupted."""
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "tax_lots.jsonl"
    have = 0
    if path.exists():
        with open(path, encoding="utf-8") as f:
            have = sum(1 for _ in f)
        print(f"  resuming: {have:,} already pulled")
    fields = "BBL,BORO,BLOCK,LOT," + ",".join(f for f, _, _ in FLAGS)
    got = have
    with open(path, "a", encoding="utf-8") as out:
        while True:
            rows = _dtm("1=1", fields, got)
            if not rows:
                break
            for r in rows:
                out.write(json.dumps(r, separators=(",", ":")) + "\n")
            got += len(rows)
            if got % progress_every < len(rows):
                print(f"    {got:,} tax lots")
            if limit and got >= limit:
                break
    print(f"  tax lots on disk: {got:,}")
    return got


def pull_condo_units(limit=None):
    """307,436 condo unit lots, each carrying its BASE LOT — 307k lineage edges
    for free."""
    import bulk
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "condo_units.jsonl"
    rows = bulk.socrata(CONDO_UNITS,
                        select="unit_bbl,unit_boro,unit_block,unit_lot,"
                               "condo_base_bbl,condo_number,unit_designation",
                        limit=limit)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")
    print(f"  condo units on disk: {len(rows):,}")
    return len(rows)


def pull_condo_billing(limit=None):
    """Condominium BILLING lots — absent from BOTH DTM layers, so PLUTO is the
    only source.

    ⚠ DEFECT 2, found by the StreetEasy decoder 2026-08-06 and verified here:
    `Tax_Lot_View` returns **14 rows total** for LOT>=7501, and Gotham Point
    (4000067503), 5Pointz (4000867501) and Skyline Tower (4004377502) all return
    ZERO. PLUTO holds 11,141 such parcels carrying **412,507 residential units**
    — these are the new towers.

    WHY THE HOLE EXISTS — the two authorities keep opposite halves of a condo:
      * the DTM keeps the pre-condo BASE lot and sets CONDO_FLAG='C' on it
      * PLUTO drops that base lot and keeps the BILLING lot instead
      * the DTM unit layer's `condo_base_bbl` points at the BASE lot, never the
        billing lot — 0 of 307,436 unit rows reference a 75xx BBL

    So neither layer alone is the parcel universe, and a spine built from one has
    a hole shaped like the other.
    """
    import bulk
    OUT.mkdir(parents=True, exist_ok=True)
    rows = bulk.socrata("64uk-42ks", select="bbl,borough,block,lot,unitsres,address",
                        where="lot>=7501", limit=limit)
    path = OUT / "condo_billing.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")
    units = sum(int(float(r.get("unitsres") or 0)) for r in rows)
    print(f"  condo billing lots on disk: {len(rows):,} carrying {units:,} "
          f"residential units")
    return len(rows)


def lot_flags(row):
    """The DTM flags as RELATIONSHIPS — "this lot HAS a related lot of that kind".

    ⚠ CORRECTED 2026-08-06. The first version read these as IDENTITIES ("this lot
    IS a REUC") and was wrong. Found by the StreetEasy decoder while reconciling
    rent ledgers, verified here independently:

        472 lots carry TWO OR MORE mutually exclusive kind flags at once —
        CONDO+REUC 348, REUC+AIR 47, CONDO+AIR 40, CONDO+SUB 21, REUC+SUB 16.

    A lot cannot simultaneously BE a utility lot and BE an air lot. Under the
    relationship reading every one of those rows is ordinary. Confirmed against
    PLUTO: BBL 4004030003, flagged REUC_FLAG='R', is **Sven** — a 958-unit,
    64-storey rental tower, not a utility lot.

    Blast radius before the fix: ~19,400 lots (2.3%) carried a wrong `kind`, and
    anything gating on `kind == "ground"` silently discarded them. In the
    StreetEasy pipeline that produced 33 false "misplaced ledger" verdicts.

    ⚠ The old spine docstring cited "BBL 1022551031 is a REUC, not a condo unit"
    as a reason to prefer the DTM over PLUTO. That claim rested on this
    misreading and DOES NOT STAND. The DTM is still the right authority — for
    the other two reasons — but not for that one.
    """
    return {"has_condo": (row.get("CONDO_FLAG") or "").strip().upper() == "C",
            "has_reuc": (row.get("REUC_FLAG") or "").strip().upper() == "R",
            "has_air": (row.get("AIR_LOT_FLAG") or "").strip().upper() == "A",
            "has_sub": (row.get("SUB_LOT_FLAG") or "").strip().upper() == "S",
            "has_easement": (row.get("EASEMENT_FLAG") or "").strip().upper() == "E"}


def lot_kind(row):
    """What this lot IS. Every row in Tax_Lot_View is a TAX LOT.

    Kind now comes only from things that genuinely identify the parcel; the
    flags describe RELATIONSHIPS and are carried separately by lot_flags().
    """
    return "tax_lot"


def build():
    """tax lots + condo units -> one spine, keyed by BBL, with lineage edges.

    ⚠ RECONCILES, AND SAYS SO. The first version of this function read 1,165,604
    rows and wrote 1,164,820 parcels without a word about the 784 difference —
    the same silent-filter failure this project has met nine times, committed in
    fresh code. Every row read now lands in exactly one bucket and the buckets
    must sum to the input, or the run says DO NOT TRUST THIS.

    The 784 turned out to be legitimate de-duplication (73 tax lots and 708
    condo units appear on more than one polygon) plus THREE genuine collisions —
    BBLs that are both a tax lot and a condo unit. Those three are a real
    ambiguity and are now recorded rather than silently resolved by whichever
    file was read second.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    spine, edges = {}, 0
    stat = {"tax_lot_lines": 0, "tax_lot_dupes": 0, "tax_lot_bad": 0,
            "condo_lines": 0, "condo_dupes": 0, "condo_bad": 0, "collisions": []}

    tl = OUT / "tax_lots.jsonl"
    if not tl.exists():
        raise SystemExit("run --pull first")
    with open(tl, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            stat["tax_lot_lines"] += 1
            bbl = str(r.get("BBL") or "").strip()
            if len(bbl) != 10 or not bbl.isdigit():
                stat["tax_lot_bad"] += 1
                continue
            if bbl in spine:
                stat["tax_lot_dupes"] += 1     # multi-polygon lot; same parcel
                continue
            spine[bbl] = {"bbl": bbl, "boro": r.get("BORO"), "block": r.get("BLOCK"),
                          "lot": r.get("LOT"), "kind": lot_kind(r),
                          **lot_flags(r),
                          "status": "live", "parent": None, "children": [],
                          "source": "DTM"}

    cu = OUT / "condo_units.jsonl"
    if cu.exists():
        with open(cu, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                stat["condo_lines"] += 1
                ub = str(r.get("unit_bbl") or "").strip()
                base = str(r.get("condo_base_bbl") or "").strip()
                if len(ub) != 10 or not ub.isdigit():
                    stat["condo_bad"] += 1
                    continue
                if ub in spine:
                    if spine[ub].get("source") == "DTM":
                        # a BBL that is BOTH a tax lot and a condo unit. Do NOT
                        # let read-order decide which one wins.
                        stat["collisions"].append(ub)
                        spine[ub]["collision"] = "also a condo unit"
                    else:
                        stat["condo_dupes"] += 1
                    continue
                spine[ub] = {"bbl": ub, "boro": r.get("unit_boro"),
                             "block": r.get("unit_block"), "lot": r.get("unit_lot"),
                             "kind": "condo_unit", "easement": False,
                             "status": "live", "parent": base or None,
                             "children": [], "source": "DTM_condo",
                             "condo_number": r.get("condo_number"),
                             "unit": r.get("unit_designation")}
                if base and base in spine:
                    spine[base]["children"].append(ub)
                    edges += 1

    # ---- condo BILLING lots, from PLUTO because neither DTM layer has them ---
    cb = OUT / "condo_billing.jsonl"
    stat["billing_lines"] = 0
    stat["billing_added"] = 0
    if cb.exists():
        for line in open(cb, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            stat["billing_lines"] += 1
            b = str(r.get("bbl") or "").split(".")[0].strip()
            if len(b) != 10 or not b.isdigit() or b in spine:
                continue
            spine[b] = {"bbl": b, "boro": b[0], "block": int(b[1:6]),
                        "lot": int(b[6:]), "kind": "condo_billing",
                        "has_condo": True, "has_reuc": False, "has_air": False,
                        "has_sub": False, "has_easement": False,
                        "status": "live", "parent": None, "children": [],
                        "source": "PLUTO", "unitsres": r.get("unitsres"),
                        "address": r.get("address")}
            stat["billing_added"] += 1

    path = OUT / "spine.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for b in sorted(spine):
            f.write(json.dumps(spine[b], separators=(",", ":")) + "\n")

    from collections import Counter
    kinds = Counter(v["kind"] for v in spine.values())
    print(f"\nSPINE BUILT — {len(spine):,} parcels at {path}")
    for k, n in kinds.most_common():
        print(f"    {k:<16}{n:>10,}")
    # flags are RELATIONSHIPS, so they are counted alongside kind, never as it
    for flag in ("has_condo", "has_reuc", "has_air", "has_sub", "has_easement"):
        n = sum(1 for v in spine.values() if v.get(flag))
        print(f"    {flag:<16}{n:>10,}")
    multi = sum(1 for v in spine.values()
                if sum(bool(v.get(f)) for f in
                       ("has_condo", "has_reuc", "has_air", "has_sub")) > 1)
    print(f"    {'MULTI-flagged':<16}{multi:>10,}  <- proof these are relationships, "
          f"not identities")
    print(f"    {'lineage edges':<16}{edges:>10,}  (condo unit -> base lot)")
    orphans = sum(1 for v in spine.values() if v["parent"] and v["parent"] not in spine)
    if orphans:
        print(f"    ⚠ {orphans:,} condo units whose BASE LOT is absent from the "
              f"tax-lot layer — reported, not dropped")

    # ---- RECONCILE. Every input row lands in exactly one bucket. -----------
    read = (stat["tax_lot_lines"] + stat["condo_lines"]
            + stat.get("billing_lines", 0))
    accounted = (len(spine) + stat["tax_lot_dupes"] + stat["condo_dupes"]
                 + stat["tax_lot_bad"] + stat["condo_bad"] + len(stat["collisions"])
                 + (stat.get("billing_lines",0) - stat.get("billing_added",0)))
    print(f"\n  RECONCILIATION")
    print(f"    rows read              {read:>10,}")
    print(f"    parcels written        {len(spine):>10,}")
    print(f"    duplicate tax lots     {stat['tax_lot_dupes']:>10,}  "
          f"(same parcel, several polygons)")
    print(f"    duplicate condo units  {stat['condo_dupes']:>10,}")
    print(f"    malformed BBL          {stat['tax_lot_bad'] + stat['condo_bad']:>10,}")
    print(f"    BBL collisions         {len(stat['collisions']):>10,}  "
          f"(both a tax lot AND a condo unit)")
    print(f"    accounted for          {accounted:>10,}  "
          f"{'✓ reconciled' if accounted == read else '✗ MISMATCH — DO NOT TRUST THIS RUN'}")
    if stat["collisions"]:
        print(f"    collided BBLs: {', '.join(stat['collisions'][:8])}")
        print(f"      -> kept as TAX LOT with collision flag; read-order does "
              f"not decide")
    (OUT / "build_report.json").write_text(
        json.dumps({**stat, "parcels": len(spine), "edges": edges,
                    "reconciled": accounted == read}, indent=1), encoding="utf-8")
    return spine


def load():
    p = OUT / "spine.jsonl"
    if not p.exists():
        raise SystemExit("no spine yet — run: python spine.py --pull --build")
    out = {}
    with open(p, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
                out[r["bbl"]] = r
            except Exception:
                continue
    return out


def walk(bbl, spine=None):
    """The whole FAMILY of a parcel — ancestors, descendants, siblings.

    A decoder handed one BBL must see what that lot became and what it came
    from, or it reads a fragment of a history and reports it as the whole.
    """
    spine = spine or load()
    seen, stack = set(), [str(bbl)]
    while stack:
        b = stack.pop()
        if b in seen or b not in spine:
            continue
        seen.add(b)
        r = spine[b]
        if r.get("parent"):
            stack.append(r["parent"])
        stack.extend(r.get("children") or [])
    # siblings: same parent
    for b in list(seen):
        p = spine.get(b, {}).get("parent")
        if p and p in spine:
            stack.extend(spine[p].get("children") or [])
    while stack:
        b = stack.pop()
        if b in spine:
            seen.add(b)
    return sorted(seen)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--pull" in a:
        lim = next((int(x) for x in a if x.isdigit()), None)
        print("pulling DTM tax lots...")
        pull_tax_lots(limit=lim)
        print("pulling DTM condo units...")
        pull_condo_units(limit=lim)
    if "--build" in a:
        build()
    if "--walk" in a:
        b = next((x for x in a if x.isdigit() and len(x) == 10), None)
        s = load()
        fam = walk(b, s)
        print(f"family of {b}: {len(fam)} parcel(s)")
        for x in fam[:25]:
            r = s[x]
            print(f"   {x}  {r['kind']:<14} parent={r.get('parent')} "
                  f"children={len(r.get('children') or [])}")
    if not a:
        print(__doc__)
