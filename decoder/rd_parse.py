"""THE ONE PLACE THE ACRIS RD PAGE FORMAT IS KNOWN (login, 2026-08-20:
"all 4 url paths result in the exact same format so just figure it out once
and you are good for all 24,039,303"). keying_walk and every demo import
THIS - a second regex for the same page is how the same page gets learned
wrong twice (measured: the demo's fresh regex truncated MCON to "M" while
the walker's read it right).

Copy-paste rule: capture the page verbatim; omit only N/A, blank, or a
flag-column N. Sections are bounded by the NEAREST other section header -
the page lays REMARKS before PARCELS in html order, so fixed successors
swallow neighbours (measured on the Vernon Blvd MCON).
"""
import html as _h
import re

BORO = {"MANHATTAN": 1, "BRONX": 2, "BROOKLYN": 3, "QUEENS": 4,
        "STATEN ISLAND": 5}
SECTIONS = ("PARTY 1", "PARTY 2", "PARTY 3", "PARCELS", "REFERENCES",
            "REMARKS")
GHOST = {"", "NAME", "PARTY 2", "PARTY 3/OTHER", "PARCELS", "BOROUGH",
         "REMARKS", "REFERENCES", "CRFN"}
# scalar labels, exactly as the page prints them (used verbatim in the
# next-label lookahead so a value can never swallow the following label)
LABELS = ("DOCUMENT ID", "CRFN", "COLLATERAL", "# of PAGES", "REEL-PAGE",
          "EXPIRATION DATE", "DOC. TYPE", "FILE NUMBER", "ASSESSMENT DATE",
          "DOC. DATE", "RECORDED / FILED", "SLID #", "DOC. AMOUNT",
          "BOROUGH", "% TRANSFERRED", "RPTT #", "MAP SEQUENCE #", "MESSAGE")
_NEXT = "|".join(re.escape(x) for x in LABELS)
FIELD_KEYS = (("DOC. TYPE", "type"), ("# of PAGES", "pages"),
              ("DOC. DATE", "doc_date"), ("CRFN", "crfn"),
              ("RECORDED / FILED", "recorded"), ("BOROUGH", "borough"),
              ("DOC. AMOUNT", "amount"), ("% TRANSFERRED", "pct"),
              ("SLID #", "slid"), ("ASSESSMENT DATE", "assessment"),
              ("EXPIRATION DATE", "expiration"), ("COLLATERAL", "collateral"),
              ("FILE NUMBER", "file_nbr"), ("RPTT #", "rptt"),
              ("MAP SEQUENCE #", "map_seq"), ("MESSAGE", "message"),
              ("REEL-PAGE", "reel_page"))


def clean_html(body_text):
    """entities unescaped BEFORE any parsing - '&nbsp;' is data-shaped noise"""
    return _h.unescape(body_text).replace("\xa0", " ")


# ⚠ TABLES CLASSIFY THEMSELVES BY THEIR OWN HEADER ROW - never by position.
# Section-position bounding failed TWICE in one evening (fixed-successor
# swallowed neighbours; nearest-header cut PARCELS off and its rows fell
# into REMARKS). The page is a template and each table DECLARES itself:
# its first row names its columns. Read that declaration, map columns BY
# NAME (the gate's own by-name rule, applied to the custodian's html).
_TABLE_SIGS = {
    "party": ("NAME", "ADDRESS 1"),
    "parcels": ("BOROUGH", "BLOCK", "LOT"),
    "references": ("CRFN", "DOCUMENT ID"),
}


from html.parser import HTMLParser


class _Tables(HTMLParser):
    """⚠ THE PAGE NESTS 32 TABLES and regex table-matching let outer tables
    swallow inner ones' openings - the data tables never matched at all
    (measured on the Vernon Blvd MCON: 0 panels found while JERIST REALTY
    sat plainly in a <td>). A real parser tracks the nesting stack; every
    table yields its OWN rows regardless of depth. Rows belonging to inner
    tables are excluded from the outer table's rows - each cell text
    belongs to exactly one table."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # per open table: {"rows":[], "row":None, "pos"}
        self.cell = None
        self.done = []           # (rows, start_pos) in document order

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.stack.append({"rows": [], "row": None,
                               "pos": self.getpos()})
        elif tag == "tr" and self.stack:
            self.stack[-1]["row"] = []
        elif tag in ("td", "th") and self.stack:
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.stack:
            t = re.sub(r"\s+", " ", "".join(self.cell)).strip()
            if self.stack[-1]["row"] is not None:
                self.stack[-1]["row"].append(t)
            self.cell = None
        elif tag == "tr" and self.stack:
            row = self.stack[-1]["row"]
            if row is not None and any(row):
                self.stack[-1]["rows"].append(row)
            self.stack[-1]["row"] = None
        elif tag == "table" and self.stack:
            t = self.stack.pop()
            if t["rows"]:
                self.done.append((t["rows"], t["pos"]))

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def classified_tables(html):
    """[(kind, header_index_map, data_rows, line_pos)] for every table the
    page declares. Twin-table layout handled: a header-only table's
    signature carries to the headerless data table that follows it."""
    p = _Tables()
    p.feed(html)
    # getpos() is (line, col); _panel_of needs character offsets - convert
    starts = [0]
    for line in html.split("\n"):
        starts.append(starts[-1] + len(line) + 1)
    out = []
    pending = None
    for rows, (ln, col) in p.done:
        pos = starts[ln - 1] + col
        hdr = [c.upper().strip() for c in rows[0]]
        sig = next((k for k, s in _TABLE_SIGS.items()
                    if all(x in hdr for x in s)), None)
        if sig:
            ix = {name: i for i, name in enumerate(hdr)}
            if len(rows) > 1:
                out.append((sig, ix, rows[1:], pos))
                pending = None
            else:
                pending = (sig, ix)
        elif pending:
            out.append((pending[0], pending[1], rows, pos))
            pending = None
    return out


def _panel_of(html, pos):
    """which PARTY panel a table belongs to: the nearest preceding title"""
    cands = [(html.upper().rfind(pn, 0, pos), pn[-1])
             for pn in ("PARTY 1", "PARTY 2", "PARTY 3/OTHER")]
    k, panel = max(cands)
    return panel if k >= 0 else "?"


def parse_acris(html):
    """the WHOLE page -> the recorded_details dict, copy-paste rule applied.
    Caller asserts the id-echo BEFORE calling (a page proven to be about the
    requested doc); this function only reads."""
    flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    rec = {}
    for lab, key in FIELD_KEYS:
        g = re.search(re.escape(lab) + r":\s*(.{0,60}?)\s*(?=(?:" + _NEXT
                      + r"):|$)", flat)
        v = (g.group(1) if g else "").strip()
        if v and v.upper() not in ("N/A", "N/A-N/A"):
            rec[key] = v
    parties, pcls, refs = [], [], []
    for kind, ix, rows, pos in classified_tables(html):
        get = lambda cs, col: (cs[ix[col]].strip()
                               if col in ix and len(cs) > ix[col] else "")
        if kind == "party":
            panel = _panel_of(html, pos)
            for cs in rows:
                name = get(cs, "NAME")
                if not name or name.upper() in GHOST:
                    continue
                p = {"panel": panel, "name": name}
                for col, k in (("ADDRESS 1", "address"),
                               ("ADDRESS 2", "address2"), ("CITY", "city"),
                               ("STATE", "state"), ("ZIP", "zip"),
                               ("COUNTRY", "country")):
                    v = get(cs, col)
                    if v:
                        p[k] = v
                parties.append(p)
        elif kind == "parcels":
            for cs in rows:
                b = get(cs, "BOROUGH").upper().split("/")[0].strip()
                blk, lot = get(cs, "BLOCK"), get(cs, "LOT")
                if b in BORO and blk.isdigit() and lot.isdigit():
                    d = {"bbl": f"{BORO[b]}{int(blk):05d}{int(lot):04d}"}
                    for col, k in (("PARTIAL", "partial"),
                                   ("PROPERTY TYPE", "use"),
                                   ("PROPERTY ADDRESS", "address"),
                                   ("UNIT", "unit"), ("REMARKS", "remarks")):
                        v = get(cs, col)
                        if v and v.upper() != "N/A":
                            d[k] = v
                    for col, k in (("EASEMENT", "easement"),
                                   ("AIR RIGHTS", "air_rights"),
                                   ("SUBTERRANEAN RIGHTS", "subterranean")):
                        if get(cs, col).upper() == "Y":
                            d[k] = "Y"
                    pcls.append(d)
        elif kind == "references":
            # each value must LOOK like its column claims (a title cell or
            # stray text can never impersonate a crfn/doc id this way)
            _VALID = {"crfn": r"\d{13}", "doc_id": r"(FT_|BK_)?\d{8,20}",
                      "borough": r"[A-Z ]{2,15}", "year": r"\d{2,4}",
                      "reel": r"\d{1,6}", "page": r"\d{1,5}",
                      "file_nbr": r"[A-Z0-9-]{4,15}"}
            for cs in rows:
                r = {}
                for col, k in (("CRFN", "crfn"), ("DOCUMENT ID", "doc_id"),
                               ("BOROUGH", "borough"), ("YEAR", "year"),
                               ("REEL", "reel"), ("PAGE", "page"),
                               ("FILE NBR", "file_nbr")):
                    v = get(cs, col).replace(" ", "")
                    if v and v.upper() != "N/A" and \
                            re.fullmatch(_VALID[k], v, re.I):
                        r[k] = v
                if r and ("crfn" in r or "doc_id" in r or "file_nbr" in r):
                    refs.append(r)
    if parties:
        rec["parties"] = parties
    if pcls:
        rec["parcels"] = pcls
    if refs:
        rec["references"] = refs
    # REMARKS is a text box, not a table: take the textarea's own content
    m = re.search(r"<textarea[^>]*>(.*?)</textarea>", html, re.S | re.I)
    if m:
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip()
        if t:
            rec["remarks"] = t
    return rec
