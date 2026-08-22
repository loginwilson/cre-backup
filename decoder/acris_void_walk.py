"""THE ACRIS VOID WALK — name and classify every issued-but-unindexed CRFN
(login 2026-08-21: "make sure we gather all doc ids... I need to know that
the count is accurate").

The census proved issued(Y) per year; the index holds fewer. The residue
(+7,638 total) is NAMED here: for each year, missing = [1..edge] minus the
index's own CRFN list, then every missing number is asked of ACRIS itself:

    resolves -> a real document the index dropped (12 already proven live)
                -> its doc id goes to the Legal Instruments db via sync
    blank    -> VOID by the county's own testimony -> the void ledger

Closing identity, per year:  index + missing docs + voids = issued.

    python acris_void_walk.py --name      build _acris_missing_crfns.json
    python acris_void_walk.py --walk      probe them all, write the ledgers
    python acris_void_walk.py --report    the identity, per year

⚠ 2026 is capped at the index's own highest CRFN: everything above it was
enumerated number-by-number by the daily live walk (that is what the walk
IS), so only the band the index should have covered is in question.
⚠ Resumable: the walk journal (_acris_void_walk.json) records every verdict;
a rerun skips them. 10 workers, one session each, LD.PACE spacing - an
eighth of the proven 4x20 daily acquisition load. STOPS on a refusal.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import threading
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP
import live_crfn as LC
import live_delta as LD

SYNC = (pathlib.Path(r"D:\CRE Decoding System\00 Synchronizations")
        / "Legal Instruments Synchronization")
CENSUS = SYNC / "ACRIS Census.json"
MISSING = SYNC / "_acris_missing_crfns.json"
JOURNAL = SYNC / "_acris_void_walk.json"
DS = ["bnx9-e6tj", "sv7x-dduq"]

ap = argparse.ArgumentParser()
ap.add_argument("--name", action="store_true")
ap.add_argument("--walk", action="store_true")
ap.add_argument("--report", action="store_true")
a = ap.parse_args()


def _tok():
    for line in pathlib.Path(r"C:\dev\acris-decoder.env").read_text().splitlines():
        if "SOCRATA" in line.upper() and "=" in line:
            return line.split("=", 1)[1].strip().strip('"')


def index_seqs(year):
    """every CRFN sequence number the index holds for the year"""
    tok = _tok()
    seqs = set()
    for ds in DS:
        off = 0
        while True:
            p = {"$select": "crfn", "$where": f"starts_with(crfn, '{year}')",
                 "$order": "crfn", "$limit": "50000", "$offset": str(off)}
            u = (f"https://data.cityofnewyork.us/resource/{ds}.json?"
                 + urllib.parse.urlencode(p))
            req = urllib.request.Request(u, headers={"X-App-Token": tok})
            for att in range(3):
                try:
                    got = json.load(urllib.request.urlopen(req, timeout=120))
                    break
                except Exception:
                    if att == 2:
                        raise
                    time.sleep(5)
            for row in got:
                c = row.get("crfn") or ""
                if len(c) == 13 and c.isdigit():
                    seqs.add(int(c[4:]))
            if len(got) < 50000:
                break
            off += 50000
    return seqs


def name():
    census = json.loads(CENSUS.read_text())
    out = {}
    for y in sorted(k for k in census if k.isdigit()):
        edge = census[y].get("issued")
        if not edge:
            continue
        held = index_seqs(int(y))
        top = max(held) if int(y) == 2026 else edge   # 2026: walk owns the tail
        miss = sorted(set(range(1, top + 1)) - held)
        out[y] = miss
        print(f"{y}: issued {edge:,} · index {len(held):,} ·"
              f" missing {len(miss):,}", flush=True)
    MISSING.write_text(json.dumps(out))
    print(f"named {sum(len(v) for v in out.values()):,} missing CRFNs"
          f" -> {MISSING.name}")


def walk():
    miss = json.loads(MISSING.read_text())
    done = json.loads(JOURNAL.read_text()) if JOURNAL.exists() else {}
    todo = [(y, s) for y, seqs in sorted(miss.items()) for s in seqs
            if f"{y}{s:09d}" not in done]
    print(f"{sum(len(v) for v in miss.values()):,} named ·"
          f" {len(done):,} already classified · {len(todo):,} to probe",
          flush=True)
    # check_same_thread=False: workers share this read-only handle; every
    # use is under navlock (the rc_census lesson - and this line only runs
    # when a probe RESOLVES, so the first real document found is what
    # crossed threads and crashed the 2026-08-21 run)
    nav = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600,
                          check_same_thread=False)
    navlock = threading.Lock()
    lock = threading.Lock()
    tls = threading.local()
    n = [0]
    t0 = time.time()

    def one(item):
        y, s = item
        crfn = f"{y}{s:09d}"
        if not hasattr(tls, "s"):
            tls.s = LD.Session().open().open_crfn()
        d = LC.parse_detail(LC.detail_html(tls.s, crfn))
        if d is None:
            verdict = {"v": "void"}
        else:
            did = d["doc_id"]
            with navlock:
                held = nav.execute("SELECT 1 FROM navigation WHERE id=?",
                                   (did,)).fetchone()
            verdict = {"v": "held" if held else "MISSING_DOC", "doc_id": did}
        with lock:
            done[crfn] = verdict
            n[0] += 1
            if verdict["v"] == "MISSING_DOC":
                print(f"  !! {crfn} -> {verdict['doc_id']} NOT IN DB",
                      flush=True)
            if n[0] % 100 == 0:
                el = (time.time() - t0) / 60
                JOURNAL.write_text(json.dumps(done))
                print(f"PROGRESS {n[0]:,}/{len(todo):,} · {el:.0f} min",
                      flush=True)

    from concurrent.futures import ThreadPoolExecutor
    # 10 workers, one session each - an eighth of the 4x20 acquisition load
    # this host served daily (login: "can you do better speed so we can start")
    try:
        with ThreadPoolExecutor(max_workers=10) as ex:
            list(ex.map(one, todo))
    finally:
        JOURNAL.write_text(json.dumps(done))
    report()


def report():
    done = json.loads(JOURNAL.read_text()) if JOURNAL.exists() else {}
    miss = json.loads(MISSING.read_text()) if MISSING.exists() else {}
    void = sum(1 for v in done.values() if v["v"] == "void")
    held = sum(1 for v in done.values() if v["v"] == "held")
    docs = sorted(v["doc_id"] for v in done.values() if v["v"] == "MISSING_DOC")
    named = sum(len(v) for v in miss.values())
    print(f"named {named:,} · classified {len(done):,} ·"
          f" void {void:,} · already held {held:,} ·"
          f" MISSING DOCS {len(docs):,}")
    if docs:
        f = SYNC / "_acris_missing_docs.txt"
        f.write_text("\n".join(docs))
        print(f"missing doc ids -> {f}  (land via nav_append --ids ... --apply)")
    if len(done) == named and not docs:
        print("IDENTITY CLOSED: index + voids = issued, every number named")


if a.name:
    name()
elif a.walk:
    walk()
elif a.report:
    report()
else:
    print(__doc__)
