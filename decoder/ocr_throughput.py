"""SUB-30 DAYS ON 148.6M PAGES. That is 5.7x faster than today. Where does it come from?

    148,628,961 pages / (30 days * 86400 s) = 57.3 pages/sec SUSTAINED, all cores

⚠ EVERY PRIOR TIMING HERE WAS SEQUENTIAL AND THAT HIDES THE BIGGEST LEVER.
Running one page at a time, Tesseract spreads itself over all 8 cores via
OpenMP. Run 8 processes at once and each STILL tries to take 8 threads — 64
threads fighting for 8 cores. The fix is one line of environment
(OMP_THREAD_LIMIT=1) and it is invisible to anyone who only ever timed a single
page, because on a single page the threading genuinely helps.

So this measures AGGREGATE THROUGHPUT under real parallelism, which is the only
number that maps to a delivery date. Sequential ms/page does not.

⚠ AND RECALL IS MEASURED AT EVERY SETTING. A configuration that doubles speed
and drops a frame has not helped — it has made the 2.56% document-level loss
worse in exchange for a schedule. Frames found is printed beside every timing
and any setting that loses frames is disqualified no matter how fast it is.

    python ocr_throughput.py [n_pages]
"""
import collections
import os
import pathlib
import re
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

from scanner_cost import FRAMES

PAGES = pathlib.Path("sample_pages")
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCRATCH = pathlib.Path(os.environ["TMP"]) / "thru"
SCRATCH.mkdir(parents=True, exist_ok=True)

CORPUS = 148_628_961
CORES = os.cpu_count()
RX = [(lab, re.compile(rx, re.I)) for lab, rx in FRAMES]


def stage(tifs, scale):
    """Write the sample once per scale so staging is not inside the timer."""
    d = SCRATCH / f"s{int(scale*100)}"
    d.mkdir(exist_ok=True)
    out = []
    for i, t in enumerate(tifs):
        f = d / f"p{i:04d}.png"
        if not f.exists():
            im = Image.open(t)
            if im.mode == "1":
                im = im.convert("L")        # ⚠ 'L' before resize, always
            if scale != 1.0:
                im = im.resize((int(im.width * scale), int(im.height * scale)),
                               Image.LANCZOS)
            im.save(f)
        out.append(str(f))
    return out


def run_one(args):
    path, env, extra = args
    r = subprocess.run([TESS, path, "stdout", "--psm", "6"] + extra,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    return r.stdout


def bench(files, workers, omp, extra=()):
    env = dict(os.environ)
    if omp:
        env["OMP_THREAD_LIMIT"] = "1"
    else:
        env.pop("OMP_THREAD_LIMIT", None)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        outs = list(ex.map(run_one, [(f, env, list(extra)) for f in files]))
    el = time.time() - t0
    hits = collections.Counter()
    for o in outs:
        for lab, rx in RX:
            n = len(rx.findall(o))
            if n:
                hits[lab] += n
    return len(files) / el, sum(hits.values())


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 48
    cand = [t for d in sorted(x for x in PAGES.iterdir() if x.is_dir())
            for t in sorted(d.glob("*.tif"))]
    tifs = cand[::max(1, len(cand) // n)][:n]
    need = CORPUS / (30 * 86400)

    print(f"  {len(tifs)} pages · {CORES} cores")
    print(f"  TARGET  {need:.1f} pages/sec sustained  = 30 days on {CORPUS:,} pages\n")

    base_hits = None
    rows = []
    print(f"  {'setting':<34}{'pages/s':>9}{'frames':>8}{'recall':>8}{'days':>8}")
    for scale in (1.0, 0.5, 0.35):
        files = stage(tifs, scale)
        for omp in (False, True):
            for workers in ({1, CORES} if scale == 1.0 and not omp else {CORES}):
                ps, h = bench(files, workers, omp)
                if base_hits is None:
                    base_hits = h
                days = CORPUS / ps / 86400
                lab = (f"scale {scale:.2f} · {workers}w · "
                       f"OMP={'1' if omp else 'default'}")
                ok = "" if h >= base_hits else "  ⚠ LOST FRAMES"
                print(f"  {lab:<34}{ps:>9.1f}{h:>8}"
                      f"{h/base_hits*100:>7.0f}%{days:>8.0f}{ok}")
                rows.append((lab, ps, h, days))

    print(f"\n  ── BEST SETTING THAT KEEPS EVERY FRAME ──")
    ok = [r for r in rows if r[2] >= base_hits]
    if ok:
        b = max(ok, key=lambda r: r[1])
        print(f"    {b[0]}   {b[1]:.1f} pages/s   {b[3]:.0f} days")
        print(f"    speedup vs 8w/default: "
              f"{b[1]/next(r[1] for r in rows if 'scale 1.00' in r[0] and 'default' in r[0] and r[1]):.2f}x")
        if b[3] > 30:
            short = b[3] / 30
            print(f"\n  ⚠ STILL {short:.1f}x SHORT OF 30 DAYS on {CORES} cores.")
            print(f"    cores needed at this setting: {CORES*short:.0f}")
    print(f"\n  ⚠ frames found is the disqualifier, not the tiebreaker. A setting")
    print(f"    below 100% recall is not a faster pipeline, it is a lossier one.")


if __name__ == "__main__":
    main()
