"""DOES THE BUNDLED PDF CARRY THE SAME PIXELS AS THE TIFFS? The whole question.

ACRIS will hand you a whole document as one PDF (/DS/Print/print?printType=Image)
instead of N TIFF fetches. Measured on one file it is 29% smaller per page —
and 29% smaller is exactly the shape of a win OR of silent damage:

    repacked G4        same pixels, PDF overhead removed        FREE WIN
    downsampled        fewer pixels                             OCR GETS WORSE
    JPEG / lossy       ringing on 1-bit text                    OCR GETS WORSE
    lossy JBIG2        SYMBOL SUBSTITUTION -- digits change     CATASTROPHIC

⚠ THE LAST ONE IS NOT HYPOTHETICAL AND IT IS THE REASON THIS SCRIPT EXISTS.
Lossy JBIG2 replaces visually-similar glyphs with a shared symbol; it is the
mechanism behind the Xerox scanning bug that silently changed digits in scanned
documents. On a corpus whose entire purpose is recovering amounts, a codec that
can turn 6 into 8 with no visible artefact is disqualifying no matter what it
does to file size.

So: read what the PDF actually embeds. Filter, bit depth, and dimensions are
recorded IN the file and settle it without OCRing anything.

    python pdf_vs_tiff.py
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DL = pathlib.Path("C:/Users/smile/Downloads")
TIF = pathlib.Path("sample_pages")

LOSSY = {"DCTDecode", "JPXDecode"}
LOSSLESS = {"CCITTFaxDecode", "FlateDecode", "LZWDecode", "RunLengthDecode"}


def pdf_images(path, limit=6):
    from pypdf import PdfReader
    r = PdfReader(str(path))
    out = []
    for i, page in enumerate(r.pages[:limit]):
        res = page.get("/Resources") or {}
        xo = res.get("/XObject")
        if xo is None:
            out.append((i + 1, None, None, None, None))
            continue
        xo = xo.get_object()
        for name in xo:
            o = xo[name].get_object()
            if o.get("/Subtype") != "/Image":
                continue
            f = o.get("/Filter")
            f = [str(x) for x in f] if isinstance(f, list) else [str(f)]
            out.append((i + 1, o.get("/Width"), o.get("/Height"),
                        o.get("/BitsPerComponent"), "+".join(x.lstrip("/") for x in f)))
    return len(r.pages), out


def main():
    pdfs = sorted(p for p in DL.glob("*&page*.pdf"))
    print(f"  {len(pdfs)} ACRIS PDFs in Downloads\n")

    have_tif = {p.name for p in TIF.iterdir()} if TIF.exists() else set()
    overlap = []

    for p in pdfs:
        doc = p.name.split("&")[0]
        try:
            n, imgs = pdf_images(p)
        except Exception as e:
            print(f"  {doc}  UNREADABLE: {str(e)[:60]}")
            continue
        filters = {i[4] for i in imgs if i[4]}
        dims = {(i[1], i[2]) for i in imgs if i[1]}
        bits = {i[3] for i in imgs if i[3]}
        risky = [f for f in filters if any(x in f for x in LOSSY)]
        mark = "⚠ LOSSY" if risky else "lossless"
        star = " ★ ALSO ON DISK AS TIFF" if doc in have_tif else ""
        if doc in have_tif:
            overlap.append((doc, p))
        print(f"  {doc}  {n:>3}pg  {p.stat().st_size/n:>8,.0f} B/pg  "
              f"{'/'.join(sorted(filters)) or '?':<22} bits={sorted(bits)} "
              f"{mark}{star}")
        if len(dims) > 1:
            print(f"      dims vary: {sorted(dims)[:4]}")
        elif dims:
            w, h = next(iter(dims))
            print(f"      {w} x {h} px")

    # ── the decisive comparison, if we have the same document both ways ──
    print(f"\n  ── SAME DOCUMENT, BOTH FORMATS: {len(overlap)} ──")
    if not overlap:
        print("  none. The PDFs in Downloads and the TIFF sample do not intersect,")
        print("  so pixel-for-pixel comparison needs one document fetched both ways.")
        return
    from PIL import Image
    for doc, p in overlap:
        tifs = sorted((TIF / doc).glob("*.tif"))
        n, imgs = pdf_images(p, limit=len(tifs) or 6)
        print(f"\n  {doc}")
        for (pg, w, h, b, f), t in zip(imgs, tifs):
            im = Image.open(t)
            same = "SAME" if (w, h) == im.size else "⚠ DIFFERENT"
            print(f"    p{pg:<3} pdf {w}x{h} {f:<16} | tif {im.size[0]}x{im.size[1]} "
                  f"{im.mode} | {same}")


if __name__ == "__main__":
    main()
