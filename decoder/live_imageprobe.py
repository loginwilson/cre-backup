"""PROBE PENDING ACRIS IMAGES — the ACRIS consumer of image_policy.py.

    ACRIS_CORPUS_ROOT=D:/acris python live_imageprobe.py            report only
    ACRIS_CORPUS_ROOT=D:/acris python live_imageprobe.py --apply    probe + write

WHY THIS EXISTS. live_land.py lands every new ACRIS document as
image_state='pending' (the single policy, both sources). Richmond's probe is its
detail page; ACRIS publishes no image marker anywhere in its index — presence is
proven only at GetImage, where past-the-end and never-imaged both serve the SAME
constant placeholder as HTTP 200 (md5 4081a3f2..., the 174k-document lesson). So
the probe is: fetch page 1 through a real session, md5 it.

    placeholder md5   -> no scan attached yet -> stays 'pending'
    a real TIFF       -> 'present'
    age > TERMINAL_DAYS still pending -> 'imageless', never asked again

⚠ ACRIS measured 400/400 imaged SAME-DAY (rc_imagelag comparison 2026-08-18), so
the steady state is ~one day's filings probed once and flipped. If 'pending'
ever accumulates here, that is a FINDING about ACRIS's scanning, not queue noise.

⚠ SESSION, PACE, AND THE LINE. Reuses session_fetch.Session — visit the
document's own viewer, keep the cookies the server sets, ~1 req/s, ONE page per
document. On ANY refusal: stop the whole run, write what was already learned,
never retry into it. This is the pattern acquisition proved for days at 80
connections; one paced connection is far inside it.

⚠ ONE WRITER on the spec DB — the routine runs this stage sequentially, never
alongside a landing or a push. All network first, then a single write pass, so
the DB is held for milliseconds, not the probe's half hour.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP
import image_policy as IP
import fetch_pages
import session_fetch

MAX_PROBES = 2500      # ~1.6x a normal day's filings; the cap is LOGGED, never silent
PACE = 1.0


def pending_acris(con, today):
    """-> (due, terminal): pending non-Richmond docs, split by the policy clock.
    A NULL recorded_date falls back to image_checked (the first probe starts the
    clock) so no document is immortal."""
    rows = con.execute(
        "SELECT document_id, recorded_date, image_checked FROM document"
        " WHERE image_state='pending' AND document_id NOT GLOB 'RC_*'").fetchall()
    due, terminal = [], []
    for did, rec, checked in rows:
        (terminal if IP.is_terminal(today, rec, checked) else due).append(did)
    return due, terminal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    today = dt.date.today()

    if not CP.drive_present():
        print(f"IMAGE PROBE — SKIPPED (drive absent: {CP.SPEC_DB} not found).")
        return

    try:
        con = CP.connect_spec(timeout=30)
    except sqlite3.OperationalError as e:
        print(f"  ⚠ DEFERRED — spec DB would not open after retries ({e}). "
              f"Pending documents keep their state; the next run probes them.")
        return
    due, terminal = pending_acris(con, today)
    print(f"ACRIS IMAGE PROBE — {today}")
    print(f"  pending: {len(due):,} due (<= {IP.TERMINAL_DAYS}d) · "
          f"{len(terminal):,} past {IP.TERMINAL_DAYS}d -> 'imageless'")
    if not a.apply:
        con.close()
        print("  --apply not given; nothing probed or written.")
        return

    dropped = 0
    if len(due) > MAX_PROBES:
        dropped = len(due) - MAX_PROBES
        due = due[:MAX_PROBES]
        print(f"  ⚠ CAPPED at {MAX_PROBES:,} probes this run — {dropped:,} "
              f"pending documents NOT probed today (they age normally and are "
              f"first in line tomorrow). A cap that fires daily is a finding.")

    # ── network first: probe every due document, stop dead on a refusal ──
    s = session_fetch.Session()
    results, refused, errs = {}, False, 0
    t0 = time.time()
    for i, did in enumerate(due, 1):
        try:
            data, ct, ln = s.page(did, 1)
        except fetch_pages.AccessDenied as e:
            print(f"  ⚠ REFUSED at {did} (probe {i}/{len(due)}) — STOPPING, no "
                  f"retry. {len(results):,} results already learned are kept. "
                  f"{str(e)[:80]}")
            refused = True
            break
        except Exception as e:
            errs += 1
            print(f"    {did} ERROR {type(e).__name__} — left pending")
            continue
        if data is None:
            errs += 1           # not an image, not a refusal: reported, counted
            print(f"    {did} not-an-image ({ct}, {ln}b) — left pending")
        elif hashlib.md5(data).hexdigest() == fetch_pages.PLACEHOLDER:
            results[did] = IP.PENDING       # no scan yet; the clock keeps running
        else:
            results[did] = IP.PRESENT
        time.sleep(PACE)
    flips = sum(1 for v in results.values() if v == IP.PRESENT)
    print(f"  probed {len(results):,}/{len(due):,} · {flips:,} -> present · "
          f"{len(results)-flips:,} still pending · {errs} errors · "
          f"{(time.time()-t0)/60:.1f} min")

    # ── one write pass: stamps + terminal reclassification ───────────────
    with con:
        con.executemany(
            "UPDATE document SET image_state=?, image_checked=? WHERE document_id=?",
            [(v, today.isoformat(), d) for d, v in results.items()])
        con.executemany(
            "UPDATE document SET image_state='imageless', image_checked=?"
            " WHERE document_id=?",
            [(today.isoformat(), d) for d in terminal])
    con.close()
    print(f"  wrote {len(results):,} probe results + {len(terminal):,} imageless"
          + (" · RUN WAS REFUSED — partial, remainder probes tomorrow" if refused
             else ""))


if __name__ == "__main__":
    main()
