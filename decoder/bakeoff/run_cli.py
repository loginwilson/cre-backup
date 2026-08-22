"""ONE PAGE PER PROCESS, VIA llama-mtmd-cli. The path that does not wedge.

    python run_cli.py qwen35-2b-cli
    python run_cli.py qwen4b-cli --model 4B-Qwen3-VL-4B-Instruct-Q4_K_M.gguf --mmproj 4B-mmproj-F16.gguf

⚠ WHY NOT llama-server. Its vision path for Qwen3.5 hangs BEFORE generation,
intermittently, on a freshly started process - measured at roughly one page in
three. With `-np 1` that wedges the only slot and the client cannot time out,
because the connection stays open. Working around it with restart-per-page plus
retries produced a real pace of 304 SECONDS PER PAGE against ~45s of actual
inference: the overhead was six times the work.

llama-mtmd-cli loads the model, reads one image, prints, and exits. There is no
slot to corrupt and nothing to carry between pages. Model load is ~8-15s, paid
every page, and that is still far cheaper than one wedge.

⚠ THIS IS NOT THE SAME CONFIGURATION AS THE SERVER RUNS AND THE DIFFERENCE MUST
BE CARRIED WITH THE RESULT. The CLI in this build exposes no way to disable
reasoning - no --chat-template-kwargs, no --reasoning-budget - so Qwen3.5 thinks
out loud and reformats the page into bulleted markdown. The 4B was measured with
thinking OFF via the HTTP API.

That asymmetry does NOT invalidate recall, which is what this bench scores: the
scorer asks whether a fact was SURFACED anywhere in the output, and reasoning
text can only add haystack. It does mean the two runs are not a controlled
comparison of pipeline output, and it is why the earlier calibrated-prompt
result (86% vs 92%) is the relevant warning - a model that reorganises a page
LOSES facts. If 3.5 scores low here, "it was thinking" is a live explanation and
must be tested before concluding the model is worse.

⚠ STDOUT ONLY. The CLI writes model loading, timing and backend chatter to
stderr; mixing them into the transcription would put words like "llama_model_
loader" into the haystack and inflate nothing that is scored, but would corrupt
any later word-count or character-accuracy measure taken off these files.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
BIN = pathlib.Path(r"C:/Users/smile/llm/bin/llama-mtmd-cli.exe")
MODELS = pathlib.Path(r"C:/Users/smile/llm/models")
TMP = pathlib.Path(r"C:/Users/smile/AppData/Local/Temp/claude"
                   r"/C--Users-smile/7c5a3ccb-a88e-40cd-a587-cc575cf7a400"
                   r"/scratchpad/mtmd")

PROMPT = ("Transcribe every word of text visible in this scanned document page, "
          "exactly as printed. Include reel, record and page stamps, document "
          "numbers, names, dollar amounts and dates. Do not summarize.")


def prep(src, width):
    """⚠ 1400px, MEASURED. A render-width sweep put 1400 ahead of 1800, ahead of
    native 2536, ahead of 3200 - native scored WORST. The CLI would otherwise
    hand the model the full-resolution page."""
    from PIL import Image
    TMP.mkdir(parents=True, exist_ok=True)
    out = TMP / f"{src.parent.name}_{src.stem}_{width}.png"
    if out.exists():
        return out
    im = Image.open(src)
    if im.mode == "1":
        im = im.convert("L")
    if im.width != width:
        im = im.resize((width, int(im.height * width / im.width)),
                       Image.LANCZOS)
    im.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--model", default="35-2B-Q4_K_M.gguf")
    ap.add_argument("--mmproj", default="35-2B-mmproj-F16.gguf")
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--ntok", type=int, default=2048)
    ap.add_argument("--timeout", type=int, default=240)
    a = ap.parse_args()

    out = HERE / "out" / a.tag
    jobs = [(d.name, p)
            for d in sorted(x for x in (HERE / "pages").iterdir() if x.is_dir())
            for p in sorted(d.glob("p*.png"))]
    print(f"  {a.tag}: {a.model} via llama-mtmd-cli")
    print(f"  {len(jobs)} pages · {a.width}px · -n {a.ntok} · "
          f"{a.timeout}s cap\n", flush=True)

    rows, t0 = [], time.time()
    for i, (docn, pg) in enumerate(jobs, 1):
        d = out / docn
        d.mkdir(parents=True, exist_ok=True)
        f = d / (pg.stem + ".txt")
        if f.exists() and f.stat().st_size > 0:
            print(f"  {i:>2}/{len(jobs)} {docn[:14]:14}/{pg.name}  (on disk)",
                  flush=True)
            continue
        img = prep(pg, a.width)
        t = time.time()
        try:
            r = subprocess.run(
                [str(BIN), "-m", str(MODELS / a.model),
                 "--mmproj", str(MODELS / a.mmproj),
                 "--image", str(img), "-p", PROMPT,
                 "-ngl", "99", "--temp", "0", "-n", str(a.ntok),
                 "--no-warmup"],
                capture_output=True, timeout=a.timeout)
            txt = r.stdout.decode("utf-8", "replace").strip()
            status = "ok" if txt else "EMPTY"
        except subprocess.TimeoutExpired:
            txt, status = "", "TIMEOUT"
        except Exception as e:
            txt, status = "", f"{type(e).__name__}"
        el = time.time() - t

        if txt:
            f.write_text(txt, encoding="utf-8")
            print(f"  {i:>2}/{len(jobs)} {docn[:14]:14}/{pg.name}  "
                  f"{len(txt.split()):>5}w {el:>5.0f}s  {status}", flush=True)
        else:
            # ⚠ NO FILE. An empty .txt reads as "the engine found nothing",
            # which is the opposite of "the engine never answered", and resume
            # would skip it forever.
            print(f"  {i:>2}/{len(jobs)} {docn[:14]:14}/{pg.name}  "
                  f"NO OUTPUT {el:>5.0f}s  {status}", flush=True)
        rows.append({"doc": docn, "page": pg.name, "sec": round(el, 1),
                     "status": status, "words": len(txt.split()) if txt else 0})

    ok = [r for r in rows if r["status"] == "ok"]
    (out / "run.json").write_text(json.dumps(
        {"engine": a.tag, "model": a.model, "via": "llama-mtmd-cli",
         "width": a.width, "ntok": a.ntok, "thinking": "ON (CLI cannot disable)",
         "pages": rows, "sec": round(time.time() - t0, 1)}, indent=1),
        encoding="utf-8")
    print(f"\n  {len(ok)}/{len(rows)} pages · {(time.time()-t0)/60:.1f} min · "
          f"{sum(r['sec'] for r in ok)/max(len(ok),1):.0f}s per page "
          f"(includes model load every page)")
    for r in rows:
        if r["status"] != "ok":
            print(f"    ⚠ {r['doc']}/{r['page']}: {r['status']}")


if __name__ == "__main__":
    main()
