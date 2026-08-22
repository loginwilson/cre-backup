"""ONE DOCUMENT, END TO END, OPTIMISED FOR SPEED. doc_id -> endpoint -> Qwen.

    python qwen_doc.py <doc_id> [max_pages]

⚠ FOUR LEVERS, AND THREE OF THEM ARE UNDOING MY OWN MISTAKES.

  1. FETCH OVERLAPS OCR.  The first pipeline fetched all N pages, THEN OCR'd all
     N — 13.5s + 7.8s serial on a 38-page document. They are different resources;
     running them concurrently costs the max, not the sum.

  2. RENDER AT 1000px, NOT 1400.  I raised the width mid-session and roughly
     doubled the vision-token count, then wondered why Qwen got slower. The
     earlier 36-49s/page runs were at 1000px.

  3. ASK FOR ARTIFACTS, NOT A TRANSCRIPTION.  This is the big one. "Transcribe
     every word" forces the model to GENERATE the whole page — 878 tokens on a
     dense page, ~98 seconds of purely sequential decoding. The pipeline never
     consumes that prose; it consumes locations. Asking for the fields directly
     cuts generation ~8x.

  4. MODEL STAYS RESIDENT.  The CLI reloaded 2.4 GB per page. A server pays it
     once.

⚠ AND THE RISK IN LEVER 2 IS REAL AND MUST BE MEASURED, NOT ASSUMED. The reel /
page stamp is the single artifact Tesseract cannot see and the main reason to
run a VLM at all. It is small dot-matrix type at the page head, so a cheaper
render could destroy exactly the thing we are paying for. Run --width 1400 and
compare before trusting the speedup.

Sequential, paced, aborts permanently on refusal. No retry, no work-around.
"""
import base64
import io
import json
import pathlib
import queue
import sys
import threading
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

import fetch_pages as FP

URL = "http://127.0.0.1:8080/v1/chat/completions"
MAPS = ("acris_maps.jsonl", "docmaps.jsonl")
OUT = pathlib.Path("render/qwendoc")
PACE = 0.5

# ⚠ THE PROMPT IS THE SPEED KNOB. Every word it is allowed to emit costs one
# sequential decode step. Naming the fields bounds the output; "transcribe
# everything" does not.
ARTIFACT_PROMPT = (
    "From this scanned land-record page, list ONLY the following if present, "
    "one per line as FIELD: VALUE. Skip anything absent. Do not transcribe the "
    "page and do not explain.\n"
    "REEL / PAGE stamp; LIBER / PAGE; DOCUMENT ID; DOCUMENT TYPE; "
    "DOCUMENT DATE; RECORDED DATE; BLOCK; LOT; UNIT; ADDRESS; "
    "GRANTOR / PARTY ONE; GRANTEE / PARTY TWO; LENDER; BORROWER; "
    "DOLLAR AMOUNTS; SQUARE FEET; COUNTY / BOROUGH."
)
FULL_PROMPT = ("Transcribe every word of text visible in this scanned document "
               "page, exactly as printed. Do not summarize.")


def page_count(doc):
    """ASK THE MAP. ⚠ Never probe — ACRIS serves a placeholder TIFF past the
    last page, so a probe loop never terminates and hammers the server."""
    head = '{"doc_id": "%s"' % doc
    for name in MAPS:
        p = pathlib.Path(name)
        if not p.exists():
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith(head):
                    try:
                        n = json.loads(line).get("hid_TotalPages")
                    except ValueError:
                        continue
                    if n:
                        return int(n)
    return None


def fetch(doc, page, width):
    url = f"{FP.BASE}?doc_id={doc}&page={page}"
    req = urllib.request.Request(url, headers={
        "User-Agent": FP.UA,
        "Referer": f"https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id={doc}",
        "Accept": "image/tiff,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data, ctype = r.read(), r.headers.get("Content-Type", "")
    FP._check_denied(data, ctype)          # ⚠ raises -> stop. no retry.
    if data[:2] not in (b"II", b"MM"):
        return None, 0
    im = Image.open(io.BytesIO(data))
    if im.mode == "1":
        im = im.convert("L")               # ⚠ 'L' before resize, always
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=False)
    return buf.getvalue(), len(data)


def ask(png, prompt, max_tok):
    b64 = base64.b64encode(png).decode()
    body = json.dumps({"messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": max_tok, "temperature": 0}).encode()
    req = urllib.request.Request(URL, data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=1800) as r:
        d = json.load(r)
    u = d.get("usage", {})
    return (d["choices"][0]["message"]["content"], time.time() - t0,
            u.get("prompt_tokens", 0), u.get("completion_tokens", 0))


def main():
    doc = sys.argv[1]
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 999
    width = 1400 if "--width" in sys.argv and "1400" in sys.argv else 1000
    full = "--full" in sys.argv
    prompt = FULL_PROMPT if full else ARTIFACT_PROMPT
    max_tok = 1100 if full else 320

    n = page_count(doc)
    if not n:
        print(f"  {doc} not in the map — refusing to probe."); return
    n = min(n, cap)
    d = OUT / doc
    d.mkdir(parents=True, exist_ok=True)

    print(f"  {doc} · {n} pages · width {width} · "
          f"{'FULL TRANSCRIPTION' if full else 'ARTIFACTS ONLY'} "
          f"(max_tokens {max_tok})\n")

    # ⚠ FETCH RUNS AHEAD OF OCR IN ITS OWN THREAD. Network and GPU are different
    # resources; serialising them was pure waste in the first pipeline.
    q = queue.Queue(maxsize=3)
    stop = threading.Event()

    def producer():
        try:
            for pg in range(1, n + 1):
                if stop.is_set():
                    break
                png, raw = fetch(doc, pg, width)
                q.put((pg, png, raw))
                time.sleep(PACE)
        except FP.AccessDenied as e:
            q.put(("DENIED", str(e), 0))
        except Exception as e:
            q.put(("ERR", f"{type(e).__name__}: {str(e)[:80]}", 0))
        q.put((None, None, 0))

    threading.Thread(target=producer, daemon=True).start()

    print(f"  {'pg':>3}{'KB':>7}{'sec':>7}{'in':>7}{'out':>6}  first line")
    t_all = time.time()
    done = tin = tout = 0
    lines = []
    while True:
        pg, png, raw = q.get()
        if pg is None:
            break
        if pg in ("DENIED", "ERR"):
            print(f"\n  ⚠ {png}"); stop.set(); break
        if not png:
            continue
        txt, el, pi, po = ask(png, prompt, max_tok)
        done += 1; tin += pi; tout += po
        (d / f"p{pg:03d}.txt").write_text(txt, encoding="utf-8")
        first = " ".join(txt.split())[:58]
        print(f"  {pg:>3}{raw/1024:>7.0f}{el:>7.1f}{pi:>7}{po:>6}  {first}")
        lines.append(txt)
    wall = time.time() - t_all

    print(f"\n  {done} pages in {wall:.1f}s = {done/max(wall,1e-9):.2f} pages/s"
          f"   ({wall/max(done,1):.1f} s/page)")
    print(f"  tokens: {tin:,} in · {tout:,} out "
          f"({tout/max(done,1):.0f} generated per page)")
    print(f"  -> {d}")
    print(f"\n  ⚠ compare against --full and --width 1400 before trusting this.")
    print(f"    The reel/page stamp is small dot-matrix type and is the whole")
    print(f"    reason to run a VLM here; a cheaper render can destroy it.")


if __name__ == "__main__":
    main()
