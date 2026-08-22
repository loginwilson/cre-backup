"""OCR LINES -> REGIONS, for a whole document. The 4B's first job.

    python doc_route.py --doc 2005082901835001

⚠ WHAT THIS STAGE IS FOR. OCR produces transcription and geometry and has no opinion
about meaning; it cannot tell a recording stamp from a granting clause. The VLM supplies
exactly that judgment and nothing else — it reads the IMAGE and says which region each
OCR line belongs to. Login, 2026-08-17: "ocr gives you transcription but no logic on what
should go into data table, the 4b in this case is the reasoning on extraction."

⚠ THE INTERFACE IS THE GUARD, AND IT IS WHY THIS SURVIVES A MODEL SWAP. The model returns
`{"<line number>": "<region>"}` and NOTHING else. It never emits characters, so invented
text is unrepresentable; it never emits coordinates, so an invented box is impossible; a
line number outside range is arithmetic to catch. The same interface constrains a 27B on
Torch or a 3.5-8B in a lab exactly as it constrains this 4B — the rules are about the
shape of the answer, not the size of the model.

⚠ KEYED BY LINE, NEVER BY REGION. Region-keyed output `{region: [lines]}` let the model
read the region list as a CHECKLIST and fill all eleven — 70 assignments for 44 lines,
`signature` and `notary` handed the SAME line. Line-keyed took duplicates 27 -> 0 and
regions 11 -> 6, and ran 35% faster. Make the bad state unrepresentable, do not detect it.

⚠ UNPLACED IS REPORTED, NEVER SILENTLY DROPPED. A line the model does not assign is a
line the harness must know about; silence there reads as "nothing there".

⚠ AND FOUR ANGLES MEAN DUPLICATE LINES. The OCR union runs 0/90/180/270, so the same text
arrives up to four times with different boxes. Sending all of them wastes the window and
invites the model to place the garbled copies. Duplicates are collapsed HERE, keeping the
upright reading where one exists, because that is the one whose box is native.
"""
from __future__ import annotations

import argparse, json, pathlib, re, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import route as RT


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", str(s or "").lower())


def collapse(lines):
    """One entry per distinct text, preferring the upright pass.

    ⚠ PREFER ANGLE 0 FOR THE BOX, NOT MERELY FOR THE TEXT. A rotated pass's box is
    unrotated arithmetically and is correct, but the upright detection is the one that
    was never transformed, so it is the box to keep when both exist.
    """
    best = {}
    for ln in lines:
        k = norm(ln.get("text"))
        if not k:
            continue
        cur = best.get(k)
        if cur is None or (cur.get("angle") and not ln.get("angle")):
            best[k] = ln
    out = []
    for i, ln in enumerate(best.values()):
        out.append({"i": i, "text": ln["text"], "box": ln.get("box"),
                    "angle": ln.get("angle", 0)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--ntok", type=int, default=900)
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None

    ocr_dir = HERE / "out" / "_ocr" / a.doc
    pages = sorted(ocr_dir.glob("p*.json"))
    if not pages:
        print(f"  no OCR under {ocr_dir} — run doc_ocr.py first"); return 1
    pgdir = HERE / "pages" / a.doc
    out = HERE / "out" / "_route" / a.doc
    out.mkdir(parents=True, exist_ok=True)

    print(f"  ROUTE {a.doc} · {len(pages)} pages · 4B places OCR lines into regions")
    t0 = time.time()
    for pf in pages:
        d = json.loads(pf.read_text(encoding="utf-8"))
        lines = collapse(d["lines"])
        img = pgdir / f"{d['page']}.png"
        if not img.exists():
            print(f"    {d['page']}  no render at {img}"); continue
        # ⚠ the render is a DERIVED CACHE of the document container, never the source
        im = Image.open(img).convert("RGB")
        if im.width > a.width:
            im = im.resize((a.width, round(im.height * a.width / im.width)),
                           Image.LANCZOS)
        tmp = HERE / f"_route_tmp.png"
        im.save(tmp)

        t = time.time()
        try:
            raw = RT.ask_http(tmp, lines, a.url, a.ntok, a.timeout)
        except Exception as e:
            print(f"    {d['page']}  {type(e).__name__}: {str(e)[:60]} — restarting")
            RT.restart_server("4B-Qwen3-VL-4B-Instruct-Q4_K_M.gguf",
                              "4B-mmproj-F16.gguf", a.url, 0, 8192)
            try:
                raw = RT.ask_http(tmp, lines, a.url, a.ntok, a.timeout)
            except Exception as e2:
                print(f"    {d['page']}  FAILED twice: {type(e2).__name__}")
                continue
        m = re.search(r"\{.*\}", raw, re.S)
        placed = {}
        bad = 0
        if m:
            try:
                j = json.loads(m.group(0))
            except Exception:
                j = {}
            for k, v in j.items():
                # ⚠ AN OUT-OF-RANGE LINE NUMBER IS ARITHMETIC, NOT JUDGMENT.
                try:
                    i = int(k)
                except Exception:
                    bad += 1; continue
                if not (0 <= i < len(lines)):
                    bad += 1; continue
                placed.setdefault(str(v), []).append(i)
        seen = {i for v in placed.values() for i in v}
        rec = {"doc": a.doc, "page": d["page"], "ocr": "v6tiny-ma4",
               "vlm": "4B-Qwen3-VL-4B-Instruct-Q4_K_M.gguf",
               "n_lines": len(lines), "seconds": round(time.time() - t, 1),
               "placed": placed,
               "integrity": {"unplaced": len(lines) - len(seen),
                             "out_of_range": bad},
               "lines": lines}
        (out / f"{d['page']}.json").write_text(json.dumps(rec, indent=1),
                                               encoding="utf-8")
        print(f"    {d['page']}  {len(lines):>3} lines -> {len(placed)} regions "
              f"· unplaced {rec['integrity']['unplaced']:>3} · bad {bad} "
              f"· {rec['seconds']:>5.1f}s")
    print(f"  {time.time()-t0:.1f}s -> out/_route/{a.doc}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
