"""THE ACQUISITION ROUTINE — the 02 phase, systemized (login 2026-08-22:
"acq is python all 4 now so it should be able to slot in").

⚠ WHY THIS FILE DID NOT EXIST UNTIL NOW. Sync, navigation and organization
were systemized on 2026-08-21; acquisition was not, and the reason was not
oversight — the richmond pdf lane had a HUMAN IN THE MIDDLE. It ran as a
DevTools snippet pasted into an Edge tab, and it stalled whenever the browser
crashed under its own download-manager growth ("Couldn't download - Browser
crashed", ~84k records). You cannot schedule a person clicking a button. On
2026-08-22 that lane became `rc_pdf_pull.py` and the phase became automatable.

The phase's one claim: EVERY id navigation tabled has its two products
LANDED — the recorded details, and the document itself — or carries a
TERMINAL state saying why it never will. The accretion:

    sync:  source | system_total | source_total | delta | doc_ids
    nav:   + rd_url + pdf_url
    acq:   + recorded_details + pdf        <- this phase's columns

⚠ THE GATE IS THE `pdf` COLUMN, AND IT IS EVIDENCE — MEASURED 2026-08-22.
`rd_url`/`pdf_url` are minted at nav time and are populated for all 24.1M
rows, landed or not. `pdf` is written by the LANDER and is populated only
where a file actually arrived (measured: rowid 5k -> 2001/2001 set;
rowid 2M/12M/20M -> 0/2001 set). So counting `pdf` counts files, not our own
optimism. routine_4am says it best: "a count computed from our own output is
not evidence; every failure today looked like success by that measure."

Steps, in the six-step grammar:
    1. SYSTEM   count each product per source (a real count - this routine
                IS the audit; the board reads denominators, never a scan)
    2. CLAIM    the unlanded remainder for each product
    3. DELTA    the work list, and which lane owns it
    4. (no pull - the LANES do the pulling and they are long-running.
                This routine audits and gates; it never launches them.
                Reports which lanes are alive so a gap has an owner.)
    5. BOARD    write the four acquisition rows into the update board
    6. CHECK    identity per source per product:
                    landed + imageless + unlanded == total
                Report a mismatch. NEVER repair a number to make it pass.

    python routine_acquisition.py            the six steps
    python routine_acquisition.py --dry      steps 1-3 only, write nothing

⚠ BUSY GUARD: steps 1-2 are full scans and must never queue behind the
writing lanes (measured: an unguarded scan dropped rd from 17 to 1.5 docs/s;
a live keyer blocked every walker). Unlike nav and org, THIS phase's lanes
are the ones it audits — so the guard is advisory here: --dry is always safe,
a full run wants a pause. Pass --anyway to override deliberately.

⚠ RICHMOND UNLANDED IS NOT ALL FAILURE. Richmond attaches scans overnight —
a step at ~24h, not a decay curve (0/15 imaged at age 0, 11/11 at age 1 day).
A document recorded today is CORRECTLY unlanded. Only age separates `pending`
from structurally imageless, which is why the terminal call is made at 7 days
and never on a single read. ACRIS by contrast is 400/400 imaged same-day.
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
SRC = {"acris": "id NOT LIKE 'RC%'", "richmond": "id LIKE 'RC%'"}

# lane -> what it lands. Reported in step 4 so an unlanded remainder has an
# owner rather than being a number nobody is responsible for.
LANES = {
    "rd_walk":     ("acris",    "rd"),
    "image_walk":  ("acris",    "pdf"),
    "rc_rd_walk":  ("richmond", "rd"),
    "rc_pdf_pull": ("richmond", "pdf"),
    "rc_feed":     ("richmond", "pdf (mint)"),
    "rc_pdf_land": ("richmond", "pdf (land)"),
}

ap = argparse.ArgumentParser()
ap.add_argument("--dry", action="store_true", help="steps 1-3 only")
ap.add_argument("--anyway", action="store_true", help="scan even while lanes write")
a = ap.parse_args()

try:
    ps = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
         " | ForEach-Object { $_.CommandLine }"],
        capture_output=True, text=True, timeout=60).stdout
except Exception:
    ps = ""
alive = sorted({name for name in LANES if name in ps})

# ⚠ `--dry` USED TO BYPASS THIS GUARD AND IT WAS NEVER SAFE TO. The condition
# was `if alive and not (a.dry or a.anyway)`, and the message below told the
# reader to "run --dry for a safe read" - but --dry only skips the WRITE, and
# the write was never the expensive part. Steps 1-2 read `recorded_details` and
# `pdf`, so they are a TABLE scan of 16.5 GB either way: measured 64.8 s per
# 200,000 rows under lane load, ~2.2 hours for the corpus.
#
# Caught by running the chain: `phase_chain.py --dry` walked straight past the
# guard and started exactly the unguarded scan this file was written to prevent
# (the one that dropped rd from 17 to 1.5 docs/s). A guard with an exemption for
# the mode everyone reaches for by default is not a guard.
#
# ⚠ ONLY --anyway OVERRIDES NOW, because only --anyway is a deliberate choice.
# `--dry` means "change nothing", which is a promise about WRITES; it can never
# be a promise about COST.
if alive and not a.anyway:
    print("lanes are writing: " + ", ".join(alive))
    print("a full scan here would slow them (measured: rd 17 -> 1.5 docs/s).")
    print("--dry does NOT make this cheap - it skips the write, not the scan.")
    print("run --anyway to scan deliberately, or wait for a pause")
    sys.exit(1)

con = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)
con.execute("PRAGMA busy_timeout=300000")

# ---------------------------------------------------------------- 1-2
print("=== 1-2 · SYSTEM + CLAIM (one scan per source) ===")
tally = {}
for src, w in SRC.items():
    row = con.execute(
        f"SELECT COUNT(*),"
        f" SUM(CASE WHEN COALESCE(recorded_details,'')<>'' THEN 1 ELSE 0 END),"
        f" SUM(CASE WHEN COALESCE(pdf,'')<>'' AND pdf<>'imageless'"
        f"          THEN 1 ELSE 0 END),"
        f" SUM(CASE WHEN pdf='imageless' THEN 1 ELSE 0 END)"
        f" FROM navigation WHERE {w}").fetchone()
    total, rd, pdf, imageless = (row[0], row[1] or 0, row[2] or 0, row[3] or 0)
    tally[src] = dict(total=total, rd=rd, pdf=pdf, imageless=imageless)
    print(f"  {src:<9} rows {total:>11,}")
    print(f"    rd   landed {rd:>11,}  unlanded {total - rd:>11,}")
    print(f"    pdf  landed {pdf:>11,}  imageless {imageless:>9,}"
          f"  unlanded {total - pdf - imageless:>11,}")

# ---------------------------------------------------------------- 3-4
print("=== 3-4 · DELTA + who owns it ===")
for src, t in tally.items():
    for prod, done in (("rd", t["rd"]),
                       ("pdf", t["pdf"] + t["imageless"])):
        gap = t["total"] - done
        owners = [n for n, (s, p) in LANES.items()
                  if s == src and p.startswith(prod)]
        run = [n for n in owners if n in alive]
        state = ("RUNNING: " + ", ".join(run)) if run else (
            "NO LANE RUNNING" if gap else "-")
        print(f"  {src:<9} {prod:<3} gap {gap:>11,}   {state}")

if a.dry:
    print("--dry: steps 5-6 skipped, nothing written")
    sys.exit(0)

# ---------------------------------------------------------------- 5-6
print("=== 5-6 · BOARD + CHECK ===")
win = time.strftime("%B %d, %Y %I:%M %p").replace(" 0", " ")
b = sqlite3.connect(BOARD, timeout=120)
ok = True
for src, t in tally.items():
    for prod in ("rd", "pdf"):
        if prod == "rd":
            landed, terminal = t["rd"], 0
        else:
            landed, terminal = t["pdf"], t["imageless"]
        unlanded = t["total"] - landed - terminal

        # THE IDENTITY. Report, never repair.
        identity = (landed + terminal + unlanded) == t["total"]
        level = unlanded == 0
        ok &= identity and level

        pct = round(100 * (landed + terminal) / t["total"], 2) if t["total"] else 0.0
        status = "COMPLETE" if level else "ACTIVE"
        b.execute(
            "INSERT OR REPLACE INTO update_board"
            " (phase,source,rate_now,rate,increase,pct_increase,landed,needed,"
            "  pct_of_total,eta,status,as_of)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"acquisition {prod}", src, 0.0, 0.0, 0, 0.0,
             landed + terminal, t["total"], pct,
             "complete" if level else "-", status, win))
        flag = "" if identity else "  ⚠ IDENTITY BROKEN - report, do not repair"
        print(f"  {src:<9} {prod:<3} landed {landed:>11,} terminal {terminal:>8,}"
              f" unlanded {unlanded:>11,} {pct:>6.2f}%  {status}{flag}")
b.commit()
b.close()
print("ACQUISITION LEVEL" if ok else "NOT LEVEL - see above")
