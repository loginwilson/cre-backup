"""FIRST PERMIT, AND FIRST PERMIT FOR THE SCOPE WORK ITSELF, per job.

⚠ "BROKE GROUND" IS THE WRONG TEST FOR HALF THE CORPUS. A conversion or an
interior enlargement never touches soil, and 215,062 of the 316,585 projects
are conversions or enlargements. Excavation is a new-build/demolition tell,
not a universal one.

The test that generalises is **work start**: the first permit authorising the
SCOPE WORK, as opposed to mobilisation and protection.

    new build     foundation · earth work · NB permit
    demolition    DM permit
    conversion    alteration · general construction
    enlargement   alteration · general construction · structural
    ---- none of these ----
    mobilisation  construction fence · sidewalk shed · scaffold · chute

A fence or a shed is pulled while the job is still in pre-development and
proves nothing about work having started. That is the whole distinction.

⚠ STREAMED. Earlier full-table pulls in this decoder died with MemoryError.
   Each page is aggregated and released; nothing accumulates except the
   per-job dict (~1M small entries).

Writes job_permits.json  ->  {job: [first_permit, first_ground, n]}
"""
import sys, json, pathlib, urllib.request, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk, dob

OUT = pathlib.Path(__file__).parent / "job_permits.json"
PAGE = 50000

# ── ipu4-2q9a (BIS era) ────────────────────────────────────────────────────
#    permit_type    NB new building · FO foundation · DM demolition
#                   AL alteration   · EQ construction equipment
#                   EW equipment work · PL plumbing · SG sign
#    permit_subtype EA earth work · FN fence · SH sidewalk shed · CH chute
GROUND_TYPE_BIS = {"NB", "FO", "DM", "AL"}
GROUND_SUB_BIS = {"EA"}
MOBILISE_SUB_BIS = {"FN", "SH", "SF", "CH"}

# ── rbx6-tga4 (DOB NOW) ────────────────────────────────────────────────────
GROUND_NOW = {"General Construction", "Structural", "Foundation", "Earth Work",
              "Protection and Mechanical Methods"}
MOBILISE_NOW = {"Sidewalk Shed", "Construction Fence", "Supported Scaffold",
                "Suspended Scaffold"}


def norm(d):
    if not d:
        return ""
    d = str(d).strip()
    if len(d) >= 10 and d[4] == "-" and d[7] == "-":
        return d[:10]
    if len(d) >= 10 and d[2] == "/" and d[5] == "/":
        return f"{d[6:10]}-{d[0:2]}-{d[3:5]}"
    return ""


def pages(ds, select):
    """$order=:id is mandatory — $offset paging without it silently drops and
    duplicates rows while the COUNT stays correct (see bulk.py)."""
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
            except Exception as e:
                if attempt == 3:
                    raise
        if not rows:
            return
        yield rows
        if len(rows) < PAGE:
            return
        off += PAGE


def bump(acc, job, date, ground):
    e = acc.get(job)
    if e is None:
        e = acc[job] = ["", "", 0]
    e[2] += 1
    if date:
        if not e[0] or date < e[0]:
            e[0] = date
        if ground and (not e[1] or date < e[1]):
            e[1] = date


def main():
    acc = {}

    n = 0
    for rows in pages(dob.PERMITS,
                      "job__,issuance_date,permit_type,permit_subtype"):
        for r in rows:
            j = (r.get("job__") or "").strip()
            if not j:
                continue
            t = (r.get("permit_type") or "").strip().upper()
            s = (r.get("permit_subtype") or "").strip().upper()
            ground = (t in GROUND_TYPE_BIS or s in GROUND_SUB_BIS) and s not in MOBILISE_SUB_BIS
            bump(acc, j, norm(r.get("issuance_date")), ground)
        n += len(rows)
        if n % 500000 < PAGE:
            print(f"   BIS permits {n:>9,}  jobs {len(acc):>9,}", flush=True)
    print(f"   BIS permits {n:>9,} rows -> {len(acc):,} jobs", flush=True)

    # ⚠ bty7-2jhb (1989-2013, 2.43M rows) is a SEPARATE permit table with the
    #   same permit_type/permit_subtype vocabulary and ISO dates. Without it,
    #   pre-2007 jobs look unpermitted and genuine construction falls back into
    #   pre-development. Its `job` column is the BIS job number, same key.
    n3 = 0
    for rows in pages(dob.HIST_PERMITS,
                      "job,issuance_date,permit_type,permit_subtype"):
        for r in rows:
            j = (r.get("job") or "").strip()
            if not j:
                continue
            t = (r.get("permit_type") or "").strip().upper()
            s = (r.get("permit_subtype") or "").strip().upper()
            ground = (t in GROUND_TYPE_BIS or s in GROUND_SUB_BIS) and s not in MOBILISE_SUB_BIS
            bump(acc, j, norm(r.get("issuance_date")), ground)
        n3 += len(rows)
        if n3 % 500000 < PAGE:
            print(f"   HIST permits {n3:>9,}  jobs {len(acc):>9,}", flush=True)
    print(f"   HIST permits {n3:>9,} rows -> {len(acc):,} jobs", flush=True)

    n2 = 0
    for rows in pages(dob.NOW_PERMITS,
                      "job_filing_number,issued_date,work_type"):
        for r in rows:
            base, _, _ = dob.now_base(r.get("job_filing_number"))
            if not base:
                continue
            w = (r.get("work_type") or "").strip()
            ground = w in GROUND_NOW
            bump(acc, base, norm(r.get("issued_date")), ground)
        n2 += len(rows)
    print(f"   NOW permits {n2:>9,} rows -> {len(acc):,} jobs total", flush=True)

    with OUT.open("w", encoding="utf-8") as f:
        json.dump(acc, f)
    withg = sum(1 for v in acc.values() if v[1])
    print(f"   wrote {OUT.name}: {len(acc):,} jobs · "
          f"{withg:,} ({withg/len(acc):.1%}) have a ground-breaking permit")


if __name__ == "__main__":
    main()
