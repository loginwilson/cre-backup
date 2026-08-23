"""RICHMOND DAILY DELTA — date-range search, the SI analogue of the CRFN walk.

    ACRIS_CORPUS_ROOT=D:/acris python rc_sync.py --days 3
    ACRIS_CORPUS_ROOT=D:/acris python rc_sync.py --from 08/01/2026 --to 08/18/2026
    ACRIS_CORPUS_ROOT=D:/acris python rc_sync.py --days 3 --detail   (+parties/lots/image)

WHY DATE RANGE FOR THE DELTA AND BLOCKS FOR HISTORY. A block ledger returns a
whole block in one request - unbeatable for the historical spine - but it cannot
answer "what is new" without re-reading 3,789 blocks, and it is STRUCTURALLY
BLIND to any document filed without a block/lot (the same class as ACRIS's 37.6%
parcel-less filings, which we only found by counting). Date range answers exactly
the daily question and sees every recorded document.

MEASURED 2026-08-18
    1 day   102 docs · 1 request · no paging
    18 days 1,425 docs · 1.03 MB · 2.7 s
    30 days 2,982 docs · 2.03 MB · 2.8 s
    60/90/365 days -> 0 docs

⚠ THE OVER-CAP RESPONSE IS A SILENT ZERO. 60 days returns HTTP 200 with an 8 KB
page and no rows - shaped exactly like a genuinely empty range. MAX_SPAN caps the
window and the density check below refuses to call any window "complete" on the
strength of its own emptiness. This is the ACRIS end-of-document placeholder
served as 200, again.

⚠ INSTRUMENT NUMBER IS A DENSE MONOTONIC COUNTER - Richmond's CRFN. A 30-day 2019
window ran 725293..728274: 2,982 slots, 2,982 documents, 0 missing. So a window
proves ITSELF complete by arithmetic, not by trusting the server's own end-signal.

⚠ THE DETAIL PAGE IS SESSION-GUARDED. A GET of /Search/viewDocumentInfo/<id>
always returns a 2,180-byte "UNAUTHORIZED SEARCH ACCESS" shell with HTTP 200 -
it parses to an empty document and every downstream count still adds up. The
detail is reached by RE-POSTING the results form with ViewDetailsButton=<id>.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import rc_source as RC
import rc_route as RR

OUT = pathlib.Path("D:/acris/01-specification/index/rc_delta.jsonl")
WM = HERE / "_rc_sync_watermark.json"
MAX_SPAN = 30                       # measured cap is between 30 and 60 days
# ⚠ THE SOURCE'S MARKUP CHANGED AND THIS SILENTLY RETURNED ZERO ROWS.
# Found 2026-08-23: every date-range window - 2019 and 2026 alike - parsed 0
# rows while the server returned a REAL 30 KB results page. Not the documented
# over-cap trap (that returns ~8 KB); the results were there and the regex no
# longer matched them.
#
#   OLD  <button name="ViewDetailsButton" value="2825706">1016821</button>
#   NEW  <a href="/Search/ViewDocumentInfo/2825706"><span>1016821</span>
#
# Same two values - internal_id and instrument - moved from a button into an
# anchor plus a span. The results table also went from 7 columns to 5 (BOOK,
# PAGE, RECORDED, TYPE, DOCUMENT No.).
#
# ⚠ THIS IS THE WORST FAILURE SHAPE IN THE SYSTEM: rc_daily/rc_sync would
# report "0 new documents" every single day, forever, and look perfectly
# healthy doing it - the same disease LIVE_SYNC.md warns about for
# recorded_datetime, arriving by a different route. A parser that can only
# return "nothing" cannot tell you it is broken.
#
# BOTH patterns are kept: the old one costs nothing and the corpus was built
# with it, so a page served in either shape still parses.
_ROW = re.compile(
    r'name="ViewDetailsButton" value="(\d+)"[^>]*>\s*(\d{4,9})\s*</button>'
    r'|href="/Search/ViewDocumentInfo/(\d+)"[^>]*>\s*<span[^>]*>\s*(\d{4,9})\s*</span>')

# "&nbsp;&nbsp;Page <span class="fw-bold">1</span> of 10&nbsp;&nbsp;"
_PAGES = re.compile(r'Page\s*<span[^>]*>\s*(\d+)\s*</span>\s*of\s*(\d+)')


def _iso(mdy):
    """MM/DD/YYYY -> YYYY-MM-DD. ⚠ The POST form takes the first, the
    pagination GET takes the second. They are not interchangeable."""
    m, d, y = mdy.split("/")
    return "%s-%s-%s" % (y, m, d)


class Window:
    """One date-range search, held open so details can be re-POSTed against it."""

    def __init__(self, a, b):
        self.a, self.b = a, b
        self.s = RC.Session()
        tok = RR.token(self.s.get("/Search/SearchIndex"))
        _, page = RR.post(self.s, "/Search/SearchIndex",
                          {"button": "DateRangeSearch", "hbutton": "DateRangeSearch",
                           "htoken": "", "__RequestVerificationToken": tok})
        self.tok = RR.token(page)
        _, self.html = RR.post(self.s, "/Search/DateRangeSearch", self._f())
        self.tok = RR.token(self.html) or self.tok

    def _f(self, **extra):
        d = {"StartSearchDate": self.a, "EndSearchDate": self.b,
             "__RequestVerificationToken": self.tok}
        d.update(extra)
        return d

    @staticmethod
    def _parse(html):
        # _ROW carries two alternations (old button markup, new anchor markup);
        # whichever matched, the pair is (internal_id, instrument).
        out = []
        for m in _ROW.finditer(html):
            iid = m.group(1) or m.group(3)
            ins = m.group(2) or m.group(4)
            if iid and ins:
                out.append({"internal_id": iid, "instrument": ins})
        return out

    def rows(self):
        """⚠ THE WINDOW IS PAGINATED NOW — 17 ROWS A PAGE. Found 2026-08-23.

        The source doc records "1 day = 102 documents, 1 request, NO PAGING",
        and that is no longer true. Every window returned exactly 17 rows, and
        `density()` is what exposed it: a 2019 day reported slots=144, docs=17,
        missing=127. The page footer says "Page 1 of 10".

        Returning page 1 and calling it the day is the same silent-zero family
        as the dead regex above — a confident, wrong, complete-looking answer.
        So this follows every page before returning.

        Pagination is a plain GET (easier than the POST that opened the
        window), and ⚠ its dates are ISO, not the form's MM/DD/YYYY."""
        out = self._parse(self.html)
        m = _PAGES.search(self.html)
        if not m:
            return out
        total = int(m.group(2))
        for p in range(2, total + 1):
            try:
                h = self.s.get(
                    "/Search/DateRangeSearch"
                    f"?StartSearchDate={_iso(self.a)}"
                    f"&EndSearchDate={_iso(self.b)}"
                    f"&SelectedDocumentIdentifier=0&pageNumber={p}")
            except Exception:
                # ⚠ Partial is not whole. Say so rather than returning a
                # short list that looks complete.
                raise RuntimeError(
                    f"page {p} of {total} failed for {self.a}..{self.b} - "
                    f"refusing to return a partial window")
            out.extend(self._parse(h))
        return out

    def page(self, p):
        """One page of an already-open window. Plain GET, ISO dates."""
        return self._parse(self.s.get(
            "/Search/DateRangeSearch"
            f"?StartSearchDate={_iso(self.a)}&EndSearchDate={_iso(self.b)}"
            f"&SelectedDocumentIdentifier=0&pageNumber={p}"))

    def pages(self):
        m = _PAGES.search(self.html)
        return int(m.group(2)) if m else 1

    def edge(self):
        """Highest instrument number in the window, WITHOUT reading every page.

        ⚠ THE EDGE IS NOT ON PAGE 1. Measured 2026-08-23 on 08/21: page 1
        topped out at 1,017,264 while the day's true max was 1,017,350. A
        monitor reading page 1 would watch a FROZEN number all day and call
        every tick "quiet" while ~86 documents landed behind it.

        Rows ascend, so the last page carries the max — 2 requests instead of
        10, which is what lets this run on a one-minute cadence."""
        n = self.pages()
        rows = self.page(n) if n > 1 else self._parse(self.html)
        nums = [int(r["instrument"]) for r in rows if r["instrument"].isdigit()]
        return (max(nums) if nums else None), n

    def detail(self, internal_id):
        _, h = RR.post(self.s, "/Search/DateRangeSearch",
                       self._f(ViewDetailsButton=str(internal_id)))
        return RC.parse_detail(h)      # raises Unauthorized on the guarded shell


def density(rows):
    """(slots, docs, missing) - the completeness proof, independent of the server."""
    n = sorted({int(r["instrument"]) for r in rows if r["instrument"].isdigit()})
    if not n:
        return 0, 0, None
    return n[-1] - n[0] + 1, len(n), (n[-1] - n[0] + 1) - len(n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, help="trailing window ending today")
    ap.add_argument("--from", dest="a")
    ap.add_argument("--to", dest="b")
    ap.add_argument("--detail", action="store_true",
                    help="also fetch parties/lots/image_state per document "
                         "(~1 request each; fine at ~102/day, NOT at corpus scale)")
    ap.add_argument("--apply", action="store_true", help="write the jsonl")
    a = ap.parse_args()

    if a.days:
        end = dt.date.today()
        start = end - dt.timedelta(days=a.days - 1)
    else:
        start = dt.datetime.strptime(a.a, "%m/%d/%Y").date()
        end = dt.datetime.strptime(a.b, "%m/%d/%Y").date()
    span = (end - start).days + 1
    if span > MAX_SPAN:
        sys.exit(f"  span {span}d > {MAX_SPAN}d cap - the server would return a "
                 f"SILENT ZERO. Split the range.")

    t0 = time.time()
    w = Window(start.strftime("%m/%d/%Y"), end.strftime("%m/%d/%Y"))
    rows = w.rows()
    slots, docs, missing = density(rows)
    print(f"  {start} .. {end}  ({span}d)  ->  {len(rows):,} documents  "
          f"{len(w.html)/1024:.0f} KB  {time.time()-t0:.1f}s")
    print(f"  instrument density: {slots:,} slots · {docs:,} docs · missing {missing}")
    if not rows:
        print("  ⚠ ZERO ROWS. This is NOT proof the range is empty - it is the "
              "same shape the server returns over the span cap. Verify with a "
              "1-day window before believing it.")
        return
    if missing:
        print(f"  ⚠ {missing:,} instrument numbers unaccounted for in this window "
              f"- they are either other-county filings or a truncated read. "
              f"Do not treat this window as complete.")

    if a.detail:
        got = pend = 0
        for i, r in enumerate(rows, 1):
            try:
                d = w.detail(r["internal_id"])
            except RC.Unauthorized:
                raise
            except Exception as e:
                r["error"] = type(e).__name__
                continue
            if d:
                r.update(d)
                got += 1
                pend += d.get("image_state") == "pending"
            if i % 25 == 0:
                print(f"    detail {i:,}/{len(rows):,} · {pend} image pending")
        print(f"  details {got:,}/{len(rows):,} · image pending {pend:,}")

    if not a.apply:
        print("  --apply not given; nothing written.")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        for r in rows:
            r["window"] = f"{start}..{end}"
            f.write(json.dumps(r) + "\n")
    WM.write_text(json.dumps(
        {"through": str(end), "max_instrument": max(int(r["instrument"]) for r in rows),
         "at": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1), encoding="utf-8")
    print(f"  appended {len(rows):,} -> {OUT}")


if __name__ == "__main__":
    main()
