"""RE-FETCH YOUNG RICHMOND RD — the maturation pass (born 2026-08-22).

A doc landed the day it was recorded freezes a PREMATURE detail page: the
county publishes the instrument number and attaches the scan with ~a-day
lag, so the rd shows instrument '' and image_state 'absent'. Frozen, that
doc is invisible to the instrument-number audit (the namespace bridge
field is blank) and PERMANENTLY skipped by the pdf lane (rc_mint selects
image_state='present'). Measured 2026-08-22: 103 docs recorded 8/21,
landed 8/21 22:40, all instrument-blank/image-absent while the county's
morning pages showed instruments 1017248-1017350.

This pass re-walks docs RECORDED IN THE LAST N DAYS whose rd is still
premature (instrument '' OR image_state 'absent') and REPLACES their rd.
Grant rule as ever: the window listing page first, then the detail. Runs
after sync in the daily chain; converges naturally (a matured rd stops
matching).

Usage:  python rc_rd_refresh.py [--days 7] [--workers 8]
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sqlite3
import sys
import threading
import time

import requests

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP
import fetch_pages

sys.argv, _argv = ["rc_rd_walk.py"], sys.argv   # import inert, reuse parser
import rc_rd_walk as W
sys.argv = _argv

RC = "https://www.richmondcountyclerk.com"

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=7)
ap.add_argument("--workers", type=int, default=8)
a = ap.parse_args()


def young_premature(nav):
    """ids recorded in the window whose rd is still premature."""
    out = {}
    today = dt.date.today()
    for rid, rd in nav.execute(
            "SELECT id, recorded_details FROM navigation"
            " WHERE id GLOB 'RC_*' AND recorded_details != ''"
            " AND CAST(substr(id,4) AS INTEGER) > 2600000"):
        d = json.loads(rd)
        rec = d.get("recorded") or ""
        try:
            m, dd, y = rec.split("/")
            when = dt.date(int(y), int(m), int(dd))
        except ValueError:
            continue
        if (today - when).days > a.days:
            continue
        if not d.get("instrument") or d.get("image_state") != "present":
            out[int(rid[3:])] = when
    return out


def main():
    nav = sqlite3.connect(CP.NAV_DB, timeout=600, check_same_thread=False)
    nav.execute("PRAGMA busy_timeout=300000")
    todo = young_premature(nav)
    if not todo:
        print("rc rd refresh: nothing premature - LEVEL")
        return
    lo, hi = min(todo.values()), max(todo.values())
    print(f"rc rd refresh: {len(todo)} premature docs recorded {lo}..{hi}")
    s = requests.Session()
    s.headers["User-Agent"] = fetch_pages.UA

    def get(url):
        last = None
        for att in range(4):
            time.sleep(0.2 if not att else 3 * att)
            try:
                r = s.get(url, timeout=90)
            except requests.RequestException as e:
                last = e
                continue
            if ("UNAUTHORIZED" in r.text[:2000]
                    and "SEARCH ACCESS" in r.text[:2000]):
                raise SystemExit("REFUSED - STOPPING")
            return r.text
        raise last

    n_new = n_still = fails = 0
    targets = set(todo)
    b = dt.date.today().isoformat()
    a_iso = min(todo.values()).isoformat()
    npage, total = 1, 1
    while npage <= total and targets:
        h = get(f"{RC}/Search/DateRangeSearch?StartSearchDate={a_iso}"
                f"&EndSearchDate={b}&SelectedDocumentIdentifier=0"
                f"&pageNumber={npage}")
        m = re.search(r"Page\s*<span[^>]*>\d+</span>\s*of\s*(\d+)", h)
        if m:
            total = int(m.group(1))
        page_ids = set(map(int, re.findall(r"ViewDocumentInfo/(\d+)", h,
                                           re.I)))
        for iid in sorted(targets & page_ids):
            try:
                rec = W.parse_detail(
                    get(f"{RC}/Search/viewDocumentInfo/{iid}"), iid)
                matured = bool(rec.get("instrument")) and \
                    rec.get("image_state") == "present"
                nav.execute("UPDATE navigation SET recorded_details=?"
                            " WHERE id=?",
                            (json.dumps(rec, separators=(",", ":")),
                             f"RC_{iid}"))
                nav.commit()
                n_new += matured
                n_still += (not matured)
            except Exception as e:
                fails += 1
                print(f"  {iid} FAIL {type(e).__name__}", flush=True)
            targets.discard(iid)
        npage += 1
    print(f"refresh done: {n_new} matured · {n_still} still young"
          f" (re-tried next run) · {fails} fail · {len(targets)} unlisted",
          flush=True)


main()
