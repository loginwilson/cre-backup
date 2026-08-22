"""THE BENCH SET: stratified random across DECADE and DOCUMENT TYPE.

⚠ ONE-OFF PAGES HAVE PRODUCED FIVE WRONG CONCLUSIONS IN THIS PROJECT. "Tesseract
fails on film" (it scores 8/10), "downscaling holds recall" (it loses 7%),
"0.35 scale is free", "the film failure is catastrophic" (it was a psm-6 cache
artefact), "the model reads better" (two pages). Every one came from a single
page that happened to behave, generalised immediately.

So the set is built to make that impossible:

    STRATIFIED   every decade 1960s-2020s and the main document types, because
                 scan quality tracks era and layout tracks type, and an engine
                 can be excellent at one and useless at another
    RANDOM       within each stratum, seeded — not "the worst page I could find"
                 and not "a page I already know something about"
    FIXED        written once to a manifest so every engine sees IDENTICAL
                 pixels; an engine compared on different pages is not compared

⚠ AND THE PAGE MUST CARRY TEXT. A signature page or a blank verso scores 100%
on every engine and dilutes the result toward a tie. Minimum word count is a
floor on informativeness, not a quality filter.

    python build_bench.py [n_per_decade]
"""
import collections
import gzip
import json
import pathlib
import random
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

OCR = pathlib.Path("sample_ocr")
PAGES = pathlib.Path("sample_pages")
IDS = pathlib.Path("acris_ids.jsonl")
OUT = pathlib.Path("render/bench2")
SEED = 20260811
MIN_WORDS = 120
WIDTH = 1400          # ⚠ the width Tesseract scored best on; same for all engines


def index():
    """doc_id -> (doc_type, decade). Only for documents we hold pages for."""
    have = {p.name for p in PAGES.iterdir() if p.is_dir()}
    out = {}
    with open(IDS, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            d = r.get("document_id") or r.get("doc_id")
            if d not in have or d in out:
                continue
            dt = (r.get("document_date") or r.get("recorded_datetime") or "")[:4]
            out[d] = (r.get("doc_type", "?"),
                      f"{dt[:3]}0s" if dt.isdigit() else "?")
            if len(out) == len(have):
                break
    return out


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    meta = index()
    rng = random.Random(SEED)

    # every page we could use, tagged with its stratum
    pool = collections.defaultdict(list)
    for p in OCR.glob("*.json.gz"):
        d = p.name[:-8]
        if d not in meta:
            continue
        dtype, dec = meta[d]
        try:
            rows = json.load(gzip.open(p, "rt", encoding="utf-8"))
        except Exception:
            continue
        for r in rows:
            if len(r["words"]) < MIN_WORDS:
                continue
            f = PAGES / d / f"p{r['page']:03d}.tif"
            if not f.exists():
                continue
            conf = statistics.mean(w.get("c", 0) for w in r["words"])
            pool[dec].append((d, r["page"], dtype, dec, round(conf, 1),
                              len(r["words"]), f))

    OUT.mkdir(parents=True, exist_ok=True)
    man = []
    print(f"  {'decade':<8}{'pool':>7}   picked")
    for dec in sorted(pool):
        if dec == "?":
            continue
        cand = pool[dec]
        # ⚠ SPREAD ACROSS TYPES INSIDE THE DECADE. Sampling the decade alone
        # tends to draw the type that happens to dominate it, which smuggles a
        # layout bias in behind an era label.
        bytype = collections.defaultdict(list)
        for c in cand:
            bytype[c[2]].append(c)
        types = sorted(bytype)
        rng.shuffle(types)
        picked = []
        for t in types:
            if len(picked) >= per:
                break
            picked.append(rng.choice(bytype[t]))
        while len(picked) < per and cand:
            c = rng.choice(cand)
            if c not in picked:
                picked.append(c)
        print(f"  {dec:<8}{len(cand):>7}   " +
              ", ".join(f"{p[2]}/{p[4]:.0f}" for p in picked))
        for d, pg, dtype, dd, conf, nw, f in picked:
            im = Image.open(f)
            if im.mode == "1":
                im = im.convert("L")      # ⚠ 'L' before resize, always
            name = f"{dd}_{dtype.replace('&','n').replace('/','-')}_{d}_p{pg:03d}.png"
            im.resize((WIDTH, int(im.height * WIDTH / im.width)),
                      Image.LANCZOS).save(OUT / name)
            man.append({"file": name, "doc": d, "page": pg, "doc_type": dtype,
                        "decade": dd, "era": "film" if d.startswith("FT_") else "modern",
                        "tess_cache_conf": conf, "tess_cache_words": nw})

    (OUT / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(f"\n  {len(man)} pages -> {OUT}")
    e = collections.Counter(m["era"] for m in man)
    t = collections.Counter(m["doc_type"] for m in man)
    print(f"  era: " + "  ".join(f"{k}={v}" for k, v in e.items()))
    print(f"  types: " + "  ".join(f"{k}={v}" for k, v in t.most_common()))
    print(f"\n  ⚠ identical pixels for every engine, seed {SEED}, width {WIDTH}")


if __name__ == "__main__":
    main()
