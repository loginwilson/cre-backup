"""HARVEST — crop, verify, then delete the pages. Storage is the constraint.

⚠ THE ARITHMETIC THAT MAKES THIS NON-OPTIONAL, measured on lot 49:

    pages_out   1,659 files   220.4 MB   avg 130 KB
    proofs         52 files     2.1 MB   avg  39 KB

    across 1,164,820 parcels ->  pages  256.7 TB
                                 crops    2.4 TB

Lot 49 is an outlier — 102 documents against a median parcel's 12 — so the
real citywide crop figure is nearer 300 GB. Either way the shape is the same:
KEEPING PAGES IS IMPOSSIBLE AND KEEPING CROPS IS ROUTINE.

The page image is SCAFFOLDING. The crop is the DELIVERABLE. A claim without
its crop is an assertion; a claim with one is evidence that survives the
deletion of everything it came from.

⚠ THE INVARIANT, AND IT IS THE ONLY THING PROTECTING THE LEDGER:

    NEVER DELETE A PAGE ANY CLAIM CITES UNTIL THAT CLAIM HAS A CROP.

Delete a page early and the claim becomes unfalsifiable — it still reads as
sourced, cites a document and a page, and can never again be checked. That is
strictly worse than having no claim at all. Today a single crop caught a page
cite that was off by one AND reversed a conclusion I had already reported. If
that page had been swept first, the error would have been permanent.

⚠ SECOND GATE: never delete a document an agent may still be reading.

    python harvest.py --plan     what would happen, nothing touched
    python harvest.py --crop     cut crops for claims on finished documents
    python harvest.py --sweep    delete pages ONLY where every claim is
                                 backed by a verified crop
"""
import hashlib
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import claims as K
import reads as R

PAGES = pathlib.Path("pages_out")
PROOFS = pathlib.Path("proofs")
IMG = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
MIN_CROP_BYTES = 2_000          # below this a crop is blank or clipped
DONE = 0.60                     # page-coverage bar, matches ledger.py


def crop_key(doc, page):
    return hashlib.md5(f"{doc}|{page}".encode()).hexdigest()[:16]


def crop_path(doc, page):
    return PROOFS / f"{crop_key(doc, page)}.png"


def page_file(doc, page):
    p = PAGES / doc / f"{page}.png"
    return p if p.exists() else None


def doc_pages(doc):
    d = PAGES / doc
    if not d.is_dir():
        return []
    return sorted(f for f in d.iterdir()
                  if f.is_file() and f.suffix.lower() in IMG)


def state():
    """Per document: claims, cited pages, crop status, read coverage."""
    by_doc = {}
    for c in K.rows():
        d = c["document_id"]
        by_doc.setdefault(d, []).append(c)
    out = {}
    for d in sorted({p.name for p in PAGES.iterdir() if p.is_dir()}):
        cs = by_doc.get(d, [])
        n_pages = len(doc_pages(d))
        opened = len(R.pages_opened(d))
        cited = sorted({c["page"] for c in cs if c["page"]})
        have = [p for p in cited
                if crop_path(d, p).exists()
                and crop_path(d, p).stat().st_size >= MIN_CROP_BYTES]
        out[d] = dict(doc=d, pages=n_pages, opened=opened,
                      cov=(opened / n_pages) if n_pages else 0.0,
                      claims=len(cs), cited=cited, cropped=have,
                      missing=[p for p in cited if p not in have])
    return out


def sweepable(s):
    """A document may be swept only when BOTH gates pass."""
    if s["cov"] < DONE:
        return False, "still being read — coverage below bar"
    if not s["claims"]:
        return False, "no claims — reading it produced nothing yet"
    if s["missing"]:
        return False, f"{len(s['missing'])} cited page(s) have no crop"
    return True, "every cited page is crop-backed"


def size_of(paths):
    return sum(p.stat().st_size for p in paths if p.exists())


def cmd_plan():
    st = state()
    ready, blocked = [], []
    for d, s in st.items():
        ok, why = sweepable(s)
        (ready if ok else blocked).append((d, s, why))

    print("HARVEST PLAN — nothing is touched by this command\n")
    print(f"  READY TO SWEEP   {len(ready)} documents")
    freed = 0
    for d, s, why in ready:
        b = size_of(doc_pages(d))
        freed += b
        print(f"    {d}  {s['pages']:>3} pages  {b/1e6:>5.1f} MB  "
              f"{len(s['cropped'])} crops hold {s['claims']} claims")
    print(f"    -> {freed/1e6:.1f} MB reclaimable\n")

    print(f"  ⚠ BLOCKED        {len(blocked)} documents")
    need_crop = [x for x in blocked if "no crop" in x[2]]
    still_read = [x for x in blocked if "still being read" in x[2]]
    barren = [x for x in blocked if "produced nothing" in x[2]]
    print(f"      {len(need_crop):>3} need crops cut  "
          f"({sum(len(s['missing']) for _, s, _ in need_crop)} pages)")
    print(f"      {len(still_read):>3} still being read — ⚠ DO NOT TOUCH, "
          f"agents may hold them")
    print(f"      {len(barren):>3} opened but yielded no claim yet")
    held = size_of([f for d, s, _ in blocked for f in doc_pages(d)])
    print(f"      {held/1e6:.1f} MB held\n")
    print("  next:  python harvest.py --crop     then  --sweep")


BAND_GAP = 28       # blank rows that separate one paragraph from the next
BAND_SCALE = 0.667  # verified legible at this scale on 200-dpi ACRIS scans


def ink_bands(im):
    """Horizontal paragraph bands. ⚠ A PROOF IS A BAND, NOT A PAGE.

    Measured on 2013052101674002 p010: the page is 68 KB, the whole page
    1-bit is 40 KB, and THE TWO BANDS THAT ACTUALLY CARRY THE CLAIM ARE
    6.8 KB — the 'Lot 20' heading plus the limiting-plane clause. Ten times
    smaller and strictly more useful, because a crop that shows only the
    clause without its heading proves a plane over an unnamed lot.
    """
    import numpy as np
    g = np.array(im.convert("L"))
    on = (g < 200).sum(axis=1) > 2
    out, start, blank = [], None, 0
    for i, v in enumerate(on):
        if v:
            if start is None:
                start = i
            blank = 0
        elif start is not None:
            blank += 1
            if blank > BAND_GAP:
                out.append((start, i - blank))
                start = None
    if start is not None:
        out.append((start, len(on) - 1))
    cols = (g < 200).any(axis=0)
    xs = np.where(cols)[0]
    x0 = max(0, int(xs[0]) - 30) if len(xs) else 0
    x1 = min(im.width, int(xs[-1]) + 30) if len(xs) else im.width
    return out, x0, x1


def cmd_crop(band_index=None):
    try:
        from PIL import Image
    except ImportError:
        print("⚠ PIL required to cut crops")
        return
    PROOFS.mkdir(exist_ok=True)
    st = state()
    cut = skipped = 0
    before = size_of(list(PROOFS.iterdir())) if PROOFS.exists() else 0
    for d, s in st.items():
        if s["cov"] < DONE or not s["claims"]:
            continue                      # ⚠ never crop a document mid-read
        for pg in s["cited"]:
            dst = crop_path(d, pg)
            src = page_file(d, pg)
            if not src:
                skipped += 1
                continue
            im = Image.open(src)
            bands, x0, x1 = ink_bands(im)
            if not bands:
                skipped += 1
                continue
            # ⚠ REGION UNKNOWN -> KEEP EVERY BAND, DROP THE WHITESPACE.
            # The reader knows which band carries the claim; I do not, for
            # claims already recorded. Stitching the bands still discards
            # the margins and gutters, which is most of a scanned page.
            top = max(0, bands[0][0] - 18)
            bot = min(im.height, bands[-1][1] + 18)
            crop = im.crop((x0, top, x1, bot))
            crop = crop.resize((int(crop.width * BAND_SCALE),
                                int(crop.height * BAND_SCALE)), Image.LANCZOS)
            crop.convert("1").save(dst, optimize=True)
            if dst.stat().st_size < MIN_CROP_BYTES:
                dst.unlink()
                skipped += 1
            else:
                cut += 1
    n = len(list(PROOFS.iterdir()))
    b = size_of(list(PROOFS.iterdir()))
    print(f"cut {cut} crops · skipped {skipped}")
    print(f"proofs {n} files · {b/1e6:.1f} MB · avg {b/max(n,1)/1024:.0f} KB"
          f"   (was {before/1e6:.1f} MB)")


def cmd_sweep():
    st = state()
    freed = n = 0
    for d, s in st.items():
        ok, _ = sweepable(s)
        if not ok:
            continue
        files = doc_pages(d)
        freed += size_of(files)
        for f in files:
            f.unlink()
        try:
            (PAGES / d).rmdir()
        except OSError:
            pass
        n += 1
    print(f"swept {n} documents · {freed/1e6:.1f} MB reclaimed")
    print("⚠ every claim from those documents still carries its crop.")


def main():
    a = sys.argv[1:]
    if "--crop" in a:
        cmd_crop()
    elif "--sweep" in a:
        cmd_sweep()
    else:
        cmd_plan()


if __name__ == "__main__":
    main()
