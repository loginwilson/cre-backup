"""INDEX ACQUISITION — the second acquisition mode, and the universal one.

⚠ THE REFRAME. "Documents with no image" first looked like a class to SKIP.
Login's correction: a release of estate tax lien is still an event, and
ENCUMBER has to report it. Skipping it does not save work — it loses a fact.

So acquisition has TWO MODES, and they are not alternatives:

    INDEX   ALWAYS. Every document, all 17M. Socrata, free, unthrottled.
            -> what kind of instrument, when, WHO (with addresses), WHICH
               parcels, cross-references, remarks.
            -> yields EVENT claims for every document in ACRIS.

    IMAGE   ONLY where pages exist (97.65%). Rate-limited, ~100 req/s.
            -> yields TERM claims: covenants, amounts, geometry, and the
               proof crops that support them.

⚠ THIS IS NOT A WORKAROUND FOR THE 2.35%. It is how acquisition should have
been built. The index carries parties and dates for EVERY document, free — and
that has been sitting unused while images were treated as the only source.
For an image-less document the index is simply the whole story rather than the
first chapter.

⚠ WHAT PROVES AN INDEX CLAIM. A read claim carries a proof crop; an index claim
has no page to crop. Its proof is THE QUERY — dataset, document_id, and the
field read. That is not weaker than a crop, it is stronger: anyone can re-run
it for free, forever, and get the same answer. A crop can only be checked
against an image somebody still has.

    evidence = "index"      dataset + document_id + field
    evidence = "read"       page + region + verbatim + crop

⚠ AND "no image" IS ITSELF A CLAIM. Recorded explicitly, so a later reader can
tell "this instrument has no scanned body" from "nobody has fetched it yet".
That distinction is the barren_reason rule in ARCHITECTURE.md, and it is the
difference between a finished document and an unfinished one.
"""
import collections
import json
import pathlib
import sys

import bulk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MASTER = "bnx9-e6tj"
LEGALS = "8h5j-fqxa"
PARTIES = "636b-3b5g"
REFS = "pwkr-dpni"
REMARKS = "9p4w-7npp"
OUT = pathlib.Path("index_acquired.jsonl")


def no_image_docs(maps_path="acris_maps.jsonl", limit=None):
    """Documents selection has proven have no retrievable image."""
    out = []
    with open(maps_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            t = r.get("hid_TotalPages")
            # ⚠ BOTH non-positive states. 0 (RTXL) and -1 (microfilm era) were
            # verified live, 28/28, to return ACRIS's placeholder image.
            if t is not None and t <= 0:
                out.append(r["doc_id"])
                if limit and len(out) >= limit:
                    break
    return out


def _by_doc(dataset, ids, select):
    """Every row of `dataset` for these documents, keyed by document_id.

    ⚠ THIS USED TO WALK ITS CHUNKS ONE AT A TIME while `bulk.socrata_in` — which
    does the identical chunking CONCURRENTLY, at a measured IN_CLAUSE_MAX of 500
    (1,000 is an HTTP 414) — sat unused in the module already imported above.
    For the 174,086 image-less documents that is 349 chunks per dataset and five
    datasets: 1,745 requests back to back. The chunking was never the cost; the
    waiting between chunks was.
    """
    got = collections.defaultdict(list)
    for r in bulk.socrata_in(dataset, "document_id", ids, select=select):
        got[r["document_id"]].append(r)
    return got


def acquire(ids):
    """Pull every index surface for these documents. Free; no image budget."""
    master = _by_doc(MASTER, ids,
                     "document_id,crfn,doc_type,document_date,recorded_datetime,"
                     "recorded_borough,document_amt,percent_trans,reel_yr,"
                     "reel_nbr,reel_pg")
    parties = _by_doc(PARTIES, ids,
                      "document_id,party_type,name,address_1,address_2,city,"
                      "state,zip,country")
    legals = _by_doc(LEGALS, ids,
                     "document_id,borough,block,lot,easement,partial_lot,"
                     "air_rights,subterranean_rights,property_type,"
                     "street_number,street_name,unit")
    refs = _by_doc(REFS, ids, "document_id,reference_by_crfn_,reference_by_doc_id,"
                              "reference_by_reel_year,reference_by_reel_borough")
    remarks = _by_doc(REMARKS, ids, "document_id,sequence_number,remark_text")

    docs = []
    for d in ids:
        m = (master.get(d) or [{}])[0]
        docs.append({
            "document_id": d,
            "acquisition_mode": "index",
            # ⚠ WHY there is no image, not merely that there isn't one.
            "no_image": True,
            "no_image_reason": "acris_placeholder_returned",
            "master": m,
            "parties": parties.get(d, []),
            "legals": legals.get(d, []),
            "references": refs.get(d, []),
            "remarks": remarks.get(d, []),
        })
    return docs


def to_event_claim(doc):
    """The one claim every document owes, whether or not it has a body."""
    m = doc["master"]
    lots = [f"{l['borough']}{int(l['block']):05d}{int(l['lot']):04d}"
            for l in doc["legals"] if l.get("block") and l.get("lot")]
    who = [f"{p.get('name')} ({p.get('party_type')})" for p in doc["parties"]]
    return {
        "document_id": doc["document_id"],
        "predicate": "instrument_recorded",
        "doc_type": m.get("doc_type"),
        "effective": (m.get("document_date") or "")[:10] or None,
        "stated": (m.get("recorded_datetime") or "")[:10] or None,
        "subject_bbl_raw": lots,
        "parties": who,
        "amount": m.get("document_amt"),
        "crfn": m.get("crfn"),
        # ⚠ evidence=index, and the proof is the query — re-runnable forever.
        "evidence": "index",
        "proof": {"datasets": ["bnx9-e6tj", "636b-3b5g", "8h5j-fqxa"],
                  "key": doc["document_id"]},
        "barren_reason": "no scanned image exists for this instrument; the "
                         "index record is the complete record",
    }


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    ids = no_image_docs(limit=n)
    print(f"{len(ids)} image-less documents selected")
    docs = acquire(ids)
    with open(OUT, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps({"document": d, "claim": to_event_claim(d)}) + "\n")
    got_m = sum(1 for d in docs if d["master"])
    got_p = sum(1 for d in docs if d["parties"])
    got_l = sum(1 for d in docs if d["legals"])
    got_r = sum(1 for d in docs if d["remarks"])
    print(f"  master  {got_m}/{len(docs)}   parties {got_p}/{len(docs)}   "
          f"legals {got_l}/{len(docs)}   remarks {got_r}/{len(docs)}")
    tc = collections.Counter(d["master"].get("doc_type") for d in docs)
    print(f"  types: {dict(tc.most_common(6))}")
    ex = next((json.loads(l)["claim"] for l in OUT.read_text(encoding="utf-8")
               .splitlines() if json.loads(l)["document"]["parties"]), None)
    if ex:
        print("\n  example event claim:")
        for k in ("doc_type", "effective", "stated", "subject_bbl_raw",
                  "parties", "crfn"):
            print(f"    {k:<16} {ex[k]}")
    print(f"\n  -> {OUT}")
