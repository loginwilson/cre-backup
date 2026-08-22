"""TRIANGULATE — settle a contested fact by laying its proofs out in time order.

⚠ TWO RULES THE USER NAMED, BOTH OF WHICH I BROKE TODAY.

RULE 1 — OLDEST TO NEWEST. Chronological order is what prevents out-of-order
change. I read in PARALLEL by batch, so the 2023 documents landed before the
1990 root. That is exactly how the tax-credit error happened: I saw the 2003
affidavit ($27,500) and the 2014 affidavit ($28,000) before I saw the 1990
instrument ($22,500) or the 2013 schedule ($22,500), and from that partial
out-of-order sample I built a "drift, each higher than the last" narrative.
In date order it is not a drift at all — it is two wrong affidavits with a
correct one between them, and the shape is obvious the moment the rows are
sorted. ⚠ AN OUT-OF-ORDER READ DOES NOT PRODUCE A GAP. IT PRODUCES A STORY.

RULE 2 — THE CROP IS WHAT MAKES TRIANGULATION POSSIBLE. A citation says where
to look. A crop is the looking, preserved. When 2013 says "below an UPPER
limiting plane" and 2019 says "below a LOWER limiting plane", no amount of
re-reading my own notes settles it, because my notes are what is in doubt.
Three crops side by side settle it in seconds.

⚠ AND THE PART THAT ONLY WORKS WITH BOTH RULES TOGETHER: a fact asserted at
T2 that contradicts T1 is not automatically an error at T1. It may be a real
CHANGE. Only the date order tells you which, and only the crops tell you the
words actually changed rather than my transcription of them.

Usage:
    python triangulate.py <fact>
    python triangulate.py plane        # the 130-foot contradiction
    python triangulate.py taxcredit    # the prior-tax figures
    python triangulate.py --list
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import claims as K

# A contested fact is a named set of claim_ids. Naming them explicitly rather
# than pattern-matching keeps the register honest: a fact enters this file
# because someone noticed a conflict, not because a regex fired.
FACTS = {
"plane": dict(
    question="Does lot 49 take the volume ABOVE or BELOW the 130-foot plane "
             "over lot 20?",
    why="one word reverses which volume was bought, and the envelope ledger "
        "cannot tell me — 14,703 sf arrives from lot 20 either way",
    claims=["c2012-lot20-plane", "c2013-plane-upper", "c2019-lot20-elevation"],
),
"taxcredit": dict(
    question="How much mortgage tax was actually paid on the 1990 Apple Bank "
             "mortgage?",
    why="each later consolidation claims a 255 exemption supported by this "
        "figure; two of the four statements of it are wrong",
    claims=["c1990-tax-actual", "c2003-affidavit-overstates",
            "c2013-taxcredit-correct", "c-taxcredit-drift"],
),
"boundary": dict(
    question="Is the parcel's westerly course 82'8-3/4\" or 82'10\"?",
    why="carried as a defect through four reads; resolved as two conventions",
    claims=["c1990-legal-conflict", "c2010-legal-conflict-again",
            "c2013-deed-vs-survey-early", "c2019-deed-vs-survey"],
),
"newmoney": dict(
    question="How much of each consolidation was actually new money?",
    why="every split is HANDWRITTEN; the typed text always states only the "
        "consolidated total",
    claims=["c2013-handwritten-advance", "c2014-split", "c2023-gap-tax",
            "c2020-tax-conflict"],
),
}


def rows_for(ids):
    by_id = {c["claim_id"]: c for c in K.rows()}
    missing = [i for i in ids if i not in by_id]
    got = [by_id[i] for i in ids if i in by_id]
    # ⚠ RULE 1, ENFORCED IN CODE RATHER THAN REMEMBERED.
    got.sort(key=lambda c: (c["effective"] or "", c["stated"] or ""))
    return got, missing


def crop_for(claim):
    """Path to this claim's proof crop, or why there isn't one."""
    import hashlib
    import pathlib
    key = f"{claim['document_id']}|{claim['page']}"
    h = hashlib.md5(key.encode()).hexdigest()[:16]
    p = pathlib.Path("proofs") / f"{h}.png"
    if p.exists():
        return str(p), None
    src = pathlib.Path("pages_out") / claim["document_id"] / f"{claim['page']}.png"
    if src.exists():
        return None, f"page on disk, CROP NOT CUT -> {src}"
    return None, "⚠ page not on disk — this claim cannot be re-verified"


def show(name):
    f = FACTS[name]
    got, missing = rows_for(f["claims"])
    print(f"CONTESTED FACT · {name}\n")
    print(f"  QUESTION  {f['question']}")
    print(f"  WHY       {f['why']}\n")
    if missing:
        print(f"  ⚠ claim ids not found: {', '.join(missing)}\n")
    print("  OLDEST TO NEWEST — the order that stops a later state being")
    print("  written over an earlier one:\n")
    for c in got:
        eff = c["effective"] or "?"
        std = c["stated"] or ""
        when = f"{eff}" + (f" (recorded {std})" if std and std != eff else "")
        print(f"  ── {when}   {c['document_id']} {c['page']}")
        print(f"     [{c['claim_id']}]")
        for line in wrap(c["value_text"] or "", 66):
            print(f"     {line}")
        crop, why = crop_for(c)
        print(f"     PROOF  {crop if crop else why}")
        print()
    n_crops = sum(1 for c in got if crop_for(c)[0])
    print(f"  crops available {n_crops}/{len(got)}")
    if n_crops < len(got):
        print("  ⚠ CANNOT ADJUDICATE FROM NOTES ALONE — my transcription is")
        print("    the thing in doubt. Cut the crops, then compare the pixels.")
        print(f"    -> python proof.py --claims {','.join(f['claims'])}")


def wrap(s, w):
    out, cur = [], ""
    for word in str(s).split():
        if len(cur) + len(word) + 1 > w:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        out.append(cur)
    return out or [""]


def main():
    args = [a for a in sys.argv[1:]]
    if not args or args[0] in ("--list", "-l"):
        print("CONTESTED FACTS REGISTER\n")
        for k, v in FACTS.items():
            got, _ = rows_for(v["claims"])
            span = (f"{got[0]['effective'][:4]}-{got[-1]['effective'][:4]}"
                    if got else "?")
            n = sum(1 for c in got if crop_for(c)[0])
            print(f"  {k:<12} {len(v['claims'])} claims  {span}  "
                  f"crops {n}/{len(got)}")
            print(f"               {v['question']}")
        print("\n  python triangulate.py <name>")
        return
    for a in args:
        if a in FACTS:
            show(a)
        else:
            print(f"unknown fact '{a}'. try --list")


main()
