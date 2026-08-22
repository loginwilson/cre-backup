# How this scales — pull, parallelise, populate, release

**Login, 2026-08-06:** *"This is how we scale. You pull docs, we parallelise to
decode and populate our decoded ACRIS ledger with function grouping, then delete
imagery and move on. Remember to always return if we find a failure in our logic
to maintain accuracy. Maybe since it's chronological, parallel isn't good — you
want to move oldest to newest. However, you could parallelise multiple lots at
once."*

---

## 1 · The chronology constraint is real, but it binds ONE STAGE

Splitting the work into three stages shows exactly where order matters:

| stage | what it does | order |
|---|---|---|
| **EXTRACT** | per document: pull verbatim clauses and stated figures, with page cites | **PARALLEL — any order** |
| **DERIVE** | running balances, differenced quantities, supersessions, contradictions | **SEQUENTIAL, oldest → newest** |
| **GROUP** | tag by function and render the views | order-independent (a query) |

**EXTRACT does not need chronology.** Reading "the chart states 232,813 sf" from
the 2012 Horne ZLDA requires no knowledge of 2010. Four agents are reading four
documents from four different years right now and none of them needs the others.

**DERIVE absolutely does, and this parcel proves it.** The Horne quantity —
22,845 sf, the single most valuable number on the block — **is stated nowhere.**
It exists only as 232,813 minus 209,968, the difference between two charts two
years apart. Extract them in either order; you can only subtract them in one.

The same applies to the envelope ledger's running balance, the debt position
rolling forward from 1990, and every `SUPERSEDES` and `CONTRADICTS` edge.

**So: fan out on extraction, fold in on derivation.** The expensive part —
reading images — is the parallel part. The cheap part — arithmetic over
extracted atoms — is the ordered part.

## 2 · Across lots, parallel is not just safe, it COMPOUNDS

Different lots are independent at extraction, and the mirroring makes the
returns superlinear: a ZLDA naming eight lots is read once and satisfies eight
parcels. Measured on Block 800 — lot 49's 96 documents also appear in the
indexes of eight neighbours, 160 of 523 documents shared.

⚠ **But run a BLOCK together, not a scattered sample.** Decoding lots 49, 53 and
22 in the same pass means one reading of the 2010 ZLDA serves all three, and the
mirror check (every transfer nets to zero across its two lots) has both sides
present to verify against. Decoding lot 49 in January and lot 53 in June means
reading the same document twice and losing the cross-check.

## 3 · ⚠ THE DELETION HAZARD — do not release imagery on a first pass

This is the one place the proposed loop can quietly destroy accuracy, and it is
worth stating flatly:

> **Every correction made today came from RE-READING a document that had already
> been decoded.**

* the 2010 easement was decoded from the chart at p038. Reading the covenant at
  **p008** three steps later produced THREE corrections — "light and air" was
  really *light, air and view*; the band ran from the **rear lot line**, not the
  line shared with lot 49; and it was granted by **lot 53 alone**, not by lots
  53, 55 and 56 as recorded. That last one was **invented data on two innocent
  parcels.**
* `store.py` exists because eight parser bugs were fixed in one session and every
  document read before each fix stayed mis-read, with the fetch ledger
  forbidding a re-fetch.

If imagery is released after the first pass, the record is frozen at whatever
was understood on the day — including the parts that were wrong.

**THE RULE:** release imagery only when a document passes the completeness bar:

1. every slot in its doc-type menu is **PRESENT or ABSENT** — zero `NOT_LOOKED`
2. every extracted term carries page + verbatim
3. every stated figure is reconciled against its own document's arithmetic
4. the document's claims raise no unresolved `CONTRADICTS` edge

Until then it is **HOLD**. A document at 76% examined is not finished, and
"we already decoded it" is precisely the belief that makes the loss invisible.

**Cheaper alternative worth costing:** keep the images and release only the
highest-resolution copies, or re-derive from a compressed archival copy. The
corpus is ~14 TB citywide; a lot's imagery is tens of MB. The storage is not
what makes this hard.

## 4 · Returning on a failure must be MECHANICAL, not remembered

*"Always return if we find a failure in our logic to maintain accuracy."*

Agreed — and a promise to remember is not a mechanism. Today's corrections were
caught by four checks that fire without being asked:

| check | what it caught |
|---|---|
| mirror nets to zero | the subdivision moving 55,915 instead of 127,035 |
| balance transcribed, not computed | the same error, from the other side |
| predicate KIND validation | a dollar amount stored inside an IDENTIFIER |
| function view rendering both | a stale claim contradicting its own correction |

**When a new trap is found, it becomes a check, and the check is re-run over
everything already decoded.** That last clause is the one that matters: a lesson
learned on document 400 must be applied backwards to documents 1–399, because
they were decoded under the older, wronger rules. Prior work looks cleanest
exactly where it is most likely to be wrong.

## 4b · ⚠ THE BEST PATTERN: one lot deep, then agents at the NAMED GAPS

**Login, 2026-08-06:** *"Or you could do one lot and set agents to find missing
information when you know what is missing."*

**This is the strongest of the three, and it is what actually happened today.**
The four agents now running were not sent to "read some documents". They were
sent at gaps the sequential pass had already NAMED:

| gap | how it was found |
|---|---|
| where lot 22's height plane landed after the split | the envelope narrative put the 2013 easement and the 2019 split in one column |
| the lot 20 airspace price | the ledger's `price_basis` said OFF_PARCEL and refused to fabricate a $/sf |
| lot 21's generated and retained columns | the allocation chart left them NULL rather than back-computing |
| the lot 20 CRFN conflict (2008 vs 2013) | two documents cited different CRFNs for the same instrument |

### Why gap-directed beats fan-out

**A precise question has a checkable answer. "Read this and tell me what's in it"
does not.** An agent asked to summarise returns confident, well-formatted prose
that cannot be verified without redoing the work — which is worse than no decode,
because it looks finished. An agent asked *"which lot holds the benefit of the
lot 22 easement after the subdivision — cite page and quote"* returns something
that is either right, wrong, or an explicit "the document is silent", and all
three are useful.

### The dependency this creates

**Pattern 3 requires pattern 2 to have run first.** You cannot dispatch agents at
gaps until a sequential pass has produced gaps worth naming. The slow walk
through one lot is not overhead before the real work — **it is what makes the
parallel work verifiable.**

### The gap register IS the work queue, and it already exists

No new machinery is needed. Four tables already emit the questions:

* `acris_extraction` — every `NOT_LOOKED` value/terms status per document
* `doctype_term_instance` — every menu slot still `NOT_LOOKED` on an instance
* `acris_claims` where `predicate = 'unresolved'` — questions the documents raised
* `acris_claim_edges` where `relation = 'CONTRADICTS'` — disagreements to settle

⚠ **A gap is only dispatchable once it is SPECIFIC.** "The Horne body is unread"
is a task. "Terms coverage is 3%" is a statistic. The register must hold the
former.

## 5 · The loop, stated

```
FIRST LOT ON A BLOCK — sequential, deep, slow. It produces the gap register
and the doc-type menus that make everything after it fast.

THEREAFTER, per BLOCK:
  1  PULL      every document in the index for every lot on the block
  2  EXTRACT   parallel agents, one per document, contract enforced:
                 verbatim mandatory · page cite mandatory
                 never carry a value from a sibling document
                 PRESENT / ABSENT / NOT_LOOKED, never two states
  3  VERIFY    agent output is a CLAIM TO CHECK, not a fact to accept
  4  DERIVE    single-threaded, oldest -> newest, per lot, mirrored across lots
  5  CHECK     run every invariant; a failure returns to step 2 and to the
               back catalogue
  6  GROUP     tag atoms by function; render ledger + function views
  6b GAP-FILL  dispatch agents at NAMED gaps from the register — never at
               "read this document and tell me what it says"
  7  RELEASE   imagery only for documents that pass the completeness bar
```

⚠ Step 3 is not optional. A parallel agent under-instructed produces
confident, well-formatted, unverifiable prose — which is more expensive than no
decode at all, because it looks finished.
