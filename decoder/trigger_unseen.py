"""THE HONEST TEST: the DEVR lexicon against six documents nobody has read.

⚠ WHY THE FIRST RESULT DOES NOT COUNT. trigger_probe.py scored 25/25 recall on
document 2014093000267001, and that number is worthless on its own: the trigger
phrases were written AFTER reading those pages. I built the key from the lock.
The only question that matters is whether a lexicon derived from one document
finds facts in documents it has never seen.

⚠ PREDICTIONS ARE WRITTEN BEFORE ANYTHING IS READ BY EYE. This file emits its
page-level predictions to disk and stops. Scoring happens afterwards, against
pages read independently. Reversing that order is how "holding at 1.00, 1.00,
0.88" got reported earlier in this project from the tail of a running log —
selection presented as measurement.

    OCR = SEARCHLIGHT, maximise recall, cheap, allowed to be wrong
    LLM = READER, maximise precision, expensive, used sparingly

⚠ AND OCR IS NEVER THE AUTHORITY. Pages that fire nothing are RECORDED, not
discarded. Exhibits, handwriting, tables, stamps and bad scans produce useless
OCR while carrying decisive facts — an exhibit page in the document that seeded
this lexicon held the only geometry in the instrument and would OCR to almost
nothing. A page that stays silent is a page the reader has not been TOLD about;
it is not a page that has been cleared.

    python trigger_unseen.py          writes _unseen_predictions.json
"""
import collections
import json
import pathlib
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import trigger_probe as TP

DOCS = [
    ("2008011100316001", "BK", 2008,  19),
    ("2012112000314001", "QN", 2012,  22),
    ("2008032000040001", "BX", 2008,  43),
    ("2007062501103003", "MN", 2007,   7),
    ("2016122101069004", "MN", 2017, 135),
    ("2006010302098004", "MN", 2006,  36),
]

# ── CLUSTER ROUTING ──────────────────────────────────────────────────────
# A single word is a weak signal; a NEIGHBOURHOOD OF MEANING is a strong one.
# "borrower" once means little. borrower + principal + interest + maturity on
# one page is loan economics and nothing else. Same logic per DEVR concept.
CLUSTERS = {
    "loan_economics":   ["PRINCIPAL", "INDEBTEDNESS", "BORROWER", "LENDER",
                         "MATURITY", "INTEREST"],
    "dev_rights":       ["DEVELOPMENT RIGHTS", "FLOOR AREA", "ZONING LOT",
                         "ZONING RESOLUTION", "TRANSFER"],
    "consideration":    ["CONSIDERATION", "DOLLARS", "RECEIPT", "SUFFICIENCY",
                         "PAID"],
    "legal_desc":       ["BEGINNING", "THENCE", "FEET", "INCHES", "CORNER",
                         "BOUNDED"],
    "execution":        ["WITNESS WHEREOF", "NOTARY", "ACKNOWLEDGED",
                         "PERSONALLY APPEARED", "TITLE"],
    "easement":         ["EASEMENT", "LIGHT AND AIR", "LIMITING PLANE",
                         "ELEVATION", "DATUM"],
    "restriction":      ["SHALL NOT", "COVENANT", "RESTRICTION", "BIND",
                         "SUCCESSORS"],
}
CLUSTER_MIN = 2      # how many members must appear before a page is flagged


def score_page(body):
    """Return (fired_slots, cluster_hits). Deliberately generous: this layer is
    tuned for RECALL. A false fire costs one page of reading. A miss costs a
    fact, and the whole point of the lexicon is that facts do not go missing."""
    slots = [s for s, ps in TP.TRIGGERS.items()
             if any(TP.norm(p) in body for p in ps)]
    hits = {}
    for name, terms in CLUSTERS.items():
        got = [t for t in terms if TP.norm(t) in body]
        if len(got) >= CLUSTER_MIN:
            hits[name] = got
    return slots, hits


def main():
    from rapidocr_onnxruntime import RapidOCR
    ocr = RapidOCR()
    out, t0, npages = {}, time.time(), 0

    for doc, boro, yr, expect in DOCS:
        d = pathlib.Path("devr_pages") / doc
        tifs = sorted(d.glob("*.tif"))
        if not tifs:
            print(f"  {doc}  NOT ON DISK — skipped")
            continue
        print(f"\n{doc}  {boro} {yr}  {len(tifs)} pages", flush=True)
        pages = {}
        for t in tifs:
            p = int(t.stem[1:])
            res, _ = ocr(str(t))
            body = TP.norm(" ".join(r[1] for r in res) if res else "")
            # ⚠ KEEP COORDINATES. Cropping to the neighbourhood of a phrase is
            # what turns a 659-token page into a ~160-token region, and the
            # boxes are free here — thrown away now, they cost a second OCR
            # pass over the whole corpus to recover.
            boxes = [{"t": r[1], "box": r[0]} for r in res] if res else []
            slots, clus = score_page(body)
            pages[p] = {"chars": len(body), "slots": slots,
                        "clusters": clus, "boxes": boxes, "text": body}
            npages += 1
            mark = ("*" if slots or clus else ".")
            print(mark, end="", flush=True)
        fired = [p for p, v in pages.items() if v["slots"] or v["clusters"]]
        silent = [p for p in pages if p not in fired]
        out[doc] = {"boro": boro, "year": yr, "pages": len(tifs),
                    "fired": sorted(fired), "silent": sorted(silent),
                    "detail": {str(k): {kk: vv for kk, vv in v.items()
                                        if kk != "boxes"}
                               for k, v in pages.items()}}
        print(f"\n   fired {len(fired)}/{len(tifs)}   silent {sorted(silent)}")
        # boxes are bulky; keep them beside the predictions, not inside
        pathlib.Path(f"_ocr_{doc}.json").write_text(
            json.dumps({str(k): v["boxes"] for k, v in pages.items()}))

    el = time.time() - t0
    pathlib.Path("_unseen_predictions.json").write_text(json.dumps(out, indent=1))
    print(f"\n\n{npages} pages in {el/60:.1f} min ({npages/el*3600:.0f} pg/hr)")

    tot_f = sum(len(v["fired"]) for v in out.values())
    print(f"\nPREDICTION, recorded BEFORE any of these pages is read by eye:")
    print(f"  {tot_f}/{npages} pages flagged = {tot_f/npages*100:.0f}% "
          f"-> the reduction, IF nothing was missed")
    print(f"\n  slots proposed per document:")
    for doc, v in out.items():
        s = collections.Counter()
        for pg in v["detail"].values():
            for x in pg["slots"]:
                s[x] += 1
        print(f"    {doc} {v['boro']}: {len(s)} distinct slots, "
              f"{sorted(s)[:4]}{'...' if len(s) > 4 else ''}")
    print("\n  ⚠ NOT A RESULT YET. This is the searchlight's claim about where")
    print("    to look. It becomes a measurement only after the silent pages")
    print("    are read and checked for facts it failed to point at.")


if __name__ == "__main__":
    main()
