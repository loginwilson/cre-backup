# Extraction framework v4

Replaces v3. Every rule here exists because a named document forced it. **A rule
with no document behind it does not belong in this file.**

**This file is the whole of what you are given.** Version history, prior rulings,
other readers' findings and retired frameworks are held by the judge and are
deliberately not in your workspace — an extractor needs the rules, not the story of
how they arrived, and least of all the answers a previous round reached.

**Cap: 20 KB.** Past that, something here is answering a question no document asked.
That is how v2 reached 129 KB.

## The job

Select a document. Read it **page by page**. On each page ask, of every one of the
eleven functions: *does anything on this page do something?* Every hit becomes a
row. Then write a short brief.

Readers work independently, with no contact, until every table is sealed. Then they
meet, read each other's **tables**, and propose changes to this file.

## The eleven functions

Ask all eleven on every page. Not the ones the document type suggests.

A function is **a kind of question about a parcel**. Together they are meant to
cover everything a recorded instrument can do. If something on the page fits none
of them, that is a finding — write it down under an explicit heading **in your own
folder**, rather than forcing it, and say what would be lost by filing it under the
nearest function.

**You are not shown the candidates other readers have raised.** A list of things to
look for is a list of things you will find. The judge collects them; a candidate
becomes a function only when a third document forces it.

| function | the question it asks | fires on |
| --- | --- | --- |
| **IDENTITY** | *who or what is this, and is it the same as that?* | aliases, "also known as", name changes, mergers, successors, the capacity a person signs in |
| **TITLE** | *who owns which estate in the land?* | grants, conveyances, reservations, life estates, remainders, condominium units, undivided interests |
| **ENTITLEMENT** | *what development rights attach to the land?* | zoning, floor area, air rights, transferable development rights, as-of-right permissions |
| **ENVELOPE** | *what physical form may a building take here?* | setbacks, height, bulk, lot coverage, yard requirements, wall and facade openings |
| **ENCUMBRANCE** | *what burdens run with the land?* | liens, easements, covenants, restrictions, subordinations, the mortgage **as a burden on title** |
| **CAPITAL** | *what is owed, by whom, on what terms?* | principal, notes, interest, advances — the **debt itself**, as distinct from the lien securing it |
| **PERMIT** | *what has government authorised, or been asked to authorise?* | building permits, certificates of occupancy, BSA and CPC approvals, applications filed |
| **AS_BUILT** | *what physically exists?* | dimensions, storeys, materials, party walls, area, improvements actually present |
| **OCCUPANCY** | *who may use the space, and how?* | number of families, residential vs commercial use, leases, tenancy, prohibited trades |
| **COST** | *what money moves for process, or must be spent?* | taxes, recording and filing fees, and duties to spend — *"shall cost not less than $2,000"* |
| **VALUE** | *what is it worth, or what was exchanged for it?* | consideration, sale price, appraised or assessed value |

### The boundaries that actually get confused

**CAPITAL vs ENCUMBRANCE.** A mortgage is both, and they are separate rows. The
promise to repay $384,900 is `CAPITAL`. The lien burdening the lot until it is
repaid is `ENCUMBRANCE`. Subordinating that lien changes the `ENCUMBRANCE` and
leaves the `CAPITAL` untouched.

> *`RC_300106`: a subordination moves a lien's priority and alters no debt.*

**COST vs VALUE.** `VALUE` is what the thing is worth or what was exchanged for it.
`COST` is money spent on process, or a duty to spend. A $100 consideration is
`VALUE`; a $2.50 recording fee is `COST`; *"shall cost not less than $2,000"* is a
`COST` obligation even though no money has moved.

**ENVELOPE vs AS_BUILT vs OCCUPANCY.** `AS_BUILT` is what **is** — a party wall
exists, the building stands two storeys. `ENVELOPE` is what **may be built** — no
flat roof, nothing within 15 feet of the avenue. `OCCUPANCY` is who may **use** it —
not more than two families, no trade or business, no liquor.

> *`RC_1598772`: the 1911 covenants are ENVELOPE and OCCUPANCY, never AS_BUILT —
> the house had not been built yet.*

**TITLE vs ENCUMBRANCE.** `TITLE` is who holds the estate. `ENCUMBRANCE` is what
rides on it. A deed conveying a lot subject to restrictions produces one of each.

**ENTITLEMENT vs PERMIT.** `ENTITLEMENT` is a right attaching to the land that
survives its owner. `PERMIT` is a government act, or an application, about a
specific project. **`PERMIT` is government only.** A private party holding a
discretionary approval right is not a `PERMIT`; if you find one, say what filing it
elsewhere loses.

### When two functions both fit

Emit the row under the function whose **question the clause actually answers**, and
note in `terms` that it also bears on the other. Do not emit one act twice under two
labels — but **do** emit separate rows when the document genuinely does two things
in one sentence, as a mortgage does.

> *Proved by `2002122700120002`: a mortgage's only structural fact about the
> building — a party wall — was inside a surveyor's third boundary course. And by
> `FT_1000000027200`: a Declaration's express statement of fee ownership was found
> only because a Title question was asked of a document nobody would ask it of.*

## The table

| column | holds |
| --- | --- |
| `#` | E1, E2, … in page order |
| `citation` | page · rect · mark · quote — see below |
| `time` | the date **and which date it is** |
| `until` | when it stops, or blank if it does not |
| `function` | one of the eleven |
| `mode` | `ASSERT` · `TRANSFER` · `CREATE` · `MODIFY` · `TERMINATE` · `STRUCK` |
| `where` | scope marker + BBL — see below |
| `parties` | `from → to`, or a labelled relation — see below |
| `quantity` | number + unit, or `UNKNOWN` with the reason |
| `terms` | the operative conditions |
| `summary` | one line, plain English |

Above every table, a labelled date block. `UNKNOWN` where the document does not say:

```
instrument:    1911-04-24
acknowledged:  1911-04-24
recorded:      1911-04-25
expires:       1915-01-01
```

Then a brief: six to ten lines, no new facts, everything traceable to a row.

## The rules

### 1. A citation carries geometry, not just characters

`p2 · [0.12,0.34,0.71,0.38] · struck · "subject, however, to all assessments"`

Page · rect in normalised page coordinates (`x0,y0,x1,y1`, origin top-left) · mark
type · the quote, isolated to the thing it proves.

Mark type is one of `plain | struck | inserted | flourish | marginal | uncertain`.

**Why this is rule 1.** The evidence for a struck clause is *a line drawn through
text*. A quotation of struck words is byte-identical to a quotation of live words,
so a `STRUCK` row cited by characters alone is a claim **nothing downstream can
falsify**. A citation format bounds the class of claims it can support: characters
support *which words are on the page* and, in principle, **nothing about how they
are marked.** Marks are not characters, so no amount of better OCR closes this.

The rect need not be tight. The test is that **cropping it shows the marked text and
little else** — that is what makes the claim checkable by someone who was not there.

> *`RC_1598772`: whether two lot numbers were struck decided whether the deed
> conveyed two lots or none. The entire finding rested on the shape of a stroke, and
> the citation column carried only characters.*

**A row whose meaning depends on a mark — any `STRUCK` row, any hand correction,
any insertion — must carry a rect.** Without one, write `mark: uncertain` and drop
the mark-dependent claim; do not assert it in `terms`.

**Mark *type* is measurable. Mark *order* is not.** These scans are bitonal, so
stroke sequence is unrecoverable — nobody can settle *drawn before or after* from
these images. `struck` is a citable claim; *struck-before-execution* is permanently
`uncertain` here.

> *`RC_1598772`: every horizontal ink run ≥110 px on page 1 returned exactly one —
> the real cancellation. Shear-corrected span put genuine cancellations at 76.3 /
> 76.4 / 53.8 % of region width and the disputed mark at 12.3 %, flat at every
> slope. A measurement ended a dispute four readings had only voted on.*

### 2. `STRUCK` is a mode, and not every strike earns a row

The instrument **considered this and removed it before execution.** That is not
`TERMINATE` — which reads downstream as *a burden was released*, and is false. It is
not `MODIFY` — which says the world changed when only the form did. It is not an
asserted absence under rule 9.

**A strike earns a row when the struck text, if left standing, would have changed
what the instrument does.** Otherwise it belongs in `terms`.

> *`RC_1598772`: three printed clauses ruled out in ink. All five readers found no
> mode fit and buried the fact in `terms`, where nothing indexing by function will
> ever find it. The test above yields one row here, not three.*

### 3. One row per operative act — not per constraint, not per citation

This is the largest single source of noise in the council's input: two readers
obeying the framework exactly differed by a **factor of two** on row count while
agreeing about everything.

Two worked cases from `RC_1598772`:

- one clause with **two dollar thresholds** ($2,000 and $3,000, by street) is **one
  row** — one duty to spend, varying by location. The variation goes in `terms`.
- **twenty prohibited trades** in one covenant is **one row** — one prohibition. The
  list goes in `terms`.

> *`RC_1598772`: counts ran 16 / 26 / 27 / 27 / 29 on identical readings. Treat
> row-count deltas as splitting artifacts until proven otherwise.*

### 4. The event date is when it happened — and the registry gets its own lane

Say which date you used: effective, instrument, execution, acknowledgment, or
`UNSUPPORTED`. Recording date is never the event date. When several candidates
coincide, **say so** rather than reporting a resolved basis you did not have to
choose.

> *`2002122700120002`: 5.4 months between signing and recording.
> `FT_1000000027200`: two years. `RC_400026`: all four dates identical — and both
> extractors reported a basis as if they had discriminated.*

**But sending the recording date to the brief silently takes three other facts with
it**, and v3 rules 1 and 5 contradicted each other on exactly this page.

So: below the event table, a **registry lane** — same citation discipline, same
checker reach, not one of the eleven functions.

| holds | example |
| --- | --- |
| recording date **and time** | *April 25, 1911 at 9 a.m.* — time fixes same-day priority |
| the registry's own act | performed by the clerk, on the **instrument**, not by a party on the parcel |
| the return-to party | *C. Livingston Bostwick, for Wood, Harmon & Co., Broadway, N.Y. City* |
| fee, tax, revenue stamps | with rule 5 applied — an unlabelled number is not a fee |

**Not a twelfth function.** A registry act stays a candidate until a third document
forces it. A lane costs nothing to withdraw; a function does.

> *`RC_1598772`: the return-to party is the only appearance in the entire document
> of the grantor's agent and address. An early round already lost party addresses as
> an undetected error. This is the same hole one page over.*

### 5. Never write a value you cannot point at

If the document does not state it, the answer is `UNKNOWN` plus the reason. Do not
infer from position, convention, or an adjacent label.

> *`RC_400026`: BBL `5009450000` ends in lot `0000` and the deed states no tax lot.
> `FT_1000000027200`: a stamp reading `16.00` with no label — one reader refused to
> call it a fee, and was right to. Round 1: two grantees, no stated shares, and
> 50/50 would have looked exactly like a measurement.*

### 6. The arrow means one relation, and one only

`from → to` means **the act moves from the first party to the second.** A grantor
conveys to a grantee. A mortgagor owes a mortgagee.

**On `ASSERT` rows there is usually no such movement.** Do not use an arrow. Write a
labelled relation instead:

```
asserted by: The Wood, Harmon Company    about: itself
```

> *`RC_1598772`: eight to ten rows per table are assertions. Two readers used the
> arrow for two different relations — one asserter → recipient, one name → capacity.
> **Two relations wearing the same notation is exactly what reads as agreement
> between readers who meant different things.***

### 7. `where` says whose land it is, before it says which land

Prefix every `where` with a scope marker, so the deterministic BBL check can see
what prose hides:

| marker | means |
| --- | --- |
| `SUBJECT` | the parcel this instrument conveys or burdens — then the BBL |
| `OTHER:` | real land, **not** the subject parcel — then the description |
| `INSTRUMENT` | the row is about the paper, not any parcel — registry lane rows |
| `UNPLACED` | the document does not place it |

Blank is never correct. Blank and `OTHER:` are different claims.

> *`RC_1598772`: two events are placed **precisely** on land this deed does not
> convey — "any part of South New York, Addition Number Four", and lots on four
> named streets. Both readers wrote prose the BBL check cannot see.*

### 8. Read the handwriting. It changes the meaning.

Corrections, strikes, insertions and marginal notes are operative. A struck digit
over a typed one is the real value. Follow an insertion line to where it points, not
to the nearest similar name. **Cite the mark with a rect (rule 1).**

> *`FT_1000000027200`: the acknowledgment year was hand-corrected 1981 → 1983; one
> extractor read the typed characters and was two years wrong. `RC_300106`: a
> boundary distance struck and rewritten by hand. Round 1: a margin note reading
> "husband and wife" attached to the wrong couple by surname match.*

**And beware the inverse.** Copperplate lead-in flourishes read as strikes at page
zoom, especially where a reader expects strikes.

> *`RC_1598772`: the orchestrator read two flourishes as cancellations and wrote it
> down as fact. Five readers disagreed, unanimously. The acknowledgment venue lines
> — State / City / County of New York — are all three operative for the same reason.*

### 9. "I found nothing" is not "the document says there is nothing"

Both are legitimate outputs and they are different claims. Only write the second
when the document actually asserts the absence.

There is a third state, and it is not the same as either: **the document declines to
say.** *"filed or intended to be filed"* asserts a date and a number while refusing
to confirm the act happened. Write it as stated; do not resolve it.

> *`RC_400026`: "the said premises are free from incumbrances" is a real asserted
> absence, and the only one found in four documents. `RC_1598772`: two readers
> checked both margins at 900 dpi for a fee and found none — "I found nothing", not
> "the document says there is nothing."*

### 10. Check the index. Trust neither side. Correct nothing.

Record where the document and the registry disagree, and leave both standing. Where
the index has no field to check against, say `NOT_CHECKABLE` — that is not the same
as agreeing.

> *`RC_400026`: index says the consideration was `$0.00`; the deed says $100.
> `RC_300106`: index types Michael Milea as a company; the acknowledgment calls him
> an individual. `2002122700120002`: index and cover read `NICLOAE ILIE`, the body
> and both signature blocks read `Nicolae Ilie`. Film rows carry no role field at
> all — on 100% of them.*

### 11. Read every page, whatever shape it is

Pages are rotated, sideways, partial strips, and endorsement backs. The page you
cannot read easily is often the one carrying the fee, the return-to party, and the
parcel identification.

> *`FT_1000000027200` p07 is rotated 90°. `RC_400026` p01 is a bottom strip of a
> book page. `RC_300106` p09 carries all 35 lots in handwriting.*

### 12. The same page can appear twice

Film frames the same leaf more than once. **The digests differ**, so a hash check
will not catch it. Match on the reel/page stamp and the printed page number, and
emit the content once.

> *`FT_1000000027200`: pages 5 and 6 are both reel 677 page 358, both footed "-4-",
> hashes `d01c7d16…` and `5474fa71…`.*

### 13. Page counts disagree, and that is not an error

Registries count cover pages; instruments do not; schedules carry their own
numbering from other documents. Report every count you find. Reconcile none of them.
Never use one as a completeness test.

> *`2002122700120002` states six counts with four denominators on its own face —
> and the stray "of 8" belongs to a title report that is not in the package.*

### 14. Verify against the artifact, never against the brief

If someone tells you a fact about the document, the checker, or another reader's
table — **go look at the thing itself.** A summary is a distortion, and a reader
working from the orchestrator's summary replicates the orchestrator's errors instead
of reading the page. Independence then quietly degrades into five readings of one
brief.

> *`RC_1598772`: told a checker defect existed, one reader checked the live tool
> instead of taking the claim, found another reader had already proved it and the
> fix had landed, and withdrew its own finding before filing. The orchestrator was
> wrong three times that session; every one was caught by someone who went to the
> source.*

## Known open, so nobody reports it as new

- **The acknowledgment day on `RC_1598772`** — four readers read 18; one reads 18
  with 15 as the only other candidate. The figure is overwritten by descenders.
  Calendar-possible range 14–25. Not outcome-bearing there.
- **`until` is not yet checked.** `bin/tablecheck.py` validates `instrument`,
  `acknowledged` and `recorded` only. An `expires:` line is currently unenforced.
- **Rects are not yet checked.** Nothing verifies that a cited rect contains the
  cited text. Until that exists, rule 1 is a discipline, not a guarantee — and a
  `STRUCK` row is only as good as the reader that wrote it.
- **No held-out scored set exists.** There is no number saying v4 is better than v3.

## What is deliberately not here

No JSON schema. No sweep serialisation. No version gate, compiler, or bundle
manifest. Those produced 32 defect reports across three documents, almost all of the
form *"the framework has no field for this"* — and not one of them was a document
the models could not read.

The reading was never the problem.
