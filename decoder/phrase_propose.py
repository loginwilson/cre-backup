"""THE PHRASE LEXICON PROPOSAL LOOP — learning what language MEANS something.

    python phrase_propose.py                 # propose, with the denominator
    python phrase_propose.py --review        # candidates with their passages
    python phrase_propose.py --inert         # show what was skipped (audit it)

⚠ THE MIDDLE GROUND BETWEEN THE INDEX AND THE WHOLE DOCUMENT IS *CHARGE*, AND THE
TEST IS THE CHARTER'S OWN: "If nothing changes, there is no function and no
event — change is what makes a function apply." So a passage earns a claim only
if it CHANGES a tracked function. The index under-extracts (entities, no terms);
the raw document over-extracts (recitals, boilerplate, jurats). Operative
language is the seam between them.

⚠ TWO VOCABULARIES, NOT ONE.
  · CONTROLLED TERMS — action/function/role/effect. Shared across all 95 doc
    types, small, grows only by necessity. That is `vocab_propose.py`.
  · TRIGGER PHRASES — per document type, large, learned. THIS FILE.
The phrase lexicon IS the per-type reading strategy, and it is why one shared
event schema can absorb 95 document types without 95 schemas: the terms stay
constant while the phrasing that triggers them is learned per type.

⚠ SELECTIVE AT THE CLAIM LAYER, LOSSLESS AT THE TEXT LAYER. The full accepted
text stays on disk regardless, so a phrase nobody knew mattered can be re-mined
later with no re-acquisition and no re-reading of images. That is what makes it
safe to be aggressive about what becomes a claim.

⚠ OVER-FILTERING IS INVISIBLE, WHICH IS WHY THIS PRINTS ITS DENOMINATOR. If
claims only ever come from phrases the lexicon already knows, what was missed
looks exactly like a document that had nothing to say — the same coverage-wearing-
a-quality-mask failure that has cost this project the most. So every run reports
clauses TOTAL, matched, candidate and inert, and `--inert` exists so the skipped
material can actually be read rather than trusted.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
EVID = HERE / "resolve" / "_evidence"
LEX = HERE / "vocab" / "phrases.json"
CAND = HERE / "vocab" / "_phrase_candidates.json"

# ⚠ SEEDS ARE A STARTING POINT, NOT THE LEXICON. Each maps operative language to
# the function it changes. They are deliberately few: the loop is supposed to
# LEARN the rest from documents, and a fat hand-written seed list would hide how
# little is being discovered.
SEEDS = {
    "ownership": [r"do(?:es)?\s+hereby\s+grant", r"grant,?\s+bargain",
                  r"sell\s+and\s+convey", r"remise,?\s+release",
                  r"quitclaim"],
    "financing": [r"to\s+secure\s+the\s+payment", r"witnesseth,?\s+that\s+to\s+secure",
                  r"principal\s+sum\s+of", r"releases?\s+and\s+discharges?",
                  r"do(?:es)?\s+hereby\s+assign"],
    "envelope":  [r"development\s+rights", r"floor\s+area\s+ratio",
                  r"unused\s+development", r"zoning\s+lot",
                  r"transferable\s+development"],
    "encumbrance": [r"subject\s+to", r"excepting\s+and\s+reserving",
                    r"together\s+with\s+all", r"easement",
                    r"covenants?\s+running\s+with"],
    "execution": [r"\bby[:,]?\s+[A-Z][a-z]+\s+[A-Z]", r"its\s+managing\s+member",
                  r"authorized\s+signator"],
    # ⚠ ADDED AFTER THE FIRST INERT AUDIT, 2026-08-14. Both were being discarded
    # entirely, and both are load-bearing.
    #
    # BOUNDARY: the metes description ("RUNNING THENCE westerly ... 115.00 feet
    # to a point") has NO operative verb and NO dollar sign, so it fell through
    # to inert. It is the one thing the index cannot supply in any form, and
    # envelope and easement work both depend on it.
    "boundary": [r"\bthence\b", r"point\s+or\s+place\s+of\s+beginning",
                 r"feet\s+to\s+a\s+point", r"tax\s+map\s+of\s+the\s+borough"],
    # COVER_PAGE: ACRIS's own recording cover, not the instrument. It carries
    # the RPTT/RETT stamps — which is where a DEVR price actually lives, since
    # `document_amt` is 0 for every one of them. Discarding this page discards
    # the money.
    "cover_page": [r"recording\s+and\s+endorsement", r"document\s+type:",
                   r"mortgage\s+amount:", r"fees\s+and\s+taxes",
                   r"\bCRFN\b", r"block\(s\)", r"lot\(s\)"],
}

# A clause with one of these is doing something legally, even when no seed
# matches — so it is a CANDIDATE for review rather than inert. This is the
# discovery half.
OPERATIVE = re.compile(
    r"\b(hereby|shall|witnesseth|conveys?|conveyed|grants?|granted|reserves?|"
    r"reserved|assigns?|assigned|releases?|released|discharges?|discharged|"
    r"encumbers?|transfers?|transferred|covenants?|warrants?|declares?)\b", re.I)

# ⚠ THE SPACE AFTER THE DOLLAR SIGN WAS A REAL BUG. `\$[\d,]+` does not match
# "$ 50,000.00", and that is exactly how ACRIS's cover page renders an amount —
# so every cover-page figure was scored inert on the first run. Money is the
# field most likely to be silently wrong (document_amt is 0 for every DEVR), so
# a regex that quietly misses the printed amount is the worst possible defect
# here. Measured on 2015022400608001 p001.
QUANTITY = re.compile(
    r"(\$\s*[\d,]+(?:\.\d{2})?"
    r"|\b[\d,]{3,}(?:\.\d+)?\s*(?:square\s+feet|sq\.?\s*ft|SF|BSF)\b"
    r"|\b\d[\d,]*\.?\d*\s*feet\b)", re.I)
SPLIT = re.compile(r"(?<=[.;:])\s+|\n+")


def clauses(text):
    for c in SPLIT.split(text or ""):
        c = " ".join(c.split())
        if len(c) >= 25:
            yield c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--inert", action="store_true")
    a = ap.parse_args()

    LEX.parent.mkdir(exist_ok=True)
    lex = json.loads(LEX.read_text(encoding="utf-8")) if LEX.exists() else {}
    seeds = {f: [re.compile(p, re.I) for p in ps] for f, ps in SEEDS.items()}

    docs = sorted(p for p in EVID.glob("*.json")
                  if not p.name.endswith((".escalate.json", ".located.json")))
    print("PHRASE LEXICON PROPOSAL LOOP\n")
    print(f"  adopted phrases  {sum(len(v) for v in lex.values()) if lex else 0}")
    print(f"  documents        {len(docs)}   <- resolve/_evidence/\n")
    if not docs:
        print("  NO FUSED EVIDENCE. This loop reads accepted text; it cannot\n"
              "  read images. Extraction must run first.")
        return 1

    tot = matched = cand = inert = 0
    hits = collections.defaultdict(list)
    cands = collections.defaultdict(list)
    inerts = []
    per_doc = {}

    for p in docs:
        rec = json.loads(p.read_text(encoding="utf-8"))
        doc = rec.get("doc_id", p.stem)
        d_tot = d_m = 0
        for page in rec.get("pages") or []:
            pg = page.get("page")
            for c in clauses(page.get("accepted_text")):
                tot += 1
                d_tot += 1
                fired = [f for f, pats in seeds.items()
                         if any(x.search(c) for x in pats)]
                if fired:
                    matched += 1
                    d_m += 1
                    for f in fired:
                        hits[f].append((doc, pg, c[:150]))
                elif OPERATIVE.search(c) or QUANTITY.search(c):
                    # ⚠ THIS IS THE DISCOVERY HALF. Operative language or a
                    # quantity, with NO seed matching, is exactly where the
                    # lexicon is thin — the phrasing nobody has taught it yet.
                    cand += 1
                    key = (OPERATIVE.search(c) or QUANTITY.search(c)).group(0).lower()
                    cands[key].append((doc, pg, c[:150]))
                else:
                    inert += 1
                    if len(inerts) < 400:
                        inerts.append((doc, pg, c[:110]))
        per_doc[doc] = (d_m, d_tot)

    print("  SEEDED HITS — language already known to change a function")
    for f in SEEDS:
        n = len(hits.get(f, []))
        print(f"    {f:<14} {n:>5}")
        if a.review:
            for doc, pg, c in hits[f][:4]:
                print(f"        {doc}:{pg}  {c}")

    print(f"\n  ⚠ CANDIDATES — operative or quantitative, NO seed matched "
          f"({cand:,} clauses, {len(cands)} distinct markers)")
    for key, ex in sorted(cands.items(), key=lambda x: -len(x[1]))[:14]:
        print(f"    {key:<16} x{len(ex):<5} {ex[0][0]}:{ex[0][1]}")
        if a.review:
            for doc, pg, c in ex[:3]:
                print(f"        {c}")

    CAND.write_text(json.dumps(
        {k: [{"doc": d, "page": p, "clause": c} for d, p, c in v[:8]]
         for k, v in cands.items()}, indent=1), encoding="utf-8")

    # ⚠ THE DENOMINATOR IS THE POINT OF THIS BLOCK. "We found 62 operative
    # clauses" means nothing without what it was 62 OF.
    print(f"\n  COVERAGE — the denominator, printed on purpose")
    print(f"    clauses total      {tot:>7,}")
    print(f"    seeded match       {matched:>7,}  {100*matched/max(tot,1):>5.1f}%")
    print(f"    candidate          {cand:>7,}  {100*cand/max(tot,1):>5.1f}%   <- lexicon is thin here")
    print(f"    inert              {inert:>7,}  {100*inert/max(tot,1):>5.1f}%")
    print(f"\n  per document (matched/total):")
    for d, (m, t) in per_doc.items():
        print(f"    {d:<24} {m:>4}/{t:<6} {100*m/max(t,1):>5.1f}%")

    if a.inert:
        print(f"\n  INERT SAMPLE — ⚠ READ THIS, DO NOT TRUST IT. Anything here "
              f"that changes a function is a lexicon MISS:")
        for doc, pg, c in inerts[:40]:
            print(f"    {doc}:{pg}  {c}")

    print(f"\n  candidates -> {CAND.relative_to(HERE)}")
    print("  ⚠ Nothing is adopted automatically. A phrase enters the lexicon\n"
          "    only when it changes a tracked function and no adopted phrase\n"
          "    already carries that meaning.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
