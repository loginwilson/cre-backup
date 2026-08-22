"""PARTY x PARCEL x ROLE x TIME — involvements, not ownership.

Login, 2026-08-06:
    "if we say joe shmo is the owner of a parcel but that was in 1990, then it
     isnt relevant. or if we say billy bob the current owner was the developer
     on a project in 1980 before he even had the land, thats an issue."

⚠ THE RULE THIS FILE EXISTS TO ENFORCE
    An INVOLVEMENT is bounded by the dates of the JOB it appears on. It says:
    "this party held this role on this job on this parcel, on this date."
    It NEVER says they owned the parcel before that job, after it, or today.

    Two errors, both fatal to trust, both easy:
      1. STALE  — presenting a 1990 owner as a reachable contact for the parcel
                  now. They may be dead, and are certainly not the owner.
      2. BACK-ATTRIBUTION — crediting today's owner with a development that
                  happened before they held the land. The permit names who owned
                  it THEN; today's owner is a DIFFERENT fact from a different
                  source (ACRIS/PLUTO), and joining them by BBL alone silently
                  merges two different people into one story.

    So every row carries `role`, `job`, `date`, `stage` and the involvement is
    never widened beyond them. "Current owner" is NOT derivable here and is not
    emitted. It comes from ACRIS, and only from ACRIS.

⚠ RECENCY IS A PROPERTY OF THE ROW, NOT OF THE PARTY. `years_ago` is computed at
  write time so a consumer cannot forget to ask.
"""
import json, pathlib, sys, time
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk, dob, keys, development as D
from harvest_owners import norm_name, norm_phone

OUT = pathlib.Path(__file__).with_name("parcel_parties.jsonl")
TODAY = "2026-08-06"

# What a party's appearance on a filing actually means, per source field.
ROLE = {
    "owner_of_record": "named as owner on the filing/permit AT THAT DATE",
    "permittee": "pulled the permit — the contractor doing the work",
    "applicant_of_record": "the PE/RA who filed and sealed the application",
    "filing_representative": "the expeditor who filed on the owner's behalf",
}


def stage_for(source, row):
    """Which lifecycle stage this appearance sits at. A permit is authorisation
    to build; a filing is only intent."""
    if source == "permit":
        st = (row.get("permit_subtype") or row.get("permit_type") or "").upper()
        if st in ("FN", "SF", "EQ", "CH", "SH"):
            return "mobilisation"
        if st in ("FO", "EA"):
            return "construction_irreversible"
        return "construction"
    return "pre_development"


def years_ago(d):
    if not d or len(d) < 4:
        return None
    try:
        return round(int(TODAY[:4]) - int(d[:4]) +
                     (int(TODAY[5:7]) - int(d[5:7])) / 12.0, 1)
    except ValueError:
        return None


def emit(f, bbl, party, role, job, jobtype, date, source, stage, extra=None):
    if not bbl or not party.get("key"):
        return 0
    rec = {"bbl": bbl,
           "party": {k: party.get(k) for k in ("person", "entity", "phone",
                                               "address", "key")},
           "role": role, "role_means": ROLE[role],
           "job": job, "job_type": jobtype, "date": date,
           "stage": stage, "source": source,
           "years_ago": years_ago(date),
           # ⚠ read this before using the row for outreach
           "scope": "involvement_at_date_only__not_current_ownership"}
    if extra:
        rec.update(extra)
    f.write(json.dumps(rec, separators=(",", ":")) + "\n")
    return 1


def run():
    t0 = time.time()
    spine = D.load_spine()
    n = 0
    per_parcel = defaultdict(int)
    roles = defaultdict(int)
    with open(OUT, "w", encoding="utf-8") as f:
        # ── 1989-2013 historical permits: owner WITH contact, and permittee ──
        for label, where in D.PERMIT_SCOPE.items():
            rows = bulk.socrata("bty7-2jhb", where=where, select=(
                "job,job_type,issuance_date,block,lot,borough,permit_type,"
                "permit_subtype,owner_s_business_name,owner_s_first_name,"
                "owner_s_last_name,owner_s_house,owner_s_house_street_name,"
                "owner_s_house_city,owner_s_house_state,owner_s_house_zip_code,"
                "owner_s_phone,permittee_s_business_name,permittee_s_phone"))
            print(f"  hist/{label:<11} {len(rows):>9,}")
            for r in rows:
                b = D._bbl_from(r, dob.PERMITS)
                if b not in spine:
                    continue
                d = D.norm_date(r.get("issuance_date"))
                st = stage_for("permit", r)
                person = norm_name(f"{r.get('owner_s_first_name') or ''} "
                                   f"{r.get('owner_s_last_name') or ''}")
                entity = norm_name(r.get("owner_s_business_name"))
                addr = ", ".join(str(x).strip() for x in (
                    r.get("owner_s_house"), r.get("owner_s_house_street_name"),
                    r.get("owner_s_house_city"), r.get("owner_s_house_state"),
                    r.get("owner_s_house_zip_code")) if x)
                if person or entity:
                    n += emit(f, b, {"person": person or None,
                                     "entity": entity or None,
                                     "phone": norm_phone(r.get("owner_s_phone")) or None,
                                     "address": addr or None,
                                     "key": f"{person}|{entity}"},
                              "owner_of_record", r.get("job"), r.get("job_type"),
                              d, "bty7-2jhb", st)
                    per_parcel[b] += 1
                    roles["owner_of_record"] += 1
                pb = norm_name(r.get("permittee_s_business_name"))
                if pb:
                    n += emit(f, b, {"person": None, "entity": pb,
                                     "phone": norm_phone(r.get("permittee_s_phone")) or None,
                                     "address": None, "key": f"|{pb}"},
                              "permittee", r.get("job"), r.get("job_type"), d,
                              "bty7-2jhb", st)
                    roles["permittee"] += 1
            del rows

        # ── 2000-2025 BIS originals: owner + applicant, at FILING (intent) ──
        w = "(" + " or ".join(f"({x})" for x in D.BIS_SCOPE.values()) + ") and doc__='01'"
        rows = bulk.socrata(dob.BIS_JOBS, where=w, select=(
            "job__,job_type,pre__filing_date,block,lot,borough,"
            "owner_s_business_name,owner_s_first_name,owner_s_last_name,"
            "applicant_s_first_name,applicant_s_last_name,applicant_license__"))
        print(f"  bis originals  {len(rows):>9,}")
        for r in rows:
            b = D._bbl_from(r, dob.BIS_JOBS)
            if b not in spine:
                continue
            d = D.norm_date(r.get("pre__filing_date"))
            person = norm_name(f"{r.get('owner_s_first_name') or ''} "
                               f"{r.get('owner_s_last_name') or ''}")
            entity = norm_name(r.get("owner_s_business_name"))
            if person or entity:
                n += emit(f, b, {"person": person or None, "entity": entity or None,
                                 "phone": None, "address": None,
                                 "key": f"{person}|{entity}"},
                          "owner_of_record", r.get("job__"), r.get("job_type"), d,
                          "ic3t-wcy2", "pre_development")
                roles["owner_of_record"] += 1
                per_parcel[b] += 1
            ap = norm_name(f"{r.get('applicant_s_first_name') or ''} "
                           f"{r.get('applicant_s_last_name') or ''}")
            if ap:
                n += emit(f, b, {"person": ap, "entity": None, "phone": None,
                                 "address": None, "key": f"{ap}|"},
                          "applicant_of_record", r.get("job__"), r.get("job_type"),
                          d, "ic3t-wcy2", "pre_development",
                          {"licence": r.get("applicant_license__")})
                roles["applicant_of_record"] += 1
        del rows

        # ── 2016-now DOB NOW: owner + applicant + filing rep ──
        w = " or ".join(f"({x})" for x in D.NOW_SCOPE.values())
        rows = bulk.socrata(dob.NOW_JOBS, where=w, select=(
            "job_filing_number,job_type,filing_date,block,lot,borough,"
            "owner_s_business_name,owner_first_name,owner_last_name,"
            "applicant_first_name,applicant_last_name,applicant_business_name,"
            "filing_representative_first_name,filing_representative_last_name,"
            "filing_representative_business_name"))
        print(f"  dob now        {len(rows):>9,}")
        seen = set()
        for r in rows:
            base = dob.now_base(r.get("job_filing_number"))[0]
            b = D._bbl_from(r, dob.NOW_JOBS)
            if b not in spine or (base, b) in seen:
                continue
            seen.add((base, b))
            d = D.norm_date(r.get("filing_date"))
            person = norm_name(f"{r.get('owner_first_name') or ''} "
                               f"{r.get('owner_last_name') or ''}")
            entity = norm_name(r.get("owner_s_business_name"))
            if person or entity:
                n += emit(f, b, {"person": person or None, "entity": entity or None,
                                 "phone": None, "address": None,
                                 "key": f"{person}|{entity}"},
                          "owner_of_record", base, r.get("job_type"), d,
                          "w9ak-ipjd", "pre_development")
                roles["owner_of_record"] += 1
                per_parcel[b] += 1
            ap = norm_name(f"{r.get('applicant_first_name') or ''} "
                           f"{r.get('applicant_last_name') or ''}")
            if ap:
                n += emit(f, b, {"person": ap,
                                 "entity": norm_name(r.get("applicant_business_name")) or None,
                                 "phone": None, "address": None, "key": f"{ap}|"},
                          "applicant_of_record", base, r.get("job_type"), d,
                          "w9ak-ipjd", "pre_development")
                roles["applicant_of_record"] += 1
            fr = norm_name(f"{r.get('filing_representative_first_name') or ''} "
                           f"{r.get('filing_representative_last_name') or ''}")
            if fr:
                n += emit(f, b, {"person": fr,
                                 "entity": norm_name(r.get("filing_representative_business_name")) or None,
                                 "phone": None, "address": None, "key": f"{fr}|"},
                          "filing_representative", base, r.get("job_type"), d,
                          "w9ak-ipjd", "pre_development")
                roles["filing_representative"] += 1
        del rows

    print(f"\n{'='*74}")
    print(f"  parcel_parties.jsonl   {n:,} involvements   {len(per_parcel):,} parcels")
    print(f"  by role: {dict(roles)}   ({time.time()-t0:.0f}s)")
    return n


if __name__ == "__main__":
    run()
