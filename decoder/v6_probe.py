"""IS PP-OCRv6 WORTH ITS COST? A small, honest probe on identical pages.

    python v6_probe.py            # 12 pages, v6 upright + rotated
                                  # compared against v4 text already captured

⚠ SMALL ON PURPOSE, AND SAID OUT LOUD. v6_medium measured 65.14 s/page against
v4/OpenVINO at 2.02 s/page — 32x. The full 495-page sweep in both orientations
would be ~18 hours on this laptop. So this reads 12 pages, which is enough to
see a large difference and NOT enough to certify one. A win here is a reason to
run v6 on Torch, never a reason to lock it as the corpus engine.

⚠ THE SAME PAGES, OR THE COMPARISON IS MEANINGLESS. v4 text is read back from
devr_text/ and devr_text_rot90/ rather than re-run, so both engines are scored on
identical pixels. Comparing engines across different page sets is how this
project has been misled before.

⚠ CHARS ARE NOT THE VERDICT. An engine can emit fluent invention and win any
length-based metric — the bakeoff scorer exists precisely because word and
character counts mislead. This prints characters AND trigger hits, and where they
disagree the trigger column is the one that matters, because the sweep exists to
learn which operative language a document type contains.

⚠ NO ANSWER KEY HERE. devr_pages has no ground truth, so this measures
DIFFERENCE, not accuracy. Only the keyed bench (bakeoff/keys/) can say which
engine is right when they disagree.
"""
import json
import os
import pathlib
import re
import sys
import time

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ.setdefault("OMP_NUM_THREADS", "8")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent

TRIGGERS = {
    "ownership": [r"do(?:es)?\s+hereby\s+grant", r"grant,?\s+bargain",
                  r"sell\s+and\s+convey", r"quitclaim"],
    "financing": [r"to\s+secure\s+the\s+payment", r"principal\s+sum\s+of",
                  r"releases?\s+and\s+discharges?"],
    "envelope": [r"development\s+rights", r"floor\s+area\s+ratio",
                 r"unused\s+development", r"zoning\s+lot"],
    "encumbrance": [r"subject\s+to", r"excepting\s+and\s+reserving",
                    r"together\s+with\s+all", r"easement"],
    "boundary": [r"\bthence\b", r"feet\s+to\s+a\s+point"],
    "cover_page": [r"document\s+type:?", r"mortgage\s+amount:?", r"\bCRFN\b"],
}
TRIG = {f: [re.compile(p, re.I) for p in ps] for f, ps in TRIGGERS.items()}


def hits(t):
    return {f: sum(len(p.findall(t)) for p in pats) for f, pats in TRIG.items()}


def v4_text(dirname):
    out = {}
    d = HERE / dirname
    if not d.exists():
        return out
    for f in d.glob("*.json"):
        rec = json.loads(f.read_text(encoding="utf-8"))
        for pg in rec.get("pages") or []:
            out[(rec["doc_id"], pg["page"])] = pg.get("accepted_text") or ""
    return out


def main():
    up4, rot4 = v4_text("devr_text"), v4_text("devr_text_rot90")
    if not up4:
        print("  no v4 text yet — run devr_sweep.py first")
        return 1

    docs = sorted({d for d, _ in up4})[:3]
    picks = []
    for d in docs:
        pgs = sorted(p for dd, p in up4 if dd == d)
        # front, middle, back — the back matters: signature blocks live there
        for i in (0, len(pgs)//2, len(pgs)-2, len(pgs)-1):
            if 0 <= i < len(pgs) and (d, pgs[i]) not in picks:
                picks.append((d, pgs[i]))
    picks = picks[:12]
    print(f"  {len(picks)} pages from {len(docs)} DEVR documents\n", flush=True)

    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    from paddleocr import PaddleOCR

    t = time.time()
    ocr = PaddleOCR(text_detection_model_name="PP-OCRv6_medium_det",
                    text_recognition_model_name="PP-OCRv6_medium_rec",
                    use_doc_orientation_classify=False, use_doc_unwarping=False,
                    use_textline_orientation=False,
                    enable_mkldnn=False, cpu_threads=8, device="cpu")
    print(f"  v6 init {time.time()-t:.1f}s\n", flush=True)

    tot = {"v4up": 0, "v4rot": 0, "v6up": 0, "v6rot": 0}
    ht = {k: {f: 0 for f in TRIG} for k in tot}
    t0 = time.time()
    for n, (doc, pg) in enumerate(picks, 1):
        src = HERE / "devr_pages" / doc / f"{pg}.tif"
        g0 = Image.open(src).convert("L")
        for label, angle in (("v6up", 0), ("v6rot", 90)):
            g = g0.rotate(angle, expand=True) if angle else g0
            w, h = g.size
            s = 1600 / max(w, h)
            a = np.array(g.resize((int(w*s), int(h*s)), Image.LANCZOS).convert("RGB"))
            txt = " ".join(x for r in (ocr.predict(a) or [])
                           for x in (r.get("rec_texts") or []))
            tot[label] += len(txt)
            for f, c in hits(txt).items():
                ht[label][f] += c
        a4 = up4.get((doc, pg), ""); r4 = rot4.get((doc, pg), "")
        tot["v4up"] += len(a4); tot["v4rot"] += len(r4)
        for f, c in hits(a4).items(): ht["v4up"][f] += c
        for f, c in hits(r4).items(): ht["v4rot"][f] += c
        el = time.time() - t0
        print(f"    {n}/{len(picks)} {doc}:{pg}  "
              f"v4 {len(a4):>5} | v6 {tot['v6up']:>6} cum   "
              f"{el/n:.0f}s/pg", flush=True)

    print(f"\n  CHARACTERS")
    for k in ("v4up", "v6up", "v4rot", "v6rot"):
        print(f"    {k:<8} {tot[k]:>8,}")
    if tot["v4up"]:
        print(f"    v6 vs v4 upright  {(tot['v6up']-tot['v4up'])/tot['v4up']*100:+.1f}%")
    if tot["v4rot"]:
        print(f"    v6 vs v4 rotated  {(tot['v6rot']-tot['v4rot'])/max(tot['v4rot'],1)*100:+.1f}%")

    print(f"\n  TRIGGER HITS")
    print(f"    {'function':<14}{'v4up':>7}{'v6up':>7}{'v4rot':>7}{'v6rot':>7}")
    for f in TRIG:
        print(f"    {f:<14}{ht['v4up'][f]:>7}{ht['v6up'][f]:>7}"
              f"{ht['v4rot'][f]:>7}{ht['v6rot'][f]:>7}")

    el = time.time() - t0
    print(f"\n  v6 read {len(picks)*2} pages in {el/60:.1f}m "
          f"({el/(len(picks)*2):.1f}s/pg) vs v4 at 1.59s/pg")
    print("  ⚠ 12 pages, no answer key — this measures DIFFERENCE, not accuracy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
