"""ALTER THE VIEW FOR READING. Deskew, unframe, despeckle — and TIME IT.

The objection this file has to answer: "it sounds like it'd add a ton of time to
the workflow." So every stage is timed separately and the totals are printed in
milliseconds per page. If pre-processing costs more than the read it precedes,
that is a finding and it should be visible, not buried.

⚠ NO MODEL IS INVOLVED HERE AND THAT IS THE POINT. Deskew, frame removal and
despeckle are arithmetic on pixels. The intelligence — "this view is not good
enough, give me a closer one" — is a SEPARATE decision made by the reader, and
it should only fire on the pages that need it. Conflating the two is how a
pipeline ends up spending model calls on a rotation.

⚠ CONFIDENCE IS A PROXY AND IT CAN LIE. Reported beside WORD COUNT, because
that is what caught the last mistake here: film scored 45.2 confidence not
because the ink was bad but because Tesseract was finding 944 phantom words in
the film grain against ~324 on a real page. If cropping works, confidence rises
AND the count falls. Confidence rising alone means something else happened.

    python preprocess.py                 run the film sample, before vs after
    python preprocess.py <doc_id>        one document, write the images out
"""
import os
import pathlib
import statistics
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = pathlib.Path("sample_pages")
OUT = pathlib.Path("render/pre")
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCRATCH = pathlib.Path(os.environ["TMP"]) / "prep"
SCRATCH.mkdir(parents=True, exist_ok=True)


# ── stage 1 · find the page inside the film frame ───────────────────────
def unframe(g, frame_ink=0.45, pad=10):
    """Largest contiguous band of rows/cols whose ink density reads as PAGE.

    ⚠ A PAGE ROW AND A FRAME ROW ARE NOT CLOSE. Measured previously: the top 3%
    of a film page is 88% black and the bottom 92%, while the document body runs
    ~16% and a modern page ~6%. The gap is enormous, so a blunt cut at 45%
    separates them with no tuning — and an untuned threshold is the only kind
    that transfers to documents nobody has looked at.
    """
    ink = (g < 128).astype(np.float32)
    rows, cols = ink.mean(1), ink.mean(0)

    def band(v):
        ok = v < frame_ink
        best = cur = 0
        s = bs = be = 0
        for i, k in enumerate(ok):
            if k:
                if cur == 0:
                    s = i
                cur += 1
                if cur > best:
                    best, bs, be = cur, s, i
            else:
                cur = 0
        return bs, be
    r0, r1 = band(rows)
    c0, c1 = band(cols)
    H, W = g.shape
    # ⚠ REFUSE A SILLY CROP. If the band logic collapses (a page that really is
    # dark, a scan with no frame) it must return the original, not a sliver.
    if (r1 - r0) < H * 0.3 or (c1 - c0) < W * 0.3:
        return g, False
    return g[max(0, r0 - pad):min(H, r1 + pad),
             max(0, c0 - pad):min(W, c1 + pad)], True


# ── stage 2 · deskew ────────────────────────────────────────────────────
def deskew(g, limit=6.0, step=0.25):
    """Rotate to maximise horizontal projection sharpness.

    ⚠ PROJECTION PROFILE, NOT minAreaRect. minAreaRect fits a box to all ink and
    is thrown by a signature, a margin stamp or a stray blob. Text lines make
    the row-sum profile spiky when they are level, and that signal comes from
    the whole page rather than its convex hull.

    ⚠ MEASURED ON A DOWNSCALE. The angle is a property of the layout, not of the
    resolution, so searching at 800px wide costs ~1/10th and finds the same
    answer. The rotation is then applied ONCE, at full size.
    """
    small = cv2.resize(g, (800, int(g.shape[0] * 800 / g.shape[1])),
                       interpolation=cv2.INTER_AREA)
    bw = (small < 128).astype(np.float32)
    best, ang = -1.0, 0.0
    a = -limit
    while a <= limit:
        M = cv2.getRotationMatrix2D((bw.shape[1] / 2, bw.shape[0] / 2), a, 1)
        r = cv2.warpAffine(bw, M, (bw.shape[1], bw.shape[0]), flags=cv2.INTER_NEAREST)
        prof = r.sum(1)
        score = float(((prof[1:] - prof[:-1]) ** 2).sum())   # sharpness
        if score > best:
            best, ang = score, a
        a += step
    if abs(ang) < step:
        return g, 0.0
    H, W = g.shape
    M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, 1)
    return cv2.warpAffine(g, M, (W, H), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE), ang


# ── stage 3 · despeckle ─────────────────────────────────────────────────
def despeckle(g, max_area=12):
    """Drop connected blobs too small to be a glyph.

    ⚠ CONSERVATIVE ON PURPOSE. A period, the dot of an i, and a decimal point
    are all tiny — and a decimal point is the difference between $120,666.44 and
    $12066644. 12px at 300dpi is smaller than any of them, so this removes grain
    and nothing else. Raising it to "clean up better" is how you delete a
    decimal.
    """
    bw = (g < 128).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
    kill = np.zeros(n, bool)
    kill[1:] = stats[1:, cv2.CC_STAT_AREA] <= max_area
    out = g.copy()
    out[kill[lab]] = 255
    return out, int(kill.sum())


def prep(path):
    t = {}
    t0 = time.time()
    g = np.array(Image.open(path).convert("L"))
    t["load"] = time.time() - t0
    native = g.shape[::-1]

    t0 = time.time(); g, cropped = unframe(g);      t["unframe"] = time.time() - t0
    t0 = time.time(); g, ang = deskew(g);           t["deskew"] = time.time() - t0
    t0 = time.time(); g, killed = despeckle(g);     t["despeckle"] = time.time() - t0
    return g, {"native": native, "out": g.shape[::-1], "cropped": cropped,
               "angle": ang, "speckles": killed, "t": t}


# ── measurement ─────────────────────────────────────────────────────────
def tess(img_arr, tag):
    f = SCRATCH / f"{tag}.png"
    Image.fromarray(img_arr).save(f)
    r = subprocess.run([TESS, str(f), "stdout", "--psm", "6", "-c",
                        "tessedit_create_tsv=1"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    confs, words = [], 0
    for line in r.stdout.splitlines()[1:]:
        p = line.split("\t")
        if len(p) < 12:
            continue
        try:
            c = float(p[10])
        except ValueError:
            continue
        if c >= 0 and p[11].strip():
            confs.append(c); words += 1
    return (statistics.mean(confs) if confs else 0.0), words


def main():
    if not SRC.exists():
        print("  run from the decoder directory"); return
    if len(sys.argv) > 1:
        doc = sys.argv[1]
        d = OUT / doc; d.mkdir(parents=True, exist_ok=True)
        for p in sorted((SRC / doc).glob("*.tif")):
            g, m = prep(p)
            Image.fromarray(g).save(d / f"{p.stem}.png")
            print(f"  {p.stem}  {m['native']} -> {m['out']}  "
                  f"skew {m['angle']:+.2f}deg  {m['speckles']:,} specks  "
                  f"{sum(m['t'].values())*1000:.0f}ms")
        print(f"\n  -> {d}"); return

    film = sorted(d for d in SRC.iterdir() if d.is_dir() and d.name.startswith("FT_"))
    pages = [next(iter(sorted(d.glob("*.tif"))), None) for d in film[:30]]
    pages = [p for p in pages if p]
    print(f"  {len(pages)} film pages (first page of {len(pages)} documents)\n")
    print(f"  {'page':<20}{'skew':>7}{'crop':>6}{'ms':>7}"
          f"{'conf before':>13}{'after':>8}{'words before':>14}{'after':>8}")

    stats = {"ms": [], "cb": [], "ca": [], "wb": [], "wa": [], "ang": []}
    for p in pages:
        raw = np.array(Image.open(p).convert("L"))
        g, m = prep(p)
        cb, wb = tess(raw, "before")
        ca, wa = tess(g, "after")
        ms = sum(m["t"].values()) * 1000
        stats["ms"].append(ms); stats["cb"].append(cb); stats["ca"].append(ca)
        stats["wb"].append(wb); stats["wa"].append(wa); stats["ang"].append(m["angle"])
        print(f"  {p.parent.name:<20}{m['angle']:>+6.2f}{'Y' if m['cropped'] else '-':>6}"
              f"{ms:>7.0f}{cb:>13.1f}{ca:>8.1f}{wb:>14,}{wa:>8,}")

    n = len(stats["ms"])
    print(f"\n  ── MEANS over {n} film pages ──")
    print(f"  pre-process time      {statistics.mean(stats['ms']):>8.0f} ms/page")
    print(f"  Tesseract confidence  {statistics.mean(stats['cb']):>8.1f}  ->"
          f"{statistics.mean(stats['ca']):>8.1f}")
    print(f"  word count            {statistics.mean(stats['wb']):>8,.0f}  ->"
          f"{statistics.mean(stats['wa']):>8,.0f}"
          f"   (toward ~324 = phantom tokens gone)")
    print(f"  |skew| corrected      {statistics.mean([abs(a) for a in stats['ang']]):>8.2f} deg")
    print(f"\n  ⚠ confidence UP and word count DOWN together is the only pattern "
          f"that means\n    the frame stopped being read. Either alone proves nothing.")


if __name__ == "__main__":
    main()
