"""THE ALLOCATION CHART, transcribed as our own table — one row per LOT per CHART.

LOGIN, 2026-08-06:

    "When you record the transfers of development rights, whatever the
     instrument is, record PARTIES so we know if this lot GAINED air rights or
     if one SOLD. That table at the end of documents needs to be recorded in our
     own decode, since ONE TABLE MAY NOT CAPTURE ALL THE ASSEMBLAGES. Especially
     here where there wasn't just one site, there were multiple."

WHY THIS IS A DIFFERENT TABLE FROM THE ENVELOPE LEDGER

    envelope_ledger.py records lot 49's VIEW: +53,578 in, balance 209,968. That
    answers "how much can lot 49 build" and destroys everything else. The chart
    itself is a statement about EVERY lot in the zoning lot — its land, what it
    generates, what it keeps, what it gives up, and who owns it.

    So the ledger is a DERIVATIVE of this table, not a substitute for it. This
    module derives it at the bottom and checks the two agree.

WHY ONE CHART IS NEVER ENOUGH

    Six charts, nine years, and each one restates the whole zoning lot as it
    stood that day:

        2010  4 lots   the Sabetfard merger
        2012  5 lots   + the Horne co-op
        2013  6 lots   + Brick Farms
        2013  7 lots   + 133 West 24th
        2013  8 lots   + the lot 20 airspace (self-dealt)
        2019  2 lots   the split — a different zoning lot entirely

    Reading only the last chart tells you the end state and nothing about how it
    was assembled, at what price, or from whom. Reading only the first tells you
    a story that was obsolete within two years. THE ASSEMBLAGE IS THE SEQUENCE.

⚠ DIRECTION IS THE FIELD THAT MAKES IT USABLE
    Without an explicit GAINED / SOLD, a row of numbers cannot tell you whether
    a lot is a buyer or a seller — and that single distinction is the difference
    between "development site" and "development-dead". It is recorded per lot
    per chart, never inferred at read time.
"""
import csv, pathlib, sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent

DDL = """
create table if not exists acris_rights_allocation (
  document_id   text not null,
  page          text not null,
  chart_date    date not null,
  chart_kind    text not null,          -- MERGER | SPLIT — selects the arithmetic
  bbl           text not null,          -- the lot this ROW is about
  role          text not null,          -- DEVELOPER | GRANTOR
  direction     text not null,          -- GAINED | SOLD | NEUTRAL
  party         text,                   -- who owned it AT THE CHART'S DATE
  lot_area      numeric,
  far           numeric,
  generated     numeric,                -- lot_area * far
  retained      numeric,                -- what the seller keeps
  transferred   numeric,                -- the excess that moved
  after_transfer numeric,               -- this lot's envelope once done
  counterparty_bbl text,
  price         numeric,                -- NULL unless priced PER LOT here
  price_basis   text,                   -- PER_LOT | BUNDLED | OFF_PARCEL
  per_sf        numeric,
  basis         text not null,          -- read | derived
  note          text,
  primary key (document_id, bbl)
);
create index if not exists acris_alloc_bbl on acris_rights_allocation(bbl, chart_date);
create index if not exists acris_alloc_dir on acris_rights_allocation(direction);

-- every lot that has ever SOLD rights, with what it has left ------------------
create or replace view rights_sellers as
select bbl, party, max(chart_date) as last_chart,
       sum(transferred) as sf_sold, min(retained) as sf_retained,
       string_agg(distinct document_id, ', ') as evidence
from acris_rights_allocation where direction = 'SOLD'
group by bbl, party order by sum(transferred) desc;

-- the assemblage as it built, chart by chart ---------------------------------
create or replace view assemblage_progression as
select chart_date, document_id, count(*) as lots_in_zoning_lot,
       sum(lot_area) as land_sf, sum(generated) as generated_sf,
       max(after_transfer) filter (where role = 'DEVELOPER') as developer_envelope
from acris_rights_allocation group by chart_date, document_id
order by chart_date;
"""

DEV = "1008000049"

# ---------------------------------------------------------------------------
# THE CHARTS, transcribed. `basis` says read where the cell is on the page and
# derived where it follows from other cells. Unknown cells are None — NEVER
# back-filled by arithmetic, because a computed cell that looks transcribed
# destroys the cross-check the chart exists to provide.
# ---------------------------------------------------------------------------
CHARTS = [
 # ---- 2010 · the Sabetfard merger --------------------------------------
 dict(doc="2010102601040006", page="p038", date="2010-10-14", kind="MERGER", bbl=DEV,
      role="DEVELOPER", direction="GAINED", party="112-118 West 25th LLC (Extell)",
      lot_area=15_639, far=10.0, generated=156_390, after=209_968, basis="read"),
 dict(doc="2010102601040006", page="p038", date="2010-10-14", kind="MERGER", bbl="1008000053",
      role="GRANTOR", direction="SOLD", party="120-22 W 25 Street LLC (Sabet Mgmt)",
      lot_area=4_077, far=10.0, generated=40_770, retained=16_906,
      transferred=23_864, after=16_906, cp=DEV, basis="read", pb="BUNDLED",
      note="120 West 25th Street"),
 dict(doc="2010102601040006", page="p038", date="2010-10-14", kind="MERGER", bbl="1008000055",
      role="GRANTOR", direction="SOLD", party="124-26 W 25 Street LLC (Sabet Mgmt)",
      lot_area=2_469, far=10.0, generated=24_690, retained=9_620,
      transferred=15_070, after=9_620, cp=DEV, basis="read", pb="BUNDLED",
      note="124 West 25th Street"),
 dict(doc="2010102601040006", page="p038", date="2010-10-14", kind="MERGER", bbl="1008000056",
      role="GRANTOR", direction="SOLD", party="124-26 W 25 Street LLC (Sabet Mgmt)",
      lot_area=2_469, far=10.0, generated=24_690, retained=10_046,
      transferred=14_644, after=10_046, cp=DEV, basis="read", pb="BUNDLED",
      note="126 West 25th Street. ⚠ SAME OWNER as lot 55 — one party, two lots, "
           "and the chart is the only place that is visible"),

 # ---- 2012 · the Horne co-op ------------------------------------------
 dict(doc="2012122701550003", page="p043", date="2012-12-19", kind="MERGER", bbl=DEV,
      role="DEVELOPER", direction="GAINED", party="112-118 West 25th LLC (Extell)",
      lot_area=15_639, far=10.0, generated=156_390, after=232_813, basis="read",
      note="developer land identical to the 2010 chart — the cross-check that "
           "made the Horne quantity derivable"),
 dict(doc="2012122701550003", page="p043", date="2012-12-19", kind="MERGER", bbl="1008000023",
      role="GRANTOR", direction="SOLD",
      party="The Horne Building Owners Corp (residential co-op)",
      lot_area=5_725, far=10.0, generated=57_250, retained=34_405,
      transferred=22_845, after=34_405, cp=DEV, price=4_614_690, pb="PER_LOT", basis="derived",
      note="127 West 24th. Chart totals: 30,379 sf land, 303,790 generated, "
           "76,423 excess. Lot 23's own line derived by subtracting the 2010 "
           "chart's four lots (24,654 sf) from this chart's total"),

 # ---- 2013 · Brick Farms ----------------------------------------------
 dict(doc="2013052101674004", page="p040", date="2013-05-17", kind="MERGER", bbl=DEV,
      role="DEVELOPER", direction="GAINED", party="112-118 West 25th LLC (Extell)",
      lot_area=15_639, far=10.0, generated=156_390, after=243_539, basis="read"),
 dict(doc="2013052101674004", page="p040", date="2013-05-17", kind="MERGER", bbl="1008000022",
      role="GRANTOR", direction="SOLD",
      party="Brick Farms Cooperative Ltd (c/o Forest City Ratner)",
      lot_area=2_862.5, far=10.0, generated=28_625, retained=17_899,
      transferred=10_726, after=17_899, cp=DEV, price=1_450_000, pb="PER_LOT", basis="read",
      note="131 West 24th. Mortgagee Ridgewood Savings Bank consented"),

 # ---- 2013 · 133 West 24th --------------------------------------------
 dict(doc="2013052101674008", page="p041", date="2013-05-17", kind="MERGER", bbl=DEV,
      role="DEVELOPER", direction="GAINED", party="112-118 West 25th LLC (Extell)",
      lot_area=15_639, far=10.0, generated=156_390, after=254_261, basis="read"),
 dict(doc="2013052101674008", page="p041", date="2013-05-17", kind="MERGER", bbl="1008000021",
      role="GRANTOR", direction="SOLD", party="133 West 24th Street Corporation (co-op)",
      lot_area=None, far=10.0, generated=None, retained=None,
      transferred=10_722, after=None, cp=DEV, price=1_340_250, pb="PER_LOT", basis="read",
      note="⚠ generated/retained NOT TRANSCRIBED — only the transferred column "
           "and the developer's after-total were read. Left NULL rather than "
           "back-computed, so the gap stays visible. Mortgagee Wells Fargo as "
           "CMBS trustee consented; lot capped at 7 dwelling units"),

 # ---- 2013 · the self-dealt airspace over lot 20 ------------------------
 dict(doc="2013080901116002", page="p040", date="2013-08-07", kind="MERGER", bbl=DEV,
      role="DEVELOPER", direction="GAINED", party="112-118 West 25th LLC (Extell)",
      lot_area=15_639, far=10.0, generated=156_390, after=268_964, basis="read",
      note="chart totals 390,160 across all eight lots"),
 dict(doc="2013080901116002", page="p040", date="2013-08-07", kind="MERGER", bbl="1008000020",
      role="GRANTOR", direction="SOLD",
      party="112-118 West 25th LLC (AS AIRSPACE OWNER — same entity as buyer)",
      lot_area=2_912, far=None, generated=None, retained=None,
      transferred=14_703, after=None, cp=DEV, price=None, basis="read", pb="OFF_PARCEL",
      note="135 West 24th, airspace above elev. 130 ft. ⚠ SELF-DEALING: one "
           "entity in two capacities, so zero tax and NO PRICE ON THIS PARCEL. "
           "The consideration was recorded against lot 20. ⚠ Lot 20's own ZLDA "
           "is CRFN 2008000078652, recorded 2008-02-26 — the assemblage's FIRST "
           "instrument, two years before Sabetfard"),

 # ---- 2019 · the split — a DIFFERENT zoning lot -------------------------
 dict(doc="2019071700601003", page="p044", date="2019-05-20", kind="SPLIT", bbl=DEV,
      role="DEVELOPER", direction="SOLD", party="LAM GEN 25 LLC",
      lot_area=8_527, far=10.0, generated=85_270, retained=141_929,
      transferred=127_035, after=141_929, cp="1008000050", basis="read",
      note="⚠ lot 49 is the GRANTOR here — the only chart where the developer "
           "parcel gives rights away. 85,270 self-generated + 56,659 acquired"),
 dict(doc="2019071700601003", page="p044", date="2019-05-20", kind="SPLIT", bbl="1008000050",
      role="DEVELOPER", direction="GAINED", party="LG CHELSEA LLC",
      lot_area=7_112, far=10.0, generated=71_120, after=127_035, cp=DEV,
      basis="read",
      note="113-117 West 24th. 71,120 self-generated + 55,915 acquired. Both "
           "sides signed by Jeffrey Lam — one control across the split"),
]


def build():
    rows = []
    for c in CHARTS:
        tr, price = c.get("transferred"), c.get("price")
        rows.append(dict(
            document_id=c["doc"], page=c["page"], chart_date=c["date"],
            chart_kind=c.get("kind", "MERGER"),
            bbl=c["bbl"], role=c["role"], direction=c["direction"],
            party=c.get("party"), lot_area=c.get("lot_area"), far=c.get("far"),
            generated=c.get("generated"), retained=c.get("retained"),
            transferred=tr, after_transfer=c.get("after"),
            counterparty_bbl=c.get("cp"), price=price,
            price_basis=c.get("pb"),
            per_sf=round(price / tr, 2) if (price and tr) else None,
            basis=c["basis"], note=c.get("note")))
    return rows


def check(rows):
    """generated = retained + transferred — but ONLY on a MERGER chart.

    ⚠ THIS CHECK FIRED ON THE 2019 CHART AND IT WAS THE CHECK THAT WAS WRONG.

    On a merger, a grantor keeps part of what its own land generates and sells
    the excess, so the three columns must close. On a SUBDIVISION they cannot:
    lot 49 generated 85,270 from its remaining land but handed lot 50 an
    envelope of 127,035 — MORE than it generates — because what moves is a share
    of the ASSEMBLED envelope, including rights bought from six other lots.

    So the two instruments are structurally different and a single invariant
    cannot cover both. `chart_kind` is not decoration; it selects the arithmetic.
    Had I silently relaxed the check to make it pass, the modelling error would
    have survived as a green tick.
    """
    bad = []
    for r in rows:
        if r["chart_kind"] != "MERGER":
            continue
        g, ret, tr = r["generated"], r["retained"], r["transferred"]
        if g and ret and tr and round(g) != round(ret + tr):
            bad.append((r["bbl"], g, ret, tr))
    return bad


def main():
    rows = build()
    bad = check(rows)

    print("ALLOCATION CHARTS — one row per LOT per CHART\n")
    hdr = f"{'chart':<11}{'lot':<5}{'dir':<7}{'land':>8}{'gen':>9}{'kept':>9}{'moved':>9}{'after':>9}  party"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        lot = r["bbl"][-3:].lstrip("0")
        f = lambda v: f"{v:,.0f}" if v else "—"
        print(f"{r['chart_date']:<11}{lot:<5}{r['direction']:<7}"
              f"{f(r['lot_area']):>8}{f(r['generated']):>9}{f(r['retained']):>9}"
              f"{f(r['transferred']):>9}{f(r['after_transfer']):>9}  "
              f"{(r['party'] or '')[:46]}")

    if bad:
        print("\n⚠ CHART DOES NOT BALANCE (generated != retained + transferred):")
        for b in bad:
            print(f"   lot {b[0]}: {b[1]:,.0f} != {b[2]:,.0f} + {b[3]:,.0f}")
    else:
        n = len([r for r in rows if r["generated"] and r["retained"] and r["transferred"]])
        print(f"\n  {n} grantor rows balance: generated = retained + transferred ✓")

    print("\nASSEMBLAGE PROGRESSION — the picture no single chart holds")
    prog = defaultdict(list)
    for r in rows:
        prog[(r["chart_date"], r["document_id"])].append(r)
    prev = None
    for (d, doc), rs in sorted(prog.items()):
        dev = [x for x in rs if x["role"] == "DEVELOPER" and x["bbl"] == DEV]
        env = dev[0]["after_transfer"] if dev else None
        delta = f"  {env - prev:+,.0f}" if (env and prev) else ""
        print(f"  {d}  {len(rs)} lots  developer envelope "
              f"{env:,.0f}{delta}" if env else f"  {d}  {len(rs)} lots")
        prev = env or prev

    print("\nWHO SOLD, AND WHAT THEY HAVE LEFT")
    sellers = defaultdict(lambda: [0, None, None, set()])
    for r in rows:
        if r["direction"] == "SOLD" and r["bbl"] != DEV:
            s = sellers[r["bbl"]]
            s[0] += r["transferred"] or 0
            s[1] = r["retained"]
            s[2] = r["party"]
            s[3].add(r["document_id"])
    for bbl in sorted(sellers):
        sold, kept, party, docs = sellers[bbl]
        k = f"{kept:,.0f} sf kept" if kept else "retained figure NOT TRANSCRIBED"
        print(f"  lot {bbl[-3:].lstrip('0'):<3} SOLD {sold:>7,.0f} sf · {k:<32} "
              f"{(party or '')[:42]}")
    print(f"\n  {len(sellers)} lots sold rights into this assemblage. Every one "
          f"is now development-dead,\n  and PLUTO still reports their unbuilt "
          f"FAR because it does not read these charts.")

    priced = [r for r in rows if r["per_sf"]]
    print("\nRATES, from the charts themselves")
    for r in sorted(priced, key=lambda x: x["chart_date"]):
        print(f"  {r['chart_date']}  lot {r['bbl'][-3:].lstrip('0'):<3} "
              f"{r['transferred']:>7,.0f} sf  ${r['price']:>10,.0f}  "
              f"${r['per_sf']:>7,.2f}/sf   {r['document_id']} {r['page']}")
    unp = [r for r in rows if r["direction"] == "SOLD" and r["bbl"] != DEV
           and not r["price"]]
    WHY = {"BUNDLED": "one price covers several lots on this instrument — a "
                      "per-lot rate would be an invention; the BUNDLE rate is "
                      "the valid comp",
           "OFF_PARCEL": "consideration recorded against the other parcel"}
    for r in unp:
        print(f"  {r['chart_date']}  lot {r['bbl'][-3:].lstrip('0'):<3} "
              f"{r['transferred']:>7,.0f} sf   NO PER-LOT RATE "
              f"({r['price_basis']}) — {WHY.get(r['price_basis'],'')}")
    b = [r for r in rows if r["price_basis"] == "BUNDLED"]
    if b:
        sf = sum(r["transferred"] for r in b)
        print(f"\n  BUNDLE 2010: {len(b)} lots, {sf:,.0f} sf for $5,000,000 = "
              f"${5_000_000/sf:,.2f}/sf — valid at the bundle, not per lot")

    p = HERE / "acris_rights_allocation.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\n  wrote {p.name} ({len(rows)} rows)")
    if bad:
        sys.exit(1)
    return rows


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL); sys.exit(0)
    main()
