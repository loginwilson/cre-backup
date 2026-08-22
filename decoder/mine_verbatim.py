"""MINE THE VERBATIM ALREADY IN THE DATABASE — vocabulary we have paid for and never read.

    python mine_verbatim.py

⚠ WHY. 18,264 rows of `decoder_facts` carry a `verbatim` field with
confidence='read' — actual sentences lifted off actual pages, each with a page
number. That is a vocabulary corpus sitting in Supabase that no reader has ever
been scored against. It costs no OCR and no acquisition.

⚠ WHAT IT IS AND IS NOT. Every row is a BSA `condition_imposed` — so this is a
deep, narrow corpus: one source, one predicate. It can prove what the ENTITLEMENT
and term vocabularies are missing. It CANNOT stand in for ACRIS prose, and any
rate from it belongs to BSA conditions, not to documents in general. Stated here
so the number cannot travel without its corpus.

⚠ THE METHOD IS THE COMPLETENESS PASS, NOT A RECALL SCORE. Asking "what fraction
do we catch" tells you nothing about the words you never thought of. So every
character a known reader claims is MASKED OUT, and what survives is ranked by how
many documents it appears in. Frequent survivors are the vocabulary we do not
have.
"""
from __future__ import annotations

import collections, json, re, sys, urllib.request

sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import lexicon
from to_supabase import URL, H

PAGE = 1000
STOP = set("""the a an and or of to in for on at by with as is are was were be been
being that this these those it its from shall will may must not no any all such
which who whom whose if then than so but nor per each other same more most
""".split())


def pull():
    """⚠ PAGINATED WITH AN ORDER. Offset paging without one silently duplicates
    and drops rows on this stack — the trap already paid for on Socrata."""
    out, off = [], 0
    while True:
        u = (f"{URL}/rest/v1/decoder_facts?select=source,source_doc_id,page,"
             f"predicate,verbatim&order=fact_hash&limit={PAGE}&offset={off}")
        rows = json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers=H), timeout=120))
        out += rows
        if len(rows) < PAGE:
            break
        off += PAGE
        if off % 5000 == 0:
            print(f"  pulled {off:,}", flush=True)
    return out


def owned_patterns():
    """Every compiled pattern any reader currently owns."""
    pats = []
    for group, d in (("function", lexicon.FUNCTIONS), ("mode", lexicon.MODES),
                     ("region", lexicon.REGIONS), ("reference", lexicon.REFERENCES)):
        for name, v in d.items():
            for p in v.get("patterns", []):
                pats.append((f"{group}/{name}", re.compile(p, re.I)))
    return pats


PHRASE = re.compile(r"[A-Za-z][A-Za-z\-']{2,}")


def phrases(text, n=3):
    w = [x.lower() for x in PHRASE.findall(text)]
    w = [x for x in w if x not in STOP]
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def main():
    print("pulling decoder_facts …", flush=True)
    rows = [r for r in pull() if (r.get("verbatim") or "").strip()]
    src = collections.Counter(r["source"] for r in rows)
    pred = collections.Counter(r["predicate"] for r in rows)
    docs = {r["source_doc_id"] for r in rows}
    print(f"\n{len(rows):,} verbatim rows · {len(docs):,} documents")
    print(f"  sources    : {dict(src)}")
    print(f"  predicates : {dict(pred.most_common(4))}")
    chars = sum(len(r["verbatim"]) for r in rows)
    print(f"  {chars:,} characters of real page text — no OCR, no acquisition\n")

    pats = owned_patterns()
    print(f"testing {len(pats)} existing patterns against it")

    fired = collections.Counter()
    claimed = unclaimed = 0
    masked_docs = collections.defaultdict(set)
    for r in rows:
        t = r["verbatim"]
        hit = False
        marks = bytearray(len(t))
        for name, rx in pats:
            for m in rx.finditer(t):
                fired[name] += 1
                hit = True
                for i in range(m.start(), m.end()):
                    marks[i] = 1
        claimed += hit
        unclaimed += (not hit)
        # ⚠ MASK WHAT IS OWNED; RANK WHAT SURVIVES.
        left = "".join(" " if marks[i] else c for i, c in enumerate(t))
        for ph in phrases(left):
            masked_docs[ph].add(r["source_doc_id"])

    print(f"  clauses where SOME reader fired : {claimed:,} "
          f"({100*claimed/len(rows):.0f}%)")
    print(f"  clauses no reader touched       : {unclaimed:,} "
          f"({100*unclaimed/len(rows):.0f}%)\n")
    print("  which readers fired:")
    for k, v in fired.most_common(10):
        print(f"    {k:<26}{v:>7,}")

    print(f"\nUNCLAIMED LANGUAGE — ranked by how many DOCUMENTS carry it")
    print("  (a phrase in one document is one drafter; in hundreds it is the form)")
    top = sorted(masked_docs.items(), key=lambda kv: -len(kv[1]))[:28]
    for ph, ds in top:
        print(f"    {len(ds):>5} docs   {ph}")

    json.dump({"rows": len(rows), "documents": len(docs), "chars": chars,
               "claimed": claimed, "unclaimed": unclaimed,
               "fired": dict(fired),
               "top_unclaimed": [[p, len(d)] for p, d in top],
               "corpus": "decoder_facts.verbatim — BSA condition_imposed only; "
                         "rates belong to this corpus and must not travel"},
              open("_verbatim_mine.json", "w"), indent=1)
    print("\nwrote _verbatim_mine.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
