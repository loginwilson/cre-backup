"""SPATIAL FIELD EXTRACTION FROM THE COVER PAGE — no language model.

⚠ THE MISTAKE THIS FIXES, AND HOW IT HID. Six OCR arms were benchmarked and
psm 6 was chosen as fastest at "full recall". The recall metric was PHRASE
PRESENCE — does the page contain "Real Property Transfer Tax" — and every arm
scored 25/25. But the cover page is a TWO-COLUMN TABLE, and reading it as one
block puts the label on a different line from its number:

    NYC Real Property Transfer Tax:
    Exemption: | $ 155,503.36

The characters are perfect. The BINDING between label and value is destroyed.
Phrase presence cannot see that, so the benchmark reported success on 150 pages
while extracting the stamp from zero of them. A metric that survives the damage
you care about will always report that nothing is wrong.

No page-segmentation mode fixes it — psm 1, 3, 4, 6, 11 and 12 all fail, because
the columns genuinely interleave in reading order. The fix is not a better
reading order, it is to stop relying on reading order: bind label to value by
POSITION.

⚠ WHY THIS MATTERS OUT OF PROPORTION TO ITS SIZE. The cover page is generated
by the City Register, in one layout, on every ACRIS document. It carries the
document id, both dates, the type, every BBL, both parties, and the transfer-tax
stamps — and the stamps are the real consideration, which the index omits from
74.3% of deeds. If this page can be read mechanically, the largest missing field
in the corpus is recoverable with no model in the loop at all.

⚠ AND IT GRADES ITSELF, TWICE OVER, FOR FREE.
    the printed document id must equal the directory name on disk
    RPTT / 2.625% must equal RETT / 0.400%, independently of both
No labelling, at any scale. Never repair a number to make either agree.
"""
import concurrent.futures as cf
import csv
import io
import json
import os
import pathlib
import re
import statistics
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bulk

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
MONEY = re.compile(r"^[\d,]+\.\d\d$")
RPTT_RATE = 0.02625      # NYC RPTT, commercial, over $500,000
RETT_RATE = 0.004        # NYS RETT, $2 per $500


def words(path):
    r = subprocess.run([TESS, str(path), "stdout", "--psm", "6", "tsv"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    out = []
    for x in csv.DictReader(io.StringIO(r.stdout), delimiter="\t",
                            quoting=csv.QUOTE_NONE):
        t = (x.get("text") or "").strip()
        if not t:
            continue
        try:
            out.append({"t": t, "x": int(x["left"]), "y": int(x["top"]),
                        "w": int(x["width"]), "h": int(x["height"]),
                        "c": float(x["conf"])})
        except (ValueError, KeyError, TypeError):
            continue
    return out


def find_phrase(ws, phrase):
    """Locate a multi-word label; return the box of its LAST word, which is
    what a value sits to the right of or below."""
    parts = phrase.upper().split()
    for i in range(len(ws) - len(parts) + 1):
        if all(ws[i + k]["t"].upper().strip(":|$") == parts[k]
               for k in range(len(parts))):
            return ws[i + len(parts) - 1]
    return None


def value_near(ws, label, maxdy=3.0):
    """⚠ SAME LINE OR THE NEXT ONE, AND TO THE RIGHT. Deliberately narrow: a
    generous search would happily bind the RPTT label to the RETT figure 108
    pixels below it, and the two are within a factor of seven of each other, so
    nothing downstream would look obviously wrong."""
    if not label:
        return None
    best = None
    for w in ws:
        if not MONEY.match(w["t"]):
            continue
        dy = w["y"] - label["y"]
        if dy < -label["h"] or dy > maxdy * label["h"]:
            continue
        if w["x"] < label["x"]:
            continue
        d = (abs(dy), w["x"] - label["x"])
        if best is None or d < best[0]:
            best = (d, w)
    return best[1] if best else None


def one(d):
    p = d / "p001.tif"
    if not p.exists():
        return None
    ws = words(p)
    flat = " ".join(w["t"] for w in ws)
    m = re.search(r"Document\s*ID[:\s]*([0-9A-Z_]{10,20})", flat, re.I)
    rp = value_near(ws, find_phrase(ws, "Real Property Transfer Tax"))
    re_ = value_near(ws, find_phrase(ws, "Real Estate Transfer Tax"))
    f = lambda v: float(v["t"].replace(",", "")) if v else None
    return {"doc": d.name, "read_id": m.group(1) if m else None,
            "rptt": f(rp), "rett": f(re_),
            "rptt_conf": rp["c"] if rp else None,
            "rett_conf": re_["c"] if re_ else None}


def main():
    docs = sorted(d for d in pathlib.Path("devr_pages").iterdir()
                  if d.is_dir() and (d / "p001.tif").exists())[:150]
    t0 = time.time()
    with cf.ThreadPoolExecutor(12) as ex:
        rows = [r for r in ex.map(one, docs) if r]
    el = time.time() - t0
    rate = len(rows) / el * 3600
    print(f"{len(rows)} cover pages in {el:.0f}s -> {rate:,.0f} pg/hr\n")

    exact = sum(1 for r in rows if r["read_id"] == r["doc"])
    print(f"  DOCUMENT ID exact vs directory name : {exact}/{len(rows)} "
          f"= {exact/len(rows):.3f}")

    got = [r for r in rows if r["rptt"] or r["rett"]]
    print(f"  a transfer-tax stamp bound          : {len(got)}/{len(rows)}")

    # ── WITNESS 1 vs WITNESS 2: the two stamps must agree with each other ──
    both = [r for r in rows if r["rptt"] and r["rett"]]
    ok = bad = 0
    for r in both:
        a, b = r["rptt"] / RPTT_RATE, r["rett"] / RETT_RATE
        # RETT rounds consideration UP to the next $500, so b >= a always,
        # and the gap is bounded by 500 * RETT_RATE / RPTT_RATE in price terms.
        if abs(a - b) / max(a, b) < 0.01:
            ok += 1
        else:
            bad += 1
    print(f"\n  both stamps present                 : {len(both)}")
    print(f"    RPTT/2.625% agrees with RETT/0.400%: {ok}")
    print(f"    DISAGREE (one was misread)        : {bad}")

    # ── WITNESS 3: MASTER.document_amt, used to CHECK, never as the source ──
    mas = {}
    for m in bulk.socrata_in("bnx9-e6tj", "document_id", [r["doc"] for r in rows],
                             select="document_id,document_amt"):
        mas.setdefault(m["document_id"], m.get("document_amt"))
    agree = dis = nocheck = 0
    gaps = []
    for r in rows:
        if not r["rptt"]:
            continue
        try:
            amt = float(mas.get(r["doc"]) or 0)
        except (TypeError, ValueError):
            amt = 0
        if not amt:
            nocheck += 1
            continue
        g = abs(r["rptt"] / RPTT_RATE - amt) / amt
        gaps.append(g)
        agree, dis = (agree + 1, dis) if g < 0.01 else (agree, dis + 1)
    print(f"\n  price from stamp vs MASTER.document_amt:")
    print(f"    agree within 1%                   : {agree}")
    print(f"    DISAGREE                          : {dis}")
    print(f"    index carries no figure to check  : {nocheck}")
    if gaps:
        print(f"    median gap                        : {statistics.median(gaps)*100:.4f}%")

    print(f"\n  at {rate:,.0f} pg/hr, one cover page per document:")
    for lbl, n in [("all DEED", 3_646_068), ("all MTGE", 4_220_709),
                   ("ALL ACRIS", 17_065_090)]:
        print(f"    {lbl:<12}{n:>12,} docs -> {n/rate/24:>6.1f} days")
    pathlib.Path("_cover_fields.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
