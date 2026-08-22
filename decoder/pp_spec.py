"""PERSONAL PROPERTY SPECIFICATION — the second ACRIS corpus.

The doc-id map is REAL property only: 17,049,742 documents. ACRIS also holds
4,544,590 distinct PERSONAL property documents (UCC filings and federal liens)
in `sv7x-dduq`, with ZERO doc-type overlap with real property — measured
2026-08-18, 30 types, 4,547,264 rows. Together the register is 21,594,332
documents, and the map has never covered the second half.

Why it matters beyond the count: `INIC` (INITIAL COOP UCC1) is 970,047 filings.
A co-op has no recorded mortgage — the UCC1 IS the financing instrument, so a
debt throughline built on real property alone is structurally blind to co-op
lending.

⚠ THIS WRITES ITS OWN STATE AND ITS OWN FILE. `pull_index_fast.py` may be
running; it rewrites `_index_fast_state.json` WHOLE, so touching that file from
here would erase whatever it recorded meanwhile. Separate state, separate
output, no shared lock needed because no shared gzip.

⚠ The partition bounds come from the REAL property id histogram. That is safe —
the ranges tile the entire key space, so a personal-property id that has never
been seen still lands in exactly one partition — but it is not SIZED for this
corpus, so expect the splitter to fire more than usual. Under-full partitions
cost requests, not rows.
"""
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import pull_index_fast as P

NAME = "personal_master"
DATASET = "sv7x-dduq"

P.STATE = HERE / "_pp_spec_state.json"
P.WORKERS = 3          # deliberately under the usual 5: the baseline pull may
                       # be running against the same host at the same time


def main():
    if not P.STATE.exists():
        P.STATE.write_text("{}", encoding="utf-8")
    st = json.loads(P.STATE.read_text(encoding="utf-8"))
    print("ACRIS PERSONAL PROPERTY — specification pull\n")
    t0 = time.time()
    P.pull(NAME, DATASET, st)
    print(f"  total {(time.time()-t0)/60:.1f} minutes -> {P.OUTDIR/(NAME+'.jsonl.gz')}")


if __name__ == "__main__":
    main()
