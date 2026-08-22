"""THE COMPLETENESS PASS — read what NOTHING claims, ranked by how often it recurs.

    python completeness.py                 # devr_text/, cover vs body
    python completeness.py --dir devr_text_rot90
    python completeness.py --show 60       # deeper lists

⚠ THIS EXISTS BECAUSE EVERY OTHER MEASUREMENT IN THIS PROJECT SCORES WHAT I
ALREADY THOUGHT OF. Coverage counts say "envelope fired 21/25" — they cannot say
"and the cover page carried both BBLs, the property type, and the RETT stamp,
none of which any pattern targets." A recall metric is blind to the fields that
were never candidates. On 2026-08-14 page 1 of three documents was read by eye
and yielded six unmodelled fields; that is not a method, it is luck. This is the
method.

⚠ THE OPERATION IS SUBTRACTION, NOT SEARCH. Every pattern in lexicon.py,
claim_read.py and roles.py is run over the accepted text and each match MARKS its
characters. What is left is, by construction, everything the system cannot see.
Searching for what is missing requires already knowing it; subtracting does not.

⚠ RANK BY DOCUMENT FREQUENCY, NOT BY COUNT. A phrase repeated 200 times inside
one instrument is that draftsman's habit. A phrase appearing once in 24 of 25
documents is the document TYPE's structure, and that is what earns a pattern.
Ranking by raw count surfaces the longest document; ranking by df surfaces the
grammar.

⚠ COVER AND BODY ARE COUNTED SEPARATELY OR THE COVER DISAPPEARS. ACRIS's wrapper
is one page in a 37-page instrument — under 3% of the characters. Pooled with the
body its labels never clear a frequency threshold, which is precisely how the
RETT stamp stayed invisible while sitting on page 1 of all 25 documents.

⚠ AN UNCLAIMED NUMBER IS THE SHARPEST SIGNAL HERE. Prose can be legitimately
inert; a printed figure almost never is. "6,26200" — the NYS transfer tax with
its decimal point eaten by OCR, and therefore no '$' and no match — is the whole
reason the price looked absent.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent

import lexicon
import roles
import claim_read

# ── every pattern the system currently owns ─────────────────────────────────
# ⚠ IMPORTED, NEVER RETYPED. A private copy here would drift from the real
# extractor and this file would then report gaps that are already closed, or —
# far worse — miss gaps that are open. Same defect that put five copies of the
# clause regex in five tools.
def owned():
    pats = []
    for group, d in (("function", lexicon.FUNCTIONS), ("region", lexicon.REGIONS),
                     ("reference", lexicon.REFERENCES)):
        for name, v in d.items():
            for p in v["patterns"]:
                pats.append((f"{group}/{name}", re.compile(p, re.I)))
    for name, rx in (("value/money", claim_read.MONEY),
                     ("value/area", claim_read.AREA),
                     ("value/bbl", claim_read.BBL),
                     ("value/crfn", claim_read.CRFN),
                     ("value/date", claim_read.DATE),
                     ("value/operative", claim_read.OPERATIVE)):
        pats.append((name, rx))
    for p, r, _s in roles.ROLE_PATTERNS:
        pats.append((f"role/{r}", re.compile(p, re.I)))
    for name, rx in (("party/person", roles.PERSON), ("party/by", roles.BY_LINE),
                     ("party/title", roles.TITLE), ("party/entity", roles.ENTITY)):
        pats.append((name, rx))
    # ⚠ THE COVER READER COUNTS AS OWNERSHIP ONLY NOW THAT ITS FIELDS ARE
    # CLAIMS. Adding it here before cover_claims.py existed would have marked
    # the page "claimed" while nothing downstream could use a single field —
    # the audit would have reported the gap closed by a file that only wrote
    # JSON. What makes a field owned is that it reaches the claim layer with
    # provenance, not that some code somewhere matched it.
    import cover_read as cvr
    for name, rx in (("cover/parcel", cvr.PROP), ("cover/ptype", cvr.PTYPE),
                     ("cover/doctype", cvr.DOCTYPE), ("cover/pagecount", cvr.PAGECOUNT),
                     ("cover/docid", cvr.DOCID), ("cover/date_doc", cvr.D_DOC),
                     ("cover/date_prep", cvr.D_PREP), ("cover/date_rec", cvr.D_REC),
                     ("cover/continuation", cvr.CONT), ("cover/pageof", cvr.PAGEOF)):
        pats.append((name, rx))
    return pats


OWNED = owned()

# ⚠ A MATCH MARKS ITS CHARACTERS AND A MARGIN. "Mortgage Amount:" matched by the
# cover_page region should not leave ": 0.00" looking unclaimed and inflate the
# report. Two characters either side absorbs the punctuation a pattern stops
# short of, and no more — widening this hides real gaps.
MARGIN = 2


def mask(text):
    m = bytearray(len(text))
    for _name, rx in OWNED:
        for x in rx.finditer(text):
            a = max(0, x.start() - MARGIN)
            b = min(len(text), x.end() + MARGIN)
            for i in range(a, b):
                m[i] = 1
    return m


WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*|\d[\d,\.]*")
# Digits vary per document; the SHAPE is what recurs. "Block 1064" and
# "Block 1034" are one structure, and collapsing them is what makes df meaningful.
NUMERIC = re.compile(r"^\d[\d,\.]*$")
STOP = set("""a an the of to in on at by for and or as is are was were be been being
it its this that these those with from not no any all such other which who whom whose
shall will may can if then than so we he she they them their our your my me i you
""".split())

LABEL = re.compile(r"([A-Z][A-Za-z][A-Za-z /&\.\-]{1,44}?)\s*:")
# ⚠ NO '$' REQUIRED, AND THAT IS THE POINT. Requiring a currency mark is exactly
# the assumption that lost the RETT. A bare figure with cents-like structure is a
# printed amount whether or not OCR kept the sigil.
FIGURE = re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d{2})?\b|\b\d+\.\d{2}\b")


def norm(tok):
    t = tok.lower()
    return "#" if NUMERIC.match(t) else t


def phrases(text, m, lo=2, hi=5):
    """Word n-grams whose every character is unclaimed."""
    toks = [(w.group(0), w.start(), w.end()) for w in WORD.finditer(text)]
    free = [i for i, (_w, s, e) in enumerate(toks) if not any(m[s:e])]
    freeset = set(free)
    out = []
    for i in free:
        for n in range(lo, hi + 1):
            idx = list(range(i, i + n))
            if idx[-1] >= len(toks) or any(j not in freeset for j in idx):
                break
            # contiguity: no claimed character BETWEEN the words either
            a, b = toks[idx[0]][1], toks[idx[-1]][2]
            if any(m[a:b]):
                break
            g = [norm(toks[j][0]) for j in idx]
            if all(x in STOP or x == "#" for x in g):
                continue
            out.append(" ".join(g))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="devr_text")
    ap.add_argument("--show", type=int, default=30)
    a = ap.parse_args()

    src = HERE / a.dir
    files = sorted(src.glob("*.json"))
    if not files:
        print(f"  no text in {a.dir}/")
        return 1

    # region -> {phrase: set(doc)}, {label: set(doc)}, {figure-context: [..]}
    ph = {"cover": collections.defaultdict(set), "body": collections.defaultdict(set)}
    lb = {"cover": collections.defaultdict(set), "body": collections.defaultdict(set)}
    fig = {"cover": [], "body": []}
    chars = {"cover": [0, 0], "body": [0, 0]}     # [total, unclaimed]
    ndocs = 0

    for f in files:
        rec = json.loads(f.read_text(encoding="utf-8"))
        doc = rec.get("doc_id", f.stem)
        ndocs += 1
        for pg in rec.get("pages") or []:
            t = pg.get("accepted_text") or ""
            if not t:
                continue
            # ⚠ PAGE 1 IS THE ACRIS WRAPPER. Not a guess — "RECORDING AND
            # ENDORSEMENT COVER PAGE" is printed on it, and it is page 1 of 25/25.
            # ⚠ THE PAGE KEY IS "p001", NOT 1. The first version tested for the
            # integer, put every cover page in the body bucket, and reported
            # "cover 0 chars" — a bucket that silently receives nothing looks
            # exactly like a document type that has no cover page.
            where = "cover" if str(pg.get("page")).lstrip("p").lstrip("0") == "1" \
                else "body"
            m = mask(t)
            chars[where][0] += len(t)
            chars[where][1] += len(m) - sum(m)
            for p in phrases(t, m):
                ph[where][p].add(doc)
            for x in LABEL.finditer(t):
                if not any(m[x.start(1):x.end(1)]):
                    lb[where][" ".join(x.group(1).split()).lower()].add(doc)
            for x in FIGURE.finditer(t):
                if not any(m[x.start():x.end()]):
                    lo = max(0, x.start() - 60)
                    fig[where].append((doc, x.group(0),
                                       " ".join(t[lo:x.start()].split())[-52:]))

    print(f"COMPLETENESS PASS — {ndocs} documents, {a.dir}/")
    print(f"  {len(OWNED)} patterns owned by lexicon + claim_read + roles\n")
    for w in ("cover", "body"):
        tot, un = chars[w]
        print(f"  {w:<6} {tot:>9,} chars   unclaimed {un:>9,}  "
              f"{100*un/max(tot,1):>5.1f}%")

    for w in ("cover", "body"):
        print(f"\n{'='*72}\n  {w.upper()} — UNCLAIMED LABELS  (`Something:` no pattern owns)")
        rows = sorted(lb[w].items(), key=lambda kv: (-len(kv[1]), kv[0]))
        rows = [r for r in rows if len(r[1]) >= max(2, ndocs // 10)]
        for k, d in rows[:a.show]:
            print(f"    {len(d):>3}/{ndocs}  {k}")
        if not rows:
            print("    (none above threshold)")

    print(f"\n{'='*72}\n  COVER — UNCLAIMED FIGURES  (a printed number nothing reads)")
    seen = collections.Counter()
    for doc, v, ctx in fig["cover"]:
        seen[ctx[-40:]] += 1
    for ctx, n in seen.most_common(a.show):
        ex = next(v for _d, v, c in fig["cover"] if c[-40:] == ctx)
        print(f"    {n:>3}x  …{ctx}  ->  {ex}")

    for w in ("cover", "body"):
        print(f"\n{'='*72}\n  {w.upper()} — UNCLAIMED PHRASES  (by document frequency)")
        rows = sorted(ph[w].items(), key=lambda kv: (-len(kv[1]), -len(kv[0])))
        rows = [r for r in rows if len(r[1]) >= max(3, int(ndocs * 0.5))]
        # keep the longest phrase of each family: if a 2-gram is fully inside a
        # printed longer one at the same df, the longer one carries more meaning
        kept, out = [], []
        for k, d in rows:
            if any(k in s and len(dd) == len(d) for s, dd in kept):
                continue
            kept.append((k, d))
            out.append((k, d))
        for k, d in out[:a.show]:
            print(f"    {len(d):>3}/{ndocs}  {k}")
        if not out:
            print("    (none above threshold)")

    print("\n  ⚠ This ranks what NO pattern claims. A row here is not automatically")
    print("    a gap — boilerplate is genuinely inert. It is the CANDIDATE list,")
    print("    and it is the only list that can contain a field nobody modelled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
