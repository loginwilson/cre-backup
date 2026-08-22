"""OCR A DOCUMENT — one multipage file in, one document's lines out.

    python doc_ocr.py --doc 2005082901835001
    python doc_ocr.py --file ../documents/2005082901835001.pdf

⚠ THE INPUT IS A DOCUMENT, NOT A FOLDER OF PAGES. Login, 2026-08-17: "not pages. do the
doc. I am not sure why we have folders of pages." Correct, and the repo already agreed
with him — `acquire_async.py` writes ONE multipage `{doc}.tif` per document and treats
loose per-page files as its WRITE-FAILURE FALLBACK. The `sample_pages/` and `devr_pages/`
trees of `p001.tif` came from the older per-page fetchers, which is why 42,310 loose files
exist and why nothing downstream could address a document as a unit.
So this reads a multipage TIFF or PDF and iterates its frames. The doc_id is the filename
and nothing has to be opened to know what a file is.

⚠ THE SETTLED OCR POLICY, NOT UP FOR RE-DERIVATION: v6-tiny, limit_side_len 736, four
angles, union. 98.6% of 73 CRITICAL artifacts at 6.1 s/page. More pixels is WORSE (native
2880 -> 91.8% vs 736's 95.9%; the detector has a trained scale), union over det-config
+0.0, union over scale +0.0, union over ANGLE +2.7. See CLAUDE.md.

⚠ BOXES ARE KEPT AND ROTATED BOXES ARE MAPPED HOME. The VLM is never asked where a value
sits — it returns a value and the anchor is SEARCHED here, in code, where the answer is
verifiable. A box from the 270-degree pass that is not unrotated points at the wrong part
of the page, which is worse than having no box at all.

⚠ OCR AND THE VLM CANNOT SHARE THIS MACHINE. 16 GB with the iGPU carving its share from
the same pool; running both gave MemoryError. Kill llama-server before this runs.
"""
from __future__ import annotations

import argparse, json, pathlib, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
DEC = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(DEC))

ANGLES = (0, 90, 180, 270)


def build():
    from rapidocr import RapidOCR, EngineType, ModelType, OCRVersion, LangDet, LangRec
    return RapidOCR(params={
        "Det.engine_type": EngineType.OPENVINO, "Det.lang_type": LangDet.CH,
        "Det.model_type": ModelType("tiny"), "Det.ocr_version": OCRVersion("PP-OCRv6"),
        "Rec.engine_type": EngineType.OPENVINO, "Rec.lang_type": LangRec.CH,
        "Rec.model_type": ModelType("tiny"), "Rec.ocr_version": OCRVersion("PP-OCRv6"),
        "Det.engine_cfg.openvino.inference_num_threads": 8,
        "Rec.engine_cfg.openvino.inference_num_threads": 8})


def frames(path):
    """Yield (index, PIL image) for every page of a multipage TIFF or a PDF."""
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    if path.suffix.lower() == ".pdf":
        # ⚠ PDF PAGES MUST BE RASTERISED AT A STATED DPI. A PDF has no pixels of its
        # own; whatever DPI is chosen here IS the input resolution, and the detector
        # was measured at a scale, not at a DPI. 200 reproduces the ~2550px scans.
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(path))
        for i in range(len(doc)):
            yield i + 1, doc[i].render(scale=200 / 72).to_pil().convert("RGB")
        return
    im = Image.open(path)
    for i in range(getattr(im, "n_frames", 1)):
        im.seek(i)
        yield i + 1, im.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", help="doc id; resolves to ../documents/<id>.tif")
    ap.add_argument("--file", help="explicit path to a multipage tif or pdf")
    ap.add_argument("--angles", type=int, default=4,
                    help="4 = the settled union; 1 = angle 0 only for a quick look")
    a = ap.parse_args()

    path = (pathlib.Path(a.file) if a.file
            else DEC / "documents" / f"{a.doc}.tif")
    if not path.exists():
        print(f"  no such document: {path}"); return 1
    doc = a.doc or path.stem

    import numpy as np
    from resolve import locate as LOC

    pages = list(frames(path))
    if not pages:
        print(f"  {path} has no pages"); return 1

    ocr = build()
    ocr(np.array(pages[0][1]))          # warm: download + graph compile
    angles = ANGLES if a.angles == 4 else ANGLES[:a.angles]

    out = HERE / "out" / "_ocr" / doc
    out.mkdir(parents=True, exist_ok=True)
    print(f"  {path.name} · {len(pages)} pages · v6-tiny · 736 · angles {list(angles)}")

    t0, tot = time.time(), 0
    for n, im in pages:
        lines, t = [], time.time()
        for ang in angles:
            r = ocr(np.array(im.rotate(ang, expand=True) if ang else im))
            txts = list(getattr(r, "txts", None) or [])
            boxes = getattr(r, "boxes", None)
            for i, tx in enumerate(txts):
                b = None
                if boxes is not None:
                    pts = np.array(boxes[i]).tolist()
                    if not ang:
                        b = pts
                    else:
                        # ⚠ unrotate is PER POINT and takes the ORIGINAL page size.
                        # PIL's expand=True swaps W/H at 90/270, which is exactly the
                        # detail an eyeballed derivation gets wrong — so the helper in
                        # resolve/locate.py is used rather than re-deriving it here.
                        try:
                            W, H = im.size
                            b = [list(LOC.unrotate(px, py, ang, W, H)) for px, py in pts]
                        except Exception:
                            b = None   # no box beats a box in the wrong frame
                lines.append({"text": str(tx), "angle": ang, "box": b})
        tot += len(lines)
        (out / f"p{n:03d}.json").write_text(
            json.dumps({"doc": doc, "page": f"p{n:03d}", "size": im.size,
                        "angles": list(angles), "lines": lines}, indent=1),
            encoding="utf-8")
        print(f"    p{n:03d}  {len(lines):>4} lines  {time.time()-t:>6.1f}s")

    el = time.time() - t0
    print(f"  {tot} lines · {el:.1f}s ({el/len(pages):.1f}s/page) -> out/_ocr/{doc}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
