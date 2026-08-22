"""THE RATE: how much of the sample resolves WITHOUT a model.

THE ONLY NUMBER THAT DECIDES THE BUDGET. A proof crop costs ~300 tokens and a
model call; at 17M documents the difference between a 90% mechanical pass rate
and a 40% one is the difference between affordable and impossible. Everything
else measured today — 20,000 pg/hr, exact coordinates, film cropping, cold
reading — is subordinate to this.

WHAT COUNTS AS RESOLVED. A price the document itself vouches for:

    RPTT / 2.625%  must equal  RETT / 0.400%      two independent stamps
    and where MASTER.document_amt exists, it is a THIRD witness

⚠ NOT REPAIRED TO PASS. A document whose stamps disagree is a failure, and the
failure rate is the entire output of this file. On 2026-08-10 a hand-written
spatial rule bound the FILING FEE on 150 consecutive cover pages at 96% OCR
confidence, and the only reason it was caught is that the three-witness check
was reported beside it rather than after it.

⚠ AND $0/$0 IS A FINDING, NOT A GAP. Commonly-controlled parties transfer at no
consideration and the stamps read zero. That is a resolved document with a
price of nothing, not a failed extraction — conflating the two would understate
the pass rate and hide the real failures.

⚠ EXPECT HANDWRITING TO DEFEAT THIS ENTIRELY ON OLD PAPER. The 2002 deed
examined by hand had its NYS transfer tax written in pen — "$ 2940" — which no
OCR will ever read. Those documents cannot resolve mechanically at any quality
of engine, and they are precisely the population that must escalate to a crop.
Counting them as OCR failures would be wrong; they are DESIGN escalations.
"""
import collections
import gzip
import json
import pathlib
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import bulk

OCR = pathlib.Path("sample_ocr")
MONEY = re.compile(r"^\$?[\d,]{1,12}\.\d\d$")
RETT_RATE = 0.004

# ⚠ NYC RPTT HAS FOUR STATUTORY RATES, NOT ONE. THIS FILE ORIGINALLY ASSUMED
# 2.625% AND REPORTED ELEVEN CORRECT EXTRACTIONS AS "REAL misreads".
#
#     residential  <= $500,000   1.000%
#     residential  >  $500,000   1.425%
#     commercial   <= $500,000   1.425%
#     commercial   >  $500,000   2.625%
#
# Measured against the sample: 9,796.88 / 1.425% = $687,500 and the RETT stamp
# independently said $687,500. Five of the six flagged "disagreements" resolved
# EXACTLY once the right rate was used.
#
# ⚠ AND TRYING FOUR RATES IS NOT THE SAME AS REPAIRING A NUMBER TO PASS. The
# rate set is fixed by statute and closed; which one applies depends on property
# class, which the cover page does not state. Selecting among four legal
# constants is inference. Fitting an arbitrary multiplier until something agreed
# would be fraud, and the difference is that RETT is computed INDEPENDENTLY —
# a wrong rate choice simply fails to agree with it.
RPTT_RATES = (0.01, 0.01425, 0.02625)

LABELS = {
    "rptt": ["Real Property Transfer Tax", "Property Transfer Tax"],
    "rett": ["Real Estate Transfer Tax", "Estate Transfer Tax"],
}


def money_val(t):
    try:
        return float(t.replace("$", "").replace(",", ""))
    except ValueError:
        return None


def find_label(words, phrases):
    for ph in phrases:
        parts = ph.upper().split()
        for i in range(len(words) - len(parts) + 1):
            if all(words[i + k]["t"].upper().strip(":|$.,'‘’") == parts[k]
                   for k in range(len(parts))):
                return words[i + len(parts) - 1]
    return None


def bind(words, anchor, maxdx=1400, maxdy=200):
    """Nearest money token below-right of the label.

    ⚠ DELIBERATELY WIDE, AND THAT IS A CHOICE WITH A COST. A tight window misses
    real values; a wide one binds the wrong number. Wide is correct here ONLY
    because every binding is then checked against a second stamp — without the
    check this window would manufacture confident nonsense, which is exactly what
    it did on the 2003 cover pages where the label ran on into "Filing Fee".
    """
    if not anchor:
        return None
    best = None
    for w in words:
        if not MONEY.match(w["t"]):
            continue
        dy, dx = w["y"] - anchor["y"], w["x"] - anchor["x"]
        if dy < -anchor["h"] or dy > maxdy or dx < -200 or dx > maxdx:
            continue
        d = (abs(dy), abs(dx))
        if best is None or d < best[0]:
            best = (d, w)
    return best[1] if best else None


def main():
    files = sorted(OCR.glob("*.json.gz"))
    print(f"{len(files)} documents\n")
    plan = json.loads(pathlib.Path("_sample_plan.json").read_text())
    cell = {d: k for k, ids in plan.items() for d in ids}

    amt = {}
    for m in bulk.socrata_in("bnx9-e6tj", "document_id",
                             [f.name.replace(".json.gz", "") for f in files],
                             select="document_id,document_amt,doc_type"):
        try:
            amt.setdefault(m["document_id"], float(m.get("document_amt") or 0))
        except (TypeError, ValueError):
            amt.setdefault(m["document_id"], 0.0)

    out = collections.Counter()
    by_era = collections.defaultdict(collections.Counter)
    gaps = []
    for f in files:
        doc = f.name.replace(".json.gz", "")
        era = cell.get(doc, "?|?").split("|")[-1]
        rows = json.load(gzip.open(f, "rt", encoding="utf-8"))
        # the stamps live on the cover; scan the first three pages to be safe
        words = [w for r in rows[:3] for w in r["words"]]
        rp = bind(words, find_label(words, LABELS["rptt"]))
        rt = bind(words, find_label(words, LABELS["rett"]))
        a = money_val(rp["t"]) if rp else None
        b = money_val(rt["t"]) if rt else None

        if a is None and b is None:
            out["no_stamp_bound"] += 1
            by_era[era]["no_stamp_bound"] += 1
            continue
        if (a or 0) == 0 and (b or 0) == 0:
            out["zero_zero"] += 1
            by_era[era]["zero_zero"] += 1
            continue
        if a and b:
            pb = b / RETT_RATE
            # try each statutory rate; the RETT stamp is the independent judge
            best = min(((abs(a / r - pb) / max(a / r, pb), r) for r in RPTT_RATES),
                       key=lambda x: x[0])
            rel, rate = best
            pa = a / rate
            if rel < 0.02:
                out["two_witness_agree"] += 1
                by_era[era]["two_witness_agree"] += 1
                out[f"rate_{rate}"] += 1
                k = amt.get(doc, 0)
                if k:
                    out["index_confirms" if abs(pa - k) / k < 0.02
                        else "index_contradicts"] += 1
            else:
                out["two_witness_DISAGREE"] += 1
                by_era[era]["two_witness_DISAGREE"] += 1
                gaps.append((doc, era, a, b, round(pa), round(pb)))
        else:
            out["one_stamp_only"] += 1
            by_era[era]["one_stamp_only"] += 1

    n = len(files)
    print(f"{'outcome':<24}{'n':>6}{'pct':>8}")
    print("-" * 38)
    order = ["two_witness_agree", "zero_zero", "one_stamp_only",
             "two_witness_DISAGREE", "no_stamp_bound"]
    for k in order:
        print(f"{k:<24}{out[k]:>6}{out[k]/n*100:>7.1f}%")
    print("-" * 38)
    resolved = out["two_witness_agree"] + out["zero_zero"]
    print(f"{'MECHANICAL PASS':<24}{resolved:>6}{resolved/n*100:>7.1f}%")
    print(f"{'NEEDS A CROP + MODEL':<24}{n-resolved:>6}{(n-resolved)/n*100:>7.1f}%")
    if out["index_confirms"] or out["index_contradicts"]:
        print(f"\n  third witness on the agreeing set: "
              f"{out['index_confirms']} confirm / {out['index_contradicts']} contradict")

    print(f"\n{'era':<8}" + "".join(f"{k[:9]:>11}" for k in order))
    for era in ("film", "pre90", "90s", "00s", "2010+"):
        if era in by_era:
            tot = sum(by_era[era].values())
            print(f"{era:<8}" + "".join(f"{by_era[era][k]:>11}" for k in order)
                  + f"   (n={tot})")
    if gaps:
        print(f"\n  sample disagreements (these are REAL misreads, not noise):")
        for g in gaps[:6]:
            print(f"    {g[0]:<20}{g[1]:<7} rptt={g[2]} rett={g[3]} -> "
                  f"${g[4]:,} vs ${g[5]:,}")


if __name__ == "__main__":
    main()
