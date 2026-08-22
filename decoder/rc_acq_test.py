"""BOUNDED RICHMOND ACQUISITION TEST — fetch, compress, verify, and TIME each step.

    ACRIS_CORPUS_ROOT=D:/acris python rc_acq_test.py --n 20 --conc 4

Answers three questions with measurements, not estimates:
  1 does programmatic fetch work reliably, and at what success rate
  2 what does the compress step actually cost in wall clock
  3 does the compressed page keep its text (ink coverage + a real OCR read)

⚠ 403 IS A BACKOFF SIGNAL, NOT A FAILURE TO RETRY HARDER. Measured on the first
5 documents: 2 returned 403, both succeeded on a single plain retry. So the
control is intermittent, not a wall - and the correct response is to slow down,
never to hammer. Any sustained 403 rate should REDUCE concurrency, not raise it.

⚠ THE FETCH FOLLOWS THE REDIRECT ITSELF. Minting a token in one client and
presenting it from another - which is what an earlier test did - produced a
Cloudflare challenge and led to a wrong conclusion about the whole source. One
client, one continuous request.

⚠ BITONAL IS LOSSY AND IRREVERSIBLE. 16.7x smaller (20.3 TB -> 1.22 TB) but it
destroys faint stamps, seals and light handwriting. This script reports ink
coverage per page so a threshold that eats content shows up as a number rather
than being discovered later on a document that mattered.
"""
from __future__ import annotations

import argparse
import csv
import io
import pathlib
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URLS = pathlib.Path("D:/acris/01-specification/index/rc_urls_ALL.csv")
DEST = pathlib.Path("D:/acris/02-acquisition/documents/_acqtest")
# ⚠ DO NOT CLAIM TO BE A BROWSER. This file used to send a Chrome User-Agent from
# curl. That is a misrepresentation to the server, and it is also the WRONG fix: the
# state viewer host (iapps.courts.state.ny.us) serves a Cloudflare MANAGED CHALLENGE
# that wants JS and cookies, so a UA string only ever papered over it. An honest
# client gets 403 + challenge here - that is the true measurement, and the document
# path is browser-assisted (see docs/sources/richmond/00-source.md §3).
UA = "acris-decoder/1.0 (public land records indexing; contact via repo owner)"


def fetch(url, dest, tries=3):
    """-> (ok, bytes, seconds, attempts). 403 backs off; it never hammers."""
    t0 = time.time()
    for a in range(tries):
        r = subprocess.run(["curl", "-sS", "-L", "-A", UA, "-o", str(dest),
                            "-w", "%{http_code} %{content_type}", url],
                           capture_output=True, text=True, timeout=300)
        code, _, ctype = (r.stdout or "").partition(" ")
        if code == "200" and "pdf" in ctype:
            return True, dest.stat().st_size, time.time() - t0, a + 1
        time.sleep(2 ** a)                     # BACK OFF, do not retry harder
    return False, 0, time.time() - t0, tries


def compress(pdf_path):
    """-> (bitonal_bytes, seconds, [ink_coverage_per_page])."""
    import fitz
    from PIL import Image
    t0 = time.time()
    doc = fitz.open(str(pdf_path))
    imgs, ink = [], []
    for pg in doc:
        pm = pg.get_pixmap(dpi=200)
        im = Image.frombytes("RGB" if pm.n >= 3 else "L",
                             [pm.width, pm.height], pm.samples).convert("L")
        bw = im.point(lambda x: 0 if x < 180 else 255, "1")
        h = bw.histogram()
        ink.append(h[0] / max(h[0] + h[-1], 1))       # fraction of black pixels
        imgs.append(bw)
    buf = io.BytesIO()
    if imgs:
        imgs[0].save(buf, format="TIFF", compression="group4",
                     save_all=True, append_images=imgs[1:])
    doc.close()
    return buf.getvalue(), time.time() - t0, ink


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--conc", type=int, default=4)
    a = ap.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)

    rows = []
    with URLS.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["doc_type"].upper() in ("DEED", "MORTGAGE"):
                rows.append(r)
                if len(rows) >= a.n:
                    break
    print(f"  testing {len(rows)} documents at conc {a.conc}\n")

    results = []

    def one(r):
        did = r["document_id"]
        raw = DEST / f"{did}.pdf"
        ok, size, secs, tries = fetch(r["image_url"], raw)
        if not ok:
            return {"id": did, "ok": False, "fetch_s": secs, "tries": tries}
        comp, csecs, ink = compress(raw)
        (DEST / f"{did}.tif").write_bytes(comp)
        return {"id": did, "ok": True, "orig": size, "comp": len(comp),
                "fetch_s": secs, "comp_s": csecs, "tries": tries,
                "pages": len(ink), "ink": sum(ink) / max(len(ink), 1)}

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.conc) as ex:
        for r in ex.map(one, rows):
            results.append(r)
            if r["ok"]:
                print(f"    {r['id']:<13} {r['orig']/1e6:>6.1f} MB -> "
                      f"{r['comp']/1e6:>5.2f} MB  {r['orig']/max(r['comp'],1):>5.1f}x · "
                      f"{r['pages']:>3}p · fetch {r['fetch_s']:>5.1f}s "
                      f"compress {r['comp_s']:>5.1f}s · ink {r['ink']*100:>4.1f}% "
                      f"{'(retried)' if r['tries']>1 else ''}")
            else:
                print(f"    {r['id']:<13} FAILED after {r['tries']} tries "
                      f"({r['fetch_s']:.1f}s)")
    el = time.time() - t0
    ok = [r for r in results if r["ok"]]
    if not ok:
        print("\n  no successful fetches.")
        return
    o = sum(r["orig"] for r in ok); c = sum(r["comp"] for r in ok)
    ftime = sum(r["fetch_s"] for r in ok); ctime = sum(r["comp_s"] for r in ok)
    retried = sum(1 for r in ok if r["tries"] > 1)
    print(f"\n  SUCCESS {len(ok)}/{len(results)}  ({retried} needed a retry)")
    print(f"  size    {o/1e6:.1f} MB -> {c/1e6:.2f} MB   {o/max(c,1):.1f}x")
    print(f"  per doc fetch {ftime/len(ok):.1f}s · compress {ctime/len(ok):.1f}s")
    print(f"  wall clock {el:.1f}s for {len(ok)} docs at conc {a.conc} "
          f"= {len(ok)/el:.2f} docs/s")
    print(f"  -> 2,426,404 docs = {2426404/max(len(ok)/el,1e-9)/3600:.0f} h "
          f"· {2426404*(c/len(ok))/1e12:.2f} TB stored")
    inks = [r["ink"] for r in ok]
    print(f"  ink coverage {min(inks)*100:.1f}%-{max(inks)*100:.1f}% "
          f"(near 0% would mean the threshold erased the page)")
    print(f"\n  files in {DEST}")


if __name__ == "__main__":
    main()
