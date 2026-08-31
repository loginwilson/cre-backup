# Extraction framework v3

Replaces v2 (`506b88d8…`, 129 KB + three JSON schemas + a version gate). Every
rule below is here because a real document proved it was needed, and the document
is named. **A rule with no document behind it does not belong in this file.**

## The job

Select a document. Read it **page by page**. On each page ask, of every one of the
eleven functions: *does anything on this page do something?* Every hit becomes a
row. Then write a short brief.

Two extractors do this independently, with no contact. Then they meet, compare
tables, and propose changes to this file.

## The eleven functions

Ask all eleven on every page. Not the ones the document type suggests.

A function is **a kind of question about a parcel**. Together they are meant to
cover everything a recorded instrument can do. If something on the page fits none
of them, that is a finding — write it down rather than forcing it.

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
specific project.

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
| `citation` | page + the quote that proves it, **isolated to the thing it proves** |
| `time` | the date **and which date it is** |
| `function` | one of the eleven |
| `mode` | `ASSERT` · `TRANSFER` · `CREATE` · `MODIFY` · `TERMINATE` |
| `where` | BBL + scope, or blank if the document doesn't place it |
| `parties` | **from → to**. Never an undirected list |
| `quantity` | number + unit, or `UNKNOWN` with the reason |
| `terms` | the operative conditions |
| `summary` | one line, plain English |

Then a brief: six to ten lines, no new facts, everything traceable to a row.

## The rules

**1. The event date is when it happened, not when it was recorded.**
Say which date you used: effective, instrument, execution, acknowledgment, or
`UNSUPPORTED`. Recording date is never the event date — it goes in the brief.
When several candidates coincide, **say so** rather than reporting a resolved basis
you did not have to choose.

> *`2002122700120002`: 5.4 months between signing and recording.
> `FT_1000000027200`: two years. `RC_400026`: all four dates identical — and both
> extractors reported a basis as if they had discriminated.*

**2. Never write a value you cannot point at.**
If the document does not state it, the answer is `UNKNOWN` plus the reason. Do not
infer from position, convention, or an adjacent label.

> *`RC_400026`: BBL `5009450000` ends in lot `0000` and the deed states no tax lot.
> `FT_1000000027200`: a stamp reading `16.00` with no label — A refused to call it a
> fee, and was right to. Round 1: two grantees, no stated shares, and 50/50 would
> have looked exactly like a measurement.*

**3. Check the index. Trust neither side. Correct nothing.**
Record where the document and the registry disagree, and leave both standing. Where
the index has no field to check against, say `NOT_CHECKABLE` — that is not the same
as agreeing.

> *`RC_400026`: index says the consideration was `$0.00`; the deed says $100.
> `RC_300106`: index types Michael Milea as a company; the acknowledgment calls him
> an individual. `2002122700120002`: index and cover read `NICLOAE ILIE`, the body
> and both signature blocks read `Nicolae Ilie`. Film rows carry no role field at
> all — on 100% of them.*

**4. Read the handwriting. It changes the meaning.**
Corrections, strikes, insertions and marginal notes are operative. A struck digit
over a typed one is the real value. Follow an insertion line to where it points,
not to the nearest similar name.

> *`FT_1000000027200`: the acknowledgment year was hand-corrected 1981 → 1983; one
> extractor read the typed characters and was two years wrong. `RC_300106`: a
> boundary distance struck and rewritten by hand. Round 1: a margin note reading
> "husband and wife" attached to the wrong couple by surname match.*

**5. Read every page, whatever shape it is.**
Pages are rotated, sideways, partial strips, and endorsement backs. The page you
cannot read easily is often the one carrying the fee, the return-to party, and the
parcel identification.

> *`FT_1000000027200` p07 is rotated 90°. `RC_400026` p01 is a bottom strip of a
> book page. `RC_300106` p09 carries all 35 lots in handwriting.*

**6. The same page can appear twice.**
Film frames the same leaf more than once. **The digests differ**, so a hash check
will not catch it. Match on the reel/page stamp and the printed page number, and
emit the content once.

> *`FT_1000000027200`: pages 5 and 6 are both reel 677 page 358, both footed "-4-",
> hashes `d01c7d16…` and `5474fa71…`.*

**7. "I found nothing" is not "the document says there is nothing."**
Both are legitimate outputs and they are different claims. Only write the second
when the document actually asserts the absence.

> *`RC_400026`: "the said premises are free from incumbrances" is a real asserted
> absence, and it is the only one found in four documents.*

**8. Page counts disagree, and that is not an error.**
Registries count cover pages; instruments do not; schedules carry their own
numbering from other documents. Report every count you find. Reconcile none of
them. Never use one as a completeness test.

> *`2002122700120002` states six counts with four denominators on its own face —
> and the stray "of 8" belongs to a title report that is not in the package.*

## What is deliberately not here

No JSON schema. No sweep serialisation. No version gate, compiler, or bundle
manifest. Those produced 32 defect reports across three documents, almost all of
the form *"the framework has no field for this"* — and not one of them was a
document the models could not read.

The reading was never the problem.
