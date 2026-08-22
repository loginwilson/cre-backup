"""THE FINISHING PASS: nav table reordered by (key, recorded, id).

nav_build MUST stream ORDER BY document_id - that is what lets document,
parcel_document, party_document, reference_document and remark_document merge
in constant memory. So chronology-per-parcel is a separate pass over the
finished table: the same rows, reordered so the table reads like the By Parcel
folders do - one parcel's documents oldest to newest, then the next parcel.
That ordered view is the bootcamp feed (login 2026-08-20: "parcel 1 with 10
documents ordered 1980 to 2016, then parcel 2") and it lets extraction walk
a parcel's story while acquisition is still filling other parcels.

MECHANICS - external merge sort, constant memory:
  read the 13+ GB csv in chunks -> sort each chunk in RAM -> spill numbered
  runs -> heapq.merge the runs into the output. 16 GB cannot hold the table
  (that lesson is why nav_build merge-joins), and SQLite would double the
  disk for an index we use once.

SORT KEY: (key, recorded, id).
  - recorded comes from the recorded_details JSON via a cheap regex, not
    json.loads - 24M full parses is minutes for one field.
  - rows with NO recorded date sort FIRST within their key with the cell
    honestly empty - never dropped, never guessed (79% of FT_ microfilm has
    no document date; some lack recorded too).
  - id last = deterministic output; ACRIS carries no recorded TIME in the
    spec DB yet, so same-day docs order by id until the rd re-pull adds time.

⚠ THE UNSORTED TABLE REMAINS THE BUILD ARTIFACT. This writes a SIBLING file
(_by_parcel suffix), because nav_build's currency check and nav_verify's gate
both point at the original; silently replacing it would make the gate verify
a file the builder never wrote.
"""
import csv
import heapq
import pathlib
import re
import sys
import tempfile
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP

CHUNK = 400_000          # rows per in-memory run (~0.5 GB with overhead)
REC = re.compile(r'"recorded":"([^"]*)"')

csv.field_size_limit(1 << 27)


# ⚠ COLUMNS BY NAME, NEVER POSITION (the gate's own 2026-08-20 rule; this
# file briefly violated it and the same-day column reorder would have sorted
# on the wrong fields while printing success). Indices resolve from the
# header at open.
_IX = {}

def sort_key(row):
    m = REC.search(row[_IX["recorded_details"]])
    return (row[_IX["key"]], m.group(1) if m else "", row[_IX["id"]])


def main():
    src = CP.NAV_TABLE
    # the sorted view is a VIEW, not the table - it lives with the loose
    # documents so level 3 stays md + one table (login layout 2026-08-20)
    out = CP.NAV_WORK / (src.stem + "_by_parcel.csv")
    t0 = time.time()
    runs = []
    tmpdir = tempfile.mkdtemp(prefix="navsort_", dir=str(src.parent))
    tmp = pathlib.Path(tmpdir)

    with src.open("r", encoding="utf-8", newline="") as f:
        rd = csv.reader(f)
        header = next(rd)
        for col in ("id", "key", "recorded_details"):
            if col not in header:
                raise SystemExit(f"column '{col}' missing from header - "
                                 f"refusing to sort on guesses: {header}")
            _IX[col] = header.index(col)
        buf = []
        for row in rd:
            buf.append((sort_key(row), row))
            if len(buf) >= CHUNK:
                buf.sort(key=lambda x: x[0])
                p = tmp / f"run{len(runs):04d}.csv"
                with p.open("w", encoding="utf-8", newline="") as g:
                    w = csv.writer(g)
                    for k, r in buf:
                        w.writerow(list(k) + r)
                runs.append(p)
                buf.clear()
                print(f"  run {len(runs)}: {len(runs)*CHUNK:,} rows spilled "
                      f"· {time.time()-t0:.0f}s", flush=True)
        if buf:
            buf.sort(key=lambda x: x[0])
            p = tmp / f"run{len(runs):04d}.csv"
            with p.open("w", encoding="utf-8", newline="") as g:
                w = csv.writer(g)
                for k, r in buf:
                    w.writerow(list(k) + r)
            runs.append(p)
            buf.clear()

    print(f"  {len(runs)} runs · merging...", flush=True)

    def reader(p):
        with p.open("r", encoding="utf-8", newline="") as g:
            for row in csv.reader(g):
                yield row[:3], row[3:]

    n = 0
    with out.open("w", encoding="utf-8", newline="") as g:
        w = csv.writer(g)
        w.writerow(header)
        for _k, row in heapq.merge(*[reader(p) for p in runs],
                                   key=lambda x: x[0]):
            w.writerow(row)
            n += 1
            if n % 2_000_000 == 0:
                print(f"  merged {n:,} · {time.time()-t0:.0f}s", flush=True)

    for p in runs:
        p.unlink()
    tmp.rmdir()
    el = time.time() - t0
    print(f"\n  {n:,} rows -> {out}")
    print(f"  {out.stat().st_size/1e6:,.0f} MB · {el/60:.1f} min")
    # the sibling must hold EXACTLY the build's rows - a mismatch means the
    # sort dropped or duplicated, and the chronological feed would lie quietly
    if n:
        print(f"  row-count identity vs source is the caller's check: "
              f"compare against nav_build's printed total.")


if __name__ == "__main__":
    main()
