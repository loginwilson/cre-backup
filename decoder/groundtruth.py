"""The labelled set: document text a human actually read off a numbered page.

⚠ WHY THIS IS A MODULE AND NOT THREE LINES OF REGEX. The first version regexed
claims.py source for quoted spans and produced "ground truth" like:

    ALL that portion of " "the below described parcel LYING BELOW...
    , TWICE MORE. Exhibit G in both the " "lot 23 and the lot 22 agreements

The first is a real quote with PYTHON STRING-CONCATENATION SEAMS baked into it
— the source breaks the literal across lines, and the regex read the source
rather than the value. The second is not document text at all; it is my own
commentary, which happens to contain quote marks.

Scored against that set, OCR came back at 0.22 recall on clean laser print and
I was one paragraph from reporting "OCR barely works on modern documents." THE
MEASUREMENT WAS BROKEN, NOT THE THING BEING MEASURED — the same failure as the
p001 fingerprint, the darkness-based cover detector, and the range scan: a
check that runs, produces a number, and answers a question nobody asked.

⚠ PARSE THE VALUE, NEVER THE SOURCE. `ast` gives the string Python would
actually build, seams closed, escapes resolved.

WHAT COUNTS AS GROUND TRUTH HERE
    Only single-quoted spans inside a claim's `text=`, which is this project's
    convention for "these are the document's words, not mine". Commentary is
    written unquoted. That convention is imperfect — some analyst asides carry
    quotes — so spans are additionally required to look like running document
    prose rather than a fragment.
"""
import ast
import collections
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MIN_LEN = 40          # shorter spans are fragments, not testable prose
MIN_WORDS = 7


def _quoted_spans(value):
    """Single-quoted runs inside a claim's text value."""
    return [m.group(1) for m in re.finditer(r"'([^']{%d,})'" % MIN_LEN, value)]


def _plausible(span):
    """Reject analyst commentary that happens to be quoted.

    ⚠ HEURISTIC, AND IT IS ALLOWED TO BE — a wrongly-excluded quote costs one
    row of a labelled set, while a wrongly-INCLUDED piece of my own prose
    silently makes the OCR look worse than it is, which is the error that
    already happened once.
    """
    if len(span.split()) < MIN_WORDS:
        return False
    if span.lstrip()[:1] in ",;:)" or span.startswith(" "):
        return False
    # commentary tells; documents state
    for tell in ("⚠", "TWICE MORE", "I ", "my ", "note that", "which means"):
        if tell in span:
            return False
    return True


def load(path="claims.py"):
    """-> {(doc_id, page_int): [verbatim, ...]}"""
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    out = collections.defaultdict(list)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "C"):
            continue
        args = node.args
        if len(args) < 3:
            continue
        try:
            doc = ast.literal_eval(args[1])
            pg = ast.literal_eval(args[2])
        except Exception:
            continue
        if not isinstance(pg, str) or not re.fullmatch(r"p\d+", pg):
            continue
        for kw in node.keywords:
            if kw.arg != "text":
                continue
            try:
                val = ast.literal_eval(kw.value)
            except Exception:
                continue
            for s in _quoted_spans(val):
                if _plausible(s):
                    out[(doc, int(pg[1:]))].append(s)
    return dict(out)


if __name__ == "__main__":
    gt = load()
    n = sum(len(v) for v in gt.values())
    print(f"{n} verbatim spans across {len(gt)} (document, page) pairs")
    docs = {d for d, _ in gt}
    print(f"{len(docs)} documents, {sum(1 for d in docs if d.startswith('FT_'))} microfilm")
    for k in list(gt)[:4]:
        print(f"\n  {k}")
        for s in gt[k][:2]:
            print(f"    {s[:150]}")
