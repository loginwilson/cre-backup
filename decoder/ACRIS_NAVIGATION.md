# Navigating ACRIS

⚠ **This file exists because every extractor in this project assumed the
document was already in hand.** Thirty-five specialists know how to read a
deed; nothing knew how to *find* one, which page of the viewer it starts on,
or that the identifier printed in the search results is not the identifier the
image endpoint wants. Learned 2026-08-09 by reading the site's own wiring —
no image requests spent.

---

## The URL surface

    /DS/DocumentSearch/BBL                            search form
    /DS/DocumentSearch/BBLResult?max_rows=99          results   (POST, form 'global')
    /DS/DocumentSearch/DocumentDetail?doc_id=<id>     indexed fields
    /DS/DocumentSearch/DocumentImageView?doc_id=<id>  the viewer
    /DS/DocumentSearch/GetImage?doc_id=<id>&page=N    ⚠ THE ONLY THROTTLED ONE

ASP.NET MVC. Search state rides in hidden fields (`hid_borough`, `hid_block`,
`hid_lot`) and every form carries a `__RequestVerificationToken`.

⚠ **`max_rows=99` is a real lever.** The default is 10. A 48-document parcel is
five page loads at the default and one at 99.

---

## ⚠ CRFN IS NOT doc_id. THEY ARE DIFFERENT NUMBERS.

    CRFN 2026000086235   ->   doc_id 2026032600589001      UCC3 TERMINATION
    CRFN 2026000013440   ->   doc_id 2026010900977002      DEED

The results table shows the **CRFN**. The image endpoint takes the **doc_id**,
which appears only inside each row's `onclick`:

    onclick="JavaScript:go_image(&quot;2026010900977002&quot;)"

⚠ **The doc_id is HTML-entity-encoded** (`&quot;`), which is how a first pass
at scraping the row returned zero matches while looking like it worked.

⚠ **BUT DO NOT SCRAPE THE ROW FOR IT.** Socrata's `document_id` on dataset
`bnx9-e6tj` **is** the doc_id, in the same `YYYYMMDDNNNNNNNNN` shape. So the
entire work list — every document on a parcel, its type, date, parties and page
count — is available **free, unthrottled, without a session**. Only the page
images are rate-limited.

    THE WORK LIST IS FREE. ONLY THE PIXELS ARE SCARCE.

That single fact should govern the harvester: decide *everything* you can from
the index before spending one image request.

---

## ⚠ THE DOCUMENT MAP — three page counts, all correct, and how to get it free

Observed on deed `2026010900977002`, all at once:

    Socrata / results table            6 pages
    cover page "Document Page Count"   4
    the viewer                         1 of 11

**They count different things, and the viewer hands you the key.** The page
`DocumentImageView?doc_id=<id>` carries hidden fields that lay out the whole
document:

    hid_TotalPages   11     everything GetImage will serve
    hid_Sup           7     supporting documents START at this page
    hid_Tax          --     absent/0 => this document HAS NO TAX RETURN
    hid_URL          /DS/DocumentSearch/DocumentImageView?doc_id=<id>&sup_page=

Which resolves to:

    pages  1-2    City cover pages     (6 indexed - 4 instrument = 2)
    pages  3-6    THE INSTRUMENT       "Document Page Count: 4"
    pages  7-11   supporting documents

    cover pages = indexed_pages - Document_Page_Count
    instrument  = [cover+1 .. indexed_pages]
    supporting  = [hid_Sup .. hid_TotalPages]
    tax return  = [hid_Tax .. ] when hid_Tax > 0

★ **This independently agrees with `coverpage.py`**, which detects 2 cover
pages on this document by barcode transitions. Two unrelated methods, same
answer.

⚠ **THIS KILLS THE RANGE SCAN — the technique that got this project blocked on
2026-08-05.** That block came from fetching 15-page ranges to *locate* an
exhibit. The location was available all along, from ONE cheap HTML page load,
with no images fetched at all. Read the map first; fetch only named pages.

## Supporting documents and tax returns

`Show Supporting Documents` = `GoToSupport('S')` -> jumps to `hid_Sup`.
`Show Tax Returns` = `GoToSupport('L')` -> jumps to `hid_Tax`.

Both are just page offsets inside the same `GetImage` sequence — **not separate
documents and not separate endpoints.**

⚠ **`hid_Tax` IS THE RP-5217 POINTER, AND THIS PROJECT HAS NEVER FETCHED ONE.**
The deed agent declares a third price witness (RP-5217 "Full Sale Price")
alongside RPTT ÷ 2.625% and RETT ÷ 0.400%, and every price derived so far has
rested on two witnesses while the third sat at a page number the viewer would
have named for free.

⚠ **AND `hid_Tax` = 0 IS ITSELF A FINDING**, as on this deed — a conveyance
with no tax return filed, consistent with its $0/$0 stamps and identical
grantor/grantee. ABSENT is an answer; it is not a gap.

---

## What a parcel actually costs

Brooklyn block 2414 lot 3 — the Domino Sugar site, Two Trees:

    48 documents · 1,944 pages · 16 distinct document types
    5 ZONING LOT DESCRIPTION · 1 DEVELOPMENT RIGHTS · 1 CONDO DECLARATION (101pp)
    1 DECLARATION at 369 pages

⚠ **The median parcel is 12 documents. This is four times that, and the page
count is far worse than four times.** A development site is exactly the parcel
this project cares about AND exactly the parcel that costs the most to acquire,
so any throughput estimate built on the median is wrong for every parcel worth
looking at.

---

## Two identifiers per lot, and the "Partial Lot" column

The results table carries a **Lot** and a **Partial / Entire Lot** flag. A
document marked `PARTIAL LOT` touches only part of the tax lot — routine on
condo and air-rights work, and it means a claim from that document must not be
attributed to the whole parcel without checking which part.
