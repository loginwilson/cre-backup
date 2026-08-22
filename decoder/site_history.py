"""SITE HISTORY — one parcel in, its development history out.

    python site_history.py 4000170001

Gives, per development cycle: TYPE · TIMELINE with stage transitions and
VELOCITY · PLAYERS · DETAILS · SOURCE DOCUMENTS.

Stage model (settled, from the project's lifecycle notes):
    filing              -> pre_development
    work permit issued  -> construction      FO/EA are the irreversible start;
                                             FN/SF/EQ/CH are only mobilisation
    TCO                 -> temporary_operation   (renewals = velocity signal)
    final CO            -> operation
    DM signed off       -> cleared (the loop closing, not operation)

⚠ A site is GROUND. Its lot number, its BINs and its addresses all change, so
  identity is resolved as a SET before anything is pulled.
⚠ DM is the cycle SEGMENTER, not a development type in the output.
"""
import sys, pathlib, json
from collections import defaultdict, Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk, dob, keys, development as D

MOBILISATION = {"FN", "SF", "EQ", "CH", "SH"}   # not construction
IRREVERSIBLE = {"FO", "EA"}                      # the true start of a new building


def _q(ds, bbl, select=None):
    b, blk, lot = dob.keyparts(bbl, ds)
    try:
        return bulk.socrata(ds, where=f"borough='{b}' and block='{blk}' and lot='{lot}'",
                            select=select)
    except Exception:
        return []


def _hist(bbl):
    b, _, _ = dob.keyparts(bbl, dob.PERMITS)
    _, blk, lot = keys.parts(bbl)[0], keys.parts(bbl)[1], keys.parts(bbl)[2]
    try:
        return bulk.socrata(D.HIST,
                            where=f"borough='{b}' and block='{blk}' and lot='{lot}'")
    except Exception:
        return []


def gather(bbl):
    """Every layer, for one parcel. Returns raw rows per layer."""
    return {
        "hist":   _hist(bbl),
        "permit": _q(dob.PERMITS, bbl),
        "bis":    _q(dob.BIS_JOBS, bbl),
        "now":    _q(dob.NOW_JOBS, bbl),
        "co_bis": _q(dob.CO, bbl),
        "co_now": _q(dob.CO_NOW, bbl),
    }


def _d(s):
    return D.norm_date(s) or (str(s or "")[:10] if str(s or "")[:4].isdigit() else "")


def build_jobs(raw):
    """Collapse rows into JOBS. A row is not a job."""
    jobs = {}
    for r in raw["bis"]:
        if (r.get("doc__") or "01") != "01":
            continue
        j = r.get("job__")
        if not j:
            continue
        jobs.setdefault(j, {"id": j, "system": "BIS", "type": r.get("job_type"),
                            "filed": _d(r.get("pre__filing_date")),
                            "approved": _d(r.get("approved")),
                            "signoff": _d(r.get("signoff_date")),
                            "status": r.get("job_status_descrp"),
                            "desc": (r.get("job_description") or "").strip(),
                            "zoning": r.get("zoning_dist1"),
                            "zoning_sqft": r.get("proposed_zoning_sqft"),
                            "enlargement": r.get("enlargement_sq_footage"),
                            "du": (r.get("existing_dwelling_units"), r.get("proposed_dwelling_units")),
                            "height": (r.get("existing_height"), r.get("proposed_height")),
                            "stories": r.get("proposed_no_of_stories"),
                            "owner": r.get("owner_s_business_name"),
                            "applicant": " ".join(x for x in (r.get("applicant_s_first_name"),
                                                              r.get("applicant_s_last_name")) if x),
                            "applicant_lic": r.get("applicant_license__"),
                            "bin": r.get("bin__"), "permits": [], "cos": []})
    for r in raw["now"]:
        base, letter, seq = dob.now_base(r.get("job_filing_number"))
        if not base:
            continue
        j = jobs.setdefault(base, {"id": base, "system": "NOW", "type": r.get("job_type"),
                                   "filed": "", "approved": "", "signoff": "",
                                   "status": r.get("filing_status"),
                                   "desc": (r.get("job_description") or "").strip(),
                                   "zoning": None, "zoning_sqft": None,
                                   "enlargement": None,
                                   "du": (r.get("existing_dwelling_units"), r.get("proposed_dwelling_units")),
                                   "height": (None, r.get("proposed_height")),
                                   "stories": r.get("proposed_no_of_stories"),
                                   "owner": r.get("owner_s_business_name"),
                                   "applicant": " ".join(x for x in (r.get("applicant_first_name"),
                                                                     r.get("applicant_last_name")) if x),
                                   "applicant_firm": r.get("applicant_business_name"),
                                   "filing_rep": r.get("filing_representative_business_name"),
                                   "tcfa": r.get("total_construction_floor_area"),
                                   "bin": r.get("bin"), "permits": [], "cos": [],
                                   "filings": []})
        fd = _d(r.get("filing_date"))
        j["filings"].append((f"{letter}{seq}", fd, r.get("filing_status")))
        if fd and (not j["filed"] or fd < j["filed"]):
            j["filed"] = fd
        ap = _d(r.get("approved_date"))
        if ap and (not j["approved"] or ap < j["approved"]):
            j["approved"] = ap
        so = _d(r.get("signoff_date"))
        if so and so > (j["signoff"] or ""):
            j["signoff"] = so
    # permits, deduped across both feeds
    merged, _ = D.merge_permits(raw["hist"], raw["permit"])
    for r in merged:
        j = str(r.get("job__") or r.get("job") or "")
        rec = {"date": r.get("_date") or _d(r.get("issuance_date")),
               "type": r.get("permit_type"), "subtype": r.get("permit_subtype"),
               "permittee": r.get("permittee_s_business_name"),
               "permittee_phone": r.get("permittee_s_phone__") or r.get("permittee_s_phone"),
               "owner": r.get("owner_s_business_name"),
               "owner_name": " ".join(x for x in (r.get("owner_s_first_name"),
                                                  r.get("owner_s_last_name")) if x),
               "owner_addr": " ".join(str(x) for x in (r.get("owner_s_house"),
                                                       r.get("owner_s_house_street_name"),
                                                       r.get("owner_s_house_city"),
                                                       r.get("owner_s_house_state"),
                                                       r.get("owner_s_house_zip_code")) if x),
               "owner_phone": r.get("owner_s_phone"),
               "job_type": r.get("job_type")}
        if j in jobs:
            jobs[j]["permits"].append(rec)
        else:
            jobs[j] = {"id": j, "system": "PERMIT-ONLY", "type": r.get("job_type"),
                       "filed": "", "approved": "", "signoff": "", "status": None,
                       "desc": "", "zoning": None, "zoning_sqft": None,
                       "enlargement": None, "du": (None, None), "height": (None, None),
                       "stories": None, "owner": rec["owner"], "applicant": None,
                       "bin": r.get("bin__") or r.get("bin"), "permits": [rec], "cos": []}
    for r in raw["co_bis"] + raw["co_now"]:
        j = str(r.get("job_number") or r.get("job_filing_name") or "")
        base = dob.now_base(j)[0] if j and j[:1].isalpha() else j
        rec = {"date": _d(r.get("c_of_o_issuance_date") or r.get("effectivedate")),
               "status": r.get("c_of_o_status"), "kind": r.get("c_of_o_filing_type"),
               "du": r.get("number_of_dwelling_units"), "no": r.get("c_of_o_number")}
        if base in jobs:
            jobs[base]["cos"].append(rec)
    return jobs


SCOPE_OF = {"NB": "NEW BUILD", "A1": "CONVERSION", "DM": "DEMOLITION",
            "New Building": "NEW BUILD",
            "ALT-CO - New Building with Existing Elements to Remain": "NEW BUILD",
            "Alteration CO": "CONVERSION", "No Work": "CONVERSION",
            "Full Demolition": "DEMOLITION"}


def scope_of(j):
    s = SCOPE_OF.get(j.get("type") or "")
    try:
        if float(j.get("enlargement") or 0) > 0:
            return "ENLARGEMENT" if not s else f"{s} + ENLARGEMENT"
    except (TypeError, ValueError):
        pass
    if not s and "ENLARG" in (j.get("desc") or "").upper():
        return "ENLARGEMENT"
    return s


def stages(j):
    """Stage transitions with dates. Only the ones that actually happened."""
    out = []
    if j["filed"]:
        out.append(("pre_development", j["filed"], "filed"))
    if j["approved"]:
        out.append(("pre_development", j["approved"], "approved"))
    perms = sorted([p for p in j["permits"] if p["date"]], key=lambda p: p["date"])
    mob = next((p for p in perms if (p["subtype"] or p["type"]) in MOBILISATION), None)
    real = next((p for p in perms if (p["subtype"] or p["type"]) in IRREVERSIBLE), None)
    first = perms[0] if perms else None
    if mob:
        out.append(("mobilisation", mob["date"], f"{mob['type']}/{mob['subtype'] or '-'} permit"))
    if real:
        out.append(("construction", real["date"],
                    f"{real['type']}/{real['subtype'] or '-'} permit  <- irreversible"))
    elif first:
        out.append(("construction", first["date"],
                    f"{first['type']}/{first['subtype'] or '-'} permit"))
    for c in sorted([c for c in j["cos"] if c["date"]], key=lambda c: c["date"]):
        stage = "temporary_operation" if (c["kind"] or "").lower().startswith(("renewal", "temp")) else "operation"
        out.append((stage, c["date"], f"CO {c['kind'] or ''} {c['no'] or ''}".strip()))
    if j["signoff"]:
        st = "cleared" if (j.get("type") in ("DM", "Full Demolition")) else "operation"
        out.append((st, j["signoff"], "signed off"))
    return sorted(out, key=lambda t: t[1])


def days(a, b):
    from datetime import date
    try:
        ya, ma, da = (int(x) for x in a.split("-")); yb, mb, db = (int(x) for x in b.split("-"))
        return (date(yb, mb, db) - date(ya, ma, da)).days
    except Exception:
        return None


def render(bbl):
    raw = gather(bbl)
    jobs = build_jobs(raw)
    scoped = {k: v for k, v in jobs.items() if scope_of(v)}
    boro, block, lot = keys.parts(bbl)
    print(f"SITE {bbl}   (boro {boro} block {block} lot {lot})")
    bins = sorted({j.get("bin") for j in jobs.values() if j.get("bin")})
    print(f"  BINs ever seen: {bins}")
    print(f"  jobs total {len(jobs):,}   IN SCOPE {len(scoped):,}   "
          f"(demolition/new build/conversion/enlargement)")
    if not scoped:
        print("\n  NO DEVELOPMENT IN SCOPE. Everything on this parcel is maintenance.")
        print("  If it was built before 1989 the only record is the HPD I-card.")
        return
    # ⚠ Order on the EARLIEST date the job has — a PERMIT-ONLY job (pre-2000,
    # no jobs-feed row) has no filing date at all, and sorting those to the end
    # put a 2003 demolition after a 2021 new building.
    def anchor(j):
        ds = [j["filed"]] + [p["date"] for p in j["permits"] if p["date"]] \
             + [c["date"] for c in j["cos"] if c["date"]]
        ds = [d for d in ds if d]
        return min(ds) if ds else "9999"

    order = sorted(scoped.values(), key=anchor)
    # ⚠ A demolition OPENS a cycle — it clears the ground for what follows.
    # Closing on it put the 2021 new building in the same cycle as the
    # demolitions that preceded it and split the three DMs across two cycles.
    cycles, cycle = [], []
    for j in order:
        if scope_of(j).startswith("DEMOLITION") and cycle and \
           not all(scope_of(x).startswith("DEMOLITION") for x in cycle):
            cycles.append(cycle); cycle = []
        cycle.append(j)
    if cycle:
        cycles.append(cycle)
    for ci, cyc in enumerate(cycles, 1):
        print(f"\n{'='*74}\n  DEVELOPMENT CYCLE {ci} of {len(cycles)}")
        for j in cyc:
            sc = scope_of(j)
            print(f"\n  ── {sc}   job {j['id']} [{j['system']}]  {j.get('type')}")
            if j["desc"]:
                print(f"     \"{j['desc'][:150]}\"")
            det = []
            if j.get("zoning"): det.append(f"zoning {j['zoning']}")
            if j.get("zoning_sqft") and str(j["zoning_sqft"]) != "0": det.append(f"zoning sf {j['zoning_sqft']}")
            if j.get("tcfa"): det.append(f"constr sf {j['tcfa']}")
            try:
                if float(j.get("enlargement") or 0) > 0: det.append(f"ENLARGEMENT {j['enlargement']} sf")
            except (TypeError, ValueError): pass
            if j["du"][1]: det.append(f"DU {j['du'][0] or '?'}->{j['du'][1]}")
            if j["height"][1]: det.append(f"height ->{j['height'][1]}")
            if j.get("stories"): det.append(f"{j['stories']} storeys")
            if det: print(f"     DETAILS  {' · '.join(str(d) for d in det)}")
            pl = []
            if j.get("owner"): pl.append(f"owner {j['owner']}")
            if j.get("applicant"): pl.append(f"applicant {j['applicant']}"
                                             + (f" ({j['applicant_lic']})" if j.get("applicant_lic") else ""))
            if j.get("applicant_firm"): pl.append(f"firm {j['applicant_firm']}")
            if j.get("filing_rep"): pl.append(f"filing rep {j['filing_rep']}")
            if pl: print(f"     PLAYERS  {' · '.join(pl)}")
            seen_p = set()
            for p in sorted(j["permits"], key=lambda p: p["date"] or ""):
                sig = (p["permittee"], p.get("permittee_phone"), p.get("owner_name"),
                       p.get("owner_phone"))
                if sig in seen_p:
                    continue          # same party across several permit sequences
                seen_p.add(sig)
                who = p["permittee"] or "-"
                ph = f" ph {p['permittee_phone']}" if p.get("permittee_phone") else ""
                print(f"       {p['date'] or '?':<11} permittee {who}{ph}")
                if p.get("owner_name") or p.get("owner_addr") or p.get("owner_phone"):
                    print(f"                   OWNER {p.get('owner_name') or ''}"
                          f"{' | ' + p['owner_addr'] if p.get('owner_addr') else ''}"
                          f"{' | ph ' + p['owner_phone'] if p.get('owner_phone') else ''}")
                if len(seen_p) >= 6:
                    break
            st = stages(j)
            if st:
                print("     TIMELINE")
                prev = None
                for stage, d, what in st:
                    gap = f"   +{days(prev, d)}d" if prev and days(prev, d) is not None else ""
                    print(f"       {d}  {stage:<22}{what}{gap}")
                    prev = d
                span = days(st[0][1], st[-1][1])
                if span is not None:
                    print(f"       VELOCITY  {span} days from {st[0][0]} to {st[-1][0]}"
                          f"  ({span/365.25:.1f} yrs)")
            fy = (j["filed"] or "")[:4]
            doc = ("B-Scan folder available" if fy.isdigit() and int(fy) >= 2008 and j["system"] == "BIS"
                   else "NOW portal Documents" if j["system"] == "NOW"
                   else "NO SCANNED DOCUMENT (pre-2008)" if fy.isdigit() and int(fy) < 2008
                   else "unknown")
            print(f"     DOCUMENTS  {doc}")


if __name__ == "__main__":
    for bbl in (sys.argv[1:] or ["4000170001"]):
        render(bbl)
        print()
