"""CPU vs DirectML on the Intel Arc 140V — measured, not assumed.

⚠ AN INTEGRATED GPU IS NOT AUTOMATICALLY FASTER. OCR runs several small models
(detect, classify, recognise) over one page. Small models on an iGPU can lose
to CPU entirely, because every inference pays a host-to-device transfer and the
kernels are too small to amortise it. Shared-memory iGPUs also contend with the
CPU for the same RAM bandwidth. So this is a real question with a real chance
of a negative answer, and a negative answer is a useful result.

⚠ WARM-UP IS EXCLUDED. First inference on DirectML compiles kernels and can
take seconds — timing it would make the GPU look catastrophic. Both backends
get an untimed warm-up page, then are measured on identical work.

⚠ AND THE SAME OUTPUT IS CHECKED, NOT JUST THE SPEED. A backend that is 5x
faster and reads different text is not faster, it is broken. Box counts and a
text sample are compared between backends on the same page.
"""
import json
import os
import pathlib
import statistics
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def collect(n):
    root = pathlib.Path("ocr_pages")
    film, modern = [], []
    for d in sorted(root.iterdir()):
        if d.is_dir():
            (film if d.name.startswith("FT_") else modern).extend(
                sorted(d.glob("p0*.png")))
    k = n // 3
    return film[:k] + modern[:n - k]


def run(paths, use_dml, label):
    from rapidocr_onnxruntime import RapidOCR
    import onnxruntime as ort
    t0 = time.time()
    eng = RapidOCR(use_dml=use_dml) if use_dml else RapidOCR()
    load = time.time() - t0

    # ⚠ UNTIMED WARM-UP — first DirectML call compiles kernels.
    try:
        eng(str(paths[0]))
    except Exception as e:
        return {"backend": label, "error": f"{type(e).__name__}: {str(e)[:80]}"}

    per, ok, fail, boxes = [], 0, 0, []
    t0 = time.time()
    for p in paths:
        t = time.time()
        try:
            res, _ = eng(str(p))
            per.append(time.time() - t)
            boxes.append(len(res) if res else 0)
            ok += 1
        except Exception:
            fail += 1
    wall = time.time() - t0
    sample, _ = eng(str(paths[0]))
    text = " ".join(r[1] for r in sample)[:120] if sample else ""
    return {"backend": label, "model_load_s": round(load, 1),
            "pages": len(paths), "ok": ok, "failed": fail,
            "wall_s": round(wall, 1),
            "pages_per_hour": round(3600 * ok / wall) if wall else 0,
            "sec_per_page": round(statistics.mean(per), 2) if per else None,
            "median_s": round(statistics.median(per), 2) if per else None,
            "total_boxes": sum(boxes), "sample_text": text,
            "providers": ort.get_available_providers()}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    paths = collect(n)
    print(f"{len(paths)} pages ({sum(1 for p in paths if 'FT_' in str(p))} film)\n")

    rows = []
    for dml, label in ((False, "CPU"), (True, "DirectML / Arc 140V")):
        r = run(paths, dml, label)
        rows.append(r)
        if "error" in r:
            print(f"  {label:<22} ERROR  {r['error']}")
            continue
        print(f"  {label:<22} {r['pages_per_hour']:>6,} pg/hr  "
              f"{r['sec_per_page']}s/pg (median {r['median_s']})  "
              f"load {r['model_load_s']}s  {r['failed']} failed  "
              f"{r['total_boxes']} boxes")

    good = [r for r in rows if "error" not in r]
    if len(good) == 2:
        cpu, gpu = good
        sp = gpu["pages_per_hour"] / cpu["pages_per_hour"] if cpu["pages_per_hour"] else 0
        print(f"\n{'='*66}")
        print(f"  DirectML is {sp:.2f}x CPU")
        # ⚠ SAME TEXT? A faster backend that reads differently is not faster.
        same = cpu["sample_text"][:60] == gpu["sample_text"][:60]
        bx = (abs(cpu["total_boxes"] - gpu["total_boxes"]) /
              max(cpu["total_boxes"], 1))
        print(f"  box counts within {bx*100:.1f}%   first-60-chars identical: {same}")
        if not same:
            print(f"    CPU: {cpu['sample_text'][:60]}")
            print(f"    GPU: {gpu['sample_text'][:60]}")
        if sp < 1.05:
            print("\n  -> NO GAIN. The models are too small to amortise transfer\n"
                  "     on an iGPU. Stay on CPU; revert with:\n"
                  "     pip install --force-reinstall onnxruntime")
        else:
            best = gpu["pages_per_hour"]
            print(f"\n  DEVR   42,928 pages : {42928/best/24:.1f} days")
            print(f"  zoning 480,455      : {480455/best/24:.1f} days")
            print(f"  ⚠ single-process figure. CPU hit 462 pg/hr at 4 workers;\n"
                  f"    GPU workers contend for one device, so parallel gains\n"
                  f"    will NOT stack the same way. Measure before promising.")
    json.dump(rows, open("_gpu_bench.json", "w"), indent=1)
