# Corrections for the DCP and LPC decoders

Paste the block for your source into that chat. Each one says what the decoder is
FOR in the parcel's life, what it got wrong (with the measurement), and what to
do instead.

---

## THE GRAND SCHEME — where every decoder sits

A parcel's life is one story told by several custodians. **No source holds the
whole thing, and each one answers a question the others structurally cannot.**

```
    WHAT MAY BE BUILT HERE?              ← DCP    (the rule for the whole area)
        ↓  a rezoning, a text amendment, a special permit
    WHAT MAY BE BUILT ON THIS LOT?       ← BSA    (relief for THIS lot only)
        ↓  a variance waives a rule that would otherwise bind
    WHO OWNS IT, WHO IS OWED, WHAT MOVED? ← ACRIS (title, debt, rights, burdens)
        ↓  deeds, mortgages, ZLDAs, easements, declarations
    WHAT IS ACTUALLY BEING BUILT?        ← DOB    (filings, permits, ZD1, CO)
        ↓  filing → permit → construction → TCO → CO
    WHAT DOES IT RENT AND SELL FOR?      ← StreetEasy / DOF (the unit economics)

    AND ACROSS ALL OF IT:
    WHAT MAY NOT BE TOUCHED?             ← LPC    (landmark constraint)
    WHO ARE THESE PEOPLE, REALLY?        ← DOS    (SPE → real party)
```

**DCP and LPC are the two that bound the envelope from OUTSIDE the property
line.** ACRIS tells you what an owner agreed to. DOB tells you what they filed.
**DCP and LPC tell you what the City permits and forbids regardless of what the
owner wants** — and neither is derivable from any other source.

---

## ▶ DCP — **HALT AND RESTART**

```
Halt and re-read RULE_DOCUMENTS_NOT_INDEXES.md before writing another fact.

WHY YOU EXIST
You answer the question that comes BEFORE every other decoder: what does the
City allow here at all? Every FAR in the app, every buildable-SF calculation,
every "as-of-right" number rests on a zoning district — and districts CHANGE.
When a rezoning lands, the envelope of every lot inside it moves at once,
without a single document being recorded against any of them. ACRIS will never
show it. DOB shows it only after someone files. You are the ONLY source for
"the rule changed", and you are also where CPC special permits and
authorizations live — relief granted by the Commission rather than by BSA.

Your facts date the moment a site became developable. Without you the timeline
says "in 2021 they filed for a 12-storey building" and cannot say why that
became possible.

WHAT WENT WRONG — measured, not asserted
  * 695 facts written. ZERO cite a page. Every one says page="project-record".
  * document_id values are ZAP PROJECT NUMBERS (2020K0276), not documents.
  * the "verbatim" is your own gloss, not document text:
        "Zoning Map Amendment — ULURP C220449ZMK (zoning map amendment — the
         district itself changes)"
    The parenthetical is a label you wrote. Verbatim means the words on the page.
  * you emitted `variance_granted` 391 times. A VARIANCE IS BSA'S INSTRUMENT
    (ZR §72-21). DCP does not grant variances. You are duplicating another
    decoder's output under the wrong name.

You harvested the index and wrote it to `facts`. That is the one thing the rule
forbids.

WHAT TO DO INSTEAD
1. Move everything you have to `sink.ledger()`. An index pull is REAL WORK — it
   tells us which documents exist and is the denominator for coverage — but it
   is a ledger row, never a fact. `sink.emit()` is for things read off a page.
2. Get the actual documents. Each ULURP action has real ones on nyc.gov:
       CPC Report                 the Commission's findings and the approved text
       Environmental (CEQR/EAS)   the development assumptions, often with SF
       Zoning text/map exhibits   what the district becomes, verbatim
   Start with the CPC Report — it carries the reasoning AND the conditions.
3. Use the right predicates. Add them to facts.PREDICATES deliberately:
       district_changed      from-district → to-district, with the effective date
       text_amended          the ZR section altered and how
       special_permit_granted  a CPC special permit (§74-xx), NOT a variance
       authorization_granted   a CPC authorization
       condition_imposed     a condition in the approved resolution
       mih_applied           an MIH area designated (this one moves FAR directly)
4. Date both axes: when the Commission approved, and when Council adopted.
   The envelope changes on adoption, not on approval.

COVERAGE
Report documents_read / documents_exist per ULURP action, always. A project
whose CPC Report is unread is a project whose envelope change is unknown — not
a project with no envelope change.
```

---

## ▶ LPC — **PAUSE AND FIX**

```
Pause. You ARE opening documents — real page numbers, real text — which puts
you ahead of DCP. Two things are wrong, and both are about classification
rather than access.

WHY YOU EXIST
You are the hard ceiling on the envelope. Every other source describes what
COULD be built; you describe what MAY NOT BE TOUCHED. A landmarked building
cannot be demolished, a facade cannot be altered, and rooftop additions must be
invisible from the street — none of which appears in FAR, in PLUTO, or in any
ACRIS instrument. A site with 71,000 unused square feet and a designated facade
is not a development site, and only you can say so.

You are also the constraint that BINDS THE FUTURE. A Certificate of
Appropriateness governs what the next owner may do, so your facts belong on the
parcel permanently, not just in the year they were issued.

WHAT WENT WRONG — measured
  1. YOU ARE TEMPLATING BY POSITION, NOT READING BY CONTENT.
     743 documents produced exactly TWO shapes: {permit 1, condition 1} for 384
     of them and {permit 2, condition 2} for 359. Pages cited are almost
     entirely 1 and 2. That is page 1 = "permit", page 2 = "condition", applied
     regardless of what those pages say.
     Compare BSA, which is reading properly: its pages range 1→11+, and one
     decision yielded 52 conditions while others yield three. THE VARIABILITY IS
     THE FINGERPRINT OF REAL READING. Uniformity is the fingerprint of a template.

  2. YOU ARE FILING FINDINGS AS CONDITIONS. These are opposite things:
       FINDING    the Commission's reasoning — why it approved
                  "that the historic stoop and entrance have been highly altered
                   and could not be restored to their historic configuration"
       CONDITION  what now binds the applicant — what they must or must not do
                  "that the window sash shall be painted to match the historic
                   colour and shall not be replaced without further approval"
     A finding explains. A condition CONSTRAINS. Only the second belongs on a
     parcel's envelope, and confusing them makes a landmark look more restricted
     than it is — which is the expensive direction to be wrong in.

WHAT TO DO INSTEAD
1. Read each CofA to the last page. Count the operative clauses; do not assume.
2. Classify by what the sentence DOES:
       permit_issued       the work approved (the scope)
       finding_recited     the Commission's reasoning  ← NEW predicate, add it
       condition_imposed   a binding obligation on the applicant
       work_prohibited     something explicitly not allowed
   A useful tell: findings are usually cast in the past or descriptive
   ("that the building was altered in 1963"); conditions are prospective and
   obligatory ("shall", "must", "shall not").
3. Capture the DESIGNATION separately from the permit. Whether a lot is an
   Individual Landmark, inside a Historic District, or merely calendared is a
   different and more durable fact than any single CofA, and it is what most
   often kills a development.
4. Re-run everything already decoded. All 743 documents were classified under
   the template, so they are all suspect — that is the backward re-check this
   project runs on: when a new failure is found, re-check every earlier entry,
   because prior work was judged by rules that predate the lesson.

COVERAGE
State pages_read / pages_total on every document, and expect the per-document
fact count to VARY. If your next 100 documents produce two shapes again,
something is still templating.
```
