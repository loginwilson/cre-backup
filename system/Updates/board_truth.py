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

    pdf = ''            undecided           (todo)
    pdf = 'pending'     no image yet, in lag (todo - stays in the queue)
    pdf = 'absent'      no image, lag expired (DONE - a determination)
    pdf = <a path>      fetched              (done)
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

    ix_nav_pdf_todo  ON navigation(id) WHERE pdf IN ('','pending')
                                                   partial - the todo set
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
import subprocess
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
# >> the acris todo count is expensive; see the note at its call site
ACRIS_EVERY = 300.0
_LAST_ACRIS = [0.0]
LOG = HERE / "board_truth.log"

# ⚠ The prefix is the source split. 'RC_' sorts above every all-digit ACRIS id
# ('R' > '9'), so the two sources are CONTIGUOUS RANGES in the id index - which
# is exactly why these counts are cheap. 'RC`' is the next string after 'RC_'
# ('`' = 0x60 follows '_' = 0x5F), giving a half-open range with no LIKE.
RC_LO, RC_HI = "RC_", "RC`"


def _acris_live():
    """⚠ IS ACRIS ACTUALLY PRODUCING? If it is not, its todo CANNOT have moved,
    and rescanning 21,617,307 index entries is pure waste - waste that BLOCKS
    THE WRITE FOR THE SOURCE THAT IS MOVING.

    Measured 2026-08-25 20:42-20:52: this pass counted rc_todo in 22 s, then
    sat on acris_todo for 10+ minutes at 0.34 s CPU per 10 s - BLOCKED, not
    scanning, because rc_lane was writing ~33 MB/s of pdfs to the same USB
    drive. The whole json write is gated behind that count (one write at the
    end of measure()), so richmond's live number could never reach the board
    while richmond was busy earning it.

    ⚠ ON DOUBT, COUNT. Any failure here returns True and the real scan runs.
    A skipped count must never be the DEFAULT - only a deliberate, observed one.
    """
    try:
        txt = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
             " | Select-Object CommandLine | ConvertTo-Csv -NoTypeInformation"],
            capture_output=True, text=True, timeout=60).stdout
        # >> THE OLD ACQUISITION LANES COUNT AS ACRIS BEING LIVE
        # (2026-08-26). login restarted acris as rd_walk + image_walk rather
        # than the consolidated acris_lane, so this test - which only knew the
        # ONE script name - reported acris dead while it was landing ~27
        # docs/s, and the board served a CACHED todo forever. login saw it
        # immediately: "not seeing the chnage in the update on acris".
        #
        # ⚠ MATCH ON THE PATH SEPARATOR, NOT THE BARE NAME. "rd_walk.py"
        # is a SUBSTRING of "rc_rd_walk.py" - richmond's own walker - so a bare
        # `in` test would let a richmond process assert that acris is live.
        # acris_reproduction.py added 2026-08-28: the group-entry lane
        # (login's batched design) IS the acris process now when it runs.
        return any(("\\" + n) in txt
                   for n in ("acris_lane.py", "rd_walk.py", "image_walk.py",
                             "acris_reproduction.py"))
    except Exception:
        return True


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
                "SELECT system_total + delta, run_at, delta FROM"
                " synchronization WHERE source=? AND system_total > 0"
                " ORDER BY rowid DESC LIMIT 1", (src,)).fetchone()
            if r:
                out[src], when = r[0] or 0, r[1]
                # >> delta kept SEPARATELY so a live system_total can be
                # substituted without losing the source-vs-us gap. MEASURED 0
                # for both sources 2026-08-26 (nav is LEVEL).
                out[src + "_delta"] = r[2] or 0
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
    # ⚠⚠ 'pending' IS TODO; 'absent' IS DONE (login 2026-08-25: "the pdf
    # cell just has the path for the fetch. if no pdf itll either be absent
    # or pending. and pedning remains in que until 7 dyas passes").
    #
    # The pdf cell now carries FOUR kinds of value and only two of them are
    # outstanding work:
    #     <a path>   fetched            DONE
    #     'absent'   the url is a dead end past the 7-day lag - a real
    #                DETERMINATION about the document          DONE
    #     'pending'  no image yet, still inside the lag        TODO
    #     ''         not yet decided                           TODO
    #
    # ⚠ WITHOUT 'absent' COUNTING AS DONE, 100% IS UNREACHABLE - login:
    # "If you arent counting no pdf determiniation into the count thats a
    # huge failure that would never result in 100% compeltion". And without
    # 'pending' counting as TODO, a row would leave the worklist AND be
    # counted landed the moment it was marked - completion would jump by
    # exactly the number of documents that are NOT done.
    # ⚠ ix_nav_pdf_todo is rebuilt on the SAME predicate; if these two ever
    # disagree the count silently uses the wrong set.
    # >> TODO IS NOW *UNASSIGNED*, NOT *UNFETCHED* (login 2026-08-26: "100%
    # to me means that 100% assigned so pending and absent count"). The pdf
    # cell answers a different question than it used to:
    #
    #     <path>      fetched                     ASSIGNED · done
    #     'absent'    determined, no image        ASSIGNED · done
    #     'pending'   no image yet, still in lag  ASSIGNED · still queued
    #     ''          never checked               NOT ASSIGNED  <- the todo
    #
    # 'pending' is a real determination about a document, so it counts toward
    # completion; it just also stays in rc_lane's worklist (the miner selects
    # pdf IN ('','pending')) so the image is collected the moment it attaches.
    #
    # ⚠ STILL INDEX-ONLY. A bare `pdf=''` CANNOT use ix_nav_pdf_todo - SQLite
    # will not prove `=''` implies the IN list, so it degrades to a 2.5M-row
    # PK scan (measured 69 s). Instead read the INDEXED todo set - a few
    # hundred rows - and split it in python. Cost is O(queued), not O(table).
    t0 = time.time()
    rc_rows = q("SELECT pdf FROM navigation WHERE pdf IN ('','pending')"
                " AND id>=? AND id<?", (RC_LO, RC_HI)).fetchall()
    rc_queued = len(rc_rows)
    rc_todo = sum(1 for (p,) in rc_rows if p == "")
    rc_pending = rc_queued - rc_todo
    t4 = time.time() - t0
    say("    rc_todo    %13s  %.0fs   (unassigned; %s pending awaiting an"
        " image, counted ASSIGNED)"
        % (f"{rc_todo:,}", t4, f"{rc_pending:,}"))
    # ⚠ SKIP THE PAUSED SOURCE - see _acris_live(). The cached value is
    # LABELLED in the output; a stale count published as fresh is worse than
    # no count at all.
    # ⚠ LIVE IS NOT THE SAME AS DUE. The acris todo count reads ~19.6M
    # index entries: MEASURED 2026-08-26 at 43.79 s cold / 1.42 s warm, and
    # this function's own history records it BLOCKING for 10+ minutes when
    # rc_lane was writing ~33 MB/s to the same USB drive. There are now THREE
    # writers on that drive (rc_lane + rd_walk + image_walk), and the json
    # write is gated behind this count - so running it every 60 s would let
    # acris's denominator freeze RICHMOND's live number, which is the exact
    # failure _acris_live() was written to prevent.
    #
    # So: richmond keeps the 60 s tick (0.17 s, it can afford it) and acris is
    # counted at most every ACRIS_EVERY seconds, serving the labelled cache in
    # between. Fresh enough for a backfill that moves in hours, cheap enough
    # not to block the source that moves in seconds.
    a_todo, t3, a_cached = None, 0.0, False
    _due = (time.time() - _LAST_ACRIS[0]) >= ACRIS_EVERY
    if not _acris_live() or not _due:
        try:
            _p = json.loads(OUT.read_text(encoding="utf-8"))
            a_todo = _p.get("sources", {}).get("acris", {}).get("todo")
        except Exception:
            a_todo = None
        a_cached = a_todo is not None
    if a_cached:
        say("    acris_todo    %13s  CACHED - %s"
            % (f"{a_todo:,}",
               "acris is not running, so this cannot have moved"
               if not _acris_live() else
               "next live count in %.0fs (the %ds acris tick)"
               % (ACRIS_EVERY - (time.time() - _LAST_ACRIS[0]), ACRIS_EVERY)))
    else:
        a_todo, t3 = one("acris_todo", "SELECT count(*) FROM navigation "
                         "WHERE pdf IN ('','pending') AND id<?", RC_LO)
        _LAST_ACRIS[0] = time.time()
    # ⚠ TIMESTAMP THE COUNTS, NOT THE WRITE. The rate was differenced against
    # the previous anchor's `at`, which is when the file was WRITTEN - and the
    # nullprobe runs BETWEEN the counting and the write (121-217 s of it). So
    # the span was understated by exactly that gap and the rate came out
    # inflated by the same factor:
    #
    #     published  21.50/s   span 174 s   <- write-to-count
    #     true        9.56/s   span 393 s   <- count-to-count
    #     ratio 2.25 = the nullprobe sitting inside the interval
    #
    # Caught only because the column had been measured directly and
    # independently (9.56/s over 448 s) an hour earlier. **A derived number
    # needs an independent measurement, not a plausible one.**
    counted_at = time.strftime("%Y-%m-%dT%H:%M:%S")
    totals, when = ledger_totals()
    rc_total, total = totals.get("richmond", 0), None
    a_total = totals.get("acris", 0)

    # >> RICHMOND'S TOTAL IS COUNTED LIVE NOW, NOT READ FROM THE LEDGER
    # (login 2026-08-26: "the numbers shouldnt wait until the night, it should
    # update live?"). They were right, and THE CALIBRATION THAT FORBADE IT HAD
    # EXPIRED.
    #
    # The rule above says READ the total because the PK's RC_ range measured
    # 168 s cold on 2026-08-23 - and it says why: "the PK's RC_ range is
    # touched by nobody". That has not been true since rc_lane became one
    # process: rd_heal does O(window) PK lookups every 15 min, _no_image() one
    # per dead-end mint, and pending_recheck() re-reads the todo set every
    # 300 s. The range is HOT now. RE-MEASURED 2026-08-26, twice, warm:
    #
    #     richmond   2,501,924 rows    0.17 s   0.18 s
    #     acris     21,617,307 rows   43.79 s    1.42 s   <- still expensive cold
    #     whole table                185.58 s              <- never
    #
    # A calibration is a value PLUS the conditions it was taken under. The
    # conditions changed, so the value had to be re-taken - not inherited.
    #
    # ⚠ ACRIS STAYS ON THE LEDGER. 43.79 s cold is exactly the cost the
    # original rule was protecting against, and acris is PAUSED - its row count
    # cannot move, so a live count would spend 44 s to reproduce a constant.
    # Same reasoning as _acris_live() already applies to the todo count.
    #
    # ⚠ THE DENOMINATOR IS STILL THE SOURCE'S COUNT. `delta` is
    # source_total - system_total; MEASURED 0 for both sources (nav is LEVEL,
    # checked by routine_navigation.py), so total == our row count today. It is
    # added back anyway so this stays correct the day nav is NOT level rather
    # than quietly reporting our own backlog as the world.
    #
    # ⚠ AND IT SAYS WHICH NUMBER IT USED. A live count that silently falls
    # back to a 3-hour-old ledger reading is worse than one that never moved,
    # because nothing on the board would look different.
    # ⚠⚠ A FALLBACK VALUE MUST NEVER BE DIFFERENCED AGAINST A LIVE ONE, AND
    # THE LEDGER IS THE WRONG THING TO FALL BACK TO. Measured 2026-08-29
    # 12:54: the acris register lane at ~32 docs/s saturated the drive, so
    # richmond's live count - normally 0.14-0.20 s - took 112 s and blew the
    # 30 s budget. This branch then published the 2026-08-27 LEDGER figure
    # (2,502,033) one pass after a LIVE 2,502,230, and routine_update
    # differenced them: the board printed richmond synchronization at
    # **-197 rows, rate -1.484/s**. login caught it: "that shouldnt make
    # negative". A sync count cannot go down - doc ids are not un-filed -
    # so any negative here is a MEASUREMENT artifact by construction.
    #
    # Two distinct bugs, both fixed by holding instead of reverting:
    #   1 the fallback jumped BACKWARDS IN TIME (2 days), inventing a loss
    #   2 two different measurement METHODS were subtracted from each other.
    #     Same column, different sources, is still a method change - the
    #     "same subtraction" law applies to the SOURCE, not just the column.
    # So: hold the last LIVE value. It is stale-but-true (the count only
    # ever grows, so a held value understates at worst and can never invent
    # a loss) and it produces a delta of exactly 0 while the read is starved
    # - which is the honest answer, because we did not measure anything.
    _held = None
    try:
        _h = ((json.loads(OUT.read_text(encoding="utf-8"))
               .get("sources", {}).get("richmond", {}) or {}).get("total"))
        if isinstance(_h, int) and _h > 0:
            _held = _h
    except Exception:
        pass                      # no prior pass - the ledger is all we have

    def _fallback(why):
        """Never returns a number older than the last thing we measured."""
        if _held:
            return _held, ("HELD %s  ⚠ %s - holding the LAST LIVE value, not"
                           " the ledger; delta suppressed to 0"
                           % (f"{_held:,}", why))
        return rc_total, ("ledger %s  ⚠ %s - and no prior live value to hold,"
                          " so this number is stale" % (when, why))

    rc_src = "ledger %s" % when
    try:
        _t = time.time()
        _v = q("SELECT count(*) FROM navigation WHERE id>=? AND id<?",
               (RC_LO, RC_HI)).fetchone()[0]
        _el = time.time() - _t
        if _v and _el < 30:
            rc_total = _v + (totals.get("richmond_delta") or 0)
            rc_src = "LIVE %.2fs" % _el
        else:
            rc_total, rc_src = _fallback(
                "live count took %.0fs (>30s budget)" % _el)
    except Exception as _e:
        rc_total, rc_src = _fallback(
            "live count failed (%s)" % type(_e).__name__)
    say("    totals  acris %s (ledger %s) · richmond %s (%s)"
        % (f"{a_total:,}", when, f"{rc_total:,}", rc_src))
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
        "richmond_pending": rc_pending,
        "null_probe": nulls,
        "acris_cached": a_cached,
        "ledger_run": when,
        "richmond_total_from": rc_src,
        "counted_at": counted_at,
    }


def measure():
    # the previous anchor, so this pass can publish a table-derived rate
    prev = None
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            prev = None

    con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=600)
    try:
        c = counts(con)
    finally:
        con.close()

    out = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "source": ("todo counted from pdf column; richmond total COUNTED LIVE, acris total from sync ledger (paused)"),
           "depends_on": "navigation LEVEL (rows == ledger)",
           "ledger_run": c.get("ledger_run"),
           "counted_at": c.get("counted_at"),
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
        if src == "acris" and c.get("acris_cached"):
            out["sources"][src]["counted"] = ("CACHED - acris paused, index "
                                              "not rescanned this pass")
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
            # count-to-count, so the nullprobe cannot sit inside the span
            span = 0.0
            if prev.get("counted_at"):
                import datetime as _dt
                span = (_dt.datetime.fromisoformat(c["counted_at"])
                        - _dt.datetime.fromisoformat(prev["counted_at"])
                        ).total_seconds()
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
