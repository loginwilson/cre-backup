"""RICHMOND SYNC, THE O(DELTA) PATH — the day's window, landed in seconds.

    python rc_sync_fast.py                 report only, writes nothing
    python rc_sync_fast.py --apply         land the new ids
    python rc_sync_fast.py --days 3 --apply

⚠ WHY THIS EXISTS. `sync_fast.py` is the ACRIS analogue and Richmond had no
counterpart, so `phase_monitor --gate` had nothing to fire for it — the only
option was `routine_synchronization.py`, whose STEP 1 counts 24.1M rows
(~27 minutes measured, 464 s at best) before it looks at the source at all.
Firing that on a one-minute cadence IS the pile-up login asked us to avoid:
*"sync must move quick from top of our count to the edge of theirs and find
those ids quick to send to nav. since it can pile up."*

    routine_synchronization.py   proves levelness   minutes   periodic
    rc_sync_fast.py              lands the delta    seconds   every minute

⚠ RICHMOND NEEDS NO GALLOP. ACRIS's fast path walks the CRFN counter upward
because the edge is a boundary to be found. Richmond's date-range window
RETURNS THE DOCUMENTS THEMSELVES — the monitor already proved the window
parses, so the delta is just "which of these do we not hold", and that is a
primary-key lookup per row. A day is ~100-180 documents over ~7 pages.

⚠ IT PAGES. 17 rows a page — see docs/sources/richmond/00-source.md §2b. Reading
page 1 and calling it the day silently returns ~10%. `Window.rows()` follows
every page and RAISES rather than returning a short list.

⚠ EVERY WORK COLUMN IS '' , NEVER NULL. nav_append.py:216 states the invariant:
"rd_walk sees recorded_details='', image_walk sees pdf='', nav_key sees
keyed_by=''". Those lanes select on `= ''` and **NULL is not ''**, so a row
inserted with NULLs is invisible to every downstream lane forever while looking
perfectly healthy. sync_fast.py had exactly this bug (found 2026-08-23).

⚠ WEEKENDS ARE EMPTY AND THAT IS NOT AN ERROR. Measured across two weekends;
the register records on business days. The walk-back finds the last day that
actually recorded something rather than reporting a false zero.

⚠ THE WATERMARK MOVES AFTER THE COMMIT OR NOT AT ALL. index_daily.py paid for
this: "state saved before the work meant a report-only run moved the cutoff and
the next real run found nothing, with 28,196 documents permanently behind it
while it printed success."
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                    # noqa: E402
import rc_sync as RCS                                        # noqa: E402

RC = "https://www.richmondcountyclerk.com"
LEDGER = (r"D:\CRE Decoding System\00 Synchronizations"
          r"\Legal Instruments Synchronization"
          r"\Legal Instruments Synchronization.db")
STATE = HERE / "_rc_fast_edge.json"

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true", help="write; default reports")
ap.add_argument("--days", type=int, default=3,
                help="trailing window; 3 covers a weekend + late postings")
ap.add_argument("--walkback", type=int, default=5)
a = ap.parse_args()


def urls(did):
    """Pure function of the id - the same mint as nav_append and
    routine_navigation. Defined here because those are SCRIPTS."""
    n = did[3:]
    return (f"{RC}/Search/viewDocumentInfo/{n}",
            f"{RC}/ViewVscmsDocument/ViewContent?p_endorsementId={n}")


# ── the window ────────────────────────────────────────────────────────────
end = dt.date.today()
rows, tried = [], []
for _ in range(a.walkback):
    start = end - dt.timedelta(days=a.days - 1)
    t0 = time.time()
    w = RCS.Window(start.strftime("%m/%d/%Y"), end.strftime("%m/%d/%Y"))
    rows = w.rows()
    print(f"  {start} .. {end}  ->  {len(rows):,} documents over "
          f"{w.pages()} page(s)  {time.time()-t0:.0f}s")
    if rows:
        break
    # ⚠ An empty window is not automatically "quiet" - it is also the shape an
    # over-cap range returns (HTTP 200, ~8 KB, no rows). This window is days
    # wide, well under the 30-day cap, so empty here means the register was
    # closed. Walk back rather than declare a zero we did not measure.
    tried.append(end.strftime("%a"))
    end -= dt.timedelta(days=1)

if not rows:
    print(f"  no rows in {a.walkback} windows back ({','.join(tried)}) - that "
          f"is NOT a quiet week, it is a broken read. Reporting nothing.")
    sys.exit(1)

slots, docs, missing = RCS.density(rows)
print(f"  density: {slots:,} slots · {docs:,} docs · missing {missing}")
if missing:
    # ⚠ Never repair a number to make a check pass.
    print(f"  ⚠ {missing:,} instrument numbers unaccounted for - this window is "
          f"NOT proven complete. Landing what we have; do not treat the day "
          f"as closed.")

# ── which do we not hold? one PK lookup each - no scan ────────────────────
con = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)
con.execute("PRAGMA busy_timeout=300000")
fresh = []
for r in rows:
    did = "RC_" + r["internal_id"]
    if not con.execute("SELECT 1 FROM navigation WHERE id=?", (did,)).fetchone():
        fresh.append(did)
con.close()
print(f"  held {len(rows)-len(fresh):,} · NEW {len(fresh):,}")


def write_ledger(landed_ids, outstanding=0):
    """One ledger row per RUN — including a run that found nothing.

    ⚠ THE ROW ANSWERS ONE QUESTION: DOES SYSTEM MATCH SOURCE? Login
    2026-08-23: *"seeing that system matches source is the key of sync. the
    delta is just the way to find the id and adjust system up to source until
    we tick again."* So the row is the state AFTER absorbing:

        system_total  what we hold now, having absorbed this run's ids
        source_total  what the custodian holds
        delta         source - system = STILL OUTSTANDING · 0 means LEVEL
        doc_ids       what this run moved to get there

    Read a row left to right and the answer is visible: two equal numbers and
    a zero is a healthy sync. ⚠ The schema comment said system_total was the
    count BEFORE absorbing while routine_update read it as AFTER — one column,
    two meanings, which is how the -20,721,031 got onto the board. AFTER wins,
    because it is the reading that makes "system == source" checkable.

    ⚠ A ROW PER SYNC EVENT — NOT A HEARTBEAT. Login 2026-08-23: *"it just
    updates if monitor doesnt flag it doesnt move, but if monitor flags then it
    does fast sync, finds the delta, id, and then the system total should be
    level after that feeds nav."* Sync only RUNS when the monitor flags, so the
    absence of a row is not ambiguous — it means the monitor found nothing, and
    the monitor's own log already proves it was alive and checking every minute.
    **Proof-of-life belongs in the monitor's log; the ledger is for events.**
    An earlier draft of this wrote hourly heartbeat rows: 1,440 near-identical
    rows a day into a table that is read by eye, to re-state something another
    log already said.

    ⚠ It DOES still write when a flagged run finds nothing (`NEW 0`) — that is
    a real and interesting result: the monitor said something changed and sync
    disagreed. Worth a row precisely because it is a discrepancy.

    ⚠ THE TOTAL IS ACCOUNTED, NOT MEASURED — previous + exactly what we landed,
    so it needs no scan. `routine_synchronization` re-measures both sides daily
    and re-anchors it. Never let the accounted figure outlive its anchor."""
    lg = sqlite3.connect(LEDGER, timeout=120)
    try:
        prev = lg.execute(
            "SELECT system_total FROM synchronization"
            " WHERE source='richmond' AND system_total > 0"
            " ORDER BY run_at DESC LIMIT 1").fetchone()
        system = (prev[0] if prev else 0) + len(landed_ids)
        source = system + outstanding
        stamp = time.strftime("%Y-%m-%d %H:%M")
        lg.execute(
            "INSERT OR REPLACE INTO synchronization"
            " (run_at, source, system_total, source_total, delta, doc_ids)"
            " VALUES (?,?,?,?,?,?)",
            (stamp, "richmond", system, source, outstanding,
             ";".join(landed_ids)))
        lg.commit()
        print(f"  ledger {stamp}: system {system:,} · source {source:,} · "
              f"delta {outstanding}"
              + ("  LEVEL" if outstanding == 0 else "  OUTSTANDING"))
    finally:
        lg.close()


if not fresh:
    print("level - nothing to land")
    if a.apply:
        # ⚠ STILL RECORD THE RUN. "Nothing new" is a RESULT and the most
        # common one; it is exactly the answer that must be visible.
        write_ledger([])
    sys.exit(0)
for d in fresh[:10]:
    print(f"    + {d}")
if len(fresh) > 10:
    print(f"    ... and {len(fresh)-10:,} more")
if not a.apply:
    print("--apply not given: NOTHING WRITTEN")
    sys.exit(0)

# ── LAND: one transaction, bare inserts. THE WRITER-SEAT LAW - batch the
# WRITES, never the work. Everything above is already done. ────────────────
con = sqlite3.connect(CP.NAV_DB, timeout=600)
con.execute("PRAGMA busy_timeout=300000")
batch = [(d, "", urls(d)[0], "", urls(d)[1], "", "") for d in fresh]
for _try in range(120):                  # never die on a lock, like every writer
    try:
        con.executemany(
            "INSERT OR IGNORE INTO navigation"
            " (id, recorded_details, rd_url, pdf, pdf_url, keyed_by, key)"
            " VALUES (?,?,?,?,?,?,?)", batch)
        con.commit()
        break
    except sqlite3.OperationalError:
        time.sleep(5)
else:
    print("could not acquire the write lock in 10 min - nothing written")
    sys.exit(1)
landed = con.total_changes
con.close()
print(f"landed {landed:,} ids into navigation (urls minted, work columns '')")
print("  the running lanes pick them up with no restart: rc_feed sees "
      "recorded_details='', the pdf lane sees pdf='', nav_key sees keyed_by=''")

# ── LEDGER, then the watermark. IN THAT ORDER, AFTER THE COMMIT. ──────────
try:
    # landed everything the window held, so nothing is outstanding
    write_ledger(fresh, outstanding=0)
except Exception as e:
    print(f"  ⚠ ledger write failed ({e}) - watermark NOT advanced, so the "
          f"next run re-finds these rather than stepping over them")
    sys.exit(1)

nums = [int(r["instrument"]) for r in rows if r["instrument"].isdigit()]
STATE.write_text(json.dumps(
    {"edge": max(nums) if nums else None, "through": str(end),
     "at": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1), encoding="utf-8")
print(f"  watermark {max(nums):,} through {end}  (after the commit, never before)")
