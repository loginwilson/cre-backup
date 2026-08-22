"""LAND THE RICHMOND DETAILS — parties, amounts, lots, image state into the spec.

    ACRIS_CORPUS_ROOT=D:/acris python rc_detail_land.py            report only
    ACRIS_CORPUS_ROOT=D:/acris python rc_detail_land.py --apply

WHY THIS IS SEPARATE FROM THE PULL. rc_detail_pull writes jsonl and nothing else -
so it can run for a day at conc 56 without ever holding the database, and a kill
costs one document instead of a transaction. This lands whatever is on disk,
whenever, and is safe to run repeatedly: every write is keyed, so re-landing the
same file changes nothing.

⚠ THE PULL IS STILL RUNNING WHILE THIS RUNS. It appends; we read. A partial last
line is expected and skipped, not treated as corruption.

⚠ ONE WRITER AT A TIME on the spec DB. Do not run alongside rc_daily or a push.

⚠ image_state COMES FROM THE PAGE, NOT FROM US. The ledger landing set every
Richmond document to 'unknown' because the ledger does not publish it; the detail
page states it outright. So this pass is ALSO the image-state backfill - the thing
that would otherwise have to be a separate campaign.

⚠ RECOMPUTE n_docs, NEVER INCREMENT, and only for parcels this pass touched.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP
import keys as K

# FIXED 2026-08-19: was hardcoded to D:/acris, which no longer exists after the
# 2026-08-19 restructure. corpus_paths is the single source of truth for paths.
SRC = CP.INDEX / "rc_detail.jsonl"
BATCH = 5000


def iso(s):
    try:
        m, d, y = (int(x) for x in (s or "").split("/"))
        return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, TypeError):
        return None


TERMINAL_DAYS = 7          # same window rc_daily uses; ~7x the measured ~24 h lag


def resolve_image_state(page_state, recorded):
    """⚠ THE PAGE CANNOT TELL pending FROM imageless - ONLY THE DATE CAN.

    The detail page says one of two things: an image link, or "No Image Available
    At This Time". The pull records the second as 'pending', which is right for a
    document filed yesterday and WRONG for one filed in 1938 that was never
    scanned. Measured 2026-08-19 over 745,166 pulled documents: 977 read
    'pending', of which 936 (95.8%) were over a year old and 772 were from the
    1930s. Only 41 were genuinely awaiting a scan.

    ⚠ rc_daily ALREADY HAD THIS RULE AND IT WAS UNREACHABLE HERE. It ages its own
    delta queue past TERMINAL_DAYS, but the bulk corpus never passes through that
    queue - so 2.4M documents had no path to 'imageless' at all. The fix is to age
    them at LANDING, where every document goes.

    ⚠ AN UNPARSEABLE DATE STAYS 'pending'. Guessing 'imageless' would permanently
    mark a document unfetchable on the strength of a bad date string; 'pending'
    keeps it visible and re-checkable. Note a merely IMPLAUSIBLE date still ages
    normally - the corpus holds a 1390s record (almost certainly 1930 mistyped),
    which parses fine and ages to 'imageless', and that is the right answer for it
    either way.
    """
    if page_state != "pending":
        return page_state or "unknown"
    d = iso(recorded)
    if not d:
        return "pending"
    try:
        age = (dt.date.today() - dt.date.fromisoformat(d)).days
    except ValueError:
        return "pending"
    return "pending" if age <= TERMINAL_DAYS else "imageless"


def rows():
    """Stream; skip the partial last line the running pull may be mid-write on."""
    with SRC.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue          # partial tail - the pull is still appending


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    n = 0
    states = collections.Counter()
    parties = lots = 0
    for r in rows():
        n += 1
        states[r.get("image_state") or ("ERR" if r.get("err") else "?")] += 1
        parties += len(r.get("parties") or [])
        lots += len(r.get("bbls") or [])
    print(f"  on disk {n:,} detail records")
    print(f"    parties {parties:,} · lot links {lots:,}")
    print(f"    image_state {dict(states)}")
    if not a.apply:
        print("  --apply not given; nothing written.")
        return

    con = sqlite3.connect(CP.SPEC_DB, timeout=900)
    con.execute("PRAGMA busy_timeout=900000")
    con.execute("PRAGMA synchronous=NORMAL")
    q = con.execute
    before = {t: q(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("party_document", "parcel_document")}
    imgs_before = dict(q("SELECT COALESCE(image_state,'(null)'), COUNT(*)"
                         # ⚠ RANGE, NOT substr(): substr() on the PK forces a
                         # 24M-row scan and made this "cheap" diagnostic cost
                         # ~25 min on the USB drive — the landing's own progress
                         # report was the slowest thing in the landing. A range
                         # on document_id uses the primary-key index and touches
                         # only the 2.4M RC_ rows. ('`' is chr(96), one past
                         # '_' at 95, so it bounds every 'RC_…' key.)
                         " FROM document WHERE document_id >= 'RC_'"
                         " AND document_id < 'RC`' GROUP BY 1").fetchall())
    print(f"  BEFORE party_document {before['party_document']:,} · "
          f"image_state {imgs_before}")

    t0 = time.time()
    dbuf, pbuf, lbuf = [], [], []
    touched = set()
    done = 0
    today = time.strftime("%Y-%m-%d")

    def flush():
        with con:
            if dbuf:
                con.executemany(
                    "UPDATE document SET image_state=?, image_checked=?,"
                    " amount=COALESCE(NULLIF(?,''), amount) WHERE document_id=?", dbuf)
            if pbuf:
                con.executemany(
                    "INSERT OR IGNORE INTO party_document(document_id, party_type,"
                    " name, address_1, address_2, city, state, zip, country)"
                    " VALUES (?,?,?,'','','','','','')", pbuf)
            if lbuf:
                con.executemany("INSERT OR IGNORE INTO parcel(bbl, n_docs,"
                                " first_date, last_date, n_microfilm)"
                                " VALUES (?,0,NULL,NULL,0)", [(b,) for b, _ in lbuf])
                con.executemany("INSERT OR IGNORE INTO parcel_document(bbl,"
                                " document_id) VALUES (?,?)", lbuf)
        dbuf.clear(); pbuf.clear(); lbuf.clear()

    rejected = []
    for r in rows():
        iid = r.get("internal_id")
        if not iid or r.get("err"):
            continue
        # ⚠ VALIDATE THE KEY AT THE BOUNDARY. A MIME multipart frame reached the
        # `document` table once (2026-08-19) because every lander trusted whatever
        # its parser handed back. Rejects are COLLECTED and REPORTED, never
        # silently skipped — a filter that drops rows without saying so is how the
        # count stays plausible while the corpus loses records.
        try:
            did = K.document_id("RC_" + str(iid))
        except ValueError as e:
            if len(rejected) < 20:
                rejected.append(str(e)[:120])
            continue
        dbuf.append((resolve_image_state(r.get("image_state"), r.get("recorded")),
                     today, (r.get("amount") or ""), did))
        for p in (r.get("parties") or []):
            nm = (p.get("name") or "").strip()
            if nm:
                pbuf.append((did, (p.get("role") or "").strip(), nm))
        for b in (r.get("bbls") or []):
            lbuf.append((b, did)); touched.add(b)
        done += 1
        if len(dbuf) >= BATCH:
            flush()
            if done % (BATCH * 4) == 0:
                el = time.time() - t0
                print(f"    {done:,}/{n:,} · {done/max(el,1e-9):,.0f} rec/s", flush=True)
    flush()

    bbls = sorted(touched)
    for i in range(0, len(bbls), BATCH):
        with con:
            con.executemany("UPDATE parcel SET n_docs=(SELECT COUNT(*) FROM"
                            " parcel_document pd WHERE pd.bbl=parcel.bbl)"
                            " WHERE bbl=?", [(b,) for b in bbls[i:i + BATCH]])

    # ── INVALIDATE THE MANIFESTS FOR EVERY PARCEL TOUCHED ────────────────
    # ⚠ THIS LANDING FLIPS image_state — `unknown` -> `present` is precisely the
    # transition that makes a document ACQUIRABLE. `_INDEX.md` is a CACHED answer
    # written when the parcel was materialised, and overnight.py skips any parcel
    # whose manifest shows nothing outstanding. So without this, enriching a
    # parcel does NOT reopen it: the manifest keeps asserting the pre-enrichment
    # answer and the newly-acquirable documents are never queued.
    # live_land.py has always done this (its "FAILURE 2"); this job changes the
    # same reachability and did not. Found 2026-08-19 tracing why acquisition was
    # not seeing the up-to-date specification.
    reopened = 0
    for b in bbls:
        f = CP.BYPARCEL / b[0] / b[1:6] / b[6:] / "_INDEX.md"
        if f.exists():
            f.unlink()
            reopened += 1
    print(f"  manifests invalidated: {reopened:,} of {len(bbls):,} touched parcels "
          f"(the rest were never materialised)")

    after = {t: q(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
             for t in ("party_document", "parcel_document")}
    imgs_after = dict(q("SELECT COALESCE(image_state,'(null)'), COUNT(*)"
                        " FROM document WHERE document_id >= 'RC_'"
                        "   AND document_id < 'RC` ' GROUP BY 1").fetchall())
    print(f"\n  RESULT ({(time.time()-t0)/60:.1f} min)")
    for k in before:
        print(f"    {k:<18} {before[k]:>12,} -> {after[k]:>12,} "
              f"({after[k]-before[k]:+,})")
    print(f"    image_state  {imgs_before}  ->  {imgs_after}")
    print(f"    n_docs recomputed on {len(bbls):,} parcels")
    # ⚠ REPORT THE REJECTS WITH THEIR DENOMINATOR, even when zero. A guard whose
    # counter reads zero is a claim, not a result — printing 0 of N states that
    # the check RAN, which a silent success cannot.
    print(f"    malformed document ids rejected: {len(rejected):,} of {done:,}")
    for m in rejected:
        print(f"      ⚠ {m}")
    con.close()


if __name__ == "__main__":
    main()
