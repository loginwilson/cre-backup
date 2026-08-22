"""FLIP THE ONE TABLE TO SQLITE (login, 2026-08-20: "yes flip it to sqlite
- as long as it is readable").

Legal Instruments Navigation.csv (the seeded frame) becomes
Legal Instruments Navigation.db - ONE table `navigation`, same seven
columns, PRIMARY KEY id, indexed on key. The walk ledger folds in as
upserts in the same pass. Landing stops being a 24M-row rewrite and becomes
an in-place upsert; every consumer reads by index instead of scanning.

Readability contract: any slice exports to csv on demand (nav_view.py);
the db opens in any sqlite browser; the gates read it with one query.
"""
import csv
import json
import pathlib
import sqlite3
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import corpus_paths as CP

NAV_DIR = pathlib.Path(r"D:\CRE Decoding System\01 Navigations"
                       r"\Legal Instruments Navigation")
SRC = NAV_DIR / "Legal Instruments Navigation.csv"
DB = NAV_DIR / "Legal Instruments Navigation.db"
LEDGER = NAV_DIR / "_working" / "rd_repull.jsonl"
csv.field_size_limit(1 << 27)

assert SRC.exists(), "frame csv missing"
if DB.exists():
    sys.exit(f"{DB.name} already exists - refusing to clobber the live table")

t0 = time.time()
con = sqlite3.connect(DB)
con.execute("PRAGMA journal_mode=WAL")
con.execute("PRAGMA synchronous=NORMAL")
con.execute("""CREATE TABLE navigation(
    id TEXT PRIMARY KEY,
    recorded_details TEXT,
    rd_url TEXT,
    pdf TEXT,
    pdf_url TEXT,
    keyed_by TEXT,
    key TEXT)""")

n = 0
with SRC.open("r", encoding="utf-8", newline="") as f:
    rd = csv.reader(f)
    header = next(rd)
    assert header == ["id", "recorded_details", "rd_url", "pdf", "pdf_url",
                      "keyed_by", "key"], f"unexpected header: {header}"
    batch = []
    for row in rd:
        batch.append(row)
        if len(batch) >= 100_000:
            con.executemany("INSERT INTO navigation VALUES (?,?,?,?,?,?,?)",
                            batch)
            n += len(batch)
            batch.clear()
            if n % 4_000_000 == 0:
                print(f"  {n:,} · {n/(time.time()-t0):,.0f} rows/s", flush=True)
    if batch:
        con.executemany("INSERT INTO navigation VALUES (?,?,?,?,?,?,?)", batch)
        n += len(batch)
con.commit()

# fold the walk ledger in as upserts (last write per id wins)
landed = 0
if LEDGER.exists():
    with LEDGER.open("r", encoding="utf-8") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            details = {k: v for k, v in r.items()
                       if k not in ("id", "at", "pdf")}
            con.execute(
                "UPDATE navigation SET recorded_details=?, pdf=COALESCE(NULLIF(?,''), pdf)"
                " WHERE id=?",
                (json.dumps(details, separators=(",", ":")),
                 r.get("pdf", ""), r["id"]))
            landed += 1
con.commit()

con.execute("CREATE INDEX ix_nav_key ON navigation(key)")
con.commit()
total = con.execute("SELECT COUNT(*) FROM navigation").fetchone()[0]
filled = con.execute("SELECT COUNT(*) FROM navigation"
                     " WHERE recorded_details != ''").fetchone()[0]
assert total == 24_039_303, f"count {total:,} != the sealed universe"
print(f"\n{DB.name}: {total:,} rows [= the sealed universe, OK]")
print(f"  recorded_details filled: {filled:,} · ledger folded: {landed:,}")
print(f"  {DB.stat().st_size/1e6:,.0f} MB · {(time.time()-t0)/60:.1f} min")
con.close()
