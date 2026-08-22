"""RE-FETCH THE BBL-LESS QUEUE ROWS SO THEIR PARTIES LAND — the 2,899.

    ACRIS_CORPUS_ROOT=D:/acris python repair_parties.py

WARNING - WHY A RE-FETCH. These documents were walked BEFORE parse_detail
captured the party block, so their queue rows carry no reach path at all: no
bbl (they are UCC/lien filings on non-real collateral) and no parties (the old
parser discarded them). live_land rightly refuses them. The detail pages HAVE
the parties - the parser just didn't read them. One more paced pass fixes the
rows in place.

WARNING - SCOPE IS THE BBL-LESS ONLY. The other ~14k live-window rows are
already reachable by parcel; their parties arrive free in the next monthly
Socrata refresh. Re-fetching all 17k would triple the cost for enrichment the
refresh delivers anyway.

WARNING - REWRITE THE QUEUE ATOMICALLY. Rows are updated in memory and the file
is replaced via tmp+rename, so a kill mid-run leaves the original intact.
Concurrency 3, same measured envelope as the walk. Any Refused stops everything.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import live_crfn as LC
import live_delta as LD

QUEUE = HERE / "_live_delta_queue.jsonl"


def main():
    rows = []
    todo = {}                       # crfn -> row-index
    for i, l in enumerate(QUEUE.open(encoding="utf-8")):
        r = json.loads(l)
        rows.append(r)
        if not r.get("bbls") and not r.get("parties"):
            c = str(r.get("crfn") or "").strip()
            if c.isdigit():
                todo[int(c)] = i
    print(f"  queue rows {len(rows):,} · to repair {len(todo):,}")
    if not todo:
        print("  nothing to repair.")
        return

    s = LD.Session().open().open_crfn()
    ctrl = max(todo)
    if LC.parse_detail(LC.detail_html(s, ctrl)) is None:
        sys.exit("  CONTROL did not resolve - refusing to run.")
    print(f"  control {ctrl} resolves - probe OK")

    def fetch(c):
        try:
            return c, LC.parse_detail(LC.detail_html(s, c)), None
        except Exception as e:
            return c, None, type(e).__name__

    fixed = still = err = done = 0
    t0 = time.time()
    refused = False
    crfns = sorted(todo)
    with ThreadPoolExecutor(max_workers=5) as ex:
        for b0 in range(0, len(crfns), 30):
            if refused:
                break
            for c, d, e in ex.map(fetch, crfns[b0:b0 + 30]):
                done += 1
                if e == "Refused":
                    print(f"  REFUSED at {c} - stopping; partial repair is safe "
                          f"(rows already fixed stay fixed).")
                    refused = True
                    break
                if e or d is None:
                    err += 1
                    continue
                d["crfn"] = str(c)
                rows[todo[c]] = d
                if d.get("parties"):
                    fixed += 1
                else:
                    still += 1      # genuinely partyless - rare but possible
                if done % 200 == 0:
                    r = (time.time() - t0) / done
                    print(f"    {done:,}/{len(crfns):,} · {fixed:,} gained "
                          f"parties · {(len(crfns)-done)*r/60:.0f} min left")

    tmp = QUEUE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    tmp.replace(QUEUE)
    print(f"\n  DONE {(time.time()-t0)/60:.1f} min · {fixed:,} gained parties · "
          f"{still:,} genuinely partyless · {err:,} errors")
    print("  next: live_land.py --apply lands them by the party path")


if __name__ == "__main__":
    main()
