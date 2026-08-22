"""OCR CONFIG SWEEP. Same pages, same machine, one variable at a time.

    python pp_sweep.py
    python pp_sweep.py --pages pages/BK_6730047100023/p001.png --threads 3,7

⚠ THIS EXISTS BECAUSE THE NUMBERS WE HAD WERE NOT COMPARABLE AND SAID SO.
`out/tesseract/run.json` and `out/rapidpool/run.json` both carry the note "wall
time from earlier local runs, NOT comparable to" - and were quoted anyway, as
0.7 s/page against Paddle's 84 s/page, which made Paddle look 120x slower than
an engine it was never measured against. `_ocr_bench.json` records 12.26 s/page
with no record of WHICH PAGES, so the 6x gap against our film scans may be
config, may be material, and nothing on disk can tell them apart.

⚠ SPEED ALONE IS THE WRONG MEASUREMENT AND WOULD PICK THE WRONG CONFIG.
`text_det_limit_side_len` is a DETECTION resolution: lowering it makes every
page faster and makes small text disappear - stamps, marginalia, the
handwritten figures that are the entire reason this corpus is being decoded. A
timing-only sweep would report a config that finds 90% of the lines as a clean
2x win. So every run here records lines, characters, and token recall against
the richest config seen, and the summary refuses to rank on seconds alone.

⚠ MODEL LOAD IS NOT PAGE TIME. Each config constructs a fresh PaddleOCR, which
costs seconds that have nothing to do with throughput. Init is timed separately
and excluded from sec/page, because at 148M pages the model is loaded once and
the per-page number is the only one that scales.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import warnings

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

HERE = pathlib.Path(__file__).parent
TOKEN = re.compile(r"\S+")


def norm(t):
    return re.sub(r"[^0-9a-z]", "", t.lower())


def toks(text):
    return {norm(w) for w in TOKEN.findall(text) if norm(w)}


def run_config(threads, side, pages):
    from paddleocr import PaddleOCR
    import numpy as np
    from PIL import Image

    t0 = time.time()
    ocr = PaddleOCR(ocr_version="PP-OCRv6", device="cpu", enable_mkldnn=False,
                    cpu_threads=threads, text_det_limit_side_len=side,
                    use_doc_orientation_classify=False, use_doc_unwarping=False,
                    use_textline_orientation=False)
    init_s = time.time() - t0

    out = []
    for p in pages:
        im = Image.open(p)
        t = time.time()
        res = ocr.predict(np.array(im.convert("RGB")))
        el = time.time() - t
        texts = []
        for r in res or []:
            j = r if isinstance(r, dict) else getattr(r, "json", {}) or {}
            j = j.get("res", j)
            texts += list(j.get("rec_texts") or [])
        txt = " ".join(texts)
        out.append({"page": p.name, "sec": round(el, 1), "lines": len(texts),
                    "chars": len(txt), "text": txt})
    return init_s, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="pages/FT_1680008647768/p001.png,"
                                       "pages/BK_6730047100023/p001.png")
    ap.add_argument("--threads", default="3,7")
    ap.add_argument("--sides", default="960,1440")
    a = ap.parse_args()

    pages = [pathlib.Path(x if pathlib.Path(x).is_absolute() else HERE / x)
             for x in a.pages.split(",") if x.strip()]
    for p in pages:
        if not p.exists():
            raise SystemExit(f"  missing page {p}")
    threads = [int(x) for x in a.threads.split(",")]
    sides = [int(x) for x in a.sides.split(",")]

    from PIL import Image
    print("  pages under test:")
    for p in pages:
        with Image.open(p) as im:
            print(f"    {p.parent.name}/{p.name}  {im.size[0]}x{im.size[1]}")
    print(f"  grid: threads {threads} x side {sides} = "
          f"{len(threads)*len(sides)} configs x {len(pages)} pages\n", flush=True)

    rows = []
    for side in sides:
        for th in threads:
            print(f"  --- threads={th} side={side} ---", flush=True)
            init_s, res = run_config(th, side, pages)
            for r in res:
                r.update(threads=th, side=side, init_s=round(init_s, 1))
                rows.append(r)
                print(f"    {r['page']:12} {r['sec']:>6.1f}s  "
                      f"{r['lines']:>4} lines  {r['chars']:>6} chars"
                      f"   (init {init_s:.0f}s)", flush=True)

    # ⚠ RECALL IS MEASURED AGAINST THE UNION OF EVERY CONFIG, not against the
    # slowest one. The slowest is not automatically the most complete, and
    # assuming it is would hide a config that finds text the others all miss.
    per_page_union = {}
    for r in rows:
        per_page_union.setdefault(r["page"], set()).update(toks(r["text"]))
    for r in rows:
        u = per_page_union[r["page"]]
        r["recall"] = round(len(toks(r["text"]) & u) / len(u), 4) if u else None
        del r["text"]

    print("\n  " + "=" * 74)
    print(f"  {'threads':>7} {'side':>5} {'page':12} {'sec':>7} {'lines':>6} "
          f"{'chars':>7} {'recall':>7}")
    for r in sorted(rows, key=lambda x: (x["page"], x["side"], x["threads"])):
        print(f"  {r['threads']:>7} {r['side']:>5} {r['page']:12} "
              f"{r['sec']:>7.1f} {r['lines']:>6} {r['chars']:>7} "
              f"{r['recall']:>7.1%}")

    print("\n  totals per config (all pages):")
    agg = {}
    for r in rows:
        k = (r["threads"], r["side"])
        d = agg.setdefault(k, {"sec": 0.0, "lines": 0, "rec": []})
        d["sec"] += r["sec"]; d["lines"] += r["lines"]; d["rec"].append(r["recall"])
    base = agg.get((min(threads), max(sides)))
    for k in sorted(agg):
        d = agg[k]
        mr = sum(d["rec"]) / len(d["rec"])
        sp = (base["sec"] / d["sec"]) if base and d["sec"] else 1.0
        lost = "" if mr > 0.995 else f"   <- LOSES {1-mr:.1%} of tokens"
        print(f"    threads={k[0]} side={k[1]:>5}  {d['sec']:>7.1f}s total  "
              f"{sp:>4.1f}x  recall {mr:>6.1%}{lost}")
    (HERE / "_pp_sweep.json").write_text(json.dumps(rows, indent=1),
                                         encoding="utf-8")
    print(f"\n  -> {HERE / '_pp_sweep.json'}")


if __name__ == "__main__":
    main()
