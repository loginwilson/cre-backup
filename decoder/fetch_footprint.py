"""HOW FEW PAGES CAN WE FETCH? The number that decides whether streaming works.

Reading every instrument page means 134M fetches. But a claim does not live on
every page — the price lives on the RPTT/RETT stamps, and the map already
records which page carries the tax return. If that page is known per document,
then the price of a deed costs ONE fetch, not 3.9.

This measures the footprint of four strategies against the real map:

    ALL          every instrument page                   the naive baseline
    FIRST        page 1 only                             parties, date, grant
    TAX          the tax-return page only                the price stamps
    FIRST+TAX    both                                    the practical minimum

⚠ READS THE MAP, ASKS ACRIS NOTHING. No network, no lock, no refusal risk.

⚠ AND IT JOINS doc_type FROM THE INDEX, NOT FROM THE MAP. amap.parse() writes no
doc_type field at all, so the 68,548 documents in docmaps.jsonl carry none —
reading the type off the map reported DEVR as 13 documents when the index says
1,198. Any per-type number sourced from the map alone is wrong by construction.

    python fetch_footprint.py
"""
import collections
import json
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAPS = ("acris_maps.jsonl", "docmaps.jsonl", "census_maps.jsonl")
IDS = pathlib.Path("acris_ids.jsonl")


def doc_types():
    """document_id -> doc_type, from the INDEX. See the warning above."""
    out = {}
    with open(IDS, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            i = line.find('"document_id": "')
            j = line.find('"doc_type": "')
            if i < 0 or j < 0:
                continue
            d = line[i + 16:line.find('"', i + 16)]
            out[d] = line[j + 13:line.find('"', j + 13)]
    return out


def main():
    t0 = time.time()
    TYPE = doc_types()
    print(f"  {len(TYPE):,} document types loaded from the index "
          f"({time.time()-t0:.0f}s)\n")

    seen = set()
    n_img = 0
    has_tax = 0
    has_sup = 0
    pages = collections.Counter()          # strategy -> pages
    per_type = collections.defaultdict(lambda: [0, 0, 0])   # docs, all, first+tax

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
                if not d or d in seen:
                    continue
                seen.add(d)
                tot = r.get("hid_TotalPages")
                if tot is None or tot <= 0:
                    continue                # no image exists; index is all there is
                n_img += 1

                inst = r.get("instrument_pages") or 0
                tax = r.get("tax_return")
                sup = r.get("supporting")
                if tax:
                    has_tax += 1
                if sup:
                    has_sup += 1

                # ⚠ FIRST+TAX must not double-count when the tax page IS page 1.
                ft = 1 + (1 if (tax and tax != 1) else 0)
                pages["ALL"] += inst
                pages["FIRST"] += 1
                pages["TAX"] += 1 if tax else 0
                pages["FIRST+TAX"] += ft

                t = TYPE.get(d, "?")
                per_type[t][0] += 1
                per_type[t][1] += inst
                per_type[t][2] += ft

    print(f"  {n_img:,} documents WITH an image\n")
    print(f"  have a tax-return page   {has_tax:>12,}   {has_tax/n_img*100:5.1f}%")
    print(f"  have supporting docs     {has_sup:>12,}   {has_sup/n_img*100:5.1f}%\n")

    base = pages["ALL"]
    print(f"  {'strategy':<12}{'pages to fetch':>18}{'vs ALL':>10}{'TB @66,855 B':>15}")
    print("  " + "-" * 55)
    for k in ("ALL", "FIRST", "TAX", "FIRST+TAX"):
        v = pages[k]
        print(f"  {k:<12}{v:>18,}{v/base*100:>9.1f}%{v*66855/1e12:>14.2f}")

    print(f"\n  ── BY TYPE, the ten heaviest ──")
    print(f"  {'type':<9}{'docs':>11}{'all pages':>13}{'first+tax':>12}{'cut':>8}")
    for t, (n, a, ft) in sorted(per_type.items(), key=lambda x: -x[1][1])[:10]:
        print(f"  {t:<9}{n:>11,}{a:>13,}{ft:>12,}{(1-ft/max(a,1))*100:>7.0f}%")

    print(f"\n  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
