"""WHERE DOES RICHMOND IMAGE FETCHING BREAK? — escalate gently, stop on degradation.

    ACRIS_CORPUS_ROOT=D:/acris python rc_img_boundary.py

⚠ THIS IS A BANDWIDTH QUESTION, NOT A REQUEST-RATE ONE. The index pull sustains
conc 56 against the SAME host on ~10 KB pages, while 20 documents at conc 4 failed
0/20 - because documents average 8.4 MB, roughly 800x larger. So the ceiling here
is throughput, and it must be measured in MB/s as well as docs/s.

⚠ ESCALATE, MEASURE, AND STOP. Each level uses FRESH documents (a re-fetch could
be served from a cache and lie about the rate), pauses between levels so one
level's burst does not poison the next, and ABORTS the whole sweep the moment a
level drops below the success floor. We already degraded this host once tonight
by going straight to conc 4 after a burst; the point of this script is to find
the boundary without doing that again.

⚠ COMPRESSION IS IN THE LOOP ON PURPOSE. Fetch-only timings overstate throughput
for a pipeline that must also convert. Bitonal G4 costs real CPU per page.
"""
from __future__ import annotations

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
DEST = pathlib.Path("D:/acris/02-acquisition/documents/_boundary")
# ⚠ DO NOT CLAIM TO BE A BROWSER. This file used to send a Chrome User-Agent from
# curl. That is a misrepresentation to the server, and it is also the WRONG fix: the
# state viewer host (iapps.courts.state.ny.us) serves a Cloudflare MANAGED CHALLENGE
# that wants JS and cookies, so a UA string only ever papered over it. An honest
# client gets 403 + challenge here - that is the true measurement, and the document
# path is browser-assisted (see docs/sources/richmond/00-source.md §3).
UA = "acris-decoder/1.0 (public land records indexing; contact via repo owner)"
LEVELS = [1, 2, 3, 4, 6]
PER_LEVEL = 6
SUCCESS_FLOOR = 0.80
COOLDOWN = 20


def load(n):
    out = []
    with URLS.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["doc_type"].upper() in ("DEED", "MORTGAGE") and r["recorded"] < "2026-07-01":
                out.append(r)
                if len(out) >= n:
                    break
    return out


def fetch_one(r):
    d = DEST / f"{r['document_id']}.pdf"
    t0 = time.time()
    p = subprocess.run(["curl", "-sS", "-L", "-A", UA, "-o", str(d),
                        "-w", "%{http_code} %{content_type}", r["image_url"]],
                       capture_output=True, text=True, timeout=300)
    code, _, ct = (p.stdout or "").partition(" ")
    el = time.time() - t0
    if code == "200" and "pdf" in ct:
        return {"ok": True, "bytes": d.stat().st_size, "s": el, "path": d}
    return {"ok": False, "code": code, "s": el}


def compress(path):
    import fitz
    from PIL import Image
    t0 = time.time()
    doc = fitz.open(str(path))
    imgs = []
    for pg in doc:
        pm = pg.get_pixmap(dpi=200)
        im = Image.frombytes("RGB" if pm.n >= 3 else "L",
                             [pm.width, pm.height], pm.samples).convert("L")
        imgs.append(im.point(lambda x: 0 if x < 180 else 255, "1"))
    buf = io.BytesIO()
    if imgs:
        imgs[0].save(buf, format="TIFF", compression="group4",
                     save_all=True, append_images=imgs[1:])
    doc.close()
    return len(buf.getvalue()), time.time() - t0, len(imgs)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    pool = load(sum(LEVELS[:len(LEVELS)]) * 0 + PER_LEVEL * len(LEVELS))
    print(f"  {len(pool)} candidate documents (pre-July, DEED/MORTGAGE)\n")
    print(f"  {'conc':>4} {'ok':>6} {'fetch MB/s':>11} {'docs/s':>7} "
          f"{'compress':>9} {'end-to-end':>11}  verdict")
    idx = 0
    for conc in LEVELS:
        batch = pool[idx:idx + PER_LEVEL]
        idx += PER_LEVEL
        if len(batch) < PER_LEVEL:
            print("  (out of candidates)")
            break
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=conc) as ex:
            res = list(ex.map(fetch_one, batch))
        fetch_el = time.time() - t0
        ok = [r for r in res if r["ok"]]
        rate = len(ok) / max(len(res), 1)
        mb = sum(r["bytes"] for r in ok) / 1e6
        # compress serially - CPU bound, measured separately
        ct = cb = pages = 0
        for r in ok:
            b, s, pg = compress(r["path"])
            cb += b; ct += s; pages += pg
        total = fetch_el + ct
        verdict = "OK" if rate >= SUCCESS_FLOOR else "DEGRADED"
        print(f"  {conc:>4} {len(ok):>3}/{len(res):<2} {mb/max(fetch_el,1e-9):>11.2f} "
              f"{len(ok)/max(fetch_el,1e-9):>7.2f} {ct/max(len(ok),1):>8.1f}s "
              f"{len(ok)/max(total,1e-9):>10.2f}/s  {verdict}", flush=True)
        if rate < SUCCESS_FLOOR:
            print(f"\n  STOPPING at conc {conc} — success {rate*100:.0f}% below "
                  f"the {SUCCESS_FLOOR*100:.0f}% floor. Not escalating further.")
            break
        if cb:
            print(f"       compressed {mb:.1f} MB -> {cb/1e6:.2f} MB "
                  f"({mb/max(cb/1e6,1e-9):.1f}x) over {pages} pages")
        time.sleep(COOLDOWN)
    print(f"\n  files in {DEST}")


if __name__ == "__main__":
    main()
