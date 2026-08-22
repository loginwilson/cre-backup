"""INDEX ACQUISITION FOR THE EVENTS THAT HAVE NO DOCUMENT.

These are not a class to skip. A release of estate tax lien is still an
encumbrance event and the parcel history has to report it. For a document with
no scanned image the index is not the first chapter — it is the whole record.

⚠ THE INDEX IS A SPINE, NOT A SOURCE — AND THIS FILE IS THE ONE EXCEPTION.
Measured 2026-08-10 on the live index:

    DEED   25.7% carry a document_amt      74.3% read as $0
    EASE    7.5%
    DEVR   49.9%

Manhattan deeds do not sell for nothing, so a 0 does not mean "no
consideration" — it means "not captured", and nothing in the index
distinguishes the two. Reading values off the index would inject a silent
error into three quarters of all deeds. So everywhere else, facts come from
documents. HERE there is no document, so the index is all there is, and that
has to be stamped on every claim it produces (evidence='index') so the
difference is never lost downstream.

⚠ WHY THIS IS CHEAP. The whole index is 100.8M rows / 12.3 GB raw. This subset
is ~1.50% of documents — measured over 9.2M mapped, projecting to ~255,640
citywide — and 78% of them are a single type (RTXL). Roughly 100 MB raw, and
gzip runs 11.1x on this data, so about 10 MB on disk.

⚠ SOCRATA IS A DIFFERENT HOST FROM ACRIS (data.cityofnewyork.us vs
a836-acris.nyc.gov) with an independent budget, so this deliberately does NOT
take the ACRIS lock and runs alongside the map. It is polite anyway: bulk.py's
measured 5 workers, not 8.

⚠ RESUMABLE, BECAUSE THE MAP IS STILL RUNNING. The no-image population grows as
mapping advances. Every run records which ids it has already pulled, so
re-running after the map moves picks up only the new ones. An earlier fetcher in
this project accumulated in memory and wrote once at the end; 762 results were
in flight and 321 on disk when it was interrupted.
"""
import collections
import gzip
import json
import pathlib
import sys
import time

import bulk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAPS = ("acris_maps.jsonl", "docmaps.jsonl", "census_maps.jsonl")
# ⚠ WRITE INTO THE CORPUS, NOT THE CWD. A relative path here creates a SECOND
# noimage_index beside the code, finds no _done.json, and re-pulls all 174,142 —
# duplicating 138,867 records already held on the drive and hiding the real 35,275 gap.
import os as _os
_root = pathlib.Path(_os.environ.get("ACRIS_CORPUS_ROOT", "."))
_corpus = _root / "01-specification" / "index" / "noimage_index"
OUT = _corpus if _corpus.exists() else pathlib.Path("noimage_index")
DONE = OUT / "_done.json"

DATASETS = [
    ("master", "bnx9-e6tj"),
    ("legals", "8h5j-fqxa"),
    ("parties", "636b-3b5g"),
    ("refs", "pwkr-dpni"),
    # ⚠ REMARKS IS THE POINT, NOT AN EXTRA. It is the only field that says WHY
    # there is no image. A remark of the form "BOOK/PAGES: 217/128" means the
    # paper exists in the physical archive and was never scanned, which is a
    # different fact from "does not exist" — and only the remark separates them.
    ("remarks", "9p4w-7npp"),
]


def noimage_ids():
    """Every mapped document whose page count is not positive.

    ⚠ THREE STATES, NOT TWO. total_pages > 0 normal; == 0 no image; < 0 also no
    image (microfilm-era WILL/MMTG/MAPS). Two bugs came from reading this as a
    plain positive integer: `if not total` scored 0 a parse failure and stalled
    an overnight run, `if total` treated -1 as truthy and wrote 19,570
    instrument ranges of [1,-1]. Test the sign explicitly, always.
    """
    ids, kinds = {}, collections.Counter()
    for name in MAPS:
        p = pathlib.Path(name)
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                t = r.get("hid_TotalPages")
                if t is None or t > 0:
                    continue
                ids[r["doc_id"]] = r.get("doc_type")
                kinds[r.get("doc_type")] += 1
    return ids, kinds


def write_gz(path, rows):
    """Append rows as gzipped jsonl. Measured 11.1x on index data."""
    with gzip.open(path, "at", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")


def main():
    OUT.mkdir(exist_ok=True)
    ids, kinds = noimage_ids()
    done = set(json.loads(DONE.read_text())) if DONE.exists() else set()
    todo = sorted(set(ids) - done)

    print(f"{len(ids):,} image-less documents found in the map")
    print(f"{len(done):,} already pulled · {len(todo):,} to do")
    if kinds:
        print("\n  top types:")
        for k, v in kinds.most_common(6):
            print(f"    {str(k):<10}{v:>9,}")
    if not todo:
        print("\n  nothing to do.")
        return

    print()
    t0 = time.time()
    for name, ds in DATASETS:
        s = time.time()
        rows = bulk.socrata_in(ds, "document_id", todo)
        write_gz(OUT / f"{name}.jsonl.gz", rows)
        print(f"  {name:<9}{len(rows):>10,} rows   {time.time()-s:>6.1f}s", flush=True)

    # ⚠ CHECKPOINT ONLY AFTER EVERY DATASET LANDED. Marking ids done between
    # datasets would leave a document recorded as pulled with its parties or its
    # remark missing, and nothing would ever go back for them.
    DONE.write_text(json.dumps(sorted(done | set(todo))))

    sz = sum(p.stat().st_size for p in OUT.glob("*.jsonl.gz"))
    print(f"\n  {len(todo):,} documents in {time.time()-t0:.0f}s")
    print(f"  {sz/1e6:.1f} MB on disk (gzipped)")
    print(f"\n  re-run after the map advances to pick up new image-less documents.")


if __name__ == "__main__":
    main()
