"""THE COVER PAGE STATES ITS OWN PAGE COUNT. Recover it, and fix the map.

    PAGE 1 OF 38               total pages, covers included
    Document Page Count: 36    the instrument alone
                            -> 2 cover pages

⚠ THE MAP CANNOT ANSWER THIS AND NEVER WILL. hid_Cov is 0 for all 16,875,600
documents because that is what the ACRIS form returns — not because the cover
pages are absent. Document 2012122701923005 plainly has two of them and the map
records instrument [1,38] / 38 pages. So instrument_pages is an UPPER BOUND
across the whole corpus, over-counting by however many cover sheets exist.

⚠ WHICH ALSO MEANS EVERY PAGE-BASED COST ESTIMATE IS HIGH. 133,988,962
instrument pages includes cover sheets. If the modern era carries ~2 each, that
is millions of pages counted as instrument that are really index.

This measures, on the 537 documents already OCR'd, how often the cover page
states its own count — i.e. how often the fix is available for free.

⚠ AND IT REPORTS WHAT IT COULD NOT READ, NOT JUST WHAT IT COULD. A recovery
rate quoted without its denominator is the failure this project keeps meeting:
the film era is 37% of the sample and if it recovers 0% that must be visible in
the headline, not buried.

    python cover_truth.py
"""
import collections
import gzip
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OCR = pathlib.Path("sample_ocr")
MAPS = ("acris_maps.jsonl", "docmaps.jsonl")

# ⚠ LOOSE ON PUNCTUATION, TIGHT ON SHAPE. OCR turns ':' into ';' and '.' and
# drops spaces; it rarely invents digits in a short isolated field.
RX_OF = re.compile(r"PAGE\s*1\s*OF\s*(\d{1,4})", re.I)
RX_CNT = re.compile(r"Document\s*Page\s*Count\s*[:;.]?\s*(\d{1,4})", re.I)
RX_DID = re.compile(r"Document\s*ID\s*[:;.]?\s*(\d{10,16})", re.I)
RX_TYPE = re.compile(r"Document\s*Type\s*[:;.]?\s*([A-Z][A-Z &/,\-]{2,40})")


def mapped():
    out = {}
    for name in MAPS:
        p = pathlib.Path(name)
        if not p.exists():
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"doc_id"' not in line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("hid_TotalPages"):
                    out[r["doc_id"]] = r
    return out


def main():
    MAP = mapped()
    docs = sorted(p.name[:-8] for p in OCR.glob("*.json.gz"))
    print(f"  {len(docs)} documents with OCR\n")

    era = lambda d: "film" if d.startswith("FT_") else "modern"
    n = collections.Counter()
    got_of = collections.Counter()
    got_cnt = collections.Counter()
    both = collections.Counter()
    covers = collections.Counter()
    mismatch = []

    for d in docs:
        n[era(d)] += 1
        try:
            rows = json.load(gzip.open(OCR / f"{d}.json.gz", "rt", encoding="utf-8"))
        except Exception:
            continue
        first = min(rows, key=lambda r: r["page"], default=None)
        if not first:
            continue
        text = " ".join(w["t"] for w in first["words"])

        m_of, m_cnt = RX_OF.search(text), RX_CNT.search(text)
        if m_of:
            got_of[era(d)] += 1
        if m_cnt:
            got_cnt[era(d)] += 1
        if m_of and m_cnt:
            both[era(d)] += 1
            tot, inst = int(m_of.group(1)), int(m_cnt.group(1))
            cov = tot - inst
            covers[cov] += 1
            mp = MAP.get(d)
            # ⚠ CROSS-CHECK AGAINST THE MAP. If the page's own total disagrees
            # with hid_TotalPages, one of them is misread and the claim is not
            # safe to use. Report it rather than picking a winner.
            if mp and mp.get("hid_TotalPages") != tot:
                mismatch.append((d, tot, mp["hid_TotalPages"], inst))

    print(f"  {'era':<9}{'docs':>7}{'PAGE 1 OF n':>14}{'Page Count':>13}{'BOTH':>9}")
    for e in ("modern", "film"):
        if not n[e]:
            continue
        print(f"  {e:<9}{n[e]:>7}{got_of[e]:>13,} {got_cnt[e]:>12,}{both[e]:>9,}")
    tot_both = sum(both.values())
    print(f"  {'ALL':<9}{sum(n.values()):>7}{sum(got_of.values()):>13,} "
          f"{sum(got_cnt.values()):>12,}{tot_both:>9,}"
          f"   = {tot_both/max(sum(n.values()),1)*100:.1f}% recoverable")

    print(f"\n  ── COVER PAGES PER DOCUMENT (total - stated instrument) ──")
    for c, k in sorted(covers.items()):
        flag = "  ⚠ negative — a misread, not a document" if c < 0 else ""
        print(f"    {c:>3} cover pages   {k:>5} documents{flag}")

    if mismatch:
        print(f"\n  ⚠ {len(mismatch)} documents where the PAGE'S OWN TOTAL "
              f"disagrees with hid_TotalPages")
        for d, tot, mt, inst in mismatch[:10]:
            print(f"      {d}  page says {tot}, map says {mt}, instrument {inst}")

    print(f"\n  ⚠ film recovery is the number that matters — those pages have no "
          f"cover\n    sheet at all, so a low rate there is correct, not a failure.")


if __name__ == "__main__":
    main()
