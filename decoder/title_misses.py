"""WHY DOES TITLE MISS 27 OF 50 DEEDS? The oldest unexplained gap in the ledger.

    python title_misses.py

⚠ WHY THIS MATTERS MORE THAN ANY OTHER READER GAP. TITLE is the second-highest-volume
function in ACRIS and the ledger records it as `weak — 46% of 50 deeds, misses
unexplained`. Every other weak reader has a stated reason (IDENTITY fires on 45% of CERTs;
`signals` has no corpus). This one just says "unexplained", which means nobody has looked.

⚠ AND A FUNCTION READER IS NOT A KEYWORD SEARCH — IT LOOKS FOR THE OPERATIVE CLAUSE.
An instrument is mostly recital, covenant and boilerplate; exactly one clause DOES the
thing. The mode ledger measured this: `transacts` cues are 95-100% OPERATIVE across 23,282
clauses. So a miss means one of three things, and they need different fixes:

    VOCABULARY   the deed conveys with words the pattern list does not know
    LOCATION     the clause exists but sits on a page the reader never saw
    TRANSCRIPTION the words are there and OCR mangled them

This separates those three rather than reporting one number.

⚠ TEXT ONLY. No image, no VLM, no server. The question is about vocabulary, and pulling a
model into it would add a variable instead of removing one.
"""
from __future__ import annotations

import collections, gzip, json, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import lexicon as L

TITLE = [re.compile(p, re.I) for p in L.FUNCTIONS["title"]["patterns"]]

# ⚠ CANDIDATE VOCABULARY IS PROPOSED, NEVER ADOPTED HERE. These are counted on the
# MISSES so we can see what they would buy — and counted on the HITS and on
# NON-DEEDS too, because a pattern that fires everywhere manufactures a function.
# "subject to" was already removed from encumbrance for exactly that reason.
CANDIDATE = {
    "grant and release": r"grant\w*\s+and\s+release",
    "bargain and sale": r"bargain\s+and\s+sale",
    "party of the first part": r"part(?:y|ies)\s+of\s+the\s+first\s+part",
    "hereby grants": r"hereby\s+grant",
    "convey": r"\bconvey\w*\b",
    "release and quitclaim": r"release\w*\s+and\s+quitclaim",
    "all right title and interest": r"all\s+right,?\s+title\s+and\s+interest",
    "fee simple": r"fee\s+simple",
    "unto the": r"\bunto\s+the\b",
    "seized/seised": r"sei[sz]ed",
    "premises herein granted": r"premises\s+herein\s+granted",
    "TO HAVE AND TO HOLD": r"to\s+have\s+and\s+to\s+hold",
    "witnesseth": r"witnesseth",
    "in consideration of": r"in\s+consideration\s+of",
    "grantor/grantee": r"\bgrant(?:or|ee)\b",
    "deed": r"\bdeed\b",
}
CAND = {k: re.compile(v, re.I) for k, v in CANDIDATE.items()}


def text_of(doc):
    p = HERE / "sample_ocr" / f"{doc}.json.gz"
    if not p.exists():
        return None, 0
    pages = json.loads(gzip.open(p, "rt", encoding="utf-8").read())
    return " ".join(str(pg.get("text") or "") for pg in pages), len(pages)


def main():
    types = json.loads((HERE / "_doctype_of.json").read_text(encoding="utf-8"))
    deeds = sorted(d for d, t in types.items() if str(t).upper() == "DEED")
    others = [(d, str(t).upper()) for d, t in types.items()
              if str(t).upper() not in ("DEED",)]

    have, hit, miss = [], [], []
    for d in deeds:
        txt, npg = text_of(d)
        if txt is None:
            continue
        have.append(d)
        (hit if any(p.search(txt) for p in TITLE) else miss).append((d, txt, npg))

    # ⚠ DENOMINATORS. "46%" means nothing without how many had text at all.
    print(f"  DEED documents in the registry : {len(deeds)}")
    print(f"  with OCR text on disk          : {len(have)}   <- the real denominator")
    print(f"  TITLE fires                    : {len(hit)}  ({len(hit)/max(1,len(have)):.0%})")
    print(f"  TITLE misses                   : {len(miss)}\n")

    # which of the six existing patterns actually carries the hits
    print("  ── which existing pattern earns its place ──")
    for p in TITLE:
        n = sum(1 for _d, t, _n in hit if p.search(t))
        print(f"     {p.pattern[:44]:<46} {n:>3} of {len(hit)} hits")

    # what the MISSES say instead
    print(f"\n  ── candidate vocabulary: fires on MISSES vs HITS vs NON-DEEDS ──")
    print(f"     {'phrase':<28}{'miss':>6}{'hit':>6}{'other':>7}   verdict")
    other_txt = []
    for d, t in others[:220]:                    # bounded: this is a specificity check
        tx, _ = text_of(d)
        if tx:
            other_txt.append((d, t, tx))
    rows = []
    for name, rx in CAND.items():
        m = sum(1 for _d, t, _n in miss if rx.search(t))
        h = sum(1 for _d, t, _n in hit if rx.search(t))
        o = sum(1 for _d, _t, tx in other_txt if rx.search(tx))
        rows.append((m, name, h, o))
    for m, name, h, o in sorted(rows, reverse=True):
        orate = o / max(1, len(other_txt))
        # ⚠ A PATTERN THAT FIRES ON EVERYTHING MANUFACTURES A FUNCTION.
        verdict = ("ADD — recovers misses, specific" if m >= 3 and orate < 0.25 else
                   "too broad" if orate >= 0.25 else
                   "weak recovery" if m else "no help")
        print(f"     {name:<28}{m:>6}{h:>6}{o:>7}   {verdict}")
    print(f"     (non-deed sample = {len(other_txt)} documents)")

    # LOCATION vs VOCABULARY vs TRANSCRIPTION on the misses
    print(f"\n  ── what KIND of miss is each one? ──")
    kinds = collections.Counter()
    for d, t, npg in miss:
        low = t.lower()
        anycand = any(rx.search(t) for n, rx in CAND.items()
                      if n not in ("deed", "grantor/grantee", "witnesseth"))
        kinds["vocabulary — conveys with words we do not know" if anycand else
              "no conveyance language at all" if "convey" not in low and
              "grant" not in low else "garbled/partial"] += 1
    for k, v in kinds.most_common():
        print(f"     {v:>3}  {k}")

    print(f"\n  ── the misses, with what they actually say ──")
    for d, t, npg in miss[:12]:
        found = [n for n, rx in CAND.items() if rx.search(t)]
        m = re.search(r".{0,60}(convey\w*|grant\w*|release\w*).{0,80}", t, re.I)
        print(f"     {d}  {npg:>3}pg  cues={found[:5]}")
        if m:
            print(f"        …{m.group(0).strip()[:132]}…")
    json.dump({"denominator": len(have), "hits": len(hit), "misses": len(miss),
               "miss_ids": [d for d, _t, _n in miss]},
              open(HERE / "_title_misses.json", "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
