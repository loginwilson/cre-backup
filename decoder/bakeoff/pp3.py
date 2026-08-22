"""PP-OCRv6 on ONE page from each era. Smoke test, not a score.

⚠ THREE PAGES IS NOT A MEASUREMENT AND MUST NOT BE REPORTED AS ONE. It answers
a narrower question: does PP-OCRv6 run at all on this box, and does what it
returns look like a film/book/digital page or like noise. The comparable number
against Tesseract (86.0%), RapidOCR (91.5%) and Qwen3-VL-4B (96.4%) needs all
26 keyed pages through the same scorer.

⚠ SPEED HERE IS MEANINGLESS. CPU-only wheel, oneDNN disabled because it throws
`ConvertPirAttribute2RuntimeAttribute` on this Intel box. The paper's 0.13 s/page
is an A100 number and nothing here bears on it.
"""
import pathlib
import sys
import time
import warnings

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

from paddleocr import PaddleOCR

HERE = pathlib.Path(__file__).parent
PICK = [("film", "FT_1680008647768", "p010.png"),
        ("book", "BK_6730047100023", "p001.png"),
        ("digital", "2015022400608001", "p001.png")]

ocr = PaddleOCR(ocr_version="PP-OCRv6", device="cpu", enable_mkldnn=False,
                use_doc_orientation_classify=False, use_doc_unwarping=False,
                use_textline_orientation=False)

for era, doc, page in PICK:
    p = HERE / "pages" / doc / page
    if not p.exists():
        print(f"  {era}: missing {p}")
        continue
    t = time.time()
    try:
        res = ocr.predict(str(p))
    except Exception as e:
        print(f"  {era:<8}{doc} {page}  FAILED {type(e).__name__}: {str(e)[:80]}")
        continue
    lines = []
    for r in res or []:
        j = r if isinstance(r, dict) else getattr(r, "json", {}) or {}
        j = j.get("res", j)
        lines += list(j.get("rec_texts") or [])
    txt = " ".join(lines)
    out = HERE / "out" / "ppv6" / doc
    out.mkdir(parents=True, exist_ok=True)
    (out / (p.stem + ".png.txt")).write_text(txt, encoding="utf-8")
    print(f"\n  === {era.upper()}  {doc} {page}  "
          f"{len(lines)} lines, {len(txt.split())} words, {time.time()-t:.1f}s ===")
    print("  " + txt[:600].replace("\n", " "))
