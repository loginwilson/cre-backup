"""Entities and their ROLE OVER TIME — the layer beneath contacts.

Login, 2026-08-05: *"keep the names with the entity and then we find contacts
later. It is important to also indicate their role and when. not just who it is
and party since that makes time hard to see linearly."*

That is the whole design. Three layers, same shape as the ledger:

    observation   immutable, stamped: this NAME, in this ROLE, on this LOT, on
                  this DOCUMENT, on this DATE. Never edited.
    entity        the resolved actor behind name variants. A JOIN, not an edit —
                  the observation keeps the name exactly as the document wrote it.
    timeline      computed by folding observations for an entity, or for a
                  parcel, in date order. This is what makes time linear.

A contact is a further fold ("who do I call today") and is deliberately NOT built
here: contacts age, observations do not.

WHY NORMALISATION IS CONSERVATIVE
    Merging two entities that are not the same is worse than failing to merge two
    that are: a false merge invents a relationship between sites and there is no
    way to see it afterwards. So the rules are few, each is recorded on the
    entity, and the original string is always kept:

      * case and punctuation folded
      * corporate suffixes normalised (L.L.C. -> LLC) but NOT dropped
      * a trailing parenthetical is kept as an ALIAS, not discarded —
        "301 East 71 Investors LLC (Torkian Group)" is one observation naming
        both the SPE and the sponsor behind it, and the sponsor is the more
        valuable half
    Anything beyond that (same address, same officer, similar name) is an
    inference and belongs in an enrichment step that can be reviewed, not here.
"""
import json, re, urllib.parse, urllib.request
from collections import defaultdict

ENV = r"C:/dev/acris-decoder.env"

SUFFIXES = {
    r"\bL\.?\s?L\.?\s?C\.?\b": "LLC", r"\bL\.?\s?P\.?\b": "LP",
    r"\bINC\.?\b": "INC", r"\bCORP\.?(ORATION)?\b": "CORP",
    r"\bCO\.?\b": "CO", r"\bLTD\.?\b": "LTD",
    r"\bASSOCIATES?\b": "ASSOCIATES", r"\bN\.?\s?A\.?\b": "NA",
}


def normalize(name):
    """(entity_key, alias, share) — the join key, the sponsor behind an SPE, and
    an ownership share if the document stated one.

    A trailing parenthetical is not one thing:
      "(Torkian Group)"  a SPONSOR — the SPE is disposable, the sponsor is the
                         thing worth tracking across sites
      "(70%)"            an OWNERSHIP SHARE — a fact about this party's stake,
                         not a name. Read as an alias it invented two entities
                         called "70%" and "30%".
    So they are separated by shape: a share is digits, punctuation and a percent
    sign; anything containing a letter is treated as a name.
    """
    raw = (name or "").strip()
    alias = share = None
    m = re.search(r"\(([^)]{1,60})\)\s*$", raw)
    if m:
        inner = m.group(1).strip()
        if re.fullmatch(r"[\d.,/%\s-]+", inner):
            share = inner
        else:
            alias = inner
        raw = raw[:m.start()].strip()
    key = raw.upper()
    for pat, rep in SUFFIXES.items():
        key = re.sub(pat, rep, key, flags=re.I)
    key = re.sub(r"[.,'\"]", " ", key)
    key = re.sub(r"\s+", " ", key).strip(" -")
    return key, alias, share


def _env():
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    return v["ACRIS_SUPABASE_URL"], v["ACRIS_SUPABASE_SERVICE_KEY"]


def observations():
    url, key = _env()
    q = ("decoder_posting?select=document_id,bbl,effective_date,payload,provenance"
         "&account=eq.party_observation&limit=5000")
    req = urllib.request.Request(url + "/rest/v1/" + q,
                                 headers={"apikey": key, "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=90) as f:
        rows = json.load(f)
    out = []
    for r in rows:
        p = r.get("payload") or {}
        ekey, alias, share = normalize(p.get("name"))
        out.append({
            "entity_key": ekey, "alias": alias, "share": share,
            "name_as_written": p.get("name"),
            "role": p.get("role") or p.get("label_in_doc") or "party",
            "label_in_doc": p.get("label_in_doc"),
            "bbl": r["bbl"], "date": r.get("effective_date"),
            "document_id": r["document_id"],
            "instrument": p.get("instrument"),
            "lot_as_stated": p.get("tax_lot_as_stated"),
            "lot_unresolved": bool(p.get("lot_string_unparsed")),
            "note": p.get("note")})
    return out


def entity_timelines(obs=None):
    """entity_key -> its observations in DATE ORDER. The linear view."""
    obs = obs if obs is not None else observations()
    by = defaultdict(list)
    for o in obs:
        by[o["entity_key"]].append(o)
    out = {}
    for k, rows in by.items():
        rows = sorted(rows, key=lambda r: (r["date"] or "", r["document_id"]))
        aliases = sorted({r["alias"] for r in rows if r["alias"]})
        shares = sorted({r["share"] for r in rows if r["share"]})
        names = sorted({r["name_as_written"] for r in rows})
        out[k] = {
            "entity_key": k, "aliases": aliases, "shares_stated": shares,
            "names_as_written": names,
            "first_seen": rows[0]["date"], "last_seen": rows[-1]["date"],
            "roles_over_time": [
                {"date": r["date"], "role": r["role"], "bbl": r["bbl"],
                 "document_id": r["document_id"], "instrument": r["instrument"]}
                for r in rows],
            "distinct_roles": sorted({r["role"] for r in rows}),
            "parcels": sorted({r["bbl"] for r in rows if r["bbl"] != "unknown"}),
            "documents": sorted({r["document_id"] for r in rows}),
            # an entity holding DIFFERENT roles is the interesting case: it means
            # the actor is on both sides of the market, not just a counterparty
            "role_changed": len({r["role"] for r in rows}) > 1,
            "multi_site": len({r["bbl"] for r in rows if r["bbl"] != "unknown"}) > 1}
    return out


def parcel_timelines(obs=None):
    """bbl -> who acted on it, in date order. The parcel's own party history."""
    obs = obs if obs is not None else observations()
    by = defaultdict(list)
    for o in obs:
        by[o["bbl"]].append(o)
    return {b: sorted(rows, key=lambda r: (r["date"] or "", r["document_id"]))
            for b, rows in by.items()}


if __name__ == "__main__":
    import sys
    obs = observations()
    ents = entity_timelines(obs)
    print(f"{len(obs)} party observations -> {len(ents)} entities\n")

    interesting = [e for e in ents.values() if e["multi_site"] or e["role_changed"]
                   or len(e["documents"]) > 1]
    print(f"entities appearing more than once, or in more than one role "
          f"({len(interesting)} of {len(ents)}):")
    for e in sorted(interesting, key=lambda e: (e["first_seen"] or "")):
        flags = ",".join(f for f, on in
                         (("multi-site", e["multi_site"]),
                          ("role-changed", e["role_changed"])) if on) or "repeat"
        print(f"\n  {e['entity_key'][:56]}   [{flags}]")
        if e["aliases"]:
            print(f"     sponsor/alias: {', '.join(e['aliases'])}")
        if e["shares_stated"]:
            print(f"     share stated: {', '.join(e['shares_stated'])}")
        for r in e["roles_over_time"]:
            print(f"     {r['date'] or '(undated)'}  {r['role']:<24} {r['bbl']:<12}"
                  f" {r['instrument'] or ''}  doc {r['document_id']}")

    if "--parcels" in sys.argv:
        print("\n\nparcel party history:")
        for b, rows in sorted(parcel_timelines(obs).items()):
            if len(rows) < 2:
                continue
            print(f"\n  {b}")
            for r in rows:
                print(f"     {r['date'] or '(undated)'}  {r['role']:<24} "
                      f"{r['name_as_written'][:44]}")

# ── Signature resolution ───────────────────────────────────────────────────────
# A signature is the weakest evidence of a NAME and the strongest evidence of an
# ACT. Resolve the person from a PRINTED rung, joining on (entity + title + date)
# — all three readable when the signature is not. See SIGNATURE_LADDER.md.

CONFIDENCE_ORDER = ["illegible", "handwritten_uncertain", "typed", "legible_print"]


def resolve_signatories(docs):
    """Match low-confidence signatures against printed names for the same entity.

    Returns candidates only. It never edits the transcription: a resolution is
    recorded BESIDE the original with its source, so a wrong one stays visible
    and reversible. Same rule as entity normalisation, same reason — a false
    merge invents a relationship that cannot be seen afterwards.
    """
    printed = []          # (entity_key, name, source)
    for d in docs:
        rf = d.get("raw_facts") or {}
        for n in rf.get("notices") or []:
            for who in (n.get("attention"), n.get("name")):
                if who:
                    printed.append((normalize(n.get("name"))[0], who,
                                    f"notices p{n.get('page')} of {d['document_id']}"))
        for a in rf.get("acknowledgments") or []:
            if a.get("signatory"):
                printed.append((normalize(a.get("for_entity") or "")[0], a["signatory"],
                                f"jurat p{a.get('page')} of {d['document_id']}"))
        for c in rf.get("certifications") or []:
            if c.get("name"):
                printed.append((normalize(c.get("firm") or "")[0], c["name"],
                                f"certification p{c.get('page')} of {d['document_id']}"))

    out = []
    for d in docs:
        for sb in ((d.get("raw_facts") or {}).get("signature_blocks") or []):
            conf = sb.get("name_confidence", "handwritten_uncertain")
            if conf in ("typed", "legible_print"):
                continue
            ekey = normalize(sb.get("entity"))[0]
            hits = [(n, src) for k, n, src in printed if k and k == ekey]
            out.append({"document_id": d["document_id"], "page": sb.get("page"),
                        "entity": sb.get("entity"), "title": sb.get("title"),
                        "as_written": sb.get("signatory_as_written"),
                        "confidence": conf, "candidates": hits,
                        "status": "resolved" if len(hits) == 1 else
                                  ("ambiguous" if hits else "no printed instance yet")})
    return out

# ── Counterparty profiles — the buyer/seller substrate ────────────────────────
# What a broker needs is not a list of owners, it is DEMONSTRATED BEHAVIOUR:
# which side of the trade someone takes, where, at what price, how often, and
# against what kind of counterparty. All of that folds out of party observations
# joined to the envelope postings — no new source required.

def counterparty_profiles(obs, postings):
    """entity_key -> a behavioural profile, folded from observations + postings.

    Every field is DERIVED from stamped observations, so any line can be walked
    back to a document and a page. Nothing here is inferred about a person; it is
    a record of what their entities did.
    """
    from collections import defaultdict
    by_doc = defaultdict(list)
    for p in postings:
        if p.get("account") == "envelope_transferable":
            by_doc[p["document_id"]].append(p)

    prof = defaultdict(lambda: {
        "sold": [], "bought": [], "lent_to": [], "declared": [],
        "parcels": set(), "documents": set(), "counterparties": set(),
        "first_seen": None, "last_seen": None, "names": set()})

    SIDE = {"grantor_of_rights": "sold", "recipient_of_rights": "bought",
            "consenting_mortgagee": "lent_to", "declarant": "declared"}
    for o in obs:
        e = prof[o["entity_key"]]
        e["names"].add(o["name_as_written"])
        e["documents"].add(o["document_id"])
        if o["bbl"] != "unknown":
            e["parcels"].add(o["bbl"])
        for d in (o["date"],):
            if d:
                e["first_seen"] = min(e["first_seen"] or d, d)
                e["last_seen"] = max(e["last_seen"] or d, d)
        side = SIDE.get(o["role"])
        if side:
            sf = usd = None
            for p in by_doc.get(o["document_id"], []):
                pl = p.get("payload") or {}
                if pl.get("group_quantity_sf"):
                    sf = pl["group_quantity_sf"]
                if pl.get("group_amount_usd"):
                    usd = pl["group_amount_usd"]
            e[side].append({"document_id": o["document_id"], "date": o["date"],
                            "bbl": o["bbl"], "sf": sf, "usd": usd,
                            "per_sf": round(usd / sf, 2) if (sf and usd) else None})
    # counterparties: anyone else observed on the same document
    doc_actors = defaultdict(set)
    for o in obs:
        doc_actors[o["document_id"]].add(o["entity_key"])
    out = {}
    for k, e in prof.items():
        for doc in e["documents"]:
            e["counterparties"] |= (doc_actors[doc] - {k})
        trades = e["sold"] + e["bought"]
        priced = [t["per_sf"] for t in trades if t["per_sf"]]
        out[k] = dict(e,
                      parcels=sorted(e["parcels"]), documents=sorted(e["documents"]),
                      counterparties=sorted(e["counterparties"]), names=sorted(e["names"]),
                      n_sold=len(e["sold"]), n_bought=len(e["bought"]),
                      both_sides=bool(e["sold"] and e["bought"]),
                      price_range=(min(priced), max(priced)) if priced else None)
    return out
