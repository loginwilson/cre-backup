"""Score OCR against the REPAIRED labelled set, and cache every OCR text.

⚠ THE CACHE IS THE POINT AS MUCH AS THE SCORE. The first run threw its text
away and kept only a recall number. When the labelled set turned out to be
broken, the whole 30-minute pass had to be repeated to ask a corrected question
of the same pixels. OCR output is small, deterministic and expensive to
recompute — it is stored, and scoring becomes free forever after.

TWO NUMBERS, NEVER ONE
    LOCATE   phrase recall over 4-word shingles. Decides WHICH page a model
             opens. A garbled word is survivable.
    READ     do the DOLLAR FIGURES in the human-read span appear EXACTLY in
             the OCR text? Decides what may be claimed. Nothing is survivable.

⚠ EXPECT THESE TO DIVERGE, AND TREAT THE DIVERGENCE AS THE RESULT. The smoke
test read '($10.00)' as '(S10.o0)' on an otherwise perfect page. If LOCATE is
high and READ is low, OCR is a filter and never a transcriber, and the pipeline
that follows is grep-to-find then vision-at-100%-to-read.
"""
import collections
import json
import pathlib
import re
import sys
import time

import numpy as np
from PIL import Image

import groundtruth
import ocr_probe

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = pathlib.Path("ocr_text")
CACHE.mkdir(exist_ok=True)
PAGES = pathlib.Path("ocr_pages")

held = json.load(open("_held_docs.json"))
GT = groundtruth.load()


def era(doc):
    if doc.startswith("FT_"):
        return "film"
    y = held.get(doc, {}).get("rec", "")[:4]
    if not y.isdigit():
        return "film"          # undated in the index here means microfilm-era
    return "laser" if int(y) >= 2013 else "middle"


def page_file(doc, pg):
    for root in (PAGES, pathlib.Path("pages_out")):
        f = root / doc / f"p{pg:03d}.png"
        if f.exists():
            return f
    return None


def ocr_cached(doc, pg, f):
    c = CACHE / doc / f"p{pg:03d}.txt"
    if c.exists():
        return c.read_text(encoding="utf-8")
    t = ocr_probe.text_of(f)
    c.parent.mkdir(exist_ok=True)
    c.write_text(t, encoding="utf-8")
    return t


MONEY = re.compile(r"\$\s?([\d][\d,]*(?:\.\d\d)?)")

work = [(d, p) for (d, p) in GT if page_file(d, p)]
print(f"{len(work)} of {len(GT)} labelled pages are held on disk\n")

rows = []
for i, (doc, pg) in enumerate(sorted(work), 1):
    f = page_file(doc, pg)
    t0 = time.time()
    txt = ocr_cached(doc, pg, f)
    dt = time.time() - t0
    spans = GT[(doc, pg)]
    rec = [ocr_probe.phrase_recall(txt, s) for s in spans]

    # READ: every dollar figure the human transcribed, found exactly?
    want = {m.replace(",", "") for s in spans for m in MONEY.findall(s)}
    gotset = {m.replace(",", "") for m in MONEY.findall(txt)}
    hit = sum(1 for w in want if w in gotset)

    rows.append(dict(doc=doc, pg=pg, era=era(doc), locate=float(np.mean(rec)),
                     nspan=len(spans), nmoney=len(want), money_hit=hit,
                     chars=len(txt), secs=dt))
    flag = "" if not want else f"  MONEY {hit}/{len(want)}"
    print(f"  {era(doc):<7}{doc[:18]:<19}p{pg:<4}locate {np.mean(rec):.2f}"
          f"  ({len(spans)} span){flag}")

print("\n" + "=" * 68)
print(f"{'era':<9}{'pages':>6}{'LOCATE':>9}{'money found':>14}")
for e in ("laser", "middle", "film"):
    r = [x for x in rows if x["era"] == e]
    if not r:
        continue
    mw = sum(x["nmoney"] for x in r)
    mh = sum(x["money_hit"] for x in r)
    print(f"{e:<9}{len(r):>6}{np.mean([x['locate'] for x in r]):>9.2f}"
          f"{(f'{mh}/{mw}' if mw else '--'):>14}")
allm_w = sum(x["nmoney"] for x in rows)
allm_h = sum(x["money_hit"] for x in rows)
print(f"\n  ALL      {len(rows):>6}{np.mean([x['locate'] for x in rows]):>9.2f}"
      f"{f'{allm_h}/{allm_w}':>14}")
json.dump(rows, open("_ocr_score.json", "w"), indent=1)
