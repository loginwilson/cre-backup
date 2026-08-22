"""HOW MANY PAGES DOES EACH DOCUMENT HAVE? The lookup that removes a request per document.

    ACRIS_CORPUS_ROOT=D:/acris python build_pagecounts.py --build

⚠ WHY. The fetch loop finds a document's end by asking for one page too many and getting
ACRIS's placeholder back. That terminal probe costs ONE REQUEST PER DOCUMENT — ~17M
across the corpus, about 10% of every request we will ever make. `acris_maps.jsonl`
already carries `hid_TotalPages`, so the end is knowable without asking.

⚠ VALIDATED BEFORE TRUSTED, AGAINST WORK ALREADY DONE. Compared to 233,712 documents
whose true page count we had actually fetched:

    exact match     233,553   99.93%
    map TOO LOW           0    0.00%   <- the only dangerous direction. NONE.
    map too high        159    0.07%   <- costs one wasted request, harmless

A wrong-low count would silently truncate a document and nothing downstream could tell
the difference. Zero in 233,712 is the reason this is safe to switch on.

⚠ BUILT ON THE NVMe, READ FROM ANYWHERE. 17M keyed inserts onto the USB corpus drive is
the mistake that cost 40 minutes on 2026-08-17. Build local, then move the finished file.

⚠ THE PLACEHOLDER REMAINS THE AUTHORITY. `expect` is a HINT that lets the loop stop
without probing; if the placeholder appears first, that is the true end and the document
is complete regardless of what the map said.
"""
from __future__ import annotations

import argparse, json, os, pathlib, sqlite3, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
MAPS = ("acris_maps.jsonl", "docmaps.jsonl", "census_maps.jsonl")


def build(dest, tmp):
    con = sqlite3.connect(tmp)
    con.executescript("PRAGMA page_size=8192; PRAGMA temp_store=MEMORY;")
    con.execute("CREATE TABLE IF NOT EXISTS pages(doc_id TEXT, n INT)")
    con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;"
                      " PRAGMA cache_size=-524288;")
    con.execute("DELETE FROM pages")
    t0 = time.time(); n = kept = 0; buf = []
    for m in MAPS:
        p = HERE / m
        if not p.exists():
            continue
        with open(p, "rb") as f:
            for line in f:
                n += 1
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                did = d.get("doc_id") or d.get("document_id")
                tp = d.get("hid_TotalPages")
                if not did or tp is None:
                    continue
                try:
                    tp = int(tp)
                except (TypeError, ValueError):
                    continue
                if tp <= 0:          # 0 or -1 == image-less; the index is its record
                    continue
                buf.append((did, tp)); kept += 1
                if len(buf) >= 200_000:
                    con.executemany("INSERT INTO pages VALUES (?,?)", buf)
                    con.commit(); buf.clear()
                    print(f"    {n:,} lines · {kept:,} counts…", flush=True)
    if buf:
        con.executemany("INSERT INTO pages VALUES (?,?)", buf)
    con.commit()
    print(f"  {n:,} map lines -> {kept:,} page counts   {time.time()-t0:.0f}s")
    print("  indexing…", flush=True)
    # ⚠ index AFTER the load, never during — the lesson from parcel_spec_db.py
    con.execute("CREATE INDEX IF NOT EXISTS ix_pages_doc ON pages(doc_id)")
    con.commit()
    d = con.execute("select count(*), count(distinct doc_id) from pages").fetchone()
    print(f"  {d[0]:,} rows · {d[1]:,} distinct documents")
    con.close()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    pathlib.Path(tmp).replace(dest)
    print(f"  -> {dest}  ({dest.stat().st_size/1e9:.2f} GB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--tmp", default="./_pagecounts.tmp.db")
    a = ap.parse_args()
    import corpus_paths as CP
    dest = CP.SPEC / "page_counts.db"
    if a.build:
        build(dest, a.tmp)
    else:
        print(f"  {dest} exists: {dest.exists()}")


if __name__ == "__main__":
    main()
