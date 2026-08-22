"""THE ACRIS DECODE, SCORED ONLY ON WHAT ACRIS IS THE AUTHORITY FOR.

Run:  python acris_report.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import claims as K
from acris_scope import SCOPE, HANDOFF, ANSWERED, NOT_RECORDED, MISSING


def wrap(s, w, ind):
    out, cur = [], ""
    for word in str(s).split():
        if len(cur) + len(word) + 1 > w:
            out.append(ind + cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        out.append(ind + cur)
    return out


def main():
    rows = K.rows()
    docs = {c["document_id"] for c in rows}
    read = {c["document_id"] for c in rows if c["evidence"] == "read"}

    print("=" * 74)
    print("ACRIS DECODE · Manhattan Block 800 Lot 49 · 1971-2025")
    print("=" * 74)
    print(f"{len(rows)} claims · {len(read)} documents read to a claim · "
          f"{len(docs)} cited\n")

    tallies = {ANSWERED: 0, NOT_RECORDED: 0, MISSING: 0}
    for fn, qs in SCOPE.items():
        n_miss = sum(1 for _, s, _ in qs if s == MISSING)
        head = "⚠ INCOMPLETE" if n_miss else "COMPLETE"
        print(f"── {fn}   {head}")
        for q, status, detail in qs:
            tallies[status] += 1
            mark = {ANSWERED: " ", NOT_RECORDED: "·", MISSING: "⚠"}[status]
            print(f"  {mark} {q}")
            print(f"      [{status}]")
            for line in wrap(detail, 66, "      "):
                print(line)
        print()

    total = sum(tallies.values())
    settled = tallies[ANSWERED] + tallies[NOT_RECORDED]

    print("=" * 74)
    print("SCORE — questions ACRIS is the authority for\n")
    print(f"  ANSWERED       {tallies[ANSWERED]:>3}   the corpus states it")
    print(f"  NOT-RECORDED   {tallies[NOT_RECORDED]:>3}   proven absent across "
          f"enough instruments to be a")
    print(f"                       finding. ⚠ THIS COUNTS AS DECODED")
    print(f"  MISSING        {tallies[MISSING]:>3}   ⚠ an ACRIS instrument I "
          f"do not hold")
    print(f"  {'-' * 60}")
    print(f"  SETTLED     {settled}/{total}   ({100 * settled // total}%)\n")

    if tallies[MISSING]:
        print("  ⚠ THE ONLY REAL FAILURES — both are FETCH failures, not")
        print("    reading failures. Nothing on disk would close either.\n")
        for fn, qs in SCOPE.items():
            for q, s, _ in qs:
                if s == MISSING:
                    print(f"      [{fn}] {q}")
        print()

    print("=" * 74)
    print("HANDOFF — not ACRIS's job, and what ACRIS hands over anyway\n")
    for who, what, gives in HANDOFF:
        print(f"  -> {who}: {what}")
        for line in wrap(gives, 66, "       "):
            print(line)
        print()

    print("=" * 74)
    print("⚠ WHAT WOULD ACTUALLY IMPROVE THIS DECODE\n")
    print("  1  FETCH the deed into Chelsea 25 Hotel LLC, and the four")
    print("     ZLDAs. Two of the six unsettled questions close instantly;")
    print("     no amount of re-reading the 1,659 pages on disk touches them.")
    print("  2  CUT THE CROPS. 309 claims, 1 crop. Every claim can point at")
    print("     a page and only one can show it — and the first crop I cut")
    print("     today caught a page cite that was off by one AND reversed a")
    print("     conclusion I had already reported.")
    print("  3  WRITE IN DATE ORDER. Reading can be parallel; deciding")
    print("     cannot. Out-of-order writes do not leave a gap, they leave")
    print("     a plausible wrong story — which is how the tax-credit")
    print("     'drift' survived being reported to the user.")


main()
