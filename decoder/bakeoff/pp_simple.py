"""PP-OCRv6 on the 26 keyed pages. Simplest possible config.

    python pp_simple.py

⚠ ACCURACY ONLY - THIS MACHINE CANNOT MEASURE PP-OCRv6's SPEED AND SHOULD NOT
TRY. PaddlePaddle here is the CPU-only wheel (`is_compiled_with_cuda: False`,
`get_all_device_type: []`) on an Intel Arc iGPU, and oneDNN - Paddle's CPU
accelerator - throws `ConvertPirAttribute2RuntimeAttribute` on this box, which
has now killed five separate attempts. So it runs on the plain CPU path, which
is slow and says nothing about the 0.13 s/page the paper reports on an A100.
The number worth having from this run is whether v6's benchmark lead survives
1967 microfilm, a faint dot-matrix stamp and a sideways backer - conditions no
OCR benchmark measures.

⚠ AND A CRASH MUST LEAVE NO FILE. An empty .txt is indistinguishable from an
engine that read the page and found nothing; those are opposite findings, and
scoring the first as the second is the failure this project has hit repeatedly.
"""
import json
import pathlib
import sys
import time
import warnings

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

from paddleocr import PaddleOCR

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out" / "ppv6"
pages = [(d.name, p) for d in sorted(x for x in (HERE / "pages").iterdir() if x.is_dir())
         for p in sorted(d.glob("p*.png"))]

print(f"  PP-OCRv6 (medium is the default for this version), CPU, oneDNN off")
print(f"  {len(pages)} pages\n")

ocr = PaddleOCR(ocr_version="PP-OCRv6", device="cpu", enable_mkldnn=False,
                use_doc_orientation_classify=False, use_doc_unwarping=False,
                use_textline_orientation=False)

ok, errs, t0 = 0, [], time.time()
for docn, pg in pages:
    d = OUT / docn
    d.mkdir(parents=True, exist_ok=True)
    f = d / (pg.stem + ".png.txt")
    if f.exists():
        ok += 1
        continue
    try:
        res = ocr.predict(str(pg))
        lines = []
        for r in res or []:
            j = r if isinstance(r, dict) else getattr(r, "json", {}) or {}
            j = j.get("res", j)
            lines += list(j.get("rec_texts") or [])
        f.write_text(" ".join(lines), encoding="utf-8")
        ok += 1
        print(f"    {docn}/{pg.name}  {len(lines)} lines")
    except Exception as e:
        errs.append((docn, pg.name, f"{type(e).__name__}: {str(e)[:90]}"))
        print(f"    {docn}/{pg.name}  FAILED {type(e).__name__}")

el = time.time() - t0
(OUT / "run.json").write_text(json.dumps(
    {"engine": "ppv6", "model": "PP-OCRv6_medium", "device": "cpu",
     "mkldnn": False, "rot": False, "pages": ok, "errors": errs,
     "sec": round(el, 1), "sec_per_page": round(el / max(ok, 1), 2),
     "note": "CPU-only wheel, oneDNN disabled - speed here is NOT indicative"},
    indent=1), encoding="utf-8")

print(f"\n  {ok}/{len(pages)} pages · {el:.0f}s · {len(errs)} error(s)")
if errs and not ok:
    print("  ⚠ ZERO PAGES — the oneDNN crash again, not a score of zero.")
