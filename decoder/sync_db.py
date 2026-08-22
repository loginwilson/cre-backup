"""THE SYNCHRONIZATION TABLE — the diagram's first table, exactly
(login 2026-08-21): source | system_total | source_total | delta | doc_ids,
one row per source plus a TOTAL row. Nothing else.

    python sync_db.py --show               read the table
    python sync_db.py --record             measure and write today's rows

⚠ doc_ids ARE DOC IDS, NEVER CRFNs (login: "it needs to convert into id,
not crfn. that's what the walk is for"). The routine's map stage resolves
every new CRFN into a document row in the SPECIFICATION - so by the time
this records, the real ids exist there, newer than what navigation holds.
The diff IS the delta id list.

⚠ RECORD BEFORE APPEND. system_total is what we held BEFORE absorbing the
delta (the diagram: system 23,039,303 vs source 24,049,303, delta +10,000).
The 4AM chain is therefore:
    routine_4am (walk + land into spec) -> sync_db --record -> nav_append
Recording after nav_append would make delta always read 0 - the append moves
the watermark this diff measures against.

source_total: ACRIS = system + the resolved delta (the spec is proven level
with live by the routine's reprobe: FINAL SPAN 0). Richmond has no counter;
its level is the window measurement, so source = system + window delta, the
induction the sync mds have always used.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP

SYNC_DIR = (pathlib.Path(r"D:\CRE Decoding System\00 Synchronizations")
            / "Legal Instruments Synchronization")
SYNC_DB = SYNC_DIR / "Legal Instruments Synchronization.db"

DDL = """
CREATE TABLE IF NOT EXISTS synchronization (
    run_at        TEXT NOT NULL,      -- the run this row measures
    source        TEXT NOT NULL,      -- acris | richmond | TOTAL
    system_total  INTEGER,            -- what we held BEFORE absorbing
    source_total  INTEGER,            -- what the custodian holds
    delta         INTEGER,            -- source - system = the work
    doc_ids       TEXT,               -- the new DOC IDS, ';'-joined
    PRIMARY KEY (run_at, source)
)"""

ap = argparse.ArgumentParser()
ap.add_argument("--show", action="store_true")
ap.add_argument("--record", action="store_true",
                help="measure and write today's rows (run AFTER the routine"
                     " lands the delta, BEFORE nav_append absorbs it)")
ap.add_argument("--acris-watermark", default="",
                help="override navigation's watermark (recover a correct"
                     " delta row when nav_append already absorbed the ids)")
a = ap.parse_args()

con = sqlite3.connect(SYNC_DB, timeout=600)
old = {r[1] for r in con.execute("PRAGMA table_info(synchronization)")}
if old and not {"source", "system_total"} <= old - {"scope", "id_kind"}:
    pass
if "scope" in old or "id_kind" in old or "status" in old:
    con.execute("DROP TABLE synchronization")   # v1 schema, one day old
con.execute(DDL)
con.commit()


def nav_counts():
    """what WE hold, per source - a full scan, daily only, never per-tick"""
    r = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=900)
    acris, rc = r.execute(
        "SELECT SUM(CASE WHEN id < 'RC_' THEN 1 ELSE 0 END),"
        "       SUM(CASE WHEN id > 'RC_' THEN 1 ELSE 0 END)"
        " FROM navigation").fetchone()
    r.close()
    return acris or 0, rc or 0


def acris_new_ids():
    """spec ids beyond navigation's watermark = the walk's resolved delta.
    ⚠ watermark over `id < '3'` ONLY - BK_/FT_ sort above digits, and a MAX
    over everything would return microfilm and skip every new recording."""
    mark = a.acris_watermark
    if not mark:
        nav = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True,
                              timeout=600)
        mark = nav.execute(
            "SELECT MAX(id) FROM navigation WHERE id < '3'").fetchone()[0] or ""
        nav.close()
    spec = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True, timeout=600)
    ids = [r[0] for r in spec.execute(
        "SELECT document_id FROM document WHERE document_id > ?"
        " AND document_id < '3' ORDER BY document_id", (mark,))]
    spec.close()
    return ids


def rc_new_ids():
    """the newest dated report's richmond block, minus what nav holds
    (PK point-probes, never a scan - the lanes may be writing)"""
    t = [p for p in sorted(SYNC_DIR.glob("*.md"))
         if re.match(r"\d{4}-\d\d-\d\d to ", p.name)]
    if not t:
        return []
    m = re.search(r"```richmond-delta(.*?)```",
                  t[-1].read_text(encoding="utf-8", errors="replace"), re.S)
    got = re.findall(r"^(RC_\d+)$", m.group(1), re.M) if m else []
    nav = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)
    fresh = [i for i in got if not nav.execute(
        "SELECT 1 FROM navigation WHERE id=?", (i,)).fetchone()]
    nav.close()
    return fresh


if a.record:
    run_at = time.strftime("%Y-%m-%d")
    sys_a, sys_r = nav_counts()
    ids_a, ids_r = acris_new_ids(), rc_new_ids()
    rows = [
        ("acris", sys_a, sys_a + len(ids_a), len(ids_a), ";".join(ids_a)),
        ("richmond", sys_r, sys_r + len(ids_r), len(ids_r), ";".join(ids_r)),
    ]
    rows.append(("TOTAL",
                 sum(r[1] for r in rows), sum(r[2] for r in rows),
                 sum(r[3] for r in rows), ""))
    for src, st, so, d, ids in rows:
        con.execute("INSERT OR REPLACE INTO synchronization VALUES"
                    " (?,?,?,?,?,?)", (run_at, src, st, so, d, ids))
    con.commit()
    print(f"recorded {run_at}: acris +{len(ids_a):,} · richmond"
          f" +{len(ids_r):,}")

if a.show or not a.record:
    rows = con.execute(
        "SELECT source, system_total, source_total, delta, doc_ids, run_at"
        " FROM synchronization s"
        " WHERE run_at = (SELECT MAX(run_at) FROM synchronization)"
        " ORDER BY CASE source WHEN 'TOTAL' THEN 1 ELSE 0 END, source"
    ).fetchall()
    if not rows:
        print("empty - run --record after the routine lands a delta")
        sys.exit()
    print(f"{'source':<9} {'system total':>13} {'source total':>13}"
          f" {'delta':>8}  doc ids")
    for src, st, so, d, ids, run_at in rows:
        n = len(ids.split(";")) if ids else 0
        head = ",".join(ids.split(";")[:3]) + ("..." if n > 3 else "")
        print(f"{src:<9} {st:>13,} {so:>13,} {d:>+8}  "
              f"{head if ids else '-'}  ({run_at})")
