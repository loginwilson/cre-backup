"""WHICH PAGES DO WE ACTUALLY HAVE TO TOGGLE TO? Measured, not assumed.

Page 1 carries the recording facts and nothing else. Fetching all 7.86
instrument pages carries everything and costs 8x. Between those is a POLICY:
fetch page 1, read it, and toggle to the pages that are likely to matter.

That policy is only worth having if claim-bearing pages sit in PREDICTABLE
POSITIONS. This measures whether they do, from the 4,271 pages already OCR'd —
no network, no ACRIS, no refusal risk.

⚠ IT MEASURES POSITION, NOT PRESENCE OF A CLAIM. A page containing the word
EXHIBIT is a page worth looking at; it is not a claim. Every number here is
"where should I look", and looking is what the crop is for.

⚠ POSITIONS ARE WITHIN THE INSTRUMENT RANGE, NOT THE DOCUMENT. Only instrument
pages were ever fetched, so "last" means last page of the instrument. That is
the right frame: supporting documents and tax returns are separately indexed
(hid_Sup / hid_Tax) and are not pages of this thing at all.

    python page_policy.py
"""
import collections
import gzip
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OCR = pathlib.Path("sample_ocr")
IDS = pathlib.Path("acris_ids.jsonl")

# ⚠ TRIGGERS ARE FOR LOCATING, SO THEY ARE DELIBERATELY LOOSE. OCR mangles
# body text; these have to survive that. A tight pattern that only matches
# clean text measures OCR quality, not page position.
SIGNALS = {
    "TAXSTAMP": re.compile(r"RPTT|RETT|REAL PROPERTY TRANSFER|NYC-?RPT|TRANSFER TAX", re.I),
    "MONEY": re.compile(r"\$\s?[\d,]{4,}"),
    "EXHIBIT": re.compile(r"\bEXHIBIT\b|\bSCHEDULE\s+[A-E]\b", re.I),
    "EXECUTION": re.compile(r"IN WITNESS WHEREOF|ACKNOWLEDG|NOTARY", re.I),
    "PARCEL": re.compile(r"\bBLOCK\b.{0,20}\bLOT\b", re.I | re.S),
    "SECTION": re.compile(r"\bSection\s+\d+\.\d+|\bARTICLE\s+[IVX\d]", re.I),
    "SQFT": re.compile(r"square\s+feet|sq\.?\s?ft|\bZFA\b|floor area", re.I),
}


def types():
    out = {}
    with open(IDS, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            i, j = line.find('"document_id": "'), line.find('"doc_type": "')
            if i < 0 or j < 0:
                continue
            out[line[i + 16:line.find('"', i + 16)]] = line[j + 13:line.find('"', j + 13)]
    return out


def main():
    TYPE = types()
    docs = sorted(p.name[:-8] for p in OCR.glob("*.json.gz"))
    print(f"  {len(docs)} documents with OCR on disk\n")

    # position buckets, and the policies we want to score
    POS = collections.defaultdict(collections.Counter)   # signal -> bucket
    hits = collections.Counter()                          # signal -> pages
    covered = collections.defaultdict(collections.Counter)  # policy -> signal
    total = collections.Counter()                         # signal -> docs having it
    npages = []

    for d in docs:
        try:
            rows = json.load(gzip.open(OCR / f"{d}.json.gz", "rt", encoding="utf-8"))
        except Exception:
            continue
        if not rows:
            continue
        pages = sorted(r["page"] for r in rows)
        lo, hi = pages[0], pages[-1]
        n = hi - lo + 1
        npages.append(n)
        text = {r["page"]: " ".join(w["t"] for w in r["words"]) for r in rows}

        for sig, rx in SIGNALS.items():
            on = [p for p, t in text.items() if rx.search(t)]
            if not on:
                continue
            total[sig] += 1
            hits[sig] += len(on)
            for p in on:
                # bucket by position within the instrument
                if p == lo:
                    POS[sig]["first"] += 1
                elif p == hi:
                    POS[sig]["last"] += 1
                elif p == hi - 1:
                    POS[sig]["last-1"] += 1
                elif p == lo + 1:
                    POS[sig]["second"] += 1
                else:
                    POS[sig]["middle"] += 1
            # ⚠ SCORE BY DOCUMENT, NOT BY PAGE. A policy that finds the signal
            # SOMEWHERE in the document has done its job; counting pages would
            # reward policies that fetch more for no extra information.
            S = set(on)
            for pol, keep in (("first", {lo}),
                              ("first+last", {lo, hi}),
                              ("first+last2", {lo, hi, hi - 1}),
                              ("first2+last2", {lo, lo + 1, hi, hi - 1}),
                              ("all", set(range(lo, hi + 1)))):
                if S & keep:
                    covered[pol][sig] += 1

    avg = sum(npages) / max(len(npages), 1)
    print(f"  mean instrument pages in sample: {avg:.1f}\n")

    print(f"  ── WHERE EACH SIGNAL SITS (share of pages carrying it) ──")
    print(f"  {'signal':<11}{'docs':>6}{'pages':>7}"
          + "".join(f"{b:>9}" for b in ("first", "second", "middle", "last-1", "last")))
    for sig in SIGNALS:
        t = sum(POS[sig].values())
        if not t:
            continue
        print(f"  {sig:<11}{total[sig]:>6}{hits[sig]:>7}"
              + "".join(f"{POS[sig][b]/t*100:>8.0f}%"
                        for b in ("first", "second", "middle", "last-1", "last")))

    print(f"\n  ── POLICY: share of documents where the signal is REACHED ──")
    POLS = ("first", "first+last", "first+last2", "first2+last2", "all")
    cost = {"first": 1.0, "first+last": 2.0, "first+last2": 3.0,
            "first2+last2": 4.0, "all": avg}
    print(f"  {'policy':<14}{'pages/doc':>10}" + "".join(f"{s:>10}" for s in SIGNALS))
    for pol in POLS:
        print(f"  {pol:<14}{cost[pol]:>10.1f}"
              + "".join(f"{covered[pol][s]/max(total[s],1)*100:>9.0f}%" for s in SIGNALS))

    print(f"\n  ⚠ 'reached' means the page was fetched, not that a claim was read.")
    print(f"    Cost is pages per document; 'all' is the sample mean of {avg:.1f}.")


if __name__ == "__main__":
    main()
