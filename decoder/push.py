"""PUSH — the decoded parcel into Supabase, along the parcel spine.

    claims -> proofs -> claim_proofs -> reads

⚠ ORDER MATTERS AND IT IS NOT ALPHABETICAL.

  claims before proofs        acris_claim_proofs has FKs to both
  supersedes patched LAST     it is a self-FK; a claim cannot reference a
                              claim that has not been inserted yet
  reads last                  acris_decode_status reads it, and the view
                              should not report a document DONE until its
                              claims and proofs are actually there

⚠ FUNCTION TAGS ARE CANONICALISED ON THE WAY IN. The `answers` array is
written freehand at claim time and drifted badly — CAPITAL vs DEBT (105
claims), ENCUMBER vs ENCUMBRANCE (26), plus eight tags naming functions no
view knew. Canonicalising at write time means the database never holds two
spellings of one function. See functions_vocab.py.

⚠ CREDENTIALS ARE READ FROM C:\\dev\\acris-decoder.env AND NEVER PRINTED.

    python push.py --dry     what would go, nothing written
    python push.py           write it
"""
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import claims as K
import functions_vocab as FV
import reads as R
import harvest as H

ENV = pathlib.Path(r"C:\dev\acris-decoder.env")
BBL = "1008000049"
BATCH = 200

CLAIM_COLS = {
    "claim_id", "bbl", "subject_bbl", "document_id", "page", "predicate",
    "value_num", "value_text", "unit", "parties", "effective", "stated",
    "answers", "evidence", "verbatim", "derivation", "supersedes",
    "v_from", "v_to", "v_datum", "h_extent", "h_from", "duration",
    "region_scope",
}


def creds():
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env["ACRIS_SUPABASE_URL"], env["ACRIS_SUPABASE_SERVICE_KEY"]


def post(url, key, table, rows, on_conflict=None, method="POST"):
    if not rows:
        return 0
    sent = 0
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        u = f"{url}/rest/v1/{table}"
        if on_conflict:
            u += f"?on_conflict={on_conflict}"
        req = urllib.request.Request(
            u, data=json.dumps(chunk, default=str).encode(),
            method=method,
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "Prefer": "resolution=merge-duplicates,return=minimal"})
        try:
            with urllib.request.urlopen(req, timeout=60):
                sent += len(chunk)
        except urllib.error.HTTPError as e:
            body = e.read()[:400].decode(errors="replace")
            print(f"  ⚠ {table} rows {i}-{i+len(chunk)}: HTTP {e.code}")
            print(f"    {body}")
            return sent
    return sent


def build_claims():
    out = []
    for c in K.rows():
        r = {k: v for k, v in c.items() if k in CLAIM_COLS}
        r["bbl"] = r.get("bbl") or BBL
        r["subject_bbl"] = r.get("subject_bbl") or r["bbl"]
        # ⚠ canonicalise here so the DB never holds two spellings of one
        # function. Unknown tags are DROPPED, not invented into new functions.
        fns = sorted({f for a in (c.get("answers") or [])
                      if (f := FV.canon(a))})
        r["answers"] = fns
        for k in ("parties",):
            if r.get(k) is not None and not isinstance(r[k], (list, dict)):
                r[k] = [r[k]]
        out.append(r)
    return out


def build_proofs():
    """One row per crop ON DISK IN proofs/, mapped back via the claim.

    ⚠ DO NOT enumerate from pages_out. After a sweep those folders are gone
    BY DESIGN, so pages_out-driven discovery returns nothing for exactly the
    documents that are furthest along. The crop is the durable artifact —
    ask the crop, not the scaffolding that produced it.
    """
    proofs, links, seen = [], [], {}
    for c in K.rows():
        if not c["page"]:
            continue
        pid = H.crop_key(c["document_id"], c["page"])
        p = H.PROOFS / f"{pid}.png"
        if not p.exists() or p.stat().st_size < H.MIN_CROP_BYTES:
            continue
        if pid not in seen:
            seen[pid] = True
            proofs.append(dict(
                proof_id=pid, document_id=c["document_id"], page=c["page"],
                y0=None, y1=None,           # ⚠ region not captured at read time
                bytes=p.stat().st_size,
                storage_path=f"proofs/{p.name}"))
        links.append(dict(claim_id=c["claim_id"], proof_id=pid))
    return proofs, links


def build_reads():
    out = []
    for doc, spec in R.OPENED.items():
        pages = sorted(R.expand(spec))
        n = len(H.doc_pages(doc))
        out.append(dict(document_id=doc, bbl=BBL,
                        pages_on_disk=n or len(pages),
                        pages_opened=pages, pages_empty=[],
                        page_count_declared=None))
    return out


def main():
    dry = "--dry" in sys.argv
    cl = build_claims()
    pr, lk = build_proofs()
    rd = build_reads()
    unnarrowed = sum(1 for p in pr if p["y0"] is None)

    print(f"  claims        {len(cl)}")
    print(f"  proofs        {len(pr)}")
    print(f"  claim_proofs  {len(lk)}")
    print(f"  reads         {len(rd)}")
    have = {p["proof_id"] for p in pr}
    orphan = sum(1 for c in K.rows()
                 if c["page"] and H.crop_key(c["document_id"], c["page"])
                 not in have)
    print(f"  ⚠ claims with no proof: {orphan}   "
          f"(their pages are still held — cannot be swept)")
    print(f"  ⚠ proofs with no region: {unnarrowed}/{len(pr)} — whole-page "
          f"crops at ~69 KB instead of ~7 KB.")
    print(f"    They can be narrowed later FROM THE CROP, without the page.")
    if dry:
        print("\n  --dry, nothing written")
        return

    url, key = creds()
    print()
    n = post(url, key, "acris_claims",
             [{k: v for k, v in r.items() if k != "supersedes"} for r in cl],
             on_conflict="claim_id")
    print(f"  acris_claims        {n}")
    # ⚠ PATCH, NOT UPSERT. Sending {claim_id, supersedes} as an upsert
    # rewrites the whole row and nulls every column not supplied — which
    # PostgREST rejected on the NOT NULL bbl, correctly. A partial update is
    # an UPDATE, and expressing it as an insert silently destroys data on
    # any table whose constraints happen to be looser.
    # ⚠ CLEAR FIRST. An upsert never REMOVES a value the source no longer
    # sets, so an earlier wrong direction survived and produced a CYCLE in
    # the database: A superseded B and B superseded A. A partial sync that
    # only writes is not a sync.
    want = {r["claim_id"]: r["supersedes"] for r in cl if r.get("supersedes")}
    try:
        q = urllib.request.Request(
            f"{url}/rest/v1/acris_claims?select=claim_id&supersedes=not.is.null",
            headers={"apikey": key, "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(q, timeout=30) as r:
            stale = [x["claim_id"] for x in json.loads(r.read().decode())
                     if x["claim_id"] not in want]
    except Exception:
        stale = []
    for cid in stale:
        u = (f"{url}/rest/v1/acris_claims?claim_id=eq."
             + urllib.parse.quote(cid))
        req = urllib.request.Request(
            u, data=b'{"supersedes":null}', method="PATCH",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "Prefer": "return=minimal"})
        try:
            with urllib.request.urlopen(req, timeout=30):
                pass
        except urllib.error.HTTPError:
            pass
    if stale:
        print(f"  supersedes cleared  {len(stale)} stale")
    sup = [r for r in cl if r.get("supersedes")]
    m = 0
    for r in sup:
        u = (f"{url}/rest/v1/acris_claims?claim_id=eq."
             + urllib.parse.quote(r["claim_id"]))
        req = urllib.request.Request(
            u, data=json.dumps({"supersedes": r["supersedes"]}).encode(),
            method="PATCH",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "Prefer": "return=minimal"})
        try:
            with urllib.request.urlopen(req, timeout=30):
                m += 1
        except urllib.error.HTTPError as e:
            print(f"    ⚠ {r['claim_id']}: HTTP {e.code}")
    print(f"  supersedes patched  {m}")
    n = post(url, key, "acris_proofs", pr, on_conflict="proof_id")
    print(f"  acris_proofs        {n}")
    n = post(url, key, "acris_claim_proofs", lk,
             on_conflict="claim_id,proof_id")
    print(f"  acris_claim_proofs  {n}")
    n = post(url, key, "acris_reads", rd, on_conflict="document_id")
    print(f"  acris_reads         {n}")


main()
