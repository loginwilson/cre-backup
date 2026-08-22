"""RENDER WHAT IS ALREADY ON DISK, THE WAY A MODEL WANTS TO SEE IT.

The pages in sample_pages/<doc_id>/p###.tif are native 2550x3300 1-bit G4 —
the same pixels ACRIS serves, the same pixels the PDF wraps. Nothing about
capture needs improving. What needs deciding is how to hand them to a model.

⚠ 1-BIT IS THE TRAP. PIL opens these in mode '1', and a naive resize of a 1-bit
image uses nearest-neighbour: it THROWS AWAY strokes rather than blending them,
so thin text disintegrates and the result looks worse than the original at a
smaller size. Convert to 'L' FIRST, then resize with LANCZOS, so downscaling
averages ink instead of discarding it.

⚠ AND BIGGER IS NOT FREE. Vision tokens scale with pixels. 2550x3300 is ~8.4MP;
most document VLMs want ~1.5-2.5MP for dense text. This renders a few widths so
the accuracy/cost curve can be measured rather than guessed.

    python render_pages.py                  list documents available
    python render_pages.py <doc_id>         render every page, all widths
    python render_pages.py <doc_id> 1  1700 render page 1 at width 1700
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

SRC = pathlib.Path("sample_pages")
OUT = pathlib.Path("render")
WIDTHS = (1275, 1700, 2550)          # 150 / 200 / 300 dpi equivalent


def render(tif, width):
    im = Image.open(tif)
    # ⚠ 'L' BEFORE RESIZE. See the note above — this line is the whole file.
    if im.mode == "1":
        im = im.convert("L")
    if width and im.width != width:
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
    return im


def main():
    if not SRC.exists():
        print("  sample_pages/ not found — run from the decoder directory")
        return
    docs = sorted(p.name for p in SRC.iterdir() if p.is_dir())
    if len(sys.argv) < 2:
        print(f"  {len(docs)} documents in {SRC}/\n")
        for d in docs[:25]:
            n = len(list((SRC / d).glob("*.tif")))
            print(f"    {d}   {n:>3} pages")
        print(f"    ... ({len(docs)} total)")
        print(f"\n  render one:  python render_pages.py {docs[0]}")
        return

    doc = sys.argv[1]
    only = int(sys.argv[2]) if len(sys.argv) > 2 else None
    widths = (int(sys.argv[3]),) if len(sys.argv) > 3 else WIDTHS

    tifs = sorted((SRC / doc).glob("*.tif"))
    if not tifs:
        print(f"  no pages for {doc}")
        return
    if only:
        tifs = [t for t in tifs if int(t.stem[1:]) == only]

    d = OUT / doc
    d.mkdir(parents=True, exist_ok=True)
    print(f"  {doc} · {len(tifs)} page(s)\n")
    print(f"  {'page':>5}{'native':>14}{'width':>8}{'out px':>14}{'KB':>9}")
    for t in tifs:
        native = Image.open(t).size
        for w in widths:
            im = render(t, w)
            f = d / f"{t.stem}_w{w}.png"
            im.save(f, optimize=True)
            print(f"  {t.stem:>5}{f'{native[0]}x{native[1]}':>14}{w:>8}"
                  f"{f'{im.width}x{im.height}':>14}{f.stat().st_size/1024:>8.0f}")
    print(f"\n  -> {d}")
    print(f"  ⚠ megapixels drive vision-token cost: "
          + ", ".join(f"{w}px={w*(native[1]/native[0])*w/1e6:.1f}MP" for w in widths))


if __name__ == "__main__":
    main()
