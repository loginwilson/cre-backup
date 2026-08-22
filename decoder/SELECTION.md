# Selection — what to acquire, and how it generalises past ACRIS

## Selection is the pipeline read backwards

    FORWARD   (execution)
      acquisition -> extraction -> IDENTIFY -> resolution -> derivation -> application

    BACKWARD  (selection)
      application -> derivation -> resolution -> QUESTIONS -> claims -> document
      types -> acquisition

A product asks something. The deriver names the output it needs. That output
needs a resolved function. **The function poses questions.** Each question needs
a claim. Each claim lives in some document type. Those document types are the
acquisition list.

That is the whole method, and it is the only thing that stops acquisition being
"fetch everything and hope".

---

## ⚠ THE BACKWARD CHAIN RUNS AT DESIGN TIME. NEVER AT RUNTIME.

This is the distinction that decides whether the corpus is reusable.

    DESIGN TIME   "which document TYPES can answer ENVELOPE's questions?"
                  A fact about the world. Stable. Computed once per function,
                  reused by every product forever.

    RUN TIME      "which documents does THIS card need for THIS parcel?"
                  ⚠ IF ACQUISITION IS DRIVEN THIS WAY THE CORPUS BECOMES
                  PRODUCT-SHAPED and the next product cannot reuse it.

Login's own diagnosis — *"I tried to start with application through direct
extraction into the application and this was wrong"* — is exactly this failure.
Going product-first means every extraction gets shaped by what one card wanted
that week.

So: the backward chain produces a **static map** of function -> question ->
document type. Acquisition then runs forward against that map, at whatever
depth and over whatever parcels the budget allows. The resolver still never
learns who is asking.

---

## The five levels are SOURCE-AGNOSTIC. Only two layers change.

    acquisition   ⚠ DIFFERENT PER SOURCE — this is where all the variation is
    extraction    ⚠ DIFFERENT PER SOURCE — and per form within a source
    IDENTIFY      one implementation, every source. keys to the parcel bank.
    resolution    one per function, reads CLAIMS — never knows the source
    derivation    one per output
    application   one per product

★ **That is why the claim table is the contract.** A DOB permit claim and an
ACRIS deed claim are the same shape, so ENCUMBER does not care which arrived.
Adding a source means writing an acquirer and an extractor — nothing above
changes.

## ⚠ AND ACRIS IS THE ONLY HARD ONE

    SOURCE          acquisition            extraction
    ACRIS images    throttled, ~10/burst   ⚠ OCR + vision. THE HARD CASE.
    ACRIS index     free, unthrottled      none — rows are already claims
    DOB NOW / BIS   free API               none — rows are already claims
    DOF sales/DTM   free API + geometry    none
    HPD             free API               none
    Zoning Res.     fetchable live text    light — prose, but text not pixels
    listing svcs    ⚠ bot-detected         HTML parse

**Everything except ACRIS document images is already structured.** ~11.6M rows
across DOB/DOF/HPD arrive as claims with no reading at all. The OCR problem,
the resolution ladder, the proof crop, the 8x storage question — every one of
them is ACRIS-image-specific.

⚠ **So do not generalise ACRIS's difficulty to the other sources, and do not
generalise their ease to ACRIS.** The correct expectation is that adding DOB or
HPD is a week of work each, and ACRIS is the multi-month problem — which is
the opposite of how effort has been split so far.

---

## What a selection row looks like

Built per function, once, and it is the acquisition plan:

    FUNCTION   ENVELOPE
    QUESTION   how much floor area may be built here?
    NEEDS      zoning district · lot area · rights transferred in/out ·
               existing floor area · applicable special district
    ANSWERED BY
      zoning district      DCP nyzd + ZR feed        free, structured
      lot area             DOF Digital Tax Map       free, structured
      existing floor area  PLUTO + DOB CO            free, structured
      rights in/out        ⚠ ACRIS DEVR·ZONE·AGMT·EASE·MTGE·AL&R
                                                     THROTTLED IMAGES
    ⚠ MEASURED CONTRIBUTION (lot 49, 99 air-rights claims):
        DEVR 21% · AGMT 13% · SAGE 13% · MTGE 12% · EASE 11% · AL&R 8% ·
        SMIS 8% · CERT 5% · ASST 3% · DEED 2% · ZONE 2%

★ **The measurement is what makes the row honest.** The naive selection for
ENVELOPE is "acquire the DEVRs". That captures **21%**. The other 79% is spread
across types with millions of documents citywide — including mortgages, because
a mortgage describes its collateral.

⚠ **WHICH FORCES A CHOICE, AND IT MUST BE MADE EXPLICITLY PER FUNCTION:**

    COMPLETE TYPE, CITYWIDE     works only for small types.
                                DEVR 1,201 · AIRRIGHT 64 · MERG 81
                                -> a citywide product, partial per parcel

    COMPLETE PARCEL, WATCHLIST  works at any type size.
                                -> a complete product, on few parcels

Those answer different questions and neither is wrong. What is wrong is doing
one and reporting the other — claiming the DEVR sweep is "the air-rights
record" when it is a fifth of it.
