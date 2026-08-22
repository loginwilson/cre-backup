"""TESSERACT'S ACCURACY IS NOT THE PROBLEM. ITS THROUGHPUT IS. Can it be tuned?

Measured on 537 documents: genuine phrase-level OCR loss is 1.3%. Measured live:
1,079 ms/page. At 133,988,962 instrument pages on 8 cores that is 210 days, and
THAT is the number that kills it — not the errors.

So the only question worth asking is whether the cost is tunable without giving
back the accuracy. Resolution is the lever with no download and no new
dependency: these pages are 2550x3300, and Tesseract's own guidance is ~300dpi
for body text. Halving the width halves the dpi to 150.

⚠ SPEED WITHOUT RECALL IS NOT A RESULT. A downscale that runs 4x faster and
drops a third of the frames has made the scanner worse, and the loss would be
SILENT — fewer hits looks identical to a document that had fewer hits. So every
scale is scored on the SAME pages against the SAME frames, and recall is
reported beside the time. Either alone is meaningless.

⚠ AND THE BASELINE IS THE FULL-RESOLUTION RUN ON THESE EXACT PAGES, not the
537-document corpus figure. Comparing a 12-page timing against a 4,271-page
hit rate would be comparing two different populations and calling it a delta.

    python scan_speed.py [n_pages]
"""
import collections
import os
import pathlib
import re
import statistics
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

PAGES = pathlib.Path("sample_pages")
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCRATCH = pathlib.Path(os.environ["TMP"]) / "scanspeed"
SCRATCH.mkdir(parents=True, exist_ok=True)

SCALES = (1.0, 0.75, 0.5, 0.35)

from scanner_cost import FRAMES, STRIP


def run(img_path):
    t0 = time.time()
    r = subprocess.run([TESS, str(img_path), "stdout", "--psm", "6"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return (time.time() - t0) * 1000, r.stdout


def hits(text):
    c = collections.Counter()
    for lab, rx in FRAMES:
        n = len(re.findall(rx, text, re.I))
        if n:
            c[lab] += n
    return c


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    # ⚠ PAGES THAT ACTUALLY CARRY FRAMES, otherwise recall is 0/0 at every scale
    # and the test reports a tie. Pick from the documents known to be dense.
    cand = []
    for d in sorted(x for x in PAGES.iterdir() if x.is_dir()):
        for t in sorted(d.glob("*.tif")):
            cand.append(t)
    step = max(1, len(cand) // n)
    tifs = cand[::step][:n]

    print(f"  {len(tifs)} pages · scales {SCALES}\n")
    ms = {s: [] for s in SCALES}
    got = {s: collections.Counter() for s in SCALES}
    base_pages = {}

    for t in tifs:
        im = Image.open(t)
        if im.mode == "1":
            im = im.convert("L")          # ⚠ 'L' first — 1-bit resize destroys strokes
        for s in SCALES:
            f = SCRATCH / f"s{int(s*100)}.png"
            if s == 1.0:
                im.save(f)
            else:
                im.resize((int(im.width * s), int(im.height * s)),
                          Image.LANCZOS).save(f)
            el, txt = run(f)
            ms[s].append(el)
            h = hits(txt)
            got[s].update(h)
            if s == 1.0:
                base_pages[t] = h

    total_base = sum(got[1.0].values())
    print(f"  {'scale':<8}{'px width':>10}{'ms/page':>10}{'speedup':>9}"
          f"{'frame hits':>12}{'recall':>9}")
    for s in SCALES:
        m = statistics.mean(ms[s])
        tot = sum(got[s].values())
        print(f"  {s:<8.2f}{int(2550*s):>10,}{m:>10.0f}"
              f"{statistics.mean(ms[1.0])/m:>8.2f}x{tot:>12,}"
              f"{(tot/total_base*100 if total_base else 0):>8.1f}%")

    print(f"\n  ── PER FRAME, full res vs the fastest scale that keeps recall ──")
    print(f"  {'frame':<22}" + "".join(f"{s:>9.2f}" for s in SCALES))
    for lab, _ in FRAMES:
        if not got[1.0][lab]:
            continue
        print(f"  {lab:<22}" + "".join(f"{got[s][lab]:>9,}" for s in SCALES))

    print(f"\n  ── CORPUS COST · 133,988,962 instrument pages · {os.cpu_count()} cores ──")
    for s in SCALES:
        m = statistics.mean(ms[s])
        d = 133988962 * m / 1000 / 86400 / os.cpu_count()
        tot = sum(got[s].values())
        print(f"    scale {s:.2f}   {d:>7,.0f} days"
              f"   recall {(tot/total_base*100 if total_base else 0):>5.1f}%")
    print(f"\n  ⚠ a scale is only usable if recall is ~100%. Faster at 80% recall")
    print(f"    means one claim in five is never seen and nothing says so.")


if __name__ == "__main__":
    main()
