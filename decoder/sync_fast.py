"""SYNC, THE O(DELTA) PATH — what the monitor found, landed in seconds.

Login 2026-08-22: *"sync must move quick from top of our count to the edge of
theirs and find those ids quick to send to nav. since it can pile up."*

⚠ WHY THIS EXISTS ALONGSIDE routine_synchronization.py, NOT INSTEAD OF IT.
That routine proves LEVELNESS: count our own rows (a scan), gallop+bisect the
edge (~30 requests), gather, land, re-confirm. It is O(corpus) and it takes
minutes - measured, it timed out at 100 s against a busy table. At a one-minute
monitor cadence with ACRIS recording ~1,550/business day (~3.2/min), a sync
that takes minutes NEVER CATCHES UP: the delta grows while it works. That is
the pile-up.

This path is O(DELTA). The monitor already answered the expensive question -
"something exists above the edge" - so this does not gallop and does not scan.
It walks forward from our known top, takes the doc ids, writes them, and stops.
At 3 documents a minute that is ~4 requests and one small transaction.

    routine_synchronization.py   proves levelness      minutes   periodic
    sync_fast.py                 lands the delta       seconds   every minute

⚠ BOTH ARE NEEDED. index_daily.py: "a forward-only watermark inherits every
gap it already has and reports clean forever - it cannot see a row withdrawn
or re-keyed." This path only ever moves forward. The full routine remains the
ground truth on a slower schedule, or the cheap check gets mistaken for a
complete one.

⚠ THE WATERMARK ADVANCES ONLY AFTER THE ROWS ARE COMMITTED - NEVER ON A LOOK.
index_daily.py paid for this: "state saved before the work meant a report-only
run moved the cutoff and the next real run found nothing, with 28,196
documents permanently behind it while it printed success." --apply is required
to write anything, and the edge file is touched after the commit or not at all.

⚠ CONTROL FIRST. A malformed request returns the same empty page as a genuine
absence. If the known edge does not resolve, this reports NOTHING rather than
"quiet". phase_monitor's first version printed "quiet" after 8 instant
failures because a broad except turned errors into absences.

⚠ A BLANK IS NOT THE END. The counter has genuine holes (11 measured in July,
all verified unissued). The walk stops only after CONFIRM_BLANKS consecutive
misses, never on the first.

⚠ IF THE WALK RUNS LONG, STOP AND ESCALATE. After an outage the delta can be
thousands, and a linear walk is O(n) where the gallop is O(log n). Past --max
this refuses to keep walking and tells you to run the full routine.

Usage:  python sync_fast.py                 # report only, writes nothing
        python sync_fast.py --apply         # land the ids + advance the edge
        python sync_fast.py --max 500
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
import live_crfn as LC
import live_delta as LD

EDGE_STATE = HERE / "_crfn_edge.json"
LEDGER = ("D:/CRE Decoding System/00 Synchronizations"
          "/Legal Instruments Synchronization"
          "/Legal Instruments Synchronization.db")
ACRIS_URL = "https://a836-acris.nyc.gov/DS/DocumentSearch/"
CONFIRM_BLANKS = 8

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true", help="write; default reports")
ap.add_argument("--max", type=int, default=500,
                help="walk bound; past this, escalate to the full routine")
a = ap.parse_args()


def urls(did):
    """Pure function of the id - the SAME mint as routine_navigation.urls.
    (nav_append is a SCRIPT: importing it would run it.)"""
    return (f"{ACRIS_URL}DocumentDetail?doc_id={did}",
            f"{ACRIS_URL}DocumentImageView?doc_id={did}")


state = json.loads(EDGE_STATE.read_text(encoding="utf-8"))
edge = int(state["edge"])
print(f"our top   CRFN {edge:,}")

s = LD.Session().open().open_crfn()
if LC.parse_detail(LC.detail_html(s, edge)) is None:
    sys.exit(f"⚠ CONTROL {edge:,} did not resolve - probe unproven, "
             f"reporting NOTHING. A malformed request looks like an empty one.")
print("control resolves - probe OK")

# ── WALK: forward from our top, stopping only on CONFIRM_BLANKS in a row ──
found, blanks, n, calls = [], 0, edge, 1
while blanks < CONFIRM_BLANKS and (n - edge) < a.max:
    n += 1
    calls += 1
    try:
        d = LC.parse_detail(LC.detail_html(s, n))
    except Exception as e:
        sys.exit(f"⚠ probe ERRORED at {n:,} ({type(e).__name__}) - stopping. "
                 f"An error is not an absence; nothing written.")
    if d is None:
        blanks += 1
        continue
    blanks = 0
    found.append((n, d["doc_id"], d.get("doc_type", ""), d.get("recorded", "")))

if (n - edge) >= a.max:
    sys.exit(f"⚠ walked {a.max} numbers without {CONFIRM_BLANKS} consecutive "
             f"blanks - the delta is too big for a linear walk. Run "
             f"routine_synchronization.py (gallop+bisect, O(log n)). "
             f"Nothing written.")

new_edge = found[-1][0] if found else edge
print(f"walked +{n - edge} ({calls} requests) · found {len(found)} new")
for crfn, did, dt, rec in found[:10]:
    print(f"    {crfn:,}  {did}  {dt[:28]:<28} {rec[:20]}")
if len(found) > 10:
    print(f"    ... and {len(found) - 10} more")

if not found:
    print("level - nothing to land")
    sys.exit(0)
if not a.apply:
    print("--apply not given: NOTHING WRITTEN, edge NOT advanced")
    sys.exit(0)

# ── LAND: one transaction, bare inserts. THE WRITER-SEAT LAW: batch the
# WRITES, never the work. The fetching above is already done. ───────────────
con = sqlite3.connect(CP.NAV_DB, timeout=600)
con.execute("PRAGMA busy_timeout=300000")
rows = [(did, *urls(did)) for _, did, _, _ in found]
con.executemany("INSERT OR IGNORE INTO navigation (id, rd_url, pdf_url)"
                " VALUES (?,?,?)", rows)
con.commit()
landed = con.total_changes
con.close()
print(f"landed {landed} ids into navigation (urls minted)")

# ── LEDGER, then the watermark. IN THAT ORDER, AFTER THE COMMIT. ───────────
try:
    lg = sqlite3.connect(LEDGER, timeout=120)
    lg.execute("INSERT INTO synchronization"
               " (run_at, source, system_total, source_total, delta, doc_ids)"
               " VALUES (?,?,?,?,?,?)",
               (time.strftime("%Y-%m-%d %H:%M"), "acris", 0, 0, len(found),
                ";".join(d for _, d, _, _ in found)))
    lg.commit()
    lg.close()
except Exception as e:
    print(f"  ⚠ ledger write failed ({e}) - edge NOT advanced, so the next "
          f"run re-finds these rather than stepping over them")
    sys.exit(1)

state["edge"] = new_edge
state["watermark"] = new_edge
EDGE_STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")
print(f"edge advanced {edge:,} -> {new_edge:,}  (after the commit, never before)")
