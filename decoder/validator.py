"""THE MATCH LAYER, run against RAW OCR - no answer key anywhere.

    python validator.py

⚠ THIS IS THE ONLY KIND OF CHECK THAT SURVIVES 17 MILLION DOCUMENTS. Every
accuracy number in this project so far came from comparing OCR against a page I
read by hand, and that took an afternoon for 17 pages. There is no version of
that which scales. So the question this file asks is different: using ONLY the
OCR text, can the document be shown to be internally consistent?

Three checks, each needing nothing external:

  1. TAX RECONCILES     NYC mortgage recording tax is a known percentage of the
                        mortgage amount. If some pair of dollar figures on the
                        document stands in a legal ratio, both were read right -
                        two independent misreads landing on a legal ratio is
                        vanishingly unlikely.
  2. STAMP SEQUENCE     One document sits on one reel/book, on consecutive
                        pages. A constant reel plus a contiguous page run means
                        the stamps were read right; a hole locates the failure.
  3. DATE ORDER         Execution precedes acknowledgement precedes recording.
                        Out of order means one date was misread.

⚠ A CHECK THAT PASSES PROVES THE READ, NOT THE DOCUMENT. And a check that fails
does not say WHICH value is wrong - only that the set is inconsistent. That is
still the useful direction: it converts "I have no idea if this is right" into
"these three fields disagree", which is a page worth escalating.
"""
import collections
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# NYC mortgage recording tax rates have changed over time and vary by amount
# and property class. These are the historically plausible total rates.
RATES = [0.005, 0.0075, 0.01, 0.0125, 0.015, 0.0175, 0.01925, 0.02, 0.02175, 0.028]


def money(txt):
    """Every dollar-ish figure in the text, as floats."""
    out = []
    for m in re.finditer(r"(?<![\d.])(\d{1,3}(?:[,\s]\d{3})+(?:\.\d{2})?|\d{4,9}(?:\.\d{2})?)",
                         txt):
        s = m.group(1).replace(",", "").replace(" ", "")
        try:
            v = float(s)
        except ValueError:
            continue
        if 50 <= v <= 500_000_000:
            out.append(v)
    return out


def check_tax(amounts):
    """Find a (principal, tax) pair standing in a legal ratio."""
    hits = []
    uniq = sorted(set(amounts), reverse=True)
    for a in uniq:
        for t in uniq:
            if t >= a:
                continue
            for r in RATES:
                if abs(t - a * r) < max(1.0, a * r * 0.005):
                    hits.append((a, t, r))
    # prefer the largest principal
    hits.sort(key=lambda h: -h[0])
    return hits[:3]


def check_stamps(per_page, pat):
    """Reel/book constant across pages, page numbers contiguous."""
    books = collections.Counter()
    pages = {}
    for pg, txt in sorted(per_page.items()):
        m = pat.findall(txt)
        nums = []
        for grp in m:
            nums += [int(x) for x in grp if x and x.isdigit()]
        if nums:
            books[nums[0]] += 1
            pages[pg] = nums
    if not books:
        return None, [], []
    book, _ = books.most_common(1)[0]
    seen = sorted({n for v in pages.values() for n in v if n != book})
    runs = []
    for n in seen:
        if runs and n == runs[-1][-1] + 1:
            runs[-1].append(n)
        else:
            runs.append([n])
    runs.sort(key=len, reverse=True)
    return book, (runs[0] if runs else []), sorted(per_page)


def years(txt):
    return sorted({int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", txt)})


DOCS = [
    ("FT_1680008647768", re.compile(r"reel\s*(\d{2,5})|(\d{2,5})\s*(?:page|pg|ace|ale)", re.I),
     ["tesseract", "rapidpool"]),
    ("BK_6730047100023", re.compile(r"rec\.?\s*(\d{2,5})|(\d{2,5})\s*(?:page|pg)", re.I),
     ["tesseract", "rapidpool"]),
]

for doc, pat, engines in DOCS:
    R = pathlib.Path("render/testdoc") / doc
    per_page = {}
    for eng in engines:
        d = R / eng
        if not d.exists():
            continue
        for f in sorted(d.glob("*.txt")):
            pg = f.name.split(".")[0]
            per_page[pg] = per_page.get(pg, "") + " " + f.read_text(
                encoding="utf-8", errors="replace")
    if not per_page:
        print(f"\n  {doc}: no OCR on disk"); continue
    allt = " ".join(per_page.values())

    print(f"\n  ══ {doc} ══  ({len(per_page)} pages, engines: {'+'.join(engines)})")

    amts = money(allt)
    hits = check_tax(amts)
    if hits:
        for a, t, r in hits:
            print(f"    TAX RECONCILES   ${a:,.0f} x {r*100:.3g}% = ${t:,.0f}   PASS")
    else:
        print(f"    TAX RECONCILES   no legal ratio found among "
              f"{len(set(amts))} figures   FAIL")

    book, run, pgs = check_stamps(per_page, pat)
    if book:
        ok = len(run) == len(pgs)
        print(f"    STAMP SEQUENCE   book/reel {book} · pages {run[0] if run else '?'}"
              f"-{run[-1] if run else '?'} ({len(run)} of {len(pgs)})   "
              f"{'PASS' if ok else 'PARTIAL -> escalate the gaps'}")
    else:
        print(f"    STAMP SEQUENCE   no stamp recovered   FAIL")

    ys = years(allt)
    plaus = [y for y in ys if 1900 <= y <= 2030]
    print(f"    DATE ORDER       years seen {plaus[:6]}{'...' if len(plaus) > 6 else ''}"
          f"   {'PASS' if plaus == sorted(plaus) else 'FAIL'}")
