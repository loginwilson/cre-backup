"""SUPABASE — create the specification schema, populate it, prove it matches.

    python supabase_setup.py --ddl     write supabase_schema.sql (run it in the
                                       Supabase SQL editor: the service key is a
                                       PostgREST key and CANNOT create tables)
    python supabase_setup.py --check   compare Supabase counts to the drive
    python supabase_setup.py --push    populate every table from the drive
    python supabase_setup.py --push --only document --batch 2000

WARNING - SUPABASE HOLDS document_map ONLY. Measured 2026-08-18: document,
parcel_document, party_document, reference_document and remark_document ALL
return 404. Every earlier claim that "all three databases agree" was comparing
document_map row counts, NOT the specification. They were never the same thing.

WARNING - COUNT-ASSERT EVERY TABLE. Today a pull filled the disk and left a
TRUNCATED file that looked complete; only comparing against an independent count
caught it. Two databases that both look full and disagree is the failure mode to
design against.

WARNING - BATCH SIZE IS UNMEASURED ABOVE 500. supabase_sync.push() 500s on ~12k
rows in one payload; nobody has tested between. 27.8M rows at 500/batch is
~55,000 requests, so batch size is the single biggest lever on runtime. Use
--batch to experiment; this is Supabase, not ACRIS, so there is no trip risk.

WARNING - RESUMABLE BY MERGE. Every write is an upsert on the primary key, so
re-running --push after a failure continues rather than duplicating.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP
import supabase_sync as S

DDL = """-- ACRIS specification schema for Supabase.
-- Run in the Supabase SQL editor, then: python supabase_setup.py --push
create table if not exists document (
  document_id text primary key, doc_type text, doc_date date,
  recorded_date date, amount text, reel_yr text, reel_nbr text,
  reel_pg text, microfilm int);

create table if not exists parcel_document (
  bbl text not null, document_id text not null, partial_lot text,
  easement text, air_rights text, subterranean text, property_type text,
  primary key (bbl, document_id));
create index if not exists ix_pcd_doc on parcel_document(document_id);

create table if not exists party_document (
  document_id text not null, party_type text not null, name text not null,
  address_1 text, address_2 text, city text, state text, zip text,
  country text,
  primary key (document_id, party_type, name));
create index if not exists ix_pyd_doc  on party_document(document_id);
create index if not exists ix_pyd_name on party_document(name);

create table if not exists reference_document (
  document_id text not null, reel_year text, reel_borough text,
  reel_nbr text, reel_page text, ref_crfn text, ref_doc_id text,
  primary key (document_id, reel_year, reel_borough, reel_nbr, reel_page));
create index if not exists ix_rfd_doc on reference_document(document_id);

create table if not exists remark_document (
  document_id text not null, sequence_number text not null, remark_text text,
  primary key (document_id, sequence_number));
create index if not exists ix_rmd_doc on remark_document(document_id);
"""

TABLES = {
    "document": ("document_id", "doc_type", "doc_date", "recorded_date",
                 "amount", "reel_yr", "reel_nbr", "reel_pg", "microfilm"),
    "parcel_document": ("bbl", "document_id", "partial_lot", "easement",
                        "air_rights", "subterranean", "property_type"),
    "party_document": ("document_id", "party_type", "name", "address_1",
                       "address_2", "city", "state", "zip", "country"),
    "reference_document": ("document_id", "reel_year", "reel_borough",
                           "reel_nbr", "reel_page", "ref_crfn", "ref_doc_id"),
    "remark_document": ("document_id", "sequence_number", "remark_text"),
}

CONFLICT = {
    "document": "document_id",
    "parcel_document": "bbl,document_id",
    "party_document": "document_id,party_type,name",
    "reference_document":
        "document_id,reel_year,reel_borough,reel_nbr,reel_page",
    "remark_document": "document_id,sequence_number",
}


def remote_count(url, key, table):
    """Supabase's own count. -404 means the table does not exist there."""
    head = {"apikey": key, "Authorization": "Bearer " + key,
            "Prefer": "count=exact", "Range": "0-0"}
    try:
        req = urllib.request.Request(url + "/rest/v1/" + table + "?select=*",
                                     headers=head)
        with urllib.request.urlopen(req, timeout=90) as resp:
            rng = resp.headers.get("Content-Range") or "/0"
            return int(rng.split("/")[-1])
    except urllib.error.HTTPError as e:
        return -404 if e.code == 404 else -e.code
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ddl", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--batch", type=int, default=1000)
    args = ap.parse_args()

    if args.ddl:
        out = HERE / "supabase_schema.sql"
        out.write_text(DDL, encoding="utf-8")
        print("  wrote " + str(out))
        print("  -> Supabase -> SQL editor -> paste and run -> then --push")
        return

    url, key = S._env()
    con = sqlite3.connect(
        "file:" + str(CP.SPEC_DB).replace("\\", "/") + "?mode=ro",
        uri=True, timeout=120)
    names = [args.only] if args.only else list(TABLES)

    print("  %-20s%14s%14s   %s" % ("table", "drive", "supabase", "status"))
    todo = []
    for t in names:
        drive = con.execute("SELECT COUNT(*) FROM " + t).fetchone()[0]
        remote = remote_count(url, key, t)
        if remote == -404:
            status = "MISSING - run --ddl first"
        elif remote == drive:
            status = "match"
        elif remote >= 0:
            status = "behind by %s" % format(drive - remote, ",")
        else:
            status = "error %d" % remote
        print("  %-20s%14s%14s   %s"
              % (t, format(drive, ","),
                 format(remote if remote >= 0 else 0, ","), status))
        if args.push and remote >= 0 and remote != drive:
            todo.append((t, drive))

    if not args.push:
        return
    if not todo:
        print("\n  nothing to push.")
        return

    head = {"apikey": key, "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal"}

    for table, drive in todo:
        cols = TABLES[table]
        print("\n  === %s: %s rows, batch %d ==="
              % (table, format(drive, ","), args.batch))
        sent = 0
        started = time.time()
        cur = con.execute("SELECT " + ",".join(cols) + " FROM " + table)
        while True:
            chunk = cur.fetchmany(args.batch)
            if not chunk:
                break
            rows = [dict(zip(cols, r)) for r in chunk]
            req = urllib.request.Request(
                url + "/rest/v1/" + table + "?on_conflict=" + CONFLICT[table],
                data=json.dumps(rows, default=str).encode(), headers=head)
            ok = False
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req, timeout=180):
                        ok = True
                        break
                except urllib.error.HTTPError as e:
                    if attempt == 3:
                        print("    FAILED at row %s: HTTP %d. Rows already sent "
                              "are NOT lost - re-run --push to resume."
                              % (format(sent, ","), e.code))
                    else:
                        time.sleep(2 ** attempt)
                except Exception:
                    if attempt < 3:
                        time.sleep(2 ** attempt)
            if not ok:
                break
            sent += len(rows)
            if sent % (args.batch * 50) == 0:
                rate = sent / max(time.time() - started, 1)
                print("    %s/%s  %s rows/s  %d min left"
                      % (format(sent, ","), format(drive, ","),
                         format(int(rate), ","),
                         (drive - sent) / max(rate, 1) / 60))
        after = remote_count(url, key, table)
        verdict = "PASS" if after == drive else "MISMATCH vs drive " + format(drive, ",")
        print("    sent %s - supabase now %s - %s"
              % (format(sent, ","), format(after, ","), verdict))


if __name__ == "__main__":
    main()
