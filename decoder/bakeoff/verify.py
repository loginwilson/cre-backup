"""THE VERIFIER TEST. Does a reasoning pass over two OCR readings actually beat
those readings - and does it need the PIXELS to do it.

    python verify.py --url http://127.0.0.1:8080 --model local --engines qwen,rapidpool

⚠ THIS IS THE ONLY EXPERIMENT THAT TESTS THE ARCHITECTURE RATHER THAN THE PARTS.
Everything measured so far scores extractors. But the whole design rests on a
claim nothing has tested: that a model reading two disagreeing transcriptions
can produce a better one than either. If it cannot, the cascade is pointless
whatever the proposers score, and the answer is one VLM reading pixels.

Three configurations, same inputs, same scorer:

  UNION      both readings concatenated. No reasoning. The baseline to beat.
  TEXT       verifier gets the two readings and NO IMAGE. This is Option A -
             OCR to text reasoner - and its ceiling is closed-vocabulary repair.
  VISION     verifier gets the two readings AND the page image. Option B.

  VISION - TEXT is the measured value of the pixels. Everything else in this
  debate has been an estimate of that number; this measures it.

⚠ THE FIELD NAMES ARE NEVER SHOWN TO THE MODEL. It is asked for a corrected
transcription, not for a list of named fields. Handing it `notary` or `reel`
would tell it what to hunt for and quietly convert this into an easier task than
the real pipeline faces - and would flatter both configurations equally, hiding
the very gap being measured.

⚠ AND A VERIFIER CAN MAKE THINGS WORSE. It can drop a correct reading it
distrusts, or "fix" a correct one into a plausible wrong one. Regressions are
reported separately from gains, because a net +1 that is +4/-3 is a different
finding from a clean +1 - the first is a coin flip with extra steps.
"""
import argparse
import base64
import io
import json
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from PIL import Image

import score as S
from report import KEYS, OUT, text

HERE = pathlib.Path(__file__).parent
PAGES = HERE / "pages"

HEAD = ("Below are two independent OCR readings of the same scanned page, "
        "produced by different systems. They disagree in places and both "
        "contain errors.\n\n")

TAIL_VISION = (
    "\n\nUsing the page image as the authority, produce ONE corrected "
    "transcription of the page. Resolve every disagreement by looking at the "
    "image. Do not add any text that is not visible on the page. Where the page "
    "is genuinely illegible and neither reading is right, write [UNCLEAR] there "
    "rather than guessing. Output only the corrected transcription.")

TAIL_TEXT = (
    "\n\nYou cannot see the page. Using only these two readings, produce ONE "
    "corrected transcription. You may correct a word when the intended text is "
    "unambiguous from context or from standard legal and administrative "
    "phrasing. You may NOT invent or choose between values you cannot verify - "
    "names, dates, dollar amounts, reel or book numbers, block and lot numbers. "
    "Where the two readings disagree on such a value and you cannot tell which "
    "is right, write [UNCLEAR] there. Output only the corrected transcription.")


def encode(path, width=1000):
    im = Image.open(path)
    if im.mode == "1":
        im = im.convert("L")
    if im.width != width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def ask(url, model, prompt, b64, ntok, timeout):
    content = [{"type": "text", "text": prompt}]
    if b64:
        content.append({"type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"}})
    body = {"messages": [{"role": "user", "content": content}],
            "max_tokens": ntok, "temperature": 0}
    if model:
        body["model"] = model
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--model", default=None)
    ap.add_argument("--engines", default="qwen,rapidpool")
    ap.add_argument("--tag", default="verify")
    ap.add_argument("--docs", default="", help="comma-separated, default all")
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=2400)
    a = ap.parse_args()
    engs = a.engines.split(",")
    want = set(a.docs.split(",")) if a.docs else None

    docs = []
    for doc, keyf, label, share in KEYS:
        p = HERE / "keys" / keyf
        if not p.exists() or (want and doc not in want):
            continue
        key = {k: v for k, v in json.loads(p.read_text(encoding="utf-8")).items()
               if not k.startswith("_")}
        docs.append((doc, key, label, share))

    jobs = [(doc, key, page, mode)
            for doc, key, _, _ in docs for page in key
            for mode in ("text", "vision")]
    print(f"  verifier: {a.model or 'server default'}   proposers: {engs}")
    print(f"  {len(jobs)} calls ({len(jobs)//2} pages x text/vision)\n")

    def one(j):
        doc, key, page, mode = j
        out = OUT / a.tag / mode / doc
        out.mkdir(parents=True, exist_ok=True)
        f = out / (page + ".txt")
        if f.exists():
            return
        reads = "\n\n".join(
            f"--- READING {i+1} ---\n{text(e, doc, page).strip()[:1200]}"
            for i, e in enumerate(engs))
        prompt = HEAD + reads + (TAIL_VISION if mode == "vision" else TAIL_TEXT)
        b64 = encode(PAGES / doc / page) if mode == "vision" else None
        try:
            f.write_text(ask(a.url, a.model, prompt, b64, a.max_tokens, a.timeout),
                         encoding="utf-8")
        except Exception as e:
            print(f"    FAILED {doc} {page} {mode}: {type(e).__name__}")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(one, jobs))
    print(f"  {time.time()-t0:.1f}s\n")

    # ── score the three configurations ───────────────────────────────────
    def hay(doc, page, cfg):
        if cfg == "union":
            return S.norm(" ".join(text(e, doc, page) for e in engs))
        f = OUT / a.tag / cfg / doc / (page + ".txt")
        return S.norm(f.read_text(encoding="utf-8", errors="replace")
                      if f.exists() else "")

    CFGS = ["union", "text", "vision"]

    # ⚠ A MISSING OR TRUNCATED OUTPUT IS A CRASH, NOT A SCORE OF ZERO, AND
    # SCORING IT AS ZERO PRODUCED A COMPLETE FICTION ON THE FIRST RUN. Four of
    # seven vision calls died on an HTTPError (server context was 4096/slot; the
    # image plus two readings plus the output did not fit). The scorer read the
    # absent files as empty text and reported VISION at 2% and "the pixels are
    # worth -3.3 points" - a confident, precise, entirely invented result.
    #
    # So: a page counts only if EVERY configuration produced real output for it.
    # Comparing configs over different page sets is not a comparison.
    def ok(doc, page, c):
        if c == "union":
            return True
        f = OUT / a.tag / c / doc / (page + ".txt")
        # 40 chars: one vision reply came back as 4 bytes, which is a failure
        # wearing a success's clothes.
        return f.exists() and len(f.read_text(encoding="utf-8",
                                              errors="replace").strip()) >= 40

    usable, dropped = {}, []
    for doc, key, label, _ in docs:
        good = [p for p in key if all(ok(doc, p, c) for c in CFGS)]
        usable[doc] = good
        for p in key:
            if p not in good:
                dropped.append((label, p,
                                ",".join(c for c in CFGS if not ok(doc, p, c))))
    if dropped:
        print(f"  ⚠ {len(dropped)} page(s) EXCLUDED - a config produced no usable "
              f"output. Not scored as zero.")
        for label, p, which in dropped:
            print(f"      {label:<14}{p:<12}failed: {which}")
        print()
    if not any(usable.values()):
        print("  ⚠ NO page has output from every configuration. Nothing to "
              "compare - fix the failures and re-run.")
        return

    print(f"  {'document':<15}" + "".join(f"{c.upper():>16}" for c in CFGS))
    print("  " + "-" * 63)
    tot = {c: [0, 0] for c in CFGS}
    wtd = {c: 0.0 for c in CFGS}
    detail = {}
    for doc, key, label, share in docs:
        pages = usable[doc]
        if not pages:
            print(f"  {label:<15}  (all pages excluded)")
            continue
        cells = ""
        base = {}
        for c in CFGS:
            h = v = 0
            got = set()
            for page in pages:
                hy = hay(doc, page, c)
                for art in key[page]["artifacts"]:
                    if art["tier"] != "CRITICAL":
                        continue
                    v += 1
                    if S.found(hy, art):
                        h += 1
                        got.add((page, art["id"]))
            base[c] = got
            tot[c][0] += h; tot[c][1] += v
            wtd[c] += share * h / v if v else 0
            cells += f"{f'{h}/{v}':>10}{h/v*100 if v else 0:>6.0f}%"
        detail[label] = (base, key, doc, pages)
        print(f"  {label:<15}{cells}")

    print(f"\n  {'CORPUS-WEIGHTED':<15}" +
          "".join(f"{wtd[c]*100:>15.1f}%" for c in CFGS))
    print(f"\n  value of the pixels (VISION - TEXT): "
          f"{(wtd['vision']-wtd['text'])*100:+.1f} points")
    print(f"  value of reasoning at all (TEXT - UNION): "
          f"{(wtd['text']-wtd['union'])*100:+.1f} points")

    # ⚠ NET CHANGE HIDES THE RISK. Report gains and regressions separately.
    print(f"\n\n  ── GAINED vs LOST against UNION ──\n")
    for label, (base, key, doc, pages) in detail.items():
        for c in ("text", "vision"):
            gain = base[c] - base["union"]
            lost = base["union"] - base[c]
            print(f"  {label:<14}{c:<8}+{len(gain):<3} -{len(lost):<3}"
                  f"  net {len(gain)-len(lost):+d}")
            for page, aid in sorted(lost)[:6]:
                val = next(x["value"] for x in key[page]["artifacts"]
                           if x["id"] == aid)
                print(f"      LOST  {page:<11}{aid:<15}{str(val)[:32]}")
    print(f"\n  ⚠ A LOST artifact is a fact the raw OCR had and the verifier")
    print(f"    destroyed. If lost is comparable to gained, the verifier is not")
    print(f"    reasoning - it is rewriting, and the net score is luck.")


if __name__ == "__main__":
    main()
