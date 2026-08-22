"""ACRIS SELECTION — THE DAILY DELTA. Cost is O(what changed), not O(17M).

    python selection_daily.py            # report only
    python selection_daily.py --repair   # populate local + Supabase, advance watermark
    python selection_daily.py --since 2026-08-01T00:00:00.000Z   # re-ask a window

⚠ THE DAILY JOB MUST NOT READ EVERYTHING. `selection_cross.py` reads all four
map files (19.5M lines, ~4 min), counts 32 Supabase slices (~3 min) and pulls
ACRIS per type (~10 min). That is a correct AUDIT and a wrong DAILY JOB: it
spends twenty minutes re-proving 17,049,742 documents that did not move in order
to find the handful that did. ACRIS stamps every row with `:updated_at`, so the
question "what changed since yesterday" is answerable in one query. This file
asks that one, and touches ONLY the ids it returns.

    daily   this file          O(delta)      seconds when nothing moved
    audit   selection_cross.py O(17M)        run it weekly, not nightly

⚠ AND THE DAILY CANNOT REPLACE THE AUDIT. A monitor that only ever asks "what
arrived since the watermark" inherits every gap it already had and reports clean
forever — it cannot see a document withdrawn, re-indexed, or missed three weeks
ago. That is not a flaw to fix here; it is the reason the full cross still runs
on its own schedule. Saying so is the point: a cheap check that is mistaken for
a complete one is worse than no check.

⚠ THE WATERMARK ADVANCES ONLY AFTER THE WORK IS DONE, NEVER ON A LOOK. An
earlier version of the sibling job saved state before doing the work, so a
report-only run moved the watermark and the next real run found 0 rows — the
28,196 documents it had just found were now behind the cutoff, permanently
invisible to every future pass, while it printed "map is current". A watermark
is a promise that everything before it has been HANDLED.

⚠ THE STAMP IS READ BEFORE THE PULL. The pull captures everything up to pull
time, which is at or after the stamp, so advancing to it can only re-show a few
rows tomorrow. Reading it afterwards would step over anything that landed
mid-run.

⚠ A QUERY THAT WILL NOT ANSWER IS UNKNOWN, NEVER ZERO. Twice a Supabase range
failed every retry and answered in one second minutes later. Anything unanswered
leaves the watermark where it is.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

MASTER = "bnx9-e6tj"
TABLE = "document_map"
STATE = HERE / "_selection_daily_state.json"
CROSS_STATE = HERE / "_selection_cross_state.json"
MAP_STATE = HERE / "_map_delta_state.json"


def seed_from_audit():
    """A CLEAN EXHAUSTIVE AUDIT *IS* A VALID STARTING POINT — take it.

    ⚠ THE TWO JOBS WROTE SEPARATE STATE FILES AND NEITHER SEEDED THE OTHER, so
    the daily could never start: selection_cross.py reconciled all three sides
    at 17,049,742 and wrote `_selection_cross_state.json`, while this job looked
    for a watermark in `_selection_daily_state.json` and found none. It then
    refused — correctly — and printed "run selection_cross.py first", which had
    ALREADY RUN AND PASSED. Measured 2026-08-14: the routine was scheduled at
    04:00 and would have refused every night indefinitely.

    That is the phase-organization failure exactly: the thing needed was not
    missing, it was UNADDRESSABLE — one job's proof sitting in a file the other
    job never reads.

    ⚠ SEED WITH THE STAMP, NEVER WITH THE CLOCK. `checked_at` is naive local
    time; ACRIS `:updated_at` is UTC. Seeding from wall-clock would skip the
    EDT offset — four hours of updates, silently, once.

    ⚠ AND ONLY FROM A CLEAN AUDIT. Seeding from an audit that found differences
    would declare those differences already handled.
    """
    try:
        cs = json.loads(CROSS_STATE.read_text(encoding="utf-8"))
    except Exception:
        return None
    if cs.get("verdict") != "clean":
        return None
    stamp = cs.get("dataset_stamp")
    if not stamp:
        # The audit did not record which stamp it verified against. Fall back to
        # the exhaustive map delta's stamp: older means a WIDER re-ask, which
        # over-reports and never misses. Never guess forward.
        try:
            stamp = json.loads(
                MAP_STATE.read_text(encoding="utf-8")).get("dataset_stamp")
        except Exception:
            return None
    if stamp:
        print(f"  seeded watermark from clean audit -> {stamp}")
    return stamp
LOG = HERE / "_selection_daily.tsv"
# Sorted 8-byte hashes of every local doc_id, written by selection_cross.py.
IDX = HERE / "_local_ids.idx"
# Hashes this job has added since that index was last rebuilt.
NEWIDX = HERE / "_local_ids.new"
MAP_CONC = 16

# PostgREST membership batch. Keeps the URL well inside any request-line limit
# while still asking about hundreds of ids per round trip.
BATCH = 150


def env():
    url = key = None
    for line in open(r"C:\dev\acris-decoder.env", encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "ACRIS_SUPABASE_URL":
                url = v.strip().strip('"').rstrip("/")
            elif k.strip() == "ACRIS_SUPABASE_SERVICE_KEY":
                key = v.strip().strip('"')
    return url, key


def sb_get(url, key, path, tries=4, timeout=120):
    req = urllib.request.Request(
        f"{url}/rest/v1/{path}",
        headers={"apikey": key, "Authorization": "Bearer " + key})
    last = None
    for a in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as f:
                return json.load(f)
        except Exception as e:
            last = e
            if a < tries - 1:
                time.sleep(4 * (a + 1))
    raise RuntimeError(f"supabase: {type(last).__name__}: {last}")


def held_by_db(url, key, ids):
    """Which of these ids document_map already has. Membership, not a scan.

    ⚠ ASKS ABOUT THE DELTA ONLY. This is the whole optimisation: `in.(...)` over
    150 primary keys is an index probe, so the cost tracks the delta and not the
    table. Counting the table to infer the same answer costs minutes and tells
    you less — a matching total does not prove these particular ids are present.
    """
    have = set()
    for i in range(0, len(ids), BATCH):
        chunk = ids[i:i + BATCH]
        lst = ",".join('"' + d.replace('"', '""') + '"' for d in chunk)
        rows = sb_get(url, key,
                      f"{TABLE}?select=document_id&document_id=in.({urllib.parse.quote(lst)})")
        have.update(r["document_id"] for r in rows)
        if (i // BATCH) % 20 == 0 and i:
            print(f"      probed {i:,}/{len(ids):,}", flush=True)
    return have


def held_by_local(ids):
    """Which of these ids the local map files hold — via the index, O(delta).

    ⚠ SCANNING THE FILES DAILY IS THE COST THIS JOB EXISTS TO AVOID. Streaming
    19,549,196 lines to answer a question about 30 ids takes four minutes and
    scales with the corpus rather than the change. `selection_cross.py` already
    reads every line during its audit, so it writes what it learned:
    `_local_ids.idx`, the sorted 8-byte hashes of every local doc_id (~136 MB,
    loads in about a second). Membership is then a binary search.

    ⚠ THE INDEX IS DERIVED, NEVER AUTHORITATIVE. It is rebuilt from the files by
    the audit and appended to by this job. If it is missing, this returns None
    and the caller reports the local side as UNKNOWN — it must never quietly
    skip the check and let "I did not look" read as "nothing is missing".
    """
    if not IDX.exists():
        return None
    blob = IDX.read_bytes()
    n = len(blob) // 8
    import bisect

    class Keys:
        __len__ = lambda self: n
        def __getitem__(self, i):
            return blob[i * 8:i * 8 + 8]

    keys = Keys()
    found = set()
    for d in ids:
        k = hashlib.blake2b(d.encode(), digest_size=8).digest()
        i = bisect.bisect_left(keys, k)
        if i < n and keys[i] == k:
            found.add(d)
    # Documents this job added since the last audit live in the sidecar.
    if NEWIDX.exists():
        extra = set()
        b2 = NEWIDX.read_bytes()
        for i in range(0, len(b2), 8):
            extra.add(b2[i:i + 8])
        for d in ids:
            if hashlib.blake2b(d.encode(), digest_size=8).digest() in extra:
                found.add(d)
    return found


def note_local(ids):
    """Record ids this job wrote to the local files, so tomorrow sees them
    without waiting for the next full audit to rebuild the index."""
    with open(NEWIDX, "ab") as f:
        for d in ids:
            f.write(hashlib.blake2b(d.encode(), digest_size=8).digest())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repair", action="store_true")
    ap.add_argument("--since", default=None,
                    help="override the watermark (re-ask a window; never advances past it)")
    a = ap.parse_args()
    t0 = time.time()
    url, key = env()
    import bulk

    st = json.loads(STATE.read_text()) if STATE.exists() else {}
    last = a.since or st.get("dataset_stamp") or seed_from_audit()

    print("ACRIS SELECTION — daily delta\n")

    # ⚠ STAMP FIRST, THEN THE PULL.
    now = bulk.socrata(MASTER, select="max(:updated_at) as mx",
                       paginate=False, limit=1)
    now = now[0]["mx"] if now else None
    print(f"  dataset stamp   {now}")
    print(f"  watermark       {last or '(never — run selection_cross.py first)'}")

    if not last:
        print("\n  NO WATERMARK. A daily delta with no starting point would "
              "report 0 and mean nothing.\n  Run `python selection_cross.py` "
              "for the exhaustive baseline first.")
        return 2

    rows = bulk.socrata(MASTER, where=f":updated_at > '{last}'",
                        select="document_id,doc_type,recorded_datetime",
                        paginate=True)
    # ⚠ MASTER CARRIES DUPLICATE document_ids — dedupe before counting anything.
    live = {}
    for r in rows:
        live.setdefault(r["document_id"], r)
    ids = sorted(live)
    print(f"  arrived/changed {len(rows):,} rows -> {len(ids):,} distinct ids"
          f"   ({time.time()-t0:.0f}s)")

    if not ids:
        print("\n  NOTHING CHANGED. Nothing to reconcile.")
        if a.repair:
            STATE.write_text(json.dumps(
                {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "dataset_stamp": now, "delta": 0, "missing_db": 0,
                 "missing_local": 0, "verdict": "no_change"}, indent=1),
                encoding="utf-8")
        print(f"  ({time.time()-t0:.0f}s)")
        return 0

    print(f"\n  CHECKING THE DELTA AGAINST BOTH SIDES")
    try:
        in_db = held_by_db(url, key, ids)
    except Exception as e:
        print(f"  [check_failed] supabase would not answer: {e}")
        print("  Watermark held. Nothing below can be trusted.")
        return 2
    miss_db = [d for d in ids if d not in in_db]
    print(f"    supabase holds  {len(in_db):>9,} of {len(ids):,}"
          f"   MISSING {len(miss_db):,}")

    in_local = held_by_local(ids)
    if in_local is None:
        # ⚠ NOT LOOKING IS NOT THE SAME AS NOTHING MISSING.
        print(f"    local           UNKNOWN — no {IDX.name}; run "
              f"`python selection_cross.py` to build it")
        print("  Watermark held: a delta checked against one side is not a "
              "reconciliation.")
        return 2
    miss_local = [d for d in ids if d not in in_local]
    print(f"    local holds     {len(in_local):>9,} of {len(ids):,}"
          f"   MISSING {len(miss_local):,}")

    st_out = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "delta": len(ids), "missing_db": len(miss_db),
              "missing_local": len(miss_local),
              "dataset_stamp": last}          # NOT advanced yet

    if not miss_db and not miss_local:
        print(f"\n  BOTH SIDES ALREADY HOLD THE ENTIRE DELTA — nothing to do.")
        st_out |= {"dataset_stamp": now, "verdict": "already_current"}
        if a.repair:
            STATE.write_text(json.dumps(st_out, indent=1), encoding="utf-8")
        print(f"  ({time.time()-t0:.0f}s)")
        return 0

    print(f"\n  DIFFERENCE   local {len(miss_local):,} · supabase {len(miss_db):,}")
    if not a.repair:
        print("  (report only — re-run with --repair to populate both)")
        for d in (miss_db or miss_local)[:10]:
            print(f"      {d}")
        return 1

    # ---- REPAIR -----------------------------------------------------------
    import acris_lock
    import amap
    import map_delta
    import push_selection
    import supabase_sync as S

    need_map = sorted(set(miss_local) | set(miss_db))
    print(f"\n  MAPPING {len(need_map):,} documents at {MAP_CONC} concurrent")
    with acris_lock.AcrisLock("selection_daily", wait=True):
        asyncio.run(amap.run(need_map, conc=MAP_CONC))
    # ⚠ RE-READ FROM THE FILE. amap.run halts the gather on a refusal and
    # returns normally either way, so "it came back" is not evidence anything
    # was written — and the watermark depends on this answer.
    after, _ = map_delta.ids_from(HERE / "docmaps.jsonl", "doc_id")
    done = [d for d in need_map if d in after]
    print(f"    mapped {len(done):,} of {len(need_map):,}   (local now holds them)")
    note_local(done)          # keep the index honest until the next full audit

    maps = {}
    with open(HERE / "docmaps.jsonl", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("doc_id") in after:
                maps[r["doc_id"]] = r
    rows_out = []
    for d in done:
        m = dict(maps.get(d) or {"doc_id": d})
        m.setdefault("doc_type", (live.get(d) or {}).get("doc_type"))
        rec = (live.get(d) or {}).get("recorded_datetime")
        m.setdefault("recorded", rec[:10] if rec else None)
        rows_out.append(push_selection.row(m))
    if rows_out:
        S.push(TABLE, rows_out, "document_id", "document_map")
        print(f"    upserted {len(rows_out):,} into {TABLE}")

    # ---- RE-VERIFY THE SAME IDS. A repair that is not re-checked is a hope. --
    print("\n  RE-CHECKING the delta ids on both sides")
    in_db2 = held_by_db(url, key, ids)
    in_local2 = held_by_local(ids)
    still_db = [d for d in ids if d not in in_db2]
    still_local = [d for d in ids if d not in in_local2]
    print(f"    supabase missing {len(still_db):,} · local missing {len(still_local):,}")

    ok = not still_db and not still_local
    st_out |= {"mapped": len(done), "upserted": len(rows_out),
               "still_missing_db": len(still_db),
               "still_missing_local": len(still_local),
               "verdict": "repaired" if ok else "incomplete"}
    # ⚠ ADVANCE ONLY ON A CLEAN RE-CHECK. Whatever stopped this — a refusal, a
    # document with no map — must still be visible to tomorrow's run.
    if ok:
        st_out["dataset_stamp"] = now
        print(f"    watermark advanced to {now}")
    else:
        print(f"    ⚠ watermark HELD at {last} — {len(still_db)+len(still_local)} "
              f"id(s) unresolved, tomorrow will see them again")
    STATE.write_text(json.dumps(st_out, indent=1), encoding="utf-8")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("\t".join(str(x) for x in (
            time.strftime("%Y-%m-%d %H:%M"), st_out["verdict"], len(ids),
            len(miss_local), len(miss_db), len(rows_out),
            f"{time.time()-t0:.0f}s")) + "\n")
    print(f"\n  ({time.time()-t0:.0f}s)   state -> {STATE.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
