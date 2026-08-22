# THE BOOTCAMP — Legal Instruments Extraction

> **SCOPE - this is SYSTEM law, not a Legal Instruments file.** Promoted to
> the system root 2026-08-19 because the eleven functions, the three modes and
> the event row govern EVERY phase and EVERY source. Source-specific lessons
> live in this same file under their own heading - there is never a second
> bootcamp, because two copies of a vocabulary drift (see lexicon.py's own
> warning: the definitions were in five places and had already drifted).


**Version: hb-2026.08.20-r49** · Every extraction stamps the version that read
it. This file is the entry point; the learning lives in the sections below
and grows one entry per miss (the failure + the teaching document, anchored +
the rule). The md is the constitution; this is the case law.

## How to use (the loading rule)

Before reading a document: load VOCABULARY (always) + the GUARDS & RAILS
sections for the document's doc type. A rule not loaded at the right moment
does not exist.

## VOCABULARY — the eleven functions (closed 2026-08-16, lexicon.py)

A function names a DOMAIN OF FACT, not an action. Nothing outside this list
is a function. The test: "if nothing changes, there is no function and no
event — change is what makes a function apply."

| function | means |
|---|---|
| IDENTITY | what the parcel IS — boundaries, area, subdivision, the lot itself |
| TITLE | who owns it and how title moved |
| OCCUPANCY | who occupies it and on what terms |
| ENCUMBRANCE | burdens that run with the land |
| ENVELOPE | how much may be built, and how that changed |
| ENTITLEMENT | rights granted by authority — what is permitted to exist |
| PERMIT | construction and the approvals behind it |
| ASBUILT | the built condition as recorded |
| CAPITAL | money against the property — lent, owed, claimed (liens, arrears) |
| VALUE | prices, taxes, assessments — worth, when |
| COST | what was spent — consideration, fees, taxes paid |

## VOCABULARY - the modes (settled, lexicon.py MODES)

MODE is NOT the instrument form. It answers: **did the world change, was state
merely recited, or is this someone intent?** Measured at CLAUSE level, not
document level, against a 23,282-clause bench.

| mode | means | status |
|---|---|---|
| **transacts** | the world changed - **only these may assert that state changed** | proven (operative language: does hereby grant/convey/mortgage/assign; in consideration of the sum) |
| **observes** | state was measured or recited; nothing changed (is the owner of / known as / outstanding balance is / was recorded) | weak - reliably RECITAL, not proven observation |
| **signals** | intent or expectation asserted by an interested party, not yet fact | proven |

WARNING: one document emits several events and **a single deed carries all
three modes at clause level** - which is why mode is assigned per event, never
per document.

## THE EVENT ROW - **SUPERSEDED, do not read as current**

⚠ This section defined the row as `mode - subject - function - quantity - term
(+ legs, + anchor)`. **"Legs" no longer exist** - the ROW is the unit. Kept only
so the history of the change is visible.

**Current definition: THE EXTRACTION DATA TABLE (eleven columns) and THE THREE
TIERS OF THE ROW, both below.** Everything still true here is restated there.

- **subject** = what the event is ABOUT (the parcel, or the entity for
  party-keyed events). Not the routing key. *(still true)*
- **quantity** = an amount ALWAYS exists; bound it when it cannot be exact
  (G-016). *(still true)*
- **term** = the duration/estate; never blank on a title event (G-015). *(still true)*


## THE TWO WEIRD SLOTS - quantity and term

Mode, subject and function are always present: every verified event changed
(or recited) something, about something, in some domain. **Quantity and term
are the two slots that can legitimately be ABSENT** - and absence has to be
told apart from failure. So each of them takes exactly one of three states,
never a blank:

| state | means | example |
|---|---|---|
| **a value** | read and verified | `$2,475,000` · `fee simple absolute` |
| **n/a + reason** | this KIND of event has none | a name-correction has no quantity; a satisfaction has no new term - it ENDS one |
| **unread** | it exists and we failed to get it | the 1986 mortgage maturity: stated in the instrument, not yet read |

`n/a` is a claim about the event kind. `unread` is a claim about us. Collapsing
them into one blank destroys the only signal that says whether to go back.

**QUANTITY carries a UNIT, always.** Money, area (SF), share (%), count. A
number without its unit is not a quantity - `100,000` is meaningless where
`100,000 SF of development rights` is an event. When exact is impossible,
BOUND it (G-016): `$10 recited, <= $500 by stamp`.

**TERM carries a KIND, always.** One of:
- **estate** - what was conveyed: fee simple absolute, life estate, leasehold
- **duration** - a fixed span: 30 years, 10-year option
- **maturity** - a date the obligation comes due
- **condition** - it ends on an event: until paid, until released, runs with
  the land (indefinite BY DESIGN - that is a value, not a blank)

**THE PAIRING CHECK - an event with neither is suspect.** If quantity AND term
are both `n/a`, the row is probably not an event at all: either nothing
actually changed (it is an `observes` recital or a REFERENCE), or both slots
went unread and the row is hollow. Every such row gets inspected before it is
allowed into a chain. A parcel event may legitimately carry a term and no
money (an easement running with the land); a payment event may carry money and
no term (a one-time discharge) - but never both empty.


## MULTIDIRECTIONAL EVENTS - one event, N leg rows (the DEVR case)

**The question:** five lots transfer air rights to one receiving lot. Five
events, or one event with five rows?

**Answer: ONE EVENT, N ROWS - one row per from->to pair.** The event is the
legal act (one instrument, one closing, one date); each sender-receiver pair
is a row, and the rows share one event id.

Why not five events: the instrument is ONE transaction. Split it and anyone
counting air-rights deals gets 5 where the market saw 1, and an aggregate price
stated once gets counted five times.

Why not one row: each sender moves its OWN square footage for its OWN money.
Collapse them and you lose per-sender pricing - which is usually the most
valuable number in the document - and the sending parcels cannot carry their
own minus in their own chains.

**Worked shape (five senders, one receiver):**

    EVENT   mode: transacts · subject: the zoning lot (senders + receiver)
            functions: ENVELOPE + VALUE   (an event may answer more than one)
            term: perpetual - the severance is permanent
            anchor: document_id + page

    LEGS    | parcel | role     | direction   | quantity (SF) | consideration |
            | A      | sender   | -45,000 SF  | 45,000        | $100,000      |
            | C      | sender   | -67,000 SF  | 67,000        | $200,000      |
            | B      | receiver | +112,000 SF | 112,000       | $300,000      |

    BALANCE 45,000 + 67,000 = 112,000 SF        [OK]
            $100,000 + $200,000 = $300,000      [OK]

**Two corrections this pattern makes to a first attempt:**

1. **Direction is NOT the term.** "parcel A to parcel B" is the leg (role +
   direction), not the duration. A DEVR term is **perpetual** - development
   rights, once severed, do not come back on a clock.
2. **A leg carries TWO quantities and they must stay together**: the SF that
   moved and the money paid for it. Splitting them into an ENVELOPE event and
   a separate money event separates the numerator from the denominator, and
   $/SF becomes unverifiable. Keep them on the same leg; derivation divides.

**What this buys downstream:** per-sender pricing survives ($100,000/45,000 =
$2.22/SF from A; $200,000/67,000 = $2.99/SF from C - a real spread, and real
market information), the receiver's envelope account gets one clean +112,000,
each sender's chain gets its own minus, and the transaction count stays 1.

**And the rule that makes it safe:** if the instrument states a TOTAL and no
per-lot split, the legs carry the total with the split marked `unread` -
**pro-rata is never assumed** (G-016 family). An invented split prices five
lots wrongly in five different directions, each one looking precise.


## THE EVENT ROW - final shape (slot values in, sentence falls out)

    mode | subject | function | from | to | quantity | term

Seven CONTENT columns - the full table is eleven, adding `event_id | row` and
`doc_id | page | recorded | executed`. See THE EXTRACTION DATA TABLE below; an
earlier "seven columns, nothing else" here contradicted it and was wrong.
**The row IS the unit** - what I earlier called a
"leg" is just a row, and the extra word bought nothing.

**from / to** = the direction of the FUNCTION, not of the money.
`from` is who parts with what the function names; `to` is who receives it.
The doc-type authority hands you both (R-004): DEED = GRANTOR -> GRANTEE,
MTGE: the LIEN moves BORROWER -> LENDER and the CASH moves LENDER -> BORROWER,
which is **two rows on one event id, not one row with a chosen direction** - see
G-018. Reading R-004 as a single mortgage row is the error G-018 was written for.
For `observes` events nothing moved, so from/to are `n/a` - the same
three-state rule as quantity and term.

**Multidirectional = several rows sharing one document and one event id.**
Five senders to one receiver is five rows, not five events: the event id keeps
the transaction count at 1 and lets the balance check run across the rows.

**THE SUMMARY IS MECHANICAL - the columns generate the sentence:**

    [from] [function verb, per mode] [quantity] of [subject] to [to], [term].

| the row | the sentence it writes |
|---|---|
| transacts / 1843-17+51 / TITLE / $10 recited, <= $500 by stamp / fee simple absolute / PROPER REALTY CORP / ELISEO RAMIREZ | "Proper Realty Corp conveyed 165 and 169 Manhattan Avenue to Eliseo Ramirez in fee simple absolute for no more than $500." |
| transacts / 1843-17+51 / CAPITAL / $2,475,000 / maturity unread / BANK LEUMI TRUST COMPANY / MANHATTAN AVENUE DEVELOPMENT CORP | "Bank Leumi lent $2,475,000 against lots 17 and 51." |
| transacts / 1843-17+51 / ENCUMBRANCE / lien securing $2,475,000 / until satisfied / MANHATTAN AVENUE DEVELOPMENT CORP / BANK LEUMI TRUST COMPANY | "Manhattan Avenue Development Corp gave Bank Leumi a lien on lots 17 and 51 securing $2,475,000, until satisfied." |
| transacts / zoning lot / ENVELOPE+VALUE / 45,000 SF, $100,000 / perpetual / parcel A / parcel B | "Parcel A transferred 45,000 SF of development rights to parcel B for $100,000, permanently." |
| observes / 1843-17+51 / ENCUMBRANCE / unresolved - tenancies and arrears / runs with the land / n/a / n/a | "The deed recites existing tenancies and unpaid municipal charges running with the land, in amounts it does not state." |

**If the sentence cannot be written from the row, the row is wrong** - a
missing subject, an unread quantity dressed as a blank, or a function that
does not match the verb. That is the test: slot the values in, read the
sentence aloud, and if it does not say what the document says, fix the ROW,
never the sentence.



### G-018 - OPPOSITE-DIRECTION FUNCTIONS ARE SEPARATE ROWS

Found 2026-08-19 by the mechanical-summary gate, which produced the sentence
"Manhattan Avenue Development Corp granted Bank Leumi a $2,475,000 mortgage"
- legally the correct phrasing, and still WRONG as an event, because it reads
as the developer handing the bank money.

A mortgage moves TWO functions in OPPOSITE directions:

    CAPITAL      $2,475,000                lender   -> borrower   (money)
    ENCUMBRANCE  lien securing $2,475,000  borrower -> lender     (security)

One row cannot hold both, so a single row must pick one direction and silently
lie about the other. **One event_id, two rows.** Same structure as the
multidirectional air-rights transfer - the row is the unit, always.

This also fixes downstream: a satisfaction closes the ENCUMBRANCE row while the
CAPITAL row is what was repaid; an assignment moves both to a new holder. With
one merged row, neither can be closed cleanly.

**The rule:** if an instrument moves value one way and rights the other way,
that is two rows. Applies to mortgage, lease (money one way, occupancy the
other), and any air-rights sale (SF one way, dollars the other).

## THE EXTRACTION DATA TABLE - one shape, universal

Two tables, and only two. Everything read goes in the first; only what CHANGED
(or was recited) goes in the second.

### 1. CLAIMS - open, free-form, the evidence layer

    claim_id | doc_id | page | region | field | value | reader | conditions

Anything a reader saw: instrument form, exemption code, title number, officer
name, notary, address, recital text, tax stamp. Free-form ON PURPOSE - it must
absorb whatever any source prints without ever changing shape. Claims may
disagree; the distribution stays here forever.

### 2. EVENTS - closed, controlled, 11 columns, NEVER more

    IDENTITY     event_id | row
    PROVENANCE   doc_id | page | recorded | executed
    CONTENT      mode | subject | function | from | to | quantity | term

- **event_id + row** - a multidirectional transfer is many ROWS, one event_id.
  Transaction counts read event_id; economics read rows.
- **doc_id + page** - the anchor. No row exists without it.
- **recorded** (public clock, chains sort on this) and **executed** (the
  instrument own date). Both, because they measurably differ.
- **mode** - transacts / observes / signals. Controlled.
- **subject** - what the event is ABOUT: a parcel or an entity. A reference.
- **function** - one (or more) of the canonical eleven. Controlled.
- **quantity** - value + UNIT (money, SF, share, count), or a delta
  (FAR 2.0 -> 6.5). Bounded when not exact; `n/a` + reason, or `unread`.
- **term** - kind + value (estate, duration, maturity, condition). Same three
  states.
- **from / to** - direction of the FUNCTION. References. `n/a` when nothing
  moved.

### WHY IT IS UNIVERSAL

Every column is one of five types: a **controlled vocabulary** (mode,
function), a **reference** (subject, from, to, doc_id), a **measured value with
a unit** (quantity), a **typed duration** (term), or a **timestamp** (recorded,
executed). **No column is free text.** Free text is where new document types
force new columns; there is none here, so they cannot.

**The test: a new source adds ROWS, never COLUMNS.**

| document | mode | subject | function | from | to | quantity | term |
|---|---|---|---|---|---|---|---|
| deed | transacts | parcel | TITLE | grantor | grantee | $250,000 | fee simple absolute |
| mortgage | transacts | parcel | CAPITAL | borrower | lender | $2,475,000 | maturity 2016-01 |
| satisfaction | transacts | parcel | CAPITAL | lender | borrower | $2,475,000 discharged | ends the 1986 term |
| lease | transacts | parcel | OCCUPANCY | landlord | tenant | $5,000/month | 10 years |
| easement | transacts | parcel | ENCUMBRANCE | owner | utility | 10 ft strip | perpetual |
| air rights (x5 rows) | transacts | zoning lot | ENVELOPE + VALUE | sending lot | receiving lot | 45,000 SF, $100,000 | perpetual |
| UCC filing | transacts | **entity** | CAPITAL | debtor | secured party | $500,000 | until terminated |
| tax lien | transacts | parcel | CAPITAL | owner | City | $45,000 | until paid |
| DOB permit *(future)* | transacts | parcel | PERMIT | DOB | owner | 12 stories / 45,000 SF | until expiry |
| certificate of occupancy *(future)* | transacts | parcel | ASBUILT | DOB | owner | 20 units | perpetual |
| zoning amendment *(future)* | transacts | parcel | ENTITLEMENT | n/a | parcel | FAR 2.0 -> 6.5 | until amended |
| recital of existing tenancies | observes | parcel | ENCUMBRANCE | n/a | n/a | unresolved | runs with land |

Twelve document kinds across four sources and three eras. Same eleven columns.

### THE RULE THAT KEEPS IT UNIVERSAL

**Anything that does not fit a column is a CLAIM, not a new column.**
Instrument form, exemption code, title number, notary, officer, presenter,
recording fee - all of them are claims on the document. They are evidence for
the event row, and they are how derivation explains it later. The moment a
column is added to hold one source quirk, the table stops being universal.

**`lexicon.canon()` is the ONE normalizer** — register labels, legacy labels,
struck labels all resolve there. CONTEXT is deliberately NOT a function.

**Three kinds, never mixed:** FUNCTION (what changed → may become an event) ·
REGION (where to look → routes extraction, never an event) · REFERENCE (what
it points at → identifies, never changes). A cover page is not a function; a
metes description that IDENTIFIES is a reference — the same description in a
subdivision CHANGES the lot and is IDENTITY.

**Doc types:** the ACRIS CODE is canonical ("MTGE"), never the description
("MORTGAGE") — the authority table is `_doctype_codes.json` (126 types).











## G-029 - READ EVERY PAGE. SAMPLING IS NOT READING.

Login, 2026-08-19: *"you need to read everything to get the context to know the
events."* Five of 110 pages were read on the ZLDA and the output then asserted
*"the per-lot split is not stated in the document"* - a statement about a
document that had not been opened. That is G-028 broken by the very summary
that was supposed to enforce it.

**A page count is not a budget.** The rule that already governs documents -
never cap how many you read - governs PAGES identically. Definitions live 3
pages in, the allocation percentages live 30 pages in, the exhibits live 70
pages in, and a reader that samples finds none of them and reports their
absence as a property of the record.

⚠ Corollary:  may NEVER be summarised as "not stated". If pages
are unopened, the honest sentence is *"I have not read it"*, and the correct
next action is to read it - not to write a finding.


## ZLDA EXHIBIT D - the allocation schedule, and what it settles

Read 2026-08-19, `2010102601040006` p38. **The per-lot numbers are in an exhibit
70 pages after the grant.** Five pages of reading had reported them "not stated".

|  | lot 49 (Developer) | lot 53 (120) | lot 55 (124) | lot 56 (126) | total |
|---|---|---|---|---|---|
| lot area | 15,639 | 4,077 | 2,469 | 2,469 | 24,654 |
| rights generated | 156,390 | 40,770 | 24,690 | 24,690 | 246,540 |
| retained (kept) | n/a | 16,906 | 9,620 | 10,046 | 36,572 |
| excess (gave) | n/a | **23,864** | **15,070** | **14,644** | **53,578** |
| allocation after | 209,968 | 16,906 | 9,620 | 10,046 | 246,540 |
| pro rata after | 85.17% | 6.86% | 3.90% | 4.07% | 100% |

Self-checks, all exact: kept + gave = generated on every lot - FAR = 10.0 on
every lot - 156,390 + 53,578 = 209,968 - 209,968 / 246,540 = 85.17%.

### G-031 - THE BONUS SPLIT IS ARITHMETIC, NOT NEGOTIATION

    gave 53,578 / generated 90,150 = 59.43%   -> Developer's bonus share 59.4%
    kept 36,572 / generated 90,150 = 40.57%   -> Owner's bonus share    40.6%

The 59.4 / 40.6 percentages defined 30 pages earlier are simply the ratio of
rights given to rights generated. **Future bonus floor area splits in the same
proportion as the original sale.** Derivable, therefore checkable - a ZLDA whose
bonus split does NOT equal its gave/generated ratio is saying something unusual
and should be escalated.

### G-032 - THE COMPARABLE'S UNIT IS THE UNIT THE DOCUMENT PRICED

    \$5,000,000 / 53,578 SF = \$93.32/SF     <- ONE observation, deal level

The document prices the whole transfer once - tax stamps are paid once - and
**never splits the money per lot**. So a deal-level \$/SF is a real comparable;
a per-lot \$/SF is fabricated.

⚠ AND PRO-RATA BY SF IS WRONG HERE ANYWAY. Lot 53 gave 23,864 SF **plus** a
perpetual light-and-air easement; lots 55 and 56 gave rights only. Splitting
evenly by floor area prices lot 53's easement at zero. **When the sides gave
different things, there is no defensible split.**

**Rule: one priced transfer = one \$/SF observation.** Never divide a
consideration across parcels to manufacture more comparables.

### G-035 - NEVER AUTHOR A FILE THROUGH A HEREDOC. AGAIN.

Writing the night's handoff through a bash heredoc, a Windows path went in as

    "D:\\Commercial Real Estate Decoding\\00 Live Syncs\\..."

and came out carrying a literal NUL byte, because `\00` is an octal escape.
`cat -A` shows it as `^@`; **Read and Edit both render it as ordinary
whitespace**, so the file looked fine and the Edit tool could not match the
string to fix it.

This is the SAME trap already recorded against `\b` becoming 0x08 through the
same mechanism, which killed a guard for a full round. The standing rule from
that day reads *never author a regex through a heredoc - write a script file*,
and it was violated within hours of being re-read, because the rule was filed
under "regex" and this was "a path".

**Widen it: anything with a backslash goes in a SCRIPT FILE, not a heredoc, and
not an inline `-c`.** Regexes, Windows paths, escape sequences, all of it. Then
verify with `cat -A` or `s.count(chr(0))` - never by looking, because the tools
that display the file are the tools that hide the damage.

⚠ Two other heredoc casualties the same night, both silent: backticks inside a
`python -c` string were command-substituted by the shell, deleting `SAGE`,
`CERT` and `PARTY 1` from a finished sentence and leaving it grammatical; and a
`⚠` printed to a cp1252 console killed a gate mid-report (G-034). **The
shell is a second parser, and every one of these got through because the output
still looked like prose.**

### G-034 - PROVE A GATE FAILS BEFORE YOU TRUST IT TO PASS

`nav_verify.py` was written to gate the navigation phase, and it passed a clean
fixture on the first run. Then it was pointed at a fixture with four deliberate
defects - an unkeyed row, a missing document id, a missing endpoint, a resolved
(non-minting) url - and it found the first one, printed `FAIL`, and **died**:

    UnicodeEncodeError: 'charmap' codec can't encode character '⚠'

The warning glyph appeared only on the FAILING branch, and the console is
cp1252. So the gate ran clean forever and crashed the moment it had something to
say, **losing every check after the first failure** - exactly the output that
matters. A gate that dies when it fails is worse than no gate: no gate makes you
look, a crashing gate makes you look at a traceback instead of the finding.

The same test found a second defect. A coverage line printed `OK` beside
`20.00%`, because only the hard checks were being compared to their totals.
Nothing was asserted, and it wore a passing badge. **A coverage number must not
wear a gate's badge** - gates say OK/FAIL, coverage says `cov` and lets the
number speak.

**Rule: a guard is not written until it has been shown to FAIL on input built to
break it.** Passing a clean fixture proves the happy path and nothing else, and
the failing path is the entire reason the guard exists. Build the broken input
deliberately - one fixture per defect the guard claims to catch - and read the
output, not the exit code.

⚠ This is the standing rule *"a counter sitting at zero is a claim to verify,
not a result"* pointed at a different target. There the guard never fired; here
it fired and could not report. Both look identical from outside: a green run.

### G-033 - THE DOCUMENTS ALREADY CONTAIN TABLES

Exhibit D IS an event table - lot, area, generated, retained, given, share
after. The event table is not an imposition on the corpus; it is the **union of
the tables the documents already publish**. Where a document tabulates, copy its
columns before inventing any.

### PATTERN REGISTER additions

| pattern | fires on | fills | taught by |
|---|---|---|---|
| `EXHIBIT D` / `ALLOCATION OF DEVELOPMENT RIGHTS` | the per-lot schedule | every ENVELOPE quantity, per parcel | ZLDA p38 |
| `Lot Area` / `Total Development Rights Generated by Lot Area` / `Retained` / `Excess` | the five-row schedule shape | kept vs gave per parcel | ZLDA p38 |
| `Excluding Bonus Development Rights` (footnote) | the schedule EXCLUDES future bonus | do not treat the table as total | ZLDA p38 |
| `deemed modified to reflect any change` | the schedule is LIVE, not a snapshot | re-check on later upzoning/subdivision | ZLDA p38 |

### CONFLICT held open

Exhibit D computes at **FAR 10.0**; PLUTO shows **12.0** today. Not resolved,
not smoothed.



## N-10 - A SAMPLER LEFT DRIVING PRODUCTION

2026-08-19, Login: *"what is this 978,538 doc thing? why not just work the
navigation when it lands?"*

`overnight.py` was written before the navigation table existed and picks its own
work: `--pool 6000` parcels, band `--lo 8 --hi 300` documents, deepest first.
That was right for learning fetch mechanics on rich parcels. Left in place for
production it means:

    non-SI parcels          1,157,407
      inside the band         899,965
      OUTSIDE the band        257,442   <- 22%, never acquired, silently
    docs on non-SI parcels 26,234,912
    the run's actual pool      978,538  <- 3.7% of documents, 0.5% of parcels

⚠ **THE BAND EXCLUDES BY SHAPE, AND NOTHING REPORTS IT.** A parcel with 4
documents or 400 is not acquired and never appears in a failure count - the run
finishes clean, reporting only what it chose to attempt. This is the same
failure as auditing a filter by reading its own output.

**Rule: a selection heuristic that was correct for a pilot must be re-derived
before it drives production, and any bound it imposes must be printed as a
denominator, not left implicit.**

⚠ Corollary on the handoff: driving acquisition from the parcel table is NOT a
departure from navigation-driven. Both come from the same specification DB, and
the nav table was built from it twenty minutes earlier. **The CSV is the
artifact for products and audit; the database is the query surface.** Re-parsing
11 GB of CSV to recover a parcel list that an indexed table answers instantly
would be slower and no more correct.

## N-11 - A LUMPY WRITER MEASURED OVER A SHORT WINDOW READS AS DEAD

2026-08-19, 21:51. `night_chain.py` decided the Richmond pull had finished and
started the next stage - a second `rc_detail_pull.py --run --conc 80` on the
same worklist. It had not finished. It was at 80%:

    pull_alive()   size of rc_detail.jsonl, compared 20 seconds apart
    the pull       commits in lumps, minutes apart
    result         healthy pull declared dead; TWO pulls, 160 connections,
                   ~70,000 duplicate fetches at one source

⚠ **THIS IS THE TRAP ALREADY WRITTEN DOWN, IN A NEW PLACE.** The acquisition
note says never measure throughput under 15 minutes because the ledger moves in
~4 lumps per minute. The same lumpiness makes a *liveness* test lie, and the
liveness test was written as if growth were continuous.

**Rule: never infer liveness from the output of a process that commits in
lumps. Ask the process table - a running process IS the process.** Keep a
growth check only as a fallback for a writer outside your process table, and
give it a window long enough to span a commit lump (300s, not 20s).

**Why it did not become damage:** the writes append one flushed record at a
time, so nothing interleaved; landing is keyed, so duplicate records are
no-ops; and the redundant sweep runs LONGER than the real pull, so the stages
after it still start in the right order. **Wasteful, not wrong** - but the
same defect ahead of a non-idempotent stage would have corrupted it. The fix
belongs in the check, not in the tolerance of what follows it.

## N-12 — TWO CONTROLLERS EACH DOING THE RIGHT THING, TWICE

The 4am routine ends with a navigation rebuild, because a sync that lands
documents and does not rebuild the table has changed nothing anyone can act on.
The night chain rebuilds navigation the moment the routine's TSV changes,
because acquisition must see what the sync landed. **Both are correct in
isolation and together they rebuild the same 11 GB table twice** — 24 minutes,
and acquisition restarts 24 minutes late, which is the single thing the night
was scheduled around.

⚠ **THE TSV ORDERING SAVED IT FROM BEING WORSE.** `_finish()` writes the TSV
AFTER the navigation stage, so the chain waits until the rebuild has finished
rather than starting a second one on top of it. Had the TSV been written first,
two processes would have been streaming to the same csv path concurrently. The
duplication was luck-limited to waste; the ordering that limited it was not
designed for that job and should not be relied on again.

**The fix is not in either controller.** Either one could be told to stand down,
and then a change to the other silently removes the rebuild entirely. The fix
is in the thing being asked to do the work:

    nav_build.py --force        rebuild unconditionally
    nav_build.py                rebuild ONLY if the specification is newer
                                than the table it produced

`nav_build` reads `parcel_spec.db` and nothing else, so if the db is older than
the csv there is no input that could produce a different row. **A full rebuild
that cannot change anything is refused and says so.** Subset builds
(`--bbl` / `--limit` / `--out`) always run.

⚠ **THE `-wal` FILE IS PART OF THE INPUT — AND `-shm` IS NOT.** SQLite writes
land in `parcel_spec.db-wal` before checkpointing, so the db file's own mtime
can be hours stale while data is arriving. Comparing against the db alone would
have skipped rebuilds that were genuinely needed — the exact failure the guard
was written to prevent, reintroduced by the guard. **Take the max of db and
`-wal` only.**

⚠ CORRECTED WITHIN THE HOUR, BEFORE IT EVER RAN. The first version also
included `-shm`. That file is a shared-memory index touched whenever ANY
connection opens — including a read-only one, including nav_build's own — so
the guard would have seen a newer source almost every time and **never fired at
all.** It would have reported a fix while changing nothing, which is worse than
the duplication it replaced: the 24 minutes would still be spent and the
bootcamp would say they were not.

**Every write reaches db or `-wal`; only connections reach `-shm`. Compare
against what records WRITES, not against what records ATTENTION.**

**Proven to fire before being believed** (five cases, both directions):
csv newer → refuses · db newer → builds · **wal newer, db stale → builds** ·
`--force` → builds · no table yet → builds.

**Rule: when two schedulers can each trigger the same expensive job, make the
JOB idempotent rather than making one scheduler defer.** A deferral encodes an
assumption about the other scheduler that nothing checks; an idempotent job is
correct no matter who calls it or how often.

## N-13 - A RESTART MUST NOT ERASE A REFUSAL

`overnight.py` opened with:

    if STOP.exists():
        STOP.unlink()

which is right for a control flag and catastrophic for a refusal. The refusal
path writes `refused <when>` into that same file and prints *"Delete _STOP to
resume later"* - a sentence that assumes a PERSON reads it. But `night_chain`
restarts acquisition after the 4am sync, and an unconditional unlink would have
**deleted the refusal and resumed against the source that refused us**, hours
later, with nobody told. The standing rule is *on a refusal: stop; do not retry,
do not rotate anything.* The code honoured it for exactly as long as nothing
restarted.

**One file carried two meanings and only one of them was safe to clear.** The
fix reads the file before deleting it: `refus`/`denied` in the contents means
decline to start, print the stop file verbatim, exit 2. Anything else is a
control flag and is cleared as before.

    CASE A  refusal stop   -> exit 2, contents printed, _STOP LEFT ON DISK
    CASE B  control stop   -> cleared, run proceeds

⚠ AND PROPAGATE THE CODE. `main()` was called bare, so a `return 2` would have
exited 0 and reported a clean run to whatever launched it - a refusal made
invisible by the very guard that caught it. `sys.exit(main() or 0)`.

⚠ **THE TEST ITSELF WAS THE NIGHT'S BIGGEST RISK.** Proving this required
running `overnight.py`, which takes a pid lock; a copy still alive when the
chain launched acquisition would have made the REAL run exit as "a second copy"
and cost the entire night. It was survivable only because `only_one()` verifies
the recorded pid is both alive AND running the same script, so the dead test's
pid file was ignored. **Before testing a guard on a live path, work out what
your test leaves behind** - the leftover, not the guard, is what breaks the run.
Check the process table and delete the pid file yourself rather than trusting
that something else will.

## N-15 - mtime CANNOT TELL "FINISHED" FROM "ABANDONED" OR "IN PROGRESS"

The N-12 currency guard - *skip a full rebuild when the specification is older
than the table it produced* - ran for the first time on 2026-08-20 at 06:00 and
printed:

    navigation table is CURRENT - legal_instrument_navigation.csv
      built 0 min ago, 5,374 MB
      specification unchanged since - nothing could differ

**The table was 5,374 MB of an expected 11,268 MB and another process was still
writing it.** A file being written has the freshest mtime there is, so the
guard's evidence for "up to date" was maximally satisfied by the one state that
means the opposite. Had that run been the only one, a half-written csv would
have been left in place as the live navigation table.

Two separate defects, and both matter:

**1 - ORDER. Ask "is someone writing it?" BEFORE "is it up to date?"** The lock
added the same morning would have refused correctly, but `_already_current()`
was checked first and returned True, so `_claim_lock()` never ran. A cheap check
placed ahead of a correct one silently replaces it.

**2 - THE WITNESS. Key currency on a COMPLETION MARKER, never on the artifact's
mtime.** `_nav_build.done` is written as the last act of a successful full
build. No marker means rebuild - which covers the first run, a crash mid-write,
and a kill, all of which leave a recent-looking file that no mtime comparison
can distinguish from a finished one.

    csv fresh, NO marker         -> rebuild   <- the case that fired
    marker newer than db         -> current
    db newer than marker         -> rebuild
    csv touched, marker still ok -> current    <- csv mtime now irrelevant

⚠ THIS IS THE PROJECT'S RECURRING SHAPE IN A NEW PLACE: a check that reports
success because it looked at the wrong evidence. The refusal detector looked in
raw bytes for a phrase that markup split (2026-08-06). The parcel-key guard
matched a backspace and read zero (RULE 10). This one asked a timestamp a
question timestamps cannot answer. **When a guard's answer is "recent", ask what
else is recent** - and prefer a witness that only the successful path can write.

## N-14 - AN HOUR IS NOT A DEADLINE (the night's worst bug, and it was mine)

`night_chain.py` step 6 waits for the 4am sync and gives up if it never comes:

    if now.hour >= 6:
        log("06:00 reached without a sync record - continuing anyway")
        break

It reached step 6 at **23:28**. `23 >= 6` is true. It logged *"06:00 reached"*
at 23:30, ran steps 7-8 immediately, and exited. The comparison reads like
"after 6am" and means "any hour numbered 6 or higher" - which is every hour from
06:00 to 23:59, i.e. most of the day.

**What it cost:**

    23:28:41  START acquisition until 03:50      <- step 5, correct
    23:30:41  "06:00 reached" -> nav-live -> START acquisition until 23:00
    result    TWO drivers, EIGHT workers, 160 connections against an ~80 ceiling,
              both walking the SAME 1,150,020-parcel worklist in the SAME
              deepest-first order - identical work, twice, at double the load

and the 4am handoff the whole chain existed to perform was skipped.

⚠ **`only_one()` DID NOT SAVE IT.** The second driver started while the first
was alive and registered. Its guard catches `NoSuchProcess`/`AccessDenied` and
falls through to writing its own pid - so under load, the duplicate-prevention
degrades to duplicate-permission. A guard whose failure mode is "allow" must say
so out loud; this one passed silently.

**Rule: never compare a bare `.hour` to decide whether a moment has passed.**
Compute an absolute `datetime` ONCE, up front, and compare against that. The
same applies to `.minute`, `.weekday()`, and anything else that wraps.

⚠ **AND TABULATE IT.** The replacement (`night_watch.py`) had the identical bug
one line lower - its give-up time was derived from `acq_end` instead of from
`now`, so a 05:30 start would wait for the NEXT day's six o'clock and sleep
through the sync it exists to catch. It was found by printing the computed
deadlines for SEVEN start times instead of only the one I happened to be
starting at. **A time calculation is not verified by the case you are in.**

⚠ Diagnosis note: the duplicate was invisible for two minutes because
`/tmp/acq.log` is TWO FILES. Python resolves `/tmp` to `C:\tmp`; Git Bash
resolves it to the user Temp directory. `chain.log` went to the bash one (shell
redirect) and `acq.log` to the Windows one (Python `open`), so tailing the
"same" path showed a stale file from two hours earlier and acquisition looked
silent. **On Windows, never write a log to a bare `/tmp/...` path from Python.**

## NAVIGATION BUILD 2026-08-19 - what shipping the table taught

24,037,915 rows, 11.20 GB, 23.7 min. UNKEYED 0.
Every lesson below cost a real failure tonight.

### N-1 - A DEAD PATH FAILS SILENTLY AND LOOKS LIKE SUCCESS

`rc_detail_land.py` and `rc_urls.py` both hardcoded `D:/acris/...`, deleted in the
morning restructure. Neither would have errored - they would have run to
completion and landed NOTHING. ~20 more scripts still carry the same string.
**Rule: a path constant outside `corpus_paths` is a silent-failure waiting for a
restructure.**

### N-2 - THE SAME FACT LIVES IN DIFFERENT PLACES PER SOURCE

Image state: Richmond publishes it on the detail page; **ACRIS does not store it
at all** - NULL on every ACRIS row, with the truth in a flat list of 174,142
imageless ids. A builder reading only the column reported the entire ACRIS side
as `unknown`, and the completeness check could never close.
**Rule: before trusting a column, check whether the other source keeps that fact
somewhere else entirely.**

### N-3 - CODES MEAN DIFFERENT THINGS PER DOCUMENT TYPE

ACRIS party_type is `1`/`2`. For a DEED, 1 is GRANTOR/SELLER; for an INIT it is
DEBTOR; for an ASST it is ASSIGNOR/OLD LENDER. Stored raw the column is
meaningless. Resolved from `_doctype_codes.json`, ACRIS's own 126-type table -
never a hand map.

### N-4 - CASE VARIANTS SPLIT A VOCABULARY IN HALF

Richmond writes `Mortgagor` 12,307 times and `MORTGAGOR` 4,786 times. One role,
two spellings; a GROUP BY halves every role and nothing errors. Same failure
shape as doc_type code-vs-description.

### N-5 - THE FALLBACK KEY WAS 7% OF THE CORPUS, NOT A ROUNDING ERROR

Projected from a 300k sample: ~535,000 party-keyed documents.
Actual across 24M: **1,710,599** - UCC filings and federal liens with no parcel.
Plus 49,806 with neither parcel nor party (PAT, MISC, MAPS).
**Without the party and document fallbacks, 7.3% of the corpus fails the gate.**
⚠ And the small sample understated it 3x - a reminder that a 1% slice does not
measure a population that is unevenly distributed by era and type.

### N-6 - DICT LOADS DIE, MERGE JOINS DO NOT

The first builder loaded every parcel link and every party into dicts and timed
out on a ONE-PARCEL test. The corpus is 24M documents with more links and far
more parties; 16 GB will not hold it. All three tables are indexed on
document_id, so ordered scans merge in constant memory.
**Rule: at corpus scale the join strategy is the design, not an optimisation.**

### N-7 - ONE ROW PER DOCUMENT, ALWAYS

Richmond: 2,426,404 documents against 2,891,086 parcel links. Per-link rows
inflate 19% and break every count taken off the table. Multi-key documents carry
their keys semicolon-separated in ONE row.

### N-8 - DERIVE, DO NOT STORE

`pdf` is a pure function of the id; `endpoint` is a pure function of the id;
era is the id prefix (`FT_` film, `RC_` Richmond, numeric CRFN); borough is the
first digit of the BBL. None are stored twice. Acquisition flips a STATE, it
never writes a path back - which is what keeps
`total - (present + pending + imageless) = 0` readable from one table with no
join.

### N-9 - THE MINTING URL, NOT THE RESOLVED ONE

Richmond mints a fresh token per request; a resolved URL carries a timestamp and
signature and is stale within minutes. Storing the minting URL is why this table
does not go out of date.

## RANDOM-DOCUMENT RUN 2 - `2012050100986004` (Queens 16233/1002)

Second cold pick, different type (AGMT), 74 pages held. **The table produced no
new columns and no new event rules.** Every finding was about ACQUISITION and
READING SCOPE - which is the convergence signal: the model stopped moving and
the failures moved to the pipeline.

### L-7 - THE COVER'S PAGE COUNT IS NOT THE FILE'S PAGE COUNT

    cover page states     PAGE 1 OF 53
    Document Page Count   51        (51 + 2 cover pages = 53, consistent)
    pages held            74

Not over-acquisition. **Page 54 is a second cover page** - `SUPPORTING DOCUMENT
COVER PAGE`, same document_id, declaring *"SUPPORTING DOCUMENTS SUBMITTED: 255
MORTGAGE TAX EXEMPT AFFIDAVIT - Page Count 10"*.

A document_id can therefore hold **two or more page series**: the recorded
instrument, then supporting documents, each with its own cover page and its own
count. The cover's count describes the INSTRUMENT ONLY.

⚠ **Any completeness check of the form `held == count + 2` fires a false alarm on
every document that has supporting papers.** The correct check walks the cover
pages and sums the series.

### L-8 - THE 255 AFFIDAVIT IS THE MISSING WITNESS FOR CONSOLIDATIONS

This document reads `Mortgage Amount \$2,600,000.00` with
`Taxable Mortgage Amount \$0.00` and `Exemption: 255` - the consolidation
signature, and the exact shape that broke R-003 (tax validates principal).

**The affidavit that JUSTIFIES the exemption is in the file, at pages 55+.** It
is the document that says why no new money was advanced. Every consolidation
read so far has treated the \$0 taxable as an unexplained anomaly; the
explanation was appended to the same PDF the whole time and was never opened,
because reading stopped at the instrument's page count.

⚠ Consequence for G-022: the closing/opening arithmetic has a WITNESS available
on any 255-exempt consolidation. Read it before asserting new money.

### L-9 - READING SCOPE IS A SETTING, AND IT WAS WRONG

Extraction had been implicitly scoped to "the instrument". The correct scope is
**every page under the document_id, across every series**. A reader that stops
at the instrument silently drops affidavits, RPT forms and exhibits - the places
where exemptions, considerations and quantities are explained rather than merely
stated.

### Correction to the ZLDA finding

The ZLDA gap (116 stated, 110 held) still stands as SHORT - supporting documents
would add pages, not remove them. But the accounting note there was too simple
and is amended: a page-count comparison is only valid once every cover page in
the file has been walked.

## RANDOM-DOCUMENT RUN 2026-08-19 - `2003041601495006` (Brooklyn 1982/7)

Picked at random from the by-parcel tree, read cold, type code ignored. Seven
pages, all read. Six lessons, one of them a confirmation.

### L-1 - G-022 CONFIRMED TO THE PENNY

Exhibit B lists four mortgages consolidated by a CEMA of even date:

    1,494,203.89   unpaid balance, First Building Loan Mtge (orig 1,495,739.00, 1998)
      279,923.62   unpaid balance, Substitute First Acquisition Loan Mtge (1998)
       37,255.38   unpaid balance, First Project Loan Mtge (1998)
      288,617.11   NEW Multifamily Mortgage, dated the same day
    ------------
    2,100,000.00   "to form a single lien of \$2,100,000.00"   EXACT

G-022 says new money = `opening - sum(closings)`. Here that is
2,100,000.00 - 1,811,382.89 = **288,617.11**, which independently equals the
principal of the new mortgage stated on the same page. **Two routes, one
number.** A single CAPITAL row at the \$2,100,000 face would have reported 7.3x
the actual new borrowing.

### L-2 - QUANTITY CARRIES A ROLE, NOT JUST A UNIT

This one document states at least five different kinds of dollar amount:

    original principal        \$1,495,739.00
    unpaid principal balance  \$1,494,203.89
    new principal             \$  288,617.11
    consolidated lien         \$2,100,000.00
    consideration paid        NEVER STATED - "FOR VALUABLE CONSIDERATION"

Conflating any two produces a wrong number, and the last one is the trap: the
price the assignee paid is **not in the record at all**. An assignment's
quantity is the PRINCIPAL ASSIGNED, never the price paid.
**Rule: quantity = value + unit + ROLE.** Not a new column - a required
qualifier inside the slot, exactly like the unit.

### L-3 - ONE DOCUMENT CAN CONTAIN A WHOLE CHAIN, AS `observes` ROWS

Exhibit B item 2 recites FIVE successive events on one 1991 mortgage - made by
Ft. Greene Assets to National Westminster Bank (\$1,000,000, 1991); assigned by
Fleet Bank (fka NatWest) to KMA Equities (1997); further assigned to Chase
Community Development Corp (1998); severed and modified into a Substitute First
Acquisition Loan Mortgage (1998); assigned to CPC (2003) - each with its own
date, parties and reel/page.

**Twelve years of lineage, recoverable from one 7-page document.** Every one of
them is `observes` - the assignment did not re-do them. Written as `transacts`
they would inject a phantom \$1,000,000 origination into 1991.
⚠ This is the mode column preventing double-count for the third time.

### L-4 - THE BORROWER IS NOT ON THE COVER PAGE

ACRIS PARTIES lists only ASSIGNOR (CPC) and ASSIGNEE (Freddie Mac).
**GRAND AVE. REALTY LLC - the borrower, the entity whose debt this is -
appears nowhere in the index.** Any party search for the borrower on this
document fails. Documents over indexes, again.

### L-5 - HANDWRITING CARRIES THE BATCH LINEAGE

The sibling document IDs exist ONLY as handwritten annotations on the exhibit:
*"Simultaneously Doc #2003041601495001"* through `...005`. Five pointers that
tie this assignment to its CEMA and its four component assignments, written in
pen. **A reader that skips handwriting loses the entire batch linkage** - and
the batch is what makes the arithmetic in L-1 checkable at all.

### L-6 - SUFFICIENCY DRIVES WHAT TO READ NEXT

The CAPITAL event has two parties and a principal but **no maturity** - the
terms live in the Consolidation Agreement, a different document
(`2003041601495005`). Under the sufficiency threshold the event is INSUFFICIENT
for runoff, and the threshold names the next document to open. That is the
threshold earning its keep: it does not just grade the event, it schedules work.

### Scope note

Cover states PAGE 1 OF 7, page count 5, 7 pages held - **complete**, unlike the
ZLDA. Lots: the cover shows 7 and 1 with a continuation; the body states lots
**1, 7, 69 and 77**. Four lots, one document.



## G-030 - SIMPLICITY IS THE PRODUCT

Login, 2026-08-19: *"beauty is in simplicity where anyone can understand how a
complex document boils down to very simple foundations."*

A 110-page zoning lot development and easement agreement:

    Three lots on West 25th Street gave their air rights to lot 49.
    Extell paid \$5,000,000.
    Lot 53 also gave up light and air over its back 20 feet.
    The four lots became one zoning lot.
    The sellers kept 40.6% of any future bonus - and all of it once
    the hotel opens.

Five sentences. **If the summary is long, the decoding is not finished.**

⚠ The machinery - eleven functions, three modes, slots, thresholds, patterns -
exists to PRODUCE those five sentences. It is never the output. A reader who has
to understand the machinery to understand the property has been handed the
scaffolding instead of the building.

**Rule: every event summary is one sentence. Every document summary is under
six.** Anything longer is a signal that a quantity is unread, a role is
unresolved, or the reader is narrating method instead of facts.

## THE DIRECTION OF WORK - patterns come from READING, the table forms around them

Login, 2026-08-19: *"this is why llm matters over pure extraction. you create
the guards and rails by reading docs to know what is important, and then we
build your extraction and the table around it via pattern. the bootcamp tells us
what is important via pattern and the table forms around those patterns."*

**This is the governing principle of 03 Extractions, and it was being run
backwards.** A table was designed, then documents were fitted into it - which is
why the rows came out thin and why every second document forced a rule change.

    WRONG   design the table -> read documents -> force them into it
    RIGHT   read documents -> find what matters -> record the PATTERN
            -> the table and its vocabularies form around the patterns

⚠ `lexicon.py` ALREADY LEARNED THIS THE HARD WAY. Its CAPITAL patterns carry the
note *"REBUILT FROM MEASURED TEXT"* - the original four were deed-era phrasing
and fired on 16% of MORTGAGES, the instrument whose entire purpose is debt. The
fix was not better theory, it was **counting words in 208 real financing
documents**. Every pattern in that file that works came from reading; every one
that failed came from assuming.

### THE THREE ROLES, AND WHY THE MODEL IS ONLY ONE OF THEM

    DISCOVERY    a model reads whole documents and finds what matters.
                 Expensive, slow, irreplaceable. This is the bootcamp.
    ENCODING     what it found becomes a PATTERN with a measured yield.
                 This is the register below, and it feeds lexicon.py.
    PRODUCTION   patterns run over the corpus. Cheap, deterministic, at scale.
                 A model is called only where a pattern misses or conflicts.

**The model is the instrument that finds the rule, not the machine that applies
it 17 million times.** That is the entire economic argument for the bootcamp,
and it is why time spent reading one document end to end is not a detour.

### THE PATTERN REGISTER - what reading produced, 2026-08-19

Each pattern names the document that taught it, what it fires on, and the slot
it fills. None of these could have been invented at a whiteboard.

| pattern | fires on | fills | taught by |
|---|---|---|---|
| `Owner hereby conveys ... the Subject Development Rights` | ZLDA operative grant | ACT -> ENVELOPE, transacts | ZLDA p8 |
| `grants ... a perpetual easement for light, air and view` | easement grant | ACT -> ENCUMBRANCE | ZLDA p8 |
| `as set forth on Exhibit ___` | **the quantity lives elsewhere** | routing: open that exhibit | ZLDA pp7, 9, 12 |
| `NN.N% of any ... Bonus Development Rights` | allocation split (59.4 / 40.6) | qty_role = allocation_share | ZLDA pp6-7 |
| `Exemption: 255` + `Taxable Mortgage Amount \$0.00` | consolidation, no new money | mode/qty_role, and go read the affidavit | Queens AGMT p1 |
| `SUPPORTING DOCUMENT COVER PAGE` | a SECOND page series under one doc id | reading scope | Queens AGMT p54 |
| handwritten `Simultaneously Doc #...` | batch lineage pointers | prior_doc references | Bklyn ASST p6-7 |
| `assigned in the unpaid principal balance of \$X by Assignment ... from A to B` | recited prior assignment | an `observes` row | Bklyn ASST p6-7 |
| `which above N mortgages were consolidated ... to form a single lien of \$X` | the closing set and the opening | G-022 arithmetic | Bklyn ASST p7 |
| `filed under the name ___ as filing number NNNNNNNNN` | **a DOB job number inside an ACRIS document** | cross-source join | ZLDA p11 |

⚠ THE LAST ROW IS THE ARGUMENT IN ONE LINE. Nobody designing an ACRIS schema
would put a DOB filing number in it. Reading page 11 found one, and it links the
air-rights purchase to the job it was bought for. **Patterns found by reading
reach places a designed schema cannot.**

### THE TABLE MOLDS ONLY IN BOOTCAMP, THEN IT FREEZES

⚠ CORRECTED SAME DAY. An earlier version of this section called the table "a
residue" that keeps forming. Login: *"this needs to scale still ... in bootcamp
the table molds around what COMMON data-to-extraction patterns occur, but then
the pull is DIRECT INTO THAT TABLE once designed."*

A table that keeps forming cannot be pulled into at scale, because every change
re-extracts the corpus. **Bootcamp's job is to make the table STOP MOVING.**

    BOOTCAMP    read documents until pattern discovery saturates on the COMMON
                cases. The table molds. Expensive, finite, front-loaded.
    FREEZE      the table is DESIGNED and fixed. Columns and vocabularies close.
    PULL        extraction writes DIRECTLY into the frozen table, at scale.
                No discovery, no molding, no model in the loop.
    ESCALATE    what no pattern matches goes to a QUEUE - never to a new column.

### "COMMON" IS THE LOAD-BEARING WORD

The table molds around what occurs COMMONLY, not around everything seen. Mold
around every rarity and the table never freezes and the pull never starts. A
rare construction is not a schema problem - it is an escalation, and it stays a
claim until enough instances make it common.

### THE EXIT CRITERION - measurable, not a feeling

**K consecutive random documents that force ZERO new columns and ZERO new
vocabulary members.** Escalations are allowed and expected; schema changes are
not. Progress so far:

    run 1  Bklyn ASST  2003041601495006   forced 3 changes   (qty_role, others)
    run 2  Qns  AGMT   2012050100986004   forced 0           <- streak 1
    run 3  ZLDA        2010102601040006   in progress

Reading resumes at run 3 page 12 of 110. The streak resets on any schema change.

### THE PRICE OF A POST-FREEZE CHANGE

After the freeze, adding a column or a vocabulary member means **re-extracting
every document already pulled**. That cost is what the exit criterion is
protecting, and it must be quoted out loud whenever a change is proposed - the
same discipline G-020 puts on a twelfth function.

### THE TEST OF THE TABLE

Not elegance. **Does every COMMON pattern in the register have a slot, and does
every slot have common patterns that fill it?** A slot nothing fills is
speculation; a common pattern with nowhere to go is why the table is not frozen
yet.

## THE EXTRACTION FILTER - read only what bears on a function

Login, 2026-08-19: *"we should only extract if it has implications on a
function."* Adopted. **The eleven functions ARE the filter.** This is the
charter's own rule turned into a reading instruction: *if nothing changes,
there is no function and no event.*

### The test, applied to every value on the page

**Name the function it bears on, and say which of two roles it plays.**
If neither can be named, it is not extracted.

    MOVER     it CHANGES the function        -> becomes part of an EVENT ROW
    WITNESS   it EVIDENCES the function      -> becomes a CLAIM
    neither   -> NOT EXTRACTED

⚠ THE WITNESS ROLE IS NOT OPTIONAL, AND READING THE FILTER WITHOUT IT IS THE
TRAP. A \$0.55 transfer-tax stamp changes nothing - it is a stamp. It is also
the ONLY thing that bounds the price on a \$10-recital deed. Read narrowly as
"does this change a function", the filter throws away the single most valuable
mark on the page. The test is **bears on**, not **changes**.

Worked, on the 1981 deed:

| value | function | role | kept? |
|---|---|---|---|
| "does hereby grant and release" | TITLE | mover | yes - the event |
| "unto ... FOREVER" | TITLE | mover | yes - the term |
| \$0.55 tax stamp | TITLE | witness | yes - bounds the quantity |
| unanimous stockholder consent | TITLE | witness | yes - evidence for internal-vs-external |
| officer LEONARD SOLOMON, President | TITLE | witness | yes - the signature test |
| notary name and county | - | - | **no** |
| recording fee | TITLE | witness | yes - corroborates the stamp |
| cover-page routing marks | - | - | **no** |
| boilerplate covenants | - | - | **no** |

### This also corrects what CLAIMS are

Earlier the claims table was described as *"every reading, kept with its
conditions"* - a vacuum cleaner. Wrong. **Claims are WITNESSES for functions.**
That makes the table smaller, purposeful, and actually useful: every claim
exists because some function needs evidence, and a claim with no function
attached is a claim that should never have been written.

### The stopping rule extraction never had

**A page is finished when the eleven functions have each been ASKED of it** -
not when the reader runs out of text. Most pages answer none, some answer one,
a few answer three. The procedure in THE FUNCTION SPECIFICATION is the same
eleven questions, and running them is what makes a page done.

### The trade-off, stated because it bites later

Filtering at read time means a value nobody asked for today is NOT captured,
and answering a new question later requires RE-READING the page. That is
accepted: the documents are held permanently, re-reading is possible, and the
alternative - extract everything - never finishes.

⚠ **The filter is only as stable as the function set.** It is safe today
because the eleven were attacked for completeness and minimality and held
(G-020). If a twelfth function is ever admitted, **every page already read
under this filter must be re-read for it** - the backward re-check rule. That
cost is the real price of adding a function, and it should be quoted whenever
one is proposed.

## THE METHOD - SLOT FILLING, NOT DOCUMENT CLASSIFICATION

⚠ THE REGRESSION THIS FIXES. 2026-08-19, Login: *"you have lost the ability to
extract as effectively as we had before ... we need a way that isnt doc type
dependent where data can extract where it slots and together it forms an
event."* Extraction had become: read document -> decide its type -> derive the
row from the type. That is CLASSIFICATION, and it fails three ways - it cannot
touch a source with no document type (portal feed, zoning text, tax roll), it
imports the type's assumptions before any evidence, and it produces thin rows
because the type already 'answered' everything.

⚠ THE TOOLING ALREADY WORKED THIS WAY. `lexicon.py` fires FUNCTION patterns on
CLAUSES, never on doc types - *"role words are deliberately absent ... they say
WHO, not WHAT CHANGED."* The method below is not new; it is the method the
lexicon was built for, which extraction drifted away from.

### 1. READ INTO SLOTS - no type consulted, ever

Every page yields values. Each value goes to the slot it fits, with its anchor.
Nothing is interpreted at this stage.

    PARTY       a named person or entity, exactly as written
    PLACE       a parcel reference - BBL, block/lot, address, metes
    MONEY       an amount, with its currency and its witness (recital? stamp?)
    MEASURE     a quantity with a unit - SF, FAR, units, stories, feet
    DATE        a point in time, with WHICH clock (executed / recorded / effective)
    TERM        a duration, estate or condition - "forever", "until paid", maturity
    ACT         an operative phrase - "does hereby grant", "secures to", "releases"
    CONDITION   a qualifier - "subject to", "provided that", "excepting"

A slot fill is a CLAIM. It has an anchor and it may conflict with another fill
for the same slot. Conflicts are kept, never resolved by preference.

### 2. COMPOSE - the slots make the event, the type never enters

    ACT       -> mode      (transacts / observes / signals) AND function
    PLACE     -> subject   (or PARTY, when the subject is an entity)
    PARTY     -> from / to
    MONEY + MEASURE -> quantity
    TERM      -> term

**The ACT is the load-bearing slot.** It is the only one that says something
CHANGED, and it carries both mode and function. A page full of parties, money
and places with no operative act is a recital - `observes` at best, and often
just claims.

### 3. THE TWO THRESHOLDS - "what is needed to know"

**EXISTENCE threshold - is this an event at all?**
An ACT that resolves to a function, plus a subject. That is the spine gate:
mode, subject, function, none of them `unread`. Below it, the fills stay
claims. This threshold is the same for every source, forever.

**SUFFICIENCY threshold - does this event answer what it is for?**
Per function, and this is the one that was missing. An event can EXIST and
still be USELESS, and saying so is the honest outcome - not dropping it, and
not fabricating the gap shut.

| function | sufficient when it also has | insufficient means |
|---|---|---|
| TITLE | 2 parties, an estate, a money value or a bound | the transfer is known, the price is not |
| CAPITAL | 2 parties, a principal, a maturity or condition | the debt is known, its runoff is not |
| ENVELOPE | 2 places, a MEASURE in SF or FAR, a money value | **no $/BSF can be computed** |
| ENCUMBRANCE | the burdened place, what is restricted, duration | the burden is known, its extent is not |
| OCCUPANCY | 2 parties, a rent, a duration | tenancy known, economics not |
| ENTITLEMENT / PERMIT / ASBUILT / VALUE / COST | *(undefined - the five with no detector; see THE FUNCTION SPECIFICATION)* | |

**Insufficiency is a REPORTED STATE, not a silent one.** The ZLDA of 2010-10-14
is the worked case: the ENVELOPE event exists - operative transfer, both
parties, both places, \$5,000,000 off the stamps - and is INSUFFICIENT, because
the instrument states the floor area by FORMULA and never as a number. It is a
real event that cannot produce a comparable, and that sentence is the correct
output.

### 4. WHY THIS IS SOURCE-INDEPENDENT

Slots are things any record has. A DOB NOW filing has PARTY, PLACE, DATE,
MEASURE and an ACT ("permit issued"). A zoning text amendment has an ACT, a
CLASS as its place, and a MEASURE. A tax roll has PLACE, MONEY, DATE and no ACT
at all - which is exactly right, because a tax roll observes rather than
transacts. **Nothing in the method asks what kind of document it is.**

The document type stays where it belongs: a CLAIM, useful for routing which
pages to read first and for the summary sentence, never an input to the row.



## THE TABLE - as posed 2026-08-19, after the day's lessons

Two tables. CLAIMS is open and holds WITNESSES. EVENTS is closed and holds
MOVERS. Everything below is EVENTS.

### As read - eight content columns, in summary order

    mode | subject | function | effect | from | to | quantity | term

    SPINE      mode - subject - function - effect   never `unread`.
                                           Below it: not an event.
    DIRECTION  from - to                   `n/a` when nothing crossed
    MEASURE    quantity - term             may be unfilled, in five states

⚠ `effect` JOINED THE SPINE ON 2026-08-19 (RUN 3). `function` says WHICH KIND
of thing, `mode` says WHETHER it moved, and neither says WHAT HAPPENED TO IT.
Without it a termination is indistinguishable from a grant - and **20.7% of the
corpus (4,977,173 documents across 17 doc types) is a release.** It sits in the
SPINE, not the MEASURE, because a row that cannot say whether the thing began
or ended is not an event that can be believed.

### As stored - the same row, typed so metrics can compute

    IDENTITY     event_id · row_no
    PROVENANCE   doc_id · doc_type · page · recorded · executed
                 (doc_type ADDED 2026-08-20, login decision: carried from the
                 index as CONTEXT, never extracted from the page. With it on
                 every row, type -> function co-occurrence becomes a MEASURED
                 ledger as extraction runs, and Resolution chains on counted
                 pairings instead of assumed ones. Backwards it is a tripwire:
                 functions far outside the type's measured distribution mean a
                 source mislabel or a genuinely unusual instrument - surface
                 both. Same rule as every vocabulary: counted, never assumed,
                 denominator mandatory.)
    SPINE        mode · subject_type · subject · function · effect
    DIRECTION    from_type · from · to_type · to
    MEASURE      qty_value · qty_unit · qty_role · qty_state
                 term_kind · term_value · term_state

⚠ HONEST COUNT. "Eleven columns and it never grows" was about CONCEPTS, and the
concepts have not grown all day. Typing them out is a different count - because
"53,578 SF" and "\$2,100,000 unpaid principal balance" are strings, and no
metric can compute on a string. The decomposition adds no meaning; it makes the
meaning already there addressable.

### The three vocabularies that make it universal

    mode          transacts · observes · signals
    function      the canonical eleven, via lexicon.canon()
    effect        creates · transfers · modifies · releases
    subject_type  parcel · entity · class

`class` is what lets a zoning text or a tax-code change in as ONE event, fanned
out to member parcels at 05 Derivations, never copied per-parcel at extraction.

### from_type / to_type are DECIDED BY THE FUNCTION

Not judged per document. TITLE · CAPITAL · OCCUPANCY -> **party**.
ENVELOPE -> **parcel** (rights are appurtenant to the land).
ENCUMBRANCE -> parcel, or party when held in gross.
ENTITLEMENT · PERMIT · ASBUILT -> **agency** on one side.
IDENTITY -> n/a, nothing crosses.

### qty_role - the lesson that cost the most to learn

One document stated five kinds of dollar (L-2). The role is mandatory:

    original_principal · unpaid_balance · new_principal · consolidated_lien
    consideration · recited · bounded · assessed · asking

**An assignment's quantity is the principal assigned, never the price paid** -
and the price paid is usually not in the record at all.

### The five states, for qty_state and term_state

    value           read and known
    n/a + reason    the document genuinely has none
    unread          the page was READ and the value could not be recovered
    not attempted   the page was never opened               (G-028)
    unavailable     the page does not exist at the source   (D-8a)

These are never interchangeable, and each names a different owner of the gap:
`unread` is a claim about the DOCUMENT, `not attempted` a claim about the
READER, `unavailable` a claim about the SOURCE. Only the middle one is work
this system can still do - which is why coverage must report them apart.

### Two thresholds, both computed from the row

    EXISTENCE     spine filled          -> it is an event
    SUFFICIENCY   per-function fields   -> it can answer what it is for

Insufficiency is REPORTED, never fixed by guessing - and it schedules the next
read, which is how the CAPITAL row on `2003041601495006` named the Consolidation
Agreement as the next document to open.

### Worked - the random document, `2003041601495006`

    event_id     ASST-2003-1982
    doc/page     2003041601495006 · p3 · recorded 2003-08-18 · executed 2003-02-26

    row 1  transacts · parcel · Bklyn 1982 lots 1,7,69,77 · CAPITAL
           from party THE COMMUNITY PRESERVATION CORPORATION
           to   party FEDERAL HOME LOAN MORTGAGE CORPORATION
           qty  2,100,000.00 · USD · consolidated_lien · value
           term — · — · unread        (maturity is in doc ...005)
           SUFFICIENCY: INSUFFICIENT - no maturity. Next read: ...005

    row 2  transacts · parcel · Bklyn 1982 lots 1,7,69,77 · ENCUMBRANCE
           from parcel/party CPC (lien held in gross) -> FHLMC
           qty  2,100,000.00 · USD · consolidated_lien · value
           term until satisfied · condition · value

    rows 3-14  `observes` — the twelve years of recited lineage from Exhibit B
           (1991 NatWest origination through the 2003 assignments), each with its
           own date, parties and reel/page. **`observes` is what stops the 1991
           \$1,000,000 becoming a phantom origination.**

### What is deliberately NOT a column

Document type · instrument form · statutory citations · notary · recording fee ·
exemption code · presenter · title number. All CLAIMS. The moment one becomes a
column, the table stops being universal - and the summary can still pull the
instrument form from claims when the sentence needs it.

## SUBJECT vs PARTIES - the parcel never moves, the FUNCTION moves

Login, 2026-08-19: *"i am caught on subject and parties since a parcel
(subject) can transfer between party 1 and 2?"* The knot, and the untying.

**A parcel is never what moves.** 165 Manhattan Avenue did not go anywhere in
1981. What moved was TITLE TO IT. The parcel is the stage; the function is the
actor; the parties are the two ends the actor moved between.

    subject   what the event is ABOUT     - the stage. Never moves.
    function  WHAT moved                  - the actor.
    from/to   the two ENDS it moved between

So the deed reads: *subject* 165 Manhattan Ave, *function* TITLE,
*from* PROPER REALTY CORP, *to* ELISEO RAMIREZ. The parcel sits still and the
title crosses it.

### THE RULE THAT REMOVES THE GUESSING

**The function decides what KIND of thing can stand at the ends.** This is
fixed, not judged per document, because it follows from what the law lets each
function attach to.

| function | attaches to | so from/to hold |
|---|---|---|
| TITLE | a person - someone owns it | **parties** |
| CAPITAL | a person - someone owes it | **parties** |
| OCCUPANCY | a person - someone possesses it | **parties** |
| ENVELOPE | **the land** - development rights are appurtenant to a zoning lot | **parcels** |
| ENCUMBRANCE | usually the land (dominant/servient estate); a party when held in gross | **parcels**, or a party |
| IDENTITY | the land itself | **n/a** - nothing crosses |
| ENTITLEMENT | the land, granted by an authority | **agency -> parcel** |
| PERMIT | granted by an authority to an owner | **agency -> party** |
| ASBUILT | certified by an authority about the land | **agency -> parcel** |
| VALUE / COST | asserted by someone about the land | **party -> parcel**, or n/a |

For `observes` nothing crossed, so from/to are `n/a` regardless.

### WHY THE ZLDA FELT WRONG

The 2010 ZLDA extraction wrote `from = the two Sabet LLCs`, `to = the Extell
LLC` - parties. But ENVELOPE attaches to LAND: the floor area belongs to lots
53, 55 and 56, not to the LLCs, and it lands on **lot 49** - which the row never
recorded at all. The receiving PARCEL fell out of the table entirely.

Corrected shape:

    subject   zoning lot 800 (49 + 53 + 55 + 56)
    function  ENVELOPE
    from      lots 53, 55, 56
    to        lot 49

### THEN WHERE DO THE PARTIES GO?

**Into claims, as witnesses, with their roles** - which is exactly what the
extraction filter already says: a value is a MOVER or a WITNESS, and the
function decides which. When the function attaches to land, the signing parties
are witnesses. When it attaches to a person, they ARE the row.

Nothing is lost - 120-22 W 25 STREET LLC and 124-26 W 25 STREET LLC stay
attached to the event as the parties in interest, and "who sold the air rights"
is still answerable. They simply are not the ends of the movement, because the
rights did not belong to them; they belonged to their lots.

⚠ This is also why `subject` and `from` can be the SAME on an encumbrance row -
the burdened land is both what the event is about and the side that gives up
something. That repetition is a signal, not noise.

## SUBJECT HAS THREE TYPES - parcel, entity, CLASS

Login, 2026-08-19: *"no matter the source whether a document, tax code, zoning
resolution, live application portal, etc. it is data. and the question is if we
can distill the mode, subject, from, to, function, term, quantity."*

Testing that against the four source kinds named found ONE gap, and it is in
`subject`, not in the column set.

| source kind | example | distils to | note |
|---|---|---|---|
| document | deed | transacts - parcel - TITLE - $1 - perpetual - A -> B | the settled case |
| live application portal | DOB NOW job filed, not approved | **signals** - parcel - PERMIT - scope - pending | this is exactly what `signals` is FOR: intent, not yet fact. Issuance later is `transacts` |
| zoning resolution | ZR text amendment | transacts - **CLASS** - ENTITLEMENT - the delta - until amended | subject is every lot the text reaches, not one parcel |
| tax code | RPTT rate change, 421-a statute | transacts - **CLASS** - CAPITAL - the rate - effective range | same shape |

### THE FINDING

**`subject` admits three types: `parcel`, `entity`, `class`.**

Parcel and entity were already carried. **Class was not**, and without it a
rule-level source has nowhere to land - which is precisely Login's earlier point
that *"a zoning resolution feed is technically an event where on this amended
resolution event this property is now eligible for this."*

A class-subject event is written ONCE and fans out to its member parcels at
**05 Derivations**, never at extraction. Writing it per-parcel at extraction
would copy one fact 1.16 million times and lose the fact that it is one rule.

⚠ This is the same shape as the three ways a candidate function dissolves
(G-020): what looked like a missing column was a missing SUBJECT TYPE. The
column set did not move. **Two of the three dissolve-routes have now been used
in anger** - listings resolved to a mode, rule-sources resolve to a subject.

### COLUMN ORDER, AND WHY THE SUMMARY IS NOT A COLUMN READ

    mode | subject | function | from | to | quantity | term

⚠ THE SUMMARY IS TEMPLATED, NOT READ LEFT TO RIGHT. 2026-08-19 the sentences
were generated by reading the columns in order and they came out wrong three
ways. **The proof that no column order fixes this is Login's own corrected
sentence:**

    "bank leumi lent $2,475,000 of capital against lots 17 and 51
     as [instrument] maturing 2016"

That sentence runs from -> verb -> quantity -> function -> subject ->
instrument -> term. As a COLUMN order it would be terrible: subject buried in
the middle, mode reduced to a verb, and `to` absent entirely. Natural language
needs grammar, not a fixed traversal. So:

- **Column order serves SCANNING** - spine 1-3, direction 4-5, measure 6-7, so
  a reader groups by subject and function and the tiers stay contiguous.
- **The summary is generated from a TEMPLATE PER FUNCTION**, which may reorder
  freely and may pull the instrument form from CLAIMS. The instrument is not an
  event column, but the sentence needs it to sound like a sentence.

### THREE SUMMARY RULES, EACH FROM A SENTENCE THAT FAILED

**G-027 - A TRIAL AGAINST A PRIOR DECODE IS NOT A TRIAL.**
2026-08-19: the eleven-column table was "trialled" on ZLDA
`2010102601040006` by reading `LOT49_EVENTS.md`, a decode already made, while
the 47-page PDF sat on disk. Every function, mode and quantity had already been
judged by the legacy file, so the table could only agree with itself.
**A test that cannot fail proves nothing.** Worse, another file's page cites
were presented as anchors. A trial reads PAGES. If the pages were not opened,
the word "trial" may not be used.

**G-028 - `unread` AND `not attempted` ARE DIFFERENT STATES.**
Same failure: the ZLDA row was marked `split: unread` when the exhibit had
never been opened. `unread` means **the page was read and the value could not
be recovered** - it is a measured claim about the document. `not attempted`
means nothing was looked at, and it is a claim about ME. Collapsing the second
into the first reports my inaction as a property of the record. The three-state
rule becomes FOUR: a value - `n/a` + reason - `unread` - `not attempted`.
⚠ EXTENDED to five by D-8a: `unavailable` - attempted, and the source does not
have the page. See the five-state table above; this entry is kept as written
because it records what the fourth state cost to learn.

**G-024 - NEVER ABBREVIATE OR PARAPHRASE A PARTY.** Written: *"Bank Leumi lent
MADC $2,475,000"*. Login: *"MADC is not natural. that doesnt make sense and is
not decoded."* An initialism invented at summary time is an undecoded token -
it appears nowhere in the record and cannot be joined to anything. Use the name
exactly as recorded: MANHATTAN AVENUE DEVELOPMENT CORP.

**G-025 - THE SUMMARY MUST NAME THE FUNCTION.** *"lent $2,475,000"* hides that
this is CAPITAL; *"$2,475,000 of capital"* states it. The function is the
dimension that makes the event mean something - a summary that omits it has
thrown away the reason the row exists.

**G-026 - A SUMMARY MUST CARRY THE UNREAD FLAGS. THIS IS THE DANGEROUS ONE.**
Written: *"Lots 53, 55 and 56 passed 53,578 SF of envelope to lot 49 for
$5,000,000, perpetually."* Login: *"very bad since we have no idea what the sf
split is, the $ split is."* The ROW was honest - one aggregate row marked
`split: unread` under G-021. **The SENTENCE laundered it into a false claim**,
reading as though three lots each passed a known share.

⚠ A summary is a LOSSY RENDER of a row, and the flags are exactly what must not
be lost. If a value is bounded, the sentence says bounded. If a split is unread,
the sentence says the split is not stated. **G-021 was written and then broken
within the hour by the sentence that rendered it** - which is why the render is
now governed, not left to prose.

### THE THREE CORRECTED SENTENCES

    transacts - 123 Street - TITLE - LOGIN WILSON -> OPUS 5 - $1 - fee simple
      "LOGIN WILSON conveyed title to 123 Street to OPUS 5 in fee simple
       absolute, for $1."
      (not "...for $1, forever" - the estate IS the term, so name the estate)

    transacts - lots 17+51 - CAPITAL - BANK LEUMI TRUST COMPANY OF NEW YORK
      -> MANHATTAN AVENUE DEVELOPMENT CORP - $2,475,000 - maturity 2016
      "BANK LEUMI TRUST COMPANY OF NEW YORK lent MANHATTAN AVENUE DEVELOPMENT
       CORP $2,475,000 of capital against lots 17 and 51 by mortgage,
       maturing 2016."

    transacts - zoning lot 800 - ENVELOPE - lots 53, 55, 56 (split: unread)
      -> lot 49 - 53,578 SF / $5,000,000 - perpetual
      "Lots 53, 55 and 56 TOGETHER passed 53,578 SF of envelope to lot 49 for
       $5,000,000 by zoning lot development agreement, perpetual. **The per-lot
       SF and dollar split is not stated in the document**, so no per-lot rate
       can be computed - $93.32/SF is a blended rate across all three."

## THE THREE TIERS OF THE ROW - why it stays concise

Login, 2026-08-19: *"mode, subject, function ... and then term and quantity are
the details in data form which allows conciseness."* That is the structure, and
it is not cosmetic - the tiers have different rules.

    SPINE      mode - subject - function     WHAT HAPPENED.  Always controlled
               - effect                      vocabulary. NEVER `unread`.
    MEASURE    quantity - term               THE DETAIL, IN DATA FORM. May be a
                                             value, `n/a` + reason, or `unread`.
    DIRECTION  from - to                     WHICH WAY. `n/a` when nothing moved.

### THE SPINE GATE

**If any of mode, subject, function or effect cannot be determined, there is no event.**
It stays a claim. This is the single hardest gate in extraction, and it is what
stops half-read documents from entering the graph wearing an event's clothes.

The measures are allowed to be unread because a document can genuinely change
the world without stating an amount. The spine cannot: a change you cannot
name, about something you cannot name, in a way you cannot name, is not a
change you observed.

### WHY THIS IS WHERE CONCISENESS COMES FROM

The spine is three controlled words, so it is sortable, groupable and countable
without reading anything. The measures are data, not prose, so they add
precision without adding length. The summary sentence is then just the row read
aloud - spine, measure, direction - which is why it can be generated
mechanically and why a sentence that will not form proves the ROW is wrong.

Chains group on the SPINE. Metrics compute on the MEASURE. Lineage walks the
DIRECTION. Three tiers, three uses, one row.

## THE COMPLETENESS TEST - why eleven, and how a candidate dissolves

Login, 2026-08-19: *"when we did the artifact, we couldnt find anything more
than 11 or a way to distill down."* The set was already attacked for both
completeness and minimality. It is therefore not open season - a twelfth
function must survive the test below, and none has.

### Why a function is the right unit

*"Each of these functions determines why an event matters, since it changes the
shape of the context."* A function is a DIMENSION OF THE PROPERTY'S STATE. An
event matters exactly because it moves one. That is why the eleven are nouns,
and why "cover page" is not one of them - it moves nothing.

### The frame - five questions, eleven answers

    1  WHAT IS IT?                    IDENTITY
    2  WHO HAS WHAT IN IT?            TITLE - OCCUPANCY
    3  WHAT BINDS IT?                 ENCUMBRANCE - CAPITAL
    4  WHAT MAY BE, AND WHAT IS, BUILT?   ENVELOPE - ENTITLEMENT - PERMIT - ASBUILT
    5  WHAT IS IT WORTH, AND WHAT DOES IT COST?   VALUE - COST

### THE THREE WAYS A CANDIDATE DISSOLVES

Every proposed twelfth function so far has failed as one of these. Run all three
before proposing anything.

1. **It is a COMBINATION of two functions** - and the table already handles that,
   because function lives on the ROW, not the document.
2. **It is a MODE, not a function** - a listing is not a new function, it is
   `signals` on TITLE or OCCUPANCY.
3. **It is a SUBJECT, not a function** - `subject` already accepts a parcel OR an
   entity. Anything about WHO rather than WHAT is a subject.

### Candidates attacked 2026-08-19 - all eleven dissolved

| candidate | dissolves as |
|---|---|
| ground / contamination / brownfield | ENCUMBRANCE (restricts regardless of owner) + COST (remediation is an exogenous input) + IDENTITY (location) |
| flood zone, waterfront | ENCUMBRANCE + IDENTITY |
| soil, bearing capacity | COST - "inputs a model needs that no property record holds" |
| entity spine / party | **SUBJECT, not function.** An LLC name change alters no dimension of the parcel |
| rent regulation | ENCUMBRANCE - it restricts regardless of who owns it |
| zoning lot composition (ZLDA) | ENVELOPE (what may be built as of right) + ENCUMBRANCE (members are bound) |
| tax abatement (421-a, ICAP, J-51) | ENTITLEMENT (benefit granted, with a term) + CAPITAL (obligation reduced) |
| litigation, lis pendens | CAPITAL via DISTRESS; TITLE where it clouds title |
| listings, offers, marketing | **MODE** - `signals`. Not a function |
| operating expenses, NOI, cap rate | COST + VALUE |
| insurance | COST |

### RETRACTED - the two "losses" flagged earlier today

Both were flagged as gaps in the 14 -> 11 collapse. Both were wrong.

- **PARCEL -> IDENTITY was NOT a loss.** "The physical lot, its ground and its
  surroundings" distributes cleanly: restrictions on the ground are ENCUMBRANCE,
  engineering and remediation numbers are COST, location is IDENTITY. Environmental
  remediation has a home after all - it is an encumbrance with a cost.
- **PARTY -> TITLE understated it, but PARTY is still not a function.** It is a
  SUBJECT. The entity spine is served by `subject = entity`, which the event table
  already supports. `_CANON`'s PARTY -> TITLE applies only to the POA case, where
  the instrument really does grant authority over an interest.

**The set stands at eleven.** Rule G-020: a proposed twelfth function must be
shown NOT to be a combination, a mode, or a subject, in writing, before it is
entertained.

## THE DEFINITIONS - Login's table, canonicalised (2026-08-19)

⚠ SOURCE OF TRUTH. These one-liners are Login's own, supplied 2026-08-19. They
are better than the ones being improvised against, because each answers a
QUESTION ABOUT THE PROPERTY rather than naming a legal category. Fourteen labels
collapse to the canonical eleven through `lexicon.canon()`, which already carries
the map. Never re-derive it here.

| Login's label | definition (verbatim) | canonical |
|---|---|---|
| IDENTIFY | which parcel is this, and what are its identifiers | IDENTITY |
| PARCEL | the physical lot, its ground and its surroundings | IDENTITY ⚠ see loss 1 |
| TITLE | who holds an interest, **and in what priority** | TITLE |
| PARTY | who the humans and entities are | TITLE ⚠ see loss 2 |
| ENCUMBER | **what restricts this land regardless of who owns it** | ENCUMBRANCE |
| ENVELOPE | what may be built here **as of right** | ENVELOPE |
| ENTITLE | permission to **change the rules**, and its conditions | ENTITLEMENT |
| PERMIT | permission to do the work | PERMIT |
| ASBUILT | what legally exists here now | ASBUILT |
| OCCUPY | who is in it, and on what terms | OCCUPANCY |
| CAPITAL | financing, its terms, and its stress | CAPITAL |
| DISTRESS | arrears, liens, litigation, enforcement | CAPITAL |
| VALUE | what it is worth - to the city, or to the market | VALUE |
| COST | **inputs a model needs that no property record holds** | COST |

### What these definitions FIX

- **ENCUMBER settles the CAPITAL boundary outright.** "Regardless of who owns
  it" IS the burden-the-land test. No further test needed.
- **ENVELOPE says "as of right."** So a variance is NOT envelope - relief from
  the rules is ENTITLE. The quantity/permission split holds, and now it has
  authority rather than inference.
- **TITLE includes PRIORITY**, which was missing. Priority is what makes a first
  mortgage first, and it is the whole point of a subordination.
- **COST is NOT money spent.** It is "inputs a model needs that no property
  record holds" - construction cost per SF, cap rates, market rents. The
  exogenous bucket. Recording a job cost off a permit filing is not COST; it is
  a quantity on the PERMIT row.

### OPEN RULINGS - both now CLOSED by this table

1. **Landmark designation -> ENCUMBRANCE.** It "restricts this land regardless
   of who owns it." ENTITLE is *permission to change the rules* - something an
   owner seeks. A designation is imposed, not sought.
   ⚠ This closes AGAINST the recommendation made earlier the same day, which
   argued ENTITLEMENT on a public-regime-vs-private-holder test. That test was
   invented; this definition is the authority. Rule G-019.
2. **HPD violation -> CAPITAL**, via DISTRESS ("arrears, liens, litigation,
   **enforcement**"). Not OCCUPANCY. Confirms the revised call.

### TWO LOSSES IN THE COLLAPSE - **RETRACTED, both dissolved (G-020)**

Superseded by THE COMPLETENESS TEST above. Kept for the record only.

#### superseded

1. **PARCEL -> IDENTITY loses the physical lot.** IDENTIFY is *identifiers*
   (BBL, lot number); PARCEL is *"the physical lot, its ground and its
   surroundings"* - soil, topography, waterfront, adjacency. Folding both into
   IDENTITY means environmental remediation, contamination and adjacency have no
   home. 05 Derivations explicitly asks "is there environmental remediation."
   Unresolved: either IDENTITY absorbs ground conditions, or a twelfth function
   is owed.
2. **PARTY -> TITLE is right only for the POA case** that `_CANON` cites
   (`POA: TITLE - signals - subject=entity`). "Who the humans and entities are"
   is the ENTITY SPINE, which 04 Resolutions needs to track a company across the
   market. Routing it through TITLE makes every entity fact look like an
   ownership fact. Unresolved.

⚠ DO NOT TRIAL THE TABLE BEFORE THE DEFINITIONS ARE WRITTEN. The looseness of
2026-08-19 came from running documents against names that had no definitions.
Definitions first, then the trial, then the failures are real failures rather
than reader improvisation.

## THE FUNCTION SPECIFICATION - assign by rule, not by feel

⚠ WHY THIS SECTION EXISTS. 2026-08-19: landmark designation, HPD violation and
tax assessment were each assigned by feel, one document at a time. The cause was
not carelessness - `lexicon.py` says it in its own CANONICAL block: **"five have
no detector yet and every read of them is `unread`, never 0%."** Six functions
carry a definition, patterns and measured coverage. Five are names in a list.
The five undefined ones are exactly the three that were guessed. There was no
rule to follow, so one got invented per document.

### The six that are defined (verbatim from lexicon.py, the authority)

| function | means | status | measured |
|---|---|---|---|
| IDENTITY | which parcel this is - STATED (observes) or CHANGED (transacts) | rebuilt | description = IDENTITY only when it ALTERS; otherwise `metes` reference |
| TITLE | title passes, is confirmed, or is clouded | **weak** | DEED 46% of 50 - highest volume after CAPITAL, least proven on its own documents |
| OCCUPANCY | who is in it and on what terms - the leasehold, not the fee | proven | - |
| ENCUMBRANCE | a burden is created, released, or modified | proven | devr 12/25 - 128 hits ("subject to" REMOVED: inflated 128 -> 220) |
| ENVELOPE | buildable envelope changes - rights severed, transferred, merged | proven | devr 21/25 - 1,104 hits |
| CAPITAL | an obligation is secured, assigned, or discharged | proven | MTGE 59% - SAT 61% - ASST 65% - AL&R 55% - AGMT 85% - DEED 0/50 |

### The five that are NOT defined

    ENTITLEMENT   PERMIT   ASBUILT   VALUE   COST

No `means` line, no patterns, no coverage. Until each is written and measured
against real documents, **a read of these five is `unread`, never 0%** - the
lexicon's own rule. Absent is a claim that has not been earned.

### The ordered procedure - all eleven, every document

Not first-hit-wins. Documents legitimately fire several; a mortgage fires two.
If none fire, it is not an event - it is a claim, and it stops at claims.

     1  did the parcel itself change (boundary, merger, subdivision, unit lots)?  IDENTITY
     2  did the fee pass, get confirmed, or get clouded?                          TITLE
     3  did possession short of the fee change?                                   OCCUPANCY
     4  is an obligation created, secured, assigned, or discharged?               CAPITAL
     5  is a burden on the land created, released, or modified?                   ENCUMBRANCE
     6  did buildable quantity move or change?                                    ENVELOPE
     7  did public permission change?                                             ENTITLEMENT
     8  was authorization to do work granted, renewed, or expired?                PERMIT
     9  was physical reality certified?                                           ASBUILT
    10  was worth asserted with no obligation attached?                           VALUE
    11  was money spent producing the asset stated?                               COST

### The four boundaries that bite (one test each)

- **CAPITAL vs ENCUMBRANCE** - does it obligate a PERSON or burden the LAND? A
  mortgage does both, which is why G-018 holds: the debt obligates the borrower,
  the lien binds whoever owns the lot. A tax lien is likewise both. An easement
  burdens the land and obligates nobody - ENCUMBRANCE alone.
  ⚠ The earlier test "does it have a payoff amount" was WRONG and would have
  collapsed the mortgage back to one row.
- **ENVELOPE vs ENTITLEMENT** - a QUANTITY or a PERMISSION? Envelope is buildable
  amount (SF, FAR as a number); entitlement is what is allowed (district,
  variance, special permit). A rezoning changes both - two rows, same shape as
  the mortgage.
- **VALUE vs the price on a deed** - a sale price is the QUANTITY on the TITLE
  row, never its own VALUE event, or every deed doubles. VALUE fires only for
  worth asserted independently of a transfer: assessment, appraisal, asking price.
- **PERMIT vs ASBUILT** - authorization to DO (future, expires) vs certification
  of what EXISTS (past, permanent). Permit is PERMIT; a CO is ASBUILT; a TCO is
  ASBUILT with a term.

### OPEN - **CLOSED 2026-08-19 by Login's definitions table above (G-019)**

Kept for the record; do not act on it. Landmark = ENCUMBRANCE, HPD violation = CAPITAL.

#### superseded reasoning

Two assignments are live judgment calls awaiting a ruling. Until ruled, mark the
row `unread` with the reasoning attached; do NOT pick one silently.

1. **Landmark designation.** Called ENCUMBRANCE on 2026-08-19. By the tests above
   it is ENTITLEMENT - a public regime changing what may be done, with no private
   holder who could release it. Recommendation ENTITLEMENT, restriction expressed
   in `term`. High volume in the LIC territory, so it must not stay open long.
2. **HPD violation.** Called OCCUPANCY on 2026-08-19; likely wrong. A violation
   obligates the owner to cure and carries a penalty - CAPITAL, plus ENCUMBRANCE
   where it attaches as a lien. OCCUPANCY should stay reserved for who is in the
   building and on what terms.

Once ruled: write the definitions into `lexicon.py` so names and meanings live in
ONE place, then measure patterns for the five undefined functions before any of
them is reported as anything but `unread`.

## HOW ANY SOURCE REACHES THIS TABLE (the distillation)

Every source invents its own words for the same handful of moves. The words are
the source's business; they are never ours. **A document type is a CLAIM, not a
schema.**

### The three questions

Point them at any record from any source. If all three answer, it is an event.
If they do not, it is a claim and it stops at the claims table.

    1. Did the world change, or is someone just saying so?   -> mode
    2. About what, and in what respect?                      -> subject + function
    3. How much, how long, and which way?                    -> quantity + term + from/to

### The discard rule

**If a field only means something inside one source's vocabulary, it is a
claim, not an event field.** That single rule is what keeps the table at eleven
columns forever. Discarded from the event table, kept forever as claims:
instrument form names, statutory citations, boilerplate covenants,
acknowledgments and notaries, recording fees, cover-page routing, exemption
codes, permit sub-types, agency form numbers.

### Jargon, translated

| what the source calls it | what it actually is |
|---|---|
| bargain and sale deed with covenant against grantor's acts | transacts / TITLE / price / fee simple / grantor -> grantee. The covenant is a claim. |
| CEMA (consolidation, extension, modification) | closes two CAPITAL rows, opens one, extends the term, $0 new money |
| satisfaction of mortgage | closes an ENCUMBRANCE row; the CAPITAL row is what was repaid |
| assignment of mortgage | same CAPITAL and ENCUMBRANCE rows, new `to` party |
| UCC-1 financing statement | identical row, except `subject` is an ENTITY, not a parcel |
| zoning lot development agreement (DEVR) | ENVELOPE moves lot -> lot; VALUE moves the other way; N rows, one event |
| certificate of occupancy | ASBUILT, agency -> owner |
| notice of property value | VALUE, one tax year |
| landmark designation | ENCUMBRANCE, perpetual, agency -> parcel |
| zoning text amendment | ENTITLEMENT, quantity is a delta (FAR 2.0 -> 6.5) |
| broker listing | **signals** / asking price / no from-to. Mode is what lets listings sit in the same table without contaminating facts. |

### Onboarding a new source - the only per-source artifact

1. List every record type the source publishes (its jargon).
2. Answer the three questions for each. Failures are claims, not events.
3. Write ONE mapping table - source type name -> mode + function - and store it
   in that source's own md. Never in code. Never as new columns.
4. Run the mechanical-summary gate on 20 records. If a plain sentence cannot be
   written from a row, the MAPPING is wrong, not the table.

One universal table, plus a small dictionary per source. That is the whole
design. A new source adds ROWS and a DICTIONARY - never a column.

## GUARDS & RAILS — one entry per miss, with its teaching document

**G-001 · Two canon maps existed and disagreed.** (Taught by: lexicon.py vs
functions_vocab.py, found 2026-08-19 at bootcamp start — before any document
was read.) functions_vocab.py maps CAPITAL→DEBT; lexicon.py canonizes CAPITAL
and does not know DEBT. RULE: only `lexicon.canon()` normalizes; any other
mapping file is history, not law.

**G-002 · The $10 recital is never the price.** (Carried in from the DEVR
graduation, measured: a 500,000x error.) Price comes from the cover page
transfer-tax stamps (RPTT/RETT); the index says $0 for whole classes. RULE:
never write a recital amount as consideration; derive from stamps; check
stamp arithmetic respecting exemption codes (a $0-tax HECM with Exemption 280
is CORRECT, not broken).

**G-003 · Never prime a reader.** (Measured: a wrong OCR candidate primed the
VLM into repeating it twice.) RULE: a reader may receive a REGION pointer,
never a candidate VALUE for the field it reads.

**G-004 · One look is never a reading.** (Measured: `732441` twice at one
scale vs `732491` five times across scales.) RULE: vary size AND crop;
agreement across varied conditions verifies; the distribution stays on the
claims forever.

**G-005 · Quantities live in exhibits, not grants.** (DEVR lesson: the SF
quantity is in an EXHIBIT, not the granting clause.) RULE: route quantity
extraction to schedules/exhibits; the grant names the act, the exhibit names
the number.

**G-006 · Anchor on the LINE's region, not the page.** (A page-level gate
once built a BBL from a reel number.) RULE: every claim gates on its anchored
line region; facts refuse to exist without document_id + page.

## GOLD SET

One folder per teaching document under `..\Gold Set\` — the document + its
known-correct extraction. Every bootcamp change re-runs it; nothing
previously correct may regress.

## RUN LOG

Bootcamp run stamps append to `..\Run Log.md`.

---

# RANDOM-DOCUMENT RUN 3 — `2012121901163001` (Queens 1266/1, TL&R, 4 pp)

Cold pick, `random.seed(20260819)`, uniform across the three store shards
weighted by file count (20 / FT / BK), bounded to documents already on disk.
Read complete: 4 of 4 pages. **This run FORCED A NEW COLUMN.** The freeze
criterion resets.

    TERMINATION OF ASSIGNMENT OF LEASES AND RENTS
    by THE PRUDENTIAL INSURANCE COMPANY OF AMERICA, a New Jersey corporation
    premises 79-02/79-10 34th Avenue, Block 1266 Lot 1, Queens
    "the certain Assignment of Leases and Rents dated as of July 28, 2005 and
     recorded ... on September 22, 2005 under CRFN 2005000533673 ...
     IS HEREBY CANCELLED AND TERMINATED"

## R3-1 — ⚠ THE TABLE CANNOT SAY THAT SOMETHING ENDED

Written in the frozen columns, this document produces:

    transacts | Queens 1266/1 | ENCUMBRANCE | Prudential | ? | n/a | 2012-12-06

which is **indistinguishable from Prudential TAKING an assignment of leases and
rents on the same parcel.** The row asserts the exact opposite of what the
document says, and nothing in it is wrong — the columns simply cannot carry the
fact.

**`function` says WHICH KIND of thing. `mode` says WHETHER it moved. Neither
says WHAT HAPPENED TO IT.**

### The new column

    effect     creates    the instrument brings the thing into being
               transfers  it moves between holders, unchanged
               modifies   its terms change, it survives
               releases   it is extinguished

`effect` is orthogonal to `mode`: a `transacts` event can create, transfer,
modify or release. It is orthogonal to `function`: every one of the eleven can
be created and released. Four members, each observed, none dissolvable into the
others.

⚠ **DO NOT ENCODE EFFECT AS DIRECTION.** The tempting alternative — "creation
runs borrower→lender, release runs lender→borrower, so `from`/`to` already say
it" — fails for the reason already recorded: **transcription scoring cannot see
a role inversion.** grantor↔grantee scores 100% and reverses the lineage. An
effect inferred from direction is destroyed by exactly the error nothing
detects. State it, do not derive it.

### WHERE `effect` COMES FROM — the doc type, not a regex

`mode` and `function` are read from clause patterns because no index field
carries them. **`effect` is different: the register already states it.**

    SAT   SATISFACTION OF MORTGAGE        ->  releases
    TERM  UCC3 TERMINATION                ->  releases
    PREL  PARTIAL RELEASE OF MORTGAGE     ->  releases (partial)
    DEVR  DEVELOPMENT RIGHTS              ->  transfers
    MTGE  MORTGAGE                        ->  creates
    AGMT / SAGE / CERT                    ->  NOT DETERMINED by type; read it

`_doctype_codes.json` is an authority we already hold, it covers every document
in the corpus, and for the release family it is unambiguous — a document typed
SATISFACTION OF MORTGAGE does not create a mortgage. Deriving effect from the
type is cheaper and stronger than any clause regex, and it comes with an exact
denominator instead of a sampled one.

⚠ **BUT THE TYPE IS A DEFAULT, NOT A VERDICT.** The catch-all types decide
nothing (`SUNDRY AGREEMENT` is 989,103 documents of "could be anything"), and a
document may do several things at once — the ZLDA creates four encumbrances and
transfers an envelope under ONE type. RULE: **the doc type SEEDS `effect` per
document; the clause CONFIRMS or overrides it per row.** Where a row's effect
disagrees with its document's type, that is a finding to record, not an error to
silence.

⚠ Do not add an `EFFECTS` vocabulary to `lexicon.py` with invented patterns and
no coverage line. `MODES` and `FUNCTIONS` each carry `measured_against` with a
denominator, and a vocabulary whose status does not travel with its denominator
is exactly the defect already recorded — `signals` proven at 97% on BSA
applications, then winning a mortgage 5-2 on a corpus where it had under 10
hits in 23,282 clauses.

### THE DENOMINATOR — this is not an edge case

    SAT   SATISFACTION OF MORTGAGE          3,037,845
    TERM  UCC3 TERMINATION                    989,103
    REL   RELEASE                             210,182
    RFL   RELEASE OF FEDERAL LIEN             192,757
    TL&R  TERMINATION OF ASSIGN OF L&R        151,778
    PREL  PARTIAL RELEASE OF MORTGAGE         119,388
    ...   17 release-effect doc types in all
    ---------------------------------------------------
          4,977,173 of 24,037,915 documents  =  20.7%

**One document in five is a release.** Without `effect`, one document in five
writes a row that says the opposite of what it means. This is the single
largest correctness gap found in the table so far, and it was found by reading
a four-page document picked at random.

## R3-2 — ONE PARTY, AND THE OTHER SIDE IS ELSEWHERE ON PURPOSE

The cover page carries **PARTY ONE and no PARTY TWO**, and the instrument never
names the owner or borrower whose encumbrance is being released. `to` is not
`n/a` — a release runs to someone — and it is not carelessness. A release is a
unilateral act; the releasing party is the only one who needs to sign.

`to` is therefore **`unread` with a POINTER**: unrecoverable from this document,
and the document names exactly where it lives (CRFN 2005000533673). That is not
a sixth state. It is `unread` + reason, where the reason happens to be a
resolvable address. RULE: **when a field is unrecoverable here and the document
names the instrument that carries it, the reason must BE that instrument's
identifier** — a pointer is worth more than the word "unread".

## R3-3 — THE CROSS-REFERENCE FIELD HAS TWO OPPOSITE MEANINGS

    ZLDA  ...006   cross-refs ...002 ...003 ...004 ...005   SIBLINGS, same minute
    TL&R           cross-refs CRFN 2005000533673            the ANCESTOR it kills

Same block on the same cover-page form. In the first it is a lateral join that
assembles one transaction out of five recordings. In the second it is a
backward edge to the instrument being extinguished — **and only the second is
lineage.** An extractor that treats every cross-reference as a sibling join
will merge a mortgage with its own satisfaction into a single event.

⚠ Tell them apart by SHAPE, not by guessing: a sibling reference is a
`document_id` recorded in the same batch; an ancestor reference is typically a
`CRFN` (or reel/page) that is older than this document. Where both a CRFN and a
recording date are given, the date settles it.

## R3-4 — D-3 CONFIRMED TWICE MORE, AND THE GAP RUNS BOTH WAYS

    signed      2012-12-03   acknowledgment, Dallas TX (p4)
    as of       2012-12-06   dateline (p2, p3)
    recorded    2013-01-23   CRFN 2013000029650 (p1)

Here the signature comes **three days BEFORE** the effective date. In the ZLDA
it came **307 days AFTER**. The gap varies in direction and in magnitude by two
orders. Any system that treats "executed" as one date is wrong in a way that
cannot be bounded.

## R3-5 — ⚠ CORRECTION TO D-8: THE COVER COUNT IS NOT "PAGES + 2"

    TL&R   "Document Page Count: 3"    "PAGE 1 OF 4"     3 + 1 cover  = 4  held 4 ✓
    ZLDA   "Document Page Count: 114"  "PAGE 1 OF 116"   114 + 2      = 116 held 110 ⚠

D-8 stated the ZLDA case as "114 (+2 covers = 116)" as though 2 were the rule.
It is not — the ZLDA has a continuation cover page and this document does not.
**`Document Page Count` excludes the cover(s), and the number of covers varies.**

RULE: the completeness check reads **`PAGE 1 OF N`**, which is the register's
own total and needs no arithmetic. Never reconstruct it as page-count plus a
constant.

## WHAT THIS RUN DID NOT BREAK

The eleven functions held — ENCUMBRANCE was the right one and no twelfth was
owed. The three tiers held. The five states held. Provenance held. `subject`
resolved cleanly to one parcel from both the cover and the instrument, and they
agreed. The extraction filter held: the notary block, the seal and the abstract
company's stamp produced nothing.

**One new column, in a table that had survived three prior documents.** That is
the exit criterion doing its job rather than being declared satisfied — and it
argues the freeze was being approached on too small a sample of document TYPES.
Four documents have now been read end to end; the corpus has 126 types.

# FULL-DOCUMENT RUN — ZLDA `2010102601040006` (Manhattan 800/49, 53, 55, 56)

The document the retracted trial pretended to read. 110 pages, read end to end.
Everything below carries a page cite to the PDF as stored.

## THE EVENT, IN ONE LINE

**Two Sabetfard entities sold 53,578 sf of development rights to an Extell
entity for $5,000,000 — $93.32 per buildable square foot — and burdened their
own three lots to protect the tower that would use them.**

## D-1 — THE PRICE IS ON THE COVER, AND TWO STAMPS AGREE

The index reports `document_amt = 0` for this DEVR, as it does for every DEVR.
The cover page (p1) carries two prepaid stamps:

    NYC Real Property Transfer Tax   $131,250.00   @ 2.625%  ->  $5,000,000
    NYS Real Estate Transfer Tax     $ 20,000.00   @ 0.400%  ->  $5,000,000

Two independently-rated taxes, two independent divisions, the same number to
the dollar. **That agreement IS the confidence.** One stamp is a claim; two
stamps that agree are a measurement. Where they disagree, neither may be used
without saying which was preferred and why.

## D-2 — $/SF IS REAL AT THE DEAL, DERIVED AT THE LOT

Exhibit D (p38) gives every quantity, and the table closes on itself:

                      Developer   120 Owner    124 Land   126 Land     TOTAL
    Lot area             15,639       4,077       2,469      2,469    24,654
    DR generated        156,390      40,770      24,690     24,690   246,540
    Retained                n/a      16,906       9,620     10,046    36,572
    Excess (moved)          n/a      23,864      15,070     14,644    53,578
    After transfer      209,968      16,906       9,620     10,046   246,540
    Pro rata             85.17%       6.86%       3.90%      4.07%      100%

    246,540 / 24,654 = FAR 10.0 exactly       156,390 + 53,578 = 209,968

    $5,000,000 / 53,578 sf  =  $93.32 per buildable sf

⚠ **THE $/SF IS ONE NUMBER, NOT THREE.** Login asked for $/sf *by lot*. The
document does not give it. The stamps rate ONE consideration for the whole
transfer; Exhibit D splits the SF but never the money. A per-lot price can be
computed pro rata ($2,227,033 / $1,406,361 / $1,366,606) but that is a
**derivation under an assumption the document does not make** — and the
assumption is weak here, because two of the three selling lots are held by the
same entity under the same signature, so the parties had no reason to split it
precisely. RULE: **quantity may be apportioned; consideration may not, unless
the document apportions it.** Record the deal-level $/sf as measured and the
lot-level $/sf as derived, and never let the derived one price a comparable.

## D-3 — "EXECUTED" IS TWO DATES, AND THE DOCUMENT SAYS SO

    signed        2009-12-11   acknowledgment before notary, both parties (p27)
    as of         2010-10-14   the agreement's own dateline (p4), handwritten
                               into a printed "20__" blank; year illegible on
                               the page and resolved by the cover (p1)
    prepared      2010-11-11   cover page (p1)
    recorded      2010-11-16   City Register stamp, CRFN 2010000384312 (p1)

    signed -> as of      307 days
    signed -> recorded   340 days
    as of  -> recorded    33 days

The dateline does not say *made on*. It says **"made as of the 14th day of
October"** — an effective date the parties chose. The acknowledgment records
when signatures were actually taken. **Both are true and they are not the same
fact**, and they sit 307 days apart in one instrument.

⚠ CORRECTS AN EARLIER READING OF THIS SAME DOCUMENT. The r27 extraction wrote
`executed 2010-10-14` from the dateline; this run first wrote `executed
2009-12-11` from the acknowledgment and accused the index of picking wrong.
Both were over-claims from one half of the record. ACRIS `document_date` is
2010-10-14 — the instrument's own "as of" date — which is **defensible, not
wrong.** The defect was a single column pretending two dates were one.

RULE: the row carries **`signed`** (from the acknowledgment) and **`effective`**
(from the dateline) as separate provenance fields, alongside `recorded`. Where
they coincide, both carry the same value and nothing is lost. Where they do
not, a timeline built on either alone is wrong by up to a year, and the one
that matters depends on the question — *when did the parties commit* (signed)
vs *when did the terms begin to run* (effective) vs *when did the world get
notice* (recorded).

⚠ A dateline year handwritten into a printed blank may be illegible; the cover
page carries the same date in print. **Prefer the legible witness and say which
one was read** — never silently resolve an ambiguous glyph.

## D-4 — THE NOTICES BLOCK UNMASKS THE SPE

The most valuable page for a broker is the one every extractor throws away.
Section XX (pp23–24) gives, for parties that reach the index as bare shells:

    112-118 West 25th LLC   ->  c/o EXTELL DEVELOPMENT COMPANY, 805 Third Ave
                                attn. DOV HERTZ
    120-22 W 25 Street LLC  ->  c/o THE SABET GROUP, 38 West 31st Street
    124-26 W 25 Street LLC  ->  c/o THE SABET GROUP, attn. ALFRED SABETFARD

and the signature page (p26) closes it: **Alfred Sabetfard signs BOTH owner
entities as Managing Member**, before the same notary on the same day. Dov
Hertz signs the developer as Vice President — an officer title an LLC does not
have, which is itself the tell that a corporate manager stands behind it.

⚠ **NONE OF THESE PEOPLE OR SPONSORS EXIST IN THE ACRIS PARTY INDEX.** The
index carries three LLC names and nothing else. Name-matching across the index
cannot connect these three entities; the document connects them in one page.
RULE: the notices block and the signature/acknowledgment pages are EXTRACTION
TARGETS, not boilerplate. They are where control is stated.

## D-5 — THE INDEX IS WRONG ABOUT THINGS THE DOCUMENT SETTLES

    signature page (p26)   124-26 W 25 STREET LLC       38 West 31st Street
    ACRIS index    (p2)    124-25 W 25 STREET LLC       28 WEST 31ST STREET

A transposed digit in the name and a wrong street number, on the cover page
that states of itself: *"The information on this page will control for indexing
purposes in the event of any conflict with the rest of the document."*

RULE: the index controls INDEXING; it does not control FACT. Where the document
and the index disagree, the document wins and **the disagreement is recorded**,
because it is the reason a name search missed this party.

## D-6 — ONE TRANSACTION, FIVE DOCUMENT IDS, JOINED ON THE COVER

    CROSS REFERENCE DATA (p1, p2)
      2010102601040002  2010102601040003  2010102601040004  2010102601040005

The ZLDA is `...006`. The declaration, the waivers and the subordinations are
separate recorded instruments with their own ids, recorded the same minute.
**The cross-reference block is the join key that makes them one event.** An
extractor that treats each document id as its own event produces five
fragments and no transaction.

### D-6a — AND ONLY ONE MEMBER OF THE PACKAGE CARRIES DIRECTION

All four siblings are held and were checked against `_doctype_codes.json`:

    ...002  CERT  CERTIFICATE        OTHER DOCUMENTS            PARTY 1 / PARTY 2
    ...003  SAGE  SUNDRY AGREEMENT   OTHER DOCUMENTS            PARTY 1 / PARTY 2
    ...004  SAGE  SUNDRY AGREEMENT   OTHER DOCUMENTS            PARTY 1 / PARTY 2
    ...005  SAGE  SUNDRY AGREEMENT   OTHER DOCUMENTS            PARTY 1 / PARTY 2
    ...006  DEVR  DEVELOPMENT RIGHTS DEEDS AND OTHER CONVEYANCES PARTY ONE / PARTY TWO

`SUNDRY AGREEMENT` is the register's catch-all, and its party roles are
literally `PARTY 1` and `PARTY 2` — **role-blind by construction.** Four of the
five instruments in this transaction cannot say who gave and who received; only
the DEVR can. RULE: **direction is recovered from the member of the package
whose doc type defines roles, and asserted for the package** — never
independently guessed per document. Where NO member defines roles, direction is
`unread`, not inferred from party order.

⚠ This is why `role_of()` in `nav_build.py` leaves unknown types RAW rather than
guessing: a `PARTY 1` that is silently promoted to `grantor` inverts the lineage,
and transcription scoring cannot see a role inversion (grantor↔grantee scores
100% and reverses the chain).

⚠ Also measured on the same package: **the shortfall in D-8 is per-document, not
systemic.** `...003` declares 16 pages (+2 covers = 18) and ACRIS serves 18. The
declared-vs-held check must run per document; one short document does not
condemn a corpus, and a clean corpus does not clear one document.

## D-7 — THE TERM OF AN EASEMENT IS NOT IN THE GRANTING CLAUSE

The light-and-air easement (§II.A.2) and the construction easement (§XIII.A.2,
p19) both grant without stating duration. Duration is in §XV BINDING EFFECT
(p22), eleven pages later: the grants *"shall run with the lands"* and bind
*"heirs, distributees, successors and assigns."* That clause — not the grant —
is what makes these ENCUMBRANCE rather than contract.

RULE: **an event's `term` may live in a different section from its `function`.**
A reader that extracts clause-locally will emit `term: unread` on an easement
whose term is stated plainly elsewhere in the same instrument. This is a
direct restatement of why the whole document must be read (G-029), measured
on a second instrument.

## D-8 — THE SOURCE CAN BE SHORT, AND ONLY THE COVER KNOWS

    cover page (p1)        Document Page Count: 114   ("PAGE 1 OF 116")
    pages ACRIS serves     110  (probed: page 111 returns the PLACEHOLDER md5)
    pages held             110

**Acquisition is complete. The instrument is not.** Six pages the City Register
recorded are not in the image system. Page 110 stops mid-exhibit, and the
exhibit schedule (p28) shows what the tail held: **Exhibit F, Form of Light and
Air Easement** — the terms of an encumbrance this run extracted.

⚠ **NOTHING IN THE PIPELINE COULD HAVE CAUGHT THIS.** The walker terminates on
the placeholder and is right to; the page-count DB records 110 and is right to;
every completeness check reads clean. The only witness to the shortfall is the
count printed on the cover page — **which is an image**. RULE: declared page
count is an EXTRACTION FIELD, and `declared - held` is a completeness check that
can only run after reading. A pipeline cannot gate on it; an extraction must
report it.

### D-8a — A FIFTH STATE: `unavailable`

The four states could not express this. The page was not `unread` (nothing was
held to read) and not `not attempted` (it was attempted, and the source
answered). The source does not have it.

    value          read and recovered
    n/a + reason   the document says it does not apply
    unread         the page is held; the value could not be recovered
    not attempted  the page was never opened
    unavailable    the page does not exist at the source   <- NEW

`unavailable` is the only one of the five that **no amount of re-reading will
fix**, which is exactly why it must be separable: it is the difference between
work outstanding and work impossible. A coverage number that folds it into
`unread` reports a backlog that can never be drained.

## D-9 — THE FILTER HELD

Sections XVI–XXVII (pp22–25) — remedies, limitation of liability, lien law,
non-waiver, headings, pronouns, counterparts — produced **zero rows and zero
claims**. So did the whole of §XIII.A.3–5 (pp19–21): engineer selection,
objection notices, independent-engineer arbitration. Real obligations, real
money, no implication for any of the eleven functions.

The reimbursement and insurance provisions (§XIII.C–D, pp21–22: Reimbursable
Expenses uncapped, $5,000,000 per occurrence / $10,000,000 aggregate) are
CONDITIONS on the construction easement, not COST events — they have no
determinable quantity and no date, and they attach to a row that already
exists. **Conditions attach; they do not multiply rows.**

**No new columns. No new vocabulary members. Two new rules (D-3, D-7), one new
state (D-8a), and one finding about the source rather than the model.** Third
consecutive document where the failures moved off the table and onto the
pipeline — which is the convergence signal.


# ENTRIES EARNED IN BOOTCAMP RUN 1
Parcel 1-01843-0017 (165 & 169 Manhattan Ave) · 6 documents read + index measured
· 2026-08-19

**R-001 · THE TAX STAMP IS THE PRICE, AND THE RATE IS DERIVABLE FROM THE
CORPUS.** (Taught by FT_1370008641337, p1 margin "S.T. $275".) $275 at the
1981 New York rate of $0.55 per $500 = **$250,000** consideration. Corroborated
by FT_1420008636442, whose stamp is the minimum $0.55 (nominal, <= $500).
RULE: read the S.T. margin notation and the cover-page stamp; derive
consideration; label it DERIVED and name the rate used. A stamp that does not
resolve to a clean multiple (FT_1380008641338, $13.50) stays **unresolved** —
never rounded into a number. NEEDS: a third witness before the rate is
promoted from hypothesis to calibration.

**G-007 · THE MARGIN TAX NOTATION USES SUPERSCRIPT CENTS.** "ST 13^50" is
$13.50, not $1,350. (Taught by FT_1380008641338 p1.)

**G-008 · DOC-TYPE MISLABEL, CONFIRMED ON LIVE DATA.** FT_1380008641338 is
indexed **MTGE**; the instrument is a "Standard N.Y.B.T.U. Form 8007 — Bargain
and Sale Deed, with Covenant against Grantor's Acts". RULE: read the FORM LINE
at the head of page 1 — it names the instrument. The index doc_type is a flag,
never a veto; a mismatch is reported upstream as an index defect and the
EVENT carries the truth. (1 of 6 documents read = 17% mislabel on a tiny
denominator — measure properly before generalizing.)

**G-009 · THE FRONT-PAGE TAX MAP MARGIN CAN BE WRONG.** FT_1420008636442 p1
margin reads "Blk. 1834"; the back cover (p4) and the handwritten margin both
read **1843**, and 1843 is the true block. RULE: block/lot needs two witnesses;
prefer the back-cover recording block; keep the dissent on the claim.

**G-010 · THE INDEX AMOUNT IS DEAD IN THIS ERA.** amount = '0' on 6 of 6
documents sampled (1981–1984). RULE: never read consideration from the index
for microfilm-era documents; the stamp is the only price witness.

**⚠ G-011 · THE FOLDER'S CHRONOLOGY IS A MIXED CLOCK — THE BIGGEST TRAP FOUND
SO FAR.** Filenames (and the `_INDEX` order) use **doc_date when present, else
recorded_date**, so a single sort mixes two different clocks. Measured on
FT_1370000032837: filename/doc_date **1982-07-31**, index recorded_date
**1983-03-13**, and the instrument itself says executed **31 August 1982** —
three dates, none of them redundant. RULE: extraction records BOTH dates as
separate claims; Resolution builds the time chain on **recorded_date** (the
public record's clock) and carries execution date as an attribute. Never
trust the folder order as a chronology.

**M-001 · THE INDEX'S PARTY VERIFIER: ACCURATE WHEN PRESENT, BUT THINLY
COVERED.** Measured on this parcel: party rows exist for **23 of 119**
documents (19%) — FT_ era 6/25, CRFN era 17/94. RULE: the md's "parties are a
GOOD verifier" is a claim about ACCURACY, not COVERAGE. When absent, the
document is the only witness; never treat an empty party set as "no parties".
This is also a NAVIGATION-phase gap: index details are incomplete for this
parcel, which the phase check ("zero rows missing index details") should
catch at scale.

**M-002 · THE CITATION RUNG IS ALREADY IN THE INDEX, AND IT IS RICH.**
`reference_document` holds **455 citations across 119 documents** on this
parcel (3.8 per document). Forms: **440 by reel/page** (microfilm era:
reel_year + reel_nbr + reel_page), **165 by CRFN**, **35 by doc_id**. Example:
the 2004 AGMT (2004050500235002) cites the 1986 MTGE (1029/1808), the 1989
MTGE (1588/1390) and the 1999 MTGE (2854/2191) — an 18-year debt chain visible
**before a single page is read**. RULE for Resolution: build the citation rung
from `reference_document` FIRST, then read documents to enrich it; the
strongest attachment rung costs nothing.

**M-003 · THE CITATION JOIN HAS NO INDEX — measured by failing.** Resolving
reel citations means joining (reel_yr, reel_nbr, reel_pg) -> document_id, and
that column set is unindexed: 455 lookups against the 8.4 GB map did not
finish in 120 s and had to be killed to protect a running pull. RULE: before
Resolution runs at scale, Navigation must add the composite index. Resolvability
is therefore **UNMEASURED** — not "low", not "high", unmeasured.

**B-001 · TITLE-CONTINUITY BREAK CANDIDATE (for Resolution).**
FT_1380008641338 (May 1981) conveys to **FIRST FUNDING EQUITY, c/o CROSSROADS
PROPERTIES, LTD.** The next deed, FT_1370000032837 (Aug 1982), has
**CROSSROADS PROPERTIES, LTD.** as grantor. Grantor != prior grantee by name.
Either the c/o party was the real principal, or a conveyance is missing. RULE:
a "c/o" party is a first-class claim — record it; the entity spine decides
whether it closes the chain, and until it does this is a NAMED BREAK, not a
silent join.

**R-002 · THE CHAIN IS A READER — let continuity resolve what the page
cannot.** FT_1370000032837's grantee is handwritten and was unreadable in
isolation; the next deed (FT_1470000032847) names BENSON HOLDING CORP as its
typed grantor, and title continuity forces the match. RULE: an unreadable
party is not automatically `unreadable` — hold it as an open claim and let
Resolution's continuity close it. Only a party that NO neighbouring
instrument can corroborate is terminal. (This is why extraction must not
declare a document finished in isolation when the missing field is a party.)

**M-004 · THE ENTITY SPINE STARTS WITH ADDRESSES, NOT NAMES.** BAUBLE REALTY
CORP (1981) and BENSON HOLDING CORP (1983) share 1051 Northern Boulevard,
Roslyn NY 11577; FIRST FUNDING EQUITY and CROSSROADS PROPERTIES LTD share
37-56 74th Street, Jackson Heights. RULE: capture the party ADDRESS as a
first-class claim on every instrument — it clusters entities that share no
name, and it is often the only bridge between an SPE and its principal.

**M-005 · THE KEY SET CAN CHANGE MID-CHAIN.** Lots 17 and 51 conveyed together
in every instrument 1981-1983; the 1984 deed conveys Lot 17 alone. RULE:
record the conveyed premises per instrument, never inherit the previous
document's key set. A chain that assumes a fixed key set will silently
attribute one lot's later history to both.

**G-012 · WATCH FOR THE RECORDER'S OWN ANNOTATIONS.** FT_1920000078092 carries
a margin stamp "SO IN ORIGINAL" — the recorder flagging an anomaly in the
instrument as filed. RULE: treat recorder annotations as claims about the
RECORD (a REFERENCE, never a function); they explain defects a reader would
otherwise attribute to the scan.

---

# ENTRIES EARNED IN BOOTCAMP RUN 1 (continued) — the 1986 pair

**R-003 · THE MORTGAGE RECORDING TAX SELF-VALIDATES THE PRINCIPAL.** Measured
on FT_1540000130354 (1986): stated Mortgage Amount **$2,475,000.00**, recording
tax stamp **$55,687.50**. $55,687.50 / $2,475,000 = **2.2500% exactly** (the NYC
rate for large mortgages in that era). RULE: check principal against the tax
stamp; an exact hit is a self-validating read with no human key. A MISMATCH is
not automatically a bad read — check for an exemption or a CEMA first (the
HECM lesson: a $0 tax with an exemption code is CORRECT). Two independent
witnesses of the same number beat one confident reading.

**M-006 · THE TITLE NUMBER LINKS INSTRUMENTS ACROSS THE SAME CLOSING.**
"M 205088" appears as `TITLE NO.` on the 1986 deed (FT_1530000130353 p4) and
handwritten in the top margin of the 1986 mortgage (FT_1540000130354 p1).
RULE: capture the title number as a REFERENCE — it is a corroborating rung
that is neither a CRFN nor a reel citation, and it binds a deed to the
mortgage that funded it even when neither cites the other.

**M-007 · A TRANSFER TAX OF "NONE" IS A SIGNAL, NOT A PRICE.** The 1986 deed's
stamp reads **NONE** and the fee line shows SST **$0.00** — yet the same day
the property carried a **$2,475,000** new mortgage. Both entities sit at
**95 Delancey Street** (159-161 Stanton Street Realty Corp -> Manhattan Avenue
Development Corp). RULE: never record $0 tax as "$0 price". Record it as NO
TAXABLE CONSIDERATION and let the entity spine explain it — related-party
restructuring, mere change of form, or an exemption. The event is a TITLE
change with unresolved consideration, plus a strong entity-relationship edge.

**M-008 · A GAP IN ONE LOT'S FOLDER MAY NOT BE A BREAK — CHECK THE SIBLING
LOT.** The 1984 deed conveys Lot 17 only; the 1986 deed conveys Lots 17 AND
51. The intervening Lot 51 conveyance is not missing from the record — it is
keyed to **1-01843-0051** and therefore sits in the other parcel's folder.
RULE: before naming a title break, resolve across every key the instrument
chain touches. Single-key reading manufactures phantom breaks on assemblages.

**C-001 · THE PRINCIPAL BEHIND THE SPE, FIRST SIGHTING.** The 1986 deed's
acknowledgment names the signing officer: **"Baruch Singer", VP of 159-161
Stanton Street Realty Corp**, residing 266 East Broadway (handwritten —
moderate confidence, needs a second witness). RULE: the acknowledgment block
is where a HUMAN appears behind a corporate party. Capture officer name, role
and address as claims — this is the raw material of the contacts traversal,
and it exists nowhere else in the record.

---

# ENTRIES EARNED FROM THE DOC-TYPE AUTHORITY (`_doctype_codes.json`, 126 types)

**R-004 · ROLES ARE DECLARED BY THE DOC TYPE — DO NOT INFER THEM FROM THE
PAGE.** The authority carries `party1_type` / `party2_type` for every type:
DEED = GRANTOR/SELLER -> GRANTEE/BUYER · MTGE = MORTGAGOR/BORROWER ->
MORTGAGEE/LENDER · ASST = ASSIGNOR/OLD LENDER -> ASSIGNEE/NEW LENDER · AL&R =
ASSIGNOR -> ASSIGNEE. RULE: take the role from the authority and VERIFY it
against the instrument; never derive direction from reading order. **This is
the structural defence against role inversion** — the failure that scores 100%
on transcription and reverses the whole lineage (a swap now contradicts a
declared role, not just a chain).
⚠ Types whose slots are generic (DEVR = PARTY ONE/PARTY TWO; SAGE = PARTY 1/
PARTY 2) declare NOTHING about direction — for those, direction must come from
the instrument text, and an unread direction stays `unresolved`.

**M-009 · CLASSIFY SCOPE BY `class_code_description`, NEVER BY A HAND LIST.**
The 126 types resolve into four classes: DEEDS AND OTHER CONVEYANCES (34) ·
MORTGAGES & INSTRUMENTS (23) · UCC AND FEDERAL LIENS (29) · OTHER DOCUMENTS
(40). Measured failure: my hand-written personal-property filter missed
**CORP, RLSE, SUBO, INIC** (all UCC AND FEDERAL LIENS), which corrupted a
parcel-closure census earlier today and made whole parcels read as "missing"
documents that were never in scope. RULE: real-property scope = the two
conveyance/mortgage classes; UCC AND FEDERAL LIENS is the party-keyed class;
OTHER DOCUMENTS is decided per type. The authority is the filter.

**G-013 · RESOLVE UNFAMILIAR TYPE CODES FROM THE AUTHORITY BEFORE READING.**
`SAGE` is **SUNDRY AGREEMENT** (class: OTHER DOCUMENTS) — not a satisfaction,
which its spelling suggests and which would have put a phantom payoff in the
debt chain. RULE: never guess a code; the table names it, and a wrong guess
writes a false event.

---

# ENTRIES EARNED FROM THE 2004 CEMA PACKAGE (CRFN era)

**⚠ G-014 · THE EXEMPTION FIELD BREAKS R-003 — READ IT FIRST.** Confirmed live
on 2004050500235002: **Mortgage Amount $3,150,000.00**, **Taxable Mortgage
Amount $0.00**, **Exemption: 255**, every tax line $0.00. Applying R-003 (tax
= 2.25% of principal) would have flagged this correct document as broken —
exactly the failure predicted for HECMs, CEMAs and government-backed loans.
RULE: read `Exemption` and `Taxable Mortgage Amount` BEFORE checking principal
against tax. A $0 tax WITH an exemption code is a valid document; a $0 tax
WITHOUT one is a finding. The check is conditional, never unconditional.

**R-005 · THE MODERN COVER PAGE IS STRUCTURED EXTRACTION, ALREADY DONE.** The
CRFN-era "RECORDING AND ENDORSEMENT COVER PAGE" carries, in labelled fields:
document id · type · document date · preparation date · **page count** ·
presenter · return-to · **property data (borough, block, lot, unit, address,
PROPERTY TYPE)** · **cross references** · **parties with slots** · **fees and
taxes broken out** · CRFN · recorded timestamp. RULE: for CRFN-era documents,
read the cover page FIRST and the instrument only for what the cover cannot
carry (terms, covenants, exhibits, quantities). **Cost lever for production:**
modern documents are cheap to extract, microfilm documents are expensive —
plan concurrency and model tier by era, not by a single average.

**M-010 · THE CEMA PACKAGE IS A THREE-DOCUMENT EVENT.** 2004-04-23 recorded as
a trio: **MTGE** (2004050500235001, the new money) + **AGMT**
(…002, the consolidation/extension/modification) + **AL&R** (…003, assignment
of leases and rents). The AGMT's cross-references name every mortgage being
consolidated (1986 reel 1029/1808, plus 1989 and 1999 on the continuation
page). RULE: treat the trio as ONE financing event with three instruments —
consolidating, not stacking. Summing the three principals would triple-count
the debt. The AGMT is the spine; the MTGE is the increment; the AL&R is
collateral, not new money.

**F-001 · FIRST HARD FACT ABOUT THE IMPROVEMENT.** The cover page's property
data states **Property Type: APARTMENT BUILDING** for both 165 (Lot 17) and
169 (Lot 51) Manhattan Avenue. RULE: property type on the cover page is a
recorded claim about the improvement — capture it; it is often the only
building-level fact in the legal-instruments corpus (until a DOB source
joins).

---

# ENTRIES EARNED FROM THE 2005 SALE

**R-006 · THE TRANSFER-TAX-IS-THE-PRICE RULE HOLDS ACROSS ERAS — BUT THE RATE
CHANGES, SO NAME IT EVERY TIME.** Measured on 2005083102072001 (CRFN
2005000536668): cover page **NYS Real Estate Transfer Tax $33,574.00**. At the
2005 rate of $2.00 per $500 (0.40%): $33,574 / 0.004 = **$8,393,500** — and
16,787 whole $500 units, an exact clean multiple. Compare 1981: $275 at $0.55
per $500 (0.11%) = $250,000, also exact. RULE: derive consideration from the
NYS RETT, ALWAYS state which rate was applied, and require the result to be a
clean multiple of the tax unit. A non-clean multiple (the 1981 $13.50 case)
means the rate or the basis is wrong — leave it unresolved.
⚠ The NYC RPTT does NOT appear as an amount on the cover page (only a $165
filing fee); the NYS RETT is the price witness in the CRFN era.

**M-011 · THE BUYER'S NAME CAN RESOLVE A DESCRIPTION MISMATCH.** The 1986
mortgage described the premises as "165/169-171 Manhattan Avenue" while the
lots are 17 and 51 — an apparent third address. The 2005 grantee is
**165-171 MANHATTAN AVENUE LLC**, which reads the assemblage as one address
range: Lot 51 carries 169-171. RULE: party names that encode addresses are
evidence about the premises; capture them as claims, they resolve
address/lot mismatches the metes descriptions leave open.

---

# FORMAT CORRECTIONS - 2026-08-19 (my errors, caught in review)

**G-015 - TERM IS NEVER BLANK ON A TITLE EVENT: THE ESTATE IS THE TERM.**
I wrote a dash for term on six deed events. Wrong: a conveyance states its
duration in the granting clause. "unto the party of the second part, the heirs
or successors and assigns of the party of the second part FOREVER" =
**fee simple absolute**. RULE: read the granting clause for the estate - fee
simple, life estate, leasehold with years, easement in gross - and put it in
`term`. A blank term on a TITLE event means the estate was not read, not that
none exists. Encumbrances take their term from their release condition
(until paid or released; runs with the land).

**G-016 - AN AMOUNT ALWAYS EXISTS: BOUND IT, NEVER BLANK IT.** I recorded
"nominal - unresolved" and left it there. Wrong: the document states $10 and
the tax stamp caps the true figure at $500 (one tax unit at $0.55 per $500).
RULE: quantity carries the recited amount AND the bound the tax implies. Write
`$10 recited, <= $500 by stamp`, never `unresolved` alone. An internal transfer
still has a price; "no market price" is a CONCLUSION about the number, not an
absence of one.

**G-017 - MODE IS transacts/observes/signals: I INVENTED A VOCABULARY.**
I wrote mode as the instrument form ("bargain and sale, without covenant").
That is the FORM, which belongs beside doc type as an attribute - mode is the
settled epistemic vocabulary above. Measured consequence: the same deed
granting clause is `transacts` while its subject-to clause is `observes`, and
only the first may assert that state changed. RULE: never invent a vocabulary;
lexicon.py holds functions AND modes, and canon() is the only normalizer.
(This is G-001 repeating on a different column - the failure mode is drift,
and it is fast.)

**G-021 - WHEN THE SPLIT IS UNREAD, WRITE ONE AGGREGATE ROW, NEVER N EVEN ONES.**
Trial 2026-08-19, ZLDA `2010102601040006`: three sending lots (53, 55, 56) pass
53,578 SF for $5,000,000 and the document states NO per-lot allocation. The
multidirectional rule says N senders = N rows, but N rows cannot be written
without the split. Write ONE row with the set in `from` and mark it
`split: unread`. **That row cannot produce a per-sender $/BSF** - $93.32 is a
blended rate. Dividing evenly to reach N rows fabricates a split the parties
never made, and it looks exactly like data.

**G-022 - A CONSOLIDATION IS CLOSING ROWS PLUS ONE OPENING ROW.**
Trial 2026-08-19, Block 800 lot 49, 2012-10-05: an eight-document batch whose
faces sum far above reality - AGMT $39,000,000 against $1,607,226 of actual new
money. A single CAPITAL row at the face double-counts, because most of it is the
prior balance rolled forward. Write each prior obligation as a CLOSING row and
the consolidated obligation as ONE opening row; new money is then COMPUTED as
`opening - sum(closings)`, never asserted. Same shape as G-018.

**G-023 - A DISSOLUTION MUST NAME THE ROW IT PRODUCES.**
Trial 2026-08-19: the completeness test retired "zoning lot composition" as
ENVELOPE + ENCUMBRANCE. The trial showed the merge is **IDENTITY** - four tax
lots become one zoning lot, and every later document addresses the merged thing.
No twelfth function was owed; the wrong ones were named. G-020 kills bad
candidates but does not check that the surviving mapping is right, so a
dissolution now has to be written as an actual ROW before it counts.


**M-012 - INTERNAL vs EXTERNAL TRANSFER: CAPTURE THE EVIDENCE, DO NOT JUDGE.**
A nominal price between apparently unrelated parties is the signature of an
internal transfer, and the difference matters enormously downstream (an
internal transfer is not a comparable and must never price a market).
Internal-ness is a **derivation inference**, never an extraction fact. RULE:
extraction captures the five tests as claims on every conveyance - **name
match, entity match, mailing-address match, signature/officer match,
corporate-authority recital** - and derivation weighs them. Measured on
FT_1420008636442: four tests read NO MATCH, but the deed carries a BCL 909
unanimous-stockholder consent and a nominal price, which is the shape of a
liquidating distribution rather than a sale. Verdict recorded as **unresolved,
leaning internal-by-structure**, with what would settle it named (was the
grantee a stockholder or officer?).

---

## 2026-08-21 — THE SUBSTRATE SETTLED (infrastructure, not vocabulary)

The system around this bootcamp closed its record layer today. What changes
for extraction training and nothing else:

- **Input surface:** `D:\CRE Decoding System\Legal Instruments.db` — every
  document reachable BY PARCEL (`key` column, custodian-asserted only),
  each row carrying `recorded_details` + the `pdf` path. No network at
  extraction time; completeness upstream is proven (both custodians closed
  by their own enumerations, 2026-08-21).
- **Output:** `Legal Instruments Decoded.db` — the reading, many rows per
  document; doc id + key join back to the record.
- **Training implication:** gold sets can now be DRAWN BY PARCEL (a whole
  lot's chain as one exercise, chronology free from the store) and every
  miss traces to a row, not a loose file. The approach question — time /
  cost / accuracy of the decode itself — stays OPEN and gets answered by
  measurement under this file's rules, one entry per miss, as ever.

---

# RANDOM-DOCUMENT RUN — `FT_2760000622076` (Bronx 4340/1269, ASST, 2 pp, 1985)

Cold pick 2026-08-22, sampled from the By Document store on DISK (the store is
the completion evidence; both attempts to sample "complete" rows from the hot
nav table walked too far and had to be killed — the table is for lookups by id,
the store is for enumeration). Read complete: 2 of 2 pages. **Zero new columns,
zero new vocabulary members — the streak advances.** First run driven by the
main model reading the stored pdf directly: no VLM server, no lane impact.

    ASSIGNMENT OF MORTGAGE WITHOUT COVENANT (Standard N.Y.B.T.U. form)
    N.A. HOME INVESTORS MORTGAGE CORPORATION (NJ, 90 Main St, Hackensack)
      -> DOLLAR DRY DOCK SAVINGS BANK OF NEW YORK (2530 Grand Concourse, Bronx)
    premises 2385 Barker Avenue UNIT 6W, Bronx — Section 16 Block 4340 Lot 1269
    reel 603/1822-1823 · signed 1985-06-04 · recorded 1985-08-07 PM 2:24

## THE EVENT (one event_id, two rows + one observes)

    row 1  transacts · parcel 2-04340-1269 · CAPITAL · transfers
           from N.A. HOME INVESTORS MORTGAGE CORPORATION
           to   DOLLAR DRY DOCK SAVINGS BANK OF NEW YORK
           qty  $27,400.00 · USD · principal_assigned · value
           term unread — maturity lives in the assigned mortgage,
                pointer: Reel 598 Mortgages p.267 (R3-2 shape)
    row 2  transacts · parcel 2-04340-1269 · ENCUMBRANCE · transfers
           same direction · lien securing $27,400.00 · until satisfied
    row 3  observes — the recited ancestor: MTGE made by PRUDENCE DRUMMOND
           and YVONNE MARRIOTT to N.A. Home Investors, $27,400.00, dated
           1985-06-04, recorded 1985-06-26 Reel 598 p.267 (L-3: recital,
           never a phantom origination)

Summary: *N.A. Home Investors Mortgage Corporation assigned the $27,400
mortgage capital and lien on Bronx 4340/1269 (2385 Barker Avenue, Unit 6W) to
Dollar Dry Dock Savings Bank of New York for $27,400 — par — signed June 4,
1985, recorded August 7, 1985. The maturity is not stated here; it lives in
the assigned mortgage at Reel 598 page 267.*

## R4-1 — AN INSTRUMENT CAN BE EXECUTED BEFORE ITS ANCESTOR IS RECORDED

    mortgage made        1985-06-04     (the ancestor)
    ASSIGNMENT SIGNED    1985-06-04     the SAME DAY
    mortgage recorded    1985-06-26     22 days later
    assignment recorded  1985-08-07

The assignment was signed the day the loan closed and 22 days BEFORE the
mortgage it assigns entered the record — the correspondent-lending shape: the
originator pre-signs the assignment at closing, the bank records both in
sequence. A chain built on `recorded` stays valid (598/267 lands first); a
chain built on `signed` shows a transfer of an instrument that does not yet
exist in the record. This is D-3/G-011 measured at its extreme: the two clocks
do not merely drift, they can INVERT ancestry. Chains sort on `recorded`,
always — now witnessed, not just ruled.

## R4-2 — L-2 REFINED: WHEN THE ASSIGNMENT *DOES* STATE THE PRICE, CAPTURE PAR-VS-DISCOUNT

L-2 says the price an assignee paid is "usually not in the record at all."
This film-era N.Y.B.T.U. form has a printed consideration blank, filled:
**$27,400.00 paid — exactly the principal assigned. A par trade, stated.**
When both numbers are in the record their RATIO is a real market fact (par /
discount / premium) and it is claimable with an anchor. The qty_role split
carries it: `principal_assigned` on the row, `consideration` as a claim.
Never derived, only captured when the form states both.

## R4-3 — THE INDEX TRUNCATES PARTY NAMES; THE DOCUMENT CARRIES THEM WHOLE

    index    N.A. HOME INVESTORSMTGE     DOLLAR DRY DK SAVS.BK/NY
    document N.A. HOME INVESTORS MORTGAGE CORPORATION
             DOLLAR DRY DOCK SAVINGS BANK OF NEW YORK

Film-era index fields truncate at a fixed width with ad-hoc abbreviation
("SAVS.BK/NY"). Name-matching against the index fails on names the document
states perfectly (D-5 family, new mechanism: truncation, not error). The
document is the party authority; the index string is a claim about the index.

## CONFIRMATIONS (no new rules owed)

- **G-010 again**: index `amount $0.00`, document states $27,400 twice.
- **The index remarks field carried the ancestor** (`A/M R.598 P.267`) — the
  citation rung (M-002) exists even in the film era's thin index.
- **The register's Section/Block/Lot back-cover block** (16 / 4340 / 1269)
  agreed with the rd's BBL 2043401269 — two witnesses, no dissent.
- Notary, title-company box, return-to block: filtered, zero rows (D-9 held).
- Unit 6W = a condo unit lot (lot 1269) — the subject is the UNIT's BBL, and
  the rd's parcel panel already carried it correctly.

## PIPELINE NOTE

This document's nav row is **unkeyed pre-trigger debt** (parcels present,
keyed_by empty) — the random draw landed on the backfill population on the
first pull, a free confirmation that the debt is real and evenly spread.

## R4-4 — THE RD ROW AND THE PDF ARE ONE INSTRUMENT'S TWO WITNESSES (the reconciliation discipline)

Login 2026-08-22: *"its important now with the db that you consider the
recorded details and the pdf to really see how they work together since that
helps with verifying and making the extraction easier."* Adopted, with the
order of operations that keeps it safe:

    1. READ THE PDF COLD.  No rd fields in view while reading - G-003 scaled
       up: an index value loaded as an expectation is a prime, and priming
       transfers errors (measured on the VLM; true of any reader).
    2. THEN RECONCILE against the rd row, field by field.
       AGREEMENT  -> a free verification (two witnesses, zero cost - run 4:
                     back-cover Section/Block/Lot 16/4340/1269 vs rd BBL
                     2043401269, no dissent)
       DISAGREEMENT -> a FINDING, never silently resolved (run 4: index
                     truncates party names; index amount $0 vs $27,400 twice
                     on the page; both recorded)
    3. THE RD IS ALSO THE READING PLAN: pages (completeness gate), type
       (which GUARDS to load), remarks (the ancestor citation was in the
       INDEX - `A/M R.598 P.267` - before the pdf was opened), parcels (the
       subject, to be confirmed not assumed).

The rd is a VERIFIER and a MAP - never a prior. For production this is the
prompt shape: the VLM receives the pdf and reads cold; the rd row rides in
the HARNESS, which runs the reconciliation mechanically after the read and
routes disagreements to findings. The model never sees the index's candidate
for a field it is reading.

## R4-5 — WHAT THE EASY RUNS DO AND DO NOT PROVE (honest scope note)

Run 4 was a 2-page printed form - the friendliest shape the corpus holds. It
exercised vocabulary, effect, qty_role, dual clocks, and reconciliation; it
did NOT exercise the hard part, which the ZLDA runs define: COMPOSITION
ACROSS DISTANCE - grant p8, price p1 (stamps), quantities in an exhibit p38,
term p22, control pp23-26. On long instruments the failure mode is not
misreading a page but failing to connect pages: an event opened early whose
term/quantity arrives 30 pages later must stay OPEN in the reader's working
state until the document closes it or the last page confirms `unread`.
RULE for the production harness: long documents are read with an OPEN-EVENTS
LEDGER - every event whose measure slots are unfilled stays listed while
reading continues, and each new page is checked against the open list before
anything else. That ledger is what "understanding exactly what happened"
means operationally - and its final state IS the extraction.

---

# RANDOM-DOCUMENT RUN 5 — `RC_1019260` (Richmond blk 3595, A/MTG, 2 pp, 1971)

Cold pick from the disk store (second draw of the 2026-08-22 sample), read
cold FIRST, rd reconciled AFTER (R4-4 order). 2 of 2 pages. **Zero new
columns, zero new vocabulary — streak advances.** First Richmond bootcamp
document; instrument 9615 · Liber 1859/47-48 (verified by Liber/Page per the
two-namespace rule, never by filename).

    ASSIGNMENT OF MORTGAGE WITH COVENANT (N.Y.B.T.U. Form 8022)
    JOHN P. CROWLEY and MARY M. CROWLEY (106 Union Road, Spring Valley NY)
      -> McKEVITT ASSOCIATES c/o Richard N. Corash, 26 Bay Street, S.I.
    premises 51 Greeley Avenue, Staten Island — Section 4, Block 3595, LOT blank
    signed 1971-04-16 · recorded 1971-04-16 PM 2:58 (SAME DAY)

## THE EVENT (one event_id: CAPITAL + ENCUMBRANCE transfer, one observes)

    row 1  transacts · parcel 5-03595 (block-level, see R5-3) · CAPITAL ·
           transfers · CROWLEY -> McKEVITT ASSOCIATES
           qty $4,573.60 · USD · unpaid_balance · value   (the covenant states it)
           term unread - maturity lives in the assigned mortgage,
                pointer: Liber 184[4?] of Mortgages p.128, Richmond (glyph
                ambiguous - resolvable against the ancestor itself in-corpus)
    row 2  transacts · ENCUMBRANCE · transfers · lien securing $4,573.60 ·
           until satisfied
    row 3  observes - ancestor MTGE: JOHN J. MASTOWSKI and ALICE MASTOWSKI
           -> the Crowleys, $4,600.00 original, dated 1970-11-06, recorded
           1970-11-09
    claims consideration: $1.00 RECITED, price not stated (no stamp exists
           for an assignment - unresolved is the honest state; L-2 confirmed
           on Richmond) · interest 7-1/2% per annum from 1970-11-01 ·
           amortization witness: 4,600.00 - 4,573.60 = $26.40 paid in 5.5 mo

Summary: *John P. and Mary M. Crowley sold their $4,600 mortgage on 51
Greeley Avenue, Staten Island (block 3595) to McKevitt Associates; the
covenant states exactly $4,573.60 remained owing at 7½% from November 1,
1970. The price paid is recited as $1 and not otherwise stated. The
borrowers — John J. and Alice Mastowski — appear nowhere in the index.
Signed and recorded the same day, April 16, 1971.*

## R5-1 — THE FORM LINE DECIDES WHICH SLOTS THE DOCUMENT CAN FILL

Run 4's form was WITHOUT covenant: no balance, price stated. This form is
WITH covenant, and the covenant clause is a structured disclosure: **unpaid
balance to the penny + interest rate + accrual date** ("there is now owing
... without offset or defense of any kind, $4,573.60 ... at 7-1/2 per centum
per annum from the 1st day of November, 1970"). The interest RATE — a value
the vocabulary ledger lists as `unread - no extractor` corpus-wide — is
sitting in plain print on a 1971 assignment. RULE: read the FORM LINE first
(G-008 already says it names the instrument); it also names WHICH quantities
the body is obligated to state, which is what makes their absence `unread`
vs `n/a`. PATTERN: `AND the assignor covenants that there is now owing` ->
fills qty(unpaid_balance) + rate + accrual date.

## R5-2 — RICHMOND INDEXES ASSIGNMENT PARTIES AS "Mortgagor" — ROLE WORDS ARE REGISTER VOCABULARY, NOT SEMANTICS

The rd lists the CROWLEYS with role `Mortgagor`. They are not mortgagors -
they are the LENDERS selling the note; the actual mortgagors (the
Mastowskis) appear NOWHERE in the index (L-4 confirmed on Richmond). A
reader that trusts the role label writes the sellers into the debt graph as
borrowers - a role inversion, the error transcription scoring cannot see.
RULE (R-004 extended to Richmond): the register's role label is a CLAIM in
the register's own vocabulary; the semantic role comes from the doc type +
the instrument text. For A/MTG, the "Mortgagor" column holds the ASSIGNOR.

## R5-3 — LOT 0000 IS A BLOCK-LEVEL KEY, NOT A LOT

Back cover: Section 4, Block 3595, **LOT blank** - "Mortgages and Indexed
under Block Number 3595 On the Land Map of the County of Richmond." The rd
key is `5035950000` - lot 0000. Pre-lot-era Richmond attaches documents to
the BLOCK. RULE for organization/resolution: a key ending `0000` is
block-scope; a parcel chronology must treat it as "somewhere on block 3595
(premises: 51 Greeley Avenue)", never as a specific lot's event. The street
address is the disambiguator a later pass (or the ancestor mortgage) can
resolve to a modern BBL.

## R5-4 — THE BUYER'S LAWYER IS THE HUB (address clustering, measured again)

Richard N. Corash: the c/o address FOR the assignee, the RETURN-TO
addressee, AND the notary on the assignors' acknowledgment - one man, one
address (26 Bay Street), three roles on a two-page instrument. M-004/C-001
confirmed in miniature: the address, not the name, clusters the deal's
control. McKevitt Associates itself is a bare name with no address of its
own - the attorney IS its recorded presence.

## CONFIRMATIONS

- **G-010 on Richmond**: rd `amount $0.00`; the document states two dollar
  figures. The index amount is dead in this era for BOTH custodians.
- **D-3 spread widens**: signed->recorded gap now measured at 0 days (here),
  64 days (run 4), 340 days (ZLDA). Same-day is common where the buyer's
  lawyer walks it in - the clerk stamp reads 2:58 PM on signing day.
- **Ambiguous glyphs, resolved by the right witness**: the dateline day is
  overwritten by hand - the acknowledgment (16 April) settles it (two
  witnesses). The ancestor liber's last digit stays AMBIGUOUS and is marked
  so - the ancestor document itself, in-corpus, is the witness that settles
  it later. Never silently resolve (D-3 corollary held).
- Reconciliation scoreboard: book/page ✓ · recorded date ✓ · doc type ✓ ·
  key block ✓ · roles CONTRADICTED (R5-2) · amount dead (G-010).

## THE PERFECTION CRITERION — the three-part test of a finished extraction

Login 2026-08-22, verbatim: *"you reach extraction perfection when you can
get any doc and perfectly summarize it so that a kid could understand, give
the data points of each event in a data table, and you dont miss a single
event that matters."* This is the definition of DONE for any document, any
source, any era — and each part already has its machinery:

    1. THE KID TEST      the summary reads plainly with zero jargon and zero
                         machinery showing (G-030: simplicity is the product;
                         under six sentences, every flag carried - G-026)
    2. THE TABLE TEST    every event as rows in the eleven columns, anchored,
                         five-state honest (the mechanical-summary gate runs
                         BOTH ways: row -> sentence and sentence -> row)
    3. THE NO-MISS TEST  not a single event that matters is absent - enforced
                         by the stopping rule (all eleven functions ASKED of
                         every page, G-029 every page read) and witnessed by
                         the open-events ledger closing empty

The three fail independently: a perfect table with a jargon summary fails 1;
a beautiful summary with unanchored rows fails 2; both can pass while a
release hiding on page 40 fails 3 — which is why 3 is the one that needs the
ledger, not taste. A bootcamp run is graded against all three, and the VLM
production gate inherits the same three, mechanically.

### ⚠ G-036 — THE KID TEST SIMPLIFIES STRUCTURE, NEVER IDENTITY (correction, same hour)

The first summary rendered under the perfection criterion wrote "a couple
named Crowley" and "a company called McKevitt Associates." Login: *"i like
it but hate when we dont give full name or real context."* That phrasing is
G-024's violation wearing the kid test as a costume — an identity blurred at
summary time is an undecoded token, and "a couple," "a company," "an
investor" are blurs. RULE: the kid test is passed by SENTENCE STRUCTURE
(short sentences, plain verbs, no machinery words), while every party keeps
its FULL RECORDED NAME and every fact its real context — JOHN P. CROWLEY and
MARY M. CROWLEY, his wife, not "the Crowleys"; McKEVITT ASSOCIATES, not "a
company." A child can read a proper name; what a child cannot read is
jargon. Simplicity that costs identity is a failure of test 1, not a pass.

---

# RANDOM-DOCUMENT RUN 6 — `FT_2720000710972` (Bronx 2709/33, AGREEMENT, 38 pp, 1988)

First LONG document read under the perfection criterion — drawn deliberately
large (3.7 MB, the biggest of a 15-folder random sample) to stress test 3.
Read complete: 38 of 38 pages, cold first, rd reconciled after. **Zero new
columns, zero new vocabulary — streak advances on a 38-page instrument.**

    NEW YORK HOUSING TRUST FUND SUBRECIPIENT'S REGULATORY AGREEMENT
    URBAN HOMESTEADING ASSISTANCE (U-HAB), INC. (Program Administrator)
      and PHOENIX HOMESTEADERS HOUSING DEVELOPMENT FUND CORPORATION
    851 Fox Street, Bronx — Block 2709 Lot 33 · Reel 830/431-468
    dated as of 1988-01-22 · signed 1988-01-22 · recorded 1988-03-09

## R6-1 — ⚠ THE FILM PUTS THE COVER AT THE END

Pages 36-38 are the instrument's own front matter — the TITLE PAGE ("This
instrument affects real and personal property... Block 2709, Lot 33"), the
TABLE OF CONTENTS, and the RECORDING ENDORSEMENT (RECORDED IN BRONX COUNTY
1988 MAR -9 A 10:31) — filmed AFTER the exhibits. A reader that stops when
the instrument's text ends never sees the indexing authority, the title
number (REC #12540-Bx, which also stamps Schedule A — an internal join), or
the recorded date. RULE: on film documents the cover walk scans the TAIL as
well as the head; "the end of the instrument" is not the end of the record.

## R6-2 — THE LOT DISSENT, SETTLED BY WEIGHT OF WITNESSES (G-009 at scale)

Exhibit A's HPD form writes Lot/Block "35/2709"; the title page, the
recording endorsement and the rd's BBL (2027090033) all write LOT 33. Three
witnesses against one, and the one is a TRANSCRIBED AGENCY FORM - the least
reliable class of page in the file. Dissent recorded, subject keyed 33.
RULE: exhibit forms are clerk-filled copies; the instrument's own cover and
the register outrank them. Never average, never silently pick.

## R6-3 — A TERM CAN BE A FORMULA, AND IT ASSEMBLES ACROSS 10 PAGES

The regulatory term: "the LATER of (1) twenty-five years from final
disbursement of the Loan or (2) payment of the entire outstanding amount"
(§1, p2) — a CONDITION-kind term whose value is a formula, not a date. Its
running-with-the-land character arrives at §15 (p11), nine pages later, and
its operational detail (resale caps, sweat-equity valuation) in Exhibit F
(pp24-26). The OPEN-EVENTS LEDGER earned its keep for the first time: the
ENCUMBRANCE row opened on p1 could not close until p11 gave it its
character and p26 its machinery. D-7 held, at triple the distance.

## R6-4 — SUBORDINATION WRITES UNDER TITLE (priority), FIRST USE

§16: the First Mortgage held by BANANA KELLY COMMUNITY IMPROVEMENT
ASSOCIATION, INC. (dated 1988-01-22, recorded 1988-02-04, Reel 822 p.721 —
handwritten fills, glyphs partly ambiguous, resolvable against the ancestor)
is made "subject and subordinate" to this Agreement. Written as TITLE ·
modifies per the Definitions table's own line — "TITLE: who holds an
interest, AND IN WHAT PRIORITY... the whole point of a subordination."
First row written under that ruling; if resolution later prefers
ENCUMBRANCE-modifies for subordinations, this entry is the one to revisit.

## R6-5 — THE FUNDING TABLE SELF-CHECKS ACROSS 8 PAGES (two routes, one number)

Exhibit A p2: HTF $114,000 + Banana Kelly weatherization $4,800 + NYC
homesteading $52,000 + homesteaders' downpayments $25,000 + NYC Catholic
Archdiocese loan (7 yrs @ 8½%) $70,000 = $265,800 funded, against stated
total development cost $335,800 — gap $70,000, attributed to sweat equity
by subtraction. Exhibit F p24, eight pages later: "Sweat equity will be
valued at $8.90 per hour and WILL NOT EXCEED $70,000 for the entire
project." Derived and stated agree to the dollar. The self-validating-
document principle (R-003 family) extends to EXHIBIT ARITHMETIC.

## CONFIRMATIONS

- **R4-3 third time**: index parties "URBAN HOMESTEADNG ETC." /
  "PHOENIX HOMESTEADRSETC." — truncation with "ETC." this time; the
  document carries full names and the officers behind them (Genaro Parra,
  President; Rafael Rojas, Secretary; Andrew Reicher, U-HAB Exec. Director).
- **Reconciliation scoreboard**: pages 38/38 ✓ · recorded 3/9/1988 ✓ ·
  reel 830-431 ✓ · BBL ✓ (and it SETTLED the lot dissent) · keyed_by EMPTY
  (pre-trigger debt, third consecutive random draw).
- **The filter carried 14 pages at zero rows**: Executive Order 21
  (pp29-35, a statutory attachment with the recorder's SO IN ORIGINAL
  annotations - G-012), marketing/relocation boilerplate, notary formulary.
  Real text, no function moved.
- Amount $0.00 in the index is CORRECT here, not dead - a regulatory
  agreement has no consideration; the money lives in the recited sibling
  loan documents (Note, Mortgage, Construction Loan Agreement, Assignment
  - the D-6 package, recorded separately).

### G-036a — REAL TERMS STAY; THE SUMMARY TEACHES THEM IN PLACE (login refinement)

Login 2026-08-22: *"the summary i said for a kid is basically saying it has
to be simple enough that its easy to understand but you still have to use
real terms."* This closes a misreading the first self-grade made: "priority"
and "regulatory agreement" in a summary are NOT kid-test failures — they are
the domain's real words, and stripping them is the same information-destroying
move as blurring a name (G-036). The test is whether the term is
UNDERSTANDABLE WHERE IT STANDS:

    FAILS   "subject to a subordination"          (term dropped in bare)
    PASSES  "Banana Kelly's own mortgage agreed to stand behind these
             rules in priority"                   (the term's meaning is
                                                   carried by the sentence)
    FAILS   "the building is encumbered"          (bare)
    PASSES  "the building is bound by strict rules that run with the land
             itself, no matter who owns it"       (ENCUMBRANCE, taught)

So the three layers of the kid test: real NAMES exact (G-036) · real TERMS
kept (this entry) · sentence STRUCTURE simple enough that the term's meaning
arrives with it. A summary that a reader finishes knowing what a
subordination IS has done more than one that avoided the word — and the
row's controlled vocabulary is unaffected either way; this governs only the
render.

### THE FIRST TEST, STATED PLAIN (supersedes the "kid" shorthand)

Login 2026-08-22: *"you want anybody who reads it to understand what
happened and this is the pass that people can understand without feeling
like its overcomplicated."* The audience was never literally a child - it
is ANYBODY: a broker, a lawyer, an owner, a stranger to the file. The pass
condition is one reading, full understanding, and **no felt complexity** -
the reader never senses machinery, never rereads a sentence, never meets a
term the sentence didn't equip them for. Real names exact (G-036), real
terms taught in place (G-036a), and the feeling of simplicity as the grade.
"A kid could understand" survives as shorthand for that standard, not as an
instruction to write for children.

### THE THREE TESTS, NAMED (canonical, login 2026-08-22)

    THE ANYBODY TEST   the summary: anybody who reads it understands what
                       happened - one pass, real names, real terms taught
                       in place, no felt complexity.
    THE DATA TEST      the table: every event as data points that can
                       DRIVE METRICS AND RELATIONS - typed, anchored,
                       five-state honest. The rows are not a record of the
                       reading; they are the fuel for resolution (chains),
                       derivation (what matters today) and every metric
                       computed later. A row a metric cannot compute on,
                       or a chain cannot join on, fails this test even if
                       it is "correct."
    THE EVENT TEST     completeness: never miss an event that would be
                       CONTEXTUALLY IMPORTANT - enforced by every page
                       read, all eleven functions asked of each, and the
                       open-events ledger closing empty. "Contextually
                       important" is the standard: the test is not "did
                       you transcribe everything" but "would the story
                       downstream be wrong or poorer without it."

Earlier names (kid test / table test / no-miss test) are superseded by
these three. A run reports its grade as three verdicts, in this order.

---

## THE FOUR PROCESS LAWS — 2026-08-22 (the vocabulary is closed; these govern HOW reading is conducted)

Three runs across three eras forced zero schema changes, and every strain
point was procedural. Each law below carries the same-day miss that taught it.

### P-1 · THE OPEN-EVENTS LEDGER IS AN ARTIFACT, NOT A HABIT

Run 6: the ENCUMBRANCE row opened on p1 and could not close until p11
("runs with the land") and p26 (the resale machinery). That state lived in
the reader's head — unauditable, and impossible for a per-page extractor.
RULE: a reader of any multi-page instrument MAINTAINS AND OUTPUTS a ledger
table — `event | slot waiting | opened p. | closed p. | by what` — updated
per page, checked before each new page is read, and EMPTY (or honestly
`unread`/`unavailable`) at the end. The ledger's final state IS the event
test's evidence. In production the harness owns this table, not the model.

### P-2 · GUARDS LOAD PER STEP, NOT PER DOCUMENT

Run 5: G-024 was violated at SUMMARY time by a reader who had loaded it at
READING time — "a rule not loaded at the right moment does not exist"
proved on its own author. Extraction has phases: READ (evidence guards:
G-003/029, R4-4 cold-read) → COMPOSE (row guards: G-015..023, R-004) →
RENDER (summary guards: G-024/025/026/036/036a). RULE: each phase begins by
loading ITS guard set. In production this is prompt assembly per step;
in bootcamp it is the checklist consulted at each transition.

### P-3 · A RUN EMITS ROWS, CLAIMS, AND RULINGS-NEEDED

Run 6: subordination was routed to TITLE(priority) unilaterally — defensible
under the Definitions table, and still a judgment call decided in silence.
The bootcamp's own pattern for these is the OPEN RULING (G-019), but a run
had nowhere to put one except deciding it. RULE: rulings-needed is a
FIRST-CLASS OUTPUT beside rows and claims; the row is written under the
best reading, marked `ruling: pending`, and the question queues for the
login. A silent ruling counts against the freeze streak exactly as a
schema change does — the table must not absorb one reader's confidence.
    OPEN: subordination → TITLE (priority) or ENCUMBRANCE (modifies)?
          (first instance: FT_2720000710972 §16)

### P-4 · EVERY TABLE FOUND GETS ITS ARITHMETIC RUN

Run 6: the $70,000 sweat-equity value closed by two routes eight pages
apart (funding-table subtraction on p16; stated cap on p24) — the run's
strongest verification, performed ad hoc. G-033 says the documents already
contain tables; this law says EVERY total, rate, schedule and split found
is summed/checked as a STANDING STEP. Agreement = free confidence, recorded
with both anchors. Disagreement = a FINDING, never smoothed (the ZLDA
FAR 10.0-vs-12.0 conflict stays open to this day, correctly). Exemption
codes gate the money checks (G-014) — the check is conditional, never
unconditional. Self-validation is the only verifier that scales with no
human key.

**NOT ADDED, deliberately:** no twelfth function, no fourth mode, no fourth
test. Every candidate today dissolved into process — which is the freeze
criterion working. Control-clustering (shared addresses/signers: Corash,
26 Bay Street; M-004/C-001/R5-4) stays a CLAIMS pattern; if it keeps
recurring it may someday earn a render section — a product decision, not
an extraction one.

### G-037 · SUBORDINATION → TITLE (priority) — RULED, queue closed

Delegated 2026-08-22 ("subordination should be what you think"). RULING:
**TITLE · modifies.** The Definitions table is the authority and is explicit
— TITLE is "who holds an interest, AND IN WHAT PRIORITY," and priority "is
the whole point of a subordination." The deciding observation: a
subordination changes NOTHING about the lien itself — amount, term, parties
all survive untouched. What changes is its RANK among the interests in the
parcel, and rank is a property of the priority ladder, which is TITLE's
domain. ENCUMBRANCE·modifies would misreport it as a change to the burden.
Shape: from = the party yielding rank · to = the interest advanced ·
quantity = the priority movement (n/a-amount) · term = the governing period.
Resolution builds the priority ladder from these rows. First instance
FT_2720000710972 §16 is updated from `ruling: pending` to this rule.

## ONE BOOTCAMP, PHASE CHAPTERS — the architecture ruling (2026-08-22)

Login raised: extraction bootcamp vs resolution bootcamp vs derivation
bootcamp, and how sources shape them ("a bootcamp on dob docs would
possibly differ"). Settled as follows, from this file's own charter:

**There is never a second bootcamp file.** The header's reason stands — two
copies of a vocabulary drift (measured: five copies had already drifted
before lexicon.py unified them). But bootcamp is a METHOD — read real
material until the model stops moving, one entry per miss — and the method
applies per PHASE, because each phase makes a different claim:

    EXTRACTION chapter   claim: events        tests: anybody · data · event
    RESOLUTION chapter   claim: the chain     tests: TO BE EARNED by chaining
                         one real parcel (candidates: does every event find
                         its place · do accounts balance opening-vs-closing
                         · do entities resolve across instruments) — named
                         now as candidates, PROVEN only by runs, exactly as
                         extraction's three were
    DERIVATION chapter   claim: what matters today   tests: earned later

Case law accrues under the phase's own heading in THIS file; the
vocabulary (functions, modes, effect, states, canon()) is shared by all
three and never copied.

**Sources shape DICTIONARIES, not bootcamps.** The onboarding recipe
already in this file is the answer to the DOB question: a new source gets
its jargon listed, the three questions asked, ONE mapping table written
into that source's own md, and 20 records through the mechanical-summary
gate. A DOB permit differs from a deed in vocabulary and region layout —
claims and dictionary — never in the eleven columns or the three tests.
The day a source genuinely cannot pass through the table is the day this
ruling is revisited, and that failure would be a finding worth more than
the architecture it breaks.

**Sequencing:** extraction bootcamp is live (6 runs). Resolution bootcamp
begins the day one parcel's full document run is extracted end to end —
richmond will get there first (rd 100% · keys 100% · pdfs accruing at the
wall). Derivation bootcamp after resolution holds. Never in parallel from
scratch: each phase's bootcamp reads the previous phase's OUTPUT, so
starting one early means bootcamping on material that is still moving.

---

# RANDOM-DOCUMENT RUN 7 — `RC_103439` (Richmond 2197/12, DEED, 7 pp, 2016)

Modern-Richmond first. Cold read 7/7 pages (instrument + Schedule A + RP-5217
+ certification — the supporting docs ride in the same pdf), rd reconciled
after. **Zero new columns, zero new vocabulary — streak: four consecutive.**
Instrument 601980 · recorded 2016-04-25 (made 2016-04-08, contract 2016-04-05).

## R7-1 — THE SPLIT ESTATE: A DEED CAN KEEP MORE THAN IT GIVES

LUCY GUERRIERO conveys 39 Nostrand Avenue to RONALD FICAROTTA and DARLYNE
FICAROTTA **as tenants by the entirety** — and "HEREBY RESERVES LIFE
ESTATE." One fee becomes two estates: the REMAINDER moves, the LIFE ESTATE
stays. ONE event, TWO TITLE rows:

    row 1  TITLE · transfers · remainder in fee, Lucy -> the Ficarottas,
           term = fee simple absolute UPON termination of the life estate
           (tenancy: by the entirety - carried in term qualifiers)
    row 2  TITLE · creates · life estate BY RESERVATION (severed from the
           fee, held by the grantor), term = the life of Lucy Guerriero

Downstream this is load-bearing: possession stays with Lucy for life with
NO occupancy event; her death EXTINGUISHES row 2 and matures row 1 with no
recorded instrument at all — a chain that expects a closing document for
every interest will wait forever. G-015 held ("the estate is the term") and
stretched: two estates from one fee, each row carrying its own.

## R7-2 — $0 CAN BE TRUE: THREE WITNESSES MAKE A GIFT, NOT A GAP

M-007 says never record $0 tax as $0 price. REFINED, not broken: here THREE
independent in-document witnesses agree — both transfer-tax stamps $0.00
(code 6095) · the RP-5217's own "Full Sale Price: $0" · condition box A
"Sale Between Relatives" checked — plus all parties at the SAME ADDRESS
(39 Nostrand). Consideration records as **$0 — gift/family transfer**, a
VALUE, not `unresolved`. The rule's shape: one $0 witness = a signal to
explain; a CONVERGENT SET including the sale-price form's own $0 = the
explanation itself. The recited purpose closes it: the deed preserves
Lucy's veterans/senior/STAR exemptions (RPTL 458/467/425 recited) — the
classic estate-planning shape, stated in the instrument.

## R7-3 — MODERN RICHMOND: THE COVER IS STRUCTURED, AND THE 5217 RIDES ALONG

R-005 (the modern cover is extraction already done) extends to Richmond's
CRFN-era equivalent: doc type · page count · block/lot · parties WITH
DECLARED ROLES (grantor/grantee — contrast 1971's role-blind "Mortgagor")
· the supporting-document list · fees · instrument #. And the RP-5217 in
the same pdf carried the facts the deed never states: sale price, the
relatives condition, building class B2, assessed value $32,563, 2-3 family
use. Reading scope = every page of the file, again (L-9's third proof).

## R7-4 — "And Others" IS COVER SHORTHAND, NOT INDEX TRUNCATION (corrected same hour)

⚠ FIRST VERSION OF THIS ENTRY WAS WRONG, caught at grading by the check it
should have had before recording: the claim "Darlyne exists only in the
deed body" was written from the COVER without reading the INDEX party list
- a one-look claim (G-004's shape, on a table instead of an image). The
index carries ALL THREE parties. Corrected findings:

- The COVER names one party per side + "And Others"; the INDEX is complete.
  Cover shorthand ≠ index truncation - the two must be checked separately.
- The TENANCY (by the entirety) remains instrument-only. True as written.
- NEW, found by the verification itself: modern Richmond indexes EVERY
  PARTY TWICE - once "GUERRIERO LUCY" (last-first, role GRANTOR) and once
  "LUCY GUERRIERO" (first-last, role Grantor). Six rows for three people:
  the N-4 case-variant split PLUS name-order variance in one table. A
  party count reads 2x; a name join must normalize BOTH case and order.

RULE: a claim about what the index lacks is made by READING THE INDEX,
never inferred from the cover - and a wrong recorded finding is corrected
in place, loudly, the same day it is caught.

## CONFIRMATIONS

- Ancestor rung: prior deed 1977-12-23, recorded 1977-12-28, Liber 2230
  p.112 (Lucy's 39-year tenure, chainable).
- The attorney hub, third sighting (R5-4 family): LOUIS LEPORE = notary +
  return-to; commission-expiry struck and handwritten "May 5, 2018".
- Metes: 40 x 100 ft, bearings-and-distances (modern form), closes.
- Reconciliation: instrument/recorded/BBL/type all ✓ · keyed_by=parcel ✓
  (richmond org 100% covers the modern era) · index amount $0.00 is TRUE
  here — first document where the index price and the truth agree.

---

# RANDOM-DOCUMENT RUN 8 — `2003010601184002` (Queens 16186/32, MTGE, 43 pp, 2002/2005)

First digital-era ACRIS document. Cold read 43/43 (cover count 42 + 1 cover
✓), rd reconciled after, sibling row pulled for the package. **Zero new
columns, zero new vocabulary — streak: five consecutive.** One ruling
queued (P-3 exercised for the first time).

    MORTGAGE, 113 ROCK HOTEL CORP. -> INTERBAY FUNDING, LLC · $320,000
    147 Beach 113th Street, Rockaway Park (Queens 16186/32, 3-family)
    executed 2002-12-11 (ack, KINGS county) · recorded 2005-10-19 15:52:19
    maturity 2018-01-01 · lender loan no. 2019007 (every page footer)

## R8-1 — MAP-LOTS ARE NOT TAX LOTS: THE DESCRIPTION CITES A DIFFERENT NAMESPACE

Schedule A describes "Lot Nos. 359, 360, 361 and 362 in Block No. 7" — of
the **"Map of Rockaway Park" FILED IN 1889**. The tax parcel is Block 16186
Lot 32, ONE lot. A keyer that reads lot numbers out of a metes description
would mint FOUR phantom parcels in a block namespace that stopped existing
generations ago. RULE: the description's lot citations are a REFERENCE
(the filed map is the authority they point at), never a key; the key comes
from the cover/index BBL, and the rd proved it right (both package rows:
4161860032). Same family as the reel-vs-BBL trap (a number's namespace is
part of the number).

## R8-2 — THE PACKAGE IS THE STORY; ONE MEMBER IS ONLY A CLAUSE OF IT

Schedule A: "Being the same premises CONVEYED to the parties of the first
part herein by deed recorded SIMULTANEOUSLY HEREWITH." The sibling
`...001` (rd): **CORRECTION DEED, MATTHEW SAFOS -> the corporation, $0,
recorded 2005-10-19 15:52:18 — ONE SECOND before the mortgage.** And the
mortgage's signer: Matthew Safos, President of the borrower. So: a
purchase-money mortgage signed 2002-12-11 whose recording waited 1,043
days — and the CORRECTION deed recorded with it reads as why. ⚠ HYPOTHESIS,
NOT FACT: "title defect cured before the lender would record" is an
inference from timestamps and the word CORRECTION; the sibling's 3 pages
were not opened this run, and the inference is labeled so a later reader
knows it was never verified. (M-012's rule at package scale: capture the
evidence, do not judge.) D-3's new extreme:
the sign->record gap now spans 0 to 1,043 days, and here the LAG ITSELF
is evidence — a package recorded years late with a correction deed at its
head is a title-cure story told entirely by timestamps.

## R8-3 — THE DIGITAL INDEX CARRIES MONEY (G-010 IS FILM-SCOPED), AND DISAGREES WITH ITSELF ELSEWHERE

rd `amount: $320,000.00` echoes the instrument exactly — G-010 ("the index
amount is dead") is hereby SCOPED to the film/pre-ACRIS era; digital-era
amounts are live and usable as a witness. But the same index calls the
property 3-FAMILY on the mortgage row and 2-FAMILY on the deed row one
second apart — and the examiner's handwritten note on p2 says "converted
rooming house." Index fields are per-row claims, never parcel facts.

## R8-4 — THE ITEMIZED TAX PANEL IS ITS OWN RATE TABLE

County $1,600 (0.50%) + City $3,200 (1.00%) + TASF $800 (0.25%) + MTA
$800 (0.25%) = **$6,400 = 2.00% of $320,000, exact to the dollar.** The
digital cover doesn't just validate the principal (R-003) — its itemization
IS the era's rate schedule, self-labeled. Any future principal check can
verify per-line, which localizes a mismatch to the specific tax instead of
the total.

## RULING QUEUED (P-3, first use)

    OPEN: does an IN-DOCUMENT absolute assignment of leases & rents
    (§1.2, "present, absolute assignment... not for additional security
    only", license back) and the §1.3 UCC security interest in personal
    property earn their OWN ROWS, or attach as conditions/claims to the
    ENCUMBRANCE row? Rows written this run: CAPITAL + ENCUMBRANCE only,
    with both collateral grants as claims marked `ruling: pending`.
    (Standalone AL&R documents already have their answer — M-010:
    collateral, not new money. The question is the in-document form.)

## CONFIRMATIONS

- G-018 held: CAPITAL creates (lender->borrower, $320,000, maturity
  2018-01-01 — the day's first FULLY SUFFICIENT capital event: parties +
  principal + maturity all read) · ENCUMBRANCE creates (lien, until
  satisfied), one event_id.
- The Note holds the rate — `interest_rate: unread, lives in the Note
  (unrecorded)` — the honest pointer, not a fabrication (the 1981 6.0%
  lesson standing).
- Due-on-sale Article 7 as claims, incl. the 49%-equity transfer
  threshold — a fact brokers ask about, captured with its anchor.
- D-9 filter: ~30 of 43 pages produced zero rows and zero claims
  (remedies, waivers, environmental boilerplate, ERISA, notices).
- Reconciliation: pages 43 ✓ · recorded-to-the-second ✓ · BBL ✓ (one lot,
  not four) · amount ✓ · keyed_by=parcel ✓ (early-digital range was
  already keyed).

---

# RANDOM-DOCUMENT RUN 9 — `RC_1003663` (Richmond blk 3333, DEED, 2 pp, 1958)

Oldest document yet (the custodian holds back to 1945). Cold read 2/2,
reconciled after — party list VERIFIED IN FULL before any claim about it
(the R7-4 lesson, applied). **Zero new columns, zero new vocabulary —
streak: six consecutive.** Instrument 4567 · Liber 1420/393-394 ·
signed 1958-04-17 · recorded 1958-04-22 PM 2:43.

    BARGAIN AND SALE DEED (with covenant vs grantor) - Blumberg form 691
    CARMILLA BIGGICA, also known as CARMELA BIGGICA -> PIETRO BIGGICA
    both at No. 284 Atlantic Ave., Staten Island 5
    THE PREMISES: a FIVE-FOOT STRIP x 100 ft deep - "the most
    northwesterly 5 feet of Lot No. 683" on the Map of Burgher Farm,
    Linden Park, SURVEYED 1870 (Map No. 290) - tax block 3333 only in
    the clerk's hand on the back panel

## R9-1 — THE INDEX EXPLODES AN ALIAS INTO A SECOND PERSON

The instrument says one woman with two spellings: "CARMILLA BIGGICA, also
known as CARMELA BIGGICA." The index (verified in full) lists THREE party
rows: Grantor BIGGICA CARMILLA + Grantor BIGGICA CARMELA + Grantee
BIGGICA PIETRO — **the aka became a phantom second grantor.** A party
count reads two sellers; an entity spine hunts a woman who does not
exist. And the DOCUMENT is the identity authority: "also known as" is the
record itself asserting sameness — an alias edge for free, stated under
signature. RULE: aka/fka phrases are ENTITY-IDENTITY CLAIMS (capture the
edge); index party rows sharing a role on an aka instrument are variant
spellings of one party until the instrument says otherwise. Third member
of the index-party family: truncation (R4-3), dual-entry casing (R7-4),
alias explosion (R9-1).

## R9-2 — A DEED CAN CONVEY FIVE FEET (the partial-premises rule, 1958 form)

The conveyance is a 5 x 100 ft sliver of a map lot — a side-strip
adjustment between family members. The block-scope key (5033330000, lot
0000 - R5-3 again) is CORRECT for organization, but resolution must read
the PREMISES, not the key: a chain that treats this as "the parcel
transferred" moves a whole lot on paper when five feet moved on earth
(M-005's key-set rule at sub-lot grain). And R8-1 held ONE RUN LATER in
its 1870 costume: Lot Nos. 682/683 are FILED-MAP lots (Map No. 290,
surveyed 1870); the custodian keyed the tax block, never the map lots.

## CONFIRMATIONS

- **The 1958 price witness is a FEDERAL documentary stamp** (NY had no
  RETT until 1968): stamp present, pen-cancelled, denomination
  UNREADABLE in this scan -> consideration = $10 recited, stamp unread,
  price unresolved; family markers (same surname, same address) captured
  per M-012, verdict left to derivation.
- The attorney hub, FOURTH sighting: JOSEPH A. LOBUE = witness + notary
  + record-and-return (3074 Amboy Road). The pattern is now 4-for-4 on
  Richmond family-scale documents: one lawyer IS the transaction's
  recorded infrastructure.
- Reconciliation: liber/page ✓ recorded ✓ block ✓ film-era amount $0.00
  (G-010 scope holds) · keyed_by=parcel ✓.

## P-5 · THE BOOTCAMP LOOP (login 2026-08-22: "run it, grade and ask why
## it matters, adjust, run again")

The loop the runs have been converging on, now stated as law. Every run:

    1  DRAW      random from the DISK store; coverage-aware (note era/
                 type/shape drawn so far; prefer unseen shapes; never
                 cherry-pick ease)
    2  READ COLD the whole file, open-events ledger maintained (P-1),
                 per-step guards loaded (P-2)
    3  RECONCILE against the rd row, field by field; NEGATIVE claims
                 about the index require reading the index (R7-4);
                 package siblings pulled when the document cites them
    4  VERDICTS  the three tests, graded honestly, WITH the miss ledger
                 - an unflagged miss found later costs double
    5  WHY-PASS  ask "why does it matter" of everything kept - as a
                 FILTER it selects claims; as an ANSWER it may only
                 produce LABELED HYPOTHESES (run 8's lesson)
    6  ADJUST    new rules/refinements/corrections written in place;
                 judgment calls to the RULINGS QUEUE (P-3), never
                 decided silently
    7  BANK      the entries ride the nightly push (or refresh.ps1 now)
    8  REPEAT    the adjustment shapes the next draw

The streak (runs with zero schema changes) is measured ACROSS this loop;
grading is INSIDE it. The loop is what a production harness will one day
execute with a VLM in step 2 - which is why every step must stay
mechanical enough to hand off.

---

# RANDOM-DOCUMENT RUN 10 — `RC_1041792` (Richmond blk 782, DEED, 2 pp, 1933/1938)

Deepest era yet, and a new ARTIFACT CLASS: not a scan of the instrument but
the clerk's TYPEWRITTEN TRANSCRIPTION into Liber 810 pp.240-241 (pre-
photostat practice: deeds were retyped into bound volumes; "(ER)" =
examiner's initials). Cold read 2/2, reconciled. **Zero new columns, zero
new vocabulary — streak: seven consecutive.** Instrument 1563 · made
1933-10-14 · recorded 1938-10-21 10:30 AM.

    WARRANTY-COVENANT DEED (five covenants, "will forever warrant")
    ENRICO VERANZINI and ANNA VERANZINI, his wife
      -> ALBERT RUSSO and DESDAMONA RUSSO, his wife, "of the same place"
    Willowbrook Road plot (metes vs Francesco Damiano's line) · Section 2,
    Block 782 · $100 recited · federal stamp "$1.00 cancelled" (clerk-
    transcribed) -> bound <= $1,000 at 50c/$500 · SUBJECT TO a $3,000
    record mortgage · Anna signs BY HER X MARK

## R10-1 — THE LIBER TRANSCRIPTION IS A DIFFERENT WITNESS CLASS

Nothing on these pages is an image of the instrument: signatures are typed
names + "(L.S.)", the tax stamp survives only as the clerk's words "(Stamp
$1.00 cancelled)", and the fee/instrument metadata ride as parentheticals
inside prose. Consequences: (a) every fact is SINGLE-WITNESS by
construction — there is no original to cross-read, so the two-witness
doctrine cannot apply within the document; (b) transcription errors are
undetectable locally and only neighboring instruments can corroborate
(R-002's chain-as-reader is the ONLY verifier for this era); (c) the
clerk's parentheticals are structured metadata wearing prose — extract
them deliberately (No. / FEE / stamp / "(For RICHARD CONDON, 29
Broadway)" = the return-to).

## R10-2 — A DEED CAN CARRY A RELEASE OF A RECORDED CONTRACT (the land-contract era)

Mid-description: "an Agreement between them dated August 20th, 1931, for
purchase of the aforesaid described premises IS HEREBY CANCELLED; said
agreement was recorded... in Liber 727 page 463 of Deeds." The Russos had
been buying ON CONTRACT since 1931; this deed completes the purchase and
extinguishes the recorded contract — TWO rows, one event: TITLE·transfers
(the fee) + ENCUMBRANCE·releases (the 1931 recorded purchase agreement,
ancestor Liber 727/463 — a recorded contract clouds title regardless of
owner, so ENCUMBRANCE by the definitions table). The land-contract era
means deeds of this vintage routinely close a years-long story the index
shows as two unrelated instruments seven years apart.

## R10-3 — THE PRE-WAR INDEX HAS NO PARTIES AT ALL

The rd row carries book/page/type/date/block — and NOT ONE party row. The
Veranzinis and Russos exist nowhere but the liber page. M-001 measured
party coverage as thin (19%); 1938 shows the floor: ZERO. Any party-keyed
search is blind before some era boundary; the DOCUMENT is not just the
best witness here, it is the ONLY one. (The index amount $0.00 also holds
G-010's film-era scope.)

## CONFIRMATIONS

- **D-3's new extreme: 1,833 days** sign->record (1933->1938, the
  Depression era) — the gap now spans 0 to 1,833 days across ten runs;
  any pipeline assumption of "recorded shortly after signed" is dead on
  arrival in this corpus.
- G-016 bound, on a transcribed stamp: consideration > $100 recited,
  <= $1,000 by the $1.00 federal stamp at 50c/$500 — the bound survives
  transcription because the CLERK recorded the stamp's value in words.
- Subject-to recital: observes · ENCUMBRANCE · the $3,000 record
  mortgage (unidentified — no liber cite; `unread` pointer, resolvable
  by the block's chain).
- "Her X mark": Anna Veranzini signed by mark — a literacy/capacity
  claim (C-001 family), and the witness/notary GEORGE J. PALMER is both
  witness AND notary (hub pattern, fifth sighting, 1933 edition).
- Block-scope key 5007820000 ✓ (R5-3 five decades before run 5's case).

### R10 addendum — RENDER MISS, CAUGHT BY THE LOGIN (G-026's shape, person-scale)

The run's chat summary wrote "Anna couldn't write." The record proves her
X MARK, witnessed — the mark is the fact; illiteracy is its usual but not
only cause (infirmity and custom also signed by mark). The md entry was
hedged ("a literacy/capacity claim"); the SUMMARY flattened it — the row
honest, the sentence over-claiming, G-026's laundering one level down (a
person's capacity instead of a quantity's split). RULE SHARPENED: facts
about PERSONS (capacity, literacy, relationship, control) get the same
render discipline as quantities — the sentence states the evidence ("signed
by her X mark") and may name the usual meaning only AS the usual meaning.
"His wife" needed no hedge - the instrument recites it verbatim.

### P-5 step 5, SHARPENED (login 2026-08-22: "the why it matters is
### regarding the document or the events of said document")

The why-pass has TWO whys with different owners, never blended:

    EVENT-WHY     asked of rows and claims. Every answer must terminate
                  at a function, a chain, or a derivation question -
                  "why does the tenancy matter" = survivorship moves
                  title with no recorded paper (the TITLE row's future).
                  A why that cannot find its event names a keep that
                  should not have been kept. THIS is the why-pass.
    PIPELINE-WHY  asked of the DOCUMENT as artifact - what it teaches
                  about reading, acquiring, indexing (liber = single-
                  witness class; film covers at the end; pre-war index
                  partyless). These are R-ENTRIES - they belong to the
                  harness and the freeze decision, and NO parcel's chain
                  ever contains one.

The grade judges both; the why-pass reports only the first; the second
lands as findings. Blending them is how a reader ends up narrating method
in a summary (G-030's failure) or losing a pipeline lesson inside a
parcel story.

---

# RANDOM-DOCUMENT RUN 11 — `FT_2970000594197` (Bronx 3214/66, EXT&MOD, 8 pp, 1983/84)

Film-era EXTENSION AND MODIFICATION OF MORTGAGE — the modification shape's
first bootcamp. Cold read 8/8, reconciled. **Zero new columns, zero new
vocabulary — streak: eight consecutive.** Reel 542/496-503 · as of
1983-12-31 · Parnes ack 1984-03-31 · bank ack 1984-04-16 · recorded
1984-04-30 13:06.

    EMIGRANT SAVINGS BANK (successor by merger to Prudential Savings
    Bank) & HOWARD PARNES (455 Central Park Ave, Scarsdale) — owner,
    "now owns the premises" · 2505 Aqueduct Avenue, Bronx (NW corner
    W 190th St) · Section 11, Block 3214, Lot 66

## R11-1 — THE LIBER SERIES IS A NAMESPACE, AND THE INDEX KEEPS ONE CITE OF SIX

The recital chains SIX ancestors: L.1300 Mp.429 · L.2810 Mp.109 · Consol.
Agmt L.2810 Mp.103 · L.3364 Mp.338 · Consol. Agmt L.3368 Mp.177 · L.3855
Mp.259 — "Mp." = the MORTGAGES liber, a different book series from run
10's "Liber 727 of DEEDS": same numbers, different shelves; a cite
without its SERIES is ambiguous (the namespace family's fifth member).
And the rd remarks holds "EXT.& MOD. L. 1300 MP. 429,ETAL" — ONE cite
plus etal. FIVE ancestors exist only in the document. M-002 refined: the
index's citation rung UNDER-COUNTS; the document is the citation
authority, the index only the hint that citations exist.

## R11-2 — NON-RECOURSE ARRIVES BY EXTENSION (the exculpation clause)

Page 2: the bank "agrees to enforce payment... SOLELY AGAINST THE
PROPERTY... and waives its right to enforce payment thereof by
DEFICIENCY or other personal judgment against the party of the second
part or any other person." A 1983 extension converted a recourse debt to
NON-RECOURSE — the lien survives, the personal claim dies. Captured as a
TERM-CLASS CLAIM on the CAPITAL row (anchored); resolution should carry
recourse/non-recourse wherever stated, because it changes what a default
can reach — a fact lenders and brokers price directly.

## R11-3 — TWO SIGNING CLOCKS ON ONE INSTRUMENT

as-of 1983-12-31 · Parnes acknowledged 1984-03-31 (Westchester) · the
bank 1984-04-16 (New York Co.) · recorded 1984-04-30. The parties signed
SIXTEEN DAYS APART — "executed" is not even one date per instrument; it
is one date PER SIGNATORY. D-3 extended: the provenance slots hold
signed-per-party when the acks differ; the earliest binds nobody until
the last, and the as-of predates them all by a quarter.

## CONFIRMATIONS

- qty_role discipline (L-2) live: consolidated face $250,000 vs unpaid
  $60,493.17 — the row carries the UNPAID balance; the face is a recited
  claim. A single-row reading would report 4x the real debt.
- THE RATE IS STATED, twice: 8-1/2% to 1984-01-15, 13-1/2% after — the
  Volcker-era repricing visible in one clause; extension = refi at +5
  points. New maturity 1987-01-01; payment $2,052.85/mo; prepayment 1%
  premium on 30 days notice; due-on-sale option.
- Register catch-all again: rd type "AGREEMENT" for an instrument whose
  own cover says EXTENSION AND MODIFICATION OF MORTGAGE (D-6a family) —
  the form line outranks the type code (G-008).
- Bank signer's name partially legible (Arthur D. McC—land, VP) — held
  at moderate confidence, not asserted (G-004).
- Reconciliation: pages 8 ✓ reel 542-496 ✓ BBL 2032140066 ✓ parties ✓ ·
  amount $0.00 (film scope holds) · keyed_by EMPTY (pre-trigger debt).

### P-5 step 5, RENDER RULE (login 2026-08-22: "after each why a more
### simple concise one sentence of it")

Every event-why is delivered as a PAIR: the technical why (terminating at
its function/chain/derivation question) followed by ONE plain sentence —
the anybody test applied to the reasoning itself. If the plain sentence
cannot be written, the why is not yet understood; if it needs two
sentences, the why is probably two whys. The pair reads:

    WHY   [technical: where it terminates and what consumes it]
    =     [one sentence anyone understands]

# RANDOM-DOCUMENT RUN 12 — RC_1002473 · DEED · Vol 396 PG 339 (1912)

2 pages, liber transcription era. WOOD HARMON RICHMOND REALTY COMPANY →
EMMA WALDEN (335 Bloomfield Street, Hoboken, NJ), lots 15 and 16 on the
1906 plan "SOUTH NEW YORK, Addition Number Four" (surveyed by Lewis T.
Haney; filed 1907-07-05 as Map No. 995-B). $1 recited. Made 1912-09-03,
acknowledged 1912-09-05 (Leonidas Keever, VP, before Elizabeth Roth,
Commissioner of Deeds, New York County; attest John H. Storer,
Secretary), recorded 1912-09-25 9 A.M. (C. Livingston Bostwick, Clerk).
Return "For Grantee". Rd: keyed_by=parcel, key=5004120015;5004120016,
book/page/date exact, amount $0.00, ZERO party fields (all keys printed
— R7-4 satisfied; the negative claim is safe).

## R12-1 — THE SUNSET COVENANT (an encumbrance with an expiry date)

The deed carries a full developer restriction scheme — dwelling-only
(detached/semi-detached), minimum cost $2,000 one-family / $3,000
double, ≥2 stories, cellar required, no flat roof, 15-ft setback from
Woodbine Avenue, stable ≥60 ft back, fence pre-approval by a company
officer, a prohibited-uses list (livery/milkman's stables, piggery,
slaughter house, forge, gunpowder/glue/varnish works, bone boiling,
tannery, brewery, distillery, HOSPITAL, noxious trades), and no liquor
sales — and then kills itself: "all restrictions and covenants ... shall
continue in force until the first day of January, 1915, and no longer."
ENCUMBRANCE·creates with term = expires 1915-01-01. The existing term
slot holds it (0 new columns), but the DERIVATION consequence is the
lesson: an expired scheme is EXTINCT — today's parcels carry none of
this, and a decoder that surfaces a 1912 no-liquor covenant as a live
restriction fails the product. Mirrors the stage model's renewals/expiry
logic: terms have clocks, and the clock's state at READ TIME is part of
the answer.

## R12-2 — THE NO-WITNESS PRICE (a third price state, by era)

$1 "and other valuable considerations" recited; NO tax stamp anywhere on
either page. FACT: this document offers zero price witness. ⚠ HYPOTHESIS
(era context, not read from the page): 1912 sits in a gap where no
federal conveyance stamp was required and NY's transfer tax did not yet
exist — deeds of this window may be UNWITNESSABLE as a class, not merely
unread. Distinct states: unread (witness exists, not yet read) vs
unavailable (no witness regime existed to consult). The stamps-rule
("$0 never verifies, stamps rule") presumes a stamp REGIME; where none
existed, price resolves `unavailable` honestly instead of hanging
forever as unread. G-026 discipline applied: the mark on the page is the
fact; the era explanation is labeled.

## R12-3 — MAP LOTS THAT BECAME TAX LOTS (the namespace's benign case)

The deed conveys PLAN lots 15 and 16 (Map No. 995-B); the rd key asserts
TAX lots 5004120015 and 5004120016 — block 412, lots 15 and 16. Same
numbers. ⚠ HYPOTHESIS: the Staten Island tax map adopted the filed-plan
lot numbers in this block, so plan-lot = tax-lot here. Even if true, the
ROUTE-3 GUARD stands unchanged: the deed cites the MAP namespace and the
key asserts the TAX namespace — their agreement is a fact about THIS
block, verified by the county's own keying, never a license to equate
the namespaces elsewhere (the 1889 and 1870 runs prove they diverge).

## CONFIRMATIONS

- Zero-parties rd row, 1912 (trap family member 3, previously seen
  pre-war): Wood Harmon and Emma Walden exist ONLY in the document — the
  index cannot surface this deed by any party search. Party coverage for
  this era comes from extraction alone.
- Printed-form deed with handwritten fills: the covenants are PRINTED
  (the developer's standard scheme), the parties/lots/dates handwritten
  — form text repeats across the subdivision's deeds, a future
  cross-document compression signal for extraction at scale.
- amount $0.00 with $1 recital: consistent with R12-2; no disagreement.
- Reconciliation: book 396 ✓ page 339 ✓ recorded 9/25/1912 ✓ DEED ✓
  image present ✓ · keyed_by=parcel (both lots keyed — multi-parcel key
  observed working).

# RULINGS DECIDED 2026-08-22 (delegated: "do what you think is best")

## RULING: in-document AL&R / UCC = OWN ROWS (run 8 queue item)

An assignment of leases and rents, or a UCC/fixture grant, made INSIDE a
mortgage instrument gets its own COLLATERAL row (same instrument, linked
to the parent CAPITAL row) — never folded into the mortgage's
conditions. Deciding principle: ADDRESSABILITY. Later instruments target
these packages specifically (assignments and releases of L&R arrive as
separate recorded documents); a resolution chain can only attach to a
row, and a condition has no address. The same lesson the phase docs
taught about configs — what is unaddressable is not merely hidden, it is
unusable. Cost: one extra row per financing package. Benefit: the chain
never dead-ends when the L&R is later assigned or released separately.

## RULING: modifies-row orientation — the one-line law

A modifies row keeps the ORIGINAL row's direction — obligor → holder —
because the arrow names the obligation, never the paperwork; whoever
initiated the amendment, the debt still points the same way.
(Corollary: a modification that TRANSFERS the holder side is two rows —
assigns + modifies — not one row with a bent arrow.)

Rulings queue: EMPTY as of 2026-08-22.

# RANDOM-DOCUMENT RUN 13 — RC_1043006 · CONSOLIDATION (CEMA) · 2009

27 pages, modern Richmond, the largest RC draw yet. New York
Consolidation, Extension, and Modification Agreement (Fannie/Freddie
Form 3172) dated 2009-08-25, recorded 2009-09-16: MICHAEL HELLER and
JEAN HELLER, 37 Gwenn Loop (block 1965 lot 92) with BANK OF AMERICA,
N.A. One instrument = agreement (7pp) + Exhibit A chain list + Exhibit B
metes + Exhibit C Consolidated Note + Exhibit D Consolidated Mortgage
(Form 3033, 11pp) + Section 255 Tax Law affidavit. Chain: 2007 mortgage
Document# 216849 to MERS as nominee for Countrywide Bank FSB, $399,900
(recorded 2009-09-11... 09/11/2007), unpaid $390,964.05 + new gap
mortgage $17,635.95 = single lien $408,600.00 — the arithmetic
self-checks to the penny. Restated terms: 5.875% fixed, $2,417.02/mo
from 2009-10-01, MATURITY 2039-09-01. Exercised the fresh orientation
ruling (obligor→holder: Heller → Bank of America on the modifies row)
and the package-component row logic on its first day.

## R13-1 — CEMA ANATOMY + THE §255 AFFIDAVIT (the exemption documents itself)

Mortgage tax was paid ONLY on the new money: $331.54 on $17,635.95 —
not on the $408,600 face. The instrument carries its own justification:
a sworn affidavit under Tax Law §255 (Jerri Ann Cirino, attorney for
the bank) reciting the 2007 tax already paid ($8,167.95 on $399,900)
and the new-money tax due. The CLAUDE.md trap confirmed in the wild: a
naive rate×face stamp check flags every CEMA; the affidavit IS the
exemption's paperwork and must be read as the price-witness for the
consolidation. Face ≠ taxable base on consolidations, by design.

## R13-2 — EXAMINER MARGINALIA, VERIFIED (a third voice in the document)

Exhibit A carries handwritten annotations in a clerk/examiner hand:
"N/K/A Bank of America NA" on the Countrywide mortgagee, "mtge tax pd
$8,167.95", "mtge tax to be pd ~$330". The typed §255 affidavit later
CONFIRMS the tax figures — the marginalia was the examiner reconciling
the chain, and the document itself corroborates it. Two consequences:
(1) handwriting on modern typed instruments is not noise — it can carry
tax facts and chain corrections; (2) the lender chain rides CORPORATE
SUCCESSION ("N/K/A" — Countrywide became Bank of America), not a
recorded assignment; MERS-as-nominee resolves by merger history, not by
an instrument. Resolution must not demand an assignment document that
never existed.

## R13-3 — FIVE NUMBERS ON ONE INSTRUMENT (rd chose the land doc#)

Cover Document Id 311973 · LAND DOC# stamp 308983 · lender's Doc ID
00021066707208009 · Loan # 210667072 · Title # 09-7405-791429-SI. The
rd row's instrument field holds 308983 — the LAND DOC number, not the
cover's Document Id. The namespace family's rule sharpened: even
WITHIN one custodian's cover page there are two candidate "document
numbers", and the index picked the stamp, not the header. Verify by
recorded date + parcel, never by whichever number is largest on the
page.

## R13-4 — THE INDEX IS AMOUNT-BLIND WHERE THE MONEY IS (debt maturity lives in extraction)

rd amount: $0.00 — for a $408,600 consolidation with a stated rate,
payment, and maturity date. The complete debt-maturity answer (5.875%,
$2,417.02/mo, matures 2039-09-01) exists ONLY inside the pdf. This is
the debt-maturity product's evidence in one document: the index can
say a consolidation happened; only extraction can say what the debt IS
and WHEN it comes due.

## CONFIRMATIONS

- Cover party block compresses ("And Others") while the INDEX carries
  all three parties in full — the inverse of the film truncation trap;
  the cover's parties block is not the index and neither is the other.
- Consolidation arithmetic pass: 390,964.05 + 17,635.95 = 408,600.00 ✓
  (P-4 satisfied by the instrument's own figures).
- Gap mortgage (Exhibit A item 1) listed "To Be Duly Recorded" —
  package sibling pending at execution; CAPITAL·creates row carried
  with recording-state unknown rather than invented.
- No rider boxes checked on the consolidated mortgage; 1-2 family
  dwelling boxes checked on agreement §X and mortgage §25 consistently.
- Two same-day acks, different counties (borrowers Richmond p7, bank
  officer Eileen Nicklaus Suffolk p5-6) — D-3 per-signatory clocks, span
  0 days this time. Notary Michael J. Cirino and affidavit attorney
  Jerri Ann Cirino share a surname — observation only, no claim.
- Reconciliation: parcel 5019650092 ✓ (= tax map info "9-1965-92" on
  p25) · type CONSOLIDATION AGR ✓ · recorded 9/16/2009 ✓ · parties 3/3
  full-printed ✓ · instrument = land doc# (R13-3) · amount $0.00
  (R13-4).

# RANDOM-DOCUMENT RUN 14 — RC_103895 · TRUSTEE'S PARTIAL RELEASE · 1944

6 pages, typed liber transcription (book 865 pp.97-102), the first
CORPORATE-TRUST instrument drawn. Made 1943-12-30, recorded 1944-02-04
2:02 P.M. (Charles F. Pallister, Clerk; return to Title Guarantee and
Trust Co., 56 Bay St., St. George). CITY BANK FARMERS TRUST COMPANY
(22 William Street, Manhattan), as Trustee under Brooklyn Edison's
Mortgage Trust Indenture, releases-and-quitclaims to BROOKLYN EDISON
COMPANY, INC. (360 Pearl Street, Brooklyn), for $1, four Arthur Kill
waterfront parcels — "Parcel No. 29" of the indenture, block 7167 —
because Edison's board resolved the land no longer necessary and sold
it to ROSEVILLE IMPROVEMENT COMPANY, INC. for $67,500 ($32,500 cash +
$35,000 purchase-money bond and mortgage). The 1936-05-15 indenture is
a BLANKET lien ("all its plant and property then or thereafter owned or
acquired") recorded in TWO counties (Kings liber 8113 mtges p.266;
Richmond Liber 742 mtges p.1; 1938-11-15 supplement Kings 8322/79,
Richmond 768/541). Rest-of-lien-unaffected clause. Executed Walter
Brown, VP (resides 12 Cole Terrace, New Rochelle); attest H. Katterner,
Asst. Secretary; ack 1943-12-30 NY County before Francis M. Pitt
(Nassau notary, certs filed in five counties, commission expires
1945-03-30); PLUS county-clerk authentication No. 38170 (Archibald R.
Watson, 1944-02-03) certifying the notary himself.

## R14-1 — THE RELEASE LEAKS THE PRICE (cross-document price witness)

The release recites the UNDERLYING SALE's full consideration structure:
$67,500, split $32,500 cash + $35,000 purchase-money bond and mortgage.
The deed to Roseville (a separate instrument) almost certainly recites
$1 — but ITS price is sitting HERE, in the lienholder's paperwork,
because the trustee needed the sale facts to justify the release. Rule:
a release/consent instrument is a price-witness CLAIM for its sibling
conveyance; extraction must bank the recital with anchors so resolution
can attach it to the deed's event. The $10-recital wall has a
documented crack: follow the lien paperwork.

## R14-2 — DISCLAIMED RECITALS (claims carry an author)

"The recitals herein are made by Brooklyn Edison Company, Inc., and
City Bank Farmers Trust Company assumes no responsibility therefor."
The instrument itself declares WHO asserts its facts — the signer
disclaims them. RULING (decided in-run, P-3 satisfied): NO new column —
the disclaimer is itself a claim anchored to its line; the claims tier
already records verbatim text with anchors, so authorship is
recoverable at resolution time. But the lesson stands: a recital's
author is not always the instrument's maker, and where stated it must
be captured as a claim.

## R14-3 — BLANKET + AFTER-ACQUIRED LIEN (chronology inverts)

The 1936 indenture lien attaches to property "then or THEREAFTER owned
or acquired" — a parcel can fall under a mortgage recorded before the
owner even bought it, and leave it parcel-by-parcel via numbered
partial releases (the indenture tracks its collateral as its own parcel
list — "Parcel No. 29"). Resolution consequences: (1) lien coverage is
not derivable from recording order; (2) partial releases must subtract
SCOPE from the blanket row, never close it ("all the rest ... shall
remain subject"); (3) one instrument can live in two counties' libers
at once — the Richmond cite is not THE mortgage, it is one custodian's
copy of it.

## R14-4 — A RELEASE FILED AS "DEED" (the catch-all hides lien surgery)

rd doc_type: DEED. The instrument's operative words are quitclaim-form
("grant, remise, release, quitclaim and set over"), and the register
filed it as a conveyance — but its function is release-of-lien, and
title does not move (Edison already owned; the trustee held only the
security interest). A chain-walker trusting rd types would insert a
phantom conveyance from a bank to Edison. G-008 extended into the
pre-war era: the type code is a shelf, the document is the function.

## CONFIRMATIONS

- Key 5071670000 = block 7167 lot 0000 — the BLOCK-SCOPE key on a
  metes-only multi-parcel instrument, agreeing with the document's own
  "Section 5 in Block 7167" endnote.
- Zero party fields in rd (all keys printed) — 1944 like 1912: the
  parties exist only in the document; amount $0.00 against $67,500 of
  recited consideration (amount-blind index, R13-4 family).
- Book 865 / page 97 verified by internal page numerals 98-102 on
  pp.2-6 (start = 97, arithmetic not trust).
- instrument "2997" ≠ the face's "(No. 19147 FEE $7.00)" — two more
  members of the number-namespace family on one document; verified by
  liber/page + date, never by number-match.
- Provenance depth 3: signature → notary (five-county certs) →
  county-clerk authentication of the notary. Corporate-trust execution
  adds a layer below the ack.
- Source transcription defect: Crocheron deed cite typed "liber 4620"
  of deeds p.327 (1916 libers ran ~459-460) — banked as a defect claim,
  not repaired (never repair a number).
- Chain citations for future walks: 1936 + 1938 indentures (dual-county
  libers), the expected Roseville deed, the expected $35,000
  purchase-money mortgage (Edison as LENDER — a role inversion for the
  reach ladder), 1916 assembly deeds (Winsor 459/322, Winants estate
  459/326, Crocheron [459?]/327), water grants 469/294 + 478/490, land
  grants Timalot (Patents 54/66) and Winant (Patents 44/150).

# RANDOM-DOCUMENT RUN 15 — RC_1023 · RELEASE OF PART OF MORTGAGED PREMISES · 1975

5 pages, printed N.Y.B.T.U. Form 8034 with typed fills (Liber 2113
pp.358-362; p.359 is the form's blank verso — a legitimately empty
liber page). Made 1975-02-13, ack 1975-02-19 (notary Steven P. Howard,
Richmond), recorded 1975-02-28 (Augustine R. Casey, County Clerk;
Chicago Title; return to Holzka, Donahue & Kuhn, P.C., 358 St. Marks
Place). NORTHFIELD SAVINGS BANK (221 Richmond Avenue; Paul E. Proske,
President, resides 246 Douglas Road; Marion Piper, Secretary) releases
to LBS CONSTRUCTION COMPANY, INC. (19 Laredo Avenue) for $18,750.00 a
~200 x 65 ft parcel (Leverett/Elverton/Doane corner, block 5442) out of
the $350,000 mortgage of 1974-08-16 (liber 2073 mtges p.326), "the
residue of the mortgaged lands" remaining as security. Released bundle
includes appurtenant ingress/egress easement over Elverton and Doane
Avenues to Leverett Avenue, "a legally opened city street" — the other
two are not.

## R15-1 — THE PRICED PARTIAL RELEASE (sales velocity before DOB existed)

Run 14's release was $1 ceremonial; this one is $18,750 REAL — the
construction-loan mechanic: builder mortgages the tract, builds, sells,
and the bank releases lot-by-lot FOR MONEY as houses close. The cadence
of REL rows against one mortgage is the project's SALES VELOCITY, and
each release price is a paydown-scale signal (~5.4% of face here).
⚠ Signal, not accounting: the release price is what the bank charged to
release, not necessarily the principal reduction — remaining-debt still
needs statements (G-022); the CADENCE is the derivation product. A
1975 subdivision's absorption rate is fully readable from the deeds
liber alone.

## R15-2 — TYPE-CODE VOCABULARY HAS A TIMELINE (REL in 1975, DEED in 1944)

The same function (partial release of mortgage lien) is shelved as
"DEED" in 1944 (R14-4) and correctly as "REL" in 1975. The register's
type vocabulary IMPROVES over time — so the reliability of the
type→function shortcut is itself era-dependent, and any accuracy
measured on modern rows says nothing about pre-war rows. The function
always comes from the document; the code's trustworthiness has a
timeline that extraction should eventually measure per-era, not assume.

## R15-3 — INDEX ROLES NAME THE UNDERLYING RELATIONSHIP, NOT THE INSTRUMENT'S DIRECTION

The REL row's parties: Mortgagor LBS, Mortgagee Northfield — but the
RELEASE runs Northfield → LBS. The index's role vocabulary stays
anchored to the MORTGAGE relationship even on instruments that act
against it. Consistent with the orientation law (rows keep
obligor→holder); a direction-from-roles heuristic would reverse every
release, satisfaction, and assignment-back. Direction comes from the
instrument's operative words; roles identify the relationship acted on.

## CONFIRMATIONS

- Block-scope key again: 5054420000 (block 5442 lot 0000), cover's lot
  field blank — multi-lot tract released mid-subdivision, no single lot
  to key.
- instrument "11239" vs face received-stamp "No. 19538" — the
  number-namespace family; verified by liber/page + date.
- amount $0.00 with $18,750 stated consideration AND a $350,000 cited
  mortgage — amount-blind index (R13-4 family), third consecutive era.
- Recorded in the DEEDS series ("Deeds, and Indexed under Block Number
  5442" stamp) though it acts on a mortgage — the two-shelf lesson
  (R11-1) from the deeds side; the mortgage lives at liber 2073 mtges,
  the release at liber 2113 deeds. A cite without its SERIES is
  ambiguous.
- Unused blank ack forms + subscribing-witness form on the printed
  instrument — form-anatomy noise, correctly yielding no events.
- Chain expectations banked: the 1974 $350,000 construction mortgage
  (2073/326), sibling releases against it (cadence!), and LBS's sale
  deeds out of block 5442 that these releases enabled.

# RANDOM-DOCUMENT RUN 16 — FT_2750004791475 · MEMORANDUM OF LEASE · 1995 (BRONX)

5 pages, film (REEL 1331 PG 1560-1564) — FIRST OCCUPANCY INSTRUMENT in
sixteen runs, and the first non-Richmond draw (Bronx block 4287 lot 18,
2100 White Plains Road — the corpus's FT_ film spans boroughs). U.S.
Postal Service Facilities Department forms: GEORGE TSILOGIANNIS (c/o
Galaxy Management, 1757 Merrick Avenue, Merrick; return address 111
Fifth Avenue) leases ~1,232 SF of single-story storefront (51'1"x23'3"
+ 10'8"x5'0", NE corner White Plains Road & Maran Place) to the UNITED
STATES POSTAL SERVICE ("Parkway Finance Station"), executed as of
1995-03-21, term 1995-06-01 to 2000-05-31, ONE 5-year renewal at USPS's
sole option on 60 days' notice; USPS may terminate on 60 days' notice
only during the renewal term. Attached: TWO Mortgagee's Agreements —
ATLANTIC BANK OF NEW YORK (Linda M. Kolachny, VP; holder of the FIRST
mortgage $841,930.80 AND a THIRD mortgage $6,371,572.80) sworn
1995-02-06, and OLYMPIAN BANK (512 86th Street, Brooklyn; rank
UNSTATED; $396,091.51) sworn 1995-02-13 — each consenting to the lease
and agreeing any foreclosure sale is made SUBJECT TO the lease.
Contracting officer Henry Burmeister acknowledged in HOBOKEN, NEW
JERSEY (Hudson County). Recorded Bronx 1995-07-24 with transfer-tax
stamp block (control 007160; slid 015210 stamped and indexed).

## R16-1 — THE MEMORANDUM SHAPE: RENT IS OMITTED BY DESIGN

A memorandum of lease is a NOTICE instrument: parties, premises, term,
options — and NO RENT. The money lives in the unrecorded lease. This is
OCCUPANCY's twin of the $10 deed recital, but structural: no stamp or
sibling will supply it; quantity resolves `unavailable` (the record
cannot hold it), while TERM is fully witnessed and is the product here
(occupancy horizon + option ladder). Extraction must not hold the row
open waiting for a rent that is not coming.

## R16-2 — G-037 EXERCISED, AND ITS FIRST CONDITIONAL (rows 2 and 3)

The mortgagee agreements are TITLE·modifies per G-037: from = the bank
yielding rank, to = the USPS leasehold advanced (lease survives
foreclosure); liens untouched. Atlantic's form carries a TYPED INSERT:
"Provided that there are no defaults (after notice, if required, and
expiration of any applicable cure period) by the U.S. Postal Service" —
a NEGOTIATED CONDITION on rank-yielding, absent from Olympian's
otherwise-identical government form. Same form, different bargains:
extraction reads each copy, never assumes form-text is constant.

## R16-3 — A LEASE MEMO IS A CAPITAL INTELLIGENCE SOURCE (and the index hides it)

The recorded lease package discloses the parcel's full debt stack WITH
BALANCES: 1st $841,930.80 (Atlantic), $396,091.51 (Olympian, rank
unstated), 3rd $6,371,572.80 (Atlantic — larger than the first;
⚠ HYPOTHESIS: cross-collateralized/blanket). The odd cents mark these
as OUTSTANDING BALANCES at consent time, not faces (L-2 qty_role) — a
mid-life debt snapshot no mortgage instrument provides. And the index
shows NONE of it: parties = lessor + lessee only; the banks are
invisible (attached instruments' parties unindexed), amount $0.00. The
richest CAPITAL fact in the package is index-dark.

## CONFIRMATIONS

- rd: LEASE / "MEMORANDUM/LEASE" remarks ✓ · 5 pages ✓ · reel 1331-1560
  ✓ · recorded 7/24/1995 = stamp ✓ · borough BRONX, BBL 2042870018
  ENTIRE LOT ("PRE-ACRIS" use flag) ✓ · slid 015210 = the ink stamp ✓.
- Index party defect: "UNITED STATES POSTALSERVICE" (concatenation, no
  space) — transcription-defect family; role fields empty on this film
  index era.
- keyed_by/key empty — FT film rides ACRIS parcels, org backfill
  pending (run 11 pattern).
- Out-of-state acknowledgment (New Jersey notary John P. D'Ercole, for
  the federal contracting officer) — provenance may cross state lines
  on government instruments.
- Government tenant (USPS) — occupancy signal class; renewal/termination
  asymmetry (options run one way, to the tenant).
- OCCUPANCY joins the exercised set: 6 of 11 functions now seen live
  (TITLE, ENCUMBRANCE, CAPITAL, COST, OCCUPANCY, IDENTITY-via-maps).

# RANDOM-DOCUMENT RUN 17 — RC_2825423 · DEED (TRUST TRANSFER) · 2026

7 pages, born-digital modern Richmond — THE FRESHNESS FRONTIER: recorded
2026-08-13, randomly drawn from the store 2026-08-22, already acquired
and parcel-keyed (ingest-to-bootcamp latency ≤9 days; clerk pipeline:
reviewed "HC 8-12-26", recorded 8-13 11:08:57). Bargain & Sale deed
with covenant against grantor's acts, made 2026-06-16 (58-day
exec→record lag): LISA ARGENZIANO → JAMES ARGENZIANO as Trustee of THE
LISA ARGENZIANO IRREVOCABLE TRUST, both of 155 Bay Street 5H — Unit 5H,
The Pointe Condominium (block 1 lot 2044 + 1.187% common interest;
declaration recorded 2012-02-16 as Land Doc 414704, Condo Plan 147).
TEN dollars; RETT $0.00 / RPT $0.00 (code 281 lines); RP-5217 Full Sale
Price $0, class R4, assessed $40,173. Prior deed cited as LAND DOC
#664055 (Gerald P. Cucchiara, Jr., 2017). Notary = submitting attorney
= return-to: Matthew Lenza. LAND DOC# 1016553.

## R17-1 — THE MODERN CHAIN LIVES IN THE LAND-DOC NAMESPACE

The deed cites its own history by LAND DOC number (#664055 prior deed;
#414704 condo declaration) — no libers, no reels. Modern Richmond
chain-walking is a land-doc-number graph, and rd's instrument field
holds exactly that number (1016553 here; R13-3 settled which of the
cover's numbers it is). The citation namespaces by era: Patents → liber
(two series) → reel-page → land doc. One chain, four addressing schemes.

## R17-2 — THE $0 THAT VERIFIES (the stamps-rule refined, not broken)

"$0 never verifies" is a rule about SALES. Here zero is affirmatively
witnessed three ways — RETT $0 + RPT $0 (coded lines) + RP-5217 "Full
Sale Price: 0" — and the context (grantor → her own irrevocable trust;
⚠ INFERRED: trustee shares surname + address, relationship UNSTATED in
the document) says NON-SALE: a beneficial transfer.
The event is real TITLE·transfers; the price is TRUE ZERO, not hidden.
Flag NOMINAL (excluded from comps, per the nominal-deed discipline);
the trust unmask is the product: legal owner becomes the trust; the
beneficiaries are NOT named in the deed (the trust agreement, unrecorded,
holds them). RP-5217 condition boxes checked "J None" — not
even "sale between relatives" — the CHECKBOX layer under-reports;
context and deed text outrank the form's self-description.

## R17-3 — TRUST DUAL-ENTRY (one grantee, two index rows)

Cover and index both render the grantee twice: "The Lisa Argenziano
Irrevocable Trust" (company row) + "James Argenziano" (name row) — one
legal grantee (trustee-of-trust) as two party rows. The R7 dual-entry
family's trust variant: identity resolution must merge trustee+trust
rows into one titleholder, or every trust deed double-counts its
grantee. (The index faithfully mirrors the cover here — the defect is
in the CONVENTION, not the transcription.)

## CONFIRMATIONS

- rd: key 5000012044 (condo UNIT lot — the spine's condo-billing lesson
  territory) ✓ · instrument = LAND DOC 1016553 ✓ · Deed · 8/13/2026 ✓ ·
  parties 3 rows ✓ · amount $0.00 (TRUE zero, R17-2).
- Assessed value $40,173 + class R4 banked as VALUE·observes claims
  (RP-5217 is a VALUE source riding inside deed packages).
- Attorney-notary-submitter one person (Matthew Lenza) — modern small-
  transfer anatomy; notary reg 02LE6117255, expires 2028-10-25.
- Blank ack variants + 40-row attachment signature sheet = form
  anatomy, zero events (G-form-noise family).
- Open chain question (NOT asserted): the 2017 cite says "parties of
  the first part" — whether Lisa took title alone in #664055 is
  answerable only there; if she had a co-owner, this deed moved only
  her interest. Banked as chain expectation.
- 58-day execution→recording lag measured — the freshness product's
  caveat: recording date ≠ event date; both are carried.

# RANDOM-DOCUMENT RUN 18 — BK_6620005200246 · DEED · 1966 (BRONX REC BOOK)

3 pages, film — a NEW ID NAMESPACE decoded: BK_ = Bronx City Register
"REC." book series; the id parses year 66 + borough 2 + book 0052 +
page 00246, matching the frame stamps (REC. 52 PAGE 246-247) and rd's
reel_page "52-246". Bargain & Sale deed dated 1966-04-16, ack same day
(notary S. Paul Squitieri, Bronx), recorded 1966-04-18 9:14 AM (G.
Michael Morris, Acting City Register; fee $6.00; "NOT SUBJECT TO MTGE
TAX"; RETURN RPT # NONE): JOHN T. RIGNEY → MARGARET M. RIGNEY, both of
1529 Hone Avenue, Bronx — an interspousal transfer, $10 recital, no
consideration (the 1966 twin of run 17's trust transfer: same
family-rearrangement shape, sixty years apart). Section 15 / block 4067
/ lot 28. Premises described from a PRE-ANNEXATION filed map ("Map of
Property ... situated in the Town of Westchester," Cornelius J. L.
Lynch C.E., filed with the REGISTER OF WESTCHESTER COUNTY — the east
Bronx was Westchester until annexation), party-wall metes on Lincoln
Street. Prior: Ezekial Varian deed 1947-02-11, Bronx Liber 1517 p.110
"of Conveyances."

## R18-1 — BK_ = THE BRONX REC-BOOK SERIES (id namespaces are per-custodian-era)

Four id families now decoded in the store: RC_ (Richmond, internal id),
FT_ (ACRIS film reel), BK_ (Bronx REC book/page, self-describing id),
16-digit (born-digital ACRIS). The BK_ id is a CITE, not an opaque
id — book and page are recoverable from the id itself, so a BK_ doc can
be verified against its frame stamps with zero lookups. Directory
sharding (BK_6\6200) is id-prefix, not year — the By Document tree has
two filing conventions.

## R18-2 — THE BACKER RECOVERS THE CUT FRAME (film defect + built-in redundancy)

Page 1's left column is cut off by the film edge — grantor, premises
opening, and half the metes are unreadable on the operative page. But
liber-era instruments carry their own abstract: the BACKER (endorsement
panel) restates parties, date, instrument type, county, address, and
block/lot, and the ack restates the grantor. Every operative fact
survived via redundancy INSIDE the instrument. Extraction rule: a
damaged operative page is not a dead document — read the backer and
ack as the recovery channel, then mark which channel each fact came
from.

## R18-3 — doc_date COPIED FROM RECORDING DATE (film index date family)

rd doc_date = recorded = 4/18/1966, but the instrument is DATED
4/16/1966 (made and acknowledged). The film-era index did not carry a
true document date — it cloned the recording date. Family member to
"79% of FT_ have NO document_date": when film doc_date EQUALS recorded
exactly, treat it as unwitnessed and let the instrument supply the true
date. Two-day gap here; run 17 showed 58 days — the gap is real data.

## CONFIRMATIONS

- Key 2040670028 ✓ — and it CONFIRMED the held-at-moderate handwritten
  "BLOCK 4067" reading (rd as verifier, R4-4 discipline working as
  designed).
- Index party defects, twice in one row: "MARGARET MRIGNEY"
  (concatenation — initial glued to surname) and name-order
  inconsistency (party 1 surname-first, party 2 given-first) — the
  dual-entry/casing family keeps growing; identity resolution must
  normalize per-party, not per-row.
- Duplicate film frame: pages 2 and 3 are the SAME liber page (REC 52
  PAGE 247) — frame count ≠ page count; dedupe before any per-page
  claim, or backers double-count.
- remarks "D BOOK/PAGES: 182/88" matches NOTHING on the instrument
  (prior deed is Liber 1517/110) — unresolved index cross-reference,
  banked as a claim with unknown referent, not silently dropped.
- Cross-county filed map: a WESTCHESTER-registry map governs BRONX
  parcels (pre-annexation) — the filed-map namespace family's
  cross-county member; map cites must carry their REGISTRY, not just
  their number.
- True-zero non-sale, 1966 edition: interspousal, $10, no tax — the
  NOMINAL flag's ancestor; family transfers look identical across six
  decades and two boroughs.

# RANDOM-DOCUMENT RUN 19 — RC_1024032 · WARRANTY DEED · 1951

4 pages, typed liber transcription (Liber 1168 pp.497-500), Statutory
Form A (Title Guarantee and Trust Co). Made 1951-08-24, ack same day
(notary S. Robert Molinari, Richmond, term expires 1952-03-30),
recorded 1951-08-28 10:24 AM: EUGENE REYNOLDS (180 Dongan Street, West
Brighton) → GEORGE J. LOOS and MARY E. LOOS, his wife (24 Sterling
Ave., New Dorp) — lots 56 and 57 on "Map of New Dorp Park" (H. S.
Thomson and Son, filed 1925-05-19 as Map No. 1484), block 939-A on the
map / indexed under 939-L / rd key block 939. $10 recital + FEDERAL
DOCUMENTARY STAMP. WARRANTY deed: five full covenants (seizin, quiet
enjoyment, free of encumbrances, further assurance, warranty) + Lien
Law §13 — the covenant LADDER distinguishes it from B&S. Subject-to
recites the JULY 25, 1916 Board of Estimate resolutions — the original
NYC Zoning Resolution appearing as a deed recital. Prior: Hyatt Holding
Corporation deed 1950-08-31, liber 1130 p.426.

## R19-1 — CROP-AND-LOOK CONVERTS UNREADABLE → READ (the stamp at 400dpi)

At 120dpi the documentary stamp was an inky blur — "present,
denomination unread." One 400dpi crop later: UNITED STATES INTERNAL
REVENUE · DOCUMENTARY · ONE DOLLAR. The stamps rule now runs in the
film era: $1.00 of tax at the 1951 schedule (⚠ era context: 55¢ per
$500 or fraction) implies a consideration band around $500-$1,000 —
though $1.00 is not an integer multiple of 55¢, so either a companion
stamp sits unseen elsewhere on the original or usage was rounded;
banked as a BAND with the friction stated, never forced to divide
(never repair a number). Two New Dorp lots for about a thousand 1951
dollars. Extraction pipeline consequence: stamp regions get a
high-resolution pass BEFORE any 'unread' verdict — same law as the
VLM crop discipline, now proven on revenue stamps.

## R19-2 — THE BLOCK-SUFFIX NAMESPACE (939-A vs 939-L vs 939)

Three block designations for one parcel IN ONE DOCUMENT: the filed
map's own block ("BLOCK NUMBER 939 A"), the county index's land-map
block ("indexed under Block Number 939 L", both this deed's stamp and
the prior deed's recital), and rd's modern key (block 939, suffix
gone). Old Richmond land-map blocks carried LETTER SUFFIXES that the
modern renumbering collapsed. Namespace family member: a mid-century
block cite without its suffix-era context can point at the wrong
sub-block; resolution across the renumbering seam must map
suffixed→plain, and rd's key is the rosetta row.

## R19-3 — THE PARTY-COVERAGE BOUNDARY: BETWEEN 1944 AND 1951

1912 row: zero parties. 1944 row: zero parties. 1951 row: ALL THREE
parties, surname-first, correctly split. The Richmond index's party
coverage begins somewhere in 1945-1951; before the boundary, party
reach is extraction-only (R12/R14 lesson), after it the index carries
names. Worth a cheap measured sweep someday (count party-bearing rows
per year); until then the boundary is bracketed by bootcamp evidence.

## CONFIRMATIONS

- rd: liber/page/date/type exact ✓ · block-scope key 5009390000 (map
  lots 56/57 have no tax-lot identity) ✓ · amount $0.00 while the stamp
  witnesses a real consideration — amount-blind index, fourth era.
- instrument "1800" — internal number absent from the face; namespace
  family (verify by liber/page).
- The 1916 Zoning Resolution as subject-to recital — ENVELOPE's
  regulatory regime surfacing inside a TITLE instrument; a recital
  (observes), not a creation; the deed-side echo of what the live ZR
  feed carries today.
- Husband-and-wife grantees ("his wife" = tenancy by the entirety
  implied, not stated — held as legal default, not asserted as text).
- Warranty vs B&S distinguished BY THE COVENANT LADDER (five covenants
  present) — instrument self-identifies beyond its title line.
- Chain: Hyatt Holding Corp (1950, 1130/426) — corporate subdivider one
  step behind a homeowner sale; New Dorp Park map 1484 (1925) joins the
  filed-map registry list.

# RANDOM-DOCUMENT RUN 20 — FT_2860007560086 · PURCHASE MONEY MORTGAGE · 2001 (BRONX)

24 pages + 1 duplicate frame (REEL 1850 PG 450-473), film at the ACRIS
seam — the first full COMMERCIAL LOAN PACKAGE drawn. 2001-02-16:
CARPENTER REALTY LLC (2578 East Tremont Avenue) borrows $975,000
PURCHASE MONEY from ASTORIA FEDERAL SAVINGS AND LOAN ASSOCIATION
against 4305 Carpenter Avenue (Bronx block 5034 lot 28; Map of
Jacksonville No. 783; metes note the corner of "Catherine Street (now
called Carpenter Avenue)" — a street rename inside the description).
Recorded 2001-03-15. Signed VITO SACCHETTI, Managing Member — seven
times; ack Nassau County (notary Sheldon Goldklang). Terms assembled
across NINE parts: Form 3033 substrate + ARM rider (7.625% initial,
5-yr Treasury + 2.50%, FLOOR at 7.625%, first change 2006-03-01) +
Balloon rider (DUE IN FULL 2016-03-01; payments computed as if maturity
were 2028-03-01) + Prepayment rider ($7,800/yr free, 5-4-3-2-1% ladder
RESETTING at years 5/10/15 with 90-day windows) + EXCULPATORY rider
(non-recourse at origination; carve-outs: environmental guaranty +
fraud) + ASSIGNMENT OF RENTS rider (absolute, and citing a "more formal
and detailed" A of L&R executed contemporaneously) + Financial
Statements rider (typed insert: personal financials of VITO SACCHETTI)
+ Environmental rider (CERCLA/RCRA reps) + Lender's rider (DELETES
reinstatement §19/§22, +5% default rate, "No Obligation To Occupy",
forfeiture, FNMA-void clause).

## R20-1 — THE RIDER LAYER IS THE OPERATIVE LAYER

The printed Fannie/Freddie uniform form is a SUBSTRATE; the deal lives
in the riders, which add, strike, and even DELETE printed sections
(§19/§22 gone; §25 checkbox declares "does not cover 1-6 family";
printed ARM caps struck and a floor typed in). A reader that stops at
the form reports a consumer home loan; the riders make it a
non-recourse commercial balloon with a rate floor. Extraction rule:
riders are read WITH the form as one instrument, and rider text
OUTRANKS printed text wherever they touch (the instrument's own §26
says so: "this Rider ... will control").

## R20-2 — THE TAX CLASSIFIES THE BUILDING (four witnesses agree)

MTGE TAX $26,812.50 = 2.75% x $975,000 EXACTLY (the over-$500k
commercial/multifamily rate). Agreeing: the "premises are NOT improved
by a one-to-six family dwelling" stamp, the circled "over 6" dwelling
type, and the §25 checkbox. The mortgage RATE SCHEDULE itself is an
asset-class witness: 2.75% says multifamily/commercial as loudly as
any use code — and it arrived self-checked to the penny (P-4).

## R20-3 — AMOUNT-BLINDNESS IS DOC-TYPE-DEPENDENT (first non-zero in 20 runs)

rd amount: $975,000.00 ✓ — after nineteen runs of $0.00. The index
carries amounts FOR MORTGAGES and not for deeds/leases/releases; the
blindness is per-type, not per-era. But the debt PRODUCT is still
index-dark: balloon date, floor, prepay ladder, non-recourse — all
rider-only. The index knows the loan's SIZE; only extraction knows its
SHAPE and its 2016 maturity.

## R20-4 — THE SPE UNMASKED BY ITS OWN RIDERS

Carpenter Realty LLC discloses its human seven signatures deep: VITO
SACCHETTI, Managing Member, and the Financial Statements rider's typed
insert binds HIS personal financials to the loan — a quasi-guarantor
signal. The borrower-SPE join (the throughline's hinge) is served by
the loan package itself: riders name the person the deed never will.

## CONFIRMATIONS

- rd: MORTGAGE ✓ 3/15/2001 ✓ BRONX ✓ reel 1850-450 ✓ parties 2/2 ✓ BBL
  2050340028 ✓ · pages "25" = FRAME count (duplicate frames 5-6
  counted; cover's own page count says 24) · "ENTIRE LOT" vs cover's
  P/O partial marker — held as ambiguity, Schedule A metes govern.
- Loan-number trio on one instrument (3-0000064646 /
  09999-0000064646 / servicing 9732458) — the lender's OWN numbers are
  a namespace family too; none is the recording identity.
- Balloon + amortization shadow: payments sized on a 2028 schedule,
  due 2016 — remaining-balance-at-balloon is computable from the two.
- Sibling expectations banked: same-day purchase DEED (PMM recital),
  the "more formal" Assignment of Leases and Rents, the Hazardous
  Material Guaranty (named in the exculpatory carve-out) — three
  instruments to expect within reel range.
- Street rename captured (Catherine → Carpenter Avenue) — description
  namespaces drift WITHIN one parcel's papers; IDENTITY claims carry
  both names.

# RANDOM-DOCUMENT RUN 21 — RC_1052597 · ASSIGNMENT OF LEASES AND RENTS · 2012

21 pages, born-digital modern Richmond (LAND DOC# 435472, fee code
25-ASSIGN,AGREE,REL). Made 2012-06-21, recorded 2012-07-23: 135 LAKE
AVENUE REALTY LLC (27 Downing Street, Manhattan; ANDREW B. LEIDER,
Member and Manager) assigns to GREATER HUDSON BANK, N.A. (Middletown)
the lessor's interest in all leases and rents of the industrial
property at 175 Lake Avenue (block 1161 lots 1 + 12), securing a
$3,000,000 Consolidated Restated Mortgage Note. Absolute assignment
with revocable license back; attorney-in-fact; RPL §291-f; conflict →
mortgage prevails; terminates on satisfaction. Ack Rockland County
(notary Thomas Scuderi = record-and-return attorney Thomas M. Scuderi,
Esq., Connell Foley LLP — the notary-is-counsel pattern, third
sighting). Run 20 banked "expect the formal AL&R as its own
instrument"; the very next draw IS one — the instrument class closed
itself.

## R21-1 — SCHEDULE B IS A DEBT BIOGRAPHY (nine instruments in one recital)

The chain, verbatim with doc numbers: (a) MM LAKE AVENUE LLC →
WASHINGTON MUTUAL $2,212,500 (2008-03-26, #2008-248012) → assigned by
JP MORGAN CHASE "as successor by merger to Washington Mutual" AND
AGAIN as "JP Morgan Chase, a national association" (#2010-349745 +
#2010-349746 — the SAME assignment recorded twice in two grantor
styles: post-collapse CURATIVE DOUBLING) → ISLAND PROPERTIES NYC LLC →
HRC FUND V. REIT LLC (again doubled: #2010-349747 + #2010-349748) +
Spreader (#2010-349742); (b) gap $605,813.25 (#2010-349741), CEMA to
$2,800,000 (#2010-349744), assigned → W FINANCIAL FUND, L.P.
(#2011-396663); (c) gap $500,000 with ANDREW LEIDER personally
(#2011-396664), CEMA to $3,300,000 (#2011-396665); (d) gap $200,000
(#2012-422566); four assigned → GREATER HUDSON BANK with OUTSTANDING
BALANCE $2,800,000 as of 2012-06-20; (e) new $200,000; five
consolidated to $3,000,000 via Mortgage ASSUMPTION Consolidation
Extension Modification and Security Agreement — with the last three
instruments "intended to be recorded simultaneously herewith".
2,800,000 + 200,000 = 3,000,000 ✓. The story: WaMu dies, JPM inherits,
sells the note to Island Properties NYC LLC (⚠ INFERRED role: a
note-purchaser by pattern — the record shows only the assignments, not
its business), borrower entity changes (MM Lake → 135 Lake,
assumption), then W Financial (⚠ same caveat), then bank refi. ONE
recital replaces nine
separate document walks — recited chains are the cheapest resolution
shortcut in the corpus, and the §255 affidavit repeats it ALL a second
time with per-instrument tax paid handwritten in ($61,950.06 checks as
2.8% of $2,212,500).

## R21-2 — DONUT PARCELS (the collateral is a shape, not a lot list)

Schedule A: Parcel A = ALL of lot 1 EXCEPTING three described parcels
("For Info Only: commonly known as" lots 10, 15, 20); Parcel B = lot
12 excepting one more. Plus: DUAL BEARINGS per course ("south 76°28'06"
east (deed) (south 76°41'06" east U.S. Std.)"), a deed-vs-tax-map
distance (117.38 deed vs 122.38 tax map), and a boundary on "Staten
Island Rapid Transit's Land". IDENTITY lesson: modern collateral
descriptions can be lot-minus-lots; the "commonly known as" labels are
informational, the metes are operative; and one course can carry two
bearing conventions and two distances, each tagged to its authority.

## R21-3 — DUAL-ENTRY BY CASING, MEASURED ON THE ROW (4 rows / 2 parties)

rd parties: ASSIGNEE/ASSIGNOR (uppercase) + Assignor/Assignee
(mixed-case) — the same two parties twice. The R7 dual-entry casing
family caught red-handed in a reconciliation: party COUNTING from
index rows must dedupe case-insensitively or every modern assignment
doubles its parties.

## CONFIRMATIONS

- rd: key BOTH lots (5011610001;5011610012) ✓ · instrument = LAND DOC
  435472 ✓ · A/LEASE ✓ · 7/23/2012 ✓ · amount $0.00 for a $3,000,000
  security instrument — R20-3 holds (amounts are for MORTGAGE-type
  rows only).
- Modern Richmond citation namespace unified: instruments cite each
  other as "#YYYY-SERIAL" (#2012-422566) while rd stores the bare
  serial (435472) — one namespace, two renderings.
- Balance snapshot: $2,800,000 outstanding at assignment (R16-3's
  lease-package balance disclosure, Richmond edition) — plus reps that
  rents are not prepaid beyond one month and leases unmodified.
- Leader unmasked TWICE: signs as Member and Manager AND appears as
  personal co-mortgagor on chain items (c)+(d) — the SPE's human is in
  the debt, not just behind it.
- Sibling expectations banked: Assignment of Mortgage (W Financial →
  GHB), the $200,000 gap mortgage, and the Assumption-CEMA — all
  "simultaneously herewith", land doc serials likely adjacent to
  435472.

# RANDOM-DOCUMENT RUN 22 — RC_1022240 · B&S DEED, SUBJECT-TO · 1958

2 pages, high-contrast PHOTOSTAT (448KB for 2 pages — density is the
artifact's own warning). Made September 1958, ack 9/04(?), recorded
1958-09-11 10:39 AM, Liber 1433 p.435: HOWARD C. FOGH and MARION E.
FOGH, his wife → MAX J. REIMAN — ALL THREE at 188 Slosson Avenue (an
intra-household transfer; relationship unstated, not asserted). A
20-foot PARTY-WALL ROWHOUSE on Chandler Avenue (party wall on BOTH
courses), described with USC&GS coordinates stamped on the street
intersection itself (S 15904.075, W 22785.048 — run 14's coordinate
system in residential use). $10 recital + TWO federal documentary
stamps. SUBJECT TO a declaration of easement (1942-05-18, rec
1942-05-29, Liber 847 p.513) AND "a First Mortgage on said premises
owned and held by THE BOWERY SAVINGS BANK dated the 31st day of May,
1946." Notary/witness Eugene V. P. Ferretti (12 Bay St). Marion's typed
name struck and corrected by hand at signature.

## R22-1 — SUBJECT-TO: TITLE MOVES, THE DEBT STAYS

The rowhouse sold WITHOUT satisfying the 1946 Bowery Savings mortgage —
conveyed "subject to" it (no assumption stated). Chain consequences:
(1) the lien crosses the title transfer intact — resolution must carry
CAPITAL rows across TITLE events, never close them at sale; (2) the
recital is a LIVE-DEBT WITNESS: it proves the 1946 mortgage was still
outstanding twelve years in (1958) — deed recitals date-stamp debt
survival exactly like run 16's consent balances; (3) the buyer's
equity, not the buyer, bears the debt — a default forecloses Reiman's
house on Fogh's loan. Subject-to recitals are a debt-timeline source.

## R22-2 — UNREAD-BY-SOURCE vs UNREAD-BY-RENDER (the crop law's limit)

Two documentary stamps PRESENT; the R19-1 high-dpi crop was applied —
and the denominations are crushed to solid black by the photostat's
threshold. R19's crop cures RENDER-limited unreadability; nothing
cures information the SOURCE destroyed. The claim records the
condition ("stamps present, denominations illegible on photostat;
better copy could read") so a later, better artifact can settle it —
the same design as the VLM disagreement-distribution: unread states
carry WHY they are unread. Weak bound only: two stamps ≥ ~$1.10 tax →
consideration real, not nominal, magnitude unknown.

## CONFIRMATIONS

- Liber digit caught by the verifier: cold read leaned "1483" on the
  degraded margin stamp; rd asserts 1433 — a photostat 8/3 confusion,
  flagged and corrected at reconciliation (R4-4 doing its job; the
  miss ledger charges it).
- Block-suffix collapse, second instance: backer "Block 375 L on the
  Land Map" → rd key 5003750000 (plain 375, block-scope) — R19-2's
  suffixed→plain mapping confirmed as a PATTERN, not a one-off.
- Party coverage 1958: full (3 parties, surname-first) — consistent
  with the 1945-51 boundary bracket (R19-3).
- Same-address triangle (both grantors + grantee at 188 Slosson) with
  REAL stamps — not nominal, relationship unknown, both facts banked
  separately without a bridging story (G-026 discipline).
- amount $0.00 + instrument "1221" internal — familiar families.
- 1942 easement declaration (Liber 847/513) banked as chain cite;
  street-corner coordinates; joint "they" ack; hand-corrected
  signature name (MARION E. over struck type) — execution-layer
  corrections are part of the record.

# RANDOM-DOCUMENT RUN 23 — RC_1009281 · B&S DEED · 1968 (THE RETT GAP)

2 pages, N.Y.B.T.U. Form 8002. Made 1968-04-02, ack same day, recorded
1968-04-24 (Liber 1815 p.418 — cold read wobbled 1815/1875, rd
settled 1815; R22's digit lesson reused): ANIELLO PALMIERI and SANTA
PALMIERI, his wife (106 Blackford Avenue) → ANIELLO PALMIERI (491
Netherlands Avenue). Lots 47+48 (50x100 each) on "Map of Cannon Plot
and adjacent property, L.W. Freeman, Surveyor," filed 1892-02-01 in
MAP CASE 628 — an 1892 filed map cited by CASE number (new member of
the map-citation namespace: Map No. vs Map Case). SANTA SIGNED WITH
HER MARK (X) — second X-mark in the corpus (G-026 applied: the mark is
the fact, cause unasserted). Notary Isaac H. Beck = return-to (492
Richmond Avenue) — notary-is-counsel, fourth sighting. Section 3,
block 1101, lot blank on backer.

## R23-1 — THE SECOND NO-WITNESS WINDOW (Jan-Jul 1968)

NO stamps on a 1968 conveyance: the federal documentary stamp DIED
1967-12-31, and ⚠ (era context, hypothesis) the NYS transfer tax
began mid-1968 — leaving a months-long gap where NO price-witness
regime existed. R12-2's 1902-1914 gap has a modern sibling: price
resolves `unavailable — no witness regime` for deeds in the window.
The witness-regime TIMELINE is now three-epoch: fed stamps (to 1967) →
GAP (early 1968) → RETT (from 1968). Worth one authoritative check of
the exact RETT start date when the ZR-style live-source rule can be
applied to tax law.

## R23-2 — SAME NAME, TWO ADDRESSES, ONE DOCUMENT (identity's hard case)

Grantor Aniello (106 Blackford) vs grantee Aniello (491 Netherlands):
same man consolidating title out of the marriage, or father deeding to
son? THE DOCUMENT DOES NOT SAY, and rd renders both as byte-identical
"PALMIERI ANIELLO" rows — the index cannot separate them even
intra-document. Identity resolution law: a PERSON is not a name; the
addresses are the only distinguishing witness here and MUST ride the
party claim. Any name-keyed reach ladder merges these two (possibly
distinct) people silently — the 0.3% name-matching lesson at
single-family scale.

## CONFIRMATIONS

- Block-scope key 5011010000 (backer lot blank) · instrument "7769"
  internal · amount $0.00 · DEED ✓ 4/24/1968 ✓ parties 3/3 ✓.
- 1892 filed map STILL the operative description in 1968 (76 years on)
  — filed-map lots outlive generations; Map Case 628 joins the
  registry list.
- Recording lag 22 days (made 4/2, recorded 4/24); joint "they" ack.
- Marital-consolidation shape: (H+W) → H alone; the mirror of run 18's
  H → W. Family title rearrangements come in both directions; both are
  NOMINAL-class non-sales.

# RANDOM-DOCUMENT RUN 24 — RC_1051736 · DEED MADE 1910, RECORDED 1918

2 pages, printed Wood-Harmon form deed (Vol 396 pp.543-544) — THE SAME
SUBDIVISION AS RUN 12 (South New York, Addition Number Four, Map
995-B; same officers Leonidas Keever VP / J.H. Storer Secretary; same
printed covenant scheme; same 1915-01-01 sunset). Made 1910-03-22, ack
1910-03-29 (James N. Dunlop, Commissioner of Deeds, NY County),
RECORDED 1918-01-03 — an EIGHT-YEAR recording delay. WOOD HARMON
RICHMOND REALTY COMPANY → JOHN DEVINCENZO (of the City and State of
New York; return "For Grantee, 31 Le Roy St. N.Y.C."), lots 48+49 in
Block 408 (Decatur Avenue at Caswell Avenue, 40x100 each... two lots
40-ft combined frontage), $1 recital, min-cost covenants $2,500
one-family / $3,500 double — HIGHER than run 12's $2,000/$3,000: the
scheme's parameters were priced PER DEED, not uniform across the
subdivision.

## R24-1 — THE EIGHT-YEAR RECORDING GAP (recording date is a filing fact)

Made 1910, recorded 1918. The lag family now spans: 2 days (run 18) →
22 days (run 23) → 58 days (run 17) → EIGHT YEARS. Consequences:
(1) chronology keyed on recording dates misdates this transfer by
nearly a decade — the event date is the instrument's, the recording
date is only when the county learned of it; (2) the covenant scheme
EXPIRED (1915 sunset) between execution and recording — the deed
entered the record already carrying dead restrictions; an
extraction that stamps state-at-recording must evaluate terms against
BOTH clocks; (3) the By Document year-tree files by RECORDING date
(this 1910 event lives in the 1918 folder) — corpus-level: era
sampling by folder year samples recording eras, not event eras.

## R24-2 — TEMPLATE CORPUS CONFIRMED (same form, different fills)

Random draw hit the same Wood-Harmon printed form twice in 13 runs
(12: lots 15+16 block 4?2, Emma Walden, $2,000/$3,000; 24: lots 48+49
block 408, John Devincenzo, $2,500/$3,500). The printed text is
IDENTICAL; only the fills differ. At-scale extraction consequence: the
subdivision's hundreds of deeds are one TEMPLATE plus per-deed fills —
dedupe the boilerplate, diff the blanks, and the per-deed cost
collapses; the fills that vary (min-cost!) are exactly the data. Also
strengthens R12-3: rd keys these plan lots as tax lots 48/49 in block
408 — second same-numbered adoption in this subdivision.

## CONFIRMATIONS

- rd: key 5004080048;5004080049 ✓ book 396/page 543 ✓ recorded
  1/3/1918 ✓ · ZERO party fields (pre-war boundary holds) · amount
  $0.00 · instrument blank.
- Vol 396 spans runs 12 (p.339, rec. 1912) and 24 (p.543, rec. 1918) —
  a liber is a shelf that fills across YEARS; volume number alone does
  not date a document.
- No stamps: the instrument is a 1910 conveyance (R12-2's no-witness
  era) — the 1918 recording did not retro-stamp it; price
  unavailable-by-era, second confirmed member.
- Printed-form strikethroughs ("or intended to be filed" struck — the
  map WAS by then filed; the assessments-lien clause struck) — the
  form predates the map filing; even boilerplate carries date
  evidence.
- Person-scale: Keever resides Brooklyn (consistent with run 12);
  developer's right-to-build-bigger reserved on the same named
  streets (Richmond Turnpike, Merrill Avenue, Watchogue Road, Wyona
  Avenue) — the subdivision's master plan restated verbatim.

# RANDOM-DOCUMENT RUN 25 — RC_1010265 · SATISFACTION OF MORTGAGE · 2018

3 pages, born-digital (LAND DOC# 684974, fee code 26-SATS) — the FIRST
SATISFACTION in 25 runs, drawn from the new DRAW BOARD (login's rule:
target unseen type x era cells, sampled from disk + typed by indexed
lookup; board banked at Bootcamp\Draw Board.md). Dated 2018-01-02,
recorded 2018-01-22 (exam 1/19, recorded next business day): ALPHA
LOAN SERVICING, LLC AS AGENT FOR CO-LENDERS (29 Union Avenue,
Lakehurst, NJ; MARK CALLAZZO, Managing Member) certifies that the
mortgage given by 151 HENDRICKS AVE, LLC (90 State St, Albany — a
registered-agent address; the SPE is NAMED FOR ITS PROPERTY, 151
Hendricks Avenue, block 45 lot 51) in the original principal amount of
$260,000.00, dated 2016-10-25, recorded 2016-11-03 as Land Doc 627636,
"is paid," consents to discharge, and warrants "Said Mortgage has not
been further assigned of record." Presenter Boston National Title
(NY17101558). Notary Melissa L. Silverglate, NEW JERSEY (Ocean
County) — over boilerplate reading "Notary Public of the State of New
York" and "that SHE executed" for Mark Callazzo: two form defects in
one ack, both non-events (form-noise family).

## R25-1 — THE SATISFACTION SHAPE (the debt's death certificate)

CAPITAL·releases, scope FULL — closes the CAPITAL row it names. The
release family now has three shapes: ceremonial partial ($1, run 14),
priced partial ($18,750, run 15), and full satisfaction (this). The
target is identified by ORIGINAL PRINCIPAL + dated + recorded + land
doc cite — everything resolution needs to find the row without
ambiguity. And the clause "has not been further assigned of record" is
not boilerplate courtesy: a satisfaction signed by a non-holder is
void, so the satisfier WARRANTS it still owns the note — the
chain-clear assertion is the instrument's own validity condition.

## R25-2 — THE CAPACITY CLAUSE IS INDEX-INVISIBLE (double-blind syndicate)

The document says "ALPHA LOAN SERVICING, LLC AS AGENT FOR CO-LENDERS";
the index party row says "ALPHA LOAN SERVICING, LLC" — capacity
STRIPPED. And the co-lenders are unnamed even in the document. Two
walls: the index hides that Alpha is only an agent; the instrument
hides who the money actually belonged to. A reach ladder ends at the
agent — the true lenders of a private syndicate are structurally
unreachable from the record. Banked as a reach CEILING, not a gap to
chase.

## R25-3 — ONE DOCUMENT DATES BOTH ENDPOINTS OF A LOAN

Origination recited (2016-10-25, $260,000, LD 627636) + death dated
(2018-01-02) = a ~14-month loan life readable WITHOUT opening the
mortgage: the profile of PRIVATE BRIDGE MONEY (SPE borrower named for
the address, NJ private-money agent, agent-for-co-lenders syndicate,
14-month hold). For the debt-maturity product: satisfactions both
CLOSE rows and date-stamp full lifecycles; a parcel's satisfaction
history is its refinance cadence.

## CONFIRMATIONS

- rd: key 5000450051 ✓ instrument = LAND DOC 684974 ✓ SAT ✓ 1/22/2018
  ✓ · amount $0.00 (dead debt's size invisible — amounts are for live
  MORTGAGE rows only, R20-3 holds) · dual-entry casing QUADRUPLE
  (MORTGAGOR/Mortgagor x2 — R21-3 pattern, second instance).
- Roles name the underlying mortgage relationship, not the
  instrument's direction (R15-3 third confirmation — mortgagee
  discharges TO mortgagor).
- SPE-named-for-property + registered-agent address: the entity name
  IS a parcel pointer (151 Hendricks Ave LLC ↔ 151 Hendricks Avenue) —
  a free, fallible join hint; the Albany address is the agent, not the
  principal (never geocode a registered agent).
- Exam Friday 1/19 → recorded Monday 1/22 11:24 AM — modern clerk
  pipeline latency measured again (run 17: 1 day).

# RANDOM-DOCUMENT RUN 26 — 2003040100272005 · SUBORDINATION OF MORTGAGE · 2003/2004 (MANHATTAN)

6 pages, born-digital ACRIS (CRFN 2004000210771) — G-037'S NATIVE
INSTRUMENT, drawn from the Draw Board. Blumberg form A311 dated
2003-03-18, recorded 2004-04-07 8:17:53 PM (13-month lag; the digital
cover carries the TRUE doc date — film cloned it, digital keeps it).
34-38 Mulberry Street, Manhattan block 164 lot 3 (THREE address rows,
ONE BBL — an assemblage of addresses on a single tax lot; rd parcels
mirror all three). EASTBANK, N.A. (Simon Tam, Vice President; ack NY
County, notary Anthony P. Colombini) holds the EXISTING mortgage —
2001-09-05, PARK MING REALTY, LLC and NG FOOK REALTY, INC. (two
co-borrower entities), $700,000, recorded Reel 3483 p.2033 on
2002-04-01 — and for $1 subordinates it to THE CHINESE AMERICAN BANK's
about-to-be-signed NEW mortgage of $3,800,000.

## R26-1 — RANK IS PER-PARCEL (typed ¶7 scopes the yield)

"This Subordination shall apply only the Property described in
Schedule A and shall not cover the premises known as 41 Canal Street
a/k/a 5 Ludlow Street." The existing lien BLANKETS multiple properties;
the rank-yield applies to ONE of them. G-037 refined: priority is a
property of (lien, parcel) PAIRS — one lien can be second on Mulberry
and still first on Canal. Resolution's ladder is built per-parcel, and
a subordination row must carry its parcel scope. (Bonus intel: the
exclusion accidentally discloses the borrowers' OTHER holding.)

## R26-2 — THE YIELD HAS A CEILING (quantity is the cap, not n/a)

"The maximum amount of the lien of the Existing Mortgage that is
subordinated is the amount secured by the New Mortgage and interest"
(+ enumerated advances). The rank movement is CAPPED at $3,800,000 +
interest + advances — above that exposure, the old priority resumes.
G-037's "quantity = n/a-amount" refined by the instrument itself: the
subordination row's quantity slot holds the CAP. Applies to
extensions/renewals/modifications of the New Mortgage (the yield
follows the new lien's life).

## R26-3 — THE COVER'S CROSS-REFERENCE BLOCK (namespace seam bridged for free)

The digital cover carries "CROSS REFERENCE DATA: MANHATTAN Year 2002
Reel 3483 Page 2033" — a STRUCTURED pointer from the CRFN era into the
reel era, naming exactly the instrument this subordination acts on.
Chain edges across the namespace seam arrive machine-readable on the
cover; extraction takes them before reading a word of the body. (And
the body confirms: same reel/page, plus parties and amount the cover
omits.)

## CONFIRMATIONS

- rd: key 1001640003 ✓ type ✓ CRFN ✓ doc_date 3/18/2003 (real, not
  cloned) ✓ recorded WITH TIMESTAMP (8:17:53 PM — evening batch) ·
  amount $0.00 (subordination untaxed, unamounted — the $3.8M cap
  lives only in the body) · parties 2, roles empty.
- Two co-borrower ENTITIES on one mortgage (Park Ming Realty LLC + Ng
  Fook Realty Inc) — multi-entity borrower side; identity resolution
  must allow >1 obligor per CAPITAL row.
- Schedule A metes in INTERIOR-ANGLE form ("forming an angle of 89°
  33' 30\" with...") — the exact course format metes.py cannot walk
  (Greenpoint lesson), now confirmed in Manhattan digital-era
  instruments; the limitation is corpus-wide, not Richmond-specific.
- Debt story for the parcel: $700k (2001) → subordinated beneath $3.8M
  (2003) — a 5.4x leverage jump on a Chinatown assemblage; the old
  bank stayed in rather than being taken out (subordinate, not
  satisfied) — a lender RELATIONSHIP signal.
- 13-month execution→recording lag (family: 2d · 22d · 58d · 13mo ·
  8yr).

# RANDOM-DOCUMENT RUN 27 — RC_1058987 · RELEASE OF LIEN OF ESTATE TAX · 1950

3 pages (Liber 1125 pp.472-474), form TT 139 (5-50) — a NEW
INSTRUMENT-MAKER CLASS: the STATE OF NEW YORK, Department of Taxation
and Finance, Transfer and Estate Tax Section, recorded in the county
liber. Estate of JOHN H. PRICE, died 1942-03-23, resident of Richmond
County. Per Tax Law §249-bb, the Article 10-C estate-tax lien is
released as to lots 15+16 on the "Map of lots, Property of Benjamin
Williams, situate at Tottenville" (S.J. Mason, surveyor, 1903-05-01),
James Street at Broadway, Fifth Ward — bounded by "lands now or
formerly of [Anderson] Fisher" (adjoiner-name boundaries). Chain
recital: same premises as Benjamin Williams and Mary Wheeler Williams
→ CROWELL B. PRICE, deed 1908-01-20, recorded 1908-10-12, Liber 353
of Deeds p.279. Issued under the STATE TAX COMMISSION seal 1950-07-21
by H. V. Delaney, Deputy Commissioner — NO notary, NO ack; recorded
1950-07-27. Return: Jerome Otis Ellis, 56 Bay Street, St. George.

## R27-1 — LIENS BORN OFF-RECORD (the release is the lien's only witness)

The estate-tax lien attached AT DEATH (1942) by operation of law — no
instrument was ever recorded creating it. Its RELEASE is the record's
first and only sighting. CAPITAL rows can be born off-record
(statutory liens: estate tax, property tax, mechanic's-lien
relation-back); their releases both close them and DATE them (date of
death recited = the off-record creation date). A chain-walker that
requires a creates-instrument for every release will orphan these;
the release's recitals are the creation evidence.

## R27-2 — DEATH IS A TITLE EVENT WITH NO INSTRUMENT

John H. Price acquired this land with NO recorded deed (the 1908 deed
runs to Crowell B. Price; John holds at death in 1942 — inheritance or
an unrecorded link), and at his death title passed by operation of law
to his heirs OR devisees (which of the two, only the Surrogate's file
knows) — again with no instrument. The county record is SILENT at both joints; a
state tax form eight years later is the only trace. Surrogate's Court
(probate) is a MISSING CUSTODIAN for the multi-source roadmap: wills,
letters, and estate files are where these off-record title events
live. For stakeholder resolution: a decedent's name on a 1950 release
implies an HEIR CLASS holding title since 1942 — people the record
never names.

## CONFIRMATIONS

- rd: key 5080210000 = backer's "Block 8021" ✓ (block-scope) ·
  R/LIEN ✓ liber 1125/472 ✓ 7/27/1950 ✓ · amount $0.00 · instrument
  "2459" internal.
- THE DECEDENT IS INDEXED AS GRANTEE (PRICE JOHN H, eight years dead)
  — the index models the release as State → decedent; stakeholder
  caution: an index party can be a dead person standing in for an
  unnamed heir class.
- Government instrument anatomy: seal + officer signature, no
  notary/ack — the authority-instrument execution class (runs 14/16
  adjacent: trustee and USPS forms; this one purest).
- Adjoiner-name boundaries ("lands now or formerly of Fisher") — a
  description namespace older than lot numbers; the 1903 Tottenville
  map (Benjamin Williams property) joins the filed-map registry.
- Death→release lag: 8 years (the estate cleared its lien only when
  needed — likely a 1950 sale pending; the NEXT deed in this liber
  range would confirm).

# RANDOM-DOCUMENT RUN 28 — RC_1020720 · UCC3 ASSIGNMENT · 2013

4 pages, born-digital (LAND DOC 484078, fee code 288-UCC BLOCK) — the
FIRST UCC instrument drawn, and it is the SECURITIZATION PIPELINE in
miniature. National form UCC3: amendment to initial financing
statement #464215 (filed 2013-02-14, Richmond County — the
origination cluster's fixture filing). Box 4 ASSIGNMENT (full):
FEDERAL HOME LOAN MORTGAGE CORPORATION (Freddie Mac, McLean VA), as
secured party of record, assigns to DEUTSCHE BANK TRUST COMPANY
AMERICAS, AS TRUSTEE FOR THE REGISTERED HOLDERS OF BANC OF AMERICA
MERRILL LYNCH COMMERCIAL MORTGAGE INC., MULTIFAMILY MORTGAGE
PASS-THROUGH CERTIFICATES, SERIES 2013-K713 (Santa Ana, CA). Debtor:
650 VICTORY BOULEVARD LLC c/o SAMSON MANAGEMENT LLC (Rego Park) —
"Victory Apartments (Account No. 708282687)", 650 Victory Boulevard
(block 589 lot 35). Filed by Anderson McCoy & Orta (Oklahoma City).
Recorded 2013-06-26. Exhibit A: USC&GS corner coordinates + "Victory
Boulevard, formerly Richmond Turnpike" (street-rename family).

## R28-1 — THE SECURITIZATION HOP (originate → agency → trust, 4 months)

Feb 2013: loan + fixture filing born. By June: Freddie Mac holds it
and assigns into a K-series CMBS trust. The lender the record now
shows is a TRUSTEE-FOR-A-SERIES — the beneficial owners are
certificate holders, unreachable by design (the institutional twin of
run 25's co-lender ceiling). For the reach ladder: when the holder is
"trustee for Series X", the actionable stakeholder is the SERVICER
(not of record; lives in trust documents off-record). The debt
biography gains a standard edge type: the agency-to-trust hop,
usually ~months after origination, usually via national filing shops.

## R28-2 — INDEX TRUNCATION, MODERN EDITION (the trust name doesn't fit)

rd party: "DEUTSCHE BANK TRUST COMPANY AMERICAS, AS TR" — the series
identity (2013-K713), the part that actually identifies the beneficial
vehicle, is CUT OFF. The film era truncated long personal names (R7
family); the digital era truncates securitization trust names — same
trap, new clothes. Trust-series identity must come from the DOCUMENT;
an index-name join on truncated trustee strings will merge every
Deutsche-as-trustee series in the county into one phantom lender.

## CONFIRMATIONS

- rd: key 5005890035 ✓ UCC ✓ 6/26/2013 ✓ land doc 484078 ✓ · SIX
  party rows for THREE parties (dual-entry with TWO role vocabularies:
  DEBTOR/LENDER + Mortgagor/Mortgagee — the casing family's role-
  vocabulary cousin) · amount $0.00.
- Cover compresses the assignee to "And Others" under LENDER —
  cover-vs-index-vs-document party coverage differs AGAIN (R16-3
  family).
- UCC1 #464215 (2013-02-14) banked as chain expectation — the
  origination cluster (mortgage + AL&R + UCC1, same date) should sit
  at adjacent land docs.
- Operator unmask: "c/o Samson Management LLC" — the property
  MANAGER rides the debtor's address block; stakeholder graph gains
  the operator edge without any instrument naming it as such.
- Fixture-filing anatomy: UCC recorded in COUNTY REAL-ESTATE records
  with block & lot ("UCC WITH BLOCK & LOT" type) — the land-records
  twin of the state-level UCC; both exist, only this one is
  parcel-keyed.

# RANDOM-DOCUMENT RUN 29 — RC_1046067 · SIDEWALK WAIVER (CO PIPELINE) · 1972

3 pages incl. survey-sketch page (Liber 2008 pp.99-101), city form
M-169-A/MP-53. MARIO FORTE (4 Cayuga Avenue), fee owner of 204-208
Dongan Hills Avenue (typed: TAX MAP block 3549, lots 73-77), built or
is building and applied to the Commissioner of BUILDINGS for a
CERTIFICATE OF OCCUPANCY; sidewalks/curbs sit at other than the
legally established lines and grades; the Commissioner of HIGHWAYS
refused to certify (City Charter §230, General City Law §36), which
would force a BOARD OF STANDARDS AND APPEALS appeal — so instead, in
consideration of Highways' CONSENT TO THE CO, the owner (1) waives all
claims against the CITY OF NEW YORK arising from that consent, (2)
covenants to install/conform sidewalks at his own cost WHENEVER the
Commissioner may hereafter direct, and (3) makes it "a covenant
running with the land" binding heirs, successors and assigns.
Executed 1972-09-15 (ack Richmond, notary Robert E. Morri[s]),
recorded 1972-10-03. Return: Norman Redlich, CORPORATION COUNSEL.

## R29-1 — A DOB ARTIFACT IN THE DEED ROOM (the CO pipeline records land covenants)

The Certificate-of-Occupancy process — DOB/Highways/BSA machinery —
deposited a PERPETUAL ENCUMBRANCE in the county land records: the
covenant (no sunset, binds successors) obliges every future owner of
these lots to rebuild sidewalks at the Commissioner's direction. Three
lessons: (1) permit-pipeline instruments (waivers, BSA consents,
restrictive declarations) live in LEGAL INSTRUMENTS, not just agency
files — the multi-source join already exists inside our own corpus;
(2) the waiver SUBSTITUTED for a BSA appeal — entitlement machinery
avoided by covenant is invisible in BSA's own records; (3) ENCUMBRANCE
·creates by a one-party instrument (owner covenants TO the City — the
index models it Grantor FORTE / Grantee CITY OF NEW YORK).

## R29-2 — TWO OFFICIAL BLOCK NUMBERS, TWO MAPS, ONE INSTRUMENT

The typed body: "designated on the TAX MAP ... Block 3549, Lots
73-77." The clerk's certification: indexed "BLOCK 3540V ON THE LAND
MAP OF THE COUNTY OF RICHMOND." rd key: 5035400000 (block 3540,
block-scope) — the INDEX RIDES THE LAND MAP. R19-2 completed: the
suffix blocks (939-L, 375-L, 3540-V) are the COUNTY LAND MAP's
namespace, coexisting with the city TAX MAP's numbers on the same
instruments; a tax-block query (3549) would MISS this waiver entirely.
The land-map↔tax-map concordance is a first-class translation table
the parcel spine needs for pre-renumbering Richmond.

## CONFIRMATIONS

- rd: WAIVER ✓ 10/3/1972 ✓ liber 2008/99 ✓ parties Forte → City of
  New York ✓ · amount $0.00 · instrument "4583" internal.
- The multi-ack printed form (individual/corporate/partnership blanks;
  only individual executed) — form anatomy, one event.
- Survey-sketch PAGE recorded as part of the instrument (dimensions
  58.88 x 57.62 x 47.55 x 58.00) — instruments can carry drawings;
  extraction must expect non-text pages mid-instrument.
- Corporation Counsel as return-to: the CITY is the drafting party on
  its own form — government-counterparty instruments cluster under
  form numbers (M-169-A, MP-53) that identify the PROGRAM, not the
  parcel.

# RANDOM-DOCUMENT RUN 30 — FT_2950006980095 · UCC3 TERMINATION · 2000 (BRONX)

1 page, film (old NY Standard Form UCC3, pre-revision). Box B
TERMINATION: TELEBANK f/k/a METROPOLITAN BANK FOR SAVINGS, FSB
(Arlington, VA; signed Victoria A. Wu) no longer claims the security
interest under financing statement 95PX02172 filed 1995-04-04, Bronx.
Debtors JOHN D. DUFFY and MARGARITA RODRIGUEZ, 5900 Arlington Avenue
#11W, Riverdale. Handwritten block 5953 lot 230; recorded 2000-01-06.
A five-year loan life, dead by termination — the UCC lifecycle's
satisfaction.

## R30-1 — CO-OP DEBT LIVES ONLY IN THE UCC LAYER (index CONFIRMS)

Individual debtors + apartment unit + the rd row's OWN FIELD:
collateral = "COOPERATIVE". Co-op apartment loans are security
interests in SHARES + proprietary lease — personal property; they
never touch the mortgage records. The UCC family (INITIAL COOP UCC1 →
continuations → termination) IS the co-op debt ledger. Any debt
product that reads only mortgages reports every co-op apartment in
the city as debt-free. Termination = COLLATERAL·releases (full),
secured-party-only execution, targeting by file number + filed date
(satisfaction's addressing pattern, UCC dialect).

## R30-2 — THE UCC INDEX ROW IS THE RICHEST YET (fields no other type has)

This film-era row carries: `collateral` (asset class!), `expiration`,
`file_nbr` (county TX-number — 00TX00054, a NEW namespace beside the
PX financing-statement number), and a `references` ARRAY of doc_id +
file_nbr pairs linking related UCC filings — machine-readable chain
edges IN THE INDEX (the UCC cousin of run 26's cover cross-reference
block). UCC rows are pre-joined; the walker should consume
`references` before reading a page.

## R30-3 — THE INDEX KEEPS THE OLD NAME (f/k/a on the secured side)

Document: "TELEBANK f/k/a METROPOLITAN BANK FOR SAVINGS." Index
party: "METROPOLITAN BANK FOR SAVINGS, FSB" — the FORMER name only.
The index was keyed from the original 1995 filing's name and never
learned the rename. Corporate-succession family (N/K/A run 13, run
18's REC books): joins on current names miss index rows still wearing
the old ones; the alias table needs BOTH directions.

## CONFIRMATIONS

- BBL 2059530230 ✓ (block 5953 lot 230 = the handwritten fill) ·
  borough BRONX ✓ 1/6/2000 ✓ 1 page ✓ · keyed_by/key empty (film
  rides parcels — run 16/20 pattern).
- Address discrepancy: typed debtor address 5900 Arlington #11W vs
  index parcel address 5800 ARLINGTON AVENUE — one is wrong; the
  block/lot fill governed the keying; banked as defect, not repaired.
- "Index in Real Estate Records" checkbox UNCHECKED yet block/lot
  handwritten and honored — clerk PRACTICE outruns the form's own
  checkboxes; what the clerk did outranks what the form says was
  asked.
- Early internet-bank sighting (Telebank, 1999-2000) as co-op lender
  successor — lender-population drift visible even in one frame.

# RANDOM-DOCUMENT RUN 31 — RC_1012471 · TAX LIEN DISCHARGE · 2018

3 pages, born-digital (LAND DOC 709639, fee code 25-ASSIGN,AGREE,REL).
THE BANK OF NEW YORK MELLON, as Collateral Agent and Custodian
(Corporate Trust Department ABS; Jacqueline Kuhn, Vice President,
signed 2018-06-20, notary Jonathan Kaplan NY County), certifies it is
record owner of Tax Liens ASSIGNED TO IT BY THE CITY OF NEW YORK per
Tax Lien Certificate dated 2009-08-18 (recorded 2009-08-20, Land Doc
305076), assigned 2011-06-30 (recorded 2011-08-22, Land Doc 392195) —
and that the lien on 30 Vineland Avenue (block 5715 lot 40) IS PAID;
discharged of record. "Duplicate Original" stamp. Presenter: Fein,
Such, Kahn & Shepard P.C. (Parsippany, NJ). Recorded 2018-08-10.

## R31-1 — TAX ARREARS BECOME TRADED DEBT (VALUE → CAPITAL, recited chain)

NYC sells delinquent property-tax liens into securitization trusts
(the NYCTL program); BNYM holds them as custodian. The full lifecycle
is recited with land-doc cites: City certificate (2009) → trust
assignment (2011) → paid → discharge (2018) — a NINE-YEAR lien life.
The login's instinct confirmed in the record itself: VALUE-function
delinquency literally converts into a CAPITAL-function traded lien;
a tax-lien certificate on a parcel is a DISTRESS EVENT, its discharge
a recovery event, and the years between are carry. Same recited-chain
economics as run 21's Schedule B, government edition.

## R31-2 — ONE TYPE CODE, TWO STATUTES (R/LIEN spans 1950 and 2018)

Run 27 (1950): estate-tax lien, born at death, state-issued, no
notary. Run 31 (2018): property-tax lien, sold to an ABS trust,
bank-issued, notarized. Same rd type (R/LIEN), utterly different
machinery — the type code names a SHELF, and 46 years of bootcamp
evidence now says every shelf mixes species; the instrument body is
the only classifier that survives eras.

## CONFIRMATIONS

- rd: key 5057150040 ✓ R/LIEN ✓ 8/10/2018 ✓ land doc 709639 ✓ ·
  dual-entry casing quadruple AGAIN (ASSIGNOR/Assignor x2 — third
  instance, now routine) · amount $0.00.
- Cover roles ASSIGNOR/ASSIGNEE on a DISCHARGE — the fee-code family
  (25-ASSIGN,AGREE,REL) lends its role vocabulary to everything it
  shelves (R15-3 family).
- Chain cites banked: Land Docs 305076 (certificate) + 392195
  (assignment) — the parcel's distress period 2009-2018 is fully
  addressable.
- "Duplicate Original" stamp — artifact-state claim (the recorded copy
  is a counterpart, fine); uniform-ack form names its own statute
  (post-1999 uniform acknowledgment) — modern ack anatomy.

### P-5 RENDER RULE (login 2026-08-22): BATCHES KEEP THE FULL FORMAT

"I am impressed with your speed, but do want to keep the same format
instead of shortened when you are doing batches." A batch changes the
PACING, never the DELIVERY: every run in an N-run or auto batch gets
the complete verdict — anybody test, data table, event test, grade
with miss ledger, why-pass pairs. The one-line Run Log note is for
progress tracking DURING the batch; it never substitutes for the full
verdicts at delivery. A shortened verdict hides exactly the misses the
grade exists to surface.

# RANDOM-DOCUMENT RUN 32 — FT_2850003884985 · UCC3 CONTINUATION · 1991 (BRONX)

2 frames = TWO INSTRUMENTS in one doc id: the 1991-04-12 UCC3
CONTINUATION (file 91PX02431; Florence Stokes, Asst. Vice President)
AND, imaged behind it, the ORIGINAL 1986-04-22 UCC1 it continues
(86PX02585, 1:41 PM). Debtor: 3530 OWNERS CORP. — the CO-OP
CORPORATION itself (3530 Henry Hudson Parkway East, Bronx; section 19
block 5795 lot 518). Secured party: THE MANHATTAN SAVINGS BANK, "Re:
Mtg #212189-5" (the bank's loan number joining the UCC to the
building's underlying mortgage). Collateral: all fixtures, equipment
and articles of personal property attached to or used in operating the
premises + products; original filed WITHOUT debtor signature (under
security agreement authority); indexed in the real-estate records.
Continuation filed TEN DAYS before the five-year lapse.

## R32-1 — THE LAPSE CLOCK (a non-event that kills liens, and renewal as velocity)

UCC financing statements DIE at five years unless continued in the
pre-lapse window. This continuation, filed 10 days before the
anniversary, is COLLATERAL·modifies (term extended) — but the deeper
lesson is the event that leaves NO instrument: a lapse. Like death
(run 27), the clock changes the world without paperwork; derivation
must compute lapse from ABSENCE (no continuation by year 5 → the
security interest is dead, silently). And a filed continuation is the
purest renewal-as-velocity signal: the lender still cares, the loan
still lives.

## R32-2 — THE CO-OP DEBT STACK HAS TWO FLOORS (and the index labels them)

Run 30: unit-level share loan (index collateral "COOPERATIVE"). Run
32: the CORPORATION's own underlying-mortgage fixture filing (index
collateral "FIXTURE FILING"). Same building type, two debt layers —
unit owners' share loans + the co-op corp's building debt — and the
index's collateral vocabulary distinguishes them cleanly. "____ Owners
Corp." at its own street address is the co-op-corporation identity
marker: the entity IS the building.

## R32-3 — THE INDEX RECONSTRUCTS THE LIFECYCLE (references + expiration)

The rd row links BACKWARD (86PX02585, the 1986 original, its FT_ doc
id given) and FORWARD (94TX00121 — a TX-family number: the
TERMINATION), and its `expiration` field reads 3/3/1994 — NOT the
statutory lapse date (1996-04-22 after continuation) but the ACTUAL
death date, backfilled from the termination. Created 1986 → continued
1991 → terminated 1994-03-03: the full arc assembled from ONE index
row before reading any page. UCC rows are a self-contained lifecycle
graph; the walker reads `references` + `expiration` FIRST, then
documents only where the graph is silent. (⚠ `expiration` is
OVERLOADED: statutory lapse on live rows, actual termination date on
dead ones — read it as "when this stopped mattering," verify which by
the references.)

## CONFIRMATIONS

- rd: type ✓ 2 pages ✓ 4/12/1991 ✓ BRONX ✓ file 91PX02431 ✓ BBL
  2057950518 ✓ parties 2 ✓ (no dual-entry on this film row).
- Two instruments in one doc id — the INVERSE of duplicate frames
  (R18/R20): frame count ≠ instrument count in BOTH directions; the
  reader identifies instruments by their own headers, never by file
  boundaries.
- "Re: Mtg #212189-5" — lender loan-number namespace joining the UCC
  to the underlying mortgage (run 20's loan-number trio family; here
  it is the JOIN HINT between two recorded instruments).
- Both filings signed by the BANK only (original under
  security-agreement authority, continuation by Asst. VP) — UCC
  execution anatomy: the debtor can be signature-absent from its own
  lien's whole life.
- Timing discipline: continuation at year 4.97 of 5 — the pre-lapse
  window practice measured.

# RANDOM-DOCUMENT RUN 33 — BK_6640023700437 · ASSIGNMENT OF MORTGAGE · 1966 (QUEENS)

2 frames, faint film (REC 237 pp.437-438), Statutory Form 1
(Assignment of Mortgage Without Covenant, Security Title and Guaranty
Co.) — the FIRST assignment read directly (10% of corpus), and an
ESTATE-DISTRIBUTION one: GEORGE ARONS (24 Audubon Blvd., Island Park),
as ADMINISTRATOR of the Estate of FANNIE ARONOWITZ (died 1965-12-10, a
Nassau resident; Letters of Administration, NASSAU COUNTY SURROGATE'S
COURT, file no. faint), for One Dollar "and to distribute the estate,"
assigns to SYLVIA HOROWITZ (275 E. Walnut St., Long Beach), LEE
GREENBERG (64 E. Market St., Long Beach), and GEORGE ARONS himself the
decedent's interest in a mortgage made by BEACH STREET REALTY CORP. to
FANNIE ARONOWITZ and ISIDOR BERMAN, $10,000, dated 1961-05-01,
recorded 1961-05-05 in QUEENS Liber 7847 of Mortgages p.600, covering
158 Beach 64th Street, Far Rockaway (75x100). Executed Sept 1966, ack
Nassau (notary Maurice Weiner[?]), recorded 1966-09-23.

## R33-1 — THE BK_ ID ENCODES BOROUGH (digit 3), CONFIRMED BY RD

BK_66|4|00237|00437 = year 66 · borough 4 · book 237 · page 437 — and
rd says QUEENS, BBL 4159350037. With run 18 (digit 2 = Bronx), the
parse is confirmed across two boroughs: the BK_ family is the
city-wide REC-book series, self-describing to year+borough+book+page.
The corpus now spans FOUR boroughs (Richmond, Bronx, Manhattan,
Queens).

## R33-2 — DEATH DISTRIBUTES DEBT (the Surrogate's machinery records here)

Run 27: death moved TITLE with no instrument. Run 33: death moved a
MORTGAGE INTEREST and DID leave an instrument — because a mortgage is
personalty the administrator must assign to distribute. CAPITAL·
assigns, consideration $1 + "to distribute the estate", authority =
Letters of Administration (Surrogate's file cited). Holder-side
consequences: Fannie's interest → THREE DISTRIBUTEES (⚠ heirship
inferred, not stated — see addendum) while ISIDOR BERMAN still
holds his — the mortgage now has FOUR holders, and
its future satisfaction needs all of them. Inheritance FRAGMENTS the
holder side; resolution must let one CAPITAL row's holder slot become
a set with fractional interests.

## R33-3 — THE CAPACITY SUFFIX PARTY ("ARONOWITZ,FANNIE (ADMTR OF)")

The index's assignor is the DECEDENT with a capacity tag appended —
the administrator's own name (George Arons) appears only as assignee.
Party-name strings carry CAPACITY IN-BAND ("(ADMTR OF)", and by
implication EXR OF, TRSTE OF, GDN OF...) — a parsing family: strip and
bank the capacity, resolve the estate as the acting entity, and find
the human in the document. A name-match on "George Arons" would MISS
his assignor role entirely.

## CONFIRMATIONS

- rd: QUEENS ✓ BBL 4159350037 ✓ reel_page 237-437 ✓ type ✓ 2 pages ✓ ·
  amount $0.00 (the $10,000 lives in the body) · doc_date = recorded
  (film clone family R18-3; execution was days earlier, faint).
- remarks "A L7847 PG600 BOOK/PAGES: 290/311": the FIRST cross-ref
  ("A L7847 PG600") is the assigned mortgage — VERIFIED against the
  document's own cite; the second (290/311) points into the REC books
  (referent unverified — likely a related assignment/satisfaction).
  Run 18's mystery "D BOOK/PAGES: 182/88" now has a family: film-index
  remarks carry typed chain cross-references, prefix-coded (A=
  assignment target, D=deed?), partially verifiable and worth
  harvesting.
- Private individuals as LENDERS (Fannie + Isidor, 1961 — seller
  financing profile) — the holder population includes people, not just
  banks; the reach ladder's lender rung can be an estate.
- Draw-method upgrade (login): consult the RD ROW FIRST for type/
  pages/path — the db is readable during acquisition (WAL readers are
  free; only scans and writes are barred); no filesystem globs.

## R33 ADDENDUM — SELF-AUDIT (login asked; corrections, same day)

1. GRADE AMENDED A− → B+. The delivered summary called the three
   assignees "her three heirs" — THE DOCUMENT NEVER SAYS HEIRS. It
   says they paid $1 and the purpose was "to distribute the estate";
   heirship is an INFERENCE (strong, unproven). G-026 family violation
   in the render layer, unflagged at delivery → double cost. The
   stakeholder lesson sharpened: distributee ≠ heir; the Surrogate's
   file, not this instrument, knows who the heirs are.
2. PROCESS MISS: single-look values on the faintest artifact yet. The
   $10,000, "Isidor Berman," "Maurice Weiner" were read once at one
   render size. The crop law (R19-1, CLAUDE.md rule 3) applies to
   AMOUNTS AND NAMES on degraded film, not just stamps — new reflex:
   on faint film, every load-bearing value gets a second look at
   higher dpi before delivery. (Mitigation held: the chain join rides
   the liber/page cite, double-witnessed by the index remark.)
3. VACUOUS RECONCILIATION: rd's BBL was ACCEPTED, not confirmed — the
   premises reading was too faint to independently verify block
   15935. Rule: when the document-side reading of a field is below
   confirmation strength, the reconciliation mark for that field is
   "accepted (rd sole witness)", never "✓". Agreement must be earned
   by two independent readings or labeled as one-witness.

# THE ASSUMPTION LAW + THE GRADING PROTOCOL (login, 2026-08-22 evening)

## THE ASSUMPTION LAW — the hallucination concern, stated as bootcamp law

"You really need to make sure not to assume. And if you do it needs to
be very clear... It is worse to overstate a false claim than to say
you don't know."

- Every statement in a delivered verdict is one of THREE kinds, and
  the kind must be VISIBLE: (1) READ — the document says it, anchored;
  (2) VERIFIED — two independent witnesses agree (doc+rd, doc+doc,
  doc+arithmetic); (3) INFERRED — context suggests it, and it is
  MARKED as inference IN THE SENTENCE ("presumably", "⚠ HYPOTHESIS",
  "the document does not say"). An unmarked inference is a defect even
  when it is probably true (run 33's "heirs").
- The rd is a HELP when stuck — a field there can settle a faint
  reading (liber digits, blocks). But rd never upgrades an unread
  document value to "read"; it makes it "accepted (rd sole witness)".
- IF SOMETHING CANNOT BE DONE, SAY SO AS THE RESULT. "The film is too
  faint to read the amount" is a deliverable; a guessed amount is
  corpus poison. Unknown > wrong, always, at any speed.

## THE GRADING PROTOCOL — who grades, when

- SINGLE RUNS (login monitoring): deliver the report — anybody test,
  data table, event test, WHY-PASS — and STOP. No self-grade at
  delivery. The login prompts for the grade after reading; grading
  prompted from outside the run's momentum is more objective (run 33
  proved it: the self-grade missed what the login's question caught).
- BATCH / OVERNIGHT (auto loop, login away): self-grade every run in
  full (report + why + grade + miss ledger), because no one is there
  to prompt and a half-graded run is worse than a self-graded one.
- The why-pass stays in BOTH modes.

# BACKWARD RE-CHECK 2026-08-22 (evening) — THE ASSUMPTION AUDIT

Login: "Should you review any that you graded in the same breath?" The
assumption law was re-run over every entry delivered today (runs
12-33). FOUR banked defects found and corrected IN PLACE:

- Run 17: "trustee is family" / "the beneficial family stays" → the
  deed states NO relationship between Lisa and James Argenziano (same
  surname + same address = inference); beneficiaries live in the
  unrecorded trust agreement. CORRECTED.
- Run 21: Island Properties NYC LLC called "a debt buyer" → role
  inferred from pattern; the record shows only assignments. MARKED.
- Run 27: "title passed to heirs" → heirs OR devisees; only the
  Surrogate's file knows which. CORRECTED.
- Run 33: entry's own text repeated "THREE heirs" that its addendum
  had corrected → now "three distributees, heirship inferred."

CHAT-DELIVERY over-claims acknowledged (not in the banked record, but
said to the login today — the render layer is also a delivery):
- Run 24: "held the paper in a drawer" — the CAUSE of the 8-year
  recording delay is unknown (escrow, loss, re-recording all possible).
- Run 30: "paid off" — a UCC termination proves the secured party
  released its claim, NOT that the debt was paid.
- Run 32: "the building refinanced" — cause of the 1994 termination
  unknown; only the termination itself is witnessed.
- Run 28: "run by Samson Management" — c/o address = management
  inferred, not stated.

Grades already issued stand as issued EXCEPT run 33 (amended B+
earlier); the audit's lesson is prospective: the assumption law now
runs at COMPOSE time, and same-breath grading ends per the grading
protocol. Pattern note: every defect found was a RELATIONSHIP or
MOTIVE claim (family, heirship, business role, cause of delay/death of
liens) — the narrative layer's temptations; quantities, dates, cites
and functions survived the audit clean across all 22 runs.

## GRADING PROTOCOL AMENDMENT — THE OVERNIGHT GRADE ROTATION

Login: "is there a way for your overnight to rotate bootcamp, grade,
bootcamp, grade?" Adopted: in auto mode, NO run is graded in the same
breath as its report. Each iteration OPENS by grading the PREVIOUS run
— re-reading its banked entry cold after a full document of unrelated
work — using the adversarial checklist measured from the 2026-08-22
audit: (1) relationship/motive claims stated as fact; (2) unmarked
inferences; (3) vacuous reconciliation ✓s; (4) single-look values on
degraded film. Sequence: grade N-1 → report N → grade N (next
iteration) → ... The final run of the night is left UNGRADED for the
login to grade in the morning — the human stays in the calibration
loop. Single-run mode unchanged: login prompts the grade.

# RANDOM-DOCUMENT RUN 34 — RC_1032054 · DECLARATION OF COVENANTS · 1976

5 pages, typed (Liber 2145 pp.475-479) — the first DECLARATION drawn:
a PRIVATE UTILITY LIEN REGIME. SPRINGVILLE CONSTRUCTION CORP. (2701
Goethals Road North) owns a sewage PUMPING STATION + private sanitary
sewer lines ("Sewage Disposal System", installed by prior owner
SPRINGVILLE ASSOCIATES). WILLIAM KARPELES (24 Jones Street), owner of
the abutting parcel (Exhibit B: Jones Street metes; "Tax Block 2156,
Lot 72 and part of 73"), about to erect a TWO-FAMILY dwelling, needs
hookup via the Jones Street manhole. Springville's price: the parcel
must carry an ANNUAL CHARGE that becomes a LIEN. So Karpeles DECLARES
(1975-12-19 [day READ from ack fill], recorded 1976-01-22 2:08 PM;
notary FRANK E. KARPELES — surname shared with declarant, relationship
UNSTATED; return to Angelo Scopellito, Esq., Garden City): annual
charge fixed by Springville, payable Jan 1 in advance, MAX $75.00/yr,
becoming a lien on the parcel each Jan 1 until paid, enforcement
vested in Springville; charge = pro-rata share (total pumping-station
operating cost ÷ connected residential units, itemized: salaries,
materials, taxes, overhead, engineering, repairs, trucking); increases
allowed within the cap to recoup losses; deeds and mortgages of the
parcel CARRY the covenants "as if inserted"; the assessment lien
SELF-SUBORDINATES to institutional first mortgages on three express
conditions (recognized-lender, mortgage-budget-collects-the-charge,
foreclosure-wipes-accrued-but-not-future); covenants run UNTIL AN
EVENT — gravity discharge into the City Sewer System, or City
acquisition of the pumping station — "whichever occurs earlier."

## R34-1 — THE RECURRING LIEN GENERATOR (a covenant that mints CAPITAL rows)

One ENCUMBRANCE·creates row births an open-ended SERIES of future
liens: every January 1, a new charge-lien arises on the parcel by
covenant + calendar, no instrument recorded (R27's off-record family,
here PRIVATE and RECURRING). Derivation: the parcel's encumbrance
state includes machine-generated liens whose existence is computed
from the covenant + the calendar + (unknowable from the record)
payment; the record can say "a lien MAY stand" but never "none does."
The regime even prices itself: cost-sharing formula + $75 cap +
loss-recoupment — a private utility's rate card recorded in the deed
room.

## R34-2 — THE EVENT-BASED SUNSET (the term family completes)

Run 12: sunset by DATE (1915-01-01). Run 34: sunset by EVENT (gravity
sewer OR municipal acquisition, whichever first). Terms now come in
three time-shapes: date-bounded, event-bounded, perpetual (run 29).
An event-bounded term is UNDECIDABLE from the instrument alone —
whether Jones Street ever got a gravity sewer lives in DEP/city
records (multi-source join), so the covenant's live/extinct state is
honestly `unresolved` until an outside witness arrives. (Contrast run
12: a date sunset self-decides at read time.)

## R34-3 — A WHOLE EXHIBIT STRUCK THROUGH (the deletion layer scales)

Exhibit "A" — the PUMPING STATION's parcel description (Arlene
Street/Dawson Circle metes, still legible) — is crossed out line by
line; Exhibit "B" stands. The strike-layer family (run 20's struck ARM
caps, run 24's struck form phrases) now includes ENTIRE EXHIBITS:
reading struck text as operative here would attach the covenant to
the WRONG PARCEL (the station's own lot). Extraction law: every text
region carries a struck/unstruck state, and struck text is banked as
deleted-but-legible, never as operative. WHY it was struck is
UNSTATED (⚠ plausibly to avoid clouding Springville's parcel — 
hypothesis only).

## CONFIRMATIONS

- rd: DECLARATION ✓ liber 2145/475 ✓ 1/22/1976 ✓ · key 5021560000 =
  BLOCK-scope though Exhibit B names "Lot 72 and part of 73" — the
  PARTIAL LOT ("part of 73") likely defeated lot-keying (⚠ inference);
  a lot-72 query would miss this declaration.
- Priority machinery written INTO the covenant (self-subordination
  with conditions) — G-037's ladder shaped by the instrument itself;
  the three conditions include a MORTGAGE-SIDE duty (the lender's
  budget must collect the charge) — a covenant reaching into future
  lenders' servicing.
- "Deeds and mortgages shall carry these covenants as if inserted" —
  the declaration binds instruments not yet written; chain-walkers
  should EXPECT the charge to surface in later deeds of block 2156
  lot 72 (banked as forward expectation).
- Springville Associates → Springville Construction Corp. (prior owner
  installed the system) — corporate-succession family, sponsor-side.
- One-party instrument (declarant only signs; beneficiary consideration
  $1 FROM Springville) — the run-29 shape (owner covenants to a
  counterparty who signs nothing).
- Notary surname = declarant surname (Frank E. / William KARPELES) —
  observation only, relationship unstated (assumption law applied).

## R34 GRADE (login-prompted, cold checklist) — A−, three delivery misses

1. EXECUTION DATE: the witness clause day is BLANK ("this ____ day of
   December, 1975"); only the ack carries 19th. Delivered table said
   "executed 1975-12-19" unqualified. CORRECT ENTRY: ack 1975-12-19,
   execution date line blank. D-3 family — when the execution clause is
   unfilled, the ack dates APPEARANCE, not signing, and the row says so.
2. "RESIDENTIAL UNITS" → "houses" in the summary: the divisor is units,
   the $75 cap is per PARCEL, and the dwelling is a TWO-FAMILY — whether
   the parcel counts as one unit or two is UNRESOLVED on the page. The
   paraphrase silently resolved it. Keep the instrument's own noun when
   the noun carries arithmetic.
3. ERA CONTEXT asserted flat ("parts of Staten Island had no city
   sewer"). The supported claim is narrower and enough: THIS parcel
   could not reach the City sewer by gravity — which is why the sunset
   is event-shaped. Background knowledge is an inference like any other.

CLEAN: no relationship/motive claim in the run (the audit's defect
class); reconciliation ✓s earned on a legible typed artifact; the three
findings anchored.

# THE LENGTH LAW — bootcamp verdict vs DB record (login 2026-08-22)

Login: "details are good to understand, but the db is designed to
DISTILL documents and if we get too long it would defeat its purpose."
Correct, and the two artifacts must never be conflated:

- THE BOOTCAMP VERDICT is a TEACHING artifact — long on purpose, exists
  to prove understanding, expose misses to grading, and mint rules.
  NEVER stored in the corpus.
- THE DB RECORD is a DISTILLATION — rows a machine joins, counts, and
  reasons over. Already ~30:1 vs the verdict (run 20: 27 pages → 2 rows;
  run 21: 21 pages → 1 row + recited chain). The ROWS are not the bloat
  risk; CLAIMS are.

## The claim gate (extends "extract only what has a slot")

A claim earns storage if it (a) fills a slot in some row's
subject/function/quantity/term, (b) is a CHAIN EDGE (cite to another
instrument), or (c) CHANGES WHAT A BROKER WOULD DO. Test (c) kills the
noise: "notary Frank E. Karpeles, Richmond County" fails all three at
10M-document scale; "$75/yr cap, lien each January 1" passes (a)+(c).
Run 34 under the gate = 1 event row + ~8-10 claims.

## Verbatim is the paid exception

Most claims are STRUCTURED VALUES, not sentences. Store verbatim only
where THE WORDS ARE THE FACT — sunset clauses, exculpation,
subordination conditions — because a paraphrase cannot be re-litigated
and silently loses meaning (run 34's "residential units" → "houses"
proved the failure mode in one word). Anchors (document_id + page +
region) are ADDRESSING, not verbosity: mandatory always.

## THE SUMMARY IS GENERATED FROM THE ROWS, NOT WRITTEN BESIDE THEM

1-2 sentences per document, composed AFTER the table, FROM the table.
Two effects at once: length is capped structurally, and the summary
becomes a COMPLETENESS CHECK — if the sentence needs a fact the rows
lack, the rows are incomplete; if the rows cannot produce a coherent
sentence, extraction failed. The anybody test survives into production
as a TEST, not as stored prose, and the DB can never hold a paragraph
that disagrees with its own table.

## Budget = a SIGNAL, not a cap

Working spec budget: 1-5 event rows · <=15 claims · <=3 sentences per
document. Exceeding it is diagnostic, never an error: either the
document is a PACKAGE that should be split into component instruments
(run 20's nine riders, run 21's Schedule B), or the claim gate is not
being applied. Never truncate to hit the number — split or gate.

## The compute argument (why terseness is throughput)

At ~60M pages, OUTPUT tokens dominate the extraction run: generation is
the bottleneck, not reading. 800 tokens/page instead of 250 roughly
TRIPLES wall-clock on the cluster — the difference between a long
weekend and most of a month. Verbosity in the spec is a compute
decision as much as a schema decision.

# RANDOM-DOCUMENT RUN 35 — RC_1050386 · GASOLINE-STATION LEASE · 1956

6 pages, Texaco form CT:R-441 (Liber 1361 pp.453-458). Agreement dated
1956-07-18, acks 1956-07-2? (both New York County; day partly
obscured), recorded 1956-08-01 (fee $9, examined M.T.B.). STATEN
ISLAND OIL COMPANY, INC. (250 Meredith Avenue, S.I.; John Leopold,
President; attest Ilma H. Leopold, Secretary [surname shared — NO
relationship stated]) leases to THE TEXAS COMPANY, a Delaware
corporation (205 East 42nd Street) the service station at 5801 Amboy
Road, Princess Bay — NW corner Amboy Road & Foster Road, USC&GS
coordinates on the corner (S 47808.509, W 44032.546). FIFTEEN YEARS
from 1956-08-01. RENT $285.00/month, payable monthly in advance.
Improvements listed as leased: 1 two-bay stucco service-station
building, 4 x 550-gallon underground tanks, 2 computer pumps (a lift
and an air compressor STRUCK from the list).

## R35-1 — THE FULL LEASE STATES RENT (the memorandum contrast, measured)

Run 16 (1995 memorandum): rent omitted BY DESIGN, `unavailable`
forever. Run 35 (1956 full lease): "$285.00 Dollars per month payable
monthly in advance" typed on the page. SAME function (OCCUPANCY·
creates), OPPOSITE quantity availability — so the OCCUPANCY price
witness depends on WHICH ARTIFACT was recorded, not on the era or the
deal. Extraction rule: a LEASE type may carry rent; a MEMORANDUM type
may not; never treat a missing rent as a read failure without first
classifying the artifact. (⚠ Two data points, not a measured rate —
worth a typed sweep later: what fraction of recorded LEASE rows state
rent?)

## R35-2 — LEASE-AND-SUBLEASE-BACK (the same premises, both directions, same day)

Rider (2-A) recites a SUB-LEASE dated the SAME DAY, 1956-07-18, from
THE TEXAS COMPANY as lessor back to STATEN ISLAND OIL COMPANY as
lessee, covering the SAME premises — and gives the lessor a 30-day
cancellation right if that sublease is ever terminated other than for
Staten Island Oil's default, CONDITIONED on Staten Island Oil first
paying in full its indebtedness to the FIRST NATIONAL CITY BANK OF
JERSEY CITY. Two OCCUPANCY rows run simultaneously in opposite
directions between the same two parties, plus a CAPITAL fact about a
third party (a bank owed money, disclosed only here — R16-3's
"lease packages leak debt" family, 39 years earlier). The operator
keeps running the station; the oil major holds the leasehold. Any
occupancy model that assumes one tenant per premises at a time
MISREADS this shape.

## R35-3 — AN OPTION TO PURCHASE, PRICE STRUCK OUT (the deleted-term state)

¶9 grants lessee "the exclusive right, at lessee's option, to purchase
the demised premises... free and clear of all liens and encumbrances
(including leases which were not on the premises at the date of this
lease) at any time during the term" — with a RIGHT OF FIRST REFUSAL
mechanic (bona fide offer → 30 days to match) and a full title/survey
delivery regime. The PRICE LINE (¶9(a) "for the sum of ______") is
BLANK and ¶10 (Application of Accrued Rentals to Purchase Price) is
STRUCK THROUGH. So: the option EXISTS (right-of-first-refusal branch
operative) while the FIXED-PRICE branch is unpriced/deleted. State the
row honestly — TITLE·(option) with quantity `unavailable — line left
blank`, NOT "option at $0" and NOT "no option". A struck clause and a
blank line are DIFFERENT states and both are different from absent.

## CONFIRMATIONS

- rd: LEASE ✓ liber 1361/453 ✓ 8/1/1956 ✓ parties 2/2 ✓ · key
  5068960000 BLOCK-scope (no lot on the record page read) · amount
  $0.00 while the document states $285/mo — the amount-blind index
  holds for LEASE rows (R20-3: amounts are for MORTGAGE rows).
- Term shapes accumulate: 15 years + extension option (¶11, term
  length UNREAD — the line is faint) + holdover→month-to-month (¶12).
- Lessee-favoring machinery worth banking as claims: termination if
  petroleum distribution is restricted by law/ordinance (¶6 — a
  REGULATORY-RISK exit), condemnation apportionment, rent-offset
  against lessor's debts (¶3), removal of lessee property within 30
  days after term (¶5).
- Corporate execution both sides (seals + boards); ¶18 lists NINE
  Texaco officer titles who may bind the company — the authority layer
  enumerated inside the lease.
- Struck equipment items (lift, air compressor) — the strike layer
  again (run 34's exhibit, run 20's caps): equipment lists are
  negotiated.
