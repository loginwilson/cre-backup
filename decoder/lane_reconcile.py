"""DOES EVERY FAILURE RESOLVE? - the residue report.

login 2026-08-24: "Can we make sure all errors resolve to 0 errors so that we
are clean and that we solve the code not to have errors in the first place?"

⚠ THE DISTINCTION THAT MAKES THIS ANSWERABLE. Errors OCCURRING can never be
zero - SSLError, ConnectionError and HTTP 400 are the network and ACRIS's own
servers, not our code, and no amount of correctness stops a dropped packet.
What must be zero is the RESIDUE: a failure has to end as a landed document or
as a RECORDED VERDICT, never as a row quietly stuck in between.

So this reports three populations, and only the third is a defect:

    RESOLVED    the doc later landed (pdf or a held imageless verdict).
                Measured 2026-08-24: 92% of all failures, every class.
    DIAGNOSED   still empty, but the failure carries a CAUSE from _frames'
                stop_why - "placeholder(end-marker) at page N" (the source
                truly ends the doc early: its defect) or "non-TIFF at page N"
                (maybe a FORMAT our II/MM test wrongly rejects: ours).
                Honest todo awaiting a POLICY, not a stuck row.
    OUTSTANDING still empty, no cause on record. ⚠ THIS IS THE ONLY NUMBER
                THAT SHOULD TREND TO ZERO, and the one to act on.

⚠ IT NEVER WRITES. Reading the corpus to grade it must not be able to change
it - a repair that runs inside a check is how a check starts passing for the
wrong reason ("never repair a number to make a check pass").

    python lane_reconcile.py            the report
    python lane_reconcile.py --ids      outstanding doc ids, one per line
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sqlite3
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                      # noqa: E402

FAILS = CP.NAV_WORK / "acris_lane_fails.jsonl"
PDF_FAILS = CP.NAV_WORK / "acris_lane_pdf_fails.jsonl"
# the same markers _diagnosed() uses in acris_lane - a cause on the record
CAUSE = ("placeholder(", "non-TIFF at page")

ap = argparse.ArgumentParser()
ap.add_argument("--ids", action="store_true",
                help="print outstanding ids instead of the report")
a = ap.parse_args()


def rows(path):
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                try:
                    yield json.loads(ln)
                except ValueError:
                    continue
    except OSError:
        return


# ⚠⚠ GRADE A FAILURE AGAINST THE STAGE IT FAILED AT (fixed 2026-08-24 after
# login called the first result out: "that makes no sense. my connection is
# sustained and if the server is working for everything else it should be
# working fine"). They were right and the defect was in the MEASUREMENT.
#
# The first version asked one question of every failure - "does this doc have
# a pdf yet?" - and reported 37% outstanding. But `pdf = ''` is the ORDINARY
# state of 91.9% of the corpus. A doc that failed at the RD stage, then landed
# its rd perfectly, is indistinguishable from the 19.8M documents simply not
# reached yet; several flagged ids were 2009 filings while the cursor was
# still in 2003, thousands of documents away.
#
# So an rd failure resolves when RECORDED_DETAILS arrives, and a pdf failure
# resolves when PDF does. Grading either one by the other manufactures alarm
# out of normal pending work - the same family as counting a re-verified
# imageless row as new readiness.
hist = collections.defaultdict(list)          # id -> [err, ...]
stage = {}                                    # id -> "rd" | "pdf"
cause = set()
for path, st in ((FAILS, "rd"), (PDF_FAILS, "pdf")):
    for r in rows(path):
        did = r.get("id")
        if not did:
            continue
        hist[did].append(r.get("err", "?"))
        # a doc that failed at BOTH stages is graded on the LATER one
        stage[did] = "pdf" if stage.get(did) == "pdf" or st == "pdf" else "rd"
        if any(c in str(r.get("msg", "")) for c in CAUSE):
            cause.add(did)

if not hist:
    print("no failures on record - nothing to reconcile")
    raise SystemExit(0)

ids = list(hist)
con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=60)
con.execute("PRAGMA busy_timeout=60000")
state = {}
for i in range(0, len(ids), 900):                 # sqlite param cap
    chunk = ids[i:i + 900]
    q = ("SELECT id, pdf, recorded_details FROM navigation WHERE id IN (%s)"
         % ",".join("?" * len(chunk)))
    for did, pdf, rd in con.execute(q, chunk):
        state[did] = (pdf, rd)
con.close()

resolved, diagnosed, outstanding = [], [], []
for did in ids:
    pdf, rd = state.get(did, ("", ""))
    done = bool(pdf) if stage.get(did) == "pdf" else bool(rd)
    if done:
        resolved.append(did)
    elif did in cause:
        diagnosed.append(did)
    else:
        outstanding.append(did)

if a.ids:
    for did in sorted(outstanding):
        print(did)
    raise SystemExit(0)

tot = len(ids)
nrd = sum(1 for d in ids if stage.get(d) == "rd")
print("FAILURE RESIDUE - %d distinct docs have failed at least once"
      " (%d at rd, %d at pdf)" % (tot, nrd, tot - nrd))
print("  graded per stage: an rd failure resolves when recorded_details"
      " arrives, a pdf failure when pdf does")
print()
print("  RESOLVED    %5d  %5.1f%%  landed later (pdf or imageless verdict)"
      % (len(resolved), 100 * len(resolved) / tot))
print("  DIAGNOSED   %5d  %5.1f%%  empty, but the cause IS on record"
      % (len(diagnosed), 100 * len(diagnosed) / tot))
print("  OUTSTANDING %5d  %5.1f%%  <- the only number that must reach 0"
      % (len(outstanding), 100 * len(outstanding) / tot))
print()

if diagnosed:
    print("DIAGNOSED - awaiting a policy, not a retry:")
    for did in sorted(diagnosed):
        msg = ""
        for r in list(rows(FAILS)) + list(rows(PDF_FAILS)):
            if r.get("id") == did and any(c in str(r.get("msg", ""))
                                          for c in CAUSE):
                msg = str(r.get("msg", ""))
        print("  %-20s %s" % (did, msg[:96]))
    print()

if outstanding:
    by = collections.Counter(hist[d][-1] for d in outstanding)
    print("OUTSTANDING by last error class:")
    for k, v in by.most_common():
        print("  %5d  %s" % (v, k))
    deep = [d for d in outstanding if len(hist[d]) >= 3]
    print()
    print("  of these, %d have failed 3+ times (quarantined - adjudication"
          " re-attempts them at the next lane start)" % len(deep))
    print()
    print("  ⚠ the rest are simply AHEAD OF THE RETRY: they keep pdf='',")
    print("    which IS the todo state the feeder selects on, so they are")
    print("    re-attempted in-run and again when the cursor wraps.")
else:
    print("✅ ZERO OUTSTANDING - every failure ended as a landing or a"
          " recorded verdict.")
