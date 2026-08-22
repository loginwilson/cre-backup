"""DOES THE FOOTPRINT JOIN AGREE WITH DOB'S OWN JOB ROWS?

⚠ A JOIN THAT WAS NEVER CONTRADICTED IS NOT A MEASURED JOIN. bin_bbl.py built
1,082,984 BIN→BBL pairs from Building Footprints. Nothing in that file proves DOB
agrees. This asks the only question that matters: take a DOB job, read the BIN it
states and the borough/block/lot it states, and see whether the footprint table
maps that BIN to that BBL.

⚠ THE JOB ROWS ARE THE SECOND WITNESS, NOT THE TRUTH. DOB_DOCUMENT_PLAN.md
already measured that BIS's own `bbl` column is a BIN 32.6% of the time, so the
key is rebuilt from borough/block/lot — never read off `bbl`. Disagreement here
is therefore a finding about which source is stale, not proof that either is
wrong.

⚠ AND DISAGREEMENT IS EXPECTED, NOT ALARMING. A building outlives the lot it sat
on. A job filed in 1998 states the lot as it was in 1998; the footprint states it
as DOF sees it now. That gap IS the lot-lineage signal — it is the reason to
build lineage, not a reason to distrust the join.

    python bin_bbl_check.py            # BIS legacy
    python bin_bbl_check.py --now      # DOB NOW Build
"""
from __future__ import annotations

import collections, json, os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))

import bulk, dob

N = int(os.environ.get("N", 60000))
BORO_NUM = {"MANHATTAN": "1", "BRONX": "2", "BROOKLYN": "3", "QUEENS": "4",
            "STATEN ISLAND": "5"}


def bbl_of(boro, block, lot):
    b = BORO_NUM.get(str(boro or "").strip().upper())
    try:
        blk, lt = int(str(block).strip()), int(str(lot).strip())
    except (TypeError, ValueError):
        return None
    if not b or blk <= 0:
        return None
    return f"{b}{blk:05d}{lt:04d}"


def main():
    now = "--now" in sys.argv
    ds = dob.NOW_JOBS if now else dob.BIS_JOBS
    binf = "bin" if now else "bin__"
    label = "DOB NOW Build" if now else "BIS legacy"

    j = json.load(open(os.path.join(HERE, "_bin_bbl.json"), encoding="utf-8"))
    b2b = j["bin2bbl"]
    print(f"footprint join: {len(b2b):,} BINs\n")

    rows = bulk.socrata(ds, select=f"{binf},borough,block,lot,job_type",
                        limit=N, paginate=False)
    print(f"{label} — {len(rows):,} job rows sampled\n")

    agree = disagree = nobin = nokey = unknown_bin = 0
    ex = []
    by_type = collections.Counter()
    for r in rows:
        b = str(r.get(binf) or "").strip().split(".")[0]
        if not b or not b.isdigit() or b.endswith("000000"):
            nobin += 1
            continue
        bbl = bbl_of(r.get("borough"), r.get("block"), r.get("lot"))
        if not bbl:
            nokey += 1
            continue
        fp = b2b.get(b)
        if fp is None:
            unknown_bin += 1
            continue
        if fp == bbl:
            agree += 1
        else:
            disagree += 1
            by_type[str(r.get("job_type") or "?")] += 1
            if len(ex) < 5:
                ex.append((b, bbl, fp))

    scored = agree + disagree
    print(f"  ⚠ placeholder or missing BIN on the job row : {nobin:,}")
    print(f"  ⚠ borough/block/lot unusable                : {nokey:,}")
    print(f"  ⚠ BIN not in the footprint table            : {unknown_bin:,}")
    print(f"  SCORED                                      : {scored:,}\n")
    if not scored:
        print("  nothing scored — stop.")
        return 1
    print(f"  AGREE     {agree:>7,}  {100*agree/scored:5.1f}%")
    print(f"  DISAGREE  {disagree:>7,}  {100*disagree/scored:5.1f}%")

    if ex:
        print("\n  DISAGREEMENTS — job row's BBL vs footprint's base_bbl")
        for b, said, fp in ex:
            print(f"    BIN {b}   job says {said}   footprint says {fp}")
    if by_type:
        print("\n  by job type: " + " · ".join(f"{k}={v}" for k, v in by_type.most_common(6)))

    print("\n  ⚠ `BIN not in the footprint table` is the number to watch: a job "
          "filed on a\n    building that no longer has a footprint is either a "
          "demolition, a bad BIN,\n    or a building the footprint file has not "
          "caught up with. It is UNREAD, not absent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
