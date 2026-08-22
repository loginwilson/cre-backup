"""CHEAP OCR SWEEP OVER DEVR DOCUMENTS — pattern discovery, not accuracy.

⚠ THIS IS THE CHEAP PASS ON PURPOSE. Login, 2026-08-14: "run cheap paddle over
tons of docs to see if we can locate patterns that determine how docs get
resolved when fused." Its output feeds the phrase lexicon and the trigger audit;
it is NOT the corpus read and must never be scored as one.

⚠ MODEL CHOICE HERE IS A COST DECISION, MEASURED 2026-08-14 on the same pages:
    PP-OCRv4 via OpenVINO    2.02 s/page   7,438 chars
    PP-OCRv6_medium native  65.14 s/page   8,166 chars   <- 32x for +9.8% text
v6_medium is a server model. This sweep would take 16 hours on it instead of 30
minutes. v6 belongs on Torch with a GPU and batching, where the trade inverts.

⚠ ALL PAGES, NOT THE FIRST N. The signature block naming the human behind an
entity sits at the END of an instrument, and the SF quantity lives in an exhibit
AFTER the granting clause. Sampling the front of a document systematically
discards the two highest-value fields — the exact failure already paid for on
DOB, where reading past the rendered page moved coverage 48% -> 95%.

⚠ 2 PROCESSES x 4 THREADS IS THE MEASURED OPTIMUM, AND IT IS NEARLY FLAT.
1x8 = 2.62 s/pg · 2x4 = 2.00 · 4x2 = 2.69, identical character counts. The Ultra
7 266V is memory-bandwidth bound at 2.2 GHz, not core-starved — there is no
large parallel win hiding here, so do not add workers expecting one.
"""
import json
import os
import pathlib
import sys
import time
import types

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "4")

_O = None


def _init(threads):
    """One reader per worker process.

    ⚠ THE SHIM IS REQUIRED, NOT OPTIONAL. rapidocr_openvino does
    `from openvino.runtime import Core`; OpenVINO >= 2025 moved Core to the top
    level and deleted that submodule. Shim sys.modules rather than downgrading
    OpenVINO or editing site-packages — both of those decay silently.

    ⚠ AND device_name IS HARDCODED TO "CPU" IN THE PACKAGE, which is correct
    here: the Arc 140V iGPU measured 3x SLOWER and read HALF the characters
    (6.65 s/pg, 3,230 ch vs 2.02 s/pg, 7,438 ch). OCR is thousands of small
    variable-shape inferences — the worst case for an iGPU.
    """
    global _O
    import openvino
    shim = types.ModuleType("openvino.runtime")
    for n in dir(openvino):
        setattr(shim, n, getattr(openvino, n))
    sys.modules["openvino.runtime"] = shim

    import rapidocr_openvino.utils.infer_engine as IE
    from openvino import Core

    def patched(self, config):
        core = Core()
        self._verify_model(config["model_path"])
        m = core.read_model(config["model_path"])
        core.set_property("CPU", {"INFERENCE_NUM_THREADS": str(threads)})
        self.session = core.compile_model(
            model=m, device_name="CPU").create_infer_request()

    IE.OpenVINOInferSession.__init__ = patched
    from rapidocr_openvino import RapidOCR
    _O = RapidOCR()


def work(args):
    """⚠ ANGLE IS A REAL VARIABLE, NOT A TWEAK. Measured on the keyed bench
    (resolve/_score_upright.json vs _score_rotated.json), the two channels prefer
    OPPOSITE orientations on pre-digital pages:

        film   upright VLM 0.980 / OCR 0.475   rotated VLM 0.549 / OCR 0.945
        book   upright VLM 0.934 / OCR 0.513   rotated VLM 0.325 / OCR 0.880
        digital           1.000 / 1.000                  1.000 / 1.000

    Paddle nearly DOUBLES on film when rotated. For an OCR-only sweep that is
    not a tuning detail, it is roughly half the recall — so the sweep is run
    both ways and the text compared rather than assumed.
    """
    doc, path, angle = args
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    try:
        g = Image.open(path).convert("L")
        if angle:
            g = g.rotate(angle, expand=True)
        w, h = g.size
        s = 1600 / max(w, h)
        a = np.array(g.resize((int(w * s), int(h * s)),
                              Image.LANCZOS).convert("RGB"))
        r, _ = _O(a)
        return doc, pathlib.Path(path).stem, " ".join(
            x[1] for x in (r or [])), None
    except Exception as e:
        # ⚠ A FAILED PAGE IS COUNTED, NEVER SWALLOWED. A sweep that quietly
        # skips unreadable pages reports the same shape as one that read them.
        return doc, pathlib.Path(path).stem, "", str(e)[:120]


if __name__ == "__main__":
    from multiprocessing import Pool
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    ANGLE = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    src = pathlib.Path(__file__).parent / "devr_pages"
    out = pathlib.Path(__file__).parent / (f"devr_text_rot{ANGLE}" if ANGLE else "devr_text")
    out.mkdir(exist_ok=True)

    docs = sorted(d for d in src.iterdir() if d.is_dir())[:N]
    jobs = [(d.name, str(p), ANGLE) for d in docs for p in sorted(d.glob("*.tif"))]
    if not jobs:
        raise SystemExit("  NO PAGES — refusing to report a successful empty run")
    print(f"  {len(docs)} DEVR documents · {len(jobs)} pages · "
          f"PP-OCRv4/OpenVINO · angle {ANGLE} · 2 proc x 4 threads", flush=True)

    t0 = time.time()
    pages, errs = {}, 0
    with Pool(2, initializer=_init, initargs=(4,)) as pool:
        for i, (doc, pg, txt, err) in enumerate(
                pool.imap_unordered(work, jobs, chunksize=2), 1):
            pages.setdefault(doc, {})[pg] = txt
            if err:
                errs += 1
            if i % 25 == 0:
                el = time.time() - t0
                print(f"    {i}/{len(jobs)}  {el/i:.2f}s/pg  "
                      f"eta {(len(jobs)-i)*el/i/60:.0f}m  errs {errs}", flush=True)

    # Written in the same shape resolve/_evidence/*.json uses, so claim_read.py
    # and phrase_propose.py read it without a special case.
    for doc, pg in pages.items():
        (out / f"{doc}.json").write_text(json.dumps(
            {"doc_id": doc, "engine": "PP-OCRv4/openvino", "angle": ANGLE,
             "pages": [{"page": k, "accepted_text": v}
                       for k, v in sorted(pg.items())]},
            indent=1), encoding="utf-8")

    el = time.time() - t0
    ch = sum(len(v) for d in pages.values() for v in d.values())
    print(f"\n  DONE {len(jobs)} pages in {el/60:.1f}m "
          f"({el/len(jobs):.2f}s/pg) · {ch:,} chars · {errs} errors "
          f"-> devr_text/  ({len(pages)} documents)")
