"""THE ACRIS SUPPORT INDEX, KEPT CURRENT — delta only, O(what changed).

    python index_daily.py            # report only
    python index_daily.py --apply    # write the delta and advance the watermark

⚠ THE BASELINE IS PULLED ONCE; AFTER THAT ONLY THE DELTA IS EVER TOUCHED.
`pull_index_fast.py` fetches all 100,764,843 rows in about an hour. Re-running it
nightly to find the few thousand rows that moved would be the same mistake the
selection job already corrected: cost tracking the CORPUS instead of the CHANGE.
Socrata stamps every row with `:updated_at`, so the question is one query per
dataset.

⚠ AND THIS CANNOT REPLACE THE BASELINE, ONLY EXTEND IT. A forward-only watermark
inherits every gap it already has and reports clean forever — it cannot see a row
withdrawn or re-keyed. `pull_index_fast.py` remains the periodic ground truth,
the same way `selection_cross.py` does for the doc-id map. Two schedules, or the
cheap check gets mistaken for a complete one.

⚠ THE WATERMARK ADVANCES ONLY AFTER THE ROWS ARE ON DISK, NEVER ON A LOOK. The
sibling job learned this the expensive way: state saved before the work meant a
report-only run moved the cutoff and the next real run found nothing, with 28,196
documents permanently behind it while it printed success.

⚠ THE STAMP IS READ BEFORE THE PULL, so anything landing mid-run is re-shown
tomorrow rather than stepped over.

Deltas are appended to `index_full/<name>.delta.jsonl.gz` rather than merged into
the baseline file: an append cannot corrupt the ground truth, and a reader that
wants "current" reads baseline + delta with the delta winning. Merging nightly
would rewrite a 1 GB gzip to add a few thousand rows, and a rewrite that fails
halfway destroys the thing it was updating.
"""
from __future__ import annotations

import argparse
import gzip
import json
import pathlib
import sys
import time
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import bulk

OUTDIR = HERE / "index_full"
STATE = HERE / "_index_daily_state.json"
LOG = HERE / "_index_daily.tsv"
BASE = HERE / "_index_fast_state.json"

SETS = [
    ("master",     "bnx9-e6tj"),
    ("legals",     "8h5j-fqxa"),
    ("parties",    "636b-3b5g"),
    ("references", "pwkr-dpni"),
    ("remarks",    "9p4w-7npp"),
]
PAGE = 50000


def stamp(ds):
    r = bulk.socrata(ds, select="max(:updated_at) as mx", paginate=False, limit=1)
    return r[0]["mx"] if r else None


def since(ds, mark):
    """Rows touched since `mark`. Paged shallowly — a delta is small, and if it
    ever is not, the count is printed rather than silently truncated."""
    out, off = [], 0
    while True:
        p = {"$limit": PAGE, "$offset": off, "$order": ":id",
             "$where": f":updated_at > '{mark}'", "$$app_token": bulk.TOKEN}
        rows = bulk._get(f"https://data.cityofnewyork.us/resource/{ds}.json?"
                         + urllib.parse.urlencode(p))
        out.extend(rows)
        if len(rows) < PAGE:
            return out
        off += PAGE
        if off > 5_000_000:
            # ⚠ A DELTA THIS SIZE IS NOT A DELTA. Something reset :updated_at
            # across the dataset; re-run the baseline rather than pretending
            # this is an increment.
            raise SystemExit(
                f"  {ds}: delta exceeded 5,000,000 rows — this is a republish, "
                f"not a change set. Re-run pull_index_fast.py for the baseline.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    base = json.loads(BASE.read_text(encoding="utf-8")) if BASE.exists() else {}

    print("ACRIS SUPPORT INDEX — daily delta\n")
    total_new, missing_base = 0, []
    for name, ds in SETS:
        if not base.get(name, {}).get("complete"):
            missing_base.append(name)
            print(f"  {name:<11} NO BASELINE — run pull_index_fast.py first")
            continue
        mark = st.get(name, {}).get("stamp")
        if not mark:
            # First run after a baseline: seed from the baseline's finish time.
            mark = base[name].get("stamp") or stamp(ds)
            st.setdefault(name, {})["stamp"] = mark
            print(f"  {name:<11} seeding watermark at {mark}")
            continue
        now = stamp(ds)                      # ⚠ read BEFORE the pull
        rows = since(ds, mark)
        total_new += len(rows)
        print(f"  {name:<11} {len(rows):>9,} rows changed since {mark}")
        if not rows or not a.apply:
            continue
        f = OUTDIR / f"{name}.delta.jsonl.gz"
        with gzip.open(f, "ab", compresslevel=1) as fh:
            fh.write("".join(json.dumps(r) + "\n" for r in rows).encode())
        # ⚠ ONLY NOW.
        st[name] = {"stamp": now, "last_delta": len(rows),
                    "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        print(f"    -> {f.name}  (+{len(rows):,})")

    if a.apply:
        STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M')}\t{total_new}\t"
                     f"{time.time()-t0:.0f}s\n")
    print(f"\n  {total_new:,} changed rows total   ({time.time()-t0:.0f}s)")
    if missing_base:
        print(f"  ⚠ no baseline for: {', '.join(missing_base)} — the delta for "
              f"these means nothing until pull_index_fast.py has run")
        return 2
    if not a.apply and total_new:
        print("  (report only — re-run with --apply to write and advance)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
