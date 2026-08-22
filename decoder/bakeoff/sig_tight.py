"""THE SIGNATURE AT THE RESOLUTION THAT ACTUALLY WORKED.

⚠ THE FIRST NEGATIVE WAS NOT A FAIR TEST. sig_test.py cropped an 1800x733 band and fit
it to 900 px wide — the pen strokes ended up at HALF native size, and the model answered
UNREADABLE. The one handwriting success on this corpus (`732441`) came from a 490x166
crop upscaled 3x to 1470 px. Same model, same page, opposite treatment. So "the VLM
cannot read the signature" was a statement about my crop, not about the model.

⚠ WHAT THE 900 CEILING ACTUALLY IS. route.py caps --width 900 for FULL PAGES; the crash
in sig_test.py came from a 3600 px upscale. 1470 px ran fine. The real constraint is
total image tokens, so a SMALL region upscaled is cheap where a WHOLE page upscaled is
fatal. Crop first, then magnify — never magnify the page.

⚠ AND THE CONTROL MUST DISCRIMINATE. In sig_test.py both the signature and the blank
strip returned UNREADABLE, so the run could not distinguish "refuses this" from "refuses
everything". Here the control is a crop of PRINTED text: a reader that is working must
read it, so a UNREADABLE on the control invalidates the whole run.
"""
from __future__ import annotations

import pathlib, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from hand_test import start, ask

PAGE = HERE / "pages" / "FT_1680008647768" / "p009.png"
TRUTH = "Ariel Gratch"

# from the OCR run: 'By:' at y=1785, 'Attorney-in-Fact' at y=1817, WITNESS at y=1404.
# A signature sits ON or just ABOVE its 'By:' rule, so each band is taken generously
# upward and kept narrow.
BANDS = [("upper-by", 1600, 1800), ("lower-by", 1720, 1900),
         ("both-by", 1600, 1900), ("wide", 1380, 1900)]


def main():
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(PAGE).convert("RGB")
    print(f"  page {im.size}")

    prompts = [
        ("sig", "This is the signature line of a 1981 legal document. A person has signed "
                "it by hand. Transcribe the handwritten signature. Reply with the name "
                "only, or UNREADABLE."),
        ("all", "Transcribe every line in this image exactly, marking handwritten lines "
                "[hand] and printed lines [print]."),
    ]

    if not start():
        print("  server did not come up"); return 1
    print(f"  truth (hand key) = {TRUTH!r}\n")

    for tag, y0, y1 in BANDS:
        # right 2/3 of the page, where the execution block sits
        c = im.crop((im.width // 3, y0, im.width, y1))
        # ⚠ upscale the CROP, and only while it stays well under the page-level ceiling
        sc = 3 if c.width * 3 <= 1700 else max(1, 1700 // c.width)
        c = c.resize((c.width * sc, c.height * sc), Image.LANCZOS)
        p = HERE / f"_sig_{tag}.png"
        c.save(p)
        for name, pr in prompts:
            try:
                a = ask(p, pr, ntok=180)
            except Exception as e:
                a = f"ERR {type(e).__name__}"
                if start():
                    try:
                        a = ask(p, pr, ntok=180)
                    except Exception as e2:
                        a = f"ERR(retry) {type(e2).__name__}"
            hit = "  <== GRATCH" if "gratch" in a.lower() else ""
            print(f"  [{tag:<9} {str(c.size):<12} x{sc}] {name:<4} "
                  f"{a[:130]!r}{hit}")
        print()

    # ⚠ PRINTED CONTROL — if this comes back UNREADABLE the reader is broken and every
    # UNREADABLE above is meaningless.
    ctl = im.crop((im.width // 3, 1380, im.width, 1450))
    ctl = ctl.resize((ctl.width * 2, ctl.height * 2), Image.LANCZOS)
    ctl.save(HERE / "_sig_printed_control.png")
    try:
        a = ask(HERE / "_sig_printed_control.png", prompts[1][1], ntok=120)
    except Exception as e:
        a = f"ERR {type(e).__name__}"
    print(f"  PRINTED CONTROL (must be readable): {a[:130]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
