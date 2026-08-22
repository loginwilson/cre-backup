"""Drop-folder ingest — documents Login saves, decoded automatically.

THE DIVISION OF LABOUR THIS EXISTS FOR
    ACRIS is refusing automated access from this machine, and that is not going
    to be worked around. But a person opening a document in a browser is simply
    using a public records system as intended. So: Login saves documents into a
    folder; this module recognises them, stores them permanently, and hands them
    to the decoder.

    A median parcel is TWELVE documents (measured on 519 LIC lots), so a live
    parcel is minutes of clicking, not an afternoon.

WHAT IT REFUSES TO DO
    * guess a doc_id it cannot justify — a misfiled document silently attaches a
      1978 mortgage to the wrong parcel, and nothing downstream would catch it
    * accept a bandwidth notice as a document — a saved HTML refusal is a real
      hazard when the person saving was not watching
    * delete anything, ever

NAMING
    Best: name the file with the document id — `2021070601644010.pdf`, or
    `2021070601644010_p18.tif` for a single page. Anything containing a 16-digit
    ACRIS id or an `FT_`-prefixed id is recognised anywhere in the filename, so
    a browser's own "2021070601644010 (1).pdf" works untouched.

    Unrecognised files are NOT guessed at. They are listed as needing a name,
    which is a two-second fix and infinitely preferable to a wrong attribution.
"""
import hashlib, io, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import store

# 16-digit ACRIS ids, plus the FT_ microfilm-era form (6,092,729 documents,
# 35.8% of ACRIS — they will absolutely turn up in a parcel's saved history)
DOC_ID = re.compile(r"(FT_\d{10,16}|\d{16})")
PAGE = re.compile(r"[_\-\s]p(?:age)?[_\-\s]?(\d{1,3})\b", re.I)

IMAGE_MAGIC = ((b"%PDF", "application/pdf"), (b"II*\x00", "image/tiff"),
               (b"MM\x00*", "image/tiff"), (b"\x89PNG", "image/png"),
               (b"\xff\xd8\xff", "image/jpeg"))

REFUSAL_SIGNALS = ("further access to acris is denied", "acris bandwidth notice",
                   "automated scripts/robots", "exceeded the bandwidth limits")


def sniff(data):
    """(content_type, pages) from the BYTES. Never from the extension.

    A file named .pdf that is actually a saved HTML error page is exactly the
    kind of thing that gets stored as a document and decoded as an empty one.
    """
    for magic, ct in IMAGE_MAGIC:
        if data.startswith(magic):
            return ct, _pages(data, ct)
    head = data[:8000].decode("utf-8", "ignore").lower()
    if "<html" in head or "<!doctype html" in head:
        return "text/html", None
    return None, None


def _pages(data, ct):
    try:
        if ct == "application/pdf":
            import pypdf
            return len(pypdf.PdfReader(io.BytesIO(data)).pages)
        if ct == "image/tiff":
            from PIL import Image
            return getattr(Image.open(io.BytesIO(data)), "n_frames", 1)
    except Exception:
        return None
    return 1


def is_refusal(data):
    """A saved bandwidth notice masquerading as a document."""
    import html as _html
    t = data[:60000].decode("utf-8", "ignore")
    t = _html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"\s+", " ", t).lower()
    return any(s in t for s in REFUSAL_SIGNALS)


def classify(path):
    """What is this file, and can it be attributed to a document with confidence?"""
    p = pathlib.Path(path)
    data = p.read_bytes()
    ct, pages = sniff(data)
    m = DOC_ID.search(p.name) or DOC_ID.search(p.parent.name)
    pm = PAGE.search(p.name)
    rec = {"path": str(p), "bytes": len(data), "content_type": ct, "pages": pages,
           "doc_id": m.group(1) if m else None,
           "page": int(pm.group(1)) if pm else ("whole" if pages and pages > 1 else 1)}
    if ct is None or ct == "text/html":
        rec["verdict"] = "REFUSAL" if is_refusal(data) else "not-a-document"
    elif not rec["doc_id"]:
        rec["verdict"] = "needs-a-name"
    else:
        rec["verdict"] = "ok"
    return rec, data


def ingest(folder, dry_run=False):
    """Store every recognisable document. Reports FOUR outcomes, never one.

    Prints denominators throughout — a summary line without one is how this
    project has repeatedly convinced itself that a partial run was complete.
    """
    folder = pathlib.Path(folder)
    if not folder.exists():
        raise SystemExit(f"no such folder: {folder}")
    files = [f for f in sorted(folder.rglob("*")) if f.is_file()
             and f.name != "manifest.jsonl" and ".part" not in f.name]
    if not files:
        print(f"{folder} is empty — save ACRIS documents into it and re-run")
        return {}

    out = {"ok": [], "needs-a-name": [], "REFUSAL": [], "not-a-document": []}
    for f in files:
        try:
            rec, data = classify(f)
        except Exception as e:
            print(f"  ERROR reading {f.name}: {type(e).__name__} {e}")
            continue
        out[rec["verdict"]].append(rec)
        if rec["verdict"] == "ok" and not dry_run:
            r = store.put(rec["doc_id"], rec["page"], data, rec["content_type"],
                          source=f"dropped:{f.name}")
            rec["stored"] = r["sha256"][:12]
            rec["new"] = r["new_blob"]

    n = len(files)
    print(f"{n} file(s) in {folder}\n")
    for rec in out["ok"]:
        pg = f"p{rec['page']}" if rec["page"] != "whole" else f"whole ({rec['pages']}pp)"
        tag = "" if rec.get("new", True) else "  (already held)"
        print(f"  ok            {rec['doc_id']:<18} {pg:<16} "
              f"{rec['bytes']:>9,}b{tag}")
    for rec in out["needs-a-name"]:
        print(f"  needs-a-name  {pathlib.Path(rec['path']).name}  "
              f"({rec['content_type']}, {rec['bytes']:,}b) — rename it to include "
              f"the document id; NOT guessed at")
    for rec in out["REFUSAL"]:
        print(f"  ⚠ REFUSAL     {pathlib.Path(rec['path']).name} is a saved ACRIS "
              f"bandwidth notice, not a document")
    for rec in out["not-a-document"]:
        print(f"  skipped       {pathlib.Path(rec['path']).name} "
              f"({rec['content_type'] or 'unknown type'})")

    stored = len(out["ok"])
    print(f"\n  {stored}/{n} stored · {len(out['needs-a-name'])} need a name · "
          f"{len(out['REFUSAL'])} refusal page(s) · "
          f"{len(out['not-a-document'])} not documents")
    if stored:
        s = store.stats()
        print(f"  corpus now: {s['documents']:,} documents · {s['pages']:,} pages · "
              f"{s['bytes']/1024**2:,.1f} MB at {s['root']}")
        print(f"\n  next: python batch.py   (decodes what is held; every future "
              f"parser fix re-runs against it)")
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    folder = args[0] if args else pathlib.Path(__file__).with_name("dropbox")
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)
    ingest(folder, dry_run="--dry-run" in sys.argv)
