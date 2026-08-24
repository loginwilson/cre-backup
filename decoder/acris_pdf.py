"""ONE ACRIS DOCUMENT'S PDF — the image_walk recipe, as a callable.

    from acris_pdf import fetch_pdf, Short
    state, value = fetch_pdf("2026081800762006", "8/21/2026 7:56:37 PM")
    # -> ("pdf", "By Document/2026/08 Aug/21/2026081800762006.pdf")
    # -> ("imageless", "imageless")

⚠ THIS IS EXTRACTED, NOT REWRITTEN. Every line is image_walk.worker()'s body,
which is ~40 lines of hard-won traps. Re-deriving them would re-derive the bugs:

    total <= 0            -> 'imageless'. A DEAD END AND A CORRECT ANSWER, not a
                             failure. The login called this out specifically.
    md5 == PLACEHOLDER    -> END OF DOCUMENT, served as HTTP 200. Treating it as
                             a page appends a blank to every pdf.
    not b"II" / b"MM"     -> not a TIFF frame; stop.
    frames != total       -> RAISE. A SHORT DOCUMENT IS A FAILURE, NEVER A PDF -
                             "a 1-of-8 read looks exactly like success". This is
                             the single most dangerous trap here, because the
                             result is a valid, openable, WRONG pdf.
    AccessDenied          -> refusal. Stop the line of work; no retry, no
                             rotation. Propagates to the caller by design.

⚠ THE Referer CHAIN IS LOAD-BEARING. GetImage is fetched with the VIEW page as
referer, and VIEW with the DETAIL page as referer - the order a browser would
walk. image_walk has always sent these; do not drop them while "simplifying".

⚠ THE USER-AGENT HERE IS NOT OURS. `fetch_pages.UA` is a Mozilla string, unlike
every other lane in this repo which announces itself as `acris-decoder/1.0`.
That is PRE-EXISTING production configuration on the image route and this module
reuses it verbatim rather than changing a working lane's identity as a side
effect of a refactor. ⚠ IT IS WORTH A DELIBERATE DECISION, NOT A SILENT ONE -
raised with login 2026-08-23.

⚠ STORE PATH = RECORDED CHRONOLOGY, from the rd row's recorded date, never the
id's embedded date (which is the SUBMISSION date and can lag recording by days -
measured up to 17). CP.doc_store_dir owns that rule.
"""
from __future__ import annotations

import contextlib
import hashlib
import pathlib
import re
import sys
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import corpus_paths as CP                                      # noqa: E402
import fetch_pages                                             # noqa: E402
import img2pdf                                                 # noqa: E402
import live_delta as LD                                        # noqa: E402

VIEW = "https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView"
DETAIL = LD.BASE + "/DS/DocumentSearch/DocumentDetail"
STORE = pathlib.Path(r"D:\CRE Decoding System\02 Acquisitions"
                     r"\Legal Instruments Acquisition")
_UA = {"User-Agent": fetch_pages.UA}
_TOTAL = re.compile(r"TotalPages%22%3A(-?\d+)")

# re-exported so callers can catch it without importing fetch_pages
AccessDenied = fetch_pages.AccessDenied


class Short(ValueError):
    """Fewer frames arrived than the map promised. ⚠ NOT a pdf - a retry row.
    The bytes we DO have would convert to a perfectly valid short document."""


# ⚠ THE LANE'S GATE, INJECTED (login 2026-08-24: "the code can never collide
# the requests"). acris_lane sets GATE = its slot() context manager, so every
# page and every map request in this module passes the tempo + no-collision
# gate. Left None for standalone use (the __main__ probe below).
GATE = None


def _get(url, referer, timeout=90):
    req = urllib.request.Request(url, headers={**_UA, "Referer": referer})
    with (GATE() if GATE is not None else contextlib.nullcontext()):
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(), r.headers.get("Content-Type", "")


def page_count(did, timeout=90):
    """One request. Returns TotalPages (<=0 means imageless)."""
    body, _ct = _get(VIEW + "?doc_id=" + did, DETAIL + "?doc_id=" + did,
                     timeout=timeout)
    m = _TOTAL.search(body.decode("utf-8", "ignore"))
    return int(m.group(1)) if m else 0


def fetch_pdf(did, rec_date="", timeout=90):
    """Returns (state, value):  ('imageless','imageless') | ('pdf', relpath).

    Raises AccessDenied on a refusal and Short when the document came back
    incomplete. Requests = 1 (the map) + TotalPages."""
    total = page_count(did, timeout=timeout)
    if total <= 0:
        return "imageless", "imageless"

    frames, stop_why = [], ""
    for p in range(1, total + 1):
        data, ct = _get("%s?doc_id=%s&page=%d" % (fetch_pages.BASE, did, p),
                        VIEW + "?doc_id=" + did, timeout=timeout)
        fetch_pages._check_denied(data, ct)
        # ⚠ DIAGNOSE THE BREAK (login 2026-08-24: "are they imageless is the
        # question? or is there a fault in our code?"). The old fleet's 191
        # Short docs (BK_/FT_/2003) never landed across ~4 attempts each -
        # persistent, but WHY was never captured. Record what the breaking
        # page actually was: placeholder = the server truly ends the doc
        # early (its defect); non-TIFF bytes = maybe an error page (load) or
        # maybe a FORMAT our II/MM assumption wrongly rejects (our defect -
        # e.g. film classes barely exercised). The fails log now carries the
        # verdict evidence at zero extra requests.
        if hashlib.md5(data).hexdigest() == fetch_pages.PLACEHOLDER:
            stop_why = "placeholder(end-marker) at page %d" % p
            break
        if data[:2] not in (b"II", b"MM"):
            stop_why = ("non-TIFF at page %d: ct=%s len=%d first16=%s"
                        % (p, ct, len(data), data[:16].hex()))
            break
        frames.append(data)

    if len(frames) != total:
        raise Short("short: %d/%d pages for %s · %s"
                    % (len(frames), total, did, stop_why))

    d = CP.doc_store_dir(did, rec_date)
    d.mkdir(parents=True, exist_ok=True)
    pdf = d / ("%s.pdf" % did)
    pdf.write_bytes(img2pdf.convert(frames))
    return "pdf", str(pdf.relative_to(STORE))


if __name__ == "__main__":
    import json
    import sqlite3
    import time
    if len(sys.argv) > 1:
        ids = sys.argv[1:]
        rec = {}
    else:
        c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True, timeout=120)
        rows = c.execute(
            "SELECT id, recorded_details FROM navigation"
            " WHERE pdf='' AND recorded_details!='' AND id>'20260815'"
            " AND id<'3' AND id NOT LIKE 'RC!_%' ESCAPE '!' LIMIT 2").fetchall()
        c.close()
        ids = [r[0] for r in rows]
        rec = {r[0]: (json.loads(r[1]).get("recorded", "") if r[1] else "")
               for r in rows}
    for did in ids:
        t = time.time()
        try:
            st, val = fetch_pdf(did, rec.get(did, ""))
            print("  %s  %-10s %.1fs  %s" % (did, st, time.time() - t, val))
        except Exception as e:
            print("  %s  %-10s %.1fs  %s" % (did, type(e).__name__,
                                             time.time() - t, e))
