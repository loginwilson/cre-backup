"""WHICH LOTS ARE THIS PARCEL, ACROSS TIME? The resolver the walk reads through.

    python lineage.py --bbl 1010381002          # what it absorbed, and when
    python lineage.py --audit                   # the count, corrected for lineage

⚠ WHY THIS EXISTS. Login, 2026-08-17 22:15: *"make sure that parcel count is right for
lineage where parcels may change over time like 10 parcels becoming a single condo lot
or 1 lot subdividing to 10 or 10 merging to 1."* Measured against DOF's Digital
Alteration Book the same night: **24,419 of the 1,250,935 BBLs ACRIS has ever attached
to are identities DOF has since superseded.** Walking one of those as a live parcel
reads a closed story; walking its successor without it loses the beginning.

    1010381002  absorbs 121 lots
    1002481004  becomes 816 lots

⚠ A BBL IS A NAME, NOT A PLACE. The rule the spine already states — *POST to what the
document names, RESOLVE at read time* — is what this implements. Nothing here rewrites
a document's stated BBL. Acquisition keeps filing under the name on the instrument;
this decides which names to gather when a parcel is READ.

⚠ EDGES ARE PUBLISHED, NOT INFERRED. Source is DOF's DAB (`spine/dab_edges.json`,
48,157 edges: 26,415 merged_into · 19,278 apportioned_to · 2,464 replaced_by), pulled
by dof_lineage.py. The earlier BIN-witness approach in lot_lineage.py infers lineage
from buildings and is BLIND BEFORE 2000; it stays a cross-check, not the authority.

⚠ DIRECTION MATTERS AND THE TWO ARE NOT SYMMETRIC.
    predecessors(X)  lots that BECAME X — their documents are X's early history
    successors(X)    what X became — if non-empty, X is a retired name
A merger has many predecessors and one successor. An apportionment has one predecessor
and many successors, and there the parent's documents are shared history for every
child: the 816 lots out of 1002481004 each inherit the same parent record, and that is
correct, not duplication.

⚠ CYCLES EXIST IN THE PUBLISHED DATA. Re-apportionments can name a lot that later
names them back. Every walk carries a visited set; without it the closure never
returns.
"""
from __future__ import annotations

import argparse, collections, json, os, pathlib, sqlite3, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).parent
ROOT = pathlib.Path(os.environ.get("ACRIS_CORPUS_ROOT", str(HERE)))
EDGES = HERE / "spine" / "dab_edges.json"
SPEC = ROOT / "01-specification" / "parcel_spec.db"

_FWD = _REV = _META = None


def _load():
    """⚠ Built once per process. 48k edges is trivial in memory and a per-parcel
    re-read would dominate a 1.25M-parcel audit."""
    global _FWD, _REV, _META
    if _FWD is not None:
        return
    _FWD = collections.defaultdict(set)
    _REV = collections.defaultdict(set)
    _META = {}
    if not EDGES.exists():
        return
    for e in json.load(open(EDGES, encoding="utf-8")):
        f, t = e.get("from"), e.get("to")
        if not f or not t or f == t:
            continue
        _FWD[f].add(t)
        _REV[t].add(f)
        _META[(f, t)] = (e.get("rel", ""), e.get("type", ""), e.get("date", ""))
    _load_instrument_edges()


def _load_instrument_edges():
    """⚠ DOF'S DAB LAGS, SO NEW LOTS HAVE NO PUBLISHED EDGE — AND "NO EDGE"
    MUST NEVER READ AS "NO PREDECESSOR". Measured 2026-08-18: of 153 parcels
    created by the live delta, 132 were condo unit lots (lot >= 1001) and ALL
    132 had no DAB edge, because DOF publishes the Alteration Book on its own
    cycle and these lots are days old. The live sync now runs ahead of the
    lineage source exactly as it runs ahead of the Socrata extract.

    But the edge is not missing — it is in the DOCUMENT. A condominium
    declaration (CDEC) and its map (MAPS) name the development lot AND the unit
    lots in one property table, so the instrument that CAUSED the split states
    it at the moment it happens, with a document_id to cite.

    ⚠ ONLY CREATION INSTRUMENTS WRITE AN EDGE. A MTGE / AGMT / ASST / TERA can
    name a development lot and its units together without establishing any
    lineage — a mortgage covering both is not an apportionment. Those rows are
    kept as `instrument-corroborating` and are NOT loaded here; treating them as
    creation would invent parents (188 TERA rows would have done exactly that).

    ⚠ DAB REMAINS THE AUTHORITY WHERE IT SPEAKS. These edges fill the window
    before publication. When DAB catches up, disagreement is a FINDING worth
    seeing, not something to overwrite silently.
    """
    if not SPEC.exists():
        return
    try:
        con = sqlite3.connect(f"file:{SPEC}?mode=ro", uri=True)
        rows = con.execute(
            "SELECT child, parent, doc_type, recorded_date, document_id "
            "FROM lineage_edge WHERE source = 'instrument-creation'").fetchall()
        con.close()
    except sqlite3.Error:
        return                      # table not built yet — DAB alone still works
    for child, parent, dt, date, doc in rows:
        if not child or not parent or child == parent:
            continue
        _FWD[parent].add(child)
        _REV[child].add(parent)
        _META.setdefault((parent, child),
                         ("apportioned_to", f"instrument:{dt}:{doc}", date or ""))


def _walk(start, graph, hops):
    """Transitive closure with a visited set. ⚠ `hops` bounds a pathological chain;
    it is a guard, not a model of how deep lineage goes."""
    _load()
    seen, front, out = {start}, {start}, []
    for _ in range(hops):
        nxt = set()
        for b in front:
            for o in graph.get(b, ()):
                if o not in seen:
                    seen.add(o); nxt.add(o); out.append((o, b))
        if not nxt:
            break
        front = nxt
    return out


def predecessors(bbl, hops=6):
    """Lots that became `bbl`. Their documents are this parcel's earlier history."""
    _load()                    # ⚠ the globals are the graph; binding them as an
    return _walk(bbl, _REV, hops)   # argument before _load() passes None


def successors(bbl, hops=6):
    """What `bbl` became. Non-empty means `bbl` is a RETIRED name."""
    _load()
    return _walk(bbl, _FWD, hops)


def edge_note(a, b):
    _load()
    rel, ty, dt = _META.get((a, b)) or _META.get((b, a)) or ("", "", "")
    return f"{rel or ty}{(' ' + dt) if dt else ''}".strip()


def family(bbl, hops=6):
    """Every BBL whose documents belong to this parcel's record: itself plus every
    predecessor. ⚠ Successors are NOT included — those are a different, later parcel."""
    return [bbl] + [b for b, _ in predecessors(bbl, hops)]


def audit():
    _load()
    if not SPEC.exists():
        sys.exit(f"  no spec db at {SPEC}")
    con = sqlite3.connect(SPEC)
    acris = {r[0] for r in con.execute("select bbl from parcel")}
    docs = dict(con.execute("select bbl, n_docs from parcel"))
    con.close()

    retired = acris & set(_FWD)
    absorbers = acris & set(_REV)
    print(f"  ACRIS BBLs (parcels ever named)     {len(acris):,}")
    print(f"  ⚠ retired names (DOF superseded)    {len(retired):,}")
    print(f"  live names that absorbed a lot      {len(absorbers):,}")
    print(f"  LINEAGE-AWARE distinct parcels      {len(acris) - len(retired):,}")

    d_ret = sum(docs.get(b, 0) for b in retired)
    print(f"\n  ⚠ documents filed under a retired name: {d_ret:,}")
    print("     — invisible to any walk keyed on the current BBL alone")

    deep = sorted(((len(family(b)) - 1, b) for b in absorbers), reverse=True)[:8]
    print("\n  parcels whose record spans the most predecessor names:")
    for n, b in deep:
        print(f"    {b}  +{n:>4} predecessor lots  ({docs.get(b,0):,} docs of its own)")
    return len(acris) - len(retired)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bbl")
    ap.add_argument("--audit", action="store_true")
    a = ap.parse_args()
    if a.audit:
        audit(); return
    if not a.bbl:
        ap.error("--bbl or --audit")
    b = a.bbl.strip()
    pre, suc = predecessors(b), successors(b)
    print(f"  BBL {b}")
    print(f"  successors ({len(suc)}) — non-empty means this name is RETIRED:")
    for x, via in suc[:10]:
        print(f"    -> {x}   {edge_note(via, x)}")
    print(f"  predecessors ({len(pre)}) — their documents are this parcel's early record:")
    for x, via in pre[:15]:
        print(f"    <- {x}   {edge_note(x, via)}")
    if len(pre) > 15:
        print(f"    … and {len(pre)-15} more")


if __name__ == "__main__":
    main()
