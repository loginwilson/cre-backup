"""CANONICAL TEXT -> CLAIMS -> EVENTS. The first half of the resolver.

    python claims.py                      # all keyed documents, best engine
    python claims.py --engine ppv6-rot

⚠ THE PATTERNS HERE ARE A PLACEHOLDER FOR A MODEL, AND SAYING SO IS THE POINT.
The contract in event.py is what must not move; the thing that fills it is
replaceable. Rules are used first because they are auditable - every claim
carries the span it came from, so when a model takes over, its output can be
diffed against a known baseline instead of trusted. A model that scores worse
than regex on `mortgagor` is a finding you can only have if the regex exists.

⚠ CLAIMS ARE NOT EVENTS. A claim is "this span of this page asserts X". An event
is "this happened, to these parties, in this direction". Several claims across
several pages collapse into one event, and keeping the layers separate is what
lets two documents describing the same transaction resolve to a single event
later without losing either citation.

⚠ ROLE IS DECIDED HERE AND IT IS THE THING MOST LIKELY TO BE SILENTLY WRONG.
`BETWEEN <A> ... and <B> ... the Mortgagee` puts A as mortgagor and B as
mortgagee - but only because of word ORDER and a trailing label, both of which
OCR can damage. When the label is missing the role is NOT guessed; the claim is
emitted with role=None and the event is refused. An inverted financing lineage
makes the borrower the lender, and it is invisible in every transcription metric
this project has.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import canonical as C
import event as E

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "bakeoff" / "out"
PAGES = HERE.parent / "bakeoff" / "pages"

MONEY = re.compile(r"\$\s?([\d][\d,]{2,})(?:\.\d\d)?")
DATE_Y = re.compile(r"\b(18|19|20)\d{2}\b")

# ⚠ WHICH KINDS DEPEND ON WORD ORDER. `mortgagor` and `mortgagee` are assigned by
# POSITION in "between X and Y" - so over a span the channels sequenced
# differently, the corroboration that covers the characters does not cover the
# direction, and a swap turns the borrower into the lender. An amount has no such
# exposure: $410,000 is $410,000 wherever it sits. See canonical.py.
ORDER_DEPENDENT = {"mortgagor", "mortgagee"}


def read_doc(engine, doc):
    """Concatenate a document's pages in order, keeping page numbers.

    ⚠ THE LEGACY PATH, KEPT ON PURPOSE. One engine's raw text, no provenance -
    which is what makes it the baseline the fused path is diffed against.
    """
    d = OUT / engine / doc
    if not d.exists():
        return []
    pages = []
    for f in sorted(d.glob("p0*")):
        if f.suffix != ".txt":
            continue
        stem = f.stem.replace(".png", "")
        pages.append((stem, f.read_text(encoding="utf-8", errors="replace"), None))
    return pages


def read_fused(doc):
    """The fused evidence record: provisional text + a gradeable span index."""
    try:
        cd = C.load(doc)
    except SystemExit:
        return []
    return [(p.page, p.provisional, p) for p in cd.pages]


def claim(kind, value, page, span, why, src=None):
    """One assertion, with the provenance of the exact characters it rests on.

    ⚠ PROVENANCE IS PER-CLAIM, NOT PER-DOCUMENT. A page that is 86% agreed can
    still have put its party name in the other 14%; grading the document and
    inheriting that grade downward is how an unconfirmed name acquires the
    confidence of the paragraph around it.
    """
    c = {"kind": kind, "value": value, "page": page, "span": span,
         "derivation": why}
    if src is None:
        # Legacy single-engine path: nothing corroborated this, and saying so is
        # the whole point of the column.
        c["provenance"] = {"grade": "single_channel", "order_safe": False,
                           "filled": [], "runs": 0}
    else:
        c["provenance"] = src.provenance_of(*span)
    p = c["provenance"]
    settled = p["grade"] in C.CONTENT_SETTLED
    if kind in ORDER_DEPENDENT and not p["order_safe"]:
        settled = False
        c["order_risk"] = True
    c["established"] = settled
    c["resolved_from"] = "image" if settled else "unresolved"
    return c


# ⚠ THE RECITAL IS ONE SENTENCE AND MUST BE MATCHED AS ONE. Searching for the
# mortgagor and the mortgagee independently looks equivalent and is not: "the
# Mortgagee" occurs NINETEEN more times in the covenant boilerplate of a single
# 1967 mortgage ("...shall be paid by the Mortgagor to the Mortgagee..."), so an
# unanchored pattern plus take-the-first-match will happily return `articles of
# personal property now or hereafter attached to` as the lender - with both
# channels agreeing on every character, because those characters really are on
# the page. Provenance cannot catch this. Only the clause structure can.
#
# ⚠ AND THE LABEL ITSELF IS DAMAGED. This document's recital ends `The MORTGAGE,
# WITNESSETH` - both engines dropped the final E of MORTGAGEE, independently.
# That is why the old pattern never matched the real clause and had to wander.
# MORTGAGEE? tolerates it; WITNESSETH is the era-stable terminator behind it.
RECITAL = re.compile(
    r"\bbetween\s+(?P<mor>.{3,300}?)\s*,?\s*the\s+MORTGAGOR\s*,?\s+and\s+"
    r"(?P<mee>.{3,300}?)\s*[,.]?\s*(?:the\s+MORTGAGEE?\b|WITNESSETH)",
    re.I | re.S)

# How far after the mortgagor a fallback mortgagee label may sit and still be
# read as the same clause. Beyond this it is boilerplate, not a recital.
SAME_CLAUSE = 400


def parties(text, page, src=None):
    """⚠ ORDER + LABEL, NEVER PLAUSIBILITY. A bank-looking name is not evidence
    of being the lender - in a satisfaction or an assignment the bank is on the
    other side. Only the instrument's own words assign the role."""
    out = []
    hits = list(RECITAL.finditer(text))
    # ⚠ TWO RECITALS IS AMBIGUITY, AND AMBIGUITY IS A RESULT. Picking the first
    # is how the wrong pair gets asserted with full provenance.
    if len(hits) == 1:
        m = hits[0]
        out.append(claim("mortgagor", " ".join(m.group("mor").split()), page,
                         m.span("mor"), "recital: 'between X, the MORTGAGOR'", src))
        out.append(claim("mortgagee", " ".join(m.group("mee").split()), page,
                         m.span("mee"),
                         "recital: 'and Y' in the same MORTGAGOR clause", src))
        return out
    if len(hits) > 1:
        return out

    # Fallback: the mortgagor label alone, with the mortgagee bounded to the
    # same clause. Never a free search of the whole page.
    m = re.search(r"BETWEEN\s+(.{3,160}?),?\s+the\s+Mortgagor\b", text, re.I | re.S)
    if not m:
        return out
    out.append(claim("mortgagor", " ".join(m.group(1).split()), page,
                     m.span(1), "labelled 'the Mortgagor'", src))
    tail = text[m.end():m.end() + SAME_CLAUSE]
    m2 = re.search(r"\band\s+(.{3,160}?),?\s+the\s+MORTGAGEE?\b", tail, re.I | re.S)
    if m2:
        off = m.end()
        out.append(claim("mortgagee", " ".join(m2.group(1).split()), page,
                         (off + m2.start(1), off + m2.end(1)),
                         f"labelled 'the Mortgagee' within {SAME_CLAUSE} chars "
                         f"of the Mortgagor label", src))
    return out


def amount(text, page, src=None):
    out = []
    for m in MONEY.finditer(text):
        v = int(m.group(1).replace(",", ""))
        # ⚠ THE $10 RECITAL IS A 500,000x TRAP in this corpus - "for TEN DOLLARS
        # and other good and valuable consideration" is boilerplate, not price.
        if v < 100:
            continue
        out.append(claim("amount", v, page, m.span(), "figure with $ sign", src))
    return out


def extract(doc, pages):
    cl = []
    for pg, text, src in pages:
        cl += parties(text, pg, src)
        cl += amount(text, pg, src)
        for m in DATE_Y.finditer(text):
            cl.append(claim("year", m.group(), pg, m.span(), "4-digit year", src))
    return cl


def to_event(doc, cl):
    """Collapse claims into ONE financing event, or refuse.

    ⚠ REFUSING IS A RESULT. A mortgage with only one identified side cannot be
    written as an event, because event.py would have to invent the counterparty
    role. Emitting nothing and reporting why is correct; emitting a half-event
    is how a lineage acquires a lender that does not exist.
    """
    def best(kind):
        v = [c for c in cl if c["kind"] == kind]
        return v[0] if v else None
    mor, mee = best("mortgagor"), best("mortgagee")
    amt = max((c for c in cl if c["kind"] == "amount"),
              key=lambda c: c["value"], default=None)
    yrs = sorted({c["value"] for c in cl if c["kind"] == "year"})
    if not (mor and mee):
        return None, (f"refused: mortgagor={'yes' if mor else 'NO'} "
                      f"mortgagee={'yes' if mee else 'NO'} - role unestablished")
    # ⚠ THE EVENT INHERITS ITS WEAKEST INGREDIENT. An event is only established
    # by the image if EVERY value it carries was; one unconfirmed party name
    # makes the whole record a lead, because the record is used as a unit. The
    # alternative - a per-field provenance the consumer must remember to check -
    # is the shape that lets a $0 microfilm mortgage become a fact.
    used = [c for c in (mor, mee, amt) if c]
    established = all(c.get("established") for c in used)
    unsafe = [c["kind"] for c in used if not c.get("established")]
    ev = E.event(
        event_id=f"{doc}-fin",
        date=(yrs[0] if yrs else None),
        action="MORTGAGE",
        functions=["financing"],
        quantity=amt["value"] if amt else None, unit="USD",
        document_id=doc, page=mor["page"],
        resolved_from="image" if established else "unresolved",
        confidence={"established": established, "unsettled_fields": unsafe},
        effects=[
            {"party_or_parcel": mor["value"], "role": "mortgagor",
             "effect": "encumbered"},
            {"party_or_parcel": mee["value"], "role": "mortgagee",
             "effect": "created"},
        ],
        claims=cl)
    return ev, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=None,
                    help="single-engine BASELINE (no provenance). Omit to read "
                         "the fused evidence record, which is the real path.")
    a = ap.parse_args()
    docs = [p.name for p in sorted(PAGES.iterdir()) if p.is_dir()]
    events, leads = [], []
    for doc in docs:
        pages = read_doc(a.engine, doc) if a.engine else read_fused(doc)
        if not pages:
            print(f"  {doc:22} "
                  f"({'no ' + a.engine + ' text' if a.engine else 'no evidence record'})")
            continue
        cl = extract(doc, pages)
        ev, why = to_event(doc, cl)
        kinds = {}
        for c in cl:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
        src = a.engine or "FUSED"
        print(f"  {doc:22} {len(pages):2} pages · {len(cl):3} claims "
              f"[{src}] {kinds}")
        if ev:
            (events if ev["resolved_from"] == "image" else leads).append(ev)
            m = {e["role"]: e["party_or_parcel"] for e in ev["effects"]}
            head = (f"      EVENT {ev['date']} {ev['action']}"
                    + (f" ${ev['quantity']:,}" if ev["quantity"] else ""))
            # ⚠ AN UNESTABLISHED EVENT IS PRINTED AS A LEAD, NOT AS A FACT WITH A
            # FOOTNOTE. The label is the first thing read; burying "unresolved"
            # in a field is how it stops being read at all.
            if ev["resolved_from"] != "image":
                bad = ",".join(ev["confidence"]["unsettled_fields"])
                head = head.replace("EVENT", "LEAD ") + f"   ⚠ unsettled: {bad}"
            print(head)
            for role in ("mortgagor", "mortgagee"):
                c = next((x for x in cl if x["kind"] == role), None)
                mark = "" if c and c.get("established") else "   ⚠"
                if c and c.get("order_risk"):
                    mark = "   ⚠ ORDER — role may be inverted"
                print(f"        {role:10}: {m.get(role,'')[:52]}{mark}")
        else:
            print(f"      {why}")
    (HERE / "_events.json").write_text(json.dumps(events, indent=1),
                                       encoding="utf-8")
    (HERE / "_leads.json").write_text(json.dumps(leads, indent=1),
                                      encoding="utf-8")
    print(f"\n  {len(events)} established events -> resolve/_events.json")
    print(f"  {len(leads)} unestablished leads  -> resolve/_leads.json")


if __name__ == "__main__":
    main()
