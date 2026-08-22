"""THE SPINE SF LEDGER — every transfer written to BOTH lots, with what remains.

LOGIN, 2026-08-06:

    "When another lot is affected, it means you write it to that parcel in the
     spine as well. So say this lot RECEIVES sf — we record the received sf,
     from who, purchased for how much. But on the other lot it's SENT: how many
     sf, to who, for how much. And with sf particularly it's a good idea to
     include the adjustments — so what is RETAINED after the transactions."

THREE REQUIREMENTS, AND EACH FIXES A REAL DEFECT

  1 · MIRRORED. One transfer, two rows. Previously the 2010 ZLDA produced a
      +53,578 row on lot 49 and NOTHING on lots 53/55/56 — so querying lot 53
      returned an ordinary Chelsea lot with unused FAR. The document had been
      read; the finding was simply never written where anyone would look for it.

  2 · RETAINED, NOT JUST TRANSFERRED. "Lot 53 sold 23,864 sf" does not say what
      lot 53 has. It generated 40,770 and kept 16,906 — its existing building.
      The transferred figure alone cannot tell a buyer whether anything is left,
      and that is the only question they are asking.

  3 · PRICE ON BOTH SIDES. The buyer's cost is the seller's proceeds. Recording
      it once, on the buyer, means a seller-side comp search finds nothing —
      even though this is the better comp: it is what a co-op board actually
      accepted for its air.

⚠ THE SIGN CONVENTION IS LOAD-BEARING
    sf is signed from THE ROW'S OWN PARCEL's point of view: positive received,
    negative sent. So sum(sf) per bbl is that lot's net position and needs no
    case statement. A mirrored pair sums to zero across the two lots, which is
    the invariant check at the bottom — if a transfer does not net to zero, one
    side was mis-transcribed.

⚠ WHAT `retained` MEANS, PRECISELY
    Floor area the lot generates FROM ITS OWN LAND that it still holds. It does
    NOT include rights bought from elsewhere — those are `received_cum`. Lot 49
    in 2013 retained 156,390 (all its own) and had received 112,574 (bought), for
    an envelope of 268,964. Collapsing those into one number loses the ability
    to ask "how much of this envelope is portable?", which is exactly what the
    2019 subdivision turned on.
"""
import csv, pathlib, sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent

DDL = """
create table if not exists spine_sf_ledger (
  bbl            text not null,
  seq            int  not null,
  effective      date not null,
  direction      text not null,   -- OPENING | RECEIVED | SENT
  sf             numeric not null,-- SIGNED from this parcel's point of view
  counterparty_bbl text,
  counterparty   text,            -- who, by name, at the time
  price          numeric,         -- same figure on both sides of a pair
  per_sf         numeric,
  price_basis    text,            -- PER_LOT | BUNDLED | OFF_PARCEL | NONE
  generated_own  numeric,         -- what this lot's OWN land generates
  retained_own   numeric,         -- of that, what it still holds
  received_cum   numeric,         -- rights bought in from elsewhere
  envelope_after numeric,         -- retained_own + received_cum
  document_id    text not null,
  page           text,
  basis          text not null,   -- read | derived
  note           text,
  primary key (bbl, seq)
);
create index if not exists spine_sf_bbl on spine_sf_ledger(bbl, effective);
create index if not exists spine_sf_cp  on spine_sf_ledger(counterparty_bbl);

-- what any lot has LEFT — the question a summary of transfers cannot answer
create or replace view spine_sf_position as
select distinct on (bbl) bbl, effective as as_of,
       generated_own, retained_own, received_cum, envelope_after,
       (generated_own - retained_own) as sf_sold_away
from spine_sf_ledger order by bbl, effective desc, seq desc;

-- seller-side comps: what owners ACCEPTED for their air
create or replace view sf_sales_by_seller as
select bbl as seller_bbl, counterparty, effective, -sf as sf_sold,
       price, per_sf, price_basis, document_id, page
from spine_sf_ledger where direction = 'SENT' and price is not null
order by effective;
"""

DEV = "1008000049"

# ---------------------------------------------------------------------------
# TRANSFERS, chronological. Each one is declared ONCE and mirrored by code —
# writing both sides by hand is how the two drift apart.
#   from_/to_   the lots
#   gen/ret     the SELLER's own generation and what it keeps (from the chart)
# ---------------------------------------------------------------------------
TRANSFERS = [
 dict(eff="2010-10-14", frm="1008000053", to=DEV, sf=23_864,
      frm_party="120-22 W 25 Street LLC (Sabet Mgmt)", to_party="112-118 West 25th LLC (Extell)",
      gen=40_770, ret=16_906, price=None, pb="BUNDLED",
      doc="2010102601040006", page="p038", basis="read",
      note="120 W 25th. Price is the $5,000,000 bundle across lots 53/55/56"),
 dict(eff="2010-10-14", frm="1008000055", to=DEV, sf=15_070,
      frm_party="124-26 W 25 Street LLC (Sabet Mgmt)", to_party="112-118 West 25th LLC (Extell)",
      gen=24_690, ret=9_620, price=None, pb="BUNDLED",
      doc="2010102601040006", page="p038", basis="read", note="124 W 25th"),
 dict(eff="2010-10-14", frm="1008000056", to=DEV, sf=14_644,
      frm_party="124-26 W 25 Street LLC (Sabet Mgmt)", to_party="112-118 West 25th LLC (Extell)",
      gen=24_690, ret=10_046, price=None, pb="BUNDLED",
      doc="2010102601040006", page="p038", basis="read",
      note="126 W 25th — SAME OWNER as lot 55"),
 dict(eff="2012-12-19", frm="1008000023", to=DEV, sf=22_845,
      frm_party="The Horne Building Owners Corp (residential co-op)",
      to_party="112-118 West 25th LLC (Extell)",
      gen=57_250, ret=34_405, price=4_614_690, pb="PER_LOT",
      doc="2012122701550003", page="p043", basis="derived",
      note="127 W 24th, the through-block linchpin. $202.00/sf exact"),
 dict(eff="2013-05-17", frm="1008000022", to=DEV, sf=10_726,
      frm_party="Brick Farms Cooperative Ltd (c/o Forest City Ratner)",
      to_party="112-118 West 25th LLC (Extell)",
      gen=28_625, ret=17_899, price=1_450_000, pb="PER_LOT",
      doc="2013052101674004", page="p040", basis="read", note="131 W 24th"),
 dict(eff="2013-05-17", frm="1008000021", to=DEV, sf=10_722,
      frm_party="133 West 24th Street Corporation (co-op)",
      to_party="112-118 West 25th LLC (Extell)",
      gen=None, ret=None, price=1_340_250, pb="PER_LOT",
      doc="2013052101674008", page="p041", basis="read",
      note="⚠ generated/retained NOT TRANSCRIBED — the chart's own columns for "
           "lot 21 were not read, so what it has LEFT is unknown. Left null "
           "rather than back-computed"),
 dict(eff="2013-08-07", frm="1008000020", to=DEV, sf=14_703,
      frm_party="112-118 West 25th LLC (as airspace owner — SAME ENTITY)",
      to_party="112-118 West 25th LLC (as developer)",
      gen=None, ret=None, price=None, pb="OFF_PARCEL",
      doc="2013080901116002", page="p040", basis="read",
      note="135 W 24th airspace above elev. 130 ft. Self-dealt, zero tax; the "
           "consideration is recorded against lot 20"),
 dict(eff="2019-05-20", frm=DEV, to="1008000050", sf=127_035,
      frm_party="LAM GEN 25 LLC", to_party="LG CHELSEA LLC",
      gen=None, ret=None, price=None, pb="NONE",
      doc="2019071700601003", page="p044", basis="read",
      # ⚠ A SUBDIVISION MOVES LAND AND ACQUIRED RIGHTS TOGETHER, and the two
      # must be tracked apart. Recording only the 127,035 total produced a
      # NEGATIVE received_cum on lot 49 (112,574 - 127,035 = -14,461) and an
      # envelope of 198,155 on lot 50 — its own 71,120 counted twice, once as
      # an opening balance and again inside the transfer. Both totals looked
      # plausible; only the components exposed it.
      #   land_sf      7,112 sf of ground, generating 71,120 at FAR 10
      #   acquired_sf  55,915 of the rights lot 49 had bought from six lots
      #   71,120 + 55,915 = 127,035, and lot 49 keeps 85,270 + 56,659 = 141,929
      subdivision=True, land_sf=71_120, acquired_sf=55_915,
      note="THE SUBDIVISION — lot 49 is the SENDER. Lot 50 takes its own land "
           "(7,112 sf = 71,120 at FAR 10) plus 55,915 of acquired rights"),
]

# the developer's own generation, and the lots' opening positions
OPENING = {
 DEV:            dict(gen=156_390, eff="2010-10-14", doc="2010102601040006",
                      page="p038", note="15,639 sf of land at FAR 10.0"),
 # ⚠ lot 50 gets NO opening row. Its land arrives WITH the subdivision, so an
 # opening balance would count the same 71,120 twice — which is exactly what
 # the first run did, reporting a 198,155 envelope against the document's
 # 127,035.
}


def build():
    rows_by_bbl = defaultdict(list)

    # opening balances
    for bbl, o in OPENING.items():
        rows_by_bbl[bbl].append(dict(
            bbl=bbl, effective=o["eff"], direction="OPENING", sf=0,
            counterparty_bbl=None, counterparty=None, price=None, per_sf=None,
            price_basis=None, land_sf=None, acquired_sf=None,
            generated_own=o["gen"], retained_own=o["gen"],
            received_cum=0, envelope_after=o["gen"], document_id=o["doc"],
            page=o["page"], basis="derived", note=o["note"]))

    # every transfer, MIRRORED
    for t in TRANSFERS:
        sf, price = t["sf"], t.get("price")
        per = round(price / sf, 2) if price else None

        # ---- the RECEIVING side
        rows_by_bbl[t["to"]].append(dict(
            bbl=t["to"], effective=t["eff"], direction="RECEIVED", sf=+sf,
            counterparty_bbl=t["frm"], counterparty=t["frm_party"],
            price=price, per_sf=per, price_basis=t["pb"],
            generated_own=None, retained_own=None, received_cum=None,
            envelope_after=None, document_id=t["doc"], page=t["page"],
            basis=t["basis"], note=t.get("note"),
            land_sf=t.get("land_sf"), acquired_sf=t.get("acquired_sf")))

        # ---- the SENDING side, with what it KEEPS
        gen, ret = t.get("gen"), t.get("ret")
        rows_by_bbl[t["frm"]].append(dict(
            bbl=t["frm"], effective=t["eff"], direction="SENT", sf=-sf,
            counterparty_bbl=t["to"], counterparty=t["to_party"],
            price=price, per_sf=per, price_basis=t["pb"],
            generated_own=gen, retained_own=ret, received_cum=0,
            envelope_after=ret, document_id=t["doc"], page=t["page"],
            basis=t["basis"],
            land_sf=t.get("land_sf"), acquired_sf=t.get("acquired_sf"),
            note=(t.get("note") or "") +
                 ("" if ret is not None else
                  "  ⚠ RETAINED UNKNOWN — chart columns not transcribed")))

    # roll the developer / receiver balances forward
    out = []
    for bbl, rs in rows_by_bbl.items():
        rs.sort(key=lambda r: (r["effective"], r["direction"] != "OPENING"))
        gen = ret = recv = None
        for r in rs:
            if r["direction"] == "OPENING":
                gen, ret, recv = r["generated_own"], r["retained_own"], 0
                continue
            if r["direction"] == "RECEIVED":
                if gen is None:            # a lot that only ever received
                    gen = ret = 0; recv = 0
                if r.get("land_sf"):       # created by a subdivision
                    gen += r["land_sf"]; ret += r["land_sf"]
                    recv += r.get("acquired_sf") or 0
                    r["generated_own"], r["retained_own"] = gen, ret
                    r["received_cum"] = recv
                    r["envelope_after"] = ret + recv
                    continue
                recv += r["sf"]
                r["generated_own"], r["retained_own"] = gen, ret
                r["received_cum"] = recv
                r["envelope_after"] = ret + recv
            else:                          # SENT
                if gen is not None and r["generated_own"] is None:
                    # the subdivision case: land AND acquired rights both move
                    gen -= r.get("land_sf") or 0
                    ret -= r.get("land_sf") or 0
                    recv -= r.get("acquired_sf") or 0
                    r["generated_own"] = gen
                    r["retained_own"] = ret
                    r["received_cum"] = recv
                    r["envelope_after"] = ret + recv
        out.extend(rs)

    out.sort(key=lambda r: (r["effective"], r["bbl"], r["direction"]))
    for i, r in enumerate(out, 1):
        r["seq"] = i
    return out


def check_mirrors(rows):
    """Every transfer must net to zero across its two lots."""
    pairs = defaultdict(float)
    for r in rows:
        if r["direction"] in ("RECEIVED", "SENT"):
            key = (r["effective"], r["document_id"],
                   tuple(sorted([r["bbl"], r["counterparty_bbl"] or ""])))
            pairs[key] += r["sf"]
    return [(k, v) for k, v in pairs.items() if round(v, 2) != 0]


def main():
    rows = build()
    bad = check_mirrors(rows)

    print("SPINE SF LEDGER — every transfer on BOTH lots, chronological\n")
    hdr = (f"{'date':<12}{'lot':<5}{'dir':<10}{'sf':>10}{'$/sf':>9}"
           f"{'gen':>9}{'kept':>9}{'recvd':>9}{'envelope':>10}  cite")
    print(hdr); print("-" * len(hdr))
    for r in rows:
        f = lambda v: f"{v:,.0f}" if v is not None else "—"
        ps = f"${r['per_sf']:,.2f}" if r["per_sf"] else "—"
        lot = r["bbl"][-3:].lstrip("0")
        print(f"{r['effective']:<12}{lot:<5}{r['direction']:<10}"
              f"{r['sf']:>+10,.0f}{ps:>9}{f(r['generated_own']):>9}"
              f"{f(r['retained_own']):>9}{f(r['received_cum']):>9}"
              f"{f(r['envelope_after']):>10}  {r['document_id']} {r['page']}")

    if bad:
        print("\n⚠ MIRROR BROKEN — a transfer does not net to zero:")
        for k, v in bad:
            print(f"   {k}  net {v:+,.0f}")
    else:
        n = len({(r['effective'], r['document_id']) for r in rows
                 if r['direction'] != 'OPENING'})
        print(f"\n  every transfer nets to zero across its two lots ✓ "
              f"({n} transfer events)")

    print("\nWHAT EACH LOT HAS LEFT — the position query")
    pos = {}
    for r in rows:
        pos[r["bbl"]] = r
    for bbl in sorted(pos):
        r = pos[bbl]
        lot = bbl[-3:].lstrip("0")
        if r["retained_own"] is None:
            print(f"  lot {lot:<3} ⚠ RETAINED UNKNOWN — sold "
                  f"{abs(r['sf']):,.0f} sf, chart columns not transcribed")
        else:
            sold = (r["generated_own"] or 0) - (r["retained_own"] or 0)
            print(f"  lot {lot:<3} generates {r['generated_own'] or 0:>8,.0f} · "
                  f"sold {sold:>8,.0f} · KEEPS {r['retained_own']:>8,.0f} · "
                  f"envelope {r['envelope_after'] or 0:>8,.0f}")

    print("\nSELLER-SIDE COMPS — what owners ACCEPTED for their air")
    for r in sorted([x for x in rows if x["direction"] == "SENT" and x["price"]],
                    key=lambda x: x["effective"]):
        print(f"  {r['effective']}  lot {r['bbl'][-3:].lstrip('0'):<3} sold "
              f"{abs(r['sf']):>7,.0f} sf for ${r['price']:>10,.0f} "
              f"= ${r['per_sf']:>7,.2f}/sf   to {r['counterparty'][:34]}")
    unp = [x for x in rows if x["direction"] == "SENT" and not x["price"]]
    for r in unp:
        print(f"  {r['effective']}  lot {r['bbl'][-3:].lstrip('0'):<3} sold "
              f"{abs(r['sf']):>7,.0f} sf   NO PRICE ON THIS SIDE "
              f"({r['price_basis']})")

    p = HERE / "spine_sf_ledger.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\n  wrote {p.name} ({len(rows)} rows across "
          f"{len({r['bbl'] for r in rows})} parcels)")
    if bad:
        sys.exit(1)
    return rows


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL); sys.exit(0)
    main()
