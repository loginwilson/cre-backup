# 2002122000002001 — table-v2 (Extractor B)

**SATISFACTION OF MORTGAGE**, Manhattan, ACRIS digital. Two pages of very
different kinds: **page 1 is the City Register's Recording and Endorsement Cover
Page**, machine-generated, which declares itself part of the instrument; **page 2
is the instrument**, one typed page prepared in Monroe, Louisiana.

No class spec applies and I read none. Framework and card only.

```
instrument: 2002-11-20
acknowledged: 2002-11-20
recorded: 2003-01-06
expires: UNKNOWN
```

**A fifth kind of date, with no slot:** `Preparation Date: 12-20-2002`, the day the
cover page was made — a month after the instrument and a fortnight before
recording. It is not instrument, not acknowledgment, not recording, not an expiry.
It carries E1 and E2, whose `basis` I had to write `UNSUPPORTED` for that reason.
**m1 produced a date with no slot too** (the 1907 map filing). Two documents, two
different unslotted dates, is a pattern rather than an instance quirk.

**Card 10 — candidates coincide.** The instrument date and the acknowledgment are
both 2002-11-20, so `instrument` here is not independently corroborated.

**rd** supplies: type `SATISFACTION OF MORTGAGE`, doc_date 11/20/2002, CRFN
`2003000000003`, recorded `1/6/2003 10:30:58 AM`, borough MANHATTAN, amount $0.00,
one parcel `1011321063` with `partial: ENTIRE LOT`, `use: DWELLING ONLY - 3
FAMILY`, address 161 WEST 61 STREET, unit 11A. Its two parties carry **`panel`
numbers, not roles** — rd does not say which is mortgagor and which mortgagee. The
cover page does. **Here the document is the richer source and rd the thinner one**,
which is the reverse of m1 and m2.

## Events

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | p1 · [0.07,0.395,0.94,0.525] · native · plain · "Borough MANHATTAN Block 1132 Lot 1063 Entire Lot Unit 11A 161 WEST 61 STREET / Property Type: DWELLING ONLY - 3 FAMILY" | 2002-12-20 | UNSUPPORTED | | AS_BUILT | ASSERT | 1011321063 | asserted by: the City Register cover page  about: block 1132 lot 1063 unit 11A | UNKNOWN(a classification code, not a measurement; no dimension, storey count or area is stated) | ⚠ **Internally inconsistent and I cannot tell which side is right (card 12).** Lot 1063 is a 1000-series lot and the record carries a unit designation, `11A`; a property type of "DWELLING ONLY - 3 FAMILY" does not sit with an eleventh-floor unit. Both readings are on the same line of the same page. A reader who treats an ACRIS classification code as indexing metadata rather than an assertion about the ground would emit no row here, and that is defensible. `basis UNSUPPORTED` because the cover page's own date is its Preparation Date and no basis term covers it | The record classifies the property as a 3-family dwelling, unit 11A of block 1132 lot 1063 |
| E2 | p1 · [0.07,0.555,0.94,0.675] · native · plain · "MORTGAGER/BORROWER: ANTHONY J. LIPP" and "MORTGAGEE/LENDER: CHASE MANHATTAN MORTGAGE" | 2002-12-20 | UNSUPPORTED | | IDENTITY | ASSERT | 1011321063 | asserted by: the City Register cover page  about: the parties to the satisfied mortgage | 2 parties | ⚠ **This conflicts with the instrument and the instrument is page 2 of the same document.** Page 2 says the mortgage was *"made by Anthony J. Lipp to THE CHASE MANHATTAN BANK"* — a bank. The cover page names *Chase Manhattan Mortgage* — which appears on page 2 only as the return-to addressee, *Chase Manhattan Mortgage Corporation*. A bank and a mortgage corporation are not stated to be the same entity and I do not merge them (card 4). **Card 9 says correct neither; the cover page says it controls.** See "Fits none of the eleven" | The cover page indexes the mortgagee as Chase Manhattan Mortgage, which page 2 contradicts |
| E3 | p2 · [0.11,0.160,0.91,0.240] · native · plain · "does hereby certify that the following Mortgage is paid ... Mortgage dated December 15, 2000, made by Anthony J. Lipp to THE CHASE MANHATTAN BANK in the principal sum of $366,000.00" | 2002-11-20 | instrument | | CAPITAL | TERMINATE | 1011321063 | JPMorgan Chase Bank → Anthony J. Lipp | $366,000.00 principal | The **debt** is certified paid, as distinct from the lien at E4 — the framework's CAPITAL-vs-ENCUMBRANCE boundary, run in reverse. The sum is the original principal, not the amount actually paid off; the instrument states no payoff figure and none can be had from it (card 4). The mortgage is dated 2000-12-15 and was recorded 2001-01-12 — **two further dates that belong to a different instrument and have no slot here** | JPMorgan Chase Bank certifies the $366,000 mortgage debt is paid |
| E4 | p2 · [0.11,0.160,0.91,0.240] · native · plain · "does hereby consent that the same be discharged of record ... recorded on January 12, 2001 in Volume/Book 3221 Page 495 in the Office of the County Clerk of New York County, New York" | 2002-11-20 | instrument | | ENCUMBRANCE | TERMINATE | 1011321063 | JPMorgan Chase Bank → Anthony J. Lipp | 1 mortgage lien | The **lien** is discharged. Target identified only by a pointer to another instrument: reel 3221, page 495, and the cover page cross-reference at p1 · [0.07,0.515,0.94,0.560] reads *"MANHATTAN Year: 2001 Reel: 3221 Page: 495"*. ⚠ **No column carries that pointer** — see "Fits none of the eleven". Incidental: the instrument says *County Clerk of New York County*, but Manhattan mortgages in 2001 were recorded with the City Register; the cover page calls the same location a **Reel** where page 2 calls it a **Volume/Book** | The mortgage lien recorded at reel 3221 page 495 is discharged of record |
| E5 | p2 · [0.11,0.160,0.91,0.240] · native · plain · "which Mortgage HAS NOT been assigned of record" | 2002-11-20 | instrument | | ENCUMBRANCE | ASSERT | 1011321063 | asserted by: JPMorgan Chase Bank  about: the mortgage at reel 3221 page 495 | 0 assignments | Card 5 second state — a real asserted absence, and the reason it matters is standing: an unassigned mortgage can be discharged by the original mortgagee's successor. Corroborated by an empty enumeration: p2 · [0.11,0.292,0.40,0.320] · native · plain · *"List of Assignments:"* with nothing beneath it through to the date line | The mortgage was never assigned of record |
| E6 | p2 · [0.11,0.430,0.60,0.510] · native · plain · "JPMORGAN CHASE BANK / F/K/A THE CHASE MANHATTAN BANK" | 2002-11-20 | instrument | | IDENTITY | ASSERT | 1011321063 | asserted by: JPMorgan Chase Bank  about: The Chase Manhattan Bank | 1 prior name | A stated name equivalence — IDENTITY's core trigger, and the load-bearing one here: it is what connects the party discharging the lien to the party that took it in 2000. Without this line the satisfier is a stranger to the mortgage. It does **not** reach Chase Manhattan Mortgage Corporation, which is a third name on this document | JPMorgan Chase Bank states it was formerly The Chase Manhattan Bank |
| E7 | p2 · [0.15,0.540,0.92,0.650] · native · plain · "Mark Ennis / Vice President" over the printed signature line, with the JPMorgan Chase Bank corporate seal impressed at right | 2002-11-20 | instrument | | IDENTITY | ASSERT | 1011321063 | JPMorgan Chase Bank, by Mark Ennis (Vice President) → Anthony J. Lipp | 1 signatory; 1 corporate seal | The instrument dates itself *"Dated: November, 20, 2002"* and the printed *"In the presence of:"* line is blank — no subscribing witness. The seal legend reads JPMORGAN CHASE BANK / CORPORATE SEAL / NEW YORK | Mark Ennis, a Vice President, executes for JPMorgan Chase Bank under its corporate seal |
| E8 | p2 · [0.11,0.625,0.91,0.755] · native · plain · "State of: Louisiana / Parish/County of: Ouachita" and "On November, 20, 2002, before me, the undersigned, personally appeared Mark Ennis, Vice President ... and that such individual(s) made such appearance before the undersigned in the City of Monroe, State of Louisiana" | 2002-11-20 | acknowledgment | | IDENTITY | ASSERT | 1011321063 | Mark Ennis → Katherine D. Harris, Notary Public | 1 deponent | ⚠ **Acknowledged out of state** — a Louisiana notary in Ouachita Parish for a Manhattan parcel, on the same day the instrument is dated. Katherine D. Harris, Notary Public, **"Lifetime Commission"** — no expiry date, where m1's and m2's notaries all carried one. The form is the modern all-purpose wording, *"he/she/they"* and *"individual(s)"*, none of it resolved to this signatory | Mark Ennis acknowledged the satisfaction in Ouachita Parish, Louisiana, on 20 November 2002 |

## Registry lane

Not one of the eleven — it asks about the instrument, not a parcel. `bbls: INSTRUMENT`.

| # | citation | date | basis | until | function | mode | bbls | parties | quantity | terms | summary |
|---|---|---|---|---|---|---|---|---|---|---|---|
| E9 | p1 · [0.07,0.670,0.94,0.870] · native · plain · "Recording Fee: $ 42.00" | 2003-01-06 | recorded | | COST | ASSERT | INSTRUMENT | Anthony J. Lipp or JPMorgan Chase Bank → City Register of the City of New York | $42.00 | ⚠ **The first labelled, legible fee in three documents.** m1 and m2 both produced only search negatives here. Who paid is not stated — the presenter is JPMorgan Chase Bank, but the instrument does not say who bore the cost, and card 4 forbids reading the presenter as the payer. Affidavit Fee, NYC Real Property Transfer Tax Filing Fee and NYS Real Estate Transfer Tax are each stated as $0.00 | The City Register charged a recording fee of $42.00 |
| E10 | p1 · [0.50,0.790,0.94,0.920] · native · plain · "RECORDED OR FILED IN THE OFFICE OF THE CITY REGISTER OF THE CITY OF NEW YORK Recorded/Filed 01-06-2003 10:30 City Register File No.(CRFN): 2003000000003" | 2003-01-06 | recorded | | IDENTITY | ASSERT | INSTRUMENT | asserted by: the City Register  about: this instrument | 1 recording, at 10:30 | Signed *"City Register Official Signature"* over the seal of the City of New York, 1625. ⚠ **rd carries `1/6/2003 10:30:58 AM` — to the second — where the document states only the minute.** Card 9: both stand, corrected neither; the index is the more precise witness here. `function` is forced — none of the eleven asks about filing, so IDENTITY is the least-wrong shelf, as on m1 and m2 | The City Register recorded the satisfaction at 10:30 on 6 January 2003 as CRFN 2003000000003 |
| E11 | p1 · [0.07,0.272,0.94,0.400] · native · plain · "RETURN TO: JPMORGAN CHASE BANK 780 KANSAS LANE MONROE, LA 71203" and p2 · [0.11,0.810,0.72,0.895] · native · plain · "Record and Return to: Chase Manhattan Mortgage Corporation Attn: Lien Release Dept. 780 Kansas Lane Suite A P.O. Box 4025 Monroe, LA 71203" | 2003-01-06 | recorded | | IDENTITY | ASSERT | INSTRUMENT | asserted by: this instrument  about: the return-to addressees | 2 return-to parties | ⚠ **Two return-to parties, two different corporate names, one street address.** The registry lane as framed assumes one. The cover page also names JPMorgan Chase Bank as PRESENTER at the same address, and page 2 names *"Prepared by: Danielle D Robinson"* — a fourth actor on the bank side, appearing nowhere in rd | The recorded satisfaction is returned to two differently-named Chase entities at one Monroe, Louisiana address |

The six tax lines — County (Basic), City (Additional), Spec (Additional), TASF, MTA, NYCTA — are each stated as $0.00 and their stated TOTAL is $0.00, so the document checks itself.

## SEARCH RECORD

Negatives are not rows (card 1). Where I looked, and how closely.

| region | dpi | found |
|---|---|---|
| p2 · [0.11,0.292,0.40,0.320] | native | the printed heading "List of Assignments:" and **nothing beneath it** through to the date line |
| p2 · [0.11,0.240,0.91,0.440] | native | blank but for the address and assignment headings — **no covenant, no reservation, no condition attached to the discharge, no reference to any other lien** |
| p2 · [0.11,0.810,0.72,0.895] | native | the printed "(this space for the recording stamp)" carries **no stamp** — the ACRIS cover page holds the endorsement instead; and the "Prepared by / Record and Return to" block |
| p1 · [0.07,0.670,0.94,0.870] | native | the fee and tax table; **no documentary stamp, no transfer tax, no mortgage tax** — every line but the recording fee reads $0.00 |
| p1 · [0.07,0.395,0.94,0.560] | native | one parcel only, qualified "Entire Lot"; **no second parcel and no partial-lot description** |
| p1 · [0.07,0.900,0.94,1.000] and p2 · [0.11,0.895,0.91,1.000] | native | page feet; the form code "NY00 12/98" on p2, nothing else |

**TITLE, ENTITLEMENT, ENVELOPE, OCCUPANCY, PERMIT, VALUE: I found nothing** —
card 5 state 1. No estate moves, no development right, no building or use
restriction, no government authorisation, and **no consideration is recited for
the satisfaction itself.** The $366,000.00 is the debt discharged, not a price.

## Fits none of the eleven

- **The cover page's own priority clause.** p1 · [0.07,0.070,0.38,0.220] · native ·
  plain · *"This page is part of the instrument. The City Register will rely on the
  information provided by you on this page for purposes of indexing this
  instrument. The information on this page will control for indexing purposes in
  the event of any conflict with the rest of the document."* This is a rule about
  **which part of the instrument governs when its two parts disagree** — and they
  do disagree here, at E2, on who the mortgagee was. It is not a claim about a
  parcel, a party, or the registry's act. Filing it under IDENTITY would say the
  document asserts something about who someone is; it does not. **m2 carried an
  interpretive clause with no home too** (*"The word 'party' shall be construed as
  if it read 'parties'"*). Second in a row.
- **A pointer to the instrument this one operates on.** A satisfaction's entire
  content is *"the mortgage at reel 3221 page 495 is discharged."* `bbls` fans the
  event to a parcel; **nothing links this `TERMINATE` to the `CREATE` it
  terminates.** The checker's REF line reports the pointer as a note, and no column
  carries it, so Reorganize sees a lien ending on a parcel with no way to know
  which lien. **Candidate field: `affects_instrument`.** This is the sharpest gap
  this document exposes, because it is the whole point of the instrument.

## Brief

On 20 November 2002 JPMorgan Chase Bank, of 780 Kansas Lane, Monroe, Louisiana,
certified that a mortgage of $366,000 made by Anthony J. Lipp on 15 December 2000
was paid, and consented to its discharge of record. The mortgage had been recorded
on 12 January 2001 at reel 3221, page 495, and had never been assigned. The bank
identified itself as formerly The Chase Manhattan Bank, which is the only thing
tying the party signing the discharge to the party that took the lien.

Mark Ennis, a Vice President, signed under the bank's corporate seal and
acknowledged it the same day before Katherine D. Harris, a notary of Ouachita
Parish, Louisiana, holding a lifetime commission. The property is unit 11A at 161
West 61st Street, Manhattan, block 1132 lot 1063, taken as an entire lot.

The City Register recorded the satisfaction at 10:30 on 6 January 2003 as CRFN
2003000000003 and charged a recording fee of $42.00; every tax line reads zero. It
was returned to Monroe, Louisiana — to JPMorgan Chase Bank per the cover page, and
to Chase Manhattan Mortgage Corporation per the instrument.

Two things in the record disagree with each other. The cover page indexes the
mortgagee as Chase Manhattan Mortgage, while page 2 says the mortgage ran to The
Chase Manhattan Bank; and the property is typed as a three-family dwelling while
also carrying a condominium unit number. The cover page states that it controls in
a conflict, which is a rule this table has no field for.
