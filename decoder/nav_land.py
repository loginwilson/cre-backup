"""LAND THE PULL INTO THE ONE TABLE - sqlite edition (superseding the csv
full-rewrite version the same evening; the flip means landing is an
IN-PLACE UPSERT, not a 24M-row stream).

Folds the walk ledger (rd_repull.jsonl, append-only, crash-safe journal)
into Legal Instruments Navigation.db: recorded_details and pdf per row,
last write per id wins. Tracks its own high-water mark (byte offset) so
each run lands only NEW ledger lines - run it as often as you like; a
landing of nothing costs nothing.

keyed_by/key stay untouched - keying is ITS OWN pass over the landed
details (login: "once done we will key based on the pull that lands in the
table").
"""
import json
import pathlib
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP

LEDGER = CP.NAV_WORK / "rd_repull.jsonl"
MARK = CP.NAV_WORK / "_landed_offset.txt"

start = int(MARK.read_text()) if MARK.exists() else 0
size = LEDGER.stat().st_size if LEDGER.exists() else 0
if start > size:
    # the ledger shrank - a rebuilt/rotated journal; land it all again
    # (idempotent: upserts converge to the same state)
    start = 0
if start == size:
    print(f"nothing new to land (ledger at {size:,} bytes)")
    sys.exit(0)

con = sqlite3.connect(CP.NAV_DB, timeout=300)
t0, landed, unknown = time.time(), 0, 0
with LEDGER.open("r", encoding="utf-8") as fh:
    fh.seek(start)
    for line in fh:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        details = {k: v for k, v in r.items() if k not in ("id", "at", "pdf")}
        cur = con.execute(
            "UPDATE navigation SET recorded_details=?,"
            " pdf=COALESCE(NULLIF(?,''), pdf) WHERE id=?",
            (json.dumps(details, separators=(",", ":")),
             r.get("pdf", ""), r["id"]))
        if cur.rowcount:
            landed += 1
        else:
            unknown += 1
            print(f"  ⚠ ledger id {r['id']} not in the table - the sealed"
                  f" universe does not know it (investigate, never insert)")
    pos = fh.tell()
con.commit()
con.close()
MARK.write_text(str(pos))
print(f"landed {landed:,} rows in {time.time()-t0:.1f}s"
      + (f" · ⚠ {unknown} unknown ids" if unknown else ""))
