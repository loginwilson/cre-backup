"""BALANCED BENCH: N film + N modern, spread across decade and document type.

⚠ THE PREVIOUS SET WAS 15 MODERN / 6 FILM AND THAT HIDES THE ONLY INTERESTING
RESULT. Film is where Tesseract and a VLM actually diverge — modern typed text
scored 10/10 for Tesseract and 10/10 for Qwen, so a modern-heavy set drives every
engine toward a tie and the average conceals the split. Equal weight makes the
divergence visible instead of averaging it away.

⚠ STRATIFIED WITHIN ERA TOO. Drawing 10 film pages at random tends to pull them
from whichever decade and doc type happens to dominate the pool, which smuggles
a layout or scan-vintage bias in behind the word "random".

    python build_bench_bal.py [n_per_era]
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
OUT = pathlib.Path("render/bench3")
SEED = 20260811
MIN_WORDS = 120
WIDTH = 1400


def index():
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
    per_era = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    meta = index()
    rng = random.Random(SEED)

    pool = collections.defaultdict(list)          # era -> pages
    for p in OCR.glob("*.json.gz"):
        d = p.name[:-8]
        if d not in meta:
            continue
        dtype, dec = meta[d]
        if dec == "?":
            continue
        try:
            rows = json.load(gzip.open(p, "rt", encoding="utf-8"))
        except Exception:
            continue
        era = "film" if d.startswith("FT_") else "modern"
        for r in rows:
            if len(r["words"]) < MIN_WORDS:
                continue
            f = PAGES / d / f"p{r['page']:03d}.tif"
            if not f.exists():
                continue
            pool[era].append((d, r["page"], dtype, dec,
                              round(statistics.mean(w.get("c", 0) for w in r["words"]), 1),
                              f))

    OUT.mkdir(parents=True, exist_ok=True)
    man = []
    for era in ("film", "modern"):
        cand = pool[era]
        # ⚠ ROUND-ROBIN OVER (decade, type) CELLS so no single vintage or layout
        # can dominate the era's sample.
        cells = collections.defaultdict(list)
        for c in cand:
            cells[(c[3], c[2])].append(c)
        keys = sorted(cells)
        rng.shuffle(keys)
        picked, i = [], 0
        while len(picked) < per_era and keys:
            k = keys[i % len(keys)]
            if cells[k]:
                picked.append(cells[k].pop(rng.randrange(len(cells[k]))))
            else:
                keys.remove(k)
                if not keys:
                    break
                i -= 1
            i += 1
        print(f"\n  ── {era.upper()}  {len(picked)} of {len(cand)} available ──")
        print(f"  {'decade':<8}{'type':<10}{'conf':>6}  doc")
        for d, pg, dtype, dec, conf, f in picked:
            im = Image.open(f)
            if im.mode == "1":
                im = im.convert("L")           # ⚠ 'L' before resize, always
            name = (f"{era}_{dec}_{dtype.replace('&','n').replace('/','-')}"
                    f"_{d}_p{pg:03d}.png")
            im.resize((WIDTH, int(im.height * WIDTH / im.width)),
                      Image.LANCZOS).save(OUT / name)
            man.append({"file": name, "doc": d, "page": pg, "doc_type": dtype,
                        "decade": dec, "era": era, "tess_cache_conf": conf})
            print(f"  {dec:<8}{dtype:<10}{conf:>6.0f}  {d} p{pg}")

    (OUT / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    c = collections.Counter(m["era"] for m in man)
    t = collections.Counter(m["doc_type"] for m in man)
    print(f"\n  {len(man)} pages -> {OUT}")
    print(f"  era:   " + "  ".join(f"{k}={v}" for k, v in c.items()))
    print(f"  types: " + "  ".join(f"{k}={v}" for k, v in t.most_common()))
    print(f"  ⚠ identical pixels for every engine · seed {SEED} · width {WIDTH}")


if __name__ == "__main__":
    main()
