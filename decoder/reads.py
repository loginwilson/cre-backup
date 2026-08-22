"""THE READ LOG — which pages were OPENED, independent of what they yielded.

⚠ THE MODELLING GAP THIS FILLS, AND IT CAUSED THE WORST ERROR OF THE SESSION.

claims.py records a page only when that page produced a fact. So the corpus
had no way to distinguish:

    a page read carefully that contained nothing        <- work done, no fact
    a page never opened                                 <- work not done

Both look like silence. And silence is what let "X is not among the documents
I was given" get promoted into "X is not in the corpus" — six times, about
instruments that were sitting on disk the whole time.

⚠ A NEGATIVE RESULT IS A RESULT. Four 2011 assignments, 29 pages, all read,
zero facts — that is not a gap, it is a finding: the servicing transfers carry
no substantive terms. Without a read log I cannot tell that apart from never
having looked, and I will send an agent to read them again.

So: three states per page, never two.

    OPENED + YIELDED   a claim cites it
    OPENED + EMPTY     read, nothing of substance. ⚠ THIS IS COVERAGE.
    NOT OPENED         ⚠ the only real gap

Populated from what the reading agents reported about their own scope. That
is legitimate here — an agent's page list is evidence about what the agent
did, which is exactly what this table records. It is NOT evidence about what
exists, which is what I wrongly used it for.
"""
import re

# doc_id -> page spec of what was OPENED. "1-39" means p001..p039.
# ⚠ TRANSCRIBED FROM AGENT REPORTS. Where an agent said "all N pages" I use
# the full range; where it enumerated, I use the enumeration; where it said
# NOT_QUOTABLE I EXCLUDE those pages, because paging past an image is not
# reading it.
OPENED = {
    # ---- microfilm era, 100/100 reported ----
    "FT_1320008495632": "1-2",
    "FT_1330008495633": "1-3",
    "FT_1980000345898": "1-26",
    "FT_1990000345899": "1-11",
    "FT_1570006671557": "1-3",
    "FT_1710006669171": "1-9",
    "FT_1370006667337": "1-13",
    "FT_1730006667273": "1-7",
    "FT_1810006667281": "1-4",
    "FT_1260006667226": "1-2",
    "2003110900238001": "1-20",
    # ---- 2007 acquisition, 87/87 reported ----
    "2007062101109001": "1-5",
    "2007062101109002": "1",
    "2007062101109003": "1-5",
    "2007062101109004": "1-15",
    "2007062101109005": "1-41",
    "2007062101109006": "1-20",
    # ---- 2010 batch ----
    "2010102601040002": "1-8",
    "2010102601040003": "1-18",
    "2010102601040004": "1-9",
    "2010102601040005": "1-8",
    "2010110900202001": "1-2",
    "2009122400274001": "1",
    "2014080700619001": "1-8",
    # ---- 2011 servicing chain: read in full, ZERO facts. coverage, not gap.
    "2011112200806001": "1-8",
    "2011112200841001": "1-8",
    "2011112200888001": "1-6",
    "2011112200913001": "1-7",
    # ---- 2012 UBS, 110/110 reported ----
    "2012101500666006": "1-39",
    "2012101500666007": "1-49",
    "2012101500666008": "1-22",
    # ---- 2013 merger set, 122/122 reported ----
    "2013052101674001": "1-10",
    "2013052101674002": "1-14",
    "2013052101674003": "1-24",
    "2013052101674005": "1-10",
    "2013052101674006": "1-10",
    "2013052101674007": "1-25",
    # ---- 2013 Goldman ----
    "2013081200922001": "1-14",
    "2013081200922002": "1-15",
    "2013081200922003": "1-61",
    "2013081200922004": "1-11,13,14,17-21",   # 12,15,16 NOT_QUOTABLE
    "2013081200922005": "1,3,4",              # 2,5,6 NOT_QUOTABLE
    # ---- 2014 ----
    "2014112601161001": "1,3,4",
    "2014112601161002": "1-6",
    "2014112601161003": "1,3-7",
    "2014112601161004": "1-8",
    "2014112601161005": "1-32",
    "2014112601161006": "1-30",
    # ---- 2015 construction ----
    "2015091001439001": "1-5",
    "2015091001439002": "1-19,22",
    "2015091001439003": "1-28,30-35",
    "2015091001439004": "1,2,3,5,8,14,16,34",
    "2015091001439005": "1-6,16,17",
    # ---- 2019 / 2020 ----
    "2019071700601001": "1-12",
    "2019071700601002": "1-20",
    "2020061600455001": "1-19",
    "2020081400407002": "1-14",
    # ---- 2023 / 2025 ----
    "2023110100486003": "1-4",
    "2023110100486004": "1-4",
    "2023110100486006": "1-9",
    "2023110100486011": "1-20",
    "2025101700864001": "1-5",
    "2025101700864002": "1-11",
    # ---- recorded after the final six agents reported. ⚠ THESE WERE
    # READ HOURS BEFORE THIS LINE EXISTED. The read log was hand-
    # populated from agent reports, so it lagged the actual reading and
    # the ledger showed 43 documents "unread" that had been read in
    # full. ⚠ A LOG THAT LAGS ITS OWN SUBJECT REPORTS FALSE GAPS, which
    # is the same failure as a summary that lags its data.
    "2010102601040006": "1-110",
    "2012101500666002": "1-6",
    "2012101500666003": "1-7",
    "2012101500666004": "1-7",
    "2012101500666005": "1-7",
    "2012122701550001": "1-10",
    "2012122701550002": "1-18",
    "2012122701550003": "1-55",
    "2012122701550004": "1-12",
    "2013052101674004": "1-45",
    "2013052101674008": "1-41",
    "2013080901116002": "1-40",
    "2014040900899002": "1",
    "2015043000681001": "1-8",
    "2015051301826001": "1-3",
    "2015052900388001": "1-4",
    "2015101301338001": "1-10",
    "2016060801066001": "1-9",
    "2018113000347001": "1-20",
    "2019071700601003": "1-44",
    "2020081400407001": "1-38",
    "2023102700777001": "1-13",
    "2023110100486005": "1-13",
    "2023110100486009": "1-10",
    "2023110100486010": "1-45",
    "2025101700864004": "1-52",
    "2025101700864005": "1-28",
    "2026052800492001": "1-3",
    "2026062301264001": "1",
    "FT_1340008617134": "1",
    "FT_1670008616267": "1",
}


def expand(spec):
    out = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(\d+)-(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            out.update(range(a, b + 1))
        elif part.isdigit():
            out.add(int(part))
    return out


def pages_opened(doc_id):
    """Set of 1-based page numbers opened for this document."""
    return expand(OPENED.get(doc_id, ""))


def summary():
    return {d: len(expand(s)) for d, s in OPENED.items()}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    s = summary()
    print(f"READ LOG · {len(s)} documents · {sum(s.values())} pages opened")
