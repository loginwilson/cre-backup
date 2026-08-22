"""COMPRESS LANDED RICHMOND PDFS IN PLACE - the background half of the
land/convert split (2026-08-21: inline G4 conversion ran ~0.4 docs/s and
bottlenecked the whole Chrome lane, so rc_pdf_land --raw lands at ~10/s
and THIS daemon compresses afterwards, at leisure).

The discriminator is the pdf's own image filter: a raw viewer save carries
JPEG pages (DCTDecode); a converted file carries G4 (CCITTFaxDecode).
Nothing needs a worklist - the store is scanned and already-converted
files identify themselves. Keep-whichever-is-smaller still rules: docs
that would inflate under G4 are marked done by rewriting nothing (their
filter stays DCTDecode but size wins; a tiny .g4skip ledger remembers them
so they are not re-tried every sweep).

Runs single-threaded on purpose - it must never compete with the lanes.

Usage:  python rc_convert.py [--loop] [--pace 0.2]
"""
import argparse
import io
import json
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fitz
import img2pdf
from PIL import Image

STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                     r"\Legal Instruments Acquisition\By Document")
SKIP = STORE.parent / "_rc_g4skip.json"   # ids proven smaller as-is

ap = argparse.ArgumentParser()
ap.add_argument("--loop", action="store_true")
ap.add_argument("--pace", type=float, default=0.2,
                help="sleep between docs - this daemon yields, always")
a = ap.parse_args()


def is_raw(path):
    """True if any page image is JPEG (DCTDecode) - i.e. not yet G4."""
    try:
        d = fitz.open(str(path))
        for page in d:
            for img in page.get_images(full=True):
                if "DCT" in (d.extract_image(img[0]).get("ext", "") or ""):
                    d.close()
                    return True
                break                      # first image per page suffices
        d.close()
    except Exception:
        return False
    return False


def sweep():
    skip = set()
    if SKIP.exists():
        try:
            skip = set(json.loads(SKIP.read_text()))
        except Exception:
            pass
    n = kept = 0
    for src in STORE.rglob("RC_*.pdf"):
        if src.stem in skip or not is_raw(src):
            continue
        try:
            d = fitz.open(str(src))
            frames = []
            for page in d:
                pix = page.get_pixmap(dpi=200)
                im = Image.frombytes("RGB", (pix.width, pix.height),
                                     pix.samples)
                buf = io.BytesIO()
                im.convert("1").save(buf, format="TIFF",
                                     compression="group4")
                frames.append(buf.getvalue())
            raw = src.stat().st_size
            d.close()
            out = img2pdf.convert(frames)
            if len(out) < raw:
                tmp = src.with_suffix(".g4tmp")
                tmp.write_bytes(out)       # never truncate the original
                tmp.replace(src)           # atomic swap on the same volume
                n += 1
            else:
                skip.add(src.stem)
                kept += 1
        except Exception as e:
            print(f"  {src.stem}: convert failed ({type(e).__name__})"
                  " - left raw", flush=True)
        if (n + kept) % 100 == 0 and (n or kept):
            SKIP.write_text(json.dumps(sorted(skip)))
            print(f"converted {n} · kept-raw {kept}", flush=True)
        time.sleep(a.pace)
    SKIP.write_text(json.dumps(sorted(skip)))
    if n or kept:
        print(f"sweep done: converted {n} · kept-raw {kept}", flush=True)


while True:
    sweep()
    if not a.loop:
        break
    time.sleep(300)
