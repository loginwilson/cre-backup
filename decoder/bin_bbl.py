"""THE BIN ↔ BBL JOIN — the bridge between the money side and the built side.

⚠ WHY IT IS THE JOIN AND NOT A LOOKUP. ACRIS speaks BBL and never says BIN. DOB
speaks BIN and treats the lot as an address. Until this join exists, CAPITAL and
TITLE live in one cabinet and PERMIT and ASBUILT live in another, and no query
can cross. Every function ACRIS cannot serve is on the far side of it.

SOURCE — Building Footprints `5zhs-2jue`, 1,082,993 rows, carrying BOTH keys:
    bin              DOB's building number
    base_bbl         DOF's tax-map BBL  <- the one ACRIS agrees with
    mappluto_bbl     PLUTO's BBL        <- measured against base_bbl, not assumed equal
    feature_code     2100 building · 5110 shed · 2110 skybridge · …
    last_status_type Demolition / Construction / Alteration / Initial
    construction_year

⚠ THREE TRAPS THIS FILE EXISTS TO MEASURE, NOT TO ASSUME AWAY:

  1. PLACEHOLDER BINs. A BIN of the form b000000 (1000000, 2000000 …) means
     "this borough, no specific building" — DOB's null. Joining on one silently
     attaches every unplaced job in a borough to a single fake building. It must
     be excluded and COUNTED, never quietly dropped.

  2. A BIN IS NOT A STANDING BUILDING. Demolished buildings keep their BIN and
     stay in this table. `last_status_type` is the only witness, and treating a
     BIN as "exists now" is the ASBUILT error waiting to happen.

  3. THE BBL MAY BE RETIRED. A footprint's base_bbl can name a lot that no
     longer exists — merged, apportioned, condo-converted. Those rows join to
     nothing in ACRIS and look exactly like "no documents", which is the lot
     lineage failure this project has already paid for. Counted here so the
     lineage work has a denominator.

    python bin_bbl.py            # pull, build, measure
    python bin_bbl.py --report   # measure from what is already on disk
"""
from __future__ import annotations

import collections, json, os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

import bulk

DATASET = "5zhs-2jue"
RAW = os.path.join(HERE, "_footprints.jsonl")
JOIN = os.path.join(HERE, "_bin_bbl.json")

FIELDS = ("bin,base_bbl,mappluto_bbl,feature_code,last_status_type,"
          "construction_year,doitt_id")

# ⚠ DOB's null. Not a building.
PLACEHOLDER = {f"{b}000000" for b in "12345"}

FEATURE = {"2100": "building", "2110": "skybridge", "5100": "gas station canopy",
           "5110": "shed / garage", "1001": "building under construction",
           "5150": "sidewalk shed", "2120": "canopy"}


def pull():
    print(f"pulling {DATASET} …", flush=True)
    rows = bulk.socrata(DATASET, select=FIELDS, paginate=True)
    with open(RAW, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    print(f"  {len(rows):,} rows -> {RAW}")
    return rows


def load():
    if not os.path.exists(RAW):
        return None
    out = []
    with open(RAW, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def norm_bbl(v):
    """10-digit BBL string, or None. ⚠ NEVER coerce a bad value into a number."""
    s = str(v or "").strip().split(".")[0]
    return s.zfill(10) if s.isdigit() and 0 < len(s) <= 10 and s != "0" * len(s) else None


def main():
    rows = load() if "--report" in sys.argv else None
    if rows is None:
        rows = pull()
    n = len(rows)
    print(f"\nFOOTPRINTS {n:,} rows\n")

    bin2bbl, bbl2bin = {}, collections.defaultdict(list)
    ph = nobin = nobbl = 0
    disagree = 0
    feat = collections.Counter()
    status = collections.Counter()
    dupe_bin = 0

    for r in rows:
        b = str(r.get("bin") or "").strip().split(".")[0]
        base = norm_bbl(r.get("base_bbl"))
        mp = norm_bbl(r.get("mappluto_bbl"))
        feat[str(r.get("feature_code") or "?")] += 1
        status[str(r.get("last_status_type") or "?")] += 1
        if not b or not b.isdigit():
            nobin += 1
            continue
        if b in PLACEHOLDER:
            ph += 1
            continue
        if base and mp and base != mp:
            disagree += 1
        if not base:
            nobbl += 1
            continue
        if b in bin2bbl:
            dupe_bin += 1
            continue
        bin2bbl[b] = base
        bbl2bin[base].append(b)

    print(f"  ⚠ placeholder BINs (b000000) EXCLUDED : {ph:,}")
    print(f"  ⚠ rows with no usable BIN             : {nobin:,}")
    print(f"  ⚠ rows with no usable base_bbl        : {nobbl:,}")
    print(f"  ⚠ BIN seen more than once             : {dupe_bin:,}")
    print(f"  JOINED  {len(bin2bbl):,} BINs -> {len(bbl2bin):,} distinct BBLs\n")

    both = sum(1 for r in rows if norm_bbl(r.get("base_bbl")) and norm_bbl(r.get("mappluto_bbl")))
    print(f"BASE_BBL vs MAPPLUTO_BBL — both present on {both:,} rows, "
          f"they DISAGREE on {disagree:,} ({100*disagree/max(both,1):.2f}%)")
    print("  base_bbl is the one ACRIS agrees with; the disagreement is PLUTO's, "
          "and it is why\n  the join is built on base_bbl and mappluto_bbl is kept "
          "only as a second witness.\n")

    print("FEATURE CODE — not every footprint is a building")
    for k, v in feat.most_common(7):
        print(f"  {k:<6}{FEATURE.get(k,'—'):<28}{v:>9,}  {100*v/n:>5.1f}%")

    print("\nLAST STATUS — ⚠ a BIN in this table is not a standing building")
    for k, v in status.most_common(6):
        print(f"  {k:<28}{v:>9,}  {100*v/n:>5.1f}%")

    d = collections.Counter(len(v) for v in bbl2bin.values())
    print(f"\nBUILDINGS PER LOT — one BBL is routinely many BINs")
    for k in sorted(d)[:6]:
        print(f"  {k:>3} BIN(s){'':<8}{d[k]:>9,} lots")
    big = sorted(bbl2bin.items(), key=lambda kv: -len(kv[1]))[:3]
    print("  most:  " + " · ".join(f"{b} = {len(v)} BINs" for b, v in big))

    # ── does it actually reach ACRIS? ────────────────────────────────────
    ap = os.path.join(HERE, "_acris_bbls.json")
    if os.path.exists(ap):
        raw = json.load(open(ap, encoding="utf-8"))
        acris = {norm_bbl(x) for x in (raw.keys() if isinstance(raw, dict) else raw)}
        acris.discard(None)
        hit = sum(1 for b in bbl2bin if b in acris)
        print(f"\nREACH INTO ACRIS — {len(acris):,} BBLs appear on ACRIS documents")
        print(f"  footprint BBLs that ACRIS also knows : {hit:,}/{len(bbl2bin):,} "
              f"({100*hit/max(len(bbl2bin),1):.1f}%)")
        miss = len(bbl2bin) - hit
        print(f"  ⚠ footprint BBLs ACRIS has never seen: {miss:,} — these are "
              f"RETIRED or\n    re-lotted BBLs plus genuine no-document lots. They "
              f"join to nothing and look\n    exactly like 'no documents'. This is "
              f"the lot-lineage denominator.")
        binreach = sum(len(bbl2bin[b]) for b in bbl2bin if b in acris)
        print(f"  BINs reachable from an ACRIS parcel  : {binreach:,}")
    else:
        print("\n  ⚠ _acris_bbls.json absent — reach into ACRIS is UNREAD, not zero.")

    json.dump({"bin2bbl": bin2bbl,
               "counts": {"rows": n, "joined_bins": len(bin2bbl),
                          "distinct_bbls": len(bbl2bin), "placeholder": ph,
                          "no_bin": nobin, "no_bbl": nobbl, "dupe_bin": dupe_bin,
                          "pluto_disagree": disagree, "pluto_both": both},
               "source": f"Socrata {DATASET} Building Footprints"},
              open(JOIN, "w"), separators=(",", ":"))
    print(f"\nwrote {JOIN}")
    return 0

# ── THE RESOLVER — use THIS, never bin2bbl raw ────────────────────────────
# ⚠ MEASURED AGAINST DOB'S OWN JOB ROWS (bin_bbl_check.py, 60,000 each):
#
#                        direct   +billing map   = agree   lineage residual
#     DOB NOW Build       93.5%          +5.9%      99.4%             0.5%
#     BIS legacy          90.9%          +2.3%      93.2%             6.8%
#
# ⚠ THE TWO SYSTEMS DISAGREE FOR DIFFERENT REASONS, and only one is fixable
# by a rule. Of DOB NOW's raw disagreements 92.7% are the CONDO BILLING LOT:
# the job states 75xx, the footprint states the land lot. That is a key
# mismatch and it resolves deterministically. Of BIS's, only 26.4% are billing
# lots — 68.4% are same-block ORDINARY lots, which is not a key problem at all.
# It is TIME: a job filed in 1996 states the lot as it was in 1996 and the
# footprint states it as DOF sees it now. No rule closes that; lot lineage does.
# So BIS's 6.8% is not join error, it is the lineage backlog with a denominator.
BILLING = None


def _billing():
    """condo bbl -> condo LAND bbl, for BOTH condo lot ranges.

    ⚠ TWO RANGES, AND ONLY ONE WAS HANDLED. Measured 2026-08-16 against live
    postings: 69.5% of posting BBLs reached no building, and the examples were
    1014461101/1102/1103 — condo UNIT lots (1001+), not BILLING lots (75xx). A
    unit lot has no footprint because the building stands on the land lot. The
    billing map alone therefore closed nothing for a ZLDA roster, which names
    every unit lot in the zoning lot. spine/condo_units_keyed.jsonl already held
    307,436 unit->land pairs; it simply was not being read.

    ⚠ 24 of 12,196 billing rows carry no billing BBL at all, so this reads with
    .get and counts, never assumes the shape."""
    global BILLING
    if BILLING is None:
        BILLING = {}
        p = os.path.join(HERE, "spine", "condo_billing_map.jsonl")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    k = r.get("condo_billing_bbl")
                    if k and r.get("condo_base_bbl"):
                        BILLING[k] = r["condo_base_bbl"]
        u = os.path.join(HERE, "spine", "condo_units_keyed.jsonl")
        if os.path.exists(u):
            with open(u, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    k, base = r.get("unit_bbl"), r.get("condo_base_bbl")
                    if k and base:
                        BILLING.setdefault(k, base)
    return BILLING


def land_bbl(bbl):
    """A DOB-stated BBL mapped to the LAND lot the footprint speaks in.

    ⚠ THIS IS THE HALF THE CONDO DEFECT PUTS IN YOUR WAY. A condo's documents
    and its buildings are keyed to different lots; without this, every condo job
    reads as 'BIN and BBL disagree' and a whole building class silently drops.
    """
    b = norm_bbl(bbl)
    return _billing().get(b, b) if b else None


def agrees(bin_, stated_bbl, join=None):
    """Does a DOB job row's own BBL agree with the footprint's, once the condo
    billing lot is resolved? Returns True / False / None (BIN unknown)."""
    j = join if join is not None else json.load(
        open(JOIN, encoding="utf-8"))["bin2bbl"]
    fp = j.get(str(bin_).strip().split(".")[0])
    if fp is None:
        return None                      # ⚠ unknown BIN is UNREAD, not False
    return fp == land_bbl(stated_bbl)


if __name__ == "__main__":
    raise SystemExit(main())
