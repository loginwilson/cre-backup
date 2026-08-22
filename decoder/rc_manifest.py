"""ACQUISITION MANIFEST FOR A PARCEL — everything needed to retrieve its documents.

    ACRIS_CORPUS_ROOT=D:/acris python rc_manifest.py 5000150012

Emits, per document: the specification's keys, the storage path it belongs at, and
the resolved access URL. Nothing here is derived at retrieval time - the manifest IS
the acquisition instruction, so whoever (or whatever) performs the fetch needs no
knowledge of the source beyond this file.

⚠ THE URL IS MINTED, NOT STORED. p_endorsementId=<internal_id> mints a fresh,
time-limited token on each request; the token in any saved URL is stale within
minutes. The DURABLE key is internal_id - which the specification holds for all
2,426,404 documents.
"""
import sqlite3, sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP

BBL = sys.argv[1] if len(sys.argv) > 1 else "5000150012"
c = sqlite3.connect("file:" + str(CP.SPEC_DB).replace("\\", "/") + "?mode=ro",
                    uri=True, timeout=300)
rows = c.execute(
    "SELECT d.document_id, d.doc_type, d.recorded_date, d.image_state,"
    "       b.instrument FROM parcel_document pd"
    " JOIN document d ON d.document_id = pd.document_id"
    " LEFT JOIN rc_binding b ON b.document_id = d.document_id"
    " WHERE pd.bbl=? AND substr(d.document_id,1,3)='RC_'"
    " ORDER BY d.recorded_date DESC", (BBL,)).fetchall()

out = []
print(f"  ACQUISITION MANIFEST — BBL {BBL}   {len(rows)} Richmond documents\n")
for did, dtype, rec, img, instr in rows:
    iid = did[3:]
    rec_ = {
        "document_id": did,
        "internal_id": iid,
        "instrument": instr,
        "doc_type": dtype,
        "recorded": rec,
        "image_state": img,
        "detail_url": f"https://www.richmondcountyclerk.com/Search/viewDocumentInfo/{iid}",
        "image_url": f"https://www.richmondcountyclerk.com/ViewVscmsDocument/ViewContent?p_endorsementId={iid}",
        "store_at": str(pathlib.Path(CP.STORE) / f"{did}.pdf"),
    }
    out.append(rec_)
for r in out[:8]:
    print(f"  {r['recorded']}  {r['doc_type']:<26} instr {r['instrument']}")
    print(f"     {r['image_url']}")
dest = pathlib.Path(f"_manifest_{BBL}.jsonl")
dest.write_text("\n".join(json.dumps(r) for r in out), encoding="utf-8")
print(f"\n  full manifest ({len(out)} documents) -> {dest}")
