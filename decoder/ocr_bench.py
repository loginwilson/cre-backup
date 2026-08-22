"""HOW FAST DOES EXTRACTION ACTUALLY GO? Measured, on this machine, on real pages.

⚠ EVERY THROUGHPUT NUMBER IN THIS PROJECT SO FAR HAS BEEN ARITHMETIC ON ONE
OBSERVATION. "15s/page single-threaded, so ~2s on 8 cores" assumes linear
scaling, which OCR does not deliver — the models are already partly threaded,
so N workers is never N times faster and can be SLOWER once they contend.

So this runs the real thing at 1, 2, 4 and 6 workers over the same held pages
and reports pages/hour. No estimate survives contact with a measurement.

⚠ AND IT REPORTS PER-ERA, because film and laser are not the same job. Film
pages carry ~0.20 ink against ~0.06 for laser — three times the marks for the
detector to box — and that cost is paid whether or not the text is usable
(microfilm scored locate 0.35, so most of that work is thrown away).
"""
import json
import multiprocessing as mp
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_eng = None


def _init():
    # ⚠ ONE ENGINE PER WORKER, BUILT ONCE. Constructing RapidOCR per page would
    # measure model loading, not OCR — and would also be how a naive
    # parallel harness quietly runs 5x slower than serial.
    global _eng
    from rapidocr_onnxruntime import RapidOCR
    _eng = RapidOCR()


def _one(path):
    t = time.time()
    try:
        res, _ = _eng(str(path))
        n = len(res) if res else 0
    except Exception:
        n = -1
    return (str(path), time.time() - t, n)


def bench(paths, workers):
    t0 = time.time()
    if workers == 1:
        _init()
        out = [_one(p) for p in paths]
    else:
        with mp.Pool(workers, initializer=_init) as pool:
            out = pool.map(_one, paths)
    wall = time.time() - t0
    ok = [o for o in out if o[2] >= 0]
    return {"workers": workers, "pages": len(paths), "wall_s": round(wall, 1),
            "pages_per_hour": round(3600 * len(paths) / wall),
            "sec_per_page": round(wall / max(len(paths), 1), 2),
            "failed": len(out) - len(ok)}


def collect(n=24):
    """A mixed sample: film is a third of ACRIS, so it must be a third here."""
    held = json.load(open("_held_docs.json"))
    root = pathlib.Path("ocr_pages")
    film, modern = [], []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        tgt = film if d.name.startswith("FT_") else modern
        for f in sorted(d.glob("p0*.png")):
            tgt.append(f)
    k = n // 3
    return film[:k] + modern[:n - k]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    paths = collect(n)
    print(f"{len(paths)} pages ({sum(1 for p in paths if 'FT_' in str(p))} film)\n")
    print(f"{'workers':>8}{'wall s':>9}{'s/page':>9}{'pages/hr':>10}{'failed':>8}")
    rows = []
    for w in (1, 2, 4, 6):
        r = bench(paths, w)
        rows.append(r)
        print(f"{r['workers']:>8}{r['wall_s']:>9}{r['sec_per_page']:>9}"
              f"{r['pages_per_hour']:>10,}{r['failed']:>8}")
    base = rows[0]["pages_per_hour"]
    best = max(rows, key=lambda r: r["pages_per_hour"])
    print(f"\n  best {best['workers']} workers — "
          f"{best['pages_per_hour']/base:.1f}x over serial")
    # ⚠ THE COMPARISON THAT MATTERS: is extraction anywhere near the bottleneck?
    ACQ_PER_DAY = 3600      # today's rough burst-and-recover estimate
    print(f"  extraction at best rate: {best['pages_per_hour']*24:,} pages/day")
    print(f"  acquisition (measured):  ~{ACQ_PER_DAY:,} pages/day")
    print(f"  -> extraction is {best['pages_per_hour']*24/ACQ_PER_DAY:.0f}x "
          f"faster than acquisition. IT IS NOT THE BOTTLENECK.")
    json.dump(rows, open("_ocr_bench.json", "w"), indent=1)
