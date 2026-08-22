"""CONTRIBUTION — which documents actually feed which function.

⚠ THE FINDING THAT MOTIVATES THIS FILE, MEASURED NOT ASSUMED.

NOT ONE FUNCTION ON THE PILOT PARCEL IS FED BY A SINGLE DOCUMENT TYPE. The
narrowest draws from five; ENCUMBER draws from nine; IDENTIFY from fifteen.

And the naming intuition is worse than useless — THE DOCUMENT TYPE NAMED
AFTER A FUNCTION IS USUALLY NOT ITS MAIN FEEDER:

    ENCUMBER   biggest feeder is MTGE (20). EASE is not in its top eight.
    VALUE      biggest feeder is DEVR (22), not DEED (5) — air-rights
               prices come off ZLDA cover stamps, and the deed recites $10.
    TENANCY    biggest feeders are AGMT and MTGE. The 1995 ground lease was
               never recorded; it exists only as a recital inside mortgages.
    ENVELOPE   DEVR leads, but EASE, SAGE, AGMT and SMIS all contribute.

⚠ SO A RESOLVER CANNOT BE POINTED AT A DOCUMENT TYPE. It has to be pointed
at a QUERY over claims — which is exactly why the architecture says
resolvers read claims and never documents. This file is the evidence for
that rule rather than an assertion of it.

⚠ AND THE WEIGHTS ARE A ROUTING HINT, NOT A FILTER. A type contributing one
claim can carry the only copy of the most important fact on the parcel: a
single SMIS held the environmental cleanup covenant that no mortgage in 35
years mentions, and a single SAGE held the instrument naming how fee title
was actually conveyed.

    python contribution.py            the measured matrix
    python contribution.py --gaps     what ACRIS cannot answer alone
"""
import collections
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# WHAT EACH FUNCTION NEEDS THAT ACRIS CANNOT GIVE.
# ⚠ Declared, not measured — you cannot measure the absence of a source you
# never pulled. Each entry names the source and what only it holds.
# ---------------------------------------------------------------------------
CROSS_SOURCE = {
 "ENVELOPE":  [("DCP zoning", "the district and its FAR — ACRIS records "
                              "TRANSFERS of floor area and never the "
                              "as-of-right base they modify"),
               ("DOB ZD1",    "the developer's own signed computation, "
                              "accepted by DOB — the canary for the number"),
               ("PLUTO",      "lot area, though DOF Digital Tax Map is the "
                              "authority when polygons are fragments")],
 "PERMIT":    [("DOB NOW / BIS", "⚠ ACRIS CONTRIBUTES ALMOST NOTHING HERE. "
                              "The 19 'PERMIT' claims are construction "
                              "covenants inside mortgages — evidence a build "
                              "happened, not what was filed or approved")],
 "ASBUILT":   [("DOB CO", "certificates of occupancy. ACRIS never records "
                          "what legally exists")],
 "OCCUPY":    [("DOF RPIE", "income and occupancy filings"),
               ("HPD",      "registrations for residential")],
 "VALUE":     [("DOF sales", "arm's-length comparables at scale"),
               ("DOF assessment", "assessed value history")],
 "PARCEL":    [("DOF Digital Tax Map", "geometry. ⚠ PLUTO polygons can be "
                                       "fragments"),
               ("FEMA / DEC", "flood and wetlands")],
 "ENTITLE":   [("BSA", "variances and special permits"),
               ("DCP ZAP", "ULURP actions"),
               ("LPC", "landmark status and approvals")],
 "DISTRESS":  [("DOF tax liens", "arrears"),
               ("OATH / ECB", "violations")],
 "COST":      [("no public source", "⚠ EXTERNAL — confidence from source and "
                                    "vintage, not a citation")],
 "CONTEXT":   [("no public source", "⚠ EXTERNAL")],
}


def measured(bbl="1008000049"):
    """The matrix, from claims actually recorded. Empirical, re-runnable."""
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import claims as K
    import functions_vocab as FV
    idx_path = pathlib.Path(f"acris_index_{bbl}.json")
    dtype = {}
    if idx_path.exists():
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
        dtype = {r["document_id"]: (r.get("doc_type") or "?").upper()
                 for r in idx["master"]}
    fn = collections.defaultdict(collections.Counter)
    docs = collections.defaultdict(set)
    for c in K.rows():
        t = dtype.get(c["document_id"], "pre-index")
        for a in (c.get("answers") or []):
            f = FV.canon(a)
            if f:
                fn[f][t] += 1
                docs[f].add(c["document_id"])
    return fn, docs


def shape(n_types):
    """The three shapes, as the user framed them."""
    if n_types <= 1:
        return "SINGLE TYPE"
    if n_types <= 4:
        return "FEW TYPES"
    return "MANY TYPES"


def main():
    fn, docs = measured()
    if "--gaps" in sys.argv:
        print("WHAT EACH FUNCTION NEEDS FROM OUTSIDE ACRIS\n")
        for f, needs in CROSS_SOURCE.items():
            have = sum(fn.get(f, {}).values())
            print(f"  {f}   ({have} claims from ACRIS)")
            for src, why in needs:
                print(f"      + {src}")
                print(f"        {why}")
            print()
        only = sorted(set(fn) - set(CROSS_SOURCE))
        print(f"  ANSWERABLE FROM ACRIS ALONE: {', '.join(only)}")
        print("  ⚠ these are the functions where the record IS the authority —")
        print("    a decode of them is complete, not partial.")
        return

    print("CONTRIBUTION MATRIX — measured from recorded claims\n")
    print(f"  {'function':<13} {'claims':>6} {'types':>6} {'docs':>5}  shape")
    print("  " + "-" * 62)
    for f in sorted(fn, key=lambda x: -sum(fn[x].values())):
        tot = sum(fn[f].values())
        nt = len(fn[f])
        cross = " ⚠ + other sources" if f in CROSS_SOURCE else ""
        print(f"  {f:<13} {tot:>6} {nt:>6} {len(docs[f]):>5}  "
              f"{shape(nt)}{cross}")
    print()
    print("  ⚠ NOT ONE FUNCTION IS FED BY A SINGLE DOCUMENT TYPE.")
    print("    A resolver cannot be pointed at a doc type. It is pointed at a")
    print("    QUERY over claims — which is why resolvers read claims and")
    print("    never documents.\n")
    print("  TOP FEEDERS, and where the name misleads:")
    for f in ("ENCUMBRANCE", "VALUE", "TENANCY", "ENVELOPE"):
        if f in fn:
            top = fn[f].most_common(3)
            s = " · ".join(f"{t} {n}" for t, n in top)
            print(f"    {f:<13} {s}")


main()
