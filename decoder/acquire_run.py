"""ACQUIRE WHOLE DOCUMENTS, ALL PAGES, AND MEASURE THE SUSTAINABLE RATE.

    ACRIS_CORPUS_ROOT=E:/acris python acquire_run.py --docs 100

⚠ ROOT IS AN ENV VAR BECAUSE THE DRIVE IS NOT HERE YET. Everything lands under
$ACRIS_CORPUS_ROOT (default ./corpus). Moving to the external drive is one
variable, not a code change.

⚠ THERE IS NO SERVER-SIDE WHOLE-DOCUMENT ENDPOINT. Verified 2026-08-12 against
2003120200544003 (8 pages): `no-page`, `allpages` and `page-0` each returned the
SAME 13,684 bytes with HTTP 200 and content-type image/tiff - and that blob is
not page 1, it is the PLACEHOLDER (md5 4081a3f2...), which page 1 is not. The
print and PDF paths returned an ACRIS error page. The viewer's Save button is
Acordex VTU + jsPDF assembling a PDF IN THE BROWSER, one GetImage call per page
("Loading Page $1 for Saving..."). So save costs the same requests as fetching
pages directly, and adds a lossy canvas re-encode on top. We fetch the pages.

⚠ PAGE COUNT COMES FROM THE MAP, AND A SHORT DOCUMENT IS A FAILURE, NOT A
DOCUMENT. hid_TotalPages is the independent expectation; if fewer pages arrive
the document is marked short rather than recorded as complete. This is the trap
fetch_document.py was written for: a 1-of-8 read that looks exactly like
success and that the ledger would never re-fetch.

⚠ PACING IS ADDITIVE-INCREASE / MULTIPLICATIVE-DECREASE AND A REFUSAL ENDS THE
RUN. 2026-08-09 established the limit is address-level rate throttling, not bot
detection - Login's own browser was refused at the same moment. So slowing down
is the correct response and the polite one. Nothing here rotates an address,
varies a User-Agent, replays a session, or retries a refused request. If the
server says no, this stops and reports.
"""
import argparse
import collections
import hashlib
import io
import json
import os
import pathlib
import sqlite3
import sys
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from PIL import Image

from fetch_pages import UA, BASE, PLACEHOLDER, AccessDenied, _check_denied

ROOT = pathlib.Path(os.environ.get("ACRIS_CORPUS_ROOT", "corpus"))
VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView"


def klass(d):
    return "film" if d.startswith("FT_") else "book" if d.startswith("BK_") else "digital"


def ledger(db):
    c = sqlite3.connect(db)
    c.execute("""CREATE TABLE IF NOT EXISTS doc(
        doc_id TEXT PRIMARY KEY, cls TEXT, doc_type TEXT, expect INT,
        got INT, bytes INT, secs REAL, status TEXT, at TEXT)""")
    c.commit()
    return c


def pick(n, per_class):
    """Spread across scan classes. ⚠ NOT the first n rows - the file is ordered,
    and the head of it is one era."""
    want, seen = [], collections.Counter()
    with open("acris_maps.jsonl", "rb") as fh:
        for i, line in enumerate(fh):
            if len(want) >= n:
                break
            try:
                d = json.loads(line)
            except ValueError:
                continue
            npg = d.get("hid_TotalPages") or 0
            k = klass(d.get("doc_id", ""))
            if npg < 1 or seen[k] >= per_class or i % 97:
                continue
            seen[k] += 1
            want.append((d["doc_id"], npg, d.get("doc_type") or "", k))
    return want


def get(doc, page, timeout=90):
    req = urllib.request.Request(
        f"{BASE}?doc_id={doc}&page={page}",
        headers={"User-Agent": UA, "Referer": f"{VIEW}?doc_id={doc}",
                 "Accept": "image/tiff,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", ""), r.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=int, default=100)
    ap.add_argument("--start-interval", type=float, default=1.0)
    ap.add_argument("--floor", type=float, default=0.5)
    ap.add_argument("--ease", type=float, default=0.97)
    ap.add_argument("--max-pages", type=int, default=1400,
                    help="hard stop so a test cannot become a bulk run")
    a = ap.parse_args()

    ROOT.mkdir(parents=True, exist_ok=True)
    db = ledger(ROOT / "ledger.sqlite")
    docs = pick(a.docs, a.docs // 3 + 1)
    done = {r[0] for r in db.execute("SELECT doc_id FROM doc WHERE status='ok'")}
    docs = [d for d in docs if d[0] not in done]
    total_expect = sum(d[1] for d in docs)
    print(f"  root: {ROOT.resolve()}")
    print(f"  {len(docs)} documents, {total_expect:,} pages expected "
          f"(cap {a.max_pages})\n")

    iv = a.start_interval
    npages = nbytes = 0
    per_class = collections.defaultdict(lambda: [0, 0])   # pages, bytes
    times = []
    t_run = time.time()
    short = refused = 0

    for doc, expect, dt, k in docs:
        if npages >= a.max_pages:
            print(f"\n  page cap {a.max_pages} reached - stopping cleanly.")
            break
        frames, dbytes, t0 = [], 0, time.time()
        for p in range(1, expect + 1):
            if npages >= a.max_pages:
                break
            t = time.time()
            try:
                data, ctype, st = get(doc, p)
            except Exception as e:
                print(f"  {doc} p{p}: TRANSPORT {type(e).__name__}")
                break
            el = time.time() - t
            try:
                _check_denied(data, ctype)
            except AccessDenied as e:
                print(f"\n  ⚠ REFUSED after {npages} pages / "
                      f"{time.time()-t_run:.0f}s. STOPPING.\n  {e}")
                refused = 1
                break
            if data[:2] not in (b"II", b"MM"):
                print(f"  {doc} p{p}: not an image ({len(data):,}b) - skipping doc")
                break
            # ⚠ PAST THE END OF A DOCUMENT, ACRIS RETURNS HTTP 200 WITH A VALID
            # 13,684-BYTE TIFF, NOT A 404. Verified 2026-08-12: page 9 of an
            # 8-page document, the page parameter omitted, and allpages=true all
            # return the identical placeholder (md5 4081a3f2...). So "fetch until
            # it fails" NEVER FAILS - it writes placeholder pages into documents
            # forever and they look exactly like content.
            #
            # This is the same shape as every other bug this project has hit:
            # A CHECK THAT REPORTS SUCCESS BECAUSE IT LOOKED IN THE WRONG PLACE.
            if hashlib.md5(data).hexdigest() == PLACEHOLDER:
                print(f"  {doc} p{p}: PLACEHOLDER - document ends at p{p-1} "
                      f"(map said {expect})")
                break
            frames.append(data)
            dbytes += len(data)
            npages += 1
            nbytes += len(data)
            times.append(el)
            per_class[k][0] += 1
            per_class[k][1] += len(data)
            iv = max(a.floor, iv * a.ease)          # additive-ish increase
            time.sleep(iv)
        if refused:
            break
        secs = time.time() - t0
        ok = len(frames) == expect
        short += (not ok)
        if frames:
            d = ROOT / k / doc
            d.mkdir(parents=True, exist_ok=True)
            for i, b in enumerate(frames, 1):
                (d / f"p{i:04d}.tif").write_bytes(b)
            # ⚠ THE TIFFs ARE THE ARCHIVE; THE PDF IS A CONVENIENCE COPY. This
            # is the same artifact the viewer's Save button produces, built
            # locally from bytes already on disk - no extra ACRIS requests, and
            # the originals stay untouched. Never OCR the PDF: it goes through a
            # raster re-encode, and the faint dot-matrix stamps it damages are
            # exactly the join keys.
            try:
                ims = [Image.open(io.BytesIO(b)) for b in frames]
                # ⚠ NEVER convert("L") A BITONAL SCAN ON THE WAY INTO A PDF. Measured
                # 2026-08-12: it cost 15.2x on disk (131 KB of TIFF -> 1,998 KB of
                # PDF) because 8-bit grey cannot use Group-4, so PIL stores it
                # essentially raw. Left in, the 9.3 TB corpus would have been
                # 141 TB. Mode "1" in, Group-4 out, 1.0x.
                ims = [im if im.mode == "1" else im.convert("1") for im in ims]
                ims[0].save(d / f"{doc}.pdf", save_all=True,
                            append_images=ims[1:])
            except Exception as e:
                print(f"    (pdf failed for {doc}: {type(e).__name__})")
        db.execute("INSERT OR REPLACE INTO doc VALUES(?,?,?,?,?,?,?,?,?)",
                   (doc, k, dt, expect, len(frames), dbytes, round(secs, 2),
                    "ok" if ok else "short", time.strftime("%Y-%m-%dT%H:%M:%S")))
        db.commit()
        print(f"  {doc:<20}{k:<8}{dt:<8}{len(frames):>3}/{expect:<3}"
              f"{dbytes/1024:>9,.0f} KB{secs:>7.1f}s  {'ok' if ok else 'SHORT'}")

    el = time.time() - t_run
    if not npages:
        print("\n  no pages fetched"); return
    kb = nbytes / npages / 1024
    rate = npages / el
    print(f"\n  ── {npages:,} pages · {el/60:.1f} min · {refused} refusal(s) · "
          f"{short} short doc(s) ──")
    print(f"  request latency  mean {sum(times)/len(times):.2f}s  "
          f"min {min(times):.2f}  max {max(times):.2f}")
    print(f"  achieved rate    {rate:.2f} pages/s  (interval settled at {iv:.2f}s)")
    print(f"  page size        {kb:,.0f} KB mean")
    print(f"\n  {'class':<10}{'pages':>8}{'KB/page':>10}")
    for k, (p, b) in sorted(per_class.items()):
        print(f"  {k:<10}{p:>8,}{b/p/1024:>10,.0f}")
    tb = 148238970 * kb * 1024 / 1e12
    print(f"\n  PROJECTED FOR 148,238,970 PAGES")
    print(f"    storage        {tb:,.1f} TB")
    print(f"    at {rate:.2f} p/s   {148238970/rate/86400:,.0f} days single stream")
    for c in (4, 8, 16, 30):
        print(f"    x{c:<3} streams  {148238970/(rate*c)/86400:>6,.0f} days")
    print(f"\n  ⚠ A SHORT SAMPLE CANNOT ESTABLISH A SUSTAINABLE RATE. This ran")
    print(f"    {el/60:.0f} minutes. The 2026-08-09 log shows refusals arriving after")
    print(f"    4, 1 and 11 requests under a different regime - the limit moves.")
    print(f"    Treat the projection as a ceiling, not a schedule.")


if __name__ == "__main__":
    main()
