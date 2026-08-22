"""PULL THE PERSONAL PROPERTY FAMILY - the never-ingested second ACRIS
channel (found 2026-08-20; see the Navigation md). Five Socrata datasets into
five pp_* tables in the spec DB, ROWS STORED AS RAW JSON - the full-page
rule at bulk grain: capture everything, exclude nothing by name; consumers
parse. document_id indexed for the nav/keying merge.

Why this exists: the sync only ever pulled the Real Property trio, which is
why 1.75M docs looked parcel-less/party-thin - the UCC/lien universe's
data (incl. ucc_collateral: F=fixture / C=cooperative, the keyable classes)
lives on this side. 0 of 2,024 sampled PP ids were new - same documents,
other channel, so this is ENRICHMENT, not universe change.

Streaming: page with $order=:id (the shared trap fix), insert per page,
commit per page - 4.5M dicts never sit in memory beside the keying walk.
Resume-safe per dataset: a completed table whose count matches the dataset
count is skipped.
"""
import json
import pathlib
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk
import corpus_paths as CP

PP = [("pp_master", "sv7x-dduq"), ("pp_legals", "uqqa-hym2"),
      ("pp_parties", "nbbg-wtuz"), ("pp_references", "6y3e-jcrc"),
      ("pp_remarks", "fuzi-5ks9")]
STEP = 50000

con = sqlite3.connect(CP.SPEC_DB, timeout=900)
con.execute("PRAGMA journal_mode=WAL")

for table, ds in PP:
    want = int(bulk.socrata(ds, select="count(1) as n")[0]["n"])
    con.execute(f"CREATE TABLE IF NOT EXISTS {table}"
                "(document_id TEXT, row TEXT)")
    have = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if have == want:
        print(f"{table}: complete at {have:,} - skipped", flush=True)
        continue
    if have:
        # partial table: cheaper to restart the dataset than to diff pages
        print(f"{table}: partial {have:,}/{want:,} - restarting", flush=True)
        con.execute(f"DELETE FROM {table}")
        con.commit()
    # CONCURRENT OFFSETS - the count is known, so the offsets are computed,
    # not discovered (bulk.py's own arcgis_all pattern; its serial socrata
    # paging is the measured 8-45 min cost this avoids). Fetches parallel,
    # inserts serial in this thread - SQLite keeps one writer.
    t0, n = time.time(), 0
    offs = list(range(0, want, STEP))
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(bulk.socrata, ds, limit=STEP, paginate=False,
                          offset=off, order=":id"): off for off in offs}
        for fut in as_completed(futs):
            rows = fut.result()
            con.executemany(
                f"INSERT INTO {table} VALUES (?,?)",
                ((r.get("document_id", ""),
                  json.dumps(r, separators=(",", ":"))) for r in rows))
            con.commit()
            n += len(rows)
            if n // (STEP * 10) != (n - len(rows)) // (STEP * 10):
                el = time.time() - t0
                print(f"  {table}: {n:,}/{want:,} · {n/el:,.0f} rows/s",
                      flush=True)
    con.execute(f"CREATE INDEX IF NOT EXISTS ix_{table}_doc"
                f" ON {table}(document_id)")
    con.commit()
    got = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    ok = "OK" if got == want else f"SHORT by {want - got:,}"
    print(f"{table}: {got:,} of {want:,} [{ok}] · "
          f"{(time.time()-t0)/60:.1f} min", flush=True)

print("\nPP family pull complete.", flush=True)
