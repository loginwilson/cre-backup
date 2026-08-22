"""DOES THE BACKER BLOCK NEED MORE PIXELS? Three pages hold all 7 universal misses.

    python backer_res.py                    # 1440 (current) vs 2880 vs 4320
    python backer_res.py --sides 2880

⚠ THE HYPOTHESIS, AND WHY IT IS NEW. A stamp-targeted second pass was already
tried and rejected - it "found nothing rotation didn't". But that experiment
changed the PROMPT. It never changed the PIXELS. Today's Qwen run showed these
readers are RESOLUTION-limited, not attention-limited: capping image tokens took
the digital class from 100% to 67% purely by starving detail, with output length
unchanged. So the backer block may not be ignored - it may be under-resolved.

PaddleOCR downsamples internally: `text_det_limit_side_len` defaults to 1440, so
a 2536px scan is shrunk before detection ever runs. A backer occupies maybe
10-15% of the page, which leaves its small, faint, overlapping stamp text a few
hundred pixels wide. This raises the detector's budget and changes nothing else.

⚠ THE SOURCE IS THE NATIVE FILE, NOT THE 1400px RENDER. Feeding an already
downsampled image to a bigger detector measures the resampler, not the page.

⚠ UNION, NEVER REPLACE. Page-cropping was measured to CUT TEXT OUT, so extra
passes are added to the whole-page read, never substituted for it. A pass that
finds 3 stamp fields while losing 12 body fields is a loss.

The 7 artifacts no engine has ever surfaced:
  film p010  aif_name Ariel Gratch · title_no 732441 · title_co ABSTRACT CORP
             · rec_tax RECORDING TAX
  book p006  notary SIDERMAN · rec_tax RECORDING TAX
  book p007  notary SIDERMAN
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
sys.path.insert(0, str(pathlib.Path(__file__).parent))

HERE = pathlib.Path(__file__).parent
TARGETS = [("BK_6730047100023", "p006", "answer_key_bookdoc.json"),
           ("BK_6730047100023", "p007", "answer_key_bookdoc.json"),
           ("FT_1680008647768", "p010", "answer_key_testdoc.json")]
_OCR = None


def init(side, threads):
    global _OCR
    import warnings as w
    w.filterwarnings("ignore")
    from paddleocr import PaddleOCR
    _OCR = PaddleOCR(ocr_version="PP-OCRv6", device="cpu", enable_mkldnn=False,
                     cpu_threads=threads, text_det_limit_side_len=side,
                     use_doc_orientation_classify=False, use_doc_unwarping=False,
                     use_textline_orientation=False)


def read(job):
    """One page at one angle, from the NATIVE file."""
    path, angle = job
    import numpy as np
    from PIL import Image
    im = Image.open(path)
    if angle:
        im = im.rotate(angle, expand=True)
    res = _OCR.predict(np.array(im.convert("RGB")))
    lines = []
    for r in res or []:
        j = r if isinstance(r, dict) else getattr(r, "json", {}) or {}
        j = j.get("res", j)
        lines += list(j.get("rec_texts") or [])
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sides", default="1440,2880")
    ap.add_argument("--angles", default="0,90,270")
    ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=420)
    a = ap.parse_args()
    sides = [int(x) for x in a.sides.split(",")]
    angles = [int(x) for x in a.angles.split(",")]

    import score as S
    keys = {}
    for _, _, kf in TARGETS:
        if kf not in keys:
            keys[kf] = {k: v for k, v in
                        json.loads((HERE / "keys" / kf).read_text(encoding="utf-8")).items()
                        if not k.startswith("_")}

    print(f"  PP-OCRv6 · native source · angles {angles} · "
          f"det_limit_side_len {sides}")
    print(f"  scoring ONLY the artifacts no engine has ever surfaced\n")

    WANT = {("BK_6730047100023", "p006"): ["notary", "rec_tax"],
            ("BK_6730047100023", "p007"): ["notary"],
            ("FT_1680008647768", "p010"): ["aif_name", "title_no", "title_co",
                                           "rec_tax"]}
    out = {}
    for side in sides:
        got = tot = 0
        print(f"  --- det_limit_side_len {side} ---")
        pool = Pool(1, initializer=init, initargs=(side, a.threads))
        try:
            for doc, pg, kf in TARGETS:
                src = HERE / "pages" / doc / f"{pg}.png"
                t, lines = time.time(), []
                bad = None
                for ang in angles:
                    try:
                        lines += pool.apply_async(read, ((str(src), ang),)).get(
                            timeout=a.timeout)
                    except Exception as e:
                        bad = type(e).__name__
                        pool.terminate(); pool.join()
                        pool = Pool(1, initializer=init,
                                    initargs=(side, a.threads))
                        break
                hay = S.norm(" ".join(lines))
                key = keys[kf][f"{pg}.png"]
                hits = []
                for aid in WANT[(doc, pg)]:
                    art = next(x for x in key["artifacts"] if x["id"] == aid)
                    ok = S.found(hay, art)
                    got += ok; tot += 1
                    hits.append(f"{aid}={'HIT' if ok else 'miss'}")
                d = HERE / "out" / f"ppv6-s{side}" / doc
                d.mkdir(parents=True, exist_ok=True)
                if lines:
                    (d / f"{pg}.png.txt").write_text(" ".join(lines),
                                                    encoding="utf-8")
                print(f"    {doc[:14]:14}/{pg}  {len(lines):4} lines "
                      f"{time.time()-t:5.0f}s  {'  '.join(hits)}"
                      f"{'  ['+bad+']' if bad else ''}", flush=True)
        finally:
            pool.terminate(); pool.join()
        out[side] = (got, tot)
        print(f"    -> {got}/{tot} of the never-surfaced artifacts\n")

    print("  RESULT")
    for side, (g, t) in out.items():
        print(f"    side_len {side:>5}: {g}/{t}")
    base = out.get(sides[0], (0, 1))[0]
    best = max(out.items(), key=lambda kv: kv[1][0])
    if best[1][0] > base:
        print(f"\n  Resolution IS the constraint: {best[0]} recovered "
              f"{best[1][0]-base} artifact(s) no engine had ever read.")
    else:
        print(f"\n  No gain from resolution. The backer misses are not a "
              f"pixel-budget problem, and a crop pass would not fix them "
              f"either - the next lever is a vision escalation, not more px.")


if __name__ == "__main__":
    main()
