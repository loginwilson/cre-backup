# MATRIX SPEC — v1 (A draft)

How an event table becomes the resolved matrix. This is a **mechanical
transform**: same event table in, byte-identical `resolved.md` out. Nothing here
requires reading the document again. If two agents produce different matrices
from the same events, this file is defective, not their judgement.

Rule ids are immutable and are `M-*` to keep them distinct from framework rules.

## 0 · WHY THIS EXISTS BEFORE THE FIRST EXTRACTION

"We got the same result" is unfalsifiable until "the result" is defined. Without
a fixed fan, sort, tie-break, fold and serialisation, two agents who extracted
identically will still produce different tables, and rounds get spent arguing
about how each of them drew it.

## 1 · SHAPE

- One matrix **per BBL**. A document touching four parcels produces four
  matrices in one `resolved.md`.
- **Time down**: each row is one *moment* on that parcel.
- **Function across**: eleven columns, always all eleven, always in this order:

  | # | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
  |---|---|---|---|---|---|---|---|---|---|---|---|
  | col | `ID` | `TTL` | `ENT` | `ENV` | `ENC` | `CAP` | `PRM` | `ASB` | `OCC` | `CST` | `VAL` |
  | function | IDENTITY | TITLE | ENTITLEMENT | ENVELOPE | ENCUMBRANCE | CAPITAL | PERMIT | AS_BUILT | OCCUPANCY | COST | VALUE |

- Each cell is the state of one function at one moment, **as far as this document
  establishes it**. A single document read alone cannot know the parcel's full
  prior state; the cell therefore holds what this document writes there, and one
  of the four nulls where it writes nothing.

## 2 · STEP 1 — FAN

**M-FAN-1.** For each event `e` and each parcel `p` in `e.parcels`, emit the
triple `(p.bbl, e, p.parcel_role)`.

**M-FAN-2.** An event with `parcels: []` is fanned nowhere. It still appears in
`extraction.json`. `resolved.md` records it under **UNFANNED EVENTS** with the
reason, so it cannot be lost by being invisible.

**M-FAN-3.** The same event fanned to two parcels appears in both matrices,
unchanged except for `parcel_role`. Quantities are **not** divided by fanning
(R-QTY-3); a grouped quantity renders as `ALLOC_ND(<group_id>)` in every cell it
reaches.

**M-FAN-4.** Parcels are ordered by BBL ascending as a 10-character string.

## 3 · STEP 2 — SORT

**M-SORT-1 · `sort_date`.** Sorting needs a total order, and `event_date` may be
`UNKNOWN`. Derive, per event:

```
sort_date = event_date.v            if event_date.v != "UNKNOWN"
          = date_bound_latest.v     otherwise
```

A `YYYY` or `YYYY-MM` precision date sorts as if `-01` were appended for each
missing component; the displayed value keeps its true precision.

**M-SORT-2 · `sort_date` is an ordering key and nothing else.** It is never
copied into `event_date`, never displayed as the event's date, and never cited.
Any row whose `sort_date` came from `date_bound_latest` is marked `~` in the
`WHEN` column, so a reader can see at a glance which moments are bounded rather
than dated.

**M-SORT-3.** Within a BBL, sort ascending by `sort_date`.

## 4 · STEP 3 — TIE-BREAK

**M-TIE-1.** Events sharing a BBL and a `sort_date` occupy the **same row**, in
different columns. No tie-break is needed to place them.

**M-TIE-2.** Two or more events in the **same cell** (same BBL, same
`sort_date`, same function) are ordered by, in order:
1. mode index: `CREATE 1 · MODIFY 2 · TRANSFER 3 · TERMINATE 4 · CORRECT 5 ·
   ASSERT 6`
2. parcel-role index: `SUBJECT 1 · GRANTING 2 · RECEIVING 3 · BURDENED 4 ·
   BENEFITED 5 · ADJOINING 6 · REFERENCED 7`
3. `event_id` ascending, as a string.

**M-TIE-3 · `event_id` assignment is itself deterministic**, so that two agents
with the same events assign the same ids. Before numbering, order all events of
the document by: `sort_date` asc → function index (§1 order) asc → mode index
asc → lowest BBL in `parcels` asc (events with no parcel sort last) →
`clause.at` asc as a string → `clause.q` asc as a string. Then number
`<docid>-E01`, `E02`, … in that order.

## 5 · STEP 4 — ROWS

**M-ROW-1.** A row is one distinct `sort_date` on one BBL. All events fanned to
that BBL with that `sort_date` fill that row's columns.

**M-ROW-2.** Rows are never invented. If a document establishes three moments,
the matrix has three rows. There is no row for "now", none for the recording
date unless an event resolves there, and no interpolation between moments.

**M-ROW-3 · The `WHEN` column** renders `sort_date` in `YYYY-MM-DD`, suffixed
`~` when M-SORT-2 applies, and suffixed `(M)` or `(Y)` when the underlying
`event_date` has month or year precision.

## 6 · STEP 5 — FOLD

**M-FOLD-1.** A cell's content is the ordered list (M-TIE-2) of its events, each
serialised by M-SER-2, joined by ` + `.

**M-FOLD-2.** Events are **not** merged at fold time. Merging happens once, at
extraction, under R-SPLIT-4. If two events survive to the same cell they are
genuinely two events and both are shown.

**M-FOLD-3.** A cell with no events takes a null from §7.

## 7 · STEP 6 — NULLS IN CELLS

**M-NULL-1.** For a cell with no event, apply R-NULL-1 at the level of the
(BBL, function) pair across the **whole document**, then write the same null in
every empty cell of that column for that BBL:

| condition | cell |
|---|---|
| no operative clause in the document writes to this function for this parcel | `·` rendering `NO_CHANGE` |
| the document affirmatively states the thing does not exist | `ASSERTED_NONE(<scope quote ≤8 words>)` |
| the document states a condition making the function valueless here | `NOT_APPLICABLE(<condition quote ≤8 words>)` |
| a clause writes here but states no value | `UNKNOWN` |

**M-NULL-2 · `NO_CHANGE` renders as `·`.** Eleven columns of spelled-out
`NO_CHANGE` makes the table unreadable and every diff enormous. The long form
survives in the canonical serialisation (§9), where nothing is abbreviated.

**M-NULL-3.** A column that is `·` for every row of every parcel is still
printed. An absent column would be indistinguishable from an omitted one.

## 8 · STEP 7 — CELL SERIALISATION

**M-SER-1 · Grammar.**

```
cell      := event ( " + " event )*
event     := MODE " " pair ( "|" pair )*
pair      := key "=" value
value     := scalar | scalar ( ";" scalar )*
```

`MODE` is the uppercase mode. Keys appear in the order given in M-SER-3 and are
**omitted when the slot is absent from that function's schema**, but written as
`key=UNKNOWN` when the schema has the slot and the document did not fill it.

**M-SER-2 · Value normalisation.** Deterministic, so cosmetic diffs cannot
happen:
- money → `USD <digits>.<2 digits>`, no thousands separators
- other quantities → `<UNIT> <number>`, units per R-QTY-1
- dates → `YYYY-MM-DD`, `YYYY-MM`, or `YYYY`
- names → uppercase, internal whitespace collapsed to one space, as printed
- lists → sorted ascending as strings, joined by `;`
- `|`, `;`, `+`, `=` occurring inside a value → replaced by a single space
- quotes inside a cell → truncated to 8 words, no ellipsis
- unknown → `UNKNOWN`; grouped quantity → `ALLOC_ND(<group_id>)`

**M-SER-3 · Key order per function.**

| col | keys, in order |
|---|---|
| `ID` | `status`, `designation`, `former`, `new`, `extent` |
| `TTL` | `from`, `to`, `interest`, `share`, `covenant` |
| `ENT` | `permission`, `authority`, `identifier`, `conditions` |
| `ENV` | `metric`, `amount`, `direction`, `counterparty_bbl` |
| `ENC` | `kind`, `holder`, `status`, `scope`, `ref` |
| `CAP` | `obligor`, `obligee`, `principal`, `rate`, `maturity`, `terms` |
| `PRM` | `identifier`, `authority`, `scope`, `status` |
| `ASB` | `metric`, `amount`, `statement` |
| `OCC` | `use`, `units`, `certificate`, `statement` |
| `CST` | `kind`, `amount`, `payer`, `payee` |
| `VAL` | `kind`, `amount`, `as_of` |

`ENV.direction` is `GRANTED` / `RECEIVED` / `RESERVED` and `counterparty_bbl`
the other parcel — an air-rights transfer's granting and receiving lots are not
interchangeable and the cell must show which this one is.

`CST` and `VAL` cells commonly hold several events (one per money kind); that is
what the ` + ` join is for.

## 9 · OUTPUT — `resolved.md`

Exactly these sections, in this order.

```markdown
# RESOLVED MATRIX — <document_id>
framework v1 · matrix-spec v1 · package <ACRIS_DIGITAL|ACRIS_FILM|BOOK|RICHMOND>
events <n> · parcels <n> · unfanned <n> · emitted <n> · flagged <n> · ratio <0.00>

## BBL <bbl>   role <parcel_role(s)>   extent <extent>
| WHEN | ID | TTL | ENT | ENV | ENC | CAP | PRM | ASB | OCC | CST | VAL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2002-11-22 | · | TRANSFER from=... | · | · | ASSERT ... | · | · | · | ASSERT ... | ASSERT ... | ASSERT ... |

## BBL <next bbl> ...

## UNFANNED EVENTS
<event_id> <FUNCTION> <MODE> — <reason>

## CANONICAL
<one line per non-NO_CHANGE cell, see M-CANON-1>
```

**M-CANON-1 · The canonical block is the artefact that gets compared.** The
markdown table is for humans; the canonical block is for diffing. One line per
cell that is not `NO_CHANGE`, tab-separated, no abbreviation:

```
<bbl>\t<sort_date>\t<flag>\t<FUNCTION>\t<cell string>
```

`<flag>` is `~` when M-SORT-2 applied, else `-`. Lines sorted by bbl asc, then
`sort_date` asc, then function index asc. `NO_CHANGE` cells are omitted from the
canonical block entirely — their absence is unambiguous because the column set
is fixed.

**M-CANON-2.** Comparison in Block 3 is: canonical block first, cell by cell;
then the event tables. A difference that vanishes in the canonical block is
cosmetic — log it, write no rule (TRAYCER "won't occur to you" #3).

## 10 · WORKED EXAMPLE

Event table (abridged) for a bargain-and-sale deed with an RP-5217 and a smoke
detector affidavit, BBL `4063520006`:

| event | function | mode | event_date | basis |
|---|---|---|---|---|
| `…-E01` | TITLE | TRANSFER | 2002-11-22 | STATED_EFFECTIVE (RP-5217 field 11) |
| `…-E02` | ENCUMBRANCE | ASSERT | 2002-11-22 | EXECUTION |
| `…-E03` | OCCUPANCY | ASSERT | 2002-11-22 | EXECUTION |
| `…-E04` | COST | ASSERT | 2002-11-22 | EXECUTION |
| `…-E05` | VALUE | ASSERT | 2002-11-22 | EXECUTION |
| `…-E06` | AS_BUILT | ASSERT | 2002-11-22 | ACKNOWLEDGMENT |

All six share a `sort_date` → **one row**, six columns filled, five `·`.

```
| WHEN | ID | TTL | ENT | ENV | ENC | CAP | PRM | ASB | OCC | CST | VAL |
| 2002-11-22 | · | TRANSFER from=SIEV AVINADAV;SIEV PAZIA|to=ZHENG SHOU HUA|interest=FEE|share=UNKNOWN|covenant=BARGAIN_SALE_WITH_COVENANT | · | · | ASSERT kind=COVENANT|holder=ZHENG SHOU HUA|status=OPEN|scope=has not done or suffered anything whereby|ref=UNKNOWN | · | · | ASSERT metric=SMOKE_DETECTOR|amount=UNKNOWN|statement=approved and operational smoke detecting device installed | ASSERT use=One Family Residential|units=UNKNOWN|certificate=UNKNOWN|statement=one or two family dwelling | ASSERT kind=CONSIDERATION_RECITED|amount=USD 10.00|payer=ZHENG SHOU HUA|payee=SIEV AVINADAV;SIEV PAZIA + ASSERT kind=SALE_PRICE|amount=USD 525500.00|payer=ZHENG SHOU HUA|payee=SIEV AVINADAV;SIEV PAZIA + ASSERT kind=TAX|amount=USD 2102.00|payer=UNKNOWN|payee=UNKNOWN | ASSERT kind=ASSESSED_VALUE|amount=USD 23039.00|as_of=UNKNOWN |
```

Canonical lines for that row:

```
4063520006	2002-11-22	-	TITLE	TRANSFER from=SIEV AVINADAV;SIEV PAZIA|to=…
4063520006	2002-11-22	-	ENCUMBRANCE	ASSERT kind=COVENANT|…
4063520006	2002-11-22	-	AS_BUILT	ASSERT metric=SMOKE_DETECTOR|…
4063520006	2002-11-22	-	OCCUPANCY	ASSERT use=One Family Residential|…
4063520006	2002-11-22	-	COST	ASSERT kind=CONSIDERATION_RECITED|… + …
4063520006	2002-11-22	-	VALUE	ASSERT kind=ASSESSED_VALUE|amount=USD 23039.00|as_of=UNKNOWN
```

Note what the example demonstrates: the deed's own text supplies two of the
eleven columns; four more come from pages the cover page does not count.

## 11 · MULTI-MOMENT AND MULTI-PARCEL

A consolidation agreement reciting a 1999 mortgage with a stated reduced balance
and consolidating it as of 2002, over four BBLs, produces: two `sort_date`s if
the reduction is dated, otherwise one; four matrices; and one quantity group
whose total appears in every `CAP` cell as `principal=ALLOC_ND(<docid>-Q1)` with
the group's total printed once under **UNFANNED EVENTS**' sibling block:

```
## QUANTITY GROUPS
<docid>-Q1  USD 1900000.00  covers E03;E04  parcels 3011290011;3011290012;…
```

**M-GRP-1.** Quantity groups are printed once per document, never per parcel.
The temptation to show the total in each parcel's cell is exactly the
mis-allocation R-QTY-3 forbids, one step removed.
