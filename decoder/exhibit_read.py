"""THE EXHIBIT READER — segment the instrument, then read where quantities live.

    python exhibit_read.py              # segment + extract, DEVR sample
    python exhibit_read.py --show
    from exhibit_read import segment, instrument_title, quantities

⚠ THE MEASUREMENT THAT REDEFINED THIS FILE. It was commissioned to recover the
SF for the 14 DEVR documents refusing with "no quantity". Probing them first
showed ZERO matches of `<number> square feet` across all 14 — not a binding
failure, no such string. Reading their first body page showed why:

    filed as  DEC OF DEVELOPMENT RIGHTS      (cover page, all 25)
    actually  PARTY WALL DECLARATION OF RESTRICTIONS   (12 of 25)

⚠⚠ TWELVE OF TWENTY-FIVE ARE MIS-FILED. They are party-wall agreements between
adjoining townhouses. No development right moves, so no square footage exists,
so the refusal was CORRECT and the reader was missing nothing. Building an
exhibit extractor for them would have produced nothing and taught nothing —
and had it been tuned until it produced *something*, that something would have
been noise promoted to evidence.

⇒ THE FIRST JOB HERE IS `filed_as` vs `is_a`. The cover page carries the type
the PRESENTER selected, and it is not a reading of the instrument. Every
downstream statistic keyed on doc_type inherits that error silently.

⚠ AND THE REAL SAMPLE IS SMALLER AGAIN. Of 25 documents: 12 party-wall, leaving
13 genuine rights instruments (ZLDAs, easements, agreements) of which 11 already
establish events. The true refusal rate on DEVRs is 2 of 13, not 14 of 25.

⚠ THE SECOND JOB IS SEGMENTATION, AND `"exhibit" appears on this page` IS NOT
IT. lexicon's exhibit region fires on 13/25 by that test, which counts the
sentence "as shown on Exhibit D" in the body — a REFERENCE to an exhibit, not
the exhibit. An exhibit begins where a page's HEAD is its label and runs to the
next label; only then can "the SF is in an exhibit, not the grant" be acted on.

⚠ AND SOMETIMES THE NUMBER IS NOT IN THE DOCUMENT AT ALL. 2003062701790001 is a
genuine ZLDA conveying "the Excess Development Rights" — a defined term whose
amount lives in a Land Disposition Agreement that was never recorded. The right
output is a LEAD naming the instrument to chase, never a number scraped from
nearby text because a number was expected.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
SRC = HERE / "devr_text"
OUT = HERE / "resolve" / "_exhibits.json"

# ── segmentation ────────────────────────────────────────────────────────────
COVER = re.compile(r"RECORDING\s*AND\s*ENDORSEMENT|NYCDEPARTMENT\s*OF\s*FINANCE|"
                   r"NYC\s*DEPARTMENT\s*OF\s*FINANCE", re.I)
# ⚠ ANCHORED TO THE HEAD OF THE PAGE. Unanchored, this matches "annexed hereto
# as Exhibit A" in the middle of a recital and declares the recital an exhibit.
EXH_HEAD = re.compile(r"^\W{0,40}(EXHIBIT|SCHEDULE|ANNEX|APPENDIX)\s*"
                      r"[\"'“‘]?\s*([A-Z0-9]{1,3})\b", re.I)

TITLE_WORDS = (r"DECLARATION|AGREEMENT|DEED|EASEMENT|COVENANT|RESTRICTIONS?|"
               r"CERTIFICATE|WAIVER|LEASE|ASSIGNMENT|SATISFACTION|MODIFICATION")
# The instrument names itself in its opening line. OCR eats the spaces, so the
# separator is optional throughout.
TITLE = re.compile(r"((?:[A-Z][A-Za-z]{2,}\s*){0,5}(?:" + TITLE_WORDS + r")"
                   r"(?:\s*(?:OF|AND|FOR)\s*(?:[A-Z][A-Za-z]*\s*){1,5})?)", re.I)


def segment(pages):
    """[{page, kind, label}] — kind: cover | body | exhibit."""
    out, cur = [], None
    seen_body = False
    for p in pages:
        t = (p.get("accepted_text") or "").lstrip()
        head = " ".join(t[:160].split())
        if not seen_body and COVER.search(head):
            out.append({"page": p["page"], "kind": "cover", "label": None})
            continue
        m = EXH_HEAD.match(head)
        if m:
            cur = f"{m.group(1).upper()} {m.group(2).upper()}"
        # ⚠ AN EXHIBIT DOES NOT END AT ITS FIRST PAGE. A metes description or a
        # rent roll runs for several pages with no header on the continuations;
        # the label carries forward until the next one.
        seen_body = True
        out.append({"page": p["page"], "kind": "exhibit" if cur else "body",
                    "label": cur})
    return out


def instrument_title(pages, segs):
    """What the document CALLS ITSELF, from its first body page.

    ⚠ THIS IS NOT doc_type AND THE DIFFERENCE IS THE POINT. doc_type is the
    filing category the presenter picked; this is the instrument's own name.
    """
    body = [p for p, s in zip(pages, segs) if s["kind"] == "body"]
    if not body:
        return None
    t = " ".join((body[0].get("accepted_text") or "")[:700].split())
    m = TITLE.search(t)
    if not m:
        return None
    v = " ".join(m.group(1).split()).upper().strip(" ,.")
    return v if len(v) > 6 else None


# ── quantities ──────────────────────────────────────────────────────────────
# ⚠ WIDER THAN `<number> square feet`, BECAUSE THAT WAS THE ONLY FORM READ AND
# IT IS NOT THE ONLY FORM WRITTEN. Each alternative was added from text actually
# seen in this corpus, not from imagination — an unused pattern costs nothing
# until it fires on something it should not.
UNIT = r"(square\s*feet|square\s*foot|sq\.?\s*ft\.?|s\.?\s*f\.?|zfa|bsf|gsf)"
AREA_PATTERNS = [
    # 12,345 square feet   ·   12,345 sf
    (re.compile(r"([\d,]+(?:\.\d+)?)\s*" + UNIT + r"\b", re.I), "unit_after"),
    # floor area of 12,345   ·   development rights of 12,345
    (re.compile(r"(?:floor\s*area|development\s*rights|zoning\s*floor\s*area|"
                r"excess\s*floor\s*area)\s*(?:of|equal\s*to|totall?ing|:)?\s*"
                r"(?:approximately\s*)?([\d,]{4,}(?:\.\d+)?)", re.I), "label_before"),
    # ⚠ THE COMMA-MANGLED FORM. OCR eats the decimal point ("6,26200"); the
    # comma group still fixes where it belonged. Same defect that hid 3 of the
    # 8 transfer-tax stamps on the cover page.
    (re.compile(r"([\d]{1,3}(?:,\d{3})+)\d{2}\s*" + UNIT + r"\b", re.I), "mangled"),
]
FAR = re.compile(r"\b(?:F\.?A\.?R\.?|floor\s*area\s*ratio)\s*(?:of|=|:)?\s*"
                 r"(\d{1,2}(?:\.\d{1,2})?)\b", re.I)


def quantities(pages, segs):
    """Every area/FAR figure, with page, span and which region it came from."""
    out, seen = [], set()
    kind_of = {s["page"]: s for s in segs}
    for p in pages:
        t = p.get("accepted_text") or ""
        s = kind_of.get(p["page"], {"kind": "body", "label": None})
        for rx, how in AREA_PATTERNS:
            for m in rx.finditer(t):
                raw = m.group(1)
                try:
                    v = float(raw.replace(",", ""))
                except ValueError:
                    continue
                # ⚠ A LOWER BOUND, NOT A TASTE FILTER. Below ~500 the token is a
                # section number, a year or a street width far more often than a
                # floor area, and every such admission becomes a fake transfer.
                if v < 500 or v > 5_000_000:
                    continue
                k = ("area", round(v, 2))
                if k in seen:
                    continue
                seen.add(k)
                out.append({"kind": "area", "value_num": v, "unit": "SF",
                            "page": p["page"], "region": s["kind"],
                            "exhibit": s["label"], "how": how,
                            "span": [m.start(), m.end()], "quote": m.group(0),
                            "established_by": f"text_{s['kind']}"})
        for m in FAR.finditer(t):
            v = float(m.group(1))
            if not (0.5 <= v <= 30):
                continue
            k = ("far", v)
            if k in seen:
                continue
            seen.add(k)
            out.append({"kind": "far", "value_num": v, "unit": "FAR",
                        "page": p["page"], "region": s["kind"],
                        "exhibit": s["label"], "how": "far",
                        "span": [m.start(), m.end()], "quote": m.group(0),
                        "established_by": f"text_{s['kind']}"})
    return out


def read(path):
    rec = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    pages = rec.get("pages") or []
    segs = segment(pages)
    q = quantities(pages, segs)
    return {"doc_id": rec.get("doc_id"),
            "n_pages": len(pages),
            "segments": segs,
            "exhibits": sorted({s["label"] for s in segs if s["label"]}),
            "instrument_title": instrument_title(pages, segs),
            "quantities": q}


def verify(path, rec):
    """Re-read every span. Byte-for-byte or it fails."""
    pages = {p["page"]: (p.get("accepted_text") or "")
             for p in json.loads(pathlib.Path(path).read_text(encoding="utf-8"))["pages"]}
    ok = bad = 0
    for q in rec["quantities"]:
        t = pages.get(q["page"], "")
        a, b = q["span"]
        if 0 <= a < b <= len(t) and t[a:b] == q["quote"]:
            ok += 1
        else:
            bad += 1
            q["status"] = "span_failed"
    return ok, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    files = sorted(SRC.glob("*.json"))
    recs, tok, tbad = {}, 0, 0
    for f in files:
        r = read(f)
        ok, bad = verify(f, r)
        tok += ok; tbad += bad
        recs[r["doc_id"]] = r

    print(f"EXHIBIT READER — {len(recs)} documents\n")

    # ── the finding that matters most ───────────────────────────────────────
    cov = {c["doc"]: c for c in
           json.loads((HERE / "_cover_read.json").read_text(encoding="utf-8"))}
    mism = []
    for d, r in recs.items():
        filed = (cov.get(d, {}).get("doc_type") or "").upper()
        isa = r["instrument_title"] or ""
        key = re.sub(r"[^A-Z]", "", isa)
        if key and "DEVELOPMENTRIGHTS" not in key and "ZONINGLOT" not in key \
           and "DEVELOPMENT" not in key:
            mism.append((d, filed, isa))
    print(f"  ⚠ filed_as vs is_a MISMATCH   {len(mism)}/{len(recs)}")
    print("    the cover carries the type the PRESENTER chose, not a reading "
          "of the instrument")
    for d, f_, i in mism[:6]:
        print(f"      {d}  filed '{f_[:26]}'  is '{i[:38]}'")
    if len(mism) > 6:
        print(f"      … and {len(mism)-6} more")

    seg = collections.Counter(s["kind"] for r in recs.values() for s in r["segments"])
    print(f"\n  PAGES BY REGION   " + " · ".join(f"{k} {v}" for k, v in seg.items()))
    withex = sum(1 for r in recs.values() if r["exhibits"])
    print(f"  documents with a real exhibit BLOCK   {withex}/{len(recs)}")
    print("    (lexicon's exhibit region fires 13/25 by 'the word appears on "
          "this page',\n     which counts 'as shown on Exhibit D' inside a recital)")

    q = [x for r in recs.values() for x in r["quantities"]]
    byreg = collections.Counter(x["region"] for x in q)
    byhow = collections.Counter(x["how"] for x in q)
    print(f"\n  QUANTITIES  {len(q)}   by region: "
          + " · ".join(f"{k} {v}" for k, v in byreg.items()))
    print(f"              by pattern: " + " · ".join(f"{k} {v}" for k, v in byhow.items()))
    docs_q = sum(1 for r in recs.values() if r["quantities"])
    print(f"  documents with at least one quantity   {docs_q}/{len(recs)}")

    print(f"\n  SPAN VERIFICATION   {tok}/{tok+tbad}"
          f"{'   OK' if tbad == 0 else '   ⚠ READER BUG'}")

    if a.show:
        for d, r in sorted(recs.items()):
            if not r["quantities"]:
                continue
            print(f"\n  {d}  '{r['instrument_title']}'  exhibits={r['exhibits']}")
            for x in r["quantities"][:6]:
                print(f"      {x['kind']:<5}{x['value_num']:>12,.0f} {x['unit']:<4}"
                      f" {x['page']} {x['region']:<8}{str(x['exhibit'] or ''):<12}"
                      f"{x['how']:<13}{x['quote'][:30]}")

    OUT.write_text(json.dumps(recs, indent=1), encoding="utf-8")
    print(f"\n  -> {OUT.relative_to(HERE)}")
    return 0 if tbad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
