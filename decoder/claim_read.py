"""THE CLAIM READER — accepted text becomes evidence that matters.

    python claim_read.py                 # read all fused documents
    python claim_read.py --doc <id>      # one document
    python claim_read.py --show          # print the claims, not just counts
    python claim_read.py --open          # clauses that need reasoning, verbatim

⚠ THE FILTER IS *CHANGE*, NOT INTEREST. Charter p5: "If nothing changes, there is
no function and no event — change is what makes a function apply." The index
under-extracts (entities, never terms); the raw document over-extracts (recitals,
boilerplate, jurats). A clause earns a claim only if it changes a tracked
function. Everything else stays in the accepted text on disk, unpromoted and
unlost.

⚠ THIS IS NOT FUSION AND MUST NEVER BE MERGED INTO IT. fuse.py settles
CHARACTERS and deliberately does not reason: "mixing the two is how a
transcription defect becomes a semantic fact with provenance attached." This file
is the layer AFTER that, and the first place in the pipeline where meaning is
assigned.

⚠ EVERY CLAIM QUOTES, AND THE QUOTE IS VERIFIED MECHANICALLY. A claim carries a
span (page + character offsets) and the text at those offsets is re-read from the
evidence record and compared byte-for-byte. A fabricated claim fails on
arithmetic, not on judgement — no threshold, no confidence score. This is the
same defence the OCR channel provides against a VLM inventing section labels,
applied to meaning instead of characters.

⚠ REFUSAL IS FIRST-CLASS, AND IT IS *TWO* DIFFERENT ANSWERS:
    inert            — no tracked function changes here
    needs_reasoning  — something changes, no adopted rule can name it
Collapsing them destroys the growth path: the second is the signal that grows the
lexicon, and it is the only reason the candidate band is visible at all.

⚠ THE DETERMINISTIC TIER RUNS HERE; THE MODEL TIER IS A DECLARED HOLE. Clauses
that need reasoning are COUNTED and EXPORTED, never silently dropped, so the
absence of the model is a number on the report rather than an invisible gap.
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
OUT = HERE / "resolve" / "_claims"
VOCAB = HERE / "vocab" / "current.json"

# ── triggers: language that changes a tracked function ──────────────────────
TRIGGERS = {
    "ownership": [r"do(?:es)?\s+hereby\s+grant", r"grant,?\s+bargain",
                  r"sell\s+and\s+convey", r"remise,?\s+release", r"quitclaim"],
    "financing": [r"to\s+secure\s+the\s+payment", r"principal\s+sum\s+of",
                  r"releases?\s+and\s+discharges?", r"do(?:es)?\s+hereby\s+assign"],
    "envelope": [r"development\s+rights", r"floor\s+area\s+ratio",
                 r"unused\s+development", r"transferable\s+development",
                 r"zoning\s+lot"],
    "encumbrance": [r"subject\s+to", r"excepting\s+and\s+reserving",
                    r"together\s+with\s+all", r"easement",
                    r"covenants?\s+running\s+with"],
    "boundary": [r"\bthence\b", r"point\s+or\s+place\s+of\s+beginning",
                 r"feet\s+to\s+a\s+point"],
    "cover_page": [r"recording\s+and\s+endorsement", r"document\s+type:?",
                   r"mortgage\s+amount:?", r"fees\s+and\s+taxes", r"\bCRFN\b"],
}
TRIG = {f: [re.compile(p, re.I) for p in ps] for f, ps in TRIGGERS.items()}

# ── value extractors: each returns (kind, value, unit, start, end) ──────────
# ⚠ THE SPACE AFTER THE DOLLAR SIGN IS LOAD-BEARING. ACRIS's cover page renders
# "$ 50,000.00"; a pattern without \s* silently misses every printed amount, and
# money is the field most likely to be wrong while looking right.
MONEY = re.compile(r"\$\s*([\d,]+(?:\.\d{2})?)")
AREA = re.compile(r"([\d,]+(?:\.\d+)?)\s*(square\s+feet|sq\.?\s*ft\.?|BSF|SF)\b", re.I)
BBL = re.compile(r"Block\(?s?\)?[:\s]+(\d+)[,\s]+Lot\(?s?\)?[:\s]+(\d+)", re.I)
CRFN = re.compile(r"\b(20\d{10,})\b")
DATE = re.compile(r"\b(\d{2}-\d{2}-\d{4}|\d{1,2}(?:st|nd|rd|th)?\s+day\s+of\s+\w+)", re.I)

# Operative language with no trigger — something changes, nothing names it.
OPERATIVE = re.compile(
    r"\b(hereby|witnesseth|conveys?|conveyed|grants?|granted|reserves?|"
    r"assigns?|assigned|releases?|released|discharges?|encumbers?|"
    r"transfers?|transferred|warrants?|declares?)\b", re.I)

# ⚠ DO NOT BREAK CLAUSES AT A COLON. The first version split on [.;:\n], which
# severed "Mortgage Amount:" from "$ 50,000.00" — so the cover_page triggers
# (which all end in a colon) could never fire, and 2015022400608001 yielded ZERO
# claims while its cover page printed the amount in plain sight. Legal text uses
# the colon as an introducer ("WITNESSETH:"), not a clause boundary.
#
# ⚠ AND phrase_propose.py SPLIT DIFFERENTLY, WHICH IS HOW THIS HID. It used a
# lookbehind that KEPT the colon on the left chunk, so it reported 9 cover_page
# hits on the same text where this file found none. Two tools disagreeing about
# what a clause is will disagree about everything downstream.
CLAUSE = re.compile(r"[^.;\n]{25,}")


def load_vocab():
    if VOCAB.exists():
        v = json.loads(VOCAB.read_text(encoding="utf-8"))
        return v, {k: set(t) for k, t in v.get("terms", {}).items()}
    return {"version": 0}, {}


def read_doc(path):
    rec = json.loads(path.read_text(encoding="utf-8"))
    return rec.get("doc_id", path.stem), rec.get("pages") or []


def claims_for(doc, page, text):
    """Every claim this page supports, each with a verifiable span."""
    out, open_clauses, inert = [], [], 0
    for m in CLAUSE.finditer(text or ""):
        clause, base = m.group(0), m.start()
        fired = [f for f, pats in TRIG.items() if any(p.search(clause) for p in pats)]
        if not fired:
            if OPERATIVE.search(clause) or MONEY.search(clause):
                open_clauses.append((page, base, clause.strip()[:180]))
            else:
                inert += 1
            continue

        found = False
        for kind, rx, unit in (("consideration", MONEY, "USD"),
                               ("quantity_area", AREA, None),
                               ("crfn", CRFN, None),
                               ("date", DATE, None)):
            for v in rx.finditer(clause):
                found = True
                out.append({
                    "doc_id": doc, "page": page, "kind": kind,
                    "value": v.group(1),
                    "unit": (v.group(2) if kind == "quantity_area" else unit),
                    "functions": fired,
                    # ⚠ ABSOLUTE OFFSETS INTO accepted_text — this is what makes
                    # the claim checkable. Relative offsets verify against
                    # nothing.
                    "span": [base + v.start(), base + v.end()],
                    "quote": v.group(0),
                    "established_by": "lexicon",
                    "status": "resolved",
                })
        for v in BBL.finditer(clause):
            found = True
            out.append({
                "doc_id": doc, "page": page, "kind": "parcel",
                "value": f"block {v.group(1)} lot {v.group(2)}", "unit": None,
                "functions": fired, "span": [base + v.start(), base + v.end()],
                "quote": v.group(0), "established_by": "lexicon",
                "status": "resolved",
            })
        if not found:
            # ⚠ A TRIGGER FIRED AND NO RULE COULD NAME THE VALUE. This is the
            # single most informative state in the file — a function changes and
            # the deterministic tier cannot express it. Counted, exported, never
            # dropped.
            open_clauses.append((page, base, clause.strip()[:180]))
    return out, open_clauses, inert


def verify(claims, pages):
    """Re-read every span from the evidence record. Byte-for-byte or it fails."""
    by_page = {p.get("page"): (p.get("accepted_text") or "") for p in pages}
    ok = bad = 0
    for c in claims:
        t = by_page.get(c["page"], "")
        s, e = c["span"]
        if 0 <= s < e <= len(t) and t[s:e] == c["quote"]:
            ok += 1
        else:
            bad += 1
            c["status"] = "span_failed"
    return ok, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default=None)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--open", action="store_true")
    a = ap.parse_args()

    vocab, _ = load_vocab()
    OUT.mkdir(parents=True, exist_ok=True)
    docs = sorted(p for p in EVID.glob("*.json")
                  if not p.name.endswith((".escalate.json", ".located.json")))
    if a.doc:
        docs = [p for p in docs if p.stem == a.doc]

    print("CLAIM READER — accepted text -> evidence\n")
    print(f"  vocabulary v{vocab.get('version', 0)}"
          f"{'  ⚠ UNFROZEN — results are not reproducible' if not vocab.get('frozen_at') else ''}")
    print(f"  documents  {len(docs)}\n")
    if not docs:
        print("  NO FUSED EVIDENCE. This layer reads accepted text, never images.")
        return 1

    all_open, kinds, fn = [], collections.Counter(), collections.Counter()
    tot_c = tot_ok = tot_bad = tot_inert = 0
    for p in docs:
        doc, pages = read_doc(p)
        claims, opens, inert = [], [], 0
        for page in pages:
            c, o, i = claims_for(doc, page.get("page"), page.get("accepted_text"))
            claims += c
            opens += o
            inert += i
        ok, bad = verify(claims, pages)
        (OUT / f"{doc}.claims.jsonl").write_text(
            "".join(json.dumps(c) + "\n" for c in claims), encoding="utf-8")
        for c in claims:
            kinds[c["kind"]] += 1
            for f in c["functions"]:
                fn[f] += 1
        tot_c += len(claims); tot_ok += ok; tot_bad += bad; tot_inert += inert
        all_open += opens
        print(f"    {doc:<24} claims {len(claims):>4}   "
              f"span ok {ok:>4}  fail {bad:>2}   "
              f"needs reasoning {len(opens):>3}   inert {inert:>4}")
        if a.show:
            for c in claims[:8]:
                print(f"        {c['kind']:<15} {str(c['value'])[:22]:<23} "
                      f"{c['page']}:{c['span'][0]}  {'|'.join(c['functions'])}")

    print(f"\n  CLAIMS BY KIND")
    for k, v in kinds.most_common():
        print(f"    {k:<18} {v:>5}")
    print(f"\n  FUNCTIONS TOUCHED")
    for k, v in fn.most_common():
        print(f"    {k:<18} {v:>5}")

    # ⚠ SPAN VERIFICATION IS THE GUARDRAIL THAT DOES NOT DEPEND ON ANYTHING
    # BEHAVING. It must be 100% for the deterministic tier; anything less is a
    # bug in the reader, not a quality signal.
    rate = 100 * tot_ok / max(tot_c, 1)
    print(f"\n  SPAN VERIFICATION   {tot_ok:,}/{tot_c:,}  {rate:.1f}%"
          f"{'   ✅' if tot_bad == 0 else '   ⚠ FAILURES — READER BUG'}")

    print(f"\n  ⚠ NEEDS REASONING   {len(all_open):,} clauses")
    print("    A function changes and no adopted rule can name it. These are\n"
          "    the model tier, which is NOT wired here — so this is a declared\n"
          "    hole with a number on it, not a silent gap.")
    if a.open:
        for page, off, c in all_open[:30]:
            print(f"      {page}:{off:<6} {c}")
    (OUT / "_needs_reasoning.jsonl").write_text(
        "".join(json.dumps({"page": p, "offset": o, "clause": c}) + "\n"
                for p, o, c in all_open), encoding="utf-8")

    print(f"\n  inert (no function changes)  {tot_inert:,}")
    print(f"\n  claims -> {OUT.relative_to(HERE)}/<doc>.claims.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
