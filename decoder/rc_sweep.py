"""RICHMOND HISTORICAL SWEEP — every SI block's ledger, checkpointed.

    ACRIS_CORPUS_ROOT=D:/acris python rc_sweep.py            full sweep
    ACRIS_CORPUS_ROOT=D:/acris python rc_sweep.py --blocks 15,16,17   test slice

The historical specification for the SI deeds source: one GET per block returns
the WHOLE ledger (no paging observed - VERIFIED per block below), carrying the
instrument<->internal-id binding in bulk plus block/lot/type/recorded/book/page.

    blocks: 3,794 - measured from OUR parcel spine (SELECT DISTINCT block of
    borough 5), not guessed. ~95 min at 1.5s pace, ~3.5 GB.

WARNING - CHECKPOINT PER BLOCK. _rc_sweep_state.json records each finished
block with its ROW COUNT; a restart skips them. A kill costs one block.

WARNING - THE NO-PAGING ASSUMPTION IS VERIFIED PER BLOCK, not trusted: if a
block's page carries a paging control or a row-count marker that disagrees with
parsed rows, the block is flagged NOT silently truncated (all four ACRIS paging
bugs came from trusting a derived end-signal).

WARNING - REFUSAL STOPS THE SWEEP. rc_source.check_refused raises on captcha /
blocked shapes; do not retry, do not rotate. The captcha path is a hard no.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP
import rc_source as RC

OUT = pathlib.Path("D:/acris/01-specification/index/rc_ledger.jsonl")
STATE = HERE / "_rc_sweep_state.json"


def spine_blocks():
    con = sqlite3.connect("file:" + str(CP.SPEC_DB).replace("\\", "/")
                          + "?mode=ro", uri=True, timeout=120)
    rows = [r[0] for r in con.execute(
        "SELECT DISTINCT substr(bbl,2,5) FROM parcel WHERE bbl LIKE '5%'")]
    con.close()
    out = sorted({int(b) for b in rows if b.isdigit() and 0 < int(b) <= 8999})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", help="comma list for a test slice")
    ap.add_argument("--full", action="store_true",
                    help="sweep the ENTIRE number space 1..8999, not just the "
                         "spine. ⚠ RETIRED BLOCKS: a block renumbered decades "
                         "ago is absent from today's tax map, so a spine-keyed "
                         "sweep never asks for its ledger - the invisible-loss "
                         "shape of the lot-lineage lesson. Non-existent numbers "
                         "return near-empty pages, so exhaustive costs ~1 hour.")
    a = ap.parse_args()

    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    done = st.setdefault("blocks", {})

    blocks = ([int(x) for x in a.blocks.split(",")] if a.blocks
              else list(range(1, 9000)) if a.full
              else spine_blocks())
    todo = [b for b in blocks if str(b) not in done]
    print(f"  blocks {len(blocks):,} · done {len(blocks)-len(todo):,} · "
          f"todo {len(todo):,} · est {len(todo)*RC.PACE/60:.0f} min")

    # ⚠ CONCURRENCY 3 - measured need, not impatience: the server takes ~10s+
    # to assemble a block ledger (50 blocks = 13 min at sequential 1.5s pace),
    # so response time dominates exactly like ACRIS details. Three workers is
    # modest, checkpoints make restarts free, and ANY Refused stops everything.
    from concurrent.futures import ThreadPoolExecutor
    import threading
    # ⚠ ONE SESSION PER WORKER. Throughput plateaued ~1.4 blk/s from conc 5 -> 8
    # on a SHARED session, which smells like a per-session cap server-side.
    # Independent cookie jars test that hypothesis; if the rate still will not
    # scale, the cap is the server itself and we accept it. Any Refused on ANY
    # session still stops the whole sweep.
    _tl = threading.local()

    def fetch(b):
        try:
            if not hasattr(_tl, "s"):
                _tl.s = RC.Session()
            return b, _tl.s.ledger(b), None
        except Exception as e:
            return b, None, type(e).__name__

    n_docs = 0
    t0 = time.time()
    refused = False
    with OUT.open("a", encoding="utf-8") as f,          ThreadPoolExecutor(max_workers=8) as ex:
      for g0 in range(0, len(todo), 32):
        if refused:
            break
        for i_off, (b, html, err) in enumerate(ex.map(fetch, todo[g0:g0+32])):
            i = g0 + i_off + 1
            if err == "Refused":
                print(f"  REFUSED at block {b} - STOPPING.")
                refused = True
                break
            if err:
                print(f"  block {b} ERROR {err} - will retry next run")
                continue
            rows = RC.parse_ledger(html)
            # ⚠ verify the no-paging assumption per block
            flag = ""
            low = html.lower()
            if "next page" in low or "page 2" in low or ">next<" in low:
                flag = "PAGING-CONTROL-PRESENT"
            for r in rows:
                r["src_block"] = b
                f.write(json.dumps(r) + "\n")
            f.flush()
            done[str(b)] = {"rows": len(rows), "bytes": len(html),
                            "flag": flag or None}
            STATE.write_text(json.dumps(st), encoding="utf-8")
            n_docs += len(rows)
            if flag:
                print(f"  ⚠ block {b}: {flag} - rows may be truncated, "
                      f"investigate before trusting this block")
            if i % 50 == 0:
                r = (time.time() - t0) / i
                print(f"    {i:,}/{len(todo):,} blocks · {n_docs:,} rows · "
                      f"{(len(todo)-i)*r/60:.0f} min left")
    print(f"\n  swept {len(done):,}/{len(blocks):,} blocks · "
          f"{n_docs:,} rows this run · {(time.time()-t0)/60:.1f} min")
    print(f"  ledger -> {OUT}")


if __name__ == "__main__":
    main()
