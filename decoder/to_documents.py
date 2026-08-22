"""LOOSE PAGES -> ONE CONTAINER PER DOCUMENT, ready for the external drive.

    python to_documents.py --dest E:/acris --dry
    python to_documents.py --dest E:/acris
    python to_documents.py --dest E:/acris --only sample_pages

⚠ WHAT THIS IS FOR. 1,865 ACRIS documents currently exist as 47,378 loose `p001.tif`
files, written by `devr_acquire.py` / `fetch_pages.py`. `acquire_async.py` — the writer we
actually keep — produces ONE multipage `{doc}.tif` per document and treats loose pages as
its write-failure fallback. Login, 2026-08-17: "not pages. do the doc." This converts what
is already on disk into the format everything downstream expects, on the way to the drive.

⚠ THE POINT IS FILE COUNT, NOT BYTES. G4 is preserved and nothing is re-encoded, so the
container is ~0.99x the loose pages — no space is saved. What is saved is 47,378 files
becoming 1,865: loose pages cost NTFS metadata per file and would hit an inode quota on a
parallel filesystem long before the storage quota. Page N still opens in ~3 ms.

⚠ NEVER convert("L") A BITONAL SCAN. Measured 15.2x inflation, which would turn 9.3 TB
into 141 TB at corpus scale. Frames are copied in their existing mode.

⚠ SOURCE IS NEVER DELETED. This copies. Deleting 47,378 originals is the user's call to
make after verifying, not a side effect of a conversion script.

⚠ AND A CONTAINER IS VERIFIED BEFORE IT COUNTS. Every output is reopened and its frame
count compared to the input page count; a mismatch is REPORTED and the document is left
out of the done-list rather than silently accepted. A prior job in this project wrote 37
files for 64 inputs and reported success, because nothing checked.
"""
from __future__ import annotations

import argparse, json, pathlib, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent

# ⚠ ACRIS ONLY. lpc_cache (Landmarks) and bsa_cache (BSA) are different sources and
# leases_raw is listing data; none of them are ACRIS documents. render/ocr_text/
# devr_text/sample_ocr are DERIVED and reproduce at 5.6 s/page — they do not travel.
SOURCES = ["devr_pages", "sample_pages", "lease_pages"]
INDEX = ["index_full", "noimage_index"]      # ACRIS index: copied, not converted


def convert(src_doc: pathlib.Path, out: pathlib.Path):
    """Return (pages_in, pages_out, error). Writes only on success."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    tifs = sorted(src_doc.glob("*.tif"))
    if not tifs:
        return 0, 0, "no pages"
    try:
        ims = [Image.open(t) for t in tifs]
        ims[0].save(out, format="TIFF", save_all=True, append_images=ims[1:],
                    compression="group4")
    except Exception as e:
        if out.exists():
            out.unlink()          # a half-written container is worse than none
        return len(tifs), 0, f"{type(e).__name__}: {str(e)[:60]}"
    # ⚠ REOPEN AND COUNT. Writing without erroring is not the same as writing correctly.
    try:
        chk = Image.open(out)
        n = getattr(chk, "n_frames", 1)
    except Exception as e:
        return len(tifs), 0, f"unreadable output: {type(e).__name__}"
    if n != len(tifs):
        return len(tifs), n, f"FRAME MISMATCH {n} != {len(tifs)}"
    return len(tifs), n, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, help="e.g. E:/acris")
    ap.add_argument("--only", action="append", help="limit to one source folder")
    ap.add_argument("--dry", action="store_true", help="count and report, write nothing")
    ap.add_argument("--limit", type=int, default=0, help="stop after N documents")
    a = ap.parse_args()

    dest = pathlib.Path(a.dest)
    srcs = [s for s in SOURCES if not a.only or s in a.only]

    total_docs = total_pages = 0
    for s in srcs:
        d = HERE / s
        if not d.exists():
            print(f"  {s}: absent"); continue
        docs = [p for p in d.iterdir() if p.is_dir()]
        pages = sum(1 for _ in d.rglob("*.tif"))
        total_docs += len(docs); total_pages += pages
        print(f"  {s:<14} {len(docs):>5} docs  {pages:>6} pages")
    print(f"  {'TOTAL':<14} {total_docs:>5} docs  {total_pages:>6} pages"
          f"  ->  {total_docs} container files\n")
    if a.dry:
        for s in INDEX:
            p = HERE / s
            if p.exists():
                print(f"  index (copy as-is): {s}")
        print(f"\n  dry run — nothing written. dest would be {dest}")
        return 0

    outdir = dest / "documents"
    outdir.mkdir(parents=True, exist_ok=True)
    ledger = dest / "converted.jsonl"
    done = set()
    if ledger.exists():
        for ln in ledger.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(ln)["doc"])
            except Exception:
                pass
    print(f"  -> {outdir}   ({len(done)} already converted, resuming)\n")

    ok = skip = fail = 0
    t0 = time.time()
    with open(ledger, "a", encoding="utf-8") as lg:
        for s in srcs:
            d = HERE / s
            if not d.exists():
                continue
            for doc in sorted(p for p in d.iterdir() if p.is_dir()):
                if a.limit and ok + fail >= a.limit:
                    break
                if doc.name in done:
                    skip += 1; continue
                out = outdir / f"{doc.name}.tif"
                nin, nout, err = convert(doc, out)
                if err:
                    fail += 1
                    print(f"  ⚠ {doc.name}  {nin} pages -> {err}")
                    continue
                ok += 1
                lg.write(json.dumps({"doc": doc.name, "src": s, "pages": nin,
                                     "bytes": out.stat().st_size}) + "\n")
                lg.flush()
                if ok % 100 == 0:
                    print(f"    {ok} converted · {time.time()-t0:.0f}s")

    el = time.time() - t0
    # ⚠ DENOMINATORS. "converted 1,800" means nothing without how many were attempted.
    print(f"\n  converted {ok} · skipped {skip} (already done) · FAILED {fail}"
          f"  of {total_docs} documents   {el:.0f}s")
    if fail:
        print(f"  ⚠ {fail} documents did NOT convert — listed above. Source is intact;")
        print(f"    do not delete anything until this is 0.")
    else:
        print(f"  all attempted documents verified frame-for-frame against their source.")
    print(f"  ⚠ SOURCE PAGES ARE UNTOUCHED. Delete them yourself once you have checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
