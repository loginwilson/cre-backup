# DRAFT NOTES — A, written before seeing B's draft

Where I am least confident, which rules I expect to break first, and which of my
own decisions I could argue the other way. Written now because now is the only
moment it is honest: I cannot yet know which of these B also found, which makes
me look careless, or which I would quietly drop after reading a better draft.

---

## 1 · THE DECISIONS I COULD ARGUE THE OTHER WAY

### 1.1 R-FN-3 — a secured obligation fires both ENCUMBRANCE and CAPITAL

**This is my most arguable structural choice and the one I most expect to lose.**
It doubles the event count on the largest class of documents in the corpus:
mortgages, assignments and satisfactions are 630 of my 2,373 sampled rows, and
every one of them now emits two events where one would carry the same facts.

The case against, which I find genuinely strong: for an assignment of mortgage,
the ENCUMBRANCE and CAPITAL events differ only in which slots are populated —
same mode, same date, same parcels, same parties. That is not two events, it is
one event serialised twice, and TRAYCER's third "won't occur to you" is about
exactly this kind of bloat.

Why I did it anyway: I tried the alternative — one event, function chosen by a
priority test, money in the event's own quantity/terms slots — and the CAPITAL
column then never records a payoff. A mortgage originates in the CAPITAL column
in 2002 and is never closed there, because the satisfaction was filed under
ENCUMBRANCE. A debt column that opens positions and never closes them is worse
than an empty one, because it looks complete.

I also tried and rejected: reserving CAPITAL for non-lien capital structure
(equity, ground rent, mezzanine). In a recording-office corpus that leaves
CAPITAL empty for almost every parcel, and a column that never fills is a design
error I would rather find now than in round nine.

**What would change my mind:** a demonstration that the ENCUMBRANCE cell can
carry the debt's close without carrying its terms, so CAPITAL fires only on
origination and modification. I could not construct one that stayed mechanical.
If B has, I should take it.

### 1.2 COST versus VALUE

I ruled consideration → COST, assessed value → VALUE, on the principle that COST
is money that moved and VALUE is worth asserted apart from a payment. The
opposite reading is respectable: an arm's-length sale price is the single best
evidence of value in the whole corpus, and a VALUE column that holds only
assessed values — which in this corpus are a small fraction of market — is a
column of systematically wrong numbers.

I kept my split because it is decidable from the document without knowing
whether a sale was arm's length. But I am aware that I chose the rule that is
easy to apply over the rule that produces the more useful column, and that is
not obviously the right trade.

### 1.3 M-AUTHORITY emits zero events

Powers of attorney are 54 of 2,373 sampled rows — call it 2% of the corpus,
which at 25M documents is 500,000 documents that produce nothing. I believe this
is right: authority is not one of the eleven functions, and inventing an IDENTITY
or TITLE event for a POA would be exactly the plausible interpolation TRAYCER
warns about. But "this document type produces no output" is the kind of rule
that looks like a bug for years, and if B emits anything at all here we will
have a large, clean disagreement on our hands. **I would rather lose this one
than be quietly right about it.**

### 1.4 R-FN-2 — IDENTITY does not fire on routine descriptions

Every instrument describes its premises. If IDENTITY fired on all of them it
would be a column of noise, so I suppressed it behind a four-case trigger. The
risk is that my four cases are not exhaustive, and a lot-line adjustment or a
partial conveyance whose language I did not anticipate silently produces
NO_CHANGE in the one column that should have caught it. A missing IDENTITY event
is invisible: nothing downstream will ever ask why the lot did not change.

This is the rule where I would most want a hostile reader.

### 1.5 M-DEED's consideration ladder reaches into the registration

Step (c) of `consideration_resolved` falls back to `registration.amount`, which
is presenter-supplied index data, to resolve a value the instrument itself
states as $10.00. I have defended this as a documented derivation with named
inputs, which the framework permits. It is still a rule that lets an index field
override the instrument on the instrument's own subject, and R-INP-8 says the
body controls the legal act. **These two rules are in tension and I did not
resolve it; I scoped my way around it by calling consideration an indexing
attribute in one place and a legal-act attribute in another.** That is a real
inconsistency in my draft and I would rather name it than have it found.

### 1.6 The RP-5217 date as the deed's effective date

M-DEED treats RP-5217 field 11 "Date of Sale/Transfer" as a `STATED_EFFECTIVE`
candidate for the TITLE transfer. The RP-5217 is a separate sworn form, not the
deed, and using its date as the deed's operative date is a stretch. On the one
deed I read the two agree exactly (both 2002-11-22), which is precisely the
condition under which a wrong rule looks right. **I have no evidence for this
rule; I have one non-falsifying observation.**

### 1.7 ENVELOPE includes "stated dimensional limits on building position"

I added this so a 60-foot clear-distance declaration would fire ENVELOPE rather
than vanish. But metes and bounds also state dimensions, and the line I drew —
boundary dimensions describe the lot, position limits constrain the building —
is a distinction I could read the other way on a different day, and so could
anyone. If it goes wrong it goes wrong in the direction of firing ENVELOPE on
every deed with a Schedule A, which would be a large, obvious failure. That is
at least a failure mode I would notice.

---

## 2 · THE RULES I EXPECT TO BREAK FIRST

Ordered by how soon I expect them to fail.

1. **R-SPLIT-4 (merge).** "Payloads that do not state conflicting values for the
   same key" has a soft edge, and I wrote it after telling everyone that soft
   edges are defects. Two readers will merge different sets. This is the single
   biggest source of event-count divergence I expect between A and B, and it is
   my fault, not the document's.

2. **R-FN-1 (the function test) on a dense instrument.** On a five-page deed it
   is well behaved. On a thirty-page declaration with sixty numbered paragraphs I
   expect over-emission, and R-SPLIT-4 is the only thing standing between that
   and an unreadable matrix — see (1).

3. **M-GENERIC.** "Read the instrument's own title and apply R-FN-1 with no
   type-specific expectations" is not a decision procedure, it is an
   encouragement. `AGREEMENT`, `SUNDRY AGREEMENT`, `MISCELLANEOUS` and Richmond's
   untyped rows are a large fraction of the corpus and they all land here.

4. **R-DATE-1's STATED_EFFECTIVE definition.** I wrote "'made this __ day of __'
   when the making *is* the act", which asks the reader to decide when making is
   acting. On almost every document the effective and execution dates coincide,
   so the ambiguity will stay hidden until it matters — and then it will matter a
   lot, because it is the date field.

5. **R-INP-4 (exhibit incorporation).** Requires a label match. An unlabeled
   annexed page, or one whose label was cropped by the scanner, is classed ADMIN
   and its content is lost silently. I have not seen this happen; I expect it
   does.

6. **R-AMB-2(b).** Allowing a flag when characters admit two readings is right,
   but it makes "I could not read it" and "the document is ambiguous" the same
   category, and the anti-flagging discipline depends on those being different.
   I expect the flagged ratio to be dominated by bad scans rather than by
   genuinely ambiguous documents, especially on `FT_` and `BK_` film.

---

## 3 · WHERE I KNOW THE DRAFT IS THIN

- **M-LEASE was written without reading a lease.** I built the package for
  `2003010600065003` and did not open it. It is the weakest module and should be
  treated as unvalidated.
- **No worked example exists for a multi-parcel document.** The matrix spec's
  §10 example is a single-parcel deed. §11 describes the multi-parcel case in
  prose without showing it, which is exactly the kind of gap that produces two
  differently-drawn tables.
- **`resolved.md`'s eleven-column markdown is unreadable at real cell widths.**
  I know this and shipped it anyway because the canonical block (M-CANON-1) is
  the artefact that gets compared. But a human reviewing the round will look at
  the table, and if it is unreadable the review degrades to reading the canonical
  block, which is not designed for humans.
- **The `at` zone vocabulary is deliberately coarse** so two readers cannot
  disagree about a locator. The cost is that `p03/MIDDLE` on a dense page does
  not actually help a verifier find the quote. I traded verifiability for
  agreement, which is the wrong direction for a framework whose whole purpose is
  to be checked.
- **I asserted a 25-word cap on quotes without testing it** against a metes and
  bounds, a habendum, or a long condition. Some values may not be quotable
  within it, and the rule offers no escape hatch.
- **Nothing in the framework has been executed.** Every rule in it is a
  prediction that it will be followable. I have applied several of them by hand
  while reading, which is not the same as a cold reader applying them.

---

## 4 · WHERE I THINK I AM WRONG, ARGUED HOSTILELY

*A reviewer holding the documents, unimpressed:*

> You defined eleven cell schemas and then claimed the function boundaries are
> "decidable". They are decidable only for clauses that state the kinds of value
> your schemas happen to enumerate. You built the schemas by reading eight
> documents, seven of them from a two-week window in 2002–2003 and one from
> 1981. The corpus spans a century. Your ENVELOPE cell has no slot for anything
> a 1920s covenant would say, and you would not know, because you did not read
> one.

I think this is largely correct. My survey is badly skewed toward ACRIS-digital
2002–2003, because that is where the readable, legible documents are dense. Two
of the ten documents I read as images were pre-1990. If the framework is quietly
tuned to a 2002 refinance closing, the first film-era round will expose it, and I
would rather that happen in round two than in round twelve.

> Your anti-flagging rule is elegant and it is also self-serving. "Two readings
> each with its own quote" is a test you will always be able to pass when you
> want to flag and always be able to fail when you do not. Nothing in it is
> checkable by anyone but you.

Fair. The only real check is the emitted-to-flagged ratio in R-AMB-4, tracked
across rounds — a single extraction's ratio means nothing.

> You wrote a rule (R-NEV-9) forbidding derivation of consideration from a tax
> amount, and the reason you wrote it is that doing so would have resolved your
> one hard case correctly. You have prohibited the method that works because it
> requires knowledge, and permitted a method (R-INP-6a, adopt the reading that
> matches another source) that got the same answer by a route you find more
> comfortable. Those are the same act.

This one lands harder than I would like. The distinction I would defend is that
R-INP-6a uses only values present in the inputs while R-NEV-9 requires a rate
that is nowhere in them — the tax rate would have to come from me. But the
reviewer is right that I reached both times for the answer I already believed,
and that the framework's rules were shaped by which route to it felt licit.

---

## 5 · THE FIRST DOCUMENT

TRAYCER Block 1 asks for the first id and the rule I expect it to break. Both
are proposals for the reconciliation, not decisions — B may have a better one,
and the choice should survive an argument.

**Primary: `2003010500008001`** — MORTGAGE, 2 parties, **13 parcels**,
ACRIS-digital 2003. I have not opened it; I know only what the census row says,
which is the right amount to know when choosing.

Why this one: it hits three of my least-tested rules simultaneously and none of
them by accident. R-QTY-3 (one stated principal across 13 parcels, allocation
not derivable) is the rule TRAYCER singles out and I have never applied it.
R-PARCEL-5 (fan only to parcels the clause affects) has to decide whether the
mortgage covers all 13 or whether the body distinguishes. And R-FN-3 produces
**26 events for one mortgage**, which will make the resolved matrix look absurd
and is the first honest test of whether §1.1 was worth it. It is also
ACRIS-digital and 2003, so it should be legible: a disagreement will be about
rules rather than about eyesight, which is what round one should be measuring.

**Alternate: `FT_1000000033900`** — AGREEMENT over 25 parcels, film era. Strains
M-GENERIC (the module I called an encouragement rather than a procedure),
R-INP-9 (no cover page, no `doc_date`), and R-DATE-3 (recording date as the only
date in the registration). I would take this second, not first, because film
legibility will confound rule disagreement with reading disagreement, and round
one should isolate one of those.

**Not `2003010600117004`**, the consolidation agreement, tempting as it is: I
read a page of it while drafting and would carry prior context B does not have.
For the same reason I would exclude every id in `surveyed.md` §1 from round one.

**The rule I expect it to break:** R-FN-3, and not in the way it fails a test —
in the way it succeeds and is unbearable. Twenty-six events, thirteen matrices,
each CAPITAL cell reading `principal=ALLOC_ND(...)` because R-QTY-3 forbids
dividing the one stated amount. Every rule will have been followed exactly and
the output will be very hard to defend. That is the most useful kind of failure
available in round one, and it is the reason I picked a document that will
produce it rather than one that will pass.
