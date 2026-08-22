"""THE BRIDGE: fused evidence -> the text claims are read from, with provenance.

    python canonical.py                    # provenance profile per document
    python canonical.py --doc FT_1680008647768 --page p003 --show

⚠ WITHOUT THIS, RESOLUTION READS ONE ENGINE AND CALLS IT PIXELS. claims.py takes
`--engine q35-fair`, concatenates that engine's raw text, and stamps every event
`resolved_from="image"`. But "image" is a claim that THE PIXELS ESTABLISHED IT,
and one engine's unconfirmed reading is exactly what the second channel exists to
refuse. The fuser already knows which spans were corroborated; nothing downstream
was asking.

⚠ THE ACCEPTED TEXT HAS HOLES AND THAT IS THE POINT. fuse.py writes [UNRESOLVED]
wherever the channels failed to agree, so at 86.6% acceptance roughly one span in
seven is a placeholder. A regex cannot match a party name that is not in the
string - so searching the accepted text alone would not produce wrong claims, it
would produce MISSING ones, which is the harder failure to notice. So this module
builds TWO strings over the same coordinates:

    settled      [UNRESOLVED] left in place - what the system asserts
    provisional  placeholders filled from the best available channel - what it
                 can SEE, every filled span tagged and never silently settled

Claims are found in `provisional` and graded by `provenance_of()`. A claim whose
span touches a filled hole is not suppressed and not trusted: it is emitted as
unresolved, which is a lead for escalation rather than a fact.

⚠ FOUR GRADES, NOT TWO, BECAUSE ORDER IS ITS OWN KIND OF DOUBT:

    image_agreement  both channels, same content, same position   SETTLED
    order_artifact   both channels read these tokens, DIFFERENT position
    disputed         both channels read here, different characters
    single_channel   one channel only; nothing corroborated it

`order_artifact` is the one that looks harmless and is not. Its content is
corroborated twice over - the tokens are present in both channels - so a value
claim over it (an amount, a date) rests on two readings. But ROLE IN THIS CORPUS
IS ASSIGNED BY WORD ORDER: claims.py reads `between X and Y ... the mortgagee`
and makes X the borrower purely by position. Over an order-unsettled span, that
is the one claim the corroboration does not cover, and an inverted financing
lineage is invisible to every transcription metric this project has (see
event.py). So provenance is returned with an `order_safe` flag, and claims that
depend on sequence must consult it.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
EVIDENCE = HERE / "_evidence"

PLACEHOLDER = "[UNRESOLVED]"

# Worst-first. A span's grade is the WEAKEST grade it touches, never an average:
# a party name that is 90% agreed and 10% invented is not 90% established.
GRADE_ORDER = ("single_channel", "disputed", "order_artifact", "image_agreement")
GRADE_RANK = {g: i for i, g in enumerate(GRADE_ORDER)}

# Which grades survive into an asserted value, and which are leads.
SETTLED = {"image_agreement"}
# ⚠ order_artifact is content-settled but NOT order-settled. It is listed here
# because a value claim over it rests on two readings; `order_safe` is what
# stops a ROLE claim from doing the same.
CONTENT_SETTLED = {"image_agreement", "order_artifact"}


def grade(run):
    """Map a fused run to one of the four grades."""
    st = run.get("status")
    if st == "agreed":
        return "image_agreement"
    if st in ("unaligned", "disputed", "single_channel"):
        return "order_artifact" if st == "unaligned" else st
    return "single_channel"


def _reading(run, channels):
    """Best available text for an unaccepted run, and which channel gave it.

    ⚠ FOR A DISPUTE THIS PICKS ONE OF TWO CONTRADICTORY READINGS, DELIBERATELY
    AND VISIBLY. The alternative - leaving the hole - hides the claim entirely,
    and a party name we cannot see is worse than one we can see and distrust.
    The VLM is preferred because it is the stronger engine on this corpus (98.9%
    vs 95.7%), NOT because it is right here. The span stays ungraded-as-settled
    either way, so nothing downstream can promote it by accident.
    """
    for name in (channels.get("vlm"), channels.get("ocr")):
        if name and run.get(name):
            return run[name], name
    return None, None


class Page:
    __slots__ = ("page", "settled", "provisional", "spans", "agreement")

    def __init__(self, page, settled, provisional, spans, agreement):
        self.page = page
        self.settled = settled
        self.provisional = provisional
        # spans: [(start, end, grade, filled_by_or_None)] over `provisional`
        self.spans = spans
        self.agreement = agreement

    def provenance_of(self, start, end):
        """Grade a character range of `provisional`. Worst grade wins.

        Returns {grade, order_safe, filled, runs} - `filled` naming the channels
        that supplied text no one corroborated, so a reader can see exactly whose
        word a claim rests on.
        """
        worst, touched, filled = "image_agreement", 0, []
        for s, e, g, by in self.spans:
            if e <= start or s >= end:
                continue
            touched += 1
            if GRADE_RANK[g] < GRADE_RANK[worst]:
                worst = g
            if by:
                filled.append(by)
        if not touched:
            # A span outside every run cannot be graded, and an ungradeable
            # span is not a settled one.
            return {"grade": "single_channel", "order_safe": False,
                    "filled": [], "runs": 0}
        return {"grade": worst,
                # Order is only safe when every run under the span agreed on
                # position too - order_artifact is precisely the case that did not.
                "order_safe": worst == "image_agreement",
                "filled": sorted(set(filled)), "runs": touched}


class Doc:
    def __init__(self, doc_id, channels, pages):
        self.doc_id = doc_id
        self.channels = channels
        self.pages = pages

    def profile(self):
        n = {g: 0 for g in GRADE_ORDER}
        chars = {g: 0 for g in GRADE_ORDER}
        for p in self.pages:
            for s, e, g, _ in p.spans:
                n[g] += 1
                chars[g] += e - s
        return n, chars


def load(doc_id):
    f = EVIDENCE / f"{doc_id}.json"
    if not f.exists():
        raise SystemExit(f"  no evidence record for {doc_id} — run fuse.py first")
    rec = json.loads(f.read_text(encoding="utf-8"))
    channels = rec.get("channels", {})
    pages = []
    for pg in rec.get("pages", []):
        settled_parts, prov_parts, spans, cur = [], [], [], 0
        for run in pg.get("runs", []):
            g = grade(run)
            acc = run.get("accepted")
            if acc is not None:
                text, by = acc, None
            else:
                text, by = _reading(run, channels)
                if text is None:
                    # Nothing to show at all: keep the placeholder so the
                    # position survives and the hole stays visible.
                    text = PLACEHOLDER
            settled_parts.append(acc if acc is not None else PLACEHOLDER)
            prov_parts.append(text)
            spans.append((cur, cur + len(text), g, by))
            cur += len(text) + 1          # +1 for the joining space
        pages.append(Page(pg.get("page"), " ".join(settled_parts),
                          " ".join(prov_parts), spans,
                          pg.get("token_agreement")))
    return Doc(rec.get("doc_id", doc_id), channels, pages)


def documents():
    return sorted(p.stem for p in EVIDENCE.glob("*.json")
                  if not p.stem.endswith((".escalate", ".located")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", default=None)
    ap.add_argument("--page", default=None)
    ap.add_argument("--show", action="store_true",
                    help="print the settled and provisional text side by side")
    a = ap.parse_args()

    docs = [a.doc] if a.doc else documents()
    for d in docs:
        doc = load(d)
        n, chars = doc.profile()
        tot = sum(chars.values()) or 1
        print(f"\n  {doc.doc_id}   {len(doc.pages)} pages   "
              f"vlm={doc.channels.get('vlm')} ocr={doc.channels.get('ocr')}")
        for g in reversed(GRADE_ORDER):
            print(f"    {g:16} {n[g]:>4} runs   {chars[g]:>7,} chars   "
                  f"{100*chars[g]/tot:>5.1f}%")
        settled_chars = sum(chars[g] for g in SETTLED)
        content = sum(chars[g] for g in CONTENT_SETTLED)
        print(f"    {'-'*54}")
        print(f"    settled (order-safe too)      {100*settled_chars/tot:>5.1f}%")
        print(f"    content-corroborated          {100*content/tot:>5.1f}%   "
              f"(+{100*(content-settled_chars)/tot:.1f}pt from order artifacts)")
        holes = sum(p.provisional.count(PLACEHOLDER) for p in doc.pages)
        if holes:
            print(f"    ⚠ {holes} span(s) NO channel read — placeholder kept")

        if a.show:
            for p in doc.pages:
                if a.page and p.page != a.page:
                    continue
                print(f"\n    --- {p.page}  agreement {p.agreement} ---")
                print(f"    SETTLED     {p.settled[:400]}")
                print(f"    PROVISIONAL {p.provisional[:400]}")


if __name__ == "__main__":
    main()
