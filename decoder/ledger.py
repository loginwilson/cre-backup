"""THE ACQUISITION LEDGER — what has been acquired, and what must not be re-asked.

    import ledger
    if ledger.already("2015022400608001"): return          # skip, done
    ...fetch...
    ledger.record(doc_id, mode="image", pages_got=n, storage_path=str(d))
    ledger.flush()                                          # end of run

    python ledger.py --status        # queue depth, by mode
    python ledger.py --verify        # pages on disk vs pages declared

⚠ WITHOUT THIS, A RESTART RE-FETCHES EVERYTHING. `acquisition_pending` is a VIEW
= document_map MINUS source_document, so a document only leaves the queue when a
row lands here. Nothing in the ACRIS path wrote one until 2026-08-14.

⚠ AND THE FAILURE IS SILENT IN BOTH DIRECTIONS. ACRIS serves its "no image"
placeholder as HTTP 200: a request past the last page succeeds, returns a
placeholder, and is indistinguishable from a real page unless the page COUNT
comes from selection. "Fetch until failure" never terminates.

⚠ NEVER GATE ON document_map.no_image. It is TRUE for the total_pages=0
population and FALSE for the total_pages=-1 population though NEITHER has an
image — 8 of 8 sampled -1 documents were sitting in the queue. Gate on THIS
table (acquisition_mode), which is why the 174,142 index-acquired documents were
backfilled before acquisition begins.

⚠ BUFFERED, BUT NEVER LOSSY. Rows batch to keep the fetcher's inner loop free of
network round-trips; flush() is called on every exit path including failure. A
ledger that loses its tail turns a completed fetch into a repeat fetch, which
costs ACRIS budget for nothing.
"""
from __future__ import annotations

import argparse
import atexit
import json
import pathlib
import sys
import threading
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
ENV = pathlib.Path(r"C:\dev\acris-decoder.env")
JOURNAL = HERE / "_ledger_journal.jsonl"

BATCH = 200
_buf: list[dict] = []
_lock = threading.Lock()
_seen: set[str] | None = None


def _env():
    e = {}
    for line in ENV.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"')
    return e["ACRIS_SUPABASE_URL"].rstrip("/"), e["ACRIS_SUPABASE_SERVICE_KEY"]


URL, KEY = _env()


def _call(path, method="GET", body=None, prefer=None, tmo=120):
    r = urllib.request.Request(f"{URL}/rest/v1/{path}", method=method,
                               data=json.dumps(body).encode() if body else None)
    r.add_header("apikey", KEY)
    r.add_header("Authorization", "Bearer " + KEY)
    if body is not None:
        r.add_header("Content-Type", "application/json")
    if prefer:
        r.add_header("Prefer", prefer)
    with urllib.request.urlopen(r, tmo) if False else urllib.request.urlopen(r, timeout=tmo) as resp:
        raw = resp.read()
        return resp.headers.get("Content-Range"), (json.loads(raw) if raw else None)


def load_done():
    """Every document already acquired — the resume set.

    ⚠ READ ONCE PER RUN, NOT PER DOCUMENT. 17M per-document existence checks is
    the pattern that made the old selection work take hours.
    """
    global _seen
    if _seen is not None:
        return _seen
    _seen = set()
    step, off = 10000, 0
    while True:
        _, rows = _call(f"source_document?select=document_id"
                        f"&order=document_id&limit={step}&offset={off}", tmo=300)
        if not rows:
            break
        _seen |= {r["document_id"] for r in rows}
        if len(rows) < step:
            break
        off += step
    return _seen


def already(doc_id):
    return doc_id in load_done()


def record(doc_id, mode, pages_got=None, storage_path=None, pages_declared=None,
           doc_type=None, no_image=False, no_image_reason=None):
    """Buffer one acquisition. mode is 'image' or 'index'."""
    row = {"document_id": doc_id, "source": "acris", "acquisition_mode": mode,
           "pages_on_disk": pages_got, "pages_declared": pages_declared,
           "storage_path": storage_path, "doc_type": doc_type,
           "no_image": no_image, "no_image_reason": no_image_reason}
    row = {k: v for k, v in row.items() if v is not None}
    with _lock:
        _buf.append(row)
        # ⚠ APPEND-ONLY JOURNAL FIRST. If the process dies between buffering and
        # the network write, the journal still holds it and --replay recovers.
        # The database is the destination; the journal is the receipt.
        with JOURNAL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        full = len(_buf) >= BATCH
    if full:
        flush()


def flush():
    with _lock:
        if not _buf:
            return 0
        batch, _buf[:] = list(_buf), []
    _call("source_document", method="POST", body=batch,
          prefer="resolution=merge-duplicates,return=minimal")
    if _seen is not None:
        _seen.update(r["document_id"] for r in batch)
    return len(batch)


# ⚠ FLUSH ON EVERY EXIT PATH, INCLUDING FAILURE.
atexit.register(flush)


def replay():
    """Push the journal — recovery when a run died before flushing."""
    if not JOURNAL.exists():
        print("  no journal")
        return 0
    rows = [json.loads(l) for l in JOURNAL.read_text(encoding="utf-8").splitlines() if l.strip()]
    seen, uniq = set(), []
    for r in reversed(rows):                     # last write per doc wins
        if r["document_id"] not in seen:
            seen.add(r["document_id"]); uniq.append(r)
    for i in range(0, len(uniq), 500):
        _call("source_document", method="POST", body=uniq[i:i+500],
              prefer="resolution=merge-duplicates,return=minimal")
    print(f"  replayed {len(uniq):,} distinct rows from the journal")
    return len(uniq)


def status():
    # ⚠ PLANNED COUNTS IGNORE THE FILTER. count=planned reads pg_class
    # statistics for the TABLE, so a filtered query returns an estimate of the
    # whole relation — this board reported "acquired · image 1" when the true
    # answer was 0 and nothing had ever fetched an image. Exact counts are used
    # on every filtered query; planned is kept only for the 17M unfiltered
    # tables, where exact times out.
    def n(q, exact=True):
        cr, _ = _call(q, prefer="count=exact" if exact else "count=planned",
                      tmo=300)
        return int(cr.split("/")[1])
    total = n("document_map?select=document_id", exact=False)
    done = n("source_document?select=document_id")
    pend = n("acquisition_pending?select=document_id", exact=False)
    img = n("source_document?select=document_id&acquisition_mode=eq.image")
    idx = n("source_document?select=document_id&acquisition_mode=eq.index")
    print("ACQUISITION LEDGER\n")
    print(f"  document_map          {total:>12,}")
    print(f"  acquired · index      {idx:>12,}   (no image will ever exist)")
    print(f"  acquired · image      {img:>12,}")
    print(f"  ── pending            {pend:>12,}")
    if img == 0:
        print("\n  ⚠ NO IMAGE ACQUISITIONS RECORDED. If a fetch run has happened,"
              "\n    the runner is not calling ledger.record() — and a restart"
              "\n    will re-fetch every document it already has.")
    return 0


def verify(limit=200):
    """Pages on disk vs pages declared, for image-mode rows.

    ⚠ A BYTE COUNT CANNOT TELL A SHORT DOCUMENT FROM A TRUNCATED ONE. The
    expected count comes from selection (document_map.total_pages); it cannot be
    discovered by fetching, because the request past the last page returns a
    placeholder as HTTP 200.
    """
    _, rows = _call(f"source_document?select=document_id,pages_on_disk,"
                    f"pages_declared,storage_path&acquisition_mode=eq.image"
                    f"&limit={limit}")
    if not rows:
        print("  no image-mode rows to verify")
        return 0
    bad = 0
    for r in rows:
        d, got = r.get("pages_declared"), r.get("pages_on_disk")
        p = r.get("storage_path")
        on_disk = len(list(pathlib.Path(p).glob("*.tif"))) if p and pathlib.Path(p).exists() else None
        if d is not None and (got != d or (on_disk is not None and on_disk != d)):
            bad += 1
            print(f"    ⚠ {r['document_id']}  declared {d}  recorded {got}  "
                  f"on disk {on_disk}")
    print(f"\n  checked {len(rows):,} · mismatches {bad}"
          f"{'   ✅' if bad == 0 else '   ⚠ DO NOT PROCEED TO EXTRACTION'}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    if a.replay:
        raise SystemExit(replay() and 0)
    if a.verify:
        raise SystemExit(verify())
    raise SystemExit(status())
