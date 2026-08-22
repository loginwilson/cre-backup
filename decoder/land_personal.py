"""LAND PERSONAL PROPERTY INTO THE SPECIFICATION. All local — no ACRIS.

    ACRIS_CORPUS_ROOT=D:/acris python land_personal.py --apply

master  -> document          4,544,590 distinct
legals  -> parcel_document   3,981,194   (62.4% of docs carry a real bbl)
parties -> party_document   11,035,386   (37.6% of docs reach ONLY this way)

⚠ ROWS ARE NOT DOCUMENTS. Socrata publishes 4,547,264 master ROWS for 4,544,590
distinct documents — 2,674 duplicates. Real property has the same artefact
(+2,764). Dedupe on document_id or every count downstream is wrong.

⚠ THIS RE-RANKS ACQUISITION, IT IS NOT AN APPEND. parcel.n_docs is recomputed
from parcel_document, and acquisition selects on it (WHERE n_docs BETWEEN ? AND ?
ORDER BY n_docs DESC). +3,981,194 links moves parcels into and out of the band and
invalidates the _INDEX.md manifest of every parcel touched.

⚠ RECOMPUTE, NEVER INCREMENT — an increment is wrong the second time it runs.
⚠ STREAM. 11M party rows do not fit in memory; batch through in chunks.
"""
from __future__ import annotations
import argparse, os, gzip, json, pathlib, sqlite3, sys, time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP

# ⚠ THE INDEX LIVES ON THE CORPUS DRIVE, NOT NEXT TO THE CODE. C: filled to
# ZERO bytes on 2026-08-18 with the pull writing here; the files moved to D:
# and this path was NOT updated, so landing crashed on a missing file and the
# chain still reported rc=0 because its LAST command succeeded.
IN = pathlib.Path(os.environ.get("ACRIS_INDEX_OUT")
                  or "D:/acris/01-specification/index/index_staging")
BATCH = 20000


def iso(s):
    return (s or "").split("T")[0] or None


def bbl_of(r):
    try:
        b, bl, lt = int(r.get("borough") or 0), int(r.get("block") or 0), int(r.get("lot") or 0)
    except (ValueError, TypeError):
        return None
    return f"{b}{bl:05d}{lt:04d}" if b and bl and lt else None


def stream(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def chunked(it, n=BATCH):
    buf = []
    for x in it:
        buf.append(x)
        if len(buf) >= n:
            yield buf; buf = []
    if buf:
        yield buf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    con = sqlite3.connect(CP.SPEC_DB, timeout=120)
    con.execute("PRAGMA busy_timeout=120000")
    con.execute("PRAGMA synchronous=NORMAL")
    q = con.execute
    before = {t: q(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("document", "parcel", "parcel_document", "party_document")}
    print("BEFORE:", {k: f"{v:,}" for k, v in before.items()})
    if not a.apply:
        print("  --apply not given, nothing written."); return

    t0 = time.time()

    # 1 · DOCUMENT
    n = 0
    for ch in chunked(stream(IN / "personal_master.jsonl.gz")):
        with con:
            con.executemany(
                "INSERT OR IGNORE INTO document(document_id, doc_type, doc_date, "
                "recorded_date, amount, reel_yr, reel_nbr, reel_pg, microfilm) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                [(r["document_id"], r.get("doc_type"), None,
                  iso(r.get("recorded_datetime")), str(r.get("document_amt") or "0"),
                  str(r.get("reel_yr") or "0"), str(r.get("reel_nbr") or "0"),
                  str(r.get("reel_pg") or "0"),
                  1 if str(r["document_id"]).startswith("FT_") else 0) for r in ch])
        n += len(ch)
        if n % 500000 == 0:
            print(f"    document {n:,}  {time.time()-t0:.0f}s")
    print(f"  document streamed {n:,}")

    # 2 · PARCEL + PARCEL_DOCUMENT
    n = 0; touched = set()
    for ch in chunked(stream(IN / "personal_legals.jsonl.gz")):
        rows = [(bbl_of(r), r["document_id"], r.get("partial_lot"),
                 r.get("easement"), r.get("air_rights"), r.get("subterranean_rights"),
                 r.get("property_type")) for r in ch]
        rows = [x for x in rows if x[0]]
        with con:
            con.executemany("INSERT OR IGNORE INTO parcel(bbl, n_docs, first_date, "
                            "last_date, n_microfilm) VALUES (?,0,NULL,NULL,0)",
                            [(x[0],) for x in rows])
            con.executemany(
                "INSERT OR IGNORE INTO parcel_document(bbl, document_id, partial_lot,"
                " easement, air_rights, subterranean, property_type) VALUES (?,?,?,?,?,?,?)",
                rows)
        touched.update(x[0] for x in rows)
        n += len(rows)
        if n % 500000 < BATCH:
            print(f"    parcel_document {n:,}  {time.time()-t0:.0f}s")
    print(f"  parcel_document streamed {n:,} across {len(touched):,} bbls")

    # 3 · PARTY_DOCUMENT — VERBATIM MIRROR of the Socrata parties index.
    # ⚠ NO invented key, NO normalizer, NO role derivation. Socrata publishes this
    # index; copying it cannot be wrong, whereas any key we invent can be. Entity
    # matching is a LATER decision and storing the index verbatim keeps it open.
    n = 0
    for ch in chunked(stream(IN / "personal_parties.jsonl.gz")):
        with con:
            con.executemany(
                "INSERT OR IGNORE INTO party_document(document_id, party_type, name,"
                " address_1, address_2, city, state, zip, country)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                [(r.get("document_id"), str(r.get("party_type") or ""), r.get("name"),
                  r.get("address_1"), r.get("address_2"), r.get("city"),
                  r.get("state"), r.get("zip"), r.get("country")) for r in ch])
        n += len(ch)
        if n % 1000000 < BATCH:
            print(f"    party_document {n:,}  {time.time()-t0:.0f}s")
    print(f"  party_document streamed {n:,}")

    # 4 · RECOMPUTE n_docs on touched parcels — never increment
    print(f"  recomputing n_docs on {len(touched):,} parcels...")
    tl = sorted(touched)
    for i in range(0, len(tl), BATCH):
        with con:
            con.executemany(
                "UPDATE parcel SET n_docs=(SELECT COUNT(*) FROM parcel_document pd "
                " WHERE pd.bbl=parcel.bbl) WHERE bbl=?", [(b,) for b in tl[i:i+BATCH]])

    # ⚠ INVALIDATE THE MANIFESTS. _INDEX.md is a CACHED answer written when the
    # parcel was materialised, and overnight.py SKIPS any parcel whose manifest
    # shows nothing outstanding. Updating the specification does NOT reopen a
    # closed parcel — without this, every parcel that just gained personal-property
    # documents stays closed and acquisition silently misses all of them.
    reopened = 0
    for b in tl:
        f = CP.BYPARCEL / b[0] / b[1:6] / b[6:] / "_INDEX.md"
        if f.exists():
            f.unlink(); reopened += 1
    print(f"  manifests invalidated: {reopened:,} of {len(tl):,} touched parcels")

    after = {t: q(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
             for t in ("document", "parcel", "parcel_document", "party_document")}
    print(f"\n  ── RESULT ({(time.time()-t0)/60:.1f} min) ──")
    for k in before:
        print(f"  {k:<18} {before[k]:>12,} -> {after[k]:>12,}   ({after[k]-before[k]:+,})")
    reach = q("SELECT COUNT(*) FROM document d WHERE NOT EXISTS(SELECT 1 FROM "
              "parcel_document p WHERE p.document_id=d.document_id) AND NOT EXISTS("
              "SELECT 1 FROM party_document y WHERE y.document_id=d.document_id)").fetchone()[0]
    print(f"\n  UNREACHABLE documents (no parcel AND no party): {reach:,}")
    con.close()


if __name__ == "__main__":
    main()
