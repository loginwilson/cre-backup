"""WHERE DOES A PARCEL'S IDENTITY ACTUALLY GET STATED — head, or body?

    python identity_depth.py            # 40 docs, stratified by type

⚠ WHY THIS AND NOT ANOTHER RECALL NUMBER. The current `identity` detector reads
`subdivid | merge into | apportion | tax lot creat` and fires on 68 of 666
documents. Reading one mortgage to page 11 showed why: pages 10 and 11 are
SCHEDULE A — "BEGINNING at a point on the Westerly side of Nostrand Avenue" —
the metes and bounds for both parcels, the strongest identity claim in the
instrument, and the detector scored zero on them.

⚠ THE OLD VOCABULARY IS NOT WRONG, IT IS HALF. `subdivid`/`merge` are the
TRANSACTS side: the parcel itself changed. A metes description is the OBSERVES
side: the parcel is being stated, not altered. Mode already separates them — that
was the argument for absorbing PARCEL into IDENTITY in the first place. So this
adds the missing half rather than replacing the existing one.

⚠ AND IT MEASURES BY DEPTH, because Schedule A sits at the END. Any head-page
rate for identity is an understatement by construction, and this counts by how
much rather than asserting it.
"""
from __future__ import annotations

import collections, json, pathlib, random, re, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import full_doc

HEAD = 3
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40

# the OBSERVES half — the parcel is stated
DESCRIBE = [
    ("metes",        r"\bBEGINNING\s+at\s+a\s+point\b|\bRUNNING\s+THENCE\b|\bTHENCE\s+(?:North|South|East|West)"),
    ("parcel_land",  r"\ball\s+that\s+certain\b|\b(?:plot|piece|parcel)\s+of\s+land\b"),
    ("schedule",     r"\bSCHEDULE\s*[\"“']?\s*A\b|\bTITLE\s*N[O0]\b"),
    ("block_lot",    r"\bBlock\s*:?\s*\d{1,5}\b.{0,24}\bLots?\b"),
    ("bounded",      r"bounded\s+and\s+described|more\s+(?:fully|particularly)\s+described"),
]
# the TRANSACTS half — the parcel changed. The vocabulary that already existed.
CHANGE = [
    ("subdivide",    r"\bsubdivid"),
    ("merge",        r"\bmerge[sd]?\s+into\b|\bzoning\s+lot\s+merger\b"),
    ("apportion",    r"\bapportion"),
    ("lot_created",  r"\btax\s+lot\s+creat"),
]
CC = [(n, re.compile(p, re.I), "describe") for n, p in DESCRIBE] + \
     [(n, re.compile(p, re.I), "change") for n, p in CHANGE]


def pick(n):
    ty = json.loads((HERE / "_doctype_of.json").read_text(encoding="utf-8"))
    by = collections.defaultdict(list)
    for d in ("sample_pages", "devr_pages", "pages_out", "fp_pages", "lease_pages"):
        p = HERE / d
        if not p.exists():
            continue
        for x in p.iterdir():
            if x.is_dir() and len(list(x.glob("p*.tif"))) >= 4 and x.name in ty:
                by[ty[x.name]].append(x.name)
    # ⚠ SPREAD ACROSS TYPES. DEVR is 1,192 of 1,649 and would otherwise BE the
    # measurement — the same homogeneity that made a one-document lexicon look
    # complete.
    rnd = random.Random(7)
    out = []
    types = sorted(by, key=lambda t: -len(by[t]))
    while len(out) < n and types:
        for t in list(types):
            if not by[t]:
                types.remove(t)
                continue
            out.append((rnd.choice(by[t]), t))
            by[t].remove(out[-1][0])
            if len(out) >= n:
                break
    return out


def main():
    docs = pick(N)
    print(f"{len(docs)} documents, stratified: "
          + " ".join(f"{t}={c}" for t, c in
                     collections.Counter(t for _, t in docs).most_common()))
    head_only = body_only = both = neither = 0
    where = collections.Counter()
    per_cue = collections.defaultdict(lambda: [0, 0])   # cue -> [head, body]
    pages_read = 0
    t0 = time.time()
    for i, (doc, ty) in enumerate(docs, 1):
        tifs = full_doc.pages_for(doc)
        if not tifs:
            continue
        got = full_doc.ocr(tifs)
        pages_read += len(got)
        h = " ".join(got[k][0] for k in sorted(got)[:HEAD])
        b = " ".join(got[k][0] for k in sorted(got)[HEAD:])
        fh = {n for n, rx, _g in CC if rx.search(h)}
        fb = {n for n, rx, _g in CC if rx.search(b)}
        for n in fh:
            per_cue[n][0] += 1
        for n in fb:
            per_cue[n][1] += 1
        if fh and fb:
            both += 1
        elif fh:
            head_only += 1
        elif fb:
            body_only += 1
            where[ty] += 1
        else:
            neither += 1
        if i % 10 == 0:
            print(f"  {i}/{len(docs)} · {pages_read} pages · "
                  f"{(time.time()-t0)/60:.1f} min", flush=True)

    n = len(docs)
    print(f"\nREAD {pages_read} pages in {(time.time()-t0)/60:.1f} min "
          f"({(time.time()-t0)/max(pages_read,1):.2f}s/page)\n")
    print(f"WHERE IDENTITY IS STATED  (head = pages 1-{HEAD})")
    print(f"  head and body   {both:>4}  {100*both/n:5.1f}%")
    print(f"  head only       {head_only:>4}  {100*head_only/n:5.1f}%")
    print(f"  ⚠ BODY ONLY     {body_only:>4}  {100*body_only/n:5.1f}%   "
          f"— invisible to every head-page read")
    print(f"  neither         {neither:>4}  {100*neither/n:5.1f}%")
    if where:
        print("    body-only by type: " + " ".join(f"{k}={v}" for k, v in where.most_common()))

    print(f"\nPER CUE — documents where it fires")
    print(f"  {'cue':<14}{'head':>6}{'body':>6}{'body-only lift':>16}")
    for name, _rx, grp in CC:
        h, b = per_cue[name]
        print(f"  {name:<14}{h:>6}{b:>6}{'':>6}{grp}")

    json.dump({"n": n, "pages": pages_read, "both": both, "head_only": head_only,
               "body_only": body_only, "neither": neither,
               "per_cue": {k: v for k, v in per_cue.items()},
               "head_pages": HEAD},
              open(HERE / "_identity_depth.json", "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
