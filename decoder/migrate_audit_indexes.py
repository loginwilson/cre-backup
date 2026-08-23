"""AUDIT INDEXES — the migration that lets nav / acq / org prove their claims.

    python migrate_audit_indexes.py            # report only: what exists, what it would cost
    python migrate_audit_indexes.py --apply --index ix_nav_url_todo

⚠⚠ **DO NOT RUN --apply WHILE THE FLEET IS WRITING. THIS IS NOT A SUGGESTION.**
`CREATE INDEX` on `navigation` must examine all 24.1M rows AND holds the single
writer seat for the whole build. Every walker, the keyer and both richmond lanes
queue behind it. On a 16.5 GB table under load that is measured in HOURS.

**THIS FILE EXISTS TO BE READY, NOT TO BE RUN TONIGHT.** It is prepared so the
decision is a decision and not a guess. Running it is login's call and needs a
deliberate pause of the fleet.

## WHY IT IS WORTH A MAINTENANCE WINDOW

The chain's first end-to-end run (2026-08-23) proved only 2 of 5 phases:

    monitor  LEVEL · sync LEVEL · nav DECLINED · acq DECLINED · org DECLINED

Every decline has one cause: **that phase's audit is a full TABLE scan** and the
fleet never stops. Measured 64.8 s per 200,000 rows under load — ~2.2 hours a
pass. So three phases can essentially never prove their claim, and the guards
that stop them are correct.

`board_truth.py` already solved exactly this for acquisition's pdf number by
counting a PARTIAL INDEX instead of the table. Measured on the same machine in
the same minute:

    ix_nav_pdf_todo   23,097,031 entries    30 s   ~770,000/s   HOT
    PK autoindex       2,501,589 entries   168 s    ~15,000/s   COLD
    table scan           200,000 rows    64.8 s     ~3,000/s

**~250x against the table scan.** And the partial index is fast *because the
lanes keep it hot* — they query `pdf=''` constantly. The audit rides the fleet's
own working set instead of fighting it. That is the trick, and it generalises to
every phase whose claim is "how many rows are still to do".

## ⚠ THE BUILD COST IS THE SCAN, REGARDLESS OF HOW SMALL THE INDEX IS

A partial index on a nearly-empty condition (`ix_nav_url_todo` should match ~0
rows — the tail probe reads 0 missing urls) produces a TINY index. It does NOT
produce a cheap build: sqlite still examines every row to find out which ones
match. **Do not mistake a small result for a small job.**

## ⚠ EACH INDEX ALSO COSTS THE WRITERS FOREVER AFTER

Every INSERT and every UPDATE that touches the indexed column must maintain the
index. `ix_nav_keyed_todo` in particular is maintained by `nav_key.py` on every
single row it keys. Build the ones that pay for themselves, not all of them:
prefer indexes whose condition SHRINKS as work completes, because a partial index
only holds the matching rows and gets cheaper over time.
"""
from __future__ import annotations

import argparse
import pathlib
import sqlite3
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                    # noqa: E402

# name -> (phase it unblocks, DDL, the claim it makes provable)
INDEXES = {
    "ix_nav_url_todo": (
        "navigation",
        "CREATE INDEX IF NOT EXISTS ix_nav_url_todo ON navigation(id)"
        " WHERE COALESCE(rd_url,'')='' OR COALESCE(pdf_url,'')=''",
        "every id is tabled with a key, an index and an ENDPOINT"),
    "ix_nav_rd_todo": (
        "acquisition rd",
        "CREATE INDEX IF NOT EXISTS ix_nav_rd_todo ON navigation(id)"
        " WHERE COALESCE(recorded_details,'')=''",
        "every document's recorded detail is landed"),
    "ix_nav_keyed_todo": (
        "organization",
        "CREATE INDEX IF NOT EXISTS ix_nav_keyed_todo ON navigation(id)"
        " WHERE COALESCE(keyed_by,'')=''",
        "every document is keyed to what it is about"),
}

LANES = ("rd_walk", "image_walk", "nav_key", "rc_feed", "rc_pdf_pull",
         "rc_pdf_land", "org_backfill_arm", "live_gap.py")

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--index", help="build exactly one, by name")
ap.add_argument("--anyway", action="store_true",
                help="⚠ build while lanes write - this WILL stall them")
a = ap.parse_args()

con = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)
have = {r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='index'")}
con.close()

print("=== EXISTING ===")
for n in sorted(have):
    print(f"  {n}")
print("\n=== PROPOSED ===")
for name, (phase, ddl, claim) in INDEXES.items():
    print(f"  {name:<20} {'PRESENT' if name in have else 'missing':<8} "
          f"unblocks: {phase}")
    print(f"    claim: {claim}")

try:
    ps = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
         " | ForEach-Object { $_.CommandLine }"],
        capture_output=True, text=True, timeout=60).stdout
except Exception:
    ps = ""
alive = sorted({k for k in LANES if k in ps})

print("\n=== FLEET ===")
print("  writing now: " + (", ".join(alive) if alive else "nothing"))

if not a.apply:
    print("\n--apply not given. Nothing built.")
    print("⚠ Build one at a time, during a deliberate pause, and expect HOURS.")
    sys.exit(0)

if alive and not a.anyway:
    # ⚠ Unlike the read-side guards, this one protects the LANES from US.
    # A CREATE INDEX takes the writer seat and holds it for the whole build.
    print("\nREFUSING: lanes are writing and this takes the WRITER SEAT for the"
          " whole build.\nStop the fleet first, or pass --anyway deliberately.")
    sys.exit(1)
if not a.index:
    print("\nREFUSING: name exactly one --index. Building several in one go"
          "\nmeans one long lock and no way to tell which one cost what.")
    sys.exit(1)
if a.index not in INDEXES:
    sys.exit(f"unknown index {a.index}")

phase, ddl, claim = INDEXES[a.index]
print(f"\nbuilding {a.index} ...")
print(f"  {ddl}")
t0 = time.time()
w = sqlite3.connect(CP.NAV_DB, timeout=36000)
w.execute("PRAGMA busy_timeout=36000000")
w.execute(ddl)
w.commit()
w.close()
print(f"  built in {time.time()-t0:.0f}s")
print(f"  {phase} can now prove: {claim}")
