"""Parcel dossier — every decoded fact bound to one parcel, in time order.

This is where the ledger becomes readable: identity and lineage, the baseline
envelope, every recorded event that touched the lot, what is still restricting
it, who has appeared on it, and — stated first, never buried — how much of the
parcel's ACRIS record we have actually decoded.

Coverage is the honesty gate. A dossier that shows 3 events out of 47 recorded
documents is a sample, not a history, and must say so. Summary and derivation
come after coverage, never instead of it.
"""
import json, sys, urllib.parse, urllib.request
from pathlib import Path

TOKEN = "XBMcBRBwtwiD4elm0XS5iwLRZ"
LEGALS = "https://data.cityofnewyork.us/resource/8h5j-fqxa.json"
MASTER = "https://data.cityofnewyork.us/resource/bnx9-e6tj.json"
ENV = r"C:/dev/acris-decoder.env"


def env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


URL, KEY = env()


def sb(path):
    req = urllib.request.Request(URL + "/rest/v1/" + path,
                                 headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=90) as f:
        return json.load(f)


def soc(url, params):
    params["$$app_token"] = TOKEN
    with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=90) as f:
        return json.load(f)


def acris_record(bbl):
    """Every ACRIS document recorded against this lot — the denominator."""
    b, blk, lot = int(bbl[0]), int(bbl[1:6]), int(bbl[6:])
    rows = soc(LEGALS, {"$select": "document_id",
                        "$where": f"borough={b} AND block={blk} AND lot={lot}",
                        "$limit": 5000})
    ids = sorted({r["document_id"] for r in rows})
    meta = []
    for i in range(0, len(ids), 50):
        w = "document_id in(" + ",".join("'" + x + "'" for x in ids[i:i + 50]) + ")"
        meta += soc(MASTER, {"$select": "document_id,doc_type,recorded_datetime,document_amt",
                             "$where": w, "$limit": 5000})
    return meta


def dossier(bbl):
    baselines = json.loads((Path(__file__).with_name("baselines.json")).read_text(encoding="utf-8"))
    try:
        hist = json.loads((Path(__file__).with_name("baselines_historical.json")).read_text(encoding="utf-8"))
    except FileNotFoundError:
        hist = {}

    spine = {}
    for r in sb("decoder_bbl_spine?select=bbl,predecessors,successors,source"):
        cur = spine.setdefault(r["bbl"], {"successors": [], "predecessors": [], "source": []})
        cur["successors"] += r.get("successors") or []
        cur["predecessors"] += r.get("predecessors") or []
        cur["source"].append(r.get("source"))

    def canonical(b):
        seen, cur = set(), b
        while cur in spine and spine[cur]["successors"] and cur not in seen:
            seen.add(cur)
            cur = sorted(spine[cur]["successors"])[0]
        return cur

    canon = canonical(bbl)
    posts = [p for p in sb("decoder_posting?select=*&limit=5000")
             if p["bbl"] == bbl or canonical(p["bbl"]) == canon]
    docs = {d["document_id"]: d for d in sb("decoder_document?select=*")}
    consents = sb("decoder_consent?select=*")
    links = sb("decoder_lifecycle_link?select=*")

    record = acris_record(bbl)
    decoded_ids = {p["document_id"] for p in posts}

    print("=" * 78)
    print(f"PARCEL DOSSIER  {bbl}" + (f"   (canonical today: {canon})" if canon != bbl else ""))
    print("=" * 78)

    # ---- coverage first, always
    print("\nCOVERAGE")
    print(f"  ACRIS documents recorded against this lot : {len(record)}")
    print(f"  decoded so far                            : {len(decoded_ids)}")
    if record:
        yrs = sorted(r["recorded_datetime"][:4] for r in record if r.get("recorded_datetime"))
        print(f"  record spans                              : {yrs[0]} - {yrs[-1]}")
        kinds = {}
        for r in record:
            kinds[r["doc_type"]] = kinds.get(r["doc_type"], 0) + 1
        top = sorted(kinds.items(), key=lambda x: -x[1])[:8]
        print(f"  by type                                   : "
              + ", ".join(f"{k}x{v}" for k, v in top))
    pct = (100.0 * len(decoded_ids) / len(record)) if record else 0
    print(f"  >> this dossier reflects {pct:.0f}% of the recorded history — "
          f"{'a SAMPLE, not a history' if pct < 90 else 'substantially complete'}")

    # ---- identity and lineage
    print("\nIDENTITY & LINEAGE")
    sp = spine.get(bbl, {})
    bl = dict(baselines.get(canon) or baselines.get(bbl) or {})
    # THE SURVEY BEATS THE TAX MAP. Where a decoded instrument states this lot's
    # area, prefer it: PLUTO holds 1,040 SF for MN1446 L151 while the instrument's
    # own survey says 1,021.8 — using PLUTO would mis-state the residual envelope
    # by 182 SF. Recompute the baseline on the document's figure.
    doc_area = None
    for did in decoded_ids:
        la = ((docs.get(did) or {}).get("raw_facts") or {}).get("lot_areas_by_bbl") or {}
        if (la.get("values") or {}).get(bbl) and (la.get("extent") or {}).get(bbl) != "partial":
            doc_area = (la["values"][bbl], did, la.get("provenance"))
    if bl and doc_area and bl.get("lot_area") and abs(bl["lot_area"] - doc_area[0]) > 1:
        bl["lot_area_taxmap"] = bl["lot_area"]
        bl["lot_area"] = doc_area[0]
        bl["lot_area_source"] = f"survey in {doc_area[1]} ({doc_area[2]})"
        far = bl.get("far") or {}
        bl["as_of_right_sf"] = {k: round(doc_area[0] * v, 2) for k, v in far.items()}
    if bl:
        far = bl.get("far") or {}
        print(f"  lot area {bl.get('lot_area')} SF | zoning {bl.get('zonedist')} | "
              f"FAR res {far.get('residfar')} com {far.get('commfar')} fac {far.get('facilfar')}")
        if bl.get("lot_area_source"):
            print(f"  lot area from the SURVEY: {bl['lot_area']} SF "
                  f"(tax map says {bl['lot_area_taxmap']}) — {bl['lot_area_source']}")
        if bl.get("as_of_right_sf"):
            print(f"  as-of-right floor area (baseline): "
                  + ", ".join(f"{k} {v:,.0f}" for k, v in bl["as_of_right_sf"].items() if v))
    if sp.get("predecessors"):
        print(f"  came from : {sorted(set(sp['predecessors']))}")
    if sp.get("successors"):
        print(f"  became    : {sorted(set(sp['successors']))}")
    for s in sp.get("source", []):
        if s:
            print(f"  evidence  : {s}")

    # ---- the timeline
    print("\nTIMELINE (decoded events, oldest first)")
    evs = sorted(posts, key=lambda p: (p.get("effective_date") or "9999", p["document_id"]))
    seen = set()
    for p in evs:
        key = (p["document_id"], p["account"])
        if key in seen:
            continue
        seen.add(key)
        d = docs.get(p["document_id"], {})
        qty = p.get("quantity_sf")
        amt = p.get("amount_usd")
        bits = []
        if qty is not None:
            bits.append(f"{qty:+,.0f} SF")
        elif (p.get("payload") or {}).get("group_quantity_sf") is not None:
            bits.append(f"part of {p['payload']['group_quantity_sf']:,} SF (no per-lot split stated)")
        if amt:
            bits.append(f"${amt:,.0f}")
        print(f"  {p.get('effective_date') or '?'}  {d.get('doc_type','?'):<5} "
              f"{p['account']:<22} {'  '.join(bits)}")
        if d.get("what_it_does"):
            print(f"              {d['what_it_does'][:150]}")
        print(f"              [{p['document_id']}] {str(p.get('provenance'))[:90]}")

    # ---- envelope position
    print("\nENVELOPE POSITION")
    known = [p["quantity_sf"] for p in posts
             if p["account"] == "envelope_transferable" and p["quantity_sf"] is not None]
    unk = [p for p in posts
           if p["account"] == "envelope_transferable" and p["quantity_sf"] is None]
    base = (bl or {}).get("as_of_right_sf") or {}
    if base:
        print(f"  baseline as-of-right      : {base}")
    if known:
        print(f"  net recorded adjustment   : {sum(known):+,.0f} SF "
              f"(from {len(known)} quantified transfer postings)")
    if unk:
        print(f"  UNQUANTIFIED transfers    : {len(unk)} posting(s) touch this lot with no "
              f"per-lot SF stated — envelope cannot be closed from the record alone")
    if base and known and not unk:
        for use, sf in base.items():
            if not sf:
                continue          # a use with no as-of-right cannot go negative
            print(f"  implied remaining {use:<10}: {sf + sum(known):,.0f} SF")

    # ---- restrictions still live
    print("\nRESTRICTIONS (form / use / standing)")
    rel = {l["resolved_doc_id"] for l in links
           if l["relation"] in ("releases", "terminates", "supersedes") and l["resolved_doc_id"]}
    any_r = False
    for p in posts:
        if p["account"] in ("envelope_form", "use_restriction", "standing"):
            any_r = True
            live = "RELEASED" if p["document_id"] in rel else "live"
            print(f"  [{live}] {p['account']}: {(p.get('payload') or {}).get('detail')}")
            print(f"          [{p['document_id']}] {str(p.get('provenance'))[:80]}")
    if not any_r:
        print("  none recorded in the decoded set")

    # ---- parties and consents
    print("\nPARTIES OBSERVED")
    for did in sorted(decoded_ids):
        raw = (docs.get(did) or {}).get("raw_facts") or {}
        for pt in raw.get("parties", []) or []:
            if bbl[6:].lstrip("0") in str(pt.get("tax_lot", "")) or canon == bbl:
                print(f"  {pt.get('normalized_role','?'):<22} {pt.get('name')}  [{did}]")
    absent = [c for c in consents if c["document_id"] in decoded_ids and not c["present"]]
    if absent:
        print("\nCONSENTS EXPECTED BUT ABSENT (findings)")
        for c in absent[:8]:
            print(f"  {c['party'][:70]} — {c['instrument']}  [{c['document_id']}]")

    print("\n" + "=" * 78)


if __name__ == "__main__":
    for b in (sys.argv[1:] or ["1014460151"]):
        dossier(b)
