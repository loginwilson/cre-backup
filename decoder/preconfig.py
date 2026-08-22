"""PRE-CONFIGURATION SWEEP: what should a page look like BEFORE OCR sees it.

    python preconfig.py [doc_id]

Answers one question with measurements instead of intuition: for a microfilm
page, what render width / contrast treatment maximises what the OCR surfaces.

⚠ THIS IS THE VARIABLE I SHOULD HAVE TESTED FIRST AND DID NOT. Two attempts
went into cropping - a fixed top band, then a page-rectangle detector - and both
made Tesseract WORSE (2/10 and 1/10 against a 3/10 baseline), the second by
cutting text out of the frame entirely. Meanwhile every one of those runs was
fed a page DOWNSCALED from 2536px to 1800px. The reel stamp is small dot-matrix
type; throwing away 30% of its pixels before OCR is a far bigger effect than any
border, and it was never once varied.

⚠ AND EVERY CONFIG IS SCORED THE SAME WAY, against the hand-read key, on the
whole document - not on the stamp alone. A treatment that rescues the stamp
while degrading the body text is not an improvement, and measuring only the
thing you are trying to fix cannot tell you that.
"""
import json
import pathlib
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image, ImageOps

import score as S

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
CORES = 8
DOC = sys.argv[1] if len(sys.argv) > 1 else "FT_1680008647768"
ROOT = pathlib.Path("render/testdoc") / DOC
RAW = ROOT / "raw"
KEY = json.loads(pathlib.Path("answer_key_testdoc.json").read_text(encoding="utf-8"))
PAGES = [k for k in KEY if not k.startswith("_")]

# (label, target width or None for native, contrast treatment)
CONFIGS = [
    ("1400",            1400, None),
    ("1800",            1800, None),
    ("native-2536",     None, None),
    ("3200",            3200, None),
    ("native+contrast", None, "autocontrast"),
    ("3200+contrast",   3200, "autocontrast"),
]


def render(p, width, treat):
    im = Image.open(p)
    if im.mode == "1":
        im = im.convert("L")
    if width and width != im.width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    if treat == "autocontrast":
        im = ImageOps.autocontrast(im.convert("L"), cutoff=1)
    return im


def ocr_file(f):
    r = subprocess.run([TESS, str(f), "stdout", "--psm", "4"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return " ".join(r.stdout.split())


def main():
    truth_reel, truth_pg = "586", {i: str(760 + i) for i in range(1, 11)}
    print(f"  {DOC} · {len(PAGES)} pages · raw {Image.open(RAW/'p001.tif').size}\n")
    print(f"  {'config':<18}{'px':>6}{'sec':>7}{'reel':>7}{'pgno':>7}"
          f"{'CRIT pt':>10}{'ALL tr':>9}{'ALL pt':>9}")
    print("  " + "-" * 76)

    rows = []
    for label, width, treat in CONFIGS:
        d = ROOT / f"_cfg_{label}"
        d.mkdir(exist_ok=True)
        files = []
        for i in range(1, 11):
            im = render(RAW / f"p{i:03d}.tif", width, treat)
            f = d / f"p{i:03d}.png"
            im.save(f)
            files.append(f)
        px = Image.open(files[0]).width

        t0 = time.time()
        with ThreadPoolExecutor(max_workers=CORES) as ex:
            texts = list(ex.map(ocr_file, files))
        el = time.time() - t0

        reel = pgno = 0
        ct = cv = at = av = 0
        for i, txt in enumerate(texts, 1):
            (d / f"p{i:03d}.png.txt").write_text(txt, encoding="utf-8")
            nums = re.findall(r"\d+", txt)
            reel += truth_reel in nums
            pgno += truth_pg[i] in nums
            hay = S.norm(txt)
            for a in KEY[f"p{i:03d}.png"]["artifacts"]:
                ok = S.found(hay, a)
                pt = ok or S.pointed(hay, a)
                av += 1; at += ok
                if a["tier"] == "CRITICAL":
                    cv += 1; ct += pt
        rows.append((label, px, el, reel, pgno, ct, cv, at, av))
        print(f"  {label:<18}{px:>6}{el:>7.1f}{f'{reel}/10':>7}{f'{pgno}/10':>7}"
              f"{f'{ct}/{cv}':>7}{ct/cv*100:>3.0f}%{f'{at}/{av}':>8}"
              f"{at/av*100:>4.0f}%{'':>4}")

    best = max(rows, key=lambda r: (r[5], r[3]))
    print(f"\n  BEST by CRITICAL-pointed: {best[0]} at {best[1]}px "
          f"-> {best[5]}/{best[6]} ({best[5]/best[6]*100:.0f}%), "
          f"reel {best[3]}/10, {best[2]:.1f}s")
    print(f"  baseline was 1800px: reel 3/10, CRITICAL pointed 81/101 (80%)")


if __name__ == "__main__":
    main()
