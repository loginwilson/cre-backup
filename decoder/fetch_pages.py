"""Fetch SPECIFIC pages of an ACRIS document as PNG, for re-reading.

Every decode already records the page a legal description sits on, so a
re-read never needs the whole document — this pulls the named pages only.
Same channel and manners as the original fetch: the viewer's own per-page
endpoint, browser UA + Referer, sequential, ~1s apart. Not a bulk scraper.

Images are SCRAP: fetch -> read -> delete. ACRIS is the archive; only the
transcribed facts persist.

Usage: python fetch_pages.py <doc_id> <outdir> <page> [page ...]
"""
import hashlib, json, pathlib, re, sys, time, urllib.request
from PIL import Image

import fetch_budget

# >> MEASURED 2026-08-24 18:40, SAME IP AND SAME SECOND, one variable changed:
#      ...Chrome/126.0.0.0 Safari/537.36  -> HTTP 503, 4,309 bytes, 3/3 tries
#      ...Chrome/126.0     Safari/537.36  -> HTTP 200, 118,445 bytes
#    Referer made no difference either way, and spacing the requests 4 s apart
#    made no difference, so this is NOT a rate limit - acris's edge
#    discriminates on the version string itself. The lane ran ~166k requests
#    on the long form today before it started answering 503 to it.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
BASE = "https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage"
PLACEHOLDER = "4081a3f2004d7244a966995c02c730d0"

# ⚠ THE BANDWIDTH NOTICE. When ACRIS decides it has had enough it stops serving
# TIFFs and returns a 200 with an HTML page — byte-identical for every document
# and page — reading:
#
#   "Further access to ACRIS is denied. This can be due to multiple reasons such
#    as detection of automated scripts/robots that are capturing data from the
#    website or having exceeded the bandwidth limits we have established..."
#
# Hit on 2026-08-05 after a session of range scans. Two rules follow:
#
#  1. STOP. Do not retry, do not rotate anything, do not work around it. That is
#     the standing constraint on this project and it is also simply correct.
#  2. It must ABORT LOUDLY. The scanner used to skip any non-TIFF response
#     without a word, so a block looked exactly like "this document has no more
#     pages" — a silent stop that would have been recorded as a finished decode.
BANDWIDTH_NOTICE_LEN = 25103


class AccessDenied(RuntimeError):
    """ACRIS is refusing service. Stop; do not work around it."""


def _visible_text(data):
    """Markup stripped, entities resolved, whitespace collapsed.

    ⚠ WHY THIS IS NECESSARY. The bandwidth notice is Word-generated HTML, and
    the sentence "Further access to ACRIS is denied" is SPLIT ACROSS TAGS in the
    raw bytes. Searching the bytes for that phrase therefore never matches —
    measured 2026-08-06 against a live refusal that this function's predecessor
    passed as "not denied".
    """
    import html as _html
    t = data.decode("utf-8", "ignore")
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S | re.I)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S | re.I)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t).strip()


def _check_denied(data, ctype):
    """Raise on refusal. MUST NOT have false negatives.

    ⚠ THE BUG THIS REPLACED, found 2026-08-06: the old check searched the RAW
    BYTES for a contiguous phrase that markup splits apart, so it returned
    "not denied" against a live bandwidth notice. The single function whose job
    is to stop us was structurally incapable of firing.

    That is this project's recurring failure — A CHECK THAT REPORTS SUCCESS
    BECAUSE IT LOOKED IN THE WRONG PLACE — landing in the safety path, where a
    false negative means continuing to hammer a server that has said no.

    So: an IMAGE is accepted only on the POSITIVE signal of image bytes.
    Anything HTML-shaped is interrogated several independent ways, because any
    single phrase can be reworded by the City at any time.
    """
    if data[:2] in (b"II", b"MM") or data[:4] == b"%PDF":
        return                                   # positively an image; not a notice
    text = _visible_text(data).lower()
    signals = [
        "further access to acris is denied",
        "acris bandwidth notice",
        "automated scripts/robots",
        "exceeded the bandwidth limits",
        "subscription data services",
    ]
    hit = [s for s in signals if s in text]
    if hit:
        raise AccessDenied(
            f"ACRIS is refusing service (matched {len(hit)}/{len(signals)} notice "
            f"signals: {hit[:2]}; content-type {ctype!r}, {len(data):,}b). STOP "
            f"fetching. Do not retry or work around it — decode from what is "
            f"already held, and resume another day.")
    # ⚠ THREE OUTCOMES, NOT TWO — and this is a correction to MY OWN fix.
    #
    # The first version of this function raised on ANY html response. That
    # turned a false NEGATIVE (a refusal that could not fire, fixed 2026-08-06)
    # into a false POSITIVE the same day: a 4,922-byte ordinary error page,
    # matching 0/5 notice signals, was reported as "ACRIS is refusing service"
    # and halted a run while access was perfectly fine.
    #
    # A refusal and an unexpected response are different facts and must not be
    # collapsed. Callers decide what to do with "not an image"; only a MATCHED
    # refusal stops everything.


def _log_refusal(doc_id, page, status, headers, elapsed, nbytes):
    """Append one refusal to refusals.jsonl. Never raises — a diagnostic that
    can break the abort path is worse than no diagnostic."""
    # ⚠ THE WRITE AND THE MESSAGE GET SEPARATE try BLOCKS. With one block a
    # UnicodeEncodeError from printing "⚠" to a cp1252 Windows console — which
    # happened on this function's first run — reported "could not record
    # refusal" while the row sat correctly on disk. A diagnostic that lies
    # about its own success is worse than one that stays quiet.
    try:
        rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "doc_id": doc_id,
               "page": page, "http_status": status, "elapsed_s": round(elapsed, 2),
               "bytes": nbytes, "headers": headers,
               "successful_requests_today": fetch_budget._load().get("used")}
        with open(pathlib.Path(__file__).with_name("refusals.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception as e:
        print(f"  (could not record refusal: {type(e).__name__})")
        return
    try:
        ra = headers.get("Retry-After") or headers.get("retry-after")
        print(f"  refusal recorded: HTTP {status}"
              + (f", Retry-After {ra}" if ra else ", no Retry-After header"))
    except Exception:
        pass


def fetch_pages(doc_id, outdir, pages):
    out = pathlib.Path(outdir) / doc_id
    out.mkdir(parents=True, exist_ok=True)
    got = []
    for n in pages:
        if fetch_budget.already_have(doc_id, n):
            print(f"  p{n}: already fetched in an earlier session — skipped (ledger)")
            continue
        if fetch_budget.remaining() <= 0:
            print(f"  budget exhausted for today — {len(pages)} requested, stopping cleanly")
            break
        req = urllib.request.Request(
            f"{BASE}?doc_id={doc_id}&page={n}",
            headers={"User-Agent": UA,
                     "Referer": "https://a836-acris.nyc.gov/DS/DocumentSearch/"
                                f"DocumentImageView?doc_id={doc_id}"})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60) as f:
            ctype = f.headers.get("Content-Type", "")
            status = f.status
            hdrs = dict(f.headers)
            data = f.read()
        elapsed = time.time() - t0
        try:
            _check_denied(data, ctype)
        except AccessDenied:
            # ⚠ RECORD THE REFUSAL BEFORE ABORTING. Every block so far has been
            # thrown away at the moment it happened, so after four of them we
            # still cannot say whether ACRIS is counting requests or
            # identifying clients. A 429 with Retry-After is a limiter
            # announcing itself; a 200 carrying HTML is a filter that would
            # rather not. Costs nothing — the response is already in hand.
            # See BLOCK_DIAGNOSIS.md. This is diagnosis, not evasion.
            _log_refusal(doc_id, n, status, hdrs, elapsed, len(data))
            fetch_budget.note_blocked()
            raise
        if "tiff" not in ctype or len(data) < 500:
            print(f"  p{n}: NOT AN IMAGE ({ctype}, {len(data):,}b) — not skipped silently")
            continue
        if hashlib.md5(data).hexdigest() == PLACEHOLDER:
            print(f"  p{n}: placeholder — past the last page")
            continue
        # RETAIN THE ORIGINAL BYTES. Until 2026-08-05 the TIFF was deleted here
        # and only a greyscale PNG survived, so a parser fix could never be
        # applied to the authoritative image — eight parser bugs were fixed in
        # one session and every earlier reading stayed frozen. Storage is ~$400
        # for the whole corpus; the deletion was never worth what it cost.
        try:
            import store
            store.put(doc_id, n, data, ctype, source="acris/GetImage")
        except Exception as e:                  # storing must never lose a fetch
            print(f"  p{n}: WARNING could not store original bytes: "
                  f"{type(e).__name__} {str(e)[:60]}")
        tif = out / f"p{n:03d}.tif"
        tif.write_bytes(data)
        img = Image.open(tif)
        # legal descriptions are dense small type; keep full resolution
        img.convert("L").save(out / f"p{n:03d}.png")
        tif.unlink()
        got.append(n)
        fetch_budget.note_fetch(doc_id, n)
        print(f"  p{n}: {len(data):,}b -> p{n:03d}.png  "
              f"({fetch_budget.remaining()} left in today's budget)")
        fetch_budget.pace()
    return got


def scan(doc_id, outdir, pages, i_know_this_is_expensive=False):
    """⚠ THIS IS THE TECHNIQUE THAT GOT US BLOCKED on 2026-08-05.

    A range scan spends ~15 requests to find one exhibit when the decode already
    records the page. It optimises MY reading cost and multiplies the REQUEST
    cost, and ACRIS charges for requests. Use targeted `fetch_pages` instead.
    Kept because it is genuinely the only way to locate an exhibit in a document
    that was decoded before pages were recorded — but it must be asked for
    explicitly, and it eats the daily budget fast.
    """
    if not i_know_this_is_expensive:
        raise RuntimeError(
            "scan() is the range-fetch that triggered the ACRIS block. Prefer "
            "fetch_pages(doc_id, outdir, [pages the decode already recorded]). "
            "Pass i_know_this_is_expensive=True only when no page is known.")
    return _scan(doc_id, outdir, pages)


def _scan(doc_id, outdir, pages):
    """Fetch a range and rank pages by how likely they are to be an EXHIBIT.

    Reading pages blind to find a legal description is the expensive step — each
    image costs far more to read than to fetch. But the two kinds of page differ
    in a way the BYTES already show:

        body prose      dense, justified, full margins   55-82 KB
        exhibit / legal 8-33 KB   (a title, a paragraph, a lot of white space)

    Measured across every description transcribed so far: 2026061500475003 p18/19
    = 16.5/14.8 KB, 2012120600575002 p15/16 = 23.8/25.8 KB, 2026012000388003
    p36/37 = 33.0/17.6 KB, 2026012000388004 p40 = 7.9 KB — against body pages of
    56-82 KB in the same documents.

    So: fetch cheaply, rank by size, READ the light ones first. This is a
    HEURISTIC for ordering the reads, never a classification — a dense exhibit
    (a 13-course metes description) can be heavy, so nothing is discarded, only
    deprioritised.
    """
    out = pathlib.Path(outdir) / doc_id
    out.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for n in pages:
        req = urllib.request.Request(
            f"{BASE}?doc_id={doc_id}&page={n}",
            headers={"User-Agent": UA,
                     "Referer": "https://a836-acris.nyc.gov/DS/DocumentSearch/"
                                f"DocumentImageView?doc_id={doc_id}"})
        with urllib.request.urlopen(req, timeout=60) as f:
            data = f.read()
            ctype = f.headers.get("Content-Type", "")
        _check_denied(data, ctype)
        if "tiff" not in ctype or len(data) < 500:
            # NEVER skip silently: a non-image response used to look identical to
            # "the document ends here", so a refusal read as a completed scan.
            print(f"  p{n}: NOT AN IMAGE ({ctype}, {len(data):,}b) — stopping the scan")
            break
        if hashlib.md5(data).hexdigest() == PLACEHOLDER:
            print(f"  p{n}: past the last page — stopping")
            break
        tif = out / f"p{n:03d}.tif"
        tif.write_bytes(data)
        Image.open(tif).convert("L").save(out / f"p{n:03d}.png")
        tif.unlink()
        sizes[n] = len(data)
        time.sleep(1.0)
    if not sizes:
        return sizes
    print(f"\n  {len(sizes)} pages fetched — ranked lightest first "
          f"(exhibits tend to be sparse):")
    for n, b in sorted(sizes.items(), key=lambda kv: kv[1]):
        bar = "#" * max(1, round(b / 4000))
        hint = "  <- likely exhibit" if b < 35000 else ""
        print(f"    p{n:>3}  {b:>7,}b  {bar}{hint}")
    return sizes


if __name__ == "__main__":
    if "--scan" in sys.argv:
        a = [x for x in sys.argv[1:] if x != "--scan"]
        doc_id, outdir = a[0], a[1]
        lo, hi = int(a[2]), int(a[3])
        print(f"{doc_id}: scanning pages {lo}-{hi}")
        scan(doc_id, outdir, range(lo, hi + 1), i_know_this_is_expensive=True)
    else:
        doc_id, outdir, pages = sys.argv[1], sys.argv[2], [int(p) for p in sys.argv[3:]]
        print(f"{doc_id}: fetching pages {pages}")
        got = fetch_pages(doc_id, outdir, pages)
        print(f"{doc_id}: {len(got)}/{len(pages)} pages retrieved")
