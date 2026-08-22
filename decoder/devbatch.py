"""BATCH THE FOUR TYPES, THEN ASSIGN TO THE SPINE.

The inversion that makes this population-scale: do NOT walk the spine calling
services per parcel. Pull demolition / new build / conversion / enlargement
wholesale from every development service, derive each project's stage, and
assign the result to its parcel.

Two populations come out of one pass:
  COMPLETE   — reached operation. History is final; decode once, never re-check.
  ACTIVE     — pre_development | construction | temporary_operation | stalled.
               These are the monitoring set: their stage will change.

Run:  python devbatch.py            -> projects.jsonl + a printed report
      python devbatch.py --sample   -> Queens only, for a fast loop
"""
import sys, json, pathlib, urllib.request, urllib.parse
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk, dob, keys

OUT = pathlib.Path(__file__).parent / "projects.jsonl"

# ── ⚠ bulk.socrata mishandles $group (sends $offset alongside it and 400s).
#    Grouped/aggregate queries go through this direct helper instead.
def q(ds, **p):
    p["$$app_token"] = bulk.TOKEN
    p.setdefault("$limit", 50000)
    prm = {(k if k.startswith("$") else "$" + k): v for k, v in p.items()}
    url = f"https://data.cityofnewyork.us/resource/{ds}.json?" + urllib.parse.urlencode(prm)
    with urllib.request.urlopen(url, timeout=300) as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════════════════
# SCOPE — the four types, in each system's own vocabulary.
#
# ⚠ ENLARGEMENT IS A FIELD, NOT A JOB TYPE (see dob.SCOPE_BIS). It rides on
#   A1/A2/A3, so a job can carry TWO scopes. Scope is a SET, never one value.
# ═══════════════════════════════════════════════════════════════════════════
BIS_SCOPE = {
    "demolition":  "job_type='DM'",
    "new_build":   "job_type='NB'",
    "conversion":  "job_type='A1'",
    "enlargement": "enlargement_sq_footage > 0",
}
NOW_SCOPE = {
    "demolition":  "job_type='Full Demolition'",
    "new_build":   ("job_type in('New Building',"
                    "'ALT-CO - New Building with Existing Elements to Remain')"),
    "conversion":  "job_type in('Alteration CO','No Work')",
    "enlargement": "upper(job_description) like '%ENLARG%'",
}

# ═══════════════════════════════════════════════════════════════════════════
# STAGE — measured vocabularies, 2026-08-07. Every status observed is mapped;
# an unmapped status must surface as 'unknown', never default to a stage.
# ═══════════════════════════════════════════════════════════════════════════
BIS_STAGE = {
    "SIGNED OFF":                             "operation",
    "PERMIT ISSUED - ENTIRE JOB/WORK":        "construction",
    "PERMIT ISSUED - PARTIAL JOB":            "construction",
    "PLAN EXAM - APPROVED":                   "pre_development",
    "PLAN EXAM - DISAPPROVED":                "pre_development",
    "PLAN EXAM - IN PROCESS":                 "pre_development",
    "PLAN EXAM - PARTIAL APPROVAL":           "pre_development",
    "PRE-FILING":                             "pre_development",
    "APPLICATION PROCESSED - ENTIRE":         "pre_development",
    "APPLICATION PROCESSED - NO PLAN EXAM":   "pre_development",
    "APPLICATION PROCESSED-PART-NO PAYMENT":  "pre_development",
    "APPLICATION PROCESSED - PAYMENT ONLY":   "pre_development",
    "APPLICATION ASSIGNED TO PLAN EXAMINER":  "pre_development",
    "SUSPENDED":                              "stalled",
    "WITHDRAWN":                              "withdrawn",
}
NOW_STAGE = {
    "CO Issued":                              "temporary_operation",
    "Permit Entire":                          "construction",
    "Permit Issued":                          "construction",
    "LOC Issued":                             "operation",     # letter of completion
    "Approved":                               "pre_development",
    "Objections":                             "pre_development",
    "Plan Examiner Review":                   "pre_development",
    "Pending Plan Examiner Assignment":       "pre_development",
    "Chief Plan Examiner/ Assistant Chief Plan Examiner Review": "pre_development",
    "SO Plan Examiner Review":                "pre_development",
    "Prof Cert QA Review":                    "pre_development",
    "Awaiting Energy Approval":               "pre_development",
    "Incomplete":                             "pre_development",
    "Filing Withdrawn":                       "withdrawn",
    # ⚠ These four were UNMAPPED on the first run and fell to 'unknown' —
    #   11,943 projects, 91% of all unknowns, and they are OPERATING.
    "TA Certificate of Operation Issued":     "operation",
    "PA Certificate of Operation Issued":     "operation",
    "Full Demolition Signed-off":             "operation",
    "PAA Approved":                           "pre_development",
    "On Hold – Administrative Action":        "stalled",   # en-dash
    "On Hold - Pending Supersede of Applicant of Record": "stalled",
    "On Hold  - Applicant Supersede Request Required":    "stalled",
    "OnHold-NoGoodCheck":                     "stalled",
    "QA Failed":                              "pre_development",
    "Pending CPE/ACPE Assignment":            "pre_development",
    "Pending Prof Cert QA Assignment":        "pre_development",
}
ACTIVE = {"pre_development", "construction", "temporary_operation", "stalled"}

# ⚠ 'SIGNED OFF' / 'LOC Issued' mean the JOB closed, NOT that a certificate of
#   occupancy exists. The CO layers below are what separate temporary_operation
#   from operation. Where a CO is found it OVERRIDES the status-derived stage.


def norm(d):
    """'05/30/2014' | '2014-05-30T00:00:00' -> '2014-05-30'. Never half-parse.

    ⚠ REGRESSION I SHIPPED AND HAD ALREADY FIXED ONCE. pkdm-hqz6 writes
      '07/09/25 9:41:42 AM' — a TWO-DIGIT year followed by a time. The naive
      rule (d[2]=='/' and d[5]=='/' -> year = d[6:10]) reads the year as
      '25 9' and emits '25 9-07-09'. 9,989 of 61,510 certificate dates (16.2%)
      came out corrupt, and they sorted as year 25 AD, which is why the
      temporary_operation p75 read 730,926 days.

      A half-parsed date is worse than no date: it survives every downstream
      check and poisons every duration it touches. Return '' instead.
    """
    if not d:
        return ""
    d = str(d).strip()
    if len(d) >= 10 and d[4] == "-" and d[7] == "-":
        return d[:10] if d[:4].isdigit() else ""
    if len(d) >= 8 and d[2] == "/" and d[5] == "/":
        mo, dy, y = d[0:2], d[3:5], d[6:10]
        if not (mo.isdigit() and dy.isdigit()):
            return ""
        if y.isdigit() and len(y) == 4:
            return f"{y}-{mo}-{dy}"
        # ⚠ 'MM/DD/YY hh:mm:ss AM' — pkdm-hqz6 writes a TWO-DIGIT year. The
        #   century is not a guess here: that feed begins in 2016 and the BIS
        #   CO feed in 2012, so 00-30 can only mean 20xx. Bounded to that
        #   window; anything outside it is refused rather than assumed.
        yy = d[6:8]
        if yy.isdigit() and 0 <= int(yy) <= 30:
            return f"20{yy}-{mo}-{dy}"
        return ""
    return ""


def bbl_of(row, boro_key="borough"):
    try:
        return keys.bbl(row.get(boro_key), row.get("block"), row.get("lot"))
    except Exception:
        return None


def pull_bis():
    """BIS originals only (doc 01). Amendments restate nothing."""
    proj = {}
    cols = ("job__,doc__,job_type,borough,block,lot,pre__filing_date,latest_action_date,"
            "signoff_date,job_status_descrp,job_description,owner_s_first_name,"
            "owner_s_last_name,owner_s_business_name,enlargement_sq_footage,"
            "proposed_dwelling_units,proposed_no_of_stories,proposed_height,"
            "applicant_s_first_name,applicant_s_last_name,applicant_professional_title")
    for scope, where in BIS_SCOPE.items():
        rows = bulk.socrata(dob.BIS_JOBS, where=f"doc__='01' and ({where})", select=cols)
        print(f"   BIS {scope:<12}{len(rows):>9,} rows", flush=True)
        for r in rows:
            j = r.get("job__")
            if not j:
                continue
            p = proj.get(j)
            if p is None:
                b = bbl_of(r)
                p = proj[j] = {
                    "job": j, "system": "BIS", "bbl": b, "scope": [],
                    "filed": norm(r.get("pre__filing_date")),
                    "last_action": norm(r.get("latest_action_date")),
                    "signoff": norm(r.get("signoff_date")),
                    "status": r.get("job_status_descrp"),
                    "desc": (r.get("job_description") or "")[:160],
                    "units": r.get("proposed_dwelling_units"),
                    "stories": r.get("proposed_no_of_stories"),
                    "height": r.get("proposed_height"),
                    "owner_name": " ".join(x for x in (r.get("owner_s_first_name"),
                                                        r.get("owner_s_last_name")) if x).strip(),
                    "owner_entity": (r.get("owner_s_business_name") or "").strip(),
                }
            if scope not in p["scope"]:
                p["scope"].append(scope)
        del rows
    return proj


def pull_now():
    """DOB NOW. Filings collapse to jobs on the FIRST dash (dob.now_base)."""
    proj = {}
    cols = ("job_filing_number,job_type,borough,block,lot,filing_date,approved_date,"
            "first_permit_date,current_status_date,filing_status,job_description,"
            "owner_first_name,owner_last_name,owner_s_business_name,"
            "proposed_dwelling_units,proposed_no_of_stories,proposed_height,"
            "applicant_first_name,applicant_last_name,applicant_business_name,"
            "filing_representative_business_name")
    for scope, where in NOW_SCOPE.items():
        rows = bulk.socrata(dob.NOW_JOBS, where=where, select=cols)
        print(f"   NOW {scope:<12}{len(rows):>9,} filings", flush=True)
        for r in rows:
            base, letter, seq = dob.now_base(r.get("job_filing_number"))
            if not base:
                continue
            p = proj.get(base)
            if p is None:
                p = proj[base] = {
                    "job": base, "system": "NOW", "bbl": bbl_of(r), "scope": [],
                    "filed": "", "approved": "", "first_permit": "",
                    "status": None, "status_date": "", "desc": "",
                    "units": None, "stories": None, "height": None,
                    "owner_name": "", "owner_entity": "",
                    "applicant": "", "filing_rep": "", "_n": 0,
                }
            p["_n"] += 1
            fd = norm(r.get("filing_date"))
            if fd and (not p["filed"] or fd < p["filed"]):
                p["filed"] = fd                       # earliest filing = the initial
            for k, col in (("approved", "approved_date"), ("first_permit", "first_permit_date")):
                v = norm(r.get(col))
                if v and (not p[k] or v < p[k]):
                    p[k] = v
            sd = norm(r.get("current_status_date"))
            if sd >= p["status_date"]:                # latest status wins
                p["status_date"], p["status"] = sd, r.get("filing_status")
            for k, col in (("owner_entity", "owner_s_business_name"),
                           ("applicant", "applicant_business_name"),
                           ("filing_rep", "filing_representative_business_name")):
                v = (r.get(col) or "").strip()
                if v and v != "Not Applicable" and not p[k]:
                    p[k] = v
            nm = " ".join(x for x in (r.get("owner_first_name"), r.get("owner_last_name")) if x).strip()
            if nm and not p["owner_name"]:
                p["owner_name"] = nm
            if not p["desc"]:
                p["desc"] = (r.get("job_description") or "")[:160]
            for f, v in (("units", "proposed_dwelling_units"), ("stories", "proposed_no_of_stories"),
                         ("height", "proposed_height")):
                if p[f] in (None, "") and r.get(v):
                    p[f] = r.get(v)
            if scope not in p["scope"]:
                p["scope"].append(scope)
        del rows
    return proj


def pull_co():
    """Certificates, keyed BY JOB — not by parcel.

    ★ Both feeds carry a job number at 100%, so a certificate attaches to the
      project that earned it. Keying by parcel (the first version) hands a new
      tower the CO of the building it replaced.

    ★ Both feeds publish temp-vs-final, in different words:
        bs8b-p36w  issue_type            Temporary 93,810 · Final 49,254
        pkdm-hqz6  c_of_o_filing_type    Final 18,750 · Initial 8,776 ·
                                         Renewal Without Change 46,134 ·
                                         Renewal With Change 6,511
      Anything that is not 'Final' is a TCO — which is why the Skyline card
      reads temporary operation off eight Initial/Renewal records.
    """
    co = defaultdict(lambda: {"first": "", "last": "", "n": 0,
                              "tco": False, "final": "", "final_seen": False})
    src = ((dob.CO,     "job_number",       "c_o_issue_date",       "issue_type"),
           (dob.CO_NOW, "job_filing_name",  "c_of_o_issuance_date", "c_of_o_filing_type"))
    for ds, jcol, dcol, tcol in src:
        rows = bulk.socrata(ds, select=f"{jcol},{dcol},{tcol}")
        print(f"   CO  {ds:<12}{len(rows):>9,} rows", flush=True)
        for r in rows:
            j = (r.get(jcol) or "").strip()
            if not j:
                continue
            base, _, _ = dob.now_base(j) if j[:1].isalpha() else (j, "", 0)
            key = base if j[:1].isalpha() else j
            d = norm(r.get(dcol))
            ft = (r.get(tcol) or "")
            e = co[key]
            e["n"] += 1
            if d and (not e["first"] or d < e["first"]):
                e["first"] = d
            if d > e["last"]:
                e["last"] = d
            if "Final" in ft:
                e["final_seen"] = True
                if d and (not e["final"] or d < e["final"]):
                    e["final"] = d
            else:
                e["tco"] = True
        del rows
    return co


# ═══════════════════════════════════════════════════════════════════════════
# THE LADDER — four stages, each defined by EVIDENCE, not by a status string.
#
#   pre_development      filed. Demolition or new build on record, but nothing
#                        has broken ground — no work permit issued.
#   construction         a work permit was issued. Ground is broken and the
#                        filings support active work.
#   temporary_operation  a TCO exists.
#   operation            a FINAL certificate of occupancy exists.
#
# Stalled / abandoned are NOT stages. They are recency judgements over `last`,
# left to the caller as an adjustable filter.
# ═══════════════════════════════════════════════════════════════════════════
BIS_PERMITTED = {"PERMIT ISSUED - ENTIRE JOB/WORK", "PERMIT ISSUED - PARTIAL JOB",
                 "SIGNED OFF"}          # signed off REQUIRES a permit to have existed
NOW_PERMITTED = {"Permit Entire", "Permit Issued", "CO Issued", "LOC Issued",
                 "Full Demolition Signed-off",
                 "TA Certificate of Operation Issued", "PA Certificate of Operation Issued"}


PERMITS = {}          # job -> [first_permit, first_ground, n]  (permit_phase.py)


def stage4(p, co):
    """Returns (stage, entered_on). Evidence beats status at every rung."""
    # ★ WORK START is a permit fact, not a status string. A fence / shed /
    #   scaffold permit is MOBILISATION — pulled while the job is still in
    #   pre-development. Foundation, earth work, structural, general
    #   construction, NB / DM / AL are the scope work itself.
    #
    # ⚠ THIS LOOKUP USED TO SIT BELOW THE CERTIFICATE BRANCH. Every project
    #   that reached a CO returned early, so first_ground was never written for
    #   any of the 61,510 certificate-stage projects — and the work-start ->
    #   certificate phase, the one a developer actually cares about, computed
    #   over ZERO rows and silently printed nothing.
    pm = PERMITS.get(p.get("job"))
    p["first_permit_any"] = pm[0] if pm else ""
    p["first_ground"] = pm[1] if pm else ""

    c = co.get(p.get("job"))
    if c:
        if c["final_seen"]:
            return "operation", c["final"]
        if c["tco"]:
            return "temporary_operation", c["first"]
    st = (p.get("status") or "").strip()
    closed = st in ("SIGNED OFF", "LOC Issued", "Full Demolition Signed-off")

    if pm and pm[1]:
        broke, when = True, pm[1]
    elif p["system"] == "BIS":
        broke = st in BIS_PERMITTED
        when = (pm[0] if pm else "") or p.get("signoff") or ""
    else:
        broke = bool(p.get("first_permit")) or st in NOW_PERMITTED
        when = (pm[0] if pm else "") or p.get("first_permit") or ""

    # ⚠ ONLY ~19% OF SCOPE-BEARING JOBS EVER PRODUCE A CERTIFICATE. Most
    #   conversions and enlargements, and EVERY demolition, close without one.
    #   For those, sign-off is the terminal state — not construction. Mapping
    #   them onto the CO ladder put 188,155 finished jobs in 'construction'.
    if closed and not c:
        if "demolition" in p["scope"]:
            # A finished demolition is not an operating building. It is a
            # CLEARED SITE — the pre-development event of whatever comes next.
            return "site_cleared", when or p.get("last_action") or ""
        return "complete", when or p.get("last_action") or ""
    if broke:
        return "construction", when
    return "pre_development", p.get("filed") or ""


def stage_of(p, co):
    """Status maps to a stage; a CERTIFICATE overrides it. Unmapped -> unknown."""
    tbl = BIS_STAGE if p["system"] == "BIS" else NOW_STAGE
    st = tbl.get((p.get("status") or "").strip(), "unknown")
    c = co.get(p.get("bbl"))
    if c and c["n"] and p.get("filed") and c["last"] >= p["filed"]:
        # A certificate exists on this parcel AND post-dates the filing —
        # otherwise it belongs to the building this project replaced.
        if st in ("operation", "construction", "temporary_operation"):
            # Only pkdm-hqz6 states temp vs final. Where it does not (BIS era),
            # say so rather than guessing a final CO into existence.
            st = "operation" if (c["final"] or not c["typed"]) else "temporary_operation"

    last = p["last"] = max((x for x in (p.get("last_action", ""), p.get("status_date", ""),
                                        p.get("first_permit", ""), p.get("filed", "")) if x),
                           default="")
    # ⚠ STALLED vs ABANDONED. The first run called anything pre-development and
    #   quiet for 3 years "stalled", which swept 48,313 filings from the 2000s
    #   into the monitoring set and inflated ACTIVE roughly 3x. A 2003 filing
    #   that never got a permit is not a project to watch — it is dead.
    if st == "pre_development" and last:
        if last < "2021-01-01":
            st = "abandoned"
        elif last < "2023-08-07":
            st = "stalled"
    return st


def main():
    sample = "--sample" in sys.argv
    pf = pathlib.Path(__file__).parent / "job_permits.json"
    if pf.exists():
        global PERMITS
        PERMITS = json.loads(pf.read_text(encoding="utf-8"))
        print(f"PERMIT PHASE cache: {len(PERMITS):,} jobs", flush=True)
    else:
        print("⚠ no job_permits.json — run permit_phase.py first; construction "
              "entry dates will fall back to sign-off", flush=True)
    print("PULLING BIS", flush=True)
    proj = pull_bis()
    print(f"   -> {len(proj):,} BIS projects", flush=True)
    print("PULLING DOB NOW", flush=True)
    now = pull_now()
    print(f"   -> {len(now):,} NOW projects", flush=True)
    proj.update({f"NOW:{k}": v for k, v in now.items()})
    del now
    print("PULLING CERTIFICATES", flush=True)
    co = pull_co()
    print(f"   -> {len(co):,} parcels with a CO", flush=True)

    by_stage, by_scope, onspine = Counter(), Counter(), Counter()
    stage_scope = defaultdict(Counter)
    nobbl = 0
    with OUT.open("w", encoding="utf-8") as fh:
        for p in proj.values():
            p["stage"], p["stage_entered"] = stage4(p, co)
            p["last"] = max((x for x in (p.get("last_action", ""), p.get("status_date", ""),
                                         p.get("first_permit", ""), p.get("stage_entered", ""),
                                         p.get("filed", "")) if x), default="")
            p["withdrawn"] = (p.get("status") or "") in ("WITHDRAWN", "Filing Withdrawn")
            c = co.get(p.get("job"))
            p["co_n"] = c["n"] if c else 0
            p["active"] = p["stage"] in ACTIVE
            if not p.get("bbl"):
                nobbl += 1
            by_stage[p["stage"]] += 1
            for s in p["scope"]:
                by_scope[s] += 1
                stage_scope[p["stage"]][s] += 1
            onspine[bool(p.get("bbl"))] += 1
            p.pop("_n", None)
            fh.write(json.dumps(p) + "\n")

    tot = sum(by_stage.values())
    print()
    print("=" * 78)
    print(f"PROJECTS: {tot:,}      written -> {OUT.name}")
    print("=" * 78)
    print(f"{'stage':<24}{'projects':>10}  {'share':>7}")
    for s, n in by_stage.most_common():
        flag = "  <- MONITOR" if s in ACTIVE else ""
        print(f"   {s:<21}{n:>10,}  {n/tot:6.1%}{flag}")
    print()
    print("SCOPE (a job may carry two):")
    for s, n in by_scope.most_common():
        print(f"   {s:<21}{n:>10,}")
    print()
    print("STAGE x SCOPE:")
    hdr = ["demolition", "new_build", "conversion", "enlargement"]
    print(f"   {'':<22}" + "".join(f"{h:>13}" for h in hdr))
    for s, _ in by_stage.most_common():
        print(f"   {s:<22}" + "".join(f"{stage_scope[s][h]:>13,}" for h in hdr))
    print()
    print(f"⚠ projects with NO usable BBL: {nobbl:,} ({nobbl/tot:.1%}) "
          f"— cannot be assigned to the spine")
    act = sum(v for k, v in by_stage.items() if k in ACTIVE)
    print(f"★ ACTIVE (the monitoring set): {act:,} ({act/tot:.1%})")


if __name__ == "__main__":
    main()
