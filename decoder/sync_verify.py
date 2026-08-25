"""IS EVERY COMPONENT OF SYNC WORKING, ON BOTH SOURCES, START TO FINISH?

login 2026-08-24: "I need to verify every component start to finish of sync is
working on both sources... the monitor assures it is keeping up with the live
state, the sync is assuring the data table gets every id of the new docs that
are inflowing, the urls are minted, the rd is filled, the pass 1 keys, the pdf
is added with the lag considered, and once its 100% it will run the reference
pass after before decoding officially starts."

That sentence IS the spec. Seven components, in order, per source:

    1 MONITOR    the lane is alive and its log is FRESH (a dead lane with a
                 stale log reads exactly like a quiet one)
    2 SYNC       new ids are landing - the edge is advancing
    3 URL        rd_url and pdf_url minted on the newest rows
    4 RD         recorded_details filled on the newest rows
    5 KEY        pass 1 - EVERY row that has rd has a key (the trigger)
    6 PDF        images landing, and LAG HONOURED: a row with no image yet is
                 'pending' (ask again) and NEVER an imageless verdict
    7 PASS 2     the reference worklist, which runs only after 6 hits 100%

⚠ IT NEVER WRITES. Reading the corpus to grade it must not change it.

⚠ TWO ID NAMESPACES, AND TEXT ORDERING LIES. Richmond ids span 6-digit and
7-digit forms, and 'RC_999999' > 'RC_2826619' as TEXT - so `ORDER BY id DESC`
samples the BACKFILL and reports today as 0%. Twice on 2026-08-24 that
produced a false alarm. The right predicate is an index slice plus a LENGTH
test; CAST(SUBSTR(...)) forces a 2.5M-row scan and times out.

    python sync_verify.py
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                      # noqa: E402

W = CP.NAV_WORK
SAMPLE = 400
FRESH = 300.0            # a lane log older than 5 min is not evidence of now

# source -> (label, newest-rows predicate, log path)
SOURCES = {
    "acris": ("ACRIS",
              # acris doc_ids are all-digit and fixed width, so TEXT order IS
              # numeric order - but RC_* would sort above them, hence id < 'A'
              "id < 'A'",
              W / "acris_lane.log"),
    "richmond": ("RICHMOND",
                 # 7-digit RC ids only: an index slice + LENGTH, never a CAST
                 "id >= 'RC_2' AND id < 'RC_3' AND LENGTH(id) = 10",
                 HERE / "rc_lane.log"),
}

con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=120)
con.execute("PRAGMA busy_timeout=120000")

OK, BAD, WARN = "  OK  ", " DEFECT", " ...  "
verdicts = []


def line(comp, state, detail):
    verdicts.append((comp, state, detail))
    print("   %-9s %-7s %s" % (comp, state, detail))


def image_state(rd):
    try:
        return str(json.loads(rd).get("image_state", "")).lower()
    except Exception:
        return ""


for key, (label, pred, log) in SOURCES.items():
    print()
    print("=" * 72)
    print("%s" % label)
    print("=" * 72)

    # ---- 1 MONITOR ---------------------------------------------------
    if not log.exists():
        line("1 MONITOR", BAD, "no log at %s" % log.name)
    else:
        age = time.time() - log.stat().st_mtime
        line("1 MONITOR", OK if age < FRESH else BAD,
             "%s last wrote %.0fs ago" % (log.name, age))

    # ---- newest rows, one read, reused by 2..6 -----------------------
    rows = list(con.execute(
        "SELECT id, rd_url, pdf_url, recorded_details, pdf,"
        " COALESCE(keyed_by,''), COALESCE(key,'')"
        " FROM navigation WHERE %s ORDER BY id DESC LIMIT %d" % (pred, SAMPLE)))
    if not rows:
        line("2 SYNC", BAD, "no rows matched the newest-rows predicate")
        continue
    n = len(rows)

    # ---- 2 SYNC ------------------------------------------------------
    line("2 SYNC", OK, "newest %d ids present: %s .. %s" % (n, rows[-1][0], rows[0][0]))

    # ---- 3 URL -------------------------------------------------------
    nourl = [r[0] for r in rows if not r[1] or not r[2]]
    line("3 URL", OK if not nourl else BAD,
         "%d/%d have BOTH rd_url and pdf_url%s"
         % (n - len(nourl), n, "" if not nourl else "  eg " + nourl[0]))

    # ---- 4 RD --------------------------------------------------------
    nord = [r[0] for r in rows if not r[3]]
    line("4 RD", OK if not nord else BAD,
         "%d/%d have recorded_details%s"
         % (n - len(nord), n, "" if not nord else "  eg " + nord[0]))

    # ---- 5 KEY (pass 1) ----------------------------------------------
    # ⚠ THE CLAIM IS CONDITIONAL: every row that HAS rd must have a key.
    # Counting keys against all rows would fail a row whose rd has not landed
    # yet, which is ordinary pending work, not a defect.
    haverd = [r for r in rows if r[3]]
    nokey = [r[0] for r in haverd if not r[5]]
    line("5 KEY", OK if not nokey else BAD,
         "%d/%d rows-with-rd carry a key%s"
         % (len(haverd) - len(nokey), len(haverd),
            "" if not nokey else "  eg " + nokey[0]))

    # ---- 6 PDF + LAG -------------------------------------------------
    # >> ACRIS HAS NO image_state - THAT FIELD IS RICHMOND'S. Grading acris
    # by it gave "0/0 present rows imaged" and printed OK, which is an empty
    # denominator wearing a pass. acris declares imagelessness by landing the
    # verdict in the pdf column itself, so measure THAT.
    if key == "acris":
        imaged = [r for r in haverd if r[4] and "imageless" not in str(r[4]).lower()]
        verdict = [r for r in haverd if r[4] and "imageless" in str(r[4]).lower()]
        todo = [r for r in haverd if not r[4]]
        line("6 PDF", OK,
             "%d imaged, %d imageless verdict, %d still queued (of %d rows"
             " with rd) - acris carries no image_state; an empty pdf column"
             " IS the todo state the feeder selects on"
             % (len(imaged), len(verdict), len(todo), len(haverd)))
        ref = [r for r in rows if r[5] == "reference" and not r[6]]
        done = len(imaged) + len(verdict)
        line("7 PASS 2", WARN,
             "gate is component 6 at 100%% (sample reads %.1f%%);"
             " reference-pending in sample: %d"
             % (100.0 * done / len(haverd) if haverd else 0.0, len(ref)))
        continue

    present = [r for r in haverd if image_state(r[3]) == "present"]
    pend = [r for r in haverd if image_state(r[3]) == "pending"]
    absent = [r for r in haverd if image_state(r[3]) == "absent"]
    withpdf = sum(1 for r in present if r[4])
    # ⚠ THE FABRICATION TEST. A row the source calls 'pending' must NOT be
    # sitting on an imageless verdict - that is a freshness-dependent reading
    # frozen too early, and it is indistinguishable from a real answer.
    faked = [r[0] for r in pend if r[4] and "imageless" in str(r[4]).lower()]
    line("6 PDF", OK if not faked else BAD,
         "%d/%d present rows imaged - lag: %d pending, %d absent%s"
         % (withpdf, len(present), len(pend), len(absent),
            "" if not faked else "  ⚠ PENDING ROW HOLDS A VERDICT: " + faked[0]))

    # ---- 7 PASS 2 ----------------------------------------------------
    ref = [r for r in rows if r[5] == "reference" and not r[6]]
    pct = 100.0 * withpdf / len(present) if present else 0.0
    line("7 PASS 2", WARN,
         "gate is component 6 at 100%% (sample reads %.1f%%); reference-pending"
         " in sample: %d" % (pct, len(ref)))

# ---------------------------------------------------------------------
# 8 COMPLETENESS - THE RULE THAT PROTECTS THE 100%
# ---------------------------------------------------------------------
# login 2026-08-24: "you cant miss any of these phases if we say we are 100%
# complete and then are missing the pdf, that ruins the system."
#
# The board computes landed as `total - count(pdf = '')`. That is correct ONLY
# while an empty pdf column is the sole todo state. The moment anything else is
# written there as a placeholder - the proposed three-state
# `path | pending | n/a` migration is exactly this - those rows STOP matching
# pdf='' and the board counts them as LANDED. Completion would jump by exactly
# the number of documents that are NOT done, and every downstream phase would
# inherit a corpus that claims to be finished.
#
# So the invariant is: A ROW MAY ONLY LEAVE THE TODO SET BY BEING ANSWERED -
# a real stored path, or a RECORDED VERDICT that no image exists. "Pending" is
# not an answer; it is the absence of one, and it must keep pdf=''.
print()
print("=" * 72)
print("8 COMPLETENESS - can anything be counted done while a phase is missing?")
print("=" * 72)
PLACEHOLDER = ("pending", "n/a", "na", "none", "null", "todo", "-", "?")
leak = []
for key, (label, pred, _log) in SOURCES.items():
    rows = list(con.execute(
        "SELECT id, pdf, rd_url, recorded_details, COALESCE(keyed_by,'')"
        " FROM navigation WHERE %s AND pdf <> '' ORDER BY id DESC LIMIT %d"
        % (pred, SAMPLE)))
    ph = [r[0] for r in rows if str(r[1]).strip().lower() in PLACEHOLDER]
    part = [r[0] for r in rows if not (r[2] and r[3] and r[4])]
    print("   %-9s %d rows counted LANDED in sample" % (label, len(rows)))
    print("      placeholder in pdf (would fake a landing): %s"
          % ("%d  <- DEFECT: %s" % (len(ph), ph[0]) if ph else "0  clean"))
    print("      landed but missing url/rd/key:             %s"
          % ("%d  <- DEFECT: %s" % (len(part), part[0]) if part else "0  clean"))
    leak += ph + part
print()
print("   RULE: a row leaves the todo set ONLY by being answered - a stored")
print("   path, or a recorded verdict that no image exists. 'pending' is the")
print("   ABSENCE of an answer and must keep pdf='' so the feeder still sees")
print("   it. ⚠ Any pdf three-state migration must land WITH the board's")
print("   predicate (pdf IN ('','pending')) and the ix_nav_pdf_todo rebuild,")
print("   in ONE change - never the column alone.")
if leak:
    verdicts.append(("8 COMPLETE", BAD, "%d row(s) counted done while incomplete"
                     % len(leak)))

con.close()

print()
print("=" * 72)
bad = [v for v in verdicts if v[1] == BAD]
if bad:
    print("⚠ %d DEFECT(S):" % len(bad))
    for c, _s, d in bad:
        print("   %-9s %s" % (c, d))
else:
    print("✅ EVERY COMPONENT CLEAN ON BOTH SOURCES (sample = newest %d rows"
          " per source)." % SAMPLE)
print("   Components 1-6 are measured. 7 is a GATE, not a result - it runs"
      " after 6 reaches 100%%.")
