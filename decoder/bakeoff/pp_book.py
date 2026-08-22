"""PP-OCRv6 OVER THE BOUND-BOOK DOCUMENT, WITH ROTATION. Book is PP's only gap.

    python pp_book.py                      # upright + 90 + 270, union
    python pp_book.py --doc FT_1680008647768
    python pp_book.py --angles 0           # baseline, no rotation

⚠ THIS TESTS ONE HYPOTHESIS AND NOTHING ELSE. On the 20 pages every engine
produced, PP-OCRv6 beat Qwen3-VL-4B on FILM (89% vs 87%) and lost badly on BOOK
(77% vs 94%). The whole blended gap is that one class. The book pages are the
ones carrying a backer printed sideways, and PP ran with
`use_doc_orientation_classify=False`, so sideways text was never readable. If
rotation closes it, PP's book number was a config artifact, not a limit of the
engine.

⚠ ROTATION, NOT A CLASSIFIER FLAG. run.py already measured this on the VLM side:
the backer block - recording tax, City Register stamp, county - is recovered by
rotating the page and by NOTHING else. Paddle's own orientation classifier is
another model that can be wrong silently; feeding it three known angles and
taking the union cannot be. The cost is 3x the pages, which is exactly why the
delta between angles=0 and angles=0,90,270 is worth measuring rather than
assuming - on a 148M-page corpus, 3x is not a rounding error.

⚠ EVERY PAGE GETS A HARD TIMEOUT. p007 - the backer - ran >10 minutes inside
pool.map with no per-page limit, blocked the whole pool, and had to be killed;
it produced no file and no error, so it silently vanished from the scored set
and PP's book number was computed WITHOUT the hardest page in the class. A page
that exceeds the limit is recorded as a TIMEOUT, which is a finding. Silence is
not.

⚠ AND A CRASH OR TIMEOUT MUST LEAVE NO FILE. An empty .txt is indistinguishable
from an engine that read the page and found nothing. That mistake has now been
made three times in this project - Paddle crashing to an empty directory and
scoring 0%, four vision calls dying into "the pixels are worth -3.3 points", and
Qwen3.5 writing five zero-byte transcriptions that resume would have skipped
forever as "done".
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
_OCR = None


def init(threads, orient):
    global _OCR
    import warnings as w
    w.filterwarnings("ignore")
    from paddleocr import PaddleOCR
    # ⚠ enable_mkldnn=False IS NOT A TUNING CHOICE. oneDNN throws
    # ConvertPirAttribute2RuntimeAttribute on this Intel box and has killed five
    # separate attempts. It costs speed, and speed from this machine was never
    # the number being collected - PP-OCRv6's 0.13 s/page is an A100 figure.
    _OCR = PaddleOCR(ocr_version="PP-OCRv6", device="cpu", enable_mkldnn=False,
                     cpu_threads=threads,
                     use_doc_orientation_classify=orient,
                     use_doc_unwarping=False,
                     use_textline_orientation=orient)


def _read(args):
    """Runs in the pool worker. Returns text for ONE page at ONE angle."""
    path, angle = args
    from PIL import Image
    p = pathlib.Path(path)
    if angle:
        from io import BytesIO
        import numpy as np
        im = Image.open(p)
        im = im.rotate(angle, expand=True)
        src = np.array(im.convert("RGB"))
    else:
        src = str(p)
    res = _OCR.predict(src)
    lines = []
    for r in res or []:
        j = r if isinstance(r, dict) else getattr(r, "json", {}) or {}
        j = j.get("res", j)
        lines += list(j.get("rec_texts") or [])
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default="BK_6730047100023")
    ap.add_argument("--angles", default="0,90,270")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--orient", type=int, default=1)
    ap.add_argument("--page-timeout", type=int, default=420)
    a = ap.parse_args()

    angles = [int(x) for x in a.angles.split(",") if x.strip()]
    tag = a.tag or ("ppv6-rot" if len(angles) > 1 else "ppv6")
    out = HERE / "out" / tag / a.doc
    out.mkdir(parents=True, exist_ok=True)

    pages = sorted((HERE / "pages" / a.doc).glob("p*.png"))
    print(f"  PP-OCRv6 · {a.doc} · {len(pages)} pages · angles {angles}")
    print(f"  orientation models {'ON' if a.orient else 'off'} · "
          f"{a.threads} threads · {a.page_timeout}s per page-angle")
    print(f"  -> out/{tag}\n")

    rows, t0 = [], time.time()
    # One persistent worker; the parent enforces the timeout and REPLACES the
    # pool if a page wedges it, so one bad page cannot stall the rest.
    pool = Pool(1, initializer=init, initargs=(a.threads, bool(a.orient)))
    try:
        for pg in pages:
            f = out / (pg.stem + ".png.txt")
            if f.exists() and f.stat().st_size > 0:
                print(f"    {pg.name}  (on disk, skipped)")
                continue
            allt, status, t = [], "ok", time.time()
            for ang in angles:
                try:
                    r = pool.apply_async(_read, ((str(pg), ang),))
                    allt += r.get(timeout=a.page_timeout)
                except Exception as e:
                    status = (f"TIMEOUT@{ang}" if "Timeout" in type(e).__name__
                              else f"{type(e).__name__}@{ang}")
                    print(f"    {pg.name}  r{ang}  {status}")
                    pool.terminate(); pool.join()
                    pool = Pool(1, initializer=init,
                                initargs=(a.threads, bool(a.orient)))
                    break
            el = time.time() - t
            if status == "ok" and allt:
                f.write_text(" ".join(allt), encoding="utf-8")
                print(f"    {pg.name}  {len(allt):4} lines  {el:6.0f}s")
            else:
                # ⚠ NO FILE. See the header - an empty file would be scored as
                # a legitimate read of a blank page.
                print(f"    {pg.name}  NO OUTPUT ({status})  {el:6.0f}s")
            rows.append({"page": pg.name, "lines": len(allt),
                         "sec": round(el, 1), "status": status})
    finally:
        pool.terminate(); pool.join()

    el = time.time() - t0
    (HERE / "out" / tag / f"run_{a.doc}.json").write_text(json.dumps(
        {"engine": tag, "model": "PP-OCRv6_medium", "device": "cpu",
         "mkldnn": False, "doc": a.doc, "angles": angles,
         "orientation_models": bool(a.orient), "threads": a.threads,
         "page_timeout": a.page_timeout, "pages": rows, "sec": round(el, 1),
         "note": "CPU-only wheel, oneDNN off - speed NOT indicative of A100"},
        indent=1), encoding="utf-8")

    bad = [r for r in rows if r["status"] != "ok"]
    print(f"\n  {len(rows)-len(bad)}/{len(rows)} pages read · {el/60:.1f} min · "
          f"{len(bad)} failed")
    for r in bad:
        print(f"    ⚠ {r['page']}: {r['status']} - NOT scored, not zero")


if __name__ == "__main__":
    main()
