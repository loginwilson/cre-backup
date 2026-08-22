"""LAND THE LIVE DELTA INTO THE SPECIFICATION — `parcel → parcel_document → document`.

    ACRIS_CORPUS_ROOT=D:/acris python live_land.py --check     report only, writes nothing
    ACRIS_CORPUS_ROOT=D:/acris python live_land.py --apply     land it, then acceptance-test

Reads `_live_delta_queue.jsonl` (written by `live_delta.py`) and lands it in the
specification on the drive. The local map and Supabase are the OTHER two legs and
they are NOT done here — those go through the existing `amap.py` -> `push_selection.py`
path, because a `document_map` row needs page RANGES this job does not have.

⚠ THE SHAPE IS NOT BOOKKEEPING — IT IS REACHABILITY (LIVE_SYNC.md §8).

    parcel            bbl, n_docs, first_date, last_date
       |               ^ overnight.py selects HERE: WHERE n_docs BETWEEN ? AND ?
    parcel_document   bbl <-> document_id                  ORDER BY n_docs DESC
       |
    document          document_id, doc_type, doc_date, recorded_date, reel...

There is no code path in acquisition that reads `document` directly. So:

⚠ FAILURE 1 — a document with no parcel link is unreachable FOREVER. It exists, it is
correct, and it is invisible; it sits in `coverage.py` as NOT YET HELD permanently,
looking exactly like work not yet done. That is why the queue carries `bbls` and why
this job refuses any record that has none.

⚠ FAILURE 2 — a new document on an ALREADY-COMPLETE parcel is never queued. `_INDEX.md`
is a CACHED answer written when the parcel was materialised, and `overnight.py` skips
any parcel whose manifest shows nothing outstanding. Updating the specification does not
reopen a closed parcel — the manifest must be invalidated.

⚠ AND n_docs IS NOT DECORATION. The pool filters and orders on it, so a parcel whose
count was not raised is still ranked on a stale number and may fall outside the band.
This recomputes the counts from `parcel_document` rather than incrementing, because an
increment is wrong the moment the same delta is applied twice.

⚠ WRITE UNDER WAL, WHICH IS ALREADY SET ON THE FILE. In `delete` mode a writer takes an
exclusive lock on the whole database and the continuously-reading walk collides with the
delta as the NORMAL case, not a rare race.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP
import keys as K

QUEUE = HERE / "_live_delta_queue.jsonl"
REPORT = HERE / "_live_land.tsv"


def iso(s):
    """'8/13/2026 8:55:13 AM' or '3/1/2026' -> '2026-08-13'. The table stores
    ISO dates as TEXT and every existing row is ISO; a stray M/D/YYYY would sort
    wrong in `first_date`/`last_date` and in `ix_doc_date`."""
    if not s:
        return None
    d = s.split()[0]
    try:
        m, day, y = (int(x) for x in d.split("/"))
        return f"{y:04d}-{m:02d}-{day:02d}"
    except (ValueError, TypeError):
        return None


def load_queue():
    if not QUEUE.exists():
        sys.exit(f"  no queue at {QUEUE.name} — run live_delta.py --write-queue first")
    recs, orphans, malformed = {}, 0, []
    with QUEUE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            # ⚠ VALIDATE THE KEY AT THE BOUNDARY. A MIME multipart closing
            # boundary reached `document` once (found 2026-08-19); it was not in
            # any Richmond index file, so this path is the likelier origin. The
            # parser hands back whatever the page contained — this is where that
            # stops being a document id.
            try:
                r["doc_id"] = K.document_id(r.get("doc_id"))
            except ValueError as e:
                if len(malformed) < 20:
                    malformed.append(str(e)[:120])
                continue
            # ⚠ TWO reach paths now: parcel (bbl) OR party (name). A record with
            # NEITHER is still refused - it would land permanently unreachable.
            # 37.6% of personal property has no parcel and lands by party alone.
            if not r.get("bbls") and not r.get("parties"):
                orphans += 1
                continue
            prev = recs.get(r["doc_id"])
            if prev:                  # same doc seen under several sweeps
                prev["bbls"] = sorted(set(prev.get("bbls") or [])
                                      | set(r.get("bbls") or []))
                if r.get("parties") and not prev.get("parties"):
                    prev["parties"] = r["parties"]
            else:
                recs[r["doc_id"]] = r
    return recs, orphans, malformed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.apply or a.check):
        a.check = True

    recs, orphans, malformed = load_queue()
    bbls = sorted({b for r in recs.values() for b in r["bbls"]})
    links = {(b, d) for d, r in recs.items() for b in r["bbls"]}
    print(f"LIVE DELTA -> SPECIFICATION   {CP.SPEC_DB}")
    print(f"  queued documents  {len(recs):,}")
    print(f"  parcel links      {len(links):,}  across {len(bbls):,} bbls")
    if orphans:
        print(f"  ⚠ {orphans:,} queued records carried NO bbl and are NOT landed — "
              f"landing them would create permanently unreachable documents")
    # denominator printed even at zero: it says the check RAN
    print(f"  malformed document ids rejected: {len(malformed):,}")
    for m in malformed:
        print(f"    ⚠ {m}")

    # ⚠ retrying open, not just locks: the One Touch throws a transient
    # 'unable to open database file' under concurrent I/O (measured 2026-08-19
    # 04:01). connect_spec backs off through it; a final failure exits nonzero
    # so the routine's existing "landing failed - NOT pushing" guard holds and
    # the queue (kept on disk, resumable by construction) lands next run.
    try:
        con = CP.connect_spec(timeout=30)
    except sqlite3.OperationalError as e:
        sys.exit(f"  ⚠ LANDING DEFERRED — spec DB would not open after retries "
                 f"({e}). The queue is untouched; the next run lands it.")
    jm = con.execute("PRAGMA journal_mode").fetchone()[0]
    if jm.lower() != "wal":
        print(f"  ⚠ journal_mode is {jm}, not wal — a writer takes an exclusive "
              f"lock and the walk will collide. Set WAL at a restart.")

    q = con.execute
    before_docs = q("SELECT COUNT(*) FROM document").fetchone()[0]
    before_links = q("SELECT COUNT(*) FROM parcel_document").fetchone()[0]
    before_parcels = q("SELECT COUNT(*) FROM parcel").fetchone()[0]

    have = set()
    for i in range(0, len(recs), 500):
        chunk = list(recs)[i:i + 500]
        marks = ",".join("?" * len(chunk))
        have |= {r[0] for r in q(
            f"SELECT document_id FROM document WHERE document_id IN ({marks})",
            chunk)}
    new_docs = [d for d in recs if d not in have]
    # ⚠ n_docs snapshot BEFORE, so acceptance test 2 can prove each touched
    # parcel's count actually moved rather than trusting "N rows inserted".
    n_before = {}
    for i in range(0, len(bbls), 500):
        chunk = bbls[i:i + 500]
        marks = ",".join("?" * len(chunk))
        n_before.update({r[0]: r[1] for r in q(
            f"SELECT bbl, n_docs FROM parcel WHERE bbl IN ({marks})", chunk)})
    new_bbls = [b for b in bbls if b not in n_before]

    print(f"\n  already in the specification : {len(have):,}")
    print(f"  NEW documents to land        : {len(new_docs):,}")
    print(f"  parcels already known        : {len(n_before):,}")
    print(f"  NEW parcels to create        : {len(new_bbls):,}")

    if a.check:
        print("\n  --check: nothing written.")
        return

    t0 = time.time()
    with con:
        # ⚠ image_state='pending' is the SINGLE image policy (image_policy.py),
        # same as Richmond: the index row is the event, the scan is probed by
        # live_imageprobe.py each daily run until present or TERMINAL_DAYS.
        con.executemany(
            "INSERT OR IGNORE INTO document(document_id, doc_type, doc_date, "
            "recorded_date, amount, reel_yr, reel_nbr, reel_pg, microfilm, "
            "image_state) VALUES (?,?,?,?,?,?,?,?,0,'pending')",
            [(d, recs[d].get("doc_type"), iso(recs[d].get("doc_date")),
              iso(recs[d].get("recorded")), "0", "0", "0", "0")
             for d in new_docs])
        con.executemany(
            "INSERT OR IGNORE INTO parcel(bbl, n_docs, first_date, last_date, "
            "n_microfilm) VALUES (?,0,NULL,NULL,0)", [(b,) for b in new_bbls])
        con.executemany(
            "INSERT OR IGNORE INTO parcel_document(bbl, document_id) VALUES (?,?)",
            sorted(links))
        # party spine: same verbatim-mirror shape as the Socrata parties index
        prows = [(d, x.get("party_type") or "", x.get("name") or "",
                  x.get("address_1"), x.get("address_2"), x.get("city"),
                  x.get("state"), x.get("zip"), x.get("country"))
                 for d, r in recs.items() for x in (r.get("parties") or [])
                 if (x.get("name") or "").strip()]
        con.executemany(
            "INSERT OR IGNORE INTO party_document(document_id, party_type, name,"
            " address_1, address_2, city, state, zip, country)"
            " VALUES (?,?,?,?,?,?,?,?,?)", prows)
        # ⚠ RECOMPUTE, never increment — an increment double-counts on re-run.
        con.executemany(
            "UPDATE parcel SET n_docs = (SELECT COUNT(*) FROM parcel_document pd "
            "  WHERE pd.bbl = parcel.bbl), "
            "first_date = (SELECT MIN(d.recorded_date) FROM parcel_document pd "
            "  JOIN document d ON d.document_id = pd.document_id WHERE pd.bbl = parcel.bbl), "
            "last_date = (SELECT MAX(d.recorded_date) FROM parcel_document pd "
            "  JOIN document d ON d.document_id = pd.document_id WHERE pd.bbl = parcel.bbl) "
            "WHERE bbl = ?", [(b,) for b in bbls])
    print(f"\n  written in {time.time()-t0:.1f}s")

    # ── FAILURE 2: reopen every parcel we touched ──────────────────────────
    reopened = 0
    for b in bbls:
        f = CP.BYPARCEL / b[0] / b[1:6] / b[6:] / "_INDEX.md"
        if f.exists():
            f.unlink()
            reopened += 1
    print(f"  manifests invalidated: {reopened:,} of {len(bbls):,} touched parcels "
          f"(the rest were never materialised)")

    # ── ACCEPTANCE TEST — do not trust the row count ───────────────────────
    print("\n  ACCEPTANCE TEST")
    after_docs = q("SELECT COUNT(*) FROM document").fetchone()[0]
    after_links = q("SELECT COUNT(*) FROM parcel_document").fetchone()[0]
    after_parcels = q("SELECT COUNT(*) FROM parcel").fetchone()[0]

    unlinked = 0
    for i in range(0, len(new_docs), 500):
        chunk = new_docs[i:i + 500]
        marks = ",".join("?" * len(chunk))
        linked = {r[0] for r in q(
            f"SELECT DISTINCT document_id FROM parcel_document "
            f"WHERE document_id IN ({marks})", chunk)}
        unlinked += len(set(chunk) - linked)
    print(f"   1 every new document reachable via parcel_document : "
          f"{'PASS' if unlinked == 0 else f'FAIL — {unlinked:,} orphans'}")

    stale = 0
    for i in range(0, len(bbls), 500):
        chunk = bbls[i:i + 500]
        marks = ",".join("?" * len(chunk))
        for b, n in q(f"SELECT bbl, n_docs FROM parcel WHERE bbl IN ({marks})",
                      chunk):
            if b in n_before and n <= n_before[b]:
                stale += 1
    print(f"   2 touched parcel n_docs increased                  : "
          f"{'PASS' if stale == 0 else f'CHECK — {stale:,} unchanged (already held the doc)'}")

    bad = sum(1 for b in bbls
              if (CP.BYPARCEL / b[0] / b[1:6] / b[6:] / "_INDEX.md").exists())
    print(f"   3 touched manifests absent / reopened              : "
          f"{'PASS' if bad == 0 else f'FAIL — {bad:,} still cached'}")

    grew = after_docs - before_docs
    print(f"   4 specification grew by exactly the new documents  : "
          f"{'PASS' if grew == len(new_docs) else f'FAIL — grew {grew:,}, expected {len(new_docs):,}'}")

    print(f"\n  documents  {before_docs:,} -> {after_docs:,}   ({grew:+,})")
    print(f"  links      {before_links:,} -> {after_links:,}   "
          f"({after_links-before_links:+,})")
    print(f"  parcels    {before_parcels:,} -> {after_parcels:,}   "
          f"({after_parcels-before_parcels:+,})")

    with REPORT.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')}\t{len(recs)}\t{len(new_docs)}"
                f"\t{after_links-before_links}\t{after_parcels-before_parcels}"
                f"\t{unlinked}\t{bad}\n")
    con.close()


if __name__ == "__main__":
    main()
