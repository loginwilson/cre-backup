# 2002122000002001 — Extractor C — cross-class probe

**SATISFACTION OF MORTGAGE.** ACRIS digital, Manhattan, CRFN 2003000000003.
p1 is the Recording and Endorsement Cover Page; p2 is the instrument itself
(form `NY00 12/98`). No class spec exists and none was read as a prediction.

```
instrument: 2002-11-20
acknowledged: 2002-11-20
recorded: 2003-01-06
expires: UNKNOWN
```

⚠ **Instrument and acknowledgment coincide** — both 2002-11-20 — so I did not have to
discriminate and am not reporting a basis I chose (card 10).

⚠ **`expires: UNKNOWN` is again the wrong shape.** Nothing here expires; a satisfaction
has no term. `UNKNOWN` says *the document does not state it*, which reads as a hole in
the reading. Second document running. The `until` column was given `UNKNOWN(<reason>)`
for exactly this; the labelled block still has two states where three are needed.

⚠ **Six dates are on the face and four of them describe something other than this
instrument's chronology.** Beyond the three above: the **satisfied mortgage** is dated
**2000-12-15** and was recorded **2001-01-12**; the cover page carries a **Preparation
Date of 2002-12-20**. None has a slot. Two belong to another instrument entirely.

rd's parcel is **`1011321063`** and for the first time in this loop the document
states the same thing exactly — p1 *"MANHATTAN 1132 1063 Entire Lot 11A"*, p2
*"BLK: 1132 LOTS: 1063 UNIT: 11A"*. Lot 1063 is a condominium unit lot. No BBL was
composed.

## Events

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | p1 · [0.06,0.560,0.95,0.615] · plain · "MORTGAGER/BORROWER: ANTHONY J. LIPP" and "MORTGAGEE/LENDER: CHASE MANHATTAN MORTGAGE" | 2003-01-06 | recorded | | IDENTITY | ASSERT | 1011321063 | asserted by: the cover page  about: Anthony J. Lipp and Chase Manhattan Mortgage | 2 parties | `basis: recorded` because the act being dated **is** the filing — this panel exists to index the instrument and is completed by the presenter for the register (card 10). ⚠ **rd gives no roles at all**: its two parties carry `panel: "1"` and `panel: "2"` and nothing else. The document supplies what the index lacks, which is the reverse of the usual direction (card 9). ⚠ **Three Chase names appear and only two are linked.** The cover page names the mortgagee **CHASE MANHATTAN MORTGAGE**; p2 says the mortgage was made to **THE CHASE MANHATTAN BANK**; p2's return block says **Chase Manhattan Mortgage Corporation**. The f/k/a at E8 links JPMorgan Chase Bank to The Chase Manhattan Bank and says nothing about the third. ACRIS's own label reads "MORTGAGER", not mortgagor. | The cover page names Lipp as borrower and Chase Manhattan Mortgage as lender. |
| E2 | p1 · [0.06,0.393,0.95,0.460] · plain · "MANHATTAN 1132 1063 Entire Lot 11A 161 WEST 61 STREET" | 2003-01-06 | recorded | | IDENTITY | ASSERT | 1011321063 | asserted by: the cover page  about: block 1132 lot 1063 unit 11A | 1 condominium unit | Restated on the instrument itself, p2 · [0.10,0.248,0.80,0.290] · plain · "BLK: 1132 LOTS: 1063 UNIT: 11A" with "Address(es) of property: 161 WEST 61ST STREET 11A, NEW YORK, NY, 10023-0000." **Document and rd agree exactly, lot included** — the first time in this loop. ⚠ **"Entire Lot" and "Unit 11A" sit in the same row**: both are true, because on a condominium the unit *is* the whole tax lot, but a reader treating "Entire Lot" as "the whole building" would be wrong. There is no metes-and-bounds description anywhere and none is needed — a unit lot number is the description. | The parcel is condominium unit 11A, block 1132 lot 1063, 161 West 61 Street. |
| E3 | p1 · [0.06,0.393,0.95,0.460] · plain · "Property Type: DWELLING ONLY - 3 FAMILY" | 2003-01-06 | recorded | | OCCUPANCY | ASSERT | 1011321063 | asserted by: the cover page  about: block 1132 lot 1063 unit 11A | 3 families | Filed `OCCUPANCY` because the field states a residential use and a family count, which is that function's question; it bears on `AS_BUILT` as a statement about what stands. ⚠ **It is contradicted by its own page.** The same panel gives a unit-numbered condominium lot on the eleventh floor of a West 61st Street building; a three-family dwelling has no unit 11A. I record it because the cover page declares itself part of the instrument, and I flag it because a downstream consumer fanning use-class to this BBL would inherit a classification the document itself refutes. Card 9 — recorded, not corrected. Whether an ACRIS tax-class field should produce a row at all is a genuine judgement; a reader who drops it is not wrong. | The cover page classifies the property as a three-family dwelling. |
| E4 | p1 · [0.48,0.693,0.95,0.715] · plain · "Recording Fee: $ 42.00" | 2003-01-06 | recorded | | COST | ASSERT | 1011321063 | JPMorgan Chase Bank → Office of the City Register | 42.00 USD | The only money that actually moves on this document. Every other figure in the FEES AND TAXES panel p1 · [0.06,0.668,0.95,0.865] is `0.00` — Mortgage Amount, Taxable Mortgage Amount, Affidavit Fee, NYC Real Property Transfer Tax Filing Fee, NYS Real Estate Transfer Tax, and each of the six mortgage-tax lines (County Basic, City Additional, Spec Additional, TASF, MTA, NYCTA) together with their stated sum. `Exemption:` is **blank**, not zero. Those zeros are card 5's second state — the document asserts the amount is none — and are distinct from the blank. | A $42.00 recording fee was charged; every tax line is zero. |
| E5 | p2 · [0.10,0.162,0.92,0.240] · plain · "does hereby certify that the following Mortgage is paid" | 2002-11-20 | instrument | | CAPITAL | TERMINATE | 1011321063 | JPMorgan Chase Bank → Anthony J. Lipp | 366000.00 USD | The debt itself. "Mortgage dated December 15, 2000, made by Anthony J. Lipp to THE CHASE MANHATTAN BANK in the principal sum of $366,000.00 and recorded on January 12, 2001 in Volume/Book 3221 Page 495 in the Office of the County Clerk of New York County". Internal reference "Loan No. 000000001134005087". ⚠ **The date the debt was actually paid is not stated** — the certificate says it *is* paid as of its own date, so 2002-11-20 is the latest possible moment, not the event. ⚠ **`bbls` cannot hold what this row is really about.** The row terminates a specific prior instrument, and the schema has no field for an instrument pointer; see the findings section. | Chase certifies the $366,000 mortgage debt is paid. |
| E6 | p2 · [0.10,0.162,0.92,0.240] · plain · "does hereby consent that the same be discharged of record" | 2003-01-06 | recorded | | ENCUMBRANCE | TERMINATE | 1011321063 | JPMorgan Chase Bank → Anthony J. Lipp | UNKNOWN(a lien discharge has no quantity; the secured sum is at E5) | The lien, as distinct from the debt. **Deliberately dated differently from E5**, and the split is textual: the instrument uses two verbs — it *certifies* the mortgage **is paid** (done by 2002-11-20) and *consents* that it **be discharged of record**, which can only happen at the register. So the debt ends on the certificate date and the burden on the parcel ends on 2003-01-06. `basis: recorded` under card 10's exception — the act being dated is the filing. A reader who dates both at 2002-11-20 has taken the consent as self-executing; that is defensible and would show up as a one-cell disagreement rather than a reading dispute. Cross-reference to the discharged lien, cover page: p1 · [0.06,0.515,0.95,0.550] "MANHATTAN Year: 2001 Reel: 3221 Page: 495" — which the instrument calls **Volume/Book** 3221 Page 495. | The mortgage lien on unit 11A is discharged of record. |
| E7 | p2 · [0.10,0.225,0.60,0.240] · plain · "which Mortgage HAS NOT been assigned of record" | 2002-11-20 | instrument | | ENCUMBRANCE | ASSERT | 1011321063 | JPMorgan Chase Bank → Anthony J. Lipp | UNKNOWN(an absence, not a quantity) | Card 5's second state, and the strongest asserted absence I have seen in four documents — capitalised in the original. It is what gives the satisfying party standing: no intervening assignee holds this lien. Corroborated by an empty labelled field, p2 · [0.10,0.293,0.60,0.315] · plain · "List of Assignments:" with nothing under it. Bears on `IDENTITY`: the claim is that the chain of holders is unbroken from The Chase Manhattan Bank to JPMorgan Chase Bank. | Chase certifies the mortgage was never assigned to anyone else. |
| E8 | p2 · [0.10,0.438,0.60,0.500] · plain · "JPMORGAN CHASE BANK F/K/A THE CHASE MANHATTAN BANK" | 2002-11-20 | instrument | | IDENTITY | ASSERT | 1011321063 | asserted by: the instrument  about: JPMorgan Chase Bank and The Chase Manhattan Bank | 2 names, 1 entity | A corporate name change asserted on the face, and the load-bearing one: the mortgagee named in the mortgage was **THE CHASE MANHATTAN BANK**, and the party discharging it is **JPMORGAN CHASE BANK**. Without this line the satisfier is a stranger to the lien. This is `IDENTITY`'s core question — *is it the same as that* — answered explicitly rather than left to inference, which is the opposite of m1's three unlinked Wood Harmon names. It does **not** reach the third name, Chase Manhattan Mortgage Corporation, at E1. | JPMorgan Chase Bank states it is the former Chase Manhattan Bank. |
| E9 | p2 · [0.15,0.545,0.50,0.600] · plain · "Mark Ennis Vice President" | 2002-11-20 | instrument | | IDENTITY | ASSERT | 1011321063 | Mark Ennis → JPMorgan Chase Bank | 1 signatory | Capacity. Signed over a printed rule, with the JPMorgan Chase Bank corporate seal impressed at p2 · [0.76,0.565,0.92,0.650] — an **actual embossed seal in the image**, not m1's script notation "(Corp. Seal)". "Dated: November, 20, 2002" and "In the presence of:" appear above with **no witness subscribed**. | Mark Ennis signs as Vice President under the corporate seal. |
| E10 | p2 · [0.10,0.628,0.92,0.740] · plain · "On November, 20, 2002, before me, the undersigned, personally appeared Mark Ennis, Vice President personally known to me or proved to me on the basis of satisfactory evidence" | 2002-11-20 | acknowledgment | | IDENTITY | ASSERT | 1011321063 | Mark Ennis → Katherine D. Harris, Notary Public | 1 deponent | ⚠ **Taken out of state**: State of Louisiana, Parish/County of Ouachita, in the City of Monroe — for an instrument recorded in New York. The notary p2 · [0.40,0.740,0.92,0.815] is **Katherine D. Harris, Notary Public, "Lifetime Commission"**, sealed Ouachita Parish Louisiana. A commission with **no expiry date**, where m2's two notaries both carried one. Same date as the instrument, so instrument, execution and acknowledgment all coincide. The form's unresolved "he/she/they" and "individual(s)" boilerplate is never struck to fit the single male signatory. | Ennis acknowledges before a Louisiana notary on the same day he signs. |

**10 events.**

## Registry lane

`bbls: INSTRUMENT`. Not one of the eleven — these ask about the paper.

| # | citation | date | what it records |
| --- | --- | --- | --- |
| R1 | p1 · [0.48,0.795,0.95,0.860] · plain · "Recorded/Filed 01-06-2003 10:30 City Register File No.(CRFN): 2003000000003" | 2003-01-06 | The register's own act, under the City of New York seal and the City Register Official Signature. ⚠ **rd is more precise than the document**: rd reads `1/6/2003 10:30:58 AM`, the page reads `10:30`. The seconds exist only in the index. That is the reverse of every precision gap in this loop so far. |
| R2 | p1 · [0.06,0.272,0.95,0.345] · plain · "PRESENTER: JPMORGAN CHASE BANK 780 KANSAS LANE MONROE, LA 71203" and "RETURN TO: JPMORGAN CHASE BANK 780 KANSAS LANE MONROE, LA 71203" | 2003-01-06 | ⚠ **Two different return-to parties on one document.** The cover page returns to *JPMorgan Chase Bank*; the instrument p2 · [0.45,0.800,0.80,0.865] returns to *"Chase Manhattan Mortgage Corporation, Attn: Lien Release Dept., 780 Kansas Lane Suite A, P.O. Box 4025"*. Same street, different corporate name and a different mail stop. Also "Prepared by: Danielle D Robinson", a preparer named nowhere else. |
| R3 | p1 · [0.06,0.222,0.95,0.275] · plain · "Document Page Count: 1" with "RECORDING AND ENDORSEMENT COVER PAGE PAGE 1 OF 2" | 2003-01-06 | **Four page counts, all correct about different things** (card 8): the instrument is 1 page; the cover page is page 1 of 2; rd says `"pages": "2"`; `MANIFEST.json` says 2. Reconciled to none, and none used as a completeness test. |
| R4 | p1 · [0.06,0.222,0.95,0.275] · plain · "Document Date: 11-20-2002 Preparation Date: 12-20-2002" | 2002-12-20 | **A fifth kind of date**: when the cover page was prepared — one month after the instrument, seventeen days before filing. It dates neither the act nor the filing, and the labelled block has no slot for it. |
| R5 | p1 · [0.06,0.075,0.38,0.215] · plain · "The information on this page will control for indexing purposes in the event of any conflict with the rest of the document." | 2003-01-06 | ⚠ **The instrument declares which of its own pages wins a conflict.** See the findings section — no function asks this. |

## SEARCH RECORD

Crops are from the native scans — 2544 × 3347 (p1) and 2544 × 4200 (p2) — unresampled,
so these carry `native` rather than a dpi (card 1).

| region | dpi | found |
| --- | --- | --- |
| p2 · [0.10,0.293,0.60,0.500] | native | the space under "List of Assignments:" is **empty** — no assignment is listed, matching the asserted absence at E7 |
| p2 · [0.10,0.790,0.55,0.860] | native | "(this space for the recording stamp)" and **nothing in it** — the recording stamp went on the cover page instead |
| p2 · [0.10,0.240,0.92,0.300] | native | block, lot, unit and street address only — **no metes and bounds, no filed-map reference, no courses** anywhere on either page |
| p1 · [0.06,0.668,0.95,0.865] | native | the fee and tax panel in full — **no documentary stamp, no revenue stamp, no affidavit** |

**I found nothing** (card 5, state 1) for: any consideration recited for the
satisfaction itself; any covenant, restriction or reservation; any conveyance of an
estate; any government permit or application; any statement of what physically
exists other than the contested Property Type at E3.

## Things the eleven functions have no question for

**1 · A document declaring which of its own parts controls.** p1: *"This page is part
of the instrument. The City Register will rely on the information provided by you on
this page for purposes of indexing this instrument. The information on this page will
control for indexing purposes in the event of any conflict with the rest of the
document."* This is a **priority rule between two texts**, and it is operative — it
tells a reader that where the cover page and the instrument disagree, the cover page
wins for indexing. It bears directly on card 9, which instructs a reader to record
document-versus-index disagreement and correct neither; here the document itself
supplies a tie-break the card does not anticipate. Filed under the nearest function it
would become `IDENTITY`, which would lose the whole point: this is not a claim that two
things are the same, it is a rule about which of two conflicting statements governs.

**2 · An obligation whose object is a prior instrument, not a parcel.** Every one of
the eleven asks a question *about a parcel*. E5 and E6 are about **a specific recorded
mortgage** — Volume/Book 3221 Page 495 — and the parcel is only where that mortgage
sat. This is the second time I have reached this shape from a different direction: on
`RC_970273` a Lien Law §13 trust bound **a fund**, not land. **A function for
"instrument-directed acts" would cover satisfactions, assignments, subordinations,
modifications and consolidations** — the majority of what a registry actually holds.

## Index check — rd vs the document

| rd field | rd says | document says | verdict |
| --- | --- | --- | --- |
| `type` | `SATISFACTION OF MORTGAGE` | "Document Type: SATISFACTION OF MORTGAGE"; p2 titled "SATISFACTION OF MORTGAGE" | agrees |
| `doc_date` | `11/20/2002` | "Document Date: 11-20-2002"; "Dated: November, 20, 2002" | agrees |
| `crfn` | `2003000000003` | "City Register File No.(CRFN): 2003000000003" | agrees |
| `recorded` | `1/6/2003 10:30:58 AM` | "Recorded/Filed 01-06-2003 10:30" | agrees to the minute; **rd carries seconds the page does not** |
| `borough` | `MANHATTAN` | "MANHATTAN" | agrees |
| `amount` | `$0.00` | no consideration recited; the mortgage sum is $366,000.00 and the recording fee $42.00 | **NOT_CHECKABLE** — rd's `amount` has no counterpart on a satisfaction, and $0.00 is not the same as agreement |
| `parties` | `panel 1: LIPP, ANTHONY J` · `panel 2: CHASE MANHATTAN MORTGAGE` | "MORTGAGER/BORROWER: ANTHONY J. LIPP" · "MORTGAGEE/LENDER: CHASE MANHATTAN MORTGAGE" | names agree; **rd carries no role field at all — panel numbers only.** The document supplies the roles |
| `parcels[0].bbl` | `1011321063` | "1132 1063 ... 11A"; "BLK: 1132 LOTS: 1063 UNIT: 11A" | **agrees exactly, lot included** |
| `parcels[0].use` | `DWELLING ONLY - 3 FAMILY` | same string on the cover page | agrees with the page, and **both are contradicted by the unit-lot designation beside them** |
| `parcels[0].partial` | `ENTIRE LOT` | "Entire Lot" | agrees |
| `pages` | `2` | "Document Page Count: 1" / "PAGE 1 OF 2" | **disagrees, correctly** — different denominators (card 8) |

## Brief

JPMorgan Chase Bank, formerly The Chase Manhattan Bank, certified on 20 November 2002
that a $366,000 mortgage made by Anthony J. Lipp on 15 December 2000 and recorded on
12 January 2001 in Volume 3221 page 495 was paid, and consented that it be discharged
of record. Mark Ennis signed as Vice President under the bank's corporate seal and
acknowledged the same day before a Louisiana notary in Monroe, Ouachita Parish.

The property is condominium unit 11A at 161 West 61st Street, block 1132 lot 1063 —
the only document in this loop where the registry's BBL and the instrument's own
designation match down to the lot. There is no description beyond that, and none is
needed for a unit lot.

The debt and the lien end on different days. Chase certifies the mortgage *is paid* as
of the certificate date; it *consents that it be discharged of record*, and that can
only happen at the register, which it did at 10:30 on 6 January 2003 under CRFN
2003000000003. A $42.00 recording fee was charged and every tax line reads zero.

Two things on the face have no home in the eleven functions: the cover page's
declaration that it controls over the rest of the instrument in any conflict, and the
fact that this entire instrument is directed at another instrument rather than at the
land.
