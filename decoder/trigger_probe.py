"""CAN OCR FIND A PHRASE IT CANNOT TRANSCRIBE?

⚠ THE QUESTION, PRECISELY. OCR was measured on this corpus at 0.57 span
location and its numbers were unusable — which killed it as a TRANSCRIBER.
That verdict was then quietly generalised to "OCR is no good here", and a
different task was never tested:

    TRANSCRIBE   reproduce every character correctly          measured 0.57
    LOCATE       does this page contain "IN WITNESS WHEREOF"  NEVER MEASURED

The second is far easier. A trigger phrase is long, distinctive and
redundant — losing a third of its characters still leaves it recognisable,
whereas losing one digit of 155,503.36 makes it worthless. So a page-level
phrase index may work at an accuracy that is hopeless for reading values.

⚠ WHY THIS MATTERS MORE THAN THE TWO TRIAGE RULES THAT DIED TODAY. Byte-size
triage was a proxy for ink and it discarded the smallest page in the document,
which held the only easement geometry. Front-and-back triage was a proxy for
structure and it discarded the middle, which held the upzoning clause. A
phrase is not a proxy for anything: "in consideration of" IS the consideration
clause. That is the whole reason it deserves a test rather than a guess.

⚠ AND IT IS SCORED AGAINST PAGES ALREADY READ BY EYE, NOT AGAINST ITSELF.
Document 2014093000267001 was read page by page on 2026-08-10 and it is
recorded below which pages carried which fact. Anything else is the run
grading its own homework.

    python trigger_probe.py
"""
import json
import pathlib
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOC = "2014093000267001"
PAGES = pathlib.Path("devr_pages") / DOC

# ── GROUND TRUTH: read by eye, page by page. See the docstring. ──────────
# Pages NOT listed here were either read and found empty (18, 25, 27) or not
# read at all — and "not read" is recorded as unknown, never as absent.
TRUTH = {
    1:  ["rptt_stamp", "rett_stamp", "granting_lot", "receiving_lot"],
    2:  ["owner_party", "developer_party", "instrument_title"],
    3:  ["retained_rights", "related_instrument", "zr_citation"],
    4:  ["consideration_recital", "quantity_basis", "zr_citation"],
    5:  ["floor_area_cap"],
    8:  ["upzoning_allocation", "separate_filing_required"],
    12: ["rights_excluded", "enlargement_right"],
    21: ["signatory"],
    26: ["zoning_lot_declaration", "covenant_runs_with_land", "date_blank"],
    28: ["metes_and_bounds", "easement_volume"],
    30: ["easement_volume"],
}
READ_AND_EMPTY = {18, 25, 27}

# ── THE LEXICON. Every phrase below was seen on a real page of this
#    document. None was invented from knowledge of how contracts usually read.
TRIGGERS = {
    "rptt_stamp":             ["REAL PROPERTY TRANSFER TAX"],
    "rett_stamp":             ["REAL ESTATE TRANSFER TAX"],
    "granting_lot":           ["PROPERTY DATA", "ENTIRE LOT"],
    "receiving_lot":          ["PROPERTY DATA", "ENTIRE LOT"],
    "instrument_title":       ["ZONING LOT DEVELOPMENT", "WITNESSETH"],
    "owner_party":            ["HEREINAFTER REFERRED TO AS", "HAVING AN ADDRESS AT"],
    "developer_party":        ["HEREINAFTER REFERRED TO AS", "HAVING AN ADDRESS AT"],
    "retained_rights":        ["RETAINED DEVELOPMENT RIGHTS"],
    "related_instrument":     ["PURCHASE AND SALE AGREEMENT"],
    "zr_citation":            ["ZONING RESOLUTION", "SECTION 23-90"],
    "consideration_recital":  ["IN CONSIDERATION OF", "TEN DOLLARS"],
    "quantity_basis":         ["TRANSFERS, ASSIGNS AND CONVEYS",
                               "AVAILABLE DEVELOPMENT RIGHTS"],
    "floor_area_cap":         ["MAXIMUM PERMISSIBLE AMOUNT OF FLOOR AREA",
                               "CERTIFIED BY AN ARCHITECTURAL FIRM"],
    "upzoning_allocation":    ["UPZONING"],
    "separate_filing_required": ["SEPARATE AND INDEPENDENT",
                                 "BUILDING DEPARTMENT"],
    "rights_excluded":        ["SHALL NOT INCLUDE", "PARTY WALL"],
    "enlargement_right":      ["ADDITIONAL PARCEL"],
    "signatory":              ["IN WITNESS WHEREOF", "MANAGING MEMBER"],
    "zoning_lot_declaration": ["SECTION 12-10", "ONE ZONING LOT",
                               "DECLARATION OF SINGLE ZONING LOT"],
    "covenant_runs_with_land": ["COVENANT RUNNING WITH THE LAND"],
    "date_blank":             ["DAY OF SEPTEMBER"],
    "metes_and_bounds":       ["BEGINNING AT A POINT", "THENCE"],
    "easement_volume":        ["LOWER LIMITING PLANE", "LIGHT AND AIR EASEMENT"],
}


def norm(s):
    """⚠ NORMALISE BEFORE MATCHING OR THE TEST MEASURES THE WRONG THING.
    OCR splits words at line ends, doubles spaces and confuses punctuation. A
    raw substring search would score misses that a human would call hits, and
    the conclusion would be about whitespace rather than about legibility."""
    return re.sub(r"[^A-Z0-9 ]", " ", re.sub(r"\s+", " ", s.upper())).strip()


def main():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    tifs = sorted(PAGES.glob("*.tif"))
    print(f"{DOC} · {len(tifs)} pages · OCR for PHRASE PRESENCE, not transcription\n")

    text, t0 = {}, time.time()
    for t in tifs:
        p = int(t.stem[1:])
        res, _ = ocr(str(t))
        text[p] = norm(" ".join(r[1] for r in res) if res else "")
        print(f"  p{p:03d} {len(text[p]):>6} chars", flush=True)
    el = time.time() - t0
    print(f"\n  {len(tifs)} pages in {el:.0f}s  ({len(tifs)/el*3600:.0f} pg/hr)\n")
    pathlib.Path("_trigger_ocr.json").write_text(json.dumps(text))

    # ── did the lexicon find what the eye found? ──────────────────────────
    hit = miss = 0
    print(f"{'page':>5} {'slot':<24}{'found':>7}   phrase")
    print("-" * 74)
    for pg, slots in sorted(TRUTH.items()):
        body = text.get(pg, "")
        for s in slots:
            got = next((p for p in TRIGGERS.get(s, []) if norm(p) in body), None)
            if got:
                hit += 1
            else:
                miss += 1
            print(f"{pg:>5} {s:<24}{'YES' if got else 'no':>7}   {got or ''}")
    tot = hit + miss
    print("-" * 74)
    print(f"  RECALL {hit}/{tot} = {hit/tot:.2f}   (fraction of KNOWN facts a "
          f"phrase scan would have led us to)")

    # ── and does it fire where there is nothing? ──────────────────────────
    print(f"\n  pages read by eye and found EMPTY: {sorted(READ_AND_EMPTY)}")
    for pg in sorted(READ_AND_EMPTY):
        body = text.get(pg, "")
        fired = [s for s, ps in TRIGGERS.items() if any(norm(p) in body for p in ps)]
        print(f"    p{pg:03d}: {'FALSE FIRE -> ' + ', '.join(fired) if fired else 'silent (correct)'}")

    # ── what would a phrase scan have SKIPPED? the number that decides it ──
    print()
    fires = {p for p in text
             if any(norm(x) in text[p] for ps in TRIGGERS.values() for x in ps)}
    known = set(TRUTH)
    print(f"  pages firing any trigger : {len(fires)}/{len(tifs)}")
    print(f"  known-claim pages missed : {sorted(known - fires) or 'NONE'}")
    print("\n  ⚠ A single missed claim page is a failure, not a rounding error —")
    print("    that is exactly how the byte-size rule lost the easement geometry.")


if __name__ == "__main__":
    main()
