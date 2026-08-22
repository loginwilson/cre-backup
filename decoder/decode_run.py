"""COLD RUN — decode a parcel from step 1, index first, as if for the first time.

⚠ THE TEST THIS PERFORMS. I cannot unknow lot 49. But I can check whether the
PIPELINE reaches the same answers without me — by starting from the ACRIS
index, routing every document by type, and measuring how much is answered
BEFORE ANY PAGE IMAGE IS OPENED.

If the index plus targeted specialist reads reproduces the closures that cost
2.7M tokens the first time, the system works. If it cannot, it does not, and
saying so is the result.

    STEP 1  LEGALS by BBL      the true document list          free
    STEP 2  MASTER join        type · date · amount · pages    free
    STEP 3  PARTIES join       every party and its role        free
    STEP 4  route by type      which specialist, what budget   free
    STEP 5  what the index alone already answers, BY FUNCTION
    STEP 6  the page budget for what remains

Steps 1-5 cost zero page-reads. That is the whole claim being tested.
"""
import collections
import json
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import doctype_registry as REG

BASE = "https://data.cityofnewyork.us/resource"
LEGALS, MASTER, PARTIES = "8h5j-fqxa", "bnx9-e6tj", "636b-3b5g"

# ⚠ WHAT ACRIS IS THE AUTHORITY FOR. Nothing outside this list belongs in a
# completeness score for an ACRIS decode — scoring it against "what does the
# hotel earn" makes a finished decode read as incomplete and sends someone
# back to re-read pages that cannot contain the answer.
FUNCTIONS = {
 "TITLE":       "who owned it, when, and how title moved",
 "DEBT":        "money lent against it and what is still owed",
 "ENVELOPE":    "how much may be built and where it came from",
 "ENCUMBRANCE": "burdens that run with the land",
 "PRIORITY":    "rank between creditors",
 "CONSENT":     "who had to agree, and who was bound without signing",
 "INCOME":      "cashflow pledged to a lender",
 "TENANCY":     "who occupies it and on what terms",
 "VALUE":       "prices, taxes and assessments",
 "PARCEL":      "the physical lot, its area and its subdivision",
 "PERMIT":      "construction and the approvals behind it",
 "IDENTIFY":    "defects in the record a careful reader would miss",
}

# which functions each doc type contributes to. Derived from the 326-claim
# decode, not guessed.
TYPE_FN = {
 "DEED": ["TITLE", "VALUE", "PARCEL"],
 "RDEED": ["TITLE", "VALUE"],
 "RPTT&RET": ["VALUE", "TITLE"],
 "RPTT": ["VALUE"],
 "MTGE": ["DEBT", "ENCUMBRANCE", "PRIORITY", "INCOME"],
 "AGMT": ["DEBT", "PRIORITY", "ENCUMBRANCE"],
 "ASST": ["DEBT"],
 "SAT": ["DEBT"],
 "AL&R": ["INCOME", "ENCUMBRANCE", "TENANCY"],
 "TL&R": ["INCOME"],
 "DEVR": ["ENVELOPE", "VALUE", "ENCUMBRANCE"],
 "AIRRIGHT": ["ENVELOPE", "VALUE"],
 "SAGE": ["ENCUMBRANCE", "CONSENT", "TENANCY"],
 "SMIS": ["ENCUMBRANCE", "CONSENT", "TENANCY"],
 "UCC1": ["DEBT"],
 "LIS": ["IDENTIFY", "TITLE"],
}


def fetch(dataset, where):
    out, off = [], 0
    while True:
        q = {"$where": where, "$order": ":id", "$limit": 1000, "$offset": off}
        url = f"{BASE}/{dataset}.json?" + urllib.parse.urlencode(q)
        with urllib.request.urlopen(
                urllib.request.Request(url), timeout=60) as r:
            b = json.loads(r.read().decode())
        out.extend(b)
        if len(b) < 1000:
            return out
        off += 1000


def chunked(dataset, ids, field="document_id"):
    out = []
    for i in range(0, len(ids), 50):
        lst = "','".join(ids[i:i + 50])
        out.extend(fetch(dataset, f"{field} in('{lst}')"))
    return out


def money(v):
    try:
        f = float(v)
        return f if f > 0 else None
    except (TypeError, ValueError):
        return None


def main():
    bbl = sys.argv[1] if len(sys.argv) > 1 else "1008000049"
    b, blk, lot = int(bbl[0]), int(bbl[1:6]), int(bbl[6:])
    print(f"COLD RUN · BBL {bbl}  (borough {b}, block {blk}, lot {lot})")
    print("=" * 70)

    print("\nSTEP 1-2 · the index, and it costs nothing\n")
    legals = fetch(LEGALS, f"borough={b} AND block={blk} AND lot={lot}")
    ids = sorted({r["document_id"] for r in legals if r.get("document_id")})
    master = {r["document_id"]: r for r in chunked(MASTER, ids)}
    print(f"  {len(ids)} documents in this parcel's ACRIS index")

    docs = []
    for d in ids:
        m = master.get(d, {})
        t = (m.get("doc_type") or "?").upper()
        spec, tier, _ = REG.route(t)
        docs.append(dict(doc=d, type=t, spec=spec, tier=tier,
                         date=(m.get("document_date") or "")[:10],
                         amt=money(m.get("document_amt")),
                         pages=int(m.get("page_count") or 0)))
    docs.sort(key=lambda r: (r["date"] or "0000", r["doc"]))
    span = [r["date"] for r in docs if r["date"]]
    print(f"  span {span[0]} to {span[-1]}  ·  "
          f"{sum(r['pages'] for r in docs):,} pages total")

    print("\nSTEP 3 · parties, also free\n")
    parties = chunked(PARTIES, ids)
    names = collections.Counter(p.get("name", "").strip().upper()
                                for p in parties if p.get("name"))
    print(f"  {len(parties)} party rows · {len(names)} distinct names")
    print("  most recurrent:")
    for n, c in names.most_common(6):
        print(f"    {c:>3}x  {n[:52]}")

    print("\nSTEP 4 · routed by type — no page has been opened\n")
    byspec = collections.Counter(r["spec"] for r in docs)
    bytier = collections.Counter(r["tier"] for r in docs)
    for s, n in byspec.most_common():
        built = "" if s in REG.BUILT else "  ⚠ specialist not built"
        print(f"  {s:<10} {n:>3} documents{built}")
    print()
    budget = sum(REG.TIER_BUDGET[r["tier"]] for r in docs)
    allpg = sum(r["pages"] for r in docs)
    for t in (REG.SIGNAL, REG.CHAIN, REG.STAMP, REG.RARE):
        if bytier[t]:
            print(f"  {t:<7} {bytier[t]:>3} docs x {REG.TIER_BUDGET[t]:>2} pages")
    print(f"\n  PAGE BUDGET {budget:,} pages  (~{budget*3100/1e6:.2f}M tokens)")
    if allpg:
        print(f"  vs {allpg:,} front-to-back — {100*(1-budget/allpg):.0f}% fewer")
    else:
        # ⚠ MEASURED, NOT ASSUMED. manifest.py's docstring claims the index
        # supplies page_count and thereby "removes the two-counter confusion
        # entirely." IT DOES NOT — MASTER returns page_count empty for every
        # document on this parcel. The count still has to be read off the
        # cover page, so the PAGE-1-OF-N vs Document-Page-Count rule stands.
        print("  ⚠ MASTER RETURNED NO page_count FOR ANY DOCUMENT — so the")
        print("    page count still has to come off the cover page, and my")
        print("    claim in manifest.py that the index removes that problem")
        print("    is WRONG. Corrected there.")

    print("\nSTEP 5 · WHAT THE INDEX ALONE ALREADY ANSWERS\n")
    fn_docs = collections.defaultdict(set)
    for r in docs:
        for f in TYPE_FN.get(r["type"], ["IDENTIFY"]):
            fn_docs[f].add(r["doc"])
    priced = [r for r in docs if r["amt"]]
    print(f"  {len(priced)} documents carry a DOLLAR AMOUNT in the index:")
    for r in priced[:9]:
        print(f"    {r['date']}  {r['type']:<9} ${r['amt']:>15,.2f}")
    if len(priced) > 9:
        print(f"    ... and {len(priced)-9} more")
    print(f"\n  function coverage from the index alone:")
    for f in FUNCTIONS:
        n = len(fn_docs.get(f, ()))
        bar = "#" * min(n, 34)
        print(f"    {f:<12} {n:>3} docs  {bar}")

    print("\n" + "=" * 70)
    print("  ⚠ EVERYTHING ABOVE COST ZERO PAGE READS.")
    print(f"    document list, types, dates, amounts, parties, routing,")
    print(f"    and a {budget:,}-page work plan — before opening one image.")


main()
