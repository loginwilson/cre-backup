"""regfields.py — registration key inventory, stratified by (source, doc_type).

The corpus half of the registry-field-coverage check (RULINGS-v1.md R-4 as
generalised, R-9's sibling). The failure it targets has no other signal: an
adapter that silently ignores a registration key it was not written for produces
output that looks complete. `references[]` proved a whole pointer class can hide
in a field nobody looked at.

    python regfields.py                      # inventory to stdout + JSON
    python regfields.py --per-cell 200 --out inventory.json

WHY (source, doc_type) AND NOT doc_type
    Pooling by type across sources produces rows like
    `SAT  n=3111  book, image_state, instrument, page, status` — which is
    Richmond's key set wearing an ACRIS heading, because only Richmond uses the
    label `SAT`. Every one of those keys is a Richmond key and none of them is
    evidence about ACRIS. Type labels are not shared across registries (R-7), so
    a type-keyed inventory silently merges four schemas.

WHY A PER-CELL CAP AND NOT A UNIFORM SAMPLE
    Novel field sets live in RARE types. `references[]`, `collateral` and
    `expiration` are UCC3 fields; UCC3 TERMINATION is 28,761 rows against
    MORTGAGE's 170,362. A uniform sample spends its budget on mortgages and
    finds nothing new. Capping per cell buys coverage of every type at a fixed
    cost, which is the opposite of what frequency-weighted sampling does.

WHY RARITY-SORTED OUTPUT
    A key on 0.1% of rows is the interesting one — `pct` on 14 ACRIS rows is
    almost certainly a fractional interest, and fractional interests are exactly
    what R-PARTY shares rules turn on. An inventory sorted by frequency buries
    what it exists to surface, so the default report is sorted by scarcity.

NESTED PATHS, NOT TOP-LEVEL KEYS
    Every pointer class found so far is nested: `parties[].role`,
    `parcels[].remarks`, `references[].file_nbr`. Top-level keys alone would
    have shown `references` present and told you nothing about the four distinct
    pointer forms inside it.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sqlite3
import sys
import time

DECODER = pathlib.Path(r"C:\Users\smile\Downloads"
                       r"\Source Folder (Real Estate Data)"
                       r"\Decoder Prompt\decoder")
sys.path.insert(0, str(DECODER))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                     # noqa: E402

SLATE = pathlib.Path(r"D:\CRE Decoding System\04 Extractions\loop\ledger\slate.db")
TYPE_CONDITIONAL = 0.90          # present on under 90% of a cell


def paths(obj, prefix="") -> set[str]:
    """Key paths one level into lists: `parties[].role`, not `parties[0].role`."""
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = "%s%s" % (prefix, k)
            out.add(p)
            if isinstance(v, (dict, list)):
                out |= paths(v, p + ("[]." if isinstance(v, list) else "."))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                out |= paths(item, prefix)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-cell", type=int, default=200)
    ap.add_argument("--out", default="regfields-inventory.json")
    a = ap.parse_args()

    s = sqlite3.connect("file:%s?mode=ro" % SLATE, uri=True)
    cells = s.execute("SELECT source, doc_type, COUNT(*) FROM slate "
                      "GROUP BY source, doc_type ORDER BY source, doc_type"
                      ).fetchall()

    n = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
    n.execute("PRAGMA busy_timeout=30000")

    inv, t0, read = {}, time.time(), 0
    for src, dt, total in cells:
        ids = [r[0] for r in s.execute(
            "SELECT id FROM slate WHERE source=? AND doc_type IS ? "
            "ORDER BY bucket LIMIT ?", (src, dt, a.per_cell))]
        seen, counts = 0, collections.Counter()
        for did in ids:
            r = n.execute("SELECT recorded_details FROM navigation WHERE id=?",
                          (did,)).fetchone()
            read += 1
            if not r or not r[0]:
                continue
            try:
                d = json.loads(r[0])
            except Exception:
                continue
            seen += 1
            for p in paths(d):
                counts[p] += 1
        if not seen:
            continue
        inv["%s\t%s" % (src, dt)] = {
            "source": src, "doc_type": dt, "cell_rows": total,
            "sampled": seen,
            "paths": {p: c / seen for p, c in sorted(counts.items())},
        }
        # >> stay polite: the reproduction lanes are the critical path
        if read % 2000 == 0:
            print("  %d reads, %d cells, %.1f min"
                  % (read, len(inv), (time.time() - t0) / 60), flush=True)
            time.sleep(1.0)

    pathlib.Path(a.out).write_text(json.dumps(inv, indent=1), encoding="utf-8")

    # ---- report -------------------------------------------------------------
    cells_by_path = collections.defaultdict(list)
    for key, rec in inv.items():
        for p, frac in rec["paths"].items():
            cells_by_path[p].append((rec["source"], rec["doc_type"], frac,
                                     rec["sampled"]))

    print("\n== KEY PATHS BY SCARCITY (rarest first — the interesting end) ==")
    print("%-34s %6s %8s   %s" % ("path", "cells", "max%", "where"))
    for p, where in sorted(cells_by_path.items(), key=lambda kv: (len(kv[1]), kv[0])):
        top = max(where, key=lambda w: w[2])
        loc = "%s/%s" % (top[0], top[1])
        if len(where) > 1:
            loc += " +%d more" % (len(where) - 1)
        print("%-34s %6d %7.1f%%   %s" % (p, len(where), top[2] * 100, loc))

    print("\n== TYPE-CONDITIONAL WITHIN A CELL (<%.0f%% of sampled rows) =="
          % (TYPE_CONDITIONAL * 100))
    print("A key absent from some rows of ONE (source, doc_type) cell is not")
    print("type-conditional — it is row-conditional, and an adapter that")
    print("assumes it is present has no symptom when it is not.")
    for key, rec in sorted(inv.items()):
        thin = {p: f for p, f in rec["paths"].items() if f < TYPE_CONDITIONAL}
        if thin:
            print("  %s/%s (n=%d): %s" % (
                rec["source"], rec["doc_type"], rec["sampled"],
                ", ".join("%s %.0f%%" % (p, f * 100)
                          for p, f in sorted(thin.items(), key=lambda kv: kv[1]))))

    print("\ncells=%d  reads=%d  %.1f min  ->  %s"
          % (len(inv), read, (time.time() - t0) / 60, a.out))
    print("\nNOT A CHECK YET. This is the corpus half. The check is the DIFF")
    print("against the paths each v1 adapter declares it consumes; the")
    print("unconsumed set is the deliverable.")


if __name__ == "__main__":
    main()
