"""THE CHECKS THAT SHOULD HAVE RUN AT FETCH TIME.

Three defects found this session were all mechanically detectable and none was
caught by a person looking:

  1 TRUNCATION   a document declares N pages on its cover and has fewer on disk
  2 FETCHED-NOT-READ  a folder full of images with no claim sourced from it
  3 ORPHAN CITE  a claim citing a page that does not exist on disk

The first is the important one. Every ACRIS cover page prints its own page
count. That makes the count a SELF-CHECK: the document tells you how much of
itself you should have. Nobody was asking.

Run:  python integrity.py
"""
import collections
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import claims as K

PAGES = pathlib.Path("pages_out")
IMG = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

# ⚠ TWO DIFFERENT COUNTERS LIVE ON AN ACRIS COVER PAGE AND THEY DISAGREE
# BY DESIGN. My first version of this check conflated them and immediately
# produced FIVE FALSE POSITIVES:
#
#   "PAGE 1 OF 11"            <- counts EVERYTHING, including the 1-2
#                                NYC-generated cover/continuation pages
#   "Document Page Count: 9"  <- counts the INSTRUMENT ONLY, excluding them
#
# An agent caught it by verifying the arithmetic held exactly on six
# documents: files_on_disk == PAGE-OF-N, every time. So PAGE 1 OF N is the
# authority here and Document Page Count is not.
#
# ⚠ THE LESSON IS NOT THE ARITHMETIC. A new check that fires immediately
# feels like it is working. Five of its first eight hits were my own bug,
# and I reported them as findings before anyone verified them.
#
# PAGE_OF_N: total images the cover page says the fetch should contain.
# A document absent here is NOT CHECKED, which is not the same as intact.
PAGE_OF_N = {
    "2023110100486011": 20,
    "2023110100486006": 9,
    "2023110100486003": 4,
    "2023110100486004": 4,
    "2025101700864001": 5,
    "2025101700864002": 11,
    "2013081200922003": 61,   # 55 main + 1 supporting cover + 4 affidavit
                              # + p056, an Exhibit A continuation the two
                              # stated counts both omit. Verified page by page.
    # ⚠ THE THREE CONFIRMED TRUNCATIONS
    "2023110100486007": 9,
    "2023110100486008": 9,
    "2025101700864003": 14,
    "2009122400274001": 5,    # ⚠ 1 image on disk. Everything but the tax
                              # stamps is gone.
    "2010102601040005": 9,
    "2010102601040002": 8,
    "2010102601040003": 18,
    "2010102601040004": 9,
    "2010110900202001": 2,
    "2014080700619001": 8,
    "2012101500666006": 39, "2012101500666007": 49, "2012101500666008": 22,
    "2019071700601001": 12, "2019071700601002": 20,
    "2020061600455001": 19, "2020081400407002": 14,
}
DECLARED = PAGE_OF_N

# documents whose declared count legitimately differs from the file count
# because the cover page and its continuation are extra images
COVER_SLACK = 4


def on_disk():
    n = collections.Counter()
    if not PAGES.exists():
        return n
    for p in PAGES.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMG:
            n[p.parent.name] += 1
    return n


def page_num(s):
    m = re.match(r"^p0*(\d+)$", str(s).strip())
    return int(m.group(1)) if m else None


def main():
    disk = on_disk()
    read = {c["document_id"] for c in K.CLAIMS if c["evidence"] == "read"}
    any_claim = {c["document_id"] for c in K.CLAIMS}

    print(f"INTEGRITY · {len(disk)} documents on disk · "
          f"{sum(disk.values())} page images\n")

    # ---- 1 TRUNCATION ---------------------------------------------------
    short, ok, unchecked, over = [], [], [], []
    for doc, n in sorted(disk.items()):
        d = DECLARED.get(doc)
        if d is None:
            unchecked.append(doc)
        elif n < d:
            short.append((doc, d, n))
        elif n > d:
            # ⚠ ADDED AFTER 2013081200922003. The check only ever tested for
            # TOO FEW pages, so an EXTRA page passed silently — and there the
            # unaccounted page was the one listing the burdened tax lots.
            over.append((doc, d, n))
        else:
            ok.append(doc)

    print("1 · TRUNCATION — cover-page count vs files on disk")
    if short:
        print(f"  ⚠ {len(short)} TRUNCATED")
        for doc, d, n in short:
            print(f"      {doc}  declares {d:>3}  has {n:>3}   "
                  f"MISSING {d - n}")
    else:
        print("  no truncation among checked documents")
    if over:
        print(f"  ⚠ {len(over)} UNACCOUNTED PAGES — more files than declared")
        for doc, d, n in over:
            print(f"      {doc}  declares {d:>3}  has {n:>3}   "
                  f"EXTRA {n - d}")
    print(f"  {len(ok)} verified intact")
    print(f"  ⚠ {len(unchecked)} NOT CHECKED — no cover-page count "
          f"transcribed yet")
    print("     NOT CHECKED is not the same as intact. Every one of these "
          "could be short\n     and nothing here would know.")

    # ---- 2 FETCHED BUT NEVER READ ---------------------------------------
    never = sorted(d for d in disk if d not in read)
    idx_only = [d for d in never if d in any_claim]
    print(f"\n2 · FETCHED BUT NEVER READ — {len(never)} documents / "
          f"{sum(disk[d] for d in never)} pages")
    print("  a folder of images proves a FETCH. only a claim proves a READING.")
    if idx_only:
        print(f"  ⚠ {len(idx_only)} of them carry index-derived claims, which "
              f"can read as coverage:")
        for d in idx_only:
            print(f"      {d}  {disk[d]:>3} pages")

    # ---- 3 ORPHAN CITATIONS ---------------------------------------------
    orphans = []
    for c in K.CLAIMS:
        doc, pg = c["document_id"], page_num(c.get("page"))
        if pg is None or doc not in disk:
            continue
        if pg > disk[doc]:
            orphans.append((c["claim_id"], doc, c["page"], disk[doc]))
    print(f"\n3 · ORPHAN CITATIONS — claims citing a page not on disk")
    if orphans:
        print(f"  ⚠ {len(orphans)}")
        for cid, doc, pg, have in orphans:
            print(f"      {cid}  cites {doc} {pg}  but only {have} pages exist")
        print("  ⚠ an orphan is EITHER a bad cite OR a truncated fetch. "
              "Both matter.")
    else:
        print("  none — every cited page exists")

    # ---- verdict ---------------------------------------------------------
    print("\n" + "-" * 68)
    fails = len(short) + len(orphans) + len(over)
    print(f"HARD FAILURES {fails}   ·   UNVERIFIABLE {len(unchecked)} "
          f"documents lack a declared count")
    print(f"READ COVERAGE {len(read)}/{len(disk)} documents "
          f"({100 * len(read) // max(1, len(disk))}%)")
    if fails:
        print("⚠ do not treat this parcel as fully decoded")


main()
