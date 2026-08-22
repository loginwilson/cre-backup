"""THE ENVELOPE FUNNEL. word -> phrase -> claim, and the reasoner sees ONLY crops.

⚠ THE POINT IS THE ISOLATION, NOT THE SPEED. An earlier run read a whole page
for the TITLE function and then re-reported it as ENVELOPE. That produced a
report that looked like a second witness and was not one — the same judgment
twice, unable to disagree with itself. This emits crops and nothing else, so
whatever reads them cannot lean on text it was never shown.

⚠ STAGE 1 IS DELIBERATELY SLOPPY. Words are free. A missing word is a claim
nobody ever looks at; a spurious word costs one phrase test. So the list is
generous on purpose and the discrimination happens at stage 2.

⚠ AND THE RECALL LIMIT IS REAL AND VISIBLE HERE. Stages 1-2 run on TESSERACT
text, which recovered both cover-page fields on only 40% of modern documents.
If Tesseract mangled a phrase, the funnel never fires and the claim is never
seen — silently. That is the argument for the model producing the text instead,
and this file exists partly to measure how badly it bites.

    python funnel_envelope.py <doc_id>
"""
import gzip
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

OCR = pathlib.Path("sample_ocr")
PAGES = pathlib.Path("sample_pages")
OUT = pathlib.Path("render/funnel")

# ── stage 1 · WORDS. Generous. Free. Never curate this down. ─────────────
WORDS = {
    "floor", "area", "zoning", "lot", "lots", "development", "rights", "right",
    "transfer", "transferred", "retained", "retain", "merge", "merged",
    "subdivision", "subdivided", "far", "bulk", "envelope", "wall", "easement",
    "air", "light", "height", "setback", "yard", "coverage", "story", "stories",
    "permit", "special", "ulurp", "declaration", "covenant", "restrict",
    "restriction", "restrictive", "landmark", "certify", "certification",
    "square", "feet", "contiguous", "ownership", "parties", "interest",
    "resolution", "premises", "buildable", "unused", "excess", "allocation",
    "allocated", "gross", "zfa", "occupancy",
}

# ── stage 2 · PHRASES. This is where discrimination happens. ─────────────
PHRASES = [
    ("floor area",                    r"floor\s+area"),
    ("development rights",            r"development\s+rights?"),
    ("zoning lot",                    r"zoning\s+lot"),
    ("party wall",                    r"party\s+wall"),
    ("sf of floor area",              r"(?:square\s+feet|sq\.?\s?ft\.?)\s+of\s+floor\s+area"),
    ("zoning resolution",             r"zoning\s+resolution"),
    ("special permit",                r"special\s+permit"),
    ("single ownership",              r"single\s+ownership"),
    ("parties in interest",           r"part(?:y|ies)\s+in\s+interest"),
    ("restrictive declaration",       r"restrictive\s+declaration"),
    ("air rights",                    r"air\s+rights?"),
    ("light and air",                 r"light\s+and\s+air"),
    ("lot area",                      r"lot\s+area"),
    ("merged zoning lot",             r"merged\s+zoning\s+lot"),
    ("ZR section",                    r"section\s+\d{2}-\d{2,3}"),
    ("landmark",                      r"landmark"),
    ("certificate of occupancy",      r"certificate\s+of\s+occupancy"),
    ("easement",                      r"easement"),
    ("height/setback",                r"height\s+and\s+setback"),
    ("unused/excess rights",          r"(?:unused|excess)\s+(?:development\s+)?rights?"),
]


def load(doc):
    p = OCR / f"{doc}.json.gz"
    if not p.exists():
        return None
    return json.load(gzip.open(p, "rt", encoding="utf-8"))


def main(doc):
    rows = load(doc)
    if not rows:
        print(f"  no OCR on disk for {doc}"); return
    d = OUT / doc
    d.mkdir(parents=True, exist_ok=True)

    n_words = n_word_hits = 0
    hits = []
    for r in rows:
        ws = r["words"]
        n_words += len(ws)
        # ⚠ STAGE 1 — count only. A word hit is not a result, it is permission
        # to run stage 2 on this page.
        n_word_hits += sum(1 for w in ws if w["t"].strip().lower().strip(".,;:()\"'") in WORDS)

        # rebuild the line with an index back to the word boxes
        toks, spans = [], []
        pos = 0
        for i, w in enumerate(ws):
            t = w["t"]
            toks.append(t)
            spans.append((pos, pos + len(t), i))
            pos += len(t) + 1
        text = " ".join(toks)

        for label, rx in PHRASES:
            for m in re.finditer(rx, text, re.I):
                idx = [i for s, e, i in spans if s < m.end() and e > m.start()]
                if not idx:
                    continue
                lo, hi = min(idx), max(idx)
                # ⚠ CONTEXT WINDOW, NOT THE MATCH. The claim follows the frame;
                # cropping the frame alone shows the reasoner the trigger and
                # hides the value.
                a, b = max(0, lo - 12), min(len(ws) - 1, hi + 40)
                box = ws[a:b + 1]
                x0 = min(w["x"] for w in box); x1 = max(w["x"] + w.get("w", 60) for w in box)
                y0 = min(w["y"] for w in box); y1 = max(w["y"] + w["h"] for w in box)
                hits.append({"page": r["page"], "phrase": label,
                             "text": text[max(0, m.start() - 60):m.end() + 160],
                             "box": (x0, y0, x1, y1)})

    print(f"  {doc} · {len(rows)} pages · {n_words:,} OCR words\n")
    print(f"  STAGE 1  word hits      {n_word_hits:>6,}   ({n_word_hits/max(n_words,1)*100:.1f}% of words)")
    print(f"  STAGE 2  phrase hits    {len(hits):>6,}\n")
    if not hits:
        print("  funnel found nothing — envelope reports NO CLAIM for this document.")
        return

    # merge overlapping boxes on the same page so one region isn't cropped twice
    bypage = {}
    for h in hits:
        bypage.setdefault(h["page"], []).append(h)
    saved = 0
    print(f"  {'#':>3}{'page':>6}  {'phrase':<24}crop")
    for pg in sorted(bypage):
        src = PAGES / doc / f"p{pg:03d}.tif"
        if not src.exists():
            continue
        im = Image.open(src).convert("L")
        W, H = im.size
        for h in sorted(bypage[pg], key=lambda x: x["box"][1]):
            x0, y0, x1, y1 = h["box"]
            x0 = max(0, x0 - 40); y0 = max(0, y0 - 30)
            x1 = min(W, x1 + 40); y1 = min(H, y1 + 30)
            if (x1 - x0) < 80 or (y1 - y0) < 30:
                continue
            c = im.crop((x0, y0, x1, y1))
            sc = min(2.5, max(1.0, 1900 / max(c.width, 1)))
            c = c.resize((int(c.width * sc), int(c.height * sc)), Image.LANCZOS)
            saved += 1
            f = d / f"h{saved:02d}_p{pg:03d}_{re.sub(r'[^a-z]', '', h['phrase'].lower())[:14]}.png"
            c.save(f)
            print(f"  {saved:>3}{pg:>6}  {h['phrase']:<24}{f.name}")
    print(f"\n  {saved} crops -> {d}")
    print(f"  ⚠ the reasoner sees these crops and nothing else.")


if __name__ == "__main__":
    main(sys.argv[1])
