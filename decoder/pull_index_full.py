"""THE ENTIRE ACRIS SUPPORT INDEX — streamed to disk, resumable, in spine order.

    python pull_index_full.py                # all five, in order
    python pull_index_full.py master parties # named subsets
    python pull_index_full.py --verify       # re-count what is on disk vs live

⚠ ORDER IS NOT ARBITRARY — MASTER IS THE SPINE. Every other surface keys to
`document_id` and means nothing without the master row that says what the
document IS. Pull master first and every later file can be checked against it
as it lands; pull parties first and 46.5M rows sit on disk with no way to tell a
missing document from a document with no parties. Cheapest and least load-bearing
goes last, so an interrupted run always leaves the useful half done:

    MASTER      17,065,090   doc type, dates, amounts        THE SPINE
    LEGALS      22,727,180   BBLs — what property it touches
    PARTIES     46,540,137   names + party_type — THE ROLE CHANNEL
    REFERENCES   8,699,896   document-to-document links
    REMARKS      5,732,540   free text                       least structured

⚠ IT MUST STREAM. `bulk.socrata()` accumulates every row in a list and returns
it — fine for a doc type, fatal for PARTIES: 46.5M dicts is far past this
machine's memory, and the failure arrives forty minutes in. Each window of pages
is written and discarded, so peak memory is WORKERS x page, not the dataset.

⚠ $order IS MANDATORY AND ITS ABSENCE IS INVISIBLE. Measured 2026-08-06: paging
with $offset and no $order returned the correct TOTAL every time while silently
duplicating some rows and dropping others — two runs an hour apart disagreed
with each other. The one check anybody runs on a bulk pull is a count, and that
is exactly the check this failure passes. `:id` is Socrata's own unique row id.

⚠ AND A COUNT IS NOT A PROOF OF COMPLETENESS EITHER. The tail is walked until a
page comes back short, because the dataset can grow mid-pull; and the finished
file's DISTINCT id count is reported next to the live count so a silent
duplication has somewhere to show up.
"""
from __future__ import annotations

import argparse
import gzip
import json
import pathlib
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import bulk

OUTDIR = HERE / "index_full"
STATE = HERE / "_index_full_state.json"

# name -> (dataset id, key column for the distinct check)
SETS = [
    ("master",     "bnx9-e6tj", "document_id"),
    ("legals",     "8h5j-fqxa", "document_id"),
    ("parties",    "636b-3b5g", "document_id"),
    ("references", "pwkr-dpni", "document_id"),
    ("remarks",    "9p4w-7npp", "document_id"),
]
PAGE = bulk.SOCRATA_LIMIT          # 50,000, measured honoured
WORKERS = bulk.WORKERS             # 5; 8 is throttled back to serial speed


LOCK = HERE / "_index_full.lock"


class SingleRun:
    """⚠ ONE WRITER, ENFORCED — CONCURRENT COPIES SILENTLY CORRUPT THE OUTPUT.

    Measured 2026-08-14: three instances of this script ran at once because two
    launch attempts LOOKED like they had failed (no log file appeared) and had
    in fact started. All three appended to the same `master.jsonl.gz` and all
    three rewrote the same state file. Nothing errored. The gzip grew at triple
    speed, which reads as good news, and the file was interleaved garbage.

    A resumable append-mode writer is exactly the shape that cannot detect this
    for itself, so the guard has to be at the door.
    """

    def __enter__(self):
        if LOCK.exists():
            try:
                pid = int(LOCK.read_text().strip() or 0)
            except ValueError:
                pid = 0
            if pid and _alive(pid):
                raise SystemExit(
                    f"  ALREADY RUNNING as PID {pid} — refusing to start a "
                    f"second writer.\n  If that process is dead, remove "
                    f"{LOCK.name} and re-run.")
            print(f"  stale lock from PID {pid} — taking over")
        LOCK.write_text(str(__import__("os").getpid()))
        return self

    def __exit__(self, *exc):
        LOCK.unlink(missing_ok=True)


def _alive(pid):
    import subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                             capture_output=True, text=True, timeout=15).stdout
        return str(pid) in out
    except Exception:
        return True          # ⚠ cannot prove it is dead -> assume it is alive


def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


def live_count(ds):
    r = bulk.socrata(ds, select="count(1) as n", paginate=False, limit=1)
    return int(r[0]["n"]) if r else None


def fetch(ds, off):
    p = {"$limit": PAGE, "$offset": off, "$$app_token": bulk.TOKEN,
         "$order": ":id"}          # ⚠ never remove — see module docstring
    return bulk._get(f"https://data.cityofnewyork.us/resource/{ds}.json?"
                     + urllib.parse.urlencode(p))


def pull(name, ds, key, st):
    OUTDIR.mkdir(exist_ok=True)
    out = OUTDIR / f"{name}.jsonl.gz"
    done = st.get(name, {})
    if done.get("complete"):
        print(f"  {name:<11} already complete "
              f"({done.get('rows', 0):,} rows) — skipping")
        return
    # ⚠ RESUME TRUNCATES TO A WHOLE PAGE. Appending after a partial page would
    # interleave a half-written record with the next pull's first row, and the
    # file would parse right up to the seam.
    start = done.get("rows_written", 0)
    start -= start % PAGE
    mode = "ab" if start else "wb"
    if start:
        print(f"  {name:<11} resuming at offset {start:,}")

    cnt = live_count(ds)
    print(f"  {name:<11} {cnt:>12,} live rows", flush=True)
    t0, written = time.time(), start
    with gzip.open(out, mode, compresslevel=6) as f:
        off = start
        while True:
            offsets = [off + i * PAGE for i in range(WORKERS)]
            if cnt is not None:
                offsets = [o for o in offsets if o < cnt + PAGE]
            if not offsets:
                break
            short = False
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                for rows in ex.map(lambda o: fetch(ds, o), offsets):
                    for r in rows:
                        f.write((json.dumps(r) + "\n").encode())
                    written += len(rows)
                    if len(rows) < PAGE:
                        short = True
            off += WORKERS * PAGE
            st[name] = {"rows_written": written, "complete": False,
                        "live_count": cnt}
            save_state(st)
            el = time.time() - t0
            rate = (written - start) / el if el else 0
            pct = f"{100*written/cnt:>5.1f}%" if cnt else "    ?"
            print(f"    {written:>12,} / {cnt:,}  {pct}  "
                  f"{rate:>8,.0f} rows/s  {el/60:>5.1f}m", flush=True)
            # ⚠ A SHORT PAGE IS THE ONLY REAL END-OF-DATA SIGNAL.
            if short:
                break
    st[name] = {"rows_written": written, "complete": True, "live_count": cnt,
                "seconds": round(time.time() - t0),
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    save_state(st)
    mb = out.stat().st_size / 1e6
    flag = "" if cnt is None or written == cnt else f"   ⚠ live said {cnt:,}"
    print(f"  {name:<11} DONE {written:,} rows · {mb:,.0f} MB gz · "
          f"{(time.time()-t0)/60:.1f}m{flag}\n")


def verify():
    """Distinct-key count per finished file, against the live count.

    ⚠ ROWS MATCHING IS NOT ENOUGH. The paging defect this file guards against
    keeps the row count correct while duplicating and dropping ids, so the
    distinct count is the check that can actually fail.
    """
    st = load_state()
    for name, ds, key in SETS:
        f = OUTDIR / f"{name}.jsonl.gz"
        if not f.exists():
            print(f"  {name:<11} (absent)")
            continue
        seen, rows = set(), 0
        with gzip.open(f, "rb") as fh:
            for line in fh:
                rows += 1
                try:
                    v = json.loads(line).get(key)
                except Exception:
                    continue
                if v:
                    seen.add(v)
        live = st.get(name, {}).get("live_count")
        ok = "" if live is None or rows == live else f"   ⚠ live {live:,}"
        print(f"  {name:<11} {rows:>12,} rows · {len(seen):>12,} distinct "
              f"{key}{ok}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="*", help="dataset names; default all")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        return verify()
    st = load_state()
    todo = [s for s in SETS if not a.which or s[0] in a.which]
    print(f"ACRIS SUPPORT INDEX — {len(todo)} dataset(s), spine order\n")
    t0 = time.time()
    with SingleRun():
        for name, ds, key in todo:
            pull(name, ds, key, st)
    print(f"  total {(time.time()-t0)/60:.1f} minutes")
    print(f"  -> {OUTDIR}    (then: python pull_index_full.py --verify)")


if __name__ == "__main__":
    main()
