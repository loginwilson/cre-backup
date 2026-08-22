"""THE WORKFLOW, END TO END, ON ONE DOCUMENT. No drive.

    selection   the map already holds it          (done, 17,049,742 documents)
    acquisition FETCH from the mapped endpoint    -- not download, not stored
    extraction  OCR -> frames -> coordinates      -- this file
    resolution  lineage across claims             (Supabase, later)
    derivation  summary + stats                   (Supabase, later)

⚠ THE PIXELS ARE SCRAP AND THAT IS THE POINT. Measured: one sequential
connection does 3.02 pages/sec against 4.14 for 8-core OCR, and 12 of 12
re-fetched pages were byte-identical to stored copies. So the network is never
the bottleneck and the bytes are always recoverable -- which makes a 6.3 TB
drive a queue for a line that has no queue in it. Pages are fetched, read, and
dropped. Only text and coordinates survive.

⚠ THE FRAME PASS IS DELIBERATELY FUZZY AND THAT IS A REVERSAL. An earlier
version disqualified fuzzy matching for generating 113 false positives on
`party wall` (`part will`). That was the wrong call, because the two errors do
not cost the same:

    false positive   one crop the model glances at and discards
    false negative   a claim nobody ever looks at, and NOTHING SAYS SO

So stage 2 over-reports on purpose. Precision is the model's job downstream;
recall is the only thing that cannot be recovered later.

⚠ COORDINATES ARE STORED AS FRACTIONS, NOT PIXELS. Pages in this corpus are not
one size -- 2544x3359 was measured where 2550x3300 was assumed. A pixel box
re-rendered against a slightly different rendition lands in the wrong place and
crops half a line, silently. A fraction survives any rendition at any scale.

    python pipeline.py <doc_id> [max_pages]
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

import fetch_pages as FP
from scanner_cost import FRAMES, lev1, norm, variants

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCRATCH = pathlib.Path(os.environ["TMP"]) / "pipe"
OUT = pathlib.Path("render/pipeline")
CORES = os.cpu_count()
PACE = 0.6


# ── acquisition · fetch, never store ────────────────────────────────────
def fetch(doc_id, page):
    url = f"{FP.BASE}?doc_id={doc_id}&page={page}"
    req = urllib.request.Request(url, headers={
        "User-Agent": FP.UA,
        "Referer": "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView",
        "Accept": "image/tiff,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data, ctype = r.read(), r.headers.get("Content-Type", "")
    FP._check_denied(data, ctype)          # ⚠ raises -> we stop. no retry.
    return data


# ── extraction · OCR with boxes ─────────────────────────────────────────
def ocr_page(path):
    r = subprocess.run([TESS, str(path), "stdout", "--psm", "4", "-c",
                        "tessedit_create_tsv=1"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    words = []
    for line in r.stdout.splitlines()[1:]:
        p = line.split("\t")
        if len(p) < 12 or not p[11].strip():
            continue
        try:
            words.append({"t": p[11], "x": int(p[6]), "y": int(p[7]),
                          "w": int(p[8]), "h": int(p[9]), "c": float(p[10])})
        except ValueError:
            continue
    return words


def find_frames(words, seqs_by_frame):
    """Fuzzy, over-reporting on purpose. Returns (label, lo, hi) indices."""
    toks = [norm(w["t"]) for w in words]
    hits, taken = [], set()
    for lab, seqs in seqs_by_frame:
        for s in seqs:
            k = len(s)
            for i in range(len(toks) - k + 1):
                if (lab, i) in taken:
                    continue
                if all(lev1(toks[i + j], s[j]) for j in range(k)):
                    taken.add((lab, i))
                    hits.append((lab, i, i + k - 1))
    return hits


def page_count(doc):
    """How many pages? ASK THE MAP. Never probe.

    ⚠ THE BUG THIS REPLACES MADE HUNDREDS OF NEEDLESS REQUESTS. The first
    version walked page=1..999 waiting for a 404 to mark the end — but ACRIS
    serves a PLACEHOLDER TIFF past the last page (fetch_pages.py carries its
    md5 for exactly this reason), so the loop never terminated. It kept asking
    a server that has already refused this project once.

    Selection exists precisely so acquisition never has to guess. hid_TotalPages
    is in the map for all 17M documents; reading it is free and exact.
    """
    head = '{"doc_id": "%s"' % doc
    for name in ("acris_maps.jsonl", "docmaps.jsonl"):
        p = pathlib.Path(name)
        if not p.exists():
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith(head):
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    n = r.get("hid_TotalPages")
                    if n:
                        return int(n)
    return None


def main():
    doc = sys.argv[1]
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else page_count(doc)
    if not cap:
        print(f"  {doc} is not in the map — refusing to probe for page count.")
        return
    SCRATCH.mkdir(parents=True, exist_ok=True)
    d = OUT / doc
    d.mkdir(parents=True, exist_ok=True)
    seqs = [(lab, variants(rx)) for lab, rx in FRAMES]

    print(f"  {doc} · fetch -> OCR -> frames -> coordinates · nothing stored\n")

    t_fetch = t_ocr = 0.0
    pages, claims = [], []
    n = 0
    try:
        for pg in range(1, cap + 1):
            t0 = time.time()
            try:
                data = fetch(doc, pg)
            except urllib.error.HTTPError as e:
                if e.code in (404, 500):
                    break                      # past the last page
                raise
            t_fetch += time.time() - t0
            if not data[:2] in (b"II", b"MM"):
                break
            f = SCRATCH / f"{doc}_p{pg:03d}.tif"
            f.write_bytes(data)
            pages.append((pg, f, len(data)))
            n += 1
            time.sleep(PACE)
    except FP.AccessDenied as e:
        print(f"  ⚠ {e}\n"); return
    if not pages:
        print("  no pages"); return

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=CORES) as ex:
        allwords = list(ex.map(lambda p: ocr_page(p[1]), pages))
    t_ocr = time.time() - t0

    nwords = 0
    for (pg, f, nb), words in zip(pages, allwords):
        nwords += len(words)
        im = Image.open(f)
        W, H = im.size
        for lab, lo, hi in find_frames(words, seqs):
            # ⚠ CONTEXT WINDOW, NOT THE MATCH. The claim follows the frame.
            a, b = max(0, lo - 10), min(len(words) - 1, hi + 35)
            box = words[a:b + 1]
            x0 = min(w["x"] for w in box); x1 = max(w["x"] + w["w"] for w in box)
            y0 = min(w["y"] for w in box); y1 = max(w["y"] + w["h"] for w in box)
            claims.append({
                "document_id": doc, "page": pg, "frame": lab,
                "box": [round(x0 / W, 4), round(y0 / H, 4),
                        round(x1 / W, 4), round(y1 / H, 4)],
                "page_px": [W, H],
                "text": " ".join(w["t"] for w in box)[:220],
                "state": "CANDIDATE",          # only the model can promote this
            })

    (d / "candidates.jsonl").write_text(
        "\n".join(json.dumps(c) for c in claims), encoding="utf-8")

    for _, f, _ in pages:                      # ⚠ pixels are scrap
        try:
            f.unlink()
        except OSError:
            pass

    mb = sum(nb for _, _, nb in pages) / 1e6
    tot = t_fetch + t_ocr
    print(f"  {'stage':<16}{'time':>9}{'rate':>16}")
    print(f"  {'acquisition':<16}{t_fetch:>8.1f}s{n/t_fetch:>11.2f} pg/s")
    print(f"  {'extraction':<16}{t_ocr:>8.1f}s{n/t_ocr:>11.2f} pg/s")
    print(f"  {'TOTAL':<16}{tot:>8.1f}s{n/tot:>11.2f} pg/s\n")
    print(f"  {n} pages · {mb:.1f} MB moved · {nwords:,} words · 0 bytes kept")

    by = {}
    for c in claims:
        by.setdefault(c["frame"], []).append(c)
    print(f"\n  {len(claims)} frame candidates on {len({c['page'] for c in claims})} pages")
    for lab in sorted(by, key=lambda k: -len(by[k])):
        pgs = sorted({c["page"] for c in by[lab]})
        print(f"    {lab:<22}{len(by[lab]):>4}  pages {pgs[:9]}")
    print(f"\n  -> {d/'candidates.jsonl'}")
    print(f"  ⚠ every row is a CANDIDATE. Nothing here is a claim until a model")
    print(f"    reads the box and says what it says.")


if __name__ == "__main__":
    main()
