"""ROUTINE UPDATE — the live report on how every routine is performing
(login 2026-08-21: "Phase, cadence, source, metrics, status").

    python routine_update.py            one pass (all phases)
    python routine_update.py --loop     the reporting daemon

One row per PHASE x SOURCE, written to Updates.db (watch it in DB Browser,
read-only) and printed for the chat monitor:

    phase | source | cadence | rate | increase | %incr | landed/needed |
    %of total | status

THE FIVE METRICS (login, standing): rate · increase amount · % increase ·
% of total · landed/needed. LIVE SHAPE (login 2026-08-21 night: "as of
seems unnecessary if we are doing 60 second intervals"): every row
refreshes EVERY 60s pass; rate AND increase are both measured over the
same trailing ~20-min window (one denominator - single-tick increases are
commit-lump noise); as_of is a plain freshness stamp, and a stale stamp
IS the signal the daemon died. ⚠ landed can only exceed needed through
COUNTER arithmetic (stale walker-generation logs summed onto the
baseline - 9 of them caused the 100.15% reading): the fix is re-baseline
from a TRUE table count and retire consumed logs, never a cap.

⚠ THE UNIT IS DOC/S, ALWAYS (login 2026-08-21: "we only measure doc/s").
Every counter this board reads is a DOCUMENT count - rd lanes' "+N this
run", pdf lanes' "N pdfs" + imageless, sync/nav ids. Pages are a
lane-internal load gauge; the board must never parse a page number into a
rate. If a new lane's log only prints pages, fix THE LANE to print docs.

⚠ STATUS IS COMPUTED, NEVER HAND-SET. A flat counter and a dead process
look identical unless the reporter checks BOTH the numbers and the process
list - that confusion cost an hour on 2026-08-21:
    COMPLETE     landed == needed (and needed > 0)
    ACTIVE       work is landing on this row
    PENDING      deliberately waiting - parked lanes, gated passes, not-yet
    STALLED      an unexpected break - wedged, errored, or died
    (four and only four - login 2026-08-23)

⚠ NO FULL TABLE SCANS ON A TICK. A 24M-row COUNT stops the WAL
checkpointing and starves the lanes (measured: WAL grew to 1.45 GB).
Absolutes come from the daily sync's step-1 count (the sync db) plus each
lane's own log counters folded across restarts - the proven pull_tick
pattern. Cadence is per phase, from updates_config.json, re-read every
pass so it can be adjusted at request mid-run.
"""
from __future__ import annotations

import json
import pathlib
import re
import sqlite3
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).parent
DECODER = pathlib.Path(r"C:\Users\smile\Downloads"
                       r"\Source Folder (Real Estate Data)"
                       r"\Decoder Prompt\decoder")
sys.path.insert(0, str(DECODER))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP

CONF = HERE / "updates_config.json"
BOARD = HERE / "Updates.db"
STATE = HERE / "_update_state.json"
SYNC_DB = (pathlib.Path(r"D:\CRE Decoding System\00 Synchronizations")
           / "Legal Instruments Synchronization"
           / "Legal Instruments Synchronization.db")
W = CP.NAV_WORK                       # the lanes' log folder
# ⚠ BY THE MINUTE + BY THE WINDOW (login 2026-08-23: "rate now shows the 60
# sec performance and the window is a 5 minute window... that solves the issue
# of wanting to see performance in a moment and over time"). rate_now = last
# ~60s, rate/increase/pct_increase = the 5-min window, ETA extrapolates the
# window. The old 20-min window meant a stall stayed invisible for 20 minutes.
RATE_WINDOW = 5 * 60

# lane heartbeat logs per (phase, source) - the stall alarm reads MTIME only.
# rd/image lanes print PROGRESS ~1/min into these; richmond pdf logs its pulls.
_HEARTBEAT = {
    ("acquisition rd", "acris"): "rd_walk_a[1-4].log",
    ("acquisition pdf", "acris"): "image_walk_i[1-3].log",
    # ⚠ rc_pdf_land.log only hears the RAW-incoming lander; the db writer is
    # rc_pdf_pull, which logs into its own cwd (the decoder dir). Watching the
    # lander's log kept a 6-hour wedge invisible until 2026-08-23 20:00.
    ("acquisition pdf", "richmond"): str(DECODER / "rc_pull.log"),
}
_STALE_S = 180


def _lane_log_stale(phase, src, now):
    """True when EVERY heartbeat log for this lane is >_STALE_S old.

    Mtime only - zero queries. No heartbeat spec, or no matching files,
    means no alarm (we cannot call unknown silence a stall)."""
    pat = _HEARTBEAT.get((phase, src))
    if not pat:
        return False
    base = pathlib.Path(pat)
    files = [base] if base.is_absolute() else list(W.glob(pat))
    mt = [p.stat().st_mtime for p in files if p.exists()]
    return bool(mt) and (now - max(mt)) > _STALE_S


# ── THE LANES' OWN CUMULATIVE COUNTERS (login 2026-08-23: "it needs to be
# tied with the result the python is coding into the db"). Every PROGRESS
# line's counter IS a count of db rows that lane landed this run - rd prints
# "X total", image prints "N pdfs" (+ imageless verdicts, which also fill the
# pdf column). Differencing THESE over our own 60s/300s samples is exact and
# costs a file-tail read - no anchors, no baselines, no log-sum pipelines.
_CUM_SPEC = {
    ("acquisition rd", "acris"):
        (("rd_walk_a1.log", "rd_walk_a2.log", "rd_walk_a3.log",
          "rd_walk_a4.log"), r"([\d,]+) total"),
    ("acquisition pdf", "acris"):
        (("image_walk_i1.log", "image_walk_i2.log", "image_walk_i3.log"),
         r"([\d,]+) pdfs.*?([\d,]+) imageless"),
    # rc_pdf_pull's "db N" IS rows written to the pdf column this run -
    # the exact "result the python is coding into the db" (login). Absolute
    # path: the puller logs into its own cwd, not NAV_WORK.
    ("acquisition pdf", "richmond"):
        ((str(DECODER / "rc_pull.log"),), r"db ([\d,]+)"),
}


def _lane_cum(phase, src, st):
    """Sum of the arms' cumulative counters, PER-FILE STATEFUL.

    ⚠ THE 9.02/+0 BUG (login's screenshot, 7:48 PM): summing only what parsed
    THIS pass meant one arm's missed parse (mid-write tail, unflushed line)
    dropped the sum, tripped the reset, and for two passes rate_now showed a
    stale anchor while increase_now read 0 - a rate with no increase, which
    is arithmetically impossible and reads as exactly the nonsense it is.
    Counters are MONOTONIC within a run, so the correct treatment of a
    missed parse is CARRY THE FILE'S LAST VALUE; a genuine restart shows as
    that file's value DROPPING, which resets that file alone."""
    spec = _CUM_SPEC.get((phase, src))
    if not spec:
        return None
    files, pat = spec
    mem = st.setdefault("cumf", {}).setdefault("%s|%s" % (phase, src), {})
    for name in files:
        p = pathlib.Path(name)
        if not p.is_absolute():
            p = W / name
        try:
            tail = p.read_text(encoding="utf-8", errors="replace")[-4000:]
        except OSError:
            continue
        hits = re.findall(pat, tail)
        if not hits:
            continue                     # carry last value
        last = hits[-1]
        v = (sum(int(x.replace(",", "")) for x in last)
             if isinstance(last, tuple) else int(last.replace(",", "")))
        mem[name] = v                    # a drop is just the new (reset) value
    return sum(mem.values()) if mem else None


# ⚠ NOW_WINDOW MUST EXCEED MIN_SPAN OR `rate_now` CAN NEVER FIRE. They were
# both 180 s, so the recent slice could never span MORE than the minimum it
# had to clear - with samples 60 s apart the oldest one inside the window sits
# ~120 s back, fails the guard, and rate_now silently copied the lifetime avg
# every pass. The board printed "now 6.6/s | avg 6.6/s" forever and looked
# frozen while landed climbed steadily (login 2026-08-22: "the rate and rate
# now arent different"). A window and its own minimum are not the same number.
NOW_WINDOW = 90            # ~the last minute (90s so two 60s passes fit)
# ⚠ NEVER DIVIDE BY A GAP SHORTER THAN THE SOURCE'S OWN UPDATE INTERVAL.
# Lane logs arrive in lumps ~60s apart, so a sample pair 11s apart divides
# a whole minute of work by 11s: on the 2026-08-22 daemon restart that
# published acris rd at 295.68 docs/s, more than 2x a ceiling we had
# MEASURED at ~138. It decayed to 64.5 over three passes as the window
# filled - but a spike that corrects itself is still a spike that got
# published. Below MIN_SPAN there is no rate yet, and saying so beats
# inventing one.
MIN_SPAN = 45
# filled by rows(): the rate each lane REPORTS about itself, per (phase,
# source). Preferred over any rate the board differences for itself.
LANE_RATE = {}
# ⚠ Rows whose `landed` came from board_truth.py this pass. Their counter is
# re-measured on a 30-minute cadence, so it is authoritative about the LEVEL and
# meaningless as a derivative - differencing it yields the anchor's step, not
# throughput. These rows take their rate from the lane's own published figure.
ANCHORED = set()
# filled by rows(): keys won by the BACKFILL SWEEPER only, per source -
# the sole component that closes organization's gap. Trigger keys arrive
# with new rd work and never touch the backlog, so they must not date it.
ORG_BACKFILL = {}

# phase | source | metrics | status | as_of - nothing else (login: "cadence
# makes no sense here"; it is a config knob, not a measurement)
# ⚠ THE SYMMETRIC LAYOUT (login 2026-08-23: "rate now should have its
# increase and percentage relative to needed. then rate (the larger window)
# gets increase and pct increase to needed... then the eta should be one on
# the rate now and rate window"). Three timescales, each with its full kit:
#   NOW (60s)     rate_now · increase_now · pct_now · eta_now
#   WINDOW (5m)   rate · increase · pct_increase · eta
#   TOTAL         landed / needed · pct_of_total
# eta_now vs eta disagreeing IS the signal something just changed.
DDL = """CREATE TABLE IF NOT EXISTS update_board (
    phase TEXT NOT NULL, source TEXT NOT NULL,
    rate_now REAL, increase_now INTEGER, pct_now REAL, eta_now TEXT,
    rate REAL, increase INTEGER, pct_increase REAL, eta TEXT,
    landed INTEGER, needed INTEGER, pct_of_total REAL,
    status TEXT, as_of TEXT,
    PRIMARY KEY (phase, source))"""
N_COLS = 15   # ⚠ schema changes DROP the old table or every INSERT dies with
              # a column-count error while the table survives (measured; the
              # board is rebuilt every pass, so dropping loses nothing)


def eta_of(landed, needed, rate):
    """Time left, extrapolated from THIS row's own measured metrics (login
    2026-08-22: "eta should work arithmetics on the rate relative to its
    landed/needed as a percentage to extrapolate time left").

        share of the whole gained per window = increase / needed
        windows left = (1 - landed/needed) / that share
        time left    = windows left x window length   ==   remaining / rate

    Both forms are the same number; the code uses remaining/rate because
    rate already carries the window. pct_increase now shares the same fixed
    denominator (NEEDED - login 2026-08-23), so it is this window's slice of
    pct_of_total; the old landed-denominator form modelled compounding and
    was banned from ETA use for exactly that reason.

    A stalled lane gets "-", never "never": no rate is no evidence about
    the future."""
    left = (needed or 0) - (landed or 0)
    if left <= 0:
        return "complete"
    if not rate or rate <= 0:
        return "-"
    s = left / rate
    # ONE UNIT, ALWAYS (login 2026-08-22: "measure in days not hours.
    # consistency is important" - overriding the hour-tier tried minutes
    # earlier). DAYS everywhere, two decimals: comparability across rows
    # beats per-row cleverness, the same lesson as doc/s being the one
    # rate unit. The frozen-looking ETA is solved by PRECISION, not by
    # switching units: 0.01 day = ~14 min, so "1.90 days" ticks all
    # afternoon while staying the same unit as "37.40 days".
    return f"{s/86400:.2f} days"

# which running process proves a row is being WORKED (status PENDING vs
# STALLED); matched against the live python command lines
PROC_SIG = {
    ("synchronization", "acris"): ("live_gap.py", "crfn_monitor.py",
                                   "routine_synchronization.py",
                                   "routine_4am.py"),
    ("synchronization", "richmond"): ("routine_synchronization.py",
                                      "rc_daily.py"),
    ("navigation", "acris"): ("nav_append.py",),
    ("navigation", "richmond"): ("nav_append.py",),
    ("acquisition rd", "acris"): ("rd_walk.py",),
    ("acquisition pdf", "acris"): ("image_walk.py",),
    # ⚠ rc_pdf_pull.py ADDED 2026-08-22 - it IS the richmond pdf lane now.
    # The browser loop was replaced that night and this map was not updated,
    # so the board could not attribute the work to this row: it reported
    # 0.20/s while the lane fetched 13/s (login: "still dont think update is
    # reading the richmond pdf acq right since its sub 1 but we expect over
    # 10"). A lane map that names dead processes reports a live lane as idle.
    # ⚠ ONLY THE ACQUIRER, NOT ITS HELPERS. Listing rc_feed and rc_pdf_land
    # here made a DEAD LANE read ACTIVE. Measured 2026-08-23 02:48:
    # rc_pdf_pull stopped itself on a 403 at 01:40, richmond pdf sat at
    # 203,917 with a measured rate of **0.00/s** - and the row still said
    # ACTIVE, because rc_feed (idle at its mint cap, 1,490 ready and nobody
    # consuming) and rc_pdf_land (backlog drained to 0) were both still alive.
    #
    # The board's own definition is "ACTIVE means a process IS PULLING on this
    # row - not that a process related to it happens to exist." An idle helper
    # is not pulling. Masking a stopped acquirer behind two idle helpers
    # defeats the entire STALLED state, which is the one state that says
    # "somebody needs to look at this".
    ("acquisition pdf", "richmond"): ("rc_pdf_pull.py",),
    ("organization", "acris"): ("nav_key.py --src acris",),
    ("organization", "richmond"): ("nav_key.py --src rc",),
}


def cfg():
    # ⚠ utf-8-sig: a PowerShell ConvertTo-Json edit wrote a BOM on 2026-08-23
    # and the silent fallback below BLANKED the whole config - show-filter off,
    # parked list gone, retired phases back on the board. A config that fails
    # to parse must SAY so, because the fallback is indistinguishable from
    # "no config" and reads as a board full of ghosts.
    try:
        return json.loads(CONF.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print("⚠ updates_config.json UNREADABLE (%s) - running with NO show "
              "filter and NO parked list; the board will show every phase"
              % e, flush=True)
        return {"cadence": {}, "parked": []}


def last_progress(name):
    p = W / f"{name}.log"
    out = ""
    if p.exists():
        for ln in p.read_text(encoding="utf-8",
                              errors="replace").splitlines():
            if "PROGRESS" in ln:
                out = ln
    return out


def num(line, pat):
    m = re.search(pat, line)
    return int(m.group(1).replace(",", "")) if m else 0


def sync_rows():
    """the sync db is small - reading it whole is free"""
    try:
        con = sqlite3.connect(f"file:{SYNC_DB}?mode=ro", uri=True, timeout=30)
        # ⚠ THE LEDGER HOLDS TWO KINDS OF ROW AND `MAX(run_at)` CANNOT TELL
        # THEM APART. routine_synchronization writes a TOTAL row (system_total
        # = our full count); sync_fast / rc_sync_fast write a DELTA row
        # (system_total 0, delta = ids just landed). Same columns, same source,
        # and the delta row is always the newest.
        #
        # Measured live 2026-08-23 01:45: the gate test's delta row
        # (`acris · system_total 0 · delta 5`) became "the latest acris row",
        # so the board showed **navigation acris 0/0 0.0%** and
        # **synchronization acris 0/0** for phases that are 100% COMPLETE.
        #
        # ⚠ THIS IS THE THIRD PLACE THE SAME DEFECT LIVED tonight (board_truth's
        # denominator, and its own landed subtraction). One ambiguous table,
        # three readers, three bugs - which is what an unmarked row kind costs.
        # The durable fix is a `kind` column; until then every reader that wants
        # a TOTAL must say so.
        rows = {r[0]: r for r in con.execute(
            "SELECT source, system_total, source_total, delta,"
            " COALESCE(doc_ids,'') FROM synchronization s"
            " WHERE source != 'TOTAL' AND system_total > 0 AND run_at ="
            " (SELECT MAX(run_at) FROM synchronization"
            "  WHERE source = s.source AND system_total > 0)")}
        con.close()
        return rows
    except Exception:
        return {}


def gather():
    """landed/needed per (phase, source) - logs + small dbs, no scans"""
    sy = sync_rows()
    out = {}
    for src in ("acris", "richmond"):
        r = sy.get(src)
        if r:
            ids = len(r[4].split(";")) if r[4] else 0
            # LEDGER SEMANTICS since 2026-08-22: columns are END-OF-RUN
            # state - system_total = our count AFTER the run, delta =
            # STILL OUTSTANDING (0 = level), doc_ids = what that run
            # landed. ⚠ SYNC'S ROW IS OUR TOTAL vs THEIR TOTAL, never
            # "ids gathered today" (login 2026-08-22: "sync richmond just
            # has 0's but the others have their last run to 100%") - a
            # quiet day gathered 0 of 0 and read as 0%, which looks
            # broken when it means PERFECTLY LEVEL. The day's catch is
            # what the increase column is for.
            out[("synchronization", src)] = ((r[1] or 0), (r[2] or 0))
            # navigation's claim: every id tabled = our after-count.
            out[("navigation", src)] = (r[1] or 0, r[2] or 0)
    # acquisition: daily true-count baseline + the lanes' own run counters
    base = {}
    bf = W / "dash_baseline.json"
    if bf.exists():
        try:
            base = json.loads(bf.read_text())
        except Exception:
            pass
    # every rd lane log NEWER THAN THE BASELINE counts (one log per lane,
    # last progress line only). Logs older than the baseline stamp are
    # already inside base['acris_rd'] - summing them again double-counts
    # (measured 2026-08-21: rd_walk_a..d predate the noon baseline).
    # ⚠ THE CONSUMPTION STAMP IS DATA, NOT THE FILE'S mtime. With mtime,
    # every baseline WRITE (adding a marker, correcting one key) reset the
    # stamp and made every CURRENT lane log look already-consumed - the
    # board showed acris rd 28.9% -> 8.2% twice and read like total
    # failure while the lanes ran untouched (2026-08-22). base["at"] moves
    # only when logs are deliberately consumed.
    _at = base.get("at")
    try:
        import datetime as _dt
        bstamp = _dt.datetime.fromisoformat(_at).timestamp() if _at else 0
    except Exception:
        bstamp = 0
    # ⚠ A LANE ALREADY MEASURED ITS OWN RATE - READ IT, DO NOT RE-DERIVE IT.
    # The board used to difference `landed` between its own 60s passes. But
    # a lane emits its PROGRESS line every ~60s too, so the board was
    # sampling exactly as fast as the source updates: the two drift in and
    # out of phase and the SAME healthy fleet reads 0.0/s, then 175.4/s,
    # then 13.3/s (2026-08-22, login: "the measurments are a bit all over").
    # Aliasing, not throughput. Every lane prints a rate computed over its
    # OWN full run - authoritative, smooth, and free. Sum those instead.
    # ⚠ A lane whose log has gone quiet is NOT contributing to the rate: a
    # 17-hour-dead image_walk log was still being summed into the fleet
    # total. Only logs touched within LANE_FRESH count toward a RATE (they
    # still count toward LANDED - that work happened and did not un-happen).
    LANE_FRESH = 10 * 60

    def fresh(p):
        return time.time() - p.stat().st_mtime <= LANE_FRESH

    rd_logs = [p for p in W.glob("rd_walk_*.log")
               if not p.name.endswith(".err.log") and p.stat().st_mtime > bstamp]
    pdf_logs = [p for p in W.glob("image_walk_*.log")
                if not p.name.endswith(".err.log") and p.stat().st_mtime > bstamp]
    LANE_RATE.clear()
    r = 0.0
    for p in rd_logs:
        if fresh(p):
            m = re.search(r"([\d.]+) docs/s", last_progress(p.stem) or "")
            r += float(m.group(1)) if m else 0.0
    if r:
        LANE_RATE[("acquisition rd", "acris")] = r
    # ⚠ THE PDF LANE PRINTS pg/s - PAGES ARE A LOAD GAUGE, NEVER A HEADLINE
    # (login, standing: "we only measure doc/s"). Derive doc/s from the
    # lane's own doc counter over its own elapsed minutes. imageless docs
    # count: they are RESOLVED, they just have no image to fetch, and
    # `landed` already sums them - a rate whose numerator excluded them
    # would disagree with its own denominator.
    r = 0.0
    for p in pdf_logs:
        if fresh(p):
            ln = last_progress(p.stem) or ""
            d = (num(ln, r"PROGRESS ([\d,]+) pdfs")
                 + num(ln, r"([\d,]+) imageless"))
            mins = num(ln, r"([\d,]+) min")
            r += d / (mins * 60) if mins else 0.0
    if r:
        LANE_RATE[("acquisition pdf", "acris")] = r
    # ⚠ RICHMOND'S PDF LANE HAD NO RATE ENTRY AT ALL, so its row fell through to
    # differencing `landed` - and once `landed` came from the 30-minute truth
    # anchor, that difference measured THE ANCHOR'S STEP, not the lane. It read
    # 1.91/s while rc_pdf_pull's own log said 10.81/s.
    # rc_pdf_pull prints its rate over its own full run, e.g.
    #   +132   total 54510   10.81/s  19069.9 MB  db 54480  q0  err 13
    # Read it. Do not re-derive what the lane already measured.
    for pp in (W / "rc_pull.log", DECODER / "rc_pull.log"):
        if not pp.exists() or not fresh(pp):
            continue
        lines = [ln for ln in pp.read_text(encoding="utf-8",
                                           errors="replace").splitlines()
                 if "total " in ln and "/s" in ln]
        if lines:
            m = re.search(r"total \d+\s+([\d.]+)/s", lines[-1])
            if m:
                LANE_RATE[("acquisition pdf", "richmond")] = float(m.group(1))
        break
    a_rd = base.get("acris_rd", 0) + sum(
        num(last_progress(p.stem), r"\+([\d,]+) this run") for p in rd_logs)
    # pdf lanes: same glob-newer-than-baseline rule as rd (the bridge
    # mirrors each image-walk arm to image_walk_<taskid>.log)
    a_pdf = base.get("acris_pdf", 0) + sum(
        num(last_progress(p.stem), pat) for p in pdf_logs
        for pat in (r"PROGRESS ([\d,]+) pdfs", r"([\d,]+) imageless"))
    rc_pdf = base.get("rc_pdf", 0)
    lp = W / "rc_pdf_land.log"
    if lp.exists():
        rc_pdf += sum(int(x) for x in re.findall(
            r"landed (\d+) pdfs",
            lp.read_text(encoding="utf-8", errors="replace")))
    # ⚠ rc_pdf_pull.py LANDS STRAIGHT INTO THE STORE and never passes through
    # _incoming, so rc_pdf_land.log cannot see it. Until this was added the
    # board reported 0.20/s while the lane ran at 13/s - it was counting only
    # the lander draining the old backlog. NO DOUBLE COUNT: a file the puller
    # wrote to the store is never in _incoming, so the lander never counts it.
    # ⚠ Its log holds ONE run (opened with '>'), and `total N` is cumulative
    # for that run - take the LAST, never the sum of the lines.
    # ⚠ AND LOOK IN THE RIGHT FOLDER. Added 2026-08-22, and it NEVER FIRED:
    # every other lane logs into NAV_WORK, but rc_pdf_pull.py writes
    # rc_pull.log into its own cwd (the decoder dir). `pp.exists()` was False
    # every pass, so the branch above quietly did nothing and 45,986 landed
    # richmond pdfs were omitted - which is 92% of the 49,996 gap measured
    # against the pdf column on 2026-08-23 (board 102,241 vs true 152,237).
    #
    # A FIX THAT DOES NOT FIRE IS INDISTINGUISHABLE FROM THE BUG IT FIXED, and
    # this one was written the same night it failed. Both locations are checked
    # now, newest wins - a path assumption should not be able to hide a lane.
    for pp in (W / "rc_pull.log", DECODER / "rc_pull.log"):
        if not pp.exists():
            continue
        tots = re.findall(
            r"total (\d+)", pp.read_text(encoding="utf-8", errors="replace"))
        if tots:
            # ⚠ ONE RUN per file (opened with '>'), `total N` cumulative within
            # it - take the LAST, never the sum of the lines.
            rc_pdf += int(tots[-1])
            break
    need_a = (sy.get("acris") or (0, 0, 21_612_715))[2] or 21_612_715
    need_r = (sy.get("richmond") or (0, 0, 2_426_588))[2] or 2_426_588

    # ⚠ EXACT RD LANDED FROM ix_nav_rd_todo (2026-08-24). The counter path
    # above zeroes on every lane relaunch ("+0 this run" against a stale
    # baseline published 12.9M while the table held 15.2M — login caught
    # it). The partial index makes the rd todo set countable in seconds;
    # total − todo cannot drift, reset, or double-count. Richmond rd is
    # complete, so every blank row in the index is acris by construction.
    # Guarded on the index existing — without it this COUNT would be the
    # 24M-row blob scan this file bans; fall back to the counter figure.
    try:
        _nc = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True,
                              timeout=15)
        _nc.execute("PRAGMA busy_timeout=15000")
        if _nc.execute("SELECT 1 FROM sqlite_master"
                       " WHERE name='ix_nav_rd_todo'").fetchone():
            a_rd = need_a - _nc.execute(
                "SELECT COUNT(*) FROM navigation"
                " WHERE recorded_details = ''").fetchone()[0]
        _nc.close()
    except Exception:
        pass

    # ⚠ THE `pdf` COLUMN OUTRANKS THE LOGS. Everything above this line is
    # counter arithmetic - baseline plus deltas scraped out of lane logs - and
    # counter arithmetic drifts one way only. Measured 2026-08-23 against the
    # column itself: richmond 102,241 shown vs 156,677 true, **a 35% undercount**,
    # because a single path assumption hid a whole lane. It read as healthy.
    #
    # `board_truth.py` counts the todo set straight off ix_nav_pdf_todo and
    # takes the denominator from the sync ledger. When its anchor is fresh it
    # REPLACES the log figure outright; the logs then serve their real purpose,
    # which is the delta since the anchor, not the total.
    #
    # ⚠ STALE ANCHOR MUST NOT WIN. An anchor older than TRUTH_FRESH is worse
    # than the logs (it cannot see the last hour of landings), so it is ignored
    # and the row says so. Never silently prefer an old truth to a live estimate.
    TRUTH_FRESH = 2 * 3600
    truth, truth_age, tj = {}, None, {}
    tf = HERE / "_board_truth.json"
    if tf.exists():
        try:
            import datetime as _dt
            tj = json.loads(tf.read_text(encoding="utf-8"))
            truth_age = (_dt.datetime.now() - _dt.datetime.fromisoformat(
                tj["at"])).total_seconds()
            if truth_age <= TRUTH_FRESH and not tj.get("warning"):
                truth = {k: v["landed"] for k, v in tj["sources"].items()}
        except Exception:
            truth = {}
    ANCHORED.clear()
    if truth:
        if "acris" in truth:
            a_pdf = truth["acris"]
            ANCHORED.add(("acquisition pdf", "acris"))
        if "richmond" in truth:
            rc_pdf = truth["richmond"]
            ANCHORED.add(("acquisition pdf", "richmond"))
        # ⚠ PREFER THE ANCHOR'S OWN RATE - it is the only figure here measured
        # from the TABLE. The lane alternative is `total_docs / total_minutes`,
        # a LIFETIME average, and this system already paid to learn that
        # "lifetime averages memorialize the past" (19 hours of history printed
        # 89.9/s while the fleet ran 122.7/s). Cross-checked by counting the
        # column twice 448 s apart: acris 9.56/s true vs 11.06/s lifetime.
        # The anchor's span IS its own interval, so it cannot alias.
        for k, v in (tj.get("sources") or {}).items():
            if v.get("rate") is not None:
                LANE_RATE[("acquisition pdf", k)] = v["rate"]

    out[("acquisition rd", "acris")] = (a_rd, need_a)
    out[("acquisition pdf", "acris")] = (a_pdf, need_a)
    out[("acquisition pdf", "richmond")] = (rc_pdf, need_r)
    # organization: NOT computed here - routine_organization writes its own
    # measured row (a fresh scan beats these stale baseline counters, and a
    # 24M-row count on a 5-minute tick is the WAL trap)
    # richmond rd: baseline FROM THE FILE (a hardcoded 2,426,803 here
    # survived two baseline rewrites and kept the row at 97%/100.17% -
    # 2026-08-21 11 PM; the baseline is data, never a literal) + the
    # CODED walk's lanes (rc_rd_walk)
    rc_rd = base.get("rc_rd", 0) + sum(
        num(last_progress(p.stem), r"\+([\d,]+) this run")
        for p in W.glob("rc_rd_walk_*.log")
        if not p.name.endswith(".err.log") and p.stat().st_mtime > bstamp)
    out[("acquisition rd", "richmond")] = (rc_rd, need_r)
    # ORGANIZATION, PER SOURCE (login 2026-08-22: "remove the old
    # organization and add in the 2 for acris and richmond"). Same shape as
    # the acq lanes: a measured baseline + the keyer's own "keyed N" log
    # lines newer than the baseline stamp. Denominator = rows that CAN key
    # (rd landed), because a row without rd has no evidence yet - keying
    # against the whole corpus would report progress against work that
    # does not exist.
    # ⚠ KEYING IS STRUCTURAL NOW, SO IT LEAVES NO LOG. The key_on_rd
    # trigger (2026-08-22) writes the key inside the same transaction that
    # lands the rd - no sweeper, no log line, nothing for a glob to sum.
    # So keyed progress RIDES rd progress: every acris row landed after
    # the trigger went live is keyed by construction. `trigger_rd_mark` is
    # the rd count at that moment; everything past it is keyed, and the
    # rows landed BEFORE it are the known backlog one quiet pass clears.
    mark = base.get("trigger_rd_mark")
    for src, key, tag, need in (("acris", "acris_keyed", "acris", a_rd),
                                ("richmond", "rc_keyed", "rc", rc_rd)):
        landed = base.get(key, 0)
        if src == "acris" and mark is not None:
            landed += max(0, a_rd - mark)
        p = W / f"nav_key_{tag}.log"
        if p.exists() and p.stat().st_mtime > bstamp:
            # ⚠ SUM EVERY SWEEP LINE, don't read the last one: each sweep
            # reports ITS OWN delta ("keyed 5,000 in 12s"), not a running
            # total - taking the last line would report one sweep as the
            # whole phase.
            swept = sum(int(x.replace(",", "")) for x in re.findall(
                r"keyed ([\d,]+) in",
                p.read_text(encoding="utf-8", errors="replace")))
            landed += swept
            ORG_BACKFILL[src] = swept
        ORG_BACKFILL.setdefault(src, 0)
        out[("organization", src)] = (landed, need)
    return out


def main(loop):
    con = sqlite3.connect(BOARD, timeout=120)
    # ⚠ THE MIGRATION CHECK MUST NAME EVERY COLUMN THE CODE WRITES. It
    # listed only "eta" when rate_now was added, so the old 11-column
    # table survived and every INSERT died with "11 columns but 12 values"
    # (2026-08-22). Derive the expectation from the DDL instead of a
    # hand-kept list, so adding a column can never desync it again.
    want = [c.split()[0] for c in DDL.split("(", 1)[1].split(")")[0]
            .replace("\n", " ").split(",") if c.split()
            and not c.strip().startswith("PRIMARY")]
    cols = [r[1] for r in con.execute("PRAGMA table_info(update_board)")]
    if cols and (set(want) - set(cols) or "cadence" in cols):
        con.execute("DROP TABLE update_board")     # old schema, transient data
    con.execute(DDL)
    cols = con.execute("PRAGMA table_info(update_board)").fetchall()
    if len(cols) != N_COLS:
        con.execute("DROP TABLE update_board")
        con.execute(DDL)
    st = {"hist": {}, "due": {}}
    if STATE.exists():
        try:
            st = json.loads(STATE.read_text())
        except Exception:
            pass
    while True:
        c = cfg()
        now = time.time()
        try:
            ps = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-CimInstance Win32_Process -Filter"
                 " \"Name='python.exe'\" | ForEach-Object"
                 " { $_.CommandLine }"],
                capture_output=True, text=True, timeout=60).stdout
        except Exception:
            ps = ""
        rows = gather()
        lines = []
        show = c.get("show") or []        # phase whitelist; empty = all
        # ⚠ THE BOARD READS IN PHASE ORDER, NOT ALPHABETICAL (login
        # 2026-08-22: "the order should be in order of the phases since org
        # is near bottom"). DB Browser shows rowid = insertion order, so
        # the table is rewritten each pass in pipeline order and the board
        # reads top-to-bottom as the work actually flows.
        ORDER = ["synchronization", "navigation", "acquisition rd",
                 "acquisition pdf", "organization", "extraction",
                 "resolution", "derivation"]
        def phase_rank(kv):
            (ph, sr), _ = kv
            return (ORDER.index(ph) if ph in ORDER else 99, ph, sr)
        con.execute("DELETE FROM update_board")   # rewritten in order below
        for (phase, src), (landed, needed) in sorted(rows.items(),
                                                     key=phase_rank):
            if show and phase not in show:
                continue
            key = f"{phase}|{src}"
            # LIVE: every row, every pass. rate AND increase share the
            # trailing ~20-min window - one denominator, lump-proof.
            h = [s for s in st["hist"].get(key, [])
                 if now - s[0] <= RATE_WINDOW] + [[now, landed]]
            # ⚠ A COUNTER THAT MOVES FASTER THAN WORK CAN = BASIS CHANGE,
            # NOT PROGRESS. These counters are monotonic and bounded: a
            # DROP (re-baseline, consumed log, restarted lane counting
            # from zero) and an IMPOSSIBLE JUMP (a dead feed restored, so
            # the count leaps back to truth) are the same event wearing
            # two faces. Both produced nonsense on 2026-08-22: -1,468,393
            # then +4,257,584 at "23,064/s". No lane on earth here
            # exceeds ~200 docs/s, so anything past MAX_RATE is the basis
            # moving. Drop the stale history and measure from here.
            MAX_RATE = 1000
            prev = h[-2] if len(h) > 1 else None
            if prev and (landed < prev[1] or
                         (landed - prev[1]) / max(now - prev[0], 1e-9)
                         > MAX_RATE):
                h = [[now, landed]]
            st["hist"][key] = h
            d = landed - h[0][1]
            span = now - h[0][0]
            was = h[0][1]
            # ⚠ CORRECTED 2026-08-22 (second swing of the pendulum): the
            # 20-MIN DIFFERENCED WINDOW IS THE RIGHT avg; the lane's own
            # lifetime rate is only the COLD-START FALLBACK. The morning's
            # aliasing disaster was SHORT windows (60s samples of 60s
            # lumps, 11s cold-starts) - a 20-min window holds ~20 lumps
            # and its edge error is ~5%. Preferring the lane's lifetime
            # rate over-corrected: 19 hours of history including every
            # dip printed "89.9/s" while the fleet measurably ran 122.7/s
            # (login: "shouldnt we be near 100/8" - it was ABOVE, and the
            # board hid it). A rate must track the CURRENT regime;
            # lifetime averages memorialize the past.
            rate = d / span if span >= MIN_SPAN \
                else LANE_RATE.get((phase, src), 0.0)
            # ⚠ NEVER DIFFERENCE AN ANCHORED COUNTER TO GET A RATE.
            # `landed` for the pdf rows now comes from board_truth.py, which
            # re-measures every 30 MINUTES. Differencing it over a 20-minute
            # window measures THE ANCHOR'S STEP, not the lane: acris pdf read
            # 1.37/s against a measured fleet of 11.06/s, and richmond read
            # 1.91/s against rc_pdf_pull's own 10.81/s. Same aliasing disease
            # as the 60s-sampling-60s-lumps morning, arriving by a new route -
            # I introduced it by making `landed` more accurate.
            #
            # An anchored counter is RIGHT about the LEVEL and USELESS as a
            # derivative. So for anchored rows the lane's own published rate
            # wins outright - it is measured over the lane's real elapsed time
            # and cannot alias against the anchor's cadence.
            if (phase, src) in ANCHORED and (phase, src) not in _CUM_SPEC and LANE_RATE.get((phase, src)):
                rate = LANE_RATE[(phase, src)]
            # TWO RATES, ON PURPOSE (login 2026-08-22, asked three times:
            # "why wont update track it" while watching files pour in).
            # `rate` is the 20-min window - stable, lump-proof, what ETA
            # uses, but it keeps reporting a stall for 20 min after the
            # stall ends. `rate_now` is the last few minutes - what the
            # eye sees. Neither is wrong; disagreement between them IS
            # the signal that something just changed.
            recent = [s for s in h if now - s[0] <= NOW_WINDOW]
            rspan = (now - recent[0][0]) if len(recent) > 1 else 0
            rate_now = ((landed - recent[0][1]) / rspan) \
                if rspan >= MIN_SPAN else rate
            # ⚠ SAME FOR rate_now, and MORE so - its window is only a few
            # minutes, so an anchor that steps every 30 reads 0.0 nearly always
            # (measured: 0.0 on both pdf rows while the lanes ran ~11/s each).
            # A zero here reads as "stalled" and is the single most misleading
            # cell on the board.
            if (phase, src) in ANCHORED and (phase, src) not in _CUM_SPEC and LANE_RATE.get((phase, src)):
                rate_now = LANE_RATE[(phase, src)]
            # FOUR STATES (login 2026-08-21): complete · active · pending ·
            # stalled. ACTIVE means a process IS PULLING on this row - not
            # "an increase happened to land inside this tick" (batch commits
            # make healthy work look flat between ticks). PENDING = its turn
            # has not come (nothing landed, nothing running). STALLED =
            # partial progress and nothing working it.
            worked = any(s in ps for s in PROC_SIG.get((phase, src), ()))
            # ⚠ CAUGHT UP ≠ COMPLETE ≠ STALLED (login 2026-08-22: "when it
            # eventually has to wait on acqs then that just means pending
            # not necessarily stalled"). A FOLLOWER phase's denominator is
            # its upstream's output, which is still growing: when it has
            # keyed everything keyable it is PENDING (waiting on evidence),
            # and it is only COMPLETE once the upstream itself is.
            up = None   # organization retired 2026-08-23 - keying is
            # pass 1 (lockstep row), pass 2/3 (gated rows); no follower
            # phase remains that waits on an upstream
            if up and landed >= needed:
                u = rows.get((up, src))
                if not (u and u[0] >= u[1] and u[1] > 0):
                    con.execute(
                        "INSERT OR REPLACE INTO update_board VALUES"
                        " (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (phase, src,
                         round(rate_now, 2), d, round(pct_i, 3), "waiting",
                         round(rate, 2), d, round(pct_i, 3), "waiting on acq",
                         landed, needed, round(pct_t, 2), "PENDING", win))
                    lines.append(
                        f"UPDATE {phase:<15} | {src:<9} | {win}"
                        f" | now {rate_now:5.1f}/s | avg {rate:5.1f}/s | +{d:>7,} {pct_i:+7.2f}%"
                        f" | {landed:>10,} / {needed:>10,} = {pct_t:6.2f}%"
                        f" | ETA waiting on acq | PENDING")
                    continue
            if landed >= needed:
                # needed == 0 is a MEASURED nothing-owed (a zero-delta sync
                # run), not an absence - nothing owed IS complete
                status = "COMPLETE"
            elif worked and d == 0 and _lane_log_stale(phase, src, now):
                # ⚠ THE 20-MINUTE BLINDNESS (login 2026-08-23: "if it stops
                # working, we lose 20 minutes"). A hung-but-ALIVE lane keeps
                # its process (worked=True) so it read ACTIVE while the rate
                # decayed for a full window. The lanes print PROGRESS about
                # once a minute, so a lane log untouched for 3+ minutes with
                # its process still present is WEDGED - visible here within
                # ~3 min instead of 20. Log MTIME only: zero queries, and a
                # busy lane that simply had a flat tick (d==0 from commit
                # batching) still has a fresh log, so it stays ACTIVE.
                status = "STALLED"
            elif worked:
                status = "ACTIVE"
            elif d > 0:
                # ⚠ AN INCREASE WITHOUT A PROCESS IS NOT "ACTIVE". Login
                # 2026-08-23, minutes after pausing the pdf lanes: "the status
                # should reflect it not say its active if paused." The old
                # `worked or d > 0` let a freshly-paused lane coast on the
                # window's residual increase and read ACTIVE for a full
                # window. Landed-but-nobody-working is the STALLED definition
                # ("partial progress, no process") - unless the increase came
                # from a trigger riding another lane, which the LOCKSTEP rows
                # already represent.
                status = "STALLED"
            elif landed > 0:
                status = "STALLED"
            else:
                status = "PENDING"
            # ⚠ DENOMINATOR IS NEEDED, NOT LANDED (login 2026-08-23: "the pct
            # increase should be the increase amounts percentage relative to
            # the needed"). Against landed it described growth relative to
            # work already done - compounding, so the same increase read
            # smaller as the phase progressed. Against needed it is a fixed
            # denominator: pct_increase and pct_of_total finally share a
            # ruler, and this window's increase IS the pct_of_total delta.
            pct_i = d / needed * 100 if needed else 0.0
            pct_t = landed / needed * 100 if needed else 0.0
            # as_of = freshness stamp + THE WINDOW THE NUMBERS DESCRIBE.
            # Login 2026-08-23: "not knowing its context of how much in a
            # given time frame makes it hard" - a bare stamp forced the
            # reader to already know that rate/increase are a trailing
            # ~20-min measure. Say it in the row itself: `increase` is docs
            # in the last N min, rate = that / the window's seconds. The
            # span right after a (re)start is shorter than 20m until the
            # history refills; the label states the design window.
            win = ("as of " + time.strftime("%B %d, %Y %I:%M %p",
                                            time.localtime(now))
                   .replace(" 0", " ")
                   + " · now=60s · window=%dm" % (RATE_WINDOW // 60))
            # ⚠ AN ETA MUST EXTRAPOLATE THE RATE THAT CLOSES *THIS* GAP.
            # organization's rate is dominated by the key_on_rd TRIGGER,
            # which keys each row as rd lands it - so that component arrives
            # WITH new work and never touches the backlog. Feeding it to
            # eta_of claimed acris org would catch up in 23.6 h when riding
            # the trigger alone it never catches up at all: the gap sits
            # frozen at ~6.0M and the phase tops out near 72%. Only BACKFILL
            # keys close it, so only their rate may date it. Same family as
            # the pct_increase trap above - a rate against the wrong
            # denominator is not a slow answer, it is a false one.
            # ⚠ RATES FROM THE LANES' OWN COUNTERS wherever they publish
            # them (login: "numbers seem all over the place... tied with the
            # result the python is coding into the db"). One sample per pass,
            # 60s and 300s deltas over OUR OWN timestamps; a counter DROP is
            # a lane restart -> start the history over, never negative work.
            cum = _lane_cum(phase, src, st)
            if cum is not None:
                ck = "cum|" + key
                ch = [x for x in st["hist"].get(ck, []) if now - x[0] <= 420]
                if ch and cum < ch[-1][1]:
                    ch = []
                ch.append([now, cum])
                st["hist"][ck] = ch
                s60 = [x for x in ch if now - x[0] >= 55]
                s300 = [x for x in ch if now - x[0] >= 290]
                if s60:
                    t0, c0 = s60[-1]
                    d_now = cum - c0
                    # counters land in ~60s lumps; an unlucky alignment gives
                    # a genuine 0-delta minute -> 0.0/s with +0, CONSISTENT
                    rate_now = d_now / (now - t0)
                    pct_n = d_now / needed * 100 if needed else 0.0
                else:
                    rate_now, d_now, pct_n = 0.0, 0, 0.0
                if s300:
                    t0, c0 = s300[-1]
                    d = cum - c0
                    rate = d / (now - t0)
                    pct_i = d / needed * 100 if needed else 0.0
                elif len(ch) > 1 and not s60:
                    # young history: show the real span we have, both kits
                    t0, c0 = ch[0]
                    if now - t0 >= MIN_SPAN:
                        d_now = d = cum - c0
                        rate_now = rate = d / (now - t0)
                        pct_n = pct_i = d / needed * 100 if needed else 0.0
            eta = eta_of(landed, needed, rate)
            eta_now = eta_of(landed, needed, rate_now)
            # ⚠ COUNTER LANES KEEP THE COUNTER'S OWN PAIR. This line used to
            # run unconditionally and OVERWROTE d_now with the anchored-landed
            # difference - near-zero between anchor re-measures - while
            # rate_now kept the counter value: 5.42/s with +0 on the board
            # (login, 8:07 PM). Rate and increase must come from the SAME
            # subtraction or they can contradict each other.
            if cum is None:
                # increase_now mirrors rate_now's own span; same fallback rule
                d_now = (landed - recent[0][1]) if len(recent) > 1 else d
                pct_n = d_now / needed * 100 if needed else 0.0
            # FOUR STATUSES ONLY (login 2026-08-23): COMPLETE - ACTIVE -
            # PENDING (deliberately waiting: parked lanes, gated passes) -
            # STALLED (an unexpected break). Parked wins over everything
            # but COMPLETE: a paused lane is a decision, not a defect.
            # parked accepts "phase" (all sources) or "phase|source" (one
            # lane) - added 2026-08-24 when acris pdf was deliberately
            # paused for the rd sprint while richmond pdf ran on: phase-
            # level parking would have wrongly marked richmond PENDING.
            _parked = c.get("parked", [])
            if ((phase in _parked or "%s|%s" % (phase, src) in _parked)
                    and status != "COMPLETE"):
                status = "PENDING"
                eta = eta_now = "paused"
                # and the rates read 0.0: the anchored lane-rate is a span
                # that can straddle the pause (login saw 1.26/s on a lane
                # paused for 20 min). A paused lane spends nothing.
                rate = rate_now = 0.0
                d = d_now = 0
                pct_i = pct_n = 0.0
            con.execute("INSERT OR REPLACE INTO update_board VALUES"
                        " (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (phase, src,
                         round(rate_now, 2), d_now, round(pct_n, 3), eta_now,
                         round(rate, 2), d, round(pct_i, 3), eta,
                         landed, needed, round(pct_t, 2), status, win))
            lines.append(
                f"UPDATE {phase:<15} | {src:<9} | {win}"
                f" | now {rate_now:5.1f}/s +{d_now:,} {pct_n:+.3f}% eta {eta_now}"
                f" | 5m {rate:5.1f}/s +{d:,} {pct_i:+.3f}% eta {eta}"
                f" | {landed:>10,} / {needed:>10,} = {pct_t:6.2f}% | {status}")
        # ── THE THREE KEYING ROWS (login 2026-08-23: "no more organization
        # phase, just keying as part of the natural progression of rd under
        # pass 1... pass 2 and 3 havent happened yet so they await") ─────────
        # ⚠ PASS 1 COUNTS NOTHING. key_on_rd keys IN THE SAME TRANSACTION as
        # every rd landing, so keyed ≡ rd-landed BY CONSTRUCTION - the row
        # copies acquisition rd's numbers outright and exists to make the
        # attachment visible. Counting it separately would be a scan to
        # re-learn an identity. Verified 2026-08-23 by full scan: 15,432,975
        # rd rows, 0 unkeyed (parcel 94.62%, pdf-pass 830,014, reference 76).
        con.execute("DELETE FROM update_board WHERE phase='keying pass 1'"
                    " AND source!='all'")
        k = con.execute(
            "SELECT SUM(rate_now), SUM(increase_now), SUM(rate),"
            " SUM(increase), SUM(landed), SUM(needed)"
            " FROM update_board WHERE phase='acquisition rd'").fetchone()
        kstats = [r[0] for r in con.execute(
            "SELECT status FROM update_board WHERE phase='acquisition rd'")]
        if k and k[5]:
            krn, kdn, kr, kd, kl, kn = (x or 0 for x in k)
            con.execute(
                "INSERT OR REPLACE INTO update_board VALUES"
                " (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("keying pass 1", "all",
                 round(krn, 2), kdn, round(kdn / kn * 100, 3),
                 eta_of(kl, kn, krn),
                 round(kr, 2), kd, round(kd / kn * 100, 3),
                 eta_of(kl, kn, kr),
                 kl, kn, round(kl / kn * 100, 2),
                 # ⚠ NEVER HARDCODED (login 2026-08-23: "make sure you arent
                 # hardcoding") - pass 1 RIDES rd, so its status IS rd's:
                 # any rd source ACTIVE -> keys are landing -> ACTIVE;
                 # rd stalled -> keys stalled; rd all complete -> COMPLETE;
                 # rd deliberately paused -> the keys wait too -> PENDING.
                 ("COMPLETE" if kl >= kn else
                  ("ACTIVE" if "ACTIVE" in kstats else
                   ("STALLED" if "STALLED" in kstats else "PENDING"))), win))
        # ⚠ PASSES 2/3 AWAIT THEIR GATES (pass 2 = rd 100%, pass 3 = pdf
        # 100%). `needed` is the pdf-pass pool ANCHORED by the 2026-08-23
        # verify scan - an accounted figure; the pass itself re-measures.
        for kphase, gate in (("keying pass 2", "at rd 100%"),
                             ("keying pass 3", "at pdf 100%")):
            con.execute("INSERT OR REPLACE INTO update_board VALUES"
                        " (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (kphase, "all", 0.0, 0, 0.0, gate,
                         0.0, 0, 0.0, gate,
                         0, 830014, 0.0, "PENDING", win))
        # the board drops only UNKNOWN phases (schema leftovers - login:
        # "still have the rows I dont want"). A KNOWN phase outside `show`
        # keeps its row: phase routines write their rows as they run, and
        # showing them later is a config flip, not a recompute.
        known = list(c.get("cadence", {}).keys()) or show
        if known:
            con.execute("DELETE FROM update_board WHERE phase NOT IN (%s)"
                        % ",".join("?" * len(known)), known)
        con.commit()
        STATE.write_text(json.dumps(st))
        if lines:
            print("\n".join(lines), flush=True)
        if not loop:
            break
        time.sleep(60)                        # loop tick; cadence gates rows


main("--loop" in sys.argv)
