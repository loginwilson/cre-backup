"""Historical baselines: every posted parcel as the tax map showed it ON THE
DOCUMENT'S FILING DATE.

Comparing a 2004 instrument's lot areas against the 2026 map measures how much
the city has changed, not whether the decode is right. Each document needs the
vintage contemporaneous with it.

Batched by vintage: every parcel whose document falls in the same PLUTO vintage
is resolved in a single pass, so ~14 documents cost ~10 reads rather than 42.
Writes to baselines_historical.json keyed "<bbl>@<filing_date>".
"""
import json, pathlib, sys, urllib.request
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import spine_archive as sa

ENV = r"C:/dev/acris-decoder.env"
OUT = pathlib.Path(__file__).with_name("baselines_historical.json")


def env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


URL, KEY = env()


def get(path):
    req = urllib.request.Request(URL + "/rest/v1/" + path,
                                 headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=90) as f:
        return json.load(f)


def main():
    docs = {d["document_id"]: d for d in
            get("decoder_document?select=document_id,document_date,recorded_date")}
    posts = get("decoder_posting?select=document_id,bbl&limit=5000")

    # (bbl, filing_date) pairs, deduped
    pairs = set()
    for p in posts:
        d = docs.get(p["document_id"]) or {}
        when = d.get("document_date") or d.get("recorded_date")
        if when:
            pairs.add((p["bbl"], str(when)[:10]))
    print(f"{len(pairs)} (parcel, filing-date) pairs to resolve")

    vs = sa.vintages()

    def nearest(when):
        w = date.fromisoformat(when)
        best = vs[0]
        for v in vs:
            if sa.vintage_date(v.stem) <= w:
                best = v
        return best

    by_vintage = {}
    for bbl, when in pairs:
        by_vintage.setdefault(nearest(when).stem, set()).add((bbl, when))
    print(f"grouped into {len(by_vintage)} vintages: "
          f"{sorted(by_vintage, key=lambda s: sa._key(s))}")

    out = {}
    for stem in sorted(by_vintage, key=lambda s: sa._key(s)):
        want = {b for b, _ in by_vintage[stem]}
        zp = [v for v in vs if v.stem == stem][0]
        hits = 0
        for r in sa._rows(zp):
            b = sa._bbl_any(r)
            if b in want:
                a = {k: r.get(k) for k in sa.ATTRS if r.get(k) not in (None, "")}
                for bbl, when in by_vintage[stem]:
                    if bbl == b:
                        def num(x):
                            try:
                                return float(str(x).strip())
                            except (TypeError, ValueError):
                                return None
                        far = {k: num(a.get(k)) for k in ("residfar", "commfar", "facilfar")
                               if num(a.get(k)) is not None}
                        out[f"{bbl}@{when}"] = {
                            "vintage": stem, "as_of": when,
                            "lot_area": num(a.get("lotarea")),
                            "zonedist": (a.get("zonedist1") or "").strip() or None,
                            "far": far,
                            "bldg_area": num(a.get("bldgarea")),
                            "built_far": num(a.get("builtfar")),
                            "owner": (a.get("ownername") or "").strip() or None,
                            "source": f"pluto_archive {stem} (map as of the filing date)"}
                hits += 1
        print(f"  {stem}: matched {hits}/{len(want)} parcels", flush=True)

    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\nwrote {len(out)} historical baselines -> {OUT.name}")
    miss = [f"{b}@{w}" for b, w in pairs if f"{b}@{w}" not in out]
    print(f"unmatched at filing date: {len(miss)}")
    if miss:
        print("  ", miss[:10], "..." if len(miss) > 10 else "")


if __name__ == "__main__":
    main()
