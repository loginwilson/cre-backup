"""ACRIS SELECTION — the three-way cross, and the repair that follows it.

    python selection_cross.py              # report only
    python selection_cross.py --repair     # populate BOTH sides, then re-verify
    python selection_cross.py --repair --quiet-ok   # for the scheduled routine

⚠ THREE SIDES, THREE PAIRS, NEVER A CHAIN. The selection map exists in three
places and every one of them can move independently:

    ACRIS      the authority — what documents exist
    local      the jsonl map files on this machine
    Supabase   document_map, what acquisition will actually read

Checking ACRIS->local and local->Supabase and calling the third pair proven is
the mistake this file exists to prevent. A=B and B=C only implies A=C when all
three were measured the SAME WAY, and they are not: ACRIS counts rows (with
duplicate document_ids), local counts distinct ids across four append-only
files, Supabase counts primary keys. Each pair is therefore crossed on its own.

⚠ THE FAILURE THAT MOTIVATED THIS. `daily_delta.py` (Task Scheduler, 04:00)
runs `map_delta.py`, which diffs ACRIS against LOCAL FILES and writes to LOCAL
FILES. It never touches Supabase. So the first day it finds anything, disk goes
to 17,049,742 + N, `document_map` stays at 17,049,742, and nothing reports it —
while `document_map` is what acquisition reads. A document missing there is
never downloaded, never decoded, and the event it records is invisible to every
later stage.

⚠ A COUNT THAT WILL NOT COME BACK IS NOT A ZERO. Twice on 2026-08-13/14 a range
failed every in-place retry and every split, then answered in ONE SECOND minutes
later. So every HTTP call retries, stragglers are re-asked at the END of the
pass, and anything still unanswered is reported UNKNOWN and excluded from the
totals — which makes the total a LOWER BOUND and the run a non-reconciliation.
Never let an unanswered query become evidence of an empty table.

⚠ THIS JOB ONLY EVER ADDS. A document present on one side and absent from
another is always treated as "the other side is behind", never as "this side
should be pruned". Deletion needs a human looking at it.
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

# ⚠ LINE BUFFERING, BECAUSE THIS RUNS UNATTENDED AND REDIRECTED. Python block-
# buffers stdout when it is not a terminal, so a log tailed mid-run shows the
# last flushed line and nothing after it — a job doing 20 minutes of real work
# looks wedged at whatever it printed last. That reads as a hang and invites
# killing a run that was fine.
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

MASTER = "bnx9-e6tj"
TABLE = "document_map"
STATE = HERE / "_selection_cross_state.json"

# ⚠ ALL FOUR FILES, AND ONE DEFINITION OF "LOCAL". map_delta.MAPS lists three
# and omits _remaining_sorted.jsonl; reconcile_selection.FILES lists four. They
# happen to agree today (verified 2026-08-14: _remaining_sorted is a strict
# subset, 0 ids unique to it) but two definitions of the same word is how they
# stop agreeing quietly. This is the one the cross uses.
FILES = ("acris_maps.jsonl", "_remaining_sorted.jsonl",
         "docmaps.jsonl", "census_maps.jsonl")
MAP_CONC = 16


def env():
    for line in open(r"C:\dev\acris-decoder.env", encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "ACRIS_SUPABASE_URL":
                url = v.strip().strip('"').rstrip("/")
            elif k.strip() == "ACRIS_SUPABASE_SERVICE_KEY":
                key = v.strip().strip('"')
    return url, key


def h(doc_id: str) -> int:
    """17M ids as Python str is ~1.7 GB and this machine has ~6 GB free."""
    return int.from_bytes(hashlib.blake2b(doc_id.encode(), digest_size=8)
                          .digest(), "big")


def get(url, key, path, count=False, timeout=240, tries=4):
    """One PostgREST call, retried. Returns (payload, count) or raises."""
    hdr = {"apikey": key, "Authorization": "Bearer " + key}
    if count:
        hdr |= {"Prefer": "count=exact", "Range": "0-0"}
    req = urllib.request.Request(f"{url}/rest/v1/{path}", headers=hdr)
    last = None
    for a in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as f:
                if count:
                    cr = f.headers.get("Content-Range", "")
                    tail = cr.split("/")[-1] if "/" in cr else ""
                    # "*" means the server DECLINED to count. Not a zero.
                    if not tail.isdigit():
                        raise RuntimeError(f"server declined to count: {cr!r}")
                    return None, int(tail)
                return json.load(f), None
        except Exception as e:
            last = e
            if a < tries - 1:
                time.sleep(4 * (a + 1))
    raise RuntimeError(f"{path[:60]}: {type(last).__name__}: {last}")


# --------------------------------------------------------------------------
# THE THREE SIDES
# --------------------------------------------------------------------------
def local_side():
    """-> ({slice: {hash}}, distinct, lines). DISTINCT IDS, NOT LINES.

    ⚠ The mapper APPENDS, so re-runs and delta runs write the same doc_id
    again: 19,549,196 lines collapse to 17,049,742 ids. Comparing line counts
    to row counts would report every duplicate as a missing row.
    """
    per, lines = {}, 0
    for name in FILES:
        p = HERE / name
        if not p.exists():
            print(f"    {name:26} (absent)")
            continue
        n = 0
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    d = json.loads(line).get("doc_id")
                except Exception:
                    continue
                if not d:
                    continue
                n += 1
                per.setdefault(d[:4], set()).add(h(d))
        lines += n
        print(f"    {name:26} {n:>12,} lines")
    distinct = sum(len(v) for v in per.values())
    print(f"    {'TOTAL':26} {lines:>12,} lines -> {distinct:,} distinct")
    # ⚠ SPEND THE PASS ONCE. This audit is the only thing that reads all
    # 19,549,196 lines; the daily job needs the same membership answer and must
    # not pay four minutes a night to re-derive it. So write what we just
    # learned: every doc_id hash, sorted, 8 bytes each. selection_daily.py
    # binary-searches it. The index is DERIVED — rebuilt here every audit, so a
    # stale or deleted one costs a rebuild, never a wrong answer.
    keys = sorted(k.to_bytes(8, "big") for v in per.values() for k in v)
    tmp = HERE / "_local_ids.idx.tmp"
    tmp.write_bytes(b"".join(keys))
    tmp.replace(HERE / "_local_ids.idx")
    # The daily job's sidecar of additions is now folded in and must be cleared,
    # or it would keep asserting ids the rebuild already accounts for.
    (HERE / "_local_ids.new").unlink(missing_ok=True)
    print(f"    {'INDEX':26} {len(keys):>12,} hashes -> _local_ids.idx")
    return per, distinct, lines


def next_key(s):
    """Smallest key greater than every id starting with `s` — WITH CARRY.

    ⚠ BUMPING THE LAST CHARACTER PRODUCED A FALSE 660,708-DOCUMENT SHORTFALL.
    "2009" -> "200:" looks right in ASCII but the column is TEXT under a
    non-C collation, where punctuation does not sort after digits: Postgres read
    [2009, 200:) as an EMPTY RANGE and answered 0 in 0.1s. Only the slices
    ending in 9 were hit — an arithmetically-defined subset, which is the tell.
    """
    ch = list(s)
    i = len(ch) - 1
    while i >= 0:
        c = ch[i]
        if c == "9":
            ch[i] = "0"; i -= 1; continue
        if c == "Z":
            ch[i] = "A"; i -= 1; continue
        if c == "z":
            ch[i] = "a"; i -= 1; continue
        ch[i] = chr(ord(c) + 1)
        return "".join(ch)
    return s + "\uffff"


def db_slice_counts(url, key, slices):
    """Exact count per slice. count=exact on the WHOLE table times out at 17M;
    document_id is the primary key, so a RANGE filter is an index scan."""
    got, failed = {}, []
    for sl in sorted(slices):
        t = time.time()
        try:
            _, n = get(url, key, f"{TABLE}?select=document_id&limit=1"
                                 f"&document_id=gte.{urllib.parse.quote(sl, safe='')}"
                                 f"&document_id=lt.{urllib.parse.quote(next_key(sl), safe='')}",
                       count=True)
        except Exception:
            failed.append(sl)
            print(f"    {sl:6} db  UNCOUNTED", flush=True)
            continue
        got[sl] = n
        print(f"    {sl:6} db {n:>9,}   {time.time()-t:>5.1f}s", flush=True)
    # ⚠ RE-ASK THE STRAGGLERS. The bad condition outlasts a 75s backoff but not
    # the rest of the pass.
    if failed:
        print(f"    re-asking {len(failed)} straggler(s)")
        still = []
        for sl in failed:
            try:
                _, n = get(url, key, f"{TABLE}?select=document_id&limit=1"
                                     f"&document_id=gte.{urllib.parse.quote(sl, safe='')}"
                                     f"&document_id=lt.{urllib.parse.quote(next_key(sl), safe='')}",
                           count=True, tries=5)
                got[sl] = n
                print(f"    {sl:6} db {n:>9,}   (on re-ask)", flush=True)
            except Exception:
                still.append(sl)
                print(f"    {sl:6} STILL UNCOUNTED", flush=True)
        failed = still
    return got, failed


def db_ids_in_slice(url, key, sl):
    """Every id in one slice. Paginated explicitly — a page that comes back
    exactly at the cap is indistinguishable from a complete one."""
    out, off, PAGE = set(), 0, 10000
    lo = urllib.parse.quote(sl, safe="")
    hi = urllib.parse.quote(next_key(sl), safe="")
    while True:
        rows, _ = get(url, key, f"{TABLE}?select=document_id"
                                f"&document_id=gte.{lo}&document_id=lt.{hi}"
                                f"&order=document_id&limit={PAGE}&offset={off}")
        out.update(r["document_id"] for r in rows)
        if len(rows) < PAGE:
            return out
        off += PAGE


def acris_side():
    """Per-doc_type row counts — the CHEAP DETECTOR, one grouped query.

    ⚠ ROWS, NOT DISTINCT IDS. MASTER carries duplicate document_ids (17,065,090
    rows -> 17,049,742 ids), so a small positive gap here can be pure
    duplication. This localises WHICH types to id-diff; the id diff decides.
    """
    import bulk
    return {r["doc_type"]: int(r["n"]) for r in
            bulk.socrata(MASTER, select="doc_type,count(1) as n",
                         group="doc_type", paginate=True)}


def acris_ids(doc_type):
    import bulk
    out = {}
    for r in bulk.socrata(MASTER, where=f"doc_type='{doc_type}'",
                          select="document_id,doc_type,recorded_datetime",
                          paginate=True):
        out.setdefault(r["document_id"], r)
    return out


def strings_for(hashes, slices=None):
    """Recover the STRING ids for a set of hashes by re-scanning the map files."""
    want, found = set(hashes), {}
    for name in FILES:
        p = HERE / name
        if not p.exists():
            continue
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                d = r.get("doc_id")
                if not d or (slices and d[:4] not in slices):
                    continue
                k = h(d)
                if k in want:
                    found[d] = r
                    want.discard(k)
                    if not want:
                        return found
    return found


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repair", action="store_true",
                    help="populate BOTH sides and re-verify (default: report only)")
    ap.add_argument("--full-ids", action="store_true",
                    help="id-diff every ACRIS type, not only the movers")
    ap.add_argument("--quiet-ok", action="store_true",
                    help="print one line when all three already agree")
    a = ap.parse_args()
    t0 = time.time()
    url, key = env()
    st = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "repair": a.repair}

    print("ACRIS SELECTION — crossing ACRIS · local · Supabase\n")

    # ---- side 1: local -----------------------------------------------------
    print("  LOCAL")
    per, local_n, local_lines = local_side()

    # ---- side 2: Supabase, per slice --------------------------------------
    print(f"\n  SUPABASE ({len(per)} slices, exact)")
    db_counts, uncounted = db_slice_counts(url, key, per)
    db_n = sum(db_counts.values())

    # ---- side 3: ACRIS, cheap detector ------------------------------------
    print("\n  ACRIS")
    live_t = acris_side()
    live_rows = sum(live_t.values())
    print(f"    {len(live_t)} doc types · {live_rows:,} rows "
          "(rows, not distinct — duplicates live here)")

    print("\n  " + "=" * 64)
    print(f"    ACRIS rows              {live_rows:>12,}")
    print(f"    local distinct ids      {local_n:>12,}")
    print(f"    supabase exact rows     {db_n:>12,}"
          + ("   ⚠ LOWER BOUND" if uncounted else ""))
    if uncounted:
        print(f"    ⚠ {len(uncounted)} slice(s) UNKNOWN: {uncounted}")
        print("      This run is NOT a reconciliation. Re-run to settle them.")

    # ---- PAIR A: local <-> Supabase, per slice ----------------------------
    print(f"\n  PAIR A  local <-> supabase")
    a_short, a_extra = [], []
    for sl in sorted(per):
        if sl in uncounted:
            continue
        d, n = len(per[sl]), db_counts[sl]
        if n < d:
            a_short.append(sl)
            print(f"    {sl:6} disk {d:>9,}  db {n:>9,}  MISSING {d-n:>7,}")
        elif n > d:
            a_extra.append(sl)
            print(f"    {sl:6} disk {d:>9,}  db {n:>9,}  EXTRA IN DB {n-d:>7,}")
    if not a_short and not a_extra and not uncounted:
        print("    every slice matches exactly")

    # ---- PAIR B: ACRIS <-> local, and PAIR C: ACRIS <-> Supabase ----------
    # Both ride the SAME ACRIS pull, so crossing the third pair is nearly free.
    print(f"\n  PAIR B/C  ACRIS <-> local · ACRIS <-> supabase")
    local_all = set()
    for v in per.values():
        local_all |= v
    # A type whose ACRIS row count exceeds what we could possibly hold is a
    # mover. With no per-type view of local/db, the cheap screen is the total.
    movers = sorted(live_t) if a.full_ids else None
    if movers is None:
        # Total-level screen first: if ACRIS distinct <= local distinct there is
        # no evidence of a gap, and pulling 17M ids to prove it costs 45 min.
        gap_hint = live_rows - local_n
        print(f"    ACRIS rows minus local distinct: {gap_hint:+,}"
              "   (duplicates make a small positive normal)")
        movers = [] if gap_hint <= 0 else sorted(live_t)
        if gap_hint > 0:
            print(f"    positive — id-diffing all {len(movers)} types")
        else:
            print("    no evidence of documents missing locally "
                  "(--full-ids forces the exhaustive diff)")

    missing_local, missing_db, live_rec = set(), set(), {}
    for i, t in enumerate(movers, 1):
        lv = acris_ids(t)
        gap_l = {d for d in lv if h(d) not in local_all}
        missing_local |= gap_l
        live_rec.update({d: lv[d] for d in gap_l})
        if gap_l:
            print(f"    [{i}/{len(movers)}] {t:<10} live {len(lv):>9,} · "
                  f"MISSING LOCALLY {len(gap_l):>7,}", flush=True)

    st |= {"acris_rows": live_rows, "local_distinct": local_n,
           "supabase_rows": db_n, "uncounted_slices": uncounted,
           "slices_short_in_db": a_short, "slices_extra_in_db": a_extra,
           "missing_locally": len(missing_local)}

    # ⚠ RECORD WHICH DATASET STATE WAS PROVEN, NOT JUST THAT IT WAS PROVEN.
    # selection_daily.py starts from a clean audit, and without this it has no
    # exact point to start FROM — it fell back to a wider window. An audit that
    # says "everything reconciles" but not "as of when" cannot seed anything.
    try:
        import bulk   # ⚠ module-level `bulk` does not exist here — every other
                      # use in this file imports it inside its own function, and
                      # without this line the try/except below would swallow a
                      # NameError and record dataset_stamp: null forever.
        _s = bulk.socrata(MASTER, select="max(:updated_at) as mx",
                          paginate=False, limit=1)
        st["dataset_stamp"] = _s[0]["mx"] if _s else None
    except Exception as e:
        st["dataset_stamp"] = None
        print(f"    ⚠ could not stamp the audit ({str(e)[:50]}) — the daily "
              f"will fall back to a wider window")

    # ---- the verdict ------------------------------------------------------
    clean = (not uncounted and not a_short and not a_extra
             and not missing_local)
    if clean:
        print(f"\n  ALL THREE AGREE — {local_n:,} documents, crossed pairwise.")
        st["verdict"] = "clean"
        STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
        print(f"  ({time.time()-t0:.0f}s)")
        return 0

    print(f"\n  DIFFERENCES FOUND")
    print(f"    missing from local        {len(missing_local):>9,}")
    print(f"    slices short in supabase  {len(a_short):>9}")
    print(f"    slices extra in supabase  {len(a_extra):>9}")

    if not a.repair:
        print("\n  (report only — re-run with --repair to populate both sides)")
        st["verdict"] = "differences_reported"
        STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
        return 1

    # ---- REPAIR -----------------------------------------------------------
    import acris_lock
    import amap
    import map_delta
    import push_selection
    import supabase_sync as S

    # 1. ACRIS -> local. Map the documents no local file has.
    if missing_local:
        ids = sorted(missing_local)
        print(f"\n  MAPPING {len(ids):,} documents at {MAP_CONC} concurrent")
        with acris_lock.AcrisLock("selection_cross", wait=True):
            asyncio.run(amap.run(ids, conc=MAP_CONC))
        # ⚠ RE-READ FROM THE FILE. amap.run halts the gather on a refusal and
        # returns normally either way, so "it came back" is not evidence
        # anything was written.
        after, _ = map_delta.ids_from(HERE / "docmaps.jsonl", "doc_id")
        done = [d for d in ids if d in after]
        print(f"    mapped {len(done):,} of {len(ids):,}")
        st["mapped"] = len(done)

    # 2. local -> Supabase. Every slice the table is short on, drilled and
    #    upserted from the local records.
    pushed = 0
    for sl in a_short:
        have = db_ids_in_slice(url, key, sl)
        gap = per[sl] - {h(d) for d in have}
        recs = strings_for(gap, slices={sl})
        rows = [push_selection.row(r) for r in recs.values()]
        if rows:
            S.push(TABLE, rows, "document_id", "document_map")
            pushed += len(rows)
            print(f"    {sl:6} upserted {len(rows):,}")
    st["upserted"] = pushed

    # 3. Supabase -> local. A document the table holds and no file does is
    #    still a real document; write it back so local is not the laggard.
    recovered = 0
    for sl in a_extra:
        have = db_ids_in_slice(url, key, sl)
        gap = [d for d in have if h(d) not in per[sl]]
        if gap:
            with open(HERE / "docmaps.jsonl", "a", encoding="utf-8") as f:
                for d in gap:
                    f.write(json.dumps({"doc_id": d}) + "\n")
            recovered += len(gap)
            print(f"    {sl:6} wrote {len(gap):,} back to docmaps.jsonl")
    st["recovered_to_local"] = recovered

    # ---- RE-VERIFY. A repair that is not re-crossed is a hope. -------------
    print("\n  RE-VERIFYING")
    per2, local2, _ = local_side()
    db2, unc2 = db_slice_counts(url, key, per2)
    db2_n = sum(db2.values())
    print(f"\n    local distinct   {local2:>12,}")
    print(f"    supabase rows    {db2_n:>12,}"
          + ("   ⚠ LOWER BOUND" if unc2 else ""))
    ok = (local2 == db2_n) and not unc2
    print(f"    {'LOCAL AND SUPABASE AGREE' if ok else '⚠ STILL DIFFERENT'}")
    st |= {"verdict": "repaired" if ok else "repair_incomplete",
           "after_local": local2, "after_supabase": db2_n}
    STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
    print(f"\n  ({time.time()-t0:.0f}s)   state -> {STATE.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
