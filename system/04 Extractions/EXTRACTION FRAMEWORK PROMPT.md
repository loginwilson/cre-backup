# Extraction Framework — Traycer prompt

Fill in the target model and six starting doc ids. Paste the block.

---

```
You are two agents — A (Claude Code) and B (Codex). Peers. Neither defers.

Build the extraction framework for NYC C.R.E.D.: the rulebook that turns any
document in the Legal Instruments DB into its event table.

HOW YOU BUILD IT
Agree a framework. Pick a doc id. Extract it INDEPENDENTLY of each other. Meet back
up, compare, argue, find where the framework let you diverge. Revise it. Pick a new
id. Repeat.

The framework is the deliverable — the extractions are not. Every document you
process exists only to expose where the rules are underspecified.

You are done when a model that has never seen this conversation reads the framework
and extracts the same way you do. Production runs on an open-weight model, so the
rules cannot lean on the reader being clever: where rules are silent, a capable
model interpolates plausibly, and plausible interpolation is indistinguishable from
fact everywhere downstream. Remove the occasions to interpolate.

WHAT EXTRACTION HAS TO DO

A document is not a fact. It is a record of things that happened. Read each one
independently — no other documents, no prior state of the parcel, no outside
lookups — and distill it into events. Events fan to the BBLs they affect, sort by
when the thing HAPPENED, and resolve into a state matrix: time down, function
across, each cell the state of one function at one moment.

Eleven functions, fixed:
  Identity · Title · Entitlement · Envelope · Encumbrance · Capital
  Permit · As Built · Occupancy · Cost · Value

Their boundaries are not fixed, and that is where errors live. Is a restrictive
declaration Encumbrance, Envelope, or both? Settle it with a procedure, not a
description.

Tagging function and date is the floor, not the job. The work is PACKAGING each
event: its mode (create / modify / transfer / terminate / assert / correct — a
mortgage origination and a satisfaction are the same function and opposite in
effect); its parties and their roles and shares, many per side or none; whether it
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
inside the id itself. Three different dates before you open anything, and none of
them is necessarily the event date. Paths, folders, filenames, urls and pipeline
metadata are never citable — and note "at" is the crawler's timestamp sitting
inside the registration JSON, so citability is decided field by field, not blob by
blob.

EVERY FIELD YOU EMIT CARRIES EITHER A VERBATIM QUOTE AND ITS LOCATION, OR THE
FRAMEWORK RULE THAT DERIVED IT AND THE INPUTS IT USED. A field with neither is a
defect whether or not the value is right. This is the only mechanical guarantee
that the framework, rather than your own knowledge of New York real estate, is
doing the work.

FIVE THINGS THE LOOP WON'T TEACH YOU

Everything else you can work out as you go. These five you cannot, because in each
one the natural move is the wrong one.

1. WORK BLIND. Write only to your own directory. Do not read, list or open anything
   of the other's until you have BOTH finished and posted a hash. You will want to
   collaborate; that instinct destroys the only evidence this method produces. One
   glimpsed intermediate result voids the round — drop the document and start over.

2. DEFINE HOW EVENTS BECOME THE MATRIX, before the first extraction. How events fan
   to BBLs, sort, tie-break, fold into a cell, serialize. "We got the same result"
   means nothing until this exists, and you will otherwise burn rounds arguing about
   differences that are only in how you each drew the table.

3. IF A DIFFERENCE DOESN'T CHANGE THE MATRIX, DON'T WRITE A RULE FOR IT. Log it and
   move on. Legislating every discrepancy produces a rulebook too bloated for any
   other model to apply — which fails the goal without ever looking like failure.

4. DON'T BUY AGREEMENT BY FLAGGING. A framework that marks everything uncertain has
   no disagreements, passes every check, and extracts nothing. Every individual
   choice to flag will feel defensible. Flag when the DOCUMENT is ambiguous, never
   when the RULE is hard to write, and track your emitted-to-flagged ratio.

5. YOUR AGREEMENT IS NOT PROOF. You share a rulebook, which is exactly what makes
   you fail identically. Where you confidently agree, nobody is looking. Each round,
   hand the document and both tables to a fresh context WITHOUT the framework and
   ask what you both missed — then to another fresh context WITH the framework and
   ask which of your agreements came from a rule rather than from the document.

START

Draft the framework and the matrix spec independently, in your own directories,
before comparing. Where your two drafts disagree is the most useful map you will
get all project.

Every rule is a decision procedure with a stable id. If two careful readers could
apply it and get different answers, it isn't a rule yet.

Then pick the first id and go.

TARGET MODEL: <MODEL>
STARTING IDS: <SIX IDS, pdf LIKE '%.pdf', mixed instrument types>
```
