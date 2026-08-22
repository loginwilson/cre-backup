"""Harvest owner contacts from bty7-2jhb — the largest free contact acquisition
available to this decoder, and until now untouched.

    bty7-2jhb  Historical DOB Permit Issuance  1989-05-11 .. 2013-04-24
    scoped to DM / NB / A1 = 719,368 rows
        owner last name         96.5%
        owner full postal       96.3%
        OWNER PHONE             94.6%
        permittee phone        100.0%

⚠ THIS WRITES A PARTY REGISTRY, NOT FACTS. A permit row is an index row; under
  RULE_DOCUMENTS_NOT_INDEXES a fact needs document_id + page. Every entry here
  carries its provenance (job number, date, BBL) so it can be walked back, but
  it is a finding aid for reaching people — not a decode.

⚠ AND EVERY ENTRY IS DATED. A 1994 phone number is a LEAD, not a fact about
  today. `last_seen` is on every row for exactly that reason.
"""
import json, pathlib, re, sys, time
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk, dob, keys, development as D

OUT = pathlib.Path(__file__).with_name("party_registry.jsonl")
SEL = ("job,job_type,issuance_date,block,lot,borough,bin,"
       "owner_s_business_name,owner_s_business_type,owner_s_first_name,"
       "owner_s_last_name,owner_s_house,owner_s_house_street_name,"
       "owner_s_house_city,owner_s_house_state,owner_s_house_zip_code,"
       "owner_s_phone,permittee_s_business_name,permittee_s_phone")

# ⚠ Names are dirty in this very feed — BANBI REALTY CORP and BAMBI REALTY CORP
# are one owner. Normalisation only collapses whitespace/case/punctuation; it
# does NOT attempt fuzzy identity. That is a separate, deliberate step.
SUFFIX = re.compile(r"\b(LLC|L\.L\.C|INC|CORP|CO|LP|L\.P|LTD|COMPANY|ASSOC|"
                    r"ASSOCIATES|REALTY|PROPERTIES|GROUP|MGMT|MANAGEMENT)\b\.?", re.I)


def norm_name(s):
    s = re.sub(r"[^A-Z0-9 &]", " ", (s or "").upper())
    return re.sub(r"\s+", " ", s).strip()


def norm_phone(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d if len(d) == 10 else (d[1:] if len(d) == 11 and d[0] == "1" else "")


def harvest():
    t0 = time.time()
    reg = {}
    stats = defaultdict(int)
    for label, where in D.PERMIT_SCOPE.items():
        rows = bulk.socrata("bty7-2jhb", where=where, select=SEL)
        print(f"  {label:<12} {len(rows):>9,} rows")
        for r in rows:
            stats["rows"] += 1
            person = norm_name(f"{r.get('owner_s_first_name') or ''} "
                               f"{r.get('owner_s_last_name') or ''}")
            entity = norm_name(r.get("owner_s_business_name"))
            if entity in ("", "N A", "NA", "NONE", "OWNER", "SELF"):
                entity = ""
            if not person and not entity:
                stats["no_party"] += 1
                continue
            phone = norm_phone(r.get("owner_s_phone"))
            street = " ".join(str(x).strip() for x in
                              (r.get("owner_s_house"),
                               r.get("owner_s_house_street_name")) if x).strip()
            city = (r.get("owner_s_house_city") or "").strip()
            state = (r.get("owner_s_house_state") or "").strip()
            zipc = (r.get("owner_s_house_zip_code") or "").strip()
            key = (person, entity)
            e = reg.get(key)
            if e is None:
                e = reg[key] = {"person": person or None, "entity": entity or None,
                                "owner_type": r.get("owner_s_business_type"),
                                "phones": {}, "addresses": {}, "bbls": set(),
                                "jobs": [], "first_seen": "", "last_seen": "",
                                "job_types": defaultdict(int)}
            d = D.norm_date(r.get("issuance_date"))
            if d:
                if not e["first_seen"] or d < e["first_seen"]:
                    e["first_seen"] = d
                if d > e["last_seen"]:
                    e["last_seen"] = d
            if phone:
                e["phones"][phone] = max(e["phones"].get(phone, ""), d or "")
                stats["with_phone"] += 1
            if street:
                addr = ", ".join(x for x in (street, city, state, zipc) if x)
                e["addresses"][addr] = max(e["addresses"].get(addr, ""), d or "")
                stats["with_addr"] += 1
            e["job_types"][r.get("job_type") or "?"] += 1
            b = D._bbl_from(r, dob.PERMITS)
            if b:
                e["bbls"].add(b)
            if len(e["jobs"]) < 25:
                e["jobs"].append({"job": r.get("job"), "date": d, "bbl": b,
                                  "type": r.get("job_type")})
        del rows
    print(f"\n  distinct parties: {len(reg):,}   ({time.time()-t0:.0f}s)")
    return reg, stats


def write(reg, stats):
    spine = D.load_spine()
    n = onspine = reachable = both = 0
    with open(OUT, "w", encoding="utf-8") as f:
        for (person, entity), e in reg.items():
            bbls = sorted(e["bbls"])
            hit = [b for b in bbls if b in spine]
            rec = {
                "person": e["person"], "entity": e["entity"],
                "owner_type": e["owner_type"],
                # most recent value first — a 1994 phone is a lead, not a fact
                "phones": [p for p, _ in sorted(e["phones"].items(),
                                                key=lambda kv: kv[1], reverse=True)],
                "addresses": [a for a, _ in sorted(e["addresses"].items(),
                                                   key=lambda kv: kv[1], reverse=True)],
                "first_seen": e["first_seen"], "last_seen": e["last_seen"],
                "n_parcels": len(bbls), "parcels_on_spine": len(hit),
                "bbls": bbls[:50],
                "job_types": dict(e["job_types"]),
                "provenance": e["jobs"],
                "source": "bty7-2jhb", "kind": "party_registry_entry",
            }
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")
            n += 1
            if hit:
                onspine += 1
            if rec["phones"]:
                reachable += 1
            if rec["phones"] and rec["addresses"]:
                both += 1
    print(f"\n{'='*74}")
    print(f"  party_registry.jsonl  {n:,} parties")
    print(f"    with a phone            {reachable:>9,}  {100*reachable/n:.1f}%")
    print(f"    with phone AND address  {both:>9,}  {100*both/n:.1f}%")
    print(f"    touching a spine parcel {onspine:>9,}  {100*onspine/n:.1f}%")
    print(f"    source rows consumed    {stats['rows']:>9,}")
    return n


if __name__ == "__main__":
    reg, stats = harvest()
    write(reg, stats)
