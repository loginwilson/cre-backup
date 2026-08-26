"""RE-FETCH THE rd FOR OLD RICHMOND ROWS THAT PREDATE `image_state`.

The last ~68 unassigned richmond rows are 1930s-40s documents whose rd was
parsed before the parser recorded `image_state` at all. Their rd has every
other field — parties, parcels, instrument — just not that one. So:

  * rc_pdf_state.py refuses to rule on them, correctly: "we never asked" is
    not "there is no image", and writing 'absent' would be a fabricated
    determination.
  * rc_lane's miner never requests them either — it selects
    image_state='present', which they cannot match.
  * rc_rd_refresh.py skips them: it walks only ids > 2,600,000 inside a
    7-day window, and these are ancient.

Nothing in the fleet can ever reach them. This closes that hole once.

⚠ THE GRANT RULE STILL APPLIES. A detail page only unlocks after the session
has fetched THE LISTING PAGE the id appears on. These docs are scattered over
~59 distinct recording dates decades apart, so a single wide DateRangeSearch
is useless — it is one narrow single-day window per date, then the details
found on it. ~2 requests per date, not per document.

⚠ REFUSAL STOPS EVERYTHING. Same rule as every other richmond caller.

    python rc_rd_backfill_old.py            report the work
    python rc_rd_backfill_old.py --apply    fetch and land the rd
"""
import argparse
import collections
import datetime as dt
import json
import pathlib
import re
import sqlite3
import sys
import time

import requests

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corpus_paths as CP                                       # noqa: E402
import fetch_pages                                              # noqa: E402

sys.argv, _argv = ["rc_rd_walk.py"], sys.argv   # import inert, reuse parser
import rc_rd_walk as W                                          # noqa: E402
sys.argv = _argv

RC = "https://www.richmondcountyclerk.com"
LO, HI = "RC_", "RC`"

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true")
ap.add_argument("--max-dates", type=int, default=0, help="0 = all")
a = ap.parse_args()


def stuck(nav):
    """Unassigned rows whose rd carries no image_state, keyed by recorded date.

    ⚠ Selected through `pdf IN ('','pending')` — the INDEXED predicate — and
    split in python. A bare `pdf=''` cannot use ix_nav_pdf_todo (SQLite will
    not prove `=''` implies the IN list) and degrades to a 2.5M-row scan."""
    out = collections.defaultdict(list)
    for rid, rd, pdf in nav.execute(
            "SELECT id, recorded_details, pdf FROM navigation"
            " WHERE pdf IN ('','pending') AND id >= ? AND id < ?", (LO, HI)):
        if pdf != "" or not rd:
            continue
        try:
            d = json.loads(rd)
        except Exception:
            continue
        if d.get("image_state") is not None:
            continue
        rec = (d.get("recorded") or "").strip()
        try:
            m, dd, y = rec.split("/")
            when = dt.date(int(y), int(m), int(dd))
        except ValueError:
            continue
        out[when].append(int(rid[3:]))
    return out


def main():
    nav = sqlite3.connect(CP.NAV_DB, timeout=1800)
    nav.execute("PRAGMA busy_timeout=900000")
    todo = stuck(nav)
    n = sum(len(v) for v in todo.values())
    print("stuck rows (rd has no image_state): %d across %d recording dates"
          % (n, len(todo)))
    if not n:
        print("nothing to do - LEVEL")
        return
    dates = sorted(todo)
    if a.max_dates:
        dates = dates[:a.max_dates]
    print("oldest %s   newest %s" % (dates[0], dates[-1]))
    if not a.apply:
        print("\nREPORT ONLY - would fetch ~%d window pages + %d details."
              % (len(dates), n))
        return

    s = requests.Session()
    s.headers["User-Agent"] = fetch_pages.UA

    def get(url):
        last = None
        for att in range(4):
            time.sleep(0.25 if not att else 3 * att)
            try:
                r = s.get(url, timeout=90)
            except requests.RequestException as e:
                last = e
                continue
            head = r.text[:2000]
            if "UNAUTHORIZED" in head and "SEARCH ACCESS" in head:
                raise SystemExit("REFUSED - STOPPING")
            return r.text
        raise last

    landed = missing = fails = 0
    for i, when in enumerate(dates, 1):
        want = set(todo[when])
        iso = when.isoformat()
        npage, total = 1, 1
        seen = set()
        try:
            while npage <= total and want - seen:
                h = get(f"{RC}/Search/DateRangeSearch?StartSearchDate={iso}"
                        f"&EndSearchDate={iso}&SelectedDocumentIdentifier=0"
                        f"&pageNumber={npage}")
                m = re.search(r"Page\s*<span[^>]*>\d+</span>\s*of\s*(\d+)", h)
                if m:
                    total = int(m.group(1))
                page_ids = set(map(int, re.findall(
                    r"ViewDocumentInfo/(\d+)", h, re.I)))
                for iid in sorted(want & page_ids):
                    seen.add(iid)
                    rec = W.parse_detail(
                        get(f"{RC}/Search/viewDocumentInfo/{iid}"), iid)
                    nav.execute(
                        "UPDATE navigation SET recorded_details=?"
                        " WHERE id=?",
                        (json.dumps(rec, separators=(",", ":")), f"RC_{iid}"))
                    nav.commit()
                    landed += 1
                npage += 1
        except SystemExit:
            raise
        except Exception as e:
            fails += 1
            print("  %s FAIL %s" % (iso, type(e).__name__), flush=True)
            continue
        # ⚠ AN ID ITS OWN RECORDING DATE DOES NOT LIST IS A REAL FINDING, not
        # an error - report it, never invent a verdict for it.
        missing += len(want - seen)
        if i % 10 == 0 or i == len(dates):
            print("  %d/%d dates · landed %d · unlisted %d · fail %d"
                  % (i, len(dates), landed, missing, fails), flush=True)

    print("\nrd landed %d · unlisted %d · window fails %d"
          % (landed, missing, fails))
    print("now run: python rc_pdf_state.py --apply")
    nav.close()


if __name__ == "__main__":
    main()
