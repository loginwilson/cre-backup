"""ACRIS as a parcel census — lot existence back to the 1960s.

PLUTO begins in 2002. ACRIS's *legals* table records a block-and-lot for every
recorded instrument back to the 1960s, so the set of documents naming a lot
brackets that lot's life: first filing … last filing. That is not geometry, but
it is an existence record with far deeper reach than any parcel file, and it is
free — we already pull it.

Why this matters for the resolve stack: PLUTO is a DERIVED convenience file, not
the legal tax map, and it LAGS (proved in this pilot — Jamaica lot 78 was
subdivided in Jan 2017 and the May 2017 instrument uses the post-subdivision
5,271 SF while PLUTO p17v1 still carried the pre-subdivision 29,568 SF). The
authority order for parcelling is:

  1. the recorded DOCUMENTS   metes and bounds define the land in any era, and
                              "f/k/a" recitals are lineage records
  2. DOF Digital Tax Map      the legal tax map and lot numbering (geometry-first,
                              versioned; NOT yet wired in)
  3. ACRIS legals             existence over time, 1960s -> present (this module)
  4. PLUTO                    richest attributes (area, zoning, FAR) but derived,
                              2002+, and known to lag the map

Writes observation windows into decoder_bbl_spine.source so a lifespan can state
where its evidence begins.
"""
import json, sys, urllib.parse, urllib.request

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


def soc(url, params):
    params["$$app_token"] = TOKEN
    with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=90) as f:
        return json.load(f)


def census(bbls):
    """{bbl: (first_filing, last_filing, n_documents)} from ACRIS legals."""
    out = {}
    for bbl in bbls:
        b, blk, lot = int(bbl[0]), int(bbl[1:6]), int(bbl[6:])
        rows = soc(LEGALS, {"$select": "document_id",
                            "$where": f"borough={b} AND block={blk} AND lot={lot}",
                            "$limit": 5000})
        ids = [r["document_id"] for r in rows]
        if not ids:
            out[bbl] = (None, None, 0)
            continue
        dates = []
        for i in range(0, len(ids), 50):
            w = "document_id in(" + ",".join("'" + x + "'" for x in ids[i:i + 50]) + ")"
            dates += [r["recorded_datetime"][:10] for r in
                      soc(MASTER, {"$select": "recorded_datetime", "$where": w, "$limit": 5000})
                      if r.get("recorded_datetime")]
        dates.sort()
        out[bbl] = (dates[0], dates[-1], len(ids)) if dates else (None, None, len(ids))
    return out


def main():
    posts = sb("decoder_posting?select=bbl&limit=5000")
    bbls = sorted({p["bbl"] for p in posts})
    # condo unit lots each carry their own thin history; census the canonical
    # parcels and the non-unit lots, which is where lineage questions live
    targets = [b for b in bbls if int(b[6:]) < 1001]
    print(f"censusing {len(targets)} parcels (excluding {len(bbls)-len(targets)} condo unit lots)")
    res = census(targets)
    rows, pre2002 = [], 0
    for bbl, (first, last, n) in sorted(res.items()):
        if not first:
            continue
        if first < "2002-01-01":
            pre2002 += 1
        rows.append(dict(bbl=bbl, valid_from=first, valid_to=None,
                         predecessors=None, successors=None,
                         source=f"acris_legals_census: {n} filings {first}..{last}"))
    if rows:
        sb("decoder_bbl_spine?on_conflict=bbl,valid_from", "POST", rows)
    print(f"census rows written: {len(rows)} | reaching before 2002: {pre2002}")
    earliest = min((r["valid_from"] for r in rows), default=None)
    print(f"earliest ACRIS evidence across the pilot: {earliest}")
    dead = [(b, v) for b, v in res.items() if v[1] and v[1] < "2015-01-01"]
    if dead:
        print("lots whose ACRIS activity stops early (candidate retirements):")
        for b, v in sorted(dead, key=lambda x: x[1][1]):
            print(f"   {b}: {v[2]:>3} filings, {v[0]} .. {v[1]}")


if __name__ == "__main__":
    main()
