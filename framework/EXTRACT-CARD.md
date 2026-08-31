# THE EXTRACT CARD — read before filling a row

Short by design, and **capped at twelve**. A thirteenth card displaces one; it never
extends the list. Sibling to `Bootcamp/Compose Card.md`, which fires when writing
prose — this one fires when filling a cell.

**Everything class-specific is in `specs/<CLASS>.md`. Everything mechanical is in
`bin/tablecheck.py`. Neither is your job to remember.**

---

## 1 · A CITATION CARRIES GEOMETRY, NOT JUST CHARACTERS

    p2 · [0.12,0.34,0.71,0.38] · struck · "subject, however, to all assessments"

Page · rect in normalised page coordinates · mark type · the quote, isolated to what
it proves. Mark is one of `plain | struck | inserted | flourish | marginal |
uncertain`.

**A NEGATIVE IS NOT A ROW.** *"I found nothing"* (card 5, state 1) has no text to
quote, because an unfound thing has no words — and it is not an event, because
nothing happened. It is a record of **what the reader did**, and it goes in a
`SEARCH RECORD` block below the table:

    SEARCH RECORD
    | region                         | dpi  | found |
    | p1 · [0.00,0.920,1.00,1.000]   | 1200 | a printed rule at the left, nothing else |
    | p2 · [0.00,0.900,1.00,1.000]   | 1200 | tail of the return-to block, nothing else |

**Different claim, different evidence, different falsification.** A row cites a rect
containing something; a search record cites **coverage and sensitivity** — where you
looked and how closely. "Not there at 300 dpi" and "not there at 900" are different
findings.

> *Three readers reached this independently when the registry lane became
> CITE-checked and their negative rows had no quote. All three removed the row rather
> than manufacture one. One put it exactly right: **"a document with no fee stamp and
> a document nobody looked at produce identical row tables unless the search itself
> is recorded."***
>
> *And writing it as a search record made the claim honest: **"stating it that way
> forced me to actually do the search rather than assert it. My original row was
> backed only by having read both pages whole, which is weaker than the row
> implied."*** A second reader corrected its own earlier claim of *"both margins at
> 900 dpi"* on discovering only one had been.

⚠ **The row form let a weak negative look strong.** That is why it moves out.

**A citation format bounds the class of claims it can support.** Characters support
*which words are on the page* and **nothing about how they are marked** — marks are
not characters, so better OCR never closes it. A quotation of struck words is
byte-identical to a quotation of live words.

**Any row whose meaning depends on a mark must carry a rect.** Without one, write
`mark: uncertain` and drop the claim — do not smuggle it into `terms`.

The rect need not be tight. The test is that **cropping it shows the marked text and
little else**. `docpkg.py --rect` takes the same shape, so record the rect you
zoomed to.

⚠ **Mark *type* is measurable; mark *order* is not.** These scans are bitonal, so
**stroke sequence is unrecoverable** — nobody, including a referee with the images,
can settle *drawn before or after* from them. `struck` is a citable claim;
*struck-before-execution* is permanently `uncertain`.

## 2 · ONE ROW PER OPERATIVE ACT

Not per constraint, not per citation, not per sentence.

One clause with two dollar thresholds is **one row** — one duty, varying by
location; the variation goes in `terms`. Twenty prohibited trades in one covenant is
**one row** — one prohibition; the list goes in `terms`.

> *Five readers obeying the framework exactly produced 16 / 26 / 27 / 27 / 29 rows
> on identical readings. Treat row-count deltas as splitting artifacts until proven
> otherwise.*

## 3 · `STRUCK` IS A MODE, AND NOT EVERY STRIKE EARNS A ROW

The instrument **considered this clause and removed it.** Not `TERMINATE` (which
reads downstream as *a burden was released* — false), not `MODIFY` (which says the
world changed when only the form did), not an asserted absence.

⚠ **`STRUCK` claims the mark, not the moment.** An earlier wording defined it as
removal *"before execution"* — which card 1 says is permanently unrecoverable from
these scans. **The mode's own definition asserted what the card set forbids
claiming.** Three readers reported the contradiction; all used the mode anyway,
because it is plainly right, and said so in `terms`. If timing matters to a consumer,
it is `uncertain`.

**A strike earns a row when the struck text, if left standing, would have changed
what the instrument does.** Otherwise it goes in `terms`.

## 4 · NEVER WRITE A VALUE YOU CANNOT POINT AT

If the document does not state it, the answer is `UNKNOWN` **plus the reason**. Never
infer from position, convention, or an adjacent label.

> *A stamp reading `16.00` with no label is not a fee. Two grantees with no stated
> shares are not 50/50 — and 50/50 would have looked exactly like a measurement.*

## 5 · THREE STATES OF ABSENCE, AND THEY ARE DIFFERENT CLAIMS

    I FOUND NOTHING            you looked and did not see it
    THE DOCUMENT ASSERTS NONE  "free from incumbrances" — a real asserted absence
    THE DOCUMENT DECLINES      "filed OR INTENDED TO BE FILED" — it asserts a date
                               and a number while refusing to confirm the act

Write the one you actually have. The third resolves to neither of the first two.

## 6 · READ THE MARKS — AND BEWARE THE INVERSE

Corrections, strikes, insertions and marginal notes are operative. A struck digit
over a typed one is the real value. Follow an insertion line to where it points, not
to the nearest similar name.

⚠ **Copperplate lead-in flourishes read as strikes at page zoom**, especially where
you expect strikes.

> *The orchestrator read two flourishes as cancellations and wrote it down as fact;
> five readers disagreed unanimously, and a measurement settled it — genuine
> cancellations spanned 76.3 / 76.4 / 53.8 % of region width, the disputed mark
> 12.3 %, flat at every slope. **A measurement ends a dispute that readings only
> vote on.** Zoom before you argue.*

## 7 · READ EVERY PAGE, WHATEVER SHAPE IT IS

Rotated, sideways, partial strips, endorsement backs. The page you cannot read
easily is often the one carrying the fee, the return-to party, and the parcel
identification.

## 8 · PAGE COUNTS DISAGREE, AND THAT IS NOT AN ERROR

Registries count cover pages; instruments do not; schedules carry numbering from
other documents. Report every count. Reconcile none. **Never use one as a
completeness test.**

## 9 · CHECK THE INDEX. TRUST NEITHER SIDE. CORRECT NOTHING.

Record where document and registry disagree and leave both standing. Where the index
has no field to check against, write `NOT_CHECKABLE` — that is not agreement.

**rd never upgrades unread → read.** When the document-side reading is too weak to
confirm, write *"accepted — rd sole witness"*.

## 10 · THE EVENT DATE IS WHEN IT HAPPENED

Say which date you used: effective, instrument, execution, acknowledgment, or
`UNSUPPORTED`. **Recording date is never the event date** — it belongs to the
registry lane. When several candidates coincide, **say so** rather than reporting a
basis you did not have to choose.

## 11 · VERIFY AGAINST THE ARTIFACT, NEVER AGAINST THE BRIEF

If anyone — including the orchestrator — tells you a fact about the document, the
checker, or another reader's table, **go look at the thing itself.**

> *A reader working from a summary replicates that summary's errors instead of
> reading the page, and five independent readings quietly become five readings of
> one brief. The orchestrator was wrong three times in one session; every catch came
> from someone who went to the source.*

## 12 · "I CANNOT TELL" IS A VALID ANSWER

And it is worth more than a confident guess. Agreement earns no credit; disagreement
is investigated.

---

**Card 12 is the last slot.** A new finding that is not class-specific and not
mechanizable must displace a card here, and the displacement must be argued.
