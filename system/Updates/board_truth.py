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


SYNC_DB = (r"D:\CRE Decoding System\00 Synchronizations"
           r"\Legal Instruments Synchronization"
           r"\Legal Instruments Synchronization.db")


def ledger_totals():
    """The SOURCE's count per source, as sync last published it.

    ⚠ `system_total + delta` is the source's number, not ours - that is the
    whole point of the sync ledger, and it is the only figure in this file
    that comes from OUTSIDE our own database. A denominator taken from our own
    table can only ever tell us we are consistent with ourselves."""
    con = sqlite3.connect("file:%s?mode=ro" % SYNC_DB, uri=True, timeout=120)
    try:
        # ⚠ THE LEDGER HOLDS TWO KINDS OF ROW AND THEY LOOK ALIKE.
        # routine_synchronization writes a TOTAL row (system_total = our full
        # count, delta = what the source has beyond it). sync_fast / rc_sync_fast
        # write a DELTA row: system_total 0, source_total 0, delta = how many ids
        # it just landed. Both are "the latest row for this source".
        #
        # Reading the latest row blindly took `system_total + delta` from a
        # DELTA row and got **5** for acris - so `landed = total - todo` came out
        # at **-20,721,031** and the board printed -414420620%. Measured live at
        # 01:20:39, minutes after the gate test wrote exactly such a row.
        #
        # ⚠ A NEGATIVE LANDED IS NOT A NUMBER TO CLAMP. It is the shape of a
        # wrong denominator, and clamping it to 0 would have hidden the bug
        # while still reporting a false level. Never repair a number to make a
        # check pass - fix the source of the number.
        #
        # Only a row that actually carries a total qualifies.
        out, when = {}, "-"
        for src in ("acris", "richmond"):
            r = con.execute(
                "SELECT system_total + delta, run_at FROM synchronization"
                " WHERE source=? AND system_total > 0"
                " ORDER BY rowid DESC LIMIT 1", (src,)).fetchone()
            if r:
                out[src], when = r[0] or 0, r[1]
        return out, when
    finally:
        con.close()


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

    # ⚠ COUNT THE TODO SET, READ THE TOTAL. Measured 2026-08-23, and the
    # asymmetry is 50x on the same machine in the same minute:
    #
    #     ix_nav_pdf_todo   23,097,031 entries    30 s   ~770,000/s   HOT
    #     PK autoindex       2,501,589 entries   168 s    ~15,000/s   COLD
    #
    # The walkers query `pdf=''` constantly so that index is always warm; the
    # PK's RC_ range is touched by nobody. Worse, a full `count(*)` picks
    # ix_nav_key - the index `nav_key.py` is actively WRITING - and a long read
    # against a hot index in WAL mode degrades as it accumulates frames. That
    # scan ran 28 minutes and was still going.
    #
    # So: TODO is counted (cheap, hot, and it is the number that actually moves
    # minute to minute). TOTAL is READ FROM THE SYNC LEDGER, which is where
    # `routine_synchronization` already publishes it after its own full pass.
    #
    # ⚠ THIS BORROWS SYNC'S ASSERTION AND MUST SAY SO. The ledger total is the
    # SOURCE's count, and `landed = total - todo` is only true if our table
    # holds a row per source document. That is navigation's claim, checked by
    # `routine_navigation.py` (rows == ledger, "LEVEL"). If nav is NOT level
    # these numbers are wrong - so the anchor records which sync run it leaned
    # on rather than presenting itself as self-evident. Composing assertions is
    # fine; hiding that you composed them is not.
    rc_todo, t4 = one("rc_todo", "SELECT count(*) FROM navigation "
                      "WHERE pdf='' AND id>=? AND id<?", RC_LO, RC_HI)
    a_todo, t3 = one("acris_todo", "SELECT count(*) FROM navigation "
                     "WHERE pdf='' AND id<?", RC_LO)
    totals, when = ledger_totals()
    rc_total, total = totals.get("richmond", 0), None
    a_total = totals.get("acris", 0)
    say("    ledger totals  acris %s · richmond %s   (sync run %s)"
        % (f"{a_total:,}", f"{rc_total:,}", when))
    total, todo, t1, t2 = a_total + rc_total, a_todo + rc_todo, 0.0, 0.0
    # ⚠ NULL is the assumption-breaker. It is NOT in the todo index and NOT a
    # path, so `total - todo` would silently count it as landed. Counted here
    # so it can never hide. This one does touch the table - but only for rows
    # that should not exist, and it is bounded by being reported, not summed.
    # ⚠ PROBE THE TAIL, NOT THE HEAD. The first version read `rowid<=200000` -
    # the OLDEST rows, minted years ago and long since landed. It could only
    # ever return 0, which is a check that cannot fail and therefore proves
    # nothing (CLAUDE.md rule 4: "a counter sitting at zero is a claim to
    # verify, not a result"). A NULL `pdf` means a row was inserted without
    # being minted, so it would appear where sync INSERTS - at the tail.
    #
    # ⚠ AND KEEP IT SMALL. At 200,000 rows this ONE check was 217 s of a 220 s
    # pass - it is the only query here that touches the table rather than an
    # index. New rows arrive only from sync (~1,550/business day), so 50,000
    # rows of tail already covers WEEKS of inserts. A safety check that
    # dominates the run it protects will be the first thing someone deletes.
    mx = q("SELECT max(rowid) FROM navigation").fetchone()[0] or 0
    nulls, t5 = one("nullprobe", "SELECT count(*) FROM navigation "
                    "WHERE pdf IS NULL AND rowid>?", mx - 50000)
    say("  counted in %.0fs total" % (t1 + t2 + t3 + t4 + t5))
    return {
        "acris": (a_total, a_todo),
        "richmond": (rc_total, rc_todo),
        "null_probe": nulls,
        "ledger_run": when,
    }


def measure():
    # the previous anchor, so this pass can publish a table-derived rate
    prev, age_s = None, 0.0
    if OUT.exists():
        try:
            import datetime as _dt
            prev = json.loads(OUT.read_text(encoding="utf-8"))
            age_s = (_dt.datetime.now()
                     - _dt.datetime.fromisoformat(prev["at"])).total_seconds()
        except Exception:
            prev = None

    con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=600)
    try:
        c = counts(con)
    finally:
        con.close()

    out = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "source": "todo counted from pdf column; total from sync ledger",
           "depends_on": "navigation LEVEL (rows == ledger)",
           "ledger_run": c.get("ledger_run"),
           "null_probe_first_200k": c["null_probe"], "sources": {}}
    # ⚠ AN IMPOSSIBLE NUMBER MUST REFUSE TO PUBLISH. There was no sanity gate
    # here, so a bad denominator sailed straight through to a written anchor:
    # `acris total 5 · LANDED -20,721,031 (-414420620.00%)`. routine_update
    # only checks the anchor's AGE and its `warning` key - it would have put a
    # negative landed on the board.
    #
    # `0 <= landed <= total` is not a formatting nicety, it is the only thing
    # standing between a wrong denominator and a published figure.
    for src in ("acris", "richmond"):
        total, todo = c[src]
        landed = total - todo
        if total <= 0 or landed < 0 or landed > total:
            say("⚠ %-9s REFUSING TO PUBLISH: total %s · todo %s · landed %s "
                "is impossible. The denominator is wrong (a ledger DELTA row "
                "read as a TOTAL row does this). Reporting nothing for this "
                "source rather than a number."
                % (src, f"{total:,}", f"{todo:,}", f"{landed:,}"))
            out["warning"] = "impossible landed for %s; anchor not usable" % src
            continue
        out["sources"][src] = {"total": total, "todo": todo, "landed": landed}
        # ⚠ THE ANCHOR SHOULD PUBLISH ITS OWN RATE, because it is the only
        # rate here derived from the TABLE rather than from a lane's printer.
        #
        # The board was using each lane's `total_docs / total_minutes` - a
        # LIFETIME average, which this system already learned to distrust:
        # "19 hours of history including every dip printed 89.9/s while the
        # fleet measurably ran 122.7/s." A direct column measurement over 448 s
        # gave acris 9.56/s against the lifetime figure's 11.06/s.
        #
        # Differencing two anchors is legitimate here precisely because the SPAN
        # is the anchor interval (~30 min), not a 60-second tick sampling a
        # 30-minute step. Aliasing comes from a window shorter than the update
        # it observes; this window IS the update.
        if prev:
            p = (prev.get("sources") or {}).get(src)
            span = age_s
            if p and span and span > 60 and p.get("landed") is not None:
                d = landed - p["landed"]
                if d >= 0:                 # a lane restart can never un-land
                    out["sources"][src]["rate"] = round(d / span, 2)
                    out["sources"][src]["rate_span_s"] = round(span)
                    say("          measured %+d docs over %.0fs -> %.2f/s "
                        "(from the column, not a lane printer)"
                        % (d, span, d / span))
        say("%-9s total %13s · todo %13s · LANDED %13s  (%.2f%%)"
            % (src, f"{total:,}", f"{todo:,}", f"{landed:,}",
               100.0 * landed / total))
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
