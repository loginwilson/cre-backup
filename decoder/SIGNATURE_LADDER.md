# Messy signatures — how a scrawl becomes a person

Handwritten signatures are normal on deeds and common on everything else. The
mistake is trying to read them. The method is to **not** read them, and to
resolve the person from somewhere the name is printed.

## The one rule everything else follows

**A signature is the WEAKEST evidence of a name and the STRONGEST evidence of an
act.** Split them:

| what | confidence |
|---|---|
| someone executed this instrument | certain |
| in this stated title | certain — the title is printed |
| on this date, for this entity | certain |
| and their name is "…" | **often uncertain, sometimes illegible** |

Recording those at the same confidence is the error. In doc 2017053000419005 the
titles (**Vice-Chairman**, **Clerk of Session**) are printed and unambiguous while
both names are barely legible. "Clerk of Session" is the correct Presbyterian
officer to execute for a board of trustees — so the execution is corroborated as
*regular* even though the name cannot be read at all.

## The join key is not the name

Resolve on **(entity + title + date)**. All three are readable when the signature
is not, and they are enough to find a printed instance of the same person.

## The ladder — printed rungs, roughly in order of reach

| rung | source | gives |
|---|---|---|
| 0 | the signature | the ACT; a name at low confidence |
| 1 | **the jurat / acknowledgment** | the signatory's name TYPED into the certificate, plus the notary |
| 2 | **the Notices block** | name, **attention-party**, street address, phone, fax — typed |
| 3 | **ACRIS party index** (`636b-3b5g`) | entity names and ADDRESSES, typed from the cover sheet |
| 4 | **DOB PW1 §26** | owner name, title, business, **phone and email** — the richest, and only in the PDF |
| 5 | **HPD registration contacts** (`feu5-w2e2`) | head officer, managing agent, **shareholder** — refreshed ANNUALLY |
| 6 | **LPC permit** (`dpm2-m9mq`) | applicant AND owner of record with mailing addresses |
| 7 | **NYS DOS corporate filings** | officers and the address for service — the rung that turns an SPE into people |
| 8 | sealed certifications, DOF `Auth_for_Change` | architect (with **licence number**), surveyor, survey date |

Each rung is a *different document type*, which is why the ladder only works once
several types are decoded for the same parcel — and why the party observations
must be stamped with date and role rather than collapsed into a contact list.

## What the index will NOT give you

The ACRIS party index for doc 2017053000419005 lists three entities. **The First
Presbyterian Church in Jamaica is not among them — and it signed the instrument.**
The index under-reports parties, so the signature page is not a nicety: it is
sometimes the only place a party appears at all.

## Confidence is upgraded, never overwritten

```jsonc
"signature_blocks": [{
  "entity": "Trustees of the First Presbyterian Church in Jamaica",
  "signatory_as_written": "DORA GRISZELL",
  "name_confidence": "handwritten_uncertain",   // legible_print | typed |
                                                // handwritten_uncertain | illegible
  "title": "Clerk of Session",                  // printed — high confidence
  "resolved_name": null,                        // filled from a PRINTED rung
  "resolved_from": null,                        // which rung, which document
  "page": 42
}]
```

The original transcription is never edited. A resolution lands *beside* it with
its source, so a wrong resolution is visible and reversible — the same rule the
entity resolver follows, and for the same reason: **a false merge invents a
relationship and there is no way to see it afterwards.**

## Where this is going

Rungs 0–3 identify the actor. Rungs 4–6 make them reachable. Rung 7 turns an SPE
into named people. Only then is a profile worth building — and it is built on
observations that each cite a document, so any claim about a person can be walked
back to the page it came from.

## ★ THE STAGE-SYNC (Login, 2026-08-06) — the parcel climbs the ladder FOR you

*"Deed will give entity, the mortgage will give name, and the PW1 will give
contact. That's your trace, and you can sync it to the parcel through its
stages."*

The rungs are not just alternative sources — **each lifecycle stage EMITS the
next rung as a matter of course**:

| stage | instrument the stage must produce | rung it emits |
|---|---|---|
| acquisition | DEED | **ENTITY** — the SPE (that is all a deed ever names) |
| financing | MTGE/AGMT jurat + signature block | **NAME** — the lender requires a human's typed name in the acknowledgment |
| construction | DOB PW1 §26 | **CONTACT** — DOB requires a reachable owner: phone + email |
| operation | HPD registration (annual) | contact REFRESHED every year |

So a decoder never hunts for the person: walking the parcel's documents in
stage order upgrades entity → name → contact automatically, and each
observation is already stamped with the stage (and date) at which that person
was attached to the parcel.

**Worked on lot 49 (Block 800), from today's reads:**
* DEED 2013080901116003 → entity: **LAM GEN 25 LLC** (and the exiting entity,
  112-118 West 25th LLC c/o Extell)
* ZLDA/financing signature blocks + jurats → names, all typed in the notary
  certificates: **Marc Kwestel, VP** (signs Extell's SPE in 2013 in TWO
  capacities), **Jeffrey Lam** (signs BOTH Lam SPEs in 2019 — one signatory =
  one control across the 49/50 split), **Jonathan Pressman** (board member,
  133 W 24th co-op), **David L. Berliner, VP** (Brick Farms co-op)
* construction 2015 → the PW1 for the hotel job carries the contact — **that
  rung lives in the DOB lane**; ACRIS emits the job-number pointer, the spine
  syncs the two.

Cross-lane by design: deed and mortgage are ACRIS rungs, the PW1 is a DOB rung,
the annual refresh is HPD — the trace is assembled at the spine, which is why
no single decoder owns "the player" (see DECODER_CHARTER.md).
