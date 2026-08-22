import sqlite3, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP
c = sqlite3.connect("file:" + str(CP.SPEC_DB).replace("\\","/") + "?mode=ro", uri=True, timeout=600)
rows = c.execute(
  "SELECT d.document_id, d.doc_type, d.recorded_date, b.instrument"
  " FROM document d JOIN rc_binding b ON b.document_id=d.document_id"
  " WHERE substr(d.document_id,1,3)='RC_' AND d.doc_type IN ('DEED','MORTGAGE','Deed','Mortgage')"
  " AND d.recorded_date IS NOT NULL"
  " ORDER BY d.recorded_date DESC LIMIT 5").fetchall()
B = "https://www.richmondcountyclerk.com"
for did, t, rec, instr in rows:
    iid = did[3:]
    print(f"\n  {t}  recorded {rec}  ·  instrument {instr}  ·  {did}")
    print(f"  {B}/ViewVscmsDocument/ViewContent?p_endorsementId={iid}")
