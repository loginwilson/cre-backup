"""⚠ WIRING SUPERSESSION. The last structural flaw in the ledger.

Zero of 348 claims used `supersedes`. So `c2007-unres` still asserted that
the $2,300,000 "corresponds to nothing ... PAGE NOT READ" while sitting
beside the claim that answers it three independent ways — and NOTHING linked
them. A query returns both, confidently, with no way to tell which is
current. That is worse than an ordinary error, because the ledger looks
healthy.

⚠ AND THE SCHEMA WAS WRONG FOR THE JOB. `supersedes` is a single-valued
column, but ONE claim here supersedes FOUR: reading both sides of the
130-foot plane out of one document retired three earlier partial readings
AND my own first attempt at resolving them. Supersession is a RELATION, not
a field. It goes in the edge table, which is many-to-many, and the column
carries only the 1:1 cases for convenience.

⚠ THE DISTINCTION THAT MATTERS FOR QUERYING:

    SUPERSEDES  the later claim REPLACES the earlier — the earlier is no
                longer true and must be excluded from any current view
    CORRECTS    the later claim FIXES an error in the earlier
    RETRACTS    the earlier claim was FALSE and is withdrawn entirely
    CORROBORATES  independent evidence for the same fact, both stay live

A view that filters on "no incoming SUPERSEDES/CORRECTS/RETRACTS edge" is
the current state of the parcel. Without these edges there is no such view.
"""
import pathlib
import re

# (new_claim, old_claim, relation, why)
LINKS = [
 ("c2007-2p3m-answer", "c2007-unres", "SUPERSEDES",
  "the $2,300,000 is the sublease assignment price, proven three ways; the "
  "earlier claim says the figure corresponds to nothing and the page was "
  "not read"),
 ("c2013-taxcredit-correct", "c-taxcredit-drift", "CORRECTS",
  "the prior-tax figures do not drift upward — the 2013 schedule has them "
  "right, so it is two wrong affidavits with a correct one between them"),
 ("c2013-plane-both-sides", "c2013-plane-upper", "SUPERSEDES",
  "both sides of the 130-foot plane quoted from one document"),
 ("c2013-plane-both-sides", "c2012-lot20-plane", "SUPERSEDES",
  "the bare '(lower limiting plane)' parenthetical is the loosest of three "
  "descriptions of the same plane"),
 ("c2013-plane-both-sides", "c2019-lot20-elevation", "SUPERSEDES",
  "the 2019 Lower Parcel / Air Space split describes the same plane from "
  "the other side"),
 ("c2013-plane-both-sides", "c2013-plane-RESOLVED", "CORRECTS",
  "⚠ MY OWN FIRST RESOLUTION WAS HALF RIGHT. Lot 49 took the development "
  "rights from BELOW the plane AND a light/air/view easement ABOVE it — "
  "both, not one"),
 ("c2013-deed-vs-survey-early", "c1990-legal-conflict", "RETRACTS",
  "not a defect — '82 feet 10 inches (deed) (82 feet 8 3/4 inches - "
  "survey)' are two measurement conventions printed side by side"),
 ("c2013-deed-vs-survey-early", "c2010-legal-conflict-again", "RETRACTS",
  "same conventions, same non-defect"),
 ("c2019-deed-vs-survey", "c2013-deed-vs-survey-early", "CORROBORATES",
  "the 2019 survey prints both conventions again, six years later"),
 ("c2013-lot22-price", "c2013-zldas-missing", "RETRACTS",
  "⚠ the ZLDAs were never missing — they were on disk the whole time and "
  "carry the prices"),
 ("c2010-price-hidden", "c2010-zlda-missing", "RETRACTS",
  "⚠ the 2010 ZLDA is document 2010102601040006, 110 pages, on disk"),
 ("c2023-owner-agreement", "c2023-chelsea-entry", "SUPERSEDES",
  "the conveyance is named: an Owner Agreement dated October 16, 2023, not "
  "a deed"),
 ("c2023-owner-agreement", "c2023-cema-missing", "RETRACTS",
  "⚠ the $120,000,000 CEMA is document 2023110100486010, 45 pages, on disk"),
 ("c2018-splitter-severs", "c2018-indexdefect", "CORRECTS",
  "the City corrected the indexing in 2020 — the remark reads 'CORRECTED TO "
  "ADD LOT 49 ... UPDATED 8/19/20', so a BBL pull no longer misses it"),
 ("c2025-maxsecured", "c2023-reconcile", "CORROBORATES",
  "the $85,000,000 reconstructed from balances is stated outright under "
  "RPL 254 in the 2025 mortgage"),
]

NEW_EDGES = "".join(
    f' ("{a}", "{b}", "{rel}", "read",\n  "{why}"),\n'
    for a, b, rel, why in LINKS)


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")

    # 1 · edges carry the many-to-many truth
    t = t.replace("EDGES = [\n", "EDGES = [\n" + NEW_EDGES, 1)

    # 2 · the column carries the 1:1 cases, for convenience only
    single = {}
    seen = {}
    for a, b, rel, _ in LINKS:
        if rel in ("SUPERSEDES", "RETRACTS"):
            seen[a] = seen.get(a, 0) + 1
    for a, b, rel, _ in LINKS:
        if rel in ("SUPERSEDES", "RETRACTS") and seen[a] == 1:
            single[b] = a           # old claim records who replaced it
    n = 0
    for old, new in single.items():
        pat = f'C("{old}",'
        i = t.find(pat)
        if i < 0:
            continue
        end = t.find('"),\n', i)
        if end < 0:
            continue
        t = t[:end + 2] + f'\n   supersedes="{new}",' + t[end + 2:]
        n += 1
    p.write_text(t, encoding="utf-8")
    print(f"wrote {len(LINKS)} edges · set supersedes on {n} claims")


main()
