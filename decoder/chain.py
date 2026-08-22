"""The financing chain — resolving SAT and ASST back to the mortgage they act on.

WHY THIS IS A LINKAGE PROBLEM, NOT A VALUATION ONE

    Measured 2026-08-06: **100% of 2,626,714 SAT and 100% of 2,207,817 ASST
    carry document_amt = 0.** They hold no money of their own. A satisfaction
    discharges *some other document*; an assignment moves *some other document*
    to a new lender. So the only question worth asking of them is WHICH ONE —
    and that is answered by the free references table, never by an image.

    SAT + ASST together are 4,834,531 documents — **28.4% of ACRIS** — and this
    module decodes all of them without fetching a single page.

THE REFERENCES TABLE (pwkr-dpni, 8,677,012 rows, free and unmetered)

    Two reference forms, and WHICH ONE IS USED DEPENDS ON THE ERA — the same
    split that governs dates (`document_date` vs `recorded_datetime`) and
    amounts (microfilm deeds report 0, microfilm mortgages do not):

        reference_by_crfn_                      modern   resolves 100% (746/747)
        reference_by_reel_year/borough/nbr/page microfilm resolves  80% (32/40)

    A decoder that reads only `reference_by_crfn_` silently drops every
    pre-electronic link — on one Manhattan block that is 487 of 1,567 references,
    31%.

★ THE CHAIN IS MULTI-HOP, WHICH IS THE WHOLE POINT

    A SAT does not reliably point at a MTGE. On Block 800 the 747 modern
    references resolved to MTGE 545, **AGMT 112, ASST 64**, M&CON 9. An
    assignment assigned onward points at the PRIOR ASSIGNMENT, not at the
    original loan.

    So `root_of()` walks transitively until it reaches a document that is not
    itself a pointer. Stopping at one hop reports the wrong lender, the wrong
    date, and — because ASST carries no amount — no amount at all.

⚠ CYCLES AND DEAD ENDS ARE REAL AND MUST NOT HANG OR LIE
    * a reference can point at a document ACRIS does not hold (20% of microfilm)
    * corrective filings can make a loop
    Both end the walk with an explicit verdict, never with a guess.
"""
import sys, pathlib
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk

REFERENCES = "pwkr-dpni"
MASTER = "bnx9-e6tj"
POINTERS = {"SAT", "ASST", "PSAT", "WSAT", "ASSTO", "ASTU"}
MAX_HOPS = 12


def references_for(doc_ids):
    """document_id -> [reference dicts]. Both forms, never just CRFN."""
    out = defaultdict(list)
    for r in bulk.socrata_in(REFERENCES, "document_id", sorted(set(doc_ids))):
        crfn = r.get("reference_by_crfn_")
        reel_n = str(r.get("reference_by_reel_nbr") or "0")
        if crfn and crfn not in ("0", ""):
            out[r["document_id"]].append({"form": "crfn", "crfn": crfn})
        elif reel_n not in ("0", ""):
            out[r["document_id"]].append(
                {"form": "reel", "year": r.get("reference_by_reel_year"),
                 "boro": r.get("reference_by_reel_borough"),
                 "nbr": reel_n, "page": r.get("reference_by_reel_page")})
        else:
            out[r["document_id"]].append({"form": "NEITHER"})
    return dict(out)


def resolve(ref):
    """One reference -> the master row it names, or None. Three forms, three
    outcomes; an unresolvable reference is reported, never skipped."""
    if ref["form"] == "crfn":
        rows = bulk.socrata(MASTER, where=f"crfn='{ref['crfn']}'", limit=2,
                            paginate=False)
    elif ref["form"] == "reel":
        rows = bulk.socrata(
            MASTER, where=(f"reel_yr='{ref['year']}' and reel_nbr='{ref['nbr']}' "
                           f"and reel_pg='{ref['page']}'"), limit=4, paginate=False)
        # a reel PAGE can hold more than one instrument; prefer a mortgage,
        # and if several remain the reference is genuinely AMBIGUOUS
        if len(rows) > 1:
            m = [r for r in rows if r.get("doc_type") == "MTGE"]
            rows = m if len(m) == 1 else rows
    else:
        return None
    if not rows:
        return None
    if len(rows) > 1:
        return {"AMBIGUOUS": [r["document_id"] for r in rows]}
    return rows[0]


def root_of(doc_id, _seen=None, _hops=0):
    """Walk a SAT/ASST back to the instrument it ultimately acts on.

    Returns the root master row plus the path taken, or an explicit verdict —
    `unresolved`, `ambiguous`, `cycle`, `too_deep`. Never a silent stop.
    """
    _seen = _seen or set()
    if doc_id in _seen:
        return {"verdict": "cycle", "path": sorted(_seen)}
    if _hops >= MAX_HOPS:
        return {"verdict": "too_deep", "path": sorted(_seen)}
    _seen.add(doc_id)

    refs = references_for([doc_id]).get(doc_id) or []
    usable = [r for r in refs if r["form"] != "NEITHER"]
    if not usable:
        return {"verdict": "no_reference", "path": sorted(_seen)}

    for ref in usable:
        got = resolve(ref)
        if got is None:
            continue
        if "AMBIGUOUS" in got:
            return {"verdict": "ambiguous", "candidates": got["AMBIGUOUS"],
                    "path": sorted(_seen)}
        t = got.get("doc_type")
        if t in POINTERS:                       # another pointer — keep walking
            deeper = root_of(got["document_id"], _seen, _hops + 1)
            if deeper.get("verdict") == "resolved":
                deeper["path"] = sorted(set(deeper["path"]) | {doc_id})
                return deeper
            continue
        return {"verdict": "resolved", "root": got, "hops": _hops + 1,
                "path": sorted(_seen | {got["document_id"]})}
    return {"verdict": "unresolved", "path": sorted(_seen)}


def close_chain(bbl):
    """Does this parcel's financing chain close? Reports what is OPEN.

    An unsatisfied mortgage is either LIVE DEBT (a finding worth money) or an
    unread satisfaction (a bug). The distinction is the point.
    """
    boro, blk, lot = bbl[0], str(int(bbl[1:6])), str(int(bbl[6:]))
    legs = bulk.socrata("8h5j-fqxa",
                        where=f"borough='{boro}' and block='{blk}' and lot='{lot}'",
                        paginate=True)
    ids = sorted({r["document_id"] for r in legs})
    if not ids:
        return {"bbl": bbl, "mortgages": 0}
    mas = bulk.socrata_in(MASTER, "document_id", ids)
    mtge = [m for m in mas if m.get("doc_type") == "MTGE"]
    ptr = [m for m in mas if m.get("doc_type") in POINTERS]

    discharged, results = set(), Counter()
    for p in ptr:
        r = root_of(p["document_id"])
        results[r["verdict"]] += 1
        if r.get("verdict") == "resolved":
            root = r["root"]
            if root.get("doc_type") == "MTGE" and p.get("doc_type") in ("SAT", "PSAT", "WSAT"):
                discharged.add(root["document_id"])
    open_debt = [m for m in mtge if m["document_id"] not in discharged]
    return {"bbl": bbl, "mortgages": len(mtge), "pointers": len(ptr),
            "verdicts": dict(results), "discharged": len(discharged),
            "OPEN": len(open_debt),
            "open_docs": [(m["document_id"], m.get("document_amt")) for m in open_debt[:8]]}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args and len(args[0]) == 10 and args[0].isdigit():
        import json
        print(json.dumps(close_chain(args[0]), indent=1))
    else:
        doc = args[0] if args else "2013081200922001"
        r = root_of(doc)
        print(f"root_of({doc}) -> {r.get('verdict')}")
        if r.get("root"):
            k = r["root"]
            print(f"   {k['doc_type']}  {k['document_id']}  "
                  f"amt={k.get('document_amt')}  crfn={k.get('crfn')}")
            print(f"   hops: {r['hops']}   path: {' -> '.join(r['path'])}")
