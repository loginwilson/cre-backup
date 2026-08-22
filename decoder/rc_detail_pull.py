"""RICHMOND LAYER 2 — the per-document detail: PARTIES, amount, status, image state.

    ACRIS_CORPUS_ROOT=D:/acris python rc_detail_pull.py --build    worklist only
    ACRIS_CORPUS_ROOT=D:/acris python rc_detail_pull.py --run --conc 8

WHY A SECOND LAYER AT ALL. The block ledger publishes master + legals + the
instrument<->internal-id binding IN BULK, so layer 1 cost 8,999 requests for
2,426,404 documents. Parties are on the detail page ONLY - Richmond has no bulk
party export the way ACRIS has Socrata - so layer 2 costs ONE REQUEST PER
DOCUMENT. That is the entire structural difference between the two sources.

MEASURED 2026-08-18 (real timings, not arithmetic)
    conc 1   0.5 docs/s      conc 4   2.1 docs/s      conc 8   4.4 docs/s
    -> 2,426,404 documents = ~153 h at conc 8. A CAMPAIGN, NOT A STEP.

Scaling was still near-linear at 8 (8.8x over conc 1), so the server cap has not
been found. It is NOT raised here on that evidence alone: the ledger sweep
plateaued ~1.4 blk/s from conc 5->8 on a different endpoint, and the one trip
this project ever caused was a cold burst at conc 16.

⚠ PRIORITY ORDER IS THE POINT. At 153 h any run is a PARTIAL run, so the order
decides what a partial run is worth. DEED + MORTGAGE are 1,309,323 documents -
54% of the corpus and the half that carries the money and the people. They go
first, so stopping at any moment leaves the most valuable half done rather than
an alphabetical slice of nothing.

⚠ A SESSION NEEDS *A* SEARCH, NOT *THE* SEARCH. Verified: internal ids 90667
(2006) and 1974647 (1998) both resolve through a window opened on 08/17/2026.
The guard requires a search to exist in the session, not that the document be in
its results - so one window per worker serves arbitrary documents. A stale
session returns the UNAUTHORIZED shell at HTTP 200, so that is caught and the
window is rebuilt rather than being written as an empty document.

⚠ RESUMABLE BY CONSTRUCTION. Every record is appended and flushed immediately;
a restart re-reads what is on disk and never re-asks for it. A kill costs one
document, never the run.

⚠ ANY Refused STOPS EVERYTHING. No retry, no rotation, no concurrency bump to
"catch up".
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import rc_source as RC
import rc_sync as RS

import corpus_paths as CP
LEDGER = CP.ARCHIVE / "rc_ledger.jsonl"
WORK = CP.INDEX / "rc_worklist.tsv"
OUT = CP.INDEX / "rc_detail.jsonl"

# money and people first; a partial run should be the useful half
PRIORITY = {"DEED": 0, "MORTGAGE": 1, "A/MTG": 2, "ASSIGNMENT OF MORTGAGE": 2,
            "CONSOLIDATION AGR": 3, "AGREEMENTS": 3, "SAT": 5,
            "SATISFACTION OF MORTGAGE": 5, "REL": 5}
DEFAULT_PRI = 4


def build():
    """Distinct documents, priority-ordered, written to disk (not held in RAM)."""
    seen, rows = {}, 0
    t0 = time.time()
    with LEDGER.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            rows += 1
            i = r["internal_id"]
            if i not in seen:
                seen[i] = (r.get("doc_type") or "").strip().upper()
            if rows % 500000 == 0:
                print(f"    scanned {rows:,} rows · {len(seen):,} distinct")
    items = sorted(seen.items(), key=lambda kv: (PRIORITY.get(kv[1], DEFAULT_PRI), kv[0]))
    WORK.parent.mkdir(parents=True, exist_ok=True)
    with WORK.open("w", encoding="utf-8") as f:
        for i, t in items:
            f.write(f"{i}\t{t}\n")
    print(f"  worklist {len(items):,} documents -> {WORK}  ({time.time()-t0:.0f}s)")
    c = collections.Counter(t for _, t in items)
    for t, n in c.most_common(6):
        print(f"    {t:<26} {n:>9,}")


def done_ids():
    if not OUT.exists():
        return set()
    got = set()
    with OUT.open(encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            # ⚠ AN ERROR ROW IS NOT A DONE ROW. The first version added every
            # internal_id it saw, so a transient URLError marked the document
            # complete forever and no later run ever re-asked for it - a silent,
            # permanent hole that grows with every network blip and is invisible
            # because the resume logic reports it as "already have".
            if r.get("err"):
                continue
            if r.get("internal_id"):
                got.add(r["internal_id"])
    return got


# ---------------------------------------------------------------- link gate
PROBE = "https://www.richmondcountyclerk.com/"
LINK = threading.Event()
LINK.set()
_LINK_LOCK = threading.Lock()
OUTAGES = []


def link_up(timeout=15):
    try:
        req = urllib.request.Request(PROBE, headers={"User-Agent": RC.UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status < 500
    except Exception:
        return False


def hold_for_link():
    """⚠ AN OUTAGE MUST NOT CONSUME THE WORKLIST.

    Login, 2026-08-18: *"if the task stalls cause of a lost connection ... you need
    to notice this and continue where you left off."* Without this gate a dropped
    link does NOT stop the pull - every worker keeps taking ids off the worklist,
    fails all 3 attempts in seconds, and writes an error row. A 20-minute outage at
    conc 20 therefore burns tens of thousands of documents into `err` rows. They are
    recoverable (an error row is not a done row, so they re-queue) but the run
    reports garbage and the jsonl bloats - and a LONG outage would march through the
    entire remainder and "finish" with everything failed.

    So: when a document has exhausted its retries, ask whether the LINK is down
    rather than whether the DOCUMENT is bad.
        link is fine  -> False. Record a genuine error row.
        link is down  -> block until it returns, then True: retry the SAME id.
    One thread probes and reports; the others wait on the event.
    """
    if link_up():
        return False
    with _LINK_LOCK:
        if LINK.is_set():
            LINK.clear()
            t0 = time.time()
            print(f"    ** LINK DOWN {time.strftime('%H:%M:%S')} - holding; "
                  f"worklist NOT consumed", flush=True)
            waited = 0
            while not link_up():
                time.sleep(15)
                waited += 15
                if waited % 300 == 0:
                    print(f"       still down after {waited // 60} min", flush=True)
            el = time.time() - t0
            OUTAGES.append((time.strftime("%H:%M:%S"), round(el)))
            print(f"    ** LINK BACK {time.strftime('%H:%M:%S')} after "
                  f"{el / 60:.1f} min - resuming where it left off", flush=True)
            LINK.set()
    LINK.wait()
    return True


def run(conc, limit):
    if not WORK.exists():
        sys.exit("  no worklist - run --build first")
    got = done_ids()
    todo = []
    with WORK.open(encoding="utf-8") as f:
        for line in f:
            i, _, t = line.rstrip("\n").partition("\t")
            if i and i not in got:
                todo.append((i, t))
                if limit and len(todo) >= limit:
                    break
    print(f"  worklist · already have {len(got):,} · TO FETCH {len(todo):,}")
    if not todo:
        print("  nothing to do.")
        return

    tl = threading.local()
    stop = threading.Event()

    def fetch(item):
        i, t = item
        while True:                    # ⚠ OUTER LOOP - see hold_for_link()
            if stop.is_set():
                return None
            err = None
            for attempt in range(3):
                try:
                    if not hasattr(tl, "w"):
                        tl.w = RS.Window("08/17/2026", "08/17/2026")
                    d = tl.w.detail(i)
                    if d is None:
                        return {"internal_id": i, "doc_type": t, "miss": True}
                    d["internal_id"] = i
                    return d
                except RC.Unauthorized:
                    if hasattr(tl, "w"):
                        del tl.w               # stale session - rebuild once
                    if attempt:
                        return {"internal_id": i, "doc_type": t,
                                "err": "Unauthorized"}
                except RC.Refused:
                    stop.set()
                    return {"internal_id": i, "err": "REFUSED"}
                except Exception as e:
                    # ⚠ RETRY TRANSIENTS, AND KEEP THE MESSAGE. The first version
                    # returned an error row on the FIRST failure and stored only
                    # type(e).__name__ - so a one-second connection blip became a
                    # permanent-looking row that could not be diagnosed. Measured:
                    # all 9 URLErrors from the first 34k succeeded on a plain
                    # sequential retry, 0 failed again - never document problems.
                    err = e
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
            # three attempts gone. Is the DOCUMENT bad, or is the LINK down?
            if err is not None and hold_for_link():
                continue               # link was down: retry the SAME id, no err row
            return {"internal_id": i, "doc_type": t,
                    "err": type(err).__name__ if err else "exhausted",
                    "err_msg": str(err)[:200] if err else ""}

    n = errs = pend = 0
    t0 = time.time()
    recent = collections.deque(maxlen=200)     # rolling outcome window
    cooldowns = [0]                            # list so the closure can mutate it
    OUT.parent.mkdir(parents=True, exist_ok=True)

    def check_degradation():
        """⚠ THE LINK GATE AND THIS GUARD CATCH DIFFERENT FAILURES.

        hold_for_link() catches the link going down - link_up() fails, so the pull
        holds and consumes nothing. But if the LINK is fine and the HOST starts
        refusing, link_up() succeeds and every failure becomes a genuine error row.
        That is what tonight looked like from the inside: clean for 190,000 rows,
        then 3.8%, then 10.5% and climbing, unattended.

        So: watch the rolling error rate. Above the floor WITH the link up, treat it
        as the host asking us to slow down - cool off, escalating each time. Never
        retry harder. Three triggers without recovery means it is not transient, and
        the run stops rather than grinding the remainder into error rows overnight.
        """
        if len(recent) < recent.maxlen:
            return True
        rate = sum(recent) / len(recent)
        if rate <= 0.10:
            cooldowns[0] = 0
            return True
        if not link_up():
            return True                        # the link gate owns this case
        cooldowns[0] += 1
        if cooldowns[0] > 2:
            print(f"  ** HOST STILL DEGRADED ({rate*100:.1f}% errors) after "
                  f"{cooldowns[0]-1} cooldowns - STOPPING rather than grinding the "
                  f"remainder into error rows. Resume with a lower --conc.",
                  flush=True)
            return False
        nap = 300 * cooldowns[0]
        print(f"  ** DEGRADED: {rate*100:.1f}% errors in the last {len(recent)} "
              f"with the link UP - cooling off {nap//60} min (trigger "
              f"{cooldowns[0]})", flush=True)
        time.sleep(nap)
        recent.clear()
        return True
    with OUT.open("a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=conc) as ex:
        for r in ex.map(fetch, todo):
            if r is None:
                continue
            if r.get("err") == "REFUSED":
                print("  REFUSED - STOPPING. Nothing already written is lost.")
                break
            f.write(json.dumps(r) + "\n")
            f.flush()
            n += 1
            recent.append(1 if r.get("err") else 0)
            if not check_degradation():
                stop.set()
                break
            errs += bool(r.get("err"))
            pend += r.get("image_state") == "pending"
            if n % 200 == 0:
                el = time.time() - t0
                rate = n / el
                left = (len(todo) - n) / rate
                print(f"    {n:,}/{len(todo):,} · {rate:.1f} docs/s · "
                      f"{errs} err · {(len(got)+n)/2426404*100:.2f}% of corpus · "
                      f"ETA {left/3600:.1f} h")
    el = time.time() - t0
    print(f"\n  {n:,} fetched · {errs} errors · {el/60:.1f} min · "
          f"{n/max(el,1e-9):.1f} docs/s")
    print(f"  corpus coverage {(len(got)+n):,}/2,426,404 "
          f"({(len(got)+n)/2426404*100:.2f}%)")
    if OUTAGES:
        tot = sum(s for _, s in OUTAGES)
        print(f"  link outages held through: {len(OUTAGES)} "
              f"({tot/60:.1f} min total) - no worklist consumed during them")
        for at, s in OUTAGES:
            print(f"      {at}  {s/60:.1f} min")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--conc", type=int, default=8)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.build:
        build()
    if a.run:
        run(a.conc, a.limit)
    if not (a.build or a.run):
        print("  pass --build and/or --run")


if __name__ == "__main__":
    main()
