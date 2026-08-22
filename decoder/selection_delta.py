"""THE DAILY SELECTION RECONCILIATION — live ACRIS vs the map IN SUPABASE.

    python selection_delta.py            report the delta (reads only)
    python selection_delta.py --map      report, then map + upsert what is missing

Login, 2026-08-13: *"the selection map should be in supabase and the daily
master row check + delta determines what needs to update to the selection map in
the database"*. So the AUTHORITY is `document_map` in Supabase, not a local
jsonl, and this is the job that keeps it level with ACRIS.

⚠ WHY THIS EXISTS ALONGSIDE map_delta.py — THREE THINGS THAT FILE CANNOT DO.

 1. **It diffs against LOCAL FILES.** `map_delta.mapped_ids()` unions three
    jsonl files on disk. That answers "is my laptop current", which is not the
    question once the database is the selection map. A file can be complete
    while the table is 12 million rows behind — measured 2026-08-13: local
    17,049,742 mapped, `document_map` holding 4,563,156.
 2. **Its fast pass is keyed on `:updated_at > watermark`, and the watermark IS
    the dataset's current maximum.** Measured 2026-08-13: fast pass reported
    **0 new** while the live row count sat **15,348 above** what was mapped.
    A monitor that can only look forward inherits every gap it already has and
    reports clean. THE COUNT IS THE INDEPENDENT WITNESS — it does not care when
    a row landed.
 3. **It writes to a local file.** Newly mapped documents go to docmaps.jsonl,
    which push_selection.py does not even read (it reads acris_maps.jsonl), so a
    delta run could "succeed" and never reach the database at all.

⚠ AND THE CHEAP TRICK THAT MAKES IT A DAILY JOB: RECONCILE PER doc_type FIRST.
Pulling 17M ids from either side to diff costs ~45 minutes. But a COUNT per
doc_type costs one query per side (95 types, grouped, two requests), and it
localises the gap to the handful of types that actually moved. Only those types
get their ids pulled and diffed. A day with 20,000 new documents touches maybe
six types, so the daily cost is six type-pulls, not ninety-five.

⚠ COUNTS ARE A DETECTOR, NOT A PROOF. ACRIS master carries duplicate
document_ids, so live_rows > distinct_ids and a small positive gap can be pure
duplication. Any type whose counts disagree is therefore taken to the ID diff,
and the ID diff is what decides. A type whose counts AGREE is not proven equal —
it is only "no evidence of a gap", and this prints it that way. `--full-ids`
forces the exhaustive per-type id diff when you want the stronger statement.

⚠ A TYPE MISSING FROM ONE SIDE IS NOT ZERO. If `document_map` has never seen a
doc_type at all it does not appear in the grouped count, and `dict.get(t)` would
return None; treating that as 0 is right, but treating a type that is live-absent
as "gone" is not — it is reported separately and never used to delete anything.
This job only ever ADDS.
"""
import argparse
import asyncio
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import acris_lock
import amap
import bulk
import supabase_sync as S

MASTER = "bnx9-e6tj"
TABLE = "document_map"
STATE = pathlib.Path(__file__).with_name("_selection_delta_state.json")
MAP_CONC = 16


def sb(path):
    url, key = S._env()
    req = urllib.request.Request(
        url.rstrip("/") + "/rest/v1/" + path,
        headers={"apikey": key, "Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=180) as f:
        return json.load(f)


def sb_count():
    """Exact row count of the selection map. Uses the count header, not a pull."""
    url, key = S._env()
    req = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/{TABLE}?select=document_id&limit=1",
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Prefer": "count=exact", "Range": "0-0"})
    with urllib.request.urlopen(req, timeout=180) as f:
        cr = f.headers.get("Content-Range", "")
    # "0-0/17049742" — the part after the slash. "*" means the server declined
    # to count, which is a CHECK FAILURE, never a zero.
    tail = cr.split("/")[-1] if "/" in cr else ""
    return int(tail) if tail.isdigit() else None


def live_by_type():
    return {r["doc_type"]: int(r["n"]) for r in
            bulk.socrata(MASTER, select="doc_type,count(1) as n",
                         group="doc_type", paginate=True)}


def db_count(where=""):
    """Exact count of document_map, optionally filtered. Header only, no pull."""
    url, key = S._env()
    q = f"{TABLE}?select=document_id&limit=1" + (("&" + where) if where else "")
    req = urllib.request.Request(
        f"{url.rstrip('/')}/rest/v1/{q}",
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Prefer": "count=exact", "Range": "0-0"})
    with urllib.request.urlopen(req, timeout=300) as f:
        cr = f.headers.get("Content-Range", "")
    tail = cr.split("/")[-1] if "/" in cr else ""
    return int(tail) if tail.isdigit() else None


def db_by_type(types):
    """Rows per doc_type, ONE FILTERED COUNT PER TYPE.

    ⚠ NOT a grouped query. Supabase refuses PostgREST aggregates outright —
    `select=doc_type,document_id.count()` returns
    400 PGRST123 "Use of aggregate functions is not allowed" — so a GROUP BY
    over the table is simply not available over this API. 95 counted requests
    is the whole cost, and each is a header, not a result set.

    ⚠ A count that comes back as None is a CHECK FAILURE, not a zero. It is
    kept as None so the caller reports "could not evaluate" instead of
    manufacturing a gap of the type's entire size.
    """
    out = {}
    for i, t in enumerate(sorted(types), 1):
        out[t] = db_count("doc_type=eq." + urllib.parse.quote(t))
        if i % 25 == 0 or i == len(types):
            print(f"    counted {i}/{len(types)} types in the map", flush=True)
    return out


def live_ids(doc_type):
    ids = {}
    for r in bulk.socrata(MASTER, where=f"doc_type='{doc_type}'",
                          select="document_id,doc_type,recorded_datetime",
                          paginate=True):
        ids.setdefault(r["document_id"], r)
    return ids


def db_ids(doc_type):
    """Every document_id the map holds for one type. Paginated explicitly —
    a page that comes back exactly at the cap is indistinguishable from a
    complete one, which is a trap this project has already paid for twice."""
    out, off, PAGE = set(), 0, 10000
    while True:
        rows = sb(f"{TABLE}?select=document_id&doc_type=eq."
                  f"{urllib.parse.quote(doc_type)}&limit={PAGE}&offset={off}"
                  f"&order=document_id")
        out.update(r["document_id"] for r in rows)
        if len(rows) < PAGE:
            return out
        off += PAGE


def upsert(rows):
    """Straight to the selection map, merging on document_id."""
    import push_selection
    S.push(TABLE, rows, "document_id", "document_map")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", action="store_true",
                    help="map the missing ids and upsert them (default: report only)")
    ap.add_argument("--full-ids", action="store_true",
                    help="id-diff EVERY type, not only the ones whose counts disagree")
    a = ap.parse_args()
    t0 = time.time()

    print("SELECTION RECONCILIATION — live ACRIS vs document_map in Supabase\n")

    held = sb_count()
    if held is None:
        print("  [check_failed] document_map would not return an exact count. "
              "Nothing below can be trusted; stopping.")
        return 2

    live_t = live_by_type()
    live_rows = sum(live_t.values())
    print(f"  live master rows     {live_rows:>12,}   ({len(live_t)} doc types)")
    print(f"  document_map holds   {held:>12,}")
    print(f"  difference           {live_rows - held:>12,}"
          "   ⚠ live rows include duplicate document_ids; the id diff decides\n")

    db_t = db_by_type(live_t)
    unevaluable = sorted(t for t, v in db_t.items() if v is None)
    suspect = sorted(t for t in live_t
                     if db_t.get(t) is None or live_t[t] != db_t[t])
    agree = [t for t in live_t if t not in suspect]
    print(f"  types whose counts AGREE          {len(agree):>3}"
          "   (no evidence of a gap — not proof of equality)")
    print(f"  types whose counts DISAGREE       {len(suspect):>3}   -> id diff")
    if unevaluable:
        print(f"  ⚠ {len(unevaluable)} type(s) the map would not count "
              f"({unevaluable[:5]}) — treated as UNKNOWN and id-diffed, "
              "never as empty")

    todo = sorted(live_t) if a.full_ids else suspect
    missing, live_rec = {}, {}
    for i, t in enumerate(todo, 1):
        lv = live_ids(t)
        have = db_ids(t)
        gap = set(lv) - have
        if gap:
            missing[t] = gap
            live_rec.update({d: lv[d] for d in gap})
        print(f"    [{i}/{len(todo)}] {t:<10} live {len(lv):>9,} distinct · "
              f"map {len(have):>9,} · MISSING {len(gap):>7,}", flush=True)

    n_missing = sum(len(v) for v in missing.values())
    print(f"\n  MISSING FROM THE SELECTION MAP   {n_missing:,}"
          f"   across {len(missing)} type(s)")

    state = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "live_rows": live_rows, "map_rows": held,
             "types_checked": len(todo), "missing": n_missing,
             "missing_by_type": {t: len(v) for t, v in missing.items()},
             "mode": "full-ids" if a.full_ids else "count-localised",
             "mapped_this_run": 0}

    if n_missing and a.map:
        ids = sorted(live_rec)
        print(f"\n  mapping {len(ids):,} documents at {MAP_CONC} concurrent ...")
        with acris_lock.AcrisLock("selection_delta", wait=True):
            asyncio.run(amap.run(ids, conc=MAP_CONC))
        # ⚠ RE-READ FROM THE FILE. amap.run halts the gather on a refusal and
        # returns normally either way, so "it came back" is not evidence
        # anything was written — the same rule map_delta.do_map already carries.
        import map_delta
        after, _ = map_delta.ids_from(pathlib.Path("docmaps.jsonl"), "doc_id")
        done = [d for d in ids if d in after]
        print(f"  mapped {len(done):,} of {len(ids):,}")
        maps = {}
        for line in open("docmaps.jsonl", encoding="utf-8", errors="replace"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("doc_id") in after:
                maps[r["doc_id"]] = r          # last write wins per doc_id
        import push_selection
        rows = []
        for d in done:
            m = dict(maps.get(d) or {"doc_id": d})
            m.setdefault("doc_type", (live_rec[d] or {}).get("doc_type"))
            rec = (live_rec[d] or {}).get("recorded_datetime")
            m.setdefault("recorded", rec[:10] if rec else None)
            rows.append(push_selection.row(m))
        if rows:
            before = sb_count()
            upsert(rows)
            after_n = sb_count()
            print(f"  document_map {before:,} -> {after_n:,}  (+{after_n - before:,})")
            state["mapped_this_run"] = len(rows)
    elif n_missing:
        print("  (report only — re-run with --map to map and upsert them)")

    STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")
    print(f"\n  {time.time() - t0:.0f}s   state -> {STATE.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
