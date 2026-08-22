"""HOW FAST CAN THE SEARCHLIGHT GO — measured, with recall reported beside it.

⚠ SPEED IS ONLY MEANINGFUL NEXT TO RECALL. Every arm below reports both, on the
same ground truth, because a faster pass that stops seeing "LOWER LIMITING
PLANE" has not been optimised, it has been broken — and the failure is silent.
That is exactly how the byte-size triage rule looked like a 4x saving right up
until the page it discarded turned out to hold the only geometry in the
instrument.

⚠ WHY TESSERACT AND NOT RAPIDOCR/PADDLE. RapidOCR is PaddleOCR's models in
ONNX: a SCENE-TEXT detector, built for photographs and signage. It runs a
detection network, then recognises every line crop separately — on a dense
legal page that is ~50 forward passes. The input here is the opposite thing: a
1-bit CCITT-G4 bilevel scan at 300 dpi, produced by a Kofax document scanner.
Classical connected-component layout analysis eats that for breakfast.
Measured on the same 30 pages: 300 pg/hr vs 1,368 pg/hr, identical recall.

⚠ ONE PROCESS PER CORE, EACH PINNED TO ONE THREAD. Tesseract's own OpenMP
threading fights itself across processes. OMP_THREAD_LIMIT=1 plus N processes
is the standard throughput recipe and it is why this can scale where RapidOCR
could not — RapidOCR was ALREADY consuming 60% of the machine in one process
(39 threads), so it had no headroom to parallelise into. Tesseract single-
threaded has all of it.
"""
import concurrent.futures as cf
import os
import pathlib
import statistics
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import trigger_probe as TP

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
DOC = pathlib.Path("devr_pages/2014093000267001")
TIFS = sorted(DOC.glob("*.tif"))
SCRATCH = pathlib.Path(os.environ["TMP"]) / "tess_bench"
SCRATCH.mkdir(parents=True, exist_ok=True)


def run_one(args):
    path, psm, scale = args
    src = path
    if scale != 1.0:
        # ⚠ THE RESIZE IS ON THE CLOCK. Downscaling that saves OCR time but
        # costs more in conversion is not a saving, and reporting it as one
        # would be the batch-size confound this project already fell for once.
        from PIL import Image
        im = Image.open(path)
        w, h = im.size
        im = im.convert("L").resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        src = SCRATCH / f"{path.parent.name}_{path.stem}_{int(scale*100)}.png"
        im.save(src)
    r = subprocess.run([TESS, str(src), "stdout", "--psm", str(psm)],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    return int(path.stem[1:]), TP.norm(r.stdout or "")


def recall(text):
    hit = miss = 0
    missed = []
    for pg, slots in TP.TRUTH.items():
        for s in slots:
            if any(TP.norm(p) in text.get(pg, "") for p in TP.TRIGGERS.get(s, [])):
                hit += 1
            else:
                miss += 1
                missed.append(f"p{pg}:{s}")
    return hit, hit + miss, missed


def arm(label, psm, workers, scale=1.0):
    jobs = [(t, psm, scale) for t in TIFS]
    t0 = time.time()
    if workers == 1:
        out = dict(run_one(j) for j in jobs)
    else:
        with cf.ThreadPoolExecutor(workers) as ex:
            out = dict(ex.map(run_one, jobs))
    el = time.time() - t0
    h, n, missed = recall(out)
    rate = len(TIFS) / el * 3600
    chars = statistics.mean(len(v) for v in out.values())
    print(f"  {label:<30}{rate:>9,.0f} pg/hr{h:>5}/{n}{chars:>9.0f} ch", flush=True)
    if missed:
        print(f"      ⚠ MISSED: {', '.join(missed)}")
    return rate, h / n


def main():
    print(f"{len(TIFS)} pages of {DOC.name} · recall scored on 25 known facts\n")
    print(f"  {'arm':<30}{'speed':>16}{'recall':>7}{'text':>12}")
    print("  " + "-" * 66)
    results = {}
    results["psm3 x1"] = arm("psm 3 (auto layout), 1 proc", 3, 1)
    results["psm6 x1"] = arm("psm 6 (uniform block), 1 proc", 6, 1)
    results["psm6 x4"] = arm("psm 6, 4 procs", 6, 4)
    results["psm6 x8"] = arm("psm 6, 8 procs", 6, 8)
    results["psm3 x8"] = arm("psm 3, 8 procs", 3, 8)
    results["psm3 x8 @50%"] = arm("psm 3, 8 procs, 150 dpi", 3, 8, 0.5)

    base = results["psm3 x1"][0]
    print("\n  vs the 1-process baseline:")
    for k, (r, rc) in results.items():
        flag = "" if rc == 1.0 else f"   ⚠ recall {rc:.2f}"
        print(f"    {k:<16}{r/base:>6.2f}x{flag}")
    best = max((v[0], k) for k, v in results.items() if v[1] == 1.0)
    print(f"\n  FASTEST ARM AT FULL RECALL: {best[1]}  ({best[0]:,.0f} pg/hr)")
    print(f"    42,310 DEVR pages  ->  {42310/best[0]:.1f} h")
    print(f"    1,997 pages (one parcel) -> {1997/best[0]*60:.0f} min")


if __name__ == "__main__":
    main()
