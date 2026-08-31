# RC_1598772 — Extractor C — table-v2

Class: `DEED-RESTRICTIVE-COVENANT` (m1). Re-emission of my sealed v3 table into the
v4 schema. **Same reading.** No fact added, none dropped.

```
instrument: 1911-04-14
acknowledged: 1911-04-18
recorded: 1911-04-25
expires: 1915-01-01
```

BBLs are **rd's**, from `registration.json` `parcels`: `5004030016`, `5004030017`.
The document's own designation — *lots 16 and 17 in Block 403*, on filed map no.
995 B — is carried in `terms`, never composed into a BBL.

## Events

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | p1 · [0.15,0.105,0.95,0.185] · plain · "by and between WOOD HARMON RICHMOND REALTY COMPANY, a corporation duly organized and existing under and by virtue of the Laws of the State of New York, party of the first part, and MINNIE A. SWEENEY, residing at No. 409 Third Street, Borough of Brooklyn" | 1911-04-14 | instrument | | IDENTITY | ASSERT | 5004030016, 5004030017 | asserted by: the indenture  about: Wood Harmon Richmond Realty Company and Minnie A. Sweeney | 2 parties | One recital, one act of identification. Grantor is a NY corporation; grantee a single natural person — printed "part___" hand-completed to "part y", and "her" / "herself" / an inserted "s" giving "she" throughout. **The class spec §1 and the worked row in framework.md both name the grantor "The Wood, Harmon Company". The page does not say that** (card 11). *Wood, Harmon & Co.* is a different string appearing twice — as the firm the plat was surveyed for, and in the return block — and this deed states no relationship between the two. | The deed is between Wood Harmon Richmond Realty Company and Minnie A. Sweeney. |
| E2 | p1 · [0.15,0.215,0.95,0.250] · plain · "in consideration of the sum of One Dollar , lawful money of the United States and other valuable considerations" | 1911-04-14 | instrument | | VALUE | ASSERT | 5004030016, 5004030017 | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | 1 USD | The "other valuable considerations" are `UNKNOWN(no amount, form or payer stated)`. rd `amount` reads `$0.00` against the deed's one dollar — both stand, neither corrected (card 9). No revenue or transfer stamp in either margin. | Stated price is one dollar plus unspecified other consideration. |
| E3 | p1 · [0.15,0.243,0.95,0.266] · plain · "does hereby grant and release unto the said part y of the second part, her heirs and assigns forever, all its right, title and interest in and to all that certain piece or parcel of land" | 1911-04-14 | instrument | | TITLE | TRANSFER | 5004030016, 5004030017 | Wood Harmon Richmond Realty Company → Minnie A. Sweeney, her heirs and assigns | 2 lots; 40 ft frontage x 100 ft depth | One conveyance, not three: granting clause, the "Together with the appurtenances and all the estate and rights of the party of the first part" clause, and the habendum p1 · [0.15,0.617,0.95,0.633] "To Have and to Hold ... her heirs and assigns forever" are three parts of one act (card 2). Form is bargain-and-sale — "all its right, title and interest" — not a warranty of the fee. Courses run west 100 ft along lot 15, north 40 ft, east 100 ft along lot 18, south 40 ft, from a point 214.28 ft north of Caswell Avenue. Area `UNKNOWN(not stated; "be said measurements and area more or less")`. | The company conveys whatever interest it holds in the two lots. |
| E4 | p1 · [0.44,0.2775,0.90,0.3080] · flourish · "known and designated as lot s No. Sixteen and Seventeen (16, 17) in Block 403" | 1911-04-14 | instrument | | IDENTITY | ASSERT | 5004030016, 5004030017 | asserted by: the indenture  about: lots 16 and 17 in Block 403 | 2 lots on map no. 995 B | Asserts the lot-and-block designation and the metes-and-bounds parcel are the same land. Map recital p1 · [0.20,0.3300,0.62,0.3480] · plain · "July, 5, 1907, as map no. 995 B" against printed "filed **or intended to be filed**" — card 5's third state: **the document declines**, giving a date and a number while refusing to confirm the act. Marks on "Sixteen"/"Seventeen" are `flourish`: at 3200 dpi each stroke stops inside the capital S, while this document's four genuine cancellations span their text end to end; the same lead-in appears on State / City / County / (Corp. Seal) / Storer / Commissioner, none of which can be struck. Not outcome-bearing — "(16, 17)" is unmarked and the courses run between lot 15 and lot 18. Spec §6 flags this row's function as a candidate: **a filed map is not a person, and IDENTITY's triggers are all persons and entities.** | The parcel is lots 16 and 17, Block 403, on filed map 995 B. |
| E5 | p1 · [0.155,0.6320,0.780,0.6480] · struck · "subject, however, to all assessments that have become a lien since the" | 1911-04-14 | instrument | | ENCUMBRANCE | STRUCK | 5004030016, 5004030017 | Wood Harmon Richmond Realty Company → Minnie A. Sweeney | UNKNOWN(the day, month and year blanks were never filled) | A complete printed sentence ruled out end to end, carrying its trailing "day", "of" and "19" on the next line. Earns a row under card 3 because standing it would have made the conveyance subject to prior assessment liens. Whether the strike preceded execution is permanently `uncertain` — these scans are bitonal and stroke order is unrecoverable (card 1). | The clause subjecting the land to existing assessment liens was struck out. |
| E6 | p1 · [0.15,0.6900,0.95,0.7300] · plain · "for herself, her heirs, executors, administrators and assigns, do th hereby covenant and agree to and with the said party of the first part, its successors and assigns" | 1911-04-14 | instrument | 1915-01-01 | ENCUMBRANCE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney and successors → Wood Harmon Richmond Realty Company and successors | UNKNOWN(this row is the running character, not a measured burden) | The covenant scheme **as a burden riding on title**: binds successors on both sides. What each covenant requires is E7–E11; no act is counted twice. Note the covenants reach only "any part of the herein-described premises" — **this instrument does not impose them on the rest of the plat**, contrary to spec §5. | The restrictions bind her successors and run to the grantor's, until 1915. |
| E7 | p1 · [0.15,0.7280,0.95,0.7440] · plain · "any building except a detached or semi-detached dwelling house" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney and successors → Wood Harmon Richmond Realty Company and successors | 15 ft front building line | One building-form programme, enumerated rather than split (card 2): detached or semi-detached only; p1 · [0.15,0.8000,0.95,0.8180] "not be less than two stories in height, shall have a cellar, shall not have what is commonly known as a flat roof"; p1 · [0.15,0.8220,0.95,0.8420] "within fifteen ( 15 ) feet of the line of Heberton Avenue", excepting steps, piazzas, bay or oriel windows; p2 · [0.15,0.0420,0.95,0.0680] a barn, stable or garage appurtenant to a private residence "must stand at least sixty feet from Heberton Avenue"; p2 · [0.15,0.0780,0.95,0.1080] "more than one such dwelling house and one such stable or garage" barred "on each parcel of land Twenty feet in width by One Hundred feet in depth". **Two struck blanks earn no row** (card 3) because their blanks were never filled and standing them would have changed nothing: p1 · [0.60,0.8300,0.95,0.8560] · struck · "nor within" with p1 · [0.15,0.8440,0.60,0.8600] · struck · "( ) feet of the line of", and p2 · [0.15,0.0560,0.60,0.0800] · struck · "( ) feet from". Effect: only Heberton Avenue carries a building line. | Only a two-storey, cellared, non-flat-roofed detached or semi-detached house, set 15 feet back. |
| E8 | p1 · [0.15,0.7440,0.95,0.7560] · plain · "no such dwelling house shall be built for use and occupancy of more than two families except as hereinafter provided" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney and successors → Wood Harmon Richmond Realty Company and successors | 2 families maximum | One use programme. Also p2 · [0.15,0.1450,0.95,0.2450] barring milkman's stable, livery stable, carpenter shop, piggery, slaughter house, smith shop, forge, furnace, steam engine, brass foundry, tin/nail/other iron factory, manufactory for gunpowder, glue, varnish, vitriol, ink or turpentine, boiling of bones, dressing/tanning/preparing of skins, hides or leather, brewery, distillery, oil or lampblack factory, any noxious or dangerous trade, any fire-engine or hose-carriage house, any hospital — one prohibition, list in terms per card 2; and p2 · [0.15,0.2320,0.95,0.2560] · inserted · "and that s he will not use or permit to be used the said premises or any part thereof for the use or carrying on of any trade or business", a general bar wider than the enumeration. The "except as hereinafter provided" points to E12 and relieves the grantor, not this parcel. | Two families at most, no named trade, and no trade or business at all. |
| E9 | p1 · [0.30,0.7500,0.72,0.7700] · plain · "shall cost not less than Two Thousand ($2000.) dollars if built for use and occupancy of one family only" | 1911-04-14 | instrument | 1915-01-01 | COST | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney and successors → Wood Harmon Richmond Realty Company and successors | 2000 USD minimum | One duty to spend, varying by occupancy — one row per card 2, reversing my v3 split. Second branch p1 · [0.40,0.7840,0.78,0.8030] · plain · "it shall cost not less than Three Thousand ($3,000.) dollars" for a double house, two families, or a double tenement. **Spec §4 says "cost floors may vary by street" and the framework worked row reads "$2,000 on Heberton; $3,000 on the avenue frontage" — on this page the variation is by family count and nothing on either page ties either figure to a street** (card 11). No money moves, so COST not VALUE and not CAPITAL. | A house here must cost at least $2,000, or $3,000 for two families. |
| E10 | p2 · [0.15,0.1250,0.95,0.1680] · plain · "nor shall any fence be built, constructed or maintained on any part of said premises unless the nature, kind, shape and material be first made known and shown to one of the officers of the said WOOD HARMON RICHMOND REALTY COMPANY, and have received his sanction and approval in writing" | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney and successors → Wood Harmon Richmond Realty Company | UNKNOWN(no height, material or setback fixed; the standard is an officer's discretion) | Kept out of E7 because it is not a rule but **a continuing discretionary veto held by a named private party** — spec §6's open candidate. ENVELOPE holds the constraint and loses the veto holder; PERMIT is government-only, so it cannot go there. Note the beneficiary is drafted as the company alone, not "its successors and assigns" as in E6. | No fence without the written approval of a company officer. |
| E11 | p2 · [0.15,0.2550,0.95,0.3300] · plain · "will sell or suffer or allow to be sold on the premises hereby conveyed, or any part thereof, any strong or spirituous liquors, or ale, beer or wine, or intoxicating liquors of any kind" | 1911-04-14 | instrument | 1915-01-01 | OCCUPANCY | CREATE | 5004030016, 5004030017 | Minnie A. Sweeney, her heirs, executors, administrators and assigns → Wood Harmon Richmond Realty Company, its successors and assigns | UNKNOWN(absolute; no quantity, licence or exception) | A **second, formally separate covenant** — its own paragraph opening "doth hereby **further** covenant" with its own recital of the parties bound — which is why it is not folded into E8. Reaches selling and suffering or allowing sale, not consumption. | No liquor of any kind may be sold on the premises. |
| E12 | p2 · [0.15,0.3150,0.95,0.3900] · plain · "The party of the first part, however, shall have the right to erect or maintain or to permit to be erected or maintained on any part of South New York, Addition Number Four, buildings in blocks for the use and occupancy of one or more families, or detached or semi-detached buildings for the use and occupancy of more than two families" | 1911-04-14 | instrument | | ENTITLEMENT | CREATE | SET: all lots in plat 995 B (South New York, Addition Number Four, Richmond County Clerk map no. 995 B) | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | UNKNOWN(no cap on families, storeys or buildings stated for the grantor's own land) | The scheme's express asymmetry: the grantee is capped at two families while the grantor may build for more anywhere in the plat. The grantor limits only itself — materials and plans "to be approved by said party of the first part", approver and applicant the same. **`until` left blank and it should not be read as perpetual:** the expiry clause reaches "all restrictions and covenants", and this is drafted as a *right*, so the page does not say whether it expires (card 12). The schema offers no UNKNOWN for `until`. | The grantor keeps the right to build multi-family anywhere in the subdivision. |
| E13 | p2 · [0.15,0.3850,0.95,0.4400] · plain · "the right to use and to grant the right to use for all purposes other than those business purposes specifically mentioned above, all of the lots on Richmond Turnpike, Merrill Avenue and Watchogue Road and the lots on Wyona Avenue between Willow Brook and Hawthorne Avenue" | 1911-04-14 | instrument | | ENTITLEMENT | CREATE | SET: lots in plat 995 B fronting Richmond Turnpike, Merrill Avenue or Watchogue Road, plus lots on Wyona Avenue between Willow Brook and Hawthorne Avenue | Minnie A. Sweeney → Wood Harmon Richmond Realty Company | UNKNOWN(lots identified by frontage, not by number or count) | Commercial use on named frontages, with a power to **grant it on**. The E8 trades stay barred. None of these streets is Heberton or Caswell, so on the face of the page none touches the subject parcel. ⚠ **The framework's own `SET:` warning names this exact clause as a failed row** — *"lots on four named streets is prose — it reaches no parcel"*. It is the only form the document gives. Written as a criterion evaluable once map 995 B is decoded; see the notes below. | The grantor keeps and may pass on business-use rights over four named frontages. |
| E14 | p2 · [0.15,0.4620,0.95,0.5000] · plain · "the party of the first part has not done or suffered anything whereby the said premises have been encumbered in any way whatever excepting as to said restrictions and limitations" | 1911-04-14 | instrument | 1915-01-01 | ENCUMBRANCE | ASSERT | 5004030016, 5004030017 | Wood Harmon Richmond Realty Company → Minnie A. Sweeney | UNKNOWN(an absence, not a quantity) | Card 5's second state — a real asserted absence, and a narrow one: only the grantor's **own acts**, expressly excepting this deed's restrictions. The deed nowhere says the premises are free of encumbrances. `until` set to 1915-01-01 on the literal text — "**all** restrictions and covenants in this instrument contained" is broad enough to catch the grantor's own covenant. That may not be intended and the page does not resolve it; flagged rather than silently exempted. | The grantor covenants it has itself encumbered the land only by these restrictions. |
| E15 | p2 · [0.15,0.5550,0.95,0.6400] · plain · "By Leonidas Keever Vice-President. Attest: John H. Storer Secretary." | 1911-04-14 | instrument | | IDENTITY | ASSERT | INSTRUMENT | Leonidas Keever and John H. Storer → Wood Harmon Richmond Realty Company | 2 signatories | The capacity each man signs in. "In Witness Whereof ... the day and year first above written" ties execution to the instrument date, so **instrument and execution coincide here and I did not have to discriminate** (card 10). The seal itself is not in the image — "(Corp. Seal)" is written in script in its place, so what is visible is a notation that a seal was there, not a seal. | Two officers execute for the company under its corporate seal. |
| E16 | p2 · [0.15,0.7280,0.95,0.7800] · plain · "that he resides in the City of New York, Borough of Brooklyn and that he is the Vice-President of WOOD HARMON RICHMOND REALTY COMPANY" | 1911-04-18 | acknowledgment | | IDENTITY | ASSERT | INSTRUMENT | Leonidas Keever → Elizabeth Roth, Commissioner of Deeds in and for New York City | 1 deponent | Sworn four days after signing; p2 · [0.15,0.6950,0.95,0.7300] "On the 18th day of April". Adds corporate authority: the seal "was so affixed by order of the Board of Directors" and he "signed his name thereto by like order". Venue is three handwritten lines — State of New York, City of New York, County of New York — and **none is struck**; at page zoom all three read as struck, and so do the words "the corporation" nearby. Storer, who attested, does not acknowledge. Spec §6 records four readers at 18 and one at 15; I read 18 — a closed upper and lower loop, not a 5. | Keever swears he is Vice-President and signed by order of the board. |

**16 events.** My v3 table had 29 on the identical reading. The whole difference is
schema, not content: `until` absorbed one row (the 1915 expiry), and card 2's
one-row-per-act rule absorbed twelve. Nothing was dropped — see the mapping below.

## Registry lane

Not one of the eleven; these ask about the instrument, not a parcel. Ids are `R#`
because `tablecheck` treats any `E#` row as an event and demands a function of the
eleven — **there is none for a recording act**, so a registry row cannot be an
`E#` row.

| # | citation | date | bbls | what it records |
| --- | --- | --- | --- | --- |
| R1 | p2 · [0.15,0.8250,0.55,0.8900] · plain · "Recorded April, 25, 1911 At 9 a.m." | 1911-04-25 | INSTRUMENT | The registry's own act, with a **time** rd has no field for. rd `recorded` reads `4/25/1911` — agrees. |
| R2 | p2 · [0.14,0.8700,0.55,0.9200] · plain · "C. Livingston Bostwick, for Wood, Harmon & Co. Broadway, N.Y. City." | 1911-04-25 | INSTRUMENT | Return-to party and the only agent address on either page. A faint mark above "25, 1911" reads as show-through from the reverse; I cannot make it out and do not guess (card 12). |
| R3 | p1 · [0.00,0.000,1.00,0.070] · marginal · "Vol. 396 PG 1" with handwritten "396" and "1" | 1911-04-25 | INSTRUMENT | Liber and page endorsement. rd `book` 396, `page` 1 — agrees. Page 2 carries "Vol. 396 PG 2" and a handwritten "2". Three counts, reconciled to none (card 8). |
| R4 | — | — | INSTRUMENT | **No fee, tax or revenue stamp found in either margin at 900 dpi.** Card 5 first state: *I found nothing*, not *the document says there is none*. No rect: there is nothing to point at. |

## Index check — rd vs the document

| rd field | rd says | document says | verdict |
| --- | --- | --- | --- |
| `instrument` | `""` | no instrument number on either page | NOT_CHECKABLE |
| `book` / `page` | `396` / `1` | "Vol. 396 PG 1"; handwritten 396 and 1 | agrees |
| `doc_type` | `DEED` | printed heading "DEED." | agrees — spec §1's untested prediction holds on m1 |
| `recorded` | `4/25/1911` | "Recorded April, 25, 1911 At 9 a.m." | agrees; rd carries no time field |
| `amount` | `$0.00` | "One Dollar ... and other valuable considerations" | **disagrees.** Both stand. |
| `parcels` | `5004030016`, `5004030017` | lots 16 and 17 in Block 403, Borough of Richmond | agrees |
| `parties` | `[]` | Wood Harmon Richmond Realty Company → Minnie A. Sweeney | NOT_CHECKABLE — an empty list is not agreement |
| `status` | `Recorded` | endorsement present | agrees |

## v3 → v2 row mapping, so nothing can quietly vanish

Row ids below are prefixed `v3` so the checker does not read this mapping as a
second event table — it treats any first cell starting `E<digit>` as an event.

| v3 rows | v2 row | absorbed by |
| --- | --- | --- |
| v3 E1 grantor + E2 grantee | E1 | one recital, one act (card 2) |
| v3 E4 grant + E6 appurtenances + E7 habendum | E3 | three parts of one conveyance |
| v3 E10 form + E14 storeys + E15 cellar + E16 roof + E17 15 ft + E18 60 ft + E19 density | E7 | one building-form programme |
| v3 E11 families + E21 trades + E22 no business | E8 | one use programme |
| v3 E12 $2,000 + E13 $3,000 | E9 | one duty, varying by occupancy |
| v3 E26 expiry 1915-01-01 | *no row* | the `until` column |
| v3 E3, E5, E8, E9, E20, E23, E24, E25, E27, E28, E29 | E2, E4, E5, E6, E10, E11, E12, E13, E14, E15, E16 | unchanged, one to one |

## What the schema could not express

1. **`until` has two states and this document needs three.** A date, or blank meaning
   never. E12 and E13 need *cannot tell*: the expiry reaches "all restrictions and
   covenants" and the reservations are drafted as **rights**. Blank now reads as a
   verified perpetuity I did not verify.
2. **`SET:` forbids the only form this document gives.** The framework names *"lots on
   four named streets"* as a row that failed — that is E13, quoted from the page.
   Frontage is how the clause defines the set and there is no other handle on it.
3. **A private discretionary veto has no function.** E10. `ENVELOPE` keeps the
   constraint and loses the holder; `PERMIT` is government-only. Spec §6 already has
   this open; a second instance sits in E12's plan-approval.
4. **A filed map is not a person.** E4 sits under `IDENTITY`, whose triggers are all
   persons and entities. Filing it there loses that the map is a **separate
   instrument in a separate series** that the parcel description is meaningless
   without.
5. **`INSTRUMENT`'s gloss is backwards.** It is defined as being for registry-lane
   rows, but a registry-lane row cannot carry a function of the eleven, so it can
   never be an `E#` row. In practice `INSTRUMENT` gets used by E15 and E16 —
   execution and acknowledgment — which are not registry acts.
6. **A row has one `date`, and E4 carries two.** The instrument date, and the map
   filing date 1907-07-05. The second went to `terms`, where nothing can sort on it.
   Spec §4 already calls it "a fourth kind of date".

## Brief

Wood Harmon Richmond Realty Company conveyed two Staten Island building lots — 16 and
17 in Block 403, a 40 by 100 foot parcel on the west side of Heberton Avenue — to
Minnie A. Sweeney of Brooklyn on 14 April 1911, for one dollar and unstated other
consideration. The form is bargain and sale of "all its right, title and interest",
not a warranty, and the printed clause subjecting the land to existing assessment
liens was struck out.

The weight is in the covenants. A detached or semi-detached dwelling only, two
storeys, a cellar, no flat roof, 15 feet back from Heberton Avenue and 60 for an
outbuilding, one house per platted lot, no fence without a company officer's written
approval, at least $2,000 of construction, two families at most, twenty named trades
barred, no trade or business at all, and no liquor sold. The grantor bound the buyer
and exempted itself, keeping the right to build multi-family anywhere in the plat and
to sell business-use rights on four named frontages.

All of it ends 1 January 1915 — under four years — which is why `until` matters more
here than any other cell. Keever acknowledged on 18 April; the deed was recorded at 9
a.m. on 25 April 1911. rd carries no parties at all and puts the consideration at
$0.00 against the deed's one dollar; both stand.
