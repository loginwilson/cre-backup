"""DID THE NEW ACRIS DOCUMENTS GET IMAGES, OR IS THE LAG A RICHMOND THING?

    python aug_imagecheck.py --n 400

Answers one question with a denominator: of documents recorded 2026-08-03..08-18,
what fraction has pages behind the image endpoint? The endpoint itself is never
in doubt - it is a pure function of doc_id - so this measures IMAGE PRESENCE,
which is the only thing a derived endpoint cannot tell you.

⚠ RANDOM SAMPLE, NOT THE HEAD. doc_id sorts by submission date, so the first N
are the oldest submissions in the window - exactly the ones most likely to be
imaged. Taking the head would manufacture the reassuring answer.

⚠ CONCURRENCY 8 - half the measured peak (amap: 16 peaked, 24 degraded). This is
a diagnostic, not acquisition; it does not need the ceiling.

⚠ WRITES ONLY TO C:. The One Touch is unplugged.
"""
from __future__ import annotations
import argparse, collections, json, pathlib, random, sys, time
from concurrent.futures import ThreadPoolExecutor
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE)); sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import docmap

SRC = HERE / "_aug_unmapped.jsonl"
OUT = HERE / "_aug_imagecheck.jsonl"

ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=400)
a = ap.parse_args()

docs = [json.loads(l) for l in SRC.open(encoding="utf-8")]
random.seed(20260818)
pick = random.sample(docs, min(a.n, len(docs)))
print(f"  population {len(docs):,} · sampling {len(pick):,}")

def one(d):
    try:
        m = docmap.fetch_map(d["doc_id"], pause=0)
        return {**d, "pages": m.get("hid_TotalPages"), "err": None}
    except Exception as e:
        return {**d, "pages": None, "err": type(e).__name__}

t0 = time.time(); res = []
with OUT.open("w", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=8) as ex:
    for i, r in enumerate(ex.map(one, pick), 1):
        f.write(json.dumps(r) + "\n"); res.append(r)
        if i % 100 == 0:
            print(f"    {i}/{len(pick)} · {(time.time()-t0)/i*(len(pick)-i):.0f}s left")

imaged = [r for r in res if r["pages"]]
noimg  = [r for r in res if r["err"] is None and not r["pages"]]
errs   = [r for r in res if r["err"]]
print(f"\n  RESULT ({time.time()-t0:.0f}s)   denominator {len(res)}")
print(f"    imaged (pages>0)   {len(imaged):>5}  {100*len(imaged)/len(res):.1f}%")
print(f"    NO IMAGE           {len(noimg):>5}  {100*len(noimg)/len(res):.1f}%")
print(f"    errors             {len(errs):>5}   {collections.Counter(r['err'] for r in errs).most_common(3)}")
if noimg:
    byday = collections.Counter(r["recorded"] for r in noimg)
    tot = collections.Counter(r["recorded"] for r in res)
    print("\n    no-image by recorded date (n = sampled that day):")
    for d in sorted(tot):
        print(f"      {d}  {byday.get(d,0):>3}/{tot[d]:<3}")
    print("\n    examples:")
    for r in noimg[:5]:
        print(f"      {r['doc_type']:<7} {r['recorded']}  {r['doc_id']}")
