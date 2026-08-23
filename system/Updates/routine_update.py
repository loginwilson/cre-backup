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
    ACTIVE       increased since the last pass
    PENDING      a process is working for this row but nothing landed yet
    STALLED      partial progress, no process, not parked
    NOT STARTED  nothing landed, no process
    PARKED       deliberately off (declared in updates_config.json)

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
RATE_WINDOW = 20 * 60
# ⚠ NOW_WINDOW MUST EXCEED MIN_SPAN OR `rate_now` CAN NEVER FIRE. They were
# both 180 s, so the recent slice could never span MORE than the minimum it
# had to clear - with samples 60 s apart the oldest one inside the window sits
# ~120 s back, fails the guard, and rate_now silently copied the lifetime avg
# every pass. The board printed "now 6.6/s | avg 6.6/s" forever and looked
# frozen while landed climbed steadily (login 2026-08-22: "the rate and rate
# now arent different"). A window and its own minimum are not the same number.
NOW_WINDOW = 5 * 60        # the "what is it doing right now" window
# ⚠ NEVER DIVIDE BY A GAP SHORTER THAN THE SOURCE'S OWN UPDATE INTERVAL.
# Lane logs arrive in lumps ~60s apart, so a sample pair 11s apart divides
# a whole minute of work by 11s: on the 2026-08-22 daemon restart that
# published acris rd at 295.68 docs/s, more than 2x a ceiling we had
# MEASURED at ~138. It decayed to 64.5 over three passes as the window
# filled - but a spike that corrects itself is still a spike that got
# published. Below MIN_SPAN there is no rate yet, and saying so beats
# inventing one.
MIN_SPAN = 3 * 60
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
DDL = """CREATE TABLE IF NOT EXISTS update_board (
    phase TEXT NOT NULL, source TEXT NOT NULL,
    rate_now REAL, rate REAL, increase INTEGER, pct_increase REAL,
    landed INTEGER, needed INTEGER, pct_of_total REAL,
    eta TEXT,
    status TEXT, as_of TEXT,
    PRIMARY KEY (phase, source))"""


def eta_of(landed, needed, rate):
    """Time left, extrapolated from THIS row's own measured metrics (login
    2026-08-22: "eta should work arithmetics on the rate relative to its
    landed/needed as a percentage to extrapolate time left").

        share of the whole gained per window = increase / needed
        windows left = (1 - landed/needed) / that share
        time left    = windows left x window length   ==   remaining / rate

    Both forms are the same number; the code uses remaining/rate because
    rate already carries the window. ⚠ DO NOT extrapolate from the
    pct_increase COLUMN: its denominator is LANDED, not needed, so it
    describes growth relative to work already done - using it would model
    compounding and shrink every ETA as the phase progresses. Percentages
    only extrapolate honestly against a FIXED denominator.

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
    ("acquisition pdf", "richmond"): ("rc_feed.py", "rc_pdf_land.py",
                                      "rc_pdf_pull.py"),
    ("organization", "acris"): ("nav_key.py --src acris",),
    ("organization", "richmond"): ("nav_key.py --src rc",),
}


def cfg():
    try:
        return json.loads(CONF.read_text(encoding="utf-8"))
    except Exception:
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
        rows = {r[0]: r for r in con.execute(
            "SELECT source, system_total, source_total, delta,"
            " COALESCE(doc_ids,'') FROM synchronization s"
            " WHERE source != 'TOTAL' AND run_at ="
            " (SELECT MAX(run_at) FROM synchronization"
            "  WHERE source = s.source)")}
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
            if (phase, src) in ANCHORED and LANE_RATE.get((phase, src)):
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
            if (phase, src) in ANCHORED and LANE_RATE.get((phase, src)):
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
            up = {"organization": "acquisition rd"}.get(phase)
            if up and landed >= needed:
                u = rows.get((up, src))
                if not (u and u[0] >= u[1] and u[1] > 0):
                    con.execute(
                        "INSERT OR REPLACE INTO update_board VALUES"
                        " (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (phase, src, round(rate_now, 2), round(rate, 2),
                         d, round(pct_i, 3),
                         landed, needed, round(pct_t, 2),
                         "waiting on acq", "PENDING", win))
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
            elif worked or d > 0:
                status = "ACTIVE"
                # ⚠ ACTIVE CANNOT DISTINGUISH "a process is spending the
                # machine on this" from "a trigger rides another phase's
                # writes for free" - and the login read the difference as
                # a leak ("organization still looks like its running" -
                # 2026-08-22, minutes after pausing the keyer so ALL power
                # went to the acqs). Organization moving with NO keyer
                # process is the key_on_rd trigger keying inside rd's own
                # transaction: zero cost, nothing to pause. Name that state
                # TRIGGER so a fleet-watcher never has to wonder whether
                # the pause took.
                if phase == "organization" and not worked:
                    status = "TRIGGER"
                    # ⚠ AND THE RATE READS 0.0, NOT rd's (login 2026-08-22:
                    # "organization still shows a rate even though it should
                    # be 0 and paused"). The rate column's unit is WORK BEING
                    # SPENT on the row; trigger keys ride rd's transaction,
                    # so their spend is already displayed as rd's own rate -
                    # printing it here a second time double-displays one
                    # stream of work and reads as an unpaused process.
                    # Movement stays visible where it belongs: increase and
                    # landed keep climbing, ETA already extrapolates only
                    # backfill keys.
                    rate = rate_now = 0.0
            elif landed > 0:
                status = "STALLED"
            else:
                status = "PENDING"
            pct_i = d / was * 100 if was else 0.0
            pct_t = landed / needed * 100 if needed else 0.0
            # as_of = plain freshness stamp (rate/increase carry their own
            # ~20-min window). If this goes stale, the daemon is dead.
            win = ("as of " + time.strftime("%B %d, %Y %I:%M %p",
                                            time.localtime(now))
                   .replace(" 0", " "))
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
            if phase == "organization":
                bkey = f"orgfill|{src}"
                bf = ORG_BACKFILL.get(src, 0)
                bh = [s for s in st["hist"].get(bkey, [])
                      if now - s[0] <= RATE_WINDOW] + [[now, bf]]
                if len(bh) > 1 and bf < bh[-2][1]:
                    bh = [[now, bf]]
                st["hist"][bkey] = bh
                bspan = now - bh[0][0]
                eta = eta_of(landed, needed,
                             (bf - bh[0][1]) / bspan
                             if bspan >= MIN_SPAN else 0.0)
            else:
                eta = eta_of(landed, needed, rate)
            con.execute("INSERT OR REPLACE INTO update_board VALUES"
                        " (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (phase, src, round(rate_now, 2), round(rate, 2),
                         d, round(pct_i, 3),
                         landed, needed, round(pct_t, 2), eta, status, win))
            lines.append(
                f"UPDATE {phase:<15} | {src:<9} | {win}"
                f" | now {rate_now:5.1f}/s | avg {rate:5.1f}/s | +{d:>7,} {pct_i:+7.2f}%"
                f" | {landed:>10,} / {needed:>10,} = {pct_t:6.2f}%"
                f" | ETA {eta:>9} | {status}")
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
