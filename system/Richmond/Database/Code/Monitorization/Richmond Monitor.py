"""RICHMOND MONITORIZATION — watch the live date range, record every new doc id.

    python "Richmond Monitor.py" --apply        watch forever
    python "Richmond Monitor.py" --once         one tick, then exit
    python "Richmond Monitor.py"                report only, writes nothing
    python "Richmond Monitor.py" --day 08/25/2026 --once --apply

One job: keep `Richmond Database.db` holding a row for every internal
document id the county lists. It reads TODAY's date-range window, asks which
listed ids we do not already hold, and lands those — SOURCE AND ID, AND
NOTHING ELSE.

⚠ IT DOES NOT WRITE THE URLS, even though both are a pure function of the
id (login 2026-08-25: "your code autofilled the urls. that was not asked of
you"). Every other column is left NULL — not '' — for the later
acquisition passes to fill. ⚠ NULL and '' are not interchangeable here: a
lane asking WHERE "Document" = '' matched 14 rows while 2,501,709 sat
invisible to it.

═══════════════════════════════════════════════════════════════════════════
THE THREE STATES, AND WHY THE THIRD ONE EXISTS
═══════════════════════════════════════════════════════════════════════════

    'rows'     rows parsed                            -> real data
    'empty'    the page SAYS "NO RECORDS FOUND ..."   -> trustworthy quiet
    'unknown'  neither                                -> WRITE NOTHING

⚠⚠ `rows == 0` IS NOT THE SAME AS A QUIET DAY. An over-cap range, changed
markup and a genuine absence all return HTTP 200 with no rows. Only the
server's own explicit negative distinguishes the third. This was not
theoretical: when the county moved the id from a <button> into an <a>, the
parser returned zero rows and the monitor reported "0 new documents" EVERY
DAY FOR WEEKS while looking perfectly healthy. A parser that can only return
"nothing" cannot tell you it is broken.

**A server that tells you it is empty is worth more than any amount of
careful inference.** So 'unknown' writes nothing and says so, loudly.

⚠ BOTH MARKUPS ARE PARSED. The old <button name="ViewDetailsButton"> form
costs nothing to keep and the corpus was built with it, so a page served in
either shape still reads.

═══════════════════════════════════════════════════════════════════════════
WHY IT READS A CACHED PAGE, AND STILL SWEEPS
═══════════════════════════════════════════════════════════════════════════

A day grows all day. Re-reading pages 1..N every tick is waste, so the tick
reads the LAST page seen and follows the day as it grows past it.

⚠ BUT THE CACHED-PAGE TICK IS BLIND TO EARLIER PAGES — documents do appear
behind the cursor — so every --sweep-every seconds it re-reads the earlier
pages once. Not immediately after an overflow-follow already read the whole
day, or every page gets read twice.

⚠ AND THE EDGE IS NOT ON PAGE 1 (measured 2026-08-23 on 08/21): page 1
topped out at document 1,017,264 while the day's true max was 1,017,350. A
monitor that watches page 1 sees a FROZEN number all day and calls every
tick quiet.

═══════════════════════════════════════════════════════════════════════════
SECURITY
═══════════════════════════════════════════════════════════════════════════

One plain GET per tick against a public search page — 0.7 s, ~8.8 KB empty,
~29.3 KB full. No session, no token, no credentials.

⚠ A REFUSAL IS NEVER RETRIED. 403/Forbidden re-raises immediately and the
monitor stops. The standing order is "stop; do not retry, do not rotate
anything." The retry below is for the connection/timeout class ONLY, which
was proven local with a neutral DNS control.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import importlib.util
import sqlite3
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).parent
STATE = HERE / "_page_state.json"


# ⚠ ONE WRITER. This monitor DISCOVERS ids; Richmond Synchronization is the
# only thing that writes them. It also owns where the database is, so there
# is ONE definition of that path instead of two that can drift apart.
_SYNC_PY = HERE.parent / "Synchronization" / "Richmond Synchronization.py"
if not _SYNC_PY.exists():
    raise SystemExit("cannot find %s" % _SYNC_PY)
_spec = importlib.util.spec_from_file_location("richmond_sync", _SYNC_PY)
SYNC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SYNC)

DB = SYNC.DB
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOURCE = "richmond"
BASE = "https://www.richmondcountyclerk.com"
# ⚠ AN HONEST UA, AND IT IS LOAD-BEARING. Do not substitute a browser string:
# measured to buy nothing here, and it would make the client dishonest.
UA = "acris-decoder/1.0 (public land records indexing; contact via repo owner)"
DRS = (BASE + "/Search/DateRangeSearch"
       "?StartSearchDate=%s&EndSearchDate=%s&SelectedDocumentIdentifier=0")
NO_RECORDS = "NO RECORDS FOUND"

#   OLD  <button name="ViewDetailsButton" value="2825706">1016821</button>
#   NEW  <a href="/Search/ViewDocumentInfo/2825706"><span>1016821</span>
# Same two values — internal_id and document number — moved from a button
# into an anchor plus a span.
ROW = re.compile(
    r'name="ViewDetailsButton" value="(\d+)"[^>]*>\s*(\d{4,9})\s*</button>'
    r'|href="/Search/ViewDocumentInfo/(\d+)"[^>]*>\s*<span[^>]*>\s*(\d{4,9})\s*</span>')
# "&nbsp;&nbsp;Page <span class="fw-bold">1</span> of 10&nbsp;&nbsp;"
PAGES = re.compile(r'Page\s*<span[^>]*>\s*(\d+)\s*</span>\s*of\s*(\d+)')

ap = argparse.ArgumentParser()
ap.add_argument("--apply", action="store_true", help="write; default reports only")
ap.add_argument("--every", type=int, default=60, help="seconds between ticks")
ap.add_argument("--sweep-every", type=int, default=900,
                help="seconds between full re-reads of the earlier pages")
ap.add_argument("--day", default="", help="MM/DD/YYYY (default: today)")
ap.add_argument("--once", action="store_true", help="one tick then exit")
a = ap.parse_args()


def say(m):
    print("%s  %s" % (time.strftime("%H:%M:%S"), m), flush=True)


def _iso(mdy):
    """MM/DD/YYYY -> YYYY-MM-DD. ⚠ The POST form takes the first, the
    pagination GET takes the second. They are not interchangeable."""
    m, d, y = mdy.split("/")
    return "%s-%s-%s" % (y, m, d)


def _retry(fn, tries=3):
    """Transient network faults only. ⚠ A REFUSAL IS NEVER RETRIED."""
    for k in range(tries):
        try:
            return fn()
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e):
                raise
            if k == tries - 1:
                raise
            time.sleep(1.5 * (k + 1))


def _parse(html):
    """(internal_id, document_number) pairs, whichever markup was served."""
    out = []
    for m in ROW.finditer(html):
        iid = m.group(1) or m.group(3)
        doc = m.group(2) or m.group(4)
        if iid and doc:
            out.append((iid, doc))
    return out


def read_day(mdy, page=None, timeout=45):
    """ONE GET. Returns (state, rows, pages) — see the three states above."""
    url = DRS % (_iso(mdy), _iso(mdy))
    if page:
        url += "&pageNumber=%d" % page
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "text/html",
                      "Referer": BASE + "/"})
    html = _retry(lambda: urllib.request.urlopen(
        req, timeout=timeout).read().decode("utf-8", "replace"))
    rows = _parse(html)
    if rows:
        m = PAGES.search(html)
        return "rows", rows, (int(m.group(2)) if m else 1)
    if NO_RECORDS in html.upper():
        return "empty", [], 0
    # ⚠ NOT EMPTY — UNREADABLE. Refuse to call this quiet.
    return "unknown", [], 0


def urls(internal_id):
    """⚠ A PURE FUNCTION OF THE ID — no lookup, no fetch, no guessing.
    The same mint the whole system uses; if it is ever wrong it is wrong
    everywhere at once, which is far easier to see than one lane drifting."""
    return (BASE + "/Search/viewDocumentInfo/%s" % internal_id,
            BASE + "/ViewVscmsDocument/ViewContent?p_endorsementId=%s"
            % internal_id)


def fresh(rows):
    """Which listed ids do we NOT hold? Delegated — the membership test and
    the write have to agree about what "held" means, so both come from the
    same module."""
    return SYNC.fresh([iid for iid, _doc in rows])


def land(ids):
    """Record them. Delegated to Richmond Synchronization, the only thing in
    this system that writes to the database — see its land() for the
    NULL-not-'' rule and why the urls are deliberately not minted here.

    ⚠ The docstring this replaced said "EVERY UNFILLED COLUMN IS '' AND
    NEVER NULL", the exact opposite of what the code did and of what was
    decided. That is what a second copy of a rule turns into."""
    return SYNC.land(ids)


def _load_page(day):
    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
        if st.get("date") == day:
            return int(st.get("page", 1))
    except Exception:
        pass
    return 1


def _save_page(day, page):
    try:
        STATE.write_text(json.dumps({"date": day, "page": max(1, page)}),
                         encoding="utf-8")
    except OSError:
        pass


def tick(last_sweep):
    day = a.day or dt.date.today().strftime("%m/%d/%Y")
    page = _load_page(day)
    sweep = (time.time() - last_sweep) >= a.sweep_every
    try:
        state, rows, pages = read_day(day, page=page)
    except Exception as e:
        if "403" in str(e) or "Forbidden" in str(e):
            say("  ⚠⚠ REFUSED (%s) - STOPPING. Not retrying, not rotating"
                " anything." % type(e).__name__)
            raise SystemExit(2)
        say("  PROBE UNPROVEN (%s: %.70s) - nothing written"
            % (type(e).__name__, e))
        return last_sweep
    if state == "unknown":
        say("  ⚠ window returned rows=0 WITHOUT '%s' - a BROKEN READ, not a"
            " quiet day. Nothing written." % NO_RECORDS)
        return last_sweep
    if state == "empty":
        say("  %s quiet - the page says %s" % (day, NO_RECORDS))
        return last_sweep

    seen = list(rows)
    if pages > page:                       # the day grew past the cached page
        for p in range(page + 1, pages + 1):
            st2, more, _ = read_day(day, page=p)
            if st2 == "rows":
                seen.extend(more)
        say("  day grew: page %d -> %d" % (page, pages))
    elif sweep and pages > 1:
        # ⚠ the cached-page tick is blind to earlier pages - sweep sometimes,
        # but NOT right after an overflow-follow already read the whole day.
        for p in range(1, pages):
            st2, more, _ = read_day(day, page=p)
            if st2 == "rows":
                seen.extend(more)
        last_sweep = time.time()

    new = fresh(seen)
    if not new:
        say("  %s - %d listed, page %d/%d - nothing new"
            % (day, len(seen), page, pages))
    elif not a.apply:
        say("  %s - WOULD LAND %d new id(s) (report only): %s"
            % (day, len(new), ", ".join(new[:10])))
    else:
        n = land(new)
        say("  SYNC LANDED %d new richmond id(s) - page %d/%d - %s"
            % (n, page, pages, ", ".join(new[:10])))
    _save_page(day, pages)
    return last_sweep


if not DB.exists():
    say("⚠ no database at %s" % DB)
    raise SystemExit(1)
say("richmond synchronization up · db %s · every %ds · sweep %ds · apply=%s"
    % (DB.name, a.every, a.sweep_every, a.apply))
_sweep = 0.0
while True:
    try:
        _sweep = tick(_sweep)
    except SystemExit:
        raise
    except Exception as e:
        say("  tick error (%s: %.90s) - continuing" % (type(e).__name__, e))
    if a.once:
        break
    time.sleep(a.every)
