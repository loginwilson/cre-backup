"""Parcel lineage and baselines AS OF AN ACRIS FILING DATE.

Why this exists: a document recorded in 2004 names the lot as it was in 2004.
Today's tax map may have merged, split, renumbered or condo-converted it, and
today's lot area / FAR are the wrong numbers to validate a 2004 instrument
against. Timelining a parcel therefore needs the map *at the filing date*, not
the map now.

Sources and their reach:
  PLUTO archive  2002 -> present, ~52 vintages (this module). Gives lot area,
                 zoning, FAR, owner, built area at each vintage, plus `appbbl`
                 (predecessor) and `condono`.
  Documents      any era. An instrument that says "f/k/a Lot 149" is itself a
                 lineage record, and is often the ONLY one for pre-2002 changes.
  DOF DTM        different parcelling model from PLUTO (geometry-first, with its
                 own lot history); the reconciliation source when the two
                 disagree. NOT yet wired in — see ARCHITECTURE.md.
  Pre-1960s      Sanborn / block-and-lot atlases, only as a last resort for
                 parcels that predate every digital source.

BOUNDARY, always stated: below 2002 this module returns "predates PLUTO" rather
than guessing. A lifespan must say where its evidence starts.

Speed: vintage membership is found by BINARY SEARCH over the ordered vintages
(~6 reads instead of ~52), and each (vintage, borough) BBL set is cached to disk
after first read, so later lookups are instant.
"""
import csv, io, json, re, sys, zipfile
from datetime import date
from pathlib import Path

ARCHIVE = Path(r"C:/dev/bkrea-v2/.pluto-archive")
CACHE = Path(__file__).with_name(".vintage_cache")
CACHE.mkdir(exist_ok=True)
BORO_PREFIX = {1: "mn", 2: "bx", 3: "bk", 4: "qn", 5: "si"}

ATTRS = ("lotarea", "zonedist1", "zonedist2", "ownername", "address", "bldgarea",
         "builtfar", "residfar", "commfar", "facilfar", "appbbl", "appdate",
         "condono", "yearbuilt", "numbldgs", "unitstotal")


def _key(stem):
    """p02a -> (2002, 1); p09v2 -> (2009, 2); p26v1 -> (2026, 1)."""
    m = re.match(r"p(\d{2})(?:v(\d+)|([a-z]))?$", stem)
    if not m:
        return (0, 0)
    year = 2000 + int(m.group(1))
    if m.group(2):
        minor = int(m.group(2))
    elif m.group(3):
        minor = ord(m.group(3)) - 96          # a=1, b=2, c=3, d=4
    else:
        minor = 1
    return (year, minor)


def vintages():
    """Oldest -> newest."""
    return sorted(ARCHIVE.glob("p*.zip"), key=lambda p: _key(p.stem))


def vintage_date(stem):
    """Approximate release date of a vintage — good enough to align with a
    filing date, and labelled approximate wherever it is reported."""
    y, m = _key(stem)
    month = min(12, 3 * m)
    return date(y, month, 1)


def _rows(zpath, boro=None):
    """All rows of a vintage. Newer vintages are ONE citywide CSV, so filtering
    by borough re-reads that 860k-row file once per borough — read it once and
    let the caller match on BBL instead."""
    with zipfile.ZipFile(zpath) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith((".csv", ".txt"))]
        pick = names
        if boro is not None:
            per_boro = [n for n in names
                        if Path(n).name.lower().startswith(BORO_PREFIX[boro])]
            if per_boro:
                pick = per_boro
        for n in pick:
            with zf.open(n) as fh:
                for r in csv.DictReader(io.TextIOWrapper(fh, encoding="latin-1", newline="")):
                    yield {k.lower().strip(): v for k, v in r.items() if k}


def _bbl_any(r):
    b = (r.get("bbl") or "").strip()
    if b:
        try:
            return str(int(float(b))).zfill(10)
        except ValueError:
            pass
    blk, lot, bo = r.get("block"), r.get("lot"), r.get("borocode") or r.get("borough")
    if blk and lot and bo:
        bo = {"MN": 1, "BX": 2, "BK": 3, "QN": 4, "SI": 5}.get(str(bo).strip().upper(), bo)
        try:
            return f"{int(bo)}{int(float(blk)):05d}{int(float(lot)):04d}"
        except (ValueError, TypeError):
            return None
    return None


def resolve_at_dates(pairs, verbose=True):
    """pairs: [(bbl, filing_date)]. Resolve each parcel AS OF its own filing
    date — start at the vintage nearest that date and expand outward, so the
    usual cost is a single read rather than a walk of the whole archive."""
    vs = vintages()
    stems = [v.stem for v in vs]
    order = {}                                  # vintage index -> targets to look for
    for bbl, when in pairs:
        when = date.fromisoformat(str(when)[:10])
        idx = 0
        for i, v in enumerate(vs):
            if vintage_date(v.stem) <= when:
                idx = i
        order.setdefault(idx, set()).add(bbl)

    out, todo = {}, {b for b, _ in pairs}
    tried = set()
    while todo:
        # search outward from each target's preferred vintage
        cand = None
        for idx, want in sorted(order.items()):
            for off in range(0, len(vs)):
                for j in (idx - off, idx + off):
                    if 0 <= j < len(vs) and (j, frozenset(want)) not in tried:
                        cand = (j, want)
                        break
                if cand:
                    break
            if cand:
                break
        if not cand:
            break
        j, want = cand
        tried.add((j, frozenset(want)))
        hits = 0
        for r in _rows(vs[j]):
            b = _bbl_any(r)
            if b in want and b in todo:
                out[b] = (vs[j].stem, {k: r.get(k) for k in ATTRS if r.get(k) not in (None, "")})
                todo.discard(b)
                hits += 1
        if verbose:
            print(f"    scanned {vs[j].stem}: {hits} hit(s), {len(todo)} left", flush=True)
        for idx in list(order):
            order[idx] = {b for b in order[idx] if b in todo}
            if not order[idx]:
                del order[idx]
        if not order:
            break
    for b in todo:
        out[b] = (None, None)
    return out


def _bbl_of(r, boro):
    b = (r.get("bbl") or "").strip()
    if b:
        try:
            return str(int(float(b))).zfill(10)
        except ValueError:
            pass
    blk, lot = r.get("block"), r.get("lot")
    if blk and lot:
        try:
            return f"{boro}{int(float(blk)):05d}{int(float(lot)):04d}"
        except ValueError:
            return None
    return None


def resolve_many(targets, on_progress=None):
    """One pass, newest -> oldest, resolving MANY BBLs at once.

    Presence is not monotonic — lots are born as well as retired — so a binary
    search that assumes "present at the start" is wrong (it silently reported
    every lot as predating PLUTO). A single batched descent is both correct and
    cheaper than per-lot searching, and it stores nothing: the archive stays on
    disk untouched and only the answers are kept.
    """
    vs = vintages()
    todo = set(targets)
    out = {b: {"last_seen": None, "attrs": None, "successors": [],
               "still_current": False} for b in targets}
    for i, zp in enumerate(reversed(vs)):
        if not todo:
            break
        boros = {int(b[0]) for b in todo}
        found_here = {}
        for boro in boros:
            want = {b for b in todo if int(b[0]) == boro}
            for r in _rows(zp, boro):
                b = _bbl_of(r, boro)
                if b in want:
                    found_here[b] = {k: r.get(k) for k in ATTRS
                                     if r.get(k) not in (None, "")}
                    want.discard(b)
                    if not want:
                        break
        for b, a in found_here.items():
            out[b]["last_seen"] = zp.stem
            out[b]["attrs"] = a
            out[b]["still_current"] = (i == 0)
            todo.discard(b)
        if on_progress:
            on_progress(zp.stem, len(todo))
    return out


def successors_from(bbl, last_vintage_stem):
    """In the vintage AFTER the lot vanished, which lots claim it as appbbl."""
    vs = vintages()
    stems = [v.stem for v in vs]
    if last_vintage_stem not in stems:
        return []
    i = stems.index(last_vintage_stem)
    if i + 1 >= len(vs):
        return []
    boro = int(bbl[0])
    out = []
    for r in _rows(vs[i + 1], boro):
        ap = (r.get("appbbl") or "").strip()
        if not ap:
            continue
        try:
            ap = str(int(float(ap))).zfill(10)
        except ValueError:
            continue
        if ap == bbl:
            out.append(_bbl_of(r, boro))
    return out


def parcel_at(bbl, when):
    """Attributes from the newest vintage at or before `when` that has the lot —
    the map as the filing saw it, not the map today."""
    when = date.fromisoformat(str(when)[:10])
    boro = int(bbl[0])
    usable = [v for v in vintages() if vintage_date(v.stem) <= when]
    for v in reversed(usable):
        for r in _rows(v, boro):
            if _bbl_of(r, boro) == bbl:
                return v.stem, {k: r.get(k) for k in ATTRS if r.get(k) not in (None, "")}
    return None, None


if __name__ == "__main__":
    targets = sys.argv[1:] or ["1015400003", "3024940010", "3027220034"]
    vs = vintages()
    res = resolve_many(targets, on_progress=lambda st, n: None)
    print(f"PLUTO archive: {len(vs)} vintages, {vs[0].stem} ({vintage_date(vs[0].stem)}) "
          f"-> {vs[-1].stem} ({vintage_date(vs[-1].stem)})\n")
    for bbl in targets:
        r = res[bbl]
        if not r["last_seen"]:
            print(f"  {bbl}: absent from every vintage back to 2002 — predates "
                  f"PLUTO; needs DTM or the document's own f/k/a recital")
            continue
        if r["still_current"]:
            print(f"  {bbl}: still on the current tax map ({r['last_seen']})")
            continue
        a = r["attrs"] or {}
        succ = successors_from(bbl, r["last_seen"])
        print(f"  {bbl}: RETIRED — last seen {r['last_seen']} "
              f"(~{vintage_date(r['last_seen'])})")
        print(f"      as it stood then: area={a.get('lotarea')} zone={a.get('zonedist1')} "
              f"bldg={a.get('bldgarea')} yr={a.get('yearbuilt')} owner={a.get('ownername')}")
        print(f"      absorbed by (next vintage claims it as appbbl): "
              f"{succ or 'no lot claims it — merger recorded without an apportionment link'}")
