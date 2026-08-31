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
    md = path.read_text(encoding="utf-8", errors="replace")
    fails, notes = [], []
    data = rows(md)

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
    LABEL = re.compile(r"^\s*(instrument|acknowledged|recorded)\s*[:=]\s*(\S+)",
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tables", nargs="+")
    a = ap.parse_args()
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
