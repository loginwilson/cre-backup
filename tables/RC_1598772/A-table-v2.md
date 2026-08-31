# RC_1598772 — Deed with developer's restrictive covenant scheme

Wood Harmon Richmond Realty Company → Minnie A. Sweeney · Richmond · 2 pages, native
3296×5132 · package `99318c29d4d4f79c…` · class `DEED-RESTRICTIVE-COVENANT` (m1)

Re-emission of my sealed v3 table into the v5 row. Reading carried over; rects, ISO dates
and rd BBLs added from the artifact.

```
instrument: 1911-04-14
acknowledged: 1911-04-18
recorded: 1911-04-25
expires: 1915-01-01
```

`acknowledged` is read `18` and the day is crossed by the descender of "County" in the venue
line above it. `15` is a live alternative I cannot eliminate from this raster; both fall
inside the instrument→recording window, so the calendar does not discriminate either. Cited
`uncertain` with a rect on E16.

## The table

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | p1 · [0.182,0.277,0.910,0.352] · flourish · "known and designated as lot**s** No. Sixteen and Seventeen (16, 17) in Block 403 … on a certain plan of lots called South New York, Addition Number Four … filed or intended to be filed in the Clerk's Office of Richmond County aforesaid, July 5, 1907, as map no. 995 B" | 1911-04-14 | instrument | | IDENTITY | ASSERT | 5004030016, 5004030017 | asserted by: Wood Harmon Richmond Realty Company  about: the premises | 100 ft × 40 ft | rd carries the two BBLs; the document's own designation is "lots Sixteen and Seventeen (16, 17) in Block 403" on filed map no. 995 B, which is **not in rd**. Filing is *declined*, not asserted — "filed **or intended to be filed**" (card 5, third state). Lot names carry copperplate lead-in flourishes, measured at 1.8% of region width against 22.1% for a confirmed strike on the same page | The premises are lots 16 and 17 in block 403 on a map the deed will not confirm was ever filed. |
| E2 | p1 · [0.187,0.245,0.905,0.268] · plain · "does hereby grant and release unto the said part**y** of the second part, **her** heirs and assigns forever, **all its right, title and interest in and to** all that certain piece or parcel of land" | 1911-04-14 | instrument | | TITLE | TRANSFER | 5004030016, 5004030017 | Wood Harmon Richmond Realty Company → Minnie A. Sweeney | UNKNOWN(no estate named — the deed says "all its right, title and interest" and nowhere recites a fee) | "Together with the appurtenances and all the estate and rights of the party of the first part"; habendum runs to her heirs and assigns forever, and is **unqualified** because the printed subjection at E8 was struck. No covenant of seisin and no warranty | A grant-and-release of whatever interest the company held. Not a warranty deed. |
| E3 | p1 · [0.182,0.215,0.910,0.250] · plain · "in consideration of the sum of **One** Dollar, lawful money of the United States and other valuable considerations" | 1911-04-14 | instrument | | VALUE | ASSERT | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | $1.00 USD stated; remainder UNKNOWN("other valuable considerations" not quantified anywhere) | recited as paid. rd `amount` reads `$0.00` — disagrees with the recital; both stand, neither corrected (card 9) | A nominal dollar plus unquantified other consideration. |
| E4 | p1 · [0.187,0.708,0.905,0.737] · plain · "the said part**y** of the second part, for **herself, her** heirs, executors, administrators and assigns, do**th** hereby covenant and agree to and with the said party of the first part, its successors and assigns" | 1911-04-14 | instrument | 1915-01-01 | ENCUMBRANCE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company, its successors and assigns | UNKNOWN(a burden, not a measured quantity) | the covenant binds heirs, executors, administrators and assigns on both sides, so it runs with the land. E5–E7 and E9–E12 are what it constrains; this row is the burden itself | The buyer covenants back to the seller, and the burden runs with the land until 1915. |
| E5 | p1 · [0.187,0.728,0.905,0.750] · plain · "will erect or permit on any part of the herein-described premises any building except a detached or semi-detached dwelling house, and no such dwelling house shall be built for use and occupancy of more than two families except as hereinafter provided" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | max 2 families per dwelling house | "except as hereinafter provided" points forward to E13, which operates on other land, not on these lots | Detached or semi-detached houses only, never more than two families. |
| E6 | p1 · [0.187,0.745,0.905,0.785] · plain · "shall cost not less than **Two Thousand ($2000.)** dollars if built for use and occupancy of one family only; or if built as a double house, for use and occupancy of two families, or as a double tenement, it shall cost not less than **Three Thousand ($3,000.)** dollars" | 1911-04-14 | instrument | 1915-01-01 | COST | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | $2,000 USD minimum; $3,000 USD minimum | one duty with two thresholds, so one row (card 2). The thresholds vary by **family count**, not by street — the spec predicted variation by street and this document does not do that. Filed COST per framework.md's function table and COST-vs-VALUE boundary, which name this exact clause; the framework's own worked row files it ENVELOPE | A floor on construction cost: $2,000 for one family, $3,000 for two. |
| E7 | p1 · [0.187,0.778,0.905,0.818] · plain · "such building shall not be less than two stories in height, shall have a cellar, shall not have what is commonly known as a flat roof, nor shall such building nor any part thereof, excepting steps, piazzas, bay or oriel windows … be erected or maintained upon any part of said premises within **fifteen (15)** feet of the line of **Heberton Avenue**" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 15 ft setback; ≥2 storeys | steps, piazzas, bay and oriel windows and "other usual projections" may encroach the setback. A second setback line was left blank and struck, so only Heberton Avenue is restricted | Fifteen feet back from Heberton Avenue, two storeys minimum, cellar, no flat roof. |
| E8 | p1 · [0.182,0.622,0.907,0.657] · struck · "subject, however, to all assessments that have become a lien since the ___ day of ___ 19__" | 1911-04-14 | instrument | | ENCUMBRANCE | STRUCK | 5004030016, 5004030017 | Wood Harmon Richmond Realty Company → Minnie A. Sweeney | UNKNOWN(nothing measured) | a continuous ruled line through every word and all three blanks, overshooting the last character into the right margin; longest uninterrupted dark run 22.1% of region width against 1.8% for the flourishes at E1. **Not** an assertion that no assessments exist (card 5, first state). Stroke *order* is unrecoverable from a bitonal scan, so *struck-before-execution* stays uncertain (card 1) | The printed clause taking the premises subject to assessment liens was ruled out, leaving the habendum unqualified. |
| E9 | p2 · [0.194,0.048,0.925,0.110] · struck · "must stand at least **sixty** feet from **Heberton Avenue** ~~and at least (___) feet from~~, nor shall more than one such dwelling house and one such stable or garage be erected or permitted on each parcel of land **Twenty** feet in width by **One Hundred** feet in depth" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 60 ft setback for outbuildings; 1 dwelling + 1 outbuilding per 20 ft × 100 ft | a second distance was struck, measured at 7.5% of region width. The premises are 40 ft wide, so **two** dwellings and two outbuildings are permitted here — the density unit is smaller than the parcel conveyed | Outbuildings sixty feet back; one house and one outbuilding per twenty feet of frontage. |
| E10 | p2 · [0.205,0.127,0.920,0.168] · plain · "nor shall any fence be built, constructed or maintained on any part of said premises unless the nature, kind, shape and material be first made known and shown to one of the officers of the said WOOD HARMON RICHMOND REALTY COMPANY, and have received his sanction and approval in writing" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | UNKNOWN(no dimension or standard stated) | **a private discretionary approval right, which has no home in the eleven.** Filed ENVELOPE because it constrains what may be built; filing it there loses the veto holder, the fact that no standard is stated, and that no time limit binds the company's decision. `PERMIT` is government-only; `ENTITLEMENT` is a right attaching to land | No fence without an officer's written approval, on no stated standard. |
| E11 | p2 · [0.205,0.163,0.920,0.258] · plain · "nor shall there be erected or maintained upon said premises … any milkman's stable, livery stable, carpenter shop, piggery, slaughter house, smith shop, forge, furnace, steam engine, brass foundry, tin, nail or other iron factory … nor any hospital, and that she will not use or permit to be used the said premises or any part thereof for the use or carrying on of any trade or business" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | ~25 named trades, then a general ban | one prohibition, list in terms (card 2). Also bans "any building for the storing, keeping or maintaining any fire-engine or truck or hose-carriage", and manufactories for gunpowder, glue, varnish, vitriol, ink, turpentine, bone-boiling, tanning, brewing, distilling, oil and lampblack. The closing catch-all makes the named list redundant against itself | Twenty-five named nuisance trades, then a catch-all forbidding any trade or business at all. |
| E12 | p2 · [0.205,0.288,0.920,0.328] · plain · "neither said part**y** of the second part nor **her** heirs, executors, administrators or assigns, will sell or suffer or allow to be sold on the premises hereby conveyed, or any part thereof, any strong or spirituous liquors, or ale, beer or wine, or intoxicating liquors of any kind" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | UNKNOWN(a prohibition, not a measure) | introduced as a **further** covenant, so a separate operative act from E11 | No liquor may be sold on the premises. |
| E13 | p2 · [0.205,0.325,0.920,0.412] · plain · "The party of the first part, however, shall have the right to erect or maintain or to permit to be erected or maintained on any part of South New York, Addition Number Four, buildings in blocks for the use and occupancy of one or more families, or detached or semi-detached buildings for the use and occupancy of more than two families … but no such building shall be erected unless the plans and specifications for same shall have been first submitted to and approved by said party of the first part" | 1911-04-14 | instrument | | ENVELOPE | CREATE | SET: all lots in plat 995 B (South New York, Addition Number Four, filed map no. 995 B, Richmond County Clerk) | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | UNKNOWN(no dimension stated) | the grantor exempts itself from E5, E7 and E9 everywhere else in the plat, subject only to its own plan approval — a second homeless private veto. `until` left **blank**: the sunset at E14's neighbour reaches "all restrictions and covenants", and a reserved right is arguably neither; I will not write a date I cannot point at (card 4) | The developer may build denser and taller elsewhere in the same subdivision, answering only to itself. |
| E14 | p2 · [0.205,0.405,0.920,0.435] · plain · "the party of the first part shall also have the right to use and to grant the right to use for all purposes other than those business purposes specifically mentioned above, all of the lots on Richmond Turnpike, Merrill Avenue and Watchogue Road and the lots on Wyona Avenue between Willow Brook and Hawthorne Avenue" | 1911-04-14 | instrument | | ENTITLEMENT | CREATE | UNPLACED | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | UNKNOWN(no count of lots stated) | **`bbls` could not be filled.** The document places this precisely — four named streets and a segment between two cross streets — but nothing states those streets are on plat 995 B, so `SET: all lots in plat 995 B` would be a derivation. framework.md names this exact clause as prose that "reaches no parcel". `UNPLACED` is the least-wrong fannable value and it is wrong: the document does place it | The developer may license business uses on four named streets, on land this row cannot reach. |
| E15 | p2 · [0.205,0.468,0.920,0.508] · plain · "the party of the first part **has not done or suffered anything whereby the said premises have been encumbered in any way whatever** excepting as to said restrictions and limitations" | 1911-04-14 | instrument | 1915-01-01 | TITLE | ASSERT | 5004030016, 5004030017 | asserted by: Wood Harmon Richmond Realty Company  about: the premises | UNKNOWN(an absence, not a measure) | a real asserted absence (card 5, second state), and a narrow one — limited to the grantor's **own** acts and expressly excepting the restrictions this deed creates. `until` set to 1915-01-01 on the **literal** reading that the sunset reaches "all restrictions and covenants in this instrument contained", which this is; flagged rather than resolved | The grantor says only that it has not encumbered the land. It says nothing about anyone before it. |
| E16 | p2 · [0.185,0.668,0.925,0.730] · uncertain · "On the **18**th day of **April** … one thousand nine hundred and **eleven** before me personally came **Leonidas Keever** … that he resides in the City of New York, Borough of Brooklyn and that he is the **Vice-President** of WOOD HARMON RICHMOND REALTY COMPANY … that the seal affixed to said instrument was such corporate seal; that it was so affixed by order of the Board of Directors" | 1911-04-18 | acknowledgment | | IDENTITY | ASSERT | 5004030016, 5004030017 | asserted by: Leonidas Keever  about: Wood Harmon Richmond Realty Company | UNKNOWN(a capacity, not a measure) | executed 1911-04-14 by Leonidas Keever, Vice-President, attested by John H. Storer, Secretary, under corporate seal; sworn four days later before Elizabeth Roth, Commissioner of Deeds in and for New York City. Venue "State of New York, City of New York, County of New York" — all three lines stand, their apparent cancellations measured at 1.6% of region width. **Day mark uncertain:** `18` read, `15` not eliminable, descender of "County" crosses the digits | The company executed by its Vice-President under seal; he swore to his capacity in Manhattan four days later. |

## Registry lane

Not one of the eleven — these ask about the instrument, not a parcel. Numbered `R` so they
are not scored as event rows.

| # | citation | date | basis | function | mode | bbls | parties | terms |
|---|---|---|---|---|---|---|---|---|
| R1 | p2 · [0.161,0.820,0.461,0.912] · plain · "Recorded April, 25, 1911 at 9 a.m." | 1911-04-25 | — | — | — | INSTRUMENT | Richmond County Clerk → the record | The registry's own act. Recording date **and time**; rd carries the date and not the time. Never an event date (card 10) |
| R2 | p2 · [0.161,0.820,0.461,0.912] · plain · "C. Livingston Bostwick, for Wood, Harmon & Co., Broadway, N.Y. City." | 1911-04-25 | — | — | — | INSTRUMENT | return-to: C. Livingston Bostwick for Wood, Harmon & Co. | The only agent address in the document. **"Wood, Harmon & Co." is not the grantor** — the grantor is Wood Harmon Richmond Realty Company |

## SEARCH RECORD — fee, tax and revenue stamps

**Not a row.** This is card 5's first state — *I found nothing* — and an absence has no quote,
so it cannot carry a citation and must not sit in a table whose every row asserts one. It was
a row in my first draft; the CITE check was right to refuse it.

Method: ink projection over the delivered native page raster (3296 × 5132), threshold
luminance < 128, per-row ink counted against 2% of band width, runs ≥ 10 rows reported.

| region | dpi | found |
|---|---|---|
| p1 · [0.00,0.00,0.18,1.00] | 330 | ink 0.047%, 1 cluster y 0.002–0.005 — the "Vol. 396 PG 1" vendor caption overlay. No stamp |
| p1 · [0.90,0.00,1.00,1.00] | 330 | ink 0.006%, 0 clusters. Empty. No stamp |
| p1 · [0.00,0.00,1.00,0.045] | 330 | ink 0.522%, below cluster threshold because the marks are sparse rather than line-scale: the vendor caption, the handwritten volume numeral "396", one diagonal pen stroke, and the leaf numeral "1". No stamp |
| p1 · [0.00,0.93,1.00,1.00] | 330 | ink 0.038%, 0 clusters. Empty. No stamp |
| p2 · [0.00,0.00,0.18,1.00] | 330 | ink 0.072%, 3 clusters y 0.002–0.005, 0.015–0.018, 0.024–0.027 — the "Vol. 396 PG 2" caption and the handwritten leaf numeral "2". No stamp |
| p2 · [0.90,0.00,1.00,1.00] | 330 | ink 0.415%, 19 clusters y 0.072–0.206+ — all last words of justified body lines, crop-verified: "house", "et in", "and", "LTY", "said", "orge,", "king", "ring", "any". No stamp |
| p2 · [0.00,0.00,1.00,0.045] | 330 | ink 0.240%, below cluster threshold: the vendor caption and the leaf numeral "2". No stamp |
| p2 · [0.00,0.93,1.00,1.00] | 330 | ink 0.000%. Wholly empty. No stamp |

**No fee, tax or revenue stamp appears anywhere in either margin, at the head or at the foot
of either page.** The document does not assert their absence; I looked and did not find them.

⚠ **The dpi column is not reproducible through `docpkg --rect` on this document, and 330 is
an approximation of a number that does not exist.** The full-page build hands over the native
bitmap unresampled — 3296 × 5132, which is what I measured. The `--rect` zoom path instead
calls `get_pixmap(dpi=…, clip=…)` on the **page box**, and the box is 10.00 × 17.00 in: it
renders 3000 × 5100 at 300 dpi. Native is therefore **329.6 dpi across and 301.9 dpi down** —
the embedded bitmap's aspect differs from the page box's by **9.2%**, the same class of
distortion `docpkg` was changed to stop delivering, still present on the crop path. So a
referee who re-renders `p1 · [0.00,0.00,0.18,1.00] --dpi 330` gets an image 9.2% narrower
than the one these percentages were taken from, and will not reproduce them. Falsifying this
negative requires the native page raster, not a re-render. I have stated 330 because the
column requires one number and the run-length measurements are taken along the horizontal
axis; the vertical figure is 302.

## Index check (card 9)

| rd field | rd says | document says | result |
|---|---|---|---|
| `parcels[0].bbl` | `5004030016` | "lots No. Sixteen and Seventeen (16, 17) in Block 403" | agrees |
| `parcels[1].bbl` | `5004030017` | same clause | agrees |
| `doc_type` | `DEED` | printed heading "DEED." | agrees — spec §1's untested prediction holds on m1 |
| `recorded` | `4/25/1911` | "Recorded April, 25, 1911 **at 9 a.m.**" | agrees; document adds a time rd lacks |
| `book` / `page` | `396` / `1` | handwritten "396" at head of p1; "1" and "2" at the leaf corners | agrees |
| `amount` | `$0.00` | "One Dollar … and other valuable considerations" | **disagrees.** Both stand |
| `parties` | `[]` | six named: Wood Harmon Richmond Realty Company, Minnie A. Sweeney, Leonidas Keever, John H. Storer, Elizabeth Roth, C. Livingston Bostwick | `NOT_CHECKABLE` |
| `instrument` | `""` | no instrument number on either page | `NOT_CHECKABLE` |
| filed map no. 995 B | **absent from rd** | "map no. 995 B", filed 1907-07-05 | `NOT_CHECKABLE` — spec §3 predicted this and it holds |

The "Vol. 396 PG 1" caption in each page's top-left corner is a modern overlay burned into
the vendor scan, not part of the 1911 record. It is not independent evidence of the locator.

## Page counts (card 8)

Page numbers "1" and "2". **No denominator anywhere** — the instrument states no total and
neither does the endorsement. Two images supplied. Completeness is proved by the sentence
running across the break: p1 ends "which barn or stable or garage, if erected," and p2 opens
"must stand at least sixty feet from". Not by a count.

## Brief

On 14 April 1911 the Wood Harmon Richmond Realty Company granted and released lots 16 and 17
in block 403 — forty feet of frontage on the west side of Heberton Avenue, a hundred feet
deep — to Minnie A. Sweeney of Brooklyn for one dollar and other valuable considerations.
Keever, its Vice-President, swore to it in Manhattan on the 18th; C. Livingston Bostwick
lodged it for Wood, Harmon & Co. and the county recorded it on the 25th at nine in the
morning.

The deed conveys "all its right, title and interest" and names no estate, gives no covenant
of seisin and no warranty, so what Sweeney received cannot be read off its face. What the
company took was the covenant, and the covenant runs backwards: the buyer promises the
seller. Detached or semi-detached only, never more than two families, two storeys, a cellar,
no flat roof, fifteen feet off Heberton and sixty for the stable, one house per twenty feet
of frontage, two thousand dollars minimum and three for a double house, no fence without an
officer's written approval, no liquor, and no trade or business after twenty-five named ones.

The company exempted itself in the same breath, reserving the right to build in blocks and
for more than two families anywhere else in South New York Addition Number Four, subject
only to its own approval of the plans, and to license business uses on four named streets.

And all of it expires. One sentence gives the scheme three years and eight months, to
1 January 1915 "and no longer" — which makes it a device for selling a subdivision still on
the market, not a permanent servitude. Two smaller things: the printed clause taking the
premises subject to assessment liens was ruled out in ink, so the habendum is unqualified —
which is not a claim that no assessments existed; and the grantor's covenant against
encumbrances reaches only its own acts.
