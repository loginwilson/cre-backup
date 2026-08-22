"""CAN OCR CARRY THE FILTER? Measured against claims whose text was read by eye.

⚠ THE QUESTION IS NOT "IS THE OCR GOOD". It is "is the OCR good enough to
decide WHICH PAGES A MODEL MUST OPEN" — because that decision is where the
6.6 billion tokens go. Today a page costs ~194 tokens just to find out it says
nothing. If a free local pass can answer that, the vision budget collapses to
the pages that actually carry a term.

So there are TWO metrics and they are not the same metric:

    LOCATE   does the distinctive PHRASE survive? decides which page to open.
             Errors are cheap: a garbled word still matches on its neighbours.

    READ     does the NUMBER or IDENTIFIER survive EXACTLY? decides what gets
             claimed. Errors here are not cheap — they are silent and wrong
             forever, and a CRFN off by one digit points at another
             instrument that really exists.

⚠ MEASURED ON THE SMOKE TEST, BEFORE ANY SCORING: prose came back clean while
"($10.00)" came back "(S10.o0)" and the grantor lost two words of its name. If
that holds, OCR is a FILTER and never a TRANSCRIBER, and any design that lets
an OCR string become a claim value is broken by construction.

GROUND TRUTH is the verbatim text already stored in claims.py — quotes taken
off the page by eye, with the document and page recorded. That is the only
labelled set this project has, and it exists because the extractor was made to
record `verbatim` and `page` from the start.
"""
import pathlib
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_ocr = None


def engine():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    return _ocr


def text_of(path):
    res, _ = engine()(str(path))
    return " ".join(r[1] for r in res) if res else ""


def norm(s):
    """Collapse to letters+digits, lowercase. For LOCATE scoring only."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def phrase_recall(hay, needle, k=4):
    """Fraction of the needle's k-word shingles present in the haystack.

    ⚠ NOT an exact-substring test. A single mangled character would score a
    perfect phrase at zero, which would answer a question nobody asked — the
    filter only needs to rank this page above the pages that lack the idea.
    """
    h, n = norm(hay), norm(needle)
    hw, nw = h.split(), n.split()
    if len(nw) < k:
        return 1.0 if n in h else 0.0
    hs = {" ".join(hw[i:i + k]) for i in range(len(hw) - k + 1)}
    ns = [" ".join(nw[i:i + k]) for i in range(len(nw) - k + 1)]
    return sum(1 for s in ns if s in hs) / len(ns)


MONEY = re.compile(r"\$\s?[\d,]+(?:\.\d\d)?")
CRFN = re.compile(r"\b(?:CRFN\s*)?(\d{10,16})\b")


def numbers_in(s):
    return {re.sub(r"[^\d.]", "", m) for m in MONEY.findall(s)}
