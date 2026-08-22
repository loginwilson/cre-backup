"""Read every crop with a vision model. Run this, send back answers.jsonl.

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
                                 "model": a.model}) + "\n")
            fh.flush()
            print(f"  {i}/{len(rows)} {r['item_id']}  {(txt or err or '')[:60]}",
                  flush=True)
    print(f"\n  -> {outp}   send this file back")

if __name__ == "__main__":
    main()
