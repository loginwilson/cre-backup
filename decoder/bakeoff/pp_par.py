"""PP-OCRv6 across processes. Same 26 keyed pages, just not one at a time.

    python pp_par.py            # 4 workers x 2 threads on 8 cores
    python pp_par.py --workers 8 --threads 1

⚠ PROCESSES, NOT THREADS - THE SAME LESSON RapidOCR ALREADY TAUGHT THIS PROJECT.
RapidOCR was reported at 0.072 pages/s from ONE process while Tesseract ran
8-wide, and it read as the slowest engine on the board when it was the most
accurate one. Paddle's plain CPU path does not saturate 8 cores on a page this
size either, so the parallelism has to come from processes.

⚠ AND workers x threads MUST NOT EXCEED CORES. 8 processes x 8 threads on 8
cores is 64 threads fighting for cache; it runs SLOWER and would read as
"parallelism does not help Paddle".

⚠ SPEED FROM THIS RUN IS STILL MEANINGLESS. CPU-only wheel, oneDNN disabled
because it throws ConvertPirAttribute2RuntimeAttribute on this Intel box. The
paper's 0.13 s/page is an A100 figure. The only number worth taking from here is
ACCURACY on film, book and digital.

⚠ A CRASH MUST LEAVE NO FILE. An empty .txt is indistinguishable from an engine
that read the page and found nothing, and those are opposite findings.
"""
import argparse
import json
import pathlib
import sys
import time
import warnings
from multiprocessing import Pool

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out" / "ppv6"
_OCR = None


def init(threads):
    global _OCR
    import warnings as w
    w.filterwarnings("ignore")
    from paddleocr import PaddleOCR
    _OCR = PaddleOCR(ocr_version="PP-OCRv6", device="cpu", enable_mkldnn=False,
                     cpu_threads=threads,
                     use_doc_orientation_classify=False, use_doc_unwarping=False,
                     use_textline_orientation=False)


def one(job):
    docn, path = job
    p = pathlib.Path(path)
    f = OUT / docn / (p.stem + ".png.txt")
    if f.exists():
        return (docn, p.name, -1, 0.0)
    t = time.time()
    try:
        res = _OCR.predict(str(p))
    except Exception as e:
        return (docn, p.name, None, f"{type(e).__name__}: {str(e)[:80]}")
    lines = []
    for r in res or []:
        j = r if isinstance(r, dict) else getattr(r, "json", {}) or {}
        j = j.get("res", j)
        lines += list(j.get("rec_texts") or [])
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(" ".join(lines), encoding="utf-8")
    return (docn, p.name, len(lines), round(time.time() - t, 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()

    jobs = [(d.name, str(p))
            for d in sorted(x for x in (HERE / "pages").iterdir() if x.is_dir())
            for p in sorted(d.glob("p*.png"))]
    print(f"  PP-OCRv6 medium · CPU · oneDNN off")
    print(f"  {len(jobs)} pages · {a.workers} workers x {a.threads} threads\n")

    t0 = time.time()
    with Pool(a.workers, initializer=init, initargs=(a.threads,)) as pool:
        res = pool.map(one, jobs)
    el = time.time() - t0

    done = [r for r in res if isinstance(r[2], int) and r[2] >= 0]
    skipped = [r for r in res if r[2] == -1]
    errs = [r for r in res if r[2] is None]
    for r in errs[:6]:
        print(f"    FAILED {r[0]}/{r[1]}: {r[3]}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "run.json").write_text(json.dumps(
        {"engine": "ppv6", "model": "PP-OCRv6_medium", "device": "cpu",
         "mkldnn": False, "rot": False,
         "workers": a.workers, "threads": a.threads,
         "pages": len(done) + len(skipped), "errors": [list(e) for e in errs],
         "sec": round(el, 1),
         "sec_per_page": round(el / max(len(done), 1), 2),
         "note": "CPU-only wheel, oneDNN off - speed NOT indicative of A100"},
        indent=1), encoding="utf-8")

    print(f"\n  {len(done)+len(skipped)}/{len(jobs)} pages "
          f"({len(skipped)} already on disk) · {el/60:.1f} min · "
          f"{len(errs)} error(s)")
    if done:
        print(f"  {el/len(done):.1f}s per new page (wall / new pages)")
    if errs and not done and not skipped:
        print("  ⚠ ZERO PAGES — the oneDNN crash again, not a score of zero.")


if __name__ == "__main__":
    main()
