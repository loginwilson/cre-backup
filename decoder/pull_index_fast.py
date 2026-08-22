"""THE ACRIS SUPPORT INDEX, PULLED BY PARTITION — no deep offsets, no paging.

    python pull_index_fast.py                # all five, spine order
    python pull_index_fast.py parties
    python pull_index_fast.py --verify

⚠ $offset IS THE BOTTLENECK AND IT GETS WORSE AS THE PULL SUCCEEDS. Measured
2026-08-14 on PARTIES (46.5M rows), 20,000 rows per request:

    offset          0     1.1s
    offset  1,000,000     4.5s
    offset  5,000,000     7.6s
    offset 20,000,000    21.4s
    offset 40,000,000    23.7s        ~850 rows/s — a 21x collapse

The server walks every skipped row. So a straight paged pull starts fast, looks
healthy for the first third, and then crawls — and the cumulative rows/s figure
hides it, because early speed keeps the average up. The instantaneous rate on
master had already halved (19,000 -> 10,400) by 43%.

⚠ THE FIX IS TO PARTITION, NOT TO PARALLELISE HARDER. Filtering
`document_id >= lo AND document_id < hi` with `$order=document_id` is an index
range scan and stays FLAT: 2.4s at offset 0, 2.1s at offset 500,000 inside the
same partition. Five workers on deep offsets is five slow requests.

⚠ AND THE PARTITIONS ARE SIZED SO NOTHING IS PAGED. `document_id` is NOT unique
in PARTIES or LEGALS — several rows share one document — so paging within a
partition by document_id would reproduce the exact instability that $order
exists to prevent (correct totals, silently duplicated and dropped rows).
Ordering by `:id` instead is stable but defeats the index: measured 28-67s
versus 2.4s. There is no fast, stable, paged option.

So a partition is split until it fits in ONE request. A response that comes
back exactly at the limit is treated as OVERFULL and subdivided — never as
complete. That is the same rule as `bulk.socrata`'s `truncated` flag: a result
whose length equals the limit is not evidence of a complete result.

⚠ EVERY PARTITION IS COUNTED FIRST AND CHECKED AFTER. The count localises the
split and then proves the pull: rows fetched must equal rows counted, per
partition, or the partition is reported FAILED rather than written.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import pathlib
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import bulk

# ⚠ OUTPUT GOES TO THE CORPUS DRIVE, NOT THE CODE DRIVE. On 2026-08-18 this
# wrote to C: while the corpus lived on D:, and a 27.8M-row pull filled C:
# to ZERO bytes — three of five datasets died mid-write with Errno 28 and
# personal_parties.jsonl.gz was left TRUNCATED but present, which is the
# worst possible state: a file that looks pulled. D: has 18 TB free.
import os as _os
OUTDIR = pathlib.Path(_os.environ.get("ACRIS_INDEX_OUT")
                      or "D:/acris/01-specification/index/index_staging")
STATE = HERE / "_index_fast_state.json"
LOCK = HERE / "_index_fast.lock"

SETS = [
    ("master",     "bnx9-e6tj"),
    ("legals",     "8h5j-fqxa"),
    ("parties",    "636b-3b5g"),
    ("references", "pwkr-dpni"),
    ("remarks",    "9p4w-7npp"),
]
LIMIT = 50000                 # measured honoured
WORKERS = bulk.WORKERS        # 5; 8 is throttled back to serial speed
# Seed partitions: the natural high-order split of an ACRIS document_id —
# "2003".."2026" for digital, "BK_n"/"FT_n" for the book and film eras.
SEEDS = ([str(y) for y in range(1960, 2027)]
         + [f"BK_{i}" for i in range(10)] + [f"FT_{i}" for i in range(10)])
ALPHA = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
DIGITS = "0123456789"


def alive(pid):
    import subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                             capture_output=True, text=True, timeout=15).stdout
        return str(pid) in out
    except Exception:
        return True           # cannot prove it is dead -> assume alive


class SingleRun:
    """⚠ ONE WRITER. Three copies of the previous puller ran at once because two
    launches printed no log and looked like failures. All three appended to the
    same gzip; nothing errored and the file was interleaved garbage."""
    def __enter__(self):
        if LOCK.exists():
            try:
                pid = int(LOCK.read_text().strip() or 0)
            except ValueError:
                pid = 0
            if pid and alive(pid):
                raise SystemExit(f"  ALREADY RUNNING as PID {pid} — refusing "
                                 f"a second writer. Remove {LOCK.name} if dead.")
            print(f"  stale lock from PID {pid} — taking over")
        LOCK.write_text(str(os.getpid()))
        return self

    def __exit__(self, *e):
        LOCK.unlink(missing_ok=True)


def next_key(s):
    """Smallest key greater than every id starting with `s` — WITH CARRY.

    ⚠ Bumping the last character produced a false 660,708-document shortfall
    elsewhere in this project: "2009" -> "200:" reads as an EMPTY RANGE under a
    non-C collation. Carrying keeps every bound in the data's own character
    class ("2009" -> "2010")."""
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
    return s + "￿"


def where(lo, hi):
    return f"document_id >= '{lo}' AND document_id < '{hi}'"


def req(ds, params):
    return bulk._get(f"https://data.cityofnewyork.us/resource/{ds}.json?"
                     + urllib.parse.urlencode(params))


def count(ds, lo=None, hi=None):
    """⚠ NO BOUNDS MEANS NO $where. Passing lo="" built
    `document_id >= ''` which Socrata answered with 0, and the run reported
    "live count says 0" beside 165,451 rows it had just written — a check that
    contradicts the thing it is checking is a broken check, not a finding."""
    p = {"$select": "count(1) as n", "$$app_token": bulk.TOKEN}
    if lo is not None:
        p["$where"] = where(lo, hi)
    r = req(ds, p)
    return int(r[0]["n"]) if r else 0


def fetch(ds, lo, hi):
    """One partition in ONE request. Order is by document_id, which is an index
    range scan; no $offset is ever used, so non-unique ids cannot destabilise
    anything."""
    return req(ds, {"$limit": LIMIT, "$order": "document_id",
                    "$where": where(lo, hi), "$$app_token": bulk.TOKEN})


def fetch_doc(ds, doc):
    """Every row of ONE document, paged.

    ⚠ A SINGLE DOCUMENT CAN EXCEED THE PAGE LIMIT, AND NO RANGE SPLIT CAN FIX
    THAT. Splitting divides the id space, but a document cannot be separated
    from itself: every child still contains the whole document, so the descent
    yields ten empty siblings per level and never converges. It does not look
    stuck — requests climb steadily and the queue even drains, because the empty
    siblings pop while one hot chain descends forever.

    Measured 2026-08-14: parties sat at EXACTLY 31,898,850 rows for ten minutes
    while requests went 3,800 -> 5,080. The arithmetic on the queue (-114 over
    1,280 requests) resolves to 106 splits and ~1,174 zero-row children — 106x11
    almost exactly. Killed at 68.5%.

    ⚠ $offset IS SAFE HERE AND NOWHERE ELSE IN THIS FILE. It collapses on deep
    pagination (23.7s at offset 40M) and silently drops and duplicates rows
    without a total sort. Neither applies to one document's rows ordered by
    :id: the offsets stay in the tens of thousands and :id is unique.
    """
    out, off = [], 0
    while True:
        page = req(ds, {"$limit": LIMIT, "$offset": off, "$order": ":id",
                        "$where": f"document_id = '{doc}'",
                        "$$app_token": bulk.TOKEN})
        out.extend(page)
        if len(page) < LIMIT:
            return out
        off += LIMIT


def after(doc):
    """The next id above `doc`, staying inside the data's character class.

    ⚠ Past position 3 an ACRIS id is digits only, so nothing sorts between
    `doc` and `doc + "0"`. Using a sentinel outside that class is what put a
    LETTER in numeric id space and cost 202,275 legals rows.
    """
    return doc + "0"


def children(prefix):
    """⚠ ONE LEVEL DEEPER THAN THE PREFIX, NOT THE COMMON PREFIX. The first
    version split at the common prefix of (lo, hi) — for ["2003","2004") that is
    "200", whose only child inside the range is "2003" again. It returned the
    partition it was asked to divide, so the planner ran its full depth budget
    reporting "24 fit · 8 overfull" eight times without ever descending. A
    splitter that can return its own input cannot terminate, and it does not
    look stuck: it prints steady progress.

    ⚠ DIGITS ONLY BEYOND THE ERA MARKER — measured, not assumed. Over 3,000,000
    local document_ids the character set by position is:
        pos 0 [2BF] · pos 1 [0KT] · pos 2 [012_] · pos 3+ [0123456789]
    So an ACRIS id is an era marker ("2019", "BK_6", "FT_1") followed by digits.
    Splitting on all 64 characters would issue 54 requests per node that cannot
    match anything — a 6.4x tax on every level of the tree.
    """
    return [prefix + c for c in (DIGITS if len(prefix) >= 3 else ALPHA)]


PREFIX_COUNTS = HERE / "_id_prefix_counts.json"
TARGET = int(LIMIT * 0.8)          # aim under the cap; the guard catches the rest

# ⚠ SIZING BY THE AVERAGE FAILS WHERE THE VARIANCE IS HIGH, AND PARTIES IS THAT
# CASE. Rows-per-document averages 2.73, but a document can carry dozens of
# parties, so partitions built from the mean overflow constantly. Each overflow
# costs a wasted 50,000-row fetch AND splits into ten children that are often
# overfull too: the queue went 533 -> 2,195 while the row count sat frozen at
# 31,465,773 for four minutes. Churn, not progress.
#
# The guard was doing its job — it never wrote a truncated page — but a splitter
# that fires on most partitions is a sizing bug, not a splitting bug. Aiming far
# under the cap makes overflow rare instead of routine: more requests, no churn,
# and a predictable finish. Legals (1.33 rows/doc, low variance) never needed it.
TARGET_BY_SET = {"parties": 12000}


def ranges_for(rows_per_doc, target=None):
    """Partition bounds computed from the LOCAL id histogram — zero planning
    queries against the server.

    ⚠ FETCH-AND-SPLIT WAS WASTING WHOLE PAGES. An overfull partition still
    transfers its 50,000 rows before we learn it is overfull, and master needs
    three levels of splitting, so the discarded traffic dwarfed the kept traffic:
    155 rows written after 80 requests, with the work queue still growing.
    Counting server-side instead is cheap per query but needs ~9,000 of them.

    Neither is necessary. We already hold all 17,049,742 document_ids, so the
    sizes are knowable offline: one 13-second pass gives 9,148 eight-character
    prefixes and their document counts. Consecutive prefixes are merged until a
    group would exceed the target.

    ⚠ THE RANGES TILE THE WHOLE KEY SPACE, so an id we have never seen still
    lands in exactly one partition. Each group ends at the NEXT group's first
    prefix rather than at its own last prefix + 1; the first starts below every
    key and the last runs to the top. A partition scheme built only from known
    ids would silently skip anything new.
    """
    counts = json.loads(PREFIX_COUNTS.read_text(encoding="utf-8"))
    keys = sorted(counts)
    per = max(1, int((target or TARGET) / max(rows_per_doc, 0.05)))
    groups, cur, tot = [], [], 0
    for k in keys:
        if cur and tot + counts[k] > per:
            groups.append(cur); cur, tot = [], 0
        cur.append(k); tot += counts[k]
    if cur:
        groups.append(cur)
    # ⚠ THE TOP BOUND MUST BE A REAL PREFIX, NOT AN OPEN SENTINEL, AND THIS COST
    # 23,010 ROWS. The last range used to be ("FT_49900", "￿"). When it came
    # back full the splitter took midpoint("FT_49900", "￿") — with a bound
    # outside the alphabet it picked ALPHA's midpoint, 'c', which is above every
    # real document_id. So each "split" trimmed only the top and never divided
    # the data: the partition kept returning exactly $limit, kept being split,
    # and quietly lost everything past the cut. Nothing failed and nothing was
    # logged; the only symptom was a short total.
    #
    # Bounding the last group by next_key() of its own last prefix keeps every
    # range inside the data's character class, so midpoint() always has a common
    # prefix to work from. A separate open-ended tail range then catches ids
    # beyond anything we have seen locally — normally empty, never assumed so.
    bounds = []
    for i, g in enumerate(groups):
        lo = "" if i == 0 else g[0]
        hi = groups[i + 1][0] if i + 1 < len(groups) else next_key(g[-1])
        bounds.append((lo, hi))
    if groups:
        bounds.append((next_key(groups[-1][-1]), "￿"))
    return bounds


def pull(name, ds, st):
    if st.get(name, {}).get("complete"):
        print(f"  {name:<11} already complete ({st[name]['rows']:,}) — skipping")
        return
    OUTDIR.mkdir(exist_ok=True)
    out = OUTDIR / f"{name}.jsonl.gz"
    t0 = time.time()
    live = count(ds)
    rpd = live / 17_049_742
    work = ranges_for(rpd, TARGET_BY_SET.get(name))
    print(f"  {name:<11} {live:>12,} live rows · {rpd:.2f} rows/doc · "
          f"{len(work):,} partitions", flush=True)

    written = reqs = split_n = 0
    bad, hot = [], []
    with gzip.open(out, "wb", compresslevel=1) as f:
        while work:
            batch, work = work[:WORKERS * 4], work[WORKERS * 4:]

            def one(b):
                lo, hi = b
                try:
                    return b, fetch(ds, lo, hi)
                except Exception as e:
                    return b, e

            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                for b, rows in ex.map(one, batch):
                    reqs += 1
                    if isinstance(rows, Exception):
                        bad.append((b[0], str(rows)[:60])); continue
                    if len(rows) >= LIMIT:
                        # ⚠ AN OVERFULL PAGE IS ADVANCED BY THE DATA, NEVER BY A
                        # GUESSED SPLIT POINT. Splitting the id space blind fails
                        # in two ways that both look like healthy progress:
                        #
                        #   1. a document cannot be separated from itself — one
                        #      document_id with >= LIMIT rows makes every child
                        #      as big as its parent (parties, frozen at exactly
                        #      31,898,850 for 10 minutes, 2026-08-14);
                        #   2. when every cut lands in dead id space ABOVE the
                        #      data, the last tile inherits the whole parent and
                        #      lo just grows: references reached
                        #      [201907129999999999999999, 20191) — "20190712"
                        #      plus sixteen 9s — appending one more 9 per level.
                        #
                        # The rows in hand already ARE the answer for the bottom
                        # of the range, so keep them and resume from the last
                        # document boundary. Progress is guaranteed because
                        # last > first >= lo, and nothing is lost because every
                        # row of `last` is dropped here and re-read next time.
                        lo, hi = b
                        first, last = (rows[0].get("document_id"),
                                       rows[-1].get("document_id"))
                        if first and first == last:
                            # The whole page is ONE document — there is no
                            # boundary to resume from. Take it whole.
                            got = fetch_doc(ds, first)
                            f.write("".join(json.dumps(r) + "\n"
                                            for r in got).encode())
                            written += len(got)
                            hot.append((first, len(got)))
                            print(f"    ⚠ single-document overflow "
                                  f"{first} = {len(got):,} rows — paged whole",
                                  flush=True)
                            nxt = after(first)
                            if nxt < hi:
                                work.append((nxt, hi))
                            continue
                        keep = [r for r in rows
                                if r.get("document_id") != last]
                        f.write("".join(json.dumps(r) + "\n"
                                        for r in keep).encode())
                        written += len(keep)
                        work.append((last, hi))
                        split_n += 1
                        continue

                    if not rows:
                        continue
                    blob = "".join(json.dumps(r) + "\n" for r in rows)
                    f.write(blob.encode())
                    written += len(rows)
            el = time.time() - t0
            print(f"    {written:>12,} / {live:,}  {100*written/live:>5.1f}%  "
                  f"{written/el:>8,.0f} rows/s  {reqs:,} req  "
                  f"{len(work):,} queued  {el/60:>5.1f}m", flush=True)

    el = time.time() - t0
    ok = (written == live) and not bad
    # ⚠ RE-READ BEFORE WRITING. This dict was loaded at start-up and the file
    # is rewritten WHOLE, so anything another process recorded meanwhile is
    # erased. Measured: repair_tail.py fixed master and set rows=17,065,090
    # between two datasets; when legals finished, this line wrote back the stale
    # master entry and the board reported a 23,016-row shortfall against a file
    # that was already correct. The data was never wrong — the bookkeeping was,
    # which is worse, because it sends someone to re-fix a fixed thing.
    disk = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    disk[name] = {"rows": written, "live": live, "requests": reqs,
                  "splits": split_n, "failed": len(bad),
                  "seconds": round(el), "complete": ok}
    st.update(disk)
    STATE.write_text(json.dumps(disk, indent=1), encoding="utf-8")
    print(f"  {name:<11} {written:,} rows · {out.stat().st_size/1e6:,.0f} MB · "
          f"{el/60:.1f}m · {written/el:,.0f} rows/s · {reqs:,} requests"
          + ("" if ok else "   ⚠"))
    if written != live:
        print(f"    ⚠ live says {live:,} — difference {written-live:+,}")
    for pfx, why in bad[:8]:
        print(f"    ⚠ {pfx}: {why}")
    print()


def subdivide(lo, hi):
    """Tile [lo, hi) with sub-ranges whose bounds are DIGITS ONLY.

    ⚠ A MIDPOINT MAY NOT LIE BETWEEN ITS OWN ENDPOINTS. The previous splitter
    took a lexicographic midpoint over the full alphabet, so dividing
    ["20030130", "20030200") produced the bound "200301W" — a LETTER dropped
    into a numeric id space. ASCII says 'W' (0x57) sorts after '3' (0x33), but
    the column is text under a NON-C collation, where that ordering is not
    guaranteed. If the server disagrees, [lo, mid) and [mid, hi) do not tile
    [lo, hi): rows fall in neither half and vanish with no error. Legals lost
    202,275 rows this way, on top of the 26,700 the tail bug took.

    This is the same collation trap that once produced a false 660,708-document
    shortfall in `reconcile_selection.py` — there it was punctuation, here a
    letter, and both times the fix is to keep every bound inside the character
    class the data actually uses. See children(): positions 3+ are digits only.

    Tiling is explicit — [lo, first), [first, second), ..., [last, hi) — so the
    sub-ranges provably cover the parent with no gap and no overlap.

    ⚠ CUTTING ONLY AT THE COMMON PREFIX RETURNS THE PARENT'S OWN DATA. For
    ["2019", "2020") the common prefix is "20", so the candidate cuts are
    "200".."209" and the only one strictly inside the range is "202". That
    yields ["2019","202") — which still contains every 2019xxxxxxxx id — plus an
    empty tail. The "split" narrowed nothing, the child overflowed again, and the
    queue grew forever: measured 2026-08-14, parties froze at 31,652,944 rows
    while the work queue climbed 597 → 1,583 over four minutes.

    It looked like slow progress rather than a loop, which is what made it
    expensive. A splitter must descend into `lo`'s OWN subtree as well as cutting
    above it, so both sets of candidates are generated and merged.
    """
    i = 0
    while i < min(len(lo), len(hi)) and lo[i] == hi[i]:
        i += 1
    pre = lo[:i]
    cuts = sorted({c for c in
                   [pre + d for d in DIGITS]      # siblings above lo
                   + [lo + d for d in DIGITS]     # INTO lo's subtree
                   if lo < c < hi})
    if not cuts:
        return []
    out, prev = [], lo
    for c in cuts:
        out.append((prev, c))
        prev = c
    out.append((prev, hi))
    return out



def verify():
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    for name, ds in SETS:
        f = OUTDIR / f"{name}.jsonl.gz"
        if not f.exists():
            print(f"  {name:<11} (absent)"); continue
        rows, seen = 0, set()
        with gzip.open(f, "rb") as fh:
            for line in fh:
                rows += 1
                try:
                    v = json.loads(line).get("document_id")
                except Exception:
                    continue
                if v:
                    seen.add(v)
        live = st.get(name, {}).get("live")
        flag = "" if live is None or rows == live else f"   ⚠ live {live:,}"
        print(f"  {name:<11} {rows:>12,} rows · {len(seen):>12,} distinct "
              f"documents{flag}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="*")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        return verify()
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    todo = [s for s in SETS if not a.which or s[0] in a.which]
    print(f"ACRIS SUPPORT INDEX — partitioned pull, {len(todo)} dataset(s)\n")
    t0 = time.time()
    with SingleRun():
        for name, ds in todo:
            pull(name, ds, st)
    print(f"  total {(time.time()-t0)/60:.1f} minutes -> {OUTDIR}")


if __name__ == "__main__":
    main()
