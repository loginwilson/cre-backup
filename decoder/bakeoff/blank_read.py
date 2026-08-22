"""READ THE FILLED BLANK, NOT THE SIGNATURE — the `personally came ____` test.

    python blank_read.py

⚠ THE HYPOTHESIS. `signature -> person` has been UNREAD since the first round, and every
attempt has aimed at the signature itself. But a signature is a stylized mark NEVER
INTENDED TO BE LEGIBLE — humans routinely cannot read them either, so no OCR quality and
no model size closes that gap; it is a category, not a shortfall. The acknowledgment states
the same person's name in a FORM BLANK a few inches below, and a filled blank is ordinary
handwriting. Different target, plausibly far easier.

⚠ AND THE PRINTED BOILERPLATE IS AN EXACT POINTER. `personally came` is pre-printed and
OCR reads it reliably (found at y=297-331 and y=862-902 on FT p010). The name sits
immediately to its right on the same line. So OCR points and the image is read in a small
region — the architecture doing what it was designed to do.

⚠ READ BLIND, NEVER PRIMED. Measured 2026-08-17 on this same document: asked cold the
model answered one way; told "OCR read this as 73241, correct it" it answered `732491`
TWICE. Priming transfers the error instead of correcting it. So the prompt here never
mentions a candidate name, never mentions the signature, and never mentions the hand key.

⚠ AND EVERY READ IS REPEATED AT TWO SCALES. Two agreeing runs at ONE size is one look —
that is exactly how `732441` was reported stable and then contradicted 5 readings to 2.
Agreement ACROSS SCALE is the test; a value that changes with magnification is unread.

⚠ CONTROL: a strip of pre-printed boilerplate with no blank. A reader that "finds" a name
there is pattern-completing, and every other answer in the run is worthless.
"""
from __future__ import annotations

import pathlib, sys, collections

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from hand_test import start, ask

PAGE = HERE / "pages" / "FT_1680008647768" / "p010.png"

# from the OCR: 'personally came' boxes. The blank runs to the right of each.
BLANKS = [("ack1-left",  (170,  285,  900,  345)),
          ("ack1-right", (875,  285, 1700,  345)),
          ("ack2-left",  (160,  850,  900,  915)),
          # a wider band in case the name wrapped to the line below
          ("ack1-2line", (170,  285, 1700,  400))]
CONTROL = ("control-boilerplate", (170, 380, 900, 430))

PROMPTS = [
    ("name", "This is a line from a printed legal form. Someone has written a person's "
             "name by hand in the blank. Reply with ONLY that name. If no handwritten "
             "name is present or it is not legible, reply NONE."),
    ("verbatim", "Transcribe this line exactly, marking handwritten words [hand] and "
                 "printed words [print]."),
]


def main():
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(PAGE).convert("RGB")
    if not start():
        print("  server did not come up"); return 1
    print(f"  FT p010 · reading the `personally came ___` blanks BLIND")
    print(f"  (no candidate name is ever shown to the model)\n")

    for tag, box in BLANKS + [CONTROL]:
        c = im.crop(box)
        answers = collections.Counter()
        for scale in (2, 3):
            # ⚠ crop-then-magnify is cheap; magnifying the PAGE is what killed the server
            up = c.resize((c.width * scale, c.height * scale), Image.LANCZOS)
            p = HERE / f"_blank_{tag}_{scale}x.png"
            up.save(p)
            for name, pr in PROMPTS:
                try:
                    a = ask(p, pr, ntok=90).strip().replace("\n", " ")
                except Exception as e:
                    a = f"ERR {type(e).__name__}"
                    if start():
                        try:
                            a = ask(p, pr, ntok=90).strip().replace("\n", " ")
                        except Exception:
                            pass
                print(f"  [{tag:<18} {scale}x] {name:<9} {a[:96]!r}")
                if name == "name":
                    answers[a.upper()] += 1
        # ⚠ agreement ACROSS SCALE is the verdict, not any single answer
        if answers:
            top, n = answers.most_common(1)[0]
            verdict = ("STABLE" if n == sum(answers.values()) and top != "NONE"
                       else "refused" if top == "NONE" else "SPLIT — unread")
            print(f"       -> {verdict}  {dict(answers)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
