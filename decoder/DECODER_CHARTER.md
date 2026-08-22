# THE DECODER CHARTER — read this when you are confused, every session at start

**Login's instruction, 2026-08-06: the decoders are crossing each other. This
file is the arbitration. When your chat is unsure what it should be doing, the
answer is HERE, not in your memory of your kickoff prompt.**

---

## 1 · Who you are — say it at session start

Paste-and-fill, first message of every session:

> I am the **____ decoder**. My source(s): ____. My current assignment: the one
> written in `status/<my-lane>.md`. I emit facts only from my own source, each
> with document_id + page. I do not fetch any other lane's source.

If you cannot fill "current assignment," STOP and read §4.

## 2 · The ownership table — the SOURCE decides, never the topic

**SPLIT 2026-08-06 (Login's call): "DEVELOPMENTS" was a QUESTION, not a source,
and a chat holding four custodians confuses itself. One chat = ONE CUSTODIAN'S
traps. The development timeline is a VIEW assembled from the sink at the spine —
no chat owns it.**

| lane | owns these sources (one custodian each) | never touches |
|---|---|---|
| **ACRIS** | ACRIS documents & images, city register covers | everything else |
| **DOB** | BIS · DOB NOW · B-Scan · permits (incl. 1989 bty7-2jhb) · CO | HPD, DORIS, ACRIS images, BSA/LPC/DCP PDFs |
| **HPD** | I-cards · CONH · registrations · violations/litigation | DOB portals, ACRIS |
| **BSA** | BSA applications + decision PDFs (10,805) | LPC, DCP, everything else |
| **LPC** | LPC designations/calendarings (39,363) | BSA, DCP, everything else |
| **DCP** | ULURP / ZAP records + documents | BSA, LPC, everything else |
| **DOS** *(ARCHIVED 2026-08-06 — no standing chat)* | data.ny.gov entity + filings — **as a LOOKUP SERVICE, see below** | everything else |
| **COMPARABLES** | StreetEasy · DOF sales | all government document stores |
| *(parked)* | DORIS tax photos — assignment-driven, no standing chat | |

**DOS's purpose, defined (it never had one — Login, 2026-08-06).** DOS is not a
corpus to browse; it is the **name-resolution service** for every other lane.
Its input is a QUEUE: entity names emitted into the sink by ACRIS (parties),
HPD (registration contacts), DOB (applicants). For each name it answers exactly
three questions — (1) active or dissolved (dissolved = a deal signal, not a
miss), (2) service-of-process address (the principal or their attorney — the
reach ladder's rung), (3) filing lineage where joinable. It emits those as
facts keyed to the requesting lane's BBL and STOPS. If its queue is empty, its
status file says BLOCKED: queue empty — it does not go exploring.

**DOS is ARCHIVED as a chat (Login, 2026-08-06).** The lane definition above
stays: when a name-queue accumulates in `status/dos.md`, any chat Login opens
(or `dos.py` run directly — it is built and tested) works the queue and closes.
A lookup service runs on demand; it does not idle.

**The collision rule.** A document in YOUR source that mentions another source's
material (a ZLDA cites a DOB application; a BSA decision cites a deed) yields a
**pointer fact** — `{cites: <id>, source: <their lane>}` — and NOTHING more. You
never follow the pointer into their source. They will meet you at the spine.

**The topic trap.** "Zoning" is not a lane. "This parcel" is not a lane. Five
lanes can all hold facts about one parcel's zoning — each from its OWN source.
That is the design, not a collision. A collision is only when two lanes fetch
the SAME source.

## 3 · Where facts go

* every fact: `sink.emit(...)` with **document_id + page** or it is not a fact
* one chat writes ONE `source` value — never another's
* heartbeat with a **denominator** (`done/total`), every N documents
* found-nothing = `complete` with 0 facts; never-ran = silence. **Never alike.**

## 4 · Direction — no decoder "just keeps learning"

Each lane has `status/<lane>.md` with exactly three lines it rewrites as it works:

    DOING: <the current assignment, one line, with a denominator>
    NEXT:  <what follows when DOING completes>
    BLOCKED: <what it cannot resolve alone, or "nothing">

The assignment is always one of:
1. **a parcel walk** — every document your source holds for one spine parcel,
   fails register kept, 100% coverage before moving on (the lot 49 discipline), or
2. **a type study** — open N documents of one type to learn its layout and traps, or
3. **a coverage sweep** — a bounded, counted population pass with the count
   printed first.

"Explore," "continue," "keep going" are NOT assignments. If DOING is empty,
take the next item from NEXT; if both are empty, write BLOCKED and ask Login.

## 5 · When you are confused — the protocol

1. Re-read this file, then your `status/<lane>.md`.
2. If the confusion is "whose source is this?" → §2 table decides. Not yours →
   emit a pointer fact and move on.
3. If the confusion is "what should I do next?" → §4. Never invent a mission.
4. Still stuck → write one precise question into BLOCKED and STOP working the
   confused thread. A stopped decoder costs nothing; a guessing decoder pollutes
   the sink for everyone.

## 6 · THE PIPELINE — parcels flow through lanes; no lane waits

**Login's design, 2026-08-06:** ACRIS finishes a lot → writes a HANDOFF →
starts its next lot. The receiving lane picks the handoff up on its own clock.
Both lanes are always working; the parcel is what moves.

* Handoffs live in `decoder/handoffs/<bbl>.md`, written by the lane that
  finished, addressed to the lane that's next (usually ACRIS → DOB → HPD).
* A handoff carries exactly four things: **join keys** (BBL family, job-number
  and CRFN pointers found in the finishing lane's documents), **the stage
  skeleton** (dated stages the finishing lane established), **the trace so far**
  (entity → name, waiting for the contact rung), and **open questions the
  receiving source can answer**. Never raw prose dumps.
* The receiving lane appends its findings to the SAME file and flags
  discrepancies — a date or sum that doesn't reconcile is a TRAP FOUND, the
  most valuable output the pipeline produces.
* Each lane's `status/<lane>.md` NEXT line points at `handoffs/` — an arriving
  handoff is the default next assignment.

**The chain is short; everything else is a spoke (Login, 2026-08-06 — a linear
pipeline through BSA/LPC/DCP would confuse itself).** Two kinds of lane:

* **CHAIN lanes — ACRIS → DOB → HPD.** Stages every built parcel actually has:
  recorded life → construction life → occupancy life. The baton passes in that
  order, each lane owed a full question list.
* **SPOKE lanes — BSA · LPC · DCP/ZAP.** Entitlements are CONDITIONS, not
  stages: most parcels have none. A spoke lane never receives the baton — the
  handoff file carries one **presence-check line per spoke** ("anything on
  these BBLs / this block?"). The spoke answers in place: findings if yes,
  **"none found" + the exact query used** if no (found-nothing ≠ never-ran,
  as always). Spokes work their checks in batches on their own clock; nothing
  upstream waits.
* A spoke answering YES upgrades itself for that parcel — its finding (a
  variance, a designation, a ULURP action) gets its own dated entry in the
  handoff and its own facts in the sink, and may add questions for the chain
  lanes (e.g. a BSA term-expiry the CO must be checked against).

## 7 · The spine is the only meeting place

Every lane keys facts to spine BBLs (`spine.py --walk <bbl>` for the family).
No lane asks another lane a question directly; the sink + spine ARE the
conversation. If your fact can't name its BBL, it waits until it can.

⚠ Known spine traps every lane inherits: C/R/A/S/E flags are RELATIONSHIPS not
identities; condo BILLING lots are in neither DTM layer; retired BBLs drop out
of gate-keyed pulls — see `SPINE_DEFECTS.md`.
