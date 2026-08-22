"""RICHMOND'S DATE-RANGE WINDOW — new-site edition (the county redesigned
their search between 2026-08-20 06:00 and 2026-08-21; the old POST-token
flow now returns the bare form and the old ViewDetailsButton markup is gone,
so every window read "0 rows" - including windows KNOWN to hold documents).

The new site is SIMPLER for the sync and richer per row:

    GET /Search/DateRangeSearch?StartSearchDate=YYYY-MM-DD
        &EndSearchDate=YYYY-MM-DD&SelectedDocumentIdentifier=0&pageNumber=N

    row: recorded date · type · internal id (in the ViewDocumentInfo href)
         · instrument - everything the sync ledger wants, no detail needed

    Page <span class="fw-bold">1</span> of 18      <- the page count

⚠ THE DETAIL PAGE IS BROWSER-ONLY NOW (a 4,212-byte shell to non-browsers,
same-host JS scaffolding). That is ACQUISITION's lane and it already runs in
Chrome. The sync needs only this list.

⚠ CONTROL FIRST, ALWAYS (the 2026-08-21 lesson): a zero window was
"verified" by a second zero window through the same broken parser, and the
sync printed ✓ LEVEL on a false zero for hours. control() asks page 1 of a
window KNOWN to hold documents (2026-08-19..20 = 315 recorded); if it parses
no rows, the PROBE is broken and no zero from it may be believed.
"""
from __future__ import annotations

import pathlib
import re
import sys
import threading
import time

import requests

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import fetch_pages

RC = "https://www.richmondcountyclerk.com"
_ROW = re.compile(
    r'data-label="Recorded">([^<]*)</td>\s*'
    r'<td[^>]*data-label="Type">([^<]*)</td>.*?'
    r'ViewDocumentInfo/(\d+)"[^>]*>\s*'
    r'<span aria-hidden="true">(\d+)</span>', re.S)
_PAGES = re.compile(r'Page\s*<span[^>]*>(\d+)</span>\s*of\s*(\d+)')


class ProbeBroken(RuntimeError):
    """the parser sees no rows where rows are KNOWN to exist - no zero from
    this probe may be believed until a human looks at the markup again"""


# one keep-alive session per thread: same request count and pacing, but no
# TCP+TLS handshake per page - LIGHTER on the county's edge, ~300 ms faster
# per request (the census fetches ~140k pages; handshakes were pure waste)
_tls = threading.local()


def _get(url):
    if not hasattr(_tls, "s"):
        _tls.s = requests.Session()
        _tls.s.headers["User-Agent"] = fetch_pages.UA
    r = _tls.s.get(url, timeout=60)
    return r.text


def _page(a_iso, b_iso, n):
    return _get(f"{RC}/Search/DateRangeSearch?StartSearchDate={a_iso}"
                f"&EndSearchDate={b_iso}&SelectedDocumentIdentifier=0"
                f"&pageNumber={n}")


def _rows(html):
    # split per <tr> so the regex can never bleed across rows
    out = []
    for chunk in html.split("<tr>"):
        m = _ROW.search(chunk)
        if m:
            out.append({"recorded": m.group(1).strip(),
                        "type": m.group(2).strip(),
                        "internal_id": m.group(3),
                        "instrument": m.group(4)})
    return out


def control():
    """page 1 of a window KNOWN nonzero must parse rows, or nothing this
    module says today is evidence. 2026-08-19..20 recorded 315 documents."""
    got = _rows(_page("2026-08-19", "2026-08-20", 1))
    if not got:
        raise ProbeBroken("control window 2026-08-19..20 parsed 0 rows"
                          " (it holds 315) - the markup changed again;"
                          " believe NO zero until the parser is re-proven")
    return len(got)


def window(a_iso, b_iso, pace=1.0):
    """every row recorded in [a, b] - all pages, deduped on internal id"""
    rows, seen, n, total = [], set(), 1, 1
    while n <= total:
        h = _page(a_iso, b_iso, n)
        m = _PAGES.search(h)
        if m:
            total = int(m.group(2))
        got = _rows(h)
        if not got:
            break
        for r in got:
            if r["internal_id"] not in seen:
                seen.add(r["internal_id"])
                rows.append(r)
        n += 1
        if n <= total:
            time.sleep(pace)
    return rows, total
