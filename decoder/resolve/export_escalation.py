"""SHIP THE CROPS, NOT THE CORPUS. A portable escalation package.

    python export_escalation.py --doc 2015022400608001
    python export_escalation.py --all --context 3

Builds a self-contained folder someone else can run a stronger model against
without this repo, the page images, or any of the pipeline:

    _escalation_export/
        manifest.jsonl     one row per open run - the ANSWER KEY SIDE
        prompts.jsonl      what the model is actually shown - NO candidates
        crops/             the PNGs
        read_crops.py      the recipient runs this
        README.md

⚠ ONLY WHAT IS STILL OPEN GETS SENT. Runs both channels agreed on are settled
and cost nothing to re-read but buy nothing either. Runs marked `unaligned` are
NOT sent: both readers already read that text, they just emitted it in
different order, so a third model would be answering a question nobody asked.
On the digital pilot that filter alone took the queue from 114 runs to 80.

⚠ THE MODEL IS NOT SHOWN WHAT THE OTHER ENGINES READ, AND THIS IS THE WHOLE
POINT OF THE FILE. Handing it "is this 107-28 or 607-28?" turns a reading into
a multiple-choice question, and a language model answers that from a prior
about what addresses look like - it will pick the plausible one, be right most
of the time, and be wrong exactly on the unusual values that matter. A BLIND
read of the pixels is independent evidence; a forced choice between two
candidates is not evidence at all. So candidates live in manifest.jsonl, which
stays home, and prompts.jsonl carries the image alone.

⚠ A CROP TOO TIGHT TO READ IS A FAILED TEST, NOT A HARD PAGE. The pilot cut a
57px box across two stacked lines and clipped the upper one - the model would
have been marked wrong for a defect in the crop. Every crop here is padded to
whole lines with `--context` lines of surroundings, and anything still thinner
than MIN_H is grown from its centre.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
EV = HERE / "_evidence"
PAGES = HERE.parent / "bakeoff" / "pages"

MIN_H = 40          # below this a crop is unreadable even when correctly placed
PAD_X = 24
LINE_H = 46         # approx text line height at the 1800px render


READ_SCRIPT = '''"""Read every crop with a vision model. Run this, send back answers.jsonl.

    python read_crops.py --url http://localhost:8080 --model qwen3.8-27b

Works against any OpenAI-compatible endpoint (llama.cpp server, vLLM, Ollama).
Nothing here needs the original corpus - the crops are self-contained.

⚠ DO NOT ADD THE OTHER ENGINES' READINGS TO THE PROMPT. They are deliberately
not in this folder. The value of this pass is that it is INDEPENDENT; showing
it what another model guessed converts it into agreement with that guess.
"""
import argparse, base64, json, pathlib, sys, time, urllib.request

HERE = pathlib.Path(__file__).parent

def ask(url, model, b64, prompt, timeout=180):
    body = {"model": model, "temperature": 0, "max_tokens": 256,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64}"}}]}]}
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    return j["choices"][0]["message"]["content"].strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8080")
    ap.add_argument("--model", default="local")
    ap.add_argument("--out", default="answers.jsonl")
    a = ap.parse_args()
    rows = [json.loads(l) for l in
            (HERE / "prompts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    done = set()
    outp = HERE / a.out
    if outp.exists():
        for l in outp.read_text(encoding="utf-8").splitlines():
            if l.strip():
                done.add(json.loads(l)["item_id"])
    print(f"  {len(rows)} crops, {len(done)} already answered")
    with outp.open("a", encoding="utf-8") as fh:
        for i, r in enumerate(rows, 1):
            if r["item_id"] in done:
                continue
            p = HERE / r["crop"]
            b64 = base64.b64encode(p.read_bytes()).decode()
            t = time.time()
            try:
                txt, err = ask(a.url, a.model, b64, r["prompt"]), None
            except Exception as e:
                txt, err = None, f"{type(e).__name__}: {e}"
            fh.write(json.dumps({"item_id": r["item_id"], "reading": txt,
                                 "error": err, "sec": round(time.time()-t, 1),
                                 "model": a.model}) + "\\n")
            fh.flush()
            print(f"  {i}/{len(rows)} {r['item_id']}  {(txt or err or '')[:60]}",
                  flush=True)
    print(f"\\n  -> {outp}   send this file back")

if __name__ == "__main__":
    main()
'''

README = """# Escalation crops — independent re-read

These are small image crops cut from NYC land records. Each one is a spot where
two independent readers (a vision model and an OCR engine) failed to agree, or
where only one of them saw anything at all.

**What we need:** an independent reading of each crop by a stronger model.

## Run it

```
python read_crops.py --url http://localhost:8080 --model <your-model-name>
```

Any OpenAI-compatible endpoint works — llama.cpp `llama-server`, vLLM, Ollama.
It resumes if interrupted, so you can stop and restart it.

Send back `answers.jsonl`. Nothing else is needed.

## Please do not

- **Do not tell the model what the other engines read.** Those readings are
  deliberately not in this folder. The whole value of this pass is that it is
  independent — a model shown two candidates picks the plausible one instead of
  reading the pixels, which is precisely the failure we are testing for.
- **Do not clean up, correct, or normalise the output.** If it reads
  `MORTGAGFE` we want `MORTGAGFE`.
- **Do not skip crops that look illegible.** `[ILLEGIBLE]` is a useful answer
  and an honest one. A guess is worse than a gap.

## What is in here

| file | what |
|---|---|
| `prompts.jsonl` | one row per crop: `item_id`, `crop`, `prompt` |
| `crops/` | the PNGs |
| `read_crops.py` | the runner |
| `answers.jsonl` | what you produce |
"""

PROMPT = ("Transcribe the text in this image exactly as it appears, including "
          "handwriting, stamps and numbers. Output only the characters that are "
          "physically present. Do not add labels, headings or commentary. "
          "If it cannot be read with confidence, output [ILLEGIBLE].")


def grow(box, img_w, img_h, context_lines):
    x0, y0, x1, y1 = box
    if y1 - y0 < MIN_H:
        c = (y0 + y1) // 2
        y0, y1 = c - MIN_H // 2, c + MIN_H // 2
    pad = LINE_H * context_lines
    return (max(0, x0 - PAD_X), max(0, y0 - pad),
            min(img_w, x1 + PAD_X), min(img_h, y1 + pad))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--context", type=int, default=1,
                    help="lines of surrounding context to include")
    ap.add_argument("--out", default="_escalation_export")
    a = ap.parse_args()

    from PIL import Image

    docs = ([p.stem.replace(".located", "") for p in EV.glob("*.located.json")]
            if a.all else [a.doc])
    if not docs or docs == [None]:
        raise SystemExit("  need --doc or --all")

    out = HERE / a.out
    crops = out / "crops"
    crops.mkdir(parents=True, exist_ok=True)
    man, prm = [], []
    skipped_unaligned = 0

    for doc in docs:
        lf = EV / f"{doc}.located.json"
        if not lf.exists():
            print(f"  {doc}: no .located.json - run locate.py first"); continue
        rows = json.loads(lf.read_text(encoding="utf-8"))
        img_cache = {}
        for r in rows:
            # ⚠ SEE THE MODULE DOCSTRING. Order artefacts are not open questions.
            if r["status"] not in ("disputed", "single_channel"):
                skipped_unaligned += 1
                continue
            pf = PAGES / doc / f"{r['page']}.png"
            if not pf.exists():
                continue
            if r["page"] not in img_cache:
                img_cache[r["page"]] = Image.open(pf)
            im = img_cache[r["page"]]
            bx = grow(r["box"], im.width, im.height, a.context)
            item = f"{doc}_{r['page']}_r{r['run_index']:03d}"
            name = f"{item}.png"
            im.crop(bx).save(crops / name)
            # HOME SIDE - carries the candidates, never shipped into the prompt
            man.append({"item_id": item, "doc_id": doc, "page": r["page"],
                        "run_index": r["run_index"], "status": r["status"],
                        "n_tokens": r["n_tokens"], "box": r["box"],
                        "crop_box": list(bx), "how_located": r.get("how"),
                        "candidates": {"vlm": r.get("vlm"), "ocr": r.get("ocr")},
                        "crop": f"crops/{name}"})
            # SHIPPED SIDE - image and instruction only
            prm.append({"item_id": item, "crop": f"crops/{name}",
                        "prompt": PROMPT})

    (out / "manifest.jsonl").write_text(
        "\n".join(json.dumps(m) for m in man), encoding="utf-8")
    (out / "prompts.jsonl").write_text(
        "\n".join(json.dumps(p) for p in prm), encoding="utf-8")
    (out / "read_crops.py").write_text(READ_SCRIPT, encoding="utf-8")
    (out / "README.md").write_text(README, encoding="utf-8")

    # ⚠ PROVE THE SHIPPED HALF CANNOT LEAK AN ANSWER. This package is worthless
    # if a candidate reading rides along in the prompts file.
    ship = (out / "prompts.jsonl").read_text(encoding="utf-8")
    leaked = [m["item_id"] for m in man
              for v in m["candidates"].values()
              if v and len(v) > 3 and v in ship]
    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"  exported {len(man)} crops from {len(docs)} document(s)")
    print(f"  skipped  {skipped_unaligned} unaligned runs (both channels read them)")
    print(f"  package  {size/1e6:.1f} MB  -> {out}")
    print(f"  leak check: {'FAIL - ' + str(leaked[:3]) if leaked else 'clean, no candidate text in prompts.jsonl'}")


if __name__ == "__main__":
    main()
