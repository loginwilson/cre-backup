"""⚠ RETRACTING THE "MISSING INSTRUMENT" CLAIMS. ALL OF THEM WERE FALSE.

I recorded, and told the user six times, that the operative instruments were
absent from the corpus, and called it the finding of the day:

    "THE FETCH SYSTEMATICALLY RETURNS THE CONSENTS AND LOSES THE DEALS"

Every one of them was on disk:

    2010102601040006   110 pages   the 2010 ZLDA
    2012122701550003    55 pages   the lot 23 ZLDA
    2013052101674004    45 pages   the lot 22 ZLDA
    2013052101674008    41 pages   the lot 21 ZLDA
    2013080901116002    40 pages   the lot 20 ZLDA
    2019071700601003    44 pages   the 2019 ZLDA
    2023110100486010    45 pages   the $120,000,000 CEMA
    2020081400407001    38 pages   the 2020 mortgage
    2025101700864004    52 pages   never opened by anyone

⚠ THE MECHANISM. I dispatched agents with HAND-BUILT document lists. Each read
exactly what it was given and correctly reported "X is not among the documents
provided" — a true statement about its own scope. I promoted that into a claim
about the world. Six times. I never ran `ls`.

⚠ WHY IT SURVIVED. The claims sourced FROM those documents were already in the
ledger — the 53,578 sf transfer cites 2010102601040006 — so the integrity
check never listed them as unread, and the "missing" story never collided with
anything. A false claim that contradicts nothing is invisible.

⚠ AND THE PART THAT GENERALISES: A SUBAGENT'S SCOPE STATEMENT IS EVIDENCE
ABOUT THE SUBAGENT, NOT ABOUT THE WORLD. The work list must be generated from
the filesystem — see ledger.py, which now does that and refuses to report a
decode as finished while any document is unopened.
"""
import pathlib
import re

RETRACT = {
 "c2023-cema-missing": (
   "⚠ RETRACTED — FALSE. I recorded that the $120,000,000 CEMA (CRFN "
   "2023000287582) was not in this corpus. IT IS ON DISK as document "
   "2023110100486010, 45 pages, and had never been opened. What remains "
   "true and useful: I misnamed 2023110100486011 as 'the 2023 CEMA' when "
   "its own cover page reads ASSIGNMENT OF LEASES AND RENTS"),
 "c2010-zlda-missing": (
   "⚠ RETRACTED — FALSE. The 2010 ZLDA is on disk as document "
   "2010102601040006, 110 pages. Eleven claims in this very ledger already "
   "cite it, including the 53,578 sf transfer. The CRFN-sequence reasoning "
   "was sound and the conclusion was still wrong, because I inferred from a "
   "sequence instead of checking the directory"),
 "c2013-zldas-missing": (
   "⚠ RETRACTED — FALSE. The lot 21 and lot 22 ZLDAs are on disk as "
   "2013052101674008 (41 pages) and 2013052101674004 (45 pages), together "
   "with the lot 23 ZLDA (2012122701550003, 55 pages) and the lot 20 ZLDA "
   "(2013080901116002, 40 pages). ⚠ THIS CLAIM CARRIED THE 'FIFTH AND SIXTH "
   "INSTANCES' TALLY THAT MADE THE PATTERN LOOK PROVEN. A count of false "
   "instances is not corroboration"),
 "c2013-nosquarefeet": (
   "⚠ SCOPE ERROR. 'Zero square-footage figures' is true of the TEN "
   "DECLARATION AND WAIVER DOCUMENTS the agent was given, and false of the "
   "corpus — the ZLDAs on disk carry every transfer figure, and the envelope "
   "chain closes to the square foot from them. The structural lesson stands "
   "(declarations merge lots, ZLDAs move floor area); the coverage claim "
   "attached to it did not"),
}

APPEND = {
 "c2019-zlda-date": (
   "  ⚠ CORRECTION: I wrote 'the ZLDA ITSELF IS STILL NOT IN THE CORPUS'. "
   "It is on disk as 2019071700601003, 44 pages"),
 "c2020-loan": (
   "  ⚠ CORRECTION: I wrote the companion mortgage 'IS NOT IN THE CORPUS'. "
   "It is on disk as 2020081400407001, 38 pages"),
}


def main():
    p = pathlib.Path("claims.py")
    t = p.read_text(encoding="utf-8")
    n = 0
    for cid, newnote in RETRACT.items():
        # replace the note= body of this claim, leaving everything else intact
        i = t.find(f'C("{cid}"')
        if i < 0:
            print(f"  ⚠ {cid} not found")
            continue
        j = t.find('   note="', i)
        end = t.find('"),\n', j)
        if j < 0 or end < 0 or end < j:
            print(f"  ⚠ {cid} note not parseable")
            continue
        body = '   note="' + '"\n        "'.join(
            _chunks(newnote, 64))
        t = t[:j] + body + t[end:]
        n += 1
    for cid, extra in APPEND.items():
        i = t.find(f'C("{cid}"')
        if i < 0:
            continue
        end = t.find('"),\n', i)
        if end < 0:
            continue
        t = t[:end] + '"\n        "' + '"\n        "'.join(
            _chunks(extra, 64)) + t[end:]
        n += 1
    p.write_text(t, encoding="utf-8")
    print(f"retracted/corrected {n} claims")


def _chunks(s, w):
    out, cur = [], ""
    for word in s.split():
        if len(cur) + len(word) + 1 > w:
            out.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        out.append(cur)
    return out


main()
