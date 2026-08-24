"""
THE PRE-DELIVERY PASS — mechanical enforcement of the delivery rules.

WHY THIS EXISTS (measured, Grade Ledger 2026-08-24):
  Rule classes whose cure produced an ARTIFACT died (crop-files: clean
  3 straight runs; count-in-action: clean 2). Rule classes whose cure
  required VIGILANCE did not (narrative import: TEN members; layer-
  consistency: fired half at r48). This script converts the vigilance
  rules into a mechanical pass that either prints findings or prints
  CLEAN. Running it produces an artifact; remembering it does not.

USAGE
  1. Write the drafted delivery to a file BEFORE delivering it, with
     the three sections marked by these exact lines:
         ## EVENT TEST
         ## DATA TEST
         ## ANYBODY TEST
  2. python precheck.py <draft.md>
  3. Resolve every finding: either ADD THE ROW to the data test, or
     DELETE the claim from the prose. Then deliver.

WHAT IT CHECKS
  DOWNWARD   every proper noun and every number in the EVENT TEST and
             ANYBODY TEST must also appear in the DATA TEST. (r47: the
             officers lived only in prose; r48: Proclamation 7402, the
             Antiquities Act, the National Trust charter and the
             Rockefeller clause lived only in prose.)
  TRIGGERS   Compose Card #4 word list — motive, era-practice, scale
             and relationship words. (r47: "wanted to".)
  OPENING    the anybody test's FIRST sentence may locate the deal only
             with tokens that appear in the data test. (r42
             "Williamsburg", r46 "Prospect Heights", r48 "New York
             Harbor" / "old forts" — all in the same slot.)
  CARDINALS  every spelled-out or digit cardinal in prose is listed so
             each one can be licensed by a count run in-action.
             (Count class: 21, 23, 39, 42, 45, 46.)
  HEDGES     ⚠ / moderate / unresolved markers present in the record
             must survive into the delivery (Card #11).
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
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
    "Sunday",
    # instrument-structure words: they are grammar, not facts
    "WHEREAS", "NOW", "THEREFORE", "RESOLVED", "WITNESSETH", "IN", "WITNESS",
    "ACTOR", "CLAIMS", "Section", "Article", "Paragraph", "Jr", "Sr", "Esq",
    "LLC", "LLP", "Inc", "Corp", "LP", "Ltd", "Co",
    # uppercase forms of the function words above (emphasis styling)
    "THE", "THIS", "THAT", "AND", "OR", "OF", "TO", "FROM", "BY", "WITH",
    "AT", "ON", "FOR", "AS", "IS", "IT", "ITS", "NOT", "NO", "ONE", "TWO",
    "ALL", "EACH", "EVERY", "READ", "DERIVED", "INFERRED", "VALUE", "COST",
    "TITLE", "IDENTITY", "OCCUPANCY", "ENCUMBRANCE", "ENVELOPE",
    "ENTITLEMENT", "PERMIT", "ASBUILT", "CAPITAL", "PAGE", "ARITHMETIC",
    "EXECUTION", "SEQUENCE", "First", "Second", "Third", "Borough",
}

# Sentence-level noise: findings whose display form is only punctuation-
# joined fragments of a stopword (e.g. "Jr. National Trust") are re-split.
SPLIT_ON = re.compile(r"(?:^|\s)(?:Jr\.|Sr\.|Esq\.|Inc\.|Corp\.|LLC|LLP)\s*")

SECTION_RE = re.compile(r"^##\s*(EVENT TEST|DATA TEST|ANYBODY TEST)", re.I | re.M)


def split_sections(text):
    """Return {section_name: body} using the three marker headings."""
    marks = [(m.group(1).upper(), m.start(), m.end()) for m in SECTION_RE.finditer(text)]
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
    print(f"\n--- {title} ({len(items)}) ---")
    if not items:
        print("  CLEAN")
    for it in items:
        print(f"  {it}")
    return len(items)


def main():
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
        problems += report(f"DOWNWARD · proper nouns in {layer} with NO table row", missing)

        nums = sorted(d for d, n in numbers(body).items()
                      if n and n not in table_nums)
        problems += report(f"DOWNWARD · numbers in {layer} not in the table", nums)

    prose = sec["EVENT TEST"] + sec["ANYBODY TEST"]
    low = prose.lower()
    problems += report("TRIGGERS · Compose Card #4",
                       sorted({t for t in TRIGGERS if t in low}))
    problems += report("RELATIONSHIP WORDS · anchor or delete",
                       sorted({w for w in RELATIONSHIP
                               if re.search(rf"\b{w}\b", low)}))

    opener = first_sentence(sec["ANYBODY TEST"])
    bad_open = sorted(d for d, n in proper_nouns(opener).items()
                      if n and n not in table_norm)
    problems += report("OPENING · locating tokens in the anybody test's first "
                       "sentence that are NOT in the table", bad_open)

    cards = sorted({m.group(0) for m in re.finditer(
        r"\b(" + "|".join(CARDINAL_WORDS) + r")\b", low)})
    report("CARDINALS · license each with a count run in-action (advisory)", cards)

    # R49: absolute / uniqueness claims are where prose over-generalises and
    # where two layers end up asserting different things about one subject.
    # The pass cannot judge coherence — it can only surface the candidates.
    sups = sorted({s for s in SUPERLATIVES if s in low})
    report("SUPERLATIVES · absolute claims — is each true of THIS instrument, "
           "and does every layer say the same thing about it? (advisory)", sups)

    hedged = bool(re.search(r"⚠|moderate|unresolved|could not|too faint", prose))
    print(f"\n--- HEDGES survive into delivery --- \n  {'PRESENT' if hedged else 'ABSENT — verify the record carries none'}")

    print("\n" + "=" * 62)
    print(f"PRECHECK: {problems} finding(s) to resolve before delivery."
          if problems else "PRECHECK: CLEAN — deliverable.")
    print("=" * 62)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
