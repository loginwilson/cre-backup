"""IS PP-OCRv6 AFFORDABLE INSIDE RAPIDOCR? The one variable never isolated.

    python rapid_v6.py

⚠ WHY THIS EXISTS. Every "RapidOCR vs Paddle" number in this project confounds THREE
variables at once: model tier (v4-mobile vs v6-medium), runtime (OpenVINO vs native
PaddlePaddle), and CPU acceleration (`enable_mkldnn=False` in pp_doc.py, disabled to
dodge a `ConvertPirAttribute2RuntimeAttribute` crash on this Intel box). The measured
gap was ~60x, and none of it could be attributed. The modern `rapidocr` package lets
the SAME OpenVINO runtime load v4/v5/v6 at any tier, so model version can finally be
changed on its own.

⚠ SCORED ON ARTIFACTS, NOT CHARACTERS. Characters reward noise — rotated passes have
already been shown to inflate token counts without adding a single artifact. The
answer keys are the arbiter, and every rate carries its denominator.

⚠ AND SPEED IS MEASURED AFTER WARM-UP. First call pays model download and graph
compile; quoting that as throughput is the same cold-start error that made an
orientation run look 6x faster than it was.
"""
from __future__ import annotations

import json, pathlib, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
DEC = HERE.parent
sys.path.insert(0, str(HERE))

import score as S

THREADS = 8

PAGES = [("BK_6730047100023", "p007", "answer_key_bookdoc.json", "sideways backer"),
         ("FT_1680008647768", "p001", "answer_key_testdoc.json", "film money page"),
         ("FT_1680008647768", "p010", "answer_key_testdoc.json", "film backer"),
         ("2015022400608001", "p001", "answer_key_moderndoc.json", "digital")]

# ⚠ v6 HAS THREE TIERS AND MEDIUM IS THE HEAVIEST. The PP-OCRv6 paper is titled
# "From 1.5M to 34.5M Parameters" — tiny is 1.5M. Testing only `medium` measured the
# most expensive point on the curve and concluded v6 costs 6x, which is a statement
# about a TIER, not about a VERSION.
CONFIGS = [
    ("v4-mobile  (today)", "PP-OCRv4", "mobile"),
    ("v6-tiny", "PP-OCRv6", "tiny"),
    ("v6-small", "PP-OCRv6", "small"),
    ("v6-medium", "PP-OCRv6", "medium"),
]


def arts_for(doc, page, keyfile):
    k = json.loads((DEC / keyfile).read_text(encoding="utf-8"))
    blk = k.get(page + ".png") or {}
    return [a for a in blk.get("artifacts", [])
            if a.get("tier") == "CRITICAL" and not a.get("ambiguous")]


def build(ver, tier):
    from rapidocr import RapidOCR, EngineType, ModelType, OCRVersion, LangDet, LangRec
    return RapidOCR(params={
        "Det.engine_type": EngineType.OPENVINO,
        "Det.lang_type": LangDet.CH,
        "Det.model_type": ModelType(tier),
        "Det.ocr_version": OCRVersion(ver),
        "Rec.engine_type": EngineType.OPENVINO,
        "Rec.lang_type": LangRec.CH,
        "Rec.model_type": ModelType(tier),
        "Rec.ocr_version": OCRVersion(ver),
        # ⚠ THE RUNTIME WAS LOGGING "Using OpenVINO config: {}" — no thread tuning
        # whatsoever, while devr_sweep has always pinned INFERENCE_NUM_THREADS.
        # An untuned runtime is not a fair reading of a model's cost.
        "Det.engine_cfg.openvino.inference_num_threads": THREADS,
        "Rec.engine_cfg.openvino.inference_num_threads": THREADS,
    })


def main():
    from PIL import Image
    import numpy as np
    Image.MAX_IMAGE_PIXELS = None

    rows = []
    for label, ver, tier in CONFIGS:
        try:
            ocr = build(ver, tier)
        except Exception as e:
            print(f"  {label:<20} UNAVAILABLE: {type(e).__name__}: {str(e)[:90]}")
            continue
        # ⚠ WARM-UP IS NOT A MEASUREMENT. Download + graph compile land on call one.
        warm = HERE / "pages" / PAGES[0][0] / f"{PAGES[0][1]}.png"
        try:
            ocr(np.array(Image.open(warm).convert("RGB")))
        except Exception as e:
            print(f"  {label:<20} warm-up failed: {type(e).__name__}: {str(e)[:80]}")
            continue

        tot_hit = tot_n = 0
        secs = []
        detail = []
        for doc, page, keyfile, what in PAGES:
            p = HERE / "pages" / doc / f"{page}.png"
            if not p.exists():
                continue
            arts = arts_for(doc, page, keyfile)
            if not arts:
                continue
            a = np.array(Image.open(p).convert("RGB"))
            t = time.time()
            res = ocr(a)
            el = time.time() - t
            txts = list(getattr(res, "txts", None) or [])
            n = S.norm(" ".join(txts))
            hit = sum(1 for x in arts if S.found(n, x) or S.pointed(n, x))
            tot_hit += hit
            tot_n += len(arts)
            secs.append(el)
            detail.append((what, hit, len(arts), el))
        if not tot_n:
            continue
        rows.append((label, tot_hit, tot_n, sum(secs) / len(secs), detail))

    print(f"\n  {'config':<20}{'hit':>5}{'of':>5}{'recall':>9}{'s/page':>9}")
    print("  " + "-" * 48)
    for label, h, n, sp, _d in rows:
        print(f"  {label:<20}{h:>5}{n:>5}{h/n:>9.1%}{sp:>9.2f}")
    print(f"\n  per page (hit/of · seconds)")
    for label, _h, _n, _sp, detail in rows:
        print(f"    {label}")
        for what, h, n, el in detail:
            print(f"       {what:<18}{h:>3}/{n:<4}{el:>7.2f}s")
    json.dump({"configs": [{"config": l, "hit": h, "of": n, "recall": h / n,
                            "sec_per_page": sp,
                            "pages": [{"page": w, "hit": hh, "of": nn, "sec": s}
                                      for w, hh, nn, s in d]}
                           for l, h, n, sp, d in rows]},
              open(HERE / "_rapid_v6.json", "w"), indent=1)
    print("\n  wrote _rapid_v6.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
