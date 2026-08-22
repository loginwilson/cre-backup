"""RECORD THE IMAGE-LESS DOCUMENTS AS ACQUIRED-BY-INDEX.

    python ledger_backfill.py --check    # look only
    python ledger_backfill.py --apply    # write source_document

⚠ THESE DOCUMENTS ARE ALREADY ACQUIRED. Their index was pulled in full on
2026-08-14 (index_noimage.jsonl, 174,142 documents, 360 MB) and no image of them
will ever exist. Until they are recorded here they sit in `acquisition_pending`,
which is exactly where the image runner takes its work from.

⚠ WHAT THAT COSTS IF IT IS NOT DONE. Measured 2026-08-14: 8 of 8 sampled
documents with total_pages = -1 carried `no_image = false` in document_map and
ALL EIGHT were in acquisition_pending. The runner would request an image for
every one, and ACRIS serves its "no image" placeholder as **HTTP 200** — so
nothing errors, nothing retries, and the run records a successful fetch of a
placeholder ~174,000 times.

⚠ AND `no_image` IN document_map IS NOT A SAFE GATE. It is true for the
total_pages = 0 population and false for the total_pages = -1 population, though
neither has an image. Gate on the ledger, not on that flag.

⚠ THE REASON IS RECOVERED FROM total_pages, NOT COPIED FROM THE PULL. The
no-image pull wrote `acris_placeholder_returned` for all 174,142, flattening a
distinction that document_map still holds: 0 means ACRIS answered with a
placeholder, -1 means the microfilm era where no image was ever scanned. Writing
the flat value would launder a real difference into the ledger permanently.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
SRC = HERE / "index_noimage.jsonl"
ENV = pathlib.Path(r"C:\dev\acris-decoder.env")

LOOKUP_BATCH = 300     # ids per document_map lookup — URL length bound
WRITE_BATCH = 1000     # rows per upsert


def env():
    e = {}
    for line in ENV.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            e[k.strip()] = v.strip().strip('"')
    return e["ACRIS_SUPABASE_URL"].rstrip("/"), e["ACRIS_SUPABASE_SERVICE_KEY"]


URL, KEY = env()


def call(path, method="GET", body=None, prefer=None, tmo=180):
    r = urllib.request.Request(f"{URL}/rest/v1/{path}", method=method,
                               data=json.dumps(body).encode() if body else None)
    r.add_header("apikey", KEY)
    r.add_header("Authorization", "Bearer " + KEY)
    if body is not None:
        r.add_header("Content-Type", "application/json")
    if prefer:
        r.add_header("Prefer", prefer)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(r, timeout=tmo) as resp:
                raw = resp.read()
                return (resp.headers.get("Content-Range"),
                        json.loads(raw) if raw else None)
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


def load_local():
    """The 174,142 image-less documents, with the index fields worth keeping."""
    out = []
    with SRC.open(encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)["document"]
            m = d.get("master") or {}
            rd = (m.get("recorded_datetime") or "")[:10] or None
            idt = (m.get("document_date") or "")[:10] or None
            out.append({
                "document_id": d["document_id"],
                "source": "acris",
                "doc_type": m.get("doc_type"),
                "recorded_date": rd,
                "instrument_date": idt,
                "acquisition_mode": "index",
                "no_image": True,
                # reason filled from document_map.total_pages below
                "no_image_reason": None,
                "pages_declared": 0,
                "pages_on_disk": 0,
            })
    return out


def true_reasons(ids):
    """total_pages per id, straight from document_map. 0 vs -1 is the fact."""
    got = {}
    for i in range(0, len(ids), LOOKUP_BATCH):
        chunk = ids[i:i + LOOKUP_BATCH]
        q = ",".join(chunk)
        _, rows = call(f"document_map?select=document_id,total_pages"
                       f"&document_id=in.({q})")
        for r in rows or []:
            got[r["document_id"]] = r.get("total_pages")
        if (i // LOOKUP_BATCH) % 40 == 0:
            print(f"    resolved {len(got):,}/{len(ids):,}", flush=True)
    return got


REASON = {0: "acris_placeholder_returned", -1: "microfilm_era_never_scanned"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t0 = time.time()

    print("LEDGER BACKFILL — image-less documents\n")
    cr, _ = call("source_document?select=document_id&limit=1", prefer="count=exact")
    before = int(cr.split("/")[1])
    print(f"  source_document holds {before:,} rows before\n")

    rows = load_local()
    print(f"  local no-image set        {len(rows):,}")

    ids = [r["document_id"] for r in rows]
    tp = true_reasons(ids)
    print(f"  resolved in document_map  {len(tp):,}")

    missing = [i for i in ids if i not in tp]
    if missing:
        # ⚠ REPORT, NEVER SILENTLY DROP. A document we hold an index for but
        # which is absent from the map is a specification gap, not a rounding
        # error.
        print(f"  ⚠ NOT IN document_map     {len(missing):,}  e.g. {missing[:3]}")

    counts = {}
    for r in rows:
        v = tp.get(r["document_id"])
        r["no_image_reason"] = REASON.get(v, f"unexpected_total_pages_{v}")
        counts[r["no_image_reason"]] = counts.get(r["no_image_reason"], 0) + 1
    print("\n  REASON, recovered from total_pages:")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"    {k:<34} {v:>9,}")

    if not a.apply:
        print("\n  (check only — re-run with --apply to write)")
        return 0

    print("\n  writing...", flush=True)
    written = 0
    for i in range(0, len(rows), WRITE_BATCH):
        batch = [r for r in rows[i:i + WRITE_BATCH]
                 if r["document_id"] in tp]
        if not batch:
            continue
        call("source_document", method="POST", body=batch,
             prefer="resolution=merge-duplicates,return=minimal")
        written += len(batch)
        if (i // WRITE_BATCH) % 20 == 0:
            print(f"    {written:,}/{len(rows):,}", flush=True)

    cr, _ = call("source_document?select=document_id&limit=1", prefer="count=exact")
    after = int(cr.split("/")[1])
    print(f"\n  source_document {before:,} -> {after:,}  (+{after - before:,})")

    # ⚠ THE PROOF IS THAT THE QUEUE SHRANK BY THE SAME NUMBER. "It did not
    # error" is not evidence: a PostgREST failure can return an empty body, and
    # an empty body reads as success.
    ok = (after - before) == written
    print(f"  wrote {written:,} · table grew {after - before:,} · "
          f"{'MATCH' if ok else '⚠ MISMATCH — DO NOT TRUST THIS RUN'}")
    print(f"\n  ({time.time() - t0:.0f}s)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
