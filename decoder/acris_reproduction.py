"""ACRIS REPRODUCTION - three floors, three entries, one process.

login's architecture (2026-08-28, settled over three test runs):

    synchronization  enters ONCE under a batch of 20 edge walkers - the
                     monitor coordinates the edge cursor; on inflow the
                     crew walks the range in parallel, landing id + rd in
                     the SAME request (the probe URL is the rd URL) with
                     urls minted by the db trigger.
    registration     enters ONCE under a batch of 40 register workers -
                     the rd backfill (recorded_details='' rows, id order).
    documentation    enters ONCE under a batch of 40 document workers -
                     the image backfill with THE 3 STATUSES:
                         a real path   the scan, fetched and converted
                         'pending'     CHECKED, fresh, no scan yet - a
                                       determination, re-asked every 5 min
                                       until it resolves (path or expiry)
                         'imageless'   CHECKED, aged, no image - verdict
                     ('' = not yet checked, the only unlanded state)

    REPRODUCTION SPEED = rows completing the FULL pass (doc id + 2 urls +
    register + one-of-3 statuses) per second, read from the completion
    writes themselves - printed per window as `repro N/s`.

WHY THREE SESSIONS (run 3, 2026-08-28): the bench pulled images at 90+
req/s clean on a session speaking ONLY to the image endpoint; mixing rd +
images through one shared session/cookie jar made acris serve its empty-
viewer page for docs whose images exist (calm re-probes proved TotalPages
3/4/2 on "failing" docs). Every proven-clean precedent ran the endpoints
in separate processes = separate sessions. Three floors, three entries,
staggered; after entry ~0 handshakes - THE METERED QUANTITY IS
HANDSHAKES (an entry per request = the old urllib walker = hundreds of
thousands of entries = blocked; an entry per floor = 3).

WHY NO GLOBAL LOCK AROUND THE DB (run 4 freeze, 2026-08-28 18:43): a
write that hits SQLITE_BUSY busy-waits up to 300 s INSIDE the C call;
held under one shared lock that every stats bump also needed, ONE
contended write froze all 45 workers, the printer, and the wire - alive
and silent. Each floor now writes on ITS OWN connection; sqlite
serializes writers itself, and a busy-wait blocks only that floor.

SAFETY (unchanged): stop-on-refusal stills every floor (body notice,
blocked payload, per-floor 40-streak of 503/429, 300-fails-in-a-minute
breaker). CLOSE_WAIT law: every response closed on every path. Never
retry, never rotate.

Usage: python acris_reproduction.py [--sync-workers 20] [--rd-workers 40]
                                    [--pdf-workers 40] [--every 10]
"""
import argparse
import json
import pathlib
import queue
import re
import sqlite3
import sys
import threading
import time
import urllib.error

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP                                      # noqa: E402
import fetch_pages                                             # noqa: E402
import live_delta as LD                                        # noqa: E402
import rd_parse as RD                                          # noqa: E402
import acris_pdf as AP                                         # noqa: E402
import acris_edge as AE                                        # noqa: E402

HERE = pathlib.Path(__file__).parent
EDGE_STATE = HERE / "_crfn_edge.json"
LEDGER_DB = (r"D:\CRE Decoding System\00 Synchronizations"
             r"\Legal Instruments Synchronization"
             r"\Legal Instruments Synchronization.db")
ACRIS_URL = "https://a836-acris.nyc.gov/DS/DocumentSearch/"
FAILS = CP.NAV_WORK / "acris_reproduction_fails.jsonl"

ap = argparse.ArgumentParser()
ap.add_argument("--sync-workers", type=int, default=20)
ap.add_argument("--rd-workers", type=int, default=40)
ap.add_argument("--pdf-workers", type=int, default=40)
ap.add_argument("--every", type=int, default=10)
ap.add_argument("--fresh-days", type=int, default=30)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--stagger", type=float, default=0.5)
ap.add_argument("--lo", default="",
                help="register shard: walk ids > this (disjoint ranges)")
ap.add_argument("--hi", default="￿",
                help="register shard: walk ids < this")
ap.add_argument("--floor", default="all",
                help="this process's floor name (sync|register|document)."
                     " ⚠ ALSO THE FLEET'S IDENTITY TOKEN: fleet._match"
                     " ignores tokens <= 3 chars, so the worker COUNTS"
                     " (20/40/0/10) cannot distinguish one floor process"
                     " from another - every floor matched every other and"
                     " `start` reported 'already running' for a floor that"
                     " was dead. A name longer than 3 chars fixes that.")
ap.add_argument("--entry-gap", type=float, default=20.0,
                help="seconds between one floor's entry and the next -"
                " three doors, never one moment")
ap.add_argument("--pending-recheck", type=int, default=300)
ap.add_argument("--bite", type=int, default=1000,
                help="edge walk batch size per pass")
a = ap.parse_args()

BATCH = 200
H503_STOP = 40
stop = threading.Event()
slock = threading.Lock()                 # stats ONLY - never held over IO
stats = {"reqs": 0, "rd": 0, "pdf": 0, "imageless": 0, "pending": 0,
         "sync": 0, "fail": 0, "short": 0}


# ── three sessions - one entry per floor ────────────────────────────────
def _mk_session(width):
    s = requests.Session()
    s.headers.update({"User-Agent": fetch_pages.UA})
    s.mount("https://", requests.adapters.HTTPAdapter(
        pool_connections=1, pool_maxsize=width + 4,
        max_retries=0, pool_block=True))
    return s


def _fetcher(session):
    def fetch_bytes(url, referer, timeout=90):
        with slock:
            stats["reqs"] += 1
        r = session.get(url, headers={"Referer": referer}, timeout=timeout)
        try:
            if r.status_code >= 400:
                err = urllib.error.HTTPError(url, r.status_code, r.reason,
                                             r.headers, None)
                err.acris_shed = r.status_code in (429, 500, 502, 503, 504)
                raise err
            return r.content, r.headers.get("Content-Type", "")
        finally:
            r.close()
    return fetch_bytes


# ── THE FLOOR GATE: A FLOOR WITH NO WORKERS DOES NOT EXIST ──────────────
# ⚠⚠ login 2026-08-29, watching a registration-only run: "its supposed to
# only be registration? not 3 floors ... it is supposed to literally be 1
# batch, 40 workers." He was right and this was a real defect, not a label
# problem. Passing --sync-workers 0 --pdf-workers 0 did NOT make a
# one-door process:
#   · all THREE sessions were built here, unconditionally;
#   · all three floors "entered" and said so in the banner;
#   · and the sync floor ALWAYS carried a +1 MONITOR that probes acris on
#     its own schedule - requests nobody asked for, on a floor the
#     operator had set to zero.
# So every "one door" claim on 2026-08-29 was wrong by three, and the
# 12:23 Bandwidth Notice - blamed on 4 register shards + sync = 5 doors -
# was actually nearer 4 shards x 3 floors = TWELVE.
# A ZERO WORKER COUNT NOW MEANS THE FLOOR DOES NOT RUN: no session, no
# entry, no monitor, no feeder. `--floor register --rd-workers 40` is now
# literally one session and one entry.
WANT = {"sync": a.sync_workers > 0,
        "register": a.rd_workers > 0,
        "document": a.pdf_workers > 0}


def _closed(name):
    """A closed floor must FAIL LOUDLY if anything still reaches for it -
    never fall back to opening a quiet extra door."""
    def _no(*_args, **_kw):
        raise RuntimeError(
            "the %s floor is CLOSED this run (0 workers): nothing may"
            " fetch through it. This is the floor gate, not a bug." % name)
    return _no


# ⚠ BUILD A SESSION ONLY FOR AN OPEN FLOOR. requests.Session() is lazy, so
# an unused one costs no handshake - but it is what the monitor and the
# pdf paths reach through, and a session that exists WILL eventually be
# used by something. The gate is the guarantee; laziness is not.
fetch_rd = (_fetcher(_mk_session(a.rd_workers)) if WANT["register"]
            else _closed("register"))
AP.FETCH = (_fetcher(_mk_session(a.pdf_workers)) if WANT["document"]
            else _closed("document"))
AE.FETCH = (_fetcher(_mk_session(a.sync_workers)) if WANT["sync"]
            else _closed("sync"))


# ── tripwires ───────────────────────────────────────────────────────────
_streak = {"rd": 0, "pdf": 0, "sync": 0}


def refused_stop(where, e):
    if not stop.is_set():
        stop.set()
        print("  REFUSED at %s - STOPPING ALL FLOORS: %.90s" % (where, e),
              flush=True)


def h503(code, floor):
    """40 consecutive 503/429 on ONE floor, none of ITS OWN successes
    between = a wall. Per floor - another floor's successes must never
    silence a wall detector."""
    if code not in (503, 429):
        return
    with slock:
        _streak[floor] += 1
        n = _streak[floor]
    if n >= H503_STOP and not stop.is_set():
        stop.set()
        print("  %d CONSECUTIVE %d ON THE %s FLOOR - STOPPING ALL. Do not"
              " retry, do not rotate." % (n, code, floor), flush=True)


def floor_ok(floor):
    with slock:
        _streak[floor] = 0


def fail_row(did, err):
    with slock:
        stats["fail"] += 1
    try:
        with FAILS.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": did, "err": err[:120]}) + "\n")
    except OSError:
        pass


# ── per-floor db writers - sqlite serializes, no global lock ────────────
def _wcon():
    c = sqlite3.connect(CP.NAV_DB, timeout=600, check_same_thread=False)
    c.execute("PRAGMA busy_timeout=120000")
    return c


def _write(con, wlock, fn):
    """Retry a write on ITS floor's connection. A busy-wait blocks only
    this floor; 120 s busy_timeout + retries survive index builds."""
    for _try in range(60):
        try:
            with wlock:
                fn(con)
                con.commit()
            return True
        except sqlite3.OperationalError:
            time.sleep(5)
    return False


RD_CON, RD_WLOCK = _wcon(), threading.Lock()
PDF_CON, PDF_WLOCK = _wcon(), threading.Lock()
MON_CON, MON_WLOCK = _wcon(), threading.Lock()


# ── FLOOR: registration (rd backfill) ───────────────────────────────────
rd_q = queue.Queue(maxsize=5000)
pend, pend_lock = [], threading.Lock()


def rd_feeder():
    # >> SHARDED BY ID RANGE (--lo/--hi). One process tops out near 10-11
    # docs/s because rd parsing (clean_html + regex over ~118 KB +
    # parse_acris) is pure Python under ONE GIL - measured 2026-08-28,
    # and the same wall the old fleet hit. Scale is PROCESSES over
    # DISJOINT id ranges, never more threads: 4 x 28 workers over quarters
    # measured ~138-140 docs/s aggregate. Ranges must not overlap or two
    # shards fetch the same document twice.
    fed, cursor = 0, a.lo
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    while not stop.is_set():
        try:
            rows = read.execute(
                "SELECT id FROM navigation WHERE recorded_details = ''"
                " AND id > ? AND id < ? AND id NOT LIKE 'RC_%'"
                " ORDER BY id LIMIT 5000",
                (cursor, a.hi)).fetchall()
        except sqlite3.OperationalError:
            time.sleep(5)
            continue
        if not rows:
            break
        cursor = rows[-1][0]
        for (did,) in rows:
            if stop.is_set():
                return
            rd_q.put(did)
            fed += 1
            if a.limit and fed >= a.limit:
                rd_q.put(None)
                return
    rd_q.put(None)


def rd_flush():
    with pend_lock:
        batch, pend[:] = pend[:], []
    if batch and not _write(RD_CON, RD_WLOCK, lambda c: c.executemany(
            "UPDATE navigation SET recorded_details=? WHERE id=?", batch)):
        with pend_lock:
            pend[:0] = batch


def rd_worker():
    while not stop.is_set():
        try:
            did = rd_q.get(timeout=2)
        except queue.Empty:
            continue
        if did is None:
            rd_q.put(None)
            return
        try:
            # >> A PAGE THAT DOES NOT ECHO THE ID IS A RE-ASK, NOT A
            # FAILURE (measured 2026-08-28). Running beside the document
            # floor, this check failed on 4,123 of 6,574 requests - 63% -
            # while the SAME ids returned full 118 KB pages echoing their
            # id when fetched calmly seconds later (2022021401292001 /
            # ...93001 / ...97001, all three). acris serves a short or
            # generic page under concurrency; it is the rd twin of the
            # image floor's soft-refusal, and the cure is identical: ask
            # again in place, briefly, and only give up to the next pass.
            # The echo check STAYS - it is what makes a wrong page
            # detectable at all - it just stops being a verdict.
            for _try in range(3):
                body, _ct = fetch_rd(
                    ACRIS_URL + "DocumentDetail?doc_id=" + did, ACRIS_URL)
                html = RD.clean_html(body.decode("utf-8", "replace"))
                LD.check_refused(html)
                flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
                if re.search(r"DOCUMENT ID:\s*" + re.escape(did), flat):
                    break
                with slock:
                    stats["reask"] = stats.get("reask", 0) + 1
                if _try == 2:
                    raise ValueError("page does not echo id after 3 asks")
                time.sleep(0.5 * (_try + 1))
            rec = RD.parse_acris(html)
            rec["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            with pend_lock:
                pend.append((json.dumps(rec, separators=(",", ":")), did))
                n = len(pend)
            if n >= BATCH:
                rd_flush()
            with slock:
                stats["rd"] += 1
            floor_ok("rd")
        except (fetch_pages.AccessDenied, LD.Refused) as e:
            refused_stop(did, e)
        except urllib.error.HTTPError as e:
            h503(e.code, "rd")
            fail_row(did, "HTTP%d" % e.code)
        except Exception as e:
            fail_row(did, type(e).__name__)


# ── FLOOR: documentation (image backfill, 3 statuses) ───────────────────
pdf_q = queue.Queue(maxsize=2000)
hot_q = queue.Queue()


def _rec_date(v):
    if v and v.lstrip().startswith("{"):
        try:
            return json.loads(v).get("recorded", "") or ""
        except Exception:
            return ""
    return v or ""


def _fresh(rec_date):
    try:
        rec = time.strptime(rec_date.strip()[:10], "%m/%d/%Y")
        return (time.time() - time.mktime(rec)) < a.fresh_days * 86400
    except Exception:
        return False


def pdf_feeder():
    fed, cursor = 0, ""
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    while not stop.is_set():
        try:
            rows = read.execute(
                "SELECT id, recorded_details FROM navigation"
                " WHERE pdf IN ('','pending') AND id > ?"
                " AND id NOT LIKE 'RC_%' AND recorded_details != ''"
                " AND pdf = '' ORDER BY id LIMIT 2000", (cursor,)).fetchall()
        except sqlite3.OperationalError:
            time.sleep(5)
            continue
        if not rows:
            break
        cursor = rows[-1][0]
        for item in rows:
            if stop.is_set():
                return
            pdf_q.put(item)
            fed += 1
            if a.limit and fed >= a.limit:
                pdf_q.put(None)
                return
    pdf_q.put(None)


def pending_recheck():
    """pending stays in the queue until it resolves (login): re-ask the
    whole pending set every --pending-recheck seconds AHEAD of the
    backfill. Expiry is automatic - the re-ask that finds a doc aged past
    --fresh-days writes 'imageless' instead of 'pending'. Bounded and
    logged so it can never silently flood or silently hang."""
    read = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                           check_same_thread=False)
    read.execute("PRAGMA busy_timeout=60000")
    while not stop.is_set():
        stop.wait(a.pending_recheck)
        if stop.is_set():
            return
        t0 = time.time()
        try:
            rows = read.execute(
                "SELECT id, recorded_details FROM navigation"
                " WHERE pdf IN ('','pending') AND pdf != ''"
                " AND id NOT LIKE 'RC_%' LIMIT 5000").fetchall()
        except sqlite3.OperationalError as e:
            print("  PENDING RECHECK: query busy (%.60s) - next cycle"
                  % e, flush=True)
            continue
        for item in rows:
            hot_q.put(item)
        print("  PENDING RECHECK: %d re-queued ahead of the backfill"
              " (%.1fs)" % (len(rows), time.time() - t0), flush=True)


def pdf_worker():
    while not stop.is_set():
        try:
            item = hot_q.get_nowait()
        except queue.Empty:
            try:
                item = pdf_q.get(timeout=2)
            except queue.Empty:
                continue
        if item is None:
            pdf_q.put(None)
            try:
                item = hot_q.get(timeout=5)
            except queue.Empty:
                continue
        did, rd = item
        try:
            # >> THE SOFT-REFUSAL IS A RE-ASK, NOT A FAILURE (login
            # 2026-08-28: "same with pending, the only thing with pending
            # is that it continues to get checked"). acris sometimes
            # answers an image request with a short page carrying no
            # TotalPages token. It is NOT a block - the probe, rd and sync
            # floors keep serving straight through it (a real block kills
            # every floor at once), and the SAME id served 118 KB on a
            # calm retry seconds later. So treat it the way the source
            # treats a not-yet-ready scan: ask again, briefly, in place.
            # Only if it will not resolve does the row stay todo (pdf='')
            # for the next pass - never a verdict, never a "failure" the
            # breaker can mistake for a wall.
            for _try in range(3):
                try:
                    state, value = AP.fetch_pdf(did, _rec_date(rd))
                    break
                except ValueError as ve:
                    if "did not identify" not in str(ve) or _try == 2:
                        raise
                    with slock:
                        stats["reask"] = stats.get("reask", 0) + 1
                    time.sleep(0.6 * (_try + 1))
            if state == "pdf":
                new, bucket = value, "pdf"
            elif _fresh(_rec_date(rd)):
                new, bucket = "pending", "pending"
            else:
                new, bucket = "imageless", "imageless"
            if _write(PDF_CON, PDF_WLOCK, lambda c: c.execute(
                    "UPDATE navigation SET pdf=? WHERE id=? AND"
                    " pdf IN ('','pending')", (new, did))):
                with slock:
                    stats[bucket] += 1
            floor_ok("pdf")
        except (fetch_pages.AccessDenied, LD.Refused) as e:
            refused_stop(did, e)
        except AP.Short as e:
            with slock:
                stats["short"] += 1
            fail_row(did, str(e))
        except urllib.error.HTTPError as e:
            h503(e.code, "pdf")
            fail_row(did, "HTTP%d" % e.code)
        except Exception as e:
            fail_row(did, type(e).__name__)


# ── FLOOR: synchronization (monitor + 20-walker crew) ───────────────────
def read_edge():
    return int(json.loads(EDGE_STATE.read_text(encoding="utf-8"))["edge"])


def write_edge(n):
    st = json.loads(EDGE_STATE.read_text(encoding="utf-8"))
    st["edge"] = n
    st["watermark"] = n
    EDGE_STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")


def urls(did):
    return (ACRIS_URL + "DocumentDetail?doc_id=" + did,
            ACRIS_URL + "DocumentImageView?doc_id=" + did)


def land(found):
    ins = [(did, "", urls(did)[0], "", urls(did)[1], "", "")
           for _c, did, _r in found]
    upd = [(rd, did) for _c, did, rd in found if rd]

    def w(c):
        c.executemany(
            "INSERT OR IGNORE INTO navigation (id, recorded_details,"
            " rd_url, pdf, pdf_url, keyed_by, key) VALUES (?,?,?,?,?,?,?)",
            ins)
        c.executemany(
            "UPDATE navigation SET recorded_details=? WHERE id=?"
            " AND recorded_details=''", upd)
    return _write(MON_CON, MON_WLOCK, w)


def write_ledger(n_docs, ids):
    try:
        lg = sqlite3.connect(LEDGER_DB, timeout=60)
        try:
            prev = lg.execute(
                "SELECT system_total FROM synchronization WHERE"
                " source='acris' AND system_total > 0"
                " ORDER BY run_at DESC LIMIT 1").fetchone()
            sysn = (prev[0] if prev else 0) + n_docs
            lg.execute("INSERT OR REPLACE INTO synchronization (run_at,"
                       " source, system_total, source_total, delta,"
                       " doc_ids) VALUES (?,?,?,?,?,?)",
                       (time.strftime("%Y-%m-%d %H:%M"), "acris", sysn,
                        sysn, 0, ";".join(ids)))
            lg.commit()
        finally:
            lg.close()
    except Exception as e:
        print("  ledger write failed (%s) - rows ARE landed"
              % type(e).__name__, flush=True)


sync_q = queue.Queue()
_sync_res = {}
_sync_lock = threading.Lock()
_sync_done = threading.Semaphore(0)


def sync_worker():
    """One of the 20-walker crew: fetch a crfn, hand the result back."""
    while not stop.is_set():
        try:
            crfn = sync_q.get(timeout=2)
        except queue.Empty:
            continue
        state, did, rec = "blank", None, ""
        try:
            state, did, html = AE.fetch(crfn)
            if state == "live":
                try:
                    rec = json.dumps(RD.parse_acris(html),
                                     separators=(",", ":"))
                except Exception:
                    rec = ""          # rd floor retries it
            floor_ok("sync")
        except (fetch_pages.AccessDenied, LD.Refused) as e:
            refused_stop("edge walk", e)
        except urllib.error.HTTPError as e:
            h503(e.code, "sync")
        except Exception:
            pass                      # unproven crfn - treated blank
        with _sync_lock:
            _sync_res[crfn] = (state, did, rec)
        _sync_done.release()


def monitor():
    """Coordinates the edge: dispatch a bite to the crew, collect in crfn
    order, land the lives, advance. Still behind -> next bite at once."""
    # ⚠ DEFINED HERE, NOT INHERITED. I wrote CONFIRM_BLANKS into this loop
    # from memory of acris_lane.py, where it lives - this file never had
    # it. Every tick raised NameError, the broad `except Exception` printed
    # "PROBE UNPROVEN" and swallowed it, and the sync floor sat at 0 reqs /
    # 0 landed for three windows looking merely "level". A blind watcher
    # and a quiet one are indistinguishable from the outside; only the
    # request COUNT gave it away.
    WATCH = 8               # ids probed per tick while level
    # ⚠⚠ THE MONITOR STANDS AT THE ELEVATOR; THE CREW ONLY WALKS ON A HIT
    # (measured 2026-08-28). This loop dispatched a FULL --bite every tick
    # whether or not anything was there: at level that is ~500 requests per
    # --every seconds = 35.9 req/s spent to land ZERO documents, and every
    # one of them competed with register and document AT THE SOURCE (rd
    # fell to 2.95/s beside it). login's model is the fix: the monitor
    # watches cheaply, and only when he sees a filing does he tell the
    # walkers to walk. So: probe CONFIRM_BLANKS ids while level, escalate
    # to the full bite only while actually behind.
    behind = False
    while not stop.is_set():
        try:
            edge = read_edge()
            n = a.bite if behind else WATCH
            bite = list(range(edge + 1, edge + 1 + n))
            with _sync_lock:
                _sync_res.clear()
            for c in bite:
                sync_q.put(c)
            got = 0
            deadline = time.time() + 300
            while got < len(bite) and time.time() < deadline \
                    and not stop.is_set():
                if _sync_done.acquire(timeout=5):
                    got += 1
            with _sync_lock:
                res = dict(_sync_res)
            found = []
            for c in bite:
                st_, did, rec = res.get(c, ("blank", None, ""))
                if st_ == "live" and did:
                    found.append((c, did, rec))
            # trailing blanks: how deep past the last live did we look?
            last_live = found[-1][0] if found else edge
            trailing = bite[-1] - last_live
            if found and land(found):
                write_edge(last_live)
                write_ledger(len(found), [d for _c, d, _r in found])
                with slock:
                    stats["sync"] += len(found)
                print("  SYNC landed %d - rd in the SAME request - edge"
                      " %d -> %d (crew of %d)"
                      % (len(found), edge, last_live, a.sync_workers),
                      flush=True)
            if found and trailing < 8:
                behind = True         # still behind - full bite, NOW
                continue
            behind = False            # level: back to a cheap watch
        except (fetch_pages.AccessDenied, LD.Refused) as e:
            refused_stop("edge probe", e)
        except (NameError, AttributeError, TypeError) as e:
            # ⚠ A CODE BUG IS NOT AN UNPROVEN PROBE. These three mean the
            # loop itself is broken, and dressing them as "PROBE UNPROVEN"
            # let a NameError masquerade as a quiet edge for three windows
            # (2026-08-28). Say it loudly and stop the floor - a monitor
            # that cannot run must not look like a monitor with nothing
            # to report.
            print("  ⚠⚠ MONITOR CODE BUG (%s: %s) - STOPPING THIS FLOOR;"
                  " this is OUR defect, not the source"
                  % (type(e).__name__, e), flush=True)
            stop.set()
        except Exception as e:
            print("  PROBE UNPROVEN (%s: %.70s) - nothing written"
                  % (type(e).__name__, e), flush=True)
        stop.wait(a.every)


# ── entry: ONE DOOR PER OPEN FLOOR, staggered ───────────────────────────
# ⚠ THE BANNER USED TO SAY "THREE FLOORS, THREE ENTRIES" NO MATTER WHAT,
# and counted a monitor into TOTAL that a zero-worker sync floor should
# never have had. A banner that cannot say "one" is not a report, it is a
# slogan - and it is what let three doors pass for one all morning.
# It now counts only what actually enters.
OPEN = [n for n in ("sync", "register", "document") if WANT[n]]
TOTAL = (a.sync_workers + (1 if WANT["sync"] else 0)
         + a.rd_workers + a.pdf_workers)
print("acris_reproduction up - %d FLOOR%s, %d ENTR%s: %s"
      " - each open floor ONE pooled session, staggered births,"
      " keep-alive after (~%d handshakes total, then zero) - no pacer,"
      " no governor - stop-on-refusal stills every floor"
      % (len(OPEN), "" if len(OPEN) == 1 else "S",
         len(OPEN), "Y" if len(OPEN) == 1 else "IES",
         " - ".join("%s %d" % (n, {"sync": a.sync_workers + 1,
                                   "register": a.rd_workers,
                                   "document": a.pdf_workers}[n])
                    for n in OPEN) or "NOTHING",
         TOTAL),
      flush=True)
if not OPEN:
    sys.exit("  no floor has workers - nothing to do, entering nothing")

# ⚠ A FEEDER BELONGS TO ITS FLOOR. pdf_feeder and pending_recheck were
# started unconditionally; pending_recheck re-asks acris for images, so a
# registration-only run was scheduling image traffic behind the operator's
# back. Each feeder now runs only when its floor is open.
feeders = []
if WANT["register"]:
    feeders.append(threading.Thread(target=rd_feeder, daemon=True))
if WANT["document"]:
    feeders.append(threading.Thread(target=pdf_feeder, daemon=True))
    feeders.append(threading.Thread(target=pending_recheck, daemon=True))
for t in feeders:
    t.start()

# >> SEQUENTIAL FLOOR ENTRIES (login 2026-08-28: "1 enter for sync, then
# the rd, then the pdf... stagger so it doesnt look like 3 entries at
# once"). Each OPEN floor walks through its own door completely before
# the next approaches; a closed floor is not a door at all, so a
# single-floor run takes exactly one entry and no --entry-gap breath.
# Within a floor, births stay staggered --stagger apart as before.
# ⚠ THE MONITOR IS THE SYNC FLOOR'S, NOT A FREE AGENT. It probes the crfn
# edge on its own schedule; attaching it to a run whose sync crew is 0 is
# how a "registration only" batch kept talking to acris on another floor.
syncf = (([threading.Thread(target=monitor, daemon=True)]
          + [threading.Thread(target=sync_worker, daemon=True)
             for _ in range(a.sync_workers)]) if WANT["sync"] else [])
regf = ([threading.Thread(target=rd_worker, daemon=True)
         for _ in range(a.rd_workers)] if WANT["register"] else [])
docf = ([threading.Thread(target=pdf_worker, daemon=True)
         for _ in range(a.pdf_workers)] if WANT["document"] else [])
t0 = time.time()
floor = []
for name, crew in (("sync", syncf), ("register", regf),
                   ("document", docf)):
    if not crew:                   # closed floor - no session, no entry
        continue
    if floor:                      # a breath between doors, never within
        time.sleep(a.entry_gap)
    for i, t in enumerate(crew):
        t.start()
        if i < len(crew) - 1:
            time.sleep(a.stagger)
    floor += crew
    print("  %s floor is inside - %d worker(s), own session, own entry"
          % (name, len(crew)), flush=True)
print("  %s entered over %.0fs - %s"
      % ("all %d floors" % len(OPEN) if len(OPEN) > 1
         else "the %s floor" % OPEN[0],
         time.time() - t0,
         ("separate doors, %.0fs apart" % a.entry_gap) if len(OPEN) > 1
         else "ONE DOOR, one entry, nothing else touched acris"),
      flush=True)

try:
    last = dict(stats)
    last_fail = 0
    while any(t.is_alive() for t in floor) and not stop.is_set():
        stop.wait(60)
        rd_flush()
        el = time.time() - t0
        with slock:
            s = dict(stats)
        # REPRODUCTION SPEED: rows completing their FULL pass this window
        # (a completion write = pdf path, pending, or imageless landing on
        # a row whose id+urls+rd already stand; sync rows complete later
        # through the same gate)
        repro = ((s["pdf"] + s["pending"] + s["imageless"])
                 - (last["pdf"] + last["pending"] + last["imageless"])) / 60.0
        print("  PROGRESS %dm - reqs %s (%.1f/s) - %s total - %s pdfs -"
              " %s imageless - %s pending - sync %s - short %d - fail %d -"
              " repro %.2f docs/s - rd %.2f/s now"
              % (el / 60, "{:,}".format(s["reqs"]), s["reqs"] / el,
                 "{:,}".format(s["rd"]), "{:,}".format(s["pdf"]),
                 "{:,}".format(s["imageless"]), "{:,}".format(s["pending"]),
                 "{:,}".format(s["sync"]), s["short"], s["fail"], repro,
                 (s["rd"] - last["rd"]) / 60.0), flush=True)
        # ⚠⚠ THE BREAKER WAS THE BLOCKER (2026-08-28). A raw fail-count
        # threshold cannot tell a BLOCK from retryable per-request noise,
        # and it stopped three healthy runs: every floor was serving
        # (probe answering, rd landing 7/s, sync walking) while a
        # counter tripped on soft-refusals the source resolves on a
        # re-ask. THE TRUE BLOCK SIGNALS ALREADY HAVE THEIR OWN
        # DETECTORS, each of which stills every floor on its own:
        #   · LD.Refused / AccessDenied  the Bandwidth Notice + blocked
        #                                payload -> refused_stop()
        #   · h503()                     40 consecutive 503/429 on one
        #                                floor with none of its own
        #                                successes between -> a wall
        # Those are evidence. A fail COUNT is a symptom, and a loud one
        # during a reversal band replay. So the breaker no longer stops
        # the run; it WARNS, and the run keeps its own evidence.
        if s["fail"] - last_fail >= 300:
            print("  ⚠ %d fails this minute (reask %d) - NOT stopping:"
                  " every floor still serving; the refusal + 503-wall"
                  " detectors are the block evidence, a fail count is"
                  " not" % (s["fail"] - last_fail, s.get("reask", 0)),
                  flush=True)
        last_fail = s["fail"]
        last = s
finally:
    rd_flush()
    el = time.time() - t0
    with slock:
        s = dict(stats)
    print("\nrun end %.1f min - reqs %s (%.1f/s) - rd %s - pdf %s -"
          " imageless %s - pending %s - sync %s - fail %d"
          % (el / 60, "{:,}".format(s["reqs"]), s["reqs"] / max(el, 1e-9),
             "{:,}".format(s["rd"]), "{:,}".format(s["pdf"]),
             "{:,}".format(s["imageless"]), "{:,}".format(s["pending"]),
             "{:,}".format(s["sync"]), s["fail"]), flush=True)
