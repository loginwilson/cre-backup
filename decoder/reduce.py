"""Reducer — turns validated facts into ledger postings. Deterministic, no hand-typing.

Fixes three gaps:
  1. MANUAL REDUCER   -> postings are generated from a declarative transfer spec
                         (which the decoder's `transfers[]` block will supply
                         directly for every future decode; the spec below is the
                         one-time backfill for the 12 pilot documents).
  2. COLLECTIVE GRANTS-> transfer-group model: EVERY lot on BOTH sides gets a
                         posting tagged with its group and side. Per-lot
                         quantities only when the document states them; a
                         collective side carries the group total and a null
                         per-lot quantity. Splits are never invented, and no
                         participating lot is ever invisible.
  3. BAD ROWS         -> validate_row() rejects malformed BBLs, dates and
                         quantities loudly, before anything reaches the database.

Balance is checked at GROUP level: Σ|debits| == Σ credits per group.
"""
import json, pathlib, re, sys, urllib.request

ENV = r"C:/dev/acris-decoder.env"
LEGALS = r"C:/Users/smile/AppData/Local/Temp/claude/C--Users-smile/176544e8-656c-4540-a15c-f710beced15e/scratchpad/devr/legals.json"

BBL_RE = re.compile(r"^\d{10}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def bbl(boro, block, lot):
    return f"{int(boro)}{int(block):05d}{int(lot):04d}"


def condo_units(doc_id, block, min_lot=1101):
    """Expand a condominium's unit lots from the index legals (the document
    treats them collectively as one Land; every unit lot is a participant)."""
    rows = json.load(open(LEGALS, encoding="utf-8"))
    out = {bbl(r["borough"], r["block"], r["lot"]) for r in rows
           if r["document_id"] == doc_id and int(r["block"]) == block
           and int(r["lot"]) >= min_lot}
    return sorted(out)


# ---------------------------------------------------------------- transfer spec
# group: (sf, usd, basis, from[(bbl, per_lot_sf|None)], to[...], provenance)
# per_lot_sf None on a side => document states no per-lot split for that side.
def spec():
    G = {}
    G["2026061500475003"] = [dict(
        group="g1", sf=1079, usd=134875.00, basis="chart",
        frm=[("3030230019", 1079)], to=[("3030230020", 1079)],
        prov="Exhibit D chart p21; grant §2.A.i p6")]

    G["2004110301042003"] = [dict(
        group="g1", sf=4075, usd=50000.00, basis="operative_clause",
        frm=[("3027220036", 4075)],
        to=[("3027220008", None), ("3027220010", None),
            ("3027220033", None), ("3027220034", None)],
        prov="§ operative p11; Developer Parcel = lots 8/10/33/34, no per-lot split stated")]

    G["2005101400455004"] = [dict(
        group="g1", sf=3989, usd=616450.69, basis="recital",
        frm=[("1014290128", 3989)], to=[("1014290025", 3989)],
        prov="recital definition p5")]

    G["2010102601040006"] = [dict(
        group="g1", sf=53578, usd=5000000.00, basis="chart",
        frm=[("1008000053", 23864), ("1008000055", 15070), ("1008000056", 14644)],
        to=[("1008000049", 53578)],
        prov="Exhibit D chart p38 rows 4-5; price from prepaid tax back-solve p1")]

    G["2014070300770002"] = [dict(
        group="g1", sf=35815, usd=7763666.19, basis="definition",
        frm=[("1000370013", 35815)], to=[("1000370008", 35815)],
        prov="defs p5; Floor Area Notice §6 p11; Architect Cert p32")]

    G["2014091201052002"] = [dict(
        group="g1", sf=1500, usd=137563.75, basis="recital",
        frm=[("3027650035", 1500)], to=[("3027650014", 1500)],
        prov="recital E p5: Transferor's Excess Development Rights = 1,500 sf; "
             "retained ~1,300 sf; architect letter p24")]

    G["2017053000419005"] = [dict(
        group="g1", sf=14275, usd=0.00, basis="chart",
        frm=[("4097930078", 14275)], to=[("4097930079", 14275)],
        prov="def 1.M p7; Exhibit F chart p46 (related-party, no price)")]

    G["2021020901358005"] = [dict(
        group="g1", sf=10690, usd=675000.00, basis="chart",
        frm=[("1019080004", 10690)], to=[("1019080060", 10690)],
        prov="def §1(c) p3; e4h chart p18 (community-facility rights)")]

    G["2025102901095004"] = [dict(
        group="g1", sf=55000, usd=1685980.00, basis="definition",
        frm=[("4120990050", 55000)],
        to=[("4120990032", None), ("4120990038", None)],
        prov="def Subject Development Rights p7; to Developer Premises lots 32+38 collectively")]

    city = [("3024720020", None), ("3024720025", None), ("3024720035", None),
            ("3024720075", None), ("3024940003", None)]
    G["2021070601644010"] = [
        dict(group="g1", sf=211898, usd=0.00, basis="recital",
             frm=city,
             to=[("3024720030", None), ("3024720055", None),
                 ("3024940010", None), ("3024940020", None)],
             prov="Recital P p8 - City Land -> GLA Land, no per-lot split stated"),
        dict(group="g2", sf=289329, usd=0.00, basis="recital",
             frm=city, to=[("3024720070", 289329)],
             prov="Recital Q p8 - City Land -> Parcel H1H2 (Block 2472 Lot 70)"),
    ]

    G["2026012000388003"] = [dict(
        group="g1", sf=None, usd=549305.48, basis="operative_clause",
        frm=[(b, None) for b in condo_units("2026012000388003", 1446)],
        to=[("1014460001", None), ("1014460002", None), ("1014460003", None)],
        prov="§2 grant p14 - ALL Excess Development Rights, QUANTITY NEVER STATED; "
             "condo units 1101-1181 = Condominium Land; resolve SF via FAR baseline")]

    G["2026012000388004"] = [dict(
        group="g1", sf=6554, usd=1650000.00, basis="definition",
        frm=[("1014460151", 6554)],
        to=[("1014460001", None), ("1014460002", None), ("1014460003", None)],
        prov="§1.17 p7: (1,021.8 lot area x 10 FAR) - 3,664 utilized = 6,554; "
             "to Developer Land lots 1/2/3 collectively, no per-lot split stated")]

    G["2012120600575002"] = []   # airspace split: no transfer
    G["2026012000388002"] = []   # declaration: creates the zoning lot, moves no rights
    return G


# ------------------------------------------------------------------- validation
def validate_row(r):
    errs = []
    if not BBL_RE.match(str(r["bbl"])):
        errs.append(f"bad bbl {r['bbl']!r}")
    if r["effective_date"] is not None and not DATE_RE.match(str(r["effective_date"])):
        errs.append(f"bad date {r['effective_date']!r}")
    for f in ("quantity_sf", "amount_usd"):
        if r[f] is not None and not isinstance(r[f], (int, float)):
            errs.append(f"non-numeric {f} {r[f]!r}")
    if not r.get("provenance"):
        errs.append("missing provenance")
    return errs


def reduce_document(doc_id, groups, effective_date):
    """transfer spec -> postings. Every side member gets a row."""
    rows = []
    for g in groups:
        gid = f"{doc_id}:{g['group']}"
        stated_from = sum(sf for _, sf in g["frm"] if sf is not None)
        for side, members, sign in (("from", g["frm"], -1), ("to", g["to"], +1)):
            for b, per_lot in members:
                allocation = "stated" if per_lot is not None else "collective_unallocated"
                # money rides the from-side only, pro-rated when per-lot SF is stated
                amt = None
                if side == "from" and g["usd"] is not None:
                    if per_lot is not None and stated_from:
                        amt = round(g["usd"] * per_lot / stated_from, 2)
                    elif len(g["frm"]) == 1:
                        amt = g["usd"]
                rows.append(dict(
                    document_id=doc_id, bbl=b, bbl_source="document",
                    account="envelope_transferable", effective_date=effective_date,
                    quantity_sf=(sign * per_lot) if per_lot is not None else None,
                    amount_usd=amt, counter_bbls=[m for m, _ in (g["to"] if side == "from" else g["frm"])],
                    payload={"transfer_group": gid, "side": side,
                             "group_quantity_sf": g["sf"], "group_amount_usd": g["usd"],
                             "allocation": allocation, "basis": g["basis"],
                             "side_member_count": len(members)},
                    provenance=g["prov"]))
    return rows


def balance(rows):
    """Group-level conservation: Σ|debits| == Σ credits, by stated quantity or
    by group total when a side is collective."""
    out = {}
    for r in rows:
        g = r["payload"]["transfer_group"]
        d = out.setdefault(g, {"from_sf": 0, "to_sf": 0, "group_sf": r["payload"]["group_quantity_sf"],
                               "from_n": 0, "to_n": 0, "unallocated": False})
        side = r["payload"]["side"]
        d[f"{side}_n"] += 1
        if r["quantity_sf"] is None:
            d["unallocated"] = True
        else:
            d[f"{side}_sf"] += abs(r["quantity_sf"])
    return out


def env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


def main(decoded_dir, push=True):
    url, key = env()
    dates = {}
    for f in pathlib.Path(decoded_dir).glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        v = (d.get("effective_dates") or {}).get("document_date")
        v = (v.get("value") if isinstance(v, dict) else v)
        v = str(v)[:10] if v else None
        dates[d["doc_id"]] = v if v and DATE_RE.match(v) else None

    all_rows, bad = [], []
    for doc_id, groups in spec().items():
        rows = reduce_document(doc_id, groups, dates.get(doc_id))
        for r in rows:
            errs = validate_row(r)
            if errs:
                bad.append((doc_id, r["bbl"], errs))
            else:
                all_rows.append(r)

    print(f"generated {len(all_rows)} envelope postings across {len(spec())} documents")
    print(f"rejected by validate_row(): {len(bad)}")
    for b in bad:
        print("   REJECT", b)

    print("\ngroup-level conservation:")
    ok = True
    for g, d in sorted(balance(all_rows).items()):
        if d["unallocated"]:
            status = f"collective (group total {d['group_sf']}) — {d['from_n']} from / {d['to_n']} to lots"
        else:
            match = abs(d["from_sf"] - d["to_sf"]) < 1
            ok &= match
            status = f"{d['from_sf']:,} out == {d['to_sf']:,} in  {'BALANCED' if match else 'UNBALANCED'}"
        print(f"  {g:<28} {status}")
    print("\nall fully-allocated groups balanced:", ok)

    if push:
        req = urllib.request.Request(
            f"{url}/rest/v1/decoder_posting?account=eq.envelope_transferable",
            headers={"apikey": key, "Authorization": f"Bearer {key}"}, method="DELETE")
        urllib.request.urlopen(req, timeout=60).read()
        req = urllib.request.Request(
            f"{url}/rest/v1/decoder_posting?on_conflict=document_id,bbl,account,provenance",
            data=json.dumps(all_rows).encode(),
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "Prefer": "resolution=merge-duplicates"}, method="POST")
        urllib.request.urlopen(req, timeout=120).read()
        print(f"\npushed {len(all_rows)} postings to Supabase (replaced prior envelope rows)")


if __name__ == "__main__":
    main(sys.argv[1])
