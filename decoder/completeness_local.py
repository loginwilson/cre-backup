"""THE COMPLETENESS PASS OVER EVERY CHARACTER ALREADY ON DISK.

    python completeness_local.py

⚠ THE QUESTION IS NOT "WHAT FRACTION DO WE CATCH". That number is unfalsifiable —
it can only ever be scored against words we already thought of. The question is
WHAT DOES NO READER CLAIM. So every character owned by a known pattern is masked
out and what survives is ranked by how many DOCUMENTS carry it. A phrase in one
document is one drafter; a phrase in four hundred is the form itself.

⚠ REPORTED PER DOC TYPE, BECAUSE A FUNCTION'S VOCABULARY IS TYPE-SPECIFIC. 1,180
of these documents are DEVRs. Pooled, they ARE the answer and every other type
disappears — the same homogeneity that made a one-document lexicon look complete.

⚠ AND THE DENOMINATOR TRAVELS WITH EVERY RATE. Nothing here is quotable without
the corpus and the n beside it.
"""
from __future__ import annotations

import collections, json, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import lexicon

DIRS = ("census_head", "devr_head", "devr_text")
MIN_DOCS = 25

STOP = set("""the a an and or of to in for on at by with as is are was were be been
being that this these those it its from shall will may must not no any all such
which who whom whose if then than so but nor per each other same more most any
said such herein hereof hereto thereof therein hereby said""".split())
WORD = re.compile(r"[A-Za-z][A-Za-z\-']{2,}")


def load():
    ty = json.loads((HERE / "_doctype_of.json").read_text(encoding="utf-8"))
    out = {}
    for d in DIRS:
        p = HERE / d
        if not p.exists():
            continue
        for f in p.glob("*.json"):
            doc = f.stem
            try:
                j = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            pg = j.get("pages")
            if isinstance(pg, list):
                t = " ".join((x.get("accepted_text") or "") for x in pg)
            else:
                t = j.get("text") or ""
            # ⚠ AN EMPTY READ IS NOT A DOCUMENT.
            if len(t.strip()) < 200:
                continue
            out[doc] = (ty.get(doc, "?"), t)
    return out


def owned():
    pats = []
    for g, d in (("function", lexicon.FUNCTIONS), ("mode", lexicon.MODES),
                 ("region", lexicon.REGIONS), ("reference", lexicon.REFERENCES)):
        for name, v in d.items():
            for p in v.get("patterns", []):
                pats.append((f"{g}/{name}", re.compile(p, re.I)))
    return pats


def grams(text, n=3):
    w = [x.lower() for x in WORD.findall(text)]
    w = [x for x in w if x not in STOP]
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def main():
    docs = load()
    if not docs:
        print("  no local text found")
        return 1
    by_type = collections.Counter(t for t, _ in docs.values())
    chars = sum(len(t) for _, t in docs.values())
    print(f"CORPUS {len(docs):,} documents · {chars:,} characters")
    print("  " + " ".join(f"{k}={v}" for k, v in by_type.most_common(12)))
    print()

    pats = owned()
    print(f"masking {len(pats)} patterns owned by existing readers …", flush=True)

    fired = collections.Counter()
    touched = 0
    surv = collections.defaultdict(set)          # phrase -> docs (all types)
    surv_t = collections.defaultdict(lambda: collections.defaultdict(set))
    for doc, (ty, t) in docs.items():
        marks = bytearray(len(t))
        hit = False
        for name, rx in pats:
            for m in rx.finditer(t):
                fired[name] += 1
                hit = True
                for i in range(m.start(), m.end()):
                    marks[i] = 1
        touched += hit
        left = "".join(" " if marks[i] else c for i, c in enumerate(t))
        for ph in grams(left):
            surv[ph].add(doc)
            surv_t[ty][ph].add(doc)

    print(f"  documents where SOME reader fired: {touched:,}/{len(docs):,} "
          f"({100*touched/len(docs):.0f}%)\n")
    print("  reader hits (occurrences, not documents):")
    for k, v in fired.most_common(12):
        print(f"    {k:<26}{v:>9,}")

    print(f"\nUNCLAIMED, POOLED — ranked by documents carrying it "
          f"(n={len(docs):,})")
    for ph, ds in sorted(surv.items(), key=lambda kv: -len(kv[1]))[:18]:
        print(f"    {len(ds):>5} docs  {100*len(ds)/len(docs):>4.0f}%   {ph}")

    print(f"\nUNCLAIMED, PER TYPE — the same pass, but the form of each type")
    for ty, n in by_type.most_common():
        if n < MIN_DOCS or ty == "?":
            continue
        top = sorted(surv_t[ty].items(), key=lambda kv: -len(kv[1]))[:6]
        if not top:
            continue
        print(f"\n  {ty}  (n={n})")
        for ph, ds in top:
            print(f"    {len(ds):>4}/{n:<5}{100*len(ds)/n:>4.0f}%   {ph}")

    json.dump({"documents": len(docs), "chars": chars,
               "by_type": dict(by_type), "fired": dict(fired),
               "touched": touched,
               "pooled": [[p, len(d)] for p, d in
                          sorted(surv.items(), key=lambda kv: -len(kv[1]))[:60]],
               "per_type": {ty: [[p, len(d)] for p, d in
                                 sorted(surv_t[ty].items(),
                                        key=lambda kv: -len(kv[1]))[:20]]
                            for ty in by_type if by_type[ty] >= MIN_DOCS}},
              open(HERE / "_completeness_local.json", "w"), indent=1)
    print("\nwrote _completeness_local.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
