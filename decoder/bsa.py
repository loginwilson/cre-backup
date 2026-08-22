"""BSA — the only agency that moves the envelope by writing a sentence.

WHY THIS SOURCE EXISTS IN AN ENVELOPE LEDGER

    Zoning says what a lot may hold. The Board of Standards and Appeals says
    what THIS lot may hold, and its resolution outranks the district. A §72-21
    variance is therefore not a permit and not an opinion — it is a permanent
    amendment to one parcel's envelope, and it is only ever stated in prose.

    On 2025-12-BZ the district permitted 102,341.6 sf (2.0 FAR) and 150 dwelling
    units. The Board granted 232,985.77 sf (4.55 FAR) and 310 units. Nothing in
    any structured feed carries either number. Both are sentences on page 4 and
    page 11 of a PDF.

WHAT A RESOLUTION IS SHAPED LIKE (measured, 2026-08-06, 13-page §72-21)

    p1   header: MEETING OF · CALENDAR NO. · PREMISES · Block/Lot · ACTION ·
         THE VOTE · then THE RESOLUTION, which QUOTES THE DOB OBJECTION —
         this is the authoritative list of WHAT WAS WAIVED, with ZR cites
    p1-2 I. The Request — the relief in one sentence, "contrary to ..."
    p2   hearing dates, applicant identity, community board recommendation
    p3   II. Location — lot area, frontage, existing improvement
         III. Proposal — proposed floor area, FAR, DU, height, coverage, parking
    p4   the AS-OF-RIGHT MAXIMA the district would allow  <- the baseline
    p4+  IV. Findings (a)-(e), V. environmental
    pN-1 VII. Decision — "Therefore, it is Resolved ... on further condition:"
         then a run of THAT-clauses. THOSE BIND THE SITE PERMANENTLY.
    pN   CERTIFICATION — "filed by the Board on <date>"

    So the document is dated on BOTH axes the ledger wants: ADOPTED (happened)
    and FILED (recorded). On 2025-12-BZ that is June 1 and June 26, 2026.

⚠ TRAPS FOUND HERE (each one cost a wrong answer first)

  1. THE INDEX LOT IS NOT THE PARCEL. yvxd-uipr says 2025-12-BZ is Block 10789
     Lot 0027. Block 10789 HAS NO LOT 27. The resolution says Lot 271, which is
     220-28 Jamaica Avenue in PLUTO — the address the index itself carries.
     Measured over all 2015+ single-lot cases: 20.4% of index BBLs do not exist
     in PLUTO. Most are lineage (ground lot -> 75xx condo billing lot), but the
     index is a filing-time snapshot either way. THE PDF STATES THE PARCEL; the
     index only suggests it.

  2. `lots` IS FREE TEXT AND IS TRUNCATED AT 20 CHARACTERS. Real values include
     '1,28,29,30,105,1001-' and '82,83,84,85 (tent 82' — both cut mid-lot. 1,365
     of 10,805 rows are non-numeric. A multi-lot assemblage variance therefore
     cannot have its parcel set read from the index at all.

  3. 'tent.' MEANS THE LOT DOES NOT EXIST YET. '50, 63 (tent. 52)' is a merger
     that has not happened. Treating a tentative lot as a BBL invents a parcel.

  4. A 403 FROM www.nyc.gov IS A USER-AGENT BLOCK, NOT A REFUSAL. The default
     python-urllib UA gets 403 on robots.txt itself; any descriptive UA gets
     200 and the policy is `Disallow: /html/misc/` — nothing else. The policy
     was always published; the default UA just could not read it.

  5. THE KICKOFF'S TYPE COUNTS WERE WRONG and would have set the denominator
     wrong. Measured: BZ 4,182 · Appeal 3,449 · SOC 2,910 · BZY 257 (not
     1,859 / 1,668 / 1,350). Total 10,805 is right.

  6. A GRANT IS NOT ALWAYS A GRANT. `status` carries Withdrawn 1,112 and Denied
     525. A denied variance that emitted `variance_granted` would put floor area
     on a parcel that never got it.
"""
import hashlib, json, os, pathlib, re, sys, time, urllib.request
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import bulk
import facts as F
import sink

SOURCE = "BSA"
APPLICATIONS = "yvxd-uipr"          # 10,805 rows, 100% carry decisions_url
# ⚠ BSA-LOCAL PARSER VERSION, separate from facts.PARSER on purpose. The sink is
# append-only and shared with decoders this chat does not own, so a bad batch
# cannot be deleted — it can only be made IDENTIFIABLE. Every BSA fact carries
# this string, so "re-read everything written by bsa/1" is a query rather than
# an archaeology problem.
#   bsa/1  first pass. Cited the Proposal page for granted figures and collapsed
#          granted building height onto the district height. SUPERSEDED — do
#          not read bsa/1 rows.
#   bsa/2  region-anchored; exact flat->page map; running header stripped;
#          proposed layer separated from granted; split-site caps flagged.
#          Still one regex per phrasing, so it read 42% of its corpus and could
#          not say what it had missed. SUPERSEDED.
#   bsa/3  lexicon-driven: three sentence SHAPES plus a phrase lexicon, with
#          every unmatched phrase recorded as `unmapped` so the gap is counted
#          rather than invisible. Sections located by NAME (the roman numeral
#          moves). Relief classified use|bulk|both, which is what makes the
#          coverage denominator honest: 89% of dimensional multi-page grants.
#   bsa/4  document-sourced: the grant/deny outcome and the borough now come
#          from the resolution's own first page, not from the index's status and
#          borough_code columns; the index is demoted to a check. Every fact
#          carries pages_read/pages_total and the BBL's provenance.
#   bsa/5  VERIFIED BY EYE against 2021-44-BZ and corrected. bsa/4 truncated
#          feet-inches (11'-6" stored as 11.0 — six inches wrong, on the
#          house-scale variances that are most of the corpus), emitted junk
#          `depth`/`width` parameters duplicating real ones, missed the
#          "a maximum of 0.50 FAR is permitted" word order entirely, and
#          measured coverage as PRESENCE (any parameter found) rather than
#          COMPLETENESS (parameters found vs bounds the document states).
#   bsa/6  ⚠ THE BIG ONE. Spot-checking ten deliberately different documents
#          (BZY, SOC, Appeal, pre-2005 BZ, multi-lot) revealed a SECOND
#          RESOLUTION FORMAT. BSA changed format in 2020: everything decided
#          2019 or earlier is the "bulletin" layout — ACTION OF THE BOARD,
#          PREMISES AFFECTED, "Borough of Manhattan", adoption date in a
#          certification line. Measured over 1,747 cached decisions: 67.9%
#          bulletin, 24.0% modern. bsa/1-5 were built against 2020+ documents
#          and could not read the outcome on 74.7% of the corpus, nor the
#          borough on 68.5%. Every coverage figure before bsa/6 described the
#          quarter of the corpus that happens to be recent.
#          Also: format B bundles cases ("104-08-BZY thru 119-08-BZY"), and its
#          lots belong to the series rather than to one calendar number.
#   bsa/7  audit of what the DOCUMENT contains vs what the decoder took, over
#          577 cached resolutions. Six things present and untaken: the vote
#          tally (98.8%), the public hearing date (93.9%), the applicant/agent
#          (91.9%), the approved-plans sheet count (64.1%), the Community Board
#          recommendation (60.5%) and — the one that changes an answer — a TERM
#          or EXPIRY deadline (46.4%). A grant whose deadline has passed is not
#          a live entitlement, and nothing else in the record says so.
PARSER_NOTE = "bsa/7"

CACHE = pathlib.Path(os.environ.get("BSA_CACHE",
                                    pathlib.Path(__file__).with_name("bsa_cache")))
# Identify honestly. The 403 in trap 4 was the default UA, not the policy.
UA = ("BSA-decoder/1.0 (NYC parcel research, public BSA decisions; "
      "contact loginwilson88@gmail.com)")
PACE = 2.0                          # seconds between fetches. unhurried by rule.
_last = [0.0]


# ---------------------------------------------------------------- retrieval

def robots_ok(host="https://www.nyc.gov"):
    """Read the policy before relying on it. Returns (allowed_paths_note, text)."""
    req = urllib.request.Request(host + "/robots.txt", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "replace")


def fetch(url, calendar):
    """Cached, paced fetch of one decision PDF. Three outcomes, never inferred."""
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / (re.sub(r"[^A-Za-z0-9._-]", "_", calendar) + ".pdf")
    if p.exists() and p.stat().st_size > 0:
        return p, "cached"
    wait = PACE - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
        ctype = r.headers.get("Content-Type", "")
    if not body.startswith(b"%PDF"):
        return None, f"NOT_PDF ctype={ctype} bytes={len(body)}"
    p.write_bytes(body)
    return p, "fetched"


def pages(pdf_path):
    """Per-page text. Page numbers are not decoration — a fact without one is
    not a fact this project keeps."""
    import pypdf
    r = pypdf.PdfReader(str(pdf_path))
    return [(pg.extract_text() or "") for pg in r.pages]


HEADER = re.compile(r"^\s*(?:[0-9]{1,4}[-–][0-9]{1,4}-[A-Z]{1,4}[IVX]*\s*)?"
                    r"(?:\n|\s)*[0-9]{1,3}\s*(?:\n|$)")


def strip_running_header(page_texts):
    """Remove the '<calendar> / <page no>' banner that opens every page after
    the first.

    ⚠ WHY THIS IS NOT COSMETIC. A resolution's sentences run across pages, and
    the banner lands INSIDE them. Unstripped, page 1-2 reads:

        "dwelling unit (Z.R. 2025-12-BZ 2 §§ 23-52(b) ..."

    so any pattern that spans the break either fails to match or captures the
    calendar number as if it were part of the citation. The banner is the only
    text in the document that is not part of the document.
    """
    out = [page_texts[0] if page_texts else ""]
    for t in page_texts[1:]:
        m = HEADER.match(t)
        out.append(t[m.end():] if m else t)
    return out


class Doc:
    """Full text, a flattened copy for matching, and an EXACT map between them.

    ⚠ THE BUG THIS CLASS EXISTS TO PREVENT. The Board typesets across line
    breaks ("maximum base h eight", "35 -22(a)"), so matching has to happen on a
    whitespace-flattened copy. But the flattened copy has different offsets, so
    a match position in it cannot address a page. The first version resolved the
    page by searching the pages for a distinctive token from the match — and
    that is silently wrong, because THE SAME NUMBERS APPEAR TWICE IN EVERY
    RESOLUTION: once in III. Proposal (what was asked for) and again in VII.
    Decision (what was granted). 16,041.79 sf was cited to page 3 when the
    binding statement is on page 11. The citation pointed at a real page with
    the real number and the wrong legal meaning.

    So the flattening keeps a per-character index back into the paginated text.
    Positions are exact, and a page is looked up, never guessed.
    """

    def __init__(self, calendar, page_texts):
        self.calendar = calendar
        self.page_texts = page_texts
        self.starts, buf = [], []
        off = 0
        for t in page_texts:
            self.starts.append(off)
            buf.append(t)
            off += len(t) + 1
        self.text = "\n".join(buf)
        flat, back, prev_ws = [], [], False
        for i, ch in enumerate(self.text):
            if ch.isspace():
                if prev_ws:
                    continue
                flat.append(" ")
                back.append(i)
                prev_ws = True
            else:
                flat.append(ch)
                back.append(i)
                prev_ws = False
        self.flat = "".join(flat)
        self._back = back

    def orig(self, flat_pos):
        """Flat offset -> offset in the paginated text. Exact, not inferred."""
        if not self._back:
            return 0
        return self._back[min(flat_pos, len(self._back) - 1)]

    def page_of(self, pos):
        n = 1
        for i, s in enumerate(self.starts):
            if pos >= s:
                n = i + 1
        return n

    def page_of_flat(self, flat_pos):
        return self.page_of(self.orig(flat_pos))

    def find(self, pattern, flags=re.I):
        return re.search(pattern, self.text, flags)


# ---------------------------------------------------------------- parsing

def _num(s):
    return float(re.sub(r"[,\s]", "", s))


# ⚠ FEET-AND-INCHES ARE HALF THE CORPUS AND I WAS DROPPING THE INCHES.
#
#   2021-44-BZ, granted:  "a front yard measuring 11'-6" at the first floor"
#   what the decoder stored:  11.0
#
# The number was cited to the right page, passed every self-check, and was six
# inches wrong. House-scale variances — the 631 §73-622 single-family
# enlargements, the side-yard and rear-yard cases — are written almost entirely
# in feet-inches, so this was a silent systematic error across the largest
# population in the corpus. A truncated measurement is worse than a missing one:
# a gap gets investigated, a plausible number gets used.
FT_IN = re.compile(r"([\d,]+)\s*['′]\s*[-–]?\s*(\d{1,2})\s*[\"″]")


def _feet(text, fallback):
    """Feet as a decimal, from either 11'-6\" or '11 feet'. Returns
    (value, exact) — `exact` is False when only feet were stated, so a
    downstream comparison can tell a rounded figure from a precise one."""
    m = FT_IN.search(text)
    if m:
        return round(_num(m.group(1)) + int(m.group(2)) / 12.0, 4), True
    return fallback, True


def _tidy(s, limit=400):
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]


BOROUGH_NUM = {"manhattan": 1, "bronx": 2, "brooklyn": 3, "queens": 4,
               "staten island": 5}

# ═══════════════════════════════════════════════════════════════════════════
# ⚠⚠ THERE ARE TWO BSA RESOLUTION FORMATS AND I BUILT FOR THE MINORITY ONE.
#
# Found 2026-08-06 by spot-checking ten deliberately DIFFERENT documents —
# BZY, SOC, Appeal, pre-2005 BZ, multi-lot — instead of more §72-21 variances.
# Eight of the ten came back with no outcome, no dates, no borough, and lot
# lists like [129,128,127,126,120,...]. They were not malformed. They are a
# different document.
#
#   FORMAT A — "modern standalone"        FORMAT B — "bulletin"
#   ────────────────────────────────      ─────────────────────────────────
#   MEETING OF: June 1, 2026              341-02-BZ
#   CALENDAR NO.: 2025-12-BZ              APPLICANT – Sheldon Lobel, P.C.,
#   PREMISES: 220-28 Jamaica Ave,           for 231 E 58 St Assoc LLC, owner.
#     Queens                              SUBJECT – Application March 25,
#   Block 10789, Lot 271                    2014 – Amendment of ...
#   ACTION OF BOARD — granted             PREMISES AFFECTED – 231 East 58th
#   THE VOTE —                              Street, ..., Block 1332, Lot 16,
#                                           Borough of Manhattan.
#                                         ACTION OF THE BOARD – granted
#                                         THE VOTE TO GRANT –
#
# Every anchor differs: ACTION OF **THE** BOARD, PREMISES **AFFECTED**, the
# borough spelled "Borough of Manhattan" rather than trailing the address, the
# adoption date in "A true copy of resolution adopted by the Board ... , July
# 15, 2014" rather than "MEETING OF:", and an en-dash where A uses an em-dash.
#
# MEASURED ON THE LIVE RUN: of 1,654 decoded documents, 1,235 (74.7%) had an
# outcome the decoder could not read, and 1,133 (68.5%) had to borrow the
# borough from the index. THE FORMAT I BUILT FOR IS A QUARTER OF THE CORPUS.
# Every coverage figure reported before this point described that quarter.
#
# ⚠ AND FORMAT B BUNDLES CASES. 112-08-BZY's document is headed "104-08-BZY
# thru 119-08-BZY" and its PREMISES line lists sixteen lots — one resolution
# deciding sixteen applications. Attributing all sixteen lots to one calendar
# number invents fifteen parcel relationships. This is the same trap ACRIS
# found as "one recording bundles several instruments".
# ═══════════════════════════════════════════════════════════════════════════

DASH = r"[-–—]"
SERIES = re.compile(r"\b(\d{1,4}-\d{2}-[A-Z]{1,4})\s*(?:thru|through)\s*"
                    r"(\d{1,4}-\d{2}-[A-Z]{1,4})\b", re.I)


def document_format(doc):
    """Which of the two the PDF is. 'unknown' is a real answer and is reported."""
    t = doc.flat
    modern = bool(re.search(r"ACTION OF BOARD|CALENDAR NO\.", t))
    bulletin = bool(re.search(r"ACTION OF THE BOARD|PREMISES AFFECTED", t))
    if modern and not bulletin:
        return "modern"
    if bulletin and not modern:
        return "bulletin"
    if modern and bulletin:
        return "both"
    return "unknown"

# what the BOARD said it did, read from "ACTION OF BOARD — ..." on page 1.
# The index's `status` column is a separate witness and is used to CHECK this,
# never to produce it.
ACTION_OUTCOME = [
    ("granted", r"granted(?: on condition| in part)?|approved"),
    ("denied", r"\bdenied\b|denial"),
    ("withdrawn", r"withdraw"),
    ("dismissed", r"dismiss"),
    ("closed", r"closed|terminated"),
]


def outcome_from_document(d):
    """Granted or not — from the document's own ACTION line.

    ⚠ THE RULE THIS FIXES. `to_facts` used to read the INDEX's status column to
    decide whether to emit `variance_granted`. That is a fact whose load-bearing
    input came from a search result, on a document that states the answer in
    capital letters on its first page:

        ACTION OF BOARD — Application granted on condition.

    Index-first also fails silently on the 13 rows whose status is 'Decision' or
    blank, and on any decode run without an index row attached at all.
    """
    action = (d.get("action") or "")
    for name, pat in ACTION_OUTCOME:
        if re.search(pat, action, re.I):
            return name, "document:ACTION OF BOARD"
    # the Decision section restates it when the header line did not extract
    for name, pat in ACTION_OUTCOME:
        if re.search(rf"Therefore,?\s*it is\s*Resolved.{{0,400}}?{pat}",
                     (d.get("_resolved_head") or ""), re.I | re.S):
            return name, "document:Resolved clause"
    return None, "not stated in document"


def header(doc):
    """Calendar, dates, premises, and — the point of the exercise — the parcel
    AS THE BOARD STATES IT, which is not always what the index says."""
    out = {}
    m = doc.find(r"MEETING OF:?\s*([A-Z][a-z]+ \d{1,2},? \d{4})")
    if m:
        out["adopted"] = _tidy(m.group(1))
        out["adopted_page"] = doc.page_of(m.start())
    m = doc.find(r"CALENDAR NO\.?:?\s*([0-9A-Za-z\-/ ]+)")
    if m:
        out["calendar_stated"] = _tidy(m.group(1), 40)
    out["format"] = document_format(doc)
    # FORMAT B puts the adoption date in a certification line, not a header
    if "adopted" not in out:
        m = re.search(r"resolution adopted by the Board of Standards and Appeals,?"
                      r"\s*([A-Z][a-z]+ \d{1,2},? \d{4})", doc.flat, re.I)
        if not m:
            m = re.search(r"Adopted by the Board of Standards and Appeals,?\s*"
                          r"([A-Z][a-z]+ \d{1,2},? \d{4})", doc.flat, re.I)
        if m:
            out["adopted"] = _tidy(m.group(1))
            out["adopted_page"] = doc.page_of_flat(m.start())
    # FORMAT B: "APPLICANT – <agent>, for <owner>, owner; <lessee>, lessee."
    # Richer than format A, which names the applicant only in prose.
    m = re.search(rf"APPLICANT\s*{DASH}\s*(.{{4,220}}?)\.\s", doc.flat)
    if m:
        out["applicant_line"] = _tidy(m.group(1), 220)
        out["applicant_page"] = doc.page_of_flat(m.start())
        o = re.search(r"for\s+(.{3,90}?),\s*(?:owner|lessee)", m.group(1), re.I)
        if o:
            out["owner_stated"] = _tidy(o.group(1), 90)
    m = re.search(rf"SUBJECT\s*{DASH}\s*Application\s+"
                  r"([A-Z][a-z]+ \d{1,2},? \d{4})", doc.flat)
    if m:
        out["application_filed"] = _tidy(m.group(1))
    # ⚠ ONE DOCUMENT, MANY CASES. "104-08-BZY thru 119-08-BZY" heads a single
    # resolution deciding sixteen applications, and its PREMISES line lists all
    # sixteen lots. Without this flag every one of those lots is attributed to
    # every calendar number in the series.
    m = SERIES.search(doc.flat)
    if m:
        out["series"] = [m.group(1), m.group(2)]
        out["series_page"] = doc.page_of_flat(m.start())
    m = doc.find(r"PREMISES(?:\s+AFFECTED)?\s*[:\-–—]?\s*(.{0,200}?)\s*(?:\n|Block\b)")
    if m:
        out["premises"] = _tidy(m.group(1), 200)
        out["premises_page"] = doc.page_of(m.start())
        # ⚠ THE BOROUGH IS IN THE DOCUMENT. The first version took it from the
        # index's borough_code to build a BBL — so every BBL this decoder
        # produced was half index-sourced, on a field the resolution states
        # plainly on page 1: "PREMISES: 220-28 Jamaica Avenue, Queens".
        # RULE_DOCUMENTS_NOT_INDEXES: the index is for finding and checking.
        for name, num in BOROUGH_NUM.items():
            if re.search(rf"\b{name}\b", out["premises"], re.I):
                out["borough_stated"] = num
                out["borough_name_stated"] = name.title()
                break
    if "borough_stated" not in out:
        # FORMAT B states it AFTER the block and lots — "Block 1332, Lot 16,
        # Borough of Manhattan." — so the premises capture stops short of it.
        m = re.search(r"Borough of\s+([A-Z][a-z]+(?: [A-Z][a-z]+)?)", doc.flat)
        if m and m.group(1).strip().lower() in BOROUGH_NUM:
            out["borough_stated"] = BOROUGH_NUM[m.group(1).strip().lower()]
            out["borough_name_stated"] = m.group(1).strip()
            out["borough_page"] = doc.page_of_flat(m.start())
    # "Block 10789, Lot 271"  /  "Block 800, Lots 49, 53, 55 and 56"
    m = re.search(r"Block\s*([0-9]{1,5})\s*,?\s*Lots?\s*([0-9][0-9,;&\s and]{0,80})",
                  doc.text, re.I)
    if m:
        out["block_stated"] = int(m.group(1))
        out["lots_stated"] = [int(x) for x in re.findall(r"\d+", m.group(2))]
        out["parcel_page"] = doc.page_of(m.start())
    # ★ THE DISTRICT, FROM THE DOCUMENT. Every resolution names it in prose —
    # "within an R3-2 (C1-2) zoning district", "located in an R4 zoning
    # district". The index carries it too, but the index is a finding aid and
    # the baseline computed from this is a FACT ABOUT THE PARCEL, so its input
    # has to be read rather than looked up.
    m = re.search(r"(?:within|in)\s+an?\s+([A-Z]\d{1,2}[-\w]*(?:\s*\([^)]{1,12}\))?"
                  r"(?:\s*/\s*[A-Z]\d{1,2}[-\w]*)?)\s+zoning district", doc.flat)
    if not m:
        m = re.search(r"([A-Z]\d{1,2}[-\w]*)\s+zoning district", doc.flat)
    if m:
        out["district_stated"] = _tidy(m.group(1), 40)
        out["district_page"] = doc.page_of_flat(m.start())
    # FORMAT B writes "ACTION OF THE BOARD" with an en-dash and sometimes two
    # spaces. One missing word cost the outcome on three quarters of the corpus.
    m = doc.find(r"ACTION OF (?:THE )?BOARD\s*[^\n]{0,140}")
    if m:
        out["action"] = _tidy(m.group(0), 180)
    elif re.search(r"THE VOTE TO (GRANT|DENY)", doc.flat, re.I):
        # B sometimes states the disposition only in the vote heading
        v = re.search(r"THE VOTE TO (GRANT|DENY)", doc.flat, re.I)
        out["action"] = f"THE VOTE TO {v.group(1).upper()}"
        out["action_source"] = "vote heading"
    # certification: when the resolution became public. the SECOND date axis.
    m = re.search(r"is hereby filed by the\s*Board of Standards and Appeals\s*"
                  r"on\s*([A-Z][a-z]+ \d{1,2},? \d{4})", doc.text, re.I)
    if not m:
        m = re.search(r"filed by the[\s\S]{0,80}?on\s*([A-Z][a-z]+ \d{1,2},? \d{4})",
                      doc.text, re.I)
    if m:
        out["filed_cert"] = _tidy(m.group(1))
        out["filed_cert_page"] = doc.page_of(m.start())
    # the DOB job the variance attaches to — the join into DOB_BIS/NOW.
    # ⚠ carries the -I1 suffix that the CO join must have stripped.
    m = re.search(r"Application No\.?\s*([A-Z]?\d{6,9}(?:-[A-Z0-9]{1,3})?)", doc.text)
    if m:
        out["dob_job"] = m.group(1).strip()
        out["dob_job_page"] = doc.page_of(m.start())
    return out


# ⚠ A ZR SECTION AND A HOUSE NUMBER LOOK THE SAME. "220-28 Jamaica Avenue" and
# "23-52(b)" are both digits-hyphen-digits. Zoning chapters are one or two
# digits, street numbers in Queens are three or more, so the leading-digit guard
# is what separates a citation from an address — without it every Queens
# premises line contributes a fictitious ZR section.
ZR_TOKEN = re.compile(r"(?<![\d\-/.])([0-9]{1,2}\s*-\s*[0-9]{2,4}(?:\([a-z0-9]\))?)")


def zr_near(text, window=90):
    """Sections cited in a §-anchored run. '§§ 35-22(a) and 23-21' cites TWO
    sections and only the first carries the §, so anchoring on § alone loses
    half of every list."""
    out = []
    for m in re.finditer(r"§", text):
        seg = text[m.start():m.start() + window]
        seg = seg.split(";")[0]
        for t in ZR_TOKEN.findall(seg):
            out.append(re.sub(r"\s+", "", t))
    return sorted(set(out))


def zr_sections(doc):
    """Every ZR section the resolution touches, deduped, with the page it was
    first cited on. The section IS the relief — 72-21 is a variance, 73-xx is a
    special permit, and they are not interchangeable."""
    seen = {}
    for m in re.finditer(r"§", doc.flat):
        seg = doc.flat[m.start():m.start() + 90].split(";")[0]
        for t in ZR_TOKEN.findall(seg):
            seen.setdefault(re.sub(r"\s+", "", t), doc.page_of_flat(m.start()))
    return seen


# ⚠ THE SECOND HALF OF THE SAME BUG. Permitted and granted are worded almost
# IDENTICALLY — "a maximum building height of 55 feet" (district, p4) and "a
# maximum building height of 122 feet" (granted, p11). Only POSITION separates
# them. Matching either pattern over the whole document returns whichever comes
# first, which is always the district figure, so every granted height silently
# collapsed to the as-of-right height and the relief computed to zero. A
# variance that grants nothing is not an implausible-looking answer, which is
# exactly why it survives review.
#
# So each layer is matched only inside ITS OWN REGION of the resolution.
# ── the generic reader ────────────────────────────────────────────────────────
# ⚠ WHY THE PATTERN-PER-PHRASING APPROACH WAS ABANDONED. Every new resolution
# taught a new wording — "shall be limited to", "shall be as follows", "§ 24-11
# permits a maximum of", "a maximum total floor area of approximately" — and
# each one was added as another regex. That decoder read 42% of its own corpus
# and had no way to say which 58% it had missed or why. The failure was
# invisible because a missing parameter and an absent parameter look identical.
#
# The Board's sentences all have ONE shape:  <maximum|minimum> <thing> of <N>
# <unit>. So the shape is matched once, and the THING is looked up in a lexicon.
# A phrase the lexicon does not know is recorded as `unmapped` — counted, named,
# and visible — instead of silently dropped. The lexicon is the thing that grows
# now, and its gaps are measurable.
PARAM_PHRASE = re.compile(
    r"\b(maximum|minimum)\s+"
    r"((?:[A-Za-z()/'’\-]+[ ]{0,2}){1,5}?)"
    r"of\s*(?:approximately\s*)?"
    r"([\d,]+(?:\.\d+)?)\s*"
    r"(square\s*feet|sq\.?\s*ft\.?|feet|percent|%|units|dwelling units|"
    r"spaces|FAR|['′]\s*[-–]?\s*\d{1,2}\s*[\"″]|['′″\"])",
    re.I)

# A third shape, learned from the cases the first two missed: the bound trails
# the parameter entirely — "the total lot coverage of the Premises shall not
# exceed a maximum of 25,209.80 square feet", "a north rear yard measuring a
# minimum of 26.08 feet". Same sentence, same force, different word order.
TRAILING = re.compile(
    r"\b((?:[A-Za-z()/'’\-]+[ ]{0,2}){1,5}?)"
    r"(?:measuring|shall not exceed|not to exceed|shall be no (?:more|less) than)"
    r"\s*(?:a\s+)?(maximum|minimum)?\s*(?:of\s*)?"
    r"([\d,]+(?:\.\d+)?)\s*"
    r"(square\s*feet|sq\.?\s*ft\.?|feet|percent|%|units|spaces|FAR|"
    r"['′]\s*[-–]?\s*\d{1,2}\s*[\"″]|['′″\"])",
    re.I)

# "a rear yard with a minimum depth of 40 feet" — the parameter comes BEFORE
# the maximum/minimum, so the generic shape cannot see it.
YARD_PHRASE = re.compile(
    r"\b(front|side|rear)\s+yards?\s+with\s+(?:a\s+)?(minimum|maximum)\s+"
    r"(depth|width)s?\s+of\s*([\d,]+(?:\.\d+)?)\s*"
    r"(feet|['′]\s*[-–]?\s*\d{1,2}\s*[\"″]|['′])", re.I)

# "232,985.77 square feet (4.55 FAR)" — the ratio rides along with the area
FAR_PAREN = re.compile(r"([\d,]+(?:\.\d+)?)\s*square\s*feet\s*\(\s*([\d.]+)\s*FAR\s*\)", re.I)

LEXICON = {
    "floor area": "floor_area",
    "total floor area": "floor_area",
    "combined (all uses) floor area": "floor_area",
    "combined floor area": "floor_area",
    "zoning floor area": "floor_area",
    "residential floor area": "residential_floor_area",
    "community facility floor area": "community_facility_floor_area",
    "commercial floor area": "commercial_floor_area",
    "floor area ratio": "far",
    "far": "far",
    "lot coverage": "lot_coverage",
    "building height": "building_height",
    "height": "building_height",
    "base height": "base_height",
    "wall height": "wall_height",
    "perimeter wall height": "wall_height",
    "street wall height": "street_wall_height",
    "density": "dwelling_units",
    "dwelling unit total": "dwelling_units",
    "dwelling units": "dwelling_units",
    "number of dwelling units": "dwelling_units",
    "units": "dwelling_units",
    "parking spaces": "parking_spaces",
    "accessory parking spaces": "parking_spaces",
    "open space ratio": "open_space_ratio",
    "osr": "open_space_ratio",
    "far": "far",
    "lot area": "lot_area",
    "rear yard": "rear_yard_depth",
    "side yard": "side_yard_depth",
    "front yard": "front_yard_depth",
    # ⚠ REMOVED: bare "depth" and "width" used to map to themselves, so
    # "a rear yard with a minimum depth of 30 feet" produced BOTH
    # rear_yard_depth=30 and a meaningless depth=30. A duplicate parameter is
    # not harmless — it inflates every "parameters captured" count with a copy
    # of a parameter already held.
    "stories": "stories",
    "number of stories": "stories",
    "recreation space": "recreation_space",
    "open space": "open_space",
    "sign area": "sign_area",
    "sign surface area": "sign_area",
    # added after the pilot named them. every entry here was an `unmapped`
    # phrase first — the lexicon grows from measurement, not from imagination.
    "lot size": "lot_area",
    "front yard depth": "front_yard_depth",
    "side yard width": "side_yard_width",
    "widths": "side_yard_width",
    "minimum widths": "side_yard_width",
    "total side yard": "combined_side_yard_width",
    "individual side yard width": "side_yard_width",
    "combined side yard width": "combined_side_yard_width",
    "combined total width": "combined_side_yard_width",
    "rear yard depth": "rear_yard_depth",
    "total height": "building_height",
    "dwelling unit total": "dwelling_units",
    "permitted floor area": "floor_area",
    "residential floor area ratio": "residential_far",
    "bulkhead height": "bulkhead_height",
    "stair bulkhead height": "bulkhead_height",
}

UNIT = {"square feet": "sf", "sq ft": "sf", "sq. ft.": "sf", "sqft": "sf",
        "feet": "ft", "'": "ft", "′": "ft", "″": "in", '"': "in",
        "percent": "pct", "%": "pct", "units": "units",
        "dwelling units": "units", "spaces": "spaces", "far": "ratio"}


# "a maximum of 216,943.98 square feet (4.24 FAR) shall be dedicated to
# residential use" — the parameter is named AFTER the number, so the generic
# shape reads the phrase as empty and drops the split of floor area by use,
# which is the whole point of a mixed-use variance.
DEDICATED = re.compile(
    r"(maximum|minimum)\s+of\s*([\d,]+(?:\.\d+)?)\s*(square\s*feet|feet|units)"
    r"\s*(?:\(\s*[\d.]+\s*FAR\s*\)\s*)?(?:shall be |)?dedicated to\s+"
    r"([A-Za-z ]{3,40}?)\s+use", re.I)

USE_KIND = {"residential": "residential_floor_area",
            "community facility": "community_facility_floor_area",
            "commercial": "commercial_floor_area",
            "manufacturing": "manufacturing_floor_area",
            "office": "commercial_floor_area", "retail": "commercial_floor_area"}


def _canon_phrase(s):
    s = re.sub(r"\s*-\s*", "-", s)          # "dwelling -unit" is one word split
    s = re.sub(r"\s+", " ", s).strip().lower().strip(" ,;:-")
    for _ in range(4):                  # "the total north rear yard"
        s2 = re.sub(r"^(a|an|the|of|its|permitted|proposed|total|entire|"
                    r"north|south|east|west|one|two|three|each|individual)\s+",
                    "", s)
        if s2 == s:
            break
        s = s2
    s = re.sub(r"\s+(shall|will|is|are|would|may)$", "", s)
    return s.replace("-", " ") if s.replace("-", " ") in LEXICON else s


# ⚠ A PATTERN-INDEPENDENT DENOMINATOR. Everything above counts what the
# decoder UNDERSTOOD. Nothing counted what the document SAID, so "granted
# envelope found on 89%" meant only "at least one parameter came out" — and on
# 2021-44-BZ that one parameter was 1 of 4 stated, while the ledger recorded the
# document as a clean success with every self-check passing.
#
# This regex belongs to no extractor. It simply counts places where the Board
# stated a bound on a number. captured/stated is then a real completeness
# figure, and it is allowed to be embarrassing.
BOUND_STATEMENT = re.compile(
    r"\b(maximum|minimum|required|permitted|shall not exceed|not to exceed)\b"
    r"[^.;]{0,60}?[\d]", re.I)

# "a maximum of 0.50 FAR is permitted", "a minimum of 150% OSR is required" —
# bound, number, unit, THEN the parameter. A fourth word order, found only by
# reading a document the decoder claimed to have handled.
INVERTED = re.compile(
    r"\b(maximum|minimum)\s+of\s*([\d,]+(?:\.\d+)?)\s*"
    r"(square\s*feet|feet|percent|%|units|spaces|FAR|OSR)?\s*"
    r"([A-Za-z()/'’\- ]{0,28}?)\s*(?:is|are)\s+(?:permitted|required|allowed)", re.I)


def count_stated(doc, lo, hi):
    return len(BOUND_STATEMENT.findall(doc.flat[lo:hi]))


def read_params(doc, lo, hi, scope):
    """Every <maximum|minimum> <thing> of <N> <unit> in a span, canonicalised.

    Returns (mapped, unmapped). The second value is not diagnostics — it is the
    honest half of the answer. A decoder that returns only what it understood
    cannot be audited.
    """
    window = doc.flat[lo:hi]
    mapped, unmapped = {}, []
    for m in PARAM_PHRASE.finditer(window):
        bound, phrase, num, unit = m.groups()
        key = _canon_phrase(phrase)
        unit_key = re.sub(r"\s+", " ", unit.lower()).replace("sq.", "sq").strip(".")
        u = UNIT.get(unit_key, unit_key)
        name = LEXICON.get(key)
        val = _num(num)
        if u in ("ft", "in") or re.search(r"['′]", unit):
            val, _ = _feet(m.group(0), val)
            u = "ft"
        rec = {"value": val, "unit": u, "bound": bound.lower(),
               "page": doc.page_of_flat(lo + m.start()), "scope": scope,
               "verbatim": _tidy(m.group(0), 220)}
        if not name:
            unmapped.append({"phrase": key, **rec})
            continue
        if name == "lot_coverage":
            name = "lot_coverage_pct" if u == "pct" else "lot_coverage_sf"
        mapped.setdefault(name, rec)          # first statement in the span wins
    for m in TRAILING.finditer(window):
        phrase, bound, num, unit = m.groups()
        key = _canon_phrase(phrase)
        unit_key = re.sub(r"\s+", " ", unit.lower()).replace("sq.", "sq").strip(".")
        name = LEXICON.get(key)
        uu = UNIT.get(unit_key, unit_key)
        val = _num(num)
        if uu in ("ft", "in") or re.search(r"['′]", unit):
            val, _ = _feet(m.group(0), val)
            uu = "ft"
        rec = {"value": val, "unit": uu,
               "bound": (bound or "maximum").lower(),
               "page": doc.page_of_flat(lo + m.start()), "scope": scope,
               "verbatim": _tidy(m.group(0), 220)}
        if not name:
            unmapped.append({"phrase": key, **rec})
            continue
        if name == "lot_coverage":
            name = "lot_coverage_pct" if rec["unit"] == "pct" else "lot_coverage_sf"
        mapped.setdefault(name, rec)
    for m in YARD_PHRASE.finditer(window):
        side, bound, dim, num, unit = m.groups()
        name = f"{side.lower()}_yard_{dim.lower().rstrip('s')}"
        v, _ = _feet(m.group(0), _num(num))
        mapped.setdefault(name, {
            "value": v, "unit": "ft", "bound": bound.lower(),
            "page": doc.page_of_flat(lo + m.start()), "scope": scope,
            "verbatim": _tidy(m.group(0), 220)})
    for m in INVERTED.finditer(window):
        bound, num, unit, phrase = m.groups()
        key = _canon_phrase(phrase or "") or (unit or "").lower()
        name = LEXICON.get(key) or LEXICON.get((unit or "").lower())
        u = UNIT.get(re.sub(r"\s+", " ", (unit or "").lower()), (unit or "").lower())
        rec = {"value": _num(num), "unit": u or "ratio", "bound": bound.lower(),
               "page": doc.page_of_flat(lo + m.start()), "scope": scope,
               "verbatim": _tidy(m.group(0), 220)}
        if name == "lot_coverage":
            name = "lot_coverage_pct" if rec["unit"] == "pct" else "lot_coverage_sf"
        if name:
            mapped.setdefault(name, rec)
        else:
            unmapped.append({"phrase": key or "(unnamed)", **rec})
    for m in DEDICATED.finditer(window):
        bound, num, unit, use = m.groups()
        key = USE_KIND.get(_canon_phrase(use))
        rec = {"value": _num(num),
               "unit": UNIT.get(re.sub(r"\s+", " ", unit.lower()), "sf"),
               "bound": bound.lower(),
               "page": doc.page_of_flat(lo + m.start()), "scope": scope,
               "verbatim": _tidy(m.group(0), 220)}
        if key:
            mapped.setdefault(key, rec)
        else:
            unmapped.append({"phrase": f"dedicated to {_canon_phrase(use)} use", **rec})
    m = FAR_PAREN.search(window)
    if m and "far" not in mapped:
        mapped["far"] = {"value": _num(m.group(2)), "unit": "ratio",
                         "bound": "maximum",
                         "page": doc.page_of_flat(lo + m.start()), "scope": scope,
                         "verbatim": _tidy(m.group(0), 220)}
    return mapped, unmapped


PERMITTED_PAT = [
    ("floor_area", "sf", r"(?:permits?|permitted)[^.;]{0,120}?maximum\s+(?:combined\s*\(all uses\)\s*)?(?:total\s+|residential\s+)?floor area of\s*(?:approximately\s*)?([\d,]+(?:\.\d+)?)\s*square\s*feet"),
    ("far", "ratio", r"(?:permits?|permitted)[^.;]{0,140}?floor area of\s*[\d,.]+\s*square\s*feet\s*\(\s*([\d.]+)\s*FAR\)"),
    ("dwelling_units", "units", r"maximum\s+dwelling\s*-?\s*unit\s+total\s+of\s*([\d,]+)\s*units"),
    ("base_height", "ft", r"maximum\s+base\s+height\s+of\s*([\d,]+(?:\.\d+)?)\s*feet"),
    ("building_height", "ft", r"maximum\s+building\s+height\s+of\s*([\d,]+(?:\.\d+)?)\s*feet"),
    ("lot_coverage_sf", "sf", r"maximum\s+lot coverage of\s*([\d,]+(?:\.\d+)?)\s*square\s*feet"),
]

# ⚠ THE PHRASING IS NOT ONE PHRASING. Measured over the pilot: the operative
# clause is "the bulk parameters of the building shall be LIMITED TO" in some
# resolutions and "shall be AS FOLLOWS" in more of them, and older ones use
# neither. Tuning on a single document produced a decoder that read 26% of its
# own corpus and reported that as the corpus.
GRANTED_PAT = [
    ("floor_area", "sf", r"maximum\s+(?:total\s+)?floor area of\s*(?:approximately\s*)?([\d,]+(?:\.\d+)?)\s*square\s*feet"),
    ("far", "ratio", r"maximum\s+(?:total\s+)?floor area of\s*(?:approximately\s*)?[\d,.]+\s*square\s*feet\s*\(\s*([\d.]+)\s*FAR\)"),
    ("residential_floor_area", "sf", r"maximum of\s*([\d,]+(?:\.\d+)?)\s*square\s*feet\s*(?:\([\d.]+\s*FAR\)\s*)?shall be dedicated to residential"),
    ("community_facility_floor_area", "sf", r"maximum of\s*([\d,]+(?:\.\d+)?)\s*square\s*feet\s*(?:\([\d.]+\s*FAR\)\s*)?shall be dedicated to community facility"),
    ("dwelling_units", "units", r"maximum (?:density|number) of\s*([\d,]+)\s*dwelling units"),
    ("building_height", "ft", r"maximum building height of\s*([\d,]+(?:\.\d+)?)\s*(?:feet|')"),
    ("lot_coverage_sf", "sf", r"maximum lot coverage of\s*([\d,]+(?:\.\d+)?)\s*square\s*feet"),
    ("lot_coverage_pct", "pct", r"maximum lot coverage of\s*([\d.]+)\s*(?:%|percent)"),
    ("parking_spaces", "spaces", r"minimum of\s*([\d,]+)\s*(?:accessory\s*)?parking spaces"),
    ("rear_yard_depth", "ft", r"rear yard with (?:a )?minimum depth of\s*([\d,]+(?:\.\d+)?)\s*(?:feet|')"),
    ("side_yard_depth", "ft", r"side yards? with (?:a )?minimum depth of\s*([\d,]+(?:\.\d+)?)\s*(?:feet|')"),
    ("front_yard_depth", "ft", r"front yard with (?:a )?minimum depth of\s*([\d,]+(?:\.\d+)?)\s*(?:feet|')"),
]

PROPOSED_PAT = [
    ("floor_area", "sf", r"proposes?[^.]{0,300}?(?:with|containing)\s*(?:approximately\s*)?([\d,]+(?:\.\d+)?)\s*square\s*feet of floor area"),
    ("far", "ratio", r"proposes?[^.]{0,300}?square\s*feet of floor area\s*\(\s*([\d.]+)\s*FAR"),
    ("dwelling_units", "units", r"proposes?[^.]{0,300}?with\s*([\d,]+)\s*(?:affordable\s*)?dwelling units"),
]

LOT_AREA_PAT = r"([\d,]+(?:\.\d+)?)\s*square\s*feet of lot area"

# a resolution that regulates PARTS of a site separately cannot be reduced to
# one number per parameter, and quietly taking the first one attributes a
# portion's cap to the whole parcel
MULTIPART = re.compile(r"portion of the (?:Premises|lot|site)|Corner Lot \d|"
                       r"Building [A-Z]\b|Zoning Lot \d|R\d[A-Z]?/[A-Z]{2} portion", re.I)


# ⚠ THE ROMAN NUMERAL MOVES. Measured across 29 cached resolutions: "Proposal"
# is section III in 19 of them and section IV in 3, because a "Board History"
# section gets inserted when the case has been before the Board before. Anchor
# on the NUMBER and you silently read the Findings as the Proposal on every
# re-opened case — which is exactly the population of cases with a long history
# and the most to say. Anchor on the NAME; it never moves.
#
# And 24% of resolutions do not use this scheme at all ("I. The Premises",
# "III. The Zoning Resolution"). Those are a different document format, not a
# malformed one, and they are reported as such rather than parsed by hope.
SECTION = re.compile(r"\b([IVX]{1,5})\.\s{0,3}(The Request|Request|Location|"
                     r"The Premises|Proposal|Board History|Findings|Decision|"
                     r"Environmental Review|Board Review|The Zoning Resolution)\b")


def sections(doc):
    """Named spans of the resolution, in document order."""
    hits = [(m.group(2), m.start()) for m in SECTION.finditer(doc.flat)]
    out = {}
    for i, (name, pos) in enumerate(hits):
        end = hits[i + 1][1] if i + 1 < len(hits) else len(doc.flat)
        out.setdefault(name, (pos, end))
    return out


def regions(doc):
    """Split the resolution into the zones where the same words mean different
    things. Returns (start, end) offsets into doc.flat and records the anchor
    used, so a fact can say how confidently it was located."""
    out = {}
    sec = sections(doc)
    out["sections_found"] = sorted(sec)
    m = re.search(r"Therefore,?\s*it is\s*Resolved", doc.flat, re.I)
    if m:
        stop = re.search(r"Adopted by the Board", doc.flat[m.start():], re.I)
        out["granted"] = (m.start(), m.start() + (stop.start() if stop else len(doc.flat)))
        out["granted_anchor"] = "Therefore it is Resolved"
    # the operative CLAUSE inside the Resolved region. Narrower than the region
    # and much safer: everything in it is a cap the Board imposed.
    if "granted" in out:
        lo, hi = out["granted"]
        m = re.search(r"bulk parameters[^:]{0,120}:", doc.flat[lo:hi], re.I)
        if m:
            start = lo + m.end()
            nxt = re.search(r"\bTHAT\b", doc.flat[start:hi])
            out["bulk_clause"] = (start, start + (nxt.start() if nxt else min(1800, hi - start)))
    # the district recital. Two phrasings measured: the narrative form
    # ("the Zoning Resolution permits the subject site to have a maximum ...")
    # and the section-led form ("§ 23-21 permits a maximum residential floor
    # area of 2,004.75 square feet"). Only the first was implemented, so 90% of
    # baselines went missing and every relief figure was uncomputable.
    # what was ASKED for — the Proposal section, located by NAME.
    prop = sec.get("Proposal")
    if not prop:
        m = re.search(r"The applicant\s+proposes", doc.flat, re.I)
        if m:
            stop = re.search(r"\b[IVX]{1,5}\.\s", doc.flat[m.start():])
            prop = (m.start(), m.start() + (stop.start() if stop else 2500))
    if prop:
        out["proposed"] = prop
        out["proposed_anchor"] = "Proposal" if sec.get("Proposal") else "applicant proposes"
    # the district recital. It sits at the END of the Proposal section or in a
    # section of its own, and is worded two ways: narrative ("the Zoning
    # Resolution permits the subject site to have a maximum ...") and
    # section-led ("§ 23-21 permits a maximum residential floor area of ...").
    # Only the narrative form was implemented, so 90% of baselines went missing
    # and every relief figure became uncomputable.
    lo = prop[0] if prop else 0
    hi = out.get("granted", (len(doc.flat),))[0]
    scan = doc.flat[lo:hi]
    m = re.search(r"(?:the\s+)?Zoning Resolution (?:permits|would permit|allows)"
                  r"|§\s*[\d\s-]{4,10}(?:\([a-z0-9]\))?\s*(?:permits|allows)"
                  r"|maximum permitted (?:floor area|FAR|residential)", scan, re.I)
    if m:
        out["permitted"] = (lo + m.start(), hi)
        out["permitted_anchor"] = _tidy(scan[m.start():m.start() + 40], 40)
        if prop:                       # the Proposal must stop where the
            out["proposed"] = (prop[0], lo + m.start())     # recital begins
    return out


def envelope(doc):
    """The numeric layers: what the district allows, what the Board allowed, and
    the lot area the ratios are taken over.

    A parameter found OUTSIDE its region is not reported. Reporting it from the
    wrong region would give the right-looking number the wrong legal meaning,
    and there is no way to tell those apart downstream.
    """
    reg = regions(doc)
    out = {"permitted": {}, "granted": {}, "proposed": {}, "lot_area": None,
           "regions": {k: v for k, v in reg.items()
                       if k.endswith("anchor") or k == "sections_found"}}
    # granted is read from the narrow bulk clause when there is one, and only
    # then from the wider Resolved region — with the scope recorded, because a
    # cap found in the clause and a number found loose in the region are not
    # equally load-bearing and must not arrive looking identical.
    spans = {"permitted": (reg.get("permitted"), "recital"),
             "proposed": (reg.get("proposed"), "proposal"),
             "granted": ((reg.get("bulk_clause") or reg.get("granted")),
                         "bulk_clause" if reg.get("bulk_clause") else "resolved_region")}
    out["unmapped"] = []
    for layer in ("permitted", "granted", "proposed"):
        span, scope = spans[layer]
        if not span:
            out[f"{layer}_missing_region"] = True
            continue
        lo, hi = span
        if layer == "granted":
            out["multipart"] = bool(MULTIPART.search(doc.flat[lo:hi]))
        mapped, unmapped = read_params(doc, lo, hi, scope)
        stated = count_stated(doc, lo, hi)
        out.setdefault("completeness", {})[layer] = {
            "stated": stated, "captured": len(mapped),
            "unmapped": len(unmapped),
            "ratio": round(len(mapped) / stated, 3) if stated else None}
        for rec in unmapped:
            out["unmapped"].append({"layer": layer, **rec})
        if layer == "granted" and out.get("multipart"):
            for rec in mapped.values():
                # the number is real but it describes a PART. Emitting it as the
                # site's cap would be a lie with a correct citation attached.
                rec["applies_to"] = "one portion of a split site — NOT site-wide"
        out[layer] = mapped
    m = re.search(LOT_AREA_PAT, doc.flat, re.I)
    if m:
        out["lot_area"] = {"value": _num(m.group(1)), "unit": "sf",
                           "page": doc.page_of_flat(m.start()),
                           "verbatim": _tidy(m.group(0), 160)}
    return out


WAIVE_HEAD = (r"required to waive the\s*following[^:]{0,60}:|"
              r"contrary to\s|"
              r"waiv(?:e|er of|ing)\s+the\s+following")


def waived(doc):
    """WHAT WAS WAIVED — the authoritative list, quoted from the DOB objection
    on page 1, not paraphrased from the project description.

    The index's `project_description` says "contrary to underlying bulk
    requirements" for hundreds of cases. That sentence names nothing. The DOB
    objection names the exact ZR sections that stopped the job, and those are
    the sections the variance permanently displaces on this parcel.
    """
    out = []
    m = re.search(r"required to waive the\s*following[^:]{0,80}:(.{0,1400}?)"
                  r"(?:I\.\s*The Request|II\.\s*Location)", doc.flat, re.I | re.S)
    block = m.group(1) if m else None
    if block:
        # the objections are numbered "1. ... 2. ... and 3. ..." — splitting on
        # the punctuation before the number misses "; and 3.", so split on the
        # numbered head itself
        cursor = 0
        for item_raw in re.split(r"(?=(?<![\d.])[1-9][0-9]?\.\s+[A-Z])", block):
            pos = m.start(1) + cursor
            cursor += len(item_raw)
            item = _tidy(item_raw, 400)
            if len(item) < 12:
                continue
            out.append({"objection": item, "zr": zr_near(item_raw),
                        "page": doc.page_of_flat(pos)})
    # the one-sentence form, present in every resolution whether or not the DOB
    # objection was quoted
    m2 = re.search(r"contrary to\s+(.{0,600}?)\s+requirements", doc.flat, re.I | re.S)
    if m2:
        out.append({"objection": "contrary to " + _tidy(m2.group(1), 400) + " requirements",
                    "zr": zr_near(m2.group(1)), "page": doc.page_of_flat(m2.start()),
                    "form": "request_sentence"})
    return out


COND_SPLIT = re.compile(r"(?=\bTHAT\b)")


def conditions(doc):
    """Every THAT-clause after the Resolved. These are the permanent burden.

    ⚠ The conditions run PAST the first page break, and the last one is followed
    by 'Adopted by the Board'. Stopping at the page break loses conditions; not
    stopping at 'Adopted' swallows the certification.
    """
    m = re.search(r"Therefore,\s*it is\s*Resolved", doc.text, re.I)
    if not m:
        return []
    tail = doc.text[m.start():]
    stop = re.search(r"Adopted by the Board", tail, re.I)
    if stop:
        tail = tail[:stop.start()]
    base, cursor = m.start(), 0
    out = []
    for piece in COND_SPLIT.split(tail):
        pos = base + cursor          # running offset — `find` would return the
        cursor += len(piece)         # FIRST match and boilerplate repeats
        p = piece.strip()
        if not p.startswith("THAT"):
            continue
        out.append({"page": doc.page_of(pos), "text": _tidy(p, 900)})
    return out


BULK_WORDS = re.compile(r"floor area|FAR|height|setback|yard|lot coverage|"
                        r"density|dwelling unit|parking|open space|bulk|"
                        r"sky exposure|wall", re.I)
USE_WORDS = re.compile(r"use regulation|use group|\bUG\s*[IVX0-9]|permitted use|"
                       r"contrary to.{0,40}\buse\b", re.I)


def classify(d):
    """USE variance or BULK variance — the distinction that fixes the
    denominator.

    ⚠ 'granted envelope found on 52%' is a meaningless number until you know
    that a chunk of §72-21 grants relief from USE regulations and states no
    dimension at all. Those resolutions are not decode failures; they have
    nothing dimensional to find. Measuring extraction against ALL variances
    understates the decoder and hides the real misses among the legitimate
    blanks.
    """
    text = " ".join(w["objection"] for w in (d.get("waived") or []))
    text += " " + ((d.get("index") or {}).get("project_description") or "")
    bulk, use = bool(BULK_WORDS.search(text)), bool(USE_WORDS.search(text))
    kind = ("both" if bulk and use else "bulk" if bulk else "use" if use
            else "unclassified")
    return {"relief_kind": kind, "dimensional_expected": kind in ("bulk", "both")}


# ── what a resolution says that the first six parser versions walked past ────
#
# Measured 2026-08-06 over 577 cached resolutions, by looking for what is THERE
# rather than checking what I had already decided to take:
#
#     98.8%  the VOTE tally            — taken: none
#     93.9%  the public hearing date   — taken: none
#     91.9%  the applicant / agent     — taken: partially (owner on 50.6%)
#     64.1%  approved plans sheet count— taken: none
#     60.5%  Community Board recommendation — taken: none
#     46.4%  a TERM or EXPIRY deadline — taken: none
#     18.5%  the CEQR number           — taken: none
#
# The last two matter most and for opposite reasons. A grant with a deadline
# ("shall be obtained within four years, by April 25, 2026") may have LAPSED,
# and an entitlement that has lapsed is not an entitlement — reporting it as one
# is the worst error this table can make. The Community Board's position is the
# only measure of local opposition that exists anywhere in the record.

VOTE = re.compile(r"Affirmative:?\s*(.{0,300}?)\s*\.{0,60}\s*(\d{1,2})\s*"
                  r"Negative:?\s*\.{0,80}\s*(\d{1,2})", re.I | re.S)
CB_REC = re.compile(r"Community Board\s*#?\s*(\d{1,2})\s*([A-Z]{0,2})[^.]{0,90}?"
                    r"\b(recommends?|voted)\b[^.]{0,80}?"
                    r"\b(approval|approve|denial|deny|disapproval|rejection|"
                    r"no objection|conditional)\b", re.I)
HEARING = re.compile(r"public hearing (?:was\s+)?(?:held\s+)?on this application "
                     r"on\s+([A-Z][a-z]+ \d{1,2},? \d{4})", re.I)
CONTINUED = re.compile(r"continued hearing on\s+([A-Z][a-z]+ \d{1,2},? \d{4})", re.I)
TERM = re.compile(r"within\s+(?:(\w+)|\((\d+)\))\s*\(?\d*\)?\s*years?,?\s*by\s+"
                  r"([A-Z][a-z]+ \d{1,2},? \d{4})", re.I)
EXPIRES = re.compile(r"(?:shall\s+)?expires?\s+(?:on\s+)?([A-Z][a-z]+ \d{1,2},? \d{4})",
                     re.I)
CEQR = re.compile(r"CEQR\s*#?\s*([\dA-Z][\dA-Z-]{5,14})", re.I)
E_DESIG = re.compile(r"\(E\)\s*[Dd]esignation[^.]{0,60}?\(?(E-?\s?\d{2,4})\)?"
                     r"|\b(E-\d{3,4})\b")
AGENT = re.compile(r"This application is (?:made\s+)?on behalf of\s+"
                   r"([A-Z][^.,;]{3,70})", re.I)
SHEETS = re.compile(r"[“\"]Approved Plans[”\"]?\s*[—–-]?\s*([A-Za-z-]+|\d{1,3})\s*"
                    r"\((\d{1,3})\)\s*sheets", re.I)


def extras(doc):
    """Everything above, read once. Absent is recorded as absent, not guessed."""
    out = {}
    m = VOTE.search(doc.flat)
    if m:
        out["vote_affirmative"] = int(m.group(2))
        out["vote_negative"] = int(m.group(3))
        out["vote_unanimous"] = out["vote_negative"] == 0
        out["vote_commissioners"] = _tidy(m.group(1), 220)
        out["vote_page"] = doc.page_of_flat(m.start())
    m = CB_REC.search(doc.flat)
    if m:
        pos = m.group(4).lower()
        out["cb"] = f"{m.group(1)}{m.group(2) or ''}"
        out["cb_recommendation"] = (
            "approval" if pos.startswith(("approv", "no objection", "conditional"))
            else "denial")
        out["cb_page"] = doc.page_of_flat(m.start())
    m = HEARING.search(doc.flat)
    if m:
        out["hearing_first"] = _tidy(m.group(1), 30)
    c = CONTINUED.findall(doc.flat)
    if c:
        out["hearing_continued"] = [_tidy(x, 30) for x in c][:4]
    # ⚠ THE LAPSE DATE — AND THE FALSE POSITIVE IT NEARLY BECAME.
    #
    # Searching the whole document for an expiry date pulled "April 1, 2027" out
    # of 2025-12-BZ. That is not the grant's deadline; it is when the CITY'S
    # HOUSING EMERGENCY DECLARATION expires, quoted in footnote 1 about the ETPA
    # rental vacancy rate. A date in a footnote about state law, filed as the
    # date this entitlement dies.
    #
    # The real deadline is always a CONDITION — "THAT a certificate of occupancy
    # ... shall be obtained within four years, by April 25, 2026" — so the
    # search is scoped to the operative clause. Outside it, a date that looks
    # like an expiry is just a date.
    reg = regions(doc)
    lo, hi = reg.get("granted", (0, 0))
    clause = doc.flat[lo:hi] if hi > lo else ""
    m = TERM.search(clause)
    if m:
        out["term_years"] = m.group(1) or m.group(2)
        out["expires"] = _tidy(m.group(3), 30)
        out["expires_basis"] = "condition: CO must be obtained by this date"
        out["expires_page"] = doc.page_of_flat(lo + m.start())
    else:
        m = EXPIRES.search(clause)
        if m:
            out["expires"] = _tidy(m.group(1), 30)
            out["expires_basis"] = "condition: term stated as expiring"
            out["expires_page"] = doc.page_of_flat(lo + m.start())
    m = CEQR.search(doc.flat)
    if m:
        out["ceqr"] = _tidy(m.group(1), 20)
    m = E_DESIG.search(doc.flat)
    if m:
        out["e_designation"] = re.sub(r"\s+", "", m.group(1) or m.group(2))
    m = AGENT.search(doc.flat)
    if m:
        out["applicant_stated"] = _tidy(m.group(1), 80)
    m = SHEETS.search(doc.flat)
    if m:
        out["approved_plan_sheets"] = int(m.group(2))
    return out


def decode(calendar, pdf_path, index_row=None):
    """One decision -> a structured reading. Never asserts what it did not find."""
    pts = strip_running_header(pages(pdf_path))
    doc = Doc(calendar, pts)
    chars = sum(len(t) for t in pts)
    read = sum(1 for t in pts if len(t.strip()) > 40)
    d = {"calendar": calendar, "pages": len(pts), "chars": chars,
         # the completeness test from RULE_DOCUMENTS_NOT_INDEXES: every claim
         # carries pages_read / pages_total. For this source they are equal by
         # construction — the whole PDF is extracted and every region is matched
         # over the full text — EXCEPT where a page yields no text at all, which
         # is a page present and unread, not a page that says nothing.
         "pages_read": read, "pages_unreadable": len(pts) - read,
         "text_bearing_pages": sum(1 for t in pts if len(t) > 200)}
    if chars < 500:
        d["status"] = "unreadable"
        d["pages_read"] = 0
        d["note"] = ("no extractable text — image-only scan, needs OCR. This is "
                     "NOT an empty decision.")
        return d
    d["status"] = "ok"
    d.update(header(doc))
    d["zr_sections"] = zr_sections(doc)
    d["waived"] = waived(doc)
    d.update(extras(doc))
    d["envelope"] = envelope(doc)
    d["conditions"] = conditions(doc)
    if index_row:
        d["index"] = {k: index_row.get(k) for k in
                      ("application", "section", "status", "block", "lots",
                       "borough_code", "zoning_district", "filed", "date",
                       "street_number", "street_name", "project_description")}
    d.update(classify(d))
    return d


# ---------------------------------------------------------------- checks

def selfcheck(d):
    """Checks the DOCUMENT makes against itself. A resolution states floor area,
    FAR and lot area independently, so FAR*lot_area must reproduce floor area —
    an arithmetic identity the typesetting cannot fake. When it fails, the
    extraction is wrong, not the Board."""
    out = []
    env = d.get("envelope") or {}
    la = (env.get("lot_area") or {}).get("value")
    for layer in ("permitted", "granted"):
        fa = (env[layer].get("floor_area") or {}).get("value") if env.get(layer) else None
        far = (env[layer].get("far") or {}).get("value") if env.get(layer) else None
        if la and fa and far:
            calc = fa / la
            ok = abs(calc - far) <= max(0.02, far * 0.01)
            out.append({"check": f"{layer}: floor_area/lot_area == stated FAR",
                        "stated": far, "computed": round(calc, 4),
                        "verdict": "PASS" if ok else "FAIL"})
    # ⚠ THE CHECK THAT WOULD HAVE CAUGHT THE HEIGHT BUG. If a variance was
    # granted, at least one parameter must differ from the district maximum —
    # that difference IS the variance. When every granted figure equals its
    # permitted twin, the decoder matched the recital twice, not the grant.
    g, p = (env.get("granted") or {}), (env.get("permitted") or {})
    shared = [k for k in g if k in p]
    if shared:
        differs = [k for k in shared if abs(g[k]["value"] - p[k]["value"]) > 1e-6]
        out.append({"check": "granted differs from permitted on >=1 parameter",
                    "stated": f"{len(shared)} comparable",
                    "computed": f"{len(differs)} differ: {differs}",
                    "verdict": "PASS" if differs else "FAIL"})
    comp = (env.get("completeness") or {})
    for layer, c in comp.items():
        if c.get("stated"):
            out.append({"check": f"{layer}: captured == stated bounds",
                        "stated": f"{c['stated']} bound statements in region",
                        "computed": f"{c['captured']} captured, {c['unmapped']} unmapped",
                        "verdict": "PASS" if c["captured"] >= c["stated"] else "FAIL"})
    # ── the index used the way the rule permits: as a free, independent
    # witness to test the decode against, never as the decode's source ──
    ix = d.get("index") or {}
    outcome, src = outcome_from_document(d)
    if ix.get("status"):
        agree = (outcome or "").lower() == (ix["status"] or "").lower()
        out.append({"check": "document outcome == index status",
                    "stated": f"doc {outcome} ({src})",
                    "computed": f"index {ix.get('status')}",
                    "verdict": "PASS" if agree else "FAIL"})
    if d.get("pages") and d.get("pages_read") is not None:
        out.append({"check": "pages_read == pages_total",
                    "stated": f"{d['pages_read']} read",
                    "computed": f"{d['pages']} total",
                    "verdict": "PASS" if d["pages_read"] == d["pages"] else "FAIL"})
    if d.get("borough_stated") and ix.get("borough_code"):
        out.append({"check": "document borough == index borough",
                    "stated": f"doc {d.get('borough_name_stated')}",
                    "computed": f"index {ix.get('borough_code')}",
                    "verdict": "PASS" if int(ix["borough_code"]) == d["borough_stated"] else "FAIL"})
    if d.get("block_stated") and (ix.get("block") or "").isdigit():
        same_blk = int(ix["block"]) == d["block_stated"]
        lots_ix = re.findall(r"\d+", ix.get("lots") or "")
        same_lot = any(int(x) in (d.get("lots_stated") or []) for x in lots_ix)
        out.append({"check": "index block/lot == document block/lot",
                    "stated": f"idx {ix.get('block')}/{ix.get('lots')}",
                    "computed": f"doc {d['block_stated']}/{d.get('lots_stated')}",
                    "verdict": "PASS" if (same_blk and same_lot) else "FAIL"})
    return out


def bbls(d):
    """BBLs from the DOCUMENT. Refuses to guess, and says which part it read.

    Returns (bbls, provenance). Provenance is not decoration: a BBL built
    entirely from the resolution and one that borrowed the borough from the
    index are different objects, and the second must be visible as such.
    """
    ix = d.get("index") or {}
    boro = d.get("borough_stated")
    prov = "document"
    if not boro and ix.get("borough_code"):
        boro, prov = int(ix["borough_code"]), "borough_from_index"
    if not boro or not d.get("block_stated") or not d.get("lots_stated"):
        return [], "insufficient"
    if d.get("series"):
        # ⚠ one resolution, many calendar numbers. 112-08-BZY's document is
        # headed "104-08-BZY thru 119-08-BZY" and lists sixteen lots. Those
        # lots belong to the SERIES; which lot answers to which calendar
        # number is not stated in this document and must not be guessed.
        prov = "series_document — lots belong to the series, not to this " \
               "calendar number alone"
    return ([f"{int(boro)}{d['block_stated']:05d}{lot:04d}"
             for lot in d["lots_stated"]], prov)


# ---------------------------------------------------------------- emit

def to_facts(d, run_id=None, emit=True):
    """A decoded resolution -> citation-grade facts.

    Every fact cites calendar number + page, which is the BSA analogue of
    document_id + page: https://www.nyc.gov/assets/bsa/downloads/pdf/decisions/
    <calendar>.pdf, page N. That URL is stable and public, so the citation is
    walkable by anyone.
    """
    ix = d.get("index") or {}
    bs, bbl_prov = bbls(d)
    happened = _isoish(d.get("adopted"))
    recorded = _isoish(d.get("filed_cert"))
    out = []

    def add(f):
        f["bsa_parser"] = PARSER_NOTE
        f["bbl_provenance"] = bbl_prov
        # the completeness test, on every fact rather than only in a report:
        # "how many pages does this document have, and how many did I read?"
        f["pages_total"] = d.get("pages")
        f["pages_read"] = d.get("pages_read")
        out.append(f)
        if emit:
            sink.emit(f, run_id)

    outcome, outcome_src = outcome_from_document(d)
    granted = outcome == "granted"
    sections = sorted(d.get("zr_sections") or {})
    relief_sec = next((s for s in sections if s.startswith(("72-", "73-", "11-4", "64-"))), None)

    if granted:
        add(F.Fact("variance_granted", document_id=d["calendar"],
                   page=d.get("parcel_page") or 1, bbls=bs, source=SOURCE,
                   happened=happened, recorded=recorded,
                   verbatim=_tidy(d.get("action") or "", 200),
                   zr_section=relief_sec, application=ix.get("application"),
                   all_sections=sections, premises=d.get("premises"),
                   dob_job=d.get("dob_job"), outcome=outcome,
                   outcome_source=outcome_src,
                   # the details a reader needs about THIS grant, carried on the
                   # grant fact itself rather than left in the decode file
                   expires=_isoish(d.get("expires")),
                   expires_basis=d.get("expires_basis"),
                   cb=d.get("cb"), cb_recommendation=d.get("cb_recommendation"),
                   vote_affirmative=d.get("vote_affirmative"),
                   vote_negative=d.get("vote_negative"),
                   vote_unanimous=d.get("vote_unanimous"),
                   hearing_first=_isoish(d.get("hearing_first")),
                   applicant=d.get("applicant_stated") or d.get("owner_stated"),
                   owner=d.get("owner_stated"),
                   e_designation=d.get("e_designation"),
                   ceqr=d.get("ceqr"),
                   approved_plan_sheets=d.get("approved_plan_sheets")))
    else:
        add(F.Fact("filed", document_id=d["calendar"], page=1, bbls=bs,
                   source=SOURCE, happened=happened, recorded=recorded,
                   verbatim=_tidy(d.get("action") or "", 200),
                   zr_section=relief_sec, application=ix.get("application"),
                   outcome=outcome, outcome_source=outcome_src))

    env = d.get("envelope") or {}
    for layer, pred in (("permitted", "envelope_permitted"),
                        ("granted", "envelope_limited"),
                        ("proposed", "envelope_proposed")):
        for param, rec in (env.get(layer) or {}).items():
            if layer in ("granted", "proposed") and not granted:
                continue
            add(F.Fact(pred, document_id=d["calendar"], page=rec["page"],
                       bbls=bs, source=SOURCE, happened=happened,
                       recorded=recorded, value=rec["value"], unit=rec["unit"],
                       verbatim=rec["verbatim"], parameter=param,
                       zr_section=relief_sec, scope=rec.get("scope"),
                       applies_to=rec.get("applies_to")))
    if env.get("lot_area"):
        r = env["lot_area"]
        add(F.Fact("lot_area_stated", document_id=d["calendar"], page=r["page"],
                   bbls=bs, source=SOURCE, happened=happened, recorded=recorded,
                   value=r["value"], unit="sf", verbatim=r["verbatim"],
                   parameter="lot_area", zr_section=relief_sec))

    if granted:
        for c in d.get("conditions") or []:
            add(F.Fact("condition_imposed", document_id=d["calendar"],
                       page=c["page"], bbls=bs, source=SOURCE,
                       happened=happened, recorded=recorded,
                       verbatim=c["text"], zr_section=relief_sec))
    return out


MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}


def _isoish(s):
    if not s:
        return None
    m = re.match(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", s.strip())
    if not m:
        return None
    mo = MONTHS.get(m.group(1).lower())
    if not mo:
        return None
    return f"{int(m.group(3)):04d}-{mo:02d}-{int(m.group(2)):02d}"


# ---------------------------------------------------------------- index

def index(where=None):
    return bulk.socrata(APPLICATIONS, where=where)


def census():
    rows = index()
    c = {"total": len(rows),
         "by_application": Counter(r.get("application") for r in rows).most_common(),
         "by_status": Counter(r.get("status") for r in rows).most_common(),
         "with_url": sum(1 for r in rows if r.get("decisions_url")),
         "distinct_sections": len({r.get("section") for r in rows}),
         "non_numeric_lots": sum(1 for r in rows
                                 if (r.get("lots") or "").strip() and
                                 not (r.get("lots") or "").strip().isdigit()),
         "empty_lots": sum(1 for r in rows if not (r.get("lots") or "").strip()),
         "lots_at_20_chars": sum(1 for r in rows if len(r.get("lots") or "") == 20)}
    return c, rows


if __name__ == "__main__":
    c, rows = census()
    print(json.dumps(c, indent=1, default=str))
