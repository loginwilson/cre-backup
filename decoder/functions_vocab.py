"""ONE CONTROLLED VOCABULARY FOR FUNCTIONS, AND THE ALIASES THAT DRIFTED.

⚠ HOW THIS BROKE, because the mechanism matters more than the fix.

Functions were assigned in two places that never spoke to each other:

  1  function_view.py derived them from the PREDICATE   (PRED_FN)
  2  every claim also carried a hand-written `ans=[...]` tag

Nothing validated (2), and (1) ignored it. So for ~14 hours I wrote answer
tags freehand and they drifted:

    CAPITAL   105 claims  ---- same function, two spellings, never reconciled
    DEBT        0 claims  /
    ENCUMBER   26 claims  ---- same again
    ENCUMBRANCE 13 claims /

and eight tags (PERMIT, PRIORITY, INCOME, IDENTIFY, PARTY, DISTRESS, ASBUILT,
OCCUPY) named functions the view had never heard of, so those claims silently
landed nowhere.

⚠ THE SYMPTOM THAT EXPOSED IT: PRIORITY read 1 atom for the whole session. I
had explicitly tagged the 2015 lien-position ladder ans=["PRIORITY"] and the
number did not move. A count that will not move when you feed it is the only
reason anyone ever finds this class of bug.

⚠ AND THE REASON IT SURVIVED SO LONG: the function table LOOKED healthy.
ENCUMBRANCE 96, DEBT 79, ENVELOPE 61. Big numbers in the rows you check first
are what hide an empty row you never look at.
"""

# the canonical set. NOTHING outside this list is a function.
CANON = {
    "TITLE":       "who owns it and how title moved",
    "DEBT":        "money lent against it, and what is still owed",
    "ENVELOPE":    "how much may be built, and how that changed",
    "ENCUMBRANCE": "burdens that run with the land",
    "PRIORITY":    "rank between creditors",
    "CONSENT":     "who had to agree, and who was bound without signing",
    "INCOME":      "cashflow pledged to a lender",
    "TENANCY":     "who occupies it and on what terms",
    "VALUE":       "prices, taxes and assessments — what it was worth, when",
    "PARCEL":      "the physical lot: area, boundaries, subdivision",
    "PERMIT":      "construction and the approvals behind it",
    "IDENTIFY":    "defects in the record itself — what a reader would miss",
}

# every spelling that ever reached a claim, mapped to canon.
# ⚠ do not delete rows here to "clean up" — they document the drift.
ALIAS = {
    "CAPITAL":     "DEBT",         # 105 claims, the biggest single drift
    "ENCUMBER":    "ENCUMBRANCE",  # 26 claims
    "ASBUILT":     "PERMIT",       # as-built condition is a construction fact
    "OCCUPY":      "TENANCY",
    "DISTRESS":    "DEBT",
    "PARTY":       "CONSENT",      # a named party matters via who bound whom
}


def canon(tag):
    """Map any tag to canon. Returns None for tags that are not functions."""
    t = (tag or "").strip().upper()
    t = ALIAS.get(t, t)
    return t if t in CANON else None


def functions_of(claim, pred_fn):
    """The functions a claim answers: predicate-derived UNION claim-declared.

    ⚠ UNION, not either alone. The predicate knows the general shape
    ('easement' is an ENCUMBRANCE); only the claim knows the specific one
    (this particular easement is also about the ENVELOPE). Taking just the
    predicate loses the second; taking just the tag loses claims I never
    tagged. Both sources are partial and neither is authoritative.
    """
    out = set()
    for f in pred_fn.get(claim["predicate"], []):
        c = canon(f)
        if c:
            out.add(c)
    for a in claim.get("answers") or []:
        c = canon(a)
        if c:
            out.add(c)
    return sorted(out)


def audit(rows):
    """Report tags that are not functions and canon entries nothing reaches."""
    import collections
    unknown = collections.Counter()
    reached = collections.Counter()
    for r in rows:
        for a in r.get("answers") or []:
            c = canon(a)
            (reached if c else unknown)[c or a] += 1
    empty = sorted(set(CANON) - set(reached))
    return unknown, reached, empty


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import claims as K
    unknown, reached, empty = audit(K.rows())
    print("FUNCTION VOCABULARY AUDIT\n")
    print("  claim tags resolving to canon:")
    for f, n in reached.most_common():
        print(f"    {f:<13} {n}")
    if unknown:
        print("\n  ⚠ TAGS THAT ARE NOT FUNCTIONS — these claims land nowhere:")
        for f, n in unknown.most_common():
            print(f"    {f:<13} {n}")
    else:
        print("\n  every claim tag resolves to canon OK")
    if empty:
        print(f"\n  ⚠ CANON FUNCTIONS NO CLAIM TAG REACHES: {', '.join(empty)}")
        print("    (they may still be reached by predicate — check "
              "function_view)")
