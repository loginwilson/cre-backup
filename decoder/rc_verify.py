"""VERIFY THE RICHMOND LANDING — counts, and that a parcel actually reads.

    ACRIS_CORPUS_ROOT=D:/acris python rc_verify.py

⚠ A COUNT IS NOT A READ. Every failure in this project looked correct by its own
total; the test that matters is walking a real parcel to real documents.
"""
from __future__ import annotations

import sqlite3
import sys
import pathlib

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP

c = sqlite3.connect("file:" + str(CP.SPEC_DB).replace("\\", "/") + "?mode=ro",
                    uri=True, timeout=300)
q = c.execute

tot = q("SELECT COUNT(*) FROM document").fetchone()[0]
rc = q("SELECT COUNT(*) FROM document WHERE substr(document_id,1,3)='RC_'").fetchone()[0]
print("  CORPUS")
print(f"    documents total          {tot:>12,}")
print(f"      Richmond (RC_)         {rc:>12,}")
print(f"      ACRIS                  {tot-rc:>12,}")
print(f"      rc_binding rows        {q('SELECT COUNT(*) FROM rc_binding').fetchone()[0]:>12,}")

print("\n  PARCEL LINKS BY BOROUGH")
for b, name in (("1", "Manhattan"), ("2", "Bronx"), ("3", "Brooklyn"),
                ("4", "Queens"), ("5", "Staten Island")):
    n = q("SELECT COUNT(DISTINCT bbl) FROM parcel_document WHERE substr(bbl,1,1)=?",
          (b,)).fetchone()[0]
    print(f"    {name:<15} {n:>10,} parcels with documents")

BBL = "5000150012"
print(f"\n  READ TEST — BBL {BBL} (Staten Island, block 15 lot 12)")
rows = q("SELECT d.document_id, d.doc_type, d.recorded_date, b.instrument"
         " FROM parcel_document pd"
         " JOIN document d ON d.document_id = pd.document_id"
         " LEFT JOIN rc_binding b ON b.document_id = d.document_id"
         " WHERE pd.bbl = ? ORDER BY d.recorded_date DESC LIMIT 6", (BBL,)).fetchall()
for did, t, rd, instr in rows:
    print(f"    {rd}  {t:<24} {did:<12} instr {instr}")
n = q("SELECT COUNT(*) FROM parcel_document WHERE bbl=?", (BBL,)).fetchone()[0]
nd = q("SELECT n_docs FROM parcel WHERE bbl=?", (BBL,)).fetchone()
print(f"    documents on this parcel: {n}   parcel.n_docs = {nd[0] if nd else None}"
      f"   {'AGREE' if nd and nd[0] == n else 'MISMATCH'}")

print("\n  IMAGE STATE")
for st, n in q("SELECT COALESCE(image_state,'(null)'), COUNT(*) FROM document"
               " GROUP BY 1 ORDER BY 2 DESC").fetchall():
    print(f"    {st:<12} {n:>12,}")
c.close()
