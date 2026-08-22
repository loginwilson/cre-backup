"""PARALLEL ACQUISITION. aiohttp, bounded pool, ledger-resumable.

    ACRIS_CORPUS_ROOT=E:/acris python acquire_async.py --docs 200 --conc 8

⚠ WHY CONCURRENCY IS THE RIGHT SHAPE HERE AND urllib WAS NOT. Single-stream
throughput is bounded by ROUND-TRIP LATENCY, not by politeness: measured 0.26s
mean per request, so one connection tops out near 3 pages/s no matter how small
the sleep. OCR_STRATEGY.md records the async client reaching 25.7-31 pg/s, and
records in the same breath that "ACRIS is blocking us (x5)" was WRONG - it was
urllib probes being compared against an aiohttp job, different headers, different
treatment. The job was never blocked. A browser opens 6+ connections; a bounded
pool of 8-12 is that, not an assault.

⚠ WHAT THIS STILL WILL NOT DO. No address rotation, no User-Agent variation, no
session replay, no retry of a refused request. On a matched refusal every task is
cancelled and the run ends. The limiter is address-level (2026-08-09: Login's own
browser was refused at the same moment a script was), so blowing through it takes
out Login's own ACRIS access too. Backing off is self-interest, not just manners.

⚠ CONCURRENCY IS AIMD ON A SHARED GATE, NOT N INDEPENDENT LOOPS. Every worker
draws from one delay value. On success it eases down; on ANY refusal the whole
run stops. N loops each with their own timer would multiply the request rate by N
while each one believed it was being polite.

⚠ THE PAGE CAP APPLIES BETWEEN DOCUMENTS, NOT INSIDE ONE. The sync version
checked inside the page loop and truncated an 84-page document at 28, then
recorded it as `short` - indistinguishable from a real defect. A cap is a
stopping rule, not a corruption rule.
"""
import argparse
import asyncio
import collections
import hashlib
import io
import json
import os
import pathlib
import sqlite3
import sys
import time

import aiohttp
import img2pdf
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from fetch_pages import UA, BASE, PLACEHOLDER, AccessDenied, _check_denied

import corpus_paths as CP
ROOT = CP.ROOT
VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView"


def klass(d):
    return "film" if d.startswith("FT_") else "book" if d.startswith("BK_") else "digital"


class Gate:
    """One shared delay for every worker. Additive ease, hard stop on refusal."""

    def __init__(self, start, floor, ease, max_fail=400):
        self.iv, self.floor, self.ease = start, floor, ease
        self.stopped = False
        self.reason = None
        self.lock = asyncio.Lock()
        # ⚠ A CIRCUIT BREAKER, BECAUSE "SKIP AND CARRY ON" IS NOT AN ERROR POLICY.
        # 2026-08-17 03:58-05:00: the link dropped and every fetch failed. Each failure
        # was caught per-document, the loop moved to the next parcel, and the run spent
        # AN HOUR issuing ~294,000 requests that could never succeed — writing them all
        # to the ledger as `empty`, which downstream reads as "this document has no
        # image". An outage silently became a corpus fact.
        # Consecutive failures are the signal. One is noise; hundreds in a row means the
        # far end or the link is gone, and continuing is neither useful nor polite.
        self.fails = 0
        self.max_fail = max_fail

    def fail(self, why=""):
        self.fails += 1
        if self.fails >= self.max_fail and not self.stopped:
            self.stop(f"{self.fails} consecutive failures — link or service down ({why})")

    def good(self):
        self.fails = 0

    async def wait(self):
        if self.iv > 0:
            await asyncio.sleep(self.iv)

    def ok(self):
        self.iv = max(self.floor, self.iv * self.ease)
        self.good()

    def stop(self, why):
        if not self.stopped:
            self.stopped = True
            self.reason = why


def ledger(db):
    c = sqlite3.connect(db)
    c.execute("""CREATE TABLE IF NOT EXISTS doc(
        doc_id TEXT PRIMARY KEY, cls TEXT, doc_type TEXT, expect INT,
        got INT, bytes INT, secs REAL, status TEXT, at TEXT)""")
    c.commit()
    return c


def pick(n, per_class, stride):
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
            if npg < 1 or seen[k] >= per_class or i % stride:
                continue
            seen[k] += 1
            want.append((d["doc_id"], npg, d.get("doc_type") or "", k))
    return want


# ⚠ PARCEL-ORDERED QUEUE — added 2026-08-17. `pick()` above STRIDES A SAMPLE out of
# acris_maps.jsonl (`i % stride`), which is right for a bakeoff and wrong for a walk:
# it can never deliver one parcel's record complete, in order. Login, 2026-08-17:
# *"prep for highest output acquisition ... and sort by parcel."*
#
# ⚠ THIS CHANGES ORDER ONLY. Same gate, same AIMD, same bounded pool, same
# stop-on-refusal. Nothing here fetches faster or differently — the queue is
# re-sorted, not the client. Do NOT add rotation, retry-on-refusal, or a second gate.
#
# ⚠ OLDEST FIRST, and the ordering rule is the one measured in parcel_spec_db.py:
# document_date then recorded_date, NEVER document_id (an intake stamp — it preceded
# recording by 5 days on 2016081800161001).
_NOIMG = None
_PAGES = None


def page_counts(doc_ids):
    """{doc_id: pages} for the ids we know. ⚠ A LOOKUP, NOT A LOAD — 17M rows would be
    ~340 MB resident in every worker; a parcel needs a few dozen, so query by batch."""
    global _PAGES
    out = {}
    if _PAGES is None:
        f = CP.SPEC / "page_counts.db"
        _PAGES = sqlite3.connect(f"file:{f}?mode=ro", uri=True) if f.exists() else False
    if not _PAGES or not doc_ids:
        return out
    ids = list(doc_ids)
    for i in range(0, len(ids), 900):
        chunk = ids[i:i+900]
        q = ",".join("?" * len(chunk))
        for d, n in _PAGES.execute(
                f"SELECT doc_id, MAX(n) FROM pages WHERE doc_id IN ({q}) GROUP BY doc_id", chunk):
            if n and n > 0:
                out[d] = n
    return out


def noimage_ids():
    """⚠ THE 138,867 DOCUMENTS THAT MUST NEVER BE FETCHED. They have no image; the index
    row IS the record. Requesting one costs a round trip and returns the placeholder —
    which our loop reads as END, so the document is written as `empty` and looks like a
    defect rather than a document that is complete by nature. Measured 2026-08-17: 26 had
    already leaked into the ledger before this filter existed.

    ⚠ NOT a page-count check and not a retry rule — a MEMBERSHIP test against
    noimage_index, loaded once per process."""
    global _NOIMG
    if _NOIMG is None:
        _NOIMG = set()
        # ⚠ THE AUTHORITATIVE LIST IS THE ID FILE, NOT THE ACQUIRED INDEX. Measured
        # 2026-08-18: `_noimage_ids.txt` holds all **174,142** image-less documents,
        # while `noimage_index/master.jsonl.gz` holds the **138,867** whose index record
        # has actually been pulled — the index-acquisition run stopped at 79.7%.
        # Filtering on the acquired subset means re-fetching the other 35,275 forever,
        # each returning a placeholder. Filter on what EXISTS; acquire the remainder
        # separately.
        ids = CP.NOIMAGE_IDS
        if ids.exists():
            for line in ids.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if s:
                    _NOIMG.add(s)
            return _NOIMG
        f = CP.NOIMAGE_INDEX / "master.jsonl.gz"
        if f.exists():
            import gzip as _gz
            with _gz.open(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        d = json.loads(line).get("document_id")
                    except ValueError:
                        continue
                    if d:
                        _NOIMG.add(d)
    return _NOIMG


def pick_parcel(bbls, n, skip_done=True, spec_db=None):
    """Documents for the given BBLs, oldest first. Returns pick()'s tuple shape.

    ⚠ SELECTION HERE IS AN INDEXED QUERY, AND THAT IS THE POINT. pick() above scans
    acris_maps.jsonl — 3.85 GB — ONCE PER PROCESS, so an 8-way run reads ~31 GB before
    fetching a single page, inside the timed window. Measured 2026-08-17: 8x8 reported
    40.6 pg/s with CPU at 30.8% mean, i.e. neither CPU- nor network-bound; it was
    waiting on that scan. The spec db answers the same question from an index.""" 
    if spec_db is None:
        spec_db = str(CP.SPEC_DB)
    # ⚠ READ-ONLY — selection only reads. See LIVE_SYNC.md §9.
    con = sqlite3.connect(f"file:{spec_db}?mode=ro", uri=True)
    marks = ("AND NOT EXISTS (SELECT 1 FROM walk w WHERE w.bbl=pd.bbl "
             "AND w.document_id=d.document_id AND w.stage='acquired')") if skip_done else ""
    # ⚠ ACQUIRE THE FAMILY, NOT THE LOT — otherwise the folder names documents it will
    # never fetch. parcel_folder.py resolves lineage at read time and lists a
    # predecessor's instruments; if selection stays keyed on the single current BBL,
    # every one of those rows is permanently "not acquired". Measured on 4000110001:
    # 46 documents under its own name, 60 across its 4 lot names — and the 14 it was
    # missing include a $260,714,020 mortgage filed under lot 4000110003.
    try:
        import lineage
        fam, fseen = [], set()
        for b in bbls:
            for x in lineage.family(b):
                if x not in fseen:
                    fseen.add(x); fam.append(x)
        bbls = fam
    except Exception:
        pass          # ⚠ lineage is an ENRICHMENT; never let it block acquisition
    want, seen = [], set()
    # ⚠ RICHMOND DOCUMENTS ARE NOT ACRIS DOCUMENTS — EXCLUDE THEM BY PREFIX.
    # The Legal Instruments specification is ONE spine with TWO registers: a BBL query
    # returns an ACRIS mortgage and a Richmond deed side by side, which is the point.
    # But they have different custodians and different transports: ACRIS serves bitonal
    # page TIFFs from a836-acris.nyc.gov to any client; Richmond serves whole-document
    # PDFs through a browser-native viewer behind a Cloudflare managed challenge.
    # ⚠ Measured 2026-08-19: parcel_document went from 0 to 2,763,250 RC_ rows in about
    # an hour as the Richmond land job ran. Without this filter the ACRIS walk would
    # request RC_2825429 from the ACRIS host at scale and fail on every one — mass
    # failures that read exactly like an ACRIS outage, on a source that is perfectly fine.
    # Richmond is acquired by its own path. See docs/sources/richmond/00-source.md.
    for bbl in bbls:
        for doc, ty in con.execute(f"""
                SELECT d.document_id, COALESCE(d.doc_type,'')
                FROM parcel_document pd JOIN document d USING (document_id)
                WHERE pd.bbl=? AND substr(d.document_id,1,3) <> 'RC_' {marks}
                ORDER BY COALESCE(NULLIF(d.doc_date,''), d.recorded_date),
                         d.document_id""", (bbl,)):
            if doc in seen:          # one document can touch several lots of one parcel set
                continue
            seen.add(doc)
            if doc in noimage_ids():   # ⚠ never fetch — the index is its whole record
                continue
            # ⚠ expect=0: page count is UNKNOWN here. acris_maps.jsonl carries
            # hid_TotalPages; the spec index does not. The fetch loop already stops on
            # the placeholder md5, so 0 means "walk until END", never "zero pages".
            want.append((doc, 0, ty, klass(doc)))
            if len(want) >= n:
                con.close(); want = _with_pages(want); return want
    con.close()
    return _with_pages(want)


def _with_pages(want):
    """⚠ REPLACE expect=0 WITH THE KNOWN COUNT SO THE LOOP NEED NOT PROBE FOR THE END.
    Unknown stays 0 and still walks to the placeholder — 3.5% of documents, unchanged.
    Validated against 233,712 already-fetched documents: 99.93% exact, ZERO under-counts,
    159 over by a page or more (which cost one wasted request and nothing else)."""
    pc = page_counts([d for d, _, _, _ in want])
    if not pc:
        return want
    return [(d, pc.get(d, 0), ty, k) for d, _, ty, k in want]


async def one_page(sess, gate, doc, p, stats):
    await gate.wait()
    if gate.stopped:
        return None
    t = time.time()
    async with sess.get(f"{BASE}?doc_id={doc}&page={p}",
                        headers={"Referer": f"{VIEW}?doc_id={doc}"}) as r:
        data = await r.read()
        ctype = r.headers.get("Content-Type", "")
    stats["lat"].append(time.time() - t)
    try:
        _check_denied(data, ctype)
    except AccessDenied as e:
        gate.stop(str(e))
        return None
    if data[:2] not in (b"II", b"MM"):
        return None
    if hashlib.md5(data).hexdigest() == PLACEHOLDER:
        return "END"
    gate.ok()
    return data


async def one_doc(sess, gate, sem, rec, stats, db_q, want_pdf=False):
    doc, expect, dt, k = rec
    async with sem:
        if gate.stopped:
            return
        t0 = time.time()
        # ⚠ PAGES OF ONE DOCUMENT GO IN ORDER AND SEQUENTIALLY. The parallelism
        # is ACROSS documents. Firing a document's pages concurrently would make
        # the placeholder-terminated end ambiguous - page 9 might land before
        # page 8 and there would be no way to say where the document stopped.
        frames = []
        # ⚠ expect==0 means UNKNOWN, NOT ZERO — and this was a silent total failure.
        # pick_parcel() returns 0 because the spec index carries no page count, and
        # its comment says "0 means walk until END". But the bound was `range(1,
        # expect+1)`, and range(1,1) is EMPTY: every parcel-driven document fetched
        # nothing, wrote nothing, and raised nothing. CEILING is a runaway guard, not
        # an expectation — the placeholder md5 is what actually ends a document.
        CEILING = 2000
        hit_end = False
        for p in range(1, (expect + 1) if expect else CEILING):
            try:
                data = await one_page(sess, gate, doc, p, stats)
            except Exception as e:
                stats.setdefault("pageerr", collections.Counter())[type(e).__name__] += 1
                gate.fail(type(e).__name__)      # ⚠ count it; an outage must end the run
                break
            if data == "END":
                hit_end = True      # ⚠ the placeholder is the TRUE end, whatever the map said
                break
            if data is None:
                break
            frames.append(data)
        if gate.stopped and not frames:
            return
        # ⚠ ONE MULTIPAGE TIFF PER DOCUMENT, NOT ONE FILE PER PAGE. Measured
        # 2026-08-12: identical bytes (0.99x), G4 compression preserved because
        # nothing is re-encoded, and page N still opens in 3ms without touching
        # the others. The reason is file COUNT, not size: 148M loose pages costs
        # ~148 GB of NTFS metadata and would hit an inode quota on Torch's
        # parallel filesystem long before the storage quota. 17M files does not.
        #
        # ⚠ AND THE doc_id IS THE FILENAME, which is a stronger binding than a
        # PDF container - nothing has to be opened to know what a file is.
        # ⚠ A DOCUMENT WITH NO FRAMES IS NOT A DOCUMENT. Writing it would create an
        # empty container that the ledger records as present and never re-fetches.
        if not frames:
            # ⚠ NEVER RECORD `empty` WHILE THE GATE IS STOPPING. `empty` means "asked and
            # this document has no image"; during an outage we asked nothing and learned
            # nothing, and writing the row would make a network fault permanent.
            if gate.stopped:
                return
            gate.fail("no frames")
            db_q.append((doc, k, dt, expect, 0, 0, round(time.time() - t0, 2),
                         "empty", time.strftime("%Y-%m-%dT%H:%M:%S")))
            return
        # ⚠ ONE WHOLE-DOCUMENT PDF, IN A SHARDED STORE — NOT loose pages and not a
        # flat directory. Login, 2026-08-17: *"it has to be organized, otherwise it
        # will be impossible to reason the extraction if its all loose."* The PDF
        # embeds the ORIGINAL G4 bytes (verified: /CCITTFaxDecode, bpc=1, exact
        # dimensions) so nothing is re-encoded — it is the TIFF data in a container
        # that opens anywhere. The 2-char shard keeps any one directory small at
        # 17M documents; by-parcel/ hardlinks into this store, it never copies.
        d = CP.STORE / doc[:2]
        d.mkdir(parents=True, exist_ok=True)
        out = d / f"{doc}.pdf"
        # ⚠ img2pdf, NEVER PIL, AND THIS WAS MEASURED THE HARD WAY. PIL's PDF writer
        # RE-ENCODES G4 and emits a malformed stream: pypdf AND MuPDF both reject it
        # ("invalid code in 2d faxd"), and 0 of 5 pages survived a round-trip. It
        # looked correct by every cheap check — /CCITTFaxDecode, bpc=1, exact
        # dimensions — which is precisely why the filter tag is not evidence.
        # img2pdf COPIES the G4 stream instead of re-encoding: 5/5 pixel-identical,
        # zero decoder complaints. ⚠ Verify pixels through a decoder, never a header.
        try:
            out.write_bytes(img2pdf.convert(frames))
        except Exception as e:
            # ⚠ FALL BACK TO LOOSE PAGES RATHER THAN LOSE THE FETCH. The bytes
            # cost real requests; a container-writing failure must never discard
            # them.
            stats.setdefault("writeerr", collections.Counter())[type(e).__name__] += 1
            dd = d / doc; dd.mkdir(parents=True, exist_ok=True)
            for i, b in enumerate(frames, 1):
                (dd / f"p{i:04d}.tif").write_bytes(b)
        # ⚠ `want_pdf` IS GONE, NOT DEMOTED. It used to write the PDF as a second
        # artifact beside a multipage TIFF; the PDF is now the only one, because it
        # carries the same G4 bytes and one artifact cannot disagree with itself.
        nb = sum(len(b) for b in frames)
        stats["pages"] += len(frames)
        stats["bytes"] += nb
        stats["cls"][k][0] += len(frames)
        stats["cls"][k][1] += nb
        # ⚠ expect==0 IS "UNKNOWN", AND "short" WOULD BE A LIE THAT NEVER SETTLES.
        # The spec index carries no page count, so parcel-driven work always has
        # expect=0 — and `len(frames)==expect` then marks every COMPLETE document
        # short. Measured: 46/46 on BBL 4000110001. Because the resume set is
        # `status='ok'`, every one would be re-fetched on every pass forever, and an
        # overnight run would spend the night re-downloading the same parcel.
        # With expect unknown, the placeholder md5 IS the authority on the end.
        # ⚠ A DOCUMENT THAT ENDED ON THE PLACEHOLDER IS COMPLETE, FULL STOP. Without
        # this, the 159-in-233,712 documents whose map count runs high would be marked
        # `short` forever — and `short` is not in the resume set, so every run would
        # re-fetch them. Trusting the map over the server would manufacture that loop.
        ok = hit_end or ((len(frames) == expect) if expect else True)
        db_q.append((doc, k, dt, expect, len(frames), nb, round(time.time() - t0, 2),
                     "ok" if ok else "short",
                     time.strftime("%Y-%m-%dT%H:%M:%S")))


async def run(a):
    ROOT.mkdir(parents=True, exist_ok=True)
    CP.ensure()
    db = ledger(CP.LEDGER)
    done = {r[0] for r in db.execute("SELECT doc_id FROM doc WHERE status='ok'")}
    bbls = list(a.parcel or [])
    if a.parcel_file:
        bbls += [ln.strip() for ln in pathlib.Path(a.parcel_file).read_text(
            encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    if bbls:
        docs = pick_parcel(bbls, a.docs, skip_done=not a.redo)
        print(f"  parcel walk: {len(bbls)} bbl(s) -> {len(docs)} documents, oldest first")
    else:
        docs = pick(a.docs, a.docs // 3 + 1, a.stride)
    docs = [d for d in docs if d[0] not in done]

    # cap applies BETWEEN documents
    # ⚠ A PARCEL PICK HAS expect=0 (the spec index has no page count), so summing
    # d[1] would never reach the cap and --max-pages would silently do nothing —
    # a limit that stops limiting is worse than no limit. Charge an estimate per
    # document instead, and say which rule is in force.
    EST = 12                      # median parcel document, from the inventory ledger
    est = bool(bbls)
    keep, tot = [], 0
    for d in docs:
        if tot >= a.max_pages:
            break
        keep.append(d); tot += (EST if est else d[1])
    if len(keep) < len(docs):
        print(f"  --max-pages {a.max_pages} stopped the queue at {len(keep)}/{len(docs)} "
              f"documents ({'estimated ' + str(EST) + ' pg/doc' if est else 'known page counts'})")
    docs = keep

    gate = Gate(a.start_interval, a.floor, a.ease)
    sem = asyncio.Semaphore(a.conc)
    stats = {"pages": 0, "bytes": 0, "lat": [],
             "cls": collections.defaultdict(lambda: [0, 0])}
    db_q = []
    print(f"  root: {ROOT.resolve()}")
    print(f"  {len(docs)} documents, {tot:,} pages, concurrency {a.conc}\n")

    t0 = time.time()
    conn = aiohttp.TCPConnector(limit=a.conc, limit_per_host=a.conc)
    to = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(
            connector=conn, timeout=to,
            headers={"User-Agent": UA,
                     "Accept": "image/tiff,image/*,*/*;q=0.8"}) as sess:
        res = await asyncio.gather(*[one_doc(sess, gate, sem, r, stats, db_q, a.pdf)
                                     for r in docs], return_exceptions=True)
    # ⚠ return_exceptions=True SWALLOWS FAILURES SILENTLY. First run recorded 50
    # of 200 documents and reported a clean finish - 150 tasks died invisibly.
    # An exception counted as "done" is the same lie as an empty output file
    # scored as zero.
    errs = collections.Counter(type(x).__name__ for x in res if isinstance(x, BaseException))
    if errs:
        print(f"  ⚠ {sum(errs.values())} document task(s) FAILED: {dict(errs)}")
        for x in res:
            if isinstance(x, BaseException):
                print(f"      {type(x).__name__}: {str(x)[:150]}"); break
    el = time.time() - t0

    db.executemany("INSERT OR REPLACE INTO doc VALUES(?,?,?,?,?,?,?,?,?)", db_q)
    db.commit()

    if gate.stopped:
        print(f"  ⚠ REFUSED - run stopped, nothing retried.\n  {gate.reason}\n")
    n = stats["pages"]
    if not n:
        print("  no pages"); return
    kb = stats["bytes"] / n / 1024
    rate = n / el
    lat = stats["lat"]
    print(f"  ── {n:,} pages · {el/60:.1f} min · conc {a.conc} ──")
    print(f"  latency   mean {sum(lat)/len(lat):.2f}s  max {max(lat):.2f}s")
    print(f"  RATE      {rate:.1f} pages/s   (delay settled {gate.iv:.3f}s)")
    print(f"  page size {kb:,.0f} KB")
    for k, (p, b) in sorted(stats["cls"].items()):
        print(f"    {k:<9}{p:>6} pg{b/p/1024:>7,.0f} KB")
    short = sum(1 for r in db_q if r[7] == "short")
    print(f"  short documents: {short}/{len(db_q)}")
    if stats.get("writeerr"):
        print(f"  ⚠ container write fell back to loose pages: {dict(stats['writeerr'])}")
    if stats.get("pageerr"):
        print(f"  page-level errors: {dict(stats['pageerr'])}")
    print(f"\n  PROJECTED 148,238,970 pages -> {148238970*kb*1024/1e12:,.1f} TB")
    print(f"    at {rate:.1f} p/s  {148238970/rate/86400:,.0f} days")
    print(f"  territory (7,030 lots x 12 docs x 9 pg = 759k pages): "
          f"{759000/rate/3600:,.1f} hours")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", type=int, default=200)
    ap.add_argument("--parcel", action="append",
                    help="BBL to acquire, oldest document first. Repeatable. "
                         "Overrides the strided sample in pick().")
    ap.add_argument("--parcel-file",
                    help="file of BBLs, one per line — the territory walk")
    ap.add_argument("--redo", action="store_true",
                    help="re-acquire documents already marked `acquired` in walk")
    ap.add_argument("--conc", type=int, default=8)
    ap.add_argument("--stride", type=int, default=53)
    ap.add_argument("--start-interval", type=float, default=0.10)
    ap.add_argument("--floor", type=float, default=0.0)
    ap.add_argument("--ease", type=float, default=0.90)
    ap.add_argument("--max-pages", type=int, default=1800)
    ap.add_argument("--pdf", action="store_true",
                    help="bundle a per-document PDF inline. ⚠ OFF BY DEFAULT: it "
                         "doubles storage (PDF is 0.98x the TIFFs, so keeping both "
                         "is ~2x) and it runs PIL decode+encode INSIDE the fetch "
                         "loop, competing with network I/O. The pipeline reads "
                         "pages, not PDFs - folder=doc_id, filename=page is a "
                         "stronger binding than a container. Build PDFs on demand.")
    asyncio.run(run(ap.parse_args()))


if __name__ == "__main__":
    main()
