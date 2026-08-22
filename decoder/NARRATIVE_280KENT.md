# Job narrative from documents — 280 Kent Avenue (Domino), BIS 320917503

Walked 2026-08-07. Purpose: prove that a job's **story** and its **party
layer** can both be built from the document history rather than the feeds.

19 documents · 104 scans · 28 PW1s · 1 job.

---

## THE PROJECT

    52 stories · 591 ft · 1,350 DU · 951,971 sf construction floor area
    zoning area 611,305 sf   residential 599,435 (R8, FAR 1.67)
                             commercial   11,870 (C2-4, FAR 0.03)
    R-2 apartment house · construction class I-B · seismic C
    structural occupancy III · peer review required BC §1627 (reviewer lic 092689)
    premises 280 KENT AVENUE, Brooklyn · BIN 3425051 · block 2414 lot 1

Filed at lot 1; the BIS header carries lot 3. **The job's own §1 and the record
header disagree on the lot** — spine matching must take §1, not the header.

---

## ★ THE ERA JOIN IS WRITTEN IN THE JOB DESCRIPTION

Document 01's description ends:

    NEW MIXED-USE BUILDING. DOB NOW JOBS: PL B01262921-S1, SP/SD B01270573-I1

and document 02's:

    PLUMBING WORK FILED UNDER DOB NOW JOB B01262921-S1

**A BIS job names its own DOB NOW continuation in free text.** The withdrawal
comment on doc 02 repeats it — `WITHDRAWN: 320917503 02 - PL BY NJY ON
04/08/26 … SUPERSEDING PLUMBING WORK FILED UNDER DOB NOW JOB B01262921-S1`.

That is a harvestable BIS→NOW edge, and it is the only one that exists for a
job that straddles the split. ⚠ **Consequence: BIS alone cannot tell you the
delivery stage of a straddling job.** `C/O Summary` here says *THIS JOB HAS NO
C OF O APPLICATION ON FILE* — not because nothing was built, but because the
certificate lives in DOB NOW.

---

## ★ THE ENTITLEMENT CHAIN IS IN "ALL COMMENTS", NOT IN ANY FIELD

    RESTRICTIVE DECLARATION RECORDED UNDER CRFN 2014000197874
    CPC APPROVAL GRANTED UNDER APPLICATIONS:
        C 140132 ZSK, C140133 ZSK, C140134 ZSK, C140135 ZSK,
        N140136 ZAK, N140137 ZAK, N140138 ZAK,
        N140139 ZCK, N140140 ZCK, N140141 ZCK
    THESE PREMISES … SUBJECT TO ZONING RESOLUTION SECTION 12-10 AS TO ZONING
    LOT OWNERSHIP … CRFN: 2014000427044, 2014000427045

Ten City Planning applications and three CRFNs — the DCP link and the ACRIS
link, both as prose in a comments blob. `§9` of the PW1 carries the same two
CRFN sets as checkbox fields, but the CPC calendar numbers appear **only**
here.

---

## VELOCITY — PLAN EXAM IS THE PRE-DEVELOPMENT STORY

    2014-05-30  pre-filed
    2014-06-02  filed
    2014-07-22  FIRST exam    DISAPPROVED   CLARA GOMEZ, Plan Exam Bklyn
    2014-08-02  RE-EXAM       DISAPPROVED   JAKE UDEH
    2014-09-12  RE-EXAM       DISAPPROVED   JAKE UDEH
    2015-01-13  RE-EXAM       APPROVED      SCOTT PAVAN — BORO COMMISSIONER
    2015-01-13  foundation approved
    2015-03-17  NB · FO · FO EA · OT · CC permits all issued   ★ CONSTRUCTION

**226 days filed → approved, 288 days filed → permit.** Three disapprovals,
and the approval was signed by the **Borough Commissioner**, not a plan
examiner — all four work types on the same day. Escalation to commissioner
level is a readable signal that a job was contested, and it is only visible in
Plan Examination; the feeds carry the approval date but not who signed it.

Permit renewals, still live:

    320917503-01-NB      seq 17   first 2015-03-17   last 2025-12-04
    320917503-01-FO      seq 16   first 2015-03-17   last 2026-02-18
    320917503-01-FO EA   seq 18   first 2015-03-17   last 2026-02-18
    320917503-01-EQ FN   seq 12   first 2015-03-17   last 2026-02-18
    permittee: ALBANESE

---

## THE AMENDMENT HISTORY IS THE NARRATIVE

Each PAA states, in its own words, what changed:

    06 → 01   revised Sched A, plans, PW1; floor designation, §8, §12, §11, §13
              OLD: 35 STORY NEW BUILDING → NEW: 36 STORY NEW BUILDING
    07 → 02   revised Schedule B, mechanical + plumbing plans
    08 → 03   supersede prior applicant of record …  §2, §3, §26
    09 → 05   update §2, §3, approved plan set
    10 → 05   update approved plan set
    11 → 03   correction to §9J — PEER REVIEW REQUIRED
    12 → 05   SOE drawings
    13 → 01   supersede prior applicant of record, OWNER SIGNATORY
    14 → 04   supersede prior applicant of record …  §1, §2, §3, §26
    15 → 05   update approved plan set
    16 → 01   updates to highlighted sections of PW1
    17 → 01   §8 only
    18 → 02   supersede applicant of record, OWNER SIGNATORY … §1,2,3,7,11,26
    19 → 01   administrative, §12; no change to plans or PW1A

PAA 06 records the building growing by a storey. PAA 11 records the peer
review being imposed after the fact.

## ★★ THE COMMENTS TELL YOU WHICH PW1 TO OPEN

Four amendments — **08, 13, 14, 18** — say *supersede … owner signatory* or
name **§26**. Those are the only four of 28 PW1s that can carry a new owner
contact; the rest leave §26 blank (see `PW1_SECTION26.md`).

**Selector: read the `Description of Amendment` first, open only the PW1s
whose text names §26 or the owner signatory.** 28 documents → 4. This is the
scalable form of "enter the documents".

---

## PARTIES — AND HOW EACH WAS REACHED

| role | who | contact | source |
|---|---|---|---|
| **Owner** | DOMINO A PARTNERS LLC · **HALE EVERETS**, Authorized Signatory | *blank on the page* | §26 |
| ↳ resolved | same person, sister entity GREEN STAR BUILDERS LLC | **45 Main Street, Brooklyn 11201 · 718-222-2503 / 718-978-5600** | `bty7-2jhb` |
| ↳ confirms | Two Trees LLC · David Walentas | 45 Main Street, Brooklyn 11201 · 718-222-2500 | `bty7-2jhb` |
| **Architect of record** (now) | BHASKAR SRIVASTAVA · DENCITYWORKS | 646-690-0333 · STUDIO@DENCITYWORKS.COM · 55 Washington St, Bklyn 11201 | §2 |
| **Architect** (2014, in the document) | BHASKAR SRIVASTAVA · **ISMAEL LEYVA ARCHITECTS** | **BSRIVASTAVA@ILARCH.COM** · 44 West 37th St, NY 10018 | PW1 doc 01 scan |
| Previous applicant of record | ISMAEL LEYVA · ISMAEL LEYVA ARCHITECTS PC · lic 021712 | — | §2 |
| **Filing rep** (now) | ALEXANDER RIPPERE · SOCOTEC | 646-847-5325 · CODE@SOCOTEC.US · 151 W 42nd St, 24th fl | §3 |
| **Expeditor** (2014) | T. DIMATTEI · VITACCO | **TDIMATTEI@VITACCO.COM** | All Comments *and* PW1 scan |
| Mechanical | DONNAMILLER JARED | — | doc 02 |
| Foundation + structural | PIMENTEL BENJAMIN | — | docs 03, 04 |
| Permittee | ALBANESE | — | All Permits |

Two things worth keeping:

1. **The owner's §26 was blank and the contact still came out** — by taking
   the *name* from §26 and the *contact* from the same person's earlier
   filings under a different entity. `HALE EVERETS` signs for `DOMINO A
   PARTNERS LLC` in 2014 with nothing attached, and for `GREEN STAR BUILDERS
   LLC` earlier with a full address and two phones. 45 Main Street is Two
   Trees' own address. **Name in the filing → contact in the history.**

2. **`PLEASE EMAIL OBJECTIONS TO TDIMATTEI@VITACCO.COM`** is stamped on
   documents 01, 02, 03 and 04. A working email address for the person
   actually driving the filing, sitting in a free-text comments field that no
   structured feed exposes.

3. The architect didn't change — **the firm did**. `ISMAEL LEYVA ARCHITECTS`
   (previous applicant of record) and `DENCITYWORKS` (current) are the same
   human, Bhaskar Srivastava, twelve years apart. Matching on firm name would
   have recorded a discontinuity that never happened.

---

## ⚠ THE LIMIT HIT ON THIS JOB

**Every one of the 28 PW1s here is an `ES` scan, and `ES` scans carry no OCR
text layer** — only the typed field overlay, and on this job the overlay does
not cover §26. So the four owner-signatory PW1s (08/13/14/18) could not be
read as text:

    doc 14  ES029100592    64 chars      scancode banner only
    doc 18  ES815508666    1 image stream, no text
    doc 19  ES837119645    1 image stream, no text
    doc 01  ES641077561    5,602 chars   ← page 2 only (§8); §26 not in this scan

Where the overlay *is* populated it is exact — doc 01 yielded
`BSRIVASTAVA@ILARCH.COM`, `TDIMATTEI@VITACCO.COM` and the CRFNs as clean text.

So the rule from `PW1_SECTION26.md` holds and sharpens:

- **`SC` (paper, B-scanned)** → whole form readable at OCR quality; §26 comes
  out. This is how the LIC owner contact was recovered.
- **`ES` (eFiling)** → only the typed overlay; §26 usually absent. Reading it
  needs the raster, not the text layer.

⚠ So **document-native owner contact is an SC-era capability.** For ES-era
jobs the party layer has to come from §2/§3 overlay text, the comments field,
and cross-era resolution of the §26 *name* — which is exactly what worked
here.
