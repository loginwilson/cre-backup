"""A SAMPLE BROAD ENOUGH TO MEASURE THE ESCALATION RATE, which is the number
the whole cost model is missing.

⚠ EVERY ACCURACY FIGURE IN THIS PROJECT COMES FROM THREE DOCUMENTS. That is
enough to show the cascade works and nowhere near enough to price it, because
the price depends on WHAT FRACTION OF PAGES ESCALATE past the cheap first pass -
and that fraction has never been measured on anything.

The escalation trigger needs no answer key: an FT_ page must carry REEL <n>, a
BK_ page must carry REC <n>, a digital document must carry a cover page with its
Document ID. Absent means failed. So the rate can be measured on hundreds of
pages nobody has read.

⚠ SAMPLED ACROSS THE MAP, NOT FROM THE TOP, and across DOC TYPES - the three
documents read so far are all MTGE, so nothing is known about how deeds, leases,
assignments or satisfactions behave.
"""
import io
import json
import pathlib
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

import fetch_pages as FP

TYPES = ("DEED", "MTGE", "ASST", "SAT", "AGMT", "LEAS")
PER_CLASS = 12          # documents per scan class
PAGES_PER_DOC = 3
OUT = pathlib.Path("render/sample")
OUT.mkdir(parents=True, exist_ok=True)


def klass(did):
    if did.startswith("FT_"):
        return "film"
    if did.startswith("BK_"):
        return "book"
    return "digital"


def pick():
    want = {"film": [], "book": [], "digital": []}
    seen = {"film": 0, "book": 0, "digital": 0}
    stride = {"film": 4001, "book": 1201, "digital": 6007}
    with open("acris_maps.jsonl", "rb") as fh:
        for line in fh:
            if all(len(v) >= PER_CLASS for v in want.values()):
                break
            try:
                d = json.loads(line)
            except ValueError:
                continue
            did = d.get("doc_id", "")
            k = klass(did)
            if len(want[k]) >= PER_CLASS:
                continue
            n = d.get("hid_TotalPages") or 0
            t = d.get("doc_type") or ""
            if n < 3 or t not in TYPES:
                continue
            seen[k] += 1
            if seen[k] % stride[k] == 1:
                want[k].append((did, t, n, d.get("recorded")))
    return want


def fetch(doc, pg):
    url = f"{FP.BASE}?doc_id={doc}&page={pg}"
    req = urllib.request.Request(url, headers={
        "User-Agent": FP.UA,
        "Referer": f"https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id={doc}",
        "Accept": "image/tiff,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data, ctype = r.read(), r.headers.get("Content-Type", "")
    FP._check_denied(data, ctype)          # raises -> stop, never retry
    if data[:2] not in (b"II", b"MM"):
        return None
    im = Image.open(io.BytesIO(data))
    if im.mode == "1":
        im = im.convert("L")
    tw = 1800
    return im.resize((tw, int(im.height * tw / im.width)), Image.LANCZOS)


def main():
    want = pick()
    man = []
    print(f"  {'doc_id':<20}{'cls':>8}{'type':>7}{'pp':>4}  recorded")
    for k, docs in want.items():
        for did, t, n, rec in docs:
            print(f"  {did:<20}{k:>8}{t:>7}{n:>4}  {rec}")
    print(f"\n  fetching up to {PAGES_PER_DOC} pages each "
          f"({sum(len(v) for v in want.values())} docs)\n")
    ok = 0
    for k, docs in want.items():
        for did, t, n, rec in docs:
            for pg in range(1, min(PAGES_PER_DOC, n) + 1):
                f = OUT / f"{k}__{t}__{did}__p{pg:03d}.png"
                if f.exists():
                    ok += 1
                    man.append({"file": f.name, "doc_id": did, "era": k,
                                "doc_type": t, "page": pg, "recorded": rec})
                    continue
                try:
                    im = fetch(did, pg)
                except FP.AccessDenied as e:
                    print(f"  ACCESS DENIED - stopping permanently: {e}")
                    (OUT / "manifest.json").write_text(json.dumps(man, indent=1),
                                                      encoding="utf-8")
                    return
                except Exception as e:
                    print(f"    {did} p{pg}: {type(e).__name__}")
                    continue
                if im is None:
                    continue
                im.save(f)
                ok += 1
                man.append({"file": f.name, "doc_id": did, "era": k,
                            "doc_type": t, "page": pg, "recorded": rec})
                time.sleep(0.4)
        print(f"    {k}: {ok} pages so far")
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(f"\n  {ok} pages -> {OUT}")


if __name__ == "__main__":
    main()
