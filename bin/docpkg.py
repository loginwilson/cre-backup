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


def native_bitmap(doc, page):
    """The page's own scan, when the page IS one scan and nothing else.

    >> page.get_pixmap(dpi=N) rasterises the PAGE BOX.  When the box's aspect
       ratio disagrees with the embedded bitmap's, content is silently squashed
       or stretched; when the box implies more pixels than the bitmap holds,
       the extra ones are manufactured.  Measured over the round-2 queue
       (54 pages): ACRIS and film are clean, EVERY Richmond page is wrong --

           RC_400026   +8.4% / +9.2% / -6.1%   direction changes mid-document
           RC_300106   -7.4% on all 9 pages, rendered at 150% of native:
                       a 1600px scan handed to the reader as 2400px

       A manufactured pixel is indistinguishable from a measured one.  That is
       this project's recurring defect -- something absent rendering identically
       to something verified -- arriving through the image pipeline instead of
       through a schema.  Extractor A found the symptom from the reading side
       (D-011: resolution is recorded and then never acted on, no floor) with no
       way to see the cause.

       So: when a page is exactly one full-page image, with no drawings, no text
       and no /Rotate, hand over THAT BITMAP -- native size, native aspect, no
       resample.  Anything else falls back to rasterising the box, which is the
       right answer for pages that really are compositions.
    """
    if page.rotation or page.get_drawings() or page.get_text().strip():
        return None
    imgs = page.get_images(full=True)
    if len(imgs) != 1:
        return None
    try:
        bbox = page.get_image_bbox(imgs[0])
    except Exception:
        return None
    r = page.rect
    if not r.width or not r.height:
        return None
    # the image must actually cover the page, or the box is carrying layout
    if not (abs(bbox.width - r.width) / r.width < 0.02
            and abs(bbox.height - r.height) / r.height < 0.02):
        return None
    info = doc.extract_image(imgs[0][0])
    if info.get("ext") != "png" or not info.get("image"):
        return None
    return info


def build(did: str, dpi: int) -> pathlib.Path:
    _, rd, pdf_value = row(did)
    src = resolve(did, pdf_value)

    out = DOCS / did
    out.mkdir(parents=True, exist_ok=True)

    reg = out / "registration.json"
    reg.write_text(json.dumps(json.loads(rd), indent=2), encoding="utf-8")

    doc = fitz.open(src)
    pages = []
    geometry = []
    for i, page in enumerate(doc, start=1):
        img = out / ("page-%02d.png" % i)
        info = native_bitmap(doc, page)
        if info:
            img.write_bytes(info["image"])
            w, h, how = info["width"], info["height"], "native"
        else:
            pm = page.get_pixmap(dpi=dpi)
            pm.save(img)
            w, h, how = pm.width, pm.height, "rasterised"
        pages.append(img)
        # >> a text layer would make this a different (easier) problem; record
        #    that there isn't one so nobody goes looking for it
        chars = len(page.get_text().strip())
        geometry.append({"page": i, "width": w, "height": h, "source": how})
        print("  page %2d  %6d x %-6d px  %-10s  %5d text chars"
              % (i, w, h, how, chars))
    doc.close()

    manifest = {
        "id": did,
        "source_pdf_relative": pdf_value,
        "dpi": dpi,
        "pages": len(pages),
        # >> recorded so a resample can never again be invisible downstream
        "geometry": geometry,
        "artifacts": {p.name: sha256(p) for p in [reg] + pages},
    }
    man = out / "MANIFEST.json"
    man.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("\npackage  %s" % out)
    print("pages    %d at %d dpi" % (len(pages), dpi))
    print("manifest %s" % sha256(man))
    return out


def zoom(did: str, page_no: int, dpi: int, rect: str | None,
         out: str | None = None) -> None:
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

    # >> Crops land in the CALLER's own folder, never in the shared package.
    #    They used to go to <loop>/docs/<id>/zoom/, which all five readers can
    #    read, and each filename IS the rect it was cut from -- so the directory
    #    listing alone told a later reader exactly which regions someone else had
    #    thought worth 900 dpi.  That is a pointer, and a pointer is contact.
    #    Blind has to include "blind about where the others looked."
    zdir = (pathlib.Path(out) if out else pathlib.Path.cwd()) / "zoom" / did
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
    ap.add_argument("--rect", help="x0,y0,x1,y1 as fractions of the page -- the "
                                   "same shape a v4 citation carries, so record "
                                   "the rect you zoomed to")
    ap.add_argument("--out", help="where crops go (default: ./zoom/<id>/). Keep "
                                  "this inside your own folder.")
    a = ap.parse_args()

    if a.page:
        zoom(a.id, a.page, a.dpi, a.rect, a.out)
    else:
        build(a.id, a.dpi)


if __name__ == "__main__":
    main()
