"""ASSIGN THE PDF STATE FOR RICHMOND — the maturation pass.

login 2026-08-26: "pending should always be checked for the lag distribution.
the moment it falls out of it, it becomes absent. and it should continuously
fill the que until it reaches day 7 so that we dont miss it when it comes in"
and "most of the syncs will likely go through this process of pending until
image attaches" — so this is the NORMAL path for every new filing, not a
cleanup tool.

⚠ THIS IS THE HALF THAT WAS MISSING. `rc_rd_refresh.py` already re-walks docs
recorded in the last N days and REPLACES their rd, so image_state flips to
'present' the moment the county attaches the scan. But it only ever writes
`recorded_details` — it never touches `pdf`. So a doc that passed day 7 with
no image simply stopped being refreshed and sat at pdf='' forever, invisible
to the lane (whose miner selects image_state='present') and permanently todo.
That is how 6,699 rows accumulated by 2026-08-26 and why richmond could not
reach 100%.

THE STATE MACHINE (the pdf cell is the evidence column):

    image present                 -> LEAVE ALONE. The lane owns it; pdf stays
                                     '' or 'pending' so the miner still sees it.
    no image, recorded <= LAG     -> 'pending'  ASSIGNED, and STAYS IN THE
                                     QUEUE (the miner selects pdf IN
                                     ('','pending')), so the image is picked up
                                     the moment it attaches.
    no image, recorded  > LAG     -> 'absent'   a DETERMINATION, counted DONE.
    no image_state in the rd      -> NO VERDICT. Reported, never written.

⚠ 'absent' NOT NULL. board_truth counts `landed = total - todo` over
`pdf IN ('','pending')`; NULL is neither, so it would be absorbed into landed
and report completion that did not happen. NULL means "never minted" and is a
defect signal — keep it that way.

⚠ NEVER GUESS AT A MISSING image_state. 72 rows (all pre-1950, parsed before
the field existed) carry no image_state at all. "We never asked" is not "there
is none": writing 'absent' there would be a fabricated determination. They need
an rd refresh first, and this pass reports them instead.

    python rc_pdf_state.py                 report only
    python rc_pdf_state.py --apply         write the verdicts
    python rc_pdf_state.py --lag 7         override the lag window
"""
import argparse
import datetime as dt
import json
import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB = r"D:\CRE Decoding System\Legal Instruments.db"
LO, HI = "RC_", "RC`"

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--lag", type=int, default=7,
                help="days a doc may sit 'pending' before it matures to"
                     " 'absent' (the county's scan lag)")
a = ap.parse_args()

CUTOFF = dt.date.today() - dt.timedelta(days=a.lag)


def recorded_on(d):
    """The rd carries M/D/YYYY. Unparseable date => no verdict."""
    s = (d.get("recorded") or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


con = sqlite3.connect(DB, timeout=1800)
con.execute("PRAGMA busy_timeout=900000")

rows = con.execute(
    "SELECT id, recorded_details, pdf FROM navigation"
    " WHERE pdf IN ('','pending') AND id >= ? AND id < ?", (LO, HI)).fetchall()

to_pending, to_absent = [], []
hold = {"image present - the lane owns it": 0,
        "no image_state in the rd - NEEDS AN rd REFRESH": 0,
        "unparseable recorded date": 0,
        "no rd": 0,
        "already correct": 0}

for did, rd, pdf in rows:
    if not rd:
        hold["no rd"] += 1
        continue
    try:
        d = json.loads(rd)
    except Exception:
        hold["no rd"] += 1
        continue
    st = d.get("image_state")
    if st == "present":
        hold["image present - the lane owns it"] += 1
        continue
    if st is None:
        hold["no image_state in the rd - NEEDS AN rd REFRESH"] += 1
        continue
    rec = recorded_on(d)
    if rec is None:
        hold["unparseable recorded date"] += 1
        continue
    want = "pending" if rec > CUTOFF else "absent"
    if pdf == want:
        hold["already correct"] += 1
    elif want == "pending":
        to_pending.append(did)
    else:
        to_absent.append(did)

print("richmond rows in the queue (pdf IN ('','pending')): %s" % f"{len(rows):,}")
print("lag %d days - matures on or before %s" % (a.lag, CUTOFF))
print()
print("  -> 'pending'  (no image, still in lag, STAYS QUEUED) %8s"
      % f"{len(to_pending):,}")
print("  -> 'absent'   (no image, lag expired, DETERMINATION) %8s"
      % f"{len(to_absent):,}")
print()
print("  left alone:")
for k, v in sorted(hold.items(), key=lambda x: -x[1]):
    if v:
        print("     %-46s %8s" % (k, f"{v:,}"))

if not a.apply:
    print("\nREPORT ONLY - nothing written. Re-run with --apply.")
    con.close()
    sys.exit(0)

con.execute("BEGIN IMMEDIATE")
con.executemany("UPDATE navigation SET pdf='pending' WHERE id=?"
                " AND pdf IN ('','pending')", [(d,) for d in to_pending])
con.executemany("UPDATE navigation SET pdf='absent' WHERE id=?"
                " AND pdf IN ('','pending')", [(d,) for d in to_absent])
con.execute("COMMIT")
print("\nCOMMITTED  %s pending  %s absent"
      % (f"{len(to_pending):,}", f"{len(to_absent):,}"))

unassigned, = con.execute(
    "SELECT COUNT(*) FROM navigation WHERE pdf = '' AND id >= ? AND id < ?",
    (LO, HI)).fetchone()
queued, = con.execute(
    "SELECT COUNT(*) FROM navigation WHERE pdf IN ('','pending')"
    " AND id >= ? AND id < ?", (LO, HI)).fetchone()
tot, = con.execute("SELECT COUNT(*) FROM navigation WHERE id >= ? AND id < ?",
                   (LO, HI)).fetchone()
print("UNASSIGNED (pdf='') %s  ->  %.4f%% ASSIGNED"
      % (f"{unassigned:,}", 100 * (tot - unassigned) / tot))
print("still queued (pending, awaiting image) %s" % f"{queued:,}")
con.close()
