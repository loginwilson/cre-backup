"""INCREMENTAL DAB REFRESH — keep parcel lineage current instead of 13 days stale.

    python lineage_refresh.py --verify            reproduce KNOWN edges, prove the rule
    python lineage_refresh.py --since 2026-08-01  pull + show what changed (no write)
    python lineage_refresh.py --refresh           pull since last edge, append

WHY THIS EXISTS. spine/dab_edges.json holds 48,157 published edges spanning
2008-05-20 .. 2026-08-05 and NOTHING REFRESHES IT — lineage appears in no routine.
DOF's DTM_ETL_DAILY_view is a DAILY etl, so staleness here is neglect, not cost.

⚠ THE EDGE RULE IS RECONSTRUCTED, SO IT IS VERIFIED BEFORE IT IS TRUSTED. DOF
publishes dab_lot (BBL + Lot_Action + TRANS_NUM) and dab_header (TRANS_NUM +
Change_Date + Change_Type); the EDGE between lots is derived by grouping a
transaction's Dropped lots to its Added/Affected lots. That derivation is MINE,
not DOF's, so --verify rebuilds a window ALREADY COVERED by dab_edges.json and
reports agreement. A wrong lineage rule does not error — it silently attaches one
parcel's history to another, the worst failure this system can have. Never
--refresh on an unverified rule.

⚠ PAGE WITH A STABLE ORDER. ArcGIS resultOffset without orderByFields has the same
defect Socrata does: rows shift between pages, so the COUNT stays right while
individual rows are dropped AND duplicated. Every page here orders by OBJECTID.

⚠ LINEAGE IS READ-TIME. Nothing here rewrites a stored BBL — lineage.py resolves at
read time ("POST to what the document names, RESOLVE at read time"). So a refresh
can never corrupt landed documents; worst case it widens or narrows what a read
gathers.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import dof_lineage as DL

EDGES = HERE / "spine" / "dab_edges.json"
PAGE = 2000


def page_query(layer, where, order="OBJECTID"):
    """Every matching row, paged with a STABLE order."""
    out, off = [], 0
    while True:
        p = {"where": where, "outFields": "*", "resultRecordCount": PAGE,
             "resultOffset": off, "orderByFields": order, "f": "json"}
        url = f"{DL.SVC}/{DL.LAYERS[layer]}/query?" + urllib.parse.urlencode(p)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=120) as f:
                    js = json.load(f)
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        feats = js.get("features") or []
        out += [f["attributes"] for f in feats]
        # ⚠ NEVER END A PAGE LOOP ON "len(feats) < requested". The SERVER caps
        # resultRecordCount at its own maxRecordCount (1,000 here) regardless of
        # what we ask for, so a full page looks like a short one and the walk
        # stops at the cap. Measured: asked 2,000, got exactly 1,000, concluded
        # "done", and rebuilt 353 of 872 edges - every one of them CORRECT, which
        # is what makes truncation so dangerous: the sample agrees perfectly and
        # the total is silently wrong. End on an EMPTY page, or on the server's
        # own exceededTransferLimit flag.
        if not feats or js.get("exceededTransferLimit") is False:
            return out
        off += len(feats)


def ms_to_date(v):
    if v in (None, ""):
        return None
    try:
        return time.strftime("%Y-%m-%d", time.gmtime(int(v) / 1000))
    except (ValueError, TypeError, OSError):
        return str(v)[:10]


def build_edges(lots, headers):
    """Group a transaction's Dropped lots -> its Added/Affected lots.

    rel follows the SHAPE of the transaction, as the existing file does:
      many -> one   merged_into
      one  -> many  apportioned_to
      else          replaced_by
    """
    hdr = {h.get("TRANS_NUM"): h for h in headers}
    by_trans = collections.defaultdict(
        lambda: {"drop": [], "affected": [], "new": []})
    for r in lots:
        t = r.get("TRANS_NUM")
        bbl = str(r.get("BBL") or "").strip()
        act = (r.get("Lot_Action") or "").strip().lower()
        if not t or not bbl:
            continue
        if act.startswith("drop"):
            by_trans[t]["drop"].append(bbl)
        elif act.startswith("affect"):
            by_trans[t]["affected"].append(bbl)
        elif act.startswith("new") or act.startswith("add"):
            by_trans[t]["new"].append(bbl)
    edges = []
    for t, g in by_trans.items():
        # ⚠ THE THREE ACTIONS ARE Dropped / Affected / New, AND "Affected" CHANGES
        # ROLE. Measured on published transactions:
        #   merger 152512        Dropped 5008240066 -> Affected 5008240068
        #   apportion 474542     Dropped {...}      -> Affected {...}
        #   apportion 628945     Affected 5008370344 -> New {343,345,342}
        # So a lot that DROPS is always a source; when nothing drops, the
        # AFFECTED lot is the parent being subdivided and NEW lots are its
        # children. Guessing a fixed mapping (my first attempt read Affected as
        # a destination and ignored New entirely) rebuilt 373 of 872 edges - and
        # every rebuilt edge AGREED, which is exactly why a wrong lineage rule is
        # dangerous: it looks perfect on what it produces and silently omits the
        # rest.
        drop = sorted(set(g["drop"]))
        aff = sorted(set(g["affected"]))
        new_ = sorted(set(g["new"]))
        src, dst = (drop, aff + new_) if drop else (aff, new_)
        src, dst = sorted(set(src)), sorted(set(dst))
        if not src or not dst:
            continue
        rel = ("merged_into" if len(src) > 1 and len(dst) == 1 else
               "apportioned_to" if len(src) == 1 and len(dst) > 1 else "replaced_by")
        h = hdr.get(t, {})
        for a in src:
            for b in dst:
                if a == b:
                    continue
                edges.append({"from": a, "to": b, "rel": rel,
                              "type": h.get("Change_Type"),
                              "date": ms_to_date(h.get("Change_Date")),
                              "trans": t})
    return edges


def key(e):
    return (e["from"], e["to"], e["trans"])


def window(since, until=None):
    w = "Change_Date >= DATE " + repr(str(since))
    if until:
        w += " AND Change_Date <= DATE " + repr(str(until))
    heads = page_query("dab_header", w)
    trans = sorted({h.get("TRANS_NUM") for h in heads if h.get("TRANS_NUM")})
    print(f"  headers {len(heads):,} · transactions {len(trans):,}")
    lots = []
    for i in range(0, len(trans), 200):
        chunk = ",".join(str(t) for t in trans[i:i + 200])
        lots += page_query("dab_lot", f"TRANS_NUM IN ({chunk})")
    print(f"  lot rows {len(lots):,}")
    return build_edges(lots, heads)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--since")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()

    have = json.loads(EDGES.read_text(encoding="utf-8"))
    dated = [e["date"] for e in have if e.get("date")]
    hi = max(dated)
    print(f"  on disk: {len(have):,} edges · through {hi}")
    known = {key(e) for e in have}

    if a.verify:
        lo = "2026-01-01"
        print(f"\n  VERIFY: rebuilding {lo} .. {hi} from DOF and comparing")
        got = window(lo, hi)
        gk = {key(e) for e in got}
        hk = {key(e) for e in have if e.get("date") and lo <= e["date"] <= hi}
        print(f"    rebuilt {len(gk):,} · on disk {len(hk):,}")
        print(f"    agree   {len(gk & hk):,}")
        print(f"    only rebuilt {len(gk - hk):,}   only on disk {len(hk - gk):,}")
        if hk and len(gk & hk) / len(hk) >= 0.98:
            print("    OK - rule reproduces the published edges; safe to --refresh")
        else:
            print("    FAIL - RULE DOES NOT REPRODUCE. Do NOT --refresh: the "
                  "derivation is wrong and would attach one parcel's history to "
                  "another.")
            for e in list(hk - gk)[:3]:
                print(f"       missed: {e}")
        return

    since = a.since or hi
    print(f"\n  pulling DAB since {since}")
    got = window(since)
    fresh = [e for e in got if key(e) not in known]
    print(f"  edges in window {len(got):,} · NEW {len(fresh):,}")
    if fresh:
        print("   ", dict(collections.Counter(e["rel"] for e in fresh)))
        print(f"    parcels retired {len({e['from'] for e in fresh}):,} -> "
              f"successors {len({e['to'] for e in fresh}):,}")
        for e in fresh[:6]:
            print(f"      {e['date']}  {e['from']} {e['rel']} {e['to']}  ({e['type']})")
    if not a.refresh:
        print("\n  --refresh not given; nothing written.")
        return
    if not fresh:
        print("  nothing new to write.")
        return
    bak = EDGES.with_suffix(".json.bak")
    bak.write_text(EDGES.read_text(encoding="utf-8"), encoding="utf-8")
    EDGES.write_text(json.dumps(have + fresh), encoding="utf-8")
    print(f"\n  {len(have):,} -> {len(have)+len(fresh):,} edges  (backup {bak.name})")


if __name__ == "__main__":
    main()
