"""RICHMOND SYNCHRONIZATION — one request every 10s, fill new ids.

    python rc_live.py                    # report only, writes nothing
    python rc_live.py --apply            # the real thing
    python rc_live.py --apply --every 10

Login 2026-08-23: *"for me richmond should run 10 s cadence too since it doesnt
throttle... cant we do the same request 1 every 10 seconds via date range and
fill new id. the only difference is that rd still needs to separate since its a
different request?"*

Exactly so. This is `acris_live.py`'s twin, and the pair is the SYNCHRONIZATION
phase: everything up to the pdf. A separate pdf lane runs alongside, and org
closes both (org costs zero requests - nav_key reads recorded_details from the
db and never touches the network).

    acris_live.py   crfn+1        -> id + rd_url + pdf_url + recorded_details
    rc_live.py      date window   -> id + rd_url + pdf_url          (rd separate)

⚠ THE ONE ASYMMETRY, AND IT IS NOT A DEFECT. ACRIS's probe URL *is* its rd_url,
so rd arrives inside the detection request. Richmond's rd is guarded:
`/Search/viewDocumentInfo/<id>` fetched cold returns HTTP 200 + "INVALID
REQUEST: UNAUTHORIZED SEARCH ACCESS" (rc_source.py:45) - it needs a live search
in the same session, re-POSTing the results form with ViewDetailsButton. So rows
land here with recorded_details='' and the rd lane picks them up. That empty
string is load-bearing: rd_walk selects `WHERE recorded_details=''`.

⚠ NEW DOCUMENTS LAND ON THE *LAST* PAGE, NOT THE FIRST. The day sorts ASCENDING
by instrument at 17 rows a page, so today's newest sit on page 7 while page 1
holds the oldest. `quick_day(day)` with no page argument reads page 1 - polling
that forever would watch a part of the day that never changes again.

So this caches today's last known page and fetches THAT page each tick. One
request returns both the rows and the total page count, which is what makes the
cache self-correcting:

    rows appear on the cached page   -> caught, 1 request
    the page fills and overflows     -> `pages` increments, fetch the new one
    the date rolls over midnight     -> page resets to 1

⚠ A FULL DAY IS 7 PAGES / ~25 SECONDS. Running that every 10s would be three
overlapping full-day reads a minute to re-learn 103 rows that have not moved.
The whole point of the cached page is to never re-read the settled part of a day.

⚠ AN EMPTY WINDOW IS AN ANSWER, NOT A FAILURE — but only because the server SAYS
so. quick_day returns 'empty' on an explicit "NO RECORDS FOUND", 'unknown'
otherwise, and 'unknown' is never treated as quiet.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sqlite3
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import corpus_paths as CP                                      # noqa: E402
import rc_sync as RCS                                          # noqa: E402

RC = "https://www.richmondcountyclerk.com"
LEDGER = (r"D:\CRE Decoding System\00 Synchronizations"
          r"\Legal Instruments Synchronization"
          r"\Legal Instruments Synchronization.db")
STATE = HERE / "_rc_live_page.json"
LOG = HERE / "rc_live.log"

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true", help="write; default reports")
ap.add_argument("--every", type=int, default=10,
                help="seconds between ticks when nothing new appeared")
ap.add_argument("--sweep-every", type=int, default=900,
                help="seconds between FULL-day sweeps. The cached-page tick "
                     "cannot see a row inserted into an earlier page; this "
                     "bounds how long such a row stays invisible.")
ap.add_argument("--day", default=None,
                help="MM/DD/YYYY instead of today. For catching up after "
                     "downtime, and for testing the page-following on a day "
                     "that actually has pages (today may be quiet).")
ap.add_argument("--once", action="store_true")
a = ap.parse_args()


def say(m):
    line = "%s  %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def urls(did):
    """Pure function of the id — the same mint as nav_append and
    routine_navigation. Defined here because those are SCRIPTS."""
    n = did[3:]
    return ("%s/Search/viewDocumentInfo/%s" % (RC, n),
            "%s/ViewVscmsDocument/ViewContent?p_endorsementId=%s" % (RC, n))


def load_state(today):
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
        if st.get("date") == today:
            return int(st.get("page", 1))
    except Exception:
        pass
    return 1                             # new day (or no state): start at 1


def save_state(today, page):
    STATE.write_text(json.dumps({"date": today, "page": page,
                                 "at": time.strftime("%Y-%m-%dT%H:%M:%S")},
                                indent=1), encoding="utf-8")


def fresh(rows):
    """Which of these do we not hold? One PK lookup each — no scan."""
    con = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=600)
    con.execute("PRAGMA busy_timeout=300000")
    out = []
    for r in rows:
        did = "RC_" + r["internal_id"]
        if not con.execute("SELECT 1 FROM navigation WHERE id=?",
                           (did,)).fetchone():
            out.append(did)
    con.close()
    return out


def land(ids):
    """⚠ EVERY WORK COLUMN IS '' AND NEVER NULL. nav_append.py:216 - rd_walk
    sees recorded_details='', image_walk sees pdf='', nav_key sees keyed_by=''.
    Those lanes select on `= ''` and NULL is not '', so a NULL row is invisible
    to every lane forever while looking perfectly healthy."""
    con = sqlite3.connect(CP.NAV_DB, timeout=600)
    con.execute("PRAGMA busy_timeout=300000")
    batch = [(d, "", urls(d)[0], "", urls(d)[1], "", "") for d in ids]
    for _try in range(120):              # never die on a lock
        try:
            con.executemany(
                "INSERT OR IGNORE INTO navigation"
                " (id, recorded_details, rd_url, pdf, pdf_url, keyed_by, key)"
                " VALUES (?,?,?,?,?,?,?)", batch)
            con.commit()
            break
        except sqlite3.OperationalError:
            time.sleep(5)
    else:
        con.close()
        raise RuntimeError("could not acquire the write lock in 10 minutes")
    n = con.total_changes
    con.close()
    return n


def write_ledger(landed_ids, outstanding=0):
    """The row is the state AFTER absorbing, so "system == source, delta 0"
    reads as healthy at a glance. Accounted, not measured — previous + exactly
    what we landed; routine_synchronization re-anchors it."""
    lg = sqlite3.connect(LEDGER, timeout=120)
    try:
        prev = lg.execute(
            "SELECT system_total FROM synchronization"
            " WHERE source='richmond' AND system_total > 0"
            " ORDER BY run_at DESC LIMIT 1").fetchone()
        system = (prev[0] if prev else 0) + len(landed_ids)
        lg.execute("INSERT OR REPLACE INTO synchronization"
                   " (run_at, source, system_total, source_total, delta, doc_ids)"
                   " VALUES (?,?,?,?,?,?)",
                   (time.strftime("%Y-%m-%d %H:%M"), "richmond", system,
                    system + outstanding, outstanding, ";".join(landed_ids)))
        lg.commit()
    finally:
        lg.close()


_last_sweep = [0.0]


def tick():
    """Returns (ok, landed). ok=False means WE LEARNED NOTHING - not level."""
    today = a.day or dt.date.today().strftime("%m/%d/%Y")
    page = load_state(today)
    sweep = (time.time() - _last_sweep[0]) >= a.sweep_every

    try:
        state, rows, pages = RCS.quick_day(today, page=page)
    except Exception as e:
        say("  PROBE UNPROVEN (%s: %.80s) - nothing written"
            % (type(e).__name__, e))
        return False, 0

    if state == "unknown":
        # ⚠ NOT QUIET. An over-cap range, a changed markup and a genuine
        # absence all return HTTP 200 with no rows; only the server's own
        # "NO RECORDS FOUND" distinguishes the third.
        say("  window returned rows=0 WITHOUT 'NO RECORDS FOUND' - that is a "
            "broken read, not a quiet day. Nothing written.")
        return False, 0
    if state == "empty":
        say("  %s · server says NO RECORDS FOUND · quiet (1 req)" % today)
        return True, 0

    reqs = 1
    seen = list(rows)
    # follow overflow: the cached page filled and the day grew past it
    if pages > page:
        for p in range(page + 1, pages + 1):
            st2, more, _ = RCS.quick_day(today, page=p)
            reqs += 1
            if st2 == "rows":
                seen.extend(more)
        say("  day grew: page %d -> %d (+%d request(s))"
            % (page, pages, pages - page))
    # ⚠ THE CACHED-PAGE TICK IS BLIND TO EARLIER PAGES. Sweep occasionally.
    #
    # ⚠ BUT NOT WHEN THE OVERFLOW-FOLLOW ALREADY READ THE WHOLE DAY. On a cold
    # start (page=1) the follow above walks 1..pages, and sweeping 1..pages-1
    # straight after re-reads every one of them: measured 205 rows "seen" on a
    # day that holds 103. It was harmless only because `fresh()` is a PK lookup
    # and duplicates collapse - but a doubled row count is exactly the kind of
    # number that later gets quoted as a measurement.
    if sweep and pages > 1 and page > 1:
        _last_sweep[0] = time.time()
        for p in range(1, pages):
            st2, more, _ = RCS.quick_day(today, page=p)
            reqs += 1
            if st2 == "rows":
                seen.extend(more)
        say("  full-day sweep of %d page(s)" % pages)

    new = fresh(seen)
    if not new:
        save_state(today, pages)
        say("  %s · page %d/%d · %d row(s) seen, all held · level (%d req)"
            % (today, pages, pages, len(seen), reqs))
        return True, 0

    if not a.apply:
        for d in new[:5]:
            say("  would land %s -> %s" % (d, urls(d)[0]))
        say("  --apply not given: NOTHING WRITTEN")
        return True, 0

    n = land(new)
    save_state(today, pages)             # after the commit, never before
    try:
        write_ledger(new)
    except Exception as e:
        say("  ⚠ ledger write failed (%s) - rows ARE landed" % type(e).__name__)
    say("  landed %d new id(s) · page %d/%d · %d req · rd lane picks them up "
        "with no restart (recorded_details='')" % (n, pages, pages, reqs))
    for d in new[:5]:
        say("      %s" % d)
    return True, n


def main():
    say("rc_live up · tick %ds · full sweep every %ds · apply=%s"
        % (a.every, a.sweep_every, a.apply))
    if not a.apply:
        say("  ⚠ --apply NOT given: reporting only, nothing will be written")
    fails = 0
    while True:
        ok, landed = tick()
        if not ok:
            fails += 1
            wait = min(a.every * (2 ** fails), 900)
            say("  held after %d failure(s) - next attempt in %ds" % (fails, wait))
        elif landed:
            fails, wait = 0, 0           # behind inflow: chase it
        else:
            fails, wait = 0, a.every
        if a.once:
            return 0 if ok else 1
        if wait:
            time.sleep(wait)


if __name__ == "__main__":
    sys.exit(main() or 0)
