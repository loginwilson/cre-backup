"""CAN THE VLM READ WHAT THE OCR CANNOT — the handwriting boundary.

⚠ WHY THIS EXISTS. After v6-tiny x 4 angles the OCR union reads 72 of 73 CRITICAL
artifacts. The single failure is `732441`, and cropping it settled what it is: a
HANDWRITTEN annotation in pen under the blackletter "Mortgage" — `7,32441 (USR 11836)`.
OCR returned `73241`, one digit short. That is not a threshold to tune; a print-trained
CTC recogniser is simply the wrong reader for a pen stroke.

So the residual gap is a MODALITY boundary, and it is the same boundary as the other
standing unread — the signatory, `signature -> person`, which the ledger has recorded as
UNREAD from the beginning. If the VLM crosses it, the architecture is right: OCR owns
printed characters and geometry, the VLM owns handwriting and structure.

⚠ THIS IS SCORED AGAINST A KNOWN ANSWER AND ASKED SEVERAL WAYS. A model shown a crop and
asked "what number is this" will always produce a number, so a single agreeing run is not
evidence. The value must be stable across repeats at temperature 0 AND the model must be
willing to say it cannot read one — the refusal control below is a crop of blank paper.
"""
from __future__ import annotations

import base64, json, pathlib, subprocess, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
MODELS = pathlib.Path(r"C:/Users/smile/llm/models")
SRV = pathlib.Path(r"C:/Users/smile/llm/bin/llama-server.exe")
URL = "http://127.0.0.1:8080"
MODEL = "4B-Qwen3-VL-4B-Instruct-Q4_K_M.gguf"
MMPROJ = "4B-mmproj-F16.gguf"


def server_up(timeout=240):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(URL + "/health", timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(3)
    return False


CTX = 8192   # overridden by vlm_res.py; see the ladder there for why this matters


def start(ctx=None):
    """⚠ CONTEXT IS A PARAMETER NOW, NOT A CONSTANT. The 8192 was inherited with the
    rest of the server invocation and never varied, so "the image was too big" and
    "the window was too small" were never separable. The ladder at 8192 crashed at
    3,311 image tokens — well UNDER the window — which already argues the wall is
    memory, not context. Raising it tests that directly: a larger KV cache costs MORE
    RAM, so if memory is the limit this makes it worse, and that is a real answer."""
    try:
        with urllib.request.urlopen(URL + "/health", timeout=3) as r:
            if r.status == 200:
                print("  server already up")
                return True
    except Exception:
        pass
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process llama-server -ErrorAction SilentlyContinue | "
                    "Stop-Process -Force"], capture_output=True)
    time.sleep(2)
    subprocess.Popen([str(SRV), "-m", str(MODELS / MODEL),
                      "--mmproj", str(MODELS / MMPROJ), "-ngl", "0",
                      "-c", str(ctx or CTX), "-np", "1", "--host", "127.0.0.1",
                      "--port", "8080", "-fa", "off"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("  starting llama-server (CPU, 4B) ...")
    return server_up()


def ask(img, prompt, ntok=96, timeout=300):
    """⚠ cache_prompt False and thinking off — both are load-bearing, see route.py."""
    b64 = base64.b64encode(pathlib.Path(img).read_bytes()).decode()
    body = {"model": "qwen", "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
            "max_tokens": ntok, "temperature": 0, "cache_prompt": False,
            "chat_template_kwargs": {"enable_thinking": False},
            "reasoning_effort": "none"}
    req = urllib.request.Request(URL + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.load(r)
    ch = j["choices"][0]
    txt = (ch["message"].get("content") or "").strip()
    if not txt:
        raise RuntimeError(f"empty (finish={ch.get('finish_reason')})")
    return txt


# ⚠ THE REFUSAL CONTROL IS NOT OPTIONAL. Without it, "it read the number" and
# "it emits a number for any image" are indistinguishable.
PROMPTS = [
    ("verbatim", "Transcribe the handwritten text in this image exactly as written. "
                 "Reply with the transcription only. If you cannot read it, reply UNREADABLE."),
    ("digits", "There is a handwritten number in this image. Reply with that number's "
               "digits only, no other text. If no handwritten number is legible, reply NONE."),
    ("ocr_check", "An OCR engine read the handwritten number in this image as '73241'. "
                  "Look at the image and reply with the correct digits only, or AGREE if "
                  "73241 is right."),
]


def main():
    if not start():
        print("  server did not come up"); return 1
    crop = HERE / "_crop_732441.png"
    if not crop.exists():
        print(f"  missing {crop}"); return 1
    blank = HERE / "_crop_blank.png"
    from PIL import Image
    Image.new("RGB", (600, 200), "white").save(blank)

    print(f"\n  truth = 732441   (handwritten '7,32441 (USR 11836)')")
    print(f"  OCR   = 73241    (v6-tiny, one digit short)\n")
    for name, p in PROMPTS:
        for rep in range(2):
            try:
                a = ask(crop, p)
            except Exception as e:
                a = f"ERR {type(e).__name__}: {str(e)[:60]}"
            hit = "  <== 732441" if "732441" in a.replace(",", "").replace(" ", "") else ""
            print(f"  {name:<11} run{rep+1}  {a[:88]!r}{hit}")
    print()
    for rep in range(2):
        try:
            a = ask(blank, PROMPTS[1][1])
        except Exception as e:
            a = f"ERR {type(e).__name__}"
        print(f"  {'CONTROL':<11} run{rep+1}  {a[:88]!r}   (blank paper — must say NONE)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
