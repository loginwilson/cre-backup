"""RICHMOND AUDIT - the enumeration safety check. NOT part of the cycle.

login (2026-08-28): "enumeration is an audit that isn't part of the cycle,
but exists to check whenever we want to as a match of total doc id in our
db vs the live source." The three richmond names:

    richmond reproduction   the db populating        rc_lane.py (rename
                                                     deferred to key-column
                                                     removal)
    richmond update         reports on our db's      Updates\\routine_update.py
                            changes                  + board_truth.py rows
    richmond audit          THIS - reads the source, compares to our db

One command, all read-only against our db; the only requests are the
county's own listing pages for the trailing window (drumroll rule - a
lone listing sweep is nothing next to the lane's normal presence).

    python richmond_audit.py [--days 30]

PASS = MISSING 0 (live membership) - MISSED 0 (census baseline) -
zero-states honest (rd-less and NULL are 0; pdf='' only a just-landed
tail). Proven shape 2026-08-28: week 08/21..08/28 -> county 745, held
745/745, MISSING 0 (login's independent count agreed: 745).
"""
import argparse
import datetime as dt
import pathlib
import sqlite3
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# ⚠ THIS FILE LIVES IN THE RICHMOND\Reproduction FOLDER (login 2026-08-28)
# but the modules it rides (rc_sync, corpus_paths, rc_census) live in the
# decoder dir - point there explicitly, never at our own parent.
DECODER = pathlib.Path(r"C:\Users\smile\Downloads"
                       r"\Source Folder (Real Estate Data)"
                       r"\Decoder Prompt\decoder")
sys.path.insert(0, str(DECODER))
import corpus_paths as CP                                      # noqa: E402
import rc_sync as RCS                                          # noqa: E402

HERE = DECODER
LO, HI = "RC_", "RC`"

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=30,
                help="trailing window checked live against the county")
ap.add_argument("--skip-census", action="store_true",
                help="skip the rc_census --report baseline accounting")
a = ap.parse_args()

c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
c.execute("PRAGMA busy_timeout=30000")

print("== 1 · OUR TOTALS (index-only) ==", flush=True)
t = time.time()
tot = c.execute("SELECT count(*) FROM navigation WHERE id>=? AND id<?",
                (LO, HI)).fetchone()[0]
rdless = c.execute("SELECT count(*) FROM navigation WHERE"
                   " recorded_details='' AND id>=? AND id<?",
                   (LO, HI)).fetchone()[0]
rows = c.execute("SELECT pdf FROM navigation WHERE pdf IN ('','pending')"
                 " AND id>=? AND id<?", (LO, HI)).fetchall()
unassigned = sum(1 for (p,) in rows if p == "")
pending = len(rows) - unassigned
nul = c.execute("SELECT count(*) FROM navigation WHERE pdf IS NULL"
                " AND id>=? AND id<?", (LO, HI)).fetchone()[0]
print("  rows %s · rd-less %d · pdf unassigned %d · pending %d ·"
      " NULL %d   (%.1fs)"
      % ("{:,}".format(tot), rdless, unassigned, pending, nul,
         time.time() - t), flush=True)

print("== 2 · LIVE MEMBERSHIP - the county's own listing, trailing %d"
      " days ==" % a.days, flush=True)
# ⚠⚠ WINDOWS MUST BE <= 30 DAYS - A LONGER ASK RETURNS A SILENT ZERO.
# This is the county's measured cap (rc_census.py's header records it),
# and passing --days 45 straight through produced
# "county lists 0 ... held 0/0 · MISSING 0" - a PASS out of a denominator
# of zero, on a window we KNEW held hundreds of filings. An audit that
# can answer "all clear" without asking anything is worse than no audit.
if a.days > 30:
    print("  ⚠ --days %d exceeds the county's 30-day window cap (a longer"
          " ask returns a SILENT ZERO) - clamping to 30" % a.days,
          flush=True)
    a.days = 30
b = dt.date.today()
lo = b - dt.timedelta(days=a.days)
fmt = "%m/%d/%Y"
w = RCS.Window(lo.strftime(fmt), b.strftime(fmt))
listed = w.rows()
print("  county lists %d for %s..%s" % (len(listed), lo.strftime(fmt),
                                        b.strftime(fmt)), flush=True)
missing = [r["internal_id"] for r in listed
           if not c.execute("SELECT 1 FROM navigation WHERE id=?",
                            ("RC_" + r["internal_id"],)).fetchone()]
print("  held %d / %d · MISSING %d" % (len(listed) - len(missing),
                                       len(listed), len(missing)),
      flush=True)
if missing:
    print("  ⚠ missing ids:", missing[:25], flush=True)

if not a.skip_census:
    print("== 3 · CENSUS BASELINE (rc_census --report) ==", flush=True)
    r = subprocess.run([sys.executable, str(HERE / "rc_census.py"),
                        "--report"], capture_output=True, text=True)
    for ln in (r.stdout or r.stderr).splitlines():
        print("  " + ln, flush=True)

# ⚠ AN EMPTY DENOMINATOR IS NOT A PASS. `MISSING 0` out of 0 listings
# means the probe asked nothing (a bad window, a redesigned page, a dead
# session) - the control-first doctrine: a known-nonzero window must
# parse rows before any zero is believed.
if not listed:
    verdict = "UNPROVEN (the county listed 0 rows - the probe asked" \
              " nothing; do not read this as coverage)"
elif missing or rdless or nul:
    verdict = "FAIL"
else:
    verdict = "PASS"
print("\nRICHMOND AUDIT: %s · our %s rows · window MISSING %d ·"
      " rd-less %d · NULL %d"
      % (verdict, "{:,}".format(tot), len(missing), rdless, nul),
      flush=True)
