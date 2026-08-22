"""THE SPECIFICATION, ORGANISED PER PARCEL — the walk queue, oldest to newest.

    python parcel_spec_db.py --build              # one pass over legals + master
    python parcel_spec_db.py --walk 1012060001    # every document on a parcel, in order
    python parcel_spec_db.py --walk 1012060001 --next 3
    python parcel_spec_db.py --mark 1012060001 FT_1440008468244 extracted
    python parcel_spec_db.py --top 20             # parcels with the deepest records

⚠ WHY THIS EXISTS. Login, 2026-08-17: *"organize our specification in a per parcel
database for the sake of training so i can just move oldest to newest records."* The
specification phase already knows every document and every BBL — 22,727,180 legals rows and
the master index, both on disk — but it is organised BY DOCUMENT. Nothing could answer
*"give me this parcel's record in date order"* without a full scan (79 s each, measured
three times today).

⚠ THIS IS THE SPECIFICATION LAYER ONLY. It says what EXISTS, never what a document means.
Extraction fills `_walk_one.db` (claim/event/subject/quantity/term). This is the queue that
feeds it, and `walk` is the only mutable table — rebuilding the index never loses progress.

⚠ NORMALISED ON PURPOSE. A flat bbl x document table is 22.7M wide rows. Splitting
`document` (one row per document) from `parcel_document` (the link, plus the per-parcel
flags that genuinely vary by lot) keeps it a fraction of the size, and `partial_lot` HAS to
live on the link — measured 2026-08-17: MN 1206/1 is `E` on the 2016 mortgage and `P` on the
2020 consolidation, same lot, same owner.

⚠ ORDER BY document_date, THEN recorded_date. Neither alone is safe: microfilm often has no
document_date, and recording lags execution by weeks (2019-12-23 executed, 2020-02-05
recorded). ⚠ NEVER order by document_id — measured, the id prefix precedes recording by five
days on 2016081800161001 and is an intake stamp, not an event date.
"""
from __future__ import annotations

import argparse, gzip, json, os, pathlib, sqlite3, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
# ⚠ ROOT IS AN ENV VAR, same convention as acquire_run.py — the corpus lives on the
# external drive and moving it must be one variable, not a code change.
ROOT = pathlib.Path(os.environ.get("ACRIS_CORPUS_ROOT", str(HERE)))
SPEC = ROOT / "01-specification"
# ⚠ THE DB IS BUILT WHERE RANDOM I/O IS CHEAP, NOT WHERE IT LIVES. Measured
# 2026-08-17: building straight onto the USB corpus drive read at ~1 MB/s with 0 B/s
# written — 40 minutes in, CREATE INDEX had not started. Every insert into a keyed
# table is a random B-tree write, and USB is the wrong device for that. Build on the
# NVMe via ACRIS_SPEC_DB, then move the finished file to the corpus drive, where it is
# only ever read sequentially.
DB = pathlib.Path(os.environ.get(
    "ACRIS_SPEC_DB", str((SPEC if SPEC.exists() else HERE) / "parcel_spec.db")))
_i = SPEC / "index" / "index_full"
IDX = _i if _i.exists() else HERE / "index_full"

DDL = """
CREATE TABLE IF NOT EXISTS document (
  document_id TEXT PRIMARY KEY, doc_type TEXT, doc_date TEXT, recorded_date TEXT,
  amount TEXT, reel_yr TEXT, reel_nbr TEXT, reel_pg TEXT, microfilm INTEGER);
-- ⚠ NO PRIMARY KEY AND NO INDEX AT LOAD TIME. First attempt used
-- `PRIMARY KEY (bbl, document_id) WITHOUT ROWID`, which makes SQLite rebalance a
-- 22.7M-row B-tree on every insert in random key order — it exhausted memory and
-- died at ~560 MB with a bare `object refcount : 3`. Load flat, index after.
-- ⚠ NO address COLUMN. It was 22.7M strings — the largest field in the schema — and
-- nothing read it: the walk orders by date and the manifest identifies documents by
-- id. It is still in legals.jsonl.gz if a use ever appears. Dropping it is what makes
-- the build fit on the NVMe, which is what makes it finish at all.
CREATE TABLE IF NOT EXISTS parcel_document (
  bbl TEXT, document_id TEXT, partial_lot TEXT, easement TEXT, air_rights TEXT,
  subterranean TEXT, property_type TEXT);
CREATE TABLE IF NOT EXISTS parcel (
  bbl TEXT PRIMARY KEY, n_docs INTEGER, first_date TEXT, last_date TEXT,
  n_microfilm INTEGER);
-- ⚠ the ONLY mutable table. Rebuilding the index must never lose walk progress.
CREATE TABLE IF NOT EXISTS walk (
  bbl TEXT, document_id TEXT, stage TEXT, at TEXT, note TEXT,
  PRIMARY KEY (bbl, document_id, stage));
"""
STAGES = ("acquired", "extracted", "derived", "resolved")


def build():
    if DB.exists():
        print(f"  {DB.name} exists — walk progress is preserved, index is rebuilt")
    con = sqlite3.connect(DB)
    # ⚠ page_size MUST be set before the first table exists or it is silently ignored.
    # 8192 matches the corpus drive's cluster size, so a page is one cluster instead of
    # straddling two. temp_store=MEMORY keeps the CREATE INDEX sort off disk entirely —
    # that sort is the step that never started on USB.
    con.executescript("PRAGMA page_size=8192; PRAGMA temp_store=MEMORY;")
    con.executescript(DDL)
    con.executescript("PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;"
                      " PRAGMA cache_size=-786432;")   # 768 MB — NVMe build, RAM is free
    con.execute("DELETE FROM document"); con.execute("DELETE FROM parcel_document")
    con.execute("DELETE FROM parcel")

    t0 = time.time(); n = bad = 0
    def legal_rows():
        nonlocal n, bad
        with gzip.open(IDX / "legals.jsonl.gz", "rt", encoding="utf-8") as f:
            for line in f:
                n += 1
                r = json.loads(line)
                try:
                    bbl = f"{int(r['borough'])}{int(r['block']):05d}{int(r['lot']):04d}"
                except (TypeError, ValueError, KeyError):
                    bad += 1; continue
                if len(bbl) != 10:
                    bad += 1; continue
                yield (bbl, r.get("document_id"), r.get("partial_lot"), r.get("easement"),
                       r.get("air_rights"), r.get("subterranean_rights"),
                       r.get("property_type"))
    # ⚠ CHUNKED. One executemany over a 22.7M-row generator keeps the whole
    # transaction hot; chunk + commit keeps memory flat and makes progress visible.
    buf, it = [], legal_rows()
    for row in it:
        buf.append(row)
        if len(buf) >= 200_000:
            con.executemany("INSERT INTO parcel_document VALUES (?,?,?,?,?,?,?)", buf)
            con.commit(); buf.clear()
            print(f"    legals {n:,}…", flush=True)
    if buf:
        con.executemany("INSERT INTO parcel_document VALUES (?,?,?,?,?,?,?)", buf)
    con.commit()
    print(f"  legals   {n:,} rows -> "
          f"{con.execute('select count(*) from parcel_document').fetchone()[0]:,} links"
          f"   (unparseable BBL: {bad:,})   {time.time()-t0:.0f}s")

    t1 = time.time(); m = 0
    def master_rows():
        nonlocal m
        with gzip.open(IDX / "master.jsonl.gz", "rt", encoding="utf-8") as f:
            for line in f:
                m += 1
                r = json.loads(line)
                d = r.get("document_id")
                if not d:
                    continue
                yield (d, r.get("doc_type"), (r.get("document_date") or "")[:10],
                       (r.get("recorded_datetime") or "")[:10], r.get("document_amt"),
                       r.get("reel_yr"), r.get("reel_nbr"), r.get("reel_pg"),
                       1 if d.startswith("FT_") else 0)
    buf = []
    for row in master_rows():
        buf.append(row)
        if len(buf) >= 200_000:
            con.executemany("INSERT OR REPLACE INTO document VALUES (?,?,?,?,?,?,?,?,?)", buf)
            con.commit(); buf.clear()
            print(f"    master {m:,}…", flush=True)
    if buf:
        con.executemany("INSERT OR REPLACE INTO document VALUES (?,?,?,?,?,?,?,?,?)", buf)
    con.commit()
    print(f"  master   {m:,} rows -> "
          f"{con.execute('select count(*) from document').fetchone()[0]:,} documents"
          f"   {time.time()-t1:.0f}s")

    print("  indexing…")
    con.executescript("""
      CREATE INDEX IF NOT EXISTS ix_pd_bbl ON parcel_document(bbl);
      CREATE INDEX IF NOT EXISTS ix_pd_doc ON parcel_document(document_id);
      CREATE INDEX IF NOT EXISTS ix_doc_date ON document(doc_date);
      INSERT INTO parcel
        SELECT pd.bbl, COUNT(*),
               MIN(NULLIF(COALESCE(NULLIF(d.doc_date,''), d.recorded_date),'')),
               MAX(NULLIF(COALESCE(NULLIF(d.doc_date,''), d.recorded_date),'')),
               SUM(COALESCE(d.microfilm,0))
        FROM parcel_document pd LEFT JOIN document d USING (document_id)
        GROUP BY pd.bbl;""")
    con.commit()
    p = con.execute("select count(*), sum(n_docs) from parcel").fetchone()
    print(f"\n  ⚠ PARCELS ACRIS HAS EVER ATTACHED TO: {p[0]:,}   ({p[1]:,} links)")
    print(f"  -> {DB.name}  ({DB.stat().st_size/1e9:.2f} GB)   total {time.time()-t0:.0f}s")
    # ⚠ a count with no denominator is not a result — show the shape too
    for b, name in (("1","Manhattan"),("2","Bronx"),("3","Brooklyn"),
                    ("4","Queens"),("5","Staten Island")):
        k = con.execute("select count(*) from parcel where bbl like ?", (b+"%",)).fetchone()[0]
        print(f"     {name:<15}{k:>10,}")
    con.close()


def walk(bbl, nxt=0, stage=None):
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    p = con.execute("select * from parcel where bbl=?", (bbl,)).fetchone()
    if not p:
        print(f"  no ACRIS record for {bbl}"); return 1
    print(f"  {bbl}   {p['n_docs']} documents   {p['first_date']} -> {p['last_date']}"
          f"   ({p['n_microfilm']} microfilm)\n")
    rows = con.execute("""
      SELECT d.document_id, COALESCE(NULLIF(d.doc_date,''),d.recorded_date) AS dt,
             d.doc_type, d.amount, d.reel_nbr, d.reel_pg, d.microfilm,
             pd.partial_lot, pd.easement, pd.air_rights,
             (SELECT group_concat(stage) FROM walk w
               WHERE w.bbl=pd.bbl AND w.document_id=d.document_id) AS done
      FROM parcel_document pd JOIN document d USING (document_id)
      WHERE pd.bbl=? ORDER BY dt, d.document_id""", (bbl,)).fetchall()
    if nxt:
        rows = [r for r in rows if not (r["done"] or "").split(",").count(stage or "extracted")][:nxt]
    print(f"  {'date':<12}{'document_id':<19}{'type':<10}{'amount':>15}  film  ext  done")
    for r in rows:
        try: a = f"{float(r['amount']):,.0f}"
        except (TypeError, ValueError): a = "-"
        film = f"{r['reel_nbr']}/{r['reel_pg']}" if r["microfilm"] else ""
        ext = "".join(x for x, v in (("P", r["partial_lot"] == "P"),
                                     ("E", r["easement"] == "Y"),
                                     ("A", r["air_rights"] == "Y")) if v)
        print(f"  {r['dt'] or '(none)':<12}{r['document_id']:<19}{r['doc_type'] or '?':<10}"
              f"{a:>15}  {film:<10}{ext:<4} {r['done'] or ''}")
    con.close()


def mark(bbl, doc, stage, note=""):
    if stage not in STAGES:
        print(f"  stage must be one of {STAGES}"); return 1
    con = sqlite3.connect(DB)
    con.execute("INSERT OR REPLACE INTO walk VALUES (?,?,?,datetime('now'),?)",
                (bbl, doc, stage, note or None))
    con.commit(); con.close()
    print(f"  {bbl} · {doc} -> {stage}")


def top(n):
    con = sqlite3.connect(DB)
    print(f"  {'bbl':<12}{'docs':>6}{'film':>6}  {'first':<12}{'last':<12}")
    for r in con.execute("SELECT bbl,n_docs,n_microfilm,first_date,last_date FROM parcel "
                         "ORDER BY n_docs DESC LIMIT ?", (n,)):
        print(f"  {r[0]:<12}{r[1]:>6}{r[2] or 0:>6}  {r[3] or '':<12}{r[4] or '':<12}")
    con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--walk"); ap.add_argument("--next", type=int, default=0)
    ap.add_argument("--stage", default="extracted")
    ap.add_argument("--mark", nargs=3, metavar=("BBL", "DOC", "STAGE"))
    ap.add_argument("--top", type=int)
    a = ap.parse_args()
    if a.build: return build()
    if a.walk: return walk(a.walk, a.next, a.stage)
    if a.mark: return mark(*a.mark)
    if a.top: return top(a.top)
    ap.print_help()


if __name__ == "__main__":
    raise SystemExit(main() or 0)
