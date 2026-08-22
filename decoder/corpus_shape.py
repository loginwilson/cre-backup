"""WHERE THE PAGES ACTUALLY ARE — the number that decides what is extractable.

The map cost days to build and it already answers a strategic question nobody
has asked it: extraction cost scales with PAGES, not documents, and pages are
not spread evenly across the 95 types. If a small number of types hold most of
the pages, then "can we extract at scale" is really "can we extract THOSE".

It also measures the cover-page lever. A cover page is one page carrying the
RPTT and RETT stamps — which is where a deed's true price lives, the $10
recital on the instrument being a 500,000x trap. If the high-volume types only
need their cover page, the page count collapses and the cost model changes
shape entirely.

⚠ READS THE MAP, ASKS ACRIS NOTHING. No network, no lock, no refusal risk.

    python corpus_shape.py
"""
import collections
import json
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAPS = ("acris_maps.jsonl", "docmaps.jsonl", "census_maps.jsonl")


def main():
    t0 = time.time()
    docs = collections.Counter()        # doc_type -> documents
    inst = collections.Counter()        # doc_type -> instrument pages
    tot = collections.Counter()         # doc_type -> total pages
    cov = collections.Counter()         # doc_type -> documents WITH a cover page
    covp = collections.Counter()        # doc_type -> cover pages
    noimg = collections.Counter()
    seen = set()

    for name in MAPS:
        p = pathlib.Path(name)
        if not p.exists():
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                d = r.get("doc_id")
                if not d or d in seen:      # ⚠ dedupe: the three files overlap
                    continue
                seen.add(d)
                t = r.get("doc_type") or "?"
                docs[t] += 1
                n = r.get("hid_TotalPages")
                if n is None or n <= 0:
                    noimg[t] += 1
                    continue
                tot[t] += n
                inst[t] += r.get("instrument_pages") or 0
                c = r.get("hid_Cov") or 0
                if c:
                    cov[t] += 1
                    covp[t] += c

    D, I, T, C = sum(docs.values()), sum(inst.values()), sum(tot.values()), sum(covp.values())
    print(f"  {D:,} documents · {T:,} pages · {I:,} instrument pages  "
          f"({time.time()-t0:.0f}s)\n")

    print(f"  {'type':<9}{'docs':>12}{'inst pages':>14}{'% inst':>8}"
          f"{'pg/doc':>8}{'cover pg':>10}{'cum %':>8}")
    print("  " + "-" * 69)
    cum = 0
    for t, _ in inst.most_common(18):
        cum += inst[t]
        print(f"  {t:<9}{docs[t]:>12,}{inst[t]:>14,}{inst[t]/I*100:>7.1f}%"
              f"{inst[t]/max(docs[t]-noimg[t],1):>8.1f}{covp[t]:>10,}"
              f"{cum/I*100:>7.1f}%")

    print(f"\n  ── THE COVER-PAGE LEVER ──")
    print(f"  instrument pages, every document      {I:>14,}")
    print(f"  cover pages only                      {C:>14,}   "
          f"{C/I*100:.1f}% of the work")
    print(f"  documents that HAVE a cover page      {sum(cov.values()):>14,}   "
          f"{sum(cov.values())/D*100:.1f}%")

    # ⚠ THE SIGNAL TYPES. Tiny, and that is the point — they are extractable
    # today at any price, because the price is multiplied by almost nothing.
    print(f"\n  ── HIGH-SIGNAL, LOW-VOLUME ──")
    print(f"  {'type':<9}{'docs':>10}{'inst pages':>13}{'hours OCR':>12}")
    for t in ("DEVR", "AIRRIGHT", "ZONE", "EASE", "RCVN", "AGMT"):
        if t in docs:
            print(f"  {t:<9}{docs[t]:>10,}{inst[t]:>13,}"
                  f"{inst[t]/13148:>12.1f}")

    print(f"\n  ── WHAT 'AT SCALE' COSTS IN OCR ──   (measured 13,148 pg/hr)")
    for label, pages in (("every instrument page", I), ("cover pages only", C)):
        hrs = pages / 13148
        print(f"  {label:<24}{pages:>14,} pages   {hrs:>9,.0f} core-hr   "
              f"{hrs/720:>6.1f} core-months")
    print(f"\n  ⚠ OCR is the CHEAP term. The LLM read is the one that is "
          f"unmeasured,\n    and it scales with pages too.")


if __name__ == "__main__":
    main()
