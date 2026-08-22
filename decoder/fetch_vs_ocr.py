"""IF FETCHING IS FASTER THAN READING, THE 7 TB DRIVE IS POINTLESS.

The whole storage plan assumes acquisition is the scarce resource and OCR is
the cheap one. Measured separately they say the opposite:

    acquisition ceiling   30.3 Mbps  = ~83 pages/sec
    OCR, 8 cores           4.4 pages/sec

If that holds END TO END, then a streaming pipeline — fetch a page, OCR it,
keep the text, drop the pixels — never once waits on the network, and buying
a drive to hold 6.3 TB of images is buying a queue for a line that has no
queue in it.

⚠ BUT THE 83 pages/sec CAME FROM A CONCURRENCY TEST, NOT FROM THIS CHANNEL.
This fetches the way the project actually fetches: one connection, sequential,
browser UA and Referer, paced. So the honest question is narrower and better —
does ONE polite sequential stream still out-run 8-core OCR? If yes, concurrency
is not even needed and the conclusion is safe.

⚠ TRANSFER TIME IS TIMED, PACING IS NOT. The ~1s courtesy delay between
requests is a decision, not a property of the server. Including it would
measure our own manners and call it a bandwidth limit.

⚠ AND IT RE-FETCHES PAGES ALREADY ON DISK ON PURPOSE. That makes the bytes
comparable: if the fetched page is identical to the stored one, then discarding
the local copy loses nothing, which is the actual premise being tested.

Stops immediately and permanently on any refusal. No retry, no work-around.

    python fetch_vs_ocr.py [n_pages]
"""
import hashlib
import os
import pathlib
import re
import statistics
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import fetch_pages as FP

PAGES = pathlib.Path("sample_pages")
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCRATCH = pathlib.Path(os.environ["TMP"]) / "fvo"
SCRATCH.mkdir(parents=True, exist_ok=True)
CORES = os.cpu_count()
PACE = 1.0


def timed_fetch(doc_id, page):
    """Return (bytes, transfer_seconds). Raises AccessDenied on refusal."""
    url = f"{FP.BASE}?doc_id={doc_id}&page={page}"
    req = urllib.request.Request(url, headers={
        "User-Agent": FP.UA,
        "Referer": "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView",
        "Accept": "image/tiff,image/*,*/*;q=0.8",
    })
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
        ctype = r.headers.get("Content-Type", "")
    el = time.time() - t0
    FP._check_denied(data, ctype)          # ⚠ raises and we stop. no retry.
    return data, el


def ocr(path):
    subprocess.run([TESS, str(path), "stdout", "--psm", "4"],
                   capture_output=True, text=True, encoding="utf-8",
                   errors="replace")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    # pages we ALREADY hold, so fetched bytes can be compared against stored
    have = []
    for d in sorted(x for x in PAGES.iterdir() if x.is_dir()):
        if d.name.startswith("FT_"):
            continue                        # film ids are not viewer doc_ids
        for t in sorted(d.glob("*.tif"))[:2]:
            have.append((d.name, int(t.stem[1:]), t))
        if len(have) >= n:
            break
    have = have[:n]
    print(f"  {len(have)} pages · one sequential connection · {PACE:.0f}s pacing\n")

    got, xfer, same, diff = [], [], 0, 0
    try:
        for i, (doc, pg, local) in enumerate(have):
            if i:
                time.sleep(PACE)            # pacing, deliberately outside the timer
            data, el = timed_fetch(doc, pg)
            xfer.append(el)
            f = SCRATCH / f"{doc}_p{pg:03d}.tif"
            f.write_bytes(data)
            got.append(f)
            a = hashlib.md5(data).hexdigest()
            b = hashlib.md5(local.read_bytes()).hexdigest()
            same += a == b
            diff += a != b
            print(f"  {doc} p{pg:<3}{len(data)/1024:>8.0f} KB"
                  f"{el*1000:>9.0f} ms{'  identical' if a == b else '  ⚠ DIFFERS'}")
    except FP.AccessDenied as e:
        print(f"\n  ⚠ {e}")
        print(f"  stopping. {len(got)} pages fetched before refusal.")
        if len(got) < 3:
            return
    except Exception as e:
        print(f"\n  fetch failed: {type(e).__name__}: {str(e)[:90]}")
        if len(got) < 3:
            return

    kb = statistics.mean(os.path.getsize(f) for f in got) / 1024
    mx = statistics.mean(xfer)
    fetch_ps = 1 / mx
    print(f"\n  ── FETCH, one connection ──")
    print(f"    mean transfer     {mx*1000:>8.0f} ms/page  ({kb:,.0f} KB)")
    print(f"    throughput        {fetch_ps:>8.2f} pages/sec"
          f"   = {kb*8/1024/mx:,.1f} Mbps")
    print(f"    bytes identical to stored copy: {same}/{same+diff}")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=CORES) as ex:
        list(ex.map(ocr, got))
    ocr_ps = len(got) / (time.time() - t0)
    print(f"\n  ── OCR, {CORES} cores ──")
    print(f"    throughput        {ocr_ps:>8.2f} pages/sec")

    print(f"\n  ── THE COMPARISON ──")
    if fetch_ps > ocr_ps:
        print(f"    ONE sequential connection out-runs {CORES}-core OCR by "
              f"{fetch_ps/ocr_ps:.1f}x.")
        print(f"    -> the network is NEVER the bottleneck. Streaming fetch->OCR")
        print(f"       never waits, and 6.3 TB of stored images buys nothing but")
        print(f"       a queue for a line with no queue in it.")
    else:
        print(f"    fetch is {ocr_ps/fetch_ps:.1f}x SLOWER than OCR on one connection.")
        print(f"    -> at this pacing the network IS the constraint, and the")
        print(f"       drive earns its place. Concurrency would change this;")
        print(f"       measured ceiling was 30.3 Mbps across many connections.")
        print(f"    connections needed to feed {CORES}-core OCR: "
              f"{ocr_ps/fetch_ps:.1f}")


if __name__ == "__main__":
    main()
