# THE DATA SANITIZATION WORKFLOW

**This is the workflow for EVERY source-to-product build.** Defined once here and
instantiated per source: the five steps are identical everywhere, only the
*method* changes. Authority: *NYC CRE Decoding System (Diagram).pdf*.

⚠ **ACRIS IS THE FIRST ATTEMPT TO APPLY IT, NOT THE DEFINITION OF IT.** Login,
2026-08-14: *"this is the workflow for all source to product builds. we are doing
acris as our first source attempt to apply it."* So nothing ACRIS-specific
belongs in this file — no doc-id endpoints, no page geometry, no Socrata
partitioning. When something learned on ACRIS turns out to hold for every source,
it graduates here; until then it lives in `sources/acris/`. The reverse mistake —
generalizing from one source — is how a method gets mistaken for the
architecture.

⚠ **AND THE SECOND SOURCE IS THE REAL TEST.** Everything here reads as clean
while exactly one source has ever run through it. Expect this file to be wrong in
places that only DOB or DCP can reveal.

```
SOURCE   ACRIS · DOB NOW · BIS · DCP · DOF · HPD · OER · PLUTO · DOS · ZAP
   │
   ▼  ─────────────── DATA SANITIZATION ───────────────
   1 SPECIFICATION   specify inputs — what data and documents are in scope
   2 ACQUISITION     acquire data — retrieve the specified inputs
   3 EXTRACTION      extract evidence — raw data into structured evidence
   4 RESOLUTION      resolve lineages — link events, parties, records over time
   5 DERIVATION      derive outputs — metrics, flags, rights, statuses
   ─────────────────────────────────────────────────────
   │
   ▼
PRODUCT   Dashboards · Maps · Reports · Comparables · Participants

LIVE SYNC   MONITOR SOURCE → COMPARE → DELTA MANIFEST → back into sanitization

across every step:   TIME  ×  COST  ×  ACCURACY
```

## ⚠ SAME WORKFLOW AND FOUNDATION, DIFFERENT SANITIZATION STRATEGY PER SOURCE

Login, 2026-08-14: *"each time you go into a source you can have a different
sanitization strategy but always the same workflow and foundation... the system
is the copy and paste approach with slight modification for the source since
youll want different approaches to sanitizing various sources."*

**Fixed for every source** — the five steps and their order · one event graph at
step 4 · evidence carries provenance and a path · derivations are values, not
products · live sync returns to specification · a value refuses to exist without
its source reference.

**Chosen per source** — the unit of specification · what is worth acquiring ·
what is worth extracting · which lineages matter · which products consume it.

### The same five steps, instantiated two ways

| step | ACRIS | BIS Web |
|---|---|---|
| 1 specification | **the document** — 17M doc ids + index | **the job** — and ⚠ *a row is not a job* |
| 2 acquisition | every page image, ~9.3 TB | PW1 + ZD1 only |
| 3 extraction | 3 channels + fusion + escalation | project details + contacts |
| 4 resolution | conveyance and rights lineages | a project through its stages; people across projects; parcels across projects over years |
| 5 derivation | $/SF on air-rights transfers | development-pipeline values |
| product | air-rights market | dev pipeline map |

⚠ **THE UNIT OF SPECIFICATION IS THE FIRST CHOICE AND THE EASIEST TO GET WRONG.**
For ACRIS it is a document. For BIS it is a **job**, and a row is not a job:
`doc__=01` is the original and `02+` are amendments that restate nothing —
`zoning_dist1` is present on **0 of 63,293** NB amendment rows. Specifying BIS
per row reports the district as 24% missing; specifying it per job reports 100%
present. **Same data, and one of those numbers is an artifact of the unit.**
(NOW: 939,107 rows = 555,652 jobs; New Building is 9,432 jobs, not 54,043 rows.)

⚠ **A STALE FINDING IS AS DANGEROUS AS A MISSING ONE.** A 2026-08-06 note here
declared BIS document access refused (403 at the Akamai edge). It had been solved
in another conversation, and planning BIS around it would have discarded real
coverage. **Before instantiating a source, check whether its blockers are still
blockers** — the phase docs record what was true when written, and "we figured
that one out" lives in whichever chat did it.

## ⚠ DATA SANITIZATION IS THE WHOLE PIPELINE, NOT A STEP INSIDE IT

Steps 1–5 *are* the sanitization. It is the name for turning a raw source into
trustworthy derived values.

⚠ **This file previously described sanitization as a step between the source and
specification.** That was wrong, and the error mattered: it implied one cleaning
stage that everything passes through, which is exactly the shared-utility design
the next rule forbids.

## ⚠ PRODUCT IS OUTSIDE SANITIZATION, WITH ITS OWN STORE

Login, 2026-08-14: *"in the end product is out of the sanitization as it is just
pulling into its own supabase from derivations basically."*

Product is not step 6. It reads **derivations** — never raw documents, never the
event graph — into its own database. This is why the two Supabase projects are
separate by design:

| | store |
|---|---|
| decoder, through derivation | `trljekigamtnxqfoyorm` |
| product | its own |

⚠ **If a product is computing, a derivation is missing.** Any calculation in
product code is a value that was not derived — and the moment a second surface
needs it, the two disagree. Push it back into step 5; never share a helper.

## ⚠ SANITIZATION IS PER-SOURCE *AND* PER-PURPOSE

Login, 2026-08-14: *"data sanitization will look different depending on the
source because what we intend to get out of a source data will change depending
on what its used for."*

So it lives **inside each source folder**, shaped by intent, never in a common
cleaning layer. The same field sanitized for two purposes is two different jobs:

- ACRIS `document_amt` — authoritative as an index value, a **500,000× trap** as
  a price (it is 0 for every DEVR; price comes from the cover-page RPTT/RETT
  stamps)
- DOB `work_on_floor` — scope, never progress
- DTM `C/R/A/S/E` flags — **relationships, not identities**; 19,419 lots are
  mis-kinded, so never gate on `kind == "ground"`

A generic cleaner cannot know which question is being asked, so a generic cleaner
will launder one of them.

## ⚠ SPECIFICATION NEVER FINISHES

Live Sync loops back into it, which makes step 1 continuous rather than a
one-time act. For ACRIS it is two standing jobs:

| track | what it keeps current |
|---|---|
| **selection** | the doc-id map — `selection_daily.py` |
| **index** | the support index — `index_daily.py` |

⚠ **Freshness is the product, not maintenance.** A decoder that is right once and
stale in a month has no edge over what already exists. The dailies are the
differentiator; budget attention accordingly.

⚠ **A daily cannot replace an audit.** A forward-only monitor inherits every gap
it already has and reports clean forever — it cannot see a withdrawal or a
re-index. Both schedules, or the cheap check gets mistaken for a complete one.

## WHERE EACH STEP'S DATA LIVES — decided by VOLUME

| step | data | store |
|---|---|---|
| 1 specification | ids, geometry, index rows | **Supabase** — small, and every later step queries it |
| 2 acquisition | page images (ACRIS: ~9.3 TB) | **drives** — written once, read sequentially |
| 3 extraction | accepted text | **drives** + offline backups |
| 3 extraction | **evidence records** | **Supabase** — small, queryable, and the bridge |
| 4 resolution | the event graph | **Supabase** |
| 5 derivation | precomputed values | **Supabase** |
| product | — | its own store |

⚠ **THE EVIDENCE RECORD IS WHAT LETS THE OFFLINE HALF AND THE ONLINE HALF BE ONE
SYSTEM.** It carries `document_id` · page · claim · confidence · channel
agreement · **and the local path**. Without the path, an online assertion can
never be audited against its offline source and the bulk becomes unreachable
rather than merely offline.

## EVERY PHASE FOLDER HAS TWO DOCUMENTS, AND THEY MUST NOT BLUR

- **`workflow.md`** — how we do it: the system, the runbook, the calibrations
- **`data.md`** — what it PRODUCES, where that lives, what consumes it

Mixing them is why "what does this phase actually hand over" was never
answerable in one place.

## ⚠ TECHNICAL DEPTH ONLY WHERE THE STEP IS PERFECTED

A file must not sound more settled than the step is. Writing speculative detail
is inventing a calibration. Depth is earned by measurement.

## ⚠ A CALIBRATION IS A VALUE PLUS ITS EVIDENCE

Recorded as **value · how it was measured · when · what breaks if it changes**.

`WORKERS = 5` written alone invites trying 8 — which measures *slower than
serial*, because the API throttles a burst.

- **Never record a value you did not measure here.**
- **Re-measure before trusting an old calibration on new material.**
- **An A/B must alternate order and repeat.** A burst-throttled API reports
  whichever arm ran second as faster — that cost a 3.7x-backwards conclusion.

## THE TWO RULES THAT KEEP THIS TRUE

1. **Point at configs, never copy them.** A transcribed value goes stale silently
   and is then *trusted*; a pointer stays true.
2. **Status is computed, not written.** `python status.py` reads the state files
   the jobs themselves write, so the board cannot disagree with reality.

⚠ **And it reports COVERAGE, not only scores.** The most expensive regressions
here were coverage failures wearing a quality mask. **A score computed over fewer
pages is not a worse score, it is a different question.**
