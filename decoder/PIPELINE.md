# acquire → extract → crop → sweep

Login's loop, with the two open questions decided and the numbers that decide
them. Measured 2026-08-09.

```
INDEX          Socrata. free, unthrottled, complete for all 17M documents.
  |            decides WHAT to fetch before one image request is spent
MAP            DocumentImageView?doc_id=X  — one cheap HTML load, no images
  |            hid_TotalPages · hid_Sup · hid_Tax  =>  which pages are the
  |            instrument, which are supporting, whether an RP-5217 exists
ACQUIRE        GetImage?doc_id=X&page=N   ⚠ THE ONLY THROTTLED STEP
  |
EXTRACT        OCR -> text + BOUNDING BOXES        free, ~2s/page on 8 cores
  |            grep the slot menu against the text  free
  |            vision @100% on the strips grep found  ~41 tok each
CROP           the proof, cut from the OCR's own box
SWEEP          delete the page image. keep text + crops.
```

## Image vs text: both, and they do different jobs

Login got here independently and the measurements agree. They are not
alternatives; **they fail in opposite places**, which is exactly why the pair
works:

    OCR     LOCATE  0.94 on a deed grant page      finds the clause
            READ    0/1 on the same page           '($10.00)' -> '(S10.o0)'

Same page, same run. So:

    OCR IS A FILTER AND A CO-ORDINATE SYSTEM. IT IS NEVER A TRANSCRIBER.

⚠ **The bounding box is worth as much as the text.** `deed_agent.py` carries a
correction saying regions must come from *looking*, because guessing them was
wrong twice in one hour (the tax block guessed at y 0.30–0.60 when it is
0.62–0.97). OCR returns every region mechanically, and it does so **even when
its text is wrong** — you do not need it to read `$10.00`, only to say "there
is a money-shaped token here". Then vision reads that strip exactly.

⚠ **AND NO OCR STRING MAY EVER BECOME A CLAIM VALUE.** That is a structural
rule, not a quality bar. A garbled word in a filter costs a wasted look; a
garbled digit in a claim is silent and wrong forever.

⚠ **FILM IS THE EXCEPTION AND IT IS 35.8% OF ACRIS.** Microfilm scored recall
**0.00** at engine confidence **0.91** — confidently wrong. On film the OCR
text is not a weak filter, it is a hostile one, and the pipeline must skip
straight to vision. Detect by era and by ink density (film pages run ~0.20 ink
against ~0.06 for laser), never trust the engine's own confidence.

## Parcel or document type? — BOTH, at different steps

This reads like a fork and is not one. They are answers to different questions:

    ACQUIRE BY PARCEL          because a parcel is what CLOSES and what you
                               can hand a broker. A DEVR without its ZLDA and
                               its deed is an orphan — resolvers need the
                               parcel to settle anything, and the envelope
                               chain only reconciles across a whole lot.

    DISPATCH BY DOCUMENT TYPE  because competence lives in the form. 35
                               specialists, 136 slots, 44 traps — all per-type,
                               and all reusable across every parcel.

★ **The index being free is what dissolves the fork.** You do not choose a
strategy up front; you pull the parcel's whole document list for nothing, then
decide *per document* whether its pixels are worth a request.

## What that saves, on a real parcel

Brooklyn block 2414 lot 3 — the Domino site:

    48 documents · 1,944 pages · 16 types

    HIGH SIGNAL   5 ZONING LOT DESCRIPTION · 1 DEVELOPMENT RIGHTS · 2 DEED
                  1 CORRECTION DEED · 1 CONDO DECLARATION · 4 DECLARATION
    HOUSEKEEPING  10 SUNDRY MISCELLANEOUS · 6 UCC · 3 TERMINATION/AMENDMENT

⚠ **AND THE MAP CUTS IT AGAIN.** Every document's cover pages and supporting
pages are named by `hid_Sup` before anything is fetched, so only instrument
pages need requesting. On the deed that is pages 3–6 of 11.

⚠ **NEVER LET THIS BECOME A SILENT CAP.** "High signal" is a fetch ORDER, not a
decision that the rest says nothing. A UCC3 termination dates the discharge of
a lien and that is a real event. Anything deprioritised gets an explicit
`barren_reason` or stays on the queue — never dropped without a row saying so.

## Sweep: what is kept and what is lost

    ALWAYS KEEP   OCR text            ~2.8 KB/page   greppable forever
    ALWAYS KEEP   every proof crop    ~10 KB         a claim without one is
                                                     unfalsifiable
    KEEP THE TIFF only where the page bears a claim, or where OCR was
                  untrustworthy (film, low yield) — the only two cases where
                  re-reading pixels is ever needed
    ELSE SWEEP    a page that OCR'd cleanly and matched no slot vocabulary has
                  been read; the text is the record

    ~56 KB fetched  ->  ~7 KB retained   8x

⚠ **THE COST IS REAL AND IT IS A DECISION.** A swept page cannot be re-read at
higher resolution, ever, because the ledger will not re-fetch it. store.py
adopted "nothing is deleted" for a good reason — eight parser fixes in one
session left every earlier reading frozen. The two KEEP rules above exist
precisely so the pages where that would hurt are the pages that stay.

## Does it scale? — one bottleneck, and it is not extraction

    EFFICIENCY   8x on storage, and the index/map steps cost nothing
    TIME         OCR ~2s/page across 8 cores, fully parallel, free
                 ⚠ ACQUISITION IS THROTTLED AND IS THE ONLY REAL LIMIT
    ACCURACY     locate ~0.9 on laser · numbers from vision, never OCR
                 deeds self-check: RPTT ÷ 2.625% must equal RETT ÷ 0.400%
                 ⚠ film: no filter works. vision or nothing.

Every route tested today — direct endpoint, browser, cheaper reading, template
shortcuts — hit the same address-level throttle. Extraction is solved enough to
proceed. **Acquisition throughput is the whole game**, which is why
`acquire.py` backs off and ramps instead of walking into the wall at a constant
25 seconds.
