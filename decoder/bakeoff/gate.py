"""DOES THE GATE ACTUALLY CATCH TIER-1 FAILURES? The confusion matrix.

    python gate.py [engine[,engine...]]      default tesseract,rapidpool

⚠ THE WHOLE 2-TIER DESIGN RESTS ON A CLAIM THAT HAS NEVER BEEN SHOWN AS A
MATRIX. "The validators caught 14/14 real failures" has been quoted all session
as though it settles whether Tier 1 can be trusted. It does not, because recall
on a hand-picked set of known failures says nothing about the two numbers that
actually matter at 148M pages:

  FALSE NEGATIVE  the page IS wrong and the gate says PASS.
                  This is the only truly dangerous outcome. It is a silent
                  error that flows into lineage, and at corpus scale nobody
                  will ever look at the page again.

  FALSE POSITIVE  the page is FINE and the gate says FAIL.
                  Costs money - an unnecessary Tier-2 call - and nothing else.
                  Every false positive is a page escalated for no reason, which
                  is exactly the "gate firing rate" that prices the design.

⚠ AND THE GATE IS STRUCTURALLY PARTIAL, WHICH IS THE POINT OF MEASURING IT.
It asks "is the reel/record stamp present" and "is there a cover page". It
cannot ask "is the mortgagee's name right", because there is nothing to check a
name against. So it should be expected to miss whole categories of failure, and
this file exists to quantify how big that blind spot is rather than to discover
that it exists.

⚠ TRUTH HERE IS THE ANSWER KEY, WHICH IS WHY THIS CAN ONLY RUN ON 3 DOCUMENTS.
The gate itself needs no key - that is its virtue and why it scales. Measuring
the gate needs one. So this is a small, honest calibration of a cheap detector,
not a corpus-wide result, and n=21 pages should be read as directional.
"""
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import score as S
from report import KEYS, text

HERE = pathlib.Path(__file__).parent


def cls(doc):
    return "film" if doc.startswith("FT_") else "book" if doc.startswith("BK_") else "digital"


def gate_fires(doc, raw, doc_raw=None):
    """TRUE = escalate. Key-free: only looks at the OCR text and the doc_id.

    ⚠ MATCHED ON NORMALISED TEXT AND REQUIRING DIGITS. The label alone is
    worthless - every film page in the corpus says REEL. What makes the stamp a
    join key is the NUMBER, so a page carrying the word without a number has
    not surfaced the artifact and must escalate.

    ⚠ TWO FIXES AFTER THE FIRST MEASUREMENT, BOTH OF WHICH WERE MY BUGS RATHER
    THAN THE GATE'S LIMITS - and both inflated the false-alarm rate, which would
    have made a usable detector look unusable:

      1. `reel \d` required the number to be the NEXT token. Real reads are
         `REEL / PAGE: 371 PAGE 656` and `REEL 586 PAGE 761`, so up to a couple
         of tokens can sit between the label and its number.
      2. The digital check ran PER PAGE. Only the ACRIS COVER PAGE carries the
         16-digit Document ID; body pages never do and never could. Asking every
         page for it escalated 3 of 4 digital pages for a fact that is not on
         them. It is a per-DOCUMENT check and is now evaluated that way.
    """
    hay = S.norm(raw)
    k = cls(doc)
    if k == "film":
        return not re.search(r" reel (?:\w+ ){0,3}?\d", hay)
    if k == "book":
        return not re.search(r" (?:rec|record|liber) (?:\w+ ){0,3}?\d", hay)
    # digital: per DOCUMENT, not per page - only the cover page carries the ID
    d = S.norm(doc_raw if doc_raw is not None else raw)
    return not re.search(r" \d{16} ", d) and not re.search(r" crfn (?:\w+ ){0,2}?\d", d)


def main():
    engs = (sys.argv[1] if len(sys.argv) > 1 else "tesseract,rapidpool").split(",")
    docs = []
    for doc, kf, label, share in KEYS:
        p = HERE / "keys" / kf
        if not p.exists():
            continue
        key = {k: v for k, v in json.loads(p.read_text(encoding="utf-8")).items()
               if not k.startswith("_")}
        docs.append((doc, key, label, share))

    print(f"  Tier 1 = {'+'.join(engs)}\n")
    TP = FP = TN = FN = 0
    fn_rows, fp_rows = [], []
    per = {}
    for doc, key, label, _ in docs:
        t = f = tn = fn = 0
        doc_raw = " ".join(text(e, doc, pg) for pg in key for e in engs)
        for page in key:
            raw = " ".join(text(e, doc, page) for e in engs)
            hay = S.norm(raw)
            crit = [a for a in key[page]["artifacts"] if a["tier"] == "CRITICAL"]
            missed = [a for a in crit if not S.found(hay, a)]
            bad = bool(missed)                    # truth: page has a wrong fact
            fired = gate_fires(doc, raw, doc_raw)  # prediction
            if bad and fired:
                TP += 1; t += 1
            elif bad and not fired:
                FN += 1; fn += 1
                fn_rows.append((label, page, len(missed), len(crit),
                                [a["id"] for a in missed][:5]))
            elif not bad and fired:
                FP += 1; f += 1
                fp_rows.append((label, page))
            else:
                TN += 1; tn += 1
        per[label] = (t, fn, f, tn)

    n = TP + FP + TN + FN
    print(f"  {'document':<15}{'caught':>8}{'MISSED':>8}{'false al':>10}{'clean':>8}")
    print("  " + "-" * 49)
    for label, (t, fn, f, tn) in per.items():
        print(f"  {label:<15}{t:>8}{fn:>8}{f:>10}{tn:>8}")
    print(f"  {'TOTAL':<15}{TP:>8}{FN:>8}{FP:>10}{TN:>8}   n={n} pages\n")

    bad = TP + FN
    print(f"  pages with at least one wrong CRITICAL fact : {bad}/{n}")
    print(f"  of those, the gate caught                   : {TP}/{bad}"
          f"{'  (' + str(round(TP/bad*100)) + '%)' if bad else ''}")
    print(f"  SILENT FAILURES (wrong, gate said pass)     : {FN}/{n}"
          f"  <-- the number that matters")
    print(f"  escalation rate (gate fires)                : {(TP+FP)}/{n}"
          f"  = {(TP+FP)/n*100:.0f}% of pages -> Tier 2")

    if fn_rows:
        print(f"\n  ── SILENT FAILURES: wrong facts the gate cannot see ──")
        for label, page, nm, nc, ids in fn_rows:
            print(f"    {label:<14}{page:<11}{nm}/{nc} missed  {', '.join(ids)}")
    if fp_rows:
        print(f"\n  ── FALSE ALARMS: escalated for nothing ({len(fp_rows)}) ──")
        for label, page in fp_rows[:10]:
            print(f"    {label:<14}{page}")

    print(f"\n  ⚠ THE GATE ONLY ASKS 'IS THE STAMP THERE'. It has no way to ask")
    print(f"    'is this name right', so every silent failure above is a whole")
    print(f"    CATEGORY of error it is blind to, not a tuning problem. Read the")
    print(f"    silent-failure list for what those categories are.")


if __name__ == "__main__":
    main()
