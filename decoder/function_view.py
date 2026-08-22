"""FUNCTION VIEW — group the decoded atoms by function, chronologically, cited.

LOGIN, 2026-08-06, the pipeline stated exactly:

    "You basically decode the documents into the TERMS/VALUES, then you
     categorise those terms and values into what you believe the FUNCTIONS of
     ACRIS are, for later to be converted into a packaged card. Right now we are
     asking for data cleaned into terms/values and then GROUPED BY FUNCTION of
     the source. Meanwhile, sourcing and citation is expected throughout."

        documents -> TERMS + VALUES -> tagged by FUNCTION -> grouped view -> card
                     (atoms, cited)     (this module)        (this module)  (later)

⚠ WHAT THIS REPLACES, AND WHY IT MATTERS

    functions.py held a hand-written ENVELOPE narrative — eight paragraphs of
    prose I typed. It read well and it was already wrong in construction: prose
    written BESIDE the atoms drifts from them the moment either changes, which
    is the exact failure that put a stale page count and an omitted 1998 deed
    into LOT49_EVENTS.md within hours.

    So the narrative is a QUERY. Every line below is emitted from a claim or a
    term, carries that atom's own document and page, and changes automatically
    when the atom does. A line with no atom cannot be written.

⚠ FUNCTION TAGGING IS DERIVED, NOT TYPED PER ROW

    The function comes from the PREDICATE (for values) and the DIMENSION (for
    terms). Tagging 108 claims by hand would be 108 opportunities to be
    inconsistent; deriving it from the vocabulary means a predicate belongs to
    the same function everywhere, forever, and re-tagging is one edit.

⚠ BASE LEVEL AND VARIANCE
    A function narrative is not a list of events. It is a BASE and its
    variations: ENVELOPE opens at 156,390 and moves seven times; DEBT opens at
    $1,000,000 in 1990 and is still being rolled forward in 2025. The running
    column is what makes it a narrative rather than a log.
"""
import csv, pathlib, sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).parent
L49 = "1008000049"

# predicate -> function(s). Derived once; a predicate means the same thing
# everywhere it appears.
PRED_FN = {
 "conveyance": ["TITLE"], "consideration": ["VALUE"],
 "consideration_recited": ["VALUE"], "tax_paid": ["VALUE"],
 "tax_rate": ["VALUE"],
 "mortgage": ["DEBT"], "consolidation": ["DEBT"],
 "rights_transferred": ["ENVELOPE"], "rights_retained": ["ENVELOPE"],
 "rights_generated": ["ENVELOPE"], "envelope_balance": ["ENVELOPE"],
 "far_implied": ["ENVELOPE"], "zoning_lot_members": ["ENVELOPE", "ENCUMBRANCE"],
 "easement": ["ENCUMBRANCE", "ENVELOPE"], "unit_cap": ["ENCUMBRANCE", "ENVELOPE"],
 "lot_area": ["PARCEL"], "subdivision": ["PARCEL"],
 "boundary_origin": ["PARCEL"], "reel_page": ["PARCEL"],
 "property_type": ["TENANCY"],
 "party_role": ["CONSENT"], "person": ["CONSENT"],
 "cross_reference": ["DEBT"],
 "defect": [], "unresolved": [],      # meta — belong to no function
}

# term dimension -> function(s)
DIM_FN = {
 "HEIGHT": ["ENCUMBRANCE", "ENVELOPE"], "USE": ["ENCUMBRANCE"],
 "ACCESS": ["ENCUMBRANCE"], "PROCESS": ["ENCUMBRANCE", "CONSENT"],
 "REMEDY": ["ENCUMBRANCE"], "FLOOR_AREA": ["ENVELOPE"],
 "UNITS": ["ENCUMBRANCE", "ENVELOPE"],
 # a mortgage covenant is a DEBT term; where it also restricts what may be
 # built or done to the building it is an ENVELOPE/ENCUMBRANCE term as well
 "REMEDY_DEBT": ["DEBT"], "PROCESS_DEBT": ["DEBT"],
 "USE_DEBT": ["DEBT", "ENVELOPE", "ENCUMBRANCE"],
 "INCOME": ["INCOME", "DEBT"],
 # the spreader touches DEBT and ENVELOPE at once: it is how acquired air
 # rights become collateral. PRIORITY is its own function — see functions.py
 "SPREADER": ["DEBT", "ENVELOPE"], "PRIORITY": ["PRIORITY", "DEBT"],
}

# term slot -> dimension, for terms sourced from the doctype menu
SLOT_DIM = {
 "light_air_view_easement": "HEIGHT", "existing_building_carveout": "HEIGHT",
 "alteration_restriction": "USE", "repair_carveout": "USE",
 "violation_covenant": "USE", "unit_cap": "UNITS",
 "self_help_license": "ACCESS", "parking_lane_letter": "ACCESS",
 "plan_review_right": "PROCESS", "confirming_instrument": "PROCESS",
 "cooperation_covenant": "PROCESS", "dob_consent_to_amend": "PROCESS",
 "runs_with_land": "PROCESS", "co_recording_covenant": "PROCESS",
 "cure_period": "REMEDY", "injunctive_relief": "REMEDY",
 "rights_conveyance": "FLOOR_AREA",
 # MTGE menu — DEBT terms, the function that had 26 values and zero terms
 "one_parcel_foreclosure": "REMEDY_DEBT", "lender_cost_lien": "REMEDY_DEBT",
 "rents_assignment": "INCOME", "advance_rent_bar": "INCOME",
 "possession_on_default": "INCOME", "acceleration_triggers": "REMEDY_DEBT",
 "alteration_consent": "USE_DEBT", "repair_covenant": "USE_DEBT",
 "violation_compliance": "USE_DEBT", "insurance_254": "PROCESS_DEBT",
 "max_principal_secured": "REMEDY_DEBT", "limited_recourse": "REMEDY_DEBT",
 "loan_agreement_controls": "PROCESS_DEBT", "lien_law_trust_fund": "PROCESS_DEBT",
 "binds_tenants": "INCOME", "no_oral_modification": "PROCESS_DEBT",
 "insurability_default": "REMEDY_DEBT", "fixtures_removal_default": "USE_DEBT",
 "tax_law_change_default": "REMEDY_DEBT",
 "catchall_covenant_default": "REMEDY_DEBT",
 # CEMA menu
 "no_default_rep": "PROCESS_DEBT", "fee_title_rep": "PROCESS_DEBT",
 "authority_rep": "PROCESS_DEBT", "consolidation_amount": "REMEDY_DEBT",
 "consolidated_note": "PROCESS_DEBT", "lien_spreader": "SPREADER",
 "single_first_lien": "PRIORITY", "modification_by_schedule": "PROCESS_DEBT",
 "collateral_additional_land": "SPREADER", "collateral_easements": "SPREADER",
 "collateral_improvements": "PROCESS_DEBT", "collateral_equipment": "PROCESS_DEBT",
 # split-ZLDA menu
 "bonus_rights_allocation": "FLOOR_AREA", "future_agency_rights": "FLOOR_AREA",
 "construction_easement": "ACCESS", "emergency_definition": "ACCESS",
 "zr_12_10_definitions": "PROCESS",
}

RUNNING = {"envelope_balance": "sf", "consolidation": "USD"}


import functions_vocab as FV


def load_values():
    sys.path.insert(0, str(HERE))
    import claims as K
    out = []
    for c in K.rows():
        # ⚠ the claim's declared KIND decides how it renders. A TERM_REF claim
        # printed in the VALUE column reads as a measured fact when it is an
        # announcement of an obligation — caught the first time this view ran.
        k = "TERM" if K.KIND[c["predicate"]] == "TERM_REF" else "VALUE"
        # ⚠ UNION of predicate-derived and claim-declared functions.
        # Taking only the predicate silently discarded every ans=[...]
        # tag for ~14 hours — see functions_vocab.py for the mechanism.
        for fn in FV.functions_of(c, PRED_FN):
            out.append(dict(
                function=fn, kind=k, effective=c["effective"],
                predicate=c["predicate"], num=c["value_num"], unit=c["unit"],
                text=c["value_text"], subject=c["subject_bbl"],
                doc=c["document_id"], page=c["page"], evidence=c["evidence"],
                detail=c.get("verbatim") or c.get("derivation")))
    return out


def load_terms():
    out = []
    tp = HERE / f"acris_terms_{L49}.csv"
    if tp.exists():
        for r in csv.DictReader(open(tp, encoding="utf-8")):
            for fn in DIM_FN.get("USE" if r["modality"].startswith("MUST")
                                 else "PROCESS", ["ENCUMBRANCE"]):
                out.append(dict(
                    function=fn, kind="TERM", effective=r["effective"],
                    predicate=r["action"], num=None, unit=None,
                    text=f"{r['actor']} {r['modality']} {r['action']}"
                         + (f" {r['object']}" if r["object"] else ""),
                    subject=r["burdened_bbl"], doc=r["document_id"],
                    page=r["page"], evidence="read",
                    detail=("RELEASE: " + (r["consent_of"] or
                            "NOBODY — cannot be released"))))
    ip = HERE / "doctype_term_instance.csv"
    if ip.exists():
        for r in csv.DictReader(open(ip, encoding="utf-8")):
            if r["status"] != "PRESENT":
                continue
            dim = SLOT_DIM.get(r["slot"], "USE")
            for fn in DIM_FN.get(dim, ["ENCUMBRANCE"]):
                out.append(dict(
                    function=fn, kind="TERM", effective=r.get("effective") or "",
                    predicate=r["slot"], num=None, unit=None,
                    text=r["value_text"], subject=r["burdened_bbl"] or L49,
                    doc=r["document_id"], page=r["page"], evidence="read",
                    detail=(r["verbatim"] or "")[:150]))
    return out


def narrate(function, atoms):
    rows = sorted([a for a in atoms if a["function"] == function],
                  key=lambda a: (a["effective"] or "", a["kind"], a["doc"]))
    if not rows:
        return
    print(f"\n{'='*80}\nFUNCTION · {function}   ({len(rows)} atoms: "
          f"{sum(1 for r in rows if r['kind']=='VALUE')} values, "
          f"{sum(1 for r in rows if r['kind']=='TERM')} terms)\n{'='*80}")
    running = None
    last_date = None
    for r in rows:
        if r["effective"] != last_date:
            print(f"\n  {r['effective']}")
            last_date = r["effective"]
        subj = "" if r["subject"] == L49 else f" [lot {r['subject'][-3:].lstrip('0')}]"
        if r["kind"] == "VALUE":
            if r["num"] is not None:
                u = r["unit"] or ""
                v = (f"${r['num']:,.2f}" if u == "USD"
                     else f"{r['num']:,.0f} {u}".strip())
            else:
                v = (r["text"] or "")[:66]
            if r["predicate"] in RUNNING and r["num"] is not None:
                running = r["num"]
            run = (f"   → running {running:,.0f}"
                   if (running is not None and r["predicate"] in RUNNING) else "")
            print(f"    VALUE  {r['predicate']:<21} {v}{subj}{run}")
        else:
            print(f"    TERM   {r['predicate']:<21} {(r['text'] or '')[:60]}{subj}")
            if r["detail"]:
                print(f"           {'':<21} {r['detail'][:66]}")
        print(f"           {'':<21} ⤷ {r['doc']}"
              f"{' ' + r['page'] if r['page'] else ''}  [{r['evidence']}]")


def main():
    atoms = load_values() + load_terms()
    byfn = defaultdict(list)
    for a in atoms:
        byfn[a["function"]].append(a)

    print(f"DECODED ATOMS GROUPED BY FUNCTION · lot 49\n")
    print(f"  {len(atoms)} function-tagged atoms from "
          f"{len({a['doc'] for a in atoms})} documents\n")
    print(f"  {'function':<14}{'atoms':>6}{'values':>8}{'terms':>7}   "
          f"{'docs':>5}")
    for fn in sorted(byfn, key=lambda f: -len(byfn[f])):
        rs = byfn[fn]
        print(f"  {fn:<14}{len(rs):>6}"
              f"{sum(1 for r in rs if r['kind']=='VALUE'):>8}"
              f"{sum(1 for r in rs if r['kind']=='TERM'):>7}   "
              f"{len({r['doc'] for r in rs}):>5}")

    for fn in ["ENVELOPE", "ENCUMBRANCE", "DEBT", "TITLE", "VALUE", "PARCEL",
               "CONSENT", "TENANCY"]:
        narrate(fn, atoms)

    rows = [dict(bbl=L49, function=a["function"], kind=a["kind"],
                 effective=a["effective"], predicate=a["predicate"],
                 value_num=a["num"], unit=a["unit"], value_text=a["text"],
                 subject_bbl=a["subject"], document_id=a["doc"], page=a["page"],
                 evidence=a["evidence"], detail=a["detail"]) for a in atoms]
    p = HERE / f"acris_function_atoms_{L49}.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"\n\n  wrote {p.name} ({len(rows)} rows)")
    print("  every line above is emitted from an atom and carries its citation.")
    print("  ⚠ no line in this output was typed as prose — the narrative is a")
    print("    query, so it cannot drift from the data it describes.")


if __name__ == "__main__":
    main()
