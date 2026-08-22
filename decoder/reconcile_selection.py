"""EXACT RECONCILIATION: what is on disk vs what is in Supabase, per key slice.

    python reconcile_selection.py
    python reconcile_selection.py --drill 2003       # list the missing ids in a slice

⚠ AN ESTIMATE IS NOT A RECONCILIATION, AND SELECTION IS THE ONE PLACE THAT
CANNOT TOLERATE ONE. The map decides what acquisition fetches; a document
missing here is never downloaded, never decoded, and the event it records is
invisible to every later stage. "Within sampling error" is an acceptable answer
for a progress bar and an unacceptable one for an inventory.

⚠ count=exact ON THE WHOLE TABLE TIMES OUT (HTTP 500, 57014) and always will at
17M rows on this instance. But `document_id` is the primary key, so a RANGE
filter is an index scan: [2003 .. 2004) returned an exact 589,070 in 4.6s. The
total is therefore computed as a SUM OF EXACT SLICES rather than one estimate,
and any slice that still times out is split in half and retried until it fits.

⚠ THE DISK SIDE MUST COUNT DISTINCT IDS, NOT LINES. The table's primary key
collapses duplicates, and the mapper APPENDS - re-runs and delta runs write the
same doc_id again. Comparing line counts to row counts would report every
duplicate as a missing row and send someone hunting for data that was never
lost.

⚠ AND IT MUST READ EVERY FILE THAT WAS EVER PUSHED. acris_maps.jsonl,
_remaining_sorted.jsonl, docmaps.jsonl and census_maps.jsonl all landed in this
table. Omitting one would make the table look like it holds rows that "should
not exist" and invert the direction of the discrepancy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
FILES = ["acris_maps.jsonl", "_remaining_sorted.jsonl",
         "docmaps.jsonl", "census_maps.jsonl"]


def env():
    e = {}
    for line in open(r"C:\dev\acris-decoder.env", encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"')
    return e["ACRIS_SUPABASE_URL"].rstrip("/"), e["ACRIS_SUPABASE_SERVICE_KEY"]


def slice_of(doc_id: str) -> str:
    """Slice key = the first 4 characters. Matches the PK's natural ordering,
    so every slice is a contiguous index range on the server side."""
    return doc_id[:4]


def read_disk():
    """-> {slice: set_of_hashes}. Hashes, not strings: 17M ids as Python str is
    ~1.7 GB and this machine has ~6 GB free."""
    per = {}
    total_lines = 0
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
                h = int.from_bytes(hashlib.blake2b(d.encode(), digest_size=8)
                                   .digest(), "big")
                per.setdefault(slice_of(d), set()).add(h)
        total_lines += n
        print(f"    {name:26} {n:>12,} lines")
    distinct = sum(len(v) for v in per.values())
    print(f"    {'TOTAL':26} {total_lines:>12,} lines -> {distinct:,} distinct")
    return per, total_lines, distinct


def count_exact(url, key, lo, hi, depth=0):
    """Exact count for [lo, hi). Splits and retries on timeout.

    ⚠ THE BOUNDS MUST BE URL-ENCODED AND THIS COST A FALSE FINDING. next_key()
    increments the last character, so "2009" -> "200:" — and a raw colon in a
    PostgREST query string does not error, it silently returns ZERO. The only
    slices affected were the two ending in 9 (2009, 2019), which were duly
    reported as 660,708 missing documents. A plain fetch of the same range
    returned rows immediately. An empty result that arrives in 0.1s while its
    neighbours take 3s is a broken query, not an empty table.
    """
    lo_q, hi_q = urllib.parse.quote(lo, safe=""), urllib.parse.quote(hi, safe="")
    u = (f"{url}/rest/v1/document_map?select=document_id&limit=1"
         f"&document_id=gte.{lo_q}&document_id=lt.{hi_q}")
    r = urllib.request.Request(u, headers={
        "apikey": key, "Authorization": "Bearer " + key,
        "Prefer": "count=exact", "Range": "0-0"})
    # ⚠ A 500 HERE IS USUALLY THROTTLING, NOT SIZE. This instance returned
    # `57014 statement timeout` intermittently all day on slices that succeeded
    # minutes earlier, so splitting on the first failure subdivides a range that
    # was never too big — and burns the depth budget doing it. Retry the same
    # range first; only split when it fails repeatedly.
    for attempt in range(3):
        try:
            with urllib.request.urlopen(r, timeout=180) as f:
                return int(f.headers.get("content-range").split("/")[-1])
        except Exception:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
    try:
        raise RuntimeError("exhausted retries")
    except Exception:
        # ⚠ SPLIT RATHER THAN GIVE UP OR ESTIMATE. A slice that times out is a
        # slice that is too big, not one whose size is unknowable.
        if depth >= 6:
            raise
        mid = midpoint(lo, hi)
        if mid in (lo, hi):
            raise
        return (count_exact(url, key, lo, mid, depth + 1)
                + count_exact(url, key, mid, hi, depth + 1))


ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"


def midpoint(lo, hi):
    """Lexicographic midpoint, one character deeper than the common prefix."""
    i = 0
    while i < min(len(lo), len(hi)) and lo[i] == hi[i]:
        i += 1
    a = ALPHA.index(lo[i]) if i < len(lo) and lo[i] in ALPHA else 0
    b = ALPHA.index(hi[i]) if i < len(hi) and hi[i] in ALPHA else len(ALPHA) - 1
    if b - a > 1:
        return lo[:i] + ALPHA[(a + b) // 2]
    return lo[:i + 1] + ALPHA[len(ALPHA) // 2]


def next_key(s):
    """Smallest key greater than every id starting with `s` — WITH CARRY.

    ⚠ BUMPING THE LAST CHARACTER IS WRONG AND PRODUCED A FALSE 660,708-DOCUMENT
    SHORTFALL. "2009" -> "200:" looks right in ASCII ('9' is 0x39, ':' is 0x3A)
    but the column is TEXT under a non-C collation, where punctuation does not
    sort after digits. Postgres therefore read [2009, 200:) as an EMPTY RANGE,
    answered 0 in 0.1s, and the reconciler reported two entire years missing.
    The only slices affected were the two ending in 9 — which is exactly the
    tell: a defect that hits a arithmetically-defined subset, not a random one.

    Carrying instead keeps every bound inside the same character class as the
    data ("2009" -> "2010", "FT_4" -> "FT_5"), so the comparison never depends
    on how the collation orders punctuation.
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
    # Carried off the front: nothing can be greater within this width.
    return s + "￿"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drill", default=None,
                    help="slice prefix to enumerate missing ids for")
    a = ap.parse_args()
    url, key = env()

    print("  DISK SIDE")
    per, lines, distinct = read_disk()

    print("\n  SUPABASE SIDE (exact, per slice)")
    tot_db = 0
    rows = []
    failed = []
    for sl in sorted(per):
        t = time.time()
        # ⚠ ONE UNCOUNTABLE SLICE MUST NOT DISCARD THE OTHER THIRTY-ONE, NOR THE
        # four-minute disk pass that produced them. It is reported as UNCOUNTED
        # and excluded from the total, because a slice whose size is unknown is
        # not a slice whose size is zero.
        try:
            n = count_exact(url, key, sl, next_key(sl))
        except Exception as e:
            failed.append(sl)
            print(f"    {sl:6} disk {len(per[sl]):>9,}   db  UNCOUNTED  "
                  f"({type(e).__name__})", flush=True)
            continue
        tot_db += n
        d = len(per[sl])
        rows.append((sl, d, n, n - d))
        flag = "" if n == d else ("  <-- SHORT" if n < d else "  <-- EXTRA")
        print(f"    {sl:6} disk {d:>9,}   db {n:>9,}   diff {n-d:>+7,}"
              f"   {time.time()-t:>5.1f}s{flag}", flush=True)

    # ⚠ RE-ASK THE STRAGGLERS BEFORE CALLING THEM UNCOUNTABLE. Twice now a slice
    # has failed every in-place retry and every split, then answered in ONE
    # SECOND minutes later — FT_4 at the end of one pass, FT_40 at the start of
    # the next. The condition outlasts a 75s backoff but not the rest of the
    # pass, so the cheapest fix is to come back at the end rather than retry
    # harder in the moment. A slice reported UNCOUNTED should mean the table
    # genuinely would not answer, not that we asked at a bad minute.
    if failed:
        print(f"\n  RE-ASKING {len(failed)} straggler(s) after the pass")
        still = []
        for sl in failed:
            t = time.time()
            try:
                n = count_exact(url, key, sl, next_key(sl))
            except Exception as e:
                still.append(sl)
                print(f"    {sl:6} db  STILL UNCOUNTED  ({type(e).__name__})",
                      flush=True)
                continue
            tot_db += n
            d = len(per[sl])
            rows.append((sl, d, n, n - d))
            flag = "" if n == d else ("  <-- SHORT" if n < d else "  <-- EXTRA")
            print(f"    {sl:6} disk {d:>9,}   db {n:>9,}   diff {n-d:>+7,}"
                  f"   {time.time()-t:>5.1f}s{flag}", flush=True)
        failed = still

    print("\n  " + "=" * 62)
    print(f"    disk distinct doc_ids   {distinct:>12,}")
    print(f"    supabase exact rows     {tot_db:>12,}")
    print(f"    DIFFERENCE              {tot_db - distinct:>+12,}")
    if failed:
        print(f"\n    ⚠ {len(failed)} slice(s) UNCOUNTED: {failed}")
        print("      The total above EXCLUDES them and is therefore a LOWER BOUND,")
        print("      not a reconciliation. Re-run to settle them.")
    short = [r for r in rows if r[3] < 0]
    if short:
        print(f"\n    {len(short)} slice(s) SHORT — run --drill <slice> to list them:")
        for sl, d, n, diff in short:
            print(f"      {sl}  missing {-diff:,}")
    elif not failed:
        print("\n    EVERY SLICE MATCHES EXACTLY — selection is reconciled.")

    if a.drill:
        sl = a.drill
        print(f"\n  DRILL {sl}: fetching every id in this slice from the table")
        got, off = set(), 0
        while True:
            u = (f"{url}/rest/v1/document_map?select=document_id"
                 f"&document_id=gte.{urllib.parse.quote(sl, safe=chr(0))}"
                 f"&document_id=lt.{urllib.parse.quote(next_key(sl), safe=chr(0))}"
                 f"&order=document_id&limit=1000&offset={off}")
            r = urllib.request.Request(u, headers={
                "apikey": key, "Authorization": "Bearer " + key})
            with urllib.request.urlopen(r, timeout=180) as f:
                batch = json.loads(f.read().decode())
            if not batch:
                break
            got.update(int.from_bytes(
                hashlib.blake2b(x["document_id"].encode(), digest_size=8)
                .digest(), "big") for x in batch)
            off += len(batch)
        missing = per.get(sl, set()) - got
        print(f"    disk {len(per.get(sl, set())):,}  db {len(got):,}  "
              f"missing {len(missing):,}")
        out = HERE / f"_missing_{sl}.txt"
        # Re-scan to recover the STRING ids for the missing hashes.
        want, found = set(missing), []
        for name in FILES:
            p = HERE / name
            if not p.exists():
                continue
            with open(p, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        d = json.loads(line).get("doc_id")
                    except Exception:
                        continue
                    if not d or slice_of(d) != sl:
                        continue
                    h = int.from_bytes(hashlib.blake2b(
                        d.encode(), digest_size=8).digest(), "big")
                    if h in want:
                        found.append(d); want.discard(h)
        out.write_text("\n".join(sorted(found)), encoding="utf-8")
        print(f"    -> {out}  ({len(found):,} ids)")


if __name__ == "__main__":
    main()
