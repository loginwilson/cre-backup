"""CROSS-ERA PARTY RESOLUTION — give the modern era its missing reach.

The gap, measured:
    2016+ DOB NOW   owner NAME + ROLE + entity        no phone, no address
    1989-2013       owner name + address + PHONE      94.6% of 719,368 rows

A developer filing in 2022 almost certainly filed before 2013 too. So resolve
the NOW-era party against the contact-bearing era and inherit the reach.

⚠ THE KEY IS A NAME — the worst key there is (DECODER_CHATS.md, and the DOS
  chat learned it the hard way). Therefore:
    * EXACT / MULTIPLE / NONE, always. Never silently take the first match.
    * MULTIPLE is reported as ambiguous and NOT resolved. Two different phone
      numbers for one name is not a contact, it is a coin toss.
    * every resolution carries the match class, the evidence, and the DATE of
      the contact. A 1994 phone is a LEAD; `contact_age_years` says so.
⚠ AND A MATCH IS NOT AN IDENTITY. `BANBI` and `BAMBI REALTY CORP` are one owner
  and will NOT match here. This resolver is deliberately exact-only; fuzzy
  clustering is a separate, reviewable step, not something to bury in a join.
"""
import json, pathlib, sys, time
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
IN = pathlib.Path(__file__).with_name("parcel_parties.jsonl")
OUT = pathlib.Path(__file__).with_name("resolved_owner_contacts.jsonl")

CONTACT_SRC = "bty7-2jhb"          # the only source carrying owner phone/address
MODERN = ("w9ak-ipjd", "ic3t-wcy2")  # identity only


MAX_PHONES = 24          # a key with more than this is not an identity anyway


def _add(idx, key, phone, address, date, bbl, job):
    """Collapse at insert. Storing every appearance is a MemoryError at 719k
    rows x 3 indexes; per key we only ever need the distinct phones, the most
    recent record for each, and the set of parcels it was seen on."""
    e = idx.get(key)
    if e is None:
        e = idx[key] = {"ph": {}, "bbls": set()}
    if bbl:
        if len(e["bbls"]) < 200:
            e["bbls"].add(bbl)
    if not phone:
        return
    cur = e["ph"].get(phone)
    if cur is None:
        if len(e["ph"]) >= MAX_PHONES:
            return
        e["ph"][phone] = (date or "", address or "", bbl or "", job or "")
    elif (date or "") > cur[0]:
        e["ph"][phone] = (date or "", address or "", bbl or "", job or "")


def load():
    """One pass. Contact-bearing appearances -> collapsed index; modern -> targets."""
    by_pe, by_e, by_p = {}, {}, {}
    targets = []
    seen_target = set()
    n = 0
    with open(IN, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            n += 1
            if r["role"] != "owner_of_record":
                continue
            p = r["party"]
            person, entity = p.get("person"), p.get("entity")
            if r["source"] == CONTACT_SRC and (p.get("phone") or p.get("address")):
                a = (p.get("phone"), p.get("address"), r["date"], r["bbl"], r["job"])
                if person and entity:
                    _add(by_pe, (person, entity), *a)
                if entity:
                    _add(by_e, entity, *a)
                if person:
                    _add(by_p, person, *a)
            elif r["source"] in MODERN:
                k = (person, entity, r["bbl"], r["job"])
                if k in seen_target:
                    continue
                seen_target.add(k)
                targets.append({"bbl": r["bbl"], "job": r["job"],
                                "job_type": r["job_type"], "date": r["date"],
                                "source": r["source"],
                                "person": person, "entity": entity})
    return by_pe, by_e, by_p, targets, n


def pick(e, bbl):
    """EXACT / MULTIPLE / NONE. Ambiguity is reported, never resolved away."""
    if not e or not e["ph"]:
        return None, "none"
    same_parcel = bbl in e["bbls"]
    items = [(ph, d, addr, b, j) for ph, (d, addr, b, j) in e["ph"].items()]
    if len(items) > 1:
        # ⚠ several distinct phones behind one name. If exactly one of them was
        # recorded on THIS PARCEL that is corroboration, not a guess.
        onlot = [t for t in items if t[3] == bbl]
        if len(onlot) == 1:
            ph, d, addr, b, j = onlot[0]
            return {"phone": ph, "address": addr, "date": d, "bbl": b,
                    "job": j}, "multiple_resolved_by_same_parcel"
        return None, "multiple_ambiguous"
    ph, d, addr, b, j = items[0]
    return ({"phone": ph, "address": addr, "date": d, "bbl": b, "job": j},
            "exact_same_parcel" if same_parcel else "exact")


def run():
    t0 = time.time()
    by_pe, by_e, by_p, targets, total = load()
    print(f"  involvements read        {total:>10,}")
    print(f"  contact-bearing keys     person+entity {len(by_pe):>8,} · "
          f"entity {len(by_e):>8,} · person {len(by_p):>8,}")
    print(f"  modern owner targets     {len(targets):>10,}\n")

    stats = defaultdict(int)
    n = 0
    with open(OUT, "w", encoding="utf-8") as f:
        for r in targets:
            person, entity, bbl = r["person"], r["entity"], r["bbl"]
            hit, cls, via = None, "none", None
            for via_name, e in (("person+entity", by_pe.get((person, entity)) if person and entity else None),
                                ("entity", by_e.get(entity) if entity else None),
                                ("person", by_p.get(person) if person else None)):
                hit, cls = pick(e, bbl)
                if hit or cls == "multiple_ambiguous":
                    via = via_name
                    break
            stats[cls] += 1
            if via:
                stats[f"via_{via}"] += 1
            if not hit:
                continue
            age = None
            if hit["date"] and r["date"]:
                try:
                    age = int(r["date"][:4]) - int(hit["date"][:4])
                except ValueError:
                    pass
            f.write(json.dumps({
                "bbl": bbl, "job": r["job"], "job_type": r["job_type"],
                "filed": r["date"], "source_modern": r["source"],
                "owner_person": person, "owner_entity": entity,
                "resolved_phone": hit["phone"], "resolved_address": hit["address"],
                "match_class": cls, "matched_via": via,
                "evidence": {"job": hit["job"], "bbl": hit["bbl"],
                             "date": hit["date"], "source": CONTACT_SRC},
                "contact_age_years": age,
                "scope": "contact_inherited_from_a_prior_filing__verify_before_use",
            }, separators=(",", ":")) + "\n")
            n += 1
    print("=" * 74)
    print(f"  resolved_owner_contacts.jsonl   {n:,} resolutions")
    tot = len(targets)
    for k in ("exact_same_parcel", "exact", "multiple_resolved_by_same_parcel",
              "multiple_ambiguous", "none"):
        print(f"    {k:<34}{stats[k]:>9,}  {100*stats[k]/tot:>5.1f}%")
    print(f"    matched via: person+entity {stats['via_person+entity']:,} · "
          f"entity {stats['via_entity']:,} · person {stats['via_person']:,}")
    print(f"  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    run()
