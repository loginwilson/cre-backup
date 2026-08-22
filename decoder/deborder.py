"""FIND THE PAGE INSIDE THE FILM FRAME, then OCR that. Preprocessing for FT_.

⚠ THE FIRST PREPROCESSING ATTEMPT MADE TESSERACT WORSE AND THIS IS WHY. Cropping
a fixed top fraction of a microfilm scan does not crop the page — it crops the
FILM CARRIER: a huge grainy black border that the page floats inside. Tesseract
was handed mostly noise and returned `EER EE EEE EE NS OT`, scoring 2/10 against
3/10 for the untouched page. And the fraction is not even stable: on p002 the
page sits lower in the frame, so a 7.5% band misses the stamp completely.

So the page rectangle has to be FOUND, not assumed. The page is the bright
region; the carrier is black. Row and column brightness profiles locate it.

⚠ AND THE CROP IS VALIDATED AGAINST A KNOWN TRUTH, NOT EYEBALLED. The reel and
page numbers for this document are known (REEL 586, pages 761-770), so a crop
that loses the stamp is caught immediately rather than being reported as an
improvement.
"""
import pathlib
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def page_box(im, dark=110, need=0.90):
    """Trim the solid black film carrier ONLY. Never cut into content.

    ⚠ THE PREVIOUS VERSION CROPPED OUT TEXT, WHICH IS THE ONE THING A CROP MUST
    NEVER DO. It looked for the longest run of rows that were >55% BRIGHT and
    called that the page — but a row of dense type is not mostly bright, so the
    run terminated at the first heavy paragraph and the "page" it found excluded
    real content. On p009 it kept 38% of the frame, discarding the top half
    including the reel stamp; on p010 it started below the stamp. Measured as a
    preprocessing step it destroyed exactly the artifact it was built to rescue.
    Cropping is for removing WASTED SPACE, not for finding content.

    So this trims inward from each edge while the edge row/column is
    OVERWHELMINGLY dark (>=90% of pixels below `dark`) and stops at the first
    row that is not. Solid carrier goes; anything with ink in it stays. The
    operation can only ever remove near-uniform black margin, so in the worst
    case it is a no-op rather than a loss.
    """
    g = im.convert("L")
    w, h = g.size
    small = g.resize((max(1, w // 8), max(1, h // 8)), Image.BILINEAR)
    sw, sh = small.size
    px = small.load()

    def row_black(y):
        return sum(1 for x in range(sw) if px[x, y] < dark) >= sw * need

    def col_black(x):
        return sum(1 for y in range(sh) if px[x, y] < dark) >= sh * need

    y0 = 0
    while y0 < sh - 1 and row_black(y0):
        y0 += 1
    y1 = sh
    while y1 > y0 + 1 and row_black(y1 - 1):
        y1 -= 1
    x0 = 0
    while x0 < sw - 1 and col_black(x0):
        x0 += 1
    x1 = sw
    while x1 > x0 + 1 and col_black(x1 - 1):
        x1 -= 1

    # back off one step on every side so no ink sits on the boundary
    x0 = max(0, x0 - 1); y0 = max(0, y0 - 1)
    x1 = min(sw, x1 + 1); y1 = min(sh, y1 + 1)
    box = (x0 * 8, y0 * 8, min(w, x1 * 8), min(h, y1 * 8))
    if (box[2] - box[0]) * (box[3] - box[1]) < 0.30 * w * h:
        return (0, 0, w, h)       # implausible -> leave the page alone
    return box


def ocr(img, psm, tmp):
    img.save(tmp)
    r = subprocess.run([TESS, str(tmp), "stdout", "--psm", str(psm)],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return " ".join(r.stdout.split())


def main():
    src = pathlib.Path("render/testdoc/FT_1680008647768/raw")
    out = pathlib.Path("render/testdoc/FT_1680008647768/_prep")
    out.mkdir(exist_ok=True)
    tmp = out / "_t.png"
    truth = {i: (586, 760 + i) for i in range(1, 11)}

    print("  page-rectangle detection (raw film frame -> page)\n")
    print(f"  {'pg':>3}{'raw size':>14}{'page box':>26}{'kept':>7}")
    boxes = {}
    for i in range(1, 11):
        im = Image.open(src / f"p{i:03d}.tif")
        if im.mode == "1":
            im = im.convert("L")
        b = page_box(im)
        boxes[i] = (im, b)
        kept = (b[2] - b[0]) * (b[3] - b[1]) / (im.width * im.height)
        print(f"  {i:>3}{f'{im.width}x{im.height}':>14}"
              f"{str(b):>26}{kept*100:>6.0f}%")

    print(f"\n  stamp band from the DETECTED page, ground truth REEL 586 / 761-770\n")
    print(f"  {'band':<8}{'psm':>4}{'reel':>8}{'page':>8}{'both':>8}   p001 sample")
    print("  " + "-" * 74)
    best = (0, None, None)
    for band in (0.06, 0.10, 0.14):
        for psm in (7, 11, 6):
            r = pg = both = 0
            sample = ""
            for i in range(1, 11):
                im, b = boxes[i]
                page = im.crop(b)
                st = page.crop((0, 0, page.width, max(8, int(page.height * band))))
                st = st.resize((st.width * 3, st.height * 3), Image.LANCZOS)
                txt = ocr(st, psm, tmp)
                if i == 1:
                    sample = txt[:30]
                nums = re.findall(r"\d+", txt)
                hr = "586" in nums
                hp = str(truth[i][1]) in nums
                r += hr; pg += hp; both += (hr and hp)
            print(f"  {band:<8.2f}{psm:>4}{f'{r}/10':>8}{f'{pg}/10':>8}"
                  f"{f'{both}/10':>8}   {sample}")
            if both > best[0]:
                best = (both, band, psm)
    print(f"\n  BEST band={best[1]} psm={best[2]} -> {best[0]}/10 with BOTH")
    print(f"  baseline: untouched full page got a usable reel number on 3/10")

    # write de-bordered full pages for a full-document re-run
    for i in range(1, 11):
        im, b = boxes[i]
        p = im.crop(b)
        tw = 1800
        p = p.resize((tw, int(p.height * tw / p.width)), Image.LANCZOS)
        p.save(out / f"p{i:03d}.png")
    print(f"\n  de-bordered pages -> {out}")


if __name__ == "__main__":
    main()
