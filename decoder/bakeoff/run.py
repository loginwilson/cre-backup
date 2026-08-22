"""ONE ENGINE OVER THE THREE KEYED DOCUMENTS. Model-agnostic on purpose.

    python run.py glm-ocr   --model zai-org/GLM-OCR          --url http://127.0.0.1:8000
    python run.py glm-ocr   --model zai-org/GLM-OCR          --url ... --rot
    python run.py qwen38-27b --model Qwen/Qwen3.8-27B        --url http://127.0.0.1:8000

Every candidate here (GLM-OCR, PaddleOCR-VL, FireRed-OCR, Qwen3.5/3.8) serves
behind vLLM's OpenAI-compatible endpoint, so ONE client covers all of them and
no per-model Python API has to be guessed at. Start the server yourself:

    vllm serve <hf-id> --limit-mm-per-prompt image=1 --port 8000

⚠ EVERY ENGINE GETS THE SAME MINIMAL PROMPT, AND THAT IS A FINDING, NOT
LAZINESS. A domain-calibrated prompt was measured against the generic one on
BK_6730047100023 (2026-08-12): it scored 86% against the generic prompt's 92%,
emitted 830 MORE words to hit 5 FEWER facts, and lost five artifacts the generic
prompt had caught. Naming the fields turned the model from a transcriber into a
form-filler. Per-engine prompt tuning would also make the results
non-transferable - a prompt tuned on 7 pages of one 1967 mortgage says nothing
about 17 million documents.

⚠ ROTATION IS A SEPARATE VARIANT BECAUSE IT IS THE ONLY THING THAT WORKS. Same
test showed the backer block - recording tax, City Register stamp, county - is
recovered by rotating the page and by NOTHING else: not by a longer prompt, not
by a dedicated stamp-only second pass. You cannot talk a model into reading
sideways text. So each engine is scored twice, upright and upright+90+270, and
the delta between them is the real cost of the historical eras.

⚠ WALL TIME IS RECORDED PER ENGINE AND IS NOT COMPARABLE ACROSS MACHINES. It is
here to convert into core-seconds/page for the corpus projection, which is the
only form in which a throughput number means anything.
"""
import argparse
import base64
import io
import json
import pathlib
import time
from concurrent.futures import ThreadPoolExecutor
import os
import urllib.request

from PIL import Image

HERE = pathlib.Path(__file__).parent
PAGES = HERE / "pages"
OUT = HERE / "out"

# ⚠ THE SAME SENTENCE FOR EVERYONE. Measured to beat every richer variant tried.
PROMPT = ("Transcribe every word of text visible in this scanned document page, "
          "exactly as printed. Include reel, record and page stamps, document "
          "numbers, names, dollar amounts and dates. Do not summarize.")

# ⚠ THE BASELINE PROMPT BANS COMPRESSION BUT NOT INVENTION, AND THAT GAP IS
# MEASURED, NOT SUSPECTED. "Do not summarize" forbids saying less than the page;
# nothing in it forbids saying MORE. On 2015022400608001 p006 the VLM emitted
#     **Document Title**  **Header**  **Body Text**  **Formalities**
#     **Signature Block**  **Stamp**  **Signature Block (Bottom)**
# - nine markdown section labels describing the LAYOUT, none of them printed
# anywhere on the page. The crop of that region reads "LR-205k (E) 10-21-2011 /
# ACKNOWLEDGEMENTS" and nothing else.
#
# ⚠ ONLY THE SECOND CHANNEL COULD SEE IT. Paddle produced 0 such tokens across
# 34 pages, because an OCR engine reports regions it detected and cannot invent
# a phrase. That asymmetry - the VLM fabricates, the OCR garbles - is the whole
# reason the weaker engine stays in the pipeline.
#
# ⚠ THIS VARIANT IS A HYPOTHESIS AND HAS NOT BEEN SCORED. The baseline above
# earned its place by beating every richer prompt tried, so a longer instruction
# is exactly the shape of change that has regressed before. Run it against the
# answer keys and compare BOTH fabricated-token count AND field accuracy before
# it replaces anything:  python run.py --prompt-variant strict
PROMPT_STRICT = (
    "Transcribe every word of text visible in this scanned document page, "
    "exactly as printed. Include reel, record and page stamps, document "
    "numbers, names, dollar amounts and dates. "
    "Output only characters that are physically printed, typed, stamped or "
    "handwritten on the page. Do not add section headings, labels, titles or "
    "any description of the layout. Do not mark up or format the output. "
    "If part of the page is illegible, write [ILLEGIBLE] rather than "
    "describing it. Do not summarize.")

PROMPTS = {"baseline": PROMPT, "strict": PROMPT_STRICT}

# ⚠ SOME OCR-SPECIALIST MODELS IGNORE THE USER PROMPT AND RUN A FIXED TASK
# HEADER (PaddleOCR-VL and dots.ocr both document their own). Where a model card
# specifies one, pass it with --prompt rather than editing this file, and RECORD
# IT IN THE RESULT so the run is reproducible. Do not invent one from memory.


def encode(path, angle=0, width=1400):
    """⚠ 1400px, MEASURED, NOT ASSUMED. A render-width sweep on the film document
    put 1400 ahead of 1800, ahead of native 2536, ahead of 3200 - the NATIVE
    resolution scored WORST. Downsampling is not a compromise here; more pixels
    per page cost more and read less.
    """
    im = Image.open(path)
    if im.mode == "1":
        im = im.convert("L")
    if angle:
        im = im.rotate(angle, expand=True)
    if im.width != width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _key():
    """API key from the environment, or from the project's gitignored env file.

    ⚠ NEVER PRINTED, NEVER LOGGED, NEVER WRITTEN INTO run.json. Only its
    PRESENCE is ever reported. A hosted endpoint is the only way to measure a
    27B honestly from this machine - local would mean a Q2 quant (12.3 GB
    resident against 15.7 GB total RAM) running at ~1 tok/s, which measures a
    crippled model, not the one that would run on Torch.
    """
    for k in ("OPENROUTER_API_KEY", "GROQ_API_KEY", "TOGETHER_API_KEY",
              "FIREWORKS_API_KEY", "DEEPINFRA_API_KEY", "NEBIUS_API_KEY",
              "VLLM_API_KEY"):
        v = os.environ.get(k)
        if v:
            return v
    for f in (pathlib.Path("C:/dev/acris-decoder.env"), HERE / ".env"):
        if f.exists():
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                if "=" in line and line.split("=", 1)[0].strip().endswith("API_KEY"):
                    v = line.split("=", 1)[1].strip()
                    return v.strip('"').strip("'")
    return None


class EmptyReply(RuntimeError):
    """⚠ AN HTTP 200 CARRYING AN EMPTY STRING IS A FAILURE, NOT A TRANSCRIPTION.

    Measured 2026-08-12 on Qwen3.5-2B: 5 of 8 pages wrote a ZERO-BYTE .txt in
    ~85s each while 3 pages read cleanly. The calls all succeeded - the model
    spent the whole token budget inside its reasoning block and emitted no
    content. run.py's `except` guard never fired because nothing was thrown, so
    the empty files landed on disk looking exactly like "this engine read the
    page and found nothing" - the opposite finding, and the one the scorer would
    have reported as 0%.

    It is also the resume trap: the harness skips any page whose .txt EXISTS, so
    a zero-byte file is permanently "done" and never retried.
    """


def ask(url, model, b64, prompt, ntok, timeout, think=False):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": ntok, "temperature": 0,
        # ⚠ KV-CACHE REUSE ACROSS DIFFERENT IMAGES WEDGES THE SLOT PERMANENTLY.
        # Server log, measured 2026-08-12: pages 1 and 2 complete normally, then
        #   W find_slot: non-consecutive token position 43 after 42 ...
        #   W find_slot: non-consecutive token position 105 after 43 ...
        #   I launch_slot_: task 984 | processing task
        # and the log ENDS - no "prompt processing" line ever follows, so it is
        # stuck in image encoding, not generating slowly. llama.cpp tries to
        # reuse the cached prefix from the previous request, but each request
        # carries a DIFFERENT image, so positions go non-consecutive and the
        # slot never recovers. With -np 1 that wedges the only slot, /health
        # stops answering, and every later request queues behind it forever -
        # which is why two earlier hypotheses were falsely disconfirmed.
        "cache_prompt": False}
    if not think:
        # ⚠ TRANSCRIPTION IS NOT A REASONING TASK AND THINKING ACTIVELY BREAKS
        # IT. Qwen3.x ships thinking ON by default; on a dense scan the model
        # narrates what it sees until it hits the cap. Both spellings are sent
        # because llama.cpp and vLLM disagree on which they honour, and an
        # unknown key is ignored rather than fatal.
        body["chat_template_kwargs"] = {"enable_thinking": False}
        body["reasoning_effort"] = "none"
    hdr = {"Content-Type": "application/json"}
    k = _key()
    if k:
        hdr["Authorization"] = f"Bearer {k}"
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(), headers=hdr)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.load(r)
    ch = j["choices"][0]
    txt = (ch["message"].get("content") or "").strip()
    if txt:
        return txt
    # Diagnose rather than return "": name WHY it was empty so the run.json says
    # "thinking ate the budget" instead of "the page was blank".
    why = ch.get("finish_reason") or "?"
    rc = len((ch["message"].get("reasoning_content") or ""))
    u = j.get("usage") or {}
    raise EmptyReply(f"empty content (finish_reason={why}, "
                     f"reasoning_chars={rc}, completion_tokens="
                     f"{u.get('completion_tokens')})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--model", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--prompt", default=PROMPT)
    ap.add_argument("--rot", action="store_true",
                    help="also run 90 and 270 (historical eras need it)")
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--think", action="store_true",
                    help="leave the model's reasoning mode ON (default: off)")
    a = ap.parse_args()

    tag = a.engine + ("-rot" if a.rot else "")
    # ⚠ SWEEP ZERO-BYTE FILES BEFORE STARTING. They are the wreckage of a failed
    # call, not results, and leaving them would make resume skip those pages.
    dead = [f for f in (OUT / tag).rglob("*.txt") if f.stat().st_size == 0] \
        if (OUT / tag).exists() else []
    for f in dead:
        f.unlink()
    if dead:
        print(f"  cleared {len(dead)} zero-byte file(s) from a previous run")
    angles = (0, 90, 270) if a.rot else (0,)
    jobs = []
    for doc in sorted(p for p in PAGES.iterdir() if p.is_dir()):
        for pg in sorted(doc.glob("p*.png")):
            for ang in angles:
                jobs.append((doc.name, pg, ang))

    print(f"  {tag}: {a.model}")
    print(f"  endpoint {a.url}   auth {'yes' if _key() else 'NONE (local server?)'}")
    print(f"  {len(jobs)} calls over {len(set(j[1] for j in jobs))} pages "
          f"({len(angles)} orientation(s)), {a.workers} concurrent\n")
    t0 = time.time()
    errs = []

    def one(j):
        docn, pg, ang = j
        d = OUT / tag / docn
        d.mkdir(parents=True, exist_ok=True)
        f = d / (pg.stem + (f"_r{ang}" if ang else "") + ".txt")
        # ⚠ EXISTS IS NOT DONE IF IT IS EMPTY. Resume skips finished pages, so a
        # zero-byte file left by an earlier bug would be skipped forever.
        if f.exists() and f.stat().st_size > 0:
            return
        try:
            txt = ask(a.url, a.model, encode(pg, ang), a.prompt,
                      a.max_tokens, a.timeout, a.think)
        except Exception as e:
            # ⚠ A FAILED CALL MUST LEAVE NO FILE. An empty .txt is
            # indistinguishable from an engine that read the page and found
            # nothing, and those are opposite findings.
            errs.append((docn, pg.name, ang, f"{type(e).__name__}: {e}"))
            return
        f.write_text(txt, encoding="utf-8")

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(one, jobs))
    el = time.time() - t0

    npages = len(set(j[1] for j in jobs))
    meta = OUT / tag / "run.json"
    meta.write_text(json.dumps({
        "engine": a.engine, "model": a.model, "rot": a.rot,
        "thinking": a.think,
        "prompt": a.prompt, "max_tokens": a.max_tokens,
        "workers": a.workers, "calls": len(jobs), "pages": npages,
        "errors": errs, "sec": round(el, 1),
        "sec_per_page": round(el / npages, 2),
    }, indent=1), encoding="utf-8")

    print(f"  {el:.1f}s   {el/npages:.2f} s/page   {len(errs)} failed call(s)")
    for e in errs[:10]:
        print(f"    FAILED {e[0]} {e[1]} r{e[2]}: {e[3][:80]}")
    if errs:
        print(f"  ⚠ {len(errs)} pages have NO output and will score as absent.")
    print(f"  -> {OUT / tag}")


if __name__ == "__main__":
    main()
