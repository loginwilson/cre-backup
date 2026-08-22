"""OCR THE STRATIFIED SAMPLE — text plus coordinates, at the measured optimum.

SETTINGS, ALL MEASURED ON 2026-08-10 RATHER THAN CHOSEN:

    tesseract    1,368 -> 20,190 pg/hr vs RapidOCR's 300 on the same 30 pages,
                 identical trigger recall. RapidOCR is PaddleOCR in ONNX: a
                 SCENE-TEXT detector running ~50 forward passes on a dense legal
                 page. These are 1-bit CCITT-G4 scans at 300 dpi, which is what
                 classical layout analysis is for.
    12 processes best of 8/12/16 (16 is worse — past the 8 physical cores)
    OMP_THREAD_LIMIT=1  one thread each, or they fight for the same cores
    --psm 6      faster than psm 3 AND equal recall
    tsv          coordinates are NOT optional. Text alone loses the label-value
                 binding on the two-column cover page, which is how a hand-built
                 rule bound the FILING FEE on 150 consecutive pages at 96%
                 confidence.

⚠ MICROFILM IS CROPPED FIRST, AND THIS IS THE WHOLE REASON IT WORKS.
Raw film scored 45.2 mean confidence against 89.7 for modern scans, and a sweep
of Otsu / autocontrast / Sauvola / median / upscale moved it by +0.3 — because
ACRIS ships film ALREADY BINARISED and there was no tone left to threshold.
Looking at the page settled in one glance what five preprocessing arms could
not: the text is perfectly legible and 20-70% of the image is microfilm grain
around it. Tesseract was reading the grain, emitting 944 phantom "words" per
page against 324 on a modern page. Cropping to the page: 45.2 -> 78.2
confidence, 944 -> 310 words.

⚠ AND THE CROP OFFSET IS RECORDED WITH EVERY PAGE. Coordinates come back in the
space of the image Tesseract was GIVEN. Store them raw and every proof crop on a
film page points at the wrong region forever — and it still crops SOMETHING, so
nothing looks broken. `origin` below is what maps a box back to the original
TIFF.
"""
import concurrent.futures as cf
import csv
import gzip
import io
import json
import os
import pathlib
import statistics
import subprocess
import sys
import time

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from microfilm_crop import page_box

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SRC = pathlib.Path("sample_pages")
OUT = pathlib.Path("sample_ocr")
SCRATCH = pathlib.Path(os.environ["TMP"]) / "ocr_sample"
PROCS = 12


def one(path):
    """OCR a page. Returns text, words with boxes, and the crop origin."""
    doc = path.parent.name
    pg = int(path.stem[1:])
    feed, origin = path, (0, 0)

    # ⚠ FILM ONLY. A modern scan has no frame; running the detector on it risks
    # cropping into the document for no gain. FT_ is the microfilm marker.
    if doc.startswith("FT_"):
        try:
            im = Image.open(path).convert("L")
            box = page_box(np.asarray(im))
            if box:
                SCRATCH.mkdir(parents=True, exist_ok=True)
                feed = SCRATCH / f"{doc}_{path.stem}.png"
                if not feed.exists():
                    im.crop(box).save(feed)
                origin = (box[0], box[1])
        except Exception:
            feed, origin = path, (0, 0)      # never lose a page to preprocessing

    r = subprocess.run([TESS, str(feed), "stdout", "--psm", "6", "tsv"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    words, confs, parts = [], [], []
    for x in csv.DictReader(io.StringIO(r.stdout), delimiter="\t",
                            quoting=csv.QUOTE_NONE):
        t = (x.get("text") or "").strip()
        if not t:
            continue
        try:
            c = float(x["conf"])
            # ⚠ BOXES ARE TRANSLATED BACK TO ORIGINAL-TIFF SPACE HERE, ONCE.
            words.append({"t": t, "x": int(x["left"]) + origin[0],
                          "y": int(x["top"]) + origin[1],
                          "w": int(x["width"]), "h": int(x["height"]),
                          "c": round(c, 1)})
            confs.append(c)
            parts.append(t)
        except (ValueError, KeyError, TypeError):
            continue
    return {"doc": doc, "page": pg, "origin": origin,
            "conf": round(statistics.mean(confs), 1) if confs else 0.0,
            "nwords": len(words), "text": " ".join(parts), "words": words}


def main():
    pages = sorted(SRC.rglob("*.tif"))
    if not pages:
        print(f"no pages under {SRC}/")
        return
    OUT.mkdir(exist_ok=True)
    film = sum(1 for p in pages if p.parent.name.startswith("FT_"))
    print(f"{len(pages):,} pages · {len(set(p.parent.name for p in pages))} documents "
          f"· {film} film pages will be frame-cropped")
    print(f"{PROCS} processes, psm 6, tsv\n")

    t0 = time.time()
    bydoc = {}
    done = 0
    with cf.ThreadPoolExecutor(PROCS) as ex:
        for r in ex.map(one, pages):
            bydoc.setdefault(r["doc"], []).append(r)
            done += 1
            if done % 400 == 0:
                el = time.time() - t0
                print(f"  {done:,}/{len(pages):,}  {done/el*3600:,.0f} pg/hr", flush=True)
    el = time.time() - t0
    print(f"\n  {len(pages):,} pages in {el/60:.1f} min  ({len(pages)/el*3600:,.0f} pg/hr)")

    for doc, rows in bydoc.items():
        rows.sort(key=lambda r: r["page"])
        with gzip.open(OUT / f"{doc}.json.gz", "wt", encoding="utf-8") as fh:
            json.dump(rows, fh)
    sz = sum(p.stat().st_size for p in OUT.glob("*.json.gz"))
    print(f"  {len(bydoc)} documents -> {OUT}/  ({sz/1e6:.0f} MB gzipped)")

    # ⚠ REPORT QUALITY BY ERA, BECAUSE THAT IS WHERE IT BREAKS. Confidence held
    # between 82 and 94 across fifteen document TYPES; it collapsed only at the
    # film boundary. Type was never the axis that mattered.
    film_rows = [r for rows in bydoc.values() for r in rows
                 if r["doc"].startswith("FT_")]
    mod_rows = [r for rows in bydoc.values() for r in rows
                if not r["doc"].startswith("FT_")]
    print()
    for label, rows in (("microfilm (cropped)", film_rows), ("modern", mod_rows)):
        if rows:
            print(f"  {label:<22}{len(rows):>6} pages   conf "
                  f"{statistics.mean(r['conf'] for r in rows):>5.1f}   "
                  f"words/pg {statistics.mean(r['nwords'] for r in rows):>5.0f}")
    print("\n  reference points: modern scans 89.7 conf / 324 words,")
    print("                    raw film 45.2 / 944, cropped film 78.2 / 310")


if __name__ == "__main__":
    main()
