"""WHAT THE INSTRUMENT CALLS ITSELF — and whether it calls itself anything at all.

    from title_read import read_title
    python title_read.py            # A/B against the old reader, no re-OCR

⚠ THE OLD READER WAS FINDING REFERENCES, NOT TITLES. It searched the first 700
characters of the first body page for any phrase containing a title noun. What
that returns, measured on the census heads:

    DEED  ->  "DOES HEREBY GRANT AND RELEASE"   the granting clause
    PAT   ->  "THAT CERTAIN DEED"               the deed the POA acts on
    CERT  ->  "THE FOLLOWING MORTGAGE"          the mortgage being certified
    SAT   ->  "MORTGAGE"                        the mortgage being satisfied

Every one is a real phrase, correctly transcribed, and none is the document's
title. A power of attorney that mentions the deed it will be used for was scored
as a mis-filed deed. This is the same defect the exhibit reader had — "as shown
on Exhibit D" inside a recital counted as an exhibit — and the same fix applies:
ANCHOR TO POSITION. A title sits at the head of the page, before the instrument
starts speaking; a reference sits inside a sentence.

⚠ THREE STATES, NEVER TWO. "No title block" and "title disagrees with the filing
code" are different facts and they were collapsed into one number:

    titled_match     the instrument names itself, consistently with its code
    titled_mismatch  it names itself something else  <- the real mis-file signal
    untitled         it never names itself           <- a PROPERTY of the type

SAGE ("sundry agreement") and PAT are largely untitled by nature; reporting them
at 97% and 59% "mis-filed" measured this reader, not ACRIS. A rate computed over
documents that cannot support the measurement is worse than no rate, because it
looks like a finding.

⚠ AND A WASTEBASKET CODE IS A REAL RESULT. Where a type's documents DO name
themselves and the names are all different — SAGE returned a Hudson Yards
improvement-fund waiver, a city subsidy agreement, an assignment and a
certificate of no harassment — the type label carries no information about
content. That is worth knowing before anyone builds a reader for "SAGE".
"""
from __future__ import annotations

import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ⚠ THE TITLE ENDS WHERE THE INSTRUMENT STARTS SPEAKING. Every one of these
# openers marks the transition from heading to operative text, so the title (if
# there is one) is entirely before the first of them.
OPENER = re.compile(
    r"\bWITNESSETH\b|\bKNOW\s+ALL\s+(?:MEN|PERSONS)\b|\bTHIS\s+(?:INDENTURE|"
    r"AGREEMENT|DECLARATION|MORTGAGE|DEED|INSTRUMENT|ASSIGNMENT)\b|"
    r"\bWHEREAS\b|\bmade\s+(?:as\s+of|this|the)\b|\bdated\s+as\s+of\b|"
    r"\bBETWEEN\b|\bBY\s+THIS\b|\bIN\s+CONSIDERATION\b", re.I)

# ⚠ A PHRASE THAT OPENS LIKE THIS IS POINTING AT ANOTHER DOCUMENT, NOT NAMING
# THIS ONE. Each was observed producing a false title in the first census.
REFERENCE = re.compile(
    r"^\W*(?:THAT|THE\s+FOLLOWING|SAID|A\s+CERTAIN|THAT\s+CERTAIN|OF\s+THAT|"
    r"DOES?\s+HEREBY|DO\s+HEREBY|TO\s+SECURE|UNDER\s+THE|PURSUANT|"
    r"REFERENCE|RECORDED|ANNEXED|DESCRIBED)\b", re.I)

# The nouns an instrument uses to name itself.
NOUN = (r"DECLARATION|AGREEMENT|DEED|EASEMENT|COVENANT|RESTRICTIONS?|"
        r"CERTIFICATE|WAIVER|LEASE|ASSIGNMENT|SATISFACTION|MODIFICATION|"
        r"CONSENT|SUBORDINATION|AMENDMENT|MEMORANDUM|MORTGAGE|RELEASE|"
        r"POWER\s*OF\s*ATTORNEY|AFFIDAVIT|CONTRACT|NOTICE|LIEN|INDENTURE|"
        r"TERMINATION|GUARANTY|ESTOPPEL|SPREADER|CONSOLIDATION")
# ⚠ FLAT AND BOUNDED, NOT NESTED. The first version read
#     (?:[A-Z][A-Za-z&/\-']*\s*){0,6}(?:NOUN)...
# a quantified group containing quantifiers, which on glued OCR text
# ("SATISFACTIONOFMORTGAGEKNOWALLMEN...") backtracks catastrophically: MEASURED
# at 3.64s for ONE call against 0.00s for the flat form. Across 1,698 documents
# and two patterns that is ~2 hours, and it presented as the job "hanging" with
# no error — twice killed before printing a line. A regex that is correct and
# exponential is a bug, not a slow path.
TITLE = re.compile(
    r"([A-Z][A-Za-z&/\-' ]{0,58}?(?:" + NOUN + r")"
    r"(?:\s{0,2}(?:OF|AND|FOR|TO)\s{0,2}[A-Za-z&/\-' ]{0,40}?)?)")

# ⚠ THE HEAD OF THE PAGE, NOT THE PAGE. 300 characters is roughly the heading
# block plus a line of the opening; beyond that every hit is body prose. The old
# reader used 700 and that is where the granting clauses came from.
HEAD = 300
MAXLEN = 78     # a title is a line; longer than this and it is a sentence


def read_title(text):
    """(title, state) — state is 'titled' or 'untitled'. Never guesses."""
    t = " ".join((text or "").split())
    if not t:
        return None, "untitled"
    # cut at the point the instrument starts speaking
    m = OPENER.search(t[:HEAD * 2])
    head = t[:m.start()] if m and m.start() > 4 else t[:HEAD]
    head = head[:HEAD]
    best = None
    for c in TITLE.finditer(head):
        v = " ".join(c.group(1).split()).strip(" ,.:;-")
        if len(v) < 5 or len(v) > MAXLEN:
            continue
        # a phrase pointing at ANOTHER instrument is not this one's name
        if REFERENCE.search(head[max(0, c.start() - 22):c.end()]):
            continue
        v = re.sub(r"^(?:THIS|THE|A)\s+", "", v, flags=re.I).strip()
        if len(v) < 5:
            continue
        # earliest qualifying candidate wins — a title precedes everything
        if best is None or c.start() < best[1]:
            best = (v.upper(), c.start())
    return (best[0], "titled") if best else (None, "untitled")


def agrees(title, type_description):
    """Does the self-title match the filing code's own description?

    ⚠ COMPARED ON SHARED NOUNS, NOT ON PREFIXES. The old check tested whether
    the description's first 6 or 9 characters appeared in the title, so
    "SATISFACTION OF MORTGAGE" vs description "SATISFACTION OF MORTGAGE" passed
    while "BARGAIN AND SALE DEED" vs "DEED" also had to pass on a 4-character
    prefix — the test was doing two different jobs badly.
    """
    if not title or not type_description:
        return None
    tw = set(re.findall(r"[A-Z]{4,}", title.upper()))
    dw = set(re.findall(r"[A-Z]{4,}", type_description.upper()))
    # OCR eats spaces: "SATISFACTIONOFMORTGAGE" has no word boundaries at all
    glued = re.sub(r"[^A-Z]", "", title.upper())
    if not dw:
        return None
    if tw & dw:
        return True
    return any(w in glued for w in dw if len(w) >= 4)


if __name__ == "__main__":
    import collections
    import json
    import pathlib
    import bulk

    HERE = pathlib.Path(__file__).parent
    COVER = re.compile(r"RECORDING\s*AND\s*ENDORSEMENT|NYC\s*DEPARTMENT\s*OF\s*FINANCE", re.I)
    # the OLD reader, reproduced flat so the A/B measures BEHAVIOUR not runtime
    OLD_TITLE = re.compile(
        r"([A-Za-z][A-Za-z ]{0,48}?(?:" + NOUN + r")"
        r"(?:\s{0,2}(?:OF|AND|FOR)\s{0,2}[A-Za-z ]{0,34}?)?)", re.I)

    recs = {}
    for d in ("census_head", "devr_head"):
        p = HERE / d
        if p.exists():
            for f in p.glob("*.json"):
                recs[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    codes = json.loads((HERE / "_doctype_codes.json").read_text(encoding="utf-8"))
    # ⚠ CACHED. Re-querying 1,698 document ids on every run made the A/B
    # itself the slowest part of the loop and it was killed twice before
    # printing anything. The map does not change between runs.
    cache = HERE / "_doctype_of.json"
    ty = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    missing = [d for d in sorted(recs) if d not in ty]
    if missing:
        for r in bulk.socrata_in("bnx9-e6tj", "document_id", missing,
                                 select="document_id,doc_type"):
            ty[r["document_id"]] = (r.get("doc_type") or "").strip()
        cache.write_text(json.dumps(ty), encoding="utf-8")
    print(f"  type map: {len(ty)} documents ({len(missing)} fetched)", flush=True)

    def body_text(rec):
        for p in rec.get("pages") or []:
            t = " ".join((p.get("accepted_text") or "").split())
            if t and not COVER.search(t[:200]):
                return t
        return ""

    stats = collections.defaultdict(lambda: collections.Counter())
    examples = collections.defaultdict(list)
    for doc, rec in recs.items():
        t = ty.get(doc)
        if not t:
            continue
        txt = body_text(rec)
        desc = (codes.get(t, {}).get("doc__type_description") or "")
        new, state = read_title(txt)
        om = OLD_TITLE.search(txt[:700])
        old = " ".join(om.group(1).split()).upper().strip(" ,.") if om else None
        old = old if old and len(old) > 6 else None
        s = stats[t]
        s["n"] += 1
        s["old_titled"] += bool(old)
        if old and not agrees(old, desc):
            s["old_mismatch"] += 1
        if state == "titled":
            s["new_titled"] += 1
            if agrees(new, desc):
                s["new_match"] += 1
            else:
                s["new_mismatch"] += 1
                if len(examples[t]) < 3:
                    examples[t].append(new)
        else:
            s["untitled"] += 1

    print("TITLE READER — old vs new, same documents, no re-OCR\n")
    print(f"  {'TYPE':<9}{'n':>5}   {'OLD mis%':>9}{'NEW mis%':>9}"
          f"{'untitled%':>11}   {'what changed'}")
    print("  " + "-" * 74)
    for t in sorted(stats, key=lambda k: -stats[k]["n"]):
        s = stats[t]
        oldp = 100 * s["old_mismatch"] // max(s["old_titled"], 1)
        newp = 100 * s["new_mismatch"] // max(s["new_titled"], 1)
        unt = 100 * s["untitled"] // s["n"]
        note = ""
        if s["new_titled"] and newp < oldp - 10:
            note = f"references rejected ({oldp}% was the reader)"
        elif unt > 45:
            note = "largely UNTITLED by nature — no rate is meaningful"
        print(f"  {t:<9}{s['n']:>5}   {oldp:>8}%{newp:>8}%{unt:>10}%   {note}")

    print("\n  remaining NEW mismatches (a genuine self-title that disagrees):")
    for t in sorted(examples, key=lambda k: -stats[k]["n"])[:8]:
        print(f"    {t:<9}{' | '.join(examples[t])[:88]}")
