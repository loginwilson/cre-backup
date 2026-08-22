"""TRANSCRIBED vs POINTED - the gap that decides whether coordinates are optional.

⚠ THESE TWO NUMBERS ANSWER DIFFERENT QUESTIONS AND THE ARCHITECTURE PICKS ONE.
POINTED asks "did the engine put something recognisable at this fact", which is
sufficient ONLY if a downstream model re-reads a crop at that location. Drop the
crops and the OCR text IS the deliverable, so TRANSCRIBED - the characters are
actually right - becomes the binding metric.

A reel stamp read as `xe. 5860` is a POINTED hit and a TRANSCRIBED miss. With
coordinates that is fine; a model crops it and reads 586. Without coordinates it
is a wrong reel number, which is a wrong lineage join, forever.
"""
import json
import pathlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from PIL import Image

import score as S

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

DOCS = [
    ("BK_6730047100023", "answer_key_bookdoc.json", "book 1967", 0.040),
    ("FT_1680008647768", "answer_key_testdoc.json", "film 1981", 0.255),
    ("2015022400608001", "answer_key_moderndoc.json", "digital 2015", 0.705),
]


def extra_passes(R, PAGES):
    T = R / "_gap"
    T.mkdir(exist_ok=True)
    jobs = []
    for p in PAGES:
        jobs.append((p, R / p, 11))
        im = Image.open(R / p)
        for ang in (90, 270):
            f = T / f"{p[:-4]}_r{ang}.png"
            if not f.exists():
                im.rotate(ang, expand=True).save(f)
            jobs.append((p, f, 4))
            jobs.append((p, f, 11))

    def ocr(j):
        r = subprocess.run([TESS, str(j[1]), "stdout", "--psm", str(j[2])],
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        return " ".join(r.stdout.split())

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        outs = list(ex.map(ocr, jobs))
    out = {p: "" for p in PAGES}
    for (p, _, _), tx in zip(jobs, outs):
        out[p] += " " + tx
    return out, time.time() - t0


rows = []
print(f"  {'document':<14}{'config':<26}{'TRANSCRIBED':>14}{'POINTED':>12}{'gap':>7}")
print("  " + "-" * 74)
for doc, keyf, label, share in DOCS:
    R = pathlib.Path("render/testdoc") / doc
    KEY = json.loads(pathlib.Path(keyf).read_text(encoding="utf-8"))
    PAGES = [k for k in KEY if not k.startswith("_")]
    S.META.update({p: {"doc_id": doc} for p in PAGES})
    extra, _ = extra_passes(R, PAGES)

    def txt(e, p):
        f = R / e / (p + ".txt")
        return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""

    combos = [("tesseract",), ("tesseract", "EXTRA"),
              ("tesseract", "rapidpool"), ("tesseract", "rapidpool", "EXTRA")]
    for c in combos:
        ct = cv = cp = 0
        for p in PAGES:
            hay = S.norm(" ".join(extra[p] if e == "EXTRA" else txt(e, p) for e in c))
            for a in KEY[p]["artifacts"]:
                if a["tier"] != "CRITICAL":
                    continue
                cv += 1
                ok = S.found(hay, a)
                ct += ok
                cp += ok or S.pointed(hay, a)
        name = "+".join("T-multi" if e == "EXTRA" else e for e in c)
        print(f"  {label:<14}{name:<26}{f'{ct}/{cv}':>8}{ct/cv*100:>5.0f}%"
              f"{f'{cp}/{cv}':>7}{cp/cv*100:>5.0f}%{(cp-ct)/cv*100:>6.0f}")
        if c == combos[-1]:
            rows.append((label, share, ct / cv, cp / cv))
    print()

print("  ══ BLENDED BY CORPUS PAGE SHARE (full cascade) ══\n")
bt = sum(s * t for _, s, t, _ in rows)
bp = sum(s * p for _, s, _, p in rows)
for label, share, t, p in rows:
    print(f"    {label:<14}{share*100:>5.1f}% of pages   transcribed {t*100:>5.1f}%"
          f"   pointed {p*100:>5.1f}%   gap {(p-t)*100:>4.1f}")
print(f"\n    {'BLENDED':<14}{'100.0':>5}% of pages   transcribed {bt*100:>5.1f}%"
      f"   pointed {bp*100:>5.1f}%   gap {(bp-bt)*100:>4.1f}")
print(f"\n  -> dropping coordinates costs {(bp-bt)*100:.1f} points blended,")
print(f"     but the loss is concentrated on film and book, which is exactly")
print(f"     where the reel numbers and parcel keys live.")
