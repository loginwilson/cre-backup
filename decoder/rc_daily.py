"""RICHMOND DAILY — new documents, their details, and the image-lag rules.

    ACRIS_CORPUS_ROOT=D:/acris python rc_daily.py            report only
    ACRIS_CORPUS_ROOT=D:/acris python rc_daily.py --apply    fetch + land

THE SHAPE, AND WHY IT DIFFERS FROM ACRIS
    ACRIS   ceiling arithmetic on a dense CRFN counter; the gap is a set of
            numbers and we walk it.
    RICHMOND a DATE RANGE search returns every document recorded in a window in
            ONE request (measured: 102 for a day, 2,982 for 30 days, no paging).
            So the daily delta costs one request, not a probe.

⚠ WINDOW <= 30 DAYS, ALWAYS. 60/90/365-day ranges return HTTP 200 with an 8 KB
page and ZERO rows - identical in shape to a genuinely empty range. Same trap as
the ACRIS end-of-document placeholder served as 200. LOOKBACK stays small and a
zero result is never read as "nothing recorded" without the density check.

⚠ THE LOOKBACK IS 3 DAYS, NOT 1. A document can be recorded and appear in a
window we already read past; re-asking a small overlap costs one request and the
dedupe is free (we keep internal_ids we already hold). A one-day window is how
you lose the documents that land late.

THE LAG RULES LIVE IN image_policy.py — ONE POLICY, BOTH SOURCES (2026-08-19).
    pending -> probed each daily run while <= TERMINAL_DAYS old -> 'imageless'.
    This file is the Richmond CONSUMER of that policy (the probe here is the
    detail page — cheap, session-guarded, unthrottled); live_land.py +
    live_imageprobe.py are the ACRIS consumers. The measurements that justify
    the rules are quoted in image_policy.py, not re-litigated here.

⚠ ONE WRITER AT A TIME on the spec DB. Do not run while rc_land or a push holds it.

⚠ THE LANDING IS IDEMPOTENT-FROM-JSONL AND FAILURE DEFERS, NEVER DIES.
Measured 2026-08-19 04:01: sqlite3.connect raised 'unable to open database file'
while rc_detail_pull was writing the same drive (transient open failure — NOT
lock contention, which reads 'database is locked'). The old shape landed only
this run's fetches, so a landing that died AFTER the jsonl merge lost its
pending->present flips forever: the jsonl said 'present', the recheck queue
dropped the doc, and the DB never learned. Now EVERY run re-lands the whole
delta jsonl (a few hundred rows, upserts, sub-second) — a failed landing costs
nothing because the next run lands the same state. The DB write is a pure
function of the jsonl. Stale-overwrite is fenced by image_checked: an upsert
only moves image fields forward in time, so a daily row can never regress a
fresher state landed by the detail pull.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP
import rc_source as RC
import rc_sync as RS
import rc_imagelag as RI
import image_policy as IP
import keys as K

DELTA = CP.INDEX / "rc_delta.jsonl"
LOOKBACK = 3
TERMINAL_DAYS = IP.TERMINAL_DAYS   # the ONE policy — never redefined per source
CONC = 6


def iso(s):
    try:
        m, d, y = (int(x) for x in (s or "").split("/"))
        return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, TypeError):
        return None


def held():
    """internal_id -> record already on disk (so we never re-ask)."""
    out = {}
    if DELTA.exists():
        with DELTA.open(encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("internal_id"):
                    out[r["internal_id"]] = r
    return out


def fetch_details(win, ids):
    """Details through ONE window; a stale session is rebuilt, never parsed."""
    import threading
    tl = threading.local()

    def one(i):
        for attempt in range(2):
            try:
                if not hasattr(tl, "w"):
                    tl.w = win if attempt == 0 else RS.Window(win.a, win.b)
                return i, tl.w.detail(i), None
            except RC.Unauthorized:
                if hasattr(tl, "w"):
                    del tl.w
                if attempt:
                    return i, None, "Unauthorized"
            except RC.Refused:
                return i, None, "REFUSED"
            except Exception as e:
                return i, None, type(e).__name__
        return i, None, "retry-exhausted"

    with ThreadPoolExecutor(max_workers=CONC) as ex:
        return list(ex.map(one, ids))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--lookback", type=int, default=LOOKBACK)
    a = ap.parse_args()
    today = dt.date.today()
    start = today - dt.timedelta(days=a.lookback - 1)
    if a.lookback > 30:
        sys.exit("  lookback > 30d would return a SILENT ZERO. Split it.")

    # ⚠ DRIVE FIRST, NETWORK SECOND. Without the One Touch there is nowhere to
    # merge (the delta jsonl lives there too) and dedupe would see an empty
    # `held` — every window row would look NEW and be re-asked for nothing.
    # SKIPPED is a clean outcome, not a failure: exit 0, say why, touch nothing.
    if not CP.drive_present():
        print(f"RICHMOND DAILY — SKIPPED (drive absent: {CP.SPEC_DB} not found). "
              f"Nothing fetched, nothing written; tomorrow's 3-day lookback "
              f"covers today's documents.")
        return

    print(f"RICHMOND DAILY — {today}  (window {start} .. {today})")
    have = held()
    win = RS.Window(start.strftime("%m/%d/%Y"), today.strftime("%m/%d/%Y"))
    rows = RI.rows_of(win.html)
    slots, docs, missing = RS.density([{"instrument": r["instrument"]} for r in rows])
    print(f"  window returned {len(rows):,} documents · instrument density "
          f"{slots:,} slots / {docs:,} docs / missing {missing}")
    if not rows:
        print("  ⚠ ZERO ROWS — not proof the window is empty; that is also the "
              "over-cap shape. Verify with a 1-day window before believing it.")
        return

    fresh = [r for r in rows if r["internal_id"] not in have]
    print(f"  already held {len(rows)-len(fresh):,} · NEW {len(fresh):,}")

    # ── RULE 2: every pending doc <= TERMINAL_DAYS is probed THIS run ────
    # ⚠ a record with no parseable recorded date must not be immortal: its
    # clock starts at first_seen (stamped on fetch), per image_policy.
    due, terminal = [], []
    for iid, r in have.items():
        if r.get("image_state") != IP.PENDING:
            continue
        rec, seen = iso(r.get("recorded")), r.get("first_seen")
        if IP.is_terminal(today, rec, seen):
            terminal.append(iid)
        else:
            due.append(iid)
    print(f"  image pending: {len(due):,} due for recheck · "
          f"{len(terminal):,} past {TERMINAL_DAYS}d -> reclassify 'imageless'")

    if not a.apply:
        print("  --apply not given; nothing fetched or written.")
        return

    # ── fetch: new documents, then the recheck queue ─────────────────────
    t0 = time.time()
    got, errs, refused = [], 0, False
    for label, ids in (("new", [r["internal_id"] for r in fresh]),
                       ("recheck", due)):
        if not ids or refused:
            continue
        for iid, d, err in fetch_details(win, ids):
            if err == "REFUSED":
                print("  REFUSED — STOPPING. Nothing written is lost.")
                refused = True
                break
            if err or d is None:
                errs += 1
                continue
            d["internal_id"] = iid
            got.append(d)
        print(f"    {label}: {len(ids):,} asked · {time.time()-t0:.0f}s")

    # ── merge to disk: recheck REPLACES, new APPENDS ─────────────────────
    # image_checked stamps WHEN this state was observed — it is the fence that
    # lets the landing upsert refuse to regress a fresher state, and first_seen
    # starts the terminal clock for records whose recorded date will not parse.
    for d in got:
        prev = have.get(d["internal_id"]) or {}
        d["first_seen"] = prev.get("first_seen") or today.isoformat()
        d["image_checked"] = today.isoformat()
        have[d["internal_id"]] = d
    for iid in terminal:
        have[iid]["image_state"] = IP.IMAGELESS
        have[iid]["image_reason"] = f"still pending after {TERMINAL_DAYS}d"
        have[iid]["image_checked"] = today.isoformat()
    tmp = DELTA.with_suffix(".tmp")
    DELTA.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8") as f:
        for r in have.values():
            f.write(json.dumps(r) + "\n")
    tmp.replace(DELTA)
    flips = sum(1 for d in got if d.get("image_state") == "present"
                and d["internal_id"] in due)
    print(f"  fetched {len(got):,} · {errs} errors · "
          f"{flips:,} pending -> present · {len(terminal):,} -> imageless")

    # ── land: the WHOLE delta jsonl, every run — idempotent by construction ──
    # A failed landing costs nothing: the jsonl above is already safe, and the
    # next run re-lands the same state. The image upsert is fenced on
    # image_checked so a daily row can never regress a fresher state written by
    # the detail pull (which covers the same recent documents).
    try:
        con = CP.connect_spec()
    except sqlite3.OperationalError as e:
        print(f"  ⚠ LANDING DEFERRED — spec DB would not open after retries ({e}). "
              f"The delta jsonl is already written; the next run lands it. "
              f"Nothing is lost.")
        return
    n_doc = n_link = n_party = 0
    malformed = []
    with con:
        for d in have.values():
            # ⚠ validate the key at the boundary (keys.document_id) — see the
            # 2026-08-19 MIME-boundary row. Rejects are reported, never dropped
            # in silence.
            try:
                did = K.document_id("RC_" + str(d.get("internal_id")))
            except ValueError as e:
                if len(malformed) < 20:
                    malformed.append(str(e)[:120])
                continue
            con.execute(
                "INSERT INTO document(document_id, doc_type, doc_date,"
                " recorded_date, amount, reel_yr, reel_nbr, reel_pg, microfilm,"
                " image_state, image_checked) VALUES (?,?,NULL,?,?,'','','',0,?,?)"
                " ON CONFLICT(document_id) DO UPDATE SET"
                " image_state=excluded.image_state,"
                " image_checked=excluded.image_checked"
                " WHERE excluded.image_checked IS NOT NULL"
                "   AND (document.image_checked IS NULL"
                "        OR excluded.image_checked >= document.image_checked)",
                (did, d.get("doc_type"), iso(d.get("recorded")),
                 (d.get("amount") or "0"), d.get("image_state"),
                 d.get("image_checked")))
            n_doc += 1
            con.execute("INSERT OR IGNORE INTO rc_binding(document_id, instrument,"
                        " book, page) VALUES (?,?,?,?)",
                        (did, d.get("instrument"), d.get("book"), d.get("page")))
            for b in (d.get("bbls") or []):
                con.execute("INSERT OR IGNORE INTO parcel(bbl, n_docs, first_date,"
                            " last_date, n_microfilm) VALUES (?,0,NULL,NULL,0)", (b,))
                con.execute("INSERT OR IGNORE INTO parcel_document(bbl, document_id)"
                            " VALUES (?,?)", (b, did))
                n_link += 1
            for p in (d.get("parties") or []):
                nm = (p.get("name") or "").strip()
                if nm:
                    con.execute(
                        "INSERT OR IGNORE INTO party_document(document_id,"
                        " party_type, name, address_1, address_2, city, state,"
                        " zip, country) VALUES (?,?,?,'','','','','','')",
                        (did, p.get("role") or "", nm))
                    n_party += 1
    # ⚠ RECOMPUTE n_docs, NEVER INCREMENT - and only for touched parcels
    touched = sorted({b for d in have.values() for b in (d.get("bbls") or [])})
    with con:
        con.executemany("UPDATE parcel SET n_docs=(SELECT COUNT(*) FROM"
                        " parcel_document pd WHERE pd.bbl=parcel.bbl) WHERE bbl=?",
                        [(b,) for b in touched])
    con.close()
    print(f"  landed {n_doc:,} delta rows (upsert, whole jsonl) · "
          f"{n_link:,} parcel links · {n_party:,} party rows · "
          f"n_docs recomputed on {len(touched):,} parcels")
    print(f"  malformed document ids rejected: {len(malformed):,} of {len(have):,}")
    for m in malformed:
        print(f"    ⚠ {m}")
    print(f"  DONE {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
