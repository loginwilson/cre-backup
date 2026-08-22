"""CALIBRATED PROMPT vs GENERIC PROMPT. Is Qwen limited by capability or by
never having been told what these documents contain?

    python qwen_prompt.py BK_6730047100023 answer_key_bookdoc.json

⚠ THE EARLIER COMPARISON WAS TILTED AND THIS IS THE CONTROL FOR IT. Tesseract
was given domain knowledge - rotate 90/270 because backers are sideways, use
psm 11 because stamps are sparse text - tuned from measurement across three
documents. Qwen was handed one generic sentence ("transcribe every word") and
shown only the upright page. So "T-multi beats Qwen" partly measured how much
configuration effort each engine received, not the engines.

This gives Qwen the SAME domain knowledge, in words instead of image
transforms, and changes nothing else: same model, same pages, same upright
orientation.

  generic    "transcribe every word"                  -> 92% book (measured)
  + rotation same prompt, plus 90/270 renders         -> 95% book (measured)
  A CALIBRATED  domain hints, one pass, UPRIGHT ONLY  -> ?
  B STAMP       second pass asking ONLY for the stamp -> ?

If calibrated reaches ~95% with no rotation, the gap was INSTRUCTION - a
fine-tune would be teaching conventions, not adding capability, and the 3x
rotation cost can be dropped. If it stays at 92%, the gap is perception and
rotation stays in the pipeline permanently.

⚠ B IS A SEPARATE QUESTION FROM A. A long "transcribe everything" answer has to
spend its attention budget across the whole page, and the stamp is six
characters in a corner - the thing most likely to be dropped for being small,
not for being unreadable. B asks for nothing but the stamp block, so if the
stamp appears in B and not in A, the limit is ATTENTION BUDGET (fixable with a
cheap short second pass) rather than either instruction or perception.

⚠ THE PROMPT MUST NOT NAME THE ANSWERS. It may describe what KINDS of things
appear on a NYC land record - stamps at the head, sideways backers, handwritten
margins - because that is knowledge available for all 17M documents. It must
never mention REC. 471, Kings County, or Peninsula National Bank, which would be
feeding this document its own answer key and would measure nothing.
"""
import base64
import io
import json
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from PIL import Image

import score as S

URL = "http://127.0.0.1:8080/v1/chat/completions"

GENERIC = ("Transcribe every word of text visible in this scanned document page, "
           "exactly as printed. Include reel, record and page stamps, document "
           "numbers, names, dollar amounts and dates. Do not summarize.")

CALIBRATED = (
    "This is a scanned New York City land record (deed, mortgage, assignment or "
    "similar), photographed from microfilm or a bound record book. Transcribe "
    "EVERY word visible on the page, exactly as printed.\n"
    "\n"
    "Pay particular attention to these, which are easy to miss:\n"
    "- A small stamp at the top or edge of the page giving a REEL, RECORD (REC.) "
    "or LIBER number and a page number. It is often dot-matrix, faint, skewed or "
    "partly cut off. Transcribe the digits exactly.\n"
    "- A BACKER or endorsement block, frequently printed SIDEWAYS (rotated 90 "
    "degrees) in the lower half or along an edge. It carries the parties, the "
    "instrument type, recording tax, the title company, the bank, and the City "
    "Register stamp. Read it and transcribe it even though it is rotated.\n"
    "- Recording stamps giving a date and time of filing, often overprinted, "
    "smudged or at an angle.\n"
    "- Handwritten margin notes, commonly a Section, Block and Lot number.\n"
    "- Text reversed out white-on-black.\n"
    "\n"
    "Transcribe verbatim. Do NOT correct spelling, names, dates or numbers, and "
    "do NOT infer text you cannot actually see. Where a character or word is "
    "genuinely illegible, write [UNCLEAR] rather than guessing."
)

STAMP = (
    "This is a scanned New York City land record. Ignore the body text of the "
    "document. Report ONLY the small administrative markings, which sit at the "
    "edges and corners and are often faint, skewed, dot-matrix, handwritten or "
    "printed sideways:\n"
    "1. The film or book stamp: a REEL, RECORD (REC.) or LIBER number and page "
    "number.\n"
    "2. Any City Register or County Clerk recording stamp, with its date and "
    "time.\n"
    "3. Any recording tax or fee amount.\n"
    "4. Any handwritten Section / Block / Lot written in a margin.\n"
    "5. Any document, control or title number.\n"
    "Give each as a short line, verbatim. If one is not present on this page, "
    "say ABSENT for it. If it is present but you cannot read a character, write "
    "[UNCLEAR] there rather than guessing."
)

VARIANTS = {"CAL": (CALIBRATED, 2048, "qwencal"),
            "STAMP": (STAMP, 384, "qwenstamp")}


def ask(png, prompt, ntok):
    b64 = base64.b64encode(png).decode()
    body = json.dumps({"messages": [{"role": "user", "content": [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": ntok, "temperature": 0}).encode()
    req = urllib.request.Request(URL, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def render(p, width=1000):
    im = Image.open(p)
    if im.mode == "1":
        im = im.convert("L")
    if im.width != width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def main():
    doc, keyf = sys.argv[1], sys.argv[2]
    R = pathlib.Path("render/testdoc") / doc
    KEY = json.loads(pathlib.Path(keyf).read_text(encoding="utf-8"))
    PAGES = [k for k in KEY if not k.startswith("_")]
    S.META.update({p: {"doc_id": doc} for p in PAGES})

    got = {}
    for tag, (prompt, ntok, sub) in VARIANTS.items():
        out = R / sub
        out.mkdir(exist_ok=True)
        print(f"  {doc}: {tag} prompt, UPRIGHT ONLY, {len(PAGES)} pages")
        t0 = time.time()

        def one(p, _pr=prompt, _n=ntok, _o=out):
            f = _o / (p + ".txt")
            if f.exists():
                return f.read_text(encoding="utf-8", errors="replace")
            tx = ask(render(R / p), _pr, _n)
            f.write_text(tx, encoding="utf-8")
            return tx

        with ThreadPoolExecutor(max_workers=2) as ex:
            outs = list(ex.map(one, PAGES))
        el = time.time() - t0
        got[tag] = dict(zip(PAGES, outs))
        print(f"    {el:.1f}s ({el/len(PAGES):.1f} s/page)\n")

    def t(e, p):
        if e in got:
            return got[e][p]
        if e == "ROT":
            return " ".join(f.read_text(encoding="utf-8", errors="replace")
                            for f in sorted((R / "qwenrot").glob(f"{p[:-4]}_r*.txt")))
        f = R / e / (p + ".txt")
        return f.read_text(encoding="utf-8", errors="replace") if f.exists() else ""

    NAME = {"CAL": "qwen-calibrated", "STAMP": "qwen-stamp-pass", "ROT": "qwen-rot"}
    combos = [("qwen",), ("CAL",), ("CAL", "STAMP"), ("qwen", "ROT"),
              ("CAL", "STAMP", "ROT"), ("tesseract", "rapidpool", "CAL", "STAMP")]

    def evaluate(c):
        ct = cv = cp = w = 0
        miss = []
        for p in PAGES:
            raw = " ".join(t(e, p) for e in c)
            w += len(raw.split())
            hay = S.norm(raw)
            for a in KEY[p]["artifacts"]:
                if a["tier"] != "CRITICAL":
                    continue
                cv += 1
                ok = S.found(hay, a)
                ct += ok
                pt = ok or S.pointed(hay, a)
                cp += pt
                if not ok:
                    miss.append((p, a["id"], str(a["value"]), pt))
        return ct, cv, cp, w, miss

    print(f"  {'config':<46}{'CRIT tr':>12}{'CRIT pt':>12}{'words':>8}")
    results = {}
    for c in combos:
        ct, cv, cp, w, miss = evaluate(c)
        results[c] = miss
        nm = "+".join(NAME.get(e, e) for e in c)
        print(f"  {nm:<46}{f'{ct}/{cv}':>8}{ct/cv*100:>4.0f}%"
              f"{f'{cp}/{cv}':>8}{cp/cv*100:>4.0f}%{w:>8}")

    # ── did the stamp pass do the one job it was written for? ──
    print("\n  ── the stamp artifacts specifically ──")
    stampish = ("rec_", "reel_", "record", "tax", "register", "block", "lot", "stamp")
    for p in PAGES:
        for a in KEY[p]["artifacts"]:
            if a["tier"] != "CRITICAL" or not any(k in a["id"] for k in stampish):
                continue
            row = [("Y" if S.found(S.norm(t(e, p)), a) else
                    ("~" if S.pointed(S.norm(t(e, p)), a) else "."))
                   for e in ("qwen", "CAL", "STAMP", "ROT")]
            print(f"    {p:<11}{a['id']:<14}{str(a['value'])[:26]:<28}"
                  f"gen {row[0]}  cal {row[1]}  stamp {row[2]}  rot {row[3]}")

    # ── what is still missing after everything, i.e. the residual ──
    best = ("CAL", "STAMP", "ROT")
    print(f"\n  ── STILL MISSED by {'+'.join(NAME.get(e, e) for e in best)} ──")
    for p, i, v, pt in results[best]:
        print(f"    {p:<11}{i:<16}{v[:38]:<40}{'POINTED (chars wrong)' if pt else 'ABSENT'}")

    # regression check: prompts can HURT
    lost = {(p, i) for p, i, _, _ in results[("CAL",)]} - \
           {(p, i) for p, i, _, _ in results[("qwen",)]}
    print(f"\n  regression - caught by generic, LOST by calibrated: {len(lost)}")
    for p, i in sorted(lost):
        print(f"    {p:<11}{i}")

    n_unc = sum(v.upper().count("[UNCLEAR]") for v in got["CAL"].values())
    print(f"\n  [UNCLEAR] markers in calibrated run: {n_unc}"
          f"   (hallucination guard - 0 means it guessed instead of flagging)")


if __name__ == "__main__":
    main()
