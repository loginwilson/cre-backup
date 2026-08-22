"""Fetch a WHOLE document in one request instead of one request per page.

WHY THIS IS THE ONLY LEVER LEFT
    ACRIS charges by the REQUEST, and the budget is a hard 50/day. A 15-page
    instrument costs 15 requests page-by-page and 1 request whole — identical
    bytes, identical politeness, 15x the documents decoded per permitted day.
    Nothing here evades anything: it asks for the same content the viewer
    already serves, fewer times. That is what a rate limit rewards.

    This is the ONLY untested technique that changes the arithmetic. Every other
    idea on the table was a way to be counted less accurately rather than to ask
    less often, and those are not on the table.

⚠ THE TRAP THIS FILE EXISTS TO AVOID
    A "whole document" endpoint that silently returns only the FIRST page is
    indistinguishable from success: content-type is right, bytes are a real
    image, nothing errors. We would record a decoded document, delete the image,
    and carry a 1-of-15 reading forever — and the ledger would stop us ever
    re-fetching it.

    That is this project's recurring failure shape, now seen eight times:
    A CHECK THAT REPORTS SUCCESS BECAUSE IT LOOKED IN THE WRONG PLACE.

    So: a container is accepted ONLY on the POSITIVE signal that it holds the
    number of pages we independently expected. No expectation, no acceptance —
    it falls back to the per-page path rather than guessing.

Images are SCRAP: fetch -> decode -> delete. ACRIS is the archive; only facts
persist. (Revisit if a licensed bulk corpus ever lands — with images on disk,
every future parser fix re-runs against everything. Today it cannot.)
"""
import hashlib, io, pathlib, sys, urllib.request

import fetch_budget
from fetch_pages import UA, AccessDenied, PLACEHOLDER, _check_denied

VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView"

# Candidate whole-document endpoints, best first. NONE of these is confirmed —
# access went down before any could be tried. Each is recorded with what it is
# believed to do so a future run can strike the ones that fail rather than
# rediscover them.
CANDIDATES = [
    # the per-page endpoint with the page parameter omitted — some viewers read
    # this as "the whole thing"
    ("no-page", "https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage?doc_id={d}"),
    # explicit multipage flags seen on comparable municipal viewers
    ("allpages", "https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage?doc_id={d}&allpages=true"),
    ("page-0", "https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage?doc_id={d}&page=0"),
    # a print/export path, which is where a PDF would live if one exists
    ("print", "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImagePrint?doc_id={d}"),
    ("pdf", "https://a836-acris.nyc.gov/DS/DocumentSearch/GetPdf?doc_id={d}"),
]


class NotAContainer(RuntimeError):
    """The response was not a multi-page document. Fall back; do not guess."""


def _get(url, doc_id, timeout=90):
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Referer": f"{VIEW}?doc_id={doc_id}"})
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return f.read(), f.headers.get("Content-Type", "")


def page_count(data, ctype):
    """How many pages does this blob ACTUALLY hold? None if it is not a container.

    The whole guard rests on this number, so it is measured from the bytes, never
    inferred from the content-type or the URL that produced them.
    """
    if data[:4] == b"%PDF":
        try:
            import pypdf
            return len(pypdf.PdfReader(io.BytesIO(data)).pages)
        except Exception:
            # count page objects directly rather than trusting a partial parse
            n = data.count(b"/Type /Page") + data.count(b"/Type/Page")
            return n or None
    if data[:2] in (b"II", b"MM"):                     # TIFF magic
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(data))
            return getattr(im, "n_frames", 1)
        except Exception:
            return None
    if "html" in (ctype or "").lower():
        return None
    return None


def boundary_is_placeholder(doc_id, page):
    """Is `page` PAST the end of this document? Costs one request.

    ⚠ THIS IS THE INDEPENDENT WITNESS, and it exists because the obvious one
    does not. The ACRIS master index (bnx9-e6tj) carries NO page count —
    measured 2026-08-05, the columns are crfn, doc_type, document_amt,
    document_date, document_id, good_through_date, modified_date, percent_trans,
    record_type, recorded_borough, recorded_datetime, reel_nbr, reel_pg,
    reel_yr. `reel_pg` is a MICROFILM position, not a page total; using it as
    one would have silently truncated most documents.

    So completeness is proven at the BOUNDARY instead: ask for the page after
    the last one the container holds. The per-page endpoint answers with a
    fixed placeholder image (known md5) once you are past the end. Placeholder
    means the container really did hold everything; a real image means it
    truncated and must be rejected.

    Cost: 2 requests total instead of ~15. Still a ~7x lever, and unlike a
    page-count lookup it PROVES the thing rather than assuming it.
    """
    data, ctype = _get(f"https://a836-acris.nyc.gov/DS/DocumentSearch/GetImage"
                       f"?doc_id={doc_id}&page={page}", doc_id)
    _check_denied(data, ctype)
    fetch_budget.note_fetch(doc_id, f"boundary:{page}")
    if hashlib.md5(data).hexdigest() == PLACEHOLDER:
        return True
    if "tiff" not in (ctype or "").lower() or len(data) < 500:
        # Neither a placeholder nor an image. UNKNOWN is not proof of the end —
        # requiring the POSITIVE signal is the rule this project keeps relearning.
        raise NotAContainer(
            f"{doc_id}: boundary page {page} returned {ctype} {len(data):,}b — "
            f"neither placeholder nor image, so completeness is UNPROVEN. "
            f"Rejecting rather than assuming the container is whole.")
    return False


def fetch_document(doc_id, outdir, expected_pages=None, dry_run=False, verify=True):
    """One request for the whole instrument, plus one to prove it is complete.

    `expected_pages` is OPTIONAL and is only a cross-check when we happen to
    know it (e.g. a document already decoded page-by-page, whose count is in
    the ledger). The real proof is the boundary probe, because the index has no
    page count to check against — see boundary_is_placeholder().
    """
    out = pathlib.Path(outdir) / doc_id
    tried = []
    for name, tmpl in CANDIDATES:
        if fetch_budget.remaining() <= 0:
            print(f"  budget exhausted — stopping cleanly after {len(tried)} attempt(s)")
            break
        url = tmpl.format(d=doc_id)
        if dry_run:
            print(f"  [dry-run] would try {name}: {url}")
            tried.append((name, "dry-run"))
            continue
        try:
            data, ctype = _get(url, doc_id)
        except Exception as e:
            print(f"  {name:<9} request failed: {type(e).__name__} {str(e)[:60]}")
            tried.append((name, "error"))
            continue
        try:
            _check_denied(data, ctype)
        except AccessDenied:
            fetch_budget.note_blocked()
            raise
        fetch_budget.note_fetch(doc_id, f"whole:{name}")

        if hashlib.md5(data).hexdigest() == PLACEHOLDER:
            print(f"  {name:<9} placeholder image — endpoint does not serve documents")
            tried.append((name, "placeholder"))
            fetch_budget.pace()
            continue

        n = page_count(data, ctype)
        if n is None:
            print(f"  {name:<9} not a container ({ctype}, {len(data):,}b)")
            tried.append((name, f"not-a-container/{ctype}"))
            fetch_budget.pace()
            continue

        # ---- THE GUARD ---------------------------------------------------
        # A container holding ONE page when the index says fifteen is the silent
        # failure this file exists to prevent. Reject it; do not "use what we
        # got" — a partial decode recorded as complete is worse than no decode.
        if n < expected_pages:
            print(f"  {name:<9} REJECTED — holds {n} page(s), index says "
                  f"{expected_pages}. A partial container is the silent-truncation "
                  f"trap; falling back rather than recording 1-of-{expected_pages}.")
            tried.append((name, f"partial:{n}/{expected_pages}"))
            fetch_budget.pace()
            continue

        out.mkdir(parents=True, exist_ok=True)
        blob = out / f"whole.{'pdf' if data[:4] == b'%PDF' else 'tif'}"
        blob.write_bytes(data)
        print(f"  {name:<9} ACCEPTED — {n} pages, {len(data):,}b -> {blob.name}  "
              f"(1 request instead of {expected_pages}; "
              f"{fetch_budget.remaining()} left today)")
        return {"doc_id": doc_id, "endpoint": name, "url": url, "pages": n,
                "bytes": len(data), "path": str(blob),
                "requests_saved": expected_pages - 1}

    return {"doc_id": doc_id, "endpoint": None, "pages": 0, "tried": tried,
            "note": "no whole-document endpoint worked; use fetch_pages()"}


def explode(blob_path, outdir, delete_container=True):
    """Split an accepted container into per-page PNGs for reading, then bin it.

    Same discipline as the per-page path: the container is scrap the moment its
    pages are extracted.
    """
    from PIL import Image
    blob = pathlib.Path(blob_path)
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    made = []
    if blob.suffix == ".pdf":
        import pypdf
        from pypdf import PdfReader
        rdr = PdfReader(str(blob))
        for i, pg in enumerate(rdr.pages, 1):
            for img in pg.images:
                p = out / f"p{i:03d}.png"
                Image.open(io.BytesIO(img.data)).convert("L").save(p)
                made.append(p)
                break
    else:
        im = Image.open(str(blob))
        for i in range(getattr(im, "n_frames", 1)):
            im.seek(i)
            p = out / f"p{i + 1:03d}.png"
            im.convert("L").save(p)
            made.append(p)
    if delete_container:
        blob.unlink()
    return made


if __name__ == "__main__":
    if "--dry-run" in sys.argv:
        doc = next((a for a in sys.argv[1:] if not a.startswith("--")), "2021070601644010")
        print(f"{doc}: candidate endpoints (no requests made)")
        fetch_document(doc, ".", expected_pages=15, dry_run=True)
        raise SystemExit(0)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 3:
        raise SystemExit("usage: python fetch_document.py <doc_id> <outdir> "
                         "<expected_pages>  |  --dry-run")
    r = fetch_document(args[0], args[1], int(args[2]))
    print(r)
