"""PP-OCRv6 OVER THE THREE KEYED DOCUMENTS. Non-generative, for the verifier slot.

    python run_ppocr.py                       # PP-OCRv6 medium, CPU
    python run_ppocr.py --version PP-OCRv5    # compare against the previous gen

⚠ WHY THIS ENGINE IS WORTH A ROW. PP-OCRv6 (PaddleOCR 3.7.0, June 2026) is
34.5M parameters - millions, not billions - and its paper claims it beats
Qwen3-VL-235B, GPT-5.5 and Gemini-3.1-Pro on OCR, at 0.13s/page on an A100.
If that transfers, the verifier slot costs almost nothing.

⚠ AND WHY THE CLAIM CANNOT BE TAKEN ON FAITH. Those benchmarks are clean modern
documents. This corpus is 1967 microfilm with a faint dot-matrix stamp, a backer
printed sideways, and handwriting - the exact conditions no OCR benchmark
measures. The same caveat already applied to OmniDocBench, where the leaders are
tuned to emit tidy markdown and the thing we need is six characters in a corner.

⚠ PADDLE HAS CRASHED ON THIS MACHINE FOUR TIMES, inside oneDNN
(`ConvertPirAttribute2RuntimeAttribute`), producing 0 pages while the harness
reported a clean finish. That was an Intel-backend problem, not a Paddle
problem, and it is why RapidOCR (the same PP models via ONNX Runtime) has been
the working stand-in. So: mkldnn is disabled, and A CRASH MUST LEAVE NO FILE -
an empty .txt is indistinguishable from an engine that read the page and found
nothing, and those are opposite findings.
"""
import argparse
import json
import pathlib
import sys
import time
import warnings

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

HERE = pathlib.Path(__file__).parent
PAGES = HERE / "pages"
OUT = HERE / "out"


def build(version, device, threads, mkldnn, batch, side_len):
    """⚠ TUNED, NOT DEFAULT. Measuring an engine at its defaults while another
    engine runs 8-wide is the sandbagging this project already committed once:
    RapidOCR was reported at 0.072 pages/s from ONE process while Tesseract ran
    across all cores, and it looked like the slowest engine on the board when it
    was actually the most accurate. Paddle's CPU path is mkldnn + cpu_threads;
    running it single-threaded and un-accelerated would repeat that mistake
    pointed at PP-OCRv6.

    ⚠ PP-OCRv6 DEFAULTS TO THE MEDIUM MODELS. `ocr_version="PP-OCRv6"` resolves
    to PP-OCRv6_medium_det / PP-OCRv6_medium_rec in
    paddleocr/_pipelines/ocr.py:331 - so medium is what is being measured, and
    it is named explicitly here rather than trusted to a default that could move.
    """
    from paddleocr import PaddleOCR
    kw = dict(ocr_version=version, device=device,
              text_detection_model_name=f"{version}_medium_det",
              text_recognition_model_name=f"{version}_medium_rec",
              use_doc_orientation_classify=False,
              use_doc_unwarping=False,
              use_textline_orientation=False,
              cpu_threads=threads,
              enable_mkldnn=mkldnn,
              mkldnn_cache_capacity=10,
              text_recognition_batch_size=batch,
              text_det_limit_side_len=side_len)
    try:
        return PaddleOCR(**kw), kw
    except Exception as e:
        # ⚠ mkldnn IS what crashed this machine four times inside
        # ConvertPirAttribute2RuntimeAttribute. Falling back is allowed; falling
        # back SILENTLY is not - the config actually used is recorded.
        if not mkldnn:
            raise
        print(f"    mkldnn build failed ({type(e).__name__}) - retrying without it")
        kw["enable_mkldnn"] = False
        return PaddleOCR(**kw), kw


def texts(res):
    """⚠ PADDLEOCR 3.x CHANGED THE RESULT SHAPE and a wrong guess here would
    read as 'the engine found nothing' rather than 'I parsed it wrong'. So every
    known shape is tried and an unrecognised one raises rather than returning
    empty."""
    out = []
    for r in (res or []):
        if isinstance(r, dict) and "rec_texts" in r:
            out += list(r["rec_texts"]); continue
        d = getattr(r, "json", None)
        if isinstance(d, dict):
            d = d.get("res", d)
            if "rec_texts" in d:
                out += list(d["rec_texts"]); continue
        if isinstance(r, (list, tuple)):
            for line in r:
                if isinstance(line, (list, tuple)) and len(line) > 1:
                    t = line[1]
                    out.append(t[0] if isinstance(t, (list, tuple)) else str(t))
            continue
        raise RuntimeError(f"unrecognised PaddleOCR result type {type(r)}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="PP-OCRv6")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--tag", default=None)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--mkldnn", type=int, default=1)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--side-len", type=int, default=1440)
    a = ap.parse_args()
    tag = a.tag or a.version.lower().replace("-", "")

    print(f"  {tag}: {a.version} on {a.device}")
    t_load = time.time()
    try:
        ocr, cfg = build(a.version, a.device, a.threads, bool(a.mkldnn),
                         a.batch, a.side_len)
    except Exception as e:
        print(f"  FAILED TO BUILD: {type(e).__name__}: {str(e)[:300]}")
        return
    print(f"  loaded in {time.time()-t_load:.1f}s\n")

    jobs = [(d.name, p) for d in sorted(x for x in PAGES.iterdir() if x.is_dir())
            for p in sorted(d.glob("p*.png"))]
    t0, ok, errs = time.time(), 0, []
    for docn, pg in jobs:
        o = OUT / tag / docn
        o.mkdir(parents=True, exist_ok=True)
        f = o / (pg.stem + ".png.txt")
        if f.exists():
            ok += 1; continue
        try:
            res = ocr.predict(str(pg)) if hasattr(ocr, "predict") else ocr.ocr(str(pg))
            txt = " ".join(texts(res))
        except Exception as e:
            errs.append((docn, pg.name, f"{type(e).__name__}: {str(e)[:120]}"))
            continue
        f.write_text(txt, encoding="utf-8")
        ok += 1
    el = time.time() - t0

    (OUT / tag / "run.json").write_text(json.dumps({
        "engine": tag, "model": a.version, "device": a.device, "rot": False,
        "pages": ok, "errors": errs, "sec": round(el, 1), "cfg": {k: v for k, v in cfg.items() if isinstance(v, (int, bool, str))},
        "sec_per_page": round(el / max(ok, 1), 2)}, indent=1), encoding="utf-8")

    print(f"  {ok}/{len(jobs)} pages · {el:.1f}s · {el/max(ok,1):.2f} s/page · "
          f"{len(errs)} error(s)")
    for e in errs[:5]:
        print(f"    FAILED {e[0]} {e[1]}: {e[2]}")
    if errs and not ok:
        print("  ⚠ ZERO PAGES. This is the oneDNN crash again, not a score of zero.")


if __name__ == "__main__":
    main()
