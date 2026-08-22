"""CAN MICROFILM BE MADE READABLE? 35.8% of ACRIS depends on the answer.

⚠ THE CLAIM THIS TESTS, AND WHY IT MAY HAVE BEEN UNFAIR. Tesseract scored 45.2%
mean word confidence on microfilm against 89.7% on modern scans, and that was
reported as "Tesseract cannot do microfilm". But those pages were fed in RAW —
no thresholding, no contrast normalisation, no despeckle, nothing. Degraded-scan
OCR normally lives or dies on preprocessing, so the 45% may be a fact about this
pipeline rather than about the film.

    modern scan     mode '1'  — 1-bit, ALREADY BINARISED by the Kofax scanner
    microfilm       mode 'L'  — 8-bit greyscale, mean 212-240, std 60-95

Tesseract binarises internally with a single global threshold. On evenly-lit
bitonal input that is free and correct. On film with a bright surround and
uneven exposure it is close to the worst available choice, because one cutoff
cannot serve a page whose background drifts across it.

⚠ 13 PAGES IS NOT A POPULATION. Three documents survive on disk. A large jump
here would justify acquiring a real microfilm sample; it would not settle
anything by itself. And a NON-result is equally informative, because 35.8% of
the corpus is riding on it.

⚠ SCORED ON CONFIDENCE, WHICH IS A PROXY AND CAN LIE. Tesseract reports
confidence on what it thinks it read, so a confident misreading scores well.
Word count is reported beside it as a sanity check: the raw baseline emitted 944
"words" per page against 324 on modern pages, which is the signature of an
engine shattering noise into fragments rather than reading text.
"""
import concurrent.futures as cf
import csv
import io
import os
import pathlib
import statistics
import subprocess
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCRATCH = pathlib.Path(os.environ["TMP"]) / "mfilm"
SCRATCH.mkdir(parents=True, exist_ok=True)
FILM = [p for d in ("FT_1340008617134", "FT_1670008616267", "FT_1990000345899")
        for p in sorted(pathlib.Path("pages_out", d).glob("*.png"))]


def otsu(a):
    """Global Otsu. What Tesseract already does internally — included as a
    control so the adaptive arms are compared against the right baseline."""
    h = np.bincount(a.ravel(), minlength=256).astype(float)
    tot = h.sum()
    best, thr = -1.0, 128
    w0 = c0 = 0.0
    s_all = float((np.arange(256) * h).sum())
    for t in range(256):
        w0 += h[t]
        if w0 == 0:
            continue
        w1 = tot - w0
        if w1 == 0:
            break
        c0 += t * h[t]
        m0 = c0 / w0
        m1 = (s_all - c0) / w1
        v = w0 * w1 * (m0 - m1) ** 2
        if v > best:
            best, thr = v, t
    return thr


def sauvola(a, win=41, k=0.25, R=128.0):
    """⚠ LOCAL threshold — the point of the whole exercise. Computes a cutoff
    per neighbourhood from local mean and deviation, so a page whose background
    drifts from 240 on one side to 180 on the other is still separable. Uses
    integral images so it stays O(n) and does not need scipy or OpenCV."""
    a = a.astype(np.float64)
    p = np.pad(a, win // 2, mode="edge")
    # ⚠ AN INTEGRAL IMAGE NEEDS A LEADING ZERO ROW AND COLUMN. Without them
    # box(y0,x0) has no cell to subtract for its top-left corner, so every
    # window index runs one past the end and the last row raises IndexError.
    ii = np.zeros((p.shape[0] + 1, p.shape[1] + 1))
    ii2 = np.zeros_like(ii)
    ii[1:, 1:] = p.cumsum(0).cumsum(1)
    ii2[1:, 1:] = (p ** 2).cumsum(0).cumsum(1)
    H, W = a.shape
    y0, x0 = np.mgrid[0:H, 0:W]
    y1, x1 = y0 + win, x0 + win

    def box(I):
        return (I[y1, x1] - I[y0, x1] - I[y1, x0] + I[y0, x0]) / (win * win)

    m = box(ii)
    v = np.clip(box(ii2) - m ** 2, 0, None)
    return (a > m * (1 + k * (np.sqrt(v) / R - 1))).astype(np.uint8) * 255


def variants(path):
    im = Image.open(path).convert("L")
    a = np.asarray(im)
    out = {"raw": im}
    out["otsu"] = Image.fromarray(((a > otsu(a)) * 255).astype(np.uint8))
    st = ImageOps.autocontrast(im, cutoff=2)
    b = np.asarray(st)
    out["autocontrast+otsu"] = Image.fromarray(((b > otsu(b)) * 255).astype(np.uint8))
    out["sauvola"] = Image.fromarray(sauvola(a))
    med = np.asarray(im.filter(ImageFilter.MedianFilter(3)))
    out["median+sauvola"] = Image.fromarray(sauvola(med))
    big = im.resize((int(im.width * 1.5), int(im.height * 1.5)), Image.LANCZOS)
    out["upscale1.5+sauvola"] = Image.fromarray(sauvola(np.asarray(big)))
    return out


def score(args):
    name, path = args
    r = subprocess.run([TESS, str(path), "stdout", "--psm", "6", "tsv"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    confs = []
    for x in csv.DictReader(io.StringIO(r.stdout), delimiter="\t",
                            quoting=csv.QUOTE_NONE):
        if (x.get("text") or "").strip():
            try:
                confs.append(float(x["conf"]))
            except (ValueError, KeyError, TypeError):
                pass
    return name, (statistics.mean(confs) if confs else 0.0), len(confs)


def main():
    print(f"{len(FILM)} microfilm pages · modern baseline is 89.7 conf / 324 words\n")
    jobs = []
    for p in FILM:
        for name, im in variants(p).items():
            f = SCRATCH / f"{p.parent.name}_{p.stem}_{name.replace('+','_').replace('.','')}.png"
            if not f.exists():
                im.save(f)
            jobs.append((name, f))
    with cf.ThreadPoolExecutor(12) as ex:
        res = list(ex.map(score, jobs))
    agg = {}
    for name, c, n in res:
        agg.setdefault(name, []).append((c, n))
    print(f"  {'preprocessing':<24}{'mean conf':>11}{'words/pg':>10}")
    print("  " + "-" * 45)
    base = None
    for name in ("raw", "otsu", "autocontrast+otsu", "sauvola",
                 "median+sauvola", "upscale1.5+sauvola"):
        v = agg.get(name)
        if not v:
            continue
        c = statistics.mean(x[0] for x in v)
        w = statistics.mean(x[1] for x in v)
        if base is None:
            base = c
        print(f"  {name:<24}{c:>11.1f}{w:>10.0f}")
    best = max(agg.items(), key=lambda kv: statistics.mean(x[0] for x in kv[1]))
    bc = statistics.mean(x[0] for x in best[1])
    print(f"\n  BEST: {best[0]}  {bc:.1f} conf  ({bc-base:+.1f} vs raw)")
    print(f"  modern scans sit at 89.7 — still {89.7-bc:.1f} short"
          if bc < 89.7 else "  reaches modern-scan quality")
    print("\n  ⚠ 13 pages, 3 documents. A jump here justifies acquiring a real")
    print("    microfilm sample; it does not settle 35.8% of the corpus.")


if __name__ == "__main__":
    main()
