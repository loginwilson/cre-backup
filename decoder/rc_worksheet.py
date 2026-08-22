"""A CLICK-THROUGH WORKSHEET FOR ONE PARCEL — skip the ledger, skip the search.

    ACRIS_CORPUS_ROOT=D:/acris python rc_worksheet.py 5000150012

The manual retrieval flow is: block ledger -> find row -> click document -> click
image -> save. The specification already knows every document on the parcel, so
the first three steps are navigation we can delete. This emits ONE page with a
direct image link per document, ordered newest first, with the filename each
document should be saved as so the corpus layout stays consistent.

⚠ THE LINKS MINT A FRESH TOKEN ON EACH CLICK - so this page does not go stale the
way a saved viewer URL does. Regenerate it any time; it is derived, not stored.
"""
import sqlite3, sys, pathlib, html
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP

BBL = sys.argv[1] if len(sys.argv) > 1 else "5000150012"
c = sqlite3.connect("file:" + str(CP.SPEC_DB).replace("\\", "/") + "?mode=ro",
                    uri=True, timeout=300)
rows = c.execute(
    "SELECT d.document_id, d.doc_type, d.recorded_date, b.instrument"
    " FROM parcel_document pd JOIN document d ON d.document_id=pd.document_id"
    " LEFT JOIN rc_binding b ON b.document_id=d.document_id"
    " WHERE pd.bbl=? AND substr(d.document_id,1,3)='RC_'"
    " ORDER BY d.recorded_date DESC", (BBL,)).fetchall()
acris = c.execute(
    "SELECT COUNT(*) FROM parcel_document pd JOIN document d"
    " ON d.document_id=pd.document_id WHERE pd.bbl=?"
    " AND substr(d.document_id,1,3)<>'RC_'", (BBL,)).fetchone()[0]

B = "https://www.richmondcountyclerk.com"
parts = [f"""<meta charset="utf-8"><title>BBL {BBL}</title>
<style>
 body{{font:14px/1.5 system-ui,sans-serif;margin:2rem;max-width:60rem}}
 h1{{font-size:1.3rem;margin:0 0 .2rem}} .sub{{color:#666;margin-bottom:1.4rem}}
 table{{border-collapse:collapse;width:100%}}
 td,th{{padding:.45rem .6rem;border-bottom:1px solid #e3e3e3;text-align:left}}
 th{{font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:#666}}
 tr:hover{{background:#f7f9fc}} a{{color:#1558d6}}
 .k{{font-family:ui-monospace,monospace;font-size:.82rem;color:#555}}
</style>
<h1>BBL {BBL} &mdash; Staten Island</h1>
<div class="sub">{len(rows)} Richmond documents &middot; {acris} ACRIS documents on the same parcel.
Each link opens the county viewer; save as the filename shown.</div>
<table><tr><th>Recorded</th><th>Type</th><th>Instrument</th><th>Open</th><th>Save as</th></tr>"""]
for did, dtype, rec, instr in rows:
    iid = did[3:]
    parts.append(
        f"<tr><td>{rec or ''}</td><td>{html.escape(dtype or '')}</td>"
        f"<td class='k'>{instr or ''}</td>"
        f"<td><a href='{B}/ViewVscmsDocument/ViewContent?p_endorsementId={iid}'"
        f" target='_blank'>image</a> &middot; "
        f"<a href='{B}/Search/viewDocumentInfo/{iid}' target='_blank'>detail</a></td>"
        f"<td class='k'>{did}.pdf</td></tr>")
parts.append("</table>")
out = pathlib.Path(f"_worksheet_{BBL}.html")
out.write_text("\n".join(parts), encoding="utf-8")
print(f"  {len(rows)} Richmond documents (+{acris} ACRIS) -> {out}")
