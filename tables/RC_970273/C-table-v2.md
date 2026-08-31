# RC_970273 — Extractor C — m2 cold read

Standard N.Y.B.T.U. Form 8002 — **Bargain and Sale Deed with Covenant against
Grantor's Acts**, Richmond County, Liber 1338 page 184. Two pages: p1 the instrument,
p2 the acknowledgments and endorsement back (rotated 90°).

**Verdict on class membership: NOT a member of `DEED-RESTRICTIVE-COVENANT`.** See
`§ Class membership` below. There is no covenant scheme, no expiry, no developer
grantor, and no reserved right. It is a private resale by two individuals, one of
them a fiduciary.

```
instrument: 1955-12-14
acknowledged: 1955-12-16
recorded: 1955-12-21
expires: UNKNOWN
```

⚠ **`acknowledged:` has one slot and this deed has two acknowledgments** — Johnson on
**1955-12-14** in New York County, Morgan on **1955-12-16** in Westchester County,
before different notaries. I wrote the later, the first date on which the instrument
was fully acknowledged. Both are rows E11 and E12.

⚠ **`expires: UNKNOWN` is the wrong shape and it is the only value available.**
Nothing in this instrument self-expires; there is no term to end. `UNKNOWN` says *the
document does not state it*, which reads as a gap in my reading. This is the same
two-states-where-three-are-needed problem that `until` was just given
`UNKNOWN(<reason>)` to fix, one level up in the labelled block.

rd's only parcel is **`5001590000`** — borough 5, block 00159, **lot `0000`**, a
placeholder. It confirms the block and identifies no lot. The document's own
designations are in `terms` and were never composed into a BBL.

## Events

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | p1 · [0.16,0.100,0.80,0.212] · plain · "BETWEEN JOHN QUINCY JOHNSON, JR., (residing at No. 200-05 111th Avenue, Hollis, Long Island, N.Y.) and BLANCHE ESTELLE MORGAN ... party of the first part, and FULTON L. REID and EDNA G. REID, his wife, both residing at No. 232 Oakland Avenue, West New Brighton, Staten Island, N. Y." | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the indenture  about: John Quincy Johnson Jr and Blanche Estelle Morgan, and Fulton L. Reid and Edna G. Reid | 2 grantors, 2 grantees | The grantees are **"his wife"** — a marital relation stated, but **no tenancy is named**: the habendum runs to "the heirs or successors and assigns", the form's singular boilerplate. Whether they take as tenants by the entirety is not on the page (card 12). The grantees' stated address, No. 232 Oakland Avenue West New Brighton, is on the same avenue as the premises; the deed does not say it is the premises and I do not infer it. Printed form closes with "The word 'party' shall be construed as if it read 'parties' whenever the sense of this indenture so requires" — operative here, since every party slot holds two people. | Two grantors convey to Fulton L. Reid and Edna G. Reid, husband and wife. |
| E2 | p1 · [0.16,0.100,0.80,0.180] · plain · "BLANCHE ESTELLE MORGAN, formerly Blanche Estelle Johnson ... individually, and as executor and executrix, respectively, under the Last Will and Testament of Blanche E. Dadswell, deceased, (said decedent also having been known as Blanche Estelle Dadswell)" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the indenture  about: Blanche Estelle Morgan, and the decedent Blanche E. Dadswell | 2 aliases; 2 capacities per grantor | **Two alias assertions about two different people, plus the authority to convey.** Morgan was **formerly Blanche Estelle Johnson**; the decedent Blanche E. Dadswell was **also known as Blanche Estelle Dadswell**. Both grantors sign twice over — individually *and* as executor/executrix under Dadswell's will — so the deed conveys both their own interests and the estate's. ⚠ **rd lists FOUR grantors**: `JOHNSON JOHN QUINCY JR`, `MORGAN BLANCHE ESTELLE`, `JOHNSON BLANCHE ESTELLE`, `DADSWELL BLANCHE ESTELLE`. The document has **two**. rd has promoted Morgan's former name into a separate grantor and the deceased testator into a grantor she cannot be. Both records stand, neither corrected (card 9). rd also types every natural person as `column: company` with `person: ""`. | Morgan conveys under a former name, and both grantors also act as executors of Blanche E. Dadswell's will. |
| E3 | p1 · [0.16,0.272,0.80,0.302] · plain · "in consideration of ten dollars and other valuable consideration paid by the party of the second part" | 1955-12-14 | instrument | | VALUE | ASSERT | 5001590000 | Fulton L. Reid and Edna G. Reid → John Quincy Johnson Jr and Blanche Estelle Morgan | 10 USD | The "other valuable consideration" is `UNKNOWN(no amount, form or payer stated)`. rd `amount` reads `$0.00` against the deed's ten dollars — both stand (card 9). ⚠ **The true price is recoverable but not from this page.** E9's $13.20 of federal documentary stamps is a fixed function of the consideration under the 1932–1967 stamp tax, but the *rate* is in a statute, not in the document. Writing a price here would be exactly the inference card 4 forbids. | Recited consideration is ten dollars plus unstated other consideration. |
| E4 | p1 · [0.16,0.293,0.62,0.330] · struck · "ALL ~~that~~ ⟨those two lots⟩ certain ~~plot,~~ piece[s] or parcel[s] of land" | 1955-12-14 | instrument | | TITLE | TRANSFER | 5001590000 | John Quincy Johnson Jr and Blanche Estelle Morgan, individually and as executors → Fulton L. Reid and Edna G. Reid | 2 lots; 115 ft x 50 ft | One conveyance. Granting words p1 · [0.16,0.272,0.80,0.302] "does hereby grant and release unto the party of the second part, the heirs or successors and assigns of the party of the second part forever"; habendum and together-with p1 · [0.16,0.665,0.80,0.725]. **Mark:** the printed singular is amended by typewriter overstrike — `that` and `plot,` x-ed out, `those two lots` typed above the line, `s` added to `piece` and `parcel`, and `in the` x-ed out lower down. Under card 3 this earns **no row of its own**: the courses and the lot numbers already convey both lots, so the struck text standing would not have changed what passes. Mode order is unrecoverable (card 1). **`bbls` cannot hold what this row also conveys:** "TOGETHER with all right, title and interest, if any ... to any streets and roads abutting the above described premises **to the center lines thereof**" reaches the bed of Oakland Avenue, which has no BBL in rd. | The two grantors convey lots 24 and 25 with the abutting street beds. |
| E5 | p1 · [0.16,0.340,0.82,0.400] · plain · "known and designated on a certain map entitled 'Map of property belonging to John Frederick Smith, West New Brighton, Borough of Richmond, City of New York, July 1906, Henry P. Morrison, C.E., July 1906' and filed in the office of the Clerk of the County of Richmond August 15th, 1907 as Map Number 941-A as and by the lots numbered 24 and 25" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | asserted by: the indenture  about: lots 24 and 25 on Map Number 941-A | 2 lots on Map Number 941-A | **Two designation systems, and the deed keeps them apart.** The subdivision map gives lots 24 and 25 on Map 941-A; the endorsement back p2 · [0.36,0.500,0.72,0.740] gives "The land affected by the within instrument lies in Section 1, in Block 159 on the Land Map of the County of Richmond". rd carries only the second, with lot `0000`. Nothing on either page equates a Map 941-A lot number to a Land Map lot. Filing is **asserted outright** — "and filed in the office of the Clerk ... August 15th, 1907" — unlike m1's "or intended to be filed", so this is not card 5's third state. **1907-08-15 is a fourth kind of date** with no slot in the labelled block. Courses p1 · [0.16,0.405,0.82,0.535]: from a point 657.47 ft north of Castleton Avenue on the westerly side of Oakland Avenue, west 115 ft along lot 23 to land now or formerly of Alexander C. Watkins, north 50 ft to the dividing line between lots 25 and 26, east 115 ft, south 50 ft. | The parcel is lots 24 and 25 on filed Map 941-A, lying in Section 1, Block 159. |
| E6 | p1 · [0.16,0.293,0.62,0.330] · plain · "with the buildings and improvements thereon erected" | 1955-12-14 | instrument | | AS_BUILT | ASSERT | 5001590000 | asserted by: the indenture  about: lots 24 and 25 | UNKNOWN(no count, storey, dimension or material is stated) | ⚠ **Deviation from the spec §2 signature, which records `AS_BUILT` at 0 rows of 99 on m1 and predicts it will not fire.** It fires here. m1's reason was that nothing had been built on a vacant platted lot; this is a 1955 resale of a lot subdivided in 1906, and the granting clause says improvements are present. **Honest qualification: this is printed form boilerplate, not a typed fill**, so a reader who folds it into E4 is not wrong. I emit it because the framework's `AS_BUILT` trigger list names *improvements actually present*, and because reporting a deviation is worth more than a tidy match to the prediction. | The deed passes buildings and improvements standing on the land. |
| E7 | p1 · [0.16,0.748,0.80,0.772] · plain · "the party of the first part covenants that the party of the first part has not done or suffered anything whereby the said premises have been encumbered in any way whatever, except as aforesaid" | 1955-12-14 | instrument | | ENCUMBRANCE | ASSERT | 5001590000 | John Quincy Johnson Jr and Blanche Estelle Morgan → Fulton L. Reid and Edna G. Reid | UNKNOWN(an absence, not a quantity) | Card 5's second state — a real asserted absence, narrow: only the grantors' **own acts**, not the state of title. ⚠ **"except as aforesaid" points at nothing.** Nowhere on either page is an exception recited — no restrictions, no mortgage, no easement, no "subject to". On m1 the same form phrase read "excepting as to said restrictions and limitations" and there were restrictions. Here the carve-out is empty on its face, and I cannot tell whether that is a form artifact or a reference to something omitted (card 12). | The grantors covenant they have themselves done nothing to encumber the land. |
| E8 | p1 · [0.16,0.768,0.80,0.815] · plain · "in compliance with Section 13 of the Lien Law, covenants that the party of the first part will receive the consideration for this conveyance and will hold the right to receive such consideration as a trust fund to be applied first for the purpose of paying the cost of the improvement" | 1955-12-14 | instrument | UNKNOWN(ends when the cost of the improvement is paid; the instrument states no date) | COST | CREATE | 5001590000 | John Quincy Johnson Jr and Blanche Estelle Morgan → Fulton L. Reid and Edna G. Reid | UNKNOWN(the fund is the whole consideration, which is not stated) | A statutory trust over the sale proceeds: the grantors must apply the price first to the cost of the improvement before any other purpose. Filed `COST` as the nearest of the eleven — it is a duty to spend. ⚠ **What that loses: the object of this obligation is a fund, not the land.** Every one of the eleven asks a question *about a parcel*; this one binds money in the grantors' hands for the benefit of anyone who improves the property. It also does not run with the land, so `ENCUMBRANCE` is wrong. | The grantors must apply the sale proceeds first to the cost of the improvement. |
| E9 | p1 · [0.07,0.050,0.20,0.42] · marginal · "DOCUMENTARY ... UNITED STATES INTERNAL REVENUE ... 10 TEN DOLLARS 10" with "3 THREE DOLLARS 3" and "20 CENTS 20" | 1955-12-14 | instrument | | COST | ASSERT | 5001590000 | John Quincy Johnson Jr and Blanche Estelle Morgan → United States Internal Revenue | 13.20 USD | Three U.S. Internal Revenue documentary stamps affixed in the left margin of p1 — **$10.00 + $3.00 + $0.20 = $13.20** — each cancelled by hand "DEC 21 1955". A federal tax on the conveyance, paid by the parties, **not** a registry act: the stamps sit in the body margin, not in the clerk's box. ⚠ **framework.md sends "any fee or stamp" to the registry lane**, which would put this below the table where it has no function and no BBL to fan — so a transfer tax on this parcel would never reach the parcel's history. I have kept it as an event row and flagged the tension. Date basis is the conveyance, not the 12-21 cancellation. | $13.20 in federal documentary stamps was affixed and cancelled. |
| E10 | p1 · [0.40,0.845,0.85,0.985] · plain · "John Quincy Johnson, Jr., individually and as executor, and Blanche Estelle Morgan, individually and as executrix, under the Last Will and Testament of Blanche E. Dadswell, deceased" | 1955-12-14 | instrument | | IDENTITY | ASSERT | 5001590000 | John Quincy Johnson Jr and Blanche Estelle Morgan → the estate of Blanche E. Dadswell and themselves | 2 signatures | Both grantors subscribe, each stating the two capacities under the signature. "IN WITNESS WHEREOF ... has duly executed this deed the day and year first above written" ties execution to the instrument date, so **instrument and execution coincide and I did not have to discriminate** (card 10). The printed "IN PRESENCE OF:" line is **blank** — no subscribing witness. | Both grantors sign, individually and as executors. |
| E11 | p2 · [0.22,0.048,0.58,0.180] · plain · "On the 14 day of December, 1955, before me personally came JOHN QUINCY JOHNSON, JR., individually and as executor ... and acknowledged that he executed the same, individually, and as such executor" | 1955-12-14 | acknowledgment | | IDENTITY | ASSERT | 5001590000 | John Quincy Johnson Jr → Jack Fialkin, Notary Public | 1 deponent | Taken in **New York County** before **Jack Fialkin**, Notary Public, State of New York, No. 24-1205900, qualified in Kings County, commission expires 1957-03-30. Same date as the instrument. The notary's seal impression overlaps the printed text at the lower left and obscures part of "to me known to be the individual"; the wording is legible from the printed form (card 9 — accepted, form is sole witness for the obscured words). | Johnson acknowledges in New York County on 14 December. |
| E12 | p2 · [0.55,0.048,0.93,0.180] · plain · "On the 16th day of December, 1955, before me personally came BLANCHE ESTELLE MORGAN, individually and as executrix ... and acknowledged that she executed the same, individually, and as such executrix" | 1955-12-16 | acknowledgment | | IDENTITY | ASSERT | 5001590000 | Blanche Estelle Morgan → Fred J. Hoff, Notary Public | 1 deponent | Taken **two days later in Westchester County** before **Fred J. Hoff**, Notary Public, appointed in Westchester County, State No. 60-6926300, commission expires 1956-03-30. ⚠ **This is the second acknowledgment and the labelled block holds one.** The two grantors never appeared together; the deed was signed 12-14 and completed 12-16. The two remaining printed acknowledgment forms on p2 — corporate, and subscribing witness — are entirely **blank**. | Morgan acknowledges in Westchester County on 16 December. |

**12 events.**

## Registry lane

`bbls: INSTRUMENT`. Not one of the eleven — these ask about the paper.

| # | citation | date | what it records |
| --- | --- | --- | --- |
| R1 | p2 · [0.20,0.735,0.36,0.870] · marginal · "RECEIVED COUNTY CLERK'S OFFICE DEC 21 3 10 PM 1955 RICHMOND COUNTY" | 1955-12-21 | **A received time distinct from the recorded time.** Struck-in clerk's stamp. The minute digits are indistinct; I read `3 10 PM` and cannot exclude `3 11 PM`. |
| R2 | p2 · [0.61,0.730,0.82,0.950] · plain · "Recorded in the Richmond County Clerk's Office on Dec 21/1955 at 3 16 P M. Liber 1338 Page 184 ... and Indexed under Block Number 159" | 1955-12-21 | Recorded **3:16 PM**, six minutes after receipt. Liber 1338 page 184 — agrees with rd `book`/`page`. Indexed under **Block Number 159** — agrees with rd's block. Signed by the County Clerk; the surname is not legible enough to transcribe. |
| R3 | p2 · [0.36,0.500,0.72,0.740] · plain · "Recorded at Request of FREDERICK L. HACKENBURG, 21 EAST 40th Street, New York 16, N.Y." | 1955-12-21 | The return-to / requesting party, and the only agent address on either page. |
| R4 | p2 · [0.470,0.730,0.560,0.935] · uncertain · "No. ... RECORDING FEE $ ..." with a handwritten "6" | 1955-12-21 | ⚠ **Recording fee: `UNKNOWN`.** One handwritten `6` sits on the dotted leader **between** the `No.` blank and the `RECORDING FEE $` blank, and I cannot tell which it fills. A second handwritten number at the head of the box reads `12930` or `12030` — I cannot resolve the third digit. Card 4: *a stamp reading 16.00 with no label is not a fee*; a digit with an ambiguous label is not one either. |

## SEARCH RECORD

Crops come from the **3164 × 4190 native scan**, unresampled, so these carry `native`
rather than a dpi (card 1).

| region | dpi | found |
| --- | --- | --- |
| p1 · [0.07,0.050,0.20,0.42] | native | the three documentary stamps and their DEC 21 1955 cancellations — nothing else in the left margin |
| p1 · [0.16,0.665,0.80,0.725] | native | together-with and habendum only; **no "subject to" clause, no restrictions, no easement, no mortgage recital** |
| p2 · [0.19,0.740,0.99,0.960] | native | the clerk's box: received stamp, recorded line, two handwritten numbers, and the `RECORDING FEE $` blank discussed at R4 |
| p2 · [0.36,0.500,0.72,0.740] | native | endorsement panel: form title, Section/Block, return-to party. A `Title No.` blank, **empty** |

**Not found, as distinct from asserted absent (card 5, state 1):** no covenant block,
no building restriction, no use restriction, no expiry clause, no reserved right in
any grantor, no mortgage, no reference to any prior recorded declaration. The only
asserted absence on the document is E7, and it is narrow.

## Class membership — NOT a member

| §1 signal | fired? | evidence |
| --- | --- | --- |
| 1 · grantor is a development company | **no** | Two natural persons, one a fiduciary. A subdivider *is* named — "Map of property belonging to **John Frederick Smith**", 1906 — but he is not a party and is 49 years upstream. |
| 2 · filed-map reference the lot numbers depend on | **yes** | Map Number 941-A, Richmond County Clerk, 1907-08-15. Without it "lots 24 and 25" is not a location. **This is the only signal that fires**, and it fires for any platted-lot deed, so it does not discriminate. |
| 3 · covenant block with a stated expiry | **no** | There is no covenant block. Nothing expires. |
| 4 · reserved rights running back to the grantor | **no** | Nothing is reserved. |

One signal of four, and it is the weakest one. The operative weight of this
instrument is entirely in the **grant** — the opposite of §1's headline test. This is
a **fiduciary resale on a standard N.Y.B.T.U. form**, and if it belongs to a class it
is that one.

⚠ **rd types it `DEED`, and §1's untested prediction about the register type holds** —
but it holds for a document that is not in the class, so it says nothing about the
class.

## Index check — rd vs the document

| rd field | rd says | document says | verdict |
| --- | --- | --- | --- |
| `instrument` | `""` | no instrument number; the clerk's box has a handwritten `12930`/`12030` that may be one | NOT_CHECKABLE |
| `book` / `page` | `1338` / `184` | "LIBER 1338 PAGE 184" stamped on p1; "Liber 1338 Page 184" in the recording line | agrees |
| `doc_type` | `DEED` | "Bargain and Sale Deed with Covenant against Grantor's Acts" | agrees |
| `recorded` | `12/21/1955` | recorded 3:16 PM 1955-12-21; received 3:10 PM | agrees; rd carries neither time |
| `amount` | `$0.00` | "ten dollars and other valuable consideration" | **disagrees.** Both stand. |
| `parcels` | `5001590000` | Section 1, Block 159 (Land Map); lots 24 and 25 (Map 941-A) | block agrees; **lot `0000` is a placeholder and confirms no lot** |
| `parties` | 4 grantors, 2 grantees | **2 grantors**, 2 grantees | **disagrees.** rd splits one grantor's former name into a second grantor and lists the deceased testator as a third. |
| `status` | `Recorded` | recording line present | agrees |

## Brief

On 14 December 1955 John Quincy Johnson, Jr. of Hollis and Blanche Estelle Morgan of
Scarsdale — she formerly Blanche Estelle Johnson — conveyed two Staten Island lots to
Fulton L. Reid and Edna G. Reid, his wife, on a standard bargain-and-sale form with
covenant against grantor's acts. Each grantor signed twice over: individually, and as
executor and executrix under the will of Blanche E. Dadswell, also known as Blanche
Estelle Dadswell, so the deed carries both their own interests and the estate's.

The land is lots 24 and 25 on Map Number 941-A, a 1906 survey of property belonging
to John Frederick Smith filed in 1907, a 115 by 50 foot parcel on the west side of
Oakland Avenue at West New Brighton, bounded west by land of Alexander C. Watkins.
The endorsement places it in Section 1, Block 159 on the County Land Map. The deed
passes the buildings and improvements standing on it and the abutting street beds to
their centre lines.

The stated price is ten dollars and other consideration; $13.20 of federal
documentary stamps in the margin says the real figure was larger. The grantors
covenant only that they have themselves encumbered nothing, "except as aforesaid" —
and nothing is aforesaid. Johnson acknowledged in New York County on the 14th, Morgan
in Westchester on the 16th; the deed reached the Richmond County Clerk at 3:10 PM on
21 December and was recorded six minutes later in Liber 1338 page 184.
