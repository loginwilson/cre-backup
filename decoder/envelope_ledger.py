"""The ENVELOPE ledger — every square foot in or out, cited to document and page.

LOGIN, 2026-08-06, and this is the module's whole reason for existing:

    "All documents that would encumber or affect the zoning envelope could be
     organized to create a fuller picture beyond zoning resolution. I could cite
     the doc # page # and say + # of sf from -. Essentially I'd be able to build
     a ledger of how sf has been transferred and the rates. But also an
     easement, knowing the details could tell me the severity of if it takes a
     site off the table for development or if it's just minor."

    Two different questions, and they need two different tables:

      1. HOW MUCH CAN BE BUILT — an accounting ledger. Every movement signed
         (+/-), sourced, priced, and running to a balance that must close.
      2. WHAT IS IN THE WAY — a burden register, graded by SEVERITY, because
         "there is an easement" is useless and "this lot can never be developed"
         is a deal.

WHY THE LEDGER FORM, NOT A CURRENT-STATE FIELD

    A single `buildable_sf` column answers today's question and destroys the
    interesting one. This parcel's envelope moved SIX times across nine years at
    prices from $93 to $202 a foot. The movements ARE the market data; a current
    balance throws away every comparable that produced it.

    The ledger also self-checks in a way a state field cannot: the movements must
    sum to the balance the documents state independently. On lot 49 they do,
    to the square foot, across six transfers and a subdivision — see verify().

⚠ THE FINDING THIS TABLE MAKES VISIBLE, WHICH NOTHING ELSE DOES

    Six lots on Manhattan Block 800 sold their development rights to lot 49.
    Those lots are now DEVELOPMENT-DEAD — a buyer gets the building and no
    envelope. PLUTO will still cheerfully report their unbuilt FAR, because
    PLUTO does not read ZLDAs. The only record that a site is off the table is
    the declaration recorded against it, and on this block three of those were
    indexed as "SMIS - miscellaneous".
"""
import csv, json, pathlib, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
BBL = "1008000049"

DDL = """
-- every square foot in or out, signed and cited -----------------------------
create table if not exists acris_envelope_ledger (
  bbl           text not null,
  seq           int  not null,
  happened      date not null,
  direction     text not null,          -- opening | in | out
  sf            numeric not null,       -- signed: positive in, negative out
  counterparty_bbl text,                -- the lot it came from / went to
  counterparty     text,
  price         numeric,                -- NULL when not priced on THIS parcel
  per_sf        numeric,
  balance_after numeric not null,       -- must equal the document's own figure
  document_id   text,
  page          text,
  basis         text not null,          -- read | derived | index
  note          text,
  primary key (bbl, seq)
);

-- what is in the way, and how badly ------------------------------------------
create table if not exists acris_encumbrances (
  burdened_bbl  text not null,
  seq           int  not null,
  benefited_bbl text,
  happened      date,
  kind          text not null,          -- RIGHTS_TRANSFERRED | LIGHT_AIR |
                                        -- UNIT_CAP | ZONING_LOT_MERGER
  severity      text not null,          -- FATAL | MAJOR | MINOR | BENEFIT
  sf_removed    numeric,
  detail        text not null,
  document_id   text,
  page          text,
  basis         text not null,
  primary key (burdened_bbl, seq)
);

-- SEVERITY, defined once so it means the same thing on every parcel:
--   FATAL    the site cannot be developed as of right — its rights are gone,
--            or a recorded restriction caps it below any viable program
--   MAJOR    development is materially constrained but possible — a light and
--            air easement over the buildable area, a height plane, a unit cap
--            that still permits a real building
--   MINOR    administrative; does not change what can be built
--   BENEFIT  this parcel is the BENEFICIARY, not the burdened party
--
-- ⚠ FATAL vs MAJOR is the only distinction a broker acts on, so it is graded
-- from the instrument's own words and cited. It is never inferred from a
-- document TYPE — on this block "SMIS" hid three declarations, one of which
-- ends the development future of two lots.

create or replace view block_development_status as
select burdened_bbl as bbl,
       min(severity) filter (where severity = 'FATAL') as fatal,
       count(*) filter (where severity = 'FATAL')  as fatal_burdens,
       count(*) filter (where severity = 'MAJOR')  as major_burdens,
       sum(sf_removed)                             as sf_stripped,
       string_agg(distinct document_id, ', ')      as evidence
from acris_encumbrances group by burdened_bbl;
"""

# ---------------------------------------------------------------------------
# LOT 49's ENVELOPE, one row per movement.
#
# `balance_after` is NOT computed by this file — it is TRANSCRIBED from the
# "developer after transfer" line of each document's own Exhibit D. verify()
# then checks that the movements sum to it. Two independent sources; if they
# disagree the decode is wrong and it says so instead of quietly recomputing.
# ---------------------------------------------------------------------------
LEDGER = [
 dict(seq=1, happened="1971-10-04", direction="opening", sf=156_390,
      balance_after=156_390, document_id="2010102601040006", page="p038",
      basis="derived",
      note="Self-generated: 15,639 sf of land at the FAR 10.0 implied by the "
           "2010 chart. NOT read from a 1971 document — zoning did not work "
           "this way in 1971. It is the baseline the later charts imply, and "
           "is marked derived for that reason."),
 dict(seq=2, happened="2010-10-14", direction="in", sf=53_578,
      counterparty_bbl="1008000053,55,56", counterparty="Sabetfard entities",
      price=5_000_000, balance_after=209_968,
      document_id="2010102601040006", page="p038", basis="read",
      note="Three lots on W 25th. Price recovered from cover-page tax stamps; "
           "ACRIS indexes this DEVR at $0."),
 dict(seq=3, happened="2012-12-19", direction="in", sf=22_845,
      counterparty_bbl="1008000023", counterparty="The Horne Building Owners Corp",
      price=4_614_690, balance_after=232_813,
      document_id="2012122701550003", page="p043", basis="derived",
      note="THE QUANTITY IS STATED NOWHERE. Derived by differencing this "
           "chart's developer allocation against the 2010 chart's "
           "(209,968 -> 232,813). $202.00/sf exact to the cent — the tell that "
           "the parties negotiated per foot. Through-block linchpin."),
 dict(seq=4, happened="2013-05-17", direction="in", sf=10_726,
      counterparty_bbl="1008000022", counterparty="Brick Farms Cooperative Ltd",
      price=1_450_000, balance_after=243_539,
      document_id="2013052101674004", page="p040", basis="read",
      note="Chart states lot 22 generated 28,625, retained 17,899, excess "
           "10,726. Exhibit D is a landscape scan."),
 dict(seq=5, happened="2013-05-17", direction="in", sf=10_722,
      counterparty_bbl="1008000021", counterparty="133 West 24th Street Corp",
      price=1_340_250, balance_after=254_261,
      document_id="2013052101674008", page="p041", basis="read",
      note="$125.00/sf exact."),
 dict(seq=6, happened="2013-08-07", direction="in", sf=14_703,
      counterparty_bbl="1008000020", counterparty="112-118 West 25th LLC (itself)",
      price=None, balance_after=268_964,
      document_id="2013080901116002", page="p040", basis="read",
      note="⚠ PRICE UNKNOWN ON THIS PARCEL. Airspace above lot 20 over "
           "elevation 130 ft, transferred by one entity acting in two "
           "capacities. Zero tax because there are not two parties, so no "
           "stamp to reverse — the consideration was recorded against LOT 20. "
           "This is why per_sf is NULL and not zero."),
 dict(seq=7, happened="2019-05-20", direction="out", sf=-127_035,
      counterparty_bbl="1008000050", counterparty="LG Chelsea LLC (the new lot 50)",
      price=None, balance_after=141_929,
      document_id="2019071700601003", page="p044", basis="read",
      note="The subdivision. Lot 50 takes its OWN land (7,112 sf = 71,120 at "
           "FAR 10) PLUS 55,915 of acquired rights = 127,035 total envelope. "
           "Lot 49 keeps 8,527 sf of land (85,270) plus 56,659 acquired = "
           "141,929. No money: same sponsor both sides.\n"
           "⚠ FIRST WRITTEN AS -55,915 AND THE CHECK CAUGHT IT. That figure is "
           "lot 50's share of the ACQUIRED rights, which is the number Exhibit "
           "D's allocation column shows and the one a reader naturally lifts. "
           "The ENVELOPE leaving lot 49 is the whole 127,035 — the acquired "
           "share plus the land-generated rights that go with the ground. "
           "Off by exactly 71,120 = 7,112 x 10. **A subdivision moves land and "
           "rights together; reading only the rights column understates the "
           "loss by the entire self-generated envelope.**"),
]

# ---------------------------------------------------------------------------
# WHAT IS IN THE WAY — and, more usefully, what lot 49's purchases did TO THE
# NEIGHBOURS. A broker working this block needs to know which doors are shut.
# ---------------------------------------------------------------------------
BURDENS = [
 dict(burdened="1008000053", seq=1, benefited=BBL, happened="2010-10-14",
      kind="RIGHTS_TRANSFERRED", severity="FATAL", sf_removed=23_864,
      document_id="2010102601040006", page="p038", basis="read",
      detail="120 W 25th. Excess development rights transferred to lot 49 and "
             "merged into its zoning lot. Retains 16,906 sf — its existing "
             "building. AS-OF-RIGHT DEVELOPMENT IS OVER for this lot."),
 dict(burdened="1008000055", seq=1, benefited=BBL, happened="2010-10-14",
      kind="RIGHTS_TRANSFERRED", severity="FATAL", sf_removed=15_070,
      document_id="2010102601040006", page="p038", basis="read",
      detail="124 W 25th. Retains 9,620 sf. Rights gone."),
 dict(burdened="1008000056", seq=1, benefited=BBL, happened="2010-10-14",
      kind="RIGHTS_TRANSFERRED", severity="FATAL", sf_removed=14_644,
      document_id="2010102601040006", page="p038", basis="read",
      detail="126 W 25th. Retains 10,046 sf. Rights gone."),
 dict(burdened="1008000023", seq=1, benefited=BBL, happened="2012-12-19",
      kind="RIGHTS_TRANSFERRED", severity="FATAL", sf_removed=22_845,
      document_id="2012122701550003", page="p043", basis="derived",
      detail="127 W 24th, the Horne co-op. A RESIDENTIAL CO-OP BOARD sold its "
             "air for $4.6M. The shareholders keep their apartments; the site "
             "will never be redeveloped at scale."),
 dict(burdened="1008000022", seq=1, benefited=BBL, happened="2013-05-17",
      kind="RIGHTS_TRANSFERRED", severity="FATAL", sf_removed=10_726,
      document_id="2013052101674004", page="p040", basis="read",
      detail="131 W 24th, Brick Farms co-op c/o Forest City Ratner."),
 dict(burdened="1008000022", seq=2, benefited=BBL, happened="2013-05-17",
      kind="LIGHT_AIR", severity="MAJOR", sf_removed=None,
      document_id="2013052101674004", page="p042", basis="read",
      detail="Light-and-air easement over ALL of lot 22 above elevation 130 ft "
             "(2.75 ft above NGVD 1929 datum). Nothing may ever rise above that "
             "plane. Compounds the rights transfer: even reacquired FAR could "
             "not be built vertically here."),
 dict(burdened="1008000021", seq=1, benefited=BBL, happened="2013-05-17",
      kind="RIGHTS_TRANSFERRED", severity="FATAL", sf_removed=10_722,
      document_id="2013052101674008", page="p041", basis="read",
      detail="133 W 24th co-op."),
 dict(burdened="1008000021", seq=2, benefited=BBL, happened="2013-05-17",
      kind="UNIT_CAP", severity="MAJOR", sf_removed=None,
      document_id="2013052101674008", page="p041", basis="read",
      detail="CAPPED AT SEVEN DWELLING UNITS in perpetuity by the agreement. "
             "A recorded restriction on the seller's own future, independent of "
             "the rights transfer."),
 dict(burdened="1008000020", seq=1, benefited=BBL, happened="2013-08-07",
      kind="RIGHTS_TRANSFERRED", severity="FATAL", sf_removed=14_703,
      document_id="2013080901116002", page="p040", basis="read",
      detail="135 W 24th. Airspace above elevation 130 ft. ⚠ The earliest "
             "instrument in this whole assemblage is a lot 20 ZLDA recorded "
             "2008-02-26, CRFN 2008000078652 — TWO YEARS before Sabetfard, "
             "indexed only against lot 20 and invisible from lot 49."),
 dict(burdened=BBL, seq=1, benefited=None, happened="2013-08-07",
      kind="ZONING_LOT_MERGER", severity="MINOR", sf_removed=None,
      document_id="2013080901116001", page="p003", basis="read",
      detail="Declaration of Zoning Lot Restrictions over all EIGHT lots with a "
             "single declarant. Lot 49 cannot be zoned independently of the "
             "other seven — administrative for the developer, but it is the "
             "instrument that makes the assemblage real. ⚠ INDEXED AS 'SMIS'."),
 dict(burdened=BBL, seq=2, benefited=BBL, happened="2010-10-14",
      kind="LIGHT_AIR", severity="BENEFIT", sf_removed=None,
      document_id="2010102601040006", page="p038", basis="read",
      detail="Lot 49 is the BENEFICIARY of a light-and-air easement 20 ft deep "
             "starting 23 ft above curb across the Sabetfard lots. Recorded "
             "here so the register never reads as if lot 49 were burdened."),
]


def verify(rows):
    """The movements must sum to each document's own stated balance.

    ⚠ balance_after is TRANSCRIBED, not computed. If this check ever passes
    trivially, someone has made it compute the thing it is meant to test.
    """
    run, bad = 0, []
    for r in rows:
        run += r["sf"]
        if round(run) != round(r["balance_after"]):
            bad.append((r["seq"], run, r["balance_after"]))
    return run, bad


def main():
    rows = []
    for r in LEDGER:
        sf, price = r["sf"], r.get("price")
        rows.append({
            "bbl": BBL, "seq": r["seq"], "happened": r["happened"],
            "direction": r["direction"], "sf": sf,
            "counterparty_bbl": r.get("counterparty_bbl"),
            "counterparty": r.get("counterparty"), "price": price,
            "per_sf": round(price / abs(sf), 2) if price else None,
            "balance_after": r["balance_after"],
            "document_id": r.get("document_id"), "page": r.get("page"),
            "basis": r["basis"], "note": r.get("note"),
        })
    total, bad = verify(rows)
    print(f"ENVELOPE LEDGER · {BBL}")
    print(f"{'date':<12}{'dir':<8}{'sf':>10}  {'$/sf':>9}  {'balance':>10}  cite")
    for r in rows:
        ps = f"${r['per_sf']:,.2f}" if r["per_sf"] else ("—" if r["direction"] != "opening" else "")
        cite = f"{r['document_id']} {r['page']}" if r["document_id"] else ""
        print(f"{r['happened']:<12}{r['direction']:<8}{r['sf']:>+10,.0f}  {ps:>9}  "
              f"{r['balance_after']:>10,.0f}  {cite}")
    if bad:
        print("\n⚠ LEDGER DOES NOT CLOSE — movements disagree with the documents:")
        for s, got, want in bad:
            print(f"   seq {s}: movements give {got:,.0f}, document states {want:,.0f}")
        sys.exit(1)
    print(f"\n  closes to {total:,.0f} sf — every stated balance reproduced ✓")

    bought = [r for r in rows if r["direction"] == "in" and r["price"]]
    sf_b = sum(r["sf"] for r in bought)
    sp = sum(r["price"] for r in bought)
    unpriced = [r for r in rows if r["direction"] == "in" and not r["price"]]
    print(f"  PRICED acquisitions: {sf_b:,.0f} sf for ${sp:,.0f} = ${sp/sf_b:,.2f}/sf")
    for u in unpriced:
        print(f"  ⚠ UNPRICED: {u['sf']:,.0f} sf from {u['counterparty_bbl']} — "
              f"consideration recorded on the OTHER parcel, so $/sf here would "
              f"be a fabrication")

    brows = []
    for b in BURDENS:
        brows.append({"burdened_bbl": b["burdened"], "seq": b["seq"],
                      "benefited_bbl": b.get("benefited"),
                      "happened": b.get("happened"), "kind": b["kind"],
                      "severity": b["severity"], "sf_removed": b.get("sf_removed"),
                      "detail": b["detail"], "document_id": b.get("document_id"),
                      "page": b.get("page"), "basis": b["basis"]})

    print(f"\nBLOCK 800 DEVELOPMENT STATUS — what lot 49's assemblage did to its neighbours")
    dead = {}
    for b in brows:
        if b["severity"] == "FATAL":
            dead.setdefault(b["burdened_bbl"], []).append(b)
    for bbl in sorted(dead):
        sf = sum(x["sf_removed"] or 0 for x in dead[bbl])
        extra = [x for x in brows if x["burdened_bbl"] == bbl and x["severity"] == "MAJOR"]
        tag = "  + " + ", ".join(x["kind"] for x in extra) if extra else ""
        print(f"  {bbl}  lot {bbl[-3:].lstrip('0'):<3} DEVELOPMENT-DEAD  "
              f"-{sf:,.0f} sf{tag}")
    print(f"\n  ⚠ {len(dead)} lots on this block cannot be developed as of right.")
    print("    PLUTO still reports their unbuilt FAR — it does not read ZLDAs.")
    print("    The only record is a declaration against each lot, and THREE of")
    print("    those were indexed as 'SMIS - miscellaneous'.")

    for name, data in (("acris_envelope_ledger", rows),
                       ("acris_encumbrances", brows)):
        p = HERE / f"{name}_{BBL}.csv"
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)
        print(f"\n  wrote {p.name} ({len(data)} rows)")
    return rows, brows


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL)
        sys.exit(0)
    r, b = main()
    if "--push" in sys.argv:
        sys.path.insert(0, str(HERE))
        import supabase_sync as S
        for t, rows, k in (("acris_envelope_ledger", r, "bbl,seq"),
                           ("acris_encumbrances", b, "burdened_bbl,seq")):
            try:
                S._post(t, rows, k)
                print(f"  {t:<24} {len(rows)} rows pushed")
            except Exception as ex:
                m = str(ex)
                print(f"  {t:<24} " + ("TABLE MISSING — run the DDL"
                      if ("PGRST205" in m or "404" in m) else f"FAILED {m[:120]}"))
