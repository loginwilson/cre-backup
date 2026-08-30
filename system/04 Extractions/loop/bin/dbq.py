"""dbq.py — read-only query against the Legal Instruments navigation table.

    python dbq.py "SELECT id, pdf FROM navigation WHERE id > '2016' ORDER BY id LIMIT 20"
    python dbq.py --json "SELECT recorded_details FROM navigation WHERE id = '...'"
    python dbq.py --type "DEED"        sample readable rows of one instrument type
    python dbq.py --row  <id>          the whole row for one id, readable

Opens read-only with busy_timeout, per DOCUMENT ACCESS.md §6.  The register
lane writes continuously; without the timeout a lock error surfaces as
"database is locked", which looks exactly like a missing document and is not.

THREE THINGS THIS GUARDS
  - No unbounded scans. A 24M-row COUNT(*) stalls WAL checkpointing and starves
    the reproduction lanes — measured 2026-08-29, a 0.14 s count took 112 s and
    made the board print a negative rate. Queries without LIMIT are refused
    unless you pass --unbounded and mean it.
  - ORDER BY is required alongside LIMIT. Unordered paging silently drops and
    duplicates rows.
  - LIKE 'RC_%' degrades to a full scan ('_' is a single-char wildcard). Use
    the range form:  id >= 'RC_' AND id < 'RC`'
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sqlite3
import sys
import time

DECODER = pathlib.Path(r"C:\Users\smile\Downloads"
                       r"\Source Folder (Real Estate Data)"
                       r"\Decoder Prompt\decoder")
sys.path.insert(0, str(DECODER))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                     # noqa: E402


def conn() -> sqlite3.Connection:
    c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
    c.execute("PRAGMA busy_timeout=30000")
    return c


def guard(sql: str, unbounded: bool) -> None:
    low = sql.lower()
    if not low.lstrip().startswith(("select", "pragma", "explain")):
        sys.exit("read-only: SELECT / PRAGMA / EXPLAIN only")
    if unbounded:
        return
    if " limit " not in low:
        sys.exit("refused: no LIMIT. 24M rows — an unbounded scan starves the\n"
                 "reproduction lanes. Add LIMIT, or --unbounded if you mean it.")
    if " order by " not in low:
        sys.exit("refused: LIMIT without ORDER BY. Unordered paging silently\n"
                 "drops and duplicates rows. Order by id.")
    if re.search(r"like\s+'rc_%'", low):
        sys.exit("refused: LIKE 'RC_%' is a full scan — '_' is a wildcard.\n"
                 "Use  id >= 'RC_' AND id < 'RC`'")


def run(sql: str, as_json: bool, unbounded: bool) -> None:
    guard(sql, unbounded)
    c = conn()
    t = time.time()
    cur = c.execute(sql)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    dt = time.time() - t

    if as_json:
        print(json.dumps([dict(zip(cols, r)) for r in rows], indent=2))
    else:
        print(" | ".join(cols))
        for r in rows:
            print(" | ".join("" if v is None else str(v) for v in r))
    print("\n-- %d rows, %.2fs" % (len(rows), dt), file=sys.stderr)


def one_row(did: str) -> None:
    c = conn()
    r = c.execute("SELECT id, recorded_details, pdf FROM navigation "
                  "WHERE id = ?", (did,)).fetchone()
    if r is None:
        sys.exit("no such id: %s" % did)
    did, rd, pdf = r
    print("id           ", did)
    print("pdf          ", pdf)
    path = CP.doc_path(pdf)
    print("resolved     ", path if path else "(state, not a file)")
    if path:
        print("exists       ", path.exists())
    print("registration ")
    print(json.dumps(json.loads(rd), indent=2))


def by_type(t: str, n: int) -> None:
    # >> recorded_details is a JSON blob; there is no type column, so this is a
    #    scan by necessity. Keep n small and it stops early.
    c = conn()
    sql = ("SELECT id, recorded_details FROM navigation "
           "WHERE pdf LIKE '%.pdf' AND recorded_details LIKE ? "
           "ORDER BY id LIMIT ?")
    for did, rd in c.execute(sql, ('%"type": "%s"%' % t, n)):
        d = json.loads(rd)
        print("%s  %-38s %-10s %s pages  %s parcels  %s parties" % (
            did, d.get("type", ""), d.get("doc_date", ""), d.get("pages", "?"),
            len(d.get("parcels", [])), len(d.get("parties", []))))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sql", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--unbounded", action="store_true")
    ap.add_argument("--row", help="print one whole row, readable")
    ap.add_argument("--type", help="sample readable rows of an instrument type")
    ap.add_argument("-n", type=int, default=20)
    a = ap.parse_args()

    if a.row:
        one_row(a.row)
    elif a.type:
        by_type(a.type, a.n)
    elif a.sql:
        run(a.sql, a.json, a.unbounded)
    else:
        ap.error("give SQL, --row <id>, or --type <TYPE>")


if __name__ == "__main__":
    main()
