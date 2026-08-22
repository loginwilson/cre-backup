"""CONSTRAINTS and SIGNALS — the two layers above the claim.

LOGIN, 2026-08-06:

    "The interplay is the important part, and it isn't always about SF. Being
     told you can't build above a certain height, or units, or you have to give
     access — all these things are crucial. Knowing how debt is formed and the
     way things actually unfold relative to a project, and where the owner's
     financing choices indicate for the project. Knowing the conveyances and
     what they MEAN in the context of a site."

TWO LAYERS, AND THEY MUST NOT BE ONE TABLE

    A CONSTRAINT is still a fact — the document says a thing may not exceed a
    limit. It has a dimension, a magnitude, a datum, a beneficiary and a
    burdened party. Floor area is ONE dimension among five, and treating the
    envelope as an SF number alone loses the four that can kill a project
    without touching FAR at all.

    A SIGNAL is an INTERPRETATION — what a fact implies about the project. It is
    not in any document. It is a rule applied to a claim, and the rule must be
    written down beside the conclusion or the conclusion cannot be audited,
    argued with, or corrected when it turns out to be wrong.

⚠ WHY SIGNALS CARRY THEIR RULE

    "MetLife took this out in 2023, therefore the asset is stabilised" is a
    useful read and an unfalsifiable one unless the rule is stated: LIFE
    INSURANCE COMPANIES LEND ON STABILISED CASH FLOW, NOT ON CONSTRUCTION. With
    the rule visible, a reader can disagree with the rule rather than with the
    conclusion — and can notice when a case breaks it. Without it, an inference
    hardens into a fact by repetition, which is how "DEVR always shows $0"
    became a rule from a single document.

THE FINANCING NARRATIVE THIS MAKES READABLE

    The lender's IDENTITY tracks the project phase more reliably than any
    filing does:

    ⚠ THE VERSION BELOW WAS WRONG IN FOUR PLACES. Corrected 2026-08-06 from
    Exhibit A of the 2014 assignment (2014112601161003 pp006-008), which sets
    out seventeen instruments from 1990 to 2014.

        1990  APPLE BANK FOR SAVINGS        a family holding an old building
        1999  Queens County Savings Bank    by assignment from Apple Bank
        2007  ANGLO IRISH BANK              a developer buying
        2011  IRISH BANK RESOLUTION CORP    ⚠ nationalised; loan book liquidated
              -> LSREF2 CLOVER TRUST (Lone Star) -> Wells Fargo -> Clover again
        2012  UBS REAL ESTATE SECURITIES    distressed paper finds a buyer
        2013  GOLDMAN SACHS                 transitional / pre-development
        2014  SHANGHAI COMMERCIAL BANK      ⚠ arrives HERE, not 2020. It funds
              the Land Loan, then the 2015 Building and Project Loans, then the
              2020 Bridge Loan - one relationship, nine years, four facilities
        2023  METROPOLITAN LIFE             stabilised, permanent

    What the corrected arc shows that the wrong one hid: SIX HOLDERS IN SEVEN
    YEARS between 2007 and 2014, driven by the Irish banking collapse. A parcel
    whose ledger reads "servicing - no money moves" through 2011 and 2012 was
    in fact sitting inside a liquidating loan book the whole time.

    Nothing states that arc. Every step of it is a claim plus a rule.
"""
import csv, pathlib, sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent

DDL = """
-- CONSTRAINTS — a limit is not always square feet -----------------------------
create table if not exists acris_constraints (
  burdened_bbl text not null,
  seq          int  not null,
  dimension    text not null,   -- FLOOR_AREA | HEIGHT | UNITS | ACCESS | USE
  limit_value  numeric,         -- the scalar, where one is meaningful
  limit_unit   text,            -- sf | ft_elevation | dwelling_units | boolean
  -- ⚠ A CONSTRAINT IS A VOLUME, NOT A SCALAR. See DECODE_EXACTNESS.md.
  -- The first version stored the 2010 easement as limit_value=23 with "20 ft
  -- deep from the lot line" written into `datum` as PROSE. The horizontal
  -- dimension was therefore unqueryable, and a whole-lot height plane (lot 22)
  -- and a 20-ft band (lots 53/55/56) were stored identically. The field read
  -- correctly and stored wrongly — the hardest failure to notice.
  vertical_from    numeric,     -- lower bound of the burdened volume
  vertical_to      numeric,     -- null = unlimited above
  -- ⚠ A CONSTRAINT CAN BE VARIABLE, and the schema assumed it never was.
  -- Found 2026-08-06 in the 2012 Horne ZLDA: the burdened owner may RAISE the
  -- 155.24 ft plane whenever it acquires bonus or upzoning rights and uses them
  -- to add floor area, on 15 business days' notice with drawings. The easement
  -- is then "deemed raised to the minimum height that would permit such
  -- Alterations".
  --
  -- Stored as a fixed number with duration=PERPETUAL, that reads as a permanent
  -- ceiling at 155.24 ft. It is a FLOOR that can rise. Anyone valuing lot 23 on
  -- the fixed reading is wrong the moment the owner exercises the increase —
  -- and the increase needs no consent from the benefited party.
  is_variable      bool default false,
  variable_by      text,        -- who can move it, and on what trigger
  variable_notice  text,        -- what they must give first
  variable_floor   numeric,     -- the value below which it cannot go
  vertical_datum   text,        -- curb level | Manhattan Topo Bureau datum | ...
  horizontal_scope text,        -- WHOLE_LOT | BAND | PORTION
  horizontal_extent numeric,    -- depth of the band, in feet
  horizontal_from  text,        -- the line it is measured from
  duration     text,            -- PERPETUAL | TERM | DURING_CONSTRUCTION
  benefited_bbl text,
  severity     text not null,   -- FATAL | MAJOR | MINOR | BENEFIT
  document_id  text not null,
  page         text,
  effective    date,
  basis        text not null,   -- read | derived
  detail       text not null,
  primary key (burdened_bbl, seq)
);
create index if not exists acris_constraints_dim on acris_constraints(dimension);

-- ⚠ FIVE DIMENSIONS, and only the first is square feet:
--   FLOOR_AREA  rights transferred away; the lot cannot build what it generated
--   HEIGHT      an elevation plane nothing may cross, regardless of unused FAR
--   UNITS       a dwelling-unit cap, which can bind long before FAR does
--   ACCESS      a right of passage, staging, or parking lane the owner must give
--   USE         a restrictive covenant on what may operate there
--
-- A site with unused FAR and a height plane at 130 ft is not a development
-- site. Only recording FLOOR_AREA would report it as one.

-- SIGNALS — interpretation, kept separate from fact ---------------------------
create table if not exists acris_signals (
  bbl         text not null,
  seq         int  not null,
  effective   date not null,
  signal      text not null,   -- the reading
  category    text not null,   -- PHASE | INTENT | RISK | MARKET
  rule        text not null,   -- ⚠ THE RULE APPLIED. Never null.
  confidence  text not null,   -- high | medium | low
  from_claims text[] not null, -- the claim_ids this rests on
  counter     text,            -- what would falsify it
  primary key (bbl, seq)
);
create index if not exists acris_signals_cat on acris_signals(category, effective);

create or replace view site_constraints as
select burdened_bbl as bbl, dimension, limit_value, limit_unit, datum,
       severity, document_id, page, detail
from acris_constraints order by burdened_bbl, severity, dimension;
"""

L49 = "1008000049"

CONSTRAINTS = [
 # ---- HEIGHT — invisible to any FAR calculation ------------------------
 dict(bbl="1008000022", seq=1, dim="HEIGHT", val=130, unit="ft_elevation",
      vfrom=130, vto=None,
      vdatum="Manhattan Highways/Topographic Bureau datum, itself 2.75 ft above "
             "NGVD 1929 mean sea level at Sandy Hook",
      hscope="WHOLE_LOT", hextent=None, hfrom="the entire lot 22 parcel",
      dur="PERPETUAL",
      # lot 22's plane: no raise mechanism found in the body as read so far
      variable=False,
      ben=L49, sev="MAJOR", doc="2013052101674004", page="p042",
      eff="2013-05-17", basis="read",
      detail="Light and air easement over the WHOLE of lot 22 (25 x 114'6\"). "
             "Nothing may ever cross that plane. ⚠ THIS BINDS INDEPENDENTLY OF "
             "FLOOR AREA — if lot 22 reacquired FAR tomorrow it still could not "
             "build above 130 ft"),
 dict(bbl="1008000020", seq=1, dim="HEIGHT", val=130, unit="ft_elevation",
      vfrom=130, vto=None, vdatum="same Manhattan Topo Bureau datum",
      hscope="WHOLE_LOT", hextent=None, hfrom="the entire lot 20 parcel",
      dur="PERPETUAL", ben=L49, sev="MAJOR",
      doc="2013080901116002", page="p040", eff="2013-08-07", basis="read",
      detail="The airspace ABOVE elev. 130 ft was severed and conveyed. Lot 20 "
             "owns the ground and 130 vertical feet; the volume above belongs "
             "to lot 49's zoning lot"),
 # ⚠ CORRECTED 2026-08-06 by reading §II.A.2 at p008. THREE errors in the
 # original row, all from decoding the Exhibit D CHART and never the covenants:
 #   (a) "light and air"        -> the grant is LIGHT, AIR AND VIEW
 #   (b) "from the lot line shared with lot 49" -> from the REAR LOT LINE,
 #       extending 20 ft NORTH. On a through-block assemblage those are
 #       different lines, so the burdened band was in the wrong place.
 #   (c) "applies to lots 53, 55 and 56 alike" -> ⚠ FALSE. The clause reads
 #       "120 Owner hereby grants", i.e. LOT 53 ONLY. Lots 55 and 56 sold
 #       development rights and granted NO easement. Their height constraint
 #       was INVENTED BY ME and is retracted below — the worst of the three,
 #       because it made two neighbours look more encumbered than they are.
 # ⚠ THE VARIABLE ONE. Recorded 2026-08-06 from the Horne ZLDA body.
 dict(bbl="1008000023", seq=2, dim="HEIGHT", val=155.24, unit="ft_elevation",
      vfrom=155.24, vto=None,
      vdatum="Manhattan Topographic Bureau datum, 2.75 ft above USC&GS mean "
             "sea level at Sandy Hook",
      hscope="WHOLE_LOT", hextent=None,
      hfrom="the whole 25 ft x 114 ft 6 in lot 23 parcel",
      dur="PERPETUAL",
      variable=True,
      var_by="lot 23's own owner, without lot 49's consent, whenever it "
             "acquires Owner Bonus or Owner Upzoning Development Rights and "
             "uses them to add floor area",
      var_notice="15 business days' prior notice with architectural drawings "
                 "and the proposed new height; the easement is then deemed "
                 "raised to the MINIMUM height permitting the work",
      var_floor=155.24,
      ben=L49, sev="MAJOR", doc="2012122701550003", page="p008",
      eff="2012-12-19", basis="read",
      detail="Perpetual light, air AND VIEW easement above a horizontal plane "
             "at 155.24 ft. ⚠ NOT A CEILING — A FLOOR THAT CAN RISE. Treating "
             "155.24 as permanent overstates lot 23's burden and understates "
             "its remaining potential"),
 dict(bbl="1008000053", seq=2, dim="HEIGHT", val=23, unit="ft_elevation",
      vfrom=23, vto=None, vdatum="curb level (as defined in the Zoning Resolution)",
      hscope="BAND", hextent=20,
      hfrom="the REAR LOT LINE of the 120 Owner Land, extending 20 ft NORTH",
      dur="PERPETUAL",
      ben=L49, sev="MAJOR", doc="2010102601040006", page="p008",
      eff="2010-10-14", basis="read",
      detail="Perpetual easement for LIGHT, AIR AND VIEW granted by the 120 "
             "Owner (lot 53) ALONE. Carve-out: the existing 120 Owner Building "
             "may remain in the easement area as it stood at the date of the "
             "agreement"),

 # ---- UNITS — binds long before FAR does -------------------------------
 dict(bbl="1008000021", seq=1, dim="UNITS", val=7, unit="dwelling_units",
      vfrom=None, vto=None, vdatum=None, hscope="WHOLE_LOT", hextent=None,
      hfrom="the whole of lot 21", dur="PERPETUAL", ben=L49, sev="MAJOR",
      doc="2013052101674008", page="p041", eff="2013-05-17", basis="read",
      detail="Capped at SEVEN dwelling units for ever. A 25-ft lot in Chelsea "
             "would otherwise support far more. ⚠ NOTHING IN THE ZONING "
             "RESOLUTION SAYS THIS — it is a private covenant, and it is the "
             "single most important fact about lot 21's future"),

 # ---- ACCESS — the owner must GIVE something ---------------------------
 dict(bbl="1008000020", seq=2, dim="ACCESS", val=None, unit="boolean",
      vfrom=None, vto=None, vdatum=None, hscope="PORTION",
      hextent=None, hfrom="the parking lane and traffic lane fronting the lot",
      dur="DURING_CONSTRUCTION", ben=L49, sev="MINOR",
      doc="2013052101674004", page="p041", eff="2013-05-17", basis="read",
      detail="Form of Parking Lane Letter (Exhibit E): the neighbouring owner "
             "authorises Extell and its contractors to occupy the PARKING LANE "
             "AND TRAFFIC LANE in front of their property for the build. "
             "⚠ A pre-negotiated construction-logistics right, and the kind of "
             "thing that becomes a hold-up problem when it is NOT in place"),

 # ---- FLOOR_AREA — one dimension of five, not the whole story ----------
 dict(bbl="1008000023", seq=1, dim="FLOOR_AREA", val=22_845, unit="sf",
      datum="excess above 34,405 sf retained", ben=L49, sev="FATAL",
      doc="2012122701550003", page="p043", eff="2012-12-19", basis="derived",
      detail="Horne co-op. Rights gone; the building stays"),
 dict(bbl="1008000022", seq=2, dim="FLOOR_AREA", val=10_726, unit="sf",
      datum="excess above 17,899 sf retained", ben=L49, sev="FATAL",
      doc="2013052101674004", page="p040", eff="2013-05-17", basis="read",
      detail="Brick Farms. ⚠ COMBINED WITH THE 130 FT PLANE this lot is closed "
             "in two independent ways"),
 dict(bbl="1008000021", seq=2, dim="FLOOR_AREA", val=10_722, unit="sf",
      datum="excess transferred", ben=L49, sev="FATAL",
      doc="2013052101674008", page="p041", eff="2013-05-17", basis="read",
      detail="133 W 24th. ⚠ ALSO unit-capped — again, two independent closures"),
 dict(bbl="1008000053", seq=1, dim="FLOOR_AREA", val=23_864, unit="sf",
      datum="excess above 16,906 sf retained", ben=L49, sev="FATAL",
      doc="2010102601040006", page="p038", eff="2010-10-14", basis="read",
      detail="120 W 25th"),
 dict(bbl="1008000055", seq=1, dim="FLOOR_AREA", val=15_070, unit="sf",
      datum="excess above 9,620 sf retained", ben=L49, sev="FATAL",
      doc="2010102601040006", page="p038", eff="2010-10-14", basis="read",
      detail="124 W 25th"),
 dict(bbl="1008000056", seq=1, dim="FLOOR_AREA", val=14_644, unit="sf",
      datum="excess above 10,046 sf retained", ben=L49, sev="FATAL",
      doc="2010102601040006", page="p038", eff="2010-10-14", basis="read",
      detail="126 W 25th"),
 dict(bbl="1008000020", seq=3, dim="FLOOR_AREA", val=14_703, unit="sf",
      datum="airspace excess", ben=L49, sev="FATAL",
      doc="2013080901116002", page="p040", eff="2013-08-07", basis="read",
      detail="135 W 24th"),

 # ---- USE / structural obligations -------------------------------------
 dict(bbl=L49, seq=1, dim="USE", val=None, unit="boolean",
      datum="all eight lots, single declarant", ben=None, sev="MINOR",
      doc="2013080901116001", page="p003", eff="2013-08-07", basis="read",
      detail="Declaration of Zoning Lot Restrictions: lot 49 cannot be zoned "
             "independently of lots 20, 21, 22, 23, 53, 55, 56. Administrative "
             "for a single owner; a genuine constraint the moment any lot "
             "changes hands"),
]

# ---------------------------------------------------------------------------
# SIGNALS — every one carries the RULE it applied and what would falsify it.
# ---------------------------------------------------------------------------
SIGNALS = [
 dict(seq=1, eff="2007-06-20", cat="INTENT",
      signal="A developer, not an investor, has taken the site",
      rule="An operating apartment building bought by an entity holding no "
           "other interest on the block, with acquisition debt at ~90% of "
           "price, is a redevelopment play — an income buyer does not lever "
           "that far on a 1920s walk-up",
      conf="medium", claims=["c2007-conveyance", "c2007-mtge", "c2007-price"],
      counter="If the buyer had held it unchanged for a decade, this reads as "
              "an income purchase instead"),
 dict(seq=2, eff="2010-10-14", cat="INTENT",
      signal="Assemblage has begun; the developer is buying the block's air",
      rule="A ZLDA merging neighbouring lots into one zoning lot is never "
           "defensive — it is only useful to a party intending to build",
      conf="high", claims=["c2010-rights", "c2010-far"],
      counter="A ZLDA recorded to CURE an existing overbuild would look similar "
              "on its face; the excess-transfer direction distinguishes them"),
 dict(seq=3, eff="2012-12-19", cat="MARKET",
      signal="Air-rights pricing on this block MORE THAN DOUBLED in 26 months "
             "— $93.32 to $202.00/sf",
      rule="Two transfers into the same zoning lot, both quantities taken from "
           "Exhibit D charts and both prices from cover-page tax stamps, are "
           "directly comparable. The premium tracks POSITION: lot 23 is the "
           "through-block linchpin joining 24th to 25th Street",
      conf="high", claims=["c2010-rate", "c2012-rate"],
      counter="If the 2010 bundle had been distress-priced the spread would "
              "measure the seller, not the market"),
 dict(seq=4, eff="2013-08-07", cat="INTENT",
      signal="Extell was assembling to SELL, not to build",
      rule="Completing the final rights transfer and the eight-lot declaration "
           "IN THE SAME RECORDING BATCH as the deed out means the envelope was "
           "the product. A builder does not finish entitlement and convey the "
           "same day",
      conf="high", claims=["c2013c-decl", "c2013-sale", "c2013c-rights"],
      counter="A forced sale would produce the same batch; the 58% gain over "
              "six years argues against distress"),
 dict(seq=5, eff="2015-09-02", cat="PHASE",
      signal="Construction started",
      rule="Two mortgage tranches recorded together with an assignment of "
           "leases and rents far exceeding them ($113.7M against $65.7M) is a "
           "construction facility — the pledge covers future income the "
           "building does not yet produce",
      conf="high", claims=["m2015a", "m2015b", "c2015-pledge"],
      counter="DOB's permit dates are the independent witness. If no NB permit "
              "precedes this, the reading is wrong"),
 dict(seq=6, eff="2018-11-19", cat="PHASE",
      signal="The construction loan was RETIRED — the project stabilised",
      rule="A consolidated position FALLING from $113.7M to $48.0M is a "
           "repayment, and a construction facility repaid without a sale means "
           "the asset began carrying itself",
      conf="medium", claims=["c2015-pledge", "p2018-pos"],
      counter="⚠ UNVERIFIED. A partial release or a lot-50 split of the debt "
              "would produce the same drop on lot 49's record alone. The lot 50 "
              "documents nobody has read would settle it"),
 dict(seq=7, eff="2023-10-16", cat="PHASE",
      signal="Permanent financing — the asset is stabilised and held long",
      rule="LIFE INSURANCE COMPANIES LEND ON STABILISED CASH FLOW, NOT ON "
           "CONSTRUCTION. A MetLife takeout replacing bank debt is the standard "
           "marker of a completed, performing asset",
      conf="high", claims=["c2023-mtge", "c2023-cons"],
      counter="If MetLife were the mezz or a rescue lender the read inverts; "
              "the $0 taxable consolidation and full-value new money argue "
              "against distress"),
 dict(seq=8, eff="2023-10-16", cat="RISK",
      signal="The owner REFINANCED rather than sold — no exit intended",
      rule="A $0 deed between entities at the same address, recorded in the "
           "same batch as $25.5M of new money, is a recapitalisation. Ownership "
           "changed on paper and control did not",
      conf="high", claims=["c2023-reorg", "c2023-mtge"],
      counter="⚠ AND THE COMPARABLES CONSEQUENCE: this deed must NEVER enter a "
              "sales comp set. Recorded at $0 it would drag any $/sf average "
              "toward zero"),
 dict(seq=9, eff="2003-10-28", cat="INTENT",
      signal="Sophisticated long-hold ownership, preserving tax basis",
      rule="Repeated use of the section 255 exemption — 2003, 2012, 2023 — "
           "means every refinancing was structured to avoid paying mortgage tax "
           "twice on the same debt. That is deliberate, advised, and consistent "
           "with an owner who does not intend to sell",
      conf="medium", claims=["c2003-cema", "c2023-cons"],
      counter="Common enough to be weak on its own; it corroborates rather "
              "than proves"),
 dict(seq=10, eff="2013-05-17", cat="RISK",
      signal="Two neighbouring lots are closed in TWO INDEPENDENT WAYS",
      rule="Lots 21 and 22 each carry a rights transfer AND a second binding "
           "constraint — a 7-unit cap and a 130 ft height plane. Reacquiring "
           "floor area would not reopen either site",
      conf="high", claims=["c2013a-ease", "c2013b-cap"],
      counter="A negotiated release by lot 49's owner could lift them; both "
              "run with the land and require that owner's consent"),
]


def main():
    crows = [dict(burdened_bbl=c["bbl"], seq=c["seq"], dimension=c["dim"],
                  limit_value=c.get("val"), limit_unit=c["unit"],
                  vertical_from=c.get("vfrom"), vertical_to=c.get("vto"),
                  vertical_datum=c.get("vdatum"),
                  horizontal_scope=c.get("hscope"),
                  horizontal_extent=c.get("hextent"),
                  horizontal_from=c.get("hfrom"),
                  duration=c.get("dur", "PERPETUAL"),
                  is_variable=c.get("variable", False),
                  variable_by=c.get("var_by"),
                  variable_notice=c.get("var_notice"),
                  variable_floor=c.get("var_floor"),
                  datum=c.get("datum"), benefited_bbl=c.get("ben"),
                  severity=c["sev"], document_id=c["doc"],
                  page=c.get("page"), effective=c["eff"], basis=c["basis"],
                  detail=c["detail"]) for c in CONSTRAINTS]
    srows = [dict(bbl=L49, seq=s["seq"], effective=s["eff"], signal=s["signal"],
                  category=s["cat"], rule=s["rule"], confidence=s["conf"],
                  from_claims=s["claims"], counter=s.get("counter"))
             for s in SIGNALS]

    from collections import Counter
    print("CONSTRAINTS — five dimensions, and only one of them is square feet\n")
    dims = Counter(c["dimension"] for c in crows)
    print("  " + " · ".join(f"{k} {v}" for k, v in dims.most_common()) + "\n")
    for dim in ["HEIGHT", "UNITS", "ACCESS", "USE", "FLOOR_AREA"]:
        sel = [c for c in crows if c["dimension"] == dim]
        if not sel:
            continue
        print(f"  {dim}")
        for c in sel:
            lv = (f"{c['limit_value']:,.0f} {c['limit_unit']}"
                  if c["limit_value"] else c["limit_unit"])
            print(f"    lot {c['burdened_bbl'][-3:].lstrip('0'):<3} {lv:<22}"
                  f"{c['severity']:<9}{c['document_id']} {c['page'] or ''}")
        print()

    print("  ⚠ LOTS CLOSED IN MORE THAN ONE DIMENSION — reacquiring floor area")
    print("    would NOT reopen these sites:")
    per = {}
    for c in crows:
        if c["severity"] in ("FATAL", "MAJOR") and c["burdened_bbl"] != L49:
            per.setdefault(c["burdened_bbl"], set()).add(c["dimension"])
    for b, ds in sorted(per.items()):
        if len(ds) > 1:
            print(f"      lot {b[-3:].lstrip('0'):<3} {' + '.join(sorted(ds))}")

    print("\n\nSIGNALS — interpretation, each with the rule it applied\n")
    for s in srows:
        print(f"  {s['effective']}  [{s['category']}·{s['confidence']}]  {s['signal']}")
        print(f"      RULE: {s['rule'][:150]}")
        if s["counter"]:
            print(f"      FALSIFIED BY: {s['counter'][:130]}")
        print(f"      rests on: {', '.join(s['from_claims'])}\n")

    for name, data in (("acris_constraints", crows), ("acris_signals", srows)):
        p = HERE / f"{name}_{L49}.csv"
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader(); w.writerows(data)
        print(f"  wrote {p.name} ({len(data)} rows)")

    # every signal must rest on claims that exist
    sys.path.insert(0, str(HERE))
    import claims as K
    ids = {c["claim_id"] for c in K.rows()}
    bad = [(s["seq"], c) for s in srows for c in s["from_claims"] if c not in ids]
    if bad:
        print("\n⚠ SIGNAL RESTS ON A CLAIM THAT DOES NOT EXIST:")
        for seq, c in bad:
            print(f"    signal {seq} -> {c}")
        sys.exit(1)
    print(f"\n  all {len(srows)} signals trace to existing claims ✓")


if __name__ == "__main__":
    if "--ddl" in sys.argv:
        print(DDL); sys.exit(0)
    main()
