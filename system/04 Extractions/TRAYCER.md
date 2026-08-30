# Traycer — paste this, once

Everything below the line. It defines the workflow, and Traycer runs it.

---

```
Set up a repeating two-agent workflow. Agents: A (Claude Code) and B (Codex).
Peers — neither is senior, neither defers.

WORKFLOW SHAPE

  BLOCK 1   FRAMEWORK CREATION      both agents, runs once
      ↓
  BLOCK 2A  EXTRACTION — agent A  ┐ run in PARALLEL, fully ISOLATED
  BLOCK 2B  EXTRACTION — agent B  ┘ from each other
      ↓
  BLOCK 3   REVIEW · VERIFY · ITERATE      both agents
      ↓
  back to 2A/2B with a new document id and the improved framework
      ↓
  3 → 2A/2B → 3 → 2A/2B …  until the exit condition in Block 3

2A and 2B MUST NOT share context. Neither agent may see the other's reasoning,
partial work, output, or working directory until both have completed. If they run
in a shared thread, enforce it as silence: from the moment the id is issued until
both post DONE, neither says anything about the document — no findings, no partial
reasoning, no questions to each other about it. The word DONE, and nothing else.

That isolation is the only evidence this workflow produces. Everything else is
recoverable; a contaminated round is not. If it breaks, discard both extractions,
drop the document, restart 2A/2B on a different one.

═══════════════════════════════════════════════════════════════════════════
SHARED CONTEXT — all blocks
═══════════════════════════════════════════════════════════════════════════

THE GOAL

Build the extraction framework for NYC C.R.E.D.: the rulebook that turns any
document in the Legal Instruments DB into its event table.

The framework is the deliverable. The extractions are not — every document exists
only to expose where the rules are underspecified. Done when a model that has never
seen this conversation reads the framework and extracts the same way you do.
Production runs on an open-weight model, so the rules cannot lean on the reader
being clever: where rules are silent, a capable model interpolates plausibly, and
plausible interpolation is indistinguishable from fact everywhere downstream.

WHAT EXTRACTION HAS TO DO

A document is not a fact. It is a record of things that happened. Each is read
INDEPENDENTLY — no other documents, no prior state of the parcel, no outside
lookups — and distilled into events. Events fan to the BBLs they affect, sort by
when the thing HAPPENED, and resolve into a state matrix: time down, function
across, each cell the state of one function at one moment.

Eleven functions, fixed:
  Identity · Title · Entitlement · Envelope · Encumbrance · Capital
  Permit · As Built · Occupancy · Cost · Value

Their boundaries are not fixed, and that is where the errors live. Is a restrictive
declaration Encumbrance, Envelope, or both? Settle it with a procedure, not a
description.

Tagging function and date is the floor, not the job. The work is PACKAGING each
event: its mode (create / modify / transfer / terminate / assert / correct — a
mortgage origination and a satisfaction are the same function and opposite in
effect); its parties with their roles and shares, many per side or none; whether it
is directional at all; quantities, including the case where one stated amount
covers several events and the allocation is NOT derivable; its terms — rate,
maturity, duration, conditions, options — which seed every predictive product and
are the first thing to get silently dropped; and each parcel's role, since an air
rights transfer's granting and receiving lots are not interchangeable.

One instrument commonly yields several events, across several functions, on several
parcels.

FILING DATE IS NOT EVENT DATE. A 2020 filing may record a 2018 event. Every event
carries a derived date and the basis it came from, and a rule for when the document
supports none — never a silent fallback to the recording date.

Distinguish NO_CHANGE, UNKNOWN, NOT_APPLICABLE and ASSERTED_NONE. A blank cell in
the matrix is otherwise meaningless.

EVERY FIELD CARRIES EITHER A VERBATIM QUOTE AND ITS LOCATION, OR THE FRAMEWORK RULE
THAT DERIVED IT AND THE INPUTS IT USED. A field with neither is a defect whether or
not the value is right. This is the only mechanical guarantee that the framework,
rather than your own knowledge of New York real estate, is doing the work.

ACCESS

One row gives you everything. Example:

  id            2002122000002001
  detail url    https://a836-acris.nyc.gov/DS/...DocumentDetail?doc_id=...   IGNORE
  image url     https://a836-acris.nyc.gov/DS/...DocumentImageView?doc_id=... IGNORE
  registration  {"type":"SATISFACTION OF MORTGAGE","pages":"2",
                 "doc_date":"11/20/2002","crfn":"2003000000003",
                 "recorded":"1/6/2003 10:30:58 AM","borough":"MANHATTAN",
                 "amount":"$0.00",
                 "parties":[{"panel":"1","name":"LIPP, ANTHONY J"},
                            {"panel":"2","name":"CHASE MANHATTAN MORTGAGE"}],
                 "parcels":[{"bbl":"1011321063","partial":"ENTIRE LOT",
                             "use":"DWELLING ONLY - 3 FAMILY",
                             "address":"161 WEST 61 STREET","unit":"11A"}],
                 "at":"2026-08-20T17:03:22"}
  pdf           By Document\2003\01 Jan\06\2002122000002001.pdf

You read three things: the id, the registration, and the document. Never the urls —
the image is already on disk.

The pdf value is relative. Hand it to the resolver and open what comes back:

  import sqlite3, corpus_paths as CP
  c = sqlite3.connect("file:%s?mode=ro" % CP.NAV_DB, uri=True)
  c.execute("PRAGMA busy_timeout=30000")
  c.execute("SELECT id, pdf FROM navigation WHERE pdf LIKE '%.pdf' ORDER BY id")

  path = CP.doc_path(pdf_value)        # Path, or None if the value is a state
  if path is None:      continue
  if not path.exists(): report_integrity_problem(did, path)   # db/store disagree
  read(path)

That is the whole read side. Never hand-join, never re-derive — doc_store_dir()
looks right and is the writer's. Read-only with busy_timeout; the register lane
writes constantly and a lock error looks exactly like a missing document. Full
detail and four real traps: D:\CRE Decoding System\04 Extractions\DOCUMENT ACCESS.md

THE PATH IS A LOCATOR, NOT EVIDENCE. That folder says 2003\01 Jan\06 — mirroring
the recording date, disagreeing with doc_date, disagreeing again with the date
inside the id itself. Three different dates before you open anything, and none is
necessarily the event date. Paths, folders, filenames, urls and pipeline metadata
are never citable — and "at" is the crawler's timestamp sitting inside the
registration JSON, so citability is decided field by field, not blob by blob.

FIVE THINGS THAT WON'T OCCUR TO YOU

Everything else you can work out as you go. Not these — in each one the natural
move is the wrong one.

1. DEFINE HOW EVENTS BECOME THE MATRIX BEFORE THE FIRST EXTRACTION. How events fan
   to BBLs, sort, tie-break, fold into a cell, serialize. "We got the same result"
   means nothing until this exists, and you will otherwise burn rounds arguing over
   differences that are only in how you each drew the table.

2. WORK BLIND WHEN EXTRACTING. You will want to collaborate. That instinct destroys
   the only evidence this workflow produces.

3. IF A DIFFERENCE DOESN'T CHANGE THE MATRIX, DON'T WRITE A RULE FOR IT. Log it and
   move on. Legislating every discrepancy produces a rulebook too bloated for any
   other model to apply — which fails the goal without ever looking like failure.

4. DON'T BUY AGREEMENT BY FLAGGING. A framework that marks everything uncertain has
   no disagreements, passes every check, and extracts nothing. Every individual
   choice to flag will feel defensible. Flag when the DOCUMENT is ambiguous, never
   when the RULE is hard to write, and track your emitted-to-flagged ratio.

5. YOUR AGREEMENT IS NOT PROOF. You share a rulebook, which is exactly what makes
   you fail identically. Where you confidently agree, nobody is looking.

═══════════════════════════════════════════════════════════════════════════
BLOCK 1 — FRAMEWORK CREATION        both agents · runs once
═══════════════════════════════════════════════════════════════════════════

DO
  Write framework v1 and the matrix spec to
  D:\CRE Decoding System\04 Extractions\framework\

  Every rule is a decision procedure with a stable, immutable id. If two careful
  readers could apply it and get different answers, it isn't a rule yet. No
  "consider whether", "generally", "typically", "use judgment".

  Cover at minimum: the event record and everything it packages; the eleven
  function boundaries; how one instrument splits into several events; date
  precedence and basis; party roles and direction; quantities and when allocation
  is not derivable; terms per instrument type; BBL attribution; the four nulls;
  what to do when the document is ambiguous; and what may never be inferred.

  Then choose the first document id. Query the db yourselves. Pick something that
  will strain the rules, not something clean.

OUTPUT
  framework v1 · matrix spec · the first document id · which rule you expect it to
  break

THEN → 2A and 2B

═══════════════════════════════════════════════════════════════════════════
BLOCK 2A / 2B — INDEPENDENT EXTRACTION     one agent each · parallel · isolated
═══════════════════════════════════════════════════════════════════════════

2A is agent A alone. 2B is agent B alone. Same document, same framework version,
no contact.

INPUT
  the document id · the registration on its row · the document · the current
  framework and matrix spec. Nothing else. No other documents, no prior state of
  the parcel, no outside lookups, no urls.

DO
  Extract the document into its event table, following the framework.

  You may use knowledge of New York real estate to READ the document — never to
  supply a value it does not contain.

  FOLLOW THE FRAMEWORK EXACTLY, INCLUDING WHERE IT IS WRONG. If it produces
  something you believe is incorrect, produce it anyway and record the objection.
  Silently fixing the framework's mistakes hides the defect, and the defect is what
  this workflow exists to find.

OUTPUT → D:\CRE Decoding System\04 Extractions\rounds\<N>\<A or B>\
  extraction.json   the event table
  resolved.md       that table pushed through the matrix spec
  objections.md     where the framework made you emit something you think is wrong
  notes.md          written BEFORE you finish: where the framework was silent or
                    had to be stretched; every decision where you could defend a
                    different answer; where you think you are wrong, argued as a
                    hostile reviewer holding the document would. Write it while you
                    cannot yet know whether it makes you look worse than the other
                    agent — that is the point of writing it then.

FINISH BY posting exactly "A DONE" or "B DONE". Not a summary, not a headline, not
how many events you found. Then wait.

THEN → 3, once both are done

═══════════════════════════════════════════════════════════════════════════
BLOCK 3 — REVIEW · VERIFY · ITERATE        both agents
═══════════════════════════════════════════════════════════════════════════

Neither table may be edited from here. Corrections happen in the open, with reasons.

REVIEW
  a. Compare the RESOLVED MATRICES first, cell by cell. Then the event tables.
     Differences that vanish at the matrix are cosmetic — log them, write no rule.
  b. Exchange notes.md and objections.md before arguing. Where you both
     independently flagged the same gap is the most valuable finding in the round.
  c. Resolve each remaining difference against the DOCUMENT, not by deferring to
     each other. Whoever's citation actually supports their value wins. If neither
     citation supports either value, you were both wrong — that outranks everything
     else in the round.

VERIFY
  d. Now check what you AGREED on, because that is where nobody is looking. Hand
     the document and both tables to a fresh context WITHOUT the framework and ask
     what you both missed. Then to another fresh context WITH the framework and ask
     which of your agreements came from a rule rather than from the document, and
     whether the document actually supports that rule's output there.

ITERATE
  e. Revise the framework. Every change must generalize beyond this document, be an
     executable decision procedure, carry a stable rule id, and freeze a test case
     with the document id and the agreed answer. No rule that only fires for the
     document that prompted it. Bump the version.
  f. Re-run every frozen test case against the new version in a fresh context, with
     the agreed answers withheld — otherwise you are testing memory, not the
     framework. A case that now fails means the change broke something: fix the
     change, don't retire the case.
  g. Log the round: id, versions in and out, what differed, what changed, and your
     emitted-to-flagged ratio. A ratio drifting toward flagging means the framework
     is buying agreement by declining to extract — say so when you see it.

OUTPUT
  the new framework version · the round log · THE NEXT DOCUMENT ID

  Pick it to strain a rule you have not tested. Never one you expect to agree on —
  a round with no disagreement has cost you a document and taught you nothing.

THEN → 2A and 2B with the new id, under the improved framework.

EXIT — do not loop past this
  Stop when five consecutive documents produce no material disagreement under one
  frozen version, every frozen test case passes, and a fresh context given only the
  framework and matrix spec extracts a document it has never seen to the same
  matrix you do.

  Declaring that early does not cost a failed test. It costs 25 million documents
  extracted under a framework that only looked finished.

BEGIN WITH BLOCK 1.
```
