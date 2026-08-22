"""WHAT A COORDINATE ACTUALLY IS, AND WHAT IT COSTS TO TURN ONE BACK INTO A PICTURE.

⚠ A HUMAN NEVER READS A COORDINATE. That is the whole point and it is easy to
lose: the box is a RECIPE, not a display format. It is stored because it is 40
bytes instead of 15 KB, and the instant anyone wants to look, it is cooked back
into the same crop it came from. Nobody is ever shown '(412, 1883, 1502, 1971)'.

So this prints the same box four ways -- raw pixels, fraction of page, inches,
and plain English -- to make the point that the pixel form is the machine's
copy and every other form is derived from it for free.

⚠ AND IT TIMES THE RENDER, because that number decides whether crops are an
ASSET or a CACHE. If cooking a crop from a stored page is fast, pre-generating
0.63 TB of crops for claims nobody ever clicks is waste. If it is slow, the
crops have to live on the drive.

    python what_is_a_coordinate.py [doc_id]
"""
import glob
import gzip
import json
import pathlib
import re
import statistics
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

OCR = pathlib.Path("sample_ocr")
PAGES = pathlib.Path("sample_pages")
OUT = pathlib.Path("render/coord")
DPI = 300.0

# a frame that should sit next to an actual NUMBER, so the crop is a claim and
# not just a phrase
RX = re.compile(r"floor\s+area", re.I)


def find_hit(doc=None):
    files = [OCR / f"{doc}.json.gz"] if doc else sorted(OCR.glob("*.json.gz"))
    for p in files:
        if not p.exists():
            continue
        try:
            rows = json.load(gzip.open(p, "rt", encoding="utf-8"))
        except Exception:
            continue
        d = p.name[:-8]
        if not (PAGES / d).exists():
            continue
        for r in rows:
            ws = r["words"]
            toks, spans, pos = [], [], 0
            for i, w in enumerate(ws):
                toks.append(w["t"]); spans.append((pos, pos + len(w["t"]), i))
                pos += len(w["t"]) + 1
            text = " ".join(toks)
            for m in RX.finditer(text):
                idx = [i for s, e, i in spans if s < m.end() and e > m.start()]
                if not idx:
                    continue
                lo, hi = min(idx), max(idx)
                # ⚠ REQUIRE A NUMBER IN THE WINDOW. "floor area" alone is a
                # phrase; "floor area of 78,000 square feet" is a claim. Showing
                # the phrase would demonstrate the plumbing and dodge the point.
                win = ws[max(0, lo - 8):min(len(ws), hi + 30)]
                if not any(re.search(r"\d[\d,]{3,}", w["t"]) for w in win):
                    continue
                if (PAGES / d / f"p{r['page']:03d}.tif").exists():
                    return d, r["page"], ws, lo, hi, win
    return None


def main():
    hit = find_hit(sys.argv[1] if len(sys.argv) > 1 else None)
    if not hit:
        print("  no claim-shaped hit found"); return
    doc, page, ws, lo, hi, win = hit

    x0 = min(w["x"] for w in win); x1 = max(w["x"] + w["w"] for w in win)
    y0 = min(w["y"] for w in win); y1 = max(w["y"] + w["h"] for w in win)

    src = PAGES / doc / f"p{page:03d}.tif"
    im = Image.open(src)
    W, H = im.size

    print(f"  document {doc}   page {page}   page is {W} x {H} px\n")
    print(f"  THE TEXT AT THAT BOX:")
    print(f"    {' '.join(w['t'] for w in win)}\n")

    print(f"  THE SAME BOX, FOUR WAYS")
    print(f"    stored (pixels)   ({x0}, {y0}, {x1}, {y1})")
    print(f"    fraction of page  x {x0/W:.3f}-{x1/W:.3f}   y {y0/H:.3f}-{y1/H:.3f}")
    print(f"    inches @300dpi    {x0/DPI:.2f}\" from left, {y0/DPI:.2f}\" from top,"
          f" {(x1-x0)/DPI:.2f}\" x {(y1-y0)/DPI:.2f}\"")
    col = "left" if x1 < W * .55 else ("right" if x0 > W * .45 else "full width")
    down = int(y0 / H * 100)
    print(f"    plain english     {col} of the page, {down}% down\n")

    print(f"  WHAT IT COSTS TO STORE")
    box_bytes = len(json.dumps({"d": doc, "p": page, "b": [x0, y0, x1, y1]}).encode())
    print(f"    the coordinate    {box_bytes} bytes")

    # ── render it back, and time that ────────────────────────────────────
    OUT.mkdir(parents=True, exist_ok=True)
    times = []
    for _ in range(5):
        t0 = time.time()
        pg = Image.open(src)
        if pg.mode == "1":
            pg = pg.convert("L")            # ⚠ 'L' before resize, always
        c = pg.crop((max(0, x0 - 40), max(0, y0 - 30),
                     min(W, x1 + 40), min(H, y1 + 30)))
        c = c.resize((int(c.width * 2.5), int(c.height * 2.5)), Image.LANCZOS)
        times.append((time.time() - t0) * 1000)
    f = OUT / f"{doc}_p{page:03d}.png"
    c.save(f)
    print(f"    the rendered crop {f.stat().st_size:,} bytes"
          f"   ({f.stat().st_size/box_bytes:,.0f}x bigger)")
    print(f"\n  WHAT IT COSTS TO COOK IT BACK")
    print(f"    median render     {statistics.median(times):.0f} ms")
    print(f"    -> {f}")

    print(f"\n  ⚠ NOBODY IS EVER SHOWN THE PIXEL FORM. It is stored because it is")
    print(f"    {f.stat().st_size/box_bytes:,.0f}x smaller than the picture, and every human-readable")
    print(f"    form above was computed from it for nothing.")


if __name__ == "__main__":
    main()
