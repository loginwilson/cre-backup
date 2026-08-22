"""OCR POINTS AT SECTIONS · CROP THE SECTION · MODEL READS PIXELS · CLAIM.

⚠ CROP BY STRUCTURE, NOT BY PROXIMITY. The obvious design is to crop a box
around whatever word triggered — 200px around "Upzoning" — and it silently
loses clauses. Section 3.1 of the document that seeded this project runs A
through G, and only G mentions upzoning; a proximity crop never shows A-F, and
nothing reports that they existed. Cropping from one section heading to the
next means nothing inside a visited section can hide.

⚠ AND THE HEADINGS ARE WHAT OCR IS BEST AT. They are short, isolated, in a
predictable format, and surrounded by whitespace. Measured across 20 DEVRs:
every numbered section was located, including on pages whose body text OCR'd
into nonsense. Locating survives what reading does not.

⚠ THE REFERENCE IS AUTHORITATIVE ABOUT *WHERE*, NEVER ABOUT *WHAT*. Today's
answer key: "20.53" for 20.33 feet, "WW ALIB, INC." for ALIB, INC., and
"820,000.00" for $20,000.00 — every one correctly LOCATED and every one wrong.
The last would have recorded a $20,000 mortgage as $820,000. So this file emits
COORDINATES and never values; the value comes from the pixels.
"""
import gzip
import json
import os
import pathlib
import re
import sys

from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OCR = pathlib.Path("sample_ocr")
PAGES = pathlib.Path("sample_pages")
OUT = pathlib.Path(os.environ["TMP"]) / "seccrop"

HEAD = re.compile(r"^(Section|ARTICLE|Article|EXHIBIT|Exhibit|Schedule|SCHEDULE)$")
NUMB = re.compile(r"^[\d]+(\.[\d]+)?[.:)]?$|^[IVXL]+[.:)]?$|^[\"'“]?[A-E](-\d)?[\"'”]?[.:)]?$")


def headings(words):
    """A heading word followed by its number/letter. Deliberately dumb — it has
    to survive OCR that mangles everything around it."""
    out = []
    for i, w in enumerate(words[:-1]):
        if HEAD.match(w["t"].strip()) and NUMB.match(words[i + 1]["t"].strip()):
            out.append({"label": f"{w['t'].strip()} {words[i+1]['t'].strip()}",
                        "x": w["x"], "y": w["y"], "h": w["h"]})
    return out


def main(doc):
    rows = json.load(gzip.open(OCR / f"{doc}.json.gz", "rt", encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    print(f"{doc} · {len(rows)} pages\n")
    print(f"  {'page':>5}{'conf':>7}  sections located")
    for r in rows:
        hs = headings(r["words"])
        if not hs:
            print(f"  {r['page']:>5}{r['conf']:>7.1f}  —")
            continue
        print(f"  {r['page']:>5}{r['conf']:>7.1f}  " +
              ", ".join(h["label"] for h in hs[:6]))
        src = PAGES / doc / f"p{r['page']:03d}.tif"
        if not src.exists():
            continue
        im = Image.open(src)
        W, H = im.size
        # ⚠ boundary = this heading to the NEXT one, or the foot of the page.
        # origin from the OCR record is already applied to the boxes, so these
        # are original-TIFF coordinates and a stored proof stays valid.
        ys = [h["y"] for h in hs] + [H]
        for i, h in enumerate(hs):
            y0 = max(0, h["y"] - 40)
            y1 = min(H, ys[i + 1] - 10 if ys[i + 1] > h["y"] + 60 else H)
            if y1 - y0 < 60:
                continue
            c = im.crop((0, y0, W, y1))
            sc = min(1.6, 1700 / max(1, c.width))
            c = c.resize((int(c.width * sc), int(c.height * sc)), Image.LANCZOS)
            safe = re.sub(r"[^A-Za-z0-9]", "", h["label"])
            f = OUT / f"{doc}_p{r['page']:03d}_{safe}.png"
            c.save(f)
            total += 1
    print(f"\n  {total} section crops -> {OUT}")
    print(f"  ⚠ coordinates only. No value in this file is a claim.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2025032500727001")
