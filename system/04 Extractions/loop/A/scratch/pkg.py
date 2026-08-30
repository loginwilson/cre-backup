"""pkg.py — docpkg, but into A's private scratch instead of the shared loop/docs.

Same module, same fitz, same default dpi, so renders are byte-identical to what
docpkg would produce.  Only the output root moves.  Reason: loop/docs is the
SHARED package directory; building my survey packages there would publish to B
the list of ids I chose to look at, which is a one-way isolation leak during a
blind phase.  Surveyed ids go in surveyed.md at reveal, not into a directory B
can list right now.

    python pkg.py <id> [<id> ...]
    python pkg.py <id> --page 3 --dpi 900 [--rect x0,y0,x1,y1]
"""
from __future__ import annotations

import argparse
import pathlib
import sys

BIN = pathlib.Path(r"D:\CRE Decoding System\04 Extractions\loop\bin")
sys.path.insert(0, str(BIN))

import docpkg                                                  # noqa: E402

docpkg.DOCS = pathlib.Path(__file__).resolve().parent / "docs"
docpkg.DOCS.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="+")
    ap.add_argument("--dpi", type=int, default=docpkg.DEFAULT_DPI)
    ap.add_argument("--page", type=int)
    ap.add_argument("--rect")
    a = ap.parse_args()

    for did in a.ids:
        print("=== %s" % did)
        try:
            if a.page:
                docpkg.zoom(did, a.page, a.dpi, a.rect)
            else:
                docpkg.build(did, a.dpi)
        except SystemExit as e:
            print("  SKIP: %s" % e)


if __name__ == "__main__":
    main()
