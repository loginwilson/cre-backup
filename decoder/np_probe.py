"""TWO PAGES — ONE FILM, ONE MODERN — against a live llama-server.

⚠ TWO PAGES ANSWERS THE CONCURRENCY QUESTION AND 21 DOES NOT ANSWER IT FASTER.
The question here is narrow: does the Arc survive N concurrent vision encodes,
and does throughput actually rise? That needs exactly N requests in flight, not
a long queue. Running 21 pages to learn it costs 10 minutes and loads a machine
that has already been struggling.

⚠ SEQUENTIAL AND CONCURRENT ARE BOTH TIMED, because "it did not crash" is not
the result. If two concurrent pages take the same wall-clock as two sequential
ones, the slots are real but the hardware is serialising them and concurrency
buys nothing.

    python np_probe.py [n_concurrent]
"""
import base64
import json
import pathlib
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BENCH = pathlib.Path("render/bench2")
URL = "http://127.0.0.1:8080/v1/chat/completions"
PROMPT = ("Transcribe every word of text visible in this scanned document page, "
          "exactly as printed. Include reel and page stamps, names, dates and "
          "dollar amounts. Do not summarize.")

# one film, one modern — deliberately the two ends of the corpus
PICK = [("FILM  ", "1990s_ASST_FT_1580004452058_p002.png"),
        ("MODERN", "2020s_CERT_2026060200874001_p003.png")]


def ask(path):
    b64 = base64.b64encode(path.read_bytes()).decode()
    body = json.dumps({
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": 900, "temperature": 0}).encode()
    req = urllib.request.Request(URL, data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=900) as r:
            d = json.load(r)
        return d["choices"][0]["message"]["content"], time.time() - t0, None
    except Exception as e:
        return "", time.time() - t0, f"{type(e).__name__}: {str(e)[:70]}"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    files = [(lab, BENCH / f) for lab, f in PICK]
    for lab, f in files:
        if not f.exists():
            print(f"  missing {f}")
            return

    print(f"  server concurrency = {n}\n")

    # ── sequential ───────────────────────────────────────────────────────
    print(f"  {'SEQUENTIAL':<12}{'sec':>8}{'words':>8}  first 60 chars")
    seq = 0.0
    outs = {}
    for lab, f in files:
        txt, el, err = ask(f)
        seq += el
        outs[lab] = txt
        head = err or " ".join(txt.split())[:60]
        print(f"  {lab:<12}{el:>8.1f}{len(txt.split()):>8}  {head}")
    print(f"  {'total':<12}{seq:>8.1f}")

    if n < 2:
        print(f"\n  (concurrency 1 — no parallel leg to run)")
    else:
        # ── concurrent ───────────────────────────────────────────────────
        print(f"\n  {'CONCURRENT':<12}{'sec':>8}{'words':>8}  first 60 chars")
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=len(files)) as ex:
            res = list(ex.map(lambda a: ask(a[1]), files))
        wall = time.time() - t0
        for (lab, _), (txt, el, err) in zip(files, res):
            head = err or " ".join(txt.split())[:60]
            print(f"  {lab:<12}{el:>8.1f}{len(txt.split()):>8}  {head}")
        print(f"  {'wall':<12}{wall:>8.1f}")
        print(f"\n  speedup {seq/wall:.2f}x   "
              + ("concurrency is REAL" if seq / wall > 1.25 else
                 "⚠ hardware is SERIALISING — slots exist but buy nothing"))

    out = BENCH / "np_probe"
    out.mkdir(exist_ok=True)
    for lab, txt in outs.items():
        (out / f"np{n}_{lab.strip()}.txt").write_text(txt, encoding="utf-8")
    print(f"\n  -> {out}")


if __name__ == "__main__":
    main()
