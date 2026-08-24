"""THE CONSOLIDATED ACRIS LANE — one process, one access point, one workflow.

    python acris_lane.py --apply --workers 28        # the real thing

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
stats = {"done": 0, "fail": 0}
ua = {"User-Agent": fetch_pages.UA}

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
            break
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


def worker():
    while not stop_workers.is_set():
        try:
            did = q.get(timeout=5)
        except queue.Empty:
            continue
        if did is None:
            q.put(None)
            return
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


say("acris_lane up · ONE access point · %d workers + edge every %ds ·"
    " apply=%s" % (a.workers, a.every, a.apply))
threads = [threading.Thread(target=edge_thread, daemon=True),
           threading.Thread(target=feeder, daemon=True)]
threads += [threading.Thread(target=worker, daemon=True)
            for _ in range(a.workers)]
t0 = time.time()
for t in threads:
    t.start()
try:
    while True:
        time.sleep(60)
        flush()
        el = (time.time() - t0) / 60
        with lock:
            d, f = stats["done"], stats["fail"]
        say("  PROGRESS %s total · %.1f docs/s · %d fail · %.0f min%s"
            % ("{:,}".format(d), d / (el * 60) if el else 0.0, f, el,
               " · WORKERS STOPPED (refusal)" if stop_workers.is_set()
               else ""))
except KeyboardInterrupt:
    stop_workers.set()
    flush()
    say("stopped · %s landed" % "{:,}".format(stats["done"]))
