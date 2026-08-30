"""docpkg.py — build the document package for one id.

The extraction loop's two agents must read BYTE-IDENTICAL inputs. If A reads a
300 dpi render and B reads a 150 dpi render, every difference between their
tables is contaminated: you cannot tell a framework gap from a resolution
artefact, and the round teaches you nothing.  So the package is built ONCE,
here, by the orchestrator, and both agents are handed the same files.

    python docpkg.py <id>                    build the package
    python docpkg.py <id> --dpi 400          rebuild at another resolution
    python docpkg.py <id> --page 2 --dpi 900 re-render one page, large
    python docpkg.py <id> --page 2 --dpi 900 --rect 0.1,0.6,0.9,0.8
                                             re-render a REGION of one page,
                                             fractions of page width/height,
                                             for a stamp / marginal note /
                                             handwritten date you cannot read

Writes to  <loop>/docs/<id>/
    registration.json   the recorded_details blob, pretty-printed
    page-01.png ...     one image per page at DPI
    MANIFEST.json       sha256 of every artefact + how it was produced

Zoom renders land in <loop>/docs/<id>/zoom/ and are NOT part of the manifest —
they are a reading aid, not a new input.  The citable page images are the
numbered ones.

Read side follows DOCUMENT ACCESS.md exactly: stored path, never re-derived;
read-only with busy_timeout; a state is not a filename; a recorded path with no
file is an integrity problem, not a miss.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sqlite3
import sys

DECODER = pathlib.Path(r"C:\Users\smile\Downloads"
                       r"\Source Folder (Real Estate Data)"
                       r"\Decoder Prompt\decoder")
sys.path.insert(0, str(DECODER))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                     # noqa: E402
import fitz                                                   # noqa: E402

LOOP = pathlib.Path(__file__).resolve().parent.parent
DOCS = LOOP / "docs"
DEFAULT_DPI = 300


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def row(did: str):
    c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
    c.execute("PRAGMA busy_timeout=30000")
    r = c.execute(
        "SELECT id, recorded_details, pdf FROM navigation WHERE id = ?",
        (did,)).fetchone()
    c.close()
    if r is None:
        sys.exit("no such id in navigation: %s" % did)
    return r


def resolve(did: str, pdf_value: str) -> pathlib.Path:
    # >> never hand-join, never re-derive; doc_store_dir() is the WRITER's
    path = CP.doc_path(pdf_value)
    if path is None:
        sys.exit("id %s has no image — navigation.pdf is the state %r, not a "
                 "file. Pick another id." % (did, pdf_value))
    if not path.exists():
        sys.exit("INTEGRITY PROBLEM — db and store disagree.\n"
                 "  id   %s\n  path %s\n"
                 "Report this with the id. Do not treat it as 'no image'."
                 % (did, path))
    return path


def build(did: str, dpi: int) -> pathlib.Path:
    _, rd, pdf_value = row(did)
    src = resolve(did, pdf_value)

    out = DOCS / did
    out.mkdir(parents=True, exist_ok=True)

    reg = out / "registration.json"
    reg.write_text(json.dumps(json.loads(rd), indent=2), encoding="utf-8")

    doc = fitz.open(src)
    pages = []
    for i, page in enumerate(doc, start=1):
        img = out / ("page-%02d.png" % i)
        page.get_pixmap(dpi=dpi).save(img)
        pages.append(img)
        # >> a text layer would make this a different (easier) problem; record
        #    that there isn't one so nobody goes looking for it
        chars = len(page.get_text().strip())
        print("  page %2d  %6d px wide  %5d text chars"
              % (i, page.get_pixmap(dpi=dpi).width, chars))
    doc.close()

    manifest = {
        "id": did,
        "source_pdf_relative": pdf_value,
        "dpi": dpi,
        "pages": len(pages),
        "artifacts": {p.name: sha256(p) for p in [reg] + pages},
    }
    man = out / "MANIFEST.json"
    man.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("\npackage  %s" % out)
    print("pages    %d at %d dpi" % (len(pages), dpi))
    print("manifest %s" % sha256(man))
    return out


def zoom(did: str, page_no: int, dpi: int, rect: str | None) -> None:
    _, _, pdf_value = row(did)
    src = resolve(did, pdf_value)
    doc = fitz.open(src)
    page = doc[page_no - 1]

    clip = None
    tag = "p%02d-%ddpi" % (page_no, dpi)
    if rect:
        x0, y0, x1, y1 = (float(v) for v in rect.split(","))
        r = page.rect
        clip = fitz.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height,
                         r.x0 + x1 * r.width, r.y0 + y1 * r.height)
        tag += "-%s" % rect.replace(",", "_")

    zdir = DOCS / did / "zoom"
    zdir.mkdir(parents=True, exist_ok=True)
    img = zdir / ("%s.png" % tag)
    page.get_pixmap(dpi=dpi, clip=clip).save(img)
    doc.close()
    print(img)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--dpi", type=int, default=DEFAULT_DPI)
    ap.add_argument("--page", type=int)
    ap.add_argument("--rect", help="x0,y0,x1,y1 as fractions of the page")
    a = ap.parse_args()

    if a.page:
        zoom(a.id, a.page, a.dpi, a.rect)
    else:
        build(a.id, a.dpi)


if __name__ == "__main__":
    main()
