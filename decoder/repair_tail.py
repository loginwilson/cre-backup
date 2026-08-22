"""Repair the tail range that the open-sentinel bug truncated.

    python repair_tail.py                 # all datasets with a shortfall
    python repair_tail.py master legals

⚠ WHAT WENT WRONG, PRECISELY. `ranges_for()` ended its last partition at the
sentinel "￿". When that partition came back at exactly $limit, the splitter
called midpoint("FT_49900", "￿"); with an upper bound outside the alphabet
it fell back to ALPHA's own midpoint, 'c' — above every real document_id. So the
"split" only trimmed the top and never divided the data. The range kept
returning $limit, kept being split, and silently dropped everything past the
cut: 23,010 master rows, ALL of them FT_4990*. No request failed and nothing was
logged. The only symptom was a short total, which is why the pull compares its
own row count to the live count rather than trusting that it finished.

⚠ THE DAMAGE IS BOUNDED AND KNOWABLE. Every partition below "FT_49900" had a
real prefix on both sides, so midpoint() always had a common prefix to work from
and those ranges are sound. Only ids >= "FT_49900" are suspect — and a truncated
fetch cuts mid-result, so a document at the boundary can be PARTIALLY present.
Repair therefore drops the whole suspect range from the file and rebuilds it,
rather than topping up the ids that appear to be missing.
"""
from __future__ import annotations

import gzip
import json
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import pull_index_fast as P

CUT = "FT_49900"          # everything at or above this is rebuilt


def tail_ranges():
    """Fine partitions covering [CUT, top). Small enough to need no splitting."""
    out = []
    for a in P.DIGITS:
        for b in P.DIGITS:
            p = CUT + a + b
            out.append((p, P.next_key(p)))
    out.append((P.next_key(CUT), "￿"))
    return out


def repair(name, ds):
    src = P.OUTDIR / f"{name}.jsonl.gz"
    if not src.exists():
        print(f"  {name:<11} (absent)"); return
    live = P.count(ds)
    t0 = time.time()

    # 1. Rebuild the suspect range from scratch.
    rows_new, bad = [], []
    def one(b):
        try:
            return b, P.fetch(ds, b[0], b[1])
        except Exception as e:
            return b, e
    with ThreadPoolExecutor(max_workers=P.WORKERS) as ex:
        for b, r in ex.map(one, tail_ranges()):
            if isinstance(r, Exception):
                bad.append((b[0], str(r)[:50])); continue
            # ⚠ A full page here would mean the rebuild is truncated too.
            if len(r) >= P.LIMIT:
                bad.append((b[0], f"still full at {P.LIMIT:,}")); continue
            rows_new.extend(r)
    if bad:
        print(f"  {name:<11} ABORTED — {len(bad)} tail range(s) unusable: "
              f"{bad[:3]}")
        return
    print(f"  {name:<11} rebuilt tail: {len(rows_new):,} rows "
          f"({time.time()-t0:.0f}s)")

    # 2. Rewrite the file: everything below CUT, then the rebuilt tail.
    tmp = P.OUTDIR / f"{name}.repair.jsonl.gz"
    kept = dropped = 0
    with gzip.open(src, "rb") as fin, gzip.open(tmp, "wb", compresslevel=1) as fout:
        for line in fin:
            try:
                d = json.loads(line).get("document_id") or ""
            except Exception:
                d = ""
            if d >= CUT:
                dropped += 1
                continue
            fout.write(line)
            kept += 1
        fout.write("".join(json.dumps(r) + "\n" for r in rows_new).encode())
    total = kept + len(rows_new)
    ok = total == live
    print(f"    kept {kept:,} · dropped {dropped:,} · added {len(rows_new):,} "
          f"-> {total:,}   live {live:,}   {'MATCH' if ok else 'STILL SHORT'}")
    if not ok:
        # ⚠ DO NOT SWAP IN A FILE THAT DOES NOT RECONCILE. Leave the original in
        # place and the repair beside it, so the next reader sees the problem
        # instead of inheriting a confidently wrong file.
        print(f"    ⚠ leaving {src.name} untouched; repair kept as {tmp.name}")
        return
    bak = P.OUTDIR / f"{name}.prerepair.jsonl.gz"
    src.replace(bak)
    tmp.replace(src)
    print(f"    swapped in · previous file kept as {bak.name}")

    st = json.loads(P.STATE.read_text(encoding="utf-8")) if P.STATE.exists() else {}
    st.setdefault(name, {}).update({"rows": total, "live": live,
                                    "complete": True, "repaired_tail": True})
    P.STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


def main():
    which = sys.argv[1:]
    print(f"REPAIRING THE TAIL RANGE (>= {CUT})\n")
    for name, ds in P.SETS:
        if which and name not in which:
            continue
        repair(name, ds)
    print()


if __name__ == "__main__":
    main()
