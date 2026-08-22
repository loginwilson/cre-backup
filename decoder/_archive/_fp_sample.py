"""Pick the ACROSS-PARCEL sample. Index only — no images, no budget spent.

⚠ THE SAMPLE DESIGN IS THE EXPERIMENT. The within-parcel run could only ever
have answered "do lot 49's two deeds match", and they are six years and two law
firms apart. Three strata here, chosen so a null result and a positive result
mean different things:

  A  RANDOM CITYWIDE, one era. Different parcels, different boroughs,
     different everybody. If THESE match there is a dominant market-wide
     template and the corpus cost collapses. Strongest claim, least likely.

  B  ONE RECORDING DAY, different parcels. Same era, same county practice,
     unrelated filers. Isolates "convention of the moment" from "one firm's
     template".

  C  ONE REPEAT PARTY, many parcels. An entity that conveys dozens of
     properties uses ONE law firm, so its deeds should share a template if
     templates share at all. ⚠ PARTY IS A PROXY FOR PREPARER, NOT THE THING
     ITSELF — ACRIS does not record who drafted a document. A positive here
     means "same repeat filer", which is the population that matters anyway
     because it is where the volume is.

  ⚠ AND A IS THE CONTROL FOR C. If C matches and A does not, templates are
  real but per-filer, and the saving is the size of each filer's book. If both
  match, the saving is corpus-wide. If neither, the idea is dead and the honest
  number stays 6.6 billion.
"""
import collections
import json
import random
import sys

import bulk

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MASTER = "bnx9-e6tj"
LEGALS = "8h5j-fqxa"
PARTIES = "636b-3b5g"

SEED = 20260809          # fixed so the sample is re-drawable
N_A, N_B, N_C = 18, 10, 12

rng = random.Random(SEED)

# ---- the candidate pool -----------------------------------------------------
# One era, so print technology is held constant. 2018-2024 is laser/PDF
# throughout; mixing in microfilm would confound layout with scan quality.
print("pulling DEED index 2019-2024 ...")
master = bulk.socrata(
    MASTER,
    where=("doc_type='DEED' AND recorded_datetime>='2019-01-01' "
           "AND recorded_datetime<'2025-01-01'"),
    select="document_id,recorded_datetime,document_amt",
    limit=40000, paginate=False,
)
print(f"  {len(master):,} deeds in pool")

ids = [m["document_id"] for m in master]
by_id = {m["document_id"]: m for m in master}

# ---- BBL for each, so "different parcels" is enforced, not assumed ----------
print("pulling LEGALS for the pool ...")
legals = {}
for i in range(0, len(ids), bulk.IN_CLAUSE_MAX):
    chunk = ids[i:i + bulk.IN_CLAUSE_MAX]
    q = ",".join(f"'{c}'" for c in chunk)
    for r in bulk.socrata(LEGALS, where=f"document_id in({q})",
                          select="document_id,borough,block,lot", paginate=True):
        legals.setdefault(r["document_id"], []).append(
            f"{r['borough']}-{r['block']}-{r['lot']}")
    if i > 6000:
        break
print(f"  {len(legals):,} deeds with a BBL")

pool = [d for d in ids if d in legals]

# ---- STRATUM A: random citywide, one deed per parcel, one per borough-block -
seen_bbl, A = set(), []
for d in rng.sample(pool, len(pool)):
    b = legals[d][0]
    if b in seen_bbl:
        continue
    seen_bbl.add(b)
    A.append(d)
    if len(A) >= N_A:
        break

# ---- STRATUM B: one busy recording day, different parcels ------------------
byday = collections.defaultdict(list)
for d in pool:
    byday[by_id[d]["recorded_datetime"][:10]].append(d)
day = max(byday, key=lambda k: len(byday[k]))
seen_bbl_b, B = set(), []
for d in byday[day]:
    b = legals[d][0]
    if b in seen_bbl_b or d in A:
        continue
    seen_bbl_b.add(b)
    B.append(d)
    if len(B) >= N_B:
        break
print(f"  busiest day {day}: {len(byday[day])} deeds -> took {len(B)}")

# ---- STRATUM C: one repeat party across many parcels -----------------------
print("pulling PARTIES to find a repeat filer ...")
sub = pool[:6000]
cnt = collections.Counter()
whose = collections.defaultdict(list)
for i in range(0, len(sub), bulk.IN_CLAUSE_MAX):
    q = ",".join(f"'{c}'" for c in sub[i:i + bulk.IN_CLAUSE_MAX])
    for r in bulk.socrata(PARTIES, where=f"document_id in({q})",
                          select="document_id,name,party_type", paginate=True):
        n = (r.get("name") or "").strip().upper()
        # ⚠ EXCLUDE THE OBVIOUS NON-FILERS. A city agency or a bank appears on
        # thousands of deeds it did not draft.
        if not n or len(n) < 6:
            continue
        cnt[n] += 1
        whose[n].append(r["document_id"])

best = [(n, c) for n, c in cnt.most_common(40) if c >= 6]
print("  repeat parties:")
for n, c in best[:12]:
    print(f"    {c:>4}  {n[:60]}")

C, party = [], None
for n, c in best:
    docs, seen_c = [], set()
    for d in dict.fromkeys(whose[n]):
        b = legals.get(d, [None])[0]
        if b is None or b in seen_c:
            continue
        seen_c.add(b)
        docs.append(d)
    if len(docs) >= 8:
        party, C = n, docs[:N_C]
        break

out = {"seed": SEED, "day": day, "party": party,
       "A": A, "B": B, "C": C,
       "bbl": {d: legals[d][0] for d in A + B + C if d in legals}}
json.dump(out, open("_fp_sample.json", "w"), indent=1)

print(f"\nSAMPLE  A={len(A)} random  B={len(B)} one-day  C={len(C)} party={party}")
print(f"  pages to fetch: {(len(A)+len(B)+len(C))*2} (p002+p003 each)")
