"""RICHMOND RD — the CODED way on the redesigned site (login 2026-08-21:
"I suggest we run richmond rd (this is the coded way)").

THE GRANT RULE, measured tonight: a detail unlocks after the session has
fetched THE LISTING PAGE the id appears on — not the whole search, not
nothing. (A held id whose page was never fetched gets the 4,212-byte
shell; the same id right after its page: full RECORDED DETAILS.) So the
walk is: window -> its pages -> its targets' details, one session per
worker, and the census db already knows every target's window.

What a detail carries (both eras verified): Document No. (instrument) ·
Book/Page (old era) · Type · Date Recorded · Consideration · Status ·
BLOCKS AND LOTS (the parcel key!) · PARTIES (name + role; may be empty on
old records - recorded as an honest []).

    python rc_rd_walk.py --run [--workers 8]
    python rc_rd_walk.py --report

⚠ CONCURRENCY, measured 2026-08-21: the county's PROVEN envelope is far
above polite-looking numbers - night_chain ran rc_detail_pull at conc 80,
TWICE CONCURRENTLY (160 connections), landing 2,498,810 details in ~26 h
(Aug 18 20:57 -> Aug 19 22:49, ~27 docs/s sustained) with no trip. The
NEW site took the same 160 the night of Aug 21 (2 shards x 80 workers,
~19-20 docs/s combined, ZERO fails) - but ONLY because sess() STAGGERS the
first handshakes: 160 cold TLS opens in one instant = SSLError across the
board while a lone request succeeds seconds later (keep-alive removes
every handshake except the first; the 0.4 s/worker ramp paces the first).
Our own GIL pins one process near one core (~10 docs/s), so scale is
PROCESS sharding (--shard i/n), not more threads. STOPS ALL on a refusal.
Lands only into EMPTY rd cells, in the CORPUS SCHEMA (bbl parcels,
image_state, person/company party columns).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sqlite3
import sys
import threading
import time

import requests

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP
import fetch_pages

RC = "https://www.richmondcountyclerk.com"
CENSUS_DB = (pathlib.Path(r"D:\CRE Decoding System\00 Synchronizations")
             / "Legal Instruments Synchronization" / "Richmond Census.db")
FAILS = CP.NAV_WORK / "rc_rd_walk_fails.jsonl"
PACE = 0.2   # 10 workers @ 0.2 = the census's proven clean load

ap = argparse.ArgumentParser()
ap.add_argument("--run", action="store_true")
ap.add_argument("--report", action="store_true")
ap.add_argument("--workers", type=int, default=8)
ap.add_argument("--limit", type=int, default=0, help="windows cap, for a probe")
ap.add_argument("--shard", default="", help="i/n - walk every n-th window,"
                " offset i (process sharding past the GIL)")
a = ap.parse_args()


class Refused(RuntimeError):
    pass


def parse_detail(html, iid):
    """RECORDED DETAILS + BLOCKS AND LOTS + PARTIES — landed in the CORPUS
    SCHEMA (the 2.4M rows' shape, login 2026-08-21 showed the reference):
    parcels carry the BBL (borough 5 + block(5) + lot(4)) or the keyer is
    blind; image_state is read from the View-Imaged link (rc_mint selects
    pdf work by it); parties keep the person/company COLUMN distinction."""
    raw = re.sub(r"&nbsp;?", " ", html)
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw))
    if "RECORDED DETAILS" not in flat:
        raise ValueError("no detail (shell or unauthorized)")

    def fld(label):
        m = re.search(label + r":\s*([^:]*?)\s*"
                      r"(?=[A-Z][a-z]+ ?[A-Z]?[a-z]*:|BLOCKS)", flat)
        return m.group(1).strip() if m else ""

    rec = {
        # ⚠ the label is "Document No.:" on modern pages (PERIOD before the
        # colon) and "Document No:" on old-era ones - a plain "Document No"
        # + ":" matched only the old form, so every SAME-DAY-landed 2026
        # doc froze with instrument '' (found 2026-08-22 when the user's
        # instrument-number audit couldn't see 103 held docs)
        "instrument": fld(r"Document No\.?"),
        "book": fld("Book"),
        "page": fld("Page"),
        "doc_type": fld("Document Type"),
        "recorded": fld("Date Recorded"),
        "amount": fld("Consideration Amount"),
        "status": re.sub(r"\s*View Imaged Document.*$", "", fld("Status")),
        "image_state": ("present" if "View Imaged Document" in flat
                        else "absent"),
        "parcels": [{"bbl": f"5{b.zfill(5)}{l.zfill(4)}"} for b, l in
                    re.findall(r"Block (\d+), Lot (\d+)", flat)],
        "parties": [],
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    in_parties = False
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", raw, re.S):
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
        if not cells:
            continue
        if cells[:3] == ["Name", "Company", "Party"]:
            in_parties = True
            continue
        if in_parties and len(cells) >= 3 and (cells[0] or cells[1]):
            person, company, role = cells[0], cells[1], cells[2]
            rec["parties"].append({
                "name": person or company, "role": role,
                "column": "name" if person else "company",
                "person": person, "company": company})
    return rec


def run():
    nav_ro = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)
    todo_ids = [int(r[0][3:]) for r in nav_ro.execute(
        "SELECT id FROM navigation WHERE id GLOB 'RC_*'"
        " AND COALESCE(recorded_details,'')=''") if r[0][3:].isdigit()]
    cen = sqlite3.connect(f"file:{CENSUS_DB}?mode=ro", uri=True, timeout=600,
                          check_same_thread=False)
    wins = {}
    have = set(todo_ids)
    for iid, ws in cen.execute("SELECT internal_id, window_start FROM listing"):
        if iid in have:
            wins.setdefault(ws, []).append(iid)
    todo = sorted(wins.items())
    if a.shard:
        i, n = map(int, a.shard.split("/"))
        todo = todo[i::n]
    if a.limit:
        todo = todo[:a.limit]
    print(f"rc rd walk: {len(have):,} empty rd · {len(todo):,} windows"
          + (f" (shard {a.shard})" if a.shard else ""), flush=True)

    con = sqlite3.connect(CP.NAV_DB, timeout=600, check_same_thread=False)
    con.execute("PRAGMA busy_timeout=300000")
    wlock = threading.Lock()
    lock = threading.Lock()
    tls = threading.local()
    stop = threading.Event()
    stats = {"done": 0, "fail": 0, "win": 0}
    t0 = time.time()

    born = [0]

    def sess():
        if not hasattr(tls, "s"):
            # ⚠ RAMP THE FIRST HANDSHAKES (measured 2026-08-21: 160 workers
            # opening TLS in the same instant = SSLError across the board,
            # while the county served a lone request seconds later - the
            # cold-burst trip, Richmond edition). Keep-alive removes every
            # handshake EXCEPT the first; this staggers the first.
            with lock:
                born[0] += 1
                k = born[0]
            time.sleep(min(k * 0.4, 45))
            tls.s = requests.Session()
            tls.s.headers["User-Agent"] = fetch_pages.UA
        return tls.s

    def get(url):
        # ⚠ RETRY PER PAGE, not per window. The window loop restarts from
        # page 1 on failure, so in a DEEP window (the census recovery
        # windows run hundreds of pages) one mid-walk timeout aborted the
        # whole window every pass - 339 docs in two deep windows survived
        # TWO full sweeps that way (2026-08-21; a targeted per-page-retry
        # pass landed all 339 in one go). The retry unit must never be
        # bigger than the failure unit. Refusal still raises immediately.
        last = None
        for att in range(4):
            time.sleep(PACE if not att else 3 * att)
            try:
                r = sess().get(url, timeout=90)
            except requests.RequestException as e:
                last = e
                continue
            if ("UNAUTHORIZED" in r.text[:2000]
                    and "SEARCH ACCESS" in r.text[:2000]):
                raise Refused("UNAUTHORIZED SEARCH ACCESS")
            return r.text
        raise last

    def one(item):
        ws, iids = item
        if stop.is_set():
            return
        try:
            import datetime as dt
            d0 = dt.date.fromisoformat(ws)
            end = cen.execute("SELECT end FROM window WHERE start=?",
                              (ws,)).fetchone()
            b = end[0] if end else (d0 + dt.timedelta(days=29)).isoformat()
            n, total, targets = 1, 1, set(iids)
            while n <= total and not stop.is_set():
                h = get(f"{RC}/Search/DateRangeSearch?StartSearchDate={ws}"
                        f"&EndSearchDate={b}&SelectedDocumentIdentifier=0"
                        f"&pageNumber={n}")
                m = re.search(r"Page\s*<span[^>]*>\d+</span>\s*of\s*(\d+)", h)
                if m:
                    total = int(m.group(1))
                page_ids = set(map(int, re.findall(r"ViewDocumentInfo/(\d+)", h)))
                for iid in sorted(targets & page_ids):
                    try:
                        rec = parse_detail(
                            get(f"{RC}/Search/viewDocumentInfo/{iid}"), iid)
                        with wlock:
                            con.execute(
                                "UPDATE navigation SET recorded_details=?"
                                " WHERE id=? AND COALESCE(recorded_details,'')=''",
                                (json.dumps(rec, separators=(",", ":")),
                                 f"RC_{iid}"))
                            con.commit()
                        with lock:
                            stats["done"] += 1
                    except Refused:
                        raise
                    except Exception as e:
                        with lock:
                            stats["fail"] += 1
                            with FAILS.open("a", encoding="utf-8") as fh:
                                fh.write(json.dumps(
                                    {"id": iid, "err": type(e).__name__}) + "\n")
                    targets.discard(iid)
                if not targets:
                    break
                n += 1
            with lock:
                stats["win"] += 1
        except Refused as e:
            stop.set()
            print(f"  REFUSED - STOPPING ALL: {e}", flush=True)
        except Exception as e:
            with lock:
                stats["fail"] += 1
            print(f"  ⚠ window {ws} failed ({type(e).__name__}) - resume"
                  f" re-finds its rows", flush=True)

    from concurrent.futures import ThreadPoolExecutor
    def reporter():
        while not stop.is_set():
            time.sleep(60)
            el = time.time() - t0
            with lock:
                d, f, w = stats["done"], stats["fail"], stats["win"]
            print(f"  PROGRESS {d:,} rc rd · +{d:,} this run ·"
                  f" {d/el:.1f} docs/s · {w}/{len(todo)} windows · {f} fail"
                  f" · {el/60:.0f} min", flush=True)
    threading.Thread(target=reporter, daemon=True).start()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(one, todo))
    stop.set()
    print(f"rc rd walk end: +{stats['done']:,} · {stats['fail']} fail",
          flush=True)


def report():
    nav = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)
    n = nav.execute("SELECT COUNT(*) FROM navigation WHERE id GLOB 'RC_*'"
                    " AND COALESCE(recorded_details,'')=''").fetchone()[0]
    print(f"RC rows with empty rd: {n:,}")


if a.run:
    run()
elif a.report:
    report()
else:
    print(__doc__)
