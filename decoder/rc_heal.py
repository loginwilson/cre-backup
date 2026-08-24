"""RC HEAL — land rd for richmond rows the census-era walker cannot see.

    python rc_heal.py --days 30            # report what it would land
    python rc_heal.py --days 30 --apply    # the real thing

login (2026-08-24): "we need to heal whatever has been missed." Ids landed
by rc_live AFTER the census was built have no listing/window row, so
rc_rd_walk is structurally blind to them - they sit rd='' forever (24
found today, some days old). The GRANT RULE closes the gap: a date-range
Window's own pages grant its ids' details. So: open a Window over the
trailing days, walk its pages, fetch the detail of every rd-less RC id it
lists, land in the CORPUS SCHEMA (rc_rd_walk.parse_detail - the 2.4M rows'
shape, NOT rc_source's). key_on_rd keys each landing in the same
transaction. Ids still rd-less after this run predate the window - rerun
with a bigger --days, and say so rather than staying silent.

Refusal discipline: a 403 or the unauthorized shell stops the run at once.
Until rc_lane exists, run this after quiet mornings or whenever the
rd-less count is nonzero. Richmond runs the DRUMROLL rule (proven 160
concurrent connections) but a healer has no reason to hurry - one detail
at a time with a breath between."""
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

import corpus_paths as CP                                      # noqa: E402
import rc_sync as RCS                                          # noqa: E402

# ⚠ rc_rd_walk parses argv at import - shim it away, then restore
_argv, sys.argv = sys.argv, ["rc_rd_walk.py"]
import rc_rd_walk as RW                                        # noqa: E402
sys.argv = _argv

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=30)
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()


def say(m):
    print("%s  %s" % (time.strftime("%H:%M:%S"), m), flush=True)


nav_ro = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=120)
todo = {r[0][3:] for r in nav_ro.execute(
    "SELECT id FROM navigation WHERE recorded_details = ''"
    " AND id >= 'RC_' AND id < 'RC`'")}
say("rd-less richmond rows: %d" % len(todo))
if not todo:
    say("nothing to heal")
    sys.exit(0)

import datetime as dt                                          # noqa: E402
b = dt.date.today()
lo = b - dt.timedelta(days=a.days)
mdy = lambda d: d.strftime("%m/%d/%Y")                         # noqa: E731
say("opening window %s .. %s (grant rule: its pages unlock its ids)"
    % (mdy(lo), mdy(b)))
w = RCS.Window(mdy(lo), mdy(b))
rows = w.rows()
say("window lists %d rows across its pages" % len(rows))
hits = [r["internal_id"] for r in rows if r["internal_id"] in todo]
say("of the rd-less set, visible in this window: %d" % len(hits))

wcon = None
if a.apply and hits:
    wcon = sqlite3.connect(CP.NAV_DB, timeout=600)
    wcon.execute("PRAGMA busy_timeout=300000")
landed = failed = 0
for iid in hits:
    try:
        _, h = RCS.RR.post(w.s, "/Search/DateRangeSearch",
                           w._f(ViewDetailsButton=str(iid)))
        rec = RW.parse_detail(h, iid)
    except Exception as e:
        msg = str(e)
        if "403" in msg or "Forbidden" in msg or "nauthorized" in msg:
            say("REFUSED at RC_%s - STOPPING: %.80s" % (iid, e))
            break
        failed += 1
        say("  RC_%s failed (%s)" % (iid, type(e).__name__))
        continue
    if not a.apply:
        say("  would land RC_%s · instrument %s · %s"
            % (iid, rec.get("instrument"), rec.get("recorded")))
        continue
    for _try in range(60):
        try:
            wcon.execute("UPDATE navigation SET recorded_details=?"
                         " WHERE id=? AND recorded_details=''",
                         (json.dumps(rec, separators=(",", ":")),
                          "RC_" + iid))
            wcon.commit()
            landed += 1
            break
        except sqlite3.OperationalError:
            time.sleep(5)
    time.sleep(0.3)
say("healed %d · failed %d · rd-less remaining beyond this window: %d"
    % (landed, failed, len(todo) - len(hits)))
if len(todo) - len(hits):
    say("⚠ the remainder predates %s - rerun with a bigger --days" % mdy(lo))
