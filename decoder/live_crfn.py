"""LIVE SYNC BY CRFN — the delta as a COUNTER WALK, not a search sweep.

    python live_crfn.py --check            report the gap, write nothing
    python live_crfn.py --walk --limit N   walk it, queue what is new

⚠ WHY THIS REPLACES THE TYPE×BOROUGH SWEEP. The sweep asks 97 document types ×
5 boroughs and pages each result set, and it can be wrong in ways nothing shows:
a type missing from the list, a page that stops early, a result set the server
re-serves. Both of today's paging bugs were of exactly that shape and both
looked like clean runs.

CRFN cannot fail that way. ACRIS issues it as a STRICT CITYWIDE COUNTER across
both corpora, and it is dense — measured 2026-07:

    real property     28,300 · personal property 5,733 · combined 34,033
    crfn span 34,044 · 11 holes, ALL verified unissued
    -> 99.98% dense, and the sequence runs unbroken across month boundaries
       (June ends 2026000182572, July opens 2026000182577)

So "the delta" is simply every number after the watermark. There is no type list
to maintain, no borough loop, no paging, and completeness is structural rather
than argued: the numbers are consecutive, so a gap is arithmetic, not opinion.

⚠ AND THE DETAIL PAGE CARRIES THE PARCELS, which is what makes this safe to land.
One lookup returns doc id, type, dates, page count, amount AND the full property
table — borough, block, lot, partial, property type, easement, air rights,
subterranean, address. That is every `parcel_document` column, so no document
lands as an orphan for want of a link (LIVE_SYNC.md §8).

⚠ A NUMBER THAT RETURNS NOTHING IS "UNISSUED", NOT "MISSING" — but only once the
probe is proven. A malformed request returns the same empty page as a genuine
absence, so this ALWAYS runs a known-good control first and refuses to classify
anything if the control does not resolve. That check caught a probe that had
reported all 11 July holes absent AND the control absent.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import urllib.parse
import urllib.request

import live_delta as LD


def detail_html(s, crfn):
    """Raw page. LD.Session.detail() returns a parsed dict; the property table
    it drops is exactly what makes a document reachable, so fetch it whole."""
    d = dict(s.crfn_defs)
    d.update({"__RequestVerificationToken": s.crfn_token,
              "hid_DocID": "", "hid_CRFN": str(crfn)})
    time.sleep(LD.PACE)
    req = urllib.request.Request(
        LD.BASE + "/DS/DocumentSearch/DocumentDetail?SearchType=DocID",
        data=urllib.parse.urlencode(d).encode(),
        headers={"Referer": LD.BASE + "/DS/DocumentSearch/CityRegisterFileNumber",
                 "Content-Type": "application/x-www-form-urlencoded"})
    # ⚠ RETRY OR THE RUN DIES ON ONE TRANSIENT. On 2026-08-18 a single HTTP 307
    # killed a walk on its FIRST document, right after the control resolved — the
    # same request succeeded 90 seconds later. Over thousands of lookups a
    # transient is near-certain, not unlucky. Back off; do NOT retry a refusal.
    last = None
    for attempt in range(4):
        try:
            with s.op.open(req, timeout=90) as r:
                h = r.read().decode("utf-8", "replace")
            LD.check_refused(h)          # a refusal arrives as HTTP 200
            return h
        except Exception as e:
            if type(e).__name__ == "Refused":
                raise
            last = e
            time.sleep(2 ** attempt * 2)
    raise last

QUEUE = HERE / "_live_delta_queue.jsonl"
STATE = HERE / "_live_crfn_state.json"
BORO = {"MANHATTAN": 1, "BRONX": 2, "BROOKLYN": 3, "QUEENS": 4,
        "STATEN ISLAND": 5}


def parse_parties(html):
    """EVERY party row, from the HTML STRUCTURE - never the flattened text.

    Flattened text scrambles sections (each section's DATA lands under the NEXT
    heading) and cannot split NAME from ADDRESS 1. The structure is unambiguous:
    a "PARTY N" banner row, then data rows <tr bgcolor="#FFFFFF"> with one <td>
    per field: name, addr1, addr2, city, state, zip, country. A party side can
    hold SEVERAL rows (the scroll div) - all of them are kept.
    """
    import re as _re
    out = []
    marks = [(m.start(), m.group(1))
             for m in _re.finditer(r">PARTY (\d)(?:/Other)?<", html)]
    for i, (pos, num) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else html.find("PARCELS", pos)
        seg = html[pos:end if end > pos else len(html)]
        for row in _re.finditer(r'<tr bgcolor="#FFFFFF">(.*?)</tr>', seg, _re.S):
            cells = []
            for c in _re.findall(r"<td[^>]*>(.*?)</td>", row.group(1), _re.S):
                v = _re.sub(r"<[^>]+>", " ", c).replace("&nbsp;", " ")
                cells.append(_re.sub(r"\s+", " ", v).strip())
            if not cells or not cells[0]:
                continue
            out.append({"party_type": num, "name": cells[0],
                        "address_1": cells[1] if len(cells) > 1 else "",
                        "address_2": cells[2] if len(cells) > 2 else "",
                        "city": cells[3] if len(cells) > 3 else "",
                        "state": cells[4] if len(cells) > 4 else "",
                        "zip": cells[5] if len(cells) > 5 else "",
                        "country": cells[6] if len(cells) > 6 else ""})
    return out


def parse_detail(html):
    """Doc header + EVERY property row. Returns None when no document exists."""
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).replace("&nbsp;", " ")
    m = re.search(r"DOCUMENT ID:\s*([A-Za-z0-9_]{10,})", t)
    if not m:
        return None

    def fld(label, stop):
        g = re.search(label + r":\s*(.*?)\s*" + stop, t)
        return g.group(1).strip() if g else ""

    doc = {"doc_id": m.group(1),
           "crfn": fld("CRFN", "COLLATERAL"),
           "pages": fld(r"# of PAGES", "REEL-PAGE"),
           "doc_type": fld(r"DOC\. TYPE", "FILE NUMBER"),
           "doc_date": fld(r"DOC\. DATE", "RECORDED / FILED"),
           "recorded": fld("RECORDED / FILED", r"SLID"),
           "amount": fld(r"DOC\. AMOUNT", "BOROUGH"),
           "borough": fld("BOROUGH", "%")}

    # ⚠ THE PROPERTY TABLE IS NESTED, so a <tr>...</tr> regex matches the INNER
    # closing tag first and shreds the cells — it reported 14 of 15 documents as
    # propertyless, which would have dropped their links silently. Read the
    # flattened property SECTION instead: it is bounded by the column header and
    # the REFERENCES block, and every row starts with a borough NAME.
    lo = t.find("SUBTERRANEAN")
    hi = t.find("REFERENCES", lo if lo > 0 else 0)
    seg = t[lo:hi if hi > lo else len(t)] if lo > 0 else ""
    props = []
    for m in re.finditer(r"(MANHATTAN|BRONX|BROOKLYN|QUEENS|STATEN ISLAND)\s+"
                         r"(\d{1,5})\s+(\d{1,5})\s+(ENTIRE LOT|PARTIAL LOT)",
                         seg):
        props.append({"bbl": f"{BORO[m.group(1)]}{int(m.group(2)):05d}"
                             f"{int(m.group(3)):04d}",
                      "partial": m.group(4)})
    doc["parties"] = parse_parties(html)
    doc["bbls"] = sorted({p["bbl"] for p in props})
    doc["props"] = props
    return doc


def watermark():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))["crfn"]
    # Seed from the delta already landed, else from the published extract's max.
    if QUEUE.exists():
        mx = max(int(json.loads(l)["crfn"]) for l in
                 QUEUE.open(encoding="utf-8") if json.loads(l).get("crfn", "").isdigit())
        return mx
    sys.exit("  no watermark and no queue — seed with --from")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--walk", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--from", dest="frm", type=int, default=0)
    ap.add_argument("--limit", type=int, default=2000)
    ap.add_argument("--stop-after-blank", type=int, default=25,
                    help="consecutive unissued numbers that mean END OF SEQUENCE")
    a = ap.parse_args()

    start = a.frm or (watermark() + 1)
    print(f"LIVE SYNC BY CRFN\n  watermark {start - 1} -> walking from {start}")

    s = LD.Session().open().open_crfn()
    # ⚠ CONTROL FIRST. Never classify a blank as unissued on an unproven probe.
    ctrl = start - 1
    if not parse_detail(detail_html(s, ctrl)):
        sys.exit(f"  ⚠ CONTROL {ctrl} did not resolve — probe unproven, refusing "
                 f"to walk. A malformed request looks exactly like an empty one.")
    print(f"  control {ctrl} resolves — probe OK")
    if a.check:
        print("  --check: nothing walked.")
        return

    found, unissued, blanks, n = [], 0, 0, 0
    while n < a.limit and blanks < a.stop_after_blank:
        crfn = start + n
        d = parse_detail(detail_html(s, crfn))
        n += 1
        if d is None:
            unissued += 1
            blanks += 1
            continue
        blanks = 0
        d["crfn"] = str(crfn)
        found.append(d)
        if len(found) % 50 == 0:
            print(f"    {len(found):,} documents · {unissued} unissued · at {crfn}")

    reached = start + n - 1 - blanks
    print(f"\n  walked {n:,} numbers -> {len(found):,} documents, "
          f"{unissued} unissued")
    print(f"  {sum(len(d['bbls']) for d in found):,} parcel links · "
          f"{sum(1 for d in found if not d['bbls'])} propertyless")
    if blanks >= a.stop_after_blank:
        print(f"  reached the END OF THE ISSUED SEQUENCE at {reached} "
              f"({blanks} consecutive unissued)")
    else:
        print(f"  stopped on --limit; MORE REMAINS after {reached}")

    if found:
        with QUEUE.open("a", encoding="utf-8") as f:
            for d in found:
                f.write(json.dumps(d) + "\n")
        print(f"  appended {len(found):,} -> {QUEUE.name}")
    STATE.write_text(json.dumps(
        {"crfn": reached, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "walked": n, "documents": len(found), "unissued": unissued},
        indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
