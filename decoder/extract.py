"""EXTRACT — the complete ACRIS index for a parcel, done properly.

⚠ WHAT THIS IS AND IS NOT.

It is NOT an image fetch. ACRIS document images cannot be pulled at scale:
the viewer rate-limits far below what a citywide pull needs, and the image
corpus is ~14.3 TB. That is a PROCUREMENT problem (the EDS "Index/Image
Retrieval" service, ~$0.0005/doc), not an engineering one, and the standing
rule on this project is no bulk image scraper and no working around bot
detection. Nothing here touches an image.

It IS the complete structured index, which is free, public, and the thing the
whole decode should have been anchored to from the start. FIVE datasets, not
the two I have been using:

    8h5j-fqxa  LEGALS      BBL -> document_id. THE SPINE JOIN.
    bnx9-e6tj  MASTER      type, dates, amounts, CRFN, recording data
    636b-3b5g  PARTIES     every party, its role, and its address
    pwkr-dpni  REFERENCES  ⚠ document -> document. THE CHAIN, PRE-BUILT.
    9p4w-7npp  REMARKS     ⚠ free-text notes recorded against a document

⚠ THE TWO I NEVER PULLED ARE THE TWO THAT WOULD HAVE SAVED THE MOST WORK.

REFERENCES is the assignment chain as a graph. I reconstructed thirteen
holders across thirty-five years by reading schedules off page images, one
agent at a time. That edge list is a table.

REMARKS is where "NOTE: Recites incorrect legal description" lives — the
27-year uncured defect I found by reading a schedule inside a mortgage.

⚠ AND THE ORDER MATTERS. Index first, then reconcile, then read. Every
structural defect on lot 49 — five foreign documents, a folder holding
another document's body, five truncations — was invisible to reading and
obvious to the index.

    python extract.py <bbl>            pull and summarise
    python extract.py <bbl> --push     pull and write to Supabase
"""
import collections
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://data.cityofnewyork.us/resource"
SETS = {
    "legals":     "8h5j-fqxa",
    "master":     "bnx9-e6tj",
    "parties":    "636b-3b5g",
    "references": "pwkr-dpni",
    "remarks":    "9p4w-7npp",
}
ENV = pathlib.Path(r"C:\dev\acris-decoder.env")


def soda(dataset, where):
    """⚠ ALWAYS $order=:id. Without it $offset silently drops and duplicates
    rows while the COUNT stays right. That trap has already corrupted a
    decoder in this project once."""
    out, off = [], 0
    while True:
        q = {"$where": where, "$order": ":id", "$limit": 1000, "$offset": off}
        url = f"{BASE}/{dataset}.json?" + urllib.parse.urlencode(q)
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url), timeout=90) as r:
                b = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            print(f"    ⚠ {dataset}: HTTP {e.code}")
            return out
        out.extend(b)
        if len(b) < 1000:
            return out
        off += 1000


def by_docs(dataset, ids):
    out = []
    for i in range(0, len(ids), 40):
        lst = "','".join(ids[i:i + 40])
        out.extend(soda(dataset, f"document_id in('{lst}')"))
    return out


def extract(bbl):
    b, blk, lot = int(bbl[0]), int(bbl[1:6]), int(bbl[6:])
    print(f"EXTRACT · BBL {bbl}\n")
    legals = soda(SETS["legals"], f"borough={b} AND block={blk} AND lot={lot}")
    ids = sorted({r["document_id"] for r in legals if r.get("document_id")})
    print(f"  legals      {len(legals):>5} rows   {len(ids)} documents")
    data = {"legals": legals}
    for name in ("master", "parties", "references", "remarks"):
        rows = by_docs(SETS[name], ids)
        data[name] = rows
        print(f"  {name:<11} {len(rows):>5} rows")
    return ids, data


def creds():
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env["ACRIS_SUPABASE_URL"], env["ACRIS_SUPABASE_SERVICE_KEY"]


def push(bbl, ids, data):
    url, key = creds()
    rows = []
    m = {r["document_id"]: r for r in data["master"]}
    for d in ids:
        x = m.get(d, {})
        # ⚠ MAPPED TO THE REAL SCHEMA. My first attempt invented columns
        # (crfn, document_amt, pages) that migration_004 never declared and
        # PostgREST rejected the whole batch. The DDL is the source of truth
        # for column names — not what the API happens to call its fields.
        amt = x.get("document_amt")
        try:
            amt = float(amt) if amt not in (None, "") else None
        except ValueError:
            amt = None
        rows.append(dict(
            bbl=bbl, document_id=d,
            event_id=d,                 # index rows are their own event
            doc_type=(x.get("doc_type") or "").upper(),
            amount_indexed=amt,
            instrument_date=(x.get("document_date") or "")[:10] or None,
            recorded_date=(x.get("recorded_datetime") or "")[:10] or None,
            role="principal",
            # ⚠ amount_real stays NULL. The INDEXED amount is what ACRIS says
            # the instrument is worth, which on this parcel is routinely a
            # face amount, a restatement, or a $10 recital. Only a decode
            # earns amount_real.
            amount_real=None,
            evidence="index",
            note="ACRIS index extract"))
    sent = 0
    for i in range(0, len(rows), 200):
        chunk = rows[i:i + 200]
        req = urllib.request.Request(
            f"{url}/rest/v1/acris_documents?on_conflict=bbl,document_id",
            data=json.dumps(chunk, default=str).encode(), method="POST",
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json",
                     "Prefer": "resolution=merge-duplicates,return=minimal"})
        try:
            with urllib.request.urlopen(req, timeout=60):
                sent += len(chunk)
        except urllib.error.HTTPError as e:
            print(f"  ⚠ acris_documents: HTTP {e.code} "
                  f"{e.read()[:200].decode(errors='replace')}")
            break
    print(f"\n  acris_documents  {sent} rows written")


def report(bbl, ids, data):
    m = {r["document_id"]: r for r in data["master"]}

    print("\n  ⚠ REFERENCES — the assignment chain, PRE-BUILT")
    refs = data["references"]
    if refs:
        print(f"    {len(refs)} document-to-document edges. I rebuilt this by")
        print(f"    reading schedules off page images, agent by agent.")
        for r in refs[:6]:
            print(f"      {r.get('document_id')} -> "
                  f"{r.get('reference_by_crfn_') or r.get('reference_by_doc_id') or '?'}")
    else:
        print("    none returned for this parcel")

    print("\n  ⚠ REMARKS — free text recorded against a document")
    rem = data["remarks"]
    if rem:
        for r in rem[:8]:
            txt = (r.get("remark_text") or "").strip()
            if txt:
                print(f"      {r.get('document_id')}  {txt[:78]}")
    else:
        print("    none returned for this parcel")

    print("\n  PARTIES by role")
    roles = collections.Counter(p.get("party_type") for p in data["parties"])
    for k, v in roles.most_common():
        print(f"    type {k}: {v}")

    print("\n  DOC TYPES")
    ts = collections.Counter((m.get(d, {}).get("doc_type") or "?").upper()
                             for d in ids)
    for t, n in ts.most_common(12):
        print(f"    {t:<10} {n}")


def main():
    bbl = sys.argv[1] if len(sys.argv) > 1 else "1008000049"
    ids, data = extract(bbl)
    report(bbl, ids, data)
    out = pathlib.Path(f"acris_index_{bbl}.json")
    out.write_text(json.dumps({"bbl": bbl, "ids": ids, **data}, indent=1),
                   encoding="utf-8")
    print(f"\n  cached -> {out}  ({out.stat().st_size/1024:.0f} KB)")
    if "--push" in sys.argv:
        push(bbl, ids, data)


main()
