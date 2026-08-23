"""BOARD TRUTH — the acquisition rows counted from the `pdf` COLUMN, not from logs.

    python board_truth.py            # one pass, print + write _board_truth.json
    python board_truth.py --loop     # re-anchor forever (default every 30 min)

WHY THIS EXISTS. The board's acquisition rows were `baseline + delta scraped from
lane logs`. That is COUNTER ARITHMETIC, and counter arithmetic drifts in one
direction only: a lane restart double-counts, a consumed baseline under-counts,
and the row sails past 100% while looking healthy. It has already happened
(2026-08-21, richmond rd pinned at 100.17%) and the standing rule from that day
is *">100% board = counter arithmetic, re-baseline from true count."*

**This file IS that true count.** `pdf` is the evidence column - a row is landed
because there is a path in it, not because a log line said so.

    pdf = ''            unlanded            (todo)
    pdf = 'imageless'   resolved, no image  (COUNTS AS DONE - nothing to fetch)
    pdf = '<path>'      landed
    pdf IS NULL         never minted        (should be 0; reported if not)

⚠ IT DOES NOT REPLACE THE 60s TICK - IT ANCHORS IT. A true count is minutes of
work; the board refreshes every 60 seconds. So truth re-anchors on a slow cadence
and the fast tick carries only the delta since the anchor. The logs stop being
the authority and become what they actually are: a short-term estimate.

⚠ NO TABLE READS. Counting `pdf != ''` directly is a 16.5 GB table scan - measured
64.8 s per 200,000 rows under lane load, ~2.2 HOURS a pass, all of it competing
with the walkers for the same disk. Every count here is INDEX-ONLY:

    ix_nav_pdf_todo  ON navigation(id) WHERE pdf = ''   partial - the todo set
    PK autoindex     ON navigation(id)                  totals

and the source split is a PREFIX (`RC_2113781` vs `2026081700306001`), so both
become RANGE scans on an index we already have, never a LIKE over the table.

    landed = total - todo          per source, both index-only

⚠ THE SUBTRACTION IS THE WHOLE TRICK AND IT HAS ONE ASSUMPTION: every row is
either todo or done. `pdf IS NULL` would break it silently by inflating landed,
so it is counted separately and reported. Never let it be absorbed.

⚠ READ-ONLY, ALWAYS. Opened `mode=ro`. This runs while four rd walkers, three
image walkers and two richmond lanes are writing. It must never take the writer
seat, and it must never be the reason a lane stalls.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(pathlib.Path(
    r"C:\Users\smile\Downloads\Source Folder (Real Estate Data)"
    r"\Decoder Prompt\decoder")))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                    # noqa: E402

OUT = HERE / "_board_truth.json"
LOG = HERE / "board_truth.log"

# ⚠ The prefix is the source split. 'RC_' sorts above every all-digit ACRIS id
# ('R' > '9'), so the two sources are CONTIGUOUS RANGES in the id index - which
# is exactly why these counts are cheap. 'RC`' is the next string after 'RC_'
# ('`' = 0x60 follows '_' = 0x5F), giving a half-open range with no LIKE.
RC_LO, RC_HI = "RC_", "RC`"


def say(m):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def counts(con):
    """Four index-only counts -> per-source (total, todo, null)."""
    q = con.execute

    # ⚠ REPORT EACH COUNT AS IT LANDS. The first version printed only after all
    # five finished, so a pass that ran 15 minutes was indistinguishable from a
    # pass that had hung - and there was no way to see WHICH count was slow.
    # A measurement you cannot watch is one you cannot tune.
    def one(label, sql, *a):
        t = time.time()
        v = q(sql, a).fetchone()[0]
        say("    %-10s %13s  %.0fs" % (label, f"{v:,}", time.time() - t))
        return v, time.time() - t

    rc_total, t2 = one("rc_total",
                       "SELECT count(*) FROM navigation WHERE id>=? AND id<?",
                       RC_LO, RC_HI)
    rc_todo, t4 = one("rc_todo", "SELECT count(*) FROM navigation "
                      "WHERE pdf='' AND id>=? AND id<?", RC_LO, RC_HI)
    todo, t3 = one("todo_all", "SELECT count(*) FROM navigation WHERE pdf=''")
    total, t1 = one("total_all", "SELECT count(*) FROM navigation")
    # ⚠ NULL is the assumption-breaker. It is NOT in the todo index and NOT a
    # path, so `total - todo` would silently count it as landed. Counted here
    # so it can never hide. This one does touch the table - but only for rows
    # that should not exist, and it is bounded by being reported, not summed.
    nulls, t5 = one("nullprobe", "SELECT count(*) FROM navigation "
                    "WHERE pdf IS NULL AND rowid<=200000")
    say("  counted in %.0fs total" % (t1 + t2 + t3 + t4 + t5))
    return {
        "acris": (total - rc_total, todo - rc_todo),
        "richmond": (rc_total, rc_todo),
        "null_probe": nulls,
    }


def measure():
    con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=600)
    try:
        c = counts(con)
    finally:
        con.close()

    out = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": "pdf column",
           "null_probe_first_200k": c["null_probe"], "sources": {}}
    for src in ("acris", "richmond"):
        total, todo = c[src]
        out["sources"][src] = {"total": total, "todo": todo,
                               "landed": total - todo}
        say("%-9s total %13s · todo %13s · LANDED %13s  (%.2f%%)"
            % (src, f"{total:,}", f"{todo:,}", f"{total-todo:,}",
               100.0 * (total - todo) / total if total else 0.0))
    if c["null_probe"]:
        # ⚠ Never repair a number to make a check pass - report it.
        say("⚠ %d NULL pdf rows in the first 200k - the landed figures above "
            "are INFLATED by rows that were never minted. Do not trust them "
            "until this is 0." % c["null_probe"])
        out["warning"] = "null pdf rows present; landed inflated"
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    say("wrote %s" % OUT.name)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--every", type=int, default=1800)
    a = ap.parse_args()
    while True:
        try:
            measure()
        except Exception as e:
            say("FAILED %s: %s" % (type(e).__name__, e))
        if not a.loop:
            break
        time.sleep(a.every)
