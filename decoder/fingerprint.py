"""LAYOUT FINGERPRINT — decide, for free, whether a page has been seen before.

⚠ WHY THIS FILE EXISTS AT ALL, AND WHY IT IS A FILE. The first version of this
test was a throwaway script in a shell pipe. Its numbers ("EASE 1.04, TL&R
0.10") could not be reproduced afterwards, so the within-parcel result could
not be compared against any later run. A measurement you cannot re-run is an
anecdote. THE METRIC HAS TO LIVE SOMEWHERE.

WHAT IS BEING TESTED
    If two documents of the same type were produced from the same word
    processor template, their pages have the same INK SKELETON — same margins,
    same paragraph starts, same blank bands — even though every name, date and
    dollar figure differs. If that is true at scale, then most pages can be
    extracted BY POSITION against a template read once, and the corpus cost
    collapses by roughly the size of the largest cluster.

    The first run tested this WITHIN ONE PARCEL and found almost no matching.
    That test was underpowered: lot 49's two deeds are six years apart from
    different law firms. The hypothesis was never "deeds match each other"; it
    is "a preparer's template matches itself." That needs documents from MANY
    parcels.

THE METRIC
    Row-ink profile, L1 distance.

      1. grayscale -> binarize at Otsu, so a dark microfilm scan and a clean
         laser print are comparable at all
      2. collapse to ROWS x 1: the fraction of dark pixels in each row
      3. resample to a fixed ROWS so different page sizes compare
      4. L1 distance between the two profiles, divided by ROWS

    0.00  identical ink skeleton
    ~0.35 empirical "same template, different content" (see CUTOFF)
    >0.50 different layouts

⚠ ROW PROFILE, NOT PIXEL DIFF, AND THAT IS THE WHOLE TRICK. A pixel diff of
two fills of one template is ~100% different — every glyph moved. The row
profile ignores WHAT is on a line and keeps WHERE the lines are, which is
exactly the part a template fixes and the content does not.

⚠ WHAT THIS CANNOT DO. A match says "same skeleton", never "same meaning". It
licenses extract-by-position for the SLOTS A HUMAN ALREADY LOCATED on the
template exemplar. It never licenses skipping a page that a template match
says is boilerplate — a rider typed into a form's blank space has the form's
skeleton and carries the only term that matters.
"""
import itertools
import json
import pathlib
import sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROWS = 256          # profile length; 256 is finer than a paragraph, coarser than a line
MATCH = 0.35        # below this: same template. See CUTOFF note in main().
NOVEL = 0.50        # above this: genuinely different layout


def _otsu(a):
    """Threshold that separates ink from paper without assuming either level.

    ⚠ A FIXED THRESHOLD FAILS ON THIS CORPUS. 1971 microfilm has grey paper
    and grey ink; a 2013 laser print is black on white. Any constant makes the
    microfilm all-ink or all-paper and every microfilm page then looks
    identical to every other — a fake 0.00 match, which is the worst possible
    error here.
    """
    hist = np.bincount(a.ravel(), minlength=256).astype(float)
    tot = hist.sum()
    if tot == 0:
        return 128
    w = np.cumsum(hist)
    m = np.cumsum(hist * np.arange(256))
    mt = m[-1]
    denom = w * (tot - w)
    denom[denom == 0] = 1
    between = (mt * w - m * tot) ** 2 / denom
    return int(np.argmax(between))


def profile(path, rows=ROWS):
    """One page -> its ink skeleton, as a length-`rows` vector."""
    im = Image.open(path).convert("L")
    a = np.asarray(im)
    if a.size == 0:
        return None
    t = _otsu(a)
    ink = (a <= t)

    # ⚠ TRIM THE SCAN BORDER, NOT THE MARGINS. Microfilm frames carry a black
    # edge tens of pixels wide that dominates the profile and makes two
    # unrelated film pages look alike. Drop 2% off each side — enough for the
    # frame, nowhere near the text block, and it does NOT touch the hand
    # annotations that live in the left margin proper.
    h, w = ink.shape
    dy, dx = int(h * 0.02), int(w * 0.02)
    ink = ink[dy:h - dy, dx:w - dx]

    rowink = ink.mean(axis=1)                       # fraction dark per row
    idx = np.linspace(0, len(rowink) - 1, rows)
    p = np.interp(idx, np.arange(len(rowink)), rowink)

    # ⚠ NORMALISE, OR TONER WINS. A darker print of the SAME template scores
    # far apart on raw ink. Scaling to unit area compares the SHAPE of the
    # distribution — where the text is — and discards how black it is.
    s = p.sum()
    return p / s if s > 0 else p


def distance(p, q):
    return float(np.abs(p - q).sum()) if p is not None and q is not None else None


def page_path(root, doc, page):
    d = pathlib.Path(root) / doc
    for pat in (f"p{page:03d}.png", f"p{page}.png", f"{page}.png"):
        f = d / pat
        if f.exists():
            return f
    return None


def compare(items, label=""):
    """items: [(name, path)]. Prints the full pairwise picture, returns pairs."""
    profs = []
    for name, path in items:
        p = profile(path)
        if p is not None:
            profs.append((name, p))
    if len(profs) < 2:
        print(f"  {label}: n={len(profs)} — need 2+")
        return []
    pairs = []
    for (an, ap), (bn, bp) in itertools.combinations(profs, 2):
        pairs.append((distance(ap, bp), an, bn))
    pairs.sort()
    ds = [d for d, _, _ in pairs]
    matched = [p for p in pairs if p[0] <= MATCH]
    print(f"\n  {label}   n={len(profs)}  pairs={len(pairs)}")
    print(f"    best {ds[0]:.3f}   median {np.median(ds):.3f}   worst {ds[-1]:.3f}")
    print(f"    pairs under {MATCH}: {len(matched)}/{len(pairs)} "
          f"({100*len(matched)/len(pairs):.0f}%)")
    for d, a, b in matched[:8]:
        print(f"      {d:.3f}  {a}  ≈  {b}")
    return pairs


def clusters(items, cutoff=MATCH):
    """Single-link clustering. THE NUMBER THAT DECIDES THE COST.

    If N pages fall into K clusters, you read K pages properly and extract the
    other N-K by position. The saving is N/K — so this function, not the
    average distance, is the answer to "what does the corpus cost".
    """
    profs = [(n, profile(p)) for n, p in items]
    profs = [(n, p) for n, p in profs if p is not None]
    parent = {n: n for n, _ in profs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (an, ap), (bn, bp) in itertools.combinations(profs, 2):
        if distance(ap, bp) <= cutoff:
            ra, rb = find(an), find(bn)
            if ra != rb:
                parent[ra] = rb
    out = {}
    for n, _ in profs:
        out.setdefault(find(n), []).append(n)
    return list(out.values())
