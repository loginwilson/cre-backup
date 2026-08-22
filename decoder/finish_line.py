"""THE FINISH LINE — supervise every remaining stage, start to finish.

    ACRIS_CORPUS_ROOT=D:/acris python finish_line.py

Sequence, each stage GATED on the previous one actually succeeding:

    1  wait for dedupe          (writer on the DB - nothing else may write)
    2  land references+remarks  (writer)
    3  verify component coverage against known targets - REFUSE to continue short
    4  start Supabase push      (reader - safe under WAL while later writers run)
    5  wait for the walk        (independent of the DB)
    6  land the walk's queue    (writer - WAL allows the concurrent push reader)
    7  wait for Supabase push, then re-push the walk's delta
    8  run the routine          (edge -> gap -> land -> map -> push -> re-probe)
    9  print the final scoreboard

WARNING - ONE WRITER AT A TIME. Every deadlock today was two writers colliding
(or one connection fighting itself). This script owns the ordering so that can't
happen: stages 1, 2 and 6 are the only writers and they never overlap.

WARNING - GATES, NOT HOPE. A chain that charges ahead reported rc=0 today while
landing nothing. Each stage here checks the thing the previous stage claims to
have produced, not its exit code alone.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP

PY = sys.executable
TARGETS = {
    "document": 21_606_916,
    "parcel_document": 26_440_183,      # EXACT - measured by the dedupe. Lower
    # than the 26.7M row estimate because a document touching one lot via
    # several property rows collapses to ONE (bbl, document_id) pair.
    # MEASURED figures, not row counts. Socrata publishes ROWS; the PK collapses
    # true duplicates (same doc+type+name party listed twice with address
    # variants: 46,098 of 11.0M). Targets below are what a CORRECT landing
    # yields, learned the same way as parcel_document's.
    "party_document": 10_989_288,
    "reference_document": 11_899_912,   # EXACT - full-pointer key; 4.5M true dupes
    "remark_document": 6_224_012,
}


def say(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def counts():
    con = sqlite3.connect(
        "file:" + str(CP.SPEC_DB).replace("\\", "/") + "?mode=ro",
        uri=True, timeout=600)
    con.execute("PRAGMA busy_timeout=600000")
    out = {}
    for t in TARGETS:
        try:
            out[t] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            out[t] = -1
    con.close()
    return out


def run(label, args, logname):
    log = HERE / logname
    say(f"{label} starting -> {logname}")
    with log.open("w", encoding="utf-8") as f:
        rc = subprocess.call([PY, "-u"] + args, stdout=f,
                             stderr=subprocess.STDOUT, cwd=str(HERE))
    tail = log.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    say(f"{label} rc={rc}")
    for t in tail[-3:]:
        print(f"      {t}", flush=True)
    return rc


def wait_for(path, patterns, label, poll=20):
    say(f"waiting on {label} ({path})")
    p = HERE / path
    while True:
        txt = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        for pat in patterns:
            if pat in txt:
                say(f"{label}: matched '{pat}'")
                return pat
        time.sleep(poll)


def main():
    # ── 1 · dedupe ────────────────────────────────────────────────────────
    hit = wait_for("_dedupe3.log", ["DONE", "Traceback", "locked"], "dedupe")
    if hit != "DONE":
        say("DEDUPE FAILED - stopping. Nothing else may write to a broken table.")
        sys.exit(1)

    # ── 2 · references + remarks ──────────────────────────────────────────
    if run("land_index_rest", ["land_index_rest.py", "--apply"],
           "_fl_rest.log") != 0:
        say("references/remarks landing FAILED - stopping.")
        sys.exit(1)

    # ── 3 · the drive must actually hold the specification ────────────────
    c = counts()
    say("component coverage on the drive:")
    bad = []
    for t, want in TARGETS.items():
        ok = c[t] >= want
        say(f"    {t:<20} {c[t]:>12,}  (target {want:,})  {'OK' if ok else 'SHORT'}")
        if not ok:
            bad.append(t)
    if bad:
        say(f"REFUSING to push a short specification: {', '.join(bad)}")
        sys.exit(1)
    say("DRIVE COMPLETE - the one-touch specification is landed.")

    # ── 4 · the walk FIRST (user's order: prove live sync before pushing) ──
    hit = wait_for("_live_gap3.log", ["  DONE ", "REFUSED at"], "gap walk", 30)
    if hit != "  DONE ":
        say("WALK WAS REFUSED - routine will re-ask what remains.")
    if run("live_land", ["live_land.py", "--apply"], "_fl_liveland.log") != 0:
        say("live_land FAILED - stopping before the routine would re-walk it.")
        sys.exit(1)

    # ── 5 · ROUTINE start-to-finish: edge, gap, land, map, push, re-probe ──
    say("RUNNING THE ROUTINE")
    run("routine", ["routine_4am.py"], "_fl_routine.log")

    # ── 6 · only now: Supabase, everything at once ────────────────────────
    say("Supabase push - full specification including the walked delta")
    run("supabase_push", ["supabase_setup.py", "--push", "--batch", "5000"],
        "_fl_supa.log")

    # ── 9 · scoreboard ───────────────────────────────────────────────────
    c = counts()
    say("FINAL STATE:")
    for t in TARGETS:
        say(f"    {t:<20} {c[t]:>12,}")
    edge = HERE / "_crfn_edge.json"
    if edge.exists():
        e = json.loads(edge.read_text(encoding="utf-8"))
        say(f"    span outstanding     {e.get('span')}  "
            f"({'LEVEL WITH LIVE' if e.get('span') == 0 else 'still open'})")
    say("FINISH LINE COMPLETE")


if __name__ == "__main__":
    main()
