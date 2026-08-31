"""tablecheck.py -- the checks that need no model.

>> Every other check in this project asks a language model whether a language
   model was right.  These do not.  They are arithmetic, calendar order, string
   equality and format -- facts from outside the system -- and they are the only
   layer that cannot be fooled by two readers sharing a blind spot.

   Round 1 is the reason this exists: two different model families, no contact,
   made two IDENTICAL errors and neither caught either one.  Family diversity
   does not guarantee decorrelated failure.  Arithmetic does.

   Run:  python tablecheck.py <table.md> [<table.md> ...]

   Checks, in order of how quietly they fail today:

     CITE   every row carries a quote.  A row with no citation is a
            hallucination, whoever wrote it, and it is invisible in prose.
     MARK   a row whose meaning depends on a MARK carries a rect.  Framework v4
            rule 1.  A quotation of struck words is byte-identical to a
            quotation of live words, so STRUCK cited by characters alone is a
            claim nobody downstream -- human or model -- can ever falsify.  On
            RC_1598772 that distinction was the difference between conveying two
            lots and conveying none.
     DATE   instrument <= acknowledgment <= recording.  A document cannot be
            recorded before it is signed.  This is what made FT_1000000027200's
            "sworn 1981, recorded 1983" suspicious before anyone zoomed -- the
            reader that misread the digit had the contradiction in its own table
            and no rule made it look.
     BBL    a BBL parses to borough 1-5 + block + lot, and the lots named in the
            body match the ones in the index.  RC_400026's index lot was 0000, a
            placeholder that renders exactly like a measured value.
     SUM    stated totals equal the sum of their parts.  2002122700120002's tax
            lines sum to $7,673.00; RC_300106's five mortgages sum to
            $32,600,000.  Both are stated ON the document, so the document
            checks itself.
     REF    every reel/page/liber pointer is well formed, and reported so it can
            later be resolved against the corpus.  RC_300106 alone cites five.

   A FAIL here is a fact, not an opinion.  A model may not overrule it.
"""

import argparse
import datetime as dt
import pathlib
import re
import sys

MONEY = re.compile(r"\$\s?([\d,]+(?:\.\d{2})?)")
BBL = re.compile(r"\b([1-5])(\d{5})(\d{4})\b")

# >> v1 of this file read ISO dates only, and so MISSED the one error we knew
#    existed.  On FT_1000000027200 an extractor recorded the acknowledgment as
#    1981 and the recording as "4 April 1983" -- a document sworn two years
#    after it was filed, sitting in its own table.  The order check was built
#    for exactly that and never fired, because the writer used prose and the
#    checker assumed a format.
#
#    A check that only works when the writer happens to match your assumption
#    is not a check.  Read every shape a date is actually written in.
MONTHS = ("january february march april may june july august september "
          "october november december").split()
ABBR = {m[:3]: i + 1 for i, m in enumerate(MONTHS)}
ABBR.update({m: i + 1 for i, m in enumerate(MONTHS)})
ABBR["sept"] = 9

_Y = r"(1[89]\d{2}|20\d{2})"
_MON = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|" \
       r"aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
DATE_FORMS = [
    # 1983-04-04
    (re.compile(r"\b" + _Y + r"-(\d{2})-(\d{2})\b"), "ymd"),
    # 4 April 1983  /  23rd March 1983
    (re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+" + _MON + r"\.?,?\s+" + _Y + r"\b",
                re.I), "dmy"),
    # April 25, 1911  /  Nov. 4, 1942
    (re.compile(r"\b" + _MON + r"\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+" + _Y + r"\b",
                re.I), "mdy"),
    # 11/19/2002  /  4/25/1911
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/" + _Y + r"\b"), "slash"),
]


def all_dates(text):
    """Every date in the text, in any shape it is actually written."""
    out = []
    for rx, kind in DATE_FORMS:
        for m in rx.finditer(text):
            try:
                if kind == "ymd":
                    d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                elif kind == "dmy":
                    d = dt.date(int(m.group(3)), ABBR[m.group(2).lower().rstrip(".")],
                                int(m.group(1)))
                elif kind == "mdy":
                    d = dt.date(int(m.group(3)), ABBR[m.group(1).lower().rstrip(".")],
                                int(m.group(2)))
                else:
                    d = dt.date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
            except (ValueError, KeyError):
                continue
            out.append((d, m.start(), m.end()))
    return out
# "reel 0058 page 489", "liber 811 of deeds, page 355", "Reel 65 at Page 2330"
POINTER = re.compile(
    r"\b(reel|liber|book)\s*[#:]?\s*(\d{1,6})\b[^.;|]{0,40}?\bpage\s*[#:]?\s*(\d{1,6})\b",
    re.I)
LOTWORD = re.compile(r"\blots?\s+(?:no\.?\s*)?([\d,\s and]+?)(?=\s*(?:in\s+)?block)", re.I)
BLOCKWORD = re.compile(r"\bblock\s+(?:no\.?\s*)?(\d{1,5})\b", re.I)

# >> Framework v4 rule 1.  A citation format bounds the class of claims it can
#    support.  Ours encoded characters, so it could support claims about WHICH
#    WORDS are on the page and nothing about HOW THEY ARE MARKED -- and marks
#    are not characters, so no amount of better OCR closes that.
#
#    p2 | [0.12,0.34,0.71,0.38] | struck | "subject, however, to all assessments"
RECT = re.compile(r"\[\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\s*,"
                  r"\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\s*\]")
MARKS = ("plain", "struck", "inserted", "flourish", "marginal", "uncertain")
MARKWORD = re.compile(r"(?<![\w-])(" + "|".join(MARKS) + r")(?![\w-])", re.I)
MODES = ("ASSERT", "TRANSFER", "CREATE", "MODIFY", "TERMINATE", "STRUCK")
COLNAMES = ("#", "citation", "time", "date", "basis", "until", "function", "mode",
            "where", "bbls", "parties", "quantity", "terms", "summary")

# >> FEED -- is this row consumable by Reorganize and Resolve?
#
#    Extraction is step 1 of Reconstruction; steps 2 and 3 run MECHANICALLY or
#    not at all.  A row can be perfectly faithful to the document and still be
#    useless: if `bbls` is prose, Reorganize cannot fan it, and a row it cannot
#    fan reaches no parcel at all.  That is deferral, not extraction.
#
#    Resolution needs no extra field.  Given every event for a BBL, ordered,
#    each tagged with a function, `mode` already says whether it adds, changes,
#    moves or ends what came before -- Resolve is ordering and projection, not
#    re-interpretation.  So BBL, time and function must be machine-readable;
#    everything else on the row is event context for the human and for Derive.
#
#    This check needs NO ground truth.  It is a property of the table alone,
#    which makes it the one accuracy-adjacent number available on every round
#    from the first document onward.
FUNCS = ("IDENTITY", "TITLE", "ENTITLEMENT", "ENVELOPE", "ENCUMBRANCE", "CAPITAL",
         "PERMIT", "AS_BUILT", "OCCUPANCY", "COST", "VALUE")
BASES = ("effective", "instrument", "execution", "acknowledgment", "unsupported")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
BBLS_OK = re.compile(r"^(?:\d{10}(?:\s*,\s*\d{10})*|SET:\s*\S.*|INSTRUMENT|UNPLACED)$")


def header_index(md):
    """Map column name -> position, from the table's own header row.

    >> Read the table's declared shape instead of assuming column order.  The
       DATE check died once already by assuming a format the writer did not
       have to match.
    """
    for line in md.splitlines():
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            continue
        cells = [c.strip().strip("`* ").lower() for c in s.strip("|").split("|")]
        hit = {c: i for i, c in enumerate(cells) if c in COLNAMES}
        if len(hit) >= 4:
            return hit
    return {}


def cell(row, hdr, name):
    i = hdr.get(name)
    return row[i] if i is not None and i < len(row) else None


def rect_of(text):
    """(rect, why-it-is-unusable).  A malformed box is worse than none: it
    looks like evidence and points nowhere."""
    m = RECT.search(text)
    if not m:
        return None, None
    v = [float(g) for g in m.groups()]
    if any(x < 0.0 or x > 1.0 for x in v):
        return v, "outside 0..1 -- coordinates must be normalised to the page"
    if v[0] >= v[2] or v[1] >= v[3]:
        return v, "x0>=x1 or y0>=y1 -- empty or transposed box"
    return v, None


def mode_of(row, hdr):
    c = cell(row, hdr, "mode")
    if c is not None:
        t = c.strip("`* ").upper()
        return t if t in MODES else None
    for x in row:                       # no header: a bare cell equal to a mode
        t = x.strip("`* ").upper()
        if t in MODES:
            return t
    return None


def cite_of(row, hdr):
    c = cell(row, hdr, "citation")
    if c is not None:
        return c
    for x in row:
        if '"' in x or "“" in x:
            return x
    return " ".join(row)


def rows(md):
    """Every pipe-table data row, as a list of cell strings."""
    out = []
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("|") or not s.endswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or all(set(c) <= set("-: ") for c in cells):
            continue                      # separator row
        out.append(cells)
    return out


def money(s):
    return [float(m.replace(",", "")) for m in MONEY.findall(s)]


def check(path):
    md = path.read_text(encoding="utf-8", errors="replace") \
        if hasattr(path, "read_text") else path
    fails, notes = [], []
    data = rows(md)
    hdr = header_index(md)

    # ---- CITE ------------------------------------------------------------
    # An event row is one whose first cell looks like an event id (E1, EV003,
    # RC_x-EV001).  Header rows and sub-tables are skipped, not failed.
    ev = [r for r in data if re.match(r"^[`*\s]*(?:[A-Z0-9_]+-)?E[V]?\d+", r[0])]
    for r in ev:
        joined = " ".join(r)
        if '"' not in joined and "“" not in joined and "'" not in joined:
            fails.append("CITE  row %s carries no quoted evidence" % r[0].strip("` *"))
    notes.append("CITE  %d event rows, %d without a quote"
                 % (len(ev), sum(1 for f in fails if f.startswith("CITE"))))

    # ---- MARK ------------------------------------------------------------
    # >> Fail only the claims geometry is LOAD-BEARING for -- a STRUCK row, or
    #    any declared mark that is not `plain`.  A v3-era table has neither, so
    #    it passes with a note saying how few rows carry a rect.  That is the
    #    honest report: the gap is stated, and no wolf is cried.  A checker that
    #    cries wolf gets ignored, and then the real failure passes too.
    n_rect, seen = 0, {}
    for r in ev:
        rid = r[0].strip("` *")
        cc = cite_of(r, hdr)
        rect, err = rect_of(cc)
        if rect and not err:
            n_rect += 1
        if err:
            fails.append("MARK  row %s rect %s -- %s" % (rid, rect, err))
        mw = MARKWORD.search(cc)
        mark = mw.group(1).lower() if mw else None
        if mark:
            seen[mark] = seen.get(mark, 0) + 1
        if mode_of(r, hdr) == "STRUCK" and not rect:
            fails.append(
                "MARK  row %s is STRUCK with no rect -- a quotation of struck "
                "words is byte-identical to a quotation of live words, so "
                "nothing downstream can tell this from a fabrication" % rid)
        elif mark and mark != "plain" and not rect:
            fails.append(
                "MARK  row %s claims mark '%s' with no rect -- a mark is not a "
                "character, and geometry is its only evidence" % (rid, mark))
    notes.append("MARK  %d of %d event rows carry a rect%s"
                 % (n_rect, len(ev),
                    ("; " + ", ".join("%s x%d" % kv for kv in sorted(seen.items())))
                    if seen else ""))

    # ---- FEED ------------------------------------------------------------
    ready = 0
    for r in ev:
        rid = r[0].strip("` *")
        ok = True

        # Q1 -- can Reorganize list the BBLs this event affects?
        b = cell(r, hdr, "bbls")
        if b is not None:
            bv = b.strip().strip("`* ")
            if not BBLS_OK.match(bv):
                fails.append("FEED  row %s bbls %r is not fannable -- needs a BBL "
                             "list, SET:<criterion>, INSTRUMENT or UNPLACED. A "
                             "description is a row that failed the test." % (rid, bv[:50]))
                ok = False
        else:
            ok = False                      # no column: not consumable, not a fail

        # Q2 -- can Resolve place it in time?
        d = cell(r, hdr, "date")
        if d is not None:
            dv = d.strip().strip("`* ")
            if not (ISO.match(dv) or dv.upper().startswith("UNKNOWN")):
                fails.append("FEED  row %s date %r is not sortable -- ISO "
                             "YYYY-MM-DD or UNKNOWN" % (rid, dv[:40]))
                ok = False
            bs = (cell(r, hdr, "basis") or "").strip().strip("`* ").lower()
            if bs and bs not in BASES:
                fails.append("FEED  row %s basis %r is not one of %s"
                             % (rid, bs[:30], "/".join(BASES)))
                ok = False
        else:
            ok = False

        # Q3 -- can Resolve project it? the function must be one of the eleven
        f = (cell(r, hdr, "function") or "").strip().strip("`* ").upper()
        if f:
            if f not in FUNCS:
                fails.append("FEED  row %s function %r is not one of the eleven"
                             % (rid, f))
                ok = False
        else:
            ok = False

        if ok:
            ready += 1
    if ev:
        notes.append("FEED  %d of %d rows Reconstruction-ready (%.0f%%) -- "
                     "fannable bbls, sortable date, function of the eleven"
                     % (ready, len(ev), 100.0 * ready / len(ev)))

    # ---- DATE ------------------------------------------------------------
    # Collect every ISO date in the file with the word nearest it, then assert
    # signing <= acknowledgment <= recording.  Only fires when at least two of
    # the three are present, so a document that states one date is not failed.
    # >> READ THE LABELLED BLOCK. Do not scan prose.
    #
    #    v2 of this check harvested every date in the file and assigned roles by
    #    looking for trigger words within +/-140 characters.  The labelled block
    #    this project now mandates is about 70 characters long, so ALL THREE
    #    dates sit inside each other's windows and match all three vocabularies.
    #    `kinds` collapsed to three identical sets and `min(a) > max(b)` became
    #    unsatisfiable.
    #
    #    Extractor C proved it with two probes: the same three dates written on
    #    consecutive lines AS INSTRUCTED reported zero failures, while the same
    #    dates separated by 420 characters of filler failed correctly.  A deed
    #    recorded eight years before it was signed passed clean in the required
    #    format.  The check built for FT_1000000027200's "sworn 1981, recorded
    #    1983" was dead on every table written to spec.
    #
    #    Worse, scanning the whole file ingested the extractor's own prose
    #    WARNING about a map-filing date as a date claim.
    #
    #    So: parse the three labels and nothing else.  A date the writer did not
    #    label is not a claim about this document's chronology.
    LABEL = re.compile(
        r"^\s*(instrument|acknowledged|recorded|expires)\s*[:=]\s*(\S+)",
        re.I | re.M)
    kinds = {}
    labelled = False
    for m in LABEL.finditer(md):
        labelled = True
        val = m.group(2).strip().strip("`*|")
        if val.upper().startswith("UNKNOWN"):
            continue
        got = all_dates(val)
        if got:
            kinds[m.group(1).lower()] = {got[0][0]}
    if not labelled:
        fails.append("DATE  no labelled date block "
                     "(instrument:/acknowledged:/recorded:) -- chronology "
                     "unverifiable, and a missing block must never read as a pass")
    order = [k for k in ("instrument", "acknowledged", "recorded") if k in kinds]
    for a, b in zip(order, order[1:]):
        lo, hi = min(kinds[a]), max(kinds[b])
        if lo > hi:
            fails.append("DATE  %s %s is AFTER %s %s -- impossible order"
                         % (a, lo, b, hi))
    if order:
        notes.append("DATE  " + " <= ".join(
            "%s %s" % (k, min(kinds[k])) for k in order))

    # >> v4 added `expires`.  It sits outside the instrument<=ack<=recorded
    #    chain -- it is the end of a term, not a step in filing it.  On
    #    RC_1598772 every covenant expires 1915-01-01, stated once on page 2;
    #    a table that omits it is wrong about the parcel from 1915 onward.
    if "expires" in kinds and "instrument" in kinds:
        exp, ins = min(kinds["expires"]), min(kinds["instrument"])
        if exp < ins:
            fails.append("DATE  expires %s is BEFORE instrument %s -- a term "
                         "cannot end before it begins" % (exp, ins))
        else:
            notes.append("DATE  expires %s (%d days after instrument)"
                         % (exp, (exp - ins).days))

    if "time" in hdr and "until" in hdr:
        for r in ev:
            t, u = cell(r, hdr, "time"), cell(r, hdr, "until")
            if not t or not u:
                continue
            td, ud = all_dates(t), all_dates(u)
            if td and ud and ud[0][0] < td[0][0]:
                fails.append("DATE  row %s until %s is before time %s"
                             % (r[0].strip("` *"), ud[0][0], td[0][0]))

    # ---- BBL / lots ------------------------------------------------------
    bbls = set(BBL.findall(md))
    idx_lots = {int(l) for _, _, l in bbls}
    idx_blocks = {int(b) for _, b, _ in bbls}
    for _, blk, lot in bbls:
        if int(lot) == 0:
            notes.append("BBL   lot 0000 in %s%s%s -- placeholder, not a lot; a "
                         "body-stated lot cannot be confirmed from it"
                         % (_, blk, lot))
    body_lots = set()
    for m in LOTWORD.finditer(md):
        body_lots |= {int(x) for x in re.findall(r"\d+", m.group(1))}
    body_blocks = {int(m.group(1)) for m in BLOCKWORD.finditer(md)}
    if body_lots and idx_lots and not (body_lots & idx_lots):
        fails.append("BBL   body lots %s share nothing with index lots %s"
                     % (sorted(body_lots), sorted(idx_lots)))
    if body_blocks and idx_blocks and not (body_blocks & idx_blocks):
        fails.append("BBL   body blocks %s share nothing with index blocks %s"
                     % (sorted(body_blocks), sorted(idx_blocks)))
    if bbls:
        notes.append("BBL   %d distinct: blocks %s lots %s"
                     % (len(bbls), sorted(idx_blocks), sorted(idx_lots)))

    # ---- SUM -------------------------------------------------------------
    # Where a line says "total"/"aggregate", test whether some subset of the
    # other amounts on the page reaches it.  Reported, never failed: a total
    # may legitimately cover parts not in the table.
    amounts = money(md)
    for line in md.splitlines():
        if not re.search(r"\btotal\b|\baggregate\b", line, re.I):
            continue
        want = money(line)
        if not want:
            continue
        t = max(want)
        others = [a for a in amounts if a != t]
        # >> v1 tried only the whole set or pairs, so it could not reconcile
        #    2002122700120002's tax total -- 1,924.50 + 3,849.00 + 0 + 962.25
        #    + 937.25 is FIVE terms.  It then reported "not reconciled" on a
        #    document whose arithmetic is correct, which is a false alarm, and
        #    a checker that cries wolf gets ignored.  Real subset sum, in cents
        #    so floats never decide equality.
        cents = sorted({int(round(a * 100)) for a in others if a}, reverse=True)
        target = int(round(t * 100))
        reach = {0}
        for c in cents[:24]:                       # bounded; totals are short
            reach |= {r + c for r in reach if r + c <= target}
            if target in reach:
                break
        notes.append("SUM   stated total %.2f %s" %
                     (t, "reconciles from its parts"
                      if target in reach else "NOT reconciled from table amounts"))

    # ---- REF -------------------------------------------------------------
    ptrs = [(a.lower(), b, c) for a, b, c in POINTER.findall(md)]
    if ptrs:
        notes.append("REF   %d corpus pointer(s): %s"
                     % (len(ptrs), ", ".join("%s %s p%s" % p for p in ptrs[:6])))

    return fails, notes


# ---------------------------------------------------------------------------
# >> PROBES.  This file has shipped broken three times -- twice on DATE, once on
#    SUM -- and each time it printed confident output while the defect it was
#    built for walked straight through.  v2 of DATE let a deed recorded EIGHT
#    YEARS BEFORE IT WAS SIGNED pass clean, in the exact format this project
#    mandates.  It was caught by an extractor writing two probes, not by review.
#
#    So the probes live here now, beside the code, and run with --selftest.
#    Each states the defect it plants and the failure it demands.  A check that
#    has never been shown to fire is not a check; it is a comment that runs.
_H = ("| # | citation | time | until | function | mode | where | parties | "
      "quantity | terms | summary |\n"
      "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
_D = "instrument: 1911-04-24\nacknowledged: 1911-04-24\nrecorded: 1911-04-25\n\n"


def _row(cite, time="1911-04-24", until="", mode="ASSERT"):
    return ("| E1 | %s | %s | %s | ENCUMBRANCE | %s | SUBJECT 5004030016 | "
            "asserted by: the company | UNKNOWN | ruled out in ink | one line |\n"
            % (cite, time, until, mode))


_Q = '"subject, however, to all assessments"'

# the v4+ row shape, for the FEED probes
_F = ("| # | citation | date | basis | until | function | mode | bbls | "
      "parties | quantity | terms | summary |\n"
      "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")


def _frow(n="E1", date="1911-04-14", basis="instrument", func="ENCUMBRANCE",
          bbls="5004030016", parties="asserted by: the company"):
    return ("| %s | p2 · [0.1,0.2,0.5,0.3] · plain · %s | %s | %s |  | %s | CREATE "
            "| %s | %s | UNKNOWN | conditions | one line |\n"
            % (n, _Q, date, basis, func, bbls, parties))

PROBES = [
    # the whole reason rule 1 exists: an unfalsifiable STRUCK claim
    ("STRUCK cited by characters only is refused",
     _D + _H + _row("p2 · " + _Q, mode="STRUCK"),
     ["STRUCK with no rect"]),

    ("STRUCK with a rect passes",
     _D + _H + _row("p2 · [0.12,0.34,0.71,0.38] · struck · " + _Q, mode="STRUCK"),
     []),

    ("a transposed box is refused, not silently accepted",
     _D + _H + _row("p2 · [0.71,0.34,0.12,0.38] · struck · " + _Q, mode="MODIFY"),
     ["transposed box"]),

    ("un-normalised coordinates are refused",
     _D + _H + _row("p2 · [0.12,0.34,1.71,0.38] · struck · " + _Q, mode="MODIFY"),
     ["must be normalised"]),

    ("any non-plain mark without a rect is refused",
     _D + _H + _row("p2 · inserted · " + _Q, mode="MODIFY"),
     ["claims mark 'inserted' with no rect"]),

    # >> the word `struck` also appears in this row's `terms` and `summary`.
    #    Parsing the CITATION CELL rather than the joined row is what keeps that
    #    from reading as a mark claim.  Row-level scanning is how the DATE check
    #    died: every field fell inside every other field's window.
    ("prose containing a mark word is not a mark claim",
     _D + _H + _row("p2 · " + _Q, mode="ASSERT"),
     []),

    ("a term cannot end before it begins",
     "instrument: 1911-04-24\nrecorded: 1911-04-25\nexpires: 1909-01-01\n\n"
     + _H + _row("p2 · " + _Q),
     ["expires 1909-01-01 is BEFORE instrument"]),

    ("a row cannot expire before it starts",
     _D + _H + _row("p2 · " + _Q, time="1911-04-24", until="1905-01-01"),
     ["until 1905-01-01 is before time 1911-04-24"]),

    # >> the regression that must never come back.  Extractor C planted exactly
    #    this and v2 of the DATE check reported zero failures.
    ("recorded eight years before signed still fails, in the mandated format",
     "instrument: 1911-04-24\nacknowledged: 1911-04-24\nrecorded: 1903-04-25\n\n"
     + _H + _row("p2 · " + _Q),
     ["impossible order"]),

    ("a missing date block never reads as a pass",
     _H + _row("p2 · " + _Q),
     ["no labelled date block"]),

    ("a row with no quote is refused",
     _D + _H + _row("p2, third paragraph"),
     ["carries no quoted evidence"]),

    # ---- FEED: consumability by Reorganize and Resolve --------------------
    ("prose in bbls is refused -- Reorganize cannot fan a description",
     _D + _F + _frow(bbls="lots on four named streets"),
     ["is not fannable"]),

    ("a BBL list and a SET criterion both pass",
     _D + _F + _frow(bbls="5004030016, 5004030017")
        + _frow(n="E2", bbls="SET: all lots in plat 995 B"),
     []),




    ("an unsortable date is refused",
     _D + _F + _frow(date="April 25, 1911"),
     ["is not sortable"]),

    ("a basis outside the vocabulary is refused",
     _D + _F + _frow(basis="recorded"),
     ["is not one of"]),

    ("a function outside the eleven is refused",
     _D + _F + _frow(func="REGISTRY"),
     ["not one of the eleven"]),

    # >> a v3-era table has no rects and no STRUCK rows.  It must PASS, with the
    #    gap stated in a note.  A checker that fails everything gets ignored,
    #    and then the real failure passes too.
    ("a v3 table passes and its gap is reported, not failed",
     _D + "| # | citation | time | function | mode | where | parties |\n"
          "| --- | --- | --- | --- | --- | --- | --- |\n"
          "| E1 | p2 " + _Q + " | 1911-04-24 | ENCUMBRANCE | CREATE | "
          "SUBJECT 5004030016 | grantor → grantee |\n",
     []),
]


def selftest():
    bad = 0
    for name, text, expect in PROBES:
        fails, notes = check(text)
        missing = [e for e in expect if not any(e in f for f in fails)]
        unmatched = [f for f in fails if not any(e in f for e in expect)]
        ok = not missing and not unmatched
        print("  %-4s %s" % ("ok" if ok else "FAIL", name))
        if not ok:
            bad += 1
            for e in missing:
                print("        demanded a failure containing %r -- none fired" % e)
            for f in unmatched:
                print("        unexpected failure: %s" % f)
    print("\n%d probe(s) failed" % bad)
    if not bad:
        print("Every check fires on the defect it was built for, and on nothing\n"
              "else. Both earlier versions of the DATE check claimed as much\n"
              "without evidence, and both claims were false.")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tables", nargs="*")
    ap.add_argument("--selftest", action="store_true",
                    help="prove the checks fire, and fire only where intended")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.tables:
        ap.error("give one or more tables, or --selftest")
    bad = 0
    for t in a.tables:
        p = pathlib.Path(t)
        print("\n=== %s" % p)
        if not p.exists():
            print("  MISSING"); bad += 1; continue
        fails, notes = check(p)
        for n in notes:
            print("  .  %s" % n)
        for f in fails:
            print("  FAIL %s" % f)
        bad += len(fails)
    print("\n%d failure(s)" % bad)
    print("A FAIL is arithmetic or calendar order, not a reading. No model "
          "overrules it.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
