"""LIVE SYNC DELTA — the doc-id map against ACRIS ITSELF, not the monthly extract.

⚠ WHY THIS EXISTS. Every ACRIS dataset on the open-data portal is published
MONTHLY (declared by DOF, and measured 2026-08-18: all five moved together at
2026-08-10 13:35Z, `good_through_date` 2026-07-31). So `selection_daily.py`
polls a source that changes twelve times a year — "0 changed rows" is the
CORRECT answer on ~30 days out of 31, and it reads as "we are current" when it
means "nothing arrived". We are not behind ACRIS; the EXTRACT is 18-41 days
behind reality, ~1,300 recordings a day unseen.

⚠ DISCOVERY WAS THE MISSING CAPABILITY. Every live endpoint the project already
uses — DocumentImageView, GetImage, GetPdf — is keyed by a doc_id we must
ALREADY HOLD, and the only source of ids was the monthly index. This asks ACRIS
what was recorded instead of waiting to be told.

    POST /DS/DocumentSearch/DocumentTypeResult

⚠ THE doc_id IS NOT IN ANY URL. Grepping a result page for `doc_id=` returns
zero. It is a bare argument on each row's buttons:
    onclick='JavaScript:go_detail("2026072900842001")'

⚠ CONSTRAINTS, READ OFF /DS/Scripts/DocumentType.js — NOT GUESSED.
    - document type is MANDATORY: there is no all-types query, one per type
    - borough is MANDATORY: "0 ALL BOROUGHS" sits at index 0 and is rejected
    - date range is capped at 31 days; presets are 7 / 31 / DR
    - page size 10/25/50/99 via hid_max_rows, paged by hid_page
    - NO TOTAL COUNT IS DISPLAYED ANYWHERE. A sweep must page to exhaustion and
      CANNOT verify itself against a stated total — so this records WHY it
      stopped, and a run that hits the page cap is a LOWER BOUND, not a
      reconciliation.

⚠ THIS JOB ONLY DISCOVERS. It does NOT write document_map. A row there carries
page ranges from the mapper, and `no_image` is computed from total_pages — so
inserting a bare id would assert "ACRIS holds no image for this document",
which is a permanent claim about the record, and false. New ids go to a queue
for the mapper.

⚠ STATEN ISLAND: borough 5 returns RPTT and RPTT&RET ONLY. DEED / MTGE / RETT /
AGMT / SAT all answer "No Records Found" (measured 2026-08-18, and the index
agrees: 400 sampled legals borough-5 documents were RPTT or RPTT&RET without
exception). SI deeds sit with the Richmond County Clerk, whose index is behind
a reCAPTCHA. Known, not a defect to chase.

Pacing is deliberately slower than the browser managed (1.62 req/s). Going
faster than a person clicking is how a working channel becomes a closed one.
"""
import argparse
import hashlib
import http.cookiejar
import json
import pathlib
import re

import lexicon as LX
import sys
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://a836-acris.nyc.gov"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
# ⚠ PACE IS A CHOICE, NOT A MEASURED CEILING. 2.5s was picked on 2026-08-18
# while diagnosing the Bandwidth Notice. What actually tripped ACRIS was
# CONCURRENCY - 12,077 documents at CONC 16, cold, in a burst. Acquisition
# sustains EIGHTY connections at 93.8 pg/s for days without a trip. So a
# faster SEQUENTIAL pace introduces no new failure mode; raising
# concurrency would. Override with ACRIS_PACE; keep it sequential.
import os as _os
PACE = float(_os.environ.get("ACRIS_PACE") or 2.5)
BUDGET_BYTES = 40_000_000   # ⚠ A HARD RAIL, NOT A GUIDELINE. On 2026-08-18 a
                            # ~350 MB day tripped ACRIS's Bandwidth Notice and
                            # Login had to clear it. "I'll be careful" is not a
                            # control; a counter that aborts is. Raise it only
                            # deliberately, never to make a run finish.
_SPENT = [0]


class BudgetExceeded(RuntimeError):
    """Stop. The run is INCOMPLETE and must say so — never widen the budget to
    make the number look finished."""


def _spend(html):
    _SPENT[0] += len(html)
    if _SPENT[0] > BUDGET_BYTES:
        raise BudgetExceeded(
            f"byte budget exhausted: {_SPENT[0]/1e6:.1f} MB of "
            f"{BUDGET_BYTES/1e6:.0f} MB — run is INCOMPLETE, stopping")
    return html
MAX_ROWS = "99"
QUEUE = HERE / "_live_delta_queue.jsonl"
STATE = HERE / "_live_delta_state.json"

class Refused(RuntimeError):
    """⚠ ACRIS DECLINED. Stop the line of work — no retry, no rotating anything,
    no routing around it. Report it."""


def check_refused(html):
    """⚠ A REFUSAL ARRIVES AS HTTP 200. Measured 2026-08-18: after ~13,000
    requests in a day (a 12,077-document mapper run at concurrency 16, ~48/s,
    on top of a 900-request sweep), every ACRIS URL began returning the SAME
    25,103-byte "ACRIS Bandwidth Notice" page — status 200, no error, no header.
    Parsing it fails somewhere downstream and reads as a code bug, which is how
    a refusal gets retried into a longer refusal. Detect it at the door."""
    if "Bandwidth Notice" in html or "bandwidth" in html[:2000].lower():
        raise Refused("ACRIS served its Bandwidth Notice — REFUSED. Stop; do "
                      "not retry, do not rotate, do not raise concurrency.")


BOROUGHS = [("1", "MANHATTAN"), ("2", "BRONX"), ("3", "BROOKLYN"),
            ("4", "QUEENS"), ("5", "STATEN ISLAND")]
SI_ONLY = {"RPTT", "RPTT&RET"}


class Session:
    """Establishes a session the way any HTTP client is supposed to: visit the
    page and keep the cookies the server sets. Nothing is fabricated and no
    token is replayed that was not issued to us. If the server declines to
    issue a session, this stops rather than pushing."""

    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
        self.op.addheaders = [("User-Agent", UA)]
        self.token = None

    def open(self):
        with self.op.open(BASE + "/DS/DocumentSearch/", timeout=60) as r:
            r.read()
        time.sleep(PACE)
        req = urllib.request.Request(
            BASE + "/DS/DocumentSearch/DocumentType",
            headers={"Referer": BASE + "/DS/DocumentSearch/"})
        with self.op.open(req, timeout=60) as r:
            h = r.read().decode("utf-8", "replace")
        check_refused(h)
        g = re.search(r"<form name='global'.*?</form>", h, re.S)
        if not g:
            raise Refused("DocumentType returned no search form — the page is "
                          "not what it should be; stopping rather than guessing")
        self.token = re.search(
            r'__RequestVerificationToken" type="hidden" value="([^"]+)"',
            g.group(0)).group(1)
        return self

    def search(self, doctype, boro, boro_name, days, form_page, want_page,
               req_id=""):
        """⚠ THE PAGE NUMBER TRAVELS IN THE QUERY STRING, NOT THE FORM BODY.
        Read off /DS/Scripts/DocumentTypeResult.js:

            var URL = '/DS/DocumentSearch/DocumentTypeResult?page='
                      + (Number(g.hid_page.value) + 1);

        `hid_page` in the body stays at the page you came FROM; the server reads
        `?page=`. Posting hid_page=2 with no query string re-serves page 1, and
        because the corpus is ordered the same way each time, that looks like a
        successful fetch of identical rows — the sweep then stops on
        "repeat-page" believing it reached the end. Measured: Queens/DEED
        reported 198 rows -> 93 distinct ids, which is page 1 twice.
        """
        d = {"__RequestVerificationToken": self.token,
             "hid_doctype": doctype, "hid_doctype_name": doctype,
             "hid_selectdate": days,
             "hid_datefromm": "", "hid_datefromd": "", "hid_datefromy": "",
             "hid_datetom": "", "hid_datetod": "", "hid_datetoy": "",
             "hid_borough": boro, "hid_borough_name": boro_name,
             "hid_max_rows": MAX_ROWS, "hid_page": str(form_page),
             "hid_ReqID": req_id, "hid_SearchType": "DOCTYPE",
             "hid_ISIntranet": "N", "hid_sort": ""}
        url = BASE + "/DS/DocumentSearch/DocumentTypeResult"
        if want_page > 1:
            url += f"?page={want_page}"
        time.sleep(PACE)
        req = urllib.request.Request(
            url, data=urllib.parse.urlencode(d).encode(),
            headers={"Referer": BASE + "/DS/DocumentSearch/DocumentType",
                     "Content-Type": "application/x-www-form-urlencoded"})
        with self.op.open(req, timeout=120) as r:
            h = r.read().decode("utf-8", "replace")
        check_refused(h)
        return _spend(h)


    def open_crfn(self):
        """Second form, second token. The CRFN lookup is a DIFFERENT page from
        the document-type search and carries its own anti-forgery token."""
        req = urllib.request.Request(
            BASE + "/DS/DocumentSearch/CityRegisterFileNumber",
            headers={"Referer": BASE + "/DS/DocumentSearch/"})
        time.sleep(PACE)
        with self.op.open(req, timeout=60) as r:
            h = r.read().decode("utf-8", "replace")
        g = re.search(r"<form name='global'.*?</form>", h, re.S).group(0)
        self.crfn_token = re.search(
            r'__RequestVerificationToken" type="hidden" value="([^"]+)"',
            g).group(1)
        self.crfn_defs = dict(
            re.findall(r'name="(hid_\w+)"[^>]*value="([^"]*)"', g))
        return self

    def detail(self, crfn):
        """⚠ BOTH LOOKUPS POST TO ?SearchType=DocID — the server distinguishes
        by WHICH hidden field is filled, not by the query string. Sending
        SearchType=CRFN returns a uniform 10,182-byte empty page that is
        indistinguishable from a genuine "no such document", so a probe built
        that way reports every CRFN absent — including ones known to exist.
        That is why this is always run against a known-good control first."""
        d = dict(self.crfn_defs)
        d.update({"__RequestVerificationToken": self.crfn_token,
                  "hid_DocID": "", "hid_CRFN": str(crfn)})
        time.sleep(PACE)
        req = urllib.request.Request(
            BASE + "/DS/DocumentSearch/DocumentDetail?SearchType=DocID",
            data=urllib.parse.urlencode(d).encode(),
            headers={"Referer": BASE + "/DS/DocumentSearch/CityRegisterFileNumber",
                     "Content-Type": "application/x-www-form-urlencoded"})
        with self.op.open(req, timeout=90) as r:
            html = r.read().decode("utf-8", "replace")
        check_refused(html)
        _spend(html)
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        m = re.search(r"DOCUMENT ID:\s*([A-Za-z0-9_]{10,})", t)
        if not m:
            return None                      # unissued — no document at this number
        def fld(label):
            g = re.search(label + r":\s*([^:]{1,40}?)\s+[A-Z#%][A-Za-z.# ]{2,}:", t)
            return g.group(1).strip() if g else ""
        # ⚠ THE DETAIL PAGE RENDERS THE DESCRIPTION, THE CORPUS STORES THE CODE.
        # "DOC. TYPE" here reads MORTGAGE / SATISFACTION OF MORTGAGE, while the
        # bulk path and every calibration in lexicon.py use MTGE / SAT. Left raw,
        # the two spellings both land in document.doc_type and every GROUP BY
        # splits one type into two buckets. Normalised HERE because live_gap.py
        # imports this parser - one origin, so one place to fix.
        # ⚠ PASS THE DOC ID. canon() is ACRIS's vocabulary; handed an id it can
        # refuse to translate a foreign register's label. Omitting it asserts
        # ACRIS implicitly, and an implicit assertion is what rewrote 644,000
        # Richmond rows on 2026-08-19.
        return {"doc_id": m.group(1),
                "doc_type": LX.doc_type_canon(fld(r"DOC\. TYPE"), m.group(1)),
                "borough": fld("BOROUGH"), "pages": fld(r"# of PAGES")}


TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
BORO_DIGIT = {"MANHATTAN": 1, "BRONX": 2, "BROOKLYN": 3, "QUEENS": 4,
              "STATEN ISLAND": 5}


def _cells(tr):
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", td))
            .replace("&nbsp;", " ").strip() for td in CELL.findall(tr)]


def _bbl(boro, block, lot):
    """⚠ A DOC ID WITHOUT ITS BBLs IS AN ORPHAN WITH A NAME (LIVE_SYNC.md §8).
    Acquisition selects PARCELS and reaches documents through parcel_document;
    nothing anywhere reads the document table directly. So a delta that writes
    only document ids produces rows that are correct, present, and permanently
    unfetchable — and they sit in coverage.py as NOT YET HELD forever, looking
    exactly like work not yet done."""
    d = BORO_DIGIT.get(boro.upper().strip())
    if not d:
        return None
    try:
        return f"{d}{int(block):05d}{int(lot):04d}"
    except (TypeError, ValueError):
        return None                      # non-numeric lot — carry the doc, drop the link


def parse(html):
    """Rows out of a result page. The id is the button argument, not a URL.

    ⚠ ROWS ARE NOT DISTINCT IDS, AND CONFUSING THEM READS EVERY FULL PAGE AS A
    SHORT ONE. A document that touches several lots occupies several rows, so a
    FULL 99-row page returns only ~85-95 distinct ids. Testing
    `len(distinct) < 99` therefore declared exhaustion on page 1 of every single
    sweep — 15 of 15, all "short-page", all silently truncated to their first
    page. Paging must be decided on the RAW ROW COUNT.

    ⚠ AND THE ROW CARRIES THE PARCEL. Columns are
    View | Borough | Block | Reel/Pg/File | CRFN | Lot | Partial | Doc Date |
    Recorded/Filed | Pages | Party1 | Party2 | Party3 | More | Corrected |
    Amount — so one search yields the document AND its bbl links AND its page
    count, which is everything the specification needs except the page ranges.
    """
    rows = []
    for tr in TR.findall(html):
        m = re.search(r'go_image\("([A-Za-z0-9_]+)"\)', tr)
        if not m:
            continue
        c = _cells(tr)
        if len(c) < 10:
            continue
        rows.append({"doc_id": m.group(1), "bbl": _bbl(c[1], c[2], c[5]),
                     "borough": c[1], "block": c[2], "lot": c[5], "crfn": c[4],
                     "doc_date": c[7], "recorded": c[8], "pages": c[9]})
    raw = [r["doc_id"] for r in rows]
    ids = list(dict.fromkeys(raw))
    rec = re.findall(r"([0-9]{1,2}/[0-9]{1,2}/20[0-9]{2}) [0-9:]+ [AP]M", html)
    rq = re.search(r'name="hid_ReqID"[^>]*value="([^"]*)"', html)
    window = re.search(r"Records\s+([0-9,]+)\s*-\s*([0-9,]+)",
                       re.sub(r"<[^>]+>", " ", html))
    hp = re.search(r'name="hid_page"[^>]*value="([0-9]*)"', html)
    none = "No Records Found" in re.sub(r"<[^>]+>", " ", html)
    # The ROW SEQUENCE, not the id set — this is what distinguishes "the server
    # re-served the same page" from "one huge document spans several pages".
    sig = hashlib.sha1("|".join(raw).encode()).hexdigest()
    return (ids, len(raw), rec, (rq.group(1) if rq else ""), window, none,
            int(hp.group(1)) if hp and hp.group(1) else 0, sig, rows)


def sweep(s, doctype, boro, boro_name, days, cap_pages):
    """Page to exhaustion. ⚠ There is no stated total to check against, so this
    records WHY it stopped. A short page is exhaustion; a full page at the cap
    is NOT, and the caller must report that as incomplete coverage."""
    found, req_id, page, stopped, rows_total = {}, "", 1, "short-page", 0
    form_page, prev_sig, links, parse_gap = 1, None, set(), 0
    while page <= cap_pages:
        html = s.search(doctype, boro, boro_name, days, form_page, page, req_id)
        ids, rows, rec, rq, window, none, hp, sig, rowdicts = parse(html)
        if none or not ids:
            stopped = "no-records" if page == 1 else "empty-page"
            break
        # ⚠ "NO NEW IDS" IS NOT THE END OF THE RESULT SET, AND TREATING IT AS
        # THE END TRUNCATES EXACTLY THE BIGGEST DOCUMENTS. One row is one
        # document-LOT pair, so a condo declaration touching hundreds of lots
        # fills whole pages by itself: Manhattan/ADEC returned 198 rows across
        # two full pages carrying FIVE distinct ids. Only an IDENTICAL ROW
        # SEQUENCE proves the server re-served a page.
        if sig == prev_sig:
            stopped = "repeat-page(server re-served)"
            break
        prev_sig = sig
        req_id = rq or req_id
        form_page = hp or page          # what the server says we are on now
        rows_total += rows
        for rd in rowdicts:
            rd["doc_type"] = LX.doc_type_canon(doctype)
            found.setdefault(rd["doc_id"], rd)
            if rd["bbl"]:
                links.add((rd["bbl"], rd["doc_id"]))
        # ⚠ NEVER INFER THE END FROM A COUNT YOU DERIVED. `rows` is how many
        # rows this code managed to parse; it is not how many the server sent.
        # Queens/SAT returned 98 parseable rows against the 99 cap and the sweep
        # declared the list finished on page 1 — 94 documents kept where ~1,000
        # exist, and Brooklyn's same query returned 612. The page STATES its own
        # range ("Records 1 - 99") and offers a next link; read that instead.
        stated = None
        if window:
            try:
                a = int(window.group(1).replace(",", ""))
                b = int(window.group(2).replace(",", ""))
                stated = b - a + 1
            except ValueError:
                stated = None
        if stated is not None and rows != stated:
            # ⚠ A PARSE FAILURE, NOT AN ENDING. Report it and KEEP PAGING.
            parse_gap += stated - rows
        if "go_next()" not in html:
            stopped = "no-next(server says end)"
            break
        page += 1
    else:
        stopped = "HIT-PAGE-CAP"
    if parse_gap:
        stopped += f" ⚠PARSE-GAP:{parse_gap}"
    return found, stopped, page, rows_total, links


def known(ids):
    """Which of these the map already holds. Chunked, because a URL has limits."""
    import supabase_sync as S
    url, key = S._env()
    H = {"apikey": key, "Authorization": "Bearer " + key}
    have, ids = set(), list(ids)
    for i in range(0, len(ids), 80):
        q = ",".join('"' + x + '"' for x in ids[i:i + 80])
        req = urllib.request.Request(
            f"{url}/rest/v1/document_map?select=document_id&document_id=in.({q})",
            headers=H)
        with urllib.request.urlopen(req, timeout=90) as r:
            have |= {x["document_id"] for x in json.load(r)}
    return have


def resolve_holes(s, found, types, boros, cap):
    """⚠ RESOLVE EVERY HOLE OR SAY YOU DIDN'T. A hole in the CRFN sequence is
    one of three things and they are NOT interchangeable:

        unissued        no document at that number — verified, closed
        out of scope    a real document, but personal property / a borough or
                        type this sweep did not cover — expected
        MISSED          a document this sweep SHOULD have found — a real defect

    Measured 2026-07: 34,044 span, 34,033 held, 11 holes, and all 11 were
    unissued — confirmed one at a time against the register with a known-good
    control proving the probe worked. So the sequence really does reconcile to
    zero, and any residue is a finding rather than background noise.

    ⚠ THE CONTROL IS NOT OPTIONAL. The first version of this probe reported all
    11 absent AND reported the known-good control absent, because a malformed
    request returns the same empty page as a real negative. A checker that
    cannot fail visibly cannot be trusted when it passes.
    """
    crfns = sorted(int(r["crfn"]) for r in found.values()
                   if r.get("crfn", "").isdigit())
    if len(crfns) < 2:
        print("  holes: too few crfns to evaluate — UNKNOWN, not clean")
        return
    have = set(crfns)
    holes = [n for n in range(crfns[0], crfns[-1] + 1) if n not in have]
    print(f"\n  CRFN HOLE RESOLUTION — {len(holes):,} holes in the span")
    if not holes:
        print("  nothing to resolve; the sequence is dense -> RECONCILED AT 0")
        return

    s.open_crfn()
    control = str(crfns[len(crfns) // 2])
    got = s.detail(control)
    if not got:
        print(f"  ⚠ CONTROL {control} DID NOT RESOLVE — the probe is broken, "
              f"not the numbers. Refusing to classify any hole.")
        return
    print(f"  control {control} -> {got['doc_id']} ({got['doc_type']}) — probe OK")

    boro_names = {b[1] for b in boros}
    unissued, out_of_scope, missed, checked, ucc = 0, 0, [], 0, []
    for n in holes[:cap]:
        checked += 1
        d = s.detail(n)
        if d is None:
            unissued += 1
        elif d["doc_type"] in types and d["borough"].upper() in boro_names:
            missed.append((n, d))
        else:
            # ⚠ THIS IS THE PERSONAL-PROPERTY CHANNEL. /DS/DocumentSearch/UCC
            # takes a borough and a FILE NUMBER — there is no date search for
            # personal property anywhere in ACRIS, so a sweep for it cannot
            # exist. The CRFN holes left after a real-property sweep ARE those
            # documents (~5,733/month, ~190/day). Resolving them is the only
            # channel there is.
            #
            # ⚠ THEY GO TO A SEPARATE QUEUE, NOT THE MAIN ONE. `parcel_spec.db`
            # and `document_map` are defined as REAL PROPERTY. Feeding 4.5M UCC
            # documents into them silently redefines the denominator, and the
            # count everything is measured against would change without anyone
            # choosing it. Capture them, count them, land them only on a
            # decision.
            out_of_scope += 1
            ucc.append(d)
    residual = len(holes) - checked
    print(f"   unissued (no document)      {unissued:,}")
    print(f"   personal property / other  {out_of_scope:,}")
    if ucc:
        uq = HERE / "_live_delta_ucc.jsonl"
        with uq.open("a", encoding="utf-8") as f:
            for d in ucc:
                f.write(json.dumps(d) + chr(10))
        print(f"     -> {len(ucc):,} captured to {uq.name} "
              f"(NOT landed: document_map is real property by definition)")
    print(f"   ⚠ MISSED by this sweep      {len(missed):,}")
    for n, d in missed[:10]:
        print(f"       crfn {n} -> {d['doc_id']} {d['doc_type']} {d['borough']}")
    if residual:
        print(f"   ⚠ UNRESOLVED {residual:,} holes — capped at {cap:,}. This run "
              f"is NOT a zero reconciliation; raise --resolve-cap to close it.")
    elif not missed:
        print("   -> RECONCILED AT 0: every hole accounted for")
    return missed


def crfn_check(found, boros):
    """⚠ THE DENOMINATOR THE SEARCH REFUSES TO PRINT.

    No result page states a total, so a sweep cannot otherwise prove it saw
    everything — and a truncated sweep and a complete one look identical. But
    ACRIS issues CRFN as a STRICT CITYWIDE COUNTER across both corpora, and it
    is essentially gapless. Measured 2026-07 against the published index:

        real property     28,300 docs   crfn 2026000182577 .. 2026000216616
        personal property  5,733 docs   crfn 2026000182573 .. 2026000216605
        combined          34,033        span                          34,040
                          -> 99.98% accounted, 7 unexplained in a whole month

    June ends 2026000182572 and July opens 2026000182577, so the sequence runs
    continuously across months too. That makes ΔCRFN between two runs the exact
    number of documents recorded citywide in between — a watermark that cannot
    silently rot, because a missing number is VISIBLE where a missing date is not.

    ⚠ EXPECTED DENSITY IS NOT 100% AND MUST NOT BE READ AS A FAILURE. This sweep
    covers real property in the boroughs asked for, so the CRFNs it will never
    hold are the personal-property ones (~17% of the sequence, they go through
    /DS/DocumentSearch/UCC) plus Staten Island and any borough not swept.
    Materially below that floor means documents were missed — a type not swept
    or paging that stopped early — not that ACRIS skipped numbers.
    """
    crfns = sorted({r["crfn"] for r in found.values()
                    if r.get("crfn", "").isdigit()})
    if len(crfns) < 2:
        print("  crfn check: too few to evaluate — UNKNOWN, not clean")
        return
    span = int(crfns[-1]) - int(crfns[0]) + 1
    density = len(crfns) / span * 100
    floor = 83.0 - (0 if len(boros) >= 5 else 1.0)   # ~17% personal + SI
    print(f"  crfn {crfns[0]} .. {crfns[-1]} · span {span:,} · held "
          f"{len(crfns):,} ({density:.1f}%)")
    print(f"  expected ~{floor:.0f}% for a full real-property sweep "
          f"(personal property + unswept boroughs take the rest)")
    if density >= floor - 5:
        print("  -> CONSISTENT WITH FULL COVERAGE")
    else:
        # ⚠ ONE VERDICT, NOT TWO. An earlier version printed "plausible" and
        # "INCOMPLETE" on consecutive lines, which is how a check stops being
        # believed — the reader keeps whichever line they liked.
        print(f"  -> INCOMPLETE: {span - len(crfns):,} numbers in the range are "
              f"not accounted for, ~{floor - density:.0f} points below the "
              f"floor. A type not swept and paging that stopped early both "
              f"look exactly like this.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", default="7", choices=["7", "31"])
    ap.add_argument("--types", default="DEED,MTGE,RPTT")
    ap.add_argument("--boroughs", default="1,2,3,4,5")
    ap.add_argument("--cap-pages", type=int, default=40)
    ap.add_argument("--write-queue", action="store_true")
    ap.add_argument("--resolve-holes", action="store_true")
    ap.add_argument("--resolve-cap", type=int, default=400)
    a = ap.parse_args()

    if a.types.upper() == "ALL":
        # ⚠ THE VOCABULARY IS 126 TYPES, NOT 95. The control-code table
        # `7isb-wh4c` holds 126; 95 of them occur in the real property master,
        # 29 are UCC AND FEDERAL LIENS that live in the PERSONAL property
        # corpus and are searched through /DS/DocumentSearch/UCC instead, and 2
        # (REIT, SI CORR) occur nowhere. Sweeping the UCC types here spends a
        # request each to be told "No Records Found".
        import bulk
        codes = bulk.socrata("7isb-wh4c", paginate=True, limit=1000)
        types = sorted({c["doc__type"].strip() for c in codes
                        if c.get("class_code_description") !=
                        "UCC AND FEDERAL LIENS"})
    else:
        types = [t.strip() for t in a.types.split(",") if t.strip()]
    boros = [b for b in BOROUGHS if b[0] in a.boroughs.split(",")]
    print(f"ACRIS LIVE DELTA — last {a.days} days · {len(types)} type(s) × "
          f"{len(boros)} borough(s)\n")

    s = Session().open()
    all_found, incomplete, all_links = {}, [], set()
    for boro, bname in boros:
        for t in types:
            if boro == "5" and t not in SI_ONLY:
                print(f"  {bname:<14} {t:<10} skipped — SI carries only "
                      f"{'/'.join(sorted(SI_ONLY))}")
                continue
            found, why, pages, rows, lk = sweep(s, t, boro, bname, a.days,
                                                a.cap_pages)
            all_links |= lk
            if why == "HIT-PAGE-CAP":
                incomplete.append((bname, t))
            print(f"  {bname:<14} {t:<10} {rows:>6} rows -> {len(found):>5} ids · "
                  f"{pages} page(s) · stopped: {why}")
            all_found.update(found)

    print(f"\n  {len(all_found):,} distinct ids · {len(all_links):,} parcel "
          f"links · {len({b for b, _ in all_links}):,} distinct bbls")
    crfn_check(all_found, boros)
    if a.resolve_holes:
        resolve_holes(s, all_found, set(types), boros, a.resolve_cap)
    if not all_found:
        return
    have = known(all_found)
    new = {k: v for k, v in all_found.items() if k not in have}
    print(f"  already in document_map : {len(have):,}")
    print(f"  NOT IN THE MAP          : {len(new):,}")

    if incomplete:
        print("\n  ⚠ COVERAGE INCOMPLETE — these hit the page cap, so the counts "
              "above are a LOWER BOUND, not a reconciliation:")
        for b, t in incomplete:
            print(f"      {b} {t}")

    if a.write_queue and new:
        by_doc = {}
        for b, d in all_links:
            by_doc.setdefault(d, []).append(b)
        with QUEUE.open("a", encoding="utf-8") as f:
            for k, v in sorted(new.items()):
                rec = dict(v)
                # ⚠ EVERY BBL THE DOCUMENT TOUCHES, not the one row we happened
                # to see it on — the links ARE the reachability (LIVE_SYNC §8).
                rec["bbls"] = sorted(set(by_doc.get(k, [])))
                f.write(json.dumps(rec) + "\n")
        print(f"\n  queued {len(new):,} ids -> {QUEUE.name} (for the mapper; "
              f"this job never writes document_map itself)")

    STATE.write_text(json.dumps(
        {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "days": a.days,
         "types": types, "boroughs": [b[0] for b in boros],
         "discovered": len(all_found), "known": len(have), "new": len(new),
         "incomplete": incomplete}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
