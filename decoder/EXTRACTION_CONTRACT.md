# Extraction Contract — what a decode must return

One fixed JSON per document, whatever the type. Every value carries a page.
Fields marked **required** must be present or explicitly null with a reason.
Nothing here is optional styling: the reducer, the validators and the audit all
read these fields by name, and a field stored as prose instead of structure is
a field no check can use.

## Governing rules

1. **Never guess.** Absent → `null` plus a note. Illegible → an anomaly, never a
   silent skip. "Blocked" and "empty" are different findings.
2. **Never repair a number to make a check pass.** Report the failure.
3. **Provenance on every value**: page, and enough of the clause that a human
   confirms it in ten seconds. A bare page number is not provenance.
4. **The document beats the index.** Contradictions go in `anomalies`.
5. **Classify before extracting** on catch-all codes (AGMT/SAGE/SMIS/DECL/MISC):
   what the instrument *does* governs, not what it is called.

## Required blocks

```jsonc
{
  "doc_id": "...",
  "instrument_title": {"value": "...", "page": 3},   // as printed inside
  "instrument_kind": "...",                          // decoded, not the index code
  "summary_what_it_does": "one sentence, plain language",

  "parties": [{"name", "label_in_doc", "normalized_role", "tax_lot", "page"}],
  // normalized_role: grantor_of_rights | recipient_of_rights |
  // other_zoning_lot_member | consenting_mortgagee | declarant | other

  "zoning_lot_roster": [{"bbl": "1014460001", "page": 24}],
  // every lot the DOCUMENT says composes the zoning lot — this is the roster,
  // and it routinely exceeds the index legals. Prefer "bbl"; {borough,block,lot}
  // is accepted. A lot bound by the instrument but deliberately NOT indexed
  // against it (see the MTA/lot-51 case) belongs here and nowhere else.

  "transfers": [{                                    // REQUIRED for ENVELOPE types
    "group": "g1",
    "quantity_sf": 6554,          // null when the document never states it
    "amount_usd": 1650000,        // null when only the index/taxes imply it
    "basis": "chart|definition|recital|operative_clause|derived",
    "from_lots": [{"bbl": "...", "per_lot_sf": 6554}],   // per_lot_sf null when
    "to_lots":   [{"bbl": "...", "per_lot_sf": null}],   // no split is stated
    "page": 7,
    "provenance": "§1.17 p7: (1,021.8 x 10 FAR) - 3,664 = 6,554"
  }],
  // The reducer turns this into balanced double-entry postings. NEVER invent a
  // split: a collective side gets per_lot_sf null on every member and the group
  // total on the group. Every participating lot must appear, never a lead lot
  // alone — a lot omitted here is invisible to the parcel timeline.

  "lot_areas_by_bbl": {                              // REQUIRED where stated
    "values": {"1014460151": 1021.8},
    "extent": {"3024720075": "partial"},   // "p/o Lot 75" — compare doc <= map
    "provenance": "§1.17 footnote p7"
  },

  "legal_descriptions": [{                           // REQUIRED — see below
    "exhibit": "A", "bbl": "1014460151",
    "shape": "per_lot",            // REQUIRED: per_lot | perimeter | vertical |
                                   // incorporation_by_reference — see below
    "courses_verbatim": "BEGINNING at a point on the easterly side of Second "
      "Avenue distant 54 feet 5 inches southerly from ...; thence easterly "
      "through a party wall 16 feet 3 inches; thence northerly 6 inches; ...",
    "stated_area_sf": null,        // only if the document states one
    "covers_bbls": null,           // perimeter only: every lot inside the bound
    "incorporates_by_reference": null,   // e.g. "ZLDA Exhibit A"
    "description_verbatim": null,  // used INSTEAD of courses when there are none
    "vertical_extent": null,       // {position: above|below, plane_ft, datum,
                                   //  datum_defined_here: bool}
    "page": 36
  }],

  "notices": [{                                      // REQUIRED where present
    "serves_party": "Owner",       // the label the document uses
    "role": "party | counsel | attention_individual",
    "name": "Bayard House, LLC",
    "attention": "Mr. Witold Brend",   // the HUMAN behind an entity
    "address": "62 Bayard Street, Brooklyn, New York 11222",
    "phone": "(718) 302-2004", "fax": "(718) 302-2005", "email": null,
    "page": 17
  }],
  // The Notices section is the richest contact source in ACRIS and every decode
  // before 2026-08-05 read past it. It gives what no index can: a NAMED HUMAN
  // behind an SPE, with a phone, from 2004 onward. It also states entity linkage
  // rather than implying it — Bayard House LLC and Sabin Enterprises Inc appear
  // with the SAME address and the SAME attention-party in one block, which is a
  // fact, not the address-matching inference that belongs in enrichment.

  "certifications": [{                               // REQUIRED where present
    "kind": "architect | surveyor | engineer | other",
    "name": "John H. Rodenbeck",
    "credentials": "AIA, NCARB, LEED AP, EDAC",
    "licence_number": "037995-1",   // joins to DOB's licence register
    "firm": null, "certifies": "floor area computation",
    "date": null, "page": 19
  }],
  // A sealed certification names the professional who stood behind a number.
  // DOF's own Auth_for_Change does the same for surveyors ("Survey by: Earl B.
  // Lovell- S.P. Belcher Inc, Survey Date: 11/30/2012"), so the two sources
  // corroborate each other.

  "acknowledgments": [{                              // REQUIRED where present
    "signatory": "David Mathew Owens",
    "also_known_as": "David M. Owens",   // "a/k/a" written into the jurat
    "for_entity": null,                  // the entity they signed for, if stated
    "date": "2014-09-09", "county": "NY",
    "notary": "Donna S. Weisman", "notary_number": "01WE6025982",
    "notary_county": "Queens", "commission_expires": "2015-06-07",
    "executed": true,                    // false = the block is BLANK
    "page": 20
  }],
  // Three reasons this is its own block and not a footnote:
  //   * it names the HUMAN who signed for an entity — often the only place the
  //     principal behind an SPE appears at all
  //   * an "a/k/a" in the jurat is a name variant stated by the document, which
  //     is exactly what entity resolution must not have to guess
  //   * a BLANK acknowledgment block is a DEFECT in the recorded original.
  //     `executed: false` records it; it is never treated as absent-and-fine.
  // Notices, certifications and acknowledgments are three views of one question
  // — who touched this document, in what capacity — and they are kept separate
  // because the capacity is the point, not incidental.

  "consideration": {
    "in_document": null,           // most instruments recite only $10
    "index_amt": 1650000,
    "recovered": null,             // e.g. from prepaid tax-return references
    "recovery_method": "cover RPTT 43,312.50 / 2.625% = 1,650,000 exactly",
    "zero_verified": null,         // REQUIRED when the amount is $0/absent:
    // how the prepaid-tax trap was ruled out, with the cover page re-read
    "per_sf": 251.75
  },

  "cross_instruments": [{"what", "how_cited", "identifier", "page"}],
  // how_cited: crfn | doc_id | reel_page | date_parties | unresolved
  // "what" is mandatory — a citation is WHAT is cited plus HOW it is identified,
  // and storing only the identifier makes reference-less citations unresolvable.

  "consents_waivers": [{"party", "instrument", "present_in_doc", "page"}],
  // expected-but-absent is a finding: record it with present_in_doc false

  "form_and_use_effects": [{"kind", "detail", "page"}],
  // kind: form_restriction (height/light-air planes with elevation AND datum,
  // coverage caps, FAR floors) | use_restriction (with expiry) | obligation

  "effective_dates": {"document_date", "recorded", "crfn"},
  "anomalies": [...],
  "self_checks": [{"check", "arithmetic", "result"}],
  "decode_status": "validated | validated_with_findings | failed_validation | unparseable",
  "validation_tier": "arithmetic | external | structural | unverified"
}
```

## Legal descriptions: transcribe the courses, do not summarize

**This is the change that matters most.** Earlier decodes recorded "25 x 100" or
"irregular, 6 courses". That is a paraphrase of the one thing in the instrument
that is *legally operative*: a deed conveys the land **described**, not a tax lot
number. Tax lots are DOF's administrative overlay; the survey is the parcel.

Requirements:

- `courses_verbatim` reproduces the description **as printed**, from BEGINNING to
  the point of beginning, with every "thence" clause, every distance in its own
  units ("16 feet 3 inches", "8 feet 9-1/2 inches", 104.96), and every bearing
  (`N 76°19'05" E`) exactly as written.
- Do not normalize, round, reorder, or fix apparent typos. A description that
  reads "28th feet" is transcribed as "28th feet" and flagged in `anomalies`.
- Keep the tie line ("distant 54 feet 5 inches southerly from the corner") — the
  parser needs it to know it is *not* a boundary course.
- Curves are transcribed in full (`radius 2,335.00 feet, arc 128.46 feet`); the
  traverse engine reports them as unhandled rather than approximating a chord.
- If a description is illegible or truncated in the recorded original, say so in
  `anomalies` and set `courses_verbatim` to null. Never reconstruct it.

Why it is worth the transcription cost: `metes.py` walks the courses, computes
the area, and reports the **closure error**. That yields an area independent of
PLUTO, valid for any era including pre-2002 where no parcel file reaches, and it
catches defects the tax map cannot — this pilot found an 18'11" gap between
abutting parcels, a non-closing lot with two variant course sets, and a
description whose duplicated course makes it unparseable.

## Four description SHAPES — and two of them are opposite errors

`shape` is required because the shapes disagree about whether areas add up, and
getting it wrong is silent:

| shape | what it describes | area behaviour |
|---|---|---|
| `per_lot` | one tax lot | its own area |
| `perimeter` | a single bound around SEVERAL lots | **additive** — the area is the sum of the constituents, so it must never be posted against one BBL |
| `vertical` | above or below a limiting plane | **NOT additive** — the footprint is the *same ground* as its counterpart, described twice |
| `incorporation_by_reference` | takes another exhibit's footprint | no courses of its own, and **complete as recorded** |

Both failure modes are real and were met in the pilot:

- **Perimeter**: doc 2021020901358005 p14, "Block 1908, Lots 4 and 60
  (Perimeter)" — one 8-course L-shape closing at 14,388.6 sf. It reconciles as
  PLUTO's lot 4 (4,297) + the document's lot 60 (10,092) = 14,389, to within
  0.4 sf. Posted against lot 4 alone it would treble that parcel.
- **Vertical**: doc 2012120600575002 Exhibits A and B are the *identical*
  footprint, one below and one above a 120-ft plane. Summed, the same 2,504.17
  sf of ground is counted twice.
- **Incorporation by reference**: Exhibit D of 2026012000388004 reads in full
  "ALL that volume of space ... above the Lower Limiting Plane ... within the
  boundaries of the Owner Premises described in Exhibit A". Scored as
  "summarised" it sends someone back to re-read a page that is already whole.

A `vertical` description must carry `vertical_extent`, including whether the
datum is DEFINED on the page. Doc 2012120600575002 spells it out ("120 feet
above the datum used by the Topographic Bureau ... which is 2.75 feet above
mean sea level"); doc 2026012000388004 says only "112 feet above Datum Level",
a defined term whose definition is elsewhere. Comparing either plane to a DOB
height without resolving the datum is wrong by that offset.

## What graduates a document type

An unseen document of the type decodes and validates with **no code changes**,
and the audit reports three outcomes — validated / failed validation /
unparseable — never two.
