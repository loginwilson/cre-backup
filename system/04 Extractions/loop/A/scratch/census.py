"""Sampled type census over the navigation table.

Bounded id-range walks only — no full scans (DOCUMENT ACCESS.md 6).
Each probe walks the PK index forward from a start id and stops after N rows.
"""
from __future__ import annotations

import collections
import json
import pathlib
import sqlite3
import sys

DECODER = pathlib.Path(r"C:\Users\smile\Downloads"
                       r"\Source Folder (Real Estate Data)"
                       r"\Decoder Prompt\decoder")
sys.path.insert(0, str(DECODER))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                     # noqa: E402

c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
c.execute("PRAGMA busy_timeout=30000")

STARTS = [
    "2002", "2004", "2006", "2008", "2010", "2012",
    "2014", "2016", "2018", "2020", "2022", "2024", "2025",
    "BK_", "FT_", "RC_", "RC_5", "RC_9",
]
N = 400

tally = collections.Counter()
by_type = collections.defaultdict(list)
multiparcel = []
multiparty = []
total = 0

for s in STARTS:
    rows = c.execute(
        "SELECT id, recorded_details, pdf FROM navigation "
        "WHERE id >= ? ORDER BY id LIMIT ?", (s, N)).fetchall()
    for did, rd, pdf in rows:
        if not pdf or not pdf.endswith(".pdf"):
            continue
        try:
            d = json.loads(rd) if rd else {}
        except Exception:
            continue
        t = d.get("type", "(none)")
        tally[t] += 1
        total += 1
        np_ = len(d.get("parcels", []))
        nq = len(d.get("parties", []))
        if len(by_type[t]) < 6:
            by_type[t].append((did, d.get("pages"), np_, nq,
                               d.get("doc_date"), d.get("amount")))
        if np_ >= 3:
            multiparcel.append((did, t, np_, nq))
        if nq >= 5:
            multiparty.append((did, t, np_, nq))

print("== SAMPLED TYPE CENSUS (%d readable rows) ==" % total)
for t, n in tally.most_common(80):
    print("%5d  %s" % (n, t))

print("\n== EXAMPLES PER TYPE  (id, pages, parcels, parties, doc_date, amount) ==")
for t in sorted(by_type):
    print("\n-- %s" % t)
    for e in by_type[t]:
        print("   %s  p=%s  parcels=%d parties=%d  %s  %s" % e)

print("\n== MULTI-PARCEL (>=3) ==")
for e in multiparcel[:60]:
    print("   %s  %-40s parcels=%d parties=%d" % e)

print("\n== MULTI-PARTY (>=5) ==")
for e in multiparty[:60]:
    print("   %s  %-40s parcels=%d parties=%d" % e)
