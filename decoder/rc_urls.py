"""EVERY RICHMOND DOCUMENT AS A ROW WITH ITS URLS — the complete access map.

    ACRIS_CORPUS_ROOT=D:/acris python rc_urls.py                 all 2,426,404
    ACRIS_CORPUS_ROOT=D:/acris python rc_urls.py --bbl 5000150012
    ACRIS_CORPUS_ROOT=D:/acris python rc_urls.py --type DEED --type MORTGAGE

Nothing here is fetched. Every column is derived from what the specification
already holds - the internal_id IS the access key, so the URLs are a rendering of
the index, not a retrieval of anything.

⚠ THE IMAGE URL MINTS A FRESH TOKEN ON EACH REQUEST. What is written here is the
MINTING url (p_endorsementId=...), never a resolved token URL - a resolved one
carries a timestamp and signature and is stale within minutes. This file does not
go out of date.

⚠ ONE ROW PER DOCUMENT, NOT PER PARCEL-LINK. A document touching several lots
appears once; its lots are in the bbls column, semicolon separated. Emitting one
row per link would inflate 2,426,404 documents to 2,891,086 rows and quietly
double-count anything measured off this file.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP

B = "https://www.richmondcountyclerk.com"
# FIXED 2026-08-19: was D:/acris (deleted in the restructure). Navigation is a
# PHASE with its own output folder; this file is its table.
OUT_DIR = CP.NAV


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbl", action="append")
    ap.add_argument("--type", action="append")
    ap.add_argument("--out")
    a = ap.parse_args()

    con = sqlite3.connect("file:" + str(CP.SPEC_DB).replace("\\", "/") + "?mode=ro",
                          uri=True, timeout=900)
    where = ["substr(d.document_id,1,3)='RC_'"]
    params = []
    if a.bbl:
        where.append("d.document_id IN (SELECT document_id FROM parcel_document"
                     " WHERE bbl IN (%s))" % ",".join("?" * len(a.bbl)))
        params += a.bbl
    if a.type:
        where.append("UPPER(d.doc_type) IN (%s)" % ",".join("?" * len(a.type)))
        params += [t.upper() for t in a.type]

    sql = ("SELECT d.document_id, d.doc_type, d.recorded_date, d.image_state,"
           " b.instrument, b.book, b.page"
           " FROM document d LEFT JOIN rc_binding b ON b.document_id=d.document_id"
           " WHERE " + " AND ".join(where) + " ORDER BY d.recorded_date DESC")

    name = a.out or ("rc_urls_%s.csv" % ("_".join(a.bbl) if a.bbl else
                                         "_".join(a.type).lower() if a.type else "ALL"))
    out = pathlib.Path(name) if a.out else OUT_DIR / name
    out.parent.mkdir(parents=True, exist_ok=True)

    # lots for the documents we emit - one pass, kept as a dict of id -> "b;b;b"
    print("  loading parcel links...", flush=True)
    lots = {}
    for did, bbl in con.execute(
            "SELECT document_id, bbl FROM parcel_document"
            " WHERE substr(document_id,1,3)='RC_'"):
        lots.setdefault(did, []).append(bbl)
    print(f"    {len(lots):,} documents carry parcel links", flush=True)

    t0 = time.time()
    n = 0
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["document_id", "internal_id", "instrument", "doc_type",
                    "recorded", "book", "page", "image_state", "bbls",
                    "image_url", "detail_url", "store_at"])
        for did, dtype, rec, img, instr, book, page in con.execute(sql, params):
            iid = did[3:]
            w.writerow([
                did, iid, instr or "", dtype or "", rec or "", book or "",
                page or "", img or "", ";".join(lots.get(did, [])),
                f"{B}/ViewVscmsDocument/ViewContent?p_endorsementId={iid}",
                f"{B}/Search/viewDocumentInfo/{iid}",
                # store_at names the ARCHIVED artifact, not the download. The
                # viewer serves PDF; the settled archive format is bitonal CCITT
                # G4 TIFF (16.7x, 20.3 TB -> 1.2 TB, signed off 2026-08-19). An
                # agent that followed a .pdf here would store the uncompressed
                # original and miss the whole point of the compression step.
                str(pathlib.Path(CP.STORE) / f"{did}.tif"),
            ])
            n += 1
            if n % 250000 == 0:
                print(f"    {n:,} rows · {time.time()-t0:.0f}s", flush=True)
    print(f"\n  {n:,} documents -> {out}")
    print(f"  {out.stat().st_size/1e6:.0f} MB · {(time.time()-t0)/60:.1f} min")
    con.close()


if __name__ == "__main__":
    main()
