"""Which functions appear in document types that do NOT expect them.

⚠ THE POINT. The register assigns each doc type ONE function. That assignment is
an EXPECTATION, and expectations are how a reader goes blind: if we only look for
envelope in envelope documents, an easement that moves floor area is invisible
forever. So this runs EVERY detector against EVERY type and reports the cells the
register does not predict.

⚠ TWO KINDS OF EMPTY CELL, AND THEY ARE NOT THE SAME.
   absent  — a detector ran and found nothing.
   unread  — no detector exists for that function at all.
Six detectors exist; the vocabulary has eleven functions. The blind columns of
this matrix cannot be filled by any amount of reading, and printing them as 0%
would be a lie told by omission. They are listed, not scored.
"""
import json, glob, os, sys, collections
import openpyxl
import lexicon

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = r"C:\Users\smile\Downloads\ACRIS Document Types.xlsx"

# detector keys are the lowercase of the canonical labels — one rule, no map
DETECTOR = {k: k.upper() for k in lexicon.FUNCTIONS}
ALL_FN = lexicon.CANONICAL


def expected_map():
    """code -> expected function, from Login's own register."""
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    ws = wb["ACRIS Documents"]
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        code = (row[3] or "").strip()
        fn = lexicon.canon(row[4])   # ⚠ THE one normaliser — never a local map
        if code and fn:
            out[code] = fn
    return out


def texts():
    """doc_id -> head text. Empty reads are DROPPED, never scored as absence."""
    out, blank = {}, 0
    for f in glob.glob(os.path.join(HERE, "census_head", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        t = " ".join((p.get("accepted_text") or "") for p in d.get("pages") or [])
        if len(t.strip()) < 200:          # a head that short is a failed read
            blank += 1
            continue
        out[str(d["doc_id"])] = t
    return out, blank


def main():
    exp = expected_map()
    txt, blank = texts()
    ty = json.load(open(os.path.join(HERE, "_doctype_of.json"), encoding="utf-8"))

    docs = [(d, ty.get(d), t) for d, t in txt.items() if ty.get(d)]
    untyped = len(txt) - len(docs)

    print(f"corpus: {len(txt) + blank} head reads")
    print(f"  dropped, read failed (<200 chars) : {blank}")
    print(f"  dropped, doc_type unknown         : {untyped}")
    print(f"  SCORED                            : {len(docs)}")
    print()

    fired = collections.defaultdict(lambda: collections.Counter())
    n = collections.Counter()
    hits = collections.defaultdict(list)
    for doc, t, text in docs:
        n[t] += 1
        for name in lexicon.fire(text, "function"):
            fn = DETECTOR[name]
            fired[t][fn] += 1
            hits[(t, fn)].append(doc)

    detected = [DETECTOR[k] for k in lexicon.FUNCTIONS]
    blind = [f for f in ALL_FN if f not in detected]

    cols = [f for f in ALL_FN if f in detected]
    MIN = 3
    types = sorted([t for t in n if n[t] >= MIN], key=lambda t: -n[t])

    print(f"MATRIX — % of documents firing each function ({MIN}+ docs per type)")
    print("  □ = expected by the register   ● = NOT expected -> hidden function")
    print()
    print("  " + "type".ljust(10) + "n".rjust(5) + "".join(c[:8].rjust(11) for c in cols))
    for t in types:
        row = f"  {t:<10}{n[t]:>5}"
        for c in cols:
            pct = 100.0 * fired[t][c] / n[t]
            mark = "□" if exp.get(t) == c else ("●" if pct else " ")
            row += f"{(f'{pct:.0f}%' if pct else '-'):>9} {mark}"
        print(row)

    print()
    print("UNEXPECTED FIRINGS, ranked by how often the register is wrong")
    rows = []
    for t in types:
        for c in cols:
            if exp.get(t) == c or not fired[t][c]:
                continue
            rows.append((fired[t][c] / n[t], fired[t][c], n[t], t, c, exp.get(t, "?")))
    rows.sort(reverse=True)
    for frac, k, tot, t, c, e in rows[:30]:
        print(f"  {t:<10} register says {e:<9} but {c:<9} fires on "
              f"{k:>3}/{tot:<3} ({frac*100:.0f}%)")

    print()
    print(f"⚠ BLIND — no detector exists, so these are `unread`, NOT absent:")
    print("   " + "  ".join(blind))
    print(f"   {len(blind)} of {len(ALL_FN)} functions. Any type whose register function is one")
    print("   of these cannot be confirmed or contradicted by this run at all.")
    unconfirmable = sorted({t for t in types if exp.get(t) in blind})
    print(f"   types in this corpus that land there: {len(unconfirmable)} — "
          + " ".join(unconfirmable))

    json.dump({"n": dict(n), "fired": {t: dict(v) for t, v in fired.items()},
               "expected": exp, "blind": blind,
               "hits": {f"{t}|{c}": v[:5] for (t, c), v in hits.items()}},
              open(os.path.join(HERE, "_hidden_function.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
