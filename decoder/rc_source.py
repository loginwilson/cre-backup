"""RICHMOND COUNTY CLERK — session, ledger parser, detail parser.

The SI deeds source. Model measured 2026-08-18 (4 probes, saved pages):

    ledger  GET /Search/ShowResultsBlocks/0?Block=N&HiLot=12&SelectedDocumentIdentifier=0
            -> the WHOLE block, no paging seen (block 15: 234 docs, 437 KB).
            Rows carry block/lot/book/page/recorded/type and a form BUTTON whose
            visible text is the INSTRUMENT number and whose value= is the
            INTERNAL id. The ledger publishes the id-binding IN BULK - ACRIS
            made us fetch its CRFN->doc_id binding one document at a time.
    detail  GET /Search/viewDocumentInfo/<internal_id>
            -> master (instrument, type, recorded, consideration, book/page,
            status) + PARTIES WITH ROLES (Mortgagor/Mortgagee named per
            document - richer than ACRIS) + every block/lot.
    image   /ViewVscmsDocument/ViewContent?p_endorsementId=<internal_id>
            -> endpoint derives from the INTERNAL id; the binding is DATA.

WARNING - TWO NAMESPACES, NO FORMULA. instrument 1004388 -> internal 2809822 and
consecutive pairs exist, but diffs range -7.4M..+2.1M. Never derive one from the
other; the ledger (bulk) and the detail page (single) are the only bindings.

WARNING - POSTs need __RequestVerificationToken + the session cookie (400
without). GETs for ledger and detail are clean. The site runs bot detection:
paced, sequential-ish, stop on any refusal shape, and the captcha path is a
hard no (user rule).
"""
from __future__ import annotations

import http.cookiejar
import re
import time
import urllib.request

BASE = "https://www.richmondcountyclerk.com"
# ⚠ IDENTIFY HONESTLY. Measured 2026-08-18: the county host serves the block
# ledger identically to a plain curl UA and to a Chrome UA (200, 437,112 bytes
# both) - it does not gate on User-Agent at all, so claiming to be Chrome bought
# nothing here and was inherited by copy-paste. The IMAGE host on
# iapps.courts.state.ny.us DOES gate on it (honest UA -> 403, Chrome UA -> 200
# application/pdf), which is exactly why nothing in this module fetches images.
UA = "acris-decoder/1.0 (public land records indexing; contact via repo owner)"
PACE = 0.5

# ⚠⚠ THE IMAGE STATE IS A READING PLUS A CLOCK (login 2026-08-25: "for
# richmond the image is present if the rd says view imaged document. if it
# says no image available at this time then it will either be pedning or
# absent, the lag determines the state").
#
# The page publishes only TWO things, and the third state is derived:
#   "View Imaged Document" / "ViewVscms"  -> present
#   "No Image Available At This Time"     -> pending INSIDE the lag window,
#                                            absent OUTSIDE it
#   neither string                        -> unknown. NEVER a conclusion -
#                                            it means we did not recognise
#                                            the page, so ask again.
#
# ⚠ PENDING AND ABSENT LOOK IDENTICAL ON ANY SINGLE READ. Only age against
# the lag distribution separates them. MEASURED 2026-08-18: doc 1016951
# recorded 8/18 read pending, doc 1016134 recorded 8/7 read present - and 10
# of 10 documents recorded on a Friday read no-image then and present after
# the weekend. That is why the window exists and why a fresh filing is never
# called absent.
#
# ⚠ AND AN UNREADABLE DATE IS ALWAYS PENDING, never absent. The failure mode
# of guessing wrong is a scanned document permanently recorded as having no
# scan, with nothing ever looking again; staying pending costs one re-ask.
IMAGE_LAG_DAYS = 7


def image_state(html, recorded=""):
    """present | pending | absent | unknown - the ONE definition, shared by
    every reader. rc_rd_walk.py used to keep its own and returned "absent"
    for anything not present, which collapsed no-image, unrecognised and
    parse-failure into one word (fixed 2026-08-25)."""
    import re as _re2
    import time as _t2
    if "View Imaged Document" in html or "ViewVscms" in html:
        return "present"
    if "No Image Available At This Time" not in html:
        return "unknown"
    m = _re2.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(recorded or "").strip())
    if not m:
        return "pending"
    try:
        t = _t2.mktime((int(m.group(3)), int(m.group(1)), int(m.group(2)),
                        0, 0, 0, 0, 0, -1))
    except (ValueError, OverflowError):
        return "pending"
    return "pending" if (_t2.time() - t) < IMAGE_LAG_DAYS * 86400 else "absent"


class Unauthorized(RuntimeError):
    """The detail route was reached WITHOUT a live search in the same session.
    ⚠ IT IS NOT A REFUSAL AND NOT AN ERROR CODE: HTTP 200, 2,180 bytes, body reads
    "INVALID REQUEST: UNAUTHORIZED SEARCH ACCESS". A GET of
    /Search/viewDocumentInfo/<id> ALWAYS returns this - the browser only appears
    to do a GET because the results page POSTs and the server redirects. Landing
    this shape writes a document with no parties, no lots and no image state,
    and every downstream count still adds up. Raise, never parse."""


class Refused(RuntimeError):
    """The site declined (captcha page, block page, or empty shell). Stop the
    line of work; do not retry, do not rotate anything."""


def check_refused(html):
    if "UNAUTHORIZED SEARCH ACCESS" in html:
        raise Unauthorized("detail needs a live search in the same session - "
                           "POST the results form with ViewDetailsButton")
    low = html[:4000].lower()
    if "captcha" in low or "access denied" in low or "blocked" in low:
        raise Refused("richmondcountyclerk served a refusal shape - STOP")


class Session:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
        self.op.addheaders = [("User-Agent", UA)]

    def get(self, path, timeout=60):
        time.sleep(PACE)
        with self.op.open(BASE + path, timeout=timeout) as r:
            h = r.read().decode("utf-8", "replace")
        check_refused(h)
        return h

    def ledger(self, block):
        return self.get(f"/Search/ShowResultsBlocks/0?Block={int(block)}"
                        f"&HiLot=12&SelectedDocumentIdentifier=0")

    def detail(self, internal_id):
        """⚠ DO NOT USE - kept only so an old caller fails loudly instead of
        silently banking empty shells. The detail page is guarded: it is reached
        by re-POSTing the SEARCH RESULTS form with ViewDetailsButton=<id>. See
        rc_detail.open_detail()."""
        raise Unauthorized(
            "GET /Search/viewDocumentInfo is always UNAUTHORIZED - re-POST the "
            "results form with ViewDetailsButton=<internal_id> instead")


# ── LEDGER ────────────────────────────────────────────────────────────────
_ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
_TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
_BTN = re.compile(r'value="(\d+)"[^>]*>\s*(\d{4,9})\s*</button>')


def _txt(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).replace("\xa0", " ").strip()


def parse_ledger(html):
    """Every document row: dict(block, lot, book, page, recorded, doc_type,
    instrument, internal_id). One INSTRUMENT can span several rows (one per
    lot) - the caller aggregates lots per instrument."""
    out = []
    for m in _ROW.finditer(html):
        row = m.group(1)
        b = _BTN.search(row)
        if not b:
            continue                      # header or non-document row
        tds = [_txt(x) for x in _TD.findall(row)]
        if len(tds) < 6:
            continue
        out.append({"block": tds[0], "lot": tds[1], "book": tds[2],
                    "page": tds[3], "recorded": tds[4], "doc_type": tds[5],
                    "internal_id": b.group(1), "instrument": b.group(2)})
    return out


# ── DETAIL ────────────────────────────────────────────────────────────────
def _field(t, label, stop):
    """⚠ THE STOP MUST BE GROUPED. Unwrapped, a stop like "View|BLOCKS" splits the
    WHOLE pattern into (Status:...View) | (BLOCKS), so a page matching the bare
    BLOCKS branch returns a match whose group(1) is None -> AttributeError. That
    branch is taken exactly when the page has NO "View Imaged Document" link, so
    the parser read every IMAGED document fine and crashed on every UNIMAGED one
    - the precise population an image-lag study is made of. Measured 2026-08-18:
    8/8 samples on the current day died this way."""
    g = re.search(re.escape(label) + r":\s*(.*?)\s*(?:" + stop + r")", t)
    return (g.group(1) or "").strip() if g else ""


def parse_detail(html):
    """Master + parties-with-roles + every block/lot, or None if no document."""
    # &nbsp; arrives as the LITERAL ENTITY, not \xa0 - strip it BEFORE
    # collapsing whitespace or every field carries "&nbsp;" and the party
    # regex never matches across it (measured: parties came back [] on a
    # page with two parties plainly visible).
    t = html.replace("&nbsp;", " ").replace("&amp;", "&")
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))
    if "Document No." not in t:
        return None
    doc = {"instrument": _field(t, "Document No.", "Book"),
           "book": _field(t, "Book", "Page"),
           "page": _field(t, "Page", "Document Type"),
           "doc_type": _field(t, "Document Type", "Date Recorded"),
           "recorded": _field(t, "Date Recorded", "Consideration"),
           "amount": _field(t, "Consideration Amount", "Status"),
           "status": _field(t, "Status", "View|BLOCKS")}
    # parties: rows of NAME  <name> Mortgagor/Mortgagee/etc. Structure-based:
    # each party sits in the PARTIES section as Name / Company / Party columns.
    # ⚠ SECTION ORDER ON THE PAGE IS BLOCKS *THEN* PARTIES (measured: BLOCKS at
    # 270, PARTIES at 554) - slicing PARTIES..BLOCKS yields an EMPTY segment and
    # zero parties on a page with two plainly visible. End at the Copyright
    # footer instead.
    # ⚠ PARSE THE TABLE, DO NOT ENUMERATE THE ROLE VOCABULARY. The first version
    # matched NAME followed by one of Mortgagor|Mortgagee|Grantor|... and failed
    # TWICE on the same document: "Party A"/"Party B" are real roles that were not
    # in the list, and a COMPANY party has an EMPTY name cell, so the "name then
    # role" shape never matched. Result: 0 parties on a document with two plainly
    # visible, indistinguishable from a genuinely partyless document. 9.8% of the
    # first 2,264 records banked this way. The source controls the role
    # vocabulary; we do not get to enumerate it.
    #
    # The table is unambiguous and structural:  Name | Company | Party
    parties = []
    _i = html.find("PARTIES")
    if _i >= 0:
        seg = html[_i:]
        _end = seg.find("</table>")
        seg = seg[:_end] if _end > 0 else seg
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", seg, re.S):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if len(tds) < 3:
                continue                       # header row (<th>) or spacer
            cells = []
            for c in tds[:3]:
                v = re.sub(r"<[^>]+>", " ", c).replace("&nbsp;", " ")
                v = v.replace("&amp;", "&").replace("&#39;", "'")
                cells.append(re.sub(r"\s+", " ", v).strip())
            name, company, role = cells
            # a party is a PERSON (name) or an ENTITY (company); keep both, and
            # keep which it was - "is this an LLC or a human" is a real signal
            label = name or company
            if not label:
                continue
            # ⚠ RECORD WHICH COLUMN IT CAME FROM, DO NOT INFER ENTITY TYPE.
            # A first version set is_company = (company and not name), which
            # asserted "this is a company" about every value in the Company
            # column - and the county routinely enters PEOPLE there on older
            # records: "XUE KAL GIN" and "XUE JUN HAO" both arrived that way.
            # The page tells us WHERE the clerk typed the name; it does not tell
            # us whether the party is a person or an entity. Storing the column
            # keeps the observation; inferring the type manufactures a fact.
            parties.append({"name": label, "role": role,
                            "column": "company" if (company and not name) else "name",
                            "person": name, "company": company})
    doc["parties"] = parties
    # lots: BLOCKS AND LOTS section, pairs of numbers
    lots = []
    seg2 = t[t.find("BLOCKS AND LOTS"):]
    seg2 = seg2[:seg2.find("Request for") if "Request for" in seg2 else len(seg2)]
    for m in re.finditer(r"\b(\d{1,5})\s+(\d{1,5})\b", seg2):
        lots.append((int(m.group(1)), int(m.group(2))))
    doc["bbls"] = sorted({f"5{b:05d}{l:04d}" for b, l in lots})
    # IMAGE STATE IS PUBLISHED, NOT GUESSED. The page says which it is:
    #   "View Imaged Document"          -> present
    #   "No Image Available At This Time" -> pending (measured 2026-08-18:
    #        doc 1016951 rec 8/18 pending · doc 1016134 rec 8/7 present)
    # So we never probe an image to learn whether an image exists, and we never
    # invent a re-check calendar - the marker is free with the fetch we already
    # make. ⚠ "pending" and "structurally imageless" are DIFFERENT STATES that
    # look identical on any single read; only age against the measured lag
    # distribution separates them, so store the OBSERVATION plus its date and
    # decide later. Collapsing them is what creates an unbounded retry loop.
    doc["image_state"] = image_state(html, doc.get("recorded", ""))
    return doc
