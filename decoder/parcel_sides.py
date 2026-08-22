"""WHICH LOT SENDS AND WHICH RECEIVES — the field no document states.

    python parcel_sides.py            # resolve + report, DEVR sample
    from parcel_sides import resolve

⚠ THIS IS THE ONE GATE BETWEEN AN EVENT AND A LINEAGE. event_build.py
establishes 11 of 25 DEVR events and 0 of them are CONSERVABLE, because
conservation is "SF leaving equals SF arriving" and that is a test on PARCELS.
The ACRIS cover page lists both lots and never says which is which; the PARTIES
index gives each PARTY a side (party_type) and never mentions a lot. The link
between them is missing from every free surface, and inventing it is not an
option — direction is the single field transcription scoring cannot catch, so a
wrong guess propagates through the whole graph in silence and scores 100%.

⚠ SO IT IS ANSWERED BY WITNESSES, AND A LONE WITNESS IS NOT AN ANSWER.
Three were measured on 25 DEVR documents before any of this was built:

  OWNERSHIP    who owned the lot on the document date, from the prior DEED's
               grantee in the free index. The party who owned it carries a side,
               so the lot inherits it. PRIMARY — it is the only witness that is
               about the parcel rather than about its name.
  ADDRESS      the lot's street address against the party's name. Real, because
               these are single-purpose entities named after their buildings
               ("691 EIGHTH AVENUE CORPORATION" owns 691 8 AVENUE) — but it fired
               on only 6 of 76 parties, so it can corroborate and cannot lead.
  AIR_RIGHTS   the legals index flags lots whose air rights are at issue. Present
               on 3 of 25 documents, and on 735009 it marks FOUR of five lots —
               so it is a hint about which side, never a determination.

⚠⚠ AND THE PARCELS THEMSELVES COME FROM THE LEGALS INDEX, NOT THE COVER PAGE.
Measured: 71 parcels in legals against 46 read off the covers — the page
under-reports on 13 of 25 documents while printing "Additional Properties on
Continuation Page" on only 5 of them. The continuation flag is not a reliable
warning, so a reader trusting the page loses 35% of the parcels AND believes it
has them all. cover_claims.py built its parcel claims from the page; that was
right for provenance and wrong for population.

⚠ CONFLICT IS AN OUTPUT, NEVER A TIEBREAK. Where two witnesses disagree the
answer is CONFLICT and the parcel keeps a null side. consideration.py already
works this way for the tax stamps and the reason is the same: a resolver that
picks a side when its evidence is split has stopped measuring and started
guessing, and nothing downstream can tell the difference.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent

import bulk

LEGALS, MASTER, PARTIES = "8h5j-fqxa", "bnx9-e6tj", "636b-3b5g"
# party_type on the SOURCE document. Confirmed 13/13, 0 inverted, against the
# cover page's printed PARTY ONE / PARTY TWO (2026-08-14).
SIDE = {"1": ("sender", -1), "2": ("receiver", +1)}
# A deed's grantee is party_type 2 — the side that RECEIVES title, i.e. the owner.
DEED_TYPES = {"DEED", "DEEDO", "DEED, LE", "RDEED", "CORRD", "BRGSL", "REFER"}

ORD = {"FIRST": "1", "SECOND": "2", "THIRD": "3", "FOURTH": "4", "FIFTH": "5",
       "SIXTH": "6", "SEVENTH": "7", "EIGHTH": "8", "NINTH": "9", "TENTH": "10",
       "ELEVENTH": "11", "TWELFTH": "12"}
SUFFIX = {"STREET", "ST", "AVENUE", "AVE", "PLACE", "PL", "ROAD", "RD",
          "BOULEVARD", "BLVD", "SQUARE", "SQ", "LANE", "DRIVE", "PARKWAY",
          "TERRACE", "COURT", "NORTH", "SOUTH", "EAST", "WEST"}
NOISE = {"LLC", "INC", "CORPORATION", "CORP", "COMPANY", "CO", "LP", "LTD",
         "ASSOCIATES", "PARTNERS", "PARTNERSHIP", "REALTY", "PROPERTIES",
         "HOLDINGS", "ASSOCIATION", "TRUST", "LIMITED", "THE", "OF", "AND",
         "OWNER", "GROUP", "MANAGEMENT", "DEVELOPMENT", "LLP", "NA", "NY"}


def toks(s):
    return [ORD.get(w, w) for w in re.findall(r"[A-Z0-9]+", (s or "").upper())]


def name_key(s):
    """Tokens that actually identify an entity — suffixes carry no information."""
    return {w for w in toks(s) if w not in NOISE and len(w) > 1}


def same_entity(a, b):
    """⚠ DELIBERATELY STRICT. "509 OWNERS LLC" and "509 FIFTH LLC" share a token
    and are different companies; a loose match here silently mis-assigns a side,
    which is the failure this whole file exists to avoid."""
    ka, kb = name_key(a), name_key(b)
    if not ka or not kb:
        return False
    inter = ka & kb
    return len(inter) >= 2 or (len(inter) == 1 and min(len(ka), len(kb)) == 1)


def as_date(s):
    for f in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%m-%d-%Y"):
        try:
            return dt.datetime.strptime((s or "")[:26], f).date()
        except (ValueError, TypeError):
            continue
    return None


# ── witness 1: who owned the lot on the document date ───────────────────────
def owners_at(parcels, on_date):
    """{(boro,block,lot): [(grantee_name, deed_date, deed_id)]} — latest first.

    ⚠ ONE QUERY PER BLOCK, NOT PER LOT. 71 parcels sit on 17 blocks; querying by
    lot would be 71 round trips for the same rows. Filtering happens locally.
    """
    blocks = sorted({(p["borough"], p["block"]) for p in parcels})
    want = {(p["borough"], p["block"], p["lot"]) for p in parcels}
    on_lot = collections.defaultdict(set)
    for boro, blk in blocks:
        for r in bulk.socrata(LEGALS, where=f"borough='{boro}' and block='{blk}'",
                              select="document_id,borough,block,lot"):
            k = (r.get("borough"), r.get("block"), r.get("lot"))
            if k in want:
                on_lot[k].add(r["document_id"])

    ids = sorted({d for v in on_lot.values() for d in v})
    meta = {}
    for m in bulk.socrata_in(MASTER, "document_id", ids,
                             select="document_id,doc_type,document_date,recorded_datetime"):
        meta[m["document_id"]] = (
            (m.get("doc_type") or "").strip().upper(),
            as_date(m.get("document_date")) or as_date(m.get("recorded_datetime")))

    # only the deeds that could have conveyed title BEFORE our document
    deeds = sorted({d for d, (ty, dd) in meta.items()
                    if ty in DEED_TYPES and dd and on_date and dd <= on_date})
    grantee = collections.defaultdict(list)
    for p in bulk.socrata_in(PARTIES, "document_id", deeds,
                             select="document_id,party_type,name"):
        if str(p.get("party_type")) == "2":
            grantee[p["document_id"]].append((p.get("name") or "").upper())

    out = {}
    for k, docids in on_lot.items():
        cand = [(meta[d][1], d, n) for d in docids
                if d in grantee for n in grantee[d]]
        # ⚠ LATEST DEED WINS, AND ONLY THE LATEST. An earlier grantee is a
        # PREVIOUS owner; treating the whole history as "the owner" would let any
        # party match any lot and manufacture agreement out of nothing.
        cand.sort(reverse=True)
        if cand:
            top = cand[0][0]
            out[k] = [(n, d, dd) for dd, d, n in cand if dd == top]
    return out


# ── witness 2: the lot's address against the party's name ───────────────────
def address_match(parcel, party_name):
    at = toks(f"{parcel.get('street_number','')} {parcel.get('street_name','')}")
    if not at or not at[0].isdigit():
        return False
    nt = set(toks(party_name))
    core = [x for x in at[1:] if x not in SUFFIX]
    # the house number must match exactly, and at least one street token with it
    return at[0] in nt and (not core or bool(set(core) & nt))


def resolve(doc, parcels, parties, owners):
    """Sides for one document's parcels, with every witness recorded."""
    out = []
    for p in parcels:
        k = (p["borough"], p["block"], p["lot"])
        votes = {}

        owner_names = [n for n, _d, _dd in owners.get(k, [])]
        for name, ptype in parties:
            side = SIDE.get(str(ptype))
            if not side:
                continue
            if any(same_entity(name, o) for o in owner_names):
                votes.setdefault("ownership", set()).add(side)
            if address_match(p, name):
                votes.setdefault("address", set()).add(side)

        # ⚠ A HINT, AND FLAGGED AS ONE. air_rights='Y' marks lots whose rights
        # are at issue, which on a rights transfer is the SENDING side — but on
        # 2003041400735009 it marks four of five lots, so it can support a side
        # and must never establish one alone.
        if p.get("air_rights") == "Y":
            votes.setdefault("air_rights", set()).add(("sender", -1))

        # ⚠ A WITNESS THAT NAMES BOTH SIDES AT ONCE HAS NAMED NEITHER. Measured:
        # lot 461/2's owner is "31 COOPER INC" and the document's two parties are
        # "31 COOPER INC." and "29-31 COOPER SQUARE ASSOCIATES LLC" — which share
        # {31, COOPER}, so BOTH sides match the owner. Taking the first, or the
        # better-scoring one, would put a side on the lot that the evidence does
        # not support.
        split = {w for w, s in votes.items() if len(s) > 1}
        clean = {w: next(iter(s)) for w, s in votes.items() if len(s) == 1}
        deciding = {w: v for w, v in clean.items() if w != "air_rights"}
        sides = {v for v in deciding.values()}

        if len(sides) == 1 and deciding:
            role, sign = sides.pop()
            status = "resolved"
        elif len(sides) > 1:
            # two DIFFERENT witnesses each name a side, and they disagree
            role, sign, status = None, 0, "conflict"
        elif split:
            # ⚠ AMBIGUOUS IS NOT UNRESOLVED, AND THE TWO NEED OPPOSITE FIXES.
            # Ambiguous means a witness fired and could not discriminate — the
            # cure is better entity resolution (these are single-purpose
            # companies with overlapping names). Unresolved means nothing fired
            # at all — the cure is another witness. Collapsing them into one
            # number hides which of the two problems is actually blocking the
            # closure test.
            role, sign, status = None, 0, "ambiguous"
        else:
            role, sign, status = None, 0, "unresolved"

        out.append({
            "borough": p["borough"], "block": p["block"], "lot": p["lot"],
            "address": " ".join(f"{p.get('street_number','')} "
                                f"{p.get('street_name','')}".split()),
            "role": role, "sign": sign, "status": status,
            "established_by": "+".join(sorted(deciding)) or None,
            "witnesses": {w: v[0] for w, v in clean.items()},
            "ambiguous_witnesses": sorted(split),
            "air_rights": p.get("air_rights") == "Y",
            "owner_at_date": owner_names[:2],
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    cov = {d["doc"]: d for d in
           json.loads((HERE / "_cover_read.json").read_text(encoding="utf-8"))}
    print(f"PARCEL SIDES — {len(cov)} documents\n")

    legals = collections.defaultdict(list)
    for r in bulk.socrata_in(LEGALS, "document_id", list(cov)):
        legals[r["document_id"]].append(r)
    parties = collections.defaultdict(list)
    for r in bulk.socrata_in(PARTIES, "document_id", list(cov),
                             select="document_id,party_type,name"):
        parties[r["document_id"]].append(((r.get("name") or "").upper(),
                                          r.get("party_type")))

    n_leg = sum(len(v) for v in legals.values())
    n_cov = sum(c["lot_count"] for c in cov.values())
    print(f"  parcels from LEGALS  {n_leg}")
    print(f"  parcels from COVER   {n_cov}   "
          f"⚠ the page under-reports by {n_leg-n_cov} ({(n_leg-n_cov)/n_leg:.0%})\n")

    allp = [p for v in legals.values() for p in v]
    dates = {d: as_date(c.get("document_date")) for d, c in cov.items()}
    owners = owners_at(allp, max(x for x in dates.values() if x))

    res, per_doc = [], {}
    for d in sorted(cov):
        r = resolve(d, legals[d], parties[d], owners)
        per_doc[d] = r
        res += r

    st = collections.Counter(x["status"] for x in res)
    print("  PARCEL SIDES")
    for k in ("resolved", "conflict", "ambiguous", "unresolved"):
        print(f"    {k:<14} {st[k]:>4}/{len(res)}")
    by = collections.Counter(x["established_by"] for x in res if x["role"])
    print("\n  ESTABLISHED BY")
    for k, v in by.most_common():
        print(f"    {k:<24} {v:>4}")
    roles = collections.Counter(x["role"] for x in res if x["role"])
    print(f"\n  {dict(roles)}")

    # ⚠ THE NUMBER THAT MATTERS IS PER DOCUMENT, NOT PER PARCEL. Conservation
    # needs BOTH sides on the same instrument; a document with three resolved
    # senders and no receiver still cannot be balanced.
    ok = sum(1 for d, r in per_doc.items()
             if {x["sign"] for x in r} >= {-1, 1})
    print(f"\n  DOCUMENTS WITH BOTH SIDES (conservation can run)   {ok}/{len(cov)}")
    part = sum(1 for d, r in per_doc.items()
               if any(x["role"] for x in r) and not {x["sign"] for x in r} >= {-1, 1})
    print(f"  one side only                                     {part}/{len(cov)}")
    print(f"  no side at all                                    "
          f"{len(cov)-ok-part}/{len(cov)}")

    out = HERE / "_parcel_sides.json"
    out.write_text(json.dumps(per_doc, indent=1), encoding="utf-8")
    if a.show:
        for d in sorted(per_doc)[:6]:
            print(f"\n  {d}")
            for x in per_doc[d]:
                print(f"    blk {x['block']:>5} lot {x['lot']:>4}  "
                      f"{str(x['role'] or '-'):<9} {x['status']:<11} "
                      f"{x['address'][:26]:<28} {x['witnesses']}")
    print(f"\n  -> {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
