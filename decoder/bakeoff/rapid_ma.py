"""RAPIDOCR, MULTI-ANGLE, WITH BOXES IN ORIGINAL PAGE COORDINATES.

    python rapid_ma.py --src pages/FT_1680008647768 --tag rapidma/FT_1680008647768
    python rapid_ma.py --src pages/X --tag rapidma/X --angles 0,90,270 --limit 4

⚠ WHY THIS EXISTS RATHER THAN pp_doc.py. Paddle is installed and correct, and on
lab hardware it is the better engine — but on THIS machine it produced ZERO pages in
~12 minutes on 10 film pages at 3 angles while pinning the CPU. RapidOCR measures
1.14 s/read at 8 processes x 1 thread on 8 cores (64 reads, devr_pages, model load
amortised). Over the 47,378 local un-OCR'd pages that is ~15 h single-angle,
against roughly two months for Paddle. Paddle returns when there is hardware.

⚠ NOT SUB-SECOND, AND THE SUB-SECOND FIGURES BELONG TO OTHER THINGS. PP-OCRv6's
0.13 s/page is an A100 number from the paper (flagged as not-ours in four files);
4.4 pages/s is TESSERACT at 8-wide, and Tesseract scores 73.8% against RapidOCR's
92.3% on the keyed bench. 0.072 pages/s was RapidOCR from ONE process. The honest
RapidOCR number on this box is ~1.1 s/read at 8-wide.

⚠ THE VLM CRASH IS NOT PADDLE'S FAULT — an earlier reading of mine said it was.
`ggml_vulkan: device lost on Vulkan0` reproduces with the machine completely idle,
so it is the `-ngl 99` Vulkan path on the Arc iGPU. route.py runs `-ngl 0`.

⚠ SAME RECORD SHAPE AS pp_doc.py, DELIBERATELY. Items are {text, box, angle, score}
so nothing downstream can tell which engine ran. Paddle drops back in unchanged when
there is hardware for it — the engine is a swappable input, not an architecture.

⚠ BOXES ARE MAPPED BACK TO THE ORIGINAL PAGE, AND THAT IS THE WHOLE POINT.
devr_sweep.work() returns `x[1]` and throws `x[0]` away, so every sweep so far
produced characters with no geometry. Without a box a claim cannot be re-verified,
a crop cannot be cut, and a value cannot be placed. Two transforms sit between the
reader and the page and BOTH must be undone:
    resize   coordinates come back in the 1600px frame -> divide by the scale
    rotate   `expand=True` swaps W and H at 90/270 -> resolve.locate.unrotate
That inverse is NOT re-derived here. A sign error does not throw; it returns a
plausible rectangle over the wrong part of the page and the crop looks fine. The
verified mapping was probe-tested at every corner and angle, so it is imported.

⚠ ANGLES ARE KEPT SEPARATE, NEVER CONCATENATED. `ppv6-rot` merged 0/90/270 into one
text file, which is why it emitted ~3x the tokens and why every token-level fusion
against it was comparing one reading to three. Each angle stays its own item stream
with `angle` on every item; merging is a downstream decision made in the open.
"""
from __future__ import annotations

import argparse, json, pathlib, sys, time
from multiprocessing import Pool

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
DEC = HERE.parent
sys.path.insert(0, str(DEC))
sys.path.insert(0, str(DEC / "resolve"))

MAXDIM = 1600          # the frame devr_sweep has always read in


def _init(threads):
    import devr_sweep
    devr_sweep._init(threads)
    global _O
    _O = devr_sweep._O


def work(args):
    """One page, one angle. Returns items with boxes in ORIGINAL coordinates."""
    path, angle = args
    import numpy as np
    from PIL import Image
    from locate import unrotate
    Image.MAX_IMAGE_PIXELS = None
    # ⚠ KEYED BY DOCUMENT AND PAGE, NEVER PAGE ALONE. Every document has a
    # `p001`, so a stem-only key silently overwrites: a 64-job run over
    # ../devr_pages produced 37 output files and reported success. At corpus
    # scale that discards most of the work while every count still looks right —
    # the exact shape of failure that large N hides.
    pp = pathlib.Path(path)
    stem = f"{pp.parent.name}/{pp.stem}"
    try:
        g = Image.open(path).convert("L")
        W, H = g.size                      # ORIGINAL dims — what unrotate needs
        r = g.rotate(angle, expand=True) if angle else g
        rw, rh = r.size
        s = MAXDIM / max(rw, rh)
        arr = np.array(r.resize((int(rw * s), int(rh * s)),
                                Image.LANCZOS).convert("RGB"))
        res, _ = _O(arr)
        items = []
        for it in (res or []):
            box, text = it[0], it[1]
            score = it[2] if len(it) > 2 else None
            pts = []
            for px, py in box:
                # 1. out of the 1600px frame, back into the rotated page
                ox, oy = px / s, py / s
                # 2. out of the rotated page, back onto the original
                ux, uy = unrotate(ox, oy, angle, W, H)
                pts.append([int(round(ux)), int(round(uy))])
            items.append({"text": text, "box": pts, "angle": angle,
                          "score": round(float(score), 4) if score is not None else None})
        return stem, angle, items, None
    except Exception as e:
        # ⚠ A FAILED PAGE IS COUNTED, NEVER SWALLOWED.
        return stem, angle, [], f"{type(e).__name__}: {str(e)[:110]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--angles", default="0,90,270")
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--threads", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    src = pathlib.Path(a.src)
    if not src.is_absolute():
        src = (HERE / a.src).resolve()
    angles = [int(x) for x in a.angles.split(",") if x.strip()]
    out = HERE / "out" / a.tag
    out.mkdir(parents=True, exist_ok=True)

    pages = sorted(p for p in src.rglob("*")
                   if p.suffix.lower() in (".png", ".tif", ".tiff", ".jpg"))
    if a.limit:
        pages = pages[:a.limit]
    # ⚠ ZERO PAGES IS A BROKEN PATH, NOT AN EMPTY JOB — the silent-success bug
    # that made Paddle "succeed" over nothing.
    if not pages:
        raise SystemExit(f"  NO PAGES under {src} — refusing to report a "
                         f"successful run over an empty set")

    jobs = [(str(p), ang) for p in pages for ang in angles]
    print(f"  RapidOCR · {src.name} · {len(pages)} pages × {len(angles)} angles "
          f"= {len(jobs)} reads · {a.procs}p × {a.threads}t")
    print(f"  -> out/{a.tag}\n", flush=True)

    got, errs, t0 = {}, [], time.time()
    with Pool(a.procs, initializer=_init, initargs=(a.threads,)) as pool:
        for i, (stem, ang, items, err) in enumerate(
                pool.imap_unordered(work, jobs, chunksize=1), 1):
            got.setdefault(stem, {})[ang] = items
            if err:
                errs.append((stem, ang, err))
            ch = sum(len(x["text"]) for x in items)
            print(f"  {i:>4}/{len(jobs)}  {stem}@{ang:<4} {len(items):>4} items "
                  f"{ch:>6} chars {'⚠ ' + err if err else ''}", flush=True)

    # ⚠ REFUSE TO REPORT SUCCESS OVER A COLLISION. If pages went missing between
    # the job list and the output, say so rather than print a tidy total.
    want = len({f"{pathlib.Path(p).parent.name}/{pathlib.Path(p).stem}"
                for p in (j[0] for j in jobs)})
    if len(got) != want:
        print(f"  ⚠ {want} distinct pages queued but {len(got)} collected — "
              f"KEY COLLISION, not a partial run")

    for stem, byang in sorted(got.items()):
        allit = [x for ang in angles for x in byang.get(ang, [])]
        f = out / f"{stem}.json"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(
            json.dumps({"page": stem, "angles": angles, "items": allit}, indent=1),
            encoding="utf-8")
        # ⚠ THE .txt IS ANGLE 0 ONLY. Concatenating angles into one text file is
        # what made ppv6-rot emit the page three times over.
        t = out / f"{stem}.txt"
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_text(" ".join(x["text"] for x in byang.get(angles[0], [])),
                     encoding="utf-8")

    el = time.time() - t0
    print(f"\n  {len(got)} pages · {el:.0f}s · {el/max(len(jobs),1):.2f}s per read")
    if errs:
        print(f"  ⚠ {len(errs)} failed read(s):")
        for s, ang, e in errs[:8]:
            print(f"      {s}@{ang}  {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
