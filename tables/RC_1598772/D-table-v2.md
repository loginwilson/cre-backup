# RC_1598772 — event table (v2 schema)

Extractor D. Re-emission of my sealed v3-era table into the new row shape. Same
reading; rects and rd BBLs added by going back to the artifact.

```
instrument: 1911-04-14
acknowledged: 1911-04-18
recorded: 1911-04-25
expires: 1915-01-01
```

A fourth date is on the face and is none of these: `July, 5, 1907`, the filed-map
date. It has no label slot, as the class spec §4 predicts.

**rd** (`registration.json`) carries `parcels: 5004030016, 5004030017`. Those are the
BBLs written below. The document's own designation is **lots 16 and 17 in Block 403,
Borough of Richmond**, on a plan called South New York, Addition Number Four, filed or
intended to be filed as map no. 995 B — that designation is context and is never
composed into a BBL here.

**Granularity rule I applied** (card 2, stated so it can be attacked as a rule rather
than row by row): *one row per operative obligation × function*. Function is a machine
field and takes exactly one value, so a single covenant sentence that constrains form,
use and spend cannot be one row. Within a function I merge: the two cost floors are one
row, the twenty-odd prohibited trades are one row, the building-form constraints are
one row.

---

## Events

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | p1 · [0.18,0.116,0.95,0.145] · plain · "WOOD HARMON RICHMOND REALTY COMPANY, a corporation duly organized and existing under and by virtue of the Laws of the State of New York" | 1911-04-14 | instrument | | IDENTITY | ASSERT | 5004030016, 5004030017 | asserted by: the instrument  about: Wood Harmon Richmond Realty Company | 1 entity | Printed in caps on p1 and repeated four times on p2. **This is not "The Wood, Harmon Company"** — that name appears only as the survey client and the return-to firm. No corporate address anywhere. rd `parties[]` is empty, so NOT_CHECKABLE. | The grantor states it is a New York corporation. |
| E2 | p1 · [0.22,0.145,0.90,0.183] · plain · "MINNIE A. SWEENEY, residing at No. 409 Third Street, Borough of Brooklyn, City and State of New York" | 1911-04-14 | instrument | | IDENTITY | ASSERT | 5004030016, 5004030017 | asserted by: the instrument  about: Minnie A. Sweeney | 1 person, 1 address | Typed. Every printed `part___` blank is hand-completed `y` (singular) and every pronoun blank `her` / `herself` / `she`; `do___` completed `th`. One grantee, female. Only party address in the instrument besides the endorsement. rd `parties[]` empty — NOT_CHECKABLE. | The grantee is one woman of 409 Third Street, Brooklyn. |
| E3 | p1 · [0.51,0.282,0.78,0.299] · flourish · "Sixteen and Seventeen (16, 17)" | 1911-04-14 | instrument | | IDENTITY | ASSERT | 5004030016, 5004030017 | asserted by: the instrument  about: lots 16 and 17 in Block 403 | 2 lots, 1 filed map | **The marks on the two lot words are copperplate lead-in flourishes, not cancellations.** In the cited rect the horizontals are three short letter-attached strokes with white gaps; in the genuine strike at p1 [0.33,0.633,0.79,0.647] one ruled line spans the region edge to edge. Parcel definition depends on the map: p1 [0.15,0.309,0.95,0.350] · plain · "filed or intended to be filed in the Clerk's Office of Richmond County aforesaid, July, 5, 1907, as map no. 995 B" — card 5 case 3, the document DECLINES to confirm the filing while stating date and number. Map number is not in rd. | The parcel is lots 16 and 17 on a 1906 survey the deed will not confirm was filed. |
| E4 | p1 · [0.18,0.215,0.92,0.245] · plain · "in consideration of the sum of One Dollar, lawful money of the United States and other valuable considerations" | 1911-04-14 | instrument | | VALUE | ASSERT | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | $1 USD stated; remainder UNKNOWN(the deed quantifies "other valuable considerations" nowhere) | Nominal recital; not the price. rd `amount` reads `$0.00`, agreeing with neither figure. Both stand, neither corrected. | One dollar and unstated other consideration. |
| E5 | p1 · [0.18,0.243,0.92,0.280] · plain · "does hereby grant and release unto the said part y of the second part, her heirs and assigns forever, all its right, title and interest" | 1911-04-14 | instrument | | TITLE | TRANSFER | 5004030016, 5004030017 | Wood Harmon Richmond Realty Company → Minnie A. Sweeney | 2 lots; 40 ft frontage on the westerly side of Heberton Avenue by 100 ft deep | Bargain-and-sale form: "all its right, title and interest", no warranty of quantum. Habendum "unto the said part y of the second part, her heirs and assigns forever" at p1 [0.19,0.620,0.85,0.632] = fee in form. Extended by the appurtenances clause at p1 [0.19,0.601,0.92,0.612], which names no specific appurtenance. Description at p1 [0.15,0.380,0.92,0.525] runs between lots 15 and 18 on the plan, qualified "be said measurements and area more or less." | The company conveys the two lots to Minnie A. Sweeney in fee. |
| E6 | p1 · [0.33,0.633,0.79,0.647] · struck · "subject, however, to all assessments that have become a lien since the" | 1911-04-14 | instrument | | ENCUMBRANCE | STRUCK | 5004030016, 5004030017 | asserted by: the instrument  about: the conveyed premises | 1 clause removed | The printed habendum qualifier is ruled out, with separate short rules through the trailing `day`, `of` and `19` blanks. Left standing it would have taken the grantee subject to assessment liens, so it changes what the instrument does (card 3). ⚠ **When** it was ruled out is not recoverable — these scans are bitonal and stroke order is unrecoverable, so *struck-before-execution* stays uncertain (card 1). | The clause taking the conveyance subject to assessment liens was ruled out. |
| E7 | p1 · [0.19,0.691,0.95,0.712] · plain · "for herself, her heirs, executors, administrators and assigns, do th hereby covenant and agree to and with the said party of the first part, its successors and assigns" | 1911-04-14 | instrument | 1915-01-01 | ENCUMBRANCE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney and her heirs, executors, administrators and assigns → Wood Harmon Richmond Realty Company and its successors and assigns | 1 covenant scheme | The burden-runs-with-the-land row, separate from the content rows E8–E17. Binds successors on both sides — this is what makes the restrictions run rather than being personal. `until` is sourced from p2 [0.19,0.440,0.95,0.463] · plain · "All restrictions and covenants in this instrument contained shall continue in force until the first day of January, 1915, and no longer." | Restrictions are imposed as a burden running to both sides' successors. |
| E8 | p1 · [0.19,0.734,0.95,0.748] · plain · "any building except a detached or semi-detached dwelling house" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 1 permitted building type; 2 storeys minimum | Merged form constraints, one obligation about what the building may look like: detached or semi-detached only, and at p1 [0.19,0.797,0.95,0.822] · plain · "shall not be less than two stories in height, shall have a cellar, shall not have what is commonly known as a flat roof". Bears on OCCUPANCY (a *dwelling*). Nothing was built here, so never AS_BUILT. | Only a detached or semi-detached dwelling, two storeys, with a cellar and no flat roof. |
| E9 | p1 · [0.19,0.747,0.95,0.759] · plain · "no such dwelling house shall be built for use and occupancy of more than two families except as hereinafter provided" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 2 families maximum per dwelling house | "except as hereinafter provided" points forward to E18, whose reservation on its face reaches this parcel. | No more than two families per dwelling house. |
| E10 | p1 · [0.19,0.759,0.95,0.772] · plain · "shall cost not less than Two Thousand ($2000.) dollars if built for use and occupancy of one family only" | 1911-04-14 | instrument | 1915-01-01 | COST | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | $2,000 USD minimum, one family; $3,000 USD minimum, two families | One duty varying by occupancy, so one row (card 2). Second threshold at p1 [0.19,0.783,0.95,0.797] · plain · "or as a double tenement, it shall cost not less than Three Thousand ($3,000.) dollars". Written `($2000.)` without a comma and `($3,000.)` with one. A duty to spend, not money that moved. ⚠ Filed COST on the eleven's own wording; the class spec and the framework's worked example both put cost floors under ENVELOPE — see the report. | A house must cost at least $2,000 for one family, $3,000 for two. |
| E11 | p1 · [0.19,0.825,0.95,0.850] · plain · "be erected or maintained upon any part of said premises within fifteen ( 15 ) feet of the line of Heberton Avenue" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 15 ft setback | Written twice, words and figures, same hand. Excepted: "steps, piazzas, bay or oriel windows, and other usual projections appurtenant thereto". A second building line was offered by the form and ruled out — p1 [0.15,0.848,0.50,0.862] · struck · "( ) feet of the line of", with "nor within" also ruled at p1 [0.62,0.836,0.80,0.850]. Its blank was never filled, so striking it changed nothing the instrument does; kept here rather than given its own row (card 3). "Heberton Avenue" itself at p1 [0.35,0.836,0.62,0.851] is flourished, not struck. | Buildings must stand 15 feet back from Heberton Avenue. |
| E12 | p2 · [0.19,0.049,0.72,0.063] · plain · "which barn or stable or garage, if erected, must stand at least sixty feet from Heberton Avenue" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 60 ft setback | Applies only to an outbuilding "appurtenant to a private residence" (p1). Second street reference ruled out at p2 [0.15,0.062,0.42,0.079] · struck · "( ) feet from", with "and at least" ruled at p2 [0.62,0.050,0.95,0.064]; blank never filled, so it stays in terms. | An outbuilding must stand 60 feet back from Heberton Avenue. |
| E13 | p2 · [0.19,0.078,0.95,0.101] · plain · "nor shall more than one such dwelling house and one such stable or garage be erected or permitted on each parcel of land Twenty feet in width by One Hundred feet in depth" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 1 dwelling plus 1 outbuilding per 20 ft by 100 ft | The density unit is a 20 by 100 parcel; the land conveyed is 40 by 100. How the two combine is UNKNOWN — arithmetic gives two dwellings, the document does not perform it and I will not. | One house and one outbuilding per 20 by 100 foot parcel. |
| E14 | p2 · [0.19,0.129,0.95,0.163] · plain · "nor shall any fence be built, constructed or maintained on any part of said premises unless the nature, kind, shape and material be first made known and shown to one of the officers of the said WOOD HARMON RICHMOND REALTY COMPANY, and have received his sanction and approval in writing" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 1 prior-written-approval requirement | ⚠ A **private discretionary approval right**, held by an officer personally, in writing, with no stated standard and no appeal. PERMIT is government-only and ENVELOPE captures the constraint while losing the veto holder. Spec §6 lists this as still homeless; this row is the evidence. | No fence without an officer's written approval. |
| E15 | p2 · [0.19,0.155,0.95,0.240] · plain · "nor shall there be erected or maintained upon said premises or any part thereof any milkman's stable, livery stable, carpenter shop, piggery, slaughter house, smith shop, forge, furnace, steam engine, brass foundry, tin, nail or other iron factory ... nor any hospital" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | about 20 enumerated establishments plus 2 catch-alls | One prohibition, list in terms (card 2). Full list also names manufactories for gunpowder, glue, varnish, vitriol, ink or turpentine, boiling of bones, dressing or tanning of skins, hides or leather, brewery, distillery, oil or lampblack factory, any noxious or dangerous trade, any building storing a fire-engine, truck or hose-carriage, and any hospital. Framed as erecting or maintaining buildings, so it bears on ENVELOPE. | A long list of trades, a hospital and a fire-engine house are barred. |
| E16 | p2 · [0.19,0.234,0.95,0.256] · plain · "she will not use or permit to be used the said premises or any part thereof for the use or carrying on of any trade or business" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | all trade and business prohibited | Distinct obligation from E15 and broader: E15 bars erecting or maintaining named buildings, this bars *using* the land for any trade at all. The `s` of "she" is a handwritten fill on a printed `___he`. | The premises may not be used for any trade or business. |
| E17 | p2 · [0.19,0.304,0.95,0.328] · plain · "will sell or suffer or allow to be sold on the premises hereby conveyed, or any part thereof, any strong or spirituous liquors, or ale, beer or wine, or intoxicating liquors of any kind" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney and her heirs, executors, administrators or assigns → Wood Harmon Richmond Realty Company | all liquor sale prohibited | Its own covenant sentence, separate from E7's. Bars selling only, not possession or consumption. | No liquor may be sold on the premises. |
| E18 | p2 · [0.19,0.325,0.95,0.382] · plain · "The party of the first part, however, shall have the right to erect or maintain or to permit to be erected or maintained on any part of South New York, Addition Number Four, buildings in blocks for the use and occupancy of one or more families, or detached or semi-detached buildings for the use and occupancy of more than two families" | 1911-04-14 | instrument | 1915-01-01 | ENTITLEMENT | CREATE | SET: all lots in plat 995 B | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 1 reserved development right, unbounded within the plat | This is E9's "except as hereinafter provided": the seller exempts itself from the two-family limit it just imposed. ⚠ **Read literally the set includes lots 16 and 17**, since they are part of Addition Number Four and the deed states no carve-out for land already sold. I cannot tell whether that was meant. Conditioned by "constructed of brick, stone or other material to be approved by said party of the first part" and "no such building shall be erected unless the plans and specifications for same shall have been first submitted to and approved by said party of the first part" — a second private approval right, folded here because it qualifies this same reservation. | The seller keeps the right to build multi-family blocks anywhere in the plat. |
| E19 | p2 · [0.19,0.394,0.95,0.431] · plain · "the right to use and to grant the right to use for all purposes other than those business purposes specifically mentioned above, all of the lots on Richmond Turnpike, Merrill Avenue and Watchogue Road and the lots on Wyona Avenue between Willow Brook and Hawthorne Avenue" | 1911-04-14 | instrument | 1915-01-01 | ENTITLEMENT | CREATE | SET: lots in plat 995 B fronting Richmond Turnpike, Merrill Avenue or Watchogue Road, or fronting Wyona Avenue between Willow Brook and Hawthorne Avenue | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 4 named street frontages; lot count UNKNOWN(the deed says "all of the lots" and counts none) | Exempts four frontages from the trade restrictions other than the specifically enumerated uses of E15 — a commercial spine kept out of the residential scheme. The criterion is evaluable against the decoded plat, which is what keeps it a SET and not a description. | Four named streets are kept free for business use. |
| E20 | p2 · [0.19,0.472,0.95,0.509] · plain · "the party of the first part has not done or suffered anything whereby the said premises have been encumbered in any way whatever excepting as to said restrictions and limitations" | 1911-04-14 | instrument | 1915-01-01 | ENCUMBRANCE | ASSERT | 5004030016, 5004030017 | Wood Harmon Richmond Realty Company → Minnie A. Sweeney | 1 covenant against grantor's acts | Card 5 case 2 — a real asserted absence, and the only title assurance in the deed. Narrow twice: limited to the grantor's *own* acts, and expressly excepting the restrictions this deed creates. ⚠ `until` is the **literal** reading — E7's expiry clause says "All restrictions and covenants in this instrument contained", and this is a covenant contained in the instrument. Whether the parties meant a title covenant to lapse in 1915 I cannot tell. | The seller warrants only that it has not itself encumbered the land. |
| E21 | p2 · [0.55,0.584,0.90,0.638] · plain · "By Leonidas Keever Vice-President." and "Attest: John H. Storer Secretary." | 1911-04-14 | execution | | IDENTITY | ASSERT | 5004030016, 5004030017 | asserted by: the instrument  about: Leonidas Keever as Vice-President and John H. Storer as Secretary of Wood Harmon Richmond Realty Company | 2 signatories | Recital at p2 [0.19,0.531,0.95,0.556] — corporate name subscribed by the Vice-President and the Secretary, seal affixed, attested by the Secretary, "the day and year first above written", which is why basis is execution on the instrument date and not the acknowledgment four days later. The seal position carries a longhand "(Corp. Seal)" rather than an impression. Both surnames are copperplate; I read Keever and Storer, and the v/r discrimination in Keever is not certain at any magnification I reached. | Signed by the Vice-President and attested by the Secretary. |
| E22 | p2 · [0.19,0.708,0.95,0.772] · plain · "before me personally came Leonidas Keever to me known and being by me duly sworn did depose and say, that he resides in the City of New York, Borough of Brooklyn and that he is the Vice-President" | 1911-04-18 | acknowledgment | | IDENTITY | ASSERT | 5004030016, 5004030017 | Leonidas Keever → Elizabeth Roth, Commissioner of Deeds in and for New York City | 1 deponent, 1 board authorisation | One jurat, one row (card 2). Also carries the corporate authority at p2 [0.19,0.800,0.95,0.824] · plain · "that it was so affixed by order of the Board of Directors of said corporation; and that he signed his name thereto by like order" — the only evidence of authority to convey, sworn by the officer himself, with no date for the board's order and no resolution in the package. Venue at p2 [0.19,0.672,0.42,0.715] reads "State of New York, City of New York, County of New York" and **all three lines stand** — the marks before `City` and `County` are the same lead-in flourish that precedes `State`, which nobody reads as struck. Deponent lives in Brooklyn and swears in New York County. Day digit is 18; the descenders of the venue line above cross it, and 15 is the only alternative I can construct. | The Vice-President swears his identity, office and board authority. |

**22 event rows.**

---

## Registry lane

About the instrument, not a parcel. Not one of the eleven; ids are outside the `E`
series so nothing here is scored as an event.

| id | citation | date | function | bbls | what it records |
|---|---|---|---|---|---|
| R1 | p2 · [0.15,0.830,0.48,0.878] · plain · "Recorded April, 25, 1911 At 9 a. m." | 1911-04-25 | registry act | INSTRUMENT | The registry's own act, with a time of day. rd `recorded` reads `4/25/1911` — agrees on the date; the 9 a.m. has no rd field, so NOT_CHECKABLE. |
| R2 | p2 · [0.15,0.885,0.48,0.925] · plain · "C. Livingston Bostwick, for Wood, Harmon & Co. Broadway, N. Y. City." | 1911-04-25 | return-to party | INSTRUMENT | ⚠ **"Wood, Harmon & Co." is not the grantor's name.** The grantor is Wood Harmon Richmond Realty Company; p1 separately says the plan was "surveyed for Wood Harmon & Co., 1906". Same entity, affiliate, or unrelated is UNKNOWN — the deed never connects them. Street with no number. |
| R3 | p1 · [0.00,0.000,1.00,0.075] · plain · handwritten "396" and "1"; p2 · [0.00,0.000,0.30,0.045] · plain · handwritten "2" | 1911-04-25 | book and page | INSTRUMENT | rd gives book 396 page 1. The instrument occupies book pages 1 and 2. Digital overlay slugs read `Vol. 396 PG 1` and `Vol. 396 PG 2`; those are added by the imaging pipeline, not document evidence. Reported, not reconciled (card 8). |
| R4 | p1 · [0.00,0.870,1.00,1.000] · plain · no stamp, no fee notation, no revenue stamp in either margin at 900 dpi; p2 · [0.00,0.900,1.00,1.000] · plain · likewise | 1911-04-25 | fee or stamp | INSTRUMENT | Card 5 case 1 — **I found nothing.** The document does not assert that no fee was paid. |

## Index check — trust neither side, correct nothing

| rd field | rd says | document says | verdict |
|---|---|---|---|
| `doc_type` | DEED | printed title "DEED." | agree |
| `recorded` | 4/25/1911 | endorsement, 25 April 1911 at 9 a.m. | agree on date; time NOT_CHECKABLE |
| `book` / `page` | 396 / 1 | 396; leaves numbered 1 and 2 | book agrees; page count differs and is not reconciled |
| `parcels` | 5004030016, 5004030017 | lots 16 and 17 in Block 403, Borough of Richmond | agree — borough digit 5 is Richmond |
| `amount` | $0.00 | One Dollar and other valuable considerations | **disagree.** Both stand. |
| `parties` | empty | grantor and grantee both named | **rd omits both.** Nothing about either name can be checked. |
| `instrument` | empty | no instrument number stated | NOT_CHECKABLE |
| `status` | Recorded | endorsement present | agree |
| — | no field | instrument date, acknowledgment date, filed map number, every covenant, the 1915 expiry | NOT_CHECKABLE |

## Brief

On 14 April 1911 Wood Harmon Richmond Realty Company, a New York corporation, granted
and released to Minnie A. Sweeney of 409 Third Street, Brooklyn, all its right, title
and interest in lots 16 and 17 in Block 403, Borough of Richmond — 40 feet on the
westerly side of Heberton Avenue by 100 feet deep, on a 1906 survey the deed says was
filed or intended to be filed as map no. 995 B.

Consideration is one dollar and unstated other value; rd records $0.00 and names no
parties, so the registry row confirms little beyond block and lots.

Most of the instrument is a covenant scheme the buyer gives back: only a detached or
semi-detached dwelling, two storeys, a cellar, no flat roof, no more than two families,
15 feet back from Heberton Avenue with any outbuilding 60 feet back, and one house plus
one outbuilding per 20 by 100 foot parcel.

The house must cost at least $2,000 for one family and $3,000 for two — duties to
spend, not prices paid.

Fences need an officer's written approval; a long list of noxious trades, a hospital
and a fire-engine house are barred; no trade or business may be carried on; no liquor
may be sold.

The seller then carves itself out, keeping the right to erect multi-family blocks
anywhere in the plat — language that on its face reaches the lots it just sold — and to
license the lots on Richmond Turnpike, Merrill Avenue, Watchogue Road and part of Wyona
Avenue for business.

Every restriction is written to expire on 1 January 1915, under four years out, which
is why every covenant row here carries an `until`.

The only title assurance is a covenant that the grantor has not itself encumbered the
premises; the printed clause taking the conveyance subject to assessment liens was
ruled out.

Leonidas Keever, Vice-President, signed with Secretary John H. Storer attesting the
seal, and acknowledged before Commissioner of Deeds Elizabeth Roth on 18 April; the
deed was recorded 25 April 1911 at 9 a.m. and returned to C. Livingston Bostwick for
Wood, Harmon & Co. — a name the deed never connects to the grantor.

The marks on "Sixteen" and "Seventeen" and on both appearances of "Heberton Avenue"
are copperplate lead-in flourishes; the three genuine strikes are ruled lines through
printed form text, and one faint mark across the grantor's name on page 2 I cannot
identify at all.
