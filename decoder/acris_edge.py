"""IS THERE A DOCUMENT ABOVE OUR EDGE? One GET, no session, no token.

    from acris_edge import quick_crfn
    state, doc_id = quick_crfn(2026000237865)   # -> ('live', '2026081800762006')
    state, doc_id = quick_crfn(2026000237866)   # -> ('blank', None)

⚠ WHY THIS EXISTS. `live_crfn.detail_html` asks the same question with a
SESSION + `__RequestVerificationToken` + a form-defs dict + an `LD.PACE` sleep,
because that is the shape the browser uses. Richmond's `Window` was equally
heavy until login found the plain date-range GET on 2026-08-23 and the probe
collapsed from 12 requests to 1. Login, the same morning:

    *"to me its all about direct gets and making sure you can access. i think
    thats what made python on richmond rd so effective is that it was a simple
    python get page details that could scale and took no time."*

ACRIS has the same door. `hid_CRFN` works as a QUERY PARAMETER — the token,
the cookie and the session are not checked on this route. Measured 2026-08-23:

    hid_CRFN=2026000237865&SearchType=DocID   131,544 bytes  0.8s  doc_id present
    hid_CRFN=2026000237866                     10,182 bytes  0.5s  no doc_id
    hid_CRFN=2026000237867                     10,182 bytes  0.5s  no doc_id
    doc_id=2026081800762006 (control)         131,535 bytes  0.7s  doc_id present

The live page matches the doc_id control to within 9 bytes — it is the same
document detail page, reached by CRFN instead of by id.

⚠ WHY NOT A DATE WINDOW, WHICH IS WHAT LOGIN ASKED FOR FIRST. Login 2026-08-23:
*"a date would be easier since you could just compare every time you fetch a
date if a new id showed... the delta becomes much easier since its just
comparison of 60 second changes."* That reasoning is right — a re-read window
makes delta a SET DIFFERENCE, which self-heals and needs no watermark. It is
exactly why Richmond's lane is simple. ACRIS just will not sell it:

    Document ID/CRFN search   no date field at all
    Document TYPE search      HAS dates (Last 7 / Last 31 / range) but REQUIRES
                              a doc type, and bounces a GET back to the menu —
                              21,724 bytes of search-options page for every
                              parameter set tried. Token POST bounced too.
    Socrata bnx9-e6tj         has recorded_datetime, and STOPS AT 2026-07-31.
                              Top CRFN 2026000216051 vs our edge 2026000237865:
                              the open dataset is 21,814 documents behind us.

So a date-keyed monitor is either impossible, 60-searches-wide, or three weeks
stale. The CRFN counter is the only live re-readable window ACRIS offers.

⚠ THE COUNTER IS FORWARD-ONLY AND THAT IS A REAL BLIND SPOT — NOT A SOLVED
PROBLEM. `sync_fast.py` states it: "a forward-only watermark inherits every gap
it already has and reports clean forever - it cannot see a row withdrawn or
re-keyed." This probe does not fix that and must never be described as if it
does. It is the CHEAP check; `routine_synchronization.py` remains the ground
truth on a slower schedule.

⚠ A REFUSAL ARRIVES AS HTTP 200. `LD.check_refused` is called on every body for
that reason. On a refusal: raise, stop, do not retry, do not rotate anything.
"""
from __future__ import annotations

import time
import urllib.error
import urllib.request

import live_crfn as LC
import live_delta as LD

URL = (LD.BASE + "/DS/DocumentSearch/DocumentDetail"
       "?hid_CRFN=%d&SearchType=DocID")
UA = "acris-decoder/1.0"
# ⚠ THE HONEST AGENT STRING IS NOT COSMETIC. Richmond returned 403 to
# `python-requests/…` and 200 to this exact string (docs/sources/richmond).
# Say who we are; never dress the client up as a browser.
HDRS = {"User-Agent": UA, "Accept": "text/html"}

# The absent-CRFN stub measured 10,182 bytes; a live detail page measured
# ~131,500. The gap is 13x, so any threshold in between is safe — but SIZE IS
# NOT THE TEST, the parse is. This only guards against calling a truncated
# response "live".
_MIN_DETAIL = 20_000


def fetch(crfn, timeout=45, tries=3):
    """ONE GET. Returns (state, doc_id, html) - the html is the PAYLOAD.

    ⚠ THE PROBE URL *IS* THE rd_url. Login 2026-08-23 spotted it: *"I'm
    realizing the link is the same as the rd link."* nav mints
    `DocumentDetail?doc_id=<id>` as rd_url, and that is byte-for-byte the page
    this probe already fetches by CRFN. So detection and rd-acquisition are the
    SAME REQUEST, and throwing the body away means fetching it twice:

        old   monitor GETs the page -> keeps the doc id, DISCARDS 131 KB
              sync GETs it again    -> keeps the doc id
              rd_walk GETs it again -> parses recorded_details
        new   one GET               -> doc id + recorded_details together

    Callers that only want existence use quick_crfn(); callers landing a row use
    this and pass the html to rd_parse.parse_acris."""
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(URL % int(crfn), headers=HDRS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
            LD.check_refused(body)        # a refusal is HTTP 200 - check first
            d = LC.parse_detail(body)
            if d is None:
                return "blank", None, None
            if len(body) < _MIN_DETAIL:
                raise RuntimeError(
                    "parsed a detail from only %d bytes - suspect truncation, "
                    "not reporting it as live" % len(body))
            return "live", d.get("doc_id"), body
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429):
                raise RuntimeError(
                    "REFUSED HTTP %d at crfn %s - stopping, not retrying"
                    % (e.code, crfn)) from e
            last = e
            if attempt < tries - 1:
                time.sleep(2 * (attempt + 1))
        except Exception as e:
            if "refus" in type(e).__name__.lower() or "Refus" in str(e):
                raise
            last = e
            if attempt < tries - 1:
                time.sleep(2 * (attempt + 1))
    raise last


def quick_crfn(crfn, timeout=45, tries=3):
    """ONE GET. Returns (state, doc_id) where state is 'live' or 'blank'.

    ⚠ IT RAISES RATHER THAN RETURNING 'blank' ON ANY FAILURE. An error is not
    an absence. phase_monitor's first version printed "quiet" after 8 instant
    failures because a broad `except` turned every error into found=False;
    every caller here must let the exception through and report NOTHING."""
    last = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(URL % int(crfn), headers=HDRS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
            LD.check_refused(body)        # a refusal is HTTP 200 - check first
            d = LC.parse_detail(body)
            if d is None:
                return "blank", None
            if len(body) < _MIN_DETAIL:
                raise RuntimeError(
                    "parsed a detail from only %d bytes - suspect truncation, "
                    "not reporting it as live" % len(body))
            return "live", d.get("doc_id")
        except urllib.error.HTTPError as e:
            # ⚠ NEVER RETRY A REFUSAL — AND AN HTTPError IS THE ONE SHAPE THAT
            # CAN BE ONE. `LD.check_refused` only runs after a body is read, so
            # it cannot see a 403; the first version of this function fell
            # through to the generic retry and would have hit a refusing host
            # three times. CLAUDE.md is unambiguous: "On a refusal: stop; do not
            # retry, do not rotate anything."
            if e.code in (401, 403, 429):
                raise RuntimeError(
                    "REFUSED HTTP %d at crfn %s - stopping, not retrying"
                    % (e.code, crfn)) from e
            last = e                      # 5xx / 307 etc: transient, retry
            if attempt < tries - 1:
                time.sleep(2 * (attempt + 1))
        except Exception as e:
            if "refus" in type(e).__name__.lower() or "Refus" in str(e):
                raise
            last = e
            if attempt < tries - 1:
                time.sleep(2 * (attempt + 1))
    raise last


def edge_holds(edge):
    """CONTROL. Does the CRFN we already hold still resolve?

    ⚠ CALL THIS BEFORE BELIEVING ANY BLANK. A malformed request, a changed
    route and a genuine absence all return 'no doc_id here'. Only a resolving
    control tells them apart."""
    state, doc_id = quick_crfn(edge)
    return state == "live", doc_id


if __name__ == "__main__":
    import sys
    args = [int(x) for x in sys.argv[1:]] or [2026000237865, 2026000237866]
    for n in args:
        t = time.time()
        try:
            st, did = quick_crfn(n)
            print("  %d  %-5s  %-16s  %.1fs" % (n, st, did or "-", time.time() - t))
        except Exception as e:
            print("  %d  ERROR %s: %s" % (n, type(e).__name__, e))
