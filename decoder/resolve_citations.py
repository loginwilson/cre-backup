"""Citation resolver — turns every reference a decoded document makes into a
resolvable ACRIS document_id, so we can always return to the occurrence.

Three resolution routes:
  crfn      -> ACRIS master lookup by crfn
  doc_id    -> direct
  batch     -> siblings sharing the 13-digit recording-batch prefix (the
               constellation: DECL / ZONE / CERT / SAGE recorded together)
  reel_page -> index lookup by reel_yr/reel_nbr/reel_pg (pre-2003 instruments)

Writes resolved_doc_id back to decoder_lifecycle_link, and reports what could NOT
be resolved (a finding, not a silent gap).
"""
import json, re, sys, urllib.parse, urllib.request

TOKEN = "XBMcBRBwtwiD4elm0XS5iwLRZ"
MASTER = "https://data.cityofnewyork.us/resource/bnx9-e6tj.json"
ENV = r"C:/dev/acris-decoder.env"


def env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


def sb(url, key, path, method="GET", body=None):
    req = urllib.request.Request(
        url + "/rest/v1/" + path,
        data=json.dumps(body).encode() if body else None,
        headers={"apikey": key, "Authorization": f"Bearer {key}",
                 "Content-Type": "application/json", "Prefer": "return=minimal"},
        method=method)
    with urllib.request.urlopen(req, timeout=60) as f:
        raw = f.read()
    return json.loads(raw) if raw and method == "GET" else None


def socrata(where, select="document_id,crfn,doc_type,recorded_datetime,document_amt"):
    q = urllib.parse.urlencode({"$select": select, "$where": where,
                                "$limit": 500, "$$app_token": TOKEN})
    with urllib.request.urlopen(MASTER + "?" + q, timeout=60) as f:
        return json.load(f)


def crfns_in(text):
    """CRFNs appear as 2016000410688, CRFN2016000410688, 'CFRN ...' typos."""
    return re.findall(r"\b(\d{13})\b", str(text))


def main():
    url, key = env()
    links = sb(url, key, "decoder_lifecycle_link?select=document_id,relation,target_kind,target_ref,resolved_doc_id")
    doc_boro = {}
    for p in sb(url, key, "decoder_posting?select=document_id,bbl&limit=5000"):
        doc_boro.setdefault(p["document_id"], int(p["bbl"][0]))
    docs = sb(url, key, "decoder_document?select=document_id")
    known = {d["document_id"] for d in docs}

    # ---- route 1: CRFN / doc_id embedded in the target_ref
    wanted_crfn, wanted_docid = set(), set()
    for l in links:
        if l["resolved_doc_id"]:
            continue
        for n in crfns_in(l["target_ref"]):
            (wanted_docid if len(n) == 16 else wanted_crfn).add(n)
        for n in re.findall(r"\b(\d{16})\b", str(l["target_ref"])):
            wanted_docid.add(n)

    found = {}
    for chunk in [list(wanted_crfn)[i:i + 40] for i in range(0, len(wanted_crfn), 40)]:
        if not chunk:
            continue
        where = "crfn in(" + ",".join(f"'{c}'" for c in chunk) + ")"
        for r in socrata(where):
            found[r["crfn"]] = r
    for chunk in [list(wanted_docid)[i:i + 40] for i in range(0, len(wanted_docid), 40)]:
        if not chunk:
            continue
        where = "document_id in(" + ",".join(f"'{c}'" for c in chunk) + ")"
        for r in socrata(where):
            found[r["document_id"]] = r

    updates, unresolved = 0, []
    for l in links:
        if l["resolved_doc_id"]:
            continue
        hit = None
        for n in crfns_in(l["target_ref"]) + re.findall(r"\b(\d{16})\b", str(l["target_ref"])):
            if n in found:
                hit = found[n]
                break
        if hit:
            sb(url, key,
               "decoder_lifecycle_link?document_id=eq.%s&relation=eq.%s&target_ref=eq.%s"
               % (l["document_id"], urllib.parse.quote(l["relation"]),
                  urllib.parse.quote(str(l["target_ref"]), safe="")),
               method="PATCH", body={"resolved_doc_id": hit["document_id"]})
            updates += 1
        else:
            unresolved.append(l)

    already = sum(1 for l in links if l["resolved_doc_id"])

    # ---- route 1b: "of even date / recorded simultaneously herewith" has no
    # reference number, but the instrument it names is almost always a sibling
    # in the same recording batch. Match on what the citation calls the target.
    # (Titles lie: a Declaration is often recorded as SAGE/SMIS, a zoning-lot
    #  certification as CERT or SMIS — so each keyword maps to several codes.)
    KIND = [
        (("declaration of zoning lot", "declaration"), ("DECL", "SAGE", "SMIS")),
        (("certification", "certificate"), ("CERT", "SMIS", "SAGE")),
        (("easement",), ("EASE", "SAGE", "SMIS")),
        (("zoning lot development agreement", "zlda"), ("DEVR",)),
        (("zoning lot description",), ("ZONE",)),
    ]
    SIMULTANEOUS = ("even date", "simultaneous", "herewith", "contemporaneous")
    sib_cache = {}
    for l in links:
        if l["resolved_doc_id"] or l["target_kind"] != "date_parties":
            continue
        ref = str(l["target_ref"]).lower()
        if not any(s in ref for s in SIMULTANEOUS):
            continue
        codes = next((c for kws, c in KIND if any(k in ref for k in kws)), None)
        if not codes:
            continue
        prefix = l["document_id"][:13]
        if prefix not in sib_cache:
            sib_cache[prefix] = socrata(f"starts_with(document_id, '{prefix}')")
        cands = [s for s in sib_cache[prefix]
                 if s["doc_type"] in codes and s["document_id"] != l["document_id"]]
        # only accept an unambiguous match; ambiguity stays a finding
        if len(cands) == 1:
            sb(url, key,
               "decoder_lifecycle_link?document_id=eq.%s&relation=eq.%s&target_ref=eq.%s"
               % (l["document_id"], urllib.parse.quote(l["relation"]),
                  urllib.parse.quote(str(l["target_ref"]), safe="")),
               method="PATCH",
               body={"resolved_doc_id": cands[0]["document_id"],
                     "target_kind": "batch_sibling"})
            updates += 1
            unresolved = [u for u in unresolved if u is not l]
            print(f"  batch-resolved: {l['document_id']} -> {cands[0]['document_id']} "
                  f"({cands[0]['doc_type']}) for '{str(l['target_ref'])[:50]}'")

    # ---- route 1c: pre-2003 REEL/PAGE citations -----------------------------
    # Before CRFNs, instruments were cited by reel and page. ACRIS's master
    # dataset still carries reel_yr / reel_nbr / reel_pg, so these resolve —
    # which is what lets a lifespan reach back past 2003.
    reel_re = re.compile(r"reel\s*(\d{1,5})\s*(?:,|\s)\s*(?:liber\s*)?(?:pa?ge?\s*)?(\d{1,5})",
                         re.I)
    for l in links:
        if l["resolved_doc_id"]:
            continue
        m = reel_re.search(str(l["target_ref"]))
        if not m:
            continue
        reel, page = int(m.group(1)), int(m.group(2))
        # Reel numbers repeat across boroughs — without a borough filter the
        # same reel/page matches several instruments. Use the borough of the
        # citing document's own lots.
        boro = doc_boro.get(l["document_id"])
        where = f"reel_nbr={reel} AND reel_pg={page}"
        if boro:
            where += f" AND recorded_borough={boro}"
        try:
            hits = socrata(where)
        except Exception:
            continue
        if len(hits) == 1:
            sb(url, key,
               "decoder_lifecycle_link?document_id=eq.%s&relation=eq.%s&target_ref=eq.%s"
               % (l["document_id"], urllib.parse.quote(l["relation"]),
                  urllib.parse.quote(str(l["target_ref"]), safe="")),
               method="PATCH",
               body={"resolved_doc_id": hits[0]["document_id"], "target_kind": "reel_page"})
            updates += 1
            unresolved = [u for u in unresolved if u is not l]
            print(f"  reel-resolved: reel {reel} pg {page} -> {hits[0]['document_id']} "
                  f"({hits[0]['doc_type']}, {str(hits[0].get('recorded_datetime'))[:10]})")
        elif len(hits) > 1:
            print(f"  reel {reel} pg {page}: {len(hits)} candidates — ambiguous, left unresolved")

    print(f"citations: {len(links)} total | already resolved: {already} | "
          f"resolved this run: {updates} | still unresolved: {len(unresolved)}")
    by_kind = {}
    for l in unresolved:
        by_kind[l["target_kind"]] = by_kind.get(l["target_kind"], 0) + 1
    print("  unresolved by citation style:", by_kind)

    # ---- route 2: recording-batch siblings (the constellation)
    print("\nbatch siblings of decoded documents (the deal's other instruments):")
    for d in sorted(known):
        prefix = d[:13]
        sibs = socrata(f"starts_with(document_id, '{prefix}')")
        others = [s for s in sibs if s["document_id"] != d]
        if others:
            print(f"  {d}: " + ", ".join(
                f"{s['doc_type']}({s['document_id'][-3:]})"
                + ("*decoded" if s["document_id"] in known else "")
                for s in sorted(others, key=lambda x: x["document_id"])))
    return unresolved


if __name__ == "__main__":
    main()
