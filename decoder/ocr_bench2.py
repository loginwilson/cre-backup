"""OCR parallelism, FIXED — one thread per worker instead of eight fighting.

⚠ THE BUG THIS FIXES, measured earlier today:

    workers   pages/hr   FAILED
        1        294        0
        2        257        7
        4        165        0        <- SLOWER THAN SERIAL
        6        753       20        <- of 24. "fast" because it crashed

RapidOCR sits on onnxruntime, which spawns its OWN thread pool sized to the
machine. Six worker processes each spawning eight compute threads is 48 threads
fighting over 8 cores: context-switch thrash, memory pressure, and crashes.

⚠ AND THE 753 pages/hr WAS THE WORST PART — it was the highest number in the
table and it came from 20 of 24 pages FAILING. The harness divided pages by
wall-clock without checking outcomes, so crashes read as throughput. A
benchmark that counts failures as successes is worse than no benchmark; it
argues confidently for the wrong configuration.

THE FIX: pin every worker to a single intra-op thread, so N processes use N
cores and nothing contends. Set BEFORE onnxruntime is imported — after import
it is already read and the variable does nothing.
"""
import json
import multiprocessing as mp
import os
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_eng = None


def _init():
    # ⚠ MUST BE SET BEFORE THE IMPORT. onnxruntime reads these at load time.
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "ORT_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[v] = "1"
    global _eng
    from rapidocr_onnxruntime import RapidOCR
    _eng = RapidOCR(intra_op_num_threads=1, inter_op_num_threads=1)


def _one(path):
    t = time.time()
    try:
        res, _ = _eng(str(path))
        return (True, time.time() - t, len(res) if res else 0)
    except Exception:
        return (False, time.time() - t, -1)


def bench(paths, workers):
    t0 = time.time()
    if workers == 1:
        _init()
        out = [_one(p) for p in paths]
    else:
        with mp.Pool(workers, initializer=_init) as pool:
            out = pool.map(_one, paths)
    wall = time.time() - t0
    ok = [o for o in out if o[0]]
    # ⚠ THROUGHPUT COUNTS SUCCESSES ONLY. This is the line the old harness got
    # wrong, and it is why a 20/24 failure rate looked like the best result.
    return {"workers": workers, "pages": len(paths), "ok": len(ok),
            "failed": len(out) - len(ok), "wall_s": round(wall, 1),
            "pages_per_hour": round(3600 * len(ok) / wall) if wall else 0,
            "sec_per_page_ok": round(sum(o[1] for o in ok) / max(len(ok), 1), 2)}


def collect(n):
    root = pathlib.Path("ocr_pages")
    film, modern = [], []
    for d in sorted(root.iterdir()):
        if d.is_dir():
            (film if d.name.startswith("FT_") else modern).extend(
                sorted(d.glob("p0*.png")))
    k = n // 3
    return film[:k] + modern[:n - k]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 32
    paths = collect(n)
    print(f"{len(paths)} pages ({sum(1 for p in paths if 'FT_' in str(p))} film), "
          f"{os.cpu_count()} cores\n")
    print(f"{'workers':>8}{'ok':>5}{'fail':>6}{'wall s':>9}{'pages/hr':>10}")
    rows = []
    for w in (1, 2, 4, 6, 8):
        r = bench(paths, w)
        rows.append(r)
        print(f"{r['workers']:>8}{r['ok']:>5}{r['failed']:>6}"
              f"{r['wall_s']:>9}{r['pages_per_hour']:>10,}")
    base = rows[0]["pages_per_hour"]
    best = max(rows, key=lambda r: (r["failed"] == 0, r["pages_per_hour"]))
    print(f"\n  best CLEAN result: {best['workers']} workers, "
          f"{best['pages_per_hour']:,} pages/hr ({best['pages_per_hour']/base:.1f}x serial)")
    for label, pages in (("DEVR 41,066", 41066), ("zoning types 1.22M", 1_220_000)):
        print(f"  {label:<20} {pages/best['pages_per_hour']/24:>6.1f} days")
    json.dump(rows, open("_ocr_bench2.json", "w"), indent=1)
