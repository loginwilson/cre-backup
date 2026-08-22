"""THE UNIT OF WORK — one document, decoded end to end, then deleted.

    fetch pages -> read OLDEST FIRST -> claim terms/values
                -> crop the proof -> push to Supabase -> DELETE the pages

Everything in this session so far was bespoke: I hand-built agent prompts,
read prose reports, and hand-wrote claims into a Python file. That does not
scale past one parcel. This file is the same work as a REPEATABLE CONTRACT.

⚠ THE ONE CHANGE THAT MAKES IT SYSTEMISABLE. Agents have been returning
PROSE. A human reads prose; a pipeline cannot. So the contract is:

    THE AGENT RETURNS STRUCTURED CLAIMS, AND EVERY CLAIM CARRIES THE REGION
    IT WAS READ FROM.

The region is the whole game for storage. Measured on a real page:

    the page image                          68 KB
    the page, 1-bit, whole                  40 KB
    every ink band stitched                 26 KB
    THE TWO BANDS THAT CARRY THE CLAIM     6.8 KB   <- legible, verified

10x, and only the reader knows which band. I could not narrow the 132 crops
I cut today because I threw that information away — the agents knew where
they read each fact and I never asked.

⚠ SEQUENCING RULES, EACH LEARNED BY BREAKING IT TODAY.

  1 THE WORK LIST COMES FROM THE FILESYSTEM. Never hand-built, never from
    what a report says it covered. A subagent's scope statement is evidence
    about the subagent, not about the world. I told the user six times that
    instruments were missing; all were on disk; I never ran `ls`.

  2 OLDEST TO NEWEST, ONE DOCUMENT AT A TIME. Parallel reading is fine;
    parallel WRITING is not. Out-of-order writes do not leave a gap, they
    leave a plausible wrong story — that is how a "drift" in tax figures got
    reported from a sample that had 2003 and 2014 but not 1990 or 2013.

  3 CROP BEFORE DELETE, ALWAYS. A claim whose page is gone and whose crop
    was never cut is unfalsifiable: it still cites a document and a page and
    can never be checked again. Worse than no claim. Today one crop caught a
    page cite off by one AND reversed a conclusion already reported.

  4 A NEGATIVE RESULT IS A RESULT. Record pages OPENED separately from pages
    that YIELDED. Four 2011 assignments, 29 pages, zero facts — that is
    coverage, and without recording it someone reads them again.

Usage
    python decode_one.py --next            what to decode next, oldest first
    python decode_one.py --prompt <doc>    the exact agent prompt for it
    python decode_one.py --ingest <file>   load an agent's JSON back in
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PAGES = pathlib.Path("pages_out")

# ---------------------------------------------------------------------------
# THE AGENT CONTRACT. One document per agent. Structured out, no prose.
# ---------------------------------------------------------------------------
CONTRACT = """Read ACRIS document {doc} for {bbl}. Pages are at:
{folder}
There are {n} page images, p001..p{n:03d}. READ EVERY ONE, IN ORDER.

⚠ RULES
- DO NOT DELEGATE. Open each image yourself with the Read tool.
- Work front to back. Do not skip a page because it "looks like" an exhibit.
- NEVER repair a number. If two figures conflict, emit BOTH as separate
  claims and say they conflict in the note.
- A page you opened that held nothing is a RESULT. List it in pages_opened.
- Do not summarise. Do not write prose. Emit the JSON below and nothing else.

⚠ EVERY CLAIM MUST CARRY ITS REGION. When you read a fact off a page, say
WHERE on that page it sits, as a fraction of page height: "y": [0.10, 0.24].
Err wide — include the heading above the clause. A crop showing a limiting
plane without the "Lot 20" heading above it proves a plane over nothing.
The region is what lets the page image be deleted afterwards, so a claim
without one costs 20x the storage forever.

RETURN EXACTLY THIS JSON:

{{
  "document_id": "{doc}",
  "doc_type_indexed": "<what the ACRIS cover page calls it>",
  "doc_type_actual": "<what the instrument calls ITSELF in its own title;
                       these disagree often and the difference is a finding>",
  "page_count_declared": <the cover page's own "PAGE 1 OF N", or null>,
  "pages_opened": [1,2,3,...],
  "pages_empty": [<opened, nothing of substance — coverage, not a gap>],
  "claims": [
    {{
      "predicate": "<one of: consideration, consideration_recited, mortgage,
                    consolidation, tax_paid, tax_rate, rights_transferred,
                    rights_retained, rights_generated, envelope_balance,
                    far_implied, lot_area, unit_cap, easement,
                    zoning_lot_members, cross_reference, reel_page,
                    party_role, person, subdivision, property_type,
                    boundary_origin, defect, unresolved>",
      "page": 10,
      "y": [0.10, 0.24],
      "value_num": 130.0,
      "unit": "ft",
      "value_text": "<what it says, as a sentence a broker can read>",
      "verbatim": "<the exact words, quoted>",
      "effective": "2013-05-17",
      "subject_bbl": "<the lot this is ABOUT, if not the filing lot —
                      a claim found in lot 49's file is often about lot 53>",
      "functions": ["ENVELOPE","ENCUMBRANCE"],
      "note": "<why it matters, or what would mislead a careful reader>"
    }}
  ]
}}

WHAT TO LOOK FOR, in priority order:
1  MONEY. Every dollar figure and what it is CALLED. ⚠ The recital is a trap
   on this corpus: deeds recite $10 against $42,700,000 of stamps. Price
   comes from the cover-page tax stamps divided by the statutory rate.
   Face amounts of consolidated mortgages are NOT additive; stated
   outstanding balances ARE.
2  FLOOR AREA. Quote the label verbatim — "transferred", "retained",
   "generated", or a balance AFTER the transaction are four different facts
   and the label is the fact. Say which lot each number belongs to.
3  TERMS. Who is bound · must / must not / may · what · on what condition ·
   WHOSE CONSENT releases it. Write sentences, not slot names.
4  GEOMETRY. Any restriction expressed as a volume: from what elevation to
   what elevation, from what datum, over what horizontal area, how long.
   ⚠ Watch for "light, air AND VIEW" — the third word gets dropped.
5  DEFECTS. Wrong cover-page party, acknowledgment dated before the
   instrument, words disagreeing with numerals, an uncured "recites
   incorrect legal description" note, a page count that does not match.
   ⚠ On this corpus every material error so far has been in HANDWRITING.
6  INSTRUMENT STATUS. If something reads like a form or specimen, say
   whether it is EXECUTED or an UNEXECUTED BLANK that binds only if signed.
"""


def doc_pages(doc):
    d = PAGES / doc
    if not d.is_dir():
        return []
    return sorted(f for f in d.iterdir()
                  if f.is_file() and f.suffix.lower() in
                  {".png", ".jpg", ".jpeg", ".tif", ".tiff"})


def next_doc():
    """Oldest unread document. Work list comes from disk — see rule 1."""
    import ledger
    rows = ledger.build()
    for r in rows:
        if r["cov"] < ledger.DONE:
            return r
    return None


def prompt_for(doc, bbl="Manhattan Block 800 Lot 49"):
    n = len(doc_pages(doc))
    return CONTRACT.format(doc=doc, bbl=bbl, n=n,
                           folder=str((PAGES / doc).resolve()))


def ingest(path):
    """Load an agent's JSON: claims + crop regions, ready to crop and push."""
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    doc = data["document_id"]
    cs = data.get("claims", [])
    with_region = sum(1 for c in cs if c.get("y"))
    print(f"{doc}: {len(cs)} claims · {with_region} carry a crop region")
    print(f"  opened {len(data.get('pages_opened', []))} pages · "
          f"{len(data.get('pages_empty', []))} empty (coverage, not a gap)")
    if data.get("doc_type_indexed") != data.get("doc_type_actual"):
        print(f"  ⚠ TYPE MISMATCH  indexed '{data.get('doc_type_indexed')}' "
              f"vs actual '{data.get('doc_type_actual')}'")
    if with_region < len(cs):
        print(f"  ⚠ {len(cs) - with_region} claims have NO REGION — those "
              f"pages cannot be narrowed and will cost 20x forever")
    return data


def main():
    a = sys.argv[1:]
    if "--prompt" in a:
        i = a.index("--prompt")
        print(prompt_for(a[i + 1]))
    elif "--ingest" in a:
        i = a.index("--ingest")
        ingest(a[i + 1])
    else:
        r = next_doc()
        if not r:
            print("✓ nothing left — every document read")
            return
        print(f"NEXT (oldest unread):  {r['doc']}   {r['key']}   "
              f"{r['pages']} pages")
        print(f"  python decode_one.py --prompt {r['doc']}")


main()
