"""SPINE CHECK — is this document even this parcel's?

⚠ THE CHECK NOTHING ELSE PERFORMS, AND THE ONE THAT SHOULD RUN FIRST.

Every gate I built asks whether a document is COMPLETE and READ. Not one asks
whether it BELONGS. On lot 49 that let at least five foreign documents sit in
the parcel folder, and I reported two of them to the user as "new 2026
activity on this parcel":

  2026052800492001   POWER OF ATTORNEY, BROOKLYN 7027 54, 3735 Oceanic Ave
                     between Ekaterina and Olga Yumakaeva
  2026062301264001   POWER OF ATTORNEY, BROOKLYN 2350 1016, 85 North 3 St
                     between Eli and Sabrina Wacht
  2014040900899002   $410,000,000 Deutsche Bank / 212 Fifth Avenue Owner LLC,
                     BLOCK 827 LOT 44 and BLOCK 799 LOT 12 — 1 of 59 pages
  FT_1340008617134   1979 subordination on 120-122 West 25th St = LOT 53
  FT_1670008616267   1979 in rem tax foreclosure vacate order, NO legible
                     block or lot anywhere on the page

⚠ THREE OF THOSE FIVE ARE ALSO SHORT (3 of 9, 1 of 10, 1 of 59), so a
truncation check would have flagged them — but for the wrong reason, and the
other two would have passed clean.

⚠ AND ONE FOLDER HOLDS A DIFFERENT DOCUMENT'S BODY ENTIRELY:
2023102700777001 has its own cover on p001-p002 and then eleven pages of
2023102700753001. THIRTEEN FILES AGAINST THIRTEEN CLAIMED — a page-count
check passes and the document is still wrong. Counting pages cannot detect a
substituted body. Only reading the document ID printed on each cover can.

⚠ THE COST ASYMMETRY IS WHY THIS RUNS FIRST. Reading one cover page is about
2,000 tokens. Reading a 59-page document that turns out to belong to another
parcel is about 180,000. On lot 49 the five foreign documents held 78 pages —
roughly 240,000 tokens spent proving they were irrelevant.

Every ACRIS cover page prints its own BOROUGH, BLOCK and LOT. The check is
one page and it gates everything downstream.
"""

# What a cover page must assert before any further page of it is opened.
GATE = """Open ONLY page p001 of {doc}. Do not open any other page.

Report exactly this and nothing else:

  document_id_printed : the Document ID the cover prints for ITSELF
  borough             :
  block               :
  lot                 :
  additional_lots     : every other lot in the PROPERTY DATA block
  doc_type            :
  document_date       :
  page_of_n           : the cover's own "PAGE 1 OF N"
  belongs             : true only if {bbl_borough} block {bbl_block} lot
                        {bbl_lot} appears in the PROPERTY DATA block

⚠ If document_id_printed differs from {doc}, say so — the folder may hold a
different instrument's body.
⚠ If the parcel is absent from PROPERTY DATA, STOP. Do not read further pages
and do not decode it. Report belongs=false and move on."""


def gate_prompt(doc, bbl):
    """bbl is a 10-char BBL: borough(1) block(5) lot(4)."""
    return GATE.format(doc=doc, bbl_borough=bbl[0], bbl_block=int(bbl[1:6]),
                       bbl_lot=int(bbl[6:]))


# documents proven NOT to belong to lot 49, with the evidence
FOREIGN = {
 "2026052800492001": "BROOKLYN 7027 54 — power of attorney, Yumakaeva",
 "2026062301264001": "BROOKLYN 2350 1016 — power of attorney, Wacht",
 "2014040900899002": "BLOCK 827 LOT 44 / BLOCK 799 LOT 12 — 212 Fifth Ave",
 "FT_1340008617134": "120-122 West 25th St = LOT 53, not 49",
 "FT_1670008616267": "no legible block or lot on the only page present",
}

# folders whose contents are a different document
SUBSTITUTED = {
 "2023102700777001": "p003-p013 are the body of 2023102700753001",
}


def audit():
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    import pathlib
    pages = pathlib.Path("pages_out")
    n_pages = 0
    print("SPINE CHECK · documents in this parcel's folder that are not this "
          "parcel\n")
    for d, why in FOREIGN.items():
        p = pages / d
        c = len(list(p.iterdir())) if p.is_dir() else 0
        n_pages += c
        print(f"  ⚠ {d}  {c:>3} pages   {why}")
    print(f"\n  {len(FOREIGN)} foreign documents · {n_pages} pages")
    print(f"  ~{n_pages * 3100 / 1000:.0f}k tokens would be spent proving "
          f"they are irrelevant\n")
    for d, why in SUBSTITUTED.items():
        print(f"  ⚠ {d}  SUBSTITUTED BODY — {why}")
    print("\n  ⚠ a page-count check PASSES on the substituted folder. "
          "13 files, 13 claimed.")
    print("    Only the document ID printed on each cover detects it.")


if __name__ == "__main__":
    audit()
