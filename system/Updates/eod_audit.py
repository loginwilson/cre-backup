"""END-OF-DAY AUDIT — a safety check OUTSIDE the system, never part of it.

    python eod_audit.py          # prints PASS/FAIL lines, writes eod/YYYY-MM-DD.md

Login 2026-08-23: *"an end of the day audit... not part of the system, but just
run at the end of the day to assure the system is functioning and no lapses
occured."* And earlier, the binding constraint: the audit must not slow the
pipeline to audit balance.

⚠ THE ONE RULE: **NO SPINE SCANS.** Measured twice (2026-08-21 keyers, and
2026-08-23 my own audit queries): unindexed COUNT(*)s on the 19 GB table
starved the lanes — acris pdf fell 9.9 -> 3.8/s and its ETA read 61 days
instead of 24. An audit that costs the system its evening throughput is a
lapse, not a safety. Everything here reads EDGES, FILES, MTIMES and the board:

    1  ACRIS edge      our crfn edge still resolves at the source; edge+1 state
    2  RICHMOND edge   today's window answers (rows or explicit NO RECORDS)
    3  LANES ALIVE     every expected process present
    4  LOGS FRESH      each lane's log written recently (a lane that lands but
                       logs nowhere is INVISIBLE to the board - found 2026-08-23)
    5  BOARD FRESH     as_of recent, and no row reads STALLED
    6  BACKUP BANKED   cre-backup's last commit is from today

Exit 0 all-pass, 1 otherwise. Report appended to eod/ so lapses have a paper
trail. ⚠ An unreachable source at audit time is reported as UNPROVEN, never as
a failure of our system - and never as "quiet".
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sqlite3
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
DECODER = pathlib.Path(r"C:\Users\smile\Downloads\Source Folder"
                       r" (Real Estate Data)\Decoder Prompt\decoder")
sys.path.insert(0, str(DECODER))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W = pathlib.Path(r"D:\CRE Decoding System\01 Navigations"
                 r"\Legal Instruments Navigation\_working")
results = []


def check(name, ok, detail):
    results.append((name, ok, detail))
    print("  %-4s %-14s %s" % ("PASS" if ok else ("FAIL" if ok is False
                                                  else "?"), name, detail),
          flush=True)


# 1 · ACRIS EDGE ------------------------------------------------------------
try:
    import json as _json
    import acris_edge as AE
    edge = int(_json.loads((DECODER / "_crfn_edge.json")
                           .read_text(encoding="utf-8"))["edge"])
    st, did = AE.quick_crfn(edge)
    check("acris-edge", st == "live",
          "crfn %d %s (doc %s)" % (edge, st, did or "-"))
except Exception as e:
    check("acris-edge", None, "UNPROVEN: %s" % e)

# 2 · RICHMOND EDGE ---------------------------------------------------------
try:
    import rc_sync as RCS
    today = dt.date.today().strftime("%m/%d/%Y")
    st, rows, pages = RCS.quick_day(today)
    check("richmond-edge", st in ("rows", "empty"),
          "%s -> %s (%s row(s) on p1, %s page(s))"
          % (today, st, len(rows) if rows else 0, pages))
except Exception as e:
    check("richmond-edge", None, "UNPROVEN: %s" % e)

# 3 · LANES ALIVE -----------------------------------------------------------
EXPECT = ["rd_walk", "image_walk", "rc_feed", "rc_pdf_pull", "rc_pdf_land",
          "acris_live", "rc_live", "routine_update", "board_truth"]
try:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
         " | ForEach-Object { $_.CommandLine }"],
        capture_output=True, text=True, timeout=60).stdout
    missing = [n for n in EXPECT if n not in out]
    check("lanes-alive", not missing,
          "all %d present" % len(EXPECT) if not missing
          else "MISSING: %s" % ", ".join(missing))
except Exception as e:
    check("lanes-alive", None, "UNPROVEN: %s" % e)

# 4 · LOGS FRESH ------------------------------------------------------------
now = time.time()
stale = []
# ⚠ a[1-4]/i[1-3] EXACTLY - the running lanes. `a*` also matched a stale
# rd_walk_a.log from an old session and failed the first audit on a ghost.
for pat, limit in (("rd_walk_a[1-4].log", 1800),
                   ("image_walk_i[1-3].log", 1800)):
    for p in W.glob(pat):
        if p.name.endswith(".err.log"):
            continue
        if now - p.stat().st_mtime > limit:
            stale.append(p.name)
for f, limit in ((DECODER / "acris_live.log", 300),
                 (DECODER / "rc_live.log", 300)):
    if not f.exists() or now - f.stat().st_mtime > limit:
        stale.append(f.name)
check("logs-fresh", not stale,
      "all lane logs current" if not stale else "STALE: %s" % ", ".join(stale))

# 5 · BOARD FRESH -----------------------------------------------------------
try:
    con = sqlite3.connect("file:%s?mode=ro" % (HERE / "Updates.db"),
                          uri=True, timeout=30)
    rows = list(con.execute("SELECT phase, source, status FROM update_board"))
    bad = [(p, s, x) for p, s, x in rows if x == "STALLED"]
    age = time.time() - (HERE / "Updates.db").stat().st_mtime
    con.close()
    ok = bool(rows) and not bad and age < 600
    check("board-fresh", ok,
          "%d row(s), touched %.0fs ago%s"
          % (len(rows), age, "" if not bad else
             " · STALLED: " + ", ".join("%s/%s" % (p, s) for p, s, _ in bad)))
except Exception as e:
    check("board-fresh", None, "UNPROVEN: %s" % e)

# 6 · BACKUP BANKED ---------------------------------------------------------
try:
    out = subprocess.run(
        ["git", "-C", r"C:\dev\cre-backup", "log", "-1", "--format=%cs %h"],
        capture_output=True, text=True, timeout=30).stdout.strip()
    check("backup-banked", out.startswith(dt.date.today().isoformat()),
          "last commit: %s" % (out or "none"))
except Exception as e:
    check("backup-banked", None, "UNPROVEN: %s" % e)

# ── REPORT ─────────────────────────────────────────────────────────────────
fails = [r for r in results if r[1] is False]
unproven = [r for r in results if r[1] is None]
verdict = ("ALL CLEAR" if not fails and not unproven else
           "%d FAIL · %d UNPROVEN" % (len(fails), len(unproven)))
print()
print("EOD %s · %s" % (dt.date.today(), verdict), flush=True)

out_dir = HERE / "eod"
out_dir.mkdir(exist_ok=True)
stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
with (out_dir / ("%s.md" % dt.date.today())).open("a", encoding="utf-8") as f:
    f.write("\n## %s — %s\n\n" % (stamp, verdict))
    for name, ok, detail in results:
        f.write("- **%s** %s — %s\n"
                % ("PASS" if ok else ("FAIL" if ok is False else "UNPROVEN"),
                   name, detail))
sys.exit(1 if fails else 0)
