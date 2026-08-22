"""HOW CURRENT IS THE SPECIFICATION? — the freshness stamp acquisition reads first.

    ACRIS_CORPUS_ROOT=D:/acris python spec_status.py            print it
    ACRIS_CORPUS_ROOT=D:/acris python spec_status.py --write    write STATUS.json

⚠ WHY THIS EXISTS. On 2026-08-19 acquisition was reading a specification that
lagged the disk by **121,274 documents** — not because anything failed, but
because the detail pull writes jsonl and the landing that moves it into the DB is
a separate step that nothing scheduled. Every artifact involved looked healthy.
There was no way, from inside acquisition, to ask *"is what I am reading current,
and if not, by how much?"* — so the gap was invisible until someone counted.

**A specification that cannot state its own freshness is a specification that
will be trusted when it is stale.** This computes the answer from the drive
itself — never from a number a previous run wrote down about itself.

THE ONE COMPARISON THAT MATTERS: records ON DISK (the jsonl the pull appends,
continuously) vs records LANDED (rows the DB can actually serve). If those differ,
`rc_detail_land.py --apply` has not run since the pull last fetched, and every
unlanded document is invisible to acquisition no matter how correct it is.

⚠ Read-only against the DB. Safe beside the pull, safe beside a landing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sqlite3
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP

DETAIL_JSONL = CP.INDEX / "rc_detail.jsonl"


def count_lines(p):
    """Records on disk. Counted, not remembered — the pull appends continuously
    and any cached figure is wrong by the time it is read."""
    if not p.exists():
        return 0
    n = 0
    with p.open("rb") as f:
        for _ in f:
            n += 1
    return n


def collect():
    if not CP.drive_present():
        return {"drive_present": False,
                "note": f"{CP.SPEC_DB} not found — the One Touch is not mounted"}

    con = sqlite3.connect(f"file:{CP.SPEC_DB}?mode=ro", uri=True)
    q = con.execute
    st = dict(q("SELECT COALESCE(image_state,'unobserved'), COUNT(*) FROM document"
                " WHERE document_id GLOB 'RC_*' GROUP BY 1").fetchall())
    total = q("SELECT COUNT(*) FROM document").fetchone()[0]
    rc = sum(st.values())
    con.close()

    on_disk = count_lines(DETAIL_JSONL)
    landed = sum(st.get(k, 0) for k in ("present", "pending", "imageless"))

    return {
        "drive_present": True,
        "measured_at": dt.datetime.now().isoformat(timespec="seconds"),
        "spec_db": str(CP.SPEC_DB),
        "spec_db_mtime": dt.datetime.fromtimestamp(
            CP.SPEC_DB.stat().st_mtime).isoformat(timespec="seconds"),
        "documents_total": total,
        "richmond_documents": rc,
        "richmond_image_state": st,
        # ── THE FRESHNESS TEST ──────────────────────────────────────────
        "detail_records_on_disk": on_disk,
        "detail_records_landed": landed,
        "unlanded_backlog": max(0, on_disk - landed),
        "current": on_disk <= landed,
        "acquisition_reads": "the rc_access VIEW in parcel_spec.db — never a CSV "
                             "snapshot, which freezes image_state (see "
                             "docs/sources/richmond/00-source.md)",
        "to_make_current": "ACRIS_CORPUS_ROOT=D:/acris python rc_detail_land.py --apply",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    s = collect()

    if not s["drive_present"]:
        print(f"SPECIFICATION STATUS — DRIVE ABSENT\n  {s['note']}")
        return

    print(f"SPECIFICATION STATUS — {s['measured_at']}")
    print(f"  documents          {s['documents_total']:,}")
    print(f"  richmond           {s['richmond_documents']:,}  {s['richmond_image_state']}")
    print(f"  detail on disk     {s['detail_records_on_disk']:,}")
    print(f"  detail landed      {s['detail_records_landed']:,}")
    if s["current"]:
        print(f"  ✓ CURRENT — the specification serves everything on disk")
    else:
        print(f"  ⚠ STALE by {s['unlanded_backlog']:,} documents — fetched but NOT "
              f"servable. Acquisition cannot see them.")
        print(f"    {s['to_make_current']}")

    if a.write:
        out = CP.SPEC / "STATUS.json"
        out.write_text(json.dumps(s, indent=1), encoding="utf-8")
        print(f"\n  wrote {out}")


if __name__ == "__main__":
    main()
