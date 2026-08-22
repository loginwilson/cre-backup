"""PROVE THE RICHMOND DETAIL INDEX IS COMPLETE — and close the gap until it is.

    ACRIS_CORPUS_ROOT=D:/acris python rc_detail_verify.py          report the gap
    ACRIS_CORPUS_ROOT=D:/acris python rc_detail_verify.py --fix    re-fetch until dry

⚠ VERIFY AGAINST THE WORKLIST, NOT AGAINST THE PULL'S OWN OUTPUT. The denominator
is the 2,426,404 distinct internal_ids derived from the block ledger. Counting
"how many records did I write" answers a different question and always agrees with
itself - that is how every silent loss in this project stayed invisible.

WHAT COUNTS AS DONE
    a record with an internal_id, no `err`, and no `miss`.
    An ERROR ROW IS NOT DONE. A transient URLError once marked a document complete
    forever because the resume logic added every id it saw; that is a permanent
    hole that grows with every network blip and reports itself as "already have".

⚠ LOOP UNTIL DRY, NOT UNTIL A COUNT. Re-fetch, re-measure, repeat while the gap
SHRINKS. Stop when it reaches zero, or when a round makes no progress - which
means the remainder is not transient and needs to be looked at, not retried
forever. Both outcomes are reported; neither is silently rounded to success.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import rc_source as RC
import rc_sync as RS

WORK = pathlib.Path("D:/acris/01-specification/index/rc_worklist.tsv")
OUT = pathlib.Path("D:/acris/01-specification/index/rc_detail.jsonl")
CONC = 56


def expected():
    """The denominator, from the ledger-derived worklist."""
    ids = {}
    with WORK.open(encoding="utf-8") as f:
        for line in f:
            i, _, t = line.rstrip("\n").partition("\t")
            if i:
                ids[i] = t
    return ids


def have():
    """internal_ids with a GOOD record, plus a tally of what went wrong."""
    good, bad = set(), collections.Counter()
    if not OUT.exists():
        return good, bad
    with OUT.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                bad["unparsable-line"] += 1
                continue
            i = r.get("internal_id")
            if not i:
                bad["no-internal-id"] += 1
                continue
            if r.get("err"):
                bad[r["err"]] += 1
                continue
            if r.get("miss"):
                bad["page-had-no-document"] += 1
                continue
            good.add(i)
    return good, bad


def fetch_missing(ids):
    tl = threading.local()
    stop = threading.Event()

    def one(i):
        if stop.is_set():
            return None
        for attempt in range(3):
            try:
                if not hasattr(tl, "w"):
                    tl.w = RS.Window("08/17/2026", "08/17/2026")
                d = tl.w.detail(i)
                if d is None:
                    return {"internal_id": i, "miss": True}
                d["internal_id"] = i
                return d
            except RC.Unauthorized:
                if hasattr(tl, "w"):
                    del tl.w
            except RC.Refused:
                stop.set()
                return {"internal_id": i, "err": "REFUSED"}
            except Exception as e:
                if attempt == 2:
                    return {"internal_id": i, "err": type(e).__name__}
                time.sleep(2 ** attempt)
        return {"internal_id": i, "err": "retry-exhausted"}

    n = 0
    with OUT.open("a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=CONC) as ex:
        for r in ex.map(one, ids):
            if r is None:
                continue
            if r.get("err") == "REFUSED":
                print("    REFUSED - stopping this round, no retry.")
                break
            f.write(json.dumps(r) + "\n")
            f.flush()
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--rounds", type=int, default=6)
    a = ap.parse_args()

    exp = expected()
    good, bad = have()
    missing = [i for i in exp if i not in good]
    print(f"  DENOMINATOR (ledger worklist) {len(exp):>12,}")
    print(f"  complete records              {len(good):>12,}")
    print(f"  MISSING                       {len(missing):>12,}"
          f"   ({100*len(missing)/max(len(exp),1):.3f}%)")
    if bad:
        print(f"  failure reasons on disk: {dict(bad)}")
    if not missing:
        print("\n  ✅ COMPLETE — every ledger document has a parsed detail record.")
        return
    if not a.fix:
        print("\n  --fix not given; nothing fetched.")
        return

    prev = len(missing)
    for rnd in range(1, a.rounds + 1):
        print(f"\n  round {rnd}: re-fetching {len(missing):,}")
        fetch_missing(missing)
        good, bad = have()
        missing = [i for i in exp if i not in good]
        print(f"    remaining {len(missing):,}")
        if not missing:
            print("\n  ✅ COMPLETE — gap closed to zero.")
            return
        if len(missing) >= prev:
            print(f"\n  ⚠ NO PROGRESS this round ({prev:,} -> {len(missing):,}). "
                  f"The remainder is NOT transient — stopping rather than "
                  f"retrying forever. Reasons on disk: {dict(bad)}")
            print("    sample:", missing[:10])
            return
        prev = len(missing)
    print(f"\n  ⚠ {len(missing):,} still missing after {a.rounds} rounds — reported, "
          f"not rounded to success.")


if __name__ == "__main__":
    main()
