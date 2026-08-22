"""Qwen3-VL over the 12-page stratified bench. Same pages Tesseract just ran.

⚠ SCORED ON LOCATION, NOT CHARACTERS — and that is a correction, not a shortcut.
The first version of this comparison scored transcription accuracy, which made
Tesseract look competitive (8/10 vs 9/10 on the film notary). But the pipeline
does not use the characters: the reader's job is to put a BOX on the field so a
reasoning model can crop it, magnify it, and read it there. Qwen wrote `1586`
for `1686` and that is irrelevant; it pointed at the stamp, which Tesseract
could not do at all.

⚠ AND THE POINTING TASK HAS A LOWER FLOOR THAN THE READING TASK. That is why
the ladder runs DOWNWARD (8B -> 4B -> 2B) rather than upward: the useful answer
is the smallest model that still points, because that is what sets the rent.

    python bench_qwen.py <model-tag>          e.g. 8B, 4B, 2B
"""
import json
import pathlib
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LLM = pathlib.Path("C:/Users/smile/llm")
BENCH = pathlib.Path("render/bench")

# ⚠ CONTEXT MUST BE CAPPED. Left at the model's default, llama.cpp reserved
# 38.6 GB for the KV cache and died before loading. Qwen3-VL advertises a 256k
# window; a page needs a few thousand tokens.
CTX = 8192
NPREDICT = 1100

NOISE = re.compile(
    r"^(ggml_|load_|llama_|clip_|build:|main:|encoding|decoding|print_info|"
    r"init_|graph_|Device |register_|warn|alloc|mtmd_|System\.|\d+\.\d+\.\d+\.\d+ [WIE] )")


def find(tag):
    m = sorted(LLM.glob(f"models/{tag}-*Instruct*.gguf"))
    p = sorted(LLM.glob(f"models/{tag}-mmproj*.gguf"))
    if not m or not p:
        return None, None
    return m[0], p[0]


def run(model, mmproj, img, prompt):
    cmd = [str(LLM / "bin/llama-mtmd-cli.exe"),
           "-m", str(model), "--mmproj", str(mmproj),
           "--image", str(img), "-p", prompt,
           "-ngl", "99", "-c", str(CTX), "-n", str(NPREDICT),
           "--temp", "0",
           # ⚠ REQUIRED FOR GROUNDING. llama.cpp warns that Qwen-VL needs >=1024
           # image tokens or coordinates degrade — and coordinates are the whole
           # point of using this model rather than Tesseract.
           "--image-min-tokens", "1024"]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    el = time.time() - t0
    body = [ln for ln in (r.stdout or "").splitlines() if ln.strip() and not NOISE.match(ln)]
    return "\n".join(body).strip(), el, r.returncode


PROMPT = ("Transcribe every word of text visible in this scanned document page, "
          "exactly as printed. Include any reel/page stamps, document numbers, "
          "names, dollar amounts and dates. Do not summarize or explain.")


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "8B"
    model, mmproj = find(tag)
    if not model:
        print(f"  no {tag} model in {LLM/'models'}")
        return
    print(f"  model  {model.name}  ({model.stat().st_size/1e9:.2f} GB)")
    print(f"  mmproj {mmproj.name}\n")

    man = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    out = BENCH / f"qwen{tag}"
    out.mkdir(exist_ok=True)

    print(f"  {'page':<44}{'sec':>7}{'words':>7}{'rc':>4}")
    tot = 0.0
    for m in man:
        txt, el, rc = run(model, mmproj, BENCH / m["file"], PROMPT)
        tot += el
        (out / (m["file"] + ".txt")).write_text(txt, encoding="utf-8")
        m[f"qwen{tag}_sec"] = round(el, 1)
        m[f"qwen{tag}_words"] = len(txt.split())
        print(f"  {m['file'][:43]:<44}{el:>7.1f}{len(txt.split()):>7}{rc:>4}")
    (BENCH / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")

    print(f"\n  total {tot:.0f}s for {len(man)} pages = {len(man)/tot:.3f} pages/s")
    print(f"  vs tesseract 0.38 pages/s single-stream "
          f"({0.38/(len(man)/tot):.0f}x faster)")
    print(f"  -> {out}")
    print(f"\n  ⚠ words alone prove nothing — a model can emit 900 fluent words")
    print(f"    of hallucination. Scoring happens against pages read by hand.")


if __name__ == "__main__":
    main()
