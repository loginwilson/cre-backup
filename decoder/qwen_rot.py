"""QWEN ON THE ROTATED PAGE TOO. Testing whether Qwen's book misses are
orientation, not capability.

    python qwen_rot.py BK_6730047100023 answer_key_bookdoc.json

⚠ THE HYPOTHESIS IS SPECIFIC AND FALSIFIABLE. Qwen alone transcribed 76/83 of
the book document's CRITICAL artifacts. All five unique misses - RECORDING TAX,
JUL 10 1967, OFFICE OF CITY REGISTER, Peninsula National Bank, SIDERMAN - sit in
the backer block that is printed ROTATED 90 DEGREES. Qwen was only ever shown
the page upright, so it never saw them the right way up. If the hypothesis is
right, showing it the rotated image recovers most of them. If it is wrong, they
were unreadable for some other reason and rotation changes nothing.

⚠ AND THE COST IS REAL: this TRIPLES the VLM cost per page (upright + 90 + 270).
On this iGPU book already runs 61 s/page, so this is ~180 s/page. Worth it only
if the recovery is large - which is exactly what is being measured.
"""
import base64
import io
import json
import pathlib
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from PIL import Image

import score as S

URL = "http://127.0.0.1:8080/v1/chat/completions"
PROMPT = ("Transcribe every word of text visible in this scanned document page, "
          "exactly as printed. Include reel, record and page stamps, document "
          "numbers, names, dollar amounts and dates. Do not summarize.")


def ask(png):
    b64 = base64.b64encode(png).decode()
    body = json.dumps({"messages": [{"role": "user", "content": [
        {"type": "text", "text": PROMPT},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": 2048, "temperature": 0}).encode()
    req = urllib.request.Request(URL, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def render(p, ang, width=1000):
    im = Image.open(p)
    if im.mode == "1":
        im = im.convert("L")
    if ang:
        im = im.rotate(ang, expand=True)
    if im.width != width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def main():
    doc = sys.argv[1]
    keyf = sys.argv[2]
    R = pathlib.Path("render/testdoc") / doc
    KEY = json.loads(pathlib.Path(keyf).read_text(encoding="utf-8"))
    PAGES = [k for k in KEY if not k.startswith("_")]
    S.META.update({p: {"doc_id": doc} for p in PAGES})
    out = R / "qwenrot"
    out.mkdir(exist_ok=True)

    jobs = [(p, ang) for p in PAGES for ang in (90, 270)]
    print(f"  {doc}: {len(PAGES)} pages x 2 rotations = {len(jobs)} Qwen calls\n")
    t0 = time.time()

    def one(j):
        p, ang = j
        f = out / f"{p[:-4]}_r{ang}.txt"
        if f.exists():
            return f.read_text(encoding="utf-8", errors="replace")
        txt = ask(render(R / p, ang))
        f.write_text(txt, encoding="utf-8")
        return txt

    with ThreadPoolExecutor(max_workers=2) as ex:
        outs = list(ex.map(one, jobs))
    el = time.time() - t0
    rot = {p: "" for p in PAGES}
    for (p, _), tx in zip(jobs, outs):
        rot[p] += " " + tx
    print(f"  rotated Qwen: {el:.1f}s ({el/len(PAGES):.1f} s/page for both rotations)\n")

    def t(e, p):
        f = R / e / (p + ".txt")
        return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""

    combos = [("qwen",), ("qwen", "ROT"),
              ("tesseract", "rapidpool", "qwen"),
              ("tesseract", "rapidpool", "qwen", "ROT")]
    print(f"  {'engine(s)':<38}{'CRIT tr':>12}{'CRIT pt':>12}")
    for c in combos:
        ct = cv = cp = 0
        for p in PAGES:
            hay = S.norm(" ".join(rot[p] if e == "ROT" else t(e, p) for e in c))
            for a in KEY[p]["artifacts"]:
                if a["tier"] != "CRITICAL":
                    continue
                cv += 1
                ok = S.found(hay, a)
                ct += ok
                cp += ok or S.pointed(hay, a)
        nm = "+".join("qwen-rot" if e == "ROT" else e for e in c)
        print(f"  {nm:<38}{f'{ct}/{cv}':>8}{ct/cv*100:>4.0f}%{f'{cp}/{cv}':>8}{cp/cv*100:>4.0f}%")

    print(f"\n  ── did rotation recover the five? ──")
    targets = ["SIDERMAN", "RECORDING TAX", "JUL 10 1967", "OFFICE OF CITY REGISTER",
               "Peninsula National Bank"]
    up = S.norm(" ".join(t("qwen", p) for p in PAGES))
    rt = S.norm(" ".join(rot[p] for p in PAGES))
    for tg in targets:
        n = S.norm(tg).strip()
        print(f"    {tg:<28}upright {'Y' if n in up else 'n'}   rotated "
              f"{'YES <- recovered' if (n in rt and n not in up) else ('Y' if n in rt else 'n')}")


if __name__ == "__main__":
    main()
