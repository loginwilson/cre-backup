"""Load decoded document JSONs into the fact store (schema.sql).

Usage: python load_facts.py <db_path> <decoded_dir>
Idempotent: re-loading a document replaces its rows.
"""
import json, sqlite3, sys, pathlib


def bbl(borough, block, lot):
    b = {"manhattan": 1, "bronx": 2, "brooklyn": 3, "queens": 4, "staten island": 5}
    if isinstance(borough, str) and not borough.isdigit():
        borough = b[borough.strip().lower()]
    return f"{int(borough)}{int(block):05d}{int(lot):04d}"


def load(db, path):
    d = json.loads(path.read_text(encoding="utf-8"))
    doc_id = d["doc_id"]
    title = (d.get("instrument_title") or {}).get("value")
    cons = d.get("consideration") or {}
    consideration = cons.get("index_amt") or cons.get("in_document")
    if isinstance(consideration, str):
        consideration = None
    checks = d.get("self_checks") or d.get("self_checks_summary")
    db.execute("DELETE FROM effect WHERE document_id=?", (doc_id,))
    db.execute("DELETE FROM lifecycle_link WHERE document_id=?", (doc_id,))
    db.execute("DELETE FROM consent WHERE document_id=?", (doc_id,))
    db.execute(
        """INSERT OR REPLACE INTO document
           (document_id, crfn, doc_type, instrument, what_it_does, document_date,
            recorded_date, batch_prefix, consideration, decode_status,
            validation_tier, checks_json, decoded_at, decoder_version, raw_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),?,?)""",
        (doc_id,
         (d.get("effective_dates") or {}).get("crfn"),
         "DEVR",
         d.get("instrument_kind"),
         d.get("summary_what_it_does") or title,
         (d.get("effective_dates") or {}).get("document_date"),
         (d.get("effective_dates") or {}).get("recorded"),
         doc_id[:13],
         consideration,
         d.get("decode_status", "validated"),
         d.get("validation_tier"),
         json.dumps(checks),
         d.get("decoder", "unknown"),
         json.dumps(d)))
    # effects: one row per roster BBL; direction from parties' normalized roles
    roster = d.get("zoning_lot_roster") or []
    roles = {}
    for p in d.get("parties") or []:
        tl = p.get("tax_lot") or ""
        roles[tl] = p.get("normalized_role")
    for r in roster:
        the_bbl = r.get("bbl") or bbl(r["borough"], r["block"], str(r["lot"]).split()[0].split("(")[0])
        kind = "object_definition"   # zoning-lot membership is itself the effect
        db.execute(
            """INSERT OR REPLACE INTO effect
               (document_id, bbl, bbl_source, effect_kind, role_in_doc,
                quantity_sf, detail_json, page_provenance)
               VALUES (?,?,?,?,?,?,?,?)""",
            (doc_id, the_bbl, "document", kind, None, None,
             json.dumps(r), str(r.get("page", ""))))
    for x in d.get("cross_instruments") or []:
        db.execute(
            """INSERT OR REPLACE INTO lifecycle_link
               (document_id, relation, target_kind, target_ref, resolved_doc_id, page_provenance)
               VALUES (?,?,?,?,?,?)""",
            (doc_id, "cites", x.get("how_cited", "unresolved"),
             str(x.get("identifier")), None, str(x.get("page", ""))))
    for c in d.get("consents_waivers") or []:
        db.execute(
            """INSERT OR REPLACE INTO consent
               (document_id, party, instrument, present, page_provenance)
               VALUES (?,?,?,?,?)""",
            (doc_id, str(c.get("party"))[:200], c.get("instrument", "consent"),
             1 if c.get("present_in_doc") else 0, str(c.get("page", ""))))
    return doc_id


if __name__ == "__main__":
    db_path, decoded = sys.argv[1], pathlib.Path(sys.argv[2])
    db = sqlite3.connect(db_path)
    db.executescript(pathlib.Path(__file__).with_name("schema.sql").read_text())
    n = 0
    for f in sorted(decoded.glob("*.json")):
        print("loaded", load(db, f)); n += 1
    db.commit()
    print(f"{n} documents loaded")
