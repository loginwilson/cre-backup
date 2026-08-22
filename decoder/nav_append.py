"""ADD THE SYNC'S NEW DOC IDS TO THE NAVIGATION TABLE — the missing link
between "the sync found 1,204 new documents" and "the pull fetches them"
(login 2026-08-21: "we need to find a way to smoothly update the table when
sync runs so whatever id it gets go to the db and naturally result in a new
row with rd and pdf urls").

    python nav_append.py --ids new_ids.txt --check     report only
    python nav_append.py --ids new_ids.txt --apply     insert them
    python nav_append.py --from-sync --apply           read the latest
                                                       dated sync table

⚠ WHY THIS EXISTS AND nav_build DOES NOT DO IT. `nav_build.py` builds the
WHOLE corpus and writes a csv; there is no incremental path. Rebuilding to
pick up a day's 1,204 documents would rewrite the table the lanes are
actively filling — 24M rows of `recorded_details`, `pdf` and `key` thrown
away to add 1,204 ids. This adds rows and touches nothing else.

⚠ A NEW ROW IS ALMOST EMPTY, AND THAT IS THE WHOLE DESIGN. It carries only
`id`, `rd_url`, `pdf_url`. Every other column is left `''` because AN EMPTY
CELL IS THE WORK LIST — rd_walk selects `WHERE recorded_details = ''`,
image_walk selects `WHERE pdf = ''`, nav_key selects `WHERE keyed_by = ''`.
So an appended row is picked up by the running lanes with no scheduling, no
signal and no restart. Nothing needs to be told it arrived.

⚠ INSERT OR IGNORE, NEVER UPSERT. Re-running must be harmless. An id already
in the table has a `recorded_details` we spent a request on; an UPSERT would
blank it and silently re-queue work that was already done. Collisions are
EXPECTED (the sync's window overlaps), so they are counted, not warned about.

Both urls are pure functions of the id, so this needs no specification read
for ACRIS at all. Richmond's rd address needs its instrument number when it
has one (an indexed `rc_binding` lookup) because Richmond's details page
renders only off a one-shot POST grant — see nav_build's note.
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

ACRIS = "https://a836-acris.nyc.gov/DS/DocumentSearch/"
RC = "https://www.richmondcountyclerk.com"

ap = argparse.ArgumentParser()
ap.add_argument("--ids", help="file of doc ids, one per line")
ap.add_argument("--from-sync", action="store_true",
                help="read ids from the newest dated sync table's delta blocks")
ap.add_argument("--acris-new", action="store_true",
                help="ACRIS ids the specification has and the table does not")
ap.add_argument("--apply", action="store_true", help="write them")
ap.add_argument("--check", action="store_true", help="report only (default)")
a = ap.parse_args()
if not a.apply:
    a.check = True


def ids_from_sync():
    """the dated sync table's ```richmond-delta``` block.

    ⚠ ONLY RICHMOND IS ENUMERABLE THERE. The acris block is deliberately a
    SPAN of CRFNs ("listing consecutive numbers individually would be noise
    pretending to be evidence") and a CRFN is NOT a doc id - the map stores
    no crfn on `document`, which is the same gap that leaves the 64-document
    2026 discrepancy open. So ACRIS ids come from the specification after
    live_land has landed them, not from this file.
    """
    d = (CP.DECODE_ROOT if hasattr(CP, "DECODE_ROOT")
         else pathlib.Path(r"D:\CRE Decoding System"))
    root = d / "00 Synchronizations" / "Legal Instruments Synchronization"
    tables = sorted(root.glob("*.md"))
    tables = [p for p in tables if re.match(r"\d{4}-\d\d-\d\d to ", p.name)]
    if not tables:
        print("no dated sync table found in", root)
        return []
    latest = tables[-1]
    txt = latest.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"```richmond-delta(.*?)```", txt, re.S)
    got = re.findall(r"^(RC_\d+)$", m.group(1), re.M) if m else []
    print(f"sync table: {latest.name} · {len(got):,} richmond ids")
    if "STAGED" in txt.split("\n")[2] if len(txt.split("\n")) > 2 else False:
        print("  ⚠ that run is STAGED, not FINALIZED - its balances did not"
              " reach 0. Appending anyway is a choice, not a default.")
    return got


def urls(did, instrument=None):
    """(rd_url, pdf_url) - pure functions of the id, per nav_build"""
    if did.startswith("RC_"):
        rd = (f"{RC}/search/ShowResultsDocumentNumberSearch/0"
              f"?DocumentNumber={instrument}&SelectedDocumentIdentifier=0"
              if instrument else f"{RC}/Search/viewDocumentInfo/{did[3:]}")
        return rd, f"{RC}/ViewVscmsDocument/ViewContent?p_endorsementId={did[3:]}"
    return (f"{ACRIS}DocumentDetail?doc_id={did}",
            f"{ACRIS}DocumentImageView?doc_id={did}")


def acris_new():
    """ACRIS ids in the specification that the table does not have yet.

    ⚠ THE WATERMARK IS `id < '3'`, NOT `id < 'RC_'`. ACRIS ids sort
    '2026…' < 'BK_' < 'FT_' < 'RC_', so a MAX over everything below 'RC_'
    returns the newest MICROFILM id and would silently skip every new
    recording. Newly recorded documents are always numeric-leading, so the
    watermark must be taken over the numeric range alone.
    ⚠ This is an index SEEK (MAX on the PK's range), not a scan - the whole
    reason it is safe to run while the lanes are writing.
    """
    nav = sqlite3.connect(f"file:{CP.NAV_DB}?mode=ro", uri=True, timeout=600)
    mark = nav.execute(
        "SELECT MAX(id) FROM navigation WHERE id < '3'").fetchone()[0] or ""
    spec = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True, timeout=600)
    got = [r[0] for r in spec.execute(
        "SELECT document_id FROM document WHERE document_id > ?"
        " AND document_id < '3' ORDER BY document_id", (mark,))]
    print(f"acris watermark {mark or '(none)'} · {len(got):,} newer in the"
          f" specification")
    return got


ids = []
if a.ids:
    ids += [ln.strip() for ln in
            pathlib.Path(a.ids).read_text(encoding="utf-8").splitlines()
            if ln.strip()]
if a.from_sync:
    ids += ids_from_sync()
if a.acris_new:
    ids += acris_new()
ids = list(dict.fromkeys(ids))
if not ids:
    print("no ids given - nothing to do")
    sys.exit()

# Richmond instrument numbers, one indexed lookup each (rc_binding is keyed
# on document_id). ~300/day, so this is milliseconds, not a scan.
instr = {}
rc_ids = [i for i in ids if i.startswith("RC_")]
if rc_ids:
    spec = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True, timeout=300)
    for did in rc_ids:
        row = spec.execute("SELECT instrument FROM rc_binding WHERE"
                           " document_id=?", (did,)).fetchone()
        if row and row[0]:
            instr[did] = row[0]

con = sqlite3.connect(CP.NAV_DB, timeout=600)
con.execute("PRAGMA busy_timeout=300000")
# ⚠ ONE INDEXED PK PROBE PER ID, NEVER A SCAN. The lanes are writing this
# table; a `WHERE id NOT IN (...)` or any full pass would queue behind them
# and starve the pull (measured 2026-08-21: an unguarded LIKE scan dropped rd
# from 17 to 1.5 docs/s). `id` is the PRIMARY KEY, so these are point reads.
present = sum(1 for did in ids if con.execute(
    "SELECT 1 FROM navigation WHERE id=?", (did,)).fetchone())
fresh = [d for d in ids if not con.execute(
    "SELECT 1 FROM navigation WHERE id=?", (d,)).fetchone()]

print(f"{len(ids):,} ids offered · {present:,} already in the table"
      f" · {len(fresh):,} new")
for did in fresh[:5]:
    rd, pdf = urls(did, instr.get(did))
    print(f"  + {did}\n      rd  {rd}\n      pdf {pdf}")
if len(fresh) > 5:
    print(f"  ... and {len(fresh)-5:,} more")

if a.check or not fresh:
    print("\nCHECK ONLY - nothing written. Re-run with --apply to insert.")
    sys.exit()

rows = [(d, "", *(lambda t: (t[0], "", t[1]))(urls(d, instr.get(d))), "", "")
        for d in fresh]
for _try in range(120):              # never die on a lock, like every writer
    try:
        con.executemany(
            "INSERT OR IGNORE INTO navigation"
            " (id, recorded_details, rd_url, pdf, pdf_url, keyed_by, key)"
            " VALUES (?,?,?,?,?,?,?)", rows)
        con.commit()
        break
    except sqlite3.OperationalError:
        time.sleep(5)
else:
    print("could not acquire the write lock in 10 min - nothing written")
    sys.exit(1)

# ⚠ THE DENOMINATOR MOVES WITH THE TABLE (login 2026-08-21: "we need to move
# the denominator, while the acquiring tasks move the numerator"). A row
# existing IS the denominator, so appending rows raises it by exactly the
# number appended. Bumping this file is cheaper and more honest than a nightly
# COUNT(*) - and a full count is what makes the WAL grow, so the board must
# never take one on a tick.
import json                                              # noqa: E402
DEN = CP.NAV_WORK / "denoms.json"
try:
    den = json.loads(DEN.read_text()) if DEN.exists() else {}
except Exception:
    den = {}
den.setdefault("acris", 21_612_715)
den.setdefault("rc", 2_426_588)
den["acris"] += sum(1 for d in fresh if not d.startswith("RC_"))
den["rc"] += sum(1 for d in fresh if d.startswith("RC_"))
den["total"] = den["acris"] + den["rc"]
den["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
DEN.write_text(json.dumps(den, indent=1))
print(f"denominators now acris {den['acris']:,} · rc {den['rc']:,}"
      f" · total {den['total']:,}")

print(f"\nappended {len(rows):,} rows at {time.strftime('%Y-%m-%d %H:%M')}."
      f"\nThe running lanes will pick them up with no restart: rd_walk sees"
      f" recorded_details='', image_walk sees pdf='', nav_key sees keyed_by=''.")
