"""LOAD THE THREE TABLES MIGRATION 006 CREATES.

    python load_006.py --check          # what exists, what is loaded, live vs disk
    python load_006.py --all
    python load_006.py --buildings      # building_bbl   1,082,984 rows
    python load_006.py --lineage        # lot_lineage        8,563 rows
    python load_006.py --vocab          # vocabulary        ~15 rows

⚠ RUN migrations/006_extend_live_model.sql FIRST. PostgREST cannot execute DDL
and this project exposes no exec_sql RPC. `post()` refuses on a missing table
rather than reporting zero rows written as success.

⚠ IT REUSES to_supabase.post/count RATHER THAN REIMPLEMENTING THEM. Those already
carry the rules this project paid for: a 4xx batch is an UNKNOWN state and not
zero rows, and the only row count that means anything is the one read back from
the server. A second copy of that logic is a second place for it to drift.

⚠ AND THE FILTERS ARE THE MEASURED ONES, NOT NEW ONES. building_bbl is rebuilt
from _footprints.jsonl through bin_bbl's own norm_bbl and PLACEHOLDER set, so the
table that lands is byte-identical to the join that was measured at 99.4%/93.2%.
Re-deriving the filter here would let the loaded table and the measured table
disagree while both looked right.
"""
from __future__ import annotations

import json, os, pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import bin_bbl
import lexicon
from to_supabase import post, count

HERE = pathlib.Path(__file__).parent
STATE = HERE / "_load_006_state.json"
BATCH = 2000

SPEC = {
    "building_bbl": "bin",
    "lot_lineage": "from_bbl,to_bbl",
    "vocabulary": "vocab_id",
}


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save(s):
    STATE.write_text(json.dumps(s, indent=1))


def send(table, rows, resume=True):
    """Upsert in batches, resumable, reconciled against the server at the end."""
    s = state()
    done = s.get(table, 0) if resume else 0
    if done >= len(rows):
        print(f"  {table}: {done:,}/{len(rows):,} already sent")
    else:
        t0, sent = time.time(), 0
        for i in range(done, len(rows), BATCH):
            b = rows[i:i + BATCH]
            post(table, b, SPEC[table])
            sent += len(b)
            s[table] = i + len(b)
            save(s)
            if sent % (BATCH * 20) < BATCH:
                el = time.time() - t0
                print(f"    {s[table]:,}/{len(rows):,}  "
                      f"{sent/max(el,1):.0f} rows/s", flush=True)
        print(f"  {table}: sent {sent:,} in {(time.time()-t0)/60:.1f} min")
    # ⚠ SENT IS NOT LANDED.
    live = count(table)
    ok = isinstance(live, int) and live >= len(rows)
    print(f"  {table}: disk {len(rows):,} · live {live} "
          f"{'OK' if ok else '⚠ SHORTFALL — do NOT treat this as loaded'}")
    return ok


# ── building_bbl ──────────────────────────────────────────────────────────
def buildings():
    raw = HERE / "_footprints.jsonl"
    if not raw.exists():
        print("  ⚠ _footprints.jsonl absent — run bin_bbl.py first. Stop.")
        return False
    rows, seen, ph, nobbl, dupe = [], set(), 0, 0, 0
    with open(raw, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            b = str(r.get("bin") or "").strip().split(".")[0]
            if not b or not b.isdigit():
                continue
            if b in bin_bbl.PLACEHOLDER:      # ⚠ DOB's null, not a building
                ph += 1
                continue
            base = bin_bbl.norm_bbl(r.get("base_bbl"))
            if not base:
                nobbl += 1
                continue
            if b in seen:
                dupe += 1
                continue
            seen.add(b)
            rows.append({"bin": b, "base_bbl": base,
                         "mappluto_bbl": bin_bbl.norm_bbl(r.get("mappluto_bbl")),
                         "feature_code": str(r.get("feature_code") or "") or None,
                         "last_status": r.get("last_status_type")})
    print(f"building_bbl — {len(rows):,} rows "
          f"(⚠ excluded: {ph} placeholder BINs, {nobbl:,} no base_bbl, "
          f"{dupe:,} duplicate BINs)")
    return send("building_bbl", rows)


# ── lot_lineage ───────────────────────────────────────────────────────────
def lineage():
    p = HERE / "_lot_lineage.json"
    if not p.exists():
        print("  ⚠ _lot_lineage.json absent — run lot_lineage.py first. Stop.")
        return False
    d = json.loads(p.read_text(encoding="utf-8"))
    rows = [{"from_bbl": e["from"], "to_bbl": e["to"],
             "witnesses": e["witnesses"], "strength": e["strength"],
             "old_last_seen": e["old_last_seen"] or None,
             "new_first_seen": e["new_first_seen"],
             "method": "bin_witness"} for e in d["edges"]]
    strong = sum(1 for r in rows if r["strength"] == "strong")
    print(f"lot_lineage — {len(rows):,} edges ({strong} strong, "
          f"{len(rows)-strong:,} weak/single-witness)")
    print(f"  ⚠ blind before {d['blind_before']} — BIS begins 01/01/2000. "
          f"Pre-2000 lot changes are unread, not absent.")
    return send("lot_lineage", rows)


# ── vocabulary ────────────────────────────────────────────────────────────
def _cov(v):
    """Coverage and its corpus, kept together. ⚠ A rate without its denominator
    is not a rate, so measured_against is pulled out and never dropped."""
    c = dict(v.get("coverage") or {})
    against = c.pop("measured_against", None)
    parts = [f"{k} {val}" for k, val in c.items()]
    return " · ".join(parts) or None, against


def vocab():
    rows = []
    for name, v in lexicon.FUNCTIONS.items():
        cov, against = _cov(v)
        rows.append({"vocab_id": f"function:{name}", "axis": "function",
                     "reader": name.upper(),
                     "patterns": " | ".join(v["patterns"])[:2000],
                     "status": v.get("status", "proposed"),
                     "coverage": cov, "measured_against": against})
    for name, v in lexicon.MODES.items():
        cov, against = _cov(v)
        rows.append({"vocab_id": f"mode:{name}", "axis": "mode", "reader": name,
                     "patterns": " | ".join(v["patterns"])[:2000],
                     "status": v.get("status", "proposed"),
                     "coverage": cov, "measured_against": against})
    # ⚠ THE FIVE FUNCTIONS WITH NO DETECTOR ARE ROWS TOO. Absent from this table
    # they would read as "not yet considered" instead of "measured as unread".
    for f in lexicon.CANONICAL:
        if f.lower() in lexicon.FUNCTIONS:
            continue
        rows.append({"vocab_id": f"function:{f.lower()}", "axis": "function",
                     "reader": f, "patterns": None, "status": "unread",
                     "coverage": None,
                     "measured_against": "no detector exists and no ACRIS type "
                                         "expects it — sources are DOB/BSA/DOF/market"})
    rows.append({"vocab_id": "subject:signature_person", "axis": "subject",
                 "reader": "signature → person", "patterns": "By: ____, authorised signatory",
                 "status": "unread", "coverage": None,
                 "measured_against": "sits past every head read — HEAD=3..6 of N pages"})
    st = {}
    for r in rows:
        st[r["status"]] = st.get(r["status"], 0) + 1
    print(f"vocabulary — {len(rows)} readers: " +
          " · ".join(f"{k}={v}" for k, v in sorted(st.items())))
    return send("vocabulary", guard(rows))


STATUS_OK = {"proven", "weak", "proposed", "unread"}


def guard(rows):
    """⚠ REFUSE, DO NOT COERCE. `title` carried status 'untested', which the
    CHECK constraint rejects. Mapping it to the nearest legal value would have
    silently rewritten a measurement; the fix belongs in lexicon.py, so this
    stops and says which row is wrong."""
    bad = [r for r in rows if r.get("status") not in STATUS_OK]
    if bad:
        for r in bad:
            print(f"  ⚠ {r['vocab_id']} has status "
                  f"{r.get('status')!r} — not in {sorted(STATUS_OK)}")
        raise SystemExit("fix the status in lexicon.py; nothing was sent.")
    return rows


def check():
    print("TABLES (006 must be run in the SQL editor first)\n")
    disk = {}
    p = HERE / "_lot_lineage.json"
    if p.exists():
        disk["lot_lineage"] = len(json.loads(p.read_text(encoding="utf-8"))["edges"])
    j = HERE / "_bin_bbl.json"
    if j.exists():
        disk["building_bbl"] = json.loads(j.read_text(encoding="utf-8"))["counts"]["joined_bins"]
    disk["vocabulary"] = len(lexicon.FUNCTIONS) + len(lexicon.MODES) + \
        len([f for f in lexicon.CANONICAL if f.lower() not in lexicon.FUNCTIONS]) + 1
    for t in SPEC:
        live = count(t)
        d = disk.get(t, "?")
        print(f"  {t:<16}live={str(live):<14} disk={d}")
    print("\n  `ABSENT (404)` means the table does not exist — run 006 first.")


def main():
    a = set(sys.argv[1:])
    if not a or "--check" in a:
        check()
        return 0
    ok = True
    if a & {"--all", "--vocab"}:
        ok &= vocab()
    if a & {"--all", "--lineage"}:
        ok &= lineage()
    if a & {"--all", "--buildings"}:
        ok &= buildings()
    print("\nDONE" if ok else "\n⚠ AT LEAST ONE TABLE DID NOT RECONCILE")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
