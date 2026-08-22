"""1.3% OF PHRASES IS THE WRONG NUMBER. What matters is 1.3% of WHAT?

⚠ A PHRASE IS NOT A CLAIM AND LOSING ONE IS USUALLY FREE. A document that
transfers development rights says "development rights" in the recital, in the
definition, in the granting clause, in the exhibit and in the acknowledgment.
Tesseract mangling one of them costs nothing — the frame still fires on the
other four, the crop is still made, the claim is still seen.

So the phrase-level rate OVERSTATES the damage, possibly by a lot. The number
that decides whether a claim is lost is:

    of the documents that contain a frame at all,
    how many lose EVERY instance of it?

That is the only miss that is silent and unrecoverable. Everything else is
redundancy doing its job.

⚠ AND THE OPPOSITE ERROR IS ALSO POSSIBLE. If a frame appears exactly once in
most documents that have it, then redundancy is NOT there and 1.3% of phrases
really is 1.3% of claims. So this reports the redundancy distribution too —
without it, the headline is unfalsifiable.

    python loss_that_matters.py
"""
import collections
import gzip
import json
import pathlib
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from scanner_cost import (FRAMES, LEX, build_lexicon, classify, lev1, norm,
                          variants)

OCR = pathlib.Path("sample_ocr")


def main():
    docs = sorted(OCR.glob("*.json.gz"))
    lex = build_lexicon(docs)
    targets = [variants(rx) for _, rx in FRAMES]

    # per document per frame: how many CLEAN instances, how many DAMAGED
    clean = collections.defaultdict(collections.Counter)   # frame -> doc -> n
    dirty = collections.defaultdict(collections.Counter)

    for p in docs:
        d = p.name[:-8]
        try:
            rows = json.load(gzip.open(p, "rt", encoding="utf-8"))
        except Exception:
            continue
        for r in rows:
            ws = r["words"]
            toks = [norm(w["t"]) for w in ws]
            for (lab, _), seqs in zip(FRAMES, targets):
                seen = set()
                for s in seqs:
                    k = len(s)
                    for i in range(len(toks) - k + 1):
                        if i in seen:
                            continue
                        if not all(lev1(toks[i + j], s[j]) for j in range(k)):
                            continue
                        seen.add(i)
                        got = [ws[i + j]["t"] for j in range(k)]
                        if tuple(norm(g) for g in got) in seqs:
                            clean[lab][d] += 1
                            continue
                        c = classify(got, seqs)
                        if c == "ocr" and all(norm(g) in lex for g in got):
                            continue                     # noise, not a hit at all
                        if c == "ocr":
                            dirty[lab][d] += 1
                        else:
                            clean[lab][d] += 1           # punct/morph — recoverable

    print(f"  {len(docs)} documents\n")
    print(f"  {'frame':<22}{'docs w/ it':>11}{'median n':>10}{'once only':>11}"
          f"{'LOST ALL':>10}")
    tot_docs = tot_lost = 0
    lost_rows = []
    for lab, _ in FRAMES:
        have = set(clean[lab]) | set(dirty[lab])
        if not have:
            continue
        counts = [clean[lab][d] + dirty[lab][d] for d in have]
        once = sum(1 for c in counts if c == 1)
        # ⚠ THE ONLY REAL LOSS: damaged instances exist and clean ones do not.
        lost = [d for d in have if dirty[lab][d] and not clean[lab][d]]
        tot_docs += len(have); tot_lost += len(lost)
        lost_rows += [(lab, d) for d in lost]
        print(f"  {lab:<22}{len(have):>11}{statistics.median(counts):>10.0f}"
              f"{once:>10}{'':>1}{len(lost):>10}")
    print(f"  {'ALL':<22}{tot_docs:>11}{'':>10}{'':>11}{tot_lost:>10}")

    print(f"\n  ── THE TWO NUMBERS SIDE BY SIDE ──")
    print(f"    phrase-level loss    1.3%   50 mangled instances of 3,946")
    print(f"    DOCUMENT-level loss  {tot_lost/max(tot_docs,1)*100:.2f}%   "
          f"{tot_lost} of {tot_docs} document-frame pairs lost entirely")

    if lost_rows:
        print(f"\n  ── WHAT WAS ACTUALLY LOST ──")
        for lab, d in lost_rows[:15]:
            print(f"    {d:<22}{lab}")

    print(f"\n  ⚠ REDUNDANCY IS THE WHOLE REASON FOR THE GAP. Check the 'once only'")
    print(f"    column: frames that appear exactly once have no second chance, and")
    print(f"    for those the phrase rate IS the claim rate.")


if __name__ == "__main__":
    main()
