"""DOES OCR NEED FULL RESOLUTION? Speed AND recall, measured together.

⚠ THE UNTESTED LEVER. Every OCR run in this project has fed the full
2550x3300 scan. Detection cost scales with pixel count, so half-scale is
roughly a quarter of the work — potentially 3-4x throughput. Nobody has
checked what it costs in recall, so nobody knows whether it is free money or
a silent accuracy loss.

⚠ AND SPEED ALONE IS NOT THE ANSWER. A 4x faster pass that finds 40% of the
clauses has made extraction worse, not better — it just fails sooner. So this
measures BOTH on the same pages, against text a human actually read off those
pages (groundtruth.py), and reports them side by side.

⚠ RECALL HERE IS *LOCATE*, NOT TRANSCRIPTION. The pipeline never lets an OCR
string become a claim value — numbers come from vision on a crop. So the
question is only "does the clause still get FOUND at this scale", which is
exactly what phrase_recall measures.
"""
import json
import os
import pathlib
import statistics
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
from PIL import Image

import groundtruth
import ocr_probe

SCALES = (1.0, 0.75, 0.5, 0.35)
TMP = pathlib.Path("_scaled")


def page_file(doc, pg):
    for root in ("ocr_pages", "pages_out"):
        f = pathlib.Path(root) / doc / f"p{pg:03d}.png"
        if f.exists():
            return f
    return None


def scaled(src, s):
    if s == 1.0:
        return src
    TMP.mkdir(exist_ok=True)
    out = TMP / f"{src.parent.name}_{src.stem}_{int(s*100)}.png"
    if not out.exists():
        im = Image.open(src)
        im.resize((int(im.width * s), int(im.height * s)),
                  Image.LANCZOS).save(out)
    return out


def main(limit=14):
    GT = groundtruth.load()
    work = [(d, p, page_file(d, p)) for (d, p) in GT if page_file(d, p)]
    work = work[:limit]
    print(f"{len(work)} pages with human-read ground truth\n")
    eng = ocr_probe.engine()

    print(f"{'scale':>7}{'sec/pg':>9}{'pg/hr':>9}{'LOCATE':>9}{'chars':>8}")
    rows = []
    for s in SCALES:
        secs, recalls, chars = [], [], []
        for doc, pg, f in work:
            fp = scaled(f, s)
            t = time.time()
            try:
                res, _ = eng(str(fp))
            except Exception:
                continue
            secs.append(time.time() - t)
            txt = " ".join(r[1] for r in res) if res else ""
            chars.append(len(txt))
            spans = GT[(doc, pg)]
            recalls.append(statistics.mean(
                [ocr_probe.phrase_recall(txt, q) for q in spans]))
        if not secs:
            continue
        sp = statistics.mean(secs)
        row = {"scale": s, "sec_per_page": round(sp, 2),
               "pages_per_hour": round(3600 / sp),
               "locate": round(statistics.mean(recalls), 3),
               "chars": round(statistics.mean(chars))}
        rows.append(row)
        print(f"{s:>7.2f}{row['sec_per_page']:>9}{row['pages_per_hour']:>9,}"
              f"{row['locate']:>9.3f}{row['chars']:>8,}")

    base = rows[0]
    print(f"\n{'='*62}")
    print(f"{'scale':>7}{'speed':>9}{'recall kept':>13}{'verdict':>26}")
    for r in rows:
        sx = r["pages_per_hour"] / base["pages_per_hour"]
        rk = r["locate"] / base["locate"] if base["locate"] else 0
        # ⚠ THE TRADE, STATED EXPLICITLY. Speed is worthless if recall goes
        # with it; the useful setting is the fastest one that keeps ~all of it.
        if rk >= 0.97:
            v = "FREE — take it"
        elif rk >= 0.90:
            v = "cheap, judgement call"
        else:
            v = "TOO LOSSY"
        print(f"{r['scale']:>7.2f}{sx:>8.2f}x{rk*100:>12.0f}%{v:>26}")
    best = None
    for r in rows:
        if base["locate"] and r["locate"] / base["locate"] >= 0.97:
            if best is None or r["pages_per_hour"] > best["pages_per_hour"]:
                best = r
    if best:
        pph = best["pages_per_hour"] * 4          # 4 CPU workers, measured clean
        print(f"\n  best lossless scale {best['scale']:.2f} -> "
              f"{best['pages_per_hour']:,} pg/hr single, ~{pph:,} at 4 workers")
        print(f"  DEVR    42,928 pages : {42928/pph/24:>5.1f} days")
        print(f"  zoning 480,455      : {480455/pph/24:>5.1f} days")
        print(f"  corpus  140.2M      : {140.2e6/pph/24/365:>5.1f} years")
    json.dump(rows, open("_ocr_scale.json", "w"), indent=1)
    print("\n  ⚠ small n — this sizes the effect, it does not certify it.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 14)
