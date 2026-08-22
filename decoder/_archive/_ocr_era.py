"""DOES OCR SURVIVE THE OLD SCANS? Stratified by era, on pages already held.

⚠ WHY THIS IS THE DECIDING TEST AND NOT A DETAIL. FT_ microfilm is 35.8% of
ACRIS. If OCR works on 2013 laser print and collapses on 1971 film, then
"grep first, look second" is not a corpus strategy — it is a strategy for the
newest two-thirds, and the oldest third still costs full vision on every page.
That would change the plan, so it gets measured before the plan is written.

⚠ AND THE 194-TOKEN FIGURE HAS THE SAME PROBLEM. It was measured once, on a
clean 2013 laser print, and has been carried through every estimate since as if
it were a corpus constant. This run also reports how much INK each era's pages
carry, which is the closest free proxy for whether 20% downscaling can possibly
be legible on film.

THREE STRATA
    laser    2013-2025   clean digital-to-paper-to-scan
    middle   1998-2012   photocopy generation loss
    film     FT_*        1960s-70s microfilm, black frames, skew, bleed

⚠ NO GROUND TRUTH EXISTS FOR MOST PAGES, so two different things are reported
and must not be confused: YIELD (how much text came back, and how confidently)
is available everywhere; RECALL against a phrase a human actually read is
available only where claims.py holds a verbatim quote for that exact page.
Yield without recall can be high on garbage — an engine hallucinating words
from film grain scores well on yield and zero on recall.
"""
import collections
import io
import json
import pathlib
import random
import re
import sys
import time

import numpy as np
from PIL import Image

import ocr_probe

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PER_STRATUM = int(sys.argv[1]) if len(sys.argv) > 1 else 10
rng = random.Random(20260809)

# ---- ground truth: verbatim quotes taken off the page by eye ---------------
src = pathlib.Path("claims.py").read_text(encoding="utf-8")
GT = collections.defaultdict(list)
for blk in re.finditer(r'C\(\s*"[^"]+"\s*,\s*"([^"]+)"\s*,\s*"(p\d+)"(.*?)(?=\n C\(|\Z)',
                       src, re.S):
    doc, pg, body = blk.group(1), blk.group(2), blk.group(3)
    for q in re.findall(r"'([^']{25,})'", body):
        GT[(doc, int(pg[1:]))].append(q)

# ---- render every held page, including microfilm ---------------------------
OUT = pathlib.Path("ocr_pages")
OUT.mkdir(exist_ok=True)
man = [json.loads(l) for l in
       pathlib.Path("corpus/manifest.jsonl").read_text(encoding="utf-8").splitlines()
       if l.strip()]
for r in man:
    if not r["page"].isdigit():
        continue
    d = OUT / r["doc_id"]
    f = d / f"p{int(r['page']):03d}.png"
    if f.exists():
        continue
    blob = pathlib.Path("corpus/blobs") / r["sha256"][:2] / r["sha256"][2:4] / r["sha256"]
    if blob.exists():
        d.mkdir(exist_ok=True)
        try:
            Image.open(io.BytesIO(blob.read_bytes())).convert("L").save(f)
        except Exception:
            pass

held = json.load(open("_held_docs.json"))


def era(doc):
    if doc.startswith("FT_"):
        return "film"
    y = held.get(doc, {}).get("rec", "")[:4]
    if not y.isdigit():
        return None
    return "laser" if int(y) >= 2013 else "middle"


import coverpage

pool = collections.defaultdict(list)
for d in sorted(OUT.iterdir()):
    if not d.is_dir():
        continue
    e = era(d.name)
    if e is None:
        continue
    for f in sorted(d.glob("p*.png")):
        pg = int(f.stem[1:])
        if pg == 1:
            continue                       # the City cover; not the document
        try:
            if coverpage.is_cover(f)[0]:
                continue
        except Exception:
            continue
        pool[e].append((d.name, pg, f))

print("pages available per era:", {k: len(v) for k, v in pool.items()})

# prefer pages that HAVE ground truth, then fill randomly
sample = []
for e, items in pool.items():
    withgt = [i for i in items if GT.get((i[0], i[1]))]
    rest = [i for i in items if not GT.get((i[0], i[1]))]
    rng.shuffle(rest)
    take = (withgt + rest)[:PER_STRATUM]
    sample += [(e, *t) for t in take]
    print(f"  {e:<7} sampled {len(take)}  ({len(withgt)} with a human-read quote)")

# ---- run --------------------------------------------------------------------
eng = ocr_probe.engine()
rows = []
for e, doc, pg, f in sample:
    t0 = time.time()
    try:
        res, _ = eng(str(f))
    except Exception as ex:
        print(f"  ⚠ {doc} p{pg}: {type(ex).__name__}")
        continue
    dt = time.time() - t0
    txt = " ".join(r[1] for r in res) if res else ""
    conf = float(np.mean([r[2] for r in res])) if res else 0.0
    a = np.asarray(Image.open(f).convert("L"))
    ink = float((a <= 128).mean())
    gts = GT.get((doc, pg), [])
    rec = ([ocr_probe.phrase_recall(txt, q) for q in gts] if gts else [])
    rows.append(dict(era=e, doc=doc, pg=pg, secs=dt, chars=len(txt), boxes=len(res or []),
                     conf=conf, ink=ink, ngt=len(gts),
                     recall=float(np.mean(rec)) if rec else None))
    print(f"  {e:<7} {doc[:18]:<18} p{pg:<3} {dt:5.1f}s {len(txt):>6}ch "
          f"conf {conf:.2f} ink {ink:.3f}"
          + (f"  RECALL {np.mean(rec):.2f} on {len(gts)} quote(s)" if rec else ""))

print("\n" + "=" * 72)
print(f"{'era':<8}{'n':>4}{'chars/pg':>10}{'conf':>7}{'ink':>8}{'secs':>7}"
      f"{'recall':>9}{'n_gt':>6}")
for e in ("laser", "middle", "film"):
    r = [x for x in rows if x["era"] == e]
    if not r:
        continue
    recs = [x["recall"] for x in r if x["recall"] is not None]
    print(f"{e:<8}{len(r):>4}{np.mean([x['chars'] for x in r]):>10,.0f}"
          f"{np.mean([x['conf'] for x in r]):>7.2f}"
          f"{np.mean([x['ink'] for x in r]):>8.3f}"
          f"{np.mean([x['secs'] for x in r]):>7.1f}"
          + (f"{np.mean(recs):>9.2f}{len(recs):>6}" if recs else f"{'--':>9}{0:>6}"))

json.dump(rows, open("_ocr_era.json", "w"), indent=1)
print("\n⚠ read YIELD and RECALL as different facts — see the module docstring.")
