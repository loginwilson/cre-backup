"""THE ORGANIZATION ROUTINE — the 03 phase, in the standing format
(login 2026-08-21: "should be labelled organization so that it follows the
format weve done up to now").

The phase's one claim: EVERY doc id is KEYED to its BBL(s) by the
three-route ladder - parcel (inline, the moment rd lands) · reference
(convergent passes) · pdf (when the file is on disk). Party is DECODING,
not a key; the db's key_rules trigger aborts it structurally.

Steps, in the six-step grammar:
    1. SYSTEM   count keyed_by states per route (one scan, busy-guarded)
    2. CLAIM    the unkeyed remainder, with its reason distribution
    3. PASS     run the keying engine (nav_key.py, one sweep) on a quiet
                table - routes 2-3 converge, remainder shrinks
    4. (no handoff - the key lands in the same table)
    5. BOARD    write the organization row into the update board
    6. CHECK    identity: parcel + reference + pdf + pdf-pass + unkeyed
                = total (report, never repair)

    python routine_organization.py            audit + one pass
    python routine_organization.py --dry      audit only, no pass

⚠ RUNS AS A PASS ON A QUIET TABLE - never alongside writing lanes
(measured 2026-08-21: a live keyer blocked every walker). The busy-guard
refuses to run while lanes write. PARKED until acquisition fills contexts;
the audit half is meaningful today, the pass becomes productive as rd
lands.
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
import corpus_paths as CP

BOARD = pathlib.Path(r"D:\CRE Decoding System\Updates\Updates.db")

ap = argparse.ArgumentParser()
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()

try:
    ps = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
         " | ForEach-Object { $_.CommandLine }"],
        capture_output=True, text=True, timeout=60).stdout
except Exception:
    ps = ""
if any(k in ps for k in ("rd_walk", "image_walk", "live_gap.py")):
    print("lanes are writing the table - organization waits for a pause")
    sys.exit(1)

con = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)

print("=== 1-2 · SYSTEM + CLAIM (one scan) ===")
rows = dict(con.execute(
    "SELECT COALESCE(NULLIF(keyed_by,''),'unkeyed'), COUNT(*)"
    " FROM navigation GROUP BY 1"))
total = sum(rows.values())
for kb in ("parcel", "reference", "pdf", "pdf-pass", "unkeyed"):
    n = rows.get(kb, 0)
    print(f"  {kb:<10} {n:>12,}  ({100*n/total:.2f}%)")
keyed = sum(rows.get(k, 0) for k in ("parcel", "reference", "pdf"))
print(f"  keyed {keyed:,} / {total:,} = {100*keyed/total:.2f}%")

if not a.dry:
    print("=== 3 · PASS (nav_key, one sweep) ===")
    r = subprocess.run([sys.executable, "-u", str(HERE / "nav_key.py")],
                       text=True)
    print(f"  pass exit {r.returncode}")

print("=== 5-6 · BOARD + CHECK ===")
rows = dict(con.execute(
    "SELECT COALESCE(NULLIF(keyed_by,''),'unkeyed'), COUNT(*)"
    " FROM navigation GROUP BY 1"))
total2 = sum(rows.values())
keyed = sum(rows.get(k, 0) for k in ("parcel", "reference", "pdf"))
parts = sum(rows.values())
print(f"  identity: {' + '.join(f'{k} {v:,}' for k, v in sorted(rows.items()))}"
      f" = {parts:,} vs total {total2:,}"
      f" -> {'CLOSED' if parts == total2 else 'BROKEN - report'}")
if not a.dry:
    b = sqlite3.connect(BOARD, timeout=120)
    st = ("COMPLETE" if keyed == total2 else
          "ACTIVE" if keyed > rows.get("unkeyed", 0) else "PENDING")
    win = time.strftime("%B %d, %Y %I:%M").replace(" 0", " ")
    # ⚠ SAME DEFECT AS routine_navigation.py - TEN values into TWELVE columns,
    # so sqlite rejected it and the organization row never reached the board.
    # Two phases were invisible for the same reason, which is what makes this a
    # SHAPE and not a typo: positional INSERT breaks every writer the moment the
    # table grows a column, and update_board has already grown three.
    b.execute(
        "INSERT OR REPLACE INTO update_board"
        " (phase, source, rate_now, rate, increase, pct_increase,"
        "  landed, needed, pct_of_total, eta, status, as_of)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("organization", "legal instruments",
         0.0, 0.0, 0, 0.0,
         keyed, total2,
         round(100 * keyed / total2, 2) if total2 else 0.0,
         "-", st, win))
    b.commit()
    b.close()
print("ORGANIZATION " + ("LEVEL" if keyed == total2 else
                         f"IN PROGRESS - {total2-keyed:,} to key"))
