# Extraction framework — the schema

**This file holds only what is true for every document: the eleven functions and
the shape of a row.** Judgment lives in `EXTRACT-CARD.md`, short enough to hold in
working memory. Class knowledge lives in `specs/<CLASS>.md`. Mechanical rules live
in `bin/tablecheck.py` and are never carried in your head.

> *Why it is split this way.* v4 reached 20 KB from a single document, and
> `Bootcamp/LOOP.md` had already diagnosed where that ends: a rule base past the
> point where it can be recalled rather than consulted, producing unverified and
> then fabricated rule citations. That is a capacity limit, not carelessness, and
> no further rule fixes it. Per LOOP.md §V, class-specific and mechanizable rules
> **leave the reader's memory entirely.** This file and the card are what remain.

## The job

Select a document. Read it **page by page**. On each page ask, of every one of the
eleven functions: *does anything on this page do something?* Every hit becomes a
row. Then write a short brief.

Before you open it, read `specs/<CLASS>.md` and write down what you expect to find.
**That prediction is scored** — see "How a round is measured" below.

## How you reach a document

**You are handed a package. You never go and get one.** Built once by the
orchestrator with `docpkg.py <id>` so every reader holds byte-identical inputs.
Your inputs are the numbered page images plus `docpkg.py --page --rect` to zoom.

**Never touch the corpus yourself** — no directory walk over the acquisition store,
no query against the navigation db, no acquisition or reproduction script, no
network. The contract is `04 Extractions/DOCUMENT ACCESS.md`; `docpkg.py`
implements it and is the only path. If a tool you need does not exist, **say so and
stop.**

## The eleven functions

Ask all eleven on every page. Not the ones the document type suggests.

A function is **a kind of question about a parcel**. If something fits none of them,
write it under an explicit heading **in your own folder** and say what filing it
under the nearest function would lose. You are not shown other readers' candidates —
a list of things to look for is a list of things you will find.

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
promise to repay is `CAPITAL`; the lien burdening the lot until it is repaid is
`ENCUMBRANCE`. Subordinating that lien changes the `ENCUMBRANCE` and leaves the
`CAPITAL` untouched.

**COST vs VALUE.** `VALUE` is what the thing is worth or what was exchanged for it.
`COST` is money spent on process, or a duty to spend. A $100 consideration is
`VALUE`; a $2.50 recording fee is `COST`; *"shall cost not less than $2,000"* is a
`COST` obligation even though no money has moved.

**ENVELOPE vs AS_BUILT vs OCCUPANCY.** `AS_BUILT` is what **is**. `ENVELOPE` is what
**may be built**. `OCCUPANCY` is who may **use** it.

**TITLE vs ENCUMBRANCE.** `TITLE` is who holds the estate; `ENCUMBRANCE` is what
rides on it. A deed conveying a lot subject to restrictions produces one of each.

**ENTITLEMENT vs PERMIT.** `ENTITLEMENT` is a right attaching to the land that
survives its owner. `PERMIT` is a **government** act or application about a specific
project. A private party holding a discretionary approval right is neither — say
what filing it elsewhere loses.

**When two fit:** emit under the function whose question the clause actually
answers, and note in `terms` that it bears on the other. Do not emit one act twice —
but **do** emit separate rows when one sentence genuinely does two things.

## What the row is FOR

Extraction is step 1 of Reconstruction. Steps 2 and 3 are **Reorganize** (fan each
event into the BBLs it affects, sort chronologically) and **Resolve** (turn the
ordered events into a function-by-time state record — the Temporal State Matrix).

**Those two run mechanically, or they do not run at all.** So the bar for extraction
is not "faithful to the document." It is **faithful AND determinate**: every field a
downstream program needs must be a value it can read, never prose it must interpret.

### The consumability test — three questions per row

1. **Can a program list the BBLs this event affects?** (Reorganize fans on this)
2. **Can a program place it in time?** (Reorganize sorts on this)
3. **Is the function one of the eleven?** (Resolve projects on this)

If any answer is *"a model would have to read the prose,"* **the row is incomplete —
however accurate it is.** A faithful row that cannot be consumed has moved the work
downstream, not done it.

**That is the whole requirement.** Given every event for a BBL, ordered, each tagged
with a function, the functional state record follows — `mode` already says whether
an event adds (`CREATE`), changes (`MODIFY`), moves (`TRANSFER`), ends (`TERMINATE`)
or merely states (`ASSERT`) what came before. Resolution is **ordering and
projection, not re-interpretation.** Extraction does not need to pre-compute state.

## THE ROW — the complete definition

**One row = one operative act.** Not one per constraint, not one per citation, not
one per sentence. That is the granularity rule, and it is the largest single source
of disagreement between readers.

Three columns are **machine fields** — a program reads them and must never guess.
The rest are **context**, for a human and for Derive.

| # | column | machine? | legal form | invalid looks like |
|---|---|---|---|---|
| 1 | `#` | — | `E1`, `E2`, … in page order | — |
| 2 | `citation` | — | `page · rect · mark · quote` | a quote with no rect on a mark-dependent row |
| 3 | **`date`** | **yes** | ISO `YYYY-MM-DD`, or `UNKNOWN` | `April 25, 1911` · `1911` · `circa 1911` |
| 4 | `basis` | yes | `effective` · `instrument` · `execution` · `acknowledgment` · `UNSUPPORTED` | `recorded` — recording is not an event date |
| 5 | `until` | yes | ISO date, or **blank** if it does not stop | a duration (*"three years"*) — compute it |
| 6 | **`function`** | **yes** | exactly one of the eleven | two functions in one cell · anything else |
| 7 | `mode` | yes | `ASSERT` · `TRANSFER` · `CREATE` · `MODIFY` · `TERMINATE` · `STRUCK` | a verb of your own |
| 8 | **`bbls`** | **yes** | see below | any description of a place |
| 9 | `parties` | — | `X → Y`, or `asserted by: X  about: Y` | an undirected list |
| 10 | `quantity` | — | number + unit, or `UNKNOWN(<reason>)` | a bare number with no unit |
| 11 | `terms` | — | the operative conditions, prose | — |
| 12 | `summary` | — | one line, plain English | — |

**`date` and `basis` are separate columns.** Resolve sorts on one and audits the
other; a cell reading *"1911-04-14 (instrument date)"* forces a parse.

**`until` exists because some states end themselves.** A covenant expiring
1915-01-01 has no terminating document — without `until`, Resolve would carry the
burden forever, and every statement about that parcel after 1915 would be wrong.

### `bbls` — a list, because one event can bind many parcels

| form | means | Reorganize |
|---|---|---|
| `5004030016` | one BBL | fans to one |
| `5004030016, 5004030017, …` | several — an 8-way air rights transfer is eight | fans to each |
| `SET: <criterion>` | a set the document defines but does not enumerate — *"all lots in plat 995 B"* | **deferred**, resolvable when the plat is decoded |
| `INSTRUMENT` | about the paper, not a parcel — registry lane rows | no fan |
| `UNPLACED` | the document does not place it | no fan, flagged |

⚠ **`SET:` is a criterion, not a description.** A later pass must be able to
evaluate it. *"lots on four named streets"* is prose — it reaches no parcel, and it
is a row that failed.

### ⚠ A BBL is a reference **in a state in time**, and you never derive one

**Parcels change.** Lots merge, split, and get renumbered. A 1911 deed's *"lot 17,
block 200"* is not today's BBL and must never be written as if it were.

So record **what was true then**, from the two sources that actually state it:

| source | gives you |
|---|---|
| **rd** (`recorded_details`) | the BBL as the registry held it for this instrument — this is where most of it comes from |
| **the document** | the parcel designation in its own words — lot, block, filed map — which is the **context** rd does not carry |

**Write rd's BBL when rd has one.** Put the document's own designation in `terms`
whenever it differs in form, and say so. Where they disagree, record both and
correct neither — that disagreement is a real finding (card 9).

**Never compose a BBL yourself** from a borough plus a lot and block on the page.
It renders exactly like a measured value and it is a guess (card 4). If rd has no
BBL and the document gives only a map designation, that is `UNPLACED` plus the
designation in `terms` — a parcel this instrument names but does not resolve.

> *Connecting 1911's lot 17 block 200 to the lot it is today is **lineage**, built by
> Resolve across many documents. It is not something a reader can see on one page,
> and a reader who tries has invented it.*

### A worked row, so there is nothing to interpret

```
| #  | citation                                          | date       | basis      | until      | function    | mode   | bbls                        | parties                    | quantity      | terms                                   | summary                          |
| E4 | p2 · [0.15,0.32,0.95,0.36] · plain · "no dwelling  | 1911-04-14 | instrument | 1915-01-01 | ENVELOPE    | CREATE | SET: all lots in plat 995 B | The Wood, Harmon Co. → all | $2,000 USD    | $2,000 on Heberton; $3,000 on the       | Every house on the plat must     |
|    | shall cost less than Two Thousand Dollars"        |            |            |            |             |        |                             | grantees in the plat       |               | avenue frontage. Runs with the land.    | cost at least $2,000 until 1915. |
```

Machine fields: `1911-04-14` sorts, `ENVELOPE` projects, `SET:` fans once the plat
is decoded. Everything else is context.

### Above and below the table

A labelled date block — `instrument:`, `acknowledged:`, `recorded:`, `expires:`,
`UNKNOWN` where unstated. Then the **registry lane**: recording date *and time*, the
registry's own act, the return-to party, and any fee or stamp. Same citation
discipline. Not one of the eleven — it asks about the **instrument**, not a parcel,
and its rows carry `bbls: INSTRUMENT`.

Then a brief: six to ten lines, no new facts, everything traceable to a row.

## Where the difficulty actually is

The schema above is small and fixed. **Everything hard is in reading the document
well enough to fill it** — which of the eleven fires, where one act ends and the
next begins, whether a mark is a strike or a flourish, which of four dates is the
event. That is what `EXTRACT-CARD.md` is for, and what the class specs accumulate.

**Measured on the five sealed RC_1598772 tables: 0 of 125 rows clear the three
machine fields.** Five careful blind readers, and nothing consumable — because the
table had never been defined this way. That number is the baseline. It should not
stay at zero for a second document.

## How a round is measured

Two numbers, from `Bootcamp/LOOP.md`. Not a letter, not an opinion.

- **COVERAGE** — of the spec fields this document actually carries, how many did the
  read find? Should sit at 100%. Below that is reading discipline, as a number.
- **STRUCTURAL SURPRISE** — how many things did it carry that the spec had **no
  place to put**? A typo or a missing exhibit is *incidental* and does not count;
  incidental surprise is unbounded because documents are messy, and driving it to
  zero would mean the spec had stopped looking.

**A class closes when two consecutive new members add no structural surprise.**

**The gate:** a spec change is re-checked against that class's prior members. A
change contradicting an already-read document is rejected, or recorded as a branch.

## Where a new rule goes — never here by default

| the finding is… | it belongs in |
| --- | --- |
| true of one document class | `specs/<CLASS>.md` — and leaves your memory |
| checkable by arithmetic, calendar, or format | `bin/tablecheck.py` — code, never a prompt |
| genuine cross-class judgment | `EXTRACT-CARD.md`, **capped at twelve cards** |

If the card set is full, a new card **displaces** one. It does not extend the list.
That cap is the only thing standing between this and the 129 KB that came before.
