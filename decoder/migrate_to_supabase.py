"""Migrate decoded documents + reduced postings to Supabase.

Reads: decoded JSONs (facts) + the per-document envelope postings derived from
their validated numbers (the DEVR reducer output, stated explicitly here with
provenance). Writes: decoder_document, decoder_posting, decoder_lifecycle_link,
decoder_consent via PostgREST. Idempotent (upsert on conflict).

Usage: python migrate_to_supabase.py <decoded_dir>
Env:   C:/dev/acris-decoder.env  (ACRIS_SUPABASE_URL, ACRIS_SUPABASE_SERVICE_KEY)
"""
import json, pathlib, re, sys, urllib.request

ENV = r"C:/dev/acris-decoder.env"


def env():
    vals = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()
    return vals["ACRIS_SUPABASE_URL"], vals["ACRIS_SUPABASE_SERVICE_KEY"]


def post(url, key, table, rows, on_conflict):
    if not rows:
        return 0
    req = urllib.request.Request(
        f"{url}/rest/v1/{table}?on_conflict={on_conflict}",
        data=json.dumps(rows).encode(),
        headers={"apikey": key, "Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 "Prefer": "resolution=merge-duplicates"},
        method="POST")
    with urllib.request.urlopen(req, timeout=60) as f:
        f.read()
    return len(rows)


# Envelope transfers are owned exclusively by reduce.py (declarative transfer
# spec -> transfer-group postings). This module handles documents, zoning-lot
# membership, form/use effects, citations and consents. The hand-typed
# ENVELOPE_POSTINGS table that used to live here has been removed: it both
# duplicated reduce.py and shadowed the bbl() helper below.

BOROS = {"manhattan": 1, "bronx": 2, "brooklyn": 3, "queens": 4, "staten island": 5}


def bbl(borough, block, lot):
    if isinstance(borough, str) and not borough.isdigit():
        borough = BOROS[borough.strip().lower()]
    return f"{int(borough)}{int(block):05d}{int(lot):04d}"


def reduce_doc(d):
    """facts JSON -> posting rows (envelope transfers + membership + form/use)."""
    doc_id = d["doc_id"]
    rows = []
    # Roster entries arrive in either shape: {"bbl": "1014460001"} or
    # {"borough": "Manhattan", "block": 1446, "lot": 1}. Filtering to the first
    # shape silently dropped every membership posting for documents written the
    # other way — the zoning-lot map lost lots with no error raised. Accept both.
    roster = []
    for r in d.get("zoning_lot_roster", []):
        if r.get("bbl"):
            roster.append(r["bbl"])
        elif r.get("borough") is not None and r.get("block") is not None:
            lot = str(r.get("lot", "")).split()[0].split("(")[0].split("-")[0].strip()
            if lot.isdigit():
                roster.append(bbl(r["borough"], r["block"], lot))
    for the_bbl in roster:
        rows.append(dict(document_id=doc_id, bbl=the_bbl, bbl_source="document",
                         account="envelope_membership", effective_date=iso(d),
                         quantity_sf=None, amount_usd=None,
                         counter_bbls=[b for b in roster if b != the_bbl],
                         payload={"instrument": d.get("instrument_kind")},
                         provenance="zoning lot roster (see raw_facts)"))
    # PARTIES. These were sitting in raw_facts unreduced — the account existed in
    # the chart and the table had zero rows, so every name we had decoded was
    # invisible to any query.
    #
    # A party observation is NOT a contact. It is immutable and stamped: this
    # name, in this role, on this lot, on this document, on this date. A contact
    # ("who do I call about this site today") is a FOLD over these, and folding
    # needs something to fold. Collect the observations; derive the contact.
    for party in d.get("parties", []):
        name = (party.get("name") or "").strip()
        if not name:
            continue
        # a party is stated against a lot when the document says so; when it
        # does not, the observation still stands against the zoning lot
        lot = str(party.get("tax_lot") or "").strip()
        m = re.match(r"^(\d)\s*/\s*(\d+)\s*/\s*(\d+)", lot)
        the_bbl = bbl(m.group(1), m.group(2), m.group(3)) if m else (
            roster[0] if roster else "unknown")
        rows.append(dict(
            document_id=doc_id, bbl=the_bbl,
            bbl_source="document" if m else "zoning_lot_lead",
            account="party_observation", effective_date=iso(d),
            quantity_sf=party.get("sf"), amount_usd=None, counter_bbls=None,
            payload={"name": name,
                     "role": party.get("normalized_role"),
                     "label_in_doc": party.get("label_in_doc"),
                     "tax_lot_as_stated": lot or None,
                     "note": party.get("note"),
                     "instrument": d.get("instrument_kind"),
                     # what the name is stated against, unresolved on purpose:
                     # "2502/1; 2510/1; 2520/57" is three lots in one string and
                     # inventing a split would be worse than carrying the string
                     "lot_string_unparsed": bool(lot and not m)},
            provenance=f"parties[]: {name} as "
                       f"{party.get('normalized_role') or party.get('label_in_doc') or 'party'}"
                       + (f" ({lot})" if lot else "")))

    for f in d.get("form_and_use_effects", []):
        acct = {"form_restriction": "envelope_form", "use_restriction": "use_restriction",
                "obligation": "standing"}.get(f.get("kind"), "envelope_form")
        rows.append(dict(document_id=doc_id, bbl=roster[0] if roster else "unknown",
                         bbl_source="document", account=acct, effective_date=iso(d),
                         quantity_sf=None, amount_usd=None, counter_bbls=None,
                         payload={"detail": f.get("detail")},
                         # a page number alone is not a locator — carry what is
                         # on that page so a human confirms it in ten seconds
                         provenance=f"p{f.get('page')}: {str(f.get('detail'))[:90]}"))
    return rows


def iso(d):
    v = (d.get("effective_dates") or {}).get("document_date")
    if isinstance(v, dict):
        v = v.get("value")
    if not v:
        return None
    v = str(v)[:10]
    return v if len(v) == 10 and v[4] == "-" else None


def main(decoded_dir):
    url, key = env()
    docs, postings, links, consents = [], [], [], []
    for f in sorted(pathlib.Path(decoded_dir).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        cons = d.get("consideration") or {}
        c = cons.get("recovered") or cons.get("index_amt")
        docs.append(dict(
            document_id=d["doc_id"], source="acris",
            crfn=(d.get("effective_dates") or {}).get("crfn"),
            doc_type="DEVR", instrument=d.get("instrument_kind"),
            what_it_does=d.get("summary_what_it_does"),
            document_date=iso(d),
            recorded_date=str((d.get("effective_dates") or {}).get("recorded") or "")[:10] or None,
            batch_prefix=d["doc_id"][:13],
            consideration=c if isinstance(c, (int, float)) else None,
            decode_status=d.get("decode_status", "validated"),
            validation_tier=d.get("validation_tier"),
            checks=d.get("self_checks") or d.get("self_checks_summary"),
            anomalies=d.get("anomalies"), raw_facts=d,
            decoder_version=d.get("decoder", "unknown")))
        postings.extend(reduce_doc(d))
        for x in d.get("cross_instruments", []):
            # A citation is WHAT is cited plus HOW it is identified. Storing only
            # the identifier loses the description, and reference-less citations
            # ("Declaration of Zoning Lot Restrictions, of even date") then cannot
            # be resolved against the recording batch at all.
            links.append(dict(document_id=d["doc_id"],
                              relation=x.get("relation", "cites"),
                              target_kind=x.get("how_cited", "unresolved"),
                              target_ref=f"{x.get('what')} :: {x.get('identifier')}"[:400],
                              provenance=str(x.get("page", ""))))
        for cw in d.get("consents_waivers", []):
            consents.append(dict(document_id=d["doc_id"], party=str(cw.get("party"))[:200],
                                 instrument=cw.get("instrument", "consent"),
                                 present=bool(cw.get("present_in_doc")),
                                 provenance=str(cw.get("page", ""))))
    # dedupe within-payload on each table's conflict key (PostgREST 500s if one
    # request updates the same row twice)
    def dedupe(rows, keyf):
        seen, out = set(), []
        for r in rows:
            k = keyf(r)
            if k not in seen:
                seen.add(k); out.append(r)
        return out
    postings = dedupe(postings, lambda r: (r["document_id"], r["bbl"], r["account"], r["provenance"]))
    links = dedupe(links, lambda r: (r["document_id"], r["relation"], r["target_ref"]))
    consents = dedupe(consents, lambda r: (r["document_id"], r["party"], r["instrument"]))
    n1 = post(url, key, "decoder_document", docs, "document_id")
    n2 = post(url, key, "decoder_posting", postings, "document_id,bbl,account,provenance")
    n3 = post(url, key, "decoder_lifecycle_link", links, "document_id,relation,target_ref")
    n4 = post(url, key, "decoder_consent", consents, "document_id,party,instrument")
    print(f"documents={n1} postings={n2} lifecycle_links={n3} consents={n4}")


if __name__ == "__main__":
    main(sys.argv[1])
