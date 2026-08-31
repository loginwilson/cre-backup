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

1. **Can a program list the BBLs this event affects?** (Reorganize)
2. **Can a program place it in time?** (Resolve)
3. **Can a program tell what state it writes under its function?** (Resolve)

If any answer is *"a model would have to read the prose,"* **the row is incomplete —
however accurate it is.** A faithful row that cannot be consumed has moved the work
downstream, not done it.

## The row

| column | holds | consumed by |
| --- | --- | --- |
| `#` | E1, E2, … in page order | — |
| `citation` | `page · rect · mark · quote` — card 1 | audit |
| `date` | ISO `YYYY-MM-DD`, or `UNKNOWN` | Resolve |
| `basis` | `effective` · `instrument` · `execution` · `acknowledgment` · `UNSUPPORTED` | Resolve |
| `until` | ISO date, or blank if it does not stop | Resolve |
| `function` | one of the eleven | Resolve |
| `mode` | `ASSERT` · `TRANSFER` · `CREATE` · `MODIFY` · `TERMINATE` · `STRUCK` | Resolve |
| `bbls` | **a list.** See below — never prose | **Reorganize** |
| `sets` | **the state this event writes.** See below — never prose | **Resolve** |
| `parties` | `from → to` for a directed act; a labelled relation otherwise | Resolve |
| `quantity` | number + unit, or `UNKNOWN` with the reason | Derive |
| `terms` | the operative conditions, in prose | human |
| `summary` | one line, plain English | human |

**`date` and `basis` are separate columns** because Resolve sorts on one and audits
the other. One cell holding *"1911-04-14 (instrument date)"* forces a parse.

### `bbls` — a list, because one event binds many lots

| form | means | Reorganize |
|---|---|---|
| `5004030016` | one BBL | fans to one |
| `5004030016, 5004030017` | several | fans to each |
| `SET: <criterion>` | a set the document defines but does not enumerate — *"all lots in plat 995 B"* | **deferred**, resolvable once the plat is decoded |
| `INSTRUMENT` | about the paper, not a parcel — registry lane | no fan |
| `UNPLACED` | the document does not place it | no fan, flagged |

⚠ **`SET:` is a promise, not prose.** It names a criterion a later pass can evaluate.
*"lots on four named streets"* written as description is not a `SET:` — it is a row
that failed the test.

### `sets` — the value that lands in the state matrix

Every cell in the Temporal State Matrix is written by some event. **This column is
that write.** `MODIFY` on `ENCUMBRANCE` with `sets` empty tells Resolve that
something changed and nothing about what it changed to.

The legal values are **per function and per class, and they live in
`specs/<CLASS>.md`** — not here. A shared vocabulary invented from one document
would be wrong for the next ten. What is universal is only this: **`sets` is never
prose, and never empty.** When the document does not determine the value, write
`UNKNOWN(<reason>)` — that is a real state, and Resolve treats it as a known gap
rather than a silent one.

Above the table, a labelled date block — `instrument:`, `acknowledged:`,
`recorded:`, `expires:`, `UNKNOWN` where unstated. Below it, the **registry lane**:
recording date *and time*, the registry's own act, the return-to party, and any fee
or stamp. Same citation discipline. Not one of the eleven — it asks about the
**instrument**, not the parcel.

`from → to` means **the act moves from the first party to the second**. On an
`ASSERT` row there is usually no such movement — write `asserted by: X  about: Y`.
Two relations wearing one notation reads as agreement between readers who meant
different things.

Above the table, a labelled date block — `instrument:`, `acknowledged:`,
`recorded:`, `expires:`, `UNKNOWN` where unstated. Below it, the **registry lane**:
recording date *and time*, the registry's own act, the return-to party, and any fee
or stamp. Same citation discipline. Not one of the eleven — it asks about the
**instrument**, not the parcel.

Then a brief: six to ten lines, no new facts, everything traceable to a row.

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
