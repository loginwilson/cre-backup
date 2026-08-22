"""READ THE p009 SIGNATURE — the ten-round permanent UNREAD.

⚠ WHY THIS IS WORTH RUNNING. `signature -> person` has been recorded UNREAD since the
first extraction round, and extract.py now emits `state: unread_handwritten` by design
rather than launder an OCR guess (`Katbhals`, `Mirort`, `easonu`) into a participant.
But the hand key's own summary names the signer: **"signed by attorney-in-fact Ariel
Gratch"**. So the fact IS on the page, in pen, and the channel that just proved it reads
handwriting (732441, exact and stable, with a blank-paper refusal control) has never been
pointed at it.

⚠ AND UNLIKE 732441 THIS IS A TABLE FIELD. Login, 2026-08-17: "we need to make sure what
we extract slots into the data tables. if it doesnt, its just wasted time." `signer_name`
is a participant on the CAPITAL event; `732441` fills nothing. That is the difference
between closing a gap and chasing a denominator.

⚠ THE OCR'S GUESS IS NEVER SHOWN TO THE MODEL. Measured one hour ago on the same
document: asked cold the VLM read `732441` correctly twice; told "OCR read this as 73241,
correct it" it answered `732491` twice — stably wrong. Priming with a candidate value
transfers the error instead of correcting it. OCR points at a REGION; it never supplies
the value for the field being read.

⚠ AND A NAME IS SCORED AGAINST A REFUSAL CONTROL, because a model asked "who signed this"
will always produce a name. The control here is a blank crop from the same page.
"""
from __future__ import annotations

import json, pathlib, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

from hand_test import start, ask  # server lifecycle + the load-bearing HTTP settings

PAGE = HERE / "pages" / "FT_1680008647768" / "p009.png"
TRUTH = "Ariel Gratch"

# ⚠ MARKERS, NOT COORDINATES. The execution block is found by the PRINTED text around
# it — the authority chain OCR reads perfectly — and the crop is taken from those boxes.
MARK = ("attorney-in-fact", "attorney in fact", "general partner", "by:", "witness")

PROMPTS = [
    ("name", "This is the signature block of a 1981 mortgage. Read the HANDWRITTEN "
             "signature and reply with the signer's name only. If the handwriting is "
             "not legible, reply UNREADABLE."),
    ("verbatim", "Transcribe everything in this image, both printed and handwritten, "
                 "line by line. Mark handwritten lines with [hand]."),
    ("who", "Who physically signed this document, and in what capacity? Reply as "
            "NAME | CAPACITY. Use UNREADABLE for either part you cannot read."),
]


def main():
    from PIL import Image
    import numpy as np
    Image.MAX_IMAGE_PIXELS = None
    from rapidocr import RapidOCR, EngineType, ModelType, OCRVersion, LangDet, LangRec

    ocr = RapidOCR(params={
        "Det.engine_type": EngineType.OPENVINO, "Det.lang_type": LangDet.CH,
        "Det.model_type": ModelType("tiny"), "Det.ocr_version": OCRVersion("PP-OCRv6"),
        "Rec.engine_type": EngineType.OPENVINO, "Rec.lang_type": LangRec.CH,
        "Rec.model_type": ModelType("tiny"), "Rec.ocr_version": OCRVersion("PP-OCRv6"),
        "Det.engine_cfg.openvino.inference_num_threads": 8,
        "Rec.engine_cfg.openvino.inference_num_threads": 8})

    im = Image.open(PAGE).convert("RGB")
    res = ocr(np.array(im))
    txts = [str(t) for t in (getattr(res, "txts", None) or [])]
    boxes = getattr(res, "boxes", None)

    ys = []
    for j, t in enumerate(txts):
        if any(m in t.lower() for m in MARK) and boxes is not None:
            b = np.array(boxes[j])
            ys.append((int(b[:, 1].min()), int(b[:, 1].max()), t.strip()[:44]))
    if not ys:
        print("  no execution-block markers found on p009"); return 1
    print(f"  OCR found {len(ys)} execution-block markers (printed, read cleanly):")
    for y0, y1, t in ys:
        print(f"     y={y0:<6} {t!r}")

    top = max(0, min(y for y, _, _ in ys) - 140)
    bot = min(im.height, max(y for _, y, _ in ys) + 140)

    # ⚠ 900 PX IS A HARD CEILING, NOT A PREFERENCE. route.py defaults --width 900
    # because 1400 hangs the encoder. The first run of this script fed a full-width
    # page strip UPSCALED 2x (3600 px) and the server died with ConnectionResetError
    # on request one, then refused every later request — six ERR rows that look like
    # six results. Upscaling helps a CTC recogniser; it kills this one.
    def fit(img, w=900):
        if img.width <= w:
            return img
        return img.resize((w, max(1, round(img.height * w / img.width))), Image.LANCZOS)

    full = im.crop((0, top, im.width, bot))
    fit(full).save(HERE / "_sig_block.png")
    # right half only — the execution block sits right of centre on this page, and a
    # tighter crop spends the 900 px budget on the signature instead of the margin.
    half = im.crop((im.width // 3, top, im.width, bot))
    fit(half).save(HERE / "_sig_block_tight.png")
    print(f"\n  crop y={top}..{bot} · full {full.size} -> {fit(full).size}"
          f" · tight {half.size} -> {fit(half).size}")

    # blank control from the same page, same width
    blank = im.crop((0, max(0, top - 400), im.width, max(1, top - 260)))
    fit(blank).save(HERE / "_sig_control.png")

    if not start():
        print("  server did not come up"); return 1
    print(f"\n  truth (hand key) = {TRUTH!r}\n")
    for img, tag in ((HERE / "_sig_block_tight.png", "tight"),
                     (HERE / "_sig_block.png", "full")):
        for name, p in PROMPTS:
            try:
                a = ask(img, p, ntok=200)
            except Exception as e:
                # ⚠ A DEAD SERVER MUST NOT BE REPORTED AS A READING. One crash makes
                # every later request fail identically, and a column of ERR rows reads
                # like evidence the model could not do it. Restart and retry once.
                a = f"ERR {type(e).__name__}: {str(e)[:50]}"
                if start():
                    try:
                        a = ask(img, p, ntok=200)
                    except Exception as e2:
                        a = f"ERR(retry) {type(e2).__name__}: {str(e2)[:44]}"
            hit = "  <== GRATCH" if "gratch" in a.lower() else ""
            print(f"  [{tag}] {name:<9} {a[:150]!r}{hit}")
        print()
    try:
        c = ask(HERE / "_sig_control.png", PROMPTS[0][1], ntok=60)
    except Exception as e:
        c = f"ERR {type(e).__name__}"
    print(f"  CONTROL (blank strip, same page)  {c[:90]!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
