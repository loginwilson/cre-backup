"""THE FRAME - phase 0 of the three-phase keying program (login 2026-08-20):
all 24,039,303 doc ids, each with its two URLs pre-populated, every other
column ready to fill. Pure id-formulas + the banked rc_binding pairing, so
this builds offline in minutes and IS the substrate the RD pass fills.

    id | recorded_details | rd_url | pdf | pdf_url | keyed_by | key
"""
import csv
import pathlib
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP

AC = "https://a836-acris.nyc.gov/DS/DocumentSearch"
RC = "https://www.richmondcountyclerk.com"
OUT = CP.NAV_TABLE
if OUT.exists():
    sys.exit(f"{OUT.name} already exists - the frame seeds the table ONCE; "
             f"landing passes update it. Delete/rename it first if a reseed "
             f"is truly intended (this guard stops a reseed from silently "
             f"discarding every landed recorded_details).")

con = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True)
t0 = n = 0
t0 = time.time()
with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "recorded_details", "rd_url", "pdf", "pdf_url",
                "keyed_by", "key"])
    for did, instr in con.execute(
            "SELECT d.document_id, b.instrument FROM document d"
            " LEFT JOIN rc_binding b ON b.document_id = d.document_id"
            " ORDER BY d.document_id"):
        if did.startswith("RC_"):
            internal = did[3:]
            # rd door: the doc-id input URL (cold-valid; the click POSTs the
            # one-shot grant). No instrument banked -> the internal-id form.
            rd = (RC + "/search/ShowResultsDocumentNumberSearch/0"
                  f"?DocumentNumber={instr}&SelectedDocumentIdentifier=0"
                  if instr else RC + f"/Search/viewDocumentInfo/{internal}")
            pdf = RC + f"/ViewVscmsDocument/ViewContent?p_endorsementId={internal}"
        else:
            rd = AC + f"/DocumentDetail?doc_id={did}"
            pdf = AC + f"/DocumentImageView?doc_id={did}"
        w.writerow([did, "", rd, "", pdf, "", ""])
        n += 1
        if n % 4_000_000 == 0:
            print(f"  {n:,} · {n/(time.time()-t0):,.0f} rows/s", flush=True)

print(f"\nframe: {n:,} rows -> {OUT}")
print(f"  {OUT.stat().st_size/1e6:,.0f} MB · {(time.time()-t0)/60:.1f} min")
assert n == 24_039_303, f"frame count {n:,} != the sealed universe"
print("  count = the sealed universe: 24,039,303  [OK]")
