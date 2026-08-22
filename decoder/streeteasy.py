"""STREETEASY — the comparables decoder. Rent ledgers reconciled against the spine.

WHERE THE DATA ACTUALLY IS

    Not in a table of its own. A StreetEasy harvest lands in
    `property_records.data.rentLog` — an array of {date, rent, unit, type, sf,
    status} merged by `POST /api/harvest`, deduped on `date|rent|unit`, stamped
    with `rentPulledAt` at the point of WRITE. One row per (owner, bbl).

    So the comparables universe is a JSONB field on a parcel row, and the only
    key it has is the BBL a geocoder chose. That is the whole risk surface.

WHY THE SPINE IS A SECOND OPINION THE APP HAS NEVER HAD

    `scripts/reconcileRentLots.ts` already adjudicates placement with PLUTO
    `unitsres` — can this lot physically hold these apartments. Good test, and
    it caught a warehouse and a school.

    The spine answers a DIFFERENT question that PLUTO structurally cannot:
    IS THIS A PARCEL AT ALL, AND WHAT KIND. A BBL absent from the spine is not
    a parcel; PLUTO can only return no row, which reads identically to a fetch
    failure. And the spine holds the 307,436 condominium UNIT lots PLUTO omits,
    so it can tell a whole building's ledger sitting on one apartment's tax lot
    from a building sitting on its own lot.

    ⚠ RUNNING THIS DECODER IS WHAT FOUND THE SPINE'S OWN TWO DEFECTS
    (SPINE_DEFECTS.md, 2026-08-06). The first pass questioned 80 of 1,212
    ledgers; every one was the spine being wrong — the DTM flags read as
    identities, and condo BILLING lots missing entirely. Both are fixed
    upstream; `load_spine()` now refuses to run against the old vocabulary.
    The lesson worth keeping: when a reconciliation indicts the data, check the
    JOIN before the data. 80 of 80 were the join.

THREE OUTCOMES, NEVER TWO
    ok / empty / FAILED. A Supabase page that errors is FAILED and stops the
    run. It is never counted as zero rows.

⚠ PAGINATE EVERY SUPABASE READ — PostgREST caps a select at 1,000 rows and
    returns them WITHOUT AN ERROR. This has already silently broken the
    territory gate (1,000 -> really 7,086) and the monitor (10,415 -> 86,571).
    Every read here goes through `page()`, which walks until short.
"""
import json, os, pathlib, sys, time, urllib.error, urllib.parse, urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import sink

SOURCE = "STREETEASY"
APP_ENV = pathlib.Path("C:/dev/bkrea-territory-intelligence-app/.env.local")


def env(path=APP_ENV):
    v = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip().strip('"').strip("'")
    return v


def page(table, select, url, key, *, eq=None, size=1000, cap=None):
    """Every row, not the first thousand. Raises on error — never returns short
    because something failed, which is the whole point."""
    out, frm = [], 0
    q = f"{table}?select={select}"
    for k, val in (eq or {}).items():
        q += f"&{k}=eq.{val}"
    q += "&order=bbl.asc"
    while True:
        req = urllib.request.Request(
            f"{url}/rest/v1/{q}",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Range-Unit": "items", "Range": f"{frm}-{frm + size - 1}"})
        try:
            with urllib.request.urlopen(req, timeout=180) as f:
                chunk = json.loads(f.read() or b"[]")
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"FAILED at offset {frm}: HTTP {e.code} "
                               f"{e.read()[:200].decode(errors='replace')}")
        out.extend(chunk)
        if len(chunk) < size or (cap and len(out) >= cap):
            break
        frm += size
    return out


SPINE_DIR = pathlib.Path(os.environ.get(
    "DECODER_SPINE", pathlib.Path(__file__).with_name("spine")))
PLUTO = "https://data.cityofnewyork.us/resource/64uk-42ks.json"


def _soda(url, tries=5):
    """Socrata, with the app token and a retry. A dropped TLS handshake is a
    FAILURE to retry, never an empty result — returning [] here would write a
    short cache that then looks authoritative forever."""
    tok = env().get("NEXT_PUBLIC_SOCRATA_APP_TOKEN")
    req = urllib.request.Request(
        url, headers={"X-App-Token": tok} if tok else {})
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=300) as f:
                return json.load(f)
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"FAILED after {tries} tries: {type(last).__name__}: {last}")


# The vocabulary a CORRECTED spine emits. Both defects this decoder found on
# 2026-08-06 (SPINE_DEFECTS.md) are fixed upstream in spine.py now, so the
# overlay that used to live here is gone. What replaces it is a GUARD.
CORRECTED_KINDS = {"tax_lot", "condo_unit", "condo_billing"}
STALE_KINDS = {"ground", "reuc", "air", "subterranean"}


def load_spine():
    """BBL -> (kind, status, parent, n_children).

    ⚠ REFUSES A STALE SPINE. Before 2026-08-06 `lot_kind()` read the DTM's
    CONDO/REUC/AIR/SUB flags as the lot's IDENTITY when they actually mark a
    RELATED lot of that kind, and condo BILLING lots were absent from every
    layer. Under that spine this decoder called 33 correct placements misplaced
    and declared 43 real parcels non-existent — 15,002 rental events wrongly
    questioned out of 84,195.

    The failure mode worth guarding is not the old bug, which is fixed; it is a
    REBUILD THAT SILENTLY REVERTS. `kind == "ground"` would sail through every
    check below and quietly reintroduce verdicts already proven wrong once. So a
    stale vocabulary is a hard stop, not a warning.
    """
    p = SPINE_DIR / "spine.jsonl"
    if not p.exists():
        raise SystemExit(f"no spine at {p} — decoders must not run before it exists")
    out, n, kinds = {}, 0, Counter()
    with open(p, encoding="utf-8") as f:
        for line in f:
            n += 1
            try:
                r = json.loads(line)
            except Exception:
                continue
            kinds[r.get("kind")] += 1
            out[r["bbl"]] = (r.get("kind"), r.get("status"), r.get("parent"),
                             len(r.get("children") or []))
    if len(out) != n:
        print(f"  ⚠ spine: {n:,} lines read, {len(out):,} parcels indexed")
    stale = STALE_KINDS & set(kinds)
    if stale:
        raise SystemExit(
            f"STALE SPINE — kinds {sorted(stale)} are the pre-2026-08-06 "
            f"vocabulary, in which the DTM flags were misread as identities. "
            f"Rebuild with the corrected spine.py (see SPINE_DEFECTS.md) before "
            f"matching anything to a parcel.")
    if "condo_billing" not in kinds:
        raise SystemExit(
            "STALE SPINE — no condo_billing parcels. 11,132 of them carry "
            "412,507 apartments and they are where the new rental towers sit; "
            "without them every such building reads as 'not a parcel'.")
    unknown = set(kinds) - CORRECTED_KINDS
    if unknown:
        print(f"  ⚠ unrecognised spine kinds {sorted(unknown)} — treated as "
              f"suspect placements rather than waved through")
    print("  spine: " + " · ".join(f"{k} {v:,}" for k, v in kinds.most_common()))
    return out


# Lot kinds a rental building's ledger may legitimately sit on. A building
# stands on a tax lot; when the building is a condominium it is BILLED on a 75xx
# lot and that is the parcel every other source (PLUTO, DOF sales, StreetEasy's
# own geocode) keys on — so it is a correct placement, not a suspect one.
def ledgers(url, key, owner):
    """Every parcel row, and which of them carry a StreetEasy rent ledger.

    Returns (all_rows, with_ledger). BOTH, deliberately: `with_ledger` alone is
    a numerator with no denominator, and that is the failure this project has
    met eight times.
    """
    rows = page("property_records", "bbl,data,updated_at", url, key,
                eq={"owner_id": owner})
    held = []
    for r in rows:
        d = r.get("data") or {}
        log = d.get("rentLog")
        if not isinstance(log, list) or not log:
            continue
        held.append({
            "bbl": str(r["bbl"]),
            "name": str(d.get("name") or ""),
            "address": str(d.get("address") or ""),
            "events": len(log),
            "pulled_at": d.get("rentPulledAt"),
            "units_total": d.get("unitsTotal"),
            "with_sf": sum(1 for e in log if isinstance(e, dict)
                           and isinstance(e.get("sf"), (int, float)) and e["sf"]),
            "statuses": Counter(str((e or {}).get("status") or "?") for e in log),
        })
    return rows, held


OK_KINDS = {"tax_lot", "condo_billing"}
WHY = {
    "condo_unit": "a single condominium UNIT lot — a whole building's rent ledger "
                  "cannot belong to one apartment's tax lot",
}


def reconcile(spine, held):
    buckets = defaultdict(list)
    for h in held:
        row = spine.get(h["bbl"])
        if row is None:
            buckets["ABSENT_FROM_SPINE"].append(h)
            continue
        kind, status, parent, nkids = row
        h["kind"], h["status"], h["parent"], h["children"] = kind, status, parent, nkids
        if status != "live":
            buckets["RETIRED"].append(h)
        else:
            buckets[kind].append(h)
    return dict(buckets)


def report(url=None, key=None, owner=None):
    e = env()
    url = url or e["NEXT_PUBLIC_SUPABASE_URL"]
    key = key or e["SUPABASE_SERVICE_ROLE_KEY"]
    owner = owner or e["HARVEST_OWNER_ID"]
    run_id = f"streeteasy-reconcile-{int(time.time())}"

    print("loading spine...")
    spine = load_spine()
    print(f"  {len(spine):,} parcels")

    print("reading property_records (paginated)...")
    rows, held = ledgers(url, key, owner)
    events = sum(h["events"] for h in held)
    print(f"  {len(rows):,} parcel rows  ->  {len(held):,} carry a rent ledger  "
          f"->  {events:,} rental events")
    sink.heartbeat(SOURCE, run_id, done=0, total=len(held),
                   note=f"{len(rows)} parcel rows, {events} events")

    if not held:
        print("\n  0 ledgers. This is COMPLETE WITH ZERO, not 'never ran'.")
        sink.heartbeat(SOURCE, run_id, done=0, total=0, status="complete",
                       note="no rent ledgers in property_records")
        return

    b = reconcile(spine, held)
    print(f"\nRECONCILED AGAINST THE SPINE — {len(held):,} ledgers, "
          f"{events:,} events\n")
    print(f"  {'lot kind':<24}{'ledgers':>9}{'events':>10}   verdict")
    order = ["tax_lot", "condo_billing", "condo_unit", "RETIRED",
             "ABSENT_FROM_SPINE"]
    for k in order + [x for x in b if x not in order]:
        if k not in b:
            continue
        n = len(b[k])
        ev = sum(h["events"] for h in b[k])
        verdict = ("stands on a tax lot — placement consistent" if k == "tax_lot"
                   else "billed as a condominium — the parcel every other source "
                   "keys on" if k == "condo_billing" else
                   "NOT A PARCEL IN ANY LAYER — DTM, PLUTO or the billing range"
                   if k == "ABSENT_FROM_SPINE" else
                   "the lot is RETIRED — its history is real, its present is not"
                   if k == "RETIRED" else WHY.get(k, "unexpected lot kind"))
        print(f"  {k:<24}{n:>9,}{ev:>10,}   {verdict}")

    covered = sum(len(v) for v in b.values())
    print(f"\n  {covered:,} of {len(held):,} ledgers bucketed"
          + ("" if covered == len(held) else "   ⚠ DO NOT TRUST THIS — rows lost"))

    suspect = [h for k, v in b.items() if k not in OK_KINDS for h in v]
    if suspect:
        print(f"\n  {len(suspect)} ledger(s) the spine questions:")
        for h in sorted(suspect, key=lambda x: -x["events"])[:40]:
            k = h.get("kind") or "—"
            print(f"    {h['bbl']}  {k:<14}{h['events']:>6} events  "
                  f"{(h['name'] or h['address'] or '(unnamed)')[:44]}")

    sink.heartbeat(SOURCE, run_id, done=len(held), total=len(held),
                   status="complete",
                   note=f"reconciled vs spine; {len(suspect)} questioned")
    return b


if __name__ == "__main__":
    report()
