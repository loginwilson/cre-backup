"""BBL spine + parcel baselines.

Two problems, one build:

  SPINE      Lots are born, merge, split and condo-convert. A document names the
             lot as it existed when recorded; the tax map shows today's lot.
             Rule: POST to what the document names, RESOLVE at read time.
             Sources: PLUTO `appbbl` (the apportioned/predecessor lot) and
             `condono` (condominium billing lot), plus unit-lot ranges recovered
             from the decoded documents themselves.

  BASELINE   An envelope posting is a delta; without an opening balance it means
             nothing. Baseline = lot area x permitted FAR from zoning, per lot,
             per use. Written locally (and to decoder_bbl_spine where the schema
             allows) until the baseline table exists in Supabase.

Nothing here guesses: a lot with no PLUTO record is reported unresolved.
"""
import json, pathlib, re, sys, urllib.parse, urllib.request

TOKEN = "XBMcBRBwtwiD4elm0XS5iwLRZ"
PLUTO = "https://data.cityofnewyork.us/resource/64uk-42ks.json"
ENV = r"C:/dev/acris-decoder.env"
OUT = pathlib.Path(__file__).with_name("baselines.json")
BORO_CODE = {1: "MN", 2: "BX", 3: "BK", 4: "QN", 5: "SI"}


def env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


URL, KEY = env()


def sb(path, method="GET", body=None):
    req = urllib.request.Request(
        URL + "/rest/v1/" + path,
        data=json.dumps(body).encode() if body else None,
        headers={"apikey": KEY, "Authorization": f"Bearer {KEY}",
                 "Content-Type": "application/json",
                 "Prefer": "resolution=merge-duplicates,return=minimal"},
        method=method)
    with urllib.request.urlopen(req, timeout=90) as f:
        raw = f.read()
    return json.loads(raw) if raw and method == "GET" else None


def pluto_block(boro_digit, block):
    q = urllib.parse.urlencode({
        "$select": "bbl,block,lot,lotarea,zonedist1,zonedist2,residfar,commfar,"
                   "facilfar,builtfar,bldgarea,condono,appbbl,appdate,ownername,address",
        "$where": f"borough='{BORO_CODE[boro_digit]}' AND block={block}",
        "$limit": 2000, "$$app_token": TOKEN})
    with urllib.request.urlopen(PLUTO + "?" + q, timeout=90) as f:
        return json.load(f)


def norm(b):
    """PLUTO returns bbl as a float string like '1014460149.00000000'."""
    if b in (None, "", "-"):
        return None
    return str(int(float(b))).zfill(10)


def main():
    posts = sb("decoder_posting?select=bbl,document_id,account&limit=5000")
    docs = sb("decoder_document?select=document_id,raw_facts")
    facts = {d["document_id"]: d["raw_facts"] for d in docs}

    blocks = sorted({(int(p["bbl"][0]), int(p["bbl"][1:6])) for p in posts})
    print(f"blocks touched by decoded documents: {len(blocks)}")

    lots, spine, baselines = {}, {}, {}
    for boro, block in blocks:
        for r in pluto_block(boro, block):
            b = norm(r.get("bbl"))
            if not b:
                continue
            lots[b] = r
            far = {k: float(r[k]) for k in ("residfar", "commfar", "facilfar")
                   if r.get(k) not in (None, "")}
            area = float(r["lotarea"]) if r.get("lotarea") else None
            baselines[b] = {
                "lot_area": area, "zonedist": r.get("zonedist1"),
                "zonedist2": r.get("zonedist2"), "far": far,
                "as_of_right_sf": {k: round(area * v, 2) for k, v in far.items()} if area else None,
                "built_far": float(r["builtfar"]) if r.get("builtfar") else None,
                "bldg_area": float(r["bldgarea"]) if r.get("bldgarea") else None,
                "condono": r.get("condono"), "owner": r.get("ownername"),
                "source": "pluto_current"}
            pred = norm(r.get("appbbl"))
            if pred and pred != b:
                # PLUTO's appbbl: the lot this one was apportioned FROM
                spine.setdefault(pred, {"successors": set(), "predecessors": set(),
                                        "source": "pluto_appbbl"})["successors"].add(b)
                spine.setdefault(b, {"successors": set(), "predecessors": set(),
                                     "source": "pluto_appbbl"})["predecessors"].add(pred)

    # ---- unit-lot ranges recovered from the documents themselves -----------
    # A condominium's unit lots are not in PLUTO (PLUTO carries one billing lot
    # per condo). The decoded documents name the unit lots AND their retired
    # base lot ("f/k/a Lot 149"); PLUTO ties that base lot to the billing lot
    # via appbbl. Chaining the two resolves every unit lot to one canonical lot.
    unit_links = 0
    for doc_id, f in facts.items():
        note = json.dumps(f)
        for b in {p["bbl"] for p in posts if p["document_id"] == doc_id}:
            lot = int(b[6:])
            if lot < 1001 or b in lots:      # not a unit lot, or PLUTO knows it
                continue
            block_lots = [x for x in lots.values()
                          if norm(x.get("bbl"))[:6] == b[:6] and x.get("condono")]
            cand = None
            if len(block_lots) == 1:
                cand = norm(block_lots[0]["bbl"])
            else:
                # Disambiguate by the retired base lot the document names.
                # Documents write it many ways: "f/k/a Lot 149", "f/k/a lot 149",
                # "f/k/a 149", "formerly Lot 149" — match case-insensitively on
                # the f/k/a / formerly phrase so a bare number cannot false-match.
                low = note.lower()
                for x in block_lots:
                    pred = norm(x.get("appbbl"))
                    if not pred:
                        continue
                    n = int(pred[6:])
                    if re.search(rf"(?:f/?k/?a|formerly)\s*(?:tax\s*)?(?:lot\s*)?0*{n}\b", low):
                        cand = norm(x["bbl"])
                        break
            if cand:
                spine.setdefault(b, {"successors": set(), "predecessors": set(),
                                     "source": "document+pluto_condono"})["successors"].add(cand)
                spine[b]["source"] = "document+pluto_condono"
                unit_links += 1

    rows = [dict(bbl=b, valid_from=None, valid_to=None,
                 predecessors=sorted(v["predecessors"]) or None,
                 successors=sorted(v["successors"]) or None,
                 source=v["source"]) for b, v in spine.items()]
    # primary key is (bbl, valid_from); PostgREST needs a non-null key component
    for r in rows:
        r["valid_from"] = "1900-01-01"
    if rows:
        sb("decoder_bbl_spine?on_conflict=bbl,valid_from", "POST", rows)

    OUT.write_text(json.dumps(baselines, indent=1), encoding="utf-8")
    posted = {p["bbl"] for p in posts}
    unresolved = sorted(b for b in posted if b not in lots and b not in spine)
    print(f"PLUTO lots loaded: {len(lots)} | spine rows: {len(rows)} "
          f"(unit-lot links: {unit_links}) | baselines written: {len(baselines)}")
    print(f"posted BBLs with no PLUTO record and no spine link: {len(unresolved)}")
    if unresolved:
        print("  ", unresolved[:12], "..." if len(unresolved) > 12 else "")


if __name__ == "__main__":
    main()
