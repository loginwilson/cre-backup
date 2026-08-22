"""STORE THE IMAGES, OR STORE THE COORDINATES? Size both, then the answer is arithmetic.

Two candidate architectures:

  A  7TB drive, every page keyed by document id. OCR sweeps it continuously and
     writes a master coordinate extract. The model second-passes flagged boxes.
  B  No storage. Map -> fetch page -> OCR -> model. Nothing kept.

⚠ B FETCHES EVERY FLAGGED PAGE TWICE AND THAT IS THE WHOLE ARGUMENT. The model
cannot read a coordinate; it needs the pixels. Discard the image after OCR and
the second pass has to re-fetch it — doubling the ONLY scarce resource in this
system. Acquisition is rate-limited; OCR is free CPU on a laptop. Paying twice
in the scarce currency to save the abundant one is backwards.

But that is not the interesting part. The interesting part is that the OCR
extract and the images are VERY different sizes, and the extract is the thing
that never needs re-making:

  IMAGES      consumable   needed only to LOOK at a box the extract already found
  EXTRACT     durable      every word + box on every page, queryable forever

A new function scanner invented next year runs over the extract in minutes with
zero fetches. That is what makes the extract the asset and the images the cache.

So this measures:
  1. bytes/page of the coordinate extract -> full-corpus extract size
  2. fraction of PAGES that flag at least one frame -> how many images are
     actually needed, which is the real size of the drive

    python extract_size.py
"""
import collections
import gzip
import json
import pathlib
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OCR = pathlib.Path("sample_ocr")
CORPUS_PAGES = 148_628_961          # measured from the map, all 16,980,823 docs
CORPUS_DOCS = 16_980_823
TB = 1024 ** 4
GB = 1024 ** 3

# ⚠ FRAMES FROM SEVERAL FUNCTIONS, NOT ONE. The page-level hit rate is the
# fraction of pages ANY scanner wants to look at. Measuring envelope alone
# understates the drive by however many functions exist — and a page that flags
# for debt still has to be on the disk.
FUNCS = {
    "envelope": [r"floor\s+area", r"development\s+rights?", r"zoning\s+lot",
                 r"zoning\s+resolution", r"lot\s+area", r"air\s+rights?",
                 r"party\s+wall", r"light\s+and\s+air", r"special\s+permit",
                 r"restrictive\s+declaration", r"single\s+ownership",
                 r"certificate\s+of\s+occupancy", r"section\s+\d{2}-\d{2,3}"],
    "title":    [r"part(?:y|ies)\s+in\s+interest", r"fee\s+simple",
                 r"subject\s+to", r"covenants?\s+running", r"of\s+record",
                 r"metes\s+and\s+bounds", r"beginning\s+at\s+a\s+point",
                 r"together\s+with\s+all"],
    "capital":  [r"principal\s+(?:sum|amount)", r"promissory\s+note",
                 r"consolidat", r"spreader", r"mortgage\s+recording\s+tax",
                 r"maturity\s+date", r"interest\s+rate", r"building\s+loan"],
    "transfer": [r"grantor", r"grantee", r"consideration",
                 r"real\s+property\s+transfer\s+tax", r"bargain\s+and\s+sale",
                 r"quitclaim", r"does\s+hereby\s+grant"],
    "encumb":   [r"lien", r"mechanic'?s?\s+lien", r"restrictive\s+covenant",
                 r"right\s+of\s+way", r"encroach", r"license\s+agreement"],
}
RX = {k: [re.compile(p, re.I) for p in v] for k, v in FUNCS.items()}


def main():
    files = sorted(OCR.glob("*.json.gz"))
    n_pages = n_words = 0
    gz_bytes = raw_bytes = 0
    flagged = collections.Counter()      # func -> pages
    any_flag = 0
    per_page_funcs = collections.Counter()

    for p in files:
        gz_bytes += p.stat().st_size
        try:
            rows = json.load(gzip.open(p, "rt", encoding="utf-8"))
        except Exception:
            continue
        raw_bytes += len(json.dumps(rows).encode())
        for r in rows:
            n_pages += 1
            n_words += len(r["words"])
            text = " ".join(w["t"] for w in r["words"])
            hit = [f for f, pats in RX.items() if any(x.search(text) for x in pats)]
            for f in hit:
                flagged[f] += 1
            if hit:
                any_flag += 1
            per_page_funcs[len(hit)] += 1

    print(f"  {len(files)} documents · {n_pages:,} pages · {n_words:,} words\n")

    # ── 1 · the extract ──────────────────────────────────────────────────
    bpp_gz = gz_bytes / n_pages
    bpp_raw = raw_bytes / n_pages
    print(f"  ── 1 · COORDINATE EXTRACT (every word + box + confidence) ──")
    print(f"    {'':<26}{'bytes/page':>12}{'full corpus':>16}")
    print(f"    {'gzipped json':<26}{bpp_gz:>12,.0f}"
          f"{bpp_gz * CORPUS_PAGES / GB:>13,.0f} GB")
    print(f"    {'raw json':<26}{bpp_raw:>12,.0f}"
          f"{bpp_raw * CORPUS_PAGES / GB:>13,.0f} GB")
    print(f"\n    vs 14.3 TB of images  ->  extract is "
          f"{14.3 * TB / (bpp_gz * CORPUS_PAGES):.0f}x smaller")

    # ── 2 · how many images are actually needed ──────────────────────────
    print(f"\n  ── 2 · PAGES THAT FLAG (any function wants a look) ──")
    print(f"    {'function':<14}{'pages':>9}{'rate':>9}")
    for f in FUNCS:
        print(f"    {f:<14}{flagged[f]:>9,}{flagged[f]/n_pages*100:>8.1f}%")
    rate = any_flag / n_pages
    print(f"    {'ANY':<14}{any_flag:>9,}{rate*100:>8.1f}%")

    print(f"\n    {'pages flagging N functions':<32}")
    for k in sorted(per_page_funcs):
        print(f"      {k} function(s){'':<10}{per_page_funcs[k]:>8,}"
              f"{per_page_funcs[k]/n_pages*100:>7.1f}%")

    print(f"\n  ── 3 · THE DRIVE ──")
    per_page_img = 14.3 * TB / CORPUS_PAGES
    print(f"    mean image                {per_page_img/1024:>10,.0f} KB/page")
    print(f"    ALL pages                 {14.3:>10,.1f} TB")
    print(f"    only FLAGGED pages        {14.3*rate:>10,.1f} TB   "
          f"({rate*100:.1f}%)")
    print(f"    extract (keep forever)    {bpp_gz*CORPUS_PAGES/TB:>10,.2f} TB")

    print(f"\n  ⚠ THE FLAGGED FRACTION IS A CEILING, NOT A PLAN. You cannot know a")
    print(f"    page flags until you have OCR'd it, and you cannot OCR it without")
    print(f"    fetching it. So the drive still sees every page ONCE. What the")
    print(f"    rate decides is how much you must KEEP after the sweep.")


if __name__ == "__main__":
    main()
