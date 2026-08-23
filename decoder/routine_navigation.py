"""THE NAVIGATION ROUTINE — the 01 phase, systemized (login 2026-08-21:
"we can send that into nav while we wait and we can systemize nav").

The phase's one claim: EVERY id in the Legal Instruments db is TABLED with
its two endpoints (rd_url, pdf_url) minted. Sync (00) lands the ids;
navigation proves the table is ready for acquisition (02). The accretion:

    sync:  source | system_total | source_total | delta | doc_ids
    nav:   + rd_url + pdf_url          <- this phase's columns

Steps, in the six-step grammar:
    1. SYSTEM   count the table per source (a real count - this routine is
                the audit; the 5-minute board reads denoms, never a scan)
    2. CLAIM    count rows missing either url
    3. DELTA    the missing rows are the work list
    4. MINT     fill them (urls are pure functions of the id - nav_append.urls)
    5. BOARD    write the navigation rows into the update board
    6. CHECK    recount: missing must be 0, and the table total must equal
                the sync ledger's system_total (report a mismatch, NEVER
                repair a number to make the check pass)

    python routine_navigation.py            run the six steps
    python routine_navigation.py --dry      steps 1-3 only, write nothing

⚠ BUSY GUARD: the count is a full scan; it must never queue behind writing
lanes (measured: an unguarded scan dropped rd from 17 to 1.5 docs/s).
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
ACRIS = "https://a836-acris.nyc.gov/DS/DocumentSearch/"
RC = "https://www.richmondcountyclerk.com"


def urls(did):
    """(rd_url, pdf_url) - pure functions of the id, same mint as nav_append
    (defined here because nav_append is a SCRIPT - importing it runs it)"""
    if did.startswith("RC_"):
        return (f"{RC}/Search/viewDocumentInfo/{did[3:]}",
                f"{RC}/ViewVscmsDocument/ViewContent?p_endorsementId={did[3:]}")
    return (f"{ACRIS}DocumentDetail?doc_id={did}",
            f"{ACRIS}DocumentImageView?doc_id={did}")

ap = argparse.ArgumentParser()
ap.add_argument("--dry", action="store_true")
a = ap.parse_args()

# ⚠ never scan while lanes write
try:
    ps = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
         " | ForEach-Object { $_.CommandLine }"],
        capture_output=True, text=True, timeout=60).stdout
except Exception:
    ps = ""
if any(k in ps for k in ("rd_walk", "image_walk", "nav_key", "live_gap.py")):
    print("lanes are writing the table - navigation audit waits; run again"
          " at a pause")
    # ⚠ DECLINING WITH NOTHING IS A WASTED TRIP. The full audit reads
    # rd_url/pdf_url, so it is a TABLE scan of 16.5 GB - measured 64.8 s per
    # 200,000 rows under lane load, ~2.2 HOURS - and the guard above is right
    # to refuse it (an unguarded scan once dropped rd from 17 to 1.5 docs/s).
    #
    # But the fleet runs nearly all the time, so "wait for a pause" means this
    # phase's claim goes UNPROVEN for days while `board_truth.py` openly
    # depends on it. A bounded tail probe costs ~65 s and answers the part that
    # actually changes: the mint is a pure function of the id (see urls()) and
    # every insert path mints, so an unminted row is a NEW row that slipped
    # through - and new rows are at the TAIL.
    #
    # ⚠ THIS IS A PARTIAL RESULT AND MUST NEVER PRINT "LEVEL". It narrows the
    # unknown from everything to everything-but-the-tail; it does not close it.
    try:
        _c = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)
        _mx = _c.execute("SELECT max(rowid) FROM navigation").fetchone()[0] or 0
        _n, _miss = _c.execute(
            "SELECT COUNT(*), SUM(CASE WHEN COALESCE(rd_url,'')=''"
            " OR COALESCE(pdf_url,'')='' THEN 1 ELSE 0 END)"
            " FROM navigation WHERE rowid>?", (_mx - 200000,)).fetchone()
        _c.close()
        print(f"  PARTIAL tail probe · last {_n:,} rows ·"
              f" missing urls {_miss or 0:,}"
              + ("  (tail clean - the full claim is still UNPROVEN)"
                 if not _miss else
                 "  ⚠ UNMINTED ROWS AT THE TAIL - report, do not repair"))
    except Exception as _e:
        print(f"  tail probe failed ({type(_e).__name__}) - reporting nothing")
    sys.exit(1)

con = sqlite3.connect(CP.NAV_DB, timeout=600)
con.execute("PRAGMA busy_timeout=300000")

SRC = {"acris": "id NOT LIKE 'RC%'", "richmond": "id LIKE 'RC%'"}

print("=== 1-2 · SYSTEM + CLAIM (one scan) ===")
tally = {}
for src, w in SRC.items():
    total, miss = con.execute(
        f"SELECT COUNT(*), SUM(CASE WHEN COALESCE(rd_url,'')=''"
        f" OR COALESCE(pdf_url,'')='' THEN 1 ELSE 0 END)"
        f" FROM navigation WHERE {w}").fetchone()
    tally[src] = (total, miss or 0)
    print(f"  {src:<9} rows {total:>10,} · missing urls {miss or 0:,}")

print("=== 3-4 · MINT the missing ===")
fixed = 0
for src, w in SRC.items():
    if not tally[src][1]:
        continue
    rows = con.execute(f"SELECT id FROM navigation WHERE {w} AND"
                       f" (COALESCE(rd_url,'')='' OR COALESCE(pdf_url,'')='')"
                       ).fetchall()
    if a.dry:
        print(f"  {src}: {len(rows):,} to mint (dry - not written)")
        continue
    for (did,) in rows:
        rd, pdf = urls(did)
        con.execute("UPDATE navigation SET rd_url=?, pdf_url=? WHERE id=?",
                    (rd, pdf, did))
        fixed += 1
    con.commit()
print(f"  minted {fixed:,}")

print("=== 6 · CHECK ===")
sy = sqlite3.connect(
    r"D:\CRE Decoding System\00 Synchronizations"
    r"\Legal Instruments Synchronization\Legal Instruments Synchronization.db",
    timeout=120)
ok = True
for src, w in SRC.items():
    total, miss = con.execute(
        f"SELECT COUNT(*), SUM(CASE WHEN COALESCE(rd_url,'')=''"
        f" OR COALESCE(pdf_url,'')='' THEN 1 ELSE 0 END)"
        f" FROM navigation WHERE {w}").fetchone()
    led = sy.execute("SELECT system_total + delta FROM synchronization"
                     " WHERE source=? ORDER BY rowid DESC LIMIT 1",
                     (src,)).fetchone()
    led = led[0] if led else None
    level = (miss or 0) == 0 and (led is None or led == total)
    ok &= level
    led_s = f"{led:,}" if led is not None else "-"
    print(f"  {src:<9} rows {total:>10,} · missing urls {miss or 0:,} ·"
          f" sync ledger {led_s:>10} ·"
          f" {'LEVEL' if level else 'NOT LEVEL - report, do not repair'}")
    if not a.dry:
        b = sqlite3.connect(BOARD, timeout=120)
        st = "COMPLETE" if level else ("ACTIVE" if fixed else "STALLED")
        win = time.strftime("%B %d, %Y %I:%M").replace(" 0", " ")
        # ⚠ NAME THE COLUMNS. This was a positional `VALUES (?,?,?,?,?,?,?,?,?,?)`
        # - TEN values into a TWELVE column table - so sqlite rejected it and
        # **the navigation row was never written**: the phase whose whole job is
        # to assert "every document is tabled" was itself absent from the board.
        # Had sqlite accepted it, it would have been worse than absent: every
        # value lands one slot early, so `landed` would have received `needed`,
        # `pct_of_total` (REAL) would have received the STATUS STRING, and
        # status/as_of would be NULL - a row that reads as data and is noise.
        #
        # Positional INSERT is the defect shape here, not this particular
        # miscount: update_board has already grown columns once (rate_now,
        # pct_increase, eta), and every future column silently breaks every
        # positional writer. Named columns cannot shift.
        landed = total - (miss or 0)
        b.execute(
            "INSERT OR REPLACE INTO update_board"
            " (phase, source, rate_now, rate, increase, pct_increase,"
            "  landed, needed, pct_of_total, eta, status, as_of)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            ("navigation", src,
             0.0, 0.0,              # nav mints in bursts; a rate would be noise
             fixed, 0.0,            # `fixed` is an INCREASE - urls minted now
             landed, total,
             round(100 * landed / total, 2) if total else 0.0,
             "-" if level else "",  # no eta for a phase that is not a walk
             st, win))
        b.commit()
        b.close()
print("NAVIGATION LEVEL" if ok else "NOT LEVEL - see above")
