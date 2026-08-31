# RC_970273 — table-v2 (Extractor B)

## PRE-READ PREDICTION

**Written and committed to disk before opening page 1 and before reading
`registration.json`.** Everything I knew: rd types it `DEED`, Richmond, 2 pages,
recorded 1955-12-21, plus the class spec's standing prediction.

**Class membership — I predicted NOT a member, ~35% it is one.** Base rate for an
arbitrary Richmond deed being a developer covenant scheme is low.

Predicted to fire: TITLE, VALUE, IDENTITY, ENCUMBRANCE as `ASSERT` not `CREATE`.
Predicted not to fire: ENVELOPE, OCCUPANCY, ENTITLEMENT, PERMIT.
**Predicted as live §2 deviations to hunt: `COST` firing on federal documentary
stamps rather than a building-cost floor; `CAPITAL` on a subject-to mortgage;
`AS_BUILT` on "together with the building thereon."** Predicted era differences:
typewritten fills not copperplate, NYBTU printed short form, rd carries parties,
revenue stamps present. Predicted spec §3 fields absent: covenant expiry, cost
floor, prohibited trades, private approval right.

**Scored below in "Prediction — what it got right and wrong".**

```
instrument: 1955-12-14
acknowledged: 1955-12-16
recorded: 1955-12-21
expires: UNKNOWN
```

⚠ **There are TWO acknowledgments and the block has one slot.** Johnson
acknowledged 1955-12-14 in New York County; Morgan acknowledged 1955-12-16 in
Westchester County. I wrote the later one, because that is when the instrument
became fully acknowledged. The earlier is E10. **Card 10 — several candidates
coincide:** the instrument date and Johnson's acknowledgment are both 1955-12-14,
so `instrument` here is not independently corroborated by a distinct date.

**rd** supplies: book 1338, page 184, `doc_type DEED`, recorded 12/21/1955,
`amount $0.00`, and one parcel — **5001590000**. ⚠ **rd's lot is `0000`, a
placeholder, not a lot.** The document designates *the lots numbered 24 and 25* on
a filed map, which are **map lots, not tax lots**. I wrote rd's BBL on every
placed row and composed nothing. The instrument's own registry statement is
*"Section 1, in Block 159 on the Land Map of the County of Richmond"* — block
only, no lot, which is exactly why rd's lot is a placeholder.

**Granularity rule, restated from m1 so a row-count delta is diagnosable:** one row
per act that could be separately breached, separately enforced, or separately
falsified. 11 event rows + 4 registry lane rows.

## Events

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | p1 · [0.15,0.078,0.82,0.200] · native · plain · "JOHN QUINCY JOHNSON, JR., (residing at No. 200-05 111th Avenue, Hollis, Long Island, N.Y.) ... individually, and as executor ... under the Last Will and Testament of Blanche E. Dadswell, deceased" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the instrument  about: John Quincy Johnson, Jr. | 2 capacities | Conveys in **two capacities at once** — in his own right and as fiduciary of a decedent's estate. Two distinct sources of title pass under one granting clause, and the deed does not say what share came from which. Address is the only one given for him | Johnson signs both individually and as executor of Blanche E. Dadswell's will |
| E2 | p1 · [0.15,0.078,0.82,0.200] · native · plain · "BLANCHE ESTELLE MORGAN, formerly Blanche Estelle Johnson, (residing at No. 17 Kent Road, Scarsdale, N. Y.), individually, and as ... executrix" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the instrument  about: Blanche Estelle Morgan | 1 prior name; 2 capacities | A stated **name change** — Morgan was formerly Johnson — which is IDENTITY's core trigger and the first one this class has produced. Same dual capacity as E1. She shares a surname with co-grantor John Quincy Johnson, Jr.; the deed states no relationship between them and I infer none | Blanche Estelle Morgan, formerly Blanche Estelle Johnson, signs individually and as executrix |
| E3 | p1 · [0.15,0.078,0.82,0.200] · native · plain · "the Last Will and Testament of Blanche E. Dadswell, deceased, (said decedent also having been known as Blanche Estelle Dadswell)" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the instrument  about: Blanche E. Dadswell, deceased | 1 alias | An alias for the **deceased testator**, a different person from E2's grantor. ⚠ **rd disagrees and I correct neither (card 9).** rd lists `MORGAN BLANCHE ESTELLE`, `JOHNSON BLANCHE ESTELLE` and `DADSWELL BLANCHE ESTELLE` all as *Grantor*, collapsing the living executrix and the dead testator into one party. On the page Morgan = Johnson is stated; Morgan = Dadswell is **not**, and cannot be — one signs, the other is deceased | The decedent whose will is being executed was also known as Blanche Estelle Dadswell |
| E4 | p1 · [0.15,0.265,0.85,0.330] · native · plain · "in consideration of ten dollars and other valuable consideration paid by the party of the second part" | 1955-12-14 | instrument | | VALUE | ASSERT | 5001590000 | Fulton L. Reid and Edna G. Reid → John Quincy Johnson, Jr. and Blanche Estelle Morgan | $10.00 stated | Plus "other valuable consideration", UNKNOWN — the deed states no amount. rd `amount` is **$0.00** against a deed reciting ten dollars; both stand. The $13.20 of federal stamps at E12 implies a real price, but the stamp *rate* is nowhere on the document, so computing one would be card 4 | Consideration is $10 plus other valuable consideration of unstated amount |
| E5 | p1 · [0.15,0.265,0.85,0.330] · native · struck · "ALL ~~that~~ certain ~~plot,~~ pieces or parcels of land ... lying and being ~~in the~~ on the westerly side of Oakland Avenue" with "those two lots" typed above the line | 1955-12-14 | instrument | | TITLE | TRANSFER | 5001590000 | John Quincy Johnson, Jr. and Blanche Estelle Morgan → Fulton L. Reid and Edna G. Reid | 115 ft x 50 ft = 5750 sq ft | Granting words at the same rect: *"does hereby grant and release unto the party of the second part, the heirs or successors and assigns of the party of the second part forever"* — fee. Description and map at p1 · [0.15,0.330,0.88,0.420]: *"Map of property belonging to John Frederick Smith, West New Brighton ... July 1906, Henry P. Morrison, C.E."*, **filed Richmond County Clerk 1907-08-15 as Map Number 941-A**, *"the lots numbered 24 and 25 ... taken together as one parcel"*. Beginning 657.47 ft north of Castleton Ave on the west side of Oakland Ave. Habendum and appurtenances at p1 · [0.15,0.650,0.82,0.800], one act, one row. **Also conveys the street bed** — *"all right, title and interest, if any ... to any streets and roads abutting ... to the center lines thereof"* — land with no BBL, which no `bbls` form can fan. Grantees are *"his wife"*; no tenancy is stated and I infer none. The four typewriter edits do not change the land conveyed, so no separate STRUCK row (card 3) | Johnson and Morgan convey map lots 24 and 25 on Oakland Avenue to the Reids in fee |
| E6 | p1 · [0.15,0.265,0.85,0.330] · native · plain · "with the buildings and improvements thereon erected" | 1955-12-14 | instrument | | AS_BUILT | ASSERT | 5001590000 | asserted by: the grantors  about: map lots 24 and 25 | UNKNOWN(no dimension, storey count or material is stated) | ⚠ **§2 deviation. AS_BUILT is measured at 0 of 99 rows on m1 and the standing prediction says it stays at zero.** Printed form language, so a reader may fairly discount it — but the drafter edited this exact line four times and left this clause standing, and it is the only statement in either page about what is on the ground. Bears on TITLE: the buildings are part of what is conveyed | The deed states that buildings and improvements stand on the premises |
| E7 | p1 · [0.15,0.650,0.82,0.800] · native · plain · "the party of the first part covenants that the party of the first part has not done or suffered anything whereby the said premises have been encumbered in any way whatever, except as aforesaid" | 1955-12-14 | instrument | | ENCUMBRANCE | ASSERT | 5001590000 | asserted by: John Quincy Johnson, Jr. and Blanche Estelle Morgan  about: map lots 24 and 25 | UNKNOWN(an asserted absence, not a count) | Card 5 second state — a real asserted absence, limited to the grantors' own acts. ⚠ **"except as aforesaid" points at nothing.** Nothing earlier in the instrument states any encumbrance, so the exception has no antecedent and I cannot tell what it reserves (card 12). On m1 the same form clause read *"excepting as to said restrictions"* and had one | The grantors covenant they have done nothing to encumber the premises, except as aforesaid |
| E8 | p1 · [0.15,0.650,0.82,0.800] · native · plain · "in compliance with Section 13 of the Lien Law, covenants that the party of the first part will receive the consideration for this conveyance and will hold the right to receive such consideration as a trust fund to be applied first for the purpose of paying the cost of the improvement" | 1955-12-14 | instrument | UNKNOWN(ends when the cost of the improvement is paid; the deed states no date) | COST | CREATE | 5001590000 | John Quincy Johnson, Jr. and Blanche Estelle Morgan → Fulton L. Reid and Edna G. Reid | UNKNOWN(the trust is over the whole consideration, which is not stated) | A **statutory trust over the sale proceeds**. Filed under COST as the nearest of the eleven — *duties to spend*. What that loses: this is not money spent on the parcel and it does not burden the land; it is a personal fiduciary duty over money the grantors receive, enforceable by unpaid contractors who are not parties to this deed. See "Fits none of the eleven" | The grantors must hold the sale money in trust to pay for improvements first |
| E9 | p1 · [0.40,0.820,0.88,0.960] · native · plain · "IN WITNESS WHEREOF, the party of the first part has duly executed this deed the day and year first above written" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | John Quincy Johnson, Jr. and Blanche Estelle Morgan → Fulton L. Reid and Edna G. Reid | 2 signatories | Signed *"John Quincy Johnson, Jr., individually and as executor"* and *"Blanche Estelle Morgan, individually and as executrix, under the Last Will and Testament of Blanche E. Dadswell, deceased."* `basis` is `instrument` because the deed states no execution date, dating itself only by reference. **No corporate seal and no subscribing witness** — the printed "IN PRESENCE OF:" line is blank | Both grantors execute the deed, each in both capacities |
| E10 | p2 · [0.20,0.040,0.58,0.220] · native · plain · "On the 14 day of December, 1955, before me personally came JOHN QUINCY JOHNSON, JR., individually and as executor ... and acknowledged that he executed the same, individually, and as such executor" | 1955-12-14 | acknowledgment | | IDENTITY | ASSERT | 5001590000 | John Quincy Johnson, Jr. → Jack Fialkin, Notary Public | 1 deponent | Venue **New York County**. Jack Fialkin, Notary Public State of New York, No. 24-1205900, qualified in Kings County, commission expires 1957-03-30, with an inked seal impression over the text. Same calendar day as the instrument date | Johnson acknowledges in New York County on 14 December 1955 |
| E11 | p2 · [0.55,0.040,0.93,0.220] · native · plain · "On the 16th day of December, 1955, before me personally came BLANCHE ESTELLE MORGAN, individually and as executrix ... and acknowledged that she executed the same, individually, and as such executrix" | 1955-12-16 | acknowledgment | | IDENTITY | ASSERT | 5001590000 | Blanche Estelle Morgan → Fred J. Hoff, Notary Public | 1 deponent | Venue **Westchester County**, two days after E10 and in a different county. Fred J. Hoff, Notary Public in the State of New York, appointed in Westchester County, State No. 60-6926300, commission expires 1956-03-30. The two lower acknowledgment blocks on this page — corporate form and subscribing-witness form — are printed and entirely blank | Morgan acknowledges in Westchester County on 16 December 1955 |

## Registry lane

Not one of the eleven — it asks about the instrument, not a parcel. `bbls: INSTRUMENT`.

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E12 | p1 · [0.05,0.030,0.20,0.220] · native · plain · "DOCUMENTARY / UNITED STATES INTERNAL REVENUE / TEN DOLLARS" and p1 · [0.05,0.185,0.22,0.420] · native · plain · "THREE DOLLARS" and "20 CENTS" | 1955-12-21 | recorded | | COST | ASSERT | INSTRUMENT | asserted by: the United States Internal Revenue  about: this conveyance | $13.20 | Three federal documentary stamps affixed in the left margin of p1, each cancelled with the `DEC 21 1955` date stamp. The stated total $13.20 is the sum of its three stated parts: $10.00 + $3.00 + $0.20 — the document checks itself. ⚠ **§2 deviation: COST fires, and for a reason m1 had none of.** m1's five COST rows were all a building-cost floor; this is a tax. **m1 had no stamp at all** and its readers recorded that as a search negative | Federal documentary stamps of $13.20 are affixed and cancelled |
| E13 | p2 · [0.20,0.745,0.95,0.960] · native · plain · "RECEIVED COUNTY CLERK'S OFFICE DEC 21 3 10 PM 1955 RICHMOND COUNTY" | 1955-12-21 | recorded | | IDENTITY | ASSERT | INSTRUMENT | asserted by: the Richmond County Clerk  about: this instrument | 1 receipt, at 15:10 | The registry's **receipt**, six minutes before its recording at E14. `function` is forced: none of the eleven asks about filing, so IDENTITY is the least-wrong shelf | The County Clerk received the deed at 3:10 PM on 21 December 1955 |
| E14 | p2 · [0.20,0.745,0.95,0.960] · native · plain · "Recorded in the Richmond County Clerk's Office on Dec 21 1955 at 3.16 P Liber 1338 Page 184 of Deeds and Indexed under Block Number 159" | 1955-12-21 | recorded | | IDENTITY | ASSERT | INSTRUMENT | asserted by: the Richmond County Clerk  about: this instrument | 1 recording, at 15:16 | Agrees with rd — book 1338, page 184, recorded 12/21/1955. The stamped liber head on p1 reads `LIBER 1338 PAGE 184` and on p2 `LIBER 1338 PAGE 185`; **rd carries only 184 and I reconcile neither (card 8)**. The clerk's handwritten page digit is ambiguous between 8 and 6; I read 184 because the stamp and rd both say so, and record the ambiguity rather than hide it. **Indexed under block only, no lot** — the source of rd's `0000` | The deed was recorded at 3:16 PM in liber 1338, page 184, indexed under block 159 |
| E15 | p2 · [0.20,0.490,0.75,0.760] · native · plain · "RECORDED AT REQUEST OF FREDERICK L. HACKENBURG 21 EAST 40" Street New York 16, N.Y." | 1955-12-21 | recorded | | IDENTITY | ASSERT | INSTRUMENT | asserted by: the instrument  about: Frederick L. Hackenburg | 1 return-to party | The only agent address on either page, and a Manhattan one for a Staten Island parcel. Appears nowhere in rd, whose party list has six names and not this one — NOT_CHECKABLE. The same endorsement carries the instrument's own parcel statement: *"The land affected by the within instrument lies in Section 1, in Block 159 on the Land Map of the County of Richmond"* | The recorded deed is directed back to Frederick L. Hackenburg in Manhattan |

## SEARCH RECORD

Negatives are not rows (card 1). Where I looked, and how closely.

| region | dpi | found |
|---|---|---|
| p1 · [0.05,0.030,0.20,0.220] | native | the $10 documentary stamp and two `DEC 21 1955` cancellations; no state or city transfer stamp |
| p1 · [0.05,0.185,0.22,0.420] | native | the $3 and $.20 documentary stamps; no other stamp below them |
| p1 · [0.15,0.650,0.82,0.800] | native | the two grantor covenants; **no "subject to" clause, no mortgage, no restrictive covenant of record** |
| p1 · [0.15,0.330,0.88,0.420] | native | description and map reference only; no easement, no reservation, no exception |
| p2 · [0.20,0.040,0.58,0.220] and [0.55,0.040,0.93,0.220] | native | the two executed acknowledgments; the corporate and subscribing-witness blocks below are printed and blank |
| p2 · [0.20,0.745,0.95,0.960] | native | the receipt and recording endorsements; **the printed `RECORDING FEE $` line carries no legible amount** — a handwritten `12930` and a `6` sit nearby but are not on that line, and card 4 forbids reading either as a fee |
| p2 · [0.20,0.490,0.75,0.760] | native | the endorsement back; `Title No.` is blank |

**CAPITAL, ENTITLEMENT, ENVELOPE, OCCUPANCY, PERMIT: I found nothing** — card 5
state 1, not an asserted absence. No debt, no development right, no building
restriction, no use restriction, no government act anywhere on either page.

## Fits none of the eleven

- **The rule of construction.** p1 · [0.15,0.650,0.82,0.800] · native · plain ·
  *"The word 'party' shall be construed as if it read 'parties' whenever the sense
  of this indenture so requires."* This is operative here — there are two grantors
  and two grantees, and the whole form is written in the singular. It is a
  direction about **how to read the text**, not a claim about a parcel, a party or
  the paper's registry history. Filing it under IDENTITY would say the deed
  asserts something about who someone is, which it does not. It has no row.
- **The Lien Law §13 trust fund** (E8) is filed under COST under protest. It is a
  personal fiduciary duty over sale proceeds, enforceable by non-parties, that
  neither burdens the land nor spends money on it. **Candidate function**, and it
  is the second class in a row to produce one.
- **Land conveyed with no BBL.** E5 also conveys the bed of Oakland Avenue to its
  centre line. No `bbls` form reaches it: it is not rd's BBL, it is not a `SET:`
  criterion the document defines, and `UNPLACED` would drop the whole conveyance.
  It is folded into E5 and is therefore invisible to Reorganize.

## Brief

On 14 December 1955 John Quincy Johnson, Jr. of Hollis and Blanche Estelle Morgan
of Scarsdale — formerly Blanche Estelle Johnson — conveyed a 115 by 50 foot parcel
on the westerly side of Oakland Avenue at West New Brighton, Staten Island, to
Fulton L. Reid and Edna G. Reid, his wife, of 232 Oakland Avenue, for ten dollars
and other valuable consideration. Each grantor signed twice over: in their own
right, and as executor and executrix of the will of Blanche E. Dadswell, deceased,
also known as Blanche Estelle Dadswell.

The land is map lots 24 and 25 on the *Map of property belonging to John Frederick
Smith*, surveyed by Henry P. Morrison in July 1906 and filed with the Richmond
County Clerk on 15 August 1907 as Map Number 941-A, taken together as one parcel
and conveyed with the buildings and improvements on it and with the grantors'
interest in the abutting street bed. The deed is a Standard N.Y.B.T.U. Form 8002
bargain and sale with covenant against grantor's acts: no warranty, one covenant
that the grantors have themselves done nothing to encumber the premises, and the
statutory Lien Law trust over the purchase money. It creates no restriction of any
kind and none is recited against the land.

Johnson acknowledged in New York County on 14 December and Morgan in Westchester
County on 16 December, before different notaries. The County Clerk received the
deed at 3:10 PM on 21 December 1955 and recorded it six minutes later in liber
1338, page 184, indexed under block 159 with no lot — which is why rd's BBL ends
in a `0000` placeholder. Federal documentary stamps of $13.20 are affixed and
cancelled in the left margin. It was returned to Frederick L. Hackenburg, 21 East
40th Street, Manhattan.
