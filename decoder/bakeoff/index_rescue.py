"""HOW MUCH OF WHAT THE ENGINES MISS DOES THE ACRIS INDEX ALREADY KNOW?

    python index_rescue.py

⚠ THE INDEX IS A SECOND WITNESS THAT COSTS NOTHING TO CALL. It carries doc_type,
document_date, recorded_datetime, reel/page (or CRFN), party names and
borough/block/lot for ALL 17M documents, independent of anything OCR produces.
So an artifact an engine missed is not automatically lost - for a whole class of
fields, the answer is already sitting in the selection mapping.

This splits every CRITICAL artifact into three buckets and then asks, for each
engine, how many of ITS misses fall in each:

  INDEX      the index supplies it directly - a miss here is recoverable with
             no model, no escalation, no human
  AMOUNT     the index HAS the column and it is a lie on historical documents -
             document_amt is 0 on 100% of microfilm deeds, so these must come
             from the page even though the field exists
  PAGE-ONLY  notary, title company, loan number, recording tax, covenants,
             dimensions - nothing outside the document records them

⚠ THE AMOUNT BUCKET IS THE TRAP AND IS KEPT SEPARATE ON PURPOSE. Counting it as
"index-recoverable" would claim the pipeline can skip reading prices, which is
the single most valuable thing on the page and the one the index reports as
zero. Treating a 0 as a value is how a $500,000 mortgage becomes free.
"""
import collections
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import score as S

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
DOCS = [("FT_1680008647768", "answer_key_testdoc.json", "film"),
        ("BK_6730047100023", "answer_key_bookdoc.json", "book"),
        ("2015022400608001", "answer_key_moderndoc.json", "digital")]
ENGINES = ["tesseract", "rapidpool", "ppv6*", "qwen"]

# Fields the ACRIS index supplies directly, from its own datasets:
# Master (doc_type, dates, reel/page, crfn) · Parties (names, addresses) ·
# Legals (borough, block, lot).
INDEX = {
    "doc_id", "doc_type", "title", "instrument", "crfn",
    "doc_date", "exec_date", "exec_month", "year", "rec_date", "recorded",
    "reel", "reel_page", "rec_book", "rec_page",
    "borough", "county", "block", "lot", "note_block", "note_lot", "section",
    "mortgagor", "mortgagor1", "mortgagor2", "mortgagor_addr",
    "mortgagee", "mortgagee_addr", "mortgagee_st", "to_party", "to_citibank",
}
# ⚠ present in the index and WRONG on historical documents - see docstring.
AMOUNT = {"mtg_amount", "amount_figs", "amount_words"}


def text(eng, doc, page):
    tags = ["ppv6-rot", "ppv6"] if eng == "ppv6*" else [eng]
    for t in tags:
        d = OUT / t / doc
        if not d.exists():
            continue
        stem = page[:-4] if page.endswith(".png") else page
        fs = sorted(d.glob(stem + "*.txt"))
        if fs:
            return " ".join(f.read_text(encoding="utf-8", errors="replace")
                            for f in fs)
    return None


def bucket(i):
    return "INDEX" if i in INDEX else ("AMOUNT" if i in AMOUNT else "PAGE-ONLY")


def main():
    arts, universe = [], collections.Counter()
    for doc, kf, label in DOCS:
        key = {k: v for k, v in
               json.loads((HERE / "keys" / kf).read_text(encoding="utf-8")).items()
               if not k.startswith("_")}
        for page in sorted(key):
            if any(text(e, doc, page) is None for e in ENGINES):
                continue
            hay = {e: S.norm(text(e, doc, page) or "") for e in ENGINES}
            for a in key[page]["artifacts"]:
                if a["tier"] != "CRITICAL":
                    continue
                b = bucket(a["id"])
                universe[b] += 1
                st = {e: S.found(hay[e], a) for e in ENGINES}
                arts.append((label, page, a, b, st))

    tot = sum(universe.values())
    print(f"  {tot} CRITICAL artifacts on pages every engine produced\n")
    print("  WHERE THE TRUTH CAN COME FROM")
    for b in ("INDEX", "AMOUNT", "PAGE-ONLY"):
        print(f"    {b:<10} {universe[b]:>4}  {universe[b]/tot*100:>4.0f}%")

    print("\n  PER ENGINE: what it missed, and whether the index covers it")
    print(f"    {'engine':<12}{'missed':>7}{'INDEX':>8}{'AMOUNT':>8}"
          f"{'PAGE-ONLY':>11}{'unrecoverable':>15}")
    for e in ENGINES:
        miss = [r for r in arts if not r[4][e]]
        c = collections.Counter(r[3] for r in miss)
        # ⚠ "unrecoverable" = missed AND not in the index. Everything else has a
        # second witness; this is the number escalation actually has to solve.
        unrec = c["AMOUNT"] + c["PAGE-ONLY"]
        print(f"    {e:<12}{len(miss):>7}{c['INDEX']:>8}{c['AMOUNT']:>8}"
              f"{c['PAGE-ONLY']:>11}{unrec:>15}")

    allmiss = [r for r in arts if not any(r[4].values())]
    print(f"\n  MISSED BY EVERY ENGINE: {len(allmiss)}")
    for label, page, a, b, st in allmiss:
        print(f"    [{b:<9}] {label:<7} {page:<9} {a['id']:<14} "
              f"{str(a['value'])[:40]}")
    idx = sum(1 for r in allmiss if r[3] == "INDEX")
    print(f"\n  of those, {idx} are INDEX fields - recoverable with no model at all")
    print(f"  and {len(allmiss)-idx} genuinely need the page")


if __name__ == "__main__":
    main()
