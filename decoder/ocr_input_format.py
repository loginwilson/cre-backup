"""AM I PAYING FOR MY OWN FILE FORMAT? The cheapest 2x, if it is real.

⚠ MY OCR TIMINGS DISAGREE WITH THEMSELVES AND THIS IS THE SUSPECT. Across this
session Tesseract measured 800, 1079, 1428 and ~2000 ms/page, putting the corpus
anywhere from 172 to 430 days. The runs that were FAST fed the original 1-bit
CCITT TIFF straight off disk. The run that was SLOW staged a grayscale PNG first
because a downscale test needed one. If that is the whole difference, then the
426-day figure is an artefact of my benchmark and not a property of Tesseract.

Three things change at once when you convert, and they pull in opposite
directions, so it has to be measured rather than reasoned:

    decode cost   G4 is cheap to decode; PNG deflate on 8.4MP is not free
    binarisation  a 1-bit image is ALREADY binary. Grayscale makes Tesseract
                  run Otsu thresholding it would otherwise skip
    pixel volume  1 bit/px vs 8 bit/px is 8x the bytes through memory

⚠ RECALL IS MEASURED TOO. If bilevel input is faster but Tesseract's own
binarisation was actually helping accuracy, that is a trade and not a win —
so frames found is printed beside every timing and decides the verdict.

    python ocr_input_format.py [n_pages]
"""
import collections
import os
import pathlib
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

from scanner_cost import FRAMES

PAGES = pathlib.Path("sample_pages")
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCRATCH = pathlib.Path(os.environ["TMP"]) / "fmt"
SCRATCH.mkdir(parents=True, exist_ok=True)

CORPUS = 148_628_961
CORES = os.cpu_count()
RX = [(lab, re.compile(rx, re.I)) for lab, rx in FRAMES]


def run_one(path):
    r = subprocess.run([TESS, path, "stdout", "--psm", "6"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.stdout


def bench(files):
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=CORES) as ex:
        outs = list(ex.map(run_one, files))
    el = time.time() - t0
    h = collections.Counter()
    for o in outs:
        for lab, rx in RX:
            n = len(rx.findall(o))
            if n:
                h[lab] += n
    return len(files) / el, sum(h.values()), h


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    cand = [t for d in sorted(x for x in PAGES.iterdir() if x.is_dir())
            for t in sorted(d.glob("*.tif"))]
    tifs = cand[::max(1, len(cand) // n)][:n]

    variants = {}
    variants["TIFF 1-bit (as stored)"] = [str(t) for t in tifs]

    # PNG from 'L' — what the throughput benchmark actually fed it
    d = SCRATCH / "png_L"; d.mkdir(exist_ok=True)
    out = []
    for i, t in enumerate(tifs):
        f = d / f"p{i:04d}.png"
        if not f.exists():
            Image.open(t).convert("L").save(f)
        out.append(str(f))
    variants["PNG grayscale (converted)"] = out

    # PNG that stays 1-bit — isolates FORMAT from BIT DEPTH
    d = SCRATCH / "png_1"; d.mkdir(exist_ok=True)
    out = []
    for i, t in enumerate(tifs):
        f = d / f"p{i:04d}.png"
        if not f.exists():
            im = Image.open(t)
            (im if im.mode == "1" else im.convert("1")).save(f)
        out.append(str(f))
    variants["PNG 1-bit"] = out

    print(f"  {len(tifs)} pages · {CORES} workers · target 57.3 pages/s = 30 days\n")
    print(f"  {'input format':<28}{'MB':>7}{'pages/s':>9}{'frames':>8}"
          f"{'recall':>8}{'days':>8}")
    base = None
    best = None
    for lab, files in variants.items():
        mb = sum(os.path.getsize(f) for f in files) / 1e6
        ps, h, det = bench(files)
        if base is None:
            base = h
        days = CORPUS / ps / 86400
        flag = "" if h >= base else "  ⚠ LOST"
        print(f"  {lab:<28}{mb:>7.1f}{ps:>9.1f}{h:>8}{h/base*100:>7.0f}%"
              f"{days:>8.0f}{flag}")
        if h >= base and (best is None or ps > best[1]):
            best = (lab, ps, days)

    if best:
        print(f"\n  ── FASTEST WITH FULL RECALL ──")
        print(f"    {best[0]}   {best[1]:.1f} pages/s   {best[2]:.0f} days")
        print(f"    still {best[2]/30:.1f}x short of 30 days on {CORES} cores")
        print(f"    cores needed for 30 days: {CORES*best[2]/30:.0f}")


if __name__ == "__main__":
    main()
