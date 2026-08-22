"""DOES THE TILING LOSE ROWS? Count a parent range, subdivide it, count every
child, compare. If the children do not sum to the parent, the partitioner is
dropping rows silently — which is what a run that terminates 14.6M short looks
like from the outside.

⚠ THIS ASKS THE SERVER BOTH TIMES. Python's string comparison and Socrata's
collation are the two things that have to agree, and only the server can say
whether they do.
"""
import sys

from pull_index_fast import count, fetch, subdivide, LIMIT

DS = "636b-3b5g"   # parties


def probe(lo, hi, depth=0, budget=[40]):
    pad = "  " * depth
    if budget[0] <= 0:
        return
    budget[0] -= 1
    n = count(DS, lo, hi)
    print(f"{pad}[{lo}, {hi}) = {n:,}", flush=True)
    if n < LIMIT:
        return
    parts = subdivide(lo, hi)
    if not parts:
        print(f"{pad}  ⚠ CANNOT SUBDIVIDE — this is the terminal case")
        return
    tot = 0
    kids = []
    for a, b in parts:
        c = count(DS, a, b)
        kids.append((a, b, c))
        tot += c
    print(f"{pad}  {len(parts)} children sum to {tot:,} "
          f"({'MATCH' if tot == n else f'LOST {n - tot:,}'})", flush=True)
    for a, b, c in kids:
        if c:
            print(f"{pad}    {c:>10,}  [{a}, {b})")
    # descend into the fattest child only
    fat = max(kids, key=lambda k: k[2])
    if fat[2] >= LIMIT and fat[2] < n:
        probe(fat[0], fat[1], depth + 1, budget)
    elif fat[2] >= n:
        print(f"{pad}  ⚠ CHILD IS AS BIG AS PARENT — descent cannot converge")
        # is it one document?
        rows = fetch(DS, fat[0], fat[1])
        ids = {r.get("document_id") for r in rows}
        print(f"{pad}    page of {len(rows):,} spans {len(ids)} document_id(s)")
        if len(ids) <= 3:
            print(f"{pad}    ⚠ SINGLE-DOCUMENT OVERFLOW: {sorted(ids)}")


if __name__ == "__main__":
    lo, hi = sys.argv[1], sys.argv[2]
    probe(lo, hi)
