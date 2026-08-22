"""BENCH FROM DOCUMENTS WE HAVE NEVER TOUCHED. Fetched live, not from the sample.

⚠ EVERY ENGINE CLAIM TODAY WAS MEASURED ON sample_pages, AND I HAVE BEEN TUNING
AGAINST IT ALL SESSION — psm modes, render widths, crop windows, frame lists. A
benchmark run on the same pages you tuned on measures the tuning, not the engine.

So: draw document ids at random from the 17M-row map, EXCLUDE anything already
on disk, and fetch one page each. Nothing here has been seen by me, by a frame
list, or by a preprocessing decision.

⚠ PAGE COUNT COMES FROM THE MAP, NOT FROM PROBING. An earlier version of the
fetch loop walked page=1..999 waiting for a 404 to mark the end — but ACRIS
serves a PLACEHOLDER TIFF past the last page, so it never terminated and made
hundreds of needless requests to a server that has already refused this project
once. hid_TotalPages is in the map for every document; it is free and exact.

⚠ MID-DOCUMENT PAGES ONLY. Page 1 is a cover sheet on modern documents and the
last pages are signatures and notary blocks. Both are unrepresentative: a cover
sheet is clean printed form text every engine aces, a signature page is nearly
empty. The body is where the claims live and where engines diverge.

Sequential, paced, aborts permanently on refusal. No retry, no work-around.

    python build_bench_live.py [n_per_era]
"""
import collections
import io
import json
import pathlib
import random
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

import fetch_pages as FP

PAGES = pathlib.Path("sample_pages")
IDS = pathlib.Path("acris_ids.jsonl")
MAPS = ("acris_maps.jsonl", "docmaps.jsonl")
OUT = pathlib.Path("render/live")
SEED = 20260811
WIDTH = 1400
PACE = 0.7
MIN_PAGES = 4          # needs a body, not a one-page satisfaction


def load_candidates(want_each):
    """Random documents from the map, never seen, with a known page count."""
    already = {p.name for p in PAGES.iterdir() if p.is_dir()} if PAGES.exists() else set()
    rng = random.Random(SEED)

    # doc_type + date from the index
    meta = {}
    with open(IDS, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            d = r.get("document_id") or r.get("doc_id")
            if not d or d in already:
                continue
            dt = (r.get("document_date") or r.get("recorded_datetime") or "")[:4]
            if not dt.isdigit():
                continue
            # ⚠ RESERVOIR-ISH: keep a bounded random subset instead of 17M rows
            if len(meta) < 400_000 or rng.random() < 0.02:
                meta[d] = (r.get("doc_type", "?"), f"{dt[:3]}0s")

    # page counts, only for documents we kept
    pc = {}
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
                d = r.get("doc_id")
                n = r.get("hid_TotalPages")
                if d in meta and n and int(n) >= MIN_PAGES:
                    pc[d] = int(n)

    by = collections.defaultdict(list)
    for d, n in pc.items():
        by["film" if d.startswith("FT_") else "modern"].append(d)
    out = {}
    for era in ("film", "modern"):
        rng.shuffle(by[era])
        out[era] = [(d, meta[d][0], meta[d][1], pc[d]) for d in by[era][:want_each * 4]]
    return out


def grab(doc, page):
    url = f"{FP.BASE}?doc_id={doc}&page={page}"
    req = urllib.request.Request(url, headers={
        "User-Agent": FP.UA,
        "Referer": f"https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id={doc}",
        "Accept": "image/tiff,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data, ctype = r.read(), r.headers.get("Content-Type", "")
    FP._check_denied(data, ctype)          # ⚠ raises -> we stop. no retry.
    return data


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    cand = load_candidates(per)
    rng = random.Random(SEED + 1)
    OUT.mkdir(parents=True, exist_ok=True)
    man = []

    for era in ("film", "modern"):
        print(f"\n  ── {era.upper()} · {len(cand[era])} candidates ──")
        print(f"  {'decade':<8}{'type':<10}{'pg':>4}{'KB':>7}  doc")
        got = 0
        for doc, dtype, dec, npages in cand[era]:
            if got >= per:
                break
            page = rng.randint(2, max(2, npages - 1))   # mid-document
            try:
                data = grab(doc, page)
            except FP.AccessDenied as e:
                print(f"\n  ⚠ {e}")
                (OUT / "manifest.json").write_text(json.dumps(man, indent=1),
                                                   encoding="utf-8")
                return
            except Exception:
                continue
            if data[:2] not in (b"II", b"MM"):
                time.sleep(PACE)
                continue
            im = Image.open(io.BytesIO(data))
            if im.mode == "1":
                im = im.convert("L")        # ⚠ 'L' before resize, always
            name = (f"{era}_{dec}_{dtype.replace('&','n').replace('/','-')}"
                    f"_{doc}_p{page:03d}.png")
            im.resize((WIDTH, int(im.height * WIDTH / im.width)),
                      Image.LANCZOS).save(OUT / name)
            man.append({"file": name, "doc": doc, "page": page, "doc_type": dtype,
                        "decade": dec, "era": era, "src_kb": round(len(data)/1024)})
            print(f"  {dec:<8}{dtype:<10}{page:>4}{len(data)/1024:>7.0f}  {doc}")
            got += 1
            time.sleep(PACE)

    (OUT / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    t = collections.Counter(m["doc_type"] for m in man)
    d = collections.Counter(m["decade"] for m in man)
    print(f"\n  {len(man)} pages -> {OUT}")
    print(f"  types:   " + "  ".join(f"{k}={v}" for k, v in t.most_common()))
    print(f"  decades: " + "  ".join(f"{k}={v}" for k, v in sorted(d.items())))
    print(f"  ⚠ none of these documents has been read, tuned on, or seen before.")


if __name__ == "__main__":
    main()
