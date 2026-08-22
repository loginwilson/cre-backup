"""PER-PAGE vs PER-DOCUMENT transcription. The metric has been understating it.

⚠ SCORING PER PAGE PENALISES THE EXTRACTOR FOR SOMETHING THE RESOLVER FIXES FOR
FREE. Tesseract read `REEL 586` correctly on pages 8, 9 and 10 of the film
mortgage and missed it on 1-7. But a document sits on ONE reel. Three good reads
resolve all ten pages, so seven of those "failures" are not failures of the
pipeline - only of a page-local view of it.

⚠ AND THE DISTINCTION IS NOT COSMETIC, IT IS PER-ARTIFACT. Facts that are
DOCUMENT-INVARIANT (reel/book number, parties, amount, block, lot) legitimately
resolve across pages. Facts that are PAGE-SPECIFIC (the page number inside the
stamp, 'PAGE 2 OF 5') do NOT - crediting page 1 with page 8's page number would
be scoring a fact that is genuinely absent. So the two are separated and the
page-specific ones keep the strict page-local rule.

This reports the honest ceiling of cross-page resolution, nothing more. It does
not invent a value; it only allows a fact read correctly SOMEWHERE in the
document to count for the document.
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

import score as S

# artifact ids that are genuinely page-specific and must stay page-local
PAGE_LOCAL = {"reel_page", "rec_page", "page_of", "page_count"}

DOCS = [
    ("BK_6730047100023", "answer_key_bookdoc.json", "book 1967", 0.040),
    ("FT_1680008647768", "answer_key_testdoc.json", "film 1981", 0.255),
    ("2015022400608001", "answer_key_moderndoc.json", "digital 2015", 0.705),
]
ENGINES = ["tesseract", "rapidpool"]

rows = []
print(f"  {'document':<14}{'PER-PAGE':>20}{'PER-DOCUMENT':>22}{'recovered':>11}")
print(f"  {'':<14}{'transcribed':>20}{'transcribed':>22}{'':>11}")
print("  " + "-" * 70)

for doc, keyf, label, share in DOCS:
    R = pathlib.Path("render/testdoc") / doc
    KEY = json.loads(pathlib.Path(keyf).read_text(encoding="utf-8"))
    PAGES = [k for k in KEY if not k.startswith("_")]
    S.META.update({p: {"doc_id": doc} for p in PAGES})

    def txt(p):
        out = ""
        for e in ENGINES:
            f = R / e / (p + ".txt")
            if f.exists():
                out += " " + f.read_text(encoding="utf-8", errors="replace")
        return out

    per_page = {p: S.norm(txt(p)) for p in PAGES}
    whole = S.norm(" ".join(txt(p) for p in PAGES))

    pv = ph = dh = 0
    gained = []
    for p in PAGES:
        for a in KEY[p]["artifacts"]:
            if a["tier"] != "CRITICAL":
                continue
            pv += 1
            page_ok = S.found(per_page[p], a)
            ph += page_ok
            # page-specific artifacts never get document-level credit
            doc_ok = page_ok if a["id"] in PAGE_LOCAL else S.found(whole, a)
            dh += doc_ok
            if doc_ok and not page_ok:
                gained.append((p, a["id"], a["value"]))
    print(f"  {label:<14}{f'{ph}/{pv}':>13}{ph/pv*100:>6.0f}%"
          f"{f'{dh}/{pv}':>15}{dh/pv*100:>6.0f}%{dh-ph:>10}")
    rows.append((label, share, ph / pv, dh / pv, gained))

print()
bp = sum(s * p for _, s, p, _, _ in rows)
bd = sum(s * d for _, s, _, d, _ in rows)
print(f"  BLENDED by corpus page share:  per-page {bp*100:.1f}%"
      f"   ->   per-document {bd*100:.1f}%   (+{(bd-bp)*100:.1f})")

for label, _, _, _, gained in rows:
    if gained:
        print(f"\n  ── {label}: recovered by cross-page resolution ({len(gained)}) ──")
        for p, i, v in gained[:12]:
            print(f"    {p:<11}{i:<14}{str(v)[:34]}")
