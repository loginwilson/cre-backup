# Non-ACRIS sources → the shared account chart
# (DOB BIS + NOW · BSA · DCP · LPC · HPD · the Zoning Resolution)

All six workbooks carry the **same 15-function legend as ACRIS**. Function is
the join language; the account chart absorbs every source without redesign.

---

## The Zoning Resolution — a live feed, not a workbook

`zr.planning.nyc.gov` is fetchable, text-based and section-addressable, and the
section number is its own address: **first digit = Article, second = Chapter**,
so `23-22` is `/article-ii/chapter-3/23-22` and `77-22` is
`/article-vii/chapter-7/77-22`. `zr_feed.py` fetches, parses the tables and
caches the **parsed facts** — same discipline as the document images: the source
stays where it lives, only what it said is kept. `LAST AMENDED` is part of the
fact, so a re-run detects an amendment.

**Why it had to be live.** Every FAR reaching the decoder had been coming
through a hand-transcribed chart, and transcription cannot carry a footnote —
but in the Resolution the footnote *is* the regulation. ZR 23-22 lists R6 at
2.20 in its own row and again as "R6¹" in the 3.00 row, where footnote 1 reads
*"For zoning lots, or portions thereof, located within 100 feet of a wide
street"*. Flattened to a number, R6 becomes either 2.20 or 3.00 and one of them
is wrong on every lot. Checked against the live section, 26 of 27 districts in
the transcribed table agreed — and the one that did not was exactly the one
whose rule lived in a footnote.

So FAR is not a number per district. It is a number per **(district,
condition)**, and the Resolution is the only source that publishes both.

Note the footnote's own wording: "or portions thereof". Wide-street FAR applies
to the part of the lot within 100 feet of the wide street, so it is a second
axis of splitting on top of the district boundary. Not yet computed — both
figures are carried and the frontage is stated as un-established.

---

## LPC — the envelope constraint that zoning cannot see

**A landmark's buildable envelope is not decided by FAR.** The workbook says it
outright on Rooftop Addition: whether an enlargement is visible, and therefore
permissible, is decided at LPC, not in the zoning calculation. A site can carry
unused development rights that the Commission will never let anyone build.

| Filing | Function | Account | Why it matters |
|---|---|---|---|
| **Individual Landmark and Historic District Building Database `gpmc-yuvp`** | ENCUMBER / IDENTIFY | `use_restriction` | Per-BBL: is this parcel regulated at all. The parcel-level join — everything else here hangs off it. |
| **Designated and Calendared `ncre-qhxs`** | ENCUMBER / ENTITLE | `standing` | **Calendared ≠ designated.** A calendared building is not yet landmarked but is already constrained in practice. An encumbrance with no recorded instrument behind it. |
| **Certificate of Appropriateness (COFA)** | PERMIT / ENVELOPE | `entitlement` | Commission-level, public hearing. Required for additions and demolition. |
| **Commission Denial** | PERMIT / ENVELOPE | `entitlement` | Can end a development scheme outright. The negative case is as much a fact as the grant. |
| **Rooftop Addition (work type)** | ENVELOPE | `envelope_claimed` | Where an enlargement is actually decided. |
| **Landmarks Violations `wycc-5aqt`** | DISTRESS | `distress` | Can force restoration at the owner's cost. |
| **Permit applicant + owner `dpm2-m9mq`** | PARTY | `party_observation` | Names **both** applicant and owner of record with full mailing addresses — an owner-contact source independent of ACRIS and DOB. |

**The connection to what is already built:** landmark development rights are
*transferable* (ZR 74-79 and the special-district TDR regimes), so a designation
does not destroy an envelope — it detaches it. That is a DEVR subtype, which
means LPC designation status belongs in the envelope ledger, not beside it.

## HPD — and the blind spot it closes

Most of HPD maps to `distress` and `occupancy` and needs no comment. Three
things do:

- **Shareholder (`feu5-w2e2` contact role) — this closes a hole in an
  ACRIS-only decoder.** A co-op transfers *shares*, not real property, so no
  deed is recorded and ACRIS is silent on every co-op ownership change. The
  registration is one of the only public routes to who holds the building. A
  parcel lifespan built from ACRIS alone would show a co-op as never having
  changed hands.
- **Certification of No Harassment `bzxi-2tsw`** — ENCUMBER / PERMIT. A CONH
  requirement **blocks DOB permits** until HPD certifies. A hard per-parcel
  gate on development that appears in no recorded instrument. → `standing`.
- **Registration is annual, not event-driven** — it files on the calendar, so
  it refreshes the owner/agent picture on a cadence the deed never does. That
  makes it a *monitoring* source rather than an event source, and the change
  detector should treat it accordingly.
- **Local Law 44 Unit Income Rent `9ay9-xkek`** — VALUE. One of very few public
  sources publishing an actual rent, per unit.
- ⚠ **Violation Class I**: the workbook flags that its meaning needs confirming
  against HPD documentation before anything relies on it. Not encoded.

New accounts needed beyond the DOB set: none. `use_restriction`, `standing`,
`entitlement`, `distress`, `occupancy`, `party_observation` and
`envelope_claimed` absorb all of LPC and HPD.

---

## DCP — and one correction to work already built

**`fdkv-4t4z` NYC Zoning Tax Lot Database is the authoritative per-BBL zoning
assignment, and it supersedes PLUTO's single zoning field.** Measured across the
pilot's 323 baseline parcels: **123 carry a commercial overlay or special
district that PLUTO's `zonedist1` drops** (~38%), and **22 are split between two
or more districts, where a single FAR is simply wrong.** The Knickerbocker
merged zoning lot, for instance, sits entirely in Special District **TA**
(Special Transit Land Use, Second Avenue Subway) with a **C1-5** overlay on the
R10A lots — none of it visible in PLUTO. Baselines now carry `dcp_zoning`, and
the audit fails on split-district lots rather than quietly using one FAR.

Other DCP layers that change envelope or viability answers:

| Layer | Function | Why it matters |
|---|---|---|
| **1961 Zoning Districts** | ENVELOPE | Non-conforming use rights descend from what was mapped in 1961. Likely the key to buildings that exceed today's FAR — e.g. the Knickerbocker's 149,436.84 SF on a lot whose as-of-right is ~100,300. |
| **Special TDR Regulations** | ENVELOPE | Where development rights may be transferred *and under what rules* — the regime governing every DEVR we decode. |
| **MIH `bw8v-wzdr`** | ENVELOPE/OCCUPY | Where affordability unlocks density; explains floor area no transfer accounts for. |
| **E-Designations `hxm3-23vy`** | ENCUMBER | Hazmat/noise/air conditions bound to a lot — "does not appear in the zoning diagram". |
| **POPS `rvih-nhyn`** | ENCUMBER | Permanent public-access obligation taken in exchange for bonus floor area. |
| **ZAP–BBL `2iga-a6mk`** | ENTITLE | Makes land-use applications parcel-addressable — the ENTITLE feed. |
| **City Map Change (CM/MM)** | PARCEL | A street must be demapped before the land beneath it is developable. |

## BSA — the ENTITLE gap, and it reaches back further than ACRIS

**The Resolution is the document, not the grant.** The workbook says it plainly:
the conditions in it *bind the land and every successor owner*. That is the same
premise as this whole project — the index tells you a grant exists; only the
document says what it does.

- **Calendar numbers run to the 1930s–40s** ("148-48-A is the 148th application
  of 1948"), and grants from that era are **still in force**. That is deeper
  reach than ACRIS's ~1966 digital horizon.
- **SOC (Special Order Calendar)** is the second most common filing: it amends,
  extends or waives conditions of a prior grant. Pure lifecycle — same handling
  as ACRIS amendments and releases.
- **Extension of Term**: a special permit granted for a fixed term makes the use
  **illegal when the term lapses**. An encumbrance with an expiry date, and
  reporting it as live after expiry is the error class we already guard against.
- **BZY / ZR 11-331** vested rights preserve a permit against a later rezoning —
  the reason a site can exceed the FAR its current district allows.
- **GCL 35 / 36** — permission to build in a mapped street bed, or on a lot with
  no frontage. A hard gate on interior and irregular lots: viability, not bulk.

Accounts: `entitlement` (new) for grants and their status; conditions post to
`use_restriction` / `standing` with expiry; approved plans to `envelope_claimed`.

---

# DOB (BIS + NOW) → the shared account chart

Mapping only. Nothing is built yet: ACRIS's ENVELOPE+ENCUMBER family graduates
first. The point of writing it now is that the schema and contract are *designed*
for these events rather than retrofitted around them.

Both DOB workbooks carry the **same 15-function legend as ACRIS**. Function is
therefore the join language across sources, and the existing account chart takes
DOB events with two additions (`asbuilt`, `envelope_claimed`) and no redesign.

## Accounts

| DOB function | Account | Feeds |
|---|---|---|
| PERMIT | `permit` | job filings, work permits, renewals. What is being *done*. |
| ASBUILT | `asbuilt` **(new)** | CO / TCO / LOC / PW7 / TR1. What legally *exists*. ACRIS has no equivalent — this is the complement, not a duplicate. |
| ENVELOPE | `envelope_claimed` **(new)** | ZD1, ZRD1, PW1B, NB and PAA floor area. **Never `envelope_transferable`.** |
| OCCUPY | `occupancy` | CO use groups per floor, PA certificates, signs, antennas. |
| DISTRESS | `distress` | violations, ECB/OATH, SWO, stalled-site register, complaints. |
| PARTY | `party_observation` | PW1 §26 owner with title/business/phone/email; licence register. |
| PARCEL / IDENTIFY | `bbl_spine` | SI and SC job types — see below. |
| COST | `cost` | PW3 cost affidavits (understated by filers; usable as a series, not a valuation). |
| TITLE / ENCUMBER / CAPITAL | — | ACRIS only. DOB never conveys anything. |
| ENTITLE | — | **Neither source covers it.** ULURP, BSA variances and special permits are DCP/BSA — a third source, later. |

## The rule that keeps the envelope honest

**A recorded instrument changes what MAY be built. A DOB filing only describes
what is being built or claimed.** So DOB floor area never enters
`envelope_transferable`, and `decoder_v_envelope_adjustment` already filters to
`source = 'acris'`.

What DOB floor area *is* good for is the strongest cross-source check available:

    ZD1 / PW1B claimed floor area   vs   baseline(t) + Σ recorded transfers

A developer claiming more floor area than the record can account for is a
finding — either rights we have not decoded yet, a bonus or special permit
(ENTITLE, uncovered), or an overclaim. Any of the three is worth knowing, and
none of them is visible from either source alone.

Immediate use: the Knickerbocker quantity that no ACRIS instrument states is the
applicant's own computation on the **ZD1 for DOB job M01361353** (301 East 71
Street, 29 storeys, 138,596 SF, filed 2026-06-09). That is where the number
lives, and it is a document decode, not a structured pull.

## Two DOB job types are lineage sources

The workbook says it outright: **SI (Subdivision — Improved)** is "the DOB side
of lot lineage" and **SC (Subdivision — Condominium)** is "what mints the 1001+
unit lots."

That is authoritative evidence for exactly the problem the spine solved by
inference. Today a condo unit lot resolves by chaining a document's "f/k/a Lot
149" recital to PLUTO's `condono`/`appbbl`; an SC filing records the event
itself, with a date. SI/SC should become the second spine source, ranking above
PLUTO and below the recorded documents.

## Structural difference from ACRIS — plan the ingestion accordingly

ACRIS is a **document-decoding** problem: scanned images, vision extraction, 126
types whose titles lie. DOB is mostly a **structured-data** problem — 15 Socrata
datasets with real fields — with a document tail where the value concentrates:

- **PW1 §26** — owner name, title, business, phone, email. The richest contact
  document in the system, and the BIS page truncates before reaching it: the
  data is only in the PDF.
- **ZD1 / ZRD1 / PW1B** — the zoning computation and any binding determination.
- **CO / TCO** — use, occupancy group and dwelling units per floor.

So the DOB front end is a bulk structured pull plus a targeted PDF decoder,
sharing the ledger, spine, validators and audit — not a second copy of the ACRIS
vision pipeline.

## Traps the workbooks flag, to encode as checks from day one

- **PAA** amends an approved filing: scope and floor area change materially with
  no new job number. *A job tracked by number alone will miss it* — the DOB
  analogue of ACRIS amendments, and the same lifecycle handling applies.
- **Renewals without sign-off** are the velocity signal: a run of renewals with
  no completion means slow or stalled work.
- **Sidewalk shed with no active job** is a stalled-site signal.
- **FN / SF / EQ / CH** are mobilisation, not construction. **FO / EA** are
  irreversible and mark the true start of a new building.
- **ACP5** asbestos assessment is often the earliest public signal of a planned
  demolition — earlier than the DM filing itself.
- BIS job documents are numbered: doc 01 is the original, doc 02+ are amendments
  under the same job number.
