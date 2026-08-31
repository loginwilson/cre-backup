# RC_970273 — event table (v2 schema)

Extractor D. Cold read, m2 candidate for `DEED-RESTRICTIVE-COVENANT`.

## PRE-READ PREDICTION

Written before opening page 1. I had seen `registration.json` (rd is a required input
for `bbls`) but no page image. **Frozen — not edited after reading.**

**The spec's standing prediction for m2**, which I am scored against: the eight-function
signature fires; `AS_BUILT` / `CAPITAL` / `PERMIT` do not; `ENTITLEMENT` fires on the
grantor's reserved rights; `STRUCK` and `TERMINATE` do not both appear; a filed-map
reference is present and not in rd; the covenant scheme carries a stated expiry; a
private approval right appears and still has no home; structural surprise ≤ 3.

**My prediction: this is probably NOT a member of the class**, and I expect the
standing prediction to fail on most counts. Reasons, all from rd:

- **§1 signal 1 fails outright.** Grantors are `JOHNSON JOHN QUINCY JR`, `MORGAN
  BLANCHE ESTELLE`, `JOHNSON BLANCHE ESTELLE`, `DADSWELL BLANCHE ESTELLE`; grantees are
  `REID FULTON L` and `REID EDNA G`. Named individuals, not a development company.
- **Three of the four grantors share the given names "Blanche Estelle" under three
  surnames.** I expect one woman recorded under maiden and married names — an IDENTITY
  alias chain, which is `IDENTITY`'s central question and was near-absent from m1.
- **A 1955 resale between individuals, not a developer's first conveyance out of a
  plat.** So I expect the covenant-*creating* functions — `ENVELOPE`, `OCCUPANCY`,
  `COST`-as-building-floor, `ENTITLEMENT` — not to fire, or to fire only by reference
  to an existing scheme.
- **No stated expiry**, because I expect nothing here creates a scheme to expire.
- **`ENCUMBRANCE` fires as `ASSERT`, not `CREATE`** — a subject-to clause pointing at
  restrictions of record rather than imposing them.

Three §2 deviations I predict *against* the spec, which says these were 0 rows out of
99 on m1:

- **`AS_BUILT` may fire.** m1 was a vacant platted lot in 1911. A 1955 Staten Island
  conveyance can carry a house, and the description may state it.
- **`CAPITAL` may fire.** 1955 is mortgage era; a purchase-money mortgage or a
  subject-to-mortgage recital is plausible.
- **`COST` may fire on a revenue stamp.** US documentary stamps were on deeds until
  1968. That is process money, which is `COST`, and it is a different trigger from m1's
  building-cost floor.

Two more expectations:

- **§1 signal 2 (a filed map) may still fire** even though signal 1 fails — Staten
  Island lots are routinely described by filed map. If so, signal 2 is not diagnostic
  of this class, it is diagnostic of Richmond.
- **rd's BBL is `5001590000` — lot `0000`, a placeholder.** I expect the document to
  state a real lot, and I will record both and correct neither (card 9).

---

## Dates

```
instrument: 1955-12-14
acknowledged: 1955-12-16
recorded: 1955-12-21
expires: UNKNOWN
```

⚠ **`acknowledged:` has one slot and this instrument has two acknowledgments** —
Johnson on 1955-12-14 in New York County, Morgan on 1955-12-16 in Westchester County,
before different notaries. I put the **later** date in the block, because the
instrument was not fully acknowledged until the second signer appeared. The block
cannot say that, and a consumer reading it will believe there was one.

⚠ **`expires:` reads `UNKNOWN` and that overstates my doubt.** Nothing in this
instrument creates a term that ends, so there is no expiry to state — card 5 state 1
against a schema that only offers a date or `UNKNOWN`. See the report.

**A fourth date is on the face and is none of these:** the filed map was filed
1907-08-15. Same class of date as m1's map date, and still with no slot.

**rd** carries one parcel, `5001590000` — Richmond, block `00159`, lot `0000`. Lot
`0000` is a placeholder, not a measured lot. The document's own designations are two
and they are in **different systems**: the conveyed land is *the lots numbered 24 and
25* on filed Map Number 941-A, and the endorsement says the land lies in *Section 1,
Block 159 on the Land Map of the County of Richmond*. Block agrees with rd. Nothing on
the page confirms rd's lot, and nothing could.

---

## Events

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | p1 · [0.16,0.085,0.80,0.180] · plain · "JOHN QUINCY JOHNSON, JR., (residing at No. 200-05 111th Avenue, Hollis, Long Island, N.Y.)" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the instrument  about: John Quincy Johnson, Jr. | 1 person, 1 address, 2 capacities | Acts in **two capacities at once** — "individually, and as executor ... under the Last Will and Testament of Blanche E. Dadswell, deceased". One signature carries both. rd lists him once, typed `column: company` with `person` empty; he is a natural person. | The first grantor, of Hollis, signs both personally and as executor. |
| E2 | p1 · [0.16,0.085,0.80,0.180] · plain · "BLANCHE ESTELLE MORGAN, formerly Blanche Estelle Johnson, (residing at No. 17 Kent Road, Scarsdale, N. Y.)" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | Blanche Estelle Johnson → Blanche Estelle Morgan | 1 person, 2 names | An **explicit alias chain in the operative recital** — the deed states the name change itself, which is IDENTITY's exact question and was near-absent from m1. She too acts individually and as executrix. ⚠ **rd carries `MORGAN BLANCHE ESTELLE` and `JOHNSON BLANCHE ESTELLE` as two separate grantors.** The deed says they are one woman. Both stand, neither corrected (card 9). | One woman under two names, signing personally and as executrix. |
| E3 | p1 · [0.16,0.085,0.80,0.180] · plain · "Blanche E. Dadswell, deceased, (said decedent also having been known as Blanche Estelle Dadswell)" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | Blanche E. Dadswell → also known as Blanche Estelle Dadswell | 1 decedent, 2 names | A **second alias chain, on a person who is not a party.** She is the source of title; the grantors convey as her executors. ⚠ **rd lists `DADSWELL BLANCHE ESTELLE` as a Grantor.** She is the decedent and grants nothing — rd has turned one grantor plus one decedent into three grantor rows. The will is an external instrument this deed depends on and does not contain. | Title runs from a deceased woman recorded under two names. |
| E4 | p1 · [0.16,0.180,0.80,0.215] · plain · "FULTON L. REID and EDNA G. REID, his wife, both residing at No. 232 Oakland Avenue, West New Brighton, Staten Island, N. Y." | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the instrument  about: Fulton L. Reid and Edna G. Reid | 2 persons, 1 shared address | The deed states they are married but states **no shares and no form of co-tenancy**. I record neither — two grantees with no stated shares are not halves (card 4). Their stated address is on the same street as the parcel; the deed does not say they occupy it and I do not infer it. | The grantees are a married couple already living on Oakland Avenue. |
| E5 | p1 · [0.16,0.268,0.80,0.300] · plain · "in consideration of ten dollars and other valuable consideration paid by the party of the second part" | 1955-12-14 | instrument | | VALUE | ASSERT | 5001590000 | Fulton L. Reid and Edna G. Reid → John Quincy Johnson, Jr. and Blanche Estelle Morgan | 10 USD stated; remainder UNKNOWN(the deed quantifies "other valuable consideration" nowhere) | Nominal recital, not the price. rd `amount` reads `$0.00`, agreeing with neither. The documentary stamps at E12 are the only other money on the instrument, and converting them to a price needs a tax rate that is not on the document — so I do not (card 4). | Ten dollars and unstated other consideration. |
| E6 | p1 · [0.16,0.290,0.85,0.330] · inserted · "those two lots" written above the line, with "that", "plot" and "in the" typed over by x's | 1955-12-14 | instrument | | TITLE | TRANSFER | 5001590000 | John Quincy Johnson, Jr. and Blanche Estelle Morgan → Fulton L. Reid and Edna G. Reid | 2 map lots taken as 1 parcel; 50 ft frontage by 115 ft deep | "does hereby grant and release ... the heirs or successors and assigns of the party of the second part forever" — a **bargain and sale deed with covenant against grantor's acts**, Standard N.Y.B.T.U. Form 8002; no warranty beyond E10. The amendment converts the printed singular to "those two lots ... pieces or parcels"; the land described is identical either way, so it does not earn its own `STRUCK` row (card 3). ⚠ The marks are **typewriter overstrikes plus a typed interlineation**, not pen rules — and one clause carries two mark types where the citation format allows one. Description at p1 [0.16,0.405,0.82,0.535]: 657.47 ft north of Castleton Avenue, 115 ft west to land now or formerly of Alexander C. Watkins, 50 ft north, 115 ft east, 50 ft south. | The two executors convey a 50 by 115 foot parcel on Oakland Avenue. |
| E7 | p1 · [0.16,0.290,0.85,0.330] · plain · "with the buildings and improvements thereon erected" | 1955-12-14 | instrument | UNKNOWN(the deed states improvements stand at conveyance and says nothing about how long they stand; blank would claim they stand forever) | AS_BUILT | ASSERT | 5001590000 | asserted by: the instrument  about: the conveyed premises | UNKNOWN(the deed states that buildings exist and counts, sizes and types none of them) | ⚠ **§2 DEVIATION — the spec records `AS_BUILT` at 0 rows out of 99 and predicted it would not fire.** It fires here. m1 was a vacant 1911 plat lot; this is a built-up 1955 parcel and the granting clause says so. The assertion is bare: something is erected, nothing about what. | The parcel carries buildings and improvements at the date of conveyance. |
| E8 | p1 · [0.16,0.318,0.82,0.400] · plain · "filed in the office of the Clerk of the County of Richmond August 15th, 1907 as Map Number 941-A as and by the lots numbered 24 and 25" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the instrument  about: the conveyed premises as designated on filed Map Number 941-A | 1 filed map, 2 map lots | The map is *"Map of property belonging to John Frederick Smith, West New Brighton ... July 1906, Henry P. Morrison, C.E., July 1906"*. ⚠ **Filed flatly — no "or intended to be filed".** m1's card 5 state 3 does **not** recur; this is an affirmative filing with a date and a number. Not in rd. The map lots (24, 25) and the tax designation at E16 (Section 1, Block 159) are different systems and the deed never equates them. | The parcel is map lots 24 and 25 on a map filed in 1907. |
| E9 | p1 · [0.16,0.660,0.80,0.720] · plain · "TOGETHER with all right, title and interest, if any, of the party of the first part of, in and to any streets and roads abutting the above described premises to the center lines thereof" | 1955-12-14 | instrument | | TITLE | TRANSFER | UNPLACED | John Quincy Johnson, Jr. and Blanche Estelle Morgan → Fulton L. Reid and Edna G. Reid | UNKNOWN(the deed says "if any" and identifies no street bed, no width and no interest) | A **separate estate from E6** — fee in the beds of abutting streets to their centre lines, land outside the metes and bounds. `UNPLACED` is the honest form: no parcel identifier exists for a street bed, rd has none, and the grant is expressly conditional on the grantors having anything to give. Filing it under the subject BBL would fan a street-bed interest onto the lot, which is a different parcel. | Whatever the grantors owned in the abutting street beds passes too, if anything. |
| E10 | p1 · [0.16,0.740,0.80,0.825] · plain · "has not done or suffered anything whereby the said premises have been encumbered in any way whatever, except as aforesaid" | 1955-12-14 | instrument | | ENCUMBRANCE | ASSERT | 5001590000 | John Quincy Johnson, Jr. and Blanche Estelle Morgan → Fulton L. Reid and Edna G. Reid | 1 covenant against grantor's acts | Card 5 state 2 — a real asserted absence, and the only title assurance in the deed. ⚠ **"except as aforesaid" has no antecedent.** Nothing earlier in this instrument states an exception; m1's parallel clause excepted its own restrictions, and here the words are left dangling on a printed form. Whether anything is excepted is unresolvable from the page. Limited to the grantors' own acts either way — silent on the decedent's acts and on prior owners. | The grantors warrant only that they have not themselves encumbered the land. |
| E11 | p1 · [0.16,0.740,0.80,0.825] · plain · "in compliance with Section 13 of the Lien Law, covenants that the party of the first part will receive the consideration for this conveyance and will hold the right to receive such consideration as a trust fund to be applied first for the purpose of paying the cost of the improvement" | 1955-12-14 | instrument | UNKNOWN(the trust ends when the cost of the improvement is paid, which the deed does not date) | COST | CREATE | 5001590000 | John Quincy Johnson, Jr. and Blanche Estelle Morgan → the beneficiaries of the Lien Law section 13 trust | UNKNOWN(the deed does not state the sum the trust attaches to) | A **statutory trust over the sale proceeds**, imposed by law and recited here. Filed COST as a duty to spend, but the fit is poor: it binds the grantors personally, not the land, and it does not run to the grantees. What the row loses is *who holds the money and for whom* — see the report. Bears on `CAPITAL` and on `ENCUMBRANCE` and answers neither question. | The grantors must hold the sale money in trust for improvement costs first. |
| E12 | p1 · [0.05,0.050,0.20,0.410] · plain · three United States Internal Revenue "DOCUMENTARY" stamps reading "10 TEN DOLLARS", "3 THREE DOLLARS" and "20 CENTS", cancelled "DEC 21 1955" | 1955-12-21 | recorded | | COST | ASSERT | 5001590000 | asserted by: the affixed and cancelled stamps  about: the conveyance | 13.20 USD in documentary stamp tax | ⚠ **§2 DEVIATION — `COST` fires, but not on a building cost floor.** The spec's five COST rows were all m1's *"shall cost not less than"* duty to spend; this is process money actually paid. Arithmetic on stated values only: 10.00 plus 3.00 plus 0.20. I do **not** convert it to a sale price — the 1955 rate is not on the document (card 4). ⚠ framework.md assigns "any fee or stamp" to the registry lane; I emit it as an event instead because a federal conveyance tax is not the registry's act and lane rows do not fan to a parcel. Stated deviation, not an oversight. | Thirteen dollars twenty cents of federal documentary stamps, cancelled on recording. |
| E13 | p1 · [0.45,0.840,0.85,0.960] · plain · "John Quincy Johnson, Jr., individually and as executor, and" / "Blanche Estelle Morgan, individually and as executrix, under the Last Will and Testament of Blanche E. Dadswell, deceased." | 1955-12-14 | execution | | IDENTITY | ASSERT | 5001590000 | asserted by: the instrument  about: the signing capacity of both grantors | 2 signatures, 4 capacities | "IN WITNESS WHEREOF, the party of the first part has duly executed this deed the day and year first above written" — execution recited as of the instrument date. ⚠ That sits awkwardly with Morgan acknowledging two days later; the deed does not say when she actually signed, and I do not infer it. The printed "IN PRESENCE OF:" slot is **empty** — no subscribing witness (see the search block below). | Both grantors sign personally and in their fiduciary capacities. |
| E14 | p2 · [0.21,0.045,0.58,0.225] · plain · "On the 14 day of December, 1955, before me personally came JOHN QUINCY JOHNSON, JR., individually and as executor ... and acknowledged that he executed the same, individually, and as such executor." | 1955-12-14 | acknowledgment | | IDENTITY | ASSERT | 5001590000 | John Quincy Johnson, Jr. → Jack Fialkin, Notary Public | 1 deponent | Venue **County of New York**, handwritten. Notary Jack Fialkin, No. 24-1205900, **qualified in Kings County**, commission expires 1957-03-30. The two grantors acknowledge separately, on different days, before different notaries, in different counties. | Johnson acknowledges in New York County on the 14th. |
| E15 | p2 · [0.55,0.045,0.92,0.245] · plain · "On the 16th day of December, 1955, before me personally came BLANCHE ESTELLE MORGAN, individually and as executrix ... and acknowledged that she executed the same, individually, and as such executrix." | 1955-12-16 | acknowledgment | | IDENTITY | ASSERT | 5001590000 | Blanche Estelle Morgan → Fred J. Hoff, Notary Public | 1 deponent | Venue **County of Westchester**, handwritten. Notary Fred J. Hoff, appointed in Westchester County, State No. 60-6926300, commission expires 1956-03-30. This is the acknowledgment that completes the instrument and the one I put in the labelled block. | Morgan acknowledges in Westchester County two days later. |
| E16 | p2 · [0.20,0.500,0.75,0.760] · plain · "The land affected by the within instrument lies in Section 1, in Block 159 on the Land Map of the County of Richmond" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the instrument  about: the conveyed premises as Section 1, Block 159 | 1 section, 1 block | The **tax-map designation**, and the only thing on the document that meets rd's BBL — block 159 matches rd's `00159`. It is a different identifier system from the filed-map lots at E8, and the deed never states that Section 1 Block 159 equals map lots 24 and 25. rd's lot `0000` is a placeholder and the page cannot confirm or contradict it. | The deed places the land in Section 1, Block 159 of the county land map. |

**16 event rows.**

---

## Registry lane

About the instrument, not a parcel. Not one of the eleven.

| id | citation | date | function | bbls | what it records |
|---|---|---|---|---|---|
| R1 | p2 · [0.19,0.740,0.78,0.970] · plain · "RECEIVED COUNTY CLERK'S OFFICE DEC 21 3 10 PM 1955 RICHMOND COUNTY" | 1955-12-21 | receipt | INSTRUMENT | The clerk's **received** stamp, 3:10 PM. A registry act distinct from recording, six minutes earlier. |
| R2 | p2 · [0.19,0.740,0.78,0.970] · plain · "Recorded in the Richmond County Clerk's Office on Dec 21/1955 at 3:16 P Liber 1338 Page 184 of Deeds" | 1955-12-21 | recording | INSTRUMENT | Recorded 3:16 PM into Liber 1338 page 184. rd `recorded` reads `12/21/1955` and `book 1338` `page 184` — agree. The time has no rd field: NOT_CHECKABLE. |
| R3 | p2 · [0.19,0.740,0.78,0.970] · plain · "and Indexed under Block Number 159 and Map of the County of Richmond" | 1955-12-21 | indexing | INSTRUMENT | The registry's **own indexing act**, naming block 159 and no lot. This is the origin of rd's `5001590000`: a block-indexed instrument produces a BBL with a placeholder lot. The registry recorded no lot because it indexed none. |
| R4 | p2 · [0.47,0.730,0.66,0.910] · uncertain · a handwritten "6" on the rule following the printed "RECORDING FEE $" | 1955-12-21 | fee | INSTRUMENT | ⚠ Read as a **$6 recording fee**. The figure sits where the `RECORDING FEE $` rule and the `No.` rule converge, so it could belong to either; if it belongs to `No.`, the fee is blank. Marked `uncertain` with the rect rather than asserted (m1's unlabelled `16.00` is the precedent for not calling this flat). |
| R5 | p2 · [0.20,0.500,0.75,0.760] · plain · "RECORDED AT REQUEST OF FREDERICK L. HACKENBURG, 21 EAST 40" STREET, NEW YORK 16, N.Y." | 1955-12-21 | return-to party | INSTRUMENT | The return-to party, with a complete street address — unlike m1's. Named nowhere else in the instrument; not a party, not a notary. |
| R6 | p1 · [0.16,0.070,0.45,0.090] · plain · "LIBER 1338 PAGE 184"; p2 · [0.88,0.150,0.94,0.250] · plain · "LIBER 1338 PAGE 185" | 1955-12-21 | liber and page | INSTRUMENT | rd gives page 184. The instrument occupies liber pages **184 and 185**. Reported, not reconciled (card 8). A further handwritten number in the recording box reads **12030 or 12930** — I cannot resolve the third digit and it is unlabelled, so I do not name it. |

⚠ **The documentary stamps are not in this lane.** framework.md puts "any fee or stamp"
here; they are at E12 instead, because a federal tax on the conveyance is not the
registry's act and lane rows do not fan to a parcel. Stated so it reads as a decision.

---

## Does not fit any of the eleven

**A construction clause.** p1 · [0.16,0.740,0.80,0.825] · plain · *"The word 'party'
shall be construed as if it read 'parties' whenever the sense of this indenture so
requires."*

It does real work here — there are two grantors and two grantees, and every operative
verb in the printed form is singular. Without it the granting language does not
grammatically reach both sides. But it is not a question about a parcel: it is an
instruction about how to read the rest of the document.

Filing it under `IDENTITY` — the nearest fit — would lose exactly what it is. IDENTITY
asks *is this the same as that* about persons and things; this clause asks nothing
about the world. It changes the meaning of every other row without being an event.

---

## SEARCH RECORD

Pages carry an embedded scan of 3164 × 4190, so sensitivity is `native`, not a dpi —
`docpkg.py --rect` crops the scan itself.

| region | dpi | found |
|---|---|---|
| p1 · [0.16,0.835,0.45,0.960] | native | The printed "IN PRESENCE OF:" slot, **empty** — no subscribing witness signed |
| p1 · [0.16,0.535,0.80,0.660] | native | Blank between the description and the TOGETHER clause; no subject-to clause, no reference to restrictions of record |
| p1 · [0.80,0.040,1.00,0.980] | native | Film edge and sprocket marks; no marginal note, no stamp, nothing operative |
| p2 · [0.21,0.245,0.92,0.420] | native | Two unused printed acknowledgment forms — corporate and subscribing-witness — both entirely blank |
| p2 · [0.00,0.000,0.20,1.000] | native | Film edge and punch holes; nothing operative |

**Not found anywhere on either page** (card 5 state 1, not an asserted absence): no
mortgage, no purchase-money debt, no subject-to-mortgage recital; no restrictive
covenant of any kind; no building, use, setback or trade restriction; no reserved right
of any kind; no government permit, approval or application; no stated expiry.

---

## Index check — trust neither side, correct nothing

| rd field | rd says | document says | verdict |
|---|---|---|---|
| `doc_type` | DEED | "Bargain and Sale Deed With Covenant Against Grantor's Acts", N.Y.B.T.U. Form 8002 | agree, and rd is coarser than the form |
| `recorded` | 12/21/1955 | recorded 1955-12-21 at 3:16 PM; received 3:10 PM | agree on date; both times NOT_CHECKABLE |
| `book` / `page` | 1338 / 184 | Liber 1338, pages 184 and 185 | book and first page agree; page count differs, not reconciled |
| `parcels` | 5001590000 | Section 1, Block 159 on the county land map; map lots 24 and 25 on Map 941-A | **block agrees; lot `0000` is a placeholder and the page cannot confirm it.** The registry indexed under a block and no lot, so the placeholder is the registry's own act (R3), not a gap in the deed |
| `amount` | $0.00 | ten dollars and other valuable consideration | **disagree.** Both stand |
| `parties` | 4 Grantors, 2 Grantees | **2 grantors**, 2 grantees, 1 decedent | ⚠ **rd inflates two grantors into four.** `JOHNSON BLANCHE ESTELLE` is Morgan's former name — the same woman. `DADSWELL BLANCHE ESTELLE` is the **decedent**, who grants nothing. Recorded, not corrected |
| `parties[].column` | `company` on all six | six natural persons | **disagree on 6 of 6.** No document-side support for any of them being a company |
| `instrument` | empty | no instrument number; the printed `No.` slot is blank | NOT_CHECKABLE |
| `status` | Recorded | clerk's endorsement present | agree |
| — | no field | both acknowledgment dates, the filed map, the will of Blanche E. Dadswell, the Lien Law trust, the documentary stamps | NOT_CHECKABLE |

---

## Brief

On 14 December 1955 John Quincy Johnson, Jr. of Hollis and Blanche Estelle Morgan of
Scarsdale — she formerly Blanche Estelle Johnson — conveyed to Fulton L. Reid and Edna
G. Reid, his wife, a parcel 50 feet on the westerly side of Oakland Avenue by 115 feet
deep at West New Brighton, Staten Island.

They conveyed in two capacities at once, individually and as executor and executrix
under the will of Blanche E. Dadswell, also known as Blanche Estelle Dadswell, so title
runs out of a dead woman's estate through an external will this deed does not contain.

The land is map lots 24 and 25 on a map filed in the Richmond County Clerk's office on
15 August 1907 as Map Number 941-A, and separately placed by the endorsement in Section
1, Block 159 of the county land map — two identifier systems the deed never equates.

Consideration is ten dollars and other valuable consideration; three cancelled federal
documentary stamps totalling thirteen dollars and twenty cents are the only other money
on the instrument, and the rate that would turn them into a price is not on the page.

The granting clause was amended on the typewriter — "that certain plot" struck and
"those two lots" typed above the line — and it recites that buildings and improvements
stand on the land.

Whatever the grantors held in the beds of the abutting streets passes as well, if
anything; the deed hedges it expressly.

The only title assurance is a covenant that the grantors have not themselves encumbered
the premises, "except as aforesaid" — words with nothing before them to except.

A Lien Law section 13 covenant makes the grantors hold the sale money in trust for the
cost of the improvement before any other use.

Johnson acknowledged in New York County on the 14th before Jack Fialkin; Morgan
acknowledged in Westchester County on the 16th before Fred J. Hoff; the deed was
received at 3:10 PM and recorded at 3:16 PM on 21 December 1955 in Liber 1338 page 184,
indexed under block 159 alone, at the request of Frederick L. Hackenburg.

**There is no restrictive covenant anywhere in this instrument** — no building, use,
setback, trade or family restriction, no reserved right, and nothing that expires.
