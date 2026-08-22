"""FULL CONTACTS PER PROJECT — name · company · phone · email · mailing.

Not names. The five fields, or an explicit statement of which are missing and
where the missing ones live.

WHERE EACH FIELD ACTUALLY EXISTS (measured 2026-08-07, whole-table fill):

  CONTRACTOR (permittee)   ipu4-2q9a  phone 99.6% · company 99.6% · licence 93.5%
                           bty7-2jhb  phone 100%  · company 100%
  APPLICANT (architect/PE) rbx6-tga4  business address 97.3% · company 99.6%
                           w9ak-ipjd  street 99.8% · company 100% · licence
  FILING REPRESENTATIVE    w9ak-ipjd  street 78.0% · zip 78.9%
                           rbx6-tga4  company 54.0%
  OWNER                    bty7-2jhb  phone 91.7% · mailing 93.5%  ← 1989-2013 ONLY
                           everything after 2013: NO owner phone column exists

  EMAIL                    ⚠ NOT IN ANY FEED, ANY ERA. Email exists only inside
                           the documents — PW1 §2/§3 for professionals, §26 for
                           the owner. Every email in this project's output so
                           far came out of a scanned PW1.

⚠ t8hj-ruu2 (licensed professional register) is NOT a contact directory. It
  carries first/last/licence number/type/status and no address or phone, so a
  licence number cannot be resolved to a contact through it.

Writes contacts.jsonl: one row per (job, role) with a completeness score.
"""
import sys, json, pathlib, urllib.request, urllib.parse
from collections import defaultdict, Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk, dob

OUT = pathlib.Path(__file__).parent / "contacts.jsonl"
PAGE = 50000
GENERIC = {"", "n/a", "na", "none", "not applicable", "unknown", "self", "owner"}
JUNK_PHONE = {"1111111111", "8888888888", "0000000000", "9999999999",
              "1234567890", "2222222222", "5555555555", "0"}


def pages(ds, select):
    off = 0
    while True:
        p = {"$select": select, "$limit": PAGE, "$offset": off,
             "$order": ":id", "$$app_token": bulk.TOKEN}
        url = (f"https://data.cityofnewyork.us/resource/{ds}.json?"
               + urllib.parse.urlencode(p))
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=300) as f:
                    rows = json.load(f)
                break
            except Exception:
                if attempt == 3:
                    raise
        if not rows:
            return
        yield rows
        if len(rows) < PAGE:
            return
        off += PAGE


def clean(v):
    v = (v or "").strip()
    return "" if v.lower() in GENERIC else v


def phone(v):
    v = "".join(ch for ch in (v or "") if ch.isdigit())
    if len(v) != 10 or v in JUNK_PHONE or len(set(v)) <= 2:
        return ""
    return f"({v[:3]}) {v[3:6]}-{v[6:]}"


def put(store, job, role, **f):
    """Fill blanks only — the first non-empty value for a field wins, so an
    earlier permit does not get overwritten by a later blank."""
    k = (job, role)
    e = store.get(k)
    if e is None:
        e = store[k] = {"job": job, "role": role, "name": "", "company": "",
                        "phone": "", "email": "", "street": "", "city": "",
                        "state": "", "zip": "", "licence": "", "src": []}
    for a, v in f.items():
        v = (v or "").strip()
        if v and not e.get(a):
            e[a] = v
    return e


def main():
    C = {}

    # ── CONTRACTOR + OWNER, historical permits (the only owner-phone source) ──
    n = 0
    for rows in pages(dob.HIST_PERMITS,
                      "job,permittee_s_first_name,permittee_s_last_name,"
                      "permittee_s_business_name,permittee_s_phone,permittee_s_license,"
                      "owner_s_first_name,owner_s_last_name,owner_s_business_name,"
                      "owner_s_phone,owner_s_house,owner_s_house_street_name,"
                      "owner_s_house_city,owner_s_house_state,owner_s_house_zip_code"):
        for r in rows:
            j = clean(r.get("job"))
            if not j:
                continue
            nm = " ".join(x for x in (clean(r.get("permittee_s_first_name")),
                                      clean(r.get("permittee_s_last_name"))) if x)
            if nm or clean(r.get("permittee_s_business_name")):
                e = put(C, j, "contractor", name=nm,
                        company=clean(r.get("permittee_s_business_name")),
                        phone=phone(r.get("permittee_s_phone")),
                        licence=clean(r.get("permittee_s_license")))
                if "bty7-2jhb" not in e["src"]:
                    e["src"].append("bty7-2jhb")
            onm = " ".join(x for x in (clean(r.get("owner_s_first_name")),
                                       clean(r.get("owner_s_last_name"))) if x)
            if onm or clean(r.get("owner_s_business_name")):
                st = " ".join(x for x in (clean(r.get("owner_s_house")),
                                          clean(r.get("owner_s_house_street_name"))) if x)
                e = put(C, j, "owner", name=onm,
                        company=clean(r.get("owner_s_business_name")),
                        phone=phone(r.get("owner_s_phone")), street=st,
                        city=clean(r.get("owner_s_house_city")),
                        state=clean(r.get("owner_s_house_state")),
                        zip=clean(r.get("owner_s_house_zip_code")))
                if "bty7-2jhb" not in e["src"]:
                    e["src"].append("bty7-2jhb")
        n += len(rows)
    print(f"   hist permits {n:>9,} rows -> {len(C):>9,} contacts", flush=True)

    # ── CONTRACTOR, modern BIS permits (phone 99.6%, no owner phone column) ──
    n = 0
    for rows in pages(dob.PERMITS,
                      "job__,permittee_s_first_name,permittee_s_last_name,"
                      "permittee_s_business_name,permittee_s_phone__,permittee_s_license__,"
                      "owner_s_first_name,owner_s_last_name,owner_s_business_name,"
                      "owner_s_house__,owner_s_house_street_name,owner_s_zip_code,city,state"):
        for r in rows:
            j = clean(r.get("job__"))
            if not j:
                continue
            nm = " ".join(x for x in (clean(r.get("permittee_s_first_name")),
                                      clean(r.get("permittee_s_last_name"))) if x)
            if nm or clean(r.get("permittee_s_business_name")):
                e = put(C, j, "contractor", name=nm,
                        company=clean(r.get("permittee_s_business_name")),
                        phone=phone(r.get("permittee_s_phone__")),
                        licence=clean(r.get("permittee_s_license__")))
                if "ipu4-2q9a" not in e["src"]:
                    e["src"].append("ipu4-2q9a")
            onm = " ".join(x for x in (clean(r.get("owner_s_first_name")),
                                       clean(r.get("owner_s_last_name"))) if x)
            if onm or clean(r.get("owner_s_business_name")):
                st = " ".join(x for x in (clean(r.get("owner_s_house__")),
                                          clean(r.get("owner_s_house_street_name"))) if x)
                e = put(C, j, "owner", name=onm,
                        company=clean(r.get("owner_s_business_name")),
                        street=st, zip=clean(r.get("owner_s_zip_code")))
                if "ipu4-2q9a" not in e["src"]:
                    e["src"].append("ipu4-2q9a")
        n += len(rows)
    print(f"   BIS permits  {n:>9,} rows -> {len(C):>9,} contacts", flush=True)

    # ── APPLICANT + FILING REP, DOB NOW permits (applicant address 97.3%) ──
    n = 0
    for rows in pages(dob.NOW_PERMITS,
                      "job_filing_number,applicant_first_name,applicant_last_name,"
                      "applicant_business_name,applicant_business_address,applicant_license,"
                      "filing_representative_first_name,filing_representative_last_name,"
                      "filing_representative_business_name,owner_name,owner_business_name"):
        for r in rows:
            base, _, _ = dob.now_base(r.get("job_filing_number"))
            if not base:
                continue
            nm = " ".join(x for x in (clean(r.get("applicant_first_name")),
                                      clean(r.get("applicant_last_name"))) if x)
            if nm or clean(r.get("applicant_business_name")):
                e = put(C, base, "applicant", name=nm,
                        company=clean(r.get("applicant_business_name")),
                        street=clean(r.get("applicant_business_address")),
                        licence=clean(r.get("applicant_license")))
                if "rbx6-tga4" not in e["src"]:
                    e["src"].append("rbx6-tga4")
            rnm = " ".join(x for x in (clean(r.get("filing_representative_first_name")),
                                       clean(r.get("filing_representative_last_name"))) if x)
            if rnm or clean(r.get("filing_representative_business_name")):
                e = put(C, base, "filing_rep", name=rnm,
                        company=clean(r.get("filing_representative_business_name")))
                if "rbx6-tga4" not in e["src"]:
                    e["src"].append("rbx6-tga4")
            if clean(r.get("owner_name")) or clean(r.get("owner_business_name")):
                e = put(C, base, "owner", name=clean(r.get("owner_name")),
                        company=clean(r.get("owner_business_name")))
                if "rbx6-tga4" not in e["src"]:
                    e["src"].append("rbx6-tga4")
        n += len(rows)
    print(f"   NOW permits  {n:>9,} rows -> {len(C):>9,} contacts", flush=True)

    # ── FILING REP mailing + APPLICANT, DOB NOW jobs ──────────────────────
    n = 0
    for rows in pages(dob.NOW_JOBS,
                      "job_filing_number,applicant_first_name,applicant_last_name,"
                      "applicant_business_name,applicant_street_name,applicant_license,"
                      "filing_representative_first_name,filing_representative_last_name,"
                      "filing_representative_business_name,filing_representative_street_name,"
                      "filing_representative_city,filing_representative_state,"
                      "filing_representative_zip,owner_first_name,owner_last_name,"
                      "owner_s_business_name"):
        for r in rows:
            base, _, _ = dob.now_base(r.get("job_filing_number"))
            if not base:
                continue
            nm = " ".join(x for x in (clean(r.get("applicant_first_name")),
                                      clean(r.get("applicant_last_name"))) if x)
            if nm:
                e = put(C, base, "applicant", name=nm,
                        company=clean(r.get("applicant_business_name")),
                        street=clean(r.get("applicant_street_name")),
                        licence=clean(r.get("applicant_license")))
                if "w9ak-ipjd" not in e["src"]:
                    e["src"].append("w9ak-ipjd")
            rnm = " ".join(x for x in (clean(r.get("filing_representative_first_name")),
                                       clean(r.get("filing_representative_last_name"))) if x)
            if rnm or clean(r.get("filing_representative_business_name")):
                e = put(C, base, "filing_rep", name=rnm,
                        company=clean(r.get("filing_representative_business_name")),
                        street=clean(r.get("filing_representative_street_name")),
                        city=clean(r.get("filing_representative_city")),
                        state=clean(r.get("filing_representative_state")),
                        zip=clean(r.get("filing_representative_zip")))
                if "w9ak-ipjd" not in e["src"]:
                    e["src"].append("w9ak-ipjd")
            onm = " ".join(x for x in (clean(r.get("owner_first_name")),
                                       clean(r.get("owner_last_name"))) if x)
            if onm or clean(r.get("owner_s_business_name")):
                e = put(C, base, "owner", name=onm,
                        company=clean(r.get("owner_s_business_name")))
                if "w9ak-ipjd" not in e["src"]:
                    e["src"].append("w9ak-ipjd")
        n += len(rows)
    print(f"   NOW jobs     {n:>9,} rows -> {len(C):>9,} contacts", flush=True)

    # ── score and write ───────────────────────────────────────────────────
    jobs = set()
    for line in (pathlib.Path(__file__).parent / "projects.jsonl").open(encoding="utf-8"):
        jobs.add(json.loads(line)["job"])

    have = Counter(); full = Counter(); onproj = Counter(); fieldfill = defaultdict(Counter)
    with OUT.open("w", encoding="utf-8") as fh:
        for (job, role), e in C.items():
            mail = ", ".join(x for x in (e["street"], e["city"], e["state"], e["zip"]) if x)
            e["mailing"] = mail
            got = [bool(e["name"] or e["company"]), bool(e["company"]),
                   bool(e["phone"]), bool(e["email"]), bool(mail)]
            e["completeness"] = sum(got)
            e["missing"] = [k for k, v in (("phone", e["phone"]), ("email", e["email"]),
                                           ("mailing", mail)) if not v]
            have[role] += 1
            for f in ("name", "company", "phone", "email", "mailing"):
                if (e[f] if f != "mailing" else mail):
                    fieldfill[role][f] += 1
            if e["completeness"] >= 4:
                full[role] += 1
            if job in jobs:
                onproj[role] += 1
                fh.write(json.dumps(e) + "\n")

    print()
    print("=" * 84)
    print(f"CONTACTS on the {len(jobs):,} batched projects   ->  {OUT.name}")
    print("=" * 84)
    print(f"{'role':<14}{'contacts':>10}{'name':>9}{'company':>9}{'phone':>9}"
          f"{'email':>8}{'mailing':>9}{'4+ of 5':>9}")
    for role in ("owner", "contractor", "applicant", "filing_rep"):
        h = have[role]
        if not h:
            continue
        ff = fieldfill[role]
        print(f"{role:<14}{onproj[role]:>10,}"
              + "".join(f"{ff[f]/h:>8.0%}" + (" " if f != "mailing" else "")
                        for f in ("name", "company", "phone", "email", "mailing"))
              + f"{full[role]/h:>9.0%}")
    print()
    print("⚠ email is 0% everywhere — it exists in NO DOB feed, any era.")
    print("  It lives only in the documents: PW1 §2/§3 (professionals), §26 (owner).")


if __name__ == "__main__":
    main()
