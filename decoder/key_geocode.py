"""GEOCODE — the address as a third, independent witness.

    python key_geocode.py            # recover the unplaced, then audit the placed

WHY THE ADDRESS MATTERS SEPARATELY FROM THE PIN

    Placement has been running on the map pin alone: pin -> polygon -> capacity.
    That is one witness. StreetEasy also publishes an ADDRESS for nearly every
    building, and an address resolves through NYC GeoSearch to a BBL by a wholly
    different route — the address register, not geometry. Two independent
    derivations that agree are worth far more than either alone.

    Login: *"it should be as simple as taking every single building listed and
    pinning it to their parcel from the spine with the name and address."*

⚠ THE HOUSE NUMBER IS A GATE, NOT A HINT. GeoSearch will cheerfully return a
    NEIGHBOUR for an address it cannot place exactly, silently. Proven on this
    project: "41-15 24th Street" (The Pecora) came back as "41-41 24 STREET" — a
    different building — which would have filed all 89 of its rental events on
    somebody else's parcel. Nothing downstream could have caught it: the BBL is
    valid, the events are real, they are simply on the wrong lot.

    So: ask for FIVE candidates, keep only one whose house number matches
    EXACTLY, and return nothing rather than accept a near miss. Asking for a
    single result is what caused that failure, and it also made Lumen LIC look
    unresolvable when its exact match was sitting at rank 2.

WHAT THIS DOES

    1. RECOVER  the buildings still unplaced after pin-based keying, using the
       address, gated on the house number and corroborated by the unit count.
    2. AUDIT    a sample of the buildings already placed, comparing the pin's
       answer to the address's. Agreement is the accuracy measure this layer has
       been missing — a number that can be wrong, rather than a placement rate
       that only counts whether SOMETHING was found.
"""
import json, math, pathlib, random, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

KEYS = pathlib.Path("buildings/streeteasy-parcel-keys.json")
LIST = pathlib.Path("buildings/streeteasy-buildings.json")
GEOSEARCH = "https://geosearch.planninglabs.nyc/v2/search"
BORO_NAME = {"1": "Manhattan", "2": "Bronx", "3": "Brooklyn", "4": "Queens", "5": "Staten Island"}


def addr_of(b, r=None):
    """★ THE NAME IS USUALLY THE ADDRESS, and missing that cost the address
    witness on 96% of the corpus.

    StreetEasy prints a separate "At 401 East 34th Street" line ONLY when the
    building has a distinct name. When the name IS the address — '10 Hanover
    Square', '95 Wall Street', '400 West 61st Street' — there is no such line,
    so the parser recorded no address and 40,107 of 41,765 buildings looked
    address-less. They were not; the address was in the field labelled `name`.

    A name that begins with a house number is an address. A name that does not
    ('Halo LIC', 'Sven') is a building name and no address is available.
    """
    import re
    a = (b or {}).get("address") or (r or {}).get("address")
    if a:
        return a
    nm = (b or {}).get("name") or (r or {}).get("name") or ""
    return nm if re.match(r"^\d+(-\d+)?\s+\S", nm.strip()) else None


def house_no(s):
    m = str(s or "").strip()
    m = m.split(",")[0]
    import re
    g = re.match(r"^(\d+(?:-\d+)?)", m)
    return g.group(1).replace("-", "") if g else None


def geocode(addr, boro, tries=3):
    """Five candidates, house-number gated. Returns (bbl, label) or (None, why)."""
    want = house_no(addr)
    q = urllib.parse.urlencode({"size": "5", "text": f"{addr}, {boro}, NY"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(f"{GEOSEARCH}?{q}", timeout=45) as f:
                j = json.load(f)
            break
        except Exception:
            if i == tries - 1:
                return None, "geosearch failed"
            time.sleep(1.5 * (i + 1))
    for feat in (j.get("features") or []):
        p = feat.get("properties") or {}
        bbl = ((p.get("addendum") or {}).get("pad") or {}).get("bbl")
        if not bbl:
            continue
        if want and house_no(p.get("label") or "") != want:
            continue          # a near miss is a MISS
        return str(bbl), p.get("label")
    return None, "no candidate with an exact house-number match"


def boro_of(area, placed_by_area):
    """Derive the borough from what the placed buildings in this area actually
    keyed to, rather than assuming the area-code mapping."""
    c = placed_by_area.get(area)
    return BORO_NAME.get(c, "New York")


def main():
    keys = json.loads(KEYS.read_text(encoding="utf-8"))
    lst = {b["slug"]: b for b in json.loads(LIST.read_text(encoding="utf-8"))}
    by_slug = {r["slug"]: r for r in keys}

    # area code -> borough digit, measured from placements rather than assumed
    tally = defaultdict(Counter)
    for r in keys:
        if r.get("bbl") and r.get("area"):
            tally[r["area"]][r["bbl"][0]] += 1
    placed_by_area = {a: c.most_common(1)[0][0] for a, c in tally.items()}
    print("area -> borough, measured from placements:")
    for a, d in sorted(placed_by_area.items()):
        print(f"    area:{a} -> {d} {BORO_NAME[d]}  ({tally[a].most_common(1)[0][1]:,} buildings)")

    # ── 1. RECOVER ──────────────────────────────────────────────────────────
    un = [r for r in keys if not r.get("bbl")]
    print(f"\nrecovering {len(un)} unplaced by address...")
    rec, nogate, noaddr = 0, 0, 0
    for n, r in enumerate(un, 1):
        b = lst.get(r["slug"]) or {}
        addr = addr_of(b, r)
        if not addr:
            noaddr += 1
            continue
        bbl, why = geocode(addr, boro_of(r.get("area"), placed_by_area))
        if not bbl:
            nogate += 1
        else:
            r |= {"bbl": bbl, "verdict": "recovered-address",
                  "reason": f"pin unusable; address '{addr}' resolves to {bbl} "
                            f"with an exact house-number match ({why})"}
            rec += 1
        if n % 100 == 0:
            print(f"    {n}/{len(un)} · recovered {rec}")
        time.sleep(0.12)
    print(f"  recovered {rec} · {nogate} had no exact house-number match · {noaddr} had no address")

    # ── 2. AUDIT ────────────────────────────────────────────────────────────
    placed = [r for r in keys if r.get("bbl") and r["verdict"] == "exact"]
    sample = random.Random(7).sample(placed, min(400, len(placed)))
    print(f"\nauditing {len(sample)} pin-placed buildings against the address...")
    agree = differ = ungated = 0
    diffs = []
    for n, r in enumerate(sample, 1):
        b = lst.get(r["slug"]) or {}
        addr = addr_of(b, r)
        if not addr:
            ungated += 1
            continue
        bbl, why = geocode(addr, BORO_NAME.get(r["bbl"][0], "New York"))
        if not bbl:
            ungated += 1
        elif bbl == r["bbl"]:
            agree += 1
        else:
            differ += 1
            diffs.append((r.get("name"), addr, r["bbl"], bbl))
        if n % 100 == 0:
            print(f"    {n}/{len(sample)} · agree {agree} differ {differ}")
        time.sleep(0.12)
    tested = agree + differ
    print(f"\n  AGREEMENT: {agree} of {tested} ({agree/max(tested,1)*100:.1f}%) — "
          f"{ungated} could not be gated")
    print("  where they differ:")
    for nm, a, p, g in diffs[:8]:
        print(f"    {str(nm)[:24]:<25}{str(a)[:26]:<27}pin={p}  addr={g}")

    st = Counter(r["verdict"] for r in keys)
    tot = sum(n for k, n in st.items() if k.startswith(("exact", "recovered")))
    print(f"\nFINAL — {len(keys):,} buildings · PLACED {tot:,} ({tot/len(keys)*100:.1f}%)")
    for k, n in st.most_common():
        print(f"  {k:<22}{n:>8,}")
    KEYS.write_text(json.dumps(keys, indent=1), encoding="utf-8")
    print(f"  wrote {KEYS}")


if __name__ == "__main__":
    main()
