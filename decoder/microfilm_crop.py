"""MICROFILM: FIND THE PAGE INSIDE THE FRAME, THEN OCR ONLY THAT.

⚠ WHAT LOOKING AT THE IMAGE CHANGED. Microfilm scored 45.2 mean confidence
against 89.7 for modern scans, and I concluded Tesseract could not read film.
Then a preprocessing sweep — Otsu, autocontrast, Sauvola, median, upscale — moved
it by +0.3, which I nearly reported as "film is unreadable, 35.8% of ACRIS is
lost".

Both conclusions were wrong, and one glance at the page settled it. THE TEXT IS
PERFECTLY LEGIBLE. "AGREEMENT, made the 21st day of November nineteen hundred
and Seventy-nine", "in the principal sum of $ 95,000", "REEL 504 PAGE 724" — all
readable by eye without effort. What surrounds it is a band of microfilm grain
20-30% of the image wide, and THAT is what Tesseract is reading. It emits 944
"words" per page against 324 on a modern page because it is finding phantom text
in the speckle, and every one of those junk tokens drags the mean confidence
down.

So the fix is not a better threshold. There is nothing wrong with the ink. The
fix is to CROP TO THE PAGE and never show the engine the frame at all.

⚠ THE GENERAL LESSON, WHICH HAS NOW COST FOUR EXPERIMENTS TODAY. Byte-size
triage, front/back triage, the legacy-engine phantom, and this. Every one was a
confident inference from a summary statistic, and every one collapsed the moment
someone looked at the actual page. A number describing an image is not the image.

⚠ CONFIDENCE IS A PROXY AND IT CAN LIE. It is reported here beside WORD COUNT
for exactly that reason: if cropping works, confidence should rise AND the count
should fall toward the ~324 of a modern page, because the phantom tokens are
gone. Confidence rising while the count stays at 944 would mean something else
happened.
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
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCRATCH = pathlib.Path(os.environ["TMP"]) / "mfcrop"
SCRATCH.mkdir(parents=True, exist_ok=True)
FILM = [p for d in ("FT_1340008617134", "FT_1670008616267", "FT_1990000345899")
        for p in sorted(pathlib.Path("pages_out", d).glob("*.png"))]


def page_box(a, frame_ink=0.45, pad=12):
    """Largest contiguous band of rows/cols whose ink density looks like a
    PAGE rather than a FRAME.

    ⚠ A PAGE ROW AND A FRAME ROW ARE NOT CLOSE. Measured: the top 3% of one film
    page is 88% black and the bottom 92%, while the document body runs about 16%
    overall and a modern page about 6%. The gap is enormous, so a blunt cut at
    45% separates them without tuning — which matters, because a threshold fitted
    to three documents would be fitted to noise.
    """
    ink = a < 128
    rows, cols = ink.mean(1), ink.mean(0)

    def longest_run(v):
        best = cur = None
        for i, x in enumerate(v <= frame_ink):
            if x:
                cur = i if cur is None else cur
            else:
                if cur is not None:
                    best = (cur, i) if best is None or i - cur > best[1] - best[0] else best
                    cur = None
        if cur is not None:
            best = (cur, len(v)) if best is None or len(v) - cur > best[1] - best[0] else best
        return best

    r = longest_run(rows)
    c = longest_run(cols)
    if not r or not c:
        return None
    y0, y1 = max(0, r[0] + pad), min(a.shape[0], r[1] - pad)
    x0, x1 = max(0, c[0] + pad), min(a.shape[1], c[1] - pad)
    if y1 - y0 < a.shape[0] * 0.2 or x1 - x0 < a.shape[1] * 0.2:
        return None                     # refuse an implausible crop; keep the page
    return x0, y0, x1, y1


def score(path):
    r = subprocess.run([TESS, str(path), "stdout", "--psm", "6", "tsv"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    confs, words = [], []
    for x in csv.DictReader(io.StringIO(r.stdout), delimiter="\t",
                            quoting=csv.QUOTE_NONE):
        t = (x.get("text") or "").strip()
        if t:
            words.append(t)
            try:
                confs.append(float(x["conf"]))
            except (ValueError, KeyError, TypeError):
                pass
    return (statistics.mean(confs) if confs else 0.0), len(words), words


def build():
    jobs = []
    for p in FILM:
        im = Image.open(p).convert("L")
        a = np.asarray(im)
        raw = SCRATCH / f"{p.parent.name}_{p.stem}_raw.png"
        if not raw.exists():
            im.save(raw)
        jobs.append(("raw", p, raw))
        box = page_box(a)
        if box:
            c = SCRATCH / f"{p.parent.name}_{p.stem}_crop.png"
            if not c.exists():
                im.crop(box).save(c)
            jobs.append(("crop", p, c))
            frac = ((box[2]-box[0]) * (box[3]-box[1])) / (a.shape[0]*a.shape[1])
            print(f"  {p.parent.name}/{p.stem}  kept {frac*100:>5.1f}% of the image")
        else:
            print(f"  {p.parent.name}/{p.stem}  NO CROP FOUND — left whole")
    return jobs


def main():
    print(f"{len(FILM)} microfilm pages · modern baseline 89.7 conf / 324 words\n")
    jobs = build()
    with cf.ThreadPoolExecutor(12) as ex:
        res = list(ex.map(lambda j: (j[0], j[1], score(j[2])), jobs))
    agg = {}
    for kind, src, (c, n, _) in res:
        agg.setdefault(kind, []).append((c, n))
    print(f"\n  {'arm':<10}{'pages':>7}{'mean conf':>11}{'words/pg':>10}")
    print("  " + "-" * 40)
    for k in ("raw", "crop"):
        v = agg.get(k)
        if v:
            print(f"  {k:<10}{len(v):>7}{statistics.mean(x[0] for x in v):>11.1f}"
                  f"{statistics.mean(x[1] for x in v):>10.0f}")
    if "crop" in agg and "raw" in agg:
        d = (statistics.mean(x[0] for x in agg["crop"])
             - statistics.mean(x[0] for x in agg["raw"]))
        print(f"\n  cropping moves confidence {d:+.1f}")

    # ⚠ CONFIDENCE IS NOT THE POINT — READABLE FACTS ARE. Show the text.
    print("\n  what the cropped page actually says (first 400 chars):")
    for kind, src, (c, n, words) in res:
        if kind == "crop" and src.parent.name == "FT_1340008617134":
            print("   ", " ".join(words)[:400])
            break


if __name__ == "__main__":
    main()
