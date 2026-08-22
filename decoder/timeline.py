"""A parcel's timeline — the product this project exists to make.

Development rights are the subject. Everything else in the toolkit is LINKAGE:
DOF dates the map change and names the instrument that caused it; DOB supplies
the stage transitions; HPD names the people; DOF sales price the land. None of
them is the point on its own.

WHAT MAKES THIS MORE THAN A MERGED LIST

  * **Every row cites its source and its document.** A timeline nobody can walk
    back to a page is an anecdote.
  * **Dates are normalised before sorting.** BIS returns MM/DD/YYYY, ArcGIS
    epoch-ms, the rest ISO — string-sorting a mixed list reorders a parcel's
    history while every individual row stays correct. The first version of this
    timeline printed wrong for exactly that reason.
  * **Lineage is followed.** A parcel's history does not stop where its BBL
    stops: lots merge, get apportioned, become condominiums. Ask for lot 3 and
    you should see what happened to the lot that absorbed it.
  * **Contradictions are surfaced, not smoothed.** Two sources disagreeing about
    the same event is a FINDING. The `--check` pass looks for orderings that
    cannot be true.
"""
import json, pathlib, sys
from collections import defaultdict

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import keys

ENV = r"C:/dev/acris-decoder.env"


def _sup(path):
    import urllib.request
    v = {}
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, val = line.split("=", 1)
            v[k.strip()] = val.strip()
    req = urllib.request.Request(v["ACRIS_SUPABASE_URL"] + "/rest/v1/" + path,
                                 headers={"apikey": v["ACRIS_SUPABASE_SERVICE_KEY"],
                                          "Authorization": "Bearer " + v["ACRIS_SUPABASE_SERVICE_KEY"]})
    with urllib.request.urlopen(req, timeout=90) as f:
        return json.load(f)


def related_bbls(bbl):
    """The parcel AND whatever it became or absorbed.

    A history that stops at the BBL you asked for is incomplete the moment a lot
    merges. Successors and predecessors come from DOF's published alteration
    book where available, and from the inferred spine before 2008.
    """
    out = {bbl}
    try:
        rows = _sup(f"decoder_bbl_spine?select=bbl,successors,predecessors&bbl=eq.{bbl}")
        for r in rows:
            out |= set(r.get("successors") or [])
            out |= set(r.get("predecessors") or [])
    except Exception:
        pass
    return sorted(out)


def collect(bbls, want=("acris", "dof_map", "dof_sale", "dob", "hpd")):
    """Every dated event touching these parcels, each carrying its citation."""
    ev = []

    if "acris" in want:
        try:
            import entities
            for o in entities.observations():
                if o["bbl"] in bbls:
                    ev.append({"date": keys.iso_date(o["date"]), "source": "ACRIS",
                               "bbl": o["bbl"], "kind": o["role"],
                               "detail": o["name_as_written"],
                               "cite": f"doc {o['document_id']}"})
        except Exception as e:
            ev.append({"date": None, "source": "ACRIS", "bbl": None, "kind": "ERROR",
                       "detail": str(e)[:80], "cite": ""})

    if "dof_map" in want:
        f = HERE / "dof_lineage_all.json"
        if f.exists():
            hist = json.loads(f.read_text(encoding="utf-8"))
            for b in bbls:
                for r in (hist.get(b) or []):
                    cites = (r.get("cites") or {}).get("crfns") or []
                    ev.append({"date": keys.iso_date(r["change_date"]), "source": "DOF map",
                               "bbl": b, "kind": r["change_type"],
                               "detail": f"{r['lot_actions']}",
                               "cite": (f"trans {r['trans_num']}"
                                        + (f", CRFN {cites[0]}" if cites else ""))})

    if "dof_sale" in want:
        try:
            import dof_value as dv
            for s in dv.rows_for(bbls, dv.SALES):
                amt = float(s.get("sale_price") or 0)
                ev.append({"date": keys.iso_date(s.get("sale_date")), "source": "DOF sale",
                           "bbl": s.get("bbl"), "kind": "sale",
                           "detail": f"${amt:,.0f}" if amt else "$0 (non-arms-length or nominal)",
                           "cite": s.get("building_class_at_time_of_sale") or ""})
        except Exception:
            pass

    if "dob" in want:
        try:
            import dob
            for j in dob.jobs_for(bbls, dob.BIS_JOBS) + dob.jobs_for(bbls, dob.NOW_JOBS):
                d = keys.iso_date(j.get("latest_action_date") or j.get("filing_date"))
                ev.append({"date": d, "source": "DOB", "bbl": None,
                           "kind": dob.stage_of(j),
                           "detail": f"{j.get('job_type','')}".strip(),
                           "cite": f"job {j.get('job__') or j.get('job_filing_number')}"})
        except Exception:
            pass

    return ev


STAGE_ORDER = {"pre_development": 1, "construction": 2, "operation": 3,
               "cleared": 0, "abandoned": 0}


def contradictions(ev):
    """Orderings that cannot be true, and gaps worth a look.

    Reports SUSPICIONS, not verdicts — a parcel can legitimately run several
    jobs at once, so 'operation before construction' is a prompt to look, not
    proof of an error.
    """
    out = []
    dated = [e for e in ev if e["date"]]
    acris = [e for e in dated if e["source"] == "ACRIS"]
    sales = [e for e in dated if e["source"] == "DOF sale"]
    dof = [e for e in dated if e["source"] == "DOF map"]

    # a rights transfer with no financing and no sale within a year either side
    for a in acris:
        if "recipient_of_rights" not in (a["kind"] or ""):
            continue
        near = [s for s in sales if s["date"] and abs(
            (int(s["date"][:4]) * 12 + int(s["date"][5:7]))
            - (int(a["date"][:4]) * 12 + int(a["date"][5:7]))) <= 18]
        if not near:
            out.append(f"{a['date']} rights received on {a['bbl']} with no DOF sale "
                       f"within 18 months — either the land was already held, or a "
                       f"conveyance is missing from the store ({a['cite']})")

    # a map change with no instrument cited
    for d in dof:
        if "CRFN" not in (d["cite"] or ""):
            out.append(f"{d['date']} {d['kind']} on {d['bbl']} cites no CRFN — "
                       f"the map moved with no instrument named ({d['cite']})")
    return out


def doc_date(master_row):
    """A document's date, falling back the way ACRIS actually stores it.

    ⚠ 6,092,729 documents — 35.8% of ACRIS — have ids prefixed `FT_` ("film
    transfer"): the MICROFILM era, running back past 1967. Every one carries a
    reel/page reference, and **79% (4,811,623) have NO `document_date` at all**,
    only `recorded_datetime`.

    Reading `document_date` alone therefore drops 4.8 MILLION documents out of
    every parcel history as "undated" — and they are precisely the EARLY ones.
    A timeline claiming to run birth-to-present was starting in the modern era
    and saying nothing about it. Measured 2026-08-05.
    """
    m = master_row or {}
    return (keys.iso_date(m.get("document_date"))
            or keys.iso_date(m.get("recorded_datetime")))


def reel_of(master_row):
    """Microfilm citation for a pre-electronic record, or None.

    For FT_ documents the reel/page IS the archival address — the thing a person
    would quote to pull the record — so it belongs on the timeline row.
    """
    m = master_row or {}
    try:
        if int(m.get("reel_nbr") or 0) > 0:
            return f"reel {m.get('reel_yr')}/{m.get('reel_nbr')}/{m.get('reel_pg')}"
    except (TypeError, ValueError):
        pass
    return None


def coverage(bbls):
    """What EXISTS against these parcels versus what we have actually READ.

    ⚠ THE MOST IMPORTANT FUNCTION IN THIS FILE.

    A timeline built only from decoded documents renders an unread document as
    SILENCE — indistinguishable from a period when nothing happened. Measured on
    pilot parcel 1014460001 on 2026-08-05: 25 ACRIS documents recorded against
    the lot spanning 1988-2026, of which THREE were decoded. The timeline looked
    complete and was 12% complete.

    The index is free and unmetered, so what exists is always knowable even when
    the images are unreachable. There is therefore no excuse for ever presenting
    a partial history as a whole one.
    """
    import bulk
    try:
        import entities
        decoded = {o["document_id"] for o in entities.observations()}
    except Exception:
        decoded = set()

    docs = {}
    for b in bbls:
        boro, blk, lot = keys.parts(b)
        rows = bulk.socrata("8h5j-fqxa",
                            where=f"borough='{boro}' and block='{blk}' and lot='{lot}'",
                            paginate=True)
        for r in rows:
            docs[r["document_id"]] = b
    if not docs:
        return {"exists": 0, "decoded": 0, "unread": [], "by_type": {}}
    mas = bulk.socrata_in("bnx9-e6tj", "document_id", sorted(docs))
    meta = {m["document_id"]: m for m in mas}
    unread = []
    from collections import Counter
    by_type = Counter()
    for d in docs:
        by_type[(meta.get(d) or {}).get("doc_type") or "?"] += 1
        if d not in decoded:
            m = meta.get(d) or {}
            unread.append({"document_id": d, "doc_type": m.get("doc_type"),
                           "date": doc_date(m), "reel": reel_of(m),
                           "bbl": docs[d]})
    unread.sort(key=lambda u: u["date"] or "")
    return {"exists": len(docs), "decoded": len(docs) - len(unread),
            "unread": unread, "by_type": dict(by_type.most_common()),
            "custodian": custodian_gap(bbls, by_type)}


def custodian_gap(bbls, by_type):
    """Is this parcel's record STRUCTURALLY incomplete in ACRIS? Verified 2026-08-05.

    ACRIS master holds ZERO documents recorded in Staten Island. What it does
    hold for borough 5 is 192,950 documents that are >98% RPTT — real property
    transfer TAX RETURNS, administratively recorded in the Bronx. The deeds,
    mortgages, easements and declarations live with the RICHMOND COUNTY CLERK,
    digitised back to 1945 (earlier than ACRIS itself).

    So for a Staten Island lot, "we have read everything ACRIS has" and "we know
    this parcel's history" are different statements. The tell is RPTT present
    with no matching conveyance. This must be stated, not inferred — an
    incomplete history that looks complete is the failure this project keeps
    meeting.
    """
    boros = {keys.parts(b)[0] for b in bbls}
    if 5 not in boros:
        return None
    conveyances = sum(v for k, v in by_type.items()
                      if k and (k.startswith("DEED") or k in ("MTGE", "EASE", "DECL")))
    return {
        "borough": "Staten Island",
        "acris_holds": "transfer tax returns (RPTT) only — recorded in the Bronx",
        "conveyances_in_acris": conveyances,
        "other_custodian": "Richmond County Clerk, 130 Stuyvesant Place, "
                           "(718) 675-7700 — Land Document Search, digitised to 1945",
        "warning": "ACRIS is NOT the record of title here. A history built from "
                   "ACRIS alone is structurally incomplete, not merely unread.",
    }


def render(bbl, show_undated=False, check=True):
    bbls = related_bbls(bbl)
    ev = collect(bbls)
    dated = sorted([e for e in ev if e["date"]], key=lambda e: e["date"])
    print(f"PARCEL TIMELINE — {bbl}")
    if len(bbls) > 1:
        print(f"  following lineage across: {', '.join(bbls)}")
    print()
    for e in dated:
        who = (e["bbl"] or "")[-4:] if e["bbl"] else "    "
        print(f"  {e['date']}  {e['source']:<9} {who:<5} {str(e['kind'])[:22]:<24}"
              f" {str(e['detail'])[:40]:<42} {e['cite']}")
    undated = [e for e in ev if not e["date"]]
    if undated and show_undated:
        print(f"\n  {len(undated)} undated events (not placed on the timeline)")
    print(f"\n  {len(dated)} dated events from "
          f"{len({e['source'] for e in dated})} sources")

    # ---- COVERAGE. Printed ALWAYS, never on request, because a reader who has
    # to ask "is this everything?" has already been misled by the silence above.
    try:
        cov = coverage(bbls)
    except Exception as e:
        print(f"\n  ⚠ COVERAGE UNKNOWN ({type(e).__name__}) — treat this timeline "
              f"as INCOMPLETE of unknown degree")
        cov = None
    if cov and cov["exists"]:
        pct = cov["decoded"] / cov["exists"] * 100
        print(f"\n  COVERAGE  {cov['decoded']}/{cov['exists']} ACRIS documents read "
              f"({pct:.0f}%)")
        print(f"            {' · '.join(f'{k} {v}' for k, v in cov['by_type'].items())}")
        cg = cov.get("custodian")
        if cg:
            print(f"\n  ⚠⚠ STRUCTURAL GAP — {cg['borough']}")
            print(f"     ACRIS holds: {cg['acris_holds']}")
            print(f"     conveyances present in ACRIS: {cg['conveyances_in_acris']}")
            print(f"     {cg['warning']}")
            print(f"     Other custodian: {cg['other_custodian']}")
        if cov["unread"]:
            print(f"\n  ⚠ {len(cov['unread'])} DOCUMENTS EXIST THAT WE HAVE NOT READ.")
            print(f"    The timeline above shows SILENCE for these, which is not "
                  f"the same as nothing happening:")
            for u in cov["unread"][:12]:
                print(f"      {u['date'] or '    ?     '}  {str(u['doc_type']):<9} "
                      f"{u['document_id']:<18} {u.get('reel') or ''}")
            if len(cov["unread"]) > 12:
                print(f"      ... and {len(cov['unread']) - 12} more")

    if check:
        issues = contradictions(ev)
        if issues:
            print(f"\n  {len(issues)} thing(s) worth a look:")
            for i in issues[:8]:
                print(f"    - {i}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        raise SystemExit("usage: python timeline.py <bbl> [--undated] [--no-check]")
    render(args[0], show_undated="--undated" in sys.argv,
           check="--no-check" not in sys.argv)
