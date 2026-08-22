"""LEARN THE COVER-PAGE FIELD MAP PER LAYOUT — supervised, free, no model.

THE QUESTION THIS ANSWERS: can Tesseract alone put a correct, checkable value
into the database, or does every document need a language model? That decides
whether renting ~97 cores for a month is worth doing, so it is worth measuring
before spending anything.

⚠ WHY A SINGLE GEOMETRIC RULE CANNOT WORK. Measured on two real cover pages:

    2014   "...Real Property Transfer Tax:"        -> 155,503.36  dy=+52 dx=+332
    2003   "...Real Property Transfer Tax Filing"  ->      25.00  dy=+51 dx=+253

Nearly identical offsets. One is the transfer tax; the other is the FILING FEE,
because on the older form the label runs on into "Filing Fee". A hand-written
"nearest money token below and to the right" rule bound the filing fee on 150
consecutive pages, at 96% OCR confidence, and every row looked plausible.

⚠ SO THE OFFSET IS LEARNED, NOT DECLARED. MASTER.document_amt is a free
training label: for documents where it exists, find which money token on the
page reproduces it, and record that token's offset from the label. The modal
offset within a layout cluster IS the field map. Documents with no index figure
then inherit the map and get read anyway — which is the whole point, since the
index omits consideration from 74.3% of deeds.

⚠ THE INDEX IS THE TEACHER HERE, NEVER THE SOURCE. Nothing it says is written
as a claim. It is used to discover where a number LIVES ON THE PAGE, after
which the page is the authority and the index can be discarded.

⚠ AND NOTHING IS EVER REPAIRED TO MAKE A CHECK PASS. A document whose two
stamps disagree is reported as a failure, because the failure rate is the
answer this file exists to produce.
"""
import collections
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
import fingerprint as FP

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
MONEY = re.compile(r"^[\d,]+\.\d\d$")
RPTT_RATE, RETT_RATE = 0.02625, 0.004
LABELS = {"rptt": "Real Property Transfer Tax",
          "rett": "Real Estate Transfer Tax"}


def tsv(path):
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
                        "h": int(x["height"])})
        except (ValueError, KeyError, TypeError):
            pass
    return out


def anchor(ws, phrase):
    """Box of the LAST word of the label, wherever it occurs."""
    parts = phrase.upper().split()
    for i in range(len(ws) - len(parts) + 1):
        if all(ws[i + k]["t"].upper().strip(":|$.,'\u2018\u2019") == parts[k]
               for k in range(len(parts))):
            return ws[i + len(parts) - 1]
    return None


def money(ws):
    return [w for w in ws if MONEY.match(w["t"])]


def val(w):
    return float(w["t"].replace(",", ""))


def page(d):
    p = d / "p001.tif"
    if not p.exists():
        return None
    ws = tsv(p)
    return {"doc": d.name, "ws": ws,
            "anchors": {k: anchor(ws, v) for k, v in LABELS.items()},
            "money": money(ws)}


def main():
    docs = sorted(x for x in pathlib.Path("devr_pages").iterdir()
                  if x.is_dir() and (x / "p001.tif").exists())
    print(f"{len(docs)} DEVR cover pages on disk\n")

    print("1 · clustering cover pages by layout")
    cl = FP.clusters([(d.name, d / "p001.tif") for d in docs])
    which = {}
    for i, c in enumerate(sorted(cl, key=len, reverse=True)):
        for n in c:
            which[n] = i
    sizes = collections.Counter(which.values())
    print(f"    {len(cl)} layouts · top 3 hold "
          f"{sum(n for _, n in sizes.most_common(3))/len(docs)*100:.0f}%")

    print("\n2 · OCR with coordinates")
    t0 = time.time()
    with cf.ThreadPoolExecutor(12) as ex:
        pages = [r for r in ex.map(page, docs) if r]
    print(f"    {len(pages)} pages in {time.time()-t0:.0f}s "
          f"({len(pages)/(time.time()-t0)*3600:,.0f} pg/hr)")

    print("\n3 · learning the offset from MASTER.document_amt (teacher only)")
    amt = {}
    for m in bulk.socrata_in("bnx9-e6tj", "document_id", [p["doc"] for p in pages],
                             select="document_id,document_amt"):
        try:
            amt.setdefault(m["document_id"], float(m.get("document_amt") or 0))
        except (TypeError, ValueError):
            amt.setdefault(m["document_id"], 0.0)
    taught = collections.defaultdict(list)
    for p in pages:
        a = amt.get(p["doc"], 0)
        anc = p["anchors"]["rptt"]
        if not a or not anc:
            continue
        for w in p["money"]:
            if val(w) and abs(val(w) / RPTT_RATE - a) / a < 0.01:
                taught[which[p["doc"]]].append((w["x"] - anc["x"], w["y"] - anc["y"]))
                break
    fieldmap = {}
    for c, offs in taught.items():
        dx = int(statistics.median(o[0] for o in offs))
        dy = int(statistics.median(o[1] for o in offs))
        fieldmap[c] = (dx, dy, len(offs))
        print(f"    layout {c}: dx={dx:+5} dy={dy:+4}   learned from {len(offs)} examples")
    if not fieldmap:
        print("    ⚠ NOTHING LEARNED — no document taught an offset.")

    print("\n4 · applying the map and CHECKING (three witnesses)")
    TOL = 90
    agree = disagree = nobind = nostamp = zero = 0
    ext_ok = ext_bad = 0
    for p in pages:
        c = which[p["doc"]]
        fm = fieldmap.get(c)
        out = {}
        for key, rate in (("rptt", RPTT_RATE), ("rett", RETT_RATE)):
            anc = p["anchors"][key]
            if not anc or not fm:
                continue
            dx, dy, _ = fm
            best = None
            for w in p["money"]:
                d = abs((w["x"] - anc["x"]) - dx) + abs((w["y"] - anc["y"]) - dy)
                if d < TOL and (best is None or d < best[0]):
                    best = (d, w)
            if best:
                out[key] = val(best[1])
        if not out:
            nobind += 1
            continue
        if out.get("rptt") == 0 and out.get("rett") == 0:
            zero += 1                      # $0/$0 = commonly-controlled: a FINDING
            continue
        if "rptt" not in out or "rett" not in out:
            nostamp += 1
            continue
        a, b = out["rptt"] / RPTT_RATE, out["rett"] / RETT_RATE
        if max(a, b) and abs(a - b) / max(a, b) < 0.01:
            agree += 1
            k = amt.get(p["doc"], 0)
            if k:
                ext_ok, ext_bad = ((ext_ok + 1, ext_bad)
                                   if abs(a - k) / k < 0.01 else (ext_ok, ext_bad + 1))
        else:
            disagree += 1

    n = len(pages)
    print(f"    stamps AGREE with each other      {agree:>5}  {agree/n*100:>5.1f}%")
    print(f"    $0 / $0  (commonly controlled)    {zero:>5}  {zero/n*100:>5.1f}%")
    print(f"    stamps DISAGREE (misread)         {disagree:>5}  {disagree/n*100:>5.1f}%")
    print(f"    only one stamp bound              {nostamp:>5}  {nostamp/n*100:>5.1f}%")
    print(f"    nothing bound                     {nobind:>5}  {nobind/n*100:>5.1f}%")
    good = agree + zero
    print(f"\n    MECHANICAL PASS RATE (no model)  {good}/{n} = {good/n*100:.1f}%")
    print(f"    needs a model                     {n-good}/{n} = {(n-good)/n*100:.1f}%")
    if ext_ok + ext_bad:
        print(f"\n    third witness (index) on the agreeing set: "
              f"{ext_ok} confirm / {ext_bad} contradict")
    json.dump({str(k): v for k, v in fieldmap.items()},
              open("_fieldmap.json", "w"), indent=1)


if __name__ == "__main__":
    main()
