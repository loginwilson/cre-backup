"""ACROSS PARCELS — from HELD BYTES, no fetching.

⚠ WHY THIS RUN EXISTS IN THIS FORM. The designed experiment was 40 deeds drawn
citywide. ACRIS refused service after four pages; the guard fired, burned the
day, and that is the end of fetching today. Working around it is the one thing
this project does not do.

But `store.py` retains the ORIGINAL BYTES of every page ever fetched — 1,688
pages, 92 non-microfilm documents, 13 distinct borough-blocks. That is a real
across-parcel sample sitting on disk, and it exists ONLY because the delete-
after-reading rule was abandoned on 2026-08-05. The store was justified then as
making parser fixes retroactive; this is a second dividend nobody predicted.

⚠ WHAT THIS SAMPLE CAN AND CANNOT ANSWER.

  CAN   "do same-type documents from DIFFERENT parcels and DIFFERENT deals
        share a layout?" Blocks 799/818/826/827/829/851/880/1113 in Manhattan
        plus Brooklyn and Queens — different owners, different counsel,
        1971-2026.

  CANNOT  the repeat-filer question (stratum C), which is where the volume
        actually is. One firm's book of 41 deeds is the population that would
        pay for template extraction, and it is untested. THE HEADLINE NUMBER
        STAYS OPEN until that runs.

  ⚠ AND THE SAMPLE IS BIASED TOWARD MATCHING, WHICH MAKES A NULL STRONG. These
  documents are neighbours in one assemblage: adjacent blocks, overlapping
  counsel, several recorded in the same batch. If layouts repeat anywhere they
  should repeat HERE. A null result on a sample stacked in favour is worth more
  than a null on a fair one.
"""
import collections
import io
import json
import pathlib
import sys

import numpy as np
from PIL import Image

import fingerprint as fp

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = pathlib.Path("fp_across")
OUT.mkdir(exist_ok=True)

# ⚠ NOT A PAGE PRIOR. The first version of this run used pages (2,3,4) on the
# reasoning "past the cover". It is not past the cover — the ACRIS cover runs to
# 4 pages on a multi-party document, and those continuation pages produced a
# "cluster of 16" spanning 2014-2025 and three boroughs that I nearly reported
# as evidence for citywide templates. Take a WIDE range and let coverpage.py
# detect the boundary per document. See coverpage.py for what the first
# detector nearly deleted.
CAND_PAGES = range(1, 9)

held = json.load(open("_held_docs.json"))
man = [json.loads(l) for l in
       pathlib.Path("corpus/manifest.jsonl").read_text(encoding="utf-8").splitlines()
       if l.strip()]

# ---- render the held blobs to PNG ------------------------------------------
idx = {}
for r in man:
    if r["doc_id"] in held and r["page"].isdigit() and int(r["page"]) in CAND_PAGES:
        idx[(r["doc_id"], int(r["page"]))] = r["sha256"]

made = 0
for (doc, pg), sha in idx.items():
    dst = OUT / doc
    dst.mkdir(exist_ok=True)
    f = dst / f"p{pg:03d}.png"
    if f.exists():
        continue
    blob = pathlib.Path("corpus/blobs") / sha[:2] / sha[2:4] / sha
    if not blob.exists():
        continue
    try:
        Image.open(io.BytesIO(blob.read_bytes())).convert("L").save(f)
        made += 1
    except Exception as e:
        print(f"  ⚠ {doc} p{pg}: {type(e).__name__}")

print(f"rendered {made} pages from held blobs "
      f"({len(idx)} body pages available across {len(held)} documents)")

# ---- group by type, and label every pair same-block vs cross-block ---------
import coverpage

bytype = collections.defaultdict(list)
dropped = 0
for doc, meta in held.items():
    blocks = {b.rsplit("-", 1)[0] for b in meta["bbl"]}
    for pg in CAND_PAGES:
        f = OUT / doc / f"p{pg:03d}.png"
        if not f.exists():
            continue
        cover, why = coverpage.is_cover(f)
        if cover:
            dropped += 1
            continue
        bytype[meta["type"]].append((f"{doc}p{pg}", f, blocks, meta["rec"][:4]))
print(f"dropped {dropped} City-generated cover pages (detected, not assumed)")

print(f"\nACROSS PARCELS — metric: row-ink L1, {fp.ROWS} rows, "
      f"match cutoff {fp.MATCH}")

import itertools
tot_same = tot_cross = m_same = m_cross = 0
best_cross = []

for t, items in sorted(bytype.items(), key=lambda kv: -len(kv[1])):
    if len(items) < 3:
        continue
    profs = [(n, fp.profile(p), b, y) for n, p, b, y in items]
    profs = [x for x in profs if x[1] is not None]
    pairs = []
    for (an, ap, ab, ay), (bn, bp, bb, by) in itertools.combinations(profs, 2):
        if an[:16] == bn[:16]:
            continue                      # two pages of ONE document — not the test
        d = fp.distance(ap, bp)
        cross = not (ab & bb)             # no block in common
        pairs.append((d, an, bn, cross, ay, by))
    if not pairs:
        continue
    pairs.sort()
    same = [p for p in pairs if not p[3]]
    cross = [p for p in pairs if p[3]]
    ms = [p for p in same if p[0] <= fp.MATCH]
    mc = [p for p in cross if p[0] <= fp.MATCH]
    tot_same += len(same); tot_cross += len(cross)
    m_same += len(ms);     m_cross += len(mc)
    best_cross += [p for p in cross][:3]
    print(f"\n  {t:<6} n={len(profs):<3} pairs={len(pairs)}   "
          f"best {pairs[0][0]:.3f}  median {np.median([p[0] for p in pairs]):.3f}")
    print(f"         same-block  {len(ms):>3}/{len(same):<4} matched   "
          f"cross-block {len(mc):>3}/{len(cross):<4} matched")
    for d, a, b, c, ay, by in pairs[:3]:
        tag = "CROSS-BLOCK" if c else "same-block "
        print(f"           {d:.3f}  {tag}  {a} ({ay}) ≈ {b} ({by})")

print(f"\n  TOTALS")
print(f"    same-block   {m_same}/{tot_same} matched "
      f"({100*m_same/max(tot_same,1):.1f}%)")
print(f"    CROSS-BLOCK  {m_cross}/{tot_cross} matched "
      f"({100*m_cross/max(tot_cross,1):.1f}%)   <- THE ANSWER")

allitems = [(n, p) for v in bytype.values() for n, p, _, _ in v]
cl = fp.clusters(allitems)
print(f"\n    {len(allitems)} pages -> {len(cl)} clusters   "
      f"saving {len(allitems)/max(len(cl),1):.2f}x")
big = sorted(cl, key=len, reverse=True)[:5]
for c in big:
    if len(c) > 1:
        print(f"      cluster of {len(c)}: {', '.join(c[:6])}")
