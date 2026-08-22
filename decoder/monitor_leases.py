"""DAILY DIFF — what changed in every building since the last pull.

    python monitor_leases.py                 # report only
    python monitor_leases.py --promote       # roll the baseline forward
    python monitor_leases.py --json out.json

THE MODEL, as the operator set it out

    "basically active and historical and running the changes across both ...
     so say an active becomes historical it goes 29, 1,193 or say a new one gets
     added to active and it jumps to 31."

    Two lanes per parcel, and the diff is yesterday's rows against today's.

        NEW ACTIVE       a listing that was not there yesterday
        WENT HISTORICAL  active yesterday, in the historical lane today
        NEW HISTORICAL   appeared already closed — a lease we never saw listed
        GONE             a row that vanished from both lanes entirely
        NEW BUILDING     a parcel with listings that had none before
        DARK BUILDING    a parcel that had listings and now has none

⚠ IDENTITY IS `source_id`, NOT (unit, date, amount). Measured on the first 24
    buildings: 1,106 of 35,156 records shared unit+date+amount while being
    different listings. On a diff that mistake is worse than on a load — the
    same apartment would look like it moved when it did not.

⚠ A LISTING KEEPS ITS `source_id` WHEN IT GOES OFF MARKET. That is what makes
    "active became historical" observable as a TRANSITION rather than inferred
    from a disappearance plus an appearance. The old rent_cache monitor could
    only see that a unit vanished, which is a lease and a broker pulling a
    listing equally often; here the row carries its own outcome.

⚠ AND A BUILDING MISSING FROM TODAY'S PULL IS NOT A BUILDING THAT WENT DARK.
    A pull that stopped early, a 403, a slug that 404s — all produce "no rows
    today" and none of them mean the listings ended. So `GONE` and `DARK` are
    only reported for buildings that WERE pulled today, and the count of
    buildings absent from the pull is printed beside them rather than folded in.
"""
import json, os, pathlib, sys, time, urllib.error, urllib.request
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import to_supabase as T

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

RAW = pathlib.Path(__file__).with_name("leases_raw")
BASELINE = pathlib.Path(__file__).with_name("leases_baseline.json")


def today_rows():
    """Every listing in the newest raw pull, keyed by (bbl, source_id)."""
    files = sorted(RAW.glob("leases_*.jsonl"))
    if not files:
        raise SystemExit(f"no pull in {RAW}")
    rows, pulled = {}, set()
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("test") or not r.get("bbl") or not r.get("source_id"):
                    continue
                pulled.add(r["bbl"])
                lane = "active" if (r.get("lane") or r.get("status")) == "active" else "historical"
                rows[(r["bbl"], str(r["source_id"]))] = {
                    "bbl": r["bbl"], "sid": str(r["source_id"]), "lane": lane,
                    "unit": r.get("unit"), "unit_key": r.get("unit_key"),
                    "type": r.get("unit_type"), "sf": r.get("sf"),
                    "amount": r.get("amount"), "date": r.get("event_date"),
                    "name": r.get("building_name"), "se_status": r.get("se_status"),
                }
    return rows, pulled


def from_supabase():
    """The last known state, read back from the table rather than a local file —
    so the diff is against what is actually stored, not what we think we stored."""
    out, frm = {}, 0
    while True:
        req = urllib.request.Request(
            f"{T.URL}/rest/v1/residential_leases?select=bbl,source_id,status,unit,"
            f"unit_key,unit_type,sf,amount,event_date,building_name"
            f"&order=bbl.asc,source_id.asc",
            headers={**T.H, "Range-Unit": "items", "Range": f"{frm}-{frm+999}"})
        with urllib.request.urlopen(req, timeout=300) as f:
            chunk = json.loads(f.read() or b"[]")
        for r in chunk:
            out[(r["bbl"], str(r["source_id"]))] = {
                "bbl": r["bbl"], "sid": str(r["source_id"]), "lane": r["status"],
                "unit": r.get("unit"), "unit_key": r.get("unit_key"),
                "type": r.get("unit_type"), "sf": r.get("sf"),
                "amount": r.get("amount"), "date": r.get("event_date"),
                "name": r.get("building_name"),
            }
        if len(chunk) < 1000:
            break
        frm += 1000
    return out


def diff(prev, now, pulled):
    ev = defaultdict(list)
    for k, n in now.items():
        p = prev.get(k)
        if p is None:
            ev["NEW ACTIVE" if n["lane"] == "active" else "NEW HISTORICAL"].append(n)
        elif p["lane"] == "active" and n["lane"] == "historical":
            ev["WENT HISTORICAL"].append({**n, "was_amount": p.get("amount")})
        elif p["lane"] == n["lane"] and p.get("amount") != n.get("amount"):
            ev["REPRICED"].append({**n, "was_amount": p.get("amount")})
    for k, p in prev.items():
        # only a building we actually pulled today can be said to have lost a row
        if k not in now and p["bbl"] in pulled:
            ev["GONE"].append(p)
    prev_b = {p["bbl"] for p in prev.values()}
    now_b = {n["bbl"] for n in now.values()}
    ev["NEW BUILDING"] = [{"bbl": b} for b in sorted(now_b - prev_b)]
    ev["DARK BUILDING"] = [{"bbl": b} for b in sorted((prev_b - now_b) & pulled)]
    return ev


def main():
    promote = "--promote" in sys.argv
    jout = next((sys.argv[i + 1] for i, a in enumerate(sys.argv)
                 if a == "--json" and i + 1 < len(sys.argv)), None)

    now, pulled = today_rows()
    print(f"today's pull: {len(now):,} listings across {len({r['bbl'] for r in now.values()}):,} parcels")

    prev = from_supabase()
    print(f"stored state: {len(prev):,} listings across {len({r['bbl'] for r in prev.values()}):,} parcels")
    if not prev:
        print("\nnothing stored yet — load first; a diff needs two states.")
        return

    # ⚠ the denominator that keeps GONE honest
    prev_b = {p["bbl"] for p in prev.values()}
    missing = len(prev_b - pulled)
    if missing:
        print(f"  ⚠ {missing:,} stored parcels were NOT in today's pull — their rows are "
              f"excluded from GONE/DARK, because 'not pulled' and 'no longer listed' "
              f"are different things")

    ev = diff(prev, now, pulled)
    print("\nCHANGES")
    for k in ("NEW ACTIVE", "WENT HISTORICAL", "NEW HISTORICAL", "GONE",
              "REPRICED", "NEW BUILDING", "DARK BUILDING"):
        print(f"  {k:<18}{len(ev.get(k, [])):>8,}")

    # per-building counts, which is how the operator reads it: 30/1,192 -> 29/1,193
    moved = defaultdict(lambda: Counter())
    for k in ("NEW ACTIVE", "WENT HISTORICAL", "NEW HISTORICAL", "GONE"):
        for r in ev.get(k, []):
            moved[r["bbl"]][k] += 1
    if moved:
        cnt_now = Counter()
        for n in now.values():
            cnt_now[(n["bbl"], n["lane"])] += 1
        cnt_prev = Counter()
        for p in prev.values():
            cnt_prev[(p["bbl"], p["lane"])] += 1
        print(f"\n  {len(moved):,} parcels moved. The busiest:")
        print(f"    {'parcel':<12}{'was':>12}{'now':>12}   building")
        for b, c in sorted(moved.items(), key=lambda x: -sum(x[1].values()))[:20]:
            nm = next((n["name"] for n in now.values() if n["bbl"] == b and n["name"]), "")
            was = f"{cnt_prev[(b,'active')]}/{cnt_prev[(b,'historical')]}"
            new = f"{cnt_now[(b,'active')]}/{cnt_now[(b,'historical')]}"
            print(f"    {b:<12}{was:>12}{new:>12}   {str(nm)[:34]}")

    show = [k for k in ("WENT HISTORICAL", "NEW ACTIVE") if ev.get(k)]
    for k in show:
        print(f"\n  {k}:")
        for r in ev[k][:12]:
            amt = f"${r['amount']:,.0f}" if r.get("amount") else "—"
            was = f" (was ${r['was_amount']:,.0f})" if r.get("was_amount") and r["was_amount"] != r.get("amount") else ""
            print(f"    {r['bbl']}  {str(r.get('unit') or '—'):<7}{str(r.get('type') or ''):<9}"
                  f"{(str(int(r['sf']))+' sf') if r.get('sf') else 'no sf':>8}  {amt:>9}{was}  {r.get('date')}")
        if len(ev[k]) > 12:
            print(f"    … and {len(ev[k])-12:,} more")

    if jout:
        pathlib.Path(jout).write_text(json.dumps(
            {k: v for k, v in ev.items()}, indent=1), encoding="utf-8")
        print(f"\nwrote {jout}")

    if promote:
        # promoting means loading today's pull, so the NEXT diff compares to it
        n = T.load_leases()
        print(f"\npromoted — {n:,} rows upserted; tomorrow's diff runs against this")
    else:
        print("\nreport only. Re-run with --promote to load today's pull and roll "
              "the baseline forward.")


if __name__ == "__main__":
    main()
