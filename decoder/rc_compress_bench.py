"""CAN COMPRESSED RICHMOND ACQUISITION RUN UNDER 1 SECOND PER DOCUMENT?

    ACRIS_CORPUS_ROOT=D:/acris python rc_compress_bench.py

Compression is PURE CPU and touches no server, so it is the one part of the
pipeline that can be parallelised freely - fetching cannot. The question is
whether it can be pushed below the fetch rate (~1 doc/s at conc 4) so it never
becomes the constraint.

⚠ MUST BE A FILE, NOT `python -c`. ProcessPoolExecutor pickles the worker by
module path; from an inline script on Windows every worker dies with
BrokenProcessPool.
"""
from __future__ import annotations

import io
import os
import pathlib
import sys
import time
from concurrent.futures import ProcessPoolExecutor

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

SRC = pathlib.Path("D:/acris/02-acquisition/documents/_boundary")


def convert(args):
    """(bytes_out, seconds, pages) for one document at one setting."""
    path, dpi, mode = args
    import fitz
    from PIL import Image
    t0 = time.time()
    doc = fitz.open(str(path))
    imgs = []
    for pg in doc:
        pm = pg.get_pixmap(dpi=dpi)
        im = Image.frombytes("RGB" if pm.n >= 3 else "L",
                             [pm.width, pm.height], pm.samples).convert("L")
        imgs.append(im.point(lambda x: 0 if x < 180 else 255, "1")
                    if mode == "bitonal" else im)
    buf = io.BytesIO()
    if imgs:
        if mode == "bitonal":
            imgs[0].save(buf, format="TIFF", compression="group4",
                         save_all=True, append_images=imgs[1:])
        else:
            imgs[0].save(buf, "PDF", save_all=True, append_images=imgs[1:],
                         quality=75)
    n = len(imgs)
    doc.close()
    return len(buf.getvalue()), time.time() - t0, n


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cores = os.cpu_count()
    src = sorted(SRC.glob("*.pdf"))[:12]
    if not src:
        sys.exit(f"  no test documents in {SRC}")
    orig = sum(p.stat().st_size for p in src)
    print(f"  {len(src)} documents · {orig/1e6:.0f} MB · {cores} CPU cores\n")
    print(f"  {'setting':<20} {'ratio':>7} {'serial s/doc':>13} "
          f"{'parallel s/doc':>15} {'verdict':>10}")

    for dpi, mode in ((200, "bitonal"), (150, "bitonal"), (120, "bitonal"),
                      (200, "gray"), (150, "gray")):
        jobs = [(p, dpi, mode) for p in src]
        t0 = time.time()
        r = [convert(j) for j in jobs]
        ser = (time.time() - t0) / len(src)
        with ProcessPoolExecutor(max_workers=min(8, cores)) as ex:
            t1 = time.time()
            list(ex.map(convert, jobs))
            par = (time.time() - t1) / len(src)
        comp = sum(x[0] for x in r)
        verdict = "SUB-1s" if par < 1.0 else ""
        print(f"  {mode+' '+str(dpi)+'dpi':<20} {orig/max(comp,1):>6.1f}x "
              f"{ser:>13.2f} {par:>15.2f} {verdict:>10}", flush=True)

    print("\n  fetch is ~1.0 doc/s at conc 4; any parallel figure below that")
    print("  means compression is NOT the constraint and can run inline.")


if __name__ == "__main__":
    main()
