"""THE DAILY ROUTINE — edge, gap, land, prove. CRFN-first.

    ACRIS_CORPUS_ROOT=D:/acris python routine_4am.py
    ACRIS_CORPUS_ROOT=D:/acris python routine_4am.py --dry     report only

⚠ THIS REPLACED A TYPE x BOROUGH SWEEP, AND HERE IS WHY (measured 2026-08-18).
The sweep asked 97 doc types x 5 boroughs and cost 156 KB per ask whether or not
anything came back:
    264 sweeps run · 166 returned ZERO rows (62.9%) · 25.3 MB spent learning nothing
It exhausted a 40 MB budget at Brooklyn and never reached Queens or Staten Island.
The CRFN counter answers the same question in ~25 requests, because the edge is a
BOUNDARY, not a corpus: gallop, bisect, confirm. O(log n).

⚠ EXPECT A NON-ZERO DELTA. ACRIS records every business day (~1,550 documents
across both registries). A morning run finding 0 means nothing filed OR the probe
is broken — which is why crfn_monitor refuses to report at all if its control
does not resolve.

⚠ THE PROOF IS THE RE-PROBE, NOT THE ROW COUNT. Stage 5 asks ACRIS's own counter
whether anything is still outstanding. A count computed from our own output is
not evidence; every failure today looked like success by that measure.

⚠ CONCURRENCY IS THE TRIP RISK, NOT VOLUME. What tripped the server was 12,077
documents at CONC 16 in a burst. This runs sequential at 2.5s — 48 KB/s, one
connection. Mapping stays at CONC 8 with a seeded session.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
LOG = HERE / "_routine_4am.tsv"
PY = sys.executable

import corpus_paths as CP


def drive_absent_msg():
    """One honest sentence, printed wherever the One Touch's absence changes
    what a stage does — the path is named so 'absent' is checkable, not vibes."""
    return f"One Touch absent ({CP.SPEC_DB} not found)"


def run(label, args, log):
    """⚠ Output to a FILE, never a pipe — a piped long run block-buffers and its
    exit status becomes the pipe's, which is how a killed transaction once
    reported success."""
    t0 = time.time()
    out = HERE / f"_routine_{label}.log"
    with out.open("w", encoding="utf-8") as f:
        rc = subprocess.call([PY, "-u"] + args, stdout=f, stderr=subprocess.STDOUT,
                             cwd=str(HERE))
    el = time.time() - t0
    txt = out.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    print(f"  {label:<10} rc={rc} {el/60:.1f}m")
    for t in txt[-4:]:
        print(f"      {t}")
    log.append((label, rc, round(el)))
    return rc


def span():
    f = HERE / "_crfn_edge.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8")).get("span")


def acris(a, log):
    """⚠ EVERY `return` IN HERE IS ACRIS-SCOPED, NOT ROUTINE-SCOPED. When this was
    one flat main(), the normal case (span 0, already level) returned before
    anything after it could run - so a SECOND SOURCE appended to the bottom would
    have executed only on days ACRIS had a backlog, and its absence would have
    looked like "nothing to do" rather than "never ran". Sources are independent:
    one having nothing to fetch says nothing about the other."""
    print("")
    print("-- ACRIS --")

    # 1 · WHERE IS LIVE? ~25 requests, O(log n)
    if run("edge", ["crfn_monitor.py"], log) != 0:
        print("  ⚠ edge probe failed or its CONTROL did not resolve — stopping. "
              "A malformed probe looks exactly like an empty register.")
        return
    n = span()
    print(f"  outstanding span: {n if n is not None else 'unknown'}")
    if a.dry:
        return
    if not n:
        print("  span 0 — already level. Nothing to fetch.")
        return

    # 2 · FETCH THE GAP — all five index components per document, one request each
    # ⚠ live_gap.py, NOT live_crfn --walk. THE GAP IS NOT A RANGE: it is holes
    # BELOW our high-water mark plus a contiguous run above it. A forward walk
    # gets the second and silently misses the first — measured 2026-08-18,
    # 3,449 holes below vs 357 above. live_gap takes the explicit list, appends
    # per record (resumable), and STOPS rather than retries on a refusal.
    if run("walk", ["live_gap.py", "--run"], log) != 0:
        print("  ⚠ walk failed — nothing lands on a partial gap; the next run "
              "re-asks from the same watermark.")
        return

    # ⚠ THE DRIVE GATE SITS BETWEEN WALK AND LAND, DELIBERATELY. The walk's
    # queue is local + append-per-record, so fetching WITHOUT the drive loses
    # nothing — the delta simply lands on the next run that has it. Landing,
    # mapping and pushing without the drive would diverge the three legs.
    if not CP.drive_present():
        print(f"  ⚠ {drive_absent_msg()} — delta queued locally; "
              f"land/map/push DEFERRED to the next run with the drive.")
        log.append(("land", "SKIP", 0))
        return

    # 3 · LAND — drive decides what gets WALKED, so it goes first
    if run("land", ["live_land.py", "--apply"], log) != 0:
        print("  ⚠ landing failed — NOT pushing. The two would diverge and only "
              "the drive can be repaired by re-running.")
        return

    # 4 · MAP + PUSH — page ranges, then Supabase (it decides what gets FETCHED)
    q = HERE / "_live_delta_queue.jsonl"
    if q.exists():
        wl = HERE / "_routine_worklist.json"
        wl.write_text(json.dumps([{"document_id": json.loads(l)["doc_id"]}
                                  for l in q.open(encoding="utf-8")]))
        run("map", ["amap.py", str(wl)], log)
    run("push", ["push_live.py"], log)

    # 5 · THE PROOF — ask ACRIS's counter again, not our own rows
    run("reprobe", ["crfn_monitor.py"], log)
    final = span()
    print(f"\n  FINAL SPAN: {final}  ->  "
          f"{'LEVEL WITH LIVE' if final == 0 else 'STILL OUTSTANDING'}")

    # ⚠ ADVANCE THE BASELINE ONLY ON A PROVEN ZERO. Once span reads 0 there are
    # no holes below the edge, so tomorrow's gap starts from OUR ceiling instead
    # of Socrata's July ceiling — the daily shrinks from ~16,820 to ~1,550.
    # ⚠ NEVER advance on a non-zero span. The holes below would become
    # unreachable forever and nothing would ever look for them again.
    if final == 0:
        e = json.loads((HERE / "_crfn_edge.json").read_text(encoding="utf-8"))
        (HERE / "_socrata_ceiling.json").write_text(json.dumps({
            "ceiling": e["edge"],
            "measured_at": time.strftime("%Y-%m-%d"),
            "source": ("SPECIFICATION ceiling - advanced after a proven span 0. "
                       "Seeded from the Socrata ceiling 2026-08-18; from here it "
                       "tracks OUR ceiling, which runs ahead of the extract."),
        }, indent=1), encoding="utf-8")
        print(f"  baseline advanced -> {e['edge']} (tomorrow's gap starts here)")


def detail(a, log):
    """LAND WHATEVER THE DETAIL PULL HAS FETCHED SINCE THE LAST RUN.

    ⚠ WHY THIS STAGE EXISTS. `rc_detail_pull.py` writes ONLY jsonl — deliberately,
    so a multi-day campaign never holds the spec DB and can be killed at any
    moment. But nothing then moved that jsonl into the specification, so
    acquisition read a database that lagged the disk by however long the pull had
    been running. Measured 2026-08-19: 945,425 records on disk, 824,151 landed —
    **121,274 documents fetched and invisible to acquisition.** Nothing had
    failed; the propagation step simply had no owner.

    ⚠ IT IS SAFE BESIDE THE PULL AND ONLY BESIDE THE PULL. The pull is not a DB
    writer, so this does not contend with it. It MUST still not overlap rc_daily
    or a Supabase push — hence its own stage here, run sequentially, never
    concurrently.

    ⚠ IDEMPOTENT: it re-reads the whole jsonl and upserts, so running it when
    nothing new has been fetched is a cheap no-op, not a duplicate."""
    print("")
    print("-- RICHMOND DETAIL -> SPECIFICATION --")
    if not CP.drive_present():
        print(f"  SKIPPED — {drive_absent_msg()}. The jsonl and the spec DB both "
              f"live on the drive; nothing to propagate without it.")
        log.append(("rc_detail_land", "SKIP", 0))
        return
    if a.dry:
        print("  --dry: not landing (this stage has no report-only mode).")
        return
    run("rc_detail_land", ["rc_detail_land.py", "--apply"], log)


def images(a, log):
    """The ACRIS image probe — its own top-level stage, NOT a tail of acris().

    ⚠ acris() returns early on the NORMAL day (span 0, nothing filed since the
    last run) — anything appended inside it runs only on backlog days and its
    absence reads as "nothing to do" rather than "never ran". But yesterday's
    pending documents need their probe on quiet days most of all: that is
    exactly when the scan-attached-late flip happens. Same lesson as the
    acris/richmond split, applied again."""
    print("")
    print("-- IMAGE POLICY (ACRIS pending) --")
    if not CP.drive_present():
        print(f"  SKIPPED — {drive_absent_msg()}. Pending documents keep their "
              f"state and age normally; the next run with the drive probes them.")
        log.append(("images", "SKIP", 0))
        return
    if a.dry:
        run("images", ["live_imageprobe.py"], log)
        return
    run("images", ["live_imageprobe.py", "--apply"], log)


def richmond(a, log):
    """Staten Island. A DIFFERENT ACCESS MODEL, NOT A SECOND COPY OF ACRIS.

    ACRIS: dense CRFN counter -> the gap is a set of numbers we walk.
    RICHMOND: a date-range search returns every document recorded in a window in
    ONE request, so the delta costs one request and proves itself complete by
    instrument density (max-min+1 == count) rather than by a probe.

    ⚠ THE LAG RULES ARE NO LONGER RICHMOND-ONLY. image_policy.py is the single
    image policy for BOTH sources (pending -> probed each daily run <= 7d ->
    'imageless'); rc_daily consumes it through the detail page, the ACRIS side
    through live_land (lands 'pending') + live_imageprobe (the images stage)."""
    print("")
    print("-- RICHMOND (Staten Island) --")
    # ⚠ SKIPPED (drive absent) is a REPORTED outcome, not a crash and not
    # silence. rc_daily also self-checks (defense for direct runs); the check
    # here keeps the tsv honest — a SKIP line is distinguishable from both
    # success and failure forever after.
    if not CP.drive_present():
        print(f"  SKIPPED — {drive_absent_msg()}. Nothing fetched: the delta "
              f"jsonl lives on the drive, so without it every window row would "
              f"look NEW and be re-asked for nothing. Tomorrow's 3-day lookback "
              f"covers today.")
        log.append(("rc_daily", "SKIP", 0))
        return
    if a.dry:
        run("rc_daily", ["rc_daily.py"], log)
        return
    run("rc_daily", ["rc_daily.py", "--apply"], log)


def sync_table_stage(a, log):
    """EMIT THE DATED PASS-OFF TABLE - what sync actually owes the next phase.

    ⚠ THE ROUTINE RAN NIGHTLY AND NEVER PRODUCED THE ONE ARTIFACT THE
    SPEC REQUIRES. Landing documents into the specification is not the end of
    sync. The phase ends when it hands the NEXT phase a dated statement of what
    each custodian holds, what we hold, and which ids moved. Without that file
    Navigation is guessing at its own input, and a quiet night leaves nothing
    to audit afterwards - "nothing was filed" and "the walk never ran" look
    exactly alike in an empty folder.

    ⚠ AFTER BOTH ID PRODUCERS, NEVER BETWEEN THEM. The gate is
    `live state - new total == 0` across BOTH custodians. A table written
    before Richmond runs states a balance for half a corpus and calls it the
    gate - wrong in the one direction nobody checks, because a zero balance is
    precisely what a healthy run looks like.

    THE EXIT CODE IS THE GATE. sync_table.py returns 0 only when the id balance
    is 0 AND both deltas are known; anything else holds Navigation."""
    print("")
    print("-- SYNC TABLE (the pass-off to Navigation) --")
    if not CP.drive_present():
        print(f"  SKIPPED - {drive_absent_msg()}. The table states what the "
              f"specification holds; with no drive there is nothing to state.")
        log.append(("table", "SKIP", 0))
        return None
    if a.dry:
        return run("table", ["sync_table.py", "--no-probe"], log)
    return run("table", ["sync_table.py"], log)


def navigation(a, log, gate=None):
    """REBUILD THE NAVIGATION TABLE — the sync's whole point is that acquisition
    sees what landed overnight.

    ⚠ WITHOUT THIS STAGE THE ROUTINE IS A NO-OP FOR THE NEXT PHASE. Edge/walk/land
    put new documents into the specification, and nothing downstream reads the
    specification — acquisition reads `legal_instrument_navigation.csv`. A sync
    that lands 1,550 documents and does not rebuild the table has changed nothing
    anyone can act on by the start of the work day.

    ⚠ FULL REBUILD, NOT AN APPEND. Measured 2026-08-19: 24,037,915 rows in 23.7
    min by streaming merge join. An append would have to know which ids changed,
    and image_state changes on documents that are not new — a pending image
    flipping to present is an UPDATE to an old row, not a new one. Rebuilding is
    cheaper than being wrong about that.

    ⚠ THE GATE IS UNKEYED == 0. nav_build prints it; a non-zero value means
    documents landed that key to neither parcel, party, nor themselves, and
    acquisition must not run against that table."""
    print("")
    print("-- NAVIGATION (rebuild the acquisition table) --")
    # ⚠ A PHASE MAY NOT START UNTIL THE PREVIOUS ONE CLOSED. Sync produces
    # ids; Navigation maps those ids to key, index and endpoint. Building from
    # a specification that is still short does NOT fail loudly - nav_build own
    # UNKEYED gate reads 0 either way, because every row it did write is
    # properly keyed. The gate passes over a wrong denominator and the absent
    # documents stay invisible until acquisition simply never fetches them.
    if gate not in (None, 0) and not a.authorize_nav:
        print(f"  HELD - sync did not close (table stage rc={gate}).")
        print("    The id balance is not 0, so the specification Navigation")
        print("    would map is known to be incomplete. Re-run sync, or pass")
        print("    --authorize-nav to build against it deliberately.")
        log.append(("navigation", "HELD", 0))
        return
    if not CP.drive_present():
        print(f"  SKIPPED — {drive_absent_msg()}.")
        log.append(("navigation", "SKIP", 0))
        return
    if a.dry:
        print("  dry run — would rebuild %s" % CP.NAV_TABLE.name)
        log.append(("navigation", "SKIP", 0))
        return
    run("navigation", ["nav_build.py"], log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", choices=["acris", "richmond", "images",
                                       "table", "navigation"])
    ap.add_argument("--authorize-nav", action="store_true",
                    help="build navigation even though the sync id balance is "
                         "not 0 (the phase gate is deliberately overridden)")
    a = ap.parse_args()
    print(f"DAILY ROUTINE — {time.strftime('%Y-%m-%d %H:%M')}")
    log = []
    # ⚠ THE ORDER IS THE PASS-OFF, NOT A PREFERENCE.
    #   acris + richmond  produce ids          <- BOTH must finish first
    #   images            updates image_state  <- nav writes it into the index
    #   table             states the balance   <- sync deliverable AND its gate
    #   navigation        maps the ids         <- only if that gate closed
    #
    # MEASURED 2026-08-20: images ran BETWEEN acris and richmond and spent 55.9
    # min there, holding the second id producer back by nearly an hour for a
    # probe that belongs to Navigation ledger rather than to sync arithmetic.
    # Nothing in the id count needs the probe, and the balance needs BOTH
    # custodians - so the two id producers now run back to back.
    if a.only in (None, "acris"):
        acris(a, log)
    if a.only in (None, "richmond"):
        richmond(a, log)
    if a.only in (None, "images"):
        images(a, log)
    gate = None
    if a.only in (None, "table"):
        gate = sync_table_stage(a, log)
    # ⚠ LAST, ALWAYS. Navigation must see everything the earlier stages
    # landed - ACRIS documents, Richmond documents, and image-state flips alike.
    # --only navigation leaves gate None: naming one stage IS the authorization.
    if a.only in (None, "navigation"):
        navigation(a, log, gate)
    _finish(log)


def _finish(log):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M") + "\t"
                + "\t".join(f"{n}:{rc}:{s}s" for n, rc, s in log) + "\n")
    # SKIP (drive absent, deferral) is a clean reported outcome, never a failure
    # ⚠ HELD IS NOT FAILED. A stage that correctly refused to start
    # because its predecessor did not close is the gate WORKING. Reporting that
    # as a failure teaches the reader to ignore the failure line.
    bad = [n for n, rc, _ in log if rc not in (0, "SKIP", "HELD")]
    skipped = [n for n, rc, _ in log if rc == "SKIP"]
    held = [n for n, rc, _ in log if rc == "HELD"]
    msg = "ALL STAGES OK" if not bad else "⚠ FAILED: " + ",".join(bad)
    if held:
        msg += "  (HELD by phase gate: " + ",".join(held) + ")"
    if skipped:
        msg += f"  (SKIPPED: {','.join(skipped)})"
    print(f"  {msg}")


if __name__ == "__main__":
    main()
