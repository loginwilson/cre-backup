"""THE CONSOLIDATED ACRIS LANE — one process, one access point, one workflow.

    python acris_lane.py --apply --workers 28        # the real thing

⚠⚠ THE RAMP LAW — NEVER COLD-LAUNCH THIS LANE (login, 2026-08-24 13:03):
"you cant cold launch the code... it needs to ramp and not just restart at
80 or whatever." A restart that fires every worker at once opens ~80 cold
TLS connections in one second - ACRIS served its Bandwidth Notice ONE
SECOND after exactly such a relaunch (trip #3), after absorbing the
governor's gentle climb to width 52 all morning without complaint. The
ramp is CODED AS UNAVOIDABLE below (pdf width always starts at RAMP_START
and climbs; rd workers stagger 0.5s apart) - do not add any launch path
that bypasses it, and treat every restart as a load event to be minimized
(width/tuning changes belong to the governor, not to relaunches).

Login's design (2026-08-24, docs/sources/acris/LIVE_SYNC.md "THE CONSOLIDATED
LANE"): ACRIS tripped its Bandwidth Notice twice while the edge-prober
(acris_live) and the doc-walkers (rd_walk x4) ran as SEPARATE python
processes - two behaviors under one IP. The theory (login's): ACRIS tolerates
ONE access point that maximizes workers, not multiple access points. So this
file IS the acris presence: the edge probe, the rd backfill, the ledger, and
the edge state all live in one process. When this runs, NOTHING ELSE may
touch ACRIS (acris_live and rd_walk must be stopped - it replaces them).

THE ROTATION (login: "constantly doing the rd, but every 10 seconds subbing
in the edge"): workers drain the backfill continuously; an edge thread runs
the probe every --every seconds. A probe hit IS the document - detection and
rd arrive in the same request (nothing to queue; the landing is a local
write and key_on_rd keys it in the same transaction). Only the pdf ever
queues, and that lane is parked separately. Bursts: the probe walks until
blanks + control re-prove level (the acris_live walk, unchanged).

REFUSAL DISCIPLINE: every fetch path catches BOTH fetch_pages.AccessDenied
and live_delta.Refused (the 09:00 lesson - a detector that fires into the
wrong except clause does not exist). On refusal the WORKERS stop for good;
the edge probe alone continues on exponential backoff as the resume
detector. Backfill resume after a refusal is LOGIN'S CALL (restart the
lane), never automatic - "resume another day" is the notice's own text.

Board: PROGRESS lines print "N total" like rd_walk's, so routine_update's
counter/heartbeat read this log (NAV_WORK\\acris_lane.log via redirect).

THE PDF POOL (login 2026-08-24: "build pdf into it too... one eta one code
that eventually results in the level ready to decode"): a third organ in the
same process - workers drain `pdf='' AND recorded_details!=''` through
acris_pdf.fetch_pdf (image_walk's body with every trap intact), and every
sync landing jumps the queue via the hot list so a new filing is fully
ready minutes after recording. Same access point, same refusal tripwire:
a notice on EITHER endpoint stops ALL workers, rd and pdf alike.

⚠ THE FRESHNESS CLAUSE (login: "a new doc id from the edge walk may very
well miss its image... the lag distribution"): TotalPages<=0 on a doc
recorded within --fresh-days is NOT an imageless verdict - the scan may
simply not be uploaded yet. Those are DEFERRED (pdf stays '', retried when
the feeder wraps), and only aged docs earn `pdf='imageless'`. A permanent
verdict must never be written on a temporary state.

READY TO DECODE = rd + (pdf|imageless) + key. Because pdf only ever follows
rd, ready = needed - pdf_todo exactly (ix_nav_pdf_todo, index-only), and
the board's synchronization row measures distance to a fully synchronized,
decode-ready mirror. That is the one rate and the one eta.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import queue
import re
import sqlite3
import sys
import threading
import time
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import acris_edge as AE                                        # noqa: E402
import acris_pdf as AP                                         # noqa: E402
import corpus_paths as CP                                      # noqa: E402
import fetch_pages                                             # noqa: E402
import live_delta as LD                                        # noqa: E402
import rd_parse as RD                                          # noqa: E402

EDGE_STATE = HERE / "_crfn_edge.json"
LEDGER_DB = (r"D:\CRE Decoding System\00 Synchronizations"
             r"\Legal Instruments Synchronization"
             r"\Legal Instruments Synchronization.db")
ACRIS_URL = "https://a836-acris.nyc.gov/DS/DocumentSearch/"
CONFIRM_BLANKS = 8
FAILS = CP.NAV_WORK / "acris_lane_fails.jsonl"
BATCH = 200

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--workers", type=int, default=28)
ap.add_argument("--pdf-workers", type=int, default=12)   # STARTING width
ap.add_argument("--pdf-max", type=int, default=48)       # governor's ceiling
ap.add_argument("--step-minutes", type=int, default=10,
                help="clean minutes a width must hold before +2 (login"
                     " 2026-08-24: 10-min windows 'to truly see if things"
                     " degrade or recover stronger' - 5 was too thin to"
                     " separate a ceiling bend from a heavy-doc patch)")
ap.add_argument("--fresh-days", type=int, default=30)
ap.add_argument("--every", type=int, default=10)
ap.add_argument("--control-every", type=int, default=60)
ap.add_argument("--deep-every", type=int, default=300)
ap.add_argument("--max", type=int, default=500)
ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()

REFUSALS = (fetch_pages.AccessDenied, LD.Refused)

stop_workers = threading.Event()     # refusal or shutdown: backfill halts
lock = threading.Lock()
q: queue.Queue = queue.Queue(maxsize=20_000)
pdf_q: queue.Queue = queue.Queue(maxsize=20_000)
pdf_hot: queue.Queue = queue.Queue()   # sync landings jump the pdf queue
stats = {"done": 0, "fail": 0,
         "pdfs": 0, "imageless": 0, "deferred": 0, "pdf_fail": 0,
         "shed": 0}          # Short/timeout = the server's load signal
pdf_width = [0]              # live width, governed; workers idle above it
rd_all_fed = threading.Event()   # rd feeder exhausted the todo set
ua = {"User-Agent": fetch_pages.UA}
PDF_FAILS = CP.NAV_WORK / "acris_lane_pdf_fails.jsonl"
PDF_BATCH = 25


def _quarantine(path, n=3):
    """ids that failed >=n times = server-side defects (login: "any defect
    should be cleaned up for maximal performance"). Skipped on sight so they
    stop costing fetches - but their columns STAY EMPTY (todo state) for a
    later adjudication pass. Never a fake verdict to make a row look done."""
    try:
        c = {}
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                i = json.loads(ln)["id"]
            except Exception:
                continue
            c[i] = c.get(i, 0) + 1
        return {i for i, k in c.items() if k >= n}
    except OSError:
        return set()


QUAR_RD = _quarantine(FAILS)
QUAR_PDF = _quarantine(PDF_FAILS)

con = sqlite3.connect(CP.NAV_DB, timeout=600, check_same_thread=False)
con.execute("PRAGMA journal_mode=WAL")
con.execute("PRAGMA busy_timeout=300000")


def say(m):
    print("%s  %s" % (time.strftime("%H:%M:%S"), m), flush=True)


def urls(did):
    return (ACRIS_URL + "DocumentDetail?doc_id=" + did,
            ACRIS_URL + "DocumentImageView?doc_id=" + did)


# ── EDGE (the sync half) — acris_live's proven machinery, verbatim logic ──

def read_edge():
    return int(json.loads(EDGE_STATE.read_text(encoding="utf-8"))["edge"])


def write_edge(n):
    st = json.loads(EDGE_STATE.read_text(encoding="utf-8"))
    st["edge"] = n
    st["watermark"] = n
    EDGE_STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


def land(rows):
    """INSERT empty then UPDATE rd, one transaction - key_on_rd is AFTER
    UPDATE OF recorded_details, so the order is what makes pass 1 fire."""
    ins = [(did, "", urls(did)[0], "", urls(did)[1], "", "")
           for _c, did, _r in rows]
    upd = [(rd, did) for _c, did, rd in rows if rd]
    for _try in range(120):
        try:
            with lock:
                con.executemany(
                    "INSERT OR IGNORE INTO navigation"
                    " (id, recorded_details, rd_url, pdf, pdf_url, keyed_by,"
                    " key) VALUES (?,?,?,?,?,?,?)", ins)
                con.executemany(
                    "UPDATE navigation SET recorded_details=?"
                    " WHERE id=? AND recorded_details=''", upd)
                con.commit()
            return
        except sqlite3.OperationalError:
            time.sleep(5)
    raise RuntimeError("write lock unavailable for 10 minutes")


def write_ledger(n_docs, ids):
    try:
        lg = sqlite3.connect(LEDGER_DB, timeout=60)
        try:
            prev = lg.execute(
                "SELECT system_total FROM synchronization"
                " WHERE source='acris' AND system_total > 0"
                " ORDER BY run_at DESC LIMIT 1").fetchone()
            sysn = (prev[0] if prev else 0) + n_docs
            lg.execute("INSERT OR REPLACE INTO synchronization"
                       " (run_at, source, system_total, source_total, delta,"
                       " doc_ids) VALUES (?,?,?,?,?,?)",
                       (time.strftime("%Y-%m-%d %H:%M"), "acris", sysn, sysn,
                        0, ";".join(ids)))
            lg.commit()
        finally:
            lg.close()
    except Exception as e:
        say("  ⚠ ledger write failed (%s) - rows ARE landed" % type(e).__name__)


_last_control = [0.0]
_last_deep = [0.0]


def control_ok(edge):
    if time.time() - _last_control[0] < a.control_every:
        return True
    state, _did = AE.quick_crfn(edge)
    if state == "live":
        _last_control[0] = time.time()
        return True
    return False


def edge_tick():
    """One sync pass: shallow probe, walk on hits, land + key + ledger.
    Returns (ok, landed, refused)."""
    edge = read_edge()
    deep = (time.time() - _last_deep[0]) >= a.deep_every
    limit = CONFIRM_BLANKS if deep else 1
    if deep:
        _last_deep[0] = time.time()
    found, blanks, n = [], 0, edge
    try:
        while blanks < limit and (n - edge) < a.max:
            n += 1
            state, did, html = AE.fetch(n)
            if state != "live":
                blanks += 1
                continue
            blanks = 0
            try:
                rec = json.dumps(RD.parse_acris(html), separators=(",", ":"))
            except Exception as e:
                say("  ⚠ rd parse failed for %s (%s) - landing rd='' for"
                    " the backfill to retry" % (did, type(e).__name__))
                rec = ""
            found.append((n, did, rec))
    except REFUSALS as e:
        say("  PROBE REFUSED: %.90s - nothing written" % e)
        return False, 0, True
    except Exception as e:
        code = getattr(e, "code", None)
        say("  PROBE UNPROVEN (%s%s: %.90s) - nothing written"
            % (type(e).__name__, " %d" % code if code else "", e))
        return False, 0, False
    if (n - edge) >= a.max:
        say("  ⚠ walked %d without %d blanks - run routine_synchronization"
            " (gallop+bisect). Nothing written." % (a.max, CONFIRM_BLANKS))
        return False, 0, False
    if not found:
        try:
            if not control_ok(edge):
                say("  CONTROL %d did not resolve - unproven" % edge)
                return False, 0, False
        except REFUSALS as e:
            say("  CONTROL REFUSED: %.60s" % e)
            return False, 0, True
        except Exception as e:
            say("  CONTROL errored (%s) - unproven" % type(e).__name__)
            return False, 0, False
        say("  level at crfn %d · %s walk, %d blank(s), control ok · %d req"
            % (edge, "DEEP" if deep else "shallow", blanks, n - edge))
        return True, 0, False
    if not a.apply:
        say("  would land %d (report-only)" % len(found))
        return True, 0, False
    land(found)
    write_edge(found[-1][0])
    write_ledger(len(found), [d for _c, d, _r in found])
    with lock:
        stats["done"] += len(found)
    # hot-list: a fresh filing's pdf is fetched NOW, not when the backfill
    # reaches it. Only rows whose rd parsed - pdf must follow rd, and a row
    # landed rd='' would break `ready = needed - pdf_todo` if pdf'd first.
    if a.pdf_workers > 0:
        for _c, did, rec in found:
            if rec:
                try:
                    pdf_hot.put((did, json.loads(rec).get("recorded", "")))
                except Exception:
                    pass
    say("  SYNC landed %d · rd in the SAME request · edge %d -> %d"
        % (len(found), edge, found[-1][0]))
    return True, len(found), False


def edge_thread():
    """The reservation: one probe per --every seconds forever, exponential
    backoff while unproven/refused. Outlives a worker stop - this is the
    resume detector."""
    fails = 0
    while True:
        ok, _landed, refused = edge_tick()
        if refused and not stop_workers.is_set():
            stop_workers.set()
            say("  ⚠ REFUSED - BACKFILL WORKERS STOPPED (probe continues on"
                " backoff; restart the lane to resume backfill: login's call)")
        if ok:
            fails = 0
            time.sleep(a.every)
        else:
            fails += 1
            hold = min(a.every * (2 ** min(fails, 7)), 900)
            say("  held after %d failure(s) - next attempt in %ds" %
                (fails, hold))
            time.sleep(hold)


# ── BACKFILL (the acq half) — rd_walk's machinery on the todo index ──

def feeder():
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    fed, cursor = 0, ""
    while not stop_workers.is_set():
        rows = read.execute(
            "SELECT id FROM navigation WHERE recorded_details = ''"
            " AND id > ? AND id NOT LIKE 'RC_%'"
            " ORDER BY id LIMIT 10000", (cursor,)).fetchall()
        if not rows:
            # drained: the governor reallocates rd's budget to pdf, and the
            # feeder WRAPS after a rest instead of exiting - error rows
            # (HTTPError voids, URLError blips) landed nothing, so the todo
            # index still owes them and each sweep re-attempts. Nothing is
            # ever missed, only delayed; the column is the ledger, not the
            # error log.
            rd_all_fed.set()
            time.sleep(600)
            cursor = ""
            continue
        cursor = rows[-1][0]
        for (did,) in rows:
            if stop_workers.is_set():
                return
            q.put(did)
            fed += 1
            if a.limit and fed >= a.limit:
                q.put(None)
                return
    q.put(None)


pend, pend_lock = [], threading.Lock()


def flush():
    with pend_lock:
        batch, pend[:] = pend[:], []
    if not batch:
        return
    for _try in range(120):
        try:
            with lock:
                con.executemany(
                    "UPDATE navigation SET recorded_details=? WHERE id=?",
                    batch)
                con.commit()
            return
        except sqlite3.OperationalError:
            time.sleep(5)
    with pend_lock:
        pend[:0] = batch


def worker(idx=0):
    time.sleep(idx * 0.5)        # stagger cold starts - never a stampede
    while not stop_workers.is_set():
        try:
            did = q.get(timeout=5)
        except queue.Empty:
            continue
        if did is None:
            q.put(None)
            return
        if did in QUAR_RD:
            continue
        try:
            req = urllib.request.Request(
                LD.BASE + "/DS/DocumentSearch/DocumentDetail?doc_id=" + did,
                headers={**ua, "Referer": LD.BASE + "/DS/DocumentSearch/"})
            with urllib.request.urlopen(req, timeout=90) as r:
                html = RD.clean_html(r.read().decode("utf-8", "replace"))
            LD.check_refused(html)
            flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
            if not re.search(r"DOCUMENT ID:\s*" + re.escape(did), flat):
                raise ValueError("page does not echo id")
            rec = RD.parse_acris(html)
            rec["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            with pend_lock:
                pend.append((json.dumps(rec, separators=(",", ":")), did))
                n = len(pend)
            if n >= BATCH:
                flush()
            with lock:
                stats["done"] += 1
        except REFUSALS as e:
            if not stop_workers.is_set():
                stop_workers.set()
                say("  REFUSED at %s - BACKFILL WORKERS STOPPED: %.90s"
                    % (did, e))
        except Exception as e:
            with lock:
                stats["fail"] += 1
            with FAILS.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"id": did,
                                     "err": type(e).__name__}) + "\n")


# ── PDF POOL (the image half) — acris_pdf's recipe on the pdf todo set ──

ppend, ppend_lock = [], threading.Lock()


def pdf_flush():
    with ppend_lock:
        batch, ppend[:] = ppend[:], []
    if not batch:
        return
    for _try in range(120):
        try:
            with lock:
                con.executemany(
                    "UPDATE navigation SET pdf=? WHERE id=? AND pdf=''",
                    batch)
                con.commit()
            return
        except sqlite3.OperationalError:
            time.sleep(5)
    with ppend_lock:
        ppend[:0] = batch


def pdf_feeder():
    """image_walk's trailing feeder: pdf follows rd through the same id
    order. When it runs dry it WRAPS to '' after a rest - that sweep is what
    retries deferred fresh docs and Short failures left behind the cursor."""
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    cursor = ""
    while not stop_workers.is_set():
        rows = read.execute(
            "SELECT id, json_extract(recorded_details, '$.recorded')"
            " FROM navigation WHERE pdf = ''"
            " AND recorded_details != ''"
            " AND id > ? AND id NOT LIKE 'RC_%'"
            " ORDER BY id LIMIT 5000", (cursor,)).fetchall()
        if not rows:
            time.sleep(600)
            cursor = ""
            continue
        cursor = rows[-1][0]
        for did, rec_date in rows:
            if stop_workers.is_set():
                return
            pdf_q.put((did, rec_date or ""))


def _fresh(rec_date):
    """Recorded within --fresh-days. On these, TotalPages<=0 means 'scan not
    uploaded yet' (the lag distribution), never an imageless verdict."""
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", rec_date or "")
    if not m:
        return False
    try:
        t = time.mktime((int(m.group(3)), int(m.group(1)), int(m.group(2)),
                         0, 0, 0, 0, 0, -1))
    except (ValueError, OverflowError):
        return False
    return (time.time() - t) < a.fresh_days * 86400


def pdf_worker(idx):
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    while not stop_workers.is_set():
        if idx >= pdf_width[0]:      # governed: idle above the live width
            time.sleep(5)
            continue
        try:
            item = pdf_hot.get_nowait()
        except queue.Empty:
            try:
                item = pdf_q.get(timeout=5)
            except queue.Empty:
                continue
        did, rec_date = item
        if did in QUAR_PDF:
            continue
        try:
            row = read.execute("SELECT pdf FROM navigation WHERE id=?",
                               (did,)).fetchone()
            if row is None or row[0]:
                continue           # landed already (hot/wrap overlap)
            st, val = AP.fetch_pdf(did, rec_date)
            if st == "imageless" and _fresh(rec_date):
                with lock:
                    stats["deferred"] += 1
                continue           # scan lag, not a verdict - wrap retries
            with ppend_lock:
                ppend.append((val, did))
                n = len(ppend)
            with lock:
                stats["pdfs" if st == "pdf" else "imageless"] += 1
            if n >= PDF_BATCH:
                pdf_flush()
        except REFUSALS as e:
            if not stop_workers.is_set():
                stop_workers.set()
                say("  PDF REFUSED at %s - ALL WORKERS STOPPED: %.90s"
                    % (did, e))
        except Exception as e:
            kind = type(e).__name__
            with lock:
                stats["pdf_fail"] += 1
                # THE SERVER'S EVERY DIALECT OF "SLOW DOWN" counts as shed
                # (2026-08-24 11:03: at width 22 the pushback arrived as
                # "connection forcibly closed"/SSL EOF/RemoteDisconnected -
                # NOT Shorts - and the governor climbed blind to it). HTTP
                # 400 stays an ordinary per-doc fail.
                msg = str(e)
                if (kind in ("Short", "TimeoutError", "RemoteDisconnected",
                             "IncompleteRead")
                        or "timed out" in msg or "10054" in msg
                        or "10060" in msg or "UNEXPECTED_EOF" in msg
                        or "forcibly closed" in msg):
                    stats["shed"] += 1
            with PDF_FAILS.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"id": did, "err": kind,
                                     "msg": str(e)[:120]}) + "\n")


def governor():
    """THE RAMP THAT KEEPS THE PHILOSOPHY (login 2026-08-24: "figure out
    where ramp up can happen without killing the philosophy... the
    intelligence needs to know once rd backfill finishes that it can
    allocate more resources to the pdf and live sync").

    One rule set, applied every minute:
      - the server's shed signal (Short/timeout) is OBEYED, never pushed
        through: a shedding minute steps width DOWN 25% and holds 10 min
      - 5 consecutive clean minutes EARN +2 width, up to --pdf-max
      - rd backfill draining hands its budget over: +8 width immediately
        (the reallocation login asked for - same server, freed tonnage)
      - a refusal is above this governor's pay grade: stop_workers stills
        everything and only the probe continues (unchanged)."""
    streak, hold, last = 0, 0, {"shed": 0, "pdfs": 0, "imageless": 0}
    rd_handed = False
    # per-width measurement: settled average over the width's WHOLE window,
    # announced at every transition - the ceiling shows as this number
    # flattening (or falling) across steps while minutes stay clean
    win_t0, win_c0 = time.time(), 0

    def settle(w):
        with lock:
            c = stats["pdfs"] + stats["imageless"]
        el = time.time() - win_t0
        return ("width %d averaged %.2f ready/s over %.1f min"
                % (w, (c - win_c0) / el if el else 0.0, el / 60)), c

    while not stop_workers.is_set():
        time.sleep(60)
        with lock:
            s = dict(stats)
        shed = s["shed"] - last["shed"]
        landed = (s["pdfs"] + s["imageless"]
                  - last["pdfs"] - last["imageless"])
        last = s
        w = pdf_width[0]
        if rd_all_fed.is_set() and not rd_handed:
            rd_handed = True
            pdf_width[0] = min(w + 8, a.pdf_max)
            verdict, win_c0 = settle(w)
            win_t0 = time.time()
            say("  GOVERNOR rd backfill drained - budget reallocated,"
                " pdf width %d -> %d (%s)" % (w, pdf_width[0], verdict))
            streak = 0
            continue
        if shed >= 3:
            verdict, win_c0 = settle(w)
            win_t0 = time.time()
            pdf_width[0] = max(w * 3 // 4, 4)
            hold, streak = 10, 0
            say("  GOVERNOR server shedding (%d) - width %d -> %d,"
                " hold 10 min (%s)" % (shed, w, pdf_width[0], verdict))
        elif hold > 0:
            hold -= 1
        elif shed == 0 and landed > 0:
            streak += 1
            if streak >= a.step_minutes and w < a.pdf_max:
                verdict, win_c0 = settle(w)
                win_t0 = time.time()
                pdf_width[0] = min(w + 2, a.pdf_max)
                streak = 0
                say("  GOVERNOR %d clean minutes - width %d -> %d (%s)"
                    % (a.step_minutes, w, pdf_width[0], verdict))
        else:
            streak = 0


# ⚠ THE STAMPEDE LESSON (13:03:50, trip #3): a relaunch that opens 50+ cold
# connections in one instant is nothing like the governor's +2 ramp - ACRIS
# absorbed a gentle climb to 52 all day, then served the Bandwidth Notice
# the second a restart fired everything at once. Same physics as richmond's
# sess() stagger ("160 cold TLS opens in one instant = SSLError across the
# board"). So a launch RAMPS: width starts small and a warmup thread raises
# it +4 every 30s until the requested width, then the governor owns it.
RAMP_START, RAMP_STEP, RAMP_EVERY = 8, 4, 30
_target = min(a.pdf_workers, a.pdf_max)
pdf_width[0] = min(RAMP_START, _target)


def warmup_ramp():
    while pdf_width[0] < _target and not stop_workers.is_set():
        time.sleep(RAMP_EVERY)
        pdf_width[0] = min(pdf_width[0] + RAMP_STEP, _target)
    if not stop_workers.is_set():
        say("  RAMP complete - width %d, governor owns it" % pdf_width[0])
say("acris_lane up · ONE access point · %d rd + pdf width %d (governed,"
    " max %d) + edge every %ds · apply=%s · quarantined %d rd / %d pdf"
    % (a.workers, pdf_width[0], a.pdf_max, a.every, a.apply,
       len(QUAR_RD), len(QUAR_PDF)))
threads = [threading.Thread(target=edge_thread, daemon=True),
           threading.Thread(target=feeder, daemon=True)]
threads += [threading.Thread(target=worker, args=(i,), daemon=True)
            for i in range(a.workers)]
if a.apply and a.pdf_workers > 0:
    threads.append(threading.Thread(target=pdf_feeder, daemon=True))
    threads.append(threading.Thread(target=governor, daemon=True))
    threads.append(threading.Thread(target=warmup_ramp, daemon=True))
    threads += [threading.Thread(target=pdf_worker, args=(i,), daemon=True)
                for i in range(a.pdf_max)]
t0 = time.time()
for t in threads:
    t.start()
try:
    while True:
        time.sleep(60)
        flush()
        pdf_flush()
        el = (time.time() - t0) / 60
        with lock:
            s = dict(stats)
        say("  PROGRESS %s total · %.1f docs/s · %d fail · %.0f min%s"
            % ("{:,}".format(s["done"]),
               s["done"] / (el * 60) if el else 0.0, s["fail"], el,
               " · WORKERS STOPPED (refusal)" if stop_workers.is_set()
               else ""))
        if a.pdf_workers > 0:
            say("  PDF PROGRESS %s pdfs · %s imageless · %d deferred ·"
                " %d fail · width %d" % ("{:,}".format(s["pdfs"]),
                                         "{:,}".format(s["imageless"]),
                                         s["deferred"], s["pdf_fail"],
                                         pdf_width[0]))
except KeyboardInterrupt:
    stop_workers.set()
    flush()
    pdf_flush()
    say("stopped · %s landed" % "{:,}".format(stats["done"]))
