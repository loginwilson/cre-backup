"""Pull the ACRIS index for every recording that has NO retrievable image.

    python pull_index_noimage.py [n]

⚠ FOR THESE DOCUMENTS THE INDEX IS NOT A SUPPLEMENT, IT IS THE RECORD. 174,086
recordings (1.03%) return ACRIS's placeholder instead of a page — 108,817 with
hid_TotalPages 0 and 65,269 from the microfilm era at -1. Most are tax liens,
but 19,712 DEEDS and 16,440 MORTGAGES are in the set, and no image of them will
ever exist. Treating "no image" as "no data" would silently drop a deed.

⚠ AND ITS PROOF IS THE QUERY, NOT A CROP. A read claim cites page and region and
needs the image kept forever to be checkable. An index claim cites dataset +
document_id + field, which anyone can re-run for free. That is stronger, not
weaker — see acquire_index.py.

Reads the id list produced by the no-image scan rather than re-walking
acris_maps.jsonl, which costs four minutes to recompute something already on
disk.
"""
import collections
import json
import pathlib
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import acquire_index as A

IDS = HERE / "_noimage_ids.txt"
OUT = HERE / "index_noimage.jsonl"


def main():
    if not IDS.exists():
        raise SystemExit(f"  {IDS.name} missing — run the no-image scan first")
    ids = [x for x in IDS.read_text(encoding="utf-8").split("\n") if x.strip()]
    if len(sys.argv) > 1:
        ids = ids[:int(sys.argv[1])]
    print(f"  {len(ids):,} image-less documents\n")

    t0 = time.time()
    docs = A.acquire(ids)
    print(f"  pulled 5 index surfaces in {time.time()-t0:.0f}s")

    with open(OUT, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps({"document": d,
                                "claim": A.to_event_claim(d)}) + "\n")

    # ⚠ COVERAGE PER SURFACE, NOT A SINGLE "DONE". A document can carry a master
    # row and no parties; reporting one number would hide exactly the gap that
    # matters for role assignment.
    got = {k: sum(1 for d in docs if d[k]) for k in
           ("master", "parties", "legals", "references", "remarks")}
    print("\n  coverage")
    for k, v in got.items():
        print(f"    {k:<12} {v:>8,}/{len(docs):,}   {100*v/len(docs):>5.1f}%")

    # ⚠ THE ONE THAT MATTERS FOR FUSION: a document whose parties carry a
    # party_type is a document whose ROLES came from a structured source rather
    # than from word order in damaged OCR.
    roles = collections.Counter()
    for d in docs:
        for p in d["parties"]:
            roles[p.get("party_type")] += 1
    print(f"\n  party_type distribution (the third fusion channel): {dict(roles)}")
    noparty = [d["document_id"] for d in docs if not d["parties"]]
    print(f"  documents with NO party row: {len(noparty):,}")

    tc = collections.Counter((d["master"] or {}).get("doc_type") for d in docs)
    print(f"\n  types: {dict(tc.most_common(8))}")
    print(f"\n  -> {OUT.name}  ({OUT.stat().st_size/1e6:.0f} MB)")


if __name__ == "__main__":
    main()
