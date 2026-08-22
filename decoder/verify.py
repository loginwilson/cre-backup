"""Prove a decode rule at scale before trusting it — the crawl→walk gate.

LOGIN, 2026-08-06: *"once youre confident that you are decoding the document
type perfectly without fails or error, you can begin scaling. crawl, walk, jog,
run."*

THE PROBLEM THIS SOLVES

    Every rule in this project is currently n=1 or n=2. "No failures observed"
    on two documents is not confidence — it is a sample too small to fail. A
    rule that holds twice and breaks on the third costs more than no rule,
    because it will be applied to millions.

    So a type does not graduate on a feeling. It graduates on a MEASURED ERROR
    RATE against a falsifiable prediction.

WHAT MAKES A RULE TESTABLE

    The rule must predict something checkable that it did not use as input.
    "The index amount is the price" is not testable on its own. But:

        index document_amt  ->  predicts NYC RPTT at 2.625% AND NYS RETT at 0.4%

    is testable, because the stamps are printed on the page and were not used to
    derive the prediction. Two independent stamps agreeing with one predicted
    figure is a real test; a rule reproducing its own input is not.

⚠ WHAT A FAILURE MEANS — three outcomes, and the middle one is the point

    PASS       predicted and observed agree within tolerance
    EXEMPT     no tax was charged (nominal transfer, exemption code) — the rule
               does not apply here, and that is NOT a failure. Counting exempts
               as failures makes a good rule look broken; counting them as
               passes makes a broken rule look good. They are their own class.
    FAIL       tax was charged and disagrees with the prediction — the rule is
               wrong, or wrong in a case we have not characterised yet

    A type graduates only when FAIL is zero across a sample big enough to have
    caught a failure if one existed, and every EXEMPT is explained.
"""
import json, os, pathlib, random, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).parent))

TOL = 0.01          # dollars; the stamps are exact, so tolerance is rounding only


def sample_documents(doc_type, n=30, seed=20260806, borough=None):
    """A RANDOM sample, not the first N.

    Socrata returns rows in insertion order, so the first N documents of a type
    are all from one era and often one filer. That is the sample that agrees
    with itself. Randomise across the whole population or the test proves
    nothing about the population.
    """
    import bulk
    where = f"doc_type='{doc_type}' and document_amt is not null and document_amt!='0'"
    if borough:
        where += f" and recorded_borough='{borough}'"
    total = int(list(bulk.socrata("bnx9-e6tj", select="count(*)", where=where,
                                  paginate=False)[0].values())[0])
    rng = random.Random(seed)
    picks, seen = [], set()
    tries = 0
    while len(picks) < n and tries < n * 8:
        tries += 1
        off = rng.randrange(0, max(1, total - 1))
        rows = bulk.socrata("bnx9-e6tj",
                            select="document_id,doc_type,document_amt,document_date,"
                                   "recorded_datetime,recorded_borough",
                            where=where, limit=1, offset=off, paginate=False)
        if rows and rows[0]["document_id"] not in seen:
            seen.add(rows[0]["document_id"])
            picks.append(rows[0])
    return picks, total


def predict_deed(amt):
    """What the stamps MUST read if the index amount is the true consideration."""
    return {"rptt_2_625": round(amt * 0.02625, 2),
            "rptt_1_425": round(amt * 0.014250, 2),
            "rett": round(amt * 0.004, 2)}


def predict_mortgage(amt):
    import consideration as C
    return C.mortgage_tax(amt)


def record(path, rec):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())


def report(results, doc_type, population):
    from collections import Counter
    c = Counter(r["verdict"] for r in results)
    n = len(results)
    print(f"\nVERIFY {doc_type} — {n} documents sampled from {population:,}\n")
    for k in ("PASS", "EXEMPT", "FAIL", "UNREADABLE"):
        if c[k]:
            print(f"    {k:<12}{c[k]:>5}  {c[k]/n*100:>5.1f}% of {n}")
    testable = c["PASS"] + c["FAIL"]
    if testable:
        print(f"\n    error rate on TESTABLE cases: {c['FAIL']}/{testable} "
              f"= {c['FAIL']/testable*100:.1f}%")
    else:
        print(f"\n    ⚠ ZERO testable cases — every document was exempt or "
              f"unreadable. This run proves NOTHING about the rule.")
    if c["FAIL"]:
        print(f"\n    FAILURES (each one is a rule to fix, not a document to "
              f"discard):")
        for r in results:
            if r["verdict"] == "FAIL":
                print(f"      {r['document_id']}  index ${r.get('index_amt',0):,.0f}  "
                      f"{r.get('why','')}")
    gate = testable >= 25 and c["FAIL"] == 0
    print(f"\n    GRADUATES TO SCALE: {'YES' if gate else 'NO'}"
          + ("" if gate else f"  (need >=25 testable and 0 FAIL; "
                             f"have {testable} testable, {c['FAIL']} fail)"))
    return gate


if __name__ == "__main__":
    print(__doc__)
