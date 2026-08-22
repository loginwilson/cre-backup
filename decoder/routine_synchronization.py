"""THE SYNCHRONIZATION ROUTINE — rebuilt from scratch (login 2026-08-21).

Six steps, no more:

    1. source document id total in the SYSTEM database
    2. source document id total AT THE SOURCE
    3. delta = step 2 - step 1
    4. gather the delta's DOC IDS and land them in the
       Legal Instruments Synchronization database (live, along the walk)
    5. once complete, SEND THE DOC IDS TO THE LEGAL INSTRUMENTS DB
       (nav_append mints rd_url + pdf_url; every other cell stays empty
       because an empty cell IS the downstream work list)
    6. CONFIRM DELTA = 0 - and if it is not, KICK OFF AGAIN (login
       2026-08-21: "step 6 doesnt have to run the entire thing. it just
       has to confirm delta = 0. if it doesnt, then it kicks off again").
       The check is ONE cheap re-ask of the source's counter/window - never
       a count of our own rows - and a nonzero answer re-enters the cycle
       at step 4 for the residual. Bounded at 3 rounds: during business
       hours the source records live, and chasing a moving edge forever is
       not levelness, it is a tail-chase; the bound makes the last measured
       residual an honest number in the ledger.

    python routine_synchronization.py                 both sources
    python routine_synchronization.py --source acris
    python routine_synchronization.py --source richmond
    python routine_synchronization.py --dry           steps 1-3 only

Configured for LEGAL INSTRUMENTS = two sources, and the steps are concrete
per source (login's spec, verbatim):

    ACRIS      1 Legal Instruments db answers step 1
               2 the CRFN EDGE answers step 2 (gallop+bisect, ~33 requests)
               3 delta = 2 - 1
               4 the CRFN DIRECTS YOU TO THE DOC ID - live_gap fetches each
                 outstanding crfn and the detail page names its doc id

    RICHMOND   1 Legal Instruments db answers step 1
               2 a DATE RANGE window forms the total (no counter exists;
                 level is induction: every window since the backfill zeroed)
               3 delta = 2 - 1
               4 doc ids COME FROM STEP 2 - the window rows carry them

⚠ THIS ROUTINE'S ONLY PRODUCT IS THE SYNC TABLE. It does not land the
specification, probe images, or rebuild csvs - those belong to later phases
(nav mints urls from these ids; acquisition pulls them). One routine, one
claim: the table says what exists, what we hold, and what is new.

⚠ REUSED MACHINERY, NOT REWRITTEN: crfn_monitor.py (edge; control-proven,
stops if its control cannot resolve), live_gap.py (crfn->doc_id; appends per
record, resumable, STOPS on a refusal), rc_sync/rc_imagelag (the window).
Scraping logic lives in exactly one place each.

⚠ THE ZERO-WINDOW RULE (richmond): zero rows is also the over-cap shape, so
a zero multi-day window is believed only after a 1-day window also returns
zero. Same-day recordings lag the county's index - tomorrow's window
catches them; that is why the lookback overlaps.
"""
from __future__ import annotations

import argparse
import datetime as dt
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

SYNC_DB = (pathlib.Path(r"D:\CRE Decoding System\00 Synchronizations")
           / "Legal Instruments Synchronization"
           / "Legal Instruments Synchronization.db")
QUEUE = HERE / "_live_delta_queue.jsonl"   # live_gap appends {crfn, doc_id}
EDGE = HERE / "_crfn_edge.json"            # crfn_monitor writes edge + span
PY = sys.executable

ap = argparse.ArgumentParser()
ap.add_argument("--source", choices=["both", "acris", "richmond"],
                default="both")
ap.add_argument("--dry", action="store_true", help="steps 1-3 only")
ap.add_argument("--lookback", type=int, default=3,
                help="richmond window days (overlap is the lag insurance)")
a = ap.parse_args()


# ── STEP 1 · the system database ─────────────────────────────────────────
def step1_system_totals():
    """one pass over the Legal Instruments Navigation db - a row per id,
    so counting rows IS the measure. Full scan: daily, never per-tick."""
    r = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=900)
    acris, rc = r.execute(
        "SELECT SUM(CASE WHEN id < 'RC_' THEN 1 ELSE 0 END),"
        "       SUM(CASE WHEN id > 'RC_' THEN 1 ELSE 0 END)"
        " FROM navigation").fetchone()
    r.close()
    return {"acris": acris or 0, "richmond": rc or 0}


# ── ACRIS steps 2-4 ──────────────────────────────────────────────────────
def acris_step2_edge():
    """the CRFN edge: gallop + bisect + confirmed blanks, control-proven.
    crfn_monitor stops ITSELF if its control does not resolve (a malformed
    probe looks exactly like an empty register) - honor its exit code."""
    rc = subprocess.run([PY, "-u", str(HERE / "crfn_monitor.py")],
                        cwd=str(HERE)).returncode
    if rc != 0 or not EDGE.exists():
        return None
    return json.loads(EDGE.read_text(encoding="utf-8"))


def _queue_ids(offset):
    ids = []
    if QUEUE.exists():
        with QUEUE.open("rb") as f:
            f.seek(offset)
            for line in f.read().decode("utf-8", "replace").splitlines():
                try:
                    d = json.loads(line).get("doc_id")
                except ValueError:
                    continue
                if d:
                    ids.append(d)
    return list(dict.fromkeys(ids))


def acris_step4_ids(dry, sys_total, src_total, span):
    """the crfn DIRECTS YOU to the doc id: live_gap fetches each outstanding
    crfn (holes below the watermark AND the run above it - the gap is not a
    range) and each detail page names its document id.

    ⚠ LANDS LIVE, every 60s, WHILE the walk runs (login 2026-08-21: "its no
    live feeding the db so the update can catch it"). The walk appends per
    record to its queue; folding the queue into the sync table's doc_ids
    cell as it grows makes THE DATABASE the live surface - the update board
    and DB Browser watch the phase's own table, never a side file. A partial
    cell is honest: it says exactly how far the gather has come."""
    offset = QUEUE.stat().st_size if QUEUE.exists() else 0
    if dry:
        return None
    proc = subprocess.Popen([PY, "-u", str(HERE / "live_gap.py"), "--run"],
                            cwd=str(HERE))
    ids = []
    while True:
        done = proc.poll() is not None
        got = _queue_ids(offset)
        if len(got) > len(ids):
            ids = got
            land([("acris", sys_total, src_total, span, ";".join(ids))],
                 quiet=True)
            print(f"  landed {len(ids):,} / {span:,} ids into the sync db",
                  flush=True)
        if done:
            break
        time.sleep(60)
    if proc.returncode != 0:
        print(f"  ⚠ walk stopped early (rc={proc.returncode}) - the"
              f" {len(ids):,} ids it DID resolve are landed; the next run"
              f" re-asks from the same watermark, so nothing is lost.")
    return ids


# ── RICHMOND steps 2-4 ───────────────────────────────────────────────────
def richmond_step24(lookback, system_held):
    """one date-range window forms the total AND carries the doc ids
    (rc_window, the new-site GET flow).

    ⚠ CONTROL FIRST. The 2026-08-21 failure: the county redesigned their
    markup, every window read zero - and the "verify with a 1-day window"
    rule re-asked through the SAME broken parser and confirmed the false
    zero. A zero can only ever be verified by a KNOWN-NONZERO control:
    rc_window.control() parses page 1 of a window that provably holds 315
    documents, and raises ProbeBroken instead of returning an empty list."""
    import rc_window as RW
    n = RW.control()
    print(f"  control window parses {n} rows - probe OK")
    today = dt.date.today()
    start = today - dt.timedelta(days=lookback - 1)
    rows, pages = RW.window(start.isoformat(), today.isoformat())
    print(f"  window {start} .. {today}: {len(rows):,} rows over"
          f" {pages} page(s)")
    got = [f"RC_{r['internal_id']}" for r in rows]
    nav = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)
    fresh = [i for i in got if not nav.execute(
        "SELECT 1 FROM navigation WHERE id=?", (i,)).fetchone()]
    nav.close()
    if got:
        print(f"  {len(got):,} in window · already held"
              f" {len(got)-len(fresh):,} · NEW {len(fresh):,}")
    return fresh, True


# ── STEP 4 landing · the synchronization database ────────────────────────
DDL = """CREATE TABLE IF NOT EXISTS synchronization (
    run_at TEXT NOT NULL, source TEXT NOT NULL,
    system_total INTEGER, source_total INTEGER, delta INTEGER, doc_ids TEXT,
    PRIMARY KEY (run_at, source))"""


def land(rows, quiet=False):
    con = sqlite3.connect(SYNC_DB, timeout=600)
    con.execute(DDL)
    # ⚠ AS-OF, NOT PER-DAY (login 2026-08-22: "I want to see it delta and
    # totalled as of, since it changes so much with its current date set
    # up"). run_at is a TIMESTAMP so every run keeps its own row and the
    # table reads as a history of measured moments; a date key collapsed
    # every run of a day into one row and erased how the day moved.
    # Sorts lexicographically, so MAX(run_at) is still "latest".
    run_at = time.strftime("%Y-%m-%d %H:%M")
    for src, st, so, d, ids in rows:
        # ⚠ A SAME-DAY RE-RUN MERGES INTO THE DAY'S ROW, NEVER REPLACES IT.
        # Measured 2026-08-21: the afternoon kick-off (+230) overwrote the
        # morning row (+2,146), so the ledger would have said the day
        # gathered 230 when it gathered 2,376. The day's row is the UNION of
        # the day's ids; system_total stays the day's FIRST measurement
        # (before any absorption) so delta = what the whole day found.
        prev = con.execute(
            "SELECT system_total, doc_ids FROM synchronization"
            " WHERE run_at=? AND source=?", (run_at, src)).fetchone()
        if prev and prev[1]:
            # END-OF-RUN semantics (2026-08-22): doc_ids stays the UNION
            # (the day's whole catch) but the STATE columns carry the
            # LATEST run's truth - system_total = newest after-count,
            # delta = newest outstanding (0 = level, visible), source =
            # ours + outstanding. (The old merge reset st to the day's
            # FIRST measurement and delta to day-found - it silently
            # converted a fresh level row back into the old shape.)
            merged = list(dict.fromkeys(
                [i for i in prev[1].split(";") if i]
                + [i for i in ids.split(";") if i]))
            ids = ";".join(merged)
            so = st + d
        con.execute("INSERT OR REPLACE INTO synchronization VALUES"
                    " (?,?,?,?,?,?)", (run_at, src, st, so, d, ids))
    # ⚠ TOTAL SUMS EVERY SOURCE'S LATEST ROW, not just the sources THIS run
    # refreshed. A --source richmond run once wrote TOTAL = richmond alone
    # (2,426,588), erasing acris from the system-wide picture. The table is
    # source-oriented and sources run independently - TOTAL must always be
    # derived from the table, never from one run's arguments.
    latest = con.execute(
        "SELECT source, system_total, source_total, delta"
        " FROM synchronization s WHERE source != 'TOTAL' AND run_at ="
        " (SELECT MAX(run_at) FROM synchronization WHERE source = s.source)"
    ).fetchall()
    tot = ("TOTAL", sum(r[1] or 0 for r in latest),
           sum(r[2] or 0 for r in latest), sum(r[3] or 0 for r in latest), "")
    # ⚠ TOTAL SITS AT THE BOTTOM, ALWAYS (login). DB Browser's default view
    # is rowid order = insertion order, and INSERT OR REPLACE on a source
    # row hands it a fresh rowid BELOW an existing TOTAL - so every
    # incremental landing pushed acris under the TOTAL row. Delete and
    # re-insert TOTAL after every landing so it always holds the highest
    # rowid in the table.
    con.execute("DELETE FROM synchronization WHERE source='TOTAL'"
                " AND run_at=?", (run_at,))
    con.execute("INSERT INTO synchronization VALUES (?,?,?,?,?,?)",
                (run_at, *tot))
    con.commit()
    if quiet:
        con.close()
        return
    shown = ([(s, st, so, d, "") for s, st, so, d in latest]
             if len(latest) > len(rows) else rows)
    print(f"\n{'source':<9} {'system total':>13} {'source total':>13}"
          f" {'delta':>8}  doc ids")
    by_src = {r[0]: r[4] for r in rows}
    for src, st, so, d, _ in shown + [tot]:
        ids = by_src.get(src, "")
        n = len(ids.split(";")) if ids else 0
        head = ",".join(ids.split(";")[:2]) + ("..." if n > 2 else "")
        print(f"{src:<9} {st:>13,} {so:>13,} {d:>+8}  {head or '-'}")
    con.close()


def step5_handoff(ids):
    """STEP 5 · send the doc ids to the Legal Instruments db. nav_append is
    the ONE inserter (INSERT OR IGNORE - a re-run can never blank a
    recorded_details we already paid a request for; collisions are counted,
    not feared). The running acquisition lanes need no signal: they select
    on empty cells, so an appended row is already on their work list."""
    if not ids:
        print("STEP 5 · nothing to hand off")
        return
    f = HERE / "_sync_handoff_ids.txt"
    f.write_text("\n".join(ids), encoding="utf-8")
    print(f"STEP 5 · handing {len(ids):,} doc ids to the Legal Instruments db")
    subprocess.run([PY, "-u", str(HERE / "nav_append.py"),
                    "--ids", str(f), "--apply"], cwd=str(HERE))


def main():
    print(f"SYNCHRONIZATION — legal instruments — {time.strftime('%Y-%m-%d %H:%M')}")
    # ⚠ ONE WALKER AT A TIME. A second edge/gap walk beside a running one
    # doubles the polite sequential shape into something else entirely.
    ps = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\""
         " | ForEach-Object { $_.CommandLine }"],
        capture_output=True, text=True, timeout=60).stdout
    # busy = the heavy NETWORK walk only. routine_4am's land/map stages are
    # LOCAL - blocking a 10-request edge probe on their process name kept
    # step 6 waiting on work that touches no ACRIS connection at all.
    busy = any(k in ps for k in ("live_gap.py", "crfn_monitor.py"))

    print("\nSTEP 1 · system totals (Legal Instruments Navigation db)")
    sys_t = step1_system_totals()
    print(f"  acris {sys_t['acris']:,} · richmond {sys_t['richmond']:,}")

    out = []
    if a.source in ("both", "acris"):
        print("\n-- ACRIS --")
        if busy:
            print("  ⚠ another ACRIS walk is already running - SKIPPING the"
                  " edge/gap this run rather than doubling the load.")
        else:
            # STEPS 2-6 AS A CONVERGING LOOP (login): measure -> gather ->
            # send -> CHECK delta = 0 -> if not, kick off again. Bounded.
            sys_now, all_ids = sys_t["acris"], []
            measured_a = False
            last_span = 0
            for rnd in (1, 2, 3):
                label = "STEP 2 · crfn edge" if rnd == 1 else \
                        f"STEP 6 · check (round {rnd - 1} done - re-ask)"
                print(label)
                e = acris_step2_edge()
                if e is None:
                    print("  ⚠ edge unproven - stopping this source")
                    break
                span = e.get("span") or 0
                measured_a, last_span = True, span
                print(f"STEP {'3' if rnd == 1 else '6'} · delta ="
                      f" {sys_now + span:,} - {sys_now:,} = +{span:,}")
                if span == 0:
                    print("  ✓ delta = 0 - LEVEL")
                    break
                if a.dry:
                    print("STEP 4 · (dry - walk skipped)")
                    break
                if rnd > 1:
                    print(f"  not level - KICKING OFF again for the"
                          f" residual {span:,}")
                ids = acris_step4_ids(False, sys_now, sys_now + span,
                                      span) or []
                print(f"STEP 4 · {len(ids):,} doc ids resolved and landed"
                      f" along the walk")
                step5_handoff(ids)
                all_ids += [i for i in ids if i not in all_ids]
                # STEP 6's OUR-SIDE RECOUNT (login: "sync recounting our db
                # doc id total and the source total and assuring its 0") -
                # it proves the handoff physically landed, not arithmetic
                sys_now = step1_system_totals()["acris"]
                print(f"STEP 6 · our db recount: {sys_now:,}")
            # ⚠ A MEASURED ZERO WRITES ITS ROW (2026-08-22: richmond ran,
            # proved LEVEL 215/215-held, wrote nothing - and the ledger
            # read exactly like the run had never happened). Only a FAILED
            # measurement leaves no row. COLUMNS ARE END-OF-RUN STATE
            # (login 2026-08-22: the run-start snapshot "doesnt really
            # show them zeroing out" and cross-day TOTALs didn't add up):
            # system_total = our count AFTER (the landing recount) ·
            # delta = STILL OUTSTANDING (0 = level, the zero visible) ·
            # doc_ids = what THIS run landed. Rows before 2026-08-22
            # carry the old run-start semantics.
            if measured_a and not a.dry:
                out.append(("acris", sys_now, sys_now + last_span,
                            last_span, ";".join(all_ids)))

    if a.source in ("both", "richmond"):
        print("\n-- RICHMOND --")
        print("STEP 2 · date-range window (carries the doc ids = step 4)")
        # ⚠ AN UNREACHABLE SOURCE IS A REPORT, NOT A CRASH (measured
        # 2026-08-21: a transient DNS failure tracebacked the whole routine
        # and took the acris row down with it). No measurement -> no row;
        # the previous run's row stands and tomorrow re-asks.
        sys_now, all_r = sys_t["richmond"], []
        measured_r = False
        last_n = 0
        for rnd in (1, 2, 3):
            try:
                fresh, _ = richmond_step24(a.lookback, sys_now)
            except Exception as e:
                print(f"  ⚠ window unreachable ({type(e).__name__}) - "
                      f"stopping this source; the last measured row stands")
                break
            measured_r, last_n = True, len(fresh)
            print(f"STEP {'3' if rnd == 1 else '6'} · delta ="
                  f" {sys_now + len(fresh):,} - {sys_now:,}"
                  f" = +{len(fresh):,}")
            if not fresh:
                print("  ✓ delta = 0 - LEVEL")
                break
            if a.dry:
                break
            if rnd > 1:
                print(f"  not level - KICKING OFF again for the residual")
            # STEP 4 = these ids (the window rows carry them); STEP 5 sends
            step5_handoff(fresh)
            all_r += [i for i in fresh if i not in all_r]
            sys_now = step1_system_totals()["richmond"]
            print(f"STEP 6 · our db recount: {sys_now:,}")
        if measured_r and not a.dry:   # measured zero = a row; END-OF-RUN
            out.append(("richmond", sys_now, sys_now + last_n,
                        last_n, ";".join(all_r)))
        # MATURATION (2026-08-22): a doc landed the day it was recorded
        # freezes a premature rd - instrument blank (the county publishes
        # "Document No." with ~a-day lag) and image_state 'absent' (the
        # scan lag), which hides it from the instrument audit AND from
        # rc_mint's pdf selection forever. The refresh re-walks young
        # premature docs daily until they mature; it converges on its own.
        if not a.dry:
            subprocess.run([sys.executable,
                            str(HERE / "rc_rd_refresh.py")], timeout=3600)

    if out and not a.dry:
        land(out)          # the ledger row: today's TOTAL gathered per source
    elif a.dry:
        print("\n(dry - nothing landed)")

    # THE BRAIN BANKS ITSELF (login 2026-08-22: "work the push into py so we
    # never miss important details"). Every sync day also refreshes the
    # off-drive backup: py/md/json from both roots + the db schema/triggers
    # -> C:\dev\cre-backup -> github.com/loginwilson/cre-backup. The pdfs
    # and dbs are re-derivable; the PROCESS is not, and it changes daily.
    # Guarded: a dead network or a git hiccup must never fail the sync -
    # the backup reports and the next day's run retries by design.
    if not a.dry:
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", r"C:\dev\cre-backup\refresh.ps1"],
                capture_output=True, text=True, timeout=900)
            tail = (r.stdout or "").strip().splitlines()
            print("BACKUP · " + (tail[-1] if tail else f"exit {r.returncode}"))
        except Exception as e:
            print(f"BACKUP · skipped ({e}) - next sync retries")


main()
