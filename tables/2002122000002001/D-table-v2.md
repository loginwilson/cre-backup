# 2002122000002001 — event table (v2 schema)

Extractor D. Cross-class probe. **Satisfaction of Mortgage**, Manhattan, digital ACRIS,
2 pages: p1 is the Recording and Endorsement Cover Page, p2 is the instrument.

No spec applies and no coverage is scored. Both pages are `native` per `MANIFEST.json`
(2544 × 3347 and 2544 × 4200), so rects map directly and sensitivity is `native`.

## Dates

```
instrument: 2002-11-20
acknowledged: 2002-11-20
recorded: 2003-01-06
expires: UNKNOWN
```

⚠ **Card 10 case — three candidates coincide and I did not have to choose.** The
instrument is dated November 20, 2002, signed the same day, and acknowledged the same
day before a Louisiana notary. Saying `instrument` is not a discrimination I made.

⚠ **`expires: UNKNOWN` overstates my doubt again.** Nothing here creates a term that
ends — a satisfaction ends things, it does not start a clock. Same defect I reported on
m2: card 5 gave rows and search records three states of absence; the labelled date block
still has two.

**Four further dates are on the face and none has a slot:**

| date | what it is |
|---|---|
| 2002-12-20 | **Preparation Date** of the cover page — a month after the instrument was signed, and the value encoded in the Document ID `2002122000002001` |
| 2000-12-15 | the satisfied mortgage's own date |
| 2001-01-12 | the satisfied mortgage's recording date |
| 2003-01-06 10:30 | recorded/filed, with a **time**; rd carries `10:30:58 AM`, the page carries only `10:30` |

**rd** carries one parcel, `1011321063` — Manhattan, block `01132`, lot `1063`, unit
`11A`. Both pages state the same designation in their own words, so for the first time
in this loop rd and the document agree on the parcel without a placeholder.

---

## Events

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | p2 · [0.10,0.130,0.93,0.240] · plain · "does hereby certify that the following Mortgage is paid" | 2002-11-20 | instrument | | CAPITAL | TERMINATE | 1011321063 | JPMorgan Chase Bank f/k/a The Chase Manhattan Bank → Anthony J. Lipp | 366000.00 USD principal discharged | The **debt itself**, ended. "Mortgage dated December 15, 2000, made by Anthony J. Lipp to THE CHASE MANHATTAN BANK in the principal sum of $366,000.00". Lender's internal reference "Loan No. 000000001134005087". The deed states the original principal and **says nothing about the payoff figure, interest, or when payment was made** — "is paid" is the whole of it. | The lender certifies the 366,000 dollar mortgage debt is paid. |
| E2 | p2 · [0.10,0.130,0.93,0.240] · plain · "does hereby consent that the same be discharged of record" | 2002-11-20 | instrument | | ENCUMBRANCE | TERMINATE | 1011321063 | JPMorgan Chase Bank f/k/a The Chase Manhattan Bank → Anthony J. Lipp | 1 mortgage lien discharged | The **lien**, ended — a separate act from E1 and the framework's own CAPITAL/ENCUMBRANCE split, running in the opposite direction from the mortgage that created them. The lien is identified by its recording: "recorded on January 12, 2001 in Volume/Book 3221 Page 495 in the Office of the County Clerk of New York County". ⚠ The cover's cross-reference reads reel 3221 page 495 for **Manhattan year 2001**, and NYC mortgages are filed with the City Register, not the County Clerk — the instrument's printed boilerplate names the wrong office. | The lender consents that the lien be discharged of record. |
| E3 | p2 · [0.15,0.470,0.55,0.505] · plain · "JPMORGAN CHASE BANK F/K/A THE CHASE MANHATTAN BANK" | 2002-11-20 | instrument | | IDENTITY | ASSERT | 1011321063 | The Chase Manhattan Bank → JPMorgan Chase Bank | 1 entity, 2 names | An **express successor identity** — the party releasing is not the party named as mortgagee, and the instrument says why. ⚠ **The cover page and rd name the mortgagee `CHASE MANHATTAN MORTGAGE`, a third name the instrument never mentions and never links to either of the other two.** The p2 return address is "Chase Manhattan Mortgage Corporation". Three names, one stated link. Recorded, not reconciled. | The releasing bank states it was formerly The Chase Manhattan Bank. |
| E4 | p2 · [0.10,0.225,0.93,0.245] · plain · "which Mortgage HAS NOT been assigned of record" | 2002-11-20 | instrument | | IDENTITY | ASSERT | 1011321063 | asserted by: JPMorgan Chase Bank f/k/a The Chase Manhattan Bank  about: the mortgage recorded at reel 3221 page 495 | 0 assignments asserted | **Card 5 state 2 — the document asserts none**, and it is the load-bearing assertion of the whole instrument: it is what establishes that the releasing party still holds the lien. Corroborated by the printed "List of Assignments:" heading at p2 · [0.10,0.293,0.45,0.315] with **nothing under it** — but the blank is card 5 state 1 and the sentence is state 2, and only the sentence is evidence. Bears on ENCUMBRANCE (who holds the burden). | The lender asserts the mortgage was never assigned. |
| E5 | p2 · [0.15,0.545,0.50,0.595] · plain · "Mark Ennis / Vice President" | 2002-11-20 | execution | | IDENTITY | ASSERT | 1011321063 | asserted by: the instrument  about: Mark Ennis as Vice President of JPMorgan Chase Bank | 1 signatory | Signed under a JPMorgan Chase Bank corporate seal at p2 · [0.75,0.565,0.92,0.640]. Acknowledged the same day at p2 · [0.10,0.680,0.93,0.750] — "On November, 20, 2002, before me, the undersigned, personally appeared Mark Ennis, Vice President" — before Katherine D. Harris, Notary Public, **Ouachita Parish, Louisiana**, holding a "Lifetime Commission". ⚠ A New York lien is released by an officer appearing in Monroe, Louisiana; the venue reads "State of: Louisiana / Parish/County of: Ouachita". Execution and acknowledgment are one appearance on one date, so one row (card 2). | A vice president signs under seal and swears to it in Louisiana. |
| E6 | p1 · [0.07,0.400,0.94,0.465] · plain · "Property Type: DWELLING ONLY - 3 FAMILY" | 2002-12-20 | UNSUPPORTED | UNKNOWN(the cover states a property type as at preparation and says nothing about how long it holds) | AS_BUILT | ASSERT | 1011321063 | asserted by: the cover page  about: block 1132 lot 1063 unit 11A | UNKNOWN(a classification code, not a measurement — no storeys, area or unit count is stated) | ⚠ **`basis: UNSUPPORTED` records that the vocabulary failed, not that the document is silent.** The only date this claim carries is the cover's **Preparation Date, 12-20-2002**, and `basis` has no term for it. ⚠ The claim itself sits oddly with its own row: the same panel reads "Lot 1063 · Entire Lot · Unit 11A", and a 1000-series lot with a unit number is a condominium unit, not a three-family dwelling. I record both and correct neither (card 9). Bears on OCCUPANCY — I cannot tell whether "DWELLING ONLY" classifies what is built or restricts how it may be used (card 12). | The cover classifies the parcel as a three-family dwelling. |
| E7 | p1 · [0.07,0.678,0.49,0.870] · plain · "TOTAL: $ 0.00" | 2003-01-06 | recorded | | COST | ASSERT | 1011321063 | asserted by: the cover page  about: this instrument | 0.00 USD mortgage recording tax | An **asserted zero**, not a missing figure — card 5 state 2 in the money lane. Seven separate lines each read 0.00: County (Basic), City (Additional), Spec (Additional), TASF, MTA, NYCTA, and the sum. "Mortgage Amount" and "Taxable Mortgage Amount" also read 0.00 because this instrument creates no debt. ⚠ **rd propagates `amount: $0.00` from that field onto a document that discharges a 366,000 dollar mortgage** — anyone reading rd.amount as "the money in this document" is wrong by the full principal. | No mortgage recording tax is due on this satisfaction. |

**7 event rows.**

Function distribution: `IDENTITY` 3 · `CAPITAL` 1 · `ENCUMBRANCE` 1 · `AS_BUILT` 1 ·
`COST` 1. Modes: `ASSERT` 5 · `TERMINATE` 2.

**Did not fire:** `TITLE` (no estate moves), `ENTITLEMENT`, `ENVELOPE`, `OCCUPANCY`,
`PERMIT`, `VALUE` (nothing is bought, sold or valued — the only sums are a discharged
principal and a fee).

---

## Registry lane

| id | citation | date | function | bbls | what it records |
|---|---|---|---|---|---|
| R1 | p1 · [0.48,0.790,0.94,0.900] · plain · "RECORDED OR FILED IN THE OFFICE OF THE CITY REGISTER OF THE CITY OF NEW YORK / Recorded/Filed 01-06-2003 10:30" | 2003-01-06 | recording | INSTRUMENT | The register's own act, under the City seal and the City Register's signature. rd carries `1/6/2003 10:30:58 AM`; the page shows only `10:30`. The seconds are NOT_CHECKABLE — rd sole witness. |
| R2 | p1 · [0.48,0.790,0.94,0.900] · plain · "City Register File No.(CRFN): 2003000000003" | 2003-01-06 | file number | INSTRUMENT | The CRFN, matching rd exactly. It replaces liber and page entirely — **this instrument has no book, no page and no reel of its own**, only the reel/page of the mortgage it discharges. |
| R3 | p1 · [0.48,0.680,0.94,0.770] · plain · "Recording Fee: $ 42.00" | 2003-01-06 | fee | INSTRUMENT | The register's own charge. Affidavit Fee 0.00, NYC Real Property Transfer Tax Filing Fee 0.00, NYS Real Estate Transfer Tax 0.00. Kept in the lane because a recording fee genuinely is the registry's charge; the tax determination at E7 is not, and is an event. |
| R4 | p1 · [0.07,0.272,0.94,0.340] · plain · "PRESENTER: JPMORGAN CHASE BANK 780 KANSAS LANE MONROE, LA 71203" and "RETURN TO:" the same | 2003-01-06 | presenter and return-to | INSTRUMENT | ⚠ **Two different return-to parties.** The cover returns it to JPMorgan Chase Bank; p2 · [0.45,0.805,0.75,0.880] reads "Record and Return to: Chase Manhattan Mortgage Corporation, Attn: Lien Release Dept., 780 Kansas Lane Suite A, P.O. Box 4025, Monroe, LA 71203". Different entities, same street. Prepared by Danielle D Robinson. |
| R5 | p1 · [0.07,0.518,0.94,0.552] · plain · "CROSS REFERENCE DATA MANHATTAN Year: 2001 Reel: 3221 Page: 495" | 2003-01-06 | cross reference | INSTRUMENT | The registry's own link from this instrument to the mortgage it discharges — the machine-readable form of what E2 states in prose. A corpus pointer resolvable against the reel series. |
| R6 | p1 · [0.07,0.212,0.94,0.270] · plain · "Document Page Count: 1" and "PAGE 1 OF 2"; barcode "2002122000002001001EC926" | 2003-01-06 | page counts | INSTRUMENT | **Three counts on one face.** The cover declares the document is 1 page; the cover's own header says page 1 of 2; the package holds 2. Reported, reconciled none (card 8). |
| R7 | p1 · [0.07,0.095,0.37,0.200] · plain · "The information on this page will control for indexing purposes in the event of any conflict with the rest of the document." | 2003-01-06 | precedence rule | INSTRUMENT | ⚠ **The cover page declares itself authoritative over the instrument.** See the report — this is the sharpest thing in the document and card 9 has no room for it. |

---

## Does not fit any of the eleven

**A precedence rule about the record itself.** p1 · [0.07,0.095,0.37,0.200] · plain ·
*"This page is part of the instrument. The City Register will rely on the information
provided by you on this page for purposes of indexing this instrument. The information
on this page will control for indexing purposes in the event of any conflict with the
rest of the document."*

This is not a question about a parcel. It is a rule for resolving conflicts between two
parts of one document, and **it fires on this document**: the cover names the mortgagee
`CHASE MANHATTAN MORTGAGE` and the instrument names `THE CHASE MANHATTAN BANK` (E3).
Filing it under `IDENTITY` would lose that it governs, rather than states, an identity.

---

## SEARCH RECORD

Both pages are native scans, so sensitivity is `native`.

| region | dpi | found |
|---|---|---|
| p2 · [0.10,0.293,0.45,0.480] | native | The printed heading "List of Assignments:" with the whole block beneath it **empty** — no assignment listed |
| p2 · [0.10,0.450,0.45,0.470] | native | The printed "In the presence of:" line, **empty** — no subscribing witness |
| p2 · [0.11,0.800,0.40,0.830] | native | The printed legend "(this space for the recording stamp)" and the space beside it **empty** — the register stamped the cover page instead |
| p1 · [0.07,0.465,0.94,0.518] | native | Blank remainder of the PROPERTY DATA panel — one parcel only, no second BBL, no easement or partial-lot note beyond "Entire Lot" |
| p1 · [0.07,0.625,0.94,0.678] | native | Blank remainder of the PARTIES panel — two parties only, no trustee, servicer or additional panel |

**Not found anywhere on either page** (card 5 state 1): no payoff figure, no interest
rate, no date of payment; no legal description, metes and bounds, or filed-map
reference; no restriction, covenant or easement of any kind; no transfer of any estate.

---

## Index check — trust neither side, correct nothing

| rd field | rd says | document says | verdict |
|---|---|---|---|
| `type` | SATISFACTION OF MORTGAGE | "Document Type: SATISFACTION OF MORTGAGE"; p2 titled the same | agree |
| `doc_date` | 11/20/2002 | "Document Date: 11-20-2002"; p2 "Dated: November, 20, 2002" | agree |
| `recorded` | 1/6/2003 10:30:58 AM | "Recorded/Filed 01-06-2003 10:30" | agree to the minute; the seconds are rd alone |
| `crfn` | 2003000000003 | "City Register File No.(CRFN): 2003000000003" | agree |
| `borough` | MANHATTAN | "MANHATTAN" on the cover; p2 gives no borough, only "New York County" for the mortgage's recording | agree |
| `parcels[0].bbl` | 1011321063 | the instrument states lots 1063 in Block 1132, unit 11A | **agree — and this is the first document in this loop where the parcel needs no reconstruction.** No filed map, no placeholder lot |
| `parcels[0].address` | 161 WEST 61 STREET | p2: "161 WEST 61ST STREET 11A, NEW YORK, NY, 10023-0000" | agree; rd drops the unit, the ordinal and the zip. The zip's +4 reads `0000` — the same placeholder shape as a lot `0000` |
| `parcels[0].use` | DWELLING ONLY - 3 FAMILY | same, on the cover only | agree, because rd copied the cover. **p2 says nothing about use, so nothing independent confirms it** |
| `parties[0]` | LIPP, ANTHONY J (panel 1) | "MORTGAGER/BORROWER: ANTHONY J. LIPP"; p2 "made by Anthony J. Lipp" | agree. ⚠ rd carries **no role field** — `panel: 1` is a position, not a role |
| `parties[1]` | CHASE MANHATTAN MORTGAGE (panel 2) | cover: "MORTGAGEE/LENDER: CHASE MANHATTAN MORTGAGE"; **p2: mortgagee is "THE CHASE MANHATTAN BANK", releasing party is "JPMORGAN CHASE BANK F/K/A THE CHASE MANHATTAN BANK"** | **disagree.** Three names, and the instrument links only two of them. ⚠ **rd names neither party that signed this instrument** |
| `amount` | $0.00 | "Mortgage Amount: $ 0.00" on the cover; "the principal sum of $366,000.00" on p2 | **both true and answering different questions.** rd propagates the cover's zero |
| `pages` | 2 | cover says "Document Page Count: 1", header says "PAGE 1 OF 2" | three counts, not reconciled |
| — | no field | the satisfied mortgage's date and recording, the f/k/a link, the notary and venue, the recording fee | NOT_CHECKABLE |

---

## Brief

On 20 November 2002 JPMorgan Chase Bank, formerly The Chase Manhattan Bank, certified
that a mortgage made by Anthony J. Lipp in the principal sum of $366,000 was paid, and
consented that it be discharged of record.

The mortgage had been dated 15 December 2000 and recorded 12 January 2001 at reel 3221
page 495; the satisfaction states it had never been assigned, and the printed list of
assignments is empty.

Two things end here and they are separate: the debt, and the lien that secured it —
the same split the framework draws for a mortgage, running backwards.

The security was a condominium unit, block 1132 lot 1063 unit 11A, at 161 West 61st
Street, and for once the registry's BBL and the instrument's own designation agree
without reconstruction.

Mark Ennis signed as vice president under the bank's corporate seal and swore to it the
same day before a notary in Ouachita Parish, Louisiana — a New York lien released from
Monroe.

The cover page classifies the parcel as a three-family dwelling, which sits oddly
against a 1000-series lot carrying a unit number, and nothing on the instrument itself
supports or contradicts it.

No mortgage recording tax was due: seven tax lines each read zero, and the registry
took a $42 recording fee.

The City Register filed it on 6 January 2003 at 10:30 as CRFN 2003000000003 — no liber,
no page, no reel of its own.

The cover page also declares that where it conflicts with the rest of the document it
controls for indexing, and it does conflict: it names the mortgagee Chase Manhattan
Mortgage where the instrument names The Chase Manhattan Bank.

rd carries that cover-page name and a zero amount, so the registry row names neither
party that signed and states none of the money that moved.
