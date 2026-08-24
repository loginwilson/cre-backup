"""
THE PRE-DELIVERY PASS — mechanical enforcement of the delivery rules.

WHY THIS EXISTS (measured, Grade Ledger 2026-08-24):
  Defect classes whose cure produced an ARTIFACT died (crop-files: clean
  5 straight runs; count-in-action: clean 2). Classes whose cure required
  VIGILANCE did not (narrative import reached TEN members). This script
  converts the vigilance rules into a mechanical pass that either prints
  findings or prints CLEAN. Running it produces an artifact; remembering
  it does not.

USAGE
  1. Write the drafted delivery to a file BEFORE delivering it, with the
     three sections marked by these exact lines:
         ## EVENT TEST
         ## DATA TEST
         ## ANYBODY TEST
  2. python precheck.py <draft.md>
  3. Resolve every finding: ADD THE ROW to the data test, or DELETE the
     claim from the prose. Then deliver.

WHAT IT CHECKS
  DOWNWARD    every proper noun and number in the EVENT TEST and ANYBODY
              TEST must also appear in the DATA TEST. (r47: the officers
              lived only in prose; r48: Proclamation 7402 and three other
              authorities lived only in prose.)
  TRIGGERS    Compose Card #4 word list — motive, era-practice, scale and
              relationship words. (r47: "wanted to".)
  OPENING     the anybody test's FIRST sentence may locate the deal only
              with tokens the table carries. (r42 "Williamsburg", r46
              "Prospect Heights", r48 "New York Harbor", r49 "Harlem" —
              all the same slot; r49 was caught here before delivery.)
  CARDINALS   every digit or spelled-out cardinal, listed for licensing
              by a count run in-action.
  VAGUE       "a couple", "several", "mostly" — cardinals in disguise.
              (r50: "a couple of vacant lots" was three.)
  CORPUS      claims about THIS FILE ("first in this corpus", "Nth
              sighting") need a grep in the same action. (r51: two such
              claims were FALSE and reached the evidence table.)
  EARNED-tick every check mark asserts two independent readings agreed
              (Card #7). (r50: a tick claimed on ids never compared.)
  SUPERLATIVE absolute claims, where prose over-generalises and where two
              layers end up disagreeing. (r49: "the root".)
  LENGTH      anybody-test words against table rows. (r51 login ruling:
              the template is the SEQUENCE and the RULES, never the SIZE
              — measured drift 297/311/281 words for 7/13/6-page docs.)
  HEADLINE    the run's H1 title line is a PROSE LAYER and was ungated
              until r52: every distinctive token in it must appear in at
              least one of the three tests. (r52: the headline named the
              type-shelf mismatch — the run's best finding — and no test
              mentioned it anywhere.)
  UNRES-ROW   every item in the ⚠ Unresolved stream must NAME THE ROW it
              bears on, or say it bears on none. An unresolved item that
              cites no row is orphaned: it floats free of the evidence and
              disciplines no cell. (r52: the tenancy inconsistency bore on
              rows 1-2, said so nowhere, and both rows went on asserting
              the branch the item calls unsettled — the mirror of Card
              #15's WHY-BIND, applied to the other stream.)
  CITED-ROW   the converse of UNRES-ROW: a row that an unresolved item
              NAMES must carry the doubt IN THE ROW (a branch written
              "A or B", or a warning mark). Together the two make a cell
              that asserts what the Unresolved stream denies structurally
              unrepresentable. (r52: rows 1-2 routed title to named
              survivors while the stream called the branch open.)
  DATE-ARITH  every stated interval recomputed against the dates present.
              A computed figure READS as verified, so a wrong one is worse
              than none. (r53: 'eleven years and eleven months' for an
              interval of 10y 11m.)
  BUDGETS     three, measured apart (r53 login ruling): the EVENT test
              SHRINKS as the document stops surprising; the DATA test GROWS
              with the number of data points, because richness is coverage;
              the ANYBODY test DOES NOT GROW - complexity changes what it
              says, not how much. Its budget is the READER's, not the
              document's.
  HEDGES      warning marks in the record must survive into delivery.
"""

import re
import sys
import pathlib

TRIGGERS = [
    "wanted to", "needed to", "so they could", "in order to", "so that",
    "which is why", "was how", "because", "typically", "at the time",
    "in those days", "the practice was", "one of the largest", "the biggest",
    "operates nationwide", "owns millions", "family firm", "landlord",
    "money partner", "its bank", "his bank", "her bank", "their bank",
]

RELATIONSHIP = [
    "wife", "husband", "son", "daughter", "family", "brother", "sister",
    "heir", "heirs", "partner of", "related to", "father", "mother",
]

SUPERLATIVES = [
    "the root", "the only", "the first", "the last", "the biggest",
    "the largest", "the smallest", "the oldest", "the newest", "never",
    "always", "every", "all of", "none of", "underneath every",
    "sits under", "unique", "unprecedented", "invariably", "must be",
]

# R51: claims ABOUT THIS CORPUS made from memory instead of from a query.
# Both of r51's C+ misses were this shape, and both reached the table.
CORPUS_CLAIMS = [
    "in this corpus", "first ever", "first time", "never seen",
    "never before", "sighting", "the only instance", "first in the file",
    "first appearance", "has never", "no prior", "unprecedented in",
]

# R50: vague quantifiers are cardinals in disguise. "a couple of vacant
# lots" shipped a wrong number past a check that only sought numerals.
VAGUE_QUANTIFIERS = [
    "a couple", "a handful", "a few", "several", "most ", "mostly",
    "many ", "numerous", "a number of", "the bulk of", "the majority",
    "almost all", "nearly all", "a dozen", "dozens", "some of the",
]

CARDINAL_WORDS = [
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "twenty",
    "thirty", "forty", "fifty", "hundred", "dozen",
]

# tokens that are structurally fine in prose without a table row
STOPWORDS = {
    "The", "This", "That", "These", "Those", "A", "An", "And", "But", "For",
    "Nor", "Or", "So", "Yet", "In", "On", "At", "To", "From", "By", "With",
    "It", "Its", "He", "She", "They", "We", "I", "If", "When", "While",
    "Each", "Every", "All", "Both", "One", "Two", "No", "Not", "Only",
    "After", "Before", "Under", "Over", "Between", "Through", "During",
    "Here", "There", "Then", "Now", "Read", "Derived", "Inferred",
    "Claims", "Unresolved", "Reconciliation", "Exhibit", "Tract", "Row",
    "Event", "Data", "Anybody", "Mode", "What", "Why", "Note", "None",
    "Without", "Upon", "Whereas", "Four", "Five", "Six",
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
    "Sunday",
    # instrument-structure words: grammar, not facts
    "WHEREAS", "NOW", "THEREFORE", "RESOLVED", "WITNESSETH", "IN", "WITNESS",
    "ACTOR", "CLAIMS", "Section", "Article", "Paragraph", "Jr", "Sr", "Esq",
    "LLC", "LLP", "Inc", "Corp", "LP", "Ltd", "Co",
    # uppercase forms of the function words above (emphasis styling)
    "THE", "THIS", "THAT", "AND", "OR", "OF", "TO", "FROM", "BY", "WITH",
    "AT", "ON", "FOR", "AS", "IS", "IT", "ITS", "NOT", "NO", "ONE", "TWO",
    "ALL", "EACH", "EVERY", "READ", "DERIVED", "INFERRED", "VALUE", "COST",
    "TITLE", "IDENTITY", "OCCUPANCY", "ENCUMBRANCE", "ENVELOPE",
    "ENTITLEMENT", "PERMIT", "ASBUILT", "CAPITAL", "PAGE", "ARITHMETIC",
    "EXECUTION", "SEQUENCE", "MECHANISM", "RECITES", "STATED", "DRAWN",
    "EVENT", "First", "Second", "Third", "Borough",
}

# Punctuation-joined fragments of a stopword ("Jr. National Trust") re-split.
SPLIT_ON = re.compile(r"(?:^|\s)(?:Jr\.|Sr\.|Esq\.|Inc\.|Corp\.|LLC|LLP)\s*")

SECTION_RE = re.compile(r"^##\s*(EVENT TEST|DATA TEST|ANYBODY TEST)", re.I | re.M)


def split_sections(text):
    """Return {section_name: body} using the three marker headings."""
    marks = [(m.group(1).upper(), m.start(), m.end())
             for m in SECTION_RE.finditer(text)]
    if len(marks) < 3:
        sys.exit(
            "PRECHECK ABORTED: the draft must contain the three marker lines\n"
            "  ## EVENT TEST\n  ## DATA TEST\n  ## ANYBODY TEST\n"
            f"(found {len(marks)})"
        )
    out = {}
    for i, (name, _s, e) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        out[name] = text[e:end]
    return out


def proper_nouns(body):
    """Capitalised runs, minus stopwords. Returns {display: normalised}."""
    found = {}
    for m in re.finditer(r"\b([A-Z][\w&.'’-]*(?:\s+[A-Z][\w&.'’-]*)*)", body):
        raw = m.group(1).strip()
        # ALL-CAPS runs longer than four words are the writer's own emphasis
        # (section labels, shouted findings), not names. Names are short.
        words = raw.split()
        if len(words) > 4 and all(w.isupper() for w in words if w.isalpha()):
            continue
        for piece in SPLIT_ON.split(raw):
            parts = piece.split()
            # trim stopwords at the EDGES only — stripping interior ones
            # ("BOOK OF PATENTS" -> "BOOK PATENTS") breaks the match
            while parts and parts[0].strip(".,;:") in STOPWORDS:
                parts.pop(0)
            while parts and parts[-1].strip(".,;:") in STOPWORDS:
                parts.pop()
            if not parts:
                continue
            tok = " ".join(parts).strip(".,;: ")
            if len(tok) < 3 or tok in STOPWORDS:
                continue
            found[tok] = re.sub(r"[^a-z0-9]", "", tok.lower())
    return found


def numbers(body):
    return {m.group(0): re.sub(r"[^0-9]", "", m.group(0))
            for m in re.finditer(r"\b\d[\d,./]*\b", body)}


def first_sentence(body):
    stripped = body.strip()
    m = re.search(r"(?<=[.!?])\s", stripped)
    return stripped[: m.start()] if m else stripped[:400]


def report(title, items):
    print("\n--- " + title + " (" + str(len(items)) + ") ---")
    if not items:
        print("  CLEAN")
    for it in items:
        print("  " + str(it))
    return len(items)


def main():
    # Windows consoles default to cp1252 and cannot print the marks this
    # file is built around (check mark, warning sign). Force UTF-8 output.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    if len(sys.argv) < 2:
        sys.exit("usage: python precheck.py <draft.md>")
    path = pathlib.Path(sys.argv[1])
    text = path.read_text(encoding="utf-8", errors="replace")
    sec = split_sections(text)
    table = sec["DATA TEST"]
    table_norm = re.sub(r"[^a-z0-9]", "", table.lower())
    table_nums = set(numbers(table).values())

    problems = 0
    for layer in ("EVENT TEST", "ANYBODY TEST"):
        body = sec[layer]
        missing = sorted(d for d, n in proper_nouns(body).items()
                         if n and n not in table_norm)
        problems += report(
            "DOWNWARD · proper nouns in " + layer + " with NO table row",
            missing)

        nums = sorted(d for d, n in numbers(body).items()
                      if n and n not in table_nums)
        problems += report(
            "DOWNWARD · numbers in " + layer + " not in the table", nums)

    prose = sec["EVENT TEST"] + sec["ANYBODY TEST"]
    low = prose.lower()

    problems += report("TRIGGERS · Compose Card #4",
                       sorted({t for t in TRIGGERS if t in low}))
    problems += report("RELATIONSHIP WORDS · anchor or delete",
                       sorted({w for w in RELATIONSHIP
                               if re.search(r"\b" + w + r"\b", low)}))

    opener = first_sentence(sec["ANYBODY TEST"])
    bad_open = sorted(d for d, n in proper_nouns(opener).items()
                      if n and n not in table_norm)
    problems += report("OPENING · locating tokens in the anybody test's first "
                       "sentence that are NOT in the table", bad_open)

    problems += report("CORPUS CLAIMS · each asserts a fact about THIS FILE — "
                       "answer with a grep run in the same action, or delete "
                       "(R51: two were false and reached the table)",
                       sorted({c for c in CORPUS_CLAIMS if c in low}))

    problems += report("VAGUE QUANTIFIERS · these ARE counts — replace with a "
                       "counted number or delete (R50: a couple was three)",
                       sorted({v.strip() for v in VAGUE_QUANTIFIERS
                               if v in low}))

    # r52 · THE HEADLINE IS A PROSE LAYER TOO. Everything before the first
    # section marker (the run's H1) must be carried by some test.
    head = text[: text.index("## ") if "## " in text else 0]
    tests_norm = re.sub(r"[^a-z0-9]", "",
                        (sec["EVENT TEST"] + sec["DATA TEST"]
                         + sec["ANYBODY TEST"]).lower())
    orphan_head = sorted(d for d, n in proper_nouns(head).items()
                         if n and n not in tests_norm)
    problems += report("HEADLINE · tokens in the run's title line that NO test "
                       "carries — the headline is a prose layer (r52: the "
                       "type-shelf mismatch was announced there and nowhere "
                       "else)", orphan_head)

    # r52 · every ⚠ Unresolved item names the row it bears on, or says none.
    um = re.search(r"⚠\s*Unresolved:?\**(.*?)(?=\n\s*\*\*|\n\s*\||\Z)", table,
                   re.S | re.I)
    orphan_items = []
    if um:
        for seg in um.group(1).split("·"):
            seg = " ".join(seg.split())
            if len(seg) < 25:
                continue
            if not re.search(r"\brows?\s*\d|\bno row\b|\bnot a row\b"
                             r"|\bactor-claims?\b|\bbears on none\b",
                             seg, re.I):
                orphan_items.append(seg[:110])
    problems += report("UNRESOLVED-ROW BINDING · each item must NAME the "
                       "row(s) it bears on, or say it bears on none — an "
                       "orphaned item disciplines no cell (r52)",
                       orphan_items)

    # r52 · CONVERSE OF THE ABOVE: a row an unresolved item names must
    # carry the doubt itself. A bare value in a cell IS a claim of settled.
    cited = set()
    if um:
        for m in re.finditer(r"\brows?\s*(\d+)(?:\s*[-\u2013,]|\s+and\s+)\s*(\d+)?",
                             um.group(1), re.I):
            lo = int(m.group(1))
            hi = int(m.group(2)) if m.group(2) else lo
            cited.update(range(lo, hi + 1))
        for m in re.finditer(r"\brows?\s*(\d+)", um.group(1), re.I):
            cited.add(int(m.group(1)))
    # r53: "\\bor\\b" alone passed a row on "legatee or devisee".
    # A branch is MARKED, not stumbled into.
    HEDGE = re.compile(r"\u26a0|unsettled|unresolved|unread|"
                       r"not stated|branch|, OR |\bOR\b", 0)
    unhedged = []
    for ln in table.splitlines():
        if not ln.strip().startswith("|") or "---" in ln:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not cells or not cells[0].isdigit():
            continue
        if int(cells[0]) in cited and not HEDGE.search(ln):
            unhedged.append("row %s carries no doubt though an unresolved "
                            "item cites it" % cells[0])
    problems += report("CITED-ROW HEDGE · a row named by an unresolved item "
                       "must carry the doubt IN THE ROW — a bare value is a "
                       "claim that the cell is SETTLED (r52)", unhedged)

    # r53 · DATE ARITHMETIC. Every stated interval is recomputed against the
    # dates present. A computed figure READS as verified, so a wrong one is
    # worse than none. ("eleven years and eleven months" was 10y 11m.)
    UNIT_D = {"day": 1, "week": 7, "month": 30.44, "year": 365.25}
    dates = set()
    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", text):
        dates.add(tuple(int(g) for g in m.groups()))
    spans = []
    if len(dates) >= 2:
        ds = sorted(dates)
        import datetime as _dt
        try:
            days = [( _dt.date(*a) - _dt.date(*b) ).days
                    for a in ds for b in ds if a > b]
        except ValueError:
            days = []
        spans = sorted({abs(d) for d in days})
    intervals = []
    for m in re.finditer(r"\b(\w+)\s+(year|month|week|day)s?\b"
                         r"(?:\s+and\s+(\w+)\s+(year|month|week|day)s?)?",
                         text, re.I):
        txt = m.group(0)
        if not re.search(r"\d|one|two|three|four|five|six|seven|eight|nine|"
                         r"ten|eleven|twelve", m.group(1), re.I):
            continue
        intervals.append(txt.strip())
    if intervals and spans:
        report("DATE ARITHMETIC \u00b7 recompute each stated interval against the "
               "dates in the draft; the real spans between dated events are "
               "%s days (advisory list, r53 delivered a false one)"
               % ", ".join(str(s) for s in spans[:6]),
               sorted(set(intervals)))

    cards = sorted({m.group(0) for m in re.finditer(
        r"\b(" + "|".join(CARDINAL_WORDS) + r")\b", low)})
    report("CARDINALS · license each with a count run in-action (advisory)",
           cards)

    ticks = [ln.strip()[:110] for ln in text.splitlines() if "✓" in ln]
    report("EARNED-tick · name the two witnesses for each, or downgrade to "
           "accepted-single-witness (advisory)", ticks)

    report("SUPERLATIVES · is each true of THIS instrument, and does every "
           "layer say the same thing about it? (advisory)",
           sorted({s for s in SUPERLATIVES if s in low}))

    # r53 login ruling \u2014 THREE BUDGETS, measured separately:
    #   EVENT   shrinks as the document stops surprising (analysis, not re-telling)
    #   DATA    grows with the number of data points \u2014 richness IS coverage
    #   ANYBODY does NOT grow. Complexity changes WHAT it says, not HOW MUCH.
    rows = [ln for ln in table.splitlines()
            if ln.strip().startswith("|") and "---" not in ln]
    rows = rows[1:] if rows else []
    ew = len(sec["EVENT TEST"].split())
    dw = len(sec["DATA TEST"].split())
    aw = len(sec["ANYBODY TEST"].split())
    print("\n--- THREE BUDGETS (r53 ruling) ---")
    print("  EVENT   %4d words   \u2014 should SHRINK run over run" % ew)
    print("  DATA    %4d words over %d rows \u2014 grows with the data points" %
          (dw, len(rows)))
    print("  ANYBODY %4d words   \u2014 CAPPED: the reader's budget, not the "
          "document's" % aw)
    print("  measured band r49-r52: anybody 272-311 words.")
    if aw > 315:
        problems += report(
            "ANYBODY TEST OVER BUDGET \u00b7 its whole point is to summarise the "
            "document's events so ANYBODY understands \u2014 complexity belongs "
            "in the DATA test, not in more summary words",
            ["%d words (band r49-r52 was 272-311)" % aw])

    hedged = bool(re.search(r"⚠|moderate|unresolved|could not|too faint",
                            prose))
    print("\n--- HEDGES survive into delivery ---")
    print("  " + ("PRESENT" if hedged else
                  "ABSENT — verify the record carries none"))

    print("\n" + "=" * 62)
    print("PRECHECK: %d finding(s) to resolve before delivery." % problems
          if problems else "PRECHECK: CLEAN — deliverable.")
    print("=" * 62)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
