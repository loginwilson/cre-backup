"""PP-OCRv6 OVER AN ARBITRARY FOLDER OF PAGE IMAGES. Canonical text for the resolver.

    python pp_doc.py --src ../render/funnel/2008022800439001 --tag doc439001
    python pp_doc.py --src ../render/sample --tag sample --angles 0

⚠ THIS IS NOT A BENCHMARK, IT IS AN INPUT STAGE. There is no answer key for
these pages, so nothing here produces a score. Its output is the canonical text
the resolution work needs - claims, events, roles, direction - on a REAL
multi-page instrument rather than the three keyed documents, which are too few
to exercise cross-page reference ("subject to the mortgage recorded in Reel...").

⚠ CPU ONLY, AND DELIBERATELY THROTTLED. The iGPU shares system RAM with the OS,
so a VLM and PaddleOCR cannot both run - measured 2026-08-12: PP on 3 threads
alongside llama-server drove CPU to 99%, free RAM to 0.3 GB, and VLM pages from
40s to 754s. Nothing else heavy should run while this does.

⚠ ROTATION IS OPTIONAL AND COSTS 3x. On bound-book and film pages the backer is
sideways and only rotation recovers it (measured: PP book 77% -> 82%). On
born-digital pages it buys nothing and triples the bill. Default is upright;
pass --angles 0,90,270 for historical scans.

⚠ A CRASH OR TIMEOUT LEAVES NO FILE. An empty .txt is indistinguishable from a
page that was read and found empty, and resume would skip it forever.
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


def init(threads, side):
    global _OCR
    import warnings as w
    w.filterwarnings("ignore")
    # ⚠ THIS ONE LINE IS WHY PADDLE "DIDN'T WORK" ON THIS MACHINE. PaddleOCR 3.x
    # phones the model hosters on every construction — "Checking connectivity to
    # the model hosters, this may take a while" — and on a slow or filtered
    # connection it never returns. Zero output, ~0% CPU, indistinguishable from
    # a slow job. The weights were cached the whole time
    # (~/.paddlex/official_models/PP-OCRv6_medium_det and _rec).
    # ⚠ Must be set BEFORE paddleocr is imported.
    import os as _os
    _os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
    from paddleocr import PaddleOCR
    # enable_mkldnn=False is not tuning: oneDNN throws
    # ConvertPirAttribute2RuntimeAttribute on this Intel box and killed five runs.
    # ⚠ `ocr_version=` IS NOT A PARAMETER IN PaddleOCR 3.7 AND NEVER SELECTED v6.
    # The 3.7 constructor takes explicit model names; an unknown kwarg was
    # accepted and ignored, so every run that "requested PP-OCRv6" silently
    # requested the default. Measured 2026-08-14 against the real signature.
    _OCR = PaddleOCR(text_detection_model_name="PP-OCRv6_medium_det",
                     text_recognition_model_name="PP-OCRv6_medium_rec",
                     device="cpu", enable_mkldnn=False,
                     cpu_threads=threads, text_det_limit_side_len=side,
                     use_doc_orientation_classify=False, use_doc_unwarping=False,
                     use_textline_orientation=True)


def read(job):
    path, angle = job
    import numpy as np
    from PIL import Image
    im = Image.open(path)
    if angle:
        im = im.rotate(angle, expand=True)
    res = _OCR.predict(np.array(im.convert("RGB")))
    out = []
    for r in res or []:
        j = r if isinstance(r, dict) else getattr(r, "json", {}) or {}
        j = j.get("res", j)
        texts = list(j.get("rec_texts") or [])
        # ⚠ KEEP THE POLYGONS. A VLM emits text with no coordinates; Paddle emits
        # boxes. Those boxes are the only thing that lets a human - or a crop
        # escalation - be shown WHERE an unresolved span sits on the page.
        # Discarding them means recomputing the whole corpus to get them back.
        polys = list(j.get("rec_polys") or j.get("dt_polys") or [])
        for i, t in enumerate(texts):
            box = polys[i] if i < len(polys) else None
            out.append({"text": t,
                        "box": [[int(x), int(y)] for x, y in box] if box is not None else None,
                        "angle": angle})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--angles", default="0")
    ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--side", type=int, default=1440)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    src = pathlib.Path(a.src)
    if not src.is_absolute():
        src = (HERE / a.src).resolve()
    angles = [int(x) for x in a.angles.split(",") if x.strip()]
    out = HERE / "out" / a.tag
    out.mkdir(parents=True, exist_ok=True)

    pages = sorted([p for p in src.rglob("*")
                    if p.suffix.lower() in (".png", ".tif", ".tiff", ".jpg")])
    if a.limit:
        pages = pages[:a.limit]
    # ⚠ ZERO PAGES IS A BROKEN PATH, NOT AN EMPTY JOB. A relative --src resolves
    # against THIS file's directory, so a caller passing "bakeoff/pages/X" from
    # the repo root silently matched nothing and the run reported success.
    if not pages:
        raise SystemExit(f"  NO PAGES matched under {src} - refusing to report "
                         f"a successful run over an empty set")
    print(f"  PP-OCRv6 · {src.name} · {len(pages)} pages · angles {angles} · "
          f"{a.threads} threads")
    print(f"  -> out/{a.tag}\n", flush=True)

    rows, t0 = [], time.time()
    pool = Pool(1, initializer=init, initargs=(a.threads, a.side))
    try:
        for i, pg in enumerate(pages, 1):
            f = out / (pg.stem + ".txt")
            if f.exists() and f.stat().st_size > 0:
                print(f"  {i:>3}/{len(pages)} {pg.name:22} (on disk)", flush=True)
                continue
            items, status, t = [], "ok", time.time()
            for ang in angles:
                try:
                    items += pool.apply_async(read, ((str(pg), ang),)).get(
                        timeout=a.timeout)
                except Exception as e:
                    status = f"{type(e).__name__}@{ang}"
                    pool.terminate(); pool.join()
                    pool = Pool(1, initializer=init,
                                initargs=(a.threads, a.side))
                    break
            el = time.time() - t
            if items:
                f.write_text(" ".join(x["text"] for x in items), encoding="utf-8")
                (out / (pg.stem + ".json")).write_text(
                    json.dumps({"page": pg.name, "items": items}, indent=1),
                    encoding="utf-8")
                print(f"  {i:>3}/{len(pages)} {pg.name:22} {len(items):4} lines "
                      f"{el:5.0f}s {status}", flush=True)
            else:
                print(f"  {i:>3}/{len(pages)} {pg.name:22} NO OUTPUT {el:5.0f}s "
                      f"{status}", flush=True)
            rows.append({"page": pg.name, "lines": len(items),
                         "sec": round(el, 1), "status": status})
    finally:
        pool.terminate(); pool.join()

    (out / "run.json").write_text(json.dumps(
        {"tag": a.tag, "src": str(src), "angles": angles, "side": a.side,
         "pages": rows, "sec": round(time.time() - t0, 1)}, indent=1),
        encoding="utf-8")
    ok = [r for r in rows if r["status"] == "ok"]
    print(f"\n  {len(ok)}/{len(rows)} pages · {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
